"""The live batch loop and the headless-run wrapper, exercised with stand-in
processes and cases: no model is called."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from evals.harness.checks import CheckResult, Status
from evals.harness.live import (
    STDERR_FILE,
    LiveOutcome,
    RunCost,
    RunInvalid,
    run_agent,
    run_batch,
)
from evals.harness.workspace import SourceError

RESULT = '{"type": "result", "total_cost_usd": 0.01}'


def sh(script: str) -> list[str]:
    return ["sh", "-c", script]


def test_run_agent_keeps_claudes_stderr_beside_the_stream(tmp_path):
    stream = run_agent(sh(f"echo '{RESULT}'; echo warming up >&2"), cwd=tmp_path,
                       replay_dir=tmp_path, stream_path=tmp_path / "out" / "stream.jsonl")
    assert stream.read_text().strip() == RESULT
    assert (tmp_path / "out" / STDERR_FILE).read_text() == "warming up\n"


def test_a_failed_run_with_no_result_is_invalid_and_quotes_stderr(tmp_path):
    with pytest.raises(RunInvalid, match="exited 3.*bad flag") as exc_info:
        run_agent(sh("echo bad flag >&2; exit 3"), cwd=tmp_path, replay_dir=tmp_path,
                  stream_path=tmp_path / "stream.jsonl")
    assert STDERR_FILE in str(exc_info.value)


def test_a_non_zero_exit_that_still_produced_a_result_is_gradable(tmp_path):
    """claude exits non-zero when the budget runs out, after a result record."""
    run_agent(sh(f"echo '{RESULT}'; exit 1"), cwd=tmp_path, replay_dir=tmp_path,
              stream_path=tmp_path / "stream.jsonl")


@dataclass(frozen=True)
class FakeCase:
    id: str


def outcome(case_id: str, status: Status, cost: float) -> LiveOutcome:
    result = CheckResult("A1", status, "evidence here")
    return LiveOutcome(case_id, [result], RunCost(cost, 2, 10, None), None, Path("/out"))


def test_one_invalid_run_does_not_abort_the_batch(capsys):
    def run_case(case: FakeCase) -> LiveOutcome:
        if case.id == "bad":
            raise RunInvalid("the stub was bypassed", cost_usd=0.25)
        return outcome(case.id, Status.PASS, 0.5)

    code = run_batch([FakeCase("bad"), FakeCase("good")], run_case)
    out = capsys.readouterr().out
    assert code == 1
    assert "bad: INVALID — the stub was bypassed" in out
    assert "good: $0.5000" in out
    assert "total cost: $0.7500" in out
    assert "invalid runs: bad" in out


def test_a_missing_source_skips_the_case(capsys):
    def run_case(case: FakeCase) -> LiveOutcome:
        if case.id == "gone":
            raise SourceError("missing source: x")
        return outcome(case.id, Status.PASS, 0.1)

    assert run_batch([FakeCase("gone"), FakeCase("ok")], run_case) == 0
    assert "gone: skipped — missing source: x" in capsys.readouterr().out


def test_a_failed_check_fails_the_batch_and_repeats_are_labelled(capsys):
    assert run_batch([FakeCase("c")], lambda c: outcome(c.id, Status.FAIL, 0.0),
                     repeat=2) == 1
    out = capsys.readouterr().out
    assert "c#1:" in out and "c#2:" in out
    assert "c#1 A1 FAIL: evidence here" in out
