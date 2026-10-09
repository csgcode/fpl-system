"""Runner commands for the usage-collector eval."""

from __future__ import annotations

from evals.harness.checks import format_scorecard, run_checks
from evals.harness.freeze import freeze, transcripts_archive
from evals.usage_collector.cases import REPLAY_CASES, REPO_ROOT
from evals.usage_collector.graders import CHECKS
from evals.usage_collector.runs import replay_run
from evals.usage_collector.skeleton import SKELETON_ROOT, freeze_skeletons


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
    for sid, lines in freeze_skeletons(archive).items():
        print(f"{(SKELETON_ROOT / sid).relative_to(REPO_ROOT)}: {lines} lines")
    return 0


def live(*, case_ids: list[str] | None, repeat: int, judge: bool, keep: bool) -> int:
    from evals.usage_collector.live import run_live_cases

    if judge:
        print("usage-collector has no judge; every check is code-graded")
    return run_live_cases(case_ids=case_ids, repeat=repeat, keep=keep)
