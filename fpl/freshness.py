"""The freshness-gate diff: which players' availability flags moved between a
baseline bootstrap and a refreshed one.

Only status, chance_of_playing_next_round and news are compared. news_added is
deliberately not: it has been seen to stay put while chance and news changed,
so a diff keyed on it misses real flag changes.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable
from dataclasses import dataclass
from typing import Any

from fpl.models import PLAYING_POSITIONS, Player, PlayerStatus, Position

FLAG_FIELDS = ("status", "chance_of_playing_next_round", "news")


@dataclass(frozen=True)
class FieldChange:
    field: str
    before: Any
    after: Any


@dataclass(frozen=True)
class FlagChange:
    id: int
    web_name: str
    position: Position
    changes: tuple[FieldChange, ...]

    def to_document(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "web_name": self.web_name,
            "position": self.position.name,
            "changes": [
                {"field": c.field, "before": c.before, "after": c.after}
                for c in self.changes
            ],
        }


def flag_delta(
    old_players: Iterable[Player],
    new_players: Iterable[Player],
    ids: Collection[int] | None = None,
) -> list[FlagChange]:
    """Changes for every playing-position player in new_players (or only
    those in ids), sorted by id. A player missing from the baseline is a
    change: nothing was known about them when the analysis ran."""
    old_by_id = {p.id: p for p in old_players}
    result = []
    for new in sorted(new_players, key=lambda p: p.id):
        if new.element_type not in PLAYING_POSITIONS:
            continue
        if ids is not None and new.id not in ids:
            continue
        old = old_by_id.get(new.id)
        if old is None:
            changes: tuple[FieldChange, ...] = (FieldChange("in_baseline", False, True),)
        else:
            changes = tuple(
                FieldChange(name, _plain(getattr(old, name)), _plain(getattr(new, name)))
                for name in FLAG_FIELDS
                if getattr(old, name) != getattr(new, name)
            )
        if changes:
            result.append(FlagChange(new.id, new.web_name, new.element_type, changes))
    return result


def _plain(value: Any) -> Any:
    return value.value if isinstance(value, PlayerStatus) else value
