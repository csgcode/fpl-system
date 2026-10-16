"""Freezes a real Claude Code transcript into a committed replay fixture.

Only what the graders read survives: user and assistant records, the message
fields, no thinking blocks, no attachments (they carry the user's private
instructions and session context), no duplicated tool output. Machine paths
are rewritten so the fixture names no real directory. A redaction gate then
refuses the whole file if anything looks like a credential or personal data.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

FROZEN_ROOT = "/repo"
MUNGED_ROOT = "-repo"
_KEPT_TYPES = ("user", "assistant")
_KEPT_FIELDS = ("type", "uuid", "parentUuid", "timestamp", "message")
_KEPT_MESSAGE_FIELDS = ("role", "id", "model", "content", "usage")
_DROPPED_BLOCKS = ("thinking", "redacted_thinking")
_PERSISTED_PATH = re.compile(r"Full output saved to: (\S+)")
# An `ls -l` row in JSON-escaped text: mode, link count, then the owner and
# group columns, which name the local account.
_LONG_LISTING = re.compile(r'((?:^|\\n|")[-dlcbps][rwxsStT-]{9}[@+.]?\s+\d+\s+)\S+(\s+)\S+')

# Cookie names from data/auth.example.json.
_COOKIE_NAMES = ("datadome", "cf_clearance", "global_sso_id", "pl_guest_id")
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("bearer token", re.compile(r"Bearer\s+[A-Za-z0-9._~+/-]{16,}")),
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("cookie", re.compile(r"(?:%s)(?:=|\\?\":)" % "|".join(_COOKIE_NAMES))),
    # The commit-attribution trailer agents sometimes echo is no one's address.
    ("email", re.compile(r"(?<![A-Za-z0-9._%+-])(?!noreply@anthropic\.com(?![A-Za-z0-9.-]))"
                         r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("eval canary", re.compile(r"EVALCANARY")),
)


ARCHIVE_ENV = "FPL_TRANSCRIPTS_ARCHIVE"


class RedactionError(ValueError):
    pass


def transcripts_archive() -> Path:
    """The durable transcript backup. Claude Code prunes ~/.claude/projects."""
    configured = os.environ.get(ARCHIVE_ENV)
    if configured:
        return Path(configured)
    return Path.home() / "Dev" / "Personal" / "fpl-transcripts-archive"


def redaction_findings(text: str) -> list[str]:
    """Names of the secret patterns found — never the matched values."""
    return [name for name, pattern in SECRET_PATTERNS if pattern.search(text)]


def freeze(src: Path, dst: Path, repo_root: str, *, inline_persisted: bool = True,
           persisted_dirs: Sequence[Path] = ()) -> int:
    """Writes the stripped fixture; returns the number of records kept. With
    `inline_persisted` False a persisted tool output keeps the preview the
    agent actually saw instead of the full saved output. A saved output that
    is no longer at its recorded path is looked up by file name in each of
    `persisted_dirs` (an archived session's tool-results/)."""
    lines: list[str] = []
    problems: list[str] = []
    for index, raw in enumerate(src.read_text(encoding="utf-8").splitlines()):
        if not raw.strip():
            continue
        record = _strip(json.loads(raw), inline_persisted, persisted_dirs)
        if record is None:
            continue
        line = _rewrite_machine_details(json.dumps(record, ensure_ascii=False), repo_root)
        problems += [f"record {index}: {name}" for name in redaction_findings(line)]
        lines.append(line)
    if problems:
        raise RedactionError(f"{src.name}: refusing to freeze — " + "; ".join(problems))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    return len(lines)


def _strip(record: dict[str, Any], inline_persisted: bool = True,
           persisted_dirs: Sequence[Path] = ()) -> dict[str, Any] | None:
    if record.get("type") not in _KEPT_TYPES:
        return None
    message = record.get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        tool_output = record.get("toolUseResult")
        saved_path = (
            tool_output.get("persistedOutputPath") if isinstance(tool_output, dict) else None
        )
        content = [_inline_persisted(block, saved_path, persisted_dirs) if inline_persisted
                   else block
                   for block in content if block.get("type") not in _DROPPED_BLOCKS]
        if not content:
            return None
    kept = {key: record[key] for key in _KEPT_FIELDS if key in record}
    kept["message"] = {key: message[key] for key in _KEPT_MESSAGE_FIELDS if key in message}
    kept["message"]["content"] = content
    return kept


def _inline_persisted(block: dict[str, Any], saved_path: str | None,
                      persisted_dirs: Sequence[Path] = ()) -> dict[str, Any]:
    content = block.get("content")
    if block.get("type") != "tool_result" or not isinstance(content, str):
        return block
    if not content.startswith("<persisted-output>"):
        return block
    if saved_path is None:
        match = _PERSISTED_PATH.search(content)
        saved_path = match.group(1) if match else None
    if saved_path is None:
        return block
    candidates = [Path(saved_path)] + [d / Path(saved_path).name for d in persisted_dirs]
    found = next((c for c in candidates if c.is_file()), None)
    if found is None:
        return block
    return {**block, "content": found.read_text(encoding="utf-8")}


def _rewrite_machine_details(text: str, repo_root: str) -> str:
    root = repo_root.rstrip("/")
    text = text.replace(root, FROZEN_ROOT)
    # Claude Code names a project's scratchpad and transcript directories
    # after the repo path with every non-alphanumeric turned into "-".
    text = text.replace(re.sub(r"[^A-Za-z0-9]", "-", root), MUNGED_ROOT)
    text = text.replace(str(Path.home()), "~")
    return _LONG_LISTING.sub(r"\1user\2staff", text)
