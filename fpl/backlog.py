"""docs/backlog.md as data: list rows by number, change a Status cell, check
every Status against the documented vocabulary.

A row's number is its 1-based position in the `## Rows` table. Rows are
appended and never deleted, so the number is stable. `status` replaces the
whole file, so it belongs to a triage session, never to a gameweek cycle,
whose agents append with `>>`.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from fpl import corrections

DEFAULT_FILE = Path("docs/backlog.md")
OPEN = "open"
KINDS = ("CODE", "TOOL", "WORKFLOW", "DATA")
HEADER = ("row", "gw", "date", "agent", "kind", "status", "finding", "evidence")

_ROWS_HEADING = re.compile(r"^## Rows[ \t]*$")
_SEPARATOR = re.compile(r"^\|(?:-+\|)+$")
_SHA = r"[0-9a-f]{7,40}"
_NOTE = r"(?: \([^()]*\))?"
_TARGET = rf"(?:C\d+|row \d+|{_SHA})"
_SHIPPED = re.compile(rf"^shipped {_SHA}{_NOTE}(?:; {_SHA}{_NOTE})*$")
_SUPERSEDED = re.compile(rf"^superseded by {_TARGET}{_NOTE}(?: and {_TARGET}{_NOTE})*$")
_REJECTED = re.compile(r"^rejected: \S.*$")
_NOTE_TEXT = re.compile(r" \([^()]*\)")
_SHA_TOKEN = re.compile(rf"(?:^shipped |; |^superseded by | and )({_SHA})\b")
_ROW_TOKEN = re.compile(r"(?:^superseded by | and )row (\d+)\b")
_C_TOKEN = re.compile(r"(?:^superseded by | and )C(\d+)\b")

GRAMMAR = ("`shipped <sha>[ (<note>)][; <sha>[ (<note>)]]…`, "
           "`superseded by <C<n> | row <n> | sha>[ (<note>)][ and …]`, or `rejected: <reason>`")


class BacklogError(Exception):
    """Refusal with a message for stderr; nothing has been written."""


@dataclass(frozen=True)
class Row:
    number: int
    line: int  # 0-based index into the file's lines
    cells: tuple[str, ...]

    @property
    def status(self) -> str:
        return self.cells[6]

    @property
    def finding(self) -> str:
        return self.cells[4]


@dataclass(frozen=True)
class Ledger:
    lines: tuple[str, ...]  # keepends
    rows: tuple[Row, ...]

    def row(self, number: int) -> Row:
        if not 1 <= number <= len(self.rows):
            raise BacklogError(f"no row {number} (the table has {len(self.rows)})")
        return self.rows[number - 1]


def parse(text: str) -> Ledger:
    if "\r" in text:
        raise BacklogError("the file has carriage returns (CRLF line endings?); convert it to LF first")
    lines = tuple(text.splitlines(keepends=True))
    start = next((i for i, line in enumerate(lines) if _ROWS_HEADING.match(line.rstrip("\n"))), None)
    if start is None:
        raise BacklogError("no `## Rows` heading")
    body = [(i, lines[i].rstrip("\n")) for i in range(start + 1, len(lines))]
    body = [(i, line) for i, line in body if line.strip()]
    if len(body) < 2 or not body[0][1].startswith("| GW |") or not _SEPARATOR.match(body[1][1]):
        raise BacklogError("the `## Rows` table has no header and separator")
    rows = []
    for i, line in body[2:]:
        cells = _cells(line)
        if cells is None:
            raise BacklogError(f"malformed row at line {i + 1}: {line}")
        rows.append(Row(len(rows) + 1, i, cells))
    if lines and not lines[-1].endswith("\n"):
        raise BacklogError(f"no trailing newline after line {len(lines)}: {lines[-1]}")
    return Ledger(lines, tuple(rows))


def _cells(line: str) -> tuple[str, ...] | None:
    if not (line.startswith("|") and line.endswith("|")):
        return None
    cells = tuple(cell.strip() for cell in line[1:-1].split("|"))
    return cells if len(cells) == 7 else None


def status_errors(status: str, ledger: Ledger, number: int, repo: Path, retro_root: Path) -> list[str]:
    """Why `status` may not stand in row `number`; empty when it may."""
    if "|" in status or status.splitlines() != [status] or not status.isprintable():
        return ["a status may not contain |, a tab, a line break or another unprintable character"]
    if status == OPEN:
        return []
    if not (_SHIPPED.match(status) or _SUPERSEDED.match(status) or _REJECTED.match(status)):
        return [f"status {status!r} is not one of {GRAMMAR}"]
    errors = []
    targets = _NOTE_TEXT.sub("", status)  # a note may say "row 3 and C9" without naming a target
    for sha in _SHA_TOKEN.findall(targets):
        full = _resolve_commit(repo, sha)
        if full is None:
            errors.append(f"{sha} is not a commit, or the prefix is ambiguous")
        elif not _is_ancestor(repo, full):
            errors.append(f"{sha} is not on the current branch (not an ancestor of HEAD)")
    for target in map(int, _ROW_TOKEN.findall(targets)):
        if target == number:
            errors.append(f"row {number} cannot be superseded by itself")
        elif not 1 <= target <= len(ledger.rows):
            errors.append(f"no row {target} (the table has {len(ledger.rows)})")
    known = _defined_corrections(retro_root)
    errors += [f"C{n} is not defined in {retro_root}/gw*.md"
               for n in map(int, _C_TOKEN.findall(targets)) if n not in known]
    return errors


def _resolve_commit(repo: Path, sha: str) -> str | None:
    out = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"],
                         capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def _is_ancestor(repo: Path, sha: str) -> bool:
    return subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", sha, "HEAD"],
                          capture_output=True).returncode == 0


def _defined_corrections(retro_root: Path) -> set[int]:
    found: set[int] = set()
    for path in sorted(retro_root.glob("gw*.md")):
        section = corrections.corrections_section(path.read_text(encoding="utf-8"))
        found |= {row.number for row in corrections.parse_status_rows(section)}
        found |= {rule.number for rule in corrections.parse_rules(section)}
    return found


def _validate(ledger: Ledger, numbers: list[int], status: str, expects: list[str],
              repo: Path, retro_root: Path) -> None:
    if len(set(numbers)) != len(numbers):
        raise BacklogError(f"duplicate row number in {','.join(map(str, numbers))}")
    if any(not expect.strip() for expect in expects):
        raise BacklogError("an --expect value is blank; give text from the row's finding")
    if len(expects) != len(numbers):
        raise BacklogError(f"{len(numbers)} row(s) but {len(expects)} --expect value(s); give one per row")
    errors = []
    for number, expect in zip(numbers, expects):
        row = ledger.row(number)
        if row.status != OPEN:
            errors.append(f"row {number} is not open (status: {row.status})")
        if expect not in row.finding:
            errors.append(f"row {number}: --expect {expect!r} is not in its finding: {row.finding}")
        errors += [f"row {number}: {e}" for e in status_errors(status, ledger, number, repo, retro_root)]
    if errors:
        raise BacklogError("\n".join(dict.fromkeys(errors)))


def set_status(path: Path, numbers: list[int], status: str, expects: list[str],
               repo: Path, retro_root: Path) -> list[Row]:
    """Rewrites only the Status cell of each row, all of them or none."""
    original = path.read_bytes()
    ledger = parse(original.decode("utf-8"))
    _validate(ledger, numbers, status, expects, repo, retro_root)
    lines = list(ledger.lines)
    for number in numbers:
        row = ledger.row(number)
        line = lines[row.line]
        cut = line.rstrip("\n")[:-1].rstrip(" ").rfind("|")
        lines[row.line] = f"{line[:cut]}| {status} |\n"
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".backlog-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write("".join(lines).encode("utf-8"))
        os.chmod(tmp, path.stat().st_mode & 0o777)
        # A `>>` landing between this read and the replace below would still be
        # lost; the window is the two calls, which is why the command is triage-only.
        if path.read_bytes() != original:
            raise BacklogError(f"{path} changed while the edit was prepared (an append?); nothing written, run again")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return [ledger.row(n) for n in numbers]


def check(ledger: Ledger, repo: Path, retro_root: Path) -> list[str]:
    return [f"row {row.number}: {e}" for row in ledger.rows
            for e in status_errors(row.status, ledger, row.number, repo, retro_root)]


def add_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("backlog", help="list backlog rows, set a row's status, check every status (triage only)")
    p.add_argument("--file", type=Path, default=DEFAULT_FILE, help=f"backlog file (default: {DEFAULT_FILE})")
    p.add_argument("--retro-root", type=Path, help="retro directory for C<n> checks (default: data/retro under the repo root)")
    cmds = p.add_subparsers(dest="backlog_cmd", required=True)
    ls = cmds.add_parser("list", help="TSV of rows, row number first")
    ls.add_argument("--status", choices=("open", "closed", "all"), default="open")
    ls.add_argument("--kind", choices=KINDS)
    st = cmds.add_parser("status", help="change the Status cell of open rows")
    st.add_argument("rows", help="row number, or several joined by commas")
    st.add_argument("status", help=GRAMMAR)
    st.add_argument("--expect", action="append", default=[], required=True,
                    help="text that must appear in the row's finding; one per row, in order")
    cmds.add_parser("check", help="every row parses and every status fits the vocabulary")


def run(args: argparse.Namespace) -> int:
    path: Path = args.file
    try:
        repo = _repo_root(path)
        retro_root = args.retro_root or repo / "data" / "retro"
        if args.backlog_cmd == "status":
            numbers = _row_numbers(args.rows)
            for row in set_status(path, numbers, args.status, args.expect, repo, retro_root):
                print(f"row {row.number}: {row.status} -> {args.status}")
            return 0
        ledger = parse(path.read_bytes().decode("utf-8"))
        if args.backlog_cmd == "list":
            print("\t".join(HEADER))
            for row in ledger.rows:
                if _wanted(row, args.status, args.kind):
                    gw, date, agent, kind, finding, evidence, status = row.cells
                    print("\t".join((str(row.number), gw, date, agent, kind, status, finding, evidence)))
            return 0
        errors = check(ledger, repo, retro_root)
        for e in errors:
            print(e, file=sys.stderr)
        print(f"{len(ledger.rows)} rows, {len(errors)} status error(s)")
        return 1 if errors else 0
    except BacklogError as e:
        print(f"backlog: {e}", file=sys.stderr)
        return 1


def _wanted(row: Row, status: str, kind: str | None) -> bool:
    if kind and row.cells[3] != kind:
        return False
    return status == "all" or (row.status == OPEN) == (status == "open")


def _row_numbers(text: str) -> list[int]:
    try:
        return [int(part) for part in text.split(",")]
    except ValueError:
        raise BacklogError(f"rows must be numbers joined by commas, got {text!r}") from None


def _repo_root(path: Path) -> Path:
    if not path.is_file():
        raise BacklogError(f"no backlog file at {path}")
    out = subprocess.run(["git", "-C", str(path.resolve().parent), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise BacklogError(f"{path} is not inside a git repository")
    return Path(out.stdout.strip())
