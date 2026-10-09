"""Live plan-builder runs: build the case's workspace, record what the CLI
itself produces there (the reference plan), run the agent headless, grade."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from evals.harness.checks import run_checks
from evals.harness.live import (
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
    DummyAuth,
    SourceError,
    Workspace,
    WorkspaceSpec,
    build_workspace,
    diff,
    make_dummy_auth,
    snapshot,
)
from evals.plan_builder.cases import (
    AGENT,
    LIVE_CASES,
    REPO_ROOT,
    CaseError,
    LiveCase,
    case_files,
)
from evals.plan_builder.checks import CHECKS, LiveWorkspace, PlanBuilderRun
from evals.plan_builder.judge import build_judge_prompt, judged

OUT_ROOT = REPO_ROOT / "evals" / "out" / AGENT
MODEL = "haiku"
JUDGE_MODEL = "haiku"
SPEC_PATH = "agents/plan-builder.md"
REFERENCE_FILE = "reference-plan.json"
CLI_TIMEOUT_S = 120

TEMPLATE = """You are agent A8 — Plan Builder for the FPL agent system.
N = {gw}. Run from the repo root (the current directory). Never run `git commit`.

{spec}"""


def build_prompt(case: LiveCase, body: str) -> str:
    return TEMPLATE.format(gw=case.gw, spec=body)


def workspace_spec(case: LiveCase, auth: DummyAuth | None) -> WorkspaceSpec:
    try:
        files: dict = dict(case_files(REPO_ROOT, case))
    except CaseError as exc:
        raise SourceError(str(exc)) from exc
    if auth is not None:
        files["data/auth.json"] = auth.content
    return WorkspaceSpec(code_paths=CODE_PATHS, files=files)


def replay_now(spec: WorkspaceSpec, case: LiveCase) -> datetime:
    """The moment the case's bootstrap was fetched, from its sidecar."""
    meta = spec.files[f"data/raw/gw{case.gw}/.meta/bootstrap.json"]
    assert isinstance(meta, bytes)
    return datetime.fromisoformat(json.loads(meta)["fetched_at"])


def prepare(case: LiveCase, *, tmp_parent: Path | None = None
            ) -> tuple[Workspace, DummyAuth, bytes | None]:
    """Raises SourceError when an input is missing, an edit no longer
    applies, or the CLI's own result no longer matches the case."""
    auth = make_dummy_auth()
    spec = workspace_spec(case, auth)
    ws = build_workspace(REPO_ROOT, spec, None, tmp_parent=tmp_parent,
                         now=replay_now(spec, case))
    return ws, auth, _reference_plan(ws, case)


def read_plan(root: Path, case: LiveCase) -> bytes | None:
    path = root / case.plan
    return path.read_bytes() if path.is_file() else None


def run_live_case(case: LiveCase, *, judge: bool = False, keep: bool = False,
                  out_root: Path = OUT_ROOT) -> LiveOutcome:
    ws, auth, reference = prepare(case)
    assert ws.replay_dir is not None
    out_dir = out_root / case.id / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    try:
        prompt = build_prompt(case, spec_body((ws.root / SPEC_PATH).read_text("utf-8")))
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
        run = plan_builder_run(case, ws, transcript, prompt, auth, reference)
        results = run_checks(CHECKS, run, mode="live")
        verdict = (run_judge(build_judge_prompt(transcript, prompt), cwd=ws.root.parent,
                             model=JUDGE_MODEL)
                   if judge and judged(case) else None)
        write_outputs(out_dir, ws, results, cost, verdict)
        return LiveOutcome(case.id, results, cost, verdict, out_dir)
    finally:
        if not keep:
            shutil.rmtree(ws.root.parent, ignore_errors=True)


def plan_builder_run(case: LiveCase, ws: Workspace, transcript: Transcript, prompt: str,
                     auth: DummyAuth, reference: bytes | None) -> PlanBuilderRun:
    after = snapshot(ws.root)
    changes = diff(ws.before, after)
    changed_text = "\n".join(
        (ws.root / path).read_text("utf-8", errors="replace")
        for path in (*changes.added, *changes.modified) if (ws.root / path).is_file()
    )
    workspace = LiveWorkspace(before=ws.before, after=after, canary=auth.canary,
                              plan_json=read_plan(ws.root, case), reference_plan=reference,
                              changed_text=changed_text)
    return PlanBuilderRun(transcript=transcript, instructions=prompt, root=str(ws.root),
                          gw=case.gw, workspace=workspace)


def run_live_cases(*, case_ids: list[str] | None, repeat: int, judge: bool, keep: bool) -> int:
    if shutil.which("claude") is None:
        print("claude is not on PATH")
        return 1
    chosen = [c for c in LIVE_CASES if not case_ids or c.id in case_ids]
    return run_batch(chosen, lambda case: run_live_case(case, judge=judge, keep=keep),
                     repeat=repeat)


def _reference_plan(ws: Workspace, case: LiveCase) -> bytes | None:
    """What the CLI writes in this workspace, set aside outside it before the
    agent runs; None when the CLI refuses."""
    assert ws.replay_dir is not None
    target = ws.root.parent / REFERENCE_FILE
    completed = subprocess.run(
        ["uv", "run", "python", "-m", "fpl", "plan", "--gw", str(case.gw),
         "--out", str(target)],
        cwd=ws.root, env=agent_env(ws.replay_dir),
        capture_output=True, text=True, timeout=CLI_TIMEOUT_S, check=False,
    )
    if completed.returncode != case.expect.exit_code:
        raise SourceError(
            f"{case.id}: the CLI exited {completed.returncode}, the case expects "
            f"{case.expect.exit_code}: {completed.stderr.strip()[-300:]}")
    return target.read_bytes() if completed.returncode == 0 else None
