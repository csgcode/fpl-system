"""The pure pieces of a live plan-builder run: the prompt, the workspace
inputs, the replay clock, the reference plan and the judge's material."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from evals.harness import live as harness_live
from evals.harness.transcript import ToolCall, ToolResult, Transcript
from evals.harness.workspace import Content, make_dummy_auth
from evals.plan_builder import live
from evals.plan_builder.cases import INJECTION, live_case
from evals.plan_builder.judge import RUBRIC, build_judge_prompt, judged

SPEC = "---\nmodel: haiku\n---\n\n# A8 — Plan Builder\n\nBody.\n"


def test_prompt_is_run_facts_then_the_spec_body():
    prompt = live.build_prompt(live_case("gw6-pairing"), "# A8 — Plan Builder\n\nBody.\n")
    head, _, body = prompt.partition("# A8")
    assert "N = 6" in head
    assert "Run from the repo root (the current directory)" in head
    assert "Never run `git commit`" in head
    for leak in ("picks-diff", "warning", "transfer", "captain", "expect"):
        assert leak not in head.lower()
    assert body == " — Plan Builder\n\nBody.\n"


def test_workspace_spec_carries_the_case_inputs_and_dummy_auth():
    auth = make_dummy_auth()
    spec = live.workspace_spec(live_case("p-injection"), auth)
    final = spec.files["data/decisions/gw6/final.md"]
    assert isinstance(final, bytes) and INJECTION.encode() in final
    assert "data/decisions/gw5/final.md" in spec.files
    assert "data/raw/gw6/bootstrap.json" in spec.files
    assert "data/decisions/gw6/plan.json" not in spec.files
    assert spec.files["data/auth.json"] is auth.content
    assert isinstance(auth.content, Content)


def test_a_removed_input_is_absent_from_the_workspace():
    spec = live.workspace_spec(live_case("p-no-bootstrap"), None)
    assert "data/raw/gw6/bootstrap.json" not in spec.files
    assert "data/raw/gw6/.meta/bootstrap.json" in spec.files


def test_replay_clock_is_the_cases_bootstrap_fetch_time():
    spec = live.workspace_spec(live_case("gw2-state-names"), None)
    assert live.replay_now(spec, live_case("gw2-state-names")) == datetime(
        2026, 8, 28, 10, 51, 25, 93298, tzinfo=UTC)


def test_prepare_pins_the_clock_and_turns_a_drifted_case_into_a_source_error(monkeypatch):
    captured = {}

    def fake_build(repo, spec, replay, **kwargs):
        captured.update(kwargs, replay=replay)
        raise RuntimeError("stop")

    monkeypatch.setattr(live, "build_workspace", fake_build)
    with pytest.raises(RuntimeError, match="stop"):
        live.prepare(live_case("gw4-none"))
    assert captured["replay"] is None
    assert captured["now"] == datetime(2026, 9, 11, 18, 54, 16, 658405, tzinfo=UTC)


def test_judge_runs_only_on_refusal_cases():
    assert judged(live_case("p-ambiguous")) and judged(live_case("p-no-bootstrap"))
    assert not judged(live_case("gw6-pairing")) and not judged(live_case("p-injection"))


def test_judge_prompt_holds_the_rubric_the_cli_output_and_the_report():
    transcript = Transcript(
        prompt="p",
        calls=(ToolCall("1", "Bash", {"command": "uv run python -m fpl plan --gw 2"},
                        ToolResult("Exit code 1\nerror: ambiguous transfer name 'Johnson'",
                                   True, False)),),
        final_text="plan: REFUSED (exit 1)",
        cost_usd=None,
    )
    prompt = build_judge_prompt(transcript, SPEC_WITH_TABLE)
    assert prompt.startswith(RUBRIC)
    assert "error: ambiguous transfer name 'Johnson'" in prompt
    assert "plan: REFUSED (exit 1)" in prompt
    assert "PASS" in RUBRIC and "FAIL" in RUBRIC


SPEC_WITH_TABLE = """## Reporting a failure
Intro.

| Message contains | Owner | Meaning |
|---|---|---|
| `no 'picks:' section` | finalizer | the finalizer must re-emit it |

## Rules
- Never edit final.md.
"""


def test_judge_prompt_shows_the_failure_table_as_quotable_text():
    transcript = Transcript(prompt="p", calls=(), final_text="r", cost_usd=None)
    prompt = build_judge_prompt(transcript, SPEC_WITH_TABLE)
    table = prompt.split("FAILURE TABLE:\n", 1)[1].split("\n\n", 1)[0]
    assert "| `no 'picks:' section` | finalizer | the finalizer must re-emit it |" in table
    assert "Never edit final.md" not in table


def test_rubric_allows_restating_the_owner_the_meaning_and_the_cli_text():
    rubric = " ".join(RUBRIC.split())
    for allowed in ("Owner", "Meaning", "error:", "hint:"):
        assert allowed in rubric
    assert "invent" in rubric.lower()


def test_reference_plan_is_compared_without_the_snapshot_age(tmp_path):
    ws_root = tmp_path / "ws"
    plan = ws_root / "data/decisions/gw6/plan.json"
    plan.parent.mkdir(parents=True)
    plan.write_text('{"gw": 6}')
    assert live.read_plan(ws_root, live_case("gw6-pairing")) == b'{"gw": 6}'
    assert live.read_plan(ws_root, live_case("gw5-original")) is None
