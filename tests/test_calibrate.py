"""Calibration: joining analyst EP predictions against a completed round's
actuals. Pure logic over already-validated inputs — no network, no clock."""

from __future__ import annotations

import json

import pytest

from fpl.calibrate import load_predictions
from fpl.models import Position

POSITION_FILES = ("GKP", "DEF", "MID", "FWD")


def prediction_row(**overrides):
    row = {
        "id": 1,
        "name": "Alpha",
        "team": "TST",
        "price": 6.0,
        "p_start": 0.9,
        "ep_gw": [3.5, 3.2, 4.0, 3.6, 3.8, 3.7],
        "ep_total6": 21.8,
        "uncertainty": "LOW",
        "notes": "some analyst prose",
        "extra_diagnostic_field": {"nested": True},
    }
    row.update(overrides)
    return row


def write_analysis(tmp_path, rows_by_position):
    analysis_dir = tmp_path / "analysis" / "gw1"
    analysis_dir.mkdir(parents=True)
    for position in POSITION_FILES:
        rows = rows_by_position.get(position, [])
        (analysis_dir / f"players-{position}.json").write_text(
            json.dumps(rows), encoding="utf-8"
        )
    return analysis_dir


def test_load_predictions_tags_position_and_tolerates_extra_fields(tmp_path):
    analysis_dir = write_analysis(
        tmp_path,
        {
            "GKP": [prediction_row(id=1, name="Keeper")],
            "MID": [prediction_row(id=2, name="Mid", ep_gw=[5.0] * 6)],
        },
    )
    predictions = load_predictions(analysis_dir)
    by_id = {p.id: p for p in predictions}
    assert by_id[1].position is Position.GKP
    assert by_id[2].position is Position.MID
    assert by_id[2].predicted == 5.0
    assert by_id[1].p_start == 0.9


def test_load_predictions_refuses_missing_directory(tmp_path):
    with pytest.raises(ValueError, match="no analysis directory"):
        load_predictions(tmp_path / "analysis" / "gw9")


def test_load_predictions_refuses_missing_position_file(tmp_path):
    analysis_dir = write_analysis(tmp_path, {})
    (analysis_dir / "players-FWD.json").unlink()
    with pytest.raises(ValueError, match="players-FWD.json"):
        load_predictions(analysis_dir)


def test_load_predictions_refuses_duplicate_id_across_positions(tmp_path):
    analysis_dir = write_analysis(
        tmp_path,
        {"MID": [prediction_row(id=7)], "FWD": [prediction_row(id=7)]},
    )
    with pytest.raises(ValueError, match="7"):
        load_predictions(analysis_dir)


def test_load_predictions_refuses_row_with_empty_ep_gw(tmp_path):
    analysis_dir = write_analysis(tmp_path, {"MID": [prediction_row(ep_gw=[])]})
    with pytest.raises(ValueError, match="players-MID.json"):
        load_predictions(analysis_dir)


def test_load_predictions_refuses_unknown_uncertainty(tmp_path):
    analysis_dir = write_analysis(
        tmp_path, {"MID": [prediction_row(uncertainty="MEDIUM")]}
    )
    with pytest.raises(ValueError, match="players-MID.json"):
        load_predictions(analysis_dir)


# --- build_report: join --------------------------------------------------


def predictions(*rows):
    from fpl.calibrate import PlayerPrediction

    return tuple(PlayerPrediction.model_validate(row) for row in rows)


def live_of(*elements):
    from fpl.models import EventLive
    from tests.factories import event_live_payload

    return EventLive.model_validate(event_live_payload(list(elements)))


def test_report_joins_predictions_to_actuals_with_signed_error():
    from fpl.calibrate import build_report
    from tests.factories import live_element_payload

    report = build_report(
        predictions(
            prediction_row(id=1, position=3, ep_gw=[4.0] * 6),
            prediction_row(id=2, position=4, ep_gw=[6.5] * 6),
        ),
        live_of(
            live_element_payload(element_id=1, total_points=9),
            live_element_payload(element_id=2, total_points=2),
        ),
        match_round=1,
    )
    by_id = {line.id: line for line in report.players}
    assert by_id[1].error == pytest.approx(5.0)   # actual - predicted
    assert by_id[2].error == pytest.approx(-4.5)
    assert report.round == 1
    assert report.unmatched_prediction_ids == ()


def test_report_lists_unmatched_predictions_and_excludes_them_from_stats():
    from fpl.calibrate import build_report
    from tests.factories import live_element_payload

    report = build_report(
        predictions(
            prediction_row(id=1, position=3, ep_gw=[4.0] * 6),
            prediction_row(id=99, position=3),
        ),
        live_of(live_element_payload(element_id=1, total_points=4)),
        match_round=1,
    )
    assert report.unmatched_prediction_ids == (99,)
    assert [line.id for line in report.players] == [1]
    assert report.overall.n == 1


def test_report_refuses_when_nothing_matches():
    from fpl.calibrate import build_report
    from tests.factories import live_element_payload

    with pytest.raises(ValueError, match="no prediction matched"):
        build_report(
            predictions(prediction_row(id=99, position=3)),
            live_of(live_element_payload(element_id=1)),
            match_round=1,
        )


# --- build_report: aggregates ---------------------------------------------


def test_report_aggregates_by_position_uncertainty_and_price_band():
    from fpl.calibrate import build_report
    from tests.factories import live_element_payload

    report = build_report(
        predictions(
            prediction_row(id=1, position=3, price=4.9, uncertainty="LOW", ep_gw=[4.0] * 6),
            prediction_row(id=2, position=3, price=7.9, uncertainty="LOW", ep_gw=[2.0] * 6),
            prediction_row(id=3, position=4, price=8.0, uncertainty="HIGH", ep_gw=[6.0] * 6),
        ),
        live_of(
            live_element_payload(element_id=1, total_points=6),   # error +2
            live_element_payload(element_id=2, total_points=2),   # error  0
            live_element_payload(element_id=3, total_points=2),   # error -4
        ),
        match_round=1,
    )
    assert report.overall.n == 3
    assert report.overall.bias == pytest.approx(-2 / 3, abs=1e-3)
    assert report.overall.mae == pytest.approx(2.0)
    assert report.by_position["MID"].n == 2
    assert report.by_position["MID"].bias == pytest.approx(1.0)
    assert report.by_position["FWD"].mae == pytest.approx(4.0)
    assert "GKP" not in report.by_position          # empty groups omitted
    assert report.by_uncertainty["LOW"].n == 2
    assert report.by_uncertainty["HIGH"].n == 1
    assert report.by_price_band["<5.5"].n == 1
    assert report.by_price_band["5.5-7.9"].n == 1
    assert report.by_price_band[">=8.0"].n == 1


def test_report_scores_minutes_model_with_brier():
    from fpl.calibrate import build_report
    from tests.factories import live_element_payload

    report = build_report(
        predictions(
            prediction_row(id=1, position=3, p_start=0.9),
            prediction_row(id=2, position=3, p_start=0.4),
        ),
        live_of(
            live_element_payload(element_id=1, starts=1),
            live_element_payload(element_id=2, starts=0, minutes=0),
        ),
        match_round=1,
    )
    minutes = report.minutes
    assert minutes.n == 2
    assert minutes.expected_starts == pytest.approx(1.3)
    assert minutes.actual_starts == 1
    assert minutes.brier == pytest.approx(((0.9 - 1) ** 2 + (0.4 - 0) ** 2) / 2, abs=1e-4)


# --- build_report: squad section -------------------------------------------


def squad_picks(captain=1, vice=2):
    from fpl.state import picks_from_ids

    return picks_from_ids(list(range(1, 16)), captain=captain, vice=vice)


def full_squad_inputs():
    """15 predicted players at 3.0 EP each; actuals are 2 everywhere except
    id 5 (XI-best, 9), id 1 the captain (4), and id 12 (bench-best, 11)."""
    from tests.factories import live_element_payload

    rows = predictions(
        *[prediction_row(id=i, name=f"P{i}", position=3, ep_gw=[3.0] * 6) for i in range(1, 16)]
    )
    actual = {i: 2 for i in range(1, 16)} | {5: 9, 1: 4, 12: 11}
    live = live_of(
        *[live_element_payload(element_id=i, total_points=actual[i]) for i in range(1, 16)]
    )
    return rows, live


def test_report_squad_totals_double_captain_and_find_hindsight_captain():
    from fpl.calibrate import build_report

    rows, live = full_squad_inputs()
    report = build_report(rows, live, match_round=1, picks=squad_picks())
    squad = report.squad
    assert squad is not None
    # XI predicted: 11 x 3.0 + captain 3.0 again = 36.0
    assert squad.predicted_xi_total == pytest.approx(36.0)
    # XI actual: 9 x 2 + 9 + 4, + captain's 4 again = 35
    assert squad.actual_xi_total == 35
    assert squad.captain.chosen_id == 1
    assert squad.captain.chosen_actual == 4
    assert squad.captain.hindsight_best_id == 5      # bench 11-pointer excluded
    assert squad.captain.forgone == 5
    assert squad.bench_points_stranded == 11 + 2 + 2 + 2


def test_report_without_picks_has_no_squad_section():
    from fpl.calibrate import build_report

    rows, live = full_squad_inputs()
    report = build_report(rows, live, match_round=1)
    assert report.squad is None


def test_report_warns_on_squad_pick_without_prediction():
    from fpl.calibrate import build_report

    rows, live = full_squad_inputs()
    rows = tuple(row for row in rows if row.id != 3)
    report = build_report(rows, live, match_round=1, picks=squad_picks())
    assert any("3" in warning for warning in report.warnings)
    assert report.squad.predicted_xi_total == pytest.approx(33.0)
    assert report.squad.actual_xi_total == 35       # actuals unaffected


# --- build_report: defcon sample -------------------------------------------


def test_report_defcon_sample_uses_position_thresholds_and_minutes_floor():
    from fpl.calibrate import build_report
    from tests.factories import live_element_payload

    report = build_report(
        predictions(
            prediction_row(id=1, position=2),   # DEF, dc 10 -> hit at threshold
            prediction_row(id=2, position=3),   # MID, dc 11 -> miss (needs 12)
            prediction_row(id=3, position=1),   # GKP -> not eligible
            prediction_row(id=4, position=4),   # FWD, 59 minutes -> excluded
        ),
        live_of(
            live_element_payload(element_id=1, defensive_contribution=10),
            live_element_payload(element_id=2, defensive_contribution=11),
            live_element_payload(element_id=3, defensive_contribution=14),
            live_element_payload(element_id=4, defensive_contribution=14, minutes=59),
        ),
        match_round=1,
    )
    by_id = {line.id: line for line in report.defcon}
    assert set(by_id) == {1, 2}
    assert by_id[1].threshold == 10 and by_id[1].hit is True
    assert by_id[2].threshold == 12 and by_id[2].hit is False


# --- cumulative -------------------------------------------------------------


def small_report(match_round, points):
    from fpl.calibrate import build_report
    from tests.factories import live_element_payload

    return build_report(
        predictions(prediction_row(id=1, position=3, ep_gw=[4.0] * 6, p_start=1.0)),
        live_of(live_element_payload(element_id=1, total_points=points)),
        match_round=match_round,
    )


def test_report_pools_cumulative_stats_across_rounds():
    from fpl.calibrate import build_report
    from tests.factories import live_element_payload

    prior = small_report(1, points=6)                       # error +2
    report = build_report(
        predictions(prediction_row(id=1, position=3, ep_gw=[4.0] * 6, p_start=1.0)),
        live_of(live_element_payload(element_id=1, total_points=0)),   # error -4
        match_round=2,
        prior_reports=(prior,),
    )
    cumulative = report.cumulative
    assert cumulative.rounds == (1, 2)
    assert cumulative.overall.n == 2
    assert cumulative.overall.bias == pytest.approx(-1.0)
    assert cumulative.overall.mae == pytest.approx(3.0)
    assert cumulative.by_position["MID"].n == 2


def test_report_refuses_duplicate_round_in_priors():
    from fpl.calibrate import build_report
    from tests.factories import live_element_payload

    prior = small_report(2, points=6)
    with pytest.raises(ValueError, match="round 2"):
        build_report(
            predictions(prediction_row(id=1, position=3)),
            live_of(live_element_payload(element_id=1)),
            match_round=2,
            prior_reports=(prior,),
        )


def test_load_report_round_trips_and_gates_schema_version(tmp_path):
    from fpl.calibrate import load_report

    report = small_report(1, points=6)
    path = tmp_path / "gw1-calibration.json"
    path.write_text(report.model_dump_json(), encoding="utf-8")
    assert load_report(path).round == 1

    stale = json.loads(report.model_dump_json())
    stale["schema_version"] = 99
    path.write_text(json.dumps(stale), encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        load_report(path)
