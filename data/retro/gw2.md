# GW2 Retro

## Squad

```
squad XI (captain doubled): predicted 51.66, actual 79; bench stranded 14
captain: Haaland 13 pts; hindsight best in XI: Haaland 13 (forgone 0)
squad rows (slot role id name pred act min):
    1 XI       1  Raya                 pred   3.77  act   6  min  90
    2 XI       4  Gabriel              pred   4.45  act   8  min  90
    3 XI     445  Thiaw                pred   3.95  act   6  min  90
    4 XI     202  Richards             pred   3.43  act   0  min  90
    5 XI     427  Mbeumo               pred   4.90  act  11  min  90  VC
    6 XI      68  Tavernier            pred   4.38  act   1  min  90
    7 XI     481  Anderson             pred   4.23  act   3  min  81
    8 XI     237  Ndiaye               pred   3.80  act   4  min  90
    9 XI      69  Scott                pred   4.03  act  12  min  86
   10 XI     411  Haaland              pred   5.32  act  13  min  90  C
   11 XI     106  Thiago               pred   4.08  act   2  min  90
   12 bench  497  Dubravka             pred   0.37  act   0  min   0
   13 bench  229  Tarkowski            pred   3.37  act  12  min  90
   14 bench  423  Shaw                 pred   3.38  act   2  min  72
   15 bench  272  Kusi-Asare           pred   0.24  act   0  min   0
```

Rank 7,094,513 → 6,163,114 (**+931,399 places**) on 79 pts, total 119.
Team value 1000 → 999 (**−0.1 this GW, −0.1 cumulative** from £100.0m); bank
0 → 10 (£1.0m), 1 transfer made — both consistent with Enzo → Tavernier.
`picks` for event 2 matches final.md's `picks:` block exactly (same 15 ids,
C 411, VC 427, no active chip), so every squad number above describes the
fielded team, not a plan.

## Misses

| id | name | pred | act | err | class | cause |
|---|---|---:|---:|---:|---|---|
| 229 | Tarkowski | 3.37 | 12 | +8.63 | VARIANCE | goal off 0.10 xG on top of a correctly-modelled dc 10 floor; benched |
| 69 | Scott | 4.03 | 12 | +7.97 | VARIANCE | goal + dc 15 + 3 bonus, both tails of a right process |
| 449 | Hall | 3.09 | 11 | +7.91 | MODEL | CS + dc 13 + 3 bonus — attacking full-backs with a DefCon floor are the band we under-predict |
| 411 | Haaland | 5.32 | 13 | +7.68 | VARIANCE | 2 goals off 0.66 xG; over-performance, not under-prediction |
| 427 | Mbeumo | 4.90 | 11 | +6.10 | MODEL | 1.76 xG at IPS(H) — attacking upside against a promoted club under-rated |
| 4 | Gabriel | 4.45 | 8 | +3.55 | VARIANCE | CS and dc 10 both landed; two modelled probabilities converging |
| 202 | Richards | 3.43 | 0 | −3.43 | VARIANCE | dc 6 against the DEF-10 threshold on a 1.08 ratio, no CS, plus a deduction |
| 68 | Tavernier | 4.38 | 1 | −3.38 | MODEL | dc 11 missed the MID-12 threshold by one action; DEF would have scored 2 |
| 129 | Ayari | 3.23 | 0 | −3.23 | MINUTES | p_start 0.88, zero minutes; INFORMATION unverifiable from the ledger |
| 426 | B.Fernandes | 5.66 | 23 | +17.34 | VARIANCE | hat-trick off 2.02 xG; not owned — a priced fade, not a selection miss |

## Captain and bench

Captain Haaland 13 (26 doubled); hindsight best in XI 13, **forgone 0** — optimal.
Bench stranded 14: Tarkowski 12 (goal + dc 10 + 2 bonus) and Shaw 2.
No auto-sub fired — all eleven starters logged ≥ 81' — so bench **order** was
never tested; the stranding traces to an XI near-tie (Richards 3.43 v
Tarkowski 3.37, a 0.06 gap), not an ordering defect.
Verdict: bench order correct within the information, realised cost 0. C8's pair
ordering was vindicated on outcome (Tarkowski 12 ahead of Shaw 2).

## Findings

- Aggregate bias +0.04 is **two offsetting errors, not accuracy**: conditional on playing we under-predict (LOW +0.64, ≥8.0 +5.67), conditional on not playing we over-predict (HIGH −0.07, <5.5 −0.16). Selection only reads the first number.
- The ≥8.0 band (n=11, bias +5.67, mae 6.05) is the ledger's largest signal and not one outlier — dropping B.Fernandes leaves +4.50 on n=10. Withheld as a level correction on power grounds; the GW4 re-test needs C10.
- Right-skew is the expected shape, not bias: 50 players err > +3 against 12 err < −3. EP is a mean drawn against a lumpy distribution.
- Minutes improved — brier 0.1030 this round against 0.1262 cumulative; expected starts 227.9 v 220 actual (3.5% high). The one recurring shape in the over-predicted block is p_start ≥ 0.79 with zero minutes (Senesi 0.90, Ayari 0.88, Alderete 0.79).
- DefCon 29/189 (15.3%) among 60'+ players, and the C3 position asymmetry is live and costing points: Tavernier's dc 11 scored 0 as a MID while Gabriel's and Tarkowski's dc 10 scored 2 each as DEFs.
- GW2's STATE block omits `chip:` and `chip_plan:` entirely; four earmarks (TC GW5, WC GW8, BB GW19, FH GW16) live only in prose, so `plan` compiled GW2 with no chip intent.
- 79 pts banked against 93 available from the same 15 — the whole gap is an XI/bench boundary decided inside 0.10 EP.
- `gap:` the ledger prints realised DefCon hits (29/189) with **no Σ P(hit)** over the same 189, so C2's GW4 level-and-slope test cannot be run from `calibrate`.
- `gap:` price-band and tier aggregates are this-round-only — `cumulative` carries just n / bias / mae / brier — so no band is power-testable across rounds.

## Corrections

| C# | Agent | Status | Evidence |
|---|---|---|---|
| C1 | A3 | satisfied | mapping held unchanged through GW2 as instructed; the instruction is spent |
| C2 | A3 | retired — moved to C10 | the sample it asks A3 to emit is arithmetic the ledger should carry, and no Σ P(hit) exists to test against |
| C3 | A3 | retired — moved to C9 | curve shape is an ep.py coefficient, not an A3 input; A3 is never asked to emulate arithmetic |
| C4 | A2 | revised — see C12 | GW1's evidence was defensive; GW2 adds the attacking side (Mbeumo 11 off 1.76 xG at IPS(H)) |
| C5 | A2, A4 | active | complied — GW2 deferred TC to GW5 on the fixture-independence test; binds again this cycle |
| C6 | A4, A5 | retired — satisfied | all 15 `picks:` lines emitted and they match the `picks` endpoint exactly |
| C7 | A3 | active | complied (Tavernier 0.879 ≥ the 0.85 floor); tier bias ordered LOW +0.64 / MED +0.12 / HIGH −0.07 |
| C8 | A4 | active | n=2. Pair ordering right (Tarkowski 12 v Shaw 2); the XI boundary went against us (Richards dc 6 → 0 v Tarkowski dc 10 → 12). Realised cost 0. Revisit GW4 as scheduled |

**C9 — CODE (fpl/ep.py): unify the DefCon probability curve across DEF, MID and
FWD — one functional form, with position entering only through the points
threshold (10 / 12).** Re-issue of C3, which was arithmetic misfiled as an A3
input. DEF bias −0.21 (n=205) against MID +0.26 (n=270) in the same round is a
0.47-point cross-position gap, and Tavernier's dc 11 scored zero where a
defender's dc 10 scored 2.

**C10 — CODE (fpl/calibrate.py): emit expected DefCon hits (Σ P(hit)) beside the
realised count, and carry the price-band and uncertainty-tier aggregates in the
cumulative block.** Both `gap:` lines above: 29/189 realised hits have nothing
to be tested against, so C2's GW4 level-and-slope test is currently unrunnable,
and the ≥8.0 band's +5.67 bias cannot be power-tested across rounds. Retires
C2's logging duty.

**C11 — A5 (finalizer): emit `chip:` and `chip_plan:` in every STATE block,
`chip: null` included, and treat a missing `chip:` as a REOPEN condition exactly
as C6 did for `picks:`.** GW2's block omits both while the prose carries four
earmarks; CLAUDE.md makes `chip_plan` the only machine-readable forecast, so the
GW5 Triple Captain earmark is invisible to every tool downstream.

**C12 — A2 (fixture-analyst): make the promoted-club ±15pp band two-sided —
apply it to the non-promoted side's attacking terms as well as to P(CS), and
never let the band's existence shrink the central attacking estimate of a player
facing a promoted club.** Revises C4. GW1's misses were defensive (HUL 2-0 MUN,
IPS 2-1 SUN against modelled clean sheets); GW2's second-largest squad miss is
attacking in the same class — Mbeumo 11 pts off 1.76 xG against 4.90 predicted.
The unified reading is inflated goal totals in **both** directions, not a one-way
defensive discount. C4's prohibition on a promoted-club fixture being a selected
player's largest EP term stands for defensive terms only.

## Running calibration stats

```
group             n    bias    mae
overall         616    0.04   1.19
DEF             205   -0.21   1.33
FWD              73    0.10   1.25
GKP              68   -0.17   0.73
MID             270    0.26   1.19
HIGH            480   -0.07   0.92
LOW              76    0.64   1.93
MED              60    0.12   2.47
5.5-7.9         212    0.11   1.51
<5.5            393   -0.16   0.89
>=8.0            11    5.67   6.05
minutes: brier 0.1030, expected starts 227.9, actual 220
defcon: 29/189 hits (players with 60'+)
cumulative (rounds 1,2): n=1216 bias=0.04 mae=1.33 brier=0.1262
```

Team value delta this GW **−0.1** (1000 → 999, from entry-history).
Cumulative team value delta **−0.1** against the £100.0m start.

## Carried into GW3

- **Premium under-prediction** — ≥8.0 band +5.67 on n=11, outlier-robust. Withheld on power; C10 is the GW4 instrument.
- **XI/bench boundary** — inside 0.10 EP two GWs running, benched player outscored both times (GW1 Thiaw/Shaw, GW2 Tarkowski/Richards). n=2, C8 binds, verdict GW4.
- **DefCon position asymmetry** — live and costing points; C9 binds, and until it ships A3 assumes C1's unchanged mapping.
- **MED-B dead bench, third GW** — Dubravka and Kusi-Asare 0 minutes again; Bench Boost unusable. GW3's free transfer is earmarked at the FWD half.
- **MED-D funding headroom** — bank exactly £1.0m against the strongest rise signal checked (Barry, net +104k). Named fallback stands; do not re-litigate.
- **MED-E template fades** — B.Fernandes 23 pts at 48.4% ownership; the fade held on funding, not EP. Second GW of evidence, verdict GW4 with LOW-4.
- **LOW-4 recency-chasing test** — still the GW4 retro's; Tavernier's 1 pt after a 10-pt GW1 is weak counter-evidence.
- **C5 binds this cycle** — any GW3 Triple Captain must clear on Haaland's fixture-independent EP alone.
