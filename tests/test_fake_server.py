"""The stateful fake FPL server that write commands talk to in replay mode:
it answers my-team, applies transfer and lineup POSTs to its saved state, and
logs every POST — so an agent under evaluation runs the real CLI end to end
while nothing reaches FPL."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests

from fpl.__main__ import main
from fpl.api import BASE_URL
from fpl.clock import REPLAY_ENV
from fpl.fake_server import (
    FAKE_STATE_FILE,
    POSTS_LOG,
    FakeFplServer,
    fake_server_dir,
    seed_fake_server,
)
from fpl.write import TRANSFERS_URL, SessionExpiredError
from tests.factories import my_team_chip_payload, my_team_transfers_payload
from tests.test_write import SQUAD, current_my_team
from tests.test_write_cli import seed_bootstrap, write_auth

MY_TEAM_URL = f"{BASE_URL}/my-team/42/"


def seeded(tmp_path: Path, **overrides) -> Path:
    root = tmp_path / "fake"
    my_team = current_my_team(
        chips=[my_team_chip_payload(name="bboost"), my_team_chip_payload(name="wildcard")],
        transfers=my_team_transfers_payload(bank=5, made=0),
    )
    seed_fake_server(root, team_id=42, my_team=my_team, **overrides)
    return root


def posts(root: Path) -> list[dict]:
    path = root / POSTS_LOG
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def by_element(payload: dict) -> dict[int, dict]:
    return {pick["element"]: pick for pick in payload["picks"]}


def transfers_payload(chip: str | None = None) -> dict:
    return {
        "entry": 42, "event": 2, "chip": chip,
        "transfers": [{"element_out": 12, "element_in": 20,
                       "purchase_price": 70, "selling_price": 52}],
    }


def test_serves_my_team(tmp_path):
    root = seeded(tmp_path)
    payload = FakeFplServer(root).get_json(MY_TEAM_URL)
    assert sorted(by_element(payload)) == sorted(SQUAD)


def test_an_expired_session_raises_the_generic_message(tmp_path):
    root = seeded(tmp_path, auth="expired")
    with pytest.raises(SessionExpiredError) as caught:
        FakeFplServer(root).get_json(MY_TEAM_URL)
    assert caught.value.refresh_failure is None


def test_invalid_grant_raises_the_refresh_failure_text(tmp_path):
    root = seeded(tmp_path, auth="invalid_grant")
    with pytest.raises(SessionExpiredError) as caught:
        FakeFplServer(root).get_json(MY_TEAM_URL)
    assert str(caught.value) == (
        "session expired and refresh failed (token endpoint returned 400: "
        "invalid_grant — Refresh token does not exist) — re-copy credentials "
        "from browser devtools (see docs/api-write.md)"
    )


@pytest.mark.parametrize("url", [f"{BASE_URL}/my-team/43/", f"{BASE_URL}/bootstrap-static/"])
def test_an_unknown_url_raises(tmp_path, url):
    with pytest.raises(ValueError, match=f"fake server: no route for {url}"):
        FakeFplServer(seeded(tmp_path)).get_json(url)


def test_a_transfers_post_is_logged_and_applied(tmp_path):
    root = seeded(tmp_path)
    FakeFplServer(root).post_json(TRANSFERS_URL, transfers_payload(chip="wildcard"))
    after = FakeFplServer(root).get_json(MY_TEAM_URL)
    picks = by_element(after)
    assert 12 not in picks
    assert picks[20]["position"] == SQUAD[12][1]
    assert picks[20]["selling_price"] == picks[20]["purchase_price"] == 70
    assert not picks[20]["is_captain"] and not picks[20]["is_vice_captain"]
    assert after["transfers"]["bank"] == 5 + 52 - 70
    assert after["transfers"]["made"] == 1
    chips = {c["name"]: c["status_for_entry"] for c in after["chips"]}
    assert chips == {"bboost": "available", "wildcard": "active"}
    assert posts(root) == [{"url": TRANSFERS_URL, "payload": transfers_payload("wildcard")}]


def test_ignored_posts_are_logged_without_changing_state(tmp_path):
    root = seeded(tmp_path, ignore_posts=("transfers",))
    before = FakeFplServer(root).get_json(MY_TEAM_URL)
    FakeFplServer(root).post_json(TRANSFERS_URL, transfers_payload())
    assert FakeFplServer(root).get_json(MY_TEAM_URL) == before
    assert len(posts(root)) == 1


def test_a_lineup_post_rearranges_the_squad_and_plays_the_chip(tmp_path):
    root = seeded(tmp_path)
    lineup = {
        "chip": "bboost",
        "picks": [
            {"element": pid, "position": slot,
             "is_captain": pid == 13, "is_vice_captain": pid == 1}
            for pid, (_, slot) in SQUAD.items() if pid not in (1, 2)
        ] + [
            {"element": 1, "position": 12, "is_captain": False, "is_vice_captain": True},
            {"element": 2, "position": 1, "is_captain": False, "is_vice_captain": False},
        ],
    }
    FakeFplServer(root).post_json(MY_TEAM_URL, lineup)
    after = FakeFplServer(root).get_json(MY_TEAM_URL)
    picks = by_element(after)
    assert (picks[1]["position"], picks[2]["position"]) == (12, 1)
    assert picks[13]["is_captain"] and not picks[14]["is_captain"]
    assert picks[1]["is_vice_captain"]
    assert {c["name"]: c["status_for_entry"] for c in after["chips"]}["bboost"] == "active"


def test_a_lineup_naming_an_unowned_player_is_rejected(tmp_path):
    root = seeded(tmp_path)
    lineup = {"chip": None, "picks": [
        {"element": 99, "position": 1, "is_captain": False, "is_vice_captain": False}]}
    with pytest.raises(ValueError, match="not in the squad"):
        FakeFplServer(root).post_json(MY_TEAM_URL, lineup)


def test_state_persists_across_instances(tmp_path):
    root = seeded(tmp_path)
    FakeFplServer(root).post_json(TRANSFERS_URL, transfers_payload())
    assert 20 in by_element(FakeFplServer(root).get_json(MY_TEAM_URL))


def test_every_request_is_logged_as_served(tmp_path):
    """The live harness's bypass check reads served.jsonl."""
    root = seeded(tmp_path)
    FakeFplServer(root).get_json(MY_TEAM_URL)
    FakeFplServer(root).post_json(TRANSFERS_URL, transfers_payload())
    lines = (root / "served.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["outcome"] for line in lines] == ["fake", "fake-post"]


# --- through main() ----------------------------------------------------------------


@pytest.fixture
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("the fake server path reached requests")

    monkeypatch.setattr(requests.Session, "request", refuse)


def cli(tmp_path: Path, *argv: str) -> int:
    return main([
        "--data-root", str(tmp_path / "raw"), *argv,
        "--team-id", "42",
        "--auth", str(write_auth(tmp_path)),
        "--executor-root", str(tmp_path / "executor"),
    ])


def test_main_dry_runs_then_applies_with_the_approved_id_end_to_end(
    tmp_path, monkeypatch, capsys, no_network
):
    root = seeded(tmp_path)
    monkeypatch.setenv(REPLAY_ENV, str(root))
    seed_bootstrap(tmp_path)
    transfer = ["make-transfers", "--gw", "2", "--out", "12", "--in", "20"]

    assert cli(tmp_path, *transfer) == 0
    out = capsys.readouterr().out
    approved = next(
        line.removeprefix("transfer id: ")
        for line in out.splitlines() if line.startswith("transfer id: ")
    )
    assert posts(root) == []

    assert cli(tmp_path, *transfer, "--apply", "--approve", approved) == 0
    assert "applied and verified" in capsys.readouterr().out
    assert [p["url"] for p in posts(root)] == [TRANSFERS_URL]
    log = (tmp_path / "executor" / "gw2" / "runs.jsonl").read_text(encoding="utf-8")
    rows = [json.loads(line) for line in log.splitlines()]
    assert [r["outcome"] for r in rows] == ["dry-run", "applied"]
    assert all(r["fake_server"] for r in rows)


def test_the_banner_names_the_fake_server(tmp_path, monkeypatch, capsys, no_network):
    root = seeded(tmp_path)
    monkeypatch.setenv(REPLAY_ENV, str(root))
    seed_bootstrap(tmp_path)
    assert cli(tmp_path, "auth-check", "--gw", "2") == 0
    err = capsys.readouterr().err.splitlines()
    assert f"FAKE SERVER — nothing is sent to FPL ({root})" in err


def test_auth_refresh_refuses_under_the_fake_server(tmp_path, monkeypatch, capsys, no_network):
    root = seeded(tmp_path)
    monkeypatch.setenv(REPLAY_ENV, str(root))
    assert main(["auth-refresh", "--auth", str(write_auth(tmp_path))]) == 1
    assert "auth-refresh is unavailable in replay mode" in capsys.readouterr().err


def test_seeding_refuses_an_unknown_auth_state(tmp_path):
    with pytest.raises(ValueError, match="auth"):
        seeded(tmp_path, auth="sometimes")


def test_the_state_file_is_where_replay_mode_looks_for_it(tmp_path):
    root = seeded(tmp_path)
    assert (root / FAKE_STATE_FILE).is_file()
    assert fake_server_dir(root) == root


def test_a_replay_directory_without_the_state_file_selects_no_fake(tmp_path):
    assert fake_server_dir(tmp_path) is None


def test_outside_replay_mode_the_fake_is_never_selected(tmp_path, monkeypatch, capsys):
    from fpl import __main__ as cli

    monkeypatch.delenv(REPLAY_ENV, raising=False)
    monkeypatch.chdir(seeded(tmp_path))
    factory = cli._default_write_gateway_factory(write_auth(tmp_path))
    assert not isinstance(factory(cli.load_auth(write_auth(tmp_path))), FakeFplServer)
    assert "FAKE SERVER" not in capsys.readouterr().err
