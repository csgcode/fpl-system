"""Backtest harness: loading a past round exactly as production saw it before
its deadline, refusing anything that could leak the outcome."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from fpl.backtest import load_round
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

    with pytest.raises(ValueError, match="analysis/gw3/inputs-MID.json"):
        _load(raw, analysis)
    assert _load(raw, analysis, drift_check=False).gw == GW


def test_load_round_outside_git_warns_once_that_drift_is_unchecked(world):
    _, raw, analysis = world
    data = _load(raw, analysis)
    assert len([w for w in data.warnings if "drift" in w]) == 1
