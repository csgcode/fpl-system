from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from fpl.kickoffs import UNREADABLE, back_gw, club_kickoffs, return_date
from fpl.models import Fixture
from tests.factories import fixture_payload


def fixture(id: int, event: int | None, home: int, away: int, kickoff: str | None) -> Fixture:
    return Fixture.model_validate(fixture_payload(
        id=id, event=event, team_h=home, team_a=away, kickoff_time=kickoff))


# --- club_kickoffs ---------------------------------------------------------


def test_club_kickoffs_lists_each_clubs_dates_per_window_gameweek():
    fixtures = [
        fixture(1, 10, 1, 2, "2026-11-07T15:00:00Z"),
        fixture(2, 11, 3, 1, "2026-11-21T17:30:00Z"),
        fixture(3, 11, 1, 4, "2026-11-25T20:00:00Z"),
        fixture(4, 12, 2, 3, "2026-11-28T15:00:00Z"),
    ]
    clubs = club_kickoffs(fixtures, range(11, 13))
    assert clubs[1] == {11: (date(2026, 11, 21), date(2026, 11, 25))}
    assert clubs[2] == {12: (date(2026, 11, 28),)}
    assert clubs[3] == {11: (date(2026, 11, 21),), 12: (date(2026, 11, 28),)}


def test_club_kickoffs_orders_a_double_gameweek_by_kickoff():
    fixtures = [
        fixture(9, 11, 1, 4, "2026-11-25T20:00:00Z"),
        fixture(2, 11, 3, 1, "2026-11-21T17:30:00Z"),
    ]
    assert club_kickoffs(fixtures, range(11, 12))[1][11] == (
        date(2026, 11, 21), date(2026, 11, 25))


def test_club_kickoffs_skips_unscheduled_fixtures():
    fixtures = [
        fixture(1, None, 1, 2, "2026-11-21T15:00:00Z"),
        fixture(2, 11, 1, 3, None),
    ]
    assert club_kickoffs(fixtures, range(11, 12)) == {}


# --- return_date -----------------------------------------------------------

REF = date(2026, 11, 6)


@pytest.mark.parametrize("news, expected", [
    ("Hamstring injury - Expected back 18 Nov", date(2026, 11, 18)),
    ("Suspended until 2 Dec", date(2026, 12, 2)),
    ("Suspended until 02 Dec", date(2026, 12, 2)),
    ("Knee injury - Expected back 3 Sept.", date(2026, 9, 3)),
    ("Expected back 31 Oct", date(2026, 10, 31)),
])
def test_return_date_reads_the_dated_phrases(news, expected):
    assert return_date(news, REF) == expected


@pytest.mark.parametrize("news", [
    "",
    "Knee injury - Unknown return date",
    "Calf injury - 75% chance of playing",
    "Has joined Juventus on loan for the rest of the season",
    "Has joined Leicester City on loan until 2 Jan",
])
def test_return_date_is_none_without_a_dated_phrase(news):
    assert return_date(news, REF) is None


@pytest.mark.parametrize("news", [
    "Suspended until further notice",
    "Expected back 31 Feb",
    "Expected back 31 Nov",
    "Expected back 3 Foo",
])
def test_return_date_flags_a_phrase_whose_date_cannot_be_read(news):
    assert return_date(news, REF) is UNREADABLE


def test_return_date_rolls_a_january_date_written_in_december_into_next_year():
    assert return_date("Suspended until 2 Jan", date(2026, 12, 20)) == date(2027, 1, 2)


def test_return_date_takes_the_nearest_year():
    assert return_date("Expected back 8 May", date(2026, 11, 6)) == date(2026, 5, 8)
    assert return_date("Expected back 7 May", date(2026, 11, 6)) == date(2027, 5, 7)


def test_return_date_reads_29_february_in_the_leap_year_nearby():
    assert return_date("Expected back 29 Feb", date(2027, 11, 1)) == date(2028, 2, 29)
    assert return_date("Expected back 29 Feb", date(2028, 9, 1)) == date(2028, 2, 29)


def test_return_date_keeps_a_stale_date_in_the_past():
    assert return_date("Expected back 18 Oct", date(2026, 12, 20)) == date(2026, 10, 18)


def test_return_date_puts_a_late_december_date_written_in_january_in_last_year():
    assert return_date("Expected back 28 Dec", date(2027, 1, 3)) == date(2026, 12, 28)


# --- back_gw ---------------------------------------------------------------

CLUB = {
    11: (date(2026, 11, 21),),
    12: (date(2026, 11, 28), date(2026, 12, 2)),
    14: (date(2026, 12, 12),),
}
WINDOW = range(11, 17)


def test_back_gw_is_n_when_the_date_is_before_the_first_kickoff():
    assert back_gw(CLUB, WINDOW, date(2026, 11, 10)) == "11"


def test_back_gw_counts_a_kickoff_on_the_return_date_as_available():
    assert back_gw(CLUB, WINDOW, date(2026, 11, 21)) == "11"


def test_back_gw_rules_out_gameweeks_whose_fixtures_all_precede_the_date():
    assert back_gw(CLUB, WINDOW, date(2026, 11, 22)) == "12"


def test_back_gw_marks_a_double_gameweek_only_partly_ruled_out():
    assert back_gw(CLUB, WINDOW, date(2026, 12, 1)) == "12*"


def test_back_gw_skips_a_blank_gameweek():
    assert back_gw(CLUB, WINDOW, date(2026, 12, 3)) == "14"


def test_back_gw_rules_out_the_whole_window():
    assert back_gw(CLUB, WINDOW, date(2026, 12, 13)) == ">16"


def test_back_gw_names_the_clipped_window_end():
    assert back_gw({38: (date(2027, 5, 23),)}, range(37, 39), date(2027, 6, 1)) == ">38"


def test_back_gw_marks_gameweek_n_when_its_double_is_partly_ruled_out():
    club = {11: (date(2026, 11, 21), date(2026, 11, 25))}
    assert back_gw(club, WINDOW, date(2026, 11, 24)) == "11*"
