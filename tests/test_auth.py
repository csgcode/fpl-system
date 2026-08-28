"""Credential-file tests. Secret values are synthetic; the invariant under
test is that they never surface in reprs or error messages."""

from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest
from pydantic import ValidationError

from fpl import auth as auth_module
from fpl.auth import (
    AuthCredentials,
    AuthMissingError,
    has_auth_bearing_header,
    load_auth,
    redacted_summary,
    save_auth,
)

SECRET = "synthetic-s3cr3t-token-value"

REPO_ROOT = Path(__file__).resolve().parent.parent


def write_auth(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "auth.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_missing_file_raises_with_setup_hint(tmp_path):
    path = tmp_path / "auth.json"
    with pytest.raises(AuthMissingError) as exc_info:
        load_auth(path)
    message = str(exc_info.value)
    assert str(path) in message
    assert "docs/api-write.md" in message


def test_loads_arbitrary_header_and_cookie_names(tmp_path):
    path = write_auth(
        tmp_path,
        {
            "headers": {"X-Some-Future-Auth-Header": SECRET},
            "cookies": {"session_v2": SECRET, "bot_shield": "abc"},
        },
    )
    credentials = load_auth(path)
    assert credentials.headers == {"X-Some-Future-Auth-Header": SECRET}
    assert credentials.cookies == {"session_v2": SECRET, "bot_shield": "abc"}


def test_headers_only_and_cookies_only_are_both_accepted(tmp_path):
    headers_only = load_auth(write_auth(tmp_path, {"headers": {"A": "x"}}))
    assert headers_only.cookies == {}
    cookies_only = load_auth(write_auth(tmp_path, {"cookies": {"B": "y"}}))
    assert cookies_only.headers == {}


def test_repr_and_str_never_contain_secret_values(tmp_path):
    credentials = load_auth(
        write_auth(tmp_path, {"headers": {"Authorization": SECRET}})
    )
    assert SECRET not in repr(credentials)
    assert SECRET not in str(credentials)
    assert SECRET not in f"{credentials}"


def test_empty_credentials_are_rejected(tmp_path):
    path = write_auth(tmp_path, {"headers": {}, "cookies": {}})
    with pytest.raises(ValidationError, match="no credentials"):
        load_auth(path)


def test_unknown_top_level_fields_are_rejected(tmp_path):
    path = write_auth(tmp_path, {"headers": {"A": "x"}, "token": "loose"})
    with pytest.raises(ValidationError):
        load_auth(path)


def test_committed_example_file_parses(tmp_path):
    example = REPO_ROOT / "data" / "auth.example.json"
    credentials = load_auth(example)
    assert credentials.headers or credentials.cookies


def test_committed_example_file_carries_no_stale_2024_cookie_names(tmp_path):
    credentials = load_auth(REPO_ROOT / "data" / "auth.example.json")
    assert "pl_profile" not in credentials.cookies
    assert {"datadome", "cf_clearance", "global_sso_id", "pl_guest_id"} <= set(
        credentials.cookies
    )
    assert has_auth_bearing_header(credentials)


# --- writing ----------------------------------------------------------------


def test_save_auth_round_trips_through_load_auth(tmp_path):
    credentials = AuthCredentials(
        headers={"x-api-authorization": f"Bearer {SECRET}"},
        cookies={"datadome": SECRET},
    )
    path = tmp_path / "nested" / "auth.json"
    save_auth(path, credentials)
    assert load_auth(path) == credentials


def test_save_auth_writes_an_owner_only_file(tmp_path):
    path = tmp_path / "auth.json"
    save_auth(path, AuthCredentials(headers={"a": "x"}))
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_save_auth_leaves_working_credentials_intact_when_the_write_fails(
    tmp_path, monkeypatch
):
    path = tmp_path / "auth.json"
    save_auth(path, AuthCredentials(headers={"x-api-authorization": "original"}))

    def explode(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(auth_module.os, "replace", explode)
    with pytest.raises(OSError):
        save_auth(path, AuthCredentials(headers={"x-api-authorization": "replacement"}))
    assert load_auth(path).headers == {"x-api-authorization": "original"}
    assert not list(tmp_path.glob(".*.tmp"))


def test_save_auth_tightens_permissions_on_an_existing_file(tmp_path):
    path = tmp_path / "auth.json"
    path.write_text("{}", encoding="utf-8")
    path.chmod(0o644)
    save_auth(path, AuthCredentials(cookies={"datadome": "x"}))
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


# --- redaction --------------------------------------------------------------


def test_redacted_summary_reports_names_and_lengths_only():
    credentials = AuthCredentials(
        headers={"x-api-authorization": SECRET}, cookies={"datadome": "abcd"}
    )
    text = "\n".join(redacted_summary(credentials))
    assert "headers (1)" in text
    assert "cookies (1)" in text
    assert "x-api-authorization" in text
    assert f"<{len(SECRET)} chars>" in text
    assert "datadome: <4 chars>" in text
    assert SECRET not in text


def test_auth_bearing_header_detection_is_a_hint_not_a_schema():
    assert has_auth_bearing_header(AuthCredentials(headers={"Authorization": "x"}))
    assert has_auth_bearing_header(AuthCredentials(headers={"x-api-authorization": "x"}))
    assert not has_auth_bearing_header(AuthCredentials(cookies={"datadome": "x"}))
    assert not has_auth_bearing_header(AuthCredentials(headers={"accept": "x"}))
