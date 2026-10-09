"""The pure pieces of a live data-collector run: the prompt, the workspace
and replay specs per case, and the judge's material."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from evals.data_collector.cases import (
    BOOTSTRAP_PINS,
    JUDGE_PASS_GW6,
    MY_TEAM_FIXTURE,
    REPLAY_NOW,
    REPO_ROOT,
    TEAM_ID,
    live_case,
)
from evals.data_collector import live as collector_live
from evals.data_collector.judge import RUBRIC, build_judge_prompt
from evals.data_collector.live import replay_spec, workspace_spec
from evals.data_collector.prompt import build_prompt
from evals.harness.live import spec_body
from evals.harness.transcript import ToolCall, ToolResult, Transcript
from evals.harness.workspace import Content, GitBlob, make_dummy_auth
from fpl.models import Bootstrap, MyTeam, is_shortlisted
from fpl.store import ARCHIVE_STAMP_FORMAT

SPEC = "---\nmodel: haiku\n---\n\n# A1 — Data Collector\n\nBody text.\n"


def test_spec_body_drops_the_frontmatter():
    assert spec_body(SPEC) == "# A1 — Data Collector\n\nBody text.\n"


def test_prompt_states_run_facts_only():
    prompt = build_prompt(Path("/tmp/ws"), live_case("L3"), spec_body(SPEC))
    assert "Repo root: /tmp/ws" in prompt
    assert "N = 4" in prompt and "M = 3" in prompt
    assert "team_id: null" in prompt
    assert "Never run `git commit`" in prompt
    assert prompt.endswith("Body text.\n")
    for leak in ("deadline", "auth.json", "already fetched"):
        assert leak not in prompt.split("# A1")[0].lower()


def test_prompt_carries_the_team_id():
    assert f"team_id: {TEAM_ID}" in build_prompt(Path("/w"), live_case("L1"), "x")


def test_l1_workspace_has_previous_cycle_files_entry_and_dummy_auth():
    auth = make_dummy_auth()
    spec = workspace_spec(live_case("L1"), auth, now=datetime(2026, 10, 9, tzinfo=UTC))
    assert spec.files["data/raw/gw5/bootstrap.json"] == GitBlob("571f5b0",
                                                                "data/raw/gw5/bootstrap.json")
    assert spec.files["data/raw/gw5/meta.md"] == GitBlob("571f5b0", "data/raw/gw5/meta.md")
    assert json.loads(spec.files["data/entry.json"]) == {"team_id": TEAM_ID}
    assert spec.files["data/auth.json"] is auth.content
    assert "data/raw/gw6/bootstrap.json" not in spec.files


def test_l2_preseeds_a_fresh_bootstrap_and_has_no_auth():
    now = datetime(2026, 9, 18, 13, 0, tzinfo=UTC)
    spec = workspace_spec(live_case("L2"), None, now=now)
    assert spec.files["data/raw/gw5/bootstrap.json"] == BOOTSTRAP_PINS[5]
    meta = json.loads(spec.files["data/raw/gw5/.meta/bootstrap.json"])
    assert datetime.fromisoformat(meta["fetched_at"]) == now - timedelta(hours=1)
    assert "data/auth.json" not in spec.files


def test_l3_has_a_null_team_and_the_stale_gw3_snapshot():
    spec = workspace_spec(live_case("L3"), make_dummy_auth(), now=datetime.now(UTC))
    assert json.loads(spec.files["data/entry.json"]) == {"team_id": None}
    assert spec.files["data/raw/gw3/bootstrap.json"] == GitBlob("82ad6da",
                                                                "data/raw/gw3/bootstrap.json")


def test_replay_specs_carry_pins_team_and_errors():
    l4 = replay_spec(live_case("L4"))
    assert l4.bootstrap == BOOTSTRAP_PINS[6]
    assert l4.team_id == TEAM_ID and l4.my_team == MY_TEAM_FIXTURE
    assert l4.errors == {f"my-team/{TEAM_ID}": 401}
    assert replay_spec(live_case("L3")).team_id is None


def test_my_team_fixture_is_a_valid_squad():
    team = MyTeam.model_validate_json(MY_TEAM_FIXTURE.read_text())
    assert len(team.picks) == 15


def test_auth_content_is_private():
    auth = make_dummy_auth()
    assert isinstance(auth.content, Content) and auth.content.mode == 0o600


def test_judge_prompt_holds_the_rubric_return_and_truncated_log():
    long_output = "x" * 5000
    transcript = Transcript(
        prompt="p",
        calls=(ToolCall("1", "Bash", {"command": "uv run python -m fpl bootstrap --gw 6"},
                        ToolResult("Exit code 1\nerror: boom", True, False)),
               ToolCall("2", "Bash", {"command": "ls"}, ToolResult(long_output, False, False)),
               ToolCall("3", "Write", {"file_path": "m", "content": "c"}, None)),
        final_text="GW: 6",
        cost_usd=None,
    )
    prompt = build_judge_prompt(transcript)
    assert prompt.startswith(RUBRIC)
    assert "GW: 6" in prompt
    assert "uv run python -m fpl bootstrap --gw 6" in prompt
    assert "failed: yes" in prompt and "failed: no" in prompt
    assert "x" * 1500 in prompt and "x" * 1501 not in prompt
    assert '"file_path"' not in prompt and "content" not in prompt


def test_judge_prompt_can_grade_a_substitute_return():
    transcript = Transcript("p", (), "the real return", None)
    prompt = build_judge_prompt(transcript, return_text=JUDGE_PASS_GW6.read_text())
    assert "the real return" not in prompt
    assert "Coverage: players 348" in prompt


def test_workspace_copies_the_python_pin_for_an_offline_sync():
    spec = workspace_spec(live_case("L1"), None, now=datetime.now(UTC))
    assert ".python-version" in spec.code_paths
    assert not any(p.startswith(("data/", "tests/", "evals/")) for p in spec.code_paths)


def test_l5_fails_the_last_shortlisted_summary_so_the_rest_are_fetched():
    """`summaries` stops at the first failing id; failing the last one leaves
    every other summary cached, so the run can still complete."""
    source = REPO_ROOT / BOOTSTRAP_PINS[6].path
    if not source.is_file():
        pytest.skip(f"missing source {source}")
    bootstrap = Bootstrap.model_validate_json(source.read_text("utf-8"))
    last = [p.id for p in bootstrap.elements if is_shortlisted(p)][-1]
    assert live_case("L5").errors == {f"element-summary/{last}": 503}


@pytest.mark.parametrize("gw", sorted(BOOTSTRAP_PINS))
def test_replay_clock_is_the_analysis_bootstrap_fetch_time(gw):
    """The pinned bootstrap's archive name is the moment it was fetched."""
    stamp = REPLAY_NOW[gw].strftime(ARCHIVE_STAMP_FORMAT)
    assert BOOTSTRAP_PINS[gw].path.endswith(f"bootstrap-{stamp}.json")


def test_prepare_pins_the_workspace_clock_and_the_preseed_to_it(monkeypatch):
    captured = {}

    def fake_build(repo, spec, replay, **kwargs):
        captured.update(kwargs, spec=spec)
        raise RuntimeError("stop")

    monkeypatch.setattr(collector_live, "build_workspace", fake_build)
    with pytest.raises(RuntimeError, match="stop"):
        collector_live.prepare(live_case("L2"))
    assert captured["now"] == REPLAY_NOW[5]
    meta = json.loads(captured["spec"].files["data/raw/gw5/.meta/bootstrap.json"])
    assert datetime.fromisoformat(meta["fetched_at"]) == REPLAY_NOW[5] - timedelta(hours=1)
