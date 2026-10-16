"""The corrections digest over synthetic retros: status from the latest
retro's table, rule text from the newest file that defines it."""

from __future__ import annotations

from pathlib import Path

import pytest

from fpl.corrections import (
    agent_corrections,
    build_digest,
    corrections_section,
    is_closed,
    parse_rules,
    parse_status_rows,
)

GW1 = """# GW1 retro

## Corrections

Prose before the rules.

**C1 — A3 (player-analyst): keep the mapping
unchanged for one more round.** Because reasons.

**C2 — A3: log the sample every week.** Spent.

**C3 — A2 and A4 (squad-optimizer): hold the gate.** Binding.

**C4 — CODE (fpl/ep.py): unify the curve.** Two shapes.

## Running calibration stats

**C9 — A3: a bold line outside the section is not a rule.**

## Carried into GW2
"""

GW2 = """# GW2 retro

## Corrections

| C# | Agent | Status | Evidence |
|---|---|---|---|
| C1 | A3 | active | complied |
| C2 | A3 | retired — moved to C4 | spent |
| C3 | A2, A4 | revised — see C6 | superseded |
| C4 | CODE | active — unshipped | still open |

**C5 — A3 (player-analyst): cap new signings at 0.7.** New rule.

**C6 — A2, A3 (fixture-analyst, player-analyst): two-sided band.** Shared.

## Running calibration stats

Prose with C1 in it.
"""

GW3 = """# GW3 retro

## Corrections

| C# | Agent | Status | Evidence |
|---|---|---|---|
| C1 | A3 | retired — satisfied | done |
| C2 | A3 | retired — moved to C4 | carried |
| C3 | A2, A4 | revised — see C6 | carried |
| C4 | CODE | active — unshipped | open |
| C5 | A3 | active — complied | fine |
| C6 | A2, A3 | active | fine |

**C5 — A3 (player-analyst): cap new signings at 0.65.** Revised in place.

## Carried into GW4
"""


def write_retros(root: Path, **files: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (root / f"{name}.md").write_text(text, encoding="utf-8")
    return root


# --- parsing -----------------------------------------------------------------


def test_section_stops_at_the_next_header():
    section = corrections_section(GW1)
    assert section.startswith("## Corrections")
    assert "**C4 — " in section
    assert "C9" not in section
    assert "Running calibration stats" not in section


def test_section_is_empty_without_a_corrections_header():
    assert corrections_section("# x\n## Squad\n") == ""


def test_parse_rules_keeps_the_whole_paragraph():
    rules = parse_rules(corrections_section(GW1))
    assert [r.number for r in rules] == [1, 2, 3, 4]
    assert rules[0].text == ("**C1 — A3 (player-analyst): keep the mapping\n"
                             "unchanged for one more round.** Because reasons.")
    assert rules[2].agents == ("A2", "A4")
    assert rules[3].agents == ("CODE",)


def test_parse_status_rows_splits_the_agent_cell():
    rows = parse_status_rows(corrections_section(GW2))
    assert [r.number for r in rows] == [1, 2, 3, 4]
    assert rows[2].agents == ("A2", "A4")
    assert rows[1].status == "retired — moved to C4"
    assert rows[0].line == "| C1 | A3 | active | complied |"


@pytest.mark.parametrize("status, closed", [
    ("retired — satisfied", True), ("revised — see C12", True), ("active", False),
    ("active — unshipped", False), ("new", False),
])
def test_is_closed(status, closed):
    assert is_closed(status) is closed


# --- retro digest (no agent) ---------------------------------------------------


def test_digest_reads_only_retros_before_the_round(tmp_path):
    root = write_retros(tmp_path, gw1=GW1, gw2=GW2, gw3=GW3)
    digest = build_digest(root, before_round=3)
    assert digest.latest == "gw2.md"
    assert [r.number for r in digest.rows] == [1, 2, 3, 4]


def test_digest_omits_closed_rules_from_the_active_list(tmp_path):
    root = write_retros(tmp_path, gw1=GW1, gw2=GW2, gw3=GW3)
    digest = build_digest(root, before_round=4)
    assert [r.number for r in digest.active] == [4, 5, 6]


def test_rule_revised_in_place_takes_the_newest_text(tmp_path):
    root = write_retros(tmp_path, gw1=GW1, gw2=GW2, gw3=GW3)
    active = {r.number: r for r in build_digest(root, before_round=4).active}
    assert "0.65" in active[5].text
    assert active[5].source == "gw3.md"
    assert active[4].source == "gw1.md"


def test_rules_new_in_the_latest_file_are_listed_and_active(tmp_path):
    root = write_retros(tmp_path, gw1=GW1, gw2=GW2)
    digest = build_digest(root, before_round=3)
    assert [r.number for r in digest.new] == [5, 6]
    assert {5, 6} <= {r.number for r in digest.active}


def test_without_a_table_every_rule_is_new(tmp_path):
    root = write_retros(tmp_path, gw1=GW1)
    digest = build_digest(root, before_round=2)
    assert digest.rows == ()
    assert [r.number for r in digest.new] == [1, 2, 3, 4]
    assert [r.number for r in digest.active] == [1, 2, 3, 4]


def test_status_row_without_rule_text_is_missing(tmp_path):
    orphan = GW2.replace("| C4 | CODE | active — unshipped | still open |",
                         "| C4 | CODE | active — unshipped | still open |\n| C7 | A3 | active | x |")
    root = write_retros(tmp_path, gw1=GW1, gw2=orphan)
    assert build_digest(root, before_round=3).missing == (7,)


def test_empty_root_has_no_latest(tmp_path):
    digest = build_digest(tmp_path / "absent", before_round=5)
    assert digest.latest is None
    assert digest.active == ()


def test_files_are_ordered_numerically(tmp_path):
    later = GW3.replace("0.65", "0.60")
    root = write_retros(tmp_path, gw9=GW2, gw10=later, gw1=GW1)
    digest = build_digest(root, before_round=11)
    assert digest.latest == "gw10.md"
    assert "0.60" in {r.number: r for r in digest.active}[5].text


def test_non_retro_files_are_ignored(tmp_path):
    root = write_retros(tmp_path, gw1=GW1)
    (root / "gw2-calibration.json").write_text("{}", encoding="utf-8")
    (root / "notes.md").write_text("## Corrections\n| C1 | A3 | retired | x |\n", "utf-8")
    assert build_digest(root, before_round=3).latest == "gw1.md"


# --- agent view ----------------------------------------------------------------


def test_agent_view_keeps_only_active_rules_addressed_to_it(tmp_path):
    root = write_retros(tmp_path, gw1=GW1, gw2=GW2, gw3=GW3)
    view = agent_corrections(root, gw=4, agent="A3")
    assert view.latest == "gw3.md"
    assert [c.rule.number for c in view.active] == [5, 6]
    assert [r.number for r in view.retired] == [1, 2]


def test_agent_view_matches_a_multi_agent_cell(tmp_path):
    root = write_retros(tmp_path, gw1=GW1, gw2=GW2, gw3=GW3)
    assert 6 in [c.rule.number for c in agent_corrections(root, gw=4, agent="A2").active]


def test_agent_view_shows_a_new_heading_with_no_ledger_row(tmp_path):
    root = write_retros(tmp_path, gw1=GW1, gw2=GW2)
    view = agent_corrections(root, gw=3, agent="A3")
    statuses = {c.rule.number: c.status for c in view.active}
    assert statuses == {1: "active", 5: "new", 6: "new"}


def test_agent_view_without_a_ledger_uses_headings_only(tmp_path):
    root = write_retros(tmp_path, gw1=GW1)
    view = agent_corrections(root, gw=2, agent="A3")
    assert [c.rule.number for c in view.active] == [1, 2]
    assert view.retired == ()


def test_code_rows_are_not_shown_to_an_analyst(tmp_path):
    root = write_retros(tmp_path, gw1=GW1, gw2=GW2, gw3=GW3)
    assert 4 not in [c.rule.number for c in agent_corrections(root, gw=4, agent="A3").active]
    assert [c.rule.number for c in agent_corrections(root, gw=4, agent="CODE").active] == [4]


def test_heading_in_an_old_retro_takes_status_from_the_latest(tmp_path):
    root = write_retros(tmp_path, gw1=GW1, gw2=GW2, gw3=GW3)
    view = agent_corrections(root, gw=4, agent="A3")
    active = {c.rule.number: c for c in view.active}
    assert active[6].status == "active"
    assert active[6].rule.source == "gw2.md"


def test_agent_view_reads_every_retro_before_the_gameweek(tmp_path):
    root = write_retros(tmp_path, gw1=GW1, gw2=GW2, gw3=GW3)
    assert agent_corrections(root, gw=3, agent="A3").latest == "gw2.md"


def test_agent_code_is_validated(tmp_path):
    with pytest.raises(ValueError, match="agent code"):
        agent_corrections(tmp_path, gw=4, agent="player-analyst")
