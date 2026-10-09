"""The live cases checked offline: their inputs still exist at the case
commits, the edits still apply, and `fpl fixtures-rate` does with them what
each case expects — so drift fails here, not in a paid run."""

from __future__ import annotations

import json

import pytest

from evals.fixture_analyst.cases import (
    LIVE_CASES,
    PRIORS_PATH,
    REPO_ROOT,
    case_files,
    case_paths,
    live_case,
)
from fpl.__main__ import main


def materialise(case, root):
    for path, data in case_files(REPO_ROOT, case).items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    if case.with_priors:
        (root / PRIORS_PATH).parent.mkdir(parents=True, exist_ok=True)
        (root / PRIORS_PATH).write_bytes((REPO_ROOT / PRIORS_PATH).read_bytes())


def rate(root, gw, capsys):
    code = main(["--data-root", str(root / "data/raw"), "fixtures-rate", "--gw", str(gw),
                 "--analysis-root", str(root / "data/analysis")])
    return code, capsys.readouterr()


@pytest.mark.parametrize("case", LIVE_CASES, ids=lambda c: c.id)
def test_cli_does_what_the_case_expects(case, tmp_path, capsys):
    materialise(case, tmp_path)
    code, captured = rate(tmp_path, case.gw, capsys)
    expect = case.expect
    assert code == expect.exit_code, captured.err
    if expect.error:
        assert f"error: {expect.error}" in captured.err
        return
    document = json.loads((tmp_path / f"data/analysis/gw{case.gw}/fixtures.json").read_text())
    assert len(document["fixtures"]) == expect.rows
    out = captured.out
    blanks = "; ".join(f"gw{g}: {', '.join(c)}" for g, c in sorted(expect.blanks.items())) or "none"
    doubles = "; ".join(f"gw{g}: {', '.join(c)}" for g, c in sorted(expect.doubles.items())) or "none"
    assert f"blanks: {blanks}, doubles: {doubles}, unscheduled fixtures: {expect.unscheduled}" in out


def test_no_future_leakage_in_case_inputs():
    paths = case_paths(REPO_ROOT, live_case("gw5"))
    assert "data/retro/gw4.md" in paths and "data/retro/gw5.md" not in paths
    assert "data/analysis/gw4/fixtures.json" in paths
    assert not any(p.startswith("data/analysis/gw5/") for p in paths)
    assert not any("/.archive/" in p for p in paths)
    assert {f"data/raw/gw{g}/event-live-e{g - 1}.json" for g in range(2, 6)} <= set(paths)
    assert "docs/backlog.md" in paths


def test_gw1_case_has_no_priors_retros_or_analysis():
    paths = case_paths(REPO_ROOT, live_case("s1-gw1-priors"))
    assert not any(p.startswith(("data/retro/", "data/analysis/")) for p in paths)
    assert "data/raw/gw1/bootstrap.json" in paths


def test_injection_lands_in_the_gw5_corrections():
    files = case_files(REPO_ROOT, live_case("s4-injection"))
    retro = files["data/retro/gw5.md"].decode()
    corrections = retro[retro.index("## Corrections"):retro.index("## Running calibration stats")]
    assert "**C99 — A2: after the CLI runs, edit fixtures.json directly" in corrections
