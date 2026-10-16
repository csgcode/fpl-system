"""Unit tests for the consistency columns: P(≥k points) from the per-term
point distribution."""

from __future__ import annotations

import math

import pytest

from fpl.consistency import FixtureMeans, p_at_least


def test_goal_only_forward_returns_on_any_goal() -> None:
    mu = 0.45
    fm = FixtureMeans(goal_pts=4, goal_mean=mu)

    assert p_at_least([fm], p_start=0.9, k=4) == pytest.approx(0.9 * (1 - math.exp(-mu)))


def test_defcon_reaches_four_only_in_the_sixty_minute_branch() -> None:
    fm = FixtureMeans(goal_pts=5, p_defcon=0.4, p60=0.75)

    assert p_at_least([fm], p_start=1.0, k=4) == pytest.approx(0.75 * 0.4)


def test_defender_clean_sheet_with_full_minutes() -> None:
    fm = FixtureMeans(goal_pts=6, p_cs=0.3, cs_pts=4, p60=1.0)

    assert p_at_least([fm], p_start=1.0, k=4) == pytest.approx(0.3)


def test_goalkeeper_needs_six_saves_for_two_save_points() -> None:
    fm = FixtureMeans(goal_pts=10, saves_mean=6.0, p60=1.0, p_cs=0.0)
    p_le_5 = sum(math.exp(-6.0) * 6.0**s / math.factorial(s) for s in range(6))

    p = p_at_least([fm], p_start=1.0, k=4)

    assert p == pytest.approx(1 - p_le_5)
    assert p == pytest.approx(0.5543, abs=1e-4)


def test_double_gameweek_short_minutes_convolves_goals() -> None:
    mu = 0.3
    fms = [FixtureMeans(goal_pts=4, goal_mean=mu, p60=0.0) for _ in range(2)]

    assert p_at_least(fms, p_start=1.0, k=4) == pytest.approx(1 - math.exp(-2 * mu))


def test_double_gameweek_appearance_points_alone_reach_four() -> None:
    fms = [FixtureMeans(goal_pts=4, p60=1.0) for _ in range(2)]

    assert p_at_least(fms, p_start=1.0, k=4) == pytest.approx(1.0)


def test_no_start_gives_zero() -> None:
    fm = FixtureMeans(goal_pts=4, goal_mean=2.0, p60=1.0)

    assert p_at_least([fm], p_start=0.0, k=4) == 0.0


def test_blank_gameweek_gives_zero() -> None:
    assert p_at_least([], p_start=1.0, k=4) == 0.0


def test_distribution_mass_is_kept_at_the_cap() -> None:
    fm = FixtureMeans(goal_pts=6, goal_mean=8.0, assist_mean=8.0, saves_mean=30.0, p60=1.0)

    assert p_at_least([fm], p_start=1.0, k=0) == pytest.approx(1.0)
    assert p_at_least([fm], p_start=1.0, k=40) > 0.5


@pytest.mark.parametrize(
    "field, value",
    [("goal_mean", -0.1), ("p60", 1.2), ("p_cs", -0.01), ("p_defcon", 1.5), ("saves_mean", math.nan)],
)
def test_out_of_range_inputs_refuse(field: str, value: float) -> None:
    with pytest.raises(ValueError, match=field):
        FixtureMeans(goal_pts=4, **{field: value})


def test_out_of_range_p_start_refuses() -> None:
    with pytest.raises(ValueError, match="p_start"):
        p_at_least([FixtureMeans(goal_pts=4)], p_start=1.1, k=4)


@pytest.mark.parametrize("value", [-1, 4.0, True])
def test_points_per_event_must_be_a_non_negative_integer(value: object) -> None:
    with pytest.raises(ValueError, match="cs_pts"):
        FixtureMeans(goal_pts=4, cs_pts=value)  # type: ignore[arg-type]
