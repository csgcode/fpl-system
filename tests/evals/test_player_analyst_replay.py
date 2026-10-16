"""Regression oracle: the player-analyst graders over the thirteen recorded
GW4–GW6 runs. Every known failure must be detected, with evidence naming the
call or the row."""

from __future__ import annotations

import pytest

from evals.harness.checks import Status, run_checks
from evals.harness.transcript import HANDBACK_TOOL, load_transcript
from evals.harness.workspace import SourceError
from evals.player_analyst.cases import REPLAY_CASES, replay_case
from evals.player_analyst.checks import CHECKS
from evals.player_analyst.runs import replay_run

P, F, NA = Status.PASS, Status.FAIL, Status.NA
IDS = [c.id for c in REPLAY_CASES]


def _grid(**rows: str) -> dict[str, dict[str, Status]]:
    """Each row is one check: a status letter per case, in REPLAY_CASES order."""
    letters = {"P": P, "F": F, "-": NA}
    return {check: dict(zip(IDS, (letters[x] for x in cells.split()), strict=True))
            for check, cells in rows.items()}


#                gw4: gkp def mid fwd  gw5: gkp def mid fwd reo  gw6: gkp def mid fwd
EXPECTED = _grid(
    P1=" F F F P   P F F P F   P F F P",
    P2=" P F F P   P F F P P   P F P P",
    P3a="P P F P   P P P P F   P P P F",
    P3b="- - - -   - - - - -   - - - -",
    P4=" P P P P   P P P P P   P P P P",
    P5=" P P P P   P P P P P   P P P P",
    P6=" P P P P   P P P P P   P P P P",
    P7=" P P P P   F P P P P   F P F P",
    V1=" P P P P   P P P P P   P P F P",
    V2=" - - - -   P P P P P   P P P P",
    V3=" P F F P   P F F P P   P P F P",
    V4=" P F P F   F P F P P   F F P F",
    V5=" - - - -   - - - - -   - - - -",
    M1=" P P P P   P P P P F   P P P P",
    M2=" P P P P   P P P P P   P P P P",
    R1=" P P P P   P P P P P   P P P P",
    R2=" - - - -   - - - - -   - - - -",
    X1=" - - - -   - - - - P   - - - -",
)

EVIDENCE = {
    ("gw4-def", "P1"): "43 work calls",
    ("gw5-def-reopen", "P1"): "26 work calls > 6",
    ("gw4-def", "P2"): "c1,c2",
    ("gw6-def", "P2"): "c3",
    ("gw4-mid", "P3a"): "bootstrap read at call(s) c10",
    ("gw5-def-reopen", "P3a"): "bootstrap read at call(s) c2,c4,c8,c9,c19; "
                               "backlog read at call(s) c22,c23",
    ("gw6-fwd", "P3a"): "bootstrap read at call(s) c5",
    ("gw5-gkp", "P7"): "18 non-blank lines",
    ("gw6-gkp", "P7"): "18 non-blank lines",
    ("gw6-mid", "P7"): "16 non-blank lines",
    ("gw6-mid", "V1"): "James 0.08 (i, Back injury - Expected back 18 Oct)",
    ("gw4-def", "V3"): "Mendy 0.86, Coyle 0.8",
    ("gw4-mid", "V3"): "Stroud 0.88",
    ("gw5-def", "V3"): "Mendy 0.84",
    ("gw5-mid", "V3"): "Stroud 0.85, Mason-Clark 0.8",
    ("gw6-mid", "V3"): "Mason-Clark 0.72",
    ("gw4-def", "V4"): "5 row(s)",
    ("gw4-fwd", "V4"): "7 row(s)",
    ("gw5-gkp", "V4"): "Benitez 0.6≠0.9",
    ("gw5-mid", "V4"): "7 row(s)",
    ("gw6-gkp", "V4"): "1 row(s)",
    ("gw6-def", "V4"): "1 row(s)",
    ("gw6-fwd", "V4"): "1 row(s)",
    ("gw5-def-reopen", "M1"): "126 lines > 120; 6 escalations > 5",
    ("gw5-def-reopen", "X1"): "changed [34, 36, 423, 447, 448]",
    ("gw4-def", "I-P3b"): "c15,c16,c17,c18,c19,c23,c25,c26,c27,c38,c39",
    ("gw6-gkp", "I-P3b"): "c4",
    ("gw6-mid", "I-P3b"): "c12",
    ("gw6-def", "I-R2"): "retired cited: none",
}


@pytest.fixture(scope="module")
def results():
    out = {}
    for case in REPLAY_CASES:
        try:
            run = replay_run(case)
        except SourceError as exc:
            pytest.skip(f"replay source missing: {exc}")
        out[case.id] = {r.id: r for r in run_checks(CHECKS, run, mode="replay")}
    return out


@pytest.mark.parametrize("check", sorted(EXPECTED))
@pytest.mark.parametrize("case_id", IDS)
def test_replay_oracle(results, case_id, check):
    got = results[case_id][check]
    assert got.status is EXPECTED[check][case_id], f"{case_id} {check}: {got.evidence}"


@pytest.mark.parametrize("key", sorted(EVIDENCE))
def test_replay_evidence_names_the_call_or_row(results, key):
    case_id, check = key
    assert EVIDENCE[key] in results[case_id][check].evidence


def test_retired_corrections_are_cited_in_eleven_of_twelve_normal_runs(results):
    clean = [c.id for c in REPLAY_CASES if c.mode == "normal"
             and results[c.id]["I-R2"].evidence.endswith("none")]
    assert clean == ["gw6-def"]


@pytest.mark.parametrize("case_id", IDS)
def test_parser_finds_the_pinned_call_count_and_return_source(case_id):
    case = replay_case(case_id)
    transcript = load_transcript(case.fixture)
    work = [c for c in transcript.calls if c.name != HANDBACK_TOOL]
    handbacks = [c for c in transcript.calls if c.name == HANDBACK_TOOL]
    assert len(work) == case.work_calls
    assert bool(handbacks) is case.handback
    assert transcript.final_text.strip()
