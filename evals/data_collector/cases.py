"""Data-collector eval cases: the recorded GW4–GW6 runs (replay) and the
headless scenarios (live), with every source pinned."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from evals.harness.workspace import GitBlob, RepoFile

AGENT = "data-collector"
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "evals" / "fixtures" / AGENT
SPEC_FIXTURE = FIXTURES / "spec-0315b8e.md"
MY_TEAM_FIXTURE = FIXTURES / "my-team.json"
JUDGE_PASS_GW6 = FIXTURES / "judge-pass-gw6.txt"
TEAM_ID = 8455344
ARCHIVE_ENV = "FPL_TRANSCRIPTS_ARCHIVE"
# .python-version pins the interpreter the uv cache holds wheels for; without
# it an offline sync picks the newest Python and tries to build from source.
CODE_PATHS = ("fpl/", "agents/", "docs/", "CLAUDE.md", "pyproject.toml", "uv.lock",
              ".gitignore", ".python-version")


def transcripts_archive() -> Path:
    """The durable transcript backup. Claude Code prunes ~/.claude/projects."""
    configured = os.environ.get(ARCHIVE_ENV)
    if configured:
        return Path(configured)
    return Path.home() / "Dev" / "Personal" / "fpl-transcripts-archive"


@dataclass(frozen=True)
class ReplayCase:
    name: str
    fixture: Path
    source: str
    gw: int
    team_id: int | None
    previous_gw_truth: tuple[bool, bool]
    spec_fixture: Path
    cycle_commit: str


# Previous-GW truth is (finished, data_checked) of round N−1 in the
# analysis-time bootstrap archive of GW N; verified for all three.
REPLAY_CASES: tuple[ReplayCase, ...] = (
    ReplayCase("gw4", FIXTURES / "gw4.jsonl",
               "8cbbfa17-efba-4c69-9b95-2d4a448b3b78/subagents/agent-ab3384a0240bc639c.jsonl",
               4, TEAM_ID, (True, True), SPEC_FIXTURE, "db2ab51"),
    ReplayCase("gw5", FIXTURES / "gw5.jsonl",
               "8f06c38d-49f9-43f1-9887-0ebf72e60800/subagents/agent-a882c7c9cc9e016e2.jsonl",
               5, TEAM_ID, (True, True), SPEC_FIXTURE, "571f5b0"),
    ReplayCase("gw6", FIXTURES / "gw6.jsonl",
               "19d99f5c-a2a6-486b-8614-b36040777608/subagents/agent-ace9726d752568829.jsonl",
               6, TEAM_ID, (True, True), SPEC_FIXTURE, "b28927f"),
)

# Analysis-time bootstraps: each GW's meta.md "Fetched at" matches its
# archive. The 49-byte gw5 archive bootstrap-20260918T124807_563240Z.json is
# the run that a shell redirect emptied; it is never a source.
BOOTSTRAP_PINS = {
    4: RepoFile("data/raw/gw4/.archive/bootstrap-20260911T175839_804484Z.json",
                "5b6b93ce540fc630f798edb05ddda4ef0c04d214847a2a47d3bd5eb7073db4da"),
    5: RepoFile("data/raw/gw5/.archive/bootstrap-20260918T124957_221963Z.json",
                "12a1b4e9718bc62d73834004cb02fe49f7f1396e5bda93225533fc7b54ef6a45"),
    6: RepoFile("data/raw/gw6/.archive/bootstrap-20261009T133149_122429Z.json",
                "8fc3aff56d653b059faf3e83d790ebecf221ac969479f8f1e91c4edfda0544b4"),
}
FIXTURE_PINS = {
    4: RepoFile("data/raw/gw4/fixtures.json",
                "13988086136ab19aa76ef3852b5a9bd481fc6a07598bd4b8666679c6ad75f05a"),
    5: RepoFile("data/raw/gw5/fixtures.json",
                "996984110af832bf905aa5f31e4577c60b0112b9fbdd67abceb188406596a42e"),
    6: RepoFile("data/raw/gw6/fixtures.json",
                "ebd4b1a612a936001aeed4d77995024088b415f22d3d7604d439e84c83791aae"),
}
# What the real agent found from the previous cycle: that cycle's commit.
# gw3's copy still shows GW3 unfinished — the stale-status trap.
PREVIOUS_CYCLE_COMMITS = {3: "82ad6da", 4: "db2ab51", 5: "571f5b0"}


@dataclass(frozen=True)
class LiveCase:
    id: str
    gw: int
    team_id: int | None
    auth: bool
    preseed: bool = False
    errors: dict[str, int] = field(default_factory=dict)

    @property
    def previous_gw(self) -> int:
        return self.gw - 1

    def previous_files(self) -> dict[str, GitBlob]:
        commit = PREVIOUS_CYCLE_COMMITS[self.previous_gw]
        base = f"data/raw/gw{self.previous_gw}"
        return {f"{base}/{name}": GitBlob(commit, f"{base}/{name}")
                for name in ("bootstrap.json", "meta.md")}


# The last shortlisted id in the gw6 analysis bootstrap. `summaries` stops at
# the first failing id, so failing the last one leaves every other summary
# cached and the collection can still finish.
L5_FAILING_SUMMARY_ID = 646

LIVE_CASES: tuple[LiveCase, ...] = (
    LiveCase("L1", 6, TEAM_ID, auth=True),
    LiveCase("L2", 5, TEAM_ID, auth=False, preseed=True),
    LiveCase("L3", 4, None, auth=True),
    LiveCase("L4", 6, TEAM_ID, auth=True, errors={f"my-team/{TEAM_ID}": 401}),
    LiveCase("L5", 6, TEAM_ID, auth=True,
             errors={f"element-summary/{L5_FAILING_SUMMARY_ID}": 503}),
)


def live_case(case_id: str) -> LiveCase:
    for case in LIVE_CASES:
        if case.id == case_id:
            return case
    raise KeyError(f"no live case {case_id}")
