"""Retro corrections, read from data/retro/gw*.md.

A retro's `## Corrections` section holds a status table (`| C<n> | agents |
status | evidence |`) carried forward from every earlier retro, then the
rules it issues this round as bold paragraphs (`**C<n> — <agents> …`). A
correction's status comes from the latest retro's table; a rule issued in the
latest retro has no row yet and counts as new. Its text comes from the newest
retro that defines it, so a rule revised in place wins.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_RETRO_FILE = re.compile(r"gw(\d+)\.md")
_SECTION = re.compile(r"(?m)^## Corrections[ \t]*$")
_NEXT_HEADER = re.compile(r"(?m)^## ")
_STATUS_ROW = re.compile(r"^\|\s*C(\d+)\s*\|([^|]*)\|([^|]*)\|")
_RULE = re.compile(r"^\*\*C(\d+) — ")
_AGENT_CODE = re.compile(r"^(?:A\d+|CODE)$")
_AGENT_TOKEN = re.compile(r"\b(A\d+|CODE)\b")
NEW = "new"


@dataclass(frozen=True)
class StatusRow:
    number: int
    agents: tuple[str, ...]
    status: str
    line: str


@dataclass(frozen=True)
class Rule:
    number: int
    agents: tuple[str, ...]
    text: str
    source: str


@dataclass(frozen=True)
class Digest:
    """`latest` is None when no retro precedes the round. `active` holds the
    rule text of every correction whose status is not closed, new ones
    included; `missing` the status rows no retro defines."""

    latest: str | None
    sources: tuple[str, ...]
    rows: tuple[StatusRow, ...]
    new: tuple[Rule, ...]
    active: tuple[Rule, ...]
    missing: tuple[int, ...]


@dataclass(frozen=True)
class AgentCorrection:
    rule: Rule
    status: str


@dataclass(frozen=True)
class AgentView:
    agent: str
    latest: str | None
    active: tuple[AgentCorrection, ...]
    retired: tuple[StatusRow, ...]


def corrections_section(text: str) -> str:
    """`## Corrections` up to the next `## ` header, or the end of the file."""
    start = _SECTION.search(text)
    if start is None:
        return ""
    rest = text[start.start():]
    end = _NEXT_HEADER.search(rest, len("## Corrections"))
    return rest[:end.start()] if end else rest


def parse_status_rows(section: str) -> tuple[StatusRow, ...]:
    rows = []
    for line in section.splitlines():
        match = _STATUS_ROW.match(line)
        if match:
            rows.append(StatusRow(int(match[1]), _split_agents(match[2]),
                                  match[3].strip(), line.rstrip()))
    return tuple(rows)


def parse_rules(section: str, source: str = "") -> tuple[Rule, ...]:
    """Each rule is its paragraph: from `**C<n> — ` to the next blank line."""
    rules = []
    lines = section.splitlines()
    index = 0
    while index < len(lines):
        match = _RULE.match(lines[index])
        if not match:
            index += 1
            continue
        paragraph = []
        while index < len(lines) and lines[index].strip():
            paragraph.append(lines[index].rstrip())
            index += 1
        text = "\n".join(paragraph)
        rules.append(Rule(int(match[1]), _heading_agents(text), text, source))
    return tuple(rules)


def is_closed(status: str) -> bool:
    return status.startswith(("retired", "revised"))


def retro_files(root: Path, *, before_round: int) -> list[Path]:
    """gwK.md files with K < before_round, oldest first (numeric order)."""
    if not root.is_dir():
        return []
    found = [(int(m[1]), path) for path in root.iterdir()
             if (m := _RETRO_FILE.fullmatch(path.name)) and int(m[1]) < before_round]
    return [path for _, path in sorted(found)]


def build_digest(root: Path, *, before_round: int) -> Digest:
    files = retro_files(root, before_round=before_round)
    if not files:
        return Digest(None, (), (), (), (), ())
    texts = {path.name: corrections_section(path.read_text(encoding="utf-8"))
             for path in files}
    latest = files[-1].name
    rules: dict[int, Rule] = {}
    for name, section in texts.items():
        for rule in parse_rules(section, name):
            rules[rule.number] = rule
    rows = parse_status_rows(texts[latest])
    tabled = {row.number for row in rows}
    new = tuple(rule for rule in parse_rules(texts[latest], latest)
                if rule.number not in tabled)
    open_numbers = {row.number for row in rows if not is_closed(row.status)}
    open_numbers |= {rule.number for rule in new}
    return Digest(
        latest=latest,
        sources=tuple(path.name for path in files),
        rows=rows,
        new=new,
        active=tuple(rules[n] for n in sorted(open_numbers) if n in rules),
        missing=tuple(sorted(row.number for row in rows if row.number not in rules)),
    )


def agent_corrections(root: Path, *, gw: int, agent: str) -> AgentView:
    """The corrections addressed to `agent` that bind at gameweek `gw`: every
    retro before GW `gw` counts, so the latest is the one written this cycle."""
    if not _AGENT_CODE.match(agent):
        raise ValueError(f"invalid agent code {agent!r}: expected A<n> or CODE")
    digest = build_digest(root, before_round=gw)
    statuses = {row.number: row.status for row in digest.rows}
    statuses |= {rule.number: NEW for rule in digest.new}
    row_agents = {row.number: row.agents for row in digest.rows}
    active = tuple(
        AgentCorrection(rule, statuses[rule.number]) for rule in digest.active
        if agent in row_agents.get(rule.number, rule.agents)
    )
    retired = tuple(row for row in digest.rows if agent in row.agents and is_closed(row.status))
    return AgentView(agent, digest.latest, active, retired)


def _split_agents(cell: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in cell.split(",") if part.strip())


def _heading_agents(text: str) -> tuple[str, ...]:
    """The agent codes between `— ` and the first `(` or `:` of a rule."""
    head = re.split(r"[(:]", text.split(" — ", 1)[1], maxsplit=1)[0]
    return tuple(_AGENT_TOKEN.findall(head))
