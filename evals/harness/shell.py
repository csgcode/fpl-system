"""Readers over the Bash commands an agent ran.

They work on command text alone, so they apply equally to a recorded
transcript and a live run. Heredoc bodies are data, not commands: every
reader looks only at the command lines around them.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass

from evals.harness.transcript import ToolCall, ToolResult, Transcript



class _Unknown:
    def __repr__(self) -> str:
        return "UNKNOWN"


UNKNOWN = _Unknown()
"""A file the agent changed in a way the transcript cannot reconstruct."""

_FPL = re.compile(r"(?:uv\s+run\s+)?python3?\s+-m\s+fpl\b([^;&|\n]*)")
_REDIRECT = re.compile(r"(?<![<>])(?:\d|&)?(>>?)(?!&)\s*([^\s;&|<>()]+)")
_TEE = re.compile(r"\btee\s+(?:-\w+\s+)*([^\s;&|<>()]+)")
_HEREDOC = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
# Echoed exit statuses come in many spellings ("EXIT 1", "EXIT auth-check 1",
# "summaries exit code: 2"); a line naming exit and ending in a non-zero
# number is a failure.
_FAILED = re.compile(
    r"(?m)^error:|\bEXIT [1-9]|\bExit code [1-9]"
    r"|(?i:\bexit\b[\w :-]{0,30}?\b[1-9]\d*\s*$)")
_IGNORED_TARGETS = ("/dev/null",)


@dataclass(frozen=True)
class FplInvocation:
    """One `python -m fpl …` run; `args` starts at the subcommand."""

    args: tuple[str, ...]

    @property
    def subcommand(self) -> str:
        return self.args[0] if self.args else ""

    @property
    def is_help(self) -> bool:
        return "--help" in self.args or "-h" in self.args

    def has(self, flag: str) -> bool:
        return flag in self.args

    def option(self, name: str) -> str | None:
        for index, token in enumerate(self.args):
            if token == name and index + 1 < len(self.args):
                return self.args[index + 1]
            if token.startswith(f"{name}="):
                return token.split("=", 1)[1]
        return None


@dataclass(frozen=True)
class _Heredoc:
    header: str
    body: str


def command_lines(command: str) -> str:
    """The command with heredoc bodies removed."""
    return "\n".join(line for line in _scan(command)[0])


def executable_text(command: str) -> str:
    """The command plus every heredoc body that is run as code. A body fed
    to `cat` is file content, not something the shell executes."""
    outer, heredocs = _scan(command)
    bodies = [h.body for h in heredocs if not re.match(r"\s*cat\b", h.header)]
    return "\n".join([*outer, *bodies])


def fpl_invocations(command: str) -> list[FplInvocation]:
    invocations = []
    for match in _FPL.finditer(command_lines(command)):
        tokens = _tokens(match.group(1))
        tokens = _until_redirect(tokens)
        tokens = _skip_global_options(tokens)
        if tokens:
            invocations.append(FplInvocation(tuple(tokens)))
    return invocations


def call_fpl_invocations(call: ToolCall) -> list[FplInvocation]:
    if call.name != "Bash":
        return []
    return fpl_invocations(str(call.input.get("command", "")))


def redirect_targets(command: str) -> list[str]:
    outer = command_lines(command)
    targets = [target for _, target in _redirects(outer)]
    targets += [_unquote(m.group(1)) for m in _TEE.finditer(outer)]
    return [t for t in targets if t not in _IGNORED_TARGETS]


def call_failed(result: ToolResult | None) -> bool:
    if result is None:
        return False
    return result.is_error or bool(_FAILED.search(result.text))


def agent_written_files(transcript: Transcript, root: str) -> dict[str, str | _Unknown]:
    """Files the agent wrote, by path relative to `root`; last write wins. An
    Edit leaves the content unknowable from the transcript alone."""
    written: dict[str, str | _Unknown] = {}
    for call in transcript.calls:
        if call.name == "Write":
            written[normalise(call.input["file_path"], root)] = call.input["content"]
        elif call.name in ("Edit", "MultiEdit", "NotebookEdit"):
            written[normalise(call.input.get("file_path", ""), root)] = UNKNOWN
        elif call.name == "Bash":
            for heredoc in _scan(str(call.input.get("command", "")))[1]:
                for path in _heredoc_targets(heredoc.header):
                    written[normalise(path, root)] = heredoc.body
    return written


def appended_text(command: str, path: str) -> str | None:
    """The heredoc bodies `cat` appends (`>>`) to `path` — relative, or the
    tail of an absolute target — in command order; None when nothing is."""
    bodies = []
    for heredoc in _scan(command)[1]:
        if not re.search(r"\bcat\b", heredoc.header):
            continue
        targets = [t for op, t in _redirects(heredoc.header) if op == ">>"]
        if any(t == path or t.endswith(f"/{path}") for t in targets):
            bodies.append(heredoc.body)
    return "".join(bodies) if bodies else None


def normalise(path: str, root: str) -> str:
    path = _unquote(path)
    prefix = root.rstrip("/") + "/"
    if path.startswith(prefix):
        path = path[len(prefix):]
    while path.startswith("./"):
        path = path[2:]
    return path


def write_paths(call: ToolCall, root: str) -> list[str]:
    """Every path a single call writes: Write/Edit targets, shell redirects and
    tee targets, relative to `root`."""
    if call.name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        return [normalise(str(call.input.get("file_path", "")), root)]
    if call.name == "Bash":
        command = str(call.input.get("command", ""))
        return [normalise(target, root) for target in redirect_targets(command)]
    return []


def _scan(command: str) -> tuple[list[str], list[_Heredoc]]:
    outer: list[str] = []
    heredocs: list[_Heredoc] = []
    lines = command.split("\n")
    index = 0
    while index < len(lines):
        line = lines[index]
        outer.append(line)
        index += 1
        for match in _HEREDOC.finditer(line):
            strip_tabs, delimiter = match.group(1) == "-", match.group(3)
            body: list[str] = []
            while index < len(lines):
                candidate = lines[index].lstrip("\t") if strip_tabs else lines[index]
                index += 1
                if candidate == delimiter:
                    break
                body.append(lines[index - 1])
            heredocs.append(_Heredoc(line, "".join(f"{b}\n" for b in body)))
    return outer, heredocs


def _redirects(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), _unquote(m.group(2))) for m in _REDIRECT.finditer(text)]


def _heredoc_targets(header: str) -> list[str]:
    if not re.match(r"\s*cat\b", header):
        return []
    return [target for op, target in _redirects(header)
            if op == ">" and target not in _IGNORED_TARGETS]


def _tokens(raw: str) -> list[str]:
    try:
        return shlex.split(raw)
    except ValueError:
        return raw.split()


def _until_redirect(tokens: list[str]) -> list[str]:
    for index, token in enumerate(tokens):
        if ">" in token or "<" in token:
            return tokens[:index]
    return tokens


def _skip_global_options(tokens: list[str]) -> list[str]:
    index = 0
    while index < len(tokens) and tokens[index].startswith("--data-root"):
        index += 1 if "=" in tokens[index] else 2
    return tokens[index:]


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value
