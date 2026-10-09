"""Every marker that gates a finalizer check must be in the current spec.
Losing one would silently turn its check into NA."""

from __future__ import annotations

import pytest

from evals.finalizer.cases import REPO_ROOT, SPEC_FIXTURE
from evals.finalizer.checks import CHECKS, SPEC_MARKERS

SPEC = (REPO_ROOT / "agents" / "finalizer.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("marker", SPEC_MARKERS)
def test_marker_is_in_the_current_spec(marker):
    assert marker in SPEC


def test_every_gating_marker_is_listed():
    assert {c.requires for c in CHECKS if c.requires} <= set(SPEC_MARKERS)


@pytest.mark.parametrize("marker", [m for m in SPEC_MARKERS if m != "At most 12 lines"])
def test_the_recorded_runs_spec_lacks_the_new_markers(marker):
    """Replay grades the runs against the spec they were given; a marker
    already in it would mean its check grades them on a rule they had."""
    assert marker not in SPEC_FIXTURE.read_text(encoding="utf-8")


def test_the_market_basis_rule_lives_in_the_correction_section():
    correction = SPEC.split("## 5.", 1)[-1]
    assert "market basis (last_deadline_value)" in correction


def test_the_pre_gate_steps_do_not_stop_a_correction():
    """A correction edits the final.md that already exists, so §0's
    'final.md exists, stop' must not apply to it."""
    before_gate = SPEC.split("## 0.", 1)[1].split("## 1.", 1)[0]
    assert "§5" in before_gate


def test_the_value_check_runs_before_final_md_is_written():
    """A value-drift stop must leave no final.md behind."""
    assemble = SPEC.split("## 2.", 1)[1].split("## 3.", 1)[0]
    assert assemble.index("my-team") < assemble.index("Squad table")


def test_the_spec_states_where_the_agent_may_write():
    """C9 grades writes against this remit, so the spec must state it."""
    rules = SPEC.split("## 4.", 1)[1].split("## 5.", 1)[0]
    assert "outside the repo" in rules


def test_the_ep_column_is_copied_unrounded():
    """C7 compares the column with ep_gw[0] to within 0.0015."""
    assemble = SPEC.split("## 2.", 1)[1].split("## 3.", 1)[0]
    assert "not rounded" in assemble


def test_the_return_forbids_notes_around_the_fixed_lines():
    """Under the fixed format, C12 fails any line that is not a keyed line."""
    section = " ".join(SPEC.split("## Return to the orchestrator", 1)[1].split())
    assert "Add nothing before or after them" in section
