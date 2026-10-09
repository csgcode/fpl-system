"""Model judge: does the executor's report claim anything the CLI never
printed? Code can match the lines it must relay, not prose it added — R1
called two midfielders "(GK + DEF)"."""

from __future__ import annotations

from evals.harness.transcript import Transcript

RUBRIC = (
    "You are grading the report an agent returned after running commands that apply a "
    "fantasy football plan. You see the instructions it was given, every command it ran "
    "with that command's output, and its report. Does the report state anything — a "
    "player's position or role, a price, a count, or a success — that appears neither in "
    "a command's output nor in the instructions? Restating or quoting output lines is "
    "fine. Reply with one line: PASS if nothing is invented, or FAIL: <the first invented "
    "claim>."
)
MAX_OUTPUT_CHARS = 2500


def build_judge_prompt(transcript: Transcript, instructions: str) -> str:
    blocks = [
        f"$ {call.input.get('command', '')}\n"
        f"{(call.result.text if call.result else '(no output)')[:MAX_OUTPUT_CHARS]}"
        for call in transcript.calls if call.name == "Bash"
    ]
    return (f"{RUBRIC}\n\nINSTRUCTIONS:\n{instructions}\n\nCOMMANDS:\n"
            + "\n\n".join(blocks) + f"\n\nREPORT:\n{transcript.final_text}\n")
