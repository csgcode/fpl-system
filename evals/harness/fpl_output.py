"""Parsers over fpl CLI stdout and over the notes an agent copies from it."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class CacheNote:
    """`kind` is fetched, cached, mixed (a count pair) or local."""

    kind: str
    fetched: int | None = None
    cached: int | None = None


@dataclass(frozen=True)
class BootstrapFacts:
    fetched_at: datetime | None
    deadline: datetime | None
    players: int | None
    current_status: tuple[int, bool, bool] | None


_LINE_SUBCOMMANDS = (
    (re.compile(r"bootstrap\.json \("), "bootstrap"),
    (re.compile(r"fixtures\.json \("), "fixtures"),
    (re.compile(r"summaries under "), "summaries"),
    (re.compile(r"^entry \d+ event \d+,"), "picks"),
    (re.compile(r"^entry \d+ history"), "entry-history"),
    (re.compile(r"^entry \d+ \("), "entry"),
)
_COUNTS = re.compile(r"(\d+) fetched, (\d+) cached")
_CACHED = re.compile(r"\bcached\b")
_FETCHED = re.compile(r"\bfetched\b")
_LOCAL = re.compile(r"\blocal\b")
_FETCHED_AT = re.compile(r"^fetched at (.+)$", re.M)
_DEADLINE = re.compile(r"next deadline: (.+)$", re.M)
_PLAYERS = re.compile(r"^players: (\d+), teams", re.M)
_STATUS = re.compile(
    r"^current GW (\d+) status: finished=(true|false) data_checked=(true|false)", re.M)
_PRIOR = re.compile(r"players: (\d+), no_pl_history: (\d+), missing_summaries: (\d+)")


def note_from_text(text: str) -> CacheNote | None:
    counts = _COUNTS.search(text)
    if counts:
        return CacheNote("mixed", fetched=int(counts.group(1)), cached=int(counts.group(2)))
    if _CACHED.search(text):
        return CacheNote("cached")
    if _FETCHED.search(text):
        return CacheNote("fetched")
    if _LOCAL.search(text):
        return CacheNote("local")
    return None


def cache_notes(text: str) -> dict[str, CacheNote]:
    """Subcommand → the cache note its stdout line printed (last one wins)."""
    notes: dict[str, CacheNote] = {}
    for line in text.splitlines():
        for pattern, subcommand in _LINE_SUBCOMMANDS:
            if pattern.search(line):
                tail = line[line.rfind("("):] if "(" in line else ""
                note = note_from_text(tail)
                if note is not None:
                    notes[subcommand] = note
                break
    return notes


def bootstrap_facts(text: str) -> BootstrapFacts:
    fetched = _FETCHED_AT.search(text)
    deadline = _DEADLINE.search(text)
    players = _PLAYERS.search(text)
    status = _STATUS.search(text)
    return BootstrapFacts(
        fetched_at=parse_datetime(fetched.group(1)) if fetched else None,
        deadline=parse_datetime(deadline.group(1)) if deadline else None,
        players=int(players.group(1)) if players else None,
        current_status=(
            (int(status.group(1)), status.group(2) == "true", status.group(3) == "true")
            if status else None
        ),
    )


def prior_season_counts(text: str) -> tuple[int, int, int] | None:
    match = _PRIOR.search(text)
    return tuple(int(g) for g in match.groups()) if match else None  # type: ignore[return-value]


def parse_datetime(value: str) -> datetime | None:
    """Tolerant of the spellings agents copy (` UTC`, `Z`, a dropped fraction);
    truncated to the second, the precision every copy keeps."""
    cleaned = value.strip().removesuffix("UTC").strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC).replace(microsecond=0)
