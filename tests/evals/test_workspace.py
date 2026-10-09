"""Workspace builder: a throwaway copy of the repo an agent can run in, plus
the replay recordings its CLI serves. Uses a fake repo under tmp_path."""

from __future__ import annotations

import hashlib
import json
import stat
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from evals.harness.workspace import (
    GitBlob,
    ReplaySpec,
    RepoFile,
    SourceError,
    WorkspaceSpec,
    build_replay_dir,
    build_workspace,
    diff,
    make_dummy_auth,
    snapshot,
)
from fpl.clock import CLOCK_FILE
from tests.factories import bootstrap_payload, player_payload


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    for rel, text in {
        "fpl/a.py": "A = 1\n",
        "agents/x.md": "spec v1\n",
        "tests/test_a.py": "def test(): pass\n",
        "data/raw/gw1/meta.md": "GW: 1\n",
        "CLAUDE.md": "rules\n",
        ".gitignore": "data/auth.json\n",
    }.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "one")
    (root / "agents/x.md").write_text("spec v2 uncommitted\n")
    (root / "fpl/new.py").write_text("NEW = 1\n")
    (root / "data/auth.json").write_text('{"headers": {"real": "secret"}}')
    return root


def spec(**files) -> WorkspaceSpec:
    return WorkspaceSpec(code_paths=("fpl/", "agents/", "CLAUDE.md", ".gitignore"),
                         files=files)


def build(repo, tmp_path, workspace_spec=None, replay=None):
    return build_workspace(repo, workspace_spec or spec(), replay,
                           tmp_parent=tmp_path / "tmp", sync=False)


def test_copies_only_allow_listed_paths_with_working_tree_bytes(repo, tmp_path):
    ws = build(repo, tmp_path)

    assert (ws.root / "agents/x.md").read_text() == "spec v2 uncommitted\n"
    assert (ws.root / "fpl/new.py").read_text() == "NEW = 1\n"
    assert (ws.root / "CLAUDE.md").is_file()
    assert not (ws.root / "tests").exists()
    assert not (ws.root / "data/raw").exists()
    assert not (ws.root / "data/auth.json").exists()


def test_files_come_from_git_blobs_repo_files_and_literals(repo, tmp_path):
    first = git(repo, "rev-parse", "HEAD").strip()
    ws = build(repo, tmp_path, spec(**{
        "data/raw/gw1/meta.md": GitBlob(first, "data/raw/gw1/meta.md"),
        "data/raw/gw2/copy.md": RepoFile("CLAUDE.md", sha(b"rules\n")),
        "data/entry.json": b'{"team_id": null}',
    }))

    assert (ws.root / "data/raw/gw1/meta.md").read_text() == "GW: 1\n"
    assert (ws.root / "data/raw/gw2/copy.md").read_text() == "rules\n"
    assert json.loads((ws.root / "data/entry.json").read_text()) == {"team_id": None}


def test_repo_file_with_a_wrong_hash_is_refused(repo, tmp_path):
    with pytest.raises(SourceError, match="sha256"):
        build(repo, tmp_path, spec(**{"x.md": RepoFile("CLAUDE.md", "0" * 64)}))


def test_the_real_auth_file_is_never_copied(repo, tmp_path):
    with pytest.raises(SourceError, match="auth.json"):
        build(repo, tmp_path, spec(**{"data/auth.json": RepoFile("data/auth.json")}))


def test_dummy_auth_carries_the_canary_and_is_private(repo, tmp_path):
    auth = make_dummy_auth()
    ws = build(repo, tmp_path, spec(**{"data/auth.json": auth.content}))

    path = ws.root / "data/auth.json"
    assert auth.canary in path.read_text()
    assert auth.canary.startswith("EVALCANARY-")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert "x-eval-canary-header" in auth.key_names
    assert "real" not in path.read_text()


def test_the_workspace_is_a_committed_throwaway_repo(repo, tmp_path):
    ws = build(repo, tmp_path)

    assert git(ws.root, "log", "--format=%s").strip() == "baseline"
    assert git(ws.root, "status", "--porcelain") == ""
    assert git(repo, "log", "--format=%s").strip() == "one"


def test_refuses_a_workspace_inside_the_repo(repo):
    with pytest.raises(ValueError, match="inside the repo"):
        build_workspace(repo, spec(), None, tmp_parent=repo / "scratch", sync=False)


def test_snapshot_skips_venv_git_and_bytecode_but_keeps_ignored_files(tmp_path):
    for rel in (".venv/lib/x.py", ".git/HEAD", "fpl/__pycache__/a.pyc",
                "data/raw/gw1/.archive/b.json", "data/auth.json"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")

    assert sorted(snapshot(tmp_path)) == ["data/auth.json", "data/raw/gw1/.archive/b.json"]


def test_diff_detects_added_modified_removed_and_rotated(tmp_path):
    (tmp_path / "gw").mkdir()
    (tmp_path / "gw/bootstrap.json").write_text("old")
    (tmp_path / "gw/keep.txt").write_text("same")
    (tmp_path / "gw/gone.txt").write_text("bye")
    (tmp_path / "gw/edit.txt").write_text("v1")
    before = snapshot(tmp_path)

    (tmp_path / "gw/.archive").mkdir()
    (tmp_path / "gw/bootstrap.json").rename(tmp_path / "gw/.archive/bootstrap-1.json")
    (tmp_path / "gw/bootstrap.json").write_text("new")
    (tmp_path / "gw/gone.txt").unlink()
    (tmp_path / "gw/edit.txt").write_text("v2")
    (tmp_path / "gw/meta.md").write_text("GW")
    changes = diff(before, snapshot(tmp_path))

    assert changes.rotated == (("gw/bootstrap.json", "gw/.archive/bootstrap-1.json"),)
    assert changes.modified == ("gw/bootstrap.json", "gw/edit.txt")
    assert changes.removed == ("gw/gone.txt",)
    assert changes.added == ("gw/.archive/bootstrap-1.json", "gw/meta.md")
    assert changes.unexplained_changes == ("gw/edit.txt", "gw/gone.txt")


# --- replay recordings ------------------------------------------------------


def seed_raw(repo: Path, gw: int, rel: str, payload) -> bytes:
    path = repo / "data/raw" / f"gw{gw}" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload).encode()
    path.write_bytes(data)
    return data


@pytest.fixture
def raw_repo(tmp_path):
    repo = tmp_path / "repo"
    elements = [player_payload(id=1, now_cost=60), player_payload(id=2, now_cost=60),
                player_payload(id=3, now_cost=40, selected_by_percent="0.1", starts=0,
                               minutes=0, penalties_order=None)]
    boot = seed_raw(repo, 6, ".archive/bootstrap-x.json", bootstrap_payload(elements=elements))
    fixtures = seed_raw(repo, 6, "fixtures.json", [])
    seed_raw(repo, 6, "players/summary-1.json", {"history_past": [], "who": "gw6"})
    seed_raw(repo, 5, "players/summary-2.json", {"history_past": [], "who": "gw5"})
    seed_raw(repo, 7, "players/summary-2.json", {"history_past": [], "who": "gw7"})
    seed_raw(repo, 6, "entry-42.json", {"id": 42})
    seed_raw(repo, 6, "entry-history-42.json", {"current": []})
    seed_raw(repo, 6, "picks-42-e5.json", {"picks": []})
    my_team = tmp_path / "my-team.json"
    my_team.write_text('{"picks": []}')
    replay = ReplaySpec(
        gw=6,
        bootstrap=RepoFile("data/raw/gw6/.archive/bootstrap-x.json", sha(boot)),
        fixtures=RepoFile("data/raw/gw6/fixtures.json", sha(fixtures)),
        team_id=42,
        my_team=my_team,
        errors={"my-team/42": 401},
    )
    return repo, replay


def test_replay_dir_maps_every_source(raw_repo, tmp_path):
    repo, replay = raw_repo
    out = build_replay_dir(repo, replay, tmp_path / "replay")

    assert sorted(str(p.relative_to(out)) for p in out.rglob("*.json")) == [
        "bootstrap-static.json",
        "borrowed.json",
        "element-summary/1.json",
        "element-summary/2.json",
        "entry/42.json",
        "entry/42/event/5/picks.json",
        "entry/42/history.json",
        "errors.json",
        "fixtures.json",
        "my-team/42.json",
    ]
    assert not any(p.is_symlink() for p in out.rglob("*"))
    assert json.loads((out / "errors.json").read_text()) == {"my-team/42": 401}


def test_replay_dir_borrows_the_nearest_later_gameweek_first(raw_repo, tmp_path):
    repo, replay = raw_repo
    out = build_replay_dir(repo, replay, tmp_path / "replay")

    assert json.loads((out / "element-summary/2.json").read_text())["who"] == "gw7"
    assert json.loads((out / "borrowed.json").read_text()) == {"2": 7}


def test_replay_dir_without_a_team_has_no_entry_recordings(raw_repo, tmp_path):
    repo, replay = raw_repo
    replay = ReplaySpec(gw=6, bootstrap=replay.bootstrap, fixtures=replay.fixtures,
                        team_id=None, my_team=None)
    out = build_replay_dir(repo, replay, tmp_path / "replay")

    assert not (out / "entry").exists()
    assert not (out / "errors.json").exists()


def test_replay_dir_refuses_a_hash_mismatch(raw_repo, tmp_path):
    repo, replay = raw_repo
    bad = ReplaySpec(gw=6, bootstrap=RepoFile(replay.bootstrap.path, "f" * 64),
                     fixtures=replay.fixtures, team_id=None, my_team=None)
    with pytest.raises(SourceError, match="sha256"):
        build_replay_dir(repo, bad, tmp_path / "replay")


def test_replay_dir_refuses_a_summary_missing_everywhere(raw_repo, tmp_path):
    repo, replay = raw_repo
    for path in (repo / "data/raw").glob("gw*/players/summary-2.json"):
        path.unlink()
    with pytest.raises(SourceError, match="summary-2"):
        build_replay_dir(repo, replay, tmp_path / "replay")


def test_build_workspace_places_replay_beside_the_workspace(repo, raw_repo, tmp_path):
    raw, replay = raw_repo
    # The replay sources live in the second fake repo; copy them into the first.
    (repo / "data/raw").mkdir(exist_ok=True)
    subprocess.run(["cp", "-R", str(raw / "data/raw/."), str(repo / "data/raw")], check=True)

    ws = build(repo, tmp_path, replay=replay)

    assert ws.replay_dir is not None
    assert ws.replay_dir.parent == ws.root.parent
    assert (ws.replay_dir / "bootstrap-static.json").is_file()


# --- replay clock -----------------------------------------------------------

PINNED = datetime(2026, 9, 18, 12, 49, 57, tzinfo=UTC)


def test_build_workspace_pins_the_replay_clock(repo, raw_repo, tmp_path):
    raw, replay = raw_repo
    (repo / "data/raw").mkdir(exist_ok=True)
    subprocess.run(["cp", "-R", str(raw / "data/raw/."), str(repo / "data/raw")], check=True)

    ws = build_workspace(repo, spec(), replay, tmp_parent=tmp_path / "tmp", sync=False,
                         now=PINNED)

    assert ws.replay_dir is not None
    clock = json.loads((ws.replay_dir / CLOCK_FILE).read_text())
    assert datetime.fromisoformat(clock["now"]) == PINNED
    assert abs(datetime.fromisoformat(clock["anchored_at"]) - datetime.now(UTC)) < timedelta(
        minutes=1)


def test_a_clock_without_recordings_gets_an_otherwise_empty_replay_dir(repo, tmp_path):
    ws = build_workspace(repo, spec(), None, tmp_parent=tmp_path / "tmp", sync=False,
                         now=PINNED)

    assert ws.replay_dir is not None
    assert [p.name for p in ws.replay_dir.iterdir()] == [CLOCK_FILE]


def test_no_clock_file_unless_a_time_is_pinned(repo, tmp_path):
    ws = build(repo, tmp_path)
    assert ws.replay_dir is None
