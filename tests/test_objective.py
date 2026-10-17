"""Reference scorer: the spec objective, move legality, gates and the greedy
reference — over synthetic views (no real-player data)."""

from __future__ import annotations

import json

import pytest

from fpl.ep import DEFAULT_CONFIG, force_prior_weight, load_inputs
from fpl.models import Bootstrap, Position
from fpl.objective import (
    FORMATIONS,
    Market,
    Move,
    Row,
    Criterion,
    Scored,
    TieBreak,
    apply_moves,
    best_lineup,
    boundary_pairs,
    captain_ranking,
    dead_bench,
    evaluate_plan,
    ft_next,
    greedy_reference,
    legal_singles,
    load_views,
    move_marginals,
    objective,
    pool,
    rows_from_documents,
    squad_violations,
    tie_break_moves,
    tie_break_winner,
)
from fpl.store import SnapshotStore
from tests.factories import (
    bootstrap_payload,
    element_summary_payload,
    event_payload,
    past_season_payload,
    player_payload,
    team_payload,
)

G, D, M, F = Position.GKP, Position.DEF, Position.MID, Position.FWD
LAYOUT = [G, G] + [D] * 5 + [M] * 5 + [F] * 3
SQUAD = list(range(1, 16))


def row(pid, position, ep, *, club=None, price=50, status="a", p0=1.0, unc="LOW",
        share=0.0, p4_3=None, ret5=None) -> Row:
    eps = tuple(ep) if isinstance(ep, (tuple, list)) else (float(ep),) * 6
    return Row(id=pid, name=f"P{pid}", position=position, club=club or pid, price=price,
               status=status, ep_gw=eps, p_start0=p0, uncertainty=unc, defcon_share=share,
               p4_3=p4_3, ret5=ret5)


def squad_view(eps=None, **kw) -> dict[int, Row]:
    eps = eps or [5, 1, 4, 4, 4, 2, 2, 5, 5, 5, 3, 3, 6, 4, 1]
    return {pid: row(pid, pos, ep, **kw) for pid, pos, ep in zip(SQUAD, LAYOUT, eps)}


def market(bank=0, free=1, sell=None) -> Market:
    return Market(sell=sell or {pid: 50 for pid in SQUAD}, bank=bank, free_transfers=free,
                  sell_basis="relayed")


# --------------------------------------------------------------- lineups


def test_best_lineup_picks_the_best_formation_and_benches_gk2_first():
    view = squad_view()
    lineup = best_lineup(SQUAD, view, 0)
    # GK 5; DEF 4,4,4; MID 5,5,5,3; FWD 6,4 beats 3-4-3's third FWD (1).
    assert lineup.formation == (3, 5, 2)
    assert lineup.captain == 13
    assert lineup.points == pytest.approx(5 + 12 + 21 + 10 + 6)
    assert lineup.bench[0] == 2
    assert len(lineup.xi) == 11 and len(lineup.bench) == 4


def test_tied_formations_resolve_to_the_first_in_order():
    view = squad_view([1] * 15)
    assert best_lineup(SQUAD, view, 0).formation == FORMATIONS[0] == (3, 4, 3)


def test_exactly_one_goalkeeper_even_when_the_backup_outscores_outfielders():
    view = squad_view([9, 8, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    lineup = best_lineup(SQUAD, view, 0)
    assert [pid for pid in lineup.xi if view[pid].position == G] == [1]
    assert lineup.bench[0] == 2


def test_captain_doubles_the_xi_maximum():
    view = squad_view([1] * 15)
    view[13] = row(13, F, 7)
    assert best_lineup(SQUAD, view, 0).points == pytest.approx(10 + 7 * 2)


def test_objective_sums_the_horizon_from_start():
    eps = {k: float(k + 1) for k in range(6)}
    view = {pid: row(pid, pos, tuple(eps[k] for k in range(6)))
            for pid, pos in zip(SQUAD, LAYOUT)}
    per_k = [best_lineup(SQUAD, view, k).points for k in range(6)]
    assert objective(SQUAD, view) == pytest.approx(sum(per_k))
    assert objective(SQUAD, view, start=1, horizon=2) == pytest.approx(per_k[1] + per_k[2])


def test_squad_violations_names_shape_and_club_breaches():
    view = squad_view()
    assert squad_violations(SQUAD, view) == []
    view[4] = row(4, D, 1, club=3)
    view[5] = row(5, D, 1, club=3)
    view[6] = row(6, D, 1, club=3)
    assert any("club 3" in v for v in squad_violations(SQUAD, view))
    assert any("DEF" in v for v in squad_violations(SQUAD[:-1] + [4], view))


# ----------------------------------------------------------------- moves


def with_pool(view, *rows_):
    return {**view, **{r.id: r for r in rows_}}


def test_apply_moves_refuses_each_illegal_move_by_name():
    view = with_pool(squad_view(), row(20, M, 9, price=70), row(21, D, 9),
                     row(22, M, 9, status="i"), row(23, M, 9, club=8),
                     row(24, M, 9, club=8))
    for moves, word in (
        ([Move(8, 21)], "position"),
        ([Move(8, 20)], "afford"),
        ([Move(8, 22)], "pool"),
        ([Move(8, 99)], "pool"),
        ([Move(99, 21)], "not in the squad"),
        ([Move(8, 9)], "already"),
    ):
        with pytest.raises(ValueError, match=word):
            apply_moves(SQUAD, moves, market(), view)
    view[9] = row(9, M, 5, club=8)
    with pytest.raises(ValueError, match="club 8"):
        apply_moves(SQUAD, [Move(10, 23), Move(11, 24)], market(), view)


def test_apply_moves_keeps_money_in_integer_tenths():
    view = with_pool(squad_view(), row(20, M, 9, price=63))
    sell = {pid: 50 for pid in SQUAD} | {8: 62}
    squad, bank = apply_moves(SQUAD, [Move(8, 20)], market(bank=1, sell=sell), view)
    assert bank == 0 and isinstance(bank, int)
    assert 20 in squad and 8 not in squad


def test_pool_excludes_unavailable_and_ids_missing_from_either_reading():
    blend = with_pool(squad_view(), row(20, M, 9), row(21, M, 9, status="s"),
                      row(22, M, 9, status="u"), row(23, M, 9, status="n"),
                      row(24, M, 9, status="i"), row(25, M, 9, status="d"),
                      row(26, M, 9))
    prior = {pid: r for pid, r in blend.items() if pid != 26}
    ids = pool(blend, prior)
    assert {20, 25} <= ids and not ids & {21, 22, 23, 24, 26}
    ins = {s.move.into for s in legal_singles(SQUAD, market(), blend, prior)}
    assert ins == {20, 25}


def test_legal_singles_are_sorted_by_blend_then_out_then_in():
    blend = with_pool(squad_view(), row(20, M, 9), row(21, M, 9))
    singles = legal_singles(SQUAD, market(), blend, blend)
    gains = [s.blend for s in singles]
    assert gains == sorted(gains, reverse=True)
    top = [(s.move.out, s.move.into) for s in singles[:2]]
    assert top == [(11, 20), (11, 21)]


def test_marginal_undoes_only_the_named_pair():
    blend = with_pool(squad_view(), row(20, M, 9), row(21, F, 8))
    moves = [Move(11, 20), Move(15, 21)]
    plan = apply_moves(SQUAD, moves, market(), blend)[0]
    undone = [pid for pid in SQUAD if pid != 15] + [21]
    marginals = move_marginals(SQUAD, moves, market(), blend, blend)
    assert marginals[0].move == moves[0]
    assert marginals[0].blend == pytest.approx(objective(plan, blend) - objective(undone, blend))


# ---------------------------------------------------------------- greedy


def gains_view(*extra):
    return with_pool(squad_view(), *extra)


def test_greedy_takes_a_free_move_at_or_above_two():
    blend = gains_view(row(20, M, 3 + 2.0 / 6))  # replaces a 3-EP bench-edge MID
    assert [s.move for s in greedy_reference(SQUAD, market(), blend, blend)] == [Move(11, 20)]


def test_greedy_banks_below_two():
    blend = gains_view(row(20, M, 3 + 1.9 / 6))
    assert greedy_reference(SQUAD, market(), blend, blend) == ()


def test_greedy_skips_a_prior_sign_flip_for_the_next_best():
    blend = gains_view(row(20, M, 4), row(21, M, 3.5))
    prior = gains_view(row(20, M, 2), row(21, M, 3.5))
    taken = greedy_reference(SQUAD, market(), blend, prior)
    assert [s.move for s in taken] == [Move(11, 21)]


def test_greedy_needs_six_and_positive_prior_once_free_transfers_run_out():
    blend = gains_view(row(20, M, 4), row(21, M, 3 + 5.9 / 6))
    taken = greedy_reference(SQUAD, market(free=1), blend, blend)
    assert [s.move for s in taken] == [Move(11, 20)]
    blend = gains_view(row(20, M, 4), row(21, M, 5))
    taken = greedy_reference(SQUAD, market(free=1), blend, blend)
    assert [s.move for s in taken] == [Move(11, 21), Move(12, 20)]
    prior = gains_view(row(20, M, 3), row(21, M, 5))  # the hit's prior gain is 0, not > 0
    taken = greedy_reference(SQUAD, market(free=1), blend, prior)
    assert [s.move for s in taken] == [Move(11, 21)]


def test_ft_next():
    assert ft_next(free=1, used=0) == 2
    assert ft_next(free=2, used=1) == 2
    assert ft_next(free=5, used=0) == 5
    assert ft_next(free=1, used=1) == 1
    assert ft_next(free=1, used=3) == 1


# ------------------------------------------------------------ evaluation


def test_evaluate_plan_reports_gates_hits_and_the_next_best():
    blend = gains_view(row(20, M, 4), row(21, M, 3.2))
    report = evaluate_plan(SQUAD, [Move(11, 20)], market(free=2), blend, blend)
    assert report.used == 1 and report.hits == 0 and report.ft_next == 2
    assert report.gain[0] == pytest.approx(6.0)
    assert report.verdict_reasons == ()
    assert report.next_best is not None and report.next_best.move == Move(12, 21)
    bad = evaluate_plan(SQUAD, [Move(12, 21)], market(free=2), blend, blend)
    assert any("free gate" in r for r in bad.verdict_reasons)
    assert any("reference" in r for r in bad.verdict_reasons)
    hit = evaluate_plan(SQUAD, [Move(11, 20), Move(12, 21)], market(free=1), blend, blend)
    assert hit.hits == 4 and hit.ft_next == 1
    assert any("hit gate" in r for r in hit.verdict_reasons)


def test_evaluate_plan_flags_a_free_transfer_left_unused_on_a_passing_move():
    blend = gains_view(row(20, M, 4))
    report = evaluate_plan(SQUAD, [], market(free=1), blend, blend)
    assert any("further free move" in r for r in report.verdict_reasons)


def test_free_hit_scores_gameweek_n_only():
    eps = (4.0, 0, 0, 0, 0, 0)
    blend = gains_view(row(20, M, eps))
    report = evaluate_plan(SQUAD, [Move(11, 20)], market(), blend, blend, chip="freehit")
    assert report.baseline[0] == pytest.approx(best_lineup(SQUAD, blend, 0).points)
    assert report.gain[0] == pytest.approx(1.0)
    assert report.ft_next is None and report.hits == 0


def test_wildcard_needs_six_over_the_greedy_plan():
    blend = gains_view(row(20, M, 4), row(21, M, 4))
    report = evaluate_plan(SQUAD, [Move(11, 20), Move(12, 21)], market(), blend, blend,
                           chip="wildcard")
    assert report.hits == 0
    assert any("chip gate" in r for r in report.verdict_reasons)


# ------------------------------------------------------- captain / bench


def test_captain_ranking_is_raw_unless_certainty_is_given():
    view = squad_view([1] * 15)
    view[13] = row(13, F, 6.0, unc="HIGH", p0=0.7)
    view[8] = row(8, M, 5.5, unc="LOW")
    lineup = best_lineup(SQUAD, view, 0)
    raw = captain_ranking(lineup, view)
    assert [r[0] for r in raw[:2]] == [13, 8] and raw[0][2] == 0.7
    weighted = captain_ranking(lineup, view, certainty={"LOW": 1, "MED": .92, "HIGH": .80})
    assert [r[0] for r in weighted[:2]] == [8, 13]
    assert weighted[1][1] == pytest.approx(4.8)


def test_boundary_pairs_are_formation_legal_only():
    eps = [5, 1, 4, 4, 4, 3.9, 2, 5, 5, 5, 3.95, 3.9, 6, 6, 5]
    view = squad_view(eps)
    lineup = best_lineup(SQUAD, view, 0)
    assert lineup.formation == (3, 4, 3)
    pairs = {(a, b) for a, b, *_ in boundary_pairs(SQUAD, lineup, view)}
    assert (11, 6) in pairs  # MID 3.95 out, DEF 3.9 in: 4-3-3 is legal
    assert (11, 12) in pairs
    assert (3, 12) not in pairs  # DEF out, MID in: two defenders is not
    assert all(not (view[a].position == G) ^ (view[b].position == G) for a, b in pairs)
    for a, b, ea, eb, gap in boundary_pairs(SQUAD, lineup, view):
        assert gap == pytest.approx(ea - eb) and abs(gap) <= 0.25


def test_dead_bench_lists_bench_players_unlikely_to_start():
    view = squad_view()
    view[2] = row(2, G, 1, p0=0.03)
    view[15] = row(15, F, 1, p0=0.5)
    lineup = best_lineup(SQUAD, view, 0)
    assert dead_bench(lineup, view) == [2]


# ------------------------------------------------------------ tie-break

MID = frozenset({M})


def tie_view(*, a_ep=3 + 2.4 / 6, b_ep=3 + 2.1 / 6, a_p4=0.30, b_p4=0.42, a_ret=(1, 5),
             b_ret=(4, 5), eps=None):
    return with_pool(squad_view(eps), row(20, M, a_ep, p4_3=a_p4, ret5=a_ret),
                     row(21, M, b_ep, p4_3=b_p4, ret5=b_ret))


def single(out, into, gain):
    return Scored(Move(out, into), gain, gain, 0)


def test_tie_break_picks_the_steadier_incoming_player():
    a, b = single(11, 20, 2.40), single(11, 21, 2.10)
    assert tie_break_moves([a, b], tie_view(), calibrated=MID) == [
        TieBreak(a, b, b, "p4 0.42 v 0.30", Criterion.P4)]


def test_no_tie_outside_the_band():
    a, b = single(11, 20, 2.70), single(11, 21, 2.10)
    assert tie_break_moves([a, b], tie_view(), calibrated=MID) == []


def test_ties_need_the_same_out_player():
    a, b = single(11, 20, 2.40), single(12, 21, 2.10)
    assert tie_break_moves([a, b], tie_view(), calibrated=MID) == []


def test_a_challenger_must_pass_the_free_gate():
    a, b = single(11, 20, 2.40), single(11, 21, 1.95)
    assert tie_break_moves([a, b], tie_view(), calibrated=MID) == []


def test_ret5_breaks_an_equal_p4():
    a, b = single(11, 20, 2.40), single(11, 21, 2.10)
    view = tie_view(a_p4=0.40, b_p4=0.42)
    assert tie_break_moves([a, b], view, calibrated=MID) == [
        TieBreak(a, b, b, "ret5 4/5 v 1/5", Criterion.RET5)]
    view = tie_view(a_p4=0.40, b_p4=0.42, a_ret=(3, 5), b_ret=(3, 4))
    assert tie_break_moves([a, b], view, calibrated=MID) == [
        TieBreak(a, b, a, "blend", Criterion.BLEND)]


def test_uncalibrated_position_skips_p4():
    a, b = single(11, 20, 2.40), single(11, 21, 2.10)
    view = tie_view(a_p4=0.90, b_p4=0.10)
    assert tie_break_moves([a, b], view, calibrated=frozenset()) == [
        TieBreak(a, b, b, "ret5 4/5 v 1/5", Criterion.RET5)]
    view = tie_view(a_p4=0.90, b_p4=0.10, a_ret=(2, 5), b_ret=(2, 5))
    assert tie_break_moves([a, b], view, calibrated=frozenset()) == [
        TieBreak(a, b, a, "blend", Criterion.BLEND)]


def test_ret5_with_zero_rounds_is_na():
    a, b = single(11, 20, 2.40), single(11, 21, 2.10)
    for a_ret, b_ret in (((0, 0), (4, 5)), ((1, 5), (0, 0)), (None, (4, 5))):
        view = tie_view(a_p4=None, b_p4=None, a_ret=a_ret, b_ret=b_ret)
        assert tie_break_moves([a, b], view, calibrated=MID) == [
            TieBreak(a, b, a, "n/a — blend", Criterion.BLEND)]


def test_ret5_needs_three_rounds_for_each_incoming_player():
    a, b = single(11, 20, 2.40), single(11, 21, 2.10)
    few = tie_view(a_p4=None, b_p4=None, a_ret=(3, 5), b_ret=(1, 1))
    assert tie_break_winner(a, b, few, calibrated=frozenset()) == (
        a, "n/a — blend", Criterion.BLEND)
    enough = tie_view(a_p4=None, b_p4=None, a_ret=(1, 5), b_ret=(3, 3))
    assert tie_break_winner(a, b, enough, calibrated=frozenset()) == (
        b, "ret5 3/3 v 1/5", Criterion.RET5)


def test_greedy_reference_takes_the_tie_break_winner():
    view = tie_view()
    taken = greedy_reference(SQUAD, market(), view, view, calibrated=MID)
    assert [s.move for s in taken] == [Move(11, 21)]
    view = tie_view(a_ret=None, b_ret=None)
    taken = greedy_reference(SQUAD, market(), view, view, calibrated=frozenset())
    assert [s.move for s in taken] == [Move(11, 20)]


def test_plan_taking_the_tie_break_winner_passes_the_reference_check():
    view = tie_view()
    report = evaluate_plan(SQUAD, [Move(11, 21)], market(), view, view, calibrated=MID)
    assert report.verdict_reasons == ()
    assert [(t.incumbent.move, t.winner.move, t.reason) for t in report.tie_breaks] \
        == [(Move(11, 20), Move(11, 21), "p4 0.42 v 0.30")]
    report = evaluate_plan(SQUAD, [Move(11, 20)], market(), view, view, calibrated=MID)
    assert len(report.verdict_reasons) == 1
    assert "tie-break" in report.verdict_reasons[0]
    assert "P11 → P21" in report.verdict_reasons[0]


def test_a_blend_decided_tie_adds_no_reason():
    view = tie_view(a_p4=None, b_p4=None, a_ret=None, b_ret=None)
    report = evaluate_plan(SQUAD, [Move(11, 20)], market(), view, view, calibrated=MID)
    assert report.verdict_reasons == ()


def test_a_tie_the_plan_does_not_touch_leaves_the_gain_bar_alone():
    """C replaces P12 at +2.15. The blend-best single is A (P11 → P20, +2.40);
    adding B, which wins A's tie at +2.10, must not lower the bar for C."""
    def view(with_b):
        v = with_pool(squad_view(), row(20, M, 3 + 2.4 / 6, p4_3=0.30, ret5=(1, 5)),
                      row(22, M, 3 + 2.15 / 6))
        if with_b:
            v[21] = row(21, M, 3 + 2.1 / 6, p4_3=0.42, ret5=(4, 5))
        return v

    for with_b in (False, True):
        v = view(with_b)
        report = evaluate_plan(SQUAD, [Move(12, 22)], market(), v, v, calibrated=MID)
        assert any("below the blend-only greedy reference +2.400" in reason
                   for reason in report.verdict_reasons), with_b
    v = view(True)
    report = evaluate_plan(SQUAD, [Move(11, 21)], market(), v, v, calibrated=MID)
    assert report.verdict_reasons == ()


def bank_view():
    """A (P11 → P20, £5.0m, +2.4) and B (P11 → P21, £5.5m, +2.1) tie and B wins
    on ret5. The goalkeeper P22 (£5.5m, +2.2) stays affordable from a £0.5m
    bank only after the cheaper A, so the tie-break reference is [B] at +2.1
    while the blend-only reference is [A, P2 → P22] at +4.6."""
    eps = [5, 1, 4, 4, 4, 2, 2, 5, 5, 5, 3, 3.5, 6, 4, 1]
    return with_pool(squad_view(eps), row(20, M, 3 + 2.4 / 6, ret5=(1, 5)),
                     row(21, M, 3 + 2.1 / 6, price=55, ret5=(4, 5)),
                     row(22, G, 5 + 2.2 / 6, price=55))


def test_the_tie_break_reference_bars_a_plan_that_takes_its_winners():
    view, none = bank_view(), frozenset()
    report = evaluate_plan(SQUAD, [Move(11, 21)], market(bank=5, free=2), view, view,
                           calibrated=none)
    assert [s.move for s in report.reference] == [Move(11, 21)]
    assert report.blend_reference_gain[0] == pytest.approx(4.6)
    assert report.verdict_reasons == ()


def test_a_plan_off_the_tie_break_keeps_the_blend_only_bar_when_references_diverge():
    view, none = bank_view(), frozenset()
    report = evaluate_plan(SQUAD, [Move(11, 20), Move(2, 22)], market(bank=5, free=2),
                           view, view, calibrated=none)
    assert any("departs from the tie-break" in r for r in report.verdict_reasons)


def chain_view(a_ret, b_ret, c_ret):
    return with_pool(squad_view(), row(20, M, 3 + 2.4 / 6, ret5=a_ret),
                     row(21, M, 3 + 2.3 / 6, ret5=b_ret), row(22, M, 3 + 2.1 / 6, ret5=c_ret))


def test_a_tie_chain_is_judged_by_its_final_winner():
    view = chain_view((2, 5), (2, 5), (4, 5))
    none = frozenset()
    for move in (Move(11, 20), Move(11, 21)):
        report = evaluate_plan(SQUAD, [move], market(), view, view, calibrated=none)
        (tie,) = [r for r in report.verdict_reasons if "departs from the tie-break" in r]
        assert "takes P11 → P22 (ret5 4/5 v 2/5)" in tie, move
    report = evaluate_plan(SQUAD, [Move(11, 22)], market(), view, view, calibrated=none)
    assert report.verdict_reasons == ()


def test_a_group_is_decided_by_the_criterion_that_unseated_the_blend_best_move():
    view = chain_view((1, 5), (4, 5), (4, 5))
    report = evaluate_plan(SQUAD, [], market(), view, view, calibrated=frozenset())
    (group,) = report.tie_groups
    assert [t.criterion for t in group.ties] == [Criterion.RET5, Criterion.BLEND]
    assert group.winner.move == Move(11, 21) and group.decided_by is Criterion.RET5
    view = chain_view((3, 5), (3, 5), (3, 5))
    report = evaluate_plan(SQUAD, [], market(), view, view, calibrated=frozenset())
    (group,) = report.tie_groups
    assert group.winner == group.best and group.decided_by is Criterion.BLEND


def test_a_displaced_move_names_the_final_winner_not_an_intermediate_one():
    view = chain_view((1, 5), (3, 5), (5, 5))
    report = evaluate_plan(SQUAD, [Move(11, 20)], market(), view, view,
                           calibrated=frozenset())
    (reason,) = report.verdict_reasons
    assert "takes P11 → P22" in reason and "P11 → P21" not in reason


def test_the_chip_gate_measures_against_the_blend_only_reference():
    view = tie_view()
    report = evaluate_plan(SQUAD, [Move(11, 20)], market(), view, view, chip="wildcard",
                           calibrated=MID)
    assert [s.move for s in report.reference] == [Move(11, 21)]
    (reason,) = report.verdict_reasons
    assert "+0.000 / +0.000 over the greedy plan" in reason


def test_next_best_after_the_winner_skips_the_displaced_swap():
    view = tie_view(eps=[5, 1, 4, 4, 4, 2, 2, 5, 5, 5, 3, 3.5, 6, 4, 1])
    report = evaluate_plan(SQUAD, [Move(11, 21)], market(free=2), view, view, calibrated=MID)
    assert report.verdict_reasons == ()
    assert report.next_best is not None and report.next_best.move != Move(21, 20)


def test_rows_without_consistency_fields_load():
    bootstrap = Bootstrap.model_validate(bootstrap_payload(
        elements=[player_payload(id=1, element_type=3), player_payload(id=2, element_type=3)],
        teams=[team_payload(id=1)], events=[event_payload(id=GW, is_next=True)]))
    old = {"id": 1, "ep_gw": [1.0] * 6}
    new = {"id": 2, "ep_gw": [1.0] * 6, "p4_gw": [0.3, 0.6, 0.0, 0.9], "returns5": [2, 4]}
    rows = rows_from_documents([old, new], bootstrap)
    assert rows[1].p4_3 is None and rows[1].ret5 is None
    assert rows[2].p4_3 == pytest.approx(0.3) and rows[2].ret5 == (2, 4)


# ----------------------------------------------------------- load_views

GW = 3


def _seed(tmp_path, *, extra_player=False):
    """`extra_player` adds an unjudged MID above £4.5m."""
    store = SnapshotStore(tmp_path / "raw")
    players = [player_payload(id=1, web_name="Alpha", team=1, element_type=3, now_cost=60),
               player_payload(id=2, web_name="Beta", team=2, element_type=3, now_cost=45)]
    if extra_player:
        players.append(player_payload(id=3, web_name="Gamma", team=2, element_type=3,
                                      now_cost=80))
    store.save(GW, "bootstrap", bootstrap_payload(
        elements=players, teams=[team_payload(id=1, short_name="TST"),
                                 team_payload(id=2, short_name="OPP")],
        events=[event_payload(id=GW, is_next=True)]), "seed://test")
    store.save(GW, "players/summary-1", element_summary_payload(
        history_past=[past_season_payload(minutes=2700, expected_goals="9.0")]), "seed://test")
    gw_dir = tmp_path / "analysis" / f"gw{GW}"
    gw_dir.mkdir(parents=True)
    (gw_dir / "fixtures.json").write_text(json.dumps({
        "schema_version": 1, "gw": GW, "base_lambda": {"home": 1.54, "away": 1.33},
        "ratings": {"TST": {"att": 1.0, "defw": 1.0}, "OPP": {"att": 1.0, "defw": 1.0}},
        "fixtures": [{"club": "TST", "gw": g, "opp": "OPP", "venue": "H", "lambda_att": 1.5,
                      "lambda_def": 1.0, "p_cs": 0.3} for g in range(GW, GW + 6)]}))
    for position in ("GKP", "DEF", "FWD"):
        (gw_dir / f"inputs-{position}.json").write_text(json.dumps(
            {"schema_version": 1, "gw": GW, "position": position, "players": []}))
        (gw_dir / f"players-{position}.json").write_text("[]")
    (gw_dir / "inputs-MID.json").write_text(json.dumps({
        "schema_version": 1, "gw": GW, "position": "MID",
        "players": [{"id": 1, "name": "Alpha", "p_start": 0.9, "uncertainty": "MED",
                     "notes": "starter"}]}))
    return store, tmp_path / "analysis"


def test_load_views_prior_equals_the_ep_cli_at_prior_weight_one(tmp_path, capsys):
    from fpl.__main__ import main

    store, analysis = _seed(tmp_path)
    gw_dir = analysis / f"gw{GW}"
    assert main(["--data-root", str(tmp_path / "raw"), "ep", "--gw", str(GW),
                 "--position", "MID", "--analysis-root", str(analysis),
                 "--decisions-root", str(tmp_path / "decisions")]) == 0
    prior_out = tmp_path / "prior-MID.json"
    assert main(["--data-root", str(tmp_path / "raw"), "ep", "--gw", str(GW),
                 "--position", "MID", "--analysis-root", str(analysis),
                 "--decisions-root", str(tmp_path / "decisions"),
                 "--prior-weight", "1.0", "--out", str(prior_out)]) == 0
    capsys.readouterr()
    blend, prior = load_views(store, analysis, GW)
    expected = {r["id"]: tuple(r["ep_gw"]) for r in json.loads(prior_out.read_text())}
    assert {pid: r.ep_gw for pid, r in prior.items()} == expected
    written = json.loads((gw_dir / "players-MID.json").read_text())[0]
    assert blend[1].ep_gw == tuple(written["ep_gw"])
    assert blend[1].price == 60 and blend[1].club == 1 and blend[1].uncertainty == "MED"
    assert blend[1].p_start0 == 0.9
    assert blend[1].defcon_share == pytest.approx(
        written["terms"]["defcon"] / written["ep_total6"])
    assert force_prior_weight(load_inputs(gw_dir / "inputs-MID.json"), 1.0)


def test_load_views_allows_unjudged_players_the_blend_view_lacks(tmp_path):
    from fpl.__main__ import main

    store, analysis = _seed(tmp_path, extra_player=True)
    assert main(["--data-root", str(tmp_path / "raw"), "ep", "--gw", str(GW),
                 "--position", "MID", "--analysis-root", str(analysis),
                 "--decisions-root", str(tmp_path / "decisions"),
                 "--allow-missing-ids", "3"]) == 0
    blend, prior = load_views(store, analysis, GW)
    assert 3 not in blend and 3 not in prior and 1 in prior


def _write_mid_players(tmp_path, analysis):
    from fpl.__main__ import main

    assert main(["--data-root", str(tmp_path / "raw"), "ep", "--gw", str(GW),
                 "--position", "MID", "--analysis-root", str(analysis),
                 "--decisions-root", str(tmp_path / "decisions")]) == 0
    return analysis / f"gw{GW}" / "players-MID.json"


def _restamp(path, digest):
    rows = json.loads(path.read_text())
    for document in rows:
        if digest is None:
            document.pop("model", None)
        else:
            document["model"] = digest
    path.write_text(json.dumps(rows))
    return rows


def test_objective_refuses_mixed_model_digests(tmp_path):
    store, analysis = _seed(tmp_path)
    mid = _write_mid_players(tmp_path, analysis)
    other = dict(json.loads(mid.read_text())[0], id=2, model="0badc0de")
    (analysis / f"gw{GW}" / "players-DEF.json").write_text(json.dumps([other]))
    with pytest.raises(ValueError, match="players files built by another model version") as exc:
        load_views(store, analysis, GW)
    message = str(exc.value)
    assert "players-DEF.json" in message and "0badc0de" in message
    assert "players-MID.json" in message and DEFAULT_CONFIG.digest() in message
    assert "rerun `fpl ep`" in message


def test_objective_refuses_a_digest_other_than_the_code(tmp_path):
    store, analysis = _seed(tmp_path)
    _restamp(_write_mid_players(tmp_path, analysis), "0badc0de")
    with pytest.raises(ValueError, match="players files built by another model version") as exc:
        load_views(store, analysis, GW)
    assert "players-MID.json" in str(exc.value) and "0badc0de" in str(exc.value)


def test_load_views_skips_the_digest_check_for_historical_files(tmp_path):
    store, analysis = _seed(tmp_path)
    _restamp(_write_mid_players(tmp_path, analysis), "0badc0de")
    blend, prior = load_views(store, analysis, GW, check_digest=False)
    assert 1 in blend and 1 in prior


def test_objective_accepts_rows_without_a_digest(tmp_path):
    store, analysis = _seed(tmp_path)
    _restamp(_write_mid_players(tmp_path, analysis), None)
    blend, prior = load_views(store, analysis, GW)
    assert 1 in blend and 1 in prior


def test_objective_judges_legacy_and_current_rows_on_the_current_digest(tmp_path):
    store, analysis = _seed(tmp_path)
    mid = _write_mid_players(tmp_path, analysis)
    legacy = {k: v for k, v in json.loads(mid.read_text())[0].items() if k != "model"}
    (analysis / f"gw{GW}" / "players-DEF.json").write_text(json.dumps([dict(legacy, id=2)]))
    blend, _ = load_views(store, analysis, GW)
    assert set(blend) == {1, 2}
