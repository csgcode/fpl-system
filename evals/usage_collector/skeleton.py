"""Reduces real Claude Code session transcripts to the fields the `usage`
CLI reads, so a frozen copy lists, inspects and costs exactly like the
original while carrying no prose, tool output or command text.

Run once from the archive: `python -m evals freeze usage-collector`.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from fpl.usage import _GIT_COMMIT, _SECRET_SHAPES, REDACTED

SKELETON_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "usage_collector" / "transcripts"
SESSIONS = ("8cbbfa17-efba-4c69-9b95-2d4a448b3b78", "8f06c38d-49f9-43f1-9887-0ebf72e60800")
PROMPT_CHARS = 500
COMMAND_CHARS = 300
_ASSISTANT_FIELDS = ("type", "timestamp", "isSidechain", "requestId", "effort", "version")
_MESSAGE_FIELDS = ("id", "model", "stop_reason")
_USAGE_FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens",
                 "output_tokens", "cache_creation", "output_tokens_details")


def skeletonize(src_root: Path, session_id: str, dst_root: Path) -> int:
    """Writes the skeleton of one session (main file, subagent files and
    their metadata) under dst_root; returns the number of lines written."""
    written = _skeleton_file(src_root / f"{session_id}.jsonl", dst_root / f"{session_id}.jsonl")
    subagents = src_root / session_id / "subagents"
    for path in sorted(subagents.glob("agent-*")):
        target = dst_root / session_id / "subagents" / path.name
        if path.name.endswith(".meta.json"):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        elif path.suffix == ".jsonl":
            written += _skeleton_file(path, target)
    return written


def _skeleton_file(src: Path, dst: Path) -> int:
    lines = []
    for raw in src.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            continue
        kept = _skeleton(record)
        if kept.get("timestamp") or kept.get("version"):
            lines.append(_without_home(json.dumps(kept, ensure_ascii=False)))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    return len(lines)


def _skeleton(record: dict[str, Any]) -> dict[str, Any]:
    kind = record.get("type")
    if kind == "assistant":
        kept = {k: record[k] for k in _ASSISTANT_FIELDS if k in record}
        message = record.get("message") or {}
        kept["message"] = {k: message[k] for k in _MESSAGE_FIELDS if k in message}
        if isinstance(message.get("usage"), dict):
            kept["message"]["usage"] = {k: message["usage"][k] for k in _USAGE_FIELDS
                                        if k in message["usage"]}
        content = message.get("content")
        kept["message"]["content"] = [
            _tool_use(block) for block in (content if isinstance(content, list) else [])
            if isinstance(block, dict) and block.get("type") == "tool_use"
        ]
        return kept
    if kind == "user":
        kept = {k: record[k] for k in ("type", "timestamp", "isMeta") if k in record}
        content = (record.get("message") or {}).get("content")
        if isinstance(content, list):
            if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
                return {k: record[k] for k in ("type", "timestamp") if k in record}
            content = " ".join(b.get("text", "") for b in content
                               if isinstance(b, dict) and b.get("type") == "text")
        if isinstance(content, str):
            kept["message"] = {"role": "user", "content": _clean(content[:PROMPT_CHARS])}
        return kept
    return {k: record[k] for k in ("type", "timestamp", "version") if k in record}


def _tool_use(block: dict[str, Any]) -> dict[str, Any]:
    source = block.get("input") or {}
    if block.get("name") == "Agent":
        tool_input = {"description": str(source.get("description") or "")}
    elif block.get("name") == "Bash" and _GIT_COMMIT.search(str(source.get("command") or "")):
        tool_input = {"command": _clean(str(source["command"])[:COMMAND_CHARS])}
    else:
        tool_input = {}
    return {"type": "tool_use", "id": block.get("id"), "name": block.get("name"), "input": tool_input}


def _without_home(text: str) -> str:
    """Spawn prompts name local paths, and Claude Code's temp dirs embed the
    home directory with `/` encoded as `-`; neither may name the account."""
    home = str(Path.home())
    return text.replace(home, "~").replace(home.replace("/", "-"), "-~")


def _clean(text: str) -> str:
    return _SECRET_SHAPES.sub(REDACTED, text)


def freeze_skeletons(archive: Path, dst_root: Path = SKELETON_ROOT) -> dict[str, int]:
    if dst_root.exists():
        shutil.rmtree(dst_root)
    return {sid: skeletonize(archive, sid, dst_root) for sid in SESSIONS}
