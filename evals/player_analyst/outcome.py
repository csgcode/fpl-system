"""Season-level outcome of the minutes model — tracked, never graded.

Reads every data/retro/gw{M}-calibration.json ledger (`players[]`: p_start,
started, predicted, actual, position) and prints, per round and pooled:
Brier of p_start against starts, overall and by position; reliability per
p_start band; Σp − starts; skill against a persistence baseline (0.88 if the
player started the previous round, else 0.08, over ids in both ledgers); and
the minutes term's share of squared EP error.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

BANDS = ((0.0, 0.3), (0.3, 0.6), (0.6, 0.9), (0.9, 1.0001))
PERSIST_STARTED = 0.88
PERSIST_BENCHED = 0.08
POSITIONS = ("GKP", "DEF", "MID", "FWD")


@dataclass(frozen=True)
class Band:
    low: float
    high: float
    n: int
    mean_p: float | None
    observed: float | None


@dataclass(frozen=True)
class RoundOutcome:
    label: str
    n: int
    brier: float
    by_position: dict[str, float]
    bands: tuple[Band, ...]
    excess_starts: float
    skill: float | None
    minutes_share: float | None


def brier(rows: Sequence[dict]) -> float:
    return sum((r["p_start"] - r["started"]) ** 2 for r in rows) / len(rows)


def bands(rows: Sequence[dict]) -> tuple[Band, ...]:
    out = []
    for low, high in BANDS:
        inside = [r for r in rows if low <= r["p_start"] < high]
        n = len(inside)
        out.append(Band(low, min(high, 1.0), n,
                        sum(r["p_start"] for r in inside) / n if n else None,
                        sum(r["started"] for r in inside) / n if n else None))
    return tuple(out)


def persistence_pairs(rows: Sequence[dict], previous: Sequence[dict] | None
                      ) -> list[tuple[dict, float]]:
    """Each row whose id the previous ledger also holds, with its baseline p."""
    if previous is None:
        return []
    started = {r["id"]: r["started"] for r in previous}
    return [(r, PERSIST_STARTED if started[r["id"]] else PERSIST_BENCHED)
            for r in rows if r["id"] in started]


def skill(pairs: Sequence[tuple[dict, float]]) -> float | None:
    if not pairs:
        return None
    model = sum((r["p_start"] - r["started"]) ** 2 for r, _ in pairs)
    base = sum((p - r["started"]) ** 2 for r, p in pairs)
    return 1 - model / base if base else None


def minutes_share(rows: Sequence[dict]) -> float | None:
    """Σ((started − p)·predicted/p)² over Σ(actual − predicted)²: how much of
    the squared error the start probability alone explains. Rows with p = 0
    predict 0 and contribute no minutes term."""
    total = sum((r["actual"] - r["predicted"]) ** 2 for r in rows)
    if not total:
        return None
    term = sum(((r["started"] - r["p_start"]) * r["predicted"] / r["p_start"]) ** 2
               for r in rows if r["p_start"] > 0)
    return term / total


def outcome(label: str, rows: Sequence[dict], pairs: Sequence[tuple[dict, float]]
            ) -> RoundOutcome:
    return RoundOutcome(
        label=label, n=len(rows), brier=brier(rows),
        by_position={pos: brier(sub) for pos in POSITIONS
                     if (sub := [r for r in rows if r["position"] == pos])},
        bands=bands(rows),
        excess_starts=sum(r["p_start"] for r in rows) - sum(r["started"] for r in rows),
        skill=skill(pairs), minutes_share=minutes_share(rows),
    )


def load_ledgers(root: Path) -> dict[int, list[dict]]:
    found = {}
    for path in (root / "data" / "retro").glob("gw*-calibration.json"):
        match = re.fullmatch(r"gw(\d+)-calibration\.json", path.name)
        if match:
            found[int(match[1])] = json.loads(path.read_text("utf-8"))["players"]
    return dict(sorted(found.items()))


def score(ledgers: dict[int, list[dict]]) -> list[RoundOutcome]:
    rounds, all_rows, all_pairs = [], [], []
    for number, rows in ledgers.items():
        pairs = persistence_pairs(rows, ledgers.get(number - 1))
        rounds.append(outcome(f"r{number}", rows, pairs))
        all_rows += rows
        all_pairs += pairs
    if all_rows:
        rounds.append(outcome("pooled", all_rows, all_pairs))
    return rounds


def _num(value: float | None, fmt: str) -> str:
    return "–" if value is None else format(value, fmt)


def print_outcome(root: Path) -> int:
    results = score(load_ledgers(root))
    if not results:
        print("no calibration ledgers under data/retro")
        return 0
    for r in results:
        positions = " ".join(f"{p} {b:.4f}" for p, b in r.by_position.items())
        print(f"{r.label}: n {r.n}  Brier {r.brier:.4f} ({positions})  Σp−starts "
              f"{r.excess_starts:+.1f}  skill vs persistence {_num(r.skill, '+.3f')}  "
              f"minutes share {_num(r.minutes_share, '.2f')}")
        for band in r.bands:
            print(f"    [{band.low:.1f}, {band.high:.1f}{']' if band.high >= 1 else ')'}  "
                  f"n {band.n:>4}  p̄ {_num(band.mean_p, '.3f')}  "
                  f"observed {_num(band.observed, '.3f')}")
    return 0
