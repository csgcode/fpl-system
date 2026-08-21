"""Contract test against a real captured snapshot.

Skipped unless FPL_LIVE_SNAPSHOT_DIR points at a gameweek directory holding a
bootstrap.json (and optionally players/summary-*.json) fetched from the live
API. Synthetic factories can drift from the real payload; this pins the model
contract to what the API actually sends.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from fpl.models import Bootstrap, ElementSummary, is_shortlisted

SNAPSHOT_DIR = os.environ.get("FPL_LIVE_SNAPSHOT_DIR")

pytestmark = pytest.mark.skipif(
    not SNAPSHOT_DIR, reason="FPL_LIVE_SNAPSHOT_DIR is not set"
)


@pytest.fixture(scope="module")
def snapshot_dir() -> Path:
    path = Path(SNAPSHOT_DIR or "")
    if not (path / "bootstrap.json").is_file():
        pytest.skip(f"no bootstrap.json under {path}")
    return path


@pytest.fixture(scope="module")
def bootstrap(snapshot_dir) -> Bootstrap:
    return Bootstrap.model_validate(
        json.loads((snapshot_dir / "bootstrap.json").read_text(encoding="utf-8"))
    )


def test_live_bootstrap_validates(bootstrap):
    assert bootstrap.elements
    assert bootstrap.teams
    assert bootstrap.events


def test_live_bootstrap_carries_chips(bootstrap):
    assert bootstrap.chips
    assert {c.name for c in bootstrap.chips} >= {"wildcard", "freehit"}
    assert all(c.start_event <= c.stop_event for c in bootstrap.chips)


def test_live_players_carry_the_new_stat_fields(bootstrap):
    player = max(bootstrap.elements, key=lambda p: p.minutes)
    for field in (
        "starts", "clean_sheets", "goals_conceded", "expected_goals_conceded",
        "saves", "cost_change_start", "cost_change_event",
        "clearances_blocks_interceptions", "recoveries", "tackles",
    ):
        assert getattr(player, field) is not None


def test_live_bootstrap_has_no_dangling_team_references(bootstrap):
    team_ids = {t.id for t in bootstrap.teams}
    assert all(p.team in team_ids for p in bootstrap.elements)


def test_live_shortlist_is_a_strict_subset_of_all_players(bootstrap):
    shortlisted = [p for p in bootstrap.elements if is_shortlisted(p)]
    assert 0 < len(shortlisted) < len(bootstrap.elements)


def test_live_element_summaries_validate(snapshot_dir):
    summaries = sorted((snapshot_dir / "players").glob("summary-*.json"))
    if not summaries:
        pytest.skip("no element summaries in this snapshot")
    for path in summaries:
        summary = ElementSummary.model_validate(
            json.loads(path.read_text(encoding="utf-8"))
        )
        for season in summary.history_past:
            assert season.season_name[4] == "/"
            assert season.bps is not None
