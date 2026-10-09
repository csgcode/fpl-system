"""Live team-executor evals: real headless Claude sessions against the fake
FPL server. They cost money, so they run only with `uv run pytest -m live`."""

from __future__ import annotations

import shutil

import pytest

from evals.harness.checks import Status
from evals.harness.workspace import SourceError
from evals.team_executor.cases import LIVE_CASES
from evals.team_executor.live import run_live_case

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(shutil.which("claude") is None, reason="claude is not on PATH"),
]


@pytest.mark.parametrize("case", LIVE_CASES, ids=[c.id for c in LIVE_CASES])
def test_live_case(case):
    try:
        outcome = run_live_case(case, judge=True)
    except SourceError as exc:
        pytest.skip(str(exc))
    print(f"{case.id}: ${outcome.cost.total_cost_usd} → {outcome.out_dir}")
    assert [(r.id, r.evidence) for r in outcome.failures] == []
    assert any(r.status is Status.PASS for r in outcome.results)
    assert outcome.judge is not None and outcome.judge.passed, outcome.judge
