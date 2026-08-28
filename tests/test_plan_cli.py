"""CLI tests for `plan`: it is local-only, so the gateway here explodes if
anything reaches for the network."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fpl.__main__ import main
from fpl.api import FplApi
from fpl.plan import SCHEMA_VERSION
from fpl.service import FplDataService
from fpl.store import SnapshotStore
from tests.test_plan import SQUAD, bootstrap, player_name


class NoNetworkGateway:
    def get_json(self, url: str):
        raise AssertionError(f"plan must not touch the network, but fetched {url}")


def run(argv, tmp_path):
    def factory(store: SnapshotStore) -> FplDataService:
        return FplDataService(FplApi(NoNetworkGateway()), store)

    return main(
        ["--data-root", str(tmp_path / "raw"), *argv], service_factory=factory
    )


def state_block(
    gw: int,
    picks: list[tuple[int, int]],
    *,
    team_id: str = "8455344",
    chip: str | None = None,
    chip_plan: list[str] | None = None,
    transfers: list[str] | None = None,
    include_picks: bool = True,
) -> str:
    lines = [
        f"gw: {gw}",
        f"team_id: {team_id}",
        "team_value: 99.9",
        "bank: 1.0",
        "free_transfers_banked: 1",
        "chips_used: []",
    ]
    if transfers:
        lines.append("transfers_made:")
        lines.extend(f"  {row}" for row in transfers)
    else:
        lines.append("transfers_made: []")
    if chip is not None:
        lines.append(f"chip: {chip}")
    if chip_plan:
        lines.append("chip_plan:")
        lines.extend(f"  {row}" for row in chip_plan)
    if include_picks:
        lines.append("picks:")
        lines.extend(
            f"  - {{id: {pid}, name: {player_name(pid)}, position: {slot}, "
            f"captain: {str(pid == 14).lower()}, vice: {str(pid == 13).lower()}}}"
            for pid, slot in picks
        )
    return "# Final\n\nprose\n\n## STATE\n\n```yaml\n" + "\n".join(lines) + "\n```\n"


def squad_slots(swap: tuple[int, int] | None = None) -> list[tuple[int, int]]:
    rows = [(pid, slot) for pid, (_, _, slot) in SQUAD.items()]
    if swap is None:
        return rows
    out_id, in_id = swap
    return [(in_id if pid == out_id else pid, slot) for pid, slot in rows]


def seed(tmp_path: Path, **kwargs) -> Path:
    """Writes the bootstrap snapshot plus gw1/gw2 final.md, returns gw2's."""
    SnapshotStore(tmp_path / "raw").save(
        2, "bootstrap", bootstrap().model_dump(mode="json"), "seed://test"
    )
    decisions = tmp_path / "decisions"
    (decisions / "gw1").mkdir(parents=True, exist_ok=True)
    (decisions / "gw2").mkdir(parents=True, exist_ok=True)
    previous = kwargs.pop("previous", None)
    if previous is not None:
        (decisions / "gw1" / "final.md").write_text(previous, encoding="utf-8")
    final = decisions / "gw2" / "final.md"
    final.write_text(
        kwargs.pop("final", None) or state_block(2, squad_slots()), encoding="utf-8"
    )
    return final


def plan_json(capsys) -> dict:
    out = capsys.readouterr().out
    return json.loads(out[out.index("{") :])


# --- json output ------------------------------------------------------------


def test_plan_prints_a_self_describing_json_document(tmp_path, capsys):
    final = seed(tmp_path)
    assert run(["plan", "--gw", "2", "--from-final", str(final), "--format", "json"], tmp_path) == 0
    payload = plan_json(capsys)
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["gw"] == 2
    assert payload["team_id"] == 8455344
    assert payload["chip"] is None
    assert payload["formation"] == "3-4-3"
    assert payload["bench"] == [2, 6, 7, 12]
    assert payload["captain"] == {"id": 14, "name": "E14"}
    assert payload["vice"] == {"id": 13, "name": "E13"}
    assert payload["deadline"].startswith("2026-08-22T12:00:00")
    assert payload["price_resolution"] == "live"
    assert payload["source"].endswith("gw2/final.md")
    assert len(payload["picks"]) == 15


def test_plan_picks_carry_every_field_the_poster_needs(tmp_path, capsys):
    final = seed(tmp_path)
    run(["plan", "--gw", "2", "--from-final", str(final), "--format", "json"], tmp_path)
    first = plan_json(capsys)["picks"][0]
    assert set(first) == {
        "element",
        "name",
        "club",
        "position",
        "slot",
        "is_captain",
        "is_vice_captain",
        "now_cost",
        "starts",
    }
    assert first == {
        "element": 1,
        "name": "E1",
        "club": "T1",
        "position": "GKP",
        "slot": 1,
        "is_captain": False,
        "is_vice_captain": False,
        "now_cost": 4.1,
        "starts": True,
    }


def test_transfers_use_the_previous_gws_picks_diff(tmp_path, capsys):
    final = seed(
        tmp_path,
        final=state_block(
            2, squad_slots(swap=(12, 20)), transfers=["- {out: E12, in: E20, cost: 0}"]
        ),
        previous=state_block(1, squad_slots()),
    )
    assert run(["plan", "--gw", "2", "--from-final", str(final), "--format", "json"], tmp_path) == 0
    payload = plan_json(capsys)
    assert payload["transfer_source"] == "picks-diff"
    assert payload["transfers"] == [
        {
            "out": {"id": 12, "name": "E12"},
            "in": {"id": 20, "name": "E20"},
            "cost": 0,
            "purchase_price_at_plan": 6.0,
            "selling_price": None,
        }
    ]


def test_transfers_fall_back_to_names_when_the_previous_final_lacks_picks(
    tmp_path, capsys
):
    final = seed(
        tmp_path,
        final=state_block(
            2, squad_slots(swap=(12, 20)), transfers=["- {out: E12, in: E20, cost: 0}"]
        ),
        previous=state_block(1, [], include_picks=False),
    )
    assert run(["plan", "--gw", "2", "--from-final", str(final), "--format", "json"], tmp_path) == 0
    payload = plan_json(capsys)
    assert payload["transfer_source"] == "state-names"
    assert payload["transfers"][0]["in"]["id"] == 20


def test_a_missing_previous_final_is_not_an_error(tmp_path, capsys):
    final = seed(tmp_path)
    assert run(["plan", "--gw", "2", "--from-final", str(final), "--format", "json"], tmp_path) == 0
    assert plan_json(capsys)["generated_from"]["previous_final"] is None


def test_ambiguous_transfer_name_exits_non_zero_with_the_candidates(tmp_path, capsys):
    final = seed(
        tmp_path,
        final=state_block(
            2, squad_slots(swap=(12, 30)), transfers=["- {out: E12, in: Hughes, cost: 0}"]
        ),
    )
    assert run(["plan", "--gw", "2", "--from-final", str(final)], tmp_path) == 1
    err = capsys.readouterr().err
    assert "ambiguous transfer name 'Hughes'" in err
    assert "id 30" in err and "id 31" in err


def test_chip_and_chip_plan_are_emitted_with_their_windows(tmp_path, capsys):
    final = seed(
        tmp_path,
        final=state_block(
            2,
            squad_slots(),
            chip="bboost",
            chip_plan=["- {chip: 3xc, gw: 5, status: provisional}"],
        ),
    )
    assert run(["plan", "--gw", "2", "--from-final", str(final), "--format", "json"], tmp_path) == 0
    payload = plan_json(capsys)
    assert payload["chip"] == "bboost"
    assert payload["chip_plan"] == [
        {
            "chip": "3xc",
            "gw": 5,
            "status": "provisional",
            "start_event": 1,
            "stop_event": 19,
        }
    ]
    assert {"name": "wildcard", "start_event": 2, "stop_event": 19} in payload[
        "chips_available"
    ]


def test_chip_outside_its_window_exits_non_zero(tmp_path, capsys):
    final = seed(tmp_path, final=state_block(2, squad_slots(), chip="freehit"))
    store = SnapshotStore(tmp_path / "raw")
    payload = bootstrap().model_dump(mode="json")
    payload["chips"] = [{"name": "freehit", "start_event": 20, "stop_event": 38}]
    store.save(2, "bootstrap", payload, "seed://test")
    assert run(["plan", "--gw", "2", "--from-final", str(final)], tmp_path) == 1
    assert "outside every window" in capsys.readouterr().err


def test_bootstrap_snapshot_age_is_reported(tmp_path, capsys):
    final = seed(tmp_path)
    run(["plan", "--gw", "2", "--from-final", str(final), "--format", "json"], tmp_path)
    assert plan_json(capsys)["bootstrap_snapshot_age_hours"] == pytest.approx(
        0.0, abs=0.1
    )


# --- output targets ---------------------------------------------------------


def test_out_writes_the_json_file_and_prints_its_path(tmp_path, capsys):
    final = seed(tmp_path)
    target = tmp_path / "decisions" / "gw2" / "plan.json"
    assert run(
        ["plan", "--gw", "2", "--from-final", str(final), "--out", str(target)],
        tmp_path,
    ) == 0
    written = json.loads(target.read_text(encoding="utf-8"))
    assert written["gw"] == 2
    assert str(target) in capsys.readouterr().out


def test_default_format_is_a_human_readable_table(tmp_path, capsys):
    final = seed(tmp_path)
    assert run(["plan", "--gw", "2", "--from-final", str(final)], tmp_path) == 0
    out = capsys.readouterr().out
    assert "gw2" in out
    assert "3-4-3" in out
    assert "chip: none" in out
    assert "E14" in out and "(C)" in out
    assert "bench" in out


def test_table_lists_transfers_and_warnings(tmp_path, capsys):
    final = seed(
        tmp_path,
        final=state_block(
            2, squad_slots(swap=(12, 20)), team_id="null",
            transfers=["- {out: E12, in: E20, cost: 0}"],
        ),
    )
    assert run(["plan", "--gw", "2", "--from-final", str(final)], tmp_path) == 0
    out = capsys.readouterr().out
    assert "E12" in out and "E20" in out
    assert "team_id is null" in out


# --- refusals ---------------------------------------------------------------


def test_missing_final_refuses_with_the_path(tmp_path, capsys):
    seed(tmp_path)
    missing = tmp_path / "nowhere" / "final.md"
    assert run(["plan", "--gw", "2", "--from-final", str(missing)], tmp_path) == 1
    err = capsys.readouterr().err
    assert "no final.md at" in err and str(missing) in err


def test_missing_bootstrap_snapshot_refuses_with_a_fetch_hint(tmp_path, capsys):
    decisions = tmp_path / "decisions" / "gw2"
    decisions.mkdir(parents=True)
    final = decisions / "final.md"
    final.write_text(state_block(2, squad_slots()), encoding="utf-8")
    assert run(["plan", "--gw", "2", "--from-final", str(final)], tmp_path) == 1
    err = capsys.readouterr().err
    assert "no snapshot 'bootstrap'" in err
    assert "bootstrap --gw 2" in err


def test_state_for_another_gameweek_refuses(tmp_path, capsys):
    final = seed(tmp_path, final=state_block(3, squad_slots()))
    assert run(["plan", "--gw", "2", "--from-final", str(final)], tmp_path) == 1
    assert "gw3" in capsys.readouterr().err


def test_final_without_picks_refuses(tmp_path, capsys):
    final = seed(tmp_path, final=state_block(2, [], include_picks=False))
    assert run(["plan", "--gw", "2", "--from-final", str(final)], tmp_path) == 1
    assert "no 'picks:' section" in capsys.readouterr().err
