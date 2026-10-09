"""Live data-collector evals: real headless Claude sessions against frozen
fixtures with the network stubbed. They cost money, so they run only with
`uv run pytest -m live`. Run the smoke test first; it costs about a cent."""

from __future__ import annotations

import pytest

from evals.data_collector.cases import JUDGE_PASS_GW6, LIVE_CASES, REPLAY_CASES
from evals.data_collector.judge import build_judge_prompt
from evals.data_collector.live import claude_available, run_live_case, smoke
from evals.harness.checks import Status
from evals.harness.live import run_judge
from evals.harness.transcript import load_transcript
from evals.harness.workspace import SourceError

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not claude_available(), reason="claude is not on PATH"),
]
REPLAYS = {case.name: case for case in REPLAY_CASES}


def test_smoke_env_reaches_the_bash_tool(tmp_path):
    echoed, transcript, cost = smoke(tmp_path)
    print(f"smoke cost: ${cost.total_cost_usd}")
    assert transcript.calls, "no tool call parsed from the stream"
    assert echoed == str(tmp_path / "replay")


@pytest.mark.parametrize("case", LIVE_CASES, ids=[c.id for c in LIVE_CASES])
def test_live_case(case):
    try:
        outcome = run_live_case(case)
    except SourceError as exc:
        pytest.skip(str(exc))
    print(f"{case.id}: ${outcome.cost.total_cost_usd} → {outcome.out_dir}")
    assert [(r.id, r.evidence) for r in outcome.failures] == []
    assert any(r.status is Status.PASS for r in outcome.results)


def test_judge_fails_the_gw5_return():
    verdict = run_judge(build_judge_prompt(load_transcript(REPLAYS["gw5"].fixture)),
                        cwd=REPLAYS["gw5"].fixture.parent)
    assert not verdict.passed


def test_judge_passes_a_correct_gw6_return():
    transcript = load_transcript(REPLAYS["gw6"].fixture)
    verdict = run_judge(build_judge_prompt(transcript, return_text=JUDGE_PASS_GW6.read_text()),
                        cwd=REPLAYS["gw6"].fixture.parent)
    assert verdict.passed, verdict.reason


def test_judge_on_the_actual_gw6_return_is_reported():
    """Expected FAIL ("captain element 9" reads the position column as the
    element id). A PASS is a judge miss to review, not a test failure."""
    verdict = run_judge(build_judge_prompt(load_transcript(REPLAYS["gw6"].fixture)),
                        cwd=REPLAYS["gw6"].fixture.parent)
    print(f"gw6 actual return: {'PASS' if verdict.passed else 'FAIL: ' + verdict.reason}")
