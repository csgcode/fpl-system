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
from datetime import UTC, datetime
from pathlib import Path

import requests
from pydantic import ValidationError

from fpl.api import FplApi
from fpl.auth import (
    DEFAULT_AUTH_PATH,
    AuthCredentials,
    AuthMissingError,
    has_auth_bearing_header,
    load_auth,
    redacted_summary,
    save_auth,
)
from fpl.calibrate import (
    Aggregate,
    CalibrationReport,
    PlayerLine,
    build_report,
    load_predictions,
    load_report,
)
from fpl.capture import is_git_ignored, parse_curl
from fpl.ep import (
    EpResult,
    build_predictions,
    inspect_fixtures,
    load_fixtures,
    load_inputs,
    write_predictions,
)
from fpl.http import RequestsGateway, RequestsTokenGateway, TokenEndpointError
from fpl.models import POSITION_ALIASES, MyTeam, PlayerStatus, Position
from fpl.plan import (
    LINEUP_TARGET,
    TRANSFERS_TARGET,
    ExecutionPlan,
    build_plan,
    parse_plan,
    route_chip,
)
from fpl.refresh import (
    RefreshPlan,
    TokenGateway,
    TokenRefreshError,
    derive_plan,
    expiry_of,
)
from fpl.refresh import refresh as refresh_token
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
    load_cached_summaries,
)
from fpl.state import (
    MAX_GW,
    MIN_GW,
    DecisionState,
    PlannedPicks,
    parse_state,
    parse_state_picks,
    picks_from_ids,
)
from fpl.store import ArchiveCollisionError, SnapshotMissingError, SnapshotStore
from fpl.usage import build_report as build_usage_report
from fpl.usage import (
    default_transcripts_root,
    fmt_ts,
    inspect_session,
    latest_ledger_end,
    list_sessions,
    load_session,
    parse_ts,
    write_report,
)
from fpl.write import (
    AuthenticatedRequestsGateway,
    RefreshingGateway,
    SessionExpiredError,
    TransferPlan,
    VerifyMismatchError,
    WriteApi,
    WriteGateway,
    WriteService,
)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_EMPTY = 2

WRITE_COMMANDS = ("auth-check", "my-team", "set-lineup", "make-transfers")
DECISIONS_ROOT = Path("data/decisions")
ANALYSIS_ROOT = Path("data/analysis")
FINAL_FILENAME = "final.md"
PLAN_FILENAME = "plan.json"
COST_ROOT = Path("data/cost")


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
            "--auth", type=Path, default=DEFAULT_AUTH_PATH,
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
        payload_source = p.add_mutually_exclusive_group()
        payload_source.add_argument(
            "--from-plan", type=Path,
            help=f"{PLAN_FILENAME} from `fpl plan` — the preferred payload source",
        )
        payload_source.add_argument(
            "--from-final", type=Path,
            help="final.md whose STATE picks: block is the payload source",
        )
        p.add_argument(
            "--chip",
            help="chip to play with this request (must agree with --from-plan)",
        )
        p.add_argument(
            "--apply", action="store_true",
            help="send the POST; without it the command is a dry run",
        )
        p.add_argument(
            "--force-deadline", action="store_true",
            help="override the 30-minute deadline margin (never a passed deadline)",
        )

    add_write("auth-check", "pre-flight: prove the stored session still works")
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

    # Local-only, and the one command with no --gw: it rebuilds credentials,
    # which are not gameweek-scoped.
    auth_import = sub.add_parser(
        "auth-import",
        help="convert a browser 'Copy as cURL' capture into a credentials file",
    )
    auth_import.add_argument(
        "--curl-file", type=Path, required=True,
        help="file holding a browser 'Copy as cURL' capture of a my-team request",
    )
    auth_import.add_argument(
        "--out", type=Path, default=DEFAULT_AUTH_PATH,
        help=f"credentials file to write (default: {DEFAULT_AUTH_PATH})",
    )

    # Local credential maintenance, so also no --gw. Reaches the identity
    # provider rather than the FPL API: the captured bearer lives an hour, the
    # refresh token beside it lives months.
    auth_refresh = sub.add_parser(
        "auth-refresh",
        help="mint a fresh bearer token from the stored refresh token",
    )
    auth_refresh.add_argument(
        "--auth", type=Path, default=DEFAULT_AUTH_PATH,
        help=f"credentials file to read and rewrite (default: {DEFAULT_AUTH_PATH})",
    )
    auth_refresh.add_argument(
        "--dry-run", action="store_true",
        help="print where the refresh would go and stop, sending nothing",
    )
    auth_refresh.add_argument(
        "--token-endpoint",
        help="override the endpoint derived from the bearer token's iss claim",
    )
    auth_refresh.add_argument(
        "--client-id",
        help="override the client id derived from the bearer token's claims",
    )

    # Local-only: reduces Claude Code's own session transcripts to token
    # usage and list-price cost. Never the network, never credentials.
    usage_cmd = add(
        "usage", "token usage and list-price cost of a Claude Code session window",
        cached=False,
    )
    usage_cmd.add_argument(
        "--transcripts-root", type=Path, default=None,
        help="Claude Code transcripts dir (default: ~/.claude/projects/<encoded cwd>)",
    )
    usage_mode = usage_cmd.add_mutually_exclusive_group()
    usage_mode.add_argument(
        "--list", action="store_true",
        help="list sessions newest first; by default only those active after the "
             "latest ledger for an earlier gameweek under --cost-root",
    )
    usage_cmd.add_argument("--since", help="with --list: only sessions active at or after this ISO-8601 UTC time")
    usage_cmd.add_argument("--all", action="store_true", help="with --list: every session, ignoring ledgers")
    usage_cmd.add_argument(
        "--cost-root", type=Path, default=COST_ROOT,
        help=f"ledger root: default --out parent and the --list cutoff source (default: {COST_ROOT})",
    )
    usage_cmd.add_argument("--session", help="session id or unique prefix")
    usage_mode.add_argument(
        "--inspect", action="store_true",
        help="print the session's prompt/spawn timeline and a suggested window for --gw",
    )
    usage_mode.add_argument("--start", help="window start, ISO-8601 UTC, inclusive")
    usage_cmd.add_argument("--end", help="window end, ISO-8601 UTC, exclusive")
    usage_cmd.add_argument("--label", default="", help="free-text label written into the report")
    usage_cmd.add_argument(
        "--out", type=Path, default=None,
        help="output directory (default: <cost-root>/gw{N})",
    )

    # Local-only: the plan is a pure function of final.md plus the cached
    # bootstrap, so it needs neither the network nor credentials.
    plan_cmd = add(
        "plan", "build the deterministic execution-plan JSON", cached=False
    )
    plan_cmd.add_argument(
        "--from-final", type=Path,
        help=f"final.md to plan from (default: {DECISIONS_ROOT}/gw{{N}}/{FINAL_FILENAME})",
    )
    plan_cmd.add_argument(
        "--prev-final", type=Path,
        help="previous gameweek's final.md (default: the gw{N-1} sibling)",
    )
    plan_cmd.add_argument("--format", choices=("table", "json"), default="table")
    plan_cmd.add_argument(
        "--out", type=Path, help="also write the JSON document to this path"
    )

    calibrate = add("calibrate", "join EP predictions vs a completed round's actuals")
    calibrate.add_argument(
        "--round", type=_gameweek, required=True,
        help="completed, data-checked gameweek to calibrate",
    )
    calibrate.add_argument(
        "--analysis-root", type=Path, default=ANALYSIS_ROOT,
        help="root holding gw{M}/players-*.json prediction files",
    )
    calibrate.add_argument(
        "--decisions-root", type=Path, default=DECISIONS_ROOT,
        help=f"root holding gw{{M}}/{FINAL_FILENAME} (squad section source)",
    )
    calibrate.add_argument(
        "--retro-root", type=Path, default=Path("data/retro"),
        help="where gw{M}-calibration.json ledgers live",
    )
    calibrate.add_argument("--format", choices=("table", "json"), default="table")

    # Local-only: expected points are a pure function of the analysts'
    # judgment files plus cached snapshots (docs/ep-model.md).
    ep = add(
        "ep", "compute expected points from inputs-{pos}.json and fixtures.json",
        cached=False,
    )
    ep.add_argument(
        "--position", type=_position_one,
        help="GKP (or GK), DEF, MID or FWD (required unless --check)",
    )
    ep.add_argument(
        "--check", action="store_true",
        help="validate fixtures.json (and inputs, when --position is given) — write nothing",
    )
    ep.add_argument(
        "--analysis-root", type=Path, default=ANALYSIS_ROOT,
        help="root holding gw{N}/inputs-*.json, fixtures.json and the output",
    )
    ep.add_argument("--inputs", type=Path, help="default: <analysis-root>/gw{N}/inputs-{POS}.json")
    ep.add_argument("--fixtures", type=Path, help="default: <analysis-root>/gw{N}/fixtures.json")
    ep.add_argument("--out", type=Path, help="default: <analysis-root>/gw{N}/players-{POS}.json")
    ep.add_argument("--format", choices=("table", "json"), default="table")
    ep.add_argument("--limit", type=int, default=15, help="rows shown in the table")

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
    players.add_argument(
        "--minutes", action="store_true",
        help="append this season's minutes per round from cached element summaries",
    )
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


def _position_one(raw: str) -> Position:
    positions = _position_set(raw)
    if len(positions) != 1:
        raise argparse.ArgumentTypeError(f"exactly one position expected, got {raw!r}")
    return next(iter(positions))


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


def _refreshing_write_gateway(
    auth_path: Path,
) -> Callable[[AuthCredentials], WriteGateway]:
    """The real write path, able to revive itself once.

    A capture's bearer lasts an hour, so a cycle that started with a valid one
    can still meet a 401 by the time it reaches the deadline. Refreshing on
    that rejection — rather than on every request — keeps the working case
    untouched and stops an expired token ending a gameweek.
    """

    def build(credentials: AuthCredentials) -> WriteGateway:
        return RefreshingGateway(
            credentials,
            build_gateway=AuthenticatedRequestsGateway,
            refresh=_exchange_refresh_token,
            on_refreshed=lambda refreshed: save_auth(auth_path, refreshed),
        )

    return build


def _exchange_refresh_token(credentials: AuthCredentials) -> AuthCredentials:
    with RequestsTokenGateway(credentials) as gateway:
        return refresh_token(
            credentials, derive_plan(credentials), gateway
        ).credentials


def main(
    argv: list[str] | None = None,
    service_factory: Callable[[SnapshotStore], FplDataService] | None = None,
    write_gateway_factory: Callable[[AuthCredentials], WriteGateway] | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    store = SnapshotStore(args.data_root)
    try:
        if args.command == "auth-import":
            return run_auth_import(args)
        if args.command == "auth-refresh":
            return run_auth_refresh(args)
        if args.command == "usage":
            return run_usage(args)
        if args.command in WRITE_COMMANDS:
            return run_write_command(
                store,
                args,
                write_gateway_factory or _refreshing_write_gateway(args.auth),
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
              f"{'bon':>4}  {'bps':>5}  {'xG':>5}  {'xA':>5}  {'dc':>3}  note")
        for line in lines:
            print(f"{line.player_id:>4}  {line.minutes:>4}  {line.total_points:>4}  "
                  f"{line.goals_scored:>4}  {line.assists:>4}  {line.bonus:>4}  "
                  f"{line.bps:>5}  {line.expected_goals:>5.2f}  "
                  f"{line.expected_assists:>5.2f}  {line.defensive_contribution:>3.0f}  "
                  f"{'' if line.matched else 'no match'}")
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
    elif args.command == "plan":
        return run_plan(store, gw, args)
    elif args.command == "calibrate":
        return run_calibrate(service, store, gw, args)
    elif args.command == "ep":
        return run_ep(store, gw, args)
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
        minutes = _minutes_by_round(store, gw, rows) if args.minutes else None
        print_players(rows, args.format, minutes)
    return EXIT_OK


def run_calibrate(
    service: FplDataService, store: SnapshotStore, gw: int, args: argparse.Namespace
) -> int:
    bootstrap = load_cached_bootstrap(store, gw)
    event = next((e for e in bootstrap.events if e.id == args.round), None)
    if event is None:
        raise ValueError(f"cached bootstrap has no event {args.round}")
    if not event.data_checked:
        raise ValueError(
            f"round {args.round} is not data-checked yet — bonus points are not "
            f"final. Refetch once FPL marks it checked: "
            f"python -m fpl bootstrap --gw {gw} --force"
        )
    predictions = load_predictions(args.analysis_root / f"gw{args.round}")
    live = service.event_live(
        gw, event=args.round, max_age_hours=args.max_age, force=args.force
    )
    cache_note = _cache_note(service)
    report = build_report(
        predictions,
        live,
        match_round=args.round,
        picks=_calibration_picks(
            args.decisions_root / f"gw{args.round}" / FINAL_FILENAME, args.round
        ),
        prior_reports=_prior_reports(args.retro_root, args.round),
    )
    document = report.model_dump_json(indent=1)
    # The ledger is derived — a pure function of the analysis files, final.md
    # and the live snapshot — so overwriting it is safe, like plan.json.
    ledger_path = args.retro_root / f"gw{args.round}-calibration.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(document + "\n", encoding="utf-8")
    if args.format == "json":
        print(document)
    else:
        print_calibration(report, cache_note)
    print(f"wrote {ledger_path}")
    for warning in report.warnings:
        _stderr(f"WARNING: {warning}")
    return EXIT_OK


def run_ep(store: SnapshotStore, gw: int, args: argparse.Namespace) -> int:
    position: Position | None = args.position
    analysis_dir = args.analysis_root / f"gw{gw}"
    fixtures_path = args.fixtures or analysis_dir / "fixtures.json"
    if args.check:
        return run_ep_check(store, gw, args, fixtures_path)
    if position is None:
        raise ValueError("--position is required unless --check is given")
    inputs_path = args.inputs or analysis_dir / f"inputs-{position.name}.json"
    out_path = args.out or analysis_dir / f"players-{position.name}.json"
    inputs = load_inputs(inputs_path)
    if inputs.position != position:
        raise ValueError(
            f"{inputs_path} is for {inputs.position.name}, not --position {position.name}"
        )
    fixtures = load_fixtures(fixtures_path)
    bootstrap = load_cached_bootstrap(store, gw)
    wanted = [p.id for p in bootstrap.elements if p.element_type == position]
    wanted += [entry.id for entry in inputs.players]
    summaries = load_cached_summaries(store, gw, wanted)
    result = build_predictions(bootstrap, summaries, fixtures, inputs, gw=gw)
    # players-{pos}.json is derived from inputs + fixtures.json + cached
    # snapshots, so overwriting it is safe, like plan.json.
    write_predictions(out_path, result)
    if args.format == "json":
        print(json.dumps(result.to_documents(), indent=1))
    else:
        print_ep(result, args.limit)
    print(f"wrote {out_path}")
    if result.missing_summaries:
        ids = ",".join(str(i) for i in result.missing_summaries)
        _stderr(
            f"WARNING: missing summaries ({len(result.missing_summaries)}) scored on "
            f"league-mean priors — fetch with: uv run python -m fpl summaries --gw {gw} --ids {ids}"
        )
    for warning in result.warnings:
        _stderr(f"WARNING: {warning}")
    return EXIT_OK


def run_ep_check(
    store: SnapshotStore, gw: int, args: argparse.Namespace, fixtures_path: Path
) -> int:
    bootstrap = load_cached_bootstrap(store, gw)
    check = inspect_fixtures(bootstrap, load_fixtures(fixtures_path), gw=gw)
    blanks = ", ".join(check.blanks) if check.blanks else "none"
    print(
        f"{fixtures_path} OK: {check.clubs} clubs rated, {check.rows_in_window} rows in "
        f"gw{check.window[0]}–{check.window[-1]}, blanks: {blanks}"
    )
    position: Position | None = args.position
    if position is None:
        return EXIT_OK
    inputs_path = args.inputs or args.analysis_root / f"gw{gw}" / f"inputs-{position.name}.json"
    inputs = load_inputs(inputs_path)
    if inputs.position != position:
        raise ValueError(
            f"{inputs_path} is for {inputs.position.name}, not --position {position.name}"
        )
    wanted = [p.id for p in bootstrap.elements if p.element_type == position]
    wanted += [entry.id for entry in inputs.players]
    result = build_predictions(
        bootstrap, load_cached_summaries(store, gw, wanted), load_fixtures(fixtures_path),
        inputs, gw=gw,
    )
    print(
        f"{inputs_path} OK: {len(result.rows)} players scored, "
        f"{len(result.missing_summaries)} without cached summary — nothing written"
    )
    for warning in result.warnings:
        _stderr(f"WARNING: {warning}")
    return EXIT_OK


def _minutes_by_round(store: SnapshotStore, gw: int, rows: list[PlayerRow]) -> dict[int, str]:
    summaries = load_cached_summaries(store, gw, [row.player.id for row in rows])
    result = {}
    for row in rows:
        summary = summaries.get(row.player.id)
        if summary is None:
            result[row.player.id] = "no summary"
            continue
        history = sorted(summary.history, key=lambda m: (m.round or 0, m.fixture))
        result[row.player.id] = ",".join(str(m.minutes) for m in history) or "-"
    return result


def print_ep(result: EpResult, limit: int) -> None:
    print(
        f"gw{result.gw} {result.position.name}: {len(result.rows)} scored, "
        f"{result.not_scored} not scored (≤£4.5m or unavailable, absent from inputs), "
        f"{len(result.missing_summaries)} without cached summary"
    )
    source = (
        f"pooled from {result.league_pool} summaries"
        if result.league_source == "pooled"
        else "v1 fallback table (see warnings)"
    )
    print(f"league mean: {source}")
    print(
        f"{'id':>4}  {'name':<18} {'team':<4} {'price':>5} {'p_st':>5} {'ep6':>6} "
        f"{'ep/£m':>5} {'unc':<4} {'app':>5} {'att':>5} {'cs':>5} {'gc':>5} "
        f"{'dc':>5} {'sv':>5} {'bon':>5} {'crd':>5}  fixtures"
    )
    for row in result.rows[:limit]:
        t = row.terms
        print(
            f"{row.id:>4}  {row.name:<18.18} {row.team:<4} {row.price:>5.1f} "
            f"{row.p_start:>5.2f} {row.ep_total6:>6.2f} {row.ep_per_million:>5.2f} "
            f"{row.uncertainty.value:<4} {t.appearance:>5.1f} {t.attack:>5.1f} "
            f"{t.clean_sheet:>5.1f} {t.goals_conceded:>5.1f} {t.defcon:>5.1f} "
            f"{t.saves:>5.1f} {t.bonus:>5.1f} {t.cards:>5.1f}  {' '.join(row.fixtures)}"
        )
    if len(result.rows) > limit:
        print(f"({len(result.rows) - limit} more rows in the file)")


def _calibration_picks(final_path: Path, match_round: int) -> PlannedPicks | None:
    if not final_path.is_file():
        _stderr(f"note: no final.md at {final_path} — squad section skipped")
        return None
    state = parse_state(
        final_path.read_text(encoding="utf-8"), expected_gw=match_round
    )
    if state.picks is None:
        _stderr(f"note: {final_path} has no picks: block — squad section skipped")
    return state.picks


def _prior_reports(retro_root: Path, match_round: int) -> tuple[CalibrationReport, ...]:
    if not retro_root.is_dir():
        return ()
    reports = [
        load_report(path)
        for path in sorted(retro_root.glob("gw*-calibration.json"))
    ]
    return tuple(report for report in reports if report.round != match_round)


def print_calibration(report: CalibrationReport, cache_note: str) -> None:
    print(
        f"round {report.round} calibration — {report.overall.n} players "
        f"matched, {len(report.unmatched_prediction_ids)} unmatched "
        f"{cache_note}".rstrip()
    )

    def agg_line(name: str, agg: Aggregate) -> None:
        print(f"{name:<14} {agg.n:>4} {agg.bias:>7.2f} {agg.mae:>6.2f}")

    print(f"{'group':<14} {'n':>4} {'bias':>7} {'mae':>6}")
    agg_line("overall", report.overall)
    for group in (report.by_position, report.by_uncertainty, report.by_price_band):
        for name, agg in sorted(group.items()):
            agg_line(name, agg)
    minutes = report.minutes
    print(
        f"minutes: brier {minutes.brier:.4f}, expected starts "
        f"{minutes.expected_starts:.1f}, actual {minutes.actual_starts}"
    )
    if report.defcon:
        hits = sum(1 for line in report.defcon if line.hit)
        print(f"defcon: {hits}/{len(report.defcon)} hits (players with 60'+)")
    squad = report.squad
    if squad is not None:
        print(
            f"squad XI (captain doubled): predicted "
            f"{squad.predicted_xi_total:.2f}, actual {squad.actual_xi_total}; "
            f"bench stranded {squad.bench_points_stranded}"
        )
        captain = squad.captain
        print(
            f"captain: {captain.chosen_name} {captain.chosen_actual} pts; "
            f"hindsight best in XI: {captain.hindsight_best_name} "
            f"{captain.hindsight_best_actual} (forgone {captain.forgone})"
        )
        print("squad rows (slot role id name pred act min):")
        for line in squad.players:
            flag = "C" if line.captain else ("VC" if line.vice else "")
            pred = "-" if line.predicted is None else f"{line.predicted:.2f}"
            act = "-" if line.actual is None else str(line.actual)
            mins = "-" if line.minutes is None else str(line.minutes)
            print(
                f"  {line.slot:>3} {line.role:<5} {line.id:>4}  {line.name:<20.20} "
                f"pred {pred:>6}  act {act:>3}  min {mins:>3}  {flag}".rstrip()
            )
    cumulative = report.cumulative
    if cumulative is not None and len(cumulative.rounds) > 1:
        rounds = ",".join(str(r) for r in cumulative.rounds)
        print(
            f"cumulative (rounds {rounds}): n={cumulative.overall.n} "
            f"bias={cumulative.overall.bias:.2f} mae={cumulative.overall.mae:.2f} "
            f"brier={cumulative.minutes_brier:.4f}"
        )
    under = sorted(
        (line for line in report.players if line.error > 3),
        key=lambda line: line.error,
        reverse=True,
    )
    over = sorted(
        (line for line in report.players if line.error < -3),
        key=lambda line: line.error,
    )
    _print_misses("under-predicted (err > +3)", under)
    _print_misses("over-predicted (err < -3)", over)


MISS_ROWS_SHOWN = 8


def _print_misses(label: str, misses: Sequence[PlayerLine]) -> None:
    if not misses:
        print(f"{label}: none")
        return
    shown = misses[:MISS_ROWS_SHOWN]
    print(f"{label}: {len(misses)} players, top {len(shown)}")
    for line in shown:
        print(
            f"  {line.id:>4}  {line.name:<20.20} {line.position:<3} "
            f"pred {line.predicted:>5.2f}  act {line.actual:>3}  "
            f"err {line.error:>+6.2f}  min {line.minutes:>3}  p_start {line.p_start:.2f}"
        )


def run_plan(store: SnapshotStore, gw: int, args: argparse.Namespace) -> int:
    final_path = args.from_final or _final_path(gw)
    state = parse_state(_read_final(final_path), expected_gw=gw)
    previous_path, previous_state = _previous_decision(gw, final_path, args.prev_final)
    plan = build_plan(
        gw=gw,
        state=state,
        bootstrap=load_cached_bootstrap(store, gw),
        source=str(final_path),
        bootstrap_source=str(store.path(gw, "bootstrap")),
        previous_state=previous_state,
        previous_source=str(previous_path) if previous_path is not None else None,
        bootstrap_age_hours=_rounded(store.age_hours(gw, "bootstrap")),
    )
    # ensure_ascii=False: plan.json is read by people, and player names carry
    # accents that would otherwise land as escapes.
    document = json.dumps(plan.to_json_dict(), indent=1, ensure_ascii=False)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(document + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    if args.format == "json":
        print(document)
    else:
        print_plan(plan)
    return EXIT_OK


def _final_path(gw: int) -> Path:
    return DECISIONS_ROOT / f"gw{gw}" / FINAL_FILENAME


def _rounded(age_hours: float | None) -> float | None:
    return None if age_hours is None else round(age_hours, 2)


def _previous_decision(
    gw: int, final_path: Path, explicit: Path | None
) -> tuple[Path | None, DecisionState | None]:
    """The previous gameweek's decision, when there is one: its picks are the
    name-free source for this gameweek's transfers."""
    if gw <= MIN_GW and explicit is None:
        return None, None
    path = explicit or final_path.parent.parent / f"gw{gw - 1}" / final_path.name
    if not path.is_file():
        if explicit is not None:
            raise ValueError(f"no final.md at {path}")
        return None, None
    return path, parse_state(path.read_text(encoding="utf-8"), expected_gw=gw - 1)


def print_plan(plan: ExecutionPlan) -> None:
    entry = "unset" if plan.team_id is None else str(plan.team_id)
    print(
        f"gw{plan.gw} plan (schema {plan.schema_version}) — entry {entry}, "
        f"deadline {plan.deadline.isoformat()}"
    )
    print(
        f"formation {plan.formation}, chip: {plan.chip or 'none'}, "
        f"bank {plan.bank:.1f}, value {plan.team_value:.1f}, "
        f"free transfers {plan.free_transfers_banked}"
    )
    print(f"{'slot':>4}  {'id':>4}  {'name':<20} {'club':<4} {'pos':<3} "
          f"{'price':>5}  role")
    for pick in plan.picks:
        role = "(C)" if pick.is_captain else ("(VC)" if pick.is_vice_captain else "")
        note = " ".join(part for part in (role, "" if pick.starts else "bench") if part)
        print(f"{pick.slot:>4}  {pick.element:>4}  {pick.name:<20.20} "
              f"{pick.club:<4} {pick.position:<3} {pick.now_cost:>5.1f}  "
              f"{note}".rstrip())
    print(f"bench order: {', '.join(str(element) for element in plan.bench)}")
    print(f"transfers ({plan.transfer_source}):")
    for transfer in plan.transfers:
        print(f"  {transfer.out.name} ({transfer.out.id}) -> "
              f"{transfer.into.name} ({transfer.into.id}), "
              f"buy £{transfer.purchase_price_at_plan:.1f}m at plan time, "
              f"cost {transfer.cost}")
    if not plan.transfers:
        print("  none")
    for earmark in plan.chip_plan:
        window = (
            f"window {earmark.start_event}-{earmark.stop_event}"
            if earmark.start_event is not None
            else "no matching window"
        )
        print(f"chip plan: {earmark.chip} gw{earmark.gw} ({earmark.status}, {window})")
    available = ", ".join(
        f"{chip.name} {chip.start_event}-{chip.stop_event}"
        for chip in plan.chips_available
    )
    print(f"chips available: {available or 'none'}")
    print(f"prices: {plan.price_resolution} — {plan.price_resolution_note}")
    for warning in plan.warnings:
        print(f"WARNING: {warning}")


def run_usage(args: argparse.Namespace) -> int:
    root = args.transcripts_root or default_transcripts_root(Path.cwd())
    if not root.is_dir():
        raise ValueError(f"transcripts root not found: {root}")
    if (args.since or args.all) and not args.list:
        raise ValueError("--since and --all apply to --list only")
    if (args.out or args.label) and not args.start:
        raise ValueError("--out and --label apply to an extract (--start/--end) only")
    if args.list:
        cutoff: datetime | None = None
        source = ""
        if args.since:
            cutoff, source = parse_ts(args.since), "--since"
        elif not args.all:
            found = latest_ledger_end(args.cost_root, before_gw=args.gw)
            if found:
                cutoff, source = found[0], str(found[1])
        if cutoff is not None:
            _stderr(
                f"listing sessions active after {fmt_ts(cutoff)} (from {source}); "
                f"--all lists every session"
            )
        rows = list_sessions(root, since=cutoff)
        if not rows:
            where = f"active after {fmt_ts(cutoff)}" if cutoff else f"under {root}"
            _stderr(f"no sessions {where}")
            return EXIT_EMPTY
        print(
            f"{'session':<9} {'first (UTC)':<17} {'last':<6} {'prompts':>7} "
            f"{'agents':>6} {'gw tags':<10} first prompt"
        )
        for row in rows:
            first = fmt_ts(row.first_at)[:16].replace("T", " ") if row.first_at else "-"
            last = fmt_ts(row.last_at)[11:16] if row.last_at else "-"
            tags = ",".join(f"GW{n}" for n in sorted(row.gw_tags)) or "-"
            print(
                f"{row.session_id[:8]:<9} {first:<17} {last:<6} {row.human_prompts:>7} "
                f"{row.agents:>6} {tags:<10} {row.first_prompt[:70]}"
            )
        return EXIT_OK
    if not args.session:
        raise ValueError("usage needs --session <id or prefix>; --list shows the sessions")
    session = load_session(root, args.session)
    if args.inspect:
        print(inspect_session(session, args.gw), end="")
        return EXIT_OK
    if not args.start or not args.end:
        raise ValueError(
            "usage needs --start and --end (ISO-8601 UTC); "
            "--inspect prints the timeline and a suggested window"
        )
    start, end = parse_ts(args.start), parse_ts(args.end)
    if end <= start:
        raise ValueError(f"--end {fmt_ts(end)} is before or equal to --start {fmt_ts(start)}")
    report = build_usage_report(
        session, gw=args.gw, start=start, end=end, label=args.label, transcripts_root=root
    )
    if not report.calls:
        _stderr(
            f"no API calls between {fmt_ts(start)} and {fmt_ts(end)} "
            f"in session {session.session_id}"
        )
        return EXIT_EMPTY
    out = args.out or (args.cost_root / f"gw{args.gw}")
    for path in write_report(report, out):
        print(path)
    t = report.totals
    print(
        f"calls: {t.calls}  agents: {t.agents}  wall: {t.wall_minutes} min  "
        f"cost: ${t.cost_usd:.2f}  (uncached-equivalent ${t.cost_uncached_equivalent:.2f})"
    )
    return EXIT_OK


def run_auth_import(args: argparse.Namespace) -> int:
    if not args.curl_file.is_file():
        raise ValueError(f"no curl capture at {args.curl_file}")
    capture = parse_curl(args.curl_file.read_text(encoding="utf-8"))
    save_auth(args.out, capture.credentials)
    print(f"source URL: {capture.url}")
    for line in redacted_summary(capture.credentials):
        print(line)
    print(f"wrote {args.out} (mode 0600)")
    if not has_auth_bearing_header(capture.credentials):
        _stderr(
            "WARNING: no authorization-like header in the capture — it may not "
            "authenticate; verify with: python -m fpl auth-check --gw N"
        )
    _warn_unless_ignored(args.curl_file)
    return EXIT_OK


def run_auth_refresh(
    args: argparse.Namespace,
    gateway_factory: Callable[[AuthCredentials], TokenGateway] | None = None,
) -> int:
    credentials = load_auth(args.auth)
    plan = derive_plan(
        credentials,
        endpoint=args.token_endpoint,
        client_id=args.client_id,
    )
    print(f"auth file: {args.auth}")
    for line in plan.describe():
        print(line)
    _print_current_expiry(credentials, plan)

    if args.dry_run:
        print("dry run — nothing sent")
        return EXIT_OK

    factory = gateway_factory or RequestsTokenGateway
    try:
        outcome = refresh_token(credentials, plan, factory(credentials))
    except (TokenEndpointError, TokenRefreshError) as exc:
        _stderr(f"FAIL — {exc}")
        return EXIT_ERROR
    except requests.RequestException as exc:
        _stderr(f"FAIL — token request failed: {_failure_reason(exc)}")
        return EXIT_ERROR

    save_auth(args.auth, outcome.credentials)
    print(f"wrote {args.auth} (mode 0600)")
    if outcome.bearer_expiry is not None:
        print(f"new bearer expires: {_stamp(outcome.bearer_expiry)}")
    elif outcome.expires_in_s is not None:
        print(f"new bearer expires in: {outcome.expires_in_s}s")
    # Rotation makes the token we just replaced unusable, so whether it
    # happened decides if an older copy of auth.json is still a fallback.
    print(
        "refresh token: rotated and saved"
        if outcome.rotated_refresh
        else "refresh token: unchanged, still valid"
    )
    print("verify with: python -m fpl auth-check --gw N")
    return EXIT_OK


def _print_current_expiry(credentials: AuthCredentials, plan: RefreshPlan) -> None:
    if plan.bearer_header is None:
        return
    expiry = expiry_of(credentials.headers[plan.bearer_header])
    if expiry is None:
        return
    remaining = (expiry - datetime.now(UTC)).total_seconds()
    state = "expired" if remaining <= 0 else "valid"
    print(
        f"current bearer: {state}, expiry {_stamp(expiry)} "
        f"({remaining / 60:+.0f} min)"
    )


def _stamp(moment: datetime) -> str:
    return f"{moment.astimezone(UTC):%Y-%m-%d %H:%M:%S}Z"


def _warn_unless_ignored(capture_file: Path) -> None:
    ignored = is_git_ignored(capture_file)
    if ignored is True:
        return
    if ignored is False:
        _stderr(
            f"WARNING: {capture_file} is not git-ignored and holds a plaintext "
            "bearer token — add it to .gitignore, then delete it"
        )
        return
    _stderr(
        f"note: could not determine whether {capture_file} is git-ignored — "
        "it holds a plaintext bearer token; delete it once you are done"
    )


def run_auth_check(
    store: SnapshotStore,
    args: argparse.Namespace,
    gateway_factory: Callable[[AuthCredentials], WriteGateway],
) -> int:
    credentials = load_auth(args.auth)
    print(f"auth file: {args.auth}")
    for line in redacted_summary(credentials):
        print(line)
    if not has_auth_bearing_header(credentials):
        _stderr(
            "WARNING: no authorization-like header in the credentials — the "
            "session may not authenticate (advice only: the schema is "
            "data-driven, so an unfamiliar header name is fine)"
        )
    team_id = _resolve_team_id(args.team_id, args.entry_file)
    service = WriteService(
        WriteApi(gateway_factory(credentials)),
        store,
        SnapshotStore(args.executor_root),
    )
    try:
        team = service.my_team(team_id)
    except SessionExpiredError as exc:
        _stderr(f"FAIL — {exc}")
        return EXIT_ERROR
    except requests.RequestException as exc:
        _stderr(f"FAIL — my-team request failed: {_failure_reason(exc)}")
        return EXIT_ERROR
    transfers = team.transfers
    print("PASS — authenticated session works")
    print(
        f"entry {team_id} — squad {len(team.picks)}, "
        f"bank {_tenths(transfers.bank)}, value {_tenths(transfers.value)}, "
        f"free transfers {_blank(transfers.limit)}"
    )
    chips = ", ".join(
        f"{chip.name} ({chip.status_for_entry or 'unknown'})" for chip in team.chips
    )
    print(f"chips: {chips or 'none'}")
    return EXIT_OK


def _failure_reason(exc: requests.RequestException) -> str:
    # Status and reason when the server answered; the exception's own text
    # only when it did not.
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if status is not None:
        return f"HTTP {status} {getattr(response, 'reason', '') or ''}".strip()
    return f"{type(exc).__name__}: {exc}"


def run_write_command(
    store: SnapshotStore,
    args: argparse.Namespace,
    gateway_factory: Callable[[AuthCredentials], WriteGateway],
) -> int:
    if args.command == "auth-check":
        return run_auth_check(store, args, gateway_factory)
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
    execution = _load_execution_plan(gw, args)
    chip = _resolve_chip(args, execution)
    if args.command == "set-lineup":
        picks = (
            execution.planned_picks()
            if execution is not None
            else _resolve_lineup_picks(args)
        )
        service.validate_formation(gw, picks)
        routed = route_chip(chip, LINEUP_TARGET)
        notes = _chip_routing_notes(chip, routed, "make-transfers")
        plan = service.plan_lineup(team_id=team_id, picks=picks, chip=routed)
        if plan.already_applied:
            print("already applied — current lineup matches; no request sent")
            _print_notes(notes)
            return EXIT_OK
        if not args.apply:
            _print_dry_run(plan.url, plan.payload, notes)
            return EXIT_OK
        print(f"applied and verified — audit: {service.apply_lineup(gw, plan)}")
        _print_notes(notes)
        return EXIT_OK
    routed = route_chip(chip, TRANSFERS_TARGET)
    notes = _chip_routing_notes(chip, routed, "set-lineup")
    plan = _transfer_plan(service, gw, team_id, args, execution, routed)
    if plan.already_applied:
        print("already applied — requested transfers are in place; no request sent")
        _print_notes(notes)
        return EXIT_OK
    if not args.apply:
        _print_dry_run(plan.url, plan.payload, [*plan.notes, *notes])
        return EXIT_OK
    print(f"applied and verified — audit: {service.apply_transfers(gw, plan)}")
    _print_notes(notes)
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


def _load_execution_plan(
    gw: int, args: argparse.Namespace
) -> ExecutionPlan | None:
    if args.from_plan is None:
        return None
    if not args.from_plan.is_file():
        raise ValueError(f"no plan at {args.from_plan}")
    return parse_plan(
        json.loads(args.from_plan.read_text(encoding="utf-8")), gw=gw
    )


def _resolve_chip(
    args: argparse.Namespace, execution: ExecutionPlan | None
) -> str | None:
    if execution is None:
        return args.chip
    if args.chip is not None and args.chip != execution.chip:
        raise ValueError(
            f"--chip {args.chip!r} contradicts the plan, which activates "
            f"{execution.chip or 'no chip'} — fix one of them"
        )
    return execution.chip


def _resolve_lineup_picks(args: argparse.Namespace) -> PlannedPicks:
    if args.from_final is not None:
        return parse_state_picks(_read_final(args.from_final), expected_gw=args.gw)
    if args.picks and args.captain is not None and args.vice is not None:
        return picks_from_ids(args.picks, captain=args.captain, vice=args.vice)
    raise ValueError(
        "provide --from-plan, --from-final, or --picks (15 ids in position "
        "order) with --captain and --vice"
    )


def _transfer_plan(
    service: WriteService,
    gw: int,
    team_id: int,
    args: argparse.Namespace,
    execution: ExecutionPlan | None,
    chip: str | None,
) -> TransferPlan:
    if execution is not None:
        return service.plan_transfers(
            gw=gw,
            team_id=team_id,
            chip=chip,
            target_ids=execution.planned_picks().ids(),
            planned_prices=execution.planned_prices(),
        )
    if args.from_final is not None:
        picks = parse_state_picks(_read_final(args.from_final), expected_gw=gw)
        return service.plan_transfers(
            gw=gw, team_id=team_id, chip=chip, target_ids=picks.ids()
        )
    if args.transfers_out and args.transfers_in:
        return service.plan_transfers(
            gw=gw, team_id=team_id, chip=chip,
            out_ids=args.transfers_out, in_ids=args.transfers_in,
        )
    raise ValueError("provide --from-plan, --from-final, or --out and --in id lists")


def _chip_routing_notes(
    chip: str | None, routed: str | None, owner_command: str
) -> list[str]:
    if chip is None or routed is not None:
        return []
    return [
        f"note: chip {chip} is activated by {owner_command}, not this command — "
        "sending chip: null here"
    ]


def _print_notes(notes: Sequence[str]) -> None:
    for note in notes:
        print(note)


def _print_dry_run(url: str, payload: dict, notes: Sequence[str]) -> None:
    print("DRY RUN — no request sent; re-run with --apply to execute")
    print(f"POST {url}")
    print(json.dumps(payload, indent=1))
    _print_notes(notes)


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
    # Flush first: stdout is block-buffered when piped, so an unflushed report
    # would surface after the warning that refers to it.
    sys.stdout.flush()
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


MINUTES_COLUMN = "minutes_by_round"


def print_players(
    rows: list[PlayerRow], fmt: str, minutes: dict[int, str] | None = None
) -> None:
    if fmt == "json":
        records = [slim_record(row) for row in rows]
        if minutes is not None:
            for record in records:
                record[MINUTES_COLUMN] = minutes[record["id"]]
        print(json.dumps(records, indent=1))
    elif fmt == "csv":
        writer = csv.writer(sys.stdout)
        header = list(PLAYERS_SLIM_COLUMNS)
        if minutes is not None:
            header.append(MINUTES_COLUMN)
        writer.writerow(header)
        for row in rows:
            values = slim_values(row)
            if minutes is not None:
                values.append(minutes[row.player.id])
            writer.writerow(values)
    else:
        tail = f"  {MINUTES_COLUMN}" if minutes is not None else ""
        print(f"{'id':>4}  {'name':<20} {'team':<4} {'pos':<3} {'price':>5} "
              f"{'st':<2} {'own%':>5} {'form':>5} {'pts':>4} {'pen':>3}{tail}")
        for row in rows:
            p = row.player
            pen = p.penalties_order if p.penalties_order is not None else ""
            extra = f"  {minutes[p.id]}" if minutes is not None else ""
            print(f"{p.id:>4}  {p.web_name:<20.20} {row.team_short_name:<4} "
                  f"{p.element_type.name:<3} {p.price_m:>5.1f} {p.status.value:<2} "
                  f"{p.selected_by_percent:>5.1f} {p.form:>5.1f} {p.total_points:>4} {pen:>3}{extra}")
        print(f"({len(rows)} players)")


if __name__ == "__main__":
    sys.exit(main())
