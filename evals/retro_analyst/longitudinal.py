"""Season-level view of the retro loop (report only, never pass/fail): the
per-round calibration series from the ledgers, and for each registered
correction its metric before and after the round that issued it."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from fpl.calibrate import CalibrationReport, load_report

_LEDGER = re.compile(r"gw(\d+)-calibration\.json")


@dataclass(frozen=True)
class RoundStats:
    round: int
    starts_gap: float
    """Expected minus actual starts: positive means p_start ran high."""
    def_minus_mid: float | None
    cumulative_mae: float | None
    cumulative_brier: float | None


@dataclass(frozen=True)
class Registered:
    correction: str
    issued_after: int
    metric: str
    label: str


@dataclass(frozen=True)
class Effect:
    registered: Registered
    before: float | None
    after: float | None


# Hand-written: a handful of entries do not justify automation.
REGISTRY = (
    Registered("C18", 4, "starts_gap", "expected − actual starts"),
    Registered("C9", 2, "def_minus_mid", "DEF bias − MID bias"),
)


def load_ledgers(root: Path) -> list[CalibrationReport]:
    found = [(int(m[1]), path) for path in root.glob("gw*-calibration.json")
             if (m := _LEDGER.fullmatch(path.name))]
    return [load_report(path) for _, path in sorted(found)]


def series(ledgers: list[CalibrationReport]) -> list[RoundStats]:
    stats = []
    for report in sorted(ledgers, key=lambda r: r.round):
        positions = report.by_position
        gap = None
        if "DEF" in positions and "MID" in positions:
            gap = positions["DEF"].bias - positions["MID"].bias
        cumulative = report.cumulative
        stats.append(RoundStats(
            round=report.round,
            starts_gap=report.minutes.expected_starts - report.minutes.actual_starts,
            def_minus_mid=gap,
            cumulative_mae=cumulative.overall.mae if cumulative else None,
            cumulative_brier=cumulative.minutes_brier if cumulative else None,
        ))
    return stats


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def effect(rounds: list[RoundStats], registered: Registered) -> Effect:
    def values(after: bool) -> list[float]:
        picked = [getattr(s, registered.metric) for s in rounds
                  if (s.round > registered.issued_after) == after]
        return [v for v in picked if v is not None]

    return Effect(registered, _mean(values(False)), _mean(values(True)))


def _fmt(value: float | None, digits: int = 2) -> str:
    return "-" if value is None else f"{value:+.{digits}f}"


def print_report(root: Path) -> int:
    rounds = series(load_ledgers(root))
    if not rounds:
        print(f"no calibration ledgers under {root}")
        return 0
    print(f"{'round':>5} {'starts gap':>11} {'DEF-MID':>8} {'cum MAE':>8} {'cum Brier':>10}")
    for s in rounds:
        mae = "-" if s.cumulative_mae is None else f"{s.cumulative_mae:.3f}"
        brier = "-" if s.cumulative_brier is None else f"{s.cumulative_brier:.4f}"
        print(f"{s.round:>5} {_fmt(s.starts_gap):>11} {_fmt(s.def_minus_mid, 3):>8} "
              f"{mae:>8} {brier:>10}")
    print()
    print("correction  issued after  metric                     before    after")
    for registered in REGISTRY:
        result = effect(rounds, registered)
        print(f"{registered.correction:<11} {'round ' + str(registered.issued_after):<13} "
              f"{registered.label:<26} {_fmt(result.before):>7} {_fmt(result.after):>8}")
    return 0
