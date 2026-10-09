"""flag_delta: the freshness-gate diff. Only status, chance and news count;
news_added is ignored because it does not reliably move when a flag does."""

from __future__ import annotations

from fpl.freshness import FieldChange, flag_delta
from fpl.models import Player, Position
from tests.factories import player_payload


def make(**overrides) -> Player:
    return Player.model_validate(player_payload(**overrides))


def test_chance_change_is_detected_even_when_news_added_is_unchanged():
    stamp = "2026-10-01T09:00:00Z"
    old = [make(id=5, status="d", chance_of_playing_next_round=75, news="Knock", news_added=stamp)]
    new = [make(id=5, status="d", chance_of_playing_next_round=25, news="Knock", news_added=stamp)]
    [change] = flag_delta(old, new)
    assert change.id == 5
    assert change.changes == (FieldChange("chance_of_playing_next_round", 75, 25),)


def test_news_only_change_is_detected():
    old = [make(id=5, news="")]
    new = [make(id=5, news="Ill - 75% chance of playing")]
    [change] = flag_delta(old, new)
    assert change.changes == (FieldChange("news", "", "Ill - 75% chance of playing"),)


def test_status_change_is_detected_as_the_letter():
    [change] = flag_delta([make(id=5, status="a")], [make(id=5, status="i")])
    assert change.changes == (FieldChange("status", "a", "i"),)


def test_news_added_only_change_is_ignored():
    old = [make(id=5, news_added="2026-10-01T09:00:00Z")]
    new = [make(id=5, news_added="2026-10-02T09:00:00Z")]
    assert flag_delta(old, new) == []


def test_ids_bound_the_scope():
    old = [make(id=1), make(id=2)]
    new = [make(id=1, status="i"), make(id=2, status="i")]
    assert [c.id for c in flag_delta(old, new, ids=[2])] == [2]
    assert [c.id for c in flag_delta(old, new)] == [1, 2]


def test_a_player_absent_from_the_baseline_counts_as_a_change():
    [change] = flag_delta([], [make(id=9, web_name="Signing", element_type=4)])
    assert (change.id, change.web_name, change.position) == (9, "Signing", Position.FWD)
    assert change.changes == (FieldChange("in_baseline", False, True),)


def test_managers_are_outside_the_pool():
    assert flag_delta([make(id=3, element_type=5)], [make(id=3, element_type=5, status="i")]) == []
