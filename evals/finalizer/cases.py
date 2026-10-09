"""Finalizer eval cases: the recorded GW4–GW6 runs (replay) and the headless
scenarios (live). Inputs are files at cycle commits, or local bootstrap
archives pinned by sha256, so a case is a manifest rather than a copy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from evals.harness.workspace import GitBlob, RepoFile

AGENT = "finalizer"
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "evals" / "fixtures" / AGENT
TEAM_ID = 8455344

ASSEMBLE = "assemble"
REOPEN = "reopen"
CORRECTION = "correction"

STOP_REOPEN = "REOPEN"
STOP_STALE = "STALE"
STOP_NO_BASELINE = "NO-BASELINE"
STOP_FINAL_EXISTS = "FINAL-EXISTS"
STOP_PROPOSAL = "PROPOSAL"
STOP_VALUE_DRIFT = "VALUE-DRIFT"

Source = RepoFile | GitBlob


def archive(gw: int, stamp: str, sha256: str) -> RepoFile:
    return RepoFile(f"data/raw/gw{gw}/.archive/bootstrap-{stamp}.json", sha256)


GW4_BASELINE = archive(4, "20260911T175839_804484Z",
                       "5b6b93ce540fc630f798edb05ddda4ef0c04d214847a2a47d3bd5eb7073db4da")
GW4_GATE = GitBlob("db2ab51", "data/raw/gw4/bootstrap.json")
GW5_BASELINE = archive(5, "20260918T124957_221963Z",
                       "12a1b4e9718bc62d73834004cb02fe49f7f1396e5bda93225533fc7b54ef6a45")
GW5_REOPEN_GATE = archive(5, "20260918T151953_303197Z",
                          "84715852f9548729a8cb59734938c922792fcf33773f916467bbd988e1225d2e")
GW5_RERUN_GATE = GitBlob("571f5b0", "data/raw/gw5/bootstrap.json")
GW6_BASELINE = archive(6, "20261009T133149_122429Z",
                       "8fc3aff56d653b059faf3e83d790ebecf221ac969479f8f1e91c4edfda0544b4")
GW6_GATE = GitBlob("b28927f", "data/raw/gw6/bootstrap.json")


@dataclass(frozen=True)
class ReplayCase:
    """`cycle_commit` holds the proposal, review, EP files and the final.md
    the run wrote; for a correction it is the record before the run and
    `after_commit` the record after it."""

    name: str
    fixture: Path
    source: str
    gw: int
    kind: str
    cycle_commit: str
    previous_commit: str
    baseline: Source | None
    gate: Source | None
    after_commit: str | None = None
    suggestions_exists: bool = True

    def decision(self, name: str, *, gw: int | None = None) -> str:
        return f"data/decisions/gw{self.gw if gw is None else gw}/{name}"


REPLAY_CASES: tuple[ReplayCase, ...] = (
    ReplayCase("gw4", FIXTURES / "gw4.jsonl",
               "8cbbfa17-efba-4c69-9b95-2d4a448b3b78/subagents/agent-a682947f873f377d0.jsonl",
               4, ASSEMBLE, "db2ab51", "82ad6da", GW4_BASELINE, GW4_GATE),
    ReplayCase("gw5-reopen", FIXTURES / "gw5-reopen.jsonl",
               "8f06c38d-49f9-43f1-9887-0ebf72e60800/subagents/agent-ac3f9e98e006d4894.jsonl",
               5, REOPEN, "571f5b0", "db2ab51", GW5_BASELINE, GW5_REOPEN_GATE),
    ReplayCase("gw5-rerun", FIXTURES / "gw5-rerun.jsonl",
               "8f06c38d-49f9-43f1-9887-0ebf72e60800/subagents/agent-a12b4db1e05f049cd.jsonl",
               5, ASSEMBLE, "571f5b0", "db2ab51", GW5_REOPEN_GATE, GW5_RERUN_GATE),
    ReplayCase("gw6", FIXTURES / "gw6.jsonl",
               "19d99f5c-a2a6-486b-8614-b36040777608/subagents/agent-af72f0cca52222b7a.jsonl",
               6, ASSEMBLE, "b28927f", "b965a64", GW6_BASELINE, GW6_GATE),
    ReplayCase("gw5-correction", FIXTURES / "gw5-correction.jsonl",
               "8f06c38d-49f9-43f1-9887-0ebf72e60800/subagents/agent-a65a2f68ab55cc42b.jsonl",
               5, CORRECTION, "571f5b0", "db2ab51", None, GW5_RERUN_GATE,
               after_commit="b965a64"),
)

SPEC_FIXTURE = FIXTURES / "spec-ff65c63.md"
SPEC_COMMIT = "ff65c63"
SPEC_PATH = "agents/finalizer.md"


# --- live -------------------------------------------------------------------


@dataclass(frozen=True)
class Replace:
    """A literal edit to a placed file that must match exactly once."""

    path: str
    old: str
    new: str


@dataclass(frozen=True)
class FlagEdit:
    """Changes one player's flag fields in the gate-time recording."""

    player_id: int
    status: str
    chance: int | None
    news: str


@dataclass(frozen=True)
class LiveCase:
    """`gate_now` is the instant the gate's refresh is replayed at, and
    `baseline_at` when the analysis-time bootstrap was fetched (None removes
    the baseline). `budget` is the my-team budget in £m; None means no auth."""

    id: str
    gw: int
    kind: str
    commit: str
    baseline: Source
    gate: Source
    gate_now: str
    baseline_at: str | None
    budget: float | None = None
    stop: str | None = None
    edits: tuple[Replace, ...] = ()
    flag_edit: FlagEdit | None = None
    keep_final: bool = False
    case_lines: tuple[str, ...] = ()
    extra: tuple[tuple[str, Source], ...] = ()
    default: bool = False

    @property
    def auth(self) -> bool:
        return self.budget is not None or self.stop == STOP_FINAL_EXISTS

    def decision(self, name: str, *, gw: int | None = None) -> str:
        return f"data/decisions/gw{self.gw if gw is None else gw}/{name}"


GW6_PROPOSAL = "data/decisions/gw6/squad-proposal.md"
GW6_NOW = "2026-10-09T14:17:28+00:00"
GW6_BASELINE_AT = "2026-10-09T13:31:49+00:00"
_GW6 = dict(gw=6, kind=ASSEMBLE, commit="b28927f", baseline=GW6_BASELINE, gate=GW6_GATE,
            gate_now=GW6_NOW, baseline_at=GW6_BASELINE_AT, budget=99.2)

LIVE_CASES: tuple[LiveCase, ...] = (
    LiveCase("L1-gw6-pass", **_GW6, default=True),
    LiveCase("L2-gw5-reopen", 5, REOPEN, "571f5b0", GW5_BASELINE, GW5_REOPEN_GATE,
             "2026-09-18T15:19:53+00:00", "2026-09-18T12:49:57+00:00", default=True),
    LiveCase("L3-gw4-pass", 4, ASSEMBLE, "db2ab51", GW4_BASELINE, GW4_GATE,
             "2026-09-11T18:54:16+00:00", "2026-09-11T17:58:39+00:00", default=True),
    LiveCase("L4-gw5-rerun", 5, ASSEMBLE, "571f5b0", GW5_REOPEN_GATE, GW5_RERUN_GATE,
             "2026-09-18T15:37:37+00:00", "2026-09-18T15:19:53+00:00", budget=99.3,
             case_lines=("This run follows a REOPEN; the affected analysis and the "
                         "proposal were re-run.",), default=True),
    LiveCase("P1-incoming-flag", **_GW6,
             flag_edit=FlagEdit(124, "d", 75, "Knock - 75% chance of playing")),
    LiveCase("P2-final-exists", **_GW6 | {"stop": STOP_FINAL_EXISTS}, keep_final=True),
    LiveCase("P3-dropped-row", **_GW6 | {"stop": STOP_PROPOSAL},
             edits=(Replace(GW6_PROPOSAL, "__S2_ROW__", ""),)),
    LiveCase("P4-malformed-state", **_GW6 | {"stop": STOP_PROPOSAL},
             edits=(Replace(GW6_PROPOSAL, "\nbank: 0.3\n", "\nbank 0.3\n"),)),
    LiveCase("P5-stale", **_GW6 | {"stop": STOP_STALE,
                                   "baseline_at": "2026-10-08T08:17:28+00:00"}),
    LiveCase("P6-no-baseline", **_GW6 | {"stop": STOP_NO_BASELINE, "baseline_at": None}),
    LiveCase("P7-value-drift", **_GW6 | {"stop": STOP_VALUE_DRIFT, "budget": 99.1}),
    LiveCase("P8-chip-omitted", **_GW6, edits=(Replace(GW6_PROPOSAL, "\nchip: null\n", "\n"),)),
    LiveCase("P9-correction", 5, CORRECTION, "571f5b0", GW5_RERUN_GATE, GW5_RERUN_GATE,
             "2026-09-18T21:30:00+00:00", "2026-09-18T15:37:37+00:00",
             case_lines=("Post-deadline correction: the GW5 deadline has passed and nothing "
                         "was POSTed (the session had expired). Follow §5.",),
             keep_final=True,
             extra=((f"entry/{TEAM_ID}.json",
                     GitBlob("b965a64", f"data/raw/gw5/entry-{TEAM_ID}.json")),
                    (f"entry/{TEAM_ID}/event/5/picks.json",
                     GitBlob("b965a64", f"data/raw/gw5/picks-{TEAM_ID}-e5.json")))),
)


def live_case(case_id: str) -> LiveCase:
    for case in LIVE_CASES:
        if case.id == case_id:
            return case
    raise KeyError(f"no live case {case_id}")


class CaseError(RuntimeError):
    pass


def apply_edit(text: str, edit: Replace) -> str:
    """`__S2_ROW__` stands for the proposal's whole `| S2 |` ledger row."""
    if edit.old == "__S2_ROW__":
        rows = [line for line in text.splitlines(keepends=True) if line.startswith("| S2 |")]
        if len(rows) != 1:
            raise CaseError(f"{len(rows)} '| S2 |' rows in {edit.path}")
        return text.replace(rows[0], "")
    if text.count(edit.old) != 1:
        raise CaseError(f"edit target occurs {text.count(edit.old)} times in {edit.path}: "
                        f"{edit.old!r}")
    return text.replace(edit.old, edit.new)


def apply_flag_edit(bootstrap: bytes, edit: FlagEdit) -> bytes:
    document = json.loads(bootstrap)
    players = [p for p in document["elements"] if p["id"] == edit.player_id]
    if len(players) != 1:
        raise CaseError(f"player {edit.player_id} occurs {len(players)} times")
    players[0].update(status=edit.status, chance_of_playing_next_round=edit.chance,
                      news=edit.news)
    return json.dumps(document).encode()


def synthetic_my_team(picks: list[tuple[int, int, bool, bool]], now_cost: dict[int, int],
                      budget_tenths: int, bank_tenths: int = 0, *,
                      free_transfers: int = 1) -> bytes:
    """A my-team body whose `budget` (selling prices + bank) is exactly
    `budget_tenths`. `picks` are (element, slot, captain, vice). Selling
    prices start at now_cost and move a tenth at a time, in id order."""
    sell = {element: now_cost[element] for element, *_ in picks}
    gap = budget_tenths - bank_tenths - sum(sell.values())
    order = sorted(sell)
    index = 0
    while gap:
        step = 1 if gap > 0 else -1
        sell[order[index % len(order)]] += step
        gap -= step
        index += 1
    body = {
        "picks": [{"element": element, "position": slot, "selling_price": sell[element],
                   "purchase_price": sell[element], "multiplier": 2 if captain else 1,
                   "is_captain": captain, "is_vice_captain": vice}
                  for element, slot, captain, vice in picks],
        "chips": [],
        "transfers": {"bank": bank_tenths, "value": sum(now_cost[e] for e, *_ in picks),
                      "limit": free_transfers, "made": 0, "cost": 4},
    }
    return json.dumps(body, indent=1).encode()
