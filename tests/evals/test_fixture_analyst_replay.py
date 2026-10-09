"""Regression oracle: the fixture-analyst graders over the real GW4–GW6 runs.

Each expectation was verified against the recorded transcripts and the cycle
commits. The runs predate `fpl fixtures-rate`, so F1/F2/F8/F9 failing is the
point: a grader that passes a known-bad run is wrong.
"""

from __future__ import annotations

import pytest

from evals.__main__ import main
from evals.fixture_analyst.cases import REPLAY_CASES
from evals.fixture_analyst.checks import CHECKS
from evals.fixture_analyst.runs import replay_run
from evals.harness.checks import Status, run_checks
from evals.harness.transcript import load_transcript

P, F = Status.PASS, Status.FAIL

ORACLE = {
    "F1": (F, F, F),
    "F2": (F, F, F),
    "F3": (P, P, P),
    "F4": (P, P, P),
    "F5": (P, P, P),
    "F6": (F, P, P),
    "F7": (P, P, P),
    "F8": (F, F, F),
    "F9": (F, F, F),
    "F10": (P, P, P),
    "F11": (P, F, F),
}
NAMES = ("gw4", "gw5", "gw6")
EVIDENCE = {
    ("gw4", "F2"): "analysis/gw4/fixtures.json','w",
    ("gw5", "F2"): 'analysis/gw5/fixtures.json","w',
    ("gw6", "F2"): "analysis/gw6/fixtures.json','w",
    ("gw4", "F4"): "p_cs max 0.0058, λ max 0.000",
    ("gw5", "F4"): "p_cs max 0.0049, λ max 0.010",
    ("gw6", "F4"): "p_cs max 0.0048, λ max 0.000",
    ("gw4", "F5"): "headline 8 numbers trace; detail 120 rows",
    ("gw5", "F5"): "headline 11 numbers trace; detail 120 rows",
    ("gw6", "F5"): "headline 12 numbers trace; detail 120 rows",
    ("gw4", "F6"): "data/retro/gw3.md",
    ("gw4", "F7"): "C4, C5, C12",
    ("gw4", "F8"): "data/analysis/gw3/fixtures.md",
    ("gw5", "F8"): "data/analysis/gw4/fixtures.md",
    ("gw6", "F8"): "cat data/analysis/gw5/fixtures.md",
    ("gw4", "F9"): "38 tool calls",
    ("gw5", "F9"): "38 tool calls",
    ("gw6", "F9"): "22 tool calls",
    ("gw6", "F3"): "after the write in the same command",
}
CASES = {case.name: case for case in REPLAY_CASES}


@pytest.fixture(scope="module")
def results():
    return {name: {r.id: r for r in run_checks(CHECKS, replay_run(case), mode="replay")}
            for name, case in CASES.items()}


@pytest.mark.parametrize(("case", "check"),
                         [(name, check) for check in ORACLE for name in NAMES])
def test_replay_status(results, case, check):
    expected = ORACLE[check][NAMES.index(case)]
    result = results[case][check]
    assert result.status is expected, result.evidence


@pytest.mark.parametrize(("case", "check"), sorted(EVIDENCE))
def test_replay_evidence(results, case, check):
    assert EVIDENCE[(case, check)] in results[case][check].evidence


@pytest.mark.parametrize(("case", "calls", "handback"),
                         [("gw4", 38, False), ("gw5", 39, True), ("gw6", 23, True)])
def test_frozen_fixture_shape(case, calls, handback):
    transcript = load_transcript(CASES[case].fixture)
    assert len(transcript.calls) == calls
    assert any(c.name == "SubagentHandback" for c in transcript.calls) is handback
    assert "/Users/" not in CASES[case].fixture.read_text("utf-8")


def test_runner_prints_the_scorecard(capsys):
    assert main(["replay", "fixture-analyst"]) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0].split() == ["check", "gw4", "gw5", "gw6"]
    assert "gw4 F6 FAIL: never read: data/retro/gw3.md" in out
