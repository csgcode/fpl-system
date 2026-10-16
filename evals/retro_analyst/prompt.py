"""The production brief for a live retro run: run facts only, never
conclusions. The agent reads its spec from the workspace itself."""

from __future__ import annotations

from pathlib import Path

from evals.retro_analyst.cases import NULL_TEAM, TEAM_ID, LiveCase

TEMPLATE = """You are agent A6 — Retro Analyst for the FPL agent system.
Run facts:
- Repo root: {root} — run every command from there.
- Completed gameweek M = {m}; current cycle N = {n}. Output: data/retro/gw{m}.md.
- team_id: {team_id}. Today's date for backlog rows: {date}.
- The data is a recorded replay: event deadlines inside it are historical; ignore them.
- Read agents/retro-analyst.md in full first and follow it.
- Never run `git commit` — the orchestrator owns the cycle commit."""


def build_prompt(root: Path, case: LiveCase) -> str:
    team_id = "null" if case.perturbation == NULL_TEAM else str(TEAM_ID)
    return TEMPLATE.format(root=root, m=case.round, n=case.gw, team_id=team_id,
                           date=case.date)
