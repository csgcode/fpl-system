"""EP model: the arithmetic behind players-{pos}.json. Pure logic over
validated inputs — no network, no clock. Hand-computed expectations follow
docs/ep-model.md."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from fpl.calibrate import PlayerPrediction
from fpl.consistency import FixtureMeans, p_at_least
from fpl import ep
from fpl.ep import (
    BLEND_EQUIV_MINUTES,
    BONUS_SHRINK_STARTS,
    BaseLambda,
    DEFCON_FIRST_SEASON,
    BLEND_PRIOR_FLOOR,
    DEFAULT_CONFIG,
    EffectiveRates,
    HORIZON,
    LEAGUE_FALLBACK,
    LEAGUE_POOL_MIN,
    POINTS,
    ModelConfig,
    PRIOR_SHRINK_MINUTES,
    Rates,
    attack_factor,
    bonus_rate,
    build_predictions,
    current_totals,
    defcon_hit_probability,
    defcon_minutes_factor,
    expected_floor_div,
    finishing_multiplier,
    force_prior_weight,
    inspect_fixtures,
    interpolate,
    league_bonus_per_start,
    match_weights,
    names_match,
    p_sixty,
    parse_fixtures,
    parse_inputs,
    played_matches,
    prior_weight,
    rates_from_seasons,
    saves_factor,
    shrink_rate,
    XG_FIRST_SEASON,
)
from fpl.models import Bootstrap, ElementSummary, MatchRecord, PastSeason, Player, Position
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


def test_prior_weight_floor_from_config():
    assert prior_weight(10_000, k=600, floor=0.1) == 0.1


def test_default_config_reproduces_the_production_constants():
    assert DEFAULT_CONFIG.blend_k == BLEND_EQUIV_MINUTES
    assert DEFAULT_CONFIG.blend_floor == BLEND_PRIOR_FLOOR


def test_config_digest_is_stable_and_changes_with_a_field():
    digest = DEFAULT_CONFIG.digest()
    assert digest == ModelConfig().digest()
    assert len(digest) == 8 and all(c in "0123456789abcdef" for c in digest)
    assert replace(DEFAULT_CONFIG, blend_k=300.0).digest() != digest


def test_config_from_int_has_the_same_digest_as_the_equal_float_config():
    config = ModelConfig(blend_k=600)
    assert isinstance(config.blend_k, float)
    assert config == DEFAULT_CONFIG
    assert config.digest() == DEFAULT_CONFIG.digest() == "64ad9c9c"


def test_match_weights_halve_every_half_life():
    assert match_weights(4, half_life=2.0) == [0.5**1.5, 0.5**1.0, 0.5**0.5, 1.0]
    assert match_weights(3, None) == [1.0, 1.0, 1.0]
    assert match_weights(0, 2.0) == []


def test_opponent_factors_match_hand_values():
    base = BaseLambda(**BASE)
    assert attack_factor(True, 1.25, base) == pytest.approx(BASE_MEAN / (1.54 * 1.25))
    assert attack_factor(False, 0.8, base) == pytest.approx(BASE_MEAN / (1.33 * 0.8))
    # The opponent of a home side plays away.
    assert saves_factor(True, 1.2, base) == pytest.approx(BASE_MEAN / (1.33 * 1.2))
    assert saves_factor(False, 1.2, base) == pytest.approx(BASE_MEAN / (1.54 * 1.2))
    assert attack_factor(True, None, base) == 1.0
    assert saves_factor(False, None, base) == 1.0
    assert attack_factor(True, 1.25, None) == 1.0
    assert saves_factor(True, 1.2, None) == 1.0


def test_played_matches_drop_unplayed_rows_and_order_oldest_first():
    rows = [
        MatchRecord.model_validate(match_record_payload(**fields))
        for fields in (
            {"fixture": 30, "round": 3},
            {"fixture": 11, "round": 1, "minutes": 0},
            {"fixture": 21, "round": 2},
            {"fixture": 20, "round": 2},
            {"fixture": 5, "round": None},
        )
    ]
    assert [(row.round, row.fixture) for row in played_matches(rows)] == [
        (None, 5), (2, 20), (2, 21), (3, 30),
    ]


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


# ------------------------------------------------------- consistency (p4)

GOAL_ONLY = {"xg90": 0.5, "xa90": 0.0, "dc90": 0.0, "minutes_per_start": 90, "prior_weight": 1.0}


def test_p4_matches_the_hand_value_for_a_goal_only_forward():
    rows = [fixture("TST", GW, "OPP", "H", lambda_att=BASE_MEAN)]
    rows += [fixture("TST", g, "OPP", "H", lambda_att=BASE_MEAN) for g in range(GW + 2, GW + HORIZON)]
    _, row = run_single(4, "FWD", overrides=GOAL_ONLY, fixtures=fixtures_doc(rows))
    # 90 minutes is 2 points; one goal (4) takes it to 6, so P(≥4) = P(goals ≥ 1).
    assert row.p4_gw[0] == pytest.approx(1 - math.exp(-0.5))
    assert row.p4_gw[1] == 0.0
    assert len(row.p4_gw) == len(row.ep_gw)


def test_p4_feeds_the_same_fixture_means_as_the_ep_terms():
    bootstrap = make_bootstrap([player(element_type=1)])
    doc = inputs_doc("GKP", [judged(p_start=0.5, overrides=FULL_OVERRIDES, reason="t")])
    row = build_predictions(bootstrap, {1: summary()}, fixtures_doc(), doc, gw=GW).rows[0]
    means = FixtureMeans(
        goal_pts=6, goal_mean=0.5, assist_mean=0.2, p60=1.0, p_cs=0.3, cs_pts=4,
        saves_mean=3.0 / BASE_MEAN,
    )
    assert row.p4_gw[0] == pytest.approx(p_at_least([means], 0.5, 4))


def test_p4_reads_assist_points_from_the_points_table(monkeypatch):
    monkeypatch.setitem(ep.POINTS, Position.FWD,
                        ep.POINTS[Position.FWD].model_copy(update={"assist": 1}))
    rows = [fixture("TST", g, "OPP", "H", lambda_att=BASE_MEAN) for g in range(GW, GW + HORIZON)]
    assists_only = {**GOAL_ONLY, "xg90": 0.0, "xa90": 0.5}
    _, row = run_single(4, "FWD", overrides=assists_only, fixtures=fixtures_doc(rows))
    # 90 minutes is 2 points and an assist 1, so P(≥4) = P(assists ≥ 2).
    assert row.p4_gw[0] == pytest.approx(1 - math.exp(-0.5) * 1.5)


def test_p4_never_exceeds_the_start_probability():
    bootstrap = make_bootstrap([player(element_type=4)])
    starts = [0.9, 0.8, 0.0, 0.6, 0.5, 0.4]
    doc = inputs_doc("FWD", [judged(p_start=0.9, p_start_gw=starts,
                                    overrides={**GOAL_ONLY, "xg90": 2.0}, reason="t")])
    row = build_predictions(bootstrap, {1: summary()}, fixtures_doc(), doc, gw=GW).rows[0]
    assert row.p_start_gw == starts
    for p4, p_start in zip(row.p4_gw, row.p_start_gw, strict=True):
        assert p4 <= p_start


def test_p4_convolves_a_double_gameweek():
    rows = [fixture("TST", GW, "OPP", "H", lambda_att=BASE_MEAN), fixture("TST", GW, "OPP", "A", lambda_att=BASE_MEAN)]
    rows += [fixture("TST", g, "OPP", "H", lambda_att=BASE_MEAN) for g in range(GW + 1, GW + HORIZON)]
    _, row = run_single(4, "FWD", overrides=GOAL_ONLY, fixtures=fixtures_doc(rows))
    # Two 90-minute appearances already make 4.
    assert row.p4_gw[0] == pytest.approx(1.0)


def test_rows_still_parse_as_calibrate_predictions():
    result, _ = run_single(3, "MID")
    for doc in result.to_documents():
        assert doc["p4_gw"] == [round(v, 3) for v in doc["p4_gw"]]
        assert len(doc["p4_gw"]) == len(doc["ep_gw"])
        assert all(0.0 <= v <= 1.0 for v in doc["p4_gw"])
        PlayerPrediction.model_validate({**doc, "position": Position.MID})


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
    [warning] = [w for w in result.warnings if "fallback" in w]
    assert warning == (
        "league mean for MID uses the v1 fallback table — only 0 players in the loaded "
        "history have history_past with ≥ 900 prior minutes (need 8); with "
        "--history-from summaries, fetch more with summaries --shortlist")


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


def test_config_blend_k_changes_the_computed_prior_weight():
    bootstrap = make_bootstrap([player()])
    history = [match_record_payload(minutes=90, round=1), match_record_payload(minutes=90, round=2)]
    result = build_predictions(
        bootstrap, {1: summary(history=history)}, fixtures_doc(),
        inputs_doc("MID", [judged()]), gw=GW, config=replace(DEFAULT_CONFIG, blend_k=300.0),
    )
    assert result.rows[0].rates.prior_weight == pytest.approx(300 / 480)


def test_no_history_blend_k_applies_only_to_league_mean_priors():
    history = [match_record_payload(minutes=90, round=1), match_record_payload(minutes=90, round=2)]
    hist_past = [past_season_payload(season_name="2025/26", minutes=1800)]

    def rates(history_past, config):
        result = build_predictions(
            make_bootstrap([player()]), {1: summary(history_past=history_past, history=history)},
            fixtures_doc(), inputs_doc("MID", [judged()]), gw=GW, config=config,
        )
        return result.rows[0].rates

    config = replace(DEFAULT_CONFIG, blend_k_no_history=300.0)
    no_history = rates([], config)
    assert no_history.prior_source == "league_mean"
    assert no_history.prior_weight == pytest.approx(300 / 480)
    assert rates(hist_past, config).prior_weight == pytest.approx(600 / 780)
    assert DEFAULT_CONFIG.blend_k_no_history is None
    assert rates([], DEFAULT_CONFIG).prior_weight == pytest.approx(600 / 780)


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


# ------------------------------------------------------------- defcon


def mid_rates(history_past, *, summaries=None, players=None):
    bootstrap = make_bootstrap([player()] + (players or []))
    world = {1: summary(history_past=history_past), **(summaries or {})}
    result = build_predictions(bootstrap, world, fixtures_doc(), inputs_doc("MID", [judged()]), gw=GW)
    return result, result.rows[0].rates


def test_defcon_counts_from_the_first_season_that_recorded_it():
    assert DEFCON_FIRST_SEASON == "2024/25"


def test_seasons_before_defcon_existed_leave_dc90_at_the_league_mean():
    old = past_season_payload(season_name="2023/24", minutes=2700, expected_goals="9.0", defensive_contribution=0.0)
    _, rates = mid_rates([old])
    league = LEAGUE_FALLBACK[Position.MID]
    assert rates.dc90 == league.dc90
    assert rates.dc90_prior == league.dc90
    assert rates.xg90 == pytest.approx(shrink_rate(0.3, 2700, league.xg90))


def test_mixed_seasons_take_dc90_from_defcon_seasons_and_shrink_by_their_minutes():
    latest = past_season_payload(season_name="2024/25", minutes=450, expected_goals="0.0", defensive_contribution=60.0)
    old = past_season_payload(season_name="2023/24", minutes=2000, expected_goals="0.0", defensive_contribution=0.0)
    _, rates = mid_rates([latest, old])
    league = LEAGUE_FALLBACK[Position.MID]
    assert rates.prior_minutes == 2450
    assert rates.dc90 == pytest.approx(shrink_rate(12.0, 450, league.dc90))
    assert rates.xg90 == pytest.approx(shrink_rate(0.0, 2450, league.xg90))


def test_a_recorded_zero_from_a_defcon_season_stays_zero():
    genuine = past_season_payload(season_name="2024/25", minutes=2700, defensive_contribution=0.0)
    _, rates = mid_rates([genuine])
    assert rates.dc90 == pytest.approx(shrink_rate(0.0, 2700, LEAGUE_FALLBACK[Position.MID].dc90))


# ------------------------------------------------------------- finishing


def finishing_seasons() -> list[dict]:
    return [past_season_payload(season_name="2023/24", goals_scored=7, expected_goals="5.0"),
            past_season_payload(season_name="2024/25", goals_scored=5, expected_goals="3.0")]


def as_seasons(payloads: list[dict]) -> list[PastSeason]:
    return [PastSeason.model_validate(p) for p in payloads]


def finishing_rates(*, overrides=None, **fields) -> EffectiveRates:
    bootstrap = make_bootstrap([player()])
    extra = {"overrides": overrides, "reason": "t"} if overrides else {}
    result = build_predictions(
        bootstrap, {1: summary(history_past=finishing_seasons())}, fixtures_doc(),
        inputs_doc("MID", [judged(**extra)]), gw=GW, config=replace(DEFAULT_CONFIG, **fields),
    )
    return result.rows[0].rates


def test_finishing_multiplier_is_heavily_shrunk():
    assert finishing_multiplier(as_seasons(finishing_seasons()), 10) == pytest.approx(22 / 18)


def test_seasons_before_xg_existed_are_ignored():
    assert XG_FIRST_SEASON == "2022/23"
    old = past_season_payload(season_name="2021/22", goals_scored=9, expected_goals="0.0")
    assert finishing_multiplier(as_seasons([*finishing_seasons(), old]), 10) == pytest.approx(22 / 18)
    assert finishing_multiplier(as_seasons([old]), 10) == 1.0


def test_multiplier_scales_xg90_but_not_an_override():
    off, on = finishing_rates(), finishing_rates(finishing_k=10)
    assert on.finishing_mult == pytest.approx(22 / 18)
    assert on.xg90 == pytest.approx(off.xg90 * 22 / 18)
    assert on.xa90 == off.xa90

    overridden = finishing_rates(overrides={"xg90": 0.5}, finishing_k=10)
    assert overridden.xg90 == 0.5
    assert overridden.finishing_mult == 1.0


def test_none_disables():
    assert DEFAULT_CONFIG.finishing_k is None
    assert finishing_multiplier(as_seasons(finishing_seasons()), None) == 1.0
    assert finishing_rates().finishing_mult == 1.0


@pytest.mark.parametrize("value", [0, 0.0, -10.0])
def test_config_refuses_a_finishing_k_that_is_not_positive(value):
    with pytest.raises(ValueError, match="finishing_k"):
        ModelConfig(finishing_k=value)


def test_config_finishing_k_from_int_has_the_float_digest():
    config = ModelConfig(finishing_k=10)
    assert isinstance(config.finishing_k, float)
    assert config.digest() == ModelConfig(finishing_k=10.0).digest() != DEFAULT_CONFIG.digest()


def test_league_dc90_ignores_minutes_from_before_defcon_existed():
    pool_ids = list(range(10, 10 + LEAGUE_POOL_MIN))
    pool = {
        i: summary(history_past=[
            past_season_payload(season_name="2025/26", minutes=450, defensive_contribution=45.0),
            past_season_payload(season_name="2023/24", minutes=2000, defensive_contribution=0.0),
        ])
        for i in pool_ids
    }
    result, rates = mid_rates(
        [], summaries=pool,
        players=[player(id=i, web_name=f"Pool{i}", now_cost=45) for i in pool_ids],
    )
    assert result.league.dc90 == pytest.approx(9.0)
    assert rates.dc90 == pytest.approx(9.0)


# ------------------------------------------------------------- bonus


def test_bonus_rate_shrinks_toward_the_league_mean_by_a_starts_pseudo_count():
    assert BONUS_SHRINK_STARTS == {
        Position.GKP: 30, Position.DEF: 60, Position.MID: 20, Position.FWD: 15,
    }
    assert bonus_rate(
        prior_bonus=0, prior_starts=0, current_bonus=0, current_starts=0, league=0.5, k=15
    ) == 0.5
    assert bonus_rate(
        prior_bonus=4, prior_starts=10, current_bonus=2, current_starts=5, league=0.5, k=15
    ) == pytest.approx((6 + 15 * 0.5) / 30)


def test_bonus_rate_converges_to_the_observed_rate_with_many_starts():
    rate = bonus_rate(
        prior_bonus=12000, prior_starts=10000, current_bonus=0, current_starts=0, league=0.3, k=20
    )
    assert rate == pytest.approx(1.2, abs=0.01)


def bootstrap_player(**overrides) -> Player:
    return Player.model_validate(player(**overrides))


def test_league_bonus_is_starts_weighted_over_every_player_of_the_position():
    players = [
        bootstrap_player(id=1, bonus=10, starts=5),
        bootstrap_player(id=2, bonus=2, starts=15),
        bootstrap_player(id=3, bonus=7, starts=0),
    ]
    assert league_bonus_per_start(Position.MID, players) == pytest.approx(19 / 20)


def test_league_bonus_falls_back_to_the_table_before_anyone_has_started():
    players = [bootstrap_player(id=1, bonus=0, starts=0)]
    assert league_bonus_per_start(Position.FWD, players) == LEAGUE_FALLBACK[Position.FWD].bonus_per_start
    assert LEAGUE_FALLBACK[Position.FWD].bonus_per_start == 0.55


def bonus_world(*, starts: int, bonus: int) -> Bootstrap:
    # Twenty-five team-mates averaging 0.4 bonus per start set the league mean.
    others = [
        player(id=i, web_name=f"Pool{i}", now_cost=45, starts=10, bonus=4) for i in range(10, 35)
    ]
    return make_bootstrap([player(starts=starts, bonus=bonus)] + others)


def bonus_history(starts: int, bonus: int) -> list[dict]:
    return [
        match_record_payload(round=r, minutes=90, starts=1, bonus=bonus if r == 1 else 0)
        for r in range(1, starts + 1)
    ]


def test_three_starts_with_six_bonus_stay_near_the_league_mean():
    bootstrap = bonus_world(starts=3, bonus=6)
    league = (6 + 25 * 4) / (3 + 25 * 10)  # whole position, the player included
    k = BONUS_SHRINK_STARTS[Position.MID]
    result = build_predictions(
        bootstrap, {1: summary(history_past=[], history=bonus_history(3, 6))}, fixtures_doc(),
        inputs_doc("MID", [judged()]), gw=GW,
    )
    rate = result.rows[0].rates.bonus_per_start
    assert rate == pytest.approx((6 + k * league) / (3 + k))
    assert rate < 0.75


def test_no_starts_anywhere_gives_the_league_mean():
    bootstrap = bonus_world(starts=0, bonus=0)
    result = build_predictions(
        bootstrap, {1: summary(history_past=[])}, fixtures_doc(), inputs_doc("MID", [judged()]), gw=GW,
    )
    assert result.rows[0].rates.bonus_per_start == pytest.approx(100 / 250)
    assert result.league.bonus_per_start == pytest.approx(100 / 250)


def test_league_bonus_does_not_depend_on_which_summaries_are_cached():
    bootstrap = bonus_world(starts=0, bonus=0)
    rich = {
        i: summary(history_past=[past_season_payload(minutes=3000, starts=34, bonus=40)])
        for i in range(10, 35)
    }
    sparse = {1: summary(history_past=[])}
    doc = inputs_doc("MID", [judged()])
    with_pool = build_predictions(bootstrap, {**rich, **sparse}, fixtures_doc(), doc, gw=GW)
    without = build_predictions(bootstrap, sparse, fixtures_doc(), doc, gw=GW)
    assert with_pool.league.bonus_per_start == without.league.bonus_per_start == pytest.approx(0.4)
    assert with_pool.rows[0].rates.bonus_per_start == without.rows[0].rates.bonus_per_start


def test_bonus_pools_prior_seasons_and_this_season_without_the_blend_floor():
    # 3000 current minutes put the minutes blend on its 0.2 floor; bonus ignores it.
    bootstrap = bonus_world(starts=34, bonus=0)
    hist_past = [past_season_payload(season_name="2025/26", minutes=3060, starts=34, bonus=24)]
    history = bonus_history(34, 34)
    result = build_predictions(
        bootstrap, {1: summary(history_past=hist_past, history=history)}, fixtures_doc(),
        inputs_doc("MID", [judged()]), gw=GW,
    )
    rates = result.rows[0].rates
    assert rates.prior_weight == BLEND_PRIOR_FLOOR
    league = result.league.bonus_per_start
    k = BONUS_SHRINK_STARTS[Position.MID]
    assert rates.bonus_per_start == pytest.approx((24 + 34 + k * league) / (34 + 34 + k))


def test_prior_weight_override_does_not_reweight_bonus():
    bootstrap = bonus_world(starts=3, bonus=6)
    hist_past = [past_season_payload(season_name="2025/26", minutes=900, starts=10, bonus=2)]
    world = {1: summary(history_past=hist_past, history=bonus_history(3, 6))}
    plain = build_predictions(bootstrap, world, fixtures_doc(), inputs_doc("MID", [judged()]), gw=GW)
    pinned = build_predictions(
        bootstrap, world, fixtures_doc(),
        inputs_doc("MID", [judged(overrides={"prior_weight": 1.0}, reason="t")]), gw=GW,
    )
    assert pinned.rows[0].rates.bonus_per_start == plain.rows[0].rates.bonus_per_start


def test_bonus_override_still_wins():
    bootstrap = bonus_world(starts=3, bonus=6)
    result = build_predictions(
        bootstrap, {1: summary(history_past=[], history=bonus_history(3, 6))}, fixtures_doc(),
        inputs_doc("MID", [judged(overrides={"bonus_per_start": 1.1}, reason="t")]), gw=GW,
    )
    assert result.rows[0].rates.bonus_per_start == 1.1


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


ACCENT_PAIRS = [
    ("Lindelof", "Lindelöf"), ("F.Kadioglu", "F.Kadıoğlu"), ("Diakite", "Diakité"),
    ("Muharemovic", "Muharemović"), ("Guehi", "Guéhi"), ("Ruben", "Rúben"),
    ("Ait-Nouri", "Aït-Nouri"), ("Dedic", "Dedić"), ("Schar", "Schär"),
    ("Milenkovic", "Milenković"), ("Munoz", "Muñoz"), ("Petrovic", "Petrović"),
    ("Hornicek", "Horníček"), ("Joao Pedro", "João Pedro"), ("Sesko", "Šeško"),
    ("Gyokeres", "Gyökeres"), ("Rodriguez", "Rodríguez"),
]


@pytest.mark.parametrize("typed, web_name", ACCENT_PAIRS)
def test_names_match_ignores_accents_on_the_real_pairs(typed, web_name):
    assert names_match(typed, web_name)


@pytest.mark.parametrize("typed, web_name", [
    ("odegaard", "Ødegaard"), ("Sorloth", "Sørloth"), ("Mlynski", "Młyński"),
    ("Dordevic", "Đorđević"), ("Gross", "Groß"), ("Aebischer", "Æbischer"),
    ("Joao  Pedro", "João Pedro"), ("SAKA", "Saka"),
])
def test_names_match_folds_letters_without_a_decomposition(typed, web_name):
    assert names_match(typed, web_name)


@pytest.mark.parametrize("typed, web_name", [
    ("Saka", "Salah"), ("Joao", "João Pedro"), ("Sesko", "Seskos"),
])
def test_names_match_still_refuses_different_names(typed, web_name):
    assert not names_match(typed, web_name)


def test_build_accepts_an_accent_free_name_and_keeps_the_web_name():
    bootstrap = make_bootstrap([player(web_name="Šeško")])
    result = build_predictions(bootstrap, {1: summary()}, fixtures_doc(),
                               inputs_doc("MID", [judged(name="Sesko")]), gw=GW)
    assert result.rows[0].name == "Šeško"


def test_build_refuses_a_wrong_name_even_without_accents():
    bootstrap = make_bootstrap([player(web_name="Salah")])
    with pytest.raises(ValueError, match="does not match"):
        build_predictions(bootstrap, {1: summary()}, fixtures_doc(),
                          inputs_doc("MID", [judged(name="Saka")]), gw=GW)


def test_build_warns_when_p_start_differs_from_the_first_gameweek():
    bootstrap = make_bootstrap([player()])
    result = build_predictions(
        bootstrap, {1: summary()}, fixtures_doc(),
        inputs_doc("MID", [judged(p_start=0.6, p_start_gw=[0.9] * HORIZON)]), gw=GW,
    )
    assert "id 1 Alpha: p_start 0.60 ignored, p_start_gw[0] is 0.90" in result.warnings
    assert result.rows[0].p_start == 0.9


@pytest.mark.parametrize("p_start, gw0", [(0.9, 0.9), (0.9, 0.904), (0.9, None)])
def test_build_is_silent_when_p_start_agrees_or_is_flat(p_start, gw0):
    bootstrap = make_bootstrap([player()])
    extra = {} if gw0 is None else {"p_start_gw": [gw0] * HORIZON}
    result = build_predictions(
        bootstrap, {1: summary()}, fixtures_doc(),
        inputs_doc("MID", [judged(p_start=p_start, **extra)]), gw=GW,
    )
    assert not any("ignored" in w for w in result.warnings)


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


def test_coverage_lets_an_allowed_absentee_through_with_a_warning():
    bootstrap = make_bootstrap([
        player(),
        player(id=2, web_name="Costly", now_cost=75, status="a"),
        player(id=3, web_name="Pricey", now_cost=80, status="a"),
    ])
    with pytest.raises(ValueError, match="Pricey"):
        build_predictions(
            bootstrap, {}, fixtures_doc(), inputs_doc("MID", [judged()]), gw=GW,
            allow_missing=frozenset({2}),
        )
    result = build_predictions(
        bootstrap, {}, fixtures_doc(), inputs_doc("MID", [judged()]), gw=GW,
        allow_missing=frozenset({2, 3}),
    )
    assert [r.id for r in result.rows] == [1]
    assert any("id 2 Costly" in w and "id 3 Pricey" in w for w in result.warnings)


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


def test_force_prior_weight_sets_every_row_and_supersedes_row_overrides():
    document = inputs_doc("MID", [
        judged(),
        judged(id=2, name="Beta", overrides={"prior_weight": 0.3, "xg90": 0.4}, reason="r"),
    ])
    forced = force_prior_weight(document, 0.6)
    assert [entry.overrides.prior_weight for entry in forced.players] == [0.6, 0.6]
    assert forced.players[1].overrides.xg90 == 0.4
    assert forced.players[0].reason is None
    assert document.players[0].overrides is None


def test_forced_prior_weight_reaches_the_effective_rates():
    bootstrap = make_bootstrap([player()])
    history = [match_record_payload(round=1, minutes=90, expected_goals="0.9")]
    result = build_predictions(
        bootstrap, {1: summary(history=history)}, fixtures_doc(),
        force_prior_weight(inputs_doc("MID", [judged()]), 1.0), gw=GW,
    )
    assert result.rows[0].rates.prior_weight == 1.0


# ------------------------------------------------- weighted, adjusted current rates


RATED = {"TST": {"att": 1.1, "defw": 0.9}, "OPP": {"att": 1.2, "defw": 1.25}}


def rich_history() -> list[dict]:
    rows = [
        (1, 90, "0.60", "0.20", 11.0, 4, 2, 1, True),
        (2, 0, "0.00", "0.00", 0.0, 0, 0, 0, False),
        (3, 75, "0.10", "0.40", 7.0, 2, 0, 0, False),
        (4, 90, "0.90", "0.05", 13.0, 5, 3, 0, True),
    ]
    return [
        match_record_payload(
            fixture=100 + rnd, round=rnd, minutes=minutes, starts=int(minutes > 0),
            expected_goals=xg, expected_assists=xa, defensive_contribution=dc,
            saves=saves, bonus=bonus, yellow_cards=yellow, was_home=home, opponent_team=2,
        )
        for rnd, minutes, xg, xa, dc, saves, bonus, yellow, home in rows
    ]


def rich_documents(position_code: int, position_name: str, config=DEFAULT_CONFIG) -> list[dict]:
    bootstrap = make_bootstrap([player(element_type=position_code)])
    past = [
        past_season_payload(season_name="2025/26", minutes=1500, starts=17, saves=40,
                            yellow_cards=3, defensive_contribution=150.0),
        past_season_payload(season_name="2024/25", minutes=900, starts=10, saves=25,
                            yellow_cards=2, defensive_contribution=90.0),
    ]
    result = build_predictions(
        bootstrap, {1: summary(history_past=past, history=rich_history())},
        fixtures_doc(ratings=RATED), inputs_doc(position_name, [judged()]), gw=GW, config=config,
    )
    documents = [{k: v for k, v in doc.items() if k not in ("model", "p4_gw", "returns5")}
                 for doc in result.to_documents()]
    for doc in documents:
        assert doc["rates"].pop("finishing_mult") == 1.0
    return documents


# Built by the code before the weighted, adjusted current totals existed.
PRE_CHANGE_DOCUMENTS = {'GKP': {'id': 1,
         'name': 'Alpha',
         'team': 'TST',
         'price': 6.0,
         'p_start': 1.0,
         'p_start_gw': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
         'ep_gw': [8.771, 8.771, 8.771, 8.771, 8.771, 8.771],
         'ep_total6': 52.63,
         'ep_per_million': 8.771,
         'uncertainty': 'LOW',
         'notes': 'n',
         'fixtures': ['OPP(H)', 'OPP(A)', 'OPP(H)', 'OPP(A)', 'OPP(H)', 'OPP(A)'],
         'terms': {'appearance': 11.98,
                   'attack': 28.88,
                   'clean_sheet': 7.18,
                   'goals_conceded': -1.63,
                   'defcon': 0.0,
                   'saves': 2.63,
                   'bonus': 4.82,
                   'cards': -1.23},
         'rates': {'xg90': 0.726,
                   'xa90': 0.363,
                   'dc90': 8.121,
                   'saves90': 2.939,
                   'bonus_per_start': 0.73,
                   'yellow90': 0.211,
                   'minutes_per_start': 87.556,
                   'dc90_prior': 6.923,
                   'prior_weight': 0.702,
                   'prior_source': 'history_past',
                   'attack_mult': 1.0,
                   'prior_minutes': 1500,
                   'current_minutes': 255}},
 'DEF': {'id': 1,
         'name': 'Alpha',
         'team': 'TST',
         'price': 6.0,
         'p_start': 1.0,
         'p_start_gw': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
         'ep_gw': [9.012, 9.012, 9.012, 9.012, 9.012, 9.012],
         'ep_total6': 54.07,
         'ep_per_million': 9.012,
         'uncertainty': 'LOW',
         'notes': 'n',
         'fixtures': ['OPP(H)', 'OPP(A)', 'OPP(H)', 'OPP(A)', 'OPP(H)', 'OPP(A)'],
         'terms': {'appearance': 11.95,
                   'attack': 29.18,
                   'clean_sheet': 7.14,
                   'goals_conceded': -1.61,
                   'defcon': 5.55,
                   'saves': 0.0,
                   'bonus': 3.17,
                   'cards': -1.31},
         'rates': {'xg90': 0.737,
                   'xa90': 0.376,
                   'dc90': 9.498,
                   'saves90': 2.453,
                   'bonus_per_start': 0.588,
                   'yellow90': 0.227,
                   'minutes_per_start': 86.746,
                   'dc90_prior': 8.885,
                   'prior_weight': 0.702,
                   'prior_source': 'history_past',
                   'attack_mult': 1.0,
                   'prior_minutes': 1500,
                   'current_minutes': 255}},
 'MID': {'id': 1,
         'name': 'Alpha',
         'team': 'TST',
         'price': 6.0,
         'p_start': 1.0,
         'p_start_gw': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
         'ep_gw': [7.698, 7.698, 7.698, 7.698, 7.698, 7.698],
         'ep_total6': 46.19,
         'ep_per_million': 7.698,
         'uncertainty': 'LOW',
         'notes': 'n',
         'fixtures': ['OPP(H)', 'OPP(A)', 'OPP(H)', 'OPP(A)', 'OPP(H)', 'OPP(A)'],
         'terms': {'appearance': 11.92,
                   'attack': 25.71,
                   'clean_sheet': 1.78,
                   'goals_conceded': 0.0,
                   'defcon': 2.83,
                   'saves': 0.0,
                   'bonus': 5.25,
                   'cards': -1.3},
         'rates': {'xg90': 0.755,
                   'xa90': 0.387,
                   'dc90': 9.255,
                   'saves90': 2.453,
                   'bonus_per_start': 0.875,
                   'yellow90': 0.227,
                   'minutes_per_start': 85.937,
                   'dc90_prior': 8.538,
                   'prior_weight': 0.702,
                   'prior_source': 'history_past',
                   'attack_mult': 1.0,
                   'prior_minutes': 1500,
                   'current_minutes': 255}},
 'FWD': {'id': 1,
         'name': 'Alpha',
         'team': 'TST',
         'price': 6.0,
         'p_start': 1.0,
         'p_start_gw': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
         'ep_gw': [6.982, 6.982, 6.982, 6.982, 6.982, 6.982],
         'ep_total6': 41.89,
         'ep_per_million': 6.982,
         'uncertainty': 'LOW',
         'notes': 'n',
         'fixtures': ['OPP(H)', 'OPP(A)', 'OPP(H)', 'OPP(A)', 'OPP(H)', 'OPP(A)'],
         'terms': {'appearance': 11.91,
                   'attack': 22.36,
                   'clean_sheet': 0.0,
                   'goals_conceded': 0.0,
                   'defcon': 2.51,
                   'saves': 0.0,
                   'bonus': 6.39,
                   'cards': -1.27},
         'rates': {'xg90': 0.79,
                   'xa90': 0.383,
                   'dc90': 8.688,
                   'saves90': 2.453,
                   'bonus_per_start': 1.064,
                   'yellow90': 0.222,
                   'minutes_per_start': 85.613,
                   'dc90_prior': 7.731,
                   'prior_weight': 0.702,
                   'prior_source': 'history_past',
                   'attack_mult': 1.0,
                   'prior_minutes': 1500,
                   'current_minutes': 255}}}


@pytest.mark.parametrize("code, name", [(1, "GKP"), (2, "DEF"), (3, "MID"), (4, "FWD")])
def test_defaults_reproduce_today_documents(code, name):
    assert rich_documents(code, name) == [PRE_CHANGE_DOCUMENTS[name]]


def test_new_config_fields_default_off():
    assert DEFAULT_CONFIG.half_life_matches is None
    assert DEFAULT_CONFIG.opponent_adjust is False
    assert DEFAULT_CONFIG.opponent_adjust_saves is False
    assert DEFAULT_CONFIG.blend_on_effective_minutes is False


@pytest.mark.parametrize("half_life", [0, 0.0, -1.0])
def test_config_refuses_a_half_life_that_is_not_positive(half_life):
    with pytest.raises(ValueError, match="half_life_matches"):
        ModelConfig(half_life_matches=half_life)


@pytest.mark.parametrize("field", ["blend_k", "blend_k_no_history"])
@pytest.mark.parametrize("value", [0, 0.0, -300.0])
def test_config_refuses_a_blend_k_that_is_not_positive(field, value):
    with pytest.raises(ValueError, match=field):
        ModelConfig(**{field: value})


def test_config_validation_leaves_the_production_digest():
    assert DEFAULT_CONFIG.digest() == "64ad9c9c"


def test_config_half_life_from_int_has_the_float_digest():
    config = ModelConfig(half_life_matches=2)
    assert isinstance(config.half_life_matches, float)
    assert config.digest() == ModelConfig(half_life_matches=2.0).digest()


def two_rounds() -> list[MatchRecord]:
    return [
        MatchRecord.model_validate(match_record_payload(
            fixture=11, round=1, minutes=90, expected_goals="1.0")),
        MatchRecord.model_validate(match_record_payload(
            fixture=12, round=2, minutes=90, expected_goals="0.0")),
    ]


def test_recency_weighted_current_rate():
    league = LEAGUE_FALLBACK[Position.MID]
    config = replace(DEFAULT_CONFIG, half_life_matches=1.0)
    totals = current_totals(two_rounds(), config, ratings=None, team_names={}, base=None)
    # 0.5×1.0 / (0.5×90 + 1×90) × 90
    assert totals.rates(league).xg90 == pytest.approx(1 / 3)

    def rates(**fields):
        bootstrap = make_bootstrap([player()])
        history = [r.model_dump() for r in two_rounds()]
        result = build_predictions(
            bootstrap, {1: summary(history=history)}, fixtures_doc(),
            inputs_doc("MID", [judged()]), gw=GW, config=replace(config, **fields),
        )
        return result.rows[0].rates

    assert rates().current_minutes == 180
    assert rates().prior_weight == pytest.approx(600 / 780)
    assert rates(blend_on_effective_minutes=True).prior_weight == pytest.approx(600 / 735)
    assert rates(blend_on_effective_minutes=True).current_minutes == 180


def adjusted_row(**overrides) -> MatchRecord:
    payload = {"fixture": 11, "round": 1, "minutes": 90, "expected_goals": "0.6",
               "expected_assists": "0.0", "saves": 3, "was_home": True, "opponent_team": 2}
    return MatchRecord.model_validate(match_record_payload(**{**payload, **overrides}))


def adjusted_totals(rows, **fields):
    config = replace(DEFAULT_CONFIG, **fields)
    ratings = fixtures_doc(ratings={"TST": {"att": 1.0, "defw": 1.0},
                                    "OPP": {"att": 1.2, "defw": 1.2}}).ratings
    return current_totals(rows, config, ratings=ratings, team_names={1: "TST", 2: "OPP"},
                          base=BaseLambda(**BASE))


def test_opponent_adjusted_current_rate():
    league = LEAGUE_FALLBACK[Position.GKP]
    totals = adjusted_totals([adjusted_row()], opponent_adjust=True)
    assert totals.rates(league).xg90 == pytest.approx(0.6 * BASE_MEAN / (1.54 * 1.2))
    assert totals.rates(league).saves90 == pytest.approx(3.0)
    assert totals.unadjusted == 0

    saves = adjusted_totals([adjusted_row()], opponent_adjust_saves=True)
    assert saves.rates(league).xg90 == pytest.approx(0.6)
    assert saves.rates(league).saves90 == pytest.approx(3.0 * BASE_MEAN / (1.33 * 1.2))

    off = adjusted_totals([adjusted_row()])
    assert off.rates(league).xg90 == pytest.approx(0.6)
    assert off.unadjusted == 0


@pytest.mark.parametrize("missing", [{"opponent_team": None}, {"opponent_team": 99},
                                     {"was_home": None}])
def test_a_row_without_an_opponent_rating_contributes_unadjusted(missing):
    rows = [adjusted_row(), adjusted_row(fixture=12, round=2, **missing)]
    totals = adjusted_totals(rows, opponent_adjust=True)
    adjusted = 0.6 * BASE_MEAN / (1.54 * 1.2)
    assert totals.rates(LEAGUE_FALLBACK[Position.MID]).xg90 == pytest.approx((adjusted + 0.6) / 2)
    assert totals.unadjusted == 1


def adjustment_warnings(position: str = "MID", **fields) -> list[str]:
    code = {"GKP": 1, "MID": 3}[position]
    bootstrap = make_bootstrap([player(element_type=code),
                                player(id=2, web_name="Beta", element_type=code)])
    rows = [adjusted_row().model_dump(), adjusted_row(fixture=12, round=2, opponent_team=None)
            .model_dump()]
    result = build_predictions(
        bootstrap, {1: summary(history=rows), 2: summary(history=rows)}, fixtures_doc(),
        inputs_doc(position, [judged(), judged(id=2, name="Beta")]), gw=GW,
        config=replace(DEFAULT_CONFIG, **fields),
    )
    return [w for w in result.warnings if "opponent" in w]


def test_one_warning_line_counts_the_unadjusted_rows():
    [line] = adjustment_warnings(opponent_adjust=True)
    assert "2 played match row(s)" in line
    assert adjustment_warnings(opponent_adjust=True, opponent_adjust_saves=True) == [line]
    assert adjustment_warnings("GKP", opponent_adjust_saves=True) == [line]
    assert adjustment_warnings() == []


def test_the_saves_adjustment_alone_never_warns_for_an_outfield_position():
    assert adjustment_warnings("MID", opponent_adjust_saves=True) == []


def test_recency_weights_defcon_but_never_adjusts_it_for_the_opponent():
    rows = [adjusted_row(defensive_contribution=12.0),
            adjusted_row(fixture=12, round=2, defensive_contribution=6.0)]
    totals = adjusted_totals(rows, opponent_adjust=True, half_life_matches=1.0)
    # (0.5×12 + 1×6) / (0.5×90 + 1×90) × 90
    assert totals.rates(LEAGUE_FALLBACK[Position.DEF]).dc90 == pytest.approx(8.0)
    assert totals.minutes == 180 and totals.starts == 2
