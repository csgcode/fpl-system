"""Season-level outcome of the squad optimizer — tracked, never graded.

Ex-ante regret: the greedy reference plan's blend gain minus the final
plan's, on the frozen view of the gameweek (≤ 0: the agent matched or beat
the reference). Realised: the calibration ledgers' squad section — predicted
v actual XI points, captain points forgone, bench points stranded.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from evals.harness.workspace import SourceError
from evals.squad_optimizer.cases import REPO_ROOT, replay_case

FINAL_PLANS = ("gw4", "gw5-rescore", "gw6")


@dataclass(frozen=True)
class Regret:
    gw: int
    plan_gain: float
    reference_gain: float

    @property
    def regret(self) -> float:
        return self.reference_gain - self.plan_gain


@dataclass(frozen=True)
class RoundSquad:
    round: int
    predicted: float
    actual: float
    forgone: int
    stranded: int


def ex_ante_regret() -> list[Regret]:
    """Empty when a frozen view is missing."""
    from evals.squad_optimizer.checks import decision, reference
    from evals.squad_optimizer.runs import replay_run

    regrets = []
    for name in FINAL_PLANS:
        try:
            run = replay_run(replay_case(name))
        except SourceError:
            return []
        made = decision(run)
        if isinstance(made, str):
            continue
        report = reference(run, made)
        regrets.append(Regret(run.gw, report.gain[0], report.reference_gain[0]))
    return regrets


def squad_rounds(root: Path = REPO_ROOT) -> list[RoundSquad]:
    rounds = []
    for path in (root / "data" / "retro").glob("gw*-calibration.json"):
        match = re.fullmatch(r"gw(\d+)-calibration\.json", path.name)
        squad = json.loads(path.read_text(encoding="utf-8")).get("squad") if match else None
        if not squad:
            continue
        rounds.append(RoundSquad(int(match.group(1)), squad["predicted_xi_total"],
                                 squad["actual_xi_total"], squad["captain"]["forgone"],
                                 squad["bench_points_stranded"]))
    return sorted(rounds, key=lambda r: r.round)


def print_outcome() -> int:
    regrets = ex_ante_regret()
    print("ex-ante regret (greedy reference gain − plan gain, blend EP6):")
    for r in regrets:
        print(f"  GW{r.gw}: plan {r.plan_gain:+.3f}  reference {r.reference_gain:+.3f}  "
              f"regret {r.regret:+.3f}")
    rounds = squad_rounds()
    print("realised squad (calibration ledgers):")
    print("  round  predicted XI  actual XI  captain forgone  bench stranded")
    for r in rounds:
        print(f"  {r.round:>5}  {r.predicted:>12.2f}  {r.actual:>9}  {r.forgone:>15}  "
              f"{r.stranded:>14}")
    print(f"season: regret {sum(r.regret for r in regrets):+.3f}; XI predicted "
          f"{sum(r.predicted for r in rounds):.2f} v actual {sum(r.actual for r in rounds)}; "
          f"captain forgone {sum(r.forgone for r in rounds)}; "
          f"bench stranded {sum(r.stranded for r in rounds)}")
    return 0
