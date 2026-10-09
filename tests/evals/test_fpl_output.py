"""Parsers over fpl CLI stdout. Inputs are real outputs copied from the GW4–GW6
data-collector transcripts."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from evals.harness.fpl_output import (
    CacheNote,
    bootstrap_facts,
    cache_notes,
    note_from_text,
    parse_datetime,
    prior_season_counts,
)

GW6_BOOTSTRAP = (
    "data/raw/gw6/bootstrap.json (fetched)\n"
    "fetched at 2026-10-09 13:31:49.122429+00:00\n"
    "players: 667, teams: 20, chips: 8\n"
    "current GW: 5, next GW: 6, next deadline: 2026-10-10 10:00:00+00:00\n"
    "EXIT 0\n"
    "data/raw/gw6/fixtures.json (380 fixtures) (fetched)\n"
    "EXIT 0"
)

GW5_ENTRY_CHAIN = (
    "entry 8455344 ('404 FC'), bank: 0, value: 996 (fetched)\n"
    "entry 8455344 event 4, active chip: none (cached, age 0.1h)\n"
    "pos  element  mult  role\n"
    "  1        1     1  \n"
    "entry 8455344 history (4 events) (cached, age 0.1h)\n"
    "event   pts   total    ovr rank   bank   value   tr  bench\n"
)


def test_cache_notes_split_a_chained_bootstrap_and_fixtures_call():
    notes = cache_notes(GW6_BOOTSTRAP)
    assert notes["bootstrap"] == CacheNote("fetched")
    assert notes["fixtures"] == CacheNote("fetched")


def test_cache_notes_classify_entry_picks_and_history():
    notes = cache_notes(GW5_ENTRY_CHAIN)
    assert notes["entry"] == CacheNote("fetched")
    assert notes["picks"] == CacheNote("cached")
    assert notes["entry-history"] == CacheNote("cached")


def test_cache_notes_read_summary_counts():
    notes = cache_notes("431 summaries under data/raw/gw5/players (421 fetched, 10 cached)")
    assert notes["summaries"] == CacheNote("mixed", fetched=421, cached=10)


def test_cache_notes_ignore_unrelated_output():
    assert cache_notes("wrote data/raw/gw5/players-slim.csv\nExit code 1") == {}


@pytest.mark.parametrize(
    ("text", "note"),
    [
        ("(fetched)", CacheNote("fetched")),
        ("(cached, age 0.1h)", CacheNote("cached")),
        ("cached, age 3.2h", CacheNote("cached")),
        ("421 fetched, 10 cached", CacheNote("mixed", fetched=421, cached=10)),
        ("(425 fetched, 0 cached)", CacheNote("mixed", fetched=425, cached=0)),
        ("421 fetched, 13 cached (434 shortlisted)",
         CacheNote("mixed", fetched=421, cached=13)),
        ("local only", CacheNote("local")),
        ("(local)", CacheNote("local")),
        ("done", None),
    ],
)
def test_note_from_text_reads_meta_md_spellings(text, note):
    assert note_from_text(text) == note


def test_bootstrap_facts():
    facts = bootstrap_facts(GW6_BOOTSTRAP)
    assert facts.fetched_at == datetime(2026, 10, 9, 13, 31, 49, tzinfo=UTC)
    assert facts.deadline == datetime(2026, 10, 10, 10, 0, tzinfo=UTC)
    assert facts.players == 667
    assert facts.current_status is None


def test_bootstrap_facts_read_the_status_line():
    facts = bootstrap_facts(
        GW6_BOOTSTRAP + "\ncurrent GW 5 status: finished=true data_checked=false")
    assert facts.current_status == (5, True, False)


def test_prior_season_counts():
    assert prior_season_counts(
        "wrote data/raw/gw4/prior-season.json\n"
        "players: 342, no_pl_history: 83, missing_summaries: 0"
    ) == (342, 83, 0)
    assert prior_season_counts("players: 667, teams: 20, chips: 8") is None


@pytest.mark.parametrize(
    "value",
    [
        "2026-09-18 12:49:57.221963+00:00",
        "2026-09-18 12:49:57+00:00",
        "2026-09-18 12:49:57 UTC",
        "2026-09-18T12:49:57Z",
    ],
)
def test_parse_datetime_compares_to_the_second(value):
    assert parse_datetime(value) == datetime(2026, 9, 18, 12, 49, 57, tzinfo=UTC)


def test_parse_datetime_rejects_garbage():
    assert parse_datetime("soon") is None
