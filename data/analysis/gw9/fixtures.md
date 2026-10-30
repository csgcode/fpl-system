# GW9 fixture analysis (window GW9–14)

Numbers from `uv run python -m fpl fixtures-rate --gw 9` and
`data/analysis/gw9/fixtures-tables.md`. Run summary: 8 rounds, 80 matches;
clipped 99 of 320 implied ratings (round 8: 14 of 40); league xG per match
home 1.56, away 1.37, total 2.93 vs base 2.87 (+2.0%); window gw9–14: 120
rows, blanks none, doubles none, unscheduled fixtures 0.

## Headline
- Best attacking run: MCI, ATT rank 1, Σλ_att 10.85 (BHA(H) 2.05, NFO(A)
  1.57, FUL(H) 2.11, ARS(A) 1.29, LEE(H) 1.92, BRE(A) 1.91). BOU is ATT rank
  2 (Σ 10.46) with FDR rank 1 (mean FDR 2.67); ARS ATT rank 3 (Σ 10.23).
- Best defensive run: ARS, CS rank 1, ΣP(CS) 2.18, led by HUL(H) 0.49 ± in
  GW10. BOU CS rank 2 (Σ 1.91), TOT CS rank 3 (Σ 1.80).
- BOU is ATT rank 2 and CS rank 2 — the best combined run in the window.
- Worst combined run: HUL, ATT rank 20 (Σ 6.38) and CS rank 20 (Σ 0.96),
  every row banded. NEW is CS rank 19 (Σ 1.18) and ATT rank 16; BRE has the
  hardest FDR run (mean 3.67, FDR rank 20) and CS rank 18.
- Largest swings (GW12–14 minus GW9–11): LEE +0.96 Σλ_att, MUN +0.81 / +0.21
  ΣP(CS), NFO +0.72 / +0.25 turn easier; ARS −0.65 / −0.18, MCI −0.61 /
  −0.13, TOT −0.69 turn harder.
- Blanks: none. Doubles: none. Unscheduled fixtures: 0.

## What changed
Largest rating moves since GW8 (Δ columns) and the round-8 match behind each
(implied-ratings table):

| Club | Rating | Now | Δ | Round-8 driver |
|---|---|---:|---:|---|
| IPS | DEFW | 1.25 (rank 20) | +0.07 | NFO(H): xGA 2.29, impDEFW 1.80* |
| BOU | ATT | 1.16 (rank 4) | +0.06 | MUN(A): xG 2.15, impATT 1.80* |
| BRE | DEFW | 1.05 (rank 13) | +0.06 | HUL(A): xGA 1.57, impDEFW 1.64 |
| MUN | DEFW | 1.06 (rank 14) | +0.05 | BOU(H): xGA 2.15, impDEFW 1.43 |
| HUL | ATT | 0.76 (rank 19) | +0.04 | BRE(H): xG 1.57, impATT 1.03 |
| NFO | ATT | 1.05 (rank 8) | +0.03 | IPS(A): xG 2.29, impATT 1.37 |
| LIV | DEFW | 0.86 (rank 3) | +0.03 | BHA(H): xGA 1.32, impDEFW 1.10 |
| CHE | ATT | 1.11 (rank 6) | −0.03 | TOT(H): xG 0.47, impATT 0.55* |
| CRY | DEFW | 1.18 (rank 19) | −0.03 | NEW(H): xGA 0.95, impDEFW 0.72 |
| SUN | DEFW | 1.09 (rank 16) | −0.03 | LEE(H): xGA 0.75, impDEFW 0.55* |
| COV | DEFW | 1.07 (rank 15) | −0.03 | FUL(H): xGA 0.55, impDEFW 0.55 |

Every move is ≤ 0.07; with n = 8 for all 20 clubs the ratings are settling.
BOU's ATT rise rests on two consecutive clipped 1.80* rounds (r7 SUN(H) 4.25
xG, r8 MUN(A) 2.15 xG). IPS DEFW is now the weakest in the league (rating
rank 20).

## Corrections applied
- **C5 — active.** Written for the GW3 Triple Captain; the principle carried
  forward is that a TC case must stand on the captain's own fixture, never
  on a promoted club's defensive rating. GW9's TC candidate fixture, MCI v
  BHA (H), is not banded and its λ_att 2.05 (att 10) heads the GW9 detail
  table. BHA DEFW 0.97 (rating rank 8) is an established-club rating on 8
  matches. Nothing in this fixture depends on a promoted-club rating, so C5
  does not block it from the fixture side; the EP case remains A4's.
- **C12 — active (untested).** The ±15pp band is applied two-sided: every
  row marked `±` in the Attack ticker carries it on λ_att as well as on
  P(CS), and the band never lowers the central estimate — the λ_att and
  P(CS) values printed are the central estimates and are quoted unchanged.
  The banded defensive rows with P(CS) ≥ 0.30 are listed in full in the
  `## Promoted band` table of `fixtures-tables.md` (banded rows in total:
  32). Under C12 the C4 prohibition stands for defensive terms only: no
  banded P(CS) row may be a selected player's single largest EP term. The
  largest banded attacking rows this window, which C12 says must not be
  shrunk: ARS v HUL (H) GW10 2.18, BOU v HUL (H) GW14 2.09, BOU v IPS (A)
  GW10 1.93, LEE v IPS (H) GW14 1.93, CRY v HUL (H) GW12 1.89 (all from the
  Attack ticker).
- **C4 — retired** (revised by C12); not applied.

## Promoted clubs
IPS, HUL and COV ratings remain an ASSUMPTION with uncertainty HIGH. All
three now have 8 played matches, but the band stays on their rows until a
retro correction releases it; that is not A2's decision.

| Club | ATT prior → now (rank) | DEFW prior → now (rank) |
|---|---|---|
| IPS | 0.70 → 0.97 (12) | 1.26 → 1.25 (20) |
| HUL | 0.62 → 0.76 (19) | 1.36 → 1.17 (17) |
| COV | 0.68 → 0.72 (20) | 1.30 → 1.07 (15) |

IPS's attack has run well above its prior; its defence is the league's
weakest by rating. HUL and COV defences have improved on their priors, so
fixtures against them are less generous than the GW1 assumption implied.

## FDR vs model
Clubs whose FDR rank is 5+ places from ATT rank or CS rank. FDR rates the
opponent only; the model also weighs the club's own ATT/DEFW, so gaps open
where a club's own strength is far from average.

| Club | FDR rank | ATT rank | CS rank | Why they differ |
|---|---:|---:|---:|---|
| AVL | 2 | 11 | 6 | Easy opponents, but own ATT rating rank 14 caps attacking returns. |
| IPS | 3 | 13 | 17 | Easy opponents, but own DEFW rating rank 20 sinks clean sheets; ATT rating rank 12 is mid-table. |
| TOT | 4 | 17 | 3 | Own ATT rating rank 18 limits goals; DEFW rating rank 5 agrees with the easy FDR on defence. |
| EVE | 5 | 14 | 7 | Own ATT rating rank 14 limits goals despite easy opponents. |
| COV | 6 | 19 | 15 | Own ATT rating rank 20 and DEFW rating rank 15 outweigh the easy run. |
| CRY | 7 | 10 | 16 | Own DEFW rating rank 19 wipes out the defensive value of the easy run. |
| SUN | 9 | 15 | 11 | Own ATT rating rank 13 below what FDR implies. |
| MCI | 10 | 1 | 9 | Own ATT rating rank 1 beats a middling FDR run. |
| ARS | 11 | 3 | 1 | Own ATT rating rank 2 and DEFW rating rank 1 beat a middling FDR run. |
| BHA | 12 | 4 | 13 | Own ATT rating rank 3 lifts attack; DEFW rating rank 8 keeps defence near FDR. |
| CHE | 13 | 5 | 14 | Own ATT rating rank 6 lifts attack above FDR. |
| NFO | 14 | 8 | 8 | Own DEFW rating rank 3 and ATT rating rank 8 beat FDR on both sides. |
| MUN | 15 | 9 | 12 | Own ATT rating rank 10 slightly above what the run implies. |
| FUL | 17 | 18 | 10 | Own DEFW rating rank 10 holds clean-sheet odds despite hard opponents. |
| LIV | 18 | 6 | 4 | Own ATT rating rank 7 and DEFW rating rank 3 beat a hard FDR run. |
| BRE | 20 | 7 | 18 | Own ATT rating rank 5 keeps attack good through the hardest FDR run; defence matches FDR. |

## Swings
Top 5 rows of the Swings table (Δ = GW12–14 minus GW9–11):
- LEE turns easy from GW12 (Δ Σλ_att +0.96, Δ ΣP(CS) +0.09).
- MUN turns easy from GW12 (+0.81, +0.21).
- NFO turns easy from GW12 (+0.72, +0.25).
- ARS turns hard from GW12 (−0.65, −0.18).
- MCI turns hard from GW12 (−0.61, −0.13).

## Blanks and doubles
None in GW9–14: blanks none, doubles none, unscheduled fixtures 0.

## Uncertainty flags
- Promoted clubs: IPS, HUL, COV — banded (32 rows), ASSUMPTION, HIGH.
- Clipping is heavy: 99 of 320 implied ratings (round 8: 14 of 40). Clubs at
  6+ in the clips column: NFO 8; SUN 7, TOT 7; MCI, BOU, IPS, AVL 6.
- BOU's ATT gain rests on two clipped rounds in a row (r7, r8).
- Sample: n = 8 for every club; no thin samples beyond that.
- League xG runs +2.0% above base (2.93 vs 2.87).
- Congested schedules and cup involvement: not visible in this step's
  inputs; none flagged.

## Scheduled checks
- GW10: ARS v HUL (H) P(CS) 0.49 heads the Promoted band table — re-check it is not a selected player's largest defensive EP term (C12).
- GW10: check whether BOU ATT (1.16, +0.06 on a second straight clipped round) holds after r9.
- GW10: check whether IPS DEFW (1.25, +0.07) and BRE DEFW (1.05, +0.06) rises hold after r9.
- GW11: confirm the LEE-, MUN-, NFO-easy / ARS-, MCI-hard swing from GW12 still holds before transfers targeting GW12–14.
