"""CLI tests for the session pre-flight (`auth-check`) and the browser-capture
importer (`auth-import`).

Every credential value is synthetic and every path is under tmp_path — these
tests never read or write the real data/auth.json.
"""

from __future__ import annotations

import json
import stat
from pathlib import Path

import requests

from fpl import __main__ as cli
from fpl.__main__ import main
from fpl.write import SessionExpiredError
from tests.test_write import MY_TEAM_URL, SECRET, FakeWriteGateway, current_my_team

TOKEN = f"Bearer {SECRET}"
DATADOME = "synthetic-datadome-cookie-value"


def write_auth(tmp_path: Path, payload: dict | None = None) -> Path:
    path = tmp_path / "auth.json"
    path.write_text(
        json.dumps(
            payload
            if payload is not None
            else {
                "headers": {"x-api-authorization": TOKEN, "x-api-language": "en"},
                "cookies": {"datadome": DATADOME, "cf_clearance": "synthetic-cf"},
            }
        ),
        encoding="utf-8",
    )
    return path


def run_auth_check(
    tmp_path: Path,
    gateway,
    *,
    team_id: str | None = "42",
    auth: Path | None = None,
    entry: dict | None = None,
) -> int:
    argv = ["--data-root", str(tmp_path / "raw"), "auth-check", "--gw", "2"]
    if team_id is not None:
        argv += ["--team-id", team_id]
    argv += ["--auth", str(auth if auth is not None else write_auth(tmp_path))]
    argv += ["--executor-root", str(tmp_path / "executor")]
    if entry is not None:
        entry_path = tmp_path / "entry.json"
        entry_path.write_text(json.dumps(entry), encoding="utf-8")
        argv += ["--entry-file", str(entry_path)]
    return main(argv, write_gateway_factory=lambda credentials: gateway)


def run_auth_import(tmp_path: Path, capture_text: str, out: Path | None = None) -> int:
    capture_file = tmp_path / "curl-request"
    capture_file.write_text(capture_text, encoding="utf-8")
    destination = out if out is not None else tmp_path / "auth.json"
    # Guard: an --out outside tmp_path would clobber the real credentials.
    assert destination.is_relative_to(tmp_path)
    return main(
        [
            "auth-import",
            "--curl-file",
            str(capture_file),
            "--out",
            str(destination),
        ]
    )


class FailingGateway:
    def __init__(self, error: Exception) -> None:
        self._error = error
        self.get_calls: list[str] = []
        self.posts: list = []

    def get_json(self, url: str):
        self.get_calls.append(url)
        raise self._error

    def post_json(self, url: str, payload: dict):
        raise self._error


def http_error(status: int, reason: str) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status
    response.reason = reason
    response.url = MY_TEAM_URL
    return requests.HTTPError(
        f"{status} Server Error: {reason} for url: {MY_TEAM_URL}", response=response
    )


CAPTURE = f"""curl 'https://fantasy.premierleague.com/api/my-team/1234567/' \\
  -H 'accept: application/json' \\
  -H 'baggage: sentry-environment=prod' \\
  -H 'sentry-trace: synthetic-trace-id-0' \\
  -H 'x-api-authorization: {TOKEN}' \\
  -b 'datadome={DATADOME}; req_language=en' \\
  --compressed
"""


# --- auth-check: pass -------------------------------------------------------


def test_auth_check_pass_reports_the_facts_that_prove_the_session_works(
    tmp_path, capsys
):
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run_auth_check(tmp_path, gateway) == 0
    out = capsys.readouterr().out
    assert "PASS" in out
    assert "entry 42" in out
    assert "squad 15" in out
    assert "bank 0.5" in out
    assert "budget 72.5" in out
    assert "api_value 100.3  (market basis" in out
    assert "free transfers 1" in out
    assert "bboost (available)" in out
    assert gateway.get_calls == [MY_TEAM_URL]


def test_auth_check_reports_credential_key_names_with_redacted_lengths(
    tmp_path, capsys
):
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    run_auth_check(tmp_path, gateway)
    out = capsys.readouterr().out
    assert "headers (2)" in out
    assert "cookies (2)" in out
    assert "x-api-authorization" in out
    assert "datadome" in out
    assert f"<{len(TOKEN)} chars>" in out
    assert SECRET not in out


def test_auth_check_uses_the_entry_file_team_id(tmp_path, capsys):
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run_auth_check(tmp_path, gateway, team_id=None, entry={"team_id": 42}) == 0
    assert gateway.get_calls == [MY_TEAM_URL]


def test_auth_check_writes_nothing_to_disk(tmp_path):
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    run_auth_check(tmp_path, gateway)
    assert not (tmp_path / "raw").exists()
    assert not (tmp_path / "executor").exists()


def test_auth_check_without_an_authorization_header_warns_but_still_passes(
    tmp_path, capsys
):
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    auth = write_auth(tmp_path, {"cookies": {"datadome": DATADOME}})
    assert run_auth_check(tmp_path, gateway, auth=auth) == 0
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "authorization" in captured.err.lower()
    assert "PASS" in captured.out


# --- auth-check: failures ---------------------------------------------------


def test_auth_check_expired_session_prints_the_generic_message_and_exits_one(
    tmp_path, capsys
):
    gateway = FailingGateway(SessionExpiredError())
    assert run_auth_check(tmp_path, gateway) == 1
    err = capsys.readouterr().err
    assert "session expired" in err
    assert "docs/api-write.md" in err


def test_auth_check_missing_auth_file_exits_one_before_any_request(tmp_path, capsys):
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run_auth_check(tmp_path, gateway, auth=tmp_path / "absent.json") == 1
    captured = capsys.readouterr()
    assert "no auth credentials" in captured.err
    assert "docs/api-write.md" in captured.err
    assert gateway.get_calls == []


def test_auth_check_null_team_id_exits_one_before_any_request(tmp_path, capsys):
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert (
        run_auth_check(tmp_path, gateway, team_id=None, entry={"team_id": None}) == 1
    )
    assert "team_id is null" in capsys.readouterr().err
    assert gateway.get_calls == []


def test_auth_check_without_a_team_id_source_exits_one(tmp_path, capsys):
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    argv = [
        "auth-check", "--gw", "2",
        "--auth", str(write_auth(tmp_path)),
        "--entry-file", str(tmp_path / "absent-entry.json"),
    ]
    assert main(argv, write_gateway_factory=lambda credentials: gateway) == 1
    assert "does not exist" in capsys.readouterr().err
    assert gateway.get_calls == []


def test_auth_check_reports_an_http_status_without_credential_values(tmp_path, capsys):
    gateway = FailingGateway(http_error(500, "Internal Server Error"))
    assert run_auth_check(tmp_path, gateway) == 1
    err = capsys.readouterr().err
    assert "FAIL" in err
    assert "500" in err
    assert "Internal Server Error" in err
    assert SECRET not in err


def test_auth_check_reports_a_network_failure(tmp_path, capsys):
    gateway = FailingGateway(requests.ConnectionError("name resolution failed"))
    assert run_auth_check(tmp_path, gateway) == 1
    err = capsys.readouterr().err
    assert "FAIL" in err
    assert "name resolution failed" in err


def test_auth_check_reports_an_unparseable_my_team_payload(tmp_path, capsys):
    gateway = FakeWriteGateway({MY_TEAM_URL: [{"picks": [{"element": "x"}]}]})
    assert run_auth_check(tmp_path, gateway) == 1
    assert "validation" in capsys.readouterr().err


# --- auth-import ------------------------------------------------------------


def test_auth_import_writes_the_captured_headers_and_cookies(tmp_path, capsys):
    out = tmp_path / "out" / "auth.json"
    assert run_auth_import(tmp_path, CAPTURE, out=out) == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["headers"]["x-api-authorization"] == TOKEN
    assert written["cookies"]["datadome"] == DATADOME
    assert written["cookies"]["req_language"] == "en"


def test_auth_import_drops_tracing_headers(tmp_path):
    out = tmp_path / "auth.json"
    run_auth_import(tmp_path, CAPTURE, out=out)
    headers = json.loads(out.read_text(encoding="utf-8"))["headers"]
    assert "baggage" not in headers
    assert "sentry-trace" not in headers


def test_auth_import_writes_an_owner_only_file(tmp_path):
    out = tmp_path / "auth.json"
    run_auth_import(tmp_path, CAPTURE, out=out)
    assert stat.S_IMODE(out.stat().st_mode) == 0o600


def test_auth_import_prints_the_source_url_names_and_lengths_only(tmp_path, capsys):
    run_auth_import(tmp_path, CAPTURE)
    out = capsys.readouterr().out
    assert "https://fantasy.premierleague.com/api/my-team/1234567/" in out
    assert "x-api-authorization" in out
    assert f"<{len(TOKEN)} chars>" in out
    assert "0600" in out
    assert SECRET not in out
    assert DATADOME not in out


def test_auth_import_refuses_an_unparseable_capture(tmp_path, capsys):
    out = tmp_path / "auth.json"
    assert run_auth_import(tmp_path, "not a curl command\n", out=out) == 1
    assert "Copy as cURL" in capsys.readouterr().err
    assert not out.exists()


def test_auth_import_refuses_a_capture_from_another_site(tmp_path, capsys):
    out = tmp_path / "auth.json"
    capture = "curl 'https://example.test/api/x' -H 'x-api-authorization: Bearer x'"
    assert run_auth_import(tmp_path, capture, out=out) == 1
    assert "fantasy.premierleague.com" in capsys.readouterr().err
    assert not out.exists()


def test_auth_import_refuses_a_missing_capture_file(tmp_path, capsys):
    missing = tmp_path / "nowhere" / "curl-request"
    assert main(
        ["auth-import", "--curl-file", str(missing), "--out", str(tmp_path / "a.json")]
    ) == 1
    err = capsys.readouterr().err
    assert "no curl capture at" in err
    assert str(missing) in err


def test_auth_import_warns_loudly_when_the_capture_is_not_git_ignored(
    tmp_path, capsys, monkeypatch
):
    monkeypatch.setattr(cli, "is_git_ignored", lambda path: False)
    assert run_auth_import(tmp_path, CAPTURE) == 0
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "git-ignored" in err
    assert "curl-request" in err


def test_auth_import_is_quiet_when_the_capture_is_git_ignored(
    tmp_path, capsys, monkeypatch
):
    monkeypatch.setattr(cli, "is_git_ignored", lambda path: True)
    assert run_auth_import(tmp_path, CAPTURE) == 0
    assert capsys.readouterr().err == ""


def test_auth_import_notes_but_does_not_fail_when_git_cannot_answer(
    tmp_path, capsys, monkeypatch
):
    monkeypatch.setattr(cli, "is_git_ignored", lambda path: None)
    assert run_auth_import(tmp_path, CAPTURE) == 0
    err = capsys.readouterr().err
    assert "WARNING" not in err
    assert "git-ignored" in err


def test_auth_import_output_is_accepted_by_auth_check(tmp_path, capsys):
    out = tmp_path / "imported.json"
    assert run_auth_import(tmp_path, CAPTURE, out=out) == 0
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    assert run_auth_check(tmp_path, gateway, auth=out) == 0
    assert "PASS" in capsys.readouterr().out


def test_auth_import_needs_no_gameweek(tmp_path):
    parser = cli.build_parser()
    args = parser.parse_args(
        ["auth-import", "--curl-file", str(tmp_path / "curl-request")]
    )
    assert not hasattr(args, "gw")


def test_auth_import_defaults_to_the_conventional_credentials_path():
    parser = cli.build_parser()
    args = parser.parse_args(["auth-import", "--curl-file", "curl-request"])
    assert args.out == Path("data/auth.json")


# --- secrets ----------------------------------------------------------------


def test_no_credential_value_appears_in_any_output(tmp_path, capsys):
    gateway = FakeWriteGateway({MY_TEAM_URL: [current_my_team()]})
    run_auth_check(tmp_path, gateway)
    run_auth_check(tmp_path, FailingGateway(SessionExpiredError()))
    run_auth_check(tmp_path, FailingGateway(http_error(403, "Forbidden")))
    run_auth_check(tmp_path, FailingGateway(requests.ConnectionError("boom")))
    run_auth_check(tmp_path, gateway, team_id=None, entry={"team_id": None})
    run_auth_check(tmp_path, gateway, auth=tmp_path / "absent.json")
    run_auth_import(tmp_path, CAPTURE, out=tmp_path / "imported.json")
    run_auth_import(tmp_path, "junk", out=tmp_path / "imported.json")
    captured = capsys.readouterr()
    for stream in (captured.out, captured.err):
        assert SECRET not in stream
        assert DATADOME not in stream
