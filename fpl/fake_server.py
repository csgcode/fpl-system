"""A stateful stand-in for FPL's authenticated API, for evaluating the agent
that applies plans.

Selected in replay mode (FPL_REPLAY_DIR) when the replay directory holds a
fake-server.json, so the one variable that keeps reads off the network also
keeps writes off it. Every write command then runs for real against this
state: refusals, notes and verify-after-write behave exactly as against FPL,
in whatever order an agent calls them. Each CLI call is a new process, so the
state is saved after every POST.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Iterable
from pathlib import Path

from fpl.replay import SERVED_LOG
from fpl.write import TRANSFERS_URL, SessionExpiredError, my_team_url

FAKE_STATE_FILE = "fake-server.json"
POSTS_LOG = "posts.jsonl"
AUTH_STATES = ("ok", "expired", "invalid_grant")
POST_KINDS = ("transfers", "lineup")
INVALID_GRANT = "token endpoint returned 400: invalid_grant — Refresh token does not exist"


def fake_server_dir(replay_root: Path | None) -> Path | None:
    if replay_root is None or not (replay_root / FAKE_STATE_FILE).is_file():
        return None
    return replay_root


def seed_fake_server(
    root: Path,
    *,
    team_id: int,
    my_team: dict,
    auth: str = "ok",
    ignore_posts: Iterable[str] = (),
) -> Path:
    """`ignore_posts` names POST kinds that are logged but change nothing, as a
    server that accepted a request and dropped it would."""
    if auth not in AUTH_STATES:
        raise ValueError(f"fake server auth must be one of {AUTH_STATES}, got {auth!r}")
    ignored = list(ignore_posts)
    unknown = [kind for kind in ignored if kind not in POST_KINDS]
    if unknown:
        raise ValueError(f"unknown POST kinds {unknown}; known: {POST_KINDS}")
    root.mkdir(parents=True, exist_ok=True)
    state = {"team_id": team_id, "auth": auth, "ignore_posts": ignored, "my_team": my_team}
    path = root / FAKE_STATE_FILE
    path.write_text(json.dumps(state, indent=1), encoding="utf-8")
    return path


class FakeFplServer:
    """Satisfies WriteGateway."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def get_json(self, url: str) -> dict | list:
        state = self._load()
        self._log_served(url, "fake")
        self._ensure_authenticated(state)
        if url != my_team_url(state["team_id"]):
            raise ValueError(f"fake server: no route for {url}")
        return state["my_team"]

    def post_json(self, url: str, payload: dict) -> None:
        state = self._load()
        self._log_served(url, "fake-post")
        self._ensure_authenticated(state)
        if url == TRANSFERS_URL:
            kind = "transfers"
        elif url == my_team_url(state["team_id"]):
            kind = "lineup"
        else:
            raise ValueError(f"fake server: no route for {url}")
        with (self._root / POSTS_LOG).open("a", encoding="utf-8") as log:
            log.write(json.dumps({"url": url, "payload": payload}) + "\n")
        if kind in state["ignore_posts"]:
            return None
        team = state["my_team"]
        if kind == "transfers":
            _apply_transfers(team, payload)
        else:
            _apply_lineup(team, payload)
        self._save(state)
        return None

    def close(self) -> None:
        return None

    def _ensure_authenticated(self, state: dict) -> None:
        if state["auth"] == "expired":
            raise SessionExpiredError()
        if state["auth"] == "invalid_grant":
            raise SessionExpiredError(INVALID_GRANT)

    def _load(self) -> dict:
        return json.loads((self._root / FAKE_STATE_FILE).read_text(encoding="utf-8"))

    def _save(self, state: dict) -> None:
        (self._root / FAKE_STATE_FILE).write_text(json.dumps(state, indent=1), "utf-8")

    def _log_served(self, url: str, outcome: str) -> None:
        line = json.dumps({"url": url, "key": None, "outcome": outcome})
        with (self._root / SERVED_LOG).open("a", encoding="utf-8") as log:
            log.write(line + "\n")


def _apply_transfers(team: dict, payload: dict) -> None:
    by_element = {pick["element"]: pick for pick in team["picks"]}
    rows = payload["transfers"]
    for row in rows:
        pick = by_element.get(row["element_out"])
        if pick is None:
            raise ValueError(f"fake server: element {row['element_out']} is not in the squad")
        replacement = copy.deepcopy(pick)
        replacement.update(
            element=row["element_in"],
            selling_price=row["purchase_price"],
            purchase_price=row["purchase_price"],
            is_captain=False,
            is_vice_captain=False,
        )
        team["picks"][team["picks"].index(pick)] = replacement
    transfers = team["transfers"]
    transfers["bank"] += sum(r["selling_price"] - r["purchase_price"] for r in rows)
    transfers["made"] = (transfers.get("made") or 0) + len(rows)
    _activate(team, payload.get("chip"))


def _apply_lineup(team: dict, payload: dict) -> None:
    by_element = {pick["element"]: pick for pick in team["picks"]}
    for planned in payload["picks"]:
        pick = by_element.get(planned["element"])
        if pick is None:
            raise ValueError(f"fake server: element {planned['element']} is not in the squad")
        pick.update(
            position=planned["position"],
            is_captain=planned["is_captain"],
            is_vice_captain=planned["is_vice_captain"],
        )
    team["picks"].sort(key=lambda pick: pick["position"])
    _activate(team, payload.get("chip"))


def _activate(team: dict, chip: str | None) -> None:
    for entry in team.get("chips", []):
        if chip is not None and entry["name"] == chip:
            entry["status_for_entry"] = "active"
