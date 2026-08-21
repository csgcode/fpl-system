import copy
import csv
import json
import math

import pytest
from pydantic import ValidationError

from fpl.api import BASE_URL, FplApi
from fpl.repository import PLAYERS_SLIM_COLUMNS
from fpl.service import FplDataService, GameweekMismatchError
from fpl.store import SnapshotStore
from tests.factories import (
    bootstrap_payload,
    element_summary_payload,
    entry_history_event_payload,
    entry_history_payload,
    event_payload,
    event_picks_payload,
    fixture_payload,
    match_record_payload,
    past_season_payload,
    pick_payload,
    player_payload,
)
from tests.test_store import FakeClock

BOOTSTRAP_URL = f"{BASE_URL}/bootstrap-static/"
FIXTURES_URL = f"{BASE_URL}/fixtures/"


class FakeGateway:
    def __init__(self, responses: dict) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def get_json(self, url: str):
        self.calls.append(url)
        return copy.deepcopy(self.responses[url])


class SpySleep:
    def __init__(self) -> None:
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def make_service(tmp_path, responses, clock=None, sleep=None, throttle_s=0.0):
    clock = clock or FakeClock()
    gateway = FakeGateway(responses)
    store = SnapshotStore(tmp_path, now=clock)
    service = FplDataService(
        FplApi(gateway),
        store,
        now=clock,
        throttle_s=throttle_s,
        sleep=sleep or (lambda _: None),
    )
    return service, gateway, store, clock


def test_bootstrap_fetches_once_then_serves_from_cache(tmp_path):
    service, gateway, _, _ = make_service(tmp_path, {BOOTSTRAP_URL: bootstrap_payload()})
    service.bootstrap(gw=2)
    service.bootstrap(gw=2)
    assert gateway.calls == [BOOTSTRAP_URL]


def test_fetch_log_reports_fetch_then_cache_hit(tmp_path):
    clock = FakeClock()
    service, _, _, _ = make_service(tmp_path, {BOOTSTRAP_URL: bootstrap_payload()}, clock)
    service.bootstrap(gw=2)
    assert [(e.name, e.fetched) for e in service.take_fetch_log()] == [
        ("bootstrap", True)
    ]

    clock.advance(hours=3)
    service.bootstrap(gw=2)
    (event,) = service.take_fetch_log()
    assert event.fetched is False
    assert event.age_hours == pytest.approx(3.0)
    assert service.take_fetch_log() == ()


def test_stale_snapshot_is_refetched(tmp_path):
    clock = FakeClock()
    service, gateway, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload()}, clock
    )
    service.bootstrap(gw=2)
    clock.advance(hours=25)
    service.bootstrap(gw=2)
    assert gateway.calls == [BOOTSTRAP_URL, BOOTSTRAP_URL]


def test_max_age_boundary_is_inclusive(tmp_path):
    clock = FakeClock()
    service, gateway, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload()}, clock
    )
    service.bootstrap(gw=2, max_age_hours=6)
    clock.advance(hours=6)
    service.bootstrap(gw=2, max_age_hours=6)
    assert gateway.calls == [BOOTSTRAP_URL]

    clock.advance(microseconds=1)
    service.bootstrap(gw=2, max_age_hours=6)
    assert gateway.calls == [BOOTSTRAP_URL, BOOTSTRAP_URL]


def test_force_refetches_and_archives(tmp_path):
    clock = FakeClock()
    service, gateway, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload()}, clock
    )
    service.bootstrap(gw=2)
    clock.advance(hours=1)
    service.bootstrap(gw=2, force=True)
    assert gateway.calls == [BOOTSTRAP_URL, BOOTSTRAP_URL]
    assert list((tmp_path / "gw2" / ".archive").glob("bootstrap-*.json"))


def test_infinite_max_age_uses_snapshot_with_missing_meta(tmp_path):
    service, gateway, store, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload()}
    )
    service.bootstrap(gw=2)
    (tmp_path / "gw2" / ".meta" / "bootstrap.json").unlink()

    service.bootstrap(gw=2, max_age_hours=math.inf)

    assert gateway.calls == [BOOTSTRAP_URL]
    (event,) = service.take_fetch_log()[-1:]
    assert event.fetched is False
    assert event.age_hours is None


def test_infinite_max_age_uses_snapshot_with_corrupt_meta(tmp_path):
    service, gateway, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload()}
    )
    service.bootstrap(gw=2)
    (tmp_path / "gw2" / ".meta" / "bootstrap.json").write_text("{corrupt")

    service.bootstrap(gw=2, max_age_hours=math.inf)

    assert gateway.calls == [BOOTSTRAP_URL]


def test_corrupt_meta_refetches_under_finite_max_age(tmp_path):
    service, gateway, _, clock = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload()}
    )
    service.bootstrap(gw=2)
    (tmp_path / "gw2" / ".meta" / "bootstrap.json").write_text("{corrupt")
    clock.advance(hours=1)

    service.bootstrap(gw=2)

    assert gateway.calls == [BOOTSTRAP_URL, BOOTSTRAP_URL]


def test_infinite_max_age_still_fetches_when_absent(tmp_path):
    service, gateway, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload()}
    )
    service.bootstrap(gw=2, max_age_hours=math.inf)
    assert gateway.calls == [BOOTSTRAP_URL]


def test_invalid_payload_is_never_persisted(tmp_path):
    service, _, store, _ = make_service(tmp_path, {BOOTSTRAP_URL: {"events": "nope"}})
    with pytest.raises(ValidationError):
        service.bootstrap(gw=2)
    assert not store.exists(2, "bootstrap")


def test_dangling_team_reference_is_never_persisted(tmp_path):
    payload = bootstrap_payload(elements=[player_payload(team=99)], teams=[])
    service, _, store, _ = make_service(tmp_path, {BOOTSTRAP_URL: payload})
    with pytest.raises(ValidationError):
        service.bootstrap(gw=2)
    assert not store.exists(2, "bootstrap")


def test_bootstrap_gw_mismatch_refuses_before_saving(tmp_path):
    payload = bootstrap_payload(events=[event_payload(id=7, is_next=True)])
    service, _, store, _ = make_service(tmp_path, {BOOTSTRAP_URL: payload})

    with pytest.raises(GameweekMismatchError) as exc_info:
        service.bootstrap(gw=3, require_next_gw=True)

    assert exc_info.value.payload_gw == 7
    assert not store.exists(3, "bootstrap")


def test_bootstrap_gw_match_saves(tmp_path):
    payload = bootstrap_payload(events=[event_payload(id=3, is_next=True)])
    service, _, store, _ = make_service(tmp_path, {BOOTSTRAP_URL: payload})
    service.bootstrap(gw=3, require_next_gw=True)
    assert store.exists(3, "bootstrap")


def test_bootstrap_gw_mismatch_allowed_when_not_required(tmp_path):
    payload = bootstrap_payload(events=[event_payload(id=7, is_next=True)])
    service, _, store, _ = make_service(tmp_path, {BOOTSTRAP_URL: payload})
    service.bootstrap(gw=3)
    assert store.exists(3, "bootstrap")


def test_fixtures_parse(tmp_path):
    service, _, _, _ = make_service(tmp_path, {FIXTURES_URL: [fixture_payload()]})
    fixtures = service.fixtures(gw=2)
    assert len(fixtures) == 1
    assert fixtures[0].team_h_difficulty == 2


def test_flag_report_forces_refresh(tmp_path):
    flagged = player_payload(id=9, status="d", chance_of_playing_next_round=75)
    clock = FakeClock()
    service, gateway, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload(elements=[flagged])}, clock
    )
    service.bootstrap(gw=2)
    clock.advance(hours=1)
    report = service.flag_report(gw=2, player_ids=[9])
    assert gateway.calls == [BOOTSTRAP_URL, BOOTSTRAP_URL]
    assert report[0].chance_of_playing_next_round == 75


def test_flag_report_rejects_unknown_ids(tmp_path):
    service, _, _, _ = make_service(tmp_path, {BOOTSTRAP_URL: bootstrap_payload()})
    with pytest.raises(ValueError, match="unknown player ids"):
        service.flag_report(gw=2, player_ids=[999])


def test_flag_report_dedupes_ids(tmp_path):
    elements = [player_payload(id=1), player_payload(id=2)]
    service, _, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload(elements=elements)}
    )
    report = service.flag_report(gw=2, player_ids=[2, 1, 2])
    assert [p.id for p in report] == [2, 1]


def test_export_players_csv_excludes_managers(tmp_path):
    elements = [
        player_payload(id=1),
        player_payload(id=2, web_name="Boss", element_type=5),
    ]
    service, _, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload(elements=elements)}
    )
    service.bootstrap(gw=2)
    path = service.export_players_csv(gw=2)

    rows = list(csv.reader(path.open(encoding="utf-8")))
    assert rows[0] == list(PLAYERS_SLIM_COLUMNS)
    assert len(rows) == 2
    assert rows[1][1] == "Alpha"
    assert rows[1][4] == "14.5"


def test_export_players_csv_archives_and_records_provenance(tmp_path):
    clock = FakeClock()
    service, _, store, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload()}, clock
    )
    service.bootstrap(gw=2)
    service.export_players_csv(gw=2)
    clock.advance(hours=1)
    service.export_players_csv(gw=2)

    assert list((tmp_path / "gw2" / ".archive").glob("players-slim-*.csv"))
    meta = json.loads((tmp_path / "gw2" / ".meta" / "players-slim.csv").read_text())
    assert meta["source_url"].startswith("derived://")
    assert meta["fetched_at"]


def test_export_players_csv_writes_non_ascii_names_as_utf8(tmp_path):
    elements = [player_payload(id=1, web_name="Ødegaard")]
    service, _, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload(elements=elements)}
    )
    service.bootstrap(gw=2)
    path = service.export_players_csv(gw=2)
    assert "Ødegaard" in path.read_text(encoding="utf-8")


def test_summaries_throttle_only_between_network_fetches(tmp_path):
    elements = [player_payload(id=1), player_payload(id=2), player_payload(id=3)]
    responses = {
        BOOTSTRAP_URL: bootstrap_payload(elements=elements),
        f"{BASE_URL}/element-summary/1/": element_summary_payload(),
        f"{BASE_URL}/element-summary/2/": element_summary_payload(),
        f"{BASE_URL}/element-summary/3/": element_summary_payload(),
    }
    sleep = SpySleep()
    service, _, _, _ = make_service(tmp_path, responses, sleep=sleep, throttle_s=0.25)

    service.player_summaries(gw=2, player_ids=[1, 2, 3])
    assert sleep.calls == [0.25, 0.25]

    sleep.calls.clear()
    service.player_summaries(gw=2, player_ids=[1, 2, 3])
    assert sleep.calls == []


def test_summaries_dedupe_ids(tmp_path):
    responses = {
        BOOTSTRAP_URL: bootstrap_payload(),
        f"{BASE_URL}/element-summary/1/": element_summary_payload(),
    }
    service, gateway, _, _ = make_service(tmp_path, responses)
    summaries = service.player_summaries(gw=2, player_ids=[1, 1, 1])
    assert list(summaries) == [1]
    assert gateway.calls == [f"{BASE_URL}/element-summary/1/"]


def test_entry_history_and_picks_snapshot_names(tmp_path):
    responses = {
        f"{BASE_URL}/entry/77/history/": entry_history_payload(),
        f"{BASE_URL}/entry/77/event/4/picks/": event_picks_payload(
            active_chip="bboost", picks=[pick_payload(element=5, position=1)]
        ),
    }
    service, _, store, _ = make_service(tmp_path, responses)

    history = service.entry_history(gw=4, team_id=77)
    picks = service.picks(gw=4, team_id=77, event=4)

    assert store.exists(4, "entry-history-77")
    assert store.exists(4, "picks-77-e4")
    assert history.current[0].event == 1
    assert picks.active_chip == "bboost"
    assert picks.picks[0].element == 5


def test_entry_history_serves_from_cache(tmp_path):
    responses = {f"{BASE_URL}/entry/77/history/": entry_history_payload()}
    service, gateway, _, _ = make_service(tmp_path, responses)
    service.entry_history(gw=4, team_id=77)
    service.entry_history(gw=4, team_id=77)
    assert gateway.calls == [f"{BASE_URL}/entry/77/history/"]


def test_entry_history_parses_multiple_events(tmp_path):
    payload = entry_history_payload(
        current=[
            entry_history_event_payload(event=1),
            entry_history_event_payload(event=2, points=48, total_points=109),
        ]
    )
    service, _, _, _ = make_service(
        tmp_path, {f"{BASE_URL}/entry/77/history/": payload}
    )
    history = service.entry_history(gw=4, team_id=77)
    assert [row.total_points for row in history.current] == [61, 109]


def test_actuals_sums_double_gameweek_rows_and_flags_absences(tmp_path):
    elements = [player_payload(id=1), player_payload(id=2)]
    responses = {
        BOOTSTRAP_URL: bootstrap_payload(elements=elements),
        f"{BASE_URL}/element-summary/1/": element_summary_payload(
            history=[
                match_record_payload(fixture=1, round=5, minutes=90, total_points=8,
                                     goals_scored=1, assists=1, bonus=2, bps=30),
                match_record_payload(fixture=2, round=5, minutes=75, total_points=5,
                                     goals_scored=0, assists=1, bonus=1, bps=22),
                match_record_payload(fixture=3, round=6, minutes=90, total_points=2,
                                     goals_scored=0, assists=0, bonus=0, bps=12),
            ]
        ),
        f"{BASE_URL}/element-summary/2/": element_summary_payload(
            history=[match_record_payload(fixture=4, round=6)]
        ),
    }
    service, gateway, _, _ = make_service(tmp_path, responses)
    service.player_summaries(gw=5, player_ids=[1, 2])
    gateway.calls.clear()

    lines = service.actuals(gw=5, player_ids=[1, 2], match_round=5)

    assert len(gateway.calls) == 2  # always refetched, never served from cache
    played, absent = lines
    assert (played.player_id, played.matched) == (1, True)
    assert (played.minutes, played.total_points) == (165, 13)
    assert (played.goals_scored, played.assists) == (1, 2)
    assert (played.bonus, played.bps) == (3, 52)
    assert absent.matched is False
    assert (absent.minutes, absent.total_points, absent.bps) == (0, 0, 0)


def test_actuals_treats_missing_bonus_as_zero(tmp_path):
    responses = {
        f"{BASE_URL}/element-summary/1/": element_summary_payload(
            history=[
                {"fixture": 1, "round": 5, "minutes": 90, "total_points": 3,
                 "goals_scored": 0, "assists": 0}
            ]
        ),
    }
    service, _, _, _ = make_service(tmp_path, responses)
    (line,) = service.actuals(gw=5, player_ids=[1], match_round=5)
    assert (line.matched, line.bonus, line.bps) == (True, 0, 0)


def test_shortlist_summaries_and_prior_season(tmp_path):
    veteran = player_payload(id=1, now_cost=60)
    newcomer = player_payload(id=2, web_name="Newboy", now_cost=75, penalties_order=None)
    unfetched = player_payload(
        id=3, web_name="Missed", selected_by_percent="9.0", now_cost=45,
        penalties_order=None,
    )
    ignored = player_payload(
        id=4, now_cost=45, selected_by_percent="0.5", penalties_order=None
    )
    responses = {
        BOOTSTRAP_URL: bootstrap_payload(elements=[veteran, newcomer, unfetched, ignored]),
        f"{BASE_URL}/element-summary/1/": element_summary_payload(),
        f"{BASE_URL}/element-summary/2/": element_summary_payload(history_past=[]),
    }
    service, _, store, _ = make_service(tmp_path, responses)
    service.bootstrap(gw=2)

    assert service.shortlist_ids(gw=2) == [1, 2, 3]
    service.player_summaries(gw=2, player_ids=[1, 2])
    result = service.build_prior_season(gw=2)

    prior = json.loads(store.path(2, "prior-season").read_text())
    assert set(prior["players"]) == {"1"}
    assert prior["players"]["1"]["season_name"] == "2025/26"
    assert prior["no_pl_history"] == [2]
    assert prior["missing_summaries"] == [3]
    assert (result.players, result.no_pl_history, result.missing_summaries) == (1, 1, 1)


@pytest.mark.parametrize("reverse", [False, True])
def test_prior_season_takes_latest_season_whatever_the_api_order(tmp_path, reverse):
    seasons = [
        past_season_payload(season_name="2024/25", total_points=100),
        past_season_payload(season_name="2025/26", total_points=211),
    ]
    if reverse:
        seasons.reverse()
    responses = {
        BOOTSTRAP_URL: bootstrap_payload(elements=[player_payload(id=1, now_cost=60)]),
        f"{BASE_URL}/element-summary/1/": element_summary_payload(history_past=seasons),
    }
    service, _, store, _ = make_service(tmp_path, responses)
    service.bootstrap(gw=2)
    service.player_summaries(gw=2, player_ids=[1])
    service.build_prior_season(gw=2)

    prior = json.loads(store.path(2, "prior-season").read_text())
    assert prior["players"]["1"]["season_name"] == "2025/26"
    assert prior["players"]["1"]["total_points"] == 211


def test_prior_season_reports_empty_result(tmp_path):
    cheap = player_payload(
        id=1, now_cost=45, selected_by_percent="0.1", penalties_order=None, minutes=0
    )
    service, _, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload(elements=[cheap])}
    )
    service.bootstrap(gw=2)
    result = service.build_prior_season(gw=2)
    assert (result.players, result.missing_summaries) == (0, 0)
