"""STATE-block parsing tests: the picks section is machine-written by the
finalizer, so the parser is strict — any deviation refuses rather than
guessing."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from fpl.state import PlannedPick, PlannedPicks, parse_state_picks, picks_from_ids


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
