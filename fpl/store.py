"""Snapshot persistence under data/raw/gw{N}/.

Invariant (CLAUDE.md): raw files are never destroyed. A refresh moves the
previous snapshot into .archive/ before writing the new one. Each snapshot
carries a .meta/ sidecar with fetch time and source URL for freshness checks
and provenance.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SnapshotMissingError(FileNotFoundError):
    def __init__(self, gw: int, name: str) -> None:
        super().__init__(f"no snapshot '{name}' for gw{gw}")
        self.gw = gw
        self.name = name


class SnapshotStore:
    def __init__(self, root: Path, now: Callable[[], datetime] = utcnow) -> None:
        self._root = root
        self._now = now

    def dir(self, gw: int) -> Path:
        return self._root / f"gw{gw}"

    def path(self, gw: int, name: str) -> Path:
        return self.dir(gw) / f"{name}.json"

    def exists(self, gw: int, name: str) -> bool:
        return self.path(gw, name).is_file()

    def fetched_at(self, gw: int, name: str) -> datetime | None:
        meta_path = self._meta_path(gw, name)
        if not meta_path.is_file():
            return None
        meta = json.loads(meta_path.read_text())
        return datetime.fromisoformat(meta["fetched_at"])

    def age_hours(self, gw: int, name: str) -> float | None:
        """None when the snapshot is missing or has no recorded fetch time."""
        if not self.exists(gw, name):
            return None
        fetched_at = self.fetched_at(gw, name)
        if fetched_at is None:
            return None
        return (self._now() - fetched_at).total_seconds() / 3600

    def save(self, gw: int, name: str, payload: dict | list, source_url: str) -> Path:
        path = self.path(gw, name)
        self._archive_existing(gw, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=1))
        meta_path = self._meta_path(gw, name)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(
            json.dumps(
                {"fetched_at": self._now().isoformat(), "source_url": source_url},
                indent=1,
            )
        )
        return path

    def load(self, gw: int, name: str) -> dict | list:
        if not self.exists(gw, name):
            raise SnapshotMissingError(gw, name)
        return json.loads(self.path(gw, name).read_text())

    def _meta_path(self, gw: int, name: str) -> Path:
        return self.dir(gw) / ".meta" / f"{name}.json"

    def _archive_existing(self, gw: int, name: str) -> None:
        path = self.path(gw, name)
        if not path.is_file():
            return
        fetched_at = self.fetched_at(gw, name)
        stamp = (fetched_at or self._now()).strftime("%Y%m%dT%H%M%SZ")
        archive_path = self.dir(gw) / ".archive" / f"{name}-{stamp}.json"
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        path.rename(archive_path)
