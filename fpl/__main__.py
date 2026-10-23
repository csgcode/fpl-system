"""CLI entry point. Usage: python -m fpl <command> --gw N [options]

Fetch commands map 1:1 to the data-collector outputs in
agents/data-collector.md; `players` is a filtered read over the cached
bootstrap. Cached snapshots are reused unless older than --max-age hours
(default 24) or --force is given. Errors go to stderr; exit 1 means the
command failed, exit 2 means it produced an empty or rejected result.
With FPL_REPLAY_DIR set, every request is answered from recordings in that
directory and nothing reaches the network (fpl/replay.py); when it also holds
a fake-server.json, write commands talk to a stateful fake (fpl/fake_server.py).
"""

from __future__ import annotations

import argparse
import csv
import functools
import json
import os
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
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
    squad_misses,
)
from fpl.capture import is_git_ignored, parse_curl
from fpl.decision_record import (
    LOCK_FILENAME,
    RecordPredictions,
    record_predictions,
    write_lock,
)
from fpl.corrections import agent_corrections, build_digest
from fpl.ep import (
    EpResult,
    build_predictions,
    force_prior_weight,
    inspect_fixtures,
    load_fixtures,
    load_inputs,
    write_predictions,
)
from fpl.http import RequestsGateway, RequestsTokenGateway, TokenEndpointError
from fpl.fixture_ratings import PRIORS_FILENAME, RatingRefusal, render_json, summary_lines
from fpl.fixture_ratings import load_inputs as load_rating_inputs
from fpl.fixture_ratings import rate as rate_fixtures
from fpl.fixture_ratings import write_outputs as write_rating_outputs
from fpl.fake_server import FakeFplServer, fake_server_dir
from fpl.final_check import Finding, check_final, check_proposal
from fpl.freshness import BASELINE_MAX_AGE_HOURS, FlagChange
from fpl import (
    backtest,
    gates,
    history_view,
    objective,
    objective_report,
    persistence,
    season_store,
    team_share,
)
from fpl.season_store import History
from fpl.models import (
    POSITION_ALIASES,
    Bootstrap,
    MyTeam,
    Player,
    PlayerStatus,
    Position,
)
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
from fpl.replay import ReplayGateway, network_blocked, replay_dir
from fpl.runlog import (
    LOGGED_COMMANDS,
    RunResult,
    append_run,
    build_row,
    run_log_path,
)
from fpl.repository import (
    PLAYERS_SLIM_COLUMNS,
    SORT_KEYS,
    PlayerFilter,
    PlayerRepository,
    PlayerRow,
    slim_record,
)
from fpl.service import (
    DEFAULT_MAX_AGE_HOURS,
    FetchEvent,
    FplDataService,
    PostDeadlineError,
    load_cached_bootstrap,
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
from fpl.store import ArchiveCollisionError, SnapshotMissingError, SnapshotStore, utcnow
from fpl.usage import build_report as build_usage_report
from fpl.usage import (
    TRANSCRIPTS_ROOT_ENV,
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
    LineupPlan,
    RefreshingGateway,
    SessionExpiredError,
    TransferPlan,
    VerifyMismatchError,
    WriteApi,
    WriteGateway,
    WriteService,
    transfer_id,
)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_EMPTY = 2
EXIT_FLAGS_CHANGED = 3
EXIT_NO_BASELINE = 4
EXIT_STALE_BASELINE = 5
DRY_RUN_LINE = "DRY RUN — no request sent; re-run with --apply to execute"

WRITE_COMMANDS = ("auth-check", "my-team", "set-lineup", "make-transfers")
DECISIONS_ROOT = Path("data/decisions")
ANALYSIS_ROOT = Path("data/analysis")
FINAL_FILENAME = "final.md"
PROPOSAL_FILENAME = "squad-proposal.md"
SUGGESTIONS_PATH = Path("data/suggestions.md")
PLAN_FILENAME = "plan.json"
COST_ROOT = Path("data/cost")
RETRO_ROOT = Path("data/retro")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fpl", description="Deterministic FPL data fetcher with snapshot cache."
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=season_store.DEFAULT_RAW_ROOT,
        help=f"snapshot root (default: {season_store.DEFAULT_RAW_ROOT})",
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
    fixtures = add("fixtures", "fetch full fixture list")
    summaries = add("summaries", "fetch element-summary per player")
    for deadline_guarded in (bootstrap, fixtures, summaries):
        deadline_guarded.add_argument(
            "--allow-post-deadline",
            action="store_true",
            help="fetch into --gw even though its deadline has passed",
        )
    group = summaries.add_mutually_exclusive_group(required=True)
    group.add_argument("--ids", type=_id_list, help="comma-separated player ids")
    group.add_argument(
        "--shortlist", action="store_true", help="all shortlisted players"
    )
    group.add_argument(
        "--missing-past", action="store_true",
        help="every bootstrap player with no kept summary in any gameweek, i.e. "
             "no history_past for the season store",
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
        "actuals", "report one round's returns from its final event-live snapshot",
        cached=False,
    )
    actuals.add_argument(
        "--round", type=_gameweek, required=True, help="completed gameweek to total"
    )
    actuals.add_argument(
        "--ids", type=_id_list, required=True, help="comma-separated player ids"
    )
    event_live = add(
        "event-live", "fetch one data-checked round's live stats (final once fetched)"
    )
    event_live.add_argument(
        "--round", type=_gameweek, required=True,
        help="data-checked gameweek to fetch, before --gw",
    )
    add("slim-csv", "write players-slim.csv from cached bootstrap", cached=False)
    add(
        "prior-season",
        "write prior-season.json from cached summaries",
        cached=False,
    )
    flags = add(
        "flags",
        "force-refresh injury/news flags and diff them against a baseline "
        f"(exit {EXIT_FLAGS_CHANGED}: a --ids player changed; "
        f"exit {EXIT_NO_BASELINE}: no baseline; "
        f"exit {EXIT_STALE_BASELINE}: baseline over {BASELINE_MAX_AGE_HOURS:g}h old)",
        cached=False,
    )
    flags.add_argument(
        "--ids", type=_id_list, required=True,
        help="comma-separated player ids — the gate scope",
    )
    flags.add_argument(
        "--baseline", type=Path,
        help="bootstrap JSON to diff against (default: the cached gw bootstrap "
             "as it stood just before this refresh)",
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
    make_transfers.add_argument(
        "--approve", metavar="TRANSFER_ID",
        help="with --apply: the transfer id the user approved, as the dry run "
             "printed it; the POST is refused when it does not match",
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
        help=f"Claude Code transcripts dir (default: ${TRANSCRIPTS_ROOT_ENV}, "
             "else ~/.claude/projects/<encoded cwd>)",
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
    plan_cmd.add_argument(
        "--analysis-root", type=Path, default=ANALYSIS_ROOT,
        help=f"root holding gw{{N}}/players-*.json, locked into {LOCK_FILENAME} "
             "beside final.md before the gw's deadline (a changed lock is "
             "archived and replaced)",
    )
    plan_cmd.add_argument("--format", choices=("table", "json"), default="table")
    plan_cmd.add_argument(
        "--out", type=Path, help="also write the JSON document to this path"
    )

    final_check = add(
        "final-check",
        "check the carry rules from squad-proposal.md into final.md (exit 1: a FAIL)",
        cached=False,
    )
    final_check.add_argument(
        "--proposal", type=Path,
        help=f"default: {DECISIONS_ROOT}/gw{{N}}/{PROPOSAL_FILENAME}",
    )
    final_check.add_argument(
        "--final", type=Path,
        help=f"default: {DECISIONS_ROOT}/gw{{N}}/{FINAL_FILENAME}, checked only if it exists",
    )
    final_check.add_argument(
        "--prev-final", type=Path,
        help=f"default: {DECISIONS_ROOT}/gw{{N-1}}/{FINAL_FILENAME}, if it exists",
    )
    final_check.add_argument(
        "--suggestions", type=Path, default=SUGGESTIONS_PATH,
        help=f"default: {SUGGESTIONS_PATH}",
    )

    # Local-only: the objective is a pure function of the EP files, the cached
    # bootstrap and the previous final.md (docs/ep-model.md §7).
    objective = add(
        "objective",
        "score the squad and a transfer plan on the spec objective, blend and prior-only "
        "(exit 1: --moves fails the transfer rule)",
        cached=False,
    )
    objective_report.add_arguments(objective)
    season_store.add_history_arguments(objective)

    backtest.register(add)
    gates.register(add)
    persistence.register(add)

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
    calibrate.add_argument(
        "--predictions-from", choices=("commit", "worktree"), default="commit",
        help="commit (default): the gw's predictions lock, else its decision commit; "
             "worktree: the files on disk",
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
    ep.add_argument(
        "--decisions-root", type=Path, default=DECISIONS_ROOT,
        help=f"root holding gw{{N}}/{FINAL_FILENAME}; once it exists only --out may be written",
    )
    ep.add_argument("--format", choices=("table", "json"), default="table")
    ep.add_argument("--limit", type=int, default=15, help="rows shown in the table")
    ep.add_argument(
        "--allow-missing-ids", type=_id_list, default=[],
        help="comma-separated ids above £4.5m that may lack an inputs row; "
             "left unscored and listed in the warnings",
    )
    ep.add_argument(
        "--share-detail", action="store_true",
        help="name each row the team-xG share check flags, with its shares, on stderr",
    )
    ep.add_argument(
        "--prior-weight", type=_unit_interval, metavar="W",
        help="what-if: force every row's prior weight to W in [0, 1], superseding "
             "per-row overrides; requires --out",
    )
    season_store.add_history_arguments(ep)

    # Local-only: club ratings and fixture rows are a pure function of the
    # cached snapshots plus club-priors.json (docs/ep-model.md §6).
    fixtures_rate = add(
        "fixtures-rate", "compile club ratings + fixtures.json + fixtures-tables.md",
        cached=False,
    )
    fixtures_rate.add_argument(
        "--priors", type=Path,
        help=f"club priors (default: <analysis-root>/{PRIORS_FILENAME})",
    )
    fixtures_rate.add_argument(
        "--analysis-root", type=Path, default=ANALYSIS_ROOT,
        help="root that receives gw{N}/fixtures.json and fixtures-tables.md",
    )
    fixtures_rate.add_argument("--format", choices=("table", "json"), default="table")
    season_store.add_history_arguments(fixtures_rate)

    players = add("players", "filtered view over the cached bootstrap", cached=False)
    season_store.add_history_arguments(players)
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
        help="append minutes per completed round (1..N-1) from the season store "
             "(gw N's cached summaries with --history-from summaries): one entry per "
             "round, '-' for no fixture row, double gameweeks summed",
    )
    players.add_argument(
        "--minutes-last", type=_positive_int, metavar="K",
        help="with --minutes, only the last K completed rounds",
    )
    players.add_argument(
        "--fields",
        help="comma-separated columns to print, in order (csv/json); default: all",
    )

    corrections = add(
        "corrections",
        "retro corrections: the latest status table plus every active rule's text, "
        "or with --agent only the active corrections addressed to that agent",
        cached=False,
    )
    corrections.add_argument(
        "--round", type=_gameweek,
        help="the round under review: read retros of earlier rounds (default: N-1); "
             "not with --agent, which reads every retro before GW N",
    )
    corrections.add_argument("--agent", help="agent code, e.g. A3 or CODE")
    corrections.add_argument("--retro-root", type=Path, default=RETRO_ROOT)
    season_store.register(add)
    history_view.register(add, positions=_position_set, ids=_id_list, count=_positive_int)
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


def _positive_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid count: {raw!r}") from exc
    if value < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {raw}")
    return value


def _unit_interval(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid prior weight: {raw!r}") from exc
    if not 0 <= value <= 1:
        raise argparse.ArgumentTypeError(f"prior weight must lie in [0, 1], got {raw}")
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
    recordings = replay_dir()
    if recordings is not None:
        # The throttle protects the live API; recordings need none.
        return FplDataService(FplApi(ReplayGateway(recordings)), store, throttle_s=0.0)
    return FplDataService(FplApi(RequestsGateway()), store)


def _default_write_gateway_factory(
    auth_path: Path,
) -> Callable[[AuthCredentials], WriteGateway]:
    recordings = replay_dir()
    fake = fake_server_dir(recordings)
    if fake is not None:
        _stderr(f"FAKE SERVER — nothing is sent to FPL ({fake})")
        return lambda credentials: FakeFplServer(fake)
    if recordings is not None:
        return lambda credentials: ReplayGateway(recordings, session_errors=True)
    return _refreshing_write_gateway(auth_path)


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


def offline_in_replay(entry: Callable[..., int]) -> Callable[..., int]:
    @functools.wraps(entry)
    def guarded(*args, **kwargs) -> int:
        if replay_dir() is None:
            return entry(*args, **kwargs)
        with network_blocked():
            return entry(*args, **kwargs)

    return guarded


@offline_in_replay
def main(
    argv: list[str] | None = None,
    service_factory: Callable[[SnapshotStore], FplDataService] | None = None,
    write_gateway_factory: Callable[[AuthCredentials], WriteGateway] | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    store = SnapshotStore(args.data_root)
    try:
        season_store.check_history_arguments(args)
        if args.command == "auth-import":
            return run_auth_import(args)
        if args.command == "auth-refresh":
            return run_auth_refresh(args)
        if args.command == "usage":
            return run_usage(args)
        if args.command == "final-check":
            return run_final_check(args)
        if args.command == "objective":
            return objective_report.run(args.data_root, args)
        if args.command == "backtest":
            return backtest.run(args.data_root, args)
        if args.command == "gates":
            return gates.run(args)
        if args.command == "persistence":
            return persistence.run(args)
        if args.command == "corrections":
            return run_corrections(args)
        if args.command == "store":
            return season_store.run(args.data_root, args)
        if args.command == "history":
            return history_view.run(args.data_root, args)
        if args.command == "fixtures-rate":
            return run_fixtures_rate(store, args)
        if args.command in WRITE_COMMANDS:
            return run_logged_write(
                store,
                args,
                write_gateway_factory or _default_write_gateway_factory(args.auth),
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
    except PostDeadlineError as exc:
        _stderr(f"error: {exc}")
        if hasattr(args, "allow_post_deadline"):
            _stderr(f"hint: pass --allow-post-deadline to fetch into gw{exc.gw} anyway")
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
            allow_post_deadline=args.allow_post_deadline,
        )
        print(f"{store.path(gw, 'bootstrap')} {_cache_note(service)}")
        print(f"fetched at {store.fetched_at(gw, 'bootstrap')}")
        print(f"players: {len(bootstrap.elements)}, teams: {len(bootstrap.teams)}, "
              f"chips: {len(bootstrap.chips)}")
        print(f"current GW: {bootstrap.current_gw()}, next GW: {bootstrap.next_gw()}, "
              f"next deadline: {bootstrap.next_deadline()}")
        print(_current_status_line(bootstrap))
    elif args.command == "fixtures":
        fixtures = service.fixtures(
            gw,
            max_age_hours=args.max_age,
            force=args.force,
            allow_post_deadline=args.allow_post_deadline,
        )
        print(f"{store.path(gw, 'fixtures')} ({len(fixtures)} fixtures) "
              f"{_cache_note(service)}")
    elif args.command == "summaries":
        ids = (service.shortlist_ids(gw) if args.shortlist
               else service.missing_past_ids(gw) if args.missing_past else args.ids)
        summaries = service.player_summaries(
            gw,
            player_ids=ids,
            max_age_hours=args.max_age,
            force=args.force,
            allow_post_deadline=args.allow_post_deadline,
        )
        print(f"{len(summaries)} summaries under {store.dir(gw) / 'players'} "
              f"{_cache_note(service) or '(0 fetched, 0 cached)'}")
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
        if args.round >= gw:
            raise ValueError(f"--round {args.round} must be before --gw {gw}")
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
    elif args.command == "event-live":
        if args.round >= gw:
            raise ValueError(f"--round {args.round} must be before --gw {gw}")
        live = service.event_live(
            gw, event=args.round, max_age_hours=args.max_age, force=args.force
        )
        print(f"{store.path(gw, f'event-live-e{args.round}')} "
              f"({len(live.elements)} players) {_cache_note(service)}")
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
                f"first (python -m fpl summaries --gw {gw} --missing-past)"
            )
            return EXIT_EMPTY
    elif args.command == "flags":
        return run_flags(service, gw, args)
    elif args.command == "plan":
        return run_plan(store, gw, args)
    elif args.command == "calibrate":
        return run_calibrate(service, gw, args)
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
        fields = _player_fields(args.fields, args.format)
        rows = PlayerRepository(store).query(gw, player_filter, args.sort, args.limit)
        minutes = (_minutes_by_round(History.from_args(args.data_root, args), gw, rows,
                                     args.minutes_last)
                   if args.minutes else None)
        print_players(rows, args.format, minutes, fields)
    return EXIT_OK


def run_flags(service: FplDataService, gw: int, args: argparse.Namespace) -> int:
    check = service.flag_check(gw, player_ids=args.ids, baseline_path=args.baseline)
    print(f"refreshed at {check.refreshed_at}")
    print(f"{'id':>4}  {'name':<20} {'st':<2} {'chance':>6}  "
          f"{'news_added':<25} news")
    for p in check.players:
        chance = "" if p.chance_of_playing_next_round is None else f"{p.chance_of_playing_next_round}%"
        added = p.news_added.isoformat() if p.news_added else ""
        print(f"{p.id:>4}  {p.web_name:<20.20} {p.status.value:<2} "
              f"{chance:>6}  {added:<25} {p.news}")
    if check.baseline is None:
        _stderr(
            f"error: no baseline — no cached gw{gw} bootstrap preceded this refresh "
            f"and no --baseline was given; the gate cannot pass without a delta"
        )
        return EXIT_NO_BASELINE
    print()
    print(f"baseline: {check.baseline.source} (fetched {check.baseline.fetched_at or 'unknown'})")
    age = check.baseline_age_hours
    print(f"baseline age: {'unknown' if age is None else f'{age:.1f}h'}")
    print(f"gate: {len(check.gate)} of {len(check.gate_ids)} ids changed")
    for change in check.gate:
        print(f"  {_flag_change_line(change)}")
    print(f"pool (informational): {len(check.pool)} changed")
    for position in Position:
        rows = [c for c in check.pool if c.position == position]
        if rows:
            print(f"  {position.name}")
            for change in rows:
                print(f"    {_flag_change_line(change)}")
    print(f"wrote {check.delta_path}")
    if check.stale:
        _stderr(
            f"error: baseline is {age:.1f}h old (> {BASELINE_MAX_AGE_HOURS:g}h) — rerun "
            f"the data collector before finalizing"
        )
        return EXIT_STALE_BASELINE
    return EXIT_FLAGS_CHANGED if check.gate else EXIT_OK


def _flag_change_line(change: FlagChange) -> str:
    # news is free text: quoted so an empty value and a boundary stay visible.
    fields = "; ".join(
        f"{c.field} {c.before!r} -> {c.after!r}" if c.field == "news"
        else f"{c.field} {c.before} -> {c.after}"
        for c in change.changes
    )
    return f"{change.id:>4} {change.web_name}: {fields}"


def _record_name(source: str) -> str:
    kind, _, ident = source.partition(" ")
    return f"{'predictions lock' if kind == 'lock' else 'decision commit'} {ident}"


def run_calibrate(service: FplDataService, gw: int, args: argparse.Namespace) -> int:
    service.data_checked_basis(gw, args.round)
    if args.predictions_from == "commit":
        record = record_predictions(args.analysis_root, args.decisions_root, args.round)
    else:
        record = RecordPredictions(
            load_predictions(args.analysis_root / f"gw{args.round}"), "worktree", ()
        )
    live = service.event_live(
        gw, event=args.round, max_age_hours=args.max_age, force=args.force
    )
    cache_note = _cache_note(service)
    report = build_report(
        record.predictions,
        live,
        match_round=args.round,
        picks=_calibration_picks(
            args.decisions_root / f"gw{args.round}" / FINAL_FILENAME, args.round
        ),
        prior_reports=_prior_reports(args.retro_root, args.round),
        predictions_source=record.source,
        drifted=record.drifted,
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
    if report.drifted:
        _stderr(
            f"WARNING: {_files(len(report.drifted), 'prediction file')} changed after "
            f"{_record_name(report.predictions_source)} — calibrated the "
            f"decision record: {', '.join(report.drifted)}"
        )
    return EXIT_OK


def run_ep(store: SnapshotStore, gw: int, args: argparse.Namespace) -> int:
    position: Position | None = args.position
    analysis_dir = args.analysis_root / f"gw{gw}"
    fixtures_path = args.fixtures or analysis_dir / "fixtures.json"
    if args.prior_weight is not None:
        if args.check:
            raise ValueError("--prior-weight cannot be combined with --check")
        # A what-if must never replace the canonical players-{pos}.json.
        if args.out is None:
            raise ValueError("--prior-weight requires --out")
    if args.check:
        return run_ep_check(store, gw, args, fixtures_path)
    if position is None:
        raise ValueError("--position is required unless --check is given")
    if args.out is None and (args.decisions_root / f"gw{gw}" / FINAL_FILENAME).is_file():
        raise ValueError(
            f"gw{gw} is decided ({FINAL_FILENAME} exists): players-{position.name}.json "
            "is the decision record; write a what-if with --out"
        )
    inputs_path = args.inputs or analysis_dir / f"inputs-{position.name}.json"
    out_path = args.out or analysis_dir / f"players-{position.name}.json"
    inputs = load_inputs(inputs_path)
    if inputs.position != position:
        raise ValueError(
            f"{inputs_path} is for {inputs.position.name}, not --position {position.name}"
        )
    if args.prior_weight is not None:
        inputs = force_prior_weight(inputs, args.prior_weight)
    fixtures = load_fixtures(fixtures_path)
    bootstrap = load_cached_bootstrap(store, gw)
    judged = [entry.id for entry in inputs.players]
    wanted = [p.id for p in bootstrap.elements if p.element_type == position] + judged
    history = History.from_args(args.data_root, args)
    summaries = history.summaries(gw, wanted, pinned=judged)
    result = build_predictions(
        bootstrap, summaries, fixtures, inputs, gw=gw,
        allow_missing=frozenset(args.allow_missing_ids), history_from=history.source,
    )
    documents = result.to_documents()
    club_xg, skipped = _club_xg(store, gw, args.analysis_root, history)
    flagged = team_share.annotate(
        documents,
        histories={pid: summary.history for pid, summary in summaries.items()},
        club_xg=club_xg, base_mean=fixtures.base_mean(),
        att_by_club={club: rating.att for club, rating in fixtures.ratings.items()},
    )
    # players-{pos}.json is derived from inputs + fixtures.json + cached
    # snapshots, so overwriting it is safe, like plan.json.
    write_predictions(out_path, documents)
    if args.format == "json":
        print(json.dumps(documents, indent=1))
    else:
        print_ep(result, args.limit, {pid: team_share.labels(f) for pid, f in flagged.items()})
    print(f"wrote {out_path}")
    if result.missing_summaries:
        _stderr(
            f"WARNING: missing summaries ({len(result.missing_summaries)}) scored on "
            f"league-mean priors — fetch with: "
            f"{history.fetch_hint(gw, result.missing_summaries)}"
        )
    for warning in result.warnings:
        _stderr(f"WARNING: {warning}")
    if skipped is not None:
        _stderr(f"WARNING: share check skipped: {skipped}")
    else:
        _print_share_check(result, flagged, detail=args.share_detail)
    return EXIT_OK


def _club_xg(
    store: SnapshotStore, gw: int, analysis_root: Path, history: History
) -> tuple[dict[tuple[int, str], float], str | None]:
    # The share check is a reading aid: a refusal becomes a skip warning and
    # never stops `ep`, which the live cycle runs at step 3.
    try:
        run = rate_fixtures(load_rating_inputs(
            store, gw, priors_path=analysis_root / PRIORS_FILENAME, analysis_root=analysis_root,
            history=history,
        ))
    # _side_xg raises a plain ValueError for a summary row with no venue.
    except (SnapshotMissingError, ValueError) as exc:
        return {}, str(exc)
    return team_share.club_xg_map(run.matches), None


def _print_share_check(
    result: EpResult, flagged: dict[int, tuple[team_share.ShareFlag, ...]], *, detail: bool
) -> None:
    ids = sorted(flagged)
    listed = f" (ids {','.join(str(i) for i in ids)})" if ids else ""
    _stderr(f"share check: {len(ids)} flagged{listed}")
    if detail:
        names = {row.id: row.name for row in result.rows}
        for pid in ids:
            _stderr(f"share check: id {pid} {names[pid]} {team_share.details(flagged[pid])}")


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
    judged = [entry.id for entry in inputs.players]
    wanted = [p.id for p in bootstrap.elements if p.element_type == position] + judged
    history = History.from_args(args.data_root, args)
    result = build_predictions(
        bootstrap, history.summaries(gw, wanted, pinned=judged),
        load_fixtures(fixtures_path),
        inputs, gw=gw, allow_missing=frozenset(args.allow_missing_ids),
        history_from=history.source,
    )
    print(
        f"{inputs_path} OK: {len(result.rows)} players scored, "
        f"{len(result.missing_summaries)} without cached summary — nothing written"
    )
    for warning in result.warnings:
        _stderr(f"WARNING: {warning}")
    return EXIT_OK


NO_FIXTURE = "-"
NO_SUMMARY = "no summary"


@dataclass(frozen=True)
class MinutesView:
    """Minutes per completed round. A player maps each round in `rounds` to
    its minutes (double gameweeks summed) or NO_FIXTURE, or is NO_SUMMARY."""

    rounds: tuple[int, ...]
    by_player: dict[int, dict[int, int | str] | str]

    @property
    def label(self) -> str:
        if not self.rounds:
            return MINUTES_COLUMN
        first, last = self.rounds[0], self.rounds[-1]
        return f"minutes_r{first}" if first == last else f"minutes_r{first}-r{last}"

    def joined(self, player_id: int) -> str:
        minutes = self.by_player[player_id]
        if isinstance(minutes, str):
            return minutes
        return ",".join(str(minutes[r]) for r in self.rounds)

    def keyed(self, player_id: int) -> dict[str, int | str] | str:
        minutes = self.by_player[player_id]
        if isinstance(minutes, str):
            return minutes
        return {str(r): minutes[r] for r in self.rounds}


def _minutes_by_round(
    history: History, gw: int, rows: list[PlayerRow], last: int | None = None
) -> MinutesView:
    """Rounds 1..gw-1 (the last `last` of them when given)."""
    first = 1 if last is None else max(1, gw - last)
    rounds = tuple(range(first, gw))
    matches = history.matches_by_player(gw, [row.player.id for row in rows])
    result: dict[int, dict[int, int | str] | str] = {}
    for row in rows:
        records = matches.get(row.player.id)
        if records is None:
            result[row.player.id] = NO_SUMMARY
            continue
        played: dict[int, int] = {}
        for match in records:
            if match.round is not None:
                played[match.round] = played.get(match.round, 0) + match.minutes
        result[row.player.id] = {r: played.get(r, NO_FIXTURE) for r in rounds}
    return MinutesView(rounds, result)


def _player_fields(raw: str | None, fmt: str) -> tuple[str, ...]:
    if raw is None:
        return PLAYERS_SLIM_COLUMNS
    if fmt not in ("csv", "json"):
        raise ValueError("--fields needs --format csv or json")
    fields = tuple(part.strip() for part in raw.split(",") if part.strip())
    for name in fields:
        if name not in PLAYERS_SLIM_COLUMNS:
            raise ValueError(
                f"unknown field {name!r}; valid: {','.join(PLAYERS_SLIM_COLUMNS)}"
            )
    return fields


def print_ep(result: EpResult, limit: int, share: dict[int, str | None]) -> None:
    print(
        f"gw{result.gw} {result.position.name}: {len(result.rows)} scored, "
        f"{result.not_scored} not scored (≤£4.5m or unavailable, absent from inputs), "
        f"{len(result.missing_summaries)} without cached summary"
    )
    print(f"model {result.config.digest()}")
    source = (
        f"pooled from {result.league_pool} summaries"
        if result.league_source == "pooled"
        else "v1 fallback table (see warnings)"
    )
    print(f"league mean: {source}")
    print(
        f"{'id':>4}  {'name':<18} {'team':<4} {'price':>5} {'p_st':>5} {'ep6':>6} "
        f"{'ep/£m':>5} {'p4':>4} {'ret5':>5} {'unc':<4} {'app':>5} {'att':>5} {'cs':>5} "
        f"{'gc':>5} {'dc':>5} {'sv':>5} {'bon':>5} {'crd':>5} {'share':<10}  fixtures"
    )
    calibrated = result.position in objective.P4_CALIBRATED
    for row in result.rows[:limit]:
        t = row.terms
        p4 = f"{row.p4_gw[0]:.2f}" if calibrated else "-"
        print(
            f"{row.id:>4}  {row.name:<18.18} {row.team:<4} {row.price:>5.1f} "
            f"{row.p_start:>5.2f} {row.ep_total6:>6.2f} {row.ep_per_million:>5.2f} "
            f"{p4:>4} {objective.ret5_text(row.returns5):>5} {row.uncertainty.value:<4} "
            f"{t.appearance:>5.1f} {t.attack:>5.1f} "
            f"{t.clean_sheet:>5.1f} {t.goals_conceded:>5.1f} {t.defcon:>5.1f} "
            f"{t.saves:>5.1f} {t.bonus:>5.1f} {t.cards:>5.1f} {share.get(row.id) or '-':<10}  "
            f"{' '.join(row.fixtures)}"
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


def _files(count: int, noun: str = "file") -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def print_calibration(report: CalibrationReport, cache_note: str) -> None:
    print(
        f"round {report.round} calibration — {report.overall.n} players "
        f"matched, {len(report.unmatched_prediction_ids)} unmatched "
        f"{cache_note}".rstrip()
    )
    if report.predictions_source == "worktree":
        print("predictions: worktree")
    else:
        drift = _files(len(report.drifted)) if report.drifted else "none"
        print(f"predictions: {report.predictions_source} (drift: {drift})")

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
        f"{minutes.expected_starts:.1f}, actual {minutes.actual_starts}, "
        f"gap {minutes.expected_starts - minutes.actual_starts:+.1f}"
    )
    if report.defcon:
        hits = sum(1 for line in report.defcon if line.hit)
        print(f"defcon: {hits}/{len(report.defcon)} hits (players with 60'+)")
    cumulative = report.cumulative
    if cumulative is not None and len(cumulative.rounds) > 1:
        rounds = ",".join(str(r) for r in cumulative.rounds)
        print(
            f"cumulative (rounds {rounds}): n={cumulative.overall.n} "
            f"bias={cumulative.overall.bias:.2f} mae={cumulative.overall.mae:.2f} "
            f"brier={cumulative.minutes_brier:.4f}"
        )
    if report.squad is not None:
        _print_squad(report)
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


def _print_squad(report: CalibrationReport) -> None:
    squad = report.squad
    assert squad is not None
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
    joined = {line.id: line for line in report.players}
    misses = squad_misses(report)
    missed = {miss.id for miss in misses}
    print("squad rows (slot role id name pred act err start p_start min; * = |err| > 3):")
    for line in squad.players:
        flag = "C" if line.captain else ("VC" if line.vice else "")
        pred = "-" if line.predicted is None else f"{line.predicted:.2f}"
        act = "-" if line.actual is None else str(line.actual)
        mins = "-" if line.minutes is None else str(line.minutes)
        player = joined.get(line.id) if line.predicted is not None else None
        err = "-" if player is None else f"{player.error:+.2f}"
        start = "-" if player is None else ("Y" if player.started else "N")
        p_start = "-" if player is None else f"{player.p_start:.2f}"
        star = "*" if line.id in missed else " "
        print(
            f"  {line.slot:>3} {line.role:<5} {line.id:>4}  {line.name:<20.20} "
            f"pred {pred:>6}  act {act:>3}  err {err:>6}{star} start {start}  "
            f"p_start {p_start}  min {mins:>3}  {flag}".rstrip()
        )
    listed = ", ".join(f"{m.slot} {m.name} {m.error:+.2f}" for m in misses)
    print(f"squad misses (|err| > 3): {listed or 'none'}")


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
    for warning in write_lock(
        args.analysis_root / f"gw{gw}", final_path.parent / LOCK_FILENAME, gw,
        deadline=plan.deadline,
    ):
        _stderr(f"WARNING: {warning}")
    if args.format == "json":
        print(document)
    else:
        free_now = previous_state.free_transfers_banked if previous_state else None
        print_plan(plan, free_now=free_now)
    return EXIT_OK


def run_corrections(args: argparse.Namespace) -> int:
    root: Path = args.retro_root
    if args.agent is not None:
        if args.round is not None:
            raise ValueError("--round applies to the retro digest only, not with --agent")
        return _print_agent_corrections(root, args.gw, args.agent)
    before = args.round if args.round is not None else args.gw - 1
    digest = build_digest(root, before_round=before)
    if digest.latest is None:
        print(f"corrections: none (no retro before round {before})")
        return EXIT_OK
    span = (digest.sources[0] if len(digest.sources) == 1
            else f"{digest.sources[0]}–{digest.sources[-1]}")
    print(f"corrections — status from {root / digest.latest}; rules from {span}")
    print("| C# | Agent | Status | Evidence |")
    print("|---|---|---|---|")
    for row in digest.rows:
        print(row.line)
    for rule in digest.new:
        print(f"| C{rule.number} | {', '.join(rule.agents)} | new in {rule.source} | – |")
    print(f"active rules: {len(digest.active)}")
    for rule in digest.active:
        print(f"{rule.text}  [{rule.source}]")
    for number in digest.missing:
        _stderr(f"warning: C{number} has a status row but no rule text")
    return EXIT_OK


def _print_agent_corrections(root: Path, gw: int, agent: str) -> int:
    view = agent_corrections(root, gw=gw, agent=agent)
    if view.latest is None:
        print("no retro yet")
        return EXIT_OK
    print(f"corrections for {agent} from {root / view.latest}: "
          f"{len(view.active)} active, {len(view.retired)} retired")
    for correction in view.active:
        rule = correction.rule
        print(f"C{rule.number} [{correction.status}] defined in {root / rule.source}")
        print(rule.text)
        print()
    retired = "; ".join(f"C{row.number} {row.status}" for row in view.retired)
    print(f"retired (not shown): {retired or 'none'}")
    return EXIT_OK


def run_final_check(args: argparse.Namespace) -> int:
    gw = args.gw
    proposal_path = args.proposal or DECISIONS_ROOT / f"gw{gw}" / PROPOSAL_FILENAME
    if not proposal_path.is_file():
        raise ValueError(f"no squad proposal at {proposal_path}")
    proposal = proposal_path.read_text(encoding="utf-8")
    previous_path = args.prev_final or _final_path(gw - 1)
    previous = (previous_path.read_text(encoding="utf-8")
                if gw > MIN_GW and previous_path.is_file() else None)
    results = _rule_lines(("P1", "P2", "P3"), check_proposal(
        proposal, gw=gw, previous_final=previous,
        suggestions_exists=args.suggestions.is_file()))
    final_path = args.final or _final_path(gw)
    if final_path.is_file():
        results += _rule_lines(("F1", "F2", "F3", "F4"), check_final(
            final_path.read_text(encoding="utf-8"), proposal, gw=gw))
    else:
        print(f"{FINAL_FILENAME}: not written — proposal checks only")
    for line in results:
        print(line)
    return EXIT_ERROR if any(line.startswith("FAIL") for line in results) else EXIT_OK


def _rule_lines(rules: tuple[str, ...], findings: list[Finding]) -> list[str]:
    by_rule = {f.rule: f.message for f in findings}
    return [f"FAIL {rule}: {by_rule[rule]}" if rule in by_rule else f"PASS {rule}"
            for rule in rules]


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
    path = explicit or final_path.parent.parent / f"gw{gw - 1}" / FINAL_FILENAME
    if not path.is_file():
        if explicit is not None:
            raise ValueError(f"no final.md at {path}")
        return None, None
    return path, parse_state(path.read_text(encoding="utf-8"), expected_gw=gw - 1)


def print_plan(plan: ExecutionPlan, *, free_now: int | None = None) -> None:
    """`free_now` is the previous STATE's free_transfers_banked: the count
    available at this deadline. The plan's own count is for the next one."""
    entry = "unset" if plan.team_id is None else str(plan.team_id)
    previous_gw = plan.gw - 1
    print(
        f"gw{plan.gw} plan (schema {plan.schema_version}) — entry {entry}, "
        f"deadline {plan.deadline.isoformat()}"
    )
    print(f"formation {plan.formation}, bank {plan.bank:.1f}, "
          f"value {plan.team_value:.1f}")
    print(f"chip: {plan.chip or 'none'}")
    print(f"captain: {plan.captain.name} ({plan.captain.id}), "
          f"vice: {plan.vice.name} ({plan.vice.id})")
    this_deadline = (
        f"{free_now} at this deadline (gw{previous_gw} STATE)"
        if free_now is not None
        else f"unknown at this deadline (no gw{previous_gw} STATE read)"
    )
    print(f"free transfers: {this_deadline}, "
          f"{plan.free_transfers_banked} banked for the next deadline")
    print(f"{'slot':>4}  {'id':>4}  {'name':<20} {'club':<4} {'pos':<3} "
          f"{'price':>5}  role")
    for pick in plan.picks:
        role = "(C)" if pick.is_captain else ("(VC)" if pick.is_vice_captain else "")
        note = " ".join(part for part in (role, "" if pick.starts else "bench") if part)
        print(f"{pick.slot:>4}  {pick.element:>4}  {pick.name:<20.20} "
              f"{pick.club:<4} {pick.position:<3} {pick.now_cost:>5.1f}  "
              f"{note}".rstrip())
    print(f"bench order: {', '.join(str(element) for element in plan.bench)}")
    print(f"transfers: {len(plan.transfers)} ({plan.transfer_source})")
    for transfer in plan.transfers:
        print(f"  {transfer.out.name} ({transfer.out.id}) -> "
              f"{transfer.into.name} ({transfer.into.id}), "
              f"buy £{transfer.purchase_price_at_plan:.1f}m at plan time, "
              f"cost {transfer.cost}")
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


def run_fixtures_rate(store: SnapshotStore, args: argparse.Namespace) -> int:
    priors_path = args.priors or args.analysis_root / PRIORS_FILENAME
    try:
        run = rate_fixtures(load_rating_inputs(
            store, args.gw, priors_path=priors_path, analysis_root=args.analysis_root,
            history=History.from_args(args.data_root, args)))
    except RatingRefusal as exc:
        _stderr(f"error: {exc}")
        if exc.hint:
            _stderr(f"hint: {exc.hint}")
        return EXIT_ERROR
    # Both outputs are derived from snapshots + priors, so overwriting is safe.
    paths = write_rating_outputs(run, args.analysis_root / f"gw{args.gw}")
    report = sys.stderr if args.format == "json" else sys.stdout
    if args.format == "json":
        print(render_json(run), end="")
    for line in [*summary_lines(run), *(f"wrote {path}" for path in paths)]:
        print(line, file=report)
    for warning in run.warnings:
        _stderr(f"WARNING: {warning}")
    return EXIT_OK


def run_usage(args: argparse.Namespace) -> int:
    env_root = os.environ.get(TRANSCRIPTS_ROOT_ENV)
    root = args.transcripts_root or (Path(env_root) if env_root else default_transcripts_root(Path.cwd()))
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
    if replay_dir() is not None:
        _stderr("error: auth-refresh is unavailable in replay mode")
        return EXIT_ERROR
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
) -> RunResult:
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
        return _auth_failed(f"FAIL — {exc}")
    except requests.RequestException as exc:
        return _auth_failed(f"FAIL — my-team request failed: {_failure_reason(exc)}")
    transfers = team.transfers
    passed = "PASS — authenticated session works"
    print(passed)
    print(
        f"entry {team_id} — squad {len(team.picks)}, "
        f"free transfers {_blank(transfers.limit)}"
    )
    _print_money(team, _cached_now_costs(store, args.gw))
    chips = ", ".join(
        f"{chip.name} ({chip.status_for_entry or 'unknown'})" for chip in team.chips
    )
    print(f"chips: {chips or 'none'}")
    return RunResult(EXIT_OK, "pass", passed)


def _auth_failed(line: str) -> RunResult:
    _stderr(line)
    return RunResult(EXIT_ERROR, "fail", line)


def _failure_reason(exc: requests.RequestException) -> str:
    # Status and reason when the server answered; the exception's own text
    # only when it did not.
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if status is not None:
        return f"HTTP {status} {getattr(response, 'reason', '') or ''}".strip()
    return f"{type(exc).__name__}: {exc}"


class _PostWatch:
    """Notes whether a POST was attempted, which decides whether a failure
    may have changed the team."""

    def __init__(self, factory: Callable[[AuthCredentials], WriteGateway]) -> None:
        self._factory = factory
        self.attempted = False

    def __call__(self, credentials: AuthCredentials) -> WriteGateway:
        inner = self._factory(credentials)
        watch = self

        class Watched:
            def get_json(self, url: str) -> dict | list:
                return inner.get_json(url)

            def post_json(self, url: str, payload: dict) -> dict | list | None:
                watch.attempted = True
                return inner.post_json(url, payload)

        return Watched()


def run_logged_write(
    store: SnapshotStore,
    args: argparse.Namespace,
    gateway_factory: Callable[[AuthCredentials], WriteGateway],
) -> int:
    """Runs a write command and appends its outcome to the run log. A failure
    is logged, then re-raised so main() prints it as before."""
    if args.command not in LOGGED_COMMANDS:
        return run_write_command(store, args, gateway_factory).exit_code
    watch = _PostWatch(gateway_factory)
    try:
        result = run_write_command(store, args, watch)
    except Exception as exc:
        _record_run(args, _failure_result(args.command, exc, watch.attempted))
        raise
    _record_run(args, result)
    return result.exit_code


def _failure_result(command: str, exc: Exception, posted: bool) -> RunResult:
    if command == "auth-check":
        outcome = "fail"
    elif isinstance(exc, VerifyMismatchError):
        outcome = "verify-failed"
    elif posted:
        outcome = "error"
    else:
        outcome = "refused"
    return RunResult(EXIT_ERROR, outcome, _error_line(exc))


def _error_line(exc: Exception) -> str:
    """The line main() prints for `exc`."""
    if isinstance(exc, (AuthMissingError, SnapshotMissingError)):
        return f"error: {exc}"
    if isinstance(exc, ValidationError):
        return (
            f"error: payload failed validation ({exc.error_count()} problems); "
            f"first: {exc.errors()[0].get('loc')} {exc.errors()[0].get('msg')}"
        )
    if isinstance(exc, requests.RequestException):
        return f"error: network request failed: {exc}"
    if isinstance(exc, OSError) and not isinstance(exc, ArchiveCollisionError):
        return f"error: filesystem failure: {exc}"
    return f"error: {exc}"


def _record_run(args: argparse.Namespace, result: RunResult) -> None:
    row = build_row(
        at=utcnow(),
        command=args.command,
        apply=bool(getattr(args, "apply", False)),
        result=result,
        plan=getattr(args, "from_plan", None),
        fake_server=replay_dir() is not None,
    )
    append_run(run_log_path(args.executor_root, args.gw), row)


def run_write_command(
    store: SnapshotStore,
    args: argparse.Namespace,
    gateway_factory: Callable[[AuthCredentials], WriteGateway],
) -> RunResult:
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
        elements = _cached_elements(store, gw)
        _print_my_team(
            service.my_team(team_id),
            team_id,
            {pid: e.web_name for pid, e in elements.items()},
            {pid: e.now_cost for pid, e in elements.items()},
        )
        return RunResult(EXIT_OK, "read", "")
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
            done = "already applied — current lineup matches; no request sent"
            print(done)
            _print_notes(notes)
            return RunResult(EXIT_OK, "already-applied", done)
        if not args.apply:
            _print_dry_run(plan.url, plan.payload, notes, details=_lineup_lines(plan))
            return RunResult(EXIT_OK, "dry-run", DRY_RUN_LINE)
        audit = service.apply_lineup(gw, plan)
        applied = f"applied and verified — audit: {audit}"
        print(applied)
        _print_notes(notes)
        return RunResult(EXIT_OK, "applied", applied, audit=audit)
    routed = route_chip(chip, TRANSFERS_TARGET)
    notes = _chip_routing_notes(chip, routed, "set-lineup")
    plan = _transfer_plan(service, gw, team_id, args, execution, routed)
    if plan.already_applied:
        done = "already applied — requested transfers are in place; no request sent"
        print(done)
        _print_notes(notes)
        return RunResult(EXIT_OK, "already-applied", done)
    approval_id = transfer_id(plan.payload)
    if not args.apply:
        names = {pid: e.web_name for pid, e in _cached_elements(store, gw).items()}
        _print_dry_run(
            plan.url, plan.payload, [*plan.notes, *notes],
            summary=_transfer_lines(plan.payload, names),
        )
        print(f"transfer id: {approval_id}")
        return RunResult(EXIT_OK, "dry-run", DRY_RUN_LINE, transfer_id=approval_id)
    _ensure_approved(args.approve, approval_id)
    audit = service.apply_transfers(gw, plan)
    applied = f"applied and verified — audit: {audit}"
    print(applied)
    _print_notes(notes)
    return RunResult(EXIT_OK, "applied", applied, audit=audit, transfer_id=approval_id)


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


def _ensure_approved(approved: str | None, actual: str) -> None:
    if approved is None:
        raise ValueError(
            "make-transfers --apply needs --approve <transfer id> — dry-run "
            "first and pass the id the user approved"
        )
    if approved != actual:
        raise ValueError(
            f"--approve {approved} does not match this payload's transfer id "
            f"{actual} — the transfers changed since approval; dry-run again and "
            "get the user's approval for the new id"
        )


def _transfer_lines(payload: dict, names: dict[int, str]) -> list[str]:
    return [
        f"transfer: {names.get(row['element_out'], '?')} ({row['element_out']}) → "
        f"{names.get(row['element_in'], '?')} ({row['element_in']}), "
        f"sell £{row['selling_price'] / 10:.1f}m, buy £{row['purchase_price'] / 10:.1f}m"
        for row in payload["transfers"]
    ]


def _lineup_lines(plan: LineupPlan) -> list[str]:
    picks = plan.expected.in_position_order()
    captain = next(p for p in picks if p.captain)
    vice = next(p for p in picks if p.vice)
    bench = ", ".join(f"{p.name} ({p.id})" for p in picks if not p.starts)
    return [
        f"captain: {captain.name} ({captain.id}), vice: {vice.name} ({vice.id})",
        f"bench: {bench}",
        "changes from the current lineup:",
        *(f"  {change}" for change in plan.changes),
    ]


def _print_dry_run(
    url: str,
    payload: dict,
    notes: Sequence[str],
    *,
    summary: Sequence[str] = (),
    details: Sequence[str] = (),
) -> None:
    """`summary` lines go before the payload, `details` after it."""
    print(DRY_RUN_LINE)
    print(f"POST {url}")
    for line in summary:
        print(line)
    print(json.dumps(payload, indent=1))
    for line in details:
        print(line)
    _print_notes(notes)


def _print_my_team(
    team: MyTeam,
    team_id: int,
    names: dict[int, str],
    now_costs: dict[int, int],
) -> None:
    transfers = team.transfers
    print(
        f"entry {team_id} — "
        f"free transfers {_blank(transfers.limit)}, made {_blank(transfers.made)}"
    )
    _print_money(team, now_costs)
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


def _print_money(team: MyTeam, now_costs: dict[int, int]) -> None:
    # The API's transfers.value is a market-price figure; agents once copied
    # it as the squad's worth, which overstates what selling can raise.
    # Every total is labelled with its basis so none can be misread.
    transfers = team.transfers
    sell_sum = sum(pick.selling_price for pick in team.picks)
    budget = None if transfers.bank is None else sell_sum + transfers.bank
    print(f"sell_sum {_tenths(sell_sum)}  (sum of selling prices)")
    print(f"bank {_tenths(transfers.bank)}")
    print(
        f"budget {_tenths(budget) or 'n/a'}  "
        "(sell_sum + bank: what a wildcard or rebuild can spend)"
    )
    if now_costs:
        market_sum = sum(now_costs.get(pick.element, 0) for pick in team.picks)
        print(f"market_sum {_tenths(market_sum)}  (sum of now_cost, cached bootstrap)")
    else:
        print("market_sum n/a  (no cached bootstrap)")
    print(
        f"api_value {_tenths(transfers.value)}  "
        "(market basis, from the API's transfers.value — never selling prices)"
    )


def _cached_elements(store: SnapshotStore, gw: int) -> dict[int, Player]:
    try:
        bootstrap = load_cached_bootstrap(store, gw)
    except SnapshotMissingError:
        return {}
    return {p.id: p for p in bootstrap.elements}


def _cached_now_costs(store: SnapshotStore, gw: int) -> dict[int, int]:
    return {pid: p.now_cost for pid, p in _cached_elements(store, gw).items()}


def _tenths(value: int | None) -> str:
    return "" if value is None else f"{value / 10:.1f}"


def _blank(value: object) -> str:
    return "" if value is None else str(value)


def _stderr(message: str) -> None:
    # Flush first: stdout is block-buffered when piped, so an unflushed report
    # would surface after the warning that refers to it.
    sys.stdout.flush()
    print(message, file=sys.stderr)


def _current_status_line(bootstrap: Bootstrap) -> str:
    current = next((e for e in bootstrap.events if e.is_current), None)
    if current is None:
        return "current GW status: none"
    return (
        f"current GW {current.id} status: "
        f"finished={str(current.finished).lower()} "
        f"data_checked={str(current.data_checked).lower()}"
    )


def _cache_note(service: FplDataService) -> str:
    return _format_fetch_log(service.take_fetch_log())


def _format_fetch_log(events: Sequence[FetchEvent]) -> str:
    if not events:
        return ""
    if len(events) == 1:
        event = events[0]
        if event.fetched:
            return "(fetched)"
        suffix = ", final" if event.final else ""
        if event.age_hours is None:
            return f"(cached, age unknown{suffix})"
        return f"(cached, age {event.age_hours:.1f}h{suffix})"
    fetched = sum(1 for event in events if event.fetched)
    return f"({fetched} fetched, {len(events) - fetched} cached)"


MINUTES_COLUMN = "minutes_by_round"


def print_players(
    rows: list[PlayerRow], fmt: str, minutes: MinutesView | None = None,
    fields: tuple[str, ...] = PLAYERS_SLIM_COLUMNS,
) -> None:
    if fmt == "json":
        records = []
        for row in rows:
            full = slim_record(row)
            record = {name: full[name] for name in fields}
            if minutes is not None:
                record[MINUTES_COLUMN] = minutes.keyed(row.player.id)
            records.append(record)
        print(json.dumps(records, indent=1))
    elif fmt == "csv":
        writer = csv.writer(sys.stdout)
        header = list(fields)
        if minutes is not None:
            header.append(minutes.label)
        writer.writerow(header)
        for row in rows:
            full = slim_record(row)
            values = [full[name] for name in fields]
            if minutes is not None:
                values.append(minutes.joined(row.player.id))
            writer.writerow(values)
    else:
        tail = f"  {minutes.label}" if minutes is not None else ""
        print(f"{'id':>4}  {'name':<20} {'team':<4} {'pos':<3} {'price':>5} "
              f"{'st':<2} {'own%':>5} {'form':>5} {'pts':>4} {'pen':>3}{tail}")
        for row in rows:
            p = row.player
            pen = p.penalties_order if p.penalties_order is not None else ""
            extra = f"  {minutes.joined(p.id)}" if minutes is not None else ""
            print(f"{p.id:>4}  {p.web_name:<20.20} {row.team_short_name:<4} "
                  f"{p.element_type.name:<3} {p.price_m:>5.1f} {p.status.value:<2} "
                  f"{p.selected_by_percent:>5.1f} {p.form:>5.1f} {p.total_points:>4} {pen:>3}{extra}")
        print(f"({len(rows)} players)")


if __name__ == "__main__":
    sys.exit(main())
