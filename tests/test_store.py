from datetime import datetime, timedelta, timezone

import pytest

from fpl.store import SnapshotMissingError, SnapshotStore


class FakeClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, hours: float) -> None:
        self.now += timedelta(hours=hours)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def store(tmp_path, clock) -> SnapshotStore:
    return SnapshotStore(tmp_path, now=clock)


def test_save_load_roundtrip_with_fetch_metadata(store, clock):
    store.save(2, "bootstrap", {"a": 1}, "https://example.test/api")
    assert store.load(2, "bootstrap") == {"a": 1}
    assert store.fetched_at(2, "bootstrap") == clock.now


def test_age_hours_tracks_clock(store, clock):
    store.save(2, "bootstrap", {}, "url")
    clock.advance(hours=6)
    assert store.age_hours(2, "bootstrap") == pytest.approx(6.0)


def test_age_hours_none_when_missing(store):
    assert store.age_hours(2, "bootstrap") is None


def test_refresh_archives_previous_snapshot(store, clock, tmp_path):
    store.save(2, "bootstrap", {"version": 1}, "url")
    clock.advance(hours=1)
    store.save(2, "bootstrap", {"version": 2}, "url")

    assert store.load(2, "bootstrap") == {"version": 2}
    archived = list((tmp_path / "gw2" / ".archive").glob("bootstrap-*.json"))
    assert len(archived) == 1
    assert '"version": 1' in archived[0].read_text()


def test_load_missing_raises_typed_error(store):
    with pytest.raises(SnapshotMissingError):
        store.load(3, "fixtures")


def test_nested_snapshot_names(store):
    store.save(2, "players/summary-7", {"history": []}, "url")
    assert store.exists(2, "players/summary-7")
    assert store.load(2, "players/summary-7") == {"history": []}
