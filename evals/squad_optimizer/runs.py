"""Builds an OptimizerRun from a recorded transcript (replay): the proposal
comes from the cycle commit, the run's own reconstructed writes, or the next
run's first Read of it; the reference figures from the frozen views."""

from __future__ import annotations

import json
import re
import subprocess
from functools import cache
from pathlib import Path

from evals.harness.freeze import FROZEN_ROOT
from evals.harness.shell import agent_written_files
from evals.harness.transcript import Transcript, load_transcript
from evals.harness.workspace import GitBlob, read_source
from evals.squad_optimizer.cases import (
    REPO_ROOT,
    SPEC_FIXTURE,
    VIEWS,
    ReplayCase,
    replay_case,
)
from evals.squad_optimizer.checks import OptimizerRun
from evals.squad_optimizer.views import load_view
from fpl.models import Bootstrap

_READ_PREFIX = re.compile(r"(?m)^\s*\d+\t")


def git_text(blob: GitBlob | None, repo: Path = REPO_ROOT) -> str | None:
    if blob is None:
        return None
    shown = subprocess.run(["git", "-C", str(repo), "show", f"{blob.commit}:{blob.path}"],
                           capture_output=True, check=False)
    return shown.stdout.decode("utf-8") if shown.returncode == 0 else None


def proposal_path(gw: int) -> str:
    return f"data/decisions/gw{gw}/squad-proposal.md"


def read_text(transcript: Transcript, path: str) -> str | None:
    """The content of the first Read of `path`, with the line-number gutter
    removed."""
    for call in transcript.calls:
        if call.name == "Read" and str(call.input.get("file_path", "")).endswith(path) \
                and call.result is not None:
            return _READ_PREFIX.sub("", call.result.text)
    return None


@cache
def case_output(name: str) -> str | None:
    case = replay_case(name)
    if case.output.blob is not None:
        return git_text(case.output.blob)
    source = case.output.source or ""
    if source == "written":
        written = agent_written_files(load_transcript(case.fixture), FROZEN_ROOT,
                                      apply_edits=True)
        text = written.get(proposal_path(case.gw))
        return text if isinstance(text, str) else None
    if source.startswith("read:"):
        reader = replay_case(source.removeprefix("read:"))
        return read_text(load_transcript(reader.fixture), proposal_path(reader.gw))
    return None


def replay_instructions(transcript: Transcript) -> str:
    """The prompt plus the spec in force for every recorded run."""
    return f"{transcript.prompt or ''}\n\n{SPEC_FIXTURE.read_text(encoding='utf-8')}"


@cache
def view_bootstrap(view_id: str) -> Bootstrap:
    return Bootstrap.model_validate(json.loads(read_source(REPO_ROOT,
                                                           VIEWS[view_id].bootstrap)))


def replay_run(case: ReplayCase) -> OptimizerRun:
    transcript = load_transcript(case.fixture)
    blend, prior, _ = load_view(VIEWS[case.view])
    return OptimizerRun(
        transcript=transcript,
        instructions=replay_instructions(transcript),
        root=FROZEN_ROOT,
        gw=case.gw,
        kind=case.kind,
        proposal=case_output(case.name),
        proposal_before=case_output(case.before) if case.before else None,
        previous_final=git_text(case.previous),
        suggestions=git_text(case.suggestions),
        review=git_text(case.review),
        blend=blend,
        prior=prior,
        market=case.market,
        bootstrap=view_bootstrap(case.view),
        c20_active=case.c20_active,
    )
