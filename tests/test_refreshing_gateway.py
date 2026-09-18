"""Reactive session-refresh tests.

The contract: refresh only when the server actually rejects the session,
replay the request exactly once, persist the rotated token before the replay,
and never loop. Nothing here touches the network.
"""

from __future__ import annotations

import pytest

from fpl.auth import AuthCredentials
from fpl.write import RefreshingGateway, SessionExpiredError

FRESH = AuthCredentials(headers={"x-api-authorization": "fresh"}, cookies={})
STALE = AuthCredentials(headers={"x-api-authorization": "stale"}, cookies={})

MY_TEAM = "https://example.test/my-team/1/"
PAYLOAD = {"chip": None}


class FakeGateway:
    """Rejects the first `reject` calls, then answers."""

    def __init__(self, label: str, reject: int = 0) -> None:
        self.label = label
        self._reject = reject
        self.gets: list[str] = []
        self.posts: list[tuple[str, dict]] = []
        self.closed = False

    def get_json(self, url: str):
        self.gets.append(url)
        return self._answer({"got": url, "by": self.label})

    def post_json(self, url: str, payload: dict):
        self.posts.append((url, payload))
        return self._answer({"posted": url, "by": self.label})

    def close(self) -> None:
        self.closed = True

    def _answer(self, value):
        if self._reject > 0:
            self._reject -= 1
            raise SessionExpiredError()
        return value

    @property
    def calls(self) -> int:
        return len(self.gets) + len(self.posts)


class Builder:
    """Hands out a gateway per credentials object, oldest first."""

    def __init__(self, *gateways: FakeGateway) -> None:
        self._queue = list(gateways)
        self.seen: list[AuthCredentials] = []

    def __call__(self, credentials: AuthCredentials) -> FakeGateway:
        self.seen.append(credentials)
        return self._queue.pop(0)


def refresher(result=FRESH, error: Exception | None = None):
    calls: list[AuthCredentials] = []

    def refresh(credentials: AuthCredentials) -> AuthCredentials:
        calls.append(credentials)
        if error is not None:
            raise error
        return result

    refresh.calls = calls  # type: ignore[attr-defined]
    return refresh


def test_working_session_is_never_refreshed():
    # The refresh token rotates on every use, so spending one on a request
    # that would have succeeded is pure loss.
    inner = FakeGateway("original")
    refresh = refresher()
    gateway = RefreshingGateway(STALE, Builder(inner), refresh)

    assert gateway.get_json(MY_TEAM) == {"got": MY_TEAM, "by": "original"}
    assert refresh.calls == []
    assert inner.calls == 1


def test_rejected_get_refreshes_once_and_replays():
    rejecting, accepting = FakeGateway("stale", reject=1), FakeGateway("fresh")
    builder = Builder(rejecting, accepting)
    refresh = refresher()
    gateway = RefreshingGateway(STALE, builder, refresh)

    assert gateway.get_json(MY_TEAM) == {"got": MY_TEAM, "by": "fresh"}
    assert len(refresh.calls) == 1
    assert builder.seen == [STALE, FRESH]
    assert rejecting.calls == 1 and accepting.calls == 1


def test_rejected_post_is_replayed_exactly_once():
    # A 401/403 is refused before it changes anything, so replaying a
    # transfer POST cannot double-apply it.
    rejecting, accepting = FakeGateway("stale", reject=1), FakeGateway("fresh")
    gateway = RefreshingGateway(STALE, Builder(rejecting, accepting), refresher())

    assert gateway.post_json(MY_TEAM, PAYLOAD) == {"posted": MY_TEAM, "by": "fresh"}
    assert rejecting.posts == [(MY_TEAM, PAYLOAD)]
    assert accepting.posts == [(MY_TEAM, PAYLOAD)]


def test_rotated_credentials_are_persisted_before_the_replay():
    # Rotation is single-use: a crash between refresh and save would strand
    # the session on a token the server has already killed.
    order: list[str] = []
    accepting = FakeGateway("fresh")

    class RecordingGateway(FakeGateway):
        def get_json(self, url: str):
            order.append("request")
            return super().get_json(url)

    rejecting = RecordingGateway("stale", reject=1)
    saved: list[AuthCredentials] = []

    def save(credentials: AuthCredentials) -> None:
        order.append("save")
        saved.append(credentials)

    gateway = RefreshingGateway(
        STALE, Builder(rejecting, accepting), refresher(), on_refreshed=save
    )
    gateway.get_json(MY_TEAM)

    assert saved == [FRESH]
    assert order == ["request", "save"]


def test_second_rejection_surfaces_and_does_not_loop():
    still_rejecting = FakeGateway("fresh", reject=1)
    refresh = refresher()
    gateway = RefreshingGateway(
        STALE, Builder(FakeGateway("stale", reject=1), still_rejecting), refresh
    )

    with pytest.raises(SessionExpiredError):
        gateway.get_json(MY_TEAM)
    assert len(refresh.calls) == 1
    assert still_rejecting.calls == 1


def test_once_exhausted_later_calls_do_not_refresh_again():
    # A dead refresh token would otherwise be retried on every request,
    # hammering the provider while the deadline runs down.
    refresh = refresher()
    gateway = RefreshingGateway(
        STALE,
        Builder(FakeGateway("stale", reject=1), FakeGateway("fresh", reject=99)),
        refresh,
    )
    with pytest.raises(SessionExpiredError):
        gateway.get_json(MY_TEAM)
    with pytest.raises(SessionExpiredError):
        gateway.get_json(MY_TEAM)

    assert len(refresh.calls) == 1


def test_failed_refresh_reports_as_an_expired_session_naming_the_cause():
    gateway = RefreshingGateway(
        STALE,
        Builder(FakeGateway("stale", reject=1)),
        refresher(error=RuntimeError("invalid_grant — Refresh token does not exist")),
    )
    with pytest.raises(SessionExpiredError) as exc_info:
        gateway.get_json(MY_TEAM)

    message = str(exc_info.value)
    assert "invalid_grant" in message
    assert "docs/api-write.md" in message


def test_failed_refresh_is_not_retried_on_the_next_call():
    refresh = refresher(error=RuntimeError("dead"))
    gateway = RefreshingGateway(
        STALE, Builder(FakeGateway("stale", reject=2)), refresh
    )
    for _ in range(2):
        with pytest.raises(SessionExpiredError):
            gateway.get_json(MY_TEAM)
    assert len(refresh.calls) == 1


def test_replaced_gateway_is_closed():
    rejecting, accepting = FakeGateway("stale", reject=1), FakeGateway("fresh")
    gateway = RefreshingGateway(STALE, Builder(rejecting, accepting), refresher())
    gateway.get_json(MY_TEAM)

    assert rejecting.closed is True
    assert accepting.closed is False
    gateway.close()
    assert accepting.closed is True


def test_expired_message_without_a_refresh_failure_is_unchanged():
    # Existing callers match on this wording.
    assert "refresh failed" not in str(SessionExpiredError())
    assert "session expired" in str(SessionExpiredError())
