"""CLI tests for `fpl ep`: argument wiring, default paths, the written
prediction file, printed output and refusals — over cached snapshots only."""

from __future__ import annotations

import json

from fpl.__main__ import main
from fpl.store import SnapshotStore
from tests.factories import (
    bootstrap_payload,
    element_summary_payload,
    event_payload,
    past_season_payload,
    player_payload,
    team_payload,
)

GW = 3


def seed(tmp_path, *, with_summary=True):
    data_root = tmp_path / "raw"
    store = SnapshotStore(data_root)
    players = [
        player_payload(id=1, web_name="Alpha", team=1, element_type=3, now_cost=60),
        player_payload(id=2, web_name="Beta", team=2, element_type=3, now_cost=45),
    ]
    teams = [team_payload(id=1, short_name="TST"), team_payload(id=2, short_name="OPP")]
    store.save(
        GW, "bootstrap",
        bootstrap_payload(elements=players, teams=teams, events=[event_payload(id=GW, is_next=True)]),
        "seed://test",
    )
    if with_summary:
        store.save(
            GW, "players/summary-1",
            element_summary_payload(history_past=[past_season_payload(minutes=2700, expected_goals="9.0")]),
            "seed://test",
        )
    analysis_root = tmp_path / "analysis"
    analysis_dir = analysis_root / f"gw{GW}"
    analysis_dir.mkdir(parents=True)
    (analysis_dir / "fixtures.json").write_text(json.dumps(fixtures_document()), encoding="utf-8")
    return data_root, analysis_root


def fixtures_document():
    return {
        "schema_version": 1,
        "gw": GW,
        "base_lambda": {"home": 1.54, "away": 1.33},
        "ratings": {"TST": {"att": 1.0, "defw": 1.0}, "OPP": {"att": 1.0, "defw": 1.0}},
        "fixtures": [
            {"club": "TST", "gw": g, "opp": "OPP", "venue": "H", "lambda_att": 1.5,
             "lambda_def": 1.0, "p_cs": 0.3}
            for g in range(GW, GW + 6)
        ],
    }


def inputs_document(players=None, position="MID"):
    return {
        "schema_version": 1,
        "gw": GW,
        "position": position,
        "players": players if players is not None else [
            {"id": 1, "name": "Alpha", "p_start": 0.9, "uncertainty": "LOW", "notes": "starter"}
        ],
    }


def write_inputs(analysis_root, document, position="MID"):
    path = analysis_root / f"gw{GW}" / f"inputs-{position}.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def run(data_root, analysis_root, *extra):
    return main([
        "--data-root", str(data_root), "ep", "--gw", str(GW), "--position", "MID",
        "--analysis-root", str(analysis_root), *extra,
    ])


def test_ep_writes_predictions_to_the_default_path_and_prints_a_table(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document())
    assert run(data_root, analysis_root) == 0
    out = capsys.readouterr().out
    written = json.loads((analysis_root / f"gw{GW}" / "players-MID.json").read_text())
    assert [row["id"] for row in written] == [1]
    assert written[0]["p_start"] == 0.9
    assert len(written[0]["ep_gw"]) == 6
    assert written[0]["rates"]["prior_source"] == "history_past"
    assert set(written[0]["terms"]) >= {"attack", "defcon", "clean_sheet"}
    text = (analysis_root / f"gw{GW}" / "players-MID.json").read_text()
    assert text.splitlines()[0] == "[" and text.count("\n") == len(written) + 2
    assert '"name": "Alpha"' in text.splitlines()[1]
    assert "gw3 MID: 1 scored, 1 not scored" in out
    assert "Alpha" in out
    assert "wrote" in out and "players-MID.json" in out
    assert "missing summaries" not in out


def test_ep_lists_missing_summaries_with_the_fetch_command(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path, with_summary=False)
    write_inputs(analysis_root, inputs_document())
    assert run(data_root, analysis_root) == 0
    captured = capsys.readouterr()
    assert "missing summaries (1)" in captured.err
    assert "summaries --gw 3 --ids 1" in captured.err
    assert "1 without cached summary" in captured.out


def test_ep_json_format_prints_the_document_and_honours_out(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document())
    target = tmp_path / "elsewhere" / "mid.json"
    assert run(data_root, analysis_root, "--format", "json", "--out", str(target)) == 0
    out = capsys.readouterr().out
    printed = json.loads(out[: out.rindex("]") + 1])
    assert printed[0]["name"] == "Alpha"
    assert target.is_file()
    assert not (analysis_root / f"gw{GW}" / "players-MID.json").exists()


def test_ep_refuses_an_unknown_key_with_the_row_id(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    document = inputs_document()
    document["players"][0]["p_strat"] = 0.5
    write_inputs(analysis_root, document)
    assert run(data_root, analysis_root) == 1
    err = capsys.readouterr().err
    assert "row 0 (id 1)" in err and "p_strat" in err
    assert not (analysis_root / f"gw{GW}" / "players-MID.json").exists()


def test_ep_refuses_a_document_for_another_position(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document(position="FWD"))
    assert run(data_root, analysis_root) == 1
    assert "FWD, not --position MID" in capsys.readouterr().err


def test_ep_refuses_when_inputs_or_fixtures_are_missing(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    assert run(data_root, analysis_root) == 1
    assert "inputs-MID.json" in capsys.readouterr().err
    write_inputs(analysis_root, inputs_document())
    (analysis_root / f"gw{GW}" / "fixtures.json").unlink()
    assert run(data_root, analysis_root) == 1
    assert "fixtures.json" in capsys.readouterr().err


def test_ep_refuses_the_coverage_gap_by_name(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document(players=[
        {"id": 2, "name": "Beta", "p_start": 0.5, "uncertainty": "MED"}
    ]))
    assert run(data_root, analysis_root) == 1
    err = capsys.readouterr().err
    assert "Alpha" in err and "£6.0" in err


def test_ep_check_validates_fixtures_without_inputs_and_writes_nothing(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    assert main([
        "--data-root", str(data_root), "ep", "--gw", str(GW), "--check",
        "--analysis-root", str(analysis_root),
    ]) == 0
    out = capsys.readouterr().out
    assert "fixtures.json OK: 2 clubs rated, 6 rows in gw3–8" in out
    assert "blanks: OPP gw3" in out
    assert not (analysis_root / f"gw{GW}" / "players-MID.json").exists()


def test_ep_check_refuses_an_unknown_club(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    document = fixtures_document()
    document["fixtures"][0]["opp"] = "XYZ"
    (analysis_root / f"gw{GW}" / "fixtures.json").write_text(json.dumps(document), encoding="utf-8")
    assert main([
        "--data-root", str(data_root), "ep", "--gw", str(GW), "--check",
        "--analysis-root", str(analysis_root),
    ]) == 1
    assert "XYZ" in capsys.readouterr().err


def test_ep_check_with_position_validates_inputs_too(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document())
    assert run(data_root, analysis_root, "--check") == 0
    out = capsys.readouterr().out
    assert "inputs-MID.json OK: 1 players scored" in out
    assert not (analysis_root / f"gw{GW}" / "players-MID.json").exists()


def test_ep_without_position_or_check_is_refused(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    assert main([
        "--data-root", str(data_root), "ep", "--gw", str(GW), "--analysis-root", str(analysis_root),
    ]) == 1
    assert "--position is required" in capsys.readouterr().err
