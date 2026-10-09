"""Live-run plumbing that needs no model: the exact headless command, cost
parsing, judge-answer parsing and the run-validity guard."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.harness.live import (
    RunInvalid,
    build_claude_argv,
    build_judge_argv,
    parse_judge_answer,
    parse_result_cost,
    validate_run,
)
from evals.harness.transcript import ToolCall, Transcript


def test_build_claude_argv_is_exact():
    argv = build_claude_argv("do it", model="haiku", replay_dir=Path("/tmp/r"))
    assert argv == [
        "claude", "-p", "do it",
        "--model", "haiku",
        "--output-format", "stream-json", "--verbose",
        "--tools", "Bash,Read,Write,Edit,Glob,Grep",
        "--permission-mode", "dontAsk",
        "--allowedTools", "Bash Read Write Edit Glob Grep",
        "--disallowedTools",
        "WebFetch WebSearch Bash(curl *) Bash(wget *) Bash(git commit *) Bash(git push *)",
        "--setting-sources", "project",
        "--settings", json.dumps({"env": {"FPL_REPLAY_DIR": "/tmp/r", "UV_OFFLINE": "1"}}),
        "--no-session-persistence",
        "--max-budget-usd", "1.00",
    ]


def test_build_claude_argv_budget_is_formatted():
    argv = build_claude_argv("p", model="opus", replay_dir=Path("/r"), budget_usd=0.25)
    assert argv[-2:] == ["--max-budget-usd", "0.25"]


def test_build_judge_argv_has_no_tools_and_reads_stdin():
    assert build_judge_argv() == [
        "claude", "-p", "--model", "opus", "--output-format", "json",
        "--tools", "", "--no-session-persistence", "--setting-sources", "project",
        "--max-budget-usd", "0.50",
    ]


def test_parse_result_cost_reads_the_last_result_record():
    cost = parse_result_cost([
        {"type": "system", "subtype": "init"},
        {"type": "result", "total_cost_usd": 0.0123, "num_turns": 7,
         "duration_ms": 4200, "result": "done", "is_error": False},
    ])
    assert cost.total_cost_usd == pytest.approx(0.0123)
    assert cost.num_turns == 7
    assert cost.duration_ms == 4200
    assert cost.result == "done"


def test_parse_result_cost_without_a_result_record():
    assert parse_result_cost([{"type": "assistant"}]).total_cost_usd is None


@pytest.mark.parametrize(
    ("answer", "verdict"),
    [
        ("PASS", (True, "")),
        ("PASS\nall claims supported", (True, "")),
        ("FAIL: the return omits the bootstrap exit 1", (False, "the return omits the bootstrap exit 1")),
        ("  fail: lowercase still counts", (False, "lowercase still counts")),
        ("I think it passes", (False, "unparseable judge answer: I think it passes")),
    ],
)
def test_parse_judge_answer(answer, verdict):
    assert parse_judge_answer(answer) == verdict


def transcript(*commands):
    calls = tuple(ToolCall(str(i), "Bash", {"command": c}, None)
                  for i, c in enumerate(commands))
    return Transcript(prompt="p", calls=calls, final_text="", cost_usd=None)


def test_run_is_invalid_when_the_replay_served_nothing(tmp_path):
    with pytest.raises(RunInvalid, match="served.jsonl"):
        validate_run(transcript("uv run python -m fpl bootstrap --gw 6"),
                     replay_dir=tmp_path, real_repo=Path("/real/repo"))


def test_run_is_valid_when_the_replay_served_requests(tmp_path):
    (tmp_path / "served.jsonl").write_text('{"outcome": "hit"}\n')
    validate_run(transcript("uv run python -m fpl bootstrap --gw 6"),
                 replay_dir=tmp_path, real_repo=Path("/real/repo"))


def test_local_only_commands_need_no_served_requests(tmp_path):
    validate_run(transcript("uv run python -m fpl slim-csv --gw 6", "ls"),
                 replay_dir=tmp_path, real_repo=Path("/real/repo"))


def test_run_is_invalid_when_a_tool_input_names_the_real_repo(tmp_path):
    (tmp_path / "served.jsonl").write_text('{"outcome": "hit"}\n')
    with pytest.raises(RunInvalid, match="real repo"):
        validate_run(transcript("cat /real/repo/data/raw/gw6/meta.md"),
                     replay_dir=tmp_path, real_repo=Path("/real/repo"))


def test_agent_env_adds_replay_mode_and_drops_the_callers_venv():
    from evals.harness.live import agent_env

    env = agent_env(Path("/r"), base={"PATH": "/bin", "VIRTUAL_ENV": "/real/.venv"})
    assert env == {"PATH": "/bin", "FPL_REPLAY_DIR": "/r", "UV_OFFLINE": "1"}
