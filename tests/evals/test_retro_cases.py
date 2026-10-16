"""Live retro cases, built offline: the workspace manifest, the replay
recordings, each perturbation, and the validity guard — calibrate in a built
workspace reproduces the committed ledger."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from evals.harness.live import RunInvalid
from evals.retro_analyst import live
from evals.retro_analyst.cases import C21_RULE, LIVE_CASES, TEAM_ID, live_case
from fpl.corrections import build_digest
from fpl.state import parse_state


def files(case_id: str) -> dict[str, bytes]:
    return live.case_files(live_case(case_id))


def recordings(case_id: str) -> dict[str, bytes]:
    case = live_case(case_id)
    return live.recording_bytes(case, live.case_files(case))


def test_every_live_case_names_a_distinct_id():
    assert len({c.id for c in LIVE_CASES}) == len(LIVE_CASES)
    assert [c.id for c in LIVE_CASES if c.default] == ["L1-gw5", "L2-gw4"]


def test_workspace_holds_the_inputs_and_never_the_answer():
    placed = files("L1-gw5")
    for path in ("data/raw/gw6/bootstrap.json", "data/raw/gw6/.meta/bootstrap.json",
                 "data/decisions/gw5/final.md", "data/analysis/gw5/players-MID.json",
                 "data/retro/gw4.md", "data/retro/gw4-calibration.json", "data/entry.json"):
        assert path in placed, path
    for path in ("data/retro/gw5.md", "data/retro/gw5-calibration.json", "data/auth.json"):
        assert path not in placed
    assert json.loads(placed["data/entry.json"]) == {"team_id": TEAM_ID}


def test_recordings_serve_the_round_the_picks_and_the_history():
    served = recordings("L1-gw5")
    assert {"event/5/live.json", f"entry/{TEAM_ID}/event/5/picks.json",
            f"entry/{TEAM_ID}/history.json", "fixtures.json"} <= set(served)


def test_p1_changes_only_the_picks_recording():
    base, swapped = recordings("L1-gw5"), recordings("P1-picks-differ")
    assert files("L1-gw5") == files("P1-picks-differ")
    key = f"entry/{TEAM_ID}/event/5/picks.json"
    assert {k for k in base if base[k] != swapped[k]} == {key}
    picks = json.loads(swapped[key])["picks"]
    assert next(p["element"] for p in picks if p["is_captain"]) == 4
    assert next(p["element"] for p in picks if p["is_vice_captain"]) == 411
    assert live.fielded_picks(swapped[key]) == (frozenset(p["element"] for p in picks), 4, 411)


def test_p2_unchecks_the_round():
    boot = json.loads(files("P2-not-checked")["data/raw/gw5/bootstrap.json"])
    assert next(e for e in boot["events"] if e["id"] == 4)["data_checked"] is False


def test_p3_nulls_the_team_id():
    assert json.loads(files("P3-null-team")["data/entry.json"]) == {"team_id": None}


def test_p4_makes_c21_an_active_correction(tmp_path):
    root = tmp_path / "retro"
    root.mkdir()
    for path, data in files("P4-arithmetic-a3").items():
        if path.startswith("data/retro/gw") and path.endswith(".md"):
            (root / Path(path).name).write_bytes(data)
    digest = build_digest(root, before_round=5)
    assert 21 in [rule.number for rule in digest.active]
    gw4 = (root / "gw4.md").read_text("utf-8")
    assert gw4.index(C21_RULE) < gw4.index("## Running calibration stats")


def test_p5_pads_final_md_before_its_state_block():
    base = files("L1-gw5")["data/decisions/gw5/final.md"].decode()
    big = files("P5-big-final")["data/decisions/gw5/final.md"].decode()
    assert len(big.encode()) - len(base.encode()) >= 40_000
    assert big.index("## Rationale (extended)") < big.index("## STATE")
    assert parse_state(big) == parse_state(base)


# --- offline integration: the CLI in a built workspace ----------------------------


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    cache: dict[str, live.Prepared] = {}

    def get(case_id: str) -> live.Prepared:
        if case_id not in cache:
            cache[case_id] = live.prepare(live_case(case_id), sync=False,
                                          tmp_parent=tmp_path_factory.mktemp(case_id))
        return cache[case_id]

    return get


def cli(prepared: live.Prepared, *args: str) -> subprocess.CompletedProcess:
    assert prepared.ws.replay_dir is not None
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    env["FPL_REPLAY_DIR"] = str(prepared.ws.replay_dir)
    return subprocess.run([sys.executable, "-m", "fpl", *args], cwd=prepared.ws.root,
                          env=env, capture_output=True, text=True, check=False)


@pytest.mark.parametrize("case_id", ["L1-gw5", "L2-gw4"])
def test_calibrate_in_the_workspace_reproduces_the_committed_ledger(case_id, built):
    case = live_case(case_id)
    prepared = built(case_id)
    done = cli(prepared, "calibrate", "--gw", str(case.gw), "--round", str(case.round))
    assert done.returncode == 0, done.stderr
    live.check_validity(prepared)
    assert "squad misses (|err| > 3):" in done.stdout
    assert "predictions: commit " in done.stdout
    for command in (["picks", "--gw", str(case.gw), "--team-id", str(TEAM_ID),
                     "--event", str(case.round)],
                    ["entry-history", "--gw", str(case.gw), "--team-id", str(TEAM_ID)],
                    ["corrections", "--gw", str(case.gw), "--round", str(case.round)]):
        ran = cli(prepared, *command)
        assert ran.returncode == 0, (command, ran.stderr)


def test_the_validity_guard_refuses_a_drifted_ledger(tmp_path):
    prepared = live.prepare(live_case("L3-gw3"), tmp_parent=tmp_path, sync=False)
    ledger = prepared.ws.root / "data/retro/gw3-calibration.json"
    ledger.write_text(json.dumps({"round": 3}), "utf-8")
    with pytest.raises(RunInvalid, match="ledger"):
        live.check_validity(prepared)


def test_p2_makes_calibrate_refuse(built):
    prepared = built("P2-not-checked")
    done = cli(prepared, "calibrate", "--gw", "5", "--round", "4")
    assert done.returncode == 1 and "data-checked" in done.stderr


def test_the_actuals_for_every_squad_miss_are_recorded(built):
    prepared = built("L2-gw4")
    done = cli(prepared, "actuals", "--gw", "5", "--round", "4",
               "--ids", "1,4,229,237,106,411")
    assert done.returncode == 0, done.stderr
    assert "round 4 actuals (6 players)" in done.stdout
