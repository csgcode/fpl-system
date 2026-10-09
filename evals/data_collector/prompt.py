"""The live-run prompt: run facts plus the spec body, nothing the run is
meant to measure (no deadline, no auth.json presence, no fetch state)."""

from __future__ import annotations

from pathlib import Path

from evals.data_collector.cases import LiveCase

TEMPLATE = """You are agent A1 — Data Collector for the FPL agent system.
Run facts:
- Repo root: {ws} — run every command from here.
- N = {gw} (the gameweek being prepared); M = {previous} (the last completed gameweek).
- data/entry.json team_id: {team_id}.
- Never run `git commit` — the orchestrator owns the cycle commit.

{spec}"""


def spec_body(spec_text: str) -> str:
    if not spec_text.startswith("---\n"):
        return spec_text
    _, _, rest = spec_text[4:].partition("\n---\n")
    return rest.lstrip("\n")


def build_prompt(ws: Path, case: LiveCase, body: str) -> str:
    return TEMPLATE.format(
        ws=ws, gw=case.gw, previous=case.previous_gw,
        team_id=case.team_id if case.team_id is not None else "null", spec=body,
    )
