"""The season store: a git-ignored SQLite file derived from data/raw.

`sync` reads every kept raw snapshot (bootstrap, fixtures, event-live,
element summaries; never .archive/ or .meta/), validates each through the
typed models, and rebuilds the derived tables in one transaction whenever a
raw file was added, changed or removed. The rebuild is deterministic, so an
incremental sync and a sync from scratch give the same database. A sync with
nothing new writes nothing.

Per-match rows come from event-live: the round's stats, the fixture each
element played (`explain`), and the side resolved from the fixture's bps
lists or else from the element's club in the bootstraps of gw r and gw r+1.
An element-summary row replaces them only where event-live cannot say: a
double gameweek or an unresolved side. Without one, a double gameweek is
split by minutes and marked, and an unresolved side is stored with no club
and listed.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cached_property
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, TypeAdapter

from fpl.models import (
    Bootstrap,
    EventLive,
    Fixture,
    LiveElement,
    MatchRecord,
    PastSeason,
)
from fpl.store import SnapshotStore

SCHEMA_VERSION = 1
DEFAULT_STORE_PATH = Path("data/store/season-2026-27.sqlite")
XG_RECORDED_FROM = "2022/23"
DC_RECORDED_FROM = "2024/25"

INT_STATS = (
    "minutes", "starts", "total_points", "goals_scored", "assists", "clean_sheets",
    "goals_conceded", "saves", "bonus", "bps", "yellow_cards", "red_cards",
    "own_goals", "penalties_saved", "penalties_missed",
)
FLOAT_STATS = (
    "expected_goals", "expected_assists", "expected_goals_conceded",
    "defensive_contribution",
)
STATS = INT_STATS + FLOAT_STATS
PLAYER_ROUND_COLUMNS = (
    "element", "fixture", "round", "team", "opponent_team", "was_home", "kickoff_time",
    *STATS, "source", "side_rule", "split", "modified", "source_path",
)
PAST_FIELDS = tuple(PastSeason.model_fields)
HISTORY_PAST_COLUMNS = (
    "element", "season_name", "code", *PAST_FIELDS[1:], "xg_recorded", "dc_recorded",
    "source_path",
)
TOTAL_FIELDS = (
    "minutes", "starts", "total_points", "goals_scored", "assists", "clean_sheets",
    "goals_conceded", "saves", "bonus", "bps", "yellow_cards", "red_cards",
    "own_goals", "penalties_saved", "penalties_missed", "defensive_contribution",
    "expected_goals", "expected_assists", "expected_goals_conceded",
)
PLAYER_STATE_COLUMNS = (
    "gw", "element", "fetched_at", "code", "web_name", "team", "position", "now_cost",
    "status", "chance", "news_added", "selected_by_percent", "form", *TOTAL_FIELDS,
)
_X_TOTALS = frozenset({"expected_goals", "expected_assists", "expected_goals_conceded"})

_SCHEMA = f"""
CREATE TABLE manifest (
    path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, kind TEXT NOT NULL, gw INTEGER NOT NULL,
    fetched_at TEXT, final INTEGER NOT NULL, ingested_rows INTEGER NOT NULL
);
CREATE TABLE events (
    id INTEGER PRIMARY KEY, deadline_time TEXT NOT NULL, finished INTEGER NOT NULL,
    data_checked INTEGER NOT NULL, seen_in INTEGER NOT NULL
);
CREATE TABLE clubs (id INTEGER PRIMARY KEY, short_name TEXT NOT NULL, name TEXT NOT NULL);
CREATE TABLE fixtures (
    id INTEGER PRIMARY KEY, event INTEGER, team_h INTEGER NOT NULL, team_a INTEGER NOT NULL,
    kickoff_time TEXT, finished INTEGER NOT NULL, team_h_score INTEGER,
    team_a_score INTEGER, source_gw INTEGER NOT NULL
);
CREATE TABLE player_rounds (
    element INTEGER NOT NULL, fixture INTEGER NOT NULL, round INTEGER NOT NULL,
    team INTEGER, opponent_team INTEGER, was_home INTEGER, kickoff_time TEXT,
    {", ".join(f"{c} INTEGER" for c in INT_STATS)},
    {", ".join(f"{c} REAL" for c in FLOAT_STATS)},
    source TEXT NOT NULL, side_rule TEXT NOT NULL, split TEXT, modified INTEGER NOT NULL,
    source_path TEXT NOT NULL,
    PRIMARY KEY (element, fixture)
);
CREATE TABLE history_past (
    element INTEGER NOT NULL, season_name TEXT NOT NULL, code INTEGER,
    {", ".join(f"{c} {'REAL' if c.startswith(('expected', 'defensive')) else 'INTEGER'}"
               for c in PAST_FIELDS[1:])},
    xg_recorded INTEGER NOT NULL, dc_recorded INTEGER NOT NULL, source_path TEXT NOT NULL,
    PRIMARY KEY (element, season_name)
);
CREATE TABLE player_state (
    gw INTEGER NOT NULL, element INTEGER NOT NULL, fetched_at TEXT, code INTEGER,
    web_name TEXT NOT NULL, team INTEGER NOT NULL, position INTEGER NOT NULL,
    now_cost INTEGER NOT NULL, status TEXT NOT NULL, chance INTEGER, news_added TEXT,
    selected_by_percent REAL NOT NULL, form REAL NOT NULL,
    {", ".join(f"{c} {'REAL' if c in _X_TOTALS or c == 'defensive_contribution' else 'INTEGER'}"
               for c in TOTAL_FIELDS)},
    PRIMARY KEY (gw, element)
);
CREATE TABLE summary_coverage (
    gw INTEGER NOT NULL, element INTEGER NOT NULL, PRIMARY KEY (gw, element)
);
"""
_TABLES = ("manifest", "events", "clubs", "fixtures", "player_rounds", "history_past",
           "player_state", "summary_coverage")

_GW_DIR = re.compile(r"^gw(\d+)$")
_LIVE_FILE = re.compile(r"^event-live-e(\d+)\.json$")
_SUMMARY_FILE = re.compile(r"^summary-(\d+)\.json$")
_FIXTURES = TypeAdapter(tuple[Fixture, ...])


class StoreSyncError(ValueError):
    """The raw tree cannot be ingested as it stands; nothing was written."""


class _SummaryRow(MatchRecord):
    opponent_team: int
    was_home: bool
    kickoff_time: datetime | None = None
    red_cards: int | None = None
    own_goals: int | None = None
    penalties_saved: int | None = None
    penalties_missed: int | None = None
    modified: bool = False


class _PastRow(PastSeason):
    element_code: int | None = None


class _Summary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    history: tuple[_SummaryRow, ...]
    history_past: tuple[_PastRow, ...]


@dataclass(frozen=True)
class UnresolvedSide:
    round: int
    element: int
    fixture: int


@dataclass(frozen=True)
class DgwSplit:
    round: int
    element: int
    fixtures: tuple[int, ...]


@dataclass(frozen=True)
class SyncReport:
    files_ingested: int
    rounds: tuple[int, ...]
    player_rounds: int
    history_past_players: int
    unresolved: tuple[UnresolvedSide, ...]
    dgw_splits: tuple[DgwSplit, ...]
    mismatches: tuple[str, ...]
    reconciliation_skipped: str | None


@dataclass(frozen=True)
class _RawFile:
    path: str
    kind: str
    gw: int
    sha256: str
    fetched_at: datetime | None
    sidecar_final: bool
    content: bytes

    @cached_property
    def payload(self) -> Any:
        """Parsed only when the store is rebuilt; a no-op sync just hashes."""
        return _parse(self.kind, self.path, self.content)


def sync(raw_root: Path, db_path: Path) -> SyncReport:
    files = _scan(raw_root)
    current = {f.path: f.sha256 for f in files}
    known = _known_manifest(db_path)
    ingested = sum(1 for path, sha in current.items() if (known or {}).get(path) != sha)
    if known is None or known != current:
        tables = _build(files)
        _write(db_path, tables)
    con = _connect(db_path)
    try:
        return _report(con, ingested)
    finally:
        con.close()


def rebuild(raw_root: Path, db_path: Path) -> SyncReport:
    db_path.unlink(missing_ok=True)
    return sync(raw_root, db_path)


def _connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path, isolation_level=None)


def _known_manifest(db_path: Path) -> dict[str, str] | None:
    """None when there is no usable store: absent, or another schema version."""
    if not db_path.is_file():
        return None
    con = _connect(db_path)
    try:
        if con.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            return None
        return dict(con.execute("SELECT path, sha256 FROM manifest"))
    finally:
        con.close()


def _scan(raw_root: Path) -> list[_RawFile]:
    store = SnapshotStore(raw_root)
    found: list[_RawFile] = []
    gws = sorted(
        int(m.group(1)) for d in raw_root.iterdir()
        if d.is_dir() and (m := _GW_DIR.match(d.name))
    ) if raw_root.is_dir() else []
    for gw in gws:
        gw_dir = raw_root / f"gw{gw}"
        names: list[tuple[str, str]] = []
        for kind in ("bootstrap", "fixtures"):
            if (gw_dir / f"{kind}.json").is_file():
                names.append((kind, kind))
        lives = sorted(
            (int(m.group(1)), p.stem) for p in gw_dir.glob("event-live-e*.json")
            if (m := _LIVE_FILE.match(p.name))
        )
        names += [("event-live", stem) for _, stem in lives]
        summaries = sorted(
            (int(m.group(1)), p.stem) for p in (gw_dir / "players").glob("summary-*.json")
            if (m := _SUMMARY_FILE.match(p.name))
        )
        names += [("summary", f"players/{stem}") for _, stem in summaries]
        for kind, name in names:
            path = store.path(gw, name)
            content = path.read_bytes()
            found.append(_RawFile(
                path=path.relative_to(raw_root).as_posix(),
                kind=kind,
                gw=gw,
                sha256=hashlib.sha256(content).hexdigest(),
                fetched_at=store.fetched_at(gw, name),
                sidecar_final=store.meta(gw, name)["final"],
                content=content,
            ))
    return found


def _parse(kind: str, path: str, content: bytes) -> Any:
    try:
        raw = json.loads(content)
        if kind == "bootstrap":
            return Bootstrap.model_validate(raw)
        if kind == "fixtures":
            return _FIXTURES.validate_python(raw)
        if kind == "event-live":
            return EventLive.model_validate(raw)
        return _Summary.model_validate(raw)
    except ValueError as exc:
        raise StoreSyncError(f"{path}: not a valid {kind} snapshot: {exc}") from None


@dataclass
class _Tables:
    manifest: list[tuple]
    events: list[tuple]
    clubs: list[tuple]
    fixtures: list[tuple]
    player_rounds: list[tuple]
    history_past: list[tuple]
    player_state: list[tuple]
    summary_coverage: list[tuple]


def _build(files: Sequence[_RawFile]) -> _Tables:
    bootstraps = {f.gw: f for f in files if f.kind == "bootstrap"}
    rows_from: dict[str, int] = {f.path: 0 for f in files}
    final_of: dict[str, bool] = {f.path: f.sidecar_final for f in files}

    def checked_before(event: int, fetched_at: datetime | None) -> bool:
        """A bootstrap fetched at or before `fetched_at` shows the round
        data-checked; data_checked never reverts, so the snapshot came after."""
        if fetched_at is None:
            return False
        return any(
            b.fetched_at is not None and b.fetched_at <= fetched_at
            and any(e.id == event and e.data_checked for e in b.payload.events)
            for b in bootstraps.values()
        )

    fixtures: dict[int, tuple[Fixture, int, str]] = {}
    frozen: set[int] = set()
    for snapshot in (f for f in files if f.kind == "fixtures"):
        for fixture in snapshot.payload:
            if fixture.id not in frozen:
                fixtures[fixture.id] = (fixture, snapshot.gw, snapshot.path)
        for fixture in snapshot.payload:
            if (fixture.finished and fixture.event is not None
                    and checked_before(fixture.event, snapshot.fetched_at)):
                frozen.add(fixture.id)
    for _, _, path in fixtures.values():
        rows_from[path] += 1

    summaries: dict[int, list[_RawFile]] = {}
    for f in files:
        if f.kind == "summary":
            summaries.setdefault(_element_of(f.path), []).append(f)

    lives: dict[int, list[_RawFile]] = {}
    for f in files:
        if f.kind == "event-live":
            lives.setdefault(int(_LIVE_FILE.match(Path(f.path).name).group(1)), []).append(f)

    player_rounds: list[tuple] = []
    for rnd in sorted(lives):
        copies = lives[rnd]
        for copy in copies:
            final_of[copy.path] = copy.sidecar_final or checked_before(rnd, copy.fetched_at)
        chosen = next((c for c in copies if final_of[c.path]), None)
        if chosen is None:
            first = copies[0]
            raise StoreSyncError(
                f"{first.path}: round {rnd} live stats are not final — no final sidecar, "
                f"and no bootstrap fetched before them shows round {rnd} data-checked. "
                f"Refetch: python -m fpl event-live --gw {first.gw} --round {rnd} --force"
            )
        clubs_by_gw = {
            gw: {p.id: p.team for p in bootstraps[gw].payload.elements}
            for gw in (rnd, rnd + 1) if gw in bootstraps
        }
        for element in sorted(chosen.payload.elements, key=lambda e: e.id):
            built = _element_rows(rnd, element, chosen, fixtures, clubs_by_gw,
                                  summaries.get(element.id, []))
            for row in built:
                rows_from[row[-1]] += 1
            player_rounds.extend(built)

    history_past: list[tuple] = []
    for element in sorted(summaries):
        first = summaries[element][0]
        for past in sorted(first.payload.history_past, key=lambda p: p.season_name):
            history_past.append((
                element, past.season_name, past.element_code,
                *(getattr(past, name) for name in PAST_FIELDS[1:]),
                int(past.season_name >= XG_RECORDED_FROM),
                int(past.season_name >= DC_RECORDED_FROM),
                first.path,
            ))
            rows_from[first.path] += 1

    player_state: list[tuple] = []
    for gw in sorted(bootstraps):
        snapshot = bootstraps[gw]
        for p in sorted(snapshot.payload.elements, key=lambda p: p.id):
            player_state.append((
                gw, p.id, _iso(snapshot.fetched_at), p.code, p.web_name, p.team,
                int(p.element_type), p.now_cost, p.status.value,
                p.chance_of_playing_next_round, _iso(p.news_added), p.selected_by_percent,
                p.form, *(getattr(p, name) for name in TOTAL_FIELDS),
            ))
            rows_from[snapshot.path] += 1

    events: list[tuple] = []
    clubs: list[tuple] = []
    if bootstraps:
        latest = bootstraps[max(bootstraps)]
        events = [
            (e.id, _api_time(e.deadline_time), int(e.finished), int(e.data_checked),
             latest.gw)
            for e in sorted(latest.payload.events, key=lambda e: e.id)
        ]
        clubs = [(t.id, t.short_name, t.name)
                 for t in sorted(latest.payload.teams, key=lambda t: t.id)]

    return _Tables(
        manifest=[
            (f.path, f.sha256, f.kind, f.gw, _iso(f.fetched_at), int(final_of[f.path]),
             rows_from[f.path])
            for f in sorted(files, key=lambda f: f.path)
        ],
        events=events,
        clubs=clubs,
        fixtures=[
            (f.id, f.event, f.team_h, f.team_a, _api_time(f.kickoff_time), int(f.finished),
             f.team_h_score, f.team_a_score, gw)
            for f, gw, _ in (fixtures[i] for i in sorted(fixtures))
        ],
        player_rounds=sorted(player_rounds, key=lambda r: (r[0], r[1])),
        history_past=history_past,
        player_state=player_state,
        summary_coverage=sorted((f.gw, _element_of(f.path)) for f in files
                                if f.kind == "summary"),
    )


def _element_rows(
    rnd: int,
    element: LiveElement,
    live: _RawFile,
    fixtures: dict[int, tuple[Fixture, int, str]],
    clubs_by_gw: dict[int, dict[int, int]],
    summaries: Sequence[_RawFile],
) -> list[tuple]:
    fids = list(dict.fromkeys(ex.fixture for ex in element.explain))
    if not fids:
        return []
    unknown = [fid for fid in fids if fid not in fixtures]
    if unknown:
        raise StoreSyncError(
            f"{live.path}: element {element.id} played fixture(s) {unknown}, "
            f"absent from every fixtures snapshot — refetch fixtures"
        )
    matches = sorted((fixtures[fid][0] for fid in fids),
                     key=lambda f: (_api_time(f.kickoff_time) or "", f.id))
    sides = {f.id: _side(element.id, f, clubs_by_gw) for f in matches}
    needs_summary = len(matches) > 1 or any(side is None for side, _ in sides.values())
    if needs_summary:
        covering = _covering_summary(element.id, rnd, matches, summaries)
        if covering is not None:
            return covering
    if len(matches) > 1:
        shares = _split_by_minutes(element, [f.id for f in matches])
        split = "minutes"
    else:
        shares = {matches[0].id: {name: getattr(element.stats, name) for name in STATS}}
        split = None
    rows = []
    for fixture in matches:
        team, rule = sides[fixture.id]
        rows.append(_row(
            element.id, fixture, rnd, team, shares[fixture.id], source="event-live",
            side_rule=rule, split=split, modified=element.modified, source_path=live.path,
        ))
    return rows


def _covering_summary(
    element: int, rnd: int, matches: Sequence[Fixture], summaries: Sequence[_RawFile]
) -> list[tuple] | None:
    """The earliest summary fetched after the round that has a row for every
    fixture the element played in it."""
    for summary in summaries:
        if summary.gw <= rnd:
            continue
        by_fixture = {row.fixture: row for row in summary.payload.history}
        if all(f.id in by_fixture for f in matches):
            return [_summary_row(element, rnd, f, by_fixture[f.id], summary.path)
                    for f in matches]
    return None


def _summary_row(
    element: int, rnd: int, fixture: Fixture, row: _SummaryRow, path: str
) -> tuple:
    team = fixture.team_h if row.was_home else fixture.team_a
    return (
        element, row.fixture, rnd, team, row.opponent_team, int(row.was_home),
        _api_time(row.kickoff_time or fixture.kickoff_time),
        *(getattr(row, name) for name in STATS),
        "summary", "summary", None, int(row.modified), path,
    )


def _side(
    element: int, fixture: Fixture, clubs_by_gw: dict[int, dict[int, int]]
) -> tuple[int | None, str]:
    side = fixture.bps_side(element)
    if side is not None:
        return (fixture.team_h if side == "h" else fixture.team_a), "bps"
    seen = {clubs[element] for clubs in clubs_by_gw.values() if element in clubs}
    candidates = seen & {fixture.team_h, fixture.team_a}
    if len(candidates) == 1:
        return candidates.pop(), "bootstrap"
    return None, "unresolved"


def _row(
    element: int, fixture: Fixture, rnd: int, team: int | None, stats: dict[str, Any], *,
    source: str, side_rule: str, split: str | None, modified: bool, source_path: str,
) -> tuple:
    if team is None:
        opponent, was_home = None, None
    else:
        was_home = int(team == fixture.team_h)
        opponent = fixture.team_a if was_home else fixture.team_h
    return (
        element, fixture.id, rnd, team, opponent, was_home, _api_time(fixture.kickoff_time),
        *(stats[name] for name in STATS), source, side_rule, split, int(modified),
        source_path,
    )


def _split_by_minutes(element: LiveElement, fids: Sequence[int]) -> dict[int, dict[str, Any]]:
    """Per-fixture stats for a double gameweek with no summary. A count is
    taken from `explain` when its per-fixture values add up to the round
    total, else apportioned by minutes (largest remainder, so the parts still
    sum to the total); expected stats are apportioned by minutes."""
    explain = {ex.fixture: ex for ex in element.explain}
    minutes = [int(explain[fid].stat("minutes")) for fid in fids]
    weights = minutes if sum(minutes) > 0 else [1] * len(fids)
    shares: dict[int, dict[str, Any]] = {fid: {} for fid in fids}
    for name in STATS:
        total = getattr(element.stats, name)
        if total is None:
            parts: list[Any] = [None] * len(fids)
        elif name in FLOAT_STATS:
            parts = [total * w / sum(weights) for w in weights]
        else:
            parts = _explained(name, fids, explain, total) or _apportion(total, weights)
        for fid, part in zip(fids, parts):
            shares[fid][name] = part
    return shares


def _explained(name: str, fids: Sequence[int], explain: dict, total: int) -> list[int] | None:
    if name == "total_points":
        parts = [sum(s.points for s in explain[fid].stats) for fid in fids]
    else:
        parts = [int(explain[fid].stat(name)) for fid in fids]
    return parts if sum(parts) == total else None


def _apportion(total: int, weights: Sequence[int]) -> list[int]:
    sign, magnitude = (-1, -total) if total < 0 else (1, total)
    exact = [magnitude * w / sum(weights) for w in weights]
    parts = [int(x) for x in exact]
    by_remainder = sorted(range(len(exact)), key=lambda i: (-(exact[i] - parts[i]), i))
    for i in by_remainder[: magnitude - sum(parts)]:
        parts[i] += 1
    return [sign * p for p in parts]


def _write(db_path: Path, tables: _Tables) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = _connect(db_path)
    try:
        con.execute("BEGIN")
        for table in _TABLES:
            con.execute(f"DROP TABLE IF EXISTS {table}")
        for statement in filter(str.strip, _SCHEMA.split(";")):
            con.execute(statement)
        _insert(con, "manifest", tables.manifest)
        _insert(con, "events", tables.events)
        _insert(con, "clubs", tables.clubs)
        _insert(con, "fixtures", tables.fixtures)
        _insert(con, "player_rounds", tables.player_rounds)
        _insert(con, "history_past", tables.history_past)
        _insert(con, "player_state", tables.player_state)
        _insert(con, "summary_coverage", tables.summary_coverage)
        con.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        con.execute("COMMIT")
    except BaseException:
        if con.in_transaction:
            con.execute("ROLLBACK")
        raise
    finally:
        con.close()


def _insert(con: sqlite3.Connection, table: str, rows: Iterable[tuple]) -> None:
    rows = list(rows)
    if rows:
        marks = ", ".join("?" * len(rows[0]))
        con.executemany(f"INSERT INTO {table} VALUES ({marks})", rows)


def _report(con: sqlite3.Connection, ingested: int) -> SyncReport:
    rounds = tuple(r for (r,) in con.execute(
        "SELECT DISTINCT round FROM player_rounds ORDER BY round"))
    unresolved = tuple(UnresolvedSide(*r) for r in con.execute(
        "SELECT round, element, fixture FROM player_rounds "
        "WHERE side_rule = 'unresolved' ORDER BY round, element, fixture"))
    splits: dict[tuple[int, int], list[int]] = {}
    for rnd, element, fixture in con.execute(
        "SELECT round, element, fixture FROM player_rounds WHERE split = 'minutes' "
        "ORDER BY round, element, kickoff_time, fixture"
    ):
        splits.setdefault((rnd, element), []).append(fixture)
    mismatches, skipped = _reconcile(con, rounds)
    return SyncReport(
        files_ingested=ingested,
        rounds=rounds,
        player_rounds=con.execute("SELECT COUNT(*) FROM player_rounds").fetchone()[0],
        history_past_players=con.execute(
            "SELECT COUNT(DISTINCT element) FROM history_past").fetchone()[0],
        unresolved=unresolved,
        dgw_splits=tuple(DgwSplit(r, e, tuple(f)) for (r, e), f in splits.items()),
        mismatches=mismatches,
        reconciliation_skipped=skipped,
    )


def _reconcile(
    con: sqlite3.Connection, rounds: tuple[int, ...]
) -> tuple[tuple[str, ...], str | None]:
    """The latest bootstrap's season totals against the sum of the stored
    rounds, once the round current at its fetch is data-checked."""
    latest = con.execute("SELECT MAX(gw) FROM player_state").fetchone()[0]
    if latest is None:
        return (), "no bootstrap ingested"
    fetched_at = con.execute(
        "SELECT fetched_at FROM player_state WHERE gw = ? LIMIT 1", (latest,)
    ).fetchone()[0]
    if fetched_at is None:
        return (), f"bootstrap gw{latest} has no recorded fetch time"
    fetched = datetime.fromisoformat(fetched_at)
    current = next(
        (row[0::2] for row in con.execute(
            "SELECT id, deadline_time, data_checked FROM events ORDER BY id DESC")
         if datetime.fromisoformat(row[1]) <= fetched),
        None,
    )
    if current is None:
        return (), f"no event had started when bootstrap gw{latest} was fetched"
    event, checked = current
    if not checked:
        return (), f"event {event} not data-checked in bootstrap gw{latest}"
    missing = sorted(set(range(1, event + 1)) - set(rounds))
    if missing:
        return (), f"no final live stats for round(s) {missing}"
    sums = ", ".join(f"SUM({name})" for name in TOTAL_FIELDS)
    summed = {
        row[0]: row[1:] for row in con.execute(
            f"SELECT element, {sums} FROM player_rounds WHERE round <= ? GROUP BY element",
            (event,),
        )
    }
    lines = []
    columns = ", ".join(TOTAL_FIELDS)
    for element, *totals in con.execute(
        f"SELECT element, {columns} FROM player_state WHERE gw = ? ORDER BY element",
        (latest,),
    ):
        stored = summed.get(element, (None,) * len(TOTAL_FIELDS))
        for name, total, rounds_sum in zip(TOTAL_FIELDS, totals, stored):
            if total is None:
                continue
            if name in _X_TOTALS:
                differs = round(total, 2) != round(rounds_sum or 0.0, 2)
            else:
                differs = total != (rounds_sum or 0)
            if differs:
                lines.append(
                    f"element {element}: {name} bootstrap gw{latest} {total} "
                    f"≠ rounds 1-{event} {rounds_sum or 0}"
                )
    return tuple(lines), None


def _element_of(path: str) -> int:
    return int(_SUMMARY_FILE.match(Path(path).name).group(1))


def _api_time(value: datetime | None) -> str | None:
    """The API's own spelling, so stored times compare equal to raw rows."""
    if value is None:
        return None
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()
