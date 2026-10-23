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
    hypothesis,
    load_round,
    p4_calibration,
    score_round,
    ship_value,
    signed,
    strip_attack_mult,
)
from fpl.ep import DEFAULT_CONFIG, InputsDocument, build_predictions
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
    assert alpha.p4 == documents[0]["p4_gw"][0]


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
    assert all(0.0 <= line.p4 <= 1.0 for line in lines.values())


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


def _inputs_document(rows: list[dict]) -> InputsDocument:
    return InputsDocument.model_validate(
        {"schema_version": 1, "gw": GW, "position": "MID", "players": rows})


def test_strip_attack_mult_removes_only_the_named_rows():
    inputs = _inputs_document([
        {"id": 5, "p_start": 0.9, "uncertainty": "LOW",
         "overrides": {"attack_mult": 0.8, "xg90": 0.3}, "reason": "role and club"},
        {"id": 6, "p_start": 0.9, "uncertainty": "LOW",
         "overrides": {"attack_mult": 0.8}, "reason": "club"},
        {"id": 7, "p_start": 0.9, "uncertainty": "LOW",
         "overrides": {"attack_mult": 0.9}, "reason": "club"},
    ])
    stripped = strip_attack_mult(inputs, ids={5, 7})
    rows = {row.id: row for row in stripped.players}
    assert rows[5].overrides.attack_mult is None
    assert rows[5].overrides.xg90 == 0.3
    assert rows[5].reason == "role and club"
    assert rows[7].overrides is None
    assert rows[7].reason is None
    assert rows[6] == inputs.players[1]
    InputsDocument.model_validate(stripped.model_dump())
    assert inputs.players[0].overrides.attack_mult == 0.8


def _set_attack_mult(analysis: Path, mults: dict[int, float]) -> None:
    inputs = analysis / f"gw{GW}" / "inputs-MID.json"
    document = json.loads(inputs.read_text())
    for row in document["players"]:
        if row["id"] in mults:
            row.update(overrides={"attack_mult": mults[row["id"]]}, reason="club discount")
    inputs.write_text(json.dumps(document), encoding="utf-8")


def _predicted(data, **kwargs) -> dict[int, float]:
    return {line.id: line.predicted for line in score_round(data, DEFAULT_CONFIG, **kwargs).lines}


def test_inputs_policy_drop_promoted(world):
    _, raw, analysis = world
    _add_beta(raw, analysis)
    _set_attack_mult(analysis, {1: 0.7, 2: 0.7})
    data = _load(raw, analysis)
    kept = _predicted(data)
    dropped = _predicted(data, inputs_policy="drop_promoted")
    assert dropped[1] == kept[1]
    assert dropped[2] > kept[2]

    path = analysis / f"gw{GW}" / "inputs-MID.json"
    document = json.loads(path.read_text())
    document["players"][1].pop("overrides")
    document["players"][1].pop("reason")
    path.write_text(json.dumps(document), encoding="utf-8")
    assert _predicted(_load(raw, analysis))[2] == dropped[2]


def test_inputs_policy_drop_no_history(world):
    _, raw, analysis = world
    _add_beta(raw, analysis)
    _write_json(analysis / "club-priors.json",
                priors_doc({"TST": (1.0, 1.0, True), "OPP": (0.8, 1.2, False)}))
    _set_attack_mult(analysis, {1: 0.7, 2: 0.7})
    data = _load(raw, analysis)
    kept = _predicted(data)
    no_history = _predicted(data, inputs_policy="drop_no_history")
    promoted = _predicted(data, inputs_policy="drop_promoted")
    assert no_history[1] == kept[1] and no_history[2] > kept[2]
    assert promoted[1] > kept[1] and promoted[2] == kept[2]
    lines = {line.id: line for line in score_round(data, DEFAULT_CONFIG,
                                                   inputs_policy="drop_no_history").lines}
    assert (lines[1].no_history, lines[2].no_history) == (False, True)


def _line(error: float, *, id: int, round: int = GW, club: str | None = None,
          position: str = "MID", promoted: bool = False,
          no_history: bool = False, p4: float | None = None,
          actual: int = 0, p_start: float = 0.9) -> BacktestLine:
    club = club or f"C{id}"
    return BacktestLine(
        id=id, name=f"P{id}", team=club, position=position, price=5.0, uncertainty="LOW",
        p_start=p_start, predicted=actual - error, actual=actual, error=error, minutes=90,
        started=True, round=round, club=club, promoted=promoted, no_history=no_history, p4=p4,
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


def _slice_sides(groups) -> tuple[list[BacktestLine], list[BacktestLine]]:
    """`groups`: (count, position, promoted, baseline error, variant error);
    every line in its own club."""
    baseline, variant = [], []
    i = 0
    for count, position, promoted, before, after in groups:
        for _ in range(count):
            i += 1
            kwargs = dict(id=i, club=f"C{i}", position=position, promoted=promoted)
            baseline.append(_line(before, **kwargs))
            variant.append(_line(after, **kwargs))
    return baseline, variant


def test_slice_gate_and_hypothesis_fields():
    baseline, variant = _slice_sides([(40, "MID", True, 2.0, 1.0),
                                      (20, "MID", False, 2.0, 2.0),
                                      (20, "MID", False, -2.0, -2.0)])
    assert compare(baseline, variant).slice_gate is None
    result = compare(baseline, variant, gate_slice="promoted")
    assert result.beats
    gate = result.slice_gate
    assert (gate.name, gate.n, gate.verdict, gate.reasons) == ("promoted", 40, "PASS", ())
    assert gate.delta_mae == pytest.approx(-1.0)
    assert (gate.baseline_bias, gate.variant_bias) == pytest.approx((2.0, 1.0))
    assert gate.pooled_positions is False
    assert hypothesis(result, policy=False) == "supported"


def test_slice_gate_pools_positions_below_the_minimum():
    baseline, variant = _slice_sides([(36, "MID", True, 2.0, 1.0),
                                      (4, "DEF", True, 2.0, 2.5),
                                      (40, "MID", False, 2.0, 2.0)])
    gate = compare(baseline, variant, gate_slice="promoted").slice_gate
    assert gate.pooled_positions is True
    assert gate.verdict == "PASS"

    baseline, variant = _slice_sides([(10, "MID", True, 2.0, 1.95),
                                      (30, "DEF", True, 2.0, 2.05),
                                      (40, "MID", False, 2.0, 1.0)])
    gate = compare(baseline, variant, gate_slice="promoted").slice_gate
    assert gate.pooled_positions is True
    assert [reason.split(":", 1)[0] for reason in gate.reasons] == [
        "ci", "position pooled", "effect"]


def test_slice_gate_is_not_applicable_below_the_minimum_lines():
    baseline, variant = _slice_sides([(39, "MID", True, 2.0, 1.0),
                                      (41, "MID", False, 2.0, 2.0)])
    result = compare(baseline, variant, gate_slice="promoted")
    assert (result.slice_gate.n, result.slice_gate.verdict) == (39, "n/a")
    assert result.slice_gate.reasons == ()
    assert hypothesis(result, policy=False) == "supported"

    baseline, variant = _slice_sides([(40, "MID", False, 2.0, 1.0)])
    result = compare(baseline, variant, gate_slice="promoted")
    assert (result.slice_gate.n, result.slice_gate.verdict) == (0, "n/a")
    assert hypothesis(result, policy=False) == "not supported"


def test_hypothesis_needs_under_rating_a_smaller_bias_and_both_gates():
    over_rated = _slice_sides([(40, "MID", True, -2.0, -1.0), (40, "MID", False, 2.0, 2.0)])
    assert hypothesis(compare(*over_rated, gate_slice="promoted"), policy=False) == "not supported"

    bias_flips = _slice_sides([(40, "MID", True, 1.0, -1.0), (40, "MID", False, 2.0, 1.0)])
    assert hypothesis(compare(*bias_flips, gate_slice="promoted"), policy=False) == "not supported"

    overall_fails = _slice_sides([(40, "MID", True, 2.0, 1.0), (40, "MID", False, 2.0, 3.5)])
    result = compare(*overall_fails, gate_slice="promoted")
    assert not result.beats and result.slice_gate.verdict == "PASS"
    assert hypothesis(result, policy=False) == "not supported"

    slice_fails = _slice_sides([(40, "MID", True, 2.0, 1.995), (40, "MID", False, 2.0, 1.0)])
    result = compare(*slice_fails, gate_slice="promoted")
    assert result.beats and result.slice_gate.verdict == "FAIL"
    assert hypothesis(result, policy=False) == "not supported"


def test_policy_hypothesis_is_judged_on_its_slice_without_harm_overall():
    """User decision 2026-10-23: a policy is `supported` when the baseline
    under-rates the slice, the variant shrinks its |bias|, the slice gate
    passes and the overall ΔMAE is not worse; the overall gate need not pass."""
    overall_unproven = _slice_sides([(40, "MID", True, 2.0, 1.0), (40, "MID", False, 2.0, 2.9)])
    result = compare(*overall_unproven, gate_slice="promoted")
    assert not result.beats and result.delta_mae <= 0
    assert result.slice_gate.verdict == "PASS"
    assert hypothesis(result, policy=True) == "supported"
    assert hypothesis(result, policy=False) == "not supported"

    no_harm = _slice_sides([(40, "MID", True, 2.0, 1.0), (40, "MID", False, 2.0, 3.0)])
    result = compare(*no_harm, gate_slice="promoted")
    assert result.delta_mae == 0
    assert hypothesis(result, policy=True) == "supported"

    harm = _slice_sides([(40, "MID", True, 2.0, 1.0), (40, "MID", False, 2.0, 3.5)])
    result = compare(*harm, gate_slice="promoted")
    assert result.delta_mae > 0 and result.slice_gate.verdict == "PASS"
    assert hypothesis(result, policy=True) == "not supported"


def test_policy_hypothesis_needs_a_slice_pass_and_an_under_rated_slice():
    too_few = _slice_sides([(39, "MID", True, 2.0, 1.0), (41, "MID", False, 2.0, 2.0)])
    result = compare(*too_few, gate_slice="promoted")
    assert result.slice_gate.verdict == "n/a"
    assert hypothesis(result, policy=True) == "not supported"
    assert hypothesis(result, policy=False) == "supported"

    slice_fails = _slice_sides([(40, "MID", True, 2.0, 1.995), (40, "MID", False, 2.0, 1.0)])
    result = compare(*slice_fails, gate_slice="promoted")
    assert result.slice_gate.verdict == "FAIL" and result.delta_mae < 0
    assert hypothesis(result, policy=True) == "not supported"

    over_rated = _slice_sides([(40, "MID", True, -2.0, -1.0), (40, "MID", False, 2.0, 2.0)])
    result = compare(*over_rated, gate_slice="promoted")
    assert result.slice_gate.verdict == "PASS"
    assert hypothesis(result, policy=True) == "not supported"

    bias_flips = _slice_sides([(40, "MID", True, 1.0, -1.5), (40, "MID", False, 2.0, 1.0)])
    assert hypothesis(compare(*bias_flips, gate_slice="promoted"), policy=True) == "not supported"


def test_compare_refuses_an_unknown_slice():
    with pytest.raises(ValueError, match="slice"):
        compare(*_sides([2, -2], [1, -1]), gate_slice="nope")


def _p4_lines(rows, *, p_start: float = 0.9) -> list[BacktestLine]:
    """(round, position, p4, returned) → lines; a return scores 6, else 1."""
    return [_line(0.0, id=i, round=r, position=pos, p4=p4, actual=6 if hit else 1,
                  p_start=p_start)
            for i, (r, pos, p4, hit) in enumerate(rows, start=1)]


def test_p4_brier_against_a_leave_one_round_out_base_rate():
    lines = _p4_lines([(3, "MID", 0.8, True), (3, "MID", 0.2, False),
                       (4, "MID", 0.5, True), (4, "MID", 0.5, False)])
    [(position, mid)] = p4_calibration(lines).items()
    assert position == "MID"
    assert mid.n == 4
    assert mid.p4_brier == pytest.approx((0.04 + 0.04 + 0.25 + 0.25) / 4)
    assert mid.base_rate_brier == pytest.approx(0.25)
    assert mid.base_rate == "leave-one-round-out"
    assert mid.skill == pytest.approx(1 - 0.145 / 0.25)


def test_p4_base_rate_comes_from_the_other_rounds_only():
    lines = _p4_lines([(3, "DEF", 0.5, True), (3, "DEF", 0.5, True),
                       (4, "DEF", 0.5, False), (4, "DEF", 0.5, False)])
    calibration = p4_calibration(lines)["DEF"]
    assert calibration.base_rate_brier == pytest.approx(1.0)
    assert calibration.skill == pytest.approx(0.75)


def test_p4_reliability_bins_mean_p4_against_observed_rate():
    lines = _p4_lines([(3, "FWD", 0.1, False), (3, "FWD", 0.15, True),
                       (4, "FWD", 0.9, True), (4, "FWD", 1.0, True)])
    bins = p4_calibration(lines)["FWD"].reliability
    assert [b.n for b in bins] == [2, 0, 0, 0, 2]
    assert (bins[0].lower, bins[0].upper) == (0.0, 0.2)
    assert bins[0].mean_p4 == pytest.approx(0.125)
    assert bins[0].observed == pytest.approx(0.5)
    assert (bins[1].mean_p4, bins[1].observed) == (None, None)
    assert bins[4].mean_p4 == pytest.approx(0.95)
    assert bins[4].observed == 1.0


def test_p4_skill_needs_a_second_round():
    calibration = p4_calibration(_p4_lines([(3, "GKP", 0.3, False), (3, "GKP", 0.6, True)]))
    assert calibration["GKP"].p4_brier == pytest.approx((0.09 + 0.16) / 2)
    assert (calibration["GKP"].base_rate_brier, calibration["GKP"].skill) == (None, None)


def test_p4_starters_subset_scores_only_likely_starters_against_their_own_base_rate():
    starters = _p4_lines([(3, "MID", 0.8, True), (3, "MID", 0.2, False),
                          (4, "MID", 0.5, True), (4, "MID", 0.5, False)])
    benched = [line.model_copy(update={"id": 100 + line.id, "p_start": 0.1})
               for line in _p4_lines([(3, "MID", 0.0, False), (4, "MID", 0.0, False)])]
    mid = p4_calibration([*starters, *benched])["MID"]
    assert mid.n == 6
    sub = mid.starters
    assert sub.n == 4
    assert sub.p4_brier == pytest.approx(0.145)
    assert sub.base_rate_brier == pytest.approx(0.25)
    assert sub.skill == pytest.approx(1 - 0.145 / 0.25)
    assert sub.base_rate == "leave-one-round-out"
    assert len(sub.reliability) == 5
    assert sub.starters is None


def test_p4_starters_threshold_is_inclusive_at_one_half():
    lines = _p4_lines([(3, "DEF", 0.5, True), (4, "DEF", 0.5, False)], p_start=0.5)
    assert p4_calibration(lines)["DEF"].starters.n == 2


def test_p4_starters_is_none_when_no_line_is_a_likely_starter():
    lines = _p4_lines([(3, "FWD", 0.1, False), (4, "FWD", 0.1, False)], p_start=0.2)
    assert p4_calibration(lines)["FWD"].starters is None


def test_p4_starters_skill_needs_a_second_round():
    lines = [*_p4_lines([(3, "GKP", 0.3, False), (3, "GKP", 0.6, True)]),
             *_p4_lines([(4, "GKP", 0.0, False)], p_start=0.1)]
    sub = p4_calibration(lines)["GKP"].starters
    assert sub.n == 2
    assert (sub.base_rate_brier, sub.skill) == (None, None)


def test_p4_calibration_skips_lines_without_p4():
    lines = [*_p4_lines([(3, "MID", 0.8, True), (4, "MID", 0.2, False)]),
             _line(0.0, id=99, round=4, position="MID")]
    assert p4_calibration(lines)["MID"].n == 2
    assert p4_calibration([_line(0.0, id=1)]) == {}


def test_compare_carries_the_variants_p4_calibration():
    baseline = _p4_lines([(3, "MID", 0.5, True), (4, "MID", 0.5, False)])
    variant = _p4_lines([(3, "MID", 0.9, True), (4, "MID", 0.1, False)])
    result = compare(baseline, variant)
    assert result.p4 == p4_calibration(variant)
    assert result.p4["MID"].p4_brier == pytest.approx(0.01)
