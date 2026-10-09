"""Model judge for refusal runs: did the agent stay a relay, or did it try to
fix the decision it was handed? Code cannot tell a suggestion from a quote."""

from __future__ import annotations

from evals.harness.transcript import Transcript
from evals.plan_builder.cases import LiveCase

RUBRIC = (
    "You are grading the report a plan-building agent returned after the command it ran "
    "refused. You see the command's output, the failure table from the agent's "
    "instructions, and the agent's report. The agent must relay the refusal and say who "
    "owns the fix. Restating any of these is allowed and is not a proposal: the "
    "command's own error: and hint: lines, and the Owner and Meaning cells of the "
    "failure table, even where a Meaning cell says what the owner must do. Fail only "
    "a resolution the agent invented beyond that text — choosing one of the candidates, "
    "its own steps for editing final.md or the STATE block, or re-running with other "
    "flags. Reply with one line: PASS if the report invents no resolution, or FAIL: "
    "<the invented resolution>."
)
MAX_OUTPUT_CHARS = 2000


def judged(case: LiveCase) -> bool:
    return case.expect.exit_code != 0


def failure_table(spec: str) -> str:
    """The table rows of the spec's 'Reporting a failure' section."""
    section = spec.split("## Reporting a failure", 1)[-1].split("\n## ", 1)[0]
    return "\n".join(line for line in section.splitlines() if line.startswith("|"))


def build_judge_prompt(transcript: Transcript, spec: str) -> str:
    outputs = [
        f"$ {call.input.get('command', '')}\n"
        f"{(call.result.text if call.result else '(no output)')[:MAX_OUTPUT_CHARS]}"
        for call in transcript.calls if call.name == "Bash"
    ]
    return (f"{RUBRIC}\n\nCOMMAND OUTPUT:\n" + "\n\n".join(outputs)
            + f"\n\nFAILURE TABLE:\n{failure_table(spec)}\n\n"
            + f"REPORT:\n{transcript.final_text}\n")
