"""Live usage-collector evals: headless haiku sessions over transcript trees
built at test time. They cost money, so they run only with `uv run pytest -m
live`; `uv run python -m evals live usage-collector` runs the same cases."""

from __future__ import annotations

import shutil

import pytest

from evals.harness.checks import Status
from evals.usage_collector.cases import LIVE_CASES
from evals.usage_collector.live import run_live_case

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(shutil.which("claude") is None, reason="claude is not on PATH"),
]
CASES = [c for c in LIVE_CASES if c.live]


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_live_case(case):
    outcome = run_live_case(case)
    print(f"{case.id}: ${outcome.cost.total_cost_usd} → {outcome.out_dir}")
    assert [(r.id, r.evidence) for r in outcome.failures] == []
    assert any(r.status is Status.PASS for r in outcome.results)
