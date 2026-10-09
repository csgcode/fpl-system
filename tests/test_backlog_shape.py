"""docs/backlog.md conventions that live as prose in other files: the agent
legend mirrored in the retro spec, and the orchestrator's shape check in
CLAUDE.md, run here against good and malformed ledgers."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HEADER = "# Improvement backlog\n\n## Rows\n\n| GW | Date | Agent | Kind | Finding | Evidence | Status |\n|---|---|---|---|---|---|---|\n"
ROW = "| GW7 | 2026-10-16 | A10 | TOOL | finding | fpl/usage.py | open |\n"


def shape_check_awk() -> str:
    match = re.search(r"^\s*(awk '/\^## Rows/.*?' docs/backlog\.md)", (REPO / "CLAUDE.md").read_text(), re.M)
    assert match, "CLAUDE.md lost the backlog shape check"
    return match.group(1)


def run_awk(tmp_path: Path, ledger: str) -> list[str]:
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "backlog.md").write_text(ledger)
    out = subprocess.run(shape_check_awk(), shell=True, cwd=tmp_path, capture_output=True, text=True, check=True)
    return out.stdout.splitlines()


@pytest.mark.skipif(shutil.which("awk") is None, reason="no awk")
def test_shape_check_passes_a_well_formed_ledger(tmp_path: Path) -> None:
    assert run_awk(tmp_path, HEADER + ROW + ROW) == ["## Rows"]


@pytest.mark.skipif(shutil.which("awk") is None, reason="no awk")
@pytest.mark.parametrize("bad", [
    "| GW7 | 2026-10-16 | A10 | TOOL | finding | fpl/usage.py | open\n",   # lost its trailing pipe
    "  EOF\n",                                                             # phantom heredoc delimiter
    "GW7 | 2026-10-16 | A10 | TOOL | finding | fpl/usage.py | open |\n",   # lost its leading pipe
], ids=["no-trailing-pipe", "phantom-eof", "no-leading-pipe"])
def test_shape_check_prints_malformed_rows(tmp_path: Path, bad: str) -> None:
    assert run_awk(tmp_path, HEADER + bad + ROW) == ["## Rows", bad.rstrip("\n")]


def test_agent_legend_names_a10_in_both_mirrors() -> None:
    backlog = (REPO / "docs/backlog.md").read_text()
    legend = next(line for line in backlog.splitlines() if line.startswith("| Agent |"))
    assert "A10 usage-collector" in legend
    assert "A10 usage-collector" in (REPO / "agents/retro-analyst.md").read_text()
