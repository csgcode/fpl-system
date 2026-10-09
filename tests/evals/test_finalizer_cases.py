"""Finalizer live cases, checked for free: the synthetic my-team budget, the
mutators, and each case workspace driven through the real CLI in-process,
so a case whose inputs drift fails here rather than in a paid run."""

from __future__ import annotations

import json

import pytest

from evals.finalizer.cases import (
    LIVE_CASES,
    CaseError,
    FlagEdit,
    Replace,
    apply_edit,
    apply_flag_edit,
    live_case,
    synthetic_my_team,
)
from evals.finalizer.live import prepare
from evals.harness.workspace import SourceError
from fpl.__main__ import main
from fpl.clock import REPLAY_ENV
from fpl.final_check import check_proposal
from fpl.freshness import flag_delta
from fpl.models import Bootstrap, MyTeam
from fpl.state import parse_state
from tests.factories import bootstrap_payload, player_payload

PICKS = [(1, 1, False, False), (2, 2, True, False), (3, 3, False, True)]
COST = {1: 50, 2: 120, 3: 65}


@pytest.mark.parametrize("budget,bank", [(240, 5), (230, 0), (235, 0)])
def test_synthetic_my_team_hits_the_budget_exactly(budget, bank):
    team = MyTeam.model_validate(json.loads(synthetic_my_team(PICKS, COST, budget, bank)))
    assert sum(p.selling_price for p in team.picks) + team.transfers.bank == budget
    assert {p.element for p in team.picks} == {1, 2, 3}
    assert [p.is_captain for p in team.picks] == [False, True, False]
    assert team.chips == ()


def test_synthetic_my_team_carries_the_free_transfers():
    team = MyTeam.model_validate(json.loads(synthetic_my_team(PICKS, COST, 240, 5,
                                                              free_transfers=3)))
    assert team.transfers.limit == 3 and team.transfers.made == 0


def test_flag_edit_changes_exactly_one_player():
    payload = bootstrap_payload(elements=[player_payload(id=7), player_payload(id=8)])
    before = Bootstrap.model_validate(payload)
    edited = Bootstrap.model_validate_json(apply_flag_edit(
        json.dumps(payload).encode(), FlagEdit(8, "d", 75, "Knock - 75% chance of playing")))
    [change] = flag_delta(before.elements, edited.elements)
    assert change.id == 8
    assert {c.field: c.after for c in change.changes} == {
        "status": "d", "chance_of_playing_next_round": 75,
        "news": "Knock - 75% chance of playing"}


def test_an_edit_that_no_longer_applies_is_a_case_error():
    with pytest.raises(CaseError, match="0 times"):
        apply_edit("text", Replace("p", "missing", "x"))
    with pytest.raises(CaseError, match="S2"):
        apply_edit("no rows", Replace("p", "__S2_ROW__", ""))


def test_default_live_set_is_l1_to_l4():
    assert [c.id[:2] for c in LIVE_CASES if c.default] == ["L1", "L2", "L3", "L4"]


# --- each case through the real CLI ------------------------------------------


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    built = []

    def build(case_id: str):
        case = live_case(case_id)
        try:
            prepared = prepare(case, tmp_parent=tmp_path, sync=False)
        except SourceError as exc:
            pytest.skip(str(exc))
        monkeypatch.chdir(prepared.ws.root)
        monkeypatch.setenv(REPLAY_ENV, str(prepared.ws.replay_dir))
        built.append(prepared)
        return case, prepared

    return build


def picks_arg(prepared, case) -> str:
    state = parse_state(prepared.files[case.decision("squad-proposal.md")].decode())
    return ",".join(str(p.id) for p in state.picks.picks)


@pytest.mark.parametrize("case_id,exit_code,named", [
    ("L1-gw6-pass", 0, None),
    ("L2-gw5-reopen", 3, "423 Shaw"),
    ("L3-gw4-pass", 0, None),
    ("L4-gw5-rerun", 0, None),
    ("P1-incoming-flag", 3, "124 Groß"),
    ("P5-stale", 5, None),
    ("P6-no-baseline", 4, None),
])
def test_flags_in_the_case_workspace(workspace, capsys, case_id, exit_code, named):
    case, prepared = workspace(case_id)
    assert main(["flags", "--gw", str(case.gw), "--ids", picks_arg(prepared, case)]) \
        == exit_code
    out = capsys.readouterr().out
    if named:
        assert named in out and "gate: 1 of" in out
    stop = case.stop or ("REOPEN" if prepared.truth else None)
    assert (stop == "REOPEN") is (exit_code == 3)


@pytest.mark.parametrize("case_id,exit_code,fail", [
    ("L1-gw6-pass", 0, None),
    ("P3-dropped-row", 1, "FAIL P3: S2 is in the previous ledger"),
    ("P4-malformed-state", 1, "FAIL P1: unparseable line in STATE block: 'bank 0.3'"),
    ("P8-chip-omitted", 0, None),
])
def test_final_check_in_the_case_workspace(workspace, capsys, case_id, exit_code, fail):
    case, _ = workspace(case_id)
    assert main(["final-check", "--gw", str(case.gw)]) == exit_code
    out = capsys.readouterr().out
    assert "final.md: not written" in out
    if fail:
        assert fail in out


def test_each_proposal_mutation_yields_exactly_its_finding(workspace):
    for case_id, rules in (("P3-dropped-row", ["P3"]), ("P4-malformed-state", ["P1"]),
                           ("P8-chip-omitted", [])):
        case, prepared = workspace(case_id)
        findings = check_proposal(
            prepared.files[case.decision("squad-proposal.md")].decode(), gw=case.gw,
            previous_final=prepared.files[case.decision("final.md", gw=case.gw - 1)].decode(),
            suggestions_exists=True)
        assert [f.rule for f in findings] == rules, case_id


@pytest.mark.parametrize("case_id,budget", [
    ("L1-gw6-pass", "99.2"), ("L4-gw5-rerun", "99.3"), ("P7-value-drift", "99.1"),
])
def test_my_team_budget_in_the_case_workspace(workspace, capsys, case_id, budget):
    case, prepared = workspace(case_id)
    assert main(["my-team", "--gw", str(case.gw)]) == 0
    out = capsys.readouterr().out
    assert f"budget {budget}" in out
    previous = parse_state(prepared.files[case.decision("final.md", gw=case.gw - 1)].decode())
    assert f"free transfers {previous.free_transfers_banked}" in out


def test_the_existing_final_is_placed_for_p2(workspace):
    case, prepared = workspace("P2-final-exists")
    assert (prepared.ws.root / case.decision("final.md")).is_file()
    assert (prepared.ws.root / "data/auth.json").is_file()


def test_the_correction_case_serves_the_fielded_picks_and_entry(workspace, capsys):
    case, prepared = workspace("P9-correction")
    assert not (prepared.ws.root / "data/auth.json").exists()
    assert main(["picks", "--gw", "5", "--team-id", "8455344", "--event", "5"]) == 0
    assert main(["entry", "--gw", "5", "--team-id", "8455344", "--force"]) == 0
    out = capsys.readouterr().out
    assert "value: 998" in out
