# GW9 Squad Proposal (2026/27) — BANK the free transfer, TRIPLE CAPTAIN Haaland

First optimizer run of the cycle (an earlier run was stopped before it wrote
anything). Weekly branch: squad from the STATE block of
data/decisions/gw8/final.md; players files `model 64ad9c9c` (MID regenerated
with the B.Fernandes team news); fixtures from data/analysis/gw9/.
Deadline 2026-10-31 11:00 UTC. Horizon GW9–GW14; no blank, no double.

## Summary

| Item | Decision |
|---|---|
| Transfers | none — bank the free transfer (1 → 2 at the GW10 deadline) |
| Chip | **3xc on Haaland** (set 1, window GW1–19) |
| Captain / vice | Haaland 6.116 / Tavernier 4.643 (vice tie v Mbeumo 4.839 broken by S8, see Captaincy) |
| XI | 3-4-3: Trafford; Gabriel, Hill, Van Hecke; Mbeumo, Tavernier, E.Le Fée, Barnes; Haaland, Barry, Isak |
| Bench | Kinsky, Gomez, Justin, Calafiori |
| Predicted GW9 | 55.458 XI incl. captain double (`objective`), +6.116 from the triple = 61.574 |
| Money | bank 0.1, team_value 99.2 (live `my-team` budget relayed by the orchestrator) |

## Money and free transfers (live account, relayed)

The orchestrator relayed today's `my-team` read: 1 free transfer, bank 0.1,
selling-price sum 99.1, budget 99.2. The optimizer never runs `my-team`, so
the per-player `--sell` list below is a reconstruction: the seven kept
players at their GW7-verified selling prices (53.5) and the eight GW8 buys at
the purchase prices the GW8 POST recorded
(data/executor/gw8/make-transfers-20261023T152430_068797Z.json, 45.6). The
reconstruction sums to 99.1, equal to the relayed selling-price sum. Three
squad prices moved this event (Calafiori −0.1, Kinsky −0.1, Barry −0.1,
Tavernier +0.2), so individual selling prices may differ from the list by
0.1 while the sum still matches; no transfer is proposed, so no POST depends
on them.

Free transfers: the GW8 STATE block forecast 2 at this deadline (1 held
through the wildcard + 1 accrued, per CLAUDE.md "Wildcard/Free Hit do NOT wipe
banked free transfers"). The live account shows 1. The live figure is used
(`--free-transfers 1`); the discrepancy is logged in docs/backlog.md for
triage, not resolved here.

`--sell 4:7.9,112:4.9,427:7.9,68:6.0,542:5.7,411:15.5,249:5.6,385:5.0,496:4.5,8:6.0,60:5.5,332:4.5,453:6.1,127:5.0,379:9.0 --bank 0.1 --free-transfers 1`

## Verification — objective (verbatim)

`uv run python -m fpl objective --gw 9 --sell <list above> --bank 0.1 --free-transfers 1 --moves none`:

```
objective gw9 — horizon GW9–GW14; squad from data/decisions/gw8/final.md
sell basis: relayed (Σ sell 99.1 + bank 0.1 = 99.2)
baseline: blend 339.865 prior 329.329
plan: none — blend +0.000 prior +0.000; bank 0.1; transfers 0 (free 1, hits 0); FT next 2
after plan, best single: Calafiori → Silva +1.797 / -0.085 — fails (prior sign flip)
reference (greedy): bank — no move passes its gate
tie-break move: none within 0.5
tie-break: none in band
verdict: PASS
GW9 XI 3-4-3 55.458: Trafford, Gabriel, Hill, Van Hecke, Mbeumo, Tavernier, E.Le Fée, Barnes, Haaland, Barry, Isak; captain top 5: Haaland 6.116 0.94, Mbeumo 4.839 0.96, Tavernier 4.643 0.93, Gabriel 4.519 0.95, Barry 4.503 0.94
boundary pairs within 0.25: Trafford 3.520 (DefCon 0.000) | Kinsky 3.321 (0.000)
bench: Kinsky 3.321, Gomez 3.583, Justin 3.216, Calafiori 2.594
```

## Step 1 — budget skeleton

Weekly cycle, one free transfer: the skeleton is the GW8 wildcard squad. Two
slots above £9m: Haaland (sell 15.5; EP6 34.47, pool #1 FWD by 6.21 over
Isak) and Isak (sell 9.0; EP6 28.26, pool #2 FWD). Neither is challenged by a
split this week: every Haaland-out and Isak-out single sits below −0.269
blend — none appears in the top 60 legal moves by blend (the 60th is
−0.269), and a two-for-one split needs a hit, which needs +6.0 gross. The
budget is exhausted (bank 0.1).

## Step 2 — XI fill by raw EP

`objective`'s GW9 XI, 3-4-3, 55.458 with the captain doubled. The formation
follows EP: Barry 4.503 (FWD3) beats the fourth defender Calafiori 2.594
(p_start_gw[0] 0.65, hip 75%, hooked at 22' in R8) and Justin 3.216. Club
caps: ARS 2 (Gabriel, Calafiori), BOU 2 (Hill, Tavernier), TOT 2 (Van Hecke,
Kinsky), LEE 2 (Trafford, Justin), MUN 1 (Mbeumo), MCI 1, LIV 1, SUN 1, NEW 1,
BHA 1, EVE 1 — none at 3.

XI/bench boundary (C20): the last XI outfielder is Barnes 4.043, the top
outfield bench row Gomez 3.583, gap 0.460 — outside the 0.25 band, no
DefCon tie-break needed. The only pair `objective` prints inside 0.25 is the
goalkeepers, Trafford 3.520 v Kinsky 3.321, both DefCon 0.000: higher EP
starts.

## Step 3 — bench

Goalkeeper: one playing keeper (Trafford, p_start 0.95 flat, LEE) with a
£4.4m non-rotating backup (Kinsky, TOT, p_start 0.95). No rotation pair:
Trafford's six fixtures carry 22.28 EP6, pool #1, and Kinsky's 19.93 is
pool #6 at £4.4m — a swap would gain at most 0.4 EP in any one GW and the
transfer to build a true pair would fail the gate (every Kinsky-out move is
−0.137 blend).

Outfield bench, ordered by GW9 EP (C8 band 0.25, no pair inside it):

| Slot | Player | Price | p_start GW9 | GW9 EP | DefCon term EP6 | Note |
|---|---|---|---|---|---|---|
| 13 | Gomez | 5.0 | 0.94 | 3.583 | 3.01 | first outfield sub; nailed BHA starter |
| 14 | Justin | 4.5 | 0.95 | 3.216 | 3.36 | gap to Gomez 0.367 > 0.25; the only DEF cover for the 3-DEF XI |
| 15 | Calafiori | 5.9 | 0.65 | 2.594 | 0.69 | gap to Justin 0.622; back to 0.85–0.92 from GW10 |

Both nailed £4.0–4.5m rows (Justin, Kinsky) are already the cheap bench.

## Step 4 — swap pass (audit trail)

`uv run python -m fpl objective --gw 9 … --free-transfers 1 --top 60`, legal
single moves and the top 10 by blend:

```
legal single moves: 1543 (pool 437); top 10 by blend:
  1 | Calafiori → Silva | +1.797 | -0.085 | bank 1.1 | p4₃ - | ret5 2/5 | fails (prior sign flip)
  2 | Van Hecke → Silva | +1.581 | -1.349 | bank 0.0 | p4₃ - | ret5 2/5 | fails (prior sign flip)
  3 | Hill → Silva | +0.779 | -2.610 | bank 0.6 | p4₃ - | ret5 2/5 | fails (prior sign flip)
  4 | Calafiori → Muharemović | +0.317 | -0.139 | bank 1.0 | p4₃ - | ret5 4/5 | fails (prior sign flip)
  5 | Calafiori → De Cuyper | +0.050 | +0.389 | bank 0.8 | p4₃ - | ret5 4/5 | fails (blend < 2.0)
  6 | Calafiori → Vuskovic | -0.079 | -0.457 | bank 0.9 | p4₃ - | ret5 4/5 | fails (prior sign flip)
  7 | Kinsky → M.Bizot | -0.137 | -0.194 | bank 0.1 | p4₃ 0.02 | ret5 0/5 | fails (prior sign flip)
  8 | Kinsky → Petrović | -0.137 | -0.194 | bank 0.1 | p4₃ 0.29 | ret5 2/5 | fails (prior sign flip)
  9 | Kinsky → Forster | -0.137 | -0.194 | bank 0.6 | p4₃ 0.01 | ret5 0/5 | fails (prior sign flip)
  10 | Kinsky → Valdimarsson | -0.137 | -0.194 | bank 0.2 | p4₃ 0.01 | ret5 0/5 | fails (prior sign flip)
tie-break move: none within 0.5
tie-break: none in band
```

Rows 11–23 are Kinsky → <keeper> at −0.137 / −0.194 and rows 24–60 Gomez →
<midfielder> at −0.269 / −0.555: the bench slots score 0 in the objective, so
every such move is a pure loss of EP. No `tie-break group:` line was printed
(no two singles with the same outgoing player within 0.5 blend EP6 pass the
gate).

Only five of 1543 legal singles are positive on blend; the best, Calafiori →
Silva +1.797, is short of the free gate's 2.0 and flips sign prior-only
(−0.085: C14). A hit plan needs +6.0 gross; the two best singles sum to 3.378
and share the incoming player, so no pair reaches it. Banking is the greedy
reference and the plan.

Moves named by open suggestions, graded with `--moves`:

| Row | Move | blend | prior | Verdict (verbatim) |
|---|---|---|---|---|
| S7 (named faller still owned) | Mbeumo → Gibbs-White | −4.365 | −3.988 | `FAIL: Mbeumo → Gibbs-White -4.365 / -3.988 fails the free gate (blend ≥ 2.0, prior ≥ 0); plan gain -4.365 below the blend-only greedy reference +0.000` |
| S7 (current faller) | Calafiori → Silva | +1.797 | −0.085 | `FAIL: Calafiori → Silva +1.797 / -0.085 fails the free gate (blend ≥ 2.0, prior ≥ 0)`; after it the best single is `Barry → Mateta +1.235 / +2.038 — fails (blend < 2.0)` |

Plan lines, verbatim:

```
plan: Mbeumo → Gibbs-White — blend -4.365 prior -3.988; bank 0.1; transfers 1 (free 1, hits 0); FT next 1
  move Mbeumo → Gibbs-White: -4.365 / -3.988 — fails (prior sign flip)
plan: Calafiori → Silva — blend +1.797 prior -0.085; bank 1.1; transfers 1 (free 1, hits 0); FT next 1
  move Calafiori → Silva: +1.797 / -0.085 — fails (prior sign flip)
```

## Man Utd exposure

Mbeumo (MUN, £7.9, p_start 0.96 flat, 90' in R8) is held: he is the pool's #1
MID on EP6 (30.69, 1.96 clear of Tavernier) and no legal move out of him
passes — the best, Mbeumo → Gibbs-White, costs 4.365 blend / 3.988
prior-only. The manager's position is a club-level risk that the model prices
through MUN's ratings (ATT rank 10, turning easier from GW12: Δ Σλ_att +0.81,
the second-largest swing in the window), not a minutes risk for Mbeumo, who
has started every round. S8's "inconsistent club" read is applied where the
spec lets a steer act — the vice tie — and not to a transfer that loses 4.4
EP6.

B.Fernandes is not owned and is not a candidate: at £11.7m he is unreachable
with one free transfer (the largest MID sale, Mbeumo 7.9 + bank 0.1 = 8.0),
and his EP6 26.48 at p_start_gw [0.65, 0.75, 0.80, 0.85, 0.85, 0.85] already
sits below Mbeumo and Tavernier. His all-or-nothing R8 selection risk never
enters the squad.

## Squad

Price = selling price on the reconstructed basis above (sum 99.1); EP6 =
`ep_total6`; GW9 = `ep_gw[0]`; p = `p_start_gw[0]`.

| Pos | Player | Club | Price | p GW9 | GW9 EP | EP6 | Role |
|---|---|---|---|---|---|---|---|
| GKP | Trafford | LEE | 5.0 | 0.95 | 3.520 | 22.28 | XI |
| GKP | Kinsky | TOT | 4.5 | 0.95 | 3.321 | 19.93 | bench 12 |
| DEF | Gabriel | ARS | 7.9 | 0.95 | 4.519 | 29.98 | XI |
| DEF | Hill | BOU | 5.5 | 0.95 | 4.385 | 26.36 | XI |
| DEF | Van Hecke | TOT | 4.9 | 0.95 | 4.189 | 24.26 | XI |
| DEF | Calafiori | ARS | 6.0 | 0.65 | 2.594 | 23.39 | bench 15 |
| DEF | Justin | LEE | 4.5 | 0.95 | 3.216 | 22.51 | bench 14 |
| MID | Mbeumo | MUN | 7.9 | 0.96 | 4.839 | 30.69 | XI |
| MID | Tavernier | BOU | 6.0 | 0.93 | 4.643 | 28.73 | XI, vice |
| MID | E.Le Fée | SUN | 5.7 | 0.94 | 4.405 | 25.86 | XI |
| MID | Barnes | NEW | 6.1 | 0.94 | 4.043 | 23.24 | XI |
| MID | Gomez | BHA | 5.0 | 0.94 | 3.583 | 23.04 | bench 13 |
| FWD | Haaland | MCI | 15.5 | 0.94 | 6.116 | 34.47 | XI, captain (3xc) |
| FWD | Isak | LIV | 9.0 | 0.88 | 4.180 | 28.26 | XI |
| FWD | Barry | EVE | 5.6 | 0.94 | 4.503 | 26.20 | XI |

Squad EP6 sum 389.2 (15 rows, bench included); objective baseline 339.865
blend / 329.329 prior-only (best XI + captain per GW, bench at 0).

## Starting XI — 3-4-3

Trafford; Gabriel, Hill, Van Hecke; Mbeumo, Tavernier, E.Le Fée, Barnes;
Haaland (C), Barry, Isak. XI EP 55.458 with the captain doubled; 61.574 with
the triple.

## Captaincy

Top 5 among the XI by single-GW EP, undiscounted (`objective`'s captain line):

| # | Player | GW9 EP | p_start_gw[0] | Gap to #1 |
|---|---|---|---|---|
| 1 | Haaland | 6.116 | 0.94 | — |
| 2 | Mbeumo | 4.839 | 0.96 | 1.277 |
| 3 | Tavernier | 4.643 | 0.93 | 1.473 |
| 4 | Gabriel | 4.519 | 0.95 | 1.597 |
| 5 | Barry | 4.503 | 0.94 | 1.613 |

Captain Haaland: 1.277 clear of the field, outside the 0.5 tie band.

Vice: Mbeumo 4.839 v Tavernier 4.643 is inside 0.5 single-GW EP and the
spec's own tie-break (p_start_gw[0] ≥ 0.85) holds both, so the tie is open
to a suggestion. S8 (standing: prefer the steadier points record and the
more consistent club when two options are close) breaks it toward Tavernier:
ret5 3/5 v 2/5; BOU ATT rank 2 and FDR rank 1 v MUN 16th with one win in
eight and the manager under pressure. The vice pays only if Haaland misses
(p_start 0.94); the steer's cost is the 0.196 EP gap in that case. Vice:
Tavernier.

## Bench order

12 Kinsky (GK) · 13 Gomez 3.583 · 14 Justin 3.216 · 15 Calafiori 2.594.
Ordered by GW9 EP; no two within C8's 0.25 band (gaps 0.367, 0.622). With a
3-DEF XI, auto-sub skips Gomez for a missing defender and brings Justin,
which is the order wanted either way.

Bench check: none

## Transfers

None. Free transfer banked: 1 now, 2 at the GW10 deadline (6 Nov 18:30 UTC).
The GW10 cycle starts with two free transfers against a top single of
+1.797 today; Calafiori's price (out 497,609 v in 23,332 this event, already
−0.1) is the one cost of waiting, 0.1 of team value at most.

Gate ids: 385,496,4,8,60,112,332,427,542,68,453,127,411,379,249

## Chips

`chip: 3xc`. Chips available (bootstrap `chips`, set 1): 3xc GW1–19, bboost
GW1–19, freehit GW2–19; wildcard played GW8. One chip per GW; no transfer
chip is in play (bank + 3xc is legal).

The EP case, on Haaland's own numbers (C5 — never on the opponent's
defensive rating):

| Figure | Value | Source |
|---|---|---|
| Haaland GW9 EP (the triple's extra multiplier) | 6.116 | `objective` captain line |
| Next-best XI captain | Mbeumo 4.839 | `objective` captain line |
| Haaland `ep_gw` GW9–14 | 6.116, 5.378, 6.208, 4.948, 5.916, 5.901 | players-FWD.json |
| Own rates | xG90 0.756, pens #1, 8/8 starts, 79/90/90 in R6–R8, p_start 0.94 (C21 streak tier) | players-FWD.json notes/rates |
| Fixture | MCI v BHA (H), λ_att 2.05, not banded; BHA DEFW 0.97 is an established-club rating on 8 matches | fixtures.md § Corrections applied |

Why GW9 and not a later week: GW9 is within 0.092 of his best window figure
(GW11 FUL(H) 6.208) and above GW10, GW12, GW13 and GW14. A 0.092 edge two
gameweeks out, across an international break (GW10 deadline 6 Nov, GW11
21 Nov), is far inside the model's error for the ≥£8.0m band (mae 2.82,
data/retro/gw8.md) and would be re-estimated twice before it could be
acted on, while today's figure stands on this week's team news. There is no
double gameweek in GW9–14 to hold the chip for, and set 1 still has to place
bboost and freehit in the ten gameweeks left before the GW19 deadline, one
chip per gameweek. The prior cycle earmarked 3xc for GW9 on exactly this
fixture and deferred the decision to fresh EP; the fresh EP confirms it.
Expected gain over a plain captaincy: +6.116.

Rejected: hold to GW11 (+0.092 on a two-week forecast, no DGW to wait for);
bboost now (bench GW9 EP 3.321 + 3.583 + 3.216 + 2.594 = 12.714, with
Calafiori at 0.65 — below the triple's 6.116 × 1 only in appearance, but the
bench is earmarked for GW19 when Calafiori's p_start is back at 0.92 and a
late set-1 bench boost has nothing else competing for its slot); free hit
(no blank or double in the window; the spec scores it on GW N alone and the
GW9 XI is already the best XI the money buys). `objective --chip` was not
run: it grades wildcard and freehit only, and neither is proposed.

Provisional chip plan: 3xc GW9 (this proposal, `chip:`); freehit GW16
(placeholder, no blank or double known through GW14); bboost GW19 (last
set-1 gameweek, bench then four playing rows). Windows from bootstrap
`chips`: freehit GW2–19, bboost and 3xc GW1–19.

## Rationale and rejected alternatives

| Alternative | blend / prior | Why not |
|---|---|---|
| Calafiori → Silva | +1.797 / −0.085 | best single; fails the free gate on blend (< 2.0) and flips sign prior-only (C14) |
| Van Hecke → Silva | +1.581 / −1.349 | prior sign flip; also sells the squad's cheapest nailed starter |
| Hill → Silva | +0.779 / −2.610 | prior sign flip |
| Calafiori → De Cuyper | +0.050 / +0.389 | the only positive-both single; +0.050 is noise, far short of 2.0 |
| Mbeumo → Gibbs-White | −4.365 / −3.988 | S7 named-faller check; loses the pool's #1 MID |
| Any Haaland-out or Isak-out single | < −0.269 | outside the top 60 by blend |
| Any hit | n/a | best two singles sum 3.378 < 6.0 and share Silva |
| Hold 3xc to GW11 | +0.092 EP on a two-week forecast | see Chips |

The calibration context argues the same way: the GW8 wildcard squad scored 94
(XI predicted 55.05), rank 4.1m → 1.3m, and every miss bar Calafiori's
minutes was positive variance (data/retro/gw8.md) — nothing in the record
says a player is mispriced enough to move for.

## Suggestions

Read data/suggestions.md through S8

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 6 | followed | both halves now complete: Ndiaye → Groß and Anderson → Schade inside the +14.449 blend / +5.210 prior-only triple; Ndiaye's marginal +2.503 / +0.665 and Anderson's +2.488 / +0.757 each clear the 2.0 gate on their own, so the steer broke no tie and the optimizer reached it unaided; EP6 delta of the row itself 0.00. The GW5 ledger's "Ndiaye half completed" was false in fact (never POSTed) and is superseded here |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |
| S3 | 6 | followed | Ndiaye → Groß made; marginal +2.503 blend / +0.665 prior against the plan without this sale (Scott + Anderson → E.Le Fée + Schade, +11.946 / +4.545), so the below-threshold clause was not needed |
| S4 | 6 | followed | Anderson → Schade made; marginal +2.488 blend / +0.757 prior against the plan without this sale (Scott + Ndiaye → E.Le Fée + Groß, +11.961 / +4.453); clears the gate on both readings, below-threshold clause not needed |
| S5 | 6 | followed | Scott → E.Le Fée made; EP6 0.00 for GW6–11 (status i, 0%); marginal +2.503 / +0.675 against the plan without this sale (Ndiaye + Anderson → E.Le Fée + Schade, +11.946 / +4.535) |
| S6 | 8 | followed | wildcard played at GW8, the timing the row left open (GW6 or GW8): the package +8.304 blend / +8.078 prior-only clears the chip gate against bank (+0.000); EP per GW over GW8–13 rises from 54.68 to 56.06 (336.354 / 6, captain included); the user's earlier hold today was withdrawn by the delegation quoted in this proposal; not taken: 60 per GW stays unreachable — the best package found on the post-Saka files is 56.06 |
| S7 | 7 | standing | honoured as a sell-side policy: of the named fallers only Mbeumo is still owned, a net faller again this event (in 87,670 v out 129,541, price 7.9 unchanged) but Mbeumo → Gibbs-White is −4.365 / −3.988 FAIL, not a small gap, so he is held; the squad's live faller is Calafiori (−0.1 this event, out 497,609 v in 23,332) and Calafiori → Silva +1.797 / −0.085 fails the free gate on blend and prior sign, which the policy never overrides — the cost accepted is at most 0.1 of team value before GW10, when 2 FTs are available; EP6 delta of the row 0.00 |
| S8 | 7 | standing | honoured: no transfer this cycle because no single passes the gate (best Calafiori → Silva +1.797 / −0.085), so no buy is judged under the row; it breaks the vice tie, Mbeumo 4.839 v Tavernier 4.643 inside 0.5 single-GW EP with the spec's p_start tie-break holding both, toward Tavernier (ret5 3/5 v 2/5; BOU ATT rank 2 and FDR rank 1 v MUN 16th, manager under pressure), a cost of 0.196 EP only if Haaland misses; EP6 delta of the row 0.00 |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW10 deadline: 1 live at GW9 (my-team, relayed) + 1 accrued, none used.
# team_value 99.2 and bank 0.1 are the live my-team budget and bank relayed by the orchestrator on 2026-10-30; no transfer this GW.
gw: 9
team_id: 8455344
team_value: 99.2
bank: 0.1
free_transfers_banked: 2
chip: 3xc
chips_used:
  - {chip: wildcard, gw: 8}
transfers_made: []
chip_plan:
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 385, name: Trafford, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: false, vice: false}
  - {id: 60, name: Hill, position: 3, captain: false, vice: false}
  - {id: 112, name: Van Hecke, position: 4, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 5, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 6, captain: false, vice: true}
  - {id: 542, name: E.Le Fée, position: 7, captain: false, vice: false}
  - {id: 453, name: Barnes, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: true, vice: false}
  - {id: 249, name: Barry, position: 10, captain: false, vice: false}
  - {id: 379, name: Isak, position: 11, captain: false, vice: false}
  - {id: 496, name: Kinsky, position: 12, captain: false, vice: false}
  - {id: 127, name: Gomez, position: 13, captain: false, vice: false}
  - {id: 332, name: Justin, position: 14, captain: false, vice: false}
  - {id: 8, name: Calafiori, position: 15, captain: false, vice: false}
```
