"""final_check: the mechanical carry rules from a squad proposal into final.md."""

from __future__ import annotations

from fpl.final_check import (
    check_final,
    check_proposal,
    has_no_suggestions_line,
    parse_ledger,
)
from tests.test_plan_cli import squad_slots, state_block

S1 = "| S1 | 4 | standing | keep the policy |"
S2 = "| S2 | 4 | rejected | unreachable |"
S3 = "| S3 | 5 | deferred | revisit GW7 |"
NO_SUGGESTIONS = "No data/suggestions.md — no ledger this cycle."


def ledger(rows: list[str], max_s: int | None = None, trailer: str = "") -> str:
    top = max_s if max_s is not None else len(rows)
    table = "\n".join(["| S# | GW | Status | Reason |", "|---|---|---|---|", *rows])
    return (f"## Suggestions\n\nRead data/suggestions.md through S{top}\n\n{table}\n"
            + (f"\n{trailer}\n" if trailer else ""))


def full_state(gw: int) -> str:
    """A STATE block with every chip key explicit, as the spec requires."""
    return state_block(gw, squad_slots(), chip="null").replace(
        "\nchip: null\n", "\nchip: null\nchip_plan: []\n")


def document(gw: int, section: str, *, state: str | None = None) -> str:
    block = state if state is not None else full_state(gw)
    return f"# GW{gw}\n\nprose\n\n{section}\n{block}"


def proposal(rows: list[str] | None = None, **kwargs) -> str:
    return document(5, ledger(rows if rows is not None else [S1, S2, S3]), **kwargs)


def previous(rows: list[str]) -> str:
    return document(4, ledger(rows))


def rules(findings) -> list[str]:
    return [f.rule for f in findings]


# --- parsing ----------------------------------------------------------------


def test_parse_ledger_reads_marker_and_rows_in_file_order():
    parsed = parse_ledger(ledger([S2, S1], max_s=3, trailer="A note after the table."))
    assert parsed is not None
    assert parsed.marker == "Read data/suggestions.md through S3"
    assert parsed.max_s == 3
    assert parsed.rows == (("S2", S2), ("S1", S1))


def test_parse_ledger_without_marker_is_none():
    assert parse_ledger("# GW5\n\nno ledger here\n") is None


def test_has_no_suggestions_line():
    assert has_no_suggestions_line(f"x\n{NO_SUGGESTIONS}\n")
    assert not has_no_suggestions_line("x\nthere is No data/suggestions.md\n")


# --- proposal rules ---------------------------------------------------------


def test_a_valid_proposal_has_no_findings():
    assert check_proposal(proposal(), gw=5, previous_final=previous([S1, S2]),
                          suggestions_exists=True) == []


def test_a_malformed_state_line_is_p1_quoting_the_line():
    broken = proposal().replace("bank: 1.0", "bank 1.0")
    findings = check_proposal(broken, gw=5, previous_final=None, suggestions_exists=True)
    assert rules(findings) == ["P1"]
    assert "bank 1.0" in findings[0].message


def test_a_gameweek_mismatch_is_p1():
    findings = check_proposal(proposal(), gw=6, previous_final=None, suggestions_exists=True)
    assert rules(findings) == ["P1"]


def test_a_state_without_picks_is_p1():
    bare = proposal(state=state_block(5, squad_slots(), include_picks=False))
    findings = check_proposal(bare, gw=5, previous_final=None, suggestions_exists=True)
    assert rules(findings) == ["P1"]
    assert "picks" in findings[0].message


def test_suggestions_without_a_marker_is_p2():
    unmarked = document(5, "## Suggestions\n\nnothing\n")
    findings = check_proposal(unmarked, gw=5, previous_final=None, suggestions_exists=True)
    assert rules(findings) == ["P2"]


def test_no_suggestions_file_needs_the_no_suggestions_line():
    with_line = document(5, NO_SUGGESTIONS)
    without = document(5, "nothing")
    assert check_proposal(with_line, gw=5, previous_final=None,
                          suggestions_exists=False) == []
    assert rules(check_proposal(without, gw=5, previous_final=None,
                                suggestions_exists=False)) == ["P2"]


def test_a_dropped_previous_row_is_p3_naming_it():
    findings = check_proposal(proposal([S1, S2]), gw=5,
                              previous_final=previous([S1, S2, S3]),
                              suggestions_exists=True)
    assert rules(findings) == ["P3"]
    assert "S3" in findings[0].message


def test_an_altered_closed_row_is_p3_but_a_reworded_open_row_passes():
    altered = S2.replace("unreachable", "out of reach")
    reworded = S1.replace("keep the policy", "policy kept")
    assert rules(check_proposal(proposal([S1, altered, S3]), gw=5,
                                previous_final=previous([S1, S2]),
                                suggestions_exists=True)) == ["P3"]
    assert check_proposal(proposal([reworded, S2, S3]), gw=5,
                          previous_final=previous([S1, S2]),
                          suggestions_exists=True) == []


def test_a_previous_final_without_a_ledger_is_vacuous():
    assert check_proposal(proposal(), gw=5, previous_final="# GW4\n\nold format\n",
                          suggestions_exists=True) == []


# --- final rules ------------------------------------------------------------


def test_a_faithful_final_has_no_findings():
    assert check_final(proposal(), proposal(), gw=5) == []


def test_a_different_bank_is_f3_naming_the_field():
    final = proposal().replace("bank: 1.0", "bank: 0.9")
    findings = check_final(final, proposal(), gw=5)
    assert rules(findings) == ["F3"]
    assert "bank" in findings[0].message


def test_an_omitted_chip_line_is_f2_while_the_states_still_match():
    final = proposal().replace("\nchip: null\n", "\n")
    findings = check_final(final, proposal(), gw=5)
    assert rules(findings) == ["F2"]
    assert "chip:" in findings[0].message


def test_a_reworded_ledger_row_is_f4_but_a_dropped_trailing_note_passes():
    noted = document(5, ledger([S1, S2, S3], trailer="No malformed rows were found."))
    plain = document(5, ledger([S1, S2, S3]))
    reworded = document(5, ledger([S1.replace("policy", "rule"), S2, S3]))
    assert check_final(plain, noted, gw=5) == []
    findings = check_final(reworded, plain, gw=5)
    assert rules(findings) == ["F4"]
    assert "S1" in findings[0].message


def test_text_after_the_state_fence_is_f1():
    findings = check_final(proposal() + "\nA closing remark.\n", proposal(), gw=5)
    assert rules(findings) == ["F1"]


def test_an_added_row_in_the_final_is_f4():
    final = proposal([S1, S2, S3, "| S7 | 7 | deferred | later |"])
    findings = check_final(final, proposal(), gw=5)
    assert rules(findings) == ["F4"]
    assert "S7" in findings[0].message


def test_the_no_suggestions_line_must_carry_into_the_final():
    source = document(5, NO_SUGGESTIONS)
    assert check_final(source, source, gw=5) == []
    assert rules(check_final(document(5, "nothing"), source, gw=5)) == ["F4"]


def test_an_unparseable_final_state_is_f1_only():
    final = proposal().replace("bank: 1.0", "bank 1.0")
    findings = check_final(final, proposal(), gw=5)
    assert rules(findings) == ["F1"]
    assert "bank 1.0" in findings[0].message
