"""Unit tests for the team-xG cross-check: a player's observed share of his
club's xG."""

from __future__ import annotations

from typing import Any

import pytest

from fpl.models import MatchRecord
from fpl.team_share import RECENT_STARTS, observed_shares


def _row(fixture: int, rnd: int, *, home: bool | None, starts: int, xg: float, xa: float) -> MatchRecord:
    overrides: dict[str, Any] = {
        "fixture": fixture, "round": rnd, "was_home": home, "starts": starts,
        "expected_goals": xg, "expected_assists": xa,
    }
    return MatchRecord.model_validate(
        {"minutes": 90 if starts else 20, "total_points": 2, "goals_scored": 0, "assists": 0} | overrides
    )


def test_observed_shares_over_started_matches() -> None:
    club_xg = {(10, "H"): 1.5, (11, "A"): 1.0, (12, "H"): 2.0}
    history = [
        _row(10, 1, home=True, starts=1, xg=0.3, xa=0.2),
        _row(11, 2, home=False, starts=1, xg=0.5, xa=0.0),
        _row(12, 3, home=True, starts=0, xg=0.4, xa=0.0),
    ]

    shares = observed_shares(history, club_xg)

    assert shares.starts == 2
    assert shares.xg_season == pytest.approx(0.8 / 2.5)
    assert shares.xa_season == pytest.approx(0.2 / 2.5)
    assert shares.xg_recent == pytest.approx(0.8 / 2.5)
    assert shares.xa_recent == pytest.approx(0.2 / 2.5)


def test_recent_uses_the_last_four_started_matches() -> None:
    club_xg = {(f, "H"): 1.0 for f in range(1, 6)}
    history = [_row(f, f, home=True, starts=1, xg=1.0 if f == 1 else 0.0, xa=0.0) for f in range(5, 0, -1)]

    shares = observed_shares(history, club_xg)

    assert RECENT_STARTS == 4
    assert shares.starts == 5
    assert shares.xg_season == pytest.approx(1.0 / 5.0)
    assert shares.xg_recent == pytest.approx(0.0)


def test_rows_outside_the_club_map_do_not_count() -> None:
    club_xg = {(10, "H"): 1.0}
    history = [
        _row(10, 1, home=True, starts=1, xg=0.5, xa=0.0),
        _row(10, 1, home=False, starts=1, xg=0.9, xa=0.0),
        _row(11, 2, home=True, starts=1, xg=0.9, xa=0.0),
        _row(12, 3, home=None, starts=1, xg=0.9, xa=0.0),
    ]

    shares = observed_shares(history, club_xg)

    assert shares.starts == 1
    assert shares.xg_season == pytest.approx(0.5)


def test_no_counted_start_gives_no_share() -> None:
    shares = observed_shares([_row(10, 1, home=True, starts=0, xg=0.4, xa=0.1)], {(10, "H"): 1.0})

    assert shares.starts == 0
    assert shares.xg_season is None
    assert shares.xa_season is None
    assert shares.xg_recent is None
    assert shares.xa_recent is None


def test_zero_club_xg_gives_no_share() -> None:
    shares = observed_shares([_row(10, 1, home=True, starts=1, xg=0.0, xa=0.0)], {(10, "H"): 0.0})

    assert shares.starts == 1
    assert shares.xg_season is None
    assert shares.xa_recent is None
