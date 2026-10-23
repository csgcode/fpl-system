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
