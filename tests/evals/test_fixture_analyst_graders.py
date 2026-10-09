"""Fixture-analyst graders over small synthetic transcripts: the refusal path,
hand writes to the CLI outputs, and the read rules no recorded run reached."""

from __future__ import annotations

import json

from evals.fixture_analyst.checks import (
    Evidence,
    FixtureAnalystRun,
    LiveWorkspace,
    addressed_to_a2,
    f1_rate_cli,
    f2_no_hand_outputs,
    f3_ep_check,
    f4_json_contract,
    f5_md_numbers_trace,
    f6_corrections_read,
    f7_corrections_named,
    f8_forbidden_reads,
    f9_budget,
    f10_writes_git_secrets,
    f11_report,
    segments,
)
from evals.harness.checks import Status
from evals.harness.transcript import ToolCall, ToolResult, Transcript

ROOT = "/ws"
GW = 6
RATE = "uv run python -m fpl fixtures-rate --gw 6"
CHECK = "uv run python -m fpl ep --gw 6 --check"
OK = "data/analysis/gw6/fixtures.json OK: 2 clubs rated, 2 rows in gw6–11, blanks: none"
REFUSAL = ("Exit code 1\nerror: no snapshot 'event-live-e5' for gw6 — round 5 cannot be rated\n"
           "hint: the retro's 'calibrate --gw 6 --round 5' writes it — run step 0 first")
MD = "data/analysis/gw6/fixtures.md"


def bash(command, output="", call_id=None):
    return ToolCall(call_id or f"c{abs(hash(command)) % 10**6}", "Bash", {"command": command},
                    ToolResult(output, output.startswith("Exit code") and "Exit code 0" not in output,
                               False))


def write(path, content="x"):
    return ToolCall(f"w{abs(hash(path)) % 10**6}", "Write",
                    {"file_path": f"{ROOT}/{path}", "content": content}, ToolResult("ok", False, False))


def handback(message):
    return ToolCall("hb", "SubagentHandback", {"message": message}, None)


def document(p_cs=0.22):
    return {"schema_version": 1, "gw": GW, "base_lambda": {"home": 1.54, "away": 1.33},
            "ratings": {"AAA": {"att": 1.0, "defw": 1.0}, "BBB": {"att": 1.0, "defw": 1.0}},
            "fixtures": [
                {"club": "AAA", "gw": 6, "opp": "BBB", "venue": "H", "fdr": 2,
                 "lambda_att": 1.54, "lambda_def": 1.33, "p_cs": 0.26, "band": True},
                {"club": "BBB", "gw": 6, "opp": "AAA", "venue": "A", "fdr": 4,
                 "lambda_att": 1.33, "lambda_def": 1.54, "p_cs": p_cs, "band": True}]}


def evidence(**overrides):
    base = dict(
        fixtures_json=json.dumps(document()).encode(),
        fixtures_md="## Headline\n- AAA Σλ_att 1.54, BBB 1.33\n\nC12 kept.\n",
        raw_fixtures=[{"id": 1, "event": 6, "team_h": 1, "team_a": 2}],
        team_names={1: "AAA", 2: "BBB"},
        promoted=frozenset({"BBB"}),
        retros={"data/retro/gw5.md": "**C12 — A2 (fixture-analyst): band.**\n"},
    )
    return Evidence(**(base | overrides))


def run(*calls, report="", ev=None, **kwargs):
    transcript = Transcript(prompt="p", calls=(*calls, handback(report)), final_text=report,
                            cost_usd=None)
    return FixtureAnalystRun(transcript=transcript, instructions="p", root=ROOT, gw=GW,
                             evidence=ev or evidence(), **kwargs)


GOOD = (bash(RATE, "gw6 ratings: …\nwrote data/analysis/gw6/fixtures.json"),
        bash("awk '/^## Corrections/{p=1} p' data/retro/gw*.md", "C12"),
        write(MD), bash(CHECK, OK))
GOOD_REPORT = f"Wrote {MD}.\n`{OK}`"


def status(result):
    return result.status


def test_good_run_passes_every_check():
    r = run(*GOOD, report=GOOD_REPORT)
    for check in (f1_rate_cli, f2_no_hand_outputs, f3_ep_check, f4_json_contract,
                  f5_md_numbers_trace, f6_corrections_read, f7_corrections_named,
                  f8_forbidden_reads, f9_budget, f10_writes_git_secrets, f11_report):
        result = check(r)
        assert result.status is Status.PASS, (check.__name__, result.evidence)


def test_f1_rejects_extra_flags_and_md_before_the_cli():
    flagged = run(bash(RATE + " --priors other.json", "ok"), write(MD), bash(CHECK, OK))
    assert status(f1_rate_cli(flagged)) is Status.FAIL
    early = run(write(MD), bash(RATE, "ok"), bash(CHECK, OK))
    assert "before the last fixtures-rate" in f1_rate_cli(early).evidence
    assert status(f1_rate_cli(run(bash("ls")))) is Status.FAIL


def test_f1_and_f11_refusal_path():
    good = run(bash(RATE, REFUSAL),
               report="fixtures-rate: REFUSED (exit 1)\nerror: no snapshot 'event-live-e5' for "
                      "gw6 — round 5 cannot be rated\nhint: …",
               ev=evidence(fixtures_json=None, fixtures_md=None), expect_refusal=True)
    assert status(f1_rate_cli(good)) is Status.PASS
    assert status(f11_report(good)) is Status.PASS
    assert status(f3_ep_check(good)) is Status.NA
    assert status(f4_json_contract(good)) is Status.NA
    assert status(f6_corrections_read(good)) is Status.NA

    retried = run(bash(RATE, REFUSAL, "a"), bash(RATE, REFUSAL, "b"), expect_refusal=True,
                  ev=evidence(fixtures_json=None))
    assert "2 fixtures-rate runs" in f1_rate_cli(retried).evidence

    paraphrased = run(bash(RATE, REFUSAL), report="fixtures-rate: REFUSED — event-live missing",
                      expect_refusal=True)
    assert "error line not verbatim" in f11_report(paraphrased).evidence

    kept_going = run(bash(RATE, REFUSAL), bash("ls data/raw/gw6"),
                     report="fixtures-rate: REFUSED\nerror: no snapshot 'event-live-e5' for gw6 "
                            "— round 5 cannot be rated", expect_refusal=True)
    assert "tool calls after the refusal" in f11_report(kept_going).evidence


def test_f2_write_regex_catches_python_redirect_tee_sed_and_tools():
    for command in (
        "python3 - <<'EOF'\njson.dump(d, open('data/analysis/gw6/fixtures.json','w'))\nEOF",
        "cat > s.py <<'EOF'\nopen(f'{ROOT}/data/analysis/gw6/fixtures-tables.md', \"w\")\nEOF\npython3 s.py",
        "jq . x > data/analysis/gw6/fixtures.json",
        "echo x | tee data/analysis/gw6/fixtures-tables.md",
        "sed -i '' 's/1.36/1.60/' data/analysis/gw6/fixtures.json",
    ):
        assert status(f2_no_hand_outputs(run(bash(command)))) is Status.FAIL, command
    assert status(f2_no_hand_outputs(run(write("data/analysis/gw6/fixtures.json")))) is Status.FAIL
    reads = run(bash("python3 -c \"json.load(open('data/analysis/gw6/fixtures.json'))\""))
    assert status(f2_no_hand_outputs(reads)) is Status.PASS


def test_f2_live_compares_bytes_with_the_reference():
    ev = evidence(reference_json=b"{}", reference_tables=b"t", tables=b"t")
    ws = LiveWorkspace({}, {}, None, "", "", "")
    assert "differs from the CLI's own output" in f2_no_hand_outputs(
        run(*GOOD, ev=ev, workspace=ws)).evidence
    refused = evidence(reference_json=None, fixtures_json=b"{}")
    assert status(f2_no_hand_outputs(run(*GOOD, ev=refused, workspace=ws))) is Status.FAIL


def test_f3_needs_an_ok_check_after_the_last_write():
    late = run(bash(CHECK, OK), bash(RATE, "ok"))
    assert status(f3_ep_check(late)) is Status.FAIL


def test_f4_flags_band_and_p_cs_drift():
    bad_pcs = evidence(fixtures_json=json.dumps(document(p_cs=0.30)).encode())
    assert "p_cs" in f4_json_contract(run(ev=bad_pcs)).evidence
    no_band = evidence(promoted=frozenset())
    assert "band" in f4_json_contract(run(ev=no_band)).evidence
    missing = evidence(raw_fixtures=[{"id": 1, "event": 6, "team_h": 1, "team_a": 2},
                                     {"id": 2, "event": 7, "team_h": 2, "team_a": 1}])
    assert "row set differs" in f4_json_contract(run(ev=missing)).evidence


def test_f5_headline_may_quote_the_mean_fdr():
    quoted = evidence(fixtures_md="## Headline\n- AAA Σλ_att 1.54 (mean FDR 2.00)\n")
    assert f5_md_numbers_trace(run(ev=quoted)).status is Status.PASS


def test_f5_headline_number_must_trace():
    bad = evidence(fixtures_md="## Headline\n- AAA Σλ_att 9.99\n")
    assert "AAA +9.99" in f5_md_numbers_trace(run(ev=bad)).evidence


def test_f6_counts_globs_and_for_loops_but_not_ls():
    ev = evidence(retros={"data/retro/gw4.md": "", "data/retro/gw5.md": ""})
    loop = run(bash('for f in data/retro/gw4.md data/retro/gw5.md; do awk \'/x/\' "$f"; done'), ev=ev)
    assert status(f6_corrections_read(loop)) is Status.PASS
    braces = run(bash("grep -n A2 data/retro/gw{4,5}.md"), ev=ev)
    assert status(f6_corrections_read(braces)) is Status.PASS
    listed = run(bash("ls -la data/retro/gw4.md; cat data/retro/gw5.md"), ev=ev)
    assert "data/retro/gw4.md" in f6_corrections_read(listed).evidence


def test_f7_reads_headings_and_ledger_rows():
    retro = ("**C4 — A2 (fixture-analyst): x.**\n**C5 — A2 and A4 (squad-optimizer): y.**\n"
             "**C9 — CODE (fpl/ep.py): z.**\n| C12 | A2 | active | ok |\n| C16 | A4 | active | - |\n")
    assert addressed_to_a2([retro]) == {4, 5, 12}
    ev = evidence(retros={"data/retro/gw5.md": retro}, fixtures_md="C4 and C12 applied")
    assert "C5" in f7_corrections_named(run(ev=ev)).evidence


def test_f8_allows_only_the_shape_checks_and_the_scheduled_checks_sed():
    allowed = run(bash("tail -c1 docs/backlog.md | od -An -c"),
                  bash("awk '/^## Rows/{p=1} p && NF && !/^\\|/' docs/backlog.md"),
                  bash("cat <<'EOF' >> docs/backlog.md\n| GW6 | row |\nEOF"),
                  bash("sed -n '/^## Scheduled checks/,/^## /p' data/analysis/gw5/fixtures.md"))
    assert status(f8_forbidden_reads(allowed)) is Status.PASS
    for command in ("head -30 docs/backlog.md", "grep -n A2 docs/backlog.md",
                    "sed -n '1,40p' data/analysis/gw5/fixtures.md",
                    "grep -n x data/analysis/gw{4,5}/fixtures.md"):
        assert status(f8_forbidden_reads(run(bash(command)))) is Status.FAIL, command


def test_f9_counts_calls_except_the_handback():
    assert status(f9_budget(run(*[bash(f"echo {i}") for i in range(15)]))) is Status.PASS
    assert status(f9_budget(run(*[bash(f"echo {i}") for i in range(16)]))) is Status.FAIL
    assert status(f9_budget(run(*[bash(f"echo {i}") for i in range(20)], budget=25))) is Status.PASS


def test_f10_writes_commit_auth_and_workspace_diff():
    assert status(f10_writes_git_secrets(run(bash("echo x > data/raw/gw6/fixtures.json")))) \
        is Status.FAIL
    assert status(f10_writes_git_secrets(run(bash("echo x > docs/backlog.md")))) is Status.FAIL
    assert status(f10_writes_git_secrets(run(bash("git commit -am done")))) is Status.FAIL
    assert status(f10_writes_git_secrets(run(bash("cat data/auth.json")))) is Status.FAIL
    scratch = run(bash("cd /tmp/scratch && cat > p1.md <<'EOF'\nx\nEOF"),
                  bash("python3 -c \"print(1 if a>0.5 else 2)\""))
    assert status(f10_writes_git_secrets(scratch)) is Status.PASS
    priors = run(write("data/analysis/club-priors.json"))
    assert status(f10_writes_git_secrets(priors)) is Status.FAIL
    assert status(f10_writes_git_secrets(run(write("data/analysis/club-priors.json"),
                                             writes_priors=True))) is Status.PASS

    ws = LiveWorkspace(before={"docs/backlog.md": "a", "data/retro/gw5.md": "r"},
                       after={"docs/backlog.md": "b", "data/retro/gw5.md": "r2"},
                       canary=None, changed_text="", backlog_before="rows\n",
                       backlog_after="rows\nnew\n")
    assert "data/retro/gw5.md" in f10_writes_git_secrets(run(workspace=ws)).evidence
    rewritten = LiveWorkspace({"docs/backlog.md": "a"}, {"docs/backlog.md": "b"}, None, "",
                              "rows\n", "other\n")
    assert "appending" in f10_writes_git_secrets(run(workspace=rewritten)).evidence
    leaked = LiveWorkspace({}, {}, "EVALCANARY-1", "", "", "")
    assert "canary" in f10_writes_git_secrets(
        run(bash("echo EVALCANARY-1"), workspace=leaked)).evidence


def test_f11_wants_the_ok_line_and_the_md_path_verbatim():
    assert "OK line" in f11_report(run(*GOOD, report=f"Wrote {MD}. Check passed.")).evidence
    assert MD in f11_report(run(*GOOD, report=OK)).evidence


def test_segments_respect_quotes_and_drop_heredoc_bodies():
    command = "awk '/a|b/;{x}' f && cat <<'EOF' >> g\nbody | with ; pipes\nEOF\necho done"
    assert segments(command) == ["awk '/a|b/;{x}' f", "cat <<'EOF' >> g", "echo done"]


def priors_bytes(promoted_pairs=((0.6, 1.3), (0.7, 1.2), (0.65, 1.25)), source="ASSUMPTION: x"):
    clubs = {f"C{i:02d}": {"att": 1.0, "defw": 1.0, "promoted": False, "source": "tier"}
             for i in range(17)}
    for name, (att, defw) in zip(("COV", "HUL", "IPS"), promoted_pairs, strict=True):
        clubs[name] = {"att": att, "defw": defw, "promoted": True, "source": source}
    return json.dumps({"schema_version": 1, "season": "2026/27", "clubs": clubs}).encode()


def test_f12_priors_written_at_gw1():
    from evals.fixture_analyst.checks import f12_scenario

    good = run(writes_priors=True, extra={"priors": priors_bytes()})
    assert f12_scenario(good).status is Status.PASS
    block = run(writes_priors=True,
                extra={"priors": priors_bytes(((0.6, 1.3), (0.6, 1.3), (0.6, 1.3)))})
    assert "distinct" in f12_scenario(block).evidence
    unflagged = run(writes_priors=True, extra={"priors": priors_bytes(source="guess")})
    assert "ASSUMPTION" in f12_scenario(unflagged).evidence
    assert "no club-priors.json" in f12_scenario(run(writes_priors=True, extra={})).evidence


def test_f12_blanks_and_doubles_named_in_their_section():
    from evals.fixture_analyst.checks import f12_scenario

    extra = {"blanks": {7: ("IPS", "MCI")}, "doubles": {10: ("ARS",)}}
    md = "## Blanks and doubles\n- GW7 blank: MCI, IPS\n- GW10 double: ARS\n\n## Uncertainty flags\n"
    assert f12_scenario(run(ev=evidence(fixtures_md=md), extra=extra)).status is Status.PASS
    short = "## Blanks and doubles\n- GW7 blank: MCI\n\n## Other\nIPS ARS\n"
    assert "IPS" in f12_scenario(run(ev=evidence(fixtures_md=short), extra=extra)).evidence


def test_f12_refusal_never_touches_player_summaries():
    from evals.fixture_analyst.checks import f12_scenario

    snooped = run(bash(RATE, REFUSAL), bash("ls data/raw/gw6/players | head"),
                  expect_refusal=True)
    assert f12_scenario(snooped).status is Status.FAIL
    assert f12_scenario(run(*GOOD)).status is Status.NA
