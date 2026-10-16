"""Live retro-analyst evals. The unmarked tests are free: the prompt, the
judge material and its parsing, the premise gold set. The `live` tests start
real headless Claude sessions and cost money, so they run only with
`uv run pytest -m live`."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from evals.harness.workspace import SourceError
from evals.retro_analyst import judge as jg
from evals.retro_analyst.cases import LIVE_CASES, REPLAY_CASES, live_case
from evals.retro_analyst.prompt import build_prompt
from evals.retro_analyst.runs import replay_run

REPLAYS = {case.name: case for case in REPLAY_CASES}
claude = pytest.mark.skipif(shutil.which("claude") is None, reason="claude is not on PATH")


def test_prompt_is_run_facts_only():
    prompt = build_prompt(Path("/ws"), live_case("L1-gw5"))
    assert "Repo root: /ws" in prompt
    assert "M = 5; current cycle N = 6. Output: data/retro/gw5.md" in prompt
    assert "team_id: 8455344. Today's date for backlog rows: 2026-10-09" in prompt
    assert "Read agents/retro-analyst.md in full first" in prompt
    assert "Never run `git commit`" in prompt
    for leak in ("EXECUTION", "C9", "Haaland", "411", "premise", "expect"):
        assert leak not in prompt


def test_prompt_says_null_when_the_team_is_null():
    assert "team_id: null." in build_prompt(Path("/ws"), live_case("P3-null-team"))


def test_judge_lines_parse_each_verdict():
    answer = "J1 PASS\n**J3** FAIL: planned XI 51 v 58"
    assert jg.parse_judge_lines(answer) == {"J1": ("PASS", ""),
                                            "J3": ("FAIL", "planned XI 51 v 58")}


def test_premise_answer_parses():
    assert jg.parse_premise("FALSE: one anchor table") == (False, "one anchor table")
    assert jg.parse_premise("TRUE: it does") == (True, "it does")
    assert jg.parse_premise("maybe")[0] is None


def test_untraceable_numbers_list_what_no_output_prints():
    numbers = jg.untraceable_numbers(replay_run(REPLAYS["gw5"]))
    assert "994894" in numbers          # the rank move, computed by hand
    assert "58" not in numbers and "4367291" not in numbers


def test_retro_judge_prompt_carries_the_material():
    run = replay_run(REPLAYS["gw4"])
    prompt = jg.build_retro_judge_prompt(run)
    assert prompt.startswith(jg.RETRO_RUBRIC)
    assert "## Misses" in prompt and "## Findings" in prompt
    assert "round 4 calibration —" in prompt
    assert "round 4 actuals" in prompt
    assert "237 Ndiaye" in prompt and "started False" in prompt
    assert "UNTRACEABLE NUMBERS" in prompt


def test_retro_judge_sees_entry_history_and_every_misses_row_truth():
    run = replay_run(REPLAYS["gw5"])
    prompt = jg.build_retro_judge_prompt(run)
    other = prompt.split("OTHER OUTPUTS", 1)[1]
    assert "4367291" in other.replace(",", "") or "4,367,291" in other
    assert "round 5 calibration —" not in other and "corrections — status" not in other
    truth = prompt.split("LEDGER ROWS", 1)[1]
    assert "552 Brobbey" in truth and "53 Manzambi" in truth
    assert "every other number is printed by some output" in prompt


def test_premise_claims_are_the_active_ep_corrections_with_code():
    run = replay_run(REPLAYS["gw5"])
    claims = jg.premise_claims(run, ep_source=jg.git_text("b28927f", "fpl/ep.py") or "")
    assert [c.number for c in claims] == [9]
    assert "defcon_hit_probability" in claims[0].code


def test_gold_set_excerpts_resolve():
    for gold in jg.GOLD:
        code = jg.gold_code(gold)
        assert len(code) > 100, gold.label
        for name in gold.names:
            assert name in code, (gold.label, name)


# --- live -------------------------------------------------------------------


@pytest.mark.live
@claude
def test_judge_calibration():
    """These must hold before judge verdicts on live runs count."""
    cwd = REPLAYS["gw4"].fixture.parent
    lines = {name: jg.run_retro_judge(jg.build_retro_judge_prompt(replay_run(REPLAYS[name])),
                                      cwd=cwd)
             for name in ("gw4", "gw5", "gw3")}
    for name, verdict in lines.items():
        print(f"{name}: {verdict.verdicts} ${verdict.cost_usd}")
    premises = [(gold.label, gold.expected, jg.run_premise_judge(gold.claim, jg.gold_code(gold),
                                                                 cwd=cwd))
                for gold in jg.GOLD]
    for label, expected, (got, reason, cost) in premises:
        print(f"premise {label}: expected {expected}, got {got} ({reason}) ${cost}")
    assert lines["gw4"].status("J1") == "FAIL" and lines["gw4"].status("J3") == "FAIL"
    assert lines["gw5"].status("J1") == "PASS" and lines["gw5"].status("J3") == "FAIL"
    assert lines["gw3"].status("J3") == "PASS"
    assert [got for _, _, (got, _, _) in premises] == [g.expected for g in jg.GOLD]


@pytest.mark.live
@claude
@pytest.mark.parametrize("case", [c for c in LIVE_CASES if c.default], ids=lambda c: c.id)
def test_live_case(case):
    from evals.retro_analyst.live import run_live_case

    try:
        outcome = run_live_case(case, judge=True)
    except SourceError as exc:
        pytest.skip(str(exc))
    print(f"{case.id}: ${outcome.cost.total_cost_usd} judge {outcome.judge} → {outcome.out_dir}")
    assert [(r.id, r.evidence) for r in outcome.failures] == []
