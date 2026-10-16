"""Season outcome of the minutes model: formulas on synthetic ledgers, then a
golden over the committed calibration ledgers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.player_analyst.cases import REPO_ROOT
from evals.player_analyst.outcome import (
    bands,
    brier,
    load_ledgers,
    minutes_share,
    persistence_pairs,
    print_outcome,
    score,
    skill,
)


def player(id, p, started, predicted=4.0, actual=4, position="MID"):
    return {"id": id, "p_start": p, "started": started, "predicted": predicted,
            "actual": actual, "position": position}


def test_brier_is_the_mean_squared_start_error():
    assert brier([player(1, 0.9, True), player(2, 0.2, False)]) == pytest.approx(
        (0.01 + 0.04) / 2)


def test_bands_report_count_mean_and_observed_rate():
    got = bands([player(1, 0.1, False), player(2, 0.2, True), player(3, 1.0, True)])
    assert (got[0].n, got[0].mean_p, got[0].observed) == (2, pytest.approx(0.15), 0.5)
    assert (got[1].n, got[1].mean_p) == (0, None)
    assert got[3].n == 1


def test_persistence_baseline_uses_ids_in_both_ledgers():
    previous = [player(1, 0.9, True), player(2, 0.9, False)]
    pairs = persistence_pairs([player(1, 0.9, True), player(2, 0.1, False),
                               player(3, 0.5, True)], previous)
    assert [(r["id"], p) for r, p in pairs] == [(1, 0.88), (2, 0.08)]
    assert persistence_pairs([player(1, 0.5, True)], None) == []


def test_skill_is_one_minus_the_brier_ratio():
    pairs = [(player(1, 1.0, True), 0.88), (player(2, 0.0, False), 0.08)]
    assert skill(pairs) == pytest.approx(1.0)
    worse = [(player(1, 0.5, True), 0.88)]
    assert skill(worse) == pytest.approx(1 - 0.25 / 0.0144)
    assert skill([]) is None


def test_minutes_share_divides_the_start_term_by_the_squared_error():
    rows = [player(1, 0.5, True, predicted=4.0, actual=8), player(2, 0.0, False, 0.0, 0)]
    assert minutes_share(rows) == pytest.approx(((0.5 * 4.0 / 0.5) ** 2) / 16)


def test_score_adds_a_pooled_row(tmp_path: Path):
    retro = tmp_path / "data" / "retro"
    retro.mkdir(parents=True)
    for number, rows in ((1, [player(1, 0.9, True)]), (2, [player(1, 0.8, False)])):
        (retro / f"gw{number}-calibration.json").write_text(json.dumps({"players": rows}))
    results = score(load_ledgers(tmp_path))
    assert [r.label for r in results] == ["r1", "r2", "pooled"]
    assert results[0].skill is None
    assert results[2].n == 2


def test_print_outcome_without_ledgers(tmp_path, capsys):
    assert print_outcome(tmp_path) == 0
    assert "no calibration ledgers" in capsys.readouterr().out


GOLDEN = {"r1": (0.1501, None, 0.53), "r2": (0.1030, 0.030, 0.38),
          "r3": (0.1037, -0.013, 0.27), "r4": (0.1097, 0.044, 0.22),
          "r5": (0.1101, 0.191, 0.20)}


@pytest.mark.skipif(not (REPO_ROOT / "data/retro/gw5-calibration.json").is_file(),
                    reason="committed calibration ledgers are absent")
def test_golden_on_committed_ledgers():
    by_label = {r.label: r for r in score(load_ledgers(REPO_ROOT))}
    for label, (b, s, share) in GOLDEN.items():
        result = by_label[label]
        assert round(result.brier, 4) == b
        assert (result.skill is None) if s is None else round(result.skill, 3) == s
        assert round(result.minutes_share, 2) == share
