"""Execution plan: one deterministic JSON artefact per gameweek describing
exactly what to POST — squad, lineup, chip, transfers.

Built by code, never by an LLM: a non-deterministic reading of prose must
never drive an irreversible transfer. Everything here is a pure function of a
parsed STATE block plus the cached bootstrap, so it needs no network.

Two fields are deliberately NOT authoritative, and the plan says so in
`price_resolution`: selling prices exist only in the authenticated my-team
read (they encode each player's own price-rise profit rule), and purchase
prices drift daily. The plan carries `purchase_price_at_plan` as an audit
snapshot; the write path re-resolves both at POST time.

Squad-legality validation lives here too, shared with the write path — one
definition of a legal squad, whether it is being planned or posted.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from fpl.models import Bootstrap, Player, Position, Team
from fpl.state import (
    SQUAD_SIZE,
    XI_SIZE,
    ChipUse,
    DecisionState,
    PlannedPick,
    PlannedPicks,
)

SCHEMA_VERSION = 1
SQUAD_SHAPE = {Position.GKP: 2, Position.DEF: 5, Position.MID: 5, Position.FWD: 3}
MAX_PER_CLUB = 3
BACKUP_GK_SLOT = XI_SIZE + 1
DEFAULT_TRANSFER_HIT = 4
NO_HIT_CHIPS = frozenset({"wildcard", "freehit"})

# Which endpoint activates which chip. The site plays bench boost and triple
# captain when saving the lineup, wildcard and free hit when confirming
# transfers; a chip sent to the other endpoint is accepted and never activates.
LINEUP_TARGET = "lineup"
TRANSFERS_TARGET = "transfers"
LINEUP_CHIPS = frozenset({"bboost", "3xc"})
TRANSFER_CHIPS = frozenset({"wildcard", "freehit"})
CHIP_TARGETS = {
    **{chip: LINEUP_TARGET for chip in LINEUP_CHIPS},
    **{chip: TRANSFERS_TARGET for chip in TRANSFER_CHIPS},
}


def route_chip(chip: str | None, target: str) -> str | None:
    """The chip `target` should carry, or None when the other endpoint owns it.

    An unrecognised chip refuses rather than being dropped: a silently omitted
    chip is indistinguishable from a write that succeeded and played it.
    """
    if chip is None:
        return None
    owner = CHIP_TARGETS.get(chip)
    if owner is None:
        known = ", ".join(sorted(CHIP_TARGETS))
        raise ValueError(
            f"unknown chip {chip!r} — cannot tell which endpoint activates it "
            f"(known: {known}); refusing rather than dropping it"
        )
    return chip if owner == target else None

PRICE_RESOLUTION = "live"
PRICE_RESOLUTION_NOTE = (
    "Every price in this file is £m at plan time and is an audit snapshot "
    "only. At POST time the selling price comes from the authenticated "
    "my-team read (it encodes each player's own price-rise profit rule) and "
    "the purchase price from the live bootstrap; a drift against "
    "purchase_price_at_plan warns, and one that breaks the bank refuses."
)

SOURCE_DIFF = "picks-diff"
SOURCE_NAMES = "state-names"
SOURCE_NONE = "none"


class PlayerRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: int
    name: str


class PlanPick(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    element: int
    name: str
    club: str
    position: str
    slot: int = Field(ge=1, le=SQUAD_SIZE)
    is_captain: bool
    is_vice_captain: bool
    now_cost: float
    starts: bool


class PlanTransfer(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    out: PlayerRef
    into: PlayerRef = Field(alias="in")
    cost: int
    purchase_price_at_plan: float
    # Typed as null, not merely defaulted: freezing a selling price here would
    # be read as authoritative and lose money.
    selling_price: None = None


class ChipWindow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    start_event: int
    stop_event: int


class PlanChipEarmark(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    chip: str
    gw: int
    status: str
    start_event: int | None = None
    stop_event: int | None = None


class PlanInputs(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    final: str
    previous_final: str | None = None
    bootstrap: str


class ExecutionPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    schema_version: int
    gw: int
    team_id: int | None
    deadline: datetime
    chip: str | None
    chip_plan: tuple[PlanChipEarmark, ...] = ()
    chips_used: tuple[ChipUse, ...] = ()
    chips_available: tuple[ChipWindow, ...] = ()
    formation: str
    picks: tuple[PlanPick, ...]
    bench: tuple[int, ...]
    captain: PlayerRef
    vice: PlayerRef
    transfers: tuple[PlanTransfer, ...] = ()
    transfer_source: str
    price_resolution: str = PRICE_RESOLUTION
    price_resolution_note: str = PRICE_RESOLUTION_NOTE
    bank: float
    team_value: float
    free_transfers_banked: int
    source: str
    generated_from: PlanInputs
    bootstrap_snapshot_age_hours: float | None = None
    warnings: tuple[str, ...] = ()

    def to_json_dict(self) -> dict:
        return self.model_dump(mode="json", by_alias=True)

    def planned_picks(self) -> PlannedPicks:
        """Re-validates the plan's 15 slots through the same model the STATE
        block goes through — a hand-edited plan is not trusted."""
        return PlannedPicks(
            picks=tuple(
                PlannedPick(
                    id=pick.element,
                    name=pick.name,
                    position=pick.slot,
                    captain=pick.is_captain,
                    vice=pick.is_vice_captain,
                )
                for pick in self.picks
            )
        )

    def planned_prices(self) -> dict[int, int]:
        """Incoming element -> purchase price in tenths, for drift checks."""
        return {t.into.id: round(t.purchase_price_at_plan * 10) for t in self.transfers}


def parse_plan(document: object, *, gw: int) -> ExecutionPlan:
    """The plan is the single source for a POST, so it is validated as
    strictly as any inbound API payload."""
    if not isinstance(document, dict):
        raise ValueError("a plan file must contain a JSON object")
    version = document.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ValueError(
            f"plan schema_version is {version!r}, this build supports "
            f"{SCHEMA_VERSION} — rebuild it with: python -m fpl plan --gw {gw}"
        )
    plan = ExecutionPlan.model_validate(document)
    if plan.gw != gw:
        raise ValueError(
            f"plan is for gw{plan.gw}, not the requested gw{gw} — refusing to "
            "apply a different gameweek's plan"
        )
    return plan


def validate_formation(bootstrap: Bootstrap, picks: PlannedPicks) -> None:
    by_id = bootstrap.player_by_id()
    unknown = sorted(p.id for p in picks.picks if p.id not in by_id)
    if unknown:
        raise ValueError(f"picks reference unknown player ids: {unknown}")
    role_of = {p.id: by_id[p.id].element_type for p in picks.picks}
    slot_role = {p.position: role_of[p.id] for p in picks.picks}
    if slot_role[1] is not Position.GKP:
        raise ValueError("position 1 must be a goalkeeper")
    if slot_role[BACKUP_GK_SLOT] is not Position.GKP:
        raise ValueError("position 12 must be a goalkeeper (first bench slot)")
    squad = Counter(role_of.values())
    if squad != Counter(SQUAD_SHAPE):
        shape = ", ".join(f"{count} {pos.name}" for pos, count in squad.items())
        raise ValueError(f"squad must be 2 GKP / 5 DEF / 5 MID / 3 FWD, got {shape}")
    xi = Counter(slot_role[slot] for slot in range(1, XI_SIZE + 1))
    if xi[Position.GKP] != 1:
        raise ValueError("the XI must contain exactly 1 GKP")
    if xi[Position.DEF] < 3:
        raise ValueError("the XI must contain at least 3 DEF")
    if xi[Position.MID] < 2:
        raise ValueError("the XI must contain at least 2 MID")
    if xi[Position.FWD] < 1:
        raise ValueError("the XI must contain at least 1 FWD")


def validate_club_limit(bootstrap: Bootstrap, picks: PlannedPicks) -> None:
    by_id = bootstrap.player_by_id()
    teams = bootstrap.team_by_id()
    counts = Counter(by_id[p.id].team for p in picks.picks)
    over = sorted(team for team, count in counts.items() if count > MAX_PER_CLUB)
    if over:
        detail = ", ".join(f"{teams[team].short_name} {counts[team]}" for team in over)
        raise ValueError(f"max 3 per club exceeded: {detail}")


def build_plan(
    *,
    gw: int,
    state: DecisionState,
    bootstrap: Bootstrap,
    source: str,
    bootstrap_source: str,
    previous_state: DecisionState | None = None,
    previous_source: str | None = None,
    bootstrap_age_hours: float | None = None,
) -> ExecutionPlan:
    if state.gw != gw:
        raise ValueError(
            f"STATE block is for gw{state.gw}, not the requested gw{gw} — "
            "refusing to plan a different gameweek's decision"
        )
    if previous_state is not None and previous_state.gw != gw - 1:
        raise ValueError(
            f"previous STATE block is for gw{previous_state.gw}, expected "
            f"gw{gw - 1} — refusing to diff against the wrong gameweek"
        )
    picks = state.picks
    if picks is None:
        raise ValueError(
            f"the gw{gw} STATE block has no 'picks:' section — the execution "
            "plan needs the 15-slot list"
        )
    validate_formation(bootstrap, picks)
    validate_club_limit(bootstrap, picks)
    deadline = bootstrap.deadline_for(gw)
    if deadline is None:
        raise ValueError(f"gw{gw} has no deadline in the cached bootstrap — refetch it")

    warnings: list[str] = []
    if state.team_id is None:
        warnings.append(
            "team_id is null in the STATE block — the executor must be given "
            "--team-id explicitly"
        )
    chip = _validate_chip(gw, state, bootstrap)
    transfers, transfer_source = _resolve_transfers(
        gw, state, bootstrap, previous_state, warnings
    )
    _warn_transfer_cost(gw, state, previous_state, chip, len(transfers), warnings)

    by_id = bootstrap.player_by_id()
    teams = bootstrap.team_by_id()
    return ExecutionPlan(
        schema_version=SCHEMA_VERSION,
        gw=gw,
        team_id=state.team_id,
        deadline=deadline,
        chip=chip,
        chip_plan=_chip_plan(bootstrap, state, warnings),
        chips_used=state.chips_used,
        chips_available=_chips_available(gw, bootstrap, state),
        formation=_formation(by_id, picks),
        picks=tuple(
            PlanPick(
                element=pick.id,
                name=by_id[pick.id].web_name,
                club=teams[by_id[pick.id].team].short_name,
                position=by_id[pick.id].element_type.name,
                slot=pick.position,
                is_captain=pick.captain,
                is_vice_captain=pick.vice,
                now_cost=by_id[pick.id].price_m,
                starts=pick.starts,
            )
            for pick in picks.in_position_order()
        ),
        bench=tuple(pick.id for pick in picks.bench()),
        captain=_ref(by_id[picks.captain().id]),
        vice=_ref(by_id[picks.vice().id]),
        transfers=transfers,
        transfer_source=transfer_source,
        bank=state.bank,
        team_value=state.team_value,
        free_transfers_banked=state.free_transfers_banked,
        source=source,
        generated_from=PlanInputs(
            final=source, previous_final=previous_source, bootstrap=bootstrap_source
        ),
        bootstrap_snapshot_age_hours=bootstrap_age_hours,
        warnings=tuple(warnings),
    )


def _ref(player: Player) -> PlayerRef:
    return PlayerRef(id=player.id, name=player.web_name)


def _formation(by_id: dict[int, Player], picks: PlannedPicks) -> str:
    """FPL convention: outfield only, the goalkeeper is implicit."""
    roles = Counter(by_id[p.id].element_type for p in picks.picks if p.starts)
    return f"{roles[Position.DEF]}-{roles[Position.MID]}-{roles[Position.FWD]}"


def _validate_chip(gw: int, state: DecisionState, bootstrap: Bootstrap) -> str | None:
    if state.chip is None:
        return None
    windows = [chip for chip in bootstrap.chips if chip.name == state.chip]
    if not windows:
        offered = ", ".join(sorted({chip.name for chip in bootstrap.chips}))
        raise ValueError(
            f"unknown chip {state.chip!r} — the bootstrap chips array offers: "
            f"{offered or 'none'}"
        )
    active = next(
        (w for w in windows if w.start_event <= gw <= w.stop_event), None
    )
    if active is None:
        ranges = ", ".join(f"{w.start_event}-{w.stop_event}" for w in windows)
        raise ValueError(
            f"gw{gw} is outside every window for chip {state.chip!r} ({ranges})"
        )
    used = [
        use
        for use in state.chips_used
        if use.chip == state.chip and active.start_event <= use.gw <= active.stop_event
    ]
    if used:
        raise ValueError(
            f"chip {state.chip!r} was already used in gw{used[0].gw}, inside the "
            f"same window ({active.start_event}-{active.stop_event})"
        )
    return state.chip


def _chips_available(
    gw: int, bootstrap: Bootstrap, state: DecisionState
) -> tuple[ChipWindow, ...]:
    return tuple(
        ChipWindow(
            name=chip.name, start_event=chip.start_event, stop_event=chip.stop_event
        )
        for chip in bootstrap.chips
        if chip.stop_event >= gw
        and not any(
            use.chip == chip.name and chip.start_event <= use.gw <= chip.stop_event
            for use in state.chips_used
        )
    )


def _chip_plan(
    bootstrap: Bootstrap, state: DecisionState, warnings: list[str]
) -> tuple[PlanChipEarmark, ...]:
    entries = []
    for earmark in state.chip_plan:
        window = next(
            (
                chip
                for chip in bootstrap.chips
                if chip.name == earmark.chip
                and chip.start_event <= earmark.gw <= chip.stop_event
            ),
            None,
        )
        if window is None:
            warnings.append(
                f"chip_plan earmark {earmark.chip!r} for gw{earmark.gw} falls in "
                "no bootstrap chip window — it is a forecast, and will not "
                "activate as written"
            )
        entries.append(
            PlanChipEarmark(
                chip=earmark.chip,
                gw=earmark.gw,
                status=earmark.status,
                start_event=window.start_event if window else None,
                stop_event=window.stop_event if window else None,
            )
        )
    return tuple(entries)


def _resolve_transfers(
    gw: int,
    state: DecisionState,
    bootstrap: Bootstrap,
    previous_state: DecisionState | None,
    warnings: list[str],
) -> tuple[tuple[PlanTransfer, ...], str]:
    assert state.picks is not None
    by_id = bootstrap.player_by_id()
    previous_picks = previous_state.picks if previous_state is not None else None
    if previous_picks is not None:
        outs = sorted(previous_picks.ids() - state.picks.ids())
        ins = sorted(state.picks.ids() - previous_picks.ids())
        # Before the name cross-check: a player who has left the game entirely
        # deserves its own message, not a spurious "readings disagree".
        unknown = sorted(pid for pid in [*outs, *ins] if pid not in by_id)
        if unknown:
            raise ValueError(f"transfers reference unknown player ids: {unknown}")
        _cross_check_names(gw, outs, ins, state, by_id, warnings)
        source = SOURCE_DIFF
    else:
        outs, ins = _resolve_by_name(gw, state, bootstrap)
        source = SOURCE_NAMES
    if not outs and not ins:
        return (), SOURCE_NONE
    declared = {(t.out, t.into): t.cost for t in state.transfers_made}
    transfers = tuple(
        PlanTransfer(
            out=_ref(by_id[out]),
            into=_ref(by_id[incoming]),
            cost=declared.get((by_id[out].web_name, by_id[incoming].web_name), 0),
            purchase_price_at_plan=by_id[incoming].price_m,
        )
        for out, incoming in pair_by_position(outs, ins, by_id)
    )
    return transfers, source


def _cross_check_names(
    gw: int,
    outs: list[int],
    ins: list[int],
    state: DecisionState,
    by_id: dict[int, Player],
    warnings: list[str],
) -> None:
    if not state.transfers_made:
        if outs or ins:
            warnings.append(
                f"transfers_made is empty but the gw{gw} squad differs from "
                f"gw{gw - 1} by {len(outs)} player(s) — the id diff is "
                "authoritative and was used"
            )
        return
    diff_out = sorted(by_id[pid].web_name for pid in outs)
    diff_in = sorted(by_id[pid].web_name for pid in ins)
    state_out = sorted(t.out for t in state.transfers_made)
    state_in = sorted(t.into for t in state.transfers_made)
    if diff_out != state_out or diff_in != state_in:
        raise ValueError(
            "the two transfer readings disagree — picks diff: "
            f"out {diff_out}, in {diff_in}; transfers_made: "
            f"out {state_out}, in {state_in}. Fix the STATE block; refusing to "
            "pick a winner"
        )


def _resolve_by_name(
    gw: int, state: DecisionState, bootstrap: Bootstrap
) -> tuple[list[int], list[int]]:
    assert state.picks is not None
    squad = state.picks.ids()
    outs: list[int] = []
    ins: list[int] = []
    for entry in state.transfers_made:
        out_id = _resolve_name(entry.out, bootstrap)
        in_id = _resolve_name(entry.into, bootstrap)
        if in_id not in squad:
            raise ValueError(
                f"transfers_made names {entry.into!r} (id {in_id}) as an incoming "
                f"transfer, but that player is not in the gw{gw} squad"
            )
        if out_id in squad:
            raise ValueError(
                f"transfers_made names {entry.out!r} (id {out_id}) as an outgoing "
                f"transfer, but that player is still in the gw{gw} squad"
            )
        outs.append(out_id)
        ins.append(in_id)
    return outs, ins


def _resolve_name(name: str, bootstrap: Bootstrap) -> int:
    teams = bootstrap.team_by_id()
    wanted = name.casefold()
    matches = [p for p in bootstrap.elements if p.web_name.casefold() == wanted]
    if len(matches) == 1:
        return matches[0].id
    if not matches:
        near = [p for p in bootstrap.elements if wanted in p.web_name.casefold()][:5]
        hint = (
            f" — closest names: {'; '.join(_describe(p, teams) for p in near)}"
            if near
            else ""
        )
        raise ValueError(f"no player named {name!r} in the cached bootstrap{hint}")
    raise ValueError(
        f"ambiguous transfer name {name!r} — {len(matches)} players match: "
        + "; ".join(_describe(p, teams) for p in matches)
        + ". Refusing to guess which one to transfer — disambiguate by adding a "
        "picks: block to the previous gameweek's final.md, so transfers derive "
        "from the id diff instead of the name"
    )


def _describe(player: Player, teams: dict[int, Team]) -> str:
    return (
        f"id {player.id} {player.web_name} ({teams[player.team].short_name} "
        f"{player.element_type.name} £{player.price_m:.1f}m)"
    )


def pair_by_position(
    outs: list[int], ins: list[int], by_id: dict[int, Player]
) -> list[tuple[int, int]]:
    outs_by_role: dict[Position, list[int]] = defaultdict(list)
    ins_by_role: dict[Position, list[int]] = defaultdict(list)
    for out in outs:
        outs_by_role[by_id[out].element_type].append(out)
    for incoming in ins:
        ins_by_role[by_id[incoming].element_type].append(incoming)
    out_shape = {role: len(ids) for role, ids in outs_by_role.items()}
    in_shape = {role: len(ids) for role, ids in ins_by_role.items()}
    if out_shape != in_shape:
        raise ValueError(
            "transfers must swap position-for-position — "
            f"out: {_role_shape(outs_by_role)}, in: {_role_shape(ins_by_role)}"
        )
    return [
        (out, incoming)
        for role in sorted(outs_by_role)
        for out, incoming in zip(sorted(outs_by_role[role]), sorted(ins_by_role[role]))
    ]


def _role_shape(by_role: dict[Position, list[int]]) -> str:
    if not by_role:
        return "none"
    return ", ".join(f"{len(ids)} {role.name}" for role, ids in sorted(by_role.items()))


def _warn_transfer_cost(
    gw: int,
    state: DecisionState,
    previous_state: DecisionState | None,
    chip: str | None,
    count: int,
    warnings: list[str],
) -> None:
    if count == 0:
        return
    if chip in NO_HIT_CHIPS:
        warnings.append(f"chip {chip} → no hit on {count} transfer(s)")
        return
    if previous_state is not None:
        free = previous_state.free_transfers_banked
        basis = f"gw{previous_state.gw} STATE free_transfers_banked"
    else:
        free = state.free_transfers_banked
        basis = (
            f"gw{gw} STATE free_transfers_banked — no gw{gw - 1} STATE was read, "
            "and that field counts the free transfers available at the NEXT "
            "deadline, so this estimate may be wrong"
        )
    if count <= free:
        return
    hit = (count - free) * DEFAULT_TRANSFER_HIT
    warnings.append(
        f"{count} transfer(s) vs {free} free ({basis}) → implied hit -{hit} pts"
    )
