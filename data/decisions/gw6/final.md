# GW6 Final (2026/27)

Deadline **2026-10-10T10:00:00Z**. Review verdict **APPROVE** (no HIGH; MED
F1–F3 carried below). No revision loop.

**Three free transfers: Scott → E.Le Fée, Ndiaye → Groß, Anderson → Schade.
Hit 0. Bank £0.3m. No chip. 3-5-2, Haaland (C), Mbeumo (V). Predicted GW6
56.18; GW6–8 mean 56.37.**

## Freshness gate

`fpl flags --gw 6` refreshed at 2026-10-09 14:17:28 UTC on all 15 selected
ids, compared against `data/raw/gw6/players-slim.csv` (bootstrap fetched
2026-10-09 13:31 UTC, under 24h old).

| Result | Detail |
|---|---|
| **PASS** | No change to `status`, `chance_of_playing_next_round` or `news` for any selected player. All 15 `a`; Shaw carries chance 100 and a stale `news_added` (2026-09-11) in both readings, unchanged. |

## Verified entry state

`fpl my-team --gw 6` (authenticated): bank 0.0, 3 free transfers, selling-
price sum 99.2, all four set-1 chips available.

## Squad — predicted points (calibration record)

`GW6 EP` = `ep_gw[0]`, `EP6` = `ep_total6` from `data/analysis/gw6/players-{pos}.json`;
`Prior6` = the optimizer's C14 prior-only rerun.

| Slot | Pos | Player | Id | Club | Sell | GW6 EP | EP6 | Prior6 | p_start | Unc | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---|---|
| 1 | GKP | Raya | 1 | ARS | 6.0 | 3.604 | 21.95 | 21.03 | 0.94 | LOW | XI |
| 2 | DEF | Tarkowski | 229 | EVE | 6.1 | 4.734 | 25.81 | 23.45 | 0.92 | LOW | XI |
| 3 | DEF | Gabriel | 4 | ARS | 8.0 | 4.671 | 28.36 | 29.98 | 0.93 | LOW | XI |
| 4 | DEF | Thiaw | 445 | NEW | 5.0 | 3.881 | 21.30 | 22.67 | 0.90 | LOW | XI |
| 5 | MID | Mbeumo | 427 | MUN | 7.9 | 5.230 | 30.21 | 27.33 | 0.93 | LOW | XI · Vice |
| 6 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.687 | 26.93 | 24.77 | 0.92 | LOW | XI · IN |
| 7 | MID | Tavernier | 68 | BOU | 6.0 | 4.618 | 27.72 | 25.45 | 0.91 | LOW | XI |
| 8 | MID | Groß | 124 | BHA | 5.9 | 4.427 | 26.58 | 22.17 | 0.93 | LOW | XI · IN |
| 9 | MID | Schade | 94 | BRE | 6.2 | 4.427 | 26.57 | 24.73 | 0.93 | LOW | XI · IN |
| 10 | FWD | Haaland | 411 | MCI | 15.5 | 5.786 | 38.36 | 35.02 | 0.93 | LOW | XI · Captain |
| 11 | FWD | Barry | 249 | EVE | 5.6 | 4.327 | 25.31 | 22.49 | 0.91 | LOW | XI |
| 12 | GKP | Dubravka | 497 | TOT | 4.0 | 0.106 | 0.67 | 0.67 | 0.03 | HIGH | Bench GK |
| 13 | FWD | Thiago | 106 | BRE | 7.8 | 4.209 | 25.37 | 27.07 | 0.92 | LOW | Bench 1 |
| 14 | DEF | Richards | 202 | CRY | 4.9 | 3.509 | 20.95 | 22.02 | 0.90 | LOW | Bench 2 |
| 15 | DEF | Shaw | 423 | MUN | 4.3 | 2.673 | 13.16 | 13.58 | 0.75 | MED | Bench 3 |
| | | **Total** | | | **98.9** | | **359.35** | 330.43 | | | |

2 GKP / 5 DEF / 5 MID / 3 FWD. Club counts ARS 2, EVE 2, MUN 2, BRE 2, all
others 1.

## Starting XI — 3-5-2

| Slot | Player | Pos | GW6 fixture | GW6 EP |
|---:|---|---|---|---:|
| 1 | Raya | GKP | LEE (H) | 3.604 |
| 2 | Tarkowski | DEF | HUL (A) | 4.734 |
| 3 | Gabriel | DEF | LEE (H) | 4.671 |
| 4 | Thiaw | DEF | COV (A) | 3.881 |
| 5 | Mbeumo (V) | MID | TOT (H) | 5.230 |
| 6 | E.Le Fée | MID | BHA (H) | 4.687 |
| 7 | Tavernier | MID | CHE (A) | 4.618 |
| 8 | Groß | MID | SUN (A) | 4.427 |
| 9 | Schade | MID | AVL (A) | 4.427 |
| 10 | Haaland (C) | FWD | LIV (A) | 5.786 |
| 11 | Barry | FWD | HUL (A) | 4.327 |
| | XI total | | | 50.392 |
| | + captain | | | 5.786 |
| | **Predicted GW6** | | | **56.178** |

## Captain and vice

- **Captain Haaland** (5.786) — leads Mbeumo by 0.556 among owned players,
  outside the 0.5 tie band, and holds on prior-only (5.287 v 4.730).
- **Vice Mbeumo** (5.230) — second-highest EP, different fixture.

## Bench order

| Slot | Player | Pos | GW6 EP |
|---:|---|---|---:|
| 12 | Dubravka | GKP | 0.106 |
| 13 | Thiago | FWD | 4.209 |
| 14 | Richards | DEF | 3.509 |
| 15 | Shaw | DEF | 2.673 |

## Transfers

| Out | In | Sell | Buy | Cost |
|---|---|---:|---:|---:|
| Scott (BOU, MID, id 69) | E.Le Fée (SUN, MID, id 542) | 6.0 | 5.7 | 0 |
| Ndiaye (MCI, MID, id 237) | Groß (BHA, MID, id 124) | 5.8 | 5.9 | 0 |
| Anderson (MCI, MID, id 481) | Schade (BRE, MID, id 94) | 6.3 | 6.2 | 0 |

Hit cost 0. Sells 18.1, buys 17.8, bank 0.0 → 0.3. Three FTs used; 1 accrues
for GW7. Package gain +14.449 blend / +5.210 prior-only over GW6–11.

**Execution order:** transfers first, then the lineup — the XI names three
players the entry does not yet own. Per F1, POST the transfers **before the
overnight price run (~01:30 UTC 2026-10-10)**, not on deadline morning.

**Price-break fallback (F1).** If price moves leave the bank short and
`make-transfers` refuses: replace Groß with **Stach** (LEE, MID, £6.0m,
id 335) — E.Le Fée + Stach + Schade, +13.293 blend / +5.459 prior-only; this
needs Scott and Ndiaye to hold price. Failing that, Stach in place of Schade
(E.Le Fée + Groß + Stach, +13.308, cost 99.2). Either fallback is a change to
this plan and needs a new final.md STATE and plan.json before any POST.

## Chips

`chip: null` this GW. No chips used. Windows from bootstrap: wildcard /
freehit GW2–19, bboost / 3xc GW1–19.

| Chip | Earmark (provisional) | Basis |
|---|---|---|
| wildcard | GW8 | GK2 / DEF5 repairs, Saka / Guéhi upgrades, re-priced on two more rounds. GW6 wildcard rejected: +1.96 over the full path in the best-blend build only (which leans on HIGH-uncertainty promoted-club defenders), −1.57 on prior-only, +1.26 per GW on GW6–8 below the 2-per-GW switch rule. The forecast +8.0 for the GW8 rebuild will shrink once its HIGH rows (Davis, Greaves, Simms) are priced on real minutes |
| 3xc | GW9 | Haaland v BHA (H), 6.87; GW11 FUL (H) tied fallback |
| freehit | GW16 | placeholder |
| bboost | GW19 | blocked until the GW8 wildcard repairs GK2 and DEF5 |

## Accepted risks

| # | Risk | Detail |
|---|---|---|
| R1 | GK2 dead, DEF5 weak | Dubravka 0.106 (p_start 0.03), Shaw 2.673 (0.75 MED). No reachable fix clears the gate; routed to the GW8 wildcard. Richards covers one DEF absence |
| R2 | Three midfield buys on one week's EP | All LOW at p_start ≥ 0.92, 5/5 starts. The GW8 wildcard re-prices them at no transfer cost |
| R3 | Template exposure (widened per F3) | Unheld: **João Pedro (CHE, 63.6% owned)** — the most-owned player after Haaland; Thiago → João Pedro is the best paid single at +1.636 gross / −1.808 prior-only, below the 6.0 hit gate and sign-flipping; he is `d` 75% (knee), p_start 0.68 HIGH, 0 minutes in GW5. **Rogers (CHE, 41.6%)**. B.Fernandes (ties Haaland on GW6 EP), Saka, Calafiori. A João Pedro haul is the largest rank-volatility event the squad is exposed to. Named for the GW8 wildcard |
| R4 | Captain fixture | Haaland at LIV (A) is his window-worst row; lead over Mbeumo still clears the band on both readings |
| R5 | Execution | The GW5 plan was never POSTed. The XI cannot be set until the three transfers land; a declined transfer leaves Scott (0 EP) in the carried-forward GW4 lineup |
| R6 | Overnight price exposure (F1) | Groß (+2 this event, 1.09m in) and Schade (+1) rising; Scott and Ndiaye (−1) falling. Groß +0.1, Schade +0.1, Scott −0.1, Ndiaye −0.1 → bank −0.1 and `make-transfers` refuses. Mitigation: execute today; fallback Stach (above) |
| R7 | Groß recency (F2) | EP6 26.58 v prior-only 22.17; 7 returns on 2.63 xG+xA and 9 bonus in five starts. Bonus regressing to prior rate takes him to about 23.8, below Stach (25.09). Held: penalty taker, 90 × 5, 31.9% owned, package positive on prior-only. Stach is the named alternative at the GW8 wildcard |

## Rationale summary

Scott is out injured for the whole window (0.00 EP). Ndiaye's phased minutes
make him the weakest midfielder on both readings. Anderson's sale clears the
gate on its own marginal (+2.488 / +0.757). The triple is the best on blend
and positive on prior-only; each sale clears 2.0 alone. No paid fourth move
comes near the hit gate. The wildcard waits to GW8 (see Chips).

Review findings F4–F11 are LOW and need no action.

## Suggestions

Read data/suggestions.md through S6

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 6 | followed | both halves now complete: Ndiaye → Groß and Anderson → Schade inside the +14.449 blend / +5.210 prior-only triple; Ndiaye's marginal +2.503 / +0.665 and Anderson's +2.488 / +0.757 each clear the 2.0 gate on their own, so the steer broke no tie and the optimizer reached it unaided; EP6 delta of the row itself 0.00. The GW5 ledger's "Ndiaye half completed" was false in fact (never POSTed) and is superseded here |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |
| S3 | 6 | followed | Ndiaye → Groß made; marginal +2.503 blend / +0.665 prior against the plan without this sale (Scott + Anderson → E.Le Fée + Schade, +11.946 / +4.545), so the below-threshold clause was not needed |
| S4 | 6 | followed | Anderson → Schade made; marginal +2.488 blend / +0.757 prior against the plan without this sale (Scott + Ndiaye → E.Le Fée + Groß, +11.961 / +4.453); clears the gate on both readings, below-threshold clause not needed |
| S5 | 6 | followed | Scott → E.Le Fée made; EP6 0.00 for GW6–11 (status i, 0%); marginal +2.503 / +0.675 against the plan without this sale (Ndiaye + Anderson → E.Le Fée + Schade, +11.946 / +4.535) |
| S6 | 6 | standing | honoured: the three free transfers lift GW6–8 from 53.99 to 56.37 per GW (+2.38); the wildcard is timed at GW8 on the fresh EP — GW6 wildcard scores 57.63 (+1.26 per GW on GW6–8) but +1.96 over the full path against 3 FTs + GW8 wildcard and −1.57 on prior-only, below the research's own 2-per-GW switch rule. 60 is unreachable: no-budget ceiling 59.61 over GW6–8 at £113.6m, best legal 57.63. Completes `followed` at the GW8 wildcard, or `expired` after GW8 |

## STATE

```yaml
# free_transfers_banked = FTs available at the GW7 deadline: 3 at GW6, 3 used, 1 accrues.
# team_value on the selling-price basis (my-team): squad sell 98.9 + bank 0.3 = 99.2.
gw: 6
team_id: 8455344
team_value: 99.2
bank: 0.3
free_transfers_banked: 1
chip: null
chips_used: []
transfers_made:
  - {out: Scott, in: E.Le Fée, cost: 0}
  - {out: Ndiaye, in: Groß, cost: 0}
  - {out: Anderson, in: Schade, cost: 0}
chip_plan:
  - {chip: wildcard, gw: 8, status: provisional}
  - {chip: 3xc, gw: 9, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 1, name: Raya, position: 1, captain: false, vice: false}
  - {id: 229, name: Tarkowski, position: 2, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 3, captain: false, vice: false}
  - {id: 445, name: Thiaw, position: 4, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 5, captain: false, vice: true}
  - {id: 542, name: E.Le Fée, position: 6, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 7, captain: false, vice: false}
  - {id: 124, name: Groß, position: 8, captain: false, vice: false}
  - {id: 94, name: Schade, position: 9, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 10, captain: true, vice: false}
  - {id: 249, name: Barry, position: 11, captain: false, vice: false}
  - {id: 497, name: Dubravka, position: 12, captain: false, vice: false}
  - {id: 106, name: Thiago, position: 13, captain: false, vice: false}
  - {id: 202, name: Richards, position: 14, captain: false, vice: false}
  - {id: 423, name: Shaw, position: 15, captain: false, vice: false}
```
