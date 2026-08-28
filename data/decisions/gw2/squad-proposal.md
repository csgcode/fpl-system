# GW2 Squad Proposal — weekly cycle

Deadline 2026-08-28T17:30:00Z | snapshot `data/raw/gw2/` (fetched
2026-08-28T09:45:31Z, age < 8h) | inputs: `data/analysis/gw2/players-*.json`,
`data/analysis/gw2/fixtures.md`, `data/retro/gw1.md` (C1–C8) | prior state:
`data/decisions/gw1/final.md` STATE block + orchestrator squad reconstruction
(the GW1 `picks:` list is missing — retro defect C6; ids below are re-derived
from the GW2 bootstrap and match the retro's reconstruction).

## Paper-team pricing convention

`team_id` is null — no real FPL entry exists, so there are no API selling
prices. Convention used throughout, and to be carried until an entry exists:

- Sell price = GW1 purchase price when the current price is unchanged, lower
  bounded by current price on drops (Anderson bought 6.5, now 6.4 → sells 6.4).
- On rises: purchase + floor(rise/2) in 0.1 steps.
- Buy prices from the GW2 bootstrap (`now_cost`).

Only one of our 15 moved: Anderson 6.5 → 6.4. Squad sell value **£98.9m**
+ bank £0.0m pre-transfer. Enzo's price is unchanged at 7.0 → sells 7.0.

## Transfer decision — 1 free transfer: Enzo → Tavernier

**OUT Enzo (CHE, sells £7.0) → IN Tavernier (BOU, £6.0). Free. Bank after:
£1.0m.**

| Metric | Enzo | Tavernier |
|---|---|---|
| Price | 7.0 | 6.0 |
| p_start | 0.61 | 0.88 |
| Uncertainty | HIGH | LOW |
| EP6 (GW2–7) | 18.30 (rank 36) | 25.00 (rank 7) |
| EP by GW | 3.05 2.53 3.71 2.79 3.17 3.05 | 4.38 4.22 4.01 3.99 3.81 4.59 |
| ± band exposure | — | none — BOU meet no COV/HUL/IPS in GW2–7 |

EP arithmetic, both ways:

- **Raw player delta: +6.70 EP6** (25.00 − 18.30).
- **Realized XI delta: +3.16 EP6.** The honest number — the old squad would
  already have benched Enzo most weeks (his GW-by-GW EP loses to the 4th-DEF
  alternative in all six GWs), so the transfer's true gain is the 10th-outfield
  slot upgrade: with Tavernier that slot scores
  max(Tavernier, Tarkowski, Shaw) = 4.38+4.22+4.01+4.27+4.38+4.59 = 25.84;
  without him it scores max(Enzo, Tarkowski, Shaw) = 3.38+3.55+3.96+4.27+4.38+3.16
  = 22.68. Allowing the 4-4-2 flex the model projects for GW5–6 adds ~0.3 more.

Both readings clear the ≥ 2 EP make-it threshold. Beyond EP, the move is the
retro's process sell: Enzo is the squad's live rotation risk (C7 — benched in
the only lineup observed, p_start 0.61 wide-not-confident, HIGH), a £7.0m asset
dominated by £6.0m alternatives at p_start 0.88–0.93, and MED-1 from GW1 is
retired with him. Tavernier: 90' in GW1, pens#3 + FK1 + CK1, BOU club count
goes to 2 (with Scott) — legal.

**No second transfer.** The dead FWD slot (Kusi-Asare 1.41 EP6) is real but a
−4 hit fails the bar once bench EP is priced honestly: a bench-3 forward's EP
realizes only through auto-subs (~0.3 expected pts/GW of cover), so the
realized gross of Kusi-Asare → Thomas-Asante is ~1.5–2 over the horizon, not
the raw +11.76 — far below the gross ≥ 6 hit rule. It costs almost nothing to
wait one week and fix it free. See the GW3 plan below.

### Why £1.0m is held (> £0.5m guideline)

The £1.0m is the exact funding gap for next cycle's planned free transfer:
Kusi-Asare (sells 4.5) + 1.0 = **£5.5m = Barry (EVE)**, the best playing
enabler that is not C4-blocked (EP6 17.92, MED, won the shirt on the pitch —
78', goal, 37 BPS vs Beto 11'). Spending the £1.0m now would force either the
failed hit above or a worse target. EVE would go to 3 (Tarkowski, Ndiaye,
Barry) — legal; Barry is a forward, so the EVE GW7 *defensive* cliff (LOW-2,
now starting GW7 per the DEF analyst) does not price into him, and EVE's
attack turns easier from GW5. Decision re-derives next cycle from GW3 analysis
— this is an earmark, not a commitment.

### Swap-pass audit (every attempted move)

| # | Move | Raw ΔEP6 | Verdict |
|---|---|---|---|
| 1 | Enzo → Tavernier (6.0) | +6.70 (realized +3.16) | **ACCEPT** — free, ≥2, frees £1.0m, kills the HIGH rotation risk |
| 2 | Enzo → Szoboszlai (LIV 7.0) | +8.72 (+2.02 vs Tavernier) | REJECT — spec rule: never buy what the ticker turns against in two. LIV P(CS) 37% → 20% at GW5, the window's largest swing (−16.7pp); he is a GW2–4 asset priced season-long. Also frees £0.0 (kills the GW3 bench fix) and converges on a 43.2%-owned template pick |
| 3 | Enzo → Gomez (BHA 5.0) | +5.55 (−1.15 vs Tavernier) | REJECT — the extra £1.0m freed buys nothing the GW3 plan needs; Tavernier strictly better on EP |
| 4 | Kusi-Asare → Thomas-Asante (COV 5.0), −4 hit | +11.76 raw, ~+1.5–2 realized | REJECT — fails gross ≥ 6 on realized bench value; C4-exposed (COV attack index is his largest EP term — the analysts clear him as bench cover only, and the safer read of C4 is not to buy the breach at all when a clean alternative exists next week) |
| 5 | Kusi-Asare → Barry (EVE 5.5), −4 hit | +16.51 raw, ~+2–2.5 realized | REJECT this week — same realized-value logic; unaffordable pre-transfer anyway (needs the £1.0m move 1 frees). Becomes the GW3 free transfer |
| 6 | Shaw → Mitchell (CRY 4.5) | +0.52 | REJECT — < 2 threshold; not worth the only FT. Wildcard-list item |
| 7 | Dubravka → Phillips (HUL 4.0) | +0.13 | REJECT — inside noise per the GKP analyst; never worth a transfer |
| 8 | Bank the FT (no move) | 0 (2 FTs at GW3) | REJECT — forgoes +3.16 realized EP; the ≥ 2 rule says move, and holding Enzo keeps an unpriced HIGH in the XI pool |
| 9 | Tarkowski → (any) | — | PREMATURE — his GW2–6 run (3.37–4.38/GW) is intact; the cliff starts GW7. Exit window GW5–6, per LOW-2 |

Premium skeleton (procedure step 1) re-affirmed, not re-derived: single
premium, Haaland only. The GW1 full-squad test (best no-Haaland structure
−4.27 over 6 GWs) stands; he remains #1 overall on EP6 (35.75) and carries the
TC earmark. No second premium: B.Fernandes (12.0, 31.46) would cost two squad
tiers to fund and GW1 showed his captaincy hedge is worth ≈0 while Haaland
out-captains him every GW.

## Squad after transfer (15) — sell value £98.9m, bank £1.0m

| Pos | Player | Club | Price | GW2 EP | EP6 | p_start | Unc | Role |
|---|---|---|---|---|---|---|---|---|
| GKP | Raya | ARS | 6.0 | 3.77 | 22.37 | 0.94 | LOW | XI |
| GKP | Dubravka | TOT | 4.0 | 0.37 | 2.38 | 0.12 | HIGH | Bench GK |
| DEF | Gabriel | ARS | 8.0 | 4.45 | 26.31 | 0.92 | LOW | XI |
| DEF | Thiaw | NEW | 5.0 | 3.95 | 24.15 | 0.89 | LOW | XI |
| DEF | Richards | CRY | 5.0 | 3.43 | 24.14 | 0.89 | LOW | XI |
| DEF | Tarkowski | EVE | 6.0 | 3.37 | 22.67 | 0.92 | LOW | Bench 1 |
| DEF | Shaw | MUN | 4.5 | 3.38 | 17.66 | 0.90 | LOW | Bench 2 |
| MID | Mbeumo | MUN | 8.0 | 4.90 | 26.84 | 0.86 | LOW | XI · **Vice** |
| MID | Anderson | MCI | 6.4 | 4.23 | 26.98 | 0.93 | LOW | XI |
| MID | Tavernier | BOU | 6.0 | 4.38 | 25.00 | 0.88 | LOW | XI |
| MID | Ndiaye | EVE | 6.0 | 3.80 | 24.25 | 0.90 | LOW | XI |
| MID | Scott | BOU | 6.0 | 4.03 | 23.36 | 0.93 | LOW | XI |
| FWD | Haaland | MCI | 15.5 | 5.32 | 35.75 | 0.93 | LOW | XI · **Captain** |
| FWD | Thiago | BRE | 8.0 | 4.08 | 26.64 | 0.90 | MED | XI |
| FWD | Kusi-Asare | FUL | 4.5 | 0.24 | 1.41 | 0.05 | HIGH | Bench 3 |

Constraints: 2 GK / 5 DEF / 5 MID / 3 FWD ✓ · club counts ARS 2, MCI 2, MUN 2,
EVE 2, BOU 2, rest ≤ 1 — all ≤ 3 ✓ · Σ buy-side spend within sell value + bank
✓ · 15 unique ✓. All 15 `status: a`, no news, per the 10:12Z flags refresh —
the finalizer re-runs this gate.

## Starting XI — 3-5-2

| Line | Players |
|---|---|
| GK | Raya |
| DEF | Gabriel, Thiaw, Richards |
| MID | Mbeumo, Tavernier, Anderson, Ndiaye, Scott |
| FWD | **Haaland (C)**, Thiago |

Selection is raw GW2 EP: the nine outfielders above Richards pick themselves;
the last slot is a three-way near-tie — Richards 3.43, Shaw 3.38, Tarkowski
3.37, all inside 0.25 EP. Applied C8 as the tie-break: Richards has the
highest DefCon floor share of the three (ratio 1.08, P(hit) 0.67,
fixture-independent) and also leads on raw EP; Shaw is additionally
disqualified from an EP-led start by C4's strict reading — his GW2 number
rests on the IPS(H) clean sheet, a ±-band term, which is the exact condition
that produced his GW1 MODEL miss. Legal: 1 GK, 3 DEF, 5 MID, 2 FWD ✓.

## Captaincy

Certainty mapping per spec: LOW 1.00 / MED 0.92 / HIGH 0.80.

| # | Option | GW2 EP | Unc | Discounted | Note |
|---|---|---|---|---|---|
| 1 | **Haaland (MCI a CRY)** | 5.32 | LOW | **5.32** | Band-free fixture |
| 2 | Mbeumo (MUN v IPS) | 4.90 | LOW | 4.90 | ± fixture — treat as range (C4 captaincy note) |
| 3 | Gabriel (ARS a AVL) | 4.45 | LOW | 4.45 | Band-free; AVL DEFW just worsened +0.17 |
| 4 | Tavernier (BOU v EVE) | 4.38 | LOW | 4.38 | |
| 5 | Anderson (MCI a CRY) | 4.23 | LOW | 4.23 | |

**Captain: Haaland** — clears the field by 0.42 discounted, on a band-free
fixture, with the squad's highest p_start. **Vice: Mbeumo** — next best
discounted EP. His IPS(H) fixture carries the ± band, but the vice only fires
if Haaland logs zero minutes (≲5%), so the banded exposure is ~0.02 EP;
Gabriel (4.45, band-free) is the safety alternative and loses 0.45 of
headline EP for it. Not taken.

## Bench order

| Slot | Player | GW2 EP | Basis |
|---|---|---|---|
| GK | Dubravka | 0.37 | Only GK2. Kinsky kept the TOT shirt; slot confirmed dead (GKP analyst: best £4.0 swap gains 0.13 — noise) |
| 1 | Tarkowski | 3.37 | **C8 tie-break**: 0.009 behind Shaw — a dead tie — so DefCon floor share decides: Tarkowski ratio 1.02 / P(hit) 0.57 vs Shaw 0.63 / 0.16. Floor is fixture-independent, and the auto-sub scenario is exactly the high-variance case where floor is worth most |
| 2 | Shaw | 3.38 | GW2 EP is ±-derived (IPS H clean sheet); C4 says do not rank him on it |
| 3 | Kusi-Asare | 0.24 | p_start 0.05, dead fodder, must sit last. GW3 fix planned |

## Predicted GW2 points

**51.66** = XI 46.34 + captain double 5.32. Per-player baseline for the GW2
retro is the GW2 EP column in the squad table above; written before the
deadline per the persistence rule.

## Provisional chip plan (set 1, windows from bootstrap `chips`)

| Chip | Window | Earmark | One-line justification |
|---|---|---|---|
| Triple Captain | GW1–19 | **GW5 — MCI v SUN, Haaland 6.67** | **Moved from GW3 (C5).** The GW3 gate is not cleared and cannot clear: 63% of Haaland's 6.90 GW3 EP is the COV attacking term, inside the ±15pp band whose floor (6.18) sits *below* the GW5 number — the case cannot rest on fixture-independent EP, so C5 mandates deferral. GW5 is band-free (SUN: full PL prior, league-worst defensive ticker, rating worsening) and costs ≤ 0.24 EP vs the GW3 central estimate — both analysts found this independently |
| Wildcard | GW2–19 | GW8 | Moved from GW10: the EVE cliff now starts GW7 (Tarkowski, partially Ndiaye), LIV/BRE defensive turns land GW5–7, and GW6–7 ratings sit behind the 19-day international break — rebuild immediately after the break with real GW6–7 information |
| Bench Boost | GW1–19 | GW19 | Unchanged. Unusable until the bench is rebuilt (MED-2): GW3 fixes the FWD slot free; GK2 stays dead until the wildcard. Last set-1 GW before expiry |
| Free Hit | GW2–19 | GW16 (placeholder) | No blank or double exists anywhere in the 380-fixture list — nothing to aim at yet; re-check every cycle for the first `event: null` fixture |

## Rationale and rejected alternatives

The week's decision is deliberately minimal: one free transfer that converts
the squad's only HIGH-uncertainty XI asset into a top-7 LOW one, plus £1.0m
staged for a free bench repair next cycle. The GW1 retro's headline —
residual model error −0.56, the miss was finishing variance — argues for
process continuity, not churn: Haaland and Thiago are held on xG (0.74 and
1.00 in GW1, the squad's two highest), and no FWD EP was shaved (retro
discipline rule).

**Three strongest rejected alternatives:**

1. **Enzo → Szoboszlai (LIV 7.0, EP6 27.02): +2.02 EP6 over Tavernier,
   forgone.** Rejected on the standing rule — never transfer for what the
   ticker turns against in two: Liverpool's P(CS) collapses 37% → 20% at GW5,
   the largest swing of any kind in the window, and his price would be paid
   at the top of a 43.2%-ownership chase. Also frees £0.0m, which kills the
   GW3 bench fix and forces a future hit — the true cost is ≈ 0 after that
   is priced.
2. **Kusi-Asare → Barry / Thomas-Asante on a −4 hit this week: raw +16.51 /
   +11.76, realized ~+2, net negative.** A bench-3 forward's EP only reaches
   the scoreline through auto-subs (~0.3 pts/GW of expected cover), so the
   hit fails the gross ≥ 6 rule by a factor of three. Deferred one week to a
   free transfer, cost of waiting ≈ 0.3 pts. Target: Barry over the COV pair
   — C4-clean, MED vs HIGH, +4.75 EP6, and the COV pair's largest EP term is
   their own promoted-club attack index.
3. **Bank the free transfer (2 FTs at GW3): forgoes +3.16 realized EP6.**
   Two FTs next week could do Enzo + Kusi-Asare together at zero cost — but
   that just moves this week's +1.01 GW2 XI gain (Tavernier 4.38 over
   Tarkowski 3.37 in the 10th slot) into lost points and keeps a p_start-0.61
   HIGH in the squad through another unobservable Chelsea team sheet. The
   same end-state is reached one GW slower for no saving.

## Retro-correction compliance (this agent's obligations)

| Correction | Compliance |
|---|---|
| C4 | No bought player carries a promoted-club term as largest EP component (Tavernier has zero ± exposure). Shaw's ±-derived GW2 EP excluded from XI/bench ranking. COV forwards not bought. Mbeumo vice exposure priced (~0.02 EP) |
| C5 | GW3 TC deferred to GW5 — the GW3 case needs the COV term (63% of the number) and so fails the fixture-independent test by construction |
| C6 | Full 15-line `picks:` list emitted below in the strict CLAUDE.md schema |
| C8 | Applied twice: Tarkowski-over-Shaw bench order (0.009 gap → floor share) and Richards for the last XI slot (0.06 gap → floor share, same verdict as raw EP) |

## Accepted risks

- **MED-A — Vice on a ± fixture.** Mbeumo's GW2 EP is partly IPS-band-derived;
  bounded at ~0.02 expected EP via the ≲5% vice-activation path.
- **MED-B — Dead bench persists one more week.** Kusi-Asare (0.05) and
  Dubravka (0.12) cover nothing in GW2. Priced: expected auto-sub loss ≈ 0.3
  pts. GW3 free transfer fixes the FWD half; GK2 waits for the wildcard.
- **MED-C — Tavernier's role evidence is n = 1** (90' + set-piece duty in the
  only observed lineup, on a 0.88 prior-blended p_start). The same is true of
  every alternative this cycle; his LOW tag is C7-compliant (p_start 0.879 ≥
  the 0.85 floor for LOW).
- **LOW — EVE concentration path.** The GW3 Barry plan would take EVE to 3
  with the club's defensive cliff at GW7; acceptable because Barry is a
  forward (no CS term) and EVE's *attack* improves from GW5, but it blocks
  any third EVE defensive asset and is re-checked next cycle.
- **LOW — chip-plan horizon.** WC GW8 and FH GW16 earmarks sit behind the
  19-day international break; both are placeholders, re-derived every cycle.

## STATE

```yaml
gw: 2
team_id: null
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

Notes for the finalizer: `free_transfers_banked: 1` follows the GW1 STATE
convention — free transfers available at the NEXT (GW3) deadline (this GW's FT
was spent; one new FT accrues). `team_value` = squad sell value 98.9 + bank
1.0 under the paper-pricing convention above. Freshness gate must be re-run on
all 15 ids before final.md; any status/news/chance delta on a selected player
is a REOPEN.
