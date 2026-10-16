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

import argparse
import json
import math
import re
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fpl.calibrate import CalibrationReport, PlayerLine, load_report

Z = 1.96
MIN_PAIRS = 100
RETRO_ROOT = Path("data/retro")
EXIT_ERROR = 1
EXIT_NOT_SIGNIFICANT = 3
_LEDGER = re.compile(r"^gw(\d+)-calibration\.json$")


@dataclass(frozen=True)
class Pair:
    id: int
    position: str
    round: int
    x: float
    y: float


@dataclass(frozen=True)
class Fit:
    """OLS of y on x. Slope, intercept, standard errors, intervals and `r` are
    None when fewer than three pairs or x does not vary. `r` is 0 when y does
    not vary."""

    n: int
    slope: float | None
    intercept: float | None
    se_ols: float | None
    se_cluster: float | None
    ci_ols: tuple[float, float] | None
    ci_cluster: tuple[float, float] | None
    r: float | None


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
    if n < 3:
        return Fit(n, None, None, None, None, None, None, None)
    x_bar = sum(p.x for p in pairs) / n
    y_bar = sum(p.y for p in pairs) / n
    sxx = sum((p.x - x_bar) ** 2 for p in pairs)
    if sxx == 0:
        return Fit(n, None, None, None, None, None, None, None)
    syy = sum((p.y - y_bar) ** 2 for p in pairs)
    sxy = sum((p.x - x_bar) * (p.y - y_bar) for p in pairs)
    r = sxy / math.sqrt(sxx * syy) if syy > 0 else 0.0

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


def register(add: Callable[..., argparse.ArgumentParser]) -> None:
    parser = add(
        "persistence",
        "does a player's recent EP residual predict his next one "
        f"(exit {EXIT_NOT_SIGNIFICANT}: not significant)",
        cached=False,
    )
    parser.add_argument("--window", type=int, default=3,
                        help="rounds before the target averaged into x (default 3)")
    parser.add_argument("--min-starts", type=int, default=2,
                        help="window starts a player needs to enter (default 2)")
    parser.add_argument("--retro-root", type=Path, default=RETRO_ROOT,
                        help="where gw{M}-calibration.json ledgers live; only M < --gw is read")
    parser.add_argument("--format", choices=("table", "json"), default="table")


def run(args: argparse.Namespace) -> int:
    try:
        reports = load_ledgers(args.retro_root, args.gw)
        results = [persistence(reports, window=args.window, min_starts=args.min_starts)]
        results += [
            persistence(reports, window=w, min_starts=min(args.min_starts, w))
            for w in range(1, args.window)
        ]
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    rounds = [report.round for report in reports]
    if args.format == "json":
        print(json.dumps(
            {
                "gw": args.gw,
                "rounds": rounds,
                "significant": results[0].significant,
                "windows": [to_document(result) for result in results],
            },
            indent=1,
        ))
    else:
        print(f"ledgers: rounds {_span(rounds)} from {args.retro_root}")
        _print_result(results[0])
        print("sensitivity:")
        for result in results[1:]:
            _print_result(result)
    return 0 if results[0].significant else EXIT_NOT_SIGNIFICANT


def load_ledgers(retro_root: Path, gw: int) -> list[CalibrationReport]:
    """Every gw{M}-calibration.json under `retro_root` with M < gw, in round order."""
    found = sorted(
        (int(match.group(1)), path)
        for path in (retro_root.iterdir() if retro_root.is_dir() else ())
        if (match := _LEDGER.match(path.name)) and int(match.group(1)) < gw
    )
    if not found:
        raise ValueError(f"no calibration ledgers before GW{gw} under {retro_root}")
    reports = []
    for _, path in found:
        try:
            reports.append(load_report(path))
        except OSError as exc:
            raise ValueError(f"cannot read ledger {path}: {exc.strerror or exc}") from exc
    return reports


def to_document(result: PersistenceResult) -> dict[str, Any]:
    """The result as JSON-ready fields, without the per-pair rows."""
    return {
        "window": result.window,
        "min_starts": result.min_starts,
        "target_rounds": list(result.target_rounds),
        **_fit_document(result),
        "significant": result.significant,
        "by_position": {pos: _fit_document(fit) for pos, fit in result.by_position.items()},
    }


def _fit_document(fit: Fit) -> dict[str, Any]:
    return {
        "n": fit.n,
        "slope": fit.slope,
        "intercept": fit.intercept,
        "se_ols": fit.se_ols,
        "se_cluster": fit.se_cluster,
        "ci_ols": list(fit.ci_ols) if fit.ci_ols else None,
        "ci_cluster": list(fit.ci_cluster) if fit.ci_cluster else None,
        "r": fit.r,
    }


def _print_result(result: PersistenceResult) -> None:
    verdict = "significant" if result.significant else "not significant"
    print(f"window {result.window}, min starts {result.min_starts}: "
          f"{_fit_text(result)} — {verdict}")
    for pos, fit in result.by_position.items():
        print(f"  {pos}: {_fit_text(fit)}")


def _fit_text(fit: Fit) -> str:
    if fit.slope is None or fit.ci_cluster is None:
        slope = "slope n/a"
    else:
        lo, hi = fit.ci_cluster
        slope = f"slope {fit.slope:.3f} [{lo:.3f}, {hi:.3f}] (cluster)"
    r = "n/a" if fit.r is None else f"{fit.r:.3f}"
    return f"n {fit.n}, {slope}, r {r}"


def _span(rounds: Sequence[int]) -> str:
    if rounds == list(range(rounds[0], rounds[-1] + 1)):
        return f"{rounds[0]}-{rounds[-1]}" if len(rounds) > 1 else str(rounds[0])
    return ", ".join(map(str, rounds))
