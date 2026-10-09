"""The check model every agent's graders share.

A check is a pure function over a run. It is NA in a mode it does not
support, and NA unless the instructions the agent received contain its
`requires` marker — a check never grades an agent on a rule it was not given.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Protocol


class Status(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NA = "NA"


@dataclass(frozen=True)
class CheckResult:
    id: str
    status: Status
    evidence: str

    @classmethod
    def passed(cls, evidence: str = "") -> CheckResult:
        return cls("", Status.PASS, evidence)

    @classmethod
    def failed(cls, evidence: str) -> CheckResult:
        return cls("", Status.FAIL, evidence)

    @classmethod
    def na(cls, evidence: str) -> CheckResult:
        return cls("", Status.NA, evidence)


class HasInstructions(Protocol):
    instructions: str


@dataclass(frozen=True)
class Check:
    id: str
    fn: Callable[[Any], CheckResult]
    requires: str | None = None
    mode: str = "both"


def run_checks(
    checks: Sequence[Check], run: HasInstructions, *, mode: str
) -> list[CheckResult]:
    results = []
    for check in checks:
        if check.mode not in ("both", mode):
            result = CheckResult.na(f"{check.mode} only")
        elif check.requires is not None and check.requires not in run.instructions:
            result = CheckResult.na(f"marker absent: {check.requires!r}")
        else:
            result = check.fn(run)
        results.append(replace(result, id=check.id))
    return results


def format_scorecard(columns: Mapping[str, Iterable[CheckResult]]) -> str:
    """One table: a row per check, a column per run, then the evidence of
    every FAIL cell."""
    by_run = {name: {r.id: r for r in results} for name, results in columns.items()}
    ids = list(dict.fromkeys(i for results in by_run.values() for i in results))
    names = list(by_run)
    width = max([len(n) for n in names] + [4])
    lines = ["check  " + "  ".join(n.ljust(width) for n in names)]
    for check_id in ids:
        cells = [by_run[n][check_id].status.value if check_id in by_run[n] else "-"
                 for n in names]
        lines.append(f"{check_id:<5}  " + "  ".join(c.ljust(width) for c in cells))
    notes = [
        f"  {n} {check_id} {by_run[n][check_id].status.value}: {by_run[n][check_id].evidence}"
        for check_id in ids for n in names
        if check_id in by_run[n] and by_run[n][check_id].status is Status.FAIL
    ]
    return "\n".join(lines + ([""] + notes if notes else []))
