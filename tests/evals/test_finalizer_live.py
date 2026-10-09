"""Live finalizer evals. The unmarked tests are free: the prompt and the
judge's parsing. The `live` tests start real headless Claude sessions and
cost money, so they run only with `uv run pytest -m live`."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from evals.finalizer.cases import LIVE_CASES, REPLAY_CASES, live_case
from evals.finalizer.judge import (
    RUBRIC,
    build_judge_prompt,
    parse_judge_lines,
    run_finalizer_judge,
    without_review_row,
)
from evals.finalizer.live import run_live_case
from evals.finalizer.prompt import build_prompt
from evals.finalizer.runs import replay_run
from evals.harness.workspace import SourceError

REPLAYS = {case.name: case for case in REPLAY_CASES}
claude = pytest.mark.skipif(shutil.which("claude") is None, reason="claude is not on PATH")


def test_prompt_is_run_facts_only():
    prompt = build_prompt(Path("/ws"), live_case("L4-gw5-rerun"))
    assert "Repo root: /ws" in prompt and "Gameweek N = 5" in prompt
    assert "Read agents/finalizer.md in full first" in prompt
    assert "This run follows a REOPEN" in prompt
    assert "Never run `git commit`" in prompt
    for leak in ("PASS", "Shaw", "99.3", "expect", "S2"):
        assert leak not in prompt


def test_a_case_without_lines_has_no_blank_fact():
    prompt = build_prompt(Path("/ws"), live_case("L1-gw6-pass"))
    assert "\n\n" not in prompt and "- \n" not in prompt


def test_judge_lines_parse_each_verdict():
    answer = "J1: PASS\n**J2**: FAIL: claims the marginal rises\nJ3: NA"
    assert parse_judge_lines(answer) == {
        "J1": ("PASS", ""), "J2": ("FAIL", "claims the marginal rises"), "J3": ("NA", "")}


def test_judge_prompt_carries_review_final_return_and_fpl_commands():
    run = replay_run(REPLAYS["gw6"])
    prompt = build_judge_prompt(run)
    assert prompt.startswith(RUBRIC)
    assert "| F1 | 11 Price risk |" in prompt
    assert "| R6 | Overnight price exposure" in prompt
    assert "$ uv run python -m fpl flags --gw 6" in prompt
    assert "$ cat data/decisions/gw6/review.md" not in prompt
    assert run.report in prompt


def test_without_review_row_drops_exactly_one_row():
    final = replay_run(REPLAYS["gw6"]).final_after
    assert final is not None
    trimmed = without_review_row(final, "R6")
    assert "| R6 |" not in trimmed and "| R7 |" in trimmed
    with pytest.raises(ValueError):
        without_review_row(trimmed, "R6")


# --- live -------------------------------------------------------------------


def judge(name: str, **overrides):
    run = replay_run(REPLAYS[name])
    lines = run_finalizer_judge(build_judge_prompt(run, **overrides),
                                cwd=REPLAYS[name].fixture.parent)
    print(f"{name}: {lines.verdicts} ${lines.cost_usd}")
    return lines


@pytest.mark.live
@claude
def test_judge_calibration():
    """These must hold before judge verdicts on live runs count."""
    reopen = judge("gw5-reopen")
    correction = judge("gw5-correction")
    gw6 = judge("gw6")
    gw4 = judge("gw4")
    final = replay_run(REPLAYS["gw6"]).final_after
    assert final is not None
    dropped = judge("gw6", final_text=without_review_row(final, "R6"))
    rerun = judge("gw5-rerun")
    print(f"gw5-rerun J1 (report only): {rerun.verdicts.get('J1')}")
    assert reopen.status("J2") == "FAIL"
    assert correction.status("J3") == "FAIL"
    assert gw6.status("J1") == "PASS" and gw6.status("J3") == "PASS"
    assert gw4.status("J1") == "PASS"
    assert dropped.status("J1") == "FAIL"


@pytest.mark.live
@claude
@pytest.mark.parametrize("case", [c for c in LIVE_CASES if c.default], ids=lambda c: c.id)
def test_live_case(case):
    try:
        outcome = run_live_case(case, judge=True)
    except SourceError as exc:
        pytest.skip(str(exc))
    print(f"{case.id}: ${outcome.cost.total_cost_usd} judge {outcome.judge} → {outcome.out_dir}")
    assert [(r.id, r.evidence) for r in outcome.failures] == []
