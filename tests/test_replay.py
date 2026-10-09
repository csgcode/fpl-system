"""Replay gateway: serves recorded API bodies from a directory so the CLI can
run against frozen fixtures without touching the network."""

from __future__ import annotations

import json

import pytest
import requests

from fpl.api import BASE_URL
from fpl.replay import (
    REPLAY_ENV,
    ReplayGateway,
    ReplayMissError,
    ReplayWriteRefusedError,
    recording_key,
    replay_dir,
)
from fpl.write import SessionExpiredError


def record(root, key, payload):
    path = root / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def served(root):
    lines = (root / "served.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


@pytest.mark.parametrize(
    ("path", "key"),
    [
        ("bootstrap-static/", "bootstrap-static"),
        ("fixtures/", "fixtures"),
        ("element-summary/17/", "element-summary/17"),
        ("entry/8455344/", "entry/8455344"),
        ("entry/8455344/history/", "entry/8455344/history"),
        ("entry/8455344/event/5/picks/", "entry/8455344/event/5/picks"),
        ("my-team/8455344/", "my-team/8455344"),
    ],
)
def test_recording_key_mirrors_the_api_path(path, key):
    assert recording_key(f"{BASE_URL}/{path}") == key


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/api/bootstrap-static/",
        "http://fantasy.premierleague.com/api/bootstrap-static/",
        f"{BASE_URL}/../secrets/",
        f"{BASE_URL}/element-summary/1%2F..%2F/",
        f"{BASE_URL}/Bootstrap-Static/",
        f"{BASE_URL}/bootstrap-static/?x=1",
        f"{BASE_URL}/",
    ],
)
def test_recording_key_is_none_for_foreign_hosts_and_bad_segments(url):
    assert recording_key(url) is None


def test_get_json_serves_the_recorded_body(tmp_path):
    record(tmp_path, "entry/42/history", {"current": [1, 2]})

    gateway = ReplayGateway(tmp_path)

    assert gateway.get_json(f"{BASE_URL}/entry/42/history/") == {"current": [1, 2]}


def test_missing_recording_is_a_request_exception_naming_the_url(tmp_path):
    gateway = ReplayGateway(tmp_path)
    url = f"{BASE_URL}/element-summary/9/"

    with pytest.raises(ReplayMissError, match="element-summary/9") as caught:
        gateway.get_json(url)
    assert isinstance(caught.value, requests.RequestException)


def test_foreign_host_is_a_miss_even_when_a_file_matches(tmp_path):
    record(tmp_path, "bootstrap-static", {"events": []})

    with pytest.raises(ReplayMissError):
        ReplayGateway(tmp_path).get_json("https://example.com/api/bootstrap-static/")


def test_injected_status_raises_http_error_carrying_it(tmp_path):
    record(tmp_path, "element-summary/1", {"history": []})
    (tmp_path / "errors.json").write_text(
        json.dumps({"element-summary/1": 503}), encoding="utf-8"
    )

    with pytest.raises(requests.HTTPError) as caught:
        ReplayGateway(tmp_path).get_json(f"{BASE_URL}/element-summary/1/")
    assert caught.value.response.status_code == 503
    assert caught.value.response.reason == "Replayed"


def test_injected_401_is_a_session_error_on_the_write_path(tmp_path):
    (tmp_path / "errors.json").write_text(
        json.dumps({"my-team/7": 401}), encoding="utf-8"
    )

    with pytest.raises(SessionExpiredError):
        ReplayGateway(tmp_path, session_errors=True).get_json(f"{BASE_URL}/my-team/7/")


def test_injected_401_is_a_plain_http_error_on_the_read_path(tmp_path):
    (tmp_path / "errors.json").write_text(
        json.dumps({"entry/7": 401}), encoding="utf-8"
    )

    with pytest.raises(requests.HTTPError):
        ReplayGateway(tmp_path).get_json(f"{BASE_URL}/entry/7/")


def test_post_is_refused(tmp_path):
    with pytest.raises(ReplayWriteRefusedError):
        ReplayGateway(tmp_path).post_json(f"{BASE_URL}/transfers/", {"x": 1})


def test_every_request_is_logged_with_its_outcome(tmp_path):
    record(tmp_path, "fixtures", [])
    (tmp_path / "errors.json").write_text(
        json.dumps({"element-summary/2": 503}), encoding="utf-8"
    )
    gateway = ReplayGateway(tmp_path)

    gateway.get_json(f"{BASE_URL}/fixtures/")
    for url in (f"{BASE_URL}/element-summary/1/", f"{BASE_URL}/element-summary/2/"):
        with pytest.raises(requests.RequestException):
            gateway.get_json(url)

    assert served(tmp_path) == [
        {"url": f"{BASE_URL}/fixtures/", "key": "fixtures", "outcome": "hit"},
        {
            "url": f"{BASE_URL}/element-summary/1/",
            "key": "element-summary/1",
            "outcome": "miss",
        },
        {
            "url": f"{BASE_URL}/element-summary/2/",
            "key": "element-summary/2",
            "outcome": "error:503",
        },
    ]


@pytest.mark.parametrize("value", [None, ""])
def test_replay_dir_is_none_when_unset_or_empty(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(REPLAY_ENV, raising=False)
    else:
        monkeypatch.setenv(REPLAY_ENV, value)
    assert replay_dir() is None


def test_replay_dir_reads_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv(REPLAY_ENV, str(tmp_path))
    assert replay_dir() == tmp_path
