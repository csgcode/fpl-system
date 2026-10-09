"""Live finalizer runs: build the case's workspace and recordings, run the
agent headless, then grade the transcript and the workspace."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from evals.finalizer.cases import (
    AGENT,
    CORRECTION,
    LIVE_CASES,
    REPO_ROOT,
    STOP_REOPEN,
    TEAM_ID,
    CaseError,
    LiveCase,
    apply_edit,
    apply_flag_edit,
    synthetic_my_team,
)
from evals.finalizer.checks import CHECKS, FinalizerRun, LiveWorkspace
from evals.finalizer.judge import build_judge_prompt, run_finalizer_judge
from evals.finalizer.prompt import build_prompt
from evals.finalizer.runs import POSITIONS
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
    DummyAuth,
    GitBlob,
    ReplaySpec,
    SourceError,
    Workspace,
    WorkspaceSpec,
    build_workspace,
    make_dummy_auth,
    read_source,
    snapshot,
)
from fpl.freshness import FlagChange, flag_delta
from fpl.models import Bootstrap
from fpl.state import parse_state

OUT_ROOT = REPO_ROOT / "evals" / "out" / AGENT
MODEL = "opus"
SPEC_PATH = "agents/finalizer.md"
BUDGET_USD = 2.50
AUTH_PATH = "data/auth.json"
BACKLOG = "docs/backlog.md"


@dataclass(frozen=True)
class Prepared:
    """A built case: the workspace plus what the graders need to know about
    it before the agent touches it."""

    ws: Workspace
    auth: DummyAuth | None
    files: dict[str, bytes]
    gate: Bootstrap
    truth: tuple[FlagChange, ...]


def case_files(case: LiveCase) -> dict[str, bytes]:
    """The case's data files after its edits. Raises SourceError when an
    input is missing, drifted, or an edit no longer applies."""
    def blob(path: str) -> bytes:
        return read_source(REPO_ROOT, GitBlob(case.commit, path))

    raw = f"data/raw/gw{case.gw}"
    paths = [case.decision("squad-proposal.md"), case.decision("review.md"),
             case.decision("final.md", gw=case.gw - 1), "data/suggestions.md",
             f"{raw}/meta.md", f"{raw}/players-slim.csv",
             *(f"data/analysis/gw{case.gw}/players-{p}.json" for p in POSITIONS)]
    if case.keep_final:
        paths.append(case.decision("final.md"))
    if case.kind == CORRECTION:
        paths.append(case.decision("plan.json"))
    files = {path: blob(path) for path in paths}
    if case.baseline_at is not None:
        files[f"{raw}/bootstrap.json"] = read_source(REPO_ROOT, case.baseline)
        files[f"{raw}/.meta/bootstrap.json"] = json.dumps({
            "fetched_at": case.baseline_at,
            "source_url": "https://fantasy.premierleague.com/api/bootstrap-static/",
        }).encode()
    files["data/entry.json"] = json.dumps({"team_id": TEAM_ID}).encode()
    try:
        for edit in case.edits:
            files[edit.path] = apply_edit(files[edit.path].decode("utf-8"), edit).encode()
    except CaseError as exc:
        raise SourceError(f"{case.id}: {exc}") from exc
    return files


def gate_bytes(case: LiveCase) -> bytes:
    data = read_source(REPO_ROOT, case.gate)
    return apply_flag_edit(data, case.flag_edit) if case.flag_edit else data


def my_team_bytes(case: LiveCase, files: dict[str, bytes], gate: Bootstrap) -> bytes | None:
    """The owned squad is the previous final's; its budget is the case's."""
    if case.budget is None:
        return None
    previous = parse_state(files[case.decision("final.md", gw=case.gw - 1)].decode())
    assert previous.picks is not None
    picks = [(p.id, p.position, p.captain, p.vice) for p in previous.picks.picks]
    now_cost = {p.id: p.now_cost for p in gate.elements}
    return synthetic_my_team(picks, now_cost, round(case.budget * 10),
                             round(previous.bank * 10),
                             free_transfers=previous.free_transfers_banked)


def gate_ids(case: LiveCase) -> set[int]:
    proposal = read_source(REPO_ROOT, GitBlob(case.commit, case.decision("squad-proposal.md")))
    state = parse_state(proposal.decode())
    return {p.id for p in state.picks.picks} if state.picks else set()


def prepare(case: LiveCase, *, tmp_parent: Path | None = None, sync: bool = True) -> Prepared:
    auth = make_dummy_auth() if case.auth else None
    files = case_files(case)
    gate_data = gate_bytes(case)
    gate = Bootstrap.model_validate(json.loads(gate_data))
    extra: dict = {key: source for key, source in case.extra}
    my_team = my_team_bytes(case, files, gate)
    if my_team is not None:
        extra[f"my-team/{TEAM_ID}.json"] = Content(my_team)
    placed: dict = dict(files)
    if auth is not None:
        placed[AUTH_PATH] = auth.content
    replay = ReplaySpec(gw=case.gw, bootstrap=Content(gate_data), summaries=False, extra=extra)
    ws = build_workspace(REPO_ROOT, WorkspaceSpec(code_paths=CODE_PATHS, files=placed), replay,
                         tmp_parent=tmp_parent, sync=sync,
                         now=datetime.fromisoformat(case.gate_now))
    baseline_raw = files.get(f"data/raw/gw{case.gw}/bootstrap.json")
    truth: tuple[FlagChange, ...] = ()
    if baseline_raw is not None and case.kind != CORRECTION:
        baseline = Bootstrap.model_validate(json.loads(baseline_raw))
        truth = tuple(flag_delta(baseline.elements, gate.elements, gate_ids(case)))
    return Prepared(ws, auth, files, gate, truth)


def finalizer_run(case: LiveCase, prepared: Prepared, transcript: Transcript,
                  instructions: str) -> FinalizerRun:
    ws, files = prepared.ws, prepared.files
    after = snapshot(ws.root)

    def text(path: str) -> str | None:
        target = ws.root / path
        return target.read_text("utf-8") if target.is_file() else None

    changed = [p for p in after if ws.before.get(p) != after[p] and p != AUTH_PATH]
    shown = subprocess.run(["git", "-C", str(ws.root), "show", f"HEAD:{BACKLOG}"],
                           capture_output=True, text=True, check=False)
    backlog_before = shown.stdout if shown.returncode == 0 else ""
    backlog_after = text(BACKLOG) or ""
    appended = backlog_after[len(backlog_before):] \
        if backlog_after.startswith(backlog_before) else ""
    workspace = LiveWorkspace(
        before=ws.before, after=after,
        canary=prepared.auth.canary if prepared.auth else None,
        key_names=prepared.auth.key_names if prepared.auth else (),
        changed_text="\n".join(t for p in changed if (t := text(p)) is not None),
        backlog_appended=appended,
    )
    final_path = case.decision("final.md")
    eps: dict[int, float] = {}
    for position in POSITIONS:
        for row in json.loads(files[f"data/analysis/gw{case.gw}/players-{position}.json"]):
            eps[int(row["id"])] = float(row["ep_gw"][0])
    stop = case.stop or (STOP_REOPEN if prepared.truth else None)
    return FinalizerRun(
        transcript=transcript,
        instructions=instructions,
        root=str(ws.root),
        gw=case.gw,
        kind=case.kind,
        proposal=files[case.decision("squad-proposal.md")].decode(),
        review=files[case.decision("review.md")].decode(),
        previous_final=files[case.decision("final.md", gw=case.gw - 1)].decode(),
        final_before=files[final_path].decode() if final_path in files else None,
        final_after=text(final_path),
        suggestions_exists=True,
        stop_expected=stop,
        truth_changes=prepared.truth,
        gate_bootstrap=prepared.gate,
        players_ep=eps,
        workspace=workspace,
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
            validate_run(transcript, replay_dir=ws.replay_dir, real_repo=REPO_ROOT)
        except RunInvalid as exc:
            raise RunInvalid(str(exc), cost_usd=cost.total_cost_usd) from exc
        instructions = f"{prompt}\n\n{(ws.root / SPEC_PATH).read_text('utf-8')}"
        run = finalizer_run(case, prepared, transcript, instructions)
        results = run_checks(CHECKS, run, mode="live")
        verdict = None
        if judge:
            lines = run_finalizer_judge(build_judge_prompt(run), cwd=ws.root.parent)
            verdict = lines.as_verdict()
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
