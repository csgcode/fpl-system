"""Backtest harness: re-scores past rounds from exactly what production read
before each deadline.

A round loads only when nothing in it could carry the outcome: every model
input was fetched before the deadline, no element summary holds the round
itself, the actuals are final, and the inputs on disk still match the
round's decision commit. A loaded round is then scored under a model
variant, one line per (player, round), exactly as the calibration ledger
scores what `fpl ep` would have written.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from fpl import calibrate, ep, fixture_ratings
from fpl.calibrate import Aggregate, PlayerLine, PlayerPrediction
from fpl.decision_record import decision_commit, drifted, repo_root
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
from fpl.store import ARCHIVE_STAMP_FORMAT, SnapshotStore

POSITIONS = (Position.GKP, Position.DEF, Position.MID, Position.FWD)
INPUTS_POLICIES = ("keep",)

GATE_Z = 1.96
GATE_BIAS_SLACK = 0.05
GATE_POSITION_SLACK = 0.02
GATE_MIN_EFFECT = -0.01


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
        reasons.append(f"ci: upper {ci[1]:+.3f} ≥ 0")
    if abs(bias_variant) > abs(bias_base) + GATE_BIAS_SLACK:
        reasons.append(f"bias: |b_v| {abs(bias_variant):.3f} > |b_b| {abs(bias_base):.3f} "
                       f"+ {GATE_BIAS_SLACK}")
    for position, group in by_position.items():
        if group.delta_mae > GATE_POSITION_SLACK:
            reasons.append(f"position {position}: ΔMAE {group.delta_mae:+.3f} "
                           f"> {GATE_POSITION_SLACK:+}")
    if delta > GATE_MIN_EFFECT:
        reasons.append(f"effect: ΔMAE {delta:+.4f} > {GATE_MIN_EFFECT:+}")
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
    sha = decision_commit(repo, gw, _relative(decisions_root, repo) or "data/decisions")
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
                         + " — restore them, or pass drift_check=False to score the files on disk")
    return sha


def _relative(path: Path, repo: Path) -> str | None:
    try:
        return str(path.resolve().relative_to(repo))
    except ValueError:
        return None
