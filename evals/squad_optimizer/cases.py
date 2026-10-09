"""Squad-optimizer eval cases: the recorded GW4–GW6 runs (replay), the frozen
EP views the reference scorer reads, and the headless scenarios (live).
Inputs are files at cycle commits or bootstrap archives pinned by sha256."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from evals.harness.workspace import GitBlob, RepoFile
from fpl.objective import Market

AGENT = "squad-optimizer"
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "evals" / "fixtures" / AGENT
REPLAY_DIR = FIXTURES / "replay"
VIEWS_DIR = FIXTURES / "views"
SPEC_FIXTURE = FIXTURES / "spec-ff65c63.md"
SPEC_COMMIT = "ff65c63"
SPEC_PATH = "agents/squad-optimizer.md"
EP_CODE = "07c8dcc"
PRE_REOPEN_DEF = REPO_ROOT / "evals" / "fixtures" / "player-analyst" / "reopen-gw5-def" \
    / "inputs-DEF.pre.json"

WEEKLY = "weekly"
REVISION = "revision"
RESCORE = "rescore"


def archive(gw: int, stamp: str, sha256: str) -> RepoFile:
    return RepoFile(f"data/raw/gw{gw}/.archive/bootstrap-{stamp}.json", sha256)


GW4_BOOTSTRAP = archive(4, "20260911T175839_804484Z",
                        "5b6b93ce540fc630f798edb05ddda4ef0c04d214847a2a47d3bd5eb7073db4da")
GW5_PRE_BOOTSTRAP = archive(5, "20260918T124957_221963Z",
                            "12a1b4e9718bc62d73834004cb02fe49f7f1396e5bda93225533fc7b54ef6a45")
GW5_POST_BOOTSTRAP = archive(5, "20260918T151953_303197Z",
                             "84715852f9548729a8cb59734938c922792fcf33773f916467bbd988e1225d2e")
GW6_BOOTSTRAP = archive(6, "20261009T133149_122429Z",
                        "8fc3aff56d653b059faf3e83d790ebecf221ac969479f8f1e91c4edfda0544b4")

# Pre-REOPEN DEF rows, (p_start, p_start_gw), used when the player-analyst
# fixture is absent.
PRE_REOPEN_ROWS = {
    "Shaw": (0.5, (0.5, 0.72, 0.74, 0.74, 0.74, 0.74)),
    "Pau": (0.62, (0.62, 0.8, 0.8, 0.8, 0.8, 0.8)),
    "Maatsen": (0.25, (0.25, 0.82, 0.84, 0.84, 0.84, 0.84)),
    "Burn": (0.12, (0.12, 0.6, 0.62, 0.62, 0.62, 0.62)),
    "Botman": (0.9, (0.9, 0.82, 0.8, 0.79, 0.79, 0.79)),
}


@dataclass(frozen=True)
class ViewSpec:
    """A frozen EP view. `regenerate` rebuilds the blend reading with the
    commit's own `fpl ep`; otherwise the committed players-*.json is the
    blend. `pre_reopen_def` swaps in the pre-REOPEN DEF inputs; `prior_stubs`
    adds p_start-0 rows the old code needs to score the prior reading."""

    id: str
    gw: int
    commit: str
    bootstrap: RepoFile
    regenerate: bool = True
    pre_reopen_def: bool = False
    prior_stubs: tuple[int, ...] = ()

    @property
    def path(self) -> Path:
        return VIEWS_DIR / f"{self.id}.json"


VIEWS: dict[str, ViewSpec] = {v.id: v for v in (
    ViewSpec("gw4", 4, "db2ab51", GW4_BOOTSTRAP),
    ViewSpec("gw5-pre", 5, "571f5b0", GW5_PRE_BOOTSTRAP, pre_reopen_def=True),
    ViewSpec("gw5-post", 5, "571f5b0", GW5_POST_BOOTSTRAP, regenerate=False,
             prior_stubs=(131,)),
    ViewSpec("gw6", 6, "b28927f", GW6_BOOTSTRAP, regenerate=False),
)}


def market(sells: dict[int, float], *, bank: float = 0.0, free: int) -> Market:
    return Market({pid: round(price * 10) for pid, price in sells.items()},
                  round(bank * 10), free, "relayed")


# The relayed GW4 prompt table; its "Σ 99.6" was wrong, the rows sum to 99.4.
GW4_MARKET = market({1: 6.0, 4: 8.0, 202: 5.0, 229: 6.0, 427: 7.9, 237: 5.9, 481: 6.3,
                     68: 6.0, 411: 15.5, 106: 7.9, 249: 5.5, 497: 4.0, 69: 6.0, 445: 5.0,
                     423: 4.4}, free=1)
# Re-score call 18.
GW5_MARKET = market({1: 6.0, 445: 5.0, 229: 6.0, 4: 8.0, 427: 7.9, 68: 6.0, 69: 6.0,
                     481: 6.3, 411: 15.5, 106: 7.8, 249: 5.5, 497: 4.0, 237: 5.9, 423: 4.4,
                     202: 5.0}, free=2)
# opt.py call 20; Σ 99.2.
GW6_MARKET = market({1: 6.0, 4: 8.0, 229: 6.1, 202: 4.9, 68: 6.0, 427: 7.9, 69: 6.0,
                     237: 5.8, 411: 15.5, 106: 7.8, 249: 5.6, 497: 4.0, 481: 6.3, 445: 5.0,
                     423: 4.3}, free=3)


@dataclass(frozen=True)
class Output:
    """Where a run's proposal text comes from: a cycle-commit blob, the
    run's own reconstructed writes ("written"), or another transcript's
    first Read of the file ("read:<case>")."""

    blob: GitBlob | None = None
    source: str | None = None


@dataclass(frozen=True)
class ReplayCase:
    name: str
    source: str
    gw: int
    kind: str
    view: str
    market: Market
    previous: GitBlob
    suggestions: GitBlob
    output: Output
    calls: int
    handback: bool
    before: str | None = None
    """The case whose output is this run's pre-run proposal (re-run kinds)."""
    review: GitBlob | None = None

    @property
    def fixture(self) -> Path:
        return REPLAY_DIR / f"{self.name}.jsonl"

    @property
    def c20_active(self) -> bool:
        return self.gw >= 5


def _proposal(commit: str, gw: int) -> GitBlob:
    return GitBlob(commit, f"data/decisions/gw{gw}/squad-proposal.md")


def _final(commit: str, gw: int) -> GitBlob:
    return GitBlob(commit, f"data/decisions/gw{gw}/final.md")


_GW5 = dict(gw=5, market=GW5_MARKET, previous=_final("db2ab51", 4),
            suggestions=GitBlob("571f5b0", "data/suggestions.md"))
_SESSION5 = "8f06c38d-49f9-43f1-9887-0ebf72e60800/subagents/"

REPLAY_CASES: tuple[ReplayCase, ...] = (
    ReplayCase("gw4", "8cbbfa17-efba-4c69-9b95-2d4a448b3b78/subagents/"
               "agent-a35987eb366382cc6.jsonl", 4, WEEKLY, "gw4", GW4_MARKET,
               _final("82ad6da", 3), GitBlob("db2ab51", "data/suggestions.md"),
               Output(blob=_proposal("db2ab51", 4)), calls=17, handback=False),
    ReplayCase("gw5-orig", _SESSION5 + "agent-aafb49eec50cc62c1.jsonl", kind=WEEKLY,
               view="gw5-pre", output=Output(source="written"), calls=95, handback=True,
               **_GW5),
    ReplayCase("gw5-rev", _SESSION5 + "agent-a901a7c11d2e61a83.jsonl", kind=REVISION,
               view="gw5-pre", output=Output(source="read:gw5-rescore"), calls=43,
               handback=True, before="gw5-orig",
               review=GitBlob("571f5b0", "data/decisions/gw5/review.md"), **_GW5),
    ReplayCase("gw5-rescore", _SESSION5 + "agent-af4ec8753dda21077.jsonl", kind=RESCORE,
               view="gw5-post", output=Output(blob=_proposal("571f5b0", 5)), calls=38,
               handback=True, before="gw5-rev", **_GW5),
    ReplayCase("gw6", "19d99f5c-a2a6-486b-8614-b36040777608/subagents/"
               "agent-a454937c9d37cf8eb.jsonl", 6, WEEKLY, "gw6", GW6_MARKET,
               _final("b965a64", 5), GitBlob("b28927f", "data/suggestions.md"),
               Output(blob=_proposal("b28927f", 6)), calls=34, handback=True),
)


def replay_case(name: str) -> ReplayCase:
    for case in REPLAY_CASES:
        if case.name == name:
            return case
    raise KeyError(name)


# --- live -------------------------------------------------------------------


@dataclass(frozen=True)
class LiveCase:
    """`commit` is the cycle commit the workspace data comes from; `view`
    names the pinned bootstrap and DEF inputs. `suggestions_through` cuts
    data/suggestions.md after that S#; `extra_suggestions` are appended rows.
    `proposal` names the replay case whose output is the pre-run proposal of
    a re-run; `stack` applies the X1 perturbations. `total_line` replaces the
    computed selling-price total in the brief (as relayed, even if wrong)."""

    id: str
    gw: int
    commit: str
    view: str
    market: Market
    suggestions_through: int
    research: bool = False
    default: bool = False
    kind: str = WEEKLY
    case_lines: tuple[str, ...] = field(default=())
    extra_suggestions: tuple[str, ...] = ()
    proposal: str | None = None
    review: GitBlob | None = None
    allow_missing: tuple[int, ...] = ()
    stack: bool = False
    total_line: str | None = None
    reopen_ids: tuple[int, ...] = ()


ELE_FEE, HAALAND, SCOTT = 542, 411, 69
X1_SUGGESTIONS = (
    "| S3 | 2026-09-18 |  |  | Score the bench with auto-subs instead of the XI-only "
    "objective; replace Shaw |",
    "| S4 | 2026-09-18 |  |  | Sell Scott this week even below the threshold |",
    "| S5 | 2026-09-18 | five |  | Bring in a second Arsenal defender |",
    "| S6 | 2026-09-18 |  |  | withdraw S2 |",
    "| S7 | 2026-09-11 | 4 | 4 | Keep Thiago for the GW4 fixture |",
)
_L1 = dict(gw=5, commit="571f5b0", view="gw5-pre", market=GW5_MARKET, suggestions_through=2)

LIVE_CASES: tuple[LiveCase, ...] = (
    LiveCase("L1-gw5", **_L1, default=True),
    LiveCase("L2-gw6", 6, "b28927f", "gw6", GW6_MARKET, suggestions_through=6, research=True,
             default=True),
    LiveCase("L3-gw4", 4, "db2ab51", "gw4", GW4_MARKET, suggestions_through=2,
             total_line="Total sell value 99.6"),
    LiveCase("X1-gw5-stack", **_L1, stack=True, extra_suggestions=X1_SUGGESTIONS),
    LiveCase("X2-gw5-revision", **_L1, kind=REVISION, proposal="gw5-orig",
             review=GitBlob("571f5b0", "data/decisions/gw5/review.md")),
    LiveCase("X3-gw5-reopen", 5, "571f5b0", "gw5-post", GW5_MARKET, suggestions_through=2,
             kind=RESCORE, proposal="gw5-rev", allow_missing=(131,),
             reopen_ids=(423, 34, 36, 448)),
)


def live_case(case_id: str) -> LiveCase:
    for case in LIVE_CASES:
        if case.id == case_id:
            return case
    raise KeyError(f"no live case {case_id}")
