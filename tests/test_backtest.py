"""Backtest harness: loading a past round exactly as production saw it before
its deadline, refusing anything that could leak the outcome, and scoring it
under a model variant."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from fpl.backtest import (
    BacktestLine,
    code_drift,
    compare,
    cross_validate,
    load_round,
    score_round,
    ship_value,
    signed,
)
from fpl.ep import DEFAULT_CONFIG, build_predictions
from fpl.models import Position
from fpl.store import ARCHIVE_STAMP_FORMAT, SnapshotStore
from tests.factories import (
    bootstrap_payload,
    element_summary_payload,
    event_live_payload,
    event_payload,
    fixture_payload,
    live_element_payload,
    match_record_payload,
    player_payload,
    priors_doc,
    team_payload,
)
from tests.gitrepo import commit_files, init_repo

GW = 3
DEADLINE = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
BEFORE = datetime(2026, 9, 11, 18, 0, tzinfo=timezone.utc)
AFTER = datetime(2026, 9, 12, 11, 0, tzinfo=timezone.utc)
CHECKED = datetime(2026, 9, 15, 9, 0, tzinfo=timezone.utc)
LIVE_FETCH = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)


def _at(moment: datetime):
    return lambda: moment


def _events(*, checked: bool) -> list[dict]:
    return [
        event_payload(id=GW, name="Gameweek 3", deadline_time=DEADLINE.isoformat(),
                      is_next=not checked, finished=checked, data_checked=checked),
        event_payload(id=GW + 1, name="Gameweek 4", deadline_time="2026-09-19T10:00:00Z",
                      is_next=checked),
    ]


def _summary(rounds=(1, 2)) -> dict:
    return element_summary_payload(history=[
        match_record_payload(fixture=r, round=r, minutes=90) for r in rounds
    ])


def _fixtures_document() -> dict:
    return {
        "schema_version": 1,
        "gw": GW,
        "base_lambda": {"home": 1.54, "away": 1.33},
        "ratings": {"TST": {"att": 1.0, "defw": 1.0}, "OPP": {"att": 1.0, "defw": 1.0}},
        "fixtures": [
            {"club": club, "gw": g, "opp": opp, "venue": venue, "lambda_att": 1.5,
             "lambda_def": 1.0, "p_cs": 0.3}
            for g in range(GW, GW + 6)
            for club, opp, venue in (("TST", "OPP", "H"), ("OPP", "TST", "A"))
        ],
    }


def _inputs(position: str) -> dict:
    players = [] if position != "MID" else [
        {"id": 1, "name": "Alpha", "p_start": 0.9, "uncertainty": "LOW", "notes": "starter"}
    ]
    return {"schema_version": 1, "gw": GW, "position": position, "players": players}


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _save_live(raw: Path, *, final: bool | None = True, fetched: datetime = LIVE_FETCH) -> None:
    store = SnapshotStore(raw, now=_at(fetched))
    store.save(GW + 1, f"event-live-e{GW}",
               event_live_payload([live_element_payload(1, total_points=7)]), "seed://test")
    if final is not None:
        meta = raw / f"gw{GW + 1}" / ".meta" / f"event-live-e{GW}.json"
        _write_json(meta, {**json.loads(meta.read_text()), "final": final})


def _save_checking_bootstrap(raw: Path, fetched: datetime) -> None:
    SnapshotStore(raw, now=_at(fetched)).save(
        GW + 1, "bootstrap", bootstrap_payload(
            elements=[player_payload(id=1)], events=_events(checked=True)), "seed://test")


@pytest.fixture
def world(tmp_path):
    raw, analysis = tmp_path / "raw", tmp_path / "analysis"
    store = SnapshotStore(raw, now=_at(BEFORE))
    players = [
        player_payload(id=1, web_name="Alpha", team=1, element_type=3, now_cost=60),
        player_payload(id=2, web_name="Beta", team=2, element_type=3, now_cost=49, status="a"),
    ]
    teams = [team_payload(id=1, short_name="TST"), team_payload(id=2, name="Opp", short_name="OPP")]
    store.save(GW, "bootstrap",
               bootstrap_payload(elements=players, teams=teams, events=_events(checked=False)),
               "seed://test")
    store.save(GW, "fixtures", [fixture_payload(id=1, event=GW)], "seed://test")
    store.save(GW, "players/summary-1", _summary(), "seed://test")
    _write_json(analysis / f"gw{GW}" / "fixtures.json", _fixtures_document())
    for position in ("GKP", "DEF", "MID", "FWD"):
        _write_json(analysis / f"gw{GW}" / f"inputs-{position}.json", _inputs(position))
    _write_json(analysis / "club-priors.json",
                priors_doc({"TST": (1.0, 1.0, False), "OPP": (0.8, 1.2, True)}))
    _save_live(raw)
    return tmp_path, raw, analysis


def _load(raw: Path, analysis: Path, **kwargs):
    return load_round(data_root=raw, analysis_root=analysis, actuals_root=raw, gw=GW, **kwargs)


def test_load_round_reads_disk(world):
    _, raw, analysis = world
    data = _load(raw, analysis)
    assert data.gw == GW
    assert data.commit is None
    assert data.deadline == DEADLINE
    assert data.promoted == frozenset({"OPP"})
    assert data.live.by_id()[1].total_points == 7
    assert set(data.inputs) == {Position.GKP, Position.DEF, Position.MID, Position.FWD}
    assert [p.id for p in data.inputs[Position.MID].players] == [1]
    assert data.inputs[Position.DEF].players == []
    assert set(data.summaries) == {1}
    assert data.fixtures.gw == GW
    assert {p.id for p in data.bootstrap.elements} == {1, 2}


def test_load_round_refuses_a_summary_holding_the_round_itself(world):
    _, raw, analysis = world
    SnapshotStore(raw, now=_at(datetime(2026, 9, 11, 19, 0, tzinfo=timezone.utc))).save(
        GW, "players/summary-1", _summary(rounds=(1, 2, 3)), "seed://test")
    with pytest.raises(ValueError, match=r"summary-1.*leak|leak.*summary-1"):
        _load(raw, analysis)


def test_load_round_refuses_an_input_fetched_after_the_deadline(world):
    _, raw, analysis = world
    SnapshotStore(raw, now=_at(AFTER)).save(GW, "players/summary-1", _summary(), "seed://test")
    with pytest.raises(ValueError) as excinfo:
        _load(raw, analysis)
    message = str(excinfo.value)
    assert "players/summary-1.json" in message
    assert DEADLINE.isoformat() in message


def test_load_round_refuses_without_actuals(world):
    _, raw, analysis = world
    (raw / f"gw{GW + 1}" / f"event-live-e{GW}.json").unlink()
    with pytest.raises(ValueError, match=str(raw / f"gw{GW + 1}" / f"event-live-e{GW}.json")):
        _load(raw, analysis)


def test_load_round_refuses_non_final_actuals(world):
    _, raw, analysis = world
    _save_live(raw, final=None, fetched=datetime(2026, 9, 15, 11, 0, tzinfo=timezone.utc))
    with pytest.raises(ValueError, match="not final"):
        _load(raw, analysis)


def test_load_round_accepts_actuals_checked_by_an_earlier_bootstrap(world):
    _, raw, analysis = world
    _save_checking_bootstrap(raw, CHECKED)
    _save_live(raw, final=None, fetched=datetime(2026, 9, 15, 11, 0, tzinfo=timezone.utc))
    assert _load(raw, analysis).live.by_id()[1].total_points == 7


def test_load_round_accepts_a_check_seen_by_an_archived_bootstrap(world):
    _, raw, analysis = world
    _save_checking_bootstrap(raw, CHECKED)
    _save_live(raw, final=None, fetched=datetime(2026, 9, 15, 11, 0, tzinfo=timezone.utc))
    _save_checking_bootstrap(raw, datetime(2026, 9, 18, 9, 0, tzinfo=timezone.utc))
    archived = raw / f"gw{GW + 1}" / ".archive" / f"bootstrap-{CHECKED.strftime(ARCHIVE_STAMP_FORMAT)}.json"
    assert archived.is_file()
    assert _load(raw, analysis).live.by_id()[1].total_points == 7


def test_load_round_refuses_actuals_fetched_before_the_check(world):
    _, raw, analysis = world
    _save_live(raw, final=None, fetched=datetime(2026, 9, 15, 8, 0, tzinfo=timezone.utc))
    _save_checking_bootstrap(raw, CHECKED)
    with pytest.raises(ValueError, match=r"fpl event-live --gw 4 --round 3 --force"):
        _load(raw, analysis)


def _commit_world(root: Path, message: str) -> str:
    files = {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }
    return commit_files(root, files, message)


def test_load_round_refuses_drift_from_the_decision_commit(world):
    root, raw, analysis = world
    init_repo(root)
    final = root / "decisions" / f"gw{GW}" / "final.md"
    final.parent.mkdir(parents=True)
    final.write_text("# Final\n", encoding="utf-8")
    sha = _commit_world(root, "gw3: decision")
    assert _load(raw, analysis).commit == sha

    inputs = analysis / f"gw{GW}" / "inputs-MID.json"
    document = json.loads(inputs.read_text())
    document["players"][0]["p_start"] = 0.5
    inputs.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="analysis/gw3/inputs-MID.json") as refused:
        _load(raw, analysis)
    assert "--no-drift-check" in str(refused.value)
    assert "drift_check=False" not in str(refused.value)
    assert _load(raw, analysis, drift_check=False).gw == GW


def test_load_round_refuses_decisions_outside_the_repo(world, tmp_path_factory):
    root, raw, analysis = world
    init_repo(root)
    _commit_world(root, "seed")
    outside = tmp_path_factory.mktemp("elsewhere") / "decisions"
    with pytest.raises(ValueError) as refused:
        _load(raw, analysis, decisions_root=outside)
    assert str(outside) in str(refused.value)
    assert "--no-drift-check" in str(refused.value)
    assert _load(raw, analysis, decisions_root=outside, drift_check=False).gw == GW


def test_load_round_outside_git_warns_once_that_drift_is_unchecked(world):
    _, raw, analysis = world
    data = _load(raw, analysis)
    assert len([w for w in data.warnings if "drift" in w]) == 1


def _record_players(analysis: Path, ep_by_id: dict[int, float]) -> None:
    for position in ("GKP", "DEF", "MID", "FWD"):
        rows = [] if position != "MID" else [
            {"id": pid, "name": f"P{pid}", "team": "TST", "price": 6.0, "p_start": 0.9,
             "ep_gw": [ep], "uncertainty": "LOW"}
            for pid, ep in ep_by_id.items()
        ]
        _write_json(analysis / f"gw{GW}" / f"players-{position}.json", rows)


def test_code_drift_is_the_mean_gap_to_the_decision_record(world):
    root, raw, analysis = world
    data = _load(raw, analysis, drift_check=False)
    [alpha] = score_round(data, DEFAULT_CONFIG).lines
    init_repo(root)
    _record_players(analysis, {1: alpha.predicted + 0.5, 99: 3.0})
    final = root / "decisions" / f"gw{GW}" / "final.md"
    final.parent.mkdir(parents=True)
    final.write_text("# Final\n", encoding="utf-8")
    _commit_world(root, "gw3: decision")
    _record_players(analysis, {1: alpha.predicted})

    assert code_drift([alpha], analysis, root / "decisions", GW) == pytest.approx(0.5, abs=1e-9)


def test_code_drift_is_none_without_a_decision_record(world):
    _, raw, analysis = world
    data = _load(raw, analysis, drift_check=False)
    lines = score_round(data, DEFAULT_CONFIG).lines
    assert code_drift(lines, analysis, analysis.parent / "decisions", GW) is None


def _add_beta(raw: Path, analysis: Path) -> None:
    """Beta (OPP, promoted) gets an inputs row, a summary with no PL history
    and an actuals row."""
    inputs = analysis / f"gw{GW}" / "inputs-MID.json"
    document = json.loads(inputs.read_text())
    document["players"].append(
        {"id": 2, "name": "Beta", "p_start": 0.6, "uncertainty": "MED", "notes": "rotation"})
    inputs.write_text(json.dumps(document), encoding="utf-8")
    SnapshotStore(raw, now=_at(BEFORE)).save(
        GW, "players/summary-2",
        element_summary_payload(history_past=[], history=[
            match_record_payload(fixture=r, round=r, minutes=30) for r in (1, 2)]),
        "seed://test")
    store = SnapshotStore(raw, now=_at(LIVE_FETCH))
    store.save(GW + 1, f"event-live-e{GW}", event_live_payload([
        live_element_payload(1, total_points=7),
        live_element_payload(2, total_points=1),
    ]), "seed://test")
    meta = raw / f"gw{GW + 1}" / ".meta" / f"event-live-e{GW}.json"
    _write_json(meta, {**json.loads(meta.read_text()), "final": True})


def _override_prior_weight(analysis: Path, weight: float) -> None:
    inputs = analysis / f"gw{GW}" / "inputs-MID.json"
    document = json.loads(inputs.read_text())
    document["players"][0].update(overrides={"prior_weight": weight}, reason="fixed blend")
    inputs.write_text(json.dumps(document), encoding="utf-8")


def test_score_round_matches_documents_and_live(world):
    _, raw, analysis = world
    data = _load(raw, analysis)
    score = score_round(data, DEFAULT_CONFIG)
    documents = build_predictions(
        data.bootstrap, data.summaries, data.fixtures, data.inputs[Position.MID],
        gw=GW, allow_missing=frozenset({2}),
    ).to_documents()
    [alpha] = score.lines
    assert isinstance(alpha, BacktestLine)
    assert alpha.id == 1
    assert alpha.predicted == documents[0]["ep_gw"][0]
    assert alpha.actual == 7
    assert alpha.error == pytest.approx(alpha.actual - alpha.predicted, abs=5e-4)


def test_score_round_scores_despite_coverage_gaps(world):
    _, raw, analysis = world
    score = score_round(_load(raw, analysis), DEFAULT_CONFIG)
    assert [line.id for line in score.lines] == [1]
    assert any("id 2 Beta" in warning for warning in score.warnings)


def test_lines_carry_slices(world):
    _, raw, analysis = world
    _add_beta(raw, analysis)
    lines = {line.id: line for line in score_round(_load(raw, analysis), DEFAULT_CONFIG).lines}
    assert {(l.round, l.club, l.promoted, l.no_history) for l in lines.values()} == {
        (GW, "TST", False, False),
        (GW, "OPP", True, True),
    }
    assert lines[2].p4 is None


def test_unchanged_player_gives_zero_difference(world):
    _, raw, analysis = world
    _override_prior_weight(analysis, 0.7)
    data = _load(raw, analysis)
    [at_600] = score_round(data, replace(DEFAULT_CONFIG, blend_k=600.0)).lines
    [at_300] = score_round(data, replace(DEFAULT_CONFIG, blend_k=300.0)).lines
    assert at_600.predicted == at_300.predicted


def test_blend_k_moves_a_player_without_an_override(world):
    _, raw, analysis = world
    data = _load(raw, analysis)
    [at_600] = score_round(data, replace(DEFAULT_CONFIG, blend_k=600.0)).lines
    [at_300] = score_round(data, replace(DEFAULT_CONFIG, blend_k=300.0)).lines
    assert at_600.predicted != at_300.predicted


def test_score_round_refuses_an_unknown_inputs_policy(world):
    _, raw, analysis = world
    with pytest.raises(ValueError, match="inputs policy"):
        score_round(_load(raw, analysis), DEFAULT_CONFIG, inputs_policy="drop")


def _line(error: float, *, id: int, round: int = GW, club: str | None = None,
          position: str = "MID", promoted: bool = False,
          no_history: bool = False) -> BacktestLine:
    club = club or f"C{id}"
    return BacktestLine(
        id=id, name=f"P{id}", team=club, position=position, price=5.0, uncertainty="LOW",
        p_start=0.9, predicted=-error, actual=0, error=error, minutes=90, started=True,
        round=round, club=club, promoted=promoted, no_history=no_history,
    )


def _sides(baseline_errors, variant_errors, **kwargs):
    baseline = [_line(e, id=i, **kwargs) for i, e in enumerate(baseline_errors, start=1)]
    variant = [_line(e, id=i, **kwargs) for i, e in enumerate(variant_errors, start=1)]
    return baseline, variant


def _alternating(n: int, magnitude: float) -> list[float]:
    return [magnitude if i % 2 == 0 else -magnitude for i in range(n)]


def _reason_keys(comparison) -> list[str]:
    return [reason.split(":", 1)[0] for reason in comparison.reasons]


def test_compare_reports_paired_delta_and_gate():
    clubs = {1: ("TST", "MID", True, False), 2: ("TST", "MID", False, True),
             3: ("OPP", "DEF", False, False), 4: ("OPP", "DEF", False, False)}

    def side(errors):
        return [_line(e, id=i, club=clubs[i][0], position=clubs[i][1],
                      promoted=clubs[i][2], no_history=clubs[i][3])
                for i, e in zip(clubs, errors)]

    result = compare(side([2, -2, 4, -4]), side([1, -1, 2, -2]))
    se = math.sqrt(2) / 4
    assert result.n == 4
    assert result.delta_mae == -1.5
    assert result.se == pytest.approx(se)
    assert result.ci == pytest.approx((-1.5 - 1.96 * se, -1.5 + 1.96 * se))
    assert result.round_deltas == {3: -1.5}
    assert result.round_wins == (1, 1)
    assert result.beats is True
    assert result.reasons == ()
    assert (result.baseline.mae, result.variant.mae) == (3.0, 1.5)
    mid, defenders = result.by_position["MID"], result.by_position["DEF"]
    assert (mid.n, mid.baseline.mae, mid.variant.mae, mid.delta_mae) == (2, 2.0, 1.0, -1.0)
    assert (defenders.n, defenders.baseline.bias, defenders.variant.mae) == (2, 0.0, 2.0)
    assert set(result.slices) == {"promoted", "no_history"}
    assert (result.slices["promoted"].n, result.slices["promoted"].variant.bias) == (1, 1.0)
    assert (result.slices["no_history"].n, result.slices["no_history"].delta_mae) == (1, -1.0)


def test_compare_slice_with_no_lines_is_none():
    baseline, variant = _sides([2, -2], [1, -1])
    result = compare(baseline, variant)
    assert result.slices == {"promoted": None, "no_history": None}


def test_gate_fails_on_ci_only():
    result = compare(*_sides([4, 0.1], [1, 3.0]))
    assert result.delta_mae == pytest.approx(-0.05)
    assert _reason_keys(result) == ["ci"]
    assert result.reasons == (f"ci: upper {signed(result.ci[1], 3)} ≥ 0",)
    assert result.reasons[0].startswith("ci: upper +")
    assert result.beats is False


def test_gate_fails_on_bias_only():
    result = compare(*_sides([2, -2, 2, -2], [1.06, -0.94, 1.06, -0.94]))
    assert result.delta_mae == pytest.approx(-1.0)
    assert result.se == pytest.approx(0.03)
    assert _reason_keys(result) == ["bias"]
    assert result.reasons == ("bias: |b_v| 0.060 > |b_b| 0.000 + 0.05",)


def test_gate_fails_on_position_only():
    mids = _alternating(20, 2), _alternating(20, 1)
    baseline = [_line(e, id=i) for i, e in enumerate(mids[0], start=1)]
    variant = [_line(e, id=i) for i, e in enumerate(mids[1], start=1)]
    baseline += [_line(e, id=100 + i, position="DEF") for i, e in enumerate([1, -1])]
    variant += [_line(e, id=100 + i, position="DEF") for i, e in enumerate([1.05, -1.05])]
    result = compare(baseline, variant)
    assert result.delta_mae == pytest.approx(-19.9 / 22)
    assert result.by_position["DEF"].delta_mae == pytest.approx(0.05)
    assert _reason_keys(result) == ["position DEF"]
    assert result.reasons == ("position DEF: ΔMAE +0.050 > +0.02",)


def test_gate_fails_on_effect_only():
    result = compare(*_sides(_alternating(100, 2), _alternating(100, 1.995)))
    assert result.delta_mae == pytest.approx(-0.005)
    assert result.se == pytest.approx(0.0, abs=1e-12)
    assert _reason_keys(result) == ["effect"]
    assert result.reasons == ("effect: ΔMAE \u22120.0050 > \u22120.01",)


def test_gate_fails_on_round_wins_only():
    baseline, variant = [], []
    for r, (before, after) in {3: (2, 1), 4: (1, 1.01), 5: (1, 1.01)}.items():
        for i, (b, v) in enumerate(zip(_alternating(10, before), _alternating(10, after))):
            baseline.append(_line(b, id=i, round=r, club=f"C{r}-{i}"))
            variant.append(_line(v, id=i, round=r, club=f"C{r}-{i}"))
    result = compare(baseline, variant)
    assert result.delta_mae == pytest.approx(-9.8 / 30)
    assert result.round_wins == (1, 3)
    assert result.round_deltas == pytest.approx({3: -1.0, 4: 0.01, 5: 0.01})
    assert _reason_keys(result) == ["rounds"]
    assert result.reasons == ("rounds: won 1 of 3, need 2",)


def test_signed_uses_the_minus_sign():
    assert signed(-0.0043, 4) == "\u22120.0043"
    assert signed(0.05, 3) == "+0.050"
    assert signed(-0.01, 2) == "\u22120.01"
    assert "-" not in signed(-1.5, 1)


def test_compare_refuses_unpaired_lines():
    baseline, variant = _sides([2, -2], [1, -1])
    with pytest.raises(ValueError, match="unpaired"):
        compare(baseline, variant[:1])
    with pytest.raises(ValueError, match="unpaired"):
        compare(baseline, [*variant, _line(1, id=1, round=GW + 1)])


def test_compare_refuses_duplicate_lines():
    baseline, variant = _sides([2, -2], [1, -1])
    with pytest.raises(ValueError, match="duplicate"):
        compare([*baseline, baseline[0]], [*variant, variant[0]])


def _round_lines(mae_by_round: dict[int, float], *, n: int = 4) -> list[BacktestLine]:
    return [_line(e, id=i, round=r, club=f"C{r}-{i}")
            for r, mae in mae_by_round.items()
            for i, e in enumerate(_alternating(n, mae), start=1)]


def test_loro_picks_per_fold_and_scores_the_held_out_round():
    lines_by_value = {
        "a": _round_lines({3: 2.0, 4: 2.0, 5: 1.0}),
        "b": _round_lines({3: 1.0, 4: 1.5, 5: 2.0}),
    }
    cv_lines, picks = cross_validate(lines_by_value)
    assert picks == {3: "a", 4: "a", 5: "b"}
    expected = [line for line in lines_by_value["a"] if line.round in (3, 4)]
    expected += [line for line in lines_by_value["b"] if line.round == 5]
    assert sorted(cv_lines, key=lambda l: (l.round, l.id)) == expected


def test_loro_tie_goes_to_the_earlier_grid_entry():
    lines_by_value = {
        "b": _round_lines({3: 1.0, 4: 1.5, 5: 2.0}),
        "a": _round_lines({3: 2.0, 4: 2.0, 5: 1.0}),
    }
    assert cross_validate(lines_by_value)[1][4] == "b"


def test_loro_accepts_tuple_grid_values():
    lines_by_value = {
        (600.0, None): _round_lines({3: 2.0, 4: 2.0}),
        (300.0, 2.0): _round_lines({3: 1.0, 4: 1.0}),
    }
    assert cross_validate(lines_by_value)[1] == {3: (300.0, 2.0), 4: (300.0, 2.0)}


def test_loro_refuses_fewer_than_two_rounds_or_mismatched_rounds():
    with pytest.raises(ValueError, match="two rounds"):
        cross_validate({"a": _round_lines({3: 1.0})})
    with pytest.raises(ValueError, match="rounds"):
        cross_validate({"a": _round_lines({3: 1.0, 4: 1.0}),
                        "b": _round_lines({3: 1.0, 5: 1.0})})
    with pytest.raises(ValueError, match="no grid"):
        cross_validate({})


def test_ship_value_mode_then_grid_order():
    assert ship_value({3: "a", 4: "a", 5: "b"}, ["a", "b"]) == "a"
    assert ship_value({3: "a", 4: "b"}, ["b", "a"]) == "b"
    assert ship_value({3: "a", 4: "b"}, ["a", "b"]) == "a"
    grid = [(600.0, None), (300.0, 2.0), (450.0, None)]
    assert ship_value({3: (300.0, 2.0), 4: (450.0, None), 5: (300.0, 2.0)}, grid) == (300.0, 2.0)
    assert ship_value({3: (450.0, None), 4: (300.0, 2.0)}, grid) == (300.0, 2.0)


def test_ship_value_refuses_a_pick_outside_the_grid():
    with pytest.raises(ValueError, match="not in the grid"):
        ship_value({3: "c"}, ["a", "b"])
    with pytest.raises(ValueError, match="no picks"):
        ship_value({}, ["a"])


def test_loro_ignores_float_noise_between_decimal_equal_maes():
    lines_by_value = {
        "a": [_line(e, id=i, round=r, club=f"C{r}-{i}")
              for r in (3, 4) for i, e in enumerate([0.1, 0.2], start=1)],
        "b": [_line(e, id=i, round=r, club=f"C{r}-{i}")
              for r in (3, 4) for i, e in enumerate([0.3, 0.0], start=1)],
    }
    assert (0.1 + 0.2) / 2 != (0.3 + 0.0) / 2
    assert cross_validate(lines_by_value)[1] == {3: "a", 4: "a"}
