"""Replay oracle: the squad-optimizer checks over the five recorded runs.
Every cell was verified against the transcripts and the cycle commits; a
check that passes a known-bad run is wrong. Evidence must name the call or
the move."""

from __future__ import annotations

import hashlib

import pytest

from evals.harness.checks import Status, run_checks
from evals.harness.transcript import HANDBACK_TOOL, load_transcript
from evals.harness.workspace import SourceError
from evals.squad_optimizer.cases import REPLAY_CASES, VIEWS, replay_case
from evals.squad_optimizer.checks import CHECKS
from evals.squad_optimizer.runs import case_output, git_text, proposal_path, read_text
from evals.squad_optimizer.views import load_view

P, F, N = Status.PASS, Status.FAIL, Status.NA
NAMES = ("gw4", "gw5-orig", "gw5-rev", "gw5-rescore", "gw6")

ORACLE = {
    "O1": (P, P, P, P, P),
    "O2": (P, P, P, P, P),
    "O3": (P, F, P, P, P),
    "O4": (P, F, P, P, P),
    "O5": (P, P, P, P, P),
    "O6": (P, P, P, P, P),
    "O7": (P, P, P, P, P),
    "O8": (F, P, P, P, P),
    "O9": (P, F, P, P, P),
    "O10": (P, N, P, F, F),
    "O11": (P, P, N, P, P),
    "O12": (N, N, N, N, N),
    "O13": (N, N, N, N, N),
    "L": (N, N, N, N, N),
}
EVIDENCE = {
    ("O3", "gw4"): "best +1.375 / -2.853",
    ("O3", "gw5-orig"): "Shaw → Justin +1.013 / +0.443",
    ("O3", "gw6"): "+2.850 / +2.963",
    ("O4", "gw5-orig"): "plan gain +5.118",
    ("O4", "gw5-rescore"): "1376 legal singles",
    ("O5", "gw5-rev"): "Anderson/E.Le Fée share 0.281 v 0.076",
    ("O8", "gw4"): "call 12 writes data/analysis/gw4/opt-blend.json",
    ("O9", "gw5-orig"): 'call 61 runs pkill: pkill -f "python3 -"',
    ("O10", "gw5-rescore"): "13 non-blank lines > 12",
    ("O10", "gw6"): "223 words > 200",
    ("O11", "gw5-orig"): "1 row(s)",
}
ORIGINAL_SHA256 = "360dfdefaea4cf6a4e1b27138cd255a1f41a3bf6bc17547067fba83ef67c3a1c"


def _views_present() -> bool:
    try:
        for spec in VIEWS.values():
            load_view(spec)
    except SourceError:
        return False
    return all(replay_case(name).fixture.is_file() for name in NAMES)


pytestmark = pytest.mark.skipif(not _views_present(),
                                reason="frozen views or transcripts missing; run "
                                       "`python -m evals freeze squad-optimizer`")


@pytest.fixture(scope="module")
def results():
    from evals.squad_optimizer.runs import replay_run

    return {name: {r.id: r for r in run_checks(CHECKS, replay_run(replay_case(name)),
                                               mode="replay")}
            for name in NAMES}


@pytest.mark.parametrize("check_id", list(ORACLE))
@pytest.mark.parametrize("index,name", list(enumerate(NAMES)))
def test_replay_oracle(results, check_id, index, name):
    result = results[name][check_id]
    assert result.status is ORACLE[check_id][index], result.evidence
    if (check_id, name) in EVIDENCE:
        assert EVIDENCE[(check_id, name)] in result.evidence


@pytest.mark.parametrize("case", REPLAY_CASES, ids=lambda c: c.name)
def test_parser_pins_call_counts_and_return_source(case):
    transcript = load_transcript(case.fixture)
    assert len(transcript.calls) == case.calls
    handbacks = [c for c in transcript.calls if c.name == HANDBACK_TOOL]
    assert bool(handbacks) is case.handback
    assert transcript.final_text.strip()


def test_gw5_original_rebuilds_from_heredoc_plus_edits_and_matches_the_revisers_read():
    rebuilt = case_output("gw5-orig")
    reviser = load_transcript(replay_case("gw5-rev").fixture)
    assert rebuilt is not None
    assert rebuilt == read_text(reviser, proposal_path(5))
    assert hashlib.sha256(rebuilt.encode()).hexdigest() == ORIGINAL_SHA256


def test_each_rerun_starts_from_the_previous_runs_output():
    rescorer = load_transcript(replay_case("gw5-rescore").fixture)
    assert case_output("gw5-rev") == read_text(rescorer, proposal_path(5))
    assert case_output("gw5-rescore") == git_text(replay_case("gw5-rescore").output.blob)
