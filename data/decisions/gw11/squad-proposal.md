# GW11 Squad Proposal (2026/27) — Calafiori → De Cuyper (free), no chip, captain Haaland

First optimizer run of the cycle. Weekly branch: squad from the STATE block
of data/decisions/gw10/final.md; players files `model 64ad9c9c` (all four
positions); fixtures from data/analysis/gw11/; retro data/retro/gw10.md
(active A4 corrections C8, C14, C15, C20; none new or changed). Deadline
2026-11-21 11:00 UTC. Horizon GW11–GW16; no blank, no double.

## Summary

| Item | Decision |
|---|---|
| Transfers | Calafiori → De Cuyper, free (sell 5.9 → buy 5.5); +2.374 blend / +1.881 prior-only; no hit |
| Free transfers | 3 now, 1 used, 3 at the GW12 deadline (`objective`: `FT next 3`) |
| Chip | none (`chip: null`); bboost and freehit remain, 3xc and wildcard played |
| Captain / vice | Haaland 6.047 / Gabriel 5.229 (captain gap to #2 Isak 0.741) |
| XI | 4-3-3: Trafford; Gabriel, Van Hecke, De Cuyper, Hill; E.Le Fée, Tavernier, Mbeumo; Haaland, Isak, Barry |
| Bench | Kinsky, Gomez, Justin, Barnes |
| Predicted GW11 | 58.405 XI incl. captain double (`objective`) |
| Money | bank 0.5, team_value 99.6 (sell sum 99.1 + bank 0.5) |

## Money and free transfers (live account, relayed)

The orchestrator relayed today's authenticated read: 3 free transfers, bank
0.1, selling-price sum 99.5, budget 99.6. The optimizer never runs
`my-team`, so the per-player `--sell` list is a reconstruction from purchase
prices on record and the half-rise rule against the gw11 bootstrap:

| Player | Bought (source) | Now | Sell |
|---|---|---|---|
| Haaland | 15.5 (GW1 bootstrap) | 15.8 | 15.6 |
| Isak | 9.0 (GW8 executor record) | 9.3 | 9.1 |
| Gabriel | 8.0 (GW1 bootstrap) | 8.1 | 8.0 |
| Mbeumo | 8.0 (GW1 bootstrap) | 7.9 | 7.9 |
| Tavernier | 6.0 (GW2 bootstrap) | 6.7 | 6.3 |
| Barnes | 6.1 (GW8 executor record) | 6.0 | 6.0 |
| Calafiori | 6.0 (GW8 executor record) | 5.9 | 5.9 |
| E.Le Fée | 5.7 (GW6 bootstrap) | 5.7 | 5.7 |
| Barry | 5.5 (GW3 bootstrap) | 5.7 | 5.6 |
| Hill | 5.5 (GW8 executor record) | 5.6 | 5.5 |
| Van Hecke | 4.9 (GW7 bootstrap) | 5.1 | 5.0 |
| Gomez | 5.0 (GW8 executor record) | 5.1 | 5.0 |
| Trafford | 5.0 (GW8 executor record) | 5.0 | 5.0 |
| Justin | 4.5 (GW8 executor record) | 4.5 | 4.5 |
| Kinsky | 4.5 (GW8 executor record) | 4.4 | 4.4 |

The list sums to 99.5, equal to the relayed selling-price sum, and
`objective` prints `sell basis: relayed`. The sold player's price rests on
the GW8 executor record (Calafiori bought at 6.0, now 5.9, so sell 5.9); at
POST time the selling price comes from `my-team`. Rows whose purchase price
is read from a bootstrap snapshot rather than an executor record (Haaland,
Gabriel, Mbeumo, Tavernier, E.Le Fée, Barry, Van Hecke) could each be off by
0.1 while the sum matches; none of them is sold.

`--sell 411:15.6,379:9.1,4:8.0,427:7.9,68:6.3,453:6.0,8:5.9,249:5.6,542:5.7,60:5.5,112:5.0,127:5.0,385:5.0,332:4.5,496:4.4 --bank 0.1 --free-transfers 3`

After the move: bank 0.1 + 5.9 − 5.5 = 0.5; selling-price sum 99.5 − 5.9 +
5.5 = 99.1; team_value 99.6.

## Verification — objective (verbatim)

`uv run python -m fpl objective --gw 11 --sell <list above> --bank 0.1 --free-transfers 3 --moves 8:115 --top 10`
(single-move table from the same command without `--moves`):

```
objective gw11 — horizon GW11–GW16; squad from data/decisions/gw10/final.md
sell basis: relayed (Σ sell 99.5 + bank 0.1 = 99.6)
baseline: blend 345.346 prior 334.971
legal single moves: 1564 (pool 439); top 40 by blend:
  1 | Calafiori → De Cuyper | +2.374 | +1.881 | bank 0.5 | p4₃ - | ret5 4/5 | passes free gate
  2 | Calafiori → Silva | +2.042 | +0.646 | bank 0.9 | p4₃ - | ret5 3/5 | passes free gate
  3 | Calafiori → Vuskovic | +1.379 | +0.300 | bank 0.7 | p4₃ - | ret5 4/5 | fails (blend < 2.0)
  4 | Calafiori → Murillo | +1.364 | -0.096 | bank 0.5 | p4₃ - | ret5 1/5 | fails (prior sign flip)
  5 | Calafiori → Muharemović | +1.172 | +0.281 | bank 0.9 | p4₃ - | ret5 3/5 | fails (blend < 2.0)
  6 | Calafiori → Truffert | -0.031 | +0.854 | bank 0.6 | p4₃ - | ret5 3/5 | fails (blend < 2.0)
  7 | Kinsky → M.Bizot | -0.041 | -0.168 | bank 0.0 | p4₃ 0.01 | ret5 0/5 | fails (prior sign flip)
  8 | Kinsky → Petrović | -0.041 | -0.168 | bank 0.0 | p4₃ 0.29 | ret5 3/5 | fails (prior sign flip)
  9 | Kinsky → Forster | -0.041 | -0.168 | bank 0.5 | p4₃ 0.01 | ret5 0/5 | fails (prior sign flip)
  10 | Kinsky → Valdimarsson | -0.041 | -0.168 | bank 0.1 | p4₃ 0.01 | ret5 0/5 | fails (prior sign flip)
plan: Calafiori → De Cuyper — blend +2.374 prior +1.881; bank 0.5; transfers 1 (free 3, hits 0); FT next 3
  move Calafiori → De Cuyper: +2.374 / +1.881 — passes free gate
after plan, best single: Barnes → Groß +0.621 / -1.723 — fails (prior sign flip)
reference (greedy): Calafiori → De Cuyper +2.374 / +1.881 — blend +2.374 prior +1.881
tie-break move: Calafiori → De Cuyper +2.374 v Calafiori → Silva +2.042 — winner Calafiori → De Cuyper (ret5 4/5 v 3/5)
tie-break group: Calafiori winner De Cuyper (decided by blend)
tie-break: plan takes Calafiori → De Cuyper
verdict: PASS
GW11 XI 4-3-3 58.405: Trafford, Gabriel, Van Hecke, De Cuyper, Hill, E.Le Fée, Tavernier, Mbeumo, Haaland, Isak, Barry; captain top 5: Haaland 6.047 0.94, Isak 5.306 0.93, Gabriel 5.229 0.95, Van Hecke 4.947 0.95, E.Le Fée 4.706 0.95
boundary pairs within 0.25: Trafford 3.578 (DefCon 0.000) | Kinsky 3.468 (0.000)
bench: Kinsky 3.468, Gomez 3.956, Justin 3.538, Barnes 3.510
```

The table header reads `top 40` because the single-move run used
`--top 40`; rows 11–22 are Kinsky → <goalkeeper> at −0.041 / −0.168, rows
23–32 further Calafiori, Hill and Van Hecke sales at −0.043 or worse on
blend, rows 33–40 Gomez → <midfielder> at −0.472 / −1.597. Only five of the
1564 singles are positive on blend, all of them Calafiori sales.

## Step 1 — budget skeleton

Weekly cycle; the skeleton is the GW8 wildcard squad. Two slots above £9m:
Haaland (sell 15.6; EP6 34.90, pool #1 FWD by 5.49 over Isak) and Isak
(sell 9.1; EP6 29.41, pool #2 FWD). Each was tested against the split the
money allows (Step 4, P6–P8): Haaland → N.Jackson loses 11.761 blend /
11.932 prior-only even when the money buys B.Fernandes (+7.930 / +7.303 as
the paired marginal); Isak → Calvert-Lewin loses 3.767 / 2.929 while funding
Mbeumo → B.Fernandes (+2.621 / +3.672); Isak → N.Jackson loses 3.618 / 4.374
while funding Barnes → Gibbs-White (+1.985 / +0.039). Neither premium is
challenged. Bank after the plan 0.5, at the ≤ 0.5 limit.

## Step 2 — XI fill by raw EP

`objective`'s GW11 XI after the move is 4-3-3, 58.405 with the captain
doubled (58.028 before it). Club counts after the move: BHA 2 (De Cuyper,
Gomez), BOU 2 (Hill, Tavernier), TOT 2 (Van Hecke, Kinsky), LEE 2 (Trafford,
Justin), ARS, MUN, MCI, LIV, SUN, NEW, EVE 1 each — none at 3.

XI/bench boundary (C20): `objective` prints one pair inside 0.25, Trafford
3.578 v Kinsky 3.468, both with DefCon share 0.000, so the floor cannot
separate them and the higher EP starts: Trafford. No outfield pair is inside
the band (the lowest outfield starter, Mbeumo 4.288, is 0.332 clear of Gomez
3.956), so C20 changes nothing this week. The retro's note that C20 went
against us once in GW10 (Van Hecke over Justin, n = 1, rule not revised) has
no bearing: the rule does not fire.

## Step 3 — bench

Goalkeeper: one playing keeper (Trafford, LEE, p_start 0.95; EP6 22.53, pool
#1) with a £4.4m non-rotating backup (Kinsky, TOT, 0.95; EP6 19.90). No
rotation pair: every Kinsky sale is −0.041 / −0.168.

Outfield bench by GW11 EP: 13 Gomez 3.956, 14 Justin 3.538, 15 Barnes 3.510.
Justin v Barnes is a 0.028 gap, inside C8's 0.25 band; `objective` prints
DefCon shares only for XI/bench boundary pairs, so none is printed for this
pair this week. The GW10 print (Justin 0.137, Barnes 0.015) puts the
defender's floor well above the winger's, the same way as the EP order, so
the order stands. All three are at p_start ≥ 0.94.

## Step 4 — swap pass (audit trail)

Legal single moves 1564; top 10, `tie-break move:` and `tie-break group:`
lines pasted above. Two singles pass the free gate, both selling Calafiori
(EP6 23.73 at p_start 0.90, pool #9 DEF): De Cuyper +2.374 / +1.881 and
Silva +2.042 / +0.646. They are 0.332 apart, inside the 0.5 tie band, and
the reference takes De Cuyper (`ret5 4/5 v 3/5`), who is also ahead on
blend and nearly three times ahead prior-only.

With three free transfers, every funding route to a second move was graded
with `objective --moves`. Plan lines verbatim:

```
P1  plan: Calafiori → De Cuyper — blend +2.374 prior +1.881; bank 0.5; transfers 1 (free 3, hits 0); FT next 3
      move Calafiori → De Cuyper: +2.374 / +1.881 — passes free gate
      verdict: PASS
P2  plan: Calafiori → Silva — blend +2.042 prior +0.646; bank 0.9; transfers 1 (free 3, hits 0); FT next 3
      move Calafiori → Silva: +2.042 / +0.646 — passes free gate
      verdict: FAIL: plan gain +2.042 below the blend-only greedy reference +2.374
P3  plan: Calafiori → De Cuyper, Barnes → Groß — blend +2.995 prior +0.158; bank 0.2; transfers 2 (free 3, hits 0); FT next 2
      move Calafiori → De Cuyper: +2.078 / +1.350 — passes free gate
      move Barnes → Groß: +0.621 / -1.723 — fails (prior sign flip)
P4  plan: Calafiori → Silva, Barnes → Groß — blend +3.196 prior -0.268; bank 0.6; transfers 2 (free 3, hits 0); FT next 2
      move Calafiori → Silva: +2.279 / +0.924 — passes free gate
      move Barnes → Groß: +1.154 / -0.914 — fails (prior sign flip)
P5  plan: Calafiori → Silva, Barnes → Groß, Justin → Muharemović — blend +3.813 prior -1.189; bank 0.0; transfers 3 (free 3, hits 0); FT next 1
      move Calafiori → Silva: +2.279 / +0.924 — passes free gate
      move Barnes → Groß: +1.154 / -0.914 — fails (prior sign flip)
      move Justin → Muharemović: +0.617 / -0.921 — fails (prior sign flip)
P6  plan: Isak → Calvert-Lewin, Mbeumo → B.Fernandes, Calafiori → Silva — blend +0.896 prior +1.378; bank 0.3; transfers 3 (free 3, hits 0); FT next 1
      move Isak → Calvert-Lewin: -3.767 / -2.929 — fails (prior sign flip)
      move Mbeumo → B.Fernandes: +2.621 / +3.672 — passes free gate
      move Calafiori → Silva: +2.335 / +0.601 — passes free gate
P7  plan: Calafiori → De Cuyper, Isak → N.Jackson, Barnes → Gibbs-White — blend +0.462 prior -2.454; bank 0.6; transfers 3 (free 3, hits 0); FT next 1
      move Calafiori → De Cuyper: +2.247 / +1.596 — passes free gate
      move Isak → N.Jackson: -3.618 / -4.374 — fails (prior sign flip)
      move Barnes → Gibbs-White: +1.985 / +0.039 — fails (blend < 2.0)
P8  plan: Haaland → N.Jackson, Barnes → B.Fernandes, Calafiori → De Cuyper — blend -3.042 prior -4.110; bank 3.3; transfers 3 (free 3, hits 0); FT next 1
      move Haaland → N.Jackson: -11.761 / -11.932 — fails (prior sign flip)
      move Barnes → B.Fernandes: +7.930 / +7.303 — passes free gate
      move Calafiori → De Cuyper: +2.247 / +1.596 — passes free gate
P9  plan: Calafiori → Silva, Barnes → Ødegaard — blend +2.146 prior -0.910; bank 0.2; transfers 2 (free 3, hits 0); FT next 2
      move Calafiori → Silva: +2.100 / +0.958 — passes free gate
      move Barnes → Ødegaard: +0.104 / -1.556 — fails (prior sign flip)
P10 plan: Calafiori → De Cuyper, Barnes → McAtee — blend +1.757 prior +2.165; bank 1.0; transfers 2 (free 3, hits 0); FT next 2
      move Calafiori → De Cuyper: +2.361 / +1.596 — passes free gate
      move Barnes → McAtee: -0.617 / +0.284 — fails (blend < 2.0)
P11 plan: Calafiori → De Cuyper, Barnes → Rayan — blend +2.033 prior +0.327; bank 0.2; transfers 2 (free 3, hits 0); FT next 2
      move Calafiori → De Cuyper: +2.370 / +1.917 — passes free gate
      move Barnes → Rayan: -0.341 / -1.554 — fails (prior sign flip)
P12 plan: Mbeumo → Gibbs-White — blend -2.610 prior -2.347; bank 0.2; transfers 1 (free 3, hits 0); FT next 3
      move Mbeumo → Gibbs-White: -2.610 / -2.347 — fails (prior sign flip)
P13 plan: Barnes → McAtee — blend -0.604 prior +0.569; bank 0.6; transfers 1 (free 3, hits 0); FT next 3
      move Barnes → McAtee: -0.604 / +0.569 — fails (blend < 2.0)
P14 error: Calafiori → De Cuyper, Barnes → Gibbs-White: cannot afford — bank after -1.3
P15 error: Calafiori → De Cuyper, Justin → Muharemović: cannot afford — bank after -0.1
P16 error: Calafiori → Silva, Justin → De Cuyper: cannot afford — bank after -0.1
P17 error: Calafiori → De Cuyper, Trafford → Raya: cannot afford — bank after -0.7
```

P2–P13 all returned FAIL. P1 is the greedy reference and the only PASS.
After it, `objective` shows `after plan, best single: Barnes → Groß +0.621 /
-1.723 — fails (prior sign flip)`: no further move passes the free gate, so
the two remaining free transfers are banked as the rule requires. P3–P5 have
a larger blend total than P1 but each extra leg fails the gate on its own
marginal and turns the prior-only total toward or below zero (C14). No hit
is in range: a paid move needs +6.0 gross and the largest second marginal is
+1.985.

Moves named by open suggestions, graded with `--moves`:

| Row | Move | blend | prior | Verdict |
|---|---|---|---|---|
| S7 (named faller still owned; in 13,145 v out 130,298, price flat) | Mbeumo → Gibbs-White | −2.610 | −2.347 | P12 FAIL (prior sign flip) |
| S7 (fell 6.1 → 6.0 this event; in 4,703 v out 81,995) | Barnes → McAtee | −0.604 | +0.569 | P13 FAIL (blend < 2.0) |
| S7 (same player, best blend replacement beside the plan) | Barnes → Groß | +0.621 | −1.723 | P3 FAIL (prior sign flip) |
| S8 (names no move) | — | — | — | applied to the De Cuyper v Silva tie and the vice tie |

Fixture context (data/analysis/gw11/fixtures.md): BHA is ATT rank 2 over the
window (Σλ_att 10.43). De Cuyper against Calafiori by gameweek: 4.61 v 4.24,
4.91 v 3.61, 3.42 v 3.82, 3.63 v 3.98, 4.50 v 3.85, 4.85 v 4.23 — ahead in
four of six, including the last two, so this is not a one-good-fixture buy
that turns bad in two. His GW11 fixture, BHA v HUL (A), is a banded
clean-sheet row (P(CS) 0.36 ±, C12).

## Squad

Price = selling price (table above; De Cuyper at his purchase price); EP6 =
`ep_total6`; GW11 = `ep_gw[0]`; p = `p_start_gw[0]`.

| Pos | Player | Club | Price | p GW11 | GW11 EP | EP6 | Role |
|---|---|---|---|---|---|---|---|
| GKP | Trafford | LEE | 5.0 | 0.95 | 3.578 | 22.53 | XI |
| GKP | Kinsky | TOT | 4.4 | 0.95 | 3.468 | 19.90 | bench 12 |
| DEF | Gabriel | ARS | 8.0 | 0.95 | 5.229 | 29.62 | XI, vice |
| DEF | Van Hecke | TOT | 5.0 | 0.95 | 4.947 | 26.46 | XI |
| DEF | De Cuyper | BHA | 5.5 | 0.94 | 4.614 | 25.93 | XI (in) |
| DEF | Hill | BOU | 5.5 | 0.95 | 4.405 | 27.00 | XI |
| DEF | Justin | LEE | 4.5 | 0.94 | 3.538 | 23.44 | bench 14 |
| MID | E.Le Fée | SUN | 5.7 | 0.95 | 4.706 | 28.44 | XI |
| MID | Tavernier | BOU | 6.3 | 0.95 | 4.547 | 28.30 | XI |
| MID | Mbeumo | MUN | 7.9 | 0.95 | 4.288 | 28.66 | XI |
| MID | Gomez | BHA | 5.0 | 0.95 | 3.956 | 23.43 | bench 13 |
| MID | Barnes | NEW | 6.0 | 0.95 | 3.510 | 23.46 | bench 15 |
| FWD | Haaland | MCI | 15.6 | 0.94 | 6.047 | 34.90 | XI, captain |
| FWD | Isak | LIV | 9.1 | 0.93 | 5.306 | 29.41 | XI |
| FWD | Barry | EVE | 5.6 | 0.94 | 4.691 | 27.68 | XI |

Out: Calafiori (ARS, sell 5.9, p 0.90, GW11 EP 4.237, EP6 23.73).
Objective after the plan: 347.720 blend / 336.852 prior-only (baseline
345.346 / 334.971 plus the plan's +2.374 / +1.881).

## Starting XI — 4-3-3

Trafford; Gabriel, Van Hecke, De Cuyper, Hill; E.Le Fée, Tavernier, Mbeumo;
Haaland (C), Isak, Barry. XI EP 58.405 with the captain doubled.

## Captaincy

Top 5 among the XI by single-GW EP, undiscounted (`objective`'s captain line):

| # | Player | GW11 EP | p_start_gw[0] | Gap to #1 |
|---|---|---|---|---|
| 1 | Haaland | 6.047 | 0.94 | — |
| 2 | Isak | 5.306 | 0.93 | 0.741 |
| 3 | Gabriel | 5.229 | 0.95 | 0.818 |
| 4 | Van Hecke | 4.947 | 0.95 | 1.100 |
| 5 | E.Le Fée | 4.706 | 0.95 | 1.341 |

Captain Haaland: 0.741 clear of Isak, outside the 0.5 tie band, so the
higher EP wins by the spec and no suggestion can reach the choice.

Vice: Isak 5.306 v Gabriel 5.229 is a 0.077 gap, inside 0.5, and the spec's
tie-break (p_start_gw[0] ≥ 0.85) holds both, so the tie is open to a
suggestion. S8 (standing: prefer the steadier record and the more consistent
club) breaks it toward Gabriel — ret5 4/5 v 3/5, p4 0.696 v 0.481,
uncertainty LOW v MED. Cost: 0.077 single-GW EP, paid only if Haaland does
not play. Vice: Gabriel.

## Bench order

12 Kinsky (GK) · 13 Gomez 3.956 · 14 Justin 3.538 · 15 Barnes 3.510, by GW11
EP (Step 3). With a 4-DEF XI any absent outfield starter brings Gomez first
(4-4-2, 3-4-3 and 4-3-3 with Gomez for a forward's place as 4-4-2 are all
legal).

Bench check: none

## Transfers

Calafiori → De Cuyper, free, cost 0. Marginal +2.374 blend / +1.881
prior-only: clears the free gate (blend ≥ 2.0, prior ≥ 0) on both readings.
One of three free transfers used; 3 at the GW12 deadline.

Gate ids: 385,496,4,112,115,60,332,542,68,427,127,453,411,379,249

## Chips

`chip: null`. Chips available (bootstrap `chips`, set 1): bboost GW1–19,
freehit GW2–19; 3xc played GW9, wildcard played GW8. One chip per GW.

Free hit, graded on GW11 alone with `objective --chip freehit`. Verbatim:

```
objective gw11 — horizon GW11–GW11; squad from data/decisions/gw10/final.md
baseline: blend 58.028 prior 55.778
plan: Calafiori → De Cuyper, Mbeumo → Doku — blend +0.690 prior +0.555; bank 0.9; transfers 2 under freehit (FT unchanged (3)); chip gate: ≥ 6.0 over the greedy plan
  move Calafiori → De Cuyper: +2.518 / +1.883 — chip package
  move Mbeumo → Doku: -4.037 / -3.776 — chip package
verdict: FAIL: freehit fails the chip gate: +0.313 / +0.276 over the greedy plan (need blend ≥ 6.0, prior ≥ 0)
```

The squad already starts the top GW11 scorer in most slots; the largest
single-GW upgrade on the files is the De Cuyper move itself (+0.377 on GW11
alone), so no package reaches 6.0. Wildcard: set-1 chip already played.

Bench boost: not played. The spec has no `objective` reading for bboost,
only the earmark; the GW11 bench is 14.472 (3.468 + 3.956 + 3.538 + 3.510).
The GW19 earmark stands.

Provisional chip plan: freehit GW16 (placeholder; no blank or double in
GW11–16 per fixtures.md); bboost GW19 (last set-1 gameweek). Windows from
bootstrap `chips`: freehit GW2–19, bboost GW1–19.

## Analyst escalations weighed

| Escalation | Effect on this proposal |
|---|---|
| CHE goalkeeper start near a coin flip (Martinez / Penders) | none — neither is owned or bought; Kinsky → Penders is −0.041 / −0.168 |
| MCI back four unclear (Guéhi, Gvardiol 75%) | none — no MCI defender owned or bought |
| Virgil and N.Williams at 75% | none — Calafiori → N.Williams −0.043 / +0.108 fails; Virgil is not in the top singles |
| Awoniyi, Osula, B.Fernandes EP inflated per share check | B.Fernandes appears only in P6 and P8, both FAIL on the funding leg, so the inflated figure decides nothing; neither Awoniyi nor Osula is in any plan |
| GW13 midweek round and European/cup rotation not priced into p_start for ARS, CHE, LIV, MCI, NEW, TOT | The move sells an ARS full-back already at p_start 0.90 for a BHA starter with no European fixtures, so unpriced rotation would add to the gain, not reduce it. Owned players exposed and held: Gabriel, Haaland, Isak, Barnes, Van Hecke, Kinsky. `objective` cannot price this; the figures above do not include it. |

## Rationale and rejected alternatives

| Alternative | blend / prior | Why not |
|---|---|---|
| Bank all three | +0.000 / +0.000 | a free move passes the gate on both readings; the rule says take it |
| Calafiori → Silva | +2.042 / +0.646 | passes the gate but loses the tie-break to De Cuyper (ret5 4/5 v 3/5) and is lower on both readings; `objective` FAILs a plan that departs from the reference; it would also put three BOU players in the squad |
| + Barnes → Groß | +0.621 / −1.723 marginal | best second move; fails on blend and flips sign prior-only (C14) |
| + Barnes → Gibbs-White (funded by Isak → N.Jackson) | +1.985 / +0.039 marginal | 0.015 short of the gate, and the funding leg loses 3.618 / 4.374 |
| Mbeumo → B.Fernandes (funded by Isak → Calvert-Lewin) | +2.621 / +3.672 marginal | the funding leg loses 3.767 / 2.929; plan total +0.896 |
| Haaland → N.Jackson + Barnes → B.Fernandes | −3.042 / −4.110 plan | the Haaland leg loses 11.761 |
| Mbeumo → Gibbs-White | −2.610 / −2.347 | S7 named-faller check; a loss on both readings |
| Any hit | — | no fourth move exists that passes; the best second marginal is +1.985 against 6.0 |
| Free hit | +0.313 / +0.276 over the greedy plan | fails the 6.0 chip gate |
| Captain Isak | 5.306 v 6.047 | 0.741 below Haaland, outside the 0.5 band |
| Vice Isak | +0.077 single-GW EP in the vice slot | inside the 0.5 band; S8 prefers Gabriel's steadier record |

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
| S7 | 7 | standing | honoured as a sell-side policy: of the named fallers only Mbeumo is still owned, a net faller again this event (in 13,145 v out 130,298, price 7.9 unchanged) but Mbeumo → Gibbs-White is −2.610 / −2.347 FAIL, not a small gap, so he is held; Barnes fell 6.1 → 6.0 this event (in 4,703 v out 81,995) and no sale of him passes the gate: Barnes → Groß +0.621 / −1.723 beside the plan (prior sign flip), Barnes → McAtee −0.604 / +0.569, Barnes → Gibbs-White +1.985 / +0.039 only inside a plan whose Isak leg loses 3.618; Haaland is net out (in 29,389 v out 55,842, price flat) and Haaland → N.Jackson loses 11.761 / 11.932; the one transfer made sells Calafiori, a net riser, on EP alone, with no rival transfer inside a small gap for the row to prefer; the policy never overrides the gate; EP6 delta of the row 0.00 |
| S8 | 7 | standing | honoured: the one buy is De Cuyper (BHA, 10/10 starts, ret5 4/5, BHA ATT rank 2), a nailed starter with the steadier record of the two close options — objective's line `tie-break move: Calafiori → De Cuyper +2.374 v Calafiori → Silva +2.042 — winner Calafiori → De Cuyper (ret5 4/5 v 3/5)` and its group line ends (decided by blend), so the steer and the blend agree and the row costs 0.00 EP6 there; it also breaks the vice tie, Isak 5.306 v Gabriel 5.229 inside 0.5 single-GW EP with both at p_start 0.93 or above, toward Gabriel (ret5 4/5 v 3/5, p4 0.696 v 0.481, uncertainty LOW v MED), at −0.077 single-GW EP in the vice slot only; it cannot reach the captaincy, Haaland 6.047 v Isak 5.306 being 0.741 apart; EP6 delta of the row 0.00 |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW12 deadline: 3 live at GW11 (auth-check, relayed) − 1 used + 1 accrued (objective: FT next 3).
# team_value 99.6 = selling-price sum 99.1 + bank 0.5 after Calafiori (sell 5.9) → De Cuyper (buy 5.5); the live budget relayed on 2026-11-20 was 99.6.
gw: 11
team_id: 8455344
team_value: 99.6
bank: 0.5
free_transfers_banked: 3
chip: null
chips_used:
  - {chip: wildcard, gw: 8}
  - {chip: 3xc, gw: 9}
transfers_made:
  - {out: Calafiori, in: De Cuyper, cost: 0}
chip_plan:
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 385, name: Trafford, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: false, vice: true}
  - {id: 112, name: Van Hecke, position: 3, captain: false, vice: false}
  - {id: 115, name: De Cuyper, position: 4, captain: false, vice: false}
  - {id: 60, name: Hill, position: 5, captain: false, vice: false}
  - {id: 542, name: E.Le Fée, position: 6, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 7, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: true, vice: false}
  - {id: 379, name: Isak, position: 10, captain: false, vice: false}
  - {id: 249, name: Barry, position: 11, captain: false, vice: false}
  - {id: 496, name: Kinsky, position: 12, captain: false, vice: false}
  - {id: 127, name: Gomez, position: 13, captain: false, vice: false}
  - {id: 332, name: Justin, position: 14, captain: false, vice: false}
  - {id: 453, name: Barnes, position: 15, captain: false, vice: false}
```
