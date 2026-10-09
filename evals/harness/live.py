"""Headless Claude runs for live evaluation: the agent run, the judge run, and
the guard that rejects a run which escaped its sandbox."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from evals.harness.checks import CheckResult, Status, format_scorecard
from evals.harness.shell import call_fpl_invocations
from evals.harness.transcript import Transcript
from evals.harness.workspace import SourceError, Workspace, diff, snapshot

AGENT_TOOLS = ("Bash", "Read", "Write", "Edit", "Glob", "Grep")
DISALLOWED = ("WebFetch", "WebSearch", "Bash(curl *)", "Bash(wget *)",
              "Bash(git commit *)", "Bash(git push *)")
NETWORK_SUBCOMMANDS = frozenset({
    "bootstrap", "fixtures", "summaries", "entry", "picks", "entry-history",
    "actuals", "flags", "calibrate", "auth-check", "my-team", "set-lineup",
    "make-transfers",
})
AGENT_TIMEOUT_S = 900
STDERR_FILE = "stderr.txt"
STDERR_TAIL = 800
JUDGE_TIMEOUT_S = 300


class RunInvalid(RuntimeError):
    """The run cannot be graded: claude failed before producing a result, the
    stub was bypassed, or the agent left its workspace. `cost_usd` is what the
    run spent anyway."""

    def __init__(self, message: str, *, cost_usd: float | None = None) -> None:
        super().__init__(message)
        self.cost_usd = cost_usd


@dataclass(frozen=True)
class RunCost:
    total_cost_usd: float | None
    num_turns: int | None
    duration_ms: int | None
    result: str | None


@dataclass(frozen=True)
class JudgeVerdict:
    passed: bool
    reason: str
    cost_usd: float | None


@dataclass(frozen=True)
class LiveOutcome:
    case_id: str
    results: list[CheckResult]
    cost: RunCost
    judge: JudgeVerdict | None
    out_dir: Path

    @property
    def failures(self) -> list[CheckResult]:
        return [r for r in self.results if r.status is Status.FAIL]


class HasId(Protocol):
    @property
    def id(self) -> str: ...


def run_batch[C: HasId](
    cases: Sequence[C], run_case: Callable[[C], LiveOutcome], *, repeat: int = 1
) -> int:
    """Runs every case, prints a line per run then one scorecard. A case whose
    sources are missing is skipped; an invalid run is reported and the batch
    moves on. Exit 1 when any check failed or any run was invalid."""
    columns: dict[str, list[CheckResult]] = {}
    invalid: list[str] = []
    total = 0.0
    for case in cases:
        for attempt in range(1, repeat + 1):
            label = case.id if repeat == 1 else f"{case.id}#{attempt}"
            try:
                outcome = run_case(case)
            except SourceError as exc:
                print(f"{case.id}: skipped — {exc}")
                break
            except RunInvalid as exc:
                total += exc.cost_usd or 0.0
                invalid.append(label)
                print(f"{label}: INVALID — {exc}")
                continue
            columns[label] = outcome.results
            cost = outcome.cost.total_cost_usd or 0.0
            total += cost + ((outcome.judge.cost_usd or 0.0) if outcome.judge else 0.0)
            judged = (f", judge {'PASS' if outcome.judge.passed else 'FAIL: ' + outcome.judge.reason}"
                      if outcome.judge else "")
            print(f"{label}: ${cost:.4f}, {outcome.cost.num_turns} turns{judged} → {outcome.out_dir}")
    if columns:
        print(format_scorecard(columns))
    if invalid:
        print(f"invalid runs: {', '.join(invalid)}")
    print(f"total cost: ${total:.4f}")
    failed = any(r.status is Status.FAIL for rs in columns.values() for r in rs)
    return 1 if failed or invalid else 0


def spec_body(spec_text: str) -> str:
    """An agent spec without its YAML frontmatter: what the agent is told."""
    if not spec_text.startswith("---\n"):
        return spec_text
    _, _, rest = spec_text[4:].partition("\n---\n")
    return rest.lstrip("\n")


def replay_env(replay_dir: Path) -> dict[str, str]:
    return {"FPL_REPLAY_DIR": str(replay_dir), "UV_OFFLINE": "1"}


def agent_env(replay_dir: Path, base: dict[str, str] | None = None) -> dict[str, str]:
    """The caller's environment plus replay mode. VIRTUAL_ENV is dropped: under
    `uv run` it names the real repo's venv, which the workspace must not use."""
    source = dict(os.environ if base is None else base)
    source.pop("VIRTUAL_ENV", None)
    return source | replay_env(replay_dir)


def build_claude_argv(
    prompt: str, *, model: str, replay_dir: Path, budget_usd: float = 1.00
) -> list[str]:
    return [
        "claude", "-p", prompt,
        "--model", model,
        "--output-format", "stream-json", "--verbose",
        "--tools", ",".join(AGENT_TOOLS),
        # dontAsk with an allow-list: a headless run can never stall on a
        # prompt, and every unlisted tool is denied.
        "--permission-mode", "dontAsk",
        "--allowedTools", " ".join(AGENT_TOOLS),
        "--disallowedTools", " ".join(DISALLOWED),
        "--setting-sources", "project",
        "--settings", json.dumps({"env": replay_env(replay_dir)}),
        # Eval sessions must stay out of ~/.claude/projects, which
        # `fpl usage` reads for the cost ledgers.
        "--no-session-persistence",
        "--max-budget-usd", f"{budget_usd:.2f}",
    ]


def build_judge_argv(model: str = "opus", budget_usd: float = 0.50) -> list[str]:
    return [
        "claude", "-p", "--model", model, "--output-format", "json",
        "--tools", "", "--no-session-persistence", "--setting-sources", "project",
        "--max-budget-usd", f"{budget_usd:.2f}",
    ]


def run_agent(argv: list[str], *, cwd: Path, replay_dir: Path, stream_path: Path) -> Path:
    """Writes claude's stderr to STDERR_FILE beside the stream. A non-zero exit
    is still gradable when the stream reached its result record (an exhausted
    budget exits non-zero after one)."""
    stream_path.parent.mkdir(parents=True, exist_ok=True)
    with stream_path.open("w", encoding="utf-8") as out:
        completed = subprocess.run(
            argv, cwd=cwd, env=agent_env(replay_dir), stdout=out,
            stderr=subprocess.PIPE, timeout=AGENT_TIMEOUT_S, check=False,
        )
    stderr_path = stream_path.with_name(STDERR_FILE)
    stderr_path.write_bytes(completed.stderr or b"")
    if completed.returncode != 0 and not _has_result(stream_path):
        tail = (completed.stderr or b"").decode("utf-8", "replace").strip()[-STDERR_TAIL:]
        raise RunInvalid(
            f"claude exited {completed.returncode} with no result record "
            f"(stderr in {stderr_path}): {tail or '(empty)'}"
        )
    return stream_path


def _has_result(stream_path: Path) -> bool:
    return any(r.get("type") == "result" for r in read_stream(stream_path))


def run_judge(prompt: str, *, cwd: Path, model: str = "opus") -> JudgeVerdict:
    completed = subprocess.run(
        build_judge_argv(model), input=prompt, cwd=cwd, capture_output=True, text=True,
        timeout=JUDGE_TIMEOUT_S, check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return JudgeVerdict(False, f"judge produced no JSON (exit {completed.returncode})", None)
    passed, reason = parse_judge_answer(str(payload.get("result", "")))
    return JudgeVerdict(passed, reason, payload.get("total_cost_usd"))


def parse_judge_answer(answer: str) -> tuple[bool, str]:
    first = answer.strip().splitlines()[0].strip() if answer.strip() else ""
    if first.upper() == "PASS" or first.upper().startswith("PASS "):
        return True, ""
    if first.upper().startswith("FAIL"):
        return False, first[4:].lstrip(":").strip()
    return False, f"unparseable judge answer: {first}"


def parse_result_cost(records: Iterable[dict]) -> RunCost:
    result = None
    for record in records:
        if record.get("type") == "result":
            result = record
    if result is None:
        return RunCost(None, None, None, None)
    return RunCost(result.get("total_cost_usd"), result.get("num_turns"),
                   result.get("duration_ms"), result.get("result"))


def read_stream(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def validate_run(transcript: Transcript, *, replay_dir: Path, real_repo: Path) -> None:
    real = str(real_repo)
    for call in transcript.calls:
        if real in json.dumps(dict(call.input)):
            raise RunInvalid(f"a tool input names the real repo ({call.name} {call.id})")
    networked = any(
        inv.subcommand in NETWORK_SUBCOMMANDS and not inv.is_help
        for call in transcript.calls for inv in call_fpl_invocations(call)
    )
    served = replay_dir / "served.jsonl"
    if networked and (not served.is_file() or not served.read_text().strip()):
        raise RunInvalid(
            "fpl network commands ran but the replay served.jsonl is empty: "
            "the stub was bypassed"
        )


def write_outputs(out_dir: Path, ws: Workspace, results: list[CheckResult], cost: RunCost,
                  verdict: JudgeVerdict | None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    scorecard = {
        "results": [{"id": r.id, "status": r.status.value, "evidence": r.evidence}
                    for r in results],
        "cost": asdict(cost),
        "judge": asdict(verdict) if verdict else None,
    }
    (out_dir / "scorecard.json").write_text(json.dumps(scorecard, indent=1), "utf-8")
    changes = diff(ws.before, snapshot(ws.root))
    (out_dir / "workspace-diff.json").write_text(json.dumps(asdict(changes), indent=1), "utf-8")
