# GW7 fixture analysis (window GW7–12)

Numbers from `uv run python -m fpl fixtures-rate --gw 7` and
`data/analysis/gw7/fixtures-tables.md`. Ratings: 6 rounds, 60 matches.

## Headline
- Best attacking run: MCI, ATT rank 1, Σλ_att 11.21 (IPS(H) 2.33 ± in GW7,
  BHA(H) 2.09 in GW9, FUL(H) 2.17 in GW11). ARS ATT rank 2, Σ 10.38.
- Best defensive run: ARS, CS rank 1, ΣP(CS) 2.20, peaking at HUL(H) 0.50 ± in
  GW10. MCI CS rank 2, Σ 1.81.
- Worst combined run: HUL, ATT rank 20 (Σ 6.45) and CS rank 20 (Σ 1.05).
  COV ATT rank 19 / CS rank 18 and NEW ATT rank 18 / CS rank 19 close behind.
- Largest swings (GW10–12 v GW7–9): MCI −1.21 Σλ_att, ARS +0.90, BHA +0.88
  (with +0.30 ΣP(CS)), NEW −0.70.
- Blanks: none. Doubles: none.

## What changed
Largest rating moves since GW6 (Δ columns), with the round-6 match behind each
(implied-ratings table):

| Club | Move | Driving match (r6) |
|---|---|---|
| NFO | ATT +0.07 (1.03), DEFW +0.05 (0.89) | CRY(A): xG 3.34, impATT 1.80*; xGA 2.59, impDEFW 1.48 |
| IPS | DEFW +0.07 (1.14) | FUL(H): xGA 1.82, impDEFW 1.80* |
| CRY | DEFW +0.06 (1.16), ATT +0.05 (1.08) | NFO(H): xGA 3.34, impDEFW 1.80*; xG 2.59, impATT 1.68 |
| BHA | DEFW −0.06 (1.02) | SUN(A): xGA 0.72, impDEFW 0.59 |
| MUN | ATT −0.05 (1.04) | TOT(H): xG 0.80, impATT 0.55* |
| TOT | ATT +0.05 (0.82), DEFW −0.05 (0.89) | MUN(A): xG 1.62, impATT 1.40; xGA 0.80, impDEFW 0.55* |
| AVL | ATT +0.05 (0.89), DEFW −0.05 (1.01) | BRE(H): xG 2.33, impATT 1.53; xGA 1.07, impDEFW 0.66 |
| BOU | DEFW −0.05 (0.88) | CHE(A): xGA 1.09, impDEFW 0.55* |

CRY v NFO (3.34 v 2.59 xG) drives four of these moves:
both clubs' attack ratings rose and both defence ratings worsened.

## Corrections applied
- **C4 — revised, see C12.** Not applied on its own; its defensive-term
  prohibition lives on inside C12.
- **C5 — active.** The GW9 Triple Captain earmark is judged on Haaland's own
  EP, never on a promoted club's defensive rating. MCI's GW9 fixture is BHA(H),
  λ_att 2.09, not a banded row, so the earmark does not lean on a promoted
  rating. MCI's GW7 fixture IPS(H), λ_att 2.33, IS banded (±): under C5, a case for moving the chip to GW7 must stand without IPS's
  DEFW 1.14. The optimizer decides; A2 only reports.
- **C12 — active.** The ±15pp band is two-sided: the tickers mark every row
  involving IPS, COV or HUL with ± on both the attack and the defence side
  (banded rows: 34). The central λ_att against a promoted club is left as
  printed — the band never shrinks it. C4's prohibition stands for defensive
  terms only: a promoted-club P(CS) must not be a selected player's single
  largest EP term. The defensive rows it bites on most are those in the
  `## Promoted band` table of `fixtures-tables.md` (P(CS) ≥ 0.30), all of
  them: GW10 ARS v HUL (H) 0.50; GW7 TOT v COV (H) 0.41; GW12 LEE v COV (H)
  0.39; GW10 EVE v COV (H) 0.37; GW7 MCI v IPS (H) 0.36; GW7 FUL v HUL (H)
  0.35; GW11 TOT v IPS (H) 0.34; GW8 BRE v HUL (A) 0.33; GW12 CRY v HUL (H)
  0.32; GW11 BHA v HUL (A) 0.31; GW8 FUL v COV (A) 0.30; GW9 SUN v COV (A)
  0.30.

## Promoted clubs
IPS, COV and HUL ratings are an ASSUMPTION, uncertainty HIGH, and stay banded
until a retro correction releases the band.

| Club | ATT prior → now | DEFW prior → now | Read |
|---|---|---|---|
| IPS | 0.70 → 0.92 (rank 14) | 1.26 → 1.14 (rank 16) | attack well above prior; DEFW worsened +0.07 this round after FUL(H) |
| COV | 0.68 → 0.74 (rank 19) | 1.30 → 1.14 (rank 16) | near prior in attack; defence better than assumed |
| HUL | 0.62 → 0.74 (rank 19) | 1.36 → 1.16 (rank 18) | weakest combined run in the window |

All three defend better than their priors assumed; that is why so few banded
defensive rows clear P(CS) 0.30.

## FDR vs model
FDR rates only the opponent; the model's ranks multiply the club's own rating
by the opponent's. Every club 5+ places apart:

| Club | FDR rank | ATT rank | CS rank | Why they differ |
|---|---:|---:|---:|---|
| TOT | 1 | 16 | 4 | easy opponents (COV, IPS, LEE, SUN), but own ATT 0.82 (rank 18) caps λ_att; DEFW 0.89 keeps CS close to FDR |
| COV | 2 | 19 | 18 | easy-looking schedule, but COV's own ATT 0.74 and DEFW 1.14 are near the bottom |
| SUN | 3 | 12 | 9 | mid-table own ratings (ATT 0.97, DEFW 1.05) dilute an easy schedule |
| CRY | 5 | 5 | 12 | DEFW 1.16 (rank 18) drags CS well below the FDR read |
| CHE | 6 | 6 | 14 | DEFW 1.08 (rank 15) — CHE concede more than FDR's opponent view implies |
| AVL | 9 | 14 | 10 | own ATT 0.89 (rank 15) below what the schedule offers |
| FUL | 10 | 15 | 8 | own ATT 0.89 (rank 15); GW11 MCI(A) 0.99 drags the run |
| ARS | 11 | 2 | 1 | own ATT 1.22 and DEFW 0.71 (rank 1) beat average opposition |
| BHA | 12 | 3 | 15 | ATT 1.12 (rank 5) outscores the FDR; DEFW 1.02 matches it |
| HUL | 14 | 20 | 20 | weakest own ratings in both directions |
| BRE | 15 | 4 | 7 | ATT 1.15 (rank 3) and HUL(A) in GW8 beat a hard FDR |
| LIV | 16 | 7 | 6 | DEFW 0.85 (rank 3) and ATT 1.09 outweigh hard opponents |
| MUN | 17 | 10 | 16 | ATT 1.04 lifts the attack read; DEFW 1.02 matches FDR |
| NFO | 18 | 11 | 11 | ATT 1.03 and DEFW 0.89 (rank 5) better than FDR's hard read |
| EVE | 20 | 13 | 13 | COV(H) in GW10 and mid ratings soften the hardest FDR run |

## Swings
Top 5 rows of the Swings table:
- MCI turns hard from GW10 (Δ Σλ_att −1.21, Δ ΣP(CS) −0.13: NFO(A), FUL(H),
  ARS(A) after IPS(H), AVL(A), BHA(H)).
- BHA turns easy from GW10 (+0.88 / +0.30: BRE(H), HUL(A) ±, NEW(H) after
  CRY(H), LIV(A), MCI(A)).
- ARS turns easy from GW10 (+0.90 / +0.14: HUL(H) ±, NEW(A), MCI(H)).
- NEW turns hard from GW10 (−0.70 / −0.14: FUL(A), ARS(H), BHA(A)).
- LIV turns easy from GW10 (+0.56 / +0.09: CRY(A), MUN(H), EVE(A) after
  BRE(A), BHA(H), ARS(H)).

## Blanks and doubles
None in GW7–12: blanks none, doubles none, unscheduled fixtures 0. No chip
timing driven by fixture count inside this window.

## Uncertainty flags
- Promoted clubs IPS, COV, HUL: ASSUMPTION ratings, HIGH, 34 banded rows.
- Heavy clipping: 73 of 240 implied ratings clipped (round 6: 9 of 40). Most
  clips: NFO 7; BRE, AVL, TOT 5 each. NFO's attack rests on five clipped
  rounds of six (1.80* three times, 0.55* twice) — its ATT 1.03 is noisy.
- League scoring above base: xG per match 3.07 against base 2.87 (+6.8%), so
  absolute λ values sit low across all clubs; ranks are unaffected.
- Thin samples: n = 6 for every club; priors still carry most of the weight
  (k = 5.7 attack, 4.0 defence; 4.0 / 3.0 for promoted clubs).
- Congested schedules and cup involvement: not visible in the inputs; no flag
  raised.

## Scheduled checks
- GW8: re-read CRY's DEFW (1.16) and NFO's ATT (1.03) — both moved on one
  match (CRY v NFO, r6); confirm whether the move holds.
- GW8: check the GW7 retro's C12 status for the banded GW7 rows (MCI v IPS,
  TOT v COV, FUL v HUL).
- GW9: before the GW9 Triple Captain, confirm MCI v BHA (H) λ_att still leads
  the GW9 detail table and is not banded (C5).
- GW10: confirm the MCI-hard / ARS-, BHA-, LIV-easy swing still holds before
  transfers that target GW10–12.
- GW10: ARS v HUL (H) P(CS) 0.50 heads the Promoted band table — re-check it
  is not a selected player's largest EP term (C12 defensive rule).
