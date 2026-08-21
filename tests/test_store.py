from datetime import datetime, timedelta, timezone

import pytest

from fpl.store import (
    ArchiveCollisionError,
    SnapshotMissingError,
    SnapshotStore,
    UnsafeSnapshotNameError,
)


class FakeClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, hours: float = 0, microseconds: float = 0) -> None:
        self.now += timedelta(hours=hours, microseconds=microseconds)


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


def test_sub_second_refreshes_both_survive_in_archive(store, clock, tmp_path):
    store.save(2, "bootstrap", {"version": 1}, "url")
    clock.advance(microseconds=1)
    store.save(2, "bootstrap", {"version": 2}, "url")
    clock.advance(microseconds=1)
    store.save(2, "bootstrap", {"version": 3}, "url")

    archived = sorted((tmp_path / "gw2" / ".archive").glob("bootstrap-*.json"))
    assert len(archived) == 2
    assert {p.read_text() for p in archived} >= {'{\n "version": 1\n}'}
    assert store.load(2, "bootstrap") == {"version": 3}


def test_archive_collision_refuses_to_replace_earlier_snapshot(store, tmp_path):
    """A stopped clock makes two archives claim the same stamp; the earlier
    snapshot must survive, even at the cost of failing the write."""
    store.save(2, "bootstrap", {"version": 1}, "url")
    store.save(2, "bootstrap", {"version": 2}, "url")
    with pytest.raises(ArchiveCollisionError):
        store.save(2, "bootstrap", {"version": 3}, "url")

    archived = list((tmp_path / "gw2" / ".archive").glob("bootstrap-*.json"))
    assert len(archived) == 1
    assert '"version": 1' in archived[0].read_text()
    assert store.load(2, "bootstrap") == {"version": 2}


def test_load_missing_raises_typed_error(store):
    with pytest.raises(SnapshotMissingError):
        store.load(3, "fixtures")


def test_snapshot_missing_error_carries_optional_hint(store):
    error = SnapshotMissingError(3, "bootstrap")
    assert error.fetch_hint is None
    assert error.with_hint("bootstrap --gw 3").fetch_hint == "bootstrap --gw 3"


def test_nested_snapshot_names(store):
    store.save(2, "players/summary-7", {"history": []}, "url")
    assert store.exists(2, "players/summary-7")
    assert store.load(2, "players/summary-7") == {"history": []}


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "players/../../escape",
        "/etc/passwd",
        "..",
        "",
        "players//summary-7",
    ],
)
def test_unsafe_names_are_rejected(store, name):
    with pytest.raises(UnsafeSnapshotNameError):
        store.save(2, name, {}, "url")


def test_unsafe_name_never_writes_outside_the_root(store, tmp_path):
    with pytest.raises(UnsafeSnapshotNameError):
        store.save(2, "../../escape", {}, "url")
    assert not (tmp_path.parent / "escape.json").exists()


def test_fetched_at_none_when_meta_missing(store, tmp_path):
    store.save(2, "bootstrap", {"a": 1}, "url")
    (tmp_path / "gw2" / ".meta" / "bootstrap.json").unlink()
    assert store.fetched_at(2, "bootstrap") is None
    assert store.age_hours(2, "bootstrap") is None


@pytest.mark.parametrize(
    "meta_text",
    ["not json at all", "{}", '{"fetched_at": null}', '{"fetched_at": "nonsense"}',
     '{"fetched_at": 17}', "[]"],
)
def test_fetched_at_none_when_meta_unusable(store, tmp_path, meta_text):
    store.save(2, "bootstrap", {"a": 1}, "url")
    (tmp_path / "gw2" / ".meta" / "bootstrap.json").write_text(meta_text)
    assert store.fetched_at(2, "bootstrap") is None
    assert store.age_hours(2, "bootstrap") is None


def test_fetched_at_coerces_naive_timestamp_to_utc(store, tmp_path, clock):
    store.save(2, "bootstrap", {"a": 1}, "url")
    (tmp_path / "gw2" / ".meta" / "bootstrap.json").write_text(
        '{"fetched_at": "2026-08-21T06:00:00", "source_url": "url"}'
    )
    assert store.fetched_at(2, "bootstrap") == datetime(
        2026, 8, 21, 6, 0, tzinfo=timezone.utc
    )
    assert store.age_hours(2, "bootstrap") == pytest.approx(6.0)


def test_corrupt_meta_still_archives_on_refresh(store, tmp_path):
    store.save(2, "bootstrap", {"version": 1}, "url")
    (tmp_path / "gw2" / ".meta" / "bootstrap.json").write_text("corrupt")
    store.save(2, "bootstrap", {"version": 2}, "url")
    assert store.load(2, "bootstrap") == {"version": 2}
    assert list((tmp_path / "gw2" / ".archive").glob("bootstrap-*.json"))


def test_interrupted_write_leaves_the_previous_snapshot_intact(
    store, clock, tmp_path, monkeypatch
):
    store.save(2, "bootstrap", {"version": 1}, "url")
    clock.advance(hours=1)
    monkeypatch.setattr(
        "fpl.store.os.replace", lambda *_: (_ for _ in ()).throw(OSError("disk full"))
    )

    with pytest.raises(OSError):
        store.save(2, "bootstrap", {"version": 2}, "url")

    archived = list((tmp_path / "gw2" / ".archive").glob("bootstrap-*.json"))
    assert len(archived) == 1
    assert '"version": 1' in archived[0].read_text()
    assert not (tmp_path / "gw2" / "bootstrap.json").exists()


def test_save_leaves_no_temp_files_behind(store, tmp_path):
    store.save(2, "bootstrap", {"a": 1}, "url")
    assert not list((tmp_path / "gw2").glob("*.tmp"))
    assert not list((tmp_path / "gw2" / ".meta").glob("*.tmp"))


def test_save_text_writes_utf8_with_archive_and_sidecar(store, clock, tmp_path):
    path = store.save_text(2, "players-slim.csv", "id,name\n1,Ødegaard\n", "derived://x")
    assert path.read_text(encoding="utf-8").endswith("Ødegaard\n")
    assert store.file_path(2, "players-slim.csv") == path

    clock.advance(hours=1)
    store.save_text(2, "players-slim.csv", "id,name\n2,Muñoz\n", "derived://x")
    archived = list((tmp_path / "gw2" / ".archive").glob("players-slim-*.csv"))
    assert len(archived) == 1
    assert "Ødegaard" in archived[0].read_text(encoding="utf-8")
    meta = (tmp_path / "gw2" / ".meta" / "players-slim.csv").read_text()
    assert "derived://x" in meta


def test_save_text_meta_does_not_collide_with_json_snapshot(store, tmp_path):
    store.save(2, "prior-season", {"players": {}}, "url")
    store.save_text(2, "prior-season.csv", "x\n", "url")
    assert (tmp_path / "gw2" / ".meta" / "prior-season.json").is_file()
    assert (tmp_path / "gw2" / ".meta" / "prior-season.csv").is_file()
