"""STATE-block parsing tests: the block is machine-written by the finalizer,
so the parser is strict — any deviation refuses with the offending line rather
than guessing."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from fpl.state import PlannedPick, parse_state, parse_state_picks, picks_from_ids


def pick_line(
    id: int, position: int, name: str = "Player", captain: bool = False,
    vice: bool = False,
) -> str:
    return (
        f"  - {{id: {id}, name: {name}, position: {position}, "
        f"captain: {str(captain).lower()}, vice: {str(vice).lower()}}}"
    )


def pick_lines(captain_position: int = 10, vice_position: int = 3) -> list[str]:
    return [
        pick_line(
            id=100 + slot,
            position=slot,
            name=f"P{slot}",
            captain=slot == captain_position,
            vice=slot == vice_position,
        )
        for slot in range(1, 16)
    ]


def final_md(picks: list[str] | None = None, gw: int = 2) -> str:
    lines = picks if picks is not None else pick_lines()
    body = "\n".join(lines)
    return (
        "# Final decision\n\nProse about the squad.\n\n"
        "```yaml\n# not the STATE block\nexample: true\n```\n\n"
        "## STATE\n\n"
        "```yaml\n"
        f"gw: {gw}\n"
        "team_id: 42\n"
        "team_value: 100.0\n"
        "bank: 0.0\n"
        "free_transfers_banked: 1\n"
        "chips_used: []\n"
        "transfers_made: []\n"
        "picks:\n"
        f"{body}\n"
        "```\n"
    )


def test_parses_fifteen_picks_from_the_last_yaml_block():
    picks = parse_state_picks(final_md(), expected_gw=2)
    assert len(picks.picks) == 15
    assert [p.position for p in picks.picks] == list(range(1, 16))
    assert picks.picks[0] == PlannedPick(
        id=101, name="P1", position=1, captain=False, vice=False
    )
    assert picks.captain().id == 110
    assert picks.vice().id == 103
    assert [p.id for p in picks.bench()] == [112, 113, 114, 115]


def test_quoted_names_are_unquoted():
    lines = pick_lines()
    lines[0] = '  - {id: 101, name: "N\'Golo", position: 1, captain: false, vice: false}'
    picks = parse_state_picks(final_md(lines), expected_gw=2)
    assert picks.picks[0].name == "N'Golo"


def test_missing_picks_section_is_refused():
    text = final_md().replace("picks:\n", "").split("picks-sentinel")[0]
    text = "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("- {")
    )
    with pytest.raises(ValueError, match="no 'picks:' section"):
        parse_state_picks(text, expected_gw=2)


def test_malformed_pick_line_is_refused_with_the_line():
    lines = pick_lines()
    lines[4] = "  - {id: 105, position: 5}"
    with pytest.raises(ValueError, match="unparseable pick line"):
        parse_state_picks(final_md(lines), expected_gw=2)


def test_state_gw_mismatch_is_refused():
    with pytest.raises(ValueError, match="STATE block is for gw3"):
        parse_state_picks(final_md(gw=3), expected_gw=2)


def test_document_without_yaml_block_is_refused():
    with pytest.raises(ValueError, match="no yaml block"):
        parse_state_picks("# Final\n\nno state here\n", expected_gw=2)


def test_wrong_pick_count_is_refused():
    with pytest.raises(ValidationError, match="15"):
        parse_state_picks(final_md(pick_lines()[:14]), expected_gw=2)


def test_duplicate_positions_are_refused():
    lines = pick_lines()[:14] + [pick_line(id=999, position=14)]
    with pytest.raises(ValidationError, match="positions"):
        parse_state_picks(final_md(lines), expected_gw=2)


def test_duplicate_ids_are_refused():
    lines = pick_lines()[:14] + [pick_line(id=114, position=15)]
    with pytest.raises(ValidationError, match="ids"):
        parse_state_picks(final_md(lines), expected_gw=2)


@pytest.mark.parametrize("captain_position", [0, 12])
def test_captain_must_exist_and_start(captain_position):
    with pytest.raises(ValidationError, match="captain"):
        parse_state_picks(
            final_md(pick_lines(captain_position=captain_position)), expected_gw=2
        )


def test_vice_must_start():
    with pytest.raises(ValidationError, match="vice"):
        parse_state_picks(final_md(pick_lines(vice_position=13)), expected_gw=2)


def test_captain_and_vice_must_differ():
    lines = [
        pick_line(id=100 + s, position=s, captain=s == 5, vice=s == 5)
        for s in range(1, 16)
    ]
    with pytest.raises(ValidationError, match="captain"):
        parse_state_picks(final_md(lines), expected_gw=2)


def test_picks_from_ids_assigns_positions_in_order():
    ids = list(range(201, 216))
    picks = picks_from_ids(ids, captain=205, vice=210)
    assert [p.position for p in picks.picks] == list(range(1, 16))
    assert [p.id for p in picks.picks] == ids
    assert picks.captain().id == 205
    assert picks.vice().id == 210
    assert all(p.name == "" for p in picks.picks)


def test_picks_from_ids_rejects_captain_outside_the_squad():
    with pytest.raises(ValidationError, match="captain"):
        picks_from_ids(list(range(201, 216)), captain=999, vice=210)


# --- full STATE block ------------------------------------------------------


def state_md(
    body: str | None = None, picks: list[str] | None = None, gw: int = 2
) -> str:
    """A final.md whose last yaml block is the STATE block."""
    default_body = (
        f"gw: {gw}\n"
        "team_id: 8455344\n"
        "team_value: 99.9\n"
        "bank: 1.0\n"
        "free_transfers_banked: 1\n"
        "chips_used: []\n"
        "transfers_made: []\n"
    )
    block = default_body if body is None else body
    if picks is not None:
        block += "picks:\n" + "\n".join(picks) + "\n"
    return (
        "# Final decision\n\nProse.\n\n"
        "```yaml\n# decoy block\nexample: true\n```\n\n"
        "## STATE\n\n```yaml\n" + block + "```\n"
    )


def test_parses_every_state_field():
    text = state_md(
        "# a comment line is ignored\n"
        "gw: 2\n"
        "team_id: 8455344\n"
        "team_value: 99.9\n"
        "bank: 1.0\n"
        "free_transfers_banked: 1\n"
        "chip: bboost\n"
        "chips_used:\n"
        "  - {chip: 3xc, gw: 1}\n"
        "transfers_made:\n"
        "  - {out: Enzo, in: Tavernier, cost: 0}\n"
        "  - {out: Hughes, in: Scott, cost: 4}\n"
        "chip_plan:\n"
        "  - {chip: wildcard, gw: 10, status: provisional}\n",
        picks=pick_lines(),
    )
    state = parse_state(text, expected_gw=2)
    assert state.gw == 2
    assert state.team_id == 8455344
    assert state.team_value == 99.9
    assert state.bank == 1.0
    assert state.free_transfers_banked == 1
    assert state.chip == "bboost"
    assert [(c.chip, c.gw) for c in state.chips_used] == [("3xc", 1)]
    assert [(t.out, t.into, t.cost) for t in state.transfers_made] == [
        ("Enzo", "Tavernier", 0),
        ("Hughes", "Scott", 4),
    ]
    assert [(e.chip, e.gw, e.status) for e in state.chip_plan] == [
        ("wildcard", 10, "provisional")
    ]
    assert state.picks is not None
    assert len(state.picks.picks) == 15


def test_absent_chip_is_null():
    assert parse_state(state_md(picks=pick_lines()), expected_gw=2).chip is None


def test_explicit_null_chip_is_null():
    text = state_md(
        "gw: 2\nteam_id: null\nteam_value: 100.0\nbank: 0.0\n"
        "free_transfers_banked: 1\nchips_used: []\ntransfers_made: []\nchip: null\n",
        picks=pick_lines(),
    )
    assert parse_state(text, expected_gw=2).chip is None


def test_absent_chip_plan_is_empty():
    assert parse_state(state_md(picks=pick_lines()), expected_gw=2).chip_plan == ()


def test_chip_plan_status_defaults_to_provisional():
    text = state_md(
        "gw: 2\nteam_id: 42\nteam_value: 100.0\nbank: 0.0\n"
        "free_transfers_banked: 1\nchips_used: []\ntransfers_made: []\n"
        "chip_plan:\n  - {chip: 3xc, gw: 3}\n",
        picks=pick_lines(),
    )
    assert parse_state(text, expected_gw=2).chip_plan[0].status == "provisional"


def test_absent_picks_section_is_none_not_an_error():
    """gw1's final.md predates the picks: schema addition."""
    state = parse_state(state_md(gw=1), expected_gw=1)
    assert state.picks is None
    assert state.team_id == 8455344


def test_null_team_id_parses():
    text = state_md(
        "gw: 1\nteam_id: null\nteam_value: 100.0\nbank: 0.0\n"
        "free_transfers_banked: 1\nchips_used: []\ntransfers_made: []\n"
    )
    assert parse_state(text, expected_gw=1).team_id is None


def test_state_gw_mismatch_is_refused_by_full_parse():
    with pytest.raises(ValueError, match="STATE block is for gw3"):
        parse_state(state_md(gw=3), expected_gw=2)


def test_expected_gw_is_optional():
    assert parse_state(state_md(gw=7)).gw == 7


def test_unknown_key_is_refused_with_the_key():
    text = state_md(
        "gw: 2\nteam_id: 42\nteam_value: 100.0\nbank: 0.0\n"
        "free_transfers_banked: 1\nchips_used: []\ntransfers_made: []\n"
        "wildcard_plan: gw10\n"
    )
    with pytest.raises(ValueError, match="unknown key in STATE block: 'wildcard_plan'"):
        parse_state(text, expected_gw=2)


def test_missing_required_key_is_refused_by_name():
    text = state_md("gw: 2\nteam_id: 42\nteam_value: 100.0\nbank: 0.0\n")
    with pytest.raises(ValueError, match="missing required key 'free_transfers_banked'"):
        parse_state(text, expected_gw=2)


def test_unparseable_line_refuses_with_the_offending_line():
    text = state_md(
        "gw: 2\nteam_id: 42\nteam_value: 100.0\nbank: 0.0\n"
        "free_transfers_banked = 1\nchips_used: []\ntransfers_made: []\n"
    )
    with pytest.raises(ValueError, match="free_transfers_banked = 1"):
        parse_state(text, expected_gw=2)


def test_duplicate_key_is_refused():
    text = state_md(
        "gw: 2\ngw: 3\nteam_id: 42\nteam_value: 100.0\nbank: 0.0\n"
        "free_transfers_banked: 1\nchips_used: []\ntransfers_made: []\n"
    )
    with pytest.raises(ValueError, match="duplicate key in STATE block: 'gw'"):
        parse_state(text, expected_gw=2)


def test_malformed_transfer_line_refuses_with_the_line():
    text = state_md(
        "gw: 2\nteam_id: 42\nteam_value: 100.0\nbank: 0.0\n"
        "free_transfers_banked: 1\nchips_used: []\n"
        "transfers_made:\n  - {out: Enzo, in: Tavernier}\n"
    )
    with pytest.raises(ValueError, match=r"unparseable transfers_made line.*out: Enzo"):
        parse_state(text, expected_gw=2)


def test_malformed_chips_used_line_refuses_with_the_line():
    text = state_md(
        "gw: 2\nteam_id: 42\nteam_value: 100.0\nbank: 0.0\n"
        "free_transfers_banked: 1\nchips_used:\n  - bboost\n"
        "transfers_made: []\n"
    )
    with pytest.raises(ValueError, match="unparseable chips_used line"):
        parse_state(text, expected_gw=2)


def test_inline_non_empty_list_is_refused():
    text = state_md(
        "gw: 2\nteam_id: 42\nteam_value: 100.0\nbank: 0.0\n"
        "free_transfers_banked: 1\nchips_used: [{chip: 3xc, gw: 1}]\n"
        "transfers_made: []\n"
    )
    with pytest.raises(ValueError, match="chips_used"):
        parse_state(text, expected_gw=2)


def test_scalar_key_given_a_list_is_refused():
    text = state_md(
        "gw: 2\nteam_id: 42\nteam_value: 100.0\nbank: 0.0\n"
        "free_transfers_banked:\n  - {chip: 3xc, gw: 1}\n"
        "chips_used: []\ntransfers_made: []\n"
    )
    with pytest.raises(ValueError, match="free_transfers_banked"):
        parse_state(text, expected_gw=2)


def test_list_item_before_any_key_is_refused():
    text = state_md("  - {chip: 3xc, gw: 1}\ngw: 2\n")
    with pytest.raises(ValueError, match="list item before any key"):
        parse_state(text, expected_gw=2)


def test_non_numeric_scalar_is_refused_by_validation():
    text = state_md(
        "gw: 2\nteam_id: 42\nteam_value: about a hundred\nbank: 0.0\n"
        "free_transfers_banked: 1\nchips_used: []\ntransfers_made: []\n"
    )
    with pytest.raises(ValidationError, match="team_value"):
        parse_state(text, expected_gw=2)


def test_picks_still_parse_through_the_shared_scanner():
    """set-lineup --from-final needs only picks: a partial block still works."""
    text = state_md("gw: 2\nteam_id: 42\n", picks=pick_lines())
    assert len(parse_state_picks(text, expected_gw=2).picks) == 15
