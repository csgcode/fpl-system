"""Runner commands for the squad-optimizer eval."""

from __future__ import annotations

import json
import subprocess

from evals.harness.freeze import freeze, transcripts_archive
from evals.harness.workspace import SourceError
from evals.squad_optimizer.cases import (
    REPLAY_CASES,
    REPO_ROOT,
    SPEC_COMMIT,
    SPEC_FIXTURE,
    SPEC_PATH,
    VIEWS,
)


def freeze_fixtures() -> int:
    from evals.squad_optimizer.views import freeze_view

    archive = transcripts_archive()
    for case in REPLAY_CASES:
        source = archive / case.source
        if not source.is_file():
            print(f"{case.name}: skipped — {source} is missing")
            continue
        kept = freeze(source, case.fixture, repo_root=str(REPO_ROOT))
        print(f"{case.fixture.relative_to(REPO_ROOT)}: {kept} records")
    spec = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{SPEC_COMMIT}:{SPEC_PATH}"],
                          capture_output=True, check=True).stdout
    SPEC_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    SPEC_FIXTURE.write_bytes(spec)
    print(f"{SPEC_FIXTURE.relative_to(REPO_ROOT)}: {len(spec)} bytes")
    for spec_view in VIEWS.values():
        try:
            document = freeze_view(spec_view)
        except SourceError as exc:
            print(f"{spec_view.id}: skipped — {exc}")
            continue
        spec_view.path.parent.mkdir(parents=True, exist_ok=True)
        rows = ",\n".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}"
                          for k, v in document["rows"].items())
        spec_view.path.write_text(
            f'{{"meta": {json.dumps(document["meta"])},\n"rows": {{\n{rows}\n}}}}\n',
            encoding="utf-8")
        print(f"{spec_view.path.relative_to(REPO_ROOT)}: {len(document['rows'])} rows")
    return 0


def replay() -> int:
    from evals.harness.checks import format_scorecard, run_checks
    from evals.squad_optimizer.checks import CHECKS
    from evals.squad_optimizer.runs import replay_run

    columns = {case.name: run_checks(CHECKS, replay_run(case), mode="replay")
               for case in REPLAY_CASES}
    print(format_scorecard(columns))
    return 0


def live(*, case_ids: list[str] | None, repeat: int, judge: bool, keep: bool,
         full: bool = False) -> int:
    from evals.squad_optimizer.live import run_live_cases

    return run_live_cases(case_ids=case_ids, repeat=repeat, judge=judge, keep=keep, full=full)


def outcome() -> int:
    from evals.squad_optimizer.outcome import print_outcome

    return print_outcome()
