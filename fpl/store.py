"""Snapshot persistence under data/raw/gw{N}/.

Invariant (CLAUDE.md): raw files are never destroyed. A refresh moves the
previous snapshot into .archive/ before writing the new one, and refuses to
write if that would overwrite an existing archive entry. Each snapshot
carries a .meta/ sidecar with fetch time and source URL for freshness checks
and provenance. Writes are atomic: an interrupted write can never leave a
truncated file where a valid snapshot was.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

ARCHIVE_STAMP_FORMAT = "%Y%m%dT%H%M%S_%fZ"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SnapshotMissingError(FileNotFoundError):
    def __init__(self, gw: int, name: str, fetch_hint: str | None = None) -> None:
        super().__init__(f"no snapshot '{name}' for gw{gw}")
        self.gw = gw
        self.name = name
        self.fetch_hint = fetch_hint

    def with_hint(self, fetch_hint: str) -> SnapshotMissingError:
        self.fetch_hint = fetch_hint
        return self


class ArchiveCollisionError(RuntimeError):
    def __init__(self, path: Path) -> None:
        super().__init__(
            f"archive entry already exists, refusing to overwrite it: {path}"
        )
        self.path = path


class UnsafeSnapshotNameError(ValueError):
    def __init__(self, name: str) -> None:
        super().__init__(f"unsafe snapshot name: {name!r}")
        self.name = name


class SnapshotStore:
    def __init__(self, root: Path, now: Callable[[], datetime] = utcnow) -> None:
        self._root = root
        self._now = now

    def dir(self, gw: int) -> Path:
        return self._root / f"gw{gw}"

    def path(self, gw: int, name: str) -> Path:
        return self.file_path(gw, f"{_safe_name(name)}.json")

    def file_path(self, gw: int, filename: str) -> Path:
        return self.dir(gw) / _safe_name(filename)

    def exists(self, gw: int, name: str) -> bool:
        return self.path(gw, name).is_file()

    def fetched_at(self, gw: int, name: str) -> datetime | None:
        """None when there is no readable fetch time — a missing, corrupt or
        malformed sidecar is 'unknown age', never an error for the caller."""
        return self._fetched_at(self._meta_path(gw, f"{_safe_name(name)}.json"))

    def age_hours(self, gw: int, name: str) -> float | None:
        """None when the snapshot is missing or has no recorded fetch time."""
        if not self.exists(gw, name):
            return None
        fetched_at = self.fetched_at(gw, name)
        if fetched_at is None:
            return None
        return (self._now() - fetched_at).total_seconds() / 3600

    def save(self, gw: int, name: str, payload: dict | list, source_url: str) -> Path:
        return self._write(
            gw, f"{_safe_name(name)}.json", json.dumps(payload, indent=1), source_url
        )

    def save_text(self, gw: int, filename: str, text: str, source_url: str) -> Path:
        """Same archive + sidecar guarantees as save(), for derived text
        artefacts (CSV exports) that are not API payloads."""
        return self._write(gw, _safe_name(filename), text, source_url)

    def load(self, gw: int, name: str) -> dict | list:
        if not self.exists(gw, name):
            raise SnapshotMissingError(gw, name)
        return json.loads(self.path(gw, name).read_text(encoding="utf-8"))

    def _write(self, gw: int, filename: str, content: str, source_url: str) -> Path:
        path = self.dir(gw) / filename
        meta_path = self._meta_path(gw, filename)
        self._archive_existing(path, meta_path)
        _atomic_write(path, content)
        _atomic_write(
            meta_path,
            json.dumps(
                {"fetched_at": self._now().isoformat(), "source_url": source_url},
                indent=1,
            ),
        )
        return path

    def _meta_path(self, gw: int, filename: str) -> Path:
        return self.dir(gw) / ".meta" / filename

    def _fetched_at(self, meta_path: Path) -> datetime | None:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            fetched_at = datetime.fromisoformat(meta["fetched_at"])
        except (OSError, ValueError, TypeError, KeyError):
            return None
        if fetched_at.tzinfo is None:
            return fetched_at.replace(tzinfo=timezone.utc)
        return fetched_at

    def _archive_existing(self, path: Path, meta_path: Path) -> None:
        if not path.is_file():
            return
        fetched_at = self._fetched_at(meta_path) or self._now()
        stamp = fetched_at.strftime(ARCHIVE_STAMP_FORMAT)
        archive_path = path.parent / ".archive" / f"{path.stem}-{stamp}{path.suffix}"
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        if archive_path.exists():
            raise ArchiveCollisionError(archive_path)
        path.rename(archive_path)


def _safe_name(name: str) -> str:
    """Snapshot names are caller-supplied identifiers, never paths: reject
    anything that could escape the gameweek directory."""
    if not name or name.startswith(("/", "\\")):
        raise UnsafeSnapshotNameError(name)
    pure = Path(name)
    if pure.is_absolute() or pure.drive or pure.anchor:
        raise UnsafeSnapshotNameError(name)
    for part in name.replace("\\", "/").split("/"):
        if part in ("", ".", ".."):
            raise UnsafeSnapshotNameError(name)
    return name


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, path)
