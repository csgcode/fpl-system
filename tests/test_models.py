import pytest
from pydantic import ValidationError

from fpl.models import Bootstrap, Player, Position, is_shortlisted
from tests.factories import bootstrap_payload, event_payload, player_payload


def test_player_parses_api_string_numbers_and_extra_fields():
    player = Player.model_validate(
        player_payload(form="4.5", selected_by_percent="12.3", expected_goals="0.45")
    )
    assert player.form == 4.5
    assert player.selected_by_percent == 12.3
    assert player.expected_goals == 0.45
    assert player.price_m == 14.5
    assert player.element_type is Position.MID


def test_player_rejects_missing_id():
    payload = player_payload()
    del payload["id"]
    with pytest.raises(ValidationError):
        Player.model_validate(payload)


def test_player_rejects_out_of_range_price():
    with pytest.raises(ValidationError):
        Player.model_validate(player_payload(now_cost=999))


def test_player_rejects_unknown_status():
    with pytest.raises(ValidationError):
        Player.model_validate(player_payload(status="x"))


def test_manager_element_type_parses_but_never_shortlists():
    manager = Player.model_validate(
        player_payload(element_type=5, now_cost=150, selected_by_percent="20.0")
    )
    assert manager.element_type is Position.MNG
    assert not is_shortlisted(manager)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"now_cost": 55, "selected_by_percent": "0.1", "penalties_order": None}, True),
        ({"now_cost": 54, "selected_by_percent": "4.9", "penalties_order": None}, False),
        ({"now_cost": 40, "selected_by_percent": "0.1", "penalties_order": 2}, True),
        ({"now_cost": 40, "selected_by_percent": "0.1", "penalties_order": 3}, False),
        ({"now_cost": 40, "selected_by_percent": "5.0", "penalties_order": None}, True),
    ],
)
def test_shortlist_rule(overrides, expected):
    assert is_shortlisted(Player.model_validate(player_payload(**overrides))) is expected


def test_bootstrap_gw_helpers():
    bootstrap = Bootstrap.model_validate(
        bootstrap_payload(
            events=[
                event_payload(id=1, is_current=True, is_next=False, finished=True),
                event_payload(id=2, is_current=False, is_next=True),
            ]
        )
    )
    assert bootstrap.current_gw() == 1
    assert bootstrap.next_gw() == 2
    assert bootstrap.next_deadline() is not None
