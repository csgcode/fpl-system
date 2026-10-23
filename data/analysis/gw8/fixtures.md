# GW8 fixture analysis (window GW8–13)

Numbers from `uv run python -m fpl fixtures-rate --gw 8` and
`data/analysis/gw8/fixtures-tables.md`. Run summary: 7 rounds, 70 matches;
clipped 85 of 280 implied ratings (round 7: 12 of 40); league xG per match
home 1.63, away 1.38, total 3.02 vs base 2.87 (+5.1%); window gw8–13, 120
rows, blanks: none, doubles: none, unscheduled fixtures: 0.

## Headline
- Best attacking run: MCI, ATT rank 1, Σλ_att 10.85 (AVL(A) 1.79, BHA(H)
  2.09, NFO(A) 1.59, FUL(H) 2.15, ARS(A) 1.29, LEE(H) 1.94). ARS ATT rank 2
  (10.40), CHE ATT rank 3 (10.09).
- Best defensive run: ARS, CS rank 1, ΣP(CS) 2.20, peaking at HUL(H) 0.51 in
  GW10 (banded). LIV CS rank 2 (1.79), BOU CS rank 3 (1.74).
- Worst combined run: HUL — ATT rank 20 (6.31) and CS rank 20 (1.03). NEW
  is next worst: ATT rank 18 (7.20), CS rank 19 (1.09), mean FDR 3.50.
- Largest swings (GW11–13 minus GW8–10): BHA +0.74 Σλ_att / +0.31 ΣP(CS)
  (turns easy); FUL −0.71 / −0.24 and SUN −0.66 / −0.03 (turn hard).
- Blanks: none. Doubles: none.

## What changed
Largest rating moves since GW7 (Δ columns) and the round-7 match behind each
(implied-ratings table):
- MCI DEFW +0.09 (0.93): IPS(H) r7, xGA 1.86, impDEFW 1.80* (clipped).
  MCI ATT also +0.04 (1.37) off 3.35 xG, impATT 1.73.
- BOU ATT +0.07 (1.10): SUN(H) r7, xG 4.25, impATT 1.80* (clipped).
- SUN DEFW +0.07 (1.12): same match, BOU(A) xGA 4.25, impDEFW 1.80*.
- IPS ATT +0.07 (0.99): MCI(A) r7, xG 1.86, impATT 1.75. IPS DEFW +0.04
  (1.18) off 3.35 xGA, impDEFW 1.56.
- CRY DEFW +0.05 (1.21, DEFW rating rank 20): BHA(A) r7, xGA 2.29,
  impDEFW 1.65.
- CHE DEFW −0.04 (1.04): EVE(A) r7, xGA 0.43, impDEFW 0.55*.
- FUL DEFW −0.04 (1.02): HUL(H) r7, xGA 0.16, impDEFW 0.55*.
- COV DEFW −0.04 (1.10): TOT(A) r7, xGA 0.87, impDEFW 0.68.

## Corrections applied
- **C4** — revised, see C12. Not applied separately.
- **C5** (A2, A4) — active. GW9 Triple Captain earmark: MCI v BHA (H)
  λ_att 2.09 still heads the GW9 detail table and is not banded (BHA is not
  promoted). The fixture supports, but must not carry, the case; the TC
  justification stays on Haaland's own fixture-independent EP (A4's call).
- **C12** (A2) — active, untested. Applied as follows: the ± band marks
  every row involving a promoted club (banded rows: 32), on both the attacking
  and the defensive side; central λ_att for a non-promoted club facing a
  promoted one is left as the command prints it, not shrunk. Defensive rule
  for A4: a promoted-club fixture must not be a selected player's largest
  defensive EP term. The rows at risk are the full `## Promoted band` table in
  `fixtures-tables.md` (P(CS) ≥ 0.30): ARS v HUL (H) GW10 0.51, LEE v COV (H)
  GW12 0.41, EVE v COV (H) GW10 0.38, NFO v HUL (A) GW13 0.38, BRE v HUL (A)
  GW8 0.33, BHA v HUL (A) GW11 0.33, FUL v COV (A) GW8 0.32, TOT v IPS (H)
  GW11 0.31, CRY v HUL (H) GW12 0.31.

## Promoted clubs
IPS, COV and HUL ratings are an ASSUMPTION, uncertainty HIGH. All three now
have n = 7 played matches (past C4's original 3-fixture threshold), but the
band stays on their rows until a retro correction releases it — that is not
A2's decision.
- IPS: ATT 0.99 (prior 0.70, ATT rating rank 12), DEFW 1.18 (prior 1.26,
  DEFW rating rank 19). Attack well above prior.
- COV: ATT 0.73 (prior 0.68, rank 19), DEFW 1.10 (prior 1.30, rank 15).
  Defence well better than prior.
- HUL: ATT 0.72 (prior 0.62, rank 20), DEFW 1.17 (prior 1.36, rank 17).

## FDR vs model
Clubs whose FDR rank is 5+ places from ATT rank or CS rank. FDR grades only
the opponents; the model also carries the club's own ATT/DEFW, so strong
clubs rank better on the model than on FDR and weak clubs worse.
- COV (FDR 1, ATT 19, CS 15): easiest FDR run (two promoted opponents plus
  FUL, SUN), but COV's own ATT 0.73 is rating rank 19.
- IPS (FDR 2, ATT 13, CS 14): six banded rows of soft fixtures; own DEFW 1.18
  (rank 19) drags CS rank.
- TOT (FDR 3, ATT 15): own ATT 0.80 (rank 18). CS rank 4 agrees with FDR —
  DEFW 0.89 (rank 5).
- CHE (FDR 4, CS 11): own DEFW 1.04 (rank 14).
- CRY (FDR 6, CS 17): own DEFW 1.21, DEFW rating rank 20.
- SUN (FDR 9, ATT 14, CS 18): DEFW 1.12 (rank 16), ATT 0.94 (rank 13), and
  GW13 LIV(A).
- HUL (FDR 14, ATT 20, CS 20): weakest ratings on both sides.
- MCI (FDR 10, ATT 1): ATT 1.37, rating rank 1.
- ARS (FDR 11, ATT 2, CS 1): ATT rank 2 and DEFW 0.71 (rank 1), plus HUL(H).
- LEE (FDR 12, CS 5): DEFW 0.92 (rank 6) with TOT(H) 0.38 and COV(H) 0.41.
- LIV (FDR 15, ATT 4, CS 2): DEFW 0.83 (rank 2), ATT 1.10 (rank 6).
- BHA (FDR 16, ATT 5): ATT 1.15 (rank 3) and HUL(A), NEW(H) in GW11–12.
- BRE (FDR 17, ATT 8, CS 10): ATT 1.12 (rank 5), HUL(A) in GW8.
- MUN (FDR 18, ATT 10): ATT 1.02 (rank 9); BRE(H), NEW(A) late in window.
- EVE (FDR 19, CS 12): COV(H) 0.38 in GW10 lifts its CS sum.

## Swings
Δ = GW11–13 minus GW8–10.
- BHA turns easy from GW11 (+0.74 Σλ_att, +0.31 ΣP(CS)): HUL(A), NEW(H),
  BOU(A) after LIV(A), MCI(A), BRE(H).
- FUL turns hard from GW11 (−0.71, −0.24): MCI(A), BOU(H), TOT(A).
- SUN turns hard from GW11 (−0.66, −0.03): AVL(A), TOT(H), LIV(A).
- LIV turns easy from GW11 (+0.42, +0.17): MUN(H), EVE(A), SUN(H) after
  BHA(H), ARS(H), CRY(A).
- NEW turns hard from GW11 (−0.46, −0.11): ARS(H), BHA(A), MUN(H).

## Blanks and doubles
None in GW8–13: blanks none, doubles none, unscheduled fixtures 0. No chip
timing signal from the schedule in this window.

## Uncertainty flags
- Promoted clubs IPS, COV, HUL: ASSUMPTION, HIGH; 32 banded rows.
- Heavy clipping: 85 of 280 implied ratings clipped (round 7: 12 of 40).
  Most clips: NFO 7, TOT 6; MCI, BRE, BOU, LIV, SUN, AVL 5 each. NFO's ATT
  1.02 rests on three clipped 1.80 rounds and two clipped 0.55 rounds.
- Round-7 extremes: BOU 4.25 xG v SUN (both sides clipped), MCI v IPS 3.35 /
  1.86 — single-match drivers of this week's largest Δs.
- League xG running +5.1% over base; λ values are built on the fixed base.
- Thin samples: n = 7 per club; still prior-weighted (k = 5.7 attack, 4.0
  defence).
- Congestion and cup involvement: not in this agent's inputs; not assessed.

## Scheduled checks
- GW9: before the GW9 Triple Captain, confirm MCI v BHA (H) λ_att still
  heads the GW9 detail table and is not banded (C5).
- GW9: re-read CRY's DEFW (1.21, rank 20) and MCI's DEFW (0.93) — both rose
  again in r7; confirm whether the moves hold.
- GW9: check whether SUN DEFW (+0.07) and BOU ATT (+0.07), driven by one
  clipped r7 match, hold after r8.
- GW10: ARS v HUL (H) P(CS) 0.51 heads the Promoted band table — re-check it
  is not a selected player's largest defensive EP term (C12).
- GW10: confirm the BHA- and LIV-easy / FUL-, SUN-, NEW-hard swing from GW11
  still holds before transfers targeting GW11–13.
