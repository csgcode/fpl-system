"""The shared readers every grader uses on a CLI call and on a report."""

from __future__ import annotations

from evals.harness.report import cli_exit, normalise_text
from evals.harness.transcript import ToolCall, ToolResult

CMD = "uv run python -m fpl plan --gw 2"


def bash(output: str | None, *, error: bool = False) -> ToolCall:
    result = None if output is None else ToolResult(output, error, False)
    return ToolCall("c1", "Bash", {"command": CMD}, result)


def test_cli_exit_reads_every_spelling():
    assert cli_exit(bash("Exit code 2\nerror: x", error=True)) == 2
    assert cli_exit(bash("error: x", error=True)) == 1
    assert cli_exit(bash("error: x\nEXIT=1")) == 1
    assert cli_exit(bash("wrote x\nEXIT=0")) == 0
    assert cli_exit(bash("wrote x")) == 0


def test_cli_exit_is_unknown_without_a_result():
    assert cli_exit(bash(None)) is None


def test_normalise_text_ignores_markdown_case_and_spacing():
    assert normalise_text("**Wrote**  `data/x.json`\n_OK_") == "wrote data/x.json ok"
