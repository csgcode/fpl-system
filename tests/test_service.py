import copy
import csv
import json
import math

import pytest
from pydantic import ValidationError

from fpl.api import BASE_URL, FplApi
from fpl.repository import PLAYERS_SLIM_COLUMNS
from fpl.service import FplDataService, GameweekMismatchError, PostDeadlineError
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


def test_flag_check_reports_baseline_age_and_stale(tmp_path):
    clock = FakeClock()
    service, _, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload(elements=[player_payload(id=9)])}, clock
    )
    service.bootstrap(gw=2)
    clock.advance(hours=25)

    check = service.flag_check(gw=2, player_ids=[9])

    assert check.baseline_age_hours == pytest.approx(25.0)
    assert check.stale is True
    document = check.to_document(2)
    assert document["baseline"]["age_hours"] == pytest.approx(25.0)
    assert document["baseline"]["stale"] is True


def test_flag_check_with_an_explicit_baseline_has_unknown_age(tmp_path):
    old = tmp_path / "old.json"
    old.write_text(json.dumps(bootstrap_payload(elements=[player_payload(id=9)])))
    service, _, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload(elements=[player_payload(id=9)])}
    )

    check = service.flag_check(gw=2, player_ids=[9], baseline_path=old)

    assert check.baseline_age_hours is None
    assert check.stale is False


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


def test_summaries_default_throttle_is_a_tenth_of_a_second(tmp_path):
    responses = {
        BOOTSTRAP_URL: bootstrap_payload(),
        f"{BASE_URL}/element-summary/1/": element_summary_payload(),
        f"{BASE_URL}/element-summary/2/": element_summary_payload(),
    }
    clock = FakeClock()
    sleep = SpySleep()
    service = FplDataService(
        FplApi(FakeGateway(responses)),
        SnapshotStore(tmp_path, now=clock),
        now=clock,
        sleep=sleep,
    )

    service.player_summaries(gw=2, player_ids=[1, 2])
    assert sleep.calls == [0.1]


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
    assert played.expected_goals == pytest.approx(0.88)
    assert played.expected_assists == pytest.approx(0.20)
    assert played.defensive_contribution == 6.0
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
    assert (line.expected_goals, line.expected_assists, line.defensive_contribution) == (0.0, 0.0, 0.0)


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


def seed_checked_bootstrap(store, gw, *, checked=(), unchecked=()):
    events = [
        event_payload(id=r, finished=True, data_checked=r in checked, is_next=False)
        for r in sorted({*checked, *unchecked})
    ] + [event_payload(id=gw, is_next=True)]
    store.save(gw, "bootstrap", bootstrap_payload(events=events), "seed://test")


def test_event_live_fetches_once_then_serves_from_cache(tmp_path):
    from tests.factories import event_live_payload, live_element_payload

    url = f"{BASE_URL}/event/1/live/"
    service, gateway, store, _ = make_service(
        tmp_path, {url: event_live_payload([live_element_payload(element_id=7)])}
    )
    seed_checked_bootstrap(store, 2, checked=(1,))
    live = service.event_live(gw=2, event=1)
    assert live.by_id()[7].total_points == 6
    service.event_live(gw=2, event=1)
    assert gateway.calls == [url]
    assert store.exists(2, "event-live-e1")


EVENT_LIVE_E7_URL = f"{BASE_URL}/event/7/live/"


def _final_event_live_service(tmp_path):
    from tests.factories import event_live_payload, live_element_payload

    service, gateway, store, clock = make_service(
        tmp_path,
        {EVENT_LIVE_E7_URL: event_live_payload([live_element_payload(element_id=7)])},
    )
    seed_checked_bootstrap(store, 8, checked=(7,))
    store.save(
        8, "event-live-e7", event_live_payload([live_element_payload(element_id=7)]),
        EVENT_LIVE_E7_URL, final=True, basis="bootstrap gw8 shows event 7 data_checked",
    )
    return service, gateway, store, clock


def test_final_snapshot_is_served_past_max_age(tmp_path):
    service, gateway, _, clock = _final_event_live_service(tmp_path)
    clock.advance(hours=100)

    live = service.event_live(gw=8, event=7, max_age_hours=24)

    assert live.by_id()[7].total_points == 6
    assert gateway.calls == []
    (event,) = service.take_fetch_log()
    assert event.fetched is False
    assert event.final is True
    assert event.age_hours == pytest.approx(100.0)


def test_force_refetches_a_final_snapshot_and_archives_it(tmp_path):
    service, gateway, store, clock = _final_event_live_service(tmp_path)
    clock.advance(hours=1)

    service.event_live(gw=8, event=7, force=True)

    assert gateway.calls == [EVENT_LIVE_E7_URL]
    archived = list((tmp_path / "gw8" / ".archive").glob("event-live-e7-*.json"))
    assert len(archived) == 1
    (event,) = service.take_fetch_log()
    assert event.fetched is True
    assert store.age_hours(8, "event-live-e7") == pytest.approx(0.0)


def test_non_final_snapshot_still_honours_max_age(tmp_path):
    from tests.factories import event_live_payload

    service, gateway, store, clock = make_service(
        tmp_path, {EVENT_LIVE_E7_URL: event_live_payload()}
    )
    seed_checked_bootstrap(store, 8, checked=(7,))
    store.save(8, "event-live-e7", event_live_payload(), EVENT_LIVE_E7_URL)
    service.event_live(gw=8, event=7)
    clock.advance(hours=25)
    service.event_live(gw=8, event=7)

    assert gateway.calls == [EVENT_LIVE_E7_URL]
    assert [e.final for e in service.take_fetch_log()] == [False, True]
    assert store.is_final(8, "event-live-e7") is True


def test_event_live_refuses_a_round_that_is_not_data_checked(tmp_path):
    from tests.factories import event_live_payload

    service, gateway, store, _ = make_service(
        tmp_path, {EVENT_LIVE_E7_URL: event_live_payload()}
    )
    seed_checked_bootstrap(store, 8, unchecked=(7,))

    with pytest.raises(ValueError, match="bootstrap --gw 8 --force"):
        service.event_live(gw=8, event=7)
    assert gateway.calls == []
    assert not store.exists(8, "event-live-e7")


def test_event_live_refuses_a_round_missing_from_the_bootstrap(tmp_path):
    service, gateway, store, _ = make_service(tmp_path, {})
    seed_checked_bootstrap(store, 8, checked=(6,))

    with pytest.raises(ValueError, match="no event 7"):
        service.event_live(gw=8, event=7)
    assert gateway.calls == []


def test_event_live_needs_a_cached_bootstrap(tmp_path):
    from fpl.store import SnapshotMissingError

    service, gateway, _, _ = make_service(tmp_path, {})

    with pytest.raises(SnapshotMissingError) as excinfo:
        service.event_live(gw=8, event=7)
    assert excinfo.value.fetch_hint == "bootstrap --gw 8"
    assert gateway.calls == []


def test_event_live_fetched_after_the_check_is_final_with_its_basis(tmp_path):
    from tests.factories import event_live_payload

    service, _, store, clock = make_service(
        tmp_path, {EVENT_LIVE_E7_URL: event_live_payload()}
    )
    seed_checked_bootstrap(store, 8, checked=(7,))
    bootstrap_time = clock.now
    clock.advance(hours=30)

    service.event_live(gw=8, event=7)

    meta = store.meta(8, "event-live-e7")
    assert meta["final"] is True
    assert meta["basis"] == (
        f"bootstrap gw8 fetched {bootstrap_time.isoformat()} shows event 7 data_checked"
    )
    assert "reason" not in meta
    (event,) = service.take_fetch_log()
    assert (event.fetched, event.final) == (True, True)


def test_final_when_decides_finality_at_fetch_time(tmp_path):
    from fpl.models import EventLive
    from tests.factories import event_live_payload

    service, gateway, store, clock = make_service(
        tmp_path, {EVENT_LIVE_E7_URL: event_live_payload()}
    )
    seen = []

    def final_when(parsed):
        seen.append(parsed)
        return True, "checked"

    service._load_or_fetch(
        8, "event-live-e7", lambda: service._api.event_live(7),
        EventLive.model_validate, 24, False, final_when=final_when,
    )

    assert len(seen) == 1 and isinstance(seen[0], EventLive)
    assert store.meta(8, "event-live-e7")["final"] is True
    assert store.meta(8, "event-live-e7")["basis"] == "checked"
    (event,) = service.take_fetch_log()
    assert (event.fetched, event.final) == (True, True)

    clock.advance(hours=72)
    seed_checked_bootstrap(store, 8, checked=(7,))
    service.event_live(gw=8, event=7)
    assert gateway.calls == [EVENT_LIVE_E7_URL]


def test_final_when_records_why_a_snapshot_is_not_final(tmp_path):
    from fpl.models import EventLive
    from tests.factories import event_live_payload

    service, _, store, _ = make_service(
        tmp_path, {EVENT_LIVE_E7_URL: event_live_payload()}
    )
    service._load_or_fetch(
        8, "event-live-e7", lambda: service._api.event_live(7),
        EventLive.model_validate, 24, False,
        final_when=lambda _: (False, "event 7 not data_checked"),
    )

    meta = store.meta(8, "event-live-e7")
    assert meta["final"] is False
    assert meta["reason"] == "event 7 not data_checked"
    assert "basis" not in meta


# --- deadline: final picks, post-deadline write guard ----------------------

PASSED_DEADLINE = "2026-08-20T17:30:00Z"
OPEN_DEADLINE = "2026-08-28T17:30:00Z"
PICKS_E7_URL = f"{BASE_URL}/entry/77/event/7/picks/"


def seed_deadline_bootstrap(store, gw, deadlines):
    events = [
        event_payload(id=event, deadline_time=deadline, is_next=event == gw)
        for event, deadline in deadlines.items()
    ]
    store.save(gw, "bootstrap", bootstrap_payload(events=events), "seed://test")


def seed_picks_bootstrap(store, *, finished, data_checked):
    events = [
        event_payload(id=7, deadline_time=PASSED_DEADLINE, finished=finished,
                      data_checked=data_checked, is_next=False),
        event_payload(id=8, deadline_time=OPEN_DEADLINE, is_next=True),
    ]
    store.save(8, "bootstrap", bootstrap_payload(events=events), "seed://test")


def test_picks_of_a_data_checked_event_are_final(tmp_path):
    service, gateway, store, clock = make_service(
        tmp_path, {PICKS_E7_URL: event_picks_payload()}
    )
    seed_picks_bootstrap(store, finished=True, data_checked=True)
    bootstrap_time = clock.now
    clock.advance(hours=2)

    service.picks(gw=8, team_id=77, event=7)

    meta = store.meta(8, "picks-77-e7")
    assert meta["final"] is True
    assert meta["basis"] == (
        f"bootstrap gw8 fetched {bootstrap_time.isoformat()} shows event 7 data_checked"
    )
    (event,) = service.take_fetch_log()
    assert (event.fetched, event.final) == (True, True)

    clock.advance(hours=100)
    service.picks(gw=8, team_id=77, event=7)
    assert gateway.calls == [PICKS_E7_URL]
    (event,) = service.take_fetch_log()
    assert (event.fetched, event.final) == (False, True)


@pytest.mark.parametrize("finished", [False, True])
def test_picks_past_the_deadline_of_an_unchecked_event_are_not_final(tmp_path, finished):
    service, _, store, clock = make_service(tmp_path, {PICKS_E7_URL: event_picks_payload()})
    seed_picks_bootstrap(store, finished=finished, data_checked=False)
    bootstrap_time = clock.now

    service.picks(gw=8, team_id=77, event=7)

    meta = store.meta(8, "picks-77-e7")
    assert meta["final"] is False
    assert meta["reason"] == (
        f"event 7 not finished/data_checked in bootstrap gw8 fetched "
        f"{bootstrap_time.isoformat()}"
    )
    assert "basis" not in meta


def test_picks_of_the_open_event_are_not_final(tmp_path):
    url = f"{BASE_URL}/entry/77/event/8/picks/"
    service, _, store, _ = make_service(tmp_path, {url: event_picks_payload()})
    seed_picks_bootstrap(store, finished=True, data_checked=True)

    service.picks(gw=8, team_id=77, event=8)

    meta = store.meta(8, "picks-77-e8")
    assert meta["final"] is False
    assert meta["reason"].startswith("event 8 not finished/data_checked in bootstrap gw8")


def test_picks_without_a_cached_bootstrap_are_not_final(tmp_path):
    service, _, store, _ = make_service(tmp_path, {PICKS_E7_URL: event_picks_payload()})

    service.picks(gw=8, team_id=77, event=7)

    meta = store.meta(8, "picks-77-e7")
    assert meta["final"] is False
    assert meta["reason"] == "no readable cached gw8 bootstrap shows event 7 data_checked"


def test_summaries_into_a_past_gw_refuse_after_its_deadline(tmp_path):
    summary_url = f"{BASE_URL}/element-summary/1/"
    service, gateway, store, _ = make_service(
        tmp_path,
        {
            summary_url: element_summary_payload(),
            BOOTSTRAP_URL: bootstrap_payload(),
            FIXTURES_URL: [fixture_payload()],
        },
    )
    seed_deadline_bootstrap(store, 6, {6: PASSED_DEADLINE})

    with pytest.raises(PostDeadlineError) as excinfo:
        service.player_summaries(gw=6, player_ids=[1], force=True)
    assert "gw6 deadline (2026-08-20T17:30:00+00:00) has passed" in str(excinfo.value)
    assert "--allow-post-deadline" not in str(excinfo.value)
    with pytest.raises(PostDeadlineError):
        service.fixtures(gw=6)
    assert gateway.calls == []
    assert not store.exists(6, "players/summary-1")
    assert not store.exists(6, "fixtures")


def deadline_bootstrap_payload(gw, deadline):
    return bootstrap_payload(
        events=[event_payload(id=gw, deadline_time=deadline, is_next=True)]
    )


def test_bootstrap_refresh_learns_a_postponed_deadline(tmp_path):
    service, gateway, store, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: deadline_bootstrap_payload(8, OPEN_DEADLINE)}
    )
    seed_deadline_bootstrap(store, 8, {8: PASSED_DEADLINE})

    refreshed = service.bootstrap(gw=8, force=True)

    assert gateway.calls == [BOOTSTRAP_URL]
    assert refreshed.deadline_for(8).isoformat() == "2026-08-28T17:30:00+00:00"
    assert store.load(8, "bootstrap")["events"][0]["deadline_time"] == OPEN_DEADLINE


def test_bootstrap_refresh_refuses_a_passed_deadline_in_the_fresh_payload(tmp_path):
    service, gateway, store, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: deadline_bootstrap_payload(6, PASSED_DEADLINE)}
    )
    seed_deadline_bootstrap(store, 6, {6: OPEN_DEADLINE})
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    with pytest.raises(PostDeadlineError, match="gw6 deadline"):
        service.bootstrap(gw=6, force=True)

    assert gateway.calls == [BOOTSTRAP_URL]
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_bootstrap_refresh_into_a_past_gw_with_the_override_saves(tmp_path):
    service, _, store, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: deadline_bootstrap_payload(6, PASSED_DEADLINE)}
    )

    service.bootstrap(gw=6, force=True, allow_post_deadline=True)

    assert store.exists(6, "bootstrap")


def test_flags_refresh_learns_a_postponed_deadline(tmp_path):
    service, gateway, store, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: deadline_bootstrap_payload(8, OPEN_DEADLINE)}
    )
    seed_deadline_bootstrap(store, 8, {8: PASSED_DEADLINE})

    check = service.flag_check(gw=8, player_ids=[1])

    assert gateway.calls == [BOOTSTRAP_URL]
    assert [p.id for p in check.players] == [1]
    assert store.load(8, "bootstrap")["events"][0]["deadline_time"] == OPEN_DEADLINE


@pytest.mark.parametrize("corrupt", ["{not json", '{"events": "nope"}'])
def test_unreadable_cached_bootstrap_means_deadline_unknown(tmp_path, corrupt):
    summary_url = f"{BASE_URL}/element-summary/1/"
    service, gateway, store, _ = make_service(
        tmp_path,
        {
            summary_url: element_summary_payload(),
            BOOTSTRAP_URL: deadline_bootstrap_payload(8, OPEN_DEADLINE),
            PICKS_E7_URL: event_picks_payload(),
        },
    )
    seed_deadline_bootstrap(store, 8, {8: OPEN_DEADLINE})
    store.path(8, "bootstrap").write_text(corrupt)

    service.player_summaries(gw=8, player_ids=[1], force=True)
    service.picks(gw=8, team_id=77, event=7)
    assert store.meta(8, "picks-77-e7")["reason"] == (
        "no readable cached gw8 bootstrap shows event 7 data_checked"
    )
    service.bootstrap(gw=8, force=True)

    assert gateway.calls == [summary_url, PICKS_E7_URL, BOOTSTRAP_URL]
    assert store.load(8, "bootstrap")["events"][0]["deadline_time"] == OPEN_DEADLINE


def test_post_deadline_guard_allows_cache_hits_and_the_override(tmp_path):
    summary_url = f"{BASE_URL}/element-summary/1/"
    service, gateway, store, _ = make_service(
        tmp_path, {summary_url: element_summary_payload()}
    )
    seed_deadline_bootstrap(store, 6, {6: PASSED_DEADLINE})

    service.bootstrap(gw=6)
    service.player_summaries(gw=6, player_ids=[1], allow_post_deadline=True)
    assert gateway.calls == [summary_url]

    service.player_summaries(gw=6, player_ids=[1])
    assert gateway.calls == [summary_url]


def test_summaries_into_an_open_gw_are_not_guarded(tmp_path):
    summary_url = f"{BASE_URL}/element-summary/1/"
    service, gateway, store, _ = make_service(
        tmp_path, {summary_url: element_summary_payload()}
    )
    seed_deadline_bootstrap(store, 7, {6: PASSED_DEADLINE, 7: OPEN_DEADLINE})

    service.player_summaries(gw=7, player_ids=[1], force=True)

    assert gateway.calls == [summary_url]


def test_event_live_is_not_guarded_by_the_gw_deadline(tmp_path):
    from tests.factories import event_live_payload

    url = f"{BASE_URL}/event/6/live/"
    service, gateway, store, _ = make_service(tmp_path, {url: event_live_payload()})
    events = [
        event_payload(id=6, deadline_time=PASSED_DEADLINE, finished=True,
                      data_checked=True, is_next=False),
        event_payload(id=7, deadline_time=PASSED_DEADLINE, is_next=True),
    ]
    store.save(7, "bootstrap", bootstrap_payload(events=events), "seed://test")

    service.event_live(gw=7, event=6)

    assert gateway.calls == [url]
