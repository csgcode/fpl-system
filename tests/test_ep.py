"""EP model: the arithmetic behind players-{pos}.json. Pure logic over
validated inputs — no network, no clock. Hand-computed expectations follow
docs/ep-model.md."""

from __future__ import annotations

import math

import pytest

from fpl.calibrate import PlayerPrediction
from fpl.ep import (
    BLEND_EQUIV_MINUTES,
    BLEND_PRIOR_FLOOR,
    EffectiveRates,
    HORIZON,
    LEAGUE_FALLBACK,
    LEAGUE_POOL_MIN,
    POINTS,
    PRIOR_SHRINK_MINUTES,
    Rates,
    build_predictions,
    defcon_hit_probability,
    defcon_minutes_factor,
    expected_floor_div,
    inspect_fixtures,
    interpolate,
    p_sixty,
    parse_fixtures,
    parse_inputs,
    prior_weight,
    rates_from_seasons,
    shrink_rate,
)
from fpl.models import Bootstrap, ElementSummary, PastSeason, Position
from tests.factories import (
    bootstrap_payload,
    element_summary_payload,
    event_payload,
    match_record_payload,
    past_season_payload,
    player_payload,
    team_payload,
)

GW = 3
BASE = {"home": 1.54, "away": 1.33}
BASE_MEAN = (1.54 + 1.33) / 2


# ---------------------------------------------------------------- primitives


def test_expected_floor_div_matches_hand_computed_poisson():
    assert expected_floor_div(0.0, 2) == 0.0
    # Poisson(2): Σ floor(n/2)·P(n) = 0.7546 (docs/ep-model.md)
    assert expected_floor_div(2.0, 2) == pytest.approx(0.7546, abs=1e-3)
    assert expected_floor_div(2.0, 2) < 2.0 / 2
    assert expected_floor_div(3.0, 3) > expected_floor_div(1.0, 3)


def test_expected_floor_div_stays_exact_for_large_means():
    # E[floor(X/2)] = (λ − P(X odd)) / 2 = (λ − (1 − e^(−2λ)) / 2) / 2
    assert expected_floor_div(60.0, 2) == pytest.approx(29.75, abs=1e-6)
    mean = 45.0
    brute = sum(
        (n // 3) * math.exp(-mean + n * math.log(mean) - math.lgamma(n + 1))
        for n in range(0, 600)
    )
    assert expected_floor_div(mean, 3) == pytest.approx(brute, abs=1e-9)
    # far beyond exp(-mean) underflow: X mod k is uniform, so E → mean/k − (k−1)/(2k), never 0
    assert expected_floor_div(800.0, 3) == pytest.approx(800 / 3 - 1 / 3, abs=1e-6)


def test_interpolate_is_linear_between_anchors_and_clamped_outside():
    anchors = ((0.0, 0.0), (1.0, 1.0), (2.0, 1.5))
    assert interpolate(anchors, -1.0) == 0.0
    assert interpolate(anchors, 0.5) == pytest.approx(0.5)
    assert interpolate(anchors, 1.5) == pytest.approx(1.25)
    assert interpolate(anchors, 5.0) == 1.5


def test_minutes_curves_follow_documented_anchors():
    assert p_sixty(90) == 1.0
    assert p_sixty(60) == pytest.approx(0.5)
    assert p_sixty(30) == pytest.approx(0.25)
    assert defcon_minutes_factor(90) == 1.0
    assert defcon_minutes_factor(60) == pytest.approx(0.65)
    assert defcon_minutes_factor(45) == 0.0


def test_prior_weight_decays_with_current_minutes_to_a_floor():
    assert prior_weight(0) == 1.0
    assert prior_weight(BLEND_EQUIV_MINUTES) == pytest.approx(0.5)
    assert prior_weight(60_000) == BLEND_PRIOR_FLOOR


def test_shrink_rate_moves_from_league_mean_to_observed_with_minutes():
    assert shrink_rate(observed=1.0, minutes=0, league=0.2) == 0.2
    assert shrink_rate(observed=1.0, minutes=PRIOR_SHRINK_MINUTES, league=0.0) == pytest.approx(0.5)
    assert shrink_rate(observed=1.0, minutes=10**6, league=0.0) == pytest.approx(1.0, abs=1e-3)


def season(**overrides) -> PastSeason:
    return PastSeason.model_validate(past_season_payload(**overrides))


def test_rates_from_seasons_pools_until_900_minutes_latest_first():
    latest = season(season_name="2025/26", minutes=300, starts=4, expected_goals="3.0", bonus=2)
    older = season(season_name="2024/25", minutes=900, starts=10, expected_goals="3.0", bonus=5)
    oldest = season(season_name="2023/24", minutes=2000, starts=22, expected_goals="20.0")
    rates, minutes = rates_from_seasons((oldest, latest, older), LEAGUE_FALLBACK[Position.MID])
    assert minutes == 1200
    assert rates.xg90 == pytest.approx(6.0 / 1200 * 90)
    assert rates.bonus_per_start == pytest.approx(7 / 14)
    assert rates.minutes_per_start == pytest.approx(1200 / 14)


def test_rates_from_seasons_uses_latest_alone_when_it_is_a_full_season():
    latest = season(season_name="2025/26", minutes=2700, expected_goals="9.0")
    older = season(season_name="2024/25", minutes=2700, expected_goals="0.0")
    rates, minutes = rates_from_seasons((older, latest), LEAGUE_FALLBACK[Position.MID])
    assert minutes == 2700
    assert rates.xg90 == pytest.approx(0.3)


def test_rates_from_seasons_without_starts_take_minutes_per_start_from_the_league():
    league = Rates(xg90=0, xa90=0, dc90=0, saves90=0, bonus_per_start=0, yellow90=0, minutes_per_start=77)
    sub_only = season(season_name="2025/26", minutes=900, starts=0, bonus=3)
    rates, minutes = rates_from_seasons((sub_only,), league)
    assert minutes == 900
    assert rates.minutes_per_start == 77
    assert rates.bonus_per_start == pytest.approx(3 / 10)
    legacy = season(season_name="2025/26", minutes=900, starts=None, bonus=3)
    assert rates_from_seasons((legacy,), league)[0].minutes_per_start == 77


def test_rates_from_seasons_without_rows_is_empty():
    rates, minutes = rates_from_seasons((), LEAGUE_FALLBACK[Position.MID])
    assert minutes == 0
    assert rates is None


def test_defcon_probability_interpolates_anchors_and_blends_observed_hits():
    assert defcon_hit_probability(12.0, 12, hits=0, matches=0, w_prior=1.0) == pytest.approx(0.55)
    assert defcon_hit_probability(12.0, 10, hits=0, matches=0, w_prior=1.0) == pytest.approx(0.775)
    assert defcon_hit_probability(0.0, 12, hits=0, matches=0, w_prior=1.0) == 0.0
    assert defcon_hit_probability(12.0, 12, hits=1, matches=1, w_prior=0.8) == pytest.approx(
        0.8 * 0.55 + 0.2 * 1.0
    )


def test_points_table_encodes_position_differences():
    assert POINTS[Position.DEF].goal == 6
    assert POINTS[Position.FWD].goal == 4
    assert POINTS[Position.MID].clean_sheet == 1
    assert POINTS[Position.FWD].clean_sheet == 0
    assert POINTS[Position.GKP].defcon_threshold is None
    assert POINTS[Position.DEF].defcon_threshold == 10
    assert POINTS[Position.MID].defcon_threshold == 12
    assert POINTS[Position.GKP].saves_per_three == 1
    assert POINTS[Position.DEF].goals_conceded_per_two == -1
    assert POINTS[Position.MID].goals_conceded_per_two == 0


# ------------------------------------------------------------------ world


def make_bootstrap(players: list[dict]) -> Bootstrap:
    return Bootstrap.model_validate(
        bootstrap_payload(
            elements=players,
            teams=[
                team_payload(id=1, short_name="TST"),
                team_payload(id=2, short_name="OPP"),
            ],
            events=[event_payload(id=GW, is_next=True)],
        )
    )


def player(**overrides) -> dict:
    base = {"id": 1, "web_name": "Alpha", "team": 1, "element_type": 3, "now_cost": 60}
    base.update(overrides)
    return player_payload(**base)


def summary(*, history_past=None, history=None) -> ElementSummary:
    return ElementSummary.model_validate(
        element_summary_payload(history_past=history_past, history=history)
    )


def fixtures_doc(rows=None, ratings=None):
    if rows is None:
        rows = [
            fixture("TST", g, "OPP", "H" if g % 2 else "A", lambda_att=BASE_MEAN * 1.0)
            for g in range(GW, GW + HORIZON)
        ]
    return parse_fixtures(
        {
            "schema_version": 1,
            "gw": GW,
            "base_lambda": BASE,
            "ratings": ratings or {"TST": {"att": 1.0, "defw": 1.0}, "OPP": {"att": 1.0, "defw": 1.0}},
            "fixtures": rows,
        }
    )


def fixture(club, gw, opp, venue, *, lambda_att=1.5, lambda_def=1.0, p_cs=0.3, **extra):
    return {
        "club": club, "gw": gw, "opp": opp, "venue": venue,
        "lambda_att": lambda_att, "lambda_def": lambda_def, "p_cs": p_cs, **extra,
    }


def inputs_doc(position: str, players: list[dict]):
    return parse_inputs(
        {"schema_version": 1, "gw": GW, "position": position, "players": players}
    )


FULL_OVERRIDES = {
    "xg90": 0.5, "xa90": 0.2, "dc90": 12.0, "saves90": 3.0,
    "bonus_per_start": 0.5, "yellow90": 0.1, "minutes_per_start": 90, "prior_weight": 1.0,
}


def judged(id=1, name="Alpha", p_start=1.0, **extra) -> dict:
    row = {"id": id, "name": name, "p_start": p_start, "uncertainty": "LOW", "notes": "n"}
    row.update(extra)
    return row


def run_single(position_code: int, position_name: str, *, overrides=FULL_OVERRIDES, fixtures=None):
    bootstrap = make_bootstrap([player(element_type=position_code)])
    result = build_predictions(
        bootstrap,
        {1: summary()},
        fixtures or fixtures_doc(),
        inputs_doc(position_name, [judged(overrides=overrides, reason="test")]),
        gw=GW,
    )
    return result, result.rows[0]


# ------------------------------------------------------------ formula


def test_mid_terms_match_hand_computation():
    _, row = run_single(3, "MID")
    # appearance 2 + attack (0.5×5 + 0.2×3) + cs 0.3×1 + defcon 2×0.55 + bonus 0.5 − cards 0.1
    assert row.ep_gw == [pytest.approx(6.9, abs=1e-6)] * HORIZON
    assert row.ep_total6 == pytest.approx(6.9 * HORIZON, abs=1e-3)
    assert row.ep_per_million == pytest.approx(6.9 * HORIZON / 6.0, abs=1e-3)
    assert row.terms.attack == pytest.approx(3.1 * HORIZON, abs=1e-3)
    assert row.terms.defcon == pytest.approx(1.1 * HORIZON, abs=1e-3)
    assert row.terms.goals_conceded == 0.0
    assert row.terms.saves == 0.0


def test_def_terms_use_defence_points_and_poisson_goals_conceded():
    _, row = run_single(2, "DEF")
    # 2 + (0.5×6 + 0.2×3) + 0.3×4 − E[floor(GC/2)|λ=1] + 2×0.775 + 0.5×0.9 − 0.1
    gc = expected_floor_div(1.0, 2)
    assert gc == pytest.approx(0.2838, abs=1e-3)
    assert row.ep_gw[0] == pytest.approx(2 + 3.6 + 1.2 - gc + 1.55 + 0.45 - 0.1, abs=1e-6)


def test_gkp_terms_have_saves_and_no_defcon():
    _, row = run_single(1, "GKP")
    saves_mean = 3.0 * (1.0 / BASE_MEAN)
    saves = expected_floor_div(saves_mean, 3) + POINTS[Position.GKP].pen_save_tail
    gc = expected_floor_div(1.0, 2)
    expected = 2 + (0.5 * 6 + 0.2 * 3) + 0.3 * 4 - gc + saves + 0.5 * 1.10 - 0.1
    assert row.ep_gw[0] == pytest.approx(expected, abs=1e-6)
    assert row.terms.defcon == 0.0


def test_fwd_has_no_clean_sheet_term():
    _, row = run_single(4, "FWD")
    assert row.terms.clean_sheet == 0.0
    assert row.terms.goals_conceded == 0.0


def test_attack_multiplier_divides_out_the_clubs_own_attack_index():
    ratings = {"TST": {"att": 1.25, "defw": 1.0}, "OPP": {"att": 1.0, "defw": 1.0}}
    rows = [fixture("TST", g, "OPP", "H", lambda_att=BASE_MEAN * 1.25 * 0.8) for g in range(GW, GW + HORIZON)]
    _, row = run_single(3, "MID", fixtures=fixtures_doc(rows, ratings))
    assert row.terms.attack == pytest.approx(3.1 * 0.8 * HORIZON, abs=1e-3)
    assert row.rates.attack_mult == 1.0


def test_attack_mult_override_scales_attack_only():
    overrides = {**FULL_OVERRIDES, "attack_mult": 0.5}
    _, row = run_single(3, "MID", overrides=overrides)
    assert row.terms.attack == pytest.approx(3.1 * 0.5 * HORIZON, abs=1e-3)
    assert row.terms.defcon == pytest.approx(1.1 * HORIZON, abs=1e-3)
    assert row.rates.attack_mult == 0.5


def test_p_start_gw_scales_each_gameweek_and_scalar_is_this_gameweeks():
    bootstrap = make_bootstrap([player()])
    doc = inputs_doc("MID", [judged(p_start=0.5, p_start_gw=[1, 0, 0, 0, 0, 0.5], overrides=FULL_OVERRIDES, reason="t")])
    result = build_predictions(bootstrap, {1: summary()}, fixtures_doc(), doc, gw=GW)
    row = result.rows[0]
    assert row.ep_gw[0] == pytest.approx(6.9, abs=1e-6)
    assert row.ep_gw[1:5] == [0.0] * 4
    assert row.ep_gw[5] == pytest.approx(3.45, abs=1e-6)
    assert row.p_start_gw == [1, 0, 0, 0, 0, 0.5]
    assert row.p_start == 1.0


def test_season_tail_window_shortens_every_per_gameweek_list_together():
    gw = 36
    bootstrap = make_bootstrap([player()])
    inputs = parse_inputs({
        "schema_version": 1, "gw": gw, "position": "MID",
        "players": [judged(p_start=0.5, p_start_gw=[0.9, 0.8, 0.7, 0.6, 0.5, 0.4], overrides=FULL_OVERRIDES, reason="t")],
    })
    fixtures = parse_fixtures({
        "schema_version": 1, "gw": gw, "base_lambda": BASE,
        "ratings": {"TST": {"att": 1.0, "defw": 1.0}, "OPP": {"att": 1.0, "defw": 1.0}},
        "fixtures": [fixture("TST", g, "OPP", "H", lambda_att=BASE_MEAN) for g in (36, 37, 38)],
    })
    row = build_predictions(bootstrap, {1: summary()}, fixtures, inputs, gw=gw).rows[0]
    assert len(row.ep_gw) == len(row.p_start_gw) == len(row.fixtures) == 3
    assert row.p_start_gw == [0.9, 0.8, 0.7]
    assert row.p_start == 0.9
    assert row.ep_total6 == pytest.approx(sum(row.ep_gw))


def test_double_gameweek_sums_two_fixtures_and_blank_scores_zero():
    rows = [fixture("TST", GW, "OPP", "H", lambda_att=BASE_MEAN), fixture("TST", GW, "OPP", "A", lambda_att=BASE_MEAN)]
    rows += [fixture("TST", g, "OPP", "H", lambda_att=BASE_MEAN) for g in range(GW + 2, GW + HORIZON)]
    result, row = run_single(3, "MID", fixtures=fixtures_doc(rows))
    assert row.ep_gw[0] == pytest.approx(13.8, abs=1e-6)
    assert row.ep_gw[1] == 0.0
    assert row.fixtures[0] == "OPP(H)+OPP(A)"
    assert row.fixtures[1] == "-"
    assert any("blank" in w and "TST" in w and str(GW + 1) in w for w in result.warnings)


# ------------------------------------------------------------- rates


def test_prior_comes_from_history_past_shrunk_toward_league_mean():
    bootstrap = make_bootstrap([player()])
    hist = [past_season_payload(season_name="2025/26", minutes=PRIOR_SHRINK_MINUTES, starts=5, expected_goals="5.0", expected_assists="0.0", defensive_contribution=0.0, bonus=0, saves=0, yellow_cards=0)]
    result = build_predictions(
        bootstrap, {1: summary(history_past=hist)}, fixtures_doc(),
        inputs_doc("MID", [judged()]), gw=GW,
    )
    row = result.rows[0]
    observed_xg90 = 5.0 / PRIOR_SHRINK_MINUTES * 90
    league = LEAGUE_FALLBACK[Position.MID].xg90
    assert row.rates.xg90 == pytest.approx((observed_xg90 + league) / 2, abs=1e-3)
    assert row.rates.prior_source == "history_past"
    assert row.rates.prior_weight == 1.0
    assert any("fallback" in w for w in result.warnings)


def test_current_season_rows_blend_in_by_minutes():
    bootstrap = make_bootstrap([player()])
    hist_past = [past_season_payload(season_name="2025/26", minutes=9000, starts=100, expected_goals="0.0", expected_assists="0.0", defensive_contribution=0.0, bonus=0, yellow_cards=0)]
    history = [match_record_payload(round=1, minutes=90, expected_goals="0.9", expected_assists="0.0", defensive_contribution=0.0, bonus=0, yellow_cards=0)]
    result = build_predictions(
        bootstrap, {1: summary(history_past=hist_past, history=history)}, fixtures_doc(),
        inputs_doc("MID", [judged()]), gw=GW,
    )
    row = result.rows[0]
    w = prior_weight(90)
    prior_xg90 = shrink_rate(0.0, 9000, LEAGUE_FALLBACK[Position.MID].xg90)
    assert row.rates.prior_weight == pytest.approx(w)
    assert row.rates.xg90 == pytest.approx(w * prior_xg90 + (1 - w) * 0.9, abs=1e-3)


def test_missing_summary_falls_back_to_league_mean_and_is_listed():
    bootstrap = make_bootstrap([player()])
    result = build_predictions(bootstrap, {}, fixtures_doc(), inputs_doc("MID", [judged()]), gw=GW)
    row = result.rows[0]
    assert row.rates.prior_source == "league_mean"
    assert row.rates.xg90 == LEAGUE_FALLBACK[Position.MID].xg90
    assert result.missing_summaries == [1]


def test_league_mean_is_pooled_from_cached_summaries_when_the_pool_is_large_enough():
    pool_ids = list(range(10, 10 + LEAGUE_POOL_MIN))
    players = [player()] + [player(id=i, web_name=f"Pool{i}", now_cost=45) for i in pool_ids]
    bootstrap = make_bootstrap(players)
    summaries = {
        i: summary(history_past=[past_season_payload(season_name="2025/26", minutes=1800, expected_goals="6.0")])
        for i in pool_ids
    }
    result = build_predictions(bootstrap, summaries, fixtures_doc(), inputs_doc("MID", [judged()]), gw=GW)
    assert result.rows[0].rates.xg90 == pytest.approx(0.3)
    assert result.rows[0].rates.prior_source == "league_mean"
    assert not any("fallback" in w for w in result.warnings)
    assert result.not_scored == LEAGUE_POOL_MIN


# --------------------------------------------------------------- contracts


def test_inputs_refuse_unknown_keys_with_the_offending_row():
    with pytest.raises(ValueError, match="id 1.*foo"):
        inputs_doc("MID", [judged(foo=1)])


def test_inputs_refuse_overrides_without_a_reason():
    with pytest.raises(ValueError, match="reason"):
        inputs_doc("MID", [judged(overrides={"xg90": 0.5})])


def test_inputs_refuse_wrong_length_p_start_gw_and_duplicate_ids():
    with pytest.raises(ValueError, match="p_start_gw"):
        inputs_doc("MID", [judged(p_start_gw=[1.0, 1.0])])
    with pytest.raises(ValueError, match="duplicate"):
        inputs_doc("MID", [judged(), judged()])


def test_inputs_accept_gk_alias_and_normalise_position():
    doc = inputs_doc("GK", [judged()])
    assert doc.position is Position.GKP


def test_build_refuses_name_mismatch_wrong_position_and_unknown_id():
    bootstrap = make_bootstrap([player(), player(id=2, web_name="Keeper", element_type=1)])
    with pytest.raises(ValueError, match="Alpha.*Beta|Beta.*Alpha"):
        build_predictions(bootstrap, {}, fixtures_doc(), inputs_doc("MID", [judged(name="Beta")]), gw=GW)
    with pytest.raises(ValueError, match="GKP"):
        build_predictions(bootstrap, {}, fixtures_doc(), inputs_doc("MID", [judged(), judged(id=2, name="Keeper")]), gw=GW)
    with pytest.raises(ValueError, match="99"):
        build_predictions(bootstrap, {}, fixtures_doc(), inputs_doc("MID", [judged(), judged(id=99, name=None)]), gw=GW)


def test_build_refuses_document_gameweek_or_position_mismatch():
    bootstrap = make_bootstrap([player()])
    with pytest.raises(ValueError, match="gw"):
        build_predictions(bootstrap, {}, fixtures_doc(), inputs_doc("MID", [judged()]), gw=GW + 1)
    with pytest.raises(ValueError, match="position MID, not FWD"):
        build_predictions(bootstrap, {}, fixtures_doc(), inputs_doc("FWD", [judged()]), gw=GW)


def test_coverage_refuses_when_an_available_player_above_4_5m_is_missing():
    bootstrap = make_bootstrap([player(), player(id=2, web_name="Costly", now_cost=75, status="a")])
    with pytest.raises(ValueError, match="Costly.*7.5"):
        build_predictions(bootstrap, {}, fixtures_doc(), inputs_doc("MID", [judged()]), gw=GW)


def test_coverage_excludes_and_counts_cheap_or_unavailable_absentees():
    bootstrap = make_bootstrap([
        player(),
        player(id=2, web_name="Cheap", now_cost=45),
        player(id=3, web_name="Injured", now_cost=90, status="i"),
    ])
    result = build_predictions(bootstrap, {}, fixtures_doc(), inputs_doc("MID", [judged()]), gw=GW)
    assert [r.id for r in result.rows] == [1]
    assert result.not_scored == 2


def test_fixtures_refuse_unknown_club_bad_probability_and_unknown_key():
    with pytest.raises(ValueError, match="p_cs"):
        fixtures_doc([fixture("TST", GW, "OPP", "H", p_cs=1.5)])
    with pytest.raises(ValueError, match="lamda_att"):
        fixtures_doc([{**fixture("TST", GW, "OPP", "H"), "lamda_att": 1.0}])
    bootstrap = make_bootstrap([player()])
    doc = fixtures_doc([fixture("XYZ", GW, "OPP", "H")], ratings={"TST": {"att": 1, "defw": 1}, "OPP": {"att": 1, "defw": 1}, "XYZ": {"att": 1, "defw": 1}})
    with pytest.raises(ValueError, match="XYZ"):
        build_predictions(bootstrap, {}, doc, inputs_doc("MID", [judged()]), gw=GW)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("xg90", 2.5), ("xa90", 2.5), ("dc90", 31), ("saves90", 11), ("bonus_per_start", 3.5),
        ("yellow90", 1.5), ("minutes_per_start", 0), ("minutes_per_start", 120),
        ("attack_mult", 0.1), ("attack_mult", 5), ("prior_weight", 1.5), ("xg", 0.5),
    ],
)
def test_overrides_refuse_implausible_or_unknown_values_with_the_row(field, value):
    with pytest.raises(ValueError, match=rf"row 0 \(id 1\): overrides\.{field}"):
        inputs_doc("MID", [judged(overrides={field: value}, reason="unit slip")])


def test_inputs_refuse_bad_schema_version_probability_and_uncertainty():
    with pytest.raises(ValueError, match="schema_version"):
        parse_inputs({"schema_version": 2, "gw": GW, "position": "MID", "players": [judged()]})
    with pytest.raises(ValueError, match=r"row 0 \(id 1\): p_start"):
        inputs_doc("MID", [judged(p_start=1.5)])
    with pytest.raises(ValueError, match=r"row 0 \(id 1\): uncertainty"):
        inputs_doc("MID", [judged(uncertainty="WILD")])


@pytest.mark.parametrize(
    ("patch", "match"),
    [
        ({"fixtures": [{"club": "TST", "gw": GW, "opp": "OPP", "venue": "H", "lambda_att": 7, "lambda_def": 1, "p_cs": 0.3}]}, r"row 0 \(id TST\): lambda_att"),
        ({"fixtures": [{"club": "TST", "gw": GW, "opp": "OPP", "venue": "H", "lambda_att": 1, "lambda_def": 45, "p_cs": 0.3}]}, r"row 0 \(id TST\): lambda_def"),
        ({"base_lambda": {"home": 100, "away": 1.3}}, "base_lambda.home"),
        ({"base_lambda": {"home": 1.5, "away": 0.01}}, "base_lambda.away"),
        ({"ratings": {"TST": {"att": 500, "defw": 1.0}, "OPP": {"att": 1.0, "defw": 1.0}}}, "ratings.TST.att"),
        ({"ratings": {"TST": {"att": 1.0, "defw": 0.1}, "OPP": {"att": 1.0, "defw": 1.0}}}, "ratings.TST.defw"),
    ],
)
def test_fixtures_refuse_implausible_magnitudes_with_the_field(patch, match):
    raw = {
        "schema_version": 1, "gw": GW, "base_lambda": BASE,
        "ratings": {"TST": {"att": 1.0, "defw": 1.0}, "OPP": {"att": 1.0, "defw": 1.0}},
        "fixtures": [fixture("TST", GW, "OPP", "H")],
    }
    with pytest.raises(ValueError, match=match):
        parse_fixtures({**raw, **patch})


def test_fixtures_refuse_a_club_playing_itself_and_a_third_fixture_in_one_gameweek():
    bootstrap = make_bootstrap([player()])
    with pytest.raises(ValueError, match="TST.*opp is the club itself"):
        inspect_fixtures(bootstrap, fixtures_doc([fixture("TST", GW, "TST", "H")]), gw=GW)
    triple = fixtures_doc([fixture("TST", GW, "OPP", v) for v in ("H", "A", "H")])
    with pytest.raises(ValueError, match="TST 3 fixtures in gw"):
        inspect_fixtures(bootstrap, triple, gw=GW)
    with pytest.raises(ValueError, match="TST 3 fixtures in gw"):
        build_predictions(bootstrap, {}, triple, inputs_doc("MID", [judged()]), gw=GW)
    repeated = fixtures_doc([fixture("TST", GW, "OPP", "H"), fixture("TST", GW, "OPP", "H")])
    with pytest.raises(ValueError, match=r"repeats TST OPP\(H\) in gw"):
        inspect_fixtures(bootstrap, repeated, gw=GW)


def test_fixtures_for_another_gameweek_are_refused_before_scoring():
    bootstrap = make_bootstrap([player()])
    with pytest.raises(ValueError, match=f"fixtures.json is for gw{GW}, not gw{GW + 1}"):
        inspect_fixtures(bootstrap, fixtures_doc(), gw=GW + 1)


def test_fixtures_must_rate_every_club_in_the_bootstrap():
    bootstrap = make_bootstrap([player()])
    doc = fixtures_doc(ratings={"TST": {"att": 1, "defw": 1}})
    with pytest.raises(ValueError, match="OPP"):
        build_predictions(bootstrap, {}, doc, inputs_doc("MID", [judged()]), gw=GW)


# ------------------------------------------------------------------ output


def test_rows_sort_by_ep_and_parse_as_calibrate_predictions():
    bootstrap = make_bootstrap([player(), player(id=2, web_name="Beta", now_cost=50)])
    doc = inputs_doc("MID", [judged(p_start=0.2), judged(id=2, name="Beta", p_start=0.9)])
    result = build_predictions(bootstrap, {}, fixtures_doc(), doc, gw=GW)
    assert [r.id for r in result.rows] == [2, 1]
    for row in result.rows:
        parsed = PlayerPrediction.model_validate({**row.model_dump(), "position": Position.MID})
        assert parsed.predicted == row.ep_gw[0]
        assert parsed.team == "TST"
    assert result.rows[0].price == 5.0
    assert math.isclose(result.rows[0].ep_per_million, result.rows[0].ep_total6 / 5.0, abs_tol=1e-3)
    assert isinstance(result.rows[0].rates, EffectiveRates)
    assert result.rows[0].rates.prior_source == "league_mean"
    assert result.rows[0].terms.total() == pytest.approx(result.rows[0].ep_total6)
