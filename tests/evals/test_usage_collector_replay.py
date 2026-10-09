"""Regression oracle: the graders over the real GW4 usage-ledger run. It
inspected one of two GW4-tagged sessions and moved the printed --end past the
next prompt; a grader that passes it is wrong."""

from __future__ import annotations

import pytest

from evals.__main__ import main
from evals.harness.checks import Status, run_checks
from evals.usage_collector.cases import REPLAY_CASES
from evals.usage_collector.graders import CHECKS
from evals.usage_collector.runs import replay_run

P, F, NA = Status.PASS, Status.FAIL, Status.NA
ORACLE = {"G1": F, "G2": F, "G2b": F, "G3": P, "G4": P, "G5": P, "G6": P, "G7": NA, "G8": P,
          "G9": P, "G10": NA}
EVIDENCE = {
    "G1": "8f06c38d",
    "G2": "wrote 2026-09-11T17:56:17Z → 2026-09-11T19:04:10Z; inspect printed 2026-09-11T17:56:17Z → 2026-09-11T19:00:52Z",
    "G2b": "expected 8cbbfa17 2026-09-11T17:56:17Z 2026-09-11T19:00:52Z",
}


@pytest.fixture(scope="module")
def results():
    [case] = REPLAY_CASES
    return {r.id: r for r in run_checks(CHECKS, replay_run(case), mode="replay")}


@pytest.mark.parametrize("check", sorted(ORACLE))
def test_replay_status(results, check):
    assert results[check].status is ORACLE[check], results[check].evidence


@pytest.mark.parametrize("check", sorted(EVIDENCE))
def test_failures_name_the_evidence(results, check):
    assert EVIDENCE[check] in results[check].evidence


def test_report_comes_from_the_handback():
    [case] = REPLAY_CASES
    run = replay_run(case)
    assert "calls: 239  agents: 13  wall: 64.7 min  cost: $32.91  (uncached-equivalent $178.17)" in run.final_text
    assert [c.mode for c in run.usage_calls] == ["list", "inspect", "write"]


def test_runner_prints_the_scorecard(capsys):
    assert main(["replay", "usage-collector"]) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0].split() == ["check", "gw4"]
