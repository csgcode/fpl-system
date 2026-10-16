from __future__ import annotations

import re
import subprocess

from tests.gitrepo import commit_files, init_repo


def _show(repo, sha, path):
    return subprocess.run(["git", "-C", str(repo), "show", f"{sha}:{path}"],
                          capture_output=True, text=True, check=True).stdout


def test_commit_files_returns_the_sha_and_the_file_is_in_the_tree(tmp_path):
    repo = init_repo(tmp_path)

    sha = commit_files(repo, {"a/b.json": "[]"}, "gw3: x")

    assert re.fullmatch(r"[0-9a-f]{40}", sha)
    assert _show(repo, sha, "a/b.json") == "[]"


def test_none_deletes_the_file_in_that_commit(tmp_path):
    repo = init_repo(tmp_path)
    first = commit_files(repo, {"a.txt": "1", "b.txt": b"2"}, "one")

    second = commit_files(repo, {"a.txt": None}, "two")

    tree = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", second],
                          capture_output=True, text=True, check=True).stdout.split()
    assert tree == ["b.txt"]
    assert _show(repo, first, "a.txt") == "1"
