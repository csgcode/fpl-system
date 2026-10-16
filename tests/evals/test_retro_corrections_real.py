"""The corrections digest over the committed retros: the input the retro
analyst's Call 1 reads."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from fpl.corrections import build_digest

REPO = Path(__file__).resolve().parents[2]
RETRO = REPO / "data" / "retro"

pytestmark = pytest.mark.skipif(not (RETRO / "gw5.md").is_file(), reason="data/retro is absent")


def test_digest_defines_every_status_row():
    assert build_digest(RETRO, before_round=6).missing == ()


def test_active_rules_are_c5_and_c7_to_c20():
    digest = build_digest(RETRO, before_round=6)
    assert [rule.number for rule in digest.active] == [5, *range(7, 21)]


def test_digest_output_stays_under_12_kb():
    out = subprocess.run(
        [sys.executable, "-m", "fpl", "corrections", "--gw", "7", "--round", "6",
         "--retro-root", str(RETRO)],
        cwd=REPO, capture_output=True, check=True,
    ).stdout
    assert len(out) < 12_000
