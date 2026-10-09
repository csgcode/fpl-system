"""Every live team-executor case, run offline through the real CLI and the
fake server by the command sequence the spec prescribes. A case whose
expected lines or POSTs drift fails here, not in a paid run."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.harness.workspace import make_dummy_auth
from evals.team_executor.cases import (
    LIVE_CASES,
    REPLAY_CASES,
    LiveCase,
    audit_payload,
)
from evals.team_executor.myteam import PRICES, build_my_team
from evals.team_executor.stage import (
    CliResult,
    approved_id,
    capture_request,
    run_cli,
    stage,
    workspace_files,
)
from fpl.capture import parse_curl
from fpl.fake_server import POSTS_LOG


def prescribed_run(case: LiveCase, root: Path, replay_dir: Path) -> list[CliResult]:
    """The spec's steps, followed exactly."""
    results: list[CliResult] = []

    def cli(*argv: str) -> CliResult:
        results.append(run_cli(root, replay_dir, list(argv)))
        return results[-1]

    gw, plan = str(case.gw), case.plan
    if not (root / plan).is_file():
        return results
    if case.capture and cli("auth-import", "--curl-file", "curl-request").exit_code:
        return results
    if cli("auth-check", "--gw", gw).exit_code:
        return results
    dry = cli("make-transfers", "--gw", gw, "--from-plan", plan)
    if dry.exit_code:
        return results
    if "already applied" not in dry.out:
        approved = approved_id(case)
        printed = [l.removeprefix("transfer id: ") for l in dry.out.splitlines()
                   if l.startswith("transfer id: ")]
        if approved is None or printed != [approved]:
            return results
        if cli("make-transfers", "--gw", gw, "--from-plan", plan, "--apply",
               "--approve", approved).exit_code:
            return results
    lineup = cli("set-lineup", "--gw", gw, "--from-plan", plan)
    if lineup.exit_code or "already applied" in lineup.out:
        return results
    cli("set-lineup", "--gw", gw, "--from-plan", plan, "--apply")
    return results


def posts(replay_dir: Path) -> list[dict]:
    path = replay_dir / POSTS_LOG
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.fixture(scope="module", params=LIVE_CASES, ids=lambda c: c.id)
def played(request, tmp_path_factory):
    case = request.param
    auth = make_dummy_auth()
    root = tmp_path_factory.mktemp(case.id) / "ws"
    replay_dir = stage(case, root, workspace_files(case, auth.content.data, auth.canary))
    return case, root, replay_dir, prescribed_run(case, root, replay_dir), auth.canary


def test_the_prescribed_calls_match_the_case(played):
    case, _, _, results, _ = played
    assert len(results) == case.required_calls


def test_every_expected_line_is_printed(played):
    case, _, _, results, _ = played
    printed = {line for r in results for line in (r.out + r.err).splitlines()}
    for line in case.expected_lines:
        assert line in printed


def test_the_posts_are_the_expected_ones(played):
    case, _, replay_dir, _, _ = played
    sent = posts(replay_dir)
    kinds = ["transfers" if p["url"].endswith("/transfers/") else "lineup" for p in sent]
    assert kinds == [e.kind for e in case.expected_posts]
    for post, expected in zip(sent, case.expected_posts, strict=True):
        if expected.audit is not None:
            assert post["payload"] == audit_payload(*expected.audit)
        for key, value in expected.payload.items():
            assert post["payload"][key] == value


def test_the_run_log_and_audits_never_hold_the_canary(played):
    case, root, replay_dir, results, canary = played
    for path in [*(root / "data" / "executor").rglob("*"), replay_dir / POSTS_LOG]:
        if path.is_file():
            assert canary not in path.read_text(encoding="utf-8")
    for result in results:
        assert canary not in result.out + result.err


def test_the_run_log_has_a_row_per_logged_command(played):
    case, root, _, results, _ = played
    log = root / "data" / "executor" / f"gw{case.gw}" / "runs.jsonl"
    rows = log.read_text(encoding="utf-8").splitlines() if log.is_file() else []
    logged = sum(1 for r in results if "auth file:" in r.out or "FAKE SERVER" in r.err)
    assert len(rows) == logged


def test_the_s3_partial_apply_changes_the_id_the_user_approved():
    case = next(c for c in LIVE_CASES if c.id.startswith("S3"))
    assert approved_id(case) is not None
    variant = next(c for c in LIVE_CASES if c.id.startswith("F5"))
    assert approved_id(case) == approved_id(variant)


def test_the_capture_parses_and_names_only_the_canary():
    capture = parse_curl(capture_request("EVALCANARY-x").decode())
    assert capture.url.startswith("https://fantasy.premierleague.com/api/my-team/")
    assert set(capture.credentials.headers.values()) | set(
        capture.credentials.cookies.values()) <= {"*/*", "Bearer EVALCANARY-x", "EVALCANARY-x"}


def test_the_price_table_covers_the_gw4_to_gw6_squad():
    squad = {1, 4, 68, 69, 106, 202, 229, 237, 249, 411, 423, 427, 445, 481, 497}
    assert set(PRICES) == squad


def test_a_website_swap_buys_at_the_bootstrap_price():
    picks = [{"element": 69, "position": 7, "is_captain": False, "is_vice_captain": False}]
    team = build_my_team(picks, 6, swaps=((69, 94),), now_costs={94: 62})
    assert team["picks"][0] | {} == {
        "element": 94, "position": 7, "selling_price": 62, "purchase_price": 62,
        "multiplier": 1, "is_captain": False, "is_vice_captain": False,
    }
    assert team["transfers"]["limit"] == 3


def test_replay_cases_point_at_frozen_fixtures():
    for case in REPLAY_CASES:
        assert case.fixture.is_file()
