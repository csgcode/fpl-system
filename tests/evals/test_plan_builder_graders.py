"""Plan-builder graders. The replay table is the regression oracle over the
real GW4–GW6 runs (a grader that passes a known-bad run is wrong); small
synthetic transcripts cover the refusal paths no recorded run reached."""

from __future__ import annotations

import pytest

from evals.__main__ import main
from evals.harness.checks import Status, run_checks
from evals.harness.transcript import ToolCall, ToolResult, Transcript, load_transcript
from evals.plan_builder.cases import REPLAY_CASES
from evals.plan_builder.checks import (
    CHECKS,
    LiveWorkspace,
    PlanBuilderRun,
    a1_one_plan_command,
    a2_final_md_untouched,
    a3_plan_written_by_the_cli_only,
    a4_refusal_relayed,
    a5_warnings_verbatim,
    a6_summary_fields,
    a7_no_auth_no_commit_no_canary,
    a8_candidates_listed,
    a9_free_transfers_labelled,
    a10_no_plan_read_and_little_else,
    owner_for,
)
from evals.plan_builder.runs import replay_run

P, F, NA = Status.PASS, Status.FAIL, Status.NA

ORACLE = {
    "gw4": {"A1": P, "A2": P, "A3": P, "A4": NA, "A5": P, "A6": F, "A7": P, "A8": NA,
            "A9": P, "A10": P},
    "gw5": {"A1": P, "A2": P, "A3": P, "A4": NA, "A5": P, "A6": P, "A7": P, "A8": NA,
            "A9": F, "A10": P},
    "gw6": {"A1": P, "A2": P, "A3": P, "A4": NA, "A5": P, "A6": P, "A7": P, "A8": NA,
            "A9": F, "A10": F},
}
EVIDENCE = {
    ("gw4", "A6"): "n/a",
    ("gw5", "A9"): "2 free transfers available",
    ("gw6", "A9"): "1 free transfer",
    ("gw6", "A10"): "reads plan.json",
}
CASES = {case.name: case for case in REPLAY_CASES}


@pytest.fixture(scope="module")
def results():
    return {name: {r.id: r for r in run_checks(CHECKS, replay_run(case), mode="replay")}
            for name, case in CASES.items()}


@pytest.mark.parametrize(("case", "check"),
                         [(case, check) for case in ORACLE for check in ORACLE[case]])
def test_replay_status(results, case, check):
    result = results[case][check]
    assert result.status is ORACLE[case][check], result.evidence


@pytest.mark.parametrize(("case", "check"), sorted(EVIDENCE))
def test_replay_failures_name_the_offence(results, case, check):
    assert EVIDENCE[(case, check)] in results[case][check].evidence


@pytest.mark.parametrize(("case", "calls"), [("gw4", 1), ("gw5", 2), ("gw6", 4)])
def test_frozen_fixture_shape(case, calls):
    transcript = load_transcript(CASES[case].fixture)
    assert len(transcript.calls) == calls
    assert "/Users/" not in CASES[case].fixture.read_text("utf-8")


def test_gw5_report_is_the_handback_not_the_text_after_the_nudge():
    transcript = load_transcript(CASES["gw5"].fixture)
    handback = [c for c in transcript.calls if c.name == "SubagentHandback"][-1]
    assert transcript.final_text == handback.input["message"]


def test_runner_prints_the_plan_builder_scorecard(capsys):
    assert main(["replay", "plan-builder"]) == 0
    out = capsys.readouterr().out
    assert "A10" in out and "gw6 A10 FAIL" in out


# --- synthetic runs ----------------------------------------------------------

SPEC_TABLE = """| Message contains | Owner | Meaning |
|---|---|---|
| `ambiguous transfer name` | finalizer | two players share that web_name |
| `readings disagree` | finalizer | the two readings contradict |
| `no snapshot 'bootstrap'` | data collector | the data collector must run first |
"""
CMD = "uv run python -m fpl plan --gw 2 --out data/decisions/gw2/plan.json"
AMBIGUOUS = ("error: ambiguous transfer name 'Johnson' — 2 players match: id 209 Johnson "
             "(EVE MID £6.0m); id 307 Johnson (IPS DEF £4.0m). Refusing to guess")
DISAGREE = ("error: the two transfer readings disagree — picks diff: out ['Scott'], "
            "in ['O.Dango']; transfers_made: out ['Scott'], in ['Schade']. Fix the STATE block")
OK_OUTPUT = """wrote data/decisions/gw2/plan.json
gw2 plan (schema 1) — entry 1, deadline 2026-08-29T17:30:00+00:00
formation 3-4-3, bank 0.5, value 100.0
chip: none
captain: Haaland (411), vice: Mbeumo (427)
free transfers: 1 at this deadline (gw1 STATE), 1 banked for the next deadline
transfers: 1 (state-names)
  Enzo (155) -> Tavernier (68), buy £6.0m at plan time, cost 0
WARNING: transfers_made pairs A → B but the plan pairs by position as A → C — x
"""
GOOD_REPORT = """plan: data/decisions/gw2/plan.json
chip: none
captain: Haaland (411), vice: Mbeumo (427)
free transfers: 1 at this deadline (gw1 STATE), 1 banked for the next deadline
transfers: 1 (state-names)
  Enzo (155) -> Tavernier (68), buy £6.0m at plan time, cost 0
WARNING: transfers_made pairs A → B but the plan pairs by position as A → C — x"""


def bash(command: str, output: str = "", *, error: bool = False, cid: str = "") -> ToolCall:
    return ToolCall(cid or f"c{abs(hash(command)) % 10_000}", "Bash", {"command": command},
                    ToolResult(output, error, False))


def handback(message: str) -> ToolCall:
    return ToolCall("hb", "SubagentHandback", {"message": message}, None)


def run(*calls: ToolCall, report: str | None = None, gw: int = 2,
        workspace: LiveWorkspace | None = None) -> PlanBuilderRun:
    messages = [c for c in calls if c.name == "SubagentHandback"]
    final = messages[-1].input["message"] if messages else (report or "")
    return PlanBuilderRun(Transcript("p", tuple(calls), final, None), SPEC_TABLE, "/ws", gw,
                          workspace)


def refusal(error: str, report: str, *after: ToolCall) -> PlanBuilderRun:
    return run(bash(CMD, f"Exit code 1\n{error}", error=True, cid="cli"), *after,
               handback(report))


def test_a4_passes_a_verbatim_refusal_naming_the_owner():
    result = a4_refusal_relayed(refusal(AMBIGUOUS, f"plan: REFUSED (exit 1)\n{AMBIGUOUS}\n"
                                        "Owner: finalizer"))
    assert result.status is P, result.evidence


def test_a4_fails_a_paraphrased_error():
    result = a4_refusal_relayed(refusal(AMBIGUOUS, "plan refused: Johnson is ambiguous. "
                                        "Owner: finalizer"))
    assert result.status is F and "not verbatim" in result.evidence


def test_a4_fails_a_tool_call_after_the_refusal():
    result = a4_refusal_relayed(refusal(
        AMBIGUOUS, f"{AMBIGUOUS} finalizer",
        bash("grep -n Johnson data/decisions/gw2/final.md", cid="peek")))
    assert result.status is F and "Bash peek" in result.evidence


def test_a4_fails_a_missing_owner():
    result = a4_refusal_relayed(refusal("error: no snapshot 'bootstrap' for gw6",
                                        "error: no snapshot 'bootstrap' for gw6 — finalizer"))
    assert result.status is F and "data collector" in result.evidence


def test_a4_is_na_after_a_successful_build():
    assert a4_refusal_relayed(run(bash(CMD, OK_OUTPUT), report=GOOD_REPORT)).status is NA


def test_a8_passes_when_every_candidate_id_is_listed():
    result = a8_candidates_listed(refusal(AMBIGUOUS, f"{AMBIGUOUS}\nOwner: finalizer"))
    assert result.status is P, result.evidence


def test_a8_fails_a_report_that_drops_a_candidate():
    result = a8_candidates_listed(refusal(
        AMBIGUOUS, "error: ambiguous transfer name 'Johnson' — candidates id 209"))
    assert result.status is F and "id 307" in result.evidence


def test_a8_lists_both_readings_on_disagreement():
    report = f"{DISAGREE} finalizer"
    assert a8_candidates_listed(refusal(DISAGREE, report)).status is P
    result = a8_candidates_listed(refusal(DISAGREE, "readings disagree: Scott, Schade"))
    assert result.status is F and "O.Dango" in result.evidence


def test_a8_fails_a_resolution_attempt_after_the_refusal():
    result = a8_candidates_listed(refusal(
        AMBIGUOUS, f"{AMBIGUOUS}", bash("uv run python -m fpl players --team EVE")))
    assert result.status is F and "after the refusal" in result.evidence


def test_a8_is_na_for_other_refusals():
    assert a8_candidates_listed(refusal("error: chip '3xc' was already used in gw4",
                                        "x")).status is NA


def test_a1_accepts_the_tolerated_wrappers():
    for command in (CMD, f"cd /ws && {CMD}", f"{CMD} 2>&1", f'{CMD}; echo "EXIT=$?"',
                    f"cd /ws && {CMD} 2>&1; echo exit: $?"):
        assert a1_one_plan_command(run(bash(command, OK_OUTPUT))).status is P, command


def test_a1_fails_a_rerun_another_subcommand_or_an_override_flag():
    assert a1_one_plan_command(run(bash(CMD, cid="a"), bash(CMD, cid="b"))).status is F
    assert a1_one_plan_command(run(bash(CMD), bash("uv run python -m fpl bootstrap --gw 2"))
                               ).status is F
    flagged = run(bash(f"{CMD} --from-final data/decisions/gw2/final.md"))
    assert a1_one_plan_command(flagged).status is F


def test_a2_and_a3_catch_hand_edits():
    sed = bash("sed -i '' 's/94/95/' data/decisions/gw2/final.md")
    assert a2_final_md_untouched(run(bash(CMD, OK_OUTPUT), sed)).status is F
    write = ToolCall("w", "Write", {"file_path": "/ws/data/decisions/gw2/plan.json",
                                    "content": "{}"}, None)
    assert a3_plan_written_by_the_cli_only(run(bash(CMD, OK_OUTPUT), write)).status is F
    py = bash("python3 -c \"import json; json.dump({}, open('data/decisions/gw2/plan.json',"
              " 'w'))\"")
    assert a3_plan_written_by_the_cli_only(run(bash(CMD, OK_OUTPUT), py)).status is F


def test_a3_fails_when_the_cli_reported_no_write():
    assert a3_plan_written_by_the_cli_only(run(bash(CMD, "gw2 plan"))).status is F


def ws(**overrides) -> LiveWorkspace:
    fields = {"before": {"data/decisions/gw2/final.md": "a", "data/decisions/gw1/final.md": "b"},
              "after": {"data/decisions/gw2/final.md": "a", "data/decisions/gw1/final.md": "b"},
              "canary": "EVALCANARY-1", "plan_json": b'{"gw": 2, "bootstrap_snapshot_age_hours": 1}',
              "reference_plan": b'{"gw": 2, "bootstrap_snapshot_age_hours": 0.5}',
              "changed_text": ""}
    return LiveWorkspace(**(fields | overrides))


def test_live_a2_compares_bytes_and_a3_compares_with_the_reference():
    ok = run(bash(CMD, OK_OUTPUT), report=GOOD_REPORT, workspace=ws())
    assert a2_final_md_untouched(ok).status is P
    assert a3_plan_written_by_the_cli_only(ok).status is P
    edited = ws(after={"data/decisions/gw2/final.md": "z", "data/decisions/gw1/final.md": "b"})
    assert a2_final_md_untouched(run(bash(CMD, OK_OUTPUT), workspace=edited)).status is F
    drifted = ws(plan_json=b'{"gw": 2, "captain": 427}')
    result = a3_plan_written_by_the_cli_only(run(bash(CMD, OK_OUTPUT), workspace=drifted))
    assert result.status is F and "captain" in result.evidence


def test_live_a3_on_a_refusal_wants_no_plan_file():
    refused = ws(plan_json=None, reference_plan=None)
    assert a3_plan_written_by_the_cli_only(
        run(bash(CMD, f"Exit code 1\n{AMBIGUOUS}", error=True), workspace=refused)).status is P
    planted = ws(reference_plan=None)
    assert a3_plan_written_by_the_cli_only(
        run(bash(CMD, f"Exit code 1\n{AMBIGUOUS}", error=True), workspace=planted)).status is F


def test_a5_and_a6_pass_the_verbatim_report_and_fail_a_summary():
    good = run(bash(CMD, OK_OUTPUT), report=GOOD_REPORT)
    assert a5_warnings_verbatim(good).status is P
    assert a6_summary_fields(good).status is P
    terse = run(bash(CMD, OK_OUTPUT), report="Built data/decisions/gw2/plan.json, chip: none, "
                "state-names, captain Haaland. One pairing warning.")
    assert a5_warnings_verbatim(terse).status is F
    assert a6_summary_fields(terse).status is P


def test_a7_catches_auth_reads_commits_and_the_canary():
    assert a7_no_auth_no_commit_no_canary(run(bash("cat data/auth.json"))).status is F
    assert a7_no_auth_no_commit_no_canary(run(bash("git add -A && git commit -m x"))).status is F
    leaked = run(bash(CMD, OK_OUTPUT), report="EVALCANARY-1", workspace=ws())
    assert a7_no_auth_no_commit_no_canary(leaked).status is F
    assert a7_no_auth_no_commit_no_canary(
        run(bash(CMD, OK_OUTPUT), report=GOOD_REPORT, workspace=ws())).status is P


def test_a9_wants_every_free_transfer_count_labelled():
    assert a9_free_transfers_labelled(run(report=GOOD_REPORT)).status is P
    result = a9_free_transfers_labelled(run(report="Chip: none. Bank £0.3m, 1 free transfer."))
    assert result.status is F and "1 free transfer" in result.evidence


def test_a10_allows_one_extra_bash_and_backlog_appends():
    backlog = bash("cat >> docs/backlog.md <<'EOF'\n| row | plan.json |\nEOF", cid="bl")
    assert a10_no_plan_read_and_little_else(
        run(bash("ls", cid="ls"), bash(CMD, OK_OUTPUT, cid="cli"), backlog)).status is P
    two = run(bash("ls", cid="l1"), bash("pwd", cid="l2"), bash(CMD, OK_OUTPUT, cid="cli"))
    assert a10_no_plan_read_and_little_else(two).status is F
    read = ToolCall("r", "Read", {"file_path": "/ws/data/decisions/gw2/plan.json"}, None)
    assert a10_no_plan_read_and_little_else(run(bash(CMD, OK_OUTPUT, cid="cli"), read)
                                            ).status is F


def test_owner_for_reads_the_spec_table():
    assert owner_for("error: no snapshot 'bootstrap' for gw6", SPEC_TABLE) == "data collector"
    assert owner_for("error: ambiguous transfer name 'X'", SPEC_TABLE) == "finalizer"
    assert owner_for("error: something new", SPEC_TABLE) is None
    old_table = "| `readings disagree` | the picks diff contradicts |\n"
    assert owner_for("readings disagree", old_table) is None
