"""Write-path tests: authenticated gateway config, endpoint URLs, and the
WriteService's deadline gate, idempotency, payload building, and
verify-after-write — all over fakes, never the real API."""

from __future__ import annotations

import json

import pytest
import requests

from fpl import write as write_module
from fpl.api import BASE_URL
from fpl.auth import AuthCredentials
from fpl.state import PlannedPick, PlannedPicks
from fpl.store import SnapshotStore
from fpl.write import (
    AuthenticatedRequestsGateway,
    DeadlineError,
    SessionExpiredError,
    TRANSFERS_URL,
    VerifyMismatchError,
    WriteApi,
    WriteService,
)
from tests.factories import (
    bootstrap_payload,
    event_payload,
    my_team_chip_payload,
    my_team_payload,
    my_team_pick_payload,
    my_team_transfers_payload,
    player_payload,
)
from tests.test_store import FakeClock

SECRET = "synthetic-s3cr3t-token-value"
MY_TEAM_URL = f"{BASE_URL}/my-team/42/"

# id → (element_type, squad slot); captain id 14, vice id 13.
SQUAD = {
    1: (1, 1), 3: (2, 2), 4: (2, 3), 5: (2, 4),
    8: (3, 5), 9: (3, 6), 10: (3, 7), 11: (3, 8),
    13: (4, 9), 14: (4, 10), 15: (4, 11),
    2: (1, 12), 6: (2, 13), 7: (2, 14), 12: (3, 15),
}
EXTRA_PLAYERS = {20: 3, 21: 2, 22: 4}  # transfer-in candidates


# --- gateway --------------------------------------------------------------


class FakeResponse:
    def __init__(self, payload=None, status_code=200, content=b"x") -> None:
        self._payload = payload
        self.status_code = status_code
        self.content = content if payload is None else b"x"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error")

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
        self.cookies: dict[str, str] = {}
        self.adapters: list = []
        self.gets: list[tuple[str, float]] = []
        self.posts: list[tuple[str, dict, float]] = []
        self.closed = False
        self.response = FakeResponse({})

    def mount(self, prefix, adapter) -> None:
        self.adapters.append((prefix, adapter))

    def get(self, url, timeout=None):
        self.gets.append((url, timeout))
        return self.response

    def post(self, url, json=None, timeout=None):
        self.posts.append((url, json, timeout))
        return self.response

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def session(monkeypatch) -> FakeSession:
    fake = FakeSession()
    monkeypatch.setattr(write_module.requests, "Session", lambda: fake)
    return fake


def credentials() -> AuthCredentials:
    return AuthCredentials(
        headers={"X-Api-Authorization": f"Bearer {SECRET}"},
        cookies={"pl_profile": SECRET},
    )


def test_gateway_injects_credentials_without_hardcoding(session):
    AuthenticatedRequestsGateway(credentials())
    assert session.headers["X-Api-Authorization"] == f"Bearer {SECRET}"
    assert session.cookies["pl_profile"] == SECRET
    assert session.headers["User-Agent"] == "fpl-system/1.0"


def test_gateway_retries_are_pinned_to_get_only(session):
    AuthenticatedRequestsGateway(credentials())
    assert session.adapters
    for _, adapter in session.adapters:
        assert tuple(adapter.max_retries.allowed_methods) == ("GET",)


def test_post_json_sends_payload_and_parses_response(session):
    session.response = FakeResponse({"ok": True})
    gateway = AuthenticatedRequestsGateway(credentials(), timeout_s=4.0)
    assert gateway.post_json("https://example.test/x", {"a": 1}) == {"ok": True}
    assert session.posts == [("https://example.test/x", {"a": 1}, 4.0)]


def test_post_json_accepts_an_empty_response_body(session):
    session.response = FakeResponse(content=b"")
    gateway = AuthenticatedRequestsGateway(credentials())
    assert gateway.post_json("https://example.test/x", {}) is None


@pytest.mark.parametrize("status", [401, 403])
@pytest.mark.parametrize("method", ["get_json", "post_json"])
def test_expired_session_raises_a_generic_message(session, status, method):
    session.response = FakeResponse({}, status_code=status)
    gateway = AuthenticatedRequestsGateway(credentials())
    args = ("https://example.test/x",) if method == "get_json" else (
        "https://example.test/x", {},
    )
    with pytest.raises(SessionExpiredError) as exc_info:
        getattr(gateway, method)(*args)
    message = str(exc_info.value)
    assert "session expired" in message
    assert "docs/api-write.md" in message
    assert SECRET not in message


def test_gateway_context_manager_closes_the_session(session):
    with AuthenticatedRequestsGateway(credentials()):
        pass
    assert session.closed


def test_api_endpoint_urls_and_verbs(session):
    session.response = FakeResponse({"picks": []})
    api = WriteApi(AuthenticatedRequestsGateway(credentials()))
    api.my_team(42)
    api.post_lineup(42, {"picks": []})
    api.post_transfers({"entry": 42})
    assert [url for url, _ in session.gets] == [MY_TEAM_URL]
    assert [(url, payload) for url, payload, _ in session.posts] == [
        (MY_TEAM_URL, {"picks": []}),
        (TRANSFERS_URL, {"entry": 42}),
    ]


# --- service fixtures -----------------------------------------------------


class FakeWriteGateway:
    """get_json serves queued responses per URL (last one sticks); post_json
    records every payload."""

    def __init__(self, gets: dict[str, list[dict]]) -> None:
        self._gets = {url: list(queue) for url, queue in gets.items()}
        self.get_calls: list[str] = []
        self.posts: list[tuple[str, dict]] = []

    def get_json(self, url: str):
        self.get_calls.append(url)
        queue = self._gets[url]
        return queue.pop(0) if len(queue) > 1 else queue[0]

    def post_json(self, url: str, payload: dict):
        self.posts.append((url, payload))
        return None


def squad_bootstrap(deadline: str = "2026-08-22T12:00:00Z") -> dict:
    elements = [
        player_payload(
            id=player_id, element_type=element_type, web_name=f"E{player_id}",
            now_cost=50 + player_id, penalties_order=None,
        )
        for player_id, element_type in (
            [(pid, et) for pid, (et, _) in SQUAD.items()] + list(EXTRA_PLAYERS.items())
        )
    ]
    return bootstrap_payload(
        elements=elements, events=[event_payload(id=2, deadline_time=deadline)]
    )


def squad_my_team_picks(squad: dict[int, tuple[int, int]] | None = None) -> list[dict]:
    squad = squad if squad is not None else SQUAD
    return [
        my_team_pick_payload(
            element=player_id, position=slot, element_type=element_type,
            selling_price=40 + player_id, purchase_price=45,
            is_captain=player_id == 14, is_vice_captain=player_id == 13,
        )
        for player_id, (element_type, slot) in sorted(
            squad.items(), key=lambda item: item[1][1]
        )
    ]


def planned_squad(captain: int = 14, vice: int = 13) -> PlannedPicks:
    return PlannedPicks(
        picks=tuple(
            PlannedPick(
                id=player_id, name=f"E{player_id}", position=slot,
                captain=player_id == captain, vice=player_id == vice,
            )
            for player_id, (_, slot) in SQUAD.items()
        )
    )


def make_write_service(tmp_path, my_team_responses, bootstrap=None):
    clock = FakeClock()
    store = SnapshotStore(tmp_path / "raw", now=clock)
    store.save(2, "bootstrap", bootstrap or squad_bootstrap(), "seed://test")
    executor = SnapshotStore(tmp_path / "executor", now=clock)
    gateway = FakeWriteGateway({MY_TEAM_URL: my_team_responses})
    service = WriteService(WriteApi(gateway), store, executor, now=clock)
    return service, gateway, executor, clock


def current_my_team(**kwargs) -> dict:
    return my_team_payload(picks=squad_my_team_picks(), **kwargs)


# --- deadline gate ---------------------------------------------------------


def test_deadline_open_returns_the_deadline(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    deadline = service.ensure_deadline_open(2)
    assert deadline.isoformat() == "2026-08-22T12:00:00+00:00"


def test_passed_deadline_refuses_even_with_override(tmp_path):
    bootstrap = squad_bootstrap(deadline="2026-08-21T11:00:00Z")
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()], bootstrap)
    with pytest.raises(DeadlineError, match="has passed"):
        service.ensure_deadline_open(2)
    with pytest.raises(DeadlineError, match="has passed"):
        service.ensure_deadline_open(2, override_margin=True)


def test_deadline_inside_margin_refuses_unless_overridden(tmp_path):
    bootstrap = squad_bootstrap(deadline="2026-08-21T12:20:00Z")
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()], bootstrap)
    with pytest.raises(DeadlineError, match="--force-deadline"):
        service.ensure_deadline_open(2)
    assert service.ensure_deadline_open(2, override_margin=True) is not None


def test_bootstrap_without_the_gameweek_event_refuses(tmp_path):
    bootstrap = squad_bootstrap()
    bootstrap["events"] = [event_payload(id=5)]
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()], bootstrap)
    with pytest.raises(DeadlineError, match="no deadline"):
        service.ensure_deadline_open(2)


# --- lineup plans ----------------------------------------------------------


def changed_picks() -> PlannedPicks:
    return planned_squad(captain=13, vice=14)


def test_lineup_plan_builds_the_picks_payload_in_position_order(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    plan = service.plan_lineup(team_id=42, picks=changed_picks())
    assert plan.url == MY_TEAM_URL
    assert plan.payload["chip"] is None
    assert [p["position"] for p in plan.payload["picks"]] == list(range(1, 16))
    captain_rows = [p for p in plan.payload["picks"] if p["is_captain"]]
    assert captain_rows == [
        {"element": 13, "position": 9, "is_captain": True, "is_vice_captain": False}
    ]
    assert plan.already_applied is False


def test_lineup_plan_matching_current_state_is_already_applied(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    plan = service.plan_lineup(team_id=42, picks=planned_squad())
    assert plan.already_applied is True


def test_lineup_plan_with_inactive_chip_is_not_already_applied(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    plan = service.plan_lineup(team_id=42, picks=planned_squad(), chip="bboost")
    assert plan.already_applied is False
    assert plan.payload["chip"] == "bboost"


def test_lineup_plan_with_active_chip_is_already_applied(tmp_path):
    payload = my_team_payload(
        picks=squad_my_team_picks(),
        chips=[my_team_chip_payload(name="bboost", status_for_entry="active")],
    )
    service, _, _, _ = make_write_service(tmp_path, [payload])
    plan = service.plan_lineup(team_id=42, picks=planned_squad(), chip="bboost")
    assert plan.already_applied is True


def test_apply_lineup_posts_verifies_and_writes_an_audit_record(tmp_path):
    changed = current_my_team()
    for pick in changed["picks"]:
        pick["is_captain"] = pick["element"] == 13
        pick["is_vice_captain"] = pick["element"] == 14
    service, gateway, executor, _ = make_write_service(
        tmp_path, [current_my_team(), changed]
    )
    plan = service.plan_lineup(team_id=42, picks=changed_picks())
    path = service.apply_lineup(2, plan)
    assert gateway.posts == [(MY_TEAM_URL, plan.payload)]
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["command"] == "set-lineup"
    assert record["verified"] is True
    assert record["payload"] == plan.payload
    assert path.is_relative_to(tmp_path / "executor" / "gw2")


def test_apply_lineup_mismatch_raises_and_still_writes_the_audit_record(tmp_path):
    service, _, executor, _ = make_write_service(
        tmp_path, [current_my_team(), current_my_team()]
    )
    plan = service.plan_lineup(team_id=42, picks=changed_picks())
    with pytest.raises(VerifyMismatchError, match="captain"):
        service.apply_lineup(2, plan)
    (audit,) = [
        p for p in (tmp_path / "executor" / "gw2").iterdir() if p.suffix == ".json"
    ]
    record = json.loads(audit.read_text(encoding="utf-8"))
    assert record["verified"] is False
    assert record["problems"]


def test_write_commands_never_touch_the_raw_snapshot_dir(tmp_path):
    changed = current_my_team()
    for pick in changed["picks"]:
        pick["is_captain"] = pick["element"] == 13
        pick["is_vice_captain"] = pick["element"] == 14
    service, _, _, _ = make_write_service(tmp_path, [current_my_team(), changed])
    raw_before = sorted(p for p in (tmp_path / "raw").rglob("*") if p.is_file())
    plan = service.plan_lineup(team_id=42, picks=changed_picks())
    service.apply_lineup(2, plan)
    raw_after = sorted(p for p in (tmp_path / "raw").rglob("*") if p.is_file())
    assert raw_after == raw_before


# --- formation validation ---------------------------------------------------


def swap_slots(picks: PlannedPicks, id_a: int, id_b: int) -> PlannedPicks:
    slots = {p.id: p.position for p in picks.picks}
    slots[id_a], slots[id_b] = slots[id_b], slots[id_a]
    return PlannedPicks(
        picks=tuple(
            PlannedPick(
                id=p.id, name=p.name, position=slots[p.id],
                captain=p.captain, vice=p.vice,
            )
            for p in picks.picks
        )
    )


def test_valid_formation_passes(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    service.validate_formation(2, planned_squad())


def test_outfielder_in_goal_slot_is_refused(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    with pytest.raises(ValueError, match="position 1 must be a goalkeeper"):
        service.validate_formation(2, swap_slots(planned_squad(), 1, 3))


def test_backup_keeper_off_slot_12_is_refused(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    with pytest.raises(ValueError, match="position 12 must be a goalkeeper"):
        service.validate_formation(2, swap_slots(planned_squad(), 2, 6))


def test_too_few_defenders_in_the_xi_is_refused(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    picks = swap_slots(planned_squad(), 5, 12)  # XI DEF out for a bench MID
    with pytest.raises(ValueError, match="at least 3 DEF"):
        service.validate_formation(2, picks)


def test_unknown_pick_ids_are_refused(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    picks = planned_squad()
    broken = PlannedPicks(
        picks=tuple(
            PlannedPick(
                id=999 if p.id == 15 else p.id, name=p.name, position=p.position,
                captain=p.captain, vice=p.vice,
            )
            for p in picks.picks
        )
    )
    with pytest.raises(ValueError, match="unknown player ids"):
        service.validate_formation(2, broken)


# --- transfer plans ----------------------------------------------------------


def test_transfer_plan_prices_come_from_my_team_and_bootstrap(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    plan = service.plan_transfers(gw=2, team_id=42, out_ids=[12], in_ids=[20])
    assert plan.url == TRANSFERS_URL
    assert plan.payload == {
        "entry": 42,
        "event": 2,
        "transfers": [
            {
                "element_in": 20,
                "element_out": 12,
                "purchase_price": 70,  # bootstrap now_cost for id 20
                "selling_price": 52,  # my-team selling_price for id 12
            }
        ],
        "chip": None,
    }
    assert plan.already_applied is False


def test_transfer_plan_pairs_outs_and_ins_by_position(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    plan = service.plan_transfers(gw=2, team_id=42, out_ids=[12, 6], in_ids=[21, 20])
    pairs = [(r["element_out"], r["element_in"]) for r in plan.payload["transfers"]]
    assert sorted(pairs) == [(6, 21), (12, 20)]


def test_transfer_plan_refuses_position_count_mismatch(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    with pytest.raises(ValueError, match="position"):
        service.plan_transfers(gw=2, team_id=42, out_ids=[6], in_ids=[20])


def test_transfer_plan_from_target_squad_computes_the_diff(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    target = (set(SQUAD) - {12}) | {20}
    plan = service.plan_transfers(gw=2, team_id=42, target_ids=target)
    assert plan.outs == (12,)
    assert plan.ins == (20,)


def test_transfer_plan_already_applied_when_target_matches_squad(tmp_path):
    service, gateway, _, _ = make_write_service(tmp_path, [current_my_team()])
    plan = service.plan_transfers(gw=2, team_id=42, target_ids=set(SQUAD))
    assert plan.already_applied is True
    assert plan.payload["transfers"] == []
    assert gateway.posts == []


def test_transfer_plan_explicit_pairs_already_applied(tmp_path):
    swapped = dict(SQUAD)
    swapped[20] = swapped.pop(12)
    service, _, _, _ = make_write_service(
        tmp_path, [my_team_payload(picks=squad_my_team_picks(swapped))]
    )
    plan = service.plan_transfers(gw=2, team_id=42, out_ids=[12], in_ids=[20])
    assert plan.already_applied is True


def test_partially_applied_transfers_are_refused(tmp_path):
    swapped = dict(SQUAD)
    swapped[20] = swapped.pop(12)
    service, _, _, _ = make_write_service(
        tmp_path, [my_team_payload(picks=squad_my_team_picks(swapped))]
    )
    with pytest.raises(ValueError, match="partially applied"):
        service.plan_transfers(gw=2, team_id=42, out_ids=[12, 6], in_ids=[20, 21])


def test_transfer_plan_estimates_the_hit(tmp_path):
    payload = my_team_payload(
        picks=squad_my_team_picks(),
        transfers=my_team_transfers_payload(limit=1, made=0, cost=4),
    )
    service, _, _, _ = make_write_service(tmp_path, [payload])
    plan = service.plan_transfers(gw=2, team_id=42, out_ids=[12, 6], in_ids=[20, 21])
    assert any("hit" in note and "4" in note for note in plan.notes)


def test_transfer_plan_with_wildcard_has_no_hit(tmp_path):
    service, _, _, _ = make_write_service(tmp_path, [current_my_team()])
    plan = service.plan_transfers(
        gw=2, team_id=42, out_ids=[12, 6], in_ids=[20, 21], chip="wildcard"
    )
    assert plan.payload["chip"] == "wildcard"
    assert any("no hit" in note for note in plan.notes)


def test_apply_transfers_posts_verifies_and_writes_an_audit_record(tmp_path):
    swapped = dict(SQUAD)
    swapped[20] = swapped.pop(12)
    after = my_team_payload(picks=squad_my_team_picks(swapped))
    service, gateway, _, _ = make_write_service(
        tmp_path, [current_my_team(), after]
    )
    plan = service.plan_transfers(gw=2, team_id=42, out_ids=[12], in_ids=[20])
    path = service.apply_transfers(2, plan)
    assert gateway.posts == [(TRANSFERS_URL, plan.payload)]
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["command"] == "make-transfers"
    assert record["verified"] is True


def test_apply_transfers_mismatch_raises(tmp_path):
    service, _, _, _ = make_write_service(
        tmp_path, [current_my_team(), current_my_team()]
    )
    plan = service.plan_transfers(gw=2, team_id=42, out_ids=[12], in_ids=[20])
    with pytest.raises(VerifyMismatchError, match="12"):
        service.apply_transfers(2, plan)
