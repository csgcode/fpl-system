"""FPL API endpoints. Returns raw payloads plus their source URL — parsing
and persistence are the service layer's job."""

from __future__ import annotations

from dataclasses import dataclass

from fpl.http import HttpGateway

BASE_URL = "https://fantasy.premierleague.com/api"


@dataclass(frozen=True)
class Fetched:
    url: str
    payload: dict | list


class FplApi:
    def __init__(self, gateway: HttpGateway) -> None:
        self._gateway = gateway

    def bootstrap(self) -> Fetched:
        return self._get(f"{BASE_URL}/bootstrap-static/")

    def fixtures(self) -> Fetched:
        return self._get(f"{BASE_URL}/fixtures/")

    def element_summary(self, player_id: int) -> Fetched:
        return self._get(f"{BASE_URL}/element-summary/{player_id}/")

    def entry(self, team_id: int) -> Fetched:
        return self._get(f"{BASE_URL}/entry/{team_id}/")

    def _get(self, url: str) -> Fetched:
        return Fetched(url=url, payload=self._gateway.get_json(url))
