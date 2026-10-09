"""Every marker that gates a squad-optimizer check must be in the current
spec. Losing one would silently turn its check into NA."""

from __future__ import annotations

import pytest

from evals.squad_optimizer.cases import REPO_ROOT, SPEC_FIXTURE
from evals.squad_optimizer.checks import CHECKS, MARK_RAW_CAPTAIN, SPEC_MARKERS

SPEC = (REPO_ROOT / "agents" / "squad-optimizer.md").read_text(encoding="utf-8")
CLAUDE = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("marker", SPEC_MARKERS)
def test_marker_is_in_the_current_spec(marker):
    assert marker in SPEC


def test_every_gating_marker_is_listed():
    assert {c.requires for c in CHECKS if c.requires} <= set(SPEC_MARKERS)


@pytest.mark.parametrize("marker", [m for m in SPEC_MARKERS if m != MARK_RAW_CAPTAIN])
def test_the_recorded_runs_spec_lacks_the_new_markers(marker):
    """Replay grades the runs against the spec they were given."""
    assert marker not in SPEC_FIXTURE.read_text(encoding="utf-8")


def test_the_prior_only_check_runs_through_objective_not_ep():
    assert "--prior-weight" not in SPEC
    assert "Record every attempted swap" not in SPEC


def test_claude_md_lists_objective_and_the_archive_exception():
    assert "| `objective " in CLAUDE
    assert "squad-proposal.v{k}.md" in CLAUDE
