"""Season outcome for the squad optimizer: ex-ante EP regret against the
greedy reference, and the realised XI, captain and bench figures."""

from __future__ import annotations

import json

import pytest

from evals.squad_optimizer.cases import REPO_ROOT
from evals.squad_optimizer.outcome import RoundSquad, ex_ante_regret, print_outcome, squad_rounds


def test_ex_ante_regret_is_zero_for_every_recorded_final_plan():
    regrets = ex_ante_regret()
    if not regrets:
        pytest.skip("frozen views missing")
    assert [(r.gw, round(r.regret, 3)) for r in regrets] == [(4, 0.0), (5, 0.0), (6, 0.0)]


def test_squad_rounds_read_the_calibration_ledgers(tmp_path):
    retro = tmp_path / "data" / "retro"
    retro.mkdir(parents=True)
    (retro / "gw1-calibration.json").write_text(json.dumps({"squad": None}))
    (retro / "gw2-calibration.json").write_text(json.dumps({"squad": {
        "predicted_xi_total": 51.66, "actual_xi_total": 79, "bench_points_stranded": 14,
        "captain": {"forgone": 0}, "players": []}}))
    assert squad_rounds(tmp_path) == [RoundSquad(2, 51.66, 79, 0, 14)]


def test_the_real_ledgers_give_the_recorded_season():
    rounds = squad_rounds(REPO_ROOT)
    if len(rounds) < 4:
        pytest.skip("calibration ledgers missing")
    by_round = {r.round: r for r in rounds}
    assert [by_round[g].forgone for g in (2, 3, 4, 5)] == [0, 1, 5, 8]
    assert [by_round[g].stranded for g in (2, 3, 4, 5)] == [14, 13, 7, 8]


def test_print_outcome_prints_both_tables_and_the_sums(capsys):
    assert print_outcome() == 0
    out = capsys.readouterr().out
    assert "ex-ante regret" in out and "season:" in out
