# GW11 fixture analysis (window GW11–16)

Numbers come from `uv run python -m fpl fixtures-rate --gw 11` and
`data/analysis/gw11/fixtures-tables.md`. Run summary: 10 rounds, 100 matches,
478 summaries, 27 player-rounds (1.41 xG) recovered from event-live; clipped
129 of 400 implied ratings (round 10: 15 of 40); league xG per match home 1.58,
away 1.36, total 2.95 vs base 2.87 (+2.7%); window gw11–16: 120 rows, blanks:
none, doubles: none, unscheduled fixtures: 0.

## Headline

- **Best attacking run:** MCI, ATT rank 1, Σλ_att 11.44 (FUL(H) 2.06 /
  ARS(A) 1.21 / LEE(H) 1.82 / BRE(A) 1.87 / CHE(H) 2.17 / HUL(H) 2.31 ±).
  BHA is ATT rank 2 (Σ 10.43), LIV ATT rank 3 (Σ 9.77).
- **Best defensive run:** ARS, CS rank 1, ΣP(CS) 2.20, every GW between 0.30
  and 0.41, none of them banded. BOU is CS rank 2 (Σ 2.01), TOT CS rank 3
  (Σ 1.85).
- **Worst combined run:** HUL — ATT rank 20 (Σ 5.76) and CS rank 19
  (Σ 1.09), all six rows banded. NEW is CS rank 20 (Σ 1.06) with ATT rank 16;
  COV is ATT rank 19 (Σ 6.68) with CS rank 16.
- **Largest swings (GW14–16 minus GW11–13):** MCI turns easy from GW14
  (Δ Σλ_att +1.26); TOT turns hard from GW14 (Δ Σλ_att −0.90, Δ ΣP(CS)
  −0.11); SUN turns easy from GW14 (+0.79).
- **Blanks and doubles:** none in GW11–16.

## What changed

The Δ columns are the moves since GW10, so each is driven by round 10.
Largest moves (±0.05 is the largest on either rating this week):

| Club | Rating | Now | Δ | Rating rank | Round-10 match that drove it |
|---|---|---:|---:|---:|---|
| MUN | ATT | 1.06 | +0.05 | 7 | AVL(H): xG 3.55, impATT 1.80* |
| SUN | ATT | 0.98 | +0.05 | 12 | CHE(H): xG 2.38, impATT 1.72 |
| AVL | ATT | 0.97 | +0.05 | 13 | MUN(A): xG 2.92, impATT 1.80* |
| ARS | ATT | 1.14 | -0.05 | 3 | HUL(H): xG 1.27, impATT 0.61 |
| CHE | ATT | 1.11 | -0.05 | 6 | SUN(A): xG 0.65, impATT 0.55* |
| CHE | DEFW | 1.05 | +0.05 | 12 | SUN(A): xGA 2.38, impDEFW 1.80* |
| AVL | DEFW | 1.09 | +0.05 | 14 | MUN(A): xGA 3.55, impDEFW 1.80* |
| SUN | DEFW | 1.01 | -0.05 | 10 | CHE(H): xGA 0.65, impDEFW 0.55* |
| NEW | DEFW | 1.16 | -0.05 | 18 | FUL(A): xGA 0.69, impDEFW 0.60 |
| HUL | DEFW | 1.12 | -0.05 | 16 | ARS(A): xGA 1.27, impDEFW 0.64 |

Next tier (±0.04): LIV ATT 1.12 +0.04 and DEFW 0.88 +0.04 (CRY(A): xG
2.64 impATT 1.80*, xGA 2.62 impDEFW 1.49); CRY ATT 1.06 +0.04 (LIV(H): xG
2.62, impATT 1.80*); MUN DEFW 1.12 +0.04 (AVL(H): xGA 2.92, impDEFW 1.80*);
BHA DEFW 0.92 −0.04 (BRE(H): xGA 0.58, impDEFW 0.55*).

MUN 3.55–2.92 AVL and CHE–SUN are one match each. All four MUN–AVL implied
values are clipped (1.80*), and three of the four CHE–SUN values (1.80* or
0.55*). No rating moved more than 0.05; read these as direction, not level.

## Corrections applied

- **C12 — A2 — active — untested.** Make the promoted-club ±15pp band
  two-sided: it applies to the non-promoted side's attacking terms as well as
  to P(CS), and the band never shrinks the central attacking estimate of a
  player facing a promoted club. Applied this gameweek:
  - Two-sided: every row involving COV, HUL or IPS carries the `±` marker
    in both the Attack ticker and the Defence ticker (e.g. BHA HUL(A) 1.73 ±
    and 0.36 ±; MCI HUL(H) 2.31 ± and 0.43 ±). banded rows: 34.
  - Central estimates unchanged: the λ_att values against promoted clubs
    are quoted as the model prints them, not discounted. MCI v HUL(H) GW16
    λ_att 2.31 and BHA v IPS(H) GW16 λ_att 2.20 stand as central estimates
    with a ±15pp band either side; nothing here marks them down.
  - Defensive side, C4's surviving clause: a banded P(CS) may not be a
    selected player's single largest EP term. The rows at risk are those in
    the `## Promoted band` table of `fixtures-tables.md` (P(CS) ≥ 0.30); see
    that table for the full list. The optimizer applies the prohibition;
    A2 only flags the rows.
  - GW10 follow-up: the GW10 retro reports ARS v HUL (H), the banded fixture
    behind the captaincy, kept a clean sheet (Gabriel 8, dc 10), and that
    whether it was the largest term stays unauditable until C17 ships.
    Status stays untested.
- **C4 — A2 — revised, see C12.** No separate application; its defensive
  prohibition is carried inside C12 above.
- **C5 — A2, A4 — retired — satisfied.** No action.

## Promoted clubs

COV, HUL and IPS ratings are an ASSUMPTION, uncertainty HIGH, and stay banded
until a retro correction releases the band (not A2's call). All three have
n = 10 matches, so the ratings are mostly data now, but the priors they
blend from were assumptions with almost no prior-season squad coverage
(HUL 0.03, COV 0.13, IPS 0.39).

| Club | ATT | ATT rating rank | DEFW | DEFW rating rank | clips | Note |
|---|---:|---:|---:|---:|---:|---|
| IPS | 0.92 | 15 | 1.23 | 19 | 6 | Attack well above its 0.70 prior; defence near its 1.26 prior |
| COV | 0.72 | 19 | 1.10 | 15 | 5 | Defence has improved from its 1.30 prior |
| HUL | 0.72 | 19 | 1.12 | 16 | 6 | DEFW −0.05 this week after ARS(A) xGA 1.27 |

The promoted clubs no longer rank as a defensive block: COV (DEFW rank 15)
and HUL (16) sit beside MUN (16), and CRY (DEFW rank 20) is weaker than all
three. The band reflects how uncertain these ratings are, not that the
clubs are weakest.

## FDR vs model

Every club whose FDR rank is 5 or more places from its ATT rank or CS rank.
FDR rates only the opponent; the model's ranks also carry the club's own
ATT (attack) and DEFW (clean sheets) and the home/away base. Most gaps come
from that.

| Club | FDR rank | ATT rank | CS rank | Why they differ |
|---|---:|---:|---:|---|
| AVL | 1 | 8 | 10 | Easiest FDR run, but own ATT 0.97 (rank 13) and DEFW 1.09 (rank 14) are mid-table |
| CRY | 3 | 5 | 18 | Own DEFW 1.25 is rating rank 20; easy opponents do not rescue the clean-sheet line |
| TOT | 4 | 17 | 3 | Own ATT 0.84 (rank 17) caps the attack; own DEFW 0.87 (rank 4) lifts clean sheets |
| COV | 5 | 19 | 16 | Promoted; own ATT 0.72 (rank 19) and DEFW 1.10 (rank 15) |
| SUN | 7 | 13 | 9 | Own ATT 0.98 (rank 12) trails the FDR; three away games in GW11–14 |
| IPS | 8 | 14 | 17 | Promoted; own DEFW 1.23 (rank 19) |
| CHE | 9 | 6 | 14 | Own DEFW 1.05 (rank 12), and GW15 MCI(A) P(CS) 0.11 |
| BOU | 10 | 7 | 2 | Own DEFW 0.85 (rank 3) plus two banded home games (HUL, COV) |
| NEW | 14 | 16 | 20 | Own DEFW 1.16 (rank 18) |
| MCI | 15 | 1 | 4 | FDR omits MCI's own ATT 1.34 (rank 1) and DEFW 0.88 (rank 5) |
| ARS | 16 | 4 | 1 | FDR omits ARS's own DEFW 0.68 (rank 1) and ATT 1.14 (rank 3) |
| BRE | 17 | 10 | 11 | Four home games; EVE, MUN and NEW defences (DEFW 1.02, 1.12, 1.16) are weaker in the model than their FDR |
| NFO | 18 | 12 | 5 | Own DEFW 0.84 (rank 2) |
| FUL | 19 | 18 | 12 | Opponent attacks TOT 0.84, EVE 0.94, LEE 0.99 are weaker in the model than FDR assumes |

## Swings

Top 5 rows of the Swings table (Δ = GW14–16 minus GW11–13):

- MCI turns easy from GW14 (Δ Σλ_att +1.26, Δ ΣP(CS) +0.07). GW12 ARS(A) 1.21 / 0.21 is the hard week before it.
- TOT turns hard from GW14 (Δ Σλ_att −0.90, Δ ΣP(CS) −0.11): ARS(H) 0.88, HUL(A) 1.25 ±, LIV(A) 0.98.
- SUN turns easy from GW14 for attack (Δ Σλ_att +0.79, Δ ΣP(CS) +0.05), ending CRY(H) 1.89.
- LIV turns hard from GW14 for attack (Δ Σλ_att −0.61); clean sheets level (Δ ΣP(CS) +0.02).
- COV turns hard from GW14 (Δ Σλ_att −0.50, Δ ΣP(CS) −0.10); every row banded.

## Blanks and doubles

- GW11–16: blanks: none; doubles: none; unscheduled fixtures: 0.
- No GW in this window offers a blank or double for set-1 Bench Boost or Free
  Hit. Set 1 expires at the GW19 deadline, beyond this window.

## Uncertainty flags

- **Promoted clubs:** COV, HUL, IPS — ASSUMPTION, HIGH, banded (34 banded
  rows). See `## Promoted band` in `fixtures-tables.md`.
- **Thin samples:** none; every club has n = 10.
- **Heavy clipping:** 129 of 400 implied ratings clipped (round 10: 15 of
  40). Most clipped: TOT 10, NFO 9, AVL 9, CHE 8, SUN 8. TOT's attack has
  two implied values above 1.07 (r6 MUN(A) 1.40, r9 CRY(H) 1.80*), and NFO's
  attack rests on three 1.80* rounds.
- **Single-match moves:** MUN ATT/DEFW and AVL ATT/DEFW this week rest on one
  3.55–2.92 xG match, both sides clipped.
- **League scoring above base:** total 2.95 vs base 2.87 (+2.7%), so model
  λ values may run slightly low across the board.
- **Congested schedules / cup involvement:** not visible in this analyst's
  inputs; the player analyst should weigh European and cup minutes for the
  clubs involved.

## Scheduled checks

- GW12: confirm MCI turns easy from GW14 (Δ Σλ_att +1.26) and TOT turns hard from GW14 (−0.90) still hold after round 11, before transfers aimed at GW14–16.
- GW12: check whether CRY DEFW (1.25, +0.02, rating rank 20) holds after r11 COV(A).
- GW12: check whether MUN ATT (1.06, +0.05) and AVL DEFW (1.09, +0.05) hold after round 11; both moved on one clipped match (r10 MUN–AVL).
- GW12: check whether SUN ATT (0.98, +0.05) holds after r11 AVL(A).
- GW12: GW11 banded clean-sheet rows BHA v HUL (A) 0.36 ± and TOT v IPS (H) 0.35 ±; in the GW11 retro, check whether either was a selected player's largest defensive EP term (C12; unauditable until C17 ships).
