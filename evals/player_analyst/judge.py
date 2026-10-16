"""Model judge J1–J3, one short call per item, for what code cannot decide:
whether a ramp follows a rival's dates, whether a guess or a research verdict
is honoured, and whether a backlog row is supported by what the run saw.
Code picks the material; the judge only reads it."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from evals.harness.live import JudgeVerdict
from evals.harness.transcript import ToolCall
from evals.harness.shell import appended_text, call_failed
from evals.player_analyst.cases import BACKLOG, FIXTURES, REPO_ROOT, git_show, replay_case
from evals.player_analyst.checks import (
    HORIZON,
    PlayerRun,
    kickoffs,
    return_date,
    starts,
)

GOLD_PATH = FIXTURES / "judge-gold.json"
NO_TOOLS = "Answer from the material below only; use no tools.\n\n"
REQUIRED_J3 = 7

J1 = NO_TOOLS + """You are checking a Fantasy Premier League minutes model. Each row below is a player \
whose club has a rival in the same position with a dated absence or return inside the \
six-gameweek window. p_start_gw lists P(start) for gameweeks {window}. PASS only if each \
row's probabilities move at the gameweek a rival's absence starts or ends, or its notes give \
a concrete reason they don't depend on that rival. Reply with one line: PASS, or FAIL: <row> \
<why>."""

J2 = NO_TOOLS + """You are checking a Fantasy Premier League minutes model. p_start_gw lists P(start) for \
gameweeks {window}. PASS only if (a) each player whose news says "Unknown return date" is 0 \
for the first gameweek, and any later value is labelled a guess or cites a source; (b) each \
player covered by a research file is consistent with its verdict (out for named gameweeks → 0 \
there; likely starter → at least 0.7 for the first gameweek) and the row's notes cite the \
file. Reply with one line: PASS, or FAIL: <row> <why>."""

J3 = NO_TOOLS + """You are auditing one backlog row an agent appended during a run. Below are \
the agent's instructions (its prompt, then the project's CLAUDE.md, which was loaded into its \
context), then every tool call of the run that mentions one of the row's names, fields, files, \
flags or figures, each with whether it failed and its full output. Calls that mention none of \
them are left out. What the instructions say counts as read. An output marked \
<persisted-output> was saved to a file: the agent saw only the preview shown unless a later \
call read that file.

FAIL the row when it:
(a) contradicts what the agent read;
(b) states as fact what another agent does or decides (its rules, discount factors, \
thresholds or candidate sets) although the run never read that agent's spec or output. A \
description of another agent quoted inside a correction or a report is second-hand: it does \
not count as reading that agent;
(c) makes a central claim that nothing in the instructions or calls supports.
Otherwise PASS. A derived figure the calls neither show nor contradict is not by itself a \
FAIL. Saying which agent or step produced a file or snapshot whose gap the run observed is \
not (b).

Reply with one line: PASS, or FAIL: <row> <why>."""

_ROW_TERM = re.compile(r"--[a-z][\w-]*|\bC\d+\b|\d+\.\d+|[A-Za-z][\w./-]*\w")
_COMMON_WORDS = frozenset({"The", "This", "That", "These", "Those", "When", "With", "Without",
                           "Each", "Every", "Some", "Consider", "Should", "Widen"})


@dataclass(frozen=True)
class JudgeItem:
    item: str
    label: str
    prompt: str


def window(run: PlayerRun) -> str:
    return f"GW{run.gw}–GW{run.gw + HORIZON - 1}"


def available_from(run: PlayerRun, team: int, back: object) -> str:
    for gw in range(run.gw, run.gw + HORIZON):
        dates = kickoffs(run, team, gw)
        if dates and min(dates) >= back:
            return f"available from GW{gw}"
    return "out for the whole window"


def rival_lines(run: PlayerRun) -> dict[int, list[str]]:
    """Per club, the same-position players whose news dates an absence or a
    return, mapped to gameweeks."""
    lines: dict[int, list[str]] = {}
    position = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}[run.pos]
    for player in run.bootstrap["elements"]:
        if player["element_type"] != position:
            continue
        back = return_date(player.get("news") or "")
        if back is None:
            continue
        lines.setdefault(player["team"], []).append(
            f"{player['web_name']} (id {player['id']}): {player['news']} → "
            f"{available_from(run, player['team'], back)}")
    return lines


def j1_material(run: PlayerRun, ids: Iterable[int] | None = None) -> list[str]:
    elements = run.elements
    rivals = rival_lines(run)
    wanted = set(ids) if ids is not None else None
    out = []
    for row in run.rows():
        player = elements.get(row["id"])
        if player is None or (wanted is not None and row["id"] not in wanted):
            continue
        others = [line for line in rivals.get(player["team"], [])
                  if f"(id {row['id']})" not in line]
        if not others or (return_date(player.get("news") or "") and wanted is None):
            continue
        out.append(f"- {row.get('name')} (id {row['id']}): p_start_gw {starts(row)}; notes: "
                   f"{row.get('notes', '')}\n  rivals: " + "; ".join(others))
    return out


def research_players(files: Mapping[str, str]) -> dict[int, tuple[str, str]]:
    """Research file → (path, title + Verdict section), keyed by the player id
    its title names."""
    found = {}
    for path, text in files.items():
        title = text.splitlines()[0] if text else ""
        match = re.search(r"\(id (\d+),", title)
        if not match:
            continue
        verdict = re.search(r"(?ms)^## Verdict\n(.*?)(?=^## |\Z)", text)
        found[int(match[1])] = (path, f"{title}\n{verdict[1].strip() if verdict else ''}")
    return found


def j2_material(run: PlayerRun, research: Mapping[str, str],
                ids: Iterable[int] | None = None) -> list[str]:
    elements = run.elements
    covered = research_players(research)
    wanted = set(ids) if ids is not None else None
    out = []
    for row in run.rows():
        if wanted is not None and row["id"] not in wanted:
            continue
        news = (elements.get(row["id"]) or {}).get("news") or ""
        unknown = "unknown return date" in news.lower()
        if not unknown and row["id"] not in covered:
            continue
        text = (f"- {row.get('name')} (id {row['id']}): news {news!r}; p_start_gw "
                f"{starts(row)}; notes: {row.get('notes', '')}")
        if row["id"] in covered:
            path, verdict = covered[row["id"]]
            text += f"\n  research file {path}:\n  " + verdict.replace("\n", "\n  ")
        out.append(text)
    return out


def row_terms(row: str) -> frozenset[str]:
    """The words that tie a backlog row to evidence: names, field and file
    names, flags, decimals and C#s from its description and evidence cells.
    The GW, date, agent, kind and status cells name nothing a call could show."""
    cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
    found = set()
    for term in _ROW_TERM.findall(" ".join(cells[4:-1])):
        if term.startswith("--") or re.fullmatch(r"C\d+|\d+\.\d+", term):
            found.add(term)
        elif (len(term) >= 4 and term not in _COMMON_WORDS and not re.match(r"GW\d", term)
              and (term[0].isupper() or re.search(r"[_./]", term))):
            found.add(term)
    return frozenset(found)


def _call_text(call: ToolCall) -> str:
    """A Bash command, or the whole input of another tool (a Write's content
    included). Rows appended to the backlog are replaced by a placeholder:
    they would otherwise vouch for themselves."""
    if call.name != "Bash":
        return json.dumps(dict(call.input), ensure_ascii=False)
    command = str(call.input.get("command", ""))
    rows = appended_text(command, BACKLOG)
    return command.replace(rows, "<backlog rows>\n") if rows else command


def referenced_calls(run: PlayerRun, row: str) -> list[tuple[int, ToolCall]]:
    """The work calls whose input or output contains a term of the row, by
    call number."""
    terms = row_terms(row)
    found = []
    for number, call in enumerate(run.work_calls, 1):
        what = _call_text(call)
        output = call.result.text if call.result else ""
        if any(term in what or term in output for term in terms):
            found.append((number, call))
    return found


def row_log(run: PlayerRun, row: str) -> str:
    return "\n".join(
        f"## call {number} ({call.name}){' FAILED' if call_failed(call.result) else ''}"
        f"\n$ {_call_text(call)}\n{call.result.text if call.result else ''}"
        for number, call in referenced_calls(run, row))


def j3_prompt(row: str, run: PlayerRun) -> str:
    return (f"{J3}\n\nROW:\n{row}\n\nINSTRUCTIONS:\n{run.instructions}\n\n"
            f"PROJECT INSTRUCTIONS (CLAUDE.md):\n{run.project_instructions}\n\n"
            f"TOOL CALLS:\n{row_log(run, row)}")


def appended_rows(run: PlayerRun) -> list[str]:
    rows = []
    for call in run.work_calls:
        if call.name == "Bash":
            body = appended_text(str(call.input.get("command", "")), BACKLOG)
            rows += [line for line in (body or "").splitlines() if line.strip()]
    return rows


def items(run: PlayerRun, research: Mapping[str, str]) -> list[JudgeItem]:
    found = []
    if (material := j1_material(run)):
        found.append(JudgeItem("J1", "rivals", J1.format(window=window(run)) + "\n\nROWS:\n"
                               + "\n".join(material)))
    if (material := j2_material(run, research)):
        found.append(JudgeItem("J2", "unknown returns and research",
                               J2.format(window=window(run)) + "\n\nROWS:\n"
                               + "\n".join(material)))
    for number, row in enumerate(appended_rows(run), 1):
        found.append(JudgeItem("J3", f"backlog row {number}", j3_prompt(row, run)))
    return found


def judge_run(run: PlayerRun, research: Mapping[str, str],
              ask: Callable[[str], JudgeVerdict]) -> list[tuple[JudgeItem, JudgeVerdict]]:
    return [(item, ask(item.prompt)) for item in items(run, research)]


# --- calibration -------------------------------------------------------------------


def gold_items() -> list[dict]:
    return json.loads(GOLD_PATH.read_text("utf-8"))


def research_at(commit: str, gw: int, paths: Iterable[str]) -> dict[str, str]:
    return {p: (git_show(commit, p) or b"").decode("utf-8") for p in paths}


def calibration_prompt(gold: Mapping) -> str:
    from evals.player_analyst.runs import replay_run

    run = replay_run(replay_case(gold["case"]))
    if gold.get("row_override"):
        override = json.loads((FIXTURES / gold["row_override"]).read_text("utf-8"))
        players = [override if r["id"] == override["id"] else r
                   for r in run.inputs["players"]]
        run = _with_inputs(run, {**run.inputs, "players": players})
    if gold["item"] == "J1":
        return J1.format(window=window(run)) + "\n\nROWS:\n" + "\n".join(
            j1_material(run, gold["ids"]))
    if gold["item"] == "J2":
        research = research_at(run_commit(gold["case"]), run.gw, gold["research"])
        return J2.format(window=window(run)) + "\n\nROWS:\n" + "\n".join(
            j2_material(run, research, gold["ids"]))
    return j3_prompt(gold["row"], run)


def run_commit(case_id: str) -> str:
    return replay_case(case_id).commit


def agreement(results: Iterable[tuple[Mapping, JudgeVerdict]]) -> tuple[int, int, bool, list[str]]:
    """(J3 agreed, J3 total, every J1/J2 agreed, disagreements)."""
    j3_agree = j3_total = 0
    others_ok = True
    wrong = []
    for gold, verdict in results:
        agreed = verdict.passed == (gold["gold"] == "PASS")
        if not agreed:
            wrong.append(f"{gold['item']} {gold['label']}: gold {gold['gold']}, judge "
                         f"{'PASS' if verdict.passed else 'FAIL: ' + verdict.reason}")
        if gold["item"] == "J3":
            j3_total += 1
            j3_agree += agreed
        else:
            others_ok &= agreed
    return j3_agree, j3_total, others_ok, wrong


def _with_inputs(run: PlayerRun, inputs: Mapping) -> PlayerRun:
    from dataclasses import replace

    return replace(run, inputs=inputs)


def gold_rows_present(repo: Path = REPO_ROOT) -> list[str]:
    """The J3 gold rows that no longer occur verbatim in the case transcript."""
    from evals.harness.transcript import load_transcript

    missing = []
    for gold in gold_items():
        if gold["item"] != "J3":
            continue
        transcript = load_transcript(replay_case(gold["case"]).fixture)
        text = "".join(appended_text(str(c.input.get("command", "")), BACKLOG) or ""
                       for c in transcript.calls if c.name == "Bash")
        if gold["row"] not in text:
            missing.append(gold["label"])
    return missing
