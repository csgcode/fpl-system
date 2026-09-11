# GW3 Retro

## Squad

```
squad XI (captain doubled): predicted 56.49, actual 55; bench stranded 13
captain: Haaland 9 pts; hindsight best in XI: Tavernier 10 (forgone 1)
squad rows (slot role id name pred act min):
    1 XI       1  Raya                 pred   3.12  act   3  min  90
    2 XI       4  Gabriel              pred   4.46  act   2  min  90
    3 XI     202  Richards             pred   4.06  act   1  min  90
    4 XI     229  Tarkowski            pred   3.73  act   3  min  90
    5 XI     427  Mbeumo               pred   5.26  act   8  min  90  VC
    6 XI     237  Ndiaye               pred   4.84  act   3  min  86
    7 XI     481  Anderson             pred   4.39  act   3  min  90
    8 XI      68  Tavernier            pred   4.34  act  10  min  88
    9 XI     411  Haaland              pred   6.39  act   9  min  90  C
   10 XI     106  Thiago               pred   5.10  act   2  min  90
   11 XI     249  Barry                pred   4.41  act   2  min  90
   12 bench  497  Dubravka             pred   0.18  act   0  min   0
   13 bench   69  Scott                pred   4.05  act  10  min  90
   14 bench  445  Thiaw                pred   3.56  act  -1  min  90
   15 bench  423  Shaw                 pred   2.39  act   4  min  90
```

Overall rank 6,163,114 → 5,635,925 on 55 points, up 527,189 places; season total 174.
Team value 999 → 999: **0.0 this GW**, **−0.1 cumulative** against the £100.0m start; bank 0.0, 1 transfer, 13 bench points.
The `picks` endpoint matches final.md's `picks:` block exactly — same 15 ids in the same order, Haaland C (mult 2), Mbeumo VC — so the ledger's squad rows describe the fielded team, not just the plan.

## Misses

| Id | Name | Pred | Act | Err | Class | Cause |
|---:|---|---:|---:|---:|---|---|
| 204 | Mitchell | 3.31 | 15 | +11.69 | VARIANCE | defender, 2 goals off 0.66 xG |
| 379 | Isak | 5.52 | 13 | +7.48 | VARIANCE | 2 goals off 0.21 xG in 63 min |
| 69 | Scott | 4.05 | 10 | +5.95 | VARIANCE | 2 assists off 0.02 xA; benched by the 0.36 XI boundary |
| 68 | Tavernier | 4.34 | 10 | +5.66 | VARIANCE | goal off 1.01 xG plus 3 bonus |
| 387 | O'Reilly | 4.65 | 0 | −4.65 | MINUTES | p_start 0.78, did not appear |
| 445 | Thiaw | 3.56 | −1 | −4.56 | VARIANCE | −3 card deduction inside a 90-minute appearance |
| 426 | B.Fernandes | 6.35 | 2 | −4.35 | MODEL | 0.15 xG; the blended attack rate carries a recency artefact |
| 398 | Foden | 4.93 | 1 | −3.93 | MINUTES | p_start 0.86, 24 min |
| 106 | Thiago | 5.10 | 2 | −3.10 | VARIANCE | 0.50 xG unconverted |
| 202 | Richards | 4.06 | 1 | −3.06 | VARIANCE | dc 9, one short of the DEF-10 threshold; no clean sheet |

## Captain and bench

Captain Haaland 9 pts (18 doubled); hindsight best in XI Tavernier 10, **forgone 1**. Correct process — a goal, 1.06 xG and 3 bonus on the round's clearest discounted-EP lead (+1.12).
Bench stranded **13** (Scott 10, Shaw 4, Thiaw −1), equal to entry-history's `bench 13`.
Bench-order verdict: correct and untested — every XI slot played ≥ 86 minutes, so no auto-sub fired; Scott at bench 1 was both the highest bench EP and the highest bench scorer.
The 13 stranded points are an XI-selection outcome (Barry 4.408 over Scott 4.048, gap 0.36), not a bench-order one; C8's 0.25 band does not reach that gap.

## Findings

- Round 3 is centred but wider: bias 0.04 as in round 2, MAE 1.56 against 1.19. Cumulative brier improves 0.1262 → 0.1204.
- The error tail is asymmetric by cause. The over-predicted top 8 is a **minutes** tail — 5 of 8 played under 60 minutes (O'Reilly 0, Wieffer 0, Collins 16, Foden 24, Sangaré 45). The under-predicted top 8 is a **finishing** tail — all 8 played 60+. Marginal accuracy now lives in p_start, not in rate estimation.
- DEF carries the round's worst MAE (1.95) and highest bias (+0.29) on defender goals alone: Mitchell 2 off 0.66 xG, Bogle 1 off 0.90, Vuskovic 1 off 0.19. **Do not raise DEF attacking rates on this.**
- The DefCon threshold asymmetry recurred inside our own squad: Scott's dc 11 at MID scored nothing while Vuskovic's dc 10 at DEF scored, with Tavernier (dc 9) and Janelt (dc 12) bracketing the same line. The 10/12 thresholds are the game's; only C9's curve shape is ours.
- **The XI/bench boundary item is closed, not carried.** The benched player has outscored the marginal starter three GWs running (Thiaw/Shaw, Tarkowski/Richards, Scott/Barry), but a 0.36 EP gap against a ~3-point per-player spread is near a coin flip, so 3/3 carries no information. Tracking it further would manufacture a signal.
- MED-B dead bench: Dubravka 0 minutes for a fourth consecutive GW. The FWD half is repaired (Barry, 90 min). Bench Boost remains unusable.
- LOW-4 recency test, partial verdict: Barry — bought on structure (Beto sold), not form — returned 2 against 4.41, mild counter-evidence. The stronger evidence is the buy we rejected on recency grounds: B.Fernandes 2 pts off 0.15 xG.
- MED-E template fades: of the four unheld >30%-owned players, only B.Fernandes (2 pts) is readable. The verdict cannot be completed this round.
- `gap:` **expected starts by p_start band.** Σ p_start has exceeded actual starts two rounds running (227.9 v 220, then 225.9 v 217) and the block reports only pooled totals, so the miss cannot be attributed to a band — uniform inflation and a few high-p_start absences are indistinguishable.
- `gap:` **round rows for named non-squad players.** calibrate prints only the top-8 error tails, so a rejected transfer target (De Cuyper) or an unheld template player (João Pedro, Calafiori, Szoboszlai) has no readable row, leaving the LOW-4 and MED-E tests without an instrument.
- Agent-code drift in the prior retros: C6 and C11 name the finalizer but carry code A5, which the roster assigns to the red-team-reviewer. Both are carried below under **A7** per the name rule; the prior files are left as written.

## Corrections

| C# | Agent | Status | Evidence |
|---|---|---|---|
| C1 | A3 | retired — satisfied | closed at GW2; carried verbatim |
| C2 | A3 | retired — moved to C10 | carried verbatim |
| C3 | A3 | retired — moved to C9 | carried verbatim |
| C4 | A2 | revised — see C12 | carried verbatim |
| C5 | A2, A4 | active | complied — no GW3 TC; the +0.10 edge over the GW5 earmark sat inside COV's band |
| C6 | A4, A7 | retired — satisfied | carried; GW3's 15 `picks:` lines match the `picks` endpoint again |
| C7 | A3 | active | complied — every XI slot LOW at p_start ≥ 0.88, Shaw MED at 0.85 benched 15th |
| C8 | A4 | active — GW4 verdict delivered | applied once (Tarkowski 25% v Thiaw 19% DefCon share, gap 0.17): Tarkowski 3, Thiaw −1, realised +4 — but the gain is a card deduction, not the floor mechanism. Band stays 0.25; the recurring revisit duty ends here |
| C9 | CODE | active — bias evidence did not replicate | the structural defect (two curve shapes for one quantity) stands, but GW2's gap reverses: DEF +0.29 / MID −0.09 against −0.21 / +0.26. Do not size the fix from either round |
| C10 | CODE | active — unshipped | both consequences recur: 34/188 realised DefCon hits with no Σ P(hit) to test, and ≥8.0 swinging +5.67 → −0.22 with no cumulative band aggregate to pool it |
| C11 | A7 | active | complied — `chip: null`, `chips_used: []` and four `chip_plan` rows all emitted |
| C12 | A2 | active — untested | no selected player's largest term was a promoted-club fixture; Barry's banded rows were attacking, which C12 permits |

**C13 — CODE (fpl/calibrate.py): emit expected-vs-actual starts by p_start band in both the round and cumulative blocks, and accept an `--ids` list whose round rows print regardless of error rank.** Both `gap:` lines above. Expected starts have exceeded actual for two rounds running with no band attribution available, and the top-8 tails hide every named non-squad player the recency (LOW-4) and template-fade (MED-E) tests depend on.

**C14 — A4 (squad-optimizer): compute every proposed transfer's gross EP gain on prior-only rates as well as blended, and never take a hit whose sign flips between the two.** GW3's review ran this once ad hoc — Isak + B.Fernandes scored +9.74 blended and −1.69 prior-only — and round 3 vindicated the prior-only reading: B.Fernandes 2 pts off 0.15 xG is the pool's third-largest over-prediction, while Haaland returned +2.61. Promotes GW3's condition (c) from a one-off gate to a standing rule.

**C15 — A4: treat the GW4 premium-restructure conditions (a) and (b) as answered NO, not as still deferred.** Round 3 reverses (a): the ≥£8.0m band's bias is −0.22 on n=11 against round 2's +5.67, and inside it Fernandes −4.35 against Haaland +2.61 — the under-prediction neither replicated nor sat away from Haaland. GW3's own final.md shows (b) is mechanical (w_prior moves only 0.769 → 0.69 at 270 minutes, so one round cannot unwind a 23-point fortnight). Condition (c), now C14, is the only live gate.

**C16 — A4: apply the certainty multipliers (LOW 1.00 / MED 0.92 / HIGH 0.80) to the captain choice only; order the XI and the bench on undiscounted EP.** C7 makes the tag a function of p_start, and p_start is already inside `ep` — outside the captaincy's variance case the multiplier discounts rotation risk twice. The tier blocks give it no calibration basis either: LOW +0.64 → −0.15, MED +0.12 → +0.25, HIGH −0.07 → +0.06 across rounds 2 and 3, small and sign-unstable, with no tier persistently over-predicted. Realised cost this round 0 — every XI slot was LOW. Any change to the multiplier **values** waits on C10's cumulative tier aggregates.

## Running calibration stats

```
group             n    bias    mae
overall         426    0.04   1.56
DEF             138    0.29   1.95
FWD              49   -0.21   1.27
GKP              36    0.16   1.18
MID             203   -0.09   1.42
HIGH            261    0.06   1.02
LOW              97   -0.15   2.47
MED              68    0.25   2.31
5.5-7.9         171   -0.09   1.72
<5.5            244    0.14   1.38
>=8.0            11   -0.22   2.86
minutes: brier 0.1037, expected starts 225.9, actual 217
defcon: 34/188 hits (players with 60'+)
cumulative (rounds 1,2,3): n=1642 bias=0.04 mae=1.39 brier=0.1204
```

Team value delta this GW **0.0** (999 → 999, from entry-history).
Cumulative team value delta **−0.1** against the £100.0m start.

## Carried into GW4

- **Premium under-prediction** — ≥8.0 swings +5.67 (round 2) → −0.22 (round 3), n=11 each. Unpowered; C10 is the instrument and C15 blocks reading it as support for the restructure.
- **DefCon position asymmetry** — structural and live; C9 binds, and until it ships A3 holds C1's mapping unchanged.
- **Start over-prediction** — Σ p_start above actual starts two rounds running; C13 is the instrument, verdict at round 4.
- **Dead GK2** — Dubravka 0 minutes a fourth GW, ≈0.18 EP/GW; repair routed to GW5 cash or the wildcard. LOW-6 in GW3's review; no C binds it.
- **MED-E template fades** — unresolvable at round 3; C13's `--ids` list is the instrument.
- **GW5 Triple Captain earmark** — C5 binds again: justify on Haaland's fixture-independent EP alone or defer.
- **Certainty-multiplier scope** — C16 binds from GW4; the multiplier values themselves wait on C10.
