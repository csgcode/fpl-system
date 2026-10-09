"""Live fixture-analyst evals: real headless Claude sessions in throwaway
workspaces. They cost money (about $1.50 a case on opus), so they run only
with `uv run pytest -m live`."""

from __future__ import annotations

import shutil

import pytest

from evals.fixture_analyst.cases import LIVE_CASES
from evals.fixture_analyst.live import run_live_case
from evals.harness.checks import Status
from evals.harness.workspace import SourceError

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
    if outcome.judge is not None:
        assert outcome.judge.passed, outcome.judge
