"""`fpl backlog list|status|check`: the triage session's only way to read rows
by number and to change a Status cell."""

from __future__ import annotations

from pathlib import Path

import pytest

from fpl.__main__ import main
from tests.gitrepo import _git, commit_files, init_repo

REPO = Path(__file__).resolve().parents[1]

PREAMBLE = """# Improvement backlog

```
cat <<'EOF' >> docs/backlog.md
| <GW> | <YYYY-MM-DD> | <agent> | <kind> | <finding> | <evidence path> | open |
EOF
```

| Column | Content |
|---|---|
| Status | `open` on write |

## Rows

| GW | Date | Agent | Kind | Finding | Evidence | Status |
|---|---|---|---|---|---|---|
"""
ROWS = [
    "| GW3 | 2026-09-03 | A6 | CODE | C9: unify the DefCon curve | fpl/ep.py | open |\n",
    "| GW4 | 2026-09-10 | A2 | DATA | bootstrap played 0 | data/raw | open |\n",
    "| 8 | 2026-10-23 | A4 | WORKFLOW | flags refresh missed Stach | agents/squad-optimizer.md | open |\n",
    "| GW5 | 2026-09-20 | A10 | TOOL | haiku price missing | fpl/usage.py | rejected: not needed |\n",
]
RETRO = "# GW6 retro\n\n## Corrections\n\n| C9 | A3 | retired | x |\n\n**C21 — A3 rotation band.** text\n"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = init_repo(tmp_path / "repo")
    commit_files(root, {"docs/backlog.md": PREAMBLE + "".join(ROWS),
                        "data/retro/gw6.md": RETRO}, "seed")
    return root


def ledger(repo: Path) -> Path:
    return repo / "docs" / "backlog.md"


def run(repo: Path, *args: str) -> int:
    return main(["backlog", "--file", str(ledger(repo)), *args])


def head(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD").strip()


# --- list -------------------------------------------------------------------

def test_list_numbers_rows_from_the_table_not_the_template(repo: Path, capsys) -> None:
    assert run(repo, "list") == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].split("\t")[:2] == ["row", "gw"]
    assert [line.split("\t")[0] for line in lines[1:]] == ["1", "2", "3"]
    assert lines[1].split("\t")[6] == "C9: unify the DefCon curve"


@pytest.mark.parametrize(("status", "rows"), [("open", ["1", "2", "3"]), ("closed", ["4"]),
                                              ("all", ["1", "2", "3", "4"])])
def test_list_filters_by_status(repo: Path, capsys, status: str, rows: list[str]) -> None:
    assert run(repo, "list", "--status", status) == 0
    assert [line.split("\t")[0] for line in capsys.readouterr().out.splitlines()[1:]] == rows


def test_list_filters_by_kind(repo: Path, capsys) -> None:
    assert run(repo, "list", "--kind", "DATA") == 0
    assert [line.split("\t")[0] for line in capsys.readouterr().out.splitlines()[1:]] == ["2"]


@pytest.mark.parametrize("bad", [
    "| GW7 | 2026-10-16 | A10 | TOOL | finding | fpl/usage.py | open\n",
    "  EOF\n",
    "| GW7 | 2026-10-16 | A10 | TOOL | finding | open |\n",
], ids=["no-trailing-pipe", "phantom-eof", "six-cells"])
@pytest.mark.parametrize("command", [["list"], ["check"], ["status", "1", "rejected: x", "--expect", "C9"]])
def test_every_command_refuses_a_malformed_ledger(repo: Path, capsys, bad: str, command: list[str]) -> None:
    ledger(repo).write_text(PREAMBLE + ROWS[0] + bad + ROWS[1])
    before = ledger(repo).read_bytes()
    assert run(repo, *command) == 1
    assert bad.strip() in capsys.readouterr().err
    assert ledger(repo).read_bytes() == before


# --- status: what changes ---------------------------------------------------

def test_status_changes_only_the_status_cell(repo: Path, capsys) -> None:
    before = ledger(repo).read_text()
    assert run(repo, "status", "3", "rejected: no longer applies", "--expect", "Stach") == 0
    after = ledger(repo).read_text()
    assert after == before.replace(
        "agents/squad-optimizer.md | open |", "agents/squad-optimizer.md | rejected: no longer applies |")
    assert after.endswith("\n")
    assert "row 3: open -> rejected: no longer applies" in capsys.readouterr().out


def test_status_sets_several_rows_in_one_write(repo: Path) -> None:
    assert run(repo, "status", "1,2", "rejected: done", "--expect", "C9", "--expect", "played 0") == 0
    text = ledger(repo).read_text()
    assert text.count("| rejected: done |") == 2
    assert "| <evidence path> | open |" in text


@pytest.mark.parametrize(("args", "why"), [
    (["1,2", "rejected: x", "--expect", "C9", "--expect", "nope"], "expect"),
    (["1,2", "rejected: x", "--expect", "C9"], "expect"),
    (["1,1", "rejected: x", "--expect", "C9", "--expect", "C9"], "duplicate"),
    (["4", "rejected: x", "--expect", "haiku"], "not open"),
    (["9", "rejected: x", "--expect", "x"], "no row 9"),
    (["1", "rejected: a | b", "--expect", "C9"], "|"),
    (["1", "rejected: a\tb", "--expect", "C9"], "tab"),
    (["1", "rejected: a\nb", "--expect", "C9"], "line break"),
    (["1", "rejected: a\rb", "--expect", "C9"], "line break"),
    (["1", "rejected: a\u2028b", "--expect", "C9"], "line break"),
    (["1", "rejected: x", "--expect", ""], "blank"),
    (["1", "rejected: x", "--expect", "  "], "blank"),
    (["1", "done", "--expect", "C9"], "status"),
    (["1", "shipped", "--expect", "C9"], "status"),
    (["1", "superseded by row 1", "--expect", "C9"], "itself"),
    (["1", "superseded by row 12", "--expect", "C9"], "no row 12"),
    (["1", "superseded by C99", "--expect", "C9"], "C99"),
    (["1", "shipped deadbeef", "--expect", "C9"], "deadbeef"),
], ids=["expect-mismatch", "expect-count", "duplicate", "not-open", "no-row", "pipe", "tab",
        "newline", "carriage-return", "line-separator", "empty-expect", "blank-expect", "bare-word", "shipped-no-sha", "self", "row-out-of-range", "unknown-c", "unknown-sha"])
def test_status_refuses_and_writes_nothing(repo: Path, capsys, args: list[str], why: str) -> None:
    before = ledger(repo).read_bytes()
    assert run(repo, "status", *args) == 1
    assert why in capsys.readouterr().err
    assert ledger(repo).read_bytes() == before


# --- status grammar ---------------------------------------------------------

def test_status_accepts_every_documented_form(repo: Path) -> None:
    sha = head(repo)
    other = commit_files(repo, {"x.txt": "x"}, "second")
    forms = {
        1: f"shipped {sha[:7]}",
        2: f"shipped {sha[:7]} (store); {other[:7]} (collector reads the store)",
        3: f"superseded by {sha[:7]} (refresh-token mint) and {other[:7]} (early preflight)",
    }
    ledger(repo).write_text(PREAMBLE + "".join(ROWS))
    expects = {1: "C9", 2: "played 0", 3: "Stach"}
    for row, status in forms.items():
        assert run(repo, "status", str(row), status, "--expect", expects[row]) == 0, status
    for status in ("superseded by C21 (rotation band)", "superseded by row 2 (GW4 A2 played 0)",
                   "superseded by C9"):
        ledger(repo).write_text(PREAMBLE + "".join(ROWS))
        assert run(repo, "status", "1", status, "--expect", "C9") == 0, status


def test_status_refuses_a_sha_not_on_the_current_branch(repo: Path, capsys) -> None:
    _git(repo, "checkout", "-q", "-b", "side")
    side = commit_files(repo, {"y.txt": "y"}, "side")
    _git(repo, "checkout", "-q", "main")
    assert run(repo, "status", "1", f"shipped {side[:7]}", "--expect", "C9") == 1
    assert "not on" in capsys.readouterr().err


def test_status_refuses_an_ambiguous_sha_prefix(repo: Path, capsys, monkeypatch) -> None:
    import fpl.backlog as backlog

    monkeypatch.setattr(backlog, "_resolve_commit", lambda root, sha: None)
    assert run(repo, "status", "1", "shipped abcdef1", "--expect", "C9") == 1
    assert "abcdef1" in capsys.readouterr().err


def test_status_refuses_when_the_file_changed_before_the_write(repo: Path, capsys, monkeypatch) -> None:
    import fpl.backlog as backlog

    real = backlog._validate

    def append_then_validate(*a, **k):
        result = real(*a, **k)
        with ledger(repo).open("a") as f:
            f.write(ROWS[1])
        return result

    monkeypatch.setattr(backlog, "_validate", append_then_validate)
    assert run(repo, "status", "1", "rejected: x", "--expect", "C9") == 1
    assert "changed" in capsys.readouterr().err
    assert ledger(repo).read_text().count("| open |") == 5  # template, 3 rows and the append; row 1 untouched


# --- check ------------------------------------------------------------------

def test_check_passes_a_valid_ledger(repo: Path) -> None:
    assert run(repo, "check") == 0


def test_check_flags_a_status_outside_the_grammar(repo: Path, capsys) -> None:
    ledger(repo).write_text(PREAMBLE + "".join(ROWS) + ROWS[0].replace("| open |", "| done |"))
    assert run(repo, "check") == 1
    assert "row 5" in capsys.readouterr().err


def test_check_passes_the_repo_ledger() -> None:
    assert main(["backlog", "--file", str(REPO / "docs/backlog.md"), "check"]) == 0


def test_status_ignores_targets_named_inside_a_note(repo: Path) -> None:
    assert run(repo, "status", "1", "superseded by C9 (dup of row 1 and C77)", "--expect", "C9") == 0


def test_status_keeps_odd_spacing_in_other_cells(repo: Path) -> None:
    odd = "|GW9|2026-11-01|A6|TOOL|odd  spacing   here|fpl/x.py|open|\n"
    ledger(repo).write_text(PREAMBLE + "".join(ROWS) + odd)
    assert run(repo, "status", "5", "rejected: x", "--expect", "odd") == 0
    assert ledger(repo).read_text().endswith("|GW9|2026-11-01|A6|TOOL|odd  spacing   here|fpl/x.py| rejected: x |\n")


@pytest.mark.parametrize("command", [["list"], ["check"], ["status", "1", "rejected: x", "--expect", "C9"]])
def test_every_command_refuses_crlf(repo: Path, capsys, command: list[str]) -> None:
    ledger(repo).write_bytes((PREAMBLE + "".join(ROWS)).replace("\n", "\r\n").encode())
    before = ledger(repo).read_bytes()
    assert run(repo, *command) == 1
    assert "carriage" in capsys.readouterr().err
    assert ledger(repo).read_bytes() == before


@pytest.mark.parametrize(("status", "why"), [
    ("superseded by C99", "C99"),
    ("superseded by row 12", "no row 12"),
    ("shipped deadbeef", "deadbeef"),
], ids=["unknown-c", "row-out-of-range", "unknown-sha"])
def test_check_flags_a_closed_status_with_a_bad_target(repo: Path, capsys, status: str, why: str) -> None:
    ledger(repo).write_text(PREAMBLE + "".join(ROWS) + ROWS[0].replace("| open |", f"| {status} |"))
    assert run(repo, "check") == 1
    err = capsys.readouterr().err
    assert "row 5" in err and why in err


def test_check_flags_a_sha_not_on_the_current_branch(repo: Path, capsys) -> None:
    _git(repo, "checkout", "-q", "-b", "side")
    side = commit_files(repo, {"y.txt": "y"}, "side")
    _git(repo, "checkout", "-q", "main")
    ledger(repo).write_text(PREAMBLE + "".join(ROWS) + ROWS[0].replace("| open |", f"| shipped {side[:7]} |"))
    assert run(repo, "check") == 1
    assert "not on" in capsys.readouterr().err


def test_resolve_commit_refuses_an_ambiguous_prefix(repo: Path) -> None:
    import fpl.backlog as backlog

    shas = [commit_files(repo, {f"f{i}.txt": str(i)}, f"c{i}") for i in range(40)]
    by_first = {}
    for sha in shas:
        by_first.setdefault(sha[0], []).append(sha)
    prefix = next(k for k, v in by_first.items() if len(v) > 1)
    assert backlog._resolve_commit(repo, prefix) is None  # git refuses an ambiguous prefix
    assert backlog._resolve_commit(repo, shas[0]) == shas[0]
