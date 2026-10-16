from __future__ import annotations

import pytest

from fpl.decision_record import decision_commit, drifted, materialize, repo_root
from tests.gitrepo import commit_files, init_repo

MID = "data/analysis/gw6/players-MID.json"
FINAL = "data/decisions/gw6/final.md"


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
