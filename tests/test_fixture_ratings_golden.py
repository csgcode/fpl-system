"""`fpl fixtures-rate` against the committed season: it must reproduce the
fixtures.json files the fixture analyst hand-built in GW3–GW6. Skipped where
the raw snapshots are absent."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fpl.__main__ import main
from fpl.fixture_ratings import load_inputs, rate, render_tables

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
ANALYSIS = REPO / "data" / "analysis"
PRIORS = ANALYSIS / "club-priors.json"


def run_for(gw):
    if not (RAW / f"gw{gw}" / "players").is_dir():
        pytest.skip(f"data/raw/gw{gw}/players is absent")
    from fpl.store import SnapshotStore

    return rate(load_inputs(SnapshotStore(RAW), gw, priors_path=PRIORS, analysis_root=ANALYSIS))


def committed(gw):
    return json.loads((ANALYSIS / f"gw{gw}" / "fixtures.json").read_text(encoding="utf-8"))


def row_key(row):
    return (row["gw"], row["club"], row["opp"], row["venue"])


def compare(run, gw):
    reference = committed(gw)
    rating_diffs = {
        (club, kind): abs(reference["ratings"][club][kind] - getattr(rating, kind))
        for club, rating in run.clubs.items() for kind in ("att", "defw")
    }
    ours = {(r.gw, r.club, r.opp, r.venue): r for r in run.rows}
    theirs = {row_key(r): r for r in reference["fixtures"]}
    return rating_diffs, ours, theirs


def max_diff(ours, theirs, field):
    return max(abs(getattr(ours[k], field) - theirs[k][field]) for k in theirs)


def test_gw6_reproduces_the_committed_file_exactly(tmp_path, capsys):
    run = run_for(6)
    rating_diffs, ours, theirs = compare(run, 6)
    assert len(rating_diffs) == 40 and max(rating_diffs.values()) < 1e-9
    assert set(ours) == set(theirs)
    for key, row in theirs.items():
        mine = ours[key]
        assert (mine.lambda_att, mine.lambda_def, mine.p_cs, mine.fdr, mine.band) == (
            row["lambda_att"], row["lambda_def"], row["p_cs"], row["fdr"], row["band"]), key


def test_gw6_stdout_and_table_anchors(tmp_path, capsys):
    if not (RAW / "gw6" / "players").is_dir():
        pytest.skip("data/raw/gw6/players is absent")
    code = main(["--data-root", str(RAW), "fixtures-rate", "--gw", "6",
                 "--priors", str(PRIORS), "--analysis-root", str(tmp_path / "analysis"),
                 "--store", str(tmp_path / "store.sqlite")])
    out = capsys.readouterr().out
    assert code == 0
    assert "clipped: 64 of 200" in out
    assert "home 1.65, away 1.41, total 3.06" in out
    assert "(+6.7%)" in out

    tables = (tmp_path / "analysis" / "gw6" / "fixtures-tables.md").read_text(encoding="utf-8")
    attack = tables[tables.index("## Attack ticker"):tables.index("## Defence ticker")]
    defence = tables[tables.index("## Defence ticker"):tables.index("## Swings")]
    swings = tables[tables.index("## Swings"):tables.index("## FDR vs model")]
    band = tables[tables.index("## Promoted band"):tables.index("## Blanks")]
    assert "| 1 | MCI | 11.79 |" in attack
    assert "| 1 | ARS | 2.24 |" in defence
    assert "| ARS | +0.48 |" in swings
    assert band.count("\n| ") - 1 == 14
    assert "| 10 | ARS | HUL (H) | 0.49 |" in band


def test_gw6_json_bytes_match_the_committed_file():
    run = run_for(6)
    from fpl.fixture_ratings import render_json

    # The committed file lacks only the trailing newline the CLI writes.
    expected = (ANALYSIS / "gw6" / "fixtures.json").read_text(encoding="utf-8")
    assert render_json(run) == expected.rstrip("\n") + "\n"


@pytest.mark.parametrize("gw", [4, 5])
def test_gw4_and_gw5_within_rounding_drift(gw):
    run = run_for(gw)
    rating_diffs, ours, theirs = compare(run, gw)
    differing = [k for k, d in rating_diffs.items() if d > 1e-9]
    assert len(differing) == 2 and max(rating_diffs.values()) <= 0.01 + 1e-9
    assert set(ours) == set(theirs)
    assert max_diff(ours, theirs, "lambda_att") <= 0.02 + 1e-9
    assert max_diff(ours, theirs, "lambda_def") <= 0.02 + 1e-9
    assert max_diff(ours, theirs, "p_cs") <= 0.01 + 1e-9
    assert all((ours[k].fdr, ours[k].band) == (r["fdr"], r["band"]) for k, r in theirs.items())


def test_gw3_ratings_within_half_a_cent():
    run = run_for(3)
    rating_diffs, ours, theirs = compare(run, 3)
    assert max(rating_diffs.values()) <= 0.005 + 1e-9
    assert set(ours) == set(theirs)


def test_tables_render_for_every_committed_gw():
    for gw in (3, 4, 5, 6):
        if (RAW / f"gw{gw}" / "players").is_dir():
            assert f"## Detail GW{gw + 5}" in render_tables(run_for(gw))
