"""CLI tests for `fpl backtest`: argument wiring, the printed report for a
baseline run, a `--set` variant and a `--sweep`, value parsing by
ModelConfig field type, and refusals — over a two-round tmp_path world."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from fpl.__main__ import main
from fpl.backtest import combine, parse_assignment, parse_sweep
from fpl.calibrate import Aggregate, CalibrationReport, MinutesCalibration
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
QUIET_POINTS = {3: {1: 1, 3: 1}, 4: {1: 1, 3: 1}}
NO_RETURNS = {"expected_goals": "0.00", "expected_assists": "0.00", "goals_scored": 0,
              "assists": 0, "bonus": 0, "defensive_contribution": 0.0}
RECORD_FIELDS = {"schema_version", "name", "kind", "argv", "rounds", "data", "decision_commits",
                 "code", "baseline_config", "grid", "picks", "ship_value", "comparison",
                 "verdict", "reasons", "recorded_at"}


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


def _seed_round(raw: Path, analysis: Path, gw: int, *, points=POINTS,
                match: dict | None = None) -> None:
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
            match_record_payload(fixture=r, round=r, minutes=minutes, **(match or {}))
            for r in range(1, gw)
        ]), "seed://test")
    _write_json(analysis / f"gw{gw}" / "fixtures.json", _fixtures_document(gw))
    for position in ("GKP", "DEF", "MID", "FWD"):
        _write_json(analysis / f"gw{gw}" / f"inputs-{position}.json", _inputs(gw, position))

    live_store = SnapshotStore(raw, now=lambda: deadline + timedelta(days=3))
    live_store.save(gw + 1, f"event-live-e{gw}", event_live_payload([
        live_element_payload(pid, total_points=points) for pid, points in points[gw].items()
    ]), "seed://test")
    meta = raw / f"gw{gw + 1}" / ".meta" / f"event-live-e{gw}.json"
    _write_json(meta, {**json.loads(meta.read_text()), "final": True})


def _seed_world(tmp_path: Path, **seed) -> tuple[Path, Path, Path]:
    raw, analysis = tmp_path / "raw", tmp_path / "analysis"
    for gw in ROUNDS:
        _seed_round(raw, analysis, gw, **seed)
    _write_json(analysis / "club-priors.json",
                priors_doc({"TST": (1.0, 1.0, False), "OPP": (0.8, 1.2, True)}))
    return tmp_path, raw, analysis


@pytest.fixture
def world(tmp_path):
    return _seed_world(tmp_path)


@pytest.fixture
def quiet_world(tmp_path):
    """Current form with no attacking returns and one-point actuals: a
    smaller blend K moves every prediction towards the outcome, so a
    `blend_k` sweep passes the gate."""
    return _seed_world(tmp_path, points=QUIET_POINTS, match=NO_RETURNS)


def _run(world, *extra: str, gw: str = "5", rounds: str = "3-4") -> int:
    root, raw, analysis = world
    return main(["--data-root", str(raw), "backtest", "--gw", gw, "--rounds", rounds,
                 "--analysis-root", str(analysis), "--retro-root", str(root / "retro"),
                 "--no-drift-check", *extra])


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
    rows = [line for line in lines if line.startswith("blend_k=")]
    assert rows[0].endswith("(production)")
    assert not any(row.endswith("(production)") for row in rows[1:])
    assert all("ΔMAE(in-sample) " in row for row in rows)
    [gate_delta] = [line for line in lines if line.startswith("ΔMAE ")]
    assert "[CI " in gate_delta


def test_sweep_with_set_labels_no_row_production(world, capsys):
    assert _run(world, "--set", "blend_floor=0.3", "--sweep", "blend_k=300", "--cv") == 0
    rows = [line for line in capsys.readouterr().out.splitlines()
            if line.startswith("blend_floor=")]
    assert [row.split()[0] for row in rows] == ["blend_floor=0.3,blend_k=600",
                                                "blend_floor=0.3,blend_k=300"]
    assert not any("(production)" in row for row in rows)


def test_sweep_values_printing_alike_exit_1(world, capsys):
    assert _run(world, "--sweep", "blend_k=300,300.0000001", "--cv") == 1
    err = capsys.readouterr().err
    assert "blend_k" in err and "300" in err


def test_sweep_refuses_values_printing_alike():
    with pytest.raises(ValueError, match="blend_k=300"):
        parse_sweep(["blend_k=300,300.0000001"], DEFAULT_CONFIG)


def test_set_key_given_twice_exits_1(world, capsys):
    assert _run(world, "--set", "blend_k=300", "--set", "blend_k=450") == 1
    assert "--set blend_k given twice" in capsys.readouterr().err


def test_key_in_both_set_and_sweep_exits_1(world, capsys):
    assert _run(world, "--set", "blend_k=300", "--sweep", "blend_k=450", "--cv") == 1
    assert "blend_k given to both --set and --sweep" in capsys.readouterr().err


def test_sweep_refuses_more_than_two_keys():
    with pytest.raises(ValueError, match="up to 2 keys"):
        parse_sweep(["blend_k=300", "blend_floor=0.3", "opponent_adjust=true"],
                    _WiderConfig())


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


def _write_ledger(retro: Path, gw: int, n: int) -> None:
    report = CalibrationReport(
        round=gw, players=(), unmatched_prediction_ids=(),
        overall=Aggregate(n=n, bias=0.0, mae=1.0), by_position={}, by_uncertainty={},
        by_price_band={},
        minutes=MinutesCalibration(n=0, brier=0.0, expected_starts=0.0, actual_starts=0),
    )
    retro.mkdir(parents=True, exist_ok=True)
    (retro / f"gw{gw}-calibration.json").write_text(report.model_dump_json(), encoding="utf-8")


def _rows(out: str) -> dict[str, list[str]]:
    lines = out.splitlines()
    header = next(line for line in lines if line.split()[:1] == ["round"])
    table = lines[lines.index(header):]
    return {row.split()[0]: row.split() for row in table if row.split()}


def test_ledger_n_gap_refuses(world, capsys):
    root = world[0]
    _write_ledger(root / "retro", 3, n=12)
    assert _run(world, "--max-ledger-n-gap", "5") == 1
    captured = capsys.readouterr()
    rows = _rows(captured.out)
    assert rows["round"] == ["round", "n", "bias", "MAE", "ledger_n", "Δn", "code_drift"]
    assert rows["3"][1] == "2"
    assert rows["3"][4:] == ["12", "\u221210", "-"]
    assert rows["4"][4:] == ["-", "-", "-"]
    assert "ledger" in captured.err and "--max-ledger-n-gap 5" in captured.err

    assert _run(world, "--max-ledger-n-gap", "10") == 0


def test_ledger_n_gap_blocks_the_record(world, capsys, tmp_path):
    _write_ledger(world[0] / "retro", 3, n=12)
    gates_root = tmp_path / "gates"
    assert _run(world, "--set", "blend_k=300", "--record", "k300",
                "--gates-root", str(gates_root), "--max-ledger-n-gap", "5") == 1
    assert not (gates_root / "k300.json").exists()


def test_record_writes_once_and_force_archives(world, capsys, tmp_path):
    _, raw, _ = world
    gates_root = tmp_path / "gates"
    record_args = ("--set", "blend_k=300", "--record", "k300", "--gates-root", str(gates_root))
    assert _run(world, *record_args) == 0
    path = gates_root / "k300.json"
    record = json.loads(path.read_text())
    assert RECORD_FIELDS <= set(record)
    assert record["schema_version"] == 1
    assert (record["name"], record["kind"]) == ("k300", "model")
    assert record["argv"] == ["--set", "blend_k=300"]
    assert record["rounds"] == [3, 4]
    actuals = raw / "gw4" / "event-live-e3.json"
    assert record["data"]["actuals"]["3"] == {
        "path": str(actuals), "sha256": hashlib.sha256(actuals.read_bytes()).hexdigest()}
    assert record["data"]["analysis_root"] == str(world[2])
    assert record["decision_commits"] == {"3": None, "4": None}
    assert set(record["code"]) == {"head", "dirty"}
    assert record["baseline_config"] == asdict(DEFAULT_CONFIG)
    assert record["ship_value"] == {"blend_k": 300.0}
    assert record["comparison"]["n"] == 4
    assert record["verdict"] in ("PASS", "FAIL")
    assert record["reasons"] == record["comparison"]["reasons"]
    assert f"wrote {path}" in capsys.readouterr().out

    first = path.read_bytes()
    assert _run(world, *record_args) == 1
    assert str(path) in capsys.readouterr().err
    assert path.read_bytes() == first

    assert _run(world, *record_args, "--force") == 0
    [archived] = (gates_root / "archive").glob("k300.*.json")
    assert archived.read_bytes() == first
    assert json.loads(path.read_text())["recorded_at"]


def test_record_of_a_sweep_needs_cv(world, capsys, tmp_path):
    assert _run(world, "--sweep", "blend_k=300", "--record", "k",
                "--gates-root", str(tmp_path / "gates")) == 1
    assert "--cv" in capsys.readouterr().err


def _write_manifest(path: Path, *entries: tuple[str, str, list[str]]) -> Path:
    blocks = [f'[[gate]]\nname = "{name}"\nkind = "{kind}"\nargv = {json.dumps(argv)}\n'
              for name, kind, argv in entries]
    path.write_text("\n".join(blocks), encoding="utf-8")
    return path


def _records(root: Path, *names: str) -> dict[str, dict]:
    return {name: json.loads((root / f"{name}.json").read_text()) for name in names}


def test_record_all_runs_in_order_with_earlier_passes_as_baseline(quiet_world, capsys, tmp_path):
    gates_root = tmp_path / "gates"
    manifest = _write_manifest(
        tmp_path / "manifest.toml",
        ("baseline", "model", []),
        ("x", "model", ["--sweep", "blend_k=300,450", "--cv"]),
        ("y", "model", ["--set", "blend_floor=0.9"]),
    )
    run_all = ("--manifest", str(manifest), "--record-all", "--gates-root", str(gates_root))
    assert _run(quiet_world, *run_all) == 0
    records = _records(gates_root, "baseline", "x", "y", "combined")
    assert records["baseline"]["baseline_config"] == asdict(DEFAULT_CONFIG)
    assert records["baseline"]["comparison"] is None
    assert records["x"]["baseline_config"] == asdict(DEFAULT_CONFIG)
    assert records["x"]["grid"] == {"blend_k": [600.0, 300.0, 450.0]}
    assert records["x"]["verdict"] == "PASS"
    assert records["x"]["ship_value"] == {"blend_k": 300.0}
    assert records["y"]["baseline_config"] == asdict(replace(DEFAULT_CONFIG, blend_k=300.0))
    assert records["y"]["verdict"] == "FAIL"
    combined = records["combined"]
    assert combined["kind"] == "combined"
    assert combined["shipped_config"] == asdict(replace(DEFAULT_CONFIG, blend_k=300.0))
    assert combined["reverted"] == []
    assert combined["verdict"] == "PASS"
    out = capsys.readouterr().out
    assert out.index("baseline:") < out.index("x:") < out.index("y:") < out.index("combined:")

    kept = {name: (gates_root / f"{name}.json").read_bytes() for name in ("baseline", "x", "y")}
    assert _run(quiet_world, *run_all) == 0
    assert "x: record exists" in capsys.readouterr().out
    assert {name: (gates_root / f"{name}.json").read_bytes() for name in kept} == kept
    assert len(list((gates_root / "archive").glob("combined.*.json"))) == 1


def test_record_all_force_reruns_from_the_recorded_baseline(quiet_world, capsys, tmp_path):
    gates_root = tmp_path / "gates"
    manifest = _write_manifest(tmp_path / "manifest.toml", ("baseline", "model", []),
                               ("x", "model", ["--sweep", "blend_k=300,450", "--cv"]))
    run_all = ("--manifest", str(manifest), "--record-all", "--gates-root", str(gates_root))
    assert _run(quiet_world, *run_all) == 0
    baseline = json.loads((gates_root / "baseline.json").read_text())
    baseline["baseline_config"]["blend_floor"] = 0.25
    (gates_root / "baseline.json").write_text(json.dumps(baseline), encoding="utf-8")

    assert _run(quiet_world, *run_all, "--force") == 0
    records = _records(gates_root, "baseline", "x")
    assert records["baseline"]["baseline_config"]["blend_floor"] == 0.25
    assert records["x"]["baseline_config"]["blend_floor"] == 0.25
    assert len(list((gates_root / "archive").glob("x.*.json"))) == 1


def test_record_all_refuses_a_baseline_record_missing_a_config_field(quiet_world, capsys,
                                                                     tmp_path):
    gates_root = tmp_path / "gates"
    manifest = _write_manifest(tmp_path / "manifest.toml", ("baseline", "model", []),
                               ("x", "model", ["--sweep", "blend_k=300,450", "--cv"]))
    run_all = ("--manifest", str(manifest), "--record-all", "--gates-root", str(gates_root))
    assert _run(quiet_world, *run_all) == 0
    baseline = json.loads((gates_root / "baseline.json").read_text())
    del baseline["baseline_config"]["blend_floor"]
    (gates_root / "baseline.json").write_text(json.dumps(baseline), encoding="utf-8")
    capsys.readouterr()
    before = {path: path.read_bytes() for path in _files(gates_root)}

    assert _run(quiet_world, *run_all, "--force") == 1
    err = capsys.readouterr().err
    assert "blend_floor" in err
    assert "re-record the baseline" in err
    assert {path: path.read_bytes() for path in _files(gates_root)} == before


def test_record_all_combined_failure_reverts_the_last_pass(quiet_world, capsys, tmp_path,
                                                           monkeypatch):
    from fpl import backtest

    real_combine = backtest.combine

    def rejecting_blend_k_300(base, passes, judge):
        def judged(config):
            verdict = judge(config)
            return replace(verdict, beats=verdict.beats and config.blend_k != 300.0)
        return real_combine(base, passes, judged)

    monkeypatch.setattr(backtest, "combine", rejecting_blend_k_300)
    gates_root = tmp_path / "gates"
    manifest_path = tmp_path / "manifest.toml"
    entries = [("baseline", "model", []), ("x", "model", ["--sweep", "blend_k=300,450", "--cv"])]
    run_all = ("--manifest", str(manifest_path), "--record-all", "--gates-root", str(gates_root))
    _write_manifest(manifest_path, *entries)
    assert _run(quiet_world, *run_all) == 0
    records = _records(gates_root, "x", "combined")
    assert records["x"]["verdict"] == "PASS"
    assert records["x"]["ship_value"] == {"blend_k": 300.0}
    assert records["combined"]["reverted"] == ["x"]
    assert records["combined"]["shipped_config"] == asdict(DEFAULT_CONFIG)

    _write_manifest(manifest_path, *entries, ("z", "model", ["--set", "blend_floor=0.9"]))
    assert _run(quiet_world, *run_all) == 0
    z = _records(gates_root, "z")["z"]
    assert z["baseline_config"] == asdict(DEFAULT_CONFIG)


def test_manifest_must_start_with_baseline(world, capsys, tmp_path):
    manifest = _write_manifest(tmp_path / "manifest.toml", ("x", "model", ["--set", "blend_k=300"]))
    assert _run(world, "--manifest", str(manifest), "--record-all",
                "--gates-root", str(tmp_path / "gates")) == 1
    assert "baseline" in capsys.readouterr().err


def test_combined_failure_reverts_the_last_pass():
    def judge(config):
        return type("Judged", (), {"beats": config.blend_floor == DEFAULT_CONFIG.blend_floor})()

    result = combine(DEFAULT_CONFIG,
                     [("x", {"blend_k": 300.0}), ("y", {"blend_floor": 0.3})], judge)
    assert result.reverted == ("y",)
    assert result.overrides == {"blend_k": 300.0}
    assert result.config == replace(DEFAULT_CONFIG, blend_k=300.0)


def test_combined_with_nothing_passing_ships_the_baseline():
    result = combine(DEFAULT_CONFIG, [("x", {"blend_k": 300.0})],
                     lambda config: type("Judged", (), {"beats": False})())
    assert result.reverted == ("x",)
    assert result.config == DEFAULT_CONFIG
    assert result.comparison is None


def _discount_gamma(analysis: Path) -> None:
    """Gamma (OPP, promoted) carries an analyst `attack_mult` in every round."""
    for gw in ROUNDS:
        path = analysis / f"gw{gw}" / "inputs-DEF.json"
        document = json.loads(path.read_text())
        document["players"][0].update(overrides={"attack_mult": 0.5}, reason="promoted club")
        path.write_text(json.dumps(document), encoding="utf-8")


def test_inputs_policy_is_a_variant_gated_on_its_slice(world, capsys, tmp_path):
    _discount_gamma(world[2])
    gates_root = tmp_path / "gates"
    argv = ["--inputs-policy", "drop_promoted", "--gate-slice", "promoted"]
    assert _run(world, *argv, "--record", "dp", "--gates-root", str(gates_root)) == 0
    lines = capsys.readouterr().out.splitlines()
    assert any(line.startswith("variant inputs_policy=drop_promoted  n 4") for line in lines)
    [slice_line] = [line for line in lines if line.startswith("slice promoted ")]
    assert slice_line.startswith("slice promoted (n 2): n/a")
    [verdict] = [line for line in lines if line.startswith("hypothesis: ")]
    record = json.loads((gates_root / "dp.json").read_text())
    assert (record["kind"], record["argv"]) == ("policy", argv)
    assert record["slice_verdict"] == "n/a"
    assert record["hypothesis"] in ("supported", "not supported")
    assert verdict == f"hypothesis: {record['hypothesis']}"
    gate = record["comparison"]["slice_gate"]
    assert (gate["name"], gate["n"], gate["verdict"]) == ("promoted", 2, "n/a")
    assert record["comparison"]["slices"]["promoted"]["delta_mae"] != 0
    assert record["comparison"]["by_position"]["MID"]["delta_mae"] == 0
    assert record["ship_value"] == {}


def test_gate_slice_needs_a_variant(world, capsys):
    assert _run(world, "--gate-slice", "promoted") == 1
    assert "--gate-slice" in capsys.readouterr().err


def test_record_all_accepts_policy_and_slice_entries(quiet_world, capsys, tmp_path):
    _discount_gamma(quiet_world[2])
    gates_root = tmp_path / "gates"
    manifest = _write_manifest(
        tmp_path / "manifest.toml",
        ("baseline", "model", []),
        ("drop-promoted", "policy", ["--inputs-policy", "drop_promoted",
                                     "--gate-slice", "promoted"]),
        ("no-history-k", "model", ["--sweep", "blend_k_no_history=none,300", "--cv",
                                   "--gate-slice", "no_history"]),
    )
    assert _run(quiet_world, "--manifest", str(manifest), "--record-all",
                "--gates-root", str(gates_root)) == 0
    records = _records(gates_root, "drop-promoted", "no-history-k", "combined")
    policy, no_history = records["drop-promoted"], records["no-history-k"]
    assert (policy["kind"], policy["verdict"], policy["ship_value"]) == ("policy", "FAIL", {})
    assert (policy["slice_verdict"], policy["hypothesis"]) == ("n/a", "not supported")
    gate = policy["comparison"]["slice_gate"]
    assert (gate["name"], gate["n"], gate["verdict"]) == ("promoted", 2, "n/a")
    assert (no_history["kind"], no_history["verdict"]) == ("model", "FAIL")
    assert no_history["ship_value"] == {"blend_k_no_history": None}
    assert (no_history["slice_verdict"], no_history["hypothesis"]) == ("n/a", "not supported")
    gate = no_history["comparison"]["slice_gate"]
    assert (gate["name"], gate["n"], gate["verdict"]) == ("no_history", 0, "n/a")
    assert records["combined"]["shipped_config"] == asdict(DEFAULT_CONFIG)
    assert records["combined"]["reverted"] == []


@pytest.mark.parametrize("argv", [
    ["--inputs-policy", "drop_promoted", "--set", "blend_k=300"],
    ["--inputs-policy", "drop_promoted", "--sweep", "blend_k=300,450", "--cv"],
])
def test_a_policy_run_refuses_model_values(world, capsys, tmp_path, argv):
    gates_root = tmp_path / "gates"
    assert _run(world, *argv, "--record", "p", "--gates-root", str(gates_root)) == 1
    assert "never carries a ship value" in capsys.readouterr().err
    assert not gates_root.exists()


def test_record_all_refuses_a_policy_entry_with_model_values(world, capsys, tmp_path):
    manifest = _write_manifest(tmp_path / "manifest.toml", ("baseline", "model", []),
                               ("p", "policy", ["--inputs-policy", "drop_promoted",
                                                "--set", "blend_k=300"]))
    assert _run(world, "--manifest", str(manifest), "--record-all",
                "--gates-root", str(tmp_path / "gates")) == 1
    err = capsys.readouterr().err
    assert "manifest entry p" in err and "never carries a ship value" in err


def _passing_policy_record(world, gates_root: Path, capsys) -> list[str]:
    """Records `p` as a policy, then marks it PASS with a ship value — the
    shape an older build could write — and returns its argv."""
    argv = ["--inputs-policy", "drop_promoted"]
    assert _run(world, *argv, "--record", "p", "--gates-root", str(gates_root)) == 0
    path = gates_root / "p.json"
    record = json.loads(path.read_text())
    record.update(verdict="PASS", reasons=[], ship_value={"blend_k": 300.0})
    path.write_text(json.dumps(record), encoding="utf-8")
    capsys.readouterr()
    return argv


@pytest.mark.parametrize("kind, entry_argv, message", [
    ("model", ["--set", "blend_k=300"], "kind policy"),
    ("policy", ["--inputs-policy", "drop_promoted", "--gate-slice", "promoted"], "argv"),
])
def test_record_all_refuses_an_existing_record_unlike_its_entry(world, capsys, tmp_path, kind,
                                                                entry_argv, message):
    gates_root = tmp_path / "gates"
    _passing_policy_record(world, gates_root, capsys)
    before = {path: path.read_bytes() for path in _files(gates_root)}
    manifest = _write_manifest(tmp_path / "manifest.toml", ("baseline", "model", []),
                               ("p", kind, entry_argv))
    assert _run(world, "--manifest", str(manifest), "--record-all",
                "--gates-root", str(gates_root)) == 1
    err = capsys.readouterr().err
    assert "p.json" in err and message in err and "--force" in err
    assert {path: path.read_bytes() for path in _files(gates_root)} == before


def test_record_all_keeps_a_passing_policy_out_of_the_overlay(quiet_world, capsys, tmp_path):
    gates_root = tmp_path / "gates"
    argv = _passing_policy_record(quiet_world, gates_root, capsys)
    manifest = _write_manifest(tmp_path / "manifest.toml", ("baseline", "model", []),
                               ("p", "policy", argv),
                               ("y", "model", ["--set", "blend_floor=0.9"]))
    assert _run(quiet_world, "--manifest", str(manifest), "--record-all",
                "--gates-root", str(gates_root)) == 0
    records = _records(gates_root, "y", "combined")
    assert records["y"]["baseline_config"] == asdict(DEFAULT_CONFIG)
    assert records["combined"]["shipped_config"]["blend_k"] == DEFAULT_CONFIG.blend_k


@pytest.mark.parametrize("kind, argv, message", [
    ("model", ["--inputs-policy", "drop_promoted"], "policy entry"),
    ("policy", ["--set", "blend_k=300"], "--inputs-policy"),
    ("model", ["--gate-slice", "promoted"], "--gate-slice"),
])
def test_record_all_refuses_a_policy_kind_mismatch(world, capsys, tmp_path, kind, argv,
                                                   message):
    manifest = _write_manifest(tmp_path / "manifest.toml", ("baseline", "model", []),
                               ("bad", kind, argv))
    assert _run(world, "--manifest", str(manifest), "--record-all",
                "--gates-root", str(tmp_path / "gates")) == 1
    err = capsys.readouterr().err
    assert "manifest entry bad" in err and message in err


def test_record_all_takes_the_policy_from_the_manifest(world, capsys, tmp_path):
    manifest = _write_manifest(tmp_path / "manifest.toml", ("baseline", "model", []))
    assert _run(world, "--manifest", str(manifest), "--record-all",
                "--gates-root", str(tmp_path / "gates"),
                "--inputs-policy", "drop_promoted") == 1
    assert "--inputs-policy" in capsys.readouterr().err


def test_record_all_calibration_entry_records_p4_per_position(world, capsys, tmp_path):
    gates_root = tmp_path / "gates"
    manifest = _write_manifest(tmp_path / "manifest.toml", ("baseline", "model", []),
                               ("p4", "calibration", []))
    assert _run(world, "--manifest", str(manifest), "--record-all",
                "--gates-root", str(gates_root)) == 0
    record = _records(gates_root, "p4")["p4"]
    assert record["kind"] == "calibration"
    assert record["verdict"] is None and record["reasons"] == []
    p4 = record["comparison"]["p4"]
    assert set(p4) == {"DEF", "MID"}
    for position in p4.values():
        assert position["n"] == 2
        assert position["base_rate"] == "leave-one-round-out"
        assert set(position) >= {"p4_brier", "base_rate_brier", "skill", "reliability"}
        assert len(position["reliability"]) == 5
    out = capsys.readouterr().out
    assert any(line.startswith("p4: calibration — ") and "MID n 2" in line
               for line in out.splitlines())
    assert "combined:" in out


def test_record_all_refuses_a_calibration_entry_with_arguments(world, capsys, tmp_path):
    manifest = _write_manifest(tmp_path / "manifest.toml", ("baseline", "model", []),
                               ("p4", "calibration", ["--set", "blend_k=300"]))
    assert _run(world, "--manifest", str(manifest), "--record-all",
                "--gates-root", str(tmp_path / "gates")) == 1
    err = capsys.readouterr().err
    assert "manifest entry p4" in err and "no arguments" in err


def test_json_comparison_carries_p4(world, capsys):
    assert _run(world, "--set", "blend_k=300", "--format", "json") == 0
    document = json.loads(capsys.readouterr().out)
    assert set(document["comparison"]["p4"]) == {"DEF", "MID"}
