"""The live player-analyst plumbing that runs before and after claude: the
prompt, the workspace manifest, the REOPEN staging, the judge material. No
model is called."""

from __future__ import annotations

import json

import pytest

from evals.harness.live import JudgeVerdict
from evals.harness.workspace import GitBlob, RepoFile, SourceError, make_dummy_auth
from evals.player_analyst import judge as judging
from evals.player_analyst.cases import (
    DEFAULT_LIVE,
    GW5_REOPEN_STAMP,
    INJECTED_ROW,
    INJECTED_RULE,
    live_case,
    replay_case,
)
from evals.player_analyst.live import case_files, prepare, summary_split
from evals.player_analyst.prompt import build_prompt, delta_path
from evals.player_analyst.runs import replay_run
from fpl.corrections import agent_corrections


def test_default_live_set_is_l1_to_l3():
    assert DEFAULT_LIVE == ("L1-gw6-gkp", "L2-gw6-fwd", "L3-gw5-def-reopen")


def test_prompt_is_run_facts_plus_the_spec_body():
    prompt = build_prompt(live_case("L2-gw6-fwd"), ws="/tmp/ws", spec="BODY")
    assert "- POS = FWD. N = 6; N-1 = 5. Today's date: 2026-10-09." in prompt
    assert "- Mode: normal" in prompt and prompt.endswith("\n\nBODY")
    reopen = build_prompt(live_case("L3-gw5-def-reopen"), ws="/tmp/ws", spec="BODY",
                          delta=delta_path(5, GW5_REOPEN_STAMP))
    assert f"- Mode: REOPEN — delta file data/raw/gw5/flags-delta-{GW5_REOPEN_STAMP}.json" \
        in reopen


def test_summaries_fetched_after_the_run_start_become_recordings():
    inside, recordings = summary_split(live_case("L1-gw6-gkp"))
    keepers = {110, 564, 300, 199, 615, 325, 560, 83, 228}
    recorded = {int(key.split("/")[1].removesuffix(".json")) for key in recordings}
    late = {k for k, source in recordings.items() if isinstance(source, GitBlob)}
    assert keepers <= recorded and len(late) == 43
    assert not any(f"summary-{i}.json" in path for i in keepers for path in inside)
    gw4 = summary_split(live_case("L6-gw4-def"))[1]
    assert len([s for s in gw4.values() if isinstance(s, GitBlob)]) == 48


def test_a_summary_the_commit_lacks_is_recorded_from_the_nearest_gameweek():
    _, recordings = summary_split(live_case("L1-gw6-gkp"))
    assert isinstance(recordings["element-summary/29.json"], RepoFile)


def test_workspace_files_hold_the_analysis_bootstrap_retros_and_canary():
    auth = make_dummy_auth()
    try:
        files = case_files(live_case("L2-gw6-fwd"), auth)
    except SourceError as exc:
        pytest.skip(str(exc))
    boot = json.loads(files["data/raw/gw6/bootstrap.json"])
    isak = next(e for e in boot["elements"] if e["id"] == 379)
    assert "Unknown return date" in isak["news"]
    assert "data/retro/gw5.md" in files and "data/retro/gw6.md" not in files
    assert "data/analysis/gw5/inputs-FWD.json" in files
    assert not any("research-" in path for path in files)
    assert auth.canary.encode() in files["data/auth.json"].data


def test_research_case_carries_the_research_files():
    files = case_files(live_case("L5-gw6-mid-research"), make_dummy_auth())
    assert "data/analysis/gw6/research-scott.md" in files


def test_injected_correction_is_active_for_the_analyst(tmp_path):
    files = case_files(live_case("L7-gw6-fwd-misrouted"), make_dummy_auth())
    text = files["data/retro/gw5.md"].decode("utf-8")
    assert INJECTED_ROW in text and INJECTED_RULE in text
    for path, data in files.items():
        if path.startswith("data/retro/") and path.endswith(".md"):
            (tmp_path / path.rsplit("/", 1)[1]).write_bytes(data)
    view = agent_corrections(tmp_path, gw=6, agent="A3")
    assert 99 in {c.rule.number for c in view.active}


def test_reopen_staging_regenerates_players_then_refreshes(tmp_path):
    case = live_case("L3-gw5-def-reopen")
    try:
        ws, _, staged, delta = prepare(case, tmp_parent=tmp_path)
    except SourceError as exc:
        pytest.skip(str(exc))
    raw = ws.root / "data/raw/gw5"
    document = json.loads((ws.root / delta).read_text("utf-8"))
    defenders = {c["id"] for c in document["pool"] if c["position"] == "DEF"}
    assert defenders == {34, 36, 423, 448}
    assert (raw / ".archive/bootstrap-20260918T124957_221963Z.json").is_file()
    shaw = next(r for r in staged["before_inputs"]["players"] if r["id"] == 423)
    assert shaw["p_start"] == 0.5
    players = json.loads((ws.root / "data/analysis/gw5/players-DEF.json").read_text("utf-8"))
    assert next(p for p in players if p["id"] == 423)["p_start"] == 0.5
    assert ws.before[delta]


# --- judge material ------------------------------------------------------------


def test_j1_material_lists_rivals_mapped_to_gameweeks():
    material = judging.j1_material(replay_run(replay_case("gw5-mid")), [237])
    assert len(material) == 1
    assert "Foden (id 398): Suspended until 17 Oct → available from GW7" in material[0]
    assert "[0.78, 0.78, 0.78, 0.78, 0.78, 0.78]" in material[0]


def test_j2_material_pairs_rows_with_research_verdicts():
    run = replay_run(replay_case("gw6-mid"))
    research = judging.research_at("b28927f", 6, ["data/analysis/gw6/research-scott.md"])
    material = judging.j2_material(run, research, [69])
    assert "Unknown return date" in material[0] and "## Verdict" not in material[0]
    assert "Long-term (6+ GWs)" in material[0]


GW6_GKP_ROW = next(g["row"] for g in judging.gold_items() if g["case"] == "gw6-gkp")


def test_row_terms_are_the_specific_words_of_the_description_and_evidence():
    terms = judging.row_terms(GW6_GKP_ROW)
    assert {"Rushworth", "Scherpen", "Walton", "Benitez", "--ids",
            "data/analysis/gw6/inputs-GKP.json"} <= terms
    assert not terms & {"GW6", "2026-10-09", "A3-GKP", "TOOL", "open"}
    assert judging.row_terms("| GW5 | d | A3-MID | TOOL | C7's bound: 0.25 vs p_start_gw | f | open |") \
        >= {"C7", "0.25", "p_start_gw"}


def test_row_log_holds_only_the_calls_the_row_mentions_in_full():
    run = replay_run(replay_case("gw6-gkp"))
    numbers = [n for n, _ in judging.referenced_calls(run, GW6_GKP_ROW)]
    assert numbers == [1, 3, 5, 6, 7]
    log = judging.row_log(run, GW6_GKP_ROW)
    assert run.work_calls[2].result.text in log
    assert "## call 4 " not in log and "## call 8 " not in log


def test_row_log_shows_write_content_and_a_shared_call_minus_the_backlog_rows():
    from evals.harness.transcript import ToolCall, ToolResult
    from tests.evals.test_player_analyst_checks import make_run, transcript

    row = "| GW6 | d | A3-FWD | DATA | Isak news_added is stale | players-FWD.md | open |"
    write = ToolCall("w", "Write", {"file_path": "/ws/data/analysis/gw6/players-FWD.md",
                                    "content": "## Escalations\n- Isak flag"},
                     ToolResult("ok", False, False))
    shared = ToolCall("s", "Bash", {"command": "cat > md <<'EOF'\nIsak line\nEOF\n"
                                    "cat <<'EOF' >> docs/backlog.md\n" + row + "\nEOF"},
                      ToolResult("", False, False))
    log = judging.row_log(make_run(transcript=transcript(write, shared)), row)
    assert "- Isak flag" in log and "Isak line" in log
    assert row not in log


def test_j3_asks_once_per_row_with_the_project_instructions():
    run = replay_run(replay_case("gw4-def"))
    rows = judging.appended_rows(run)
    j3 = [i for i in judging.items(run, {}) if i.item == "J3"]
    assert len(rows) > 1 and len(j3) == len(rows)
    assert all(row in item.prompt for row, item in zip(rows, j3, strict=True))
    assert "summaries --ids <ids> \\| --shortlist" in j3[0].prompt


def test_gold_rows_occur_verbatim_in_their_transcripts():
    assert judging.gold_rows_present() == []
    assert len([g for g in judging.gold_items() if g["item"] == "J3"]) == 8


def test_agreement_threshold():
    gold = judging.gold_items()
    perfect = [(g, JudgeVerdict(g["gold"] == "PASS", "", 0.0)) for g in gold]
    assert judging.agreement(perfect)[:3] == (8, 8, True)
    flipped = [(g, JudgeVerdict(not v.passed, "x", 0.0)) if g["item"] == "J1" else (g, v)
               for g, v in perfect]
    assert judging.agreement(flipped)[2] is False


@pytest.mark.parametrize("gold", judging.gold_items(), ids=lambda g: g["label"])
def test_every_calibration_prompt_builds(gold):
    prompt = judging.calibration_prompt(gold)
    assert ("ROW:" in prompt or "ROWS:" in prompt) and prompt.startswith(
        judging.NO_TOOLS + "You are")
