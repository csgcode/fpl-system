"""Runner commands for the player-analyst eval."""

from __future__ import annotations

from evals.harness.checks import format_scorecard, run_checks
from evals.harness.freeze import freeze, transcripts_archive
from evals.player_analyst.cases import REPLAY_CASES, REPO_ROOT
from evals.player_analyst.checks import CHECKS
from evals.player_analyst.runs import replay_run


def replay() -> int:
    columns = {case.id: run_checks(CHECKS, replay_run(case), mode="replay")
               for case in REPLAY_CASES}
    print(format_scorecard(columns))
    print()
    for name, results in columns.items():
        notes = [f"{r.id} {r.evidence[len('info: '):]}" for r in results
                 if r.evidence.startswith("info: ")]
        print(f"  {name} INFO: " + "; ".join(notes))
    return 0


def freeze_fixtures() -> int:
    archive = transcripts_archive()
    for case in REPLAY_CASES:
        kept = freeze(archive / case.source, case.fixture, repo_root=str(REPO_ROOT),
                      inline_persisted=False)
        print(f"{case.fixture.relative_to(REPO_ROOT)}: {kept} records")
    return 0


def live(*, case_ids: list[str] | None, repeat: int, judge: bool, keep: bool,
         full: bool = False) -> int:
    from evals.player_analyst.live import run_live_cases

    return run_live_cases(case_ids=case_ids, repeat=repeat, judge=judge, keep=keep, full=full)


def outcome() -> int:
    from evals.player_analyst.outcome import print_outcome

    return print_outcome(REPO_ROOT)
