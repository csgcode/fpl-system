# GW7 Squad Proposal (2026/27) — re-run, no chip

Deadline 2026-10-17T10:00:00Z. Weekly cycle; squad from the STATE block of
data/decisions/gw6/final.md. Selling prices relayed by the orchestrator
(`my-team`, auth-check PASS today: 1 free transfer, sell sum 98.8, bank 0.3),
resolved per id from the GW6 sell column plus the bootstrap price moves since
(Gabriel 8.0 → 7.9 is the only fall; derived sum 98.8 equals the relayed
figure). Budget 99.1.

Re-run on a user directive: no chip of any kind this gameweek. The archived
squad-proposal.v1.md proposed the set-1 wildcard; its wildcard package is off
the table here and the wildcard is re-earmarked for GW8 (provisional). The
no-chip plan is regraded from scratch below; the figures reproduce v1's
no-chip rows exactly because the GW7 analysis files are unchanged.

**Decision: one free transfer, Thiaw → Van Hecke (sell 5.0, buy 4.9),
hit 0, bank 0.4, FT next 1. `chip: null`. 3-4-3, Haaland (C), Mbeumo (V).
Predicted GW7 54.855. Plan gain +2.223 blend / +1.214 prior-only over
GW7–12; banking the transfer fails the rule because this move passes the
free gate.**

## Inputs read

- data/analysis/gw7/players-{GKP,DEF,MID,FWD}.json (+ .md), fixtures.md,
  fixtures-tables.md — current; no analyst re-run.
- data/retro/gw6.md via `fpl corrections --gw 7 --agent A4`: C5, C8, C14,
  C15, C20 active (C6, C16 retired).
- data/decisions/gw7/review.md (review of the wildcard proposal): F6 (GK2
  dead, bboost blocked until repaired) and F1's two-sided price exposure
  carry over to any plan; F2–F5 and F7–F9 concern wildcard pairs that are
  not made here.
- data/suggestions.md — S# set fixed at the cycle's first run: read through
  S8 (rows added since wait for GW8). GW6 ledger in
  data/decisions/gw6/final.md.
- Bootstrap chips: wildcard / freehit GW2–19, bboost / 3xc GW1–19 (set 1);
  set 2 GW20–38. No chip used.
- data/raw/gw7/players/summary-*.json for per-round points in the S8
  comparison.

Every EP figure below is printed by `fpl objective --gw 7 --sell … --bank
0.3 --free-transfers 1`.

## Budget skeleton (step 1)

Weekly cycle, one free transfer: the premium structure is inherited, not
re-chosen. Haaland £15.5m is the one premium; B.Fernandes / Saka are
wildcard-scale moves (Tavernier → Saka needs £3.6m the bank does not hold,
and a two-transfer funding route costs a hit the gate refuses below). The
budget is exhausted to 0.4 after the plan (≤ 0.5 rule met).

## Baseline and single moves (steps 2 and 4)

```
sell basis: relayed (Σ sell 98.8 + bank 0.3 = 99.1)
baseline: blend 318.730 prior 313.869
legal single moves: 1555 (pool 417); top 20 by blend:
  1 | Thiaw → Silva | +4.017 | -0.634 | bank 0.3 | fails (prior sign flip)
  2 | Tarkowski → Silva | +2.489 | -1.414 | bank 1.4 | fails (prior sign flip)
  3 | Richards → Silva | +2.366 | -1.943 | bank 0.2 | fails (prior sign flip)
  4 | Thiaw → Van Hecke | +2.223 | +1.214 | bank 0.4 | passes free gate
  5 | Schade → Sávio | +2.005 | +3.634 | bank 0.0 | passes free gate
  6 | Thiaw → De Cuyper | +1.777 | -0.231 | bank 0.2 | fails (prior sign flip)
  7 | Thiaw → Muharemović | +1.774 | -0.388 | bank 0.3 | fails (prior sign flip)
  8 | Tarkowski → Hill | +1.744 | +1.458 | bank 0.9 | fails (blend < 2.0)
  9 | Shaw → Justin | +1.219 | +0.968 | bank 0.1 | fails (blend < 2.0)
  10 | Tarkowski → Calafiori | +1.217 | -0.034 | bank 0.5 | fails (prior sign flip)
  11 | Thiaw → Khalaili | +1.092 | -1.379 | bank 0.3 | fails (prior sign flip)
  12 | Thiaw → Vuskovic | +1.010 | -1.104 | bank 0.2 | fails (prior sign flip)
  13 | Thiaw → Justin | +0.995 | +0.298 | bank 0.8 | fails (blend < 2.0)
  14 | Tarkowski → Mukiele | +0.878 | -1.491 | bank 1.0 | fails (prior sign flip)
  15 | Tarkowski → Guéhi | +0.743 | +1.064 | bank 0.4 | fails (blend < 2.0)
  16 | Schade → Stach | +0.740 | -0.427 | bank 0.5 | fails (prior sign flip)
  17 | Shaw → Ajer | +0.681 | +0.872 | bank 0.1 | fails (blend < 2.0)
  18 | Raya → Trafford | +0.662 | +0.460 | bank 1.3 | fails (blend < 2.0)
  19 | Shaw → Konsa | +0.611 | +0.088 | bank 0.0 | fails (blend < 2.0)
  20 | Tarkowski → Van Hecke | +0.572 | +0.380 | bank 1.5 | fails (blend < 2.0)
```

Two of 1555 legal singles pass the free gate. Graded plans:

| Plan | `objective --moves` | Verdict |
|---|---|---|
| bank the FT | `plan: none — blend +0.000 prior +0.000; bank 0.3; transfers 0 (free 1, hits 0); FT next 2` | FAIL: further free move passes: Thiaw → Van Hecke +2.223 / +1.214; plan gain +0.000 below the greedy reference +2.223 |
| **A: Thiaw → Van Hecke** | `plan: Thiaw → Van Hecke — blend +2.223 prior +1.214; bank 0.4; transfers 1 (free 1, hits 0); FT next 1` | **PASS** |
| B: Schade → Sávio | `plan: Schade → Sávio — blend +2.005 prior +3.634; bank 0.0; transfers 1 (free 1, hits 0); FT next 1` | FAIL: plan gain +2.005 below the greedy reference +2.223 |
| A + B (one hit) | `plan: Thiaw → Van Hecke, Schade → Sávio — blend +4.228 prior +4.848; bank 0.1; transfers 2 (free 1, hits 4); FT next 1` | FAIL: Schade → Sávio +2.005 / +3.634 fails the hit gate (blend ≥ 6.0, prior > 0) |

Plan A's full print:

```
plan: Thiaw → Van Hecke — blend +2.223 prior +1.214; bank 0.4; transfers 1 (free 1, hits 0); FT next 1
  move Thiaw → Van Hecke: +2.223 / +1.214 — passes free gate
after plan, best single: Schade → Sávio +2.005 / +3.634 — passes free gate
reference (greedy): Thiaw → Van Hecke +2.223 / +1.214 — blend +2.223 prior +1.214
verdict: PASS
GW7 XI 3-4-3 54.855: Raya, Van Hecke, Gabriel, Tarkowski, Mbeumo, Groß, Tavernier, E.Le Fée, Haaland, Barry, Thiago; captain top 5: Haaland 6.579 0.93, Van Hecke 4.596 0.92, Barry 4.582 0.90, Mbeumo 4.572 0.93, Groß 4.435 0.93
boundary pairs within 0.25: none
bench: Dubravka 0.123 (p 0.03 — dead), Richards 3.089, Schade 2.761, Shaw 1.907
```

"After plan, best single" names Schade → Sávio as still passing the free
gate, but no free transfer is left after plan A (FT next 1 is the accrual
for GW8), so the rule's "no further move passing the free gate with free
transfers left" clause is satisfied; as a paid second move it fails the hit
gate (table above).

### Why transfer rather than bank

Banking is a valid outcome only when no move passes the free gate. One
does, on both readings, so the rule makes the move. The cost of banking is
measurable: 2.223 EP6 forgone on blend, 0.806 of it in GW7 alone (XI 54.855
v 54.049). The case for holding — two free transfers at GW8 — is weakened by
the wildcard earmark: a GW8 wildcard does not consume free transfers, and
if it is not played, 1 free transfer at GW8 plus Van Hecke already in is
the same squad position the 2-FT route would reach by making this move
then.

### The move itself

| | Thiaw (NEW, id 445) | Van Hecke (TOT, id 112) |
|---|---|---|
| Price | sell 5.0 | buy 4.9 |
| EP6 (blend) | 20.20 | 23.47 |
| ep_gw GW7–12 | 3.79, 3.17, 3.69, 3.46, 3.05, 3.04 | 4.60, 3.42, 3.97, 3.55, 4.26, 3.69 |
| p_start | 0.92, LOW, 6/6 full 90s | 0.92, LOW, 6/6 full 90s, flag cleared (chance 100) |
| Points R1–R6 | 3, 6, −1, 2, 4, 0 = 14 (1 return ≥ 5) | 1, 1, 8, 8, 6, 3 = 27 (3 returns ≥ 5) |
| Club CS rank (GW7–12) | NEW 19; turns hard from GW10 (−0.70 Σλ_att, −0.14 ΣP(CS)) | TOT 4; GW10–12 swing −0.46 / −0.05 |
| Largest EP term | appearance 11.04; defcon 4.82 | appearance 11.04; clean_sheet 6.44 over six rounds |
| Price pressure this event | 17.4k out v 1.6k in (net −15.8k), no change yet | 22.1k out v 46.2k in (net +24.1k), no change yet |

- Not a one-fixture buy: Van Hecke leads Thiaw on every one of the six rows,
  by 1.94 over GW10–12 (11.49 v 9.55) where NEW's ticker turns hard; TOT's
  own swing is −0.46 and stays ahead.
- C12: the GW7 TOT v COV (H) row is banded (P(CS) 0.41 ±), but Van Hecke's
  single largest term is appearance, then a six-round clean-sheet term;
  the banded row is not his largest term. His EP6 lead over Thiaw also holds
  with GW7 removed (18.87 v 16.41).
- C14: positive on both readings (+2.223 / +1.214); no hit involved.
- Prior-only view: TOT's defence is rated on 3210 prior minutes
  (prior_weight 0.526); the prior reading keeps the move positive.

### Rejected moves

| Move | Figure | Why rejected |
|---|---|---|
| Thiaw → Silva | +4.017 / −0.634 | prior sign flip (C14); below the 6.0 hit gate in any case |
| Schade → Sávio (plan B) | +2.005 / +3.634 | FAIL on the greedy reference (0.218 below A); S8 also prefers A — Sávio 10 pts, 330', 0 returns v Van Hecke 27 pts, 3 returns |
| Tarkowski → Hill | +1.744 / +1.458 | blend < 2.0 |
| Shaw → Justin | +1.219 / +0.968 | blend < 2.0; Shaw is bench 3 at p 0.70 (d 75%), scored at 0 by the objective; a GW8 wildcard repairs DEF5 free |
| Raya → Trafford | +0.662 / +0.460 | blend < 2.0 |
| Any hit | best gross two-move +4.228 | hit gate needs ≥ 6.0 gross |
| Free hit GW7 | not graded | user directive: no chip this GW |
| Wildcard GW7 | v1 graded +16.239 / +3.979 (chip gate PASS) | user directive: no chip this GW; re-earmarked GW8, provisional |

## Squad after the transfer (step 2)

| Slot | Pos | Player | Id | Club | Price | GW7 EP | EP6 | p_start | Unc | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|---|
| 1 | GKP | Raya | 1 | ARS | 6.0 | 3.343 | 21.18 | 0.94 | LOW | XI |
| 2 | DEF | Van Hecke | 112 | TOT | 4.9 | 4.596 | 23.47 | 0.92 | LOW | XI · IN |
| 3 | DEF | Gabriel | 4 | ARS | 7.9 | 4.062 | 26.27 | 0.92 | LOW | XI |
| 4 | DEF | Tarkowski | 229 | EVE | 6.1 | 3.793 | 22.90 | 0.92 | LOW | XI |
| 5 | MID | Mbeumo | 427 | MUN | 7.9 | 4.572 | 28.79 | 0.93 | LOW | XI · Vice |
| 6 | MID | Groß | 124 | BHA | 5.9 | 4.435 | 24.66 | 0.93 | LOW | XI |
| 7 | MID | Tavernier | 68 | BOU | 6.0 | 4.274 | 24.32 | 0.90 | LOW | XI |
| 8 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.006 | 26.11 | 0.92 | LOW | XI |
| 9 | FWD | Haaland | 411 | MCI | 15.5 | 6.579 | 35.06 | 0.93 | LOW | XI · Captain |
| 10 | FWD | Barry | 249 | EVE | 5.6 | 4.582 | 25.38 | 0.90 | LOW | XI |
| 11 | FWD | Thiago | 106 | BRE | 7.8 | 4.034 | 25.14 | 0.92 | LOW | XI |
| 12 | GKP | Dubravka | 497 | TOT | 4.0 | 0.123 | 0.68 | 0.03 | HIGH | Bench GK |
| 13 | DEF | Richards | 202 | CRY | 4.9 | 3.089 | 22.19 | 0.92 | LOW | Bench 1 |
| 14 | MID | Schade | 94 | BRE | 6.2 | 2.761 | 22.12 | 0.65 | LOW | Bench 2 |
| 15 | DEF | Shaw | 423 | MUN | 4.3 | 1.907 | 11.96 | 0.70 | MED | Bench 3 |
| | | **Total** | | | **98.7** | | | | | |

Price = selling price for kept players, purchase price for Van Hecke.
GW7 EP and EP6 from data/analysis/gw7/players-{pos}.json; the XI rows sum
to the objective's 48.276. 2 GKP / 5 DEF / 5 MID / 3 FWD.
Club counts ARS 2, EVE 2, MUN 2, BRE 2, TOT 2 (Van Hecke, Dubravka), all
others 1. Bank 0.4.

## Bench strategy (step 3)

One playing goalkeeper (Raya, 0.94) plus a dead £4.0m backup. Raya →
Trafford grades +0.662 / +0.460, below the gate; a £4.5m playing second
keeper needs a DEF downgrade and the objective scores GK2 at 0 either way.
GK2 therefore stays dead (R1, review F6) and is the first repair candidate
for the GW8 wildcard, or for the GW8 free transfer if the wildcard waits.

Outfield bench: Richards £4.9m (0.92, 6/6 × 90, 18 pts) is the only nailed
cover; Schade (0.65 for GW7, shoulder, d 75%; 0.85–0.88 from GW8) and Shaw
(0.70, d 75%) are the two flagged rows. Both are wildcard-scale repairs:
neither has a free move that passes the gate (Shaw → Justin +1.219 is the
best).

## Starting XI — 3-4-3

| Slot | Player | Pos | GW7 fixture | GW7 EP |
|---:|---|---|---|---:|
| 1 | Raya | GKP | NFO (A) | 3.343 |
| 2 | Van Hecke | DEF | COV (H) ± | 4.596 |
| 3 | Gabriel | DEF | NFO (A) | 4.062 |
| 4 | Tarkowski | DEF | CHE (H) | 3.793 |
| 5 | Mbeumo (V) | MID | LEE (A) | 4.572 |
| 6 | Groß | MID | CRY (H) | 4.435 |
| 7 | Tavernier | MID | SUN (H) | 4.274 |
| 8 | E.Le Fée | MID | BOU (A) | 4.006 |
| 9 | Haaland (C) | FWD | IPS (H) ± | 6.579 |
| 10 | Barry | FWD | CHE (H) | 4.582 |
| 11 | Thiago | FWD | LIV (H) | 4.034 |
| | XI total | | | 48.276 |
| | + captain | | | 6.579 |
| | **Predicted GW7** | | | **54.855** |

XI total 48.276 is the sum of the eleven `ep_gw[0]` rows and equals the
objective's 54.855 less the captain's 6.579. Boundary: `objective` reports no
XI/bench pair within 0.25 (C20 does not bite): Thiago 4.034 sits 0.945
above Richards 3.089, so 3-4-3 holds over 4-4-2.

## Captain and vice

Top 5 among the XI by single-GW EP, undiscounted (`captain top 5` line):

| Rank | Player | GW7 EP | p_start_gw[0] | Points R1–R6 |
|---:|---|---:|---:|---|
| 1 | Haaland | 6.579 | 0.93 | 45 |
| 2 | Van Hecke | 4.596 | 0.92 | 1, 1, 8, 8, 6, 3 |
| 3 | Barry | 4.582 | 0.90 | 8, 2, 2, 2, 6, 6 |
| 4 | Mbeumo | 4.572 | 0.93 | 2, 11, 8, 2, 2, 8 |
| 5 | Groß | 4.435 | 0.93 | 53 total |

- **Captain Haaland** — gap to #2 is 1.983, far outside the 0.5 tie band.
  The IPS (H) row is banded (±) but he leads the field on every row of the
  window; C5 concerns the 3xc, which stays earmarked for GW9 (BHA (H),
  λ_att 2.09, not banded).
- **Vice Mbeumo** — #2 to #4 sit inside 0.024 (4.596 / 4.582 / 4.572), all
  at p_start ≥ 0.85, so the spec's tiebreak does not separate them. S8 breaks
  the tie inside the 0.5 single-GW band: Mbeumo has the steadiest points
  record of the three (33 pts, three returns of 8+, 6/6 × 90, p 0.93 the
  highest) and his row does not lean on a banded promoted-club P(CS) as
  Van Hecke's GW7 row does (COV (H) 0.41 ±). Different club and fixture
  from the captain.

## Bench order

| Slot | Player | Pos | GW7 EP | p_start_gw[0] |
|---:|---|---|---:|---:|
| 12 | Dubravka | GKP | 0.123 | 0.03 |
| 13 | Richards | DEF | 3.089 | 0.92 |
| 14 | Schade | MID | 2.761 | 0.65 |
| 15 | Shaw | DEF | 1.907 | 0.70 |

Gaps 0.328 and 0.854 are outside C8's 0.25 band; EP order stands and no
DefCon tie-break is needed. Richards first: the only bench row above 0.85
p_start and a DEF, so a single DEF absence keeps three defenders.

## Transfers

| Out | In | Sell | Buy | Cost |
|---|---|---:|---:|---:|
| Thiaw (NEW, DEF, id 445) | Van Hecke (TOT, DEF, id 112) | 5.0 | 4.9 | 0 |

Sells 5.0, buys 4.9, bank 0.3 → 0.4. One free transfer used; 1 accrues for
GW8 (free_transfers_banked 1).

Execution order: transfers first, then the lineup (the XI names Van Hecke).
Price exposure overnight (review F1, two-sided): Van Hecke is a net riser
this event (+24.1k) and Thiaw a net faller (−15.8k); a 0.1 rise on Van Hecke
or a 0.1 fall on Thiaw each leave the bank at 0.3, and both together 0.2 —
no combination of single-tick moves breaks the bank, so no fallback plan is
needed. POST today anyway so the sell price is the one graded.

## Chips

`chip: null` this GW — user directive, no chip of any kind. Set-1 windows
from bootstrap: wildcard / freehit GW2–19, bboost / 3xc GW1–19; none used.

Provisional chip plan: wildcard GW8 (the v1 package cleared the chip gate on
this week's EP by +14.016 / +2.765 over plan A; the GW8 cycle regrades it on
GW8–13, which already spans the GW10 fixture swing the analyst flags — MCI
harder, ARS / BHA / LIV easier), 3xc GW9 (Haaland v BHA (H), λ_att 2.09, not
banded — C5 holds), freehit GW16 (placeholder), bboost GW19 (placeholder;
needs GK2 repaired first). Van Hecke was in the v1 wildcard squad, so this
move is a step toward it, not against it. Only one chip per gameweek; a
GW8 wildcard and GW9 3xc do not clash.

## Money

Bank 0.4. team_value 99.1 (Σ selling prices after the transfer 98.7 + bank
0.4; kept players keep their GW6 selling prices, Van Hecke at purchase
price). Sell basis relayed.

Gate ids: 1,112,4,229,427,124,68,542,411,249,106,497,202,94,423

Bench check: Dubravka (12, 0.03) | none other

## Accepted risks

| # | Risk | Detail |
|---|---|---|
| R1 | GK2 dead | Dubravka 0.123 (p 0.03). Raya is a six-of-six starter; a Raya absence leaves the GK slot empty. First repair at the GW8 wildcard, or the GW8 free transfer if the wildcard waits (review F6) |
| R2 | Bench rows flagged | Schade d 75% (0.65 for GW7) and Shaw d 75% (0.70); auto-sub cover is Richards alone. Scored at 0 by the objective; no free move from either passes the gate |
| R3 | Template exposure | Unheld > 30%: João Pedro 70.9, Calafiori 52.7, Rogers 45.9, De Cuyper 37.3, Cherki 34.0, B.Fernandes 33.0 (review F3). Held: Haaland, Raya, Groß. No single move toward them passes the gate this week; the GW8 wildcard is the free moment to take cover |
| R4 | Van Hecke's GW7 row banded | COV (H) P(CS) 0.41 ±; his largest term is appearance, the buy stands on EP6 with GW7 excluded (18.87 v 16.41) |
| R5 | Promoted-club rows in the XI | Haaland v IPS, Van Hecke v COV, both banded; neither is a defensive largest-term pick (C12) |
| R6 | Free transfer spent before a possible wildcard | 1 FT at GW8 instead of 2. Costless if the wildcard is played; if not, the move's +2.223 / +1.214 is banked EP rather than a banked transfer |

## Suggestions

Read data/suggestions.md through S8

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 6 | followed | both halves now complete: Ndiaye → Groß and Anderson → Schade inside the +14.449 blend / +5.210 prior-only triple; Ndiaye's marginal +2.503 / +0.665 and Anderson's +2.488 / +0.757 each clear the 2.0 gate on their own, so the steer broke no tie and the optimizer reached it unaided; EP6 delta of the row itself 0.00. The GW5 ledger's "Ndiaye half completed" was false in fact (never POSTed) and is superseded here |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |
| S3 | 6 | followed | Ndiaye → Groß made; marginal +2.503 blend / +0.665 prior against the plan without this sale (Scott + Anderson → E.Le Fée + Schade, +11.946 / +4.545), so the below-threshold clause was not needed |
| S4 | 6 | followed | Anderson → Schade made; marginal +2.488 blend / +0.757 prior against the plan without this sale (Scott + Ndiaye → E.Le Fée + Groß, +11.961 / +4.453); clears the gate on both readings, below-threshold clause not needed |
| S5 | 6 | followed | Scott → E.Le Fée made; EP6 0.00 for GW6–11 (status i, 0%); marginal +2.503 / +0.675 against the plan without this sale (Ndiaye + Anderson → E.Le Fée + Schade, +11.946 / +4.535) |
| S6 | 6 | standing | honoured: the wildcard is not played at GW7 by user directive (chip null), so its timing moves to GW8, inside this row's window; the GW7 EP cleared the chip gate (v1: +16.239 / +3.979, +14.016 / +2.765 over plan A) and the GW8 cycle regrades it; the free move Thiaw → Van Hecke +2.223 / +1.214 lifts GW7 to 54.86 from 54.05; 60 per GW stays unreachable (best legal GW7 build 57.49). Completes `followed` at a GW8 wildcard, or `expired` after GW8 |
| S7 | 7 | standing | honoured: the one legal free move sells a faller — Thiaw (17.4k out v 1.6k in this event, sold at 5.0 before a drop) — though he is not a named row; of the named fallers Richards (0.6% owned, net −406), Thiago (net −34.5k), Shaw (net −62.7k) and Mbeumo (net −18.7k) have no move passing the gate (Shaw → Justin +1.219 / +0.968, Richards → Silva +2.366 / −1.943 sign flip, Thiago and Mbeumo absent from the top 20), none within 0.5 of plan A, so no in-band tie to settle; Gabriel (−0.1 this event, net −94k) held, no DEF move from him in the top 20; policy stays live for GW8 |
| S8 | 7 | standing | honoured: Van Hecke (27 pts, 3 returns ≥ 5, 6/6 × 90, TOT CS rank 4) over Sávio (10 pts, 0 returns, 330', TOT ATT rank 16) inside the 0.5 band on the package delta (+2.223 v +2.005 blend), the same way the objective's greedy reference falls; vice tie inside 0.5 single-GW EP broken to Mbeumo 4.572 (33 pts, three 8+ returns, p 0.93) over Van Hecke 4.596 (banded COV row) and Barry 4.582; the GW6 buys E.Le Fée, Groß and Schade are held because no move from them passes the gate (Schade → Sávio FAIL on reference, Schade → Stach +0.740 / −0.427) |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW8 deadline: 1 at GW7, 1 used, 1 accrues.
# team_value on the selling-price basis: kept players at GW6 sell prices + Van Hecke at purchase price = 98.7, bank 0.4.
gw: 7
team_id: 8455344
team_value: 99.1
bank: 0.4
free_transfers_banked: 1
chip: null
chips_used: []
transfers_made:
  - {out: Thiaw, in: Van Hecke, cost: 0}
chip_plan:
  - {chip: wildcard, gw: 8, status: provisional}
  - {chip: 3xc, gw: 9, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 1, name: Raya, position: 1, captain: false, vice: false}
  - {id: 112, name: Van Hecke, position: 2, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 3, captain: false, vice: false}
  - {id: 229, name: Tarkowski, position: 4, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 5, captain: false, vice: true}
  - {id: 124, name: Groß, position: 6, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 7, captain: false, vice: false}
  - {id: 542, name: E.Le Fée, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: true, vice: false}
  - {id: 249, name: Barry, position: 10, captain: false, vice: false}
  - {id: 106, name: Thiago, position: 11, captain: false, vice: false}
  - {id: 497, name: Dubravka, position: 12, captain: false, vice: false}
  - {id: 202, name: Richards, position: 13, captain: false, vice: false}
  - {id: 94, name: Schade, position: 14, captain: false, vice: false}
  - {id: 423, name: Shaw, position: 15, captain: false, vice: false}
```
