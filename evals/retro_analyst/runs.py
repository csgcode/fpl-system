"""Builds a RetroRun from a recorded transcript (replay): the retro is the
file the run wrote, the truth ledger and the prior retros come from the cycle
commits."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from evals.harness.freeze import FROZEN_ROOT
from evals.harness.shell import agent_written_files
from evals.harness.transcript import Transcript, load_transcript
from evals.retro_analyst.cases import PROMPT_AND_SPEC, REPO_ROOT, SPEC_FIXTURE, ReplayCase
from evals.retro_analyst.checks import RetroRun, backlog_from_transcript
from fpl.calibrate import CalibrationReport


def git_text(commit: str, path: str, repo: Path = REPO_ROOT) -> str | None:
    blob = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"],
                          capture_output=True, check=False)
    return blob.stdout.decode("utf-8") if blob.returncode == 0 else None


def ledger_at(commit: str, round_: int) -> CalibrationReport | None:
    text = git_text(commit, f"data/retro/gw{round_}-calibration.json")
    return CalibrationReport.model_validate(json.loads(text)) if text else None


def prior_retros_at(commit: str, round_: int) -> dict[str, str]:
    found = {}
    for k in range(1, round_):
        text = git_text(commit, f"data/retro/gw{k}.md")
        if text is not None:
            found[f"gw{k}.md"] = text
    return found


def replay_instructions(case: ReplayCase, transcript: Transcript) -> str:
    """GW3 and GW4 embedded the spec in the prompt; GW5 read the file, which
    was the spec fixture at the time."""
    prompt = transcript.prompt or ""
    if case.instructions == PROMPT_AND_SPEC:
        return f"{prompt}\n\n{SPEC_FIXTURE.read_text(encoding='utf-8')}"
    return prompt


def replay_run(case: ReplayCase) -> RetroRun:
    transcript = load_transcript(case.fixture)
    written = agent_written_files(transcript, FROZEN_ROOT, apply_edits=True)
    retro = written.get(f"data/retro/gw{case.round}.md")
    return RetroRun(
        transcript=transcript,
        instructions=replay_instructions(case, transcript),
        root=FROZEN_ROOT,
        round=case.round,
        retro=retro if isinstance(retro, str) else None,
        ledger=ledger_at(case.cycle_commit, case.round),
        final_md=git_text(case.cycle_commit, f"data/decisions/gw{case.round}/final.md"),
        prior_retros=prior_retros_at(case.cycle_commit, case.round),
        backlog_appended=backlog_from_transcript(transcript),
    )
