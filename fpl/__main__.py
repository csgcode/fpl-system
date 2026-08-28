"""CLI entry point. Usage: python -m fpl <command> --gw N [options]

Fetch commands map 1:1 to the data-collector outputs in
agents/data-collector.md; `players` is a filtered read over the cached
bootstrap. Cached snapshots are reused unless older than --max-age hours
(default 24) or --force is given. Errors go to stderr; exit 1 means the
command failed, exit 2 means it produced an empty or rejected result.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

import requests
from pydantic import ValidationError

from fpl.api import FplApi
from fpl.auth import AuthCredentials, AuthMissingError, load_auth
from fpl.http import RequestsGateway
from fpl.models import POSITION_ALIASES, MyTeam, PlayerStatus, Position
from fpl.repository import (
    PLAYERS_SLIM_COLUMNS,
    SORT_KEYS,
    PlayerFilter,
    PlayerRepository,
    PlayerRow,
    slim_record,
    slim_values,
)
from fpl.service import (
    DEFAULT_MAX_AGE_HOURS,
    FetchEvent,
    FplDataService,
    load_cached_bootstrap,
)
from fpl.state import PlannedPicks, parse_state_picks, picks_from_ids
from fpl.store import ArchiveCollisionError, SnapshotMissingError, SnapshotStore
from fpl.write import (
    AuthenticatedRequestsGateway,
    SessionExpiredError,
    TransferPlan,
    VerifyMismatchError,
    WriteApi,
    WriteGateway,
    WriteService,
)

MIN_GW = 1
MAX_GW = 38
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_EMPTY = 2

WRITE_COMMANDS = ("my-team", "set-lineup", "make-transfers")


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
        p.add_argument(
            "--gw", type=_gameweek, required=True,
            help=f"gameweek number ({MIN_GW}-{MAX_GW})",
        )
        if cached:
            p.add_argument(
                "--max-age",
                type=float,
                default=DEFAULT_MAX_AGE_HOURS,
                help="reuse cache younger than this many hours (inf = any age)",
            )
            p.add_argument("--force", action="store_true", help="refetch even if fresh")
        return p

    bootstrap = add("bootstrap", "fetch bootstrap-static (players, teams, events)")
    bootstrap.add_argument(
        "--allow-gw-mismatch",
        action="store_true",
        help="save even if the payload's next gameweek is not --gw",
    )
    add("fixtures", "fetch full fixture list")
    summaries = add("summaries", "fetch element-summary per player")
    group = summaries.add_mutually_exclusive_group(required=True)
    group.add_argument("--ids", type=_id_list, help="comma-separated player ids")
    group.add_argument(
        "--shortlist", action="store_true", help="all shortlisted players"
    )
    entry = add("entry", "fetch our FPL entry (bank, team value)")
    entry.add_argument("--team-id", type=int, required=True, help="our FPL entry id")
    entry_history = add("entry-history", "fetch our per-gameweek entry history")
    entry_history.add_argument(
        "--team-id", type=int, required=True, help="our FPL entry id"
    )
    picks = add("picks", "fetch our picks for one event")
    picks.add_argument("--team-id", type=int, required=True, help="our FPL entry id")
    picks.add_argument(
        "--event", type=_gameweek, required=True, help="gameweek the picks belong to"
    )
    actuals = add(
        "actuals", "force-refresh summaries and report one round's returns",
        cached=False,
    )
    actuals.add_argument(
        "--round", type=_gameweek, required=True, help="completed gameweek to total"
    )
    actuals.add_argument(
        "--ids", type=_id_list, required=True, help="comma-separated player ids"
    )
    add("slim-csv", "write players-slim.csv from cached bootstrap", cached=False)
    add(
        "prior-season",
        "write prior-season.json from cached summaries",
        cached=False,
    )
    flags = add("flags", "force-refresh injury/news flags for given players", cached=False)
    flags.add_argument(
        "--ids", type=_id_list, required=True, help="comma-separated player ids"
    )
    def add_write(name: str, help_text: str) -> argparse.ArgumentParser:
        p = add(name, help_text, cached=False)
        p.add_argument(
            "--team-id", type=int,
            help="our FPL entry id (default: team_id from data/entry.json)",
        )
        p.add_argument(
            "--auth", type=Path, default=Path("data/auth.json"),
            help="credentials file (git-ignored; see docs/api-write.md)",
        )
        p.add_argument(
            "--executor-root", type=Path, default=Path("data/executor"),
            help="audit-record root for applied writes",
        )
        p.add_argument(
            "--entry-file", type=Path, default=Path("data/entry.json"),
            help="team-id fallback source",
        )
        return p

    def add_apply_gates(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--from-final", type=Path,
            help="final.md whose STATE picks: block is the payload source",
        )
        p.add_argument("--chip", help="chip to play with this request")
        p.add_argument(
            "--apply", action="store_true",
            help="send the POST; without it the command is a dry run",
        )
        p.add_argument(
            "--force-deadline", action="store_true",
            help="override the 30-minute deadline margin (never a passed deadline)",
        )

    add_write("my-team", "authenticated read: squad, sell prices, chips, transfers")
    set_lineup = add_write("set-lineup", "set XI, captain, vice and bench order")
    add_apply_gates(set_lineup)
    set_lineup.add_argument(
        "--picks", type=_id_list, help="all 15 player ids in position order"
    )
    set_lineup.add_argument("--captain", type=int, help="captain's player id")
    set_lineup.add_argument("--vice", type=int, help="vice-captain's player id")
    make_transfers = add_write("make-transfers", "make transfers (--apply is the gate)")
    add_apply_gates(make_transfers)
    make_transfers.add_argument(
        "--out", dest="transfers_out", type=_id_list,
        help="comma-separated player ids to transfer out",
    )
    make_transfers.add_argument(
        "--in", dest="transfers_in", type=_id_list,
        help="comma-separated player ids to transfer in",
    )

    players = add("players", "filtered view over the cached bootstrap", cached=False)
    players.add_argument(
        "--position", type=_position_set, default=frozenset(),
        help="comma-separated: GKP (or GK),DEF,MID,FWD",
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


def _gameweek(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid gameweek: {raw!r}") from exc
    if not MIN_GW <= value <= MAX_GW:
        raise argparse.ArgumentTypeError(
            f"gameweek must be between {MIN_GW} and {MAX_GW}, got {value}"
        )
    return value


def _id_list(raw: str) -> list[int]:
    try:
        return [int(part) for part in raw.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid id list: {raw!r}") from exc


def _position_set(raw: str) -> frozenset[Position]:
    positions = []
    for part in raw.split(","):
        token = part.strip().upper()
        if not token:
            continue
        if token in POSITION_ALIASES:
            positions.append(POSITION_ALIASES[token])
            continue
        try:
            positions.append(Position[token])
        except KeyError as exc:
            raise argparse.ArgumentTypeError(f"invalid position in: {raw!r}") from exc
    return frozenset(positions)


def _status_set(raw: str) -> frozenset[PlayerStatus]:
    try:
        return frozenset(
            PlayerStatus(part.strip().lower()) for part in raw.split(",") if part.strip()
        )
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid status in: {raw!r}") from exc


def _upper_set(raw: str) -> frozenset[str]:
    return frozenset(part.strip().upper() for part in raw.split(",") if part.strip())


def _default_service(store: SnapshotStore) -> FplDataService:
    return FplDataService(FplApi(RequestsGateway()), store)


def _default_write_gateway(credentials: AuthCredentials) -> WriteGateway:
    return AuthenticatedRequestsGateway(credentials)


def main(
    argv: list[str] | None = None,
    service_factory: Callable[[SnapshotStore], FplDataService] | None = None,
    write_gateway_factory: Callable[[AuthCredentials], WriteGateway] | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    store = SnapshotStore(args.data_root)
    try:
        if args.command in WRITE_COMMANDS:
            return run_write_command(
                store, args, write_gateway_factory or _default_write_gateway
            )
        service = (service_factory or _default_service)(store)
        return run_command(service, store, args.gw, args)
    except AuthMissingError as exc:
        _stderr(f"error: {exc}")
        return EXIT_ERROR
    except (SessionExpiredError, VerifyMismatchError) as exc:
        _stderr(f"error: {exc}")
        return EXIT_ERROR
    except SnapshotMissingError as exc:
        _stderr(f"error: {exc}")
        hint = exc.fetch_hint
        if hint:
            _stderr(f"hint: python -m fpl --data-root {args.data_root} {hint}")
        else:
            _stderr(f"hint: data root is {args.data_root}")
        return EXIT_ERROR
    except requests.RequestException as exc:
        _stderr(f"error: network request failed: {exc}")
        return EXIT_ERROR
    except ArchiveCollisionError as exc:
        _stderr(f"error: {exc}")
        return EXIT_ERROR
    except ValidationError as exc:
        _stderr(
            f"error: payload failed validation ({exc.error_count()} problems); "
            f"first: {exc.errors()[0].get('loc')} {exc.errors()[0].get('msg')}"
        )
        return EXIT_ERROR
    except ValueError as exc:
        _stderr(f"error: {exc}")
        return EXIT_ERROR
    except OSError as exc:
        # requests.RequestException is an OSError subclass: it is handled above.
        _stderr(f"error: filesystem failure: {exc}")
        return EXIT_ERROR


def run_command(
    service: FplDataService, store: SnapshotStore, gw: int, args: argparse.Namespace
) -> int:
    if args.command == "bootstrap":
        bootstrap = service.bootstrap(
            gw,
            max_age_hours=args.max_age,
            force=args.force,
            require_next_gw=not args.allow_gw_mismatch,
        )
        print(f"{store.path(gw, 'bootstrap')} {_cache_note(service)}")
        print(f"fetched at {store.fetched_at(gw, 'bootstrap')}")
        print(f"players: {len(bootstrap.elements)}, teams: {len(bootstrap.teams)}, "
              f"chips: {len(bootstrap.chips)}")
        print(f"current GW: {bootstrap.current_gw()}, next GW: {bootstrap.next_gw()}, "
              f"next deadline: {bootstrap.next_deadline()}")
    elif args.command == "fixtures":
        fixtures = service.fixtures(gw, max_age_hours=args.max_age, force=args.force)
        print(f"{store.path(gw, 'fixtures')} ({len(fixtures)} fixtures) "
              f"{_cache_note(service)}")
    elif args.command == "summaries":
        ids = service.shortlist_ids(gw) if args.shortlist else args.ids
        summaries = service.player_summaries(
            gw, player_ids=ids, max_age_hours=args.max_age, force=args.force
        )
        print(f"{len(summaries)} summaries under {store.dir(gw) / 'players'} "
              f"{_cache_note(service)}")
    elif args.command == "entry":
        entry = service.entry(
            gw, team_id=args.team_id, max_age_hours=args.max_age, force=args.force
        )
        print(f"entry {entry.id} ('{entry.name}'), bank: {entry.last_deadline_bank}, "
              f"value: {entry.last_deadline_value} {_cache_note(service)}")
    elif args.command == "entry-history":
        history = service.entry_history(
            gw, team_id=args.team_id, max_age_hours=args.max_age, force=args.force
        )
        print(f"entry {args.team_id} history ({len(history.current)} events) "
              f"{_cache_note(service)}")
        print(f"{'event':>5}  {'pts':>4}  {'total':>6}  {'ovr rank':>10}  "
              f"{'bank':>5}  {'value':>6}  {'tr':>3}  {'bench':>5}")
        for row in history.current:
            print(f"{row.event:>5}  {_blank(row.points):>4}  "
                  f"{_blank(row.total_points):>6}  {_blank(row.overall_rank):>10}  "
                  f"{_blank(row.bank):>5}  {_blank(row.value):>6}  "
                  f"{_blank(row.event_transfers):>3}  "
                  f"{_blank(row.points_on_bench):>5}")
    elif args.command == "picks":
        event_picks = service.picks(
            gw,
            team_id=args.team_id,
            event=args.event,
            max_age_hours=args.max_age,
            force=args.force,
        )
        print(f"entry {args.team_id} event {args.event}, "
              f"active chip: {event_picks.active_chip or 'none'} "
              f"{_cache_note(service)}")
        print(f"{'pos':>3}  {'element':>7}  {'mult':>4}  role")
        for pick in event_picks.picks:
            role = "C" if pick.is_captain else ("VC" if pick.is_vice_captain else "")
            print(f"{_blank(pick.position):>3}  {pick.element:>7}  "
                  f"{_blank(pick.multiplier):>4}  {role}")
    elif args.command == "actuals":
        lines = service.actuals(gw, player_ids=args.ids, match_round=args.round)
        print(f"round {args.round} actuals ({len(lines)} players)")
        print(f"{'id':>4}  {'min':>4}  {'pts':>4}  {'gls':>4}  {'ast':>4}  "
              f"{'bon':>4}  {'bps':>5}  note")
        for line in lines:
            print(f"{line.player_id:>4}  {line.minutes:>4}  {line.total_points:>4}  "
                  f"{line.goals_scored:>4}  {line.assists:>4}  {line.bonus:>4}  "
                  f"{line.bps:>5}  {'' if line.matched else 'no match'}")
    elif args.command == "slim-csv":
        print(f"wrote {service.export_players_csv(gw)}")
    elif args.command == "prior-season":
        result = service.build_prior_season(gw)
        print(f"wrote {result.path}")
        print(f"players: {result.players}, no_pl_history: {result.no_pl_history}, "
              f"missing_summaries: {result.missing_summaries}")
        if result.players == 0:
            _stderr(
                "WARNING: prior-season has no players — fetch element summaries "
                f"first (python -m fpl summaries --gw {gw} --shortlist)"
            )
            return EXIT_EMPTY
    elif args.command == "flags":
        players = service.flag_report(gw, player_ids=args.ids)
        print(f"refreshed at {store.fetched_at(gw, 'bootstrap')}")
        print(f"{'id':>4}  {'name':<20} {'st':<2} {'chance':>6}  "
              f"{'news_added':<25} news")
        for p in players:
            chance = "" if p.chance_of_playing_next_round is None else f"{p.chance_of_playing_next_round}%"
            added = p.news_added.isoformat() if p.news_added else ""
            print(f"{p.id:>4}  {p.web_name:<20.20} {p.status.value:<2} "
                  f"{chance:>6}  {added:<25} {p.news}")
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
    return EXIT_OK


def run_write_command(
    store: SnapshotStore,
    args: argparse.Namespace,
    gateway_factory: Callable[[AuthCredentials], WriteGateway],
) -> int:
    gw = args.gw
    team_id = _resolve_team_id(args.team_id, args.entry_file)
    credentials = load_auth(args.auth)
    service = WriteService(
        WriteApi(gateway_factory(credentials)),
        store,
        SnapshotStore(args.executor_root),
    )
    if args.command == "my-team":
        _print_my_team(service.my_team(team_id), team_id, _player_names(store, gw))
        return EXIT_OK
    service.ensure_deadline_open(gw, override_margin=args.force_deadline)
    if args.command == "set-lineup":
        picks = _resolve_lineup_picks(args)
        service.validate_formation(gw, picks)
        plan = service.plan_lineup(team_id=team_id, picks=picks, chip=args.chip)
        if plan.already_applied:
            print("already applied — current lineup matches; no request sent")
            return EXIT_OK
        if not args.apply:
            _print_dry_run(plan.url, plan.payload, ())
            return EXIT_OK
        print(f"applied and verified — audit: {service.apply_lineup(gw, plan)}")
        return EXIT_OK
    plan = _transfer_plan(service, gw, team_id, args)
    if plan.already_applied:
        print("already applied — requested transfers are in place; no request sent")
        return EXIT_OK
    if not args.apply:
        _print_dry_run(plan.url, plan.payload, plan.notes)
        return EXIT_OK
    print(f"applied and verified — audit: {service.apply_transfers(gw, plan)}")
    return EXIT_OK


def _resolve_team_id(explicit: int | None, entry_file: Path) -> int:
    if explicit is not None:
        return explicit
    if not entry_file.is_file():
        raise ValueError(f"no --team-id given and {entry_file} does not exist")
    entry = json.loads(entry_file.read_text(encoding="utf-8"))
    if not isinstance(entry, dict):
        raise ValueError(f"{entry_file} must be a JSON object with a team_id field")
    team_id = entry.get("team_id")
    if team_id is None:
        raise ValueError(
            f"team_id is null in {entry_file} — register the team and fill it "
            "in, or pass --team-id"
        )
    return int(team_id)


def _read_final(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"no final.md at {path}")
    return path.read_text(encoding="utf-8")


def _resolve_lineup_picks(args: argparse.Namespace) -> PlannedPicks:
    if args.from_final is not None:
        return parse_state_picks(_read_final(args.from_final), expected_gw=args.gw)
    if args.picks and args.captain is not None and args.vice is not None:
        return picks_from_ids(args.picks, captain=args.captain, vice=args.vice)
    raise ValueError(
        "provide --from-final, or --picks (15 ids in position order) with "
        "--captain and --vice"
    )


def _transfer_plan(
    service: WriteService, gw: int, team_id: int, args: argparse.Namespace
) -> TransferPlan:
    if args.from_final is not None:
        picks = parse_state_picks(_read_final(args.from_final), expected_gw=gw)
        return service.plan_transfers(
            gw=gw, team_id=team_id, chip=args.chip, target_ids=picks.ids()
        )
    if args.transfers_out and args.transfers_in:
        return service.plan_transfers(
            gw=gw, team_id=team_id, chip=args.chip,
            out_ids=args.transfers_out, in_ids=args.transfers_in,
        )
    raise ValueError("provide --from-final, or --out and --in id lists")


def _print_dry_run(url: str, payload: dict, notes: Sequence[str]) -> None:
    print("DRY RUN — no request sent; re-run with --apply to execute")
    print(f"POST {url}")
    print(json.dumps(payload, indent=1))
    for note in notes:
        print(note)


def _print_my_team(team: MyTeam, team_id: int, names: dict[int, str]) -> None:
    transfers = team.transfers
    print(
        f"entry {team_id} — bank {_tenths(transfers.bank)}, "
        f"value {_tenths(transfers.value)}, "
        f"free transfers {_blank(transfers.limit)}, made {_blank(transfers.made)}"
    )
    chips = ", ".join(
        f"{chip.name} ({chip.status_for_entry or 'unknown'})" for chip in team.chips
    )
    print(f"chips: {chips or 'none'}")
    print(f"{'pos':>3}  {'element':>7}  {'name':<20} {'sell':>5}  {'buy':>5}  role")
    for pick in sorted(team.picks, key=lambda p: p.position):
        role = "C" if pick.is_captain else ("VC" if pick.is_vice_captain else "")
        print(
            f"{pick.position:>3}  {pick.element:>7}  "
            f"{names.get(pick.element, ''):<20.20} "
            f"{_tenths(pick.selling_price):>5}  "
            f"{_tenths(pick.purchase_price):>5}  {role}"
        )


def _player_names(store: SnapshotStore, gw: int) -> dict[int, str]:
    try:
        bootstrap = load_cached_bootstrap(store, gw)
    except SnapshotMissingError:
        return {}
    return {p.id: p.web_name for p in bootstrap.elements}


def _tenths(value: int | None) -> str:
    return "" if value is None else f"{value / 10:.1f}"


def _blank(value: object) -> str:
    return "" if value is None else str(value)


def _stderr(message: str) -> None:
    print(message, file=sys.stderr)


def _cache_note(service: FplDataService) -> str:
    return _format_fetch_log(service.take_fetch_log())


def _format_fetch_log(events: Sequence[FetchEvent]) -> str:
    if not events:
        return ""
    if len(events) == 1:
        event = events[0]
        if event.fetched:
            return "(fetched)"
        if event.age_hours is None:
            return "(cached, age unknown)"
        return f"(cached, age {event.age_hours:.1f}h)"
    fetched = sum(1 for event in events if event.fetched)
    return f"({fetched} fetched, {len(events) - fetched} cached)"


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
