"""Consistency columns: the chance a player returns at least k points.

`p_at_least` builds an integer points distribution for a gameweek from the
same per-fixture means the EP formula uses, then reads its upper tail. Given a
start, one fixture's points are the sum of independent parts:

- appearance: 2 with probability `p60` (60+ minutes), else 1;
- clean sheet: `cs_pts` with probability `p_cs`, in the 60+ branch only;
- goals: Poisson(`goal_mean`) × `goal_pts`, the goal count truncated at 10;
- assists: Poisson(`assist_mean`) × 3;
- DefCon: 2 with probability `p_defcon`;
- saves: ⌊S/3⌋ for S ~ Poisson(`saves_mean`).

A double gameweek convolves its fixtures. Points run 0..40; mass above 40 is
kept at 40.

Left out, with the direction each omission biases P(X ≥ k):

- bonus points: biases P down;
- goals conceded, and its dependence on the clean sheet: biases GKP/DEF up;
- yellow and red cards, own goals, missed penalties: bias P up;
- penalty saves: biases GKP down, slightly.

Inputs are plain floats so the module stays independent of `fpl.ep`.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, fields

MAX_POINTS = 40
MAX_GOALS = 10
ASSIST_PTS = 3
DEFCON_PTS = 2
SAVES_PER_POINT = 3
APPEARANCE_PTS_60 = 2
APPEARANCE_PTS_SHORT = 1

_PROBABILITIES = ("p60", "p_cs", "p_defcon")
_MEANS = ("goal_mean", "assist_mean", "saves_mean")
_POINTS = ("goal_pts", "cs_pts")

Pmf = list[float]


@dataclass(frozen=True)
class FixtureMeans:
    """One fixture's scoring inputs, conditional on the player starting."""

    goal_pts: int
    goal_mean: float = 0.0
    assist_mean: float = 0.0
    p60: float = 0.0
    p_cs: float = 0.0
    cs_pts: int = 0
    p_defcon: float = 0.0
    saves_mean: float = 0.0

    def __post_init__(self) -> None:
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name in _PROBABILITIES:
                _check_probability(f.name, value)
            elif f.name in _MEANS:
                if not (math.isfinite(value) and value >= 0):
                    raise ValueError(f"{f.name} must be a finite mean ≥ 0, got {value!r}")
            elif f.name in _POINTS:
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise ValueError(f"{f.name} must be an integer ≥ 0, got {value!r}")


def p_at_least(fixtures: Sequence[FixtureMeans], p_start: float, k: int) -> float:
    """P(points ≥ k) in a gameweek: `p_start` × the tail of the convolved
    fixture distribution. A blank gameweek (no fixtures) scores 0 points."""
    _check_probability("p_start", p_start)
    pmf = _point_mass(0)
    for fixture in fixtures:
        pmf = _convolve(pmf, fixture_pmf(fixture))
    tail = sum(pmf[max(k, 0) :]) if k <= MAX_POINTS else 0.0
    return p_start * min(tail, 1.0)


def fixture_pmf(fm: FixtureMeans) -> Pmf:
    """Points distribution on 0..MAX_POINTS for one fixture, given a start."""
    cs = _bernoulli(fm.cs_pts, fm.p_cs)
    full = _convolve(_point_mass(APPEARANCE_PTS_60), cs)
    short = _point_mass(APPEARANCE_PTS_SHORT)
    pmf = [fm.p60 * a + (1 - fm.p60) * b for a, b in zip(full, short, strict=True)]
    parts = (
        _poisson_points(fm.goal_mean, lambda n: n * fm.goal_pts, max_count=MAX_GOALS),
        _poisson_points(fm.assist_mean, lambda n: n * ASSIST_PTS),
        _bernoulli(DEFCON_PTS, fm.p_defcon),
        _poisson_points(fm.saves_mean, lambda n: n // SAVES_PER_POINT),
    )
    for part in parts:
        pmf = _convolve(pmf, part)
    return pmf


def _check_probability(name: str, value: float) -> None:
    if not (math.isfinite(value) and 0.0 <= value <= 1.0):
        raise ValueError(f"{name} must be a probability in [0, 1], got {value!r}")


def _point_mass(points: int) -> Pmf:
    pmf = [0.0] * (MAX_POINTS + 1)
    pmf[min(points, MAX_POINTS)] = 1.0
    return pmf


def _bernoulli(points: int, p: float) -> Pmf:
    pmf = [0.0] * (MAX_POINTS + 1)
    pmf[0] += 1 - p
    pmf[min(points, MAX_POINTS)] += p
    return pmf


def _poisson_points(mean: float, points_of: Callable[[int], int], max_count: int | None = None) -> Pmf:
    """Distribution of points_of(N) for N ~ Poisson(mean). The tail from the
    first count that reaches MAX_POINTS (or `max_count`) sits at that count."""
    pmf = [0.0] * (MAX_POINTS + 1)
    p_n = math.exp(-mean)
    cumulative = 0.0
    n = 0
    while True:
        points = points_of(n)
        if points >= MAX_POINTS or n == max_count:
            pmf[min(points, MAX_POINTS)] += max(1.0 - cumulative, 0.0)
            return pmf
        pmf[points] += p_n
        cumulative += p_n
        n += 1
        p_n *= mean / n


def _convolve(a: Pmf, b: Pmf) -> Pmf:
    out = [0.0] * (MAX_POINTS + 1)
    for i, pa in enumerate(a):
        if pa == 0.0:
            continue
        for j, pb in enumerate(b):
            if pb:
                out[min(i + j, MAX_POINTS)] += pa * pb
    return out
