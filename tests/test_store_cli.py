"""CLI tests for `fpl store sync|verify|status|rebuild`: the report lines and
exits, that verify and status write nothing, and that no action needs the
network."""

from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest

from fpl.__main__ import main
from fpl.season_store import sync
from tests.test_season_store import Match, Season, double_gameweek, fetch_time, rows, save_raw


@pytest.fixture
def raw(tmp_path) -> Path:
    return tmp_path / "raw"


@pytest.fixture
def db(tmp_path) -> Path:
    return tmp_path / "store" / "season.sqlite"


def no_network(store):
    raise AssertionError("store commands must not build a network service")


def run(raw: Path, db: Path, action: str, gw: int = 3) -> int:
    return main(["--data-root", str(raw), "store", action, "--gw", str(gw), "--store", str(db)],
                service_factory=no_network)


def tree(path: Path) -> dict[str, tuple[bytes, int]]:
    return {p.relative_to(path).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in sorted(path.rglob("*")) if p.is_file()}


def tamper(db: Path) -> None:
    con = sqlite3.connect(db)
    try:
        con.execute("UPDATE player_rounds SET total_points = 99 WHERE element = 1")
        con.commit()
    finally:
        con.close()


def test_sync_prints_the_report_and_exits_0(raw, db, capsys):
    Season().write(raw)

    assert run(raw, db, "sync") == 0

    out = capsys.readouterr().out.splitlines()
    (count,) = rows(db, "SELECT COUNT(*) AS n FROM player_rounds")
    assert "rounds 1-2" in out
    assert f"player_rounds {count['n']}" in out
    assert "history_past players 3" in out
    assert "unresolved sides 0" in out
    assert "dgw splits 0" in out
    assert "reconciliation: OK" in out


def test_sync_reports_files_ingested_then_none_on_a_second_run(raw, db, capsys):
    Season().write(raw)
    run(raw, db, "sync")
    first = capsys.readouterr().out
    files = len(rows(db, "SELECT path FROM manifest"))

    assert run(raw, db, "sync") == 0

    assert f"{files} files ingested" in first
    assert "0 files ingested" in capsys.readouterr().out


def test_a_seeded_mismatch_prints_it_and_exits_3(raw, db, capsys):
    Season(totals_delta={(3, 1): {"total_points": 1}}).write(raw)

    assert run(raw, db, "sync") == 3

    out = capsys.readouterr().out
    assert "reconciliation: 1 mismatch" in out
    assert "element 1: total_points" in out


def test_a_skipped_reconciliation_names_the_reason_and_exits_0(raw, db, capsys):
    Season(unchecked={3: {2}}, final_sidecar={2}).write(raw)

    assert run(raw, db, "sync") == 0

    assert "reconciliation: skipped (event 2 not data-checked" in capsys.readouterr().out


def test_unresolved_sides_and_dgw_splits_are_listed(raw, db, capsys):
    season = double_gameweek()
    season.summary_ids = {2, 3}
    season.clubs[6] = {1: 1, 2: 2, 3: 2}
    season.matches.append(Match(6, 1, minutes=0, club=2))
    season.write(raw)

    assert run(raw, db, "sync") == 0

    out = capsys.readouterr().out.splitlines()
    assert "unresolved sides 1" in out
    assert "  round 1 element 6 fixture 1" in out
    assert "dgw splits 1" in out
    assert "  round 2 element 1 fixtures 2,3" in out


def test_sync_refusal_exits_1_and_writes_no_store(raw, db, capsys):
    Season(live_before_bootstrap={1}).write(raw)

    assert run(raw, db, "sync") == 1

    assert "not final" in capsys.readouterr().err
    assert not db.exists()


def test_status_prints_the_manifest_summary_and_writes_nothing(raw, db, capsys):
    Season().write(raw)
    sync(raw, db)
    before = tree(db.parent)

    assert run(raw, db, "status") == 0

    out = capsys.readouterr().out
    assert f"store {db}: schema 3" in out
    assert "gw1-3" in out
    assert any(line.split()[:3] == ["event-live", "2", "2"] for line in out.splitlines())
    assert any(line.split()[:2] == ["summary", "6"] for line in out.splitlines())
    assert "rounds 1-2" in out
    assert "in sync with" in out
    assert tree(db.parent) == before


def test_status_names_the_first_raw_change_the_store_has_not_ingested(raw, db, capsys):
    Season().write(raw)
    sync(raw, db)
    save_raw(raw, fetch_time(3) + timedelta(hours=3), 3, "players/summary-9", {
        "fixtures": [], "history": [], "history_past": []})

    assert run(raw, db, "status") == 0

    out = capsys.readouterr().out
    assert "behind" in out and "gw3/players/summary-9.json not ingested" in out
    assert "fpl store sync --gw 3" in out


@pytest.mark.parametrize("action", ["status", "verify"])
def test_a_missing_store_exits_1_naming_sync_and_creates_nothing(raw, db, capsys, action):
    Season().write(raw)

    assert run(raw, db, action) == 1

    assert "fpl store sync --gw 3" in capsys.readouterr().err
    assert not db.parent.exists()


def test_verify_passes_on_a_synced_store_and_writes_nothing(raw, db, capsys):
    Season().write(raw)
    sync(raw, db)
    before = tree(db.parent)
    raw_before = tree(raw)

    assert run(raw, db, "verify") == 0

    out = capsys.readouterr().out
    assert "rounds 1-2" in out
    assert "reconciliation: OK" in out
    assert "content: matches a fresh build" in out
    assert tree(db.parent) == before
    assert tree(raw) == raw_before


def test_verify_refuses_a_store_behind_the_raw(raw, db, capsys):
    Season().write(raw)
    sync(raw, db)
    save_raw(raw, fetch_time(3) + timedelta(hours=3), 3, "players/summary-9", {
        "fixtures": [], "history": [], "history_past": []})

    assert run(raw, db, "verify") == 1

    err = capsys.readouterr().err
    assert "summary-9.json not ingested" in err and "fpl store sync --gw 3" in err


def test_verify_detects_content_that_differs_from_a_fresh_build(raw, db, capsys):
    Season().write(raw)
    sync(raw, db)
    tamper(db)

    assert run(raw, db, "verify") == 1

    out = capsys.readouterr()
    assert "content: differs from a fresh build" in out.out
    assert "fpl store rebuild --gw 3" in out.err


def test_verify_exits_3_on_a_reconciliation_mismatch(raw, db, capsys):
    Season(totals_delta={(3, 1): {"total_points": 1}}).write(raw)
    sync(raw, db)

    assert run(raw, db, "verify") == 3

    assert "reconciliation: 1 mismatch" in capsys.readouterr().out


def test_rebuild_rewrites_a_store_that_sync_leaves_alone(raw, db, capsys):
    Season().write(raw)
    sync(raw, db)
    tamper(db)
    files = len(rows(db, "SELECT path FROM manifest"))

    assert run(raw, db, "sync") == 3
    assert rows(db, "SELECT DISTINCT total_points FROM player_rounds WHERE element = 1") \
        == [{"total_points": 99}]
    capsys.readouterr()

    assert run(raw, db, "rebuild") == 0

    assert f"{files} files ingested" in capsys.readouterr().out
    assert run(raw, db, "verify") == 0
