"""Team-xG cross-check: what share of his club's xG a player has taken.

A reading aid for the analyst, never an EP input. `observed_shares` sums a
player's xG and xA over the matches he started and divides each by his
club's xG in those same matches. xA is divided by club xG too, so both
shares sit on the scale the EP formula uses for attacking rates.

`implied_share` turns a player's EP rate into the share of club xG it
assumes, and `share_flags` flags it when it sits far from the observed
season share. `annotate` applies both to the rows `fpl ep` writes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from fpl.ep import FULL_MATCH_MINUTES
from fpl.fixture_ratings import MatchXg
from fpl.models import MatchRecord

RECENT_STARTS = 4
SHARE_MIN_STARTS = 3
SHARE_ABS_TOL = 0.05
SHARE_REL_TOL = 0.4

ClubXg = Mapping[tuple[int, str], float]


def club_xg_map(matches: Iterable[MatchXg]) -> dict[tuple[int, str], float]:
    """Each rated match's xG keyed by (fixture, "H") and (fixture, "A")."""
    return {key: xg for m in matches
            for key, xg in (((m.fixture, "H"), m.xg_home), ((m.fixture, "A"), m.xg_away))}


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


@dataclass(frozen=True)
class ShareFlag:
    """One stat ("xG" or "xA") whose implied share is far from the season share."""

    stat: str
    implied: float
    season: float
    starts: int

    @property
    def label(self) -> str:
        return f"{self.stat} EP{'>' if self.implied > self.season else '<'}club"

    @property
    def detail(self) -> str:
        return f"{self.label} (implied {self.implied:.2f}, season {self.season:.2f}, {self.starts} starts)"


def implied_share(*, rate90: float, mps: float, attack_mult: float, base_mean: float, att_club: float) -> float:
    """The share of club xG that a per-90 rate implies, on the EP formula's
    fixture scale: rate90 x min(mps, 90)/90 x attack_mult / (base_mean x ATT_club)."""
    return rate90 * min(mps, FULL_MATCH_MINUTES) / FULL_MATCH_MINUTES * attack_mult / (base_mean * att_club)


def share_flags(*, implied_xg: float | None, implied_xa: float | None, shares: Shares) -> tuple[ShareFlag, ...]:
    """xG then xA, each flagged when the player has SHARE_MIN_STARTS counted
    starts and |implied - season| > max(SHARE_ABS_TOL, SHARE_REL_TOL x season).
    A stat with no implied or no season share is never flagged."""
    if shares.starts < SHARE_MIN_STARTS:
        return ()
    pairs = (("xG", implied_xg, shares.xg_season), ("xA", implied_xa, shares.xa_season))
    return tuple(
        ShareFlag(stat, implied, season, shares.starts)
        for stat, implied, season in pairs
        if implied is not None and season is not None and _far_apart(implied, season)
    )


def labels(flags: Sequence[ShareFlag]) -> str | None:
    """Short labels joined by "; ", or None when nothing is flagged."""
    return "; ".join(flag.label for flag in flags) or None


def details(flags: Sequence[ShareFlag]) -> str | None:
    """Labels with implied share, season share and starts, joined by "; "."""
    return "; ".join(flag.detail for flag in flags) or None


def _far_apart(implied: float, season: float) -> bool:
    return abs(implied - season) > max(SHARE_ABS_TOL, SHARE_REL_TOL * season)


def annotate(
    documents: Sequence[dict[str, Any]],
    *,
    histories: Mapping[int, Sequence[MatchRecord]],
    club_xg: ClubXg,
    base_mean: float,
    att_by_club: Mapping[str, float],
) -> dict[int, tuple[ShareFlag, ...]]:
    """Set `share_flag` on each players-{pos}.json row: the flag details, or
    None. The implied shares use the row's own rates and the club rating and
    base mean the EP was scored with; xG is taken before the finishing
    multiplier, since the observed share is of xG, not goals. Returns the flags of the flagged rows
    by id. An empty `club_xg` flags nothing."""
    flagged: dict[int, tuple[ShareFlag, ...]] = {}
    for document in documents:
        rates = document["rates"]
        shares = observed_shares(histories.get(document["id"], ()), club_xg)

        def implied(rate90: float) -> float:
            return implied_share(rate90=rate90, mps=rates["minutes_per_start"],
                                 attack_mult=rates["attack_mult"], base_mean=base_mean,
                                 att_club=att_by_club[document["team"]])

        xg90 = rates["xg90"] / rates.get("finishing_mult", 1.0)
        flags = share_flags(implied_xg=implied(xg90), implied_xa=implied(rates["xa90"]),
                            shares=shares)
        document["share_flag"] = details(flags)
        if flags:
            flagged[document["id"]] = flags
    return flagged
