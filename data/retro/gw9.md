# GW9 Retro

## Squad

```
squad XI (captain doubled): predicted 55.46, actual 58; bench stranded 17
captain: Haaland 2 pts; hindsight best in XI: Van Hecke 15 (forgone 13)
squad rows (slot role id name pred act err start p_start min; * = |err| > 3):
    1 XI     385  Trafford             pred   3.52  act   2  err  -1.52  start Y  p_start 0.95  min  90
    2 XI       4  Gabriel              pred   4.52  act   6  err  +1.48  start Y  p_start 0.95  min  90
    3 XI      60  Hill                 pred   4.38  act   6  err  +1.61  start Y  p_start 0.95  min  90
    4 XI     112  Van Hecke            pred   4.19  act  15  err +10.81* start Y  p_start 0.95  min  90
    5 XI     427  Mbeumo               pred   4.84  act   1  err  -3.84* start Y  p_start 0.96  min  90
    6 XI      68  Tavernier            pred   4.64  act   3  err  -1.64  start Y  p_start 0.93  min  90  VC
    7 XI     542  E.Le Fée             pred   4.41  act   8  err  +3.60* start Y  p_start 0.94  min  90
    8 XI     453  Barnes               pred   4.04  act   2  err  -2.04  start Y  p_start 0.94  min  90
    9 XI     411  Haaland              pred   6.12  act   2  err  -4.12* start Y  p_start 0.94  min  90  C
   10 XI     249  Barry                pred   4.50  act   9  err  +4.50* start Y  p_start 0.94  min  79
   11 XI     379  Isak                 pred   4.18  act   2  err  -2.18  start Y  p_start 0.88  min  90
   12 bench  496  Kinsky               pred   3.32  act   6  err  +2.68  start Y  p_start 0.95  min  90
   13 bench  127  Gomez                pred   3.58  act   3  err  -0.58  start Y  p_start 0.94  min  83
   14 bench  332  Justin               pred   3.22  act   2  err  -1.22  start Y  p_start 0.95  min  83
   15 bench    8  Calafiori            pred   2.59  act   6  err  +3.41* start Y  p_start 0.65  min  90
squad misses (|err| > 3): 4 Van Hecke +10.81, 5 Mbeumo -3.84, 7 E.Le Fée +3.60, 9 Haaland -4.12, 10 Barry +4.50, 15 Calafiori +3.41
```
Entry-history: 60 pts (3xc live); overall rank 1325502 → 1114461 (up 211041); value 997 → 1000 (+0.3).
`picks` matches final.md: same 15 ids and slots, captain 411 (mult 3, active chip 3xc), vice 68.

## Misses

| id | name | pred | act | err | class | cause |
|---:|---|---:|---:|---:|---|---|
| 112 | Van Hecke | 4.19 | 15 | +10.81 | VARIANCE | started; a DEF goal off 0.94 xG plus 3 bonus — finishing, not a repeatable rate |
| 427 | Mbeumo | 4.84 | 1 | -3.84 | VARIANCE | started, 90'; 0.02 xG / 0.33 xA — a low-threat match, one round |
| 542 | E.Le Fée | 4.41 | 8 | +3.60 | VARIANCE | started; goal off 0.85 xG, dc 11 one short of the MID threshold |
| 411 | Haaland | 6.12 | 2 | -4.12 | VARIANCE | started, 90'; 0.47 xG / 0.08 xA did not convert — captaincy (3xc) was the right process |
| 249 | Barry | 4.50 | 9 | +4.50 | VARIANCE | started, 79'; goal off 1.29 xG plus 3 bonus |
| 8 | Calafiori | 2.59 | 6 | +3.41 | MINUTES | started and played 90' on p_start 0.65 (hip, 75%); dc 9, clean-sheet points |
| 161 | Lavia | 0.32 | 8 | +7.68 | MINUTES | 90' on p_start 0.10; dc 23 — the rotation band held a full-match starter |
| 145 | Fofana | 2.25 | 11 | +8.74 | MINUTES | 90' on p_start 0.60; assist plus 2 bonus off 0.15 xGI is the variance share |
| 492 | Awoniyi | 1.56 | 9 | +7.44 | MINUTES | 71' on p_start 0.30; goal off 0.18 xG is the variance share |
| 388 | Guéhi | 3.42 | 0 | -3.42 | MINUTES | 0' on p_start 0.90; whether news preceded the deadline is not in the outputs |
| 223 | Mateta | 3.79 | -2 | -5.79 | VARIANCE | 12' for −2 pts and −4 BPS — a disciplinary deduction, not a p_start error on this evidence |

## Captain and bench

Captain Haaland 2 pts (tripled); hindsight best in XI Van Hecke 15, forgone 13 on calibrate's single-multiplier basis (see gap below).
Bench stranded 17: every XI player played (Barry 79' the shortest), so no auto-sub could fire.
Bench order verdict: not a BENCH-ORDER loss — no non-player in the XI; Kinsky 6 behind Trafford 2 was the GK pair inside 0.25 (3.52 v 3.32), started on higher EP.
Outfield XI/bench boundary Barnes 4.04 v Gomez 3.58 (0.46) sat outside C8/C20's 0.25 band; realised 2 v 3.

## Findings

- predictions: lock 1235d0cc1924, drift none — the record scored is the decision record.
- Triple Captain: played GW9 on Haaland's fixture-independent EP (6.116, 1.277 clear of Mbeumo); returned 2 pts on 0.55 xGI. Process sound; outcome variance. Set-1 3xc is now spent.
- XI predicted 55.46 v actual 58 (captain doubled): five of six squad misses are VARIANCE with xG behind the hauls (Van Hecke 0.94, Le Fée 0.85, Barry 1.29) and behind the blanks (Haaland 0.47, Mbeumo 0.02). No process error in the XI.
- Minutes: brier 0.1029; expected starts 215.3 v actual 219, gap −3.7 — second round under C21, narrowing from −6.1 at GW8. The pool's under-predicted tail is again led by low-p_start players who played 90' (Lavia 0.10, Fofana 0.60, Awoniyi 0.30 at 71').
- C21's rotation-band clause (raise p_start below 0.30 when the player started either of the two most recent rounds) cannot be checked for Lavia or Awoniyi: their prior-round starts are not in the outputs (same gap as GW8, covered by C13's `--ids` request).
- DefCon: 33/186 hits (players with 60'+); no expected count to test against (C10).
- Price bands: ≥8.0 bias −0.33 on n=9 — no premium under-prediction (C15). Tier rows (HIGH/MED/LOW) are this round only, post-GW7 meaning.
- Overall bias +0.14 this round, cumulative +0.15 on n=4265; 47 players under-predicted by more than 3 against 10 over. No level correction: the per-round series needed to call this a 3+ GW trend is not printed, and no term can be attributed without C17.
- gap: calibrate's `squad XI` and `captain` lines apply a ×2 captain multiplier when the round's active chip is 3xc — the chip-adjusted predicted XI (final.md 61.574) and actual XI (entry-history 60) and the 3xc-adjusted hindsight forgone are not printed.
- gap: calibrate's cumulative block prints pooled n/bias/mae/brier only — a per-round bias series is needed to test whether the overall +0.15 under-prediction persists 3+ GWs.

## Corrections

| C# | Agent | Status | Evidence |
|---|---|---|---|
| C1 | A3 | retired — satisfied | closed at GW2; carried verbatim |
| C2 | A3 | retired — moved to C10 | carried verbatim |
| C3 | A3 | retired — moved to C9 | carried verbatim |
| C4 | A2 | revised — see C12 | carried verbatim |
| C5 | A2, A4 | retired — satisfied | set-1 3xc played GW9 on Haaland's fixture-independent EP (6.116, final.md: "rests on his own rates"); the gate it governed is spent |
| C6 | A4, A7 | retired — satisfied | carried verbatim |
| C7 | A3 | retired — superseded by spec | the player-analyst spec binds the tag to rate risk only, from GW7 |
| C8 | A4 | active | not engaged — bench gaps 0.367 and 0.622, none inside 0.25; no auto-sub fired |
| C9 | CODE | retired — premise false: `defcon_hit_probability` already maps dc90_prior / threshold through the single `DEFCON_HIT_ANCHORS` curve for every position | carried verbatim |
| C10 | CODE | active — unshipped | ninth round: 33/186 hits with no Σ P(hit); cumulative still n/bias/mae/brier only |
| C11 | A7 | active | complied — STATE emits `chip: 3xc`, `chips_used` and two `chip_plan` rows |
| C12 | A2 | active — untested | opponents are not in this retro's outputs; largest terms still unauditable until C17 |
| C13 | CODE | active — unshipped | round block prints expected starts 215.3 v actual 219 with no band attribution; no `--ids` rows |
| C14 | A4 | active | complied — Calafiori → Silva +1.797 blend / −0.085 prior-only rejected for the sign flip |
| C15 | A4 | active — answered | ≥8.0 bias −0.33 on n=9; no premium under-prediction |
| C16 | A4 | retired — superseded by spec | captaincy ranks on raw EP; the multipliers no longer exist |
| C17 | CODE | active — unshipped | squad rows still carry no largest EP term |
| C18 | A3 | revised — see C21 | carried verbatim |
| C19 | CODE | active — unshipped | squad rows print `min` but no expected v actual minutes; Barry at 79' books as a start success |
| C20 | A4 | active | not engaged — XI/bench boundary Barnes 4.043 v Gomez 3.583, 0.460 outside 0.25; realised 2 v 3 |
| C21 | A3 | active | second round in force: starts gap −3.7 against −6.1 the round before; rotation-band clause untestable (Findings) |

No new corrections this round: every squad miss is VARIANCE or a bench MINUTES row, and the pool's minutes misses fall under C21, already in force and narrowing the starts gap.

## Running calibration stats

```
group             n    bias    mae
overall         476    0.14   1.36
DEF             182    0.15   1.41
FWD              47    0.29   1.82
GKP              38    0.11   1.29
MID             209    0.11   1.22
HIGH            294    0.19   0.95
LOW             109    0.16   2.18
MED              73   -0.05   1.78
5.5-7.9         130    0.12   1.67
<5.5            337    0.17   1.22
>=8.0             9   -0.33   2.22
minutes: brier 0.1029, expected starts 215.3, actual 219, gap -3.7
defcon: 33/186 hits (players with 60'+)
cumulative (rounds 1,2,3,4,5,6,7,8,9): n=4265 bias=0.15 mae=1.52 brier=0.1182
```
Team value (entry-history): GW9 997 → 1000 (+0.3); cumulative GW1 1000 → 1000 (0.0).

## Carried into GW10

- Starts still under-forecast (gap −3.7), rotation band (Lavia, Awoniyi) — C21.
- Near-tie bench and XI/bench boundaries — C8, C20.
- Transfers with a prior-only sign flip (2 FTs banked for GW10) — C14.
- Promoted-club fixtures on both attacking and defensive terms — C12.
- DefCon hits untestable against expectation — C10 (CODE, unshipped).
- Starts-by-band and named-player rows missing — C13 (CODE, unshipped).
- Largest EP term per squad row missing — C17 (CODE, unshipped).
- Minutes (not only starts) unscored — C19 (CODE, unshipped).
