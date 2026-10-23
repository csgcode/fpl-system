# GW8 Squad Proposal (2026/27) — RE-DECISION: WILDCARD, red-team F1 package

Third run of the cycle. v1 (archived as squad-proposal.v1.md) proposed the
wildcard with plan C; the red-team returned REVISE (F1); the revision run
(archived as squad-proposal.v2.md) held the wildcard under the user's
in-chat steers of the day (keep Raya, drop Saka, hold the chip). The user
then withdrew those steers and delegated the choice. Suggestion cut-off
stays S8 (first run of the cycle). Deadline 2026-10-23T17:30:00Z. Horizon
GW8–13. Squad from the STATE block of data/decisions/gw7/final.md; budget =
its `team_value` 99.1.

**User instruction, verbatim:** "Ignore all my suggestions made today, Out
of all the suggestions that you made, select which is best for the future,
both in terms of short term and long term. You have my belief. I need you
to justify your actions and then make a decision."

**Orchestrator decision under that delegation:** play the set-1 wildcard in
GW8 with the red-team's F1 package — Raya → Trafford, Dubravka → Kinsky,
Tarkowski → Calafiori, Shaw → Justin, Groß → Saka, Schade → Gomez, Thiago →
Wissa — because it is the only graded package strong on both readings (no
prior sign flip), clears the 6.0 chip gate by a margin that survives Saka
missing GW8–10, fixes the two dead bench slots (Shaw status i, Dubravka p
0.03), and keeps 2 FTs for GW9. This run verifies that package against the
hard constraints and the chip gate, and sets the lineup.

**Wildcard. Seven transfers, hit 0. 5-3-2, Haaland (C), Gabriel (V).
Predicted GW8 54.411. Bank £0.0m. FT at GW9: 2.**

Sell basis: the GW7-verified selling prices from data/decisions/gw7/final.md
passed as `--sell` (the basis the review and both research files used), so
the CLI labels it `relayed`. No fresh `my-team` read this cycle (session
expired at step 1); every kept player's now_cost is ≥ his GW7 sell price, so
99.1 is a floor and the true bank is ≥ 0.0. The finalizer confirms against
`my-team` once credentials are re-captured.

## Verification — objective (verbatim)

`objective --gw 8 --sell 1:6.0,112:4.9,4:7.9,229:6.1,427:7.9,124:5.9,68:6.0,542:5.7,411:15.5,249:5.6,106:7.8,497:4.0,202:4.9,94:6.2,423:4.3 --bank 0.4 --free-transfers 1 --chip wildcard --moves 1:385,497:496,229:8,423:332,124:12,94:127,106:464`:

```
objective gw8 — horizon GW8–GW13; squad from data/decisions/gw7/final.md
sell basis: relayed (Σ sell 98.7 + bank 0.4 = 99.1)
baseline: blend 328.050 prior 318.513
legal single moves: 1586 (pool 417); top 10 by blend:
  1 | Richards → Silva | +2.301 | -1.562 | bank 0.3 | fails (prior sign flip)
  2 | Schade → Stach | +1.764 | +0.894 | bank 0.6 | fails (blend < 2.0)
  3 | Tarkowski → Silva | +1.741 | -2.077 | bank 1.5 | fails (prior sign flip)
  4 | Tarkowski → Calafiori | +1.711 | +0.272 | bank 0.5 | fails (blend < 2.0)
  5 | Van Hecke → Silva | +1.551 | -1.835 | bank 0.3 | fails (prior sign flip)
  6 | Shaw → Justin | +1.439 | +2.019 | bank 0.2 | fails (blend < 2.0)
  7 | Groß → Stach | +1.382 | +0.535 | bank 0.3 | fails (blend < 2.0)
  8 | Schade → Barnes | +1.263 | +2.765 | bank 0.5 | fails (blend < 2.0)
  9 | Thiago → João Pedro | +1.139 | -0.516 | bank 0.3 | fails (prior sign flip)
  10 | Shaw → Konsa | +1.096 | +0.884 | bank 0.1 | fails (blend < 2.0)
plan: Raya → Trafford, Dubravka → Kinsky, Tarkowski → Calafiori, Shaw → Justin, Groß → Saka, Schade → Gomez, Thiago → Wissa — blend +9.537 prior +8.627; bank 0.0; transfers 7 under wildcard (FT unchanged (1)); chip gate: ≥ 6.0 over the greedy plan
  move Raya → Trafford: +0.042 / +0.045 — chip package
  move Dubravka → Kinsky: +0.119 / +0.189 — chip package
  move Tarkowski → Calafiori: +1.771 / +0.404 — chip package
  move Shaw → Justin: +1.439 / +1.972 — chip package
  move Groß → Saka: +5.878 / +4.626 — chip package
  move Schade → Gomez: +0.141 / +0.029 — chip package
  move Thiago → Wissa: +0.382 / +1.245 — chip package
after plan, best single: none legal
reference (greedy): bank — no move passes its gate
verdict: PASS
GW8 XI 4-3-3 54.506: Trafford, Gabriel, Calafiori, Richards, Justin, Mbeumo, E.Le Fée, Tavernier, Haaland, Wissa, Barry; captain top 5: Haaland 5.798 0.94, Gabriel 5.080 0.95, Mbeumo 4.932 0.96, Calafiori 4.596 0.94, Wissa 4.494 0.94
boundary pairs within 0.25: Justin 3.773 (DefCon 0.161) | Van Hecke 3.565 (0.190) ; Justin 3.773 (DefCon 0.161) | Gomez 3.541 (0.139) ; Barry 3.660 (DefCon 0.008) | Van Hecke 3.565 (0.190) ; Barry 3.660 (DefCon 0.008) | Gomez 3.541 (0.139)
bench: Kinsky 2.916, Van Hecke 3.565, Gomez 3.541, Saka 2.951
```

| Check | Result |
|---|---|
| Legality | `objective` accepts the package (an illegal one refuses): 2 GKP / 5 DEF / 5 MID / 3 FWD |
| Budget | sells 40.3 + bank 0.4 = 40.7; buys Trafford 5.0 + Kinsky 4.5 + Calafiori 6.0 + Justin 4.5 + Saka 9.6 + Gomez 5.0 + Wissa 6.1 = 40.7; bank 0.0 on the GW7-verified floor, so never negative |
| 3 per club | ARS 3 (Gabriel, Calafiori, Saka), LEE 2 (Trafford, Justin), TOT 2 (Kinsky, Van Hecke), BOU, BHA, MUN, CRY, SUN, MCI, EVE, NEW 1 each |
| Chip gate | greedy reference is bank (+0.000 / +0.000: no single move passes the free gate); the wildcard is +9.537 blend (≥ 6.0) and +8.627 prior-only (≥ 0). PASS, margin 3.537 on blend |
| Prior sign flips | none of the seven components; the smallest prior-only marginal is Schade → Gomez +0.029 |
| Flags | Saka d 50% (thigh, news 21 Oct) — his GW8 row is benched; the other 14 are `a`. The 13:13 UTC `flags` refresh changed none of the 15 ids in this package (flags-delta-20261023T131322_242608Z.json, gate_changed false, pool delta touches none of them) |
| Window | wildcard set 1, GW2–19 in bootstrap `chips`, unused (chips_used empty in GW7 STATE) |

The package passes every hard constraint and the gate, so no substitute is
proposed.

## Why this package — the justification the user asked for

The question is which of the graded options is best for the future, short
and long term. Every figure is on the same sell basis.

| Option | Transfers | blend / prior-only (GW8–13) | GW8 XI (objective) | Chip gate | Sign-flip components |
|---|---|---:|---:|---|---|
| **F1 (this plan)** | 7, wildcard | **+9.537 / +8.627** | 54.506 | PASS (+3.54) | none |
| C (v1) | 7, wildcard | +9.800 / +6.557 | 54.010 | PASS (+3.80) | Tarkowski → Silva −1.959 |
| C with Calvert-Lewin for Wissa | 7, wildcard | +9.527 / +5.102 | — | PASS | Silva; Calvert-Lewin −0.210 (review) |
| F1 with Calvert-Lewin for Wissa | 7, wildcard | +9.345 / +7.172 | 54.393 | PASS | Thiago → Calvert-Lewin −0.210 |
| F1 with Hill for Calafiori | 7, wildcard | +8.469 / +8.811 | 53.887 | PASS | Schade → Gomez −0.179 |
| R1 (Raya kept, no Saka, Rogers) | 6, wildcard | +7.523 / +3.213 | 55.73 (research-mid.md) | PASS (+1.52) | Richards → Silva −1.279; Groß → Rogers −0.112 |
| X1 (Raya kept, no Saka, Isak) | 6, wildcard | +9.338 / +3.626 | 55.79 (research-mid.md) | PASS (+3.34) | Richards → Silva −1.269 |
| Hold (v2) | 0 | +0.000 / +0.000 | 53.638 | — | — |

- **Short term (GW8).** The objective's GW8 XI is 54.506 for F1 against
  53.638 for the hold and 54.010 for plan C. After the C20 tie-break (below)
  the fielded XI is 54.411: +0.8 on holding, +0.5 on C. Of the chip's gain,
  research-transfers.md §2 puts +0.87 in GW8 and the rest across GW9–13,
  with GW10 (ARS v HUL (H), Saka and Calafiori) the peak at 59.92.
- **Long term (GW8–13 and beyond).** F1 is the strongest package on the
  prior-only reading by a wide margin (+8.627 against C +6.557, X1 +3.626,
  R1 +3.213). Prior-only is the model's view with this season's seven games
  discounted, so it is the reading that says least about a hot streak and
  most about what the squad does over the long run. F1 is also the only
  package with no component whose sign flips between the readings (C14's
  rule for hits, applied here to the whole package). The blend gap to C is
  0.263, inside the 0.5 band the v1 proposal itself used to settle A v C on
  the prior-only margin; applying the same decider picks F1 over C.
- **Durability.** research-transfers.md §3 rescores Saka's ramp: F1 holds
  +9.01 / +8.14 if he misses GW8–9, +8.23 / +7.72 back at GW10, and
  +6.22 / +6.12 if he misses GW8–10 — still over the 6.0 gate in every case
  bar a season-long absence (+2.81 / +3.37). No other graded package keeps
  its gate margin under that stress.
- **Against holding.** The hold's value is the chip kept for later plus two
  free transfers at GW9, which research-mid.md §3c prices at roughly +3
  blend over GW9–13; the chip's gain is +9.5 now, so playing it is worth
  about +6.5 over the hold on the horizon. Nothing in GW8–13 argues for
  waiting: no blank or double gameweek (fixture analyst), and the set-1
  wildcard expires at GW19 whether or not a better week appears. The squad
  also carries two dead bench slots (Shaw i, Dubravka p 0.03) that the hold
  leaves in place, with no single move passing the free gate to repair them
  (best Shaw → Justin +1.439 < 2.0).
- **Structure.** Bench of four playing rows (Kinsky 6/6 × 90, Van Hecke,
  Gomez 7/7, Saka), which makes the GW19 bench-boost earmark live, and two
  free transfers banked for GW9 to absorb the GW11 fixture turn (SUN and NEW
  harden: E.Le Fée and Wissa).

Rejected, with the reason:

- **Plan C** (+9.800 / +6.557): 0.263 better on blend, 2.070 worse on
  prior-only, and the gap rests on Tarkowski → Silva (+1.598 / −1.959):
  Silva has 630 PL minutes and a league-average prior, so his gain is seven
  games of form. The v1 claim that Calafiori "does not fit the £99.1 floor"
  was wrong — Kinsky for Suzuki funds him (review F1).
- **Hill variants** (+8.469 / +8.811 with Kinsky): no sign flip and £0.5m
  kept, but −1.068 blend and a lower GW8 XI (53.887); the prior-only edge
  of +0.184 does not cover it.
- **Calvert-Lewin for Wissa** (+9.345 / +7.172): inside the 0.5 blend band
  (−0.192) but −1.455 prior-only, the component itself flips sign
  (−0.210), and Calvert-Lewin went `d` 50% (foot) at 13:00 UTC today —
  after players-FWD.json was built with his p_start_gw at 0.94, so his
  25.42 EP6 is overstated. Wissa stands. Resolves review F4.
- **R1 / X1** (Raya kept, no Saka): +7.523 / +3.213 and +9.338 / +3.626.
  Both clear the gate on blend but each needs Richards → Silva (prior sign
  flip) to do it, keep Dubravka as a dead keeper, and sit 5.0–5.4 behind F1
  on prior-only. The best no-flip Rogers package (R5) fails the gate.
- **Hold** (+0.000): see above; it was the user's choice earlier today and
  is withdrawn by the instruction quoted at the top.

## Step 1 — budget skeleton

Premiums (> £9m): Haaland 15.5 (sell basis) and Saka 9.6 — unchanged from
v1, whose justification holds: Haaland is 3.65 EP6 clear of the pool's #2
and is the 3xc earmark; Saka's split (plan H: Saka + Gomez + Justin → Stach
+ Barnes + Calafiori, +7.261 / +5.433) loses 2.5 blend / 1.1 prior-only
against C and is further behind F1. The two-premium skeleton leaves £74.0m
for 13 slots; the budget is exhausted (bank 0.0).

## Step 2 — XI fill by raw EP

- GKP: Trafford 5.0 (21.70, pool #1). Raya 21.66 at 6.0 sells for −0.04
  EP6 and £1.0m; inside this package the move is +0.042 / +0.045.
- DEF: Gabriel 28.58 (held), Calafiori 25.67 (6.0, the #3 DEF in the pool
  and the best with a full PL prior: 24.14 prior-only), Van Hecke 24.30
  (held), Richards 22.70 (held), Justin 22.37 (4.5). Silva 25.85 is the
  blend #2 but 21.87 prior-only — rejected above.
- MID: Mbeumo 30.43 (held), Saka 28.64, Tavernier 26.95 (held), E.Le Fée
  26.20 (held), Gomez 22.86 (5.0, BHA 7/7).
- FWD: Haaland 34.96 (held), Barry 25.51 (held), Wissa 25.32 (6.1; 28.14
  prior-only).

Clubs after: ARS 3, LEE 2, TOT 2, rest 1. The three Arsenal rows share one
clean sheet (Gabriel, Calafiori) and one attack (Saka); legal, and the ARS
defence is the pool's best rated (ΣP(CS) 2.20).

## Step 3 — bench

GK: **single playing keeper** Trafford, with Kinsky (TOT, 4.5, 6/6 × 90) as
a playing backup rather than a rotation partner — Kinsky's GW8–13 rows are
below Trafford's in five of six weeks (research-transfers.md §4), so the
rotation value is +0.12 and he is bought for auto-sub cover and the GW19
bench-boost earmark, at £0.5m less than Suzuki. Dubravka (p 0.03) leaves.

Outfield bench: Van Hecke 4.9 (p 0.95), Gomez 5.0 (p 0.93), Saka 9.6 (p
0.50 this GW). No £4.0–4.5m outfield filler: Justin 4.5 (p 0.95) is the
cheapest DEF and starts.

## Step 4 — swap pass (audit trail)

The single-move table above (1586 legal, top 10) shows no move passing the
free gate without the chip; the no-chip plan is bank. Rows for the moves the
open suggestions name, as singles on the same basis (from the v2 run, same
figures):

| Row | For | blend / prior | Verdict |
|---|---|---|---|
| Richards → Silva (202:566) | S7 (Richards a named faller) | +2.301 / −1.562 | FAIL, prior sign flip |
| Shaw → Justin (423:332) | S7 (Shaw a named faller, status i) | +1.439 / +2.019 | FAIL as a single (blend < 2.0); made inside the wildcard, +1.439 / +1.972 |
| Thiago → João Pedro (106:383) | S7 (Thiago a named faller) | +1.139 / −0.516 | FAIL, prior sign flip; Thiago sold inside the wildcard for Wissa |
| Mbeumo → Gibbs-White (427:480) | S7 (Mbeumo a named faller) | −5.326 / −3.776 | FAIL |
| E.Le Fée → Stach (542:335) | S8 (Le Fée a named GW6 buy) | −0.968 / −0.700 | FAIL |
| Groß → Stach (124:335) | S8 (Groß a named GW6 buy) | +1.382 / +0.535 | FAIL as a single; Groß sold inside the wildcard for Saka |
| Schade → Stach (94:335) | S8 (Schade a named GW6 buy) | +1.764 / +0.894 | FAIL as a single; Schade sold inside the wildcard for Gomez |

Wildcard packages graded this run, all `--chip wildcard` on the relayed
basis: the table in the justification section. After the plan `objective`
reports `best single: none legal`; the wildcard uses no free transfer (FT 1
unchanged, 2 at GW9).

## Squad

Price = purchase price for buys, GW7-verified selling price for kept players
(now_cost in brackets where different). EP6 = `ep_total6`, GW8 = `ep_gw[0]`.

| Slot | Pos | Player | Id | Club | Price | GW8 EP | EP6 | p_start GW8 | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|
| 1 | GKP | Trafford | 385 | LEE | 5.0 | 3.574 | 21.70 | 0.95 | XI · IN |
| 2 | DEF | Gabriel | 4 | ARS | 7.9 | 5.080 | 28.58 | 0.95 | XI · Vice |
| 3 | DEF | Calafiori | 8 | ARS | 6.0 | 4.596 | 25.67 | 0.94 | XI · IN |
| 4 | DEF | Richards | 202 | CRY | 4.9 | 4.044 | 22.70 | 0.95 | XI |
| 5 | DEF | Justin | 332 | LEE | 4.5 | 3.773 | 22.37 | 0.95 | XI · IN |
| 6 | DEF | Van Hecke | 112 | TOT | 4.9 | 3.565 | 24.30 | 0.95 | XI |
| 7 | MID | Mbeumo | 427 | MUN | 7.9 | 4.932 | 30.43 | 0.96 | XI |
| 8 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.406 | 26.20 | 0.94 | XI |
| 9 | MID | Tavernier | 68 | BOU | 6.0 (6.2) | 4.351 | 26.95 | 0.93 | XI |
| 10 | FWD | Haaland | 411 | MCI | 15.5 (15.7) | 5.798 | 34.96 | 0.94 | XI · Captain |
| 11 | FWD | Wissa | 464 | NEW | 6.1 | 4.494 | 25.32 | 0.94 | XI · IN |
| 12 | GKP | Kinsky | 496 | TOT | 4.5 | 2.916 | 19.06 | 0.95 | Bench GK · IN |
| 13 | MID | Gomez | 127 | BHA | 5.0 | 3.541 | 22.86 | 0.93 | Bench 1 · IN |
| 14 | FWD | Barry | 249 | EVE | 5.6 (5.7) | 3.660 | 25.51 | 0.94 | Bench 2 |
| 15 | MID | Saka | 12 | ARS | 9.6 | 2.951 | 28.64 | 0.50 | Bench 3 · IN |
| | | **Total** | | | **99.1** | | | | |

2 GKP / 5 DEF / 5 MID / 3 FWD. Max club count 3 (ARS).

## Starting XI — 5-3-2

The objective's best GW8 XI is the 4-3-3 above (54.506 with captain), Barry
in and Van Hecke on the bench. C20 applies C8's tie-break at the XI/bench
boundary: Barry 3.660 (DefCon share 0.008) and Van Hecke 3.565 (0.190) are
0.095 apart, inside the 0.25 band, so Van Hecke starts and Barry sits
(−0.095 EP). The other boundary pairs the objective prints already favour
the XI player on floor share after that swap: Justin 3.773 (0.161) v Gomez
3.541 (0.139); Justin v Van Hecke are both in the XI.

| Slot | Player | Pos | GW8 fixture | GW8 EP |
|---:|---|---|---|---:|
| 1 | Trafford | GKP | SUN (A) | 3.574 |
| 2 | Gabriel (V) | DEF | EVE (H) | 5.080 |
| 3 | Calafiori | DEF | EVE (H) | 4.596 |
| 4 | Richards | DEF | NEW (H) | 4.044 |
| 5 | Justin | DEF | SUN (A) | 3.773 |
| 6 | Van Hecke | DEF | CHE (A) | 3.565 |
| 7 | Mbeumo | MID | BOU (H) | 4.932 |
| 8 | E.Le Fée | MID | LEE (H) | 4.406 |
| 9 | Tavernier | MID | MUN (A) | 4.351 |
| 10 | Haaland (C) | FWD | AVL (A) | 5.798 |
| 11 | Wissa | FWD | CRY (A) | 4.494 |
| | XI total | | | 48.613 |
| | + captain | | | 5.798 |
| | **Predicted GW8** | | | **54.411** |

C12: no XI row is a promoted-club fixture this GW.

## Captain and vice

Top 5 in the XI by single-GW EP, undiscounted (`objective` captain line):

| Rank | Player | GW8 EP | p_start_gw[0] |
|---:|---|---:|---:|
| 1 | **Haaland** (C) | 5.798 | 0.94 |
| 2 | Gabriel (V) | 5.080 | 0.95 |
| 3 | Mbeumo | 4.932 | 0.96 |
| 4 | Calafiori | 4.596 | 0.94 |
| 5 | Wissa | 4.494 | 0.94 |

Captain Haaland, 0.718 clear of Gabriel — outside the 0.5 band, EP decides.
Vice Gabriel: 0.148 over Mbeumo, inside the band; both p_start_gw[0] ≥
0.85, so the tiebreak does not separate them and the higher EP holds (S8's
read is mixed, as the v2 run recorded: Mbeumo 41 pts v Gabriel 35, four
returns each, Gabriel at the more consistent club).

## Bench order

| Slot | Player | Pos | GW8 EP | p_start | DefCon share |
|---:|---|---|---:|---:|---:|
| 12 | Kinsky | GKP | 2.916 | 0.95 | — |
| 13 | Gomez | MID | 3.541 | 0.93 | 0.139 |
| 14 | Barry | FWD | 3.660 | 0.94 | 0.008 |
| 15 | Saka | MID | 2.951 | 0.50 | — |

Gomez ahead of Barry: 0.119 apart, inside C8's band, higher DefCon floor
share first. Saka last: 0.59 below Gomez and a 50% flag. Kinsky is the only
other keeper.

Bench check: none

## Transfers (wildcard, cost 0)

| Out | Id | Sell (GW7 verified) | In | Id | Buy |
|---|---:|---:|---|---:|---:|
| Raya (ARS, GKP) | 1 | 6.0 | Trafford (LEE, GKP) | 385 | 5.0 |
| Dubravka (TOT, GKP) | 497 | 4.0 | Kinsky (TOT, GKP) | 496 | 4.5 |
| Tarkowski (EVE, DEF) | 229 | 6.1 | Calafiori (ARS, DEF) | 8 | 6.0 |
| Shaw (MUN, DEF, status i) | 423 | 4.3 | Justin (LEE, DEF) | 332 | 4.5 |
| Groß (BHA, MID) | 124 | 5.9 | Saka (ARS, MID) | 12 | 9.6 |
| Schade (BRE, MID) | 94 | 6.2 | Gomez (BHA, MID) | 127 | 5.0 |
| Thiago (BRE, FWD) | 106 | 7.8 | Wissa (NEW, FWD) | 464 | 6.1 |
| | | 40.3 | | | 40.7 |

Bank after: 0.4 + 40.3 − 40.7 = **0.0** on the GW7-verified basis. The
deadline is today and the overnight price run has passed, so no price moves
before the POST; the plan-builder's `purchase_price_at_plan` audit covers
drift. Execution (review F9): the session was expired at step 1 — the chip
rides the make-transfers POST, so if credentials are not re-captured the
user applies by hand and must **activate the wildcard before confirming the
seven transfers**, or the site books six of them as hits.

Gate ids: 385,496,4,8,202,332,112,427,542,68,127,12,411,249,464

## Chips

`chip: wildcard` — set-1 wildcard, window GW2–19 (bootstrap `chips`),
unused, clears the gate (+9.537 ≥ 6.0 blend, +8.627 ≥ 0 prior-only over the
greedy plan, which is bank). No blank or double in GW8–13; S6's window ends
this GW.

Provisional chip plan (windows from bootstrap `chips`: freehit GW2–19,
bboost and 3xc GW1–19):

- 3xc GW9 — Haaland v BHA (H), his own GW9 row 6.276 (C5: on his own EP;
  MCI λ_att supports but does not carry it). His GW11 row FUL (H) 6.371 is
  0.095 higher, inside noise; the GW9 cycle decides on fresh EP.
- freehit GW16 — placeholder, no blank or double in GW8–13.
- bboost GW19 — placeholder; live now that the bench is four playing rows
  (Kinsky, Van Hecke, Gomez, Saka).

## Rationale and rejected alternatives

- The user delegated the choice; the orchestrator chose the F1 package;
  this run verified it (legal, bank 0.0, ARS 3, gate PASS by 3.537) and
  found no hard-constraint or gate failure, so no substitute was needed.
- Where the gain comes from: Groß → Saka +5.878 / +4.626 is the largest
  component; Tarkowski → Calafiori +1.771 / +0.404 and Shaw → Justin
  +1.439 / +1.972 add the rest of substance; Thiago → Wissa, Schade → Gomez,
  Dubravka → Kinsky and Raya → Trafford are small positives on both
  readings that fund the structure.
- Review findings carried as accepted risk (final.md should name them):
  F2 Saka d 50% on £9.6m with a guessed ramp (freshness gate re-checks him;
  `i` → REOPEN); F3 template exposure — held > 30%-owned: Haaland,
  Calafiori; sold Raya (44.9%) and Groß (45.8%); still off João Pedro,
  Rogers, De Cuyper, Cherki, B.Fernandes; F7 price risk ≈ −0.2m (Saka,
  Wissa net outflows); F10 SUN and NEW turn hard from GW11, two free
  transfers at GW9 cover it.
- Review F4 resolved: Wissa over Calvert-Lewin on the prior-only margin
  (+1.455 as packages, Calvert-Lewin's component −0.210) and the fresh 50%
  flag; written into the S8 reason.
- Review F5 resolved: S7 is read as a sell-side policy; the −0.2m from
  buying two net fallers is accepted explicitly in the S7 reason.
- Risks: Saka's return; three Arsenal rows (one bad ARS week hits Gabriel,
  Calafiori and Saka); Justin v Van Hecke v Barry sit 0.2 apart at the
  boundary, so one news item can reorder the back line; bank 0.0 leaves no
  room for a price-driven refusal if `my-team` shows a selling price below
  the GW7 figure (none is expected: every now_cost is ≥ the GW7 sell price).

## Suggestions

Read data/suggestions.md through S8

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 6 | followed | both halves now complete: Ndiaye → Groß and Anderson → Schade inside the +14.449 blend / +5.210 prior-only triple; Ndiaye's marginal +2.503 / +0.665 and Anderson's +2.488 / +0.757 each clear the 2.0 gate on their own, so the steer broke no tie and the optimizer reached it unaided; EP6 delta of the row itself 0.00. The GW5 ledger's "Ndiaye half completed" was false in fact (never POSTed) and is superseded here |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |
| S3 | 6 | followed | Ndiaye → Groß made; marginal +2.503 blend / +0.665 prior against the plan without this sale (Scott + Anderson → E.Le Fée + Schade, +11.946 / +4.545), so the below-threshold clause was not needed |
| S4 | 6 | followed | Anderson → Schade made; marginal +2.488 blend / +0.757 prior against the plan without this sale (Scott + Ndiaye → E.Le Fée + Groß, +11.961 / +4.453); clears the gate on both readings, below-threshold clause not needed |
| S5 | 6 | followed | Scott → E.Le Fée made; EP6 0.00 for GW6–11 (status i, 0%); marginal +2.503 / +0.675 against the plan without this sale (Ndiaye + Anderson → E.Le Fée + Schade, +11.946 / +4.535) |
| S6 | 8 | followed | wildcard played at GW8, the timing the row left open (GW6 or GW8): the package +9.537 blend / +8.627 prior-only clears the chip gate against bank (+0.000); EP per GW over GW8–13 rises from 54.68 to 56.26 (337.587 / 6, captain included); the user's earlier hold today was withdrawn by the delegation quoted in this proposal; not taken: 60 per GW stays unreachable — the best package found (v1 plan A) is 56.45 |
| S7 | 7 | standing | honoured as a sell-side policy (review F5): the wildcard sells Thiago (net faller, sold at 7.8 before a drop), Schade (the squad's largest faller) and Shaw (status i); of the named fallers still held, Richards → Silva +2.301 / −1.562 (prior sign flip; Silva also rejected as a package component) and Mbeumo → Gibbs-White −5.326 / −3.776 FAIL, so no in-band tie to settle; the buys Saka (357k out this event) and Wissa (254k out) are net fallers, an expected −0.1 each after the deadline, −0.2m team value accepted against +9.537 EP6; EP6 delta of the row 0.00; policy stays live for GW9 with 2 FTs |
| S8 | 7 | standing | honoured: six of the seven buys are unbroken-streak starters at p_start 0.93–0.95 (Trafford 6/6 × 90, Kinsky 6/6 × 90, Calafiori, Justin, Gomez 7/7, Wissa); the one flagged buy, Saka (d 50%), is the pool's #3 MID EP6 and his split (plan H) loses 2.539 blend / 1.124 prior-only against C and more against F1, outside the 0.5 band, so the steer cannot override it; Wissa v Calvert-Lewin (review F4) is inside the band (−0.192 blend as packages) and the row's points test favours Calvert-Lewin (33 v 18 pts) but the decider is the prior-only margin (+1.455 as packages; the Calvert-Lewin component −0.210 flips sign) and Calvert-Lewin went d 50% (foot) at 13:00 UTC today, so the row's nailed-starter test now points to Wissa as well; the GW6 buys Groß and Schade are sold, E.Le Fée held (E.Le Fée → Stach −0.968 / −0.700 FAIL); vice tie Gabriel 5.080 v Mbeumo 4.932 inside 0.5 single-GW EP is mixed on the row's read (Mbeumo 41 pts v Gabriel 35, four returns each; Gabriel at the more consistent club), so the higher EP holds; EP6 delta of the row 0.00 |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW9 deadline: 1 unchanged under the wildcard, 1 accrues.
# team_value and bank on the GW7-verified selling-price basis (my-team not read this cycle, session expired): kept players at GW7 sell prices 58.4 + buys at purchase 40.7 = 99.1, bank 0.0.
gw: 8
team_id: 8455344
team_value: 99.1
bank: 0.0
free_transfers_banked: 2
chip: wildcard
chips_used: []
transfers_made:
  - {out: Raya, in: Trafford, cost: 0}
  - {out: Dubravka, in: Kinsky, cost: 0}
  - {out: Tarkowski, in: Calafiori, cost: 0}
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
  - {id: 8, name: Calafiori, position: 3, captain: false, vice: false}
  - {id: 202, name: Richards, position: 4, captain: false, vice: false}
  - {id: 332, name: Justin, position: 5, captain: false, vice: false}
  - {id: 112, name: Van Hecke, position: 6, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 7, captain: false, vice: false}
  - {id: 542, name: E.Le Fée, position: 8, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 9, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 10, captain: true, vice: false}
  - {id: 464, name: Wissa, position: 11, captain: false, vice: false}
  - {id: 496, name: Kinsky, position: 12, captain: false, vice: false}
  - {id: 127, name: Gomez, position: 13, captain: false, vice: false}
  - {id: 249, name: Barry, position: 14, captain: false, vice: false}
  - {id: 12, name: Saka, position: 15, captain: false, vice: false}
```
