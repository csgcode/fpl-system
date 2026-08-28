# GW2 Final — weekly cycle (2026/27)

Deadline 2026-08-28T17:30:00Z. Review verdict: **APPROVE** (zero HIGH; two MED
and five LOW findings, all documentation conditions). Finalized from
`data/decisions/gw2/squad-proposal.md` with **no selection changes** — the
review's conditions are recorded below, not acted on as re-selection. No
revision loop ran.

## Freshness gate — PASS

| Check | Method | Result |
|---|---|---|
| Injury/news flags, all 15 | `fpl flags --gw 2 --ids 1,4,445,202,427,68,481,237,69,411,106,497,229,423,272` refreshed 2026-08-28T10:51:25Z | Zero deltas on `status`, `chance_of_playing_next_round` and `news` against the analysis-time baseline |
| Baseline source | `data/raw/gw2/players-slim.csv` + `data/analysis/gw2/players-*.json` | 14 players `status: a`, `chance: null`, `news: ""`; Anderson per F4 below |
| Anderson (F4 baseline) | Baseline recorded explicitly as `status: a`, `chance_of_playing_next_round: 100`, `news_added: 2026-08-23T17:00:07Z` (a cleared knock) | Live values identical — **no delta**. Recorded so a future re-downgrade (e.g. 100 → 75) diffs as REOPEN rather than reading as "still flagged, no change" |
| Snapshot age | `data/raw/gw2/` fetched 2026-08-28T09:45:31Z, finalized 10:51Z | ~1.1h — well inside the 24h requirement ✓ |
| Deadline margin | Deadline 17:30Z vs finalization 10:51Z | 6h39m remaining ✓ |

No `status`, `chance_of_playing_next_round` or `news` value moved for any
selected player between analysis time and finalization. Gate cleared; no REOPEN.

## Transfer made

**OUT Enzo (CHE, sold £7.0m) → IN Tavernier (BOU, £6.0m). 1 free transfer,
hit cost 0.** Bank after: £1.0m. Free transfers banked toward GW3: 1.

| Metric | Enzo | Tavernier |
|---|---|---|
| Price | 7.0 | 6.0 |
| p_start | 0.61 | 0.88 |
| Uncertainty | HIGH | LOW |
| EP6 (GW2–7) | 18.30 (rank 36) | 25.00 (rank 7) |
| ± band exposure | — | none — BOU meet no COV/HUL/IPS in GW2–7 |

Raw player delta **+6.70 EP6**; realized-XI delta **+3.16 EP6** (the honest
number — the old squad benched Enzo in all six GWs, so the gain is the
10th-outfield slot upgrade: 25.84 with Tavernier vs 22.68 without). Both
readings clear the ≥ 2 EP threshold. Beyond EP this is the retro's process
sell: Enzo was the squad's only HIGH-uncertainty XI asset (C7), and MED-1 from
GW1 retires with him. BOU club count goes to 2 — legal.

No second transfer: the dead FWD slot is real, but the −4 hit fails the gross
≥ 6 bar once bench EP is priced through auto-subs (~1.5–2 realized, not the
+11.76 raw). Waiting one week fixes it free.

## Squad (15) — sell value £98.9m + bank £1.0m = team value £99.9m

Pre-transfer sell value was **£99.9m** (GW1 Σ100.0 − 0.1 on Anderson's price
drop, Enzo still held at 7.0); £98.9m is the *post*-transfer figure. This
supersedes the proposal's prose slip, which labelled £98.9m as pre-transfer
(review F3); every downstream number was already correct.

Predicted points below are the calibration baseline: score these against
`fpl actuals --round 2` in the GW2 retro.

| # | Pos | Player | Club | Price | GW2 EP | EP6 | p_start | Unc | Role |
|---|-----|--------|------|-------|--------|-----|---------|-----|------|
| 1 | GKP | Raya | ARS | 6.0 | 3.77 | 22.37 | 0.94 | LOW | XI |
| 2 | GKP | Dubravka | TOT | 4.0 | 0.37 | 2.38 | 0.12 | HIGH | Bench (GK) |
| 3 | DEF | Gabriel | ARS | 8.0 | 4.45 | 26.31 | 0.92 | LOW | XI |
| 4 | DEF | Thiaw | NEW | 5.0 | 3.95 | 24.15 | 0.89 | LOW | XI |
| 5 | DEF | Richards | CRY | 5.0 | 3.43 | 24.14 | 0.89 | LOW | XI |
| 6 | DEF | Tarkowski | EVE | 6.0 | 3.37 | 22.67 | 0.92 | LOW | Bench 1 |
| 7 | DEF | Shaw | MUN | 4.5 | 3.38 | 17.66 | 0.90 | LOW | Bench 2 |
| 8 | MID | Mbeumo | MUN | 8.0 | 4.90 | 26.84 | 0.86 | LOW | XI · **Vice** |
| 9 | MID | Anderson | MCI | 6.4 | 4.23 | 26.98 | 0.93 | LOW | XI |
| 10 | MID | Tavernier | BOU | 6.0 | 4.38 | 25.00 | 0.88 | LOW | XI |
| 11 | MID | Ndiaye | EVE | 6.0 | 3.80 | 24.25 | 0.90 | LOW | XI |
| 12 | MID | Scott | BOU | 6.0 | 4.03 | 23.36 | 0.93 | LOW | XI |
| 13 | FWD | Haaland | MCI | 15.5 | 5.32 | 35.75 | 0.93 | LOW | XI · **Captain** |
| 14 | FWD | Thiago | BRE | 8.0 | 4.08 | 26.64 | 0.90 | MED | XI |
| 15 | FWD | Kusi-Asare | FUL | 4.5 | 0.24 | 1.41 | 0.05 | HIGH | Bench 3 |

Constraints (recomputed at finalization): 2 GK / 5 DEF / 5 MID / 3 FWD ✓ ·
Σ sell value £98.9m, buy-side spend within sell value + bank ✓ · club counts
ARS 2, MCI 2, MUN 2, EVE 2, BOU 2, rest ≤ 1 — all ≤ 3 ✓ · 15 unique ✓.

Pricing convention (paper team — no authenticated selling prices available):
sell price = GW1 purchase price when unchanged, lower-bounded by current price
on drops (Anderson 6.5 → 6.4); on rises, purchase + floor(rise/2). Buy prices
from the GW2 bootstrap.

**Real entry confirmed post-assembly.** This decision was assembled as a paper
team, but `data/entry.json` was filled at 10:53Z with `team_id: 8455344`
("404 FC"), and the fetched snapshot `data/raw/gw2/entry-8455344.json` confirms
the entry holds exactly this squad: joined 2026-08-21 before the GW1 deadline,
`entered_events: [1]`, GW1 points 40 (matches the retro's actual),
`last_deadline_bank: 0`, `last_deadline_value: 1000` (£100.0m). **This final.md
therefore applies to the real team, not a paper one.** No `data/auth.json`
exists, so the team-executor stays off this GW and the paper-pricing convention
above still stands (authenticated sell prices come from `my-team`, which needs
credentials); **the transfer and lineup must be applied manually on the FPL
site.** The freshness gate is unaffected — it passed at 10:51Z and no player
input changed.

## Starting XI — 3-5-2

| Line | Players |
|---|---|
| GK | Raya |
| DEF | Gabriel, Thiaw, Richards |
| MID | Mbeumo, Tavernier, Anderson, Ndiaye, Scott |
| FWD | **Haaland (C)**, Thiago |

Legal: 1 GK, 3 DEF ≥ 3, 5 MID ≥ 2, 2 FWD ≥ 1, 11 total ✓. Auto-sub paths
legal — a missing FWD routes to Tarkowski for a 4-5-1 (≥ 1 FWD retained via
Haaland).

Selection is raw GW2 EP: the nine outfielders above Richards pick themselves;
the last slot was a three-way tie inside 0.25 EP (Richards 3.43, Shaw 3.38,
Tarkowski 3.37), broken by C8 on DefCon floor share — Richards leads on ratio
1.08 / P(hit) 0.67 and on raw EP. Shaw is additionally disqualified from an
EP-led start by C4: his GW2 number rests on the IPS(H) clean sheet, a ±-band
term, the exact condition behind his GW1 model miss.

- **Captain: Haaland** — 5.32 GW2 EP, LOW uncertainty (discount 1.00), clears
  the field by 0.42 discounted on a band-free fixture (MCI a CRY) with the
  squad's highest p_start. Carries the TC earmark for GW5.
- **Vice: Mbeumo** — next best discounted EP (4.90). His IPS(H) fixture carries
  the ± band, but the vice only fires if Haaland logs zero minutes (≲ 5%), so
  banded exposure is ~0.02 EP. Gabriel (4.45, band-free) is the safety
  alternative and costs 0.45 headline EP — not taken.

## Bench order

| Slot | Player | GW2 EP | Basis |
|---|---|---|---|
| GK | Dubravka | 0.37 | Only GK2. Kinsky kept the TOT shirt; slot dead — best £4.0 swap gains 0.13, inside noise |
| 1 | Tarkowski | 3.37 | **C8 tie-break**: 0.009 behind Shaw — a dead tie — so DefCon floor share decides (ratio 1.02 / P(hit) 0.57 vs Shaw 0.63 / 0.16). Floor is fixture-independent, and auto-subs are the high-variance case where floor is worth most |
| 2 | Shaw | 3.38 | GW2 EP is ±-derived (IPS H clean sheet); C4 forbids ranking him on it |
| 3 | Kusi-Asare | 0.24 | p_start 0.05, dead fodder, must sit last. GW3 fix planned |

## Predicted GW2 points

**51.66** = XI 46.34 + captain double 5.32. Recomputed at finalization from the
per-player GW2 EP above.

## Chip plan (set 1, windows from bootstrap `chips`) — none played this GW

| Chip | Window | Earmark | Justification |
|---|---|---|---|
| Triple Captain | GW1–19 | **GW5 — MCI v SUN, Haaland 6.67** | Moved from GW3 (C5): 63% of Haaland's 6.90 GW3 EP is the COV attacking term, whose band floor (6.18) sits *below* the GW5 number, so the case cannot rest on fixture-independent EP. GW5 is band-free and costs ≤ 0.24 EP vs the GW3 central estimate |
| Wildcard | GW2–19 | GW8 | Moved from GW10: the EVE cliff starts GW7, LIV/BRE defensive turns land GW5–7, and GW6–7 ratings sit behind the 19-day international break — rebuild with real GW6–7 information |
| Bench Boost | GW1–19 | GW19 | Unusable until the bench is rebuilt (MED-B). GW3 fixes the FWD half free; GK2 waits for the wildcard. Last set-1 GW before expiry |
| Free Hit | GW2–19 | GW16 (placeholder) | No blank or double exists in the 380-fixture list — nothing to aim at yet; re-check every cycle for the first `event: null` fixture |

## GW3 plan (earmark, re-derived next cycle — not a commitment)

Kusi-Asare (sells 4.5) + bank 1.0 = **£5.5m Barry (EVE)**: EP6 17.92, MED, won
the shirt on the pitch (78', goal, 37 BPS vs Beto's 11'), C4-clean. EVE would go
to 3 (Tarkowski, Ndiaye, Barry) — legal; Barry is a forward, so the EVE GW7
*defensive* cliff does not price into him.

## Accepted risks

Carried forward unresolved after the review. All were priced, not overlooked.

### MED-A — Vice on a ± fixture
Mbeumo's GW2 EP is partly IPS-band-derived; bounded at ~0.02 expected EP via the
≲ 5% vice-activation path.

### MED-B — Dead bench persists one more week (review F7 concurs)
Kusi-Asare (p_start 0.05) and Dubravka (0.12) cover nothing in GW2. Expected
auto-sub loss ≈ 0.3 pts, and three simultaneous XI absences are needed before a
dead slot is reached — Tarkowski (0.92) and Shaw (0.90) are genuine cover. No
cheaper fix exists this week: the Kusi-Asare hit fails the gross ≥ 6 bar and
Dubravka swaps gain ≤ 0.13. GW3's free transfer fixes the FWD half; GK2 waits
for the wildcard, which also gates Bench Boost.

### MED-C — Tavernier's role evidence is n = 1
90' plus set-piece duty (pens #3, FK1, CK1) in the only observed lineup, on a
0.88 prior-blended p_start. True of every alternative this cycle; the LOW tag is
C7-compliant (0.879 ≥ the 0.85 floor).

### MED-D (review F1) — Barry earmark has zero funding headroom against the market's strongest rise signal
The GW3 plan leaves exactly £0.0m slack, and Barry carries the heaviest buy
pressure of any player checked: `transfers_in_event` 122,618 vs out 18,560
(net +104k at 3.2% ownership, off an 8-point GW1). A £0.1 rise before the GW3
deadline strands the plan. **Named fallback, from this cycle's own rejected
alternatives: the COV £5.0m forwards Thomas-Asante or Simms as bench cover** —
with a playing £4.5m GK for Dubravka, or simply banking the FT, as further
options. GW3 must not re-litigate this. The GW2 decision is robust to every
Barry price: the transfer cannot be brought forward (bank is 0.0 until Enzo
sells), Szoboszlai frees £0.0m and kills the plan outright, and Gomez costs a
guaranteed −1.15 EP6 — more than the expected loss if Barry rises. If decisions
are applied manually and the move slips, it is the earmark that degrades, not
the GW2 transfer.

### MED-E (review F2) — Template fades re-affirmed on current numbers
Deliberate, on the record this cycle, per the differential-risk rule:

| Faded | Own % | Why faded, GW2 numbers |
|---|---|---|
| João Pedro (CHE) | 67.8 (up from 63.9) | Thiago is held above him on EP6: **26.64 vs 26.36**. His GW4 (CHE v HUL, 5.41 EP — his best window fixture) is now inside the horizon while the GW3 FT is earmarked for Barry, so this is the week it is most likely to bite |
| Calafiori (ARS) | 41.6 | EP6 24.56 clears Thiaw (24.15) and Richards (24.14) by less than a transfer is worth, while adding a third correlated ARS asset |
| B.Fernandes (MUN) | 48.4 | £12.0 costs two squad tiers to fund; GW1 showed his captaincy hedge is worth ≈ 0 while Haaland out-captains him every GW |
| Szoboszlai (LIV) | 43.2 | +2.02 EP6 over Tavernier, forgone on the standing rule — LIV P(CS) collapses 37% → 20% at GW5, the window's largest swing |

**The Enzo sale takes CHE exposure to zero** while CHE rates 2nd on the 6-GW
attack ticker — the sharpest edge of the João Pedro fade. Both fades are
defensible on the numbers above; the review classed the omission as a process
defect, not a selection error.

### LOW items
- **LOW-1 — EVE concentration path.** The GW3 Barry plan takes EVE to 3 with the
  club's defensive cliff at GW7. Acceptable (Barry is a forward, no CS term;
  EVE's attack improves from GW5) but it blocks any third EVE defensive asset.
  Re-checked next cycle.
- **LOW-2 — Chip-plan horizon.** WC GW8 and FH GW16 sit behind the 19-day
  international break; both are placeholders, re-derived every cycle.
- **LOW-3 (review F5) — Price drift on holds, notional under paper pricing.**
  Anderson (net −134k, already −0.1 this event) and Dubravka (net −25k) risk
  further −0.1 steps, each costing 0.1 of sell value under the drop-bounded
  convention. Mbeumo shows net −117k (post-loss MUN exodus) — EP case intact, no
  action, check at GW3. Timing on the executed move is favorable both ways:
  Tavernier bought ahead of a rise (net +57k), Enzo sold at 7.0 ahead of heavy
  outflow (net −60k).
- **LOW-4 (review F6) — Recency-pattern watch, assigned to the GW4 retro.** This
  cycle's buy (Tavernier, 10 pts GW1) and next cycle's earmark (Barry, 8 pts
  GW1) are both GW1 top-scorers. Each has model support independent of the haul,
  and the sale is process-driven, so no bias verdict now — **the GW4 retro must
  test whether incoming transfers systematically chase last-GW points.**
- **LOW-5 (review F3) — Prose arithmetic slip in the proposal, superseded here.**
  The proposal's "£98.9m pre-transfer" is wrong; pre-transfer is £99.9m,
  post-transfer £98.9m. Corrected in the squad section above. No downstream
  number was affected.

## Rationale summary

The week's decision is deliberately minimal: one free transfer converting the
squad's only HIGH-uncertainty XI asset into a top-7 LOW one, plus £1.0m staged
for a free bench repair next cycle. The GW1 retro's headline — residual model
error −0.56, the miss was finishing variance — argues for process continuity
rather than churn: Haaland and Thiago are held on xG (0.74 and 1.00 in GW1, the
squad's two highest) and no FWD EP was shaved.

The premium skeleton is re-affirmed, not re-derived: single premium, Haaland
only. The GW1 full-squad test (best no-Haaland structure −4.27 over six GWs)
stands; he remains #1 overall on EP6 (35.75) and carries the TC earmark.

Retro-correction compliance: **C4** — no bought player carries a promoted-club
term as its largest EP component (Tavernier has zero ± exposure), Shaw's
±-derived EP excluded from XI and bench ranking, COV forwards not bought.
**C5** — GW3 TC deferred to GW5, the GW3 case failing the fixture-independent
test by construction. **C6** — the full 15-line `picks:` list is emitted below
in the strict schema (its absence from GW1's final.md was the defect).
**C8** — applied twice, on the Tarkowski-over-Shaw bench order (0.009 gap) and
the last XI slot (0.06 gap).

## STATE

```yaml
# Convention: free_transfers_banked = free transfers available at the NEXT
# (GW3) deadline. This GW's FT was spent on Enzo → Tavernier; one new FT accrues.
# team_value = post-transfer squad sell value 98.9 + bank 1.0, paper-pricing
# convention (no data/auth.json, so no authenticated selling prices exist).
gw: 2
team_id: 8455344
team_value: 99.9
bank: 1.0
free_transfers_banked: 1
chips_used: []
transfers_made:
  - {out: Enzo, in: Tavernier, cost: 0}
picks:
  - {id: 1, name: Raya, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: false, vice: false}
  - {id: 445, name: Thiaw, position: 3, captain: false, vice: false}
  - {id: 202, name: Richards, position: 4, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 5, captain: false, vice: true}
  - {id: 68, name: Tavernier, position: 6, captain: false, vice: false}
  - {id: 481, name: Anderson, position: 7, captain: false, vice: false}
  - {id: 237, name: Ndiaye, position: 8, captain: false, vice: false}
  - {id: 69, name: Scott, position: 9, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 10, captain: true, vice: false}
  - {id: 106, name: Thiago, position: 11, captain: false, vice: false}
  - {id: 497, name: Dubravka, position: 12, captain: false, vice: false}
  - {id: 229, name: Tarkowski, position: 13, captain: false, vice: false}
  - {id: 423, name: Shaw, position: 14, captain: false, vice: false}
  - {id: 272, name: Kusi-Asare, position: 15, captain: false, vice: false}
```
