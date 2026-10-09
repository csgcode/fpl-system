"""Every live plan-builder case, run through the current CLI with no agent:
the inputs must still produce what the case expects, and the spec's failure
table must name the owner the case expects."""

from __future__ import annotations

import re

import pytest

from evals.plan_builder.cases import (
    LIVE_CASES,
    REPO_ROOT,
    CaseError,
    LiveCase,
    Replace,
    case_files,
    live_case,
)
from evals.plan_builder.checks import owner_for
from fpl.__main__ import main
from fpl.replay import REPLAY_ENV


def run_cli(case: LiveCase, tmp_path, monkeypatch, capsys) -> tuple[int, str, str]:
    for path, data in case_files(REPO_ROOT, case).items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    replay = tmp_path / "replay"
    replay.mkdir()
    monkeypatch.setenv(REPLAY_ENV, str(replay))
    monkeypatch.chdir(tmp_path)
    code = main(["plan", "--gw", str(case.gw), "--out", case.plan])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.mark.parametrize("case", LIVE_CASES, ids=[c.id for c in LIVE_CASES])
def test_case_inputs_produce_the_expected_cli_result(case, tmp_path, monkeypatch, capsys):
    try:
        code, out, err = run_cli(case, tmp_path, monkeypatch, capsys)
    except CaseError as exc:
        pytest.skip(str(exc))
    expect = case.expect
    assert code == expect.exit_code, err
    if expect.exit_code == 0:
        lines = out.splitlines()
        assert f"transfers: {expect.transfers} ({expect.transfer_source})" in lines
        assert any(line.startswith(f"captain: {expect.captain} (") for line in lines)
        warnings = [line for line in lines if line.startswith("WARNING: ")]
        assert len(warnings) == len(expect.warnings), warnings
        for wanted in expect.warnings:
            assert any(wanted in line for line in warnings), (wanted, warnings)
        assert (tmp_path / case.plan).is_file()
    else:
        assert expect.error is not None
        assert any(expect.error in line for line in err.splitlines()
                   if line.startswith("error: ")), err
        for candidate in expect.candidate_ids:
            assert re.search(rf"\bid {candidate}\b", err)
        assert not (tmp_path / case.plan).exists()


@pytest.mark.parametrize("case", [c for c in LIVE_CASES if c.expect.exit_code != 0],
                         ids=lambda c: c.id)
def test_the_spec_table_names_the_expected_owner(case):
    spec = (REPO_ROOT / "agents/plan-builder.md").read_text("utf-8")
    assert owner_for(case.expect.error or "", spec) == case.expect.owner


def test_an_edit_that_no_longer_matches_refuses():
    case = live_case("p-disagree")
    broken = LiveCase(case.id, case.gw, case.commit, case.expect,
                      edits=(Replace(case.final, "no such text", "x"),))
    with pytest.raises(CaseError, match="occurs 0 times"):
        case_files(REPO_ROOT, broken)


def test_the_cycles_own_plan_is_never_an_input():
    for case in LIVE_CASES:
        assert case.plan not in case.sources
