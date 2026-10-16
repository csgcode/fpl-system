"""`fpl objective`: the reference scorer's report for one gameweek's squad.

Local only: the squad comes from the previous final.md's STATE block, the
two readings from players-*.json and inputs-*.json, prices from the cached
bootstrap. Every figure is printed on one labelled line so a reader (or a
grader) can quote it verbatim.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from fpl import objective
from fpl.objective import (
    CHIP_GATE,
    FREE_GATE,
    HIT_GATE,
    HORIZON,
    NEAR_TIE,
    NEAR_TIE_MOVE,
    TRANSFER_CHIPS,
    Market,
    Move,
    PlanReport,
    Row,
    Scored,
    best_lineup,
    boundary_pairs,
    captain_ranking,
    dead_bench,
    evaluate_plan,
    legal_singles,
    load_views,
    pool,
    ret5_text,
)
from fpl.state import parse_state
from fpl.store import SnapshotStore

DECISIONS_ROOT = Path("data/decisions")
ANALYSIS_ROOT = Path("data/analysis")
SQUAD_SIZE = 15
RELAYED = "relayed"
TIE_BREAK_LABEL = "tie-break move:"
UNVERIFIED = "now_cost — unverified"
_FINAL_DIR = re.compile(r"^gw(\d+)$")


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--analysis-root", type=Path, default=ANALYSIS_ROOT,
                        help="root holding gw{N}/players-*.json and inputs-*.json")
    parser.add_argument("--from-final", type=Path,
                        help=f"the squad's STATE block (default: the latest "
                             f"{DECISIONS_ROOT}/gw{{M}}/final.md with M < N)")
    parser.add_argument("--sell", type=_sell_list,
                        help="selling prices from my-team, ID:£m,... covering all 15 ids")
    parser.add_argument("--bank", type=float, help="bank in £m (default: the STATE bank)")
    parser.add_argument("--free-transfers", type=int,
                        help="free transfers this deadline (default: the STATE's banked count)")
    parser.add_argument("--moves", type=_move_list,
                        help="the plan as OUT:IN id pairs, comma-separated, or 'none'; "
                             "grades it (exit 1 on FAIL)")
    parser.add_argument("--chip", choices=TRANSFER_CHIPS)
    parser.add_argument("--top", type=int, default=10, help="single moves listed")
    parser.add_argument("--format", choices=("table", "json"), default="table")


def run(data_root: Path, args: argparse.Namespace) -> int:
    gw = args.gw
    final_path = args.from_final or latest_final(gw)
    state = parse_state(final_path.read_text(encoding="utf-8"))
    if state.picks is None:
        raise ValueError(f"{final_path} has no picks: in its STATE block")
    squad = [pick.id for pick in sorted(state.picks.picks, key=lambda p: p.position)]
    blend, prior = load_views(SnapshotStore(data_root), args.analysis_root, gw)
    missing = [pid for pid in squad if pid not in blend or pid not in prior]
    if missing:
        raise ValueError(f"squad ids missing from the EP views: {', '.join(map(str, missing))}")
    market = _market(args, state.bank, state.free_transfers_banked, squad, blend)
    moves = args.moves if args.moves is not None else []
    report = evaluate_plan(squad, moves, market, blend, prior, chip=args.chip)
    singles = legal_singles(squad, market, blend, prior)
    if args.format == "json":
        print(json.dumps(_document(gw, final_path, squad, market, report, singles, blend,
                                   prior, args), indent=1, ensure_ascii=False))
    else:
        for line in _table(gw, final_path, squad, market, report, singles, blend, prior, args):
            print(line)
    if args.moves is None:
        return 0
    return 1 if report.verdict_reasons else 0


def latest_final(gw: int, root: Path = DECISIONS_ROOT) -> Path:
    candidates = []
    for child in root.iterdir() if root.is_dir() else ():
        match = _FINAL_DIR.match(child.name)
        if match and int(match.group(1)) < gw and (child / "final.md").is_file():
            candidates.append((int(match.group(1)), child / "final.md"))
    if not candidates:
        raise ValueError(f"no {root}/gw{{M}}/final.md with M < {gw}; pass --from-final")
    return max(candidates)[1]


def _market(args: argparse.Namespace, bank: float, free: int, squad: list[int],
            blend: dict[int, Row]) -> Market:
    bank_tenths = round((args.bank if args.bank is not None else bank) * 10)
    free_transfers = args.free_transfers if args.free_transfers is not None else free
    if args.sell is None:
        return Market({pid: blend[pid].price for pid in squad}, bank_tenths, free_transfers,
                      UNVERIFIED)
    if set(args.sell) != set(squad):
        missing = sorted(set(squad) - set(args.sell))
        extra = sorted(set(args.sell) - set(squad))
        raise ValueError(f"--sell must cover all {SQUAD_SIZE} squad ids or none "
                         f"(missing {missing}, not in the squad {extra})")
    return Market(dict(args.sell), bank_tenths, free_transfers, RELAYED)


def _sell_list(raw: str) -> dict[int, int]:
    prices = {}
    for item in raw.split(","):
        pid, _, price = item.strip().partition(":")
        try:
            prices[int(pid)] = round(float(price) * 10)
        except ValueError:
            raise argparse.ArgumentTypeError(f"bad --sell item {item!r}; use ID:£m") from None
    return prices


def _move_list(raw: str) -> list[Move]:
    if raw.strip().lower() == "none":
        return []
    moves = []
    for item in raw.split(","):
        out, _, into = item.strip().partition(":")
        try:
            moves.append(Move(int(out), int(into)))
        except ValueError:
            raise argparse.ArgumentTypeError(f"bad --moves item {item!r}; use OUT:IN") from None
    return moves


# ------------------------------------------------------------- rendering


def _m(tenths: int) -> str:
    return f"{tenths / 10:.1f}"


def _pair(scored: Scored, view: dict[int, Row]) -> str:
    return f"{view[scored.move.out].name} → {view[scored.move.into].name}"


def _gate_note(scored: Scored, *, free: bool = True) -> str:
    gate = FREE_GATE if free else HIT_GATE
    if scored.blend >= gate - 1e-9 and (scored.prior >= -1e-9 if free else scored.prior > 1e-9):
        return f"passes {'free' if free else 'hit'} gate"
    if scored.prior < -1e-9 or (not free and scored.prior <= 1e-9):
        return "fails (prior sign flip)"
    return f"fails (blend < {gate})"


def _table(gw, final_path, squad, market, report: PlanReport, singles, blend, prior, args):
    horizon_end = gw if report.chip == "freehit" else gw + HORIZON - 1
    total = sum(market.sell[pid] for pid in squad)
    yield (f"objective gw{gw} — horizon GW{gw}–GW{horizon_end}; squad from {final_path}")
    yield (f"sell basis: {market.sell_basis} (Σ sell {_m(total)} + bank {_m(market.bank)} = "
           f"{_m(total + market.bank)})")
    yield f"baseline: blend {report.baseline[0]:.3f} prior {report.baseline[1]:.3f}"
    yield (f"legal single moves: {len(singles)} (pool {len(pool(blend, prior))}); "
           f"top {args.top} by blend:")
    for rank, scored in enumerate(singles[:args.top], start=1):
        incoming = blend[scored.move.into]
        yield (f"  {rank} | {_pair(scored, blend)} | {scored.blend:+.3f} | "
               f"{scored.prior:+.3f} | bank {_m(scored.bank_after)} | "
               f"p4₃ {_p4_text(incoming)} | ret5 {ret5_text(incoming.ret5)} | {_gate_note(scored)}")
    yield _plan_line(report, market, blend)
    hit_count = report.hits // 4
    by_gain = sorted(report.marginals, key=lambda s: (s.blend, s.move.out))
    hits = {s.move for s in by_gain[:hit_count]}
    for scored in report.marginals:
        note = ("chip package" if report.chip
                else _gate_note(scored, free=scored.move not in hits))
        yield f"  move {_pair(scored, blend)}: {scored.blend:+.3f} / {scored.prior:+.3f} — {note}"
    if report.next_best is not None:
        nb = report.next_best
        yield (f"after plan, best single: {_pair(nb, blend)} {nb.blend:+.3f} / "
               f"{nb.prior:+.3f} — {_gate_note(nb)}")
    else:
        yield "after plan, best single: none legal"
    if report.reference:
        moves = ", ".join(f"{_pair(s, blend)} {s.blend:+.3f} / {s.prior:+.3f}"
                          for s in report.reference)
        yield (f"reference (greedy): {moves} — blend {report.reference_gain[0]:+.3f} "
               f"prior {report.reference_gain[1]:+.3f}")
    else:
        yield "reference (greedy): bank — no move passes its gate"
    yield from _tie_break_lines(report, blend, graded=args.moves is not None)
    if args.moves is None:
        yield "verdict: none — pass --moves OUT:IN,... (or --moves none to bank) to grade a plan"
    elif report.verdict_reasons:
        yield "verdict: FAIL: " + "; ".join(report.verdict_reasons)
    else:
        yield "verdict: PASS"
    yield from _lineup_lines(gw, list(report.squad_after), blend)


def _p4_text(row: Row) -> str:
    if row.p4_3 is None or row.position not in objective.P4_CALIBRATED:
        return "-"
    return f"{row.p4_3:.2f}"


def _tie_break_lines(report: PlanReport, blend, *, graded: bool):
    if report.chip:
        return
    if not report.tie_breaks:
        yield f"{TIE_BREAK_LABEL} none within {NEAR_TIE_MOVE}"
    for tie in report.tie_breaks:
        yield (f"{TIE_BREAK_LABEL} {_pair(tie.incumbent, blend)} {tie.incumbent.blend:+.3f} v "
               f"{_pair(tie.challenger, blend)} {tie.challenger.blend:+.3f} — winner "
               f"{_pair(tie.winner, blend)} ({tie.reason})")
    if not graded:
        return
    if not report.tie_groups:
        yield "tie-break: none in band"
    taken = {scored.move for scored in report.marginals}
    for group in report.tie_groups:
        winner = _pair(group.winner, blend)
        others = [m for m in group.members if m != group.winner and m.move in taken]
        if group.winner.move in taken:
            yield f"tie-break: plan takes {winner}"
        elif others:
            yield (f"tie-break: plan takes {_pair(others[0], blend)}, not the winner "
                   f"{winner}")
        else:
            yield f"tie-break: plan takes none of the tie; winner {winner}"


def _plan_line(report: PlanReport, market: Market, blend) -> str:
    moves = ", ".join(_pair(s, blend) for s in report.marginals) or "none"
    if report.chip:
        tail = (f"transfers {report.used} under {report.chip} (FT unchanged "
                f"({market.free_transfers})); chip gate: ≥ {CHIP_GATE} over the greedy plan")
    else:
        tail = (f"transfers {report.used} (free {market.free_transfers}, hits {report.hits}); "
                f"FT next {report.ft_next}")
    return (f"plan: {moves} — blend {report.gain[0]:+.3f} prior {report.gain[1]:+.3f}; "
            f"bank {_m(report.bank_after)}; {tail}")


def _lineup_lines(gw: int, squad: list[int], blend: dict[int, Row]):
    lineup = best_lineup(squad, blend, 0)
    names = ", ".join(blend[pid].name for pid in lineup.xi)
    captains = ", ".join(f"{blend[pid].name} {ep:.3f} {p0:.2f}"
                         for pid, ep, p0 in captain_ranking(lineup, blend))
    formation = "-".join(map(str, lineup.formation))
    yield (f"GW{gw} XI {formation} {lineup.points:.3f}: {names}; captain top 5: {captains}")
    pairs = boundary_pairs(squad, lineup, blend)
    shown = " ; ".join(
        f"{blend[a].name} {ea:.3f} (DefCon {blend[a].defcon_share:.3f}) | "
        f"{blend[b].name} {eb:.3f} ({blend[b].defcon_share:.3f})"
        for a, b, ea, eb, _ in pairs) or "none"
    yield f"boundary pairs within {NEAR_TIE}: {shown}"
    dead = set(dead_bench(lineup, blend))
    bench = ", ".join(
        f"{blend[pid].name} {blend[pid].ep(0):.3f}"
        + (f" (p {blend[pid].p_start0:.2f} — dead)" if pid in dead else "")
        for pid in lineup.bench)
    yield f"bench: {bench}"


def _scored_dict(scored: Scored, view) -> dict:
    return {"out": scored.move.out, "in": scored.move.into, "name": _pair(scored, view),
            "blend": round(scored.blend, 3), "prior": round(scored.prior, 3),
            "bank_after": scored.bank_after / 10}


def _p4_value(row: Row) -> float | None:
    return None if _p4_text(row) == "-" else round(row.p4_3 or 0.0, 3)


def _document(gw, final_path, squad, market, report: PlanReport, singles, blend, prior, args):
    lineup = best_lineup(list(report.squad_after), blend, 0)
    return {
        "gw": gw,
        "squad_from": str(final_path),
        "sell_basis": market.sell_basis,
        "budget": (sum(market.sell[pid] for pid in squad) + market.bank) / 10,
        "baseline": {"blend": round(report.baseline[0], 3),
                     "prior": round(report.baseline[1], 3)},
        "legal_singles": len(singles),
        "pool": len(pool(blend, prior)),
        "top": [{**_scored_dict(s, blend), "p4_3": _p4_value(blend[s.move.into]),
                 "ret5": list(blend[s.move.into].ret5) if blend[s.move.into].ret5 else None}
                for s in singles[:args.top]],
        "plan": {
            "moves": [_scored_dict(s, blend) for s in report.marginals],
            "gain": {"blend": round(report.gain[0], 3), "prior": round(report.gain[1], 3)},
            "bank_after": report.bank_after / 10, "used": report.used, "hits": report.hits,
            "ft_next": report.ft_next, "chip": report.chip,
        },
        "next_best": _scored_dict(report.next_best, blend) if report.next_best else None,
        "reference": [_scored_dict(s, blend) for s in report.reference],
        "tie_breaks": [{"incumbent": _scored_dict(tie.incumbent, blend),
                        "challenger": _scored_dict(tie.challenger, blend),
                        "winner": _scored_dict(tie.winner, blend), "reason": tie.reason}
                       for tie in report.tie_breaks],
        "reference_gain": {"blend": round(report.reference_gain[0], 3),
                           "prior": round(report.reference_gain[1], 3)},
        "verdict": (None if args.moves is None
                    else "FAIL" if report.verdict_reasons else "PASS"),
        "verdict_reasons": list(report.verdict_reasons),
        "xi": {"formation": "-".join(map(str, lineup.formation)), "ids": list(lineup.xi),
               "points": round(lineup.points, 3), "captain": lineup.captain},
        "bench": list(lineup.bench),
        "dead_bench": dead_bench(lineup, blend),
    }
