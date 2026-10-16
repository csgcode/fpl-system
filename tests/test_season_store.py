import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from fpl.ep import _league_mean
from fpl.fixture_ratings import _side_xg, load_inputs
from fpl.models import Position, is_shortlisted
from fpl.season_store import (
    COVERAGES,
    SCHEMA_VERSION,
    StoreReadError,
    StoreSyncError,
    _build,
    _scan,
    open_ro,
    rebuild,
    sync,
)
from fpl.service import load_cached_bootstrap, load_cached_summaries
from fpl.store import SnapshotStore
from tests.factories import (
    bootstrap_payload,
    event_payload,
    fixture_bps_stat,
    fixture_payload,
    live_stats_payload,
    past_season_payload,
    player_payload,
    priors_doc,
    team_payload,
)

DEADLINES = {
    1: datetime(2026, 8, 14, 17, 30, tzinfo=timezone.utc),
    2: datetime(2026, 8, 21, 17, 30, tzinfo=timezone.utc),
    3: datetime(2026, 8, 28, 17, 30, tzinfo=timezone.utc),
    4: datetime(2026, 9, 4, 17, 30, tzinfo=timezone.utc),
}
X_FIELDS = ("expected_goals", "expected_assists", "expected_goals_conceded")
COMPARED = (
    "round", "opponent_team", "was_home", "kickoff_time", "minutes", "starts",
    "total_points", "goals_scored", "assists", "clean_sheets", "goals_conceded",
    "saves", "bonus", "bps", *X_FIELDS, "defensive_contribution", "yellow_cards",
    "red_cards", "own_goals", "penalties_saved", "penalties_missed", "modified",
)


def fetch_time(gw: int) -> datetime:
    """A gameweek's snapshots are fetched three days before its deadline."""
    return DEADLINES[gw] - timedelta(days=3)


@dataclass(frozen=True)
class Match:
    element: int
    fixture: int
    minutes: int = 90
    goals: int = 0
    xg: str = "0.00"
    bonus: int = 0
    club: int | None = None

    def points(self) -> int:
        appearance = 2 if self.minutes >= 60 else 1 if self.minutes > 0 else 0
        return appearance + 5 * self.goals + self.bonus

    def stats(self) -> dict[str, Any]:
        played = self.minutes > 0
        return live_stats_payload(
            minutes=self.minutes, starts=int(played), goals_scored=self.goals,
            clean_sheets=0, goals_conceded=int(played), saves=0, bonus=self.bonus,
            bps=10 + 20 * self.goals if played else 0, expected_goals=self.xg,
            expected_assists="0.00",
            expected_goals_conceded="0.50" if played else "0.00",
            recoveries=3 if played else 0, total_points=self.points(),
        )

    def explain(self) -> dict[str, Any]:
        stats = [{"identifier": "minutes", "points": self.points() - 5 * self.goals - self.bonus,
                  "value": self.minutes, "points_modification": 0}]
        if self.goals:
            stats.append({"identifier": "goals_scored", "points": 5 * self.goals,
                          "value": self.goals, "points_modification": 0})
        if self.bonus:
            stats.append({"identifier": "bonus", "points": self.bonus,
                          "value": self.bonus, "points_modification": 0})
        return {"fixture": self.fixture, "stats": stats}


def _sum_stats(stats: list[dict[str, Any]]) -> dict[str, Any]:
    total = dict(stats[0])
    for extra in stats[1:]:
        for key, value in extra.items():
            if isinstance(value, bool):
                continue
            if isinstance(value, int):
                total[key] += value
            elif key in X_FIELDS:
                total[key] = f"{float(total[key]) + float(value):.2f}"
    return total


@dataclass
class Season:
    """A synthetic raw tree: three clubs, rounds 1–2, one gw directory per
    gameweek written in fetch order (bootstrap, fixtures, live, summaries)."""

    fixtures: dict[int, tuple[int, int, int, str]] = field(default_factory=lambda: {
        1: (1, 1, 2, "2026-08-15T14:00:00Z"),
        2: (2, 2, 1, "2026-08-22T14:00:00Z"),
    })
    clubs: dict[int, dict[int, int]] = field(default_factory=lambda: {
        1: {1: 1, 2: 1, 3: 1}, 2: {1: 2, 2: 2, 3: 2}, 3: {1: 1, 2: 1, 3: 1},
    })
    positions: dict[int, int] = field(default_factory=lambda: {1: 3, 2: 2, 3: 1})
    matches: list[Match] = field(default_factory=lambda: [
        Match(1, 1, goals=1, xg="0.61", bonus=3), Match(2, 1), Match(3, 1, minutes=0),
        Match(1, 2, xg="0.20"), Match(2, 2, minutes=75), Match(3, 2, minutes=0),
    ])
    summary_ids: set[int] = field(default_factory=lambda: {1, 2, 3})
    final_sidecar: set[int] = field(default_factory=set)
    live_before_bootstrap: set[int] = field(default_factory=set)
    unchecked: dict[int, set[int]] = field(default_factory=dict)
    totals_delta: dict[tuple[int, int], dict[str, int]] = field(default_factory=dict)
    history_past: dict[tuple[int, int], list[dict]] = field(default_factory=dict)
    player_overrides: dict[int, dict[str, Any]] = field(default_factory=dict)

    def round_of(self, fixture: int) -> int:
        return self.fixtures[fixture][0]

    def club_at(self, match: Match) -> int:
        if match.club is not None:
            return match.club
        return self.clubs[match.element][self.round_of(match.fixture)]

    def write(self, root: Path, gws: range = range(1, 4)) -> None:
        for gw in gws:
            when = fetch_time(gw)
            self._bootstrap(root, gw, when)
            self._fixtures(root, gw, when + timedelta(minutes=30))
            if gw - 1 in {self.round_of(f) for f in self.fixtures}:
                live_at = (when - timedelta(hours=1) if gw - 1 in self.live_before_bootstrap
                           else when + timedelta(hours=1))
                self._live(root, gw, gw - 1, live_at)
                for element in sorted(self.summary_ids):
                    self._summary(root, gw, element, when + timedelta(hours=2))

    def _save(self, root: Path, when: datetime, gw: int, name: str, payload: Any,
              **kwargs: Any) -> None:
        SnapshotStore(root, now=lambda: when).save(gw, name, payload, "https://x.test", **kwargs)

    def _checked(self, gw: int) -> set[int]:
        return {r for r in range(1, gw) if r not in self.unchecked.get(gw, set())}

    def _bootstrap(self, root: Path, gw: int, when: datetime) -> None:
        checked = self._checked(gw)
        events = [event_payload(
            id=e, name=f"Gameweek {e}", deadline_time=DEADLINES[e].isoformat(),
            finished=e < gw, data_checked=e in checked, is_current=e == gw - 1,
            is_next=e == gw,
        ) for e in sorted(DEADLINES)]
        teams = [team_payload(id=i, name=f"Club {i}", short_name=f"C{i}") for i in (1, 2, 3)]
        elements = []
        for element, by_gw in sorted(self.clubs.items()):
            if gw not in by_gw:
                continue
            played = [m for m in self.matches
                      if m.element == element and self.round_of(m.fixture) < gw]
            totals = {"minutes": 0, "starts": 0, "total_points": 0, "bonus": 0,
                      "goals_scored": 0, "assists": 0, "saves": 0,
                      "goals_conceded": 0, "clean_sheets": 0}
            xg = xgc = 0.0
            for match in played:
                stats = match.stats()
                for key in totals:
                    totals[key] += stats[key]
                xg += float(stats["expected_goals"])
                xgc += float(stats["expected_goals_conceded"])
            for key, delta in self.totals_delta.get((gw, element), {}).items():
                totals[key] += delta
            elements.append(player_payload(
                id=element, code=900000 + element, web_name=f"P{element}",
                team=by_gw[gw], element_type=self.positions.get(element, 3),
                expected_goals=f"{xg:.2f}", expected_goals_conceded=f"{xgc:.2f}",
                penalties_order=None, **totals | self.player_overrides.get(element, {}),
            ))
        self._save(root, when, gw, "bootstrap", bootstrap_payload(elements, teams, events))

    def _fixtures(self, root: Path, gw: int, when: datetime) -> None:
        payload = []
        for fid, (rnd, home, away, kickoff) in sorted(self.fixtures.items()):
            done = rnd < gw
            sides: dict[int, dict[int, int]] = {home: {}, away: {}}
            for m in self.matches:
                if m.fixture == fid and m.minutes > 0:
                    sides[self.club_at(m)][m.element] = m.minutes // 10
            payload.append(fixture_payload(
                id=fid, event=rnd, team_h=home, team_a=away, kickoff_time=kickoff,
                finished=done, team_h_score=1 if done else None,
                team_a_score=0 if done else None,
                stats=[fixture_bps_stat(sides[home], sides[away])] if done else [],
            ))
        self._save(root, when, gw, "fixtures", payload)

    def _live(self, root: Path, gw: int, rnd: int, when: datetime) -> None:
        elements = []
        for element in sorted(self.clubs):
            played = [m for m in self.matches
                      if m.element == element and self.round_of(m.fixture) == rnd]
            if not played:
                continue
            elements.append({
                "id": element, "stats": _sum_stats([m.stats() for m in played]),
                "explain": [m.explain() for m in played], "modified": False,
            })
        self._save(root, when, gw, f"event-live-e{rnd}", {"elements": elements},
                   final=rnd in self.final_sidecar)

    def summary_rows(self, element: int, before_gw: int) -> list[dict[str, Any]]:
        rows = []
        for m in self.matches:
            rnd, home, away, kickoff = self.fixtures[m.fixture]
            if m.element != element or rnd >= before_gw:
                continue
            was_home = self.club_at(m) == home
            rows.append({
                **m.stats(), "element": element, "fixture": m.fixture,
                "opponent_team": away if was_home else home, "was_home": was_home,
                "kickoff_time": kickoff, "team_h_score": 1, "team_a_score": 0,
                "round": rnd, "modified": False, "value": 50, "selected": 1000,
            })
        return sorted(rows, key=lambda r: (r["kickoff_time"], r["fixture"]))

    def _summary(self, root: Path, gw: int, element: int, when: datetime) -> None:
        past = self.history_past.get(
            (gw, element), [past_season_payload(element_code=900000 + element)])
        self._save(root, when, gw, f"players/summary-{element}", {
            "fixtures": [], "history": self.summary_rows(element, gw), "history_past": past,
        })


def rows(db: Path, sql: str, *args: Any) -> list[dict[str, Any]]:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, args)]
    finally:
        con.close()


def dump(db: Path) -> str:
    con = sqlite3.connect(db)
    try:
        return "\n".join(con.iterdump())
    finally:
        con.close()


def player_round(db: Path, element: int, fixture: int) -> dict[str, Any]:
    (row,) = rows(db, "SELECT * FROM player_rounds WHERE element = ? AND fixture = ?",
                  element, fixture)
    return row


def assert_equals_summary_row(stored: dict[str, Any], summary: dict[str, Any]) -> None:
    for key in COMPARED:
        expected = summary[key]
        if key in X_FIELDS:
            expected = float(expected)
        actual = bool(stored[key]) if key in ("was_home", "modified") else stored[key]
        assert actual == expected, (key, stored["element"], stored["fixture"])


@pytest.fixture
def raw(tmp_path) -> Path:
    return tmp_path / "raw"


@pytest.fixture
def db(tmp_path) -> Path:
    return tmp_path / "store" / "season.sqlite"


def test_sync_rebuilds_summary_rows_from_event_live(raw, db):
    season = Season()
    season.write(raw)

    report = sync(raw, db)

    stored = rows(db, "SELECT * FROM player_rounds")
    assert {r["source"] for r in stored} == {"event-live"}
    covered = [row for element in season.summary_ids
               for row in season.summary_rows(element, before_gw=3)]
    assert len(stored) == len(covered) == report.player_rounds
    for summary in covered:
        assert_equals_summary_row(player_round(db, summary["element"], summary["fixture"]),
                                  summary)
    assert report.rounds == (1, 2)


def test_side_from_bps_list_then_bootstrap_union(raw, db):
    season = Season()
    season.clubs[4] = {1: 3, 2: 1, 3: 1}
    season.clubs[5] = {2: 2, 3: 2}
    season.matches += [Match(4, 1, minutes=0), Match(5, 1, minutes=0)]
    season.write(raw)

    sync(raw, db)

    def side(element: int) -> tuple:
        row = player_round(db, element, 1)
        return row["side_rule"], row["team"], row["opponent_team"], row["was_home"]

    assert side(1) == ("bps", 1, 2, 1)
    assert side(2) == ("bps", 2, 1, 0)
    assert side(3) == ("bootstrap", 1, 2, 1)
    assert side(4) == ("bootstrap", 1, 2, 1)
    assert side(5) == ("bootstrap", 2, 1, 0)


def test_unresolved_side_is_listed_not_guessed(raw, db):
    season = Season()
    season.clubs[6] = {1: 1, 2: 2, 3: 2}
    season.matches.append(Match(6, 1, minutes=0, club=2))
    season.write(raw)

    report = sync(raw, db)

    row = player_round(db, 6, 1)
    assert (row["team"], row["opponent_team"], row["was_home"]) == (None, None, None)
    assert row["side_rule"] == "unresolved"
    assert row["minutes"] == 0
    assert [(u.round, u.element, u.fixture) for u in report.unresolved] == [(1, 6, 1)]


def test_unresolved_side_with_a_summary_takes_the_summary_row(raw, db):
    season = Season()
    season.clubs[6] = {1: 1, 2: 2, 3: 2}
    season.matches.append(Match(6, 1, minutes=0, club=2))
    season.summary_ids.add(6)
    season.write(raw)

    report = sync(raw, db)

    row = player_round(db, 6, 1)
    assert (row["source"], row["side_rule"], row["team"]) == ("summary", "summary", 2)
    assert row["source_path"] == "gw2/players/summary-6.json"
    assert_equals_summary_row(row, season.summary_rows(6, before_gw=2)[0])
    assert report.unresolved == ()


def double_gameweek() -> Season:
    season = Season()
    season.fixtures[3] = (2, 1, 3, "2026-08-24T19:00:00Z")
    season.matches[3] = Match(1, 2, minutes=60, goals=1, xg="0.70")
    season.matches += [Match(1, 3, minutes=30, xg="0.20"), Match(3, 3, minutes=0)]
    return season


def test_double_gameweek_without_summary_splits_by_minutes_and_marks_it(raw, db):
    season = double_gameweek()
    season.summary_ids = {2, 3}
    season.write(raw)

    report = sync(raw, db)

    first, second = player_round(db, 1, 2), player_round(db, 1, 3)
    assert (first["split"], second["split"]) == ("minutes", "minutes")
    assert (first["minutes"], second["minutes"]) == (60, 30)
    assert (first["goals_scored"], second["goals_scored"]) == (1, 0)
    assert (first["total_points"], second["total_points"]) == (7, 1)
    assert first["expected_goals"] == pytest.approx(0.6)
    assert second["expected_goals"] == pytest.approx(0.3)
    assert first["bps"] + second["bps"] == 30 + 10
    assert (first["team"], first["was_home"]) == (1, 0)
    assert (second["team"], second["was_home"]) == (1, 1)
    assert [(d.round, d.element, d.fixtures) for d in report.dgw_splits] == [(2, 1, (2, 3))]


def test_double_gameweek_with_summary_uses_the_summary_rows(raw, db):
    season = double_gameweek()
    season.write(raw)

    report = sync(raw, db)

    for summary in season.summary_rows(1, before_gw=3):
        if summary["round"] != 2:
            continue
        stored = player_round(db, 1, summary["fixture"])
        assert (stored["source"], stored["split"]) == ("summary", None)
        assert stored["source_path"] == "gw3/players/summary-1.json"
        assert_equals_summary_row(stored, summary)
    assert report.dgw_splits == ()


def test_a_summary_fetched_before_its_round_is_checked_does_not_cover_it(raw, db):
    season = double_gameweek()
    season.unchecked = {3: {2}}
    season.final_sidecar = {2}
    season.write(raw)

    report = sync(raw, db)

    assert (player_round(db, 1, 2)["source"], player_round(db, 1, 3)["source"]) == (
        "event-live", "event-live")
    assert [(d.round, d.element, d.fixtures) for d in report.dgw_splits] == [
        (2, 1, (2, 3)), (2, 3, (2, 3))]


def test_a_bootstrap_refreshed_after_the_live_fetch_proves_nothing(raw, db):
    season = Season()
    season.write(raw)
    payload = SnapshotStore(raw).load(2, "bootstrap")
    later = fetch_time(2) + timedelta(hours=5)
    SnapshotStore(raw, now=lambda: later).save(2, "bootstrap", payload, "https://x.test")

    with pytest.raises(StoreSyncError, match="gw2/event-live-e1.json"):
        sync(raw, db)


def test_refuses_a_non_final_event_live(raw, db):
    season = Season(live_before_bootstrap={1})
    season.write(raw)

    with pytest.raises(StoreSyncError) as refused:
        sync(raw, db)

    message = str(refused.value)
    assert "gw2/event-live-e1.json" in message
    assert "event-live --gw 2 --round 1 --force" in message
    assert not db.exists()


def test_a_final_sidecar_makes_an_event_live_final(raw, db):
    season = Season(live_before_bootstrap={1}, final_sidecar={1})
    season.write(raw)

    assert sync(raw, db).rounds == (1, 2)


def test_an_event_live_is_final_by_the_shared_rule_only(raw, db):
    """A bootstrap of the round's own gameweek proves nothing, even one that
    shows the round checked before the live snapshot was fetched."""
    season = Season(live_before_bootstrap={1})
    season.write(raw)
    early = fetch_time(2) - timedelta(hours=2)
    save_raw(raw, early, 1, "bootstrap", bootstrap_payload(
        [], [], [event_payload(id=1, deadline_time=DEADLINES[1].isoformat(),
                               finished=True, data_checked=True)]))

    with pytest.raises(StoreSyncError, match="gw2/event-live-e1.json"):
        sync(raw, db)


def test_manifest_finality_matches_live_final(raw, db):
    from fpl.store import live_final

    Season(final_sidecar={1}).write(raw)
    sync(raw, db)

    for row in rows(db, "SELECT path, gw, final FROM manifest WHERE kind = 'event-live'"):
        rnd = int(row["path"].rsplit("-e", 1)[1].removesuffix(".json"))
        assert bool(row["final"]) == (live_final(raw, row["gw"], rnd) is not None)


@pytest.mark.parametrize("bad", [
    ("gw3/players/summary-1.json", {"history": "not rows", "history_past": []}),
    ("gw3/event-live-e1.json", {"elements": "not elements"}),
])
def test_every_raw_file_is_validated_not_only_the_ones_read(raw, db, bad):
    path, payload = bad
    Season(final_sidecar={1}).write(raw)
    gw, name = int(path.split("/")[0][2:]), path.split("/", 1)[1].removesuffix(".json")
    save_raw(raw, fetch_time(gw) + timedelta(hours=4), gw, name, payload)

    with pytest.raises(StoreSyncError, match=path):
        sync(raw, db)


def test_a_file_changed_after_the_scan_refuses(raw, db):
    Season().write(raw)
    files = _scan(raw)
    (raw / "gw2" / "fixtures.json").write_text("[]")

    with pytest.raises(StoreSyncError, match=r"gw2/fixtures\.json.*changed"):
        _build(files)


def test_a_refused_rebuild_leaves_the_existing_store_untouched(raw, db):
    Season().write(raw)
    sync(raw, db)
    before = db.read_bytes()
    payload = SnapshotStore(raw).load(2, "bootstrap")
    save_raw(raw, fetch_time(2) + timedelta(hours=5), 2, "bootstrap", payload)

    with pytest.raises(StoreSyncError, match="gw2/event-live-e1.json"):
        rebuild(raw, db)

    assert db.read_bytes() == before
    assert sorted(p.name for p in db.parent.iterdir()) == [db.name]


def test_an_insert_error_rolls_back_and_leaves_the_store_untouched(raw, db, monkeypatch):
    import fpl.season_store as season_store

    Season().write(raw, range(1, 3))
    sync(raw, db)
    before = db.read_bytes()
    Season().write(raw, range(3, 4))
    real_insert = season_store._insert

    def failing_insert(con, table, table_rows):
        if table == "player_rounds":
            raise sqlite3.IntegrityError("boom")
        real_insert(con, table, table_rows)

    monkeypatch.setattr(season_store, "_insert", failing_insert)

    with pytest.raises(sqlite3.IntegrityError):
        sync(raw, db)

    assert db.read_bytes() == before
    assert sorted(p.name for p in db.parent.iterdir()) == [db.name]


def _empty_sqlite_with_current_version(db: Path) -> None:
    con = sqlite3.connect(db)
    con.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    con.close()


@pytest.mark.parametrize("corrupt", [
    lambda db: db.write_bytes(b"not a sqlite database " * 100),
    _empty_sqlite_with_current_version,
])
def test_a_corrupt_store_is_rebuilt_by_sync_and_refused_by_the_reader(raw, db, corrupt):
    Season().write(raw)
    fresh = db.with_name("fresh.sqlite")
    sync(raw, fresh)
    db.parent.mkdir(parents=True, exist_ok=True)
    corrupt(db)

    with pytest.raises(StoreReadError, match="store rebuild"):
        open_ro(db, raw)
    report = sync(raw, db)

    assert report.files_ingested == len(rows(fresh, "SELECT path FROM manifest"))
    assert dump(db) == dump(fresh)


def test_sync_is_incremental_and_idempotent(raw, db):
    Season().write(raw)
    first = sync(raw, db)
    before = dump(db)

    second = sync(raw, db)

    assert first.files_ingested > 0
    assert second.files_ingested == 0
    assert dump(db) == before
    assert second.player_rounds == first.player_rounds


def test_rebuild_equals_incremental(tmp_path):
    season = Season()
    incremental_raw, incremental_db = tmp_path / "a" / "raw", tmp_path / "a" / "s.sqlite"
    season.write(incremental_raw, range(1, 3))
    assert sync(incremental_raw, incremental_db).rounds == (1,)
    season.write(incremental_raw, range(3, 4))
    added = sync(incremental_raw, incremental_db)

    full_raw, full_db = tmp_path / "b" / "raw", tmp_path / "b" / "s.sqlite"
    season.write(full_raw)
    sync(full_raw, full_db)

    assert added.files_ingested == 3 + len(season.summary_ids)
    assert dump(incremental_db) == dump(full_db)


def test_a_refetch_with_identical_bytes_but_a_new_sidecar_is_reingested(tmp_path):
    season = Season()
    raw, db = tmp_path / "raw", tmp_path / "s.sqlite"
    season.write(raw)
    sync(raw, db)
    path = raw / "gw3" / "event-live-e2.json"
    before = path.read_bytes()
    refetched = fetch_time(3) + timedelta(hours=9)
    SnapshotStore(raw, now=lambda: refetched).save(
        3, "event-live-e2", SnapshotStore(raw).load(3, "event-live-e2"), "https://x.test",
        final=True)
    assert path.read_bytes() == before

    with pytest.raises(StoreReadError, match=r"gw3/event-live-e2\.json changed"):
        open_ro(db, raw)
    again = sync(raw, db)

    assert again.files_ingested == 1
    (live,) = rows(db, "SELECT fetched_at, final FROM manifest "
                       "WHERE path = 'gw3/event-live-e2.json'")
    assert live == {"fetched_at": refetched.isoformat(), "final": 1}
    fresh = tmp_path / "fresh.sqlite"
    sync(raw, fresh)
    assert dump(db) == dump(fresh)


def test_schema_version_mismatch_rebuilds(raw, db):
    Season().write(raw)
    first = sync(raw, db)
    before = dump(db)
    con = sqlite3.connect(db)
    con.execute("PRAGMA user_version = 999")
    con.close()

    again = sync(raw, db)

    assert again.files_ingested == first.files_ingested
    assert rows(db, "PRAGMA user_version")[0]["user_version"] == SCHEMA_VERSION
    assert dump(db) == before


def test_history_past_ingested_once_per_player(raw, db):
    season = Season()
    season.history_past[(2, 1)] = [
        past_season_payload(season_name=name, element_code=900001, total_points=pts)
        for name, pts in (("2021/22", 90), ("2023/24", 120), ("2025/26", 150))
    ]
    season.history_past[(3, 1)] = [
        past_season_payload(season_name="2025/26", element_code=900001, total_points=999)
    ]
    season.write(raw)

    report = sync(raw, db)

    stored = rows(db, "SELECT * FROM history_past WHERE element = 1 ORDER BY season_name")
    assert [(r["season_name"], r["total_points"]) for r in stored] == [
        ("2021/22", 90), ("2023/24", 120), ("2025/26", 150)]
    assert {r["source_path"] for r in stored} == {"gw2/players/summary-1.json"}
    assert {r["code"] for r in stored} == {900001}
    assert [(r["xg_recorded"], r["dc_recorded"]) for r in stored] == [(0, 0), (1, 0), (1, 1)]
    assert report.history_past_players == 3


def test_archives_are_not_ingested(raw, db):
    season = Season()
    season.write(raw)
    refreshed = fetch_time(1) + timedelta(hours=5)
    payload = SnapshotStore(raw).load(1, "bootstrap")
    payload["elements"][0]["web_name"] = "Renamed"
    SnapshotStore(raw, now=lambda: refreshed).save(1, "bootstrap", payload, "https://x.test")
    assert list((raw / "gw1" / ".archive").glob("bootstrap-*.json"))

    sync(raw, db)

    paths = {r["path"] for r in rows(db, "SELECT path FROM manifest")}
    assert not any(".archive" in p or ".meta" in p for p in paths)
    assert "gw1/bootstrap.json" in paths
    state = rows(db, "SELECT web_name, fetched_at FROM player_state WHERE gw = 1 AND element = 1")
    assert state == [{"web_name": "Renamed", "fetched_at": refreshed.isoformat()}]


def test_manifest_records_kind_finality_and_rows(raw, db):
    Season().write(raw)

    sync(raw, db)

    (live,) = rows(db, "SELECT * FROM manifest WHERE path = 'gw2/event-live-e1.json'")
    assert (live["kind"], live["gw"], live["final"], live["ingested_rows"]) == (
        "event-live", 2, 1, 3)
    assert len(live["sha256"]) == 64
    coverage = rows(db, "SELECT gw, element FROM summary_coverage ORDER BY gw, element")
    assert coverage == [{"gw": g, "element": e} for g in (2, 3) for e in (1, 2, 3)]


def test_reconciliation_passes_when_totals_match(raw, db):
    Season().write(raw)

    report = sync(raw, db)

    assert report.mismatches == ()
    assert report.reconciliation_skipped is None


def test_reconciliation_flags_a_total_mismatch(raw, db):
    Season(totals_delta={(3, 1): {"total_points": 1}}).write(raw)

    report = sync(raw, db)

    (line,) = report.mismatches
    assert "element 1" in line and "total_points" in line


def test_reconciliation_is_skipped_when_the_current_event_is_not_data_checked(raw, db):
    Season(unchecked={3: {2}}, final_sidecar={2},
           totals_delta={(3, 1): {"total_points": 1}}).write(raw)

    report = sync(raw, db)

    assert report.mismatches == ()
    assert "event 2" in report.reconciliation_skipped


# --- as-of readers -----------------------------------------------------------


def three_rounds() -> Season:
    """Rounds 1–3 played (gw1–gw4 written); round 3 has a distinctive brace,
    and fixture 5 is a round-4 fixture that is never played."""
    season = Season()
    season.fixtures[4] = (3, 1, 2, "2026-08-29T14:00:00Z")
    season.fixtures[5] = (4, 2, 1, "2026-09-05T14:00:00Z")
    for by_gw in season.clubs.values():
        by_gw[4] = by_gw[3]
    season.matches += [Match(1, 4, goals=2, xg="1.99", bonus=3), Match(2, 4),
                       Match(3, 4, minutes=0)]
    return season


def save_raw(raw: Path, when: datetime, gw: int, name: str, payload: Any) -> None:
    SnapshotStore(raw, now=lambda: when).save(gw, name, payload, "https://x.test")


def test_as_of_excludes_round_r_and_later(raw, db):
    season = three_rounds()
    season.clubs[7] = {4: 1}
    season.write(raw, range(1, 5))
    save_raw(raw, fetch_time(4) + timedelta(hours=2), 4, "players/summary-7", {
        "fixtures": [], "history": [], "history_past": [past_season_payload()]})
    sync(raw, db)

    with open_ro(db, raw) as store:
        rounds = store.rounds(3, [1, 2, 3])
        summaries = {c: store.summaries(3, [1, 2, 3, 7], coverage=c) for c in COVERAGES}
        signed_later = store.summaries(4, [7], coverage="all")
        xg = store.club_match_xg(3)
        schedule = {f.id: f for f in store.fixtures(3)}
        state = store.player_state(3)
        later = store.rounds(4, [1])

    assert {m.round for ms in rounds.values() for m in ms} == {1, 2}
    assert all(m.fixture != 4 for ms in rounds.values() for m in ms)
    for by_id in summaries.values():
        assert set(by_id) == {1, 2, 3}
        assert {m.round for s in by_id.values() for m in s.history} == {1, 2}
    assert set(signed_later) == {7}
    assert set(xg) == {1, 2}
    assert (schedule[4].finished, schedule[4].team_h_score) == (False, None)
    assert state[1].goals_scored == 1
    assert [m.round for m in later[1]] == [1, 2, 3]
    assert later[1][-1].expected_goals == pytest.approx(1.99)


def test_as_of_summaries_equal_raw_summaries_for_covered_ids(raw, db):
    season = double_gameweek()
    season.clubs[4] = {1: 1, 2: 1, 3: 1}
    season.matches.append(Match(4, 1, minutes=20))
    season.write(raw)
    sync(raw, db)
    ids = [1, 2, 3, 4]

    with open_ro(db, raw) as store:
        got = store.summaries(3, ids, coverage="production")
    want = load_cached_summaries(SnapshotStore(raw), 3, ids)

    assert set(got) == set(want) == {1, 2, 3}
    for element, summary in want.items():
        assert got[element].history_past == summary.history_past
        assert [m.model_dump(exclude={"opponent_team"}) for m in got[element].history] == [
            m.model_dump() for m in summary.history]
        raw_rows = SnapshotStore(raw).load(3, f"players/summary-{element}")["history"]
        assert [m.opponent_team for m in got[element].history] == [
            r["opponent_team"] for r in raw_rows]


def league_world() -> Season:
    """Nine shortlisted midfielders with a summary each, and element 20: a
    cheap, unowned midfielder whose only summary was fetched before GW1."""
    season = Season()
    for element in range(10, 18):
        season.clubs[element] = {1: 1, 2: 1, 3: 1}
        season.positions[element] = 3
        season.summary_ids.add(element)
    season.clubs[20] = {1: 2, 2: 2, 3: 2}
    season.positions[20] = 3
    season.player_overrides[20] = {"now_cost": 40, "selected_by_percent": "0.5"}
    return season


def test_coverage_shortlist_pins_the_league_pool(raw, db):
    league_world().write(raw)
    save_raw(raw, fetch_time(1) + timedelta(hours=2), 1, "players/summary-20", {
        "fixtures": [], "history": [], "history_past": [past_season_payload(
            element_code=900020, minutes=2000, goals_scored=30, expected_goals="25.00")],
    })
    sync(raw, db)
    bootstrap = load_cached_bootstrap(SnapshotStore(raw), 3)
    mids = [p for p in bootstrap.elements if p.element_type == Position.MID]
    ids = [p.id for p in mids]
    assert not is_shortlisted(bootstrap.player_by_id()[20])

    with open_ro(db, raw) as store:
        by_coverage = {c: store.summaries(3, ids, coverage=c) for c in COVERAGES}
        pinned = store.summaries(3, ids, coverage="shortlist", pinned=[20])

    assert 20 not in by_coverage["production"]
    assert 20 not in by_coverage["shortlist"]
    assert by_coverage["all"][20].history_past[0].minutes == 2000
    assert 20 in pinned
    league = {c: _league_mean(Position.MID, mids, s) for c, s in by_coverage.items()}
    assert league["production"] == league["shortlist"]
    assert league["all"] != league["shortlist"]
    assert league["all"][2] == league["shortlist"][2] + 1


def test_schedule_comes_from_the_as_of_fixtures_snapshot(raw, db):
    three_rounds().write(raw, range(1, 5))
    moved = SnapshotStore(raw).load(4, "fixtures")
    for fixture in moved:
        if fixture["id"] == 5:
            fixture.update(event=None, kickoff_time=None)
    save_raw(raw, fetch_time(4) + timedelta(hours=3), 4, "fixtures", moved)
    sync(raw, db)

    with open_ro(db, raw) as store:
        as_of_3 = {f.id: f for f in store.fixtures(3)}
        as_of_4 = {f.id: f for f in store.fixtures(4)}

    assert as_of_3[5].event == 4
    assert as_of_3[5].kickoff_time == datetime(2026, 9, 5, 14, tzinfo=timezone.utc)
    assert (as_of_3[5].team_h_difficulty, as_of_3[5].team_a_difficulty) == (2, 4)
    assert (as_of_4[5].event, as_of_4[5].kickoff_time) == (None, None)
    assert as_of_4[4].finished and not as_of_3[4].finished


def test_club_match_xg_equals_fixture_ratings_side_xg(raw, db, tmp_path):
    season = Season()
    season.clubs[4] = {1: 2, 2: 2, 3: 2}
    season.matches += [Match(4, 1, minutes=30, xg="0.33"), Match(4, 2, minutes=15, xg="0.07")]
    season.write(raw)
    sync(raw, db)
    priors = tmp_path / "club-priors.json"
    priors.write_text(json.dumps(priors_doc({f"C{i}": (1.0, 1.0, False) for i in (1, 2, 3)})))
    inputs = load_inputs(SnapshotStore(raw), 3, priors_path=priors,
                         analysis_root=tmp_path / "analysis")
    played = sorted((f for f in inputs.fixtures if f.event is not None and f.event < 3
                     and f.finished), key=lambda f: f.id)
    tally = _side_xg(played, inputs)
    assert tally.recovered > 0

    with open_ro(db, raw) as store:
        got = store.club_match_xg(3)

    assert {fid: (round(h, 2), round(a, 2)) for fid, (h, a) in got.items()} == {
        f.id: (round(tally.xg[(f.id, "H")], 2), round(tally.xg[(f.id, "A")], 2))
        for f in played
    }


def test_reader_refuses_a_store_behind_the_raw(raw, db):
    Season().write(raw)
    sync(raw, db)
    save_raw(raw, fetch_time(3) + timedelta(hours=3), 3, "players/summary-9", {
        "fixtures": [], "history": [], "history_past": []})

    with pytest.raises(StoreReadError) as refused:
        open_ro(db, raw)

    message = str(refused.value)
    assert "gw3/players/summary-9.json" in message
    assert "fpl store sync --gw 3" in message


def test_reader_refuses_a_changed_raw_file_and_a_missing_store(raw, db):
    Season().write(raw)
    sync(raw, db)
    payload = SnapshotStore(raw).load(2, "fixtures")
    save_raw(raw, fetch_time(2) + timedelta(hours=1), 2, "fixtures", payload[:1])

    with pytest.raises(StoreReadError, match=r"gw2/fixtures\.json.*fpl store sync --gw 3"):
        open_ro(db, raw)
    with pytest.raises(StoreReadError, match="fpl store sync --gw 3"):
        open_ro(db.with_name("absent.sqlite"), raw)


def test_reader_never_writes_the_store(raw, db):
    three_rounds().write(raw, range(1, 5))
    sync(raw, db)
    before = db.read_bytes()

    with open_ro(db, raw) as store:
        store.summaries(4, [1, 2, 3], coverage="all")
        store.club_match_xg(4)
        store.player_state(4)

    assert db.read_bytes() == before


def test_as_of_refuses_a_snapshot_fetched_after_its_deadline(raw, db):
    Season(final_sidecar={1, 2}).write(raw)
    payload = SnapshotStore(raw).load(3, "bootstrap")
    save_raw(raw, DEADLINES[3] + timedelta(hours=1), 3, "bootstrap", payload)
    sync(raw, db)

    with open_ro(db, raw) as store:
        with pytest.raises(StoreReadError, match=r"gw3/bootstrap\.json.*deadline"):
            store.summaries(3, [1], coverage="shortlist")
        with pytest.raises(StoreReadError, match=r"gw3/bootstrap\.json"):
            store.player_state(3)
        assert set(store.summaries(3, [1], coverage="production")) == {1}


def test_as_of_refuses_a_round_without_final_live_stats(raw, db):
    Season().write(raw)
    sync(raw, db)

    with open_ro(db, raw) as store:
        with pytest.raises(StoreReadError, match=r"round\(s\) \[3\].*event-live --gw 4 --round 3"):
            store.rounds(4, [1])
