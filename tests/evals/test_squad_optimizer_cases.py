"""Squad-optimizer fixtures and manifests: frozen transcripts pass the
redaction gate, frozen views carry their pins, markets sum as relayed."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.harness.freeze import redaction_findings
from evals.squad_optimizer.cases import (
    EP_CODE,
    GW4_MARKET,
    GW5_MARKET,
    GW6_MARKET,
    LIVE_CASES,
    REPLAY_CASES,
    VIEWS,
)


@pytest.mark.parametrize("case", REPLAY_CASES, ids=lambda c: c.name)
def test_frozen_transcripts_are_clean(case):
    if not case.fixture.is_file():
        pytest.skip("not frozen")
    text = case.fixture.read_text(encoding="utf-8")
    assert redaction_findings(text) == []
    assert str(Path.home()) not in text and "/Users/" not in text


@pytest.mark.parametrize("spec", VIEWS.values(), ids=lambda v: v.id)
def test_frozen_views_carry_their_pins(spec):
    if not spec.path.is_file():
        pytest.skip("not frozen")
    meta = json.loads(spec.path.read_text(encoding="utf-8"))["meta"]
    assert meta["commit"] == spec.commit and meta["gw"] == spec.gw
    assert meta["bootstrap_sha256"] == spec.bootstrap.sha256
    assert meta["ep_code"] == EP_CODE


@pytest.mark.parametrize(("market", "total"), [(GW4_MARKET, 994), (GW5_MARKET, 993),
                                               (GW6_MARKET, 992)])
def test_markets_sum_to_the_relayed_budget(market, total):
    assert sum(market.sell.values()) + market.bank == total
    assert len(market.sell) == 15


def test_the_default_live_set_is_l1_and_l2():
    assert [c.id for c in LIVE_CASES if c.default] == ["L1-gw5", "L2-gw6"]
