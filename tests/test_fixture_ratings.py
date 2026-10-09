"""Unit tests for `fpl fixtures-rate` arithmetic: club xG attribution, implied
ratings, the prior blend, fixture rows and the generated tables — over a
small synthetic league."""

from __future__ import annotations

import json
import math

import pytest

from fpl.ep import inspect_fixtures, parse_fixtures
from fpl.fixture_ratings import (
    BASE_AWAY,
    BASE_HOME,
    CS_BAND_ROW_THRESHOLD,
    K_ATT,
    K_ATT_PROMOTED,
    K_DEFW,
    K_DEFW_PROMOTED,
    RatingInputs,
    blend,
    check_priors_clubs,
    decile,
    implied_attack,
    implied_defence,
    k_for,
    parse_priors,
    rate,
    render_json,
    render_tables,
    renormalise,
)
from fpl.models import Bootstrap, ElementSummary, EventLive, Fixture
from tests.factories import (
    bootstrap_payload,
    element_summary_payload,
    event_live_payload,
    fixture_payload,
    live_element,
    player_payload,
    priors_doc,
    summary_row,
    team_payload,
)

# short name → (team id, att, defw, promoted)
CLUBS = {
    "AAA": (1, 1.2, 0.8, False),
    "BBB": (2, 1.0, 1.0, False),
    "CCC": (3, 0.9, 1.1, False),
    "DDD": (4, 0.7, 1.3, True),
}
NAME = {team_id: name for name, (team_id, *_rest) in CLUBS.items()}
PRIORS = {name: (att, defw, promoted) for name, (_, att, defw, promoted) in CLUBS.items()}

# Rounds 1–2 played; a round robin fills GW3–8.
PLAYED = [(1, 1, 1, 2), (2, 1, 3, 4), (3, 2, 2, 3), (4, 2, 4, 1)]
PAIRINGS = [((1, 2), (3, 4)), ((2, 3), (4, 1)), ((1, 3), (2, 4))]


def fixtures_list(*, played=PLAYED, extra=()):
    fixtures = [fixture_payload(id=fid, event=event, team_h=h, team_a=a, finished=True)
                for fid, event, h, a in played]
    fid = 100
    for gw in range(3, 9):
        for h, a in PAIRINGS[gw % 3]:
            fixtures.append(fixture_payload(id=fid, event=gw, team_h=h, team_a=a,
                                            team_h_difficulty=2, team_a_difficulty=4))
            fid += 1
    fixtures += [fixture_payload(**f) for f in extra]
    return tuple(Fixture.model_validate(f) for f in fixtures)


def bootstrap(extra_players=()):
    teams = [team_payload(id=team_id, short_name=name) for name, (team_id, *_r) in CLUBS.items()]
    players = [player_payload(id=10 * team_id + 1, team=team_id) for team_id in NAME]
    players += [player_payload(**p) for p in extra_players]
    return Bootstrap.model_validate(bootstrap_payload(elements=players, teams=teams))


def side_rows(xg_by_fixture):
    """{fixture: (home xG, away xG)} → one summary per club's player-11 style id."""
    histories: dict[int, list[dict]] = {}
    for fid, event, h, a in PLAYED:
        if fid not in xg_by_fixture:
            continue
        xh, xa = xg_by_fixture[fid]
        histories.setdefault(10 * h + 1, []).append(
            summary_row(fixture=fid, round=event, was_home=True, expected_goals=str(xh)))
        histories.setdefault(10 * a + 1, []).append(
            summary_row(fixture=fid, round=event, was_home=False, expected_goals=str(xa)))
    return {pid: ElementSummary.model_validate(element_summary_payload(history=rows))
            for pid, rows in histories.items()}


NEUTRAL_XG = {1: (1.54 * 1.0, 1.33 * 0.8), 2: (1.54 * 1.3, 1.33 * 1.1),
              3: (1.54 * 1.1, 1.33 * 1.0), 4: (1.54 * 0.8, 1.33 * 1.3)}


def inputs(*, gw=3, summaries=None, live=None, priors=None, fixtures=None, boot=None,
           previous=None):
    return RatingInputs(
        gw=gw,
        bootstrap=boot or bootstrap(),
        fixtures=fixtures if fixtures is not None else fixtures_list(),
        summaries=summaries if summaries is not None else side_rows(NEUTRAL_XG),
        live=live if live is not None else {1: EventLive.model_validate(event_live_payload([])),
                                            2: EventLive.model_validate(event_live_payload([]))},
        priors=parse_priors(priors or priors_doc(PRIORS)),
        previous=previous,
    )


def match(run, fid):
    return next(m for m in run.matches if m.fixture == fid)


# --- priors ------------------------------------------------------------------


def test_priors_refuse_unknown_key():
    doc = priors_doc(PRIORS)
    doc["clubs"]["AAA"]["haircut"] = 0.1
    with pytest.raises(ValueError, match="AAA.haircut"):
        parse_priors(doc)


def test_priors_refuse_missing_club():
    doc = priors_doc({k: v for k, v in PRIORS.items() if k != "DDD"})
    with pytest.raises(ValueError, match=r"missing.*DDD"):
        check_priors_clubs(parse_priors(doc), set(PRIORS))


def test_priors_refuse_club_not_in_bootstrap():
    doc = priors_doc(PRIORS | {"ZZZ": (1.0, 1.0, False)})
    with pytest.raises(ValueError, match=r"not in the bootstrap.*ZZZ"):
        check_priors_clubs(parse_priors(doc), set(PRIORS))


def test_priors_refuse_rating_out_of_range():
    doc = priors_doc(PRIORS | {"BBB": (3.5, 1.0, False)})
    with pytest.raises(ValueError, match="BBB.att"):
        parse_priors(doc)


def test_priors_refuse_empty_source():
    doc = priors_doc(PRIORS)
    doc["clubs"]["CCC"]["source"] = "  "
    with pytest.raises(ValueError, match="CCC.source"):
        parse_priors(doc)


# --- club xG attribution -----------------------------------------------------


def test_summary_xg_attributed_by_row_fixture_not_current_team():
    # Player 11 now plays for AAA, but this row is BBB's home match v CCC.
    summaries = side_rows(NEUTRAL_XG)
    moved = summary_row(fixture=3, round=2, was_home=True, expected_goals="0.50")
    rows = list(summaries[11].history) + [ElementSummary.model_validate(
        element_summary_payload(history=[moved])).history[0]]
    summaries[11] = summaries[11].model_copy(update={"history": tuple(rows)})
    run = rate(inputs(summaries=summaries))
    assert match(run, 3).xg_home == round(1.54 * 1.1 + 0.5, 2)
    assert match(run, 4).xg_away == round(1.33 * 1.3, 2)


def test_event_live_recovers_player_without_summary_row():
    boot = bootstrap(extra_players=[{"id": 12, "team": 1}])
    live = {1: EventLive.model_validate(event_live_payload([live_element(12, "0.30", {1: 90})])),
            2: EventLive.model_validate(event_live_payload([]))}
    run = rate(inputs(boot=boot, live=live))
    assert match(run, 1).xg_home == round(1.54 + 0.30, 2)
    assert (run.recovered, run.recovered_xg) == (1, pytest.approx(0.30))


def test_event_live_skips_player_with_summary_row():
    live = {1: EventLive.model_validate(event_live_payload([live_element(11, "0.70", {1: 90})])),
            2: EventLive.model_validate(event_live_payload([]))}
    run = rate(inputs(live=live))
    assert match(run, 1).xg_home == round(1.54, 2)
    assert run.recovered == 0


def test_event_live_double_gameweek_splits_xg_by_minutes():
    played = PLAYED + [(5, 1, 1, 3)]
    boot = bootstrap(extra_players=[{"id": 12, "team": 1}])
    live = {1: EventLive.model_validate(
                event_live_payload([live_element(12, "0.80", {1: 90, 5: 30})])),
            2: EventLive.model_validate(event_live_payload([]))}
    run = rate(inputs(boot=boot, live=live, fixtures=fixtures_list(played=played)))
    assert match(run, 1).xg_home == round(1.54 + 0.60, 2)
    assert match(run, 5).xg_home == 0.20
    assert run.recovered == 2


def test_event_live_unresolved_player_warns():
    # Player 31 plays for CCC, which was not in fixture 1.
    summaries = side_rows({k: v for k, v in NEUTRAL_XG.items() if k != 2})
    live = {1: EventLive.model_validate(event_live_payload([live_element(31, "0.25", {1: 90})])),
            2: EventLive.model_validate(event_live_payload([]))}
    run = rate(inputs(summaries=summaries, live=live))
    assert run.unresolved == 1
    assert any("1 event-live player-round(s)" in w and "0.25 xG" in w for w in run.warnings)


def test_played_row_without_was_home_refuses_naming_the_player():
    summaries = side_rows(NEUTRAL_XG)
    row = summaries[21].history[0].model_copy(update={"was_home": None})
    summaries[21] = summaries[21].model_copy(update={"history": (row,)})
    with pytest.raises(ValueError, match="player 21"):
        rate(inputs(summaries=summaries))


def test_side_xg_rounded_to_two_decimals_before_rating():
    xg = dict(NEUTRAL_XG) | {1: (1.234, 1.0)}
    run = rate(inputs(summaries=side_rows(xg)))
    assert match(run, 1).xg_home == 1.23
    aaa_r1 = run.clubs["AAA"].matches[0]
    assert aaa_r1.att == pytest.approx(1.23 / (BASE_HOME * 1.0))


# --- implied ratings and the blend -------------------------------------------


def test_implied_attack_uses_prior_opponent_defw_and_own_venue_base():
    assert implied_attack(1.848, "H", opp_defw=0.8) == pytest.approx(1.5)
    assert implied_attack(1.33, "A", opp_defw=1.0) == pytest.approx(1.0)


def test_implied_defence_uses_opponent_venue_base_and_prior_opponent_att():
    # At home, the goals conceded are the away side's: base_away × opp ATT.
    assert implied_defence(0.798, "H", opp_att=1.2) == pytest.approx(0.5)
    assert implied_defence(1.54, "A", opp_att=1.0) == pytest.approx(1.0)


def test_implied_values_clip_and_are_counted():
    xg = dict(NEUTRAL_XG) | {1: (5.0, 0.0)}
    run = rate(inputs(summaries=side_rows(xg)))
    aaa = run.clubs["AAA"].matches[0]
    bbb = run.clubs["BBB"].matches[0]
    assert (aaa.att, aaa.att_clipped) == (1.80, True)
    assert (aaa.defw, aaa.defw_clipped) == (0.55, True)
    assert (bbb.att, bbb.att_clipped) == (0.55, True)
    assert run.clips == 4 and run.clips_by_round == {1: 4, 2: 0}
    assert run.clip_total == 16


def test_blend_k_by_side_and_promotion():
    assert blend(1.2, [1.5], k_for("att", promoted=False)) == pytest.approx((5.7 * 1.2 + 1.5) / 6.7)
    assert (k_for("att", promoted=False), k_for("defw", promoted=False)) == (K_ATT, K_DEFW)
    assert (k_for("att", promoted=True), k_for("defw", promoted=True)) == (
        K_ATT_PROMOTED, K_DEFW_PROMOTED)
    assert (K_ATT, K_DEFW, K_ATT_PROMOTED, K_DEFW_PROMOTED) == (5.7, 4.0, 4.0, 3.0)


def test_ratings_renormalised_to_mean_one_then_rounded():
    assert renormalise({"A": 3.0, "B": 1.0}) == {"A": 1.5, "B": 0.5}
    assert renormalise({"A": 1.234, "B": 0.766}) == {"A": 1.23, "B": 0.77}


def test_prior_weight_at_least_20pct_through_gw10():
    for k in (K_ATT, K_DEFW, K_ATT_PROMOTED, K_DEFW_PROMOTED):
        assert k / (k + 9) >= 0.20


def test_gw1_without_played_rounds_gives_renormalised_priors():
    run = rate(inputs(gw=1, summaries={}, live={}, fixtures=fixtures_list(played=[])))
    mean_att = sum(att for att, _, _ in PRIORS.values()) / 4
    assert run.clubs["AAA"].att == round(1.2 / mean_att, 2)
    assert run.matches == [] and run.league is None


def test_blend_uses_each_club_match_count():
    run = rate(inputs())
    expected = (K_ATT_PROMOTED * 0.7 + sum(m.att for m in run.clubs["DDD"].matches)) / (
        K_ATT_PROMOTED + 2)
    assert run.clubs["DDD"].n == 2
    assert run.clubs["DDD"].raw_att == pytest.approx(expected)


# --- fixture rows ------------------------------------------------------------


def test_lambda_from_two_decimal_ratings():
    run = rate(inputs())
    row = next(r for r in run.rows if r.club == "AAA" and r.venue == "H")
    opp = run.clubs[row.opp]
    assert row.lambda_att == round(BASE_HOME * run.clubs["AAA"].att * opp.defw, 2)
    away = next(r for r in run.rows if r.club == "AAA" and r.venue == "A")
    assert away.lambda_att == round(BASE_AWAY * run.clubs["AAA"].att * run.clubs[away.opp].defw, 2)


def test_lambda_def_is_opponent_lambda_att():
    run = rate(inputs())
    by_key = {(r.gw, r.club, r.opp): r for r in run.rows}
    for row in run.rows:
        assert row.lambda_def == by_key[(row.gw, row.opp, row.club)].lambda_att


def test_p_cs_is_exp_of_rounded_lambda_def():
    run = rate(inputs())
    for row in run.rows:
        assert row.p_cs == round(math.exp(-row.lambda_def), 2)
        assert abs(row.p_cs - math.exp(-row.lambda_def)) <= 0.005


def test_band_when_either_side_promoted():
    run = rate(inputs())
    for row in run.rows:
        assert row.band == ("DDD" in (row.club, row.opp))


def test_window_rows_double_two_rows_blank_none_stop_at_gw38_unscheduled_counted():
    extra = [{"id": 900, "event": 4, "team_h": 1, "team_a": 3},
             {"id": 901, "event": None, "team_h": 2, "team_a": 4},
             {"id": 902, "event": 9, "team_h": 1, "team_a": 2}]
    fixtures = [f for f in fixtures_list(extra=extra) if not (f.event == 5 and f.team_h == 2)]
    run = rate(inputs(fixtures=tuple(fixtures)))
    assert run.window == [3, 4, 5, 6, 7, 8]
    assert run.doubles == {4: ["AAA", "CCC"]}
    assert run.blanks == {5: ["BBB", "DDD"]}
    assert run.unscheduled == 1
    assert len([r for r in run.rows if r.club == "AAA" and r.gw == 4]) == 2
    assert all(r.gw <= 8 for r in run.rows)
    assert len(run.rows) == 6 * 4 + 2 - 2

    late = rate(inputs(gw=36, fixtures=fixtures_list(played=[]), summaries={},
                       live={r: EventLive.model_validate(event_live_payload([]))
                             for r in range(1, 36)}))
    assert late.window == [36, 37, 38]


def test_output_passes_parse_and_inspect_fixtures():
    run = rate(inputs())
    document = parse_fixtures(json.loads(render_json(run)))
    check = inspect_fixtures(bootstrap(), document, gw=3)
    assert check.rows_in_window == len(run.rows) and check.blanks == []


def test_same_inputs_same_bytes():
    first, second = rate(inputs()), rate(inputs())
    assert render_json(first) == render_json(second)
    assert render_tables(first) == render_tables(second)
    assert render_json(first).endswith("}\n")
    assert render_json(first).startswith('{\n "schema_version": 1,\n "gw": 3,')


def test_league_xg_line_against_base():
    run = rate(inputs())
    home = sum(round(h, 2) for h, _ in NEUTRAL_XG.values()) / 4
    away = sum(round(a, 2) for _, a in NEUTRAL_XG.values()) / 4
    assert run.league.home == pytest.approx(home)
    assert run.league.away == pytest.approx(away)
    assert run.league.matches == 4


# --- tables ------------------------------------------------------------------


def section(text, heading):
    start = text.index(f"## {heading}")
    end = text.find("\n## ", start + 1)
    return text[start:end if end != -1 else None]


def table_rows(block):
    return [[c.strip() for c in line.strip("|").split("|")]
            for line in block.splitlines()
            if line.startswith("|") and not line.startswith("|---") and "---" not in line]


def test_ticker_sums_and_cells():
    run = rate(inputs())
    rows = table_rows(section(render_tables(run), "Attack ticker"))[1:]
    aaa = next(r for r in rows if r[1] == "AAA")
    expected = sum(r.lambda_att for r in run.rows if r.club == "AAA")
    assert aaa[2] == f"{expected:.2f}"
    gw3 = next(r for r in run.rows if r.club == "AAA" and r.gw == 3)
    assert aaa[4] == f"{gw3.opp}({gw3.venue}) {gw3.lambda_att:.2f}" + (" ±" if gw3.band else "")
    assert [int(r[0]) for r in rows] == [1, 2, 3, 4]
    sums = [float(r[2]) for r in rows]
    assert sums == sorted(sums, reverse=True)


def test_ticker_double_joins_cells_and_blank_is_dash():
    extra = [{"id": 900, "event": 4, "team_h": 1, "team_a": 3}]
    fixtures = [f for f in fixtures_list(extra=extra) if not (f.event == 5 and f.team_h == 2)]
    text = render_tables(rate(inputs(fixtures=tuple(fixtures))))
    rows = {r[1]: r for r in table_rows(section(text, "Attack ticker"))[1:]}
    assert " + " in rows["AAA"][5]
    assert rows["BBB"][6] == "-"
    assert "gw4: AAA, CCC" in section(text, "Blanks, doubles, unscheduled")


def test_swings_second_half_minus_first():
    run = rate(inputs())
    rows = {r[0]: r for r in table_rows(section(render_tables(run), "Swings"))[1:]}
    mine = [r for r in run.rows if r.club == "CCC"]
    first = sum(r.lambda_att for r in mine if r.gw <= 5)
    second = sum(r.lambda_att for r in mine if r.gw >= 6)
    assert rows["CCC"][1] == f"{second - first:+.2f}"
    cs = sum(r.p_cs for r in mine if r.gw >= 6) - sum(r.p_cs for r in mine if r.gw <= 5)
    assert rows["CCC"][2] == f"{cs:+.2f}"


def test_decile_formula():
    values = [0.1 * i for i in range(1, 11)]
    assert decile(values, values[0]) == 1
    assert decile(values, values[5]) == 6
    assert decile(values, values[-1]) == 10
    assert decile([1.0, 1.0, 1.0], 1.0) == 1


def test_band_rows_threshold():
    run = rate(inputs())
    text = section(render_tables(run), "Promoted band")
    listed = table_rows(text)[1:]
    expected = [r for r in run.rows if r.band and r.p_cs >= CS_BAND_ROW_THRESHOLD]
    assert len(listed) == len(expected)
    assert all(float(r[3]) >= 0.30 for r in listed)
    assert f"banded rows: {sum(r.band for r in run.rows)}" in text


def test_delta_dash_without_previous():
    rows = table_rows(section(render_tables(rate(inputs())), "Ratings"))
    assert rows[0][6] == "Δ gw2"
    assert all(r[6] == "—" and r[10] == "—" for r in rows[1:])


def test_ratings_table_prints_rating_ranks():
    run = rate(inputs())
    rows = table_rows(section(render_tables(run), "Ratings"))
    header = rows[0]
    assert header[4:6] == ["ATT", "ATT rating rank"]
    assert header[8:10] == ["DEFW", "DEFW rating rank"]
    by_club = {r[0]: r for r in rows[1:]}
    for club, rating in run.clubs.items():
        stronger = sum(other.att > rating.att for other in run.clubs.values())
        meaner = sum(other.defw < rating.defw for other in run.clubs.values())
        assert by_club[club][5] == str(1 + stronger)
        assert by_club[club][9] == str(1 + meaner)


def test_delta_against_previous_ratings():
    previous = parse_fixtures({
        "schema_version": 1, "gw": 2, "base_lambda": {"home": 1.54, "away": 1.33},
        "ratings": {c: {"att": 1.0, "defw": 1.0} for c in CLUBS}, "fixtures": []})
    run = rate(inputs(previous=previous))
    rows = {r[0]: r for r in table_rows(section(render_tables(run), "Ratings"))[1:]}
    assert rows["AAA"][6] == f"{run.clubs['AAA'].att - 1.0:+.2f}"


def test_level_ratings_share_a_rank():
    level = PRIORS | {"CCC": (1.0, 1.0, False)}
    run = rate(inputs(gw=1, live={}, priors=priors_doc(level)))
    rows = {r[0]: r for r in table_rows(section(render_tables(run), "Ratings"))[1:]}
    assert run.clubs["BBB"].att == run.clubs["CCC"].att
    assert rows["BBB"][5] == rows["CCC"][5] == "2"
    assert rows["DDD"][5] == "4"


def test_ticker_rank_columns_match_fdr_vs_model():
    text = render_tables(rate(inputs()))
    attack = table_rows(section(text, "Attack ticker"))
    defence = table_rows(section(text, "Defence ticker"))
    assert attack[0][:2] == ["ATT rank", "Club"]
    assert defence[0][:2] == ["CS rank", "Club"]
    model = {r[0]: r for r in table_rows(section(text, "FDR vs model"))[1:]}
    assert all(model[r[1]][3] == r[0] for r in attack[1:])
    assert all(model[r[1]][4] == r[0] for r in defence[1:])


def test_fdr_vs_model_ranks():
    text = section(render_tables(rate(inputs())), "FDR vs model")
    rows = table_rows(text)
    assert rows[0][:5] == ["Club", "mean FDR", "FDR rank", "ATT rank", "CS rank"]
    assert sorted(int(r[2]) for r in rows[1:]) == [1, 2, 3, 4]


def test_detail_tables_per_window_gw_sorted_by_lambda():
    run = rate(inputs())
    text = render_tables(run)
    for gw in run.window:
        rows = table_rows(section(text, f"Detail GW{gw}"))[1:]
        lambdas = [float(r[4]) for r in rows]
        assert lambdas == sorted(lambdas, reverse=True)
        assert len(rows) == len([r for r in run.rows if r.gw == gw])
