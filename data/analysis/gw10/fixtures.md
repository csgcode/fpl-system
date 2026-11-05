# GW10 fixture analysis (window GW10–15)

Numbers are quoted from `fpl fixtures-rate --gw 10` and `data/analysis/gw10/fixtures-tables.md`. Ratings: 9 rounds, 90 matches; clipped 114 of 360 implied ratings (round 9: 15 of 40); league xG per match home 1.56, away 1.36, total 2.91 vs base 2.87 (+1.5%).

## Headline
- Best attacking run: MCI, ATT rank 1, Σλ_att 10.69 (NFO(A) 1.51, FUL(H) 2.12, ARS(A) 1.26, LEE(H) 1.87, BRE(A) 1.85, CHE(H) 2.08). ARS ATT rank 2 (10.21), BHA ATT rank 3 (10.07).
- Best defensive run: ARS, CS rank 1, ΣP(CS) 2.23, opening HUL(H) 0.50 ± — a banded row (see § Promoted clubs). TOT CS rank 2 (1.92), BOU CS rank 3 (1.87).
- Worst combined run: HUL (ATT rank 20, Σ 5.74; CS rank 19, Σ 1.04) and NEW (ATT rank 18, Σ 7.34; CS rank 20, Σ 1.04).
- Largest swings (Δ = GW13–15 minus GW10–12): BHA −1.43 λ_att / −0.23 P(CS) and ARS −1.21 / −0.13 turn hard; NEW +1.02 / +0.14 and MCI +0.91 / +0.02 turn easy.
- Blanks: none. Doubles: none. Unscheduled fixtures: 0.

## What changed
Rating moves since GW9 (Δ columns of the Ratings table) and the round-9 match behind each:

| Club | Rating | Now | Δ | Round-9 driver (implied-ratings table) |
|---|---|---:|---:|---|
| TOT | ATT | 0.86 | +0.07 | CRY(H): xG 3.46, impATT 1.80* |
| EVE | ATT | 0.96 | +0.06 | NEW(A): xG 2.44, impATT 1.80* |
| FUL | ATT | 0.92 | +0.06 | AVL(A): xG 2.33, impATT 1.80* |
| CHE | ATT | 1.16 | +0.05 | MUN(H): xG 3.00, impATT 1.80* |
| BRE | ATT | 1.08 | -0.04 | NFO(H): xG 0.45, impATT 0.55* |
| AVL | DEFW | 1.04 | +0.06 | FUL(H): xGA 2.33, impDEFW 1.80* |
| CRY | DEFW | 1.23 | +0.05 | TOT(A): xGA 3.46, impDEFW 1.80* |
| COV | DEFW | 1.12 | +0.05 | SUN(H): xGA 1.83, impDEFW 1.74 |
| NEW | DEFW | 1.21 | +0.04 | EVE(H): xGA 2.44, impDEFW 1.80* |
| IPS | DEFW | 1.22 | -0.03 | HUL(A): xGA 0.78, impDEFW 0.82 |
| SUN | DEFW | 1.06 | -0.03 | COV(A): xGA 0.69, impDEFW 0.66 |

DEFW up = weaker defence. CRY's DEFW 1.23 now holds DEFW rating rank 20, below both promoted clubs IPS (19) and HUL (17); CRY's round-9 xG was 0.15 at TOT (impATT 0.55*).

Last week's scheduled checks, resolved:
- BOU ATT did not hold: 1.13, Δ −0.03, after round 9 LEE(H) xG 1.28, impATT 0.81.
- IPS DEFW rise did not hold: 1.22, Δ −0.03 (round 9 HUL(A) impDEFW 0.82). BRE DEFW rise did not hold: 1.03, Δ −0.02 (round 9 NFO(H) impDEFW 0.71).
- ARS v HUL (H): see § Corrections applied.
- The GW11 swing check carries forward (§ Scheduled checks).

## Corrections applied
- **C12 — A2, active — untested.** The ±15pp promoted-club band is two-sided: it applies to P(CS) and to the non-promoted side's attacking terms on every banded row, and it never shrinks the central λ_att of a player facing a promoted club. This gameweek: banded rows: 34 (marked ± in the tickers and detail tables); central λ and P(CS) are quoted unshaded. Rows with P(CS) ≥ 0.30 are the `## Promoted band` table in `fixtures-tables.md`, every row: GW10 ARS v HUL (H) 0.50; GW14 BOU v HUL (H) 0.44; GW12 LEE v COV (H) 0.43; GW10 EVE v COV (H) 0.39; GW13 NFO v HUL (A) 0.38; GW15 TOT v HUL (A) 0.38; GW14 MUN v COV (H) 0.36; GW11 TOT v IPS (H) 0.35; GW11 BHA v HUL (A) 0.34; GW14 LEE v IPS (H) 0.32; GW15 AVL v COV (A) 0.32; GW10 BOU v IPS (A) 0.30; GW12 CRY v HUL (H) 0.30. ARS v HUL (H) 0.50 is this week's largest P(CS) in the window: downstream (A3/A4) must not let it be a selected ARS player's largest defensive EP term. The equivalent attacking row, ARS λ_att 2.14 v HUL, keeps its central value — C12 permits an attacking term to be the largest.
- **C4 — revised, see C12.** Carried by C12; no separate action.
- **C5** — retired (satisfied) at GW9; no action.

## Promoted clubs
IPS, HUL and COV. Every rating is an ASSUMPTION, uncertainty HIGH, blended with k = 4.0 (attack) and 3.0 (defence) on 9 matches each:
- IPS: ATT 0.94 (prior 0.70, rank 13), DEFW 1.22 (prior 1.26, rank 19).
- HUL: ATT 0.74 (prior 0.62, rank 19), DEFW 1.17 (prior 1.36, rank 17).
- COV: ATT 0.71 (prior 0.68, rank 20), DEFW 1.12 (prior 1.30, rank 16).

The promoted band stays on all their rows (banded rows: 34) until a retro correction releases it. All three have played well over 3 fixtures, C4's original release threshold, but C12 superseded C4 and has not released the band.

## FDR vs model
FDR rates only the opponent; the model also uses the club's own ATT and DEFW. Clubs 5+ places apart:

| Club | FDR rank | ATT rank | CS rank | Why they differ |
|---|---:|---:|---:|---|
| COV | 3 | 19 | 15 | Promoted; own ATT 0.71 (rank 20) and DEFW 1.12 (rank 16) blunt a soft schedule |
| TOT | 2 | 17 | 2 | Easy opponents but own ATT 0.86 (rank 17); defence (DEFW 0.85, rank 5) agrees with FDR |
| AVL | 1 | 9 | 10 | Easiest FDR run, but own ATT 0.92 (rank 15) and DEFW 1.04 (rank 13) are mid-to-low |
| NEW | 9 | 18 | 20 | Own ATT 0.85 (rank 18) and DEFW 1.21 (rank 18) |
| IPS | 7 | 14 | 16 | Promoted; DEFW 1.22 (rank 19) |
| CRY | 8 | 8 | 18 | DEFW 1.23 (rank 20) drags CS far below FDR |
| MUN | 6 | 7 | 11 | DEFW 1.08 (rank 15) |
| MCI | 14 | 1 | 8 | Hard FDR run (ARS, BRE, CHE) outweighed by ATT 1.35 (rank 1) |
| NFO | 18 | 10 | 5 | Hard FDR run; DEFW 0.84 (rank 3) keeps CS high |
| ARS | 10 | 2 | 1 | ATT 1.19 (rank 2), DEFW 0.70 (rank 1) beat a mid FDR run |
| BOU | 12 | 6 | 3 | DEFW 0.83 (rank 2), ATT 1.13 (rank 5) |
| LEE | 15 | 13 | 6 | DEFW 0.90 (rank 6) plus COV(H) and IPS(H) banded rows |
| BRE | 19 | 11 | 17 | ATT 1.08 (rank 6) lifts the attack ticker; DEFW 1.03 (rank 12) does not lift CS |
| CHE | 11 | 5 | 14 | ATT 1.16 (rank 3); DEFW 1.00 (rank 9) leaves CS close to FDR |

## Swings
Top 5 rows of the Swings table (Δ = GW13–15 minus GW10–12):
- BHA turns hard from GW13 (Δ Σλ_att −1.43, Δ ΣP(CS) −0.23).
- ARS turns hard from GW13 (−1.21, −0.13).
- NEW turns easy from GW13 (+1.02, +0.14).
- MCI turns easy from GW13 (+0.91, +0.02).
- MUN turns easy from GW13 (+0.67, +0.13).

## Blanks and doubles
None in GW10–15: blanks none, doubles none, unscheduled fixtures 0. No chip-driving blank or double in this window.

## Uncertainty flags
- Promoted clubs IPS, HUL, COV: ASSUMPTION, HIGH; 34 banded rows under C12's two-sided ±15pp band.
- Clipping: 114 of 360 implied ratings clipped (round 9: 15 of 40). Most clips per club: NFO 9, TOT 9; BOU, SUN, AVL 7 each. Every ATT move in § What changed (TOT, EVE, FUL, CHE at 1.80*; BRE at 0.55*) and the AVL, CRY and NEW DEFW moves (1.80*) rest on clipped round-9 values.
- Thin samples: none — every club n = 9.
- Data: 26 player-rounds (1.41 xG) recovered from event-live rather than summaries.
- Congested schedules / cup involvement: not visible in this agent's inputs; not assessed.

## Scheduled checks
- GW11: confirm the LEE-, MUN-, NFO-easy / ARS-, MCI-hard swing from GW12 still holds before transfers targeting GW12–14 (this week's table already shows MCI turning easy from GW13 and LEE's ΣP(CS) Δ −0.30).
- GW11: check whether CRY DEFW (1.23, +0.05, rank 20) holds after r10 LIV(H).
- GW11: check whether TOT ATT (0.86, +0.07 on a clipped 1.80*) holds after r10 LEE(A).
- GW11: ARS v NEW (A) P(CS) 0.40 is unbanded; re-check that ARS v HUL (H) 0.50 was not a selected player's largest defensive EP term in the GW10 retro (C12).
