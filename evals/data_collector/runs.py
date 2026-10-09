"""Builds a CollectorRun from a recorded transcript (replay) or from a
finished headless run in a workspace (live)."""

from __future__ import annotations

from evals.data_collector.cases import ReplayCase
from evals.data_collector.checks import CollectorRun
from evals.harness.freeze import FROZEN_ROOT
from evals.harness.shell import agent_written_files
from evals.harness.transcript import load_transcript


def replay_run(case: ReplayCase) -> CollectorRun:
    transcript = load_transcript(case.fixture)
    written = agent_written_files(transcript, FROZEN_ROOT)
    # Some runs were only told to read the spec file, so the spec text the
    # agent saw is part of what it was instructed.
    instructions = (transcript.prompt or "") + "\n" + case.spec_fixture.read_text("utf-8")
    return CollectorRun(
        transcript=transcript,
        instructions=instructions,
        root=FROZEN_ROOT,
        gw=case.gw,
        team_id=case.team_id,
        auth_present=None,
        meta_md=written.get(f"data/raw/gw{case.gw}/meta.md"),
        previous_gw_truth=case.previous_gw_truth,
        workspace=None,
    )
