"""CLI-level tests: they drive main() exactly as a shell would, over a fake
gateway and a tmp_path data root, so argument wiring, exit codes and printed
output are all under test."""

from __future__ import annotations

import argparse
import csv
import io
import json

import pytest
import requests

from fpl.__main__ import (
    MAX_GW,
    _id_list,
    _position_set,
    _status_set,
    _upper_set,
    main,
)
from fpl.api import BASE_URL, FplApi
from fpl.models import PlayerStatus, Position
from fpl.repository import PLAYERS_SLIM_COLUMNS
from fpl.service import FplDataService
from fpl.store import ARCHIVE_STAMP_FORMAT, SnapshotStore
from tests.factories import (
    bootstrap_payload,
    element_summary_payload,
    entry_history_event_payload,
    entry_history_payload,
    event_payload,
    event_picks_payload,
    fixture_payload,
    match_record_payload,
    pick_payload,
    player_payload,
)
from tests.test_service import FakeGateway

BOOTSTRAP_URL = f"{BASE_URL}/bootstrap-static/"
FIXTURES_URL = f"{BASE_URL}/fixtures/"


class ExplodingGateway:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.calls: list[str] = []

    def get_json(self, url: str):
        self.calls.append(url)
        raise self.error


def run(argv, tmp_path, gateway):
    """Runs main() with the real store (real clock) over a fake gateway."""

    def factory(store: SnapshotStore) -> FplDataService:
        return FplDataService(
            FplApi(gateway), store, throttle_s=0.0, sleep=lambda _: None
        )

    return main(["--data-root", str(tmp_path), *argv], service_factory=factory)


def seed(tmp_path, name, payload):
    SnapshotStore(tmp_path).save(1, name, payload, "seed://test")


# --- argument converters -------------------------------------------------


def test_id_list_parses_and_ignores_blanks():
    assert _id_list("1,2, 3,") == [1, 2, 3]


def test_id_list_rejects_non_numeric():
    with pytest.raises(argparse.ArgumentTypeError, match="invalid id list"):
        _id_list("1,x")


def test_position_set_parses_names_case_insensitively():
    assert _position_set("mid,FWD") == frozenset({Position.MID, Position.FWD})


def test_position_set_accepts_gk_alias():
    assert _position_set("GK") == frozenset({Position.GKP})
    assert _position_set("gk,def") == frozenset({Position.GKP, Position.DEF})


def test_position_set_rejects_unknown_position():
    with pytest.raises(argparse.ArgumentTypeError, match="invalid position"):
        _position_set("MID,SWEEPER")


def test_status_set_parses_letters():
    assert _status_set("a, I") == frozenset(
        {PlayerStatus.AVAILABLE, PlayerStatus.INJURED}
    )


def test_status_set_rejects_unknown_letter():
    with pytest.raises(argparse.ArgumentTypeError, match="invalid status"):
        _status_set("a,z")


def test_upper_set_normalises_team_names():
    assert _upper_set("ars, liv") == frozenset({"ARS", "LIV"})


@pytest.mark.parametrize("gw", ["0", "39", "99", "-1", "abc"])
def test_gameweek_outside_the_season_is_rejected(tmp_path, gw, capsys):
    with pytest.raises(SystemExit) as exc_info:
        run(["players", "--gw", gw], tmp_path, FakeGateway({}))
    assert exc_info.value.code == 2
    assert "gameweek" in capsys.readouterr().err.lower()


def test_last_gameweek_of_the_season_is_accepted(tmp_path):
    SnapshotStore(tmp_path).save(MAX_GW, "bootstrap", bootstrap_payload(), "seed://test")
    assert run(["players", "--gw", str(MAX_GW)], tmp_path, FakeGateway({})) == 0


# --- bootstrap caching wiring -------------------------------------------


def test_bootstrap_fetches_then_reports_cache_hit(tmp_path, capsys):
    gateway = FakeGateway({BOOTSTRAP_URL: bootstrap_payload()})

    assert run(["bootstrap", "--gw", "1"], tmp_path, gateway) == 0
    first = capsys.readouterr().out
    assert "(fetched)" in first
    assert "fetched at 20" in first
    assert "players: 1, teams: 1, chips: 1" in first
    assert "next GW: 1" in first

    assert run(["bootstrap", "--gw", "1"], tmp_path, gateway) == 0
    second = capsys.readouterr().out
    assert "(cached, age 0.0h)" in second
    assert gateway.calls == [BOOTSTRAP_URL]


def test_bootstrap_force_refetches(tmp_path, capsys):
    gateway = FakeGateway({BOOTSTRAP_URL: bootstrap_payload()})
    run(["bootstrap", "--gw", "1"], tmp_path, gateway)
    capsys.readouterr()

    assert run(["bootstrap", "--gw", "1", "--force"], tmp_path, gateway) == 0
    assert "(fetched)" in capsys.readouterr().out
    assert gateway.calls == [BOOTSTRAP_URL, BOOTSTRAP_URL]


def test_bootstrap_max_age_zero_refetches(tmp_path, capsys):
    gateway = FakeGateway({BOOTSTRAP_URL: bootstrap_payload()})
    run(["bootstrap", "--gw", "1"], tmp_path, gateway)
    capsys.readouterr()

    assert run(["bootstrap", "--gw", "1", "--max-age", "0"], tmp_path, gateway) == 0
    assert "(fetched)" in capsys.readouterr().out
    assert gateway.calls == [BOOTSTRAP_URL, BOOTSTRAP_URL]


def test_bootstrap_max_age_inf_uses_cache_without_meta(tmp_path, capsys):
    gateway = FakeGateway({BOOTSTRAP_URL: bootstrap_payload()})
    run(["bootstrap", "--gw", "1"], tmp_path, gateway)
    (tmp_path / "gw1" / ".meta" / "bootstrap.json").unlink()
    capsys.readouterr()

    assert run(["bootstrap", "--gw", "1", "--max-age", "inf"], tmp_path, gateway) == 0
    assert "(cached, age unknown)" in capsys.readouterr().out
    assert gateway.calls == [BOOTSTRAP_URL]


def test_bootstrap_refuses_gameweek_mismatch(tmp_path, capsys):
    payload = bootstrap_payload(events=[event_payload(id=1, is_next=True)])
    gateway = FakeGateway({BOOTSTRAP_URL: payload})

    assert run(["bootstrap", "--gw", "2"], tmp_path, gateway) == 1
    captured = capsys.readouterr()
    assert "next gameweek 1" in captured.err
    assert captured.out == ""
    assert not (tmp_path / "gw2" / "bootstrap.json").exists()


def test_bootstrap_gameweek_mismatch_can_be_allowed(tmp_path):
    payload = bootstrap_payload(events=[event_payload(id=1, is_next=True)])
    gateway = FakeGateway({BOOTSTRAP_URL: payload})

    assert run(
        ["bootstrap", "--gw", "2", "--allow-gw-mismatch"], tmp_path, gateway
    ) == 0
    assert (tmp_path / "gw2" / "bootstrap.json").is_file()


def test_fixtures_reports_count_and_cache_state(tmp_path, capsys):
    gateway = FakeGateway({FIXTURES_URL: [fixture_payload(), fixture_payload(id=2)]})
    assert run(["fixtures", "--gw", "1"], tmp_path, gateway) == 0
    assert "(2 fixtures) (fetched)" in capsys.readouterr().out
    assert run(["fixtures", "--gw", "1"], tmp_path, gateway) == 0
    assert "(cached, age 0.0h)" in capsys.readouterr().out


# --- summaries / entry / picks / entry-history ---------------------------


def test_summaries_by_ids_reports_fetched_then_cached(tmp_path, capsys):
    gateway = FakeGateway(
        {
            f"{BASE_URL}/element-summary/1/": element_summary_payload(),
            f"{BASE_URL}/element-summary/2/": element_summary_payload(),
        }
    )
    assert run(["summaries", "--gw", "1", "--ids", "1,2"], tmp_path, gateway) == 0
    assert "(2 fetched, 0 cached)" in capsys.readouterr().out

    assert run(["summaries", "--gw", "1", "--ids", "1,2"], tmp_path, gateway) == 0
    assert "(0 fetched, 2 cached)" in capsys.readouterr().out


def test_summaries_shortlist_reads_cached_bootstrap(tmp_path, capsys):
    elements = [
        player_payload(id=1, now_cost=100),
        player_payload(
            id=2, now_cost=40, selected_by_percent="0.1", penalties_order=None
        ),
    ]
    seed(tmp_path, "bootstrap", bootstrap_payload(elements=elements))
    gateway = FakeGateway({f"{BASE_URL}/element-summary/1/": element_summary_payload()})

    assert run(["summaries", "--gw", "1", "--shortlist"], tmp_path, gateway) == 0
    assert "1 summaries" in capsys.readouterr().out
    assert gateway.calls == [f"{BASE_URL}/element-summary/1/"]


def test_entry_prints_bank_and_value(tmp_path, capsys):
    gateway = FakeGateway(
        {
            f"{BASE_URL}/entry/42/": {
                "id": 42, "name": "Test XI", "last_deadline_bank": 5,
                "last_deadline_value": 1003,
            }
        }
    )
    assert run(["entry", "--gw", "1", "--team-id", "42"], tmp_path, gateway) == 0
    out = capsys.readouterr().out
    assert "entry 42 ('Test XI')" in out
    assert "bank: 5" in out and "value: 1003" in out
    assert "(fetched)" in out


def test_entry_history_prints_one_row_per_event(tmp_path, capsys):
    payload = entry_history_payload(
        current=[
            entry_history_event_payload(event=1),
            entry_history_event_payload(
                event=2, points=48, total_points=109, overall_rank=250000,
                bank=2, value=1005, event_transfers=1, points_on_bench=7,
            ),
        ]
    )
    gateway = FakeGateway({f"{BASE_URL}/entry/42/history/": payload})

    assert run(["entry-history", "--gw", "1", "--team-id", "42"], tmp_path, gateway) == 0
    out = capsys.readouterr().out
    assert "history (2 events) (fetched)" in out
    assert "event" in out and "ovr rank" in out
    rows = [line.split() for line in out.splitlines()[2:]]
    assert rows[0][:4] == ["1", "61", "61", "412345"]
    assert rows[1] == ["2", "48", "109", "250000", "2", "1005", "1", "7"]
    assert (tmp_path / "gw1" / "entry-history-42.json").is_file()


def test_picks_prints_chip_and_captain_markers(tmp_path, capsys):
    payload = event_picks_payload(
        active_chip="3xc",
        picks=[
            pick_payload(element=10, position=1, multiplier=1),
            pick_payload(element=11, position=2, multiplier=3, is_captain=True),
            pick_payload(element=12, position=3, multiplier=1, is_vice_captain=True),
            pick_payload(element=13, position=12, multiplier=0),
        ],
    )
    gateway = FakeGateway({f"{BASE_URL}/entry/42/event/5/picks/": payload})

    assert run(
        ["picks", "--gw", "1", "--team-id", "42", "--event", "5"], tmp_path, gateway
    ) == 0
    out = capsys.readouterr().out
    assert "active chip: 3xc" in out
    rows = [line.split() for line in out.splitlines()[2:]]
    assert rows[0] == ["1", "10", "1"]
    assert rows[1] == ["2", "11", "3", "C"]
    assert rows[2] == ["3", "12", "1", "VC"]
    assert rows[3] == ["12", "13", "0"]
    assert (tmp_path / "gw1" / "picks-42-e5.json").is_file()


def test_picks_without_chip_prints_none(tmp_path, capsys):
    gateway = FakeGateway(
        {f"{BASE_URL}/entry/42/event/5/picks/": event_picks_payload()}
    )
    run(["picks", "--gw", "1", "--team-id", "42", "--event", "5"], tmp_path, gateway)
    assert "active chip: none" in capsys.readouterr().out


# --- actuals -------------------------------------------------------------


def test_actuals_sums_double_gameweek_and_marks_absences(tmp_path, capsys):
    gateway = FakeGateway(
        {
            f"{BASE_URL}/element-summary/1/": element_summary_payload(
                history=[
                    match_record_payload(fixture=1, round=5, minutes=90,
                                         total_points=8, goals_scored=1, assists=1,
                                         bonus=2, bps=30),
                    match_record_payload(fixture=2, round=5, minutes=62,
                                         total_points=5, goals_scored=0, assists=1,
                                         bonus=1, bps=22),
                    match_record_payload(fixture=3, round=6, minutes=90,
                                         total_points=2, goals_scored=0, assists=0,
                                         bonus=0, bps=11),
                ]
            ),
            f"{BASE_URL}/element-summary/2/": element_summary_payload(
                history=[match_record_payload(fixture=4, round=6)]
            ),
        }
    )

    assert run(
        ["actuals", "--gw", "1", "--round", "5", "--ids", "1,2"], tmp_path, gateway
    ) == 0
    out = capsys.readouterr().out
    rows = [line.split() for line in out.splitlines()[2:]]
    assert rows[0] == ["1", "152", "13", "1", "2", "3", "52"]
    assert rows[1] == ["2", "0", "0", "0", "0", "0", "0", "no", "match"]


def test_actuals_always_refetches(tmp_path):
    gateway = FakeGateway(
        {
            f"{BASE_URL}/element-summary/1/": element_summary_payload(
                history=[match_record_payload(round=5)]
            )
        }
    )
    run(["actuals", "--gw", "1", "--round", "5", "--ids", "1"], tmp_path, gateway)
    run(["actuals", "--gw", "1", "--round", "5", "--ids", "1"], tmp_path, gateway)
    assert len(gateway.calls) == 2


def test_actuals_dedupes_repeated_ids(tmp_path, capsys):
    gateway = FakeGateway(
        {
            f"{BASE_URL}/element-summary/1/": element_summary_payload(
                history=[match_record_payload(round=5)]
            )
        }
    )
    run(["actuals", "--gw", "1", "--round", "5", "--ids", "1,1,1"], tmp_path, gateway)
    assert "1 players" in capsys.readouterr().out
    assert len(gateway.calls) == 1


# --- players view --------------------------------------------------------


def players_fixture(tmp_path):
    teams = [
        {"id": 1, "name": "Test Town", "short_name": "TST",
         "strength_attack_home": 1200, "strength_attack_away": 1200,
         "strength_defence_home": 1200, "strength_defence_away": 1200},
        {"id": 2, "name": "Other City", "short_name": "OTH",
         "strength_attack_home": 1100, "strength_attack_away": 1100,
         "strength_defence_home": 1100, "strength_defence_away": 1100},
    ]
    elements = [
        player_payload(id=1, web_name="Keeper", element_type=1, now_cost=45,
                       team=1, selected_by_percent="1.0", penalties_order=None),
        player_payload(id=2, web_name="Backup", element_type=1, now_cost=40,
                       team=2, selected_by_percent="0.5", penalties_order=None,
                       status="i"),
        player_payload(id=3, web_name="Winger", element_type=3, now_cost=95,
                       team=1, selected_by_percent="30.0"),
        player_payload(id=4, web_name="Striker", element_type=4, now_cost=120,
                       team=2, selected_by_percent="40.0"),
        player_payload(id=5, web_name="Gaffer", element_type=5, now_cost=50, team=1),
    ]
    seed(tmp_path, "bootstrap", bootstrap_payload(elements=elements, teams=teams))


def test_players_position_and_price_filter(tmp_path, capsys):
    players_fixture(tmp_path)
    assert run(
        ["players", "--gw", "1", "--position", "GK",
         "--min-price", "4.1", "--max-price", "4.9"],
        tmp_path, FakeGateway({}),
    ) == 0
    out = capsys.readouterr().out
    assert "Keeper" in out
    assert "Backup" not in out
    assert "(1 players)" in out


def test_players_team_status_and_ownership_filters(tmp_path, capsys):
    players_fixture(tmp_path)
    run(["players", "--gw", "1", "--team", "OTH", "--status", "a",
         "--min-ownership", "10"], tmp_path, FakeGateway({}))
    out = capsys.readouterr().out
    assert "Striker" in out and "Backup" not in out


def test_players_shortlist_and_sort_and_limit(tmp_path, capsys):
    players_fixture(tmp_path)
    run(["players", "--gw", "1", "--shortlist", "--sort", "ownership", "--limit", "1"],
        tmp_path, FakeGateway({}))
    out = capsys.readouterr().out
    assert "Striker" in out and "Winger" not in out


def test_players_json_format_carries_every_slim_column(tmp_path, capsys):
    players_fixture(tmp_path)
    run(["players", "--gw", "1", "--position", "FWD", "--format", "json"],
        tmp_path, FakeGateway({}))
    records = json.loads(capsys.readouterr().out)
    assert len(records) == 1
    assert tuple(records[0]) == PLAYERS_SLIM_COLUMNS
    assert records[0]["name"] == "Striker"


def test_players_csv_format_matches_header(tmp_path, capsys):
    players_fixture(tmp_path)
    run(["players", "--gw", "1", "--position", "MID", "--format", "csv"],
        tmp_path, FakeGateway({}))
    rows = list(csv.reader(io.StringIO(capsys.readouterr().out)))
    assert rows[0] == list(PLAYERS_SLIM_COLUMNS)
    assert len(rows[1]) == len(PLAYERS_SLIM_COLUMNS)
    assert rows[1][1] == "Winger"


def test_players_excludes_managers(tmp_path, capsys):
    players_fixture(tmp_path)
    run(["players", "--gw", "1"], tmp_path, FakeGateway({}))
    assert "Gaffer" not in capsys.readouterr().out


def test_players_negative_limit_fails_with_a_message(tmp_path, capsys):
    players_fixture(tmp_path)
    assert run(["players", "--gw", "1", "--limit", "-1"], tmp_path, FakeGateway({})) == 1
    captured = capsys.readouterr()
    assert "must not be negative" in captured.err
    assert captured.out == ""


# --- derived artefacts ---------------------------------------------------


def test_slim_csv_writes_all_columns(tmp_path, capsys):
    players_fixture(tmp_path)
    assert run(["slim-csv", "--gw", "1"], tmp_path, FakeGateway({})) == 0
    assert "players-slim.csv" in capsys.readouterr().out

    rows = list(csv.reader((tmp_path / "gw1" / "players-slim.csv").open(encoding="utf-8")))
    assert rows[0] == list(PLAYERS_SLIM_COLUMNS)
    assert len(rows) == 5  # header + 4 players, manager excluded
    assert (tmp_path / "gw1" / ".meta" / "players-slim.csv").is_file()


def test_prior_season_prints_counts(tmp_path, capsys):
    elements = [
        player_payload(id=1, now_cost=100),
        player_payload(id=2, now_cost=100, web_name="Newboy"),
        player_payload(id=3, now_cost=100, web_name="Unfetched"),
    ]
    seed(tmp_path, "bootstrap", bootstrap_payload(elements=elements))
    seed(tmp_path, "players/summary-1", element_summary_payload())
    seed(tmp_path, "players/summary-2", element_summary_payload(history_past=[]))

    assert run(["prior-season", "--gw", "1"], tmp_path, FakeGateway({})) == 0
    out = capsys.readouterr().out
    assert "players: 1, no_pl_history: 1, missing_summaries: 1" in out


def test_prior_season_exits_2_when_empty(tmp_path, capsys):
    cheap = player_payload(
        id=1, now_cost=40, selected_by_percent="0.1", penalties_order=None
    )
    seed(tmp_path, "bootstrap", bootstrap_payload(elements=[cheap]))

    assert run(["prior-season", "--gw", "1"], tmp_path, FakeGateway({})) == 2
    captured = capsys.readouterr()
    assert "players: 0" in captured.out
    assert "WARNING" in captured.err


def test_flags_prints_header_and_refresh_time(tmp_path, capsys):
    flagged = player_payload(
        id=7, web_name="Crocked", status="i", chance_of_playing_next_round=25,
        news="Knee injury - 50% chance of playing",
        news_added="2026-08-20T09:00:00Z",
    )
    gateway = FakeGateway({BOOTSTRAP_URL: bootstrap_payload(elements=[flagged])})

    assert run(["flags", "--gw", "1", "--ids", "7"], tmp_path, gateway) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("refreshed at 20")
    assert lines[1].split() == ["id", "name", "st", "chance", "news_added", "news"]
    assert "Crocked" in lines[2] and "25%" in lines[2]
    assert "Knee injury" in lines[2]


def test_flags_rejects_unknown_ids(tmp_path, capsys):
    gateway = FakeGateway({BOOTSTRAP_URL: bootstrap_payload()})
    assert run(["flags", "--gw", "1", "--ids", "999"], tmp_path, gateway) == 1
    assert "unknown player ids" in capsys.readouterr().err


# --- error surfaces ------------------------------------------------------


def test_missing_snapshot_prints_hint_with_data_root(tmp_path, capsys):
    assert run(["players", "--gw", "1"], tmp_path, FakeGateway({})) == 1
    captured = capsys.readouterr()
    assert "no snapshot 'bootstrap' for gw1" in captured.err
    assert f"python -m fpl --data-root {tmp_path} bootstrap --gw 1" in captured.err
    assert captured.out == ""


def test_missing_nested_snapshot_hint_names_the_right_command(tmp_path, capsys):
    """A nested snapshot name must not be mistaken for a command name."""
    assert run(["prior-season", "--gw", "1"], tmp_path, FakeGateway({})) == 1
    assert "bootstrap --gw 1" in capsys.readouterr().err


def test_network_failure_is_reported_without_a_traceback(tmp_path, capsys):
    gateway = ExplodingGateway(requests.ConnectionError("connection refused"))
    assert run(["bootstrap", "--gw", "1"], tmp_path, gateway) == 1
    captured = capsys.readouterr()
    assert "network request failed" in captured.err
    assert captured.out == ""


def test_http_error_is_reported_without_a_traceback(tmp_path, capsys):
    gateway = ExplodingGateway(requests.HTTPError("503 Server Error"))
    assert run(["fixtures", "--gw", "1"], tmp_path, gateway) == 1
    assert "503" in capsys.readouterr().err


def test_invalid_payload_is_reported_without_a_traceback(tmp_path, capsys):
    gateway = FakeGateway({BOOTSTRAP_URL: {"events": "nope"}})
    assert run(["bootstrap", "--gw", "1"], tmp_path, gateway) == 1
    captured = capsys.readouterr()
    assert "failed validation" in captured.err
    assert captured.out == ""


def test_archive_collision_is_reported_and_keeps_the_snapshot(tmp_path, capsys):
    gateway = FakeGateway({BOOTSTRAP_URL: bootstrap_payload()})
    run(["bootstrap", "--gw", "1"], tmp_path, gateway)
    store = SnapshotStore(tmp_path)
    stamp = store.fetched_at(1, "bootstrap").strftime(ARCHIVE_STAMP_FORMAT)
    archive_dir = tmp_path / "gw1" / ".archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / f"bootstrap-{stamp}.json").write_text('{"earlier": true}')
    capsys.readouterr()

    assert run(["bootstrap", "--gw", "1", "--force"], tmp_path, gateway) == 1
    assert "refusing to overwrite" in capsys.readouterr().err
    assert (archive_dir / f"bootstrap-{stamp}.json").read_text() == '{"earlier": true}'


def test_non_json_payload_is_reported_without_a_traceback(tmp_path, capsys):
    class ScalarGateway:
        calls: list[str] = []

        def get_json(self, url):
            raise ValueError(f"expected a JSON object or array from {url}, got int")

    assert run(["bootstrap", "--gw", "1"], tmp_path, ScalarGateway()) == 1
    assert "expected a JSON object or array" in capsys.readouterr().err
