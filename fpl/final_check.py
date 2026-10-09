"""The mechanical carry rules from a squad proposal into final.md.

The finalizer makes no decisions of its own: final.md's STATE block is the
proposal's, and its suggestions ledger is the proposal's verbatim. The
proposal in turn must carry every suggestion the previous final.md recorded,
with closed rows unchanged. These are text comparisons, so they live here
rather than in an agent's judgement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from fpl.state import DecisionState, parse_state

CLOSED = frozenset({"followed", "rejected", "expired", "withdrawn"})
STATE_CHIP_KEYS = ("chip", "chips_used", "chip_plan")

_MARKER = re.compile(r"(?m)^Read data/suggestions\.md through S(\d+)\s*$")
_ROW = re.compile(r"^\|\s*(S\d+)\s*\|")
_NO_SUGGESTIONS = "No data/suggestions.md"
_YAML_BLOCK = re.compile(r"```yaml\n(.*?)```", re.DOTALL)


@dataclass(frozen=True)
class Finding:
    rule: str
    message: str


@dataclass(frozen=True)
class Ledger:
    marker: str
    max_s: int
    rows: tuple[tuple[str, str], ...]
    """(S#, verbatim line) in file order."""

    def row(self, s_id: str) -> str | None:
        return next((line for sid, line in self.rows if sid == s_id), None)


def parse_ledger(text: str) -> Ledger | None:
    """The marker line, then the `| S<n> |` rows of the table that follows it.
    Prose after the table is not part of the ledger."""
    matches = list(_MARKER.finditer(text))
    if not matches:
        return None
    marker = matches[-1]
    rows: list[tuple[str, str]] = []
    in_table = False
    for line in text[marker.end():].splitlines():
        if line.startswith("|"):
            in_table = True
            row = _ROW.match(line)
            if row:
                rows.append((row.group(1), line.rstrip()))
            continue
        if in_table or line.strip():
            break
    return Ledger(marker.group(0).rstrip(), int(marker.group(1)), tuple(rows))


def has_no_suggestions_line(text: str) -> bool:
    return any(line.startswith(_NO_SUGGESTIONS) for line in text.splitlines())


def check_proposal(
    proposal: str, *, gw: int, previous_final: str | None, suggestions_exists: bool
) -> list[Finding]:
    findings: list[Finding] = []
    state, error = _state(proposal, gw)
    if error is not None:
        findings.append(Finding("P1", error))
    elif state is not None and state.picks is None:
        findings.append(Finding("P1", "the STATE block has no 'picks:' section"))

    current = parse_ledger(proposal)
    if suggestions_exists and current is None:
        findings.append(Finding(
            "P2", "data/suggestions.md exists but the proposal has no "
                  "'Read data/suggestions.md through S<n>' line"))
    if not suggestions_exists and not has_no_suggestions_line(proposal):
        findings.append(Finding(
            "P2", "data/suggestions.md is absent but the proposal lacks the "
                  "'No data/suggestions.md' line"))

    prior = parse_ledger(previous_final) if previous_final is not None else None
    if prior is not None:
        problems = _carry_problems(prior, current)
        if problems:
            findings.append(Finding("P3", "; ".join(problems)))
    return findings


def check_final(final: str, proposal: str, *, gw: int) -> list[Finding]:
    findings: list[Finding] = []
    final_state, error = _state(final, gw)
    if error is not None:
        findings.append(Finding("F1", error))
    else:
        trailing = _after_state(final)
        if trailing.strip():
            findings.append(Finding(
                "F1", f"text after the STATE block: {trailing.strip().splitlines()[0]!r}"))

    missing = [key for key in STATE_CHIP_KEYS if not _has_key_line(final, key)]
    if missing:
        findings.append(Finding(
            "F2", "the STATE block lacks " + ", ".join(f"'{k}:'" for k in missing)))

    proposal_state, _ = _state(proposal, gw)
    if final_state is not None and proposal_state is not None and final_state != proposal_state:
        fields = _differing_fields(final_state, proposal_state)
        findings.append(Finding(
            "F3", "STATE differs from the proposal's in: " + ", ".join(fields)))

    problems = _ledger_copy_problems(parse_ledger(final), parse_ledger(proposal))
    if has_no_suggestions_line(proposal) and not has_no_suggestions_line(final):
        problems.append("the proposal's 'No data/suggestions.md' line is missing")
    if problems:
        findings.append(Finding("F4", "; ".join(problems)))
    return findings


def _state(text: str, gw: int) -> tuple[DecisionState | None, str | None]:
    try:
        return parse_state(text, expected_gw=gw), None
    except ValueError as exc:
        return None, str(exc).splitlines()[0] if str(exc) else type(exc).__name__


def _after_state(text: str) -> str:
    blocks = list(_YAML_BLOCK.finditer(text))
    return text[blocks[-1].end():] if blocks else text


def _has_key_line(text: str, key: str) -> bool:
    blocks = _YAML_BLOCK.findall(text)
    return bool(blocks) and re.search(rf"(?m)^{key}:", blocks[-1]) is not None


def _differing_fields(a: DecisionState, b: DecisionState) -> list[str]:
    left, right = a.model_dump(), b.model_dump()
    return [name for name in left if left[name] != right[name]]


def _status(line: str) -> str:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return cells[2].lower() if len(cells) > 2 else ""


def _carry_problems(prior: Ledger, current: Ledger | None) -> list[str]:
    if current is None:
        return [f"the previous ledger has {', '.join(s for s, _ in prior.rows)} "
                f"but the proposal has no ledger"] if prior.rows else []
    problems = []
    for s_id, line in prior.rows:
        carried = current.row(s_id)
        if carried is None:
            problems.append(f"{s_id} is in the previous ledger but not the proposal's")
        elif _status(line) in CLOSED and carried != line:
            problems.append(f"{s_id} is closed ({_status(line)}) but its row changed")
    return problems


def _ledger_copy_problems(final: Ledger | None, proposal: Ledger | None) -> list[str]:
    if proposal is None:
        return ["the final has a ledger the proposal does not"] if final else []
    if final is None:
        return ["the proposal's ledger is missing"]
    problems = []
    if final.marker != proposal.marker:
        problems.append(f"marker {final.marker!r} != the proposal's {proposal.marker!r}")
    if final.rows != proposal.rows:
        final_ids = [s for s, _ in final.rows]
        proposal_ids = [s for s, _ in proposal.rows]
        added = [s for s in final_ids if s not in proposal_ids]
        dropped = [s for s in proposal_ids if s not in final_ids]
        changed = [s for s in final_ids
                   if s in proposal_ids and final.row(s) != proposal.row(s)]
        if added:
            problems.append(f"rows not in the proposal: {', '.join(added)}")
        if dropped:
            problems.append(f"rows dropped: {', '.join(dropped)}")
        if changed:
            problems.append(f"rows not verbatim: {', '.join(changed)}")
        if not (added or dropped or changed):
            problems.append("rows reordered")
    return problems
