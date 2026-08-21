"""CLI entry point. Usage: python -m fpl <command> --gw N [options]

Fetch commands map 1:1 to the data-collector outputs in
agents/data-collector.md; `players` is a filtered read over the cached
bootstrap. Cached snapshots are reused unless older than --max-age hours
(default 24) or --force is given.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from fpl.api import FplApi
from fpl.http import RequestsGateway
from fpl.models import PlayerStatus, Position
from fpl.repository import (
    PLAYERS_SLIM_COLUMNS,
    SORT_KEYS,
    PlayerFilter,
    PlayerRepository,
    PlayerRow,
    slim_record,
    slim_values,
)
from fpl.service import DEFAULT_MAX_AGE_HOURS, FplDataService
from fpl.store import SnapshotMissingError, SnapshotStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fpl", description="Deterministic FPL data fetcher with snapshot cache."
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data/raw"),
        help="snapshot root (default: data/raw)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name: str, help_text: str, cached: bool = True) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--gw", type=int, required=True, help="gameweek number")
        if cached:
            p.add_argument(
                "--max-age",
                type=float,
                default=DEFAULT_MAX_AGE_HOURS,
                help="reuse cache younger than this many hours (inf = any age)",
            )
            p.add_argument("--force", action="store_true", help="refetch even if fresh")
        return p

    add("bootstrap", "fetch bootstrap-static (players, teams, events)")
    add("fixtures", "fetch full fixture list")
    summaries = add("summaries", "fetch element-summary per player")
    group = summaries.add_mutually_exclusive_group(required=True)
    group.add_argument("--ids", type=_id_list, help="comma-separated player ids")
    group.add_argument(
        "--shortlist", action="store_true", help="all shortlisted players"
    )
    entry = add("entry", "fetch our FPL entry (squad, bank, chips)")
    entry.add_argument("--team-id", type=int, required=True)
    add("slim-csv", "write players-slim.csv from cached bootstrap", cached=False)
    add(
        "prior-season",
        "write prior-season.json from cached summaries",
        cached=False,
    )
    flags = add("flags", "force-refresh injury/news flags for given players", cached=False)
    flags.add_argument("--ids", type=_id_list, required=True)
    players = add("players", "filtered view over the cached bootstrap", cached=False)
    players.add_argument(
        "--position", type=_position_set, default=frozenset(),
        help="comma-separated: GKP,DEF,MID,FWD",
    )
    players.add_argument("--min-price", type=float, help="minimum price in £m, inclusive")
    players.add_argument("--max-price", type=float, help="maximum price in £m, inclusive")
    players.add_argument(
        "--team", type=_upper_set, default=frozenset(),
        help="comma-separated team short names, e.g. ARS,LIV",
    )
    players.add_argument(
        "--status", type=_status_set, default=frozenset(),
        help="comma-separated status letters: a,d,i,n,s,u",
    )
    players.add_argument("--min-ownership", type=float, help="minimum selected_by %%")
    players.add_argument("--shortlist", action="store_true", help="shortlisted players only")
    players.add_argument("--sort", choices=sorted(SORT_KEYS), default="price")
    players.add_argument("--limit", type=int, help="return at most this many players")
    players.add_argument("--format", choices=("table", "csv", "json"), default="table")
    return parser


def _id_list(raw: str) -> list[int]:
    try:
        return [int(part) for part in raw.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid id list: {raw!r}") from exc


def _position_set(raw: str) -> frozenset[Position]:
    try:
        return frozenset(
            Position[part.strip().upper()] for part in raw.split(",") if part.strip()
        )
    except KeyError as exc:
        raise argparse.ArgumentTypeError(f"invalid position in: {raw!r}") from exc


def _status_set(raw: str) -> frozenset[PlayerStatus]:
    try:
        return frozenset(
            PlayerStatus(part.strip().lower()) for part in raw.split(",") if part.strip()
        )
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid status in: {raw!r}") from exc


def _upper_set(raw: str) -> frozenset[str]:
    return frozenset(part.strip().upper() for part in raw.split(",") if part.strip())


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = SnapshotStore(args.data_root)
    service = FplDataService(FplApi(RequestsGateway()), store)
    gw = args.gw
    try:
        run_command(service, store, gw, args)
    except SnapshotMissingError as exc:
        print(f"error: {exc} — fetch it first (python -m fpl {exc.name.split('/')[0]} --gw {exc.gw})")
        return 1
    return 0


def run_command(
    service: FplDataService, store: SnapshotStore, gw: int, args: argparse.Namespace
) -> None:
    if args.command == "bootstrap":
        bootstrap = service.bootstrap(gw, args.max_age, args.force)
        print(f"saved {store.path(gw, 'bootstrap')} (fetched {store.fetched_at(gw, 'bootstrap')})")
        print(f"players: {len(bootstrap.elements)}, teams: {len(bootstrap.teams)}")
        print(f"current GW: {bootstrap.current_gw()}, next GW: {bootstrap.next_gw()}, "
              f"next deadline: {bootstrap.next_deadline()}")
    elif args.command == "fixtures":
        fixtures = service.fixtures(gw, args.max_age, args.force)
        print(f"saved {store.path(gw, 'fixtures')} ({len(fixtures)} fixtures)")
    elif args.command == "summaries":
        ids = service.shortlist_ids(gw) if args.shortlist else args.ids
        summaries = service.player_summaries(gw, ids, args.max_age, args.force)
        print(f"saved {len(summaries)} summaries under {store.dir(gw) / 'players'}")
    elif args.command == "entry":
        entry = service.entry(gw, args.team_id, args.max_age, args.force)
        print(f"saved entry {entry.id} ('{entry.name}'), "
              f"bank: {entry.last_deadline_bank}, value: {entry.last_deadline_value}")
    elif args.command == "slim-csv":
        print(f"wrote {service.export_players_csv(gw)}")
    elif args.command == "prior-season":
        path = service.build_prior_season(gw)
        print(f"wrote {path}")
    elif args.command == "flags":
        for p in service.flag_report(gw, args.ids):
            chance = "" if p.chance_of_playing_next_round is None else f"{p.chance_of_playing_next_round}%"
            added = p.news_added.isoformat() if p.news_added else ""
            print(f"{p.id:>4}  {p.web_name:<20} {p.status.value}  {chance:>4}  {added}  {p.news}")
    elif args.command == "players":
        player_filter = PlayerFilter(
            positions=args.position,
            min_price_m=args.min_price,
            max_price_m=args.max_price,
            teams=args.team,
            statuses=args.status,
            min_ownership_pct=args.min_ownership,
            shortlisted_only=args.shortlist,
        )
        rows = PlayerRepository(store).query(gw, player_filter, args.sort, args.limit)
        print_players(rows, args.format)


def print_players(rows: list[PlayerRow], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps([slim_record(row) for row in rows], indent=1))
    elif fmt == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(PLAYERS_SLIM_COLUMNS)
        for row in rows:
            writer.writerow(slim_values(row))
    else:
        print(f"{'id':>4}  {'name':<20} {'team':<4} {'pos':<3} {'price':>5} "
              f"{'st':<2} {'own%':>5} {'form':>5} {'pts':>4} {'pen':>3}")
        for row in rows:
            p = row.player
            pen = p.penalties_order if p.penalties_order is not None else ""
            print(f"{p.id:>4}  {p.web_name:<20.20} {row.team_short_name:<4} "
                  f"{p.element_type.name:<3} {p.price_m:>5.1f} {p.status.value:<2} "
                  f"{p.selected_by_percent:>5.1f} {p.form:>5.1f} {p.total_points:>4} {pen:>3}")
        print(f"({len(rows)} players)")


if __name__ == "__main__":
    sys.exit(main())
