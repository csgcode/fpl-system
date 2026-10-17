"""CLI tests for `fpl history`: read-only agent views over the season store —
per-match and per-round rows of the completed rounds before GW N, past
seasons, and one row per club."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest

from fpl.__main__ import main
from fpl.season_store import sync
from tests.factories import past_season_payload
from tests.test_season_store import Match, Season, double_gameweek, three_rounds


@pytest.fixture
def raw(tmp_path) -> Path:
    return tmp_path / "raw"


@pytest.fixture
def db(tmp_path) -> Path:
    return tmp_path / "store" / "season.sqlite"


def no_network(store):
    raise AssertionError("history must not build a network service")


def run(raw: Path, db: Path, *args: str, gw: int = 4) -> int:
    return main(["--data-root", str(raw), "history", "--gw", str(gw), "--store", str(db),
                 *args], service_factory=no_network)


def csv_rows(capsys) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(capsys.readouterr().out)))


def synced(raw: Path, db: Path, season: Season, gws: range = range(1, 5)) -> None:
    season.write(raw, gws)
    sync(raw, db)


def midfield_world() -> Season:
    """three_rounds plus element 4, a second midfielder at club 2."""
    season = three_rounds()
    season.clubs[4] = {1: 2, 2: 2, 3: 2, 4: 2}
    season.positions[4] = 3
    season.summary_ids.add(4)
    season.matches += [Match(4, 1, minutes=60, xg="0.30"), Match(4, 2, minutes=0),
                       Match(4, 4, minutes=90, xg="0.45")]
    return season


def test_last_k_prints_one_row_per_player_match_of_those_rounds_only(raw, db, capsys):
    synced(raw, db, midfield_world())

    assert run(raw, db, "--position", "MID", "--last", "2", "--format", "csv", "--fields",
               "id,name,round,opp,venue,minutes,xg,xa,points") == 0

    got = csv_rows(capsys)
    assert [(r["id"], r["round"]) for r in got] == [("1", "2"), ("1", "3"), ("4", "2"),
                                                    ("4", "3")]
    assert list(got[0]) == ["id", "name", "round", "opp", "venue", "minutes", "xg", "xa",
                            "points"]
    assert got[1] == {"id": "1", "name": "P1", "round": "3", "opp": "C2", "venue": "H",
                      "minutes": "90", "xg": "1.99", "xa": "0.0", "points": "15"}
    assert (got[2]["opp"], got[2]["venue"]) == ("C1", "H")


def test_ids_limits_the_players(raw, db, capsys):
    synced(raw, db, midfield_world())

    assert run(raw, db, "--ids", "2,3", "--format", "csv", "--fields", "id,round") == 0

    assert {r["id"] for r in csv_rows(capsys)} == {"2", "3"}


def test_per_round_sums_a_double_gameweek(raw, db, capsys):
    synced(raw, db, double_gameweek(), range(1, 4))

    assert run(raw, db, "--ids", "1", "--per", "round", "--format", "csv", "--fields",
               "id,round,fixture,opp,venue,minutes,goals,xg", gw=3) == 0

    got = csv_rows(capsys)
    assert [r["round"] for r in got] == ["1", "2"]
    assert got[1] == {"id": "1", "round": "2", "fixture": "2+3", "opp": "C2+C3",
                      "venue": "A+H", "minutes": "90", "goals": "1", "xg": "0.9"}


def test_per_match_keeps_double_gameweek_fixtures_apart(raw, db, capsys):
    synced(raw, db, double_gameweek(), range(1, 4))

    assert run(raw, db, "--ids", "1", "--format", "csv", "--fields", "round,fixture,minutes",
               gw=3) == 0

    assert [(r["round"], r["fixture"], r["minutes"]) for r in csv_rows(capsys)] == [
        ("1", "1", "90"), ("2", "2", "60"), ("2", "3", "30")]


def past_world() -> Season:
    season = midfield_world()
    season.history_past = {
        (gw, element): [
            past_season_payload(season_name="2024/25", minutes=2000 + element,
                                element_code=900000 + element),
            past_season_payload(season_name="2025/26", minutes=minutes,
                                expected_goals=f"{element}.50",
                                element_code=900000 + element),
        ]
        for gw in range(1, 5)
        for element, minutes in ((1, 2500), (2, 600), (3, 900), (4, 0))
    }
    return season


def test_past_filters_season_and_min_minutes(raw, db, capsys):
    synced(raw, db, past_world())

    assert run(raw, db, "--past", "--season", "2025/26", "--min-minutes", "900",
               "--format", "csv", "--fields", "id,name,minutes,xg") == 0

    assert csv_rows(capsys) == [
        {"id": "1", "name": "P1", "minutes": "2500", "xg": "1.5"},
        {"id": "3", "name": "P3", "minutes": "900", "xg": "3.5"},
    ]


def test_group_by_team_prints_one_row_per_club(raw, db, capsys):
    synced(raw, db, midfield_world())

    assert run(raw, db, "--group-by", "team", "--format", "json", "--fields",
               "team,players,rows,minutes,xg") == 0

    got = json.loads(capsys.readouterr().out)
    assert got == [
        {"team": "C1", "players": 2, "rows": 6, "minutes": 270, "xg": 2.8},
        {"team": "C2", "players": 2, "rows": 6, "minutes": 405, "xg": 0.75},
    ]


def test_group_by_team_labels_matches_of_an_unresolved_side(raw, db, capsys):
    season = midfield_world()
    season.clubs[6] = {1: 1, 2: 2, 3: 2, 4: 2}
    season.positions[6] = 3
    season.matches.append(Match(6, 1, minutes=0, club=2))
    synced(raw, db, season)

    assert run(raw, db, "--ids", "6", "--group-by", "team", "--format", "csv",
               "--fields", "team,players,rows") == 0

    assert csv_rows(capsys) == [{"team": "?", "players": "1", "rows": "1"}]


def test_unknown_ids_exit_1_naming_them(raw, db, capsys):
    synced(raw, db, midfield_world())

    assert run(raw, db, "--ids", "1,98,99", "--format", "csv") == 1

    err = capsys.readouterr().err
    assert "98" in err and "99" in err and "bootstrap" in err


def test_group_by_team_of_past_seasons_uses_the_current_club(raw, db, capsys):
    synced(raw, db, past_world())

    assert run(raw, db, "--past", "--season", "2025/26", "--group-by", "team",
               "--format", "csv", "--fields", "team,players,minutes") == 0

    assert csv_rows(capsys) == [
        {"team": "C1", "players": "2", "minutes": "3400"},
        {"team": "C2", "players": "2", "minutes": "600"},
    ]


def test_table_prints_the_rows_and_a_count(raw, db, capsys):
    synced(raw, db, midfield_world())

    assert run(raw, db, "--ids", "1", "--last", "1") == 0

    out = capsys.readouterr().out.splitlines()
    assert out[0].split()[:4] == ["id", "name", "team", "position"]
    assert out[1].split()[:5] == ["1", "P1", "C1", "MID", "3"]
    assert out[-1] == "(1 row)"


@pytest.mark.parametrize("args, valid", [
    (("--fields", "id,shots"), "id,name,team,position,round,fixture"),
    (("--past", "--fields", "round"), "id,name,team,position,season"),
    (("--group-by", "team", "--fields", "name"), "team,players,rows,minutes"),
])
def test_an_unknown_field_exits_1_listing_valid_fields(raw, db, capsys, args, valid):
    synced(raw, db, midfield_world())

    assert run(raw, db, "--format", "csv", *args) == 1

    err = capsys.readouterr().err
    assert "unknown field" in err and valid in err


@pytest.mark.parametrize("args", [
    ("--season", "2025/26"),
    ("--past", "--per", "round"),
    ("--past", "--last", "2"),
    ("--fields", "id"),
])
def test_conflicting_options_exit_1(raw, db, capsys, args):
    synced(raw, db, midfield_world())

    assert run(raw, db, *args) == 1

    assert "error:" in capsys.readouterr().err


def test_refuses_a_store_behind_the_raw(raw, db, capsys):
    synced(raw, db, midfield_world())
    (raw / "gw4" / "players" / "summary-1.json").write_text("{}", encoding="utf-8")

    assert run(raw, db, "--format", "csv") == 1

    assert "store sync" in capsys.readouterr().err


def test_history_writes_nothing(raw, db):
    synced(raw, db, midfield_world())
    before = {p: p.read_bytes() for p in db.parent.iterdir()}

    assert run(raw, db, "--format", "csv") == 0

    assert {p: p.read_bytes() for p in db.parent.iterdir()} == before
