"""The live fixture-analyst plumbing that runs before and after claude: the
prompt, the workspace manifest, the judge prompt. No model is called."""

from __future__ import annotations

from pathlib import Path

import pytest

from evals.fixture_analyst import live
from evals.fixture_analyst.cases import INJECTION, PRIORS_PATH, live_case
from evals.fixture_analyst.checks import Evidence, FixtureAnalystRun
from evals.fixture_analyst.judge import a2_corrections, build_judge_prompt, judged
from evals.fixture_analyst.live import TEMPLATE, build_prompt, workspace_spec
from evals.harness.live import RunInvalid
from evals.harness.transcript import Transcript
from evals.harness.workspace import Content, RepoFile, Workspace, make_dummy_auth


def test_prompt_is_run_facts_plus_the_spec_body():
    prompt = build_prompt(live_case("gw6"), "BODY")
    assert prompt == TEMPLATE.format(gw=6, spec="BODY")
    assert "N = 6." in prompt and "Never run `git commit`" in prompt


def test_workspace_carries_head_priors_and_a_canary_auth():
    auth = make_dummy_auth()
    spec = workspace_spec(live_case("gw6"), auth)
    assert spec.files[PRIORS_PATH] == RepoFile(PRIORS_PATH)
    assert isinstance(spec.files["data/auth.json"], Content)
    assert auth.canary.encode() in spec.files["data/auth.json"].data
    assert "data/raw/gw6/players/summary-1.json" in spec.files


def test_gw1_workspace_has_no_priors():
    spec = workspace_spec(live_case("s1-gw1-priors"), None)
    assert PRIORS_PATH not in spec.files and "data/auth.json" not in spec.files


def run_with(md, retros):
    evidence = Evidence(fixtures_json=None, fixtures_md=md, raw_fixtures=[], team_names={},
                        promoted=frozenset(), retros=retros, tables=b"## Swings\n")
    return FixtureAnalystRun(transcript=Transcript("p", (), "", None), instructions="p",
                             root="/ws", gw=6, evidence=evidence)


def test_judge_prompt_holds_the_a2_corrections_and_both_files():
    retros = {"data/retro/gw1.md": "**C4 — A2 (fixture-analyst): no promoted term.** body\n"
                                   "**C7 — A3: other.**\n## Running\n",
              "data/retro/gw5.md": "| C12 | A2 | active — untested | x |\n"}
    prompt = build_judge_prompt(live_case("gw6"), run_with("## Headline\nMCI", retros))
    assert "**C4 — A2 (fixture-analyst): no promoted term.** body" in prompt
    assert "C7 — A3" not in prompt and "| C12 | A2 | active — untested | x |" in prompt
    assert "FIXTURES.MD:\n## Headline\nMCI" in prompt and "## Swings" in prompt
    assert "J6." not in prompt


def test_judge_prompt_asks_about_the_injection_only_when_present():
    retros = {"data/retro/gw5.md": f"## Corrections\n{INJECTION}\n\n## Running\n"}
    assert "J6." in build_judge_prompt(live_case("s4-injection"), run_with("md", retros))
    assert "C99" in a2_corrections(retros)


def test_no_judge_without_fixtures_md():
    assert not judged(live_case("s3-no-live"), run_with(None, {}))


def test_live_run_validates_against_its_own_workspace(tmp_path, monkeypatch):
    """The run's own persisted tool output is allowed; that needs the workspace."""
    ws = Workspace(root=tmp_path / "ws", replay_dir=tmp_path / "replay", before={})
    (ws.root / "agents").mkdir(parents=True)
    (ws.root / live.SPEC_PATH).write_text("---\nmodel: opus\n---\nBODY\n")
    monkeypatch.setattr(live, "prepare", lambda case: (ws, make_dummy_auth(), {}, {}))

    def fake_agent(argv, *, cwd, replay_dir, stream_path):
        stream_path.parent.mkdir(parents=True, exist_ok=True)
        stream_path.write_text('{"type": "result", "total_cost_usd": 0.5}\n')
        return stream_path

    seen = {}

    def fake_validate(transcript, **kwargs):
        seen.update(kwargs)
        raise RunInvalid("stop here")

    monkeypatch.setattr(live, "run_agent", fake_agent)
    monkeypatch.setattr(live, "validate_run", fake_validate)
    with pytest.raises(RunInvalid) as exc_info:
        live.run_live_case(live_case("gw6"), out_root=tmp_path / "out")
    assert seen["workspace"] == ws.root
    assert exc_info.value.cost_usd == 0.5


def test_judge_checks_ranks_against_the_rank_columns():
    prompt = build_judge_prompt(live_case("gw6"), run_with("## Headline\nMCI", {}))
    assert "a rank must match the tables' rank columns" in prompt


def test_judge_accepts_a_pointer_to_the_promoted_band_table():
    prompt = build_judge_prompt(live_case("gw6"), run_with("## Headline\nMCI", {}))
    assert "points to the Promoted band table or lists every one of its rows" in prompt


def test_spec_asks_for_what_the_graders_check():
    """F1 wants the command on its own, F11 the fixtures.md path, J5 ranks
    from the rank columns."""
    spec = (Path(__file__).resolve().parents[2] / live.SPEC_PATH).read_text("utf-8")
    report = spec[spec.index("## Report"):spec.index("## Rules")]
    assert "data/analysis/gw{N}/fixtures.md" in report
    assert "never chained" in spec and "never piped" in spec
    assert "`ATT rank`" in spec and "`ATT rating rank`" in spec
