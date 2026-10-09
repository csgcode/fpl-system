"""Builds a UsageRun from a recorded transcript (replay)."""

from __future__ import annotations

from evals.harness.freeze import FROZEN_ROOT
from evals.harness.transcript import load_transcript
from evals.usage_collector.cases import ReplayCase
from evals.usage_collector.graders import UsageRun


def replay_run(case: ReplayCase) -> UsageRun:
    transcript = load_transcript(case.fixture)
    return UsageRun(transcript=transcript, instructions=transcript.prompt or "", root=FROZEN_ROOT,
                    gw=case.gw, expect=case.expect, workspace=None)
