"""CLI tests for `fpl gates`: the one-line summary per record with its
status, and `--render` rewriting only the block between the markers."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from fpl import gates
from fpl.__main__ import main
from fpl.ep import DEFAULT_CONFIG


def _comparison(delta: float, ci: tuple[float, float], bias: tuple[float, float],
                wins: tuple[int, int], reasons: list[str]) -> dict:
    return {
        "n": 1688,
        "baseline": {"n": 1688, "bias": bias[0], "mae": 1.664},
        "variant": {"n": 1688, "bias": bias[1], "mae": 1.664 + delta},
        "delta_mae": delta, "se": 0.004, "ci": list(ci),
        "round_deltas": {"3": delta}, "round_wins": list(wins),
        "by_position": {}, "slices": {"promoted": None, "no_history": None},
        "beats": not reasons, "reasons": reasons,
    }


def _record(name: str, *, kind: str = "model", ship: dict | None = None,
            grid: dict | None = None, comparison: dict | None = None,
            verdict: str | None = None, recorded_at: str = "2026-10-21T09:00:00+00:00",
            **extra) -> dict:
    return {
        "schema_version": 1, "name": name, "kind": kind, "argv": [],
        "rounds": [3, 4, 5, 6, 7],
        "data": {"data_root": "raw", "analysis_root": "analysis", "decisions_root": "decisions",
                 "retro_root": "retro", "drift_check": True, "actuals": {}},
        "decision_commits": {"3": None},
        "code": {"head": None, "dirty": None},
        "baseline_config": asdict(DEFAULT_CONFIG),
        "grid": grid, "picks": None, "ship_value": ship,
        "comparison": comparison, "verdict": verdict,
        "reasons": [] if comparison is None else comparison["reasons"],
        "recorded_at": recorded_at, **extra,
    }


PASSING = _record(
    "k450", ship={"blend_k": 450.0}, grid={"blend_k": [600.0, 300.0, 450.0]}, verdict="PASS",
    comparison=_comparison(-0.0123, (-0.0201, -0.0044), (0.18, 0.17), (5, 5), []),
    recorded_at="2026-10-21T09:00:01+00:00")
FAILING = _record(
    "k300", ship={"blend_k": 300.0}, verdict="FAIL",
    comparison=_comparison(-0.0043, (-0.006, -0.002), (0.18, 0.18), (4, 5),
                           ["effect: ΔMAE −0.0043 > −0.01"]),
    recorded_at="2026-10-21T09:00:02+00:00")


@pytest.fixture
def gates_root(tmp_path) -> Path:
    root = tmp_path / "gates"
    root.mkdir()
    for record in (PASSING, FAILING):
        (root / f"{record['name']}.json").write_text(json.dumps(record), encoding="utf-8")
    return root


def test_gates_summary_prints_report_and_status_lines(gates_root, capsys):
    assert main(["gates", "--gw", "8", "--summary", "--gates-root", str(gates_root)]) == 0
    lines = capsys.readouterr().out.splitlines()
    passing = lines.index("k450: PASS ship blend_k=450 — ΔMAE −0.0123 "
                          "[CI −0.020, −0.004], bias 0.18→0.17, wins 5/5")
    assert lines[passing + 1].strip() == "shipped"
    failing = next(i for i, line in enumerate(lines) if line.startswith("k300: FAIL"))
    assert lines[failing + 1].strip() == "rejected: ΔMAE −0.0043 > −0.01 (effect)"


def test_gates_summary_marks_a_pass_reverted_by_combined(gates_root, capsys):
    combined = _record("combined", kind="combined", ship={}, shipped_config=asdict(DEFAULT_CONFIG),
                       reverted=["k450"], recorded_at="2026-10-21T09:00:03+00:00")
    (gates_root / "combined.json").write_text(json.dumps(combined), encoding="utf-8")
    assert main(["gates", "--gw", "8", "--summary", "--gates-root", str(gates_root)]) == 0
    lines = capsys.readouterr().out.splitlines()
    passing = next(i for i, line in enumerate(lines) if line.startswith("k450: PASS"))
    assert lines[passing + 1].strip().startswith("reverted")
    assert any(line.startswith("combined: ") for line in lines)


def test_gates_summary_with_no_records(tmp_path, capsys):
    assert main(["gates", "--gw", "8", "--summary", "--gates-root", str(tmp_path)]) == 0
    assert "no gate records" in capsys.readouterr().out


def test_render_rewrites_only_the_marked_block(gates_root, tmp_path, capsys):
    doc = tmp_path / "ep-model.md"
    doc.write_text("# EP\n\nbefore\n\n<!-- gates:begin -->\nstale\n<!-- gates:end -->\n\nafter\n",
                   encoding="utf-8")
    assert main(["gates", "--gw", "8", "--render", "--gates-root", str(gates_root),
                 "--doc", str(doc)]) == 0
    text = doc.read_text(encoding="utf-8")
    assert text.startswith("# EP\n\nbefore\n\n<!-- gates:begin -->\n")
    assert text.endswith("<!-- gates:end -->\n\nafter\n")
    assert "stale" not in text
    records = gates.load_records(gates_root)
    assert gates.block(text).strip() == gates.render(records).strip()
    rows = [line for line in gates.block(text).splitlines() if line.startswith("| k")]
    assert [row.split("|")[1].strip() for row in rows] == ["k450", "k300"]
    assert "blend_k=600,300,450" in rows[0]


def test_render_refuses_a_doc_without_markers(gates_root, tmp_path, capsys):
    doc = tmp_path / "ep-model.md"
    doc.write_text("# EP\n", encoding="utf-8")
    assert main(["gates", "--gw", "8", "--render", "--gates-root", str(gates_root),
                 "--doc", str(doc)]) == 1
    assert "gates:begin" in capsys.readouterr().err


def test_render_of_no_records_is_empty():
    assert gates.render([]) == ""


def test_records_follow_manifest_order_with_combined_last(tmp_path):
    root = tmp_path / "gates"
    root.mkdir()
    same = "2026-10-21T09:00:00+00:00"
    for record in (
        _record("baseline", recorded_at=same),
        _record("k450", ship={"blend_k": 450.0}, recorded_at=same),
        _record("k300", ship={"blend_k": 300.0}, recorded_at=same),
        _record("combined", kind="combined", ship={}, shipped_config=asdict(DEFAULT_CONFIG),
                reverted=[], recorded_at=same),
        _record("adhoc", recorded_at="2026-10-21T08:00:00+00:00"),
    ):
        (root / f"{record['name']}.json").write_text(json.dumps(record), encoding="utf-8")
    (root / gates.MANIFEST).write_text(
        "".join(f'[[gate]]\nname = "{name}"\nkind = "model"\nargv = {argv}\n\n'
                for name, argv in (("baseline", "[]"), ("k450", '["--set", "blend_k=450"]'),
                                   ("k300", '["--set", "blend_k=300"]'))),
        encoding="utf-8")
    names = [record.name for record in gates.load_records(root)]
    assert names == ["baseline", "k450", "k300", "adhoc", "combined"]


def test_records_without_a_manifest_keep_combined_last(tmp_path):
    root = tmp_path / "gates"
    root.mkdir()
    same = "2026-10-21T09:00:00+00:00"
    for record in (_record("k450", recorded_at=same),
                   _record("combined", kind="combined", ship={},
                           shipped_config=asdict(DEFAULT_CONFIG), reverted=[], recorded_at=same)):
        (root / f"{record['name']}.json").write_text(json.dumps(record), encoding="utf-8")
    assert [record.name for record in gates.load_records(root)] == ["k450", "combined"]


def test_gates_summary_shows_policy_slice_and_hypothesis(tmp_path, capsys):
    root = tmp_path / "gates"
    root.mkdir()
    policy = _record(
        "drop-promoted", kind="policy", ship={}, verdict="PASS",
        comparison=_comparison(-0.012, (-0.02, -0.004), (0.18, 0.16), (5, 5), []),
        slice_verdict="PASS", hypothesis="supported")
    (root / "drop-promoted.json").write_text(json.dumps(policy), encoding="utf-8")
    assert main(["gates", "--gw", "8", "--summary", "--gates-root", str(root)]) == 0
    lines = capsys.readouterr().out.splitlines()
    status = lines[lines.index(next(l for l in lines if l.startswith("drop-promoted:"))) + 1]
    assert status.strip() == "passed (a policy never ships) · slice PASS · hypothesis supported"
