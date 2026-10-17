"""The player analyst's Call 1, Call 2 and Call 4 outputs stay inline: Claude
Code persists Bash output above about 30,000 characters, and a persisted
output costs the agent extra calls to page through. The Call 1 and Call 2
commands are taken from agents/player-analyst.md itself; Call 4 is a single
`ep` command, written out here with `--out` because GW6 is decided. All run
on the committed GW6 data."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SPEC = (REPO / "agents" / "player-analyst.md").read_text(encoding="utf-8")
LIMIT = 20_000
CALL_1 = ("uv run python -m fpl players --gw N --position POS --status a,d,i,s,n --minutes "
          "--minutes-last 6 --fields id,name,team,price,status,chance_of_playing,news,minutes,"
          "starts,xG,xA,penalties_order,direct_freekicks_order,"
          "corners_and_indirect_freekicks_order --format csv")
CALL_2_FIRST = "uv run python -m fpl corrections --gw N --agent A3"

pytestmark = pytest.mark.skipif(not (REPO / "data/raw/gw6/players").is_dir(),
                                reason="committed gw6 data is absent")


def spec_block(call: int) -> str:
    match = re.search(rf"\*\*Call {call} — [^\n]*\n\n```\n(.*?)\n```", SPEC, re.S)
    assert match, f"no code block under Call {call}"
    return match[1]


def concrete(block: str, pos: str) -> str:
    return (block.replace("{N-1}", "5").replace("{N}", "6").replace("gwN", "gw6")
            .replace("--gw N", "--gw 6").replace("POS", pos))


def run_block(block: str, shell: str = "bash") -> str:
    completed = subprocess.run([shell, "-c", block], cwd=REPO, capture_output=True,
                               text=True, timeout=120, check=False)
    assert completed.returncode == 0, completed.stderr[-500:]
    return completed.stdout + completed.stderr


def test_the_spec_carries_the_measured_commands():
    assert spec_block(1) == CALL_1
    assert spec_block(2).splitlines()[0] == CALL_2_FIRST


@pytest.mark.parametrize("pos", ["GKP", "DEF", "MID", "FWD"])
def test_call_1_fits_inline(pos):
    out = run_block(concrete(spec_block(1), pos))
    assert out.startswith("id,name,team,price,status")
    assert len(out) < LIMIT


@pytest.mark.skipif(shutil.which("zsh") is None, reason="zsh is absent")
def test_call_2_succeeds_under_zsh_without_research_files():
    block = concrete(spec_block(2), "GKP").replace("gw6", "gw5")
    out = run_block(block, shell="zsh")
    assert "no matches found" not in out and "== data/analysis" not in out


@pytest.mark.parametrize("pos", ["GKP", "DEF", "MID", "FWD"])
def test_call_2_fits_inline(pos):
    out = run_block(concrete(spec_block(2), pos))
    assert out.startswith("corrections for A3 from data/retro/gw5.md")
    assert "== data/analysis/gw6/research-" in out
    assert len(out) < LIMIT


@pytest.mark.parametrize("pos", ["GKP", "DEF", "MID", "FWD"])
def test_call_4_fits_inline(pos, tmp_path):
    out = run_block(f"uv run python -m fpl ep --gw 6 --position {pos} --out {tmp_path}/p.json")
    assert "share check" in out
    assert len(out) < LIMIT
