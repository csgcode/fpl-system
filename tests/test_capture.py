"""Browser-capture parsing tests. Every credential value here is synthetic;
the invariants under test are which headers survive the capture, how the
cookie header is split, and that a non-FPL or unparseable capture is refused.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from fpl.capture import CurlParseError, is_git_ignored, parse_curl

TOKEN = "synthetic-jwt-header.synthetic-jwt-payload.synthetic-jwt-signature"
DATADOME = "synthetic-datadome-value"
CF_CLEARANCE = "synthetic-cf=clearance=value"

CAPTURE = f"""curl 'https://fantasy.premierleague.com/api/my-team/1234567/' \\
  -H 'accept: application/json' \\
  -H 'accept-language: en-GB,en;q=0.9' \\
  -H 'priority: u=1, i' \\
  -H 'sec-ch-ua: "Chromium";v="140", "Not=A?Brand";v="24"' \\
  -H 'sec-ch-ua-mobile: ?0' \\
  -H 'sec-fetch-mode: cors' \\
  -H 'x-api-authorization: Bearer {TOKEN}' \\
  -H 'x-api-language: en' \\
  -b 'datadome={DATADOME}; cf_clearance={CF_CLEARANCE}; req_language=en' \\
  --compressed
"""


def capture_with(*extra_lines: str) -> str:
    lines = CAPTURE.rstrip("\n").splitlines()
    return "\n".join([*lines[:-1], *extra_lines, lines[-1]]) + "\n"


# --- headers ---------------------------------------------------------------


def test_keeps_browser_fingerprint_and_auth_headers():
    capture = parse_curl(CAPTURE)
    headers = capture.credentials.headers
    assert headers["x-api-authorization"] == f"Bearer {TOKEN}"
    assert headers["x-api-language"] == "en"
    assert headers["accept"] == "application/json"
    assert headers["priority"] == "u=1, i"
    assert headers["sec-ch-ua"] == '"Chromium";v="140", "Not=A?Brand";v="24"'


def test_drops_transport_headers_requests_must_own():
    capture = parse_curl(
        capture_with(
            "  -H 'content-length: 0' \\",
            "  -H 'host: fantasy.premierleague.com' \\",
            "  -H 'connection: keep-alive' \\",
            "  -H 'accept-encoding: gzip, deflate, br' \\",
            "  -H 'content-type: application/json' \\",
            "  -H 'transfer-encoding: chunked' \\",
        )
    )
    names = {name.lower() for name in capture.credentials.headers}
    assert names.isdisjoint(
        {
            "content-length",
            "host",
            "connection",
            "accept-encoding",
            "content-type",
            "transfer-encoding",
        }
    )


def test_drops_per_request_tracing_headers():
    capture = parse_curl(
        capture_with(
            "  -H 'baggage: sentry-environment=prod,sentry-release=synthetic' \\",
            "  -H 'sentry-trace: 0123456789abcdef0123456789abcdef-0123456789abcdef-1' \\",
        )
    )
    names = {name.lower() for name in capture.credentials.headers}
    assert "baggage" not in names
    assert "sentry-trace" not in names


def test_drops_http2_pseudo_headers():
    capture = parse_curl(
        capture_with(
            "  -H ':authority: fantasy.premierleague.com' \\",
            "  -H ':method: GET' \\",
            "  -H ':path: /api/my-team/1234567/' \\",
            "  -H ':scheme: https' \\",
        )
    )
    headers = capture.credentials.headers
    assert all(name and not name.startswith(":") for name in headers)
    assert "authority" not in {name.lower() for name in headers}


def test_long_form_header_flag_is_accepted():
    capture = parse_curl(capture_with("  --header 'x-extra: kept' \\"))
    assert capture.credentials.headers["x-extra"] == "kept"


def test_a_body_flag_value_is_never_mistaken_for_the_url():
    capture = parse_curl(
        capture_with("  --data-raw 'https://evil.test/not-the-url' \\")
    )
    assert capture.url == "https://fantasy.premierleague.com/api/my-team/1234567/"


# --- cookies ---------------------------------------------------------------


def test_cookie_flag_is_split_into_individual_cookies():
    cookies = parse_curl(CAPTURE).credentials.cookies
    assert cookies["datadome"] == DATADOME
    assert cookies["req_language"] == "en"


def test_cookie_values_containing_equals_are_kept_whole():
    assert parse_curl(CAPTURE).credentials.cookies["cf_clearance"] == CF_CLEARANCE


def test_a_cookie_header_is_split_the_same_way_as_the_cookie_flag():
    capture = parse_curl(
        f"curl 'https://fantasy.premierleague.com/api/my-team/1/' "
        f"-H 'cookie: datadome={DATADOME}; pl_guest_id=synthetic-guest'"
    )
    assert capture.credentials.cookies == {
        "datadome": DATADOME,
        "pl_guest_id": "synthetic-guest",
    }
    assert "cookie" not in {n.lower() for n in capture.credentials.headers}


def test_analytics_cookies_are_kept_verbatim():
    capture = parse_curl(
        capture_with("  -b 'AMCV_synthetic%40AdobeOrg=1234|MCMID|5678; s_nr=9' \\")
    )
    assert capture.credentials.cookies["AMCV_synthetic%40AdobeOrg"] == "1234|MCMID|5678"
    assert capture.credentials.cookies["s_nr"] == "9"


# --- shape -----------------------------------------------------------------


def test_line_continuations_are_joined_before_parsing():
    assert "\\\n" in CAPTURE
    assert len(parse_curl(CAPTURE).credentials.headers) == 8


def test_carriage_return_line_continuations_are_joined():
    capture = parse_curl(CAPTURE.replace("\n", "\r\n"))
    assert capture.credentials.headers["x-api-language"] == "en"


def test_url_query_and_fragment_are_stripped_from_the_reported_url():
    capture = parse_curl(
        "curl 'https://fantasy.premierleague.com/api/my-team/1/?token=synthetic#frag' "
        "-H 'x-api-authorization: Bearer x'"
    )
    assert capture.url == "https://fantasy.premierleague.com/api/my-team/1/"


def test_url_userinfo_is_stripped_from_the_reported_url():
    capture = parse_curl(
        "curl 'https://someone:synthetic-password@fantasy.premierleague.com/api/x' "
        "-H 'x-api-authorization: Bearer x'"
    )
    assert capture.url == "https://fantasy.premierleague.com/api/x"


def test_header_names_that_are_not_http_tokens_are_dropped():
    capture = parse_curl(
        capture_with(
            "  -H 'bad name: value' \\",
            "  -H 'x-escape\x1b[31m: value' \\",
        )
    )
    names = list(capture.credentials.headers)
    assert "bad name" not in names
    assert all("\x1b" not in name for name in names)


def test_control_characters_in_values_are_dropped():
    capture = parse_curl(
        capture_with(
            "  -H 'x-injected: line-one\nSet-Cookie: evil=1' \\",
            "  -b 'x_injected=one\ntwo' \\",
        )
    )
    assert "x-injected" not in capture.credentials.headers
    assert "x_injected" not in capture.credentials.cookies


def test_parsed_credentials_redact_their_values_in_reprs():
    credentials = parse_curl(CAPTURE).credentials
    assert TOKEN not in repr(credentials)
    assert DATADOME not in str(credentials)


# --- refusals --------------------------------------------------------------


def test_refuses_a_capture_with_no_headers_or_cookies():
    with pytest.raises(CurlParseError, match="Copy as cURL"):
        parse_curl("this is not a curl command at all\n")


def test_refuses_a_capture_for_another_site():
    with pytest.raises(CurlParseError, match="fantasy.premierleague.com"):
        parse_curl("curl 'https://example.test/api/x' -H 'x-api-authorization: Bearer x'")


def test_refuses_a_lookalike_host():
    with pytest.raises(CurlParseError, match="fantasy.premierleague.com"):
        parse_curl(
            "curl 'https://fantasy.premierleague.com.evil.test/api/x' "
            "-H 'x-api-authorization: Bearer x'"
        )


def test_accepts_a_subdomain_of_the_fpl_host():
    capture = parse_curl(
        "curl 'https://users.fantasy.premierleague.com/accounts/me/' "
        "-H 'x-api-authorization: Bearer x'"
    )
    assert capture.url.startswith("https://users.fantasy.premierleague.com/")


def test_refuses_a_capture_with_no_url():
    with pytest.raises(CurlParseError, match="no request URL"):
        parse_curl("curl -H 'x-api-authorization: Bearer x'")


def test_refusal_messages_never_quote_credential_values():
    with pytest.raises(CurlParseError) as exc_info:
        parse_curl(f"curl 'https://example.test/x' -H 'x-api-authorization: {TOKEN}'")
    assert TOKEN not in str(exc_info.value)


# --- capture-file hygiene ---------------------------------------------------


needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


@needs_git
def test_git_ignored_capture_file_is_reported_as_ignored(tmp_path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("curl-request\n", encoding="utf-8")
    capture_file = tmp_path / "curl-request"
    capture_file.write_text("curl 'https://example.test/'", encoding="utf-8")
    assert is_git_ignored(capture_file) is True


@needs_git
def test_tracked_capture_file_is_reported_as_not_ignored(tmp_path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    capture_file = tmp_path / "curl-request"
    capture_file.write_text("curl 'https://example.test/'", encoding="utf-8")
    assert is_git_ignored(capture_file) is False


def test_outside_a_git_repo_the_answer_is_unknown_not_false(tmp_path):
    capture_file = tmp_path / "curl-request"
    capture_file.write_text("curl 'https://example.test/'", encoding="utf-8")
    assert is_git_ignored(capture_file) is None


def test_a_missing_git_binary_is_unknown_not_a_crash(tmp_path, monkeypatch):
    def explode(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", explode)
    assert is_git_ignored(Path(tmp_path / "curl-request")) is None
