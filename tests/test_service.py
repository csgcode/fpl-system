import copy
import csv
import json

import pytest
from pydantic import ValidationError

from fpl.api import BASE_URL, FplApi
from fpl.repository import PLAYERS_SLIM_COLUMNS
from fpl.service import FplDataService
from fpl.store import SnapshotStore
from tests.factories import (
    bootstrap_payload,
    element_summary_payload,
    fixture_payload,
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


def make_service(tmp_path, responses, clock=None):
    clock = clock or FakeClock()
    gateway = FakeGateway(responses)
    store = SnapshotStore(tmp_path, now=clock)
    service = FplDataService(
        FplApi(gateway), store, now=clock, throttle_s=0, sleep=lambda _: None
    )
    return service, gateway, store, clock


def test_bootstrap_fetches_once_then_serves_from_cache(tmp_path):
    service, gateway, _, _ = make_service(tmp_path, {BOOTSTRAP_URL: bootstrap_payload()})
    service.bootstrap(gw=2)
    service.bootstrap(gw=2)
    assert gateway.calls == [BOOTSTRAP_URL]


def test_stale_snapshot_is_refetched(tmp_path):
    clock = FakeClock()
    service, gateway, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload()}, clock
    )
    service.bootstrap(gw=2)
    clock.advance(hours=25)
    service.bootstrap(gw=2)
    assert gateway.calls == [BOOTSTRAP_URL, BOOTSTRAP_URL]


def test_force_refetches_and_archives(tmp_path):
    service, gateway, store, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload()}
    )
    service.bootstrap(gw=2)
    service.bootstrap(gw=2, force=True)
    assert gateway.calls == [BOOTSTRAP_URL, BOOTSTRAP_URL]
    assert list((tmp_path / "gw2" / ".archive").glob("bootstrap-*.json"))


def test_invalid_payload_is_never_persisted(tmp_path):
    service, _, store, _ = make_service(tmp_path, {BOOTSTRAP_URL: {"events": "nope"}})
    with pytest.raises(ValidationError):
        service.bootstrap(gw=2)
    assert not store.exists(2, "bootstrap")


def test_fixtures_parse(tmp_path):
    service, _, _, _ = make_service(tmp_path, {FIXTURES_URL: [fixture_payload()]})
    fixtures = service.fixtures(gw=2)
    assert len(fixtures) == 1
    assert fixtures[0].team_h_difficulty == 2


def test_flag_report_forces_refresh(tmp_path):
    flagged = player_payload(id=9, status="d", chance_of_playing_next_round=75)
    service, gateway, _, _ = make_service(
        tmp_path, {BOOTSTRAP_URL: bootstrap_payload(elements=[flagged])}
    )
    service.bootstrap(gw=2)
    report = service.flag_report(gw=2, player_ids=[9])
    assert gateway.calls == [BOOTSTRAP_URL, BOOTSTRAP_URL]
    assert report[0].chance_of_playing_next_round == 75


def test_flag_report_rejects_unknown_ids(tmp_path):
    service, _, _, _ = make_service(tmp_path, {BOOTSTRAP_URL: bootstrap_payload()})
    with pytest.raises(ValueError, match="unknown player ids"):
        service.flag_report(gw=2, player_ids=[999])


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

    rows = list(csv.reader(path.open()))
    assert rows[0] == list(PLAYERS_SLIM_COLUMNS)
    assert len(rows) == 2
    assert rows[1][1] == "Alpha"
    assert rows[1][4] == "14.5"


def test_shortlist_summaries_and_prior_season(tmp_path):
    veteran = player_payload(id=1, now_cost=60)
    newcomer = player_payload(id=2, web_name="Newboy", now_cost=75, penalties_order=None)
    unfetched = player_payload(id=3, web_name="Missed", selected_by_percent="9.0", now_cost=45)
    cheap = player_payload(id=4, now_cost=40, selected_by_percent="0.5", penalties_order=None)
    responses = {
        BOOTSTRAP_URL: bootstrap_payload(elements=[veteran, newcomer, unfetched, cheap]),
        f"{BASE_URL}/element-summary/1/": element_summary_payload(),
        f"{BASE_URL}/element-summary/2/": element_summary_payload(history_past=[]),
    }
    service, _, store, _ = make_service(tmp_path, responses)
    service.bootstrap(gw=2)

    assert service.shortlist_ids(gw=2) == [1, 2, 3]
    service.player_summaries(gw=2, player_ids=[1, 2])
    service.build_prior_season(gw=2)

    prior = json.loads(store.path(2, "prior-season").read_text())
    assert set(prior["players"]) == {"1"}
    assert prior["players"]["1"]["season_name"] == "2025/26"
    assert prior["no_pl_history"] == [2]
    assert prior["missing_summaries"] == [3]
