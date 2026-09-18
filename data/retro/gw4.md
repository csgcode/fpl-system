# GW4 Retro

## Squad

```
squad XI (captain doubled): predicted 55.20, actual 69; bench stranded 7
captain: Haaland 9 pts; hindsight best in XI: Raya 14 (forgone 5)
squad rows (slot role id name pred act min):
    1 XI       1  Raya                 pred   3.78  act  14  min  90
    2 XI       4  Gabriel              pred   5.05  act   9  min  90  VC
    3 XI     229  Tarkowski            pred   4.33  act   8  min  90
    4 XI     202  Richards             pred   3.79  act   2  min  90
    5 XI      68  Tavernier            pred   5.00  act   8  min  82
    6 XI     427  Mbeumo               pred   4.82  act   2  min  90
    7 XI      69  Scott                pred   4.15  act   4  min  90
    8 XI     237  Ndiaye               pred   4.04  act   1  min  45
    9 XI     411  Haaland              pred   6.00  act   9  min  90  C
   10 XI     106  Thiago               pred   4.38  act   1  min  90
   11 XI     249  Barry                pred   3.87  act   2  min  90
   12 bench  497  Dubravka             pred   0.15  act   0  min   0
   13 bench  481  Anderson             pred   3.85  act   5  min  90
   14 bench  445  Thiaw                pred   3.21  act   2  min  90
   15 bench  423  Shaw                 pred   1.46  act   0  min   0
```

Rank 5,635,925 → 5,362,185, up 273,740 on 69 points; season total 243.
Team value 999 → 996: **−0.3** this GW, cumulative **−0.4** against £100.0m.
`picks` (event 4) matches final.md's `picks:` block exactly — 15 ids, captain 411, vice 4, bench 497/481/445/423 — so the ledger scores the fielded XI, not a plan.

## Misses

| id | Name | Pred | Act | Err | Class | Cause |
|---:|---|---:|---:|---:|---|---|
| 1 | Raya | 3.78 | 14 | +10.22 | VARIANCE | ARS clean sheet at SUN (A) plus 3 bonus at 38 BPS, and 5 points beyond appearance/CS/bonus from keeper save returns |
| 4 | Gabriel | 5.05 | 9 | +3.95 | VARIANCE | the same ARS clean sheet as row 1 plus a DefCon hit at dc 11 (DEF threshold 10) — not an independent miss |
| 229 | Tarkowski | 4.33 | 8 | +3.67 | VARIANCE | EVE clean sheet at TOT (A) with 2 bonus; dc 8 fell short of the DEF threshold |
| 237 | Ndiaye | 4.04 | 1 | −3.04 | MINUTES | started as modelled (p_start 0.93) but withdrawn at 45' on dc 10 — a 90-minute pace clear of MID's 12 |
| 106 | Thiago | 4.38 | 1 | −3.38 | VARIANCE | 90 minutes at BOU (A) for xG 0.11, xA 0.03, 3 BPS — no chances created rather than chances missed |
| 203 | Canvot | 3.93 | 0 | −3.93 | MINUTES | p_start 0.90, 0 minutes |
| 200 | Lacroix | 4.88 | 1 | −3.88 | MINUTES | p_start 0.90, 4 minutes |
| 94 | Schade | 4.00 | 15 | +11.00 | VARIANCE | 2 goals off xG 0.21 |
| 116 | Dunk | 3.09 | 12 | +8.91 | VARIANCE | 1 goal off xG 0.03 |
| 492 | Awoniyi | 4.00 | −2 | −6.00 | VARIANCE | dismissed at 52', −5 BPS |

## Captain and bench

Haaland 9 (1 goal off xG 0.87, 3 bonus) doubled to 18; hindsight best in XI Raya 14, forgone 5. Correct process — the only ex-ante rival, Gabriel at 5.05 against 6.00, also returned 9.
Bench stranded 7 (Anderson 5, Thiaw 2); all eleven XI players appeared, so no auto-sub was available and nothing was recoverable by ordering.
Bench order correct — Anderson at slot 13 was also the top bench scorer.
C8 did not bite: gaps 0.64 and 1.75, both outside the 0.25 band.

## Findings

The XI beat is one fixture. Single-counted, the XI predicted 49.20 and scored 60; Raya alone is +10.22 of the +10.8 residual and Gabriel's +3.95 is the same ARS clean sheet counted twice. Net of that fixture the XI landed within a point of prediction, consistent with the round's pool bias of +0.09.

Start over-prediction is now a three-round trend and widening: expected minus actual starts +7.9 (r2), +8.9 (r3), +10.7 (r4), with Brier 0.1030 → 0.1037 → 0.1097. Canvot and Lacroix both carried p_start 0.90 for 0 and 4 minutes. The trend rule is met; C18 binds, and C13 would localise it by band.

Promoted-club selection: ARS at SUN (A) was a selected player's promoted-club fixture and the clean sheet landed for +14.17 across Raya and Gabriel, the round's two largest positive residuals. Whether C4's defensive prohibition was breached in selecting them cannot be determined here.

gap: the ledger's squad rows carry no per-term EP breakdown, so C4/C12 — which bind on which term is a selected player's largest — cannot be audited from `calibrate` output. C17 raises it.

gap: the ledger scores start/no-start only, so Ndiaye's correctly-predicted start at 45 minutes books as a minutes-model success carrying a −3.04 residual with no attribution path. C19 raises it.

Instrumentation already filed and still unshipped blocked three further tests: 31/174 realised DefCon hits with no Σ P(hit) to test against and no cumulative tier or price-band aggregate (C10), and no named non-squad rows, leaving the template-fade question (MED-E) unrunnable a third round — João Pedro, Calafiori, B.Fernandes, Szoboszlai and Rogers appear in no permitted output (C13).

Premium under-prediction is closed: the ≥8.0 band reads +5.67 (n=11), −0.22 (n=11), +0.30 (n=8) across rounds 2–4. Three rounds, no replication; C15's answer stands and the carry retires.

Team value fell 0.3 in one gameweek, the season's largest single-GW bleed, against the exact exposure F2 named — the GW5 payoff needs £14.0 out of a £14.2 sale. It must be re-derived on live prices, never carried as a commitment.

## Corrections

| C# | Agent | Status | Evidence |
|---|---|---|---|
| C1 | A3 | retired — satisfied | closed at GW2; carried verbatim |
| C2 | A3 | retired — moved to C10 | carried verbatim |
| C3 | A3 | retired — moved to C9 | carried verbatim |
| C4 | A2 | revised — see C12 | carried verbatim |
| C5 | A2, A4 | active | complied — the GW4 3xc gate was refused on Haaland's own fixture (λ_att 1.80, EP 6.00 below his 6.32 window mean) and the earmark moved to GW9; his 9 points vindicate the deferral |
| C6 | A4, A7 | retired — satisfied | carried; GW4's 15 `picks:` lines match the `picks` endpoint again |
| C7 | A3 | active | complied — 13 rows LOW at p_start ≥ 0.88, Dubravka HIGH at 0.04 and Shaw HIGH at 0.62, both benched; the tag tracked p_start everywhere |
| C8 | A4 | active | did not bite — bench gaps 0.64 and 1.75 sit outside the 0.25 band. The scheduled revisit duty ended at GW3; the tie-break itself stands, and C20 widens its scope |
| C9 | CODE | active — unshipped | the two-curve defect stands but bias still refuses to size it: DEF +0.06 (n=143) v MID −0.03 (n=200), a 0.09 gap against −0.47 (r2) and +0.38 (r3). Gabriel's dc 11 hit at DEF's 10 while Ndiaye's dc 10 missed at MID's 12 |
| C10 | CODE | active — unshipped | fourth round of the same two consequences: 31/174 realised DefCon hits with no Σ P(hit), and the cumulative block still prints only n/bias/mae/brier, so the tier and price-band series cannot be pooled |
| C11 | A7 | active | complied — `chip: null`, `chips_used: []` and four `chip_plan` rows all emitted in GW4's STATE block |
| C12 | A2 | active — untested | no promoted-club EP term can be identified from the ledger (see C17); the one promoted-club fixture in the XI resolved in our favour, which tests nothing |
| C13 | CODE | active — unshipped | both consequences recur: start over-prediction reached +10.7 with no band attribution, and the top-8 tails again hide every named player the template-fade test needs |
| C14 | A4 | active | complied — every GW4 single and pair was scored on both readings, and the sign-flip rule is what banked the transfer; round 4 gave it no new test |
| C15 | A4 | active — answered | the ≥8.0 band's third reading (+0.30, n=8) neither replicates nor reverses; the premium restructure stays answered NO |
| C16 | A4 | active | complied — final.md orders the XI and bench on undiscounted EP and confines the multipliers to the captain choice. Realised cost 0; every XI row was LOW |

**C17 — CODE (fpl/calibrate.py): carry each squad row's largest EP term, by
name and value, in the round block.** C4 and C12 bind selection on which term
is a selected player's largest, and that is unauditable from the ledger: GW4
fielded Raya and Gabriel on ARS at SUN (A), a promoted-club fixture, for the
round's two largest positive residuals (+10.22 and +3.95), and this retro
cannot say whether the clean-sheet term was their largest without opening
analysis files it may not read.

**C18 — A3 (player-analyst): stop defaulting a nominal first-choice starter to
p_start ≥ 0.88 — cap p_start at 0.90 absent same-week confirmation, and reserve
≥ 0.93 for a player with an unbroken start streak across the three most recent
rounds.** Σ p_start has exceeded actual starts for three pool-wide rounds and
the gap is widening — +7.9, +8.9, +10.7 — with Brier moving 0.1030 → 0.1037 →
0.1097. Canvot and Lacroix both held p_start 0.90 for 0 and 4 minutes. The
3-round trend rule is met on n ≈ 680 player-rounds per round; this corrects the
level only, and C13 remains the instrument that would localise it by band.

**C19 — CODE (fpl/calibrate.py): score minutes as well as starts — emit
expected versus actual minutes beside expected versus actual starts, in both
the round and cumulative blocks.** Ndiaye started exactly as modelled
(p_start 0.93) and was withdrawn at 45' on dc 10, a pace clear of MID's
threshold, for 1 point against 4.04 predicted. The Brier resolves start versus
no-start only, so that row books as a minutes-model success while carrying the
squad's second-largest negative residual, with no attribution path.

**C20 — A4 (squad-optimizer): apply C8's near-tie DefCon-floor tie-break at the
XI/bench boundary, not only within the bench ordering.** GW4's slot 11 was a
0.02 EP gap, far inside C8's 0.25 band, between a forward with no floor term
and the bench's highest DefCon share (0.26); C8 was invoked only for slots
12–15 and the boundary was settled on other grounds. The benched player scored
5 against 2, realised cost 3, and the boundary has now gone against us in three
of four rounds. The argument is strictly stronger here than inside the bench: a
bench ordering pays out only if an auto-sub fires, an XI boundary always does.

## Running calibration stats

```
group             n    bias    mae
overall         426    0.09   1.78
DEF             143    0.06   2.16
FWD              47    0.42   2.07
GKP              36    0.46   1.72
MID             200   -0.03   1.46
HIGH            252    0.08   1.15
LOW             111    0.30   2.66
MED              63   -0.22   2.78
5.5-7.9         151    0.27   2.22
<5.5            267   -0.01   1.51
>=8.0             8    0.30   2.51
minutes: brier 0.1097, expected starts 227.7, actual 217
defcon: 31/174 hits (players with 60'+)
cumulative (rounds 1,2,3,4): n=2068 bias=0.05 mae=1.47 brier=0.1182
```

Team value delta this GW **−0.3** (999 → 996, from entry-history).
Cumulative team value delta **−0.4** against the £100.0m start.

## Carried into GW5

- **Start over-prediction** — three rounds, widening to +10.7. C18 binds now; C13 is the band instrument and is unshipped.
- **Ledger instrumentation** — C10, C13, C17 and C19 all unshipped; together they block the DefCon slope test, the tier/band pooling, the C4/C12 compliance audit and all minutes attribution.
- **DefCon position asymmetry** — structural and unsized; C9 binds, and until it ships A3 holds C1's mapping unchanged.
- **XI/bench boundary** — against us in three of four rounds, realised cost 3 this GW. C20 binds from GW5.
- **Dead GK2 and DEF5** — Dubravka 0 minutes a fifth GW, Shaw 0 minutes at 75%. F4's repair is routed to GW5 headroom or the GW8 wildcard; no C binds it.
- **Price bleed against F2** — −0.3 this GW puts the £14.0-from-£14.2 pair at risk; re-derive on live prices, never as a commitment.
- **Template fades (MED-E)** — unrunnable a third round; C13 is the instrument.
- **Triple Captain GW9 earmark** — C5 binds: justify on Haaland's fixture-independent EP alone, or defer again.
