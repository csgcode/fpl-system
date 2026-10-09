"""Every marker that gates a data-collector check must be in the current
spec. Losing one would silently turn its check into NA."""

from __future__ import annotations

import pytest

from evals.data_collector.cases import REPO_ROOT
from evals.data_collector.checks import CHECKS, MARKERS

SPEC = (REPO_ROOT / "agents" / "data-collector.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("marker", MARKERS)
def test_marker_is_in_the_current_spec(marker):
    assert marker in SPEC


def test_every_gating_marker_is_listed():
    assert {c.requires for c in CHECKS if c.requires} <= set(MARKERS)
