"""HTTP boundary. Everything network-facing lives behind HttpGateway so the
rest of the system (and every test) can substitute a fake."""

from __future__ import annotations

from typing import Protocol

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class HttpGateway(Protocol):
    def get_json(self, url: str) -> dict | list: ...


class RequestsGateway:
    def __init__(self, timeout_s: float = 10.0) -> None:
        self._timeout_s = timeout_s
        self._session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retry))
        # The FPL API rejects some default library user agents.
        self._session.headers["User-Agent"] = "fpl-system/1.0"

    def get_json(self, url: str) -> dict | list:
        response = self._session.get(url, timeout=self._timeout_s)
        response.raise_for_status()
        return response.json()
