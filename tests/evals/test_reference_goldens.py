"""The reference scorer on the frozen cycle-code views reproduces every
figure the squad-optimizer plan verified by hand."""

from __future__ import annotations

import pytest

from evals.harness.workspace import SourceError
from evals.squad_optimizer.cases import GW4_MARKET, GW5_MARKET, GW6_MARKET, VIEWS
from evals.squad_optimizer.views import load_view
from fpl.objective import (
    Market,
    Move,
    best_lineup,
    evaluate_plan,
    greedy_reference,
    legal_singles,
    objective,
    pool,
)


def view(view_id):
    try:
        return load_view(VIEWS[view_id])
    except SourceError as exc:
        pytest.skip(str(exc))


def names(scored, blend):
    return f"{blend[scored.move.out].name}→{blend[scored.move.into].name}"


def figures(scored):
    return round(scored.blend, 3), round(scored.prior, 3)


def squad_of(market: Market) -> list[int]:
    return list(market.sell)


@pytest.mark.parametrize(("view_id", "market", "pool_size", "singles", "baseline", "best"), [
    ("gw4", GW4_MARKET, 417, 1427, (338.508, 327.236), ("Anderson→Stach", (1.375, -2.853))),
    ("gw5-pre", GW5_MARKET, 406, 1392, (337.699, 323.421),
     ("Ndiaye→E.Le Fée", (4.105, 2.205))),
    ("gw5-post", GW5_MARKET, 402, 1376, (337.699, 323.421),
     ("Ndiaye→E.Le Fée", (4.105, 2.205))),
    ("gw6", GW6_MARKET, 402, 1355, (325.669, 316.594), ("Scott→E.Le Fée", (6.530, 3.788))),
])
def test_pool_singles_baseline_and_best_single(view_id, market, pool_size, singles, baseline,
                                               best):
    blend, prior, _ = view(view_id)
    squad = squad_of(market)
    assert len(pool(blend, prior)) == pool_size
    scored = legal_singles(squad, market, blend, prior)
    assert len(scored) == singles
    assert (round(objective(squad, blend), 3), round(objective(squad, prior), 3)) == baseline
    assert (names(scored[0], blend), figures(scored[0])) == best


def test_gw4_best_no_flip_single_and_greedy_banks():
    blend, prior, _ = view("gw4")
    scored = legal_singles(squad_of(GW4_MARKET), GW4_MARKET, blend, prior)
    no_flip = next(s for s in scored if s.prior >= 0)
    assert (names(no_flip, blend), figures(no_flip)) == ("Thiago→João Pedro", (1.267, 0.434))
    assert greedy_reference(squad_of(GW4_MARKET), GW4_MARKET, blend, prior) == ()


@pytest.mark.parametrize(("view_id", "legal_after"), [("gw5-pre", 1469), ("gw5-post", 1452)])
def test_gw5_after_the_first_move(view_id, legal_after):
    blend, prior, _ = view(view_id)
    squad = squad_of(GW5_MARKET)
    report = evaluate_plan(squad, [Move(237, 542)], GW5_MARKET, blend, prior)
    assert report.bank_after == 1
    sell = {pid: p for pid, p in GW5_MARKET.sell.items() if pid != 237} | {542: blend[542].price}
    after = Market(sell, report.bank_after, 2, "relayed")
    scored = legal_singles(list(report.squad_after), after, blend, prior)
    assert len(scored) == legal_after
    assert (names(scored[0], blend), figures(scored[0])) == ("Anderson→Schade", (1.853, -1.107))
    shaw = next(s for s in scored if names(s, blend) == "Shaw→Justin")
    assert figures(shaw) == (1.013, 0.443)
    reference = greedy_reference(squad, GW5_MARKET, blend, prior)
    assert [names(s, blend) for s in reference] == ["Ndiaye→E.Le Fée"]


def test_gw6_greedy_pair_marginals_and_after_plan():
    blend, prior, _ = view("gw6")
    squad = squad_of(GW6_MARKET)
    reference = greedy_reference(squad, GW6_MARKET, blend, prior)
    assert [(names(s, blend), figures(s)) for s in reference] == [
        ("Scott→E.Le Fée", (6.530, 3.788)), ("Ndiaye→Groß", (5.431, 0.665)),
        ("Anderson→Schade", (2.488, 0.757))]
    report = evaluate_plan(squad, [Move(69, 542), Move(237, 124), Move(481, 94)],
                           GW6_MARKET, blend, prior)
    assert (round(report.gain[0], 3), round(report.gain[1], 3)) == (14.449, 5.210)
    assert [figures(s) for s in report.marginals] == [(2.850, 2.963), (2.503, 0.665),
                                                      (2.488, 0.757)]
    assert report.verdict_reasons == ()
    assert (names(report.next_best, blend), figures(report.next_best)) == (
        "Thiago→João Pedro", (1.636, -1.808))


@pytest.mark.parametrize(("view_id", "market", "moves", "formation", "points", "captain_ep"), [
    ("gw4", GW4_MARKET, [], (3, 4, 3), 55.204, 5.998),
    ("gw5-pre", GW5_MARKET, [Move(237, 542)], (3, 4, 3), 57.397, 6.721),
    ("gw6", GW6_MARKET, [Move(69, 542), Move(237, 124), Move(481, 94)], (3, 5, 2), 56.178,
     5.786),
])
def test_gameweek_xi(view_id, market, moves, formation, points, captain_ep):
    blend, prior, _ = view(view_id)
    report = evaluate_plan(squad_of(market), moves, market, blend, prior)
    lineup = best_lineup(list(report.squad_after), blend, 0)
    assert lineup.formation == formation
    assert round(lineup.points, 3) == points
    assert blend[lineup.captain].name == "Haaland"
    assert round(blend[lineup.captain].ep(0), 3) == captain_ep
