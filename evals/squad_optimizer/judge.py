"""Model judge for what code cannot decide: whether the proposal's claims
about players and numbers hold (J1), and whether every choice rests on the
spec objective and rules rather than another metric (J2)."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from evals.harness.live import JUDGE_TIMEOUT_S, build_judge_argv
from evals.squad_optimizer.checks import OptimizerRun, decision, fold, reference

RUBRIC = (
    "You grade a squad-optimizer proposal. You get the proposal, the objective summary "
    "(baseline, plan gains, best rejected move), and for every player named in its prose: "
    "bootstrap status, chance and news, and the analyst's p_start_gw and notes. Reply with "
    "exactly two lines.\n"
    "J1 claims: PASS only if every factual claim about a player (injury, suspension, minutes, "
    "role, fixtures) agrees with that evidence, and no number in the prose contradicts the "
    "objective summary.\n"
    "J2 basis: PASS only if every transfer, XI, captain and chip choice rests on the spec "
    "objective, the transfer rule, an active retro correction or a suggestion disposition, "
    "and no other metric (simulation, auto-sub model, invented tie-break) decides any "
    "choice. Each of these is spec basis: the transfer rule (a free move needs blend gain "
    "≥ 2.0 and prior-only gain ≥ 0; a hit needs blend ≥ 6.0 and prior-only > 0); the chip "
    "gate (a wildcard or free hit needs ≥ 6.0 blend and ≥ 0 prior-only over the best plan "
    "without it); and active retro corrections, for example C14 (score every move on "
    "prior-only rates as well as blend and refuse one whose sign flips). Reasoning that "
    "applies them, including comparing options on prior-only figures, is spec basis.\n"
    "Format: `J<n>: PASS` or `J<n>: FAIL: <first offending sentence>`."
)
JUDGE_MODEL = "opus"
JUDGE_BUDGET_USD = 1.00
KEYS = ("J1", "J2")
_LINE = re.compile(r"^\W*(J[12])\W*:?\s*(PASS|FAIL)\b:?\s*(.*)$", re.I)


@dataclass(frozen=True)
class Analyst:
    p_start_gw: tuple[float, ...]
    notes: str


@dataclass(frozen=True)
class JudgeLines:
    verdicts: dict[str, tuple[str, str]]
    cost_usd: float | None

    def status(self, key: str) -> str:
        return self.verdicts.get(key, ("MISSING", ""))[0]


def parse_lines(answer: str) -> dict[str, tuple[str, str]]:
    verdicts: dict[str, tuple[str, str]] = {}
    for line in answer.splitlines():
        match = _LINE.match(line.strip())
        if match and match.group(1).upper() not in verdicts:
            verdicts[match.group(1).upper()] = (match.group(2).upper(), match.group(3).strip())
    return verdicts


def analyst_rows(documents: list[dict]) -> dict[int, Analyst]:
    return {int(row["id"]): Analyst(tuple(row.get("p_start_gw") or [row.get("p_start", 0)]),
                                    str(row.get("notes", "")))
            for row in documents}


def named_players(text: str, run: OptimizerRun) -> list[int]:
    folded = fold(text)
    return sorted(pid for pid, row in run.blend.items()
                  if re.search(rf"(?<![\w.]){re.escape(fold(row.name))}(?![\w])", folded))


def objective_summary(run: OptimizerRun) -> str:
    made = decision(run)
    if isinstance(made, str):
        return f"(objective unavailable: {made})"
    report = reference(run, made)
    moves = "; ".join(f"{run.blend[s.move.out].name} → {run.blend[s.move.into].name} "
                      f"{s.blend:+.3f} / {s.prior:+.3f}" for s in report.marginals) or "none"
    best = report.next_best
    rejected = (f"{run.blend[best.move.out].name} → {run.blend[best.move.into].name} "
                f"{best.blend:+.3f} / {best.prior:+.3f}" if best else "none")
    return (f"baseline: blend {report.baseline[0]:.3f} prior {report.baseline[1]:.3f}\n"
            f"plan: blend {report.gain[0]:+.3f} prior {report.gain[1]:+.3f}; moves {moves}\n"
            f"best rejected single after the plan: {rejected}")


def build_judge_prompt(run: OptimizerRun, analysts: Mapping[int, Analyst], *,
                       proposal: str | None = None) -> str:
    text = proposal if proposal is not None else (run.proposal or "")
    players = run.bootstrap.player_by_id()
    evidence = []
    for pid in named_players(text, run):
        player = players.get(pid)
        analyst = analysts.get(pid)
        evidence.append(
            f"- {run.blend[pid].name} (id {pid}): status {player.status.value if player else '?'}, "
            f"chance {player.chance_of_playing_next_round if player else '?'}, "
            f"news {player.news if player else ''!r}; p_start_gw "
            f"{list(analyst.p_start_gw) if analyst else '?'}; notes: "
            f"{analyst.notes if analyst else '(none)'}")
    return (f"{RUBRIC}\n\nPROPOSAL:\n{text}\n\nOBJECTIVE SUMMARY:\n{objective_summary(run)}\n\n"
            "PLAYER EVIDENCE:\n" + ("\n".join(evidence) or "(none)") + "\n")


def run_judge_lines(prompt: str, *, cwd: Path, model: str = JUDGE_MODEL) -> JudgeLines:
    completed = subprocess.run(
        build_judge_argv(model, budget_usd=JUDGE_BUDGET_USD), input=prompt, cwd=cwd,
        capture_output=True, text=True, timeout=JUDGE_TIMEOUT_S, check=False)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return JudgeLines({}, None)
    return JudgeLines(parse_lines(str(payload.get("result", ""))), payload.get("total_cost_usd"))


# --- calibration --------------------------------------------------------------

S5_FACT = "Scott is fit and starts GW6"
SIM_SENTENCE = "This was decided on the auto-sub simulation (+3.1)."


def with_s5_reason(proposal: str) -> str:
    """GW6 with S5's reason replaced by a claim the evidence contradicts."""
    rows = [line for line in proposal.splitlines() if line.startswith("| S5 |")]
    if len(rows) != 1:
        raise ValueError(f"{len(rows)} '| S5 |' rows")
    cells = rows[0].split("|")
    cells[4] = f" {S5_FACT} "
    return proposal.replace(rows[0], "|".join(cells))


def with_sim_basis(proposal: str) -> str:
    """GW6 with a simulation named as the decider in its transfers section."""
    match = re.search(r"(?m)^#+ .*Transfers.*$", proposal)
    if match is None:
        raise ValueError("no Transfers heading")
    return proposal[:match.end()] + f"\n\n{SIM_SENTENCE}\n" + proposal[match.end():]


@dataclass(frozen=True)
class Gold:
    label: str
    case: str
    expected: Mapping[str, str]
    """J<n> → PASS | FAIL; a key left out is reported, not compared."""
    mutate: str | None = None


GOLDS = (
    Gold("gw5-orig", "gw5-orig", {"J1": "FAIL", "J2": "FAIL"}),
    Gold("gw5-rev", "gw5-rev", {"J2": "PASS"}),
    Gold("gw6", "gw6", {"J2": "PASS"}),
    Gold("gw4", "gw4", {"J2": "PASS"}),
    Gold("gw6-false-fact", "gw6", {"J1": "FAIL"}, mutate="s5"),
    Gold("gw6-sim-basis", "gw6", {"J2": "FAIL"}, mutate="sim"),
)
MUTATIONS = {"s5": with_s5_reason, "sim": with_sim_basis}
