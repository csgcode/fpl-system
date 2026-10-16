"""Unit tests for the residual persistence statistic: does a player's recent
EP error predict his next one?"""

from __future__ import annotations

import math
from collections.abc import Mapping

import pytest

from fpl.calibrate import (
    Aggregate,
    CalibrationReport,
    MinutesCalibration,
    PlayerLine,
    Uncertainty,
)
from fpl.persistence import persistence

ROUNDS = range(1, 6)
_ZERO = Aggregate(n=0, bias=0.0, mae=0.0)

Errors = Mapping[int, Mapping[int, float | None]]


def _line(pid: int, position: str, error: float | None) -> PlayerLine:
    started = error is not None
    return PlayerLine(
        id=pid,
        name=f"P{pid}",
        team="AAA",
        position=position,
        price=5.0,
        uncertainty=Uncertainty.MED,
        p_start=0.9,
        predicted=3.0,
        actual=0,
        error=error if started else -3.0,
        minutes=90 if started else 0,
        started=started,
    )


def _reports(
    errors: Errors, positions: Mapping[int, str] | None = None, rounds: range = ROUNDS
) -> list[CalibrationReport]:
    """`errors[pid][round]` is the error in a started round; None means the
    player did not start; a missing round means no ledger row."""
    positions = positions or {}
    return [
        CalibrationReport(
            round=r,
            players=tuple(
                _line(pid, positions.get(pid, "MID"), by_round[r])
                for pid, by_round in errors.items()
                if r in by_round
            ),
            unmatched_prediction_ids=(),
            overall=_ZERO,
            by_position={},
            by_uncertainty={},
            by_price_band={},
            minutes=MinutesCalibration(n=0, brier=0.0, expected_starts=0.0, actual_starts=0),
        )
        for r in rounds
    ]


def _all_started(values: list[float | None]) -> dict[int, float | None]:
    return dict(zip(ROUNDS, values, strict=True))


def test_exact_linear_persistence() -> None:
    # Players whose round-4 and round-5 errors are half their window mean.
    errors = {
        1: _all_started([2.0, 2.0, 2.0, 1.0, 0.5 * (2.0 + 2.0 + 1.0) / 3]),
        2: _all_started([-4.0, -4.0, -4.0, -2.0, 0.5 * (-4.0 - 4.0 - 2.0) / 3]),
        3: _all_started([0.0, 3.0, 6.0, 1.5, 0.5 * (3.0 + 6.0 + 1.5) / 3]),
    }

    result = persistence(_reports(errors))

    assert result.n == 6
    assert result.slope == pytest.approx(0.5)
    assert result.se_ols == pytest.approx(0.0, abs=1e-12)
    assert result.se_cluster == pytest.approx(0.0, abs=1e-12)
    assert result.r == pytest.approx(1.0)


def test_no_persistence() -> None:
    # Window mean x ∈ {−2, −1, 1, 2}, each paired once with y = +1 and once with −1.
    errors: dict[int, dict[int, float | None]] = {}
    pid = 0
    for x in (-2.0, -1.0, 1.0, 2.0):
        for y in (1.0, -1.0):
            pid += 1
            errors[pid] = {1: x, 2: x, 3: x, 4: y, 5: None}

    result = persistence(_reports(errors))

    assert result.n == 8
    assert result.slope == pytest.approx(0.0, abs=1e-12)
    assert result.ci_cluster[0] <= 0 <= result.ci_cluster[1]
    assert result.ci_ols[0] <= 0 <= result.ci_ols[1]
    assert not result.significant


def test_constant_y_gives_r_zero() -> None:
    errors = {pid: {1: float(pid), 2: float(pid), 3: float(pid), 4: 1.0} for pid in range(1, 5)}

    result = persistence(_reports(errors))

    assert result.r == 0
    assert result.slope == pytest.approx(0.0, abs=1e-12)


def test_inclusion_rules() -> None:
    errors = {
        1: {1: 1.0, 2: 1.0, 3: 1.0, 4: None},  # not started at the target round
        2: {1: 5.0, 2: None, 3: None, 4: 1.0},  # one window start
        3: {1: 2.0, 2: None, 3: 4.0, 4: 0.5},  # two starts: x = mean(2, 4)
        4: {1: 6.0, 3: 0.0, 4: 2.0},  # no ledger row in round 2: x = mean(6, 0)
    }

    result = persistence(_reports(errors), window=3, min_starts=2)

    assert {(p.id, p.round): (p.x, p.y) for p in result.pairs} == {
        (3, 4): (3.0, 0.5),
        (4, 4): (3.0, 2.0),
    }


def test_by_position_and_target_rounds() -> None:
    positions = {1: "DEF", 2: "DEF", 3: "FWD"}
    errors = {
        1: _all_started([1.0, 2.0, 3.0, 4.0, 5.0]),
        2: _all_started([0.0, -1.0, 2.0, 1.0, None]),
        3: _all_started([3.0, 1.0, -2.0, 0.0, 2.0]),
    }

    result = persistence(_reports(errors, positions))

    assert result.target_rounds == (4, 5)
    assert {pos: fit.n for pos, fit in result.by_position.items()} == {"DEF": 3, "FWD": 2}
    assert result.n == 5


def test_cluster_se_by_player() -> None:
    errors = {
        1: _all_started([1.0, 2.0, 3.0, 1.0, 4.0]),
        2: _all_started([-1.0, 0.0, -2.0, 2.0, -3.0]),
    }
    # Pairs (x, y) by player: window means over rounds t−3..t−1.
    by_player = {
        1: [(2.0, 1.0), (2.0, 4.0)],
        2: [(-1.0, 2.0), (0.0, -3.0)],
    }
    pairs = [p for ps in by_player.values() for p in ps]
    x_bar = sum(x for x, _ in pairs) / 4
    y_bar = sum(y for _, y in pairs) / 4
    sxx = sum((x - x_bar) ** 2 for x, _ in pairs)
    beta = sum((x - x_bar) * (y - y_bar) for x, y in pairs) / sxx
    alpha = y_bar - beta * x_bar
    meat = sum(
        sum((x - x_bar) * (y - alpha - beta * x) for x, y in ps) ** 2 for ps in by_player.values()
    )
    expected = math.sqrt(meat) / sxx

    result = persistence(_reports(errors))

    assert result.n == 4
    assert result.slope == pytest.approx(beta)
    assert result.se_cluster == pytest.approx(expected)
    assert result.ci_cluster == pytest.approx((beta - 1.96 * expected, beta + 1.96 * expected))


def test_significant_needs_enough_pairs_and_a_positive_clustered_ci() -> None:
    def strong(n_players: int) -> dict[int, dict[int, float | None]]:
        return {
            pid: {1: x, 2: x, 3: x, 4: x + (0.1 if pid % 2 else -0.1)}
            for pid in range(1, n_players + 1)
            for x in [float(pid % 7 - 3)]
        }

    assert persistence(_reports(strong(100))).significant
    assert not persistence(_reports(strong(99))).significant


def test_rejects_bad_parameters_and_duplicate_rounds() -> None:
    reports = _reports({1: _all_started([1.0] * 5)})

    with pytest.raises(ValueError, match="window"):
        persistence(reports, window=0)
    with pytest.raises(ValueError, match="min_starts"):
        persistence(reports, window=2, min_starts=3)
    with pytest.raises(ValueError, match="round 1"):
        persistence(reports + reports[:1])


def test_too_few_pairs_leaves_the_fit_undefined() -> None:
    errors = {1: _all_started([1.0, 2.0, 3.0, 4.0, None])}

    result = persistence(_reports(errors))

    assert result.n == 1
    assert result.slope is None
    assert result.se_cluster is None
    assert result.r == 0
    assert not result.significant
