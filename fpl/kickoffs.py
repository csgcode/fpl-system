"""Club kickoff dates over the EP window and the player analyst's dated
availability rule: "Expected back D" / "Suspended until D" rules a player out
of every gameweek whose fixtures all kick off before D.

Dates are UTC calendar dates. Premier League kickoffs end by about 20:00 UTC,
so the UTC date is the London date the FPL news line uses."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from datetime import date
from typing import Final

from fpl.models import Fixture

UNREADABLE: Final = "?"
"""A return phrase is present but its date cannot be read."""
STALE: Final = "stale"
"""The return date is before the gameweek deadline, yet the news still stands."""

_PHRASE = re.compile(r"\b(?:Expected back|Suspended until)\b")
_DATED = re.compile(
    r"\b(?:Expected back|Suspended until) (\d{1,2}) ([A-Z][a-z]{2})[a-z]*\.?"
)
_MONTHS = {name: i for i, name in enumerate(
    ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), start=1)}

ClubKickoffs = Mapping[int, tuple[date, ...]]


def club_kickoffs(
    fixtures: Iterable[Fixture], window: range
) -> dict[int, dict[int, tuple[date, ...]]]:
    """team id → gameweek → kickoff dates in order. A gameweek with no
    fixture for the club is absent; unscheduled fixtures are skipped."""
    found: dict[int, dict[int, list[date]]] = {}
    for f in fixtures:
        if f.event is None or f.event not in window or f.kickoff_time is None:
            continue
        for team in (f.team_h, f.team_a):
            found.setdefault(team, {}).setdefault(f.event, []).append(f.kickoff_time.date())
    return {team: {gw: tuple(sorted(dates)) for gw, dates in sorted(by_gw.items())}
            for team, by_gw in found.items()}


def return_date(news: str, reference: date) -> date | str | None:
    """The D of a dated return phrase, UNREADABLE when the phrase has no
    readable date, None when there is no phrase. The news omits the year: D
    is the matching date nearest `reference` (when the news was added)."""
    if not _PHRASE.search(news):
        return None
    match = _DATED.search(news)
    if match is None or match[2] not in _MONTHS:
        return UNREADABLE
    month, day = _MONTHS[match[2]], int(match[1])
    candidates = []
    for year in (reference.year - 1, reference.year, reference.year + 1):
        try:
            candidates.append(date(year, month, day))
        except ValueError:
            continue
    if not candidates:
        return UNREADABLE
    return min(candidates, key=lambda c: abs(c - reference))


def back_gw(club: ClubKickoffs, window: range, back: date) -> str:
    """The first window gameweek with a club kickoff on or after `back`;
    every earlier window gameweek is ruled out. `N*` marks a double gameweek
    with a fixture before `back`; `>M` rules out the whole window."""
    for gw in window:
        dates = club.get(gw, ())
        if any(d >= back for d in dates):
            return f"{gw}*" if any(d < back for d in dates) else str(gw)
    return f">{window[-1]}"
