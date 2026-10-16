"""Unit tests for the team-xG cross-check: a player's observed share of his
club's xG."""

from __future__ import annotations

from typing import Any

import pytest

from fpl.models import MatchRecord
from fpl.team_share import (
    RECENT_STARTS,
    SHARE_ABS_TOL,
    SHARE_MIN_STARTS,
    SHARE_REL_TOL,
    Shares,
    details,
    implied_share,
    labels,
    observed_shares,
    share_flags,
)


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


def _season(xg: float | None, xa: float | None = None, *, starts: int = 4) -> Shares:
    return Shares(xg_season=xg, xa_season=xa, xg_recent=xg, xa_recent=xa, starts=starts)


def test_implied_share() -> None:
    implied = implied_share(rate90=0.45, mps=90, attack_mult=1.0, base_mean=1.435, att_club=1.2)

    assert implied == pytest.approx(0.45 / (1.435 * 1.2))
    assert implied == pytest.approx(0.2613, abs=1e-4)


def test_implied_share_caps_minutes_at_a_full_match_and_scales_by_attack_mult() -> None:
    capped = implied_share(rate90=0.45, mps=120, attack_mult=1.0, base_mean=1.435, att_club=1.2)
    partial = implied_share(rate90=0.45, mps=60, attack_mult=0.8, base_mean=1.435, att_club=1.2)

    assert capped == pytest.approx(0.45 / (1.435 * 1.2))
    assert partial == pytest.approx(0.45 * 60 / 90 * 0.8 / (1.435 * 1.2))


def test_flag_when_far_apart() -> None:
    flags = share_flags(implied_xg=0.30, implied_xa=None, shares=_season(0.18))

    assert labels(flags) == "xG EP>club"


def test_no_flag_inside_tolerance() -> None:
    assert SHARE_ABS_TOL == 0.05
    assert SHARE_REL_TOL == 0.4
    assert share_flags(implied_xg=0.22, implied_xa=None, shares=_season(0.18)) == ()
    assert labels(()) is None


def test_tolerance_floor_is_absolute_for_small_shares() -> None:
    assert share_flags(implied_xg=0.09, implied_xa=None, shares=_season(0.05)) == ()
    assert labels(share_flags(implied_xg=0.11, implied_xa=None, shares=_season(0.05))) == "xG EP>club"


def test_no_flag_under_three_starts() -> None:
    assert SHARE_MIN_STARTS == 3
    assert share_flags(implied_xg=0.30, implied_xa=0.30, shares=_season(0.18, 0.05, starts=2)) == ()
    assert labels(share_flags(implied_xg=0.30, implied_xa=None, shares=_season(0.18, starts=3))) == "xG EP>club"


def test_no_flag_without_a_season_share() -> None:
    assert share_flags(implied_xg=0.30, implied_xa=0.30, shares=_season(None, None)) == ()


def test_both_xg_and_xa_flagged() -> None:
    flags = share_flags(implied_xg=0.30, implied_xa=0.02, shares=_season(0.18, 0.12))

    assert labels(flags) == "xG EP>club; xA EP<club"
    assert details(flags) == (
        "xG EP>club (implied 0.30, season 0.18, 4 starts); "
        "xA EP<club (implied 0.02, season 0.12, 4 starts)"
    )
