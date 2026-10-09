# GW5 Retro

## Squad

The GW5 plan was never applied (expired session, deadline passed; see the
CORRECTION at the top of data/decisions/gw5/final.md). The STATE block was
replaced with the team actually fielded — GW4's fifteen, slots and armbands — and
calibrate builds its squad rows from that block. The `picks` endpoint for event 5
matches it on all 15 ids, every slot, captain 411 and vice 4. So the rows below
describe the **fielded** team scored on GW5 per-player predictions, not the plan.

```
squad XI (captain doubled): predicted 55.47, actual 58; bench stranded 8
captain: Haaland 6 pts; hindsight best in XI: Tarkowski 14 (forgone 8)
squad rows (slot role id name pred act min):
    1 XI       1  Raya                 pred   3.31  act   1  min  90
    2 XI       4  Gabriel              pred   4.42  act   1  min  90  VC
    3 XI     229  Tarkowski            pred   4.42  act  14  min  90
    4 XI     202  Richards             pred   2.87  act   8  min  90
    5 XI      68  Tavernier            pred   4.91  act   2  min  74
    6 XI     427  Mbeumo               pred   5.21  act   2  min  90
    7 XI      69  Scott                pred   4.17  act   2  min  90
    8 XI     237  Ndiaye               pred   3.66  act   5  min  74
    9 XI     411  Haaland              pred   6.72  act   6  min  90  C
   10 XI     106  Thiago               pred   4.62  act   5  min  90
   11 XI     249  Barry                pred   4.43  act   6  min  90
   12 bench  497  Dubravka             pred   0.12  act   0  min   0
   13 bench  481  Anderson             pred   4.00  act   2  min  90
   14 bench  445  Thiaw                pred   4.45  act   4  min  90
   15 bench  423  Shaw                 pred   1.01  act   2  min  83
```

Rank 5,362,185 → 4,367,291 (−994,894), GW points 58 (entry-history).
Team value 996 → 998: **+0.2** this GW.

## Misses

| id | name | pred | act | err | class | cause |
|---:|---|---:|---:|---:|---|---|
| 229 | Tarkowski | 4.42 | 14 | +9.57 | VARIANCE | CS + assist off 0.01 xA + 3 bonus + DefCon (dc 12) |
| 202 | Richards | 2.87 | 8 | +5.13 | VARIANCE | CS at LEE (A) plus DefCon hit (dc 10); no attacking return |
| 4 | Gabriel | 4.42 | 1 | −3.42 | VARIANCE | ARS conceded at BHA; dc 9, one short of the DEF threshold |
| 427 | Mbeumo | 5.21 | 2 | −3.21 | VARIANCE | 0.27 xG + 0.25 xA, 90 min, no return |
| 552 | Brobbey (pool) | 2.58 | 17 | +14.42 | VARIANCE | hat-trick off 2.35 xG — a genuine chance haul, not a rate miss |
| 397 | Semenyo (pool) | 3.93 | 17 | +13.07 | VARIANCE | 2 goals off 0.16 xG |
| 53 | Manzambi (pool) | 0.73 | 13 | +12.27 | MINUTES | p_start 0.20, started and played 71' |
| 93 | Schuster (pool) | 2.60 | 14 | +11.40 | VARIANCE | CS + assist + DefCon (dc 16) + 3 bonus at p_start 0.72 |
| 464 | Wissa (pool) | 4.71 | 0 | −4.71 | VARIANCE | 0.84 xG, blank, 0 BPS |
| 565 | M.Sangaré (pool) | 3.92 | 0 | −3.92 | MINUTES | p_start 0.90, 21 minutes |

## Captain and bench

Captain hindsight forgone 8 (Tarkowski 14 v Haaland 6): VARIANCE — Haaland was also the plan's captain at a 1.509 EP lead, and Tarkowski's 14 rests on 0.01 xA.
Bench stranded 8; no auto-sub was due, since all eleven starters played. The bench order was GW4's, carried forward, not a GW5 decision.
Boundary in the fielded team went in our favour: Richards 8 (XI) v Thiaw 4 (bench); Ndiaye 5 (XI) v Anderson 2 (bench).
Verdict: no bench-order or captain process error. Nothing in this section was a GW5 decision.

## Findings

- **EXECUTION — the plan was never applied.** Expired credentials; `auth-check` failed twice at the team-executor step, and no re-capture completed before the 2026-09-18T17:30Z deadline. Already logged to docs/backlog.md (GW5 / ORCH / WORKFLOW) per the final.md CORRECTION; not re-mirrored here. Per that CORRECTION, no correction is raised against A2–A5 for the non-application.
- **Plan v fielded, realised.** Ex ante the plan led by +1.93 EP (57.397 v 55.47). From the squad rows plus Le Fée's actuals, the planned XI (Thiaw and Anderson in for Richards and Ndiaye, Le Fée benched) would have scored 51 against the fielded 58. Execution failure **gained 7 points this round** — variance on two clean sheets, not evidence for the fielded XI. The real cost is forward: the unmade Ndiaye → E.Le Fée move (+4.105 EP6 blend) is still open, and 3 FTs now sit idle into GW6. Le Fée 5 v Ndiaye 5 this round.
- **Start over-prediction reversed in the first round under C18.** Expected starts 211.8 v actual 215 (−3.2), after +7.9 / +8.9 / +10.7 in rounds 2–4. Brier 0.1101 is not better than round 4's 0.1097, so the gain is in level, not in discrimination. One round: do not tighten or loosen C18 on it.
- **MINUTES misses now sit on both sides.** Manzambi (0.20 → 71') and Sangaré (0.90 → 21'), plus Aina (0.85) and João Pedro (0.68, flagged `d` 75%) at 0 minutes. No direction dominates; consistent with the level fix holding.
- **Pool bias positive in every group** (overall +0.34, LOW tier +0.55, all four positions +0.15 to +0.50). Driven by a high-scoring round — the top under-predictions are xG-light hauls (Semenyo 0.16 xG, Tarkowski 0.01 xA). Cumulative bias +0.10. Withheld on power: one round.
- **≥8.0 band** −0.04 on n=9, fourth reading near zero after round 2's +5.67. C15 stays answered.
- **Template fades held**: B.Fernandes 2 (pred 5.88), João Pedro 0 (pred 3.45). Still not a test — C13's `--ids` list is unshipped and these two surfaced only because they made the top-8 tails.
- **DefCon** 35/188 hits with no Σ P(hit) to test against — fifth round; C10 unshipped.
- No new `gap:` lines; every missing number this round is already bound by C10, C13, C17 or C19.

## Corrections

| C# | Agent | Status | Evidence |
|---|---|---|---|
| C1 | A3 | retired — satisfied | closed at GW2; carried verbatim |
| C2 | A3 | retired — moved to C10 | carried verbatim |
| C3 | A3 | retired — moved to C9 | carried verbatim |
| C4 | A2 | revised — see C12 | carried verbatim |
| C5 | A2, A4 | active | complied — no GW5 3xc; GW9 earmark kept on Haaland's band-free 6.995 |
| C6 | A4, A7 | retired — satisfied | carried; the corrected STATE `picks:` matches the `picks` endpoint on all 15 |
| C7 | A3 | active | complied — planned XI all LOW at p_start ≥ 0.90; Dubravka HIGH 0.03, Shaw HIGH 0.32 |
| C8 | A4 | active | did not bite in the plan (bench gaps 1.014, 1.855); untested in the fielded team, whose bench was GW4's |
| C9 | CODE | active — unshipped | DEF +0.37 (n=145) v MID +0.33 (n=191), a 0.04 gap; bias again refuses to size the structural defect |
| C10 | CODE | active — unshipped | fifth round: 35/188 DefCon hits with no Σ P(hit); cumulative still n/bias/mae/brier only |
| C11 | A7 | active | complied — corrected STATE block emits `chip: null`, `chips_used: []` and four `chip_plan` rows |
| C12 | A2 | active — untested | EVE v IPS (H) fielded Tarkowski and Barry on a promoted-club fixture; their largest terms are unauditable until C17 ships |
| C13 | CODE | active — unshipped | start level flipped to −3.2 with no band attribution; the template-fade ids again visible only by chance in the tails |
| C14 | A4 | active | complied — every single and the second FT scored on both readings in final.md |
| C15 | A4 | active — answered | ≥8.0 bias −0.04 on n=9; no replication of round 2 |
| C16 | A4 | active | complied — multipliers confined to the captain choice; every candidate LOW |
| C17 | CODE | active — unshipped | ledger still carries no largest EP term per squad row; C12 audit blocked again |
| C18 | A3 | active — complied, first effect | expected v actual starts −3.2 after +7.9 / +8.9 / +10.7; hold the cap unchanged, re-read at GW7 |
| C19 | CODE | active — unshipped | Tavernier 74' and Ndiaye 74' book as start successes; minutes still unscored |
| C20 | A4 | active — untested | applied in the plan (Anderson v E.Le Fée, gap 0.119, resolved on DefCon share) but the plan's XI was never fielded |

No new corrections. GW5's gap is attributed to EXECUTION per the final.md CORRECTION, every squad-row miss is VARIANCE, and the pool signals (positive bias, minutes reversal) are one round deep.

## Running calibration stats

```
group             n    bias    mae
overall         415    0.34   1.68
DEF             145    0.37   1.92
FWD              43    0.15   1.57
GKP              36    0.50   1.54
MID             191    0.33   1.55
HIGH            248    0.27   1.15
LOW              98    0.55   2.66
MED              69    0.29   2.19
5.5-7.9         132    0.26   2.00
<5.5            274    0.39   1.46
>=8.0             9   -0.04   3.84
minutes: brier 0.1101, expected starts 211.8, actual 215
defcon: 35/188 hits (players with 60'+)
cumulative (rounds 1,2,3,4,5): n=2483 bias=0.10 mae=1.51 brier=0.1168
```

Team value delta this GW **+0.2** (996 → 998, from entry-history).
Cumulative team value delta **−0.2** against the £100.0m start.

## Carried into GW6

- **Execution** — the GW5 transfer never happened; S1 is fully open again (final.md CORRECTION) and 3 FTs are available at GW6. Run `auth-check` early in the cycle, not only at the executor step. No C binds it; the backlog row does.
- **Start level** — reversed to −3.2 in C18's first round. C18 binds unchanged; C13 is the band instrument, unshipped.
- **Ledger instrumentation** — C10, C13, C17, C19 unshipped; they block the DefCon slope test, tier/band pooling, the C4/C12 audit and minutes attribution.
- **DefCon position asymmetry** — structural, unsized; C9 binds, A3 holds C1's mapping.
- **XI/bench boundary** — C20 binds; untested this round because the plan was not fielded.
- **Dead GK2 and DEF5** — Dubravka 0 minutes a sixth GW; Shaw 83' this round but still flagged. Routed to the GW8 wildcard or the 3 banked FTs.
- **Triple Captain GW9 earmark** — C5 binds: justify on Haaland's fixture-independent EP alone, or defer.
