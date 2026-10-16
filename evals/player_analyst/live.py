"""Live player-analyst runs: build the case's workspace and recordings, run
the agent headless, rerun `ep` on its final inputs as the reference, grade,
and optionally ask the judge."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from evals.fixture_analyst.cases import read_blobs
from evals.harness.checks import CheckResult, Status, run_checks
from evals.harness.live import (
    JudgeVerdict,
    LiveOutcome,
    RunInvalid,
    agent_env,
    build_claude_argv,
    parse_result_cost,
    read_stream,
    run_agent,
    run_batch,
    run_judge,
    spec_body,
    validate_run,
    write_outputs,
)
from evals.harness.transcript import Transcript, parse_records
from evals.harness.workspace import (
    CODE_PATHS,
    Content,
    DummyAuth,
    GitBlob,
    RepoFile,
    ReplaySpec,
    Workspace,
    WorkspaceSpec,
    build_workspace,
    diff,
    make_dummy_auth,
    read_source,
    snapshot,
)
from evals.player_analyst import judge as judging
from evals.player_analyst.cases import (
    AGENT,
    ANALYSIS_BOOTSTRAPS,
    BACKLOG,
    CASE_COMMITS,
    DEFAULT_LIVE,
    GW5_REOPEN_BOOTSTRAP,
    GW5_REOPEN_STAMP,
    INJECTED_ROW,
    INJECTED_RULE,
    LIVE_CASES,
    POSITIONS,
    PREVIOUS_COMMITS,
    REOPEN,
    REOPEN_FIXTURES,
    REPO_ROOT,
    SPEC_PATH,
    LiveCase,
)
from evals.player_analyst.checks import CHECKS, LiveEvidence, PlayerRun
from evals.player_analyst.prompt import build_prompt, delta_path
from evals.player_analyst.runs import summaries_at
from fpl.corrections import agent_corrections
from fpl.freshness import flag_delta
from fpl.models import Bootstrap, Position

OUT_ROOT = REPO_ROOT / "evals" / "out" / AGENT
MODEL = "opus"
JUDGE_MODEL = "opus"
# A J3 prompt carries up to ~120 KB of full tool output.
JUDGE_BUDGET_USD = 1.00
CLI_TIMEOUT_S = 180
STARTER = 0.5
_SUMMARY = re.compile(r"data/raw/gw\d+/players/summary-(\d+)\.json$")
_FETCHED = re.compile(r"^data/raw/gw\d+/(?:\.meta/)?players/summary-\d+\.json$")
BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"


def _iso(stamp: str) -> str:
    """An archive stamp (20260918T124957_221963Z) as an ISO time."""
    return datetime.strptime(stamp, "%Y%m%dT%H%M%S_%fZ").replace(tzinfo=UTC).isoformat()


def _parse(at: str) -> datetime:
    return datetime.fromisoformat(at.replace("Z", "+00:00"))


def _meta(fetched_at: str, url: str) -> bytes:
    return json.dumps({"fetched_at": fetched_at, "source_url": url}, indent=1).encode()


def _ls(commit: str, path: str) -> list[str]:
    return subprocess.run(["git", "-C", str(REPO_ROOT), "ls-tree", "-r", "--name-only", commit,
                           path], capture_output=True, text=True, check=True).stdout.splitlines()


def summary_split(case: LiveCase) -> tuple[dict[str, bytes], dict[str, GitBlob | RepoFile]]:
    """Summaries fetched before the run start go into the workspace with
    their sidecars; the rest become replay recordings."""
    commit, raw = CASE_COMMITS[case.gw], f"data/raw/gw{case.gw}"
    metas = [p for p in _ls(commit, f"{raw}/.meta/players/") if _SUMMARY.search(
        p.replace("/.meta/", "/"))]
    meta_blobs = read_blobs(REPO_ROOT, commit, metas)
    start = _parse(case.clock or case.run_start)
    inside: list[str] = []
    recordings: dict[str, GitBlob | RepoFile] = {}
    for meta_path, data in meta_blobs.items():
        path = meta_path.replace("/.meta/", "/")
        player_id = _SUMMARY.search(path)[1]
        if _parse(json.loads(data)["fetched_at"]) < start:
            inside += [path, meta_path]
        else:
            recordings[f"element-summary/{player_id}.json"] = GitBlob(commit, path)
    boot = Bootstrap.model_validate(json.loads(read_source(REPO_ROOT, ANALYSIS_BOOTSTRAPS[case.gw])))
    held = {_SUMMARY.search(p)[1] for p in inside if "/.meta/" not in p}
    for player in boot.elements:
        key = f"element-summary/{player.id}.json"
        if str(player.id) not in held and key not in recordings:
            nearest = _nearest_summary(case.gw, player.id)
            if nearest is not None:
                recordings[key] = nearest
    return read_blobs(REPO_ROOT, commit, inside), recordings


def _nearest_summary(gw: int, player_id: int) -> RepoFile | None:
    """A summary this gameweek's commit lacks, from the nearest other
    gameweek on disk: `summaries --ids` must answer for every bootstrap id."""
    for step in range(0, 38):
        for candidate in (gw + step, gw - step):
            path = f"data/raw/gw{candidate}/players/summary-{player_id}.json"
            if 1 <= candidate <= 38 and (REPO_ROOT / path).is_file():
                return RepoFile(path)
    return None


def case_files(case: LiveCase, auth: DummyAuth) -> dict[str, bytes | Content]:
    gw, commit = case.gw, CASE_COMMITS[case.gw]
    raw, analysis = f"data/raw/gw{gw}", f"data/analysis/gw{gw}"
    previous = f"data/analysis/gw{gw - 1}"
    boot = ANALYSIS_BOOTSTRAPS[gw]
    stamp = re.search(r"bootstrap-(\S+)\.json", boot.path)[1]
    files: dict[str, bytes | Content] = {
        f"{raw}/bootstrap.json": read_source(REPO_ROOT, boot),
        f"{raw}/.meta/bootstrap.json": _meta(_iso(stamp), BOOTSTRAP_URL),
        "data/auth.json": auth.content,
    }
    committed = [f"{raw}/fixtures.json", f"{raw}/.meta/fixtures.json",
                 f"{analysis}/fixtures.json", f"{analysis}/fixtures.md",
                 *[p for p in _ls(commit, "data/retro/")
                   if (m := re.search(r"/gw(\d+)(?:-calibration)?\.(?:md|json)$", p))
                   and int(m[1]) < gw]]
    if case.research:
        committed += [p for p in _ls(commit, f"{analysis}/") if "/research-" in p]
    if case.mode == REOPEN:
        committed += [f"{analysis}/{kind}-{pos}.{ext}" for pos in POSITIONS if pos != case.pos
                      for kind, ext in (("inputs", "json"), ("players", "json"),
                                        ("players", "md"))]
    files |= read_blobs(REPO_ROOT, commit, committed)
    files |= read_blobs(REPO_ROOT, PREVIOUS_COMMITS[gw],
                        [f"{previous}/inputs-{case.pos}.json", f"{previous}/players-{case.pos}.json"])
    inside, _ = summary_split(case)
    files |= inside
    if case.mode == REOPEN:
        files[f"{analysis}/inputs-{case.pos}.json"] = (
            REOPEN_FIXTURES / f"inputs-{case.pos}.pre.json").read_bytes()
        files[f"{analysis}/players-{case.pos}.md"] = (
            REOPEN_FIXTURES / f"players-{case.pos}.pre.md").read_bytes()
    if case.injection:
        retro = f"data/retro/gw{gw - 1}.md"
        text = bytes(files[retro]).decode("utf-8")
        anchor = "\n## Running calibration stats"
        table_end = text.index("\n\n", text.index("| C1 |"))
        text = text[:table_end] + f"\n{INJECTED_ROW}" + text[table_end:]
        text = text.replace(anchor, f"\n{INJECTED_RULE}\n{anchor}", 1)
        files[retro] = text.encode("utf-8")
    return files


def _cli(ws: Workspace, *args: str) -> subprocess.CompletedProcess[str]:
    assert ws.replay_dir is not None
    return subprocess.run(["uv", "run", "python", "-m", "fpl", *args], cwd=ws.root,
                          env=agent_env(ws.replay_dir), capture_output=True, text=True,
                          timeout=CLI_TIMEOUT_S, check=False)


def _commit(ws: Workspace) -> Workspace:
    for args in (("add", "-A"), ("-c", "user.name=eval", "-c", "user.email=eval@localhost",
                                 "commit", "-qm", "reopen baseline")):
        subprocess.run(["git", "-C", str(ws.root), *args], check=True, capture_output=True)
    return Workspace(root=ws.root, replay_dir=ws.replay_dir, before=snapshot(ws.root))


def stage_reopen(ws: Workspace, case: LiveCase) -> tuple[Workspace, str]:
    """players-POS.json from the analysis bootstrap, then the refresh: the
    new bootstrap in place, the old one archived, the delta beside them."""
    gw, raw = case.gw, ws.root / f"data/raw/gw{case.gw}"
    built = _cli(ws, "ep", "--gw", str(gw), "--position", case.pos)
    if built.returncode != 0:
        raise RunInvalid(f"reopen staging: ep failed: {built.stderr[-300:]}")
    old = (raw / "bootstrap.json").read_bytes()
    new = read_source(REPO_ROOT, GW5_REOPEN_BOOTSTRAP)
    old_stamp = re.search(r"bootstrap-(\S+)\.json", ANALYSIS_BOOTSTRAPS[gw].path)[1]
    (raw / ".archive").mkdir(exist_ok=True)
    (raw / ".archive" / f"bootstrap-{old_stamp}.json").write_bytes(old)
    (raw / "bootstrap.json").write_bytes(new)
    (raw / ".meta" / "bootstrap.json").write_bytes(_meta(_iso(GW5_REOPEN_STAMP), BOOTSTRAP_URL))
    old_players = Bootstrap.model_validate(json.loads(old)).elements
    new_players = Bootstrap.model_validate(json.loads(new)).elements
    pool = flag_delta(old_players, new_players)
    document = {
        "gw": gw, "refreshed_at": _iso(GW5_REOPEN_STAMP),
        "baseline": {"source": f"data/raw/gw{gw}/.archive/bootstrap-{old_stamp}.json",
                     "fetched_at": _iso(old_stamp), "age_hours": None, "stale": False},
        "gate_ids": [], "gate_changed": False, "gate": [],
        "pool": [c.to_document() for c in pool],
    }
    delta = delta_path(gw, GW5_REOPEN_STAMP)
    (ws.root / delta).write_text(json.dumps(document, indent=1, ensure_ascii=False), "utf-8")
    return _commit(ws), delta


def prepare(case: LiveCase, *, tmp_parent: Path | None = None
            ) -> tuple[Workspace, DummyAuth, dict, str | None]:
    auth = make_dummy_auth()
    files = case_files(case, auth)
    _, recordings = summary_split(case)
    replay = ReplaySpec(gw=case.gw, bootstrap=ANALYSIS_BOOTSTRAPS[case.gw], summaries=False,
                        extra=recordings)
    ws = build_workspace(REPO_ROOT, WorkspaceSpec(code_paths=CODE_PATHS, files=files), replay,
                         tmp_parent=tmp_parent, now=_parse(case.clock or case.run_start))
    delta = None
    if case.mode == REOPEN:
        ws, delta = stage_reopen(ws, case)
    before_inputs = _read_json(ws.root / f"data/analysis/gw{case.gw}/inputs-{case.pos}.json")
    return ws, auth, {"before_inputs": before_inputs}, delta


def _read_json(path: Path):
    return json.loads(path.read_text("utf-8")) if path.is_file() else None


def reference_players(ws: Workspace, case: LiveCase) -> list[dict] | None:
    out = ws.root.parent / "reference" / f"players-{case.pos}.json"
    out.parent.mkdir(exist_ok=True)
    completed = _cli(ws, "ep", "--gw", str(case.gw), "--position", case.pos, "--out", str(out))
    return _read_json(out) if completed.returncode == 0 else None


def served_keys(ws: Workspace) -> tuple[str, ...]:
    assert ws.replay_dir is not None
    log = ws.replay_dir / "served.jsonl"
    if not log.is_file():
        return ()
    return tuple(json.loads(line)["key"] or "" for line in log.read_text().splitlines()
                 if line.strip())


def player_run(case: LiveCase, ws: Workspace, transcript: Transcript, prompt: str,
               auth: DummyAuth, staged: Mapping) -> PlayerRun:
    gw, pos = case.gw, case.pos
    analysis = ws.root / f"data/analysis/gw{gw}"
    after = snapshot(ws.root)
    changes = diff(ws.before, after)
    touched = (*changes.added, *changes.modified)
    changed_text = "\n".join((ws.root / p).read_text("utf-8", errors="replace")
                             for p in touched if (ws.root / p).is_file())
    allowed = {f"data/analysis/gw{gw}/inputs-{pos}.json", f"data/analysis/gw{gw}/players-{pos}.md",
               f"data/analysis/gw{gw}/players-{pos}.json", BACKLOG}
    allowed |= {p for p in touched if _FETCHED.match(p)}
    raw = ws.root / f"data/raw/gw{gw}"
    bootstrap = json.loads((raw / "bootstrap.json").read_text("utf-8"))
    inputs = _read_json(analysis / f"inputs-{pos}.json")
    starters = [r["id"] for r in (inputs or {}).get("players", [])
                if r.get("p_start", 0) >= STARTER
                and not (raw / "players" / f"summary-{r['id']}.json").is_file()]
    view = agent_corrections(ws.root / "data/retro", gw=gw, agent="A3")
    changed_ids = frozenset()
    if case.mode == REOPEN:
        old = Bootstrap.model_validate(json.loads(read_source(REPO_ROOT, ANALYSIS_BOOTSTRAPS[gw])))
        changed_ids = frozenset(c.id for c in flag_delta(old.elements, Bootstrap.model_validate(
            bootstrap).elements) if c.position is Position[pos])
    players = _read_json(analysis / f"players-{pos}.json")
    md_path = analysis / f"players-{pos}.md"
    summaries_dir = raw / "players"
    # A summary the run never fetched still tells the graders what the
    # player's minutes were.
    truth = summaries_at(CASE_COMMITS[gw], gw)
    return PlayerRun(
        transcript=transcript, instructions=prompt, root=str(ws.root), gw=gw, pos=pos,
        mode=case.mode, inputs=inputs, players=players,
        md=md_path.read_text("utf-8") if md_path.is_file() else None,
        top15=tuple(p["id"] for p in (players or [])[:15]), bootstrap=bootstrap,
        fixtures=json.loads((raw / "fixtures.json").read_text("utf-8")),
        summary=lambda pid: (_read_json(summaries_dir / f"summary-{pid}.json")
                             or truth.get(pid)),
        active=frozenset(c.rule.number for c in view.active),
        retired=frozenset(r.number for r in view.retired),
        changed_ids=changed_ids,
        before_inputs=staged.get("before_inputs") if case.mode == REOPEN else None,
        live=LiveEvidence(before=ws.before, after=after, canary=auth.canary,
                          changed_text=changed_text,
                          reference_players=reference_players(ws, case),
                          served_keys=served_keys(ws), allowed_changes=frozenset(allowed)),
        extra={"expect": case.expect, "missing_starter_summaries": starters},
        project_instructions=(ws.root / "CLAUDE.md").read_text("utf-8"),
        before_md=(REOPEN_FIXTURES / f"players-{pos}.pre.md").read_text("utf-8")
        if case.mode == REOPEN else None,
    )


def research_files(ws: Workspace, gw: int) -> dict[str, str]:
    analysis = ws.root / f"data/analysis/gw{gw}"
    return {f"data/analysis/gw{gw}/{p.name}": p.read_text("utf-8")
            for p in sorted(analysis.glob("research-*.md"))}


def run_live_case(case: LiveCase, *, judge: bool = False, keep: bool = False,
                  out_root: Path = OUT_ROOT) -> LiveOutcome:
    ws, auth, staged, delta = prepare(case)
    assert ws.replay_dir is not None
    out_dir = out_root / case.id / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    try:
        spec = spec_body((ws.root / SPEC_PATH).read_text("utf-8"))
        prompt = build_prompt(case, ws=str(ws.root), spec=spec, delta=delta)
        stream = run_agent(
            build_claude_argv(prompt, model=MODEL, replay_dir=ws.replay_dir,
                              budget_usd=case.budget_usd),
            cwd=ws.root, replay_dir=ws.replay_dir, stream_path=out_dir / "stream.jsonl")
        records = read_stream(stream)
        transcript = parse_records(records)
        cost = parse_result_cost(records)
        try:
            validate_run(transcript, replay_dir=ws.replay_dir, real_repo=REPO_ROOT,
                         workspace=ws.root)
        except RunInvalid as exc:
            raise RunInvalid(str(exc), cost_usd=cost.total_cost_usd) from exc
        run = player_run(case, ws, transcript, prompt, auth, staged)
        results = run_checks(CHECKS, run, mode="live")
        verdict = None
        if judge:
            verdicts = judging.judge_run(run, research_files(ws, case.gw), _ask(ws))
            results += [_judge_result(item.item, v) for item, v in verdicts]
            verdict = _combined(verdicts)
        write_outputs(out_dir, ws, results, cost, verdict)
        return LiveOutcome(case.id, results, cost, verdict, out_dir)
    finally:
        if not keep:
            shutil.rmtree(ws.root.parent, ignore_errors=True)


def _ask(ws: Workspace):
    return lambda prompt: run_judge(prompt, cwd=ws.root.parent, model=JUDGE_MODEL,
                                    budget_usd=JUDGE_BUDGET_USD)


def _judge_result(item: str, verdict: JudgeVerdict) -> CheckResult:
    status = Status.PASS if verdict.passed else Status.FAIL
    return CheckResult(item, status, verdict.reason or "judge PASS")


def _combined(verdicts: list) -> JudgeVerdict | None:
    if not verdicts:
        return None
    failed = [f"{item.item}: {v.reason}" for item, v in verdicts if not v.passed]
    cost = sum(v.cost_usd or 0.0 for _, v in verdicts)
    return JudgeVerdict(not failed, "; ".join(failed), cost)


def run_judge_calibration(tmp_parent: Path | None = None, *, only: str | None = None
                          ) -> tuple[int, float]:
    """Asks the judge every gold item; exit 1 below the required agreement."""
    import tempfile

    total = 0.0
    results = []
    base = Path(tempfile.mkdtemp(prefix="fpl-eval-judge-", dir=tmp_parent))
    try:
        for gold in judging.gold_items():
            if only is not None and gold["item"] != only:
                continue
            verdict = run_judge(judging.calibration_prompt(gold), cwd=base, model=JUDGE_MODEL,
                                budget_usd=JUDGE_BUDGET_USD)
            total += verdict.cost_usd or 0.0
            results.append((gold, verdict))
            print(f"judge {gold['item']} {gold['label']}: gold {gold['gold']}, judge "
                  f"{'PASS' if verdict.passed else 'FAIL: ' + verdict.reason}")
    finally:
        shutil.rmtree(base, ignore_errors=True)
    agree, j3_total, others, wrong = judging.agreement(results)
    ok = agree >= judging.REQUIRED_J3 and others
    print(f"judge calibration: J3 {agree}/{j3_total} (need {judging.REQUIRED_J3}), J1/J2 "
          f"{'all agree' if others else 'disagree'} → {'PASS' if ok else 'FAIL'}; "
          f"cost ${total:.4f}")
    for line in wrong:
        print(f"  {line}")
    return (0 if ok else 1), total


def run_live_cases(*, case_ids: list[str] | None, repeat: int, judge: bool, keep: bool,
                   full: bool = False) -> int:
    if shutil.which("claude") is None:
        print("claude is not on PATH")
        return 1
    wanted = set(case_ids or ())
    calibrate = judge and (not case_ids or "judge-calibration" in wanted)
    chosen = [c for c in LIVE_CASES
              if (c.id in wanted) or (not case_ids and (full or c.id in DEFAULT_LIVE))]
    code = 0
    if chosen:
        code = run_batch(chosen, lambda case: run_live_case(case, judge=judge, keep=keep),
                         repeat=repeat)
    if calibrate:
        calibration_code, _ = run_judge_calibration()
        code = code or calibration_code
    return code
