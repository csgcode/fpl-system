"""Runner commands for the team-executor eval."""

from __future__ import annotations

from evals.harness.checks import format_scorecard, run_checks
from evals.harness.freeze import freeze, transcripts_archive
from evals.team_executor.cases import REPLAY_CASES, REPO_ROOT
from evals.team_executor.checks import CHECKS
from evals.team_executor.runs import replay_run


def replay() -> int:
    columns = {case.name: run_checks(CHECKS, replay_run(case), mode="replay")
               for case in REPLAY_CASES}
    print(format_scorecard(columns))
    return 0


def freeze_fixtures() -> int:
    archive = transcripts_archive()
    for case in REPLAY_CASES:
        kept = freeze(archive / case.source, case.fixture, repo_root=str(REPO_ROOT))
        print(f"{case.fixture.relative_to(REPO_ROOT)}: {kept} records")
    return 0


def live(*, case_ids: list[str] | None, repeat: int, judge: bool, keep: bool) -> int:
    from evals.team_executor.live import run_live_cases

    return run_live_cases(case_ids=case_ids, repeat=repeat, judge=judge, keep=keep)
