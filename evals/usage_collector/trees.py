"""Transcript trees for the live usage-collector cases, built in a temp
directory at test time. Real cycles come from the committed skeletons; the
traps are synthetic sessions in the shape Claude Code writes."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from evals.usage_collector.skeleton import SKELETON_ROOT
from fpl.usage import SYNTHETIC_MODEL, fmt_ts, parse_ts

GW4_SID = "8cbbfa17-efba-4c69-9b95-2d4a448b3b78"
GW5_SID = "8f06c38d-49f9-43f1-9887-0ebf72e60800"
GW4_RESUMED_SID = "f7e99747-b438-4ae1-a41d-784a327c0acd"
GW6_SID = "19d99f5c-a2a6-486b-8614-b36040777608"
FABLE = "claude-fable-5-1"
HAIKU = "claude-haiku-4-5-20251001"
UNPRICED = "claude-nova-9"
# Window end of the synthetic GW6 ledger every GW7 case starts from.
GW6_LEDGER_END = "2026-10-09T15:00:00Z"
GW7_LEDGER = json.dumps({"schema_version": 1, "window": {"gw": 6, "end": GW6_LEDGER_END}}).encode()


@dataclass(frozen=True)
class Agent:
    agent_id: str
    description: str
    tool_use_id: str
    tier: str
    lines: tuple[dict, ...]


def human(when: str, text: str) -> dict:
    return {"type": "user", "timestamp": when, "message": {"role": "user", "content": text}}


def assistant(when: str, mid: str, *, model: str = FABLE, tools: tuple[dict, ...] = (),
              usage: dict | None = None) -> dict:
    return {
        "type": "assistant", "timestamp": when, "requestId": f"req_{mid}", "version": "2.1.280",
        "message": {
            "id": mid, "model": model, "stop_reason": "tool_use" if tools else "end_turn",
            "usage": usage or {"input_tokens": 2, "output_tokens": 300, "cache_read_input_tokens": 40_000,
                               "cache_creation_input_tokens": 1_000},
            "content": list(tools) or [{"type": "text", "text": "ok"}],
        },
    }


def spawn(when: str, mid: str, tool_use_id: str, description: str, *, model: str = FABLE) -> dict:
    return assistant(when, mid, model=model, tools=(
        {"type": "tool_use", "id": tool_use_id, "name": "Agent", "input": {"description": description}},))


def commit(when: str, mid: str, subject: str, *, model: str = FABLE) -> dict:
    command = f"git add -A && git commit -q -F - <<'EOF'\n{subject}\nEOF"
    return assistant(when, mid, model=model, tools=(
        {"type": "tool_use", "id": f"tu_{mid}", "name": "Bash", "input": {"command": command}},))


def write_session(root: Path, sid: str, lines: list[dict], agents: tuple[Agent, ...] = ()) -> None:
    _write_jsonl(root / f"{sid}.jsonl", lines)
    for agent in agents:
        folder = root / sid / "subagents"
        folder.mkdir(parents=True, exist_ok=True)
        meta = {"agentType": "general-purpose", "description": agent.description,
                "toolUseId": agent.tool_use_id, "spawnDepth": 1, "model": agent.tier}
        (folder / f"agent-{agent.agent_id}.meta.json").write_text(json.dumps(meta))
        _write_jsonl(folder / f"agent-{agent.agent_id}.jsonl", list(agent.lines))


def copy_skeleton(root: Path, sid: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SKELETON_ROOT / f"{sid}.jsonl", root / f"{sid}.jsonl")
    if (SKELETON_ROOT / sid).is_dir():
        shutil.copytree(SKELETON_ROOT / sid, root / sid)


def at(base: str, minutes: float) -> str:
    return fmt_ts(parse_ts(base) + timedelta(minutes=minutes))


def cycle(root: Path, sid: str, gw: int, base: str, *, tail: list[dict] | None = None,
          model: str = FABLE, agent_model: str = HAIKU, prefix: str = "") -> None:
    """A complete GW{gw} cycle: prompt, data collection and squad optimizer
    spawns, an orchestrator turn, "Commit the changes.", the gw{gw}: commit.
    `tail` follows the commit."""
    p = prefix or sid[:4]
    lines = [
        human(base, "Run for next gameweek."),
        spawn(at(base, 0.2), f"{p}m1", f"{p}tu1", f"GW{gw} data collection", model=model),
        spawn(at(base, 10), f"{p}m2", f"{p}tu2", f"GW{gw} squad optimizer", model=model),
        assistant(at(base, 16), f"{p}m3", model=model),
        human(at(base, 20), "Commit the changes."),
        commit(at(base, 20.5), f"{p}m4", f"gw{gw}: bank the FT", model=model),
        *(tail or []),
    ]
    agents = (
        Agent(f"{p}a1", f"GW{gw} data collection", f"{p}tu1", "haiku",
              (assistant(at(base, 1), f"{p}h1", model=agent_model),
               assistant(at(base, 3), f"{p}h2", model=agent_model))),
        Agent(f"{p}a2", f"GW{gw} squad optimizer", f"{p}tu2", "fable",
              (assistant(at(base, 11), f"{p}f1", model=model),
               assistant(at(base, 15), f"{p}f2", model=model))),
    )
    write_session(root, sid, lines, agents)


# ------------------------------------------------------------------ cases

def build_c1(root: Path) -> None:
    """GW4: the real cycle, the real GW5 session carrying the GW4 retro and
    usage ledger, and a resumed copy of the GW4 main thread with no agents."""
    copy_skeleton(root, GW4_SID)
    copy_skeleton(root, GW5_SID)
    shutil.copyfile(root / f"{GW4_SID}.jsonl", root / f"{GW4_RESUMED_SID}.jsonl")


def build_c2(root: Path) -> None:
    """GW5: the real cycle, the real GW4 session, and a stand-in for the GW6
    session that carries the GW5 retro."""
    copy_skeleton(root, GW5_SID)
    copy_skeleton(root, GW4_SID)
    base = "2026-10-09T13:30:00Z"
    write_session(root, GW6_SID, [
        human(base, "Run for next gameweek."),
        spawn(at(base, 0.2), "g6m1", "g6tu1", "GW5 retro analysis"),
        spawn(at(base, 5), "g6m2", "g6tu2", "GW6 data collection"),
        spawn(at(base, 20), "g6m3", "g6tu3", "GW6 squad optimizer"),
    ], (
        Agent("g6a1", "GW5 retro analysis", "g6tu1", "opus", (assistant(at(base, 1), "g6o1", model="claude-opus-5"),)),
        Agent("g6a2", "GW6 data collection", "g6tu2", "haiku", (assistant(at(base, 6), "g6h1", model=HAIKU),)),
        Agent("g6a3", "GW6 squad optimizer", "g6tu3", "fable", (assistant(at(base, 21), "g6f1"),)),
    ))


S1_A = "a1a1a1a1-0000-4000-8000-000000000001"
S1_B = "b2b2b2b2-0000-4000-8000-000000000002"


def build_s1(root: Path) -> None:
    """No GW7 cycle: a GW6 cycle, and the session that opened GW8 with the GW7
    retro and usage ledger."""
    cycle(root, S1_A, 6, "2026-10-10T09:00:00Z")
    base = "2026-10-23T09:00:00Z"
    write_session(root, S1_B, [
        human(base, "Run for next gameweek."),
        spawn(at(base, 0.2), "s1m1", "s1tu1", "GW7 retro analysis"),
        spawn(at(base, 5), "s1m2", "s1tu2", "GW7 usage ledger"),
    ], (
        Agent("s1a1", "GW7 retro analysis", "s1tu1", "opus", (assistant(at(base, 1), "s1o1", model="claude-opus-5"),)),
        Agent("s1a2", "GW7 usage ledger", "s1tu2", "haiku", (assistant(at(base, 6), "s1h1", model=HAIKU),)),
    ))


S2_A = "c3c3c3c3-0000-4000-8000-000000000003"
S2_B = "d4d4d4d4-0000-4000-8000-000000000004"


def build_s2(root: Path) -> None:
    """Two sessions that each ran a full GW7 cycle."""
    cycle(root, S2_A, 7, "2026-10-16T09:00:00Z", tail=[human("2026-10-16T09:40:00Z", "thanks")])
    cycle(root, S2_B, 7, "2026-10-16T18:00:00Z", tail=[human("2026-10-16T18:40:00Z", "thanks")])


S3_SID = "e5e5e5e5-0000-4000-8000-000000000005"
S3_BASE = "2026-10-16T09:00:00Z"
S3_FOLLOW_UP = "2026-10-16T09:25:00Z"


def build_s3(root: Path) -> None:
    """The prompt after the cycle commit mentions commit and push: the CLI's
    end already counts the commit turn and must be used as printed."""
    cycle(root, S3_SID, 7, S3_BASE, tail=[human(S3_FOLLOW_UP, "commit and push done?"),
                                          assistant("2026-10-16T09:25:10Z", "e5m9")])


def build_s3b(root: Path) -> None:
    """As S3 with nothing after the commit: the end is the last line plus one second."""
    cycle(root, S3_SID, 7, S3_BASE)


S4_SID = "f6f6f6f6-0000-4000-8000-000000000006"


def build_s4(root: Path) -> None:
    """A GW7 spawn whose agent never made an API call, in a main thread whose
    only responses are synthetic: the window holds no calls."""
    base = "2026-10-16T09:00:00Z"
    write_session(root, S4_SID, [
        human(base, "Run for next gameweek."),
        spawn(at(base, 0.2), "f6m1", "f6tu1", "GW7 data collection", model=SYNTHETIC_MODEL),
        assistant(at(base, 2), "f6m2", model=SYNTHETIC_MODEL),
        human(at(base, 10), "Is it done?"),
    ], (Agent("f6a1", "GW7 data collection", "f6tu1", "haiku",
              ({"type": "user", "timestamp": at(base, 0.3), "message": {"role": "user", "content": "go"}},)),))


S5_SID = "a7a7a7a7-0000-4000-8000-000000000007"


def build_s5(root: Path) -> None:
    """A GW7 cycle run on a model with no list price."""
    cycle(root, S5_SID, 7, "2026-10-16T09:00:00Z", model=UNPRICED, agent_model=UNPRICED,
          tail=[human("2026-10-16T09:40:00Z", "thanks")])


S6_REAL = "b8b8b8b8-0000-4000-8000-000000000008"
S6_RESUMED = "c9c9c9c9-0000-4000-8000-000000000009"
S6_SHIFT = timedelta(days=9)


def build_s6(root: Path) -> None:
    """A GW7 cycle that ended before the GW6 ledger cutoff, and a resumed copy
    of its main thread (same message ids, later timestamps, no agents) after
    it. Only the copy is listed by default, untagged."""
    cycle(root, S6_REAL, 7, "2026-10-08T09:00:00Z", tail=[human("2026-10-08T09:40:00Z", "thanks")])
    lines = [json.loads(raw) for raw in (root / f"{S6_REAL}.jsonl").read_text().splitlines()]
    for line in lines:
        line["timestamp"] = _shift(line["timestamp"], S6_SHIFT)
    _write_jsonl(root / f"{S6_RESUMED}.jsonl", lines)


def _shift(when: str, delta: timedelta) -> str:
    return fmt_ts(parse_ts(when) + delta)


def _write_jsonl(path: Path, lines: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(line) + "\n" for line in lines))

