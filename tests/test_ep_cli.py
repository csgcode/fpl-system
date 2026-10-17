"""CLI tests for `fpl ep`: argument wiring, default paths, the written
prediction file, printed output and refusals — over cached snapshots only."""

from __future__ import annotations

import json

import pytest

from fpl.__main__ import main
from fpl.store import SnapshotStore
from tests.factories import (
    bootstrap_payload,
    element_summary_payload,
    event_payload,
    match_record_payload,
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
        "--analysis-root", str(analysis_root),
        "--decisions-root", str(analysis_root.parent / "decisions"), *extra,
    ])


def decide(analysis_root):
    final = analysis_root.parent / "decisions" / f"gw{GW}" / "final.md"
    final.parent.mkdir(parents=True)
    final.write_text("# Final\n", encoding="utf-8")


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


def test_ep_allow_missing_ids_scores_the_rest_and_warns(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document(players=[
        {"id": 2, "name": "Beta", "p_start": 0.5, "uncertainty": "MED"}
    ]))
    assert run(data_root, analysis_root, "--allow-missing-ids", "1") == 0
    err = capsys.readouterr().err
    written = json.loads((analysis_root / f"gw{GW}" / "players-MID.json").read_text())
    assert [row["id"] for row in written] == [2]
    assert "WARNING" in err and "Alpha" in err


def seed_with_current_minutes(tmp_path):
    data_root, analysis_root = seed(tmp_path)
    SnapshotStore(data_root).save(
        GW, "players/summary-1",
        element_summary_payload(
            history_past=[past_season_payload(minutes=2700, expected_goals="9.0")],
            history=[match_record_payload(round=1, minutes=90, expected_goals="0.9")],
        ),
        "seed://test",
    )
    return data_root, analysis_root


def test_ep_prior_weight_forces_every_row_and_writes_only_to_out(tmp_path, capsys):
    data_root, analysis_root = seed_with_current_minutes(tmp_path)
    write_inputs(analysis_root, inputs_document(players=[
        {"id": 1, "name": "Alpha", "p_start": 0.9, "uncertainty": "LOW",
         "overrides": {"prior_weight": 0.2}, "reason": "analyst blend"},
        {"id": 2, "name": "Beta", "p_start": 0.5, "uncertainty": "MED"},
    ]))
    target = tmp_path / "scratch" / "players-MID-prior.json"
    assert run(data_root, analysis_root, "--prior-weight", "1.0", "--out", str(target)) == 0
    written = json.loads(target.read_text())
    assert {row["id"] for row in written} == {1, 2}
    assert all(row["rates"]["prior_weight"] == 1.0 for row in written)
    assert not (analysis_root / f"gw{GW}" / "players-MID.json").exists()
    assert "players-MID-prior.json" in capsys.readouterr().out


def test_ep_without_prior_weight_keeps_the_computed_blend(tmp_path):
    data_root, analysis_root = seed_with_current_minutes(tmp_path)
    write_inputs(analysis_root, inputs_document())
    assert run(data_root, analysis_root) == 0
    written = json.loads((analysis_root / f"gw{GW}" / "players-MID.json").read_text())
    assert written[0]["rates"]["prior_weight"] < 1.0


@pytest.mark.parametrize("weight", ["1.5", "-0.1", "nan", "abc"])
def test_ep_prior_weight_outside_zero_to_one_is_refused(tmp_path, weight, capsys):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document())
    with pytest.raises(SystemExit) as exc_info:
        run(data_root, analysis_root, "--prior-weight", weight, "--out", str(tmp_path / "x.json"))
    assert exc_info.value.code == 2
    assert "prior weight" in capsys.readouterr().err
    assert not (tmp_path / "x.json").exists()


def test_ep_prior_weight_without_out_is_refused(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document())
    assert run(data_root, analysis_root, "--prior-weight", "1.0") == 1
    assert "--prior-weight requires --out" in capsys.readouterr().err
    assert not (analysis_root / f"gw{GW}" / "players-MID.json").exists()


def test_ep_prior_weight_with_check_is_refused(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document())
    assert run(
        data_root, analysis_root, "--check", "--prior-weight", "1.0",
        "--out", str(tmp_path / "x.json"),
    ) == 1
    assert "--prior-weight cannot be combined with --check" in capsys.readouterr().err
    assert not (tmp_path / "x.json").exists()


# --- a decided gameweek -----------------------------------------------------

def test_ep_refuses_the_canonical_file_once_final_md_exists(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document())
    decide(analysis_root)

    assert run(data_root, analysis_root) == 1

    err = capsys.readouterr().err
    assert "final.md" in err and "--out" in err
    assert not (analysis_root / f"gw{GW}" / "players-MID.json").exists()


def test_ep_out_still_works_on_a_decided_gameweek(tmp_path):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document())
    decide(analysis_root)

    assert run(data_root, analysis_root, "--out", str(tmp_path / "x.json")) == 0
    assert run(data_root, analysis_root, "--prior-weight", "1.0",
               "--out", str(tmp_path / "p.json")) == 0
    assert not (analysis_root / f"gw{GW}" / "players-MID.json").exists()


def test_ep_writes_before_final_md_exists(tmp_path):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document())

    assert run(data_root, analysis_root) == 0
    assert (analysis_root / f"gw{GW}" / "players-MID.json").is_file()


# --- --history-from store ------------------------------------------------------


def store_world(tmp_path):
    """A synced season (rounds 1–2, gw3 open) with gw3 inputs and fixtures for
    its three clubs; element 1 is the MID judged."""
    from fpl.season_store import sync
    from tests.test_season_store import Season

    raw, db = tmp_path / "raw", tmp_path / "store" / "s.sqlite"
    Season().write(raw)
    sync(raw, db)
    analysis_root = tmp_path / "analysis"
    (analysis_root / f"gw{GW}").mkdir(parents=True)
    clubs = ("C1", "C2", "C3")
    document = {
        "schema_version": 1, "gw": GW, "base_lambda": {"home": 1.54, "away": 1.33},
        "ratings": {c: {"att": 1.0, "defw": 1.0} for c in clubs},
        "fixtures": [
            {"club": c, "gw": g, "opp": "C2" if c != "C2" else "C1", "venue": "H",
             "lambda_att": 1.5, "lambda_def": 1.0, "p_cs": 0.3}
            for c in clubs for g in range(GW, GW + 6)
        ],
    }
    (analysis_root / f"gw{GW}" / "fixtures.json").write_text(json.dumps(document))
    write_inputs(analysis_root, inputs_document(
        [{"id": 1, "name": "P1", "p_start": 0.9, "uncertainty": "LOW", "notes": "starter"}]))
    return raw, db, analysis_root


def test_ep_from_store_equals_ep_from_summaries(tmp_path):
    raw, db, analysis_root = store_world(tmp_path)
    outputs = {}
    for source in ("store", "summaries"):
        out = tmp_path / f"{source}.json"
        assert run(raw, analysis_root, "--history-from", source, "--store", str(db),
                   "--out", str(out)) == 0
        outputs[source] = out.read_bytes()

    assert outputs["store"] == outputs["summaries"]
    (row,) = json.loads(outputs["store"])
    assert row["id"] == 1 and row["rates"]["prior_weight"] < 1


def test_ep_check_reads_the_store_too(tmp_path, capsys):
    raw, db, analysis_root = store_world(tmp_path)
    assert run(raw, analysis_root, "--check", "--history-from", "store", "--store",
               str(db)) == 0
    assert "1 players scored, 0 without cached summary" in capsys.readouterr().out


def test_ep_from_a_store_behind_the_raw_refuses_naming_the_sync(tmp_path, capsys):
    raw, db, analysis_root = store_world(tmp_path)
    SnapshotStore(raw).save(GW, "players/summary-9", element_summary_payload(), "seed://test")

    assert run(raw, analysis_root, "--history-from", "store", "--store", str(db),
               "--out", str(tmp_path / "x.json")) == 1
    err = capsys.readouterr().err
    assert "summary-9.json not ingested" in err and f"store sync --gw {GW}" in err
    assert not (tmp_path / "x.json").exists()


def test_ep_reads_summaries_by_default_and_never_opens_the_store(tmp_path):
    raw, _, analysis_root = store_world(tmp_path)
    out = tmp_path / "default.json"
    assert run(raw, analysis_root, "--store", str(tmp_path / "absent.sqlite"),
               "--out", str(out)) == 0
