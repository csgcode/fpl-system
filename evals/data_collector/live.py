"""Live data-collector runs: build the workspace and recordings for a case,
run the agent headless, then grade the transcript and the workspace."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from evals.data_collector.cases import (
    AGENT,
    BOOTSTRAP_PINS,
    FIXTURE_PINS,
    LIVE_CASES,
    MY_TEAM_FIXTURE,
    REPLAY_NOW,
    REPO_ROOT,
    LiveCase,
)
from evals.data_collector.checks import CHECKS, CollectorRun, LiveWorkspace
from evals.data_collector.judge import build_judge_prompt
from evals.data_collector.prompt import build_prompt
from evals.harness.checks import run_checks
from evals.harness.live import (
    LiveOutcome,
    RunCost,
    RunInvalid,
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
    DummyAuth,
    ReplaySpec,
    SourceError,
    Workspace,
    WorkspaceSpec,
    build_workspace,
    make_dummy_auth,
    snapshot,
)
from fpl.models import Bootstrap, is_shortlisted

OUT_ROOT = REPO_ROOT / "evals" / "out" / AGENT
MODEL = "haiku"
SPEC_PATH = "agents/data-collector.md"


def workspace_spec(case: LiveCase, auth: DummyAuth | None, *, now: datetime) -> WorkspaceSpec:
    files: dict = dict(case.previous_files())
    files["data/entry.json"] = json.dumps({"team_id": case.team_id}).encode()
    if auth is not None:
        files["data/auth.json"] = auth.content
    if case.preseed:
        raw = f"data/raw/gw{case.gw}"
        files[f"{raw}/bootstrap.json"] = BOOTSTRAP_PINS[case.gw]
        files[f"{raw}/.meta/bootstrap.json"] = json.dumps({
            "fetched_at": (now - timedelta(hours=1)).isoformat(),
            "source_url": "https://fantasy.premierleague.com/api/bootstrap-static/",
        }).encode()
    return WorkspaceSpec(code_paths=CODE_PATHS, files=files)


def replay_spec(case: LiveCase) -> ReplaySpec:
    return ReplaySpec(
        gw=case.gw,
        bootstrap=BOOTSTRAP_PINS[case.gw],
        fixtures=FIXTURE_PINS[case.gw],
        team_id=case.team_id,
        my_team=MY_TEAM_FIXTURE if case.team_id is not None else None,
        errors=dict(case.errors),
    )


def claude_available() -> bool:
    return shutil.which("claude") is not None


def prepare(case: LiveCase, *, tmp_parent: Path | None = None) -> tuple[Workspace, DummyAuth | None]:
    """Raises SourceError when a pinned source is missing or has drifted."""
    auth = make_dummy_auth() if case.auth else None
    now = REPLAY_NOW[case.gw]
    ws = build_workspace(REPO_ROOT, workspace_spec(case, auth, now=now),
                         replay_spec(case), tmp_parent=tmp_parent, now=now)
    if case.errors:
        _assert_injected_ids_are_shortlisted(ws, case)
    return ws, auth


def run_live_case(case: LiveCase, *, judge: bool = False, keep: bool = False,
                  out_root: Path = OUT_ROOT) -> LiveOutcome:
    ws, auth = prepare(case)
    assert ws.replay_dir is not None
    out_dir = out_root / case.id / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    try:
        prompt = build_prompt(ws.root, case,
                              spec_body((ws.root / SPEC_PATH).read_text("utf-8")))
        stream = run_agent(build_claude_argv(prompt, model=MODEL, replay_dir=ws.replay_dir),
                           cwd=ws.root, replay_dir=ws.replay_dir,
                           stream_path=out_dir / "stream.jsonl")
        records = read_stream(stream)
        transcript = parse_records(records)
        cost = parse_result_cost(records)
        try:
            validate_run(transcript, replay_dir=ws.replay_dir, real_repo=REPO_ROOT)
        except RunInvalid as exc:
            raise RunInvalid(str(exc), cost_usd=cost.total_cost_usd) from exc
        run = collector_run(case, ws, transcript, prompt, auth)
        results = run_checks(CHECKS, run, mode="live")
        verdict = run_judge(build_judge_prompt(transcript), cwd=ws.root) if judge else None
        write_outputs(out_dir, ws, results, cost, verdict)
        return LiveOutcome(case.id, results, cost, verdict, out_dir)
    finally:
        if not keep:
            shutil.rmtree(ws.root.parent, ignore_errors=True)


def collector_run(case: LiveCase, ws: Workspace, transcript: Transcript, prompt: str,
                  auth: DummyAuth | None) -> CollectorRun:
    assert ws.replay_dir is not None
    meta_path = ws.root / f"data/raw/gw{case.gw}/meta.md"
    backlog = subprocess.run(["git", "-C", str(ws.root), "show", "HEAD:docs/backlog.md"],
                             capture_output=True, text=True, check=False)
    workspace = LiveWorkspace(
        root=ws.root,
        before=ws.before,
        after=snapshot(ws.root),
        canary=auth.canary if auth else None,
        credential_keys=auth.key_names if auth else (),
        error_keys=tuple(case.errors),
        backlog_before=backlog.stdout if backlog.returncode == 0 else None,
    )
    return CollectorRun(
        transcript=transcript,
        instructions=prompt,
        root=str(ws.root),
        gw=case.gw,
        team_id=case.team_id,
        auth_present=case.auth,
        meta_md=meta_path.read_text("utf-8") if meta_path.is_file() else None,
        previous_gw_truth=_previous_gw_truth(ws.replay_dir / "bootstrap-static.json"),
        workspace=workspace,
    )


def run_live_cases(*, case_ids: list[str] | None, repeat: int, judge: bool, keep: bool) -> int:
    if not claude_available():
        print("claude is not on PATH")
        return 1
    chosen = [c for c in LIVE_CASES if not case_ids or c.id in case_ids]
    return run_batch(chosen, lambda case: run_live_case(case, judge=judge, keep=keep),
                     repeat=repeat)


def smoke(tmp_dir: Path) -> tuple[str | None, Transcript, RunCost]:
    """Asks a headless haiku session to echo FPL_REPLAY_DIR: proves the
    stream-json shape and that the variable reaches the Bash tool."""
    replay = tmp_dir / "replay"
    replay.mkdir(parents=True, exist_ok=True)
    argv = build_claude_argv(
        "Run exactly this Bash command and nothing else: echo \"$FPL_REPLAY_DIR\"",
        model=MODEL, replay_dir=replay, budget_usd=0.10)
    stream = run_agent(argv, cwd=tmp_dir, replay_dir=replay,
                       stream_path=tmp_dir / "smoke.jsonl")
    records = read_stream(stream)
    transcript = parse_records(records)
    echoed = next((c.result.text.strip() for c in transcript.calls
                   if c.name == "Bash" and c.result is not None), None)
    return echoed, transcript, parse_result_cost(records)


def _previous_gw_truth(bootstrap_path: Path) -> tuple[bool, bool] | None:
    bootstrap = Bootstrap.model_validate_json(bootstrap_path.read_text("utf-8"))
    current = next((e for e in bootstrap.events if e.is_current), None)
    return (current.finished, current.data_checked) if current else None


def _assert_injected_ids_are_shortlisted(ws: Workspace, case: LiveCase) -> None:
    assert ws.replay_dir is not None
    bootstrap = Bootstrap.model_validate_json(
        (ws.replay_dir / "bootstrap-static.json").read_text("utf-8"))
    shortlisted = {p.id for p in bootstrap.elements if is_shortlisted(p)}
    for key in case.errors:
        if key.startswith("element-summary/"):
            player_id = int(key.rsplit("/", 1)[1])
            if player_id not in shortlisted:
                raise SourceError(f"injected id {player_id} is not shortlisted in gw{case.gw}")
