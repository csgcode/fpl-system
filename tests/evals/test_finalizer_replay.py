"""Replay oracle: the finalizer checks over the five recorded runs. Every cell
was verified by hand against the transcripts and the cycle commits; a check
that passes a known-bad run is wrong."""

from __future__ import annotations

import pytest

from evals.finalizer.cases import REPLAY_CASES
from evals.finalizer.checks import CHECKS
from evals.finalizer.runs import git_text, load_bootstrap, replay_run
from evals.harness.checks import Status, run_checks
from evals.harness.shell import agent_written_files
from evals.harness.transcript import HANDBACK_TOOL, load_transcript

P, F, N = Status.PASS, Status.FAIL, Status.NA
CASES = {case.name: case for case in REPLAY_CASES}
NAMES = ("gw4", "gw5-reopen", "gw5-rerun", "gw6", "gw5-correction")

ORACLE = {
    "C1": (P, P, P, P, N),
    "C2": (P, P, P, P, N),
    "C3": (N, P, N, N, N),
    "C4": (N, P, N, N, N),
    "C5": (P, N, P, P, N),
    "C6": (N, N, P, F, N),
    "C7": (P, N, P, P, N),
    "C8": (P, N, P, P, P),
    "C9": (P, P, P, P, P),
    "C10": (P, P, P, P, F),
    "C11": (N, P, N, N, P),
    "C12": (P, N, N, F, P),
    "C13": (N, N, F, N, N),
    "C14": (N, N, N, N, N),
    "C15": (N, N, N, N, P),
    "C16": (N, N, N, N, N),
    "C17": (N, N, N, N, N),
    "C18": (N, N, N, N, N),
}
ARCHIVE_CHECKS = {"C2", "C3"}


@pytest.fixture(scope="module")
def results():
    return {name: {r.id: r for r in run_checks(CHECKS, replay_run(CASES[name]), mode="replay")}
            for name in NAMES}


def _archives_present(name: str) -> bool:
    case = CASES[name]
    return load_bootstrap(case.baseline) is not None and load_bootstrap(case.gate) is not None


@pytest.mark.parametrize("check_id", list(ORACLE))
@pytest.mark.parametrize("index,name", list(enumerate(NAMES)))
def test_replay_oracle(results, check_id, index, name):
    if check_id in ARCHIVE_CHECKS and name != "gw5-correction" and not _archives_present(name):
        pytest.skip(f"{name}: a pinned bootstrap archive is missing or drifted")
    result = results[name][check_id]
    assert result.status is ORACLE[check_id][index], result.evidence


def test_the_oracle_covers_every_check():
    assert set(ORACLE) == {check.id for check in CHECKS}


def test_failures_name_the_offending_evidence(results):
    assert "data/decisions/gw5/final.md" in results["gw6"]["C6"].evidence
    assert "git checkout" in results["gw5-correction"]["C10"].evidence
    assert "227 words > 150" in results["gw6"]["C12"].evidence
    assert "S2" in results["gw5-rerun"]["C13"].evidence


def test_passes_carry_their_evidence(results):
    if _archives_present("gw5-reopen"):
        assert "1 changed id" in results["gw5-reopen"]["C3"].evidence
    assert "2 row(s), agents A7" == results["gw5-reopen"]["C11"].evidence
    assert "agents ORCH" in results["gw5-correction"]["C11"].evidence
    assert "0 transfer(s)" in results["gw5-correction"]["C8"].evidence
    assert "transfers_made pairs" in results["gw6"]["C8"].evidence


@pytest.mark.parametrize("name,calls,handback", [
    ("gw4", 9, False), ("gw5-reopen", 14, True), ("gw5-rerun", 20, True),
    ("gw5-correction", 27, True), ("gw6", 8, True),
])
def test_parser_pins_call_counts_and_return_source(name, calls, handback):
    transcript = load_transcript(CASES[name].fixture)
    assert len(transcript.calls) == calls
    handbacks = [c for c in transcript.calls if c.name == HANDBACK_TOOL]
    assert bool(handbacks) is handback
    if handback:
        assert transcript.final_text == handbacks[-1].input["message"]


@pytest.mark.parametrize("name", ["gw4", "gw5-rerun", "gw6"])
def test_the_agents_own_write_is_the_committed_final(name):
    """Replay grades final.md from the cycle commit; that is only sound while
    the commit holds exactly what the agent wrote."""
    case = CASES[name]
    written = agent_written_files(load_transcript(case.fixture), "/repo")
    assert written[case.decision("final.md")] == git_text(case.cycle_commit,
                                                          case.decision("final.md"))


def test_the_rerun_has_one_executable_flags_call_despite_the_heredoc_prose(results):
    assert results["gw5-rerun"]["C1"].status is P
    assert "flags" in str(load_transcript(CASES["gw5-rerun"].fixture).calls[16].input)
