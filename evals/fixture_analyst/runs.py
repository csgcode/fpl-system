"""Builds a FixtureAnalystRun from a recorded transcript (replay): the
outputs and inputs come from the cycle commit, the promoted set from the
committed club priors."""

from __future__ import annotations

import json
import re
from pathlib import Path

from evals.fixture_analyst.cases import PRIORS_PATH, REPO_ROOT, ReplayCase, git_show, read_blobs
from evals.fixture_analyst.checks import Evidence, FixtureAnalystRun
from evals.harness.freeze import FROZEN_ROOT
from evals.harness.transcript import load_transcript


def promoted_clubs(priors: bytes) -> frozenset[str]:
    clubs = json.loads(priors)["clubs"]
    return frozenset(c for c, prior in clubs.items() if prior["promoted"])


def team_names(bootstrap: bytes) -> dict[int, str]:
    return {t["id"]: t["short_name"] for t in json.loads(bootstrap)["teams"]}


def retro_paths(repo: Path, commit: str, gw: int) -> list[str]:
    from evals.fixture_analyst.cases import _git

    listed = _git(repo, "ls-tree", "--name-only", commit, "data/retro/").splitlines()
    return [p for p in listed
            if (m := re.fullmatch(r"data/retro/gw(\d+)\.md", p)) and int(m.group(1)) < gw]


def replay_evidence(case: ReplayCase, repo: Path = REPO_ROOT) -> Evidence:
    analysis, raw = f"data/analysis/gw{case.gw}", f"data/raw/gw{case.gw}"
    retros = read_blobs(repo, case.commit, retro_paths(repo, case.commit, case.gw))
    md = git_show(repo, case.commit, f"{analysis}/fixtures.md")
    return Evidence(
        fixtures_json=git_show(repo, case.commit, f"{analysis}/fixtures.json"),
        fixtures_md=md.decode("utf-8") if md is not None else None,
        raw_fixtures=json.loads(git_show(repo, case.commit, f"{raw}/fixtures.json") or b"[]"),
        team_names=team_names(git_show(repo, case.commit, f"{raw}/bootstrap.json") or b"{}"),
        promoted=promoted_clubs((repo / PRIORS_PATH).read_bytes()),
        retros={path: text.decode("utf-8") for path, text in retros.items()},
    )


def replay_run(case: ReplayCase) -> FixtureAnalystRun:
    transcript = load_transcript(case.fixture)
    return FixtureAnalystRun(transcript=transcript, instructions=transcript.prompt or "",
                             root=FROZEN_ROOT, gw=case.gw, evidence=replay_evidence(case))
