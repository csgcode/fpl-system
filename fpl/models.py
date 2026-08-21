"""Typed models for FPL API payloads.

All validation happens here, at the boundary: a payload that parses is safe
for every downstream consumer. Models are frozen — snapshots are immutable.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, IntEnum

from pydantic import BaseModel, ConfigDict, Field


class Position(IntEnum):
    GKP = 1
    DEF = 2
    MID = 3
    FWD = 4
    # Assistant-manager element type; parsed so bootstrap validation never
    # fails on it, excluded from all analysis outputs.
    MNG = 5


PLAYING_POSITIONS = frozenset({Position.GKP, Position.DEF, Position.MID, Position.FWD})


class PlayerStatus(str, Enum):
    AVAILABLE = "a"
    DOUBTFUL = "d"
    INJURED = "i"
    NOT_ELIGIBLE = "n"
    SUSPENDED = "s"
    UNAVAILABLE = "u"


class _FrozenModel(BaseModel):
    # extra="ignore": the FPL API adds fields between seasons; unknown inbound
    # fields stay available in the raw snapshot, they are not contract here.
    model_config = ConfigDict(frozen=True, extra="ignore")


class Team(_FrozenModel):
    id: int
    name: str
    short_name: str
    strength_attack_home: int
    strength_attack_away: int
    strength_defence_home: int
    strength_defence_away: int


class Event(_FrozenModel):
    id: int
    name: str
    deadline_time: datetime
    finished: bool
    is_current: bool
    is_next: bool


class Player(_FrozenModel):
    id: int
    web_name: str
    first_name: str
    second_name: str
    team: int
    element_type: Position
    now_cost: int = Field(ge=30, le=200)
    status: PlayerStatus
    chance_of_playing_next_round: int | None = Field(default=None, ge=0, le=100)
    news: str = ""
    news_added: datetime | None = None
    minutes: int = Field(ge=0)
    total_points: int
    form: float
    selected_by_percent: float = Field(ge=0, le=100)
    ict_index: float
    expected_goals: float = Field(ge=0)
    expected_assists: float = Field(ge=0)
    defensive_contribution: float | None = None
    penalties_order: int | None = None
    direct_freekicks_order: int | None = None
    corners_and_indirect_freekicks_order: int | None = None

    @property
    def price_m(self) -> float:
        return self.now_cost / 10


class Bootstrap(_FrozenModel):
    events: tuple[Event, ...]
    teams: tuple[Team, ...]
    elements: tuple[Player, ...]

    def next_gw(self) -> int | None:
        return next((e.id for e in self.events if e.is_next), None)

    def current_gw(self) -> int | None:
        return next((e.id for e in self.events if e.is_current), None)

    def next_deadline(self) -> datetime | None:
        return next((e.deadline_time for e in self.events if e.is_next), None)

    def team_by_id(self) -> dict[int, Team]:
        return {t.id: t for t in self.teams}

    def player_by_id(self) -> dict[int, Player]:
        return {p.id: p for p in self.elements}


class Fixture(_FrozenModel):
    id: int
    event: int | None
    team_h: int
    team_a: int
    team_h_difficulty: int = Field(ge=1, le=5)
    team_a_difficulty: int = Field(ge=1, le=5)
    kickoff_time: datetime | None = None
    finished: bool


class MatchRecord(_FrozenModel):
    fixture: int
    round: int | None = None
    minutes: int = Field(ge=0)
    total_points: int
    goals_scored: int = Field(ge=0)
    assists: int = Field(ge=0)
    expected_goals: float | None = None
    expected_assists: float | None = None
    defensive_contribution: float | None = None


class PastSeason(_FrozenModel):
    season_name: str
    start_cost: int
    end_cost: int
    minutes: int = Field(ge=0)
    total_points: int
    goals_scored: int = Field(ge=0)
    assists: int = Field(ge=0)
    expected_goals: float | None = None
    expected_assists: float | None = None
    defensive_contribution: float | None = None


class ElementSummary(_FrozenModel):
    history: tuple[MatchRecord, ...]
    history_past: tuple[PastSeason, ...]


class EntrySummary(_FrozenModel):
    id: int
    name: str
    summary_overall_points: int | None = None
    last_deadline_bank: int | None = None
    last_deadline_value: int | None = None


SHORTLIST_MIN_PRICE_TENTHS = 55
SHORTLIST_MIN_OWNERSHIP_PCT = 5.0
SHORTLIST_MAX_PENALTY_ORDER = 2


def is_shortlisted(player: Player) -> bool:
    """Shortlist rule from agents/data-collector.md (element-summary fetches)."""
    if player.element_type not in PLAYING_POSITIONS:
        return False
    return (
        player.now_cost >= SHORTLIST_MIN_PRICE_TENTHS
        or player.selected_by_percent >= SHORTLIST_MIN_OWNERSHIP_PCT
        or (
            player.penalties_order is not None
            and player.penalties_order <= SHORTLIST_MAX_PENALTY_ORDER
        )
    )
