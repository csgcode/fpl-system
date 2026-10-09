"""Usage-collector eval cases: the recorded GW4 ledger run (replay) and the
headless scenarios (live). Each live case is a transcript tree built at test
time plus the ledgers already under data/cost/."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from evals.harness.workspace import RepoFile
from evals.usage_collector import trees

AGENT = "usage-collector"
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "evals" / "fixtures" / "usage_collector"

WRITE, WRITE_FAILS, STOP = "write", "write-fails", "stop"


@dataclass(frozen=True)
class Expect:
    """`outcome`: WRITE (one write, exit 0), WRITE_FAILS (one write that exits
    `write_exit`, then STOP) or STOP (no write)."""

    outcome: str
    candidates: tuple[str, ...] = ()
    session: str | None = None
    start: str | None = None
    end: str | None = None
    calls_line: str | None = None
    write_exit: int | None = None
    error: str | None = None
    stop_phrases: tuple[str, ...] = ()
    backlog_model: str | None = None


@dataclass(frozen=True)
class ReplayCase:
    name: str
    fixture: Path
    source: str
    gw: int
    expect: Expect


REPLAY_CASES: tuple[ReplayCase, ...] = (
    ReplayCase(
        "gw4", FIXTURES / "replay" / "gw4-ad256df23a6b4e90b.jsonl",
        "8f06c38d-49f9-43f1-9887-0ebf72e60800/subagents/agent-ad256df23a6b4e90b.jsonl", 4,
        Expect(WRITE, candidates=("8f06c38d", "8cbbfa17"), session=trees.GW4_SID,
               start="2026-09-11T17:56:17Z", end="2026-09-11T19:00:52Z"),
    ),
)


def _ledgers(*gws: int) -> dict[str, RepoFile]:
    return {f"data/cost/gw{gw}/{name}": RepoFile(f"data/cost/gw{gw}/{name}")
            for gw in gws for name in ("usage.md", "usage.json", "calls.csv")}


GW7_LEDGERS: Mapping[str, bytes] = {"data/cost/gw6/usage.json": trees.GW7_LEDGER}
NO_GW7 = "no session tagged GW7"


@dataclass(frozen=True)
class LiveCase:
    id: str
    gw: int
    build: Callable[[Path], None]
    ledgers: Mapping[str, RepoFile | bytes]
    expect: Expect
    live: bool = True


LIVE_CASES: tuple[LiveCase, ...] = (
    LiveCase("C1", 4, trees.build_c1, _ledgers(1, 2, 3), Expect(
        WRITE, candidates=("8cbbfa17",), session=trees.GW4_SID,
        start="2026-09-11T17:56:17Z", end="2026-09-11T19:00:52Z",
        calls_line="calls: 237  agents: 13  wall: 63.2 min  cost: $32.76")),
    LiveCase("C2", 5, trees.build_c2, _ledgers(1, 2, 3, 4), Expect(
        WRITE, candidates=("8f06c38d",), session=trees.GW5_SID,
        start="2026-09-18T12:47:49Z", end="2026-09-18T20:53:35Z",
        calls_line="calls: 485  agents: 20  wall: 482.0 min  cost: $48.70")),
    LiveCase("S1", 7, trees.build_s1, GW7_LEDGERS, Expect(
        STOP, stop_phrases=(NO_GW7, trees.GW6_LEDGER_END))),
    LiveCase("S2", 7, trees.build_s2, GW7_LEDGERS, Expect(
        STOP, candidates=(trees.S2_B[:8], trees.S2_A[:8]),
        stop_phrases=(trees.S2_A[:8], trees.S2_B[:8]))),
    LiveCase("S3", 7, trees.build_s3, GW7_LEDGERS, Expect(
        WRITE, candidates=(trees.S3_SID[:8],), session=trees.S3_SID,
        start=trees.S3_BASE, end=trees.S3_FOLLOW_UP)),
    LiveCase("S3b", 7, trees.build_s3b, GW7_LEDGERS, Expect(
        WRITE, candidates=(trees.S3_SID[:8],), session=trees.S3_SID,
        start=trees.S3_BASE, end="2026-10-16T09:20:31Z"), live=False),
    LiveCase("S4", 7, trees.build_s4, GW7_LEDGERS, Expect(
        WRITE_FAILS, candidates=(trees.S4_SID[:8],), session=trees.S4_SID,
        start="2026-10-16T09:00:00Z", end="2026-10-16T09:10:00Z", write_exit=2,
        error="no API calls between 2026-10-16T09:00:00Z and 2026-10-16T09:10:00Z")),
    LiveCase("S5", 7, trees.build_s5, GW7_LEDGERS, Expect(
        WRITE_FAILS, candidates=(trees.S5_SID[:8],), session=trees.S5_SID,
        start="2026-10-16T09:00:00Z", end="2026-10-16T09:40:00Z", write_exit=1,
        error="no list price for model 'claude-nova-9'", backlog_model=trees.UNPRICED)),
    LiveCase("S6", 7, trees.build_s6, GW7_LEDGERS, Expect(STOP, stop_phrases=(NO_GW7,))),
)
