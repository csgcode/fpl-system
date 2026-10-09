"""The executor's run log: one JSON line per `auth-check`, `make-transfers` or
`set-lineup` run, whatever its outcome — checked, dry-run, refused, applied.

The CLI writes it because the CLI sees every outcome, refusals included, and
cannot skip the write. The file is append-only: a plain append, never the
snapshot store, which archives and rewrites. Rows carry outcomes, paths and
ids, never credentials.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

RUN_LOG_FILE = "runs.jsonl"
LOGGED_COMMANDS = frozenset({"auth-check", "make-transfers", "set-lineup"})


@dataclass(frozen=True)
class RunResult:
    """`message` is the result or error line exactly as the CLI printed it."""

    exit_code: int
    outcome: str
    message: str
    audit: Path | None = None
    transfer_id: str | None = None


def run_log_path(executor_root: Path, gw: int) -> Path:
    return executor_root / f"gw{gw}" / RUN_LOG_FILE


def build_row(
    *,
    at: datetime,
    command: str,
    apply: bool,
    result: RunResult,
    plan: Path | None,
    fake_server: bool,
) -> dict:
    return {
        "at": at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "command": command,
        "apply": apply,
        "outcome": result.outcome,
        "message": result.message,
        "plan": str(plan) if plan is not None else None,
        "plan_sha256": (
            hashlib.sha256(plan.read_bytes()).hexdigest()
            if plan is not None and plan.is_file()
            else None
        ),
        "transfer_id": result.transfer_id,
        "audit": str(result.audit) if result.audit is not None else None,
        "fake_server": fake_server,
    }


def append_run(path: Path, row: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as log:
        log.write(json.dumps(row, ensure_ascii=False) + "\n")
