"""Live squad-optimizer runs: build the case's workspace from its cycle
commit, regenerate players-*.json with the working-tree `fpl ep` (so both
readings come from one code version), run the agent headless on Fable, then
grade against the reference scorer on the workspace's own files."""

from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from evals.harness.checks import Check, CheckResult, Status, run_checks
from evals.harness.live import (
    JudgeVerdict,
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
from evals.harness.shell import call_fpl_invocations
from evals.harness.transcript import Transcript, parse_records
from evals.harness.workspace import (
    CODE_PATHS,
    Content,
    GitBlob,
    SourceError,
    Workspace,
    WorkspaceSpec,
    build_workspace,
    read_source,
    snapshot,
)
from evals.squad_optimizer.cases import (
    AGENT,
    ELE_FEE,
    HAALAND,
    LIVE_CASES,
    REPO_ROOT,
    SCOTT,
    VIEWS,
    LiveCase,
)
from evals.squad_optimizer.checks import (
    BACKLOG,
    CHECKS,
    LiveWorkspace,
    OptimizerRun,
    _cells,
    decision,
    fold,
)
from evals.squad_optimizer.judge import (
    GOLDS,
    MUTATIONS,
    analyst_rows,
    build_judge_prompt,
    run_judge_lines,
)
from evals.squad_optimizer.prompt import build_prompt
from evals.squad_optimizer.runs import case_output
from evals.squad_optimizer.views import POSITIONS, pre_reopen_inputs
from fpl.final_check import parse_ledger
from fpl.models import Bootstrap
from fpl.objective import (
    FREE_GATE,
    Market,
    best_lineup,
    captain_ranking,
    evaluate_plan,
    legal_singles,
    load_views,
)
from fpl.store import SnapshotStore

OUT_ROOT = REPO_ROOT / "evals" / "out" / AGENT
MODEL = "fable"
MODEL_TAG = "fable"
SPEC_PATH = "agents/squad-optimizer.md"
BUDGET_USD = 5.50
CASE_NOW = {4: "2026-09-11T18:40:00+00:00", 5: "2026-09-18T13:00:00+00:00",
            6: "2026-10-09T13:40:00+00:00"}
_S_ROW = re.compile(r"^\|\s*S(\d+)\s*\|")


@dataclass(frozen=True)
class Prepared:
    ws: Workspace
    files: dict[str, bytes]
    bootstrap: Bootstrap
    names: dict[int, str]


def _archive(commit: str, paths: tuple[str, ...]) -> dict[str, bytes]:
    archived = subprocess.run(["git", "-C", str(REPO_ROOT), "archive", commit, *paths],
                              capture_output=True, check=False)
    if archived.returncode != 0:
        raise SourceError(f"git archive {commit} {paths}: {archived.stderr.decode()[-300:]}")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archived.stdout)) as tar:
        for member in tar.getmembers():
            if member.isfile():
                handle = tar.extractfile(member)
                assert handle is not None
                files[member.name] = handle.read()
    return files


def case_files(case: LiveCase) -> dict[str, bytes]:
    """The data the agent sees, before players-*.json is regenerated."""
    gw, raw, analysis = case.gw, f"data/raw/gw{case.gw}", f"data/analysis/gw{case.gw}"
    found = _archive(case.commit, ("data/decisions", "data/retro", analysis, raw,
                                   "data/entry.json", "data/suggestions.md"))
    keep = {}
    for path, data in found.items():
        decided = re.fullmatch(r"data/decisions/gw(\d+)/final\.md", path)
        retro = re.fullmatch(r"data/retro/gw(\d+)\.md", path)
        if decided and int(decided.group(1)) < gw or retro and int(retro.group(1)) < gw:
            keep[path] = data
        elif path.startswith(f"{analysis}/") and (case.research or "/research-" not in path):
            keep[path] = data
        elif re.fullmatch(rf"{raw}/(?:fixtures\.json|meta\.md|players-slim\.csv"
                          rf"|players/.*|\.meta/players/.*)", path):
            keep[path] = data
        elif path == "data/entry.json":
            keep[path] = data
    view = VIEWS[case.view]
    keep[f"{raw}/bootstrap.json"] = read_source(REPO_ROOT, view.bootstrap)
    stamp = re.search(r"bootstrap-(\d{8}T\d{6})_(\d+)Z", view.bootstrap.path)
    fetched = datetime.strptime(stamp.group(1), "%Y%m%dT%H%M%S").replace(tzinfo=UTC) \
        if stamp else datetime.now(UTC)
    keep[f"{raw}/.meta/bootstrap.json"] = json.dumps({
        "fetched_at": fetched.isoformat(),
        "source_url": "https://fantasy.premierleague.com/api/bootstrap-static/"}).encode()
    if view.pre_reopen_def:
        with tempfile.TemporaryDirectory() as tmp:
            current = Path(tmp) / "inputs-DEF.json"
            current.write_bytes(keep[f"{analysis}/inputs-DEF.json"])
            keep[f"{analysis}/inputs-DEF.json"] = json.dumps(pre_reopen_inputs(current),
                                                             indent=1).encode()
    suggestions = truncate_suggestions(found["data/suggestions.md"].decode("utf-8"),
                                       case.suggestions_through)
    keep["data/suggestions.md"] = (suggestions.rstrip("\n") + "\n" + "".join(
        f"{row}\n" for row in case.extra_suggestions)).encode()
    decisions = f"data/decisions/gw{gw}"
    if case.proposal is not None:
        text = case_output(case.proposal)
        if text is None:
            raise SourceError(f"{case.id}: the {case.proposal} proposal cannot be rebuilt")
        keep[f"{decisions}/squad-proposal.md"] = text.encode()
    if case.review is not None:
        keep[f"{decisions}/review.md"] = read_source(REPO_ROOT, case.review)
    if case.stack:
        stack_market(keep, gw)
    return keep


def stack_market(files: dict[str, bytes], gw: int) -> None:
    """X1: E.Le Fée becomes unaffordable for Ndiaye and Scott (5.8 → 6.1; at
    6.0 Scott's £6.0m sale still buys him) and Haaland's GW-N start
    probability drops to 0.80, which brings the captaincy tiebreak into play."""
    path = f"data/raw/gw{gw}/bootstrap.json"
    document = json.loads(files[path])
    for player in document["elements"]:
        if player["id"] == ELE_FEE:
            player["now_cost"] = 61
    files[path] = json.dumps(document).encode()
    path = f"data/analysis/gw{gw}/inputs-FWD.json"
    inputs = json.loads(files[path])
    for row in inputs["players"]:
        if row["id"] == HAALAND:
            vector = list(row.get("p_start_gw") or [row["p_start"]] * 6)
            row["p_start_gw"] = [0.80, *vector[1:]]
    files[path] = json.dumps(inputs, indent=1).encode()


class CaseError(RuntimeError):
    """A perturbed case no longer sets up the situation it tests."""


def views_of(files: dict[str, bytes], gw: int):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for path, data in files.items():
            if path.startswith((f"data/raw/gw{gw}/", f"data/analysis/gw{gw}/")):
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_bytes(data)
        return load_views(SnapshotStore(root / "data/raw"), root / "data/analysis", gw)


def stack_expectations(case: LiveCase, blend, prior) -> dict[str, str]:
    """X1's builder asserts: the captaincy is a tiebreak and Scott's best
    single stays under the free gate. Fails loudly rather than weakening."""
    market = case.market
    plan = evaluate_plan(list(market.sell), [], market, blend, prior)
    squad = list(market.sell)
    for scored in plan.reference:
        squad = [scored.move.into if pid == scored.move.out else pid for pid in squad]
    ranking = captain_ranking(best_lineup(squad, blend, 0), blend, n=2)
    (top, top_ep, _), (second, second_ep, second_p0) = ranking
    if top != HAALAND or top_ep - second_ep >= 0.5 or second_p0 < 0.85:
        raise CaseError(f"{case.id}: captaincy is not a tiebreak: {ranking}")
    scott = [s for s in legal_singles(list(market.sell), market, blend, prior)
             if s.move.out == SCOTT]
    if scott and scott[0].blend >= FREE_GATE:
        raise CaseError(f"{case.id}: Scott's best single {scott[0].blend:+.3f} passes")
    return {"S3": "rejected", "S4": "rejected", "through": "7",
            "captain": blend[second].name}


def truncate_suggestions(text: str, through: int) -> str:
    return "".join(line for line in text.splitlines(keepends=True)
                   if not ((m := _S_ROW.match(line)) and int(m.group(1)) > through))


def regenerate_players(files: dict[str, bytes], gw: int, allow_missing: tuple[int, ...] = ()
                       ) -> dict[str, bytes]:
    """players-*.json from the working-tree `fpl ep` over the case files."""
    from fpl.__main__ import main

    out: dict[str, bytes] = {}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for path, data in files.items():
            if path.startswith((f"data/raw/gw{gw}/", f"data/analysis/gw{gw}/")):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        for position in POSITIONS:
            target = root / f"data/analysis/gw{gw}/players-{position}.json"
            argv = ["--data-root", str(root / "data/raw"), "ep", "--gw", str(gw),
                    "--position", position, "--analysis-root", str(root / "data/analysis"),
                    "--out", str(target), "--history-from", "summaries"]
            if allow_missing:
                argv += ["--allow-missing-ids", ",".join(map(str, allow_missing))]
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()) as err:
                code = main(argv)
            if code != 0:
                raise SourceError(f"fpl ep {position} failed: {err.getvalue()[-400:]}")
            out[f"data/analysis/gw{gw}/players-{position}.json"] = target.read_bytes()
    return out


def prepare(case: LiveCase, *, tmp_parent: Path | None = None, sync: bool = True) -> Prepared:
    files = case_files(case)
    files.update(regenerate_players(files, case.gw, case.allow_missing))
    if case.stack:
        stack_expectations(case, *views_of(files, case.gw))
    bootstrap = Bootstrap.model_validate(json.loads(files[f"data/raw/gw{case.gw}/bootstrap.json"]))
    placed = {path: Content(data) for path, data in files.items()}
    ws = build_workspace(REPO_ROOT, WorkspaceSpec(code_paths=CODE_PATHS, files=placed), None,
                         tmp_parent=tmp_parent, sync=sync,
                         now=datetime.fromisoformat(CASE_NOW[case.gw]))
    names = {p.id: p.web_name for p in bootstrap.elements}
    return Prepared(ws, files, bootstrap, names)


def expectations(case: LiveCase, blend, prior, market: Market) -> dict[str, str]:
    """Case expectations beyond the O-checks, computed on the run's views."""
    if case.stack:
        return stack_expectations(case, blend, prior)
    if case.id.startswith("L1"):
        return {"S1": "standing"}
    if case.id.startswith("L2"):
        ndiaye = next(pid for pid, row in blend.items() if row.name == "Ndiaye")
        squad = list(market.sell)
        moves = [s for s in legal_singles(squad, market, blend, prior)
                 if s.move.out == ndiaye and s.prior >= 0]
        if not moves or moves[0].blend < FREE_GATE:
            return {"S3": "rejected"}
    return {}


def e_case_expectations(run: OptimizerRun) -> CheckResult:
    expected = dict(run.expectations)
    ledger = parse_ledger(run.proposal or "")
    problems = []
    through = expected.pop("through", None)
    if through is not None and (ledger is None or str(ledger.max_s) != through):
        problems.append(f"marker through S{ledger.max_s if ledger else '?'}, want S{through}")
    captain = expected.pop("captain", None)
    made = decision(run)
    if captain is not None and not isinstance(made, str) and made.after.picks:
        chosen = next(p.name for p in made.after.picks.picks if p.captain)
        if fold(chosen) != fold(captain):
            problems.append(f"captain {chosen}, want {captain} (tiebreak)")
    for s_id, status in expected.items():
        row = ledger.row(s_id) if ledger else None
        got = _cells(row)[2].lower() if row else "absent"
        if got != status:
            problems.append(f"{s_id} {got}, want {status}")
        elif status == "rejected" and not re.search(r"\d\.\d", _cells(row)[3]):
            problems.append(f"{s_id} rejected without the rule's numbers")
    if not isinstance(made, str) and made.after.chip:
        graded = any(inv.subcommand == "objective" and inv.option("--chip") == made.after.chip
                     and call.result is not None and "verdict: PASS" in call.result.text
                     for call in run.calls for inv in call_fpl_invocations(call))
        if not graded:
            problems.append(f"chip {made.after.chip} without a passing `objective --chip` run")
    if problems:
        return CheckResult.failed("; ".join(problems))
    shown = ", ".join(f"{s} {v}" for s, v in expected.items()) or "none"
    return CheckResult.passed(f"expectations: {shown}")


LIVE_CHECKS = (*CHECKS, Check("E", e_case_expectations, mode="live"))


def optimizer_run(case: LiveCase, prepared: Prepared, transcript: Transcript,
                  instructions: str) -> OptimizerRun:
    ws, files = prepared.ws, prepared.files
    after = snapshot(ws.root)

    def text(path: str) -> str | None:
        target = ws.root / path
        return target.read_text("utf-8") if target.is_file() else None

    shown = subprocess.run(["git", "-C", str(ws.root), "show", f"HEAD:{BACKLOG}"],
                           capture_output=True, text=True, check=False)
    backlog_before = shown.stdout if shown.returncode == 0 else ""
    backlog_after = text(BACKLOG) or ""
    appended = backlog_after[len(backlog_before):] \
        if backlog_after.startswith(backlog_before) else ""
    served = ""
    if ws.replay_dir is not None and (ws.replay_dir / "served.jsonl").is_file():
        served = (ws.replay_dir / "served.jsonl").read_text("utf-8")
    proposal = f"data/decisions/gw{case.gw}/squad-proposal.md"
    workspace = LiveWorkspace(before=ws.before, after=after, backlog_appended=appended,
                              served=served,
                              archived_before=text(proposal.replace(".md", ".v1.md")))
    blend, prior = load_views(SnapshotStore(ws.root / "data/raw"), ws.root / "data/analysis",
                              case.gw)
    run = OptimizerRun(
        transcript=transcript, instructions=instructions, root=str(ws.root), gw=case.gw,
        kind=case.kind, proposal=text(proposal),
        proposal_before=files.get(proposal, b"").decode() or None,
        previous_final=files[f"data/decisions/gw{case.gw - 1}/final.md"].decode(),
        suggestions=files["data/suggestions.md"].decode(),
        review=None, blend=blend, prior=prior, market=case.market,
        bootstrap=prepared.bootstrap, c20_active=case.gw >= 5, workspace=workspace)
    return replace(run, expectations=expectations(case, blend, prior, case.market))


def model_problem(records: list[dict]) -> str | None:
    models = {r.get("message", {}).get("model") for r in records if r.get("type") == "assistant"}
    models.discard(None)
    wrong = sorted(m for m in models if MODEL_TAG not in m)
    if not models:
        return "no assistant turn recorded a model"
    return f"ran on {', '.join(wrong)}, not {MODEL}" if wrong else None


def run_live_case(case: LiveCase, *, judge: bool = False, calibrated: bool = False,
                  keep: bool = False, out_root: Path = OUT_ROOT) -> LiveOutcome:
    """`calibrated`: the judge agreed with every gold item, so its verdicts
    grade; otherwise they are reported only."""
    prepared = prepare(case)
    ws = prepared.ws
    assert ws.replay_dir is not None
    out_dir = out_root / case.id / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    try:
        prompt = build_prompt(ws.root, case, prepared.names)
        stream = run_agent(
            build_claude_argv(prompt, model=MODEL, replay_dir=ws.replay_dir,
                              budget_usd=BUDGET_USD),
            cwd=ws.root, replay_dir=ws.replay_dir, stream_path=out_dir / "stream.jsonl")
        records = read_stream(stream)
        transcript = parse_records(records)
        cost = parse_result_cost(records)
        problem = model_problem(records)
        if problem:
            raise RunInvalid(problem, cost_usd=cost.total_cost_usd)
        try:
            validate_run(transcript, replay_dir=ws.replay_dir, real_repo=REPO_ROOT,
                         workspace=ws.root)
        except RunInvalid as exc:
            raise RunInvalid(str(exc), cost_usd=cost.total_cost_usd) from exc
        instructions = f"{prompt}\n\n{(ws.root / SPEC_PATH).read_text('utf-8')}"
        run = optimizer_run(case, prepared, transcript, instructions)
        results = run_checks(LIVE_CHECKS, run, mode="live")
        verdict = None
        if judge:
            documents = [row for p in POSITIONS for row in json.loads(
                prepared.files[f"data/analysis/gw{case.gw}/players-{p}.json"])]
            lines = run_judge_lines(build_judge_prompt(run, analyst_rows(documents)),
                                    cwd=ws.root.parent)
            results += [CheckResult(key, _judge_status(lines.status(key), calibrated),
                                    lines.verdicts.get(key, ("MISSING", ""))[1]
                                    + ("" if calibrated else " (uncalibrated: report only)"))
                        for key in ("J1", "J2")]
            bad = [k for k in ("J1", "J2") if lines.status(k) != "PASS"]
            verdict = JudgeVerdict(not bad, "; ".join(f"{k} {lines.status(k)}" for k in bad),
                                   lines.cost_usd)
        write_outputs(out_dir, ws, results, cost, verdict)
        return LiveOutcome(case.id, results, cost, verdict, out_dir)
    finally:
        if not keep:
            shutil.rmtree(ws.root.parent, ignore_errors=True)


def _judge_status(status: str, calibrated: bool) -> Status:
    if not calibrated:
        return Status.NA
    return Status.PASS if status == "PASS" else Status.FAIL


def calibrate_judge() -> tuple[bool, float]:
    """Runs every gold item; (all agree, cost)."""
    from evals.squad_optimizer.cases import replay_case
    from evals.squad_optimizer.runs import git_text, replay_run

    total = 0.0
    agree = True
    base = Path(tempfile.mkdtemp(prefix="so-judge-")).resolve()
    try:
        for gold in GOLDS:
            run = replay_run(replay_case(gold.case))
            view = VIEWS[replay_case(gold.case).view]
            documents = []
            for position in POSITIONS:
                text = git_text(GitBlob(view.commit, f"data/analysis/gw{view.gw}/players-"
                                                    f"{position}.json"))
                documents += json.loads(text) if text else []
            proposal = run.proposal or ""
            if gold.mutate:
                proposal = MUTATIONS[gold.mutate](proposal)
            lines = run_judge_lines(build_judge_prompt(run, analyst_rows(documents),
                                                       proposal=proposal), cwd=base)
            total += lines.cost_usd or 0.0
            got = {k: lines.status(k) for k in ("J1", "J2")}
            ok = all(got[k] == v for k, v in gold.expected.items())
            agree &= ok
            print(f"judge gold {gold.label}: {got} want {dict(gold.expected)} "
                  f"{'agree' if ok else 'DISAGREE'}"
                  + "".join(f"\n    {k}: {r}" for k, (s, r) in lines.verdicts.items() if r))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print(f"judge calibration: {'all agree' if agree else 'DISAGREES'}; ${total:.4f}")
    return agree, total


def run_live_cases(*, case_ids: list[str] | None, repeat: int, judge: bool, keep: bool,
                   full: bool = False) -> int:
    if shutil.which("claude") is None:
        print("claude is not on PATH")
        return 1
    calibrated = calibrate_judge()[0] if judge else False
    chosen = [c for c in LIVE_CASES if (c.id in case_ids if case_ids else c.default or full)]
    return run_batch(chosen, lambda case: run_live_case(
        case, judge=judge, calibrated=calibrated, keep=keep), repeat=repeat)
