"""Token usage and list-price cost of one Claude Code session window.

Reads the transcripts Claude Code keeps under ~/.claude/projects/<project>/:
the main <session>.jsonl plus <session>/subagents/agent-<id>.jsonl with its
.meta.json. Each API response is written as one line per content block, all
sharing the message id and only the last carrying the final output count, so
lines are folded into one record per id taking the maximum output. Subagent
calls belong to the window in which the orchestrator spawned them, not to
the window their own timestamps fall in.

The transcript format is internal to Claude Code and can change between
releases: this module reads the few fields it needs and refuses loudly when a
model it cannot price appears, rather than guessing.

Costs are Anthropic list-price equivalents. On a subscription nothing is
billed at these rates; use them as a relative measure.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

PRICING_DATE = "2026-06-24"
# USD per 1M tokens: input, output, cache write 5m TTL, cache write 1h TTL, cache read.
PRICES: dict[str, tuple[float, float, float, float, float]] = {
    "claude-fable-5-1": (10.0, 50.0, 12.5, 20.0, 0.25),
    "claude-fable-5": (10.0, 50.0, 12.5, 20.0, 1.0),
    "claude-opus-5": (5.0, 25.0, 6.25, 10.0, 0.5),
    "claude-sonnet-5": (2.0, 10.0, 2.5, 4.0, 0.2),
    "claude-haiku-4-5": (1.0, 5.0, 1.25, 2.0, 0.1),
}
_PRICE_KEYS = sorted(PRICES, key=len, reverse=True)

MAIN_THREAD = "main"
ORCHESTRATOR = "orchestrator"
SYNTHETIC_MODEL = "<synthetic>"
ACTIVE_GAP_CAP = timedelta(minutes=5)
PROMPT_PREVIEW = 160
REDACTED = "[redacted]"
# Prompt text is copied into committed ledgers; anything shaped like a token
# is masked before it gets there.
_SECRET_SHAPES = re.compile(
    r"(?i)(bearer\s+\S+|eyJ[A-Za-z0-9_-]{10,}[A-Za-z0-9._-]*"
    r"|\b(?:csrftoken|sessionid|pl_profile|x-api-key|api[_-]?key|token|password)\s*[=:]\s*\S+)"
)

# Pipeline stage from the orchestrator's Agent-call description, first match
# wins, so the more specific rows sit above the broader ones.
STAGES: tuple[tuple[str, str], ...] = (
    (ORCHESTRATOR, r"^orchestrator$"),
    ("data-collector", r"collect|raw data"),
    ("retro-analyst", r"retro"),
    ("fixture-analyst", r"fixture"),
    ("player-analyst", r"score .*players|score gw|player analysis"),
    ("squad-optimizer", r"optimi"),
    ("red-team-reviewer", r"red[- ]team"),
    ("finalizer", r"finali"),
    ("plan-builder", r"plan[- ]builder"),
    ("team-executor", r"executor|auth import|apply transfer|lineup"),
    ("in-cycle patch", r"patch"),
)
OTHER_STAGE = "other"
_STAGE_ORDER = [name for name, _ in STAGES] + [OTHER_STAGE]
_GW_TAG = re.compile(r"\bgw\s?(\d{1,2})\b", re.IGNORECASE)


class UnpricedModelError(ValueError):
    pass


class SessionNotFoundError(ValueError):
    pass


def default_transcripts_root(cwd: Path, home: Path | None = None) -> Path:
    """Claude Code keys a project's transcripts by its cwd with every
    non-alphanumeric character replaced by '-'."""
    home = home or Path.home()
    return home / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(cwd.resolve()))


def stage_for(description: str) -> str:
    text = description.lower()
    for name, pattern in STAGES:
        if re.search(pattern, text):
            return name
    return OTHER_STAGE


def gw_tags(description: str) -> set[int]:
    return {int(m) for m in _GW_TAG.findall(description)}


def parse_ts(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def fmt_ts(dt: datetime, ms: bool = False) -> str:
    if ms:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------ records

@dataclass(frozen=True)
class Cost:
    input: float
    cache_write: float
    cache_read: float
    output: float
    uncached_equivalent: float

    @property
    def total(self) -> float:
        return self.input + self.cache_write + self.cache_read + self.output


@dataclass
class Call:
    message_id: str
    request_id: str | None
    thread: str
    agent: str
    agent_type: str
    requested_tier: str
    timestamp: datetime
    model: str
    effort: str | None
    input_tokens: int = 0
    cache_write_5m: int = 0
    cache_write_1h: int = 0
    cache_read: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    stop_reason: str | None = None
    tool_names: tuple[str, ...] = ()
    version: str | None = None
    lines: int = 0

    @property
    def cache_write_total(self) -> int:
        return self.cache_write_5m + self.cache_write_1h

    @property
    def context_tokens(self) -> int:
        return self.input_tokens + self.cache_read + self.cache_write_total

    @property
    def stage(self) -> str:
        return stage_for(self.agent)


def rates_for(model: str) -> tuple[float, float, float, float, float]:
    for key in _PRICE_KEYS:
        if model.startswith(key):
            return PRICES[key]
    raise UnpricedModelError(
        f"no list price for model {model!r}; add it to fpl.usage.PRICES "
        f"(known: {', '.join(sorted(PRICES))})"
    )


def cost_of(call: Call) -> Cost:
    inp, out, w5, w1, rd = rates_for(call.model)
    return Cost(
        input=call.input_tokens * inp / 1e6,
        cache_write=(call.cache_write_5m * w5 + call.cache_write_1h * w1) / 1e6,
        cache_read=call.cache_read * rd / 1e6,
        output=call.output_tokens * out / 1e6,
        uncached_equivalent=(call.context_tokens * inp + call.output_tokens * out) / 1e6,
    )


@dataclass
class Prompt:
    timestamp: datetime
    kind: str
    text: str


@dataclass
class Agent:
    agent_id: str
    description: str
    agent_type: str
    requested_tier: str
    tool_use_id: str | None
    parent_agent_id: str | None
    spawn_depth: int
    spawned_at: datetime | None
    calls: list[Call] = field(default_factory=list)

    @property
    def last_call_at(self) -> datetime | None:
        return max((c.timestamp for c in self.calls), default=None)


@dataclass
class Session:
    session_id: str
    path: Path
    main_calls: list[Call]
    agents: dict[str, Agent]
    prompts: list[Prompt]
    versions: set[str]
    first_at: datetime | None
    last_at: datetime | None


# ------------------------------------------------------------------ parsing

def _iter_lines(path: Path):
    with path.open() as handle:
        for raw in handle:
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                continue


def _usage_counts(usage: dict) -> tuple[int, int, int, int, int, int]:
    total_write = int(usage.get("cache_creation_input_tokens") or 0)
    split = usage.get("cache_creation") or {}
    if split:
        w5 = int(split.get("ephemeral_5m_input_tokens") or 0)
        w1 = int(split.get("ephemeral_1h_input_tokens") or 0)
    else:
        w5, w1 = total_write, 0
    thinking = int((usage.get("output_tokens_details") or {}).get("thinking_tokens") or 0)
    return (
        int(usage.get("input_tokens") or 0), w5, w1,
        int(usage.get("cache_read_input_tokens") or 0),
        int(usage.get("output_tokens") or 0), thinking,
    )


def _fold_calls(
    path: Path, *, thread: str, agent: str, agent_type: str, requested_tier: str,
    seen: set[str], tool_use_times: dict[str, datetime], skip_sidechain: bool,
) -> list[Call]:
    calls: dict[str, Call] = {}
    tool_ids: dict[str, set[str]] = {}
    for line in _iter_lines(path):
        if line.get("type") != "assistant" or (skip_sidechain and line.get("isSidechain")):
            continue
        message = line.get("message") or {}
        when = line.get("timestamp")
        if not when:
            continue
        content = message.get("content") or []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("id"):
                tool_use_times.setdefault(block["id"], parse_ts(when))
        usage = message.get("usage")
        model = message.get("model")
        mid = message.get("id")
        if not usage or not mid or not model or model == SYNTHETIC_MODEL:
            continue
        inp, w5, w1, rd, out, thinking = _usage_counts(usage)
        call = calls.get(mid)
        if call is None:
            if mid in seen:
                continue
            seen.add(mid)
            call = calls[mid] = Call(
                message_id=mid, request_id=line.get("requestId"), thread=thread, agent=agent,
                agent_type=agent_type, requested_tier=requested_tier, timestamp=parse_ts(when),
                model=model, effort=line.get("effort"), input_tokens=inp, cache_write_5m=w5,
                cache_write_1h=w1, cache_read=rd, version=line.get("version"),
            )
            tool_ids[mid] = set()
        call.lines += 1
        call.output_tokens = max(call.output_tokens, out)
        call.thinking_tokens = max(call.thinking_tokens, thinking)
        if message.get("stop_reason"):
            call.stop_reason = message["stop_reason"]
        names = list(call.tool_names)
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("id") not in tool_ids[mid]:
                tool_ids[mid].add(block.get("id"))
                names.append(block.get("name") or "?")
        call.tool_names = tuple(names)
    return sorted(calls.values(), key=lambda c: c.timestamp)


def _prompt_text(message: dict) -> str | None:
    content = message.get("content")
    if isinstance(content, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            return None
        content = " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    if not isinstance(content, str) or not content.strip():
        return None
    return content.strip()


def _prompt_kind(text: str) -> str:
    if text.startswith("<task-notification>"):
        return "notification"
    if text == "/compact":
        return "compact"
    if text.startswith("<command-name>") or text.startswith("<local-command"):
        return "command"
    if text.startswith("[Request interrupted"):
        return "interrupt"
    if text.startswith("This session is being continued"):
        return "continuation"
    if text.startswith("<"):
        return "system"
    return "human"


def _resolve_session_path(root: Path, session_id: str) -> Path:
    exact = root / f"{session_id}.jsonl"
    if exact.exists():
        return exact
    matches = sorted(p for p in root.glob(f"{session_id}*.jsonl"))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SessionNotFoundError(f"no session {session_id!r} under {root}")
    names = ", ".join(p.stem for p in matches)
    raise SessionNotFoundError(f"session prefix {session_id!r} is ambiguous: {names}")


def load_session(root: Path, session_id: str) -> Session:
    path = _resolve_session_path(root, session_id)
    sid = path.stem
    seen: set[str] = set()
    tool_use_times: dict[str, datetime] = {}
    main_calls = _fold_calls(
        path, thread=MAIN_THREAD, agent=ORCHESTRATOR, agent_type=MAIN_THREAD, requested_tier="",
        seen=seen, tool_use_times=tool_use_times, skip_sidechain=True,
    )
    prompts: list[Prompt] = []
    versions: set[str] = set()
    stamps: list[datetime] = []
    for line in _iter_lines(path):
        if line.get("timestamp"):
            stamps.append(parse_ts(line["timestamp"]))
        if line.get("version"):
            versions.add(line["version"])
        if line.get("type") != "user" or line.get("isMeta"):
            continue
        text = _prompt_text(line.get("message") or {})
        if text is not None and line.get("timestamp"):
            prompts.append(Prompt(parse_ts(line["timestamp"]), _prompt_kind(text), text))

    agents: dict[str, Agent] = {}
    pending: list[tuple[Agent, Path]] = []
    for meta_path in sorted((root / sid / "subagents").glob("agent-*.meta.json")):
        try:
            meta = json.loads(meta_path.read_text())
        except (OSError, ValueError) as exc:
            raise ValueError(f"malformed subagent metadata {meta_path}: {exc}") from exc
        agent_id = meta_path.name[len("agent-"):-len(".meta.json")]
        agent = Agent(
            agent_id=agent_id, description=str(meta.get("description") or agent_id),
            agent_type=str(meta.get("agentType") or ""), requested_tier=str(meta.get("model") or ""),
            tool_use_id=meta.get("toolUseId"), parent_agent_id=meta.get("parentAgentId"),
            spawn_depth=int(meta.get("spawnDepth") or 1), spawned_at=None,
        )
        agents[agent_id] = agent
        pending.append((agent, meta_path.with_suffix("").with_suffix(".jsonl")))
    for agent, jsonl in pending:
        if jsonl.exists():
            agent.calls = _fold_calls(
                jsonl, thread=agent.agent_id, agent=agent.description, agent_type=agent.agent_type,
                requested_tier=agent.requested_tier, seen=seen, tool_use_times=tool_use_times,
                skip_sidechain=False,
            )
            for call in agent.calls:
                stamps.append(call.timestamp)
                if call.version:
                    versions.add(call.version)
    for agent in agents.values():
        agent.spawned_at = tool_use_times.get(agent.tool_use_id or "") or (
            agent.calls[0].timestamp if agent.calls else None
        )
    # A subagent's subagent belongs to the window in which the orchestrator
    # spawned its depth-1 ancestor, so the whole tree moves together.
    for agent in agents.values():
        ancestor, hops = agent, 0
        while ancestor.parent_agent_id in agents and hops < 16:
            ancestor, hops = agents[ancestor.parent_agent_id], hops + 1
        if ancestor is not agent and ancestor.spawned_at is not None:
            agent.spawned_at = ancestor.spawned_at
    return Session(
        session_id=sid, path=path, main_calls=main_calls, agents=agents, prompts=prompts,
        versions=versions, first_at=min(stamps, default=None), last_at=max(stamps, default=None),
    )


# ---------------------------------------------------------- window & report

def select_calls(session: Session, start: datetime, end: datetime) -> list[Call]:
    picked = [c for c in session.main_calls if start <= c.timestamp < end]
    for agent in session.agents.values():
        if agent.spawned_at is not None and start <= agent.spawned_at < end:
            picked.extend(agent.calls)
    return sorted(picked, key=lambda c: (c.timestamp, c.thread, c.message_id))


@dataclass
class Totals:
    calls: int = 0
    agents: int = 0
    tool_uses: int = 0
    input_tokens: int = 0
    cache_write_5m: int = 0
    cache_write_1h: int = 0
    cache_read: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    context_tokens_sum: int = 0
    peak_context_tokens: int = 0
    cache_hit_ratio: float = 0.0
    cost_input: float = 0.0
    cost_cache_write: float = 0.0
    cost_cache_read: float = 0.0
    cost_output: float = 0.0
    cost_usd: float = 0.0
    cost_uncached_equivalent: float = 0.0
    caching_saving_usd: float = 0.0
    first_call: str | None = None
    last_call: str | None = None
    wall_minutes: float = 0.0
    active_minutes: float = 0.0


def aggregate(calls: list[Call]) -> Totals:
    t = Totals(calls=len(calls), agents=len({c.thread for c in calls}))
    for c in calls:
        cost = cost_of(c)
        t.tool_uses += len(c.tool_names)
        t.input_tokens += c.input_tokens
        t.cache_write_5m += c.cache_write_5m
        t.cache_write_1h += c.cache_write_1h
        t.cache_read += c.cache_read
        t.output_tokens += c.output_tokens
        t.thinking_tokens += c.thinking_tokens
        t.context_tokens_sum += c.context_tokens
        t.peak_context_tokens = max(t.peak_context_tokens, c.context_tokens)
        t.cost_input += cost.input
        t.cost_cache_write += cost.cache_write
        t.cost_cache_read += cost.cache_read
        t.cost_output += cost.output
        t.cost_usd += cost.total
        t.cost_uncached_equivalent += cost.uncached_equivalent
    t.cache_hit_ratio = round(t.cache_read / t.context_tokens_sum, 4) if t.context_tokens_sum else 0.0
    t.caching_saving_usd = t.cost_uncached_equivalent - t.cost_usd
    if calls:
        stamps = sorted(c.timestamp for c in calls)
        t.first_call, t.last_call = fmt_ts(stamps[0], ms=True), fmt_ts(stamps[-1], ms=True)
        t.wall_minutes = round((stamps[-1] - stamps[0]).total_seconds() / 60, 1)
        gaps = (min(b - a, ACTIVE_GAP_CAP) for a, b in zip(stamps, stamps[1:]))
        t.active_minutes = round(sum((g.total_seconds() for g in gaps), 0.0) / 60, 1)
    for name in ("cost_input", "cost_cache_write", "cost_cache_read", "cost_output",
                 "cost_usd", "cost_uncached_equivalent", "caching_saving_usd"):
        setattr(t, name, round(getattr(t, name), 4))
    return t


@dataclass
class ModelRow:
    model: str
    totals: Totals

    @property
    def cost_usd(self) -> float:
        return self.totals.cost_usd


@dataclass
class StageRow:
    stage: str
    agents: int
    models: str
    totals: Totals

    @property
    def cost_usd(self) -> float:
        return self.totals.cost_usd


@dataclass
class AgentRow:
    agent_id: str
    description: str
    stage: str
    requested_tier: str
    models: str
    spawned_at: str | None
    totals: Totals


@dataclass
class Report:
    gw: int
    session_id: str
    session_path: str
    transcripts_root: str
    start: datetime
    end: datetime
    label: str
    calls: list[Call]
    totals: Totals
    by_model: list[ModelRow]
    by_stage: list[StageRow]
    agents: list[AgentRow]
    prompts: list[Prompt]
    versions: list[str]


def build_report(
    session: Session, *, gw: int, start: datetime, end: datetime, label: str = "",
    transcripts_root: Path | None = None,
) -> Report:
    calls = select_calls(session, start, end)
    totals = aggregate(calls)
    by_model = [ModelRow(m, aggregate([c for c in calls if c.model == m])) for m in sorted({c.model for c in calls})]
    stages: list[StageRow] = []
    for stage in _STAGE_ORDER:
        rows = [c for c in calls if c.stage == stage]
        if rows:
            stages.append(StageRow(stage, len({c.thread for c in rows}), ";".join(sorted({c.model for c in rows})), aggregate(rows)))
    threads: dict[str, list[Call]] = {}
    for c in calls:
        threads.setdefault(c.thread, []).append(c)

    def spawn_key(thread: str) -> tuple[int, datetime]:
        if thread == MAIN_THREAD:
            return (0, start)
        agent = session.agents[thread]
        return (1, agent.spawned_at or agent.calls[0].timestamp)

    agents = []
    for thread in sorted(threads, key=spawn_key):
        rows = threads[thread]
        agent = session.agents.get(thread)
        agents.append(AgentRow(
            agent_id=thread, description=rows[0].agent, stage=rows[0].stage,
            requested_tier=rows[0].requested_tier, models=";".join(sorted({c.model for c in rows})),
            spawned_at=fmt_ts(agent.spawned_at, ms=True) if agent and agent.spawned_at else None,
            totals=aggregate(rows),
        ))
    prompts = [p for p in session.prompts if start <= p.timestamp < end]
    return Report(
        gw=gw, session_id=session.session_id, session_path=display_path(session.path),
        transcripts_root=display_path(transcripts_root or session.path.parent), start=start, end=end,
        label=label, calls=calls, totals=totals, by_model=by_model, by_stage=stages, agents=agents,
        prompts=prompts, versions=sorted(session.versions),
    )


# ------------------------------------------------------------------ writing

CALL_COLUMNS = (
    "timestamp", "thread", "agent", "stage", "model", "requested_tier", "effort", "stop_reason",
    "input_tokens", "cache_write_5m", "cache_write_1h", "cache_read", "output_tokens", "thinking_tokens",
    "context_tokens", "cost_input", "cost_cache_write", "cost_cache_read", "cost_output", "cost_usd",
    "cost_uncached_equiv", "tool_uses", "tool_names", "message_id", "request_id", "version", "lines",
)


def _call_row(c: Call) -> dict:
    cost = cost_of(c)
    return {
        "timestamp": fmt_ts(c.timestamp, ms=True), "thread": c.thread, "agent": c.agent, "stage": c.stage,
        "model": c.model, "requested_tier": c.requested_tier, "effort": c.effort or "",
        "stop_reason": c.stop_reason or "", "input_tokens": c.input_tokens, "cache_write_5m": c.cache_write_5m,
        "cache_write_1h": c.cache_write_1h, "cache_read": c.cache_read, "output_tokens": c.output_tokens,
        "thinking_tokens": c.thinking_tokens, "context_tokens": c.context_tokens,
        "cost_input": round(cost.input, 6), "cost_cache_write": round(cost.cache_write, 6),
        "cost_cache_read": round(cost.cache_read, 6), "cost_output": round(cost.output, 6),
        "cost_usd": round(cost.total, 6), "cost_uncached_equiv": round(cost.uncached_equivalent, 6),
        "tool_uses": len(c.tool_names), "tool_names": ";".join(c.tool_names), "message_id": c.message_id,
        "request_id": c.request_id or "", "version": c.version or "", "lines": c.lines,
    }


def _n(value: int | float) -> str:
    return f"{value:,.0f}" if isinstance(value, int) else f"{value:,.1f}"


def _usd(value: float) -> str:
    return f"{value:,.2f}"


def preview_text(text: str) -> str:
    one_line = _SECRET_SHAPES.sub(REDACTED, " ".join(text.split()))
    return one_line if len(one_line) <= PROMPT_PREVIEW else one_line[: PROMPT_PREVIEW - 1] + "…"


_preview = preview_text


def display_path(path: Path | str) -> str:
    """Home-relative spelling for paths written into committed ledgers."""
    path = Path(path)
    try:
        return "~/" + str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)


def render_markdown(report: Report) -> str:
    t = report.totals
    lines = [f"# GW{report.gw} — Claude Code usage" + (f" ({report.label})" if report.label else ""), ""]
    lines += ["## 1. Window", "", "| Field | Value |", "|---|---|",
              f"| Gameweek | {report.gw} |", f"| Session | `{report.session_id}` |",
              f"| Transcripts root | `{report.transcripts_root}` |",
              f"| Start (inclusive, UTC) | {fmt_ts(report.start)} |", f"| End (exclusive, UTC) | {fmt_ts(report.end)} |",
              f"| Claude Code versions | {', '.join(report.versions) or '-'} |",
              f"| Models | {', '.join(m.model for m in report.by_model) or '-'} |", ""]
    lines += ["## 2. Totals", "", "| Metric | Value |", "|---|---|",
              f"| API calls | {_n(t.calls)} |", f"| Agent threads (incl. orchestrator) | {_n(t.agents)} |",
              f"| Tool calls | {_n(t.tool_uses)} |", f"| First → last call | {t.first_call or '-'} → {t.last_call or '-'} |",
              f"| Wall-clock minutes | {_n(t.wall_minutes)} |", f"| Active minutes (gaps capped at 5) | {_n(t.active_minutes)} |",
              f"| Input tokens (uncached) | {_n(t.input_tokens)} |", f"| Cache write 5m / 1h | {_n(t.cache_write_5m)} / {_n(t.cache_write_1h)} |",
              f"| Cache read | {_n(t.cache_read)} |", f"| Output tokens | {_n(t.output_tokens)} |",
              f"| of which thinking | {_n(t.thinking_tokens)} |", f"| Peak context (one call) | {_n(t.peak_context_tokens)} |",
              f"| Cache hit ratio | {t.cache_hit_ratio:.3f} |",
              f"| Cost $ (input / cache write / cache read / output) | {_usd(t.cost_input)} / {_usd(t.cost_cache_write)} / {_usd(t.cost_cache_read)} / {_usd(t.cost_output)} |",
              f"| **Cost $ total** | **{_usd(t.cost_usd)}** |", f"| Uncached-equivalent $ | {_usd(t.cost_uncached_equivalent)} |",
              f"| Saved by caching $ | {_usd(t.caching_saving_usd)} |", ""]
    lines += ["## 3. By model", "", "| Model | Calls | Input | Cache write | Cache read | Output | Cost $ |", "|---|---|---|---|---|---|---|"]
    for m in report.by_model:
        mt = m.totals
        lines.append(f"| {m.model} | {_n(mt.calls)} | {_n(mt.input_tokens)} | {_n(mt.cache_write_5m + mt.cache_write_1h)} | {_n(mt.cache_read)} | {_n(mt.output_tokens)} | {_usd(mt.cost_usd)} |")
    lines += ["", "## 4. By stage", "", "| Stage | Agents | Models | Calls | Wall min | Peak context | Output | Cost $ |", "|---|---|---|---|---|---|---|---|"]
    for s in report.by_stage:
        st = s.totals
        lines.append(f"| {s.stage} | {s.agents} | {s.models} | {_n(st.calls)} | {_n(st.wall_minutes)} | {_n(st.peak_context_tokens)} | {_n(st.output_tokens)} | {_usd(st.cost_usd)} |")
    lines += ["", "## 5. By agent", "", "Spawn order; the orchestrator first.", "",
              "| Spawned | Agent | Stage | Tier → model | Calls | Wall min | Peak context | Output | Cost $ |", "|---|---|---|---|---|---|---|---|---|"]
    for a in report.agents:
        at = a.totals
        lines.append(f"| {a.spawned_at or '-'} | {a.description} | {a.stage} | {a.requested_tier or 'main'} → {a.models} | {_n(at.calls)} | {_n(at.wall_minutes)} | {_n(at.peak_context_tokens)} | {_n(at.output_tokens)} | {_usd(at.cost_usd)} |")
    lines += ["", "## 6. Prompts in window", "", "| Time | Kind | Text |", "|---|---|---|"]
    for p in report.prompts:
        lines.append(f"| {fmt_ts(p.timestamp)} | {p.kind} | {_preview(p.text).replace('|', '\\|')} |")
    lines += ["", "## 7. Pricing and method", "", f"Anthropic list price, USD per 1M tokens, as of {PRICING_DATE}.", "",
              "| Model | Input | Output | Cache write 5m | Cache write 1h | Cache read |", "|---|---|---|---|---|---|"]
    for key in sorted(PRICES):
        inp, out, w5, w1, rd = PRICES[key]
        lines.append(f"| {key} | {inp} | {out} | {w5} | {w1} | {rd} |")
    lines += ["",
              "- Costs are API list-price equivalents; a subscription is not billed at these rates.",
              "- One row per API call (message id). Claude Code writes one transcript line per content block; output tokens are the max across a call's lines.",
              "- Subagent calls belong to the window in which the orchestrator spawned them.",
              "- `/compact` summarisation calls are not logged in transcripts and are not counted.",
              "- Cache hit ratio = cache read ÷ (input + cache read + cache write).",
              "- Uncached-equivalent prices every context token at the input rate; the difference is what prompt caching saved.",
              ""]
    return "\n".join(lines)


def report_dict(report: Report) -> dict:
    return {
        "schema_version": 1,
        "window": {
            "gw": report.gw, "label": report.label, "session_id": report.session_id,
            "session_path": report.session_path, "transcripts_root": report.transcripts_root,
            "start": fmt_ts(report.start), "end": fmt_ts(report.end),
            "claude_code_versions": report.versions,
        },
        "totals": asdict(report.totals),
        "by_model": [{"model": m.model, **asdict(m.totals)} for m in report.by_model],
        "by_stage": [{"stage": s.stage, "agents": s.agents, "models": s.models, **asdict(s.totals)} for s in report.by_stage],
        "agents": [{**{k: v for k, v in asdict(a).items() if k != "totals"}, **asdict(a.totals)} for a in report.agents],
        "prompts": [{"timestamp": fmt_ts(p.timestamp), "kind": p.kind, "text": _preview(p.text)} for p in report.prompts],
        "pricing": {"as_of": PRICING_DATE, "usd_per_mtok": {
            k: dict(zip(("input", "output", "cache_write_5m", "cache_write_1h", "cache_read"), v)) for k, v in PRICES.items()
        }},
    }


def write_report(report: Report, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    md, js, cs = out_dir / "usage.md", out_dir / "usage.json", out_dir / "calls.csv"
    md.write_text(render_markdown(report))
    js.write_text(json.dumps(report_dict(report), indent=1) + "\n")
    with cs.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CALL_COLUMNS)
        writer.writeheader()
        for call in report.calls:
            writer.writerow(_call_row(call))
    return [md, js, cs]


# ------------------------------------------------------- list & inspect

@dataclass
class SessionSummary:
    session_id: str
    path: Path
    first_at: datetime | None
    last_at: datetime | None
    first_prompt: str
    human_prompts: int
    agents: int
    gw_tags: set[int]


def latest_ledger_end(cost_root: Path, *, before_gw: int) -> tuple[datetime, Path] | None:
    """Window end of the most recently processed ledger for an earlier
    gameweek: sessions that ended before it cannot hold a later cycle."""
    best: tuple[datetime, Path] | None = None
    for path in sorted(cost_root.glob("gw*/usage.json")):
        try:
            window = json.loads(path.read_text())["window"]
            gw, end = int(window["gw"]), parse_ts(str(window["end"]))
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if gw < before_gw and (best is None or end > best[0]):
            best = (end, path)
    return best


def list_sessions(root: Path, since: datetime | None = None) -> list[SessionSummary]:
    """Sessions under root, newest first. With `since`, only sessions still
    active at or after it; files last written before it are skipped unread."""
    rows = []
    for path in root.glob("*.jsonl"):
        if since is not None and datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc) < since:
            continue
        first = last = None
        first_prompt, humans = "", 0
        for line in _iter_lines(path):
            when = line.get("timestamp")
            if when:
                stamp = parse_ts(when)
                first = stamp if first is None or stamp < first else first
                last = stamp if last is None or stamp > last else last
            if line.get("type") == "user" and not line.get("isMeta"):
                text = _prompt_text(line.get("message") or {})
                if text is not None and _prompt_kind(text) == "human":
                    humans += 1
                    first_prompt = first_prompt or _preview(text)
        if since is not None and (last is None or last < since):
            continue
        tags: set[int] = set()
        agents = 0
        for meta_path in (root / path.stem / "subagents").glob("agent-*.meta.json"):
            try:
                description = json.loads(meta_path.read_text()).get("description") or ""
            except (OSError, ValueError):
                continue
            agents += 1
            tags |= gw_tags(str(description))
        rows.append(SessionSummary(path.stem, path, first, last, first_prompt, humans, agents, tags))
    return sorted(rows, key=lambda r: (r.first_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)


@dataclass(frozen=True)
class Window:
    start: datetime
    end: datetime
    rule: str


def suggest_window(session: Session, gw: int) -> Window | None:
    """Heuristic only: the human prompt preceding the first GW-tagged agent
    spawn, to the first human prompt after the last such agent finished."""
    tagged = [a for a in session.agents.values() if gw in gw_tags(a.description) and a.spawned_at]
    if not tagged:
        return None
    first_spawn = min(a.spawned_at for a in tagged)
    finished = max(a.last_call_at or a.spawned_at for a in tagged)
    humans = [p for p in session.prompts if p.kind == "human"]
    before = [p.timestamp for p in humans if p.timestamp <= first_spawn]
    after = [p.timestamp for p in humans if p.timestamp > finished]
    start = max(before) if before else first_spawn
    end = min(after) if after else (session.last_at or finished) + timedelta(seconds=1)
    return Window(start, end, "prompt before first GW-tagged spawn → first human prompt after the last GW-tagged agent finished")


def inspect_session(session: Session, gw: int) -> str:
    lines = [f"session {session.session_id}", f"  span      {fmt_ts(session.first_at) if session.first_at else '-'} → {fmt_ts(session.last_at) if session.last_at else '-'}",
             f"  versions  {', '.join(sorted(session.versions)) or '-'}",
             f"  calls     main {len(session.main_calls)}, agents {len(session.agents)}", "", "timeline (UTC)"]
    events: list[tuple[datetime, str]] = []
    for p in session.prompts:
        if p.kind in ("human", "compact", "continuation", "interrupt"):
            events.append((p.timestamp, f"{p.kind:<9} {_preview(p.text)}"))
    for a in sorted(session.agents.values(), key=lambda a: a.spawned_at or datetime.max.replace(tzinfo=timezone.utc)):
        tags = ",".join(f"GW{n}" for n in sorted(gw_tags(a.description))) or "-"
        when = a.spawned_at
        last = fmt_ts(a.last_call_at) if a.last_call_at else "-"
        events.append((when or datetime.max.replace(tzinfo=timezone.utc),
                       f"{'spawn':<9} [{a.requested_tier or '?':<5}] {a.description}  tags={tags} calls={len(a.calls)} last={last}"))
    for when, text in sorted(events, key=lambda e: e[0]):
        stamp = fmt_ts(when) if when != datetime.max.replace(tzinfo=timezone.utc) else "unknown             "
        lines.append(f"  {stamp}  {text}")
    window = suggest_window(session, gw)
    lines.append("")
    if window is None:
        lines.append(f"suggested window for GW{gw}: none (no agent description tagged GW{gw})")
    else:
        lines += [f"suggested window for GW{gw}: --start {fmt_ts(window.start)} --end {fmt_ts(window.end)}",
                  f"  rule: {window.rule}",
                  "  check: extend --end past the cycle-commit turn if the next prompt is the commit"]
    return "\n".join(lines) + "\n"
