"""The suite-wide guard in tests/conftest.py: no test may change the repo's
real data/ tree, which holds the live season's snapshots, decisions and
executor audit records."""

from __future__ import annotations

import json
import os

import pytest

from fpl.__main__ import main
from fpl.write import SessionExpiredError
from tests import conftest
from tests.conftest import REPO_DATA, RepoDataWriteError

PROBE = REPO_DATA / "executor" / "gw99" / "guard-probe.json"


class ExpiredSession:
    def get_json(self, url):
        raise SessionExpiredError()

    def post_json(self, url, payload):
        raise AssertionError("no POST expected")


@pytest.fixture
def forgive_violations():
    yield
    conftest.violations.clear()


def test_opening_a_repo_data_file_for_writing_is_refused(forgive_violations):
    with pytest.raises(RepoDataWriteError):
        PROBE.write_text("{}")
    assert not PROBE.exists()


def test_creating_a_repo_data_directory_is_refused(forgive_violations):
    with pytest.raises(RepoDataWriteError):
        PROBE.parent.mkdir(parents=True)
    assert not PROBE.parent.exists()


def test_a_relative_path_is_resolved_against_the_working_directory(
    forgive_violations, monkeypatch
):
    monkeypatch.chdir(REPO_DATA.parent)
    with pytest.raises(RepoDataWriteError):
        with open("data/executor/gw99/guard-probe.json", "a"):
            pass


def test_reading_repo_data_is_allowed():
    with open(REPO_DATA / "entry.json", encoding="utf-8") as handle:
        assert "team_id" in json.load(handle)


def test_writing_elsewhere_is_allowed(tmp_path):
    (tmp_path / "data" / "executor").mkdir(parents=True)
    (tmp_path / "data" / "executor" / "runs.jsonl").write_text("{}\n")


def test_a_write_command_left_on_the_default_executor_root_is_caught(
    forgive_violations, monkeypatch, tmp_path
):
    """The leak this guard exists for: a CLI test that omits --executor-root
    while the working directory is the repo root appends its run-log row to
    the real data/executor/gw{N}/runs.jsonl."""
    monkeypatch.chdir(REPO_DATA.parent)
    auth = tmp_path / "auth.json"
    auth.write_text(json.dumps({"headers": {"x-api-authorization": "Bearer x"}}))
    with pytest.raises(RepoDataWriteError):
        main(
            ["--data-root", str(tmp_path / "raw"), "auth-check", "--gw", "38",
             "--team-id", "42", "--auth", str(auth)],
            write_gateway_factory=lambda credentials: ExpiredSession(),
        )
    assert not (REPO_DATA / "executor" / "gw38").exists()
    assert os.getcwd() == str(REPO_DATA.parent)


def test_removing_a_tmp_tree_that_holds_a_data_directory_is_allowed(tmp_path):
    import shutil

    tree = tmp_path / "ws"
    (tree / "data" / "executor").mkdir(parents=True)
    (tree / "data" / "executor" / "runs.jsonl").write_text("{}\n")
    shutil.rmtree(tree)
    assert not tree.exists()
