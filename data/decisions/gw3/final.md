# GW3 Final Decision (2026/27)

Deadline **2026-09-04T17:30:00Z**. Weekly cycle. Verdict from
`data/decisions/gw3/review.md`: **APPROVE**, no HIGH findings — no revision
loop. Sources: `data/decisions/gw3/squad-proposal.md`, that review,
`data/analysis/gw3/players-{GKP,DEF,MID,FWD}.json`, `data/raw/gw3/` (snapshot
2026-09-03T17:38Z), STATE block of `data/decisions/gw2/final.md`.

**One free transfer: Kusi-Asare → Barry. Hit 0. Bank £0.0m. 3-4-3, Haaland
(C), Mbeumo (V). Predicted GW3 56.49. No chip.**

## Freshness gate — PASS

`fpl flags --gw 3 --ids 1,4,445,202,427,68,481,237,69,411,106,497,229,423,249,272`
refreshed 2026-09-03T21:43:26Z (16 ids — the post-transfer 15 plus the outgoing
Kusi-Asare). Compared field-by-field against
`data/raw/gw3/players-slim.csv` (fetched 2026-09-03T17:38Z).

| Field | Live reading | Baseline | Delta |
|---|---|---|---|
| `status` | `a` for all 16 | `a` for all 16 | none |
| `news` | blank for all 16 | blank for all 16 | none |
| `chance_of_playing_next_round` | null for 15; Anderson (481) `100` | null for 15; Anderson `100` | none |
| Anderson `news_added` | 2026-08-23T17:00:07.952697Z | identical | none |

No change to any gated field for any selected player. Anderson's `cop 100` is
the cleared flag whose baseline GW2 recorded; it is unchanged, so it is not a
REOPEN. Raw snapshot age at write time ≈ 4h; the 24h window closes
2026-09-04T17:38Z, after the deadline.

## Squad (15) — sell value £99.9m + bank £0.0m = team value £99.9m

EP figures are the code's `ep_gw[0]` (GW3) and `ep_total6` from
`data/analysis/gw3/players-{pos}.json`. Nothing is recomputed here; this table
is the calibration raw material for `fpl calibrate --round 3`.

| Slot | Pos | Player | Id | Club | £ | GW3 EP | EP6 | p_start | Unc | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|---|
| 1 | GKP | Raya | 1 | ARS | 6.0 | 3.123 | 21.39 | 0.95 | LOW | XI |
| 2 | DEF | Gabriel | 4 | ARS | 8.0 | 4.455 | 29.40 | 0.93 | LOW | XI |
| 3 | DEF | Richards | 202 | CRY | 5.0 | 4.064 | 22.96 | 0.90 | LOW | XI |
| 4 | DEF | Tarkowski | 229 | EVE | 6.0 | 3.731 | 23.55 | 0.92 | LOW | XI |
| 5 | MID | Mbeumo | 427 | MUN | 8.0 | 5.265 | 31.58 | 0.91 | LOW | XI · **Vice** |
| 6 | MID | Ndiaye | 237 | MCI | 6.0 | 4.840 | 27.31 | 0.92 | LOW | XI |
| 7 | MID | Anderson | 481 | MCI | 6.4 | 4.393 | 25.00 | 0.90 | LOW | XI |
| 8 | MID | Tavernier | 68 | BOU | 6.0 | 4.339 | 25.88 | 0.92 | LOW | XI |
| 9 | FWD | Haaland | 411 | MCI | 15.5 | 6.388 | 36.40 | 0.93 | LOW | XI · **Captain** |
| 10 | FWD | Thiago | 106 | BRE | 8.0 | 5.098 | 29.13 | 0.92 | LOW | XI |
| 11 | FWD | Barry | 249 | EVE | 5.5 | 4.408 | 25.40 | 0.88 | LOW | XI · **IN** |
| 12 | GKP | Dubravka | 497 | TOT | 4.0 | 0.178 | 1.10 | 0.05 | HIGH | Bench GK |
| 13 | MID | Scott | 69 | BOU | 6.0 | 4.048 | 24.13 | 0.92 | LOW | Bench 1 |
| 14 | DEF | Thiaw | 445 | NEW | 5.0 | 3.561 | 22.79 | 0.88 | LOW | Bench 2 |
| 15 | DEF | Shaw | 423 | MUN | 4.5 | 2.387 | 14.95 | 0.85 | MED | Bench 3 |

Constraints: 2 GKP / 5 DEF / 5 MID / 3 FWD ✓ · Σ price **99.9** ≤ 98.9 sell +
1.0 bank ✓ · club counts MCI 3 (Haaland, Anderson, **Ndiaye — MCI in the GW3
snapshot after his deadline-day move**), ARS 2, EVE 2, MUN 2, BOU 2, CRY 1,
BRE 1, TOT 1, NEW 1 — all ≤ 3 ✓ · 15 unique ids ✓. Shaw (MED) is the only
non-LOW outfielder and is 15th on GW3 EP.

## Starting XI — 3-4-3

| Line | Players |
|---|---|
| GK | Raya |
| DEF | Gabriel, Richards, Tarkowski |
| MID | Mbeumo, Ndiaye, Anderson, Tavernier |
| FWD | **Haaland (C)**, Thiago, Barry |

Legal: 1 GK, 3 DEF, 4 MID, 3 FWD ✓. Two boundary calls, both from the
proposal and both re-verified by the review:

| Boundary | Gap | Rule | Call |
|---|---:|---|---|
| Barry 4.408 (in) vs Scott 4.048 (out) — 3-4-3 vs 3-5-2 | 0.36 | > 0.25 → EP decides | 3-4-3, +0.36 |
| Tarkowski 3.731 vs Thiaw 3.561 for DEF 3 | 0.17 | ≤ 0.25 → **C8** DefCon floor share | Tarkowski (dc 5.8/23.55 = 25% vs Thiaw 4.3/22.79 = 19%); also leads raw EP |

Third C8 boundary observation logged for the GW4 verdict (n → 3): the pair is
**Barry (started) / Scott (benched)**, gap 0.36. The review notes this
boundary narrows to −0.19 on prior-only rates and would then flip to Scott on
DefCon share (22% vs 1%) — recorded as LOW-9 evidence, not acted on: the
blended rate is the system's estimate.

## Captain and vice

certainty multipliers LOW 1.00 / MED 0.92 / HIGH 0.80.

| Rank | Player | Fixture | GW3 EP | Unc | × certainty |
|---:|---|---|---:|---|---:|
| 1 | **Haaland (C)** | MCI v COV (H) | 6.388 | LOW | **6.388** |
| 2 | **Mbeumo (V)** | EVE v MUN (A) | 5.265 | LOW | 5.265 |
| 3 | Thiago | BRE v SUN (H) | 5.098 | LOW | 5.098 |

- **Captain Haaland**, clear by 1.12 discounted. At COV's DEFW band floor
  (0.96) MCI's λ_att falls 2.42 → 2.08 and Haaland lands ≈ 5.9 — still 0.6
  above Mbeumo, so the pick is robust across the whole band. The term is
  attacking, so C12 governs and the C4 residual does not apply.
- **Vice Mbeumo**, second on discounted EP on a band-free fixture, so GW2's
  MED-A (vice on a ± fixture) does not recur. Mbeumo v Thiago is 0.17 and
  flips on prior-only rates; the vice fires only on a Haaland non-start
  (≲ 7%), expected cost < 0.05.

## Bench order

| Slot | Player | GW3 EP | Basis |
|---:|---|---:|---|
| 12 | Dubravka (GK) | 0.178 | only GK2; dead slot, repair queued behind the FWD fix |
| 13 | Scott | 4.048 | highest bench EP; covers any MID or FWD absence (3-4-3 and 3-5-2 both stay legal). A DEF absence skips him to Thiaw automatically |
| 14 | Thiaw | 3.561 | gap to Scott 0.49 > 0.25 → EP orders; the DEF cover |
| 15 | Shaw | 2.387 | MED (0.85), gap 1.17 — last |

## Transfers made

| Out | In | Cost |
|---|---|---:|
| Kusi-Asare (FUL, FWD, 4.5, id 272) | Barry (EVE, FWD, 5.5, id 249) | **0** (1 free transfer) |

Funding: bank 1.0 + Kusi-Asare 4.5 = 5.5 = Barry's GW3 price
(`cost_change_event 0`). Bank after **£0.0m**. Free transfers at this deadline
were 1 (GW2 STATE); one new FT accrues for GW4.

Realized value +1.84 on XI-only, **+4.37 with auto-sub cover** — the move that
converts a FWD bench slot with 0 minutes in three consecutive GWs (retro MED-B)
into a 0.88-p_start starter, enables the 3-4-3 (+0.36 in GW3 alone) and
promotes Scott (4.4 EP-if-plays) to first sub. Structural, not form: Barry's
0.72 → 0.88 p_start is Beto's 2 Sep sale to Fiorentina, leaving Everton no
other senior forward, and his rates are prior-blended (`prior_weight 0.80`,
1898 prior minutes). Logged for LOW-4: the earmark predates his GW2 points —
GW2's final.md wrote it off his GW1 start. Prior-only EP6 22.10 still beats
every ≤ £5.5m alternative.

No second transfer: no pair including Barry reaches the gross ≥ 6 hit bar; the
best (Tarkowski → De Cuyper, +4.14 gross) nets +0.14 and spends GW4's best FT
candidate.

### Executor note — apply before the price window (review edit 2)

Apply Kusi-Asare → Barry **before ~01:30 UTC on 4 Sep**, the single price-change
night between now and the deadline. Barry is net **+75k in-event** at 4.5%
ownership with `cost_change_event 0`; a rise to 5.6 makes the move unfundable
(bank 1.0 + 4.5 = 5.5). Executing tonight is a zero-cost action that retires
the risk.

**Fallback if Barry is ≥ 5.6 at execution: bank the free transfer** — one of
the three options GW2 named. With 2 FTs at GW4, Kusi-Asare → Barry plus
Raya → Trafford (+0.49 EP6 on its own, frees £1.0m) funds Barry at 5.6
hit-free. Deferring Barry one GW costs ≈ 0.7 EP (0.36 XI + ≈ 0.4 cover). Do
**not** substitute a HIGH-tagged HUL forward (McBurnie 19.43, all six rows
banded) — it would fill the slot for less and need fixing again. The COV pair
GW2 named first is retired on evidence: Thomas-Asante lost the start to
Awoniyi (p_start 0.45) and Simms is unscored. Kusi-Asare is net −7k, no drop
risk.

There is no `data/auth.json`, so the API executor step does not run; the plan
is applied manually on the website.

## Predicted GW3 points

**56.49** = XI 50.104 + captain double 6.388. Recomputed at finalization from
the per-player GW3 EP in the squad table above.

Six-GW horizon of this squad (best legal XI + captain per GW): **337.04**,
against 335.20 for the pre-transfer squad.

| GW | Formation | XI EP | Captain | Total |
|---:|---|---:|---|---:|
| 3 | 3-4-3 | 50.10 | Haaland 6.39 | 56.49 |
| 4 | 3-4-3 | 48.66 | Haaland 5.73 | 54.39 |
| 5 | 3-4-3 | 51.86 | Haaland 6.29 | 58.15 |
| 6 | 3-4-3 | 50.40 | Mbeumo 5.68 | 56.08 |
| 7 | 3-4-3 | 50.30 | Haaland 6.67 | 56.97 |
| 8 | 3-5-2 | 49.26 | Mbeumo 5.69 | 54.95 |

## Chips — none played (`chip: null`)

### GW3 Triple Captain gate (C5) — not activated

The gate is clearable on arithmetic (the COV-dependent share of MCI's λ_att is
10.3%; nine-tenths is City's own rating plus home advantage), but clearing it
is not the decision. The TC's marginal value is one extra Haaland: GW3 6.388
against GW5 (SUN H, band-free) 6.29 — **+0.10 EP for accepting a ±15% band
whose floor (≈ 5.9) sits below the GW5 central estimate**. Hold GW5, as GW2
earmarked. GW7 IPS(H) 6.67 is the model's best of the three but is banded and
IPS's attack rating just rose +0.15; re-derive when the band lifts after GW3,
once the promoted clubs reach three played fixtures.

### Plan (set 1; windows read from bootstrap `chips`)

| Chip | Window | Earmark | Status | Basis |
|---|---|---|---|---|
| 3xc | GW1–19 | **GW5** — MCI v SUN (H), Haaland 6.29 | provisional | Band-free; GW3 offers only +0.10 for a ±15% band. If the GW4 premium restructure ever proceeds, this migrates to **Fernandes GW6 TOT(H) 6.79** |
| wildcard | GW2–19 | **GW8** | provisional | EVE defensive cliff from GW7 (Tarkowski 3.36 / 3.26), LIV/NFO swings land GW5–7, GW6–7 sit behind the 19-day break; MCI at the 3-cap blocks Guéhi/Cherki without a rebuild. Held from GW2 |
| bboost | GW1–19 | **GW19** | provisional | Bench half-repaired (Barry); GK2 and Shaw remain dead weight. Last set-1 GW |
| freehit | GW2–19 | **GW16** | provisional | Placeholder — no blank or double in the 380-fixture list; re-check each cycle |

All four earmarks are in-window, one per GW, and freehit is non-consecutive
trivially. Nothing sold this GW is a chip target.

**GW8 BOU(H) is struck as a Fernandes TC option (review edit 3, LOW-8).** It
collides with the GW8 wildcard earmark, and only one chip may be played per
gameweek. While that earmark stands, **GW6 TOT(H) 6.79 is the only legal
Fernandes TC slot**.

This prose is a forecast. `chip: null` in the STATE block is the only field
that activates a chip this GW, and `chip_plan:` the only machine-readable
version of the plan above.

## Accepted risks

Carried from the review with no HIGH outstanding and no revision loop run.

| Ref | Level | Risk | Handling |
|---|---|---|---|
| MED-1 | MED | GW4 restructure decision rule is not recency-robust: on prior-only attack rates the Isak + B.Fernandes move is **−1.69 gross**, not +9.74, and conditions (a) and (b) as written would fire it anyway | Fixed in §GW4 earmarks below by condition (c). Nothing in GW3's executed decision changes |
| MED-2 | MED | Barry rises to 5.6 before the deadline (net +75k in-event, one price night at ~01:30 UTC 4 Sep) | Executor note above: apply tonight; named fallback is banking the FT for the GW4 two-FT route |
| MED-3 | MED | Four >30%-owned players unheld: João Pedro 69.7, B.Fernandes 48.6, Calafiori 43.9, Szoboszlai 41.4 (≈ 204pp combined) | Deliberate and priced. João Pedro is the one that bites — +0.1/event at +243k net, so the eventual swap gets ≈ 0.1 dearer per week deferred; on prior-only rates JP 27.88 v Thiago 29.13, so the hold is not a recency call. MED-E verdict stays at GW4 |
| MED-4 | MED | MCI at the 3-cap with the captain on the same fixture: 4 XI shares on MCI v COV; P(MCI blank) 8.9% central, 12.8% at band floor | Accepted. Anderson's and Ndiaye's DefCon terms are the floor. The cap block on Guéhi (30.37, 2nd-best DEF) and Cherki (30.68) is structural — wildcard GW8 material |
| LOW-6 | LOW | Dead GK2 leaks ≈ 0.18 EP/GW (5% Raya non-start × 3.6) | Repair queued behind the FWD fix; needs +£0.5m the bank lacks. Route: GW5 via the Tarkowski → De Cuyper cash, or the wildcard |
| LOW-9 | LOW | Barry/Scott XI boundary (0.36) and Mbeumo/Thiago vice (0.17) both flip on prior-only rates | Inside the model's own estimate; logged as GW4 C8 / LOW-4 evidence |
| LOW-5 | LOW | EVE v MUN carries Tarkowski, Barry, Mbeumo (V) and Shaw (bench) | Internal hedge, not a stack: a Mbeumo goal costs Tarkowski's CS, worth 5.11/23.55 of his EP6 at P(CS) 0.185. No action |
| LOW-7 | LOW | Sell-value drift — Mbeumo −491k, Gabriel −217k, Ndiaye −213k, Shaw −209k, Thiago −192k net out this event | Up to −£0.5m team value; no GW3 selection impact. Trims GW4/5 headroom, but Tarkowski → De Cuyper still frees ≥ £1.2m at 4.8 |

## GW4 earmarks — re-derived next cycle, not commitments

**1. Premium skeleton (the headline GW4 decision).** Haaland → Isak (or João
Pedro) + Scott → B.Fernandes, −4, gross +9.74 / net +5.74 on GW3 blended
numbers. It proceeds only if **all three** conditions hold:

- (a) the C10 ledger shows the ≥ £8.0m under-prediction is not concentrated in
  Haaland;
- (b) the Fernandes-over-Haaland EP6 lead survives round 3;
- (c) **its gross clears ≥ 6 with the attack terms recomputed on prior-only
  rates, i.e. with the current-season component removed. Today that figure is
  −1.69, against +9.74 blended.**

Condition (c) is the operative gate, and GW4 must **test** it rather than
re-discover it. The reason: (a) is already answered by the pooled GW1–2
ledger, which puts the band's under-prediction on **Fernandes +6.84 per
appearance, not Haaland +1.69** (Isak +0.48) — so "not concentrated in
Haaland" is already true and cannot be what protects the decision. And (b) is
mechanical: `w_prior` only moves 0.769 → 0.69 at 270 minutes, so one ordinary
game cannot unwind a 23-point one. On prior-only rates the horizon reverses —
base Σ6 331.92 v 330.22 for Isak + Fernandes — because Fernandes' outright EP6
lead (38.06 → 33.26) is his 1.05 xG/90 fortnight against a 0.30 prior, while
Haaland's rises (36.40 → 36.87). Conditions (a) and (b) alone are not a gate.
Rank variance points the same way: Haaland is 71.2% owned and captained by
most of that, so on a trade whose EV sign flips under a robustness check,
variance breaks the tie toward holding.

**2. Otherwise the FT.** Tarkowski → De Cuyper (+2.3 realized, frees £1.3m →
the GK2 fix at GW5) or Shaw → Ajer / Justin (+6.8 / +7.2 raw, ≈ +2.9 with
cover). Shaw → De Cuyper needs £0.2m the bank will not have unless a holding
rises. De Cuyper was rejected this week on sequencing only — buying him ahead
of the flagged bench fix would have stranded Barry at this budget.

**3. Chips.** Hold the GW8 wildcard; after GW4's band lift, re-check whether
the GW7 IPS(H) TC alternative beats GW5.

## Retro-correction compliance

| Item | Binding | How met |
|---|---|---|
| **C11** | emit `chip:`, `chips_used:` and `chip_plan:` explicitly every GW | All three present in the STATE block, `chip: null` included |
| **C5** | TC only on fixture-independent EP | No GW3 TC; GW5 earmark held. GW3's edge over GW5 is +0.10 and inside the band |
| **C8** | near-tied bench/XI orderings resolved on DefCon floor | Applied once (Tarkowski over Thiaw, gap 0.17). Barry/Scott (0.36) and Scott/Thiaw (0.49) exceed the tie band. Third boundary observation logged for the GW4 verdict |
| **C4 residual / C12** | a banded fixture is never a selected player's largest *defensive* term | Checked all 11 XI: no DEF or GK has a banded CS term as its largest component (ARS unbanded; Richards' and Tarkowski's largest terms are appearance). Barry's banded rows (EVE GW5 IPS(H)±, GW6 HUL(A)±) are attacking-side, which C12 permits |
| **C7** (consumed) | discount by uncertainty tag | All XI LOW; Shaw's MED sits 15th; no HIGH-tagged player bought |
| **C6** | full 15-line `picks:` block | Emitted below in the strict schema |
| **MED-B** dead bench | GW3 FT earmarked at the FWD half | Done via Barry. GK2 repair path: GW5 via the Tarkowski → De Cuyper cash, or the wildcard |
| **MED-D** funding headroom | do not re-litigate | Executed at 5.5 as GW2 planned; fallback is a GW2-named option |
| **LOW-4** recency test (GW4 retro) | log incoming transfers against last-GW points | Barry: 10 pts GW1–2, but the driver is structural (Beto sold), rates prior-blended, earmark written before those points. De Cuyper (17 pts, 599k in) and the Fernandes/Isak restructure rejected/deferred partly on this test |
| **Premium under-prediction** | withheld on power | Skeleton restructure deferred to GW4 behind the C10 ledger and the new condition (c) |

## Rationale summary

The week is deliberately minimal: one free transfer, no hit, no chip. It spends
the FT on the squad's only structural defect — a forward bench slot that has
recorded 0 minutes for three consecutive gameweeks (retro MED-B) — and buys a
starter whose minutes case is a rival's departure rather than a hot streak.
The +4.37 honest value is mostly auto-sub cover and the 3-4-3 it unlocks, not
a bet on Barry's form.

The genuinely large decision, breaking the single-premium skeleton for
Isak + B.Fernandes, is deferred a second time. The model says it now clears
the hit bar (+9.74 gross), but the review's robustness check reverses the sign
on prior-only rates (−1.69), and the retro's largest open calibration item —
the ≥ £8.0m under-prediction band — is the very sample this trade would act
on. Deferral is nearly free: GW4 has the same single FT and the same −4, so
waiting forfeits only GW3's own +1.10 and buys a third round of premium data
plus the C10 ledger. What changes this cycle is not the deferral but the
decision rule: condition (c) makes prior-only gross the gate, so GW4 tests the
recency artefact rather than re-derives it.

Captaincy is unchanged and robust — Haaland clears the field by 1.12 and stays
0.6 ahead at COV's band floor. MCI sits at the 3-player cap with four XI shares
on one fixture; that concentration is accepted and correctly routed to the GW8
wildcard, which is also where the unreachable Guéhi and Cherki live.

## STATE

```yaml
# Convention (as GW2): free_transfers_banked = free transfers available at the
# NEXT (GW4) deadline. This GW's single FT was spent on Kusi-Asare → Barry;
# one new FT accrues.
# team_value = post-transfer squad sell value 99.9 + bank 0.0 under the
# paper-pricing convention (no data/auth.json, so no authenticated selling
# prices exist). The GW3 entry snapshot shows bank 1.0 / value 99.9
# pre-transfer, matching the convention exactly.
gw: 3
team_id: 8455344
team_value: 99.9
bank: 0.0
free_transfers_banked: 1
chip: null
chips_used: []
transfers_made:
  - {out: Kusi-Asare, in: Barry, cost: 0}
chip_plan:
  - {chip: 3xc, gw: 5, status: provisional}
  - {chip: wildcard, gw: 8, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 1, name: Raya, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: false, vice: false}
  - {id: 202, name: Richards, position: 3, captain: false, vice: false}
  - {id: 229, name: Tarkowski, position: 4, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 5, captain: false, vice: true}
  - {id: 237, name: Ndiaye, position: 6, captain: false, vice: false}
  - {id: 481, name: Anderson, position: 7, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: true, vice: false}
  - {id: 106, name: Thiago, position: 10, captain: false, vice: false}
  - {id: 249, name: Barry, position: 11, captain: false, vice: false}
  - {id: 497, name: Dubravka, position: 12, captain: false, vice: false}
  - {id: 69, name: Scott, position: 13, captain: false, vice: false}
  - {id: 445, name: Thiaw, position: 14, captain: false, vice: false}
  - {id: 423, name: Shaw, position: 15, captain: false, vice: false}
```
