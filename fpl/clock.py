"""The CLI's clock.

Outside replay mode it is the real UTC time. In replay mode (FPL_REPLAY_DIR
set) a clock.json in the replay directory pins it to the recorded gameweek,
so snapshot ages and deadline margins match the recordings rather than the
day the replay runs. The pinned clock starts at the recorded instant and
advances with real elapsed time: a constant instant would give two rotations
of one snapshot the same archive stamp, which the store refuses.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

REPLAY_ENV = "FPL_REPLAY_DIR"
CLOCK_FILE = "clock.json"


def utcnow() -> datetime:
    real = datetime.now(UTC)
    root = os.environ.get(REPLAY_ENV, "")
    if not root:
        return real
    path = Path(root) / CLOCK_FILE
    if not path.is_file():
        return real
    pinned, anchored_at = _read_clock(path)
    return pinned + (real - anchored_at)


def write_clock(directory: Path, now: datetime, *, anchored_at: datetime) -> Path:
    """Pins the replay clock to `now` as of the real instant `anchored_at`."""
    if now.tzinfo is None or anchored_at.tzinfo is None:
        raise ValueError("the replay clock needs timezone-aware instants")
    path = directory / CLOCK_FILE
    path.write_text(
        json.dumps({"now": now.isoformat(), "anchored_at": anchored_at.isoformat()}),
        encoding="utf-8",
    )
    return path


def _read_clock(path: Path) -> tuple[datetime, datetime]:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        pinned = datetime.fromisoformat(record["now"])
        anchored_at = datetime.fromisoformat(record["anchored_at"])
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError(f"unreadable replay {CLOCK_FILE} at {path}: {exc}") from exc
    if pinned.tzinfo is None or anchored_at.tzinfo is None:
        raise ValueError(f"replay {CLOCK_FILE} at {path} holds a naive time")
    return pinned, anchored_at
