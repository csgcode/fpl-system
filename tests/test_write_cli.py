"""CLI tests for the authenticated write commands: dry-run/--apply gating,
deadline refusals, auth refusals, idempotency, and the no-secrets-in-output
invariant — all through main() over a fake write gateway."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from fpl.__main__ import main
from fpl.store import SnapshotStore, utcnow
from fpl.write import SessionExpiredError
from tests.factories import my_team_payload
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
