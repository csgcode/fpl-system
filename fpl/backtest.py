"""Backtest harness: re-scores past rounds from exactly what production read
before each deadline.

A round loads only when nothing in it could carry the outcome: every model
input was fetched before the deadline, no element summary holds the round
itself, the actuals are final, and the inputs on disk still match the
round's decision commit. A loaded round is then scored under a model
variant, one line per (player, round), exactly as the calibration ledger
scores what `fpl ep` would have written. A gated run can be written once
as a gate record (fpl/gates.py), singly or in manifest order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from collections.abc import Callable, Hashable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from types import NoneType
from typing import Any, TypeVar, get_args, get_type_hints

from fpl import calibrate, ep, fixture_ratings, gates
from fpl.calibrate import Aggregate, PlayerLine, PlayerPrediction
from fpl.decision_record import decision_commit, drifted, record_predictions, repo_root
from fpl.ep import (
    DEFAULT_CONFIG,
    FixturesDocument,
    InputsDocument,
    ModelConfig,
    build_predictions,
    load_fixtures,
    load_inputs,
)
from fpl.models import Bootstrap, ElementSummary, EventLive, PLAYING_POSITIONS, Position
from fpl.service import load_cached_bootstrap, load_cached_summaries
from fpl.state import MAX_GW, MIN_GW
from fpl.gates import GateRecord, ManifestEntry, signed, value_text
from fpl.store import ARCHIVE_STAMP_FORMAT, SnapshotStore

POSITIONS = (Position.GKP, Position.DEF, Position.MID, Position.FWD)
INPUTS_POLICIES = ("keep",)

GATE_Z = 1.96
GATE_BIAS_SLACK = 0.05
GATE_POSITION_SLACK = 0.02
GATE_MIN_EFFECT = -0.01

ANALYSIS_ROOT = Path("data/analysis")
DECISIONS_ROOT = Path("data/decisions")
RETRO_ROOT = Path("data/retro")
MAX_SWEEP_KEYS = 2

GridValue = TypeVar("GridValue", bound=Hashable)


@dataclass(frozen=True)
class RoundData:
    gw: int
    commit: str | None
    deadline: datetime
    bootstrap: Bootstrap
    summaries: dict[int, ElementSummary]
    fixtures: FixturesDocument
    inputs: dict[Position, InputsDocument]
    live: EventLive
    promoted: frozenset[str]
    warnings: tuple[str, ...] = ()


def load_round(
    *,
    data_root: Path,
    analysis_root: Path,
    actuals_root: Path,
    gw: int,
    decisions_root: Path | None = None,
    drift_check: bool = True,
) -> RoundData:
    """Round `gw` as production saw it before its deadline, with its final
    actuals. Raises ValueError naming the file on any leak, missing or
    non-final actuals, or drift from the decision commit."""
    store = SnapshotStore(data_root)
    bootstrap = load_cached_bootstrap(store, gw)
    deadline = bootstrap.deadline_for(gw)
    if deadline is None:
        raise ValueError(f"gw{gw} bootstrap has no event {gw} deadline")
    round_dir = analysis_root / f"gw{gw}"
    inputs = {pos: load_inputs(round_dir / f"inputs-{pos.name}.json") for pos in POSITIONS}
    fixtures = load_fixtures(round_dir / fixture_ratings.JSON_FILENAME)
    wanted = [p.id for p in bootstrap.elements if p.element_type in PLAYING_POSITIONS]
    wanted += [entry.id for doc in inputs.values() for entry in doc.players]
    summaries = load_cached_summaries(store, gw, wanted)
    promoted = fixture_ratings.load_priors(analysis_root / fixture_ratings.PRIORS_FILENAME).promoted

    _check_summaries_predate(summaries, gw, store)
    names = ["bootstrap", *(["fixtures"] if store.exists(gw, "fixtures") else []),
             *(f"players/summary-{pid}" for pid in summaries)]
    _check_fetched_before(store, gw, names, deadline)
    live = _load_final_actuals(actuals_root, gw)

    warnings: list[str] = []
    commit = None
    if drift_check:
        commit = _check_drift(data_root, analysis_root,
                              decisions_root or analysis_root.parent / "decisions", gw, warnings)
    return RoundData(gw=gw, commit=commit, deadline=deadline, bootstrap=bootstrap,
                     summaries=summaries, fixtures=fixtures, inputs=inputs, live=live,
                     promoted=promoted, warnings=tuple(warnings))


class BacktestLine(PlayerLine):
    round: int
    club: str
    promoted: bool
    no_history: bool
    p4: float | None = None


@dataclass(frozen=True)
class RoundScore:
    lines: tuple[BacktestLine, ...]
    warnings: tuple[str, ...]


def score_round(data: RoundData, config: ModelConfig = DEFAULT_CONFIG, *,
                inputs_policy: str = "keep") -> RoundScore:
    """Every judged player of the round scored under `config`. An a/d player
    above the coverage floor with no inputs row is left unscored and named in
    the warnings rather than refused: the round's inputs are fixed history."""
    if inputs_policy not in INPUTS_POLICIES:
        raise ValueError(f"unknown inputs policy {inputs_policy!r}; "
                         f"expected one of {', '.join(INPUTS_POLICIES)}")
    warnings = list(data.warnings)
    predictions: list[PlayerPrediction] = []
    no_history: dict[int, bool] = {}
    for position in POSITIONS:
        inputs = data.inputs[position]
        if not inputs.players:
            continue
        result = build_predictions(
            data.bootstrap, data.summaries, data.fixtures, inputs, gw=data.gw,
            allow_missing=_uncovered(data.bootstrap, position, inputs), config=config,
        )
        warnings += result.warnings
        for doc in result.to_documents():
            predictions.append(PlayerPrediction.model_validate({**doc, "position": position}))
            no_history[doc["id"]] = doc["rates"]["prior_source"] == "league_mean"
    if not predictions:
        raise ValueError(f"gw{data.gw} has no inputs rows to score")
    report = calibrate.build_report(tuple(predictions), data.live, match_round=data.gw)
    if report.unmatched_prediction_ids:
        warnings.append(f"gw{data.gw}: no actuals row for id(s) "
                        + ", ".join(map(str, report.unmatched_prediction_ids))
                        + " — not scored")
    lines = tuple(
        BacktestLine(**line.model_dump(), round=data.gw, club=line.team,
                     promoted=line.team in data.promoted, no_history=no_history[line.id])
        for line in report.players
    )
    return RoundScore(lines=lines, warnings=tuple(warnings))


@dataclass(frozen=True)
class GroupComparison:
    n: int
    baseline: Aggregate
    variant: Aggregate
    delta_mae: float


@dataclass(frozen=True)
class Comparison:
    """A variant against the baseline on the same (round, id) lines.
    `delta_mae`, `se`, `ci` and `round_deltas` come from the unrounded
    per-line differences; the aggregates are rounded and for display only.
    A slice with no lines is None."""

    n: int
    baseline: Aggregate
    variant: Aggregate
    delta_mae: float
    se: float
    ci: tuple[float, float]
    round_deltas: dict[int, float]
    round_wins: tuple[int, int]
    by_position: dict[str, GroupComparison]
    slices: dict[str, GroupComparison | None]
    beats: bool
    reasons: tuple[str, ...]


SLICES: dict[str, Callable[[BacktestLine], bool]] = {
    "promoted": lambda line: line.promoted,
    "no_history": lambda line: line.no_history,
}


def compare(baseline: Sequence[BacktestLine], variant: Sequence[BacktestLine]) -> Comparison:
    """Pairs the two sides on (round, id), d = |e_variant| − |e_baseline|
    per line, and applies the gate: the CI of mean d, clustered by
    (round, club), lies below zero; the variant's bias is no worse than the
    baseline's plus a slack; no position worsens by more than a slack; the
    mean improvement reaches the minimum effect; and the variant wins all
    rounds but at most one. Raises ValueError on unpaired or duplicate lines."""
    base_by_key = _keyed(baseline, "baseline")
    variant_by_key = _keyed(variant, "variant")
    if base_by_key.keys() != variant_by_key.keys():
        only_base = sorted(base_by_key.keys() - variant_by_key.keys())
        only_variant = sorted(variant_by_key.keys() - base_by_key.keys())
        raise ValueError("unpaired lines (round, id): baseline only "
                         f"{only_base or 'none'}, variant only {only_variant or 'none'}")
    if not base_by_key:
        raise ValueError("no lines to compare")
    keys = sorted(base_by_key)
    pairs = [(base_by_key[k], variant_by_key[k]) for k in keys]
    d = [abs(v.error) - abs(b.error) for b, v in pairs]
    n = len(d)
    delta = sum(d) / n

    clusters: dict[tuple[int, str], float] = {}
    for (b, _), di in zip(pairs, d):
        key = (b.round, b.club)
        clusters[key] = clusters.get(key, 0.0) + (di - delta)
    se = math.sqrt(sum(total ** 2 for total in clusters.values())) / n
    ci = (delta - GATE_Z * se, delta + GATE_Z * se)

    by_round: dict[int, list[float]] = {}
    for (b, _), di in zip(pairs, d):
        by_round.setdefault(b.round, []).append(di)
    round_deltas = {r: sum(values) / len(values) for r, values in sorted(by_round.items())}
    wins = sum(1 for value in round_deltas.values() if value < 0)
    rounds = len(round_deltas)

    by_position = {
        position: _group(pairs, d, lambda line, position=position: line.position == position)
        for position in _positions(b.position for b, _ in pairs)
    }
    slices = {name: _group(pairs, d, member) for name, member in SLICES.items()}

    bias_base = _mean_error(b for b, _ in pairs)
    bias_variant = _mean_error(v for _, v in pairs)
    reasons: list[str] = []
    if ci[1] >= 0:
        reasons.append(f"ci: upper {signed(ci[1], 3)} ≥ 0")
    if abs(bias_variant) > abs(bias_base) + GATE_BIAS_SLACK:
        reasons.append(f"bias: |b_v| {abs(bias_variant):.3f} > |b_b| {abs(bias_base):.3f} "
                       f"+ {GATE_BIAS_SLACK}")
    for position, group in by_position.items():
        if group.delta_mae > GATE_POSITION_SLACK:
            reasons.append(f"position {position}: ΔMAE {signed(group.delta_mae, 3)} "
                           f"> {signed(GATE_POSITION_SLACK, 2)}")
    if delta > GATE_MIN_EFFECT:
        reasons.append(f"effect: ΔMAE {signed(delta, 4)} > {signed(GATE_MIN_EFFECT, 2)}")
    if wins < rounds - 1:
        reasons.append(f"rounds: won {wins} of {rounds}, need {rounds - 1}")

    return Comparison(
        n=n,
        baseline=calibrate.aggregate([b for b, _ in pairs]),
        variant=calibrate.aggregate([v for _, v in pairs]),
        delta_mae=delta,
        se=se,
        ci=ci,
        round_deltas=round_deltas,
        round_wins=(wins, rounds),
        by_position=by_position,
        slices=slices,
        beats=not reasons,
        reasons=tuple(reasons),
    )


def cross_validate(
    lines_by_value: Mapping[GridValue, Sequence[BacktestLine]],
) -> tuple[list[BacktestLine], dict[int, GridValue]]:
    """Leave-one-round-out selection over a grid, in grid order (the
    mapping's order). For each held-out round, the value with the lowest
    pooled MAE over the other rounds is picked, ties to the earlier grid
    entry, and its lines for the held-out round become that round's CV
    lines. Returns the CV lines and the pick per round.

    A fold trains on later rounds for an earlier held-out round. That is
    acceptable for a hyper-parameter: LORO measures the selection
    procedure, not the exact constant shipped."""
    if not lines_by_value:
        raise ValueError("no grid values to cross-validate")
    by_value = {value: _by_round(lines) for value, lines in lines_by_value.items()}
    rounds = sorted(next(iter(by_value.values())))
    for value, per_round in by_value.items():
        if sorted(per_round) != rounds:
            raise ValueError(f"grid value {value!r} covers rounds {sorted(per_round)}, "
                             f"expected {rounds}")
    if len(rounds) < 2:
        raise ValueError(f"leave-one-round-out needs at least two rounds, got {rounds}")

    cv_lines: list[BacktestLine] = []
    picks: dict[int, GridValue] = {}
    for held_out in rounds:
        best, best_mae = None, math.inf
        for value, per_round in by_value.items():
            training = [line for r in rounds if r != held_out for line in per_round[r]]
            mae = sum(abs(line.error) for line in training) / len(training)
            if mae < best_mae:
                best, best_mae = value, mae
        picks[held_out] = best
        cv_lines += by_value[best][held_out]
    return cv_lines, picks


def ship_value(picks: Mapping[int, GridValue], grid: Sequence[GridValue]) -> GridValue:
    """The value to ship after a sweep: the most frequent LORO pick, ties
    to the earlier grid entry."""
    if not picks:
        raise ValueError("no picks to choose a ship value from")
    outside = [value for value in picks.values() if value not in grid]
    if outside:
        raise ValueError(f"pick(s) {outside!r} not in the grid {list(grid)!r}")
    counts = {value: 0 for value in grid}
    for value in picks.values():
        counts[value] += 1
    return max(grid, key=counts.__getitem__)


def _by_round(lines: Sequence[BacktestLine]) -> dict[int, list[BacktestLine]]:
    per_round: dict[int, list[BacktestLine]] = {}
    for line in lines:
        per_round.setdefault(line.round, []).append(line)
    return per_round


def _keyed(lines: Sequence[BacktestLine], side: str) -> dict[tuple[int, int], BacktestLine]:
    keyed: dict[tuple[int, int], BacktestLine] = {}
    for line in lines:
        key = (line.round, line.id)
        if key in keyed:
            raise ValueError(f"duplicate {side} line (round, id) {key}")
        keyed[key] = line
    return keyed


def _positions(seen) -> list[str]:
    present = set(seen)
    ordered = [p.name for p in POSITIONS if p.name in present]
    return ordered + sorted(present - set(ordered))


def _group(pairs: list[tuple[BacktestLine, BacktestLine]], d: list[float],
           member: Callable[[BacktestLine], bool]) -> GroupComparison | None:
    chosen = [(pair, di) for pair, di in zip(pairs, d) if member(pair[0])]
    if not chosen:
        return None
    return GroupComparison(
        n=len(chosen),
        baseline=calibrate.aggregate([b for (b, _), _ in chosen]),
        variant=calibrate.aggregate([v for (_, v), _ in chosen]),
        delta_mae=sum(di for _, di in chosen) / len(chosen),
    )


def _mean_error(lines) -> float:
    errors = [line.error for line in lines]
    return sum(errors) / len(errors)


def _uncovered(bootstrap: Bootstrap, position: Position,
               inputs: InputsDocument) -> frozenset[int]:
    judged = {entry.id for entry in inputs.players}
    return frozenset(
        p.id for p in bootstrap.elements
        if p.element_type == position and p.id not in judged
        and p.now_cost > ep.COVERAGE_PRICE_FLOOR_TENTHS and p.status in ep.COVERAGE_STATUSES
    )


def _check_summaries_predate(summaries: dict[int, ElementSummary], gw: int,
                             store: SnapshotStore) -> None:
    for pid, summary in summaries.items():
        rounds = [row.round for row in summary.history if row.round is not None]
        if rounds and max(rounds) >= gw:
            path = store.path(gw, f"players/summary-{pid}")
            raise ValueError(f"leak: {path} holds round {max(rounds)}, "
                             f"not only rounds before gw{gw}")


def _check_fetched_before(store: SnapshotStore, gw: int, names: list[str],
                          deadline: datetime) -> None:
    for name in names:
        fetched = store.fetched_at(gw, name)
        if fetched is None:
            raise ValueError(f"leak check: {store.path(gw, name)} has no recorded fetch time, "
                             f"so it cannot be shown to predate the gw{gw} deadline "
                             f"{deadline.isoformat()}")
        if fetched >= deadline:
            raise ValueError(f"leak: {store.path(gw, name)} was fetched {fetched.isoformat()}, "
                             f"after the gw{gw} deadline {deadline.isoformat()}")


def _load_final_actuals(actuals_root: Path, gw: int) -> EventLive:
    store = SnapshotStore(actuals_root)
    name = f"event-live-e{gw}"
    path = store.path(gw + 1, name)
    if not path.is_file():
        raise ValueError(f"no actuals for round {gw}: {path} is missing")
    if not _is_final(actuals_root, store, gw):
        raise ValueError(
            f"{path} is not final: its sidecar has no `final` key and no bootstrap of "
            f"gw{gw + 1} or later, fetched at or before it, shows event {gw} data_checked "
            f"— refetch with fpl event-live --gw {gw + 1} --round {gw} --force"
        )
    return EventLive.model_validate(store.load(gw + 1, name))


def _is_final(actuals_root: Path, store: SnapshotStore, gw: int) -> bool:
    name = f"event-live-e{gw}"
    meta = store.dir(gw + 1) / ".meta" / f"{name}.json"
    try:
        if json.loads(meta.read_text(encoding="utf-8")).get("final") is True:
            return True
    except (OSError, ValueError, AttributeError):
        pass
    fetched = store.fetched_at(gw + 1, name)
    if fetched is None:
        return False
    return any(
        seen <= fetched and _shows_checked(path, gw)
        for path, seen in _bootstraps_from(actuals_root, store, gw + 1)
    )


def _bootstraps_from(root: Path, store: SnapshotStore, first_gw: int):
    """Every cached bootstrap of gw ≥ first_gw with its fetch time, archived
    ones included: an archive entry's stamp is the fetch time it was saved with."""
    for directory in sorted(root.glob("gw*")):
        try:
            n = int(directory.name[2:])
        except ValueError:
            continue
        if n < first_gw:
            continue
        current = store.fetched_at(n, "bootstrap")
        if current is not None and store.exists(n, "bootstrap"):
            yield store.path(n, "bootstrap"), current
        for archived in sorted((directory / ".archive").glob("bootstrap-*.json")):
            try:
                stamp = datetime.strptime(archived.stem.removeprefix("bootstrap-"),
                                          ARCHIVE_STAMP_FORMAT).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            yield archived, stamp


def _shows_checked(path: Path, gw: int) -> bool:
    try:
        events = json.loads(path.read_text(encoding="utf-8")).get("events", [])
    except (OSError, ValueError, AttributeError):
        return False
    return any(isinstance(e, dict) and e.get("id") == gw and e.get("data_checked") is True
               for e in events)


def _check_drift(data_root: Path, analysis_root: Path, decisions_root: Path, gw: int,
                 warnings: list[str]) -> str | None:
    try:
        repo = repo_root(analysis_root.resolve())
    except ValueError:
        warnings.append(f"{analysis_root} is not inside a git repository — "
                        f"gw{gw} inputs not checked for drift from the decision commit")
        return None
    decisions = _relative(decisions_root, repo)
    if decisions is None:
        raise ValueError(f"{decisions_root} is outside the repository {repo}, so gw{gw} inputs "
                         f"cannot be checked against its decision commit — pass "
                         f"--no-drift-check to score the files on disk")
    sha = decision_commit(repo, gw, decisions)
    if sha is None:
        warnings.append(f"gw{gw} has no decision commit — inputs not checked for drift")
        return None
    raw = _relative(data_root / f"gw{gw}", repo)
    analysis = _relative(analysis_root / f"gw{gw}", repo)
    paths = [f"{analysis}/inputs-*.json", f"{analysis}/{fixture_ratings.JSON_FILENAME}"]
    if raw is not None:
        paths += [f"{raw}/bootstrap.json", f"{raw}/fixtures.json", f"{raw}/players"]
    changed = drifted(repo, sha, paths)
    if changed:
        raise ValueError(f"gw{gw} inputs differ from decision commit {sha[:12]}: "
                         + ", ".join(changed)
                         + " — restore them, or pass --no-drift-check to score the files on disk")
    return sha


def _relative(path: Path, repo: Path) -> str | None:
    try:
        return str(path.resolve().relative_to(repo))
    except ValueError:
        return None


@dataclass(frozen=True)
class RoundCheck:
    """A round's backtest n against its calibration ledger's, and how far
    today's code moves the baseline from the decision record."""

    n: int
    ledger_n: int | None
    code_drift: float | None

    @property
    def delta_n(self) -> int | None:
        return None if self.ledger_n is None else self.n - self.ledger_n


def code_drift(lines: Sequence[BacktestLine], analysis_root: Path, decisions_root: Path,
               gw: int) -> float | None:
    """Mean |predicted − the decision record's ep_gw[0]| over the ids both
    hold, or None when the round has no readable decision record."""
    try:
        record = record_predictions(analysis_root, decisions_root, gw)
    except (ValueError, OSError, subprocess.CalledProcessError):
        return None
    recorded = {p.id: p.predicted for p in record.predictions}
    gaps = [abs(line.predicted - recorded[line.id]) for line in lines if line.id in recorded]
    return sum(gaps) / len(gaps) if gaps else None


def round_checks(lines: Sequence[BacktestLine], rounds: Sequence[int], *, retro_root: Path,
                 analysis_root: Path, decisions_root: Path,
                 warnings: list[str]) -> dict[int, RoundCheck]:
    per_round = _by_round(lines)
    checks: dict[int, RoundCheck] = {}
    for r in rounds:
        round_lines = per_round.get(r, [])
        checks[r] = RoundCheck(
            n=len(round_lines),
            ledger_n=_ledger_n(retro_root / f"gw{r}-calibration.json", warnings),
            code_drift=code_drift(round_lines, analysis_root, decisions_root, r),
        )
    return checks


def _ledger_n(path: Path, warnings: list[str]) -> int | None:
    if not path.is_file():
        return None
    try:
        return calibrate.load_report(path).overall.n
    except ValueError as exc:
        warnings.append(f"ledger {path} unreadable, ledger_n not compared: {exc}")
        return None


def check_ledger_gap(checks: Mapping[int, RoundCheck], limit: int | None) -> None:
    if limit is None:
        return
    over = [(r, c.delta_n) for r, c in checks.items()
            if c.delta_n is not None and abs(c.delta_n) > limit]
    if over:
        raise ValueError("ledger n gap: " + ", ".join(f"round {r} Δn {_signed_int(dn)}"
                                                     for r, dn in over)
                         + f" exceeds --max-ledger-n-gap {limit} — the backtest does not "
                           "score the players the calibration ledger scored")


@dataclass(frozen=True)
class Combined:
    overrides: dict[str, Any]
    config: ModelConfig
    reverted: tuple[str, ...]
    comparison: Comparison | None


def combine(base: ModelConfig, passes: Sequence[tuple[str, Mapping[str, Any]]],
            judge: Callable[[ModelConfig], Comparison]) -> Combined:
    """Every passing entry's ship value overlaid on `base` and judged
    together. While the combination fails, the last remaining entry is
    dropped and named in `reverted`; with nothing left, `base` ships."""
    kept = list(passes)
    reverted: list[str] = []
    while kept:
        overrides: dict[str, Any] = {}
        for _, ship in kept:
            overrides.update(ship)
        config = _overlay(base, overrides)
        comparison = judge(config)
        if comparison.beats:
            return Combined(overrides, config, tuple(reverted), comparison)
        reverted.append(kept.pop()[0])
    return Combined({}, base, tuple(reverted), None)


def _overlay(config: ModelConfig, overrides: Mapping[str, Any]) -> ModelConfig:
    try:
        return replace(config, **overrides)
    except TypeError:
        valid = ", ".join(f.name for f in fields(config))
        raise ValueError(f"overrides {dict(overrides)!r} are not all ModelConfig fields "
                         f"({valid})") from None


ConfigValue = float | bool | None


def register(add: Callable[..., argparse.ArgumentParser]) -> None:
    p = add("backtest", "re-score past rounds under a model variant against actuals",
            cached=False)
    p.add_argument("--rounds", required=True, metavar="A-B",
                   help="past rounds to score, each before --gw")
    p.add_argument("--analysis-root", type=Path, default=ANALYSIS_ROOT,
                   help="root holding gw{M}/inputs-*.json, gw{M}/fixtures.json and "
                        "club-priors.json")
    p.add_argument("--decisions-root", type=Path, default=DECISIONS_ROOT,
                   help="root holding gw{M}/final.md, whose adding commit is the drift reference")
    p.add_argument("--retro-root", type=Path, default=RETRO_ROOT,
                   help="where gw{M}-calibration.json ledgers live")
    p.add_argument("--no-drift-check", action="store_true",
                   help="score the files on disk even when they differ from the decision commit")
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                   help="variant: a ModelConfig field to change (repeatable)")
    p.add_argument("--sweep", action="append", default=[], metavar="KEY=V1,V2,...",
                   help=f"grid over a ModelConfig field, production value first "
                        f"(repeatable, up to {MAX_SWEEP_KEYS} keys, cartesian)")
    p.add_argument("--cv", action="store_true",
                   help="pick the sweep value leave-one-round-out and gate the held-out lines")
    p.add_argument("--detail", action="store_true",
                   help="add the baseline tables to a sweep and per-position and slice deltas")
    p.add_argument("--format", choices=("table", "json"), default="table")
    p.add_argument("--out", type=Path, help="also write the JSON document here")
    p.add_argument("--max-ledger-n-gap", type=int, metavar="N",
                   help="exit 1 when a round's n differs from its calibration ledger's by more "
                        "than N")
    p.add_argument("--record", metavar="NAME",
                   help="write this run's gate record to <gates-root>/NAME.json (once)")
    p.add_argument("--manifest", type=Path, help="gate manifest run by --record-all")
    p.add_argument("--record-all", action="store_true",
                   help="record every manifest entry that has no record, in order, then "
                        "rewrite combined.json")
    p.add_argument("--force", action="store_true",
                   help="archive existing records and record them again")
    p.add_argument("--gates-root", type=Path, default=gates.GATES_ROOT,
                   help="where gate records live")


def run(data_root: Path, args: argparse.Namespace) -> int:
    rounds = parse_rounds(args.rounds, args.gw)
    _check_record_args(args)
    if args.record_all:
        entries = gates.load_manifest(args.manifest)
        baseline = _recorded_baseline(args.gates_root)
        for entry in entries:
            _entry_variant(entry, baseline)
    else:
        baseline = DEFAULT_CONFIG
        fixed = _parse_sets(args.set, baseline)
        sweep = parse_sweep(args.sweep, baseline)
        _check_variant(fixed, sweep, args.cv, recording=args.record is not None)
        if args.record is not None and not args.force:
            _refuse_existing(args.gates_root, args.record)

    drift_check = not args.no_drift_check
    data = [load_round(data_root=data_root, analysis_root=args.analysis_root,
                       actuals_root=data_root, gw=r, decisions_root=args.decisions_root,
                       drift_check=drift_check) for r in rounds]
    scorer = _Scorer(data)
    checks = round_checks(scorer.lines(baseline), rounds, retro_root=args.retro_root,
                          analysis_root=args.analysis_root,
                          decisions_root=args.decisions_root, warnings=scorer.warnings)
    context = _RecordContext(args, data_root, data, checks)

    if args.record_all:
        for line in [_header(rounds, drift_check),
                     *_baseline_table(scorer.lines(baseline), checks)]:
            print(line)
        _print_warnings(scorer.warnings)
        check_ledger_gap(checks, args.max_ledger_n_gap)
        return _record_all(scorer, entries, baseline, context)

    report = _evaluate(scorer, baseline, fixed, sweep, cv=args.cv)
    document = _document(args.gw, rounds, drift_check, data, report, checks)
    if args.format == "json":
        print(json.dumps(document, indent=1, ensure_ascii=False))
    else:
        for line in _table(rounds, drift_check, report, checks, detail=args.detail):
            print(line)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n",
                            encoding="utf-8")
        if args.format == "table":
            print(f"wrote {args.out}")
    _print_warnings(report.warnings)
    check_ledger_gap(checks, args.max_ledger_n_gap)
    if args.record is not None:
        argv = ([a for text in args.set for a in ("--set", text)]
                + [a for text in args.sweep for a in ("--sweep", text)]
                + (["--cv"] if args.cv else []))
        record = _record(context, args.record, "model", argv, report)
        path = gates.write_record(args.gates_root, record, force=args.force)
        if args.format == "table":
            print(f"wrote {path}")
    return 0


def _print_warnings(warnings: Sequence[str]) -> None:
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)


def _check_record_args(args: argparse.Namespace) -> None:
    if args.record is not None and args.record_all:
        raise ValueError("--record and --record-all are exclusive")
    if args.record_all != (args.manifest is not None):
        raise ValueError("--record-all runs a --manifest; give both")
    if args.force and args.record is None and not args.record_all:
        raise ValueError("--force re-records; give --record or --record-all")
    if args.record is not None:
        gates.check_name(args.record)
    if args.record_all:
        given = [flag for flag, value in (("--set", args.set), ("--sweep", args.sweep),
                                          ("--cv", args.cv), ("--out", args.out))
                 if value]
        if args.format == "json":
            given.append("--format json")
        if given:
            raise ValueError(f"--record-all takes each variant from the manifest; drop "
                             f"{', '.join(given)}")


def _check_variant(fixed: Mapping[str, ConfigValue], sweep: Mapping[str, list[ConfigValue]],
                   cv: bool, *, recording: bool) -> None:
    both = sorted(fixed.keys() & sweep.keys())
    if both:
        raise ValueError(f"{', '.join(both)} given to both --set and --sweep")
    if cv and not sweep:
        raise ValueError("--cv selects a --sweep value; give --sweep")
    if recording and sweep and not cv:
        raise ValueError("a recorded sweep is gated on its leave-one-round-out lines; "
                         "pass --cv")


def _refuse_existing(root: Path, name: str) -> None:
    path = gates.record_path(root, name)
    if path.exists():
        raise ValueError(f"{path} exists — gate records are written once; "
                         "pass --force to archive it and record again")


def _recorded_baseline(root: Path) -> ModelConfig:
    """The `baseline` record's config, so a forced re-run reproduces the
    records; production's config only before the first baseline record."""
    record = gates.read_record(root, gates.BASELINE)
    if record is None:
        return DEFAULT_CONFIG
    return _overlay(ModelConfig(), record.baseline_config)


def _entry_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="manifest entry", add_help=False, allow_abbrev=False,
                                exit_on_error=False)
    p.add_argument("--set", action="append", default=[])
    p.add_argument("--sweep", action="append", default=[])
    p.add_argument("--cv", action="store_true")
    return p


def _entry_variant(entry: ManifestEntry, config: ModelConfig
                   ) -> tuple[dict[str, ConfigValue], dict[str, list[ConfigValue]], bool]:
    try:
        parsed, unknown = _entry_parser().parse_known_args(list(entry.argv))
        if unknown:
            raise ValueError(f"unknown argument(s) {' '.join(unknown)}")
        fixed = _parse_sets(parsed.set, config)
        sweep = parse_sweep(parsed.sweep, config)
        _check_variant(fixed, sweep, parsed.cv, recording=True)
    except (argparse.ArgumentError, ValueError) as exc:
        raise ValueError(f"manifest entry {entry.name}: {exc}") from None
    return fixed, sweep, parsed.cv


@dataclass(frozen=True)
class _RecordContext:
    args: argparse.Namespace
    data_root: Path
    data: Sequence[RoundData]
    checks: Mapping[int, RoundCheck]


def _record_all(scorer: _Scorer, entries: Sequence[ManifestEntry], base: ModelConfig,
                context: _RecordContext) -> int:
    """Each entry without a record, in manifest order, against `base`
    overlaid with the ship values of earlier passing model entries that the
    last combined record did not revert; then combined.json afresh."""
    root, force = context.args.gates_root, context.args.force
    previous = gates.read_record(root, gates.COMBINED)
    reverted = set(previous.reverted or ()) if previous is not None else set()
    records: dict[str, GateRecord] = {}
    for index, entry in enumerate(entries):
        existing = gates.read_record(root, entry.name)
        if existing is not None and not force:
            records[entry.name] = existing
            print(f"{entry.name}: record exists — skipped")
            continue
        overlay: dict[str, Any] = {}
        for earlier in entries[:index]:
            record = records[earlier.name]
            if (earlier.kind == "model" and record.verdict == "PASS"
                    and earlier.name not in reverted):
                overlay.update(record.ship_value or {})
        entry_base = _overlay(base, overlay)
        fixed, sweep, cv = _entry_variant(entry, entry_base)
        report = _evaluate(scorer, entry_base, fixed, sweep, cv=cv)
        document = _record(context, entry.name, entry.kind, entry.argv, report)
        gates.write_record(root, document, force=force)
        records[entry.name] = GateRecord.model_validate(document)
        for line in gates.summary_lines([records[entry.name]]):
            print(line)

    passes = [(entry.name, records[entry.name].ship_value or {}) for entry in entries
              if entry.kind == "model" and records[entry.name].verdict == "PASS"]
    base_lines = scorer.lines(base)
    result = combine(base, passes, lambda config: compare(base_lines, scorer.lines(config)))
    document = _combined_record(context, Scored("baseline", {}, base, base_lines), result)
    gates.write_record(root, document, force=True)
    for line in gates.summary_lines([GateRecord.model_validate(document)]):
        print(line)
    _print_warnings(scorer.warnings)
    return 0


def _record(context: _RecordContext, name: str, kind: str, argv: Sequence[str],
            report: Report) -> dict[str, Any]:
    c = report.comparison
    if report.ship is not None:
        ship = report.ship.overrides
    elif not report.sweep_keys and report.variants:
        ship = report.variants[0].overrides
    else:
        ship = None
    return {
        **_record_base(context, name, kind, argv, report.baseline),
        "grid": {key: list(values) for key, values in report.grid.items()} or None,
        "picks": None if report.picks is None
        else {str(r): s.overrides for r, s in sorted(report.picks.items())},
        "ship_value": ship,
        "comparison": None if c is None else comparison_document(c),
        "verdict": None if c is None else ("PASS" if c.beats else "FAIL"),
        "reasons": [] if c is None else list(c.reasons),
    }


def _combined_record(context: _RecordContext, baseline: Scored,
                     result: Combined) -> dict[str, Any]:
    c = result.comparison
    return {
        **_record_base(context, gates.COMBINED, "combined", (), baseline),
        "grid": None,
        "picks": None,
        "ship_value": result.overrides,
        "comparison": None if c is None else comparison_document(c),
        "verdict": None if c is None else "PASS",
        "reasons": [],
        "shipped_config": asdict(result.config),
        "reverted": list(result.reverted),
    }


def _record_base(context: _RecordContext, name: str, kind: str, argv: Sequence[str],
                 baseline: Scored) -> dict[str, Any]:
    args = context.args
    store = SnapshotStore(context.data_root)
    actuals = {}
    for d in context.data:
        path = store.path(d.gw + 1, f"event-live-e{d.gw}")
        actuals[str(d.gw)] = {"path": str(path),
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return {
        "schema_version": gates.SCHEMA_VERSION,
        "name": name,
        "kind": kind,
        "argv": list(argv),
        "rounds": [d.gw for d in context.data],
        "data": {
            "data_root": str(context.data_root),
            "analysis_root": str(args.analysis_root),
            "decisions_root": str(args.decisions_root),
            "retro_root": str(args.retro_root),
            "drift_check": not args.no_drift_check,
            "actuals": actuals,
        },
        "decision_commits": {str(d.gw): d.commit for d in context.data},
        "code": _code_state(),
        "baseline_config": asdict(baseline.config),
        "baseline": _scored_document(baseline),
        "round_checks": _checks_document(context.checks),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def _code_state() -> dict[str, Any]:
    package = Path(__file__).resolve().parent
    try:
        head = _git(package, "rev-parse", "HEAD").strip()
        dirty = bool(_git(package, "status", "--porcelain", "--", ".").strip())
    except (OSError, subprocess.CalledProcessError):
        return {"head": None, "dirty": None}
    return {"head": head, "dirty": dirty}


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True,
                          text=True).stdout


def parse_rounds(text: str, gw: int) -> list[int]:
    match = re.fullmatch(r"(\d+)(?:-(\d+))?", text.strip())
    if match is None:
        raise ValueError(f"--rounds {text!r}: expected A-B, e.g. 3-6")
    first = int(match.group(1))
    last = int(match.group(2) or first)
    if not MIN_GW <= first <= last <= MAX_GW:
        raise ValueError(f"--rounds {text!r}: need {MIN_GW} ≤ A ≤ B ≤ {MAX_GW}")
    if last >= gw:
        raise ValueError(f"round {last} is not before --gw {gw}")
    return list(range(first, last + 1))


def parse_assignment(text: str, config: ModelConfig) -> tuple[str, ConfigValue]:
    """`key=value` for a field of `config`'s class, the value parsed by the
    field's type: `none` for an optional field, `true`/`false` for a bool,
    else a float."""
    key, sep, raw = text.partition("=")
    if not sep:
        raise ValueError(f"{text!r}: expected KEY=VALUE")
    return key, _parse_value(key, raw, _field_types(config))


def parse_sweep(texts: Sequence[str], config: ModelConfig) -> dict[str, list[ConfigValue]]:
    """Each `key=v1,v2,...` as the key's grid, `config`'s value first (added
    when absent), duplicates dropped, keys in the order given."""
    types = _field_types(config)
    grid: dict[str, list[ConfigValue]] = {}
    for text in texts:
        key, sep, raw = text.partition("=")
        if not sep or not raw:
            raise ValueError(f"--sweep {text!r}: expected KEY=V1,V2,...")
        if key in grid:
            raise ValueError(f"--sweep {key} given twice")
        values = [getattr(config, key) if key in types else None]
        for item in raw.split(","):
            value = _parse_value(key, item, types)
            if value not in values:
                values.append(value)
        grid[key] = values
    if len(grid) > MAX_SWEEP_KEYS:
        raise ValueError(f"--sweep takes up to {MAX_SWEEP_KEYS} keys, got {', '.join(grid)}")
    return grid


@dataclass(frozen=True)
class Scored:
    label: str
    overrides: dict[str, ConfigValue]
    config: ModelConfig
    lines: tuple[BacktestLine, ...]


@dataclass(frozen=True)
class Report:
    baseline: Scored
    variants: tuple[Scored, ...]
    sweep_keys: tuple[str, ...]
    grid: dict[str, list[ConfigValue]]
    picks: dict[int, Scored] | None
    ship: Scored | None
    comparison: Comparison | None
    warnings: tuple[str, ...]


class _Scorer:
    """Scores every loaded round under a config once; later requests for
    the same config reuse the lines."""

    def __init__(self, data: Sequence[RoundData]) -> None:
        self._data = data
        self._cache: dict[ModelConfig, tuple[BacktestLine, ...]] = {}
        self.warnings: list[str] = [w for d in data for w in d.warnings]

    def lines(self, config: ModelConfig) -> tuple[BacktestLine, ...]:
        if config not in self._cache:
            lines: list[BacktestLine] = []
            for round_data in self._data:
                result = score_round(round_data, config)
                lines += result.lines
                self.warnings.extend(w for w in result.warnings if w not in self.warnings)
            self._cache[config] = tuple(lines)
        return self._cache[config]


def _evaluate(scorer: _Scorer, baseline: ModelConfig, fixed: dict[str, ConfigValue],
              sweep: dict[str, list[ConfigValue]], *, cv: bool) -> Report:
    def score(overrides: dict[str, ConfigValue]) -> Scored:
        config = replace(baseline, **overrides)
        return Scored(_label(overrides), overrides, config, scorer.lines(config))

    base = score({})
    if sweep:
        keys = tuple(sweep)
        variants = tuple(score({**fixed, **dict(zip(keys, combo))})
                         for combo in product(*sweep.values()))
    elif fixed:
        keys, variants = (), (score(fixed),)
    else:
        keys, variants = (), ()

    picks = ship = comparison = None
    if sweep and cv:
        by_label = {v.label: v for v in variants}
        cv_lines, label_picks = cross_validate({v.label: v.lines for v in variants})
        picks = {r: by_label[label] for r, label in label_picks.items()}
        ship = by_label[ship_value(label_picks, list(by_label))]
        comparison = compare(base.lines, cv_lines)
    elif not sweep and variants:
        comparison = compare(base.lines, variants[0].lines)
    return Report(base, variants, keys, dict(sweep), picks, ship, comparison,
                  tuple(scorer.warnings))


def _header(rounds: list[int], drift_check: bool) -> str:
    return f"rounds {_span(rounds)} · drift check: {'on' if drift_check else 'off'}"


def _table(rounds: list[int], drift_check: bool, report: Report,
           checks: Mapping[int, RoundCheck], *, detail: bool) -> list[str]:
    out = [_header(rounds, drift_check)]
    if not report.sweep_keys or detail:
        out += _baseline_table(report.baseline.lines, checks)
    if report.sweep_keys:
        production = report.variants[0]
        base_mae = _mae(report.baseline.lines)
        for variant in report.variants:
            note = "  (production)" if variant is production else ""
            out.append(f"{variant.label}  {_aggregate_text(variant.lines)}  "
                       f"ΔMAE {signed(_mae(variant.lines) - base_mae, 4)}{note}")
        if report.picks is None:
            out.append("gate: not run — a sweep is gated on its leave-one-round-out lines; "
                       "pass --cv")
            return out
        out.append("LORO picks: " + ", ".join(
            f"{r}→{_pick_text(report.picks[r], report.sweep_keys)}" for r in sorted(report.picks)))
        out.append(f"ship: {report.ship.label}")
    elif report.variants:
        variant = report.variants[0]
        out.append(f"variant {variant.label}  {_aggregate_text(variant.lines)}")
    if report.comparison is not None:
        out += _comparison_text(report.comparison, detail=detail)
    return out


def _baseline_table(lines: Sequence[BacktestLine],
                    checks: Mapping[int, RoundCheck]) -> list[str]:
    rows = [("round", "n", "bias", "MAE", "ledger_n", "Δn", "code_drift")]
    for r, per_round in sorted(_by_round(lines).items()):
        rows.append(_aggregate_row(str(r), calibrate.aggregate(per_round))
                    + _check_cells(checks.get(r)))
    rows.append(_aggregate_row("baseline", calibrate.aggregate(lines)) + ("", "", ""))
    groups = calibrate.grouped(lines, lambda line: line.position)
    rows += [_aggregate_row(pos, groups[pos]) + ("", "", "") for pos in _positions(groups)]
    return [f"{label:<9} {n:>4} {bias:>7} {mae:>6} {ledger:>8} {dn:>4} {drift:>10}".rstrip()
            for label, n, bias, mae, ledger, dn, drift in rows]


def _check_cells(check: RoundCheck | None) -> tuple[str, str, str]:
    if check is None:
        return "-", "-", "-"
    return ("-" if check.ledger_n is None else str(check.ledger_n),
            "-" if check.delta_n is None else _signed_int(check.delta_n),
            "-" if check.code_drift is None else f"{check.code_drift:.3f}")


def _signed_int(value: int) -> str:
    return f"{value:+d}".replace("-", "−")


def _checks_document(checks: Mapping[int, RoundCheck]) -> dict[str, Any]:
    return {str(r): {"n": c.n, "ledger_n": c.ledger_n, "delta_n": c.delta_n,
                     "code_drift": c.code_drift} for r, c in sorted(checks.items())}


def _aggregate_row(label: str, agg: Aggregate) -> tuple[str, str, str, str]:
    return label, str(agg.n), signed(agg.bias, 3), f"{agg.mae:.3f}"


def _aggregate_text(lines: Sequence[BacktestLine]) -> str:
    agg = calibrate.aggregate(lines)
    return f"n {agg.n}  bias {signed(agg.bias, 3)}  MAE {agg.mae:.3f}"


def _comparison_text(c: Comparison, *, detail: bool) -> list[str]:
    wins, rounds = c.round_wins
    out = [
        f"ΔMAE {signed(c.delta_mae, 4)} [CI {signed(c.ci[0], 3)}, {signed(c.ci[1], 3)}] · "
        f"bias {signed(c.baseline.bias, 3)}→{signed(c.variant.bias, 3)} · wins {wins}/{rounds}",
        "per-round ΔMAE: " + ", ".join(f"{r} {signed(v, 4)}" for r, v in c.round_deltas.items()),
    ]
    if detail:
        out.append("per-position ΔMAE: " + ", ".join(
            f"{pos} {signed(g.delta_mae, 4)} (n {g.n})" for pos, g in c.by_position.items()))
        out.append("slices: " + ", ".join(
            f"{name} -" if g is None else f"{name} {signed(g.delta_mae, 4)} (n {g.n})"
            for name, g in c.slices.items()))
    out.append("gate: PASS" if c.beats else "gate: FAIL — " + "; ".join(c.reasons))
    return out


def _document(gw: int, rounds: list[int], drift_check: bool, data: Sequence[RoundData],
              report: Report, checks: Mapping[int, RoundCheck]) -> dict[str, Any]:
    return {
        "gw": gw,
        "rounds": rounds,
        "drift_check": drift_check,
        "decision_commits": {str(d.gw): d.commit for d in data},
        "round_checks": _checks_document(checks),
        "baseline": _scored_document(report.baseline),
        "variants": [_scored_document(v) for v in report.variants],
        "sweep_keys": list(report.sweep_keys),
        "picks": None if report.picks is None
        else {str(r): s.overrides for r, s in sorted(report.picks.items())},
        "ship_value": None if report.ship is None else report.ship.overrides,
        "comparison": None if report.comparison is None
        else comparison_document(report.comparison),
        "warnings": list(report.warnings),
    }


def _scored_document(scored: Scored) -> dict[str, Any]:
    groups = calibrate.grouped(scored.lines, lambda line: line.position)
    return {
        "label": scored.label,
        "overrides": scored.overrides,
        "config": asdict(scored.config),
        "digest": scored.config.digest(),
        "aggregate": calibrate.aggregate(scored.lines).model_dump(),
        "per_round": {str(r): calibrate.aggregate(lines).model_dump()
                      for r, lines in sorted(_by_round(scored.lines).items())},
        "by_position": {pos: groups[pos].model_dump() for pos in _positions(groups)},
    }


def comparison_document(c: Comparison) -> dict[str, Any]:
    return {
        "n": c.n,
        "baseline": c.baseline.model_dump(),
        "variant": c.variant.model_dump(),
        "delta_mae": c.delta_mae,
        "se": c.se,
        "ci": list(c.ci),
        "round_deltas": {str(r): v for r, v in c.round_deltas.items()},
        "round_wins": list(c.round_wins),
        "by_position": {pos: _group_document(g) for pos, g in c.by_position.items()},
        "slices": {name: _group_document(g) for name, g in c.slices.items()},
        "beats": c.beats,
        "reasons": list(c.reasons),
    }


def _group_document(group: GroupComparison | None) -> dict[str, Any] | None:
    if group is None:
        return None
    return {"n": group.n, "baseline": group.baseline.model_dump(),
            "variant": group.variant.model_dump(), "delta_mae": group.delta_mae}


def _parse_sets(texts: Sequence[str], config: ModelConfig) -> dict[str, ConfigValue]:
    fixed: dict[str, ConfigValue] = {}
    for text in texts:
        key, value = parse_assignment(text, config)
        if key in fixed:
            raise ValueError(f"--set {key} given twice")
        fixed[key] = value
    return fixed


def _field_types(config: ModelConfig) -> dict[str, Any]:
    hints = get_type_hints(type(config))
    return {f.name: hints[f.name] for f in fields(config)}


def _parse_value(key: str, raw: str, types: dict[str, Any]) -> ConfigValue:
    if key not in types:
        raise ValueError(f"unknown ModelConfig key {key!r}; valid keys: {', '.join(types)}")
    hint = types[key]
    text = raw.strip().lower()
    if text == "none":
        if NoneType in get_args(hint):
            return None
        raise ValueError(f"{key} is not optional: 'none' is not a value for it")
    if hint is bool:
        if text in ("true", "false"):
            return text == "true"
        raise ValueError(f"{key} is a bool: expected true or false, got {raw!r}")
    try:
        return float(text)
    except ValueError:
        raise ValueError(f"{key}: expected a number, got {raw!r}") from None


def _label(overrides: Mapping[str, ConfigValue]) -> str:
    return gates.overrides_text(overrides) or "baseline"


def _pick_text(scored: Scored, keys: Sequence[str]) -> str:
    return "/".join(value_text(scored.overrides[key]) for key in keys)


def _span(rounds: list[int]) -> str:
    return str(rounds[0]) if len(rounds) == 1 else f"{rounds[0]}-{rounds[-1]}"


def _mae(lines: Sequence[BacktestLine]) -> float:
    return sum(abs(line.error) for line in lines) / len(lines)
