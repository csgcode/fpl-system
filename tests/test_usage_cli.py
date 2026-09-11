"""CLI tests for `usage`: local-only, so the gateway explodes if anything
reaches for the network."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fpl.__main__ import main
from fpl.api import FplApi
from fpl.service import FplDataService
from fpl.store import SnapshotStore
from tests.test_usage import SID, T0, root  # noqa: F401  (fixture)


class NoNetworkGateway:
    def get_json(self, url: str):
        raise AssertionError(f"usage must not touch the network, but fetched {url}")


def run(argv, tmp_path):
    def factory(store: SnapshotStore) -> FplDataService:
        return FplDataService(FplApi(NoNetworkGateway()), store)

    return main(["--data-root", str(tmp_path / "raw"), *argv], service_factory=factory)


def test_extract_writes_files_and_prints_summary(root: Path, tmp_path: Path, capsys) -> None:
    out = tmp_path / "cost" / "gw3"
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--session", SID,
                "--start", T0, "--end", "2026-09-03T22:24:06Z", "--out", str(out)], tmp_path)
    assert code == 0
    assert (out / "usage.md").exists() and (out / "usage.json").exists() and (out / "calls.csv").exists()
    printed = capsys.readouterr().out
    assert str(out / "usage.md") in printed
    assert "calls: 8" in printed and "cost: $" in printed
    data = json.loads((out / "usage.json").read_text())
    assert data["window"]["start"] == "2026-09-03T20:47:43Z"


def test_extract_default_out_is_cost_root_per_gw(root: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--session", SID,
                "--start", T0, "--end", "2026-09-03T22:24:06Z"], tmp_path)
    assert code == 0
    assert (tmp_path / "data" / "cost" / "gw3" / "usage.md").exists()


def test_extract_accepts_session_prefix(root: Path, tmp_path: Path) -> None:
    out = tmp_path / "o"
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--session", SID[:8],
                "--start", T0, "--end", "2026-09-03T22:24:06Z", "--out", str(out)], tmp_path)
    assert code == 0


def test_list_prints_sessions_newest_first(root: Path, tmp_path: Path, capsys) -> None:
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--cost-root", str(tmp_path / "cost"), "--list"], tmp_path)
    assert code == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("session")
    assert "99999999" in lines[1] and SID[:8] in lines[2]
    assert "GW3" in lines[2] and "run for gw 3." in lines[2]


def test_inspect_prints_timeline(root: Path, tmp_path: Path, capsys) -> None:
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--session", SID, "--inspect"], tmp_path)
    assert code == 0
    printed = capsys.readouterr().out
    assert "suggested window" in printed and "Commit the changes." in printed


def test_missing_session_exits_1(root: Path, tmp_path: Path, capsys) -> None:
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--session", "deadbeef",
                "--start", T0, "--end", "2026-09-03T22:24:06Z"], tmp_path)
    assert code == 1
    assert "deadbeef" in capsys.readouterr().err


def test_extract_requires_window(root: Path, tmp_path: Path, capsys) -> None:
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--session", SID], tmp_path)
    assert code == 1
    assert "--start" in capsys.readouterr().err


def test_end_before_start_refuses(root: Path, tmp_path: Path, capsys) -> None:
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--session", SID,
                "--start", "2026-09-03T22:24:06Z", "--end", T0], tmp_path)
    assert code == 1
    assert "before" in capsys.readouterr().err


def test_missing_transcripts_root_exits_1(tmp_path: Path, capsys) -> None:
    code = run(["usage", "--gw", "3", "--transcripts-root", str(tmp_path / "nope"), "--cost-root", str(tmp_path / "cost"), "--list"], tmp_path)
    assert code == 1
    assert "nope" in capsys.readouterr().err


def test_list_defaults_to_sessions_after_latest_earlier_ledger(root: Path, tmp_path: Path, capsys) -> None:
    from tests.test_usage import ledger

    cost = tmp_path / "cost"
    ledger(cost, 2, "2026-09-04T00:00:00Z")   # GW2 processed; its window ended after the GW3 session
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--cost-root", str(cost), "--list"], tmp_path)
    assert code == 0
    out, err = capsys.readouterr()
    lines = out.splitlines()
    assert len(lines) == 2 and "99999999" in lines[1]
    assert "2026-09-04T00:00:00Z" in err and "gw2" in err and "--all" in err


def test_list_ignores_ledgers_for_the_requested_or_later_gameweeks(root: Path, tmp_path: Path, capsys) -> None:
    from tests.test_usage import ledger

    cost = tmp_path / "cost"
    ledger(cost, 3, "2026-09-04T00:00:00Z")   # re-running GW3 must still find its own session
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--cost-root", str(cost), "--list"], tmp_path)
    assert code == 0
    assert len(capsys.readouterr().out.splitlines()) == 3


def test_list_all_and_since_override_the_ledger_cutoff(root: Path, tmp_path: Path, capsys) -> None:
    from tests.test_usage import ledger

    cost = tmp_path / "cost"
    ledger(cost, 2, "2026-09-04T00:00:00Z")
    assert run(["usage", "--gw", "3", "--transcripts-root", str(root), "--cost-root", str(cost), "--list", "--all"], tmp_path) == 0
    assert len(capsys.readouterr().out.splitlines()) == 3
    assert run(["usage", "--gw", "3", "--transcripts-root", str(root), "--cost-root", str(cost), "--list",
                "--since", "2026-09-04T09:00:00Z"], tmp_path) == 0
    assert len(capsys.readouterr().out.splitlines()) == 2


def test_list_with_no_match_after_cutoff_exits_2(root: Path, tmp_path: Path, capsys) -> None:
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--list", "--since", "2027-01-01T00:00:00Z"], tmp_path)
    assert code == 2
    assert "no sessions" in capsys.readouterr().err


def test_cost_root_sets_default_out(root: Path, tmp_path: Path) -> None:
    cost = tmp_path / "ledgers"
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--cost-root", str(cost), "--session", SID,
                "--start", T0, "--end", "2026-09-03T22:24:06Z"], tmp_path)
    assert code == 0
    assert (cost / "gw3" / "usage.md").exists()


def test_since_without_list_refuses(root: Path, tmp_path: Path, capsys) -> None:
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--since", "2027-01-01T00:00:00Z",
                "--session", SID, "--inspect"], tmp_path)
    assert code == 1
    assert "--since" in capsys.readouterr().err


def test_out_without_extract_refuses(root: Path, tmp_path: Path, capsys) -> None:
    code = run(["usage", "--gw", "3", "--transcripts-root", str(root), "--session", SID, "--inspect",
                "--out", str(tmp_path / "x")], tmp_path)
    assert code == 1
    assert "--out" in capsys.readouterr().err


def test_modes_are_mutually_exclusive(root: Path, tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        run(["usage", "--gw", "3", "--transcripts-root", str(root), "--list", "--session", SID, "--inspect"], tmp_path)
