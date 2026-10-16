from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest

from fpl.decision_record import (
    LOCK_FILENAME,
    decision_commit,
    drifted,
    materialize,
    repo_root,
    write_lock,
)
from tests.gitrepo import commit_files, init_repo

MID = "data/analysis/gw6/players-MID.json"
FINAL = "data/decisions/gw6/final.md"
DEADLINE = datetime(2026, 8, 22, 12, 0, tzinfo=UTC)


def before_deadline():
    return DEADLINE - timedelta(hours=1)


def lock(analysis_dir, lock_path, gw, *, now=before_deadline):
    return write_lock(analysis_dir, lock_path, gw, deadline=DEADLINE, now=now)


@pytest.fixture
def history(tmp_path):
    repo = init_repo(tmp_path / "repo")
    commit_files(repo, {MID: '[{"v": 1}]'}, "gw6: progress")
    decision = commit_files(repo, {MID: '[{"v": 2}]', FINAL: "decided"}, "gw6: decision")
    commit_files(repo, {MID: '[{"v": 3}]'}, "ep: rewrite")
    commit_files(repo, {MID: '[{"v": 4}]', FINAL: "corrected"}, "gw6: correct record — x")
    return repo, decision


def test_decision_commit_is_the_commit_that_adds_final_md(history):
    repo, decision = history
    assert decision_commit(repo, 6) == decision


def test_decision_commit_is_none_for_an_undecided_gameweek(history):
    repo, _ = history
    assert decision_commit(repo, 7) is None


def test_predictions_without_final_md_have_no_decision_commit(tmp_path):
    repo = init_repo(tmp_path / "repo")
    commit_files(repo, {MID: "[]"}, "gw6: progress")
    assert decision_commit(repo, 6) is None


def test_decision_commit_looks_under_the_given_decisions_path(tmp_path):
    repo = init_repo(tmp_path / "repo")
    commit_files(repo, {FINAL: "decided"}, "gw6: decision")
    elsewhere = commit_files(repo, {"elsewhere/decisions/gw6/final.md": "x"}, "other")

    assert decision_commit(repo, 6, decisions_rel="elsewhere/decisions") == elsewhere


def test_repo_root_resolves_from_a_subdirectory(history):
    repo, _ = history
    assert repo_root(repo / "data" / "analysis") == repo.resolve()


def test_repo_root_outside_git_names_the_worktree_flag(tmp_path):
    with pytest.raises(ValueError, match="--predictions-from worktree"):
        repo_root(tmp_path)


def test_materialize_writes_the_commit_version(history, tmp_path):
    repo, decision = history
    dest = tmp_path / "out"

    materialize(repo, decision, ["data/analysis/gw6"], dest)

    assert (dest / MID).read_text() == '[{"v": 2}]'
    assert (repo / MID).read_text() == '[{"v": 4}]'


def test_drifted_names_changed_and_deleted_paths(tmp_path):
    repo = init_repo(tmp_path / "repo")
    gk = "data/analysis/gw6/players-GKP.json"
    fwd = "data/analysis/gw6/players-FWD.json"
    decision = commit_files(repo, {MID: "[1]", gk: "[2]", fwd: "[3]", FINAL: "d"}, "gw6: decision")
    (repo / MID).write_text("[9]")
    (repo / gk).unlink()

    assert drifted(repo, decision, ["data/analysis/gw6"]) == sorted([MID, gk])


def test_nothing_drifts_when_the_tree_matches_the_commit(history):
    repo, _ = history
    head = commit_files(repo, {}, "empty")
    assert drifted(repo, head, ["data/analysis/gw6"]) == []


# --- the predictions lock ---------------------------------------------------


def seed_players(analysis_dir, rows_by_position):
    analysis_dir.mkdir(parents=True, exist_ok=True)
    for position, rows in rows_by_position.items():
        (analysis_dir / f"players-{position}.json").write_text(json.dumps(rows), encoding="utf-8")


def players_row(id, ep, p_start):
    return {"id": id, "name": f"P{id}", "ep_gw": [ep, 1.0], "p_start": p_start}


def test_write_lock_records_hashes_and_rows(tmp_path):
    analysis_dir = tmp_path / "analysis" / "gw2"
    seed_players(analysis_dir, {"MID": [players_row(1, 3.0, 0.9)],
                                "FWD": [players_row(2, 4.25, 0.5)]})
    lock_path = tmp_path / "decisions" / "gw2" / LOCK_FILENAME

    assert lock(analysis_dir, lock_path, 2) == []

    def digest(name):
        return hashlib.sha256((analysis_dir / name).read_bytes()).hexdigest()

    assert json.loads(lock_path.read_text(encoding="utf-8")) == {
        "schema_version": 1,
        "gw": 2,
        "files": {"players-FWD.json": digest("players-FWD.json"),
                  "players-MID.json": digest("players-MID.json")},
        "rows": {"1": [3.0, 0.9], "2": [4.25, 0.5]},
    }


def test_write_lock_is_write_once(tmp_path):
    analysis_dir = tmp_path / "analysis" / "gw2"
    seed_players(analysis_dir, {"MID": [players_row(1, 3.0, 0.9)]})
    lock_path = tmp_path / "decisions" / "gw2" / LOCK_FILENAME
    lock(analysis_dir, lock_path, 2)
    first = lock_path.read_bytes()

    assert lock(analysis_dir, lock_path, 2) == []

    seed_players(analysis_dir, {"MID": [players_row(1, 5.0, 0.9)]})
    warnings = lock(analysis_dir, lock_path, 2)

    assert lock_path.read_bytes() == first
    assert len(warnings) == 1 and str(lock_path) in warnings[0]


def test_write_lock_without_players_files_writes_nothing(tmp_path):
    lock_path = tmp_path / "decisions" / "gw2" / LOCK_FILENAME

    warnings = lock(tmp_path / "analysis" / "gw2", lock_path, 2)

    assert warnings == ["no players-*.json for gw2 — predictions lock not written"]
    assert not lock_path.exists()


@pytest.mark.parametrize("now", [DEADLINE, DEADLINE + timedelta(days=30)])
def test_write_lock_after_the_deadline_writes_nothing(tmp_path, now):
    analysis_dir = tmp_path / "analysis" / "gw2"
    seed_players(analysis_dir, {"MID": [players_row(1, 3.0, 0.9)]})
    lock_path = tmp_path / "decisions" / "gw2" / LOCK_FILENAME

    warnings = lock(analysis_dir, lock_path, 2, now=lambda: now)

    assert warnings == ["gw2 deadline passed — predictions lock not written"]
    assert not lock_path.exists()
