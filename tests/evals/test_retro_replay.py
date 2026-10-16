"""Replay oracle: the retro-analyst checks over the three recorded retros.
Every cell was verified by hand against the transcripts, the ledgers and the
cycle commits; a check that passes a known-bad run is wrong."""

from __future__ import annotations

import pytest

from evals.harness.checks import Status, run_checks
from evals.harness.freeze import FROZEN_ROOT
from evals.harness.shell import agent_written_files
from evals.harness.transcript import HANDBACK_TOOL, load_transcript, tool_turns
from evals.retro_analyst.cases import REPLAY_CASES
from evals.retro_analyst.checks import CHECKS
from evals.retro_analyst.runs import git_text, replay_run

P, F, N = Status.PASS, Status.FAIL, Status.NA
CASES = {case.name: case for case in REPLAY_CASES}
NAMES = ("gw3", "gw4", "gw5")

ORACLE = {
    "R1": (P, P, P),
    "R2": (F, F, F),
    "R3": (N, N, N),
    "R4": (P, P, P),
    "R5": (P, P, F),
    "R6": (P, P, P),
    "R7": (P, P, P),
    "R8": (P, P, F),
    "R9": (P, P, P),
    "R10": (P, P, P),
    "R11": (P, F, P),
    "R12": (P, F, P),
    "R13": (F, P, P),
    "R14": (P, P, P),
    "R15": (P, P, P),
    "R16": (P, P, F),
    "R17": (N, N, P),
    "R18": (N, N, N),
    "R19": (N, N, N),
    "R20": (N, N, N),
    "R21": (N, N, N),
    "R22": (N, N, N),
    "R23": (N, N, N),
}

EVIDENCE = {
    ("R2", "gw3"): "10 turns, budget 4",
    ("R2", "gw4"): "10 turns, budget 4",
    ("R2", "gw5"): "5 turns, budget 3",
    ("R5", "gw5"): "ls /repo/data/retro/",
    ("R8", "gw5"): "Squad 8 > 3",
    ("R11", "gw4"): "411 Haaland +3.002",
    ("R12", "gw4"): "n ≈ 680",
    ("R13", "gw3"): "C15, C16",
    ("R14", "gw3"): "3 rows (",
    ("R14", "gw4"): "4 rows (",
    ("R14", "gw5"): "0 rows (",
    ("R16", "gw5"): "S1 is fully open again",
}


@pytest.fixture(scope="module")
def results():
    return {name: {r.id: r for r in run_checks(CHECKS, replay_run(CASES[name]), mode="replay")}
            for name in NAMES}


@pytest.mark.parametrize("check_id", list(ORACLE))
def test_oracle(results, check_id):
    got = tuple(results[name][check_id].status for name in NAMES)
    assert got == ORACLE[check_id], {n: results[n][check_id].evidence for n in NAMES}


@pytest.mark.parametrize("key", list(EVIDENCE))
def test_evidence_names_the_offence(results, key):
    check_id, name = key
    assert EVIDENCE[key] in results[name][check_id].evidence


def test_every_check_has_an_oracle_row():
    assert {check.id for check in CHECKS} == set(ORACLE)


# --- guards on the fixtures themselves ---------------------------------------


@pytest.mark.parametrize("name, calls, turns, handback", [
    ("gw3", 10, 10, False), ("gw4", 11, 11, True), ("gw5", 6, 6, True),
])
def test_fixture_call_and_turn_counts(name, calls, turns, handback):
    transcript = load_transcript(CASES[name].fixture)
    assert len(transcript.calls) == calls
    assert len(tool_turns(transcript, exclude=())) == turns
    assert any(c.name == HANDBACK_TOOL for c in transcript.calls) is handback


@pytest.mark.parametrize("name", NAMES)
def test_written_retro_is_the_committed_file(name):
    case = CASES[name]
    path = f"data/retro/gw{case.round}.md"
    written = agent_written_files(load_transcript(case.fixture), FROZEN_ROOT, apply_edits=True)
    assert written[path] == git_text(case.cycle_commit, path)


@pytest.mark.parametrize("name", NAMES)
def test_calibrate_stdout_is_complete(name):
    stdout = replay_run(CASES[name]).calibrate_stdout
    assert stdout is not None and "over-predicted" in stdout
    assert stdout.rstrip().endswith(f"gw{CASES[name].round}-calibration.json")


def test_runner_replay_prints_the_scorecard(capsys):
    from evals.__main__ import main

    assert main(["replay", "retro-analyst"]) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0].split() == ["check", "gw3", "gw4", "gw5"]
    assert "gw4 R11 FAIL" in out


def test_runner_longitudinal_prints_the_registry(capsys):
    from evals.__main__ import main

    assert main(["longitudinal", "retro-analyst"]) == 0
    assert "C18" in capsys.readouterr().out
