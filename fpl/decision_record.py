"""The decision record of a gameweek: what we predicted when we decided.

Prediction files on disk can be rewritten after the decision. The record is
the commit that first adds data/decisions/gw{M}/final.md; a `correct record`
commit only modifies final.md, so it is never chosen.
"""

from __future__ import annotations

import io
import subprocess
import tarfile
from collections.abc import Sequence
from pathlib import Path


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


def repo_root(path: Path) -> Path:
    try:
        top = _git(path, "rev-parse", "--show-toplevel").strip()
    except (OSError, subprocess.CalledProcessError):
        raise ValueError(f"{path} is not inside a git repository — "
                         "pass --predictions-from worktree") from None
    return Path(top).resolve()


def decision_commit(repo: Path, gw: int, decisions_rel: str = "data/decisions") -> str | None:
    shas = _git(repo, "log", "--diff-filter=A", "--format=%H", "--",
                f"{decisions_rel}/gw{gw}/final.md").split()
    return shas[-1] if shas else None


def materialize(repo: Path, commit: str, paths: Sequence[str], dest: Path) -> None:
    """Writes `paths` as they were at `commit` under `dest`, keeping repo-relative paths."""
    archive = subprocess.run(["git", "-C", str(repo), "archive", commit, "--", *paths],
                             check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(dest, filter="data")


def drifted(repo: Path, commit: str, paths: Sequence[str]) -> list[str]:
    """Paths under `paths` whose working-tree state differs from `commit`."""
    return sorted(_git(repo, "diff", "--name-only", commit, "--", *paths).split())
