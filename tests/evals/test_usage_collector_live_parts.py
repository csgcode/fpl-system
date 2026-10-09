"""The pure pieces of a live usage-collector run: prompt, argv, workspace
files, and the workspace evidence the graders read."""

from __future__ import annotations

import json
from pathlib import Path

from evals.harness.workspace import Content, RepoFile, make_dummy_auth
from evals.usage_collector import live
from evals.usage_collector.cases import LIVE_CASES
from evals.usage_collector.graders import LEDGER_FILES

C1 = next(c for c in LIVE_CASES if c.id == "C1")


def test_prompt_is_the_collect_usage_template() -> None:
    prompt = live.build_prompt(7, "# A10 — Usage Collector\n")
    assert prompt == ("Collect the usage ledger for GW7. Follow this agent spec exactly; N is 7.\n\n"
                      "# A10 — Usage Collector\n")


def test_argv_allows_only_the_usage_cli_and_points_at_the_tree(tmp_path: Path) -> None:
    argv = live.build_argv("p", replay_dir=tmp_path / "replay", transcripts=tmp_path / "t")
    assert argv[argv.index("--model") + 1] == "haiku"
    assert argv[argv.index("--allowedTools") + 1] == "Bash(uv run python -m fpl usage*)"
    assert argv[argv.index("--permission-mode") + 1] == "dontAsk"
    assert "--no-session-persistence" in argv
    env = json.loads(argv[argv.index("--settings") + 1])["env"]
    assert env["FPL_TRANSCRIPTS_ROOT"] == str(tmp_path / "t")
    assert env["FPL_REPLAY_DIR"] == str(tmp_path / "replay")


def test_workspace_spec_carries_the_ledgers_and_a_dummy_auth() -> None:
    auth = make_dummy_auth()
    spec = live.workspace_spec(C1, auth)
    assert spec.files["data/cost/gw3/usage.json"] == RepoFile("data/cost/gw3/usage.json")
    assert isinstance(spec.files["data/auth.json"], Content)
    assert "agents/" in spec.code_paths
    assert not any(p.startswith("data/cost/gw4") for p in spec.files)


def test_live_workspace_lists_cost_changes_and_the_reference(tmp_path: Path) -> None:
    from evals.harness.workspace import snapshot

    root, tree = tmp_path / "ws", tmp_path / "t"
    C1.build(tree)
    (root / "data/cost/gw3").mkdir(parents=True)
    (root / "data/cost/gw3/usage.json").write_text("{}")
    before = snapshot(root)
    out = root / "data/cost/gw4"
    live.reference_ledger(tree, gw=4, session="8cbbfa17", start="2026-09-11T17:56:17Z",
                          end="2026-09-11T19:00:52Z", out=out)
    (root / "stream.txt").write_text("leak CANARY-1")
    ws = live.live_workspace(root, before, gw=4, tree=tree, canary="CANARY-1",
                             write=("8cbbfa17", "2026-09-11T17:56:17Z", "2026-09-11T19:00:52Z"),
                             extra_texts={"stream.jsonl": "clean"}, scratch=tmp_path / "ref")
    assert ws.cost_changes == tuple(f"data/cost/gw4/{n}" for n in sorted(LEDGER_FILES))
    assert ws.reference is not None and ws.ledger == ws.reference
    assert ws.canary_hits == ("stream.txt",)


def test_live_workspace_without_a_write_has_no_reference(tmp_path: Path) -> None:
    from evals.harness.workspace import snapshot

    root = tmp_path / "ws"
    root.mkdir()
    ws = live.live_workspace(root, snapshot(root), gw=7, tree=tmp_path, canary="C", write=None,
                             extra_texts={}, scratch=tmp_path / "ref")
    assert ws.cost_changes == () and ws.reference is None and ws.ledger == {}
