"""Prediction-vs-actual calibration for a completed round.

Joins the player analysts' EP predictions (data/analysis/gw{M}/players-*.json)
against the round's finalized actuals and reduces them to the stats the
retro-analyst needs. All arithmetic lives here, in code — the analyst agents
interpret the numbers, they never recompute them.

Prediction files are LLM-written, so they are validated at this boundary the
same way API payloads are: a row that parses is safe everywhere downstream.
Analysts enrich rows with diagnostic fields beyond the documented schema;
unknown fields are ignored, not contract.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fpl.models import EventLive, LiveStats, Position
from fpl.state import PlannedPicks

PREDICTION_POSITIONS = (Position.GKP, Position.DEF, Position.MID, Position.FWD)
SCHEMA_VERSION = 1


class Uncertainty(str, Enum):
    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"


class PlayerPrediction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    id: int
    name: str
    team: str
    position: Position
    price: float
    p_start: float = Field(ge=0, le=1)
    ep_gw: tuple[float, ...] = Field(min_length=1)
    uncertainty: Uncertainty

    @property
    def predicted(self) -> float:
        return self.ep_gw[0]


class PlayerLine(BaseModel):
    """One matched prediction: what we said, what happened. `error` is
    actual − predicted, so positive means we under-predicted."""

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    team: str
    position: str
    price: float
    uncertainty: Uncertainty
    p_start: float
    predicted: float
    actual: int
    error: float
    minutes: int
    started: bool


class Aggregate(BaseModel):
    model_config = ConfigDict(frozen=True)

    n: int
    bias: float
    mae: float


DEFCON_THRESHOLDS = {"DEF": 10, "MID": 12, "FWD": 12}
DEFCON_MINUTES_FLOOR = 60


class DefconLine(BaseModel):
    """One DefCon observation for the retro-analyst's pooled recalibration
    sample. Only near-full matches count — a sub's rate says nothing about
    the per-match step function."""

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    position: str
    minutes: int
    value: float
    threshold: int
    hit: bool


class SquadPlayerLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    slot: int
    role: str
    captain: bool
    vice: bool
    predicted: float | None
    actual: int | None
    minutes: int | None


class CaptainReport(BaseModel):
    """Chosen captain vs the hindsight-best captain among the XI we fielded —
    the bench is excluded because captaining it was never available."""

    model_config = ConfigDict(frozen=True)

    chosen_id: int
    chosen_name: str
    chosen_predicted: float | None
    chosen_actual: int
    hindsight_best_id: int
    hindsight_best_name: str
    hindsight_best_actual: int
    forgone: int


class SquadSection(BaseModel):
    """XI totals count the captain's points twice, matching FPL scoring.
    Actuals ignore auto-subs: this is the raw XI-as-named score."""

    model_config = ConfigDict(frozen=True)

    predicted_xi_total: float
    actual_xi_total: int
    players: tuple[SquadPlayerLine, ...]
    captain: CaptainReport
    bench_points_stranded: int


class MinutesCalibration(BaseModel):
    model_config = ConfigDict(frozen=True)

    n: int
    brier: float
    expected_starts: float
    actual_starts: int


class CumulativeStats(BaseModel):
    """Pooled per-player rows across every calibrated round so far — the
    6-GW calibration horizon reads from here, not from any single retro."""

    model_config = ConfigDict(frozen=True)

    rounds: tuple[int, ...]
    overall: Aggregate
    by_position: dict[str, Aggregate]
    minutes_brier: float
    minutes_n: int


class CalibrationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = SCHEMA_VERSION
    round: int
    players: tuple[PlayerLine, ...]
    unmatched_prediction_ids: tuple[int, ...]
    overall: Aggregate
    by_position: dict[str, Aggregate]
    by_uncertainty: dict[str, Aggregate]
    by_price_band: dict[str, Aggregate]
    minutes: MinutesCalibration
    defcon: tuple[DefconLine, ...] = ()
    squad: SquadSection | None = None
    cumulative: CumulativeStats | None = None
    warnings: tuple[str, ...] = ()


def build_report(
    predictions: tuple[PlayerPrediction, ...],
    live: EventLive,
    *,
    match_round: int,
    picks: PlannedPicks | None = None,
    prior_reports: Sequence[CalibrationReport] = (),
) -> CalibrationReport:
    stats_by_id = live.by_id()
    players = []
    unmatched = []
    for prediction in predictions:
        stats = stats_by_id.get(prediction.id)
        if stats is None:
            unmatched.append(prediction.id)
            continue
        players.append(
            PlayerLine(
                id=prediction.id,
                name=prediction.name,
                team=prediction.team,
                position=prediction.position.name,
                price=prediction.price,
                uncertainty=prediction.uncertainty,
                p_start=prediction.p_start,
                predicted=prediction.predicted,
                actual=stats.total_points,
                error=round(stats.total_points - prediction.predicted, 3),
                minutes=stats.minutes,
                started=stats.started,
            )
        )
    if not players:
        raise ValueError(
            "no prediction matched the live payload — are the analysis files "
            "and the round from the same gameweek?"
        )
    warnings: list[str] = []
    squad = None
    if picks is not None:
        prediction_by_id = {p.id: p for p in predictions}
        squad = _squad_section(picks, prediction_by_id, stats_by_id, warnings)
    return CalibrationReport(
        round=match_round,
        cumulative=_cumulative(match_round, players, prior_reports),
        players=tuple(players),
        unmatched_prediction_ids=tuple(unmatched),
        overall=_aggregate(players),
        by_position=_grouped(players, lambda line: line.position),
        by_uncertainty=_grouped(players, lambda line: line.uncertainty.value),
        by_price_band=_grouped(players, lambda line: _price_band(line.price)),
        minutes=_minutes_calibration(players),
        defcon=_defcon_sample(predictions, stats_by_id),
        squad=squad,
        warnings=tuple(warnings),
    )


def _cumulative(
    match_round: int,
    players: Sequence[PlayerLine],
    prior_reports: Sequence[CalibrationReport],
) -> CumulativeStats:
    rounds = sorted([report.round for report in prior_reports] + [match_round])
    duplicates = {r for r in rounds if rounds.count(r) > 1}
    if duplicates:
        raise ValueError(
            f"round {min(duplicates)} appears more than once in the pooled "
            "reports — a recalibrated round replaces its file, it is never "
            "passed as a prior"
        )
    pooled = [line for report in prior_reports for line in report.players]
    pooled.extend(players)
    return CumulativeStats(
        rounds=tuple(rounds),
        overall=_aggregate(pooled),
        by_position=_grouped(pooled, lambda line: line.position),
        minutes_brier=_brier(pooled),
        minutes_n=len(pooled),
    )


def load_report(path: Path) -> CalibrationReport:
    document = json.loads(path.read_text(encoding="utf-8"))
    version = document.get("schema_version") if isinstance(document, dict) else None
    if version != SCHEMA_VERSION:
        raise ValueError(
            f"{path} has schema_version {version!r}, expected {SCHEMA_VERSION} — "
            "regenerate it with `fpl calibrate` (calibration files are derived)"
        )
    return CalibrationReport.model_validate(document)


def _defcon_sample(
    predictions: tuple[PlayerPrediction, ...],
    stats_by_id: dict[int, LiveStats],
) -> tuple[DefconLine, ...]:
    lines = []
    for prediction in predictions:
        threshold = DEFCON_THRESHOLDS.get(prediction.position.name)
        stats = stats_by_id.get(prediction.id)
        if threshold is None or stats is None:
            continue
        if stats.minutes < DEFCON_MINUTES_FLOOR:
            continue
        value = stats.defensive_contribution or 0.0
        lines.append(
            DefconLine(
                id=prediction.id,
                name=prediction.name,
                position=prediction.position.name,
                minutes=stats.minutes,
                value=value,
                threshold=threshold,
                hit=value >= threshold,
            )
        )
    return tuple(lines)


def _squad_section(
    picks: PlannedPicks,
    prediction_by_id: dict[int, PlayerPrediction],
    stats_by_id: dict[int, LiveStats],
    warnings: list[str],
) -> SquadSection:
    lines = []
    for pick in picks.in_position_order():
        prediction = prediction_by_id.get(pick.id)
        stats = stats_by_id.get(pick.id)
        if prediction is None:
            warnings.append(
                f"squad pick {pick.name or pick.id} (id {pick.id}) has no "
                "prediction row — excluded from the predicted total"
            )
        if stats is None:
            warnings.append(
                f"squad pick {pick.name or pick.id} (id {pick.id}) is missing "
                "from the live payload — excluded from the actual total"
            )
        lines.append(
            SquadPlayerLine(
                id=pick.id,
                name=pick.name,
                slot=pick.position,
                role="XI" if pick.starts else "bench",
                captain=pick.captain,
                vice=pick.vice,
                predicted=None if prediction is None else prediction.predicted,
                actual=None if stats is None else stats.total_points,
                minutes=None if stats is None else stats.minutes,
            )
        )
    xi = [line for line in lines if line.role == "XI"]
    bench = [line for line in lines if line.role == "bench"]
    captain_line = next(line for line in lines if line.captain)
    hindsight = max(
        (line for line in xi if line.actual is not None),
        key=lambda line: line.actual,
    )
    chosen_actual = captain_line.actual or 0
    return SquadSection(
        predicted_xi_total=round(
            sum(line.predicted or 0.0 for line in xi) + (captain_line.predicted or 0.0),
            2,
        ),
        actual_xi_total=sum(line.actual or 0 for line in xi) + chosen_actual,
        players=tuple(lines),
        captain=CaptainReport(
            chosen_id=captain_line.id,
            chosen_name=captain_line.name,
            chosen_predicted=captain_line.predicted,
            chosen_actual=chosen_actual,
            hindsight_best_id=hindsight.id,
            hindsight_best_name=hindsight.name,
            hindsight_best_actual=hindsight.actual or 0,
            forgone=(hindsight.actual or 0) - chosen_actual,
        ),
        bench_points_stranded=sum(line.actual or 0 for line in bench),
    )


def _aggregate(players: Sequence[PlayerLine]) -> Aggregate:
    errors = [line.error for line in players]
    return Aggregate(
        n=len(errors),
        bias=round(sum(errors) / len(errors), 3),
        mae=round(sum(abs(e) for e in errors) / len(errors), 3),
    )


def _grouped(
    players: Sequence[PlayerLine], key: Callable[[PlayerLine], str]
) -> dict[str, Aggregate]:
    groups: dict[str, list[PlayerLine]] = {}
    for line in players:
        groups.setdefault(key(line), []).append(line)
    return {name: _aggregate(lines) for name, lines in groups.items()}


def _price_band(price: float) -> str:
    if price < 5.5:
        return "<5.5"
    if price < 8.0:
        return "5.5-7.9"
    return ">=8.0"


def _minutes_calibration(players: Sequence[PlayerLine]) -> MinutesCalibration:
    return MinutesCalibration(
        n=len(players),
        brier=_brier(players),
        expected_starts=round(sum(line.p_start for line in players), 2),
        actual_starts=sum(1 for line in players if line.started),
    )


def _brier(players: Sequence[PlayerLine]) -> float:
    squared = [(line.p_start - (1 if line.started else 0)) ** 2 for line in players]
    return round(sum(squared) / len(squared), 4)


def _prediction_filename(position: Position) -> str:
    return f"players-{position.name}.json"


def load_predictions(analysis_dir: Path) -> tuple[PlayerPrediction, ...]:
    if not analysis_dir.is_dir():
        raise ValueError(f"no analysis directory at {analysis_dir}")
    missing = [
        _prediction_filename(position)
        for position in PREDICTION_POSITIONS
        if not (analysis_dir / _prediction_filename(position)).is_file()
    ]
    if missing:
        raise ValueError(
            f"analysis at {analysis_dir} is incomplete — missing "
            f"{', '.join(missing)}"
        )
    predictions: dict[int, PlayerPrediction] = {}
    for position in PREDICTION_POSITIONS:
        path = analysis_dir / _prediction_filename(position)
        for prediction in _load_position_file(path, position):
            existing = predictions.get(prediction.id)
            if existing is not None:
                raise ValueError(
                    f"player id {prediction.id} appears in both "
                    f"{_prediction_filename(existing.position)} and "
                    f"{_prediction_filename(position)}"
                )
            predictions[prediction.id] = prediction
    return tuple(predictions.values())


def _load_position_file(path: Path, position: Position) -> list[PlayerPrediction]:
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.name} is not valid JSON: {exc}") from None
    if not isinstance(rows, list):
        raise ValueError(f"{path.name} must be a JSON list of prediction rows")
    parsed = []
    for index, row in enumerate(rows):
        try:
            parsed.append(
                PlayerPrediction.model_validate({**row, "position": position})
            )
        except ValidationError as exc:
            first = exc.errors()[0]
            raise ValueError(
                f"{path.name} row {index} (id {row.get('id', '?')}): "
                f"{first.get('loc')} {first.get('msg')}"
            ) from None
    return parsed
