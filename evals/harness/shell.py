"""Readers over the Bash commands an agent ran.

They work on command text alone, so they apply equally to a recorded
transcript and a live run. Heredoc bodies are data, not commands: every
reader looks only at the command lines around them.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

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
    segment: str = ""
    """The simple command on the header line that receives the heredoc: the
    text between the separators (`&&`, `||`, `;`, `|`) around its `<<`."""


def command_lines(command: str) -> str:
    """The command with heredoc bodies removed."""
    return "\n".join(line for line in _scan(command)[0])


def executable_text(command: str) -> str:
    """The command plus every heredoc body that is run as code. A body fed
    to `cat` is file content, not something the shell executes."""
    outer, heredocs = _scan(command)
    bodies = [h.body for h in heredocs if not re.match(r"\s*cat\b", h.segment)]
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


def agent_written_files(transcript: Transcript, root: str, *,
                        apply_edits: bool = False) -> dict[str, str | _Unknown]:
    """Files the agent wrote, by path relative to `root`; last write wins. An
    Edit leaves the content unknowable from the transcript alone — unless
    `apply_edits` replays it on content already known, where its old string
    must occur exactly once (every occurrence, with `replace_all`)."""
    written: dict[str, str | _Unknown] = {}
    for call in transcript.calls:
        if call.name == "Write":
            written[normalise(call.input["file_path"], root)] = call.input["content"]
        elif call.name == "Edit" and apply_edits:
            path = normalise(call.input.get("file_path", ""), root)
            written[path] = _replayed(written.get(path), call.input)
        elif call.name in ("Edit", "MultiEdit", "NotebookEdit"):
            written[normalise(call.input.get("file_path", ""), root)] = UNKNOWN
        elif call.name == "Bash":
            for heredoc in _scan(str(call.input.get("command", "")))[1]:
                for path in _heredoc_targets(heredoc.segment):
                    written[normalise(path, root)] = heredoc.body
    return written


def _replayed(content: str | _Unknown | None, edit: Mapping[str, Any]) -> str | _Unknown:
    if not isinstance(content, str):
        return UNKNOWN
    old, new = str(edit.get("old_string", "")), str(edit.get("new_string", ""))
    if edit.get("replace_all"):
        return content.replace(old, new) if old and old in content else UNKNOWN
    if not old or content.count(old) != 1:
        return UNKNOWN
    return content.replace(old, new, 1)


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
    """Every path a single call writes, relative to `root`: Write/Edit
    targets; shell redirects and tee targets outside quotes; `rm` and `mv`
    operands; and python `open(path, 'w'|'a')`. A leading `cd DIR` and
    `VAR=value` assignments in the same command are resolved."""
    if call.name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        return [normalise(str(call.input.get("file_path", "")), root)]
    if call.name != "Bash":
        return []
    command = str(call.input.get("command", ""))
    outer = command_lines(command)
    targets = [t for t in redirect_targets(command) if not _inside_quotes(outer, t)]
    targets += _removed_or_moved(outer) + _python_writes(executable_text(command))
    variables = _assignments(outer)
    cwd = _cd_target(outer, variables)
    return [normalise(_resolved(t, variables, cwd), root) for t in targets]


_QUOTED_SPAN = re.compile(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"")
_ASSIGNMENT = re.compile(
    r"(?:^|[\s;&|(])(?:export\s+)?([A-Za-z_]\w*)=(\"[^\"]*\"|'[^']*'|[^\s;&|]+)")
_CD = re.compile(r"(?:^|&&|;|\n)\s*cd\s+(\"[^\"]+\"|'[^']+'|[^\s;&|]+)\s*(?:&&|;|\n|$)")
_VARIABLE = re.compile(r"\$\{?([A-Za-z_]\w*)\}?")
_SEPARATORS = re.compile(r"&&|\|\||;|\||\n")
_PY_OPEN = re.compile(
    r"""open\(\s*(?:(['"])([^'"]+)\1|([A-Za-z_]\w*))\s*,\s*(?:mode\s*=\s*)?['"][wax]""")
_PY_STRING = re.compile(r"""\b([A-Za-z_]\w*)\s*=\s*(['"])([^'"]+)\2""")


def _inside_quotes(outer: str, target: str) -> bool:
    """True when every redirect naming `target` sits inside a quoted span."""
    spans = [m.span() for m in _QUOTED_SPAN.finditer(outer)]
    found = [m for m in _REDIRECT.finditer(outer) if _unquote(m.group(2)) == target]
    found += [m for m in _TEE.finditer(outer) if _unquote(m.group(1)) == target]
    return bool(found) and all(any(a <= m.start() < b for a, b in spans) for m in found)


def _assignments(outer: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for match in _ASSIGNMENT.finditer(outer):
        values[match.group(1)] = _expand(_unquote(match.group(2)), values)
    return values


def _expand(value: str, variables: Mapping[str, str]) -> str:
    return _VARIABLE.sub(lambda m: variables.get(m.group(1), m.group(0)), value)


def _cd_target(outer: str, variables: Mapping[str, str]) -> str | None:
    match = _CD.search(outer)
    return _expand(_unquote(match.group(1)), variables) if match else None


def _resolved(target: str, variables: Mapping[str, str], cwd: str | None) -> str:
    path = _expand(target, variables)
    if cwd and not path.startswith(("/", "~", "$")):
        return f"{cwd.rstrip('/')}/{path}"
    return path


def _removed_or_moved(outer: str) -> list[str]:
    operands = []
    for segment in _SEPARATORS.split(outer):
        tokens = _tokens(segment)
        if tokens and tokens[0] in ("rm", "mv"):
            operands += [t for t in tokens[1:] if not t.startswith("-")]
    return operands


def _python_writes(code: str) -> list[str]:
    strings = {m.group(1): m.group(3) for m in _PY_STRING.finditer(code)}
    paths = []
    for match in _PY_OPEN.finditer(code):
        path = match.group(2) or strings.get(match.group(3) or "")
        if path:
            paths.append(path)
    return paths


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
            heredocs.append(_Heredoc(line, "".join(f"{b}\n" for b in body),
                                     _segment(line, match.start(), match.end())))
    return outer, heredocs


def _segment(line: str, start: int, end: int) -> str:
    before = _SEPARATORS.split(line[:start])[-1]
    after = _SEPARATORS.split(line[end:])[0]
    return before + line[start:end] + after


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
