"""Headless Claude runs for live evaluation: the agent run, the judge run, and
the guard that rejects a run which escaped its sandbox."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from evals.harness.shell import call_fpl_invocations
from evals.harness.transcript import Transcript

AGENT_TOOLS = ("Bash", "Read", "Write", "Edit", "Glob", "Grep")
DISALLOWED = ("WebFetch", "WebSearch", "Bash(curl *)", "Bash(wget *)",
              "Bash(git commit *)", "Bash(git push *)")
NETWORK_SUBCOMMANDS = frozenset({
    "bootstrap", "fixtures", "summaries", "entry", "picks", "entry-history",
    "actuals", "flags", "calibrate", "auth-check", "my-team", "set-lineup",
    "make-transfers",
})
AGENT_TIMEOUT_S = 900
JUDGE_TIMEOUT_S = 300


class RunInvalid(RuntimeError):
    """The run cannot be graded: the stub was bypassed or the agent left its
    workspace."""


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
    stream_path.parent.mkdir(parents=True, exist_ok=True)
    with stream_path.open("w", encoding="utf-8") as out:
        subprocess.run(
            argv, cwd=cwd, env=agent_env(replay_dir), stdout=out,
            stderr=subprocess.PIPE, timeout=AGENT_TIMEOUT_S, check=False,
        )
    return stream_path


def run_judge(prompt: str, *, cwd: Path) -> JudgeVerdict:
    completed = subprocess.run(
        build_judge_argv(), input=prompt, cwd=cwd, capture_output=True, text=True,
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
