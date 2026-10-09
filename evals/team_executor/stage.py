"""Lays a case out on disk — the repo-relative inputs plus the replay
directory holding the fake server and the pinned clock — and runs the CLI
against it in-process. The live harness stages the agent's workspace this
way; the approved transfer id and the offline case tests use it too."""

from __future__ import annotations

import io
import json
import os
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fpl.clock import REPLAY_ENV, write_clock
from fpl.fake_server import seed_fake_server

from evals.team_executor.cases import TEAM_ID, LiveCase, case_files
from evals.team_executor.myteam import case_my_team

_TRANSFER_ID_PREFIX = "transfer id: "


@dataclass(frozen=True)
class CliResult:
    exit_code: int
    out: str
    err: str


def case_now(case: LiveCase) -> datetime:
    """The pinned clock: the case's offset before its gameweek's deadline."""
    bootstrap = json.loads(case_files(case, base=True)[case.bootstrap])
    event = next(e for e in bootstrap["events"] if e["id"] == case.gw)
    deadline = datetime.fromisoformat(event["deadline_time"].replace("Z", "+00:00"))
    return deadline - case.deadline_offset


def capture_request(canary: str) -> bytes:
    """A browser 'Copy as cURL' capture whose only values are the canary."""
    return (
        f"curl 'https://fantasy.premierleague.com/api/my-team/{TEAM_ID}/' \\\n"
        "  -H 'accept: */*' \\\n"
        f"  -H 'x-api-authorization: Bearer {canary}' \\\n"
        f"  -b 'refresh_token={canary}'\n"
    ).encode()


def workspace_files(case: LiveCase, auth: bytes, canary: str) -> dict[str, bytes]:
    files = case_files(case)
    files["data/auth.json"] = auth
    if case.capture:
        files["curl-request"] = capture_request(canary)
    return files


def seed_server(case: LiveCase, replay_dir: Path, *, base: bool = False) -> Path:
    return seed_fake_server(
        replay_dir, team_id=TEAM_ID, my_team=case_my_team(case, base=base),
        auth="ok" if base else case.auth,
        ignore_posts=() if base else case.ignore_posts,
    )


def stage(case: LiveCase, root: Path, files: Mapping[str, bytes], *, base: bool = False) -> Path:
    """Writes `files` under `root` and a replay directory beside it; returns
    the replay directory."""
    for rel, data in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    replay_dir = root.parent / "replay"
    replay_dir.mkdir(parents=True, exist_ok=True)
    write_clock(replay_dir, case_now(case), anchored_at=datetime.now(UTC))
    seed_server(case, replay_dir, base=base)
    return replay_dir


@contextmanager
def _inside(root: Path, replay_dir: Path) -> Iterator[None]:
    previous_cwd, previous_env = Path.cwd(), os.environ.get(REPLAY_ENV)
    os.chdir(root)
    os.environ[REPLAY_ENV] = str(replay_dir)
    try:
        yield
    finally:
        os.chdir(previous_cwd)
        if previous_env is None:
            os.environ.pop(REPLAY_ENV, None)
        else:
            os.environ[REPLAY_ENV] = previous_env


def run_cli(root: Path, replay_dir: Path, argv: list[str]) -> CliResult:
    from fpl.__main__ import main

    out, err = io.StringIO(), io.StringIO()
    with _inside(root, replay_dir), redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as exc:
            code = int(exc.code or 0)
    return CliResult(code, out.getvalue(), err.getvalue())


def approved_id(case: LiveCase) -> str | None:
    """The id the case's Approval block names, from a dry-run in a scratch
    copy: against the case's own transfers (`case`) or the unedited
    gameweek's (`base`). Neither auth nor the deadline enters the id, so the
    dry-run uses a working session and a comfortable clock."""
    if case.approval is None or case.approval.id_from == "none":
        return None
    base = case.approval.id_from == "base"
    variant = replace(case, auth="ok", ignore_posts=(), deadline_offset=timedelta(hours=24),
                      remove_plan=False)
    with tempfile.TemporaryDirectory(prefix="fpl-eval-id-") as scratch:
        root = Path(scratch) / "ws"
        files = case_files(variant, base=base)
        files["data/auth.json"] = b'{"headers": {"x-api-authorization": "Bearer x"}}'
        replay_dir = stage(variant, root, files, base=base)
        result = run_cli(root, replay_dir, [
            "make-transfers", "--gw", str(case.gw), "--from-plan", case.plan,
            "--executor-root", str(Path(scratch) / "pre"),
        ])
    ids = [line.removeprefix(_TRANSFER_ID_PREFIX) for line in result.out.splitlines()
           if line.startswith(_TRANSFER_ID_PREFIX)]
    if result.exit_code != 0 or len(ids) != 1:
        raise RuntimeError(f"{case.id}: no transfer id from the reference dry-run: "
                           f"{result.err.strip()[-300:]}")
    return ids[0]
