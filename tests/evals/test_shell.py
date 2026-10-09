"""Shell-command readers the graders share: which fpl subcommands a Bash call
ran, where it redirected output, which files it wrote, whether it failed."""

from __future__ import annotations

import pytest

from evals.harness.shell import (
    UNKNOWN,
    agent_written_files,
    appended_text,
    call_failed,
    fpl_invocations,
    redirect_targets,
)
from evals.harness.transcript import ToolCall, ToolResult, Transcript


def subcommands(command):
    return [inv.subcommand for inv in fpl_invocations(command)]


def test_fpl_invocations_in_a_compound_command():
    command = ("uv run python -m fpl entry --gw 5 --team-id 1 2>&1 && "
               "uv run python -m fpl picks --gw 5 --team-id 1 --event 4 2>&1; "
               "echo \"EXIT $?\"")
    invocations = fpl_invocations(command)
    assert [i.subcommand for i in invocations] == ["entry", "picks"]
    assert invocations[1].option("--event") == "4"
    assert invocations[0].option("--event") is None


def test_fpl_invocations_skip_data_root_and_accept_python3():
    assert subcommands("python3 -m fpl --data-root /tmp/x summaries --gw 6 --shortlist") == [
        "summaries"
    ]
    assert subcommands("python -m fpl --data-root=/tmp/x bootstrap --gw 6") == ["bootstrap"]


def test_fpl_invocation_stops_at_a_redirect():
    [inv] = fpl_invocations(
        "uv run python -m fpl bootstrap --gw 5 > data/raw/gw5/bootstrap.json 2>&1")
    assert inv.subcommand == "bootstrap"
    assert inv.args == ("bootstrap", "--gw", "5")


def test_fpl_invocation_flags():
    [inv] = fpl_invocations("uv run python -m fpl bootstrap --gw 5 --force")
    assert inv.has("--force") and not inv.has("--apply")
    [help_call] = fpl_invocations("uv run python -m fpl bootstrap --help >/dev/null 2>&1")
    assert help_call.is_help


def test_no_fpl_invocation_in_unrelated_commands():
    assert fpl_invocations("ls data/raw/gw5; cat docs/fpl.md") == []


@pytest.mark.parametrize(
    ("command", "targets"),
    [
        ("uv run python -m fpl bootstrap --gw 5 > data/raw/gw5/bootstrap.json 2>&1",
         ["data/raw/gw5/bootstrap.json"]),
        ("cat <<'EOF' >> docs/backlog.md\n| row > x |\nEOF", ["docs/backlog.md"]),
        ("ls x 2>/dev/null; echo hi >&2", []),
        ("uv run python -m fpl fixtures --gw 1 | tee -a data/raw/gw1/log.txt",
         ["data/raw/gw1/log.txt"]),
        ("echo a 1> out.txt", ["out.txt"]),
    ],
)
def test_redirect_targets(command, targets):
    assert redirect_targets(command) == targets


def bash(command, tool_id="t"):
    return ToolCall(tool_id, "Bash", {"command": command}, None)


def transcript_of(*calls):
    return Transcript(prompt="p", calls=tuple(calls), final_text="", cost_usd=None)


def test_heredoc_writes_are_reconstructed_relative_to_the_root():
    files = agent_written_files(transcript_of(
        bash("cat > data/raw/gw4/meta.md << 'EOF'\nGW: 4\nDeadline: x\nEOF\ncat data/raw/gw4/meta.md"),
        bash("cat > /repo/data/raw/gw5/meta.md <<EOF\nGW: 5\nEOF", "u"),
        bash('cat <<"END" > ./notes.txt\nhello\nEND', "v"),
    ), root="/repo")
    assert files == {
        "data/raw/gw4/meta.md": "GW: 4\nDeadline: x\n",
        "data/raw/gw5/meta.md": "GW: 5\n",
        "notes.txt": "hello\n",
    }


def test_write_tool_and_last_write_wins_then_edit_is_unknown():
    write = ToolCall("w", "Write", {"file_path": "/ws/data/raw/gw6/meta.md",
                                     "content": "GW: 6\n"}, None)
    rewrite = ToolCall("x", "Write", {"file_path": "/ws/data/raw/gw6/meta.md",
                                       "content": "GW: 6 again\n"}, None)
    assert agent_written_files(transcript_of(write, rewrite), root="/ws") == {
        "data/raw/gw6/meta.md": "GW: 6 again\n"
    }
    edit = ToolCall("e", "Edit", {"file_path": "/ws/data/raw/gw6/meta.md",
                                   "old_string": "a", "new_string": "b"}, None)
    assert agent_written_files(transcript_of(write, edit), root="/ws") == {
        "data/raw/gw6/meta.md": UNKNOWN
    }


@pytest.mark.parametrize(
    ("result", "failed"),
    [
        (ToolResult("Exit code 1\nerror: boom", True, False), True),
        (ToolResult("ok\nEXIT 0", False, False), False),
        (ToolResult("error: Expecting value\nEXIT 1", False, False), True),
        (ToolResult("out\nEXIT 2\nmore\nEXIT 0", False, False), True),
        (ToolResult("Exit code 3", False, False), True),
        (ToolResult("FAIL — expired\nEXIT auth-check 1", False, False), True),
        (ToolResult("ok\nauth-check exit 0", False, False), False),
        (ToolResult("boom\nsummaries exit code: 2", False, False), True),
        (ToolResult("no errors here; terror: no", False, False), False),
        (None, False),
    ],
)
def test_call_failed(result, failed):
    assert call_failed(result) is failed


def test_executable_text_keeps_code_heredocs_and_drops_file_content():
    from evals.harness.shell import executable_text

    command = ("python3 << 'EOF'\nimport requests\nEOF\n"
               "cat > meta.md << 'EOF'\nno curl here\nEOF")
    text = executable_text(command)
    assert "import requests" in text
    assert "no curl here" not in text


def test_appended_text_is_the_heredoc_body_appended_to_the_path():
    command = ("tail -c1 docs/backlog.md | od -An -c && cat <<'EOF' >> docs/backlog.md\n"
               "| GW5 | 2026-09-18 | A7 | DATA | x | y | open |\n"
               "EOF\n"
               "cat >> /repo/docs/backlog.md <<EOF\n| second |\nEOF")
    assert appended_text(command, "docs/backlog.md") == (
        "| GW5 | 2026-09-18 | A7 | DATA | x | y | open |\n| second |\n")


def test_appended_text_ignores_overwrites_and_other_paths():
    command = "cat > docs/backlog.md <<'EOF'\nall\nEOF\ncat <<'EOF' >> notes.md\nx\nEOF"
    assert appended_text(command, "docs/backlog.md") is None


# --- heredoc header segments, Edit replay, write_paths (squad-optimizer eval) --


def test_a_heredoc_after_and_and_is_still_a_cat_write():
    command = ("mkdir -p /repo/data/decisions/gw5 && cat > /repo/data/decisions/gw5/"
               "squad-proposal.md <<'MDEOF'\n# GW5\ngit commit is never run\nMDEOF")
    files = agent_written_files(transcript_of(bash(command)), root="/repo")
    assert files == {"data/decisions/gw5/squad-proposal.md": "# GW5\ngit commit is never run\n"}
    from evals.harness.shell import executable_text
    assert "git commit" not in executable_text(command)


def edit(path, old, new, *, replace_all=False, tool_id="e"):
    return ToolCall(tool_id, "Edit", {"file_path": path, "old_string": old,
                                      "new_string": new, "replace_all": replace_all}, None)


def test_apply_edits_replays_an_edit_on_known_content():
    write = ToolCall("w", "Write", {"file_path": "/ws/p.md", "content": "a b a\nc\n"}, None)
    files = agent_written_files(transcript_of(write, edit("/ws/p.md", "c", "d")), root="/ws",
                                apply_edits=True)
    assert files == {"p.md": "a b a\nd\n"}
    files = agent_written_files(transcript_of(write, edit("/ws/p.md", "a", "x")), root="/ws",
                                apply_edits=True)
    assert files == {"p.md": UNKNOWN}
    files = agent_written_files(
        transcript_of(write, edit("/ws/p.md", "a", "x", replace_all=True)), root="/ws",
        apply_edits=True)
    assert files == {"p.md": "x b x\nc\n"}
    assert agent_written_files(transcript_of(write, edit("/ws/p.md", "c", "d")),
                               root="/ws") == {"p.md": UNKNOWN}


def test_an_edit_on_unknown_content_stays_unknown():
    files = agent_written_files(transcript_of(edit("/ws/p.md", "c", "d")), root="/ws",
                                apply_edits=True)
    assert files == {"p.md": UNKNOWN}


def paths(command, root="/repo"):
    from evals.harness.shell import write_paths
    return write_paths(bash(command), root)


def test_write_paths_ignore_redirect_signs_inside_quotes():
    assert paths('python3 -c "import json; print([x for x in y if x > 1e-9])"') == []
    assert paths("echo '>> not a file' > out.txt") == ["out.txt"]


def test_write_paths_resolve_cd_and_same_command_variables():
    assert paths("cd /tmp/scratch && python3 sim.py > bltest.md") == ["/tmp/scratch/bltest.md"]
    assert paths("cd /repo && echo x > notes.md") == ["notes.md"]
    assert paths('S=/tmp/s; uv run python -m fpl ep --gw 4 > "$S/prior/out.txt"') == [
        "/tmp/s/prior/out.txt"]
    assert paths("export SP=/tmp/sp && echo x > ${SP}/a.md") == ["/tmp/sp/a.md"]


def test_write_paths_count_rm_and_mv_targets():
    assert paths("rm -f data/analysis/gw4/opt-blend.json /repo/x.json") == [
        "data/analysis/gw4/opt-blend.json", "x.json"]
    assert paths("mv a.md data/b.md") == ["a.md", "data/b.md"]
    assert paths("ls -la; grep rm notes.md") == []


def test_write_paths_count_python_open_for_writing():
    command = ("python3 - <<'EOF'\nimport json\n"
               "json.dump(d, open('data/analysis/gw4/opt-blend.json', 'w'))\n"
               "p = \"/repo/out.md\"\nwith open(p, \"a\") as f:\n    f.write('x')\n"
               "open('data/in.json').read()\nEOF")
    assert paths(command) == ["data/analysis/gw4/opt-blend.json", "out.md"]
