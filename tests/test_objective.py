"""Reference scorer: the spec objective, move legality, gates and the greedy
reference — over synthetic views (no real-player data)."""

from __future__ import annotations

import json

import pytest

from fpl.ep import force_prior_weight, load_inputs
from fpl.models import Position
from fpl.objective import (
    FORMATIONS,
    Market,
    Move,
    Row,
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
    squad_violations,
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
        share=0.0) -> Row:
    eps = tuple(ep) if isinstance(ep, (tuple, list)) else (float(ep),) * 6
    return Row(id=pid, name=f"P{pid}", position=position, club=club or pid, price=price,
               status=status, ep_gw=eps, p_start0=p0, uncertainty=unc, defcon_share=share)


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
                 "--position", "MID", "--analysis-root", str(analysis)]) == 0
    prior_out = tmp_path / "prior-MID.json"
    assert main(["--data-root", str(tmp_path / "raw"), "ep", "--gw", str(GW),
                 "--position", "MID", "--analysis-root", str(analysis),
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
                 "--allow-missing-ids", "3"]) == 0
    blend, prior = load_views(store, analysis, GW)
    assert 3 not in blend and 3 not in prior and 1 in prior
