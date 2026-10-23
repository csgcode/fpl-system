"""The repo's committed gate records against the code and the docs: the
shipped model is the one the records say passed, and the gate table in
docs/ep-model.md is the one the records render."""

from __future__ import annotations

from pathlib import Path

import pytest

from fpl import gates
from fpl.ep import DEFAULT_CONFIG, ModelConfig

REPO = Path(__file__).resolve().parent.parent
GATES_ROOT = REPO / "data" / "model" / "gates"
COMBINED = GATES_ROOT / "combined.json"
EP_MODEL_DOC = REPO / "docs" / "ep-model.md"


@pytest.mark.parametrize("combined", [pytest.param(
    COMBINED, id="combined-record" if COMBINED.exists() else "no-combined-record-yet")])
def test_default_config_matches_gate_records(combined):
    if not combined.exists():
        return
    record = gates.read_record(GATES_ROOT, gates.COMBINED)
    assert DEFAULT_CONFIG == ModelConfig(**record.shipped_config)


def test_ep_model_gate_block_matches_records():
    block = gates.block(EP_MODEL_DOC.read_text(encoding="utf-8"))
    assert block.strip() == gates.render(gates.load_records(GATES_ROOT)).strip()


def test_manifest_starts_with_the_baseline_entry():
    entries = gates.load_manifest(GATES_ROOT / gates.MANIFEST)
    assert entries[0] == gates.ManifestEntry(name="baseline", kind="model", argv=())


def test_p4_calibrated_positions_match_record():
    if not COMBINED.exists():
        return
    from fpl import objective
    from fpl.models import Position

    p4 = gates.read_record(GATES_ROOT, gates.COMBINED).comparison["p4"]
    calibrated = frozenset(
        Position[pos] for pos, v in p4.items()
        if v["starters"] is not None and v["starters"]["skill"] is not None
        and v["starters"]["skill"] > 0)
    assert objective.P4_CALIBRATED == calibrated
