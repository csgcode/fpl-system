"""Expected points: the arithmetic behind data/analysis/gw{N}/players-{pos}.json.

The player analyst decides who plays and how far to trust each player's
history (inputs-{pos}.json); the fixture analyst supplies per-fixture λ and
P(CS) (fixtures.json); this module does every multiplication, once, for all
four positions. Both documents are LLM-written, so they are validated at the
boundary the way API payloads are: a row that parses is safe downstream, and
a row that does not refuses with its id.

Formula, constants and contracts: docs/ep-model.md.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from fpl.calibrate import DEFCON_MINUTES_FLOOR, Uncertainty
from fpl.models import (
    POSITION_ALIASES,
    Bootstrap,
    ElementSummary,
    MatchRecord,
    PastSeason,
    Player,
    PlayerStatus,
    Position,
)
from fpl.state import MAX_GW, MIN_GW

SCHEMA_VERSION = 1
HORIZON = 6

PRIOR_SHRINK_MINUTES = 450.0
PRIOR_POOL_TARGET_MINUTES = 900
PRIOR_MAX_SEASONS = 2
BLEND_EQUIV_MINUTES = 600.0
BLEND_PRIOR_FLOOR = 0.2
LEAGUE_POOL_MIN = 8
LEAGUE_POOL_MIN_MINUTES = 900
COVERAGE_PRICE_FLOOR_TENTHS = 45
COVERAGE_STATUSES = frozenset({PlayerStatus.AVAILABLE, PlayerStatus.DOUBTFUL})
FULL_MATCH_MINUTES = 90
POISSON_TAIL_MIN = 40
POISSON_TAIL_SIGMAS = 10.0

# Ceilings on LLM-written numbers: a decimal slip (0.50 typed as 50) refuses
# instead of producing a thousand-point player.
RATE_CEILINGS = {
    "xg90": 2.0, "xa90": 2.0, "dc90": 30.0, "saves90": 10.0,
    "bonus_per_start": 3.0, "yellow90": 1.0,
}
ATTACK_MULT_RANGE = (0.25, 4.0)
LAMBDA_MAX = 6.0
BASE_LAMBDA_RANGE = (0.5, 5.0)
CLUB_RATING_RANGE = (0.3, 3.0)

P60_ANCHORS = ((50.0, 0.25), (60.0, 0.50), (70.0, 0.80), (80.0, 0.95), (88.0, 1.00))
DEFCON_MINUTES_ANCHORS = ((45.0, 0.0), (60.0, 0.65), (90.0, 1.0))
DEFCON_HIT_ANCHORS = (
    (0.0, 0.00), (0.4, 0.05), (0.7, 0.20), (0.85, 0.35),
    (1.0, 0.55), (1.1, 0.70), (1.3, 0.85), (1.6, 0.93),
)

Anchors = tuple[tuple[float, float], ...]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class _Contract(BaseModel):
    """LLM-written document: unknown keys are refused, not ignored."""

    model_config = ConfigDict(frozen=True, extra="forbid")


# ------------------------------------------------------------- constants


class PositionPoints(_Frozen):
    goal: int
    assist: int = 3
    clean_sheet: int
    goals_conceded_per_two: int
    saves_per_three: int
    defcon_threshold: int | None
    defcon_points: int = 2
    bonus_adjust: float
    pen_save_tail: float = 0.0


POINTS: dict[Position, PositionPoints] = {
    Position.GKP: PositionPoints(
        goal=6, clean_sheet=4, goals_conceded_per_two=-1, saves_per_three=1,
        defcon_threshold=None, bonus_adjust=1.10, pen_save_tail=0.10,
    ),
    Position.DEF: PositionPoints(
        goal=6, clean_sheet=4, goals_conceded_per_two=-1, saves_per_three=0,
        defcon_threshold=10, bonus_adjust=0.90,
    ),
    Position.MID: PositionPoints(
        goal=5, clean_sheet=1, goals_conceded_per_two=0, saves_per_three=0,
        defcon_threshold=12, bonus_adjust=1.00,
    ),
    Position.FWD: PositionPoints(
        goal=4, clean_sheet=0, goals_conceded_per_two=0, saves_per_three=0,
        defcon_threshold=12, bonus_adjust=1.00,
    ),
}


class Rates(_Frozen):
    xg90: float
    xa90: float
    dc90: float
    saves90: float
    bonus_per_start: float
    yellow90: float
    minutes_per_start: float


LEAGUE_FALLBACK: dict[Position, Rates] = {
    Position.GKP: Rates(xg90=0.0, xa90=0.0, dc90=0.0, saves90=3.0, bonus_per_start=0.25, yellow90=0.05, minutes_per_start=90),
    Position.DEF: Rates(xg90=0.07, xa90=0.08, dc90=8.5, saves90=0.0, bonus_per_start=0.30, yellow90=0.15, minutes_per_start=85),
    Position.MID: Rates(xg90=0.18, xa90=0.15, dc90=7.0, saves90=0.0, bonus_per_start=0.30, yellow90=0.15, minutes_per_start=80),
    Position.FWD: Rates(xg90=0.40, xa90=0.12, dc90=3.5, saves90=0.0, bonus_per_start=0.35, yellow90=0.12, minutes_per_start=78),
}

RATE_FIELDS = tuple(Rates.model_fields)


# ------------------------------------------------------------- contracts


class RateOverrides(_Contract):
    xg90: float | None = Field(default=None, ge=0, le=RATE_CEILINGS["xg90"])
    xa90: float | None = Field(default=None, ge=0, le=RATE_CEILINGS["xa90"])
    dc90: float | None = Field(default=None, ge=0, le=RATE_CEILINGS["dc90"])
    saves90: float | None = Field(default=None, ge=0, le=RATE_CEILINGS["saves90"])
    bonus_per_start: float | None = Field(default=None, ge=0, le=RATE_CEILINGS["bonus_per_start"])
    yellow90: float | None = Field(default=None, ge=0, le=RATE_CEILINGS["yellow90"])
    minutes_per_start: float | None = Field(default=None, gt=0, le=FULL_MATCH_MINUTES)
    prior_weight: float | None = Field(default=None, ge=0, le=1)
    attack_mult: float | None = Field(
        default=None, ge=ATTACK_MULT_RANGE[0], le=ATTACK_MULT_RANGE[1]
    )

    def is_empty(self) -> bool:
        return all(getattr(self, name) is None for name in type(self).model_fields)


class PlayerInput(_Contract):
    id: int
    name: str | None = None
    p_start: float = Field(ge=0, le=1)
    p_start_gw: list[float] | None = Field(
        default=None, min_length=HORIZON, max_length=HORIZON
    )
    uncertainty: Uncertainty
    notes: str = ""
    overrides: RateOverrides | None = None
    reason: str | None = None

    @field_validator("p_start_gw")
    @classmethod
    def _probabilities(cls, values: list[float] | None) -> list[float] | None:
        if values is not None and any(not 0 <= v <= 1 for v in values):
            raise ValueError("p_start_gw values must lie in [0, 1]")
        return values

    @model_validator(mode="after")
    def _overrides_need_a_reason(self) -> PlayerInput:
        if self.overrides is not None and not self.overrides.is_empty():
            if not (self.reason or "").strip():
                raise ValueError("overrides need a reason")
        return self

    def start_probabilities(self) -> list[float]:
        return list(self.p_start_gw) if self.p_start_gw is not None else [self.p_start] * HORIZON


def _parse_position(value: Any) -> Any:
    if isinstance(value, str):
        token = value.strip().upper()
        if token in POSITION_ALIASES:
            return POSITION_ALIASES[token]
        try:
            return Position[token]
        except KeyError:
            raise ValueError(
                f"unknown position {value!r}; use GKP, DEF, MID or FWD"
            ) from None
    return value


class InputsDocument(_Contract):
    schema_version: Literal[SCHEMA_VERSION]  # type: ignore[valid-type]
    gw: int = Field(ge=MIN_GW, le=MAX_GW)
    position: Position
    players: list[PlayerInput]

    _position = field_validator("position", mode="before")(_parse_position)

    @model_validator(mode="after")
    def _unique_ids(self) -> InputsDocument:
        seen: set[int] = set()
        duplicates: set[int] = set()
        for entry in self.players:
            if entry.id in seen:
                duplicates.add(entry.id)
            seen.add(entry.id)
        if duplicates:
            raise ValueError(f"duplicate player ids: {sorted(duplicates)}")
        return self


class BaseLambda(_Contract):
    home: float = Field(ge=BASE_LAMBDA_RANGE[0], le=BASE_LAMBDA_RANGE[1])
    away: float = Field(ge=BASE_LAMBDA_RANGE[0], le=BASE_LAMBDA_RANGE[1])


class ClubRating(_Contract):
    att: float = Field(ge=CLUB_RATING_RANGE[0], le=CLUB_RATING_RANGE[1])
    defw: float = Field(ge=CLUB_RATING_RANGE[0], le=CLUB_RATING_RANGE[1])


class FixtureRow(_Contract):
    club: str
    gw: int = Field(ge=MIN_GW, le=MAX_GW)
    opp: str
    venue: Literal["H", "A"]
    fdr: int | None = Field(default=None, ge=1, le=5)
    lambda_att: float = Field(gt=0, le=LAMBDA_MAX)
    lambda_def: float = Field(gt=0, le=LAMBDA_MAX)
    p_cs: float = Field(ge=0, le=1)
    band: bool = False

    def label(self) -> str:
        return f"{self.opp}({self.venue})"


class FixturesDocument(_Contract):
    schema_version: Literal[SCHEMA_VERSION]  # type: ignore[valid-type]
    gw: int = Field(ge=MIN_GW, le=MAX_GW)
    base_lambda: BaseLambda
    ratings: dict[str, ClubRating]
    fixtures: list[FixtureRow]

    def base_mean(self) -> float:
        return (self.base_lambda.home + self.base_lambda.away) / 2

    def by_club_gw(self) -> dict[tuple[str, int], list[FixtureRow]]:
        grouped: dict[tuple[str, int], list[FixtureRow]] = {}
        for row in self.fixtures:
            grouped.setdefault((row.club, row.gw), []).append(row)
        return grouped


def parse_inputs(raw: Any, *, label: str = "inputs") -> InputsDocument:
    return _validate(InputsDocument, raw, label, row_key="players")


def parse_fixtures(raw: Any, *, label: str = "fixtures.json") -> FixturesDocument:
    return _validate(FixturesDocument, raw, label, row_key="fixtures")


def load_inputs(path: Path) -> InputsDocument:
    return parse_inputs(_read_json(path), label=str(path))


def load_fixtures(path: Path) -> FixturesDocument:
    return parse_fixtures(_read_json(path), label=str(path))


def _read_json(path: Path) -> Any:
    if not path.is_file():
        raise ValueError(f"no such file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from None


def _validate(model: type[BaseModel], raw: Any, label: str, *, row_key: str) -> Any:
    try:
        return model.model_validate(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        loc = tuple(first.get("loc") or ())
        where = ""
        if len(loc) >= 2 and loc[0] == row_key and isinstance(loc[1], int):
            index = loc[1]
            row = raw.get(row_key, [])[index] if isinstance(raw, dict) else None
            row_id = row.get("id", row.get("club", "?")) if isinstance(row, dict) else "?"
            where = f" row {index} (id {row_id})"
            loc = loc[2:]
        field = ".".join(str(part) for part in loc)
        detail = f"{field}: {first.get('msg')}" if field else str(first.get("msg"))
        raise ValueError(f"{label}{where}: {detail}") from None


# ------------------------------------------------------------- primitives


def expected_floor_div(mean: float, k: int) -> float:
    """E[floor(X/k)] for X ~ Poisson(mean) — step functions are never
    linearised."""
    if mean <= 0:
        return 0.0
    tail = max(POISSON_TAIL_MIN, math.ceil(mean + POISSON_TAIL_SIGMAS * math.sqrt(mean)))
    log_mean = math.log(mean)
    return sum(
        (n // k) * math.exp(-mean + n * log_mean - math.lgamma(n + 1))
        for n in range(k, tail + 1)
    )


def interpolate(anchors: Anchors, x: float) -> float:
    if x <= anchors[0][0]:
        return anchors[0][1]
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return anchors[-1][1]


def p_sixty(minutes_per_start: float) -> float:
    return interpolate(P60_ANCHORS, minutes_per_start)


def defcon_minutes_factor(minutes_per_start: float) -> float:
    return interpolate(DEFCON_MINUTES_ANCHORS, minutes_per_start)


def prior_weight(current_minutes: float) -> float:
    return max(BLEND_PRIOR_FLOOR, BLEND_EQUIV_MINUTES / (BLEND_EQUIV_MINUTES + current_minutes))


def shrink_rate(observed: float, minutes: float, league: float) -> float:
    return (observed * minutes + league * PRIOR_SHRINK_MINUTES) / (minutes + PRIOR_SHRINK_MINUTES)


def defcon_hit_probability(
    dc90_prior: float, threshold: int, *, hits: int, matches: int, w_prior: float
) -> float:
    mapped = interpolate(DEFCON_HIT_ANCHORS, dc90_prior / threshold)
    if matches <= 0:
        return mapped
    return w_prior * mapped + (1 - w_prior) * hits / matches


# ------------------------------------------------------------- rates


@dataclass
class _Totals:
    minutes: int = 0
    starts: int = 0
    xg: float = 0.0
    xa: float = 0.0
    dc: float = 0.0
    saves: int = 0
    bonus: int = 0
    yellow: int = 0

    def add(self, row: PastSeason | MatchRecord) -> None:
        self.minutes += row.minutes
        self.starts += row.starts or 0
        self.xg += row.expected_goals or 0.0
        self.xa += row.expected_assists or 0.0
        self.dc += row.defensive_contribution or 0.0
        self.saves += row.saves or 0
        self.bonus += row.bonus or 0
        self.yellow += row.yellow_cards or 0

    def rates(self, league: Rates) -> Rates:
        if self.minutes <= 0:
            return league
        per90 = FULL_MATCH_MINUTES / self.minutes
        # Rows without a start (substitute-only spells, seasons predating the
        # starts field) say nothing about how long the player lasts when he
        # does start: take that from the league, not from 90.
        if self.starts > 0:
            starts = float(self.starts)
            minutes_per_start = min(FULL_MATCH_MINUTES, self.minutes / starts)
        else:
            starts = self.minutes / FULL_MATCH_MINUTES
            minutes_per_start = league.minutes_per_start
        return Rates(
            xg90=self.xg * per90,
            xa90=self.xa * per90,
            dc90=self.dc * per90,
            saves90=self.saves * per90,
            bonus_per_start=self.bonus / starts,
            yellow90=self.yellow * per90,
            minutes_per_start=minutes_per_start,
        )


def _prior_seasons(history_past: Sequence[PastSeason]) -> list[PastSeason]:
    chosen: list[PastSeason] = []
    minutes = 0
    for row in sorted(history_past, key=lambda s: s.season_name, reverse=True):
        chosen.append(row)
        minutes += row.minutes
        if minutes >= PRIOR_POOL_TARGET_MINUTES or len(chosen) >= PRIOR_MAX_SEASONS:
            break
    return chosen


def rates_from_seasons(
    history_past: Sequence[PastSeason], league: Rates
) -> tuple[Rates | None, int]:
    totals = _Totals()
    for row in _prior_seasons(history_past):
        totals.add(row)
    if totals.minutes <= 0:
        return None, 0
    return totals.rates(league), totals.minutes


def _shrunk(rates: Rates | None, minutes: int, league: Rates) -> Rates:
    if rates is None or minutes <= 0:
        return league
    return Rates(**{
        name: shrink_rate(getattr(rates, name), minutes, getattr(league, name))
        for name in RATE_FIELDS
    })


def _blend(prior: Rates, current: Rates | None, w: float) -> Rates:
    if current is None:
        return prior
    return Rates(**{
        name: w * getattr(prior, name) + (1 - w) * getattr(current, name)
        for name in RATE_FIELDS
    })


def _league_mean(
    position: Position, players: Iterable[Player], summaries: Mapping[int, ElementSummary]
) -> tuple[Rates, str, int]:
    pool = _Totals()
    members = 0
    for player in players:
        summary = summaries.get(player.id)
        if summary is None:
            continue
        seasons = _prior_seasons(summary.history_past)
        minutes = sum(row.minutes for row in seasons)
        if minutes < LEAGUE_POOL_MIN_MINUTES:
            continue
        members += 1
        for row in seasons:
            pool.add(row)
    if members >= LEAGUE_POOL_MIN:
        return pool.rates(LEAGUE_FALLBACK[position]), "pooled", members
    return LEAGUE_FALLBACK[position], "fallback", members


# ------------------------------------------------------------- output


class EffectiveRates(Rates):
    dc90_prior: float
    prior_weight: float
    prior_source: str
    attack_mult: float
    prior_minutes: int
    current_minutes: int


class Terms(_Frozen):
    appearance: float = 0.0
    attack: float = 0.0
    clean_sheet: float = 0.0
    goals_conceded: float = 0.0
    defcon: float = 0.0
    saves: float = 0.0
    bonus: float = 0.0
    cards: float = 0.0

    def total(self) -> float:
        return sum(getattr(self, name) for name in type(self).model_fields)

    def scaled(self, factor: float) -> Terms:
        return Terms(**{name: getattr(self, name) * factor for name in type(self).model_fields})

    def plus(self, other: Terms) -> Terms:
        return Terms(**{
            name: getattr(self, name) + getattr(other, name) for name in type(self).model_fields
        })


class EpRow(_Frozen):
    id: int
    name: str
    team: str
    price: float
    p_start: float
    p_start_gw: list[float]
    ep_gw: list[float]
    ep_total6: float
    ep_per_million: float
    uncertainty: Uncertainty
    notes: str
    fixtures: list[str]
    terms: Terms
    rates: EffectiveRates


class FixturesCheck(_Frozen):
    clubs: int
    rows_in_window: int
    window: list[int]
    blanks: list[str]


def inspect_fixtures(bootstrap: Bootstrap, fixtures: FixturesDocument, *, gw: int) -> FixturesCheck:
    """Everything build_predictions would refuse about fixtures.json, without
    needing an inputs file — the fixture analyst's self-check."""
    if fixtures.gw != gw:
        raise ValueError(f"fixtures.json is for gw{fixtures.gw}, not gw{gw}")
    clubs = {team.short_name for team in bootstrap.teams}
    _check_clubs(fixtures, clubs)
    _check_fixture_rows(fixtures)
    window = [g for g in range(gw, gw + HORIZON) if g <= MAX_GW]
    grouped = fixtures.by_club_gw()
    blanks = [f"{club} gw{g}" for club in sorted(clubs) for g in window if (club, g) not in grouped]
    return FixturesCheck(
        clubs=len(clubs),
        rows_in_window=sum(len(rows) for (club, g), rows in grouped.items() if g in window),
        window=window,
        blanks=blanks,
    )


class EpResult(_Frozen):
    gw: int
    position: Position
    rows: list[EpRow]
    warnings: list[str]
    missing_summaries: list[int]
    not_scored: int
    league: Rates
    league_source: str
    league_pool: int

    def to_documents(self) -> list[dict[str, Any]]:
        """Rounded rows in the documented prediction schema plus the term and
        rate breakdown — what players-{pos}.json holds."""
        return [_round_row(row) for row in self.rows]


def _round_row(row: EpRow) -> dict[str, Any]:
    return {
        "id": row.id,
        "name": row.name,
        "team": row.team,
        "price": row.price,
        "p_start": round(row.p_start, 3),
        "p_start_gw": [round(v, 3) for v in row.p_start_gw],
        "ep_gw": [round(v, 3) for v in row.ep_gw],
        "ep_total6": round(row.ep_total6, 2),
        "ep_per_million": round(row.ep_per_million, 3),
        "uncertainty": row.uncertainty.value,
        "notes": row.notes,
        "fixtures": row.fixtures,
        "terms": {k: round(v, 2) for k, v in row.terms.model_dump().items()},
        "rates": {
            k: (round(v, 3) if isinstance(v, float) else v)
            for k, v in row.rates.model_dump().items()
        },
    }


def write_predictions(path: Path, result: EpResult) -> None:
    """One row per line inside a JSON list: still `json.loads`-able as a
    whole, and a `grep` for a name returns the complete row."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = ",\n".join(json.dumps(row, ensure_ascii=False) for row in result.to_documents())
    path.write_text(f"[\n{body}\n]\n", encoding="utf-8")


# ------------------------------------------------------------- scoring


def _score_fixture(
    points: PositionPoints,
    rates: Rates,
    fixture: FixtureRow,
    *,
    base_mean: float,
    att_club: float,
    attack_mult: float,
    p_hit: float,
) -> Terms:
    mps = min(rates.minutes_per_start, FULL_MATCH_MINUTES)
    share = mps / FULL_MATCH_MINUTES
    p60 = p_sixty(mps)
    fixture_mult = fixture.lambda_att / (base_mean * att_club) * attack_mult
    saves = 0.0
    if points.saves_per_three:
        saves_mean = rates.saves90 * share * fixture.lambda_def / base_mean
        saves = points.saves_per_three * expected_floor_div(saves_mean, 3) + points.pen_save_tail
    defcon = 0.0
    if points.defcon_threshold is not None:
        defcon = points.defcon_points * p_hit * defcon_minutes_factor(mps)
    return Terms(
        appearance=1 + p60,
        attack=(rates.xg90 * points.goal + rates.xa90 * points.assist) * share * fixture_mult,
        clean_sheet=fixture.p_cs * points.clean_sheet * p60,
        goals_conceded=points.goals_conceded_per_two
        * expected_floor_div(fixture.lambda_def * share, 2),
        defcon=defcon,
        saves=saves,
        bonus=rates.bonus_per_start * points.bonus_adjust,
        cards=-rates.yellow90 * share,
    )


def build_predictions(
    bootstrap: Bootstrap,
    summaries: Mapping[int, ElementSummary],
    fixtures: FixturesDocument,
    inputs: InputsDocument,
    *,
    gw: int,
) -> EpResult:
    if inputs.gw != gw:
        raise ValueError(f"inputs document is for gw{inputs.gw}, not gw{gw}")
    if fixtures.gw != gw:
        raise ValueError(f"fixtures.json is for gw{fixtures.gw}, not gw{gw}")
    position = inputs.position
    points = POINTS[position]
    teams = bootstrap.team_by_id()
    clubs = {team.short_name for team in teams.values()}
    _check_clubs(fixtures, clubs)
    _check_fixture_rows(fixtures)
    by_id = bootstrap.player_by_id()
    window = [g for g in range(gw, gw + HORIZON) if g <= MAX_GW]
    fixtures_by_club_gw = fixtures.by_club_gw()
    warnings: list[str] = []

    for entry in inputs.players:
        player = by_id.get(entry.id)
        if player is None:
            raise ValueError(f"unknown player id {entry.id}")
        if player.element_type != position:
            raise ValueError(
                f"id {entry.id} {player.web_name} has position "
                f"{player.element_type.name}, not {position.name}"
            )
        if entry.name is not None and entry.name != player.web_name:
            raise ValueError(
                f"id {entry.id}: inputs name {entry.name!r} does not match "
                f"bootstrap web_name {player.web_name!r}"
            )

    position_players = [p for p in bootstrap.elements if p.element_type == position]
    not_scored = _check_coverage(position, position_players, inputs)
    league, league_source, league_pool = _league_mean(position, position_players, summaries)
    if league_source == "fallback":
        warnings.append(
            f"league mean for {position.name} uses the v1 fallback table — only "
            f"{league_pool} cached summaries with ≥ {LEAGUE_POOL_MIN_MINUTES} prior "
            f"minutes (need {LEAGUE_POOL_MIN}); run summaries --shortlist first"
        )
    base_mean = fixtures.base_mean()
    missing_summaries: list[int] = []
    blanks: set[tuple[str, int]] = set()
    rows: list[EpRow] = []
    for entry in inputs.players:
        player = by_id[entry.id]
        club = teams[player.team].short_name
        summary = summaries.get(entry.id)
        if summary is None:
            missing_summaries.append(entry.id)
        rates = _effective_rates(entry, summary, league, points)
        p_hit = 0.0
        if points.defcon_threshold is not None:
            p_hit = _defcon_probability(summary, rates, points.defcon_threshold)
        starts = entry.start_probabilities()[: len(window)]
        ep_gw: list[float] = []
        labels: list[str] = []
        terms = Terms()
        for index, g in enumerate(window):
            rows_for_gw = fixtures_by_club_gw.get((club, g), [])
            if not rows_for_gw:
                blanks.add((club, g))
                ep_gw.append(0.0)
                labels.append("-")
                continue
            gw_terms = Terms()
            for fixture in rows_for_gw:
                gw_terms = gw_terms.plus(
                    _score_fixture(
                        points, rates, fixture,
                        base_mean=base_mean,
                        att_club=fixtures.ratings[club].att,
                        attack_mult=rates.attack_mult,
                        p_hit=p_hit,
                    )
                )
            weighted = gw_terms.scaled(starts[index])
            terms = terms.plus(weighted)
            ep_gw.append(weighted.total())
            labels.append("+".join(f.label() for f in rows_for_gw))
        ep_total = sum(ep_gw)
        rows.append(
            EpRow(
                id=player.id,
                name=player.web_name,
                team=club,
                price=player.price_m,
                p_start=starts[0],
                p_start_gw=starts,
                ep_gw=ep_gw,
                ep_total6=ep_total,
                ep_per_million=ep_total / player.price_m,
                uncertainty=entry.uncertainty,
                notes=entry.notes,
                fixtures=labels,
                terms=terms,
                rates=rates,
            )
        )
    for club, g in sorted(blanks):
        warnings.append(f"{club} has no fixture in gw{g} (blank) — scored 0 for that gameweek")
    rows.sort(key=lambda row: (-row.ep_total6, row.id))
    return EpResult(
        gw=gw,
        position=position,
        rows=rows,
        warnings=warnings,
        missing_summaries=missing_summaries,
        not_scored=not_scored,
        league=league,
        league_source=league_source,
        league_pool=league_pool,
    )


def _check_clubs(fixtures: FixturesDocument, clubs: set[str]) -> None:
    named = set(fixtures.ratings) | {r.club for r in fixtures.fixtures} | {r.opp for r in fixtures.fixtures}
    unknown = sorted(named - clubs)
    if unknown:
        raise ValueError(
            f"fixtures.json names unknown club(s) {unknown}; bootstrap short names are "
            f"{sorted(clubs)}"
        )
    unrated = sorted(clubs - set(fixtures.ratings))
    if unrated:
        raise ValueError(f"fixtures.json rates no club {unrated}")


def _check_fixture_rows(fixtures: FixturesDocument) -> None:
    for index, row in enumerate(fixtures.fixtures):
        if row.opp == row.club:
            raise ValueError(
                f"fixtures.json row {index} (club {row.club}): gw{row.gw} opp is the club itself"
            )
    for (club, g), rows in fixtures.by_club_gw().items():
        if len(rows) > 2:
            raise ValueError(
                f"fixtures.json gives {club} {len(rows)} fixtures in gw{g}; "
                f"a gameweek holds at most two"
            )
        if len(rows) == 2 and (rows[0].opp, rows[0].venue) == (rows[1].opp, rows[1].venue):
            raise ValueError(
                f"fixtures.json repeats {club} {rows[0].label()} in gw{g}; "
                f"a double gameweek needs two different fixtures"
            )


def _check_coverage(
    position: Position, players: Sequence[Player], inputs: InputsDocument
) -> int:
    judged = {entry.id for entry in inputs.players}
    required = []
    not_scored = 0
    for player in players:
        if player.id in judged:
            continue
        if player.now_cost > COVERAGE_PRICE_FLOOR_TENTHS and player.status in COVERAGE_STATUSES:
            required.append(player)
        else:
            not_scored += 1
    if required:
        listing = ", ".join(
            f"id {p.id} {p.web_name} £{p.price_m:.1f} {p.status.value}"
            for p in sorted(required, key=lambda p: -p.now_cost)[:30]
        )
        raise ValueError(
            f"inputs-{position.name}.json misses {len(required)} player(s) above "
            f"£4.5m with status a/d — every one needs a p_start: {listing}"
        )
    return not_scored


def _effective_rates(
    entry: PlayerInput, summary: ElementSummary | None, league: Rates, points: PositionPoints
) -> EffectiveRates:
    prior_rates, prior_minutes = (
        rates_from_seasons(summary.history_past, league) if summary else (None, 0)
    )
    prior = _shrunk(prior_rates, prior_minutes, league)
    current_totals = _Totals()
    if summary is not None:
        for row in summary.history:
            if row.minutes > 0:
                current_totals.add(row)
    current = current_totals.rates(league) if current_totals.minutes > 0 else None
    overrides = entry.overrides or RateOverrides()
    w = overrides.prior_weight if overrides.prior_weight is not None else prior_weight(
        current_totals.minutes
    )
    blended = _blend(prior, current, w)
    values = {
        name: (
            getattr(overrides, name)
            if getattr(overrides, name) is not None
            else getattr(blended, name)
        )
        for name in RATE_FIELDS
    }
    return EffectiveRates(
        **values,
        dc90_prior=overrides.dc90 if overrides.dc90 is not None else prior.dc90,
        prior_weight=w,
        prior_source="history_past" if prior_minutes > 0 else "league_mean",
        attack_mult=overrides.attack_mult if overrides.attack_mult is not None else 1.0,
        prior_minutes=prior_minutes,
        current_minutes=current_totals.minutes,
    )


def _defcon_probability(
    summary: ElementSummary | None, rates: EffectiveRates, threshold: int
) -> float:
    hits = matches = 0
    if summary is not None:
        for row in summary.history:
            if row.minutes >= DEFCON_MINUTES_FLOOR:
                matches += 1
                hits += int((row.defensive_contribution or 0.0) >= threshold)
    return defcon_hit_probability(
        rates.dc90_prior, threshold, hits=hits, matches=matches, w_prior=rates.prior_weight
    )
