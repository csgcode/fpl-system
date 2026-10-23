"""Worked examples in docs/ep-model.md against the code: a marker
`<!-- example: <function> <arg>=<value> -->` names the call, and the line after
it must state the value that call returns with the current constants, to 2 dp."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fpl.ep import prior_weight

EP_MODEL_DOC = Path(__file__).resolve().parent.parent / "docs" / "ep-model.md"

EXAMPLES = {
    "prior_weight minutes=180": lambda: prior_weight(180),
}


def _line_after(text: str, marker: str) -> str:
    lines = text.splitlines()
    hits = [i for i, line in enumerate(lines) if line.strip() == f"<!-- example: {marker} -->"]
    assert len(hits) == 1, f"expected one '{marker}' example marker, found {len(hits)}"
    assert hits[0] + 1 < len(lines), f"'{marker}' marker is the last line"
    return lines[hits[0] + 1]


@pytest.mark.parametrize("marker", sorted(EXAMPLES))
def test_ep_model_worked_examples(marker):
    line = _line_after(EP_MODEL_DOC.read_text(encoding="utf-8"), marker)
    expected = f"{EXAMPLES[marker]():.2f}"
    numbers = re.findall(r"(?<![\d.])\d+\.\d+(?![\d.])", line)
    assert expected in numbers, f"line after '{marker}' states {numbers}, code gives {expected}: {line!r}"


def test_ep_model_names_only_gate_records_that_exist():
    text = EP_MODEL_DOC.read_text(encoding="utf-8")
    named = set(re.findall(r"data/model/gates/([\w.-]+\.json)", text))
    gates_root = EP_MODEL_DOC.parent.parent / "data" / "model" / "gates"
    assert {"drop-promoted.json", "drop-no-history.json", "no-history-k.json"} <= named
    assert sorted(n for n in named if not (gates_root / n).exists()) == []


GATES_ROOT = EP_MODEL_DOC.parent.parent / "data" / "model" / "gates"

# (record, field, value the prose relies on, a phrase of that prose). A re-run
# that changes the value fails here, so the prose is edited with it.
PROSE_FACTS = [
    ("prior-weight", "verdict", "FAIL", "K = 600 is the value the `prior-weight` gate kept"),
    ("no-history-k", "verdict", "FAIL", "the separate K did not beat the shared one"),
    ("drop-promoted", "hypothesis", "not supported",
     "removing the discounts did not make those players' predictions better"),
    ("drop-no-history", "hypothesis", "not supported",
     "removing the discounts did not make those players' predictions better"),
    ("finishing", "verdict", "FAIL", "The multiplier is off (`FINISHING_K = None`"),
    ("persistence", "significant", False, "There is no form term."),
]


def _prose() -> str:
    return " ".join(EP_MODEL_DOC.read_text(encoding="utf-8").split())


@pytest.mark.parametrize("name, field, value, phrase", PROSE_FACTS,
                         ids=[f"{name}.{field}" for name, field, *_ in PROSE_FACTS])
def test_ep_model_prose_matches_its_gate_record(name, field, value, phrase):
    from fpl import gates

    record = gates.read_record(GATES_ROOT, name)
    assert record is not None, f"data/model/gates/{name}.json is missing"
    assert getattr(record, field) == value, (
        f"{name}.json {field} is now {getattr(record, field)!r}: edit the docs/ep-model.md "
        f"prose that says {phrase!r}")
    assert phrase in _prose()


def test_ep_model_names_the_calibrated_p4_positions():
    from fpl import gates, objective
    from fpl.models import Position

    p4 = gates.read_record(GATES_ROOT, gates.COMBINED).comparison["p4"]
    from_record = [pos for pos, v in p4.items()
                   if v["starters"] is not None and (v["starters"]["skill"] or 0) > 0]
    assert frozenset(Position[pos] for pos in from_record) == objective.P4_CALIBRATED
    order = [p.name for p in Position]
    names = sorted(from_record, key=order.index)
    listed = ", ".join(names[:-1]) + f" and {names[-1]}" if len(names) > 1 else names[0]
    assert f"The calibrated positions are {listed}." in _prose()
