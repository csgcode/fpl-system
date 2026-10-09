"""The fake server's starting my-team for a case: the previous gameweek's
picks at the case commit, with the selling and purchase prices the real
my-team read showed during GW6 (the squad was the same 15 in GW4–GW6)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from evals.team_executor.cases import LiveCase, case_files, git_show

# element → (selling_price, purchase_price), in tenths of £m.
PRICES: Mapping[int, tuple[int, int]] = {
    1: (60, 60), 4: (80, 80), 229: (61, 60), 202: (49, 50), 68: (60, 60),
    427: (79, 80), 69: (60, 60), 237: (58, 60), 411: (155, 155), 106: (78, 80),
    249: (56, 55), 497: (40, 40), 481: (63, 65), 445: (50, 50), 423: (43, 45),
}
FREE_TRANSFERS: Mapping[int, int] = {4: 1, 5: 2, 6: 3}
CHIPS = ("bboost", "3xc", "wildcard", "freehit")
TEAM_VALUE = 998


def build_my_team(
    picks: Sequence[Mapping], gw: int, *, swaps: Sequence[tuple[int, int]] = (),
    now_costs: Mapping[int, int] | None = None,
) -> dict:
    """`swaps` replaces (out, in) in place, as a transfer made on the website
    would; the incoming player is bought and valued at `now_costs`."""
    swapped = dict(swaps)
    built = []
    for pick in picks:
        element = pick["element"]
        if element in swapped:
            incoming = swapped[element]
            if now_costs is None or incoming not in now_costs:
                raise ValueError(f"no price for incoming element {incoming}")
            sell = buy = now_costs[incoming]
            element = incoming
        else:
            sell, buy = PRICES[element]
        built.append({
            "element": element,
            "position": pick["position"],
            "selling_price": sell,
            "purchase_price": buy,
            "multiplier": pick.get("multiplier", 1),
            "is_captain": pick["is_captain"],
            "is_vice_captain": pick["is_vice_captain"],
        })
    return {
        "picks": built,
        "chips": [{"name": name, "status_for_entry": "available"} for name in CHIPS],
        "transfers": {"bank": 0, "value": TEAM_VALUE, "limit": FREE_TRANSFERS[gw],
                      "made": 0, "cost": 4},
    }


def case_my_team(case: LiveCase, *, base: bool = False) -> dict:
    picks = json.loads(git_show(case.commit, case.picks))["picks"]
    bootstrap = json.loads(case_files(case, base=True)[case.bootstrap])
    now_costs = {p["id"]: p["now_cost"] for p in bootstrap["elements"]}
    return build_my_team(picks, case.gw, swaps=() if base else case.swaps,
                         now_costs=now_costs)
