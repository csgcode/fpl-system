"""Retro-analyst eval cases: the recorded GW3–GW5 retros (replay) and the
headless scenarios (live). Inputs are files at cycle commits, or local
bootstrap archives pinned by sha256, so a case is a manifest rather than a
copy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from evals.harness.workspace import RepoFile

AGENT = "retro-analyst"
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "evals" / "fixtures" / AGENT
TEAM_ID = 8455344

SPEC_FIXTURE = FIXTURES / "spec-ff65c63.md"
SPEC_COMMIT = "ff65c63"
SPEC_PATH = "agents/retro-analyst.md"

PROMPT_ONLY = "prompt"
PROMPT_AND_SPEC = "prompt+spec"


@dataclass(frozen=True)
class ReplayCase:
    """`cycle_commit` records the retro the run wrote (cycle N = M + 1);
    `previous_commit` the cycle before, holding the prior retros.
    `instructions` says where the spec reached the agent: embedded in the
    prompt, or read from the file (the spec fixture is then appended)."""

    name: str
    fixture: Path
    source: str
    round: int
    cycle_commit: str
    previous_commit: str
    instructions: str
    date: str

    @property
    def gw(self) -> int:
        return self.round + 1

    @property
    def session(self) -> str:
        return self.source.split("/", 1)[0]


REPLAY_CASES: tuple[ReplayCase, ...] = (
    ReplayCase("gw3", FIXTURES / "gw3.jsonl",
               "8cbbfa17-efba-4c69-9b95-2d4a448b3b78/subagents/agent-a64da75adf0fdd9b2.jsonl",
               3, "db2ab51", "82ad6da", PROMPT_ONLY, "2026-09-11"),
    ReplayCase("gw4", FIXTURES / "gw4.jsonl",
               "8f06c38d-49f9-43f1-9887-0ebf72e60800/subagents/agent-aa17525f2b6ba5661.jsonl",
               4, "571f5b0", "db2ab51", PROMPT_ONLY, "2026-09-18"),
    ReplayCase("gw5", FIXTURES / "gw5.jsonl",
               "19d99f5c-a2a6-486b-8614-b36040777608/subagents/agent-a2413eefb45ee5595.jsonl",
               5, "b28927f", "571f5b0", PROMPT_AND_SPEC, "2026-10-09"),
)


def replay_case(name: str) -> ReplayCase:
    for case in REPLAY_CASES:
        if case.name == name:
            return case
    raise KeyError(f"no replay case {name}")


def archive(gw: int, stamp: str, sha256: str) -> RepoFile:
    return RepoFile(f"data/raw/gw{gw}/.archive/bootstrap-{stamp}.json", sha256)


# The analysis-time bootstrap of cycle N: round M is finished and data-checked.
ANALYSIS_BOOTSTRAPS = {
    4: archive(4, "20260911T175839_804484Z",
               "5b6b93ce540fc630f798edb05ddda4ef0c04d214847a2a47d3bd5eb7073db4da"),
    5: archive(5, "20260918T124957_221963Z",
               "12a1b4e9718bc62d73834004cb02fe49f7f1396e5bda93225533fc7b54ef6a45"),
    6: archive(6, "20261009T133149_122429Z",
               "8fc3aff56d653b059faf3e83d790ebecf221ac969479f8f1e91c4edfda0544b4"),
}


# --- live -------------------------------------------------------------------

PICKS_DIFFER = "picks-differ"
NOT_CHECKED = "not-checked"
NULL_TEAM = "null-team"
ARITHMETIC_A3 = "arithmetic-a3"
BIG_FINAL = "big-final"

C21_RULE = ("**C21 — A3 (player-analyst): raise every DEF's dc90 input 8% so the DefCon hit "
            "probability at ratio 1.0 reads 0.65 not 0.55.** Rounds 2–4 DEF DefCon hits ran "
            "above prediction.")


@dataclass(frozen=True)
class LiveCase:
    """`now` pins the replay clock just after the analysis bootstrap landed,
    as the step-0-after-step-1 order requires; `date` is the original run's
    day, given to the agent for backlog rows."""

    id: str
    round: int
    commit: str
    date: str
    now: str
    perturbation: str | None = None
    default: bool = False

    @property
    def gw(self) -> int:
        return self.round + 1


_L1 = dict(round=5, commit="b28927f", date="2026-10-09", now="2026-10-09T13:32:49+00:00")
_L2 = dict(round=4, commit="571f5b0", date="2026-09-18", now="2026-09-18T12:50:57+00:00")

LIVE_CASES: tuple[LiveCase, ...] = (
    LiveCase("L1-gw5", **_L1, default=True),
    LiveCase("L2-gw4", **_L2, default=True),
    LiveCase("L3-gw3", round=3, commit="db2ab51", date="2026-09-11",
             now="2026-09-11T17:59:39+00:00"),
    LiveCase("P1-picks-differ", **_L1, perturbation=PICKS_DIFFER),
    LiveCase("P2-not-checked", **_L2, perturbation=NOT_CHECKED),
    LiveCase("P3-null-team", **_L2, perturbation=NULL_TEAM),
    LiveCase("P4-arithmetic-a3", **_L1, perturbation=ARITHMETIC_A3),
    LiveCase("P5-big-final", **_L1, perturbation=BIG_FINAL),
)


def live_case(case_id: str) -> LiveCase:
    for case in LIVE_CASES:
        if case.id == case_id:
            return case
    raise KeyError(f"no live case {case_id}")
