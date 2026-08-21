"""Fetch-if-stale orchestration: the one place deciding when the network is
touched. Payloads are validated BEFORE persisting — an invalid response is
never written to disk. Analysts consume only what this service has saved.
"""

from __future__ import annotations

import csv
import io
import math
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from fpl.api import Fetched, FplApi
from fpl.models import (
    Bootstrap,
    ElementSummary,
    EntryHistory,
    EntrySummary,
    EventPicks,
    Fixture,
    MatchRecord,
    Player,
    is_shortlisted,
)
from fpl.repository import PLAYERS_SLIM_COLUMNS, PlayerRepository, slim_values
from fpl.store import SnapshotMissingError, SnapshotStore, utcnow

DEFAULT_MAX_AGE_HOURS = 24.0
PLAYERS_SLIM_FILENAME = "players-slim.csv"


def _summary_name(player_id: int) -> str:
    return f"players/summary-{player_id}"


def _dedupe(ids: Iterable[int]) -> list[int]:
    """Order-preserving: callers pass shortlists that may repeat an id, and a
    repeated fetch would archive the snapshot it just wrote."""
    return list(dict.fromkeys(ids))


class GameweekMismatchError(ValueError):
    def __init__(self, requested_gw: int, payload_gw: int | None) -> None:
        super().__init__(
            f"bootstrap reports next gameweek {payload_gw}, not the requested "
            f"gw{requested_gw}; pass --allow-gw-mismatch to save it anyway"
        )
        self.requested_gw = requested_gw
        self.payload_gw = payload_gw


@dataclass(frozen=True)
class FetchEvent:
    """One snapshot access: whether the network was touched, and the age of
    the snapshot served from cache."""

    name: str
    fetched: bool
    age_hours: float | None = None


@dataclass(frozen=True)
class PriorSeasonResult:
    path: Path
    players: int
    no_pl_history: int
    missing_summaries: int


@dataclass(frozen=True)
class ActualLine:
    """Per-player totals for one round; DGW rows are summed."""

    player_id: int
    matched: bool
    minutes: int = 0
    total_points: int = 0
    goals_scored: int = 0
    assists: int = 0
    bonus: int = 0
    bps: int = 0


@dataclass
class _Log:
    events: list[FetchEvent] = field(default_factory=list)


class FplDataService:
    def __init__(
        self,
        api: FplApi,
        store: SnapshotStore,
        now: Callable[[], datetime] = utcnow,
        throttle_s: float = 0.3,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api = api
        self._store = store
        self._now = now
        self._throttle_s = throttle_s
        self._sleep = sleep
        self._log = _Log()

    def take_fetch_log(self) -> tuple[FetchEvent, ...]:
        """Drains the snapshot accesses since the last call — the CLI reports
        cache hits from this."""
        events = tuple(self._log.events)
        self._log.events.clear()
        return events

    def bootstrap(
        self,
        gw: int,
        *,
        max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
        force: bool = False,
        require_next_gw: bool = False,
    ) -> Bootstrap:
        def guard(parsed: Bootstrap) -> None:
            if require_next_gw and parsed.next_gw() != gw:
                raise GameweekMismatchError(gw, parsed.next_gw())

        return self._load_or_fetch(
            gw,
            "bootstrap",
            self._api.bootstrap,
            Bootstrap.model_validate,
            max_age_hours,
            force,
            guard=guard,
        )

    def fixtures(
        self,
        gw: int,
        *,
        max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
        force: bool = False,
    ) -> tuple[Fixture, ...]:
        return self._load_or_fetch(
            gw,
            "fixtures",
            self._api.fixtures,
            lambda raw: tuple(Fixture.model_validate(f) for f in raw),
            max_age_hours,
            force,
        )

    def entry(
        self,
        gw: int,
        *,
        team_id: int,
        max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
        force: bool = False,
    ) -> EntrySummary:
        return self._load_or_fetch(
            gw,
            f"entry-{team_id}",
            lambda: self._api.entry(team_id),
            EntrySummary.model_validate,
            max_age_hours,
            force,
        )

    def entry_history(
        self,
        gw: int,
        *,
        team_id: int,
        max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
        force: bool = False,
    ) -> EntryHistory:
        return self._load_or_fetch(
            gw,
            f"entry-history-{team_id}",
            lambda: self._api.entry_history(team_id),
            EntryHistory.model_validate,
            max_age_hours,
            force,
        )

    def picks(
        self,
        gw: int,
        *,
        team_id: int,
        event: int,
        max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
        force: bool = False,
    ) -> EventPicks:
        return self._load_or_fetch(
            gw,
            f"picks-{team_id}-e{event}",
            lambda: self._api.event_picks(team_id, event),
            EventPicks.model_validate,
            max_age_hours,
            force,
        )

    def player_summaries(
        self,
        gw: int,
        *,
        player_ids: Sequence[int],
        max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
        force: bool = False,
    ) -> dict[int, ElementSummary]:
        summaries: dict[int, ElementSummary] = {}
        previous_was_fetched = False
        for player_id in _dedupe(player_ids):
            if previous_was_fetched:
                self._sleep(self._throttle_s)
            before = len(self._log.events)
            summaries[player_id] = self._load_or_fetch(
                gw,
                _summary_name(player_id),
                lambda pid=player_id: self._api.element_summary(pid),
                ElementSummary.model_validate,
                max_age_hours,
                force,
            )
            previous_was_fetched = self._log.events[before].fetched
        return summaries

    def shortlist_ids(self, gw: int) -> list[int]:
        bootstrap = self._cached_bootstrap(gw)
        return [p.id for p in bootstrap.elements if is_shortlisted(p)]

    def flag_report(self, gw: int, *, player_ids: Sequence[int]) -> list[Player]:
        """Freshness gate: force-refresh bootstrap, return current flags."""
        bootstrap = self.bootstrap(gw, force=True)
        by_id = bootstrap.player_by_id()
        ids = _dedupe(player_ids)
        unknown = [pid for pid in ids if pid not in by_id]
        if unknown:
            raise ValueError(f"unknown player ids: {unknown}")
        return [by_id[pid] for pid in ids]

    def actuals(
        self, gw: int, *, player_ids: Sequence[int], match_round: int
    ) -> list[ActualLine]:
        """Force-refreshes each summary, then sums every history row for the
        round — a double gameweek contributes two rows."""
        ids = _dedupe(player_ids)
        summaries = self.player_summaries(gw, player_ids=ids, force=True)
        return [
            _aggregate_round(pid, summaries[pid].history, match_round) for pid in ids
        ]

    def export_players_csv(self, gw: int) -> Path:
        rows = PlayerRepository(self._store).query(gw, sort="id")
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(PLAYERS_SLIM_COLUMNS)
        for row in rows:
            writer.writerow(slim_values(row))
        return self._store.save_text(
            gw,
            PLAYERS_SLIM_FILENAME,
            buffer.getvalue(),
            source_url="derived://bootstrap-static/elements",
        )

    def build_prior_season(self, gw: int) -> PriorSeasonResult:
        """Cold-start priors: last-season row per shortlisted player, from
        cached element summaries. Gaps are reported, never silently dropped."""
        bootstrap = self._cached_bootstrap(gw)
        teams = bootstrap.team_by_id()
        players: dict[str, dict[str, Any]] = {}
        no_pl_history: list[int] = []
        missing_summaries: list[int] = []
        for player in bootstrap.elements:
            if not is_shortlisted(player):
                continue
            if not self._store.exists(gw, _summary_name(player.id)):
                missing_summaries.append(player.id)
                continue
            summary = ElementSummary.model_validate(
                self._store.load(gw, _summary_name(player.id))
            )
            if not summary.history_past:
                no_pl_history.append(player.id)
                continue
            # Latest by season name, not by list order: the API's ordering is
            # not a documented guarantee and picking wrong is silent.
            last = max(summary.history_past, key=lambda season: season.season_name)
            players[str(player.id)] = {
                "web_name": player.web_name,
                "team": teams[player.team].short_name,
                "position": player.element_type.name,
                **last.model_dump(),
            }
        payload = {
            "players": players,
            "no_pl_history": no_pl_history,
            "missing_summaries": missing_summaries,
        }
        path = self._store.save(
            gw,
            "prior-season",
            payload,
            source_url="derived://element-summary/history_past",
        )
        return PriorSeasonResult(
            path=path,
            players=len(players),
            no_pl_history=len(no_pl_history),
            missing_summaries=len(missing_summaries),
        )

    def _cached_bootstrap(self, gw: int) -> Bootstrap:
        try:
            raw = self._store.load(gw, "bootstrap")
        except SnapshotMissingError as exc:
            raise exc.with_hint(f"bootstrap --gw {gw}") from None
        return Bootstrap.model_validate(raw)

    def _load_or_fetch(
        self,
        gw: int,
        name: str,
        fetch: Callable[[], Fetched],
        parse: Callable[[Any], Any],
        max_age_hours: float,
        force: bool,
        guard: Callable[[Any], None] | None = None,
    ) -> Any:
        if not force and self._store.exists(gw, name):
            age = self._store.age_hours(gw, name)
            # max_age_hours == inf means "any snapshot will do", including one
            # whose sidecar is missing or unreadable.
            if _is_positive_inf(max_age_hours) or (
                age is not None and age <= max_age_hours
            ):
                parsed = parse(self._store.load(gw, name))
                self._log.events.append(FetchEvent(name, fetched=False, age_hours=age))
                return parsed
        fetched = fetch()
        parsed = parse(fetched.payload)
        if guard is not None:
            guard(parsed)
        self._store.save(gw, name, fetched.payload, fetched.url)
        self._log.events.append(FetchEvent(name, fetched=True))
        return parsed


def _is_positive_inf(value: float) -> bool:
    return math.isinf(value) and value > 0


def _aggregate_round(
    player_id: int, history: Sequence[MatchRecord], match_round: int
) -> ActualLine:
    rows = [row for row in history if row.round == match_round]
    if not rows:
        return ActualLine(player_id=player_id, matched=False)
    return ActualLine(
        player_id=player_id,
        matched=True,
        minutes=sum(row.minutes for row in rows),
        total_points=sum(row.total_points for row in rows),
        goals_scored=sum(row.goals_scored for row in rows),
        assists=sum(row.assists for row in rows),
        bonus=sum(row.bonus or 0 for row in rows),
        bps=sum(row.bps or 0 for row in rows),
    )
