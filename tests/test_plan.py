"""Execution-plan tests: the plan is a pure function of a final.md STATE block
plus the cached bootstrap, so every case here runs offline over synthetic
payloads. The transfer-resolution and chip-window rules carry the most risk —
a wrong id or a wrong chip drives an irreversible POST."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from fpl.models import Bootstrap
from fpl.plan import (
    LINEUP_CHIPS,
    LINEUP_TARGET,
    SCHEMA_VERSION,
    TRANSFER_CHIPS,
    TRANSFERS_TARGET,
    build_plan,
    parse_plan,
    route_chip,
)
from fpl.state import DecisionState, PlannedPick, PlannedPicks
from tests.factories import (
    bootstrap_payload,
    chip_payload,
    event_payload,
    player_payload,
    team_payload,
)

DEADLINE = "2026-08-22T12:00:00Z"

# id -> (element_type, team, squad slot). 2 GKP / 5 DEF / 5 MID / 3 FWD,
# 3 per club, XI 1-11 is a 3-4-3.
SQUAD = {
    1: (1, 1, 1),
    3: (2, 1, 2),
    4: (2, 2, 3),
    5: (2, 2, 4),
    8: (3, 3, 5),
    9: (3, 3, 6),
    10: (3, 4, 7),
    11: (3, 4, 8),
    13: (4, 5, 9),
    14: (4, 5, 10),
    15: (4, 1, 11),
    2: (1, 2, 12),
    6: (2, 3, 13),
    7: (2, 4, 14),
    12: (3, 5, 15),
}
CAPTAIN, VICE = 14, 13

# Not in the squad: transfer candidates, a club-5 midfielder that would take
# that club to four, plus two players sharing a web_name.
EXTRAS = {20: (3, 6), 21: (2, 6), 22: (4, 6), 23: (1, 6), 24: (3, 5), 30: (3, 6), 31: (2, 6)}
AMBIGUOUS_NAME = "Hughes"
AMBIGUOUS_IDS = (30, 31)

CHIP_WINDOWS = (
    ("wildcard", 2, 19),
    ("wildcard", 20, 38),
    ("freehit", 2, 19),
    ("freehit", 20, 38),
    ("bboost", 1, 19),
    ("bboost", 20, 38),
    ("3xc", 1, 19),
    ("3xc", 20, 38),
)


def player_name(player_id: int) -> str:
    return AMBIGUOUS_NAME if player_id in AMBIGUOUS_IDS else f"E{player_id}"


def bootstrap(deadline: str = DEADLINE) -> Bootstrap:
    roster = {pid: (et, team) for pid, (et, team, _) in SQUAD.items()} | EXTRAS
    elements = [
        player_payload(
            id=pid,
            element_type=element_type,
            team=team,
            web_name=player_name(pid),
            now_cost=40 + pid,
            penalties_order=None,
        )
        for pid, (element_type, team) in sorted(roster.items())
    ]
    return Bootstrap.model_validate(
        bootstrap_payload(
            elements=elements,
            teams=[
                team_payload(id=n, name=f"Club {n}", short_name=f"T{n}")
                for n in range(1, 7)
            ],
            events=[
                event_payload(id=1, is_next=False, finished=True),
                event_payload(id=2, deadline_time=deadline),
            ],
            chips=[
                chip_payload(name=name, start_event=start, stop_event=stop)
                for name, start, stop in CHIP_WINDOWS
            ],
        )
    )


def planned(squad: dict[int, tuple[int, int, int]] | None = None) -> PlannedPicks:
    squad = squad if squad is not None else SQUAD
    return PlannedPicks(
        picks=tuple(
            PlannedPick(
                id=pid,
                name=player_name(pid),
                position=slot,
                captain=pid == CAPTAIN,
                vice=pid == VICE,
            )
            for pid, (_, _, slot) in squad.items()
        )
    )


def swapped(out_id: int, in_id: int) -> dict[int, tuple[int, int, int]]:
    element_type, team, slot = SQUAD[out_id]
    squad = {pid: value for pid, value in SQUAD.items() if pid != out_id}
    squad[in_id] = (element_type, team, slot)
    return squad


DEFAULT_PICKS = object()


def state(
    *,
    gw: int = 2,
    picks: PlannedPicks | None | object = DEFAULT_PICKS,
    team_id: int | None = 42,
    chip: str | None = None,
    chips_used: list[dict] | None = None,
    chip_plan: list[dict] | None = None,
    transfers_made: list[dict] | None = None,
    free_transfers_banked: int = 1,
    bank: float = 1.0,
    team_value: float = 99.9,
) -> DecisionState:
    return DecisionState(
        gw=gw,
        team_id=team_id,
        team_value=team_value,
        bank=bank,
        free_transfers_banked=free_transfers_banked,
        chips_used=chips_used or [],
        transfers_made=transfers_made or [],
        chip=chip,
        chip_plan=chip_plan or [],
        picks=planned() if picks is DEFAULT_PICKS else picks,
    )


def plan(**kwargs):
    kwargs.setdefault("gw", 2)
    kwargs.setdefault("state", state())
    kwargs.setdefault("bootstrap", bootstrap())
    kwargs.setdefault("source", "data/decisions/gw2/final.md")
    kwargs.setdefault("bootstrap_source", "data/raw/gw2/bootstrap.json")
    return build_plan(**kwargs)


def transfer(out: str, into: str, cost: int = 0) -> dict:
    return {"out": out, "into": into, "cost": cost}


# --- shape ------------------------------------------------------------------


def test_plan_carries_schema_version_gw_team_and_deadline():
    result = plan()
    assert result.schema_version == SCHEMA_VERSION
    assert result.gw == 2
    assert result.team_id == 42
    assert result.deadline.isoformat().startswith("2026-08-22T12:00:00")
    assert result.source == "data/decisions/gw2/final.md"
    assert result.generated_from.bootstrap == "data/raw/gw2/bootstrap.json"


def test_picks_are_enriched_with_club_position_price_and_slot():
    picks = {p.element: p for p in plan().picks}
    haaland_like = picks[14]
    assert haaland_like.name == "E14"
    assert haaland_like.club == "T5"
    assert haaland_like.position == "FWD"
    assert haaland_like.slot == 10
    assert haaland_like.is_captain is True
    assert haaland_like.now_cost == pytest.approx(5.4)
    assert haaland_like.starts is True
    assert picks[12].starts is False


def test_picks_are_emitted_in_slot_order():
    assert [p.slot for p in plan().picks] == list(range(1, 16))


def test_formation_and_bench_are_derived_not_inferred():
    result = plan()
    assert result.formation == "3-4-3"
    assert result.bench == (2, 6, 7, 12)


def test_captain_and_vice_refs():
    result = plan()
    assert (result.captain.id, result.captain.name) == (14, "E14")
    assert (result.vice.id, result.vice.name) == (13, "E13")


def test_bootstrap_snapshot_age_is_carried():
    assert plan(bootstrap_age_hours=3.5).bootstrap_snapshot_age_hours == 3.5


def test_null_team_id_warns_without_failing():
    result = plan(state=state(team_id=None))
    assert result.team_id is None
    assert any("team_id is null" in w for w in result.warnings)


# --- transfers --------------------------------------------------------------


def test_transfers_come_from_the_previous_gw_id_diff():
    """The diff is name-free, so an ambiguous web_name costs nothing here."""
    result = plan(
        state=state(
            picks=planned(swapped(12, 30)),
            transfers_made=[transfer("E12", AMBIGUOUS_NAME)],
        ),
        previous_state=state(gw=1, picks=planned()),
    )
    assert result.transfer_source == "picks-diff"
    assert [(t.out.id, t.into.id) for t in result.transfers] == [(12, 30)]
    assert (result.transfers[0].out.name, result.transfers[0].into.name) == (
        "E12",
        AMBIGUOUS_NAME,
    )


def test_transfers_fall_back_to_names_when_the_previous_gw_has_no_picks():
    result = plan(
        state=state(picks=planned(swapped(12, 20)), transfers_made=[transfer("E12", "E20")]),
        previous_state=state(gw=1, picks=None),
    )
    assert result.transfer_source == "state-names"
    assert [(t.out.id, t.into.id) for t in result.transfers] == [(12, 20)]


def test_no_previous_state_at_all_uses_names():
    result = plan(
        state=state(picks=planned(swapped(12, 20)), transfers_made=[transfer("E12", "E20")])
    )
    assert result.transfer_source == "state-names"


def test_no_transfers_reports_source_none():
    result = plan(previous_state=state(gw=1, picks=planned()))
    assert result.transfers == ()
    assert result.transfer_source == "none"


def test_ambiguous_transfer_name_refuses_and_names_every_candidate():
    with pytest.raises(ValueError) as exc_info:
        plan(
            state=state(
                picks=planned(swapped(12, 30)),
                transfers_made=[transfer("E12", AMBIGUOUS_NAME)],
            )
        )
    message = str(exc_info.value)
    assert "ambiguous" in message
    assert "'Hughes'" in message
    for candidate in ("id 30", "id 31", "T6", "MID", "DEF", "7.0", "7.1"):
        assert candidate in message
    assert "disambiguate" in message


def test_unknown_transfer_name_refuses():
    with pytest.raises(ValueError, match="no player named 'Nobody'"):
        plan(
            state=state(
                picks=planned(swapped(12, 20)), transfers_made=[transfer("E12", "Nobody")]
            )
        )


def test_incoming_player_must_be_in_this_gws_picks():
    with pytest.raises(ValueError, match="E21.*not in the gw2 squad"):
        plan(
            state=state(
                picks=planned(swapped(12, 20)), transfers_made=[transfer("E12", "E21")]
            )
        )


def test_outgoing_player_must_not_be_in_this_gws_picks():
    with pytest.raises(ValueError, match="E11.*still in the gw2 squad"):
        plan(
            state=state(
                picks=planned(swapped(12, 20)), transfers_made=[transfer("E11", "E20")]
            )
        )


def test_diff_and_names_disagreement_refuses_showing_both_readings():
    with pytest.raises(ValueError) as exc_info:
        plan(
            state=state(
                picks=planned(swapped(12, 20)), transfers_made=[transfer("E11", "E20")]
            ),
            previous_state=state(gw=1, picks=planned()),
        )
    message = str(exc_info.value)
    assert "disagree" in message
    assert "picks diff" in message and "transfers_made" in message
    assert "E12" in message and "E11" in message


def test_transfers_must_swap_position_for_position():
    previous = {pid: value for pid, value in SQUAD.items() if pid != 12}
    previous[21] = (2, 6, 15)  # previous squad ran a DEF in that slot
    with pytest.raises(ValueError, match="position-for-position"):
        plan(
            state=state(picks=planned(), transfers_made=[transfer("E21", "E12")]),
            previous_state=state(gw=1, picks=planned(previous)),
        )


def test_empty_transfers_made_against_a_changed_squad_warns():
    result = plan(
        state=state(picks=planned(swapped(12, 20))),
        previous_state=state(gw=1, picks=planned()),
    )
    assert [(t.out.id, t.into.id) for t in result.transfers] == [(12, 20)]
    assert any("transfers_made is empty" in w for w in result.warnings)


def test_selling_price_is_never_frozen_into_the_plan():
    result = plan(
        state=state(picks=planned(swapped(12, 20)), transfers_made=[transfer("E12", "E20")])
    )
    assert result.price_resolution == "live"
    assert result.transfers[0].selling_price is None
    assert result.transfers[0].purchase_price_at_plan == pytest.approx(6.0)
    assert "my-team" in result.price_resolution_note


# --- transfer cost ----------------------------------------------------------


def test_hit_warning_uses_the_previous_gws_free_transfer_count():
    result = plan(
        state=state(
            picks=planned(swapped(12, 20)),
            transfers_made=[transfer("E12", "E20")],
        ),
        previous_state=state(gw=1, picks=planned(), free_transfers_banked=0),
    )
    assert any("-4 pts" in w and "gw1 STATE" in w for w in result.warnings)


def test_no_hit_warning_when_transfers_fit_the_free_allowance():
    result = plan(
        state=state(picks=planned(swapped(12, 20)), transfers_made=[transfer("E12", "E20")]),
        previous_state=state(gw=1, picks=planned(), free_transfers_banked=1),
    )
    assert result.warnings == ()


def test_hit_warning_falls_back_to_this_gws_count_with_a_caveat():
    result = plan(
        state=state(
            picks=planned(swapped(12, 20)),
            transfers_made=[transfer("E12", "E20")],
            free_transfers_banked=0,
        )
    )
    assert any("NEXT deadline" in w for w in result.warnings)


def test_wildcard_means_no_hit():
    result = plan(
        state=state(
            picks=planned(swapped(12, 20)),
            transfers_made=[transfer("E12", "E20")],
            chip="wildcard",
            free_transfers_banked=0,
        )
    )
    assert any("wildcard" in w and "no hit" in w for w in result.warnings)
    assert not any("-4 pts" in w for w in result.warnings)


# --- chips ------------------------------------------------------------------


def test_chip_must_appear_in_the_bootstrap_chips_array():
    with pytest.raises(ValueError, match="unknown chip 'megaboost'"):
        plan(state=state(chip="megaboost"))


def narrow_bootstrap() -> Bootstrap:
    """Only the second-half wildcard window exists."""
    payload = bootstrap().model_dump(mode="json")
    payload["chips"] = [{"name": "wildcard", "start_event": 20, "stop_event": 38}]
    return Bootstrap.model_validate(payload)


def test_chip_outside_its_window_refuses_with_the_window():
    with pytest.raises(ValueError) as exc_info:
        plan(state=state(chip="wildcard"), bootstrap=narrow_bootstrap())
    message = str(exc_info.value)
    assert "outside" in message and "wildcard" in message and "20-38" in message


def test_chip_already_used_in_the_same_window_refuses():
    with pytest.raises(ValueError, match="already used"):
        plan(state=state(chip="bboost", chips_used=[{"chip": "bboost", "gw": 1}]))


def test_the_same_chip_in_the_other_window_is_allowed():
    result = plan(
        gw=2, state=state(gw=2, chip="bboost", chips_used=[{"chip": "bboost", "gw": 25}])
    )
    assert result.chip == "bboost"


def test_chips_available_excludes_used_and_expired_windows():
    result = plan(state=state(chips_used=[{"chip": "3xc", "gw": 1}]))
    available = {(c.name, c.start_event, c.stop_event) for c in result.chips_available}
    assert ("3xc", 1, 19) not in available
    assert ("3xc", 20, 38) in available
    assert ("wildcard", 2, 19) in available


def test_chip_plan_is_enriched_with_bootstrap_windows():
    result = plan(
        state=state(chip_plan=[{"chip": "3xc", "gw": 5, "status": "provisional"}])
    )
    earmark = result.chip_plan[0]
    assert (earmark.chip, earmark.gw, earmark.status) == ("3xc", 5, "provisional")
    assert (earmark.start_event, earmark.stop_event) == (1, 19)


def test_chip_plan_outside_a_window_warns_but_does_not_fail():
    result = plan(state=state(chip_plan=[{"chip": "wildcard", "gw": 1}]))
    assert result.chip_plan[0].start_event is None
    assert any("chip_plan" in w and "wildcard" in w for w in result.warnings)


def test_absent_chip_plan_is_an_empty_list():
    assert plan().chip_plan == ()


# --- squad legality ---------------------------------------------------------


def test_missing_picks_refuses():
    with pytest.raises(ValueError, match="no 'picks:' section"):
        plan(state=state(picks=None))


def test_unknown_element_id_refuses():
    with pytest.raises(ValueError, match="unknown player ids"):
        plan(state=state(picks=planned(swapped(12, 999))))


def test_wrong_squad_shape_refuses():
    with pytest.raises(ValueError, match="2 GKP / 5 DEF / 5 MID / 3 FWD"):
        plan(state=state(picks=planned(swapped(12, 21))))


def test_more_than_three_players_from_one_club_refuses():
    with pytest.raises(ValueError, match="max 3 per club exceeded: T5 4"):
        plan(state=state(picks=planned(swapped(8, 24))))


def test_illegal_xi_shape_refuses():
    squad = dict(SQUAD)
    squad[5] = (2, 2, 15)  # third starting DEF benched
    squad[12] = (3, 5, 4)  # midfielder into the XI -> 2 DEF starting
    with pytest.raises(ValueError, match="at least 3 DEF"):
        plan(state=state(picks=planned(squad)))


def test_goalkeeper_must_hold_slot_one():
    squad = dict(SQUAD)
    squad[1] = (1, 1, 2)
    squad[3] = (2, 1, 1)
    with pytest.raises(ValueError, match="position 1 must be a goalkeeper"):
        plan(state=state(picks=planned(squad)))


def test_state_gw_must_match_the_requested_gw():
    with pytest.raises(ValueError, match="gw3"):
        plan(gw=2, state=state(gw=3))


def test_previous_state_must_be_the_preceding_gameweek():
    with pytest.raises(ValueError, match="gw1"):
        plan(state=state(), previous_state=state(gw=3, picks=planned()))


def test_missing_deadline_refuses():
    payload = bootstrap().model_dump(mode="json")
    payload["events"] = [
        {**payload["events"][0], "id": 1, "is_next": False, "finished": True}
    ]
    with pytest.raises(ValueError, match="no deadline"):
        plan(bootstrap=Bootstrap.model_validate(payload))


# --- round trip -------------------------------------------------------------


def test_a_built_plan_reloads_through_parse_plan():
    """The writer and the POST-side reader must agree on the document."""
    built = plan(
        state=state(
            picks=planned(swapped(12, 20)),
            chip="bboost",
            chip_plan=[{"chip": "wildcard", "gw": 10}],
            transfers_made=[transfer("E12", "E20")],
        )
    )
    reloaded = parse_plan(json.loads(json.dumps(built.to_json_dict())), gw=2)
    assert reloaded == built
    assert reloaded.planned_picks().ids() == built.planned_picks().ids()
    assert reloaded.planned_prices() == {20: 60}


def test_json_document_spells_the_incoming_side_in():
    built = plan(
        state=state(picks=planned(swapped(12, 20)), transfers_made=[transfer("E12", "E20")])
    )
    assert set(built.to_json_dict()["transfers"][0]) == {
        "out",
        "in",
        "cost",
        "purchase_price_at_plan",
        "selling_price",
    }


def test_an_unrecognised_field_in_a_plan_is_refused():
    document = plan().to_json_dict() | {"apply_now": True}
    with pytest.raises(ValidationError):
        parse_plan(document, gw=2)


def test_a_plan_without_a_schema_version_is_refused():
    document = {key: value for key, value in plan().to_json_dict().items()
                if key != "schema_version"}
    with pytest.raises(ValueError, match="schema_version"):
        parse_plan(document, gw=2)


def test_a_non_object_plan_is_refused():
    with pytest.raises(ValueError, match="JSON object"):
        parse_plan([1, 2, 3], gw=2)


def test_a_previous_pick_missing_from_the_bootstrap_is_named():
    """A player removed from the game between gameweeks."""
    previous = {pid: value for pid, value in SQUAD.items() if pid != 12}
    previous[900] = SQUAD[12]
    with pytest.raises(ValueError, match=r"unknown player ids: \[900\]"):
        plan(
            state=state(picks=planned()),
            previous_state=state(gw=1, picks=planned(previous)),
        )


# --- chip routing --------------------------------------------------------------


@pytest.mark.parametrize(
    ("chip", "lineup", "transfers"),
    [
        (None, None, None),
        ("bboost", "bboost", None),
        ("3xc", "3xc", None),
        ("wildcard", None, "wildcard"),
        ("freehit", None, "freehit"),
    ],
)
def test_each_chip_goes_only_to_the_endpoint_that_activates_it(
    chip, lineup, transfers
):
    assert route_chip(chip, LINEUP_TARGET) == lineup
    assert route_chip(chip, TRANSFERS_TARGET) == transfers


def test_an_unknown_chip_refuses_rather_than_being_dropped():
    with pytest.raises(ValueError, match="unknown chip 'megaboost'"):
        route_chip("megaboost", LINEUP_TARGET)


def test_every_bootstrap_chip_name_has_a_routing_target():
    """A chip the game offers but nothing routes would be silently unplayable."""
    assert LINEUP_CHIPS | TRANSFER_CHIPS == {"bboost", "3xc", "wildcard", "freehit"}
    assert not LINEUP_CHIPS & TRANSFER_CHIPS
