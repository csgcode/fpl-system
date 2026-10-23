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


def test_event_live_counts_as_a_network_command(tmp_path):
    with pytest.raises(RunInvalid, match="served.jsonl"):
        validate_run(transcript("uv run python -m fpl event-live --gw 8 --round 7"),
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
