"""Runner commands for the finalizer eval."""

from __future__ import annotations

import subprocess

from evals.harness.freeze import freeze, transcripts_archive
from evals.finalizer.cases import REPLAY_CASES, REPO_ROOT, SPEC_COMMIT, SPEC_FIXTURE, SPEC_PATH


def freeze_fixtures() -> int:
    archive = transcripts_archive()
    for case in REPLAY_CASES:
        kept = freeze(archive / case.source, case.fixture, repo_root=str(REPO_ROOT))
        print(f"{case.fixture.relative_to(REPO_ROOT)}: {kept} records")
    spec = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{SPEC_COMMIT}:{SPEC_PATH}"],
                          capture_output=True, check=True).stdout
    SPEC_FIXTURE.write_bytes(spec)
    print(f"{SPEC_FIXTURE.relative_to(REPO_ROOT)}: {len(spec)} bytes")
    return 0


def replay() -> int:
    from evals.finalizer.checks import CHECKS
    from evals.finalizer.runs import replay_run
    from evals.harness.checks import format_scorecard, run_checks

    columns = {case.name: run_checks(CHECKS, replay_run(case), mode="replay")
               for case in REPLAY_CASES}
    print(format_scorecard(columns))
    return 0


def live(*, case_ids: list[str] | None, repeat: int, judge: bool, keep: bool) -> int:
    from evals.finalizer.live import run_live_cases

    return run_live_cases(case_ids=case_ids, repeat=repeat, judge=judge, keep=keep)
