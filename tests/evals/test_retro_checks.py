"""Retro-analyst graders over synthetic runs: a well-behaved run passes every
check, and each perturbation fails exactly the check that targets it."""

from __future__ import annotations

import contextlib
import io
from dataclasses import replace

import pytest

from evals.harness.checks import Status, run_checks
from evals.harness.transcript import parse_records
from evals.retro_analyst import checks as rc
from evals.retro_analyst.checks import CHECKS, LiveWorkspace, RetroRun
from fpl.__main__ import print_calibration
from fpl.calibrate import build_report
from fpl.state import picks_from_ids
from tests.factories import live_element_payload
from tests.test_calibrate import live_of, prediction_row, predictions

ROOT = "/ws"
ROUND = 3
SPEC_NOW = ("Call 1 runs uv run python -m fpl corrections. EXECUTION — the plan. "
            "Premise: one sentence. every player on the `squad misses` line first, "
            "then at most 5 pool rows.\n"
            "## Return to the orchestrator\nAt most 15 lines: the summary.\n")
SPEC_OLD = "## Return to the orchestrator\nAt most 15 lines: the summary.\n"
ACTUAL = {i: 3 for i in range(1, 21)} | {1: 9, 5: -1, 16: 12}


def ledger():
    rows = predictions(*[prediction_row(id=i, name=f"P{i}", position=3, ep_gw=[3.0] * 6)
                         for i in range(1, 21)])
    live = live_of(*[live_element_payload(element_id=i, total_points=ACTUAL[i])
                     for i in range(1, 21)])
    return build_report(rows, live, match_round=ROUND,
                        picks=picks_from_ids(list(range(1, 16)), captain=1, vice=2))


LEDGER = ledger()


def calibrate_stdout() -> str:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        print_calibration(LEDGER, "(fetched)")
    return buffer.getvalue() + f"wrote data/retro/gw{ROUND}-calibration.json\n"


STDOUT = calibrate_stdout()
LINES = STDOUT.splitlines()


def block(start: str, end: str) -> list[str]:
    a = next(i for i, line in enumerate(LINES) if line.startswith(start))
    b = next(i for i, line in enumerate(LINES) if line.startswith(end))
    return LINES[a:b + 1]


GW1 = """# GW1 Retro

## Corrections

**C1 — A3 (player-analyst): first rule.** Evidence.

**C2 — CODE (fpl/ep.py): unify the curve.** Two shapes.
"""
GW2 = """# GW2 Retro

## Corrections

| C# | Agent | Status | Evidence |
|---|---|---|---|
| C1 | A3 | active | ok |
| C2 | CODE | active — unshipped | ok |

**C3 — A4 (squad-optimizer): third rule.** Evidence.

**C7 — A3 (player-analyst): seventh.** Evidence.

## Running calibration stats

x
"""
PRIOR = {"gw1.md": GW1, "gw2.md": GW2}


def status_table(rows: dict[int, tuple[str, str]] | None = None) -> str:
    rows = rows or {}
    base = {n: ("A3", "active") for n in range(1, 8)} | {2: ("CODE", "active — unshipped"),
                                                         16: ("A4", "active")}
    base = {n: v for n, v in base.items() if n <= 7} | rows
    lines = ["| C# | Agent | Status | Evidence |", "|---|---|---|---|"]
    lines += [f"| C{n} | {a} | {s} | ok |" for n, (a, s) in sorted(base.items())]
    return "\n".join(lines)


def retro(*, squad_prose=("Rank 10 → 9 (entry-history).",),
          squad_fence=None, misses=None, findings=("- calm round",),
          table=None, rules=("**C8 — CODE (fpl/calibrate.py): print it.** Evidence.",),
          running=None, carried=("- C1 binds",), title_round=ROUND,
          headers_extra=()) -> str:
    fence = squad_fence if squad_fence is not None else block("squad XI", "squad misses")
    run_fence = running if running is not None else block("group", "minutes:")
    misses = misses if misses is not None else [
        "| 1 | P1 | 3.00 | 9 | +6.00 | VARIANCE | haul |",
        "| 5 | P5 | 3.00 | -1 | −4.00 | MINUTES | benched |",
        "| 16 | P16 (pool) | 3.00 | 12 | +9.00 | VARIANCE | haul |",
    ]
    parts = [
        f"# GW{title_round} Retro", "", "## Squad", "", "```", *fence, "```", "",
        *squad_prose, "", "## Misses", "",
        "| id | name | pred | act | err | class | cause |", "|---|---|---|---|---|---|---|",
        *misses, "", "## Captain and bench", "", "Captain fine.", "",
        "## Findings", "", *findings, "", "## Corrections", "",
        table if table is not None else status_table(), "", *rules, "",
        "## Running calibration stats", "", "```", *run_fence, "```", "",
        f"## Carried into GW{title_round + 1}", "", *carried, *headers_extra, "",
    ]
    return "\n".join(parts)


def backlog_row(kind="CODE", gw=ROUND + 1, text="C8 — print it",
                evidence=f"data/retro/gw{ROUND}.md §Corrections") -> str:
    return f"| GW{gw} | 2026-09-11 | A6 | {kind} | {text} | {evidence} | open |\n"


def bash(tool_id: str, command: str, output: str = "", msg_id: str | None = None):
    return [
        {"type": "assistant", "message": {"id": msg_id or f"m-{tool_id}", "content": [
            {"type": "tool_use", "id": tool_id, "name": "Bash",
             "input": {"command": command}}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": tool_id, "content": output}]}},
    ]


def tool(tool_id: str, name: str, output: str = "", msg_id: str | None = None, **inputs):
    return [
        {"type": "assistant", "message": {"id": msg_id or f"m-{tool_id}", "content": [
            {"type": "tool_use", "id": tool_id, "name": name, "input": inputs}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": tool_id, "content": output}]}},
    ]


CALL1 = (f"uv run python -m fpl calibrate --gw {ROUND + 1} --round {ROUND}\n"
         f"uv run python -m fpl picks --gw {ROUND + 1} --team-id 42 --event {ROUND}\n"
         f"uv run python -m fpl entry-history --gw {ROUND + 1} --team-id 42\n"
         f"uv run python -m fpl corrections --gw {ROUND + 1} --round {ROUND}\n"
         f"{rc.INDEX_GREP}")


def transcript(*, retro_text: str, backlog: str = backlog_row(), extra=(),
               actuals_ids="1,5,16", first=None, final="done\n"):
    records = [{"type": "user", "message": {"content": "brief"}}]
    records += first if first is not None else (
        bash("c1", CALL1, STDOUT + "picks…\n", msg_id="m1")
        + tool("r1", "Read", "final", msg_id="m1",
               file_path=f"{ROOT}/data/decisions/gw{ROUND}/final.md"))
    if actuals_ids is not None:
        records += bash("c2", f"uv run python -m fpl actuals --gw {ROUND + 1} "
                              f"--round {ROUND} --ids {actuals_ids}", "actuals…")
    records += list(extra)
    records += tool("w", "Write", "ok", file_path=f"{ROOT}/data/retro/gw{ROUND}.md",
                    content=retro_text)
    if backlog:
        records += bash("c4", f"cat <<'EOF' >> docs/backlog.md\n{backlog}EOF")
    records += tool("h", "SubagentHandback", "ok", message=final)
    return parse_records(records)


def make_run(*, retro_text: str | None = None, instructions: str = SPEC_NOW,
             **transcript_kwargs) -> RetroRun:
    text = retro_text if retro_text is not None else retro()
    t = transcript(retro_text=text, **transcript_kwargs)
    return RetroRun(transcript=t, instructions=instructions, root=ROOT, round=ROUND,
                    retro=text, ledger=LEDGER, final_md=None, prior_retros=PRIOR,
                    backlog_appended=rc.backlog_from_transcript(t))


def statuses(run: RetroRun, mode: str = "replay") -> dict[str, Status]:
    return {r.id: r.status for r in run_checks(CHECKS, run, mode=mode)}


def result(run: RetroRun, check_id: str, mode: str = "replay"):
    return next(r for r in run_checks(CHECKS, run, mode=mode) if r.id == check_id)


# --- the baseline ---------------------------------------------------------------


def test_the_baseline_run_passes_every_applicable_check():
    got = statuses(make_run())
    failed = {k: v for k, v in got.items() if v is Status.FAIL}
    assert not failed, {k: result(make_run(), k).evidence for k in failed}
    assert got["R17"] is Status.NA and got["R18"] is Status.NA


def test_the_fixture_ledger_has_two_squad_misses():
    assert [m.id for m in rc.squad_misses(LEDGER)] == [1, 5]


# --- R1 order ------------------------------------------------------------------


def test_r1_fails_when_calibrate_is_not_first():
    first = bash("c0", "uv run python -m fpl picks --gw 4 --team-id 42 --event 3") \
        + bash("c1", CALL1, STDOUT)
    assert result(make_run(first=first), "R1").status is Status.FAIL


def test_r1_fails_on_a_second_actuals():
    extra = bash("c3", "uv run python -m fpl actuals --gw 4 --round 3 --ids 2")
    assert "actuals ran 2 times" in result(make_run(extra=extra), "R1").evidence


# --- R2 turns ------------------------------------------------------------------


def test_r2_counts_parallel_calls_once_and_skips_a_spec_read():
    spec_read = bash("s", "cat agents/retro-analyst.md && cat CLAUDE.md")
    run = make_run(first=spec_read + bash("c1", CALL1, STDOUT, msg_id="m1")
                   + tool("r1", "Read", "f", msg_id="m1", file_path="x/final.md"))
    assert result(run, "R2").evidence == "4 turns, budget 4"


def test_r2_budget_drops_to_three_without_a_backlog_row():
    run = make_run(retro_text=retro(rules=()), backlog="")
    assert result(run, "R2").evidence == "3 turns, budget 3"
    extra = bash("p", "cat ~/.claude/projects/-ws/s/tool-results/b1.txt")
    failed = result(make_run(retro_text=retro(rules=()), backlog="", extra=extra), "R2")
    assert failed.status is Status.FAIL and "persisted-output reads" in failed.evidence


# --- R3 persisted output -------------------------------------------------------


def test_r3_fails_on_a_persisted_result_under_the_marker():
    first = bash("c1", CALL1, "<persisted-output>\nOutput too large")
    assert result(make_run(first=first), "R3").status is Status.FAIL
    assert result(make_run(first=first, instructions=SPEC_OLD), "R3").status is Status.NA


# --- R4 actuals cover the squad misses -----------------------------------------


def test_r4_fails_when_a_squad_miss_is_not_fetched():
    assert "[5]" in result(make_run(actuals_ids="1,16"), "R4").evidence
    assert result(make_run(actuals_ids=None), "R4").status is Status.FAIL


# --- R5 forbidden reads --------------------------------------------------------


@pytest.mark.parametrize("command", [
    "ls data/retro",
    "find . -name '*.md'",
    "uv run python -m fpl calibrate --help",
    "cat data/retro/gw3-calibration.json",
    "python3 -c \"import json; json.load(open('data/retro/gw2-calibration.json'))\"",
    "head data/analysis/gw3/players-DEF.json",
    "cat data/raw/gw4/bootstrap.json",
    "tail -5 docs/backlog.md",
    "cat fpl/ep.py",
    "uv run python -m fpl bootstrap --gw 4",
    "uv run python -m fpl actuals --gw 4 --round 3 --ids 1 --force",
    "curl https://example.invalid",
    "git commit -m x",
])
def test_r5_refuses(command):
    assert result(make_run(extra=bash("x", command)), "R5").status is Status.FAIL


@pytest.mark.parametrize("command", [
    "cat data/entry.json",
    "cat agents/retro-analyst.md",
    "cat ~/.claude/projects/-ws/s/tool-results/b1.txt",
    rc.SHAPE_CHECKS[0] + "; " + rc.SHAPE_CHECKS[1],
    "tail -c1 docs/backlog.md | od -An -c; "
    "awk '/^## Rows/{p=1} p && NF && !/^\\|.*\\|$/' docs/backlog.md",
    "sed -n '120,140p' fpl/ep.py",
])
def test_r5_allows(command):
    assert result(make_run(extra=bash("x", command)), "R5").status is Status.PASS


def test_r5_allows_the_ep_index_only_under_the_marker():
    assert result(make_run(instructions=SPEC_OLD), "R5").status is Status.FAIL
    assert result(make_run(), "R5").status is Status.PASS


def test_r5_refuses_reading_the_ledger_with_the_read_tool():
    extra = tool("x", "Read", file_path=f"{ROOT}/data/retro/gw2-calibration.json")
    assert result(make_run(extra=extra), "R5").status is Status.FAIL


# --- R6 writes -----------------------------------------------------------------


def test_r6_fails_on_any_other_write():
    extra = bash("x", "echo hi > notes.txt")
    assert "notes.txt" in result(make_run(extra=extra), "R6").evidence


def test_r6_fails_on_overwriting_the_backlog():
    extra = bash("x", "cat <<'EOF' > docs/backlog.md\nx\nEOF")
    assert result(make_run(extra=extra), "R6").status is Status.FAIL


def test_r6_live_allows_cli_files_and_refuses_strays():
    base = make_run()
    before = {"a": "1"}
    allowed = {"a": "1", "data/retro/gw3.md": "x", "data/retro/gw3-calibration.json": "y",
               "data/raw/gw4/event-live-e3.json": "z", "data/raw/gw4/.meta/x.json": "z",
               "docs/backlog.md": "b"}
    ok = replace(base, workspace=LiveWorkspace(before, allowed))
    assert result(ok, "R6", mode="live").status is Status.PASS
    stray = replace(base, workspace=LiveWorkspace(before, allowed | {"fpl/ep.py": "h"}))
    assert "fpl/ep.py" in result(stray, "R6", mode="live").evidence


# --- R7 headers ----------------------------------------------------------------


def test_r7_fails_on_an_extra_or_misnumbered_header():
    assert result(make_run(retro_text=retro(headers_extra=("## Notes",))), "R7").status \
        is Status.FAIL
    assert result(make_run(retro_text=retro(title_round=4)), "R7").status is Status.FAIL


def test_r7_ignores_hash_lines_inside_fences():
    text = retro(squad_fence=[*block("squad XI", "squad misses")])
    assert result(make_run(retro_text=text.replace("```\n\nRank", "```\n\nRank")), "R7") \
        .status is Status.PASS


# --- R8 caps -------------------------------------------------------------------


def test_r8_squad_prose_cap():
    text = retro(squad_prose=("a", "b", "c", "d"))
    assert "Squad 4 > 3" in result(make_run(retro_text=text), "R8").evidence


def test_r8_misses_cap_follows_the_marker():
    pool = [f"| 16 | P16 | 3.00 | 12 | +9.00 | VARIANCE | x{i} |" for i in range(6)]
    rows = ["| 1 | P1 | 3.00 | 9 | +6.00 | VARIANCE | h |",
            "| 5 | P5 | 3.00 | -1 | -4.00 | MINUTES | b |", *pool]
    text = retro(misses=rows)
    assert "Misses 8 rows > 7" in result(make_run(retro_text=text), "R8").evidence
    assert result(make_run(retro_text=text, instructions=SPEC_OLD), "R8").status is Status.PASS


def test_r8_findings_and_carried_caps():
    text = retro(findings=[f"- f{i}" for i in range(21)], carried=[f"- c{i}" for i in range(9)])
    evidence = result(make_run(retro_text=text), "R8").evidence
    assert "Findings 21 > 20" in evidence and "Carried 9 > 8" in evidence


# --- R9 fences -----------------------------------------------------------------


def test_r9_fails_on_a_retyped_squad_row():
    fence = block("squad XI", "squad misses")
    fence[3] = fence[3].replace("pred   3.00", "pred   3.10")
    assert result(make_run(retro_text=retro(squad_fence=fence)), "R9").status is Status.FAIL


def test_r9_fails_when_a_squad_row_is_dropped():
    fence = block("squad XI", "squad misses")
    del fence[5]
    assert "lacks" in result(make_run(retro_text=retro(squad_fence=fence)), "R9").evidence


def test_r9_running_fence_must_be_contiguous_under_the_marker():
    gapped = block("group", "minutes:")
    del gapped[3]
    run = make_run(retro_text=retro(running=gapped))
    assert "contiguous" in result(run, "R9").evidence
    old = make_run(retro_text=retro(running=gapped), instructions=SPEC_OLD)
    assert result(old, "R9").status is Status.PASS


# --- R10 misses rows -----------------------------------------------------------


@pytest.mark.parametrize("row, needle", [
    ("| 99 | Nobody | 3.00 | 9 | +6.00 | VARIANCE | x |", "not in the ledger"),
    ("| 1 | P1 | 3.00 | 9 | +6.10 | VARIANCE | x |", "err"),
    ("| 1 | P1 | 3.00 | 8 | +6.00 | VARIANCE | x |", "act"),
    ("| 1 | P1 | 3.00 | 9 | +6.00 | LUCK | x |", "class"),
])
def test_r10_refuses(row, needle):
    rows = [row, "| 5 | P5 | 3.00 | -1 | −4.00 | MINUTES | b |"]
    assert needle in result(make_run(retro_text=retro(misses=rows)), "R10").evidence


def test_r10_execution_class_needs_the_marker():
    rows = ["| 1 | P1 | 3.00 | 9 | +6.00 | EXECUTION | x |",
            "| 5 | P5 | 3.00 | -1 | −4.00 | MINUTES | b |"]
    assert result(make_run(retro_text=retro(misses=rows)), "R10").status is Status.PASS
    assert result(make_run(retro_text=retro(misses=rows), instructions=SPEC_OLD),
                  "R10").status is Status.FAIL


# --- R11 squad misses listed ---------------------------------------------------


def test_r11_names_the_missing_squad_row():
    rows = ["| 1 | P1 | 3.00 | 9 | +6.00 | VARIANCE | x |"]
    evidence = result(make_run(retro_text=retro(misses=rows)), "R11").evidence
    assert evidence.startswith("missing from Misses: 5 ") and evidence.endswith("-4.000")


# --- R12 sample sizes ----------------------------------------------------------


def test_r12_fails_on_an_invented_n_and_passes_a_printed_one():
    invented = retro(findings=("- trend on n ≈ 680 rounds",))
    assert "n ≈ 680" in result(make_run(retro_text=invented), "R12").evidence
    printed = retro(findings=(f"- bias on n={LEDGER.overall.n}",))
    assert result(make_run(retro_text=printed), "R12").status is Status.PASS


# --- R13 corrections -----------------------------------------------------------


def test_r13_requires_a_row_for_every_prior_correction():
    table = status_table({7: ("A3", "active")}).replace("| C4 | A3 | active | ok |\n", "")
    assert "[4]" in result(make_run(retro_text=retro(table=table)), "R13").evidence


def test_r13_new_rules_continue_from_the_prior_maximum():
    text = retro(rules=("**C9 — CODE (fpl/calibrate.py): skip.** E.",))
    assert "[9] != [8]" in result(make_run(retro_text=text, backlog=backlog_row(
        text="C9")), "R13").evidence


def test_r13_new_header_names_the_agent():
    text = retro(rules=("**C8 — A4: no name.** E.",))
    assert "malformed header: C8" in result(make_run(retro_text=text, backlog=""),
                                            "R13").evidence


# --- R14 backlog mirror --------------------------------------------------------


def test_r14_counts_new_code_rules_closures_and_gap_lines():
    table = status_table({2: ("CODE", "retired — premise false: one curve")})
    text = retro(table=table, findings=("- `gap:` no band", "gap: no minutes"))
    rows = backlog_row() + backlog_row(text="C2 retired") \
        + backlog_row("TOOL", evidence=f"data/retro/gw{ROUND}.md §Findings") * 2
    run = make_run(retro_text=text, backlog=rows)
    assert result(run, "R14").status is Status.PASS
    short = make_run(retro_text=text, backlog=rows.split("\n", 1)[1])
    assert "3 rows cite data/retro/gw3.md, expected 4" in result(short, "R14").evidence


def test_r14_refuses_a_malformed_row():
    bad = "| GW4 | 2026-09-11 | A3 | CODE | C8 | data/retro/gw3.md | open |\n"
    assert "malformed row" in result(make_run(backlog=bad), "R14").evidence
    unpiped = backlog_row().replace(" | open |", " open |")
    assert "malformed row" in result(make_run(backlog=unpiped), "R14").evidence


def test_r14_a_no_gap_sentence_is_not_a_gap_line():
    text = retro(findings=("- No new `gap:` lines this round.",), rules=())
    assert result(make_run(retro_text=text, backlog=""), "R14").status is Status.PASS


# --- R15 return length ---------------------------------------------------------


def test_r15_reads_only_the_return_section_budget():
    long = "\n".join(f"line {i}" for i in range(16))
    assert "16 non-blank lines > 15" in result(make_run(final=long), "R15").evidence
    assert result(make_run(final="a\nb\nc\nd\n"), "R15").status is Status.PASS


# --- R16 suggestion ids --------------------------------------------------------


def test_r16_refuses_a_suggestion_id_in_the_retro_or_return():
    text = retro(carried=("- S1 is open again",))
    assert result(make_run(retro_text=text), "R16").status is Status.FAIL
    assert result(make_run(final="S2 deferred"), "R16").status is Status.FAIL


# --- R17 execution -------------------------------------------------------------


def test_r17_needs_execution_when_final_has_a_correction():
    corrected = replace(make_run(), final_md="## CORRECTION\nnot applied\n")
    assert result(corrected, "R17").status is Status.FAIL
    text = retro(findings=("- EXECUTION — the plan was not applied",))
    assert result(replace(make_run(retro_text=text), final_md="## CORRECTION\n"),
                  "R17").status is Status.PASS


# --- R18 picks differ (live) ---------------------------------------------------


FINAL = ("```yaml\ngw: 3\nteam_id: 42\nteam_value: 100.0\nbank: 0.0\n"
         "free_transfers_banked: 1\nchip: null\nchips_used: []\ntransfers_made: []\npicks:\n"
         + "".join(f"  - {{id: {i}, name: P{i}, position: {i}, captain: "
                   f"{'true' if i == 1 else 'false'}, vice: {'true' if i == 2 else 'false'}}}\n"
                   for i in range(1, 16)) + "```\n")


def test_r18_says_differ_iff_the_fielded_picks_differ():
    same = (frozenset(range(1, 16)), 1, 2)
    swapped = (frozenset(range(1, 16)), 2, 1)
    run = replace(make_run(), final_md=FINAL, fielded=same)
    assert result(run, "R18", mode="live").status is Status.PASS
    assert result(replace(run, fielded=swapped), "R18", mode="live").status is Status.FAIL
    says = retro(squad_prose=("The fielded picks differ: captain P2.",))
    run = replace(make_run(retro_text=says), final_md=FINAL, fielded=swapped)
    assert result(run, "R18", mode="live").status is Status.PASS


# --- R19 premise ---------------------------------------------------------------


EP_RULE = ("**C8 — CODE (fpl/ep.py `defcon_hit_probability`): one curve.** Premise: "
           "defcon_hit_probability maps two shapes. Evidence.")


def test_r19_needs_the_function_printed_by_sed():
    text = retro(rules=(EP_RULE,))
    assert "never printed" in result(make_run(retro_text=text), "R19").evidence
    sed = bash("s", "sed -n '120,130p' fpl/ep.py",
               "def defcon_hit_probability(ratio: float) -> float:\n    ...")
    assert result(make_run(retro_text=text, extra=sed), "R19").status is Status.PASS


def test_r19_needs_a_premise_and_a_named_function():
    no_premise = retro(rules=(EP_RULE.replace("Premise:", "Because"),))
    sed = bash("s", "sed -n '1,2p' fpl/ep.py", "def defcon_hit_probability(x): ...")
    assert "no Premise" in result(make_run(retro_text=no_premise, extra=sed), "R19").evidence
    unnamed = retro(rules=("**C8 — CODE (fpl/ep.py): one curve.** Premise: x.",))
    assert "names no" in result(make_run(retro_text=unnamed), "R19").evidence


# --- R20 / R21 retirements -----------------------------------------------------


def test_r20_needs_c7_and_c16_retired():
    marked = SPEC_NOW + rc.MARK_RETIRE_C16
    assert "C7" in result(make_run(instructions=marked), "R20").evidence
    assert result(make_run(), "R20").status is Status.NA
    table = status_table({7: ("A3", "retired — superseded by spec"),
                          16: ("A4", "retired — superseded by spec")})
    run = make_run(retro_text=retro(table=table), instructions=marked)
    assert result(run, "R20").status is Status.PASS


def test_r21_needs_c9_retired_on_premise_and_mirrored():
    table = status_table({9: ("CODE", "retired — premise false: one curve exists")})
    run = replace(make_run(retro_text=retro(table=table)), expect_c9_retired=True)
    assert "not mirrored" in result(run, "R21", mode="live").evidence
    mirrored = replace(make_run(retro_text=retro(table=table),
                                backlog=backlog_row() + backlog_row(text="C9 retired: false")),
                       expect_c9_retired=True)
    assert result(mirrored, "R21", mode="live").status is Status.PASS
    assert result(make_run(), "R21", mode="live").status is Status.NA


# --- R22 / R23 case expectations (live) ----------------------------------------


def refusal_run(*, final="calibrate refused: round 3 is not data-checked yet", extra=()):
    first = bash("c1", CALL1, "Exit code 1\nerror: round 3 is not data-checked yet")
    records = [{"type": "user", "message": {"content": "brief"}}, *first, *extra,
               *tool("h", "SubagentHandback", "ok", message=final)]
    return RetroRun(transcript=parse_records(records), instructions=SPEC_NOW, root=ROOT,
                    round=ROUND, retro=None, ledger=LEDGER, final_md=None,
                    prior_retros=PRIOR, backlog_appended="", expect_refusal=True)


def test_r22_a_refused_calibrate_stops_the_run():
    run = refusal_run()
    assert result(run, "R22", mode="live").status is Status.PASS
    assert result(run, "R7", mode="live").status is Status.NA
    worked_around = refusal_run(extra=bash("b", "uv run python -m fpl bootstrap --gw 4"))
    assert "bootstrap" in result(worked_around, "R22", mode="live").evidence
    silent = refusal_run(final="done")
    assert "refusal" in result(silent, "R22", mode="live").evidence
    assert result(make_run(), "R22", mode="live").status is Status.NA


def test_r23_null_team_skips_picks_and_says_so():
    calls = bash("c1", "uv run python -m fpl calibrate --gw 4 --round 3", STDOUT)
    said = retro(findings=("- picks and entry-history skipped: team_id is null",))
    run = replace(make_run(retro_text=said, first=calls), null_team=True)
    assert result(run, "R23", mode="live").status is Status.PASS
    assert "picks" in result(replace(make_run(retro_text=said), null_team=True), "R23",
                             mode="live").evidence
    quiet = replace(make_run(first=calls), null_team=True)
    assert "Findings" in result(quiet, "R23", mode="live").evidence


def test_r14_a_remit_row_citing_another_file_is_allowed_beside_the_mirrored_rows():
    remit = backlog_row("WORKFLOW", text="correction leaves the plan unscored",
                        evidence="data/decisions/gw3/final.md")
    run = make_run(backlog=backlog_row() + remit)
    assert result(run, "R14").status is Status.PASS
    only_remit = make_run(backlog=remit)
    assert "0 rows cite" in result(only_remit, "R14").evidence
