"""`fpl history`: read-only views over the season store for the agents.

Three shapes, each filtered to the players of the gw N bootstrap:
- per match (default) or per round (`--per round`, a double gameweek summed):
  the completed rounds before gw N, or the last K of them (`--last K`);
- past seasons (`--past`, optionally one `--season`);
- one row per club (`--group-by team`) summing either of the above. A match
  row counts for the club he played for in it; a past season for his club
  in the gw N bootstrap. Matches whose side the store could not resolve
  group under "?".

`--fields` and `--format` follow `fpl players`: fields pick and order the
csv/json columns, and the table prints every field.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

from fpl.models import PastSeason, Position
from fpl.season_store import DEFAULT_STORE_PATH, PlayerMatch, PlayerState, open_ro

STATS: dict[str, str] = {
    "minutes": "minutes",
    "starts": "starts",
    "points": "total_points",
    "goals": "goals_scored",
    "assists": "assists",
    "xg": "expected_goals",
    "xa": "expected_assists",
    "xgc": "expected_goals_conceded",
    "cs": "clean_sheets",
    "gc": "goals_conceded",
    "saves": "saves",
    "bonus": "bonus",
    "bps": "bps",
    "dc": "defensive_contribution",
    "yellow": "yellow_cards",
}
MATCH_FIELDS = ("id", "name", "team", "position", "round", "fixture", "opp", "venue",
                "kickoff", *STATS)
PAST_FIELDS = ("id", "name", "team", "position", "season", *STATS)
GROUP_FIELDS = ("team", "players", "rows", *STATS)
JOINED = ("team", "fixture", "opp", "venue", "kickoff")

UNRESOLVED_TEAM = "?"

Record = dict[str, Any]


def register(
    add: Callable[..., argparse.ArgumentParser],
    *,
    positions: Callable[[str], frozenset[Position]],
    ids: Callable[[str], list[int]],
    count: Callable[[str], int],
) -> None:
    """Adds `fpl history` through the CLI's own `add` and argument types."""
    p = add("history", "per-match, per-round, past-season or per-club views over the "
            "season store (local only; read-only)", cached=False)
    p.add_argument("--position", type=positions, default=frozenset(),
                   help="comma-separated: GKP (or GK),DEF,MID,FWD")
    p.add_argument("--ids", type=ids, help="comma-separated player ids")
    p.add_argument("--last", type=count, metavar="K",
                   help="only the last K completed rounds before gw N")
    p.add_argument("--per", choices=("match", "round"),
                   help="one row per match (default) or per round, a double gameweek summed")
    p.add_argument("--past", action="store_true", help="past seasons instead of this one")
    p.add_argument("--season", help="with --past, one season, e.g. 2025/26")
    p.add_argument("--min-minutes", type=int, default=0,
                   help="drop rows (matches, rounds or seasons) with fewer minutes, "
                        "before any grouping")
    p.add_argument("--group-by", choices=("team",), help="one row per club, summed")
    p.add_argument("--format", choices=("table", "csv", "json"), default="table")
    p.add_argument("--fields", help="comma-separated columns to print, in order "
                   "(csv/json); default: all")
    p.add_argument("--store", type=Path, default=DEFAULT_STORE_PATH,
                   help=f"store file (default: {DEFAULT_STORE_PATH})")


def run(raw_root: Path, args: argparse.Namespace) -> int:
    _check_options(args)
    valid = GROUP_FIELDS if args.group_by else PAST_FIELDS if args.past else MATCH_FIELDS
    fields = _fields(args.fields, args.format, valid)
    with open_ro(args.store, raw_root) as reader:
        bootstrap = reader.player_state(args.gw)
        unknown = sorted(set(args.ids or ()) - bootstrap.keys())
        if unknown:
            raise ValueError(
                f"ids not in the gw{args.gw} bootstrap: {', '.join(map(str, unknown))}")
        players = {
            element: state for element, state in bootstrap.items()
            if (not args.position or state.position in args.position)
            and (args.ids is None or element in args.ids)
        }
        clubs = reader.clubs()
        if args.past:
            records = _past_records(reader.past(players), players, clubs, args.season)
        else:
            first = 1 if args.last is None else max(1, args.gw - args.last)
            matches = [m for m in reader.matches(args.gw, first) if m.element in players]
            records = [_match_record(m, players[m.element], clubs) for m in matches]
            if args.per == "round":
                records = _per_round(records)
    records = [r for r in records if (r["minutes"] or 0) >= args.min_minutes]
    if args.group_by:
        records = _per_team(records)
    _print(records, fields, args.format)
    return 0


def _check_options(args: argparse.Namespace) -> None:
    if args.season is not None and not args.past:
        raise ValueError("--season needs --past")
    if args.past and (args.per is not None or args.last is not None):
        raise ValueError("--per and --last apply to this season's rounds, not --past")


def _fields(raw: str | None, fmt: str, valid: Sequence[str]) -> tuple[str, ...]:
    if raw is None:
        return tuple(valid)
    if fmt not in ("csv", "json"):
        raise ValueError("--fields needs --format csv or json")
    fields = tuple(part.strip() for part in raw.split(",") if part.strip())
    for name in fields:
        if name not in valid:
            raise ValueError(f"unknown field {name!r}; valid: {','.join(valid)}")
    return fields


def _stats(source: PlayerMatch | PastSeason) -> Record:
    return {name: getattr(source, attr) for name, attr in STATS.items()}


def _match_record(match: PlayerMatch, player: PlayerState, clubs: dict[int, str]) -> Record:
    venue = "" if match.was_home is None else "H" if match.was_home else "A"
    return {
        "id": match.element,
        "name": player.web_name,
        "team": clubs.get(match.team, "") if match.team is not None else "",
        "position": player.position.name,
        "round": match.round,
        "fixture": str(match.fixture),
        "opp": clubs.get(match.opponent_team, "") if match.opponent_team is not None else "",
        "venue": venue,
        "kickoff": match.kickoff_time.isoformat() if match.kickoff_time else "",
        **_stats(match),
    }


def _past_records(
    past: dict[int, tuple[PastSeason, ...]], players: dict[int, PlayerState],
    clubs: dict[int, str], season: str | None,
) -> list[Record]:
    return [
        {
            "id": element,
            "name": players[element].web_name,
            "team": clubs.get(players[element].team, ""),
            "position": players[element].position.name,
            "season": row.season_name,
            **_stats(row),
        }
        for element in sorted(past)
        for row in past[element]
        if season is None or row.season_name == season
    ]


def _per_round(records: list[Record]) -> list[Record]:
    grouped: dict[tuple[int, int], list[Record]] = {}
    for record in records:
        grouped.setdefault((record["id"], record["round"]), []).append(record)
    merged = []
    for rows in grouped.values():
        record = dict(rows[0])
        for name in JOINED:
            record[name] = "+".join(_unique(row[name] for row in rows))
        record.update(_summed(rows))
        merged.append(record)
    return merged


def _per_team(records: list[Record]) -> list[Record]:
    grouped: dict[str, list[Record]] = {}
    for record in records:
        grouped.setdefault(record["team"] or UNRESOLVED_TEAM, []).append(record)
    return [
        {"team": team, "players": len({row["id"] for row in rows}), "rows": len(rows),
         **_summed(rows)}
        for team, rows in sorted(grouped.items())
    ]


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _summed(rows: Sequence[Record]) -> Record:
    totals: Record = {}
    for name in STATS:
        values = [row[name] for row in rows if row[name] is not None]
        if not values:
            totals[name] = None
        elif any(isinstance(v, float) for v in values):
            totals[name] = round(sum(values), 2)
        else:
            totals[name] = sum(values)
    return totals


def _print(records: list[Record], fields: tuple[str, ...], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps([{name: r[name] for name in fields} for r in records], indent=1))
        return
    if fmt == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(fields)
        for record in records:
            writer.writerow(_cell(record[name]) for name in fields)
        return
    table = [list(fields)] + [[_cell(r[name]) for name in fields] for r in records]
    widths = [max(len(row[i]) for row in table) for i in range(len(fields))]
    for row in table:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip())
    print(f"({len(records)} row{'' if len(records) == 1 else 's'})")


def _cell(value: Any) -> str:
    return "" if value is None else str(value)
