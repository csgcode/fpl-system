"""The decision record of a gameweek: what we predicted when we decided.

Prediction files on disk can be rewritten after the decision. The record is
the predictions lock `fpl plan` writes next to final.md when it exists, else
the commit that first adds data/decisions/gw{M}/final.md; a `correct record`
commit only modifies final.md, so it is never chosen.
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from fpl.calibrate import PREDICTION_POSITIONS, PlayerPrediction, load_predictions

LOCK_FILENAME = "predictions.lock.json"
LOCK_SCHEMA_VERSION = 1
_PLAYERS_FILES = tuple(f"players-{position.name}.json" for position in PREDICTION_POSITIONS)


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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _lock_document(analysis_dir: Path, gw: int) -> dict | None:
    names = [name for name in _PLAYERS_FILES if (analysis_dir / name).is_file()]
    if not names:
        return None
    rows: dict[str, list] = {}
    for name in names:
        for row in json.loads((analysis_dir / name).read_text(encoding="utf-8")):
            rows[str(row["id"])] = [row["ep_gw"][0], row["p_start"]]
    return {
        "schema_version": LOCK_SCHEMA_VERSION,
        "gw": gw,
        "files": {name: _sha256(analysis_dir / name) for name in sorted(names)},
        "rows": rows,
    }


def write_lock(analysis_dir: Path, lock_path: Path, gw: int) -> list[str]:
    """Locks the gw's prediction files: their sha256 and each row's
    [ep_gw[0], p_start]. Write-once — an existing lock is never replaced.
    Returns warnings; a lock that cannot be built is a warning, not an error."""
    try:
        document = _lock_document(analysis_dir, gw)
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        return [f"players-*.json for gw{gw} unreadable ({exc!r}) — predictions lock not written"]
    if document is None:
        return [f"no players-*.json for gw{gw} — predictions lock not written"]
    if lock_path.exists():
        try:
            locked = json.loads(lock_path.read_text(encoding="utf-8")).get("files")
        except (OSError, ValueError, AttributeError):
            locked = None
        if locked == document["files"]:
            return []
        return [f"predictions lock {lock_path} already exists and differs from the "
                "players-*.json on disk — left unchanged"]
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(document, indent=1) + "\n")
    return []


def _lock_predictions(analysis_dir: Path, lock_path: Path) -> RecordPredictions:
    raw = lock_path.read_bytes()
    try:
        lock = json.loads(raw)
        files: dict[str, str] = lock["files"]
        rows = {int(key): (float(ep), float(p_start))
                for key, (ep, p_start) in lock["rows"].items()}
    except (ValueError, TypeError, KeyError, AttributeError):
        raise ValueError(f"{lock_path} is not a valid predictions lock — "
                         "pass --predictions-from worktree") from None
    if lock.get("schema_version") != LOCK_SCHEMA_VERSION:
        raise ValueError(f"{lock_path} has schema_version {lock.get('schema_version')!r}, "
                         f"expected {LOCK_SCHEMA_VERSION}")
    on_disk = load_predictions(analysis_dir)
    missing = sorted(set(rows) - {prediction.id for prediction in on_disk})
    if missing:
        ids = ", ".join(str(i) for i in missing)
        raise ValueError(
            f"{lock_path} locks player id{'s' if len(missing) > 1 else ''} {ids} "
            "absent from every players-*.json on disk — pass --predictions-from "
            "worktree to calibrate the files on disk"
        )
    changed = {name for name in _PLAYERS_FILES
               if files.get(name) != _sha256(analysis_dir / name)}
    predictions = []
    for prediction in on_disk:
        if f"players-{prediction.position.name}.json" not in changed:
            predictions.append(prediction)
        elif prediction.id in rows:
            ep, p_start = rows[prediction.id]
            predictions.append(PlayerPrediction.model_validate({
                **prediction.model_dump(),
                "ep_gw": (ep, *prediction.ep_gw[1:]),
                "p_start": p_start,
            }))
    source = f"lock {hashlib.sha256(raw).hexdigest()[:12]}"
    return RecordPredictions(tuple(predictions), source,
                             tuple(str(analysis_dir / name) for name in sorted(changed)))


def record_predictions(analysis_root: Path, decisions_root: Path, gw: int) -> RecordPredictions:
    """The gw's predictions as locked by `fpl plan`, else as committed in its
    decision commit, plus the prediction files changed on disk since."""
    lock_path = decisions_root / f"gw{gw}" / LOCK_FILENAME
    if lock_path.is_file():
        return _lock_predictions(analysis_root / f"gw{gw}", lock_path)
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
