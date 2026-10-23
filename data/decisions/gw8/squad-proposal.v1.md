# GW8 Squad Proposal (2026/27) — WILDCARD

Deadline 2026-10-23T17:30:00Z. Horizon GW8–13. Squad from the STATE block of
data/decisions/gw7/final.md; budget = its `team_value` 99.1 (selling prices +
bank, verified by `my-team` at GW7). Sell basis in every `objective` line
below is **unverified** (now_cost): the orchestrator relayed no `my-team`
prices and this agent never runs authenticated commands. On now_cost the CLI
sees Σ sell 99.7 + bank 0.4 = 100.1; the GW7-verified 99.1 is a floor (no held
player's now_cost is below his GW7 selling price), so every squad here is
sized to 99.1, and the bank is quoted on that floor. The finalizer should
confirm against `my-team` as GW7's final did.

**Wildcard. Seven transfers, hit 0. 5-3-2, Haaland (C), Gabriel (V).
Predicted GW8 53.915. Bank £0.5m (floor basis). FT at GW9: 2.**

## Scoring — objective (verbatim)

```
objective gw8 — horizon GW8–GW13; squad from data/decisions/gw7/final.md
sell basis: now_cost — unverified (Σ sell 99.7 + bank 0.4 = 100.1)
baseline: blend 328.050 prior 318.513
```

Plan (`--chip wildcard --moves 1:385,497:597,229:566,423:332,124:12,94:127,106:464`):

```
plan: Raya → Trafford, Dubravka → Suzuki, Tarkowski → Silva, Shaw → Justin, Groß → Saka, Schade → Gomez, Thiago → Wissa — blend +9.800 prior +6.557; bank 1.0; transfers 7 under wildcard (FT unchanged (1)); chip gate: ≥ 6.0 over the greedy plan
  move Raya → Trafford: -0.104 / -0.110 — chip package
  move Dubravka → Suzuki: +0.555 / +0.482 — chip package
  move Tarkowski → Silva: +1.598 / -1.959 — chip package
  move Shaw → Justin: +1.296 / +2.027 — chip package
  move Groß → Saka: +5.818 / +4.494 — chip package
  move Schade → Gomez: +0.091 / +0.222 — chip package
  move Thiago → Wissa: +0.411 / +1.245 — chip package
after plan, best single: none legal
reference (greedy): bank — no move passes its gate
verdict: PASS
GW8 XI 4-3-3 54.010: Trafford, Gabriel, Silva, Richards, Justin, Mbeumo, E.Le Fée, Tavernier, Haaland, Wissa, Barry; captain top 5: Haaland 5.798 0.94, Gabriel 5.080 0.95, Mbeumo 4.932 0.96, Wissa 4.494 0.94, E.Le Fée 4.406 0.94
boundary pairs within 0.25: Justin 3.773 (DefCon 0.161) | Van Hecke 3.565 (0.190) ; Justin 3.773 (DefCon 0.161) | Gomez 3.541 (0.139) ; Barry 3.660 (DefCon 0.008) | Van Hecke 3.565 (0.190) ; Barry 3.660 (DefCon 0.008) | Gomez 3.541 (0.139)
bench: Suzuki 3.223, Van Hecke 3.565, Gomez 3.541, Saka 2.951
```

The `bank 1.0` is on the unverified now_cost basis; on the GW7-verified
floor it is 0.5 (kept players at GW7 selling prices 58.4 + buys 40.2 = 98.6
against team_value 99.1).

Chip gate: the greedy reference is bank (+0.000 / +0.000; no single move
passes the free gate), so the wildcard clears it by +9.800 blend (≥ 6.0) and
+6.557 prior-only (≥ 0).

## Step 1 — budget skeleton

Premiums (> £9m): Haaland 15.7 and Saka 9.6.

| Premium | Kept because |
|---|---|
| Haaland 15.7 (EP6 34.96) | 6.3 EP6 clear of the pool's #2 (B.Fernandes 31.31); the best two unheld attackers a 7.85 + 7.85 split buys (João Pedro 26.37 + Gibbs-White 25.40 = 51.77) must also displace a ~£5m XI member (Gomez 22.86), net ≈ −6.0 EP6; also the GW9 Triple Captain earmark (C5: justified on his own EP, MCI v BHA (H) is the pool's top GW9 λ_att but not the case) |
| Saka 9.6 (EP6 28.64, p_start_gw 0.50/0.85/0.92/0.92/0.92/0.92) | the split graded: Saka + Gomez + Justin → Stach + Barnes + Calafiori (plan H, `--moves 1:385,497:597,229:566,423:8,124:335,94:453,106:464`) scores +7.261 / +5.433, −2.539 blend / −1.124 prior-only against this plan; with the £1.0m leftover spent on Richards → Hill (H2) +7.517 / +6.924, still −2.283 blend. Saka's GW8 row (2.951) is benched; his EP is GW9–13 |

The two-premium skeleton leaves £73.8m for 13 slots; the budget is exhausted
(Σ 99.1 on the floor basis, bank 0.5 only because three kept players sell
below now_cost).

## Step 2 — XI fill by raw EP

Position by position, the best EP6 inside the skeleton and club limits:

- GKP: Trafford 5.0 (21.70, pool #1). Raya (21.66, 6.1) costs £1.1m more for
  −0.04 EP6; sold.
- DEF: Gabriel 28.58 (held), Silva 25.85, Van Hecke 24.30 (held), Richards
  22.70 (held), Justin 22.37. Calafiori 25.67 (6.0) would be the #3 DEF but
  only fits by dropping Van Hecke or Richards for a promoted-club £3.9–4.0
  filler (plan A below).
- MID: Mbeumo 30.43 (held), Saka 28.64, Tavernier 26.95 (held), E.Le Fée
  26.20 (held), Gomez 22.86 (5.0, BHA 7/7 starts; the cheapest MID at
  p_start ≥ 0.93 with EP6 > 22).
- FWD: Haaland 34.96 (held), Barry 25.51 (held), Wissa 25.32 (6.1). Thiago
  25.23 at 7.8 is sold for Wissa (+0.411 / +1.245) to fund the GK pair.

Clubs: ARS 2 (Gabriel, Saka), BOU 2 (Silva, Tavernier), LEE 2 (Trafford,
Justin), MUN 1, TOT 1, CRY 1, SUN 1, BHA 1, MCI 1, EVE 1, NEW 1, AVL 1.

## Step 3 — bench

GK: **rotating pair** Trafford (LEE) + Suzuki (AVL), £5.0m each. The
objective takes the better keeper each GW (T/S/T/S/T/S: 3.574, 3.654, 3.896,
3.563, 3.977, 3.591 = 22.255 v Trafford alone 21.70); Suzuki's package
marginal is +0.555 / +0.482 against the Kinsky-£4.5m single-keeper version
(plan C2, +9.364 / +6.264). Dubravka (p 0.03, dead since GW1) is sold: the
GK2 slot is repaired without a dead body, which the bench-boost earmark
needs.

Outfield bench: every bench player is a nailed starter (p_start_gw[0] ≥ 0.93
except Saka 0.50): Gomez 5.0 (p 0.93), Barry 5.7 (p 0.94), Saka 9.6. No
£4.0–4.5m outfield filler was needed: Justin 4.5 (p 0.95, 22.37) is the
cheapest DEF in the squad and starts.

## Step 4 — swap pass (audit trail)

Single moves without the chip (`objective --gw 8 --free-transfers 1 --bank 0.4`):

```
legal single moves: 1598 (pool 416); top 10 by blend:
  1 | Richards → Silva | +2.301 | -1.562 | bank 0.3 | fails (prior sign flip)
  2 | Schade → Stach | +1.764 | +0.894 | bank 0.6 | fails (blend < 2.0)
  3 | Tarkowski → Silva | +1.741 | -2.077 | bank 1.6 | fails (prior sign flip)
  4 | Tarkowski → Calafiori | +1.711 | +0.272 | bank 0.6 | fails (blend < 2.0)
  5 | Van Hecke → Silva | +1.551 | -1.835 | bank 0.3 | fails (prior sign flip)
  6 | Shaw → Justin | +1.439 | +2.019 | bank 0.2 | fails (blend < 2.0)
  7 | Groß → Stach | +1.382 | +0.535 | bank 0.6 | fails (blend < 2.0)
  8 | Schade → Barnes | +1.263 | +2.765 | bank 0.5 | fails (blend < 2.0)
  9 | Thiago → João Pedro | +1.139 | -0.516 | bank 0.3 | fails (prior sign flip)
  10 | Shaw → Konsa | +1.096 | +0.884 | bank 0.1 | fails (blend < 2.0)
plan: none — blend +0.000 prior +0.000; bank 0.4; transfers 0 (free 1, hits 0); FT next 2
after plan, best single: Richards → Silva +2.301 / -1.562 — fails (prior sign flip)
reference (greedy): bank — no move passes its gate
verdict: PASS
```

No single move passes the free gate, so without the chip the plan is bank
(FT 2 at GW9). Rows for moves the open suggestions name (single moves, no
chip):

| Row | For | blend / prior | Verdict |
|---|---|---|---|
| Richards → Silva (202:566) | S7 (Richards a named faller) | +2.301 / −1.562 | FAIL, prior sign flip |
| Mbeumo → Gibbs-White (427:480) | S7 (Mbeumo a named faller) | −5.326 / −3.776 | FAIL |
| E.Le Fée → Stach (542:335) | S8 (Le Fée a named GW6 buy) | −0.968 / −0.700 | FAIL |

Wildcard packages graded (all `--chip wildcard`, all PASS the 6.0 / 0 gate):

| Plan | Moves | blend / prior | Why not |
|---|---|---|---|
| **C (this plan)** | Raya→Trafford, Dubravka→Suzuki, Tarkowski→Silva, Shaw→Justin, Groß→Saka, Schade→Gomez, Thiago→Wissa | **+9.800 / +6.557** | — |
| A | Raya→Trafford, Dubravka→Walton, Van Hecke→Silva, Tarkowski→Calafiori, Richards→Thomas, Shaw→Diop, Groß→Saka, Schade→Stach, Thiago→Wissa | +10.628 / +3.434 | +0.828 blend over C but −3.123 prior-only. Two package components fail on prior-only (Van Hecke→Silva +1.456 / −1.835, Richards→Thomas −0.134 / −1.864 — the latter negative on blend too) and three of its five DEF/GK buys are promoted-club rows rated ASSUMPTION / HIGH (Thomas COV, Diop IPS, Walton IPS; every fixture banded). C keeps Van Hecke and Richards (both 7/7 starts) instead; the prior-only margin and the uncertainty cost outweigh 0.83 blend. S8 points the same way but is not the decider (gap > 0.5) |
| C2 | C with Kinsky for Suzuki | +9.364 / +6.264 | −0.436 blend, bank 0.5 unspent |
| B | Raya→Trafford, Dubravka→Kinsky, Tarkowski→Calafiori, Shaw→Justin, Groß→Stach, Schade→Gomez, Thiago→Isak | +8.108 / +5.138 | −1.692 blend / −1.419 prior v C; Isak (p 0.88 after one 78' start, MED) is no safer than Saka |
| H | C with Saka+Gomez+Justin → Stach+Barnes+Calafiori | +7.261 / +5.433 | −2.539 / −1.124: the Saka split loses |
| H2 | H + Richards→Hill | +7.517 / +6.924 | −2.283 blend |
| bank (no chip) | none | +0.000 / +0.000 | the wildcard's +9.800 clears the chip gate |

Tarkowski → Silva (+1.598 / −1.959) is the one component of this plan whose
prior-only sign flips. It is kept: Silva is the pool's #2 DEF EP6 (25.85 at
£5.0m, p 0.95, BOU CS rank 3), the alternatives that hold on prior
(Calafiori 6.0) do not fit the £99.1 floor with Van Hecke and Richards kept,
and a wildcard package is gated as a whole (C14 binds hits, and the chip
takes none).

After the plan `objective` reports `best single: none legal` — the wildcard
uses no free transfer, so the FT gate is moot (FT 1 unchanged, 2 at GW9).

## Squad

Price = now_cost (buys = purchase price; kept players' GW7 selling prices in
brackets where lower). EP6 = `ep_total6`, GW8 = `ep_gw[0]`.

| Slot | Pos | Player | Id | Club | Price | GW8 EP | EP6 | p_start GW8 | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|
| 1 | GKP | Trafford | 385 | LEE | 5.0 | 3.574 | 21.70 | 0.95 | XI · IN |
| 2 | DEF | Gabriel | 4 | ARS | 7.9 | 5.080 | 28.58 | 0.95 | XI · Vice |
| 3 | DEF | Silva | 566 | BOU | 5.0 | 4.100 | 25.85 | 0.95 | XI · IN |
| 4 | DEF | Richards | 202 | CRY | 4.9 | 4.044 | 22.70 | 0.95 | XI |
| 5 | DEF | Justin | 332 | LEE | 4.5 | 3.773 | 22.37 | 0.95 | XI · IN |
| 6 | DEF | Van Hecke | 112 | TOT | 4.9 | 3.565 | 24.30 | 0.95 | XI |
| 7 | MID | Mbeumo | 427 | MUN | 7.9 | 4.932 | 30.43 | 0.96 | XI |
| 8 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.406 | 26.20 | 0.94 | XI |
| 9 | MID | Tavernier | 68 | BOU | 6.2 (6.0) | 4.351 | 26.95 | 0.93 | XI |
| 10 | FWD | Haaland | 411 | MCI | 15.7 (15.5) | 5.798 | 34.96 | 0.94 | XI · Captain |
| 11 | FWD | Wissa | 464 | NEW | 6.1 | 4.494 | 25.32 | 0.94 | XI · IN |
| 12 | GKP | Suzuki | 597 | AVL | 5.0 | 3.223 | 20.74 | 0.95 | Bench GK · IN |
| 13 | MID | Gomez | 127 | BHA | 5.0 | 3.541 | 22.86 | 0.93 | Bench 1 · IN |
| 14 | FWD | Barry | 249 | EVE | 5.7 (5.6) | 3.660 | 25.51 | 0.94 | Bench 2 |
| 15 | MID | Saka | 12 | ARS | 9.6 | 2.951 | 28.64 | 0.50 | Bench 3 · IN |
| | | **Total** | | | **99.1** (98.6 floor) | | | | |

2 GKP / 5 DEF / 5 MID / 3 FWD. Max club count 2.

## Starting XI — 5-3-2

The objective's best GW8 XI is the 4-3-3 above (54.010 with captain). C20
applies C8's tie-break at the XI/bench boundary: Barry 3.660 (DefCon share
0.008) and Van Hecke 3.565 (0.190) are 0.095 apart, inside the 0.25 band, so
Van Hecke starts and Barry sits (−0.095 EP). After the swap every remaining
boundary pair inside 0.25 already favours the XI player on DefCon share:
Justin 3.773 (0.161) v Barry 3.660 (0.008), Justin v Gomez 3.541 (0.139),
Van Hecke (0.190) v Barry (0.008).

| Slot | Player | Pos | GW8 fixture | GW8 EP |
|---:|---|---|---|---:|
| 1 | Trafford | GKP | SUN (A) | 3.574 |
| 2 | Gabriel (V) | DEF | EVE (H) | 5.080 |
| 3 | Silva | DEF | MUN (A) | 4.100 |
| 4 | Richards | DEF | NEW (H) | 4.044 |
| 5 | Justin | DEF | SUN (A) | 3.773 |
| 6 | Van Hecke | DEF | CHE (A) | 3.565 |
| 7 | Mbeumo | MID | BOU (H) | 4.932 |
| 8 | E.Le Fée | MID | LEE (H) | 4.406 |
| 9 | Tavernier | MID | MUN (A) | 4.351 |
| 10 | Haaland (C) | FWD | AVL (A) | 5.798 |
| 11 | Wissa | FWD | CRY (A) | 4.494 |
| | XI total | | | 48.117 |
| | + captain | | | 5.798 |
| | **Predicted GW8** | | | **53.915** |

No XI row is a promoted-club fixture (C12 defensive rule: n/a this GW).

## Captain and vice

Top 5 in the XI by single-GW EP, undiscounted (`objective` captain line):

| Rank | Player | GW8 EP | p_start_gw[0] |
|---:|---|---:|---:|
| 1 | **Haaland** (C) | 5.798 | 0.94 |
| 2 | Gabriel (V) | 5.080 | 0.95 |
| 3 | Mbeumo | 4.932 | 0.96 |
| 4 | Wissa | 4.494 | 0.94 |
| 5 | E.Le Fée | 4.406 | 0.94 |

Captain Haaland, 0.718 clear of Gabriel — outside the 0.5 tiebreak band, so
EP decides. Vice Gabriel: 0.148 over Mbeumo, inside the band, both
p_start_gw[0] ≥ 0.85, so the higher EP holds; Gabriel's EVE (H) row is not
banded.

## Bench order

| Slot | Player | Pos | GW8 EP | p_start | DefCon share |
|---:|---|---|---:|---:|---:|
| 12 | Suzuki | GKP | 3.223 | 0.95 | — |
| 13 | Gomez | MID | 3.541 | 0.93 | 0.139 |
| 14 | Barry | FWD | 3.660 | 0.94 | 0.008 |
| 15 | Saka | MID | 2.951 | 0.50 | — |

Gomez ahead of Barry: 0.119 apart, inside C8's band, higher DefCon floor
share first. Saka last: 0.59 below Gomez and a 50% flag.

Bench check: none

## Transfers (wildcard, cost 0)

| Out | Id | Sell (GW7 verified / now_cost) | In | Id | Buy |
|---|---:|---:|---|---:|---:|
| Raya (ARS, GKP) | 1 | 6.0 / 6.1 | Trafford (LEE, GKP) | 385 | 5.0 |
| Dubravka (TOT, GKP) | 497 | 4.0 / 4.0 | Suzuki (AVL, GKP) | 597 | 5.0 |
| Tarkowski (EVE, DEF) | 229 | 6.1 / 6.2 | Silva (BOU, DEF) | 566 | 5.0 |
| Shaw (MUN, DEF, status i) | 423 | 4.3 / 4.3 | Justin (LEE, DEF) | 332 | 4.5 |
| Groß (BHA, MID) | 124 | 5.9 / 6.2 | Saka (ARS, MID) | 12 | 9.6 |
| Schade (BRE, MID) | 94 | 6.2 / 6.2 | Gomez (BHA, MID) | 127 | 5.0 |
| Thiago (BRE, FWD) | 106 | 7.8 / 7.8 | Wissa (NEW, FWD) | 464 | 6.1 |
| | | 40.3 / 40.8 | | | 40.2 |

Bank after: 0.4 + 40.3 − 40.2 = **0.5** on the GW7-verified basis (the CLI's
1.0 is now_cost). Deadline is today, so no price change lands before the
POST; the plan-builder's `purchase_price_at_plan` audit covers drift anyway.

Gate ids: 385,597,4,566,112,202,332,427,12,68,542,127,411,249,464

## Chips

`chip: wildcard` — set-1 wildcard, window GW2–19 (bootstrap `chips`),
unused, clears the gate (+9.800 ≥ 6.0 blend, +6.557 ≥ 0 prior-only over the
greedy plan, which is bank). No blank or double in GW8–13 (fixture analyst),
so nothing in the schedule argues for holding it; S6's window ends this GW.

Provisional chip plan: 3xc GW9 (Haaland v BHA (H); C5: on his own EP, MCI
λ_att 2.09 supports but does not carry it), freehit GW16 (placeholder),
bboost GW19 (placeholder; GK2 now playing, so the earmark is live). All inside
the set-1 windows (3xc / bboost GW1–19, freehit GW2–19).

## Rationale and rejected alternatives

- Of 1598 legal single moves none passes the free gate (best blend +2.301
  with a prior sign flip; best gate-shaped move Schade → Stach +1.764 <
  2.0), so the non-chip plan is bank at +0.000. The wildcard package scores
  +9.800 / +6.557 and clears the chip gate by 3.8 on blend.
- Where the gain comes from: Groß → Saka +5.818 / +4.494 is the single
  largest component; Tarkowski → Silva, Shaw → Justin and Dubravka → Suzuki
  each add 0.5–1.6; Thiago → Wissa and Schade → Gomez are small positives
  that fund the structure; Raya → Trafford is −0.104 but frees £1.1m.
- Plan A (+10.628 / +3.434) is the highest blend found and is rejected on
  the prior-only margin (−3.1 against this plan), two components that fail
  on prior-only (one negative on blend), and three promoted-club buys at
  HIGH uncertainty — see the package table.
- Dead bench repaired: Dubravka (p 0.03) and Shaw (status i, 0%) both leave.
- Template exposure after: unheld > 30% still includes João Pedro,
  Calafiori, Rogers, De Cuyper, Cherki, B.Fernandes.
- Risks: Saka d 50% (thigh) — his GW8 row is benched, the EP6 prices the
  0.50/0.85 ramp, and the freshness gate re-checks him; Silva's prior-only
  sign flip; Justin v Van Hecke v Barry sit 0.2 apart at the boundary, so a
  single news item can reorder the back line.

## Suggestions

Read data/suggestions.md through S8

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 6 | followed | both halves now complete: Ndiaye → Groß and Anderson → Schade inside the +14.449 blend / +5.210 prior-only triple; Ndiaye's marginal +2.503 / +0.665 and Anderson's +2.488 / +0.757 each clear the 2.0 gate on their own, so the steer broke no tie and the optimizer reached it unaided; EP6 delta of the row itself 0.00. The GW5 ledger's "Ndiaye half completed" was false in fact (never POSTed) and is superseded here |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |
| S3 | 6 | followed | Ndiaye → Groß made; marginal +2.503 blend / +0.665 prior against the plan without this sale (Scott + Anderson → E.Le Fée + Schade, +11.946 / +4.545), so the below-threshold clause was not needed |
| S4 | 6 | followed | Anderson → Schade made; marginal +2.488 blend / +0.757 prior against the plan without this sale (Scott + Ndiaye → E.Le Fée + Groß, +11.961 / +4.453); clears the gate on both readings, below-threshold clause not needed |
| S5 | 6 | followed | Scott → E.Le Fée made; EP6 0.00 for GW6–11 (status i, 0%); marginal +2.503 / +0.675 against the plan without this sale (Ndiaye + Anderson → E.Le Fée + Schade, +11.946 / +4.535) |
| S6 | 8 | followed | wildcard played at GW8, the timing the row left open: the package +9.800 blend / +6.557 prior-only clears the chip gate against bank (+0.000); EP per GW over GW8–13 rises from 54.68 to 56.31 (337.85 / 6, captain included); not taken: 60 per GW stays unreachable — the best package found (plan A) is 338.68 / 6 = 56.45 |
| S7 | 7 | standing | honoured: the wildcard sells Thiago (net faller at GW7, sold at 7.8 before a drop), Schade (the squad's largest faller) and Shaw (status i); of the named fallers still held, Richards → Silva +2.301 / −1.562 and Mbeumo → Gibbs-White −5.326 / −3.776 both FAIL as single moves and neither is within 0.5 of any plan, so no in-band tie to settle; EP6 delta of the row 0.00; policy stays live for GW9 |
| S8 | 7 | standing | honoured: six of the seven buys are unbroken-streak starters at p_start 0.93–0.95 (Trafford 6/6 × 90, Suzuki, Silva, Justin, Gomez 7/7, Wissa); the one flagged buy, Saka (d 50%), is the pool's #3 MID EP6 and his split (plan H) loses 2.539 blend / 1.124 prior-only, outside the 0.5 band, so the steer could not override it; the GW6 buys Groß and Schade are sold, E.Le Fée held (E.Le Fée → Stach −0.968 / −0.700 FAIL); between plans A and C the steer points to C (Richards and Van Hecke, 7/7 starts, kept over Thomas and Diop) but the 0.828 blend gap is outside the band, so the decider is the prior-only margin, not this row; EP6 delta of the row 0.00 |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW9 deadline: 1 unchanged under the wildcard, 1 accrues.
# team_value and bank on the GW7-verified selling-price basis (my-team not relayed this cycle): kept players at GW7 sell prices 58.4 + buys at purchase 40.2 = 98.6, bank 0.5. now_cost basis would read bank 1.0.
gw: 8
team_id: 8455344
team_value: 99.1
bank: 0.5
free_transfers_banked: 2
chip: wildcard
chips_used: []
transfers_made:
  - {out: Raya, in: Trafford, cost: 0}
  - {out: Dubravka, in: Suzuki, cost: 0}
  - {out: Tarkowski, in: Silva, cost: 0}
  - {out: Shaw, in: Justin, cost: 0}
  - {out: Groß, in: Saka, cost: 0}
  - {out: Schade, in: Gomez, cost: 0}
  - {out: Thiago, in: Wissa, cost: 0}
chip_plan:
  - {chip: 3xc, gw: 9, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 385, name: Trafford, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: false, vice: true}
  - {id: 566, name: Silva, position: 3, captain: false, vice: false}
  - {id: 202, name: Richards, position: 4, captain: false, vice: false}
  - {id: 332, name: Justin, position: 5, captain: false, vice: false}
  - {id: 112, name: Van Hecke, position: 6, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 7, captain: false, vice: false}
  - {id: 542, name: E.Le Fée, position: 8, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 9, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 10, captain: true, vice: false}
  - {id: 464, name: Wissa, position: 11, captain: false, vice: false}
  - {id: 597, name: Suzuki, position: 12, captain: false, vice: false}
  - {id: 127, name: Gomez, position: 13, captain: false, vice: false}
  - {id: 249, name: Barry, position: 14, captain: false, vice: false}
  - {id: 12, name: Saka, position: 15, captain: false, vice: false}
```
