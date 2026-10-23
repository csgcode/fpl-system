"""The squad optimizer's objective, scored in code (docs/ep-model.md §7).

Objective: Σ over the horizon of the best XI's EP plus the captain's EP (the
XI maximum, so the captain is counted twice). The best XI is exact: it is
the best of every legal formation, each filled by the top players per
position, and the squad's maximum is always in it, so the captain term never
changes which XI wins.

Two singles with the same outgoing player whose blend gains are within
NEAR_TIE_MOVE are a near tie: the reference takes the steadier incoming
player (P(≥4) over the next three gameweeks where that reading is calibrated,
then observed returns over the last five rounds, read only when both incoming
players have RET5_MIN_ROUNDS of them), else the higher blend. The gain bar
stays the blend-only greedy reference; a plan earns the tie's shortfall only
by taking that tie's winner, and a plan that takes every steadiness-decided
winner is held at most to the tie-break greedy reference.

Every figure is read twice: on the blend view (players-*.json, what the
analysts published) and on the prior-only view (the same inputs at prior
weight 1.0). A move must gain on blend and must not flip sign on prior-only.
Money is integer tenths throughout, as the API states it.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import NamedTuple

from fpl.ep import (
    DEFAULT_CONFIG,
    build_predictions,
    force_prior_weight,
    load_fixtures,
    load_inputs,
)
from fpl.models import PLAYING_POSITIONS, Bootstrap, PlayerStatus, Position
from fpl.season_store import History
from fpl.service import load_cached_bootstrap, load_cached_summaries
from fpl.store import SnapshotStore

HORIZON = 6
FREE_GATE = 2.0
HIT_GATE = 6.0
CHIP_GATE = 6.0
HIT_COST = 4
NEAR_TIE = 0.25
NEAR_TIE_MOVE = 0.5
# Positions whose p4 beats a base rate among likely starters (combined.json
# comparison.p4[pos].starters.skill > 0): only there may p4 decide a tie-break.
P4_CALIBRATED: frozenset[Position] = frozenset({Position.GKP, Position.FWD})
P4_TIE_GAP = 0.03
RET5_TIE_GAP = 0.2
RET5_MIN_ROUNDS = 3
P4_WINDOW = 3
BLEND_DECIDED = "blend"
DEAD_BENCH = 0.5
MAX_FREE_TRANSFERS = 5
REFERENCE_TOLERANCE = 0.05
TRANSFER_CHIPS = ("wildcard", "freehit")
SHAPE = {Position.GKP: 2, Position.DEF: 5, Position.MID: 5, Position.FWD: 3}
CLUB_LIMIT = 3
FORMATIONS = ((3, 4, 3), (3, 5, 2), (4, 3, 3), (4, 4, 2), (4, 5, 1), (5, 2, 3), (5, 3, 2),
              (5, 4, 1))
POOL_STATUSES = frozenset({PlayerStatus.AVAILABLE.value, PlayerStatus.DOUBTFUL.value})
COVERAGE_PRICE_FLOOR_TENTHS = 45
# Gains are sums of rounded floats: compare and sort on a rounded value so a
# tie in exact arithmetic stays a tie.
_EPS = 1e-9
_ORDER_DP = 9


@dataclass(frozen=True)
class Row:
    id: int
    name: str
    position: Position
    club: int
    price: int
    status: str
    ep_gw: tuple[float, ...]
    p_start0: float
    uncertainty: str
    defcon_share: float
    p4_3: float | None = None
    ret5: tuple[int, int] | None = None

    def ep(self, k: int) -> float:
        return self.ep_gw[k] if k < len(self.ep_gw) else 0.0


View = Mapping[int, Row]


@dataclass(frozen=True)
class Market:
    """`sell` is the selling price of each owned player; a player bought
    inside a plan sells at its purchase price (now_cost)."""

    sell: Mapping[int, int]
    bank: int
    free_transfers: int
    sell_basis: str


@dataclass(frozen=True)
class Move:
    out: int
    into: int


@dataclass(frozen=True)
class Scored:
    move: Move
    blend: float
    prior: float
    bank_after: int


class Criterion(Enum):
    P4 = "p4"
    RET5 = "ret5"
    BLEND = "blend"


class TieBreak(NamedTuple):
    incumbent: Scored
    challenger: Scored
    winner: Scored
    reason: str
    criterion: Criterion


@dataclass(frozen=True)
class TieGroup:
    """One greedy step's near tie: the blend-best single and its challengers,
    met in blend order."""

    ties: tuple[TieBreak, ...]

    @property
    def best(self) -> Scored:
        return self.ties[0].incumbent

    @property
    def winner(self) -> Scored:
        return self.ties[-1].winner

    @property
    def members(self) -> tuple[Scored, ...]:
        return (self.best, *(tie.challenger for tie in self.ties))

    @property
    def decided_by(self) -> Criterion:
        """The criterion that put the final winner ahead of the blend-best
        move; blend when the blend-best move won."""
        return Criterion.BLEND if self.winner == self.best else self.deciding.criterion

    @property
    def deciding(self) -> TieBreak:
        """The tie in which the final winner took over."""
        return next(tie for tie in self.ties if tie.challenger == self.winner)


@dataclass(frozen=True)
class Lineup:
    xi: tuple[int, ...]
    bench: tuple[int, ...]
    formation: tuple[int, int, int]
    captain: int
    points: float


@dataclass(frozen=True)
class PlanReport:
    baseline: tuple[float, float]
    gain: tuple[float, float]
    marginals: tuple[Scored, ...]
    bank_after: int
    used: int
    hits: int
    ft_next: int | None
    next_best: Scored | None
    reference: tuple[Scored, ...]
    reference_gain: tuple[float, float]
    verdict_reasons: tuple[str, ...]
    chip: str | None = None
    squad_after: tuple[int, ...] = ()
    tie_groups: tuple[TieGroup, ...] = ()
    blend_reference_gain: tuple[float, float] = (0.0, 0.0)

    @property
    def tie_breaks(self) -> tuple[TieBreak, ...]:
        return tuple(tie for group in self.tie_groups for tie in group.ties)


# ------------------------------------------------------------- objective


def _ranked(squad: Iterable[int], view: View, position: Position, k: int) -> list[int]:
    return sorted((pid for pid in squad if view[pid].position == position),
                  key=lambda pid: (-view[pid].ep(k), pid))


def best_lineup(squad: Sequence[int], view: View, k: int) -> Lineup:
    """Bench: the second goalkeeper first, then outfielders by EP desc."""
    ranked = {position: _ranked(squad, view, position, k) for position in SHAPE}
    best: tuple[float, tuple[int, ...], tuple[int, int, int]] | None = None
    for formation in FORMATIONS:
        d, m, f = formation
        if len(ranked[Position.DEF]) < d or len(ranked[Position.MID]) < m \
                or len(ranked[Position.FWD]) < f or not ranked[Position.GKP]:
            continue
        xi = (ranked[Position.GKP][:1] + ranked[Position.DEF][:d]
              + ranked[Position.MID][:m] + ranked[Position.FWD][:f])
        total = sum(view[pid].ep(k) for pid in xi) + max(view[pid].ep(k) for pid in xi)
        if best is None or total > best[0] + _EPS:
            best = (total, tuple(xi), formation)
    if best is None:
        raise ValueError("no legal formation: the squad lacks a goalkeeper or outfielders")
    total, xi, formation = best
    captain = min(xi, key=lambda pid: (-view[pid].ep(k), pid))
    outfield_bench = sorted((pid for pid in squad if pid not in xi
                             and view[pid].position != Position.GKP),
                            key=lambda pid: (-view[pid].ep(k), pid))
    keepers = [pid for pid in ranked[Position.GKP] if pid not in xi]
    return Lineup(xi, tuple(keepers + outfield_bench), formation, captain, total)


def objective(squad: Sequence[int], view: View, *, start: int = 0,
              horizon: int = HORIZON) -> float:
    return sum(_points(squad, view, k) for k in range(start, start + horizon))


def _points(squad: Sequence[int], view: View, k: int) -> float:
    """best_lineup(...).points without building the lineup: the hot path of
    every move search. The captain is the squad maximum in any formation."""
    eps: dict[Position, list[float]] = {position: [] for position in SHAPE}
    for pid in squad:
        row = view[pid]
        eps[row.position].append(row.ep(k))
    for values in eps.values():
        values.sort(reverse=True)
    prefix = {position: [0.0] for position in SHAPE}
    for position, values in eps.items():
        for value in values:
            prefix[position].append(prefix[position][-1] + value)
    best = None
    for d, m, f in FORMATIONS:
        if d > len(eps[Position.DEF]) or m > len(eps[Position.MID]) \
                or f > len(eps[Position.FWD]) or not eps[Position.GKP]:
            continue
        total = (prefix[Position.DEF][d] + prefix[Position.MID][m]
                 + prefix[Position.FWD][f])
        best = total if best is None else max(best, total)
    if best is None:
        raise ValueError("no legal formation: the squad lacks a goalkeeper or outfielders")
    keeper = eps[Position.GKP][0]
    captain = max(values[0] for values in eps.values() if values)
    return keeper + best + captain


def squad_violations(squad: Sequence[int], view: View) -> list[str]:
    problems = []
    unknown = [pid for pid in squad if pid not in view]
    if unknown:
        return [f"ids not in the view: {', '.join(map(str, unknown))}"]
    duplicates = sorted(pid for pid, n in Counter(squad).items() if n > 1)
    if duplicates:
        problems.append(f"duplicate ids: {', '.join(map(str, duplicates))}")
    if len(squad) != sum(SHAPE.values()):
        problems.append(f"{len(squad)} players, not {sum(SHAPE.values())}")
    counts = Counter(view[pid].position for pid in squad)
    for position, need in SHAPE.items():
        if counts[position] != need:
            problems.append(f"{counts[position]} {position.name}, not {need}")
    clubs = Counter(view[pid].club for pid in squad)
    for club, n in sorted(clubs.items()):
        if n > CLUB_LIMIT:
            problems.append(f"{n} players from club {club} (max {CLUB_LIMIT})")
    return problems


# ----------------------------------------------------------------- moves


def pool(blend: View, prior: View) -> set[int]:
    """Buyable ids: present in both readings, status a or d."""
    return {pid for pid, row in blend.items() if pid in prior and row.status in POOL_STATUSES}


def _sell_price(pid: int, market: Market, view: View) -> int:
    return market.sell[pid] if pid in market.sell else view[pid].price


def _label(move: Move, view: View) -> str:
    def name(pid: int) -> str:
        return view[pid].name if pid in view else str(pid)
    return f"{name(move.out)} → {name(move.into)}"


def apply_moves(squad: Sequence[int], moves: Sequence[Move], market: Market,
                view: View, *, buyable: set[int] | None = None) -> tuple[list[int], int]:
    """The squad after every move, and the bank left. `buyable` defaults to
    the ids of `view` with status a or d."""
    buyable = buyable if buyable is not None else {
        pid for pid, row in view.items() if row.status in POOL_STATUSES}
    current = list(squad)
    bank = market.bank
    for move in moves:
        label = _label(move, view)
        if move.out not in current:
            raise ValueError(f"{label}: {move.out} is not in the squad")
        if move.into in current:
            raise ValueError(f"{label}: {move.into} is already in the squad")
        if move.into not in buyable:
            raise ValueError(f"{label}: {move.into} is not in the pool (unknown, or status "
                             f"not a/d)")
        if view[move.into].position != view[move.out].position:
            raise ValueError(f"{label}: wrong position ({view[move.out].position.name} out, "
                             f"{view[move.into].position.name} in)")
        bank += _sell_price(move.out, market, view) - view[move.into].price
        current[current.index(move.out)] = move.into
    if bank < 0:
        raise ValueError(f"{', '.join(_label(m, view) for m in moves)}: cannot afford — "
                         f"bank after {bank / 10:.1f}")
    clubs = Counter(view[pid].club for pid in current)
    for move in moves:
        club = view[move.into].club
        if clubs[club] > CLUB_LIMIT:
            raise ValueError(f"{_label(move, view)}: {clubs[club]} players from club {club} "
                             f"(max {CLUB_LIMIT})")
    return current, bank


def _swap(squad: Sequence[int], out: int, into: int) -> list[int]:
    return [into if pid == out else pid for pid in squad]


def legal_singles(squad: Sequence[int], market: Market, blend: View,
                  prior: View) -> list[Scored]:
    """Every affordable, club-legal single swap into the pool, sorted by blend
    gain desc, then out id, then in id."""
    buyable = pool(blend, prior)
    base_blend, base_prior = objective(squad, blend), objective(squad, prior)
    clubs = Counter(blend[pid].club for pid in squad)
    scored = []
    for out in squad:
        budget = market.bank + _sell_price(out, market, blend)
        for into in buyable:
            row = blend[into]
            if into in squad or row.position != blend[out].position or row.price > budget:
                continue
            if row.club != blend[out].club and clubs[row.club] >= CLUB_LIMIT:
                continue
            after = _swap(squad, out, into)
            scored.append(Scored(Move(out, into), objective(after, blend) - base_blend,
                                 objective(after, prior) - base_prior, budget - row.price))
    scored.sort(key=lambda s: (-round(s.blend, _ORDER_DP), s.move.out, s.move.into))
    return scored


def move_marginals(squad: Sequence[int], moves: Sequence[Move], market: Market,
                   blend: View, prior: View) -> list[Scored]:
    """Each move's marginal: the plan minus the plan with that pair undone."""
    plan, bank = apply_moves(squad, moves, market, blend, buyable=pool(blend, prior))
    marginals = []
    for move in moves:
        undone = _swap(plan, move.into, move.out)
        marginals.append(Scored(
            move,
            objective(plan, blend) - objective(undone, blend),
            objective(plan, prior) - objective(undone, prior),
            bank,
        ))
    return marginals


def _after(market: Market, move: Move, view: View, bank: int) -> Market:
    sell = {pid: price for pid, price in market.sell.items() if pid != move.out}
    sell[move.into] = view[move.into].price
    return Market(sell, bank, market.free_transfers, market.sell_basis)


def _passes(scored: Scored, *, free: bool) -> bool:
    if free:
        return scored.blend >= FREE_GATE - _EPS and scored.prior >= -_EPS
    return scored.blend >= HIT_GATE - _EPS and scored.prior > _EPS


def _ratio(ret5: tuple[int, int] | None) -> float | None:
    return ret5[0] / ret5[1] if ret5 and ret5[1] >= RET5_MIN_ROUNDS else None


def ret5_text(ret5: tuple[int, int] | None) -> str:
    return f"{ret5[0]}/{ret5[1]}" if ret5 else "-"


def tie_break_winner(a: Scored, b: Scored, view: View, *, calibrated: frozenset[Position]
                     ) -> tuple[Scored, str, Criterion]:
    """The winner of a near tie, why, and which criterion decided it. A is the
    move ahead on blend; B wins only on a clearly steadier incoming player:
    P(≥4) first where that position is calibrated, then the observed return
    rate when both players have RET5_MIN_ROUNDS rounds."""
    row_a, row_b = view[a.move.into], view[b.move.into]
    if row_a.position in calibrated and row_a.p4_3 is not None and row_b.p4_3 is not None \
            and abs(row_b.p4_3 - row_a.p4_3) >= P4_TIE_GAP - _EPS:
        win, lose = (b, a) if row_b.p4_3 > row_a.p4_3 else (a, b)
        return win, (f"p4 {view[win.move.into].p4_3:.2f} v "
                     f"{view[lose.move.into].p4_3:.2f}"), Criterion.P4
    rate_a, rate_b = _ratio(row_a.ret5), _ratio(row_b.ret5)
    if rate_a is None or rate_b is None:
        return a, f"n/a — {BLEND_DECIDED}", Criterion.BLEND
    if abs(rate_b - rate_a) >= RET5_TIE_GAP - _EPS:
        win, lose = (b, a) if rate_b > rate_a else (a, b)
        return win, (f"ret5 {ret5_text(view[win.move.into].ret5)} v "
                     f"{ret5_text(view[lose.move.into].ret5)}"), Criterion.RET5
    return a, BLEND_DECIDED, Criterion.BLEND


def tie_break_moves(singles: Sequence[Scored], view: View, *,
                    calibrated: frozenset[Position], free: bool = True) -> list[TieBreak]:
    """(incumbent, challenger, winner, reason) for each passing single with
    the best passing single's outgoing player and a blend gain within
    NEAR_TIE_MOVE of it. Challengers meet the incumbent in blend order, so
    the last winner is the move the reference takes."""
    passing = sorted((s for s in singles if _passes(s, free=free)),
                     key=lambda s: (-round(s.blend, _ORDER_DP), s.move.out, s.move.into))
    if not passing:
        return []
    best = incumbent = passing[0]
    ties = []
    for challenger in passing[1:]:
        if challenger.move.out != best.move.out \
                or best.blend - challenger.blend > NEAR_TIE_MOVE + _EPS:
            continue
        winner, reason, criterion = tie_break_winner(incumbent, challenger, view,
                                                     calibrated=calibrated)
        ties.append(TieBreak(incumbent, challenger, winner, reason, criterion))
        incumbent = winner
    return ties


def _greedy(squad: Sequence[int], market: Market, blend: View, prior: View,
            calibrated: frozenset[Position] | None, *, tie_break: bool = True
            ) -> tuple[tuple[Scored, ...], tuple[TieGroup, ...]]:
    calibrated = P4_CALIBRATED if calibrated is None else calibrated
    current, state, taken, groups = list(squad), market, [], []
    for _ in range(sum(SHAPE.values())):
        free = len(taken) < market.free_transfers
        candidates = [s for s in legal_singles(current, state, blend, prior)
                      if (s.prior >= -_EPS if free else s.prior > _EPS)]
        if not candidates or not _passes(candidates[0], free=free):
            break
        step = (tie_break_moves(candidates, blend, calibrated=calibrated, free=free)
                if tie_break else [])
        group = TieGroup(tuple(step)) if step else None
        chosen = group.winner if group else candidates[0]
        if group:
            groups.append(group)
        taken.append(chosen)
        current = _swap(current, chosen.move.out, chosen.move.into)
        state = _after(state, chosen.move, blend, chosen.bank_after)
    return tuple(taken), tuple(groups)


def greedy_reference(squad: Sequence[int], market: Market, blend: View, prior: View, *,
                     calibrated: frozenset[Position] | None = None) -> tuple[Scored, ...]:
    """The rule-compliant reference plan: repeatedly the best legal single
    that keeps its prior-only sign, while it passes the gate for its slot
    (free while free transfers last, then a hit). A near tie on the same
    outgoing player goes to the tie-break winner."""
    return _greedy(squad, market, blend, prior, calibrated)[0]


def ft_next(*, free: int, used: int) -> int:
    if used <= free:
        return min(MAX_FREE_TRANSFERS, free - used + 1)
    return 1


def _market_after(market: Market, moves: Sequence[Move], view: View, bank: int) -> Market:
    state = market
    for move in moves:
        state = _after(state, move, view, bank)
    return state


def evaluate_plan(squad: Sequence[int], moves: Sequence[Move], market: Market,
                  blend: View, prior: View, *, chip: str | None = None,
                  calibrated: frozenset[Position] | None = None) -> PlanReport:
    """The plan against the transfer rule. A free hit scores GW N only. A
    transfer chip must beat the greedy no-chip plan, net of its hits, by
    CHIP_GATE on blend without losing on prior-only. Both bars are the
    blend-only greedy reference. Without a chip, a plan that takes any other
    move of a near tie whose final winner is not its blend-best move fails; a
    plan that takes that winner may fall short of the bar by the winner's gap
    to the blend-best move. A plan that takes every such winner is held at
    most to the tie-break greedy reference's gain."""
    if chip is not None and chip not in TRANSFER_CHIPS:
        raise ValueError(f"unknown transfer chip {chip!r}; use {' or '.join(TRANSFER_CHIPS)}")
    horizon = 1 if chip == "freehit" else HORIZON

    def score(ids: Sequence[int]) -> tuple[float, float]:
        return objective(ids, blend, horizon=horizon), objective(ids, prior, horizon=horizon)

    baseline = score(squad)
    plan, bank = apply_moves(squad, moves, market, blend, buyable=pool(blend, prior))
    after = score(plan)
    gain = (after[0] - baseline[0], after[1] - baseline[1])
    marginals = tuple(move_marginals(squad, moves, market, blend, prior)) if moves else ()
    used = len(moves)

    def reference_gain_of(taken: Sequence[Scored]) -> tuple[float, float]:
        ids = list(squad)
        for scored in taken:
            ids = _swap(ids, scored.move.out, scored.move.into)
        ref_after = score(ids)
        return ref_after[0] - baseline[0], ref_after[1] - baseline[1]

    reference, groups = _greedy(squad, market, blend, prior, calibrated)
    reference_gain = reference_gain_of(reference)
    blend_reference = _greedy(squad, market, blend, prior, calibrated, tie_break=False)[0]
    blend_reference_gain = reference_gain_of(blend_reference)
    blend_reference_hits = HIT_COST * max(0, len(blend_reference) - market.free_transfers)

    reasons: list[str] = []
    next_best = None
    if chip is None:
        hits = HIT_COST * max(0, used - market.free_transfers)
        hit_moves = {s.move for s in sorted(marginals, key=lambda s: (s.blend, s.move.out))
                     [:hits // HIT_COST]}
        for scored in marginals:
            free = scored.move not in hit_moves
            if not _passes(scored, free=free):
                gate = (f"free gate (blend ≥ {FREE_GATE}, prior ≥ 0)" if free
                        else f"hit gate (blend ≥ {HIT_GATE}, prior > 0)")
                reasons.append(f"{_label(scored.move, blend)} {scored.blend:+.3f} / "
                               f"{scored.prior:+.3f} fails the {gate}")
        taken = set(moves)
        displaced = set()
        allowance = 0.0
        for group in groups:
            winner = group.winner
            others = [m for m in group.members if m != winner]
            if winner.move in taken:
                displaced.update(Move(winner.move.into, m.move.into) for m in others)
                allowance += group.best.blend - winner.blend
            elif winner != group.best:
                for loser in others:
                    if loser.move in taken:
                        reasons.append(
                            f"{_label(loser.move, blend)} departs from the tie-break: the "
                            f"greedy reference takes {_label(winner.move, blend)} "
                            f"({group.deciding.reason})")
        singles = [s for s in legal_singles(plan, _market_after(market, moves, blend, bank),
                                            blend, prior) if s.move not in displaced]
        passing = [s for s in singles if _passes(s, free=True)]
        next_best = passing[0] if passing else (singles[0] if singles else None)
        if used < market.free_transfers and passing:
            reasons.append(f"further free move passes: {_label(passing[0].move, blend)} "
                           f"{passing[0].blend:+.3f} / {passing[0].prior:+.3f}")
        bar = blend_reference_gain[0] - allowance
        takes_winners = all(group.winner.move in taken for group in groups
                            if group.winner != group.best)
        if takes_winners and reference_gain[0] < bar:
            # A taken winner can change later greedy steps (bank, club limit),
            # so the tie-break reference may fall below the blend-only bar.
            if gain[0] < reference_gain[0] - REFERENCE_TOLERANCE:
                reasons.append(f"plan gain {gain[0]:+.3f} below the tie-break greedy "
                               f"reference {reference_gain[0]:+.3f}")
        elif gain[0] < bar - REFERENCE_TOLERANCE:
            shortfall = f" less the tie-break gap {allowance:.3f}" if allowance > _EPS else ""
            reasons.append(f"plan gain {gain[0]:+.3f} below the blend-only greedy reference "
                           f"{blend_reference_gain[0]:+.3f}{shortfall}")
        next_ft: int | None = ft_next(free=market.free_transfers, used=used)
    else:
        hits = 0
        next_ft = None
        edge = (gain[0] - (blend_reference_gain[0] - blend_reference_hits),
                gain[1] - blend_reference_gain[1])
        if edge[0] < CHIP_GATE - _EPS or edge[1] < -_EPS:
            reasons.append(f"{chip} fails the chip gate: {edge[0]:+.3f} / {edge[1]:+.3f} over "
                           f"the greedy plan (need blend ≥ {CHIP_GATE}, prior ≥ 0)")
    return PlanReport(
        baseline=baseline, gain=gain, marginals=marginals, bank_after=bank, used=used,
        hits=hits, ft_next=next_ft, next_best=next_best, reference=reference,
        reference_gain=reference_gain, verdict_reasons=tuple(reasons), chip=chip,
        squad_after=tuple(plan), tie_groups=groups,
        blend_reference_gain=blend_reference_gain,
    )


# ------------------------------------------------------- captain / bench


def captain_ranking(lineup: Lineup, view: View, k: int = 0, n: int = 5,
                    certainty: Mapping[str, float] | None = None
                    ) -> list[tuple[int, float, float]]:
    """(id, score, p_start0) for the top `n` of the XI. The score is raw
    GW-k EP, or EP × the uncertainty factor when `certainty` maps tags to
    factors."""
    def score(pid: int) -> float:
        factor = certainty.get(view[pid].uncertainty, 1.0) if certainty else 1.0
        return view[pid].ep(k) * factor
    ranked = sorted(lineup.xi, key=lambda pid: (-round(score(pid), _ORDER_DP), pid))
    return [(pid, score(pid), view[pid].p_start0) for pid in ranked[:n]]


def _legal_xi(xi: Iterable[int], view: View) -> bool:
    counts = Counter(view[pid].position for pid in xi)
    return (counts[Position.GKP] == 1 and counts[Position.DEF] >= 3
            and counts[Position.MID] >= 2 and counts[Position.FWD] >= 1)


def boundary_pairs(squad: Sequence[int], lineup: Lineup, view: View, k: int = 0
                   ) -> list[tuple[int, int, float, float, float]]:
    """(xi id, bench id, xi ep, bench ep, gap) for every formation-legal
    XI↔bench swap whose GW-k EP gap is within NEAR_TIE."""
    pairs = []
    for starter in lineup.xi:
        for sub in lineup.bench:
            gap = view[starter].ep(k) - view[sub].ep(k)
            if abs(gap) > NEAR_TIE + _EPS:
                continue
            swapped = [sub if pid == starter else pid for pid in lineup.xi]
            if _legal_xi(swapped, view):
                pairs.append((starter, sub, view[starter].ep(k), view[sub].ep(k), gap))
    return pairs


def dead_bench(lineup: Lineup, view: View) -> list[int]:
    """Bench players with p_start_gw[0] below DEAD_BENCH. The objective scores
    the bench at zero, so a dead slot is reported, never priced."""
    return [pid for pid in lineup.bench if view[pid].p_start0 < DEAD_BENCH - _EPS]


# ------------------------------------------------------------- loading


def _row(player_id: int, document: Mapping, bootstrap_rows: Mapping) -> Row:
    player = bootstrap_rows[player_id]
    p_start_gw = document.get("p_start_gw") or []
    total = float(document.get("ep_total6") or 0.0)
    defcon = float((document.get("terms") or {}).get("defcon", 0.0))
    return Row(
        id=player_id, name=player.web_name, position=player.element_type, club=player.team,
        price=player.now_cost, status=player.status.value,
        ep_gw=tuple(float(v) for v in document["ep_gw"]),
        p_start0=float(p_start_gw[0] if p_start_gw else document.get("p_start", 0.0)),
        uncertainty=str(document.get("uncertainty", "")),
        defcon_share=defcon / total if total else 0.0,
        p4_3=_mean(document["p4_gw"][:P4_WINDOW]) if document.get("p4_gw") else None,
        ret5=(int(returns[0]), int(returns[1])) if (returns := document.get("returns5"))
        else None,
    )


def _mean(values: Sequence[float]) -> float:
    return sum(float(v) for v in values) / len(values)


def rows_from_documents(documents: Iterable[Mapping], bootstrap: Bootstrap) -> dict[int, Row]:
    by_id = bootstrap.player_by_id()
    rows = {}
    for document in documents:
        player_id = int(document["id"])
        if player_id not in by_id:
            raise ValueError(f"id {player_id} is not in the bootstrap")
        rows[player_id] = _row(player_id, document, by_id)
    return rows


def prior_documents(store: SnapshotStore, analysis_root: Path, gw: int,
                    bootstrap: Bootstrap, history: History | None = None) -> list[dict]:
    """The prior-only reading: every inputs-*.json at prior weight 1.0, scored
    and rounded exactly as `fpl ep` writes players-*.json."""
    analysis_dir = analysis_root / f"gw{gw}"
    fixtures = load_fixtures(analysis_dir / "fixtures.json")
    documents: list[dict] = []
    for position in sorted(PLAYING_POSITIONS):
        inputs = force_prior_weight(load_inputs(analysis_dir / f"inputs-{position.name}.json"),
                                    1.0)
        judged = {entry.id for entry in inputs.players}
        members = [p for p in bootstrap.elements if p.element_type == position]
        unjudged = frozenset(p.id for p in members if p.id not in judged
                             and p.now_cost > COVERAGE_PRICE_FLOOR_TENTHS
                             and p.status.value in POOL_STATUSES)
        wanted = [p.id for p in members] + sorted(judged)
        summaries = (history.summaries(gw, wanted, pinned=judged) if history is not None
                     else load_cached_summaries(store, gw, wanted))
        source = history.source if history is not None else "summaries"
        result = build_predictions(bootstrap, summaries, fixtures, inputs, gw=gw,
                                   allow_missing=unjudged, history_from=source)
        documents += result.to_documents()
    return documents


def _check_model_digests(digests: Mapping[Path, set[str]]) -> None:
    # Rows written before the digest existed carry no `model` key; they are
    # legacy, not a mismatch, so only stamped rows are judged. The prior view
    # is rebuilt by this code, so the stamps must also match the code.
    code = DEFAULT_CONFIG.digest()
    found = set().union(*digests.values())
    if not found or found == {code}:
        return
    stamped = "; ".join(f"{path} {', '.join(sorted(seen))}"
                        for path, seen in digests.items() if seen)
    raise ValueError(
        f"players files built by another model version — rerun `fpl ep` for every "
        f"position, or check out the code they were built with. This code is model "
        f"{code}; the files carry {stamped}")


def load_views(store: SnapshotStore, analysis_root: Path, gw: int,
               history: History | None = None, *,
               check_digest: bool = True) -> tuple[dict[int, Row], dict[int, Row]]:
    """(blend, prior): players-*.json as published, and the prior-only
    reading rebuilt in memory from the same inputs. `check_digest=False`
    is for reading historical files, whose stamps may predate this code's
    model; the prior view is then rebuilt with this code regardless."""
    bootstrap = load_cached_bootstrap(store, gw)
    analysis_dir = analysis_root / f"gw{gw}"
    blend_documents: list[dict] = []
    digests: dict[Path, set[str]] = {}
    for position in sorted(PLAYING_POSITIONS):
        path = analysis_dir / f"players-{position.name}.json"
        if not path.is_file():
            raise ValueError(f"no {path} — run `fpl ep --position {position.name}` first")
        documents = json.loads(path.read_text(encoding="utf-8"))
        digests[path] = {d["model"] for d in documents if "model" in d}
        blend_documents += documents
    if check_digest:
        _check_model_digests(digests)
    blend = rows_from_documents(blend_documents, bootstrap)
    prior = rows_from_documents(prior_documents(store, analysis_root, gw, bootstrap, history),
                                bootstrap)
    return blend, prior
