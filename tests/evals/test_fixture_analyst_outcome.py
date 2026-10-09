"""Season outcome tracker for fixture forecasts: Brier score of P(CS) and
Poisson log-likelihood of λ_att against final scores, beside a constant
baseline from earlier rounds. Prints only; never pass/fail."""

from __future__ import annotations

import json
import math

import pytest

from evals.fixture_analyst.outcome import MIN_ROUNDS, print_outcome, score_rounds


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed(root, *, forecast_gws=(2,)):
    teams = [{"id": 1, "short_name": "AAA"}, {"id": 2, "short_name": "BBB"}]
    fixtures = [
        {"id": 1, "event": 1, "team_h": 1, "team_a": 2, "finished": True,
         "team_h_score": 2, "team_a_score": 0},
        {"id": 2, "event": 2, "team_h": 2, "team_a": 1, "finished": True,
         "team_h_score": 1, "team_a_score": 1},
        {"id": 3, "event": 3, "team_h": 1, "team_a": 2, "finished": False,
         "team_h_score": None, "team_a_score": None},
    ]
    write(root / "data/raw/gw3/bootstrap.json", {"teams": teams})
    write(root / "data/raw/gw3/fixtures.json", fixtures)
    for gw in forecast_gws:
        write(root / f"data/analysis/gw{gw}/fixtures.json", {"gw": gw, "fixtures": [
            {"club": "BBB", "gw": 2, "opp": "AAA", "venue": "H", "lambda_att": 1.5,
             "lambda_def": 1.2, "p_cs": 0.30},
            {"club": "AAA", "gw": 2, "opp": "BBB", "venue": "A", "lambda_att": 1.2,
             "lambda_def": 1.5, "p_cs": 0.22},
            {"club": "AAA", "gw": 3, "opp": "BBB", "venue": "H", "lambda_att": 1.0,
             "lambda_def": 1.0, "p_cs": 0.37}]})


def test_scores_only_the_forecast_round_against_final_scores(tmp_path):
    seed(tmp_path)
    [round_] = score_rounds(tmp_path)
    assert (round_.gw, round_.rows) == (2, 2)
    # Both sides scored once: no clean sheets.
    assert round_.brier == pytest.approx((0.30 ** 2 + 0.22 ** 2) / 2)
    expected_ll = (math.log(1.5 * math.exp(-1.5)) + math.log(1.2 * math.exp(-1.2))) / 2
    assert round_.log_lik == pytest.approx(expected_ll)


def test_baseline_is_the_constant_rate_from_earlier_rounds(tmp_path):
    seed(tmp_path)
    [round_] = score_rounds(tmp_path)
    # Round 1: one clean sheet in two team-matches; home 2 goals, away 0.
    assert round_.brier_base == pytest.approx(((0.5 - 0) ** 2 + (0.5 - 0) ** 2) / 2)
    assert round_.base_lambda == {"H": 2.0, "A": 0.0}


def test_print_waits_for_enough_rounds(tmp_path, capsys):
    seed(tmp_path)
    assert print_outcome(tmp_path) == 0
    out = capsys.readouterr().out
    assert "gw2: 2 rows" in out
    assert f"1 scored round(s); the season comparison starts at {MIN_ROUNDS}" in out


def test_unplayed_rounds_are_skipped(tmp_path):
    seed(tmp_path, forecast_gws=(2, 3))
    assert [r.gw for r in score_rounds(tmp_path)] == [2]
