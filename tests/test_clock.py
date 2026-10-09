"""The CLI clock: real time, except in replay mode where a clock file pins it
to the recorded gameweek so freshness and deadline arithmetic match the
recordings."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from fpl.clock import CLOCK_FILE, REPLAY_ENV, utcnow, write_clock
from fpl.store import SnapshotStore

FROZEN = datetime(2026, 9, 18, 12, 49, 57, tzinfo=UTC)


def test_real_time_outside_replay_mode(monkeypatch, tmp_path):
    monkeypatch.delenv(REPLAY_ENV, raising=False)
    write_clock(tmp_path, FROZEN, anchored_at=datetime.now(UTC))
    assert abs(utcnow() - datetime.now(UTC)) < timedelta(seconds=5)


def test_real_time_in_replay_mode_without_a_clock_file(monkeypatch, tmp_path):
    monkeypatch.setenv(REPLAY_ENV, str(tmp_path))
    assert abs(utcnow() - datetime.now(UTC)) < timedelta(seconds=5)


def test_replay_clock_starts_at_the_pinned_instant(monkeypatch, tmp_path):
    monkeypatch.setenv(REPLAY_ENV, str(tmp_path))
    write_clock(tmp_path, FROZEN, anchored_at=datetime.now(UTC))
    assert FROZEN <= utcnow() < FROZEN + timedelta(seconds=5)


def test_replay_clock_advances_with_real_elapsed_time(monkeypatch, tmp_path):
    """Successive snapshot rotations need distinct archive stamps."""
    monkeypatch.setenv(REPLAY_ENV, str(tmp_path))
    write_clock(tmp_path, FROZEN, anchored_at=datetime.now(UTC) - timedelta(hours=2))
    assert FROZEN + timedelta(hours=2) <= utcnow() < FROZEN + timedelta(hours=2, seconds=5)


def test_a_malformed_clock_file_refuses_naming_it(monkeypatch, tmp_path):
    monkeypatch.setenv(REPLAY_ENV, str(tmp_path))
    (tmp_path / CLOCK_FILE).write_text(json.dumps({"now": "not a time"}), "utf-8")
    with pytest.raises(ValueError, match=CLOCK_FILE):
        utcnow()


def test_a_naive_pinned_instant_is_refused(tmp_path):
    with pytest.raises(ValueError, match="timezone"):
        write_clock(tmp_path, datetime(2026, 9, 18), anchored_at=datetime.now(UTC))


def test_snapshot_store_stamps_fetches_with_the_replay_clock(monkeypatch, tmp_path):
    replay = tmp_path / "replay"
    replay.mkdir()
    monkeypatch.setenv(REPLAY_ENV, str(replay))
    write_clock(replay, FROZEN, anchored_at=datetime.now(UTC))
    store = SnapshotStore(tmp_path / "raw")
    store.save(5, "bootstrap", {"events": []}, "seed://test")
    age = store.age_hours(5, "bootstrap")
    assert age is not None and 0 <= age < 0.01
    meta = json.loads((tmp_path / "raw/gw5/.meta/bootstrap.json").read_text("utf-8"))
    assert datetime.fromisoformat(meta["fetched_at"]) - FROZEN < timedelta(seconds=5)
