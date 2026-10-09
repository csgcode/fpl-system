"""CLI tests for the authenticated write commands: dry-run/--apply gating,
deadline refusals, auth refusals, idempotency, and the no-secrets-in-output
invariant — all through main() over a fake write gateway."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path

import requests

from fpl.__main__ import main
from fpl.models import Position
from fpl.plan import SCHEMA_VERSION
from fpl.store import SnapshotStore, utcnow
from fpl.write import SessionExpiredError, transfer_id
from tests.factories import my_team_payload, my_team_transfers_payload
from tests.test_write import (
    MY_TEAM_URL,
    SECRET,
    SQUAD,
    FakeWriteGateway,
    current_my_team,
    squad_bootstrap,
    squad_my_team_picks,
)

ORDERED_IDS = ",".join(
    str(pid) for pid, _ in sorted(SQUAD.items(), key=lambda item: item[1][1])
)


def deadline_in(hours: float = 0, minutes: float = 0) -> str:
    at = utcnow() + timedelta(hours=hours, minutes=minutes)
    return at.strftime("%Y-%m-%dT%H:%M:%SZ")


def seed_bootstrap(tmp_path: Path, deadline: str | None = None) -> None:
    payload = squad_bootstrap(deadline=deadline or deadline_in(hours=2))
    SnapshotStore(tmp_path / "raw").save(2, "bootstrap", payload, "seed://test")


def write_auth(tmp_path: Path) -> Path:
    path = tmp_path / "auth.json"
    path.write_text(
        json.dumps({"headers": {"X-Api-Authorization": f"Bearer {SECRET}"}}),
        encoding="utf-8",
    )
    return path


def run(argv, tmp_path, gateway, *, auth: bool = True, entry: dict | None = None):
    extra = []
    auth_path = write_auth(tmp_path) if auth else tmp_path / "auth.json"
    extra += ["--auth", str(auth_path)]
    extra += ["--executor-root", str(tmp_path / "executor")]
    if entry is not None:
        entry_path = tmp_path / "entry.json"
        entry_path.write_text(json.dumps(entry), encoding="utf-8")
        extra += ["--entry-file", str(entry_path)]
    return main(
        ["--data-root", str(tmp_path / "raw"), *argv, *extra],
        write_gateway_factory=lambda credentials: gateway,
    )


def changed_captain_my_team() -> dict:
    payload = current_my_team()
    for pick in payload["picks"]:
        pick["is_captain"] = pick["element"] == 13
        pick["is_vice_captain"] = pick["element"] == 14
    return payload


def final_md(tmp_path: Path, gw: int = 2, captain: int = 13, vice: int = 14) -> Path:
    lines = [
        f"  - {{id: {pid}, name: E{pid}, position: {slot}, "
        f"captain: {str(pid == captain).lower()}, vice: {str(pid == vice).lower()}}}"
        for pid, (_, slot) in sorted(SQUAD.items(), key=lambda item: item[1][1])
    ]
    path = tmp_path / "final.md"
    path.write_text(
        "# Final\n\nprose\n\n## STATE\n\n```yaml\n"
        f"gw: {gw}\nteam_id: 42\npicks:\n" + "\n".join(lines) + "\n```\n",
        encoding="utf-8",
    )
    return path


SET_LINEUP_CHANGED = [
    "set-lineup", "--gw", "2", "--team-id", "42",
    "--picks", ORDERED_IDS, "--captain", "13", "--vice", "14",
]


# --- my-team ---------------------------------------------------------------


def test_my_team_prints_squad_bank_and_sell_prices(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(["my-team", "--gw", "2", "--team-id", "42"], tmp_path, gateway) == 0
    out = capsys.readouterr().out
    assert "entry 42" in out
    assert "bank 0.5" in out
    assert "free transfers 1" in out
    assert "bboost (available)" in out
    assert "E14" in out  # name joined from the cached bootstrap
    assert "5.4" in out  # id 14 selling_price 54 → £5.4m
    assert gateway.get_calls == [MY_TEAM_URL]


def test_my_team_labels_sell_market_and_budget_totals(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    run(["my-team", "--gw", "2", "--team-id", "42"], tmp_path, gateway)
    lines = capsys.readouterr().out.splitlines()
    # ids 1-15: selling_price 40+id sums to 720; now_cost 50+id sums to 870
    assert "sell_sum 72.0  (sum of selling prices)" in lines
    assert "bank 0.5" in lines
    assert "budget 72.5  (sell_sum + bank: what a wildcard or rebuild can spend)" in lines
    assert "market_sum 87.0  (sum of now_cost, cached bootstrap)" in lines
    assert any(
        line.startswith("api_value 100.3  (market basis") for line in lines
    )
    assert not any(line.startswith("value ") or ", value " in line for line in lines)


def test_my_team_without_a_cached_bootstrap_leaves_market_sum_unknown(
    tmp_path, capsys
):
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(["my-team", "--gw", "2", "--team-id", "42"], tmp_path, gateway) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "budget 72.5  (sell_sum + bank: what a wildcard or rebuild can spend)" in lines
    assert "market_sum n/a  (no cached bootstrap)" in lines


def test_my_team_marks_captain_and_vice(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    run(["my-team", "--gw", "2", "--team-id", "42"], tmp_path, gateway)
    rows = capsys.readouterr().out.splitlines()
    captain_row = next(line for line in rows if " 14 " in f" {line} " or "  14  " in line)
    assert captain_row.rstrip().endswith("C")


def test_my_team_does_not_write_into_the_raw_snapshot_dir(tmp_path):
    seed_bootstrap(tmp_path)
    before = sorted(p for p in (tmp_path / "raw").rglob("*") if p.is_file())
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    run(["my-team", "--gw", "2", "--team-id", "42"], tmp_path, gateway)
    assert sorted(p for p in (tmp_path / "raw").rglob("*") if p.is_file()) == before
    assert not (tmp_path / "executor").exists()


def test_team_id_falls_back_to_the_entry_file(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(
        ["my-team", "--gw", "2"], tmp_path, gateway, entry={"team_id": 42}
    ) == 0
    assert gateway.get_calls == [MY_TEAM_URL]


def test_null_team_id_refuses_with_registration_hint(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(
        ["my-team", "--gw", "2"], tmp_path, gateway, entry={"team_id": None}
    ) == 1
    captured = capsys.readouterr()
    assert "team_id is null" in captured.err
    assert captured.out == ""
    assert gateway.get_calls == []


def test_non_object_entry_file_refuses(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    entry_path = tmp_path / "entry.json"
    entry_path.write_text("[1]", encoding="utf-8")
    argv = ["my-team", "--gw", "2", "--entry-file", str(entry_path)]
    assert main(
        ["--data-root", str(tmp_path / "raw"), *argv,
         "--auth", str(write_auth(tmp_path))],
        write_gateway_factory=lambda credentials: gateway,
    ) == 1
    assert "JSON object" in capsys.readouterr().err


def test_from_final_missing_file_refuses_with_the_path(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    missing = tmp_path / "nowhere" / "final.md"
    argv = [
        "set-lineup", "--gw", "2", "--team-id", "42", "--from-final", str(missing),
    ]
    assert run(argv, tmp_path, gateway) == 1
    captured = capsys.readouterr()
    assert "no final.md at" in captured.err
    assert str(missing) in captured.err


def test_missing_auth_refuses_before_any_request(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(
        ["my-team", "--gw", "2", "--team-id", "42"], tmp_path, gateway, auth=False
    ) == 1
    captured = capsys.readouterr()
    assert "no auth credentials" in captured.err
    assert "docs/api-write.md" in captured.err
    assert captured.out == ""
    assert gateway.get_calls == []


# --- set-lineup --------------------------------------------------------------


def test_set_lineup_dry_run_prints_the_payload_and_never_posts(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(SET_LINEUP_CHANGED, tmp_path, gateway) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "--apply" in out
    payload = json.loads(out[out.index("{"): out.rindex("}") + 1])
    assert len(payload["picks"]) == 15
    assert payload["chip"] is None
    captain_rows = [p for p in payload["picks"] if p["is_captain"]]
    assert [p["element"] for p in captain_rows] == [13]
    assert gateway.posts == []


def test_set_lineup_apply_posts_verifies_and_writes_audit(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway(
        {MY_TEAM_URL: [current_my_team(), changed_captain_my_team()]}
    )
    assert run([*SET_LINEUP_CHANGED, "--apply"], tmp_path, gateway) == 0
    out = capsys.readouterr().out
    assert "applied and verified" in out
    assert len(gateway.posts) == 1
    audits = list((tmp_path / "executor" / "gw2").glob("set-lineup-*.json"))
    assert len(audits) == 1


def test_set_lineup_already_applied_skips_the_post(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    argv = [
        "set-lineup", "--gw", "2", "--team-id", "42",
        "--picks", ORDERED_IDS, "--captain", "14", "--vice", "13", "--apply",
    ]
    assert run(argv, tmp_path, gateway) == 0
    assert "already applied" in capsys.readouterr().out
    assert gateway.posts == []


def test_set_lineup_from_final_builds_payload_from_the_state_block(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    final = final_md(tmp_path)
    argv = ["set-lineup", "--gw", "2", "--team-id", "42", "--from-final", str(final)]
    assert run(argv, tmp_path, gateway) == 0
    out = capsys.readouterr().out
    payload = json.loads(out[out.index("{"): out.rindex("}") + 1])
    captain_rows = [p for p in payload["picks"] if p["is_captain"]]
    assert [p["element"] for p in captain_rows] == [13]


def test_set_lineup_from_final_refuses_a_different_gameweeks_state(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    final = final_md(tmp_path, gw=3)
    argv = ["set-lineup", "--gw", "2", "--team-id", "42", "--from-final", str(final)]
    assert run(argv, tmp_path, gateway) == 1
    assert "gw3" in capsys.readouterr().err
    assert gateway.posts == []


def test_set_lineup_passed_deadline_refuses_even_forced(tmp_path, capsys):
    seed_bootstrap(tmp_path, deadline=deadline_in(hours=-1))
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run([*SET_LINEUP_CHANGED, "--apply"], tmp_path, gateway) == 1
    assert "has passed" in capsys.readouterr().err
    assert run(
        [*SET_LINEUP_CHANGED, "--apply", "--force-deadline"], tmp_path, gateway
    ) == 1
    assert "has passed" in capsys.readouterr().err
    assert gateway.posts == []


def test_set_lineup_inside_margin_needs_force_deadline(tmp_path, capsys):
    seed_bootstrap(tmp_path, deadline=deadline_in(minutes=10))
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(SET_LINEUP_CHANGED, tmp_path, gateway) == 1
    assert "--force-deadline" in capsys.readouterr().err
    assert run([*SET_LINEUP_CHANGED, "--force-deadline"], tmp_path, gateway) == 0
    assert "DRY RUN" in capsys.readouterr().out


def test_set_lineup_without_a_picks_source_refuses(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(["set-lineup", "--gw", "2", "--team-id", "42"], tmp_path, gateway) == 1
    assert "--from-final" in capsys.readouterr().err


# --- make-transfers ----------------------------------------------------------


TRANSFER_ARGS = [
    "make-transfers", "--gw", "2", "--team-id", "42", "--out", "12", "--in", "20",
]


# The id of TRANSFER_ARGS' one swap (12 out, 20 in) for entry 42 in gw2.
TRANSFER_ID = transfer_id(
    {"entry": 42, "event": 2, "chip": None,
     "transfers": [{"element_out": 12, "element_in": 20}]}
)
APPROVED = ["--apply", "--approve", TRANSFER_ID]


def swapped_my_team() -> dict:
    swapped = dict(SQUAD)
    swapped[20] = swapped.pop(12)
    return my_team_payload(picks=squad_my_team_picks(swapped))


def test_make_transfers_dry_run_prints_payload_and_hit_never_posts(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(TRANSFER_ARGS, tmp_path, gateway) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "--apply" in out
    payload = json.loads(out[out.index("{"): out.rindex("}") + 1])
    assert payload["transfers"] == [
        {"element_in": 20, "element_out": 12, "purchase_price": 70,
         "selling_price": 52}
    ]
    assert "hit" in out
    assert gateway.posts == []


def test_make_transfers_apply_posts_and_verifies(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway(
        {MY_TEAM_URL: [current_my_team(), swapped_my_team()]}
    )
    assert run([*TRANSFER_ARGS, *APPROVED], tmp_path, gateway) == 0
    assert "applied and verified" in capsys.readouterr().out
    assert len(gateway.posts) == 1
    assert list((tmp_path / "executor" / "gw2").glob("make-transfers-*.json"))


def test_make_transfers_verify_mismatch_fails_loudly(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway(
        {MY_TEAM_URL: [current_my_team(), current_my_team()]}
    )
    assert run([*TRANSFER_ARGS, *APPROVED], tmp_path, gateway) == 1
    assert "verify-after-write failed" in capsys.readouterr().err


def test_make_transfers_from_final_computes_the_diff(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [swapped_my_team()]})
    final = final_md(tmp_path)  # target = SQUAD → swap 20 back out for 12
    argv = [
        "make-transfers", "--gw", "2", "--team-id", "42", "--from-final", str(final),
    ]
    assert run(argv, tmp_path, gateway) == 0
    out = capsys.readouterr().out
    payload = json.loads(out[out.index("{"): out.rindex("}") + 1])
    assert [(t["element_out"], t["element_in"]) for t in payload["transfers"]] == [
        (20, 12)
    ]


def test_make_transfers_already_applied_is_a_no_op(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [swapped_my_team()]})
    assert run([*TRANSFER_ARGS, "--apply"], tmp_path, gateway) == 0
    assert "already applied" in capsys.readouterr().out
    assert gateway.posts == []


def test_make_transfers_without_a_source_refuses(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(
        ["make-transfers", "--gw", "2", "--team-id", "42"], tmp_path, gateway
    ) == 1
    assert "--from-final" in capsys.readouterr().err


# --- secrets ------------------------------------------------------------------


class ExpiredGateway:
    get_calls: list[str] = []
    posts: list = []

    def get_json(self, url: str):
        raise SessionExpiredError()

    def post_json(self, url: str, payload: dict):
        raise SessionExpiredError()


def test_expired_session_prints_the_generic_message(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    assert run(
        ["my-team", "--gw", "2", "--team-id", "42"], tmp_path, ExpiredGateway()
    ) == 1
    captured = capsys.readouterr()
    assert "session expired" in captured.err
    assert "docs/api-write.md" in captured.err


def test_secrets_never_appear_in_any_output(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway(
        {MY_TEAM_URL: [current_my_team(), changed_captain_my_team()]}
    )
    run(["my-team", "--gw", "2", "--team-id", "42"], tmp_path, gateway)
    run(SET_LINEUP_CHANGED, tmp_path, gateway)
    run(["my-team", "--gw", "2", "--team-id", "42"], tmp_path, ExpiredGateway())
    captured = capsys.readouterr()
    assert SECRET not in captured.out
    assert SECRET not in captured.err


# --- --from-plan --------------------------------------------------------------


def plan_document(
    *,
    gw: int = 2,
    chip: str | None = None,
    transfers: list[dict] | None = None,
    schema_version: int = SCHEMA_VERSION,
    captain: int = 13,
    vice: int = 14,
) -> dict:
    ordered = sorted(SQUAD.items(), key=lambda item: item[1][1])
    return {
        "schema_version": schema_version,
        "gw": gw,
        "team_id": 42,
        "deadline": "2026-08-22T12:00:00Z",
        "chip": chip,
        "chip_plan": [],
        "chips_used": [],
        "chips_available": [{"name": "bboost", "start_event": 1, "stop_event": 19}],
        "formation": "3-4-3",
        "picks": [
            {
                "element": pid,
                "name": f"E{pid}",
                "club": "TST",
                "position": Position(element_type).name,
                "slot": slot,
                "is_captain": pid == captain,
                "is_vice_captain": pid == vice,
                "now_cost": (50 + pid) / 10,
                "starts": slot <= 11,
            }
            for pid, (element_type, slot) in ordered
        ],
        "bench": [pid for pid, (_, slot) in ordered if slot > 11],
        "captain": {"id": captain, "name": f"E{captain}"},
        "vice": {"id": vice, "name": f"E{vice}"},
        "transfers": transfers or [],
        "transfer_source": "picks-diff" if transfers else "none",
        "price_resolution": "live",
        "price_resolution_note": "prices are re-resolved at POST time",
        "bank": 0.5,
        "team_value": 100.3,
        "free_transfers_banked": 1,
        "source": "data/decisions/gw2/final.md",
        "generated_from": {
            "final": "data/decisions/gw2/final.md",
            "previous_final": None,
            "bootstrap": "data/raw/gw2/bootstrap.json",
        },
        "bootstrap_snapshot_age_hours": 1.0,
        "warnings": [],
    }


def plan_file(tmp_path: Path, **kwargs) -> Path:
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan_document(**kwargs)), encoding="utf-8")
    return path


def transfer_row(purchase_price_at_plan: float) -> dict:
    return {
        "out": {"id": 20, "name": "E20"},
        "in": {"id": 12, "name": "E12"},
        "cost": 0,
        "purchase_price_at_plan": purchase_price_at_plan,
        "selling_price": None,
    }


def swapped_my_team_with_bank(bank: int) -> dict:
    swapped = dict(SQUAD)
    swapped[20] = swapped.pop(12)
    return my_team_payload(
        picks=squad_my_team_picks(swapped),
        transfers=my_team_transfers_payload(bank=bank),
    )


def test_set_lineup_from_plan_builds_the_payload(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    argv = [
        "set-lineup", "--gw", "2", "--team-id", "42",
        "--from-plan", str(plan_file(tmp_path)),
    ]
    assert run(argv, tmp_path, gateway) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    payload = json.loads(out[out.index("{") : out.rindex("}") + 1])
    assert len(payload["picks"]) == 15
    assert [p["element"] for p in payload["picks"] if p["is_captain"]] == [13]
    assert payload["chip"] is None
    assert gateway.posts == []


def test_set_lineup_from_plan_carries_the_chip(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    argv = [
        "set-lineup", "--gw", "2", "--team-id", "42",
        "--from-plan", str(plan_file(tmp_path, chip="bboost")),
    ]
    assert run(argv, tmp_path, gateway) == 0
    out = capsys.readouterr().out
    assert '"chip": "bboost"' in out


def test_chip_flag_contradicting_the_plan_refuses(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    argv = [
        "set-lineup", "--gw", "2", "--team-id", "42",
        "--from-plan", str(plan_file(tmp_path, chip="bboost")), "--chip", "3xc",
    ]
    assert run(argv, tmp_path, gateway) == 1
    assert "contradicts the plan" in capsys.readouterr().err
    assert gateway.posts == []


def test_plan_for_another_gameweek_refuses(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    argv = [
        "set-lineup", "--gw", "2", "--team-id", "42",
        "--from-plan", str(plan_file(tmp_path, gw=3)),
    ]
    assert run(argv, tmp_path, gateway) == 1
    assert "gw3" in capsys.readouterr().err


def test_unsupported_plan_schema_version_refuses(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    argv = [
        "set-lineup", "--gw", "2", "--team-id", "42",
        "--from-plan", str(plan_file(tmp_path, schema_version=SCHEMA_VERSION + 1)),
    ]
    assert run(argv, tmp_path, gateway) == 1
    err = capsys.readouterr().err
    assert "schema_version" in err and "fpl plan --gw 2" in err


def test_missing_plan_file_refuses_with_the_path(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    missing = tmp_path / "nowhere" / "plan.json"
    argv = [
        "set-lineup", "--gw", "2", "--team-id", "42", "--from-plan", str(missing),
    ]
    assert run(argv, tmp_path, gateway) == 1
    err = capsys.readouterr().err
    assert "no plan at" in err and str(missing) in err


def test_make_transfers_from_plan_diffs_against_the_live_squad(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [swapped_my_team_with_bank(5)]})
    argv = [
        "make-transfers", "--gw", "2", "--team-id", "42",
        "--from-plan", str(plan_file(tmp_path, transfers=[transfer_row(6.2)])),
    ]
    assert run(argv, tmp_path, gateway) == 0
    out = capsys.readouterr().out
    payload = json.loads(out[out.index("{") : out.rindex("}") + 1])
    assert payload["transfers"] == [
        {"element_in": 12, "element_out": 20, "purchase_price": 62,
         "selling_price": 60}
    ]
    assert "drift" not in out
    assert gateway.posts == []


def test_make_transfers_from_plan_warns_on_purchase_price_drift(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [swapped_my_team_with_bank(5)]})
    argv = [
        "make-transfers", "--gw", "2", "--team-id", "42",
        "--from-plan", str(plan_file(tmp_path, transfers=[transfer_row(6.0)])),
    ]
    assert run(argv, tmp_path, gateway) == 0
    out = capsys.readouterr().out
    assert "price drift: element 12 planned at £6.0m, now £6.2m" in out
    assert gateway.posts == []


def test_make_transfers_from_plan_refuses_when_drift_breaks_the_bank(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [swapped_my_team_with_bank(0)]})
    argv = [
        "make-transfers", "--gw", "2", "--team-id", "42",
        "--from-plan", str(plan_file(tmp_path, transfers=[transfer_row(6.0)])),
        "--apply",
    ]
    assert run(argv, tmp_path, gateway) == 1
    err = capsys.readouterr().err
    assert "bank" in err and "short by" in err
    assert gateway.posts == []


def test_selling_prices_always_come_from_the_authenticated_read(tmp_path, capsys):
    """The plan never carries one, so the payload can only have got it live."""
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [swapped_my_team_with_bank(5)]})
    argv = [
        "make-transfers", "--gw", "2", "--team-id", "42",
        "--from-plan", str(plan_file(tmp_path, transfers=[transfer_row(6.2)])),
    ]
    run(argv, tmp_path, gateway)
    out = capsys.readouterr().out
    payload = json.loads(out[out.index("{") : out.rindex("}") + 1])
    assert payload["transfers"][0]["selling_price"] == 60


# --- ordering and chip routing -------------------------------------------------


def transfer_argv(tmp_path: Path, **plan_kwargs) -> list[str]:
    return [
        "make-transfers", "--gw", "2", "--team-id", "42",
        "--from-plan", str(plan_file(tmp_path, **plan_kwargs)),
    ]


def lineup_argv(tmp_path: Path, **plan_kwargs) -> list[str]:
    return [
        "set-lineup", "--gw", "2", "--team-id", "42",
        "--from-plan", str(plan_file(tmp_path, **plan_kwargs)),
    ]


def test_set_lineup_refuses_while_the_plan_transfers_are_unapplied(tmp_path, capsys):
    """F1: the lineup names the incoming player, who is not owned until the
    transfer lands — so transfers must be applied first."""
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [swapped_my_team_with_bank(5)]})
    argv = lineup_argv(tmp_path, transfers=[transfer_row(6.2)])
    assert run(argv, tmp_path, gateway) == 1
    err = capsys.readouterr().err
    assert "not in the squad: E12 (12)" in err
    assert "transfers first" in err
    assert gateway.posts == []


def test_set_lineup_succeeds_once_the_transfers_have_landed(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    argv = lineup_argv(tmp_path, transfers=[transfer_row(6.2)])
    assert run(argv, tmp_path, gateway) == 0
    assert "DRY RUN" in capsys.readouterr().out


def test_make_transfers_routes_a_lineup_chip_away(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [swapped_my_team_with_bank(5)]})
    argv = transfer_argv(tmp_path, chip="3xc", transfers=[transfer_row(6.2)])
    assert run(argv, tmp_path, gateway) == 0
    out = capsys.readouterr().out
    payload = json.loads(out[out.index("{") : out.rindex("}") + 1])
    assert payload["chip"] is None
    assert "chip 3xc is activated by set-lineup" in out


def test_set_lineup_routes_a_transfer_chip_away(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    argv = lineup_argv(tmp_path, chip="freehit")
    assert run(argv, tmp_path, gateway) == 0
    out = capsys.readouterr().out
    assert '"chip": null' in out
    assert "chip freehit is activated by make-transfers" in out


def test_make_transfers_carries_a_transfer_chip(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [swapped_my_team_with_bank(5)]})
    argv = transfer_argv(tmp_path, chip="wildcard", transfers=[transfer_row(6.2)])
    assert run(argv, tmp_path, gateway) == 0
    out = capsys.readouterr().out
    payload = json.loads(out[out.index("{") : out.rindex("}") + 1])
    assert payload["chip"] == "wildcard"
    assert "no hit" in out


def test_a_gameweek_with_no_transfers_is_a_no_op_not_a_failure(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(transfer_argv(tmp_path), tmp_path, gateway) == 0
    assert "already applied" in capsys.readouterr().out
    assert gateway.posts == []


def test_a_lineup_chip_survives_a_gameweek_with_no_transfers(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(transfer_argv(tmp_path, chip="bboost"), tmp_path, gateway) == 0
    out = capsys.readouterr().out
    assert "already applied" in out
    assert gateway.posts == []
    lineup = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(lineup_argv(tmp_path, chip="bboost"), tmp_path, lineup) == 0
    assert '"chip": "bboost"' in capsys.readouterr().out


def test_a_transfer_chip_with_no_transfers_refuses_rather_than_dropping_it(
    tmp_path, capsys
):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(transfer_argv(tmp_path, chip="wildcard"), tmp_path, gateway) == 1
    assert "silently skipped" in capsys.readouterr().err
    assert gateway.posts == []


# --- transfer approval -----------------------------------------------------------


def test_apply_with_pending_transfers_and_no_approve_refuses_without_posting(
    tmp_path, capsys
):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run([*TRANSFER_ARGS, "--apply"], tmp_path, gateway) == 1
    assert (
        "error: make-transfers --apply needs --approve <transfer id> — dry-run "
        "first and pass the id the user approved"
    ) in capsys.readouterr().err
    assert gateway.posts == []


def test_apply_with_a_mismatched_approve_refuses_without_posting(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    argv = [*TRANSFER_ARGS, "--apply", "--approve", "000000000000"]
    assert run(argv, tmp_path, gateway) == 1
    err = capsys.readouterr().err
    assert (
        f"error: --approve 000000000000 does not match this payload's transfer id "
        f"{TRANSFER_ID} — the transfers changed since approval; dry-run again and "
        "get the user's approval for the new id"
    ) in err
    assert gateway.posts == []


def test_apply_with_the_dry_run_transfer_id_posts(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    dry = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    run(TRANSFER_ARGS, tmp_path, dry)
    printed = [
        line.removeprefix("transfer id: ")
        for line in capsys.readouterr().out.splitlines()
        if line.startswith("transfer id: ")
    ]
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team(), swapped_my_team()]})
    argv = [*TRANSFER_ARGS, "--apply", "--approve", printed[0]]
    assert run(argv, tmp_path, gateway) == 0
    assert len(gateway.posts) == 1


def test_already_applied_needs_no_approve(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [swapped_my_team()]})
    assert run([*TRANSFER_ARGS, "--apply"], tmp_path, gateway) == 0
    assert "already applied" in capsys.readouterr().out
    assert gateway.posts == []


def test_make_transfers_dry_run_names_each_transfer(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    run(TRANSFER_ARGS, tmp_path, gateway)
    lines = capsys.readouterr().out.splitlines()
    line = "transfer: E12 (12) → E20 (20), sell £5.2m, buy £7.0m"
    assert line in lines
    assert lines.index(line) < lines.index("{")


def test_make_transfers_dry_run_prints_the_transfer_id(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    run(TRANSFER_ARGS, tmp_path, gateway)
    lines = capsys.readouterr().out.splitlines()
    assert lines[-1] == f"transfer id: {TRANSFER_ID}"
    assert any("estimated hit" in line for line in lines[:-1])


def test_price_drift_keeps_the_transfer_id(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    ids = []
    for planned in (6.2, 6.0):
        gateway = FakeWriteGateway({MY_TEAM_URL: [swapped_my_team_with_bank(5)]})
        run(transfer_argv(tmp_path, transfers=[transfer_row(planned)]), tmp_path, gateway)
        ids += [
            line for line in capsys.readouterr().out.splitlines()
            if line.startswith("transfer id: ")
        ]
    assert len(ids) == 2 and ids[0] == ids[1]


# --- set-lineup summary --------------------------------------------------------


def test_set_lineup_dry_run_prints_captain_vice_and_bench_by_name(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(lineup_argv(tmp_path), tmp_path, gateway) == 0
    lines = capsys.readouterr().out.splitlines()
    captain = "captain: E13 (13), vice: E14 (14)"
    assert captain in lines
    assert "bench: E2 (2), E6 (6), E7 (7), E12 (12)" in lines
    assert lines.index("}") < lines.index(captain)


def test_set_lineup_dry_run_lists_changes_from_the_current_lineup(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    run(lineup_argv(tmp_path, chip="freehit"), tmp_path, gateway)
    lines = capsys.readouterr().out.splitlines()
    start = lines.index("changes from the current lineup:")
    assert lines[start + 1:start + 5] == [
        "  element 13: captain flag is False, expected True",
        "  element 13: vice flag is True, expected False",
        "  element 14: captain flag is True, expected False",
        "  element 14: vice flag is False, expected True",
    ]
    assert lines[-1].startswith("note: chip freehit is activated by make-transfers")


# --- run log -------------------------------------------------------------------


def run_rows(tmp_path: Path, gw: int = 2) -> list[dict]:
    path = tmp_path / "executor" / f"gw{gw}" / "runs.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


AUTH_CHECK = ["auth-check", "--gw", "2", "--team-id", "42"]


def test_auth_check_pass_appends_a_pass_row(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(AUTH_CHECK, tmp_path, gateway) == 0
    [row] = run_rows(tmp_path)
    assert row["command"] == "auth-check"
    assert row["outcome"] == "pass"
    assert row["message"] == "PASS — authenticated session works"
    assert row["apply"] is False
    assert row["plan"] is None and row["plan_sha256"] is None
    assert row["transfer_id"] is None and row["audit"] is None
    assert row["fake_server"] is False
    assert row["at"].endswith("Z") and "T" in row["at"]


def test_auth_check_expired_session_appends_a_fail_row_with_the_printed_line(
    tmp_path, capsys
):
    seed_bootstrap(tmp_path)
    assert run(AUTH_CHECK, tmp_path, ExpiredGateway()) == 1
    [row] = run_rows(tmp_path)
    assert row["outcome"] == "fail"
    assert row["message"] == (
        "FAIL — session expired — re-copy credentials from browser devtools "
        "(see docs/api-write.md)"
    )
    assert row["message"] in capsys.readouterr().err.splitlines()


def test_missing_auth_file_appends_a_fail_row(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(AUTH_CHECK, tmp_path, gateway, auth=False) == 1
    [row] = run_rows(tmp_path)
    assert row["outcome"] == "fail"
    assert row["message"].startswith("error: no auth credentials")
    assert row["message"] in capsys.readouterr().err.splitlines()


def test_make_transfers_dry_run_row_has_plan_hash_and_transfer_id(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [swapped_my_team_with_bank(5)]})
    argv = transfer_argv(tmp_path, transfers=[transfer_row(6.2)])
    assert run(argv, tmp_path, gateway) == 0
    printed = capsys.readouterr().out.splitlines()
    [row] = run_rows(tmp_path)
    plan = tmp_path / "plan.json"
    assert row["command"] == "make-transfers"
    assert row["outcome"] == "dry-run"
    assert row["message"] == printed[0]
    assert row["plan"] == str(plan)
    assert row["plan_sha256"] == hashlib.sha256(plan.read_bytes()).hexdigest()
    assert f"transfer id: {row['transfer_id']}" in printed


def test_make_transfers_apply_row_has_the_audit_path(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team(), swapped_my_team()]})
    assert run([*TRANSFER_ARGS, *APPROVED], tmp_path, gateway) == 0
    printed = capsys.readouterr().out.splitlines()
    [row] = run_rows(tmp_path)
    assert row["outcome"] == "applied"
    assert row["apply"] is True
    assert row["transfer_id"] == TRANSFER_ID
    assert row["message"] == printed[0]
    assert printed[0] == f"applied and verified — audit: {row['audit']}"
    assert Path(row["audit"]).is_file()


def test_already_applied_row(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(lineup_argv(tmp_path, captain=14, vice=13), tmp_path, gateway) == 0
    [row] = run_rows(tmp_path)
    assert row["command"] == "set-lineup"
    assert row["outcome"] == "already-applied"
    assert row["message"] == capsys.readouterr().out.splitlines()[0]


def test_deadline_refusal_appends_a_refused_row_and_sends_nothing(tmp_path, capsys):
    seed_bootstrap(tmp_path, deadline=deadline_in(minutes=10))
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run([*TRANSFER_ARGS, *APPROVED], tmp_path, gateway) == 1
    [row] = run_rows(tmp_path)
    assert row["outcome"] == "refused"
    assert "under 30 minutes away" in row["message"]
    assert row["message"] in capsys.readouterr().err.splitlines()
    assert gateway.posts == []


def test_verify_mismatch_appends_a_verify_failed_row(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team(), current_my_team()]})
    assert run([*TRANSFER_ARGS, *APPROVED], tmp_path, gateway) == 1
    [row] = run_rows(tmp_path)
    assert row["outcome"] == "verify-failed"
    assert row["message"].startswith("error: verify-after-write failed: ")
    assert row["message"] in capsys.readouterr().err.splitlines()


class PostFailsGateway(FakeWriteGateway):
    def post_json(self, url: str, payload: dict):
        self.posts.append((url, payload))
        raise requests.ConnectionError("connection reset")


def test_a_network_failure_after_the_post_appends_an_error_row(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = PostFailsGateway({MY_TEAM_URL: [current_my_team()]})
    assert run([*TRANSFER_ARGS, *APPROVED], tmp_path, gateway) == 1
    [row] = run_rows(tmp_path)
    assert row["outcome"] == "error"
    assert row["message"] in capsys.readouterr().err.splitlines()


def test_rows_are_appended_never_rewritten(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    for _ in range(2):
        run(AUTH_CHECK, tmp_path, FakeWriteGateway({MY_TEAM_URL: [current_my_team()]}))
    log = tmp_path / "executor" / "gw2" / "runs.jsonl"
    first = log.read_bytes()
    run(TRANSFER_ARGS, tmp_path, FakeWriteGateway({MY_TEAM_URL: [current_my_team()]}))
    assert log.read_bytes().startswith(first)
    assert [r["command"] for r in run_rows(tmp_path)] == [
        "auth-check", "auth-check", "make-transfers",
    ]


def test_run_log_never_contains_credentials(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    run(AUTH_CHECK, tmp_path, FakeWriteGateway({MY_TEAM_URL: [current_my_team()]}))
    run(AUTH_CHECK, tmp_path, ExpiredGateway())
    run(TRANSFER_ARGS, tmp_path, FakeWriteGateway({MY_TEAM_URL: [current_my_team()]}))
    log = tmp_path / "executor" / "gw2" / "runs.jsonl"
    assert len(run_rows(tmp_path)) == 3
    assert SECRET not in log.read_text(encoding="utf-8")


def test_my_team_writes_no_run_log_row(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run(["my-team", "--gw", "2", "--team-id", "42"], tmp_path, gateway) == 0
    assert run_rows(tmp_path) == []


def test_a_malformed_auth_file_logs_a_fail_row_without_its_values(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    write_auth(tmp_path).write_text(
        json.dumps({"headers": {"X-Api-Authorization": [f"Bearer {SECRET}"]}}),
        encoding="utf-8",
    )
    argv = [*AUTH_CHECK, "--auth", str(tmp_path / "auth.json"),
            "--executor-root", str(tmp_path / "executor")]
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert main(["--data-root", str(tmp_path / "raw"), *argv],
                write_gateway_factory=lambda credentials: gateway) == 1
    log = tmp_path / "executor" / "gw2" / "runs.jsonl"
    assert [r["outcome"] for r in run_rows(tmp_path)] == ["fail"]
    assert SECRET not in log.read_text(encoding="utf-8")
    assert SECRET not in capsys.readouterr().err
