"""`fpl corrections`: the retro digest (no --agent) and the analyst view
(--agent), both local-only."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fpl.__main__ import main
from tests.test_corrections import GW1, GW2, GW3, write_retros

REPO_RETRO = Path(__file__).resolve().parent.parent / "data" / "retro"


def no_gateway(store):
    raise AssertionError("corrections must never build a gateway")


def corrections(*argv: str) -> int:
    return main(["corrections", *argv], service_factory=no_gateway)


@pytest.fixture
def retros(tmp_path) -> Path:
    return write_retros(tmp_path / "retro", gw1=GW1, gw2=GW2, gw3=GW3)


# --- analyst view --------------------------------------------------------------


def test_agent_view_prints_header_rules_and_retired_line(retros, capsys):
    assert corrections("--gw", "4", "--agent", "A3", "--retro-root", str(retros)) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == f"corrections for A3 from {retros}/gw3.md: 2 active, 2 retired"
    assert f"C5 [active — complied] defined in {retros}/gw3.md" in lines
    assert "**C5 — A3 (player-analyst): cap new signings at 0.65.** Revised in place." in lines
    assert f"C6 [active] defined in {retros}/gw2.md" in lines
    assert lines[-1] == ("retired (not shown): C1 retired — satisfied; "
                         "C2 retired — moved to C4")


def test_agent_view_never_prints_retired_rule_text(retros, capsys):
    corrections("--gw", "4", "--agent", "A3", "--retro-root", str(retros))
    out = capsys.readouterr().out
    assert "keep the mapping" not in out
    assert "**C2 — " not in out


def test_agent_view_without_retros(tmp_path, capsys):
    assert corrections("--gw", "1", "--agent", "A3", "--retro-root", str(tmp_path)) == 0
    assert capsys.readouterr().out.strip() == "no retro yet"


def test_agent_view_refuses_a_bad_code(retros, capsys):
    assert corrections("--gw", "4", "--agent", "player", "--retro-root", str(retros)) == 1
    assert "agent code" in capsys.readouterr().err


def test_agent_view_refuses_round(retros, capsys):
    assert corrections("--gw", "4", "--agent", "A3", "--round", "3",
                       "--retro-root", str(retros)) == 1
    assert "--round" in capsys.readouterr().err


# --- retro digest --------------------------------------------------------------


def test_digest_prints_table_new_rows_and_active_rules(tmp_path, capsys):
    root = write_retros(tmp_path / "retro", gw1=GW1, gw2=GW2)
    assert corrections("--gw", "4", "--round", "3", "--retro-root", str(root)) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == f"corrections — status from {root}/gw2.md; rules from gw1.md–gw2.md"
    assert lines[1:3] == ["| C# | Agent | Status | Evidence |", "|---|---|---|---|"]
    assert "| C2 | A3 | retired — moved to C4 | spent |" in lines
    assert "| C5 | A3 | new in gw2.md | – |" in lines
    assert "| C6 | A2, A3 | new in gw2.md | – |" in lines
    assert "active rules: 4" in lines
    assert "**C4 — CODE (fpl/ep.py): unify the curve.** Two shapes.  [gw1.md]" in lines


def test_digest_default_round_is_gw_minus_1(retros, capsys):
    assert corrections("--gw", "4", "--retro-root", str(retros)) == 0
    assert capsys.readouterr().out.splitlines()[0].startswith(
        f"corrections — status from {retros}/gw2.md")


def test_digest_warns_on_a_status_row_without_rule_text(tmp_path, capsys):
    orphan = GW2.replace("| C1 | A3 | active | complied |",
                         "| C1 | A3 | active | complied |\n| C8 | A4 | active | x |")
    root = write_retros(tmp_path / "retro", gw1=GW1, gw2=orphan)
    assert corrections("--gw", "4", "--round", "3", "--retro-root", str(root)) == 0
    assert "warning: C8 has a status row but no rule text" in capsys.readouterr().err


def test_digest_without_retros(tmp_path, capsys):
    assert corrections("--gw", "3", "--retro-root", str(tmp_path)) == 0
    assert capsys.readouterr().out.strip() == "corrections: none (no retro before round 2)"


# --- golden on the committed retros -------------------------------------------

needs_retros = pytest.mark.skipif(not (REPO_RETRO / "gw5.md").is_file(),
                                  reason="data/retro is absent")


def _active_numbers(out: str) -> set[str]:
    return {line.split(" ", 1)[0] for line in out.splitlines() if " defined in " in line}


@needs_retros
@pytest.mark.parametrize("gw, active", [
    (4, {"C7"}), (5, {"C7", "C18"}), (6, {"C7", "C18"}),
])
def test_golden_analyst_view_on_committed_retros(gw, active, capsys):
    assert corrections("--gw", str(gw), "--agent", "A3", "--retro-root", str(REPO_RETRO)) == 0
    out = capsys.readouterr().out
    assert _active_numbers(out) == active
    retired = out.splitlines()[-1]
    assert retired.startswith("retired (not shown): C1 ")
    assert "C2 " in retired and "C3 " in retired
    for hidden in ("**C1 — ", "**C2 — ", "**C3 — "):
        assert hidden not in out


@needs_retros
def test_golden_digest_on_committed_retros(capsys):
    assert corrections("--gw", "7", "--round", "6", "--retro-root", str(REPO_RETRO)) == 0
    captured = capsys.readouterr()
    assert "warning" not in captured.err
    assert "active rules: 15" in captured.out
    printed = {int(n) for n in re.findall(r"(?m)^\*\*C(\d+) — ", captured.out)}
    assert printed == {5, *range(7, 21)}
    assert len(captured.out.encode("utf-8")) < 12_000
