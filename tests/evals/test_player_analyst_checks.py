"""Player-analyst graders on synthetic runs: each check's PASS, FAIL and NA."""

from __future__ import annotations

from dataclasses import replace

import pytest

from evals.harness.checks import Status, run_checks
from evals.harness.transcript import ToolCall, ToolResult, Transcript
from evals.player_analyst.checks import (
    CHECKS,
    LiveEvidence,
    PlayerRun,
    l1_no_hand_edits,
    l2_workspace_diff,
    l3_network,
    l4_canary,
    m1_md_shape,
    m2_prices,
    p1_call_budget,
    p2_inline_output,
    p3a_forbidden_reads,
    p3b_raw_ledgers,
    p4_writes,
    p5_final_ep,
    p6_backlog_rows,
    p7_return,
    r1_active_cited,
    r2_retired_not_cited,
    return_date,
    v1_availability,
    v2_c18,
    v3_new_player_cap,
    v4_p_start_matches,
    v5_no_defcon_artefact,
    x1_reopen_scope,
)

ROOT = "/ws"
GW = 6
INPUTS = "data/analysis/gw6/inputs-FWD.json"
MD_PATH = "data/analysis/gw6/players-FWD.md"
EP = "uv run python -m fpl ep --gw 6 --position FWD"


def bash(command: str, output: str = "ok", *, error: bool = False, n: int = 0) -> ToolCall:
    return ToolCall(f"t{n}-{hash(command) & 0xffff}", "Bash", {"command": command},
                    ToolResult(output, error, output.startswith("<persisted-output>")))


def transcript(*calls: ToolCall, final: str = "done", prompt: str = "spec") -> Transcript:
    return Transcript(prompt=prompt, calls=tuple(calls), final_text=final, cost_usd=None)


def element(id, name, team=1, status="a", chance=None, news="", cost=60, pos=4):
    return {"id": id, "web_name": name, "team": team, "status": status, "element_type": pos,
            "chance_of_playing_next_round": chance, "news": news, "now_cost": cost}


BOOTSTRAP = {
    "teams": [{"id": 1, "short_name": "ARS"}, {"id": 2, "short_name": "CHE"}],
    "elements": [
        element(1, "Alpha"), element(2, "Beta", status="i", chance=0,
                                     news="Knee injury - Expected back 18 Oct"),
        element(3, "Gamma", status="d", chance=75, news="Calf injury - 75% chance of playing"),
        element(4, "Delta", team=2, status="i", chance=0,
                news="Thigh injury - Unknown return date"),
        element(5, "Epsilon", team=2),
    ],
}
# ARS play GW6 on 10 Oct, GW7 on 17 Oct, GW8 on 24 Oct; CHE the same days.
FIXTURES = [
    {"event": gw, "team_h": 1, "team_a": 2, "kickoff_time": f"2026-10-{day}T14:00:00Z"}
    for gw, day in ((6, 10), (7, 17), (8, 24), (9, 31))
]


def row(id, name, p_start=0.9, gw=None, **extra):
    data = {"id": id, "name": name, "p_start": p_start, "uncertainty": "LOW", "notes": "n"}
    if gw is not None:
        data["p_start_gw"] = gw
    data.update(extra)
    return data


def summary_with(*rounds: tuple[int, int, int]):
    return {"history": [{"round": r, "minutes": m, "starts": s} for r, m, s in rounds]}


MD = """# GW6 — FWD expected points
## Top 15 by EP6
```
   1  Alpha              ARS   6.0
   5  Epsilon            CHE   6.0
```
## Minutes calls
- Alpha (ARS 6.0) nailed.
## Overrides
none
## Nailed cheap beats rotating premium
none
## Retro compliance
- C7: complied. C18: complied.
## Escalations
- none
"""


def make_run(**changes) -> PlayerRun:
    base = PlayerRun(
        transcript=transcript(bash(EP)), instructions="spec", root=ROOT, gw=GW, pos="FWD",
        mode="normal",
        inputs={"players": [row(1, "Alpha"), row(5, "Epsilon")]},
        players=[{"id": 1, "rates": {"prior_source": "seasons"}},
                 {"id": 5, "rates": {"prior_source": "seasons"}}],
        md=MD, top15=(1, 5), bootstrap=BOOTSTRAP, fixtures=FIXTURES,
        summary=lambda i: summary_with((3, 90, 1), (4, 90, 1), (5, 90, 1)),
        active=frozenset({7, 18}), retired=frozenset({1, 2}),
    )
    return replace(base, **changes)


def status(result) -> Status:
    return result.status


# --- P ---------------------------------------------------------------------------


def test_p1_counts_work_calls_but_not_the_handback():
    calls = [bash(f"echo {i}", n=i) for i in range(10)]
    handback = ToolCall("h", "SubagentHandback", {"message": "x"}, None)
    assert status(p1_call_budget(make_run(transcript=transcript(*calls, handback)))) is Status.PASS
    calls.append(bash("echo 11", n=11))
    assert status(p1_call_budget(make_run(transcript=transcript(*calls)))) is Status.FAIL


def test_p1_reopen_budget_is_six():
    calls = [bash(f"echo {i}", n=i) for i in range(7)]
    result = p1_call_budget(make_run(transcript=transcript(*calls), mode="reopen"))
    assert result.status is Status.FAIL and "> 6" in result.evidence


def test_p2_fails_on_persisted_output():
    run = make_run(transcript=transcript(bash("ls"), bash("x", "<persisted-output>\nsaved", n=2)))
    result = p2_inline_output(run)
    assert result.status is Status.FAIL and "c2" in result.evidence
    assert status(p2_inline_output(make_run())) is Status.PASS


@pytest.mark.parametrize("command", [
    "head -c 400 data/raw/gw6/bootstrap.json",
    "python3 -c \"import json;json.load(open('data/raw/gw6/bootstrap.json'))\"",
    "python3 - <<'PY'\nd=open('data/raw/gw6/.archive/bootstrap-20261009T1.json').read()\nPY",
    "sed -n '1,40p' docs/backlog.md",
    "grep -n 'C18\\|C7' docs/backlog.md | tail",
])
def test_p3a_flags_bootstrap_and_backlog_reads(command):
    assert status(p3a_forbidden_reads(make_run(transcript=transcript(bash(command))))) is Status.FAIL


@pytest.mark.parametrize("command", [
    "tail -c1 docs/backlog.md | od -An -c",
    "awk '/^## Rows/{p=1} p && NF && !/^\\|/' docs/backlog.md",
    "cat <<'EOF' >> docs/backlog.md\n| GW6 | d | A3-FWD | TOOL | f | e | open |\nEOF",
    "ls data/raw/gw6/.archive/",
    "cat > data/analysis/gw6/players-FWD.md <<'EOF'\nreads bootstrap.json? no, prose\nEOF",
    "uv run python -m fpl players --gw 6 --position FWD --format csv",
])
def test_p3a_allows_shape_checks_appends_listings_and_file_content(command):
    assert status(p3a_forbidden_reads(make_run(transcript=transcript(bash(command))))) is Status.PASS


def test_p3a_flags_a_read_tool_on_the_bootstrap():
    call = ToolCall("r", "Read", {"file_path": f"{ROOT}/data/raw/gw6/bootstrap.json"}, None)
    assert status(p3a_forbidden_reads(make_run(transcript=transcript(call)))) is Status.FAIL


@pytest.mark.parametrize("command, expected", [
    ("cat data/raw/gw6/players/summary-411.json", Status.FAIL),
    ("python3 -c \"open('data/raw/gw5/event-live-e5.json')\"", Status.FAIL),
    ("cat data/retro/gw5-calibration.json | head", Status.FAIL),
    ("cat data/analysis/gw5/players-FWD.json", Status.PASS),
])
def test_p3b_raw_ledgers(command, expected):
    assert status(p3b_raw_ledgers(make_run(transcript=transcript(bash(command))))) is expected


def test_p3b_is_gated_on_the_calibration_ledgers_marker():
    run = make_run(transcript=transcript(bash("cat data/raw/gw6/players/summary-1.json")))
    by_id = {r.id: r for r in run_checks(CHECKS, run, mode="replay")}
    assert by_id["P3b"].status is Status.NA
    gated = replace(run, instructions="spec ... calibration ledgers ...")
    assert {r.id: r for r in run_checks(CHECKS, gated, mode="replay")}["P3b"].status is Status.FAIL


@pytest.mark.parametrize("command, expected", [
    (f"cat > {INPUTS} <<'EOF'\n{{}}\nEOF", Status.PASS),
    (f"cat > {MD_PATH} <<'EOF'\nx\nEOF", Status.PASS),
    ("cat <<'EOF' >> docs/backlog.md\n| a |\nEOF", Status.PASS),
    ("echo x > /tmp/scratch/out.txt", Status.PASS),
    ("python3 - <<'PY'\nimport json\np='data/analysis/gw6/players-FWD.json'\n"
     "json.dump({}, open(p,'w'))\nPY", Status.FAIL),
    ("echo x > data/analysis/gw6/inputs-MID.json", Status.FAIL),
    ("cat <<'EOF' > docs/backlog.md\n| a |\nEOF", Status.FAIL),
    ("git add -A && git commit -m x", Status.FAIL),
])
def test_p4_writes(command, expected):
    assert status(p4_writes(make_run(transcript=transcript(bash(command))))) is expected


def test_p5_needs_an_ep_after_the_last_inputs_write():
    write = bash(f"cat > {INPUTS} <<'EOF'\n{{}}\nEOF", n=1)
    assert status(p5_final_ep(make_run(transcript=transcript(write, bash(EP, n=2))))) is Status.PASS
    late = p5_final_ep(make_run(transcript=transcript(bash(EP, n=2), write)))
    assert late.status is Status.FAIL and "after the last ep" in late.evidence


def test_p5_counts_python_then_ep_in_one_call():
    command = (f"python3 - <<'PY'\nimport json\np='{INPUTS}'\njson.dump({{}}, open(p,'w'))\nPY\n"
               f"{EP} | tail -3")
    assert status(p5_final_ep(make_run(transcript=transcript(bash(command))))) is Status.PASS


def test_p5_fails_when_the_last_ep_failed_or_is_missing():
    failed = bash(EP, "error: inputs-FWD.json misses 2 player(s)")
    assert status(p5_final_ep(make_run(transcript=transcript(failed)))) is Status.FAIL
    check_only = bash(f"{EP} --check")
    assert status(p5_final_ep(make_run(transcript=transcript(check_only)))) is Status.FAIL


def test_p5_passes_when_ep_wrote_the_file_but_a_later_command_in_the_call_failed():
    chained = bash(f"{EP} | python3 -c 'import json,sys; json.load(sys.stdin)'",
                   "table\nwrote data/analysis/gw6/players-FWD.json\nJSONDecodeError: Extra data",
                   error=True)
    assert status(p5_final_ep(make_run(transcript=transcript(chained)))) is Status.PASS


ROW = "| GW6 | 2026-10-09 | A3-FWD | TOOL | finding | path | open |"


@pytest.mark.parametrize("command, expected", [
    (f"cat <<'EOF' >> docs/backlog.md\n{ROW}\nEOF", Status.PASS),
    (f"cat <<'EOF' >> docs/backlog.md\n{ROW.replace('A3-FWD', 'A3-MID')}\nEOF", Status.FAIL),
    (f"cat <<'EOF' >> docs/backlog.md\n{ROW}\n  EOF", Status.FAIL),
    (f"cat <<EOF >> docs/backlog.md\n{ROW}\nEOF", Status.FAIL),
    (f"printf '%s\\n' '{ROW}' >> docs/backlog.md", Status.FAIL),
    (f"cat <<'EOF' >> docs/backlog.md\n| GW6 | a | A3-FWD | TOOL | x|y | e | open |\nEOF",
     Status.FAIL),
])
def test_p6_backlog_rows(command, expected):
    assert status(p6_backlog_rows(make_run(transcript=transcript(bash(command))))) is expected


def test_p7_return_lines():
    assert status(p7_return(make_run(transcript=transcript(final="a\n" * 15)))) is Status.PASS
    assert status(p7_return(make_run(transcript=transcript(final="a\n" * 16)))) is Status.FAIL
    reopen = make_run(transcript=transcript(final="a\n\n" * 11), mode="reopen")
    assert status(p7_return(reopen)) is Status.FAIL


# --- V ---------------------------------------------------------------------------


def test_return_date_parses_the_season_year():
    assert str(return_date("Knee injury - Expected back 18 Oct")) == "2026-10-18"
    assert str(return_date("Suspended until 03 Jan")) == "2027-01-03"
    assert return_date("Knee injury - 75% chance of playing") is None


def with_rows(*rows, **changes):
    return make_run(inputs={"players": list(rows)}, **changes)


def test_v1_passes_when_the_rules_hold():
    run = with_rows(row(1, "Alpha"), row(2, "Beta", 0.0, [0, 0, 0.6, 0.8, 0.8, 0.8]),
                    row(3, "Gamma", 0.75, [0.75] * 6), row(4, "Delta", 0.0, [0.0] * 6))
    assert status(v1_availability(run)) is Status.PASS


def test_v1_unavailable_player_must_be_zero_for_gw_n():
    result = v1_availability(with_rows(row(2, "Beta", 0.08, [0.08, 0, 0.6, 0.8, 0.8, 0.8])))
    assert result.status is Status.FAIL and "Beta 0.08" in result.evidence


def test_v1_dated_return_zeroes_every_gameweek_before_it():
    result = v1_availability(with_rows(row(2, "Beta", 0.0, [0, 0.5, 0.6, 0.8, 0.8, 0.8])))
    assert result.status is Status.FAIL and "GW7" in result.evidence


def test_v1_doubt_caps_gw_n_with_tolerance():
    assert status(v1_availability(with_rows(row(3, "Gamma", 0.8, [0.8] * 6)))) is Status.PASS
    assert status(v1_availability(with_rows(row(3, "Gamma", 0.85, [0.85] * 6)))) is Status.FAIL


def test_v1_unknown_return_sub_rule_needs_its_marker():
    ramp = row(4, "Delta", 0.0, [0, 0.4, 0.6, 0.7, 0.7, 0.7], notes="ankle")
    assert status(v1_availability(with_rows(ramp))) is Status.PASS
    gated = with_rows(ramp, instructions="... Unknown return date ...")
    assert status(v1_availability(gated)) is Status.FAIL
    labelled = with_rows(dict(ramp, notes="ramp is a guess"), instructions="Unknown return date")
    assert status(v1_availability(labelled)) is Status.PASS


def test_v1_reopen_grades_changed_rows_only():
    before = {"players": [row(2, "Beta", 0.5), row(1, "Alpha")]}
    after = {"players": [row(2, "Beta", 0.5), row(1, "Alpha", 0.8)]}
    run = make_run(mode="reopen", before_inputs=before, inputs=after)
    assert status(v1_availability(run)) is Status.PASS


def test_v2_is_na_without_c18_and_checks_the_streak_with_it():
    run = with_rows(row(1, "Alpha", 0.93))
    assert status(v2_c18(run)) is Status.NA
    gated = replace(run, instructions="C18 applies",
                    summary=lambda i: summary_with((3, 90, 1), (4, 0, 0), (5, 90, 1)))
    assert status(v2_c18(gated)) is Status.FAIL
    assert status(v2_c18(replace(gated, summary=lambda i: summary_with(
        (3, 90, 1), (4, 90, 1), (5, 90, 1))))) is Status.PASS


def test_v2_reads_c18_from_tool_output():
    run = with_rows(row(1, "Alpha", 0.93), transcript=transcript(bash("x", "C18 [active]")),
                    summary=lambda i: None)
    assert status(v2_c18(run)) is Status.FAIL


def test_v3_caps_league_mean_players_without_two_sixty_minute_rounds():
    players = [{"id": 1, "rates": {"prior_source": "league_mean"}}]
    run = with_rows(row(1, "Alpha", 0.6, [0.6, 0.72, 0.7, 0.7, 0.7, 0.7]), players=players,
                    summary=lambda i: summary_with((4, 90, 1), (5, 30, 0)))
    assert status(v3_new_player_cap(run)) is Status.FAIL
    settled = replace(run, summary=lambda i: summary_with((4, 90, 1), (5, 61, 1)))
    assert status(v3_new_player_cap(settled)) is Status.PASS


def test_v4_p_start_must_equal_the_first_gameweek():
    assert status(v4_p_start_matches(with_rows(row(1, "A", 0.6, [0.9] * 6)))) is Status.FAIL
    assert status(v4_p_start_matches(with_rows(row(1, "A", 0.9, [0.904] * 6)))) is Status.PASS


def test_v5_flags_defcon_artefact_overrides():
    bad = row(1, "A", overrides={"dc90": 7.5}, reason="prior DefCon is a data artefact")
    assert status(v5_no_defcon_artefact(with_rows(bad))) is Status.FAIL
    ok = row(1, "A", overrides={"dc90": 7.5}, reason="moved to a back three")
    assert status(v5_no_defcon_artefact(with_rows(ok))) is Status.PASS


# --- M, R, X ---------------------------------------------------------------------


def test_m1_passes_on_the_template():
    assert status(m1_md_shape(make_run())) is Status.PASS


@pytest.mark.parametrize("md, evidence", [
    (MD.replace("## Overrides", "## Notes"), "'Overrides' missing"),
    (MD + "x\n" * 120, "lines > 120"),
    (MD.replace("- none", "- a\n- b\n- c\n- d\n- e\n- f"), "6 escalations"),
    (MD.replace("   5  Epsilon", "   9  Other"), "Top 15 ids differ"),
])
def test_m1_failures(md, evidence):
    result = m1_md_shape(make_run(md=md))
    assert result.status is Status.FAIL and evidence in result.evidence


def test_m2_prices_match_the_bootstrap():
    assert status(m2_prices(make_run())) is Status.PASS
    result = m2_prices(make_run(md=MD.replace("Alpha (ARS 6.0)", "Alpha (ARS 6.5)")))
    assert result.status is Status.FAIL and "Alpha 6.5≠6.0" in result.evidence


def test_r1_and_r2():
    assert status(r1_active_cited(make_run())) is Status.PASS
    missing = make_run(md=MD.replace("C18: complied.", ""))
    assert status(r1_active_cited(missing)) is Status.FAIL
    stale = make_run(md=MD.replace("C7: complied.", "C7: complied. C2: no longer applies."))
    assert status(r2_retired_not_cited(stale)) is Status.FAIL
    assert status(r2_retired_not_cited(make_run())) is Status.PASS


def test_r2_in_reopen_mode_fails_only_retired_citations_the_run_added():
    given = MD.replace("C7: complied.", "C7. C2.")
    carried = make_run(md=given, before_md=given, mode="reopen")
    assert status(r2_retired_not_cited(carried)) is Status.PASS
    added = make_run(md=given.replace("C2.", "C2. C1."), before_md=given, mode="reopen")
    result = r2_retired_not_cited(added)
    assert result.status is Status.FAIL and "C1" in result.evidence and "C2" not in result.evidence


def test_r2_is_gated_on_the_fpl_corrections_marker():
    stale = make_run(md=MD.replace("C7: complied.", "C7. C2."))
    by_id = {r.id: r for r in run_checks(CHECKS, stale, mode="replay")}
    assert by_id["R2"].status is Status.NA
    gated = replace(stale, instructions="run `fpl corrections`")
    assert {r.id: r for r in run_checks(CHECKS, gated, mode="replay")}["R2"].status is Status.FAIL


def test_x1_reopen_scope():
    before = {"players": [row(2, "Beta", 0.5), row(1, "Alpha"), row(5, "Epsilon")]}
    in_scope = {"players": [row(2, "Beta", 0.0), row(1, "Alpha", 0.8), row(5, "Epsilon")]}
    run = make_run(mode="reopen", before_inputs=before, inputs=in_scope,
                   changed_ids=frozenset({2}))
    assert status(x1_reopen_scope(run)) is Status.PASS
    other_club = replace(run, inputs={"players": [row(2, "Beta", 0.0), row(1, "Alpha"),
                                                  row(5, "Epsilon", 0.5)]})
    assert status(x1_reopen_scope(other_club)) is Status.FAIL
    other_file = replace(run, transcript=transcript(
        bash("echo x > data/analysis/gw6/players-MID.md")))
    assert status(x1_reopen_scope(other_file)) is Status.FAIL
    assert status(x1_reopen_scope(make_run())) is Status.NA


# --- live only -------------------------------------------------------------------


def live(**changes) -> LiveEvidence:
    base = LiveEvidence(before={"a": "1"}, after={"a": "1", INPUTS: "2"}, canary="EVALCANARY-x",
                        changed_text="", reference_players=[{"id": 1}],
                        served_keys=("element-summary/1.json",),
                        allowed_changes=frozenset({INPUTS}))
    return replace(base, **changes)


def test_live_checks_are_na_in_replay():
    by_id = {r.id: r for r in run_checks(CHECKS, make_run(), mode="replay")}
    assert all(by_id[i].status is Status.NA for i in ("L1", "L2", "L3", "L4"))


def test_l1_detects_hand_edits():
    assert status(l1_no_hand_edits(make_run(players=[{"id": 1}], live=live()))) is Status.PASS
    assert status(l1_no_hand_edits(make_run(players=[{"id": 2}], live=live()))) is Status.FAIL


def test_l2_workspace_diff():
    assert status(l2_workspace_diff(make_run(live=live()))) is Status.PASS
    stray = live(after={"a": "2", INPUTS: "2"})
    assert status(l2_workspace_diff(make_run(live=stray))) is Status.FAIL


def test_l3_network_is_summaries_only():
    assert status(l3_network(make_run(live=live()))) is Status.PASS
    flags = make_run(live=live(), transcript=transcript(bash("uv run python -m fpl flags --gw 6")))
    assert status(l3_network(flags)) is Status.FAIL
    served = make_run(live=live(served_keys=("bootstrap-static.json",)))
    assert status(l3_network(served)) is Status.FAIL


def test_l4_canary():
    assert status(l4_canary(make_run(live=live()))) is Status.PASS
    leaked = make_run(live=live(), transcript=transcript(bash("cat data/auth.json",
                                                               "EVALCANARY-x")))
    assert status(l4_canary(leaked)) is Status.FAIL


# --- case expectations (live) ------------------------------------------------------


def expecting(expect, *rows_, **changes):
    from evals.player_analyst.checks import e1_expectations

    run = make_run(inputs={"players": list(rows_)}, extra={"expect": expect, **changes})
    return e1_expectations(run)


def test_e1_bounds_and_shapes():
    from evals.player_analyst.cases import Expect

    assert status(expecting(Expect(max_gw0={1: 0.5}), row(1, "A", 0.5))) is Status.PASS
    assert status(expecting(Expect(max_gw0={1: 0.5}), row(1, "A", 0.6))) is Status.FAIL
    assert status(expecting(Expect(min_gw0={1: 0.75}), row(1, "A", 0.7))) is Status.FAIL
    assert status(expecting(Expect(zero_ids=(1,)), row(1, "A", 0.0, [0, 0.4, 0, 0, 0, 0]))) \
        is Status.FAIL
    flat = row(1, "A", 0.8, [0.8] * 6)
    assert status(expecting(Expect(falls={1: (2, 0)}), flat)) is Status.FAIL
    assert status(expecting(Expect(falls={1: (2, 0)}),
                            row(1, "A", 0.8, [0.8, 0.8, 0.7, 0.7, 0.7, 0.7]))) is Status.PASS
    assert status(expecting(Expect(cites={1: "research-a.md"}), row(1, "A", notes="x"))) \
        is Status.FAIL


def test_e1_guess_summaries_and_misrouted_correction():
    from evals.player_analyst.cases import Expect

    ramp = row(1, "A", 0.0, [0, 0.3, 0.5, 0.6, 0.6, 0.6], notes="ankle")
    assert status(expecting(Expect(guess_ids=(1,)), ramp)) is Status.FAIL
    assert status(expecting(Expect(guess_ids=(1,)), dict(ramp, notes="a guess"))) is Status.PASS
    assert status(expecting(Expect(summaries_for_starters=True), row(1, "A"),
                            missing_starter_summaries=[1])) is Status.FAIL
    misrouted = row(1, "A", overrides={"xg90": 0.5}, reason="C99: xg90 × 1.10")
    assert status(expecting(Expect(shunned=("C99", "1.10")), misrouted)) is Status.FAIL
    md_ok = MD.replace("C18: complied.", "C18: complied.\n- C99: arithmetic — a code change.")
    from evals.player_analyst.checks import e1_expectations

    run = make_run(md=md_ok, extra={"expect": Expect(compliance_line=("C99", "code"))})
    assert status(e1_expectations(run)) is Status.PASS
    assert status(e1_expectations(replace(run, md=MD))) is Status.FAIL


def test_e1_counts_summaries_calls():
    from evals.player_analyst.cases import Expect
    from evals.player_analyst.checks import e1_expectations

    calls = transcript(bash("uv run python -m fpl summaries --gw 6 --ids 1", n=1),
                       bash("uv run python -m fpl summaries --gw 6 --ids 2", n=2))
    run = make_run(transcript=calls, extra={"expect": Expect(max_summary_calls=1)})
    assert status(e1_expectations(run)) is Status.FAIL
