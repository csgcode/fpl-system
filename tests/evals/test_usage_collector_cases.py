"""The live cases checked offline against the real CLI: each tree lists,
inspects and writes what its expectation says, so a drifted case fails here
rather than in a paid run."""

from __future__ import annotations

from pathlib import Path

import pytest

from evals.harness.workspace import RepoFile
from evals.usage_collector import trees
from evals.usage_collector.cases import LIVE_CASES, REPO_ROOT, STOP, WRITE, LiveCase
from evals.usage_collector.graders import listed_tags, suggestion
from fpl.__main__ import main
from fpl.api import FplApi
from fpl.service import FplDataService
from fpl.store import SnapshotStore


class NoNetworkGateway:
    def get_json(self, url: str):
        raise AssertionError(f"usage must not touch the network, but fetched {url}")


def cli(argv: list[str], tmp: Path, capsys) -> tuple[int, str]:
    def factory(store: SnapshotStore) -> FplDataService:
        return FplDataService(FplApi(NoNetworkGateway()), store)

    code = main(["--data-root", str(tmp / "raw"), *argv], service_factory=factory)
    out, err = capsys.readouterr()
    return code, out + err


def prepare(case: LiveCase, tmp: Path) -> tuple[Path, Path]:
    transcripts, cost = tmp / "transcripts", tmp / "data" / "cost"
    case.build(transcripts)
    for dest, source in case.ledgers.items():
        path = tmp / dest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((REPO_ROOT / source.path).read_bytes() if isinstance(source, RepoFile) else source)
    return transcripts, cost


@pytest.mark.parametrize("case", LIVE_CASES, ids=[c.id for c in LIVE_CASES])
def test_case_matches_the_cli(case: LiveCase, tmp_path: Path, capsys) -> None:
    transcripts, cost = prepare(case, tmp_path)
    base = ["usage", "--gw", str(case.gw), "--transcripts-root", str(transcripts), "--cost-root", str(cost)]
    code, listing = cli([*base, "--list"], tmp_path, capsys)
    assert code == 0, listing
    candidates = sorted(sid for sid, tags in listed_tags(listing).items() if case.gw in tags)
    assert candidates == sorted(case.expect.candidates)

    windows = {}
    for sid in candidates:
        code, text = cli([*base, "--session", sid, "--inspect"], tmp_path, capsys)
        assert code == 0, text
        windows[sid] = suggestion(text, case.gw)
    if case.expect.outcome == STOP:
        assert all(windows.values()) if candidates else True
        for phrase in case.expect.stop_phrases:
            if phrase.startswith("20"):   # the cutoff timestamp the agent must quote
                assert phrase in listing
        return

    [window] = windows.values()
    assert window == (case.expect.start, case.expect.end)
    code, text = cli([*base, "--session", candidates[0], "--start", window[0], "--end", window[1]], tmp_path, capsys)
    if case.expect.outcome == WRITE:
        assert code == 0, text
        if case.expect.calls_line:
            assert case.expect.calls_line in text
        assert (cost / f"gw{case.gw}" / "usage.json").is_file()
    else:
        assert code == case.expect.write_exit
        assert case.expect.error in text
        assert not (cost / f"gw{case.gw}").exists()


def test_s6_hides_the_real_cycle_behind_the_cutoff(tmp_path: Path, capsys) -> None:
    [case] = [c for c in LIVE_CASES if c.id == "S6"]
    transcripts, cost = prepare(case, tmp_path)
    _, listing = cli(["usage", "--gw", "7", "--transcripts-root", str(transcripts), "--cost-root", str(cost), "--list"],
                     tmp_path, capsys)
    assert listed_tags(listing) == {trees.S6_RESUMED[:8]: set()}
    _, everything = cli(["usage", "--gw", "7", "--transcripts-root", str(transcripts), "--list", "--all"],
                        tmp_path, capsys)
    assert listed_tags(everything)[trees.S6_REAL[:8]] == {7}

