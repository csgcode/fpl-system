"""`fpl persistence`: the residual-persistence statistic over the calibration
ledgers on disk, local-only."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from fpl.__main__ import main
from tests.test_persistence import _reports

POSITIONS = ("GKP", "DEF", "MID", "FWD")
FIT = r"n \d+, slope -?\d+\.\d{3} \[-?\d+\.\d{3}, -?\d+\.\d{3}\] \(cluster\), r -?\d+\.\d{3}"


def no_gateway(store):
    raise AssertionError("persistence must never build a gateway")


def run(*argv: str) -> int:
    return main(["persistence", *argv], service_factory=no_gateway)


def write_ledgers(root: Path, n_players: int, rounds: range = range(1, 7)) -> Path:
    errors = {}
    for pid in range(1, n_players + 1):
        x = float(pid % 7 - 3)
        noise = 0.1 if pid % 2 else -0.1
        errors[pid] = {r: x if r <= 3 else x + noise for r in rounds}
    positions = {pid: POSITIONS[pid % 4] for pid in errors}
    root.mkdir(parents=True, exist_ok=True)
    for report in _reports(errors, positions, rounds):
        (root / f"gw{report.round}-calibration.json").write_text(report.model_dump_json())
    return root


@pytest.fixture
def strong(tmp_path) -> Path:
    root = write_ledgers(tmp_path / "retro", n_players=100)
    # Rounds at or after --gw are never read: these would fail to load.
    (root / "gw7-calibration.json").write_text("{}")
    (root / "gw8-calibration.json").write_text("{}")
    return root


def test_prints_window_three_positions_and_sensitivity(strong, capsys):
    assert run("--gw", "7", "--retro-root", str(strong)) == 0
    lines = capsys.readouterr().out.splitlines()

    assert lines[0] == f"ledgers: rounds 1-6 from {strong}"
    assert re.fullmatch(rf"window 3, min starts 2: {FIT} — significant", lines[1])
    assert [line.split(":")[0].strip() for line in lines[2:6]] == ["DEF", "FWD", "GKP", "MID"]
    assert all(re.fullmatch(rf"  [A-Z]{{3}}: {FIT}", line) for line in lines[2:6])
    assert lines[6] == "sensitivity:"
    assert re.fullmatch(rf"window 1, min starts 1: {FIT} — (not )?significant", lines[7])
    assert re.fullmatch(rf"window 2, min starts 2: {FIT} — (not )?significant", lines[12])


def test_window_three_line_carries_the_fit(strong, capsys):
    run("--gw", "7", "--retro-root", str(strong))
    line = capsys.readouterr().out.splitlines()[1]

    # Targets 4, 5, 6 × 100 players.
    assert line.startswith("window 3, min starts 2: n 300, slope ")


def test_exit_three_when_not_significant(tmp_path, capsys):
    root = write_ledgers(tmp_path / "retro", n_players=10)

    assert run("--gw", "7", "--retro-root", str(root)) == 3
    assert capsys.readouterr().out.splitlines()[1].endswith("— not significant")


def test_window_and_min_starts_options(strong, capsys):
    assert run("--gw", "7", "--retro-root", str(strong), "--window", "2", "--min-starts", "1") == 0
    lines = capsys.readouterr().out.splitlines()

    assert lines[1].startswith("window 2, min starts 1: ")
    assert [line.split(":")[0] for line in lines if line.startswith("window")] == [
        "window 2, min starts 1",
        "window 1, min starts 1",
    ]


def test_json_format(strong, capsys):
    assert run("--gw", "7", "--retro-root", str(strong), "--format", "json") == 0
    document = json.loads(capsys.readouterr().out)

    assert document["gw"] == 7
    assert document["rounds"] == [1, 2, 3, 4, 5, 6]
    assert document["significant"] is True
    assert [w["window"] for w in document["windows"]] == [3, 1, 2]
    main_fit = document["windows"][0]
    assert main_fit["n"] == 300
    assert main_fit["target_rounds"] == [4, 5, 6]
    assert set(main_fit["by_position"]) == set(POSITIONS)
    assert len(main_fit["ci_cluster"]) == 2
    assert "pairs" not in main_fit


def test_undefined_fit_prints_na(tmp_path, capsys):
    root = write_ledgers(tmp_path / "retro", n_players=1, rounds=range(1, 5))

    assert run("--gw", "7", "--retro-root", str(root)) == 3
    line = capsys.readouterr().out.splitlines()[1]
    assert line == "window 3, min starts 2: n 1, slope n/a, r n/a — not significant"


def test_unreadable_ledger_exits_one_naming_the_file(tmp_path, capsys):
    root = write_ledgers(tmp_path / "retro", n_players=10)
    unreadable = root / "gw6-calibration.json"
    unreadable.unlink()
    unreadable.mkdir()

    assert run("--gw", "7", "--retro-root", str(root)) == 1
    err = capsys.readouterr().err
    assert err.startswith(f"error: cannot read ledger {unreadable}: ")


def test_refuses_without_ledgers(tmp_path, capsys):
    assert run("--gw", "7", "--retro-root", str(tmp_path / "missing")) == 1
    assert "no calibration ledgers before GW7" in capsys.readouterr().err


def test_refuses_a_bad_min_starts(strong, capsys):
    assert run("--gw", "7", "--retro-root", str(strong), "--min-starts", "4") == 1
    assert "min_starts" in capsys.readouterr().err
