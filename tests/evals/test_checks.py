"""The shared check model: marker gating, mode gating and the scorecard."""

from __future__ import annotations

from dataclasses import dataclass

from evals.harness.checks import (
    Check,
    CheckResult,
    Status,
    budget_overruns,
    format_scorecard,
    return_budgets,
    run_checks,
)


@dataclass(frozen=True)
class FakeRun:
    instructions: str


def passing(run):
    return CheckResult.passed("ok")


def failing(run):
    return CheckResult.failed("bad: `cmd`")


def test_checks_run_in_their_mode_and_pass_through_results():
    checks = [Check("C1", passing), Check("C2", failing),
              Check("C3", passing, mode="live")]

    results = run_checks(checks, FakeRun("x"), mode="replay")

    assert [(r.id, r.status) for r in results] == [
        ("C1", Status.PASS), ("C2", Status.FAIL), ("C3", Status.NA)]
    assert results[1].evidence == "bad: `cmd`"
    assert results[2].evidence == "live only"


def test_a_check_is_na_unless_its_marker_is_in_the_instructions():
    check = Check("C9", failing, requires="Return exactly these lines")

    [absent] = run_checks([check], FakeRun("old spec"), mode="live")
    [present] = run_checks([check], FakeRun("… Return exactly these lines …"), mode="live")

    assert absent.status is Status.NA
    assert "Return exactly these lines" in absent.evidence
    assert present.status is Status.FAIL


def test_scorecard_lists_one_row_per_check():
    results = [CheckResult("C1", Status.PASS, "fine"), CheckResult("C2", Status.FAIL, "x")]
    table = format_scorecard({"gw4": results})
    assert "gw4" in table and "C1" in table and "FAIL" in table


def test_return_budgets_reads_line_and_word_limits():
    instructions = ("Return to the orchestrator. At most 12 lines.\n"
                    "Keep it ≤150 words, and at most 15 lines if it fails.")
    assert return_budgets(instructions) == [("lines", 12), ("lines", 15), ("words", 150)]
    assert return_budgets("no limit here") == []
    assert return_budgets("At most 12 lines. ... in at most 12 lines.") == [("lines", 12)]
    assert return_budgets("then a ≤200-word summary") == [("words", 200)]


def test_budget_overruns_count_non_blank_lines_and_words():
    text = "one two\n\nthree\nfour five six\n"
    assert budget_overruns(text, [("lines", 3), ("words", 6)]) == []
    assert budget_overruns(text, [("lines", 2), ("words", 5)]) == [
        "3 non-blank lines > 2", "6 words > 5"]
