"""Live evals are disabled: nothing in evals/ may start a `claude` process."""

import subprocess

import pytest

from evals.harness import live
from evals.harness.live import LiveEvalsDisabled
from evals.usage_collector import live as usage_live


@pytest.fixture
def no_subprocess(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("a claude process was started")
    monkeypatch.setattr(subprocess, "run", refuse)


@pytest.mark.parametrize("call", [
    lambda tmp: live.build_claude_argv("p", model="haiku", replay_dir=tmp),
    lambda tmp: live.build_judge_argv(),
    lambda tmp: live.run_agent(["claude", "-p", "x"], cwd=tmp, replay_dir=tmp,
                               stream_path=tmp / "s.jsonl"),
    lambda tmp: live.run_judge("p", cwd=tmp),
    lambda tmp: usage_live.build_argv("p", replay_dir=tmp, transcripts=tmp),
], ids=["agent-argv", "judge-argv", "run-agent", "run-judge", "usage-argv"])
def test_every_entry_point_refuses(call, tmp_path, no_subprocess):
    with pytest.raises(LiveEvalsDisabled, match="disabled"):
        call(tmp_path)


def test_the_refusal_has_no_override(monkeypatch, tmp_path, no_subprocess):
    for name in ("FPL_EVAL_ALLOW_LIVE", "EVALS_LIVE", "ALLOW_LIVE"):
        monkeypatch.setenv(name, "1")
    with pytest.raises(LiveEvalsDisabled):
        live.build_judge_argv()
