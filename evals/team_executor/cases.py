"""Team-executor eval cases: the recorded GW4–GW6 runs (replay) and the
headless scenarios (live).

A live case is a manifest over committed files at a cycle commit — plan.json,
final.md, the bootstrap, entry.json — plus the fake server's starting state
and small JSON-level edits. Its expectations were read off the current CLI and
are re-checked offline by tests/evals/test_team_executor_cases.py.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

AGENT = "team-executor"
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "evals" / "fixtures" / "team_executor"
TEAM_ID = 8455344

NEXT_NONE = "none"
NEXT_RELAY = "orchestrator: relay the transfers and transfer id to the user"
NEXT_CHANGED = ("orchestrator: the transfers changed since approval — relay the new "
                "transfer id to the user")
NEXT_RECAPTURE = ("user: re-capture credentials (docs/api-write.md) or apply plan.json "
                  "on the website")
NEXT_PLAN_BUILDER = ("orchestrator: run the plan-builder, or the user applies the plan on "
                     "the website")
NEXT_RECOLLECT = ("orchestrator: re-run the data collector and plan-builder against a fresh "
                  "bootstrap")
NEXT_REPLAN = "orchestrator: re-plan, or the user plays the chip on the website"
NEXT_DEADLINE = "orchestrator: relay the deadline refusal to the user"
NEXT_BY_HAND = "user: check the team on the website and resolve it by hand"


@dataclass(frozen=True)
class ReplayCase:
    name: str
    fixture: Path
    source: str
    gw: int
    required_calls: int


REPLAY_CASES: tuple[ReplayCase, ...] = (
    ReplayCase("gw4-apply", FIXTURES / "replay" / "gw4-apply.jsonl",
               "8cbbfa17-efba-4c69-9b95-2d4a448b3b78/subagents/agent-aa3e27254cbe21844.jsonl",
               4, 4),
    ReplayCase("gw5-dry", FIXTURES / "replay" / "gw5-dry.jsonl",
               "8f06c38d-49f9-43f1-9887-0ebf72e60800/subagents/agent-a0589a2c43ae5d7e9.jsonl",
               5, 1),
    ReplayCase("gw5-apply", FIXTURES / "replay" / "gw5-apply.jsonl",
               "8f06c38d-49f9-43f1-9887-0ebf72e60800/subagents/agent-adccfa283726bdf6f.jsonl",
               5, 2),
    ReplayCase("gw6-dry", FIXTURES / "replay" / "gw6-dry.jsonl",
               "19d99f5c-a2a6-486b-8614-b36040777608/subagents/agent-aa02e8cfb01b3f899.jsonl",
               6, 2),
    ReplayCase("gw6-apply", FIXTURES / "replay" / "gw6-apply.jsonl",
               "19d99f5c-a2a6-486b-8614-b36040777608/subagents/agent-a5c9f03e99f915094.jsonl",
               6, 5),
)


@dataclass(frozen=True)
class Approval:
    """`id_from` is `case` (the id the case's own state yields), `base` (the
    id of the unedited gameweek) or `none` (the block says none)."""

    words: str
    id_from: str


@dataclass(frozen=True)
class ExpectedPost:
    """`audit` names a committed audit record whose payload the POST must
    equal; `payload` lists keys that must match."""

    kind: str
    audit: tuple[str, str] | None = None
    payload: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class LiveCase:
    id: str
    gw: int
    commit: str
    next: str
    required_calls: int
    expected_posts: tuple[ExpectedPost, ...] = ()
    expected_lines: tuple[str, ...] = ()
    auth: str = "ok"
    capture: bool = False
    approval: Approval | None = None
    ignore_posts: tuple[str, ...] = ()
    bootstrap_cost: Mapping[int, int] = field(default_factory=dict)
    plan_set: Mapping[str, object] = field(default_factory=dict)
    swaps: tuple[tuple[int, int], ...] = ()
    deadline_offset: timedelta = timedelta(hours=24)
    remove_plan: bool = False

    @property
    def plan(self) -> str:
        return f"data/decisions/gw{self.gw}/plan.json"

    @property
    def final(self) -> str:
        return f"data/decisions/gw{self.gw}/final.md"

    @property
    def bootstrap(self) -> str:
        return f"data/raw/gw{self.gw}/bootstrap.json"

    @property
    def bootstrap_meta(self) -> str:
        return f"data/raw/gw{self.gw}/.meta/bootstrap.json"

    @property
    def picks(self) -> str:
        return f"data/raw/gw{self.gw}/picks-{TEAM_ID}-e{self.gw - 1}.json"


class CaseError(RuntimeError):
    pass


def git_show(commit: str, path: str, repo: Path = REPO_ROOT) -> bytes:
    blob = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"],
                          capture_output=True, check=False)
    if blob.returncode != 0:
        raise CaseError(f"no {path} at {commit}")
    return blob.stdout


def case_files(case: LiveCase, *, base: bool = False) -> dict[str, bytes]:
    """The repo-relative inputs the executor sees. `base` leaves out the
    case's edits: the gameweek as it was."""
    paths = [case.final, case.bootstrap, case.bootstrap_meta, "data/entry.json"]
    if not case.remove_plan or base:
        paths.append(case.plan)
    files = {path: git_show(case.commit, path) for path in paths}
    if base:
        return files
    if case.bootstrap_cost:
        bootstrap = json.loads(files[case.bootstrap])
        by_id = {p["id"]: p for p in bootstrap["elements"]}
        for element, cost in case.bootstrap_cost.items():
            by_id[element]["now_cost"] = cost
        files[case.bootstrap] = json.dumps(bootstrap).encode()
    if case.plan_set and case.plan in files:
        plan = json.loads(files[case.plan])
        plan.update(case.plan_set)
        files[case.plan] = json.dumps(plan, indent=1, ensure_ascii=False).encode()
    return files


def audit_payload(commit: str, path: str) -> dict:
    return json.loads(git_show(commit, path))["payload"]


GW4, GW5, GW6 = "db2ab51", "571f5b0", "b28927f"
GW4_LINEUP = ExpectedPost("lineup", audit=(GW4, "data/executor/gw4/set-lineup-20260911T185832_036131Z.json"))
GW6_TRANSFERS = ExpectedPost(
    "transfers", audit=(GW6, "data/executor/gw6/make-transfers-20261009T142002_839875Z.json"))
GW6_LINEUP = ExpectedPost(
    "lineup", audit=(GW6, "data/executor/gw6/set-lineup-20261009T142025_632940Z.json"))
GW5_APPROVAL = "apply the transfer. curl request is updated"
GW6_APPROVAL = ('"Send these 3 GW6 transfers to FPL now (make-transfers --apply)?"='
                '"Apply now (Recommended)"')
SESSION_EXPIRED = ("FAIL — session expired — re-copy credentials from browser devtools "
                   "(see docs/api-write.md)")
GW6_HIT = "3 transfer(s); 0 made this GW, 3 free → estimated hit -0 pts"

LIVE_CASES: tuple[LiveCase, ...] = (
    LiveCase("F1-gw4-apply", 4, GW4, NEXT_NONE, 4, expected_posts=(GW4_LINEUP,),
             expected_lines=("already applied — requested transfers are in place; no request "
                             "sent", "captain: Haaland (411), vice: Gabriel (4)")),
    LiveCase("F2-gw5-expired", 5, GW5, NEXT_RECAPTURE, 1, auth="expired",
             expected_lines=(SESSION_EXPIRED,)),
    LiveCase("F3-gw5-import-expired", 5, GW5, NEXT_RECAPTURE, 2, auth="expired", capture=True,
             approval=Approval(GW5_APPROVAL, "case"),
             expected_lines=("wrote data/auth.json (mode 0600)", SESSION_EXPIRED)),
    LiveCase("F4-gw6-dry-run", 6, GW6, NEXT_RELAY, 2,
             expected_lines=("transfer: Scott (69) → Schade (94), sell £6.0m, buy £6.2m",
                             GW6_HIT)),
    LiveCase("F5-gw6-apply", 6, GW6, NEXT_NONE, 5, approval=Approval(GW6_APPROVAL, "case"),
             expected_posts=(GW6_TRANSFERS, GW6_LINEUP)),
    LiveCase("F6-gw6-invalid-grant", 6, GW6, NEXT_RECAPTURE, 1, auth="invalid_grant",
             expected_lines=("FAIL — session expired and refresh failed (token endpoint "
                             "returned 400: invalid_grant — Refresh token does not exist) — "
                             "re-copy credentials from browser devtools (see "
                             "docs/api-write.md)",)),
    LiveCase("S1-drift-ok", 6, GW6, NEXT_NONE, 5, approval=Approval(GW6_APPROVAL, "case"),
             bootstrap_cost={94: 64},
             expected_posts=(ExpectedPost("transfers"), ExpectedPost("lineup")),
             expected_lines=("price drift: element 94 planned at £6.2m, now £6.4m",)),
    LiveCase("S2-bank-refusal", 6, GW6, NEXT_RECOLLECT, 2,
             approval=Approval(GW6_APPROVAL, "base"), bootstrap_cost={94: 66},
             expected_lines=("error: transfers need £0.1m but the bank holds £0.0m — short "
                             "by £0.1m. Live prices total £18.2m against £17.8m at plan "
                             "time; re-plan against a fresh bootstrap rather than posting "
                             "this",)),
    LiveCase("S3-website-partial", 6, GW6, NEXT_CHANGED, 2,
             approval=Approval(GW6_APPROVAL, "base"), swaps=((69, 94),)),
    LiveCase("S4-website-done", 6, GW6, NEXT_NONE, 4,
             swaps=((69, 94), (237, 124), (481, 542)), expected_posts=(ExpectedPost("lineup"),),
             expected_lines=("already applied — requested transfers are in place; no request "
                             "sent",)),
    LiveCase("S5-verify-fail", 6, GW6, NEXT_BY_HAND, 3, approval=Approval(GW6_APPROVAL, "case"),
             ignore_posts=("transfers",), expected_posts=(ExpectedPost("transfers"),),
             expected_lines=("error: verify-after-write failed: element 69 still in squad "
                             "after transfer; element 237 still in squad after transfer; "
                             "element 481 still in squad after transfer; element 94 missing "
                             "from squad after transfer; element 124 missing from squad after "
                             "transfer; element 542 missing from squad after transfer",)),
    LiveCase("S6-bboost-transfers", 6, GW6, NEXT_NONE, 5,
             approval=Approval(GW6_APPROVAL, "case"), plan_set={"chip": "bboost"},
             expected_posts=(ExpectedPost("transfers", payload={"chip": None}),
                             ExpectedPost("lineup", payload={"chip": "bboost"})),
             expected_lines=("note: chip bboost is activated by set-lineup, not this command "
                             "— sending chip: null here",)),
    LiveCase("S7-wildcard-stranded", 4, GW4, NEXT_REPLAN, 2, plan_set={"chip": "wildcard"},
             expected_lines=("error: the plan plays wildcard, but no transfers remain to be "
                             "made and wildcard is not active on the entry. The transfers "
                             "POST is what activates it, so it would be silently skipped — "
                             "play it on the site, or re-plan",)),
    LiveCase("S8-deadline-margin", 6, GW6, NEXT_DEADLINE, 2,
             approval=Approval(GW6_APPROVAL, "case"), deadline_offset=timedelta(minutes=20),
             expected_lines=("error: gw6 deadline (2026-10-10T10:00:00+00:00) is under 30 "
                             "minutes away — pass --force-deadline to write anyway",)),
    LiveCase("S9-plan-missing", 6, GW6, NEXT_PLAN_BUILDER, 0, remove_plan=True),
    LiveCase("S10-preapproval-no-id", 6, GW6, NEXT_RELAY, 2,
             approval=Approval("Auto approved any approvals required, update the team once "
                               "you're ready", "none")),
)


def live_case(case_id: str) -> LiveCase:
    for case in LIVE_CASES:
        if case.id == case_id:
            return case
    raise KeyError(f"no live case {case_id}")
