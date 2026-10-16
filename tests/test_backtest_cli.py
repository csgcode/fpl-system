"""CLI tests for `fpl backtest`: argument wiring, the printed report for a
baseline run, a `--set` variant and a `--sweep`, value parsing by
ModelConfig field type, and refusals — over a two-round tmp_path world."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from fpl.__main__ import main
from fpl.backtest import parse_assignment, parse_sweep
from fpl.ep import DEFAULT_CONFIG, ModelConfig
from fpl.store import SnapshotStore
from tests.factories import (
    bootstrap_payload,
    element_summary_payload,
    event_live_payload,
    event_payload,
    fixture_payload,
    live_element_payload,
    match_record_payload,
    player_payload,
    priors_doc,
    team_payload,
)

ROUNDS = (3, 4)
FIRST_DEADLINE = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
POINTS = {3: {1: 7, 3: 2}, 4: {1: 2, 3: 6}}


def _deadline(gw: int) -> datetime:
    return FIRST_DEADLINE + timedelta(days=7 * (gw - ROUNDS[0]))


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _fixtures_document(gw: int) -> dict:
    return {
        "schema_version": 1,
        "gw": gw,
        "base_lambda": {"home": 1.54, "away": 1.33},
        "ratings": {"TST": {"att": 1.0, "defw": 1.0}, "OPP": {"att": 1.0, "defw": 1.0}},
        "fixtures": [
            {"club": club, "gw": g, "opp": opp, "venue": venue, "lambda_att": 1.5,
             "lambda_def": 1.0, "p_cs": 0.3}
            for g in range(gw, gw + 6)
            for club, opp, venue in (("TST", "OPP", "H"), ("OPP", "TST", "A"))
        ],
    }


def _inputs(gw: int, position: str) -> dict:
    rows = {
        "MID": [{"id": 1, "name": "Alpha", "p_start": 0.9, "uncertainty": "LOW",
                 "notes": "starter"}],
        "DEF": [{"id": 3, "name": "Gamma", "p_start": 0.8, "uncertainty": "MED",
                 "notes": "starter"}],
    }
    return {"schema_version": 1, "gw": gw, "position": position,
            "players": rows.get(position, [])}


def _seed_round(raw: Path, analysis: Path, gw: int) -> None:
    deadline = _deadline(gw)
    store = SnapshotStore(raw, now=lambda: deadline - timedelta(hours=16))
    players = [
        player_payload(id=1, web_name="Alpha", team=1, element_type=3, now_cost=60),
        player_payload(id=3, web_name="Gamma", team=2, element_type=2, now_cost=45),
    ]
    teams = [team_payload(id=1, short_name="TST"), team_payload(id=2, name="Opp", short_name="OPP")]
    events = [event_payload(id=r, name=f"Gameweek {r}", deadline_time=_deadline(r).isoformat(),
                            is_next=r == gw, finished=r < gw, data_checked=r < gw)
              for r in range(1, gw + 2)]
    store.save(gw, "bootstrap",
               bootstrap_payload(elements=players, teams=teams, events=events), "seed://test")
    store.save(gw, "fixtures", [fixture_payload(id=1, event=gw)], "seed://test")
    for pid, minutes in ((1, 90), (3, 70)):
        store.save(gw, f"players/summary-{pid}", element_summary_payload(history=[
            match_record_payload(fixture=r, round=r, minutes=minutes) for r in range(1, gw)
        ]), "seed://test")
    _write_json(analysis / f"gw{gw}" / "fixtures.json", _fixtures_document(gw))
    for position in ("GKP", "DEF", "MID", "FWD"):
        _write_json(analysis / f"gw{gw}" / f"inputs-{position}.json", _inputs(gw, position))

    live_store = SnapshotStore(raw, now=lambda: deadline + timedelta(days=3))
    live_store.save(gw + 1, f"event-live-e{gw}", event_live_payload([
        live_element_payload(pid, total_points=points) for pid, points in POINTS[gw].items()
    ]), "seed://test")
    meta = raw / f"gw{gw + 1}" / ".meta" / f"event-live-e{gw}.json"
    _write_json(meta, {**json.loads(meta.read_text()), "final": True})


@pytest.fixture
def world(tmp_path):
    raw, analysis = tmp_path / "raw", tmp_path / "analysis"
    for gw in ROUNDS:
        _seed_round(raw, analysis, gw)
    _write_json(analysis / "club-priors.json",
                priors_doc({"TST": (1.0, 1.0, False), "OPP": (0.8, 1.2, True)}))
    return tmp_path, raw, analysis


def _run(world, *extra: str, gw: str = "5", rounds: str = "3-4") -> int:
    _, raw, analysis = world
    return main(["--data-root", str(raw), "backtest", "--gw", gw, "--rounds", rounds,
                 "--analysis-root", str(analysis), "--no-drift-check", *extra])


def _files(root: Path) -> set[Path]:
    return {path for path in root.rglob("*") if path.is_file()}


def test_baseline_run_prints_per_round_and_position_tables(world, capsys):
    assert _run(world) == 0
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert "rounds 3-4 · drift check: off" in lines
    header = next(line for line in lines if line.split()[:4] == ["round", "n", "bias", "MAE"])
    table = lines[lines.index(header) + 1:]
    assert [row.split()[0] for row in table[:2]] == ["3", "4"]
    assert [row.split()[1] for row in table[:2]] == ["2", "2"]
    baseline = next(row for row in table if row.split()[0] == "baseline")
    assert baseline.split()[1] == "4"
    assert {row.split()[0] for row in table} >= {"DEF", "MID"}
    assert "gate:" not in out


def test_set_prints_variant_round_deltas_and_gate(world, capsys):
    assert _run(world, "--set", "blend_k=300") == 0
    out = capsys.readouterr().out
    assert "variant blend_k=300" in out
    [deltas] = [line for line in out.splitlines() if line.startswith("per-round ΔMAE: ")]
    assert deltas.startswith("per-round ΔMAE: 3 ")
    assert ", 4 " in deltas
    [gate] = [line for line in out.splitlines() if line.startswith("gate: ")]
    assert gate == "gate: PASS" or gate.startswith("gate: FAIL — ")


def test_sweep_output_is_compact(world, capsys):
    assert _run(world, "--sweep", "blend_k=300,450", "--cv") == 0
    lines = capsys.readouterr().out.splitlines()
    configs = 3
    assert len(lines) <= configs + 6
    [picks] = [line for line in lines if line.startswith("LORO picks: ")]
    assert picks.startswith("LORO picks: 3→") and ", 4→" in picks
    assert any(line.startswith("ship: blend_k=") for line in lines)
    assert any(line.startswith("gate: ") for line in lines)
    grid = [line.split()[0] for line in lines if line.split()[:1]
            and line.split()[0].startswith("blend_k=")]
    assert grid == ["blend_k=600", "blend_k=300", "blend_k=450"]


@dataclass(frozen=True)
class _WiderConfig(ModelConfig):
    half_life_matches: float | None = None
    opponent_adjust: bool = False


def test_sweep_parses_none_and_bool():
    base = _WiderConfig()
    assert parse_sweep(["half_life_matches=none,2"], base) == {
        "half_life_matches": [None, 2.0]}
    assert parse_sweep(["opponent_adjust=false,true"], base) == {
        "opponent_adjust": [False, True]}
    assert parse_sweep(["half_life_matches=2"], replace(base, half_life_matches=4.0)) == {
        "half_life_matches": [4.0, 2.0]}
    assert parse_sweep(["blend_k=300,600"], base) == {"blend_k": [600.0, 300.0]}
    assert parse_assignment("half_life_matches=none", base) == ("half_life_matches", None)
    assert parse_assignment("opponent_adjust=true", base) == ("opponent_adjust", True)
    with pytest.raises(ValueError, match="blend_k"):
        parse_assignment("blend_k=none", base)
    with pytest.raises(ValueError, match="opponent_adjust"):
        parse_assignment("opponent_adjust=2", base)


def test_two_key_sweep_is_a_cartesian_grid(world, capsys):
    assert _run(world, "--sweep", "blend_k=300", "--sweep", "blend_floor=0.3", "--cv") == 0
    lines = capsys.readouterr().out.splitlines()
    grid = [line.split()[0] for line in lines if line.startswith("blend_k=")]
    floor = f"{DEFAULT_CONFIG.blend_floor:g}"
    assert grid == [f"blend_k=600,blend_floor={floor}", "blend_k=600,blend_floor=0.3",
                    f"blend_k=300,blend_floor={floor}", "blend_k=300,blend_floor=0.3"]
    [picks] = [line for line in lines if line.startswith("LORO picks: ")]
    assert picks.count("/") == 2


def test_unknown_key_exits_1_listing_the_valid_keys(world, capsys):
    assert _run(world, "--set", "nope=1") == 1
    err = capsys.readouterr().err
    assert "nope" in err
    assert "blend_k" in err and "blend_floor" in err


def test_round_not_before_gw_exits_1(world, capsys):
    assert _run(world, rounds="3-5", gw="5") == 1
    assert "round 5 is not before --gw 5" in capsys.readouterr().err


def test_json_format_is_one_document(world, capsys):
    assert _run(world, "--set", "blend_k=300", "--format", "json") == 0
    document = json.loads(capsys.readouterr().out)
    assert document["rounds"] == [3, 4]
    assert document["drift_check"] is False
    assert set(document["baseline"]["per_round"]) == {"3", "4"}
    comparison = document["comparison"]
    assert set(comparison["round_deltas"]) == {"3", "4"}
    assert {"n", "delta_mae", "se", "ci", "round_wins", "beats", "reasons"} <= set(comparison)
    assert document["variants"][0]["config"]["blend_k"] == 300.0


def test_nothing_is_written_without_out(world, capsys):
    root = world[0]
    before = {path: path.read_bytes() for path in _files(root)}
    assert _run(world, "--sweep", "blend_k=300", "--cv") == 0
    assert {path: path.read_bytes() for path in _files(root)} == before


def test_out_writes_the_json_document(world, capsys, tmp_path):
    out = tmp_path / "scratch" / "backtest.json"
    assert _run(world, "--set", "blend_k=300", "--out", str(out)) == 0
    assert json.loads(out.read_text())["comparison"]["n"] == 4
    assert f"wrote {out}" in capsys.readouterr().out


def test_cv_needs_a_sweep(world, capsys):
    assert _run(world, "--cv") == 1
    assert "--cv" in capsys.readouterr().err
