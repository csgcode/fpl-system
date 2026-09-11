"""Unit tests for fpl.usage: transcript parsing, window selection, pricing,
stage classification and report writing. Transcripts are synthetic and
carry no prompt text beyond short markers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from fpl.usage import (
    MAIN_THREAD,
    PRICES,
    SessionNotFoundError,
    UnpricedModelError,
    build_report,
    cost_of,
    gw_tags,
    inspect_session,
    list_sessions,
    load_session,
    preview_text,
    select_calls,
    stage_for,
    suggest_window,
    write_report,
)

SID = "11111111-2222-3333-4444-555555555555"
T0 = "2026-09-03T20:47:43.000Z"


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def usage(*, inp=0, cw5=0, cw1=0, cr=0, out=0, thinking=None) -> dict:
    u = {
        "input_tokens": inp,
        "cache_creation_input_tokens": cw5 + cw1,
        "cache_read_input_tokens": cr,
        "output_tokens": out,
        "cache_creation": {
            "ephemeral_5m_input_tokens": cw5,
            "ephemeral_1h_input_tokens": cw1,
        },
        "service_tier": "standard",
    }
    if thinking is not None:
        u["output_tokens_details"] = {"thinking_tokens": thinking}
    return u


def user_line(when: str, text: str, *, meta: bool = False) -> dict:
    return {
        "type": "user",
        "timestamp": when,
        "isMeta": meta,
        "message": {"role": "user", "content": text},
    }


def tool_result_line(when: str, tool_use_id: str) -> dict:
    return {
        "type": "user",
        "timestamp": when,
        "message": {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": "ok"}],
        },
    }


def assistant_line(
    when: str,
    mid: str,
    model: str,
    use: dict,
    content: list | None = None,
    *,
    stop_reason: str | None = "end_turn",
    effort: str | None = "xhigh",
    version: str = "2.1.259",
) -> dict:
    return {
        "type": "assistant",
        "timestamp": when,
        "requestId": f"req_{mid}",
        "effort": effort,
        "version": version,
        "message": {
            "id": mid,
            "model": model,
            "role": "assistant",
            "content": content or [{"type": "text", "text": "x"}],
            "stop_reason": stop_reason,
            "usage": use,
        },
    }


def spawn(when: str, mid: str, tool_use_id: str, description: str, model: str = "claude-fable-5-1") -> dict:
    return assistant_line(
        when,
        mid,
        model,
        usage(inp=2, cw1=1000, cr=50_000, out=200),
        [{"type": "tool_use", "id": tool_use_id, "name": "Agent", "input": {"description": description}}],
        stop_reason="tool_use",
    )


def write_jsonl(path: Path, lines: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(line) + "\n" for line in lines))


def write_agent(root: Path, sid: str, agent_id: str, meta: dict, lines: list[dict]) -> None:
    d = root / sid / "subagents"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"agent-{agent_id}.meta.json").write_text(json.dumps(meta))
    write_jsonl(d / f"agent-{agent_id}.jsonl", lines)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """One session shaped like a GW3 cycle: prompt → orchestrator spawns a
    haiku collector and an opus analyst → user prompt after → commit turn →
    unrelated follow-up prompt."""
    r = tmp_path / "projects"
    main = [
        user_line(T0, "run for gw 3."),
        spawn("2026-09-03T20:47:50Z", "m1", "tu_collect", "GW3 raw data collection"),
        tool_result_line("2026-09-03T20:52:00Z", "tu_collect"),
        spawn("2026-09-03T20:52:10Z", "m2", "tu_fwd", "GW3 FWD player analysis", "claude-fable-5-1"),
        # same message id across three lines: output grows, prompt-side identical
        assistant_line("2026-09-03T21:00:00Z", "m3", "claude-fable-5-1", usage(inp=3, cw5=100, cr=60_000, out=5),
                       [{"type": "text", "text": "a"}], stop_reason=None),
        assistant_line("2026-09-03T21:00:01Z", "m3", "claude-fable-5-1", usage(inp=3, cw5=100, cr=60_000, out=5),
                       [{"type": "tool_use", "id": "tu_bash1", "name": "Bash", "input": {}}], stop_reason=None),
        assistant_line("2026-09-03T21:00:02Z", "m3", "claude-fable-5-1", usage(inp=3, cw5=100, cr=60_000, out=900, thinking=400),
                       [{"type": "tool_use", "id": "tu_read1", "name": "Read", "input": {}}], stop_reason="tool_use"),
        assistant_line("2026-09-03T21:00:03Z", "m4", "<synthetic>", {"input_tokens": 0, "output_tokens": 0}),
        {"type": "assistant", "timestamp": "2026-09-03T21:00:04Z", "message": {"id": "m5", "model": "claude-fable-5-1",
                                                                              "role": "assistant", "content": []}},
        user_line("2026-09-03T21:05:00Z", "<task-notification>done</task-notification>"),
        user_line("2026-09-03T22:08:54Z", "Commit the changes."),
        assistant_line("2026-09-03T22:09:18Z", "m6", "claude-fable-5-1", usage(inp=1, cw1=500, cr=70_000, out=300)),
        user_line("2026-09-03T22:24:06Z", "Does the code corrections c9 and c10 be picked up later?"),
        assistant_line("2026-09-03T22:24:30Z", "m7", "claude-fable-5-1", usage(inp=1, cr=70_000, out=100)),
    ]
    write_jsonl(r / f"{SID}.jsonl", main)
    write_agent(
        r, SID, "aaa111",
        {"agentType": "general-purpose", "description": "GW3 raw data collection", "toolUseId": "tu_collect",
         "spawnDepth": 1, "model": "haiku"},
        [assistant_line("2026-09-03T20:48:00Z", "h1", "claude-haiku-4-5-20251001", usage(inp=10, cw5=25_000, out=500),
                        [{"type": "tool_use", "id": "tu_b", "name": "Bash", "input": {}}], stop_reason="tool_use", effort=None),
         assistant_line("2026-09-03T20:51:00Z", "h2", "claude-haiku-4-5-20251001", usage(inp=5, cw5=2_000, cr=25_000, out=300),
                        effort=None)],
    )
    write_agent(
        r, SID, "bbb222",
        {"agentType": "general-purpose", "description": "GW3 FWD player analysis", "toolUseId": "tu_fwd",
         "spawnDepth": 1, "model": "opus"},
        # finishes after a window that ends at 21:00: still attributed to its spawn
        [assistant_line("2026-09-03T20:53:00Z", "o1", "claude-opus-5", usage(inp=2, cw5=40_000, out=1_000), effort=None),
         assistant_line("2026-09-03T21:04:00Z", "o2", "claude-opus-5", usage(inp=2, cr=40_000, cw5=3_000, out=2_000), effort=None)],
    )
    # a second, unrelated session
    write_jsonl(r / "99999999-0000-0000-0000-000000000000.jsonl",
                [user_line("2026-09-04T10:00:00Z", "fix the tests"),
                 assistant_line("2026-09-04T10:00:05Z", "z1", "claude-fable-5-1", usage(inp=1, cr=10, out=10))])
    return r


# ---------------------------------------------------------------- parsing

def test_dedupes_lines_by_message_id_taking_max_output(root: Path) -> None:
    session = load_session(root, SID)
    m3 = next(c for c in session.main_calls if c.message_id == "m3")
    assert m3.output_tokens == 900
    assert m3.thinking_tokens == 400
    assert m3.cache_read == 60_000 and m3.cache_write_5m == 100
    assert m3.tool_names == ("Bash", "Read")
    assert m3.stop_reason == "tool_use"
    assert m3.lines == 3


def test_skips_synthetic_and_usage_less_messages(root: Path) -> None:
    ids = {c.message_id for c in load_session(root, SID).main_calls}
    assert "m4" not in ids and "m5" not in ids
    assert {"m1", "m2", "m3", "m6", "m7"} <= ids


def test_subagent_spawn_time_comes_from_orchestrator_tool_use(root: Path) -> None:
    session = load_session(root, SID)
    fwd = session.agents["bbb222"]
    assert fwd.spawned_at == ts("2026-09-03T20:52:10Z")
    assert fwd.requested_tier == "opus"
    assert [c.model for c in fwd.calls] == ["claude-opus-5", "claude-opus-5"]


def test_prompt_timeline_classifies_kinds(root: Path) -> None:
    kinds = [(p.kind, p.text[:12]) for p in load_session(root, SID).prompts]
    assert kinds[0] == ("human", "run for gw 3")
    assert ("notification", "<task-notifi") in kinds
    assert ("human", "Commit the c") in kinds


# --------------------------------------------------------------- windows

def test_window_is_start_inclusive_end_exclusive(root: Path) -> None:
    session = load_session(root, SID)
    calls = select_calls(session, ts(T0), ts("2026-09-03T22:24:06Z"))
    ids = {c.message_id for c in calls}
    assert "m6" in ids            # commit turn at 22:09 is inside
    assert "m7" not in ids        # 22:24:30 is past the exclusive end
    at_start = select_calls(session, ts("2026-09-03T22:09:18Z"), ts("2026-09-03T22:09:19Z"))
    assert {c.message_id for c in at_start} == {"m6"}


def test_subagent_attributed_by_spawn_not_by_its_own_timestamps(root: Path) -> None:
    session = load_session(root, SID)
    calls = select_calls(session, ts(T0), ts("2026-09-03T21:00:00Z"))
    assert "o2" in {c.message_id for c in calls}   # 21:04 message, spawned 20:52
    later = select_calls(session, ts("2026-09-03T21:00:00Z"), ts("2026-09-04T00:00:00Z"))
    assert not any(c.thread == "bbb222" for c in later)


# ---------------------------------------------------------------- pricing

@pytest.mark.parametrize(
    ("model", "use", "expected"),
    [
        # Fable 5.1: 1M cache read = $0.25
        ("claude-fable-5-1", usage(inp=1_000_000, out=1_000_000, cw5=1_000_000, cw1=1_000_000, cr=1_000_000), 10 + 50 + 12.5 + 20 + 0.25),
        # Fable 5: cache read at the usual 0.1x
        ("claude-fable-5", usage(cr=1_000_000), 1.0),
        ("claude-opus-5", usage(inp=2_000_000, cw5=1_000_000), 10 + 6.25),
        # dated Haiku id resolves by prefix
        ("claude-haiku-4-5-20251001", usage(out=1_000_000, cw1=1_000_000), 5 + 2),
    ],
)
def test_cost_per_model(root: Path, model: str, use: dict, expected: float) -> None:
    write_jsonl(root / "s.jsonl", [assistant_line("2026-01-01T00:00:00Z", "x", model, use)])
    [call] = load_session(root, "s").main_calls
    assert cost_of(call).total == pytest.approx(expected)


def test_uncached_equivalent_prices_all_context_as_input(root: Path) -> None:
    write_jsonl(root / "s.jsonl", [assistant_line("2026-01-01T00:00:00Z", "x", "claude-opus-5",
                                                   usage(inp=100_000, cw5=200_000, cr=700_000, out=10_000))])
    [call] = load_session(root, "s").main_calls
    assert call.context_tokens == 1_000_000
    assert cost_of(call).uncached_equivalent == pytest.approx(5.0 + 0.25)


def test_unknown_model_refuses_naming_it(root: Path) -> None:
    write_jsonl(root / "s.jsonl", [assistant_line("2026-01-01T00:00:00Z", "x", "claude-nova-9", usage(out=1))])
    [call] = load_session(root, "s").main_calls
    with pytest.raises(UnpricedModelError, match="claude-nova-9"):
        cost_of(call)


def test_price_table_has_every_rate() -> None:
    assert all(len(rates) == 5 for rates in PRICES.values())


# ----------------------------------------------------------------- stages

@pytest.mark.parametrize(
    ("description", "stage"),
    [
        ("Collect GW1 raw data", "data-collector"),
        ("GW3 raw data collection", "data-collector"),
        ("Retro-analyze completed GW1", "retro-analyst"),
        ("GW2 retro analysis", "retro-analyst"),
        ("Analyze GW1 fixtures", "fixture-analyst"),
        ("Score MID players GW1", "player-analyst"),
        ("Score GW2 goalkeepers", "player-analyst"),
        ("GW3 FWD player analysis", "player-analyst"),
        ("Optimize GW2 transfers/lineup", "squad-optimizer"),
        ("GW3 squad optimizer", "squad-optimizer"),
        ("Red-team GW1 proposal", "red-team-reviewer"),
        ("GW3 red-team review", "red-team-reviewer"),
        ("Finalize GW1 decision", "finalizer"),
        ("GW3 plan builder", "plan-builder"),
        ("GW3 team executor dry-run", "team-executor"),
        ("GW3 auth import and transfer dry-run", "team-executor"),
        ("GW3 apply transfer and lineup", "team-executor"),
        ("Patch player-analyst spec formula", "in-cycle patch"),
        ("Build FPL write API module", "other"),
    ],
)
def test_stage_for(description: str, stage: str) -> None:
    assert stage_for(description) == stage


def test_gw_tags_from_descriptions() -> None:
    assert gw_tags("GW3 squad optimizer") == {3}
    assert gw_tags("Score MID players GW1") == {1}
    assert gw_tags("Retro-analyze completed gw 12") == {12}
    assert gw_tags("Build write API") == set()


# ----------------------------------------------------------------- report

def test_report_totals(root: Path) -> None:
    report = build_report(load_session(root, SID), gw=3, start=ts(T0), end=ts("2026-09-03T22:24:06Z"))
    t = report.totals
    assert t.calls == 4 + 2 + 2           # m1,m2,m3,m6 + haiku h1,h2 + opus o1,o2
    assert t.output_tokens == 200 + 200 + 900 + 300 + 500 + 300 + 1_000 + 2_000
    assert t.thinking_tokens == 400
    assert t.cache_read == 50_000 * 2 + 60_000 + 70_000 + 25_000 + 40_000
    assert 0 < t.cache_hit_ratio < 1
    assert t.cost_usd == pytest.approx(sum(cost_of(c).total for c in report.calls), abs=1e-4)
    assert report.by_stage[0].stage == "orchestrator"
    assert [a.agent_id for a in report.agents] == [MAIN_THREAD, "aaa111", "bbb222"]
    assert [p.text for p in report.prompts if p.kind == "human"] == ["run for gw 3.", "Commit the changes."]


def test_report_by_model_and_stage_sum_to_total(root: Path) -> None:
    report = build_report(load_session(root, SID), gw=3, start=ts(T0), end=ts("2026-09-03T22:24:06Z"))
    assert sum(m.cost_usd for m in report.by_model) == pytest.approx(report.totals.cost_usd)
    assert sum(s.cost_usd for s in report.by_stage) == pytest.approx(report.totals.cost_usd)
    assert {m.model for m in report.by_model} == {"claude-fable-5-1", "claude-haiku-4-5-20251001", "claude-opus-5"}


def test_write_report_files_and_section_order(root: Path, tmp_path: Path) -> None:
    report = build_report(load_session(root, SID), gw=3, start=ts(T0), end=ts("2026-09-03T22:24:06Z"))
    out = tmp_path / "cost" / "gw3"
    written = write_report(report, out)
    assert {p.name for p in written} == {"usage.md", "usage.json", "calls.csv"}
    md = (out / "usage.md").read_text()
    headings = [line for line in md.splitlines() if line.startswith("## ")]
    assert headings == [
        "## 1. Window", "## 2. Totals", "## 3. By model", "## 4. By stage",
        "## 5. By agent", "## 6. Prompts in window", "## 7. Pricing and method",
    ]
    rows = (out / "calls.csv").read_text().splitlines()
    assert rows[0].startswith("timestamp,thread,agent,stage,model,")
    assert len(rows) == 1 + report.totals.calls
    data = json.loads((out / "usage.json").read_text())
    assert data["window"]["gw"] == 3 and data["window"]["session_id"] == SID
    assert data["totals"]["calls"] == report.totals.calls
    assert "generated_at" not in data


def test_write_report_is_deterministic(root: Path, tmp_path: Path) -> None:
    report = build_report(load_session(root, SID), gw=3, start=ts(T0), end=ts("2026-09-03T22:24:06Z"))
    a, b = tmp_path / "a", tmp_path / "b"
    write_report(report, a)
    write_report(report, b)
    for name in ("usage.md", "usage.json", "calls.csv"):
        assert (a / name).read_bytes() == (b / name).read_bytes()


# ------------------------------------------------------- list and inspect

def test_list_sessions_summarises_each_transcript(root: Path) -> None:
    rows = list_sessions(root)
    assert [r.session_id for r in rows] == ["99999999-0000-0000-0000-000000000000", SID]  # newest first
    gw3 = rows[1]
    assert gw3.first_prompt == "run for gw 3."
    assert gw3.gw_tags == {3}
    assert gw3.agents == 2 and gw3.human_prompts == 3
    assert gw3.first_at == ts(T0)


def test_suggest_window_spans_gw_tagged_spawns_to_next_prompt(root: Path) -> None:
    session = load_session(root, SID)
    window = suggest_window(session, gw=3)
    assert window is not None
    assert window.start == ts(T0)                              # prompt before first GW3 spawn
    assert window.end == ts("2026-09-03T22:08:54Z")            # first human prompt after the last GW3 agent's last call
    assert suggest_window(session, gw=7) is None


def test_inspect_lists_prompts_spawns_and_suggestion(root: Path) -> None:
    text = inspect_session(load_session(root, SID), gw=3)
    assert "run for gw 3." in text
    assert "GW3 FWD player analysis" in text and "opus" in text
    assert "suggested window" in text and "2026-09-03T22:08:54Z" in text


# -------------------------------------------------------- incremental listing

def ledger(cost_root: Path, gw: int, end: str) -> Path:
    path = cost_root / f"gw{gw}" / "usage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "window": {"gw": gw, "end": end}}))
    return path


def test_latest_ledger_end_uses_only_earlier_gameweeks(tmp_path: Path) -> None:
    from fpl.usage import latest_ledger_end

    cost = tmp_path / "cost"
    assert latest_ledger_end(cost, before_gw=3) is None
    ledger(cost, 1, "2026-08-21T14:40:12Z")
    two = ledger(cost, 2, "2026-08-28T14:25:48Z")
    assert latest_ledger_end(cost, before_gw=3) == (ts("2026-08-28T14:25:48Z"), two)
    assert latest_ledger_end(cost, before_gw=2)[0] == ts("2026-08-21T14:40:12Z")
    assert latest_ledger_end(cost, before_gw=1) is None


def test_latest_ledger_end_ignores_malformed_ledgers(tmp_path: Path) -> None:
    from fpl.usage import latest_ledger_end

    cost = tmp_path / "cost"
    (cost / "gw9").mkdir(parents=True)
    (cost / "gw9" / "usage.json").write_text("{not json")
    ledger(cost, 1, "2026-08-21T14:40:12Z")
    assert latest_ledger_end(cost, before_gw=10)[0] == ts("2026-08-21T14:40:12Z")


def test_list_sessions_since_keeps_sessions_still_active_after_cutoff(root: Path) -> None:
    # a session that started before the cutoff but was active after it stays: one
    # session can host two cycles
    since = ts("2026-09-03T22:00:00Z")
    rows = list_sessions(root, since=since)
    assert [r.session_id for r in rows] == ["99999999-0000-0000-0000-000000000000", SID]
    assert list_sessions(root, since=ts("2026-09-04T09:00:00Z"))[0].session_id.startswith("99999999")
    assert len(list_sessions(root, since=ts("2026-09-04T09:00:00Z"))) == 1
    assert list_sessions(root, since=ts("2026-09-05T00:00:00Z")) == []


def test_list_sessions_since_skips_old_files_without_reading_them(root: Path) -> None:
    import os

    # Content timestamps (Sep 4) are after the cutoff; only the file's last
    # write (Sep 1) is before it, so exclusion proves the mtime gate ran first.
    old = root / "99999999-0000-0000-0000-000000000000.jsonl"
    stamp = ts("2026-09-01T00:00:00Z").timestamp()
    os.utime(old, (stamp, stamp))
    rows = list_sessions(root, since=ts("2026-09-02T00:00:00Z"))
    assert [r.session_id for r in rows] == [SID]


# ------------------------------------------------------------ review fixes

def test_depth_two_agent_inherits_the_orchestrator_spawn(tmp_path: Path) -> None:
    r, sid = tmp_path / "p", "s2"
    write_jsonl(r / f"{sid}.jsonl", [user_line("2026-01-01T10:00:00Z", "go"),
                                     spawn("2026-01-01T10:00:10Z", "m1", "tu_parent", "Build plan module")])
    write_agent(r, sid, "parent1",
                {"agentType": "general-purpose", "description": "Build plan module", "toolUseId": "tu_parent",
                 "spawnDepth": 1, "model": "opus"},
                # the parent spawns its reviewer after the window has closed
                [assistant_line("2026-01-01T11:30:00Z", "p1", "claude-opus-5", usage(inp=1, out=10),
                                [{"type": "tool_use", "id": "tu_child", "name": "Agent", "input": {}}], stop_reason="tool_use")])
    write_agent(r, sid, "child1",
                {"agentType": "code-reviewer", "description": "Review the plan-layer changes", "toolUseId": "tu_child",
                 "parentAgentId": "parent1", "spawnDepth": 2},
                [assistant_line("2026-01-01T11:31:00Z", "c1", "claude-opus-5", usage(inp=1, out=10))])
    session = load_session(r, sid)
    assert session.agents["child1"].spawned_at == ts("2026-01-01T10:00:10Z")
    calls = select_calls(session, ts("2026-01-01T10:00:00Z"), ts("2026-01-01T11:00:00Z"))
    assert {c.message_id for c in calls} == {"m1", "p1", "c1"}


def test_malformed_meta_is_skipped_by_list_and_named_by_load(root: Path) -> None:
    bad = root / SID / "subagents" / "agent-zzz999.meta.json"
    bad.write_text("{not json")
    row = next(r for r in list_sessions(root) if r.session_id == SID)
    assert row.agents == 2
    with pytest.raises(ValueError, match="agent-zzz999.meta.json"):
        load_session(root, SID)


def test_usage_without_cache_creation_split_prices_writes_at_5m(root: Path) -> None:
    old = {"input_tokens": 1, "cache_creation_input_tokens": 500, "cache_read_input_tokens": 0, "output_tokens": 2}
    write_jsonl(root / "old.jsonl", [assistant_line("2026-01-01T00:00:00Z", "x", "claude-opus-5", old, version="2.1.237")])
    [call] = load_session(root, "old").main_calls
    assert (call.cache_write_5m, call.cache_write_1h) == (500, 0)
    assert cost_of(call).cache_write == pytest.approx(500 * 6.25 / 1e6)


def test_ambiguous_session_prefix_refuses(root: Path) -> None:
    write_jsonl(root / "1111aaaa.jsonl", [assistant_line("2026-01-01T00:00:00Z", "x", "claude-opus-5", usage(out=1))])
    with pytest.raises(SessionNotFoundError, match="ambiguous"):
        load_session(root, "1111")
    assert load_session(root, "1111aaaa").session_id == "1111aaaa"


@pytest.mark.parametrize(
    "text",
    ["use Bearer abc.def.ghi please", "cookie sessionid=XYZ123; ok", "jwt eyJhbGciOiJIUzI1NiJ9.payload.sig here",
     "x-api-key: sk-ant-000", "password = hunter2"],
)
def test_preview_masks_credential_shaped_text(text: str) -> None:
    masked = preview_text(text)
    assert "[redacted]" in masked
    for secret in ("abc.def.ghi", "XYZ123", "eyJhbGciOiJIUzI1NiJ9", "sk-ant-000", "hunter2"):
        assert secret not in masked


def test_report_paths_are_home_relative(root: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    report = build_report(load_session(root, SID), gw=3, start=ts(T0), end=ts("2026-09-03T22:24:06Z"))
    assert report.transcripts_root == "~/projects"
    assert report.session_path.startswith("~/projects/")
