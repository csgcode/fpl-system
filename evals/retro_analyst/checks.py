"""Retro-analyst graders R1–R21: pure functions over a run.

The retro analyst runs calibrate, reads final.md and the prior corrections,
fetches actuals for the misses it attributes, writes data/retro/gwM.md and
mirrors its CODE corrections and gap lines into docs/backlog.md. The checks
compare what it wrote against the truth ledger, calibrate's own stdout and the
prior retros; a few read the command lines and the return text.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from evals.harness.checks import Check, CheckResult, budget_overruns, return_budgets
from evals.harness.shell import (
    appended_text,
    call_fpl_invocations,
    command_lines,
    executable_text,
    write_paths,
)
from evals.harness.transcript import ToolCall, Transcript, tool_turns
from evals.harness.workspace import Manifest
from fpl.calibrate import CalibrationReport, squad_misses
from fpl.corrections import (
    StatusRow,
    corrections_section,
    is_closed,
    parse_rules,
    parse_status_rows,
)
from fpl.state import parse_state

MARK_CORRECTIONS_CLI = "uv run python -m fpl corrections"
MARK_EXECUTION = "EXECUTION —"
MARK_PREMISE = "Premise:"
MARK_POOL_ROWS = "then at most 5 pool rows"
MARK_RETIRE_C16 = "retire C16 the same way"
SPEC_MARKERS = (MARK_CORRECTIONS_CLI, MARK_EXECUTION, MARK_PREMISE, MARK_POOL_ROWS,
                MARK_RETIRE_C16)

CLASSES = frozenset({"MINUTES", "VARIANCE", "MODEL", "INFORMATION", "BENCH-ORDER"})
EXECUTION = "EXECUTION"
ALLOWED_FPL = frozenset({"calibrate", "picks", "entry-history", "actuals", "corrections"})
KINDS = ("CODE", "TOOL", "WORKFLOW", "DATA")
BASE_TURNS = 3
LEDGER_TOLERANCE = 0.0051
MISSES_CAP = 10
POOL_ROWS_CAP = 5
SECTION_CAPS = {"Squad": 3, "Captain and bench": 4, "Findings": 20}
CARRIED_CAP = 8
BACKLOG = "docs/backlog.md"

SPEC_FILES = ("agents/retro-analyst.md", "CLAUDE.md")
# Both spellings of the CLAUDE.md awk check: the GW4 one and the current one.
SHAPE_CHECKS = ("tail -c1 docs/backlog.md | od -An -c",
                "awk '/^## Rows/{p=1} p && NF && !/^\\|.*\\|$/' docs/backlog.md",
                "awk '/^## Rows/{p=1} p && NF && !/^\\|/' docs/backlog.md")
INDEX_GREP = "grep -n '^def \\|^class \\|^[A-Z][A-Z0-9_]* = ' fpl/ep.py"
_EP_SED = re.compile(r"sed\s+-n\s+'\d+,\d+p'\s+fpl/ep\.py")

_HEADER = re.compile(r"^#{1,6} .*$")
_FENCE = re.compile(r"^```")
_N_CLAIM = re.compile(r"\bn\s*(=|≈|~)\s*(\d[\d,]*(?:\.\d+)?)")
_S_ID = re.compile(r"\bS\d{1,2}\b")
_GAP_LINE = re.compile(r"^(- )?`?gap:`?")
_NEW_HEADER = re.compile(
    r"^\*\*C\d+ — (CODE \(fpl/\w+\.py[^)]*\)|A\d+(, A\d+)* \([a-z-]+(, [a-z-]+)*\)): ")
_EP_TARGET = re.compile(r"^\*\*C\d+ — CODE \(fpl/ep\.py\s+`([A-Za-z_]\w*)`\)")
_DATE = r"\d{4}-\d{2}-\d{2}"
_SEGMENTS = re.compile(r"&&|\|\||;|\||\n")
_FORBIDDEN = (
    (re.compile(r"\bgit\s+(?:-\S+\s+)*(commit|push|checkout|reset|restore|stash)\b"), "git {0}"),
    (re.compile(r"\b(curl|wget)\b"), "{0}"),
    (re.compile(r"\brequests\."), "requests."),
    (re.compile(r"--help\b"), "--help"),
    (re.compile(r"--force\b"), "--force"),
)
_EXPLORERS = frozenset({"ls", "find"})
_PERSISTED = re.compile(r"tool-results/")
_LIVE_CLI_FILES = re.compile(
    r"^data/raw/gw{n}/(?:\.meta/|\.archive/|picks-|entry-history-|event-live-|players/)")


@dataclass(frozen=True)
class LiveWorkspace:
    before: Manifest
    after: Manifest


@dataclass(frozen=True)
class RetroRun:
    """`retro` is the gwM.md the run left (None when it wrote none); `ledger`
    the truth calibration ledger; `prior_retros` maps gw1.md… to text for every
    retro before round M; `fielded` the picks recording's (ids, captain,
    vice) when the case knows it."""

    transcript: Transcript
    instructions: str
    root: str
    round: int
    retro: str | None
    ledger: CalibrationReport | None
    final_md: str | None
    prior_retros: Mapping[str, str]
    backlog_appended: str
    fielded: tuple[frozenset[int], int, int] | None = None
    workspace: LiveWorkspace | None = None
    expect_c9_retired: bool = False
    expect_refusal: bool = False
    """calibrate must refuse: the round is not data-checked."""
    null_team: bool = False

    @property
    def gw(self) -> int:
        return self.round + 1

    @property
    def calls(self) -> tuple[ToolCall, ...]:
        return self.transcript.calls

    @property
    def report(self) -> str:
        return self.transcript.final_text

    @property
    def retro_path(self) -> str:
        return f"data/retro/gw{self.round}.md"

    @property
    def outputs(self) -> str:
        return "\n".join(c.result.text for c in self.calls if c.result is not None)

    @property
    def calibrate_stdout(self) -> str | None:
        """From calibrate's header line through its `wrote` line, in the
        first tool result that carries it."""
        header = f"round {self.round} calibration —"
        for call in self.calls:
            text = call.result.text if call.result else ""
            start = text.find(header)
            if start < 0:
                continue
            end = text.find("wrote data/retro/", start)
            if end < 0:
                end = text.find("wrote ", start)
            stop = text.find("\n", end) if end >= 0 else -1
            return text[start:stop if stop >= 0 else len(text)]
        return None


# --- retro text helpers -------------------------------------------------------


def outside_fences(text: str) -> list[str]:
    lines, inside = [], False
    for line in text.splitlines():
        if _FENCE.match(line):
            inside = not inside
            continue
        if not inside:
            lines.append(line)
    return lines


def headers(text: str) -> list[str]:
    return [line.rstrip() for line in outside_fences(text) if _HEADER.match(line)]


def section(text: str, title: str) -> str:
    """The body under `## <title…>` up to the next header outside a fence."""
    body: list[str] = []
    inside, active = False, False
    for line in text.splitlines():
        if _FENCE.match(line):
            inside = not inside
        if not inside and _HEADER.match(line) and not _FENCE.match(line):
            if active:
                break
            active = line.startswith(f"## {title}")
            continue
        if active:
            body.append(line)
    return "\n".join(body)


def fences(text: str) -> list[list[str]]:
    blocks, current = [], None
    for line in text.splitlines():
        if _FENCE.match(line):
            if current is None:
                current = []
            else:
                blocks.append(current)
                current = None
        elif current is not None:
            current.append(line)
    return blocks


def non_blank(lines: Sequence[str]) -> int:
    return sum(1 for line in lines if line.strip())


def expected_headers(round_: int) -> list[str]:
    return [f"# GW{round_} Retro", "## Squad", "## Misses", "## Captain and bench",
            "## Findings", "## Corrections", "## Running calibration stats",
            f"## Carried into GW{round_ + 1}"]


def table_rows(body: str) -> list[list[str]]:
    """Data rows of the first markdown table: header and rule rows dropped."""
    rows = [line for line in body.splitlines() if line.lstrip().startswith("|")]
    cells = [[c.strip() for c in row.strip().strip("|").split("|")] for row in rows]
    return [c for c in cells[1:] if not all(re.fullmatch(r":?-+:?", x) for x in c if x)]


def misses_header(body: str) -> list[str]:
    for line in body.splitlines():
        if line.lstrip().startswith("|"):
            return [c.strip().lower() for c in line.strip().strip("|").split("|")]
    return []


def number(cell: str) -> float | None:
    cleaned = re.sub(r"[*`\s]", "", cell).replace("−", "-").replace("+", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def calibrate_lines(stdout: str) -> list[str]:
    return [line.rstrip() for line in stdout.splitlines()]


def squad_row_lines(stdout: str) -> list[str]:
    lines = calibrate_lines(stdout)
    start = next((i for i, line in enumerate(lines) if line.startswith("squad rows")), None)
    if start is None:
        return []
    rows = []
    for line in lines[start + 1:]:
        if not line.startswith(" "):
            break
        rows.append(line)
    return rows


def is_subsequence(lines: Sequence[str], source: Sequence[str]) -> bool:
    position = 0
    for line in lines:
        while position < len(source) and source[position] != line:
            position += 1
        if position == len(source):
            return False
        position += 1
    return True


def is_contiguous(lines: Sequence[str], source: Sequence[str]) -> bool:
    width = len(lines)
    return any(list(source[i:i + width]) == list(lines) for i in range(len(source) - width + 1))


def max_prior_number(prior_retros: Mapping[str, str]) -> int:
    numbers = [0]
    for text in prior_retros.values():
        part = corrections_section(text)
        numbers += [row.number for row in parse_status_rows(part)]
        numbers += [rule.number for rule in parse_rules(part)]
    return max(numbers)


def latest_prior(prior_retros: Mapping[str, str]) -> str | None:
    if not prior_retros:
        return None
    return max(prior_retros, key=lambda name: int(re.sub(r"\D", "", name) or 0))


def previous_statuses(prior_retros: Mapping[str, str]) -> dict[int, tuple[str, bool]]:
    """C# → (status, is CODE) in the latest prior retro, rules new in it
    counting as active."""
    name = latest_prior(prior_retros)
    if name is None:
        return {}
    part = corrections_section(prior_retros[name])
    statuses = {row.number: (row.status, "CODE" in row.agents)
                for row in parse_status_rows(part)}
    for rule in parse_rules(part):
        statuses.setdefault(rule.number, ("new", "CODE" in rule.agents))
    return statuses


def current_rows(run: RetroRun) -> tuple[StatusRow, ...]:
    return parse_status_rows(corrections_section(run.retro or ""))


def new_rules(run: RetroRun):
    floor = max_prior_number(run.prior_retros)
    return [rule for rule in parse_rules(corrections_section(run.retro or ""))
            if rule.number > floor]


def gap_lines(run: RetroRun) -> list[str]:
    return [line for line in section(run.retro or "", "Findings").splitlines()
            if _GAP_LINE.match(line.strip())]


def expected_backlog(run: RetroRun) -> list[str]:
    """What Call 4 must mirror: new CODE C#s, CODE C#s closed this retro,
    and every gap line."""
    reasons = [f"new CODE C{r.number}" for r in new_rules(run) if "CODE" in r.agents]
    before = previous_statuses(run.prior_retros)
    for row in current_rows(run):
        status, was_code = before.get(row.number, ("", False))
        if (was_code or "CODE" in row.agents) and status and not is_closed(status) \
                and is_closed(row.status):
            reasons.append(f"C{row.number} {row.status.split(' ', 1)[0]}")
    reasons += [f"gap line {i + 1}" for i, _ in enumerate(gap_lines(run))]
    return reasons


def appended_rows(run: RetroRun) -> list[str]:
    return [line for line in run.backlog_appended.splitlines() if line.strip()]


def misses_ids(run: RetroRun) -> list[int]:
    ids = []
    for row in table_rows(section(run.retro or "", "Misses")):
        value = number(row[0]) if row else None
        if value is not None:
            ids.append(int(value))
    return ids


def _segments(text: str) -> list[str]:
    return [s.strip() for s in _SEGMENTS.split(text) if s.strip()]


def _reads_only_spec(call: ToolCall) -> bool:
    if call.name == "Read":
        return str(call.input.get("file_path", "")).endswith(SPEC_FILES)
    if call.name != "Bash":
        return False
    segments = _segments(command_lines(str(call.input.get("command", ""))))
    return bool(segments) and all(
        re.fullmatch(r"(?:cat|head|sed -n '[^']*')\s+\S*(?:agents/retro-analyst\.md|CLAUDE\.md)",
                     segment) for segment in segments)


def counted_turns(run: RetroRun) -> list[tuple[ToolCall, ...]]:
    return [turn for turn in tool_turns(run.transcript)
            if not all(_reads_only_spec(call) for call in turn)]


def _call_text(call: ToolCall) -> str:
    if call.name == "Bash":
        return executable_text(str(call.input.get("command", "")))
    if call.name in ("Read", "Grep", "Glob"):
        return " ".join(str(v) for v in call.input.values())
    return ""


# --- checks -------------------------------------------------------------------


def r1_order(run: RetroRun) -> CheckResult:
    sequence = [(index, inv) for index, call in enumerate(run.calls)
                for inv in call_fpl_invocations(call)]
    if not sequence:
        return CheckResult.failed("no fpl invocation")
    first = sequence[0][1]
    if first.subcommand != "calibrate" or first.option("--round") != str(run.round):
        return CheckResult.failed(f"first fpl call is `{' '.join(first.args)}`, "
                                  f"not calibrate --round {run.round}")
    actuals = [index for index, inv in sequence if inv.subcommand == "actuals"]
    if len(actuals) > 1:
        return CheckResult.failed(f"actuals ran {len(actuals)} times")
    writes = [index for index, call in enumerate(run.calls)
              if run.retro_path in write_paths(call, run.root)]
    if actuals and writes and min(writes) < actuals[0]:
        return CheckResult.failed(f"{run.retro_path} written (call {min(writes) + 1}) "
                                  f"before actuals (call {actuals[0] + 1})")
    return CheckResult.passed(f"calibrate first; actuals ×{len(actuals)}")


def r2_turns(run: RetroRun) -> CheckResult:
    turns = counted_turns(run)
    budget = BASE_TURNS + (1 if expected_backlog(run) else 0)
    persisted = [f"call {run.calls.index(c) + 1}" for turn in turns for c in turn
                 if _PERSISTED.search(json.dumps(dict(c.input)))]
    evidence = f"{len(turns)} turns, budget {budget}"
    if persisted:
        evidence += f"; persisted-output reads: {', '.join(persisted)}"
    return CheckResult.passed(evidence) if len(turns) <= budget \
        else CheckResult.failed(evidence)


def r3_no_persisted(run: RetroRun) -> CheckResult:
    truncated = [f"call {i + 1}" for i, c in enumerate(run.calls)
                 if c.result is not None and c.result.truncated]
    return CheckResult.failed(f"persisted output: {', '.join(truncated)}") if truncated \
        else CheckResult.passed("every result inline")


def r4_actuals_cover(run: RetroRun) -> CheckResult:
    if run.ledger is None or run.expect_refusal:
        return CheckResult.na("no ledger, or calibrate must refuse")
    needed = {miss.id for miss in squad_misses(run.ledger)}
    asked: set[int] = set()
    for call in run.calls:
        for inv in call_fpl_invocations(call):
            if inv.subcommand == "actuals":
                raw = inv.option("--ids") or ""
                asked |= {int(x) for x in re.split(r"[,\s]+", raw) if x.isdigit()}
    missing = sorted(needed - asked)
    return CheckResult.failed(f"squad misses not fetched: {missing}") if missing \
        else CheckResult.passed(f"{len(needed)} squad misses fetched")


def _allowed_fpl_paths(text: str, *, index_allowed: bool) -> str:
    if index_allowed:
        text = text.replace(INDEX_GREP, " ")
        text = _EP_SED.sub(" ", text)
    return text


def r5_forbidden(run: RetroRun) -> CheckResult:
    index_allowed = MARK_CORRECTIONS_CLI in run.instructions
    for number, call in enumerate(run.calls, 1):
        if call.name == "Read":
            path = str(call.input.get("file_path", ""))
            if _PERSISTED.search(path) or path.endswith((*SPEC_FILES, "data/entry.json")):
                continue
            if re.search(r"-calibration\.json$|data/(?:analysis|raw)/|docs/backlog\.md|"
                         r"(?:^|/)fpl/", path):
                return CheckResult.failed(f"call {number} reads {path}")
            continue
        if call.name in ("Grep", "Glob"):
            return CheckResult.failed(f"call {number} explores with {call.name}")
        if call.name != "Bash":
            continue
        command = str(call.input.get("command", ""))
        text = executable_text(command)
        for segment in _segments(command_lines(command)):
            word = segment.split()[0] if segment.split() else ""
            if word in _EXPLORERS:
                return CheckResult.failed(f"call {number} runs `{segment[:80]}`")
        for pattern, label in _FORBIDDEN:
            match = pattern.search(text)
            if match:
                return CheckResult.failed(f"call {number}: {label.format(*match.groups())}")
        for inv in call_fpl_invocations(call):
            if inv.subcommand not in ALLOWED_FPL:
                return CheckResult.failed(f"call {number}: fpl {inv.subcommand}")
        scrubbed = text
        for allowed in SHAPE_CHECKS:
            scrubbed = scrubbed.replace(allowed, " ")
        scrubbed = re.sub(r">>\s*docs/backlog\.md", " ", scrubbed)
        scrubbed = _allowed_fpl_paths(scrubbed, index_allowed=index_allowed)
        for pattern, label in (
            (r"-calibration\.json", "a calibration ledger"),
            (r"data/analysis/", "data/analysis/"),
            (r"data/raw/", "data/raw/"),
            (r"docs/backlog\.md", "docs/backlog.md"),
            (r"(?<![\w-])fpl/\S*", "fpl/ source"),
        ):
            match = re.search(pattern, scrubbed)
            if match:
                return CheckResult.failed(f"call {number} reads {label}: `{match.group(0)}`")
    return CheckResult.passed("")


def r6_writes(run: RetroRun) -> CheckResult:
    for number, call in enumerate(run.calls, 1):
        for path in write_paths(call, run.root):
            if path == run.retro_path:
                continue
            if path == BACKLOG and call.name == "Bash" and not re.search(
                    r"(?<![>&\d])>\s*docs/backlog\.md", command_lines(
                        str(call.input.get("command", ""))).replace(">>", "")):
                continue
            return CheckResult.failed(f"call {number} writes {path}")
    if run.workspace is not None:
        managed = re.compile(_LIVE_CLI_FILES.pattern.format(n=run.gw))
        allowed = {run.retro_path, f"data/retro/gw{run.round}-calibration.json", BACKLOG}
        changed = sorted(p for p in set(run.workspace.before) | set(run.workspace.after)
                         if run.workspace.before.get(p) != run.workspace.after.get(p))
        stray = [p for p in changed if p not in allowed and not managed.match(p)]
        if stray:
            return CheckResult.failed(f"workspace changed: {stray[:5]}")
    return CheckResult.passed("")


def r7_headers(run: RetroRun) -> CheckResult:
    if run.expect_refusal:
        return CheckResult.na("calibrate must refuse")
    if run.retro is None:
        return CheckResult.failed(f"no {run.retro_path}")
    found, wanted = headers(run.retro), expected_headers(run.round)
    return CheckResult.passed("") if found == wanted \
        else CheckResult.failed(f"headers {found} != {wanted}")


def r8_caps(run: RetroRun) -> CheckResult:
    if run.retro is None:
        return CheckResult.na("no retro")
    over = []
    for title, cap in SECTION_CAPS.items():
        count = non_blank(outside_fences(section(run.retro, title)))
        if count > cap:
            over.append(f"{title} {count} > {cap}")
    carried = non_blank(outside_fences(section(run.retro, "Carried into")))
    if carried > CARRIED_CAP:
        over.append(f"Carried {carried} > {CARRIED_CAP}")
    rows = len(table_rows(section(run.retro, "Misses")))
    cap = MISSES_CAP
    if MARK_POOL_ROWS in run.instructions and run.ledger is not None:
        cap = len(squad_misses(run.ledger)) + POOL_ROWS_CAP
    if rows > cap:
        over.append(f"Misses {rows} rows > {cap}")
    return CheckResult.failed("; ".join(over)) if over else CheckResult.passed("")


def r9_fences(run: RetroRun) -> CheckResult:
    stdout = run.calibrate_stdout
    if run.retro is None or stdout is None:
        return CheckResult.na("no retro or no calibrate stdout")
    source = calibrate_lines(stdout)
    problems = []
    squad = fences(section(run.retro, "Squad"))
    squad_lines = [line.rstrip() for line in (squad[0] if squad else [])]
    if not is_subsequence(squad_lines, source):
        problems.append("Squad fence is not calibrate's lines in order")
    needed = [line for line in source if line.startswith(("squad XI", "captain:"))]
    needed += squad_row_lines(stdout)
    absent = [line.split()[2] if line.startswith(" ") else line.split(":")[0]
              for line in needed if line not in squad_lines]
    if absent:
        problems.append(f"Squad fence lacks {absent[:5]}")
    running = fences(section(run.retro, "Running calibration stats"))
    running_lines = [line.rstrip() for line in (running[0] if running else [])]
    if not running_lines or not is_subsequence(running_lines, source):
        problems.append("Running fence is not calibrate's lines in order")
    elif MARK_CORRECTIONS_CLI in run.instructions and not is_contiguous(running_lines, source):
        problems.append("Running fence is not one contiguous block")
    return CheckResult.failed("; ".join(problems)) if problems else CheckResult.passed("")


def r10_misses_rows(run: RetroRun) -> CheckResult:
    if run.retro is None or run.ledger is None:
        return CheckResult.na("no retro or ledger")
    allowed = CLASSES | ({EXECUTION} if MARK_EXECUTION in run.instructions else set())
    body = section(run.retro, "Misses")
    header = misses_header(body)

    def column(name: str, default: int) -> int:
        return header.index(name) if name in header else default

    cols = {k: column(k, i) for i, k in enumerate(("id", "name", "pred", "act", "err",
                                                   "class"))}
    truth = {line.id: line for line in run.ledger.players}
    for row in table_rows(body):
        ident = number(row[cols["id"]]) if len(row) > cols["id"] else None
        if ident is None or int(ident) not in truth:
            return CheckResult.failed(f"row {row[:2]}: id not in the ledger")
        line = truth[int(ident)]
        for key, value in (("pred", line.predicted), ("act", float(line.actual)),
                           ("err", line.error)):
            cell = number(row[cols[key]]) if len(row) > cols[key] else None
            if cell is None or abs(cell - value) > LEDGER_TOLERANCE:
                return CheckResult.failed(f"id {line.id} {key} {row[cols[key]]!r} != "
                                          f"ledger {value}")
        klass = re.sub(r"[*`]", "", row[cols["class"]]).strip() if len(row) > cols["class"] \
            else ""
        if klass not in allowed:
            return CheckResult.failed(f"id {line.id} class {klass!r}")
    return CheckResult.passed(f"{len(table_rows(body))} rows")


def r11_squad_misses_listed(run: RetroRun) -> CheckResult:
    if run.retro is None or run.ledger is None:
        return CheckResult.na("no retro or ledger")
    listed = set(misses_ids(run))
    absent = [f"{m.id} {m.name} {m.error:+.3f}" for m in squad_misses(run.ledger)
              if m.id not in listed]
    return CheckResult.failed(f"missing from Misses: {', '.join(absent)}") if absent \
        else CheckResult.passed("")


def r12_sample_sizes(run: RetroRun) -> CheckResult:
    if run.retro is None:
        return CheckResult.na("no retro")
    haystack = run.outputs + "\n" + run.instructions
    invented = []
    for line in outside_fences(run.retro):
        for match in _N_CLAIM.finditer(line):
            value = match.group(2)
            if not re.search(rf"(?<![\w.]){re.escape(value)}(?![\w]|\.\d)", haystack):
                invented.append(f"n {match.group(1)} {value}")
    return CheckResult.failed(f"untraceable: {', '.join(invented)}") if invented \
        else CheckResult.passed("")


def r13_corrections(run: RetroRun) -> CheckResult:
    if run.retro is None:
        return CheckResult.na("no retro")
    floor = max_prior_number(run.prior_retros)
    numbers = [row.number for row in current_rows(run)]
    problems = []
    duplicates = sorted({n for n in numbers if numbers.count(n) > 1})
    absent = sorted(set(range(1, floor + 1)) - set(numbers))
    if duplicates:
        problems.append(f"rows repeated: {duplicates}")
    if absent:
        problems.append(f"no status row for {absent}")
    fresh = new_rules(run)
    expected = list(range(floor + 1, floor + 1 + len(fresh)))
    if [r.number for r in fresh] != expected:
        problems.append(f"new rules {[r.number for r in fresh]} != {expected}")
    malformed = [f"C{r.number}" for r in fresh if not _NEW_HEADER.match(r.text)]
    if malformed:
        problems.append(f"malformed header: {', '.join(malformed)}")
    return CheckResult.failed("; ".join(problems)) if problems \
        else CheckResult.passed(f"C1–C{floor} tabled; new {[r.number for r in fresh]}")


def r14_backlog(run: RetroRun) -> CheckResult:
    if run.retro is None:
        return CheckResult.na("no retro")
    expected = expected_backlog(run)
    rows = appended_rows(run)
    shape = re.compile(rf"^\| GW{run.gw} \| {_DATE} \| A6 \| (?:{'|'.join(KINDS)}) \|")
    for row in rows:
        if row.count("|") != 8 or not shape.match(row):
            return CheckResult.failed(f"malformed row: {row[:90]}")
    # Rows for findings outside the remit may cite any file; the mirrored
    # rows are the ones citing the retro.
    mirrored = [row for row in rows if f"data/retro/gw{run.round}.md" in row]
    if len(mirrored) != len(expected):
        return CheckResult.failed(f"{len(mirrored)} rows cite data/retro/gw{run.round}.md, "
                                  f"expected {len(expected)} ({', '.join(expected) or 'none'})")
    return CheckResult.passed(f"{len(mirrored)} rows ({', '.join(expected) or 'none'}), "
                              f"{len(rows) - len(mirrored)} remit")


def _return_section(instructions: str) -> str:
    start = instructions.find("## Return to the orchestrator")
    if start < 0:
        return ""
    end = instructions.find("\n## ", start + 1)
    return instructions[start:end if end >= 0 else len(instructions)]


def r15_return_length(run: RetroRun) -> CheckResult:
    budgets = return_budgets(_return_section(run.instructions))
    if not budgets:
        return CheckResult.na("no return budget stated")
    overruns = budget_overruns(run.report, budgets)
    lines = sum(1 for line in run.report.splitlines() if line.strip())
    return CheckResult.failed("; ".join(overruns)) if overruns \
        else CheckResult.passed(f"{lines} lines")


def r16_no_suggestion_ids(run: RetroRun) -> CheckResult:
    for label, text in (("retro", run.retro or ""), ("return", run.report)):
        for line in text.splitlines():
            match = _S_ID.search(line)
            if match:
                return CheckResult.failed(f"{label} names {match.group(0)}: {line.strip()[:90]}")
    return CheckResult.passed("")


def r17_execution(run: RetroRun) -> CheckResult:
    if run.expect_refusal or run.final_md is None or "## CORRECTION" not in run.final_md:
        return CheckResult.na("final.md has no CORRECTION")
    return CheckResult.passed("") if EXECUTION in (run.retro or "") \
        else CheckResult.failed("final.md has a CORRECTION; the retro never says EXECUTION")


def r18_picks_differ(run: RetroRun) -> CheckResult:
    if run.fielded is None or run.final_md is None or run.retro is None:
        return CheckResult.na("no fielded picks recording")
    state = parse_state(run.final_md)
    if state.picks is None:
        return CheckResult.na("final.md has no picks")
    picks = state.picks.picks
    planned = (frozenset(p.id for p in picks),
               next(p.id for p in picks if p.captain), next(p.id for p in picks if p.vice))
    differ = planned != run.fielded
    prose = "\n".join(outside_fences(section(run.retro, "Squad")))
    says = bool(re.search(r"(?i)differ", prose))
    if differ == says:
        return CheckResult.passed(f"picks differ: {differ}")
    return CheckResult.failed(f"picks differ: {differ}, Squad says differ: {says}")


def r19_premise(run: RetroRun) -> CheckResult:
    targets = [r for r in new_rules(run) if re.match(r"^\*\*C\d+ — CODE \(fpl/ep\.py", r.text)]
    if not targets:
        return CheckResult.na("no new CODE (fpl/ep.py) rule")
    printed = "\n".join(c.result.text for c in run.calls
                        if c.name == "Bash" and c.result is not None
                        and _EP_SED.search(str(c.input.get("command", ""))))
    for rule in targets:
        match = _EP_TARGET.match(rule.text)
        if match is None:
            return CheckResult.failed(f"C{rule.number} names no fpl/ep.py function")
        name = match.group(1)
        if MARK_PREMISE not in rule.text:
            return CheckResult.failed(f"C{rule.number} has no Premise:")
        if not re.search(rf"(?m)^\s*(?:\d+\s+)?(?:def {name}\b|{name}\s*[:=])", printed):
            return CheckResult.failed(f"C{rule.number}: {name} was never printed by sed")
    return CheckResult.passed(f"{len(targets)} premises checked")


def r20_retire_c7_c16(run: RetroRun) -> CheckResult:
    rows = {row.number: row.status for row in current_rows(run)}
    bad = [f"C{n} {rows.get(n, 'missing')!r}" for n in (7, 16)
           if not rows.get(n, "").startswith("retired")]
    return CheckResult.failed("; ".join(bad)) if bad else CheckResult.passed("")


def r21_c9_premise_false(run: RetroRun) -> CheckResult:
    if not run.expect_c9_retired:
        return CheckResult.na("case does not carry C9")
    status = {row.number: row.status for row in current_rows(run)}.get(9, "")
    if not re.match(r"retired — premise false", status):
        return CheckResult.failed(f"C9 status {status!r}")
    if not any(re.search(r"\bC9\b", row) and "retired" in row for row in appended_rows(run)):
        return CheckResult.failed("C9's retirement is not mirrored to the backlog")
    return CheckResult.passed("")


def r22_refusal(run: RetroRun) -> CheckResult:
    if not run.expect_refusal:
        return CheckResult.na("calibrate is expected to run")
    ran = [inv.subcommand for c in run.calls for inv in call_fpl_invocations(c)]
    for forbidden in ("actuals", "bootstrap"):
        if forbidden in ran:
            return CheckResult.failed(f"ran {forbidden} after the refusal")
    if run.retro is not None or appended_rows(run):
        return CheckResult.failed("wrote the retro or a backlog row after the refusal")
    if "data-checked" not in run.report:
        return CheckResult.failed("the return does not quote the refusal")
    return CheckResult.passed("")


def r23_null_team(run: RetroRun) -> CheckResult:
    if not run.null_team:
        return CheckResult.na("team_id is set")
    ran = {inv.subcommand for c in run.calls for inv in call_fpl_invocations(c)}
    if ran & {"picks", "entry-history"}:
        return CheckResult.failed(f"ran {sorted(ran & {'picks', 'entry-history'})} "
                                  "with a null team_id")
    if run.retro is None:
        return CheckResult.failed("no retro written")
    findings = section(run.retro, "Findings").lower()
    if "picks" not in findings and "entry-history" not in findings:
        return CheckResult.failed("Findings does not say picks and entry-history were skipped")
    return CheckResult.passed("")


CHECKS: tuple[Check, ...] = (
    Check("R1", r1_order),
    Check("R2", r2_turns),
    Check("R3", r3_no_persisted, requires=MARK_CORRECTIONS_CLI),
    Check("R4", r4_actuals_cover),
    Check("R5", r5_forbidden),
    Check("R6", r6_writes),
    Check("R7", r7_headers),
    Check("R8", r8_caps),
    Check("R9", r9_fences),
    Check("R10", r10_misses_rows),
    Check("R11", r11_squad_misses_listed),
    Check("R12", r12_sample_sizes),
    Check("R13", r13_corrections),
    Check("R14", r14_backlog),
    Check("R15", r15_return_length),
    Check("R16", r16_no_suggestion_ids),
    Check("R17", r17_execution),
    Check("R18", r18_picks_differ, mode="live"),
    Check("R19", r19_premise, requires=MARK_PREMISE),
    Check("R20", r20_retire_c7_c16, requires=MARK_RETIRE_C16),
    Check("R21", r21_c9_premise_false, requires=MARK_PREMISE, mode="live"),
    Check("R22", r22_refusal, mode="live"),
    Check("R23", r23_null_team, mode="live"),
)


def backlog_from_transcript(transcript: Transcript) -> str:
    return "".join(appended_text(str(c.input.get("command", "")), BACKLOG) or ""
                   for c in transcript.calls if c.name == "Bash")
