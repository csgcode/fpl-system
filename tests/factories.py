"""Synthetic API payloads mirroring real FPL API shapes (string-encoded
floats, nullable fields, extra unmodelled keys). No real-player data."""

from __future__ import annotations

from typing import Any


def player_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "id": 1,
        "web_name": "Alpha",
        "first_name": "Test",
        "second_name": "Alpha",
        "team": 1,
        "element_type": 3,
        "now_cost": 145,
        "status": "a",
        "chance_of_playing_next_round": None,
        "news": "",
        "news_added": None,
        "minutes": 0,
        "starts": 0,
        "total_points": 0,
        "form": "0.0",
        "selected_by_percent": "45.3",
        "ict_index": "0.0",
        "expected_goals": "0.00",
        "expected_assists": "0.00",
        "expected_goals_conceded": "0.00",
        "clean_sheets": 0,
        "goals_conceded": 0,
        "saves": 0,
        "defensive_contribution": 0.0,
        "clearances_blocks_interceptions": 0,
        "recoveries": 0,
        "tackles": 0,
        "cost_change_start": 0,
        "cost_change_event": 0,
        "penalties_order": 1,
        "direct_freekicks_order": None,
        "corners_and_indirect_freekicks_order": None,
        "some_future_api_field": 123,
    }
    payload.update(overrides)
    return payload


def team_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "id": 1,
        "name": "Test Town",
        "short_name": "TST",
        "strength_attack_home": 1200,
        "strength_attack_away": 1250,
        "strength_defence_home": 1180,
        "strength_defence_away": 1220,
    }
    payload.update(overrides)
    return payload


def event_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "id": 1,
        "name": "Gameweek 1",
        "deadline_time": "2026-08-14T17:30:00Z",
        "finished": False,
        "is_current": False,
        "is_next": True,
        "data_checked": False,
    }
    payload.update(overrides)
    return payload


def chip_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "id": 1,
        "name": "wildcard",
        "number": 1,
        "start_event": 2,
        "stop_event": 19,
        "chip_type": "transfer",
    }
    payload.update(overrides)
    return payload


def bootstrap_payload(
    elements: list[dict] | None = None,
    teams: list[dict] | None = None,
    events: list[dict] | None = None,
    chips: list[dict] | None = None,
) -> dict[str, Any]:
    return {
        "events": events if events is not None else [event_payload()],
        "teams": teams if teams is not None else [team_payload()],
        "elements": elements if elements is not None else [player_payload()],
        "chips": chips if chips is not None else [chip_payload()],
    }


def fixture_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "id": 1,
        "event": 1,
        "team_h": 1,
        "team_a": 2,
        "team_h_difficulty": 2,
        "team_a_difficulty": 4,
        "kickoff_time": "2026-08-15T14:00:00Z",
        "finished": False,
    }
    payload.update(overrides)
    return payload


def past_season_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "season_name": "2025/26",
        "start_cost": 130,
        "end_cost": 145,
        "minutes": 3060,
        "total_points": 211,
        "goals_scored": 18,
        "assists": 10,
        "clean_sheets": 12,
        "goals_conceded": 30,
        "saves": 0,
        "bonus": 24,
        "bps": 700,
        "starts": 34,
        "expected_goals": "17.20",
        "expected_assists": "9.10",
        "expected_goals_conceded": "31.40",
        "defensive_contribution": 4.0,
    }
    payload.update(overrides)
    return payload


def match_record_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "fixture": 10,
        "round": 5,
        "minutes": 90,
        "starts": 1,
        "total_points": 6,
        "goals_scored": 1,
        "assists": 0,
        "clean_sheets": 0,
        "goals_conceded": 1,
        "saves": 0,
        "bonus": 1,
        "bps": 23,
        "expected_goals": "0.44",
        "expected_assists": "0.10",
        "expected_goals_conceded": "1.20",
        "defensive_contribution": 3.0,
        "some_future_api_field": "ignored",
    }
    payload.update(overrides)
    return payload


def element_summary_payload(
    history_past: list[dict] | None = None,
    history: list[dict] | None = None,
) -> dict[str, Any]:
    return {
        "fixtures": [],
        "history": history if history is not None else [],
        "history_past": history_past if history_past is not None else [past_season_payload()],
    }


def entry_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "id": 42,
        "name": "Test XI",
        "summary_overall_points": 0,
        "last_deadline_bank": 5,
        "last_deadline_value": 1000,
    }
    payload.update(overrides)
    return payload


def entry_history_event_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "event": 1,
        "points": 61,
        "total_points": 61,
        "rank": 500000,
        "overall_rank": 412345,
        "bank": 5,
        "value": 1001,
        "event_transfers": 0,
        "event_transfers_cost": 0,
        "points_on_bench": 4,
    }
    payload.update(overrides)
    return payload


def entry_history_payload(current: list[dict] | None = None) -> dict[str, Any]:
    return {
        "current": current if current is not None else [entry_history_event_payload()],
        "past": [],
        "chips": [],
    }


def pick_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "element": 1,
        "position": 1,
        "multiplier": 1,
        "is_captain": False,
        "is_vice_captain": False,
        "element_type": 1,
    }
    payload.update(overrides)
    return payload


def event_picks_payload(
    picks: list[dict] | None = None, active_chip: str | None = None
) -> dict[str, Any]:
    return {
        "active_chip": active_chip,
        "automatic_subs": [],
        "entry_history": {"event": 1, "points": 61},
        "picks": picks if picks is not None else [pick_payload()],
    }
