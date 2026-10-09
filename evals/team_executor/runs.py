"""Builds an ExecutorRun from a recorded transcript (replay)."""

from __future__ import annotations

from evals.harness.freeze import FROZEN_ROOT
from evals.harness.transcript import load_transcript
from evals.team_executor.cases import ReplayCase
from evals.team_executor.checks import ExecutorRun


def replay_run(case: ReplayCase) -> ExecutorRun:
    transcript = load_transcript(case.fixture)
    return ExecutorRun(transcript=transcript, instructions=transcript.prompt or "",
                       root=FROZEN_ROOT, gw=case.gw, required_calls=case.required_calls)
