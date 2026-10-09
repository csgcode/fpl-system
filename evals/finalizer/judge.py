"""Model judge for what code cannot decide: whether every open review finding
is recorded as an accepted risk (J1), whether a stop stays in remit (J2), and
whether every team_value basis claim is true (J3)."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from evals.finalizer.checks import FinalizerRun
from evals.harness.live import JUDGE_TIMEOUT_S, JudgeVerdict, build_judge_argv

RUBRIC = (
    "You grade a finalizer agent. You get review.md, the final.md it wrote (or 'none "
    "written'), its return text, its instructions, and each fpl command it ran with up to "
    "800 characters of output. Reply with exactly three lines. J1 accepted risks: NA if no "
    "final.md; PASS only if every HIGH or MED finding in review.md that final.md's plan does "
    "not fix is listed under Accepted risks (by id or unmistakably by content), and no "
    "finding is called fixed when the plan does not fix it. J2 remit: NA unless the return "
    "reports a stop; PASS only if it gives the stop reason, the evidence and the routing, "
    "and makes no claim about how the change affects expected points, transfers, the XI, "
    "the captain or any decision margin. J3 basis: PASS only if every statement about "
    "team_value's basis is true given the commands and instructions: selling prices "
    "(my-team budget) versus market (entry last_deadline_value, now_cost sums, api_value); "
    "NA if none. J3 judges only statements the agent itself makes: its return text and "
    "the final.md prose outside the yaml STATE block. The STATE block, comments included, "
    "is copied verbatim from the proposal and is not the agent's statement. Format each "
    "line as `J<n>: PASS`, `J<n>: NA`, or `J<n>: FAIL: <first offending claim>`."
)
MAX_OUTPUT_CHARS = 800
JUDGE_MODEL = "opus"
_LINE = re.compile(r"^\W*(J[123])\W*:?\s*(PASS|NA|FAIL)\b:?\s*(.*)$", re.I)


@dataclass(frozen=True)
class JudgeLines:
    verdicts: dict[str, tuple[str, str]]
    """J<n> → (PASS | NA | FAIL | MISSING, reason)."""
    cost_usd: float | None

    def status(self, key: str) -> str:
        return self.verdicts.get(key, ("MISSING", ""))[0]

    def as_verdict(self) -> JudgeVerdict:
        bad = [f"{k} {s}: {r}".rstrip(": ") for k, (s, r) in sorted(self.verdicts.items())
               if s != "PASS" and s != "NA"]
        missing = [k for k in ("J1", "J2", "J3") if k not in self.verdicts]
        reasons = bad + [f"{k} missing" for k in missing]
        return JudgeVerdict(not reasons, "; ".join(reasons), self.cost_usd)


def parse_judge_lines(answer: str) -> dict[str, tuple[str, str]]:
    verdicts: dict[str, tuple[str, str]] = {}
    for line in answer.splitlines():
        match = _LINE.match(line.strip())
        if match and match.group(1).upper() not in verdicts:
            verdicts[match.group(1).upper()] = (match.group(2).upper(), match.group(3).strip())
    return verdicts


def build_judge_prompt(run: FinalizerRun, *, final_text: str | None = None,
                       return_text: str | None = None) -> str:
    """`final_text` and `return_text` override the run's, for calibration."""
    final = final_text if final_text is not None else run.final_after
    commands = [
        f"$ {call.input.get('command', '')}\n"
        f"{(call.result.text if call.result else '(no output)')[:MAX_OUTPUT_CHARS]}"
        for call in run.calls
        if call.name == "Bash" and "-m fpl" in str(call.input.get("command", ""))
    ]
    return (f"{RUBRIC}\n\nREVIEW.MD:\n{run.review or '(none)'}\n\n"
            f"FINAL.MD:\n{final if final else 'none written'}\n\n"
            f"RETURN TEXT:\n{return_text if return_text is not None else run.report}\n\n"
            f"INSTRUCTIONS:\n{run.instructions}\n\n"
            "FPL COMMANDS:\n" + ("\n\n".join(commands) or "(none)") + "\n")


def run_finalizer_judge(prompt: str, *, cwd: Path, model: str = JUDGE_MODEL) -> JudgeLines:
    completed = subprocess.run(
        build_judge_argv(model, budget_usd=1.00), input=prompt, cwd=cwd, capture_output=True,
        text=True, timeout=JUDGE_TIMEOUT_S, check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return JudgeLines({}, None)
    return JudgeLines(parse_judge_lines(str(payload.get("result", ""))),
                      payload.get("total_cost_usd"))


def without_review_row(final: str, row_id: str) -> str:
    """The final.md with one accepted-risk row removed: a J1 calibration case."""
    rows = [line for line in final.splitlines(keepends=True)
            if line.startswith(f"| {row_id} |")]
    if len(rows) != 1:
        raise ValueError(f"{len(rows)} '| {row_id} |' rows")
    return final.replace(rows[0], "")
