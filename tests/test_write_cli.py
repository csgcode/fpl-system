"""CLI tests for the authenticated write commands: dry-run/--apply gating,
deadline refusals, auth refusals, idempotency, and the no-secrets-in-output
invariant — all through main() over a fake write gateway."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from fpl.__main__ import main
from fpl.models import Position
from fpl.plan import SCHEMA_VERSION
from fpl.store import SnapshotStore, utcnow
from fpl.write import SessionExpiredError
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
    assert "bank 0.5" in out and "value 100.3" in out
    assert "free transfers 1" in out
    assert "bboost (available)" in out
    assert "E14" in out  # name joined from the cached bootstrap
    assert "5.4" in out  # id 14 selling_price 54 → £5.4m
    assert gateway.get_calls == [MY_TEAM_URL]


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
    payload = json.loads(out[out.index("{"):])
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
    payload = json.loads(out[out.index("{"):])
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
    assert run([*TRANSFER_ARGS, "--apply"], tmp_path, gateway) == 0
    assert "applied and verified" in capsys.readouterr().out
    assert len(gateway.posts) == 1
    assert list((tmp_path / "executor" / "gw2").glob("make-transfers-*.json"))


def test_make_transfers_verify_mismatch_fails_loudly(tmp_path, capsys):
    seed_bootstrap(tmp_path)
    gateway = FakeWriteGateway(
        {MY_TEAM_URL: [current_my_team(), current_my_team()]}
    )
    assert run([*TRANSFER_ARGS, "--apply"], tmp_path, gateway) == 1
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
    payload = json.loads(out[out.index("{") :])
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
