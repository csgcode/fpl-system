"""Residual persistence: does a player's recent EP error predict his next one?

For each target round t and each player who started at t, x is his mean error
over the rounds t−window..t−1 he started, and y is his error at t. A player
needs at least `min_starts` window starts to enter. A round is a target only
when every round of its window has a ledger.

y is regressed on x by OLS. The slope's standard error is reported twice:
the classical OLS one, and one clustered by player (CR0 sandwich), because a
player contributes overlapping windows to consecutive target rounds. Only the
clustered interval decides `significant`.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from fpl.calibrate import CalibrationReport, PlayerLine

Z = 1.96
MIN_PAIRS = 100


@dataclass(frozen=True)
class Pair:
    id: int
    position: str
    round: int
    x: float
    y: float


@dataclass(frozen=True)
class Fit:
    """OLS of y on x. Slope, intercept, standard errors and intervals are
    None when fewer than three pairs or x does not vary. `r` is 0 when either
    x or y does not vary."""

    n: int
    slope: float | None
    intercept: float | None
    se_ols: float | None
    se_cluster: float | None
    ci_ols: tuple[float, float] | None
    ci_cluster: tuple[float, float] | None
    r: float


@dataclass(frozen=True)
class PersistenceResult(Fit):
    window: int
    min_starts: int
    target_rounds: tuple[int, ...]
    pairs: tuple[Pair, ...]
    by_position: dict[str, Fit]
    significant: bool


def persistence(
    reports: Iterable[CalibrationReport], *, window: int = 3, min_starts: int = 2
) -> PersistenceResult:
    """Pool (x, y) pairs over every target round and fit y = α + βx.

    `significant` is True only with at least MIN_PAIRS pairs and a clustered
    95% interval for β lying wholly above 0.
    """
    if window < 1:
        raise ValueError(f"window must be ≥ 1, got {window}")
    if not 1 <= min_starts <= window:
        raise ValueError(f"min_starts must be in 1..{window}, got {min_starts}")
    by_round: dict[int, dict[int, PlayerLine]] = {}
    for report in reports:
        if report.round in by_round:
            raise ValueError(f"two ledgers for round {report.round}")
        by_round[report.round] = {line.id: line for line in report.players}

    targets = tuple(
        t
        for t in sorted(by_round)
        if all(r in by_round for r in range(t - window, t))
    )
    pairs = tuple(
        pair for t in targets for pair in _pairs_at(by_round, t, window, min_starts)
    )
    positions: dict[str, list[Pair]] = {}
    for pair in pairs:
        positions.setdefault(pair.position, []).append(pair)
    overall = _fit(pairs)
    return PersistenceResult(
        **vars(overall),
        window=window,
        min_starts=min_starts,
        target_rounds=targets,
        pairs=pairs,
        by_position={pos: _fit(ps) for pos, ps in sorted(positions.items())},
        significant=(
            overall.n >= MIN_PAIRS
            and overall.ci_cluster is not None
            and overall.ci_cluster[0] > 0
        ),
    )


def _pairs_at(
    by_round: dict[int, dict[int, PlayerLine]], t: int, window: int, min_starts: int
) -> list[Pair]:
    pairs = []
    for line in by_round[t].values():
        if not line.started:
            continue
        past = [by_round[r].get(line.id) for r in range(t - window, t)]
        errors = [p.error for p in past if p is not None and p.started]
        if len(errors) >= min_starts:
            pairs.append(Pair(line.id, line.position, t, sum(errors) / len(errors), line.error))
    return pairs


def _fit(pairs: Sequence[Pair]) -> Fit:
    n = len(pairs)
    if n == 0:
        return Fit(0, None, None, None, None, None, None, 0.0)
    x_bar = sum(p.x for p in pairs) / n
    y_bar = sum(p.y for p in pairs) / n
    sxx = sum((p.x - x_bar) ** 2 for p in pairs)
    syy = sum((p.y - y_bar) ** 2 for p in pairs)
    sxy = sum((p.x - x_bar) * (p.y - y_bar) for p in pairs)
    r = sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else 0.0
    if n < 3 or sxx == 0:
        return Fit(n, None, None, None, None, None, None, r)

    slope = sxy / sxx
    intercept = y_bar - slope * x_bar
    residuals = [p.y - intercept - slope * p.x for p in pairs]
    s2 = sum(u * u for u in residuals) / (n - 2)
    se_ols = math.sqrt(s2 / sxx)
    scores: dict[int, float] = {}
    for p, u in zip(pairs, residuals, strict=True):
        scores[p.id] = scores.get(p.id, 0.0) + (p.x - x_bar) * u
    se_cluster = math.sqrt(sum(s * s for s in scores.values())) / sxx
    return Fit(
        n=n,
        slope=slope,
        intercept=intercept,
        se_ols=se_ols,
        se_cluster=se_cluster,
        ci_ols=(slope - Z * se_ols, slope + Z * se_ols),
        ci_cluster=(slope - Z * se_cluster, slope + Z * se_cluster),
        r=r,
    )
