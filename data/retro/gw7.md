# GW7 Retro

## Squad

```
squad XI (captain doubled): predicted 54.85, actual 80; bench stranded 2
captain: Haaland 13 pts; hindsight best in XI: Haaland 13 (forgone 0)
squad rows (slot role id name pred act err start p_start min; * = |err| > 3):
    1 XI       1  Raya                 pred   3.34  act   9  err  +5.66* start Y  p_start 0.94  min  90
    2 XI     112  Van Hecke            pred   4.60  act   4  err  -0.60  start Y  p_start 0.92  min  90
    3 XI       4  Gabriel              pred   4.06  act   8  err  +3.94* start Y  p_start 0.92  min  90
    4 XI     229  Tarkowski            pred   3.79  act   0  err  -3.79* start Y  p_start 0.92  min  90
    5 XI     427  Mbeumo               pred   4.57  act   8  err  +3.43* start Y  p_start 0.93  min  90  VC
    6 XI     124  Groß                 pred   4.43  act   5  err  +0.56  start Y  p_start 0.93  min  70
    7 XI      68  Tavernier            pred   4.27  act  10  err  +5.73* start Y  p_start 0.90  min  78
    8 XI     542  E.Le Fée             pred   4.01  act   4  err  -0.01  start Y  p_start 0.92  min  90
    9 XI     411  Haaland              pred   6.58  act  13  err  +6.42* start Y  p_start 0.93  min  90  C
   10 XI     249  Barry                pred   4.58  act   2  err  -2.58  start Y  p_start 0.90  min  90
   11 XI     106  Thiago               pred   4.03  act   4  err  -0.03  start Y  p_start 0.92  min  90
   12 bench  497  Dubravka             pred   0.12  act   0  err  -0.12  start N  p_start 0.03  min   0
   13 bench  202  Richards             pred   3.09  act   2  err  -1.09  start Y  p_start 0.92  min  90
   14 bench   94  Schade               pred   2.76  act   0  err  -2.76  start N  p_start 0.65  min  45
   15 bench  423  Shaw                 pred   1.91  act   0  err  -1.91  start N  p_start 0.70  min   0
squad misses (|err| > 3): 1 Raya +5.66, 3 Gabriel +3.94, 4 Tarkowski -3.79, 5 Mbeumo +3.43, 7 Tavernier +5.73, 9 Haaland +6.42
```

Rank 5544586 → 4106307 (up 1438279). Team value 997 → 998 (+0.1m); 80 pts, 1 transfer, 2 on the bench.
`picks` for event 7 matches final.md's `picks:` on all 15 ids, captain 411 and vice 427; no chip. The ledger describes the fielded team.

## Misses

| id | name | pred | act | err | class | cause |
|---:|---|---:|---:|---:|---|---|
| 1 | Raya | 3.34 | 9 | +5.66 | VARIANCE | started, 90', 3 bonus (bps 29) on an ARS clean-sheet return |
| 4 | Gabriel | 4.06 | 8 | +3.94 | VARIANCE | started, 90', dc 12 cleared the DEF threshold alongside the ARS clean sheet |
| 229 | Tarkowski | 3.79 | 0 | -3.79 | VARIANCE | started, 90', dc 7 short of the threshold, bps 3 on goals conceded v CHE |
| 427 | Mbeumo | 4.57 | 8 | +3.43 | VARIANCE | started, 90', 1 goal off 0.65 xG plus 1 bonus |
| 68 | Tavernier | 4.27 | 10 | +5.73 | VARIANCE | started, 78', 1 goal off 1.19 xG plus 2 bonus — the chance volume was there; one round, no rate move |
| 411 | Haaland | 6.58 | 13 | +6.42 | VARIANCE | started, 90', 2 goals off 0.87 xG, 3 bonus (bps 71) |
| 156 | Neto | 3.36 | 15 | +11.64 | VARIANCE | 90', 2 goals off 0.37 xG — finishing, not process |
| 148 | Hato | 0.61 | 11 | +10.38 | MINUTES | 90' against p_start 0.22 |
| 379 | Isak | 0.77 | 9 | +8.23 | MINUTES | 78' against p_start 0.15 |
| 403 | Sávio | 4.62 | 0 | -4.62 | MINUTES | 0' against p_start 0.92 |
| 480 | Gibbs-White | 4.02 | 0 | -4.02 | MINUTES | 0' against p_start 0.93 |

## Captain and bench

Captain Haaland 13 pts was the hindsight best in the XI: forgone 0.
Bench stranded 2 (Richards started for his club, 2 pts on our bench); Schade came on as a substitute for 45' and 0, Shaw 0'.
No auto-sub was needed: every XI player played 70'+, so bench order cost nothing.
Bench gaps 0.328 (Richards v Schade) and 0.854 (Schade v Shaw) sit outside C8's 0.25 band; order verdict: sound.

## Findings

- XI predicted 54.85 v actual 80 (+25.15). All six squad misses are VARIANCE: five are positive conversions (goals over xG, clean sheets, bonus), and the one negative (Tarkowski) is a conceded-goals blank on a non-promoted fixture. No process correction is drawn from the squad.
- `predictions:` commit bacd40409de5, drift none — the scored files are the decision record.
- Minutes: expected starts 206.0 v actual 217, gap -11.0, Brier 0.1211 against cumulative 0.1179. This is the third consecutive round with actual starts above expected (−3.2, −11.0, −11.0) since C18 capped nominal starters at 0.90 at GW4, after three rounds of the opposite sign (+7.9, +8.9, +10.7). The trend rule is met: C18 has overshot. Revised as C21.
- The pool misses point both ways: low-p_start players who played 90'/78' (Hato 0.22, Isak 0.15) and top-band players who did not play at all (Sávio 0.92, Gibbs-White 0.93; also Cherki 0.70 at 0'). Which band carries the −11.0 is unattributable until C13 ships.
- gap: the pool under-/over-predicted rows print min and p_start but no start flag, so Isak's 78' (p_start 0.15) cannot be classed as a start or a substitute appearance, and the MINUTES class for pool rows cannot separate a missed start from a missed cameo.
- Danso (p_start 0.88, 16', −3, bps −19) is the round's largest over-prediction; one event, outside the row cap, no rule.
- Uncertainty tier: round 7 is the first round scored under the rate-risk-only tag. HIGH n=258 mae 0.99, MED n=73 1.98, LOW n=108 2.64 — one round only; no tier conclusion drawn, and pooled tier figures straddling GW7 are not comparable.
- Price band ≥8.0: bias 0.09 on n=8 — no premium under-prediction this round (C15 stays answered).
- FWD bias 0.63 on n=47 is the largest positional bias this round; one round, withheld on power grounds.
- DefCon: 30/178 hits (players with 60'+) with no expected count to test against (C10 unshipped).
- C12: two banded promoted-club rows fielded. Haaland v IPS (H) +6.42 (attacking, the direction C12 predicts) and Van Hecke v COV (H) −0.60; the largest term of each is still unauditable from the ledger (C17).

## Corrections

| C# | Agent | Status | Evidence |
|---|---|---|---|
| C1 | A3 | retired — satisfied | closed at GW2; carried verbatim |
| C2 | A3 | retired — moved to C10 | carried verbatim |
| C3 | A3 | retired — moved to C9 | carried verbatim |
| C4 | A2 | revised — see C12 | carried verbatim |
| C5 | A2, A4 | active | complied — no GW7 chip; GW9 3xc earmark held provisional on Haaland's own EP |
| C6 | A4, A7 | retired — satisfied | carried verbatim |
| C7 | A3 | retired — superseded by spec | the player-analyst spec binds the tag to rate risk only, from GW7 |
| C8 | A4 | active | did not bite: bench gaps 0.328 and 0.854, both outside 0.25; no auto-sub fired |
| C9 | CODE | retired — premise false: `defcon_hit_probability` already maps dc90_prior / threshold through the single `DEFCON_HIT_ANCHORS` curve for every position | carried verbatim |
| C10 | CODE | active — unshipped | seventh round: 30/178 hits with no Σ P(hit); cumulative still n/bias/mae/brier only |
| C11 | A7 | active | complied — STATE emits `chip: null`, `chips_used: []` and four `chip_plan` rows |
| C12 | A2 | active — untested | Haaland v IPS (H) +6.42 and Van Hecke v COV (H) −0.60 on banded rows; largest terms unauditable until C17 |
| C13 | CODE | active — unshipped | round block prints expected starts 206.0 v actual 217 with no band attribution |
| C14 | A4 | active | complied — Thiaw → Van Hecke +2.223 blend / +1.214 prior-only, sign holds on both |
| C15 | A4 | active — answered | ≥8.0 bias 0.09 on n=8; no premium under-prediction |
| C16 | A4 | retired — superseded by spec | captaincy ranks on raw EP; the multipliers no longer exist |
| C17 | CODE | active — unshipped | squad rows still carry no largest EP term; C12 audit blocked for Haaland and Van Hecke |
| C18 | A3 | revised — see C21 | starts gap −3.2, −11.0, −11.0: three rounds on the far side since the cap |
| C19 | CODE | active — unshipped | squad rows print `min` but no expected v actual minutes; Groß 70' and Tavernier 78' book as start successes |
| C20 | A4 | active | did not bite: slot-11 boundary Thiago 4.034 v Richards 3.089, gap 0.945, outside the band |

**C21 — A3 (player-analyst): drop C18's blanket 0.90 cap on nominal first-choice starters and set each p_start from that player's own recent start record; keep only C18's reservation of p_start ≥ 0.93 for an unbroken start streak across the three most recent rounds, and raise a rotation-band p_start (below 0.30) when the player started either of the two most recent rounds.** Revises C18. Since the cap took effect, expected starts have fallen short of actual starts for three straight rounds (gaps −3.2, −11.0, −11.0, after +7.9, +8.9, +10.7 before it), and round 7's largest minutes misses include Hato and Isak playing 90' and 78' on p_start 0.22 and 0.15.

## Running calibration stats

```
group             n    bias    mae
overall         439    0.20   1.56
DEF             151    0.19   1.68
FWD              47    0.63   1.80
GKP              37    0.12   1.18
MID             204    0.13   1.49
HIGH            258    0.16   0.99
LOW             108    0.22   2.64
MED              73    0.31   1.98
5.5-7.9         132    0.30   1.99
<5.5            299    0.16   1.31
>=8.0             8    0.09   3.85
minutes: brier 0.1211, expected starts 206.0, actual 217, gap -11.0
defcon: 30/178 hits (players with 60'+)
cumulative (rounds 1,2,3,4,5,6,7): n=3343 bias=0.13 mae=1.53 brier=0.1179
```

Team value this GW: 997 → 998 (+0.1m). Cumulative: 1000 → 998 (−0.2m).

## Carried into GW8

- p_start levels for every position under C21 (C18 revised); re-read the starts gap at GW9 for overshoot in the new direction.
- GW8 wildcard (provisional) and GW9 Triple Captain on Haaland v BHA (H): the 3xc case rests on Haaland's own EP (C5).
- Promoted-club fixture rows stay two-sided ±15pp (C12); audit blocked until C17 ships.
- Every proposed transfer scored blend and prior-only; no hit whose sign flips (C14).
- Bench and XI/bench boundary near-ties within 0.25 broken on DefCon floor share (C8, C20).
- Calibrate code outputs still unshipped: Σ P(hit) and cumulative band/tier (C10), starts by p_start band and `--ids` (C13), largest EP term per squad row (C17), expected v actual minutes (C19).
