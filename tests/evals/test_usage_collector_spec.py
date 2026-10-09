"""The usage-collector spec states every rule its graders check, in the words
they check for."""

from __future__ import annotations

from evals.usage_collector.cases import REPO_ROOT

SPEC = (REPO_ROOT / "agents/usage-collector.md").read_text()


def test_spec_states_the_graded_rules() -> None:
    for phrase in (
        "Inspect EVERY candidate",                       # G1
        "Use both timestamps exactly as printed",        # G2
        "Write the ledger, ONCE",                        # G3
        "Never add\n   `--all` or `--since`",            # G4
        "`calls: … cost: …` line verbatim",              # G5
        "NEVER hand-edit anything under data/cost/",     # G6
        "report the exact words\n   `no session tagged GW{N}`",  # G7
        "Never commit to git",                           # G8
        "| GW<N> | <YYYY-MM-DD> | A10 | TOOL | <finding> | fpl/usage.py | open |",  # G10
    ):
        assert phrase in SPEC, phrase


def test_spec_forbids_compound_commands() -> None:
    # The headless wrapper allows only a bare `usage` command and denies a compound one.
    assert "on its own" in SPEC and "`echo $?`" in SPEC
