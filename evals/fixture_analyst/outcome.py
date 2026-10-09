"""Season-level outcome of the fixture forecasts — tracked, never graded.

For each committed data/analysis/gw{N}/fixtures.json, the GW N rows are joined
to the final scores in the latest raw fixture list. P(CS) is scored by Brier
against clean sheets, λ_att by Poisson log-likelihood against goals, each
beside a constant baseline from the rounds before N: the league clean-sheet
rate and the mean goals per side by venue.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

MIN_ROUNDS = 5
LAMBDA_FLOOR = 0.1


@dataclass(frozen=True)
class RoundOutcome:
    gw: int
    rows: int
    brier: float
    brier_base: float
    log_lik: float
    log_lik_base: float
    base_lambda: dict[str, float]


def _poisson_log(k: int, lam: float) -> float:
    lam = max(lam, LAMBDA_FLOOR)
    return k * math.log(lam) - lam - math.lgamma(k + 1)


def _latest_raw(root: Path) -> Path | None:
    gws = [int(m.group(1)) for p in (root / "data/raw").glob("gw*/fixtures.json")
           if (m := re.fullmatch(r"gw(\d+)", p.parent.name))]
    return root / "data/raw" / f"gw{max(gws)}" if gws else None


def score_rounds(root: Path) -> list[RoundOutcome]:
    raw = _latest_raw(root)
    if raw is None:
        return []
    names = {t["id"]: t["short_name"]
             for t in json.loads((raw / "bootstrap.json").read_text("utf-8"))["teams"]}
    results = {}
    sides = []
    for f in json.loads((raw / "fixtures.json").read_text("utf-8")):
        if not f.get("finished") or f.get("event") is None:
            continue
        home, away = names[f["team_h"]], names[f["team_a"]]
        hs, as_ = f["team_h_score"], f["team_a_score"]
        results[(f["event"], home, away, "H")] = (hs, as_)
        results[(f["event"], away, home, "A")] = (as_, hs)
        sides += [(f["event"], "H", hs, as_), (f["event"], "A", as_, hs)]
    outcomes = []
    for path in sorted((root / "data/analysis").glob("gw*/fixtures.json"),
                       key=lambda p: int(re.sub(r"\D", "", p.parent.name))):
        gw = int(re.sub(r"\D", "", path.parent.name))
        rows = [r for r in json.loads(path.read_text("utf-8"))["fixtures"] if r["gw"] == gw]
        scored = [(r, results[(gw, r["club"], r["opp"], r["venue"])]) for r in rows
                  if (gw, r["club"], r["opp"], r["venue"]) in results]
        if not scored:
            continue
        earlier = [s for s in sides if s[0] < gw]
        base_cs = (sum(1 for s in earlier if s[3] == 0) / len(earlier)) if earlier else \
            math.exp(-1.435)
        base_lambda = {v: (sum(s[2] for s in earlier if s[1] == v)
                           / max(1, sum(1 for s in earlier if s[1] == v)))
                       for v in ("H", "A")}
        n = len(scored)
        outcomes.append(RoundOutcome(
            gw=gw, rows=n,
            brier=sum((r["p_cs"] - (ga == 0)) ** 2 for r, (_, ga) in scored) / n,
            brier_base=sum((base_cs - (ga == 0)) ** 2 for _, (_, ga) in scored) / n,
            log_lik=sum(_poisson_log(gf, r["lambda_att"]) for r, (gf, _) in scored) / n,
            log_lik_base=sum(_poisson_log(gf, base_lambda[r["venue"]])
                             for r, (gf, _) in scored) / n,
            base_lambda=base_lambda,
        ))
    return outcomes


def print_outcome(root: Path) -> int:
    rounds = score_rounds(root)
    for r in rounds:
        print(f"gw{r.gw}: {r.rows} rows  Brier P(CS) {r.brier:.3f} (base {r.brier_base:.3f})  "
              f"log-lik λ_att {r.log_lik:.3f} (base {r.log_lik_base:.3f})")
    if len(rounds) < MIN_ROUNDS:
        print(f"{len(rounds)} scored round(s); the season comparison starts at {MIN_ROUNDS}")
        return 0
    total = sum(r.rows for r in rounds)

    def pooled(field: str) -> float:
        return sum(getattr(r, field) * r.rows for r in rounds) / total

    print(f"season ({len(rounds)} rounds, {total} rows): Brier {pooled('brier'):.3f} vs base "
          f"{pooled('brier_base'):.3f}; log-lik {pooled('log_lik'):.3f} vs base "
          f"{pooled('log_lik_base'):.3f}")
    return 0
