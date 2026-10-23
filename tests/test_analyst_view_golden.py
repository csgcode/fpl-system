"""The player analyst's Call 1 and Call 2 outputs stay inline: Claude Code
persists Bash output above about 30,000 characters, and a persisted output
costs the agent extra calls to page through. The commands are taken from
agents/player-analyst.md itself and run on the committed GW6 data."""

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


@pytest.fixture(scope="module")
def season_store(tmp_path_factory) -> Path:
    """A store built from the committed raw tree outside the repo: the
    spec's commands read a season store, and the repo's data/store is not
    the test's to write."""
    from fpl.season_store import sync

    db = tmp_path_factory.mktemp("store") / "season.sqlite"
    sync(REPO / "data/raw", db)
    return db


@pytest.mark.parametrize("pos", ["GKP", "DEF", "MID", "FWD"])
def test_call_1_fits_inline(pos, season_store):
    out = run_block(f"{concrete(spec_block(1), pos)} --store {season_store}")
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
def test_call_1_from_the_store_fills_no_summary_rows_and_fits_inline(pos, season_store):
    command = concrete(spec_block(1), pos)
    from_summaries = run_block(f"{command} --history-from summaries").splitlines()
    from_store = run_block(f"{command} --store {season_store}").splitlines()

    assert from_store[0] == from_summaries[0]
    assert len(from_store) == len(from_summaries)
    changed = [(a, b) for a, b in zip(from_summaries, from_store, strict=True) if a != b]
    assert changed and all(a.endswith(",no summary") for a, _ in changed)
    assert not any("no summary" in line for line in from_store)
    assert len("\n".join(from_store)) < LIMIT
