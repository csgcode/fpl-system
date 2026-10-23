# GW8 Red-Team Review — W2 wildcard package (pre-apply, advisory)

Scope: the package in data/decisions/gw8/final.md and squad-proposal.md
(set-1 wildcard, eight transfers, 4-4-2, Haaland C, Gabriel V), reviewed
against data/analysis/gw8/* (MID re-run after Saka went `i`), the prior-only
EP files rebuilt with `ep --prior-weight 1.0`, data/raw/gw8/bootstrap.json
(13:53 UTC refresh), the retro corrections through gw7.md (C21) and the
S1–S8 ledger. data/decisions/gw8/review.md graded v1 (Saka); W2 was not
red-teamed before this. This is advisory, not a REVISE loop: nothing here
changes final.md, plan.json or the proposal.

**Verdict: GO.** No change beats W2 by ≥ 0.5 blend without losing
prior-only. The package rests on one player (F1); that is a reason to hold,
not to swap, and holding loses on a fair comparison (§ Hold v W2). One
record correction is due after the apply (F2).

## Reproduction on the real selling-price basis

`my-team` now reads. The dry-run's sell prices for the eight outgoing
players: Raya 6.0, Dubravka 4.0, Richards 4.9, Tarkowski 6.1, Shaw 4.3,
Schade 6.2, Groß 6.0, Thiago 7.8 (Σ 45.3; GW7 basis 45.2). The dry-run's
sell sum is 99.0, so the seven kept players sell for 53.7 against the GW7
basis 53.5. The +0.2 is Tavernier 6.1 and Haaland 15.6 (bought 6.0 and
15.5, now 6.2 and 15.7; every other kept player's now_cost is within 0.1 of
his purchase price, so his sell price is unchanged). Budget 99.4 = Σ sell
99.0 + bank 0.4.

```
objective --gw 8 --sell 1:6.0,497:4.0,202:4.9,229:6.1,423:4.3,94:6.2,124:6.0,106:7.8,4:7.9,112:4.9,427:7.9,68:6.1,542:5.7,411:15.6,249:5.6 --bank 0.4 --free-transfers 1 --chip wildcard --moves 1:385,497:496,229:8,423:332,94:127,106:379,124:453,202:60
sell basis: relayed (Σ sell 99.0 + bank 0.4 = 99.4)
baseline: blend 328.050 prior 318.513
plan: … — blend +8.304 prior +8.078; bank 0.1; transfers 8 under wildcard (FT unchanged (1))
  move Raya → Trafford: +0.042 / +0.045        move Shaw → Justin: +1.138 / +1.482
  move Dubravka → Kinsky: +0.119 / +0.189      move Schade → Gomez: +0.224 / +0.485
  move Tarkowski → Calafiori: +1.914 / +0.820  move Thiago → Isak: +3.314 / +1.636
  move Groß → Barnes: +0.813 / +2.427          move Richards → Hill: +0.978 / +1.031
reference (greedy): bank — no move passes its gate
verdict: PASS
GW8 XI 4-4-2 55.260 (Justin in); captain top 5: Haaland 5.798, Gabriel 5.080, Mbeumo 4.932, Isak 4.854, Calafiori 4.596
```

Identical gains to the proposal; only the bank moves, 0.0 → 0.1.

| Check | Result |
|---|---|
| Budget | outs 45.3 + bank 0.4 = 45.7; buys 45.6; bank **0.1**. Bank not double-counted. STATE says 99.1 / 0.0 — see F2 |
| Positions / clubs / formation | 2 GKP, 5 DEF, 5 MID, 3 FWD; ARS 2, BOU 2, LEE 2, TOT 2, rest 1; 4-4-2 legal; captain and vice both in the XI |
| Minutes | XI p_start_gw[0] 0.93–0.96 bar Isak 0.88 (F1); bench Kinsky 0.95, Justin 0.95, Gomez 0.93, Barry 0.94 — no dead slot; the seven non-Isak buys are 7/7 starters, six of them 90 × 7 |
| Flags | all 15 `a`; Isak a/100 (news cleared 27 Sep), Haaland a/100, Van Hecke a/100. Saka `i` (thigh, no date) not bought; Stach and Calvert-Lewin d 50% not bought. Baseline 13:53 UTC (F9) |
| Prior sign flips | none of the eight components on the real basis; smallest prior-only marginal Raya → Trafford +0.045 |
| Concentration | no club with more than one attack-dependent row (ARS, LEE, TOT, BOU pairs are defender/keeper pairs, or Tavernier + Hill) |
| Captain / vice | Haaland 5.798 is the top undiscounted single-GW EP, 0.718 clear. Vice Gabriel 5.080 v Mbeumo 4.932 inside 0.5, both p ≥ 0.85, higher EP holds |
| XI boundary | C20/C8: Justin 3.773 (DefCon 0.161) v Van Hecke 3.565 (0.190), 0.208 apart → Van Hecke starts, −0.208 EP. Barnes 4.121 v Van Hecke 0.556 apart, no 5-3-2 |
| Bench order | Justin, Gomez, Barry: Gomez 3.541 v Barry 3.660 inside 0.25, Gomez's floor share 0.139 > 0.008 → Gomez first, per C8. See F6 for the auto-sub path |
| Chip path | wildcard GW8, 3xc GW9, freehit GW16, bboost GW19 — all inside the bootstrap set-1 windows (wildcard/freehit 2–19, bboost/3xc 1–19), one chip per GW, no consecutive free hit, Haaland held for the 3xc, bench of four playing rows for the bboost |
| C12 | no GW8 XI row is a promoted-club fixture |
| Ledger | marker S8; S1–S5 verbatim; S6 followed at GW8 with the part not taken named; S7 and S8 standing at GW 7, unchanged from the GW7 ledger, each reason says how the plan honours it; no open S# without a row; nothing expired; nothing above the marker. No finding |

## Findings, ranked

### F1 — MED — The wildcard is a one-player bet: nothing without Isak clears the gate

Thiago → Isak is +3.314 / +1.636. Every package without him fails the
system's own chip gate (blend ≥ 6.0 and prior-only ≥ 0 over the greedy
plan, which is bank), on the real basis:

| Package | blend / prior | Gate |
|---|---:|---|
| W2 | +8.304 / +8.078 | PASS (+2.30) |
| W2 minus Thiago → Isak (Thiago kept, 7 moves, bank 1.3) | +4.990 / +6.442 | FAIL |
| W2 with Thiago → Wissa (bank 3.0) | +5.247 / +7.687 | FAIL |
| W2 with Thiago → João Pedro (bank 1.2) | +6.074 / +5.926 | PASS by 0.07, but João Pedro's component is +1.084 / **−0.516**, a prior sign flip — rejected on C14 |

Stress test on Isak's p_start alone (what-if `ep --out` files, the other
positions unchanged, same `objective` basis):

| Isak p_start (flat) | Isak EP6 | Thiago → Isak | Package | Gate |
|---:|---:|---:|---:|---|
| 0.88 (analyst) | 28.62 | +3.314 / +1.636 | +8.304 / +8.078 | PASS |
| 0.85 | — | +2.339 / +0.663 | +7.329 / +7.105 | PASS |
| 0.83 | — | +1.689 / **+0.014** | +6.679 / +6.456 | PASS (sign flip from here down) |
| 0.80 | — | +0.713 / **−0.960** | +5.703 / +5.482 | FAIL |
| 0.75 | — | −0.656 / −2.545 | +4.334 / +3.897 | FAIL |

The package holds the gate down to p ≈ 0.82 and the Isak component keeps its
prior-only sign down to p ≈ 0.83. The whole 2.30 gate margin is worth about
0.06 of Isak's p_start. The proposal's own sensitivity ("about p 0.83,
fails near 0.80") reproduces.

Independent read of 0.88: 6/7 starts (90, 90, 63, 90, 80, 0, 78); the r6
absence was the thigh flag, now cleared a/100 with the news field empty;
Ekitiké out with no date, so LIV have no other fit senior forward; C21
keeps him under 0.93 because the r5–r7 streak is broken. 0.88 is the right
side of the line for GW8. The MED is the shape of the risk, not the
number: an injury is persistent, not an independent 12% per week, and his
2025/26 record is 694 minutes. A recurrence at GW9 leaves a £9.0m row at
zero with the chip spent, and the GW9 fix costs a free transfer and a
£2.9m downgrade.

Bounded downside: even an Isak write-off leaves the W2 squad about +5.0
blend over the current one across GW8–13 (the "Thiago kept" row above
measures the other seven moves); what the bet puts at risk is the chip's
option value, priced by the 6.0 gate, not points against the hold. The
alternative to W2 is therefore hold (§ Hold v W2), not another package.

Note for the GW9 cycle: if Isak starts GW8 and GW9 his r7–r9 streak is
unbroken and C21 lifts him to ≥ 0.93; if he misses either, the package's
assumed EP was over-stated and the retro should say so.

### F2 — MED — STATE `team_value` 99.1 / `bank` 0.0 is now known to be 99.4 / 0.1

final.md copied the GW7 basis because `my-team` could not be read at the
time. It reads now, and the dry-run shows Σ sell 99.0 + bank 0.4 = 99.4,
bank 0.1 after W2. The plan is unaffected (the POST uses `my-team` prices;
`plan.json` already warns that its prices are an audit snapshot), but the
GW9 cycle reads `team_value` from this STATE block as its budget. Ask the
finalizer for a post-deadline record correction (agents/finalizer.md §5,
commit `gw8: correct record — my-team basis 99.4 / 0.1`) once the transfers
are applied, with the `my-team` budget line as the figure.

Does the extra £0.3m open a better package? No. Only £0.1m of it is spendable
without selling a kept player (the other £0.2m sits in Tavernier's and
Haaland's sell prices). Search over every same-position replacement of a W2
buy within its price + 0.1, every pair of such replacements, and every
single swap of a kept player at his real sell price + 0.1, with p_start ≥
0.85 and the club cap: **no candidate gains ≥ 0.3 blend without losing
prior-only.** The blend-positive ones all flip:

| Swap | blend / prior (EP6) | Why rejected |
|---|---:|---|
| Barnes → Stach (LEE 6.0) | +1.55 / −1.89 | prior sign flip; d 50% foot since 13:00Z, priced at p 0.95 |
| Hill → Silva (BOU 5.0) | +0.90 / −3.18 | prior sign flip (review.md F1) |
| Justin → Thomas (COV 4.0) | +0.58 / −3.24 | prior sign flip, promoted club |
| Kinsky → Leno (FUL 4.5) | +0.29 / −0.27 | inside noise, loses prior |

### F3 — MED — Groß → Barnes is the lowest-conviction component (accepted)

+0.813 blend / +2.427 prior-only: the prior carries it. Barnes' blend EP6
23.68 is 1.78 **below** his prior-only 25.46 — his 2026/27 rates are worse
than his history — and the calibration ledger has him at 32 points on 26.0
predicted over seven rounds, two hauls (12, 9) and five rounds of 2–3.
Groß is the reverse: 58 points on 26.8 predicted, +4.46 per GW, the
pool's largest under-prediction in the squad, 46.0% owned, pens, net riser
(+234k). Barnes is 7.5% owned, a net faller (−48k, likely −0.1 tonight),
and NEW turn hard from GW11 (ARS (H), BHA (A), MUN (H); ATT rank 18). So
the move sells the template's steadiest realised scorer for a prior-rated
one whose fixtures end badly inside the window.

It stands because every alternative is worse on the system's numbers:
Groß kept (7 moves) is +7.49 / +5.65; Groß kept with Suzuki +7.102 / +4.685;
Groß → Stach flips and Stach is d 50%. S8 cannot break the tie: +0.813 is
outside its 0.5 band. Accepted risk: the model's 7-round miss on Groß is
the retro's to attribute (BHA pens and bonus, or luck), not this review's
to override. Minutes security is not in question: Barnes 90 × 7.

### F4 — MED — Hill's EP is a model floor the model has over-paid for seven rounds (accepted)

Hill 24.95 blend / 25.05 prior-only, 7/7 × 90, 0.8% owned. His EP is
DefCon (term 6.86 off dc90 10.27) plus BOU's CS rank 3; attack 2.34. The
calibration ledger: 21 points on 24.7 predicted over seven rounds, −0.53
per GW, negative in five of seven — consistent with a DefCon hit rate below
the curve's 10.27 / 10 reading. If that persists his EP6 is about 3 high,
which takes the move to roughly +0.5 blend and the package to about +7.8.
Still comfortably over the gate, and the sold player is no better: Richards
20 on 24.3 predicted (−0.61 per GW). The package without the move
(Richards kept, bank 0.7) is +7.326 / +7.047 PASS — that is also the
fallback named in F5. Minutes security is not in question.

### F5 — LOW — Price and the £0.1m bank

The overnight run has passed and the deadline is today, so no price moves
before the POST; `make-transfers` takes purchase prices from the live
bootstrap and refuses only if drift breaks the bank. Fallback if it does:
drop Richards → Hill (seven moves, +7.326 / +7.047, PASS, bank 0.7).

After the deadline: Isak (+161k net) and Calafiori (+141k) are likely
risers — buying today locks 9.0 and 6.0; Barnes (−48k), Kinsky (−65k) and
held Barry (−86k) are likely fallers. Net ≈ −0.1 team value. Immaterial.

### F6 — LOW — Auto-sub path for the most likely absentee

If Isak (the only XI row under 0.93) misses, bench slot 13 Justin comes in
for a 5-4-1 — legal, and Justin 3.773 is the bench's highest EP anyway. If
a DEF misses, Justin; if a MID misses, Justin (5-3-2). Barry at 15 only
fires on a second absence. Order is right for every single-absence case.

### F7 — LOW — Fixture decay (accepted)

SUN and NEW turn hard from GW11 (E.Le Fée, Barnes). GW14–16 for the squad's
clubs has no cliff: LIV CHE (A), LEE (H), TOT (H); ARS TOT (A), BOU (H), MUN
(H); BOU HUL (H), ARS (A), COV (H); NEW SUN (H), IPS (A), BRE (A). Two free
transfers at GW9 cover the GW11 turn.

### F8 — LOW — Template exposure (accepted, named in final.md)

Held above 30%: Haaland 77.2, Calafiori 54.5. Sold: Groß 46.0, Raya 45.1.
Not held: João Pedro 73.4, Rogers 49.1, De Cuyper 41.8, Cherki 38.8. A João
Pedro or Groß haul lands as rank loss. The two sells are the system's
reading; the Groß one is the thinner (F3).

### F9 — LOW — Flags baseline is 13:53 UTC

The freshness gate passed at 13:53 on all 15 ids. This review ran no
refresh (network). The executor's `auth-check` and `my-team` read precede
the POST; a late team-news change between 13:53 and the apply would show
up only in the live bootstrap's status fields, which `make-transfers` does
not gate on. Friday deadline, press conferences done — small.

## Hold v W2, on a fair comparison

The 6.0 blend gate is the system's price for the chip's future value; W2
clears it by 2.30 on blend and is +8.08 prior-only, so blend and prior agree
to 0.23 — the gain is not a form premium. Three ways to hold, each priced:

| Option | GW8–13 v current | What it keeps | Net v W2 |
|---|---:|---|---:|
| **W2 now** | +8.30 / +8.08 | 2 FTs at GW9 (wildcard does not spend the FT) | — |
| Hold, bank FT, use 2 FTs at GW9 | ≈ +3 blend over GW9–13 (research-mid §3c: best pairs +2.7 to +3.1) | the wildcard to GW19 | ≈ −5.3 blend, ≈ −7 prior |
| Hold one week, wildcard GW9 with Isak's GW8 start seen | −1.41 at GW8 (53.64 v 55.05, and two dead bench slots in the current squad); Isak and Calafiori are both likely +0.1 tonight, so the same package costs 0.2 more against a 0.1 bank and needs a downgrade worth ≈ −0.3 | one week of information on Isak (p ≈ 0.12 of learning he is unfit), Saka (no date) and Stach | ≈ −1.7 certain, against ≈ +0.7 expected from the information |

No blank or double through GW13 and nothing in the GW14–16 fixtures argues
for waiting; the set-1 wildcard expires at GW19 regardless; Saka has no
return date to wait for. The hold's real value is the chip's option on a
future injury crisis, and the gate already prices that at 6.0. W2 wins.

## Verdict

**GO.** Material findings for the user, in order: F1 (the package is a
bet on Isak's fitness at a 0.06 p_start margin; the alternative is hold,
and hold loses), F2 (correct the STATE record to 99.4 / 0.1 after the
apply; the extra money buys nothing better), F3 and F4 (Barnes and Hill
are prior-carried picks the model has mis-priced in opposite directions
this season; both stay on the numbers). No CHANGE: no single or pair swap
within the real budget gains ≥ 0.5 blend without losing prior-only.
