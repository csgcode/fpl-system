# GW10 Squad Proposal (2026/27) — BANK both free transfers, no chip, captain Gabriel

First optimizer run of the cycle. Weekly branch: squad from the STATE block
of data/decisions/gw9/final.md; players files `model 64ad9c9c` (all four
positions); fixtures from data/analysis/gw10/; retro data/retro/gw9.md
(active A4 corrections C8, C14, C15, C20). Deadline 2026-11-06 18:30 UTC.
Horizon GW10–GW15; no blank, no double.

## Summary

| Item | Decision |
|---|---|
| Transfers | none — bank both free transfers (2 → 3 at the GW11 deadline) |
| Chip | none (`chip: null`); bboost and freehit remain, 3xc and wildcard played |
| Captain / vice | Gabriel 5.785 / Haaland 5.265 (gap 0.520, outside the 0.5 band) |
| XI | 4-3-3: Trafford; Gabriel, Calafiori, Hill, Van Hecke; Mbeumo, Tavernier, E.Le Fée; Haaland, Isak, Barry |
| Bench | Kinsky, Justin, Gomez, Barnes |
| Predicted GW10 | 58.945 XI incl. captain double (`objective`'s 59.026 XI less the C20 swap Justin 4.155 → Van Hecke 4.074) |
| Money | bank 0.1, team_value 99.5 (live `my-team` budget relayed by the orchestrator) |

## Money and free transfers (live account, relayed)

The orchestrator relayed today's `my-team` read: 2 free transfers, bank 0.1,
selling-price sum 99.4, budget 99.5. The optimizer never runs `my-team`, so
the per-player `--sell` list is a reconstruction: the GW9 list (sum 99.1,
which matched that week's relayed sum) carried forward through the bootstrap
price moves since (Isak 9.1 → 9.2, Tavernier 6.4 → 6.6, Gabriel 7.9 → 8.0,
Van Hecke 4.9 → 5.0), applying the half-rise rule to the known purchase
prices (GW8 buys from data/executor/gw8/make-transfers-20261023T152430_068797Z.json).
It sums to 99.4, equal to the relayed selling-price sum. Rows whose purchase
price is not on record (Tavernier 6.3, Gabriel 7.9, Barry 5.6, Haaland 15.6)
may each be off by 0.1 while the sum matches; no transfer is proposed, so no
POST depends on them.

Free transfers: the GW9 STATE block forecast 2 at this deadline; the live
account shows 2. `--free-transfers 2`. Banking gives min(5, 2 − 0 + 1) = 3
at GW11 (`objective`: `FT next 3`).

`--sell 4:7.9,112:4.9,427:7.9,68:6.3,542:5.7,411:15.6,249:5.6,385:5.0,496:4.4,8:5.9,60:5.5,332:4.5,453:6.1,127:5.0,379:9.1 --bank 0.1 --free-transfers 2`

## Verification — objective (verbatim)

`uv run python -m fpl objective --gw 10 --sell <list above> --bank 0.1 --free-transfers 2 --moves none --top 60`:

```
objective gw10 — horizon GW10–GW15; squad from data/decisions/gw9/final.md
sell basis: relayed (Σ sell 99.4 + bank 0.1 = 99.5)
baseline: blend 342.415 prior 333.269
legal single moves: 1551 (pool 437); top 60 by blend:
  1 | Calafiori → Silva | +0.771 | -0.301 | bank 0.9 | p4₃ - | ret5 3/5 | fails (prior sign flip)
  2 | Hill → Silva | +0.704 | -2.082 | bank 0.5 | p4₃ - | ret5 3/5 | fails (prior sign flip)
  3 | Calafiori → De Cuyper | +0.238 | +0.661 | bank 0.6 | p4₃ - | ret5 4/5 | fails (blend < 2.0)
  4 | Calafiori → Murillo | +0.085 | -0.488 | bank 0.5 | p4₃ - | ret5 1/5 | fails (prior sign flip)
  5 | Barnes → McAtee | +0.072 | +0.414 | bank 0.7 | p4₃ - | ret5 2/5 | fails (blend < 2.0)
  6 | Calafiori → Muharemović | +0.019 | -0.362 | bank 0.9 | p4₃ - | ret5 3/5 | fails (prior sign flip)
  7 | Calafiori → Vuskovic | +0.005 | -0.603 | bank 0.8 | p4₃ - | ret5 4/5 | fails (prior sign flip)
  8 | Barnes → Stach | -0.114 | -2.005 | bank 0.2 | p4₃ - | ret5 1/5 | fails (prior sign flip)
  9 | Barnes → Enciso | -0.116 | -1.896 | bank 0.7 | p4₃ - | ret5 2/5 | fails (prior sign flip)
  10 | Gomez → Nørgaard | -0.127 | -0.943 | bank 0.3 | p4₃ - | ret5 0/5 | fails (prior sign flip)
plan: none — blend +0.000 prior +0.000; bank 0.1; transfers 0 (free 2, hits 0); FT next 3
after plan, best single: Calafiori → Silva +0.771 / -0.301 — fails (prior sign flip)
reference (greedy): bank — no move passes its gate
tie-break move: none within 0.5
tie-break: none in band
verdict: PASS
GW10 XI 4-3-3 59.026: Trafford, Gabriel, Calafiori, Hill, Justin, Mbeumo, Tavernier, E.Le Fée, Haaland, Isak, Barry; captain top 5: Gabriel 5.785 0.95, Haaland 5.265 0.94, Mbeumo 5.213 0.96, Isak 5.167 0.93, Barry 5.081 0.94
boundary pairs within 0.25: Hill 4.245 (DefCon 0.263) | Van Hecke 4.074 (0.151) ; Justin 4.155 (DefCon 0.137) | Van Hecke 4.074 (0.151) ; Justin 4.155 (DefCon 0.137) | Gomez 3.949 (0.123)
bench: Kinsky 3.220, Van Hecke 4.074, Gomez 3.949, Barnes 3.741
```

Rows 11–60 are Gomez → <midfielder> at −0.127 / −0.943: the bench slots
score 0 in the objective, so every such move is a pure loss. No
`tie-break group:` line was printed.

## Step 1 — budget skeleton

Weekly cycle, two free transfers: the skeleton is the GW8 wildcard squad.
Two slots above £9m: Haaland (sell 15.6; EP6 34.08, pool #1 FWD by 4.35
over Isak) and Isak (sell 9.1; EP6 29.73, pool #2 FWD). Each was tested
against the one split the money allows, with the freed funds spent on the
best midfielder the pair can reach (Step 4, P8 and P9): Haaland → Thiago
loses 11.580 blend / 8.527 prior-only even when the money buys
B.Fernandes (+5.651 / +7.372 as the paired marginal); Isak → Kostoulas
loses 4.971 / 2.241 even when it funds Barnes → Gibbs-White (+1.903 /
−0.551). Neither premium is challenged. The budget is exhausted (bank 0.1).

Pool position of the squad: GKP #1 (Trafford), DEF #1, #2, #4, #6 (Gabriel,
Van Hecke, Hill, Calafiori), MID #1, #3, #4 (Mbeumo, Tavernier, E.Le Fée),
FWD #1, #2, #3 (Haaland, Isak, Barry). The slots that could move are the
fourth defender / third-choice midfielder (Justin 22.65, Gomez 23.24, Barnes
22.90) and Calafiori (24.37 at p_start 0.90), and every upgrade into them
tops out at +0.771 (Calafiori → Silva).

## Step 2 — XI fill by raw EP

`objective`'s GW10 XI is 4-3-3, 59.026 with the captain doubled, Justin as
the fourth defender over Barnes 3.741 and Gomez 3.949. Club caps: ARS 2
(Gabriel, Calafiori), BOU 2 (Hill, Tavernier), TOT 2 (Van Hecke, Kinsky),
LEE 2 (Trafford, Justin), MUN, MCI, LIV, SUN, NEW, BHA, EVE 1 each — none
at 3.

XI/bench boundary (C20): `objective` prints three pairs inside 0.25.

| Pair (XI v bench) | GW10 EP gap | DefCon share of EP6 | C20 pick |
|---|---|---|---|
| Hill 4.245 v Van Hecke 4.074 | 0.171 | 0.263 v 0.151 | Hill (higher on both) |
| Justin 4.155 v Van Hecke 4.074 | 0.081 | 0.137 v 0.151 | **Van Hecke** — the higher DefCon floor |
| Justin 4.155 v Gomez 3.949 | 0.206 | 0.137 v 0.123 | Justin (higher on both) |

C20 applies C8's rule at the XI boundary: inside 0.25 single-GW EP, prefer
the higher DefCon floor share, because the floor is fixture-independent and
an XI boundary always pays out. Justin v Van Hecke is a 0.081 gap on one
fixture — the same match, LEE v TOT, from opposite sides — and Van Hecke
carries the higher floor share, the higher EP6 (26.69 v 22.65, pool #2 DEF)
and p4 0.577 v 0.562. Van Hecke starts; Justin is first outfield sub.

Final XI 4-3-3: Trafford; Gabriel, Calafiori, Hill, Van Hecke; Mbeumo,
Tavernier, E.Le Fée; Haaland, Isak, Barry. XI EP 59.026 − 4.155 + 4.074 =
58.945 with the captain doubled (the swap is between two defenders, so the
captain term and formation are unchanged).

## Step 3 — bench

Goalkeeper: one playing keeper (Trafford, p_start 0.95 flat, LEE; EP6
22.17, pool #1) with a £4.4m non-rotating backup (Kinsky, TOT, 0.95; EP6
20.19, pool #6). No rotation pair: the top 15 keepers sit in a 3.6-point
band over six GWs, and every Kinsky-out move is negative on blend (Kinsky →
Suzuki +0.358 / −0.126 appears only after a hit plan, Step 4 P11).

Outfield bench, ordered by GW10 EP with C8's 0.25 band checked:

| Slot | Player | Price | p_start GW10 | GW10 EP | DefCon share | Note |
|---|---|---|---|---|---|---|
| 13 | Justin | 4.5 | 0.94 | 4.155 | 0.137 | first sub; the nailed £4.5m defender; covers a 4-DEF XI in any formation |
| 14 | Gomez | 5.0 | 0.95 | 3.949 | 0.123 | gap to Justin 0.206, inside 0.25 — C8 agrees with EP (0.137 > 0.123) |
| 15 | Barnes | 6.1 | 0.95 | 3.741 | 0.015 | gap to Gomez 0.208, inside 0.25 — C8 agrees with EP (0.123 > 0.015) |

Both nailed £4.0–4.5m rows (Justin, Kinsky) are already the cheap bench.
Bench GW10 EP 3.220 + 4.155 + 3.949 + 3.741 = 15.065, all four at p_start
≥ 0.94 (see Chips).

## Step 4 — swap pass (audit trail)

Legal single moves 1551, top 10 pasted above (Verification). Only seven of
1551 singles are positive on blend; the best, Calafiori → Silva +0.771, is
short of the free gate's 2.0 and flips sign prior-only (C14). The two
positive-both singles (Calafiori → De Cuyper +0.238 / +0.661, Barnes →
McAtee +0.072 / +0.414) are noise against 2.0. `tie-break move: none within
0.5`; `tie-break: none in band`; no `tie-break group:` line.

With two free transfers a pair can shift money the single-move table cannot
see, so every funding route to a player the squad lacks was graded with
`objective --moves`. Plan lines verbatim:

```
P1  plan: Calafiori → Silva — blend +0.771 prior -0.301; bank 0.9; transfers 1 (free 2, hits 0); FT next 2
      move Calafiori → Silva: +0.771 / -0.301 — fails (prior sign flip)
P2  plan: Mbeumo → Gibbs-White — blend -4.331 prior -4.477; bank 0.2; transfers 1 (free 2, hits 0); FT next 2
      move Mbeumo → Gibbs-White: -4.331 / -4.477 — fails (prior sign flip)
P3  plan: Barnes → McAtee — blend +0.072 prior +0.414; bank 0.7; transfers 1 (free 2, hits 0); FT next 2
      move Barnes → McAtee: +0.072 / +0.414 — fails (blend < 2.0)
P4  error: Barnes → B.Fernandes: cannot afford — bank after -5.5
P5  plan: Calafiori → Silva, Barnes → Ødegaard — blend +1.134 prior -1.837; bank 0.3; transfers 2 (free 2, hits 0); FT next 1
      move Calafiori → Silva: +0.964 / +0.232 — fails (blend < 2.0)
      move Barnes → Ødegaard: +0.363 / -1.536 — fails (prior sign flip)
P6  plan: Calafiori → De Cuyper, Barnes → McAtee — blend +0.310 prior +1.075; bank 1.2; transfers 2 (free 2, hits 0); FT next 1
      move Calafiori → De Cuyper: +0.238 / +0.661 — fails (blend < 2.0)
      move Barnes → McAtee: +0.072 / +0.414 — fails (blend < 2.0)
P7  plan: Calafiori → Silva, Barnes → McAtee — blend +0.833 prior +0.224; bank 1.5; transfers 2 (free 2, hits 0); FT next 1
      move Calafiori → Silva: +0.761 / -0.190 — fails (prior sign flip)
      move Barnes → McAtee: +0.062 / +0.525 — fails (blend < 2.0)
P8  plan: Isak → Kostoulas, Barnes → Gibbs-White — blend -3.068 prior -2.792; bank 1.7; transfers 2 (free 2, hits 0); FT next 1
      move Isak → Kostoulas: -4.971 / -2.241 — fails (prior sign flip)
      move Barnes → Gibbs-White: +1.903 / -0.551 — fails (prior sign flip)
P9  plan: Haaland → Thiago, Barnes → B.Fernandes — blend -5.970 prior -2.076; bank 2.3; transfers 2 (free 2, hits 0); FT next 1
      move Haaland → Thiago: -11.580 / -8.527 — fails (prior sign flip)
      move Barnes → B.Fernandes: +5.651 / +7.372 — passes free gate
P10 plan: Van Hecke → Konsa, Barnes → Iwobi — blend -3.135 prior -4.617; bank 0.9; transfers 2 (free 2, hits 0); FT next 1
      move Van Hecke → Konsa: -2.717 / -2.327 — fails (prior sign flip)
      move Barnes → Iwobi: -0.692 / -2.539 — fails (prior sign flip)
P11 plan: Calafiori → Silva, Barnes → McAtee, Justin → Muharemović — blend +1.530 prior -0.624; bank 0.9; transfers 3 (free 2, hits 4); FT next 1
      move Calafiori → Silva: +0.761 / -0.327 — fails (prior sign flip)
      move Barnes → McAtee: +0.062 / +0.525 — fails (blend < 6.0)
      move Justin → Muharemović: +0.697 / -0.848 — fails (prior sign flip)
```

Every run printed `reference (greedy): bank — no move passes its gate` and
`tie-break move: none within 0.5`; every verdict was FAIL. The largest
marginal any plan produced is Barnes → Gibbs-White +1.903 blend inside P8,
below 2.0 and negative prior-only. B.Fernandes (EP6 30.37, the one
unowned player in a top-two pool slot) is reachable only by selling Haaland
(P9) and the Haaland leg loses 11.580; no other sale pair frees 5.5 (Isak →
any playable forward frees at most 3.8). A hit needs +6.0 gross per paid
move; the best three singles sum to +1.530 (P11). Banking is the greedy
reference and the plan.

Moves named by open suggestions, graded with `--moves`:

| Row | Move | blend | prior | Verdict (verbatim) |
|---|---|---|---|---|
| S7 (named faller still owned, out 123,616 v in 19,147 this event) | Mbeumo → Gibbs-White | −4.331 | −4.477 | `FAIL: Mbeumo → Gibbs-White -4.331 / -4.477 fails the free gate (blend ≥ 2.0, prior ≥ 0); further free move passes: Gibbs-White → Mbeumo +4.331 / +4.477; plan gain -4.331 below the blend-only greedy reference +0.000` |
| S7 (squad's other net-out row, out 37,613 v in 12,129) | Barnes → McAtee | +0.072 | +0.414 | `FAIL: Barnes → McAtee +0.072 / +0.414 fails the free gate (blend ≥ 2.0, prior ≥ 0)` |
| S7 (last cycle's faller; flat at 5.9 this event, out 83,450 v in 62,480) | Calafiori → Silva | +0.771 | −0.301 | `FAIL: Calafiori → Silva +0.771 / -0.301 fails the free gate (blend ≥ 2.0, prior ≥ 0)` |
| S8 (names no move) | — | — | — | applied to the vice tie only (Captaincy) |

Fixture context (data/analysis/gw10/fixtures.md): ARS turns hard from GW13
(Δ Σλ_att −1.21, Δ ΣP(CS) −0.13) and MCI turns easy (+0.91), so the GW9
review's F6 premise that both turn harder holds for ARS only. Nothing in the
window is a one-good-fixture buy that the ticker turns bad in two; nothing
was bought.

## Squad

Price = selling price on the reconstructed basis above (sum 99.4); EP6 =
`ep_total6`; GW10 = `ep_gw[0]`; p = `p_start_gw[0]`.

| Pos | Player | Club | Price | p GW10 | GW10 EP | EP6 | Role |
|---|---|---|---|---|---|---|---|
| GKP | Trafford | LEE | 5.0 | 0.95 | 3.888 | 22.17 | XI |
| GKP | Kinsky | TOT | 4.4 | 0.95 | 3.220 | 20.19 | bench 12 |
| DEF | Gabriel | ARS | 7.9 | 0.95 | 5.785 | 29.71 | XI, captain |
| DEF | Calafiori | ARS | 5.9 | 0.90 | 4.876 | 24.37 | XI |
| DEF | Hill | BOU | 5.5 | 0.95 | 4.245 | 25.46 | XI |
| DEF | Van Hecke | TOT | 4.9 | 0.95 | 4.074 | 26.69 | XI |
| DEF | Justin | LEE | 4.5 | 0.94 | 4.155 | 22.65 | bench 13 |
| MID | Mbeumo | MUN | 7.9 | 0.96 | 5.213 | 30.50 | XI |
| MID | Tavernier | BOU | 6.3 | 0.95 | 4.932 | 27.85 | XI |
| MID | E.Le Fée | SUN | 5.7 | 0.95 | 4.634 | 26.82 | XI |
| MID | Gomez | BHA | 5.0 | 0.95 | 3.949 | 23.24 | bench 14 |
| MID | Barnes | NEW | 6.1 | 0.95 | 3.741 | 22.90 | bench 15 |
| FWD | Haaland | MCI | 15.6 | 0.94 | 5.265 | 34.08 | XI, vice |
| FWD | Isak | LIV | 9.1 | 0.93 | 5.167 | 29.73 | XI |
| FWD | Barry | EVE | 5.6 | 0.94 | 5.081 | 27.73 | XI |

Squad EP6 sum 394.1 (15 rows, bench included); objective baseline 342.415
blend / 333.269 prior-only (best XI + captain per GW, bench at 0).

## Starting XI — 4-3-3

Trafford; Gabriel, Calafiori, Hill, Van Hecke; Mbeumo, Tavernier, E.Le Fée;
Haaland (C), Isak, Barry. XI EP 58.945 with the captain doubled (Step 2).

## Captaincy

Top 5 among the XI by single-GW EP, undiscounted (`objective`'s captain line):

| # | Player | GW10 EP | p_start_gw[0] | p4 GW10 | Gap to #1 |
|---|---|---|---|---|---|
| 1 | Gabriel | 5.785 | 0.95 | 0.731 | — |
| 2 | Haaland | 5.265 | 0.94 | 0.447 | 0.520 |
| 3 | Mbeumo | 5.213 | 0.96 | 0.466 | 0.572 |
| 4 | Isak | 5.167 | 0.93 | 0.477 | 0.618 |
| 5 | Barry | 5.081 | 0.94 | 0.501 | 0.704 |

Captain Gabriel: 0.520 clear of Haaland, outside the 0.5 tie band, so the
higher EP wins by the spec and no suggestion can reach the choice. ARS v HUL
(H): λ_att 2.14 (HUL ATT rank 19), P(CS) 0.50 — the window's largest, and a
banded row under C12 (±15pp, two-sided). Sensitivity, derived from the band
and not printed by `objective`: at the band's low end (0.35) the clean-sheet
term falls by about 0.57 and Gabriel drops to roughly 5.21, below Haaland;
at the high end he rises to roughly 6.36. The band is symmetric, so the
central EP is the expected value and the rule stands; the red-team should
weigh C4/C12's "largest EP term" prohibition, which on this reading is a tie
between the appearance term (about 1.90) and the clean-sheet term (about
1.90), not a single largest term. Haaland's own GW10 figure is his lowest in
the window (NFO (A), λ_att 1.51, NFO DEFW rank 3); his GW11 FUL (H) is 6.20.

Vice: Haaland 5.265 v Mbeumo 5.213 is inside 0.5 and the spec's tie-break
(p_start_gw[0] ≥ 0.85) holds both, so the tie is open to a suggestion. S8
(standing: prefer the steadier record and the more consistent club) breaks
it toward Haaland — ret5 4/5 v 2/5, MCI ATT rank 1 v MUN rank 7 — which is
also the higher EP, so the steer costs nothing. Vice: Haaland.

## Bench order

12 Kinsky (GK) · 13 Justin 4.155 · 14 Gomez 3.949 · 15 Barnes 3.741.
Ordered by GW10 EP; the two outfield gaps (0.206, 0.208) are inside C8's
0.25 band and the DefCon floor shares (0.137 > 0.123 > 0.015) rank the same
way, so the tie-break confirms the EP order. With a 4-DEF XI an absent
defender brings Justin; an absent midfielder or forward also brings Justin
(5-2-3 and 5-3-2 are legal), the higher-EP sub either way.

Bench check: none

## Transfers

None. Both free transfers banked: 2 now, 3 at the GW11 deadline (21 Nov
2026, after the international break). The best single today is +0.771 and
the best paired marginal +1.903, both failing the free gate; three free
transfers at GW11 cover a reshape before ARS turn harder from GW13 (fixtures
§ Swings) with the post-break team news priced in. Cost of waiting: Mbeumo
(out 123,616 v in 19,147, price 7.9 unchanged) and Barnes (out 37,613 v in
12,129) are the squad's net-out rows; each fall costs 0.1 of team value, and
neither has a replacement that passes the gate.

Gate ids: 385,496,4,8,60,112,332,427,542,68,453,127,411,379,249

## Chips

`chip: null`. Chips available (bootstrap `chips`, set 1): bboost GW1–19,
freehit GW2–19; 3xc played GW9, wildcard played GW8. One chip per GW.

Free hit, graded on GW10 alone with `objective --chip freehit`. The best
package the money and club caps allow for a single GW is Van Hecke → Konsa
plus Barnes → Iwobi (Konsa 4.788 is the third-best DEF GW10 EP; the three
best ARS rows are then held). Verbatim:

```
objective gw10 — horizon GW10–GW10; squad from data/decisions/gw9/final.md
baseline: blend 59.026 prior 56.825
plan: Van Hecke → Konsa, Barnes → Iwobi — blend +0.633 prior +0.191; bank 0.9; transfers 2 under freehit (FT unchanged (2)); chip gate: ≥ 6.0 over the greedy plan
verdict: FAIL: freehit fails the chip gate: +0.633 / +0.191 over the greedy plan (need blend ≥ 6.0, prior ≥ 0)
```

No free-hit package can reach 6.0: the squad already starts the pool's
top-two GW10 scorer at every position but goalkeeper (Raya 4.089 v Trafford
3.888, +0.2), and the unconstrained best GW10 XI from the players files
(B.Fernandes and Konsa added to the current XI) is about 60.1 against
59.026, +1.1 before any budget. Wildcard: set-1 chip already played (GW8),
not gradable.

Bench boost: not played. The current bench is the strongest this squad has
carried — GW10 EP 15.065, four rows at p_start ≥ 0.94 with no rotation risk
before the break — and the spec has no `objective` reading for bboost, only
the earmark. The GW19 earmark rests on optionality (a double gameweek, if
one is announced for GW16–19, and three banked transfers to shape the bench
with) rather than on a higher bench EP; on the current players files the
bench scores 14–15 in each of GW10–12. The missing gate is logged in
docs/backlog.md; the earmark stands until a rule grades it.

Provisional chip plan: freehit GW16 (placeholder, no blank or double known
through GW15); bboost GW19 (last set-1 gameweek). Windows from bootstrap
`chips`: freehit GW2–19, bboost GW1–19.

## Rationale and rejected alternatives

| Alternative | blend / prior | Why not |
|---|---|---|
| Calafiori → Silva | +0.771 / −0.301 | best single; fails the free gate on blend (< 2.0) and flips sign prior-only (C14) |
| Calafiori → Silva + Barnes → Ødegaard | +1.134 / −1.837 | best pair by blend; both legs fail (Silva leg +0.964 / +0.232 < 2.0, Ødegaard leg sign flip) |
| Isak → Kostoulas + Barnes → Gibbs-White | −3.068 / −2.792 | the Gibbs-White leg is the largest marginal seen (+1.903 / −0.551) but still fails; the Isak leg loses 4.971 |
| Haaland → Thiago + Barnes → B.Fernandes | −5.970 / −2.076 | the only route to B.Fernandes; the Haaland leg loses 11.580 |
| Mbeumo → Gibbs-White | −4.331 / −4.477 | S7 named-faller check; loses the pool's #1 MID |
| Calafiori → De Cuyper + Barnes → McAtee | +0.310 / +1.075 | the two positive-both singles together; noise against 2.0 per move |
| Any hit | +1.530 / −0.624 (P11) | best three singles sum to 1.530 gross against a 6.0 gate |
| Free hit | +0.633 / +0.191 | fails the 6.0 chip gate; the squad already holds the GW10 top scorers |
| Bench boost now | bench 15.065 | no spec gate; earmark GW19 kept, see Chips |
| Captain Haaland | 5.265 v 5.785 | 0.520 below Gabriel, outside the 0.5 band |
| Start Justin over Van Hecke | +0.081 GW10 EP | C20: inside 0.25, the higher DefCon floor share (0.151 v 0.137) starts |

Calibration context (data/retro/gw9.md): the XI scored 58 against 55.46
predicted; every squad miss was VARIANCE (Van Hecke +10.81, Barry +4.50,
E.Le Fée +3.60, Haaland −4.12, Mbeumo −3.84) or a bench MINUTES row
(Calafiori, now p_start 0.90). The ≥£8.0m band's bias is −0.33 on n=9 (C15:
no premium under-prediction). Nothing in the record says a player is
mispriced enough to move for.

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
| S7 | 7 | standing | honoured as a sell-side policy: of the named fallers only Mbeumo is still owned, a net faller again this event (in 19,147 v out 123,616, price 7.9 unchanged) but Mbeumo → Gibbs-White is −4.331 / −4.477 FAIL, not a small gap, so he is held; the squad's other net-out row is Barnes (out 37,613 v in 12,129) and Barnes → McAtee +0.072 / +0.414 fails the free gate on blend; Calafiori is flat at 5.9 this event and Calafiori → Silva +0.771 / −0.301 fails on blend and prior sign; the policy never overrides the gate — the cost accepted is 0.1 of team value per fall before GW11, when 3 FTs are available; EP6 delta of the row 0.00 |
| S8 | 7 | standing | honoured: no buy this cycle because no move passes the gate (best single Calafiori → Silva +0.771 / −0.301; best paired marginal Barnes → Gibbs-White +1.903 / −0.551), so no buy is judged under the row; it breaks the vice tie, Haaland 5.265 v Mbeumo 5.213 inside 0.5 single-GW EP with the spec's p_start tie-break holding both, toward Haaland (ret5 4/5 v 2/5; MCI ATT rank 1 v MUN rank 7), the higher EP as well, so the steer costs 0.00; it cannot reach the captaincy, Gabriel 5.785 v Haaland 5.265 being 0.520 apart, outside the band; EP6 delta of the row 0.00 |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW11 deadline: 2 live at GW10 (my-team, relayed) + 1 accrued, none used (objective: FT next 3).
# team_value 99.5 and bank 0.1 are the live my-team budget and bank relayed by the orchestrator on 2026-11-05; no transfer this GW.
gw: 10
team_id: 8455344
team_value: 99.5
bank: 0.1
free_transfers_banked: 3
chip: null
chips_used:
  - {chip: wildcard, gw: 8}
  - {chip: 3xc, gw: 9}
transfers_made: []
chip_plan:
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 385, name: Trafford, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: true, vice: false}
  - {id: 8, name: Calafiori, position: 3, captain: false, vice: false}
  - {id: 60, name: Hill, position: 4, captain: false, vice: false}
  - {id: 112, name: Van Hecke, position: 5, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 6, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 7, captain: false, vice: false}
  - {id: 542, name: E.Le Fée, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: false, vice: true}
  - {id: 379, name: Isak, position: 10, captain: false, vice: false}
  - {id: 249, name: Barry, position: 11, captain: false, vice: false}
  - {id: 496, name: Kinsky, position: 12, captain: false, vice: false}
  - {id: 332, name: Justin, position: 13, captain: false, vice: false}
  - {id: 127, name: Gomez, position: 14, captain: false, vice: false}
  - {id: 453, name: Barnes, position: 15, captain: false, vice: false}
```
