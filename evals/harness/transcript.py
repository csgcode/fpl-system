"""One parser for Claude Code subagent JSONL and `claude -p` stream-json.

Both formats carry the same `{type, message}` user/assistant records; the
stream adds `system` and `result` records and tags nested-subagent records
with `parent_tool_use_id`.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PERSISTED_MARKER = "<persisted-output>"
HANDBACK_TOOL = "SubagentHandback"


@dataclass(frozen=True)
class ToolResult:
    text: str
    is_error: bool
    truncated: bool


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    input: Mapping[str, Any]
    result: ToolResult | None
    turn: int = 0
    """The ordinal (from 1) of the assistant message that issued the call;
    parallel tool uses in one message share it."""


@dataclass(frozen=True)
class Transcript:
    prompt: str | None
    calls: tuple[ToolCall, ...]
    final_text: str
    cost_usd: float | None


def load_transcript(path: Path) -> Transcript:
    with path.open(encoding="utf-8") as handle:
        return parse_records(json.loads(line) for line in handle if line.strip())


def parse_records(records: Iterable[dict]) -> Transcript:
    prompt: str | None = None
    uses: list[tuple[dict, int]] = []
    turns: dict[str, int] = {}
    turn = 0
    results: dict[str, ToolResult] = {}
    last_text = ""
    result_record: dict | None = None

    for record in records:
        kind = record.get("type")
        if kind == "result":
            result_record = record
            continue
        if kind not in ("user", "assistant") or record.get("parent_tool_use_id"):
            continue
        content = record.get("message", {}).get("content")
        if isinstance(content, str):
            if kind == "user" and prompt is None:
                prompt = content
            continue
        if kind == "assistant":
            message_id = record.get("message", {}).get("id") or f"anon-{len(turns)}"
            turn = turns.setdefault(message_id, len(turns) + 1)
        for block in content or ():
            block_type = block.get("type")
            if block_type == "tool_use":
                uses.append((block, turn))
            elif block_type == "tool_result":
                results[block["tool_use_id"]] = _tool_result(block)
            elif block_type == "text" and kind == "assistant":
                last_text = block["text"]

    seen: set[str] = set()
    calls = []
    for block, turn in uses:
        if block["id"] in seen:
            continue
        seen.add(block["id"])
        calls.append(ToolCall(block["id"], block["name"], block.get("input") or {},
                              results.get(block["id"]), turn))
    return Transcript(
        prompt=prompt,
        calls=tuple(calls),
        final_text=_final_text(calls, result_record, last_text),
        cost_usd=_cost(result_record),
    )


def tool_turns(transcript: Transcript, *,
               exclude: tuple[str, ...] = (HANDBACK_TOOL,)) -> list[tuple[ToolCall, ...]]:
    """The calls grouped by the turn that issued them, in order; a turn whose
    calls are all `exclude`d is dropped."""
    grouped: dict[int, list[ToolCall]] = {}
    for call in transcript.calls:
        if call.name not in exclude:
            grouped.setdefault(call.turn, []).append(call)
    return [tuple(calls) for _, calls in sorted(grouped.items())]


def _tool_result(block: dict) -> ToolResult:
    content = block.get("content")
    if isinstance(content, list):
        text = "\n".join(part.get("text", "") for part in content
                         if part.get("type") == "text")
    else:
        text = content or ""
    return ToolResult(text=text, is_error=bool(block.get("is_error")),
                      truncated=text.startswith(PERSISTED_MARKER))


def _final_text(calls: list[ToolCall], result_record: dict | None, last_text: str) -> str:
    handbacks = [c for c in calls if c.name == HANDBACK_TOOL]
    if handbacks:
        return str(handbacks[-1].input.get("message", ""))
    if result_record is not None and isinstance(result_record.get("result"), str):
        return result_record["result"]
    return last_text


def _cost(result_record: dict | None) -> float | None:
    if result_record is None:
        return None
    cost = result_record.get("total_cost_usd")
    return float(cost) if cost is not None else None
