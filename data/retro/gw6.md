# GW6 Retro

## Squad

```
squad XI (captain doubled): predicted 53.80, actual 44; bench stranded 11
captain: Haaland 6 pts; hindsight best in XI: Mbeumo 8 (forgone 2)
squad rows (slot role id name pred act err start p_start min; * = |err| > 3):
    1 XI       1  Raya                 pred   3.48  act   3  err  -0.48  start Y  p_start 0.94  min  90
    2 XI     229  Tarkowski            pred   4.36  act   3  err  -1.36  start Y  p_start 0.92  min  90
    3 XI       4  Gabriel              pred   4.51  act   2  err  -2.51  start Y  p_start 0.93  min  90
    4 XI     445  Thiaw                pred   3.94  act   0  err  -3.94* start Y  p_start 0.90  min  90
    5 XI     427  Mbeumo               pred   5.15  act   8  err  +2.85  start Y  p_start 0.93  min  90  VC
    6 XI     542  E.Le Fée             pred   4.73  act   2  err  -2.73  start Y  p_start 0.92  min  80
    7 XI      68  Tavernier            pred   4.24  act   1  err  -3.24* start Y  p_start 0.91  min  72
    8 XI     124  Groß                 pred   3.98  act   6  err  +2.02  start Y  p_start 0.93  min  90
    9 XI      94  Schade               pred   4.13  act   1  err  -3.13* start Y  p_start 0.93  min  51
   10 XI     411  Haaland              pred   5.47  act   6  err  +0.53  start Y  p_start 0.93  min  79  C
   11 XI     249  Barry                pred   4.34  act   6  err  +1.66  start Y  p_start 0.91  min  85
   12 bench  497  Dubravka             pred   0.11  act   0  err  -0.11  start N  p_start 0.03  min   0
   13 bench  106  Thiago               pred   4.37  act   4  err  -0.37  start Y  p_start 0.92  min  90
   14 bench  202  Richards             pred   3.59  act   4  err  +0.41  start Y  p_start 0.90  min  90
   15 bench  423  Shaw                 pred   2.74  act   3  err  +0.26  start Y  p_start 0.75  min  90
squad misses (|err| > 3): 4 Thiaw -3.94, 7 Tavernier -3.24, 9 Schade -3.13
```

Rank 4,367,291 → 5,544,586 (1,177,295 places worse); GW6 44 pts. Team value 99.8 → 99.7 (−0.1), bank 0.3, 3 transfers.
`picks` matches final.md on all 15 ids, captain Haaland (411) and vice Mbeumo (427): the three transfers and the lineup were POSTed as planned.

## Misses

| id | name | pred | act | err | class | cause |
|---:|---|---:|---:|---:|---|---|
| 445 | Thiaw | 3.94 | 0 | -3.94 | MODEL | started, 90' at COV (A) with dc 8 short of DEF's 10 and BPS −3; NEW's other defender Hall also 0 (pred 3.98) — a defence misjudged against a promoted club, one fixture, unauditable until C17 |
| 68 | Tavernier | 4.24 | 1 | -3.24 | VARIANCE | started, 72' at CHE (A) on 0.00 xG / 0.04 xA, dc 5; one quiet round after LOW-tier selection |
| 94 | Schade | 4.13 | 1 | -3.13 | MINUTES | started, withdrawn at 51' — below 60, so the appearance point and most of the window were lost; 0.41 xG unconverted |
| 101 | Henderson | 0.93 | 18 | +17.07 | MINUTES | p_start 0.30, played 90; 2 goals on 0.14 xG on top (variance) |
| 368 | Szoboszlai | 4.01 | 0 | -4.01 | MINUTES | p_start 0.92, 0 minutes |
| 516 | Bentancur | 3.14 | -2 | -5.14 | VARIANCE | p_start 0.88, 11 minutes for −2 pts and BPS −6 |
| 115 | De Cuyper | 3.43 | 15 | +11.57 | VARIANCE | goal and 3 bonus off 0.25 xG in 67' |
| 236 | Dewsbury-Hall | 3.96 | 13 | +9.04 | VARIANCE | goal + assist off 0.40 xG / 0.06 xA, plus dc 10 short of MID's 12 |

## Captain and bench

Haaland 6 (C) against Mbeumo 8 in hindsight: 2 forgone. VARIANCE — Haaland led Mbeumo by 0.556 on blend and held on prior-only; correct process.
Bench stranded 11, but every XI player recorded minutes, so no auto-sub could fire. The stranded points are a selection outcome, not an ordering one.
Bench-order verdict: correct. Thiago 4.209 / Richards 3.509 / Shaw 2.673 are separated by more than C8's 0.25 band.
The XI/bench boundary, Barry 4.327 v Thiago 4.209 (gap 0.118), fell inside C20's band. Barry 6 v Thiago 4: realised cost 0.

## Findings

- Execution clean for the first time since GW4: transfers and lineup POSTed, `picks` equals the plan.
- Prediction record mismatch: calibrate's squad XI predicted 53.80 against final.md's 56.178 for the same 15 ids and captain. Per-row preds differ (Raya 3.48 v 3.604, Haaland 5.47 v 5.786, Gabriel 4.51 v 4.671), a 2.38 gap. The ledger may be joining against players-*.json regenerated after the deadline; until that is resolved, the squad pred column is not the decision-time record.
- Starts: expected 205.0 v actual 216, gap −11.0 after −3.2 at GW5 and +7.9 / +8.9 / +10.7 before. C18 has overshot for two rounds. The pool's large positive residuals are low-p_start players who started (Henderson 0.30, Ouattara 0.20, Cherif 0.10, Gelhardt 0.10). Brier 0.1209 is the worst round printed so far. Not a 3-round trend yet; withhold a level correction and re-read at GW8.
- Position bias: MID +0.48 (n=196), FWD +0.75 (n=45), DEF −0.04 (n=144), GKP −0.41 (n=36). One round; no level correction on power grounds.
- DefCon: 38/183 hits, with nothing to test against (C10).
- Tier aggregates (HIGH +0.48 n=263, LOW −0.05 n=106, MED −0.31 n=52) are on the old p_start-bound tag; cumulative tier pools spanning GW7 will not be comparable.
- gap: actuals prints no goals-conceded, card, or own-goal column, so a 90-minute 0 (Thiaw) or 1 (Tavernier) cannot be split between goals conceded and a booking.

## Corrections

| C# | Agent | Status | Evidence |
|---|---|---|---|
| C1 | A3 | retired — satisfied | closed at GW2; carried verbatim |
| C2 | A3 | retired — moved to C10 | carried verbatim |
| C3 | A3 | retired — moved to C9 | carried verbatim |
| C4 | A2 | revised — see C12 | carried verbatim |
| C5 | A2, A4 | active | complied — no GW6 3xc; GW9 earmark held on Haaland's own EP |
| C6 | A4, A7 | retired — satisfied | carried verbatim |
| C7 | A3 | retired — superseded by spec | the player-analyst spec now binds the tag to rate risk only, from GW7 |
| C8 | A4 | active | did not bite: bench gaps 0.700 and 0.836, both outside 0.25; no auto-sub fired |
| C9 | CODE | retired — premise false: `defcon_hit_probability` already maps dc90_prior / threshold through the single `DEFCON_HIT_ANCHORS` curve for every position | premise checked: defcon_hit_probability, _defcon_probability, DEFCON_HIT_ANCHORS — position enters only through `threshold` |
| C10 | CODE | active — unshipped | sixth round: 38/183 hits with no Σ P(hit); cumulative still n/bias/mae/brier only |
| C11 | A7 | active | complied — STATE emits `chip: null`, `chips_used: []` and four `chip_plan` rows |
| C12 | A2 | active — untested | Tarkowski and Barry at HUL (A) and Thiaw at COV (A) fielded on promoted-club fixtures; largest terms unauditable until C17 |
| C13 | CODE | active — unshipped | starts gap −11.0 with no band attribution; no `--ids` option in this run |
| C14 | A4 | active | complied — every single and the package scored on both readings (+14.449 / +5.210) |
| C15 | A4 | active — answered | ≥8.0 bias −0.91 on n=9; no replication of round 2's under-prediction |
| C16 | A4 | retired — superseded by spec | captaincy ranks on raw EP; the multipliers no longer exist |
| C17 | CODE | active — unshipped | squad rows still carry no largest EP term; C12 audit blocked for Thiaw at COV |
| C18 | A3 | active — overshoot watch | starts gap −3.2 then −11.0; two rounds on the far side, re-read at GW8 before revising |
| C19 | CODE | active — unshipped | squad rows now print `min`, but no expected v actual minutes; Schade's 51' books as a start success |
| C20 | A4 | active | boundary gap 0.118 inside the band; final.md names no DefCon tie-break, Barry 6 v Thiago 4, realised cost 0 |

## Running calibration stats

```
group             n    bias    mae
overall         421    0.25   1.64
DEF             144   -0.04   1.74
FWD              45    0.75   1.77
GKP              36   -0.41   1.09
MID             196    0.48   1.63
HIGH            263    0.48   1.27
LOW             106   -0.05   2.35
MED              52   -0.31   2.01
5.5-7.9         130    0.46   1.98
<5.5            282    0.19   1.46
>=8.0             9   -0.91   2.12
minutes: brier 0.1209, expected starts 205.0, actual 216, gap -11.0
defcon: 38/183 hits (players with 60'+)
cumulative (rounds 1,2,3,4,5,6): n=2904 bias=0.12 mae=1.52 brier=0.1174
```

Team value (entry-history) this GW: 99.8 → 99.7, −0.1.
Cumulative: 100.0 → 99.7, −0.3.

## Carried into GW7

- CODE fpl/calibrate.py backlog unshipped: Σ P(hit) and cumulative band/tier (C10), starts by p_start band + `--ids` (C13), largest EP term per squad row (C17), expected v actual minutes (C19).
- Promoted-club fixtures remain unauditable on the defensive side; Thiaw at COV is the latest case (C12, blocked on C17).
- Starts calibration overshoot, −11.0 this round: A3 holds the C18 cap; re-read at GW8 (C18).
- GW9 Triple Captain earmark on Haaland's own EP only (C5).
- XI/bench boundary within 0.25 settles on DefCon floor share and is stated in final.md (C20); bench near-ties likewise (C8).
- GK2 dead / DEF5 weak, routed to the GW8 wildcard (C8 applies to its bench order).
- Squad pred column ≠ final.md EP this round; treat the ledger's squad preds as provisional until the backlog row is triaged.
