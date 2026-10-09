"""Builds a PlanBuilderRun from a recorded transcript (replay)."""

from __future__ import annotations

from evals.harness.freeze import FROZEN_ROOT
from evals.harness.transcript import load_transcript
from evals.plan_builder.cases import ReplayCase
from evals.plan_builder.checks import PlanBuilderRun


def replay_run(case: ReplayCase) -> PlanBuilderRun:
    transcript = load_transcript(case.fixture)
    return PlanBuilderRun(transcript=transcript, instructions=transcript.prompt or "",
                          root=FROZEN_ROOT, gw=case.gw, workspace=None)
