"""The production brief for a live squad-optimizer run: run facts only,
never conclusions. The agent reads its spec from the workspace itself."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from evals.squad_optimizer.cases import RESCORE, REVISION, LiveCase

TEMPLATE = """You are agent A4 — Squad Optimizer for the FPL agent system.
Run facts:
- Repo root: {root} — run every command from there.
- Gameweek N = {gw}; weekly branch; {branch}.
- Read agents/squad-optimizer.md in full first and follow it.
- From my-team: selling prices {sells}; {total_line}; bank {bank:.1f}; free transfers {free}.
- The data is a recorded replay: event deadlines inside it are historical; ignore them.
{case_lines}- Never run `git commit` — the orchestrator owns the cycle commit."""

FIRST_RUN = "first run of the cycle"


def build_prompt(root: Path, case: LiveCase, names: Mapping[int, str]) -> str:
    market = case.market
    sells = ", ".join(f"{pid} {names.get(pid, pid)} {price / 10:.1f}"
                      for pid, price in market.sell.items())
    total = sum(market.sell.values()) / 10
    branch = {REVISION: f"revision run after a REVISE: data/decisions/gw{case.gw}/review.md",
              RESCORE: "REOPEN re-run: the freshness gate changed ids "
                       + ", ".join(map(str, case.reopen_ids))
                       + "; the affected analysis was re-run"}.get(case.kind, FIRST_RUN)
    total_line = case.total_line or (
        f"Σ selling prices {total:.1f} + bank {market.bank / 10:.1f} = "
        f"{total + market.bank / 10:.1f}")
    return TEMPLATE.format(
        root=root, gw=case.gw, branch=branch, sells=sells, total_line=total_line,
        bank=market.bank / 10, free=market.free_transfers,
        case_lines="".join(f"- {line}\n" for line in case.case_lines))
