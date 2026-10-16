"""CLI tests for `fpl calibrate`: argument wiring, the data-checked gate,
the written ledger file, and printed output — over a fake gateway."""

from __future__ import annotations

import hashlib
import json

from fpl.__main__ import main
from fpl.decision_record import write_lock
from fpl.api import BASE_URL, FplApi
from fpl.service import FplDataService
from fpl.store import SnapshotStore
from tests.factories import (
    bootstrap_payload,
    event_live_payload,
    event_payload,
    live_element_payload,
)
from tests.test_calibrate import POSITION_FILES, prediction_row
from tests.gitrepo import commit_files, init_repo
from tests.test_service import FakeGateway

LIVE_1_URL = f"{BASE_URL}/event/1/live/"


def run(argv, data_root, gateway):
    """Runs in worktree mode unless argv picks a mode: most tests seed no git history."""
    if "calibrate" in argv and "--predictions-from" not in argv:
        argv = [*argv, "--predictions-from", "worktree"]
    return run_committed(argv, data_root, gateway)


def run_committed(argv, data_root, gateway):
    def factory(store: SnapshotStore) -> FplDataService:
        return FplDataService(
            FplApi(gateway), store, throttle_s=0.0, sleep=lambda _: None
        )

    return main(["--data-root", str(data_root), *argv], service_factory=factory)


def seed_bootstrap(data_root, *, gw=2, checked_rounds=(1,)):
    events = [
        event_payload(
            id=r, finished=True, data_checked=r in checked_rounds, is_next=False
        )
        for r in (1, 2)
    ] + [event_payload(id=3, is_next=True)]
    SnapshotStore(data_root).save(
        gw, "bootstrap", bootstrap_payload(events=events), "seed://test"
    )


def write_analysis(root, gw, rows_by_position):
    analysis_dir = root / f"gw{gw}"
    analysis_dir.mkdir(parents=True)
    for position in POSITION_FILES:
        (analysis_dir / f"players-{position}.json").write_text(
            json.dumps(rows_by_position.get(position, [])), encoding="utf-8"
        )


def write_final(root, gw):
    lines = "\n".join(
        f"  - {{id: {i}, name: P{i}, position: {i}, "
        f"captain: {'true' if i == 1 else 'false'}, "
        f"vice: {'true' if i == 2 else 'false'}}}"
        for i in range(1, 16)
    )
    directory = root / f"gw{gw}"
    directory.mkdir(parents=True)
    (directory / "final.md").write_text(
        "# Final\n\n```yaml\n"
        f"gw: {gw}\nteam_id: null\nteam_value: 100.0\nbank: 0.0\n"
        "free_transfers_banked: 1\nchip: null\nchips_used: []\n"
        f"transfers_made: []\npicks:\n{lines}\n```\n",
        encoding="utf-8",
    )


def setup_round(tmp_path, *, with_final=True, checked=True, points=None):
    points = points or (lambda i: i % 5)
    data_root = tmp_path / "raw"
    seed_bootstrap(data_root, checked_rounds=(1,) if checked else ())
    write_analysis(
        tmp_path / "analysis",
        1,
        {"MID": [prediction_row(id=i, name=f"P{i}") for i in range(1, 16)]},
    )
    if with_final:
        write_final(tmp_path / "decisions", 1)
    gateway = FakeGateway(
        {
            LIVE_1_URL: event_live_payload(
                [live_element_payload(element_id=i, total_points=points(i)) for i in range(1, 16)]
            )
        }
    )
    argv = [
        "calibrate", "--gw", "2", "--round", "1",
        "--analysis-root", str(tmp_path / "analysis"),
        "--decisions-root", str(tmp_path / "decisions"),
        "--retro-root", str(tmp_path / "retro"),
    ]
    return data_root, gateway, argv


def test_calibrate_writes_ledger_and_prints_summary(tmp_path, capsys):
    data_root, gateway, argv = setup_round(tmp_path)
    assert run(argv, data_root, gateway) == 0
    ledger_path = tmp_path / "retro" / "gw1-calibration.json"
    document = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert document["round"] == 1
    assert document["overall"]["n"] == 15
    assert document["squad"]["captain"]["chosen_id"] == 1
    out = capsys.readouterr().out
    assert "overall" in out
    assert str(ledger_path) in out


def block_after(out, header):
    lines = out.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(header)) + 1
    block = []
    for line in lines[start:]:
        if not line.startswith(" "):
            break
        block.append(line)
    return block


def test_calibrate_prints_one_row_per_squad_slot(tmp_path, capsys):
    data_root, gateway, argv = setup_round(tmp_path)
    assert run(argv, data_root, gateway) == 0
    rows = block_after(capsys.readouterr().out, "squad rows")
    assert len(rows) == 15
    captain_row = next(row for row in rows if " P1 " in row)
    tokens = captain_row.split()
    assert tokens[-1] == "C" and tokens[1] == "XI"
    assert (tokens[5], tokens[7], tokens[-2]) == ("3.50", "1", "90")
    vice_row = next(row for row in rows if " P2 " in row)
    assert vice_row.endswith("VC")
    bench_row = next(row for row in rows if " P12 " in row)
    assert "bench" in bench_row


def test_calibrate_splits_misses_by_sign(tmp_path, capsys):
    # predicted 3.50 everywhere: id 3 scores 12 (err +8.5), ids 5/10/15 score 0 (err -3.5)
    data_root, gateway, argv = setup_round(
        tmp_path, points=lambda i: 12 if i == 3 else i % 5
    )
    assert run(argv, data_root, gateway) == 0
    out = capsys.readouterr().out
    assert "under-predicted (err > +3): 1 players" in out
    under = block_after(out, "under-predicted")
    assert len(under) == 1 and " P3 " in under[0] and "+8.50" in under[0]
    assert "over-predicted (err < -3): 3 players" in out
    over = block_after(out, "over-predicted")
    assert [row.split()[1] for row in over] == ["P5", "P10", "P15"]


def test_calibrate_reports_no_misses_explicitly(tmp_path, capsys):
    data_root, gateway, argv = setup_round(tmp_path, points=lambda i: 3)
    assert run(argv, data_root, gateway) == 0
    out = capsys.readouterr().out
    assert "under-predicted (err > +3): none" in out
    assert "over-predicted (err < -3): none" in out


def test_calibrate_refuses_unchecked_round(tmp_path, capsys):
    data_root, gateway, argv = setup_round(tmp_path, checked=False)
    assert run(argv, data_root, gateway) == 1
    assert "data-checked" in capsys.readouterr().err
    assert not (tmp_path / "retro" / "gw1-calibration.json").exists()
    assert gateway.calls == []          # gate refuses before any fetch


def test_calibrate_without_final_md_warns_and_skips_squad(tmp_path, capsys):
    data_root, gateway, argv = setup_round(tmp_path, with_final=False)
    assert run(argv, data_root, gateway) == 0
    document = json.loads(
        (tmp_path / "retro" / "gw1-calibration.json").read_text(encoding="utf-8")
    )
    assert document["squad"] is None
    assert "final.md" in capsys.readouterr().err


def test_calibrate_pools_prior_rounds_into_cumulative(tmp_path):
    data_root, gateway, argv = setup_round(tmp_path)
    assert run(argv, data_root, gateway) == 0

    write_analysis(
        tmp_path / "analysis",
        2,
        {"MID": [prediction_row(id=1, name="P1")]},
    )
    seed_bootstrap(data_root, checked_rounds=(1, 2))
    gateway.responses[f"{BASE_URL}/event/2/live/"] = event_live_payload(
        [live_element_payload(element_id=1, total_points=7)]
    )
    argv2 = [arg if arg != "1" else "2" for arg in argv]
    assert run(argv2, data_root, gateway) == 0
    document = json.loads(
        (tmp_path / "retro" / "gw2-calibration.json").read_text(encoding="utf-8")
    )
    assert document["cumulative"]["rounds"] == [1, 2]
    assert document["cumulative"]["overall"]["n"] == 16


def output_lines(tmp_path, capsys, **kwargs):
    data_root, gateway, argv = setup_round(tmp_path, **kwargs)
    assert run(argv, data_root, gateway) == 0
    return capsys.readouterr().out.splitlines()


def test_table_prints_aggregates_and_cumulative_contiguously(tmp_path, capsys):
    data_root, gateway, argv = setup_round(tmp_path)
    assert run(argv, data_root, gateway) == 0
    write_final(tmp_path / "decisions", 2)
    write_analysis(tmp_path / "analysis", 2,
                   {"MID": [prediction_row(id=i, name=f"P{i}") for i in range(1, 16)]})
    seed_bootstrap(data_root, checked_rounds=(1, 2))
    gateway.responses[f"{BASE_URL}/event/2/live/"] = event_live_payload(
        [live_element_payload(element_id=i, total_points=3) for i in range(1, 16)])
    capsys.readouterr()
    assert run([arg if arg != "1" else "2" for arg in argv], data_root, gateway) == 0
    lines = capsys.readouterr().out.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("group"))
    end = next(i for i, line in enumerate(lines) if line.startswith("cumulative"))
    assert all(not line.startswith("squad") for line in lines[start:end + 1])
    assert lines[end + 1].startswith("squad XI")
    assert lines[end + 2].startswith("captain:")
    assert lines[end + 3].startswith("squad rows")


def test_minutes_line_prints_gap(tmp_path, capsys):
    lines = output_lines(tmp_path, capsys)
    minutes = next(line for line in lines if line.startswith("minutes:"))
    # 15 players at p_start 0.9 → 13.5 expected; all 15 started
    assert minutes.endswith("expected starts 13.5, actual 15, gap -1.5")


def test_squad_rows_carry_err_start_and_p_start(tmp_path, capsys):
    lines = output_lines(tmp_path, capsys)
    assert ("squad rows (slot role id name pred act err start p_start min; "
            "* = |err| > 3):") in lines
    rows = block_after("\n".join(lines), "squad rows")
    captain = next(row for row in rows if " P1 " in row).split()
    assert captain[:3] == ["1", "XI", "1"]
    assert captain[4:] == ["pred", "3.50", "act", "1", "err", "-2.50", "start", "Y",
                           "p_start", "0.90", "min", "90", "C"]


def test_squad_row_star_marks_err_over_3_even_when_it_prints_3_00(tmp_path, capsys):
    data_root, gateway, argv = setup_round(tmp_path, points=lambda i: 6 if i == 4 else 3)
    rows_path = tmp_path / "analysis" / "gw1" / "players-MID.json"
    rows = json.loads(rows_path.read_text(encoding="utf-8"))
    rows[3]["ep_gw"] = [2.998] * 6
    rows_path.write_text(json.dumps(rows), encoding="utf-8")
    assert run(argv, data_root, gateway) == 0
    squad = block_after(capsys.readouterr().out, "squad rows")
    row = next(r for r in squad if " P4 " in r)
    assert "err  +3.00* start" in row
    assert all("*" not in r for r in squad if " P4 " not in r)


def test_squad_misses_line_lists_starred_rows_in_slot_order(tmp_path, capsys):
    lines = output_lines(tmp_path, capsys, points=lambda i: {3: 12, 9: 0}.get(i, 3))
    rows_end = next(i for i, line in enumerate(lines) if line.startswith("squad rows")) + 16
    assert lines[rows_end] == "squad misses (|err| > 3): 3 P3 +8.50, 9 P9 -3.50"


def test_squad_misses_none(tmp_path, capsys):
    lines = output_lines(tmp_path, capsys, points=lambda i: 3)
    assert "squad misses (|err| > 3): none" in lines
    tails = [i for i, line in enumerate(lines) if "-predicted (err" in line]
    misses_at = lines.index("squad misses (|err| > 3): none")
    assert all(i > misses_at for i in tails)


# --- the decision record ----------------------------------------------------

ALPHA_MID = "analysis/gw1/players-MID.json"


def mid_rows(alpha_ep):
    rows = [prediction_row(id=i, name=f"P{i}") for i in range(1, 16)]
    rows[0] = prediction_row(id=1, name="P1", ep_gw=[alpha_ep] * 6)
    return json.dumps(rows)


def setup_committed_round(tmp_path, *, rewrite=True, commit_final=True):
    data_root, gateway, argv = setup_round(tmp_path)
    repo = init_repo(tmp_path)
    decided = {f"analysis/gw1/players-{pos}.json": "[]" for pos in POSITION_FILES}
    decided[ALPHA_MID] = mid_rows(3.0)
    if commit_final:
        decided["decisions/gw1/final.md"] = (tmp_path / "decisions/gw1/final.md").read_text()
    sha = commit_files(repo, decided, "gw1: decision")
    if rewrite:
        commit_files(repo, {ALPHA_MID: mid_rows(5.0)}, "ep: x")
    return data_root, gateway, argv, sha


def ledger(tmp_path):
    return json.loads((tmp_path / "retro/gw1-calibration.json").read_text(encoding="utf-8"))


def alpha_predicted(document):
    return next(p["predicted"] for p in document["players"] if p["id"] == 1)


def test_calibrate_reads_predictions_from_the_decision_commit(tmp_path, capsys):
    data_root, gateway, argv, sha = setup_committed_round(tmp_path)

    assert run_committed(argv, data_root, gateway) == 0

    document = ledger(tmp_path)
    assert alpha_predicted(document) == 3.0
    assert document["predictions_source"].startswith("commit ")
    assert document["drifted"] == [ALPHA_MID]
    captured = capsys.readouterr()
    lines = [line for line in captured.out.splitlines() if line.startswith("predictions:")]
    assert lines == [f"predictions: commit {sha[:12]} (drift: 1 file)"]
    warnings = [line for line in captured.err.splitlines() if line.startswith("WARNING:")]
    assert warnings == [
        f"WARNING: 1 prediction file changed after decision commit {sha[:12]} — "
        f"calibrated the decision record: {ALPHA_MID}"
    ]


def test_calibrate_prints_no_warning_without_drift(tmp_path, capsys):
    data_root, gateway, argv, sha = setup_committed_round(tmp_path, rewrite=False)

    assert run_committed(argv, data_root, gateway) == 0

    captured = capsys.readouterr()
    assert f"predictions: commit {sha[:12]} (drift: none)" in captured.out.splitlines()
    assert "WARNING" not in captured.err


def test_calibrate_refuses_without_a_decision_commit(tmp_path, capsys):
    data_root, gateway, argv, _ = setup_committed_round(tmp_path, commit_final=False)

    assert run_committed(argv, data_root, gateway) == 1
    assert "--predictions-from worktree" in capsys.readouterr().err


def test_calibrate_still_refuses_an_unchecked_round_first(tmp_path, capsys):
    data_root, gateway, argv = setup_round(tmp_path, checked=False)

    assert run_committed(argv, data_root, gateway) == 1
    assert "data-checked" in capsys.readouterr().err


def test_calibrate_worktree_mode_reads_the_files_on_disk(tmp_path, capsys):
    data_root, gateway, argv, _ = setup_committed_round(tmp_path)
    (tmp_path / ALPHA_MID).write_text(mid_rows(5.0), encoding="utf-8")

    assert run_committed([*argv, "--predictions-from", "worktree"], data_root, gateway) == 0

    document = ledger(tmp_path)
    assert alpha_predicted(document) == 5.0
    assert document["predictions_source"] == "worktree"
    assert "predictions: worktree" in capsys.readouterr().out.splitlines()


def setup_locked_round(tmp_path):
    data_root, gateway, argv = setup_round(tmp_path)
    analysis_dir = tmp_path / "analysis" / "gw1"
    (analysis_dir / "players-MID.json").write_text(mid_rows(3.0), encoding="utf-8")
    lock_path = tmp_path / "decisions" / "gw1" / "predictions.lock.json"
    assert write_lock(analysis_dir, lock_path, 1) == []
    return data_root, gateway, argv, analysis_dir, lock_path


def test_calibrate_prefers_the_lock(tmp_path, capsys):
    data_root, gateway, argv, analysis_dir, lock_path = setup_locked_round(tmp_path)
    rows = json.loads(mid_rows(5.0))
    rows[0]["p_start"] = 0.2
    (analysis_dir / "players-MID.json").write_text(json.dumps(rows), encoding="utf-8")

    assert run_committed(argv, data_root, gateway) == 0

    document = ledger(tmp_path)
    alpha = next(p for p in document["players"] if p["id"] == 1)
    assert (alpha["predicted"], alpha["p_start"]) == (3.0, 0.9)
    lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()[:12]
    assert document["predictions_source"] == f"lock {lock_sha}"
    assert document["drifted"] == [str(analysis_dir / "players-MID.json")]
    captured = capsys.readouterr()
    assert f"predictions: lock {lock_sha} (drift: 1 file)" in captured.out.splitlines()
    warnings = [line for line in captured.err.splitlines() if line.startswith("WARNING:")]
    assert warnings == [
        f"WARNING: 1 prediction file changed after predictions lock {lock_sha} — "
        f"calibrated the decision record: {analysis_dir / 'players-MID.json'}"
    ]


def test_calibrate_reads_an_untouched_lock_without_drift(tmp_path, capsys):
    data_root, gateway, argv, _, lock_path = setup_locked_round(tmp_path)

    assert run_committed(argv, data_root, gateway) == 0

    document = ledger(tmp_path)
    assert alpha_predicted(document) == 3.0
    assert document["drifted"] == []
    assert "WARNING" not in capsys.readouterr().err


def test_calibrate_refuses_a_lock_id_missing_on_disk(tmp_path, capsys):
    data_root, gateway, argv, analysis_dir, _ = setup_locked_round(tmp_path)
    rows = json.loads(mid_rows(3.0))
    (analysis_dir / "players-MID.json").write_text(json.dumps(rows[1:]), encoding="utf-8")

    assert run_committed(argv, data_root, gateway) == 1

    err = capsys.readouterr().err
    assert "player id 1 " in err and "--predictions-from worktree" in err
