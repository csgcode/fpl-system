"""Fixture freezer: strips a real transcript down to what the graders read and
refuses to write anything that looks like a credential or personal data."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.harness.freeze import RedactionError, freeze, redaction_findings
from evals.harness.transcript import load_transcript

ROOT = "/Users/someone/Dev/fpl-system"


def records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def base_records(command: str = "uv run python -m fpl bootstrap --gw 6",
                 output: str = "ok") -> list[dict]:
    return [
        {"type": "user", "uuid": "u0", "parentUuid": None, "cwd": ROOT,
         "timestamp": "t0", "sessionId": "s", "gitBranch": "main",
         "message": {"role": "user", "content": f"Repo root: {ROOT}. Go."}},
        {"type": "attachment", "attachment": {"rendered": "private instructions"},
         "cwd": ROOT},
        {"type": "assistant", "uuid": "a1", "parentUuid": "u0", "cwd": ROOT,
         "timestamp": "t1",
         "message": {"role": "assistant", "id": "m1", "model": "haiku",
                     "usage": {"input_tokens": 3},
                     "content": [{"type": "thinking", "thinking": "x",
                                  "signature": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.sig"}]}},
        {"type": "assistant", "uuid": "a2", "parentUuid": "a1", "cwd": ROOT,
         "timestamp": "t2",
         "message": {"role": "assistant", "id": "m1", "model": "haiku",
                     "content": [{"type": "tool_use", "id": "toolu_1", "name": "Bash",
                                  "input": {"command": command}}]}},
        {"type": "user", "uuid": "u3", "parentUuid": "a2", "cwd": ROOT,
         "timestamp": "t3",
         "toolUseResult": {"stdout": output, "stderr": "", "bashEditDiff": "huge"},
         "message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": "toolu_1", "content": output,
              "is_error": False}]}},
    ]


def test_keeps_only_user_and_assistant_records_and_known_fields(tmp_path):
    src = write_jsonl(tmp_path / "src.jsonl", base_records())
    dst = tmp_path / "out" / "frozen.jsonl"

    freeze(src, dst, repo_root=ROOT)

    rows = records(dst)
    assert [r["type"] for r in rows] == ["user", "assistant", "user"]
    for row in rows:
        assert set(row) <= {"type", "uuid", "parentUuid", "timestamp", "message"}
        assert set(row["message"]) <= {"role", "id", "model", "content", "usage"}
    assert "thinking" not in dst.read_text()
    assert "bashEditDiff" not in dst.read_text()


def test_rewrites_the_repo_root_and_home(tmp_path):
    rows = base_records(command=f"cat {ROOT}/data/x; ls {Path.home()}/notes")
    src = write_jsonl(tmp_path / "src.jsonl", rows)
    dst = tmp_path / "frozen.jsonl"

    freeze(src, dst, repo_root=ROOT)

    text = dst.read_text()
    assert ROOT not in text
    assert str(Path.home()) not in text
    transcript = load_transcript(dst)
    assert transcript.prompt == "Repo root: /repo. Go."
    assert transcript.calls[0].input["command"] == "cat /repo/data/x; ls ~/notes"


def test_rewrites_the_munged_project_dir_in_scratchpad_paths(tmp_path):
    scratch = "/private/tmp/claude-501/-Users-someone-Dev-fpl-system/abc/scratchpad"
    rows = base_records(command=f"cat {scratch}/out.txt > {ROOT}/x")
    src = write_jsonl(tmp_path / "src.jsonl", rows)
    dst = tmp_path / "frozen.jsonl"

    freeze(src, dst, repo_root=ROOT)

    command = load_transcript(dst).calls[0].input["command"]
    assert command == "cat /private/tmp/claude-501/-repo/abc/scratchpad/out.txt > /repo/x"
    assert "someone" not in dst.read_text()


def test_inlines_a_persisted_output(tmp_path):
    saved = tmp_path / "saved.txt"
    saved.write_text("the full output", encoding="utf-8")
    preview = (f"<persisted-output>\nOutput too large (50.1KB). Full output saved to: "
               f"{saved}\n\nPreview (first 2KB):\nthe fu")
    rows = base_records(output=preview)
    rows[-1]["toolUseResult"]["persistedOutputPath"] = str(saved)
    src = write_jsonl(tmp_path / "src.jsonl", rows)
    dst = tmp_path / "frozen.jsonl"

    freeze(src, dst, repo_root=ROOT)

    result = load_transcript(dst).calls[0].result
    assert result.text == "the full output"
    assert result.truncated is False


def test_keeps_the_persisted_preview_when_asked(tmp_path):
    saved = tmp_path / "saved.txt"
    saved.write_text("the full output", encoding="utf-8")
    preview = (f"<persisted-output>\nOutput too large (50.1KB). Full output saved to: "
               f"{saved}\n\nPreview (first 2KB):\nthe fu")
    rows = base_records(output=preview)
    rows[-1]["toolUseResult"]["persistedOutputPath"] = str(saved)
    src = write_jsonl(tmp_path / "src.jsonl", rows)
    dst = tmp_path / "frozen.jsonl"

    freeze(src, dst, repo_root=ROOT, inline_persisted=False)

    result = load_transcript(dst).calls[0].result
    assert result.truncated is True
    assert result.text.endswith("the fu")


def _moved_persisted_records(tmp_path: Path) -> list[dict]:
    gone = tmp_path / "pruned" / "tool-results" / "b123.txt"
    preview = (f"<persisted-output>\nOutput too large (50.1KB). Full output saved to: "
               f"{gone}\n\nPreview (first 2KB):\nthe fu")
    rows = base_records(output=preview)
    rows[-1]["toolUseResult"]["persistedOutputPath"] = str(gone)
    return rows


def test_inlines_a_persisted_output_from_a_fallback_dir(tmp_path):
    archive = tmp_path / "archive" / "tool-results"
    archive.mkdir(parents=True)
    (archive / "b123.txt").write_text("the full output", encoding="utf-8")
    src = write_jsonl(tmp_path / "src.jsonl", _moved_persisted_records(tmp_path))
    dst = tmp_path / "frozen.jsonl"

    freeze(src, dst, repo_root=ROOT, persisted_dirs=[archive])

    result = load_transcript(dst).calls[0].result
    assert result.text == "the full output"
    assert result.truncated is False


def test_keeps_the_preview_when_no_fallback_dir_holds_the_output(tmp_path):
    empty = tmp_path / "archive" / "tool-results"
    empty.mkdir(parents=True)
    src = write_jsonl(tmp_path / "src.jsonl", _moved_persisted_records(tmp_path))
    dst = tmp_path / "frozen.jsonl"

    freeze(src, dst, repo_root=ROOT, persisted_dirs=[empty])

    assert load_transcript(dst).calls[0].result.truncated is True


SECRETS = {
    "bearer": "Bearer abcdefghijklmnopqrstuvwxyz012345",
    "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.c2ln",
    "cookie": 'datadome=Q2xvdWRmbGFyZVNlY3JldA',
    "cookie-json": '{"cf_clearance": "zzz"}',
    "email": "someone.private@example.org",
    "canary": "EVALCANARY-1234",
}


@pytest.mark.parametrize("name", sorted(SECRETS))
def test_refuses_each_secret_pattern_without_echoing_it(tmp_path, name):
    secret = SECRETS[name]
    src = write_jsonl(tmp_path / "src.jsonl", base_records(output=f"x {secret} y"))
    dst = tmp_path / "frozen.jsonl"

    with pytest.raises(RedactionError) as caught:
        freeze(src, dst, repo_root=ROOT)

    message = str(caught.value)
    assert "record 4" in message
    assert secret not in message
    assert not dst.exists()


def test_redaction_findings_is_empty_for_clean_text():
    assert redaction_findings("players: 667, teams: 20 — no secrets here") == []


def test_the_commit_attribution_address_is_not_personal_data():
    trailer = "Co-Authored-By: Claude <noreply@anthropic.com>"
    assert redaction_findings(trailer) == []
    assert redaction_findings("ops-noreply@anthropic.com") == ["email"]
    assert redaction_findings("noreply@anthropic.com.evil.org") == ["email"]


def test_rewrites_the_owner_and_group_columns_of_long_listings(tmp_path):
    listing = ("total 17344\n"
               "drwxr-xr-x@ 438 jdoe  admins  14016  9 Oct 14:34 .\n"
               "-rw-r--r--@   1 jdoe  admins   2.1M 11 Sep 18:58 bootstrap.json\n"
               "-rw-r--r-- 1 jdoe admins 2169532  3 Sep 22:43 data/raw/gw3/bootstrap.json")
    src = write_jsonl(tmp_path / "src.jsonl", base_records("ls -la", listing))
    dst = tmp_path / "frozen.jsonl"

    freeze(src, dst, repo_root=ROOT)

    text = load_transcript(dst).calls[0].result.text
    assert "jdoe" not in text and "admins" not in text
    assert "drwxr-xr-x@ 438 user  staff  14016  9 Oct 14:34 ." in text
    assert "-rw-r--r-- 1 user staff 2169532  3 Sep 22:43 data/raw/gw3/bootstrap.json" in text
