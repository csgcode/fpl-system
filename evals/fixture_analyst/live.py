"""Live fixture-analyst runs: build the case's workspace, record what
`fpl fixtures-rate` itself writes there (the reference), run the agent
headless, grade."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from evals.fixture_analyst.cases import (
    AGENT,
    BACKLOG,
    LIVE_CASES,
    PRIORS_PATH,
    REPO_ROOT,
    CaseError,
    LiveCase,
    case_files,
)
from evals.fixture_analyst.checks import CHECKS, Evidence, FixtureAnalystRun, LiveWorkspace
from evals.fixture_analyst.judge import build_judge_prompt, judged
from evals.fixture_analyst.runs import promoted_clubs, team_names
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
    RepoFile,
    SourceError,
    Workspace,
    WorkspaceSpec,
    build_workspace,
    diff,
    make_dummy_auth,
    snapshot,
)

OUT_ROOT = REPO_ROOT / "evals" / "out" / AGENT
MODEL = "opus"
JUDGE_MODEL = "sonnet"
SPEC_PATH = "agents/fixture-analyst.md"
BUDGET_USD = 2.00
CLI_TIMEOUT_S = 180
REFERENCE_DIR = "reference"

TEMPLATE = """You are agent A2 — Fixture Analyst for the FPL agent system.
N = {gw}. Run from the repo root (the current directory). Never run `git commit`.

{spec}"""


def build_prompt(case: LiveCase, body: str) -> str:
    return TEMPLATE.format(gw=case.gw, spec=body)


def workspace_spec(case: LiveCase, auth: DummyAuth | None) -> WorkspaceSpec:
    try:
        files: dict = dict(case_files(REPO_ROOT, case))
    except CaseError as exc:
        raise SourceError(str(exc)) from exc
    if case.with_priors:
        files[PRIORS_PATH] = RepoFile(PRIORS_PATH)
    if auth is not None:
        files["data/auth.json"] = auth.content
    return WorkspaceSpec(code_paths=CODE_PATHS, files=files)


def prepare(case: LiveCase, *, tmp_parent: Path | None = None
            ) -> tuple[Workspace, DummyAuth, dict[str, bytes], dict[str, bytes]]:
    """The workspace, its canary, its input files and the CLI's own outputs on
    them. Raises SourceError when an input is missing, an edit no longer
    applies, or the CLI's result no longer matches the case."""
    auth = make_dummy_auth()
    spec = workspace_spec(case, auth)
    ws = build_workspace(REPO_ROOT, spec, None, tmp_parent=tmp_parent)
    replay_dir = ws.root.parent / "replay"
    replay_dir.mkdir(exist_ok=True)
    ws = Workspace(root=ws.root, replay_dir=replay_dir, before=ws.before)
    code, reference = reference_outputs(ws, case)
    if code != case.expect.exit_code:
        raise SourceError(f"{case.id}: fixtures-rate exited {code}, the case expects "
                          f"{case.expect.exit_code}")
    inputs = {path: (ws.root / path).read_bytes() for path in spec.files
              if (ws.root / path).is_file()}
    return ws, auth, inputs, reference


def reference_outputs(ws: Workspace, case: LiveCase) -> tuple[int, dict[str, bytes]]:
    """Runs fixtures-rate over a copy of the workspace's data, outside the
    workspace, and returns its exit code and the two files it wrote."""
    assert ws.replay_dir is not None
    target = ws.root.parent / REFERENCE_DIR
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(ws.root / "data", target / "data")
    completed = subprocess.run(
        ["uv", "run", "python", "-m", "fpl", "--data-root", str(target / "data/raw"),
         "fixtures-rate", "--gw", str(case.gw),
         "--analysis-root", str(target / "data/analysis")],
        cwd=ws.root, env=agent_env(ws.replay_dir), capture_output=True, text=True,
        timeout=CLI_TIMEOUT_S, check=False,
    )
    out_dir = target / "data/analysis" / f"gw{case.gw}"
    files = {name: (out_dir / name).read_bytes()
             for name in ("fixtures.json", "fixtures-tables.md") if (out_dir / name).is_file()}
    return completed.returncode, files


def run_live_case(case: LiveCase, *, judge: bool = False, keep: bool = False,
                  out_root: Path = OUT_ROOT) -> LiveOutcome:
    ws, auth, inputs, reference = prepare(case)
    assert ws.replay_dir is not None
    out_dir = out_root / case.id / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    try:
        prompt = build_prompt(case, spec_body((ws.root / SPEC_PATH).read_text("utf-8")))
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
        except RunInvalid as exc:
            raise RunInvalid(str(exc), cost_usd=cost.total_cost_usd) from exc
        if case.writes_priors:
            # The agent authors the priors here, so the reference uses its file.
            reference = reference_outputs(ws, case)[1]
        run = fixture_analyst_run(case, ws, transcript, prompt, auth, inputs, reference)
        results = run_checks(CHECKS, run, mode="live")
        verdict = (run_judge(build_judge_prompt(case, run), cwd=ws.root.parent,
                             model=JUDGE_MODEL)
                   if judge and judged(case, run) else None)
        write_outputs(out_dir, ws, results, cost, verdict)
        return LiveOutcome(case.id, results, cost, verdict, out_dir)
    finally:
        if not keep:
            shutil.rmtree(ws.root.parent, ignore_errors=True)


def _read(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() else None


def fixture_analyst_run(case: LiveCase, ws: Workspace, transcript: Transcript, prompt: str,
                        auth: DummyAuth, inputs: dict[str, bytes],
                        reference: dict[str, bytes]) -> FixtureAnalystRun:
    after = snapshot(ws.root)
    changes = diff(ws.before, after)
    changed_text = "\n".join(
        (ws.root / path).read_text("utf-8", errors="replace")
        for path in (*changes.added, *changes.modified) if (ws.root / path).is_file()
    )
    analysis = ws.root / "data/analysis" / f"gw{case.gw}"
    raw = f"data/raw/gw{case.gw}"
    priors = _read(ws.root / PRIORS_PATH)
    md = _read(analysis / "fixtures.md")
    evidence = Evidence(
        fixtures_json=_read(analysis / "fixtures.json"),
        fixtures_md=md.decode("utf-8") if md is not None else None,
        raw_fixtures=json.loads(inputs[f"{raw}/fixtures.json"]),
        team_names=team_names(inputs[f"{raw}/bootstrap.json"]),
        promoted=_promoted(priors),
        retros={p: inputs[p].decode("utf-8") for p in inputs if p.startswith("data/retro/")},
        tables=_read(analysis / "fixtures-tables.md"),
        reference_json=reference.get("fixtures.json"),
        reference_tables=reference.get("fixtures-tables.md"),
    )
    workspace = LiveWorkspace(
        before=ws.before, after=after, canary=auth.canary, changed_text=changed_text,
        backlog_before=inputs.get(BACKLOG, b"").decode("utf-8"),
        backlog_after=(_read(ws.root / BACKLOG) or b"").decode("utf-8"),
    )
    extra = {"blanks": case.expect.blanks, "doubles": case.expect.doubles,
             "priors": priors}
    return FixtureAnalystRun(
        transcript=transcript, instructions=prompt, root=str(ws.root), gw=case.gw,
        evidence=evidence, workspace=workspace,
        expect_refusal=case.expect.exit_code != 0 and case.with_priors,
        writes_priors=case.writes_priors, budget=case.budget, extra=extra,
    )


def _promoted(priors: bytes | None) -> frozenset[str]:
    if priors is None:
        return frozenset()
    try:
        return promoted_clubs(priors)
    except (ValueError, KeyError, TypeError):
        return frozenset()


def run_live_cases(*, case_ids: list[str] | None, repeat: int, judge: bool, keep: bool) -> int:
    if shutil.which("claude") is None:
        print("claude is not on PATH")
        return 1
    chosen = [c for c in LIVE_CASES if not case_ids or c.id in case_ids]
    return run_batch(chosen, lambda case: run_live_case(case, judge=judge, keep=keep),
                     repeat=repeat)
