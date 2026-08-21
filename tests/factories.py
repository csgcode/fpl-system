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
        "total_points": 0,
        "form": "0.0",
        "selected_by_percent": "45.3",
        "ict_index": "0.0",
        "expected_goals": "0.00",
        "expected_assists": "0.00",
        "defensive_contribution": 0.0,
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
    }
    payload.update(overrides)
    return payload


def bootstrap_payload(
    elements: list[dict] | None = None,
    teams: list[dict] | None = None,
    events: list[dict] | None = None,
) -> dict[str, Any]:
    return {
        "events": events if events is not None else [event_payload()],
        "teams": teams if teams is not None else [team_payload()],
        "elements": elements if elements is not None else [player_payload()],
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
        "expected_goals": "17.20",
        "expected_assists": "9.10",
        "defensive_contribution": 4.0,
    }
    payload.update(overrides)
    return payload


def element_summary_payload(history_past: list[dict] | None = None) -> dict[str, Any]:
    return {
        "fixtures": [],
        "history": [],
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
