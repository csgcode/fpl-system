"""Token-refresh tests.

Every token here is synthetic and unsigned — the module reads claims for
routing, never trusts them as an authority, so a real signature buys nothing.
The invariants under test: the endpoint is derived rather than assumed, a
credential is never sent anywhere but an allow-listed provider, rotation is
persisted, and no token value reaches an exception message.
"""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta

import pytest

from fpl.auth import AuthCredentials
from fpl.refresh import (
    RefreshPlan,
    TokenRefreshError,
    decode_claims,
    derive_plan,
    expiry_of,
    is_expired,
    refresh,
    seconds_until_expiry,
)

PING_ISS = "https://auth.pingone.eu/68340de1-dfb9-412e-937c-20172986d129/as"
BRANDED_ISS = "https://account.premierleague.com/as"
API_CLIENT = "bfcbaf69-aade-4c1b-8f00-c1cb8a193030"
PING_CLIENT = "1f243d70-a140-4035-8c41-341f5af5aa12"


def jwt(**claims) -> str:
    def segment(payload: dict) -> str:
        raw = json.dumps(payload).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    return f"{segment({'alg': 'RS256'})}.{segment(claims)}.synthetic-signature"


def bearer(exp_offset_min: int = 60) -> str:
    return jwt(
        iss=BRANDED_ISS,
        client_id=API_CLIENT,
        exp=int((datetime.now(UTC) + timedelta(minutes=exp_offset_min)).timestamp()),
    )


def refresh_jwt() -> str:
    return jwt(
        iss=PING_ISS,
        scope="openid profile offline_access",
        exp=int((datetime.now(UTC) + timedelta(days=180)).timestamp()),
    )


def credentials(**overrides) -> AuthCredentials:
    payload = {
        "headers": {
            "x-api-authorization": f"Bearer {bearer()}",
            "user-agent": "synthetic-agent",
        },
        "cookies": {
            "refresh_token": refresh_jwt(),
            "access_token": jwt(iss=PING_ISS, client_id=PING_CLIENT, exp=1),
            "datadome": "synthetic-fingerprint",
        },
    }
    payload.update(overrides)
    return AuthCredentials(**payload)


class FakeTokenGateway:
    def __init__(self, response: dict) -> None:
        self._response = response
        self.calls: list[tuple[str, dict[str, str]]] = []

    def post_form(self, url: str, data: dict[str, str]) -> dict:
        self.calls.append((url, data))
        return self._response


# --- claim reading -------------------------------------------------------


def test_decode_claims_reads_payload_of_a_jwt():
    assert decode_claims(jwt(iss="x", client_id="y"))["client_id"] == "y"


@pytest.mark.parametrize(
    "value", ["", "not-a-jwt", "a.b", "a.b.c.d", "a.!!!.c", "a." + "eyJ9" + ".c"]
)
def test_decode_claims_returns_empty_for_non_jwt(value):
    assert decode_claims(value) == {}


def test_decode_claims_strips_bearer_prefix():
    assert decode_claims(f"Bearer {jwt(iss='x')}")["iss"] == "x"


def test_expiry_and_remaining_seconds_track_the_exp_claim():
    token = bearer(exp_offset_min=30)
    assert expiry_of(token) is not None
    remaining = seconds_until_expiry(token)
    assert 29 * 60 < remaining <= 30 * 60


def test_is_expired_is_true_past_expiry_and_respects_skew():
    assert is_expired(bearer(exp_offset_min=-1))
    assert not is_expired(bearer(exp_offset_min=10))
    # Inside the skew window the token is treated as already gone, which is
    # what lets a caller refresh before a request rather than after a 401.
    assert is_expired(bearer(exp_offset_min=4), skew_s=300)


def test_unreadable_expiry_is_not_expired():
    # No exp claim: let the server decide rather than refusing locally.
    assert not is_expired(jwt(iss="x"))
    assert seconds_until_expiry("not-a-jwt") is None


# --- plan derivation -----------------------------------------------------


def test_endpoint_comes_from_the_bearer_issuer_not_the_refresh_issuer():
    # The two issuers differ: a branded domain fronts the identity provider.
    # The API trusts the branded one, so that is where the grant must go.
    plan = derive_plan(credentials())
    assert plan.endpoint == f"{BRANDED_ISS}/token"


def test_client_id_is_the_refresh_tokens_own_client_not_the_bearers():
    # The grant is validated against the client the refresh token was issued
    # to. Sending the bearer's client id instead is rejected live with
    # "invalid_grant - Refresh token does not exist".
    plan = derive_plan(credentials())
    assert plan.client_id == PING_CLIENT
    assert plan.client_id != API_CLIENT


def test_plan_identifies_the_slots_it_will_replace():
    plan = derive_plan(credentials())
    assert plan.refresh_cookie == "refresh_token"
    assert plan.bearer_header == "x-api-authorization"
    assert plan.access_cookie == "access_token"


def test_overrides_win_over_derivation():
    plan = derive_plan(
        credentials(),
        endpoint="https://account.premierleague.com/other/token",
        client_id="explicit-client",
    )
    assert plan.endpoint == "https://account.premierleague.com/other/token"
    assert plan.client_id == "explicit-client"


def test_refresh_token_found_by_scope_when_the_cookie_name_is_unfamiliar():
    creds = AuthCredentials(
        headers={"x-api-authorization": bearer()},
        cookies={"session_grant": refresh_jwt()},
    )
    assert derive_plan(creds).refresh_cookie == "session_grant"


def test_missing_refresh_token_names_the_cookies_present_but_no_values():
    creds = AuthCredentials(
        headers={"x-api-authorization": bearer()},
        cookies={"datadome": "synthetic-fingerprint"},
    )
    with pytest.raises(TokenRefreshError) as exc_info:
        derive_plan(creds)
    message = str(exc_info.value)
    assert "datadome" in message
    assert "synthetic-fingerprint" not in message


def test_endpoint_falls_back_to_the_refresh_issuer_without_a_bearer_header():
    creds = AuthCredentials(
        headers={"user-agent": "synthetic-agent"},
        cookies={"refresh_token": refresh_jwt(), "access_token": jwt(
            iss=PING_ISS, client_id=PING_CLIENT, exp=1
        )},
    )
    plan = derive_plan(creds)
    assert plan.endpoint == f"{PING_ISS}/token"
    assert plan.bearer_header is None
    assert plan.client_id == PING_CLIENT


def test_underivable_endpoint_asks_for_the_override():
    creds = AuthCredentials(
        headers={},
        cookies={"refresh_token": jwt(scope="offline_access", exp=1)},
    )
    with pytest.raises(TokenRefreshError, match="--token-endpoint"):
        derive_plan(creds)


def test_underivable_client_id_asks_for_the_override():
    creds = AuthCredentials(
        headers={},
        cookies={"refresh_token": jwt(iss=PING_ISS, scope="offline_access", exp=1)},
    )
    with pytest.raises(TokenRefreshError, match="--client-id"):
        derive_plan(creds)


# --- the SSRF guard ------------------------------------------------------


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://account.premierleague.com/as/token",  # not TLS
        "https://localhost/as/token",
        "https://127.0.0.1/as/token",
        "https://169.254.169.254/as/token",  # cloud metadata
        "https://10.0.0.5/as/token",
        "https://evil.test/as/token",
        "https://evil-premierleague.com/as/token",  # suffix, not subdomain
        "https://premierleague.com.evil.test/as/token",
        "//account.premierleague.com/as/token",  # no scheme
    ],
)
def test_refresh_token_is_never_sent_to_a_disallowed_endpoint(endpoint):
    with pytest.raises(TokenRefreshError):
        derive_plan(credentials(), endpoint=endpoint)


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://account.premierleague.com/as/token",
        "https://auth.pingone.eu/env/as/token",
        "https://premierleague.com/as/token",
    ],
)
def test_known_provider_endpoints_are_allowed(endpoint):
    assert derive_plan(credentials(), endpoint=endpoint).endpoint == endpoint


def test_a_hostile_iss_claim_cannot_redirect_the_credential():
    # The iss claim is read from a token whose signature is never verified,
    # so it is untrusted input to an outbound request carrying a secret.
    creds = AuthCredentials(
        headers={"x-api-authorization": jwt(iss="https://evil.test/as", client_id="c")},
        cookies={"refresh_token": refresh_jwt()},
    )
    with pytest.raises(TokenRefreshError, match="not an allowed identity"):
        derive_plan(creds)


# --- the exchange --------------------------------------------------------


def test_refresh_posts_the_grant_and_folds_the_new_bearer_back_in():
    creds = credentials()
    plan = derive_plan(creds)
    fresh = bearer(exp_offset_min=60)
    gateway = FakeTokenGateway({"access_token": fresh, "expires_in": 3600})

    outcome = refresh(creds, plan, gateway)

    url, form = gateway.calls[0]
    assert url == f"{BRANDED_ISS}/token"
    assert form["grant_type"] == "refresh_token"
    assert form["client_id"] == PING_CLIENT
    assert form["refresh_token"] == creds.cookies["refresh_token"]
    # The capture sent 'Bearer <jwt>', so the replacement keeps that shape.
    assert outcome.credentials.headers["x-api-authorization"] == f"Bearer {fresh}"
    assert outcome.credentials.cookies["access_token"] == fresh
    assert outcome.expires_in_s == 3600


def test_a_raw_bearer_header_stays_raw():
    creds = credentials(
        headers={"x-api-authorization": bearer(), "user-agent": "synthetic-agent"}
    )
    plan = derive_plan(creds)
    fresh = bearer()
    outcome = refresh(creds, plan, FakeTokenGateway({"access_token": fresh}))
    assert outcome.credentials.headers["x-api-authorization"] == fresh


def test_rotated_refresh_token_is_persisted():
    # Rotation is single-use: failing to save the new one loses the session.
    creds = credentials()
    rotated = refresh_jwt()
    outcome = refresh(
        creds,
        derive_plan(creds),
        FakeTokenGateway({"access_token": bearer(), "refresh_token": rotated}),
    )
    assert outcome.rotated_refresh is True
    assert outcome.credentials.cookies["refresh_token"] == rotated


def test_unrotated_refresh_token_is_left_alone():
    creds = credentials()
    outcome = refresh(
        creds, derive_plan(creds), FakeTokenGateway({"access_token": bearer()})
    )
    assert outcome.rotated_refresh is False
    assert outcome.credentials.cookies["refresh_token"] == creds.cookies["refresh_token"]


def test_unrelated_headers_and_cookies_survive_untouched():
    creds = credentials()
    outcome = refresh(
        creds, derive_plan(creds), FakeTokenGateway({"access_token": bearer()})
    )
    assert outcome.credentials.headers["user-agent"] == "synthetic-agent"
    assert outcome.credentials.cookies["datadome"] == "synthetic-fingerprint"


def test_input_credentials_are_not_mutated():
    # A failed or partial refresh must not leave a half-updated session.
    creds = credentials()
    before = (dict(creds.headers), dict(creds.cookies))
    refresh(creds, derive_plan(creds), FakeTokenGateway({"access_token": bearer()}))
    assert (dict(creds.headers), dict(creds.cookies)) == before


def test_response_without_an_access_token_fails_naming_only_keys():
    creds = credentials()
    gateway = FakeTokenGateway({"error": "invalid_grant", "trace": "abc"})
    with pytest.raises(TokenRefreshError) as exc_info:
        refresh(creds, derive_plan(creds), gateway)
    message = str(exc_info.value)
    assert "invalid_grant" not in message  # a value, not a key
    assert "error" in message and "trace" in message


def test_no_token_value_appears_in_any_failure_message():
    creds = credentials()
    plan = RefreshPlan(
        endpoint=f"{BRANDED_ISS}/token",
        client_id=API_CLIENT,
        refresh_cookie="refresh_token",
        bearer_header="x-api-authorization",
        access_cookie="access_token",
    )
    with pytest.raises(TokenRefreshError) as exc_info:
        refresh(creds, plan, FakeTokenGateway({}))
    message = str(exc_info.value)
    for secret in (*creds.headers.values(), *creds.cookies.values()):
        assert secret not in message


def test_plan_description_carries_no_secrets():
    creds = credentials()
    described = "\n".join(derive_plan(creds).describe())
    for secret in (*creds.headers.values(), *creds.cookies.values()):
        assert secret not in described
    # Client id is a public OIDC identifier and is useful to see.
    assert PING_CLIENT in described
