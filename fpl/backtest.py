"""Backtest harness: re-scores past rounds from exactly what production read
before each deadline.

A round loads only when nothing in it could carry the outcome: every model
input was fetched before the deadline, no element summary holds the round
itself, the actuals are final, and the inputs on disk still match the
round's decision commit.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from fpl import fixture_ratings
from fpl.decision_record import decision_commit, drifted, repo_root
from fpl.ep import FixturesDocument, InputsDocument, load_fixtures, load_inputs
from fpl.models import Bootstrap, ElementSummary, EventLive, PLAYING_POSITIONS, Position
from fpl.service import load_cached_bootstrap, load_cached_summaries
from fpl.store import ARCHIVE_STAMP_FORMAT, SnapshotStore

POSITIONS = (Position.GKP, Position.DEF, Position.MID, Position.FWD)


@dataclass(frozen=True)
class RoundData:
    gw: int
    commit: str | None
    deadline: datetime
    bootstrap: Bootstrap
    summaries: dict[int, ElementSummary]
    fixtures: FixturesDocument
    inputs: dict[Position, InputsDocument]
    live: EventLive
    promoted: frozenset[str]
    warnings: tuple[str, ...] = ()


def load_round(
    *,
    data_root: Path,
    analysis_root: Path,
    actuals_root: Path,
    gw: int,
    decisions_root: Path | None = None,
    drift_check: bool = True,
) -> RoundData:
    """Round `gw` as production saw it before its deadline, with its final
    actuals. Raises ValueError naming the file on any leak, missing or
    non-final actuals, or drift from the decision commit."""
    store = SnapshotStore(data_root)
    bootstrap = load_cached_bootstrap(store, gw)
    deadline = bootstrap.deadline_for(gw)
    if deadline is None:
        raise ValueError(f"gw{gw} bootstrap has no event {gw} deadline")
    round_dir = analysis_root / f"gw{gw}"
    inputs = {pos: load_inputs(round_dir / f"inputs-{pos.name}.json") for pos in POSITIONS}
    fixtures = load_fixtures(round_dir / fixture_ratings.JSON_FILENAME)
    wanted = [p.id for p in bootstrap.elements if p.element_type in PLAYING_POSITIONS]
    wanted += [entry.id for doc in inputs.values() for entry in doc.players]
    summaries = load_cached_summaries(store, gw, wanted)
    promoted = fixture_ratings.load_priors(analysis_root / fixture_ratings.PRIORS_FILENAME).promoted

    _check_summaries_predate(summaries, gw, store)
    names = ["bootstrap", *(["fixtures"] if store.exists(gw, "fixtures") else []),
             *(f"players/summary-{pid}" for pid in summaries)]
    _check_fetched_before(store, gw, names, deadline)
    live = _load_final_actuals(actuals_root, gw)

    warnings: list[str] = []
    commit = None
    if drift_check:
        commit = _check_drift(data_root, analysis_root,
                              decisions_root or analysis_root.parent / "decisions", gw, warnings)
    return RoundData(gw=gw, commit=commit, deadline=deadline, bootstrap=bootstrap,
                     summaries=summaries, fixtures=fixtures, inputs=inputs, live=live,
                     promoted=promoted, warnings=tuple(warnings))


def _check_summaries_predate(summaries: dict[int, ElementSummary], gw: int,
                             store: SnapshotStore) -> None:
    for pid, summary in summaries.items():
        rounds = [row.round for row in summary.history if row.round is not None]
        if rounds and max(rounds) >= gw:
            path = store.path(gw, f"players/summary-{pid}")
            raise ValueError(f"leak: {path} holds round {max(rounds)}, "
                             f"not only rounds before gw{gw}")


def _check_fetched_before(store: SnapshotStore, gw: int, names: list[str],
                          deadline: datetime) -> None:
    for name in names:
        fetched = store.fetched_at(gw, name)
        if fetched is None:
            raise ValueError(f"leak check: {store.path(gw, name)} has no recorded fetch time, "
                             f"so it cannot be shown to predate the gw{gw} deadline "
                             f"{deadline.isoformat()}")
        if fetched >= deadline:
            raise ValueError(f"leak: {store.path(gw, name)} was fetched {fetched.isoformat()}, "
                             f"after the gw{gw} deadline {deadline.isoformat()}")


def _load_final_actuals(actuals_root: Path, gw: int) -> EventLive:
    store = SnapshotStore(actuals_root)
    name = f"event-live-e{gw}"
    path = store.path(gw + 1, name)
    if not path.is_file():
        raise ValueError(f"no actuals for round {gw}: {path} is missing")
    if not _is_final(actuals_root, store, gw):
        raise ValueError(
            f"{path} is not final: its sidecar has no `final` key and no bootstrap of "
            f"gw{gw + 1} or later, fetched at or before it, shows event {gw} data_checked "
            f"— refetch with fpl event-live --gw {gw + 1} --round {gw} --force"
        )
    return EventLive.model_validate(store.load(gw + 1, name))


def _is_final(actuals_root: Path, store: SnapshotStore, gw: int) -> bool:
    name = f"event-live-e{gw}"
    meta = store.dir(gw + 1) / ".meta" / f"{name}.json"
    try:
        if json.loads(meta.read_text(encoding="utf-8")).get("final") is True:
            return True
    except (OSError, ValueError, AttributeError):
        pass
    fetched = store.fetched_at(gw + 1, name)
    if fetched is None:
        return False
    return any(
        seen <= fetched and _shows_checked(path, gw)
        for path, seen in _bootstraps_from(actuals_root, store, gw + 1)
    )


def _bootstraps_from(root: Path, store: SnapshotStore, first_gw: int):
    """Every cached bootstrap of gw ≥ first_gw with its fetch time, archived
    ones included: an archive entry's stamp is the fetch time it was saved with."""
    for directory in sorted(root.glob("gw*")):
        try:
            n = int(directory.name[2:])
        except ValueError:
            continue
        if n < first_gw:
            continue
        current = store.fetched_at(n, "bootstrap")
        if current is not None and store.exists(n, "bootstrap"):
            yield store.path(n, "bootstrap"), current
        for archived in sorted((directory / ".archive").glob("bootstrap-*.json")):
            try:
                stamp = datetime.strptime(archived.stem.removeprefix("bootstrap-"),
                                          ARCHIVE_STAMP_FORMAT).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            yield archived, stamp


def _shows_checked(path: Path, gw: int) -> bool:
    try:
        events = json.loads(path.read_text(encoding="utf-8")).get("events", [])
    except (OSError, ValueError, AttributeError):
        return False
    return any(isinstance(e, dict) and e.get("id") == gw and e.get("data_checked") is True
               for e in events)


def _check_drift(data_root: Path, analysis_root: Path, decisions_root: Path, gw: int,
                 warnings: list[str]) -> str | None:
    try:
        repo = repo_root(analysis_root.resolve())
    except ValueError:
        warnings.append(f"{analysis_root} is not inside a git repository — "
                        f"gw{gw} inputs not checked for drift from the decision commit")
        return None
    sha = decision_commit(repo, gw, _relative(decisions_root, repo) or "data/decisions")
    if sha is None:
        warnings.append(f"gw{gw} has no decision commit — inputs not checked for drift")
        return None
    raw = _relative(data_root / f"gw{gw}", repo)
    analysis = _relative(analysis_root / f"gw{gw}", repo)
    paths = [f"{analysis}/inputs-*.json", f"{analysis}/{fixture_ratings.JSON_FILENAME}"]
    if raw is not None:
        paths += [f"{raw}/bootstrap.json", f"{raw}/fixtures.json", f"{raw}/players"]
    changed = drifted(repo, sha, paths)
    if changed:
        raise ValueError(f"gw{gw} inputs differ from decision commit {sha[:12]}: "
                         + ", ".join(changed)
                         + " — restore them, or pass drift_check=False to score the files on disk")
    return sha


def _relative(path: Path, repo: Path) -> str | None:
    try:
        return str(path.resolve().relative_to(repo))
    except ValueError:
        return None
