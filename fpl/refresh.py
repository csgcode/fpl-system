"""Mint a fresh bearer token from the stored refresh token.

The captured bearer lives 60 minutes; the refresh token beside it lives
months. Re-capturing by hand therefore fails for a reason that has nothing to
do with the capture being wrong — it is simply late. This module trades the
long-lived credential for a new short-lived one and writes both back, so a
single capture keeps working for as long as the refresh token does.

Everything is derived, never hardcoded: the token endpoint comes from the
`iss` claim of the token the API actually reads, and the client id from that
same token's `client_id` claim. FPL's auth shape has already moved twice, and
a hardcoded endpoint would be the thing that breaks next.

No credential value is returned, logged, printed or placed in an exception
message anywhere in this module. Claim *names* and non-secret OIDC metadata
(issuer, client id, expiry) are the only things that reach a caller.
"""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from urllib.parse import urlsplit

from fpl.auth import AuthCredentials

BEARER_PREFIX = "Bearer "
AUTH_HEADER_HINT = "authorization"
OFFLINE_SCOPE = "offline_access"
REFRESH_COOKIE_HINT = "refresh_token"
ACCESS_COOKIE_HINT = "access_token"
TOKEN_PATH = "token"
GRANT_TYPE = "refresh_token"

# A refresh token is a months-long bearer credential, and the endpoint it is
# sent to comes from an `iss` claim we do not verify the signature of (or from
# an operator's --token-endpoint). Both are untrusted input to an outbound
# request, so the destination is allow-listed by registrable domain: FPL's own
# estate and the identity provider behind it. Extend this list when the
# provider moves — never widen it to make one call work.
REQUIRED_SCHEME = "https"
ALLOWED_ENDPOINT_DOMAINS = ("premierleague.com", "pingone.eu")


class TokenRefreshError(RuntimeError):
    """Refresh could not be attempted or did not succeed.

    Messages quote endpoints, client ids, claim names and OAuth error codes —
    never a token value.
    """


class TokenGateway(Protocol):
    def post_form(self, url: str, data: dict[str, str]) -> dict: ...


@dataclass(frozen=True)
class RefreshPlan:
    """Where the refresh goes and which stored values it replaces."""

    endpoint: str
    client_id: str
    refresh_cookie: str
    bearer_header: str | None
    access_cookie: str | None

    def describe(self) -> list[str]:
        lines = [
            f"endpoint: {self.endpoint}",
            f"client id: {self.client_id}",
            f"refresh token: cookie {self.refresh_cookie}",
        ]
        target = self.bearer_header or "(none — no authorization-like header)"
        lines.append(f"bearer target: header {target}")
        if self.access_cookie:
            lines.append(f"also updating: cookie {self.access_cookie}")
        return lines


@dataclass(frozen=True)
class RefreshOutcome:
    credentials: AuthCredentials
    expires_in_s: int | None
    rotated_refresh: bool
    bearer_expiry: datetime | None


def decode_claims(token: str) -> dict:
    """Claims of a JWT, or {} for anything that is not one.

    Signature is not verified: we are reading routing metadata out of a token
    the browser already obtained, not trusting it as an authority.
    """
    body = token.strip()
    if body.lower().startswith(BEARER_PREFIX.lower()):
        body = body[len(BEARER_PREFIX) :]
    parts = body.split(".")
    if len(parts) != 3:
        return {}
    segment = parts[1]
    padded = segment + "=" * (-len(segment) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded)
        claims = json.loads(decoded)
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return {}
    return claims if isinstance(claims, dict) else {}


def expiry_of(token: str) -> datetime | None:
    exp = decode_claims(token).get("exp")
    if not isinstance(exp, (int, float)):
        return None
    return datetime.fromtimestamp(exp, UTC)


def seconds_until_expiry(token: str, *, now: datetime | None = None) -> float | None:
    expiry = expiry_of(token)
    if expiry is None:
        return None
    return (expiry - (now or datetime.now(UTC))).total_seconds()


def is_expired(token: str, *, skew_s: float = 0.0, now: datetime | None = None) -> bool:
    """True when the token is past expiry, or within `skew_s` of it.

    Unreadable expiry counts as not-expired: the caller should try the request
    and let the server decide, rather than refuse on a claim it cannot read.
    """
    remaining = seconds_until_expiry(token, now=now)
    return remaining is not None and remaining <= skew_s


def derive_plan(
    credentials: AuthCredentials,
    *,
    endpoint: str | None = None,
    client_id: str | None = None,
) -> RefreshPlan:
    """Work out where to refresh and what to replace, from the tokens held.

    The endpoint is taken from the issuer of the *bearer* token rather than of
    the refresh token: the two can differ (a branded custom domain in front of
    the identity provider), and the one that matters is whichever issuer the
    API trusts.
    """
    refresh_cookie = _find_refresh_cookie(credentials)
    bearer_header = _find_bearer_header(credentials)
    access_cookie = _find_access_cookie(credentials, exclude=refresh_cookie)

    resolved_endpoint = endpoint or _derive_endpoint(
        credentials, bearer_header, refresh_cookie
    )
    resolved_client = client_id or _derive_client_id(
        credentials, bearer_header, access_cookie, refresh_cookie
    )
    _require_https(resolved_endpoint)
    return RefreshPlan(
        endpoint=resolved_endpoint,
        client_id=resolved_client,
        refresh_cookie=refresh_cookie,
        bearer_header=bearer_header,
        access_cookie=access_cookie,
    )


def refresh(
    credentials: AuthCredentials, plan: RefreshPlan, gateway: TokenGateway
) -> RefreshOutcome:
    """Exchange the refresh token for a new bearer and fold it back in.

    The returned credentials are a new object; the input is untouched, so a
    failed call cannot leave a half-updated session behind.
    """
    payload = gateway.post_form(
        plan.endpoint,
        {
            "grant_type": GRANT_TYPE,
            "refresh_token": credentials.cookies[plan.refresh_cookie],
            "client_id": plan.client_id,
        },
    )
    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise TokenRefreshError(
            "token endpoint returned no access_token — response keys: "
            f"{sorted(payload)}"
        )

    headers = dict(credentials.headers)
    cookies = dict(credentials.cookies)

    if plan.bearer_header is not None:
        headers[plan.bearer_header] = _match_bearer_shape(
            credentials.headers[plan.bearer_header], access_token
        )
    if plan.access_cookie is not None:
        cookies[plan.access_cookie] = access_token

    rotated = payload.get("refresh_token")
    rotated_refresh = isinstance(rotated, str) and bool(rotated)
    if rotated_refresh:
        # Rotation is single-use: the old token is dead the moment the server
        # issues this one, so it must be persisted or the session is lost.
        cookies[plan.refresh_cookie] = rotated

    expires_in = payload.get("expires_in")
    return RefreshOutcome(
        credentials=AuthCredentials(headers=headers, cookies=cookies),
        expires_in_s=expires_in if isinstance(expires_in, int) else None,
        rotated_refresh=rotated_refresh,
        bearer_expiry=expiry_of(access_token),
    )


def _find_refresh_cookie(credentials: AuthCredentials) -> str:
    """Prefer the token that says it may be used offline; fall back to name.

    Scope is the substantive test — `offline_access` is what makes a refresh
    grant legal — so it wins over a cookie that merely looks right.
    """
    by_scope = [
        name
        for name, value in sorted(credentials.cookies.items())
        if OFFLINE_SCOPE in str(decode_claims(value).get("scope", ""))
        and "exp" in decode_claims(value)
    ]
    named = [
        name
        for name in sorted(credentials.cookies)
        if REFRESH_COOKIE_HINT in name.lower()
    ]
    for candidates in (
        [n for n in by_scope if REFRESH_COOKIE_HINT in n.lower()],
        named,
        by_scope,
    ):
        if candidates:
            return candidates[0]
    raise TokenRefreshError(
        "no refresh token in the credentials — expected a cookie named "
        f"'{REFRESH_COOKIE_HINT}' or one scoped '{OFFLINE_SCOPE}'; "
        f"cookies present: {sorted(credentials.cookies)}. Re-capture while "
        "logged in (see docs/api-write.md)"
    )


def _find_bearer_header(credentials: AuthCredentials) -> str | None:
    for name in sorted(credentials.headers):
        if AUTH_HEADER_HINT in name.lower() and decode_claims(
            credentials.headers[name]
        ):
            return name
    return None


def _find_access_cookie(credentials: AuthCredentials, *, exclude: str) -> str | None:
    for name in sorted(credentials.cookies):
        if name == exclude:
            continue
        if ACCESS_COOKIE_HINT in name.lower() and decode_claims(
            credentials.cookies[name]
        ):
            return name
    return None


def _derive_endpoint(
    credentials: AuthCredentials, bearer_header: str | None, refresh_cookie: str
) -> str:
    sources = []
    if bearer_header is not None:
        sources.append(credentials.headers[bearer_header])
    sources.append(credentials.cookies[refresh_cookie])
    for token in sources:
        issuer = decode_claims(token).get("iss")
        if isinstance(issuer, str) and issuer:
            return f"{issuer.rstrip('/')}/{TOKEN_PATH}"
    raise TokenRefreshError(
        "no 'iss' claim in the bearer or refresh token, so the token endpoint "
        "cannot be derived — pass --token-endpoint explicitly"
    )


def _derive_client_id(
    credentials: AuthCredentials,
    bearer_header: str | None,
    access_cookie: str | None,
    refresh_cookie: str,
) -> str:
    """The client the REFRESH token belongs to, not the one the bearer came from.

    A refresh grant is validated against the client the token was issued to.
    FPL runs two clients in one environment — the refresh token's sibling is
    the access-token cookie, while the API bearer comes from a different
    client — and presenting the bearer's client id is rejected with
    `invalid_grant — Refresh token does not exist`. Verified 2026-09-18.
    """
    sources = []
    if access_cookie is not None:
        sources.append(credentials.cookies[access_cookie])
    sources.append(credentials.cookies[refresh_cookie])
    if bearer_header is not None:
        sources.append(credentials.headers[bearer_header])
    for token in sources:
        client = decode_claims(token).get("client_id")
        if isinstance(client, str) and client:
            return client
    raise TokenRefreshError(
        "no 'client_id' claim in any stored token, so the OAuth client cannot "
        "be derived — pass --client-id explicitly"
    )


def _match_bearer_shape(existing: str, access_token: str) -> str:
    """Keep the captured header's own prefix convention.

    The header carried a raw JWT or a 'Bearer '-prefixed one; whichever FPL
    sent is what FPL expects back.
    """
    if existing.strip().lower().startswith(BEARER_PREFIX.lower()):
        return f"{BEARER_PREFIX}{access_token}"
    return access_token


def _require_https(endpoint: str) -> None:
    """Refuse to send the refresh token anywhere but a known provider, on TLS.

    Both inputs that reach here are untrusted — an unverified `iss` claim and
    an operator override — and the payload is a credential valid for months.
    A bare scheme check would still allow an internal address or an attacker's
    host, so the registrable domain is checked too.
    """
    parts = urlsplit(endpoint)
    host = (parts.hostname or "").lower().rstrip(".")
    if parts.scheme != REQUIRED_SCHEME or not host:
        raise TokenRefreshError(
            f"refresh endpoint must be {REQUIRED_SCHEME}:// with a host — "
            f"refusing to send a refresh token to {endpoint!r}"
        )
    if not _is_allowed_host(host):
        raise TokenRefreshError(
            f"refresh endpoint host {host!r} is not an allowed identity "
            f"provider (expected a subdomain of: "
            f"{', '.join(ALLOWED_ENDPOINT_DOMAINS)}) — refusing to send a "
            "refresh token there. If the provider has moved, extend "
            "ALLOWED_ENDPOINT_DOMAINS in fpl/refresh.py deliberately"
        )


def _is_allowed_host(host: str) -> bool:
    # Exact domain or a subdomain of it — never a suffix match, which would
    # accept 'evil-premierleague.com'.
    return any(
        host == domain or host.endswith(f".{domain}")
        for domain in ALLOWED_ENDPOINT_DOMAINS
    )
