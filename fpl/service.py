"""Fetch-if-stale orchestration: the one place deciding when the network is
touched. Payloads are validated BEFORE persisting — an invalid response is
never written to disk. Analysts consume only what this service has saved.
"""

from __future__ import annotations

import csv
import io
import json
import math
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from fpl.api import Fetched, FplApi
from fpl.freshness import BASELINE_MAX_AGE_HOURS, FlagChange, flag_delta
from fpl.models import (
    Bootstrap,
    ElementSummary,
    EntryHistory,
    EntrySummary,
    EventLive,
    EventPicks,
    Fixture,
    LiveStats,
    Player,
    is_shortlisted,
)
from fpl.repository import PLAYERS_SLIM_COLUMNS, PlayerRepository, slim_values
from fpl.store import (
    ARCHIVE_STAMP_FORMAT,
    SnapshotMissingError,
    SnapshotStore,
    utcnow,
)

DEFAULT_MAX_AGE_HOURS = 24.0
PLAYERS_SLIM_FILENAME = "players-slim.csv"


def _summary_name(player_id: int) -> str:
    return f"players/summary-{player_id}"


def load_cached_bootstrap(store: SnapshotStore, gw: int) -> Bootstrap:
    try:
        raw = store.load(gw, "bootstrap")
    except SnapshotMissingError as exc:
        raise exc.with_hint(f"bootstrap --gw {gw}") from None
    return Bootstrap.model_validate(raw)


def load_cached_summaries(
    store: SnapshotStore, gw: int, player_ids: Iterable[int]
) -> dict[int, ElementSummary]:
    """Cached element summaries only — ids without a snapshot are simply
    absent, so callers can report them rather than fetch."""
    summaries: dict[int, ElementSummary] = {}
    for player_id in _dedupe(player_ids):
        name = _summary_name(player_id)
        if store.exists(gw, name):
            summaries[player_id] = ElementSummary.model_validate(store.load(gw, name))
    return summaries


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


class PostDeadlineError(ValueError):
    def __init__(self, gw: int, deadline: datetime) -> None:
        super().__init__(
            f"gw{gw} deadline ({deadline.isoformat()}) has passed — its snapshots "
            f"are the record of that gameweek and are not refetched"
        )
        self.gw = gw
        self.deadline = deadline


@dataclass(frozen=True)
class FetchEvent:
    """One snapshot access: whether the network was touched, the age of the
    snapshot served from cache, and whether that snapshot is final."""

    name: str
    fetched: bool
    age_hours: float | None = None
    final: bool = False


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
    expected_goals: float = 0.0
    expected_assists: float = 0.0
    defensive_contribution: float = 0.0


@dataclass(frozen=True)
class FlagBaseline:
    bootstrap: Bootstrap
    source: str
    fetched_at: datetime | None


@dataclass
class FlagCheck:
    """baseline None means no delta could be computed — the gate cannot
    pass on it."""

    players: list[Player]
    refreshed_at: datetime | None
    baseline: FlagBaseline | None = None
    gate_ids: list[int] = field(default_factory=list)
    gate: list[FlagChange] = field(default_factory=list)
    pool: list[FlagChange] = field(default_factory=list)
    delta_path: Path | None = None

    @property
    def baseline_age_hours(self) -> float | None:
        """Hours between the baseline fetch and this refresh; None when either
        instant is unknown (an explicit --baseline file carries none)."""
        if self.baseline is None or self.baseline.fetched_at is None:
            return None
        if self.refreshed_at is None:
            return None
        return (self.refreshed_at - self.baseline.fetched_at).total_seconds() / 3600

    @property
    def stale(self) -> bool:
        age = self.baseline_age_hours
        return age is not None and age > BASELINE_MAX_AGE_HOURS

    def to_document(self, gw: int) -> dict[str, Any]:
        if self.baseline is None:
            raise ValueError("no baseline: there is no delta to serialise")
        fetched_at = self.baseline.fetched_at
        return {
            "gw": gw,
            "refreshed_at": self.refreshed_at.isoformat() if self.refreshed_at else None,
            "baseline": {
                "source": self.baseline.source,
                "fetched_at": fetched_at.isoformat() if fetched_at else None,
                "age_hours": self.baseline_age_hours,
                "stale": self.stale,
            },
            "gate_ids": self.gate_ids,
            "gate_changed": bool(self.gate),
            "gate": [c.to_document() for c in self.gate],
            "pool": [c.to_document() for c in self.pool],
        }


@dataclass
class _Log:
    events: list[FetchEvent] = field(default_factory=list)


class FplDataService:
    def __init__(
        self,
        api: FplApi,
        store: SnapshotStore,
        now: Callable[[], datetime] = utcnow,
        throttle_s: float = 0.1,
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
        allow_post_deadline: bool = False,
    ) -> Bootstrap:
        # The deadline is read from the fresh payload, not the cached one: a
        # postponed deadline is only learned by refetching.
        def guard(parsed: Bootstrap) -> None:
            if require_next_gw and parsed.next_gw() != gw:
                raise GameweekMismatchError(gw, parsed.next_gw())
            deadline = parsed.deadline_for(gw)
            if allow_post_deadline or deadline is None:
                return
            if self._now() >= deadline:
                raise PostDeadlineError(gw, deadline)

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
        allow_post_deadline: bool = False,
    ) -> tuple[Fixture, ...]:
        return self._load_or_fetch(
            gw,
            "fixtures",
            self._api.fixtures,
            lambda raw: tuple(Fixture.model_validate(f) for f in raw),
            max_age_hours,
            force,
            before_fetch=None if allow_post_deadline else self._deadline_guard(gw),
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
            final_when=lambda _: self._round_settled(gw, event),
        )

    def event_live(
        self,
        gw: int,
        *,
        event: int,
        max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
        force: bool = False,
    ) -> EventLive:
        """One round's live stats, only once the round is data-checked. Every
        snapshot fetched here is final (see data_checked_basis)."""
        basis = self.data_checked_basis(gw, event)
        name = f"event-live-e{event}"
        # The round is data-checked, so a cached snapshot that is not final
        # (fetched before the check, or without a sidecar verdict) is replaced
        # by a final one at any age, never served.
        stale = self._store.exists(gw, name) and not self._store.is_final(gw, name)
        return self._load_or_fetch(
            gw,
            name,
            lambda: self._api.event_live(event),
            EventLive.model_validate,
            max_age_hours,
            force or stale,
            final_when=lambda _: (True, basis),
        )

    def data_checked_basis(self, gw: int, event: int) -> str:
        """Why a live snapshot of `event` fetched now is final: the cached gw
        bootstrap, fetched before it, shows the round data-checked, and
        data_checked never reverts. Refuses while it does not."""
        bootstrap = self._cached_bootstrap(gw)
        checked = next((e for e in bootstrap.events if e.id == event), None)
        if checked is None:
            raise ValueError(f"cached bootstrap has no event {event}")
        if not checked.data_checked:
            raise ValueError(
                f"round {event} is not data-checked yet — bonus points are not "
                f"final. Refetch once FPL marks it checked: "
                f"python -m fpl bootstrap --gw {gw} --force"
            )
        return f"{self._bootstrap_label(gw)} shows event {event} data_checked"

    def _bootstrap_label(self, gw: int) -> str:
        fetched_at = self._store.fetched_at(gw, "bootstrap")
        when = fetched_at.isoformat() if fetched_at else "at an unknown time"
        return f"bootstrap gw{gw} fetched {when}"

    def player_summaries(
        self,
        gw: int,
        *,
        player_ids: Sequence[int],
        max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
        force: bool = False,
        allow_post_deadline: bool = False,
    ) -> dict[int, ElementSummary]:
        summaries: dict[int, ElementSummary] = {}
        previous_was_fetched = False
        guard = None if allow_post_deadline else self._deadline_guard(gw)
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
                before_fetch=guard,
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

    def flag_check(
        self, gw: int, *, player_ids: Sequence[int], baseline_path: Path | None = None
    ) -> FlagCheck:
        """flag_report plus the delta against a baseline: baseline_path when
        given, else the cached bootstrap as it stood just before this refresh
        (the snapshot the latest analysis read). The delta is persisted as
        flags-delta-<refresh stamp>.json beside the bootstrap."""
        baseline = self._flag_baseline(gw, baseline_path)
        players = self.flag_report(gw, player_ids=player_ids)
        refreshed = self._cached_bootstrap(gw)
        refreshed_at = self._store.fetched_at(gw, "bootstrap")
        if baseline is None:
            return FlagCheck(players=players, refreshed_at=refreshed_at)
        gate_ids = _dedupe(player_ids)
        check = FlagCheck(
            players=players,
            refreshed_at=refreshed_at,
            baseline=baseline,
            gate_ids=gate_ids,
            gate=flag_delta(baseline.bootstrap.elements, refreshed.elements, set(gate_ids)),
            pool=flag_delta(baseline.bootstrap.elements, refreshed.elements),
        )
        stamp = (refreshed_at or self._now()).strftime(ARCHIVE_STAMP_FORMAT)
        check.delta_path = self._store.save(
            gw, f"flags-delta-{stamp}", check.to_document(gw), "derived://flags-delta"
        )
        return check

    def _flag_baseline(self, gw: int, baseline_path: Path | None) -> FlagBaseline | None:
        if baseline_path is not None:
            raw = json.loads(baseline_path.read_text(encoding="utf-8"))
            return FlagBaseline(Bootstrap.model_validate(raw), str(baseline_path), None)
        if not self._store.exists(gw, "bootstrap"):
            return None
        archived = self._store.archive_path(gw, "bootstrap")
        return FlagBaseline(
            self._cached_bootstrap(gw),
            str(archived or self._store.path(gw, "bootstrap")),
            self._store.fetched_at(gw, "bootstrap"),
        )

    def actuals(
        self, gw: int, *, player_ids: Sequence[int], match_round: int
    ) -> list[ActualLine]:
        """Reads the round's final event-live snapshot, from gw or else the gw
        after the round; never fetches. Live stats arrive already summed over
        a double gameweek."""
        name = f"event-live-e{match_round}"
        source = next(
            (g for g in _dedupe([gw, match_round + 1]) if self._store.is_final(g, name)),
            None,
        )
        if source is None:
            force = " --force" if self._store.exists(gw, name) else ""
            raise ValueError(
                f"no final event-live snapshot of round {match_round} in gw{gw} or "
                f"gw{match_round + 1} — fetch it first: "
                f"python -m fpl event-live --gw {gw} --round {match_round}{force}"
            )
        stats = EventLive.model_validate(self._store.load(source, name)).by_id()
        return [_actual_line(pid, stats.get(pid)) for pid in _dedupe(player_ids)]

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
        return load_cached_bootstrap(self._store, gw)

    def _readable_cached_bootstrap(self, gw: int) -> Bootstrap | None:
        """The cached bootstrap, or None when it is missing or unreadable —
        a corrupt snapshot must not block the refetch that replaces it."""
        if not self._store.exists(gw, "bootstrap"):
            return None
        try:
            return self._cached_bootstrap(gw)
        except ValueError:
            return None

    def _cached_deadline(self, gw: int, event: int) -> datetime | None:
        bootstrap = self._readable_cached_bootstrap(gw)
        return None if bootstrap is None else bootstrap.deadline_for(event)

    def _round_settled(self, gw: int, event: int) -> tuple[bool, str]:
        """Picks for an event keep changing (automatic subs, multipliers,
        entry_history) until the round is processed, so they are final only
        once the cached gw bootstrap shows the event finished and data-checked."""
        bootstrap = self._readable_cached_bootstrap(gw)
        if bootstrap is None:
            return False, (
                f"no readable cached gw{gw} bootstrap shows event {event} data_checked"
            )
        settled = next((e for e in bootstrap.events if e.id == event), None)
        if settled is not None and settled.finished and settled.data_checked:
            return True, self.data_checked_basis(gw, event)
        return False, (
            f"event {event} not finished/data_checked in {self._bootstrap_label(gw)}"
        )

    def _deadline_guard(self, gw: int) -> Callable[[], None]:
        """Refuses a fetch into gw{gw} once its deadline has passed: that
        directory is the record of what the gameweek's analysis read. The
        deadline is looked up once, on the first fetch, so a run serving
        every snapshot from cache never parses the bootstrap."""
        checked = False

        def guard() -> None:
            nonlocal checked
            if checked:
                return
            deadline = self._cached_deadline(gw, gw)
            if deadline is not None and self._now() >= deadline:
                raise PostDeadlineError(gw, deadline)
            checked = True

        return guard

    def _load_or_fetch(
        self,
        gw: int,
        name: str,
        fetch: Callable[[], Fetched],
        parse: Callable[[Any], Any],
        max_age_hours: float,
        force: bool,
        guard: Callable[[Any], None] | None = None,
        final_when: Callable[[Any], tuple[bool, str | None]] | None = None,
        before_fetch: Callable[[], None] | None = None,
    ) -> Any:
        if not force and self._store.exists(gw, name):
            age = self._store.age_hours(gw, name)
            final = self._store.is_final(gw, name)
            # max_age_hours == inf means "any snapshot will do", including one
            # whose sidecar is missing or unreadable. A final snapshot can no
            # longer change, so it is served at any age.
            if final or _is_positive_inf(max_age_hours) or (
                age is not None and age <= max_age_hours
            ):
                parsed = parse(self._store.load(gw, name))
                self._log.events.append(
                    FetchEvent(name, fetched=False, age_hours=age, final=final)
                )
                return parsed
        if before_fetch is not None:
            before_fetch()
        fetched = fetch()
        parsed = parse(fetched.payload)
        if guard is not None:
            guard(parsed)
        # final_when explains its verdict either way: the basis of a final
        # snapshot, or the reason a snapshot is not final yet.
        final, why = final_when(parsed) if final_when is not None else (False, None)
        self._store.save(
            gw, name, fetched.payload, fetched.url, final=final,
            basis=why if final else None, reason=None if final else why,
        )
        self._log.events.append(FetchEvent(name, fetched=True, final=final))
        return parsed


def _is_positive_inf(value: float) -> bool:
    return math.isinf(value) and value > 0


def _actual_line(player_id: int, stats: LiveStats | None) -> ActualLine:
    if stats is None:
        return ActualLine(player_id=player_id, matched=False)
    return ActualLine(
        player_id=player_id,
        matched=True,
        minutes=stats.minutes,
        total_points=stats.total_points,
        goals_scored=stats.goals_scored,
        assists=stats.assists,
        bonus=stats.bonus,
        bps=stats.bps,
        expected_goals=round(stats.expected_goals or 0.0, 2),
        expected_assists=round(stats.expected_assists or 0.0, 2),
        defensive_contribution=stats.defensive_contribution or 0.0,
    )
