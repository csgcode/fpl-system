"""Live retro-analyst runs: build the case's workspace and recordings, run
the agent headless, then grade the transcript and the workspace."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from evals.harness.checks import run_checks
from evals.harness.live import (
    LiveOutcome,
    RunInvalid,
    build_claude_argv,
    parse_result_cost,
    read_stream,
    run_agent,
    run_batch,
    validate_run,
    write_outputs,
)
from evals.harness.transcript import Transcript, parse_records
from evals.harness.workspace import (
    CODE_PATHS,
    Content,
    GitBlob,
    ReplaySpec,
    Workspace,
    WorkspaceSpec,
    build_workspace,
    read_source,
    snapshot,
)
from evals.retro_analyst.cases import (
    AGENT,
    ANALYSIS_BOOTSTRAPS,
    ARITHMETIC_A3,
    BIG_FINAL,
    C21_RULE,
    LIVE_CASES,
    NOT_CHECKED,
    NULL_TEAM,
    PICKS_DIFFER,
    REPO_ROOT,
    TEAM_ID,
    LiveCase,
)
from evals.retro_analyst.checks import (
    CHECKS,
    LiveWorkspace,
    RetroRun,
    previous_statuses,
)
from evals.retro_analyst.prompt import build_prompt
from fpl.calibrate import CalibrationReport
from fpl.corrections import is_closed

OUT_ROOT = REPO_ROOT / "evals" / "out" / AGENT
MODEL = "opus"
SPEC_PATH = "agents/retro-analyst.md"
BUDGET_USD = 3.00
BACKLOG = "docs/backlog.md"
POSITIONS = ("GKP", "DEF", "MID", "FWD")
EXTENDED_RATIONALE = "## Rationale (extended)"
_PADDING = ("The optimizer weighed every legal single move against the six-gameweek horizon, "
            "compared the blended and prior-only readings, and kept the bench order that "
            "protects the defensive floor. The reviewer agreed with the ordering and asked "
            "for no revision. ")
PADDING_BYTES = 40_000


@dataclass(frozen=True)
class Prepared:
    ws: Workspace
    case: LiveCase
    files: dict[str, bytes]
    recordings: dict[str, bytes]
    truth: CalibrationReport


def _blob(case: LiveCase, path: str) -> bytes:
    return read_source(REPO_ROOT, GitBlob(case.commit, path))


def truth_ledger(case: LiveCase) -> CalibrationReport:
    raw = _blob(case, f"data/retro/gw{case.round}-calibration.json")
    return CalibrationReport.model_validate(json.loads(raw))


def _archive_time(source_path: str) -> str:
    stamp = re.search(r"bootstrap-(\d{8}T\d{6})_(\d+)Z", source_path)
    assert stamp is not None, source_path
    moment = datetime.strptime(stamp[1], "%Y%m%dT%H%M%S").replace(tzinfo=UTC)
    return moment.replace(microsecond=int(stamp[2])).isoformat()


def uncheck_round(bootstrap: bytes, round_: int) -> bytes:
    document = json.loads(bootstrap)
    events = [e for e in document["events"] if e["id"] == round_]
    events[0]["data_checked"] = False
    return json.dumps(document).encode()


def insert_before(text: str, anchor: str, block: str) -> str:
    if text.count(anchor) != 1:
        raise ValueError(f"anchor occurs {text.count(anchor)} times: {anchor!r}")
    return text.replace(anchor, f"{block}\n\n{anchor}")


def padded_final(final: str) -> str:
    repeats = PADDING_BYTES // len(_PADDING.encode()) + 1
    prose = "\n\n".join([_PADDING] * repeats)
    return insert_before(final, "## STATE", f"{EXTENDED_RATIONALE}\n\n{prose}")


def case_files(case: LiveCase) -> dict[str, bytes]:
    """The case's data files after its perturbation. Never the retro the run
    must write, its ledger, or credentials."""
    m, n = case.round, case.gw
    paths = [f"data/decisions/gw{m}/final.md",
             *(f"data/analysis/gw{m}/players-{p}.json" for p in POSITIONS)]
    for k in range(1, m):
        paths += [f"data/retro/gw{k}.md", f"data/retro/gw{k}-calibration.json"]
    placed = {path: _blob(case, path) for path in paths}
    pin = ANALYSIS_BOOTSTRAPS[n]
    bootstrap = read_source(REPO_ROOT, pin)
    if case.perturbation == NOT_CHECKED:
        bootstrap = uncheck_round(bootstrap, m)
    placed[f"data/raw/gw{n}/bootstrap.json"] = bootstrap
    placed[f"data/raw/gw{n}/.meta/bootstrap.json"] = json.dumps({
        "fetched_at": _archive_time(pin.path),
        "source_url": "https://fantasy.premierleague.com/api/bootstrap-static/",
    }).encode()
    team = None if case.perturbation == NULL_TEAM else TEAM_ID
    placed["data/entry.json"] = json.dumps({"team_id": team}).encode()
    if case.perturbation == ARITHMETIC_A3:
        latest = f"data/retro/gw{m - 1}.md"
        placed[latest] = insert_before(placed[latest].decode(), "## Running calibration stats",
                                       C21_RULE).encode()
    if case.perturbation == BIG_FINAL:
        final = f"data/decisions/gw{m}/final.md"
        placed[final] = padded_final(placed[final].decode()).encode()
    return placed


def swap_armbands(picks: bytes, captain: int, vice: int) -> bytes:
    document = json.loads(picks)
    for pick in document["picks"]:
        element = pick["element"]
        pick["is_captain"] = element == captain
        pick["is_vice_captain"] = element == vice
        pick["multiplier"] = 2 if element == captain else (1 if pick["multiplier"] else 0)
    return json.dumps(document).encode()


def fielded_picks(picks: bytes) -> tuple[frozenset[int], int, int]:
    rows = json.loads(picks)["picks"]
    return (frozenset(p["element"] for p in rows),
            next(p["element"] for p in rows if p["is_captain"]),
            next(p["element"] for p in rows if p["is_vice_captain"]))


def recording_bytes(case: LiveCase, files: dict[str, bytes]) -> dict[str, bytes]:
    """The `extra` recordings, keyed as the replay serves them."""
    m, n = case.round, case.gw
    raw = f"data/raw/gw{n}"
    picks_key = f"entry/{TEAM_ID}/event/{m}/picks.json"
    served = {
        f"event/{m}/live.json": _blob(case, f"{raw}/event-live-e{m}.json"),
        picks_key: _blob(case, f"{raw}/picks-{TEAM_ID}-e{m}.json"),
        f"entry/{TEAM_ID}/history.json": _blob(case, f"{raw}/entry-history-{TEAM_ID}.json"),
        "fixtures.json": _blob(case, f"{raw}/fixtures.json"),
    }
    if case.perturbation == PICKS_DIFFER:
        served[picks_key] = swap_armbands(served[picks_key], captain=4, vice=411)
    return served


def prepare(case: LiveCase, *, tmp_parent: Path | None = None, sync: bool = True) -> Prepared:
    files = case_files(case)
    served = recording_bytes(case, files)
    truth = truth_ledger(case)
    ids = {line.id for line in truth.players}
    if truth.squad is not None:
        ids |= {line.id for line in truth.squad.players}
    replay = ReplaySpec(
        gw=case.gw, bootstrap=Content(files[f"data/raw/gw{case.gw}/bootstrap.json"]),
        summary_ids=tuple(sorted(ids)), summary_min_gw=case.gw,
        extra={key: Content(data) for key, data in served.items()},
    )
    ws = build_workspace(REPO_ROOT, WorkspaceSpec(code_paths=CODE_PATHS, files=files), replay,
                         tmp_parent=tmp_parent, sync=sync,
                         now=datetime.fromisoformat(case.now))
    return Prepared(ws, case, files, served, truth)


def check_validity(prepared: Prepared) -> None:
    """A ledger the run wrote must be the committed one: otherwise the
    replay is not faithful and the run grades nothing."""
    path = prepared.ws.root / f"data/retro/gw{prepared.case.round}-calibration.json"
    if not path.is_file():
        return
    written = json.loads(path.read_text("utf-8"))
    if written != json.loads(prepared.truth.model_dump_json()):
        raise RunInvalid(f"the workspace ledger {path.name} differs from the committed one")


def retro_run(prepared: Prepared, transcript: Transcript, instructions: str) -> RetroRun:
    ws, case, files = prepared.ws, prepared.case, prepared.files
    after = snapshot(ws.root)
    retro_path = ws.root / f"data/retro/gw{case.round}.md"
    shown = subprocess.run(["git", "-C", str(ws.root), "show", f"HEAD:{BACKLOG}"],
                           capture_output=True, text=True, check=False)
    before = shown.stdout if shown.returncode == 0 else ""
    now = (ws.root / BACKLOG).read_text("utf-8") if (ws.root / BACKLOG).is_file() else ""
    appended = now[len(before):] if now.startswith(before) else now
    prior = {Path(p).name: data.decode() for p, data in files.items()
             if re.fullmatch(r"data/retro/gw\d+\.md", p)}
    c9 = previous_statuses(prior).get(9)
    picks = prepared.recordings[f"entry/{TEAM_ID}/event/{case.round}/picks.json"]
    return RetroRun(
        transcript=transcript,
        instructions=instructions,
        root=str(ws.root),
        round=case.round,
        retro=retro_path.read_text("utf-8") if retro_path.is_file() else None,
        ledger=prepared.truth,
        final_md=files[f"data/decisions/gw{case.round}/final.md"].decode(),
        prior_retros=prior,
        backlog_appended=appended,
        fielded=fielded_picks(picks),
        workspace=LiveWorkspace(ws.before, after),
        expect_c9_retired=c9 is not None and not is_closed(c9[0]),
        expect_refusal=case.perturbation == NOT_CHECKED,
        null_team=case.perturbation == NULL_TEAM,
    )


def run_live_case(case: LiveCase, *, judge: bool = False, keep: bool = False,
                  out_root: Path = OUT_ROOT) -> LiveOutcome:
    prepared = prepare(case)
    ws = prepared.ws
    assert ws.replay_dir is not None
    out_dir = out_root / case.id / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    try:
        prompt = build_prompt(ws.root, case)
        stream = run_agent(
            build_claude_argv(prompt, model=MODEL, replay_dir=ws.replay_dir,
                              budget_usd=BUDGET_USD),
            cwd=ws.root, replay_dir=ws.replay_dir, stream_path=out_dir / "stream.jsonl")
        records = read_stream(stream)
        transcript = parse_records(records)
        cost = parse_result_cost(records)
        try:
            validate_run(transcript, replay_dir=ws.replay_dir, real_repo=REPO_ROOT,
                         workspace=ws.root)
            check_validity(prepared)
        except RunInvalid as exc:
            raise RunInvalid(str(exc), cost_usd=cost.total_cost_usd) from exc
        instructions = f"{prompt}\n\n{(ws.root / SPEC_PATH).read_text('utf-8')}"
        run = retro_run(prepared, transcript, instructions)
        results = run_checks(CHECKS, run, mode="live")
        verdict = None
        if judge:
            from evals.retro_analyst.judge import judge_run

            verdict = judge_run(run, cwd=ws.root.parent)
        if run.retro is not None:
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"gw{case.round}.md").write_text(run.retro, "utf-8")
        write_outputs(out_dir, ws, results, cost, verdict)
        return LiveOutcome(case.id, results, cost, verdict, out_dir)
    finally:
        if not keep:
            shutil.rmtree(ws.root.parent, ignore_errors=True)


def run_live_cases(*, case_ids: list[str] | None, repeat: int, judge: bool, keep: bool) -> int:
    if shutil.which("claude") is None:
        print("claude is not on PATH")
        return 1
    chosen = [c for c in LIVE_CASES if (c.id in case_ids if case_ids else c.default)]
    return run_batch(chosen, lambda case: run_live_case(case, judge=judge, keep=keep),
                     repeat=repeat)
