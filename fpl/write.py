"""Authenticated write path: my-team reads, lineup POSTs, transfer POSTs.

Retries stay pinned to GET — a retried POST could double-apply a transfer.
Responses derived from the authenticated session are never cached into the
raw snapshot dirs; the only persistence is the audit record written under the
executor store after an --apply, and it contains payloads and verification
results, never credentials.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from fpl.api import BASE_URL, Fetched
from fpl.auth import AuthCredentials
from fpl.models import MyTeam, MyTeamTransfersState, Position
from fpl.service import load_cached_bootstrap
from fpl.state import PlannedPicks
from fpl.store import ARCHIVE_STAMP_FORMAT, SnapshotStore, utcnow

TRANSFERS_URL = f"{BASE_URL}/transfers/"
DEADLINE_MARGIN = timedelta(minutes=30)
DEFAULT_TRANSFER_HIT = 4
NO_HIT_CHIPS = frozenset({"wildcard", "freehit"})

SQUAD_SHAPE = {Position.GKP: 2, Position.DEF: 5, Position.MID: 5, Position.FWD: 3}


def my_team_url(team_id: int) -> str:
    return f"{BASE_URL}/my-team/{team_id}/"


class SessionExpiredError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            "session expired — re-copy credentials from browser devtools "
            "(see docs/api-write.md)"
        )


class DeadlineError(ValueError):
    pass


class VerifyMismatchError(RuntimeError):
    def __init__(self, problems: Sequence[str]) -> None:
        super().__init__(
            "verify-after-write failed: " + "; ".join(problems)
        )
        self.problems = tuple(problems)


class WriteGateway(Protocol):
    def get_json(self, url: str) -> dict | list: ...

    def post_json(self, url: str, payload: dict) -> dict | list | None: ...


class AuthenticatedRequestsGateway:
    def __init__(self, credentials: AuthCredentials, timeout_s: float = 10.0) -> None:
        self._timeout_s = timeout_s
        self._session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retry))
        self._session.headers["User-Agent"] = "fpl-system/1.0"
        # The unofficial API rejects state-changing requests without a site
        # referer; auth.json headers can override it.
        self._session.headers["Referer"] = "https://fantasy.premierleague.com/"
        self._session.headers.update(credentials.headers)
        self._session.cookies.update(credentials.cookies)

    def get_json(self, url: str) -> dict | list:
        response = self._session.get(url, timeout=self._timeout_s)
        _ensure_session_alive(response)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, (dict, list)):
            raise ValueError(
                f"expected a JSON object or array from {url}, "
                f"got {type(payload).__name__}"
            )
        return payload

    def post_json(self, url: str, payload: dict) -> dict | list | None:
        response = self._session.post(url, json=payload, timeout=self._timeout_s)
        _ensure_session_alive(response)
        response.raise_for_status()
        if not response.content:
            return None
        return response.json()

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> AuthenticatedRequestsGateway:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _ensure_session_alive(response) -> None:
    if response.status_code in (401, 403):
        raise SessionExpiredError()


class WriteApi:
    def __init__(self, gateway: WriteGateway) -> None:
        self._gateway = gateway

    def my_team(self, team_id: int) -> Fetched:
        url = my_team_url(team_id)
        return Fetched(url=url, payload=self._gateway.get_json(url))

    def post_lineup(self, team_id: int, payload: dict) -> None:
        self._gateway.post_json(my_team_url(team_id), payload)

    def post_transfers(self, payload: dict) -> None:
        self._gateway.post_json(TRANSFERS_URL, payload)


@dataclass(frozen=True)
class LineupPlan:
    team_id: int
    url: str
    payload: dict
    already_applied: bool
    expected: PlannedPicks
    chip: str | None


@dataclass(frozen=True)
class TransferPlan:
    team_id: int
    url: str
    payload: dict
    already_applied: bool
    outs: tuple[int, ...]
    ins: tuple[int, ...]
    notes: tuple[str, ...]


class WriteService:
    def __init__(
        self,
        api: WriteApi,
        store: SnapshotStore,
        executor_store: SnapshotStore,
        now: Callable[[], datetime] = utcnow,
    ) -> None:
        self._api = api
        self._store = store
        self._executor_store = executor_store
        self._now = now

    def my_team(self, team_id: int) -> MyTeam:
        return MyTeam.model_validate(self._api.my_team(team_id).payload)

    def ensure_deadline_open(
        self, gw: int, *, override_margin: bool = False
    ) -> datetime:
        bootstrap = load_cached_bootstrap(self._store, gw)
        deadline = bootstrap.deadline_for(gw)
        if deadline is None:
            raise DeadlineError(
                f"gw{gw} has no deadline in the cached bootstrap — refetch it"
            )
        now = self._now()
        if now >= deadline:
            raise DeadlineError(
                f"gw{gw} deadline ({deadline.isoformat()}) has passed — "
                "refusing to write; this cannot be forced"
            )
        if not override_margin and deadline - now < DEADLINE_MARGIN:
            margin_minutes = int(DEADLINE_MARGIN.total_seconds() // 60)
            raise DeadlineError(
                f"gw{gw} deadline ({deadline.isoformat()}) is under "
                f"{margin_minutes} minutes away — pass --force-deadline to "
                "write anyway"
            )
        return deadline

    def validate_formation(self, gw: int, picks: PlannedPicks) -> None:
        bootstrap = load_cached_bootstrap(self._store, gw)
        by_id = bootstrap.player_by_id()
        unknown = sorted(p.id for p in picks.picks if p.id not in by_id)
        if unknown:
            raise ValueError(f"picks reference unknown player ids: {unknown}")
        role_of = {p.id: by_id[p.id].element_type for p in picks.picks}
        slot_role = {p.position: role_of[p.id] for p in picks.picks}
        if slot_role[1] is not Position.GKP:
            raise ValueError("position 1 must be a goalkeeper")
        if slot_role[12] is not Position.GKP:
            raise ValueError("position 12 must be a goalkeeper (first bench slot)")
        squad = Counter(role_of.values())
        if squad != Counter(SQUAD_SHAPE):
            shape = ", ".join(f"{count} {pos.name}" for pos, count in squad.items())
            raise ValueError(f"squad must be 2 GKP / 5 DEF / 5 MID / 3 FWD, got {shape}")
        xi = Counter(slot_role[slot] for slot in range(1, 12))
        if xi[Position.GKP] != 1:
            raise ValueError("the XI must contain exactly 1 GKP")
        if xi[Position.DEF] < 3:
            raise ValueError("the XI must contain at least 3 DEF")
        if xi[Position.MID] < 2:
            raise ValueError("the XI must contain at least 2 MID")
        if xi[Position.FWD] < 1:
            raise ValueError("the XI must contain at least 1 FWD")

    def plan_lineup(
        self, *, team_id: int, picks: PlannedPicks, chip: str | None = None
    ) -> LineupPlan:
        current = self.my_team(team_id)
        payload = {
            "picks": [
                {
                    "element": p.id,
                    "position": p.position,
                    "is_captain": p.captain,
                    "is_vice_captain": p.vice,
                }
                for p in picks.in_position_order()
            ],
            "chip": chip,
        }
        already_applied = not _lineup_mismatches(current, picks, chip)
        return LineupPlan(
            team_id=team_id,
            url=my_team_url(team_id),
            payload=payload,
            already_applied=already_applied,
            expected=picks,
            chip=chip,
        )

    def apply_lineup(self, gw: int, plan: LineupPlan) -> Path:
        self._api.post_lineup(plan.team_id, plan.payload)
        after = self.my_team(plan.team_id)
        problems = _lineup_mismatches(after, plan.expected, plan.chip)
        return self._record_and_verify("set-lineup", gw, plan.team_id, plan, problems)

    def plan_transfers(
        self,
        *,
        gw: int,
        team_id: int,
        chip: str | None = None,
        out_ids: Sequence[int] | None = None,
        in_ids: Sequence[int] | None = None,
        target_ids: Iterable[int] | None = None,
    ) -> TransferPlan:
        current = self.my_team(team_id)
        squad = current.squad_ids()
        if target_ids is not None:
            target = frozenset(target_ids)
            outs = sorted(squad - target)
            ins = sorted(target - squad)
        else:
            outs, ins = _pending_transfers(list(out_ids or ()), list(in_ids or ()), squad)
        if not outs and not ins:
            payload = {"entry": team_id, "event": gw, "transfers": [], "chip": chip}
            return TransferPlan(
                team_id=team_id, url=TRANSFERS_URL, payload=payload,
                already_applied=True, outs=(), ins=(), notes=(),
            )
        rows = self._transfer_rows(gw, current, outs, ins)
        payload = {"entry": team_id, "event": gw, "transfers": rows, "chip": chip}
        return TransferPlan(
            team_id=team_id,
            url=TRANSFERS_URL,
            payload=payload,
            already_applied=False,
            outs=tuple(sorted(outs)),
            ins=tuple(sorted(ins)),
            notes=tuple(_hit_notes(len(rows), current.transfers, chip)),
        )

    def apply_transfers(self, gw: int, plan: TransferPlan) -> Path:
        self._api.post_transfers(plan.payload)
        after = self.my_team(plan.team_id)
        squad = after.squad_ids()
        problems = [
            f"element {out} still in squad after transfer"
            for out in plan.outs
            if out in squad
        ] + [
            f"element {incoming} missing from squad after transfer"
            for incoming in plan.ins
            if incoming not in squad
        ]
        return self._record_and_verify(
            "make-transfers", gw, plan.team_id, plan, problems
        )

    def _transfer_rows(
        self, gw: int, current: MyTeam, outs: Sequence[int], ins: Sequence[int]
    ) -> list[dict]:
        bootstrap = load_cached_bootstrap(self._store, gw)
        by_id = bootstrap.player_by_id()
        unknown = sorted(pid for pid in [*outs, *ins] if pid not in by_id)
        if unknown:
            raise ValueError(f"transfers reference unknown player ids: {unknown}")
        outs_by_role: dict[Position, list[int]] = {}
        ins_by_role: dict[Position, list[int]] = {}
        for out in outs:
            outs_by_role.setdefault(by_id[out].element_type, []).append(out)
        for incoming in ins:
            ins_by_role.setdefault(by_id[incoming].element_type, []).append(incoming)
        if {r: len(v) for r, v in outs_by_role.items()} != {
            r: len(v) for r, v in ins_by_role.items()
        }:
            out_shape = _role_shape(outs_by_role)
            in_shape = _role_shape(ins_by_role)
            raise ValueError(
                "transfers must swap position-for-position — "
                f"out: {out_shape}, in: {in_shape}"
            )
        selling = {p.element: p.selling_price for p in current.picks}
        rows = []
        for role in sorted(outs_by_role):
            for out, incoming in zip(
                sorted(outs_by_role[role]), sorted(ins_by_role[role])
            ):
                rows.append(
                    {
                        "element_in": incoming,
                        "element_out": out,
                        "purchase_price": by_id[incoming].now_cost,
                        "selling_price": selling[out],
                    }
                )
        return rows

    def _record_and_verify(
        self,
        command: str,
        gw: int,
        team_id: int,
        plan: LineupPlan | TransferPlan,
        problems: Sequence[str],
    ) -> Path:
        record = {
            "command": command,
            "team_id": team_id,
            "payload": plan.payload,
            "verified": not problems,
            "problems": list(problems),
        }
        stamp = self._now().strftime(ARCHIVE_STAMP_FORMAT)
        path = self._executor_store.save(
            gw, f"{command}-{stamp}", record, source_url=plan.url
        )
        if problems:
            raise VerifyMismatchError(problems)
        return path


def _lineup_mismatches(
    current: MyTeam, expected: PlannedPicks, chip: str | None
) -> list[str]:
    problems = []
    by_position = {p.position: p for p in current.picks}
    for planned in expected.in_position_order():
        actual = by_position.get(planned.position)
        if actual is None or actual.element != planned.id:
            found = actual.element if actual else "nothing"
            problems.append(
                f"position {planned.position}: expected element {planned.id}, "
                f"found {found}"
            )
            continue
        if actual.is_captain != planned.captain:
            problems.append(
                f"element {planned.id}: captain flag is {actual.is_captain}, "
                f"expected {planned.captain}"
            )
        if actual.is_vice_captain != planned.vice:
            problems.append(
                f"element {planned.id}: vice flag is {actual.is_vice_captain}, "
                f"expected {planned.vice}"
            )
    if chip is not None and not _chip_active(current, chip):
        problems.append(f"chip {chip} is not active")
    return problems


def _chip_active(current: MyTeam, chip: str) -> bool:
    return any(
        c.name == chip and c.status_for_entry == "active" for c in current.chips
    )


def _pending_transfers(
    outs: list[int], ins: list[int], squad: frozenset[int]
) -> tuple[list[int], list[int]]:
    if len(set(outs)) != len(outs) or len(set(ins)) != len(ins):
        raise ValueError("duplicate ids in transfer request")
    if len(outs) != len(ins):
        raise ValueError(
            "each transfer swaps one player out for one in — "
            f"got {len(outs)} out, {len(ins)} in"
        )
    applied_ins = [incoming for incoming in ins if incoming in squad]
    gone_outs = [out for out in outs if out not in squad]
    if applied_ins or gone_outs:
        if len(applied_ins) == len(ins) and len(gone_outs) == len(outs):
            return [], []
        raise ValueError(
            "transfers look partially applied — already in squad: "
            f"{applied_ins}, already gone: {gone_outs}; resolve manually"
        )
    return outs, ins


def _role_shape(by_role: dict[Position, list[int]]) -> str:
    if not by_role:
        return "none"
    return ", ".join(f"{len(ids)} {role.name}" for role, ids in sorted(by_role.items()))


def _hit_notes(
    count: int, transfers: MyTeamTransfersState, chip: str | None
) -> list[str]:
    if chip in NO_HIT_CHIPS:
        return [f"chip {chip} → no hit"]
    if transfers.limit is None:
        return [f"{count} transfer(s); free-transfer limit unknown — server decides the hit"]
    made = transfers.made or 0
    cost = transfers.cost or DEFAULT_TRANSFER_HIT
    hit = max(0, count + made - transfers.limit) * cost
    return [
        f"{count} transfer(s); {made} made this GW, {transfers.limit} free → "
        f"estimated hit -{hit} pts"
    ]
