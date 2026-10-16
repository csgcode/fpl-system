"""Live player-analyst evals: real headless Claude sessions in throwaway
workspaces. They cost money (about $1.50–$5 a case on opus), so they run only
with `uv run pytest -m live`; the full-suite cases need `--full` on the
runner instead."""

from __future__ import annotations

import shutil

import pytest

from evals.harness.workspace import SourceError
from evals.player_analyst.cases import DEFAULT_LIVE, live_case
from evals.player_analyst.live import run_judge_calibration, run_live_case

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(shutil.which("claude") is None, reason="claude is not on PATH"),
]


@pytest.mark.parametrize("case_id", DEFAULT_LIVE)
def test_live_case(case_id):
    try:
        outcome = run_live_case(live_case(case_id), judge=True)
    except SourceError as exc:
        pytest.skip(str(exc))
    print(f"{case_id}: ${outcome.cost.total_cost_usd} → {outcome.out_dir}")
    assert [(r.id, r.evidence) for r in outcome.failures] == []


def test_judge_calibration():
    code, cost = run_judge_calibration()
    print(f"judge calibration: ${cost:.4f}")
    assert code == 0
