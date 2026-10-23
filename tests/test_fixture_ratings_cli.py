"""CLI tests for `fixtures-rate`: it is local-only, so the gateway here
explodes if anything reaches for the network."""

from __future__ import annotations

import json

from fpl.__main__ import main
from fpl.api import FplApi
from fpl.ep import parse_fixtures
from fpl.service import FplDataService
from fpl.store import SnapshotStore
from tests.factories import (
    bootstrap_payload,
    element_summary_payload,
    event_live_payload,
    fixture_payload,
    player_payload,
    priors_doc,
    summary_row,
    team_payload,
)

GW = 2
CLUBS = {"AAA": (1, 1.2, 0.8, False), "BBB": (2, 0.8, 1.2, True)}


class NoNetworkGateway:
    def get_json(self, url: str):
        raise AssertionError(f"fixtures-rate must not touch the network, but fetched {url}")


def seed(tmp_path, *, priors=True, live=True):
    store = SnapshotStore(tmp_path / "raw")
    teams = [team_payload(id=i, short_name=c) for c, (i, *_r) in CLUBS.items()]
    players = [player_payload(id=11, team=1), player_payload(id=21, team=2)]
    store.save(GW, "bootstrap", bootstrap_payload(elements=players, teams=teams), "seed://t")
    fixtures = [fixture_payload(id=1, event=1, team_h=1, team_a=2, finished=True)]
    fixtures += [fixture_payload(id=10 + g, event=g, team_h=1 + g % 2, team_a=2 - g % 2)
                 for g in range(2, 8)]
    store.save(GW, "fixtures", fixtures, "seed://t")
    store.save(GW, "players/summary-11", element_summary_payload(
        history=[summary_row(fixture=1, round=1, was_home=True, expected_goals="2.00")]), "seed://t")
    store.save(GW, "players/summary-21", element_summary_payload(
        history=[summary_row(fixture=1, round=1, was_home=False, expected_goals="0.50")]), "seed://t")
    if live:
        store.save(2, "event-live-e1", event_live_payload([]), "seed://t")
    analysis = tmp_path / "analysis"
    analysis.mkdir()
    if priors:
        doc = priors_doc({c: (att, defw, prom) for c, (_, att, defw, prom) in CLUBS.items()})
        (analysis / "club-priors.json").write_text(json.dumps(doc), encoding="utf-8")
    return analysis


def run(tmp_path, *extra):
    def factory(store: SnapshotStore) -> FplDataService:
        return FplDataService(FplApi(NoNetworkGateway()), store)

    return main(["--data-root", str(tmp_path / "raw"), "fixtures-rate", "--gw", str(GW),
                 "--analysis-root", str(tmp_path / "analysis"), "--history-from", "summaries",
                 *extra],
                service_factory=factory)


def test_writes_both_files_and_prints_wrote_lines(tmp_path, capsys):
    analysis = seed(tmp_path)
    assert run(tmp_path) == 0
    out = capsys.readouterr().out
    json_path = analysis / "gw2" / "fixtures.json"
    tables_path = analysis / "gw2" / "fixtures-tables.md"
    assert f"wrote {json_path}" in out and f"wrote {tables_path}" in out
    document = parse_fixtures(json.loads(json_path.read_text(encoding="utf-8")))
    assert document.gw == GW and len(document.fixtures) == 12
    assert tables_path.read_text(encoding="utf-8").startswith("# GW2 fixture tables")


def test_league_xg_and_clip_lines(tmp_path, capsys):
    seed(tmp_path)
    run(tmp_path)
    out = capsys.readouterr().out
    assert "gw2 ratings: 1 rounds, 1 matches, 2 summaries, 0 player-rounds (0.00 xG)" in out
    assert "clipped: " in out and " of 4 implied ratings (round 1: " in out
    assert "league xG per match: home 2.00, away 0.50, total 2.50 vs base 2.87 (-12.9%)" in out
    assert "window gw2–7: 12 rows, blanks: none, doubles: none, unscheduled fixtures: 0" in out


def test_json_format_prints_the_document(tmp_path, capsys):
    seed(tmp_path)
    assert run(tmp_path, "--format", "json") == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)["gw"] == GW
    assert "wrote " in captured.err


def test_missing_priors_refuses_with_hint(tmp_path, capsys):
    seed(tmp_path, priors=False)
    assert run(tmp_path) == 1
    err = capsys.readouterr().err
    assert "error: no club priors at" in err
    assert ("hint: at GW1 the fixture analyst writes data/analysis/club-priors.json "
            "(agents/fixture-analyst.md § Priors)") in err
    assert not (tmp_path / "analysis" / "gw2").exists()


def test_missing_event_live_refuses_naming_round_and_hint(tmp_path, capsys):
    seed(tmp_path, live=False)
    assert run(tmp_path) == 1
    err = capsys.readouterr().err
    assert "error: no snapshot 'event-live-e1' for gw2 — round 1 cannot be rated" in err
    assert ("hint: fetch it with 'event-live --gw 2 --round 1' "
            "(the data collector's event-live step)") in err


def test_invalid_priors_refuse(tmp_path, capsys):
    analysis = seed(tmp_path)
    doc = json.loads((analysis / "club-priors.json").read_text(encoding="utf-8"))
    del doc["clubs"]["BBB"]
    (analysis / "club-priors.json").write_text(json.dumps(doc), encoding="utf-8")
    assert run(tmp_path) == 1
    assert "error: club priors missing for BBB" in capsys.readouterr().err


def test_never_builds_a_gateway(tmp_path, capsys):
    seed(tmp_path)

    def factory(store):
        raise AssertionError("fixtures-rate built a data service")

    code = main(["--data-root", str(tmp_path / "raw"), "fixtures-rate", "--gw", str(GW),
                 "--analysis-root", str(tmp_path / "analysis"), "--history-from", "summaries"],
                service_factory=factory)
    assert code == 0
