"""The committed transcript skeletons: the usage CLI must read them exactly as
it reads the real transcripts, and they must carry nothing secret."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pytest

from evals.harness.freeze import redaction_findings
from evals.usage_collector.skeleton import SKELETON_ROOT, skeletonize
from fpl.usage import (
    _SECRET_SHAPES,
    build_report,
    fmt_ts,
    inspect_session,
    list_sessions,
    load_session,
    suggest_window,
    write_report,
)
from tests.test_usage import SID, T0, root  # noqa: F401  (fixture)

REPO = Path(__file__).resolve().parents[2]
GW4_SID = "8cbbfa17-efba-4c69-9b95-2d4a448b3b78"
GW5_SID = "8f06c38d-49f9-43f1-9887-0ebf72e60800"


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def test_skeletonize_keeps_every_number_the_cli_reads(root: Path, tmp_path: Path) -> None:  # noqa: F811
    dst = tmp_path / "skel"
    skeletonize(root, SID, dst)
    end = ts("2026-09-03T22:24:06Z")
    for source, out in ((root, tmp_path / "a"), (dst, tmp_path / "b")):
        write_report(build_report(load_session(source, SID), gw=3, start=ts(T0), end=end), out)
    assert (tmp_path / "a" / "calls.csv").read_bytes() == (tmp_path / "b" / "calls.csv").read_bytes()


def test_skeletonize_drops_text_and_non_commit_commands(root: Path, tmp_path: Path) -> None:  # noqa: F811
    main = root / f"{SID}.jsonl"
    lines = main.read_text().splitlines()
    lines.append(json.dumps({
        "type": "assistant", "timestamp": "2026-09-03T22:30:00Z",
        "message": {"id": "b1", "model": "claude-fable-5-1", "usage": {"output_tokens": 1},
                    "content": [{"type": "text", "text": "secret prose"},
                                {"type": "tool_use", "id": "t1", "name": "Bash",
                                 "input": {"command": "cat data/auth.json", "description": "x"}},
                                {"type": "tool_use", "id": "t2", "name": "Bash",
                                 "input": {"command": "git commit -qm 'gw3: x'"}}]},
    }))
    main.write_text("\n".join(lines) + "\n")
    dst = tmp_path / "skel"
    skeletonize(root, SID, dst)
    text = (dst / f"{SID}.jsonl").read_text()
    assert "secret prose" not in text and "auth.json" not in text
    assert "gw3: x" in text


def test_skeletonize_rewrites_the_home_directory(
    root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,  # noqa: F811
) -> None:
    monkeypatch.setenv("HOME", "/Users/someone")
    main = root / f"{SID}.jsonl"
    main.write_text(main.read_text() + json.dumps({
        "type": "user", "timestamp": "2026-09-03T22:30:00Z",
        "message": {"role": "user", "content": "Read /Users/someone/Dev/x.md and "
                                               "/private/tmp/claude-501/-Users-someone-Dev-x/tasks/a.output"},
    }) + "\n")
    dst = tmp_path / "skel"
    skeletonize(root, SID, dst)
    text = (dst / f"{SID}.jsonl").read_text()
    assert "someone" not in text
    assert "~/Dev/x.md" in text


SKELETON_FILES = sorted(p for p in SKELETON_ROOT.rglob("*") if p.is_file())


@pytest.mark.parametrize("path", SKELETON_FILES, ids=lambda p: p.name)
def test_skeletons_name_no_home_directory(path: Path) -> None:
    home = str(Path.home())
    text = path.read_text("utf-8")
    assert home not in text and home.replace("/", "-") not in text


# Opaque API identifiers, e.g. msg_011CfB7fbAVeYjcXt4sRSf9K, can match the
# case-insensitive JWT shape by chance.
_ID_KEYS = frozenset({"id", "requestId", "toolUseId"})


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            if k not in _ID_KEYS:
                yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def test_skeletons_are_committed() -> None:
    names = {p.name for p in SKELETON_FILES}
    assert {f"{GW4_SID}.jsonl", f"{GW5_SID}.jsonl"} <= names


@pytest.mark.parametrize("path", SKELETON_FILES, ids=lambda p: p.name)
def test_skeletons_carry_no_secrets(path: Path) -> None:
    text = path.read_text("utf-8")
    assert redaction_findings(text) == []
    records = [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == ".jsonl" \
        else [json.loads(text)]
    hits = [s[:40] for record in records for s in _strings(record) if _SECRET_SHAPES.search(s)]
    assert hits == []


def test_skeleton_list_tags_count_only_cycle_spawns() -> None:
    tags = {row.session_id[:8]: row.gw_tags for row in list_sessions(SKELETON_ROOT)}
    assert tags == {GW4_SID[:8]: {4}, GW5_SID[:8]: {5}}


@pytest.mark.parametrize(
    ("sid", "gw", "start", "end"),
    [(GW4_SID, 4, "2026-09-11T17:56:17Z", "2026-09-11T19:00:52Z"),
     (GW5_SID, 5, "2026-09-18T12:47:49Z", "2026-09-18T20:53:35Z")],
)
def test_skeleton_windows(sid: str, gw: int, start: str, end: str) -> None:
    window = suggest_window(load_session(SKELETON_ROOT, sid), gw)
    assert window is not None and (fmt_ts(window.start), fmt_ts(window.end)) == (start, end)


def test_skeleton_gw4_retro_and_ledger_session_has_no_gw4_window() -> None:
    text = inspect_session(load_session(SKELETON_ROOT, GW5_SID), 4)
    assert "suggested window for GW4: none (no GW4 cycle spawn" in text


def test_skeleton_reproduces_the_committed_gw4_ledger() -> None:
    committed = json.loads((REPO / "data/cost/gw4/usage.json").read_text())
    window = committed["window"]
    report = build_report(load_session(SKELETON_ROOT, GW4_SID), gw=4,
                          start=ts(window["start"]), end=ts(window["end"]))
    assert (report.totals.calls, round(report.totals.cost_usd, 2)) == (239, 32.91)
    assert asdict(report.totals) == committed["totals"]
