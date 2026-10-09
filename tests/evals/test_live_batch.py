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
