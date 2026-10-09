"""Live team-executor runs: stage the case's workspace and fake server, run
the agent headless, then grade it against what the CLI and the fake server
recorded. Nothing reaches FPL: the CLI runs in replay mode against the fake,
with credentials that are only a canary."""

from __future__ import annotations

import json
import shutil
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
from evals.team_executor.cases import (
    AGENT,
    LIVE_CASES,
    REPO_ROOT,
    CaseError,
    LiveCase,
    audit_payload,
)
from evals.team_executor.checks import CHECKS, ExecutorRun, LiveFacts
from evals.team_executor.judge import build_judge_prompt
from evals.team_executor.stage import approved_id, case_now, seed_server, workspace_files
from fpl.fake_server import POSTS_LOG

OUT_ROOT = REPO_ROOT / "evals" / "out" / AGENT
MODEL = "haiku"
JUDGE_MODEL = "haiku"
SPEC_PATH = "agents/team-executor.md"
MODELS_FILE = "models.json"
# auth-import rewrites these with the canary by design.
CREDENTIAL_FILES = frozenset({"data/auth.json", "curl-request"})

TEMPLATE = """{spec}

## Run facts
N = {gw}
Capture: {capture}
Approval: {approval}
Run from the repo root (the current directory). Never run `git commit`."""


@dataclass(frozen=True)
class Prepared:
    ws: Workspace
    auth: DummyAuth
    prompt: str


def approval_block(case: LiveCase, approved: str | None) -> str:
    if case.approval is None:
        return "none"
    return (f'\n    User\'s words (verbatim): "{case.approval.words}"\n'
            f"    Approved transfer id: {approved or 'none'}")


def build_prompt(case: LiveCase, body: str, approved: str | None) -> str:
    return TEMPLATE.format(spec=body.rstrip(), gw=case.gw,
                           capture="yes" if case.capture else "no",
                           approval=approval_block(case, approved))


def prepare(case: LiveCase, *, tmp_parent: Path | None = None, sync: bool = True) -> Prepared:
    """Raises SourceError when a committed input is missing."""
    auth = make_dummy_auth()
    try:
        files: dict = workspace_files(case, auth.content.data, auth.canary)
        approved = approved_id(case)
    except CaseError as exc:
        raise SourceError(str(exc)) from exc
    files["data/auth.json"] = auth.content
    ws = build_workspace(REPO_ROOT, WorkspaceSpec(code_paths=CODE_PATHS, files=files), None,
                         tmp_parent=tmp_parent, sync=sync, now=case_now(case))
    assert ws.replay_dir is not None
    seed_server(case, ws.replay_dir)
    body = spec_body((ws.root / SPEC_PATH).read_text("utf-8"))
    return Prepared(ws, auth, build_prompt(case, body, approved))


def live_facts(case: LiveCase, prepared: Prepared) -> LiveFacts:
    ws = prepared.ws
    assert ws.replay_dir is not None
    after = snapshot(ws.root)
    changes = diff(ws.before, after)
    protected = {case.plan, case.final, "data/entry.json"}
    touched = [*changes.added, *changes.modified]
    texts = {path: (ws.root / path).read_text("utf-8", errors="replace")
             for path in touched if path not in CREDENTIAL_FILES}
    posts_path = ws.replay_dir / POSTS_LOG
    if posts_path.is_file():
        texts[POSTS_LOG] = posts_path.read_text("utf-8")
    run_log = ws.root / "data" / "executor" / f"gw{case.gw}" / "runs.jsonl"
    return LiveFacts(
        canary=prepared.auth.canary,
        runs=tuple(_jsonl(run_log)),
        posts=tuple(_jsonl(posts_path)),
        expected_posts=tuple(_expected_post(e) for e in case.expected_posts),
        expected_next=case.next,
        protected_changed=tuple(sorted(
            p for p in protected if ws.before.get(p) != after.get(p))),
        leaked_into=tuple(sorted(p for p, text in texts.items()
                                 if prepared.auth.canary in text)),
    )


def _expected_post(expected) -> dict:
    payload = dict(expected.payload)
    if expected.audit is not None:
        payload = audit_payload(*expected.audit)
    return {"kind": expected.kind, "payload": payload}


def _jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


def executor_run(case: LiveCase, prepared: Prepared, transcript: Transcript) -> ExecutorRun:
    return ExecutorRun(transcript=transcript, instructions=prepared.prompt,
                       root=str(prepared.ws.root), gw=case.gw,
                       required_calls=case.required_calls, plan_missing=case.remove_plan,
                       live=live_facts(case, prepared))


def resolved_models(records: list[dict]) -> list[str]:
    found = [r.get("model") for r in records if r.get("type") == "system" and r.get("model")]
    found += [r.get("message", {}).get("model") for r in records
              if r.get("type") == "assistant" and r.get("message", {}).get("model")]
    return list(dict.fromkeys(found))


def run_live_case(case: LiveCase, *, judge: bool = False, keep: bool = False,
                  out_root: Path = OUT_ROOT) -> LiveOutcome:
    prepared = prepare(case)
    ws = prepared.ws
    assert ws.replay_dir is not None
    out_dir = out_root / case.id / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    try:
        stream = run_agent(
            build_claude_argv(prepared.prompt, model=MODEL, replay_dir=ws.replay_dir),
            cwd=ws.root, replay_dir=ws.replay_dir, stream_path=out_dir / "stream.jsonl")
        records = read_stream(stream)
        transcript = parse_records(records)
        cost = parse_result_cost(records)
        try:
            validate_run(transcript, replay_dir=ws.replay_dir, real_repo=REPO_ROOT)
        except RunInvalid as exc:
            raise RunInvalid(str(exc), cost_usd=cost.total_cost_usd) from exc
        run = executor_run(case, prepared, transcript)
        results = run_checks(CHECKS, run, mode="live")
        verdict = (run_judge(build_judge_prompt(transcript, prepared.prompt),
                             cwd=ws.root.parent, model=JUDGE_MODEL) if judge else None)
        write_outputs(out_dir, ws, results, cost, verdict)
        (out_dir / MODELS_FILE).write_text(json.dumps(resolved_models(records)), "utf-8")
        return LiveOutcome(case.id, results, cost, verdict, out_dir)
    finally:
        if not keep:
            shutil.rmtree(ws.root.parent, ignore_errors=True)


def run_live_cases(*, case_ids: list[str] | None, repeat: int, judge: bool, keep: bool) -> int:
    if shutil.which("claude") is None:
        print("claude is not on PATH")
        return 1
    chosen = [c for c in LIVE_CASES if not case_ids or c.id in case_ids]
    return run_batch(chosen, lambda case: run_live_case(case, judge=judge, keep=keep),
                     repeat=repeat)
