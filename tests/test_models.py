import pytest
from pydantic import ValidationError

from fpl.models import (
    Bootstrap,
    ElementSummary,
    EntryHistory,
    EventPicks,
    PastSeason,
    Player,
    Position,
    is_shortlisted,
)
from tests.factories import (
    bootstrap_payload,
    chip_payload,
    element_summary_payload,
    entry_history_event_payload,
    entry_history_payload,
    event_payload,
    event_picks_payload,
    match_record_payload,
    past_season_payload,
    pick_payload,
    player_payload,
)


def test_player_parses_api_string_numbers_and_extra_fields():
    player = Player.model_validate(
        player_payload(form="4.5", selected_by_percent="12.3", expected_goals="0.45")
    )
    assert player.form == 4.5
    assert player.selected_by_percent == 12.3
    assert player.expected_goals == 0.45
    assert player.price_m == 14.5
    assert player.element_type is Position.MID


def test_player_parses_new_scoring_fields():
    player = Player.model_validate(
        player_payload(
            starts=37,
            clean_sheets=19,
            goals_conceded=26,
            expected_goals_conceded="27.56",
            saves=60,
            cost_change_start=-3,
            cost_change_event=-1,
            clearances_blocks_interceptions=37,
            recoveries=304,
            tackles=1,
        )
    )
    assert player.starts == 37
    assert player.clean_sheets == 19
    assert player.goals_conceded == 26
    assert player.expected_goals_conceded == 27.56
    assert player.saves == 60
    assert player.cost_change_start == -3
    assert player.cost_change_event == -1
    assert player.clearances_blocks_interceptions == 37
    assert player.recoveries == 304
    assert player.tackles == 1


def test_player_rejects_missing_id():
    payload = player_payload()
    del payload["id"]
    with pytest.raises(ValidationError):
        Player.model_validate(payload)


def test_player_rejects_missing_new_required_field():
    payload = player_payload()
    del payload["starts"]
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


NO_DISJUNCT_MET = {
    "now_cost": 45,
    "selected_by_percent": "0.1",
    "penalties_order": None,
    "minutes": 0,
    "defensive_contribution": 0.0,
}


def shortlist_case(**overrides):
    return {**NO_DISJUNCT_MET, **overrides}


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        (shortlist_case(), False),
        (shortlist_case(now_cost=46), True),
        (shortlist_case(now_cost=45), False),
        (shortlist_case(selected_by_percent="2.0"), True),
        (shortlist_case(selected_by_percent="1.9"), False),
        (shortlist_case(penalties_order=2), True),
        (shortlist_case(penalties_order=3), False),
        (shortlist_case(minutes=900), True),
        (shortlist_case(minutes=899), False),
        (shortlist_case(minutes=90, defensive_contribution=8.0), True),
        (shortlist_case(minutes=90, defensive_contribution=7.9), False),
        (shortlist_case(minutes=0, defensive_contribution=500.0), False),
        (shortlist_case(minutes=90, defensive_contribution=None), False),
    ],
)
def test_shortlist_rule_disjuncts(overrides, expected):
    assert is_shortlisted(Player.model_validate(player_payload(**overrides))) is expected


@pytest.mark.parametrize("status", ["u", "n"])
def test_shortlist_excludes_unavailable_and_not_eligible(status):
    premium = player_payload(now_cost=145, selected_by_percent="50.0", status=status)
    assert not is_shortlisted(Player.model_validate(premium))


@pytest.mark.parametrize("status", ["a", "d", "i", "s"])
def test_shortlist_keeps_other_statuses(status):
    premium = player_payload(now_cost=145, status=status)
    assert is_shortlisted(Player.model_validate(premium))


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


def test_bootstrap_parses_chips():
    bootstrap = Bootstrap.model_validate(
        bootstrap_payload(
            chips=[
                chip_payload(name="wildcard", start_event=2, stop_event=19),
                chip_payload(id=2, name="3xc", start_event=20, stop_event=38),
            ]
        )
    )
    assert [c.name for c in bootstrap.chips] == ["wildcard", "3xc"]
    assert bootstrap.chips[1].start_event == 20
    assert bootstrap.chips[1].stop_event == 38


def test_bootstrap_rejects_element_referencing_unknown_team():
    payload = bootstrap_payload(
        elements=[player_payload(id=1, team=1), player_payload(id=2, team=99)],
        teams=[],
    )
    with pytest.raises(ValidationError, match="unknown team ids"):
        Bootstrap.model_validate(payload)


def test_bootstrap_accepts_fully_referenced_elements():
    payload = bootstrap_payload(elements=[player_payload(id=1, team=1)])
    assert len(Bootstrap.model_validate(payload).elements) == 1


def test_event_requires_data_checked():
    payload = event_payload()
    del payload["data_checked"]
    with pytest.raises(ValidationError):
        Bootstrap.model_validate(bootstrap_payload(events=[payload]))


def test_past_season_rejects_malformed_season_name():
    with pytest.raises(ValidationError):
        PastSeason.model_validate(past_season_payload(season_name="2025-26"))


def test_past_season_parses_extended_stats():
    season = PastSeason.model_validate(
        past_season_payload(
            goals_conceded=25,
            clean_sheets=16,
            expected_goals_conceded="26.09",
            starts=34,
            saves=0,
            bonus=9,
            bps=604,
        )
    )
    assert season.goals_conceded == 25
    assert season.clean_sheets == 16
    assert season.expected_goals_conceded == 26.09
    assert season.starts == 34
    assert season.bonus == 9
    assert season.bps == 604


def test_match_record_parses_extended_stats_and_tolerates_absence():
    summary = ElementSummary.model_validate(
        element_summary_payload(
            history=[
                match_record_payload(),
                {"fixture": 11, "minutes": 0, "total_points": 0,
                 "goals_scored": 0, "assists": 0},
            ]
        )
    )
    full, sparse = summary.history
    assert (full.goals_conceded, full.clean_sheets, full.saves) == (1, 0, 0)
    assert (full.bonus, full.bps, full.starts) == (1, 23, 1)
    assert full.expected_goals_conceded == 1.20
    assert sparse.bonus is None
    assert sparse.bps is None
    assert sparse.starts is None


def test_entry_history_parses_current_rows():
    history = EntryHistory.model_validate(
        entry_history_payload(
            current=[
                entry_history_event_payload(event=1, points=61, total_points=61),
                entry_history_event_payload(
                    event=2, points=48, total_points=109, overall_rank=None
                ),
            ]
        )
    )
    assert [row.event for row in history.current] == [1, 2]
    assert history.current[0].overall_rank == 412345
    assert history.current[1].overall_rank is None
    assert history.current[1].points_on_bench == 4


def test_entry_history_tolerates_sparse_rows():
    history = EntryHistory.model_validate({"current": [{"event": 7}]})
    row = history.current[0]
    assert row.event == 7
    assert row.points is None
    assert row.value is None


def test_entry_history_defaults_to_no_events():
    assert EntryHistory.model_validate({}).current == ()


def test_event_picks_parses_captain_markers_and_chip():
    picks = EventPicks.model_validate(
        event_picks_payload(
            active_chip="3xc",
            picks=[
                pick_payload(element=10, position=1, multiplier=1),
                pick_payload(element=11, position=2, multiplier=3, is_captain=True),
                pick_payload(element=12, position=3, is_vice_captain=True),
                pick_payload(element=13, position=12, multiplier=0),
            ],
        )
    )
    assert picks.active_chip == "3xc"
    assert [p.element for p in picks.picks] == [10, 11, 12, 13]
    assert picks.picks[1].is_captain and picks.picks[1].multiplier == 3
    assert picks.picks[2].is_vice_captain
    assert picks.picks[3].multiplier == 0


def test_event_picks_tolerates_missing_chip_and_sparse_pick():
    picks = EventPicks.model_validate({"picks": [{"element": 5}]})
    assert picks.active_chip is None
    assert picks.picks[0].position is None
    assert picks.picks[0].multiplier is None
    assert picks.picks[0].is_captain is False
