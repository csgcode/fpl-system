"""CLI tests for `fpl ep`: argument wiring, default paths, the written
prediction file, printed output and refusals — over cached snapshots only."""

from __future__ import annotations

import json

import pytest

from fpl.__main__ import main
from fpl.ep import DEFAULT_CONFIG
from fpl.models import Position
from fpl.store import SnapshotStore
from tests.factories import (
    bootstrap_payload,
    element_summary_payload,
    event_live_payload,
    event_payload,
    fixture_payload,
    match_record_payload,
    past_season_payload,
    player_payload,
    priors_doc,
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


def test_documents_and_table_carry_the_model_digest(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document())
    assert run(data_root, analysis_root) == 0
    out = capsys.readouterr().out
    written = json.loads((analysis_root / f"gw{GW}" / "players-MID.json").read_text())
    assert written and all(row["model"] == DEFAULT_CONFIG.digest() for row in written)
    assert out.splitlines()[1] == f"model {DEFAULT_CONFIG.digest()}"


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


def seed_with_returns(tmp_path):
    data_root, analysis_root = seed(tmp_path)
    SnapshotStore(data_root).save(
        GW, "players/summary-1",
        element_summary_payload(
            history_past=[past_season_payload(minutes=2700, expected_goals="9.0")],
            history=[
                match_record_payload(round=1, minutes=90, total_points=6),
                match_record_payload(round=2, minutes=90, total_points=2),
            ],
        ),
        "seed://test",
    )
    return data_root, analysis_root


def alpha_line(out):
    return next(line for line in out.splitlines() if " Alpha " in line)


def header_line(out):
    return next(line for line in out.splitlines() if line.lstrip().startswith("id "))


@pytest.mark.parametrize("calibrated", [True, False])
def test_ep_table_and_file_carry_p4_and_ret5(tmp_path, capsys, monkeypatch, calibrated):
    monkeypatch.setattr(
        "fpl.objective.P4_CALIBRATED", frozenset({Position.MID}) if calibrated else frozenset()
    )
    data_root, analysis_root = seed_with_returns(tmp_path)
    write_inputs(analysis_root, inputs_document(players=[
        {"id": 1, "name": "Alpha", "p_start": 0.9, "uncertainty": "LOW"},
        {"id": 2, "name": "Beta", "p_start": 0.5, "uncertainty": "MED"},
    ]))
    assert run(data_root, analysis_root) == 0
    out = capsys.readouterr().out
    written = {row["id"]: row for row in json.loads(
        (analysis_root / f"gw{GW}" / "players-MID.json").read_text()
    )}
    assert written[1]["returns5"] == [1, 2]
    assert written[2]["returns5"] == [0, 0]
    header = header_line(out)
    assert " p4 " in header and "ret5" in header
    assert header.index("ep/£m") < header.index(" p4 ") < header.index("ret5")
    p4_text = f"{written[1]['p4_gw'][0]:.2f}" if calibrated else "-"
    fields = alpha_line(out).split()
    ep_m = fields.index(f"{written[1]['ep_per_million']:.2f}")
    assert fields[ep_m + 1 : ep_m + 3] == [p4_text, "1/2"]


ALPHA_SHARE_DETAIL = "xG EP>club (implied 0.40, season 0.10, 3 starts)"


def seed_share_check(tmp_path):
    """Rounds 1–2 played (round 2 a double): TST took 1.0 xG a match, Alpha
    0.1 of it over 3 starts. His overrides put the EP at 0.40 of club xG for
    xG and 0.10 for xA, so only xG is flagged."""
    data_root, analysis_root = seed(tmp_path)
    store = SnapshotStore(data_root)
    bootstrap = store.load(GW, "bootstrap")
    bootstrap["elements"].append(
        player_payload(id=3, web_name="Gamma", team=1, element_type=4, now_cost=70)
    )
    store.save(GW, "bootstrap", bootstrap, "seed://test")
    played = [(101, 1, True), (102, 2, False), (103, 2, True)]
    store.save(GW, "fixtures", [
        fixture_payload(id=fid, event=rnd, team_h=1 if home else 2, team_a=2 if home else 1,
                        finished=True)
        for fid, rnd, home in played
    ], "seed://test")

    def history(xg):
        return [match_record_payload(fixture=fid, round=rnd, was_home=home, starts=1,
                                     expected_goals=xg, expected_assists="0.10")
                for fid, rnd, home in played]

    store.save(GW, "players/summary-1", element_summary_payload(
        history_past=[past_season_payload(minutes=2700, expected_goals="9.0")],
        history=history("0.10")), "seed://test")
    store.save(GW, "players/summary-3", element_summary_payload(history=history("0.90")),
               "seed://test")
    store.save(2, "event-live-e1", event_live_payload([]), "seed://test")
    store.save(3, "event-live-e2", event_live_payload([]), "seed://test")
    (analysis_root / "club-priors.json").write_text(
        json.dumps(priors_doc({"TST": (1.0, 1.0, False), "OPP": (1.0, 1.0, False)})),
        encoding="utf-8",
    )
    write_inputs(analysis_root, inputs_document(players=[{
        "id": 1, "name": "Alpha", "p_start": 0.9, "uncertainty": "LOW",
        "overrides": {"xg90": 0.574, "xa90": 0.1435, "minutes_per_start": 90},
        "reason": "synthetic share test",
    }]))
    return data_root, analysis_root


def share_lines(err):
    return [line for line in err.splitlines() if "share check" in line]


def test_ep_flags_a_share_disagreement(tmp_path, capsys):
    data_root, analysis_root = seed_share_check(tmp_path)
    assert run(data_root, analysis_root) == 0
    captured = capsys.readouterr()
    written = json.loads((analysis_root / f"gw{GW}" / "players-MID.json").read_text())
    assert written[0]["share_flag"] == ALPHA_SHARE_DETAIL
    header = header_line(captured.out)
    assert header.index("crd") < header.index("share") < header.index("fixtures")
    assert "xG EP>club" in alpha_line(captured.out)
    assert share_lines(captured.err) == ["share check: 1 flagged (ids 1)"]


def test_ep_share_detail_names_each_flagged_row(tmp_path, capsys):
    data_root, analysis_root = seed_share_check(tmp_path)
    assert run(data_root, analysis_root, "--share-detail") == 0
    assert share_lines(capsys.readouterr().err) == [
        "share check: 1 flagged (ids 1)",
        f"share check: id 1 Alpha {ALPHA_SHARE_DETAIL}",
    ]


def test_ep_json_format_prints_the_share_flag(tmp_path, capsys):
    data_root, analysis_root = seed_share_check(tmp_path)
    assert run(data_root, analysis_root, "--format", "json") == 0
    out = capsys.readouterr().out
    assert json.loads(out[: out.rindex("]") + 1])[0]["share_flag"] == ALPHA_SHARE_DETAIL


def test_ep_unflagged_rows_carry_a_null_share_flag(tmp_path, capsys):
    data_root, analysis_root = seed_share_check(tmp_path)
    write_inputs(analysis_root, inputs_document())
    assert run(data_root, analysis_root) == 0
    captured = capsys.readouterr()
    written = json.loads((analysis_root / f"gw{GW}" / "players-MID.json").read_text())
    assert [row["share_flag"] for row in written] == [None]
    assert share_lines(captured.err) == ["share check: 0 flagged"]


def test_ep_share_check_leaves_the_ep_fields_unchanged(tmp_path):
    data_root, analysis_root = seed_share_check(tmp_path)
    assert run(data_root, analysis_root) == 0
    flagged = json.loads((analysis_root / f"gw{GW}" / "players-MID.json").read_text())
    (analysis_root / "club-priors.json").unlink()
    assert run(data_root, analysis_root) == 0
    skipped = json.loads((analysis_root / f"gw{GW}" / "players-MID.json").read_text())
    assert flagged[0]["share_flag"] and skipped[0]["share_flag"] is None
    assert [{k: v for k, v in row.items() if k != "share_flag"} for row in flagged] == [
        {k: v for k, v in row.items() if k != "share_flag"} for row in skipped
    ]


def test_ep_runs_without_rating_inputs(tmp_path, capsys):
    data_root, analysis_root = seed(tmp_path)
    write_inputs(analysis_root, inputs_document())
    assert run(data_root, analysis_root) == 0
    captured = capsys.readouterr()
    written = json.loads((analysis_root / f"gw{GW}" / "players-MID.json").read_text())
    assert all(row["share_flag"] is None for row in written)
    lines = share_lines(captured.err)
    assert len(lines) == 1 and lines[0].startswith("WARNING: share check skipped: ")
    assert "club-priors.json" in lines[0]


def test_ep_share_check_skips_a_summary_row_without_a_venue(tmp_path, capsys):
    data_root, analysis_root = seed_share_check(tmp_path)
    store = SnapshotStore(data_root)
    store.save(GW, "players/summary-3", element_summary_payload(history=[
        match_record_payload(fixture=101, round=1, starts=1, expected_goals="0.90")
    ]), "seed://test")
    assert run(data_root, analysis_root) == 0
    captured = capsys.readouterr()
    written = json.loads((analysis_root / f"gw{GW}" / "players-MID.json").read_text())
    assert written[0]["share_flag"] is None
    lines = share_lines(captured.err)
    assert len(lines) == 1 and lines[0].startswith("WARNING: share check skipped: ")
    assert "was_home" in lines[0]


# --- --history-from store ------------------------------------------------------


def store_world(tmp_path, season=None, after_write=None):
    """A synced season (rounds 1–2, gw3 open) with gw3 inputs and fixtures for
    its three clubs; element 1 is the MID judged. `after_write(raw)` edits
    the raw tree before the sync."""
    from fpl.season_store import sync
    from tests.test_season_store import Season

    raw, db = tmp_path / "raw", tmp_path / "store" / "s.sqlite"
    (season or Season()).write(raw)
    if after_write is not None:
        after_write(raw)
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
        store = ["--store", str(db)] if source == "store" else []
        assert run(raw, analysis_root, "--history-from", source, *store,
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


def test_ep_reads_summaries_by_default_and_never_opens_the_store(tmp_path, monkeypatch):
    raw, _, analysis_root = store_world(tmp_path)
    monkeypatch.chdir(tmp_path)  # the default store path, relative, names nothing here
    out = tmp_path / "default.json"
    assert run(raw, analysis_root, "--out", str(out)) == 0


def test_ep_share_check_reads_the_store_with_history_from_store(tmp_path, capsys):
    """Element 1 starts three times (round 2 a double) and takes all of C1's
    event-live xG. The cached summary of his teammate, element 3, claims 1.50
    xG in round 1 that event-live does not, so the summaries halve element 1's
    share while the store keeps it whole. His xg90 override implies about all
    of C1's xG: flagged against the summaries, not against the store."""
    from datetime import timedelta

    from tests.test_season_store import double_gameweek, fetch_time, save_raw

    season = double_gameweek()

    def inflate_teammate_summary(raw):
        rows = season.summary_rows(3, before_gw=GW)
        for row in rows:
            if row["round"] == 1:
                row["expected_goals"] = "1.50"
        save_raw(raw, fetch_time(GW) + timedelta(hours=4), GW, "players/summary-3",
                 {"fixtures": [], "history": rows, "history_past": []})

    raw, db, analysis_root = store_world(tmp_path, season, inflate_teammate_summary)
    (analysis_root / "club-priors.json").write_text(json.dumps(priors_doc(
        {c: (1.0, 1.0, False) for c in ("C1", "C2", "C3")})), encoding="utf-8")
    write_inputs(analysis_root, inputs_document([{
        "id": 1, "name": "P1", "p_start": 0.9, "uncertainty": "LOW",
        "overrides": {"xg90": 1.4, "xa90": 0.0, "minutes_per_start": 90},
        "reason": "synthetic share test",
    }]))
    flags = {}
    for source in ("summaries", "store"):
        out = tmp_path / f"{source}.json"
        store = ["--store", str(db)] if source == "store" else []
        assert run(raw, analysis_root, "--history-from", source, *store,
                   "--out", str(out)) == 0
        assert "share check skipped" not in capsys.readouterr().err
        (row,) = json.loads(out.read_text())
        flags[source] = row["share_flag"]

    assert flags["summaries"] is not None and flags["summaries"].startswith("xG EP>club")
    assert flags["store"] is None
