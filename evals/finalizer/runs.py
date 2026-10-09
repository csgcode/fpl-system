"""Builds a FinalizerRun from a recorded transcript (replay): the texts come
from the cycle commits, the gate truth from the pinned bootstrap pair."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from evals.finalizer.cases import (
    CORRECTION,
    REOPEN,
    REPO_ROOT,
    SPEC_FIXTURE,
    ReplayCase,
    Source,
)
from evals.finalizer.checks import STOP_REOPEN, FinalizerRun
from evals.harness.freeze import FROZEN_ROOT
from evals.harness.transcript import Transcript, load_transcript
from evals.harness.workspace import SourceError, read_source
from fpl.freshness import FlagChange, flag_delta
from fpl.models import Bootstrap
from fpl.state import parse_state

POSITIONS = ("GKP", "DEF", "MID", "FWD")


def git_text(commit: str, path: str, repo: Path = REPO_ROOT) -> str | None:
    blob = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"],
                          capture_output=True, check=False)
    return blob.stdout.decode("utf-8") if blob.returncode == 0 else None


def load_bootstrap(source: Source | None, repo: Path = REPO_ROOT) -> Bootstrap | None:
    """None when the source is a local archive that is missing or drifted."""
    if source is None:
        return None
    try:
        return Bootstrap.model_validate(json.loads(read_source(repo, source)))
    except SourceError:
        return None


def players_ep(commit: str, gw: int) -> dict[int, float]:
    ep: dict[int, float] = {}
    for position in POSITIONS:
        text = git_text(commit, f"data/analysis/gw{gw}/players-{position}.json")
        for row in json.loads(text) if text else ():
            ep[int(row["id"])] = float(row["ep_gw"][0])
    return ep


def gate_truth(baseline: Bootstrap | None, gate: Bootstrap | None,
               proposal: str | None) -> tuple[FlagChange, ...] | None:
    if baseline is None or gate is None or proposal is None:
        return None
    state = parse_state(proposal)
    ids = {p.id for p in state.picks.picks} if state.picks else set()
    return tuple(flag_delta(baseline.elements, gate.elements, ids))


def replay_instructions(transcript: Transcript) -> str:
    """The prompt plus the spec in force for every recorded run."""
    return f"{transcript.prompt or ''}\n\n{SPEC_FIXTURE.read_text(encoding='utf-8')}"


def replay_run(case: ReplayCase) -> FinalizerRun:
    transcript = load_transcript(case.fixture)
    proposal = git_text(case.cycle_commit, case.decision("squad-proposal.md"))
    if case.kind == CORRECTION:
        final_before = git_text(case.cycle_commit, case.decision("final.md"))
        final_after = git_text(case.after_commit or "", case.decision("final.md"))
        truth = None
    else:
        final_before = None
        final_after = git_text(case.cycle_commit, case.decision("final.md"))
        truth = gate_truth(load_bootstrap(case.baseline), load_bootstrap(case.gate), proposal)
    expect_delta = bool(truth) if truth is not None else case.kind == REOPEN
    stop = STOP_REOPEN if expect_delta else None
    return FinalizerRun(
        transcript=transcript,
        instructions=replay_instructions(transcript),
        root=FROZEN_ROOT,
        gw=case.gw,
        kind=case.kind,
        proposal=proposal,
        review=git_text(case.cycle_commit, case.decision("review.md")),
        previous_final=git_text(case.previous_commit, case.decision("final.md", gw=case.gw - 1)),
        final_before=final_before,
        final_after=None if stop else final_after,
        suggestions_exists=case.suggestions_exists,
        stop_expected=stop,
        truth_changes=truth,
        gate_bootstrap=load_bootstrap(case.gate),
        players_ep=players_ep(case.cycle_commit, case.gw),
    )
