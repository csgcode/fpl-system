"""Team-xG cross-check: what share of his club's xG a player has taken.

A reading aid for the analyst, never an EP input. `observed_shares` sums a
player's xG and xA over the matches he started and divides each by his
club's xG in those same matches. xA is divided by club xG too, so both
shares sit on the scale the EP formula uses for attacking rates.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from fpl.models import MatchRecord

RECENT_STARTS = 4

ClubXg = Mapping[tuple[int, str], float]


@dataclass(frozen=True)
class Shares:
    """Shares are None when the counted matches give the club no xG."""

    xg_season: float | None
    xa_season: float | None
    xg_recent: float | None
    xa_recent: float | None
    starts: int


def observed_shares(history: Iterable[MatchRecord], club_xg: ClubXg) -> Shares:
    """Shares over every started match whose (fixture, "H"/"A" side) is in
    `club_xg`, and over the last RECENT_STARTS of them by round. Rows with no
    `was_home` cannot be placed on a side and are left out."""
    counted = sorted(
        (row for row in history if (row.starts or 0) >= 1 and _key(row) in club_xg),
        key=lambda row: (row.round or 0, row.fixture),
    )
    xg_season, xa_season = _shares(counted, club_xg)
    xg_recent, xa_recent = _shares(counted[-RECENT_STARTS:], club_xg)
    return Shares(xg_season, xa_season, xg_recent, xa_recent, starts=len(counted))


def _key(row: MatchRecord) -> tuple[int, str] | None:
    if row.was_home is None:
        return None
    return row.fixture, "H" if row.was_home else "A"


def _shares(rows: Sequence[MatchRecord], club_xg: ClubXg) -> tuple[float | None, float | None]:
    club = sum(club_xg[_key(row)] for row in rows)
    if club <= 0:
        return None, None
    xg = sum(row.expected_goals or 0.0 for row in rows)
    xa = sum(row.expected_assists or 0.0 for row in rows)
    return xg / club, xa / club
