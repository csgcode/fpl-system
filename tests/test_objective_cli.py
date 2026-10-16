"""CLI tests for `fpl objective`: labelled report lines, the PASS / FAIL /
error exits, the selling-price basis, and that it never needs the network."""

from __future__ import annotations

import json

import pytest

from fpl.__main__ import main
from fpl.objective_report import TIE_BREAK_LABEL
from fpl.store import SnapshotStore
from tests.factories import bootstrap_payload, event_payload, player_payload, team_payload
from tests.test_plan_cli import state_block

GW = 3
LAYOUT = {**{i: 1 for i in (1, 2)}, **{i: 2 for i in range(3, 8)},
          **{i: 3 for i in range(8, 13)}, **{i: 4 for i in range(13, 16)}, 16: 3, 17: 3}
POSITION_NAMES = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
CLUBS = ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF")
P_START = {11: 0.3, 12: 0.3, 16: 1.0, 17: 0.35, 18: 1.0, 2: 0.03}
PRICE = {16: 55, 17: 50, 18: 55}


TWIN = 18


def seed(root, *, twin=False):
    """`twin` adds P18, a MID with P16's price, start chance and fixtures."""
    store = SnapshotStore(root / "data" / "raw")
    layout = {**LAYOUT, TWIN: 3} if twin else LAYOUT
    players = [player_payload(id=pid, web_name=f"P{pid}", team=pid % 6 + 1, element_type=pos,
                              now_cost=PRICE.get(pid, 50))
               for pid, pos in layout.items()]
    teams = [team_payload(id=i + 1, short_name=name) for i, name in enumerate(CLUBS)]
    store.save(GW, "bootstrap", bootstrap_payload(
        elements=players, teams=teams, events=[event_payload(id=GW, is_next=True)]),
        "seed://test")
    gw_dir = root / "data" / "analysis" / f"gw{GW}"
    gw_dir.mkdir(parents=True)
    pairs = [("AAA", "BBB"), ("CCC", "DDD"), ("EEE", "FFF")]
    rows = []
    for g in range(GW, GW + 6):
        for home, away in pairs:
            for club, opp, venue in ((home, away, "H"), (away, home, "A")):
                rows.append({"club": club, "gw": g, "opp": opp, "venue": venue,
                             "lambda_att": 1.4, "lambda_def": 1.2, "p_cs": 0.3})
    (gw_dir / "fixtures.json").write_text(json.dumps({
        "schema_version": 1, "gw": GW, "base_lambda": {"home": 1.54, "away": 1.33},
        "ratings": {c: {"att": 1.0, "defw": 1.0} for c in CLUBS}, "fixtures": rows}))
    for pos, name in POSITION_NAMES.items():
        inputs = [{"id": pid, "name": f"P{pid}", "p_start": P_START.get(pid, 0.9),
                   "uncertainty": "LOW", "notes": ""}
                  for pid, p in layout.items() if p == pos]
        (gw_dir / f"inputs-{name}.json").write_text(json.dumps(
            {"schema_version": 1, "gw": GW, "position": name, "players": inputs}))
        assert main(["--data-root", str(root / "data" / "raw"), "ep", "--gw", str(GW),
                     "--position", name, "--analysis-root", str(root / "data" / "analysis"),
                     "--decisions-root", str(root / "data" / "decisions")]) == 0
    final = root / "data" / "decisions" / f"gw{GW - 1}" / "final.md"
    final.parent.mkdir(parents=True)
    # state_block captains id 14 and vices id 13: both must start.
    order = [1, 3, 4, 5, 8, 9, 10, 11, 13, 14, 15, 2, 6, 7, 12]
    picks = [(pid, slot) for slot, pid in enumerate(order, start=1)]
    final.write_text(state_block(GW - 1, picks), encoding="utf-8")
    return final


@pytest.fixture
def repo(tmp_path, monkeypatch, capsys):
    seed(tmp_path)
    capsys.readouterr()
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def tied(tmp_path, monkeypatch, capsys):
    """P16 and P18 tie on blend for P8's slot; P18 returned more often."""
    seed(tmp_path, twin=True)
    capsys.readouterr()
    path = tmp_path / "data" / "analysis" / f"gw{GW}" / "players-MID.json"
    rows = json.loads(path.read_text())
    returns = {16: [1, 5], TWIN: [4, 5]}
    for row in rows:
        if row["id"] in returns:
            row["returns5"] = returns[row["id"]]
    path.write_text(json.dumps(rows))
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run(*extra):
    return main(["objective", "--gw", str(GW), *extra])


def lines_of(out: str) -> dict[str, str]:
    found = {}
    for line in out.splitlines():
        key = line.split(":", 1)[0].strip()
        found.setdefault(key, line)
    return found


def test_prints_every_labelled_line_from_the_previous_final(repo, capsys):
    assert run() == 0
    out = capsys.readouterr().out
    first = out.splitlines()[0]
    assert first == (f"objective gw{GW} — horizon GW{GW}–GW{GW + 5}; "
                     f"squad from data/decisions/gw{GW - 1}/final.md")
    keys = lines_of(out)
    for key in ("sell basis", "baseline", "plan", "after plan, best single",
                "reference (greedy)", "verdict", "boundary pairs within 0.25", "bench"):
        assert key in keys, key
    assert keys["sell basis"].startswith("sell basis: now_cost — unverified")
    assert keys["baseline"].startswith("baseline: blend ")
    assert " prior " in keys["baseline"]
    assert "legal single moves: " in out and "top 10 by blend" in out
    assert keys["plan"].startswith("plan: none")
    assert f"GW{GW} XI " in out and "captain top 5:" in out
    assert "P2 " in keys["bench"] and "dead" in keys["bench"]


def test_a_passing_plan_exits_0_and_a_failing_one_exits_1(repo, capsys):
    assert run("--moves", "11:16") == 0
    out = capsys.readouterr().out
    assert "verdict: PASS" in out
    assert "  move P11 → P16: +" in out and "passes free gate" in out
    assert "transfers 1 (free 1, hits 0); FT next 1" in out
    assert run("--moves", "11:17") == 1
    out = capsys.readouterr().out
    assert "verdict: FAIL" in out


def test_moves_none_grades_banking(repo, capsys):
    assert run("--moves", "none") == 1
    assert "further free move passes" in capsys.readouterr().out


def test_relayed_sells_must_cover_the_whole_squad(repo, capsys):
    sells = ",".join(f"{pid}:5.0" for pid in range(1, 16))
    assert run("--sell", sells, "--bank", "0.5", "--free-transfers", "2") == 0
    out = capsys.readouterr().out
    assert "sell basis: relayed (Σ sell 75.0 + bank 0.5 = 75.5)" in out
    assert run("--sell", "1:5.0,2:5.0") == 1
    assert "error:" in capsys.readouterr().err


def test_an_illegal_move_is_an_error_naming_it(repo, capsys):
    assert run("--moves", "1:16") == 1
    err = capsys.readouterr().err
    assert err.startswith("error:") and "P1 → P16" in err and "position" in err


def test_json_format(repo, capsys):
    assert run("--moves", "11:16", "--format", "json") == 0
    document = json.loads(capsys.readouterr().out)
    assert document["verdict"] == "PASS"
    assert document["plan"]["moves"][0]["out"] == 11
    assert len(document["top"]) <= 10


def test_never_builds_a_gateway(repo, capsys):
    def refuse(store):
        raise AssertionError("objective must not build a data service")

    assert main(["objective", "--gw", str(GW)], service_factory=refuse) == 0


def test_singles_table_carries_p4_and_ret5_columns(tied, capsys):
    assert run() == 0
    out = capsys.readouterr().out
    rows = [line for line in out.splitlines() if line.startswith("  ") and " | " in line]
    twin = next(line for line in rows if "P11 → P18" in line)
    assert "| p4₃ - |" in twin and "| ret5 4/5 |" in twin


def test_tie_break_line_names_the_winner(tied, capsys):
    assert run() == 0
    out = capsys.readouterr().out
    line = next(line for line in out.splitlines() if line.startswith(TIE_BREAK_LABEL))
    assert "P8 → P16" in line and "winner P8 → P18" in line and "ret5 4/5 v 1/5" in line
    assert "reference (greedy): P8 → P18" in out


def test_plan_taking_the_winner_passes_and_says_so(tied, capsys):
    assert run("--moves", "8:18") == 0
    out = capsys.readouterr().out
    assert "verdict: PASS" in out
    assert "tie-break: plan takes P8 → P18" in out


def test_plan_taking_the_displaced_move_fails(tied, capsys):
    assert run("--moves", "8:16") == 1
    out = capsys.readouterr().out
    assert "departs from the tie-break" in out
    assert "tie-break: plan takes P8 → P16, not the winner P8 → P18" in out


def test_no_tie_in_band(repo, capsys):
    assert run("--moves", "11:16") == 0
    out = capsys.readouterr().out
    assert f"{TIE_BREAK_LABEL} none within 0.5" in out
    assert "tie-break: none in band" in out


def test_json_carries_tie_breaks(tied, capsys):
    assert run("--format", "json") == 0
    document = json.loads(capsys.readouterr().out)
    (tie,) = document["tie_breaks"]
    assert (tie["best"]["in"], tie["challenger"]["in"], tie["winner"]["in"]) == (16, TWIN, TWIN)
    assert tie["reason"] == "ret5 4/5 v 1/5"
