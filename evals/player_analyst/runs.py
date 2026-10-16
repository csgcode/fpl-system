"""Builds a PlayerRun from a recorded transcript (replay): outputs from the
cycle commit or the transcript itself, the analysis-time bootstrap from its
pinned archive, the corrections from the retros committed before the run."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from functools import cache
from pathlib import Path

from evals.fixture_analyst.cases import read_blobs
from evals.harness.freeze import FROZEN_ROOT
from evals.harness.shell import agent_written_files, command_lines, normalise
from evals.harness.transcript import load_transcript
from evals.harness.workspace import read_source
from evals.player_analyst.cases import (
    ANALYSIS_BOOTSTRAPS,
    REOPEN,
    REOPEN_FIXTURES,
    REPO_ROOT,
    ReplayCase,
    git_show,
)
from evals.player_analyst.checks import PlayerRun
from fpl.corrections import agent_corrections
from fpl.freshness import flag_delta
from fpl.models import Bootstrap, Position

_TOP_ROW = re.compile(r"^\s*(\d+)\s{2}\S", re.M)
_APPEND = re.compile(r">>\s*([^\s;&|<>()]+)")


@cache
def summaries_at(commit: str, gw: int) -> dict[int, dict]:
    listing = _git_lines(commit, f"data/raw/gw{gw}/players/")
    paths = [p for p in listing if re.search(r"/summary-\d+\.json$", p)]
    blobs = read_blobs(REPO_ROOT, commit, paths)
    return {int(re.search(r"summary-(\d+)", p)[1]): json.loads(b) for p, b in blobs.items()}


@cache
def bootstrap_bytes(case_source) -> bytes:
    return read_source(REPO_ROOT, case_source)


def corrections_at(commit: str, gw: int) -> tuple[frozenset[int], frozenset[int]]:
    paths = [p for p in _git_lines(commit, "data/retro/") if re.fullmatch(r"data/retro/gw\d+\.md", p)]
    blobs = read_blobs(REPO_ROOT, commit, paths)
    with tempfile.TemporaryDirectory() as tmp:
        for path, data in blobs.items():
            (Path(tmp) / Path(path).name).write_bytes(data)
        view = agent_corrections(Path(tmp), gw=gw, agent="A3")
    return (frozenset(c.rule.number for c in view.active),
            frozenset(r.number for r in view.retired))


def reopen_delta(gw: int, pos: str, before: bytes, after: bytes) -> frozenset[int]:
    old = Bootstrap.model_validate(json.loads(before)).elements
    new = Bootstrap.model_validate(json.loads(after)).elements
    return frozenset(c.id for c in flag_delta(old, new) if c.position is Position[pos])


def replay_run(case: ReplayCase) -> PlayerRun:
    transcript = load_transcript(case.fixture)
    commit, gw, pos = case.commit, case.gw, case.pos
    analysis = f"data/analysis/gw{gw}"
    pre_inputs = json.loads((REOPEN_FIXTURES / f"inputs-{pos}.pre.json").read_text("utf-8")) \
        if case.pre_reopen_inputs or case.mode == REOPEN else None
    committed_inputs = json.loads(git_show(commit, f"{analysis}/inputs-{pos}.json") or b"null")
    inputs = pre_inputs if case.pre_reopen_inputs else committed_inputs
    players = json.loads(git_show(commit, f"{analysis}/players-{pos}.json") or b"null")
    md_path = f"{analysis}/players-{pos}.md"
    written = agent_written_files(transcript, FROZEN_ROOT).get(md_path)
    if _appended(transcript, md_path):
        written = None
    md = written if isinstance(written, str) else (
        git_show(commit, f"{analysis}/players-{pos}.md") or b"").decode("utf-8") or None
    if case.top15_call is not None:
        call = [c for c in transcript.calls if c.name != "SubagentHandback"][case.top15_call - 1]
        top15 = tuple(int(i) for i in _TOP_ROW.findall(call.result.text if call.result else ""))
    else:
        top15 = tuple(p["id"] for p in (players or [])[:15])
    boot = bootstrap_bytes(case.bootstrap)
    active, retired = corrections_at(commit, gw)
    changed = frozenset()
    if case.mode == REOPEN:
        changed = reopen_delta(gw, pos, bootstrap_bytes(ANALYSIS_BOOTSTRAPS[gw]), boot)
    summaries = summaries_at(commit, gw)
    return PlayerRun(
        transcript=transcript, instructions=transcript.prompt or "", root=FROZEN_ROOT,
        gw=gw, pos=pos, mode=case.mode, inputs=inputs, players=players, md=md,
        top15=top15[:15], bootstrap=json.loads(boot),
        fixtures=json.loads(git_show(commit, f"data/raw/gw{gw}/fixtures.json") or b"[]"),
        summary=summaries.get, active=active, retired=retired, changed_ids=changed,
        before_inputs=pre_inputs if case.mode == REOPEN else None,
        project_instructions=(git_show(commit, "CLAUDE.md") or b"").decode("utf-8"),
        before_md=(REOPEN_FIXTURES / f"players-{pos}.pre.md").read_text("utf-8")
        if case.mode == REOPEN else None,
    )


def _appended(transcript, path: str) -> bool:
    """Whether a shell append (`>>`) extends `path`: the transcript then holds
    only part of the file."""
    return any(normalise(target, FROZEN_ROOT) == path
               for call in transcript.calls if call.name == "Bash"
               for target in _APPEND.findall(command_lines(str(call.input.get("command", "")))))


def _git_lines(commit: str, path: str) -> list[str]:
    return subprocess.run(["git", "-C", str(REPO_ROOT), "ls-tree", "-r", "--name-only",
                           commit, path], capture_output=True, text=True,
                          check=True).stdout.splitlines()
