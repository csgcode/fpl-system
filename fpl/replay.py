"""Replay mode: the CLI serves recorded API bodies instead of the network.

Selected by the FPL_REPLAY_DIR environment variable, so an agent under
evaluation runs byte-identical commands while every request is answered from
a directory of recordings. A request with no recording fails loudly rather
than falling through to the network.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import NoReturn

import requests

from fpl.api import BASE_URL
from fpl.write import SessionExpiredError

REPLAY_ENV = "FPL_REPLAY_DIR"
SERVED_LOG = "served.jsonl"
ERRORS_FILE = "errors.json"

_SEGMENT = re.compile(r"^[a-z0-9-]+$")
_SESSION_STATUSES = frozenset({401, 403})


def replay_dir() -> Path | None:
    value = os.environ.get(REPLAY_ENV, "")
    return Path(value) if value else None


def recording_key(url: str) -> str | None:
    """The recording path for an FPL API URL, or None when the URL is not one
    the replay may answer. Segment validation also blocks path traversal."""
    prefix = f"{BASE_URL}/"
    if not url.startswith(prefix):
        return None
    segments = url[len(prefix):].rstrip("/").split("/")
    if not all(_SEGMENT.match(segment) for segment in segments):
        return None
    return "/".join(segments)


class ReplayMissError(requests.ConnectionError):
    pass


class ReplayWriteRefusedError(RuntimeError):
    pass


class ReplayGateway:
    """Satisfies both HttpGateway and WriteGateway.

    With `session_errors`, an injected 401/403 surfaces as the write path's
    SessionExpiredError, as the authenticated gateway raises it.
    """

    def __init__(self, root: Path, *, session_errors: bool = False) -> None:
        self._root = root
        self._session_errors = session_errors

    def get_json(self, url: str) -> dict | list:
        key = recording_key(url)
        status = self._injected_status(key)
        if status is not None:
            self._log(url, key, f"error:{status}")
            if self._session_errors and status in _SESSION_STATUSES:
                raise SessionExpiredError()
            raise requests.HTTPError(
                f"{status} Replayed for url: {url}", response=_response(url, status)
            )
        path = self._root / f"{key}.json" if key is not None else None
        if path is None or not path.is_file():
            self._log(url, key, "miss")
            raise ReplayMissError(f"no replay recording for {url}")
        self._log(url, key, "hit")
        return json.loads(path.read_text(encoding="utf-8"))

    def post_json(self, url: str, payload: dict) -> NoReturn:
        self._log(url, recording_key(url), "refused")
        raise ReplayWriteRefusedError(f"replay mode never sends a POST ({url})")

    def close(self) -> None:
        return None

    def _injected_status(self, key: str | None) -> int | None:
        path = self._root / ERRORS_FILE
        if key is None or not path.is_file():
            return None
        status = json.loads(path.read_text(encoding="utf-8")).get(key)
        return int(status) if status is not None else None

    def _log(self, url: str, key: str | None, outcome: str) -> None:
        line = json.dumps({"url": url, "key": key, "outcome": outcome})
        with (self._root / SERVED_LOG).open("a", encoding="utf-8") as log:
            log.write(line + "\n")


def _response(url: str, status: int) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response.reason = "Replayed"
    response.url = url
    return response
