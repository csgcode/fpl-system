"""Transcript parser over both record styles: Claude Code subagent JSONL and
`claude -p --output-format stream-json`."""

from __future__ import annotations

import json

from evals.harness.transcript import load_transcript, parse_records


def assistant(*blocks, message_id="m1", **extra):
    return {"type": "assistant", "message": {"id": message_id, "role": "assistant",
                                             "content": list(blocks)}, **extra}


def user(content, **extra):
    return {"type": "user", "message": {"role": "user", "content": content}, **extra}


def use(tool_id, name="Bash", **tool_input):
    return {"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}


def result(tool_id, content, is_error=None):
    return {"type": "tool_result", "tool_use_id": tool_id, "content": content,
            "is_error": is_error}


def text(value):
    return {"type": "text", "text": value}


def test_pairs_calls_with_results_and_keeps_order():
    transcript = parse_records([
        user("do the thing"),
        assistant(use("a", command="echo 1"), message_id="m1"),
        assistant(use("b", command="false"), message_id="m1"),
        user([result("b", "Exit code 1", True), result("a", "1", None)]),
    ])

    assert transcript.prompt == "do the thing"
    assert [c.id for c in transcript.calls] == ["a", "b"]
    first, second = transcript.calls
    assert first.input == {"command": "echo 1"}
    assert first.result.text == "1" and first.result.is_error is False
    assert second.result.is_error is True


def test_list_content_is_flattened_to_text():
    transcript = parse_records([
        user("p"),
        assistant(use("a")),
        user([result("a", [{"type": "text", "text": "one"},
                           {"type": "text", "text": "two"}])]),
    ])
    assert transcript.calls[0].result.text == "one\ntwo"


def test_persisted_output_marks_the_result_truncated():
    preview = ("<persisted-output>\nOutput too large (50.1KB). Full output saved to: "
               "/x/y.txt\n\nPreview (first 2KB):\nabc")
    transcript = parse_records([user("p"), assistant(use("a")),
                                user([result("a", preview)])])
    assert transcript.calls[0].result.truncated is True
    assert "abc" in transcript.calls[0].result.text


def test_call_without_result_has_none():
    transcript = parse_records([user("p"), assistant(use("a"))])
    assert transcript.calls[0].result is None


def test_final_text_prefers_the_handback_message():
    transcript = parse_records([
        user("p"),
        assistant(use("h", name="SubagentHandback", message="the report")),
        user([result("h", '{"success":true}')]),
        user("[Your previous response had no visible output.]"),
        assistant(text("a restated report")),
        {"type": "result", "result": "result text", "total_cost_usd": 0.1},
    ])
    assert transcript.final_text == "the report"
    assert transcript.prompt == "p"


def test_final_text_falls_back_to_the_result_record_then_last_text():
    with_result = parse_records([
        user("p"), assistant(text("thinking aloud")),
        {"type": "result", "result": "final answer", "total_cost_usd": 0.25},
    ])
    assert with_result.final_text == "final answer"
    assert with_result.cost_usd == 0.25

    text_only = parse_records([user("p"), assistant(text("first")),
                               assistant(text("last"), message_id="m2")])
    assert text_only.final_text == "last"
    assert text_only.cost_usd is None


def test_nested_subagent_records_are_skipped():
    transcript = parse_records([
        user("p"),
        assistant(use("inner", command="ls"), parent_tool_use_id="toolu_x"),
        assistant(use("outer", command="pwd"), parent_tool_use_id=None),
    ])
    assert [c.id for c in transcript.calls] == ["outer"]


def test_system_records_and_thinking_blocks_are_ignored():
    transcript = parse_records([
        {"type": "system", "subtype": "init"},
        user("p"),
        assistant({"type": "thinking", "thinking": "hmm", "signature": "sig"},
                  text("done")),
    ])
    assert transcript.final_text == "done"
    assert transcript.calls == ()


def test_load_transcript_reads_jsonl(tmp_path):
    path = tmp_path / "t.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in [
        user("p"), assistant(text("ok")),
    ]) + "\n", encoding="utf-8")
    assert load_transcript(path).final_text == "ok"
