"""Fetch-if-stale orchestration: the one place deciding when the network is
touched. Payloads are validated BEFORE persisting — an invalid response is
never written to disk. Analysts consume only what this service has saved.
"""

from __future__ import annotations

import csv
import time
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from fpl.api import Fetched, FplApi
from fpl.models import (
    Bootstrap,
    ElementSummary,
    EntrySummary,
    Fixture,
    Player,
    is_shortlisted,
)
from fpl.repository import PLAYERS_SLIM_COLUMNS, PlayerRepository, slim_values
from fpl.store import SnapshotStore, utcnow

DEFAULT_MAX_AGE_HOURS = 24.0


def _summary_name(player_id: int) -> str:
    return f"players/summary-{player_id}"


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

    def bootstrap(
        self, gw: int, max_age_hours: float = DEFAULT_MAX_AGE_HOURS, force: bool = False
    ) -> Bootstrap:
        parsed, _ = self._load_or_fetch(
            gw, "bootstrap", self._api.bootstrap, Bootstrap.model_validate,
            max_age_hours, force,
        )
        return parsed

    def fixtures(
        self, gw: int, max_age_hours: float = DEFAULT_MAX_AGE_HOURS, force: bool = False
    ) -> tuple[Fixture, ...]:
        parsed, _ = self._load_or_fetch(
            gw, "fixtures", self._api.fixtures,
            lambda raw: tuple(Fixture.model_validate(f) for f in raw),
            max_age_hours, force,
        )
        return parsed

    def entry(
        self,
        gw: int,
        team_id: int,
        max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
        force: bool = False,
    ) -> EntrySummary:
        parsed, _ = self._load_or_fetch(
            gw, f"entry-{team_id}", lambda: self._api.entry(team_id),
            EntrySummary.model_validate, max_age_hours, force,
        )
        return parsed

    def player_summaries(
        self,
        gw: int,
        player_ids: Sequence[int],
        max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
        force: bool = False,
    ) -> dict[int, ElementSummary]:
        summaries: dict[int, ElementSummary] = {}
        previous_was_fetched = False
        for player_id in player_ids:
            if previous_was_fetched:
                self._sleep(self._throttle_s)
            summaries[player_id], previous_was_fetched = self._load_or_fetch(
                gw,
                _summary_name(player_id),
                lambda pid=player_id: self._api.element_summary(pid),
                ElementSummary.model_validate,
                max_age_hours,
                force,
            )
        return summaries

    def shortlist_ids(self, gw: int) -> list[int]:
        bootstrap = self._cached_bootstrap(gw)
        return [p.id for p in bootstrap.elements if is_shortlisted(p)]

    def flag_report(self, gw: int, player_ids: Sequence[int]) -> list[Player]:
        """Freshness gate: force-refresh bootstrap, return current flags."""
        bootstrap = self.bootstrap(gw, force=True)
        by_id = bootstrap.player_by_id()
        unknown = [pid for pid in player_ids if pid not in by_id]
        if unknown:
            raise ValueError(f"unknown player ids: {unknown}")
        return [by_id[pid] for pid in player_ids]

    def export_players_csv(self, gw: int) -> Path:
        rows = PlayerRepository(self._store).query(gw, sort="id")
        path = self._store.dir(gw) / "players-slim.csv"
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(PLAYERS_SLIM_COLUMNS)
            for row in rows:
                writer.writerow(slim_values(row))
        return path

    def build_prior_season(self, gw: int) -> Path:
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
            last = summary.history_past[-1]
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
        return self._store.save(
            gw, "prior-season", payload,
            source_url="derived://element-summary/history_past",
        )

    def _cached_bootstrap(self, gw: int) -> Bootstrap:
        return Bootstrap.model_validate(self._store.load(gw, "bootstrap"))

    def _load_or_fetch(
        self,
        gw: int,
        name: str,
        fetch: Callable[[], Fetched],
        parse: Callable[[Any], Any],
        max_age_hours: float,
        force: bool,
    ) -> tuple[Any, bool]:
        if not force:
            age = self._store.age_hours(gw, name)
            if age is not None and age <= max_age_hours:
                return parse(self._store.load(gw, name)), False
        fetched = fetch()
        parsed = parse(fetched.payload)
        self._store.save(gw, name, fetched.payload, fetched.url)
        return parsed, True
