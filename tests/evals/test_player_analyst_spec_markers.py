"""Every marker that gates a player-analyst check must be in the current
spec. Losing one would silently turn its check into NA."""

from __future__ import annotations

import pytest

from evals.player_analyst.cases import REPO_ROOT, SPEC_PATH
from evals.player_analyst.checks import CHECKS, MARKERS

SPEC = (REPO_ROOT / SPEC_PATH).read_text(encoding="utf-8")


@pytest.mark.parametrize("marker", MARKERS)
def test_marker_is_in_the_current_spec(marker):
    assert marker in SPEC


def test_every_gating_marker_is_listed():
    assert {c.requires for c in CHECKS if c.requires} <= set(MARKERS)


def test_the_recorded_spec_lacks_the_new_markers():
    recorded = (REPO_ROOT / "evals/fixtures/player-analyst/spec-0ff0db4.md").read_text("utf-8")
    assert [m for m in MARKERS if m in recorded] == []


@pytest.mark.parametrize("line", [
    "Return plain lines, no tables or headings, ≤ 15 lines in all",
    "Return plain lines, no tables or headings, ≤ 10 lines in all",
])
def test_the_return_limits_rule_out_formatted_reports(line):
    assert line in " ".join(SPEC.split())
