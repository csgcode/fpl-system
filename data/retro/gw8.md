# GW8 Retro

## Squad

```
squad XI (captain doubled): predicted 55.05, actual 94; bench stranded 19
captain: Haaland 8 pts; hindsight best in XI: Gabriel 17 (forgone 9)
squad rows (slot role id name pred act err start p_start min; * = |err| > 3):
    1 XI     385  Trafford             pred   3.57  act  10  err  +6.43* start Y  p_start 0.95  min  90
    2 XI       4  Gabriel              pred   5.08  act  17  err +11.92* start Y  p_start 0.95  min  90  VC
    3 XI       8  Calafiori            pred   4.60  act   1  err  -3.60* start N  p_start 0.94  min  22
    4 XI      60  Hill                 pred   3.98  act  11  err  +7.02* start Y  p_start 0.95  min  90
    5 XI     112  Van Hecke            pred   3.56  act   7  err  +3.44* start Y  p_start 0.95  min  90
    6 XI     427  Mbeumo               pred   4.93  act   2  err  -2.93  start Y  p_start 0.96  min  90
    7 XI     542  E.Le Fée             pred   4.41  act   3  err  -1.41  start Y  p_start 0.94  min  78
    8 XI      68  Tavernier            pred   4.35  act  10  err  +5.65* start Y  p_start 0.93  min  86
    9 XI     453  Barnes               pred   4.12  act   8  err  +3.88* start Y  p_start 0.96  min  76
   10 XI     411  Haaland              pred   5.80  act   8  err  +2.20  start Y  p_start 0.94  min  90  C
   11 XI     379  Isak                 pred   4.85  act   9  err  +4.15* start Y  p_start 0.88  min  76
   12 bench  496  Kinsky               pred   2.92  act   9  err  +6.08* start Y  p_start 0.95  min  90
   13 bench  332  Justin               pred   3.77  act   6  err  +2.23  start Y  p_start 0.95  min  90
   14 bench  127  Gomez                pred   3.54  act   2  err  -1.54  start Y  p_start 0.93  min  90
   15 bench  249  Barry                pred   3.66  act   2  err  -1.66  start Y  p_start 0.94  min  90
squad misses (|err| > 3): 1 Trafford +6.43, 2 Gabriel +11.92, 3 Calafiori -3.60, 4 Hill +7.02, 5 Van Hecke +3.44, 8 Tavernier +5.65, 9 Barnes +3.88, 11 Isak +4.15, 12 Kinsky +6.08
```

Rank 4,106,307 → 1,325,502 (up 2,780,805); 94 pts. Team value 99.8 → 99.7 (−0.1), bank 0.4 → 0.1.
`picks` matches final.md: same 15 ids in the same slots, captain Haaland (411), vice Gabriel (4), active chip wildcard. The ledger describes the fielded team.

## Misses

| id | name | pred | act | err | class | cause |
|---|---|---|---|---|---|---|
| 385 | Trafford | 3.57 | 10 | +6.43 | VARIANCE | clean sheet at SUN plus 3 bonus; no attacking return involved |
| 4 | Gabriel | 5.08 | 17 | +11.92 | VARIANCE | goal off 0.54 xG, clean sheet, 3 bonus, DefCon hit (dc 14) in one match |
| 8 | Calafiori | 4.60 | 1 | -3.60 | MINUTES | did not start (p_start 0.94); came on as a substitute for 22' |
| 60 | Hill | 3.98 | 11 | +7.02 | VARIANCE | clean sheet at MUN, DefCon hit on dc 22, 3 bonus |
| 112 | Van Hecke | 3.56 | 7 | +3.44 | VARIANCE | clean sheet at CHE plus 1 bonus; dc 8, no DefCon hit |
| 68 | Tavernier | 4.35 | 10 | +5.65 | VARIANCE | goal off 0.72 xG plus 2 bonus — xG-backed conversion |
| 453 | Barnes | 4.12 | 8 | +3.88 | VARIANCE | goal off 0.27 xG |
| 379 | Isak | 4.85 | 9 | +4.15 | VARIANCE | goal off 0.40 xG plus 3 bonus |
| 496 | Kinsky | 2.92 | 9 | +6.08 | VARIANCE | clean sheet plus 2 bonus (bench) |
| 514 | Tel | 0.46 | 11 | +10.54 | MINUTES | started and played 88' on p_start 0.12; goal off 0.14 xG |
| 593 | Dedić | 0.85 | 11 | +10.15 | MINUTES | played 90' on p_start 0.30; assist and clean sheet |
| 426 | B.Fernandes | 5.09 | 0 | -5.09 | MINUTES | 0' on p_start 0.96 |
| 165 | João Pedro | 4.25 | 0 | -4.25 | MINUTES | 0' on p_start 0.88 |
| 154 | Palmer | 4.13 | -1 | -5.13 | VARIANCE | played 79' for −1 pts on bps 1 — deductions (card or own goal), not a minutes or rate miss |

## Captain and bench

Captain Haaland 8 against Gabriel 17 in hindsight: forgone 9. Haaland led the XI on EP (5.80 v Gabriel 5.08, 0.718 clear); Gabriel's 17 is a 0.54-xG goal stacked on a clean sheet and 3 bonus — variance, the pick was right.
Bench stranded 19 (Kinsky 9, Justin 6, Gomez 2, Barry 2). No auto-sub could fire: every XI player took the field, Calafiori included (22').
Bench-order verdict: correct. C20 started Van Hecke (3.565, DefCon share 0.190) over Justin (3.773, 0.161) — Van Hecke 7 v Justin 6. C8 put Gomez (share 0.139) above Barry (0.008) — 2 v 2, no cost.

## Findings

- 8 of 9 squad misses are positive: a high-scoring round (94, 38.95 above the XI prediction). Seven are VARIANCE built on clean sheets and bonus (bonus 3/3/3/3/2/2/1 across Trafford, Gabriel, Hill, Isak, Tavernier, Kinsky, Van Hecke); the four goals came off 0.27–0.72 xG each. Do not correct on this.
- Round bias +0.27 overall, DEF +0.41, GKP +0.49 (n 153 and 37); cumulative bias 0.15 on n=3789. One round's positive DEF/GKP level is withheld on power grounds — no clean-sheet-level correction.
- Tier rows (HIGH 1.14, MED 2.18, LOW 2.53 mae) are round 8 only and all from after GW7's tag change, so they compare like with like; but the cumulative line carries no tier split, so no cross-round tier conclusion is drawn.
- ≥8.0 band: bias −0.80 on n=9 — no premium under-prediction (C15 holds).
- Minutes: expected starts 212.9 v actual 219, gap −6.1, the fourth round in a row with actual above expected (−3.2, −11.0, −11.0, −6.1). Round 8 is the first under C21; the gap halved. The miss pattern is two-sided: low-p starters (Tel 0.12, Osula 0.10, O.Dango 0.25, O'Nien 0.25, Dedić 0.30) and high-p no-shows (B.Fernandes 0.96, Calafiori 0.94, João Pedro 0.88). One round under the new rule — no further change.
- gap: per-player starts in rounds M−2 and M−1 for the pool's under- and over-predicted rows. C21's rotation-band clause (raise p_start below 0.30 when the player started either of the two most recent rounds) cannot be tested on Tel, Osula, O.Dango, O'Nien or Dedić without it.
- entry-history prints `tr 0` for event 8 although `picks` shows all eight wildcard buys fielded; under a wildcard the transfer count is not carried in that column. Read it as hits-free, not as no transfers.
- Execution: the plan was fielded as written (picks match, wildcard active) despite the expired session noted in final.md.
- DefCon 43/189 hits on 60'+ players; still no Σ P(hit) to test it against (C10).

## Corrections

| C# | Agent | Status | Evidence |
|---|---|---|---|
| C1 | A3 | retired — satisfied | closed at GW2; carried verbatim |
| C2 | A3 | retired — moved to C10 | carried verbatim |
| C3 | A3 | retired — moved to C9 | carried verbatim |
| C4 | A2 | revised — see C12 | carried verbatim |
| C5 | A2, A4 | active | complied — no 3xc in GW8 (wildcard week); GW9 3xc earmark held provisional, final.md defers it to fresh EP |
| C6 | A4, A7 | retired — satisfied | carried verbatim |
| C7 | A3 | retired — superseded by spec | the player-analyst spec binds the tag to rate risk only, from GW7 |
| C8 | A4 | active | complied — Gomez (3.541, share 0.139) above Barry (3.66, 0.008), gap 0.119 inside 0.25; no auto-sub fired, 2 v 2 |
| C9 | CODE | retired — premise false: `defcon_hit_probability` already maps dc90_prior / threshold through the single `DEFCON_HIT_ANCHORS` curve for every position | carried verbatim |
| C10 | CODE | active — unshipped | eighth round: 43/189 hits with no Σ P(hit); cumulative still n/bias/mae/brier only |
| C11 | A7 | active | complied — STATE emits `chip: wildcard`, `chips_used: []` and three `chip_plan` rows |
| C12 | A2 | active — untested | no XI row faced a promoted club in GW8; largest terms still unauditable until C17 |
| C13 | CODE | active — unshipped | round block prints expected starts 212.9 v actual 219 with no band attribution |
| C14 | A4 | active | complied — no wildcard component flips sign prior-only (smallest Raya → Trafford +0.045); Richards → Silva and Thiago → João Pedro rejected for flips |
| C15 | A4 | active — answered | ≥8.0 bias −0.80 on n=9; no premium under-prediction |
| C16 | A4 | retired — superseded by spec | captaincy ranks on raw EP; the multipliers no longer exist |
| C17 | CODE | active — unshipped | squad rows still carry no largest EP term |
| C18 | A3 | revised — see C21 | carried verbatim |
| C19 | CODE | active — unshipped | squad rows print `min` but no expected v actual minutes; Barnes and Isak at 76' book as start successes |
| C20 | A4 | active | complied and bit — Van Hecke (0.190) started over Justin (0.161), 0.208 apart; 7 v 6, realised +1 |
| C21 | A3 | active | first round in force: starts gap −6.1 against −11.0 the round before; rotation-band clause untestable (gap line in Findings) |

No new corrections this round: every squad miss is VARIANCE bar one MINUTES row, and the round-level biases are one round deep.

## Running calibration stats

```
group             n    bias    mae
overall         446    0.27   1.65
DEF             153    0.41   2.02
FWD              46    0.15   1.75
GKP              37    0.49   1.59
MID             210    0.16   1.37
HIGH            264    0.38   1.14
LOW             109    0.02   2.53
MED              73    0.26   2.18
5.5-7.9         132    0.13   2.18
<5.5            305    0.36   1.39
>=8.0             9   -0.80   2.82
minutes: brier 0.1368, expected starts 212.9, actual 219, gap -6.1
defcon: 43/189 hits (players with 60'+)
cumulative (rounds 1,2,3,4,5,6,7,8): n=3789 bias=0.15 mae=1.54 brier=0.1201
```

Team value this GW: 99.8 → 99.7 (−0.1). Cumulative: 100.0 → 99.7 (−0.3).

## Carried into GW9

- GW9 3xc earmark on Haaland: decide on his own fixture-independent EP, never on the opponent's defensive rating — C5.
- Two FTs at GW9: every transfer's sign must hold on prior-only as well as blend — C14.
- XI/bench boundary and bench order: DefCon-share tie-break inside 0.25 EP — C8, C20.
- p_start from each player's own start record; watch the starts gap for a second round under the rule — C21.
- Promoted-club band two-sided on attacking and defensive terms — C12.
- Calibrate ledger gaps blocking audits (Σ P(hit), starts by band, largest EP term, expected minutes) — C10, C13, C17, C19.
