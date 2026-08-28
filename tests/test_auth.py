"""Credential-file tests. Secret values are synthetic; the invariant under
test is that they never surface in reprs or error messages."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from fpl.auth import AuthCredentials, AuthMissingError, load_auth

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
