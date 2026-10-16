"""Throwaway git repositories for tests. The user's and system git config never
apply, so commits are reproducible and unsigned on any machine."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_CONFIG = ("-c", "user.name=test", "-c", "user.email=test@localhost",
           "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main")
_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *_CONFIG, "-C", str(repo), *args], check=True,
                          capture_output=True, text=True, env=_ENV).stdout


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    return path


def commit_files(repo: Path, files: dict[str, str | bytes | None], message: str) -> str:
    """Writes each file (None deletes it), commits them all, returns the sha."""
    for name, content in files.items():
        target = repo / name
        if content is None:
            _git(repo, "rm", "-q", "--", name)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
        _git(repo, "add", "--", name)
    _git(repo, "commit", "-q", "--allow-empty", "-m", message)
    return _git(repo, "rev-parse", "HEAD").strip()
