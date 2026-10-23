"""The season store: a git-ignored SQLite file derived from data/raw.

`sync` reads every kept raw snapshot (bootstrap, fixtures, event-live,
element summaries; never .archive/ or .meta/), validates each through the
typed models, and rebuilds the derived tables whenever a raw file was added,
changed or removed, or its sidecar's fetch time or finality changed. The
rebuild is deterministic, so an incremental sync and a sync from scratch give
the same database. It is written to a temporary file beside the store and
moved over it only once complete, so a refused or failed sync leaves the
previous store as it was. A sync with nothing new writes nothing.

Per-match rows come from event-live: the round's stats, the fixture each
element played (`explain`), and the side resolved from the fixture's bps
lists or else from the element's club in the bootstraps of gw r and gw r+1.
An element-summary row replaces them only where event-live cannot say: a
double gameweek or an unresolved side. Without one, a double gameweek is
split by minutes and marked, and an unresolved side is stored with no club
and listed.

A round's live stats are stored only from a final event-live snapshot, by
the one rule in `fpl.store.prove_live_final`, applied to the kept bootstraps
the sync reads.

`open_ro` serves as-of reads that return the existing models. It refuses a
store that has not ingested exactly the current raw tree; `open_synced`, which
the CLI readers use, syncs such a store first and says so in one line. A sync
holds a lock file beside the store, so two processes never build it at once.
Every input to the finality rule (each sidecar's fetch time and `final` key,
each bootstrap's content) is in the manifest it compares, so a store it opens
agrees with `fpl.store.live_final` on the current tree.

A sync also writes a scan cache beside the store: the size, mtime, inode and
ctime of each raw file and sidecar it hashed, tied to that store's manifest.
`open_ro` and `status` re-read only the files whose stat differs from it; `sync`
and `verify` always hash every file. The cache is outside the database, so
the database stays a pure function of the raw tree.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, TypeAdapter

from fpl.models import (
    Bootstrap,
    ElementSummary,
    EventLive,
    Fixture,
    LiveElement,
    MatchRecord,
    PastSeason,
    PlayerStatus,
    Position,
    is_shortlisted,
)
from fpl.service import load_cached_summaries
from fpl.store import SeenBootstrap, SnapshotStore, prove_live_final

SCHEMA_VERSION = 3
STORE_FILENAME = "season-2026-27.sqlite"
DEFAULT_RAW_ROOT = Path("data/raw")


def default_store_path(raw_root: Path) -> Path:
    """The store beside the raw tree it is derived from: data/store for
    data/raw. A run over another raw tree never touches the repo's store."""
    return raw_root.parent / "store" / STORE_FILENAME


DEFAULT_STORE_PATH = default_store_path(DEFAULT_RAW_ROOT)
SCAN_CACHE_SUFFIX = ".scan.json"
LOCK_SUFFIX = ".lock"
MAX_AUTO_SYNCS = 2
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
    "status", "chance", "news_added", "selected_by_percent", "form", "shortlisted",
    *TOTAL_FIELDS,
)
FIXTURE_SNAPSHOT_COLUMNS = (
    "gw", "id", "event", "team_h", "team_a", "team_h_difficulty", "team_a_difficulty",
    "kickoff_time", "finished", "team_h_score", "team_a_score",
)
_X_TOTALS = frozenset({"expected_goals", "expected_assists", "expected_goals_conceded"})

_SCHEMA = f"""
CREATE TABLE manifest (
    path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, kind TEXT NOT NULL, gw INTEGER NOT NULL,
    fetched_at TEXT, final INTEGER NOT NULL, sidecar_final INTEGER NOT NULL,
    ingested_rows INTEGER NOT NULL
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
CREATE TABLE fixture_snapshots (
    gw INTEGER NOT NULL, id INTEGER NOT NULL, event INTEGER, team_h INTEGER NOT NULL,
    team_a INTEGER NOT NULL, team_h_difficulty INTEGER NOT NULL,
    team_a_difficulty INTEGER NOT NULL, kickoff_time TEXT, finished INTEGER NOT NULL,
    team_h_score INTEGER, team_a_score INTEGER,
    PRIMARY KEY (gw, id)
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
    selected_by_percent REAL NOT NULL, form REAL NOT NULL, shortlisted INTEGER NOT NULL,
    {", ".join(f"{c} {'REAL' if c in _X_TOTALS or c == 'defensive_contribution' else 'INTEGER'}"
               for c in TOTAL_FIELDS)},
    PRIMARY KEY (gw, element)
);
CREATE TABLE summary_coverage (
    gw INTEGER NOT NULL, element INTEGER NOT NULL, PRIMARY KEY (gw, element)
);
"""

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
    files_total: int
    rebuilt: bool
    rounds: tuple[int, ...]
    player_rounds: int
    history_past_players: int
    unresolved: tuple[UnresolvedSide, ...]
    dgw_splits: tuple[DgwSplit, ...]
    mismatches: tuple[str, ...]
    reconciliation_skipped: str | None


ChangeKey = tuple[str, str | None, bool]
FileStat = tuple[int, int, int, int]
Stat = tuple[FileStat, FileStat | None]


@dataclass(frozen=True)
class _RawFile:
    """A raw file as scanned: its hash and sidecar, not its content. The
    content is re-read when the store is rebuilt, so a sync holds at most a
    few parsed snapshots at a time."""

    path: str
    source: Path
    raw_root: Path
    kind: str
    gw: int
    sha256: str
    fetched_at: datetime | None
    sidecar_final: bool
    stat: Stat

    @property
    def key(self) -> ChangeKey:
        """What a sync compares: the content and the sidecar keys it uses."""
        return self.sha256, _iso(self.fetched_at), self.sidecar_final

    def load(self) -> Any:
        content = self.source.read_bytes()
        if hashlib.sha256(content).hexdigest() != self.sha256:
            raise StoreSyncError(f"{self.path}: changed during the sync — run the sync again")
        return _parse(self.kind, self.path, content)


def sync(raw_root: Path, db_path: Path) -> SyncReport:
    with sync_lock(db_path):
        return _sync(raw_root, db_path, force=False)


def rebuild(raw_root: Path, db_path: Path) -> SyncReport:
    with sync_lock(db_path):
        return _sync(raw_root, db_path, force=True)


@contextlib.contextmanager
def sync_lock(db_path: Path) -> Iterator[None]:
    """Held while the store is built. The store itself is replaced
    atomically, so readers need no lock; the lock stops two syncs from
    building it at once."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with open(db_path.with_name(db_path.name + LOCK_SUFFIX), "a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _sync(raw_root: Path, db_path: Path, *, force: bool) -> SyncReport:
    files = _scan(raw_root)
    current = {f.path: f.key for f in files}
    known = None if force else _known_manifest(db_path)
    ingested = sum(1 for path, key in current.items() if (known or {}).get(path) != key)
    rebuilt = known is None or known != current
    if rebuilt:
        _write(db_path, _build(files))
    _write_scan_cache(db_path, files)
    con = _connect(db_path)
    try:
        return _report(con, ingested, len(files), rebuilt)
    finally:
        con.close()


def _connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path, isolation_level=None)


def _known_manifest(db_path: Path) -> dict[str, ChangeKey] | None:
    """None when there is no usable store: absent, unreadable, or another
    schema version."""
    if not db_path.is_file():
        return None
    con = _connect(db_path)
    try:
        if con.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            return None
        return _manifest_keys(con)
    except sqlite3.DatabaseError:
        return None
    finally:
        con.close()


def _manifest_keys(con: sqlite3.Connection) -> dict[str, ChangeKey]:
    return {
        path: (sha256, fetched_at, bool(sidecar_final))
        for path, sha256, fetched_at, sidecar_final in con.execute(
            "SELECT path, sha256, fetched_at, sidecar_final FROM manifest")
    }


def _scan(
    raw_root: Path, trusted: dict[str, tuple[Stat, ChangeKey]] | None = None
) -> list[_RawFile]:
    """Every kept raw file with its change key. A file whose stat, and its
    sidecar's, equal a `trusted` entry takes that entry's key unread."""
    store = SnapshotStore(raw_root)
    trusted = trusted or {}
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
            relative = path.relative_to(raw_root).as_posix()
            # Stat before reading: a write during the read leaves a newer mtime,
            # so the next open re-reads the file instead of trusting this key.
            stat = _stat(path, store.meta_path(gw, name))
            known = trusted.get(relative)
            if known is not None and known[0] == stat:
                sha256, fetched_iso, sidecar_final = known[1]
                fetched_at = None if fetched_iso is None else datetime.fromisoformat(fetched_iso)
            else:
                sha256 = _digest(path)
                fetched_at = store.fetched_at(gw, name)
                sidecar_final = store.meta(gw, name)["final"]
            found.append(_RawFile(
                path=relative,
                source=path,
                raw_root=raw_root,
                kind=kind,
                gw=gw,
                sha256=sha256,
                fetched_at=fetched_at,
                sidecar_final=sidecar_final,
                stat=stat,
            ))
    return found


def _digest(path: Path) -> str:
    with path.open("rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def _stat(path: Path, meta_path: Path) -> Stat:
    data = path.stat()
    try:
        meta = meta_path.stat()
    except FileNotFoundError:
        return _fingerprint(data), None
    return _fingerprint(data), _fingerprint(meta)


def _fingerprint(st: os.stat_result) -> FileStat:
    # The inode and ctime catch what size and mtime miss: a rewrite whose mtime
    # was set back, or a tree copied with its mtimes (cp -p, rsync -a, tar).
    # Neither can be set from user space.
    return st.st_size, st.st_mtime_ns, st.st_ino, st.st_ctime_ns


def _cache_path(db_path: Path) -> Path:
    return db_path.with_name(db_path.name + SCAN_CACHE_SUFFIX)


def _manifest_digest(keys: dict[str, ChangeKey]) -> str:
    return hashlib.sha256(json.dumps(sorted(keys.items())).encode()).hexdigest()


def _write_scan_cache(db_path: Path, files: Sequence[_RawFile]) -> None:
    """Skipped when the cache already says the same, so a sync with nothing
    new writes nothing at all."""
    document = json.dumps({
        "manifest": _manifest_digest({f.path: f.key for f in files}),
        "files": {f.path: list(f.stat) for f in sorted(files, key=lambda f: f.path)},
    }, indent=0)
    path = _cache_path(db_path)
    try:
        if path.read_text(encoding="utf-8") == document:
            return
    except OSError:
        pass
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(document)
    os.replace(name, path)


def _trusted(db_path: Path, known: dict[str, ChangeKey]) -> dict[str, tuple[Stat, ChangeKey]]:
    """The scan cache's stats, only when it was written for exactly this
    store's manifest; otherwise nothing is trusted and every file is read."""
    try:
        document = json.loads(_cache_path(db_path).read_text(encoding="utf-8"))
        if document["manifest"] != _manifest_digest(known):
            return {}
        return {path: ((tuple(data), None if meta is None else tuple(meta)), known[path])
                for path, (data, meta) in document["files"].items() if path in known}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return {}


def _parse(kind: str, path: str, content: bytes) -> Any:
    try:
        if kind == "summary":
            return _Summary.model_validate_json(content)
        raw = json.loads(content)
        if kind == "bootstrap":
            return Bootstrap.model_validate(raw)
        if kind == "fixtures":
            return _FIXTURES.validate_python(raw)
        return EventLive.model_validate(raw)
    except ValueError as exc:
        raise StoreSyncError(f"{path}: not a valid {kind} snapshot: {exc}") from None


@dataclass
class _Tables:
    manifest: list[tuple]
    events: list[tuple]
    clubs: list[tuple]
    fixtures: list[tuple]
    fixture_snapshots: list[tuple]
    player_rounds: list[tuple]
    history_past: list[tuple]
    player_state: list[tuple]
    summary_coverage: list[tuple]


def _build(files: Sequence[_RawFile]) -> _Tables:
    """Every file is validated; each is parsed once (a covering summary once
    more) and released before the next, keeping only the rows it yields."""
    rows_from: dict[str, int] = {f.path: 0 for f in files}
    final_of: dict[str, bool] = {f.path: f.sidecar_final for f in files}

    first_checked: dict[int, datetime] = {}
    clubs_of: dict[int, dict[int, int]] = {}
    player_state: list[tuple] = []
    events: list[tuple] = []
    clubs: list[tuple] = []
    seen: list[SeenBootstrap] = []
    bootstraps = sorted((f for f in files if f.kind == "bootstrap"), key=lambda f: f.gw)
    for snapshot in bootstraps:
        bootstrap: Bootstrap = snapshot.load()
        if snapshot.fetched_at is not None:
            seen.append(SeenBootstrap(
                snapshot.gw, snapshot.source, snapshot.fetched_at,
                frozenset(e.id for e in bootstrap.events if e.data_checked),
            ))
            for e in bootstrap.events:
                if e.data_checked and (e.id not in first_checked
                                       or snapshot.fetched_at < first_checked[e.id]):
                    first_checked[e.id] = snapshot.fetched_at
        clubs_of[snapshot.gw] = {p.id: p.team for p in bootstrap.elements}
        for p in sorted(bootstrap.elements, key=lambda p: p.id):
            player_state.append((
                snapshot.gw, p.id, _iso(snapshot.fetched_at), p.code, p.web_name, p.team,
                int(p.element_type), p.now_cost, p.status.value,
                p.chance_of_playing_next_round, _iso(p.news_added), p.selected_by_percent,
                p.form, int(is_shortlisted(p)), *(getattr(p, name) for name in TOTAL_FIELDS),
            ))
            rows_from[snapshot.path] += 1
        if snapshot is bootstraps[-1]:
            events = [
                (e.id, _api_time(e.deadline_time), int(e.finished), int(e.data_checked),
                 snapshot.gw)
                for e in sorted(bootstrap.events, key=lambda e: e.id)
            ]
            clubs = [(t.id, t.short_name, t.name)
                     for t in sorted(bootstrap.teams, key=lambda t: t.id)]

    def checked_before(event: int, fetched_at: datetime | None) -> bool:
        """A bootstrap fetched at or before `fetched_at` shows the round
        data-checked; data_checked never reverts, so the snapshot came after."""
        first = first_checked.get(event)
        return fetched_at is not None and first is not None and first <= fetched_at

    fixtures: dict[int, tuple[Fixture, int, str]] = {}
    frozen: set[int] = set()
    fixture_snapshots: list[tuple] = []
    for snapshot in (f for f in files if f.kind == "fixtures"):
        payload: tuple[Fixture, ...] = snapshot.load()
        for fixture in payload:
            if fixture.id not in frozen:
                fixtures[fixture.id] = (fixture, snapshot.gw, snapshot.path)
        for fixture in payload:
            if (fixture.finished and fixture.event is not None
                    and checked_before(fixture.event, snapshot.fetched_at)):
                frozen.add(fixture.id)
        fixture_snapshots.extend(
            (snapshot.gw, x.id, x.event, x.team_h, x.team_a, x.team_h_difficulty,
             x.team_a_difficulty, _api_time(x.kickoff_time), int(x.finished),
             x.team_h_score, x.team_a_score)
            for x in sorted(payload, key=lambda x: x.id)
        )
    for _, _, path in fixtures.values():
        rows_from[path] += 1

    summaries: dict[int, list[_RawFile]] = {}
    for f in files:
        if f.kind == "summary":
            summaries.setdefault(_element_of(f.path), []).append(f)

    history_past: list[tuple] = []
    for element in sorted(summaries):
        first, *rest = summaries[element]
        for past in sorted(first.load().history_past, key=lambda p: p.season_name):
            history_past.append((
                element, past.season_name, past.element_code,
                *(getattr(past, name) for name in PAST_FIELDS[1:]),
                int(past.season_name >= XG_RECORDED_FROM),
                int(past.season_name >= DC_RECORDED_FROM),
                first.path,
            ))
            rows_from[first.path] += 1
        for later in rest:
            later.load()

    lives: dict[int, list[_RawFile]] = {}
    for f in files:
        if f.kind == "event-live":
            lives.setdefault(int(_LIVE_FILE.match(Path(f.path).name).group(1)), []).append(f)

    player_rounds: list[tuple] = []
    for rnd in sorted(lives):
        copies = lives[rnd]
        chosen: tuple[_RawFile, EventLive] | None = None
        for copy in copies:
            live: EventLive = copy.load()
            final_of[copy.path] = prove_live_final(
                copy.raw_root, copy.gw, rnd, sidecar_final=copy.sidecar_final,
                fetched_at=copy.fetched_at, bootstraps=seen,
            ) is not None
            if chosen is None and final_of[copy.path]:
                chosen = copy, live
        if chosen is None:
            first = copies[0]
            raise StoreSyncError(
                f"{first.path}: round {rnd} live stats are not final — no final sidecar, "
                f"and no kept bootstrap of gw{rnd + 1} or later, fetched at or before "
                f"them, shows round {rnd} data-checked. "
                f"Refetch: python -m fpl event-live --gw {first.gw} --round {rnd} --force"
            )
        source, live = chosen
        clubs_by_gw = {gw: clubs_of[gw] for gw in (rnd, rnd + 1) if gw in clubs_of}
        for element in sorted(live.elements, key=lambda e: e.id):
            built = _element_rows(rnd, element, source, fixtures, clubs_by_gw,
                                  summaries.get(element.id, []), checked_before)
            for row in built:
                rows_from[row[-1]] += 1
            player_rounds.extend(built)

    return _Tables(
        manifest=[
            (f.path, f.sha256, f.kind, f.gw, _iso(f.fetched_at), int(final_of[f.path]),
             int(f.sidecar_final), rows_from[f.path])
            for f in sorted(files, key=lambda f: f.path)
        ],
        events=events,
        clubs=clubs,
        fixtures=[
            (f.id, f.event, f.team_h, f.team_a, _api_time(f.kickoff_time), int(f.finished),
             f.team_h_score, f.team_a_score, gw)
            for f, gw, _ in (fixtures[i] for i in sorted(fixtures))
        ],
        fixture_snapshots=fixture_snapshots,
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
    checked_before: Callable[[int, datetime | None], bool],
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
        covering = _covering_summary(element.id, rnd, matches, summaries, checked_before)
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
    element: int, rnd: int, matches: Sequence[Fixture], summaries: Sequence[_RawFile],
    checked_before: Callable[[int, datetime | None], bool],
) -> list[tuple] | None:
    """The earliest summary fetched after the round was data-checked that has
    a row for every fixture the element played in it. One fetched before the
    check may carry provisional bonus and points."""
    for summary in summaries:
        if summary.gw <= rnd or not checked_before(rnd, summary.fetched_at):
            continue
        by_fixture = {row.fixture: row for row in summary.load().history}
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
    """Builds the store in a temporary file beside it and moves it into place
    only once committed."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{db_path.name}.", suffix=".tmp", dir=db_path.parent)
    os.close(fd)
    building = Path(name)
    try:
        _fill(building, tables)
        os.replace(building, db_path)
    except BaseException:
        building.unlink(missing_ok=True)
        raise
    _remove_orphans(db_path)


def _remove_orphans(db_path: Path) -> None:
    """Temporary files of the store or its scan cache that a killed sync left
    behind. Only a sync, under the sync lock, writes them, so none is live."""
    for orphan in db_path.parent.glob(f".{db_path.name}.*.tmp"):
        orphan.unlink(missing_ok=True)


def _fill(db_path: Path, tables: _Tables) -> None:
    con = _connect(db_path)
    try:
        con.execute("BEGIN")
        for statement in filter(str.strip, _SCHEMA.split(";")):
            con.execute(statement)
        _insert(con, "manifest", tables.manifest)
        _insert(con, "events", tables.events)
        _insert(con, "clubs", tables.clubs)
        _insert(con, "fixtures", tables.fixtures)
        _insert(con, "fixture_snapshots", tables.fixture_snapshots)
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


def _report(con: sqlite3.Connection, ingested: int, total: int, rebuilt: bool) -> SyncReport:
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
        files_total=total,
        rebuilt=rebuilt,
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


# --- as-of readers -----------------------------------------------------------

Coverage = Literal["production", "shortlist", "all"]
COVERAGES: tuple[Coverage, ...] = ("production", "shortlist", "all")


class StoreReadError(ValueError):
    """The store cannot answer an as-of question without leaking or guessing."""


class StoreStaleError(StoreReadError):
    """The store is missing, unreadable, of another schema, or behind the raw
    tree: a sync fixes it."""

    def __init__(self, message: str, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


class StoredMatch(MatchRecord):
    """A per-match row as the readers return it: an element-summary `history`
    row, with the opponent the summary also carries."""

    opponent_team: int | None = None


class PlayerMatch(StoredMatch):
    """A stored match row with its player and the club he played for."""

    element: int
    team: int | None
    kickoff_time: datetime | None


class PlayerState(BaseModel):
    model_config = ConfigDict(frozen=True)

    gw: int
    element: int
    fetched_at: datetime | None
    code: int | None
    web_name: str
    team: int
    position: Position
    now_cost: int
    status: PlayerStatus
    chance: int | None
    news_added: datetime | None
    selected_by_percent: float
    form: float
    shortlisted: bool
    minutes: int
    starts: int
    total_points: int
    goals_scored: int | None
    assists: int | None
    clean_sheets: int
    goals_conceded: int
    saves: int
    bonus: int
    bps: int | None
    yellow_cards: int | None
    red_cards: int | None
    own_goals: int | None
    penalties_saved: int | None
    penalties_missed: int | None
    defensive_contribution: float | None
    expected_goals: float
    expected_assists: float
    expected_goals_conceded: float


_MATCH_COLUMNS = tuple(name for name in StoredMatch.model_fields if name in PLAYER_ROUND_COLUMNS)


def open_ro(db_path: Path, raw_root: Path) -> SeasonReader:
    """A read-only view of the store, refused unless it has ingested exactly
    the raw tree it was built from."""
    con, _ = _open_checked(db_path, raw_root)
    con.row_factory = sqlite3.Row
    return SeasonReader(con, raw_root, db_path)


def open_synced(
    db_path: Path, raw_root: Path, *, notify: Callable[[str], None] | None = None
) -> SeasonReader:
    """`open_ro`, syncing the store first when it is stale. The staleness is
    re-checked under the sync lock, so a reader that waited on another's sync
    reads that result instead of syncing again. A raw file written between a
    sync and the open triggers one more sync; a tree still changing after
    MAX_AUTO_SYNCS refuses. A failed sync refuses and leaves the store as it
    was."""
    try:
        return open_ro(db_path, raw_root)
    except StoreStaleError:
        pass
    reason: str | None = None
    report: SyncReport | None = None
    with sync_lock(db_path):
        for attempt in range(MAX_AUTO_SYNCS + 1):
            try:
                reader = open_ro(db_path, raw_root)
                break
            except StoreStaleError as stale:
                if attempt == MAX_AUTO_SYNCS:
                    raise StoreStaleError(
                        f"{stale} — {raw_root} changed during {MAX_AUTO_SYNCS} syncs; "
                        f"run the command again once nothing is writing to it",
                        stale.reason) from None
                reason = reason or stale.reason
                report = _sync(raw_root, db_path, force=False)
    if report is not None:
        (notify or _stderr_line)(f"season store {db_path} synced ({reason}): {_built(report)}")
    return reader


def _built(report: SyncReport) -> str:
    """Every sync that finds a change rebuilds the whole store from the raw
    tree; the count says how many raw files differed from the last build."""
    if report.rebuilt:
        return (f"rebuilt from {report.files_total} raw files "
                f"({report.files_ingested} new or changed)")
    return f"up to date, {report.files_total} raw files, none new or changed"


def _stderr_line(line: str) -> None:
    print(line, file=sys.stderr)


def _open_checked(
    db_path: Path, raw_root: Path, files: Sequence[_RawFile] | None = None
) -> tuple[sqlite3.Connection, Sequence[_RawFile]]:
    """The store opened read-only and the scan it was checked against. With
    no `files`, the raw tree is scanned trusting the store's scan cache."""
    con = _open_existing(db_path, raw_root)
    try:
        known = _readable(db_path, raw_root, lambda: (
            _manifest_keys(con) if _version(con) == SCHEMA_VERSION else None))
        if files is None:
            files = _scan(raw_root, _trusted(db_path, known) if known is not None else None)
        hint = _hint(raw_root, db_path, _gws(files))
        if known is None:
            raise StoreStaleError(
                f"season store {db_path} has another schema version — {hint}",
                "another schema version")
        stale = _first_difference(known, {f.path: f.key for f in files})
        if stale is not None:
            raise StoreStaleError(
                f"season store {db_path} is behind {raw_root}: {stale} — {hint}", stale)
    except BaseException:
        con.close()
        raise
    return con, files


def _open_existing(db_path: Path, raw_root: Path) -> sqlite3.Connection:
    if not db_path.is_file():
        raise StoreStaleError(
            f"no season store at {db_path} — {_hint(raw_root, db_path, _raw_gws(raw_root))}",
            "no store yet")
    return sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)


def _version(con: sqlite3.Connection) -> int:
    return con.execute("PRAGMA user_version").fetchone()[0]


def _readable(db_path: Path, raw_root: Path, read: Callable[[], Any]) -> Any:
    try:
        return read()
    except sqlite3.DatabaseError as exc:
        hint = _hint(raw_root, db_path, _raw_gws(raw_root), "rebuild")
        raise StoreStaleError(f"season store {db_path} is unreadable ({exc}) — {hint}",
                              f"unreadable: {exc}") from None


def _gws(files: Sequence[_RawFile]) -> list[int]:
    return [f.gw for f in files]


def _raw_gws(raw_root: Path) -> list[int]:
    """The gameweeks holding a kept snapshot, without hashing anything."""
    if not raw_root.is_dir():
        return []
    return [
        int(m.group(1)) for d in raw_root.iterdir()
        if d.is_dir() and (m := _GW_DIR.match(d.name)) and (
            any(_is_snapshot(p.name) for p in d.glob("*.json"))
            or any((d / "players").glob("summary-*.json")))
    ]


def _is_snapshot(name: str) -> bool:
    return name in ("bootstrap.json", "fixtures.json") or _LIVE_FILE.match(name) is not None


def _hint(raw_root: Path, db_path: Path, gws: Iterable[int], action: str = "sync") -> str:
    """The command that brings the store level with the raw tree, naming
    --data-root and --store only when they are not the defaults."""
    latest = max(gws, default=None)
    if latest is None:
        return f"no raw snapshots under {raw_root} — fetch them first"
    store = "" if db_path == default_store_path(raw_root) else f" --store {db_path}"
    return f"run: {_fpl(raw_root)} store {action} --gw {latest}{store}"


def _fpl(raw_root: Path) -> str:
    data_root = "" if raw_root == DEFAULT_RAW_ROOT else f" --data-root {raw_root}"
    return f"uv run python -m fpl{data_root}"


def _first_difference(
    known: dict[str, ChangeKey], current: dict[str, ChangeKey]
) -> str | None:
    for path in sorted(current.keys() | known.keys()):
        if path not in known:
            return f"{path} not ingested"
        if path not in current:
            return f"{path} ingested but no longer in the raw tree"
        if known[path] != current[path]:
            return f"{path} changed since the last sync"
    return None


class SeasonReader:
    """As of round r: match rows of rounds < r only, and the gw r snapshots
    (bootstrap, fixtures), refused when fetched at or after deadline r."""

    def __init__(self, con: sqlite3.Connection, raw_root: Path, db_path: Path) -> None:
        self._con = con
        self._raw_root = raw_root
        self._db_path = db_path

    def close(self) -> None:
        self._con.close()

    def __enter__(self) -> SeasonReader:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def rounds(self, as_of: int, ids: Iterable[int]) -> dict[int, tuple[StoredMatch, ...]]:
        self._require_rounds(as_of)
        wanted = set(ids)
        found: dict[int, list[StoredMatch]] = {}
        for row in self._con.execute(
            f"SELECT element, {', '.join(_MATCH_COLUMNS)} FROM player_rounds "
            "WHERE round < ? ORDER BY element, kickoff_time, fixture", (as_of,)
        ):
            if row["element"] in wanted:
                found.setdefault(row["element"], []).append(
                    StoredMatch.model_validate({name: row[name] for name in _MATCH_COLUMNS}))
        return {element: tuple(rows) for element, rows in found.items()}

    def matches(self, as_of: int, first: int = 1) -> tuple[PlayerMatch, ...]:
        """Every stored match row of rounds first..as_of-1, with the club the
        player played for (None when the side was unresolved)."""
        self._require_rounds(as_of)
        columns = ("element", "team", "kickoff_time", *_MATCH_COLUMNS)
        return tuple(
            PlayerMatch.model_validate({name: row[name] for name in columns})
            for row in self._con.execute(
                f"SELECT {', '.join(columns)} FROM player_rounds "
                "WHERE round >= ? AND round < ? ORDER BY element, kickoff_time, fixture",
                (first, as_of),
            )
        )

    def clubs(self) -> dict[int, str]:
        """club id → short name, from the latest bootstrap."""
        return {row["id"]: row["short_name"]
                for row in self._con.execute("SELECT id, short_name FROM clubs")}

    def past(self, ids: Iterable[int]) -> dict[int, tuple[PastSeason, ...]]:
        """Every past season of each id that has a summary on file; an id
        whose summary lists none maps to (). history_past does not change
        during a season, so any snapshot's copy is the as-of copy."""
        wanted = set(ids)
        found: dict[int, list[PastSeason]] = {
            element: [] for (element,) in self._con.execute(
                "SELECT DISTINCT element FROM summary_coverage") if element in wanted
        }
        for row in self._con.execute(
            f"SELECT element, {', '.join(PAST_FIELDS)} FROM history_past "
            "ORDER BY element, season_name"
        ):
            if row["element"] in found:
                found[row["element"]].append(
                    PastSeason.model_validate({name: row[name] for name in PAST_FIELDS}))
        return {element: tuple(rows) for element, rows in found.items()}

    def summaries(
        self, as_of: int, ids: Iterable[int], coverage: Coverage = "production", *,
        pinned: Iterable[int] = (),
    ) -> dict[int, ElementSummary]:
        """The summaries a gw `as_of` run would have read, by coverage:
        production — the ids with a summary in data/raw/gw{as_of}/players;
        shortlist — shortlisted in the gw `as_of` bootstrap, plus `pinned`
        (the round's inputs ids); all — every id in that bootstrap. An id
        whose history_past was never fetched is absent under every coverage."""
        ids = list(dict.fromkeys(ids))
        if coverage == "production":
            pool = {element for (element,) in self._con.execute(
                "SELECT element FROM summary_coverage WHERE gw = ?", (as_of,))}
        elif coverage in ("shortlist", "all"):
            self._require_before_deadline("bootstrap", as_of)
            condition = " AND shortlisted = 1" if coverage == "shortlist" else ""
            pool = {element for (element,) in self._con.execute(
                f"SELECT element FROM player_state WHERE gw = ?{condition}", (as_of,))}
            if coverage == "shortlist":
                pool |= set(pinned)
        else:
            raise ValueError(f"unknown coverage {coverage!r}; expected one of {COVERAGES}")
        chosen = [element for element in ids if element in pool]
        past = self.past(chosen)
        matches = self.rounds(as_of, chosen)
        return {
            element: ElementSummary(history=matches.get(element, ()),
                                    history_past=past[element])
            for element in chosen if element in past
        }

    def fixtures(self, as_of: int) -> tuple[Fixture, ...]:
        """The fixture list as the gw `as_of` snapshot had it (no stats)."""
        self._require_before_deadline("fixtures", as_of)
        columns = FIXTURE_SNAPSHOT_COLUMNS[1:]
        return tuple(
            Fixture.model_validate({name: row[name] for name in columns})
            for row in self._con.execute(
                f"SELECT {', '.join(columns)} FROM fixture_snapshots WHERE gw = ? ORDER BY id",
                (as_of,),
            )
        )

    def club_match_xg(self, as_of: int) -> dict[int, tuple[float, float]]:
        """fixture id → (home xG, away xG) for every fixture of rounds < as_of
        that the gw `as_of` snapshot shows finished. Rows with no resolved
        side are left out."""
        self._require_rounds(as_of)
        played = [f for f in self.fixtures(as_of)
                  if f.finished and f.event is not None and f.event < as_of]
        xg: dict[tuple[int, int], float] = {
            (fixture, team): total for fixture, team, total in self._con.execute(
                "SELECT fixture, team, SUM(expected_goals) FROM player_rounds "
                "WHERE round < ? AND team IS NOT NULL GROUP BY fixture, team", (as_of,))
        }
        return {
            f.id: (xg.get((f.id, f.team_h)) or 0.0, xg.get((f.id, f.team_a)) or 0.0)
            for f in played
        }

    def player_state(self, gw: int) -> dict[int, PlayerState]:
        self._require_before_deadline("bootstrap", gw)
        return {
            row["element"]: PlayerState.model_validate(dict(row))
            for row in self._con.execute(
                "SELECT * FROM player_state WHERE gw = ? ORDER BY element", (gw,))
        }

    def _require_rounds(self, as_of: int) -> None:
        if as_of < 1:
            raise ValueError(f"as-of round must be ≥ 1, got {as_of}")
        stored = {r for (r,) in self._con.execute("SELECT DISTINCT round FROM player_rounds")}
        missing = sorted(set(range(1, as_of)) - stored)
        if missing:
            r = missing[0]
            raise StoreReadError(
                f"round(s) {missing} have no final live stats in the store — fetch: "
                f"{_fpl(self._raw_root)} event-live --gw {r + 1} --round {r} "
                f"(the next read syncs it into the store)"
            )

    def _require_before_deadline(self, kind: str, gw: int) -> None:
        path = f"gw{gw}/{kind}.json"
        found = self._con.execute(
            "SELECT fetched_at FROM manifest WHERE path = ?", (path,)).fetchone()
        if found is None:
            raise StoreReadError(f"no {path} in the store — gw{gw} has no {kind} snapshot")
        deadline = self._con.execute(
            "SELECT deadline_time FROM events WHERE id = ?", (gw,)).fetchone()
        if deadline is None:
            return
        if found["fetched_at"] is None:
            raise StoreReadError(
                f"{path} has no recorded fetch time — cannot show it predates deadline {gw}")
        if datetime.fromisoformat(found["fetched_at"]) >= datetime.fromisoformat(deadline[0]):
            raise StoreReadError(
                f"{path} was fetched at {found['fetched_at']}, not before the gw{gw} "
                f"deadline {deadline[0]} — it may show round {gw}"
            )


# --- the history source of ep, objective, players and fixtures-rate ----------

HistorySource = Literal["summaries", "store"]
HISTORY_SOURCES: tuple[HistorySource, ...] = ("summaries", "store")
DEFAULT_HISTORY_SOURCE: HistorySource = "store"


def add_history_arguments(parser: argparse.ArgumentParser) -> None:
    """`--history-from` and `--store`, shared by every command that reads
    this season's per-match history."""
    parser.add_argument(
        "--history-from", choices=HISTORY_SOURCES, default=DEFAULT_HISTORY_SOURCE,
        help="this season's per-match history: the season store (default), synced "
             "first when it is behind the raw tree, or the cached element summaries of gw N",
    )
    parser.add_argument("--store", type=Path, default=None,
                        help=f"season store for --history-from store (default: "
                             f"store/{STORE_FILENAME} beside --data-root); refused "
                             f"with any other --history-from")


def check_history_arguments(args: argparse.Namespace) -> None:
    """Refuses `--store` without `--history-from store`, where it would be
    silently ignored."""
    if getattr(args, "history_from", "store") != "store" and args.store is not None:
        raise ValueError(
            f"--store is read only with --history-from store "
            f"(this run reads --history-from {args.history_from})")


@dataclass(frozen=True)
class History:
    """Where a gw N run reads per-match history. `summaries` reads the cached
    element summaries of gw N. `store` reads the season store as of round N,
    synced first when it is behind, with shortlist coverage: the ids
    shortlisted in the gw N bootstrap plus the ids the caller pins (the
    round's inputs ids), each with the history_past of whichever summary the
    raw tree holds for it. gw N's own summaries are only the players the
    collector fetched with `--missing-past`, so they are not the pool."""

    source: HistorySource
    raw_root: Path
    store_path: Path = DEFAULT_STORE_PATH

    @classmethod
    def from_args(cls, raw_root: Path, args: argparse.Namespace) -> History:
        check_history_arguments(args)
        return cls(args.history_from, raw_root, args.store or default_store_path(raw_root))

    def summaries(
        self, gw: int, ids: Iterable[int], *, pinned: Iterable[int] = ()
    ) -> dict[int, ElementSummary]:
        if self.source == "summaries":
            return load_cached_summaries(SnapshotStore(self.raw_root), gw, ids)
        with self.open() as reader:
            return reader.summaries(gw, ids, coverage="shortlist", pinned=pinned)

    def fetch_hint(self, gw: int, ids: Sequence[int]) -> str:
        """The command that gives `ids` a summary this source reads."""
        if self.source == "summaries":
            return f"{_fpl(self.raw_root)} summaries --gw {gw} --ids {','.join(map(str, ids))}"
        return (f"{_fpl(self.raw_root)} summaries --gw {gw} --missing-past "
                f"(the next read syncs it into the store)")

    def matches_by_player(
        self, gw: int, ids: Iterable[int]
    ) -> dict[int, tuple[MatchRecord, ...]]:
        """Each id's match rows of rounds < gw. From summaries, an id with no
        summary is absent; from the store, every id is present, with () when
        it played no match."""
        ids = list(dict.fromkeys(ids))
        if self.source == "summaries":
            return {element: summary.history
                    for element, summary in self.summaries(gw, ids).items()}
        with self.open() as reader:
            rows = reader.rounds(gw, ids)
        return {element: rows.get(element, ()) for element in ids}

    def open(self) -> SeasonReader:
        if self.source != "store":
            raise ValueError("the season store is read only with --history-from store")
        return open_synced(self.store_path, self.raw_root)


# --- fpl store ---------------------------------------------------------------

ACTIONS = ("sync", "verify", "status", "rebuild")
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_MISMATCH = 3


def register(add: Callable[..., argparse.ArgumentParser]) -> None:
    """Adds `fpl store` through the CLI's own `add`, so it takes `--gw` like
    every other command."""
    p = add("store", "build and check the local season store (derived from data/raw)",
            cached=False)
    p.add_argument(
        "action", choices=ACTIONS,
        help="sync: rebuild when a raw file is new or changed; rebuild: always; verify: in sync, "
             "reconciled and equal to a fresh build (writes nothing); status: the "
             "manifest summary (writes nothing). Every action covers the whole raw tree; "
             f"exit {EXIT_MISMATCH}: a reconciliation mismatch",
    )
    p.add_argument("--store", type=Path, default=None,
                   help=f"store file (default: store/{STORE_FILENAME} beside --data-root)")


def run(raw_root: Path, args: argparse.Namespace) -> int:
    args.store = args.store or default_store_path(raw_root)
    if args.action == "status":
        return _status(raw_root, args.store)
    if args.action == "verify":
        return _verify(raw_root, args.store)
    report = (rebuild if args.action == "rebuild" else sync)(raw_root, args.store)
    print(f"store {args.store}: {_built(report)}")
    exit_code = _print_report(report)
    print(_coverage_line(args.store, args.gw))
    return exit_code


def _coverage_line(db_path: Path, gw: int) -> str:
    """How much of the gw bootstrap the store has history_past for: players
    with a kept summary in some gameweek (no_pl_history of them with no past
    PL season), and missing_past, the ids `summaries --missing-past` fetches."""
    con = _connect(db_path)
    try:
        ids = {e for (e,) in con.execute(
            "SELECT element FROM player_state WHERE gw = ?", (gw,))}
        covered = {e for (e,) in con.execute("SELECT DISTINCT element FROM summary_coverage")}
        with_past = {e for (e,) in con.execute("SELECT DISTINCT element FROM history_past")}
    finally:
        con.close()
    if not ids:
        return f"coverage gw{gw}: no bootstrap in the store"
    players = ids & covered
    return (f"coverage gw{gw}: players {len(players)}, "
            f"no_pl_history {len(players - with_past)}, missing_past {len(ids - covered)}")


def _print_report(report: SyncReport) -> int:
    print(f"rounds {_spans(report.rounds)}")
    print(f"player_rounds {report.player_rounds}")
    print(f"history_past players {report.history_past_players}")
    print(f"unresolved sides {len(report.unresolved)}")
    for u in report.unresolved:
        print(f"  round {u.round} element {u.element} fixture {u.fixture}")
    print(f"dgw splits {len(report.dgw_splits)}")
    for d in report.dgw_splits:
        print(f"  round {d.round} element {d.element} "
              f"fixtures {','.join(map(str, d.fixtures))}")
    if report.reconciliation_skipped is not None:
        print(f"reconciliation: skipped ({report.reconciliation_skipped})")
        return EXIT_OK
    if not report.mismatches:
        print("reconciliation: OK")
        return EXIT_OK
    count = len(report.mismatches)
    print(f"reconciliation: {count} mismatch{'' if count == 1 else 'es'}")
    for line in report.mismatches:
        print(f"  {line}")
    return EXIT_MISMATCH


def _verify(raw_root: Path, db_path: Path) -> int:
    files = _scan(raw_root)
    con, _ = _open_checked(db_path, raw_root, files)
    try:
        exit_code = _print_report(_report(con, 0, len(files), False))
        stored = list(con.iterdump())
    finally:
        con.close()
    with tempfile.TemporaryDirectory(prefix="fpl-store-verify-") as scratch:
        fresh_path = Path(scratch) / "fresh.sqlite"
        _fill(fresh_path, _build(files))
        fresh = _connect(fresh_path)
        try:
            built = list(fresh.iterdump())
        finally:
            fresh.close()
    if stored != built:
        first = next((a for a, b in zip(stored, built) if a != b),
                     "row count differs" if len(stored) != len(built) else "")
        print(f"content: differs from a fresh build (first: {first[:160]})")
        print(f"error: season store {db_path} does not equal a fresh build of {raw_root} — "
              f"{_hint(raw_root, db_path, _gws(files), 'rebuild')}", file=sys.stderr)
        return EXIT_ERROR
    print("content: matches a fresh build")
    return exit_code


def _status(raw_root: Path, db_path: Path) -> int:
    con = _open_existing(db_path, raw_root)
    try:
        version = _readable(db_path, raw_root, lambda: _version(con))
        if version != SCHEMA_VERSION:
            raise StoreReadError(
                f"season store {db_path} has schema {version}, this code reads "
                f"{SCHEMA_VERSION} — {_hint(raw_root, db_path, _raw_gws(raw_root))}")
        manifest = _readable(db_path, raw_root, lambda: con.execute(
            "SELECT kind, gw, final, ingested_rows, fetched_at FROM manifest").fetchall())
        rounds = tuple(r for (r,) in con.execute(
            "SELECT DISTINCT round FROM player_rounds ORDER BY round"))
        player_rounds = con.execute("SELECT COUNT(*) FROM player_rounds").fetchone()[0]
        known = _manifest_keys(con)
    finally:
        con.close()
    files = _scan(raw_root, _trusted(db_path, known))
    stale = _first_difference(known, {f.path: f.key for f in files})
    gws = sorted({gw for _, gw, *_ in manifest})
    span = f"gw{gws[0]}-{gws[-1]}" if gws else "no gameweeks"
    print(f"store {db_path}: schema {version}, {len(manifest)} files, {span}")
    print(f"{'kind':<11}{'files':>7}{'final':>7}{'rows':>9}")
    for kind in ("bootstrap", "fixtures", "event-live", "summary"):
        of_kind = [row for row in manifest if row[0] == kind]
        print(f"{kind:<11}{len(of_kind):>7}{sum(row[2] for row in of_kind):>7}"
              f"{sum(row[3] for row in of_kind):>9}")
    print(f"rounds {_spans(rounds)}")
    print(f"player_rounds {player_rounds}")
    fetched = [row[4] for row in manifest if row[4] is not None]
    print(f"latest fetch {max(fetched, key=datetime.fromisoformat) if fetched else 'none'}")
    if stale is None:
        print(f"in sync with {raw_root}")
    else:
        print(f"behind {raw_root}: {stale} — {_hint(raw_root, db_path, _gws(files))}")
    return EXIT_OK


def _spans(values: Sequence[int]) -> str:
    """1,2,3,5 → '1-3, 5'."""
    if not values:
        return "none"
    spans: list[list[int]] = []
    for value in values:
        if spans and value == spans[-1][1] + 1:
            spans[-1][1] = value
        else:
            spans.append([value, value])
    return ", ".join(str(lo) if lo == hi else f"{lo}-{hi}" for lo, hi in spans)
