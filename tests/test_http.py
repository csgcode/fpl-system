import pytest
import requests

from fpl import http
from fpl.api import BASE_URL, FplApi
from fpl.http import RequestsGateway


class FakeResponse:
    def __init__(self, payload, error=None) -> None:
        self._payload = payload
        self._error = error

    def raise_for_status(self) -> None:
        if self._error is not None:
            raise self._error

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
        self.mounted: list[str] = []
        self.requests: list[tuple[str, float]] = []
        self.closed = False
        self.response = FakeResponse({})

    def mount(self, prefix, adapter) -> None:
        self.mounted.append(prefix)

    def get(self, url, timeout=None):
        self.requests.append((url, timeout))
        return self.response

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def session(monkeypatch) -> FakeSession:
    fake = FakeSession()
    monkeypatch.setattr(http.requests, "Session", lambda: fake)
    return fake


def test_get_json_returns_object_payload(session):
    session.response = FakeResponse({"a": 1})
    assert RequestsGateway().get_json("https://example.test/x") == {"a": 1}


def test_get_json_returns_array_payload(session):
    session.response = FakeResponse([1, 2])
    assert RequestsGateway().get_json("https://example.test/x") == [1, 2]


@pytest.mark.parametrize("payload", [7, "text", None, True])
def test_get_json_rejects_non_container_payloads(session, payload):
    session.response = FakeResponse(payload)
    with pytest.raises(ValueError, match="expected a JSON object or array"):
        RequestsGateway().get_json("https://example.test/x")


def test_get_json_propagates_http_errors(session):
    session.response = FakeResponse({}, error=requests.HTTPError("503"))
    with pytest.raises(requests.HTTPError):
        RequestsGateway().get_json("https://example.test/x")


def test_gateway_sets_timeout_and_user_agent(session):
    RequestsGateway(timeout_s=2.5).get_json("https://example.test/x")
    assert session.requests == [("https://example.test/x", 2.5)]
    assert session.headers["User-Agent"] == "fpl-system/1.0"
    assert "https://" in session.mounted


def test_close_releases_the_session(session):
    RequestsGateway().close()
    assert session.closed


def test_context_manager_closes_the_session(session):
    with RequestsGateway() as gateway:
        assert not session.closed
        gateway.get_json("https://example.test/x")
    assert session.closed


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        (lambda api: api.bootstrap(), f"{BASE_URL}/bootstrap-static/"),
        (lambda api: api.fixtures(), f"{BASE_URL}/fixtures/"),
        (lambda api: api.element_summary(7), f"{BASE_URL}/element-summary/7/"),
        (lambda api: api.entry(42), f"{BASE_URL}/entry/42/"),
        (lambda api: api.entry_history(42), f"{BASE_URL}/entry/42/history/"),
        (lambda api: api.event_picks(42, 5), f"{BASE_URL}/entry/42/event/5/picks/"),
    ],
)
def test_api_endpoint_urls(call, expected):
    class RecordingGateway:
        def get_json(self, url):
            return {"url": url}

    fetched = call(FplApi(RecordingGateway()))
    assert fetched.url == expected
    assert fetched.payload == {"url": expected}
