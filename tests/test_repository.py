import pytest

from fpl.models import Player, PlayerStatus, Position
from fpl.repository import (
    PLAYERS_SLIM_COLUMNS,
    PlayerFilter,
    PlayerRepository,
    PlayerRow,
    slim_record,
)
from fpl.store import SnapshotStore
from tests.factories import bootstrap_payload, player_payload, team_payload

GW = 5


@pytest.fixture
def store(tmp_path) -> SnapshotStore:
    return SnapshotStore(tmp_path)


def save_bootstrap(store: SnapshotStore, **kwargs) -> PlayerRepository:
    store.save(GW, "bootstrap", bootstrap_payload(**kwargs), "url")
    return PlayerRepository(store)


def query_ids(
    repo: PlayerRepository,
    player_filter: PlayerFilter = PlayerFilter(),
    sort: str = "id",
    limit: int | None = None,
) -> list[int]:
    return [row.player.id for row in repo.query(GW, player_filter, sort, limit)]


def test_position_filter_returns_only_that_position(store):
    elements = [
        player_payload(id=1, element_type=1),
        player_payload(id=2, element_type=2),
        player_payload(id=3, element_type=3),
        player_payload(id=4, element_type=4),
    ]
    repo = save_bootstrap(store, elements=elements)

    ids = query_ids(repo, PlayerFilter(positions=frozenset({Position.MID})))

    assert ids == [3]


def test_mid_under_price_cap_combines_position_and_price(store):
    elements = [
        player_payload(id=1, element_type=3, now_cost=55),
        player_payload(id=2, element_type=3, now_cost=60),
        player_payload(id=3, element_type=2, now_cost=50),
    ]
    repo = save_bootstrap(store, elements=elements)

    ids = query_ids(
        repo, PlayerFilter(positions=frozenset({Position.MID}), max_price_m=5.5)
    )

    assert ids == [1]


def test_min_ownership_pct_excludes_below_threshold(store):
    elements = [
        player_payload(id=1, selected_by_percent="3.0"),
        player_payload(id=2, selected_by_percent="15.0"),
    ]
    repo = save_bootstrap(store, elements=elements)

    ids = query_ids(repo, PlayerFilter(min_ownership_pct=10.0))

    assert ids == [2]


def test_statuses_filter_matches_only_given_statuses(store):
    elements = [
        player_payload(id=1, status="a"),
        player_payload(id=2, status="i"),
    ]
    repo = save_bootstrap(store, elements=elements)

    ids = query_ids(repo, PlayerFilter(statuses=frozenset({PlayerStatus.INJURED})))

    assert ids == [2]


def test_teams_filter_matches_short_name(store):
    teams = [team_payload(id=1, short_name="ARS"), team_payload(id=2, short_name="LIV")]
    elements = [player_payload(id=1, team=1), player_payload(id=2, team=2)]
    repo = save_bootstrap(store, elements=elements, teams=teams)

    ids = query_ids(repo, PlayerFilter(teams=frozenset({"ARS"})))

    assert ids == [1]


def test_sort_price_descending_with_limit_ties_broken_by_id(store):
    elements = [
        player_payload(id=1, now_cost=50),
        player_payload(id=2, now_cost=100),
        player_payload(id=3, now_cost=75),
        player_payload(id=4, now_cost=100),
    ]
    repo = save_bootstrap(store, elements=elements)

    ids = query_ids(repo, sort="price", limit=3)

    assert ids == [2, 4, 3]


def test_shortlisted_only_excludes_non_shortlisted(store):
    elements = [
        player_payload(id=1, now_cost=40, selected_by_percent="0.1", penalties_order=1),
        player_payload(id=2, now_cost=40, selected_by_percent="0.1", penalties_order=None),
    ]
    repo = save_bootstrap(store, elements=elements)

    ids = query_ids(repo, PlayerFilter(shortlisted_only=True))

    assert ids == [1]


def test_manager_excluded_even_with_empty_filter(store):
    elements = [
        player_payload(id=1, element_type=3),
        player_payload(id=2, element_type=5, web_name="Boss"),
    ]
    repo = save_bootstrap(store, elements=elements)

    ids = query_ids(repo)

    assert ids == [1]


def test_slim_record_keys_match_players_slim_columns():
    row = PlayerRow(Player.model_validate(player_payload(id=1)), team_short_name="TST")

    assert tuple(slim_record(row).keys()) == PLAYERS_SLIM_COLUMNS
