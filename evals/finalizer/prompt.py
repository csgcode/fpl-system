"""The production brief for a live finalizer run: run facts only, never
conclusions. The agent reads its spec from the workspace itself."""

from __future__ import annotations

from pathlib import Path

from evals.finalizer.cases import LiveCase

TEMPLATE = """You are agent A7 — Finalizer for the FPL agent system.
Run facts:
- Repo root: {root} — run every command from there.
- Gameweek N = {gw}.
- Read agents/finalizer.md in full first and follow it.
- The data is a recorded replay: event deadlines inside it are historical; ignore them.
{case_lines}- Never run `git commit` — the orchestrator owns the cycle commit."""


def build_prompt(root: Path, case: LiveCase) -> str:
    lines = "".join(f"- {line}\n" for line in case.case_lines)
    return TEMPLATE.format(root=root, gw=case.gw, case_lines=lines)
