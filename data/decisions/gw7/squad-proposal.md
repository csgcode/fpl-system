# GW7 Squad Proposal (2026/27)

Deadline 2026-10-17T10:00:00Z. Weekly cycle; squad from the STATE block of
data/decisions/gw6/final.md. Selling prices relayed by the orchestrator
(`my-team`, auth-check PASS today: 1 free transfer, sell sum 98.8, bank 0.3)
and resolved per id from the GW6 sell column plus the bootstrap price moves
since (Gabriel 8.0 → 7.9 is the only fall; the derived sum is 98.8, equal to
the relayed figure). Budget 99.1.

**Decision: play the WILDCARD now (GW7), eight transfers, hit 0, bank 0.0.
3-4-3, Haaland (C), Saka (V). Predicted GW7 57.49. The one-move no-chip
alternative, Thiaw → Van Hecke, is +2.223 / +1.214 over GW7–12; the wildcard
is +16.239 / +3.979, an edge of +14.016 blend / +2.765 prior-only over the
chip gate's comparator (needs ≥ 6.0 / ≥ 0).**

## Inputs read

- data/analysis/gw7/players-{GKP,DEF,MID,FWD}.json (+ .md), fixtures.md,
  fixtures-tables.md.
- data/retro/gw6.md via `fpl corrections --gw 7 --agent A4`: C5, C8, C14,
  C15, C20 active (C6, C16 retired).
- data/suggestions.md (read through S8) and the GW6 ledger in
  data/decisions/gw6/final.md.
- Bootstrap chips: wildcard / freehit GW2–19, bboost / 3xc GW1–19 (set 1);
  set 2 GW20–38. No chip used yet.

Every EP figure below is printed by `fpl objective --gw 7 --sell … --bank 0.3
--free-transfers 1`; the wildcard squad search ran as scratch work in the
session scratchpad and only the `objective` grades are cited.

## Baseline and the no-chip plan

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

Graded no-chip plans:

| Plan | `objective --moves` | Verdict |
|---|---|---|
| bank the FT | `none` — blend +0.000 prior +0.000; FT next 2 | FAIL: further free move passes: Thiaw → Van Hecke +2.223 / +1.214 |
| A: Thiaw → Van Hecke | +2.223 / +1.214; bank 0.4; transfers 1 (free 1, hits 0); FT next 1; GW7 XI 54.855 | PASS |
| B: Schade → Sávio | +2.005 / +3.634; bank 0.0; GW7 XI 54.663 | FAIL: plan gain +2.005 below the greedy reference +2.223 |
| A + B with a hit | gross +4.2 blend | fails the hit gate (needs ≥ 6.0) — not graded further |

Plan A is the best legal no-chip plan and the chip gate's comparator. Plan B
has three times A's prior-only gain but is refused by the 0.05 reference
tolerance (backlog row).

## Wildcard

### Timing — GW7, not the GW8 earmark

GW6 deferred the wildcard to GW8 because the then-best rebuild leaned on
HIGH-uncertainty rows (Davis, Greaves, Simms) and forecast only +8.0. Both
conditions have reversed on the GW7 EP:

- every player bought is LOW uncertainty with p_start ≥ 0.88 (six at
  0.92–0.94), all of them six-of-six starters this season;
- the gain is +16.239 blend / +3.979 prior-only over GW7–12, against the
  +14.016 / +2.765 edge the gate requires over plan A (+6.0 / ≥ 0);
- the wildcard keeps the banked free transfer (FT unchanged at 1, so 2 at the
  GW8 deadline), whereas plan A spends it;
- the GW7 XI rises from 54.855 (plan A) to 57.492, and the fixture swing the
  analyst flags from GW10 (MCI harder; ARS, BHA, LIV, LEE easier) is already
  inside the scoring window, so waiting a week buys no fixture information.

What waiting would buy is one more round of minutes evidence (C18 overshoot
re-read at GW8). That is a calibration question, not an EP one; the gate is
cleared by more than double on blend.

### Budget skeleton (step 1)

Premiums (> £9m): Haaland £15.6m and Saka £9.6m; B.Fernandes £11.9m not taken.

| Premium | Kept because | Checked against |
|---|---|---|
| Haaland 35.06 | best build without him is +11.040 / +1.447 (B.Fernandes + João Pedro + Calafiori + Muharemović with the freed money): −5.2 blend, −2.5 prior against this plan | scratch search excluding id 411, graded on the same objective |
| Saka 32.10 | best build without him is +13.251 / +5.064 (B.Fernandes + Gomez + Hill + Calafiori): −3.0 blend against this plan; the +1.1 prior does not cover it | scratch search excluding id 12 |
| B.Fernandes 31.28 at £11.9m | Saka scores more for £2.3m less; the two together need the dead-GK2 money and a £4.0m DEF5 | no build with both inside 99.1 beat this plan |

### Squad (step 2)

| Slot | Pos | Player | Id | Club | Price | GW7 EP | EP6 | p_start | Unc | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|---|
| 1 | GKP | Trafford | 385 | LEE | 5.0 | 3.599 | 21.85 | 0.94 | LOW | XI · IN |
| 2 | DEF | Van Hecke | 112 | TOT | 4.9 | 4.596 | 23.47 | 0.92 | LOW | XI · IN |
| 3 | DEF | Silva | 566 | BOU | 5.0 | 4.479 | 25.39 | 0.92 | LOW | XI · IN |
| 4 | DEF | Gabriel | 4 | ARS | 7.9 | 4.062 | 26.27 | 0.92 | LOW | XI |
| 5 | MID | Saka | 12 | ARS | 9.6 | 4.878 | 32.10 | 0.92 | LOW | XI · Vice · IN |
| 6 | MID | Sávio | 403 | TOT | 6.5 | 4.620 | 25.78 | 0.92 | LOW | XI · IN |
| 7 | MID | Mbeumo | 427 | MUN | 7.9 | 4.572 | 28.79 | 0.93 | LOW | XI |
| 8 | MID | Groß | 124 | BHA | 5.9 | 4.435 | 24.66 | 0.93 | LOW | XI |
| 9 | FWD | Haaland | 411 | MCI | 15.5 | 6.579 | 35.06 | 0.93 | LOW | XI · Captain |
| 10 | FWD | Barry | 249 | EVE | 5.6 | 4.582 | 25.38 | 0.90 | LOW | XI |
| 11 | FWD | Gonzalo | 569 | FUL | 6.1 | 4.511 | 24.64 | 0.90 | LOW | XI · IN |
| 12 | GKP | Dubravka | 497 | TOT | 4.0 | 0.123 | 0.68 | 0.03 | HIGH | Bench GK |
| 13 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.006 | 26.11 | 0.92 | LOW | Bench 1 |
| 14 | DEF | Justin | 332 | LEE | 4.5 | 3.637 | 21.77 | 0.88 | LOW | Bench 2 · IN |
| 15 | DEF | Khalaili | 588 | CRY | 5.0 | 3.074 | 22.31 | 0.90 | LOW | Bench 3 · IN |
| | | **Total** | | | **99.1** | | **364.26** | | | |

Price = selling price for kept players, purchase price for ins. 2 GKP / 5 DEF
/ 5 MID / 3 FWD. Club counts ARS 2, TOT 3 (Van Hecke, Sávio, Dubravka), LEE 2,
all others 1. Bank 0.0 — the budget is exhausted (≤ 0.5 rule met).

### Bench strategy (step 3)

One playing goalkeeper plus a dead £4.0m backup. Trafford is the position's
top EP6 (21.85) on a 0.94 six-of-six start streak; a playing £4.5m second
keeper (Kinsky, Leno) costs £0.5m the squad does not have without a DEF
downgrade, and a rotating pair adds only the per-GW max over two similar
keepers. Dubravka is kept rather than swapped for another £4.0m dead keeper:
Dubravka → Steele grades +0.000 / +0.000 and would be a ninth POST for
nothing. GK2 therefore stays dead (R1 carried; Bench check below) and is the
first free-transfer repair candidate after the wildcard.

Outfield bench: Justin £4.5m (0.88, six starts, 3 returns ≥ 5 in 6 rounds)
and Khalaili £5.0m (0.90, 2 returns) are nailed cheap starters; E.Le Fée is
the 3-5-2 swing man. No bench slot is a rotation risk.

### Swap pass (step 4)

The wildcard package, every pair graded by `objective --chip wildcard --moves`:

```
plan: Raya → Trafford, Tarkowski → Van Hecke, Thiaw → Silva, Tavernier → Saka, Schade → Sávio, Thiago → Gonzalo, Richards → Khalaili, Shaw → Justin — blend +16.239 prior +3.979; bank 0.0; transfers 8 under wildcard (FT unchanged (1)); chip gate: ≥ 6.0 over the greedy plan
  move Raya → Trafford: +0.662 / +0.460 — chip package
  move Tarkowski → Van Hecke: +0.403 / +0.415 — chip package
  move Thiaw → Silva: +3.066 / -0.556 — chip package
  move Tavernier → Saka: +8.588 / +3.458 — chip package
  move Schade → Sávio: +2.076 / +3.634 — chip package
  move Thiago → Gonzalo: +0.065 / -2.778 — chip package
  move Richards → Khalaili: +0.247 / -1.713 — chip package
  move Shaw → Justin: +0.804 / +1.205 — chip package
after plan, best single: none legal
reference (greedy): Thiaw → Van Hecke +2.223 / +1.214 — blend +2.223 prior +1.214
verdict: PASS
GW7 XI 3-4-3 57.492: Trafford, Van Hecke, Silva, Gabriel, Saka, Sávio, Mbeumo, Groß, Haaland, Barry, Gonzalo; captain top 5: Haaland 6.579 0.93, Saka 4.878 0.92, Sávio 4.620 0.92, Van Hecke 4.596 0.92, Barry 4.582 0.90
boundary pairs within 0.25: none
bench: Dubravka 0.123 (p 0.03 — dead), E.Le Fée 4.006, Justin 3.637, Khalaili 3.074
```

Alternative wildcard builds graded on the same command (all PASS the chip
gate; none beats the plan on blend):

| Build | Change against the plan | Blend / prior | Why not |
|---|---|---|---|
| V3 | sell Gabriel; Hill, Calafiori, Mukiele in; Wissa for Gonzalo | +15.843 / +5.575 | −0.40 blend, inside the 0.5 band; S8 settles it for Gabriel (ARS, 27 pts, 3 returns in 6) over Hill (14 pts, 0 returns) — see Suggestions |
| V2 | Trafford + Kelleher pair; Khalaili for Tarkowski, Hill for Gabriel | +15.966 / +1.870 | −0.27 blend and −2.1 prior for a second keeper the objective scores at 0 |
| keep Tarkowski | best build holding id 229 | +15.171 / +1.729 | −1.07 blend, −2.25 prior: holding him forces Gabriel out for Hill |
| keep Tarkowski + Gabriel | best build holding 229 and 4 | +14.452 / +3.776 | −1.79 blend; needs a £4.0m DEF5 (Thomas, COV) and Gomez for Groß |
| João Pedro | best build holding id 165 | +15.214 / +1.892 | −1.03 blend, −2.09 prior; he is MED at 0.86 and the squad loses Gabriel |
| Calvert-Lewin for Gonzalo | 106:346 | +15.278 / +5.920 | −0.96 blend, outside the band; the prior gain does not move the gate |

Single-pair notes:

- Tavernier → Saka is the move: +8.588 / +3.458 on its own, positive on both
  readings, and funded by Raya → Trafford (+0.662 / +0.460) and Tarkowski →
  Van Hecke (+0.403 / +0.415).
- Thiaw → Silva (+3.066 / −0.556), Thiago → Gonzalo (+0.065 / −2.778) and
  Richards → Khalaili (+0.247 / −1.713) are blend-positive, prior-negative
  pairs. C14 forbids sign-flipping hits; these are free wildcard pairs inside
  a package that is +3.979 on prior-only. Each is the best affordable option
  for its slot: no DEF within 0.5 EP6 of Silva costs ≤ £5.0m (Calafiori
  24.01 is £0.9m more), no FWD within 0.5 of Gonzalo fits the bank (Wissa
  £6.3m needs £0.2m; Calvert-Lewin graded above), and Khalaili over Richards
  is the within-band call S7 and S8 both make (below).
- Schade → Sávio (+2.076 / +3.634): Schade is `d` 75% (shoulder, 51' in GW6,
  p_start 0.65 for GW7); Sávio is 0.92 on a four-start streak.
- Shaw → Justin (+0.804 / +1.205): Shaw is `d` 75% at 0.70; Justin 0.88.

### Never transfer for one good fixture

No move above targets a GW7 fixture: Saka, Sávio, Silva, Van Hecke, Gonzalo
and Trafford all keep their EP6 rank through GW12. The three GW7 promoted-club
rows in the squad (Haaland v IPS, Van Hecke and Sávio v COV, Gonzalo v HUL)
are attack-side or not a player's largest EP term; C12's defensive-term
rule bites on none of them (Van Hecke's largest term is cs 6.4 over six
rounds, not the GW7 row).

## Starting XI — 3-4-3

| Slot | Player | Pos | GW7 fixture | GW7 EP |
|---:|---|---|---|---:|
| 1 | Trafford | GKP | MUN (H) | 3.599 |
| 2 | Van Hecke | DEF | COV (H) ± | 4.596 |
| 3 | Silva | DEF | SUN (H) | 4.479 |
| 4 | Gabriel | DEF | NFO (A) | 4.062 |
| 5 | Saka (V) | MID | NFO (A) | 4.878 |
| 6 | Sávio | MID | COV (H) ± | 4.620 |
| 7 | Mbeumo | MID | LEE (A) | 4.572 |
| 8 | Groß | MID | CRY (H) | 4.435 |
| 9 | Haaland (C) | FWD | IPS (H) ± | 6.579 |
| 10 | Barry | FWD | CHE (H) | 4.582 |
| 11 | Gonzalo | FWD | HUL (H) ± | 4.511 |
| | XI total | | | 50.913 |
| | + captain | | | 6.579 |
| | **Predicted GW7** | | | **57.492** |

Boundary: `objective` reports no XI/bench pair within 0.25 (C20 does not
bite). E.Le Fée 4.006 sits 0.505 below Gonzalo 4.511, so 3-4-3 beats 3-5-2.

## Captain and vice

Top 5 among the XI by single-GW EP, undiscounted (`captain top 5` line):

| Rank | Player | GW7 EP | p_start_gw[0] |
|---:|---|---:|---:|
| 1 | Haaland | 6.579 | 0.93 |
| 2 | Saka | 4.878 | 0.92 |
| 3 | Sávio | 4.620 | 0.92 |
| 4 | Van Hecke | 4.596 | 0.92 |
| 5 | Barry | 4.582 | 0.90 |

- **Captain Haaland** — gap to #2 is 1.701, far outside the 0.5 tie band.
  The IPS (H) row is banded (±) but his EP6 lead holds on every row of the
  window; C5 is about the 3xc, which is not played this week.
- **Vice Saka** — second on EP, different club and fixture.

## Bench order

| Slot | Player | Pos | GW7 EP | DefCon share |
|---:|---|---|---:|---:|
| 12 | Dubravka | GKP | 0.123 | — |
| 13 | E.Le Fée | MID | 4.006 | 0.067 |
| 14 | Justin | DEF | 3.637 | 0.165 |
| 15 | Khalaili | DEF | 3.074 | 0.161 |

Gaps 0.369 and 0.563 are outside C8's 0.25 band, so EP order stands and no
DefCon tie-break is needed.

## Transfers

| Out | In | Sell | Buy |
|---|---|---:|---:|
| Raya (ARS, GKP, id 1) | Trafford (LEE, GKP, id 385) | 6.0 | 5.0 |
| Tarkowski (EVE, DEF, id 229) | Van Hecke (TOT, DEF, id 112) | 6.1 | 4.9 |
| Thiaw (NEW, DEF, id 445) | Silva (BOU, DEF, id 566) | 5.0 | 5.0 |
| Tavernier (BOU, MID, id 68) | Saka (ARS, MID, id 12) | 6.0 | 9.6 |
| Schade (BRE, MID, id 94) | Sávio (TOT, MID, id 403) | 6.2 | 6.5 |
| Thiago (BRE, FWD, id 106) | Gonzalo (FUL, FWD, id 569) | 7.8 | 6.1 |
| Richards (CRY, DEF, id 202) | Khalaili (CRY, DEF, id 588) | 4.9 | 5.0 |
| Shaw (MUN, DEF, id 423) | Justin (LEE, DEF, id 332) | 4.3 | 4.5 |

Sells 46.3, buys 46.6, bank 0.3 → 0.0. Hit cost 0 under the wildcard. The
banked free transfer is untouched: 1 carried + 1 accrued = 2 at the GW8
deadline.

Execution order: the wildcard rides the make-transfers POST
(`chip: wildcard`); the lineup follows once the eight ins land. Price
exposure overnight: Groß rose 0.1 this event and Gabriel fell 0.1; of the
ins, none moved this event. A rise of 0.1 on any in before the POST breaks
the bank (0.0) and `make-transfers` refuses — the fallback is Justin → a
£4.4m DEF or Khalaili → Richards kept (drop that pair, bank 0.1), either of
which is a new STATE and plan.json before any POST.

## Chips

`chip: wildcard` this GW. Set-1 wildcard window GW2–19 (bootstrap), unused.
Edge over the best no-chip plan: +14.016 blend / +2.765 prior-only (gate
≥ 6.0 / ≥ 0). Note for the finalizer and plan-builder: `chips_used` stays
empty in this STATE block — `plan` refuses a `chip` that is also listed as
used inside the same window; the GW8 cycle records it.

Provisional chip plan: 3xc GW9 (Haaland v BHA (H), λ_att 2.09, not banded —
C5 holds), freehit GW16 (placeholder), bboost GW19 (placeholder; needs GK2
repaired by free transfer first — the bench is otherwise three playing
starters).

## Money

Bank 0.0. team_value 99.1 (Σ selling prices after the wildcard 99.1 + bank
0.0; kept players keep their GW6 selling prices, ins are at purchase price).
Sell basis relayed.

Gate ids: 385,112,566,4,12,403,427,124,411,249,569,497,542,332,588

Bench check: Dubravka (12, 0.03) | none other

## Rejected alternatives

| Alternative | Figure | Why rejected |
|---|---|---|
| Plan A alone, wildcard at GW8 as earmarked | +2.223 / +1.214; GW7 XI 54.855 | the wildcard clears its gate by +14.016 / +2.765 now, on LOW rows; waiting costs 2.6 on GW7 and one free transfer |
| Plan B (Schade → Sávio) | +2.005 / +3.634 | FAIL on the greedy reference (0.218 below A) |
| Best paid single: Thiaw → Silva | +4.017 / −0.634 | prior sign flip; and below the 6.0 hit gate |
| Free hit | not graded | the wildcard is the better chip for a permanent repair of GK2, DEF5 and the midfield |
| Triple captain GW7 | not graded | C5: earmark stays GW9 on Haaland's own EP; the GW7 IPS row is banded |

## Accepted risks

| # | Risk | Detail |
|---|---|---|
| R1 | GK2 dead | Dubravka 0.123 (p 0.03). Trafford is a six-of-six 90-minute starter; a Trafford absence leaves the GK slot empty. First repair candidate for the GW8 free transfers (2 available) |
| R2 | Eight buys on six rounds of evidence | All LOW, p_start ≥ 0.88. Silva (att 5.4 of 25.39), Sávio (four starts) and Gonzalo carry thin points records — 0, 0 and 1 returns ≥ 5 in six rounds — and are prior-negative pairs (see Swap pass); the package is +3.979 on prior-only |
| R3 | Template exposure | Unheld: João Pedro (CHE, 70.9%), Calafiori (52.7%), Groß held (41.3%). João Pedro's best build is −1.03 blend / −2.09 prior |
| R4 | Overnight price break | Bank 0.0; any 0.1 rise on an in before the POST refuses the package (fallback above) |
| R5 | Promoted-club rows | Haaland v IPS, Van Hecke and Sávio v COV, Gonzalo v HUL all banded ±; none is a defensive largest-term pick (C12) |
| R6 | TOT at the club cap | Van Hecke, Sávio, Dubravka: a future TOT buy needs Dubravka out first |

## Suggestions

Read data/suggestions.md through S8

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 6 | followed | both halves now complete: Ndiaye → Groß and Anderson → Schade inside the +14.449 blend / +5.210 prior-only triple; Ndiaye's marginal +2.503 / +0.665 and Anderson's +2.488 / +0.757 each clear the 2.0 gate on their own, so the steer broke no tie and the optimizer reached it unaided; EP6 delta of the row itself 0.00. The GW5 ledger's "Ndiaye half completed" was false in fact (never POSTed) and is superseded here |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |
| S3 | 6 | followed | Ndiaye → Groß made; marginal +2.503 blend / +0.665 prior against the plan without this sale (Scott + Anderson → E.Le Fée + Schade, +11.946 / +4.545), so the below-threshold clause was not needed |
| S4 | 6 | followed | Anderson → Schade made; marginal +2.488 blend / +0.757 prior against the plan without this sale (Scott + Ndiaye → E.Le Fée + Groß, +11.961 / +4.453); clears the gate on both readings, below-threshold clause not needed |
| S5 | 6 | followed | Scott → E.Le Fée made; EP6 0.00 for GW6–11 (status i, 0%); marginal +2.503 / +0.675 against the plan without this sale (Ndiaye + Anderson → E.Le Fée + Schade, +11.946 / +4.535) |
| S6 | 7 | followed | wildcard played at GW7 on the fresh EP: +16.239 blend / +3.979 prior over GW7–12, +14.016 / +2.765 over the best no-chip plan, every buy LOW at p_start ≥ 0.88, the GW6 reason for GW8 (HIGH rows) gone; GW7 XI 57.49 after GW6's 56.18; 60 per GW stays unreachable, the best legal build tops out at 57.49 on GW7 (objective prints no GW8 XI total — backlog row) |
| S7 | 7 | standing | honoured: of the named fallers Richards, Thiago and Shaw are sold in the wildcard (Ndiaye and Anderson went at GW6); Mbeumo held — the best same-price alternative Gibbs-White is −2.82 EP6, not small; within the band the policy settled Richards → Khalaili (+0.247 blend) alongside S8; policy stays live for the GW8 free transfers |
| S8 | 7 | standing | honoured within the band: Gabriel (ARS, 3 returns in 6) kept over the V3 build's Hill/Calafiori/Mukiele (−0.40 blend, inside 0.5); Khalaili (7, 6 pts in R4–R5) over Richards (+0.247); outside the band EP wins: Tarkowski held costs −1.07 / −2.25, João Pedro −1.03 / −2.09, Calvert-Lewin for Gonzalo −0.96; Silva, Sávio and Gonzalo bought on EP despite thin records (0, 0, 1 returns) because no steadier player sits within 0.5 EP6 at their price |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW8 deadline: 1 at GW7, wildcard played (none used), 1 accrues.
# team_value on the selling-price basis: kept players at GW6 sell prices + ins at purchase price = 99.1, bank 0.0.
# chips_used stays empty: `plan` refuses a chip listed as used inside its own window; the GW8 cycle records the wildcard.
gw: 7
team_id: 8455344
team_value: 99.1
bank: 0.0
free_transfers_banked: 2
chip: wildcard
chips_used: []
transfers_made:
  - {out: Raya, in: Trafford, cost: 0}
  - {out: Tarkowski, in: Van Hecke, cost: 0}
  - {out: Thiaw, in: Silva, cost: 0}
  - {out: Tavernier, in: Saka, cost: 0}
  - {out: Schade, in: Sávio, cost: 0}
  - {out: Thiago, in: Gonzalo, cost: 0}
  - {out: Richards, in: Khalaili, cost: 0}
  - {out: Shaw, in: Justin, cost: 0}
chip_plan:
  - {chip: 3xc, gw: 9, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 385, name: Trafford, position: 1, captain: false, vice: false}
  - {id: 112, name: Van Hecke, position: 2, captain: false, vice: false}
  - {id: 566, name: Silva, position: 3, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 4, captain: false, vice: false}
  - {id: 12, name: Saka, position: 5, captain: false, vice: true}
  - {id: 403, name: Sávio, position: 6, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 7, captain: false, vice: false}
  - {id: 124, name: Groß, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: true, vice: false}
  - {id: 249, name: Barry, position: 10, captain: false, vice: false}
  - {id: 569, name: Gonzalo, position: 11, captain: false, vice: false}
  - {id: 497, name: Dubravka, position: 12, captain: false, vice: false}
  - {id: 542, name: E.Le Fée, position: 13, captain: false, vice: false}
  - {id: 332, name: Justin, position: 14, captain: false, vice: false}
  - {id: 588, name: Khalaili, position: 15, captain: false, vice: false}
```
