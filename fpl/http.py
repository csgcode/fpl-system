"""HTTP boundary. Everything network-facing lives behind HttpGateway so the
rest of the system (and every test) can substitute a fake."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from fpl.auth import AuthCredentials

# Headers the token POST must own itself. Replaying the capture's versions
# would describe the captured body, not this one.
_TOKEN_POST_DROPS = frozenset({"content-type", "content-length", "accept"})


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
        payload = response.json()
        if not isinstance(payload, (dict, list)):
            raise ValueError(
                f"expected a JSON object or array from {url}, "
                f"got {type(payload).__name__}"
            )
        return payload

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> RequestsGateway:
        return self


    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class RequestsTokenGateway:
    """POSTs an OAuth form grant to the identity provider.

    Separate from RequestsGateway because it talks to the auth server rather
    than the FPL API, and POSTs a form rather than reading JSON. The captured
    browser headers and cookies are mirrored: the token endpoint sits behind
    the same bot protection as the rest of the site, and a bare request looks
    nothing like the browser that was issued the credential.

    Retries are deliberately absent. A refresh grant can rotate the token
    server-side, so a retried POST risks presenting a token the server has
    already burned — a failure must surface, not be silently repeated.
    """

    def __init__(
        self, credentials: AuthCredentials, timeout_s: float = 10.0
    ) -> None:
        self._timeout_s = timeout_s
        self._session = requests.Session()
        self._session.headers["User-Agent"] = "fpl-system/1.0"
        for name, value in credentials.headers.items():
            if name.lower() not in _TOKEN_POST_DROPS:
                self._session.headers[name] = value
        self._session.cookies.update(credentials.cookies)

    def post_form(self, url: str, data: dict[str, str]) -> dict:
        response = self._session.post(url, data=data, timeout=self._timeout_s)
        payload = _json_or_none(response)
        if response.status_code >= 400:
            raise TokenEndpointError(_oauth_failure(response.status_code, payload))
        if not isinstance(payload, dict):
            raise TokenEndpointError(
                f"token endpoint returned {response.status_code} with a "
                f"non-JSON body ({len(response.content)} bytes)"
            )
        return payload

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> RequestsTokenGateway:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class TokenEndpointError(RuntimeError):
    """The identity provider refused the grant.

    Carries the OAuth `error`/`error_description` when the server sent one —
    those name the fault (expired token, unknown client) and are not secrets.
    """


def _json_or_none(response: requests.Response) -> object:
    try:
        return response.json()
    except ValueError:
        return None


def _oauth_failure(status: int, payload: object) -> str:
    if isinstance(payload, dict):
        code = payload.get("error")
        detail = payload.get("error_description") or payload.get("message")
        if code or detail:
            described = " — ".join(str(p) for p in (code, detail) if p)
            return f"token endpoint returned {status}: {described}"
    return f"token endpoint returned {status} with no OAuth error body"
