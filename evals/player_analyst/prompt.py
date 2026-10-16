"""The live prompt: the run facts the orchestrator would give, then the spec
body. No conclusions are injected."""

from __future__ import annotations

from evals.player_analyst.cases import REOPEN, LiveCase

TEMPLATE = """You are agent A3 — Player Analyst for the FPL agent system.
Run facts:
- Repo root: {ws} — run every command from here.
- POS = {pos}. N = {gw}; N-1 = {previous}. Today's date: {today}.
- Mode: {mode}
- Never run `git commit` — the orchestrator owns the cycle commit.

{spec}"""


def delta_path(gw: int, stamp: str) -> str:
    return f"data/raw/gw{gw}/flags-delta-{stamp}.json"


def build_prompt(case: LiveCase, *, ws: str, spec: str, delta: str | None = None) -> str:
    mode = (f"REOPEN — delta file {delta}" if case.mode == REOPEN else "normal")
    return TEMPLATE.format(ws=ws, pos=case.pos, gw=case.gw, previous=case.gw - 1,
                           today=case.today, mode=mode, spec=spec)
