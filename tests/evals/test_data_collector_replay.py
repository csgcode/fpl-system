"""Regression oracle: the graders over the real GW4–GW6 data-collector runs.

Each expectation was verified against the recorded transcripts. A grader that
passes a known-bad run is wrong, so the FAIL cells matter most.
"""

from __future__ import annotations

import pytest

from evals.__main__ import main
from evals.data_collector.cases import REPLAY_CASES
from evals.data_collector.checks import CHECKS
from evals.data_collector.runs import replay_run
from evals.harness.checks import Status, run_checks
from evals.harness.transcript import load_transcript

P, F, NA = Status.PASS, Status.FAIL, Status.NA
LIVE_ONLY = {"C1": NA, "C10": NA, "C11": NA, "C14": NA, "C15": NA}
UNGATED = {"C9": NA, "C13": NA}

ORACLE = {
    "gw4": {"C2": P, "C3": P, "C4": P, "C5": P, "C6": P, "C7": P, "C8": F, "C12": F},
    "gw5": {"C2": F, "C3": P, "C4": P, "C5": P, "C6": P, "C7": F, "C8": NA, "C12": NA},
    "gw6": {"C2": P, "C3": P, "C4": P, "C5": P, "C6": P, "C7": P, "C8": NA, "C12": NA},
}
EVIDENCE = {
    ("gw4", "C8"): "GW3 status: not finished, not data_checked",
    ("gw4", "C12"): "16 non-blank lines",
    ("gw5", "C2"): "data/raw/gw5/bootstrap.json",
    ("gw5", "C7"): "bootstrap --gw 5",
}
CASES = {case.name: case for case in REPLAY_CASES}


@pytest.fixture(scope="module")
def results():
    return {name: {r.id: r for r in run_checks(CHECKS, replay_run(case), mode="replay")}
            for name, case in CASES.items()}


@pytest.mark.parametrize(
    ("case", "check"),
    [(case, check) for case in ORACLE for check in {**ORACLE[case], **LIVE_ONLY, **UNGATED}],
)
def test_replay_status(results, case, check):
    expected = {**ORACLE[case], **LIVE_ONLY, **UNGATED}[check]
    result = results[case][check]
    assert result.status is expected, result.evidence


@pytest.mark.parametrize(("case", "check"), sorted(EVIDENCE))
def test_failures_name_the_offending_command_or_line(results, case, check):
    assert EVIDENCE[(case, check)] in results[case][check].evidence


@pytest.mark.parametrize(
    ("case", "calls", "via_handback"),
    [("gw4", 13, False), ("gw5", 15, True), ("gw6", 11, True)],
)
def test_frozen_fixture_shape(case, calls, via_handback):
    transcript = load_transcript(CASES[case].fixture)
    assert len(transcript.calls) == calls
    handbacks = [c for c in transcript.calls if c.name == "SubagentHandback"]
    assert bool(handbacks) is via_handback
    if via_handback:
        assert transcript.final_text == handbacks[-1].input["message"]


def test_replay_meta_is_rebuilt_from_the_agents_own_write():
    gw4 = replay_run(CASES["gw4"])
    assert "GW3 status: not finished" in gw4.meta_md
    gw6 = replay_run(CASES["gw6"])
    assert gw6.meta_md.startswith("GW: 6\n")


def test_replay_instructions_include_the_spec_the_agents_ran():
    gw6 = replay_run(CASES["gw6"])
    assert "last-season minutes ≥ 900" in gw6.instructions


def test_runner_prints_the_scorecard(capsys):
    assert main(["replay", "data-collector"]) == 0
    out = capsys.readouterr().out
    assert "gw4" in out and "gw5" in out and "gw6" in out
    assert "C8" in out and "FAIL" in out
