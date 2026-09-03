"""CLI tests for `fpl calibrate`: argument wiring, the data-checked gate,
the written ledger file, and printed output — over a fake gateway."""

from __future__ import annotations

import json

from fpl.__main__ import main
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
from tests.test_service import FakeGateway

LIVE_1_URL = f"{BASE_URL}/event/1/live/"


def run(argv, data_root, gateway):
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
    assert (tokens[5], tokens[7], tokens[9]) == ("3.50", "1", "90")
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
