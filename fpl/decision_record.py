"""The decision record of a gameweek: what we predicted when we decided.

Prediction files on disk can be rewritten after the decision. The record is
the commit that first adds data/decisions/gw{M}/final.md; a `correct record`
commit only modifies final.md, so it is never chosen.
"""

from __future__ import annotations

import io
import subprocess
import tarfile
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from fpl.calibrate import PlayerPrediction, load_predictions


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


@dataclass(frozen=True)
class RecordPredictions:
    predictions: tuple[PlayerPrediction, ...]
    source: str
    drifted: tuple[str, ...]


def record_predictions(analysis_root: Path, decisions_root: Path, gw: int) -> RecordPredictions:
    """The gw's predictions as committed in its decision commit, plus the
    prediction files changed on disk since."""
    repo = repo_root(analysis_root.resolve())
    rel = str((analysis_root.resolve() / f"gw{gw}").relative_to(repo))
    decisions_rel = str(decisions_root.resolve().relative_to(repo))
    sha = decision_commit(repo, gw, decisions_rel=decisions_rel)
    if sha is None:
        raise ValueError(
            f"gw{gw} has no decision commit (no commit adds {decisions_rel}/gw{gw}/final.md) "
            "— pass --predictions-from worktree to calibrate the files on disk"
        )
    with tempfile.TemporaryDirectory() as tmp:
        materialize(repo, sha, [rel], Path(tmp))
        predictions = load_predictions(Path(tmp) / rel)
    return RecordPredictions(predictions, f"commit {sha[:12]}",
                             tuple(drifted(repo, sha, [rel])))
