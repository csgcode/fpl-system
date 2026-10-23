"""Club attack/defence ratings and the fixture rows `fpl ep` consumes.

Each played match yields an implied rating per side: the side's xG over what
a 1.00 club would expect against that opponent's GW1 prior. The season's
implied values are blended with the club's prior and renormalised to a league
mean of 1.00. Rows for the six-gameweek window then follow from the rounded
ratings, so fixtures.json is a pure function of the cached snapshots plus
data/analysis/club-priors.json. Formula and constants: docs/ep-model.md §6.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from fpl.ep import CLUB_RATING_RANGE, HORIZON, SCHEMA_VERSION, FixturesDocument, load_fixtures
from fpl.models import Bootstrap, ElementSummary, EventLive, Fixture
from fpl.season_store import History, PlayerMatch
from fpl.service import load_cached_bootstrap, load_cached_summaries
from fpl.state import MAX_GW
from fpl.store import SnapshotMissingError, SnapshotStore

BASE_HOME = 1.54
BASE_AWAY = 1.33
BASE = {"H": BASE_HOME, "A": BASE_AWAY}
CLIP = (0.55, 1.80)
K_ATT = 5.7
K_DEFW = 4.0
K_ATT_PROMOTED = 4.0
K_DEFW_PROMOTED = 3.0
CS_BAND_ROW_THRESHOLD = 0.30
PRIORS_FILENAME = "club-priors.json"
JSON_FILENAME = "fixtures.json"
TABLES_FILENAME = "fixtures-tables.md"

Venue = Literal["H", "A"]
Kind = Literal["att", "defw"]


class RatingRefusal(ValueError):
    """A refusal the CLI prints as `error:` plus a `hint:` line."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint


# --- priors ------------------------------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ClubPrior(_Strict):
    att: float = Field(ge=CLUB_RATING_RANGE[0], le=CLUB_RATING_RANGE[1])
    defw: float = Field(ge=CLUB_RATING_RANGE[0], le=CLUB_RATING_RANGE[1])
    promoted: bool
    source: str

    @field_validator("source")
    @classmethod
    def _source_named(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must say where the prior came from")
        return value


class PriorsDocument(_Strict):
    schema_version: Literal[1]
    season: str
    clubs: dict[str, ClubPrior]

    @property
    def promoted(self) -> frozenset[str]:
        return frozenset(c for c, prior in self.clubs.items() if prior.promoted)


def parse_priors(raw: Any, *, label: str = PRIORS_FILENAME) -> PriorsDocument:
    try:
        return PriorsDocument.model_validate(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        where = ".".join(str(part) for part in first.get("loc") or ())
        raise ValueError(f"{label} invalid: {where}: {first.get('msg')}") from None


def load_priors(path: Path) -> PriorsDocument:
    if not path.is_file():
        raise RatingRefusal(
            f"no club priors at {path}",
            "at GW1 the fixture analyst writes data/analysis/club-priors.json "
            "(agents/fixture-analyst.md § Priors)",
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from None
    return parse_priors(raw, label=str(path))


def check_priors_clubs(priors: PriorsDocument, clubs: set[str]) -> None:
    missing = sorted(clubs - set(priors.clubs))
    unknown = sorted(set(priors.clubs) - clubs)
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing for {', '.join(missing)}")
        if unknown:
            parts.append(f"not in the bootstrap: {', '.join(unknown)}")
        raise ValueError(f"club priors {'; '.join(parts)}")


# --- arithmetic --------------------------------------------------------------


def _other(venue: Venue) -> Venue:
    return "A" if venue == "H" else "H"


def implied_attack(xg: float, venue: Venue, *, opp_defw: float) -> float:
    return xg / (BASE[venue] * opp_defw)


def implied_defence(xga: float, venue: Venue, *, opp_att: float) -> float:
    """The goals conceded are the opponent's, scored at the opponent's venue."""
    return xga / (BASE[_other(venue)] * opp_att)


def clip(value: float) -> tuple[float, bool]:
    clipped = min(CLIP[1], max(CLIP[0], value))
    return clipped, clipped != value


def k_for(kind: Kind, *, promoted: bool) -> float:
    if kind == "att":
        return K_ATT_PROMOTED if promoted else K_ATT
    return K_DEFW_PROMOTED if promoted else K_DEFW


def blend(prior: float, implied: Sequence[float], k: float) -> float:
    return (k * prior + sum(implied)) / (k + len(implied))


def renormalise(values: Mapping[str, float]) -> dict[str, float]:
    mean = sum(values.values()) / len(values)
    return {club: round(value / mean, 2) for club, value in values.items()}


def decile(values: Sequence[float], x: float) -> int:
    below = sum(v < x for v in values)
    return min(10, 1 + math.floor(10 * below / len(values)))


# --- the run -----------------------------------------------------------------


@dataclass(frozen=True)
class RatingInputs:
    gw: int
    bootstrap: Bootstrap
    fixtures: Sequence[Fixture]
    summaries: Mapping[int, ElementSummary]
    live: Mapping[int, EventLive]
    priors: PriorsDocument
    previous: FixturesDocument | None = None
    matches: Sequence[PlayerMatch] | None = None


@dataclass(frozen=True)
class MatchXg:
    fixture: int
    round: int
    home: str
    away: str
    xg_home: float
    xg_away: float


@dataclass(frozen=True)
class ImpliedMatch:
    round: int
    opp: str
    venue: Venue
    xg: float
    xga: float
    att: float
    att_clipped: bool
    defw: float
    defw_clipped: bool


@dataclass(frozen=True)
class ClubRating:
    prior_att: float
    prior_defw: float
    promoted: bool
    matches: tuple[ImpliedMatch, ...]
    raw_att: float
    raw_defw: float
    att: float
    defw: float

    @property
    def n(self) -> int:
        return len(self.matches)

    @property
    def clips(self) -> int:
        return sum(m.att_clipped + m.defw_clipped for m in self.matches)


@dataclass(frozen=True)
class Row:
    club: str
    gw: int
    opp: str
    venue: Venue
    fdr: int
    lambda_att: float
    lambda_def: float
    p_cs: float
    band: bool

    def cell(self, value: float) -> str:
        return f"{self.opp}({self.venue}) {value:.2f}{' ±' if self.band else ''}"


@dataclass(frozen=True)
class LeagueXg:
    home: float
    away: float
    matches: int

    @property
    def total(self) -> float:
        return self.home + self.away

    def line(self) -> str:
        base = BASE_HOME + BASE_AWAY
        return (f"league xG per match: home {self.home:.2f}, away {self.away:.2f}, "
                f"total {self.total:.2f} vs base {base:.2f} "
                f"({100 * (self.total / base - 1):+.1f}%)")


@dataclass(frozen=True)
class RatingRun:
    gw: int
    rounds: int
    summaries: int
    matches: list[MatchXg]
    recovered: int
    recovered_xg: float
    unresolved: int
    clubs: dict[str, ClubRating]
    rows: list[Row]
    window: list[int]
    blanks: dict[int, list[str]]
    doubles: dict[int, list[str]]
    unscheduled: int
    previous: dict[str, tuple[float, float]] | None
    warnings: list[str] = field(default_factory=list)

    @property
    def clips(self) -> int:
        return sum(club.clips for club in self.clubs.values())

    @property
    def clip_total(self) -> int:
        return 4 * len(self.matches)

    @property
    def clips_by_round(self) -> dict[int, int]:
        counts = {r: 0 for r in range(1, self.rounds + 1)}
        for club in self.clubs.values():
            for m in club.matches:
                counts[m.round] += m.att_clipped + m.defw_clipped
        return counts

    @property
    def league(self) -> LeagueXg | None:
        if not self.matches:
            return None
        count = len(self.matches)
        return LeagueXg(home=sum(m.xg_home for m in self.matches) / count,
                        away=sum(m.xg_away for m in self.matches) / count, matches=count)


def rate(inputs: RatingInputs) -> RatingRun:
    gw, priors = inputs.gw, inputs.priors
    names = {team.id: team.short_name for team in inputs.bootstrap.teams}
    check_priors_clubs(priors, set(names.values()))
    played = sorted(
        (f for f in inputs.fixtures if f.event is not None and 1 <= f.event < gw and f.finished),
        key=lambda f: (f.event, f.id),
    )
    tally = _side_xg(played, inputs)
    matches = [
        MatchXg(f.id, f.event or 0, names[f.team_h], names[f.team_a],
                round(tally.xg[(f.id, "H")], 2), round(tally.xg[(f.id, "A")], 2))
        for f in played
    ]
    clubs = _ratings(matches, priors)
    rows, window, blanks, doubles = _rows(gw, inputs.fixtures, names, clubs, priors.promoted)
    warnings = []
    if tally.unresolved:
        warnings.append(
            f"{tally.unresolved} event-live player-round(s) ({tally.unresolved_xg:.2f} xG) "
            "matched neither side of their fixture — their xG is left out"
        )
    previous = ({c: (r.att, r.defw) for c, r in inputs.previous.ratings.items()}
                if inputs.previous is not None else None)
    return RatingRun(
        gw=gw, rounds=gw - 1, summaries=len(inputs.summaries), matches=matches,
        recovered=tally.recovered, recovered_xg=tally.recovered_xg,
        unresolved=tally.unresolved, clubs=clubs, rows=rows, window=window,
        blanks=blanks, doubles=doubles,
        unscheduled=sum(1 for f in inputs.fixtures if f.event is None),
        previous=previous, warnings=warnings,
    )


@dataclass
class _Tally:
    xg: dict[tuple[int, str], float]
    recovered: int = 0
    recovered_xg: float = 0.0
    unresolved: int = 0
    unresolved_xg: float = 0.0


def _side_xg(played: Sequence[Fixture], inputs: RatingInputs) -> _Tally:
    """Summary rows are attributed by their own fixture and venue, so a
    transferred player's old matches stay with his old club. Players without
    a summary row are recovered from event-live, on their current club's side."""
    if inputs.matches is not None:
        return _stored_side_xg(played, inputs)
    by_id = {f.id: f for f in played}
    tally = _Tally(xg={(f.id, side): 0.0 for f in played for side in ("H", "A")})
    seen: set[tuple[int, int]] = set()
    for element, summary in inputs.summaries.items():
        for row in summary.history:
            if row.fixture not in by_id:
                continue
            if row.was_home is None:
                raise ValueError(
                    f"player {element}: summary row for played fixture {row.fixture} "
                    "has no was_home — refetch the summaries"
                )
            tally.xg[(row.fixture, "H" if row.was_home else "A")] += row.expected_goals or 0.0
            if row.minutes > 0:
                seen.add((element, row.fixture))
    team_of = {p.id: p.team for p in inputs.bootstrap.elements}
    for event in sorted(inputs.live):
        for element in inputs.live[event].elements:
            shares = [(ex.fixture, ex.stat("minutes")) for ex in element.explain]
            shares = [(fid, mins) for fid, mins in shares if mins > 0 and fid in by_id]
            total = sum(mins for _, mins in shares)
            for fid, mins in shares:
                if (element.id, fid) in seen:
                    continue
                xg = (element.stats.expected_goals or 0.0) * mins / total
                fixture, team = by_id[fid], team_of.get(element.id)
                side = "H" if team == fixture.team_h else "A" if team == fixture.team_a else None
                if side is None:
                    tally.unresolved += 1
                    tally.unresolved_xg += xg
                    continue
                tally.xg[(fid, side)] += xg
                tally.recovered += 1
                tally.recovered_xg += xg
    return tally


def _stored_side_xg(played: Sequence[Fixture], inputs: RatingInputs) -> _Tally:
    """The season store's rows, each on the side of the club the player played
    for in that match. A row of a player without a summary counts as
    recovered, as on the summaries path. Rows are summed in the summaries
    path's order (summarised players first, then the rest by round), so the
    rounded match xG agree wherever both paths attribute a row alike."""
    by_id = {f.id: f for f in played}
    tally = _Tally(xg={(f.id, side): 0.0 for f in played for side in ("H", "A")})
    order = {element: i for i, element in enumerate(inputs.summaries)}
    rows = sorted(
        (m for m in inputs.matches or () if m.fixture in by_id),
        key=lambda m: ((0, order[m.element], 0, 0) if m.element in order
                       else (1, m.round or 0, m.element, m.fixture)),
    )
    for m in rows:
        xg = m.expected_goals or 0.0
        recovered = m.element not in order
        if m.team is None:
            if m.minutes > 0:
                tally.unresolved += 1
                tally.unresolved_xg += xg
            continue
        fixture = by_id[m.fixture]
        tally.xg[(m.fixture, "H" if m.team == fixture.team_h else "A")] += xg
        if recovered and m.minutes > 0:
            tally.recovered += 1
            tally.recovered_xg += xg
    return tally


def _ratings(matches: Sequence[MatchXg], priors: PriorsDocument) -> dict[str, ClubRating]:
    implied: dict[str, list[ImpliedMatch]] = {club: [] for club in priors.clubs}
    for m in matches:
        for club, opp, venue, xg, xga in ((m.home, m.away, "H", m.xg_home, m.xg_away),
                                          (m.away, m.home, "A", m.xg_away, m.xg_home)):
            opp_prior = priors.clubs[opp]
            att, att_clipped = clip(implied_attack(xg, venue, opp_defw=opp_prior.defw))
            defw, defw_clipped = clip(implied_defence(xga, venue, opp_att=opp_prior.att))
            implied[club].append(ImpliedMatch(m.round, opp, venue, xg, xga,
                                              att, att_clipped, defw, defw_clipped))
    raw = {
        club: (
            blend(prior.att, [m.att for m in implied[club]], k_for("att", promoted=prior.promoted)),
            blend(prior.defw, [m.defw for m in implied[club]],
                  k_for("defw", promoted=prior.promoted)),
        )
        for club, prior in sorted(priors.clubs.items())
    }
    att = renormalise({club: value[0] for club, value in raw.items()})
    defw = renormalise({club: value[1] for club, value in raw.items()})
    return {
        club: ClubRating(prior.att, prior.defw, prior.promoted, tuple(implied[club]),
                         raw[club][0], raw[club][1], att[club], defw[club])
        for club, prior in sorted(priors.clubs.items())
    }


def _rows(
    gw: int, fixtures: Iterable[Fixture], names: Mapping[int, str],
    clubs: Mapping[str, ClubRating], promoted: frozenset[str],
) -> tuple[list[Row], list[int], dict[int, list[str]], dict[int, list[str]]]:
    window = [g for g in range(gw, gw + HORIZON) if g <= MAX_GW]
    rows: list[Row] = []
    scheduled = sorted((f for f in fixtures if f.event in window), key=lambda f: (f.event, f.id))
    for f in scheduled:
        home, away = names[f.team_h], names[f.team_a]
        lambda_home = round(BASE_HOME * clubs[home].att * clubs[away].defw, 2)
        lambda_away = round(BASE_AWAY * clubs[away].att * clubs[home].defw, 2)
        band = home in promoted or away in promoted
        event = f.event or 0
        rows.append(Row(home, event, away, "H", f.team_h_difficulty, lambda_home, lambda_away,
                        round(math.exp(-lambda_away), 2), band))
        rows.append(Row(away, event, home, "A", f.team_a_difficulty, lambda_away, lambda_home,
                        round(math.exp(-lambda_home), 2), band))
    counts: dict[tuple[str, int], int] = {}
    for row in rows:
        counts[(row.club, row.gw)] = counts.get((row.club, row.gw), 0) + 1
    blanks = {g: [c for c in sorted(clubs) if (c, g) not in counts] for g in window}
    doubles = {g: [c for c in sorted(clubs) if counts.get((c, g), 0) > 1] for g in window}
    return (rows, window, {g: v for g, v in blanks.items() if v},
            {g: v for g, v in doubles.items() if v})


# --- outputs -----------------------------------------------------------------


def fixtures_document(run: RatingRun) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "gw": run.gw,
        "base_lambda": {"home": BASE_HOME, "away": BASE_AWAY},
        "ratings": {club: {"att": r.att, "defw": r.defw} for club, r in sorted(run.clubs.items())},
        "fixtures": [
            {"club": r.club, "gw": r.gw, "opp": r.opp, "venue": r.venue, "fdr": r.fdr,
             "lambda_att": r.lambda_att, "lambda_def": r.lambda_def, "p_cs": r.p_cs,
             "band": r.band}
            for r in run.rows
        ],
    }


def render_json(run: RatingRun) -> str:
    return json.dumps(fixtures_document(run), indent=1, ensure_ascii=False) + "\n"


def summary_lines(run: RatingRun) -> list[str]:
    window = f"gw{run.window[0]}–{run.window[-1]}" if run.window else "none"
    latest = run.clips_by_round.get(run.rounds)
    by_round = f" (round {run.rounds}: {latest} of {4 * _matches_in(run, run.rounds)})" \
        if run.rounds and latest is not None else ""
    league = run.league
    return [
        f"gw{run.gw} ratings: {run.rounds} rounds, {len(run.matches)} matches, "
        f"{run.summaries} summaries, {run.recovered} player-rounds "
        f"({run.recovered_xg:.2f} xG) recovered from event-live",
        f"clipped: {run.clips} of {run.clip_total} implied ratings{by_round}",
        league.line() if league else "league xG per match: none (no played matches)",
        f"window {window}: {len(run.rows)} rows, blanks: {_by_gw(run.blanks)}, "
        f"doubles: {_by_gw(run.doubles)}, unscheduled fixtures: {run.unscheduled}",
    ]


def _matches_in(run: RatingRun, round_: int) -> int:
    return sum(1 for m in run.matches if m.round == round_)


def _by_gw(groups: Mapping[int, list[str]]) -> str:
    if not groups:
        return "none"
    return "; ".join(f"gw{g}: {', '.join(clubs)}" for g, clubs in sorted(groups.items()))


def render_tables(run: RatingRun) -> str:
    by_club: dict[str, list[Row]] = {club: [] for club in run.clubs}
    for row in run.rows:
        by_club[row.club].append(row)
    att_sum = {c: sum(r.lambda_att for r in rows) for c, rows in by_club.items()}
    cs_sum = {c: sum(r.p_cs for r in rows) for c, rows in by_club.items()}
    att_order = sorted(run.clubs, key=lambda c: (-att_sum[c], c))
    cs_order = sorted(run.clubs, key=lambda c: (-cs_sum[c], c))
    out = [
        f"# GW{run.gw} fixture tables",
        "",
        "Written by `uv run python -m fpl fixtures-rate`; regenerated on every run — "
        "never edit by hand. Formula: docs/ep-model.md §6.",
        "",
        *_ratings_table(run),
        *_implied_table(run),
        "## League xG vs base",
        "",
        run.league.line() if run.league else "No played matches yet.",
        "",
        *_ticker(run, "Attack ticker", "ATT rank", att_order, att_sum, by_club, "lambda_att"),
        *_ticker(run, "Defence ticker", "CS rank", cs_order, cs_sum, by_club, "p_cs"),
        *_swings(run, by_club),
        *_fdr_vs_model(run, by_club, att_order, cs_order, att_sum),
        *_band_rows(run),
        "## Blanks, doubles, unscheduled",
        "",
        f"- blanks: {_by_gw(run.blanks)}",
        f"- doubles: {_by_gw(run.doubles)}",
        f"- unscheduled fixtures: {run.unscheduled}",
        "",
        *_details(run),
    ]
    return "\n".join(out).rstrip("\n") + "\n"


def _delta(now: float, previous: float | None) -> str:
    return "—" if previous is None else f"{now - previous:+.2f}"


def _shared_rank(values: Mapping[str, float], club: str, *, higher_is_better: bool) -> int:
    """1 + the clubs strictly better, so level clubs share a rank."""
    mine = values[club]
    return 1 + sum((v > mine) if higher_is_better else (v < mine) for v in values.values())


def _ratings_table(run: RatingRun) -> list[str]:
    prev = run.previous or {}
    att = {c: r.att for c, r in run.clubs.items()}
    defw = {c: r.defw for c, r in run.clubs.items()}
    lines = [
        "## Ratings",
        "",
        "Rating rank 1 = strongest attack (highest ATT) or meanest defence (lowest DEFW); "
        "level clubs share a rank.",
        "",
        f"| Club | promoted | n | ATT prior | ATT | ATT rating rank | Δ gw{run.gw - 1} | "
        "DEFW prior | DEFW | DEFW rating rank | Δ | clips |",
        "|---|:-:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for club in sorted(run.clubs, key=lambda c: (-run.clubs[c].att, c)):
        r = run.clubs[club]
        before = prev.get(club)
        lines.append(
            f"| {club} | {'yes' if r.promoted else ''} | {r.n} | {r.prior_att:.2f} | "
            f"{r.att:.2f} | {_shared_rank(att, club, higher_is_better=True)} | "
            f"{_delta(r.att, before[0] if before else None)} | "
            f"{r.prior_defw:.2f} | {r.defw:.2f} | "
            f"{_shared_rank(defw, club, higher_is_better=False)} | "
            f"{_delta(r.defw, before[1] if before else None)} | {r.clips} |"
        )
    return [*lines, ""]


def _implied_table(run: RatingRun) -> list[str]:
    lines = ["## Implied ratings by round", ""]
    if not run.rounds:
        return [*lines, "No played rounds: the ratings are the priors, renormalised.", ""]
    rounds = range(1, run.rounds + 1)
    span = f"r1–r{run.rounds}"
    lines += [
        "`*` = clipped to [0.55, 1.80]; a double gameweek joins its matches with `+`; "
        "`-` = no match that round.",
        "",
        f"| Club | Opp {span} | xG {span} | xGA {span} | impATT {span} | impDEFW {span} |",
        "|---|---|---|---|---|---|",
    ]

    def per_round(matches: Sequence[ImpliedMatch], fmt) -> str:
        cells = []
        for r in rounds:
            in_round = [m for m in matches if m.round == r]
            cells.append("+".join(fmt(m) for m in in_round) if in_round else "-")
        return " / ".join(cells)

    for club in sorted(run.clubs, key=lambda c: (-run.clubs[c].att, c)):
        ms = run.clubs[club].matches
        lines.append(
            f"| {club} | {per_round(ms, lambda m: f'{m.opp}({m.venue})')} | "
            f"{per_round(ms, lambda m: f'{m.xg:.2f}')} | "
            f"{per_round(ms, lambda m: f'{m.xga:.2f}')} | "
            f"{per_round(ms, lambda m: f'{m.att:.2f}' + ('*' if m.att_clipped else ''))} | "
            f"{per_round(ms, lambda m: f'{m.defw:.2f}' + ('*' if m.defw_clipped else ''))} |"
        )
    return [*lines, ""]


def _mean_fdr(rows: Sequence[Row]) -> float | None:
    return sum(r.fdr for r in rows) / len(rows) if rows else None


def _ticker(run: RatingRun, title: str, rank_label: str, order: Sequence[str],
            sums: Mapping[str, float], by_club: Mapping[str, list[Row]], key: str) -> list[str]:
    lines = [
        f"## {title}",
        "",
        f"| {rank_label} | Club | Σ | mean FDR | " + " | ".join(f"GW{g}" for g in run.window) + " |",
        "|---:|---|---:|---:|" + "---|" * len(run.window),
    ]
    for rank, club in enumerate(order, 1):
        cells = []
        for g in run.window:
            rows = [r for r in by_club[club] if r.gw == g]
            cells.append(" + ".join(r.cell(getattr(r, key)) for r in rows) if rows else "-")
        fdr = _mean_fdr(by_club[club])
        lines.append(f"| {rank} | {club} | {sums[club]:.2f} | "
                     f"{'-' if fdr is None else f'{fdr:.2f}'} | " + " | ".join(cells) + " |")
    return [*lines, ""]


def _swings(run: RatingRun, by_club: Mapping[str, list[Row]]) -> list[str]:
    first, second = run.window[:3], run.window[3:]
    span = (f"GW{second[0]}–{second[-1]} minus GW{first[0]}–{first[-1]}"
            if first and second else "no second half in the window")
    swings = []
    for club, rows in by_club.items():
        def total(gws: Sequence[int], key: str) -> float:
            return sum(getattr(r, key) for r in rows if r.gw in gws)
        swings.append((club, round(total(second, "lambda_att") - total(first, "lambda_att"), 2),
                       round(total(second, "p_cs") - total(first, "p_cs"), 2)))
    swings.sort(key=lambda s: (-(abs(s[1]) + abs(s[2])), s[0]))
    lines = ["## Swings", "", f"Δ = {span}.", "", "| Club | Δ Σλ_att | Δ ΣP(CS) |", "|---|---:|---:|"]
    lines += [f"| {c} | {a:+.2f} | {d:+.2f} |" for c, a, d in swings]
    return [*lines, ""]


def _fdr_vs_model(run: RatingRun, by_club: Mapping[str, list[Row]], att_order: Sequence[str],
                  cs_order: Sequence[str], att_sum: Mapping[str, float]) -> list[str]:
    fdr = {c: _mean_fdr(rows) for c, rows in by_club.items()}
    fdr_order = sorted(run.clubs, key=lambda c: (fdr[c] if fdr[c] is not None else math.inf,
                                                 -att_sum[c], c))
    fdr_rank = {c: i for i, c in enumerate(fdr_order, 1)}
    att_rank = {c: i for i, c in enumerate(att_order, 1)}
    cs_rank = {c: i for i, c in enumerate(cs_order, 1)}
    lines = [
        "## FDR vs model",
        "",
        "Rank 1 = easiest run. FDR ties are broken by Σλ_att.",
        "",
        "| Club | mean FDR | FDR rank | ATT rank | CS rank | FDR−ATT | FDR−CS |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for club in fdr_order:
        mean = fdr[club]
        lines.append(
            f"| {club} | {'-' if mean is None else f'{mean:.2f}'} | {fdr_rank[club]} | "
            f"{att_rank[club]} | {cs_rank[club]} | {fdr_rank[club] - att_rank[club]:+d} | "
            f"{fdr_rank[club] - cs_rank[club]:+d} |"
        )
    return [*lines, ""]


def _band_rows(run: RatingRun) -> list[str]:
    listed = sorted((r for r in run.rows if r.band and r.p_cs >= CS_BAND_ROW_THRESHOLD),
                    key=lambda r: (-r.p_cs, r.gw, r.club))
    lines = [
        f"## Promoted band — rows with P(CS) ≥ {CS_BAND_ROW_THRESHOLD:.2f}",
        "",
        "| GW | Club | Fixture | P(CS) |",
        "|---:|---|---|---:|",
    ]
    lines += [f"| {r.gw} | {r.club} | {r.opp} ({r.venue}) | {r.p_cs:.2f} |" for r in listed]
    return [*lines, "", f"banded rows: {sum(r.band for r in run.rows)}", ""]


def _details(run: RatingRun) -> list[str]:
    lambdas = [r.lambda_att for r in run.rows]
    clean_sheets = [r.p_cs for r in run.rows]
    lines: list[str] = []
    for g in run.window:
        lines += [
            f"## Detail GW{g}",
            "",
            "| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |",
            "|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|",
        ]
        for r in sorted((r for r in run.rows if r.gw == g), key=lambda r: (-r.lambda_att, r.club)):
            lines.append(
                f"| {r.club} | {r.opp} | {r.venue} | {r.fdr} | {r.lambda_att:.2f} | "
                f"{decile(lambdas, r.lambda_att)} | {r.lambda_def:.2f} | {r.p_cs:.2f} | "
                f"{decile(clean_sheets, r.p_cs)} | {'±' if r.band else ''} |"
            )
        lines.append("")
    return lines


# --- loading and writing -----------------------------------------------------


def load_inputs(store: SnapshotStore, gw: int, *, priors_path: Path,
                analysis_root: Path, history: History | None = None,
                pinned: Iterable[int] = ()) -> RatingInputs:
    """From the store, the summaries are the shortlist plus `pinned`; they
    only order the stored rows and give the summaries count."""
    priors = load_priors(priors_path)
    bootstrap = load_cached_bootstrap(store, gw)
    try:
        raw_fixtures = store.load(gw, "fixtures")
    except SnapshotMissingError as exc:
        raise exc.with_hint(f"fixtures --gw {gw}") from None
    if not isinstance(raw_fixtures, list):
        raise ValueError(f"gw{gw} fixtures.json is not a list")
    fixtures = tuple(Fixture.model_validate(f) for f in raw_fixtures)
    ids = [p.id for p in bootstrap.elements]
    previous_path = analysis_root / f"gw{gw - 1}" / JSON_FILENAME
    previous = load_fixtures(previous_path) if gw > 1 and previous_path.is_file() else None
    if history is not None and history.source == "store":
        with history.open() as reader:
            summaries = reader.summaries(gw, ids, coverage="shortlist", pinned=pinned)
            matches = reader.matches(gw)
        return RatingInputs(gw=gw, bootstrap=bootstrap, fixtures=fixtures,
                            summaries=summaries, live={}, priors=priors, previous=previous,
                            matches=matches)
    summaries = load_cached_summaries(store, gw, ids)
    live = {}
    for r in range(1, gw):
        name = f"event-live-e{r}"
        if not store.exists(r + 1, name):
            raise RatingRefusal(
                f"no snapshot '{name}' for gw{r + 1} — round {r} cannot be rated",
                f"the retro's 'calibrate --gw {r + 1} --round {r}' writes it — run step 0 first",
            )
        live[r] = EventLive.model_validate(store.load(r + 1, name))
    return RatingInputs(gw=gw, bootstrap=bootstrap, fixtures=fixtures, summaries=summaries,
                        live=live, priors=priors, previous=previous)


def write_outputs(run: RatingRun, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path, tables_path = out_dir / JSON_FILENAME, out_dir / TABLES_FILENAME
    json_path.write_text(render_json(run), encoding="utf-8")
    tables_path.write_text(render_tables(run), encoding="utf-8")
    return json_path, tables_path
