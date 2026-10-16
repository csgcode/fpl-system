"""Every marker that gates a retro-analyst check must be in the current spec.
Losing one would silently turn its check into NA."""

from __future__ import annotations

import pytest

from evals.retro_analyst.cases import REPO_ROOT, SPEC_FIXTURE
from evals.retro_analyst.checks import CHECKS, MARK_RETIRE_C16, SPEC_MARKERS

SPEC = (REPO_ROOT / "agents" / "retro-analyst.md").read_text(encoding="utf-8")
CLAUDE = " ".join((REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8").split())


@pytest.mark.parametrize("marker", SPEC_MARKERS)
def test_marker_is_in_the_current_spec(marker):
    assert marker in SPEC


def test_every_gating_marker_is_listed():
    assert {c.requires for c in CHECKS if c.requires} <= set(SPEC_MARKERS)


@pytest.mark.parametrize("marker", [m for m in SPEC_MARKERS if m != MARK_RETIRE_C16])
def test_the_recorded_runs_spec_lacks_the_new_markers(marker):
    """Replay grades the runs against the spec they were given; a marker
    already in it would mean its check grades them on a rule they had."""
    assert marker not in SPEC_FIXTURE.read_text(encoding="utf-8")


def test_call_1_no_longer_cats_final_md_or_loops_over_the_retros():
    call_1 = SPEC.split("Call 1", 1)[1].split("Call 2", 1)[0]
    assert "cat data/decisions" not in call_1
    assert "for f in data/retro" not in call_1


def test_corrections_section_ends_at_the_next_header():
    assert "nothing after that header may be narrative" not in SPEC
    assert "About 120 lines" not in SPEC


def test_claude_md_orders_the_retro_after_the_collector_and_lists_corrections():
    assert "calibrate reads that snapshot's data_checked flag" in CLAUDE
    assert "squad misses" in CLAUDE
