"""Player-analyst graders: pure functions over a run.

P = procedure (call budget, reads, writes, ep, backlog, return), V = the
minutes model's availability rules, M = players-POS.md, R = retro
corrections, X = REOPEN scope. Checks that need a spec rule the recorded runs
were not given are gated on the rule's marker text.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime

from evals.fixture_analyst.checks import segments
from evals.harness.checks import Check, CheckResult
from evals.harness.shell import (
    appended_text,
    call_failed,
    call_fpl_invocations,
    command_lines,
    executable_text,
    normalise,
    write_paths,
)
from evals.harness.transcript import HANDBACK_TOOL, ToolCall, Transcript
from evals.harness.workspace import Manifest
from evals.player_analyst.cases import (
    BACKLOG,
    MAX_CALLS,
    MAX_CALLS_REOPEN,
    MAX_ESCALATIONS,
    MAX_MD_LINES,
    MAX_RETURN_LINES,
    MAX_RETURN_LINES_REOPEN,
    POSITIONS,
    REOPEN,
)

MARKERS = ("at most 10 tool calls", "fpl corrections", "calibration ledgers", "## REOPEN mode",
           "Unknown return date", "treats those seasons as missing")
HORIZON = 6
ZERO = 0.05
P_TOLERANCE = 0.005
C18_CEILING = 0.90
NEW_PLAYER_CAP = 0.70
MD_HEADINGS = ("Top 15 by EP6", "Minutes calls", "Overrides",
               "Nailed cheap beats rotating premium", "Retro compliance", "Escalations")
MONTHS = {m: i for i, m in enumerate(
    ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1)}
SEASON_START_YEAR = 2026

_BOOTSTRAP_READ = re.compile(r"bootstrap(?:-[\dT_Z]+)?\.json|/\.archive/\S")
_RAW_LEDGER_READ = re.compile(r"summary-[\d*{]|raw/gw[^/\s]*/players/|event-live"
                              r"|-calibration\.json")
_BACKLOG_ALLOWED = (re.compile(r"^tail -c ?1 \S*docs/backlog\.md$"),
                    re.compile(r"^awk '/\^## Rows/.*' \S*docs/backlog\.md$"))
_GIT_COMMIT = re.compile(r"\bgit\b[^\n;&|]*\bcommit\b")
_QUOTED_HEREDOC = re.compile(r"<<-?\s*(['\"])[A-Za-z_]\w*\1")
_RETURN_DATE = re.compile(r"(?:Expected back|Suspended until) (\d{1,2}) ([A-Z][a-z]{2})")
_DOUBT = re.compile(r"(\d{1,3})% chance of playing")
_PRICE_MENTION = re.compile(
    r"([A-Z][\w'.À-ž-]+(?: [A-Z][\w'.À-ž-]+)?) \(([A-Z]{3}),? £?(\d{1,2}\.\d)\)")
_TOP_ROW = re.compile(r"^\s*(\d+)\s{2}\S", re.M)
_BULLET = re.compile(r"^\s*(?:[-*]|\d+\.)\s", re.M)
_CORRECTION_ID = re.compile(r"\bC(\d+)\b")


@dataclass(frozen=True)
class LiveEvidence:
    """What only a live run can show: the workspace before and after, the
    reference `ep` rerun from the final inputs, and the replay log."""

    before: Manifest
    after: Manifest
    canary: str
    changed_text: str
    reference_players: list[dict] | None
    served_keys: tuple[str, ...]
    allowed_changes: frozenset[str]


@dataclass(frozen=True)
class PlayerRun:
    """`inputs`/`players`/`md` are the run's final outputs; `before_inputs`
    the inputs it started from and `before_md` the md (REOPEN). `top15` is what the md's Top 15 must
    list. `summary` returns a player's element summary as the run saw it.
    `project_instructions` is the CLAUDE.md the run had in its context."""

    transcript: Transcript
    instructions: str
    root: str
    gw: int
    pos: str
    mode: str
    inputs: Mapping | None
    players: list[dict] | None
    md: str | None
    top15: tuple[int, ...]
    bootstrap: Mapping
    fixtures: list[dict]
    summary: Callable[[int], Mapping | None]
    active: frozenset[int]
    retired: frozenset[int]
    changed_ids: frozenset[int] = frozenset()
    before_inputs: Mapping | None = None
    live: LiveEvidence | None = None
    extra: Mapping = field(default_factory=dict)
    project_instructions: str = ""
    before_md: str | None = None

    @property
    def calls(self) -> tuple[ToolCall, ...]:
        return self.transcript.calls

    @property
    def work_calls(self) -> list[ToolCall]:
        return [c for c in self.calls if c.name != HANDBACK_TOOL]

    @property
    def reopen(self) -> bool:
        return self.mode == REOPEN

    @property
    def inputs_path(self) -> str:
        return f"data/analysis/gw{self.gw}/inputs-{self.pos}.json"

    @property
    def md_path(self) -> str:
        return f"data/analysis/gw{self.gw}/players-{self.pos}.md"

    @property
    def players_path(self) -> str:
        return f"data/analysis/gw{self.gw}/players-{self.pos}.json"

    @property
    def elements(self) -> dict[int, Mapping]:
        return {e["id"]: e for e in self.bootstrap["elements"]}

    @property
    def team_names(self) -> dict[int, str]:
        return {t["id"]: t["short_name"] for t in self.bootstrap["teams"]}

    def rows(self) -> list[Mapping]:
        rows = list((self.inputs or {}).get("players", []))
        if self.reopen:
            changed = changed_rows(self.before_inputs, self.inputs)
            rows = [r for r in rows if r["id"] in changed]
        return rows


def changed_rows(before: Mapping | None, after: Mapping | None) -> set[int]:
    old = {r["id"]: r for r in (before or {}).get("players", [])}
    return {r["id"] for r in (after or {}).get("players", []) if old.get(r["id"]) != r}


def starts(row: Mapping) -> list[float]:
    gws = row.get("p_start_gw")
    return list(gws) if gws else [row["p_start"]] * HORIZON


def call_no(run: PlayerRun, call: ToolCall) -> int:
    return run.work_calls.index(call) + 1 if call in run.work_calls else 0


# --- P: procedure ----------------------------------------------------------------


def p1_call_budget(run: PlayerRun) -> CheckResult:
    limit = MAX_CALLS_REOPEN if run.reopen else MAX_CALLS
    used = len(run.work_calls)
    if used > limit:
        return CheckResult.failed(f"{used} work calls > {limit}")
    return CheckResult.passed(f"{used} work calls")


def p2_inline_output(run: PlayerRun) -> CheckResult:
    persisted = [call_no(run, c) for c in run.work_calls if c.result and c.result.truncated]
    if persisted:
        return CheckResult.failed(f"output persisted at call(s) {_numbers(persisted)}")
    return CheckResult.passed("every output inline")


def p3a_forbidden_reads(run: PlayerRun) -> CheckResult:
    boot, backlog = [], []
    for call in run.work_calls:
        number = call_no(run, call)
        for target in _read_targets(call, run.root):
            if _BOOTSTRAP_READ.search(target):
                boot.append(number)
            if BACKLOG in target and not _backlog_allowed(target):
                backlog.append(number)
    problems = []
    if boot:
        problems.append(f"bootstrap read at call(s) {_numbers(sorted(set(boot)))}")
    if backlog:
        problems.append(f"backlog read at call(s) {_numbers(sorted(set(backlog)))}")
    return CheckResult.failed("; ".join(problems)) if problems else CheckResult.passed(
        "no bootstrap or backlog read")


def p3b_raw_ledgers(run: PlayerRun) -> CheckResult:
    found = raw_ledger_reads(run)
    if found:
        return CheckResult.failed(f"summary/event-live/calibration read at call(s) "
                                  f"{_numbers(found)}")
    return CheckResult.passed("no summary, event-live or calibration read")


def raw_ledger_reads(run: PlayerRun) -> list[int]:
    return sorted({call_no(run, call) for call in run.work_calls
                   for target in _read_targets(call, run.root)
                   if _RAW_LEDGER_READ.search(target)})


def p4_writes(run: PlayerRun) -> CheckResult:
    allowed = {run.inputs_path, run.md_path}
    for call in run.work_calls:
        number = call_no(run, call)
        if call.name == "Bash" and _GIT_COMMIT.search(command_lines(_command(call))):
            return CheckResult.failed(f"call {number} runs git commit")
        appends = _backlog_appends(call)
        for path in write_paths(call, run.root):
            if path == run.players_path:
                return CheckResult.failed(f"call {number} writes {path} by hand")
            if path in allowed or _outside_repo(path) or (path == BACKLOG and appends):
                continue
            return CheckResult.failed(f"call {number} writes {path}")
    return CheckResult.passed("writes limited to own inputs, md and backlog appends")


def p5_final_ep(run: PlayerRun) -> CheckResult:
    last_write = max((i for i, c in enumerate(run.work_calls, 1)
                      if run.inputs_path in write_paths(c, run.root)), default=0)
    last_ep = None
    for index, call in enumerate(run.work_calls, 1):
        for inv in call_fpl_invocations(call):
            if (inv.subcommand == "ep" and not inv.has("--check") and not inv.has("--out")
                    and str(inv.option("--gw")) == str(run.gw)
                    and _position(inv.option("--position")) == run.pos):
                last_ep = (index, call)
    if last_ep is None:
        return CheckResult.failed("no `fpl ep` run on the final inputs")
    index, call = last_ep
    if index < last_write:
        return CheckResult.failed(f"inputs written at call {last_write} after the last ep "
                                  f"(call {index})")
    # A later command chained into the same call can fail after ep succeeded;
    # ep's closing `wrote <path>` line is the ep's own outcome.
    wrote = call.result is not None and f"wrote {run.players_path}" in call.result.text
    if call_failed(call.result) and not wrote:
        return CheckResult.failed(f"the last ep (call {index}) failed")
    return CheckResult.passed(f"last ep at call {index}, inputs last written at call "
                              f"{last_write or '-'}")


def p6_backlog_rows(run: PlayerRun) -> CheckResult:
    agent = f"A3-{run.pos}"
    count = 0
    for call in run.work_calls:
        if call.name != "Bash":
            continue
        command = _command(call)
        number = call_no(run, call)
        if BACKLOG not in " ".join(write_paths(call, run.root)) and not _appends_backlog(command):
            continue
        body = appended_text(command, BACKLOG)
        if body is None or not _QUOTED_HEREDOC.search(command):
            return CheckResult.failed(f"call {number} appends to the backlog without a quoted "
                                      f"heredoc")
        for line in body.splitlines():
            cells = line.split("|")
            if not line.startswith("| ") or line.count("|") != 8:
                return CheckResult.failed(f"call {number}: malformed row {line[:60]!r}")
            if cells[3].strip() != agent:
                return CheckResult.failed(f"call {number}: agent cell {cells[3].strip()!r} "
                                          f"is not {agent}")
            count += 1
    return CheckResult.passed(f"{count} well-formed row(s)")


def p7_return(run: PlayerRun) -> CheckResult:
    limit = MAX_RETURN_LINES_REOPEN if run.reopen else MAX_RETURN_LINES
    lines = sum(1 for line in run.transcript.final_text.splitlines() if line.strip())
    if lines > limit:
        return CheckResult.failed(f"return is {lines} non-blank lines > {limit}")
    return CheckResult.passed(f"{lines} lines")


# --- V: minutes model ------------------------------------------------------------


def v1_availability(run: PlayerRun) -> CheckResult:
    if run.inputs is None:
        return CheckResult.failed("no inputs file")
    elements = run.elements
    unknown_rule = "Unknown return date" in run.instructions
    problems = []
    for row in run.rows():
        player = elements.get(row["id"])
        if player is None:
            continue
        probs = starts(row)
        news = player.get("news") or ""
        status, chance = player.get("status"), player.get("chance_of_playing_next_round")
        returns = return_date(news)
        name = row.get("name") or player["web_name"]
        window = list(range(run.gw, run.gw + HORIZON))
        first_kickoff = kickoffs(run, player["team"], run.gw)
        unavailable = status in ("i", "s", "u", "n") or chance == 0
        back_in_time = (returns is not None and first_kickoff
                        and returns <= min(first_kickoff))
        if unavailable and not back_in_time and probs[0] > ZERO:
            problems.append(f"{name} {probs[0]:g} ({status}, {news or 'no news'})")
            continue
        if returns is not None:
            for index, gw in enumerate(window):
                dates = kickoffs(run, player["team"], gw)
                if dates and max(dates) < returns and probs[index] > ZERO:
                    problems.append(f"{name} GW{gw} {probs[index]:g} (back {returns:%d %b})")
                    break
        doubt = _DOUBT.search(news)
        if status == "d" and doubt and probs[0] > int(doubt[1]) / 100 + ZERO + 1e-9:
            problems.append(f"{name} {probs[0]:g} > d {doubt[1]}%")
        if unknown_rule and "unknown return date" in news.lower():
            later = [p for p in probs[1:] if p > ZERO]
            notes = str(row.get("notes", "")).lower()
            if later and "guess" not in notes and "research-" not in notes:
                problems.append(f"{name}: later values {later} neither labelled a guess nor "
                                f"sourced")
    if problems:
        return CheckResult.failed("; ".join(problems))
    return CheckResult.passed("availability rules hold")


def v2_c18(run: PlayerRun) -> CheckResult:
    if not _mentions_c18(run):
        return CheckResult.na("C18 not in the prompt or any tool output")
    rounds = (run.gw - 3, run.gw - 2, run.gw - 1)
    problems = []
    for row in run.rows():
        first = starts(row)[0]
        if first <= C18_CEILING + 1e-9:
            continue
        by_round = _history_by_round(run.summary(row["id"]))
        if not all(any((m.get("starts") or 0) >= 1 for m in by_round.get(r, [])) for r in rounds):
            problems.append(f"{row.get('name')} {first:g}")
    if problems:
        return CheckResult.failed("gw[0] > 0.90 without a 3-round start streak: "
                                  + ", ".join(problems))
    return CheckResult.passed("C18 cap holds")


def v3_new_player_cap(run: PlayerRun) -> CheckResult:
    sources = {p["id"]: p.get("rates", {}).get("prior_source") for p in run.players or []}
    problems = []
    for row in run.rows():
        if sources.get(row["id"]) != "league_mean":
            continue
        minutes = [sum(m.get("minutes") or 0 for m in matches)
                   for _, matches in sorted(_history_by_round(run.summary(row["id"])).items())]
        settled = any(a >= 60 and b >= 60 for a, b in zip(minutes, minutes[1:]))
        peak = max(starts(row))
        if not settled and peak > NEW_PLAYER_CAP + 1e-9:
            problems.append(f"{row.get('name')} {peak:g}")
    if problems:
        return CheckResult.failed("no-PL-history player above 0.70 without two 60' starts: "
                                  + ", ".join(problems))
    return CheckResult.passed("new-signing cap holds")


def v4_p_start_matches(run: PlayerRun) -> CheckResult:
    bad = [f"{r.get('name')} {r['p_start']:g}≠{r['p_start_gw'][0]:g}" for r in run.rows()
           if r.get("p_start_gw") and abs(r["p_start"] - r["p_start_gw"][0]) > P_TOLERANCE]
    if bad:
        return CheckResult.failed(f"{len(bad)} row(s): " + ", ".join(bad))
    return CheckResult.passed("p_start equals p_start_gw[0]")


def v5_no_defcon_artefact(run: PlayerRun) -> CheckResult:
    bad = []
    for row in run.rows():
        overrides = row.get("overrides") or {}
        reason = str(row.get("reason", "")).lower()
        if "dc90" in overrides and ("data artefact" in reason or "artifact" in reason
                                    or "2024/25" in reason or "pre-2024" in reason):
            bad.append(str(row.get("name")))
    if bad:
        return CheckResult.failed(f"{len(bad)} dc90 DefCon-artefact override(s): "
                                  + ", ".join(bad))
    return CheckResult.passed("no DefCon-artefact overrides")


# --- M: players-POS.md -----------------------------------------------------------


def m1_md_shape(run: PlayerRun) -> CheckResult:
    md = run.md
    if md is None:
        return CheckResult.failed(f"no {run.md_path}")
    problems = []
    headings = re.findall(r"^## (.+)$", md, re.M)
    position = 0
    for wanted in MD_HEADINGS:
        found = next((i for i, h in enumerate(headings[position:], position)
                      if h.strip().startswith(wanted)), None)
        if found is None:
            problems.append(f"heading {wanted!r} missing or out of order")
            break
        position = found + 1
    lines = md.count("\n") + (0 if md.endswith("\n") else 1)
    if lines > MAX_MD_LINES:
        problems.append(f"{lines} lines > {MAX_MD_LINES}")
    top = [int(i) for i in _TOP_ROW.findall(section(md, "Top 15") or "")][:15]
    if top != list(run.top15):
        problems.append(f"Top 15 ids differ from ep: {top[:5]}… vs {list(run.top15[:5])}…")
    escalations = len(_BULLET.findall(section(md, "Escalations") or ""))
    if escalations > MAX_ESCALATIONS:
        problems.append(f"{escalations} escalations > {MAX_ESCALATIONS}")
    if problems:
        return CheckResult.failed("; ".join(problems))
    return CheckResult.passed(f"{lines} lines, {escalations} escalations")


def m2_prices(run: PlayerRun) -> CheckResult:
    if run.md is None:
        return CheckResult.failed(f"no {run.md_path}")
    teams = run.team_names
    prices: dict[tuple[str, str], float] = {}
    for player in run.bootstrap["elements"]:
        prices.setdefault((player["web_name"], teams[player["team"]]), player["now_cost"] / 10)
    bad = []
    for match in _PRICE_MENTION.finditer(run.md):
        key = (match[1], match[2])
        if key in prices and abs(prices[key] - float(match[3])) > 0.05:
            bad.append(f"{match[1]} {match[3]}≠{prices[key]:.1f}")
    if bad:
        return CheckResult.failed(", ".join(bad))
    return CheckResult.passed("every quoted price matches the bootstrap")


# --- R: corrections --------------------------------------------------------------


def r1_active_cited(run: PlayerRun) -> CheckResult:
    cited = _cited(run)
    if cited is None:
        return CheckResult.failed("no Retro compliance section")
    missing = sorted(run.active - cited)
    if missing:
        return CheckResult.failed("active correction(s) not cited: "
                                  + ", ".join(f"C{n}" for n in missing))
    return CheckResult.passed("every active correction cited")


def r2_retired_not_cited(run: PlayerRun) -> CheckResult:
    cited = _cited(run) or set()
    if run.reopen:
        if run.before_md is None:
            return CheckResult.na("REOPEN run without the md it was given")
        cited -= _cited(replace(run, md=run.before_md)) or set()
    stale = sorted(run.retired & cited)
    if stale:
        return CheckResult.failed("retired correction(s) cited: "
                                  + ", ".join(f"C{n}" for n in stale))
    return CheckResult.passed("no retired correction cited")


def info_r2(run: PlayerRun) -> CheckResult:
    stale = sorted(run.retired & (_cited(run) or set()))
    return CheckResult.na("info: retired cited: " + (", ".join(f"C{n}" for n in stale)
                                                     or "none"))


def info_p3b(run: PlayerRun) -> CheckResult:
    found = raw_ledger_reads(run)
    return CheckResult.na("info: summary/event-live/calibration reads at "
                          + (_numbers(found) if found else "none"))


def info_u1(run: PlayerRun) -> CheckResult:
    sources = {p["id"]: p.get("rates", {}).get("prior_source") for p in run.players or []}
    rows = [r for r in run.rows() if sources.get(r["id"]) == "league_mean"
            and r.get("uncertainty") != "HIGH"]
    return CheckResult.na(f"info: {len(rows)} league_mean row(s) not HIGH")


# --- X: REOPEN scope -------------------------------------------------------------


def x1_reopen_scope(run: PlayerRun) -> CheckResult:
    if not run.reopen:
        return CheckResult.na("normal mode")
    changed = changed_rows(run.before_inputs, run.inputs)
    elements = run.elements
    flagged_clubs = {elements[i]["team"] for i in run.changed_ids if i in elements}
    outside = sorted(i for i in changed if i not in run.changed_ids
                     and elements.get(i, {}).get("team") not in flagged_clubs)
    others = [f"data/analysis/gw{run.gw}/{kind}-{pos}.{ext}"
              for pos in POSITIONS if pos != run.pos
              for kind, ext in (("inputs", "json"), ("players", "md"), ("players", "json"))]
    touched = sorted({p for c in run.work_calls for p in write_paths(c, run.root)
                      if p in others})
    if outside or touched:
        return CheckResult.failed("; ".join(filter(None, (
            f"changed rows outside the delta and its clubs: {outside}" if outside else "",
            f"other positions' files written: {touched}" if touched else ""))))
    return CheckResult.passed(f"changed {sorted(changed)}")


# --- live only -------------------------------------------------------------------


def l1_no_hand_edits(run: PlayerRun) -> CheckResult:
    live = run.live
    if live is None or live.reference_players is None:
        return CheckResult.failed("no reference ep rerun")
    if run.players != live.reference_players:
        return CheckResult.failed(f"{run.players_path} differs from an ep rerun of the final "
                                  f"inputs")
    return CheckResult.passed("players json equals the ep rerun")


def l2_workspace_diff(run: PlayerRun) -> CheckResult:
    live = run.live
    assert live is not None
    changed = {p for p in set(live.before) | set(live.after)
               if live.before.get(p) != live.after.get(p)}
    stray = sorted(p for p in changed if p not in live.allowed_changes
                   and not p.startswith(f"data/raw/gw{run.gw}/.archive/"))
    if stray:
        return CheckResult.failed(f"unexpected workspace changes: {stray[:5]}")
    return CheckResult.passed(f"{len(changed)} allowed change(s)")


def l3_network(run: PlayerRun) -> CheckResult:
    live = run.live
    assert live is not None
    networked = sorted({inv.subcommand for c in run.work_calls for inv in call_fpl_invocations(c)
                        if inv.subcommand in _NETWORK and not inv.is_help})
    if set(networked) - {"summaries"}:
        return CheckResult.failed(f"network fpl commands: {networked}")
    stray = [k for k in live.served_keys if not k.startswith("element-summary/")]
    if stray:
        return CheckResult.failed(f"served non-summary recordings: {stray[:5]}")
    return CheckResult.passed(f"{len(live.served_keys)} summary fetch(es)")


def l4_canary(run: PlayerRun) -> CheckResult:
    live = run.live
    assert live is not None
    haystack = json.dumps([dict(c.input) for c in run.calls]) + run.transcript.final_text
    haystack += "".join(c.result.text for c in run.calls if c.result) + live.changed_text
    if live.canary in haystack:
        return CheckResult.failed("the auth canary leaked")
    return CheckResult.passed("canary absent")


def e1_expectations(run: PlayerRun) -> CheckResult:
    """The case's own expected outcomes (cases.Expect)."""
    expect = run.extra.get("expect")
    if expect is None:
        return CheckResult.na("no case expectations")
    rows = {r["id"]: r for r in (run.inputs or {}).get("players", [])}
    problems = []

    def gw0(pid: int) -> float | None:
        return starts(rows[pid])[0] if pid in rows else None

    for pid, ceiling in expect.max_gw0.items():
        value = gw0(pid)
        if value is not None and value > ceiling + 1e-9:
            problems.append(f"id {pid} gw[0] {value:g} > {ceiling:g}")
    for pid, floor in expect.min_gw0.items():
        value = gw0(pid)
        if value is None or value < floor - 1e-9:
            problems.append(f"id {pid} gw[0] {value} < {floor:g}")
    for pid in expect.zero_ids:
        if pid in rows and max(starts(rows[pid])) > ZERO:
            problems.append(f"id {pid} not zero across the window: {starts(rows[pid])}")
    for pid in expect.guess_ids:
        notes = str(rows.get(pid, {}).get("notes", "")).lower()
        later = [p for p in starts(rows[pid])[1:] if p > ZERO] if pid in rows else []
        if later and "guess" not in notes and "research-" not in notes:
            problems.append(f"id {pid}: later values neither a guess nor sourced")
    for pid, (later, earlier) in expect.falls.items():
        probs = starts(rows[pid]) if pid in rows else []
        if not probs or probs[later] >= probs[earlier]:
            problems.append(f"id {pid}: gw[{later}] not below gw[{earlier}] ({probs})")
    for pid, text in expect.cites.items():
        if text not in str(rows.get(pid, {}).get("notes", "")):
            problems.append(f"id {pid} notes do not cite {text}")
    if expect.max_summary_calls is not None:
        used = sum(1 for c in run.work_calls for inv in call_fpl_invocations(c)
                   if inv.subcommand == "summaries")
        if used > expect.max_summary_calls:
            problems.append(f"{used} summaries calls > {expect.max_summary_calls}")
    if expect.summaries_for_starters and run.extra.get("missing_starter_summaries"):
        problems.append(f"no summary for starters {run.extra['missing_starter_summaries']}")
    for word in expect.shunned:
        hit = [r["id"] for r in rows.values()
               if word in str(r.get("reason", "")) + str(r.get("notes", ""))]
        if hit:
            problems.append(f"{word!r} in the reason or notes of {hit}")
    if expect.compliance_line is not None:
        tag, word = expect.compliance_line
        body = section(run.md or "", "Retro compliance") or ""
        if not any(re.search(rf"\b{tag}\b", line) and word in line.lower()
                   for line in body.splitlines()):
            problems.append(f"no Retro compliance line for {tag} saying {word!r}")
    if problems:
        return CheckResult.failed("; ".join(problems))
    return CheckResult.passed("case expectations met")


_NETWORK = frozenset({"bootstrap", "fixtures", "summaries", "entry", "picks", "entry-history",
                      "actuals", "flags", "calibrate", "auth-check", "my-team", "set-lineup",
                      "make-transfers"})


CHECKS: tuple[Check, ...] = (
    Check("P1", p1_call_budget),
    Check("P2", p2_inline_output),
    Check("P3a", p3a_forbidden_reads),
    Check("P3b", p3b_raw_ledgers, requires="calibration ledgers"),
    Check("P4", p4_writes),
    Check("P5", p5_final_ep),
    Check("P6", p6_backlog_rows),
    Check("P7", p7_return),
    Check("V1", v1_availability),
    Check("V2", v2_c18),
    Check("V3", v3_new_player_cap),
    Check("V4", v4_p_start_matches),
    Check("V5", v5_no_defcon_artefact, requires="treats those seasons as missing"),
    Check("M1", m1_md_shape),
    Check("M2", m2_prices),
    Check("R1", r1_active_cited),
    Check("R2", r2_retired_not_cited, requires="fpl corrections"),
    Check("X1", x1_reopen_scope),
    Check("I-P3b", info_p3b),
    Check("I-R2", info_r2),
    Check("U1", info_u1),
    Check("L1", l1_no_hand_edits, mode="live"),
    Check("L2", l2_workspace_diff, mode="live"),
    Check("L3", l3_network, mode="live"),
    Check("L4", l4_canary, mode="live"),
    Check("E1", e1_expectations, mode="live"),
)


# --- helpers ---------------------------------------------------------------------


def return_date(news: str) -> date | None:
    match = _RETURN_DATE.search(news)
    if not match or match[2] not in MONTHS:
        return None
    month = MONTHS[match[2]]
    year = SEASON_START_YEAR if month >= 7 else SEASON_START_YEAR + 1
    return date(year, month, int(match[1]))


def section(md: str, heading: str) -> str | None:
    match = re.search(rf"(?m)^## {re.escape(heading)}.*$", md)
    if match is None:
        return None
    rest = md[match.end():]
    end = re.search(r"(?m)^## ", rest)
    return rest[:end.start()] if end else rest


def _cited(run: PlayerRun) -> set[int] | None:
    body = section(run.md or "", "Retro compliance")
    if body is None:
        return None
    return {int(n) for n in _CORRECTION_ID.findall(body)}


def _mentions_c18(run: PlayerRun) -> bool:
    if re.search(r"\bC18\b", run.instructions):
        return True
    return any(c.result and re.search(r"\bC18\b", c.result.text) for c in run.calls)


def kickoffs(run: PlayerRun, team: int, gw: int) -> list[date]:
    found = []
    for fixture in run.fixtures:
        if fixture.get("event") == gw and team in (fixture["team_h"], fixture["team_a"]):
            if fixture.get("kickoff_time"):
                found.append(datetime.fromisoformat(
                    fixture["kickoff_time"].replace("Z", "+00:00")).astimezone(UTC).date())
    return found


def _history_by_round(summary: Mapping | None) -> dict[int, list[Mapping]]:
    by_round: dict[int, list[Mapping]] = {}
    for match in (summary or {}).get("history", []):
        if match.get("round") is not None:
            by_round.setdefault(match["round"], []).append(match)
    return by_round


def _command(call: ToolCall) -> str:
    return str(call.input.get("command", ""))


def _read_targets(call: ToolCall, root: str) -> list[str]:
    """Text a call reads from: a Read/Grep path, or each shell segment and
    executed heredoc line, with write redirects removed."""
    if call.name in ("Read", "Grep"):
        return [normalise(str(call.input.get("file_path") or call.input.get("path", "")), root)]
    if call.name != "Bash":
        return []
    command = _command(call)
    outer = command_lines(command)
    bodies = executable_text(command)[len(outer):].splitlines()
    found = []
    for segment in [*segments(command), *bodies]:
        stripped = re.sub(r">>?\s*\S+", "", segment).strip()
        if re.match(r"^ls\b", stripped):
            continue
        found.append(stripped)
    return found


def _backlog_allowed(segment: str) -> bool:
    segment = re.sub(r"\s+", " ", segment).strip()
    if re.match(r"^cat <<-?\s*['\"]?\w+['\"]?$", segment):
        return True
    return any(p.match(segment) for p in _BACKLOG_ALLOWED)


def _backlog_appends(call: ToolCall) -> bool:
    return call.name == "Bash" and _appends_backlog(_command(call))


def _appends_backlog(command: str) -> bool:
    return bool(re.search(r">>\s*\S*docs/backlog\.md", command_lines(command)))


def _outside_repo(path: str) -> bool:
    return path.startswith(("/", "~")) or path in ("", "/dev/null")


def _position(value: str | None) -> str | None:
    if value is None:
        return None
    upper = value.upper()
    return "GKP" if upper == "GK" else upper


def _numbers(values: list[int]) -> str:
    return ",".join(f"c{v}" for v in values)
