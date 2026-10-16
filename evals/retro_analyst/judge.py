"""Model judge for what code cannot decide. J-retro grades attribution (J1)
and arithmetic provenance (J3) in one call; J-premise asks, per CODE
(fpl/ep.py) correction the run issues or keeps active, whether the code really
has the defect the correction claims (J2)."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from evals.harness.live import JUDGE_TIMEOUT_S, JudgeVerdict, build_judge_argv
from evals.retro_analyst.cases import REPO_ROOT
from evals.retro_analyst.checks import (
    RetroRun,
    current_rows,
    misses_ids,
    outside_fences,
    section,
)
from fpl.corrections import Rule, corrections_section, is_closed, parse_rules

JUDGE_MODEL = "opus"
RETRO_RUBRIC = (
    "You grade a retro-analyst's write-up. Reply with exactly two lines. J1 attribution: "
    "PASS only if every Misses class and cause is consistent with the supplied rows "
    "(minutes, started, xG/xA, p_start), captain verdicts judge process not outcome, and no "
    "level correction rests on a single round. J3 arithmetic: PASS only if every number not "
    "printed in the outputs is a difference of two printed numbers; a counterfactual total, "
    "a re-derived statistic, or an invented sample size is FAIL. Format: `J1 PASS` or "
    "`J1 FAIL: <first offending claim>`; same for J3."
)
PREMISE_RUBRIC = (
    "Here is a claim about what this code does, and the code. Reply TRUE if the code has "
    "the defect the claim says it has, FALSE if the code contradicts it. One line: TRUE or "
    "FALSE: <reason>."
)
JUDGED_SECTIONS = ("Squad", "Misses", "Captain and bench", "Findings")
_LINE = re.compile(r"^\W*(J[13])\W*:?\s*(PASS|FAIL)\b:?\s*(.*)$", re.I)
_PREMISE = re.compile(r"^\W*(TRUE|FALSE)\b\W*(.*)$", re.I)
_NUMBER = re.compile(r"(?<![\w.])[−+-]?\d[\d,]*(?:\.\d+)?(?![\w])")
_WORD = re.compile(r"[a-z]{5,}")
_IDENT = re.compile(r"`([A-Za-z_]\w*)`")


@dataclass(frozen=True)
class JudgeLines:
    verdicts: dict[str, tuple[str, str]]
    cost_usd: float | None

    def status(self, key: str) -> str:
        return self.verdicts.get(key, ("MISSING", ""))[0]


@dataclass(frozen=True)
class PremiseClaim:
    number: int
    claim: str
    code: str


def parse_judge_lines(answer: str) -> dict[str, tuple[str, str]]:
    verdicts: dict[str, tuple[str, str]] = {}
    for line in answer.splitlines():
        match = _LINE.match(line.strip())
        if match and match.group(1).upper() not in verdicts:
            verdicts[match.group(1).upper()] = (match.group(2).upper(), match.group(3).strip())
    return verdicts


def parse_premise(answer: str) -> tuple[bool | None, str]:
    first = answer.strip().splitlines()[0] if answer.strip() else ""
    match = _PREMISE.match(first.strip())
    if not match:
        return None, f"unparseable: {first[:80]}"
    return match.group(1).upper() == "TRUE", match.group(2).strip()


def _normal(token: str) -> str:
    return token.replace(",", "").replace("−", "-").lstrip("+")


def untraceable_numbers(run: RetroRun) -> list[str]:
    """Numbers in the judged prose (fences excluded) that no tool output
    prints, after normalising thousands commas and the minus sign."""
    printed = {_normal(t).lstrip("-") for t in _NUMBER.findall(run.outputs)}
    prose = "\n".join(outside_fences("\n".join(section(run.retro or "", title)
                                                for title in JUDGED_SECTIONS)))
    found = []
    for token in _NUMBER.findall(prose):
        value = _normal(token).lstrip("-")
        if value not in printed and value not in found:
            found.append(value)
    return found


def _fpl_outputs(run: RetroRun, subcommand: str) -> str:
    texts = []
    for call in run.calls:
        command = str(call.input.get("command", ""))
        if call.name == "Bash" and re.search(rf"-m fpl {subcommand}\b", command) \
                and call.result is not None:
            texts.append(call.result.text)
    return "\n\n".join(texts)


_PICKS_HISTORY = re.compile(r"^(?:entry \d+ |pos |event |\s*\d)")


def _picks_and_history(run: RetroRun) -> str:
    """The `picks` and `entry-history` tables: the lines that follow
    calibrate's stdout in Call 1, up to the next command's output."""
    stdout = run.calibrate_stdout or ""
    for call in run.calls:
        text = call.result.text if call.result else ""
        if not re.search(r"-m fpl (?:picks|entry-history)\b", str(call.input.get("command", ""))):
            continue
        rest = text.split(stdout, 1)[1] if stdout and stdout in text else text
        kept = []
        for line in rest.splitlines():
            if kept and not _PICKS_HISTORY.match(line):
                break
            if _PICKS_HISTORY.match(line):
                kept.append(line)
        return "\n".join(kept)
    return ""


def _ledger_truth(run: RetroRun) -> str:
    """The squad rows, then every other Misses-table id, with `started`."""
    if run.ledger is None:
        return "(none)"
    joined = {line.id: line for line in run.ledger.players}
    squad = run.ledger.squad.players if run.ledger.squad is not None else ()
    rows = []

    def detail(player_id: int) -> str:
        player = joined.get(player_id)
        return ("no prediction" if player is None else
                f"pred {player.predicted:.3f} act {player.actual} err {player.error:+.3f} "
                f"started {player.started} minutes {player.minutes} "
                f"p_start {player.p_start:.2f}")

    for line in squad:
        rows.append(f"{line.slot} {line.role} {line.id} {line.name}: {detail(line.id)}")
    squad_ids = {line.id for line in squad}
    for player_id in misses_ids(run):
        if player_id not in squad_ids and player_id in joined:
            rows.append(f"pool {player_id} {joined[player_id].name}: {detail(player_id)}")
    return "\n".join(rows)


def build_retro_judge_prompt(run: RetroRun) -> str:
    retro = run.retro or ""
    parts = [f"## {title}\n{section(retro, title)}" for title in JUDGED_SECTIONS]
    fresh = [rule.text for rule in parse_rules(corrections_section(retro))
             if rule.number not in {row.number for row in current_rows(run)}]
    numbers = untraceable_numbers(run)
    return (f"{RETRO_RUBRIC}\n\nRETRO SECTIONS:\n" + "\n\n".join(parts)
            + "\n\nNEW RULES:\n" + ("\n\n".join(fresh) or "(none)")
            + f"\n\nCALIBRATE STDOUT:\n{run.calibrate_stdout or '(none)'}"
            + f"\n\nACTUALS OUTPUT:\n{_fpl_outputs(run, 'actuals') or '(none)'}"
            + "\n\nLEDGER ROWS (truth, with started; the squad, then pool Misses rows):\n"
            + _ledger_truth(run)
            + "\n\nOTHER OUTPUTS (picks, entry-history, as the run printed them):\n"
            + (_picks_and_history(run) or "(none)")
            + "\n\nUNTRACEABLE NUMBERS (in the prose, printed by no output; every other number "
              "is printed by some output, including ones not reproduced here such as "
              "final.md): " + (", ".join(numbers) or "none") + "\n")


def top_level_spans(source: str) -> dict[str, tuple[int, int]]:
    spans: dict[str, tuple[int, int]] = {}
    for node in ast.parse(source).body:
        names: list[str] = []
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            names = [node.name]
        elif isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
        start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
        for name in names:
            spans[name] = (start, node.end_lineno or node.lineno)
    return spans


def excerpt(source: str, names: tuple[str, ...]) -> str:
    lines = source.splitlines()
    spans = top_level_spans(source)
    return "\n\n".join("\n".join(lines[spans[n][0] - 1:spans[n][1]])
                       for n in names if n in spans)


def _claim_names(rule: Rule, spans: dict[str, tuple[int, int]]) -> tuple[str, ...]:
    named = [n for n in _IDENT.findall(rule.text) if n in spans]
    if named:
        return tuple(dict.fromkeys(named))
    head = rule.text.split("**", 2)[1].lower() if rule.text.count("**") >= 2 else rule.text
    words = set(_WORD.findall(head))
    return tuple(n for n in spans if any(w in n.lower() for w in words))


def premise_claims(run: RetroRun, *, ep_source: str) -> list[PremiseClaim]:
    """Every CODE (fpl/ep.py) correction the retro issues or leaves open,
    with the fpl/ep.py code its claim is about."""
    texts: dict[int, Rule] = {}
    for _, text in sorted(run.prior_retros.items(), key=lambda kv: int(re.sub(r"\D", "", kv[0]))):
        for rule in parse_rules(corrections_section(text)):
            texts[rule.number] = rule
    for rule in parse_rules(corrections_section(run.retro or "")):
        texts[rule.number] = rule
    closed = {row.number for row in current_rows(run) if is_closed(row.status)}
    spans = top_level_spans(ep_source)
    claims = []
    for number, rule in sorted(texts.items()):
        if number in closed or not re.match(r"^\*\*C\d+ — CODE \(fpl/ep\.py", rule.text):
            continue
        claims.append(PremiseClaim(number, rule.text,
                                   excerpt(ep_source, _claim_names(rule, spans))))
    return claims


def _run_claude(prompt: str, cwd: Path, model: str) -> tuple[str, float | None]:
    completed = subprocess.run(
        build_judge_argv(model, budget_usd=1.00), input=prompt, cwd=cwd, capture_output=True,
        text=True, timeout=JUDGE_TIMEOUT_S, check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return "", None
    return str(payload.get("result", "")), payload.get("total_cost_usd")


def run_retro_judge(prompt: str, *, cwd: Path, model: str = JUDGE_MODEL) -> JudgeLines:
    answer, cost = _run_claude(prompt, cwd, model)
    return JudgeLines(parse_judge_lines(answer), cost)


def run_premise_judge(claim: str, code: str, *, cwd: Path,
                      model: str = JUDGE_MODEL) -> tuple[bool | None, str, float | None]:
    answer, cost = _run_claude(f"{PREMISE_RUBRIC}\n\nCLAIM:\n{claim}\n\nCODE:\n{code}\n",
                               cwd, model)
    verdict, reason = parse_premise(answer)
    return verdict, reason, cost


def judge_run(run: RetroRun, *, cwd: Path) -> JudgeVerdict:
    lines = run_retro_judge(build_retro_judge_prompt(run), cwd=cwd)
    reasons = [f"{key} {lines.status(key)}: {lines.verdicts.get(key, ('', ''))[1]}".rstrip(": ")
               for key in ("J1", "J3") if lines.status(key) != "PASS"]
    cost = lines.cost_usd or 0.0
    ep_source = (Path(run.root) / "fpl" / "ep.py").read_text("utf-8")
    for claim in premise_claims(run, ep_source=ep_source):
        verdict, reason, spent = run_premise_judge(claim.claim, claim.code, cwd=cwd)
        cost += spent or 0.0
        if verdict is not True:
            reasons.append(f"J2 C{claim.number} {verdict}: {reason}")
    return JudgeVerdict(not reasons, "; ".join(reasons), cost)


# --- J-premise gold set -----------------------------------------------------------


@dataclass(frozen=True)
class Gold:
    label: str
    claim: str
    commit: str
    path: str
    names: tuple[str, ...] = ()
    lines: tuple[tuple[int, int], ...] = ()
    expected: bool = True


def git_text(commit: str, path: str) -> str | None:
    blob = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{commit}:{path}"],
                          capture_output=True, check=False)
    return blob.stdout.decode("utf-8") if blob.returncode == 0 else None


def _c9_text() -> str:
    text = git_text("0b36b83", "data/retro/gw2.md") or ""
    return next(r.text for r in parse_rules(corrections_section(text)) if r.number == 9)


GOLD: tuple[Gold, ...] = (
    Gold("C9", _c9_text(), "0b36b83", "fpl/ep.py",
         names=("DEFCON_HIT_ANCHORS", "defcon_hit_probability"), expected=False),
    Gold("flat-0.80", "The squad optimizer applies a flat 0.80 HIGH discount across all six "
         "gameweeks of a player's EP.", "571f5b0", "agents/squad-optimizer.md",
         lines=((55, 65),), expected=False),
    Gold("pre-2024/25-defcon", "history_past records defensive_contribution as 0 for every "
         "season before 2024/25 because the stat did not exist, and the prior reads it as a "
         "genuine zero, so a player whose prior pool predates 2024/25 gets a near-zero dc90 "
         "prior.", "8307b53", "fpl/ep.py", names=("_Totals", "_prior_seasons")),
    Gold("my-team-value", "my-team prints the team value total without saying whether it is "
         "the selling-price sum or the purchase-price (now_cost) sum.", "88882a2",
         "fpl/__main__.py", lines=((1255, 1265), (1445, 1455))),
    Gold("ep-coverage", "`fpl ep` refuses to write players-{pos}.json when an available or "
         "doubtful player priced above £4.5m has no inputs row.", "571f5b0", "fpl/ep.py",
         names=("_check_coverage",)),
    Gold("shortlist-minutes", "is_shortlisted's 900-minute test reads this season's minutes, "
         "not last season's.", "ae4b9e4", "fpl/models.py", names=("is_shortlisted",)),
)


def gold_code(gold: Gold) -> str:
    source = git_text(gold.commit, gold.path) or ""
    if gold.names:
        return excerpt(source, gold.names)
    lines = source.splitlines()
    return "\n\n".join("\n".join(lines[a - 1:b]) for a, b in gold.lines)
