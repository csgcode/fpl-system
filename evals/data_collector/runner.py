"""Runner commands for the data-collector eval."""

from __future__ import annotations

from evals.data_collector.cases import REPLAY_CASES, REPO_ROOT, transcripts_archive
from evals.data_collector.checks import CHECKS
from evals.data_collector.runs import replay_run
from evals.harness.checks import format_scorecard, run_checks
from evals.harness.freeze import freeze


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
    from evals.data_collector.live import run_live_cases

    return run_live_cases(case_ids=case_ids, repeat=repeat, judge=judge, keep=keep)
