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
        "reasons": [] if comparison is None else comparison.get("reasons", []),
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


P4_CALIBRATION = _record("p4", kind="calibration", comparison={"p4": {
    "MID": {"n": 1688, "p4_brier": 0.18, "base_rate_brier": 0.2, "base_rate": "leave-one-round-out",
            "skill": 0.1, "reliability": [],
            "starters": {"n": 900, "p4_brier": 0.21, "base_rate_brier": 0.22,
                         "base_rate": "leave-one-round-out", "skill": 0.012,
                         "reliability": [], "starters": None}},
    "DEF": {"n": 1500, "p4_brier": 0.25, "base_rate_brier": 0.2,
            "base_rate": "leave-one-round-out", "skill": -0.25, "reliability": []},
}})


def test_calibration_record_summarises_and_renders_p4_skill(tmp_path, capsys):
    root = tmp_path / "gates"
    root.mkdir()
    (root / "p4.json").write_text(json.dumps(P4_CALIBRATION), encoding="utf-8")
    assert main(["gates", "--gw", "8", "--summary", "--gates-root", str(root)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == ("p4: calibration — p4 skill MID n 1688 Brier 0.180 v base 0.200 "
                        "skill +0.100 (starters n 900 Brier 0.210 v base 0.220 skill +0.0120); "
                        "DEF n 1500 Brier 0.250 v base 0.200 skill −0.250")
    assert lines[1].strip() == "calibration"
    [row] = gates.render(gates.load_records(root)).splitlines()[2:]
    assert row.startswith("| p4 | calibration |")
    assert "p4 skill MID +0.100 (starters +0.0120), DEF −0.250" in row


def test_calibration_record_with_no_likely_starters_says_none(tmp_path, capsys):
    record = json.loads(json.dumps(P4_CALIBRATION))
    record["comparison"]["p4"]["DEF"]["starters"] = None
    root = tmp_path / "gates"
    root.mkdir()
    (root / "p4.json").write_text(json.dumps(record), encoding="utf-8")
    assert main(["gates", "--gw", "8", "--summary", "--gates-root", str(root)]) == 0
    assert "DEF n 1500 Brier 0.250 v base 0.200 skill −0.250 (starters none)" in (
        capsys.readouterr().out)
    [row] = gates.render(gates.load_records(root)).splitlines()[2:]
    assert "DEF −0.250 (starters none)" in row


def _policy(verdict: str) -> dict:
    reasons = [] if verdict == "PASS" else ["effect: ΔMAE +0.0043 > −0.01"]
    return _record(
        "drop-promoted", kind="policy", ship={}, verdict=verdict,
        comparison=_comparison(-0.012, (-0.02, -0.004), (0.18, 0.16), (5, 5), reasons),
        slice_verdict="PASS", hypothesis="supported")


@pytest.mark.parametrize("verdict, word", [("PASS", "passed (a policy never ships)"),
                                           ("FAIL", "FAIL policy")])
def test_policy_headline_never_reads_as_shipping(verdict, word):
    [headline, _] = gates.summary_lines([gates.GateRecord.model_validate(_policy(verdict))])
    assert headline == (f"drop-promoted: {word} — ΔMAE −0.0120 [CI −0.020, −0.004], "
                        "bias 0.18→0.16, wins 5/5")


def test_render_shows_slice_verdict_and_hypothesis():
    policy = gates.GateRecord.model_validate(_policy("PASS"))
    plain = gates.GateRecord.model_validate(PASSING)
    [policy_row, plain_row] = gates.render([policy, plain]).splitlines()[2:]
    cells = [cell.strip() for cell in policy_row.split("|")[1:-1]]
    assert cells[gates.RENDER_HEADER.index("Verdict")] == (
        "PASS · slice PASS · hypothesis supported")
    cells = [cell.strip() for cell in plain_row.split("|")[1:-1]]
    assert cells[gates.RENDER_HEADER.index("Verdict")] == "PASS"


def _window(window: int, n: int, slope: float, ci: tuple[float, float], r: float) -> dict:
    return {"window": window, "min_starts": min(2, window), "target_rounds": [4, 5, 6, 7],
            "n": n, "slope": slope, "intercept": 0.1, "se_ols": 0.05, "se_cluster": 0.06,
            "ci_ols": list(ci), "ci_cluster": list(ci), "r": r, "significant": False,
            "by_position": {}}


PERSISTENCE = _record(
    "persistence", kind="persistence", baseline_config=None,
    decision_commits=None, predictions_commits={"3": None},
    comparison={"significant": False, "windows": [
        _window(3, 711, 0.034, (-0.095, 0.162), 0.020),
        _window(1, 1098, 0.007, (-0.046, 0.060), 0.007),
        _window(2, 805, 0.018, (-0.083, 0.119), 0.013)]},
    reasons=["ci: clustered lower −0.095 ≤ 0"], significant=False)


def test_persistence_record_summarises_and_renders_its_windows(tmp_path, capsys):
    root = tmp_path / "gates"
    root.mkdir()
    (root / "persistence.json").write_text(json.dumps(PERSISTENCE), encoding="utf-8")
    assert main(["gates", "--gw", "8", "--summary", "--gates-root", str(root)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines == [
        "persistence: not significant — window 3, min starts 2: n 711, "
        "slope +0.034 [CI −0.095, +0.162] (cluster), r +0.020",
        "  no form term: clustered lower −0.095 ≤ 0 (ci)",
    ]
    [row] = gates.render(gates.load_records(root)).splitlines()[2:]
    assert row == (
        "| persistence | persistence | 3-7 | — | — | — | — | — | — | not significant | "
        "window 3: n 711, slope +0.034 [−0.095, +0.162], r +0.020; "
        "window 1: n 1098, slope +0.007 [−0.046, +0.060], r +0.007; "
        "window 2: n 805, slope +0.018 [−0.083, +0.119], r +0.013 |")


def test_significant_persistence_record_sends_the_form_term_to_its_gate(tmp_path, capsys):
    record = json.loads(json.dumps(PERSISTENCE))
    record["significant"] = record["comparison"]["significant"] = True
    record["reasons"] = []
    root = tmp_path / "gates"
    root.mkdir()
    (root / "persistence.json").write_text(json.dumps(record), encoding="utf-8")
    assert main(["gates", "--gw", "8", "--summary", "--gates-root", str(root)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("persistence: significant — window 3")
    assert lines[1] == "  significant: the form term goes to its gate"


SLICE_GATE = {"name": "promoted", "n": 319, "verdict": "FAIL",
              "reasons": ["effect: ΔMAE +0.0141 > −0.01"], "pooled_positions": True,
              "delta_mae": 0.0141, "ci": [-0.0029, 0.031], "round_wins": [1, 5],
              "baseline_bias": 0.1366, "variant_bias": 0.0768}
SLICE_TEXT = "slice promoted FAIL: n 319, ΔMAE +0.0141 [CI −0.003, +0.031], bias +0.137→+0.077"


def _sliced_policy() -> dict:
    record = _policy("FAIL")
    record["comparison"]["slice_gate"] = SLICE_GATE
    record["slice_verdict"] = "FAIL"
    record["hypothesis"] = "not supported"
    return record


def test_summary_shows_slice_delta_ci_and_bias():
    [_, status] = gates.summary_lines([gates.GateRecord.model_validate(_sliced_policy())])
    assert status.strip() == ("rejected: ΔMAE +0.0043 > −0.01 (effect) · "
                              f"{SLICE_TEXT} · hypothesis not supported")


def test_render_shows_slice_delta_ci_and_bias():
    [row] = gates.render([gates.GateRecord.model_validate(_sliced_policy())]).splitlines()[2:]
    cells = [cell.strip() for cell in row.split("|")[1:-1]]
    assert cells[gates.RENDER_HEADER.index("Verdict")] == (
        f"FAIL · {SLICE_TEXT} · hypothesis not supported")


def test_an_empty_slice_shows_its_verdict_without_statistics():
    record = _sliced_policy()
    record["comparison"]["slice_gate"] = {
        **SLICE_GATE, "n": 0, "verdict": "n/a", "reasons": [], "delta_mae": None, "ci": None,
        "round_wins": None, "baseline_bias": None, "variant_bias": None}
    record["slice_verdict"] = "n/a"
    [_, status] = gates.summary_lines([gates.GateRecord.model_validate(record)])
    assert "· slice promoted n/a: n 0 ·" in status


def _ship_cell(record: dict) -> str:
    [row] = gates.render([gates.GateRecord.model_validate(record)]).splitlines()[2:]
    return [cell.strip() for cell in row.split("|")[1:-1]][gates.RENDER_HEADER.index("Ship value")]


def test_render_ship_value_is_blank_for_a_failed_gate():
    assert _ship_cell(PASSING) == "blend_k=450"
    assert _ship_cell(FAILING) == "—"


def test_render_combined_with_no_passing_entries_ships_the_baseline():
    combined = _record("combined", kind="combined", ship={},
                       shipped_config=asdict(DEFAULT_CONFIG), reverted=[])
    assert _ship_cell(combined) == "ships baseline (no passing entries)"


def test_write_record_archives_a_combined_record_only_when_its_content_changes(tmp_path):
    root = tmp_path / "gates"
    combined = _record("combined", kind="combined", ship={},
                       shipped_config=asdict(DEFAULT_CONFIG), reverted=[])
    gates.write_record(root, combined, force=True, archive_unchanged=False)
    rerun = {**combined, "code": {"head": "abc", "dirty": False},
             "recorded_at": "2026-10-22T09:00:00+00:00"}
    gates.write_record(root, rerun, force=True, archive_unchanged=False)
    assert not (root / gates.ARCHIVE_DIR).exists()
    assert gates.read_record(root, "combined").code == {"head": "abc", "dirty": False}

    changed = {**rerun, "reverted": ["k450"]}
    gates.write_record(root, changed, force=True, archive_unchanged=False)
    [archived] = (root / gates.ARCHIVE_DIR).glob("combined.*.json")
    assert json.loads(archived.read_text())["code"] == {"head": "abc", "dirty": False}


def test_render_shows_a_tiny_negative_starter_skill_with_its_sign():
    record = json.loads(json.dumps(P4_CALIBRATION))
    record["comparison"]["p4"]["MID"]["starters"]["skill"] = -0.0001
    [row] = gates.render([gates.GateRecord.model_validate(record)]).splitlines()[2:]
    assert "MID +0.100 (starters −0.0001)" in row


@pytest.mark.parametrize("kind", ["model", "policy", "calibration", "combined"])
def test_a_record_judging_a_config_needs_its_baseline_config(kind):
    record = _record("x", kind=kind, baseline_config=None)
    with pytest.raises(ValueError, match="baseline_config"):
        gates.GateRecord.model_validate(record)


def test_only_a_persistence_record_carries_significant():
    with pytest.raises(ValueError, match="significant"):
        gates.GateRecord.model_validate(_record("x", significant=False))
    gates.GateRecord.model_validate(PERSISTENCE)


def test_predictions_commits_belong_to_persistence_and_decision_commits_to_the_rest():
    with pytest.raises(ValueError, match="predictions_commits"):
        gates.GateRecord.model_validate(_record("x", predictions_commits={"3": None}))
    with pytest.raises(ValueError, match="decision_commits"):
        gates.GateRecord.model_validate({**_record("x"), "decision_commits": None})


def test_a_combined_record_run_from_another_checkout_is_not_archived(tmp_path):
    root = tmp_path / "gates"
    combined = _record("combined", kind="combined", ship={},
                       shipped_config=asdict(DEFAULT_CONFIG), reverted=[])
    combined["data"]["actuals"] = {"3": {"path": "/a/raw/gw4/event-live-e3.json",
                                         "sha256": "aa"}}
    gates.write_record(root, combined, force=True, archive_unchanged=False)
    elsewhere = json.loads(json.dumps(combined))
    elsewhere["data"].update(data_root="/b/raw", analysis_root="/b/analysis",
                             decisions_root="/b/decisions", retro_root="/b/retro")
    elsewhere["data"]["actuals"]["3"]["path"] = "/b/raw/gw4/event-live-e3.json"
    gates.write_record(root, elsewhere, force=True, archive_unchanged=False)
    assert not (root / gates.ARCHIVE_DIR).exists()
    assert gates.read_record(root, "combined").data["data_root"] == "/b/raw"

    other_snapshot = json.loads(json.dumps(elsewhere))
    other_snapshot["data"]["actuals"]["3"]["sha256"] = "bb"
    gates.write_record(root, other_snapshot, force=True, archive_unchanged=False)
    assert len(list((root / gates.ARCHIVE_DIR).glob("combined.*.json"))) == 1


def test_summary_shows_a_tiny_negative_starter_skill_with_its_sign(tmp_path, capsys):
    record = json.loads(json.dumps(P4_CALIBRATION))
    record["comparison"]["p4"]["MID"]["starters"]["skill"] = -0.0001
    root = tmp_path / "gates"
    root.mkdir()
    (root / "p4.json").write_text(json.dumps(record), encoding="utf-8")
    assert main(["gates", "--gw", "8", "--summary", "--gates-root", str(root)]) == 0
    assert "(starters n 900 Brier 0.210 v base 0.220 skill −0.0001)" in capsys.readouterr().out


def test_new_records_are_written_at_schema_version_2_and_version_1_still_reads():
    assert gates.SCHEMA_VERSION == 2
    gates.GateRecord.model_validate({**_record("x"), "schema_version": 2})
    gates.GateRecord.model_validate({**_record("x"), "schema_version": 1})
    with pytest.raises(ValueError, match="schema_version"):
        gates.GateRecord.model_validate({**_record("x"), "schema_version": 3})


def _persistence(**changes) -> dict:
    return {**PERSISTENCE, "schema_version": 2, **changes}


def test_a_persistence_record_rejects_decision_commits():
    with pytest.raises(ValueError, match="decision_commits"):
        gates.GateRecord.model_validate(_persistence(decision_commits={"3": None}))


def test_a_persistence_record_requires_predictions_commits():
    with pytest.raises(ValueError, match="predictions_commits"):
        gates.GateRecord.model_validate(_persistence(predictions_commits=None))
    record = _persistence()
    del record["predictions_commits"]
    with pytest.raises(ValueError, match="predictions_commits"):
        gates.GateRecord.model_validate(record)


def test_a_persistence_record_judges_no_baseline_config():
    with pytest.raises(ValueError, match="baseline_config"):
        gates.GateRecord.model_validate(_persistence(baseline_config=asdict(DEFAULT_CONFIG)))


def test_a_version_1_persistence_record_may_carry_decision_commits():
    legacy = {**PERSISTENCE, "schema_version": 1, "decision_commits": {"3": None}}
    del legacy["predictions_commits"]
    gates.GateRecord.model_validate(legacy)
