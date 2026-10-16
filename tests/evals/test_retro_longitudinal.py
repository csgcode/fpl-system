"""The longitudinal report: per-round calibration series and, for each
registered correction, its metric before and after the round it was issued."""

from __future__ import annotations

from pathlib import Path

import pytest

from evals.retro_analyst import longitudinal as lg
from fpl.calibrate import build_report
from tests.factories import live_element_payload
from tests.test_calibrate import live_of, prediction_row, predictions

RETRO = Path(__file__).resolve().parents[2] / "data" / "retro"


def write_ledger(root: Path, round_: int, *, p_start: float, points: int) -> None:
    rows = predictions(prediction_row(id=1, position=2, p_start=p_start, ep_gw=[3.0] * 6),
                       prediction_row(id=2, position=3, p_start=p_start, ep_gw=[3.0] * 6))
    live = live_of(live_element_payload(element_id=1, total_points=points),
                   live_element_payload(element_id=2, total_points=3))
    report = build_report(rows, live, match_round=round_)
    root.mkdir(parents=True, exist_ok=True)
    (root / f"gw{round_}-calibration.json").write_text(report.model_dump_json(), "utf-8")


def test_series_reads_every_ledger_in_round_order(tmp_path):
    for r, p in ((2, 0.5), (1, 0.9), (10, 0.7)):
        write_ledger(tmp_path, r, p_start=p, points=5)
    series = lg.series(lg.load_ledgers(tmp_path))
    assert [s.round for s in series] == [1, 2, 10]
    assert [s.starts_gap for s in series] == pytest.approx([-0.2, -1.0, -0.6])
    assert series[0].def_minus_mid == pytest.approx(2.0)


def test_effect_splits_at_the_issuing_round(tmp_path):
    for r, p in ((1, 0.9), (2, 0.5), (3, 0.7)):
        write_ledger(tmp_path, r, p_start=p, points=3)
    effect = lg.effect(lg.series(lg.load_ledgers(tmp_path)),
                       lg.Registered("C1", 2, "starts_gap", "expected − actual starts"))
    assert effect.before == pytest.approx((-0.2 + -1.0) / 2)
    assert effect.after == pytest.approx(-0.6)


def test_report_prints_series_and_registry(tmp_path, capsys):
    for r in (1, 2):
        write_ledger(tmp_path, r, p_start=0.9, points=3)
    assert lg.print_report(tmp_path) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith("round")
    assert "C18" in out and "C9" in out


@pytest.mark.skipif(not (RETRO / "gw5-calibration.json").is_file(), reason="no ledgers")
def test_real_c18_series():
    by_round = {s.round: s for s in lg.series(lg.load_ledgers(RETRO))}
    assert [round(by_round[r].starts_gap, 2) for r in (2, 3, 4, 5)] == \
        [7.91, 8.95, 10.69, -3.19]
