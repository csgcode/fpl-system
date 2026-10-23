"""Gate records: the written-once outcome of each backtest gate, the
manifest that orders them, and their renderings — the one-line summary
and the table kept between the markers in docs/ep-model.md."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from fpl.store import ARCHIVE_STAMP_FORMAT

SCHEMA_VERSION = 1
GATES_ROOT = Path("data/model/gates")
EP_MODEL_DOC = Path("docs/ep-model.md")
MANIFEST = "manifest.toml"
COMBINED = "combined"
BASELINE = "baseline"
ARCHIVE_DIR = "archive"
BLOCK_BEGIN = "<!-- gates:begin -->"
BLOCK_END = "<!-- gates:end -->"
NAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.-]*$"
RESERVED_NAMES = frozenset({COMBINED, "manifest"})

Kind = Literal["model", "policy", "calibration", "persistence", "combined"]
EntryKind = Literal["model", "policy", "calibration", "persistence"]


def signed(value: float, digits: int) -> str:
    """`value` to `digits` places with an explicit sign, minus as U+2212."""
    return f"{value:+.{digits}f}".replace("-", "−")


def value_text(value: float | bool | None) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return str(value).lower()
    return f"{value:g}"


def overrides_text(overrides: Mapping[str, Any]) -> str:
    return ",".join(f"{key}={value_text(value)}" for key, value in overrides.items())


class GateRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    name: str = Field(pattern=NAME_PATTERN)
    kind: Kind
    argv: tuple[str, ...]
    rounds: tuple[int, ...]
    data: dict[str, Any]
    decision_commits: dict[str, str | None] | None
    code: dict[str, Any]
    baseline_config: dict[str, Any] | None
    grid: dict[str, list[Any]] | None
    picks: dict[str, dict[str, Any]] | None
    ship_value: dict[str, Any] | None
    comparison: dict[str, Any] | None
    verdict: Literal["PASS", "FAIL"] | None
    reasons: tuple[str, ...]
    recorded_at: str
    baseline: dict[str, Any] | None = None
    round_checks: dict[str, Any] | None = None
    slice_verdict: str | None = None
    hypothesis: str | None = None
    shipped_config: dict[str, Any] | None = None
    reverted: tuple[str, ...] | None = None
    significant: bool | None = None
    predictions_commits: dict[str, str | None] | None = None

    @model_validator(mode="after")
    def _fields_match_kind(self) -> GateRecord:
        """A persistence record reads ledgers, so it names each ledger's
        predictions commit and judges no config; every other kind judges a
        config on rounds with decision commits."""
        if self.kind == "persistence":
            if self.decision_commits is not None:
                raise ValueError("a persistence record has predictions_commits, "
                                 "not decision_commits")
            return self
        if self.baseline_config is None:
            raise ValueError(f"a {self.kind} record needs baseline_config")
        if self.decision_commits is None:
            raise ValueError(f"a {self.kind} record needs decision_commits")
        if self.significant is not None:
            raise ValueError("significant belongs to a persistence record only")
        if self.predictions_commits is not None:
            raise ValueError("predictions_commits belong to a persistence record only")
        return self


class ManifestEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(pattern=NAME_PATTERN)
    kind: EntryKind
    argv: tuple[str, ...]


class _Manifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    gate: tuple[ManifestEntry, ...] = Field(min_length=1)


def check_name(name: str) -> str:
    if re.fullmatch(NAME_PATTERN, name) is None:
        raise ValueError(f"gate name {name!r}: use letters, digits, '_', '.' or '-'")
    if name in RESERVED_NAMES:
        raise ValueError(f"gate name {name!r} is reserved")
    return name


def record_path(root: Path, name: str) -> Path:
    return root / f"{name}.json"


def read_record(root: Path, name: str) -> GateRecord | None:
    path = record_path(root, name)
    return _load(path) if path.is_file() else None


def load_records(root: Path) -> list[GateRecord]:
    """Every record directly under `root`: manifest entries in manifest
    order, then records the manifest does not name by recording time, then
    `combined`. Ordering by time alone is ambiguous — stamps have one-second
    resolution and a whole manifest run can share one."""
    if not root.is_dir():
        return []
    records = [_load(path) for path in sorted(root.glob("*.json"))]
    manifest = root / MANIFEST
    order = ({entry.name: i for i, entry in enumerate(load_manifest(manifest))}
             if manifest.is_file() else {})
    return sorted(records, key=lambda record: (record.kind == "combined",
                                               order.get(record.name, len(order)),
                                               record.recorded_at, record.name))


def _load(path: Path) -> GateRecord:
    try:
        return GateRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from None
    except ValidationError as exc:
        first = exc.errors()[0]
        raise ValueError(f"{path}: {first.get('loc')} {first.get('msg')}") from None


def write_record(root: Path, record: Mapping[str, Any], *, force: bool,
                 archive_unchanged: bool = True,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> Path:
    """Writes the record once. With `force`, an existing record moves to
    archive/<name>.<UTC stamp>.json first — unless `archive_unchanged` is
    False and the two differ only in `code` and `recorded_at`, when the old
    one is simply replaced."""
    parsed = GateRecord.model_validate(record)
    path = record_path(root, parsed.name)
    if path.exists():
        if not force:
            raise ValueError(f"{path} exists — gate records are written once; "
                             "pass --force to archive it and record again")
        if archive_unchanged or _content(_load(path)) != _content(parsed):
            archive = root / ARCHIVE_DIR
            archive.mkdir(parents=True, exist_ok=True)
            path.rename(archive / f"{parsed.name}.{now().strftime(ARCHIVE_STAMP_FORMAT)}.json")
    root.mkdir(parents=True, exist_ok=True)
    document = parsed.model_dump(mode="json", exclude_unset=True)
    path.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _content(record: GateRecord) -> dict[str, Any]:
    return record.model_dump(mode="json", exclude={"code", "recorded_at"})


def load_manifest(path: Path) -> list[ManifestEntry]:
    """The manifest's `[[gate]]` entries in order. The first is `baseline`
    with no arguments; names are unique and none is reserved."""
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"cannot read manifest {path}: {exc.strerror}") from None
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"{path} is not valid TOML: {exc}") from None
    try:
        entries = list(_Manifest.model_validate(document).gate)
    except ValidationError as exc:
        first = exc.errors()[0]
        raise ValueError(f"{path}: {first.get('loc')} {first.get('msg')}") from None
    names = [entry.name for entry in entries]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"{path}: duplicate gate name(s) {', '.join(duplicates)}")
    for name in names:
        if name in RESERVED_NAMES:
            raise ValueError(f"{path}: gate name {name!r} is reserved")
    first = entries[0]
    if first.name != BASELINE or first.argv:
        raise ValueError(f"{path}: the first entry must be "
                         f'name = "{BASELINE}" with argv = []')
    return entries


def summary_lines(records: Sequence[GateRecord]) -> list[str]:
    """Two lines per record: the result, then its status."""
    combined = next((r for r in records if r.kind == "combined"), None)
    reverted = set(combined.reverted or ()) if combined else set()
    out: list[str] = []
    for record in records:
        out.append(_headline(record))
        out.append(f"  {_status(record, reverted)}{_slice_suffix(record)}")
    return out


def _slice_suffix(record: GateRecord) -> str:
    suffix = ""
    if record.slice_verdict is not None:
        suffix += f" · {_slice_text(record)}"
    if record.hypothesis is not None:
        suffix += f" · hypothesis {record.hypothesis}"
    return suffix


def _slice_text(record: GateRecord) -> str:
    """The slice gate's verdict with its n, ΔMAE, CI and bias, baseline to
    variant; the verdict alone when the record holds no slice statistics."""
    g = (record.comparison or {}).get("slice_gate")
    if not g:
        return f"slice {record.slice_verdict}"
    text = f"slice {g['name']} {g['verdict']}: n {g['n']}"
    if g["delta_mae"] is None:
        return text
    lo, hi = g["ci"]
    return (f"{text}, ΔMAE {signed(g['delta_mae'], 4)} [CI {signed(lo, 3)}, {signed(hi, 3)}], "
            f"bias {signed(g['baseline_bias'], 3)}→{signed(g['variant_bias'], 3)}")


def _ship_cell(record: GateRecord) -> str:
    """A FAIL entry's sweep pick is not shipped, so only a PASS shows one."""
    ship = overrides_text(record.ship_value or {})
    if record.kind == "combined" and not ship:
        return ("ships baseline (no passing entries)" if not record.reverted
                else "ships baseline (passing entries reverted)")
    if record.verdict == "FAIL":
        return "—"
    return ship or "—"


def _headline(record: GateRecord) -> str:
    c = _gate_comparison(record)
    if record.kind == "calibration":
        return f"{record.name}: calibration — {_p4_text(record)}"
    if record.kind == "persistence":
        window = _persistence_windows(record)[0]
        return (f"{record.name}: {_significance(record)} — window {window['window']}, "
                f"min starts {window['min_starts']}: "
                f"{_window_text(window, ci_label='CI ', ci_suffix=' (cluster)')}")
    if c is None:
        if record.kind == "combined":
            return f"{record.name}: no passing entries — ships the baseline config"
        return f"{record.name}: reference — {_aggregate_text(record)}"
    if record.kind == "policy":
        result = "passed (a policy never ships)" if record.verdict == "PASS" else "FAIL policy"
    else:
        ship = overrides_text(record.ship_value or {}) or "baseline"
        word = "ship" if record.verdict == "PASS" else "tried"
        result = f"{record.verdict} {word} {ship}"
    wins, rounds = c["round_wins"]
    return (f"{record.name}: {result} — ΔMAE {signed(c['delta_mae'], 4)} "
            f"[CI {signed(c['ci'][0], 3)}, {signed(c['ci'][1], 3)}], "
            f"bias {_plain(c['baseline']['bias'], 2)}→{_plain(c['variant']['bias'], 2)}, "
            f"wins {wins}/{rounds}")


def _status(record: GateRecord, reverted: set[str]) -> str:
    if record.kind == "combined":
        shipped = overrides_text(record.ship_value or {}) or "baseline"
        return f"shipped_config {shipped}; reverted {', '.join(record.reverted or ()) or 'none'}"
    if record.kind == "calibration":
        return "calibration"
    if record.kind == "persistence":
        if record.significant:
            return "significant: the form term goes to its gate"
        return "no form term: " + "; ".join(_reason_text(reason) for reason in record.reasons)
    if record.verdict is None:
        return "reference"
    if record.verdict == "FAIL":
        return "rejected: " + "; ".join(_reason_text(reason) for reason in record.reasons)
    if record.kind == "policy":
        return "passed (a policy never ships)"
    if record.name in reverted:
        return "reverted: dropped from combined"
    return "shipped"


def _gate_comparison(record: GateRecord) -> dict[str, Any] | None:
    """The record's gate statistics; None when it holds none, as for a
    combined record that ships the baseline and carries only its p4."""
    c = record.comparison
    return c if c is not None and "round_wins" in c else None


def _reason_text(reason: str) -> str:
    key, sep, text = reason.partition(": ")
    return f"{text} ({key})" if sep else reason


def _aggregate_text(record: GateRecord) -> str:
    aggregate = (record.baseline or {}).get("aggregate")
    if not aggregate:
        return "no aggregate recorded"
    return (f"n {aggregate['n']}, bias {signed(aggregate['bias'], 3)}, "
            f"MAE {aggregate['mae']:.3f}")


def _p4_text(record: GateRecord) -> str:
    p4 = (record.comparison or {}).get("p4")
    if not p4:
        return "no p4 recorded"
    return "p4 skill " + "; ".join(
        f"{pos} {_p4_scores(v)}" + _starters_suffix(v, _p4_scores) for pos, v in p4.items())


def _p4_scores(v: Mapping[str, Any]) -> str:
    return (f"n {v['n']} Brier {v['p4_brier']:.3f} v base {_optional(v['base_rate_brier'])} "
            f"skill {_optional_signed(v['skill'])}")


def _starters_suffix(v: Mapping[str, Any], text: Callable[[Mapping[str, Any]], str]) -> str:
    """Records written before the starter subset carry no `starters` key and
    print nothing for it; a recorded None means no line was a likely starter."""
    if "starters" not in v:
        return ""
    starters = v["starters"]
    return " (starters none)" if starters is None else f" (starters {text(starters)})"


def _p4_skills(record: GateRecord) -> str:
    """Starter skill to 4 places: it decides P4_CALIBRATED by its sign, and
    a value such as −0.0001 must not print as −0.000."""
    p4 = (record.comparison or {}).get("p4") or {}
    return "p4 skill " + (", ".join(
        f"{pos} {_optional_signed(v['skill'])}"
        + _starters_suffix(v, lambda s: _optional_signed(s["skill"], 4))
        for pos, v in p4.items()) or "none recorded")


def _optional(value: float | None) -> str:
    return "-" if value is None else f"{value:.3f}"


def _optional_signed(value: float | None, digits: int = 3) -> str:
    return "-" if value is None else signed(value, digits)


def _significance(record: GateRecord) -> str:
    return "significant" if record.significant else "not significant"


def _persistence_windows(record: GateRecord) -> list[dict[str, Any]]:
    """The recorded windows, the main window first."""
    return list((record.comparison or {}).get("windows") or [])


def _window_text(window: Mapping[str, Any], *, ci_label: str = "", ci_suffix: str = "") -> str:
    if window["slope"] is None or window["ci_cluster"] is None:
        slope = "slope n/a"
    else:
        lo, hi = window["ci_cluster"]
        slope = (f"slope {signed(window['slope'], 3)} "
                 f"[{ci_label}{signed(lo, 3)}, {signed(hi, 3)}]{ci_suffix}")
    r = "n/a" if window["r"] is None else signed(window["r"], 3)
    return f"n {window['n']}, {slope}, r {r}"


def _plain(value: float, digits: int) -> str:
    return f"{value:.{digits}f}".replace("-", "−")


RENDER_HEADER = ("Gate", "Kind", "Rounds", "Grid", "Ship value", "ΔMAE", "CI", "Bias", "Wins",
                 "Verdict", "Reasons")


def render(records: Sequence[GateRecord]) -> str:
    """The markdown table kept between the gate markers, one row per record."""
    if not records:
        return ""
    rows = [RENDER_HEADER, tuple("---" for _ in RENDER_HEADER)]
    rows += [_render_row(record) for record in records]
    return "\n".join("| " + " | ".join(row) + " |" for row in rows)


def _render_row(record: GateRecord) -> tuple[str, ...]:
    c = _gate_comparison(record)
    rounds = record.rounds
    span = str(rounds[0]) if len(rounds) == 1 else f"{rounds[0]}-{rounds[-1]}"
    grid = "; ".join(f"{key}=" + ",".join(value_text(v) for v in values)
                     for key, values in (record.grid or {}).items()) or "—"
    ship = _ship_cell(record)
    reasons = list(record.reasons)
    if record.kind == "combined" and record.reverted:
        reasons.append("reverted: " + ", ".join(record.reverted))
    if record.kind == "calibration":
        return (record.name, record.kind, span, grid, ship, "—", "—", "—", "—",
                record.verdict or "—", _p4_skills(record))
    if record.kind == "persistence":
        windows = "; ".join(f"window {w['window']}: {_window_text(w)}"
                            for w in _persistence_windows(record))
        return (record.name, record.kind, span, grid, ship, "—", "—", "—", "—",
                _significance(record), windows or "—")
    if c is None:
        if record.kind != "combined":
            reasons.append(f"reference: {_aggregate_text(record)}")
        return (record.name, record.kind, span, grid, ship, "—", "—", "—", "—",
                record.verdict or "—", "; ".join(reasons) or "—")
    wins, total = c["round_wins"]
    return (
        record.name, record.kind, span, grid, ship, signed(c["delta_mae"], 4),
        f"[{signed(c['ci'][0], 3)}, {signed(c['ci'][1], 3)}]",
        f"{signed(c['baseline']['bias'], 3)}→{signed(c['variant']['bias'], 3)}",
        f"{wins}/{total}", (record.verdict or "—") + _slice_suffix(record),
        "; ".join(reasons) or "—",
    )


def _markers(text: str) -> tuple[int, int]:
    begin = text.find(BLOCK_BEGIN)
    end = text.find(BLOCK_END)
    if begin < 0 or end < 0 or end < begin:
        raise ValueError(f"no {BLOCK_BEGIN} … {BLOCK_END} block in the document")
    return begin + len(BLOCK_BEGIN), end


def block(text: str) -> str:
    """The text between the gate markers."""
    start, end = _markers(text)
    return text[start:end]


def replace_block(text: str, rendered: str) -> str:
    start, end = _markers(text)
    return text[:start] + "\n" + (rendered + "\n" if rendered else "") + text[end:]


def register(add: Callable[..., argparse.ArgumentParser]) -> None:
    p = add("gates", "summarise the backtest gate records or render them into the docs",
            cached=False)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--render", action="store_true",
                      help="rewrite the table between the gate markers in --doc")
    mode.add_argument("--summary", action="store_true",
                      help="print each record's result and status")
    p.add_argument("--gates-root", type=Path, default=GATES_ROOT,
                   help="where the gate records live")
    p.add_argument("--doc", type=Path, default=EP_MODEL_DOC,
                   help="the document holding the gate markers")


def run(args: argparse.Namespace) -> int:
    records = load_records(args.gates_root)
    if args.summary:
        if not records:
            print(f"no gate records under {args.gates_root}")
            return 0
        for line in summary_lines(records):
            print(line)
        return 0
    try:
        text = args.doc.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {args.doc}: {exc.strerror}") from None
    try:
        updated = replace_block(text, render(records))
    except ValueError as exc:
        raise ValueError(f"{args.doc}: {exc}") from None
    if updated == text:
        print(f"{args.doc}: gate table unchanged")
        return 0
    args.doc.write_text(updated, encoding="utf-8")
    print(f"wrote the gate table into {args.doc} ({len(records)} record(s))")
    return 0
