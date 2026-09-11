# GW4 Squad Proposal — weekly cycle (2026/27)

Optimizer: A4. Horizon GW4–GW9 (six gameweeks, no blank or double in window).
Deadline 2026-09-12 12:30 UTC. Budget = live `my-team` selling prices
(Σ 99.4 by the fifteen relayed rows; the relayed total said 99.6 — the rows
are used) + bank 0.0 = **£99.4m**; the GW3 STATE block's paper 99.9 is
superseded. Free transfers available: 1. Chips available: bboost, 3xc,
wildcard, freehit (set 1; windows from bootstrap `chips`: wildcard/freehit
GW2–19, bboost/3xc GW1–19).

## Decision in one line

**Bank the free transfer** (2 FTs at the GW5 deadline). No chip. XI 3-4-3
unchanged from GW3. Captain **Haaland**, vice **Gabriel**. Triple Captain
earmark moves **GW5 → GW9**. Predicted GW4: **55.21** (prior-only 52.66).

## 0. State read

| Source | Read |
|---|---|
| Live `my-team` (11 Sep ~18:10 UTC) | 15 picks as GW3 STATE; sell Σ 99.4 (row sum; relayed total 99.6), bank 0.0, FT 1, 0 transfers this GW; all four set-1 chips unused |
| data/decisions/gw3/final.md STATE | same 15 ids; `chip_plan` 3xc GW5, wildcard GW8, freehit GW16, bboost GW19; no `## Suggestions` section (ledger introduced after GW3 → every row of data/suggestions.md in window is open) |
| data/retro/gw3.md | C5, C8, C14, C15, C16 bind A4 — applied in §9 |
| Analyst escalations | Shaw (bench 15) flagged 11 Sep 13:00, 75% unspecified, p_start_gw 0.62 then 0.80–0.82; Dubravka 0 minutes four GWs; Gakpo (not owned) thigh flag; GW4 fails the C5 TC gate; GW7 IPS(H) banded; GW9 BHA(H) 2.28 beats GW5 SUN(H) 2.15 band-free; ARS P(CS) is a clip floor; EVE turns bad from GW7, BRE/MCI improve from GW7, CHE front-loaded |
| Snapshot | data/raw/gw4 fetched 2026-09-11 17:58 UTC (< 24h at deadline) |

Two EP sets are used throughout, per C14: **blend** = the analysts'
data/analysis/gw4/players-*.json; **prior-only** = the same inputs rerun
through `fpl ep` with `prior_weight: 1.0` on every row (scratch output, not
written to data/analysis). Prior-only changes only the rates; p_start,
fixtures and the formula are identical.

## 1. Premium skeleton — Haaland only, re-tested

Haaland (15.5, EP6 37.94 blend / prior-only within 0.5) is the squad's only
player above £9m. The GW3 restructure question (Haaland + Anderson →
Isak + B.Fernandes) is closed per C15 — conditions (a) and (b) are answered
NO — and re-scored here under C14's rule as the only live gate:

| Move | Buy | Sell | Gross EP6 blend | Gross EP6 prior-only | Verdict |
|---|---:|---:|---:|---:|---|
| Haaland + Anderson → Isak + B.Fernandes (−4) | 21.1 | 21.8 | +3.33 | **−1.91** | sign flips; below 6 on both — never |
| Haaland → Isak (free) | 9.1 | 15.5 | −12.65 | −11.19 | never |

Would £15.5 split 7.9 + 7.6 score more? No route in the pool reaches
Haaland's 6.32 EP/GW mean from two mid-priced slots without displacing an
existing 4.0+ EP/GW starter; the best FWD pair under £15.5 (João Pedro 28.95
+ Wissa 27.01 = 55.96 EP6) replaces Haaland + Barry (62.19) and loses the
captain multiplier on the pool's highest single-GW EP every week. Skeleton
holds: one premium, funds spread over four 5.9–7.9 midfield/forward slots.

## 2. Transfer decision — swap pass (audit trail)

Every same-position swap within budget (sell + bank 0.0) and the club cap
was scored on the 6-GW objective (Σ best-XI EP + captain EP), on both EP
sets. Full enumeration: 15 out-slots × every eligible in-player, then every
pair of out-slots against the top-40 EP6 of each position (−4 hit applied
once, 1 FT banked). Top rows:

| Out (sell) | In (buy) | Own | Δ blend | Δ prior-only | Rule |
|---|---|---:|---:|---:|---|
| Anderson (6.3) | Stach LEE (6.0) | 2.8% | **+1.38** | −2.85 | < 2 on blend; sign flips |
| Thiago (7.9) | João Pedro CHE (7.7) | 73.2% | +1.27 | +0.43 | < 2 on both |
| Anderson (6.3) | E.Le Fée SUN (5.9) | 4.6% | +1.21 | −2.05 | < 2; flips |
| Anderson (6.3) | Schade BRE (6.0) | 3.7% | +1.17 | −1.63 | < 2; flips |
| Richards (5.0) | De Cuyper BHA (4.8) | 21.4% | +1.05 | −0.96 | < 2; flips |
| Tarkowski (6.0) | Calafiori ARS (5.8) | 48.7% | +0.79 | +0.39 | < 2 on both |
| Scott (6.0) | Stach LEE (6.0) | 2.8% | +0.64 | +0.25 | < 2 on both |
| Shaw (4.4) | O'Shea IPS (4.0) | 3.0% | +0.49 | +0.09 | < 2; bench-only value |
| Shaw (4.4) | Thomas COV (4.0) | 9.0% | +0.42 | +0.05 | < 2; bench-only value |
| Scott (6.0) | Barnes NEW (6.0) | 2.3% | −0.42 | **+2.94** | prior-only lead only; negative on blend |
| Scott (6.0) | Barkley AVL (5.0) | 0.3% | −1.14 | +2.27 | as above |
| Richards (5.0) | Canvot CRY (4.9) | 0.2% | +0.41 | +2.13 | as above |
| Thiago (7.9) | Wissa NEW (6.2) | 17.6% | −0.68 | +2.03 | as above |
| Dubravka (4.0) | Steele BHA (4.0) | 4.3% | 0.00 | 0.00 | no playing £4.0 GK exists; Raya starts every modelled GW |
| Ndiaye (5.9) | E.Le Fée SUN (5.9) | 4.6% | −0.07 | −0.24 | best Ndiaye swap is negative |

Best swap per out-slot (blend): Anderson +1.38, Thiago +1.27, Richards
+1.05, Tarkowski +0.79, Scott +0.64, Shaw +0.49, Raya +0.31 (Martinez CHE,
then 1.0 in bank), Thiaw +0.19, Dubravka 0.00, Ndiaye −0.07, Barry −0.43,
Mbeumo −3.67, Gabriel −3.84, Tavernier −4.26, Haaland −12.65.

Two-transfer moves (gross; net = gross − 4):

| Out | In | Buy | Gross blend | Gross prior-only | Rule |
|---|---|---:|---:|---:|---|
| Anderson + Thiago | Cherki MCI (7.8) + Wissa NEW (6.2) | 14.0 | **+5.06** | +3.46 | < 6 on both → no hit; the only pair positive on both readings |
| Anderson + Thiaw | Janelt BRE (5.0) + Guéhi MCI (6.0) | 11.0 | +4.99 | −2.77 | flips |
| Tarkowski + Anderson | Guéhi MCI (6.0) + Stach LEE (6.0) | 12.0 | +4.17 | −2.03 | flips |
| Thiago + Anderson | João Pedro CHE (7.7) + Stach LEE (6.0) | 13.7 | +2.64 | −2.42 | flips |
| Barry + Scott | Wissa NEW (6.2) + Janelt BRE (5.0) | 11.2 | +1.49 | **+5.91** | prior-only lead only |

### Verdict: bank the free transfer

- Best free move +1.38 < 2.0 → bank (transfer rule).
- Best hit gross +5.06 < 6.0 → no hit; every other pair above +4 flips sign
  on prior-only rates, which C14 forbids outright.
- The pattern is the one C14 was written for: every blended gain above +1
  is a two-to-three-round rate tilt (Stach, Le Fée, Schade, De Cuyper each
  turn negative on prior rates), and every prior-only gain above +2 is
  negative on the blend. No move clears 2.0 on both readings.
- Banking buys a **free two-transfer** at GW5: Anderson + Thiago → Cherki +
  Wissa is +5.06 / +3.46 with no hit, clearing the gate on both readings, and
  MCI stays at the 3-cap because Anderson leaves as Cherki arrives. Re-derived
  next cycle on GW5 data, not committed here.
- Bench repairs (Shaw → Thomas/O'Shea, GK2) are worth < 0.5 on the XI
  objective and wait for the GW5 headroom or the wildcard. Shaw's 75% flag
  costs nothing while he is 15th.

### Template exposure — accepted, priced

João Pedro 73.2% unheld (Thiago → JP +1.27 / +0.43), Calafiori 48.7%
(Tarkowski → Calafiori +0.79 / +0.39), B.Fernandes 48.6% (no single route
under the cap and budget; the pair is C15-closed). Each is below the transfer
gate on both readings; MED-E remains an accepted, priced rank-variance risk.

## 3. Squad (15) — sell £99.4m + bank £0.0m = team value £99.4m

| # | Player | Club | Pos | Sell | Buy | EP6 blend | EP6 prior | p_start GW4 | Unc | Role GW4 |
|---:|---|---|---|---:|---:|---:|---:|---:|---|---|
| 1 | Raya | ARS | GKP | 6.0 | 6.0 | 21.76 | 22.29 | 0.96 | LOW | XI |
| 2 | Dubravka | TOT | GKP | 4.0 | 4.0 | 0.89 | 0.89 | 0.04 | HIGH | GK2 |
| 3 | Gabriel | ARS | DEF | 8.0 | 8.0 | 29.41 | 30.83 | 0.93 | LOW | XI (V) |
| 4 | Tarkowski | EVE | DEF | 6.0 | 6.0 | 24.78 | 23.76 | 0.92 | LOW | XI |
| 5 | Richards | CRY | DEF | 5.0 | 5.0 | 20.97 | 22.28 | 0.90 | LOW | XI |
| 6 | Thiaw | NEW | DEF | 5.0 | 5.0 | 21.74 | 23.60 | 0.90 | LOW | bench 14 |
| 7 | Shaw | MUN | DEF | 4.4 | 4.4 | 13.12 | 13.50 | 0.62 | HIGH | bench 15 |
| 8 | Mbeumo | MUN | MID | 7.9 | 7.9 | 31.02 | 27.21 | 0.93 | LOW | XI |
| 9 | Tavernier | BOU | MID | 6.0 | 6.0 | 29.68 | 26.07 | 0.93 | LOW | XI |
| 10 | Ndiaye | MCI | MID | 5.9 | 5.9 | 25.40 | 24.58 | 0.93 | LOW | XI |
| 11 | Scott | BOU | MID | 6.0 | 6.1 | 24.78 | 23.15 | 0.93 | LOW | XI |
| 12 | Anderson | MCI | MID | 6.3 | 6.3 | 24.00 | 26.38 | 0.92 | LOW | bench 13 |
| 13 | Haaland | MCI | FWD | 15.5 | 15.5 | 37.94 | 35.27 | 0.93 | LOW | XI (C) |
| 14 | Thiago | BRE | FWD | 7.9 | 7.9 | 27.69 | 27.25 | 0.92 | LOW | XI |
| 15 | Barry | EVE | FWD | 5.5 | 5.6 | 24.25 | 21.45 | 0.88 | LOW | XI |
| | **Total** | | | **99.4** | 99.6 | **357.43** | 348.51 | | | |

Constraints: 2 GKP / 5 DEF / 5 MID / 3 FWD ✓; clubs MCI 3 (Haaland, Ndiaye,
Anderson), ARS 2, EVE 2, MUN 2, BOU 2, CRY/BRE/TOT/NEW 1 ✓; no transfer, so
bank stays 0.0 (the ≤ £0.5m rule is met by construction).

Six-gameweek horizon of this squad (blend), the objective the swap pass
scored against:

| GW | Opp (Haaland) | Best XI EP + cap (blend) | Formation | Notes |
|---:|---|---:|---|---|
| 4 | MUN(A) | 55.21 | 3-4-3 | Barry over Anderson by 0.02 |
| 5 | SUN(H) | 58.35 | 3-4-3 | Thiaw in for Richards |
| 6 | LIV(A) | 56.12 | 3-4-3 |  |
| 7 | IPS(H) | 57.39 | 3-5-2 | Anderson in for Barry; EVE cliff starts |
| 8 | AVL(A) | 55.16 | 3-5-2 | Richards in for Thiaw |
| 9 | BHA(H) | 56.28 | 3-5-2 |  |
| | **Σ GW4–9** | **338.51** (prior-only 327.24) | | ceiling with no budget or club cap: 376.98 = 62.8 per GW |

## 4. Starting XI — 3-4-3

| Slot | Player | Club | Pos | GW4 fixture | EP blend | EP prior |
|---:|---|---|---|---|---:|---:|
| 1 | Raya | ARS | GKP | SUN(A) | 3.78 | 3.86 |
| 2 | Gabriel (V) | ARS | DEF | SUN(A) | 5.05 | 5.28 |
| 3 | Tarkowski | EVE | DEF | TOT(A) | 4.33 | 4.16 |
| 4 | Richards | CRY | DEF | IPS(H) | 3.79 | 4.03 |
| 5 | Tavernier | BOU | MID | BRE(H) | 5.00 | 4.39 |
| 6 | Mbeumo | MUN | MID | MCI(H) | 4.82 | 4.25 |
| 7 | Scott | BOU | MID | BRE(H) | 4.15 | 3.88 |
| 8 | Ndiaye | MCI | MID | MUN(A) | 4.04 | 3.89 |
| 9 | Haaland (C) | MCI | FWD | MUN(A) | 6.00 | 5.58 |
| 10 | Thiago | BRE | FWD | BOU(A) | 4.38 | 4.33 |
| 11 | Barry | EVE | FWD | TOT(A) | 3.87 | 3.44 |
| | **XI total** | | | | **49.21** | 47.08 |
| | + captain (Haaland) | | | | 6.00 | 5.58 |
| | **Predicted GW4** | | | | **55.21** | 52.66 |

Formation and boundary calls (C16: undiscounted EP, no certainty multiplier):

- **Barry 3.87 v Anderson 3.85** for the eleventh slot — 3-4-3 v 3-5-2.
  The blend edge is 0.02, inside model noise; prior-only reverses it
  (3.44 v 4.25). C8 does not reach this slot (it governs the auto-sub order,
  where the floor argument lives). Open suggestion S1 asks to move away from
  Anderson and may break a tie inside 0.5 EP → **Barry starts**. Logged as a
  robustness flag, as GW3's review logged the Barry/Scott boundary.
- **Richards 3.79 v Thiaw 3.21** for DEF3. Richards' IPS(H) row is banded;
  at the band floor (P(CS) 0.29 → 0.14) his EP is ≈ 3.25, still ahead.
  Prior-only 4.03 v 3.50. C4 residual: IPS(H) 0.29 ties CRY's band-free
  NEW(H) GW8 row at 0.29, so the promoted-club fixture is not his *single*
  largest defensive term. Marginal at the floor — noted for the red team.
- Scott 4.15 and Ndiaye 4.04 hold MID3/MID4 on both readings (prior-only
  3.88 / 3.89 v Anderson 4.25 — see the Barry note; only one of the three can
  sit in 3-4-3 and Anderson's EP6 24.00 is the lowest of the five MIDs).

## 5. Captaincy

certainty: LOW 1.00 / MED 0.92 / HIGH 0.80 — applied to this step only (C16).

| Rank | Player | GW4 fixture | EP blend | Unc | × certainty | Gap to #1 | EP prior-only |
|---:|---|---|---:|---|---:|---:|---:|
| 1 | **Haaland** | MUN (A), λ_att 1.80 | 6.00 | LOW | **6.00** | — | 5.58 |
| 2 | Gabriel | SUN (A), P(CS) 0.44 (clip floor) | 5.05 | LOW | 5.05 | 0.95 | 5.28 |
| 3 | Tavernier | BRE (H) | 5.00 | LOW | 5.00 | 1.00 | 4.39 |
| 4 | Mbeumo | MCI (H) | 4.82 | LOW | 4.82 | 1.18 | 4.25 |
| 5 | Thiago | BOU (A) | 4.38 | LOW | 4.38 | 1.62 | 4.33 |

Haaland by 0.95 over the field — above the 0.5 tie band, so no suggestion
or variance argument enters. Prior-only narrows the gap to 0.30 but does not
flip it. **Vice: Gabriel** — 5.05 v Tavernier 5.00 v Mbeumo 4.82 sit inside
0.5 with no suggestion touching them; EP order picks Gabriel, prior-only
widens his lead to 0.89, and he is on a different fixture from the captain
(Mbeumo shares the derby). The vice fires only on a Haaland non-start
(p_start 0.93).

## 6. Bench order

| Slot | Player | Pos | GW4 fixture | EP blend | EP prior | DefCon share | Gap to slot above |
|---:|---|---|---|---:|---:|---:|---:|
| 12 | Dubravka | GKP | EVE(H) | 0.15 | 0.15 | 0.00 |  |
| 13 | Anderson | MID | MUN(A) | 3.85 | 4.25 | 0.26 |  |
| 14 | Thiaw | DEF | LEE(A) | 3.21 | 3.50 | 0.17 | 0.64 |
| 15 | Shaw | DEF | MCI(H) | 1.46 | 1.51 | 0.08 | 1.75 |

C8 (near-tie ≤ 0.25 → DefCon floor share): Anderson v Thiaw gap 0.64,
Thiaw v Shaw 1.75 — no pair inside the band, EP order stands. Anderson's
0.26 share is also the highest, so the tie-break would not have reordered
anything. Shaw at 75% is 15th; a non-start costs nothing unless two XI
outfielders also miss.

## 7. Predicted GW4 points

XI 49.21 + captain 6.00 = **55.21** (blend). Prior-only for the same XI:
47.08 + 5.58 = 52.66; the prior-only optimum (3-5-2 with Anderson) is 53.46.

## 8. Chips — none played this GW (`chip: null`)

### C5 — GW4 Triple Captain gate: FAILS

Haaland's GW4 row is MUN (A), λ_att 1.80 — City's third-worst attacking row
in the window; his 6.00 is below his 6.32 window mean. No fixture-independent
case survives that, and nothing else in the squad is within 0.95 of him.

### Plan (set 1, windows from bootstrap `chips`)

| Chip | Window | Earmark | Status | Basis |
|---|---|---|---|---|
| 3xc | GW1–19 | **GW9** — MCI v BHA (H), Haaland 6.75 (moved from GW5) | provisional | GW9 6.75 v GW5 SUN(H) 6.54: +0.21 on Haaland's own row, +0.13 λ_att per A2, both rows band-free. GW7 IPS(H) 6.81 is his highest row but banded — rejected on C5 regardless of arithmetic. Brighton's DEFW moved 0.97 → 1.08 in two cycles, so re-test every cycle to GW9 |
| wildcard | GW2–19 | **GW8** | provisional | EVE cliff from GW7 (Tarkowski 3.64 / 3.36, Barry 4.17 / 3.28 GW7–8); Thiaw's and Tarkowski's promoted-club rows expire by then; GK2 and Shaw dead weight. The GW5 two-FT window may pre-empt part of it — re-derive |
| freehit | GW2–19 | **GW16** | provisional | Placeholder — no blank or double in GW4–9; re-check each cycle |
| bboost | GW1–19 | **GW19** | provisional | Last set-1 GW; needs GK2 and DEF5 repaired first |

One chip per GW ✓ (GW8 wildcard, GW9 3xc are distinct GWs); freehit
non-consecutive ✓; all earmarks inside their windows ✓. `chip_plan` is a
forecast; nothing here activates a chip.

## 9. Retro-correction compliance

| C# | Rule | Applied |
|---|---|---|
| C5 | TC on fixture-independent EP, never on a promoted-club rating | GW4 fails (λ_att 1.80); GW7 rejected as banded; earmark → GW9 band-free |
| C8 | bench near-ties (≤ 0.25) on DefCon floor share | no bench pair inside 0.25; order by EP |
| C14 | gross gain on prior-only as well as blend; never a hit whose sign flips | every table in §1–§2 carries both; four of the five +4 pairs flip → none taken; no move clears 2.0 on both |
| C15 | restructure conditions (a), (b) = NO; (c) = C14 is the gate | pair scores +3.33 / −1.91, below 6 on both — closed |
| C16 | certainty multiplier on the captain choice only | §5 only; §4 and §6 use undiscounted EP |
| C4 residual (A2) | no selected player's single largest defensive term from COV/HUL/IPS | Richards: IPS(H) 0.29 ties NEW(H) 0.29 band-free. Tarkowski's HUL(A) GW6 0.39 and Thiaw's HUL(H) GW5 0.42 are their largest rows, but neither is selected on them: both are GW3 holds kept because no swap clears the transfer gate (Tarkowski → Calafiori +0.79 / +0.39), and Tarkowski's GW4 XI slot is TOT(A) 0.31, band-free |

## 10. Risks and freshness-gate list

| Id | Sev | Risk | Disposition |
|---|---|---|---|
| R1 | MED | MCI 3-cap with the captain on the same fixture: Haaland (C) and Ndiaye in the XI, Anderson bench 13, all at MUN (A) | accepted; Ndiaye's DefCon 30 is a floor; P(CS) 0.25 not relied on |
| R2 | MED | Derby cross-exposure: Mbeumo (MUN) starts against Haaland/Ndiaye; Shaw (MUN) bench | internal hedge, no action |
| R3 | MED | Template: João Pedro 73.2%, Calafiori 48.7%, B.Fernandes 48.6% unheld | priced in §2; each < 2 on both readings |
| R4 | LOW | Shaw 75% unspecified (news 11 Sep 13:00) | bench 15; freshness gate re-checks status/news at final |
| R5 | LOW | Dead GK2 leaks ≈ 0.18 EP/GW (4% Raya non-start × ~3.7) | no £4.0 playing GK; GW5 two-FT window or wildcard |
| R6 | LOW | EVE (Tarkowski, Barry) turn bad from GW7 — ARS(A) λ_att 0.77 | GW4–6 hold; GW8 wildcard covers; GW7 XI already drops Barry |
| R7 | LOW | Barry/Anderson and Richards/Thiaw boundaries flip on prior-only rates | logged §4; both inside model noise |

Freshness gate ids for the finalizer: 1, 4, 202, 229, 427, 237, 481, 68,
411, 106, 249, 497, 69, 445, 423. Snapshot 17:58 UTC 11 Sep → < 24h at the
12:30 UTC deadline.

## 11. GW5 earmarks (re-derived next cycle — not commitments)

- Two free transfers. Candidate that clears 2.0 on both readings today:
  Anderson + Thiago → Cherki + Wissa (+5.06 / +3.46, bank 0.2 after). Any
  single that clears 2.0 on both readings is also eligible; none does today.
- GK2: a playing £4.0–4.5 GK needs +0.5 of headroom; pair with the above
  only if the bank allows.
- 3xc GW9 earmark: re-test Haaland's BHA(H) row against SUN(H) each cycle;
  revert to GW5 only if the edge closes before the GW5 deadline.
- S1 (standing): the GW5 midfield move above is how it is honoured; Ndiaye's
  half stays unsupported while he keeps 88+ minutes.

## Suggestions

Read data/suggestions.md through S2

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 4 | standing | EP6 +0.00 this GW (FT banked either way); Anderson is the target: best single Anderson→Stach +1.38 blend / −2.85 prior fails the 2.0 gate on both readings, so honoured by banking to 2 FTs for a GW5 upgrade (Anderson+Thiago→Cherki+Wissa +5.06 / +3.46 clears free); broke the 0.02 Barry v Anderson XI tie toward Barry; the Ndiaye half is unsupported — 266 of 270 minutes, EP6 25.40 third of five MIDs, best Ndiaye swap −0.07 |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |

## STATE

```yaml
# Convention (as GW2/GW3): free_transfers_banked = free transfers available
# at the NEXT (GW5) deadline. This GW's FT is banked (1 + 1 accrued = 2).
# team_value = live my-team selling prices Σ 99.4 + bank 0.0 (authenticated
# read 2026-09-11 ~18:10 UTC, fifteen rows summed; the relayed total of 99.6
# does not match its own rows — finalizer to reconcile against my-team).
# Supersedes GW3's paper 99.9. No transfer, so both values are unchanged by
# this decision.
gw: 4
team_id: 8455344
team_value: 99.4
bank: 0.0
free_transfers_banked: 2
chip: null
chips_used: []
transfers_made: []
chip_plan:
  - {chip: 3xc, gw: 9, status: provisional}
  - {chip: wildcard, gw: 8, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 1, name: Raya, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: false, vice: true}
  - {id: 229, name: Tarkowski, position: 3, captain: false, vice: false}
  - {id: 202, name: Richards, position: 4, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 5, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 6, captain: false, vice: false}
  - {id: 69, name: Scott, position: 7, captain: false, vice: false}
  - {id: 237, name: Ndiaye, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: true, vice: false}
  - {id: 106, name: Thiago, position: 10, captain: false, vice: false}
  - {id: 249, name: Barry, position: 11, captain: false, vice: false}
  - {id: 497, name: Dubravka, position: 12, captain: false, vice: false}
  - {id: 481, name: Anderson, position: 13, captain: false, vice: false}
  - {id: 445, name: Thiaw, position: 14, captain: false, vice: false}
  - {id: 423, name: Shaw, position: 15, captain: false, vice: false}
```
