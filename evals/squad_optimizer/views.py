"""Frozen EP views: both readings of one gameweek's analysis, compacted to
what the reference scorer needs, so replay never re-runs old EP code.

Freezing extracts the cycle commit with `git archive`, drops in the pinned
bootstrap, and runs that tree's own `fpl ep` — the code that produced the
numbers the agent saw. The prior-only reading injects a prior_weight 1.0
override into every inputs row, since the old code has no flag for it.
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from evals.harness.workspace import SourceError, read_source
from evals.squad_optimizer.cases import (
    EP_CODE,
    PRE_REOPEN_DEF,
    PRE_REOPEN_ROWS,
    REPO_ROOT,
    ViewSpec,
)
from fpl.models import Bootstrap, Position
from fpl.objective import Row, rows_from_documents

POSITIONS = ("GKP", "DEF", "MID", "FWD")


def load_view(spec: ViewSpec) -> tuple[dict[int, Row], dict[int, Row], dict]:
    """(blend, prior, meta). Raises SourceError when the view is not frozen."""
    if not spec.path.is_file():
        raise SourceError(f"no frozen view {spec.path.name}; run `python -m evals freeze "
                          f"squad-optimizer`")
    document = json.loads(spec.path.read_text(encoding="utf-8"))
    return (_rows(document, "blend"), _rows(document, "prior"), document["meta"])


def _rows(document: dict, reading: str) -> dict[int, Row]:
    rows = {}
    for key, row in document["rows"].items():
        if row.get(reading) is None:
            continue
        rows[int(key)] = Row(
            id=int(key), name=row["name"], position=Position[row["pos"]], club=row["club"],
            price=row["now_cost"], status=row["status"], ep_gw=tuple(row[reading]),
            p_start0=row["p_start0"], uncertainty=row["uncertainty"],
            defcon_share=row["defcon_share"],
        )
    return rows


def compact(meta: dict, bootstrap: Bootstrap, blend_docs: list[dict],
            prior_docs: list[dict]) -> dict:
    blend = rows_from_documents(blend_docs, bootstrap)
    prior = rows_from_documents(prior_docs, bootstrap)
    rows = {}
    for pid in sorted(set(blend) | set(prior)):
        base = blend.get(pid) or prior[pid]
        rows[str(pid)] = {
            "name": base.name, "pos": base.position.name, "club": base.club,
            "now_cost": base.price, "status": base.status,
            "blend": list(blend[pid].ep_gw) if pid in blend else None,
            "prior": list(prior[pid].ep_gw) if pid in prior else None,
            "p_start0": base.p_start0, "uncertainty": base.uncertainty,
            "defcon_share": round(base.defcon_share, 4),
        }
    return {"meta": meta, "rows": rows}


def freeze_view(spec: ViewSpec, repo: Path = REPO_ROOT) -> dict:
    """Builds the compact view; raises SourceError on a missing or drifted
    source and AssertionError when a regenerated blend differs from git."""
    bootstrap_bytes = read_source(repo, spec.bootstrap)
    bootstrap = Bootstrap.model_validate(json.loads(bootstrap_bytes))
    tree = Path(tempfile.mkdtemp(prefix="so-view-"))
    try:
        _extract(repo, spec.commit, tree, ("fpl", f"data/analysis/gw{spec.gw}",
                                           f"data/raw/gw{spec.gw}"))
        raw = tree / "data" / "raw" / f"gw{spec.gw}"
        (raw / "bootstrap.json").write_bytes(bootstrap_bytes)
        analysis = tree / "data" / "analysis" / f"gw{spec.gw}"
        if spec.pre_reopen_def:
            (analysis / "inputs-DEF.json").write_text(
                json.dumps(pre_reopen_inputs(analysis / "inputs-DEF.json")), encoding="utf-8")
        committed = {p: _git_json(repo, spec.commit,
                                  f"data/analysis/gw{spec.gw}/players-{p}.json")
                     for p in POSITIONS}
        if spec.regenerate:
            blend_docs = []
            for position in POSITIONS:
                docs = _run_ep(tree, spec.gw, position, tree / "data" / "analysis",
                               tree / "out" / "blend" / f"players-{position}.json")
                if not spec.pre_reopen_def and committed[position] is not None:
                    assert docs == committed[position], \
                        f"{spec.id}: regenerated players-{position}.json differs from git"
                blend_docs += docs
        else:
            blend_docs = [row for p in POSITIONS for row in committed[p] or []]
        prior_root = tree / "prior"
        (prior_root / f"gw{spec.gw}").mkdir(parents=True)
        shutil.copy(analysis / "fixtures.json", prior_root / f"gw{spec.gw}" / "fixtures.json")
        prior_docs = []
        for position in POSITIONS:
            inputs = json.loads((analysis / f"inputs-{position}.json").read_text("utf-8"))
            prior_inputs(inputs, bootstrap, spec.prior_stubs)
            (prior_root / f"gw{spec.gw}" / f"inputs-{position}.json").write_text(
                json.dumps(inputs), encoding="utf-8")
            prior_docs += _run_ep(tree, spec.gw, position, prior_root,
                                  tree / "out" / "prior" / f"players-{position}.json")
    finally:
        shutil.rmtree(tree, ignore_errors=True)
    meta = {"gw": spec.gw, "view": spec.id, "commit": spec.commit,
            "bootstrap": spec.bootstrap.path,
            "bootstrap_sha256": hashlib.sha256(bootstrap_bytes).hexdigest(),
            "ep_code": EP_CODE, "blend": "regenerated" if spec.regenerate else "git"}
    return compact(meta, bootstrap, blend_docs, prior_docs)


def pre_reopen_inputs(current: Path) -> dict:
    """The DEF inputs as they stood before the GW5 REOPEN: the player-analyst
    fixture when present, else the commit's file with the five rows reset."""
    if PRE_REOPEN_DEF.is_file():
        return json.loads(PRE_REOPEN_DEF.read_text(encoding="utf-8"))
    document = json.loads(current.read_text(encoding="utf-8"))
    for row in document["players"]:
        if row.get("name") in PRE_REOPEN_ROWS:
            p0, vector = PRE_REOPEN_ROWS[row["name"]]
            row["p_start"], row["p_start_gw"] = p0, list(vector)
    return document


def prior_inputs(inputs: dict, bootstrap: Bootstrap, stubs: tuple[int, ...]) -> None:
    position = Position[inputs["position"]] if isinstance(inputs["position"], str) \
        else Position(inputs["position"])
    for row in inputs["players"]:
        overrides = dict(row.get("overrides") or {})
        overrides["prior_weight"] = 1.0
        row["overrides"] = overrides
        row.setdefault("reason", "prior-only reading")
        if not row["reason"]:
            row["reason"] = "prior-only reading"
    by_id = bootstrap.player_by_id()
    for stub in stubs:
        player = by_id[stub]
        if player.element_type == position:
            inputs["players"].append({
                "id": stub, "p_start": 0.0, "uncertainty": "HIGH", "notes": "eval stub",
                "overrides": {"prior_weight": 1.0}, "reason": "prior-only reading"})


def _run_ep(tree: Path, gw: int, position: str, analysis_root: Path, out: Path) -> list[dict]:
    out.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [sys.executable, "-m", "fpl", "ep", "--gw", str(gw), "--position", position,
         "--analysis-root", str(analysis_root), "--out", str(out), "--format", "json",
         "--limit", "0", "--history-from", "summaries"],
        cwd=tree, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise SourceError(f"fpl ep {position} at {tree} failed: {completed.stderr.strip()[-400:]}")
    return json.loads(out.read_text(encoding="utf-8"))


def _extract(repo: Path, commit: str, dest: Path, paths: tuple[str, ...]) -> None:
    archived = subprocess.run(["git", "-C", str(repo), "archive", commit, *paths],
                              capture_output=True, check=False)
    if archived.returncode != 0:
        raise SourceError(f"git archive {commit} failed: {archived.stderr.decode()[-300:]}")
    with tarfile.open(fileobj=io.BytesIO(archived.stdout)) as tar:
        tar.extractall(dest, filter="data")


def _git_json(repo: Path, commit: str, path: str) -> list[dict] | None:
    shown = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"],
                           capture_output=True, check=False)
    return json.loads(shown.stdout) if shown.returncode == 0 else None
