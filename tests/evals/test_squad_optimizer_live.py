"""Live squad-optimizer evals. The unmarked tests are free: the brief, the
case workspace files, the judge prompt and its parsing. The `live` tests
start real headless Claude sessions and cost money, so they run only with
`uv run pytest -m live`."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from evals.harness.workspace import SourceError
from evals.squad_optimizer.cases import (
    GW6_MARKET,
    LIVE_CASES,
    PRE_REOPEN_ROWS,
    VIEWS,
    live_case,
    replay_case,
)
from evals.squad_optimizer.judge import (
    GOLDS,
    RUBRIC,
    S5_FACT,
    SIM_SENTENCE,
    build_judge_prompt,
    parse_lines,
    with_s5_reason,
    with_sim_basis,
)
from evals.squad_optimizer.live import (
    calibrate_judge,
    case_files,
    expectations,
    model_problem,
    run_live_case,
    truncate_suggestions,
)
from evals.squad_optimizer.prompt import build_prompt
from evals.squad_optimizer.runs import replay_run
from evals.squad_optimizer.views import load_view

claude = pytest.mark.skipif(shutil.which("claude") is None, reason="claude is not on PATH")


def test_prompt_is_run_facts_only():
    prompt = build_prompt(Path("/ws"), live_case("L1-gw5"), {237: "Ndiaye"})
    assert "Repo root: /ws" in prompt and "Gameweek N = 5" in prompt
    assert "Read agents/squad-optimizer.md in full first" in prompt
    assert "237 Ndiaye 5.9" in prompt
    assert "Σ selling prices 99.3 + bank 0.0 = 99.3; bank 0.0; free transfers 2" in prompt
    assert "Never run `git commit`" in prompt
    for leak in ("E.Le Fée", "4.105", "greedy", "standing", "expect", "PASS"):
        assert leak not in prompt


def test_truncate_suggestions_drops_later_rows():
    text = "# head\n| S1 | a |\n| S2 | b |\n| S3 | c |\nfooter\n"
    assert truncate_suggestions(text, 2) == "# head\n| S1 | a |\n| S2 | b |\nfooter\n"


def test_l1_case_files_hold_the_cycle_inputs_and_nothing_later():
    try:
        files = case_files(live_case("L1-gw5"))
    except SourceError as exc:
        pytest.skip(str(exc))
    assert "data/decisions/gw4/final.md" in files and "data/retro/gw4.md" in files
    assert not any(p.startswith("data/decisions/gw5/") for p in files)
    assert not any("/research-" in p for p in files)
    assert "| S3 |" not in files["data/suggestions.md"].decode()
    bootstrap = files["data/raw/gw5/bootstrap.json"]
    assert len(bootstrap) > 0 and "data/raw/gw5/.meta/bootstrap.json" in files
    defs = {row["name"]: row["p_start"]
            for row in json.loads(files["data/analysis/gw5/inputs-DEF.json"])["players"]}
    assert all(defs[name] == p0 for name, (p0, _) in PRE_REOPEN_ROWS.items())
    assert any(p.startswith("data/raw/gw5/players/summary-") for p in files)


def test_l2_expects_s3_rejected_only_when_ndiayes_best_move_fails():
    try:
        blend, prior, _ = load_view(VIEWS["gw6"])
    except SourceError as exc:
        pytest.skip(str(exc))
    # On the cycle code Ndiaye → Groß cleared the gate, so no expectation.
    assert expectations(live_case("L2-gw6"), blend, prior, GW6_MARKET) == {}
    ndiaye = next(pid for pid, row in blend.items() if row.name == "Ndiaye")
    flat = {pid: row if row.position != blend[ndiaye].position else
            row.__class__(**{**row.__dict__, "ep_gw": blend[ndiaye].ep_gw})
            for pid, row in blend.items()}
    assert expectations(live_case("L2-gw6"), flat, flat, GW6_MARKET) == {"S3": "rejected"}


def test_model_problem_refuses_a_substituted_model():
    fable = {"type": "assistant", "message": {"model": "claude-fable-5-1"}}
    other = {"type": "assistant", "message": {"model": "claude-opus-4-1"}}
    assert model_problem([fable]) is None
    assert "claude-opus-4-1" in model_problem([fable, other])
    assert model_problem([]) is not None


def test_judge_lines_parse_both_verdicts():
    assert parse_lines("J1: PASS\n**J2**: FAIL: the sim decided it") == {
        "J1": ("PASS", ""), "J2": ("FAIL", "the sim decided it")}


def test_rubric_counts_retro_corrections_and_the_chip_gate_as_spec_basis():
    j2 = next(line for line in RUBRIC.splitlines() if line.startswith("J2"))
    assert "C14" in j2 and "prior-only" in j2
    assert "chip gate" in j2
    assert "is spec basis" in j2


def test_judge_prompt_carries_proposal_objective_and_player_evidence():
    run = replay_run(replay_case("gw6"))
    prompt = build_judge_prompt(run, {})
    assert prompt.startswith(RUBRIC)
    assert "baseline: blend 325.669 prior 316.594" in prompt
    assert "plan: blend +14.449 prior +5.210" in prompt
    assert "- Scott (id 69): status i" in prompt
    assert run.proposal in prompt


def test_calibration_mutations_change_exactly_their_target():
    proposal = replay_run(replay_case("gw6")).proposal
    assert S5_FACT in with_s5_reason(proposal) and S5_FACT not in proposal
    assert with_sim_basis(proposal).count(SIM_SENTENCE) == 1
    assert {g.case for g in GOLDS} == {"gw4", "gw5-orig", "gw5-rev", "gw6"}


# --- live -------------------------------------------------------------------


@pytest.mark.live
@claude
def test_judge_calibration():
    agree, cost = calibrate_judge()
    print(f"calibration ${cost:.4f}")
    assert agree


@pytest.mark.live
@claude
@pytest.mark.parametrize("case", [c for c in LIVE_CASES if c.default], ids=lambda c: c.id)
def test_live_case(case):
    try:
        outcome = run_live_case(case, judge=True, calibrated=True)
    except SourceError as exc:
        pytest.skip(str(exc))
    print(f"{case.id}: ${outcome.cost.total_cost_usd} judge {outcome.judge} → {outcome.out_dir}")
    assert [(r.id, r.evidence) for r in outcome.failures] == []


# --- --full case builders (free) --------------------------------------------


def _files(case_id):
    from evals.squad_optimizer.live import regenerate_players

    case = live_case(case_id)
    try:
        files = case_files(case)
    except SourceError as exc:
        pytest.skip(str(exc))
    files.update(regenerate_players(files, case.gw, case.allow_missing))
    return case, files


def test_x1_perturbs_the_market_and_asserts_its_preconditions():
    from evals.squad_optimizer.live import stack_expectations, views_of

    case, files = _files("X1-gw5-stack")
    bootstrap = json.loads(files["data/raw/gw5/bootstrap.json"])
    assert next(p for p in bootstrap["elements"] if p["id"] == 542)["now_cost"] == 61
    suggestions = files["data/suggestions.md"].decode()
    assert "| S7 | 2026-09-11 | 4 | 4 |" in suggestions and suggestions.endswith("|\n")
    expected = stack_expectations(case, *views_of(files, case.gw))
    assert expected["S3"] == expected["S4"] == "rejected" and expected["through"] == "7"
    assert expected["captain"] != "Haaland"


def test_reruns_start_from_the_rebuilt_proposal():
    from evals.squad_optimizer.runs import case_output

    try:
        revision = case_files(live_case("X2-gw5-revision"))
        reopen = case_files(live_case("X3-gw5-reopen"))
    except SourceError as exc:
        pytest.skip(str(exc))
    path = "data/decisions/gw5/squad-proposal.md"
    assert revision[path].decode() == case_output("gw5-orig")
    assert "data/decisions/gw5/review.md" in revision
    assert reopen[path].decode() == case_output("gw5-rev")


def test_x3_regenerates_with_the_unjudged_player_allowed():
    _, files = _files("X3-gw5-reopen")
    ids = {row["id"] for row in json.loads(files["data/analysis/gw5/players-MID.json"])}
    assert 131 not in ids


def test_briefs_for_the_full_cases():
    names = {}
    l3 = build_prompt(Path("/ws"), live_case("L3-gw4"), names)
    assert "Total sell value 99.6; bank 0.0; free transfers 1" in l3
    x2 = build_prompt(Path("/ws"), live_case("X2-gw5-revision"), names)
    assert "revision run after a REVISE: data/decisions/gw5/review.md" in x2
    x3 = build_prompt(Path("/ws"), live_case("X3-gw5-reopen"), names)
    assert "changed ids 423, 34, 36, 448; the affected analysis was re-run" in x3
