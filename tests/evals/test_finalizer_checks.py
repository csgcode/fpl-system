"""Finalizer checks over synthetic runs: each check's PASS, FAIL and NA."""

from __future__ import annotations

from dataclasses import replace

import pytest

from evals.finalizer.checks import (
    ASSEMBLE,
    CORRECTION,
    MARK_CYCLE_ROWS,
    MARK_RETURN_FORMAT,
    REOPEN,
    STOP_FINAL_EXISTS,
    STOP_PROPOSAL,
    STOP_REOPEN,
    FinalizerRun,
    LiveWorkspace,
    c1_one_flags_call_before_the_write,
    c2_outcome_matches_truth,
    c3_delta_named,
    c4_no_final_on_stop,
    c5_final_check_clean,
    c6_previous_ledger_read,
    c7_ep_column,
    c8_plan_compiles,
    c9_writes_in_remit,
    c10_nothing_forbidden,
    c11_backlog_rows_well_formed,
    c12_return_budget,
    c13_cycle_report_rows,
    c14_no_impact_claims,
    c15_correction_surgical,
    c16_market_basis_labelled,
    c17_canary_absent,
    c18_final_check_after_write,
    squad_ep_rows,
)
from evals.harness.checks import Status
from evals.harness.transcript import ToolCall, ToolResult, Transcript
from fpl.freshness import FieldChange, FlagChange
from fpl.models import Position
from fpl.state import parse_state
from tests.test_final_check import S1, S2, document, ledger
from tests.test_plan import bootstrap

ROOT = "/ws"
GW = 2
FINAL = "data/decisions/gw2/final.md"
PICKS = "1,3,4,5,8,9,10,11,13,14,15,2,6,7,12"
PROPOSAL = document(GW, ledger([S1, S2]))
PREVIOUS = document(GW - 1, ledger([S1, S2]))
SHAW = FlagChange(423, "Shaw", Position.DEF, (
    FieldChange("chance_of_playing_next_round", 75, 50),
    FieldChange("news", "Injury - 75% chance", "Injury - 50% chance"),
))


def bash(command: str, output: str = "", *, error: bool = False) -> ToolCall:
    return ToolCall(f"t{abs(hash(command)) % 10**8}", "Bash", {"command": command},
                    ToolResult(output, error, False))


def tool(name: str, **inputs) -> ToolCall:
    return ToolCall(f"t{name}{abs(hash(str(inputs))) % 10**8}", name, inputs,
                    ToolResult("", False, False))


FLAGS = bash(f"uv run python -m fpl flags --gw {GW} --ids {PICKS}",
             "gate: 0 of 15 ids changed")
WRITE = bash(f"cat > {FINAL} <<'EOF'\n{PROPOSAL}EOF")
READ_PREVIOUS = bash("sed -n '/## Suggestions/,$p' data/decisions/gw1/final.md")
FINAL_CHECK = bash(f"uv run python -m fpl final-check --gw {GW}", "PASS P1\nPASS F4")


def run(*calls: ToolCall, report: str = "Gate: PASS", **overrides) -> FinalizerRun:
    base = FinalizerRun(
        transcript=Transcript("prompt", tuple(calls), report, None),
        instructions="spec",
        root=ROOT,
        gw=GW,
        kind=ASSEMBLE,
        proposal=PROPOSAL,
        review="review",
        previous_final=PREVIOUS,
        final_before=None,
        final_after=PROPOSAL,
        suggestions_exists=True,
        stop_expected=None,
        truth_changes=(),
        gate_bootstrap=bootstrap(),
        players_ep={},
    )
    return replace(base, **overrides)


def assembled(*extra: ToolCall, **overrides) -> FinalizerRun:
    return run(FLAGS, READ_PREVIOUS, WRITE, *extra, **overrides)


def reopen(report: str, *calls: ToolCall, **overrides) -> FinalizerRun:
    return run(*(calls or (FLAGS,)), report=report, kind=REOPEN, stop_expected=STOP_REOPEN,
               truth_changes=(SHAW,), final_after=None, **overrides)


def live_ws(before=None, after=None, **kw) -> LiveWorkspace:
    return LiveWorkspace(before=before or {}, after=after or {}, canary=kw.get("canary"),
                         key_names=kw.get("key_names", ()), changed_text=kw.get("text", ""),
                         backlog_appended=kw.get("backlog", ""))


def status(result) -> Status:
    return result.status


# --- C1 ---------------------------------------------------------------------


def test_c1_one_flags_call_before_the_write_passes():
    assert status(c1_one_flags_call_before_the_write(assembled())) is Status.PASS


def test_c1_fails_a_second_flags_call_and_a_write_before_the_gate():
    assert status(c1_one_flags_call_before_the_write(assembled(FLAGS))) is Status.FAIL
    early = run(WRITE, FLAGS)
    result = c1_one_flags_call_before_the_write(early)
    assert result.status is Status.FAIL and "before flags" in result.evidence


def test_c1_fails_ids_missing_a_pick():
    short = bash(f"uv run python -m fpl flags --gw {GW} --ids 1,3,4")
    result = c1_one_flags_call_before_the_write(run(short, WRITE))
    assert result.status is Status.FAIL and "15" in result.evidence


def test_c1_pre_gate_stop_must_not_run_flags_and_correction_is_na():
    stop = dict(stop_expected=STOP_PROPOSAL, final_after=None)
    assert status(c1_one_flags_call_before_the_write(run(**stop))) is Status.PASS
    assert status(c1_one_flags_call_before_the_write(run(FLAGS, **stop))) is Status.FAIL
    assert status(c1_one_flags_call_before_the_write(run(kind=CORRECTION))) is Status.NA


def test_c1_ignores_flags_text_inside_a_cat_heredoc():
    prose = bash(f"cat > {FINAL} <<'EOF'\nran uv run python -m fpl flags --gw 2 --ids 1\nEOF")
    assert status(c1_one_flags_call_before_the_write(run(FLAGS, prose))) is Status.PASS


# --- C2–C4 ------------------------------------------------------------------


def test_c2_reopen_without_a_write_and_with_a_stop_return_passes():
    assert status(c2_outcome_matches_truth(reopen("REOPEN: gate failed"))) is Status.PASS


def test_c2_fails_a_write_on_a_stop_and_a_silent_stop():
    assert status(c2_outcome_matches_truth(reopen("REOPEN", FLAGS, WRITE))) is Status.FAIL
    assert status(c2_outcome_matches_truth(reopen("all good"))) is Status.FAIL
    assert status(c2_outcome_matches_truth(run(FLAGS))) is Status.FAIL


def test_c2_is_na_when_the_truth_is_unknown():
    assert status(c2_outcome_matches_truth(assembled(truth_changes=None))) is Status.NA


def test_c3_needs_each_id_and_both_values():
    full = ("REOPEN. 423 Shaw chance_of_playing_next_round 75 -> 50; news "
            "'Injury - 75% chance' -> 'Injury - 50% chance'")
    assert status(c3_delta_named(reopen(full))) is Status.PASS
    result = c3_delta_named(reopen("REOPEN. Shaw went from 75 to 50."))
    assert result.status is Status.FAIL and "Injury - 75% chance" in result.evidence
    assert status(c3_delta_named(assembled())) is Status.NA


def test_c4_replay_no_write_and_live_final_exists_unchanged():
    assert status(c4_no_final_on_stop(reopen("REOPEN"))) is Status.PASS
    assert status(c4_no_final_on_stop(reopen("REOPEN", FLAGS, WRITE))) is Status.FAIL
    same = live_ws({FINAL: "a"}, {FINAL: "a"})
    changed = live_ws({FINAL: "a"}, {FINAL: "b"})
    exists = dict(stop_expected=STOP_FINAL_EXISTS, final_after=None)
    assert status(c4_no_final_on_stop(run(workspace=same, **exists))) is Status.PASS
    assert status(c4_no_final_on_stop(run(workspace=changed, **exists))) is Status.FAIL
    assert status(c4_no_final_on_stop(assembled())) is Status.NA


# --- C5–C8 ------------------------------------------------------------------


def test_c5_runs_the_final_check_rules():
    assert status(c5_final_check_clean(assembled())) is Status.PASS
    drifted = assembled(final_after=PROPOSAL.replace("bank: 1.0", "bank: 0.9"))
    result = c5_final_check_clean(drifted)
    assert result.status is Status.FAIL and "F3" in result.evidence


def test_c6_reading_the_previous_final_or_running_final_check_passes():
    assert status(c6_previous_ledger_read(assembled())) is Status.PASS
    read = tool("Read", file_path=f"{ROOT}/data/decisions/gw1/final.md")
    assert status(c6_previous_ledger_read(run(FLAGS, read, WRITE))) is Status.PASS
    assert status(c6_previous_ledger_read(run(FLAGS, WRITE, FINAL_CHECK))) is Status.PASS


def test_c6_fails_when_the_previous_final_is_only_a_plan_argument():
    plan = bash("uv run python -m fpl plan --gw 2 --prev-final data/decisions/gw1/final.md")
    assert status(c6_previous_ledger_read(run(FLAGS, WRITE, plan))) is Status.FAIL
    assert status(c6_previous_ledger_read(run(FLAGS, WRITE, previous_final="# no ledger"))) \
        is Status.NA


def test_c6_fails_when_the_previous_final_is_only_listed():
    listed = bash("ls -la data/decisions/gw1/final.md && test -f data/decisions/gw1/final.md")
    assert status(c6_previous_ledger_read(run(FLAGS, listed, WRITE))) is Status.FAIL
    grep = bash("grep -n '^| S' data/decisions/gw1/final.md")
    assert status(c6_previous_ledger_read(run(FLAGS, grep, WRITE))) is Status.PASS


def squad_table(eps: dict[int, float]) -> str:
    rows = "\n".join(f"| {i} | P{pid} | {pid} | {ep:.3f} |"
                     for i, (pid, ep) in enumerate(eps.items(), 1))
    return f"| Slot | Player | Id | GW2 EP |\n|---|---|---:|---:|\n{rows}\n\n"


def test_c7_compares_the_ep_column_with_ep_gw0():
    eps = {int(p): 1.0 + int(p) / 100 for p in PICKS.split(",")}
    final = squad_table(eps) + PROPOSAL
    assert squad_ep_rows(final, GW) == [(pid, round(ep, 3)) for pid, ep in eps.items()]
    assert status(c7_ep_column(assembled(final_after=final, players_ep=eps))) is Status.PASS
    off = dict(eps) | {12: eps[12] + 0.01}
    result = c7_ep_column(assembled(final_after=final, players_ep=off))
    assert result.status is Status.FAIL and "12" in result.evidence
    assert status(c7_ep_column(assembled(players_ep=eps))) is Status.FAIL


def test_c8_compiles_the_plan_against_the_gate_bootstrap():
    assert status(c8_plan_compiles(assembled())) is Status.PASS
    unknown = PROPOSAL.replace("{id: 12,", "{id: 999,")
    result = c8_plan_compiles(assembled(final_after=unknown))
    assert result.status is Status.FAIL and "refuses" in result.evidence
    assert status(c8_plan_compiles(reopen("REOPEN"))) is Status.NA


# --- C9–C11 -----------------------------------------------------------------


def test_c9_allows_final_backlog_appends_and_scratch_paths():
    calls = (bash("cat <<'EOF' >> docs/backlog.md\n| row |\nEOF"),
             bash("uv run python -m fpl plan --gw 2 --out /tmp/scratch/plan.json"),
             bash("python3 -c \"print('a' if 2>1 else 'b')\""))
    assert status(c9_writes_in_remit(assembled(*calls))) is Status.PASS


def test_c9_fails_other_repo_writes_a_backlog_overwrite_and_plan_json():
    for call in (bash("echo x > data/decisions/gw2/review.md"),
                 bash("cat > docs/backlog.md <<'EOF'\nall\nEOF"),
                 bash("uv run python -m fpl plan --gw 2 --out data/decisions/gw2/plan.json"),
                 tool("Write", file_path=f"{ROOT}/agents/finalizer.md", content="x")):
        assert status(c9_writes_in_remit(assembled(call))) is Status.FAIL, call.input


def test_c9_correction_may_regenerate_plan_json():
    plan = bash("uv run python -m fpl plan --gw 2 --out data/decisions/gw2/plan.json")
    assert status(c9_writes_in_remit(run(plan, kind=CORRECTION))) is Status.PASS


def test_c9_live_manifest_allows_flags_managed_files_only():
    before = {"data/raw/gw2/bootstrap.json": "a"}
    after = {"data/raw/gw2/bootstrap.json": "b", "data/raw/gw2/.archive/bootstrap-x.json": "a",
             "data/raw/gw2/flags-delta-x.json": "c",
             "data/raw/gw2/.meta/flags-delta-x.json": "c", FINAL: "d"}
    assert status(c9_writes_in_remit(assembled(workspace=live_ws(before, after)))) \
        is Status.PASS
    stray = after | {"data/analysis/gw2/players-DEF.json": "e"}
    result = c9_writes_in_remit(assembled(workspace=live_ws(before, stray)))
    assert result.status is Status.FAIL and "players-DEF" in result.evidence


def test_c10_forbids_git_mutation_posts_and_auth_reads():
    for command in ("git checkout -- data/decisions/gw2/final.md", "git -C . reset --hard",
                    "uv run python -m fpl make-transfers --gw 2 --apply", "cat data/auth.json",
                    "curl https://example.invalid"):
        assert status(c10_nothing_forbidden(assembled(bash(command)))) is Status.FAIL, command
    allowed = bash("test -e data/auth.json && echo yes; git diff -U0 -- x; git status")
    assert status(c10_nothing_forbidden(assembled(allowed))) is Status.PASS
    allowed = bash("grep -n MED review.md; ls data/auth.json 2>&1; ls -la data/auth.json; "
                   "ls data/decisions/gw4/ data/auth.json 2>&1")
    assert status(c10_nothing_forbidden(assembled(allowed))) is Status.PASS


def test_c10_ignores_forbidden_words_inside_written_file_content():
    prose = bash(f"cat > {FINAL} <<'EOF'\nNever run git commit here.\nEOF")
    assert status(c10_nothing_forbidden(run(FLAGS, prose))) is Status.PASS


def test_c11_checks_appended_rows():
    good = "| GW2 | 2026-10-09 | A7 | DATA | finding | data/x | open |"
    bad = "| GW2 | 2026-10-09 | FIN | DATA | finding | data/x | open |"
    append = "cat <<'EOF' >> docs/backlog.md\n{}\nEOF"
    assert status(c11_backlog_rows_well_formed(assembled(bash(append.format(good))))) \
        is Status.PASS
    result = c11_backlog_rows_well_formed(assembled(bash(append.format(bad))))
    assert result.status is Status.FAIL and "FIN" in result.evidence
    assert status(c11_backlog_rows_well_formed(assembled())) is Status.NA


# --- C12–C14 ----------------------------------------------------------------


FIXED = ("Gate: PASS (flags exit 0)\nWritten: data/decisions/gw2/final.md\n"
         "Transfers: none; hit 0\nLedger rows for the cycle report: S1 standing (GW1)")


def test_c12_line_and_word_budgets():
    assert status(c12_return_budget(assembled())) is Status.NA
    long = "\n".join(f"line {i}" for i in range(13))
    assert status(c12_return_budget(assembled(report=long, instructions="At most 12 lines"))) \
        is Status.FAIL
    words = " ".join(["w"] * 151)
    assert status(c12_return_budget(assembled(report=words, instructions="≤150 words"))) \
        is Status.FAIL


def test_c12_fixed_format_allows_only_the_keyed_lines():
    spec = f"{MARK_RETURN_FORMAT}. At most 12 lines."
    assert status(c12_return_budget(assembled(report=FIXED, instructions=spec))) is Status.PASS
    fenced = f"```\n{FIXED}\n```"
    assert status(c12_return_budget(assembled(report=fenced, instructions=spec))) is Status.PASS
    chatty = FIXED + "\nI also double-checked everything."
    result = c12_return_budget(assembled(report=chatty, instructions=spec))
    assert result.status is Status.FAIL and "double-checked" in result.evidence


def test_c13_strict_form_needs_exactly_the_surfaced_rows():
    spec = f"... {MARK_CYCLE_ROWS} ..."
    assert status(c13_cycle_report_rows(assembled(report=FIXED, instructions=spec))) \
        is Status.PASS
    both = FIXED.replace("S1 standing (GW1)", "S1 standing (GW1), S2 rejected (GW4)")
    assert status(c13_cycle_report_rows(assembled(report=both, instructions=spec))) \
        is Status.FAIL
    assert status(c13_cycle_report_rows(assembled(report="Gate: PASS", instructions=spec))) \
        is Status.FAIL


def test_c13_loose_form_flags_closed_rows_after_a_cycle_report_mention():
    loose = "### For your cycle report\nS1 standing; S2 rejected"
    result = c13_cycle_report_rows(assembled(report=loose))
    assert result.status is Status.FAIL and "S2" in result.evidence
    assert status(c13_cycle_report_rows(assembled(report="done"))) is Status.NA


def test_c14_a_stop_return_quotes_the_gate_and_claims_no_impact():
    quoted = "REOPEN\ngate: 1 of 15 ids changed\n   423 Shaw: chance_of_playing_next_round 75 -> 50"
    assert status(c14_no_impact_claims(reopen(quoted))) is Status.PASS
    claim = quoted + "\nCutting Shaw's p_start raises that marginal."
    result = c14_no_impact_claims(reopen(claim))
    assert result.status is Status.FAIL and "p_start" in result.evidence
    assert status(c14_no_impact_claims(assembled())) is Status.NA


def test_c14_a_quoted_gate_line_cannot_carry_an_impact_claim():
    tail = "REOPEN\n   423 Shaw: chance_of_playing_next_round 75 -> 50 — EP6 drops 0.4"
    result = c14_no_impact_claims(reopen(tail))
    assert result.status is Status.FAIL and "EP6" in result.evidence
    news = "REOPEN\n   423 Shaw: news 'Objective: back for EP training' -> ''"
    assert status(c14_no_impact_claims(reopen(news))) is Status.PASS


# --- C15–C18 ----------------------------------------------------------------


ORIGINAL = "# GW2\n\nintro\n\n## Squad\n\nrows\n\n## STATE\n\n```yaml\nbank: 1.0\n```\n"


def test_c15_correction_replaces_only_the_yaml_and_leads_with_correction():
    good = ORIGINAL.replace("intro\n", "intro\n\n## CORRECTION — plan not applied\n\nwhy\n") \
        .replace("bank: 1.0", "bank: 0.0")
    assert status(c15_correction_surgical(run(kind=CORRECTION, final_before=ORIGINAL,
                                              final_after=good))) is Status.PASS
    lost = good.replace("rows\n", "")
    result = c15_correction_surgical(run(kind=CORRECTION, final_before=ORIGINAL,
                                         final_after=lost))
    assert result.status is Status.FAIL and "rows" in result.evidence
    late = ORIGINAL.replace("## STATE", "## CORRECTION\n\n## STATE")
    assert status(c15_correction_surgical(run(kind=CORRECTION, final_before=ORIGINAL,
                                              final_after=late))) is Status.FAIL
    assert status(c15_correction_surgical(assembled())) is Status.NA


def test_c16_market_basis_line_unless_my_team_succeeded():
    labelled = ORIGINAL.replace("## STATE", "team_value: market basis (last_deadline_value), "
                                "not selling prices\n\n## STATE")
    assert status(c16_market_basis_labelled(run(kind=CORRECTION, final_after=labelled))) \
        is Status.PASS
    assert status(c16_market_basis_labelled(run(kind=CORRECTION, final_after=ORIGINAL))) \
        is Status.FAIL
    my_team = bash("uv run python -m fpl my-team --gw 2", "budget 99.2")
    assert status(c16_market_basis_labelled(run(my_team, kind=CORRECTION,
                                                final_after=ORIGINAL))) is Status.NA


def test_c17_canary_and_key_names_stay_out():
    clean = live_ws(canary="EVAL-X", key_names=("eval_key",))
    assert status(c17_canary_absent(assembled(workspace=clean))) is Status.PASS
    leaked = live_ws(canary="EVAL-X", key_names=("eval_key",), text="token EVAL-X")
    assert status(c17_canary_absent(assembled(workspace=leaked))) is Status.FAIL
    named = assembled(report="used eval_key", workspace=clean)
    assert status(c17_canary_absent(named)) is Status.FAIL


def test_c18_final_check_must_pass_after_the_last_write():
    assert status(c18_final_check_after_write(assembled(FINAL_CHECK))) is Status.PASS
    before = run(FLAGS, FINAL_CHECK, WRITE)
    assert status(c18_final_check_after_write(before)) is Status.FAIL
    same_call = bash(f"cat > {FINAL} <<'EOF'\nx\nEOF\nuv run python -m fpl final-check --gw 2",
                     "PASS P1\nPASS F4")
    assert status(c18_final_check_after_write(run(FLAGS, same_call))) is Status.PASS
    check_first = bash(f"uv run python -m fpl final-check --gw 2; cat > {FINAL} <<'EOF'\nx\nEOF",
                       "PASS P1")
    assert status(c18_final_check_after_write(run(FLAGS, check_first))) is Status.FAIL
    failing = bash("uv run python -m fpl final-check --gw 2", "FAIL F3: bank")
    assert status(c18_final_check_after_write(assembled(failing))) is Status.FAIL


@pytest.mark.parametrize("bad", ["bank 1.0"])
def test_parse_state_of_the_fixture_is_valid(bad):
    assert parse_state(PROPOSAL).gw == GW
    with pytest.raises(ValueError):
        parse_state(PROPOSAL.replace("bank: 1.0", bad))
