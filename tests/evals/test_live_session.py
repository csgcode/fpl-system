"""The project directory Claude Code keeps for a live eval run: the run may
read its own persisted tool output there, never another project's, and the
directory is deleted once the run is over. A stand-in projects root keeps
the real ~/.claude/projects out of reach."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.harness.live import (
    RunInvalid,
    forget_session,
    project_dir_name,
    run_agent,
    run_judge,
    validate_run,
)
from evals.harness.transcript import ToolCall, ToolResult, Transcript

RESULT = '{"type": "result", "total_cost_usd": 0.01}'


@pytest.fixture
def projects(tmp_path, monkeypatch):
    root = tmp_path / "claude-config" / "projects"
    root.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(root.parent))
    return root


@pytest.fixture
def workspace(tmp_path):
    ws = tmp_path / "fpl-eval-abc" / "ws"
    ws.mkdir(parents=True)
    return ws.resolve()


def session_dir(projects: Path, cwd: Path) -> Path:
    path = projects / project_dir_name(cwd)
    (path / "0000-session" / "tool-results").mkdir(parents=True)
    (path / "0000-session" / "tool-results" / "b1.txt").write_text("big output")
    (path / "memory").mkdir()
    return path


def test_project_dir_name_dashes_every_non_alphanumeric():
    assert project_dir_name(Path("/private/var/T/fpl-eval-x_1/ws")) == \
        "-private-var-T-fpl-eval-x-1-ws"


def test_forget_session_deletes_only_the_runs_own_directory(projects, workspace):
    own = session_dir(projects, workspace)
    neighbour = session_dir(projects, workspace.parent)
    assert forget_session(workspace) == own
    assert not own.exists()
    assert neighbour.is_dir()


def test_forget_session_without_a_directory_is_a_no_op(projects, workspace):
    assert forget_session(workspace) is None


def test_forget_session_refuses_a_cwd_outside_the_temp_dir(projects):
    # The real repo's directory holds the transcripts `fpl usage` costs.
    home_repo = Path.home() / "Dev" / "fpl-system"
    with pytest.raises(ValueError, match="outside the temp dir"):
        forget_session(home_repo)


def test_forget_session_refuses_a_symlinked_directory(projects, workspace, tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (projects / project_dir_name(workspace)).symlink_to(elsewhere)
    with pytest.raises(ValueError, match="symlink"):
        forget_session(workspace)
    assert elsewhere.is_dir()


def read(cid: str, path: str) -> ToolCall:
    return ToolCall(cid, "Read", {"file_path": path}, ToolResult("text", False, False))


def bash(cid: str, command: str) -> ToolCall:
    return ToolCall(cid, "Bash", {"command": command}, ToolResult("text", False, False))


def transcript(*calls: ToolCall) -> Transcript:
    return Transcript("p", calls, "done", None)


def test_validate_run_allows_the_runs_own_persisted_output(projects, workspace, tmp_path):
    own = projects / project_dir_name(workspace) / "s1" / "tool-results" / "b1.txt"
    run = transcript(read("r1", str(own)), bash("b1", f"F={own}; sed -n '1,9p' $F"))
    validate_run(run, replay_dir=tmp_path, real_repo=Path("/nowhere"), workspace=workspace)


def test_validate_run_rejects_another_projects_directory(projects, workspace, tmp_path):
    other = projects / "-Users-someone-Dev-fpl-system" / "s9.jsonl"
    with pytest.raises(RunInvalid, match="r1.*another Claude Code project"):
        validate_run(transcript(read("r1", str(other))), replay_dir=tmp_path,
                     real_repo=Path("/nowhere"), workspace=workspace)


def test_validate_run_rejects_a_tilde_path_to_another_project(projects, workspace, tmp_path,
                                                              monkeypatch):
    monkeypatch.delenv("CLAUDE_CONFIG_DIR")
    call = bash("b1", "cat ~/.claude/projects/-Users-someone-Dev-fpl-system/memory/MEMORY.md")
    with pytest.raises(RunInvalid, match="b1"):
        validate_run(transcript(call), replay_dir=tmp_path, real_repo=Path("/nowhere"),
                     workspace=workspace)


def test_validate_run_without_a_workspace_skips_the_project_check(projects, tmp_path):
    other = projects / "-Users-someone-Dev-fpl-system" / "s9.jsonl"
    validate_run(transcript(read("r1", str(other))), replay_dir=tmp_path,
                 real_repo=Path("/nowhere"))

