"""Squad-optimizer graders on synthetic runs: each check's PASS, FAIL and NA
paths, without any recorded data."""

from __future__ import annotations

from dataclasses import replace

import pytest

from evals.harness.checks import Status
from evals.harness.transcript import ToolCall, Transcript
from evals.squad_optimizer.checks import (
    MARK_ARCHIVE,
    MARK_BENCH_CHECK,
    MARK_OBJECTIVE,
    MARK_RAW_CAPTAIN,
    MARK_RETURN_FORMAT,
    LiveWorkspace,
    OptimizerRun,
    expected_mechanical,
    l_live_workspace,
    o1_state_compiles,
    o2_money_and_free_transfers,
    o3_transfer_rule,
    o4_objective_fidelity,
    o5_xi_and_bench,
    o6_captain,
    o7_ledger,
    o8_writes_in_remit,
    o9_nothing_forbidden,
    o10_return_budget,
    o11_backlog_rows,
    o12_rerun_archives,
    o13_bench_check,
)
from fpl.models import Bootstrap, Position
from fpl.objective import Market, Move, Row, evaluate_plan
from tests.factories import bootstrap_payload, event_payload, player_payload, team_payload

GW = 5
G, D, M, F = Position.GKP, Position.DEF, Position.MID, Position.FWD
LAYOUT = {1: G, 2: G, **{i: D for i in range(3, 8)}, **{i: M for i in range(8, 13)},
          **{i: F for i in range(13, 16)}, 20: M, 21: M}
EP = {1: 5, 2: 1, 3: 4, 4: 4, 5: 4, 6: 2, 7: 2, 8: 5, 9: 5, 10: 5, 11: 3, 12: 3, 13: 6, 14: 4,
      15: 1, 20: 4, 21: 3.2}
P0 = {2: 0.03}
SQUAD = list(range(1, 16))
ORDER = [1, 3, 4, 5, 8, 9, 10, 11, 12, 13, 14, 2, 6, 7, 15]
PASS, FAIL, NA = Status.PASS, Status.FAIL, Status.NA


def view(eps=None, shares=None):
    eps = {**EP, **(eps or {})}
    return {pid: Row(pid, f"P{pid}", pos, pid, 50, "a", (float(eps[pid]),) * 6,
                     P0.get(pid, 1.0), "LOW", (shares or {}).get(pid, 0.0))
            for pid, pos in LAYOUT.items()}


def bootstrap():
    players = [player_payload(id=pid, web_name=f"P{pid}", team=pid, element_type=int(pos),
                              now_cost=50) for pid, pos in LAYOUT.items()]
    teams = [team_payload(id=pid, short_name=f"T{pid:02d}") for pid in LAYOUT]
    return Bootstrap.model_validate(bootstrap_payload(
        elements=players, teams=teams, events=[event_payload(id=GW, is_next=True)]))


def state(gw, order, *, captain=13, vice=8, bank=0.0, team_value=75.0, ft=2,
          transfers=(), chip="null"):
    lines = [f"gw: {gw}", "team_id: 1", f"team_value: {team_value}", f"bank: {bank}",
             f"free_transfers_banked: {ft}", "chips_used: []"]
    if transfers:
        lines.append("transfers_made:")
        lines += [f"  - {{out: P{o}, in: P{i}, cost: {c}}}" for o, i, c in transfers]
    else:
        lines.append("transfers_made: []")
    lines += [f"chip: {chip}", "chip_plan: []", "picks:"]
    lines += [f"  - {{id: {pid}, name: P{pid}, position: {slot}, "
              f"captain: {str(pid == captain).lower()}, vice: {str(pid == vice).lower()}}}"
              for slot, pid in enumerate(order, start=1)]
    return "\n".join(["```yaml", *lines, "```", ""])


LEDGER = ("## Suggestions\n\nRead data/suggestions.md through S1\n\n"
          "| S# | GW | Status | Reason |\n|---|---|---|---|\n| S1 | 4 | rejected | no |\n")
SUGGESTIONS = ("| S# | Date | From GW | Until GW | Suggestion |\n|---|---|---|---|---|\n"
               "| S1 | 2026-09-01 |  |  | hold |\n")
MOVE_ORDER = [20 if pid == 11 else pid for pid in ORDER]
BASELINE_LINE = "baseline: blend {:.3f} prior {:.3f}"


def proposal(order=MOVE_ORDER, *, prose="", **kw):
    kw.setdefault("transfers", ((11, 20, 0),))
    return f"# GW{GW}\n\n{prose}\n\n{LEDGER}\n## STATE\n\n{state(GW, order, **kw)}"


def bash(command, tool_id="t"):
    return ToolCall(tool_id, "Bash", {"command": command}, None)


def make_run(text=None, *, calls=(), report="done", instructions="spec", kind="weekly",
             eps=None, shares=None, before=None, workspace=None, suggestions=SUGGESTIONS,
             free=1):
    blend = view(eps, shares)
    return OptimizerRun(
        transcript=Transcript("p", tuple(calls), report, None),
        instructions=instructions, root="/ws", gw=GW, kind=kind,
        proposal=proposal() if text is None else text, proposal_before=before,
        previous_final=f"# GW4\n\n{LEDGER}\n{state(GW - 1, ORDER)}",
        suggestions=suggestions, review=None, blend=blend, prior=blend,
        market=Market({pid: 50 for pid in SQUAD}, 0, free, "relayed"),
        bootstrap=bootstrap(), c20_active=True, workspace=workspace)


def reference_gain(run):
    report = evaluate_plan(SQUAD, [Move(11, 20)], run.market, run.blend, run.prior)
    return report


# --- O1–O3 --------------------------------------------------------------------


def test_o1_passes_a_compiling_state_and_fails_a_malformed_one():
    assert o1_state_compiles(make_run()).status is PASS
    broken = proposal().replace("bank: 0.0", "bank 0.0")
    result = o1_state_compiles(make_run(broken))
    assert result.status is FAIL and "STATE" in result.evidence


def test_o1_treats_the_no_hit_note_of_a_transfer_chip_as_info():
    result = o1_state_compiles(make_run(proposal(chip="wildcard")))
    assert result.status is PASS and "INFO" in result.evidence


def test_o2_checks_bank_team_value_free_transfers_and_hit_cost():
    assert o2_money_and_free_transfers(make_run(proposal(ft=1))).status is PASS
    for text, word in ((proposal(ft=1, bank=0.5), "bank"),
                       (proposal(ft=2), "free_transfers_banked"),
                       (proposal(ft=1, team_value=76.0), "team_value"),
                       (proposal(ft=1, transfers=((11, 20, 4),)), "cost")):
        result = o2_money_and_free_transfers(make_run(text))
        assert result.status is FAIL and word in result.evidence


def test_o3_grades_each_move_against_the_gate():
    result = o3_transfer_rule(make_run(proposal(ft=1)))
    assert result.status is PASS and "P11 → P20 +6.000" in result.evidence
    weak = [21 if pid == 11 else pid for pid in ORDER]
    result = o3_transfer_rule(make_run(proposal(weak, ft=1, transfers=((11, 21, 0),))))
    assert result.status is FAIL and "free gate" in result.evidence


# --- O4 -------------------------------------------------------------------------


def test_o4_loose_needs_the_baseline_and_the_plan_gain_quoted():
    run = make_run()
    report = reference_gain(run)
    quoted = f"objective {report.baseline[0]:.2f}; gain +{report.gain[0]:.3f}"
    assert o4_objective_fidelity(make_run(proposal(prose=quoted))).status is PASS
    result = o4_objective_fidelity(make_run(proposal(prose="no numbers")))
    assert result.status is FAIL and "baseline" in result.evidence


def test_o4_strict_needs_the_objective_lines_equal_to_a_rerun():
    run = make_run()
    report = reference_gain(run)
    lines = (BASELINE_LINE.format(*report.baseline) + "\n"
             f"plan: P11 → P20 — blend {report.gain[0]:+.3f} prior {report.gain[1]:+.3f}; bank 0.0")
    good = make_run(proposal(prose=lines), instructions=MARK_OBJECTIVE)
    assert o4_objective_fidelity(good).status is PASS
    bad = make_run(proposal(prose=lines.replace(f"{report.gain[0]:+.3f}", "+9.999")),
                   instructions=MARK_OBJECTIVE)
    assert o4_objective_fidelity(bad).status is FAIL
    missing = make_run(proposal(prose="none"), instructions=MARK_OBJECTIVE)
    assert "`baseline:`" in o4_objective_fidelity(missing).evidence


# --- O5–O6 ----------------------------------------------------------------------


def test_o5_accepts_the_reference_xi_and_refuses_a_worse_starter():
    assert o5_xi_and_bench(make_run()).status is PASS
    swapped = [15 if pid == 14 else 14 if pid == 15 else pid for pid in MOVE_ORDER]
    result = o5_xi_and_bench(make_run(proposal(swapped)))
    assert result.status is FAIL and "P15" in result.evidence


def test_o5_near_tie_is_free_unless_c20_shares_differ():
    eps = {6: 3.9, 12: 3.95}
    order = [1, 3, 4, 5, 8, 9, 10, 20, 6, 13, 14, 2, 12, 7, 15]  # DEF 3.9 over MID 3.95
    assert o5_xi_and_bench(make_run(proposal(order), eps=eps)).status is PASS
    result = o5_xi_and_bench(make_run(proposal(order), eps=eps, shares={12: 0.3}))
    assert result.status is FAIL and "C20" in result.evidence


def test_o5_bench_order():
    bad = MOVE_ORDER[:11] + [2, 15, 6, 7]
    result = o5_xi_and_bench(make_run(proposal(bad), eps={15: 1.0, 6: 2.0}))
    assert result.status is FAIL and "bench order" in result.evidence
    gk_last = MOVE_ORDER[:11] + [6, 7, 15, 2]
    assert "slot 12" in o5_xi_and_bench(make_run(proposal(gk_last))).evidence


def test_o6_captain_is_the_top_starter_with_the_nailed_tiebreak():
    assert o6_captain(make_run()).status is PASS
    result = o6_captain(make_run(proposal(captain=14)))
    assert result.status is FAIL and "P13" in result.evidence
    close = {14: 5.7}
    assert o6_captain(make_run(proposal(captain=14), eps=close)).status is FAIL
    nailed = make_run(proposal(captain=14), eps=close, instructions=MARK_RAW_CAPTAIN)
    nailed = replace(nailed, blend={**nailed.blend, 13: replace(nailed.blend[13], p_start0=0.7)})
    assert o6_captain(nailed).status is PASS


# --- O7 -------------------------------------------------------------------------

ROWS = "| S# | Date | From GW | Until GW | Suggestion |\n|---|---|---|---|---|\n"


def test_expected_mechanical_withdraw_expiry_and_malformed():
    text = ROWS + "\n".join([
        "| S1 | d |  |  | hold |",
        "| S2 | d |  | 4 | old steer |",
        "| S3 | d |  |  | withdraw S1 |",
        "| S4 | d | five |  | bad gw |",
        "| S5 | d |  |  | withdraw S9 |",
        "| S6 | d |  | 3 | closed already |",
    ])
    previous = ("Read data/suggestions.md through S6\n\n| S# | GW | Status | Reason |\n"
                "|---|---|---|---|\n| S6 | 3 | rejected | no |\n")
    assert expected_mechanical(text, previous, 5) == {
        "S1": "withdrawn", "S2": "expired", "S3": "followed", "S4": "malformed",
        "S5": "rejected"}


def test_o7_runs_final_check_and_the_mechanical_rows():
    assert o7_ledger(make_run()).status is PASS
    dropped = proposal().replace("| S1 | 4 | rejected | no |\n", "")
    assert o7_ledger(make_run(dropped)).status is FAIL
    withdraw = SUGGESTIONS + "| S2 | 2026-09-02 |  |  | withdraw S1 |\n"
    result = o7_ledger(make_run(suggestions=withdraw))
    assert result.status is FAIL and "S2 absent, want followed" in result.evidence


# --- O8–O11 ---------------------------------------------------------------------


def test_o8_writes():
    ok = [bash("cd /tmp/s && python3 x.py > out.md"),
          bash("cat <<'EOF' >> docs/backlog.md\n| a |\nEOF"),
          ToolCall("w", "Write", {"file_path": f"/ws/data/decisions/gw{GW}/squad-proposal.md",
                                  "content": "x"}, None)]
    assert o8_writes_in_remit(make_run(calls=ok)).status is PASS
    result = o8_writes_in_remit(make_run(calls=[bash("rm -f data/analysis/gw5/x.json")]))
    assert result.status is FAIL and "call 1 writes data/analysis/gw5/x.json" in result.evidence
    assert o8_writes_in_remit(make_run(calls=[bash("echo x > docs/backlog.md")])).status is FAIL


def test_o9_forbidden_commands_outside_quotes():
    assert o9_nothing_forbidden(make_run(calls=[bash('grep -n "git commit" CLAUDE.md')])
                                ).status is PASS
    for command in ('pkill -f "python3 -"', "git stash", "uv run python -m fpl my-team --gw 5",
                    "curl https://x", "kill -9 123"):
        assert o9_nothing_forbidden(make_run(calls=[bash(command)])).status is FAIL, command


def test_o10_budget_and_fixed_lines():
    assert o10_return_budget(make_run()).status is NA
    long = "\n".join(f"line {i}" for i in range(13))
    assert o10_return_budget(make_run(report=long, instructions="At most 12 lines")
                             ).status is FAIL
    fixed = "Written: x\nTransfers: none\nStray prose"
    result = o10_return_budget(make_run(report=fixed, instructions=MARK_RETURN_FORMAT))
    assert result.status is FAIL and "Stray prose" in result.evidence


def test_o11_backlog_rows():
    good = "cat <<'EOF' >> docs/backlog.md\n| GW5 | d | A4 | CODE | x | y | open |\nEOF"
    assert o11_backlog_rows(make_run(calls=[bash(good)])).status is PASS
    assert o11_backlog_rows(make_run(calls=[bash(good.replace("'EOF'", "EOF"))])
                            ).status is FAIL
    assert "A5" in o11_backlog_rows(make_run(calls=[bash(good.replace("A4", "A5"))])).evidence
    assert o11_backlog_rows(make_run()).status is NA


# --- O12, O13, L ----------------------------------------------------------------


def live(**kw):
    return LiveWorkspace(before={}, after={}, backlog_appended="", served="", **kw)


def test_o12_rerun_archives_the_previous_proposal():
    assert o12_rerun_archives(make_run()).status is NA
    rerun = dict(kind="revision", before="old", instructions=MARK_ARCHIVE)
    assert o12_rerun_archives(make_run(**rerun)).status is FAIL
    assert o12_rerun_archives(make_run(**rerun, workspace=live(archived_before="old"))
                              ).status is PASS
    assert o12_rerun_archives(make_run(**rerun, workspace=live(archived_before="new"))
                              ).status is FAIL


@pytest.mark.parametrize(("line", "status"), [
    ("Bench check: P2 (12, p 0.03)", PASS), ("Bench check: none", FAIL),
    ("Bench check: P2, P6", FAIL),
    ("Bench check: P2 (12, 0.03) — P15 (15, 0.50) sits at the threshold, not under it", PASS)])
def test_o13_names_exactly_the_dead_bench_slots(line, status):
    run = make_run(report=line, instructions=MARK_BENCH_CHECK)
    assert o13_bench_check(run).status is status


def test_l_refuses_changed_ep_files_and_network():
    changed = LiveWorkspace({"data/analysis/gw5/players-MID.json": "a"}, {}, "", "")
    assert l_live_workspace(make_run(workspace=changed)).status is FAIL
    networked = LiveWorkspace({}, {}, "", served='{"hit": "bootstrap"}')
    assert l_live_workspace(make_run(workspace=networked)).status is FAIL
    assert l_live_workspace(make_run(workspace=live())).status is PASS
