"""Readers graders share: a CLI call's exit code and a report compared
formatting-blind."""

from __future__ import annotations

import re

from evals.harness.transcript import ToolCall

_EXIT_PREFIX = re.compile(r"\AExit code (\d+)")
_ECHOED_EXIT = re.compile(r"(?im)^[^\n]*\bexit\w*\s*[=:]?\s*(\d+)\s*\Z")


def cli_exit(call: ToolCall) -> int | None:
    """Claude Code prefixes a failed command's output with `Exit code N`;
    an agent may instead echo `$?` as the last line. None when the call has
    no result."""
    result = call.result
    if result is None:
        return None
    prefixed = _EXIT_PREFIX.match(result.text)
    if prefixed:
        return int(prefixed.group(1))
    if result.is_error:
        return 1
    echoed = _ECHOED_EXIT.search(result.text.rstrip())
    return int(echoed.group(1)) if echoed else 0


def normalise_text(text: str) -> str:
    """Markdown emphasis and code marks gone, lower case, whitespace
    collapsed."""
    return " ".join(re.sub(r"[*_`]", "", text).lower().split())
