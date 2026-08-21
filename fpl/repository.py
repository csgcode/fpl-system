"""Filterable read side over cached snapshots. Tools and agents build on
this instead of re-parsing raw JSON — a query touches only the players that
match (e.g. MID under £5.5m), never the full dump."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from fpl.models import (
    PLAYING_POSITIONS,
    Bootstrap,
    Player,
    PlayerStatus,
    Position,
    is_shortlisted,
)
from fpl.store import SnapshotMissingError, SnapshotStore

PLAYERS_SLIM_COLUMNS = (
    "id",
    "name",
    "team",
    "position",
    "price",
    "status",
    "chance_of_playing",
    "news",
    "news_added",
    "minutes",
    "total_points",
    "form",
    "xG",
    "xA",
    "ict_index",
    "defensive_contribution",
    "selected_by_percent",
    "penalties_order",
    "direct_freekicks_order",
    "corners_and_indirect_freekicks_order",
    "starts",
    "clean_sheets",
    "goals_conceded",
    "xGC",
    "saves",
    "cost_change_start",
)


@dataclass(frozen=True)
class PlayerRow:
    player: Player
    team_short_name: str


@dataclass(frozen=True)
class PlayerFilter:
    """Empty collections / None mean 'no constraint'. Non-playing element
    types (managers) never match any filter."""

    positions: frozenset[Position] = field(default_factory=frozenset)
    min_price_m: float | None = None
    max_price_m: float | None = None
    teams: frozenset[str] = field(default_factory=frozenset)
    statuses: frozenset[PlayerStatus] = field(default_factory=frozenset)
    min_ownership_pct: float | None = None
    shortlisted_only: bool = False

    def matches(self, row: PlayerRow) -> bool:
        p = row.player
        if p.element_type not in PLAYING_POSITIONS:
            return False
        if self.positions and p.element_type not in self.positions:
            return False
        if self.min_price_m is not None and p.price_m < self.min_price_m:
            return False
        if self.max_price_m is not None and p.price_m > self.max_price_m:
            return False
        if self.teams and row.team_short_name not in self.teams:
            return False
        if self.statuses and p.status not in self.statuses:
            return False
        if (
            self.min_ownership_pct is not None
            and p.selected_by_percent < self.min_ownership_pct
        ):
            return False
        if self.shortlisted_only and not is_shortlisted(p):
            return False
        return True


SORT_KEYS: dict[str, Callable[[PlayerRow], Any]] = {
    "id": lambda r: r.player.id,
    "price": lambda r: (-r.player.now_cost, r.player.id),
    "points": lambda r: (-r.player.total_points, r.player.id),
    "ownership": lambda r: (-r.player.selected_by_percent, r.player.id),
    "form": lambda r: (-r.player.form, r.player.id),
}


class PlayerRepository:
    def __init__(self, store: SnapshotStore) -> None:
        self._store = store

    def query(
        self,
        gw: int,
        player_filter: PlayerFilter = PlayerFilter(),
        sort: str = "price",
        limit: int | None = None,
    ) -> list[PlayerRow]:
        if sort not in SORT_KEYS:
            raise ValueError(
                f"unknown sort key {sort!r}; choose one of: "
                f"{', '.join(sorted(SORT_KEYS))}"
            )
        if limit is not None and limit < 0:
            raise ValueError(f"limit must not be negative, got {limit}")
        try:
            raw = self._store.load(gw, "bootstrap")
        except SnapshotMissingError as exc:
            raise exc.with_hint(f"bootstrap --gw {gw}") from None
        bootstrap = Bootstrap.model_validate(raw)
        teams = bootstrap.team_by_id()
        rows = [
            row
            for row in (
                PlayerRow(p, teams[p.team].short_name) for p in bootstrap.elements
            )
            if player_filter.matches(row)
        ]
        rows.sort(key=SORT_KEYS[sort])
        return rows[:limit] if limit is not None else rows


def slim_values(row: PlayerRow) -> list[Any]:
    p = row.player

    def blank_if_none(value: Any) -> Any:
        return "" if value is None else value

    return [
        p.id,
        p.web_name,
        row.team_short_name,
        p.element_type.name,
        f"{p.price_m:.1f}",
        p.status.value,
        blank_if_none(p.chance_of_playing_next_round),
        p.news,
        p.news_added.isoformat() if p.news_added else "",
        p.minutes,
        p.total_points,
        p.form,
        p.expected_goals,
        p.expected_assists,
        p.ict_index,
        blank_if_none(p.defensive_contribution),
        p.selected_by_percent,
        blank_if_none(p.penalties_order),
        blank_if_none(p.direct_freekicks_order),
        blank_if_none(p.corners_and_indirect_freekicks_order),
        p.starts,
        p.clean_sheets,
        p.goals_conceded,
        p.expected_goals_conceded,
        p.saves,
        p.cost_change_start,
    ]


def slim_record(row: PlayerRow) -> dict[str, Any]:
    return dict(zip(PLAYERS_SLIM_COLUMNS, slim_values(row)))
