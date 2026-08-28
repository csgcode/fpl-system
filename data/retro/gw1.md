# GW1 Retro — predictions vs actuals

Completed GW **M = 1**, run during the **N = 2** cycle against snapshot
`data/raw/gw2/` (fetched 2026-08-28). Predictions from
`data/decisions/gw1/final.md`.

**Scoring gate:** bootstrap `events[id=1]` shows `finished: true`,
`data_checked: true` — bonus points final. Scoring proceeded.

## Scope limits

- `data/entry.json` `team_id` is **null**. GW1 was a paper decision, never
  entered on the FPL site, so `picks`, `entry` and `entry-history` were skipped.
  **There is no rank, bank or team-value actual to compare.** Everything below
  is computed against our own `final.md` and the public `actuals` feed.
- `data/retro/` was empty before this file, so the **trend check has nothing
  prior**. No error can yet be shown to persist ≥3 GWs, and therefore no
  systematic-bias rule is derived from trend in this retro. First trend check
  possible at GW3; first meaningful one at GW4.
- **n = 1 gameweek.** Every level correction below is deliberately withheld on
  power grounds. See C1/C2.

## Squad total

| Metric | Value |
|---|---|
| Predicted GW1 total | **54.66** (final.md states 54.65; rounding) |
| Actual GW1 total | **40** |
| Miss | **−14.66** |
| Starting XI predicted / actual | 48.35 / 38 |
| Captain (Haaland) contribution predicted / actual | 6.31 / 2 |
| Bench points stranded | 4 (Thiaw 3, Shaw 1) |
| Bench points *recoverable* | **0** — no auto-sub could fire |
| Auto-subs triggered | none — all 11 XI players logged ≥1 minute |
| Team value | 100.0 → 99.9 (**−0.1**, Anderson 6.5 → 6.4); cumulative −0.1 |

Team value is notional — no entry exists.

## Prediction vs actual, all 15

| Player | Pos | Role | EP | Act | Error | Min | Return | Note |
|---|---|---|---:|---:|---:|---:|---|---|
| Raya | GKP | XI | 4.27 | 6 | **+1.73** | 90 | CS | ARS 3-0 COV, 1 save |
| Gabriel | DEF | XI | 5.31 | 5 | −0.31 | 90 | CS | yellow card −1 |
| Tarkowski | DEF | XI | 3.64 | 6 | **+2.36** | 90 | CS | DefCon missed (9 vs T=10) |
| Richards | DEF | XI | 3.55 | 3 | −0.55 | 90 | DefCon | 2 conceded −1 |
| Mbeumo | MID | XI | 4.70 | 2 | **−2.70** | 90 | — | MUN lost 0-2 at HUL |
| Anderson | MID | XI | 4.43 | 2 | **−2.43** | 62 | — | DefCon missed (6 vs T=12) |
| Enzo | MID | XI | 4.00 | 1 | **−3.00** | 25 | — | **did not start** |
| Ndiaye | MID | XI | 3.84 | 9 | **+5.16** | 90 | assist, CS, DefCon, 1 bonus | 36 BPS |
| Scott | MID | XI | 3.68 | 2 | −1.68 | 90 | — | DefCon missed **by 1** (11 vs T=12) |
| Haaland (C) | FWD | XI | 6.31 | 2 | **−4.31** | 90 | — | 0.74 xG, no goal |
| Thiago | FWD | XI | 4.62 | 0 | **−4.62** | 82 | — | **penalty missed −2**, 1.00 xG |
| Shaw | DEF | Bench 1 | 3.41 | 1 | **−2.41** | 90 | — | 2 conceded −1 |
| Thiaw | DEF | Bench 2 | 3.26 | 3 | −0.26 | 90 | DefCon | 2 conceded −1 |
| Kusi-Asare | FWD | Bench 3 | 0.66 | 0 | −0.66 | 0 | — | unused, as modelled |
| Dubravka | GKP | Bench GK | 1.08 | 0 | −1.08 | 0 | — | unused, as modelled |

## The headline: the miss is almost entirely finishing variance

The XI generated **14.08 expected attacking points** (xG × goal value + xA × 3)
and returned **3**.

| Player | xG | xA | xAttPts | Actual attacking pts |
|---|---:|---:|---:|---:|
| Thiago | 1.00 | 0.08 | 4.24 | 0 |
| Mbeumo | 0.50 | 0.23 | 3.19 | 0 |
| Haaland | 0.74 | 0.02 | 3.02 | 0 |
| Ndiaye | 0.24 | 0.32 | 2.16 | 3 |
| Anderson | 0.00 | 0.25 | 0.75 | 0 |
| Gabriel / Tarkowski / Enzo / Scott | — | — | 0.72 | 0 |
| **XI total** | | | **14.08** | **3** |

Attacking variance = **−11.08**. Haaland's own 3.02 shortfall counts twice
under the captaincy, adding **−3.02**, for a captain-weighted attacking
variance of **−14.10** against a total squad miss of **−14.66**.

**Residual model error is −0.56 points.** Minutes, clean sheets, DefCon and
bonus — every non-finishing component — landed within half a point of
prediction in aggregate. This is the single most important finding in the
retro and it constrains everything below: there is almost no model error in
GW1 to correct, and the loudest-looking signals (FWD bias, DefCon) are noise
around a well-calibrated centre.

## Miss attribution

Misses with |error| > 3:

| Player | Error | Class | Reasoning |
|---|---:|---|---|
| Ndiaye | **+5.16** | **VARIANCE** (positive) | Assist, clean sheet, DefCon hit and a bonus point all landed in one match. His prior dc90 is 9.16 (ratio 0.76 of the MID threshold) — the DefCon hit was *against* his own prior, not evidence the model underrates him. 2.16 xAttPts → 3 actual. Do not chase. |
| Thiago | **−4.62** | **VARIANCE** | 1.00 xG — the highest of any player we owned — plus a won-and-missed penalty (−2). Process was correct: he got the chances and the spot kick. A penalty miss is the definition of outcome noise. |
| Haaland | **−4.31** | **VARIANCE** | 90 minutes, 0.74 xG, led the line as modelled. MCI won 2-1; he simply did not convert. |
| Enzo | **−3.00** | **MINUTES** | Started on the bench at Fulham, 25 minutes. p_start was 0.81 — **this exact risk was priced and accepted as MED-1 in final.md**. The risk realised; the process that priced it was sound. But see C7: the *uncertainty tag* was wrong. |

Notable sub-threshold misses:

| Player | Error | Class | Reasoning |
|---|---:|---|---|
| Mbeumo | −2.70 | **MODEL** | MUN modelled at 44% clean sheet away to promoted HUL; MUN lost 0-2. Assumption-grade promoted-club rating, flagged as MED-5. See C4. |
| Shaw | −2.41 | **MODEL** | Same fixture, same rating error. |
| Anderson | −2.43 | MINUTES + MODEL | Subbed at 62'; DefCon reached only 6 of 12 against a modelled P(hit) of 0.73 — his single largest EP term. |
| Tarkowski | +2.36 | VARIANCE (positive) | Clean sheet landed against a modelled 28% mean P(CS). |

No **INFORMATION** miss. `final.md` records the freshness gate passing at
2026-08-21T14:34:24Z with all 15 players `status: a`, `news: ""` and zero
deltas. Enzo's benching was not public pre-deadline. Nothing available was
missed.

### Captain delta

| | Player | Actual | Captain contribution |
|---|---|---:|---:|
| Chosen | Haaland | 2 | +2 |
| Hindsight-best in XI | **Ndiaye** | 9 | +9 |
| **Forgone** | | | **−7** |

**No correction warranted.** Haaland led the squad on GW1 EP by 1.61 and
generated 0.74 xG. Ndiaye ranked 9th of 11 on EP; captaining him was
unavailable to any sane process. This is exactly the case the discipline rule
protects — a captain who blanked on justified chances was still the right pick.

### Bench-order loss

**Realised loss: 0.** No auto-sub could fire — all eleven XI players logged
at least one minute, including Enzo's 25.

Recorded for calibration only: Thiaw (3) finished ahead of Shaw (1), inverting
the fixture-driven Shaw-over-Thiaw ordering. The ordering was wrong by 2 points
in hindsight but cost nothing, because it was never activated. See C8.

### Dead-bench confirmation

MED-2 realised exactly as priced: Kusi-Asare and Dubravka played **0 minutes
each** and returned 0. Two of four bench slots remain incapable of returning
points. **Bench Boost stays unusable** until the bench is rebuilt, consistent
with the GW19 earmark.

## Calibration commitment 1 — DefCon anchor mapping

The GW1 cycle recorded a suspicion that the v1 anchor mapping was **5–8pp low
below 0.85 × threshold**. Tested directly. **The hypothesis is refuted.**

Mechanics confirmed from the round-1 data: `defensive_contribution` =
CBI + tackles for DEF (threshold **10**), and CBI + tackles + recoveries for
MID/FWD (threshold **12**). A hit is worth **2 points**.

### Our six DefCon-relevant players

| Player | Pos | prior dc90 | ratio | v1 P(hit) | GW1 DC | Hit? |
|---|---|---:|---:|---:|---:|---|
| Tarkowski | DEF | 10.16 | 1.016 | 0.55 | 9 | ✗ |
| Richards | DEF | 9.91 | 0.991 | 0.55 | 16 | ✓ |
| Thiaw | DEF | 8.87 | 0.887 | 0.38 | 15 | ✓ |
| Anderson | MID | 13.60 | 1.133 | 0.73 | 6 (62') | ✗ |
| Scott | MID | 12.00 | 1.000 | 0.51 | 11 | ✗ (by 1) |
| Ndiaye | MID | 9.16 | 0.763 | not itemised (≈0.13–0.30) | 12 | ✓ |
| **Σ predicted** | | | | **2.85 – 3.02** | | **3 actual** |

Individual assignments were wrong in three of six cases, but the **aggregate is
essentially exact**.

### League-wide check

Every outfield player with ≥900 prior-season minutes and ≥80 GW1 minutes
(n = 65 across DEF and MID), bucketed by dc90 ÷ threshold, with Wilson 95%
intervals on the observed rate:

| Group | n | hits | v1 pred | actual | delta | 95% CI | v1 inside CI? |
|---|---:|---:|---:|---:|---:|---|---|
| DEF below 0.85T | 18 | 1 | 0.186 | 0.056 | −13.0pp | [0.010, 0.258] | **yes** |
| DEF ≥ 0.85T | 16 | 10 | 0.458 | 0.625 | +16.7pp | [0.386, 0.815] | **yes** |
| DEF all | 34 | 11 | 0.314 | 0.324 | **+1.0pp** | [0.191, 0.492] | **yes** |
| MID below 0.85T | 27 | 4 | 0.132 | 0.148 | +1.7pp | [0.059, 0.325] | **yes** |
| MID ≥ 0.85T | 4 | 3 | 0.456 | 0.750 | +29.4pp | [0.301, 0.954] | **yes** |
| MID all | 31 | 7 | 0.173 | 0.226 | **+5.2pp** | [0.114, 0.398] | **yes** |
| Pooled below 0.85T | 45 | 5 | 0.153 | 0.111 | **−4.2pp** | [0.048, 0.235] | **yes** |
| Pooled ≥ 0.85T | 20 | 13 | 0.458 | 0.650 | **+19.2pp** | [0.433, 0.819] | **yes** |
| Pooled all | 65 | 18 | 0.247 | 0.277 | +3.0pp | [0.183, 0.396] | **yes** |

Findings:

1. **The suspected error does not exist, and its sign is backwards.** Below
   0.85 × threshold — the exact band the commitment flagged as 5–8pp *low* —
   v1 is if anything **4.2pp high** (pooled).
2. **Aggregate calibration is good.** DEF +1.0pp, MID +5.2pp, pooled +3.0pp.
3. **What the data weakly suggests instead is a shape error, not a level
   error.** v1 looks too *flat*: under by ~19pp at ratio ≥0.85 and over by
   ~4pp below it. The curve needs more slope through the threshold.
4. **Nothing is statistically distinguishable from noise.** The v1 prediction
   lies inside the 95% interval in **every single band**. One gameweek has no
   power to recalibrate a probability mapping.

**Decision: the mapping is NOT corrected.** See C1, C2.

### Cross-position shape inconsistency (new finding)

Reconstructing the v1 curve from the itemised analysis notes — 111 distinct
DEF and 38 distinct MID (metric → P(hit)) pairs — shows the two positions use
**different functional forms**:

| ratio | DEF v1 | MID v1 |
|---:|---:|---:|
| 0.80 | 0.24 | 0.30 |
| 0.90 | 0.38 | ~0.40 |
| 1.00 | 0.55 | ~0.51 |
| 1.13 | 0.55 (capped) | ~0.73 |

DEF is a four-step band function capped at 0.55; MID is continuous and keeps
rising. At ratio ≥1.10 a defender is scored **18pp below** a midfielder on the
identical ratio, with no stated justification. This compounds the still-open
LOW-4 cross-position scale inconsistency. See C3.

## Calibration commitment 2 — Coventry defensive rating (GW3 TC gate)

The GW3 Triple Captain earmark (Haaland, MCI **v** COV) is gated on COV's
assumption-grade defensive rating. GW1 evidence, recorded for the fixture
analyst and optimizer:

| COV GW1 | Value | League rank |
|---|---|---|
| Result | ARS 3-0 COV (away) | — |
| xG conceded | **1.88** | 7th-highest of 20 |
| xG created | **0.21** | **lowest of 20** |
| ARS xG in the same match | 1.88 (scored 3) | — |

Reading:

- **COV's attack is confirmed dire** — 0.21 xG is the worst in the league.
- **COV's defence is not yet confirmed soft.** 1.88 xG conceded away to the
  second-rated team is unremarkable. **The 3-0 scoreline overstates it**: ARS
  converted 3 goals from 1.88 xG, so finishing overperformance, not defensive
  collapse, produced the margin.
- **GW2 will not resolve this.** COV's GW2 fixture is **COV v HUL** —
  promoted against promoted. It cannot test COV's defence against an elite
  attack. At the GW3 deadline the TC decision will still rest on **one**
  elite-opposition data point.

**Gate status: NOT cleared.** See C5.

## Corrections

Numbered, imperative, binding on the named agents.

**C1 — A3 (player-analyst): keep the v1 DefCon anchor mapping unchanged for
GW2.** The "5–8pp low below 0.85 × threshold" hypothesis is refuted: pooled
below-threshold error is −4.2pp (wrong sign), aggregate error is +3.0pp, and
the v1 value sits inside the 95% Wilson interval in every ratio band. Do not
shift DefCon levels on one gameweek of data.

**C2 — A3: log the DefCon calibration sample every gameweek and re-test at
GW4.** Emit per qualifying player (≥900 prior minutes, ≥80 GW minutes):
position, prior dc90, ratio to threshold, v1 P(hit), realised DC count, hit
flag. Pool across gameweeks. At GW4 (pooled n ≈ 250) test the **slope**
hypothesis, not the level one — GW1 point estimates suggest v1 is too flat.
Recalibrate **only if** the ≥0.85 band still shows ≥15pp under-prediction
*and* the v1 value falls outside the 95% interval.

**C3 — A3: unify the DefCon curve shape across positions before GW2 analysis.**
DEF currently uses a four-step band function capped at 0.55 while MID uses a
continuous curve reaching 0.73, so an identical ratio scores up to 18pp lower
for a defender. Pick one functional form and apply it to DEF, MID and FWD.
Resolve alongside the still-open LOW-4 (`1/ATT_club` applied weighted for MID,
flat for DEF/FWD) — both are the same class of defect.

**C4 — A2 (fixture-analyst): downgrade confidence in promoted-club ratings; do
not upgrade it.** GW1: HUL beat MUN 2-0 at home against our modelled 44% MUN
clean sheet, and IPS beat SUN 2-1. Two of three promoted clubs won. Carry an
explicit ±15pp band on every promoted-club-derived P(CS) until that club has
3+ played fixtures, and **never let a promoted-club fixture be the single
largest EP term for a selected player** — that condition held for Gabriel,
Raya, Mbeumo and Shaw in GW1 and produced both MODEL misses.

**C5 — A2 and A4 (squad-optimizer): the GW3 Triple Captain gate is NOT cleared,
and GW2 cannot clear it.** COV conceded 1.88 xG away at ARS (7th-highest of 20)
and the 3-0 scoreline is inflated by ARS converting 3 from 1.88 xG. COV's GW2
opponent is HUL — promoted v promoted — which cannot test COV against an elite
attack. **Justify any GW3 TC on Haaland's own fixture-independent EP alone. If
the case requires COV's defensive rating to clear, defer the chip.**

**C6 — A4 and the finalizer: `final.md` MUST emit the `picks:` list in the
STATE block.** `data/decisions/gw1/final.md` omits it entirely. Consequences:
`set-lineup --from-final` and `make-transfers --from-final` would both fail to
strict-parse GW1 state, and this retro had to reconstruct all 15 element ids by
name-matching against bootstrap. Emit all 15 lines in the exact CLAUDE.md
format — positions 1–11 XI, 12–15 bench in auto-sub order, position 12 the
backup GK, exactly one captain and one vice, both in the XI. **Treat a missing
or malformed `picks:` block as a REOPEN condition, not a cosmetic defect.**

**C7 — A3: bind the uncertainty tag to p_start.** Enzo and Mbeumo were both
tagged **LOW** uncertainty at p_start 0.81. The optimizer's captain/selection
discount tiers are LOW 1.00 / MED 0.92 / HIGH 0.80, so a sub-0.85 p_start
player received **no rotation discount at all**, while `final.md` MED-1
simultaneously named those two as the squad's live rotation risk — the tag and
the stated risk contradicted each other. Rule: **p_start < 0.85 → MED at best;
p_start < 0.70 → HIGH.** Enzo's −3.00 is the realised cost.

**C8 — A4: break near-tied bench orderings on DefCon floor share, not on
fixture.** Shaw (EP 3.41, DefCon ratio 0.63) was benched ahead of Thiaw
(EP 3.26, ratio 0.89) on a fixture read; Thiaw outscored him 3-1. When two
bench candidates are within 0.25 EP, prefer the higher DefCon floor share —
floor is fixture-independent, and the auto-sub scenario is precisely the
high-variance case where a floor is worth most. **Low confidence, n = 1,
realised cost 0** — apply as a tie-break only, and revisit at GW4.

## Running calibration stats

Cumulative = GW1 only; this is the first retro.

| Group | n | Predicted Σ | Actual Σ | Bias | Mean error | MAE |
|---|---:|---:|---:|---:|---:|---:|
| All 15 | 15 | 56.76 | 42 | −14.76 | −0.98 | 2.22 |
| Starting XI | 11 | 48.35 | 38 | −10.35 | −0.94 | 2.62 |
| Bench | 4 | 8.41 | 4 | −4.41 | −1.10 | 1.10 |
| GKP | 2 | 5.35 | 6 | +0.65 | +0.33 | 1.41 |
| DEF | 5 | 19.17 | 18 | −1.17 | −0.23 | 1.18 |
| MID | 5 | 20.65 | 16 | −4.65 | −0.93 | 2.99 |
| FWD | 3 | 11.59 | 2 | −9.59 | −3.20 | 3.20 |

**Read these with the variance finding above, not against it.** FWD shows the
largest apparent high bias (−3.20 mean error), but both forwards who played
generated more xG than any other squad member — Thiago 1.00, Haaland 0.74 —
and one of them missed a penalty. **Concluding "FWD EPs are biased high" after
one gameweek would be exactly the overcorrection the discipline rule forbids.**
Revisit at GW6+ per the 6-gameweek calibration horizon.

### Minutes model

| Metric | Value |
|---|---|
| Expected starts (Σ p_start) | 12.06 |
| Actual starts | 12 |
| Delta | **−0.06** |
| Brier score (start / no-start) | **0.0622** |
| Directional misses | 1 (Enzo) |

The minutes model is **well calibrated in aggregate** — expected and actual
starts agree to within 0.06 of a player. Both zero-minute players (Dubravka
0.37, Kusi-Asare 0.08) were correctly modelled as non-starters. The single
directional miss, Enzo, was pre-priced as MED-1. C7 addresses the tagging
defect, not the probability.

### Team value

| | This GW | Cumulative |
|---|---:|---:|
| Team value delta | −0.1 | −0.1 |

Anderson 6.5 → 6.4 was the only price move across the 15. Notional — no entry
exists.

## Carried into GW2

- **MED-2 dead bench confirmed** — 2 of 4 slots returned 0 from 0 minutes.
  Bench Boost remains unusable.
- **MED-5 promoted-club ratings** — partially realised as a MODEL miss on the
  HUL fixture (Mbeumo, Shaw). C4 binds.
- **MED-4 DefCon exposure** — tested and cleared for now; the mapping is
  aggregate-unbiased. C1–C3 bind.
- **LOW-4 cross-position scale inconsistency** — still open, now compounded by
  the DefCon curve-shape finding. C3 binds.
- **MED-1 rotation risk** — realised on Enzo. C7 binds.
- **MED-3 template fades** — no GW1 verdict; Ndiaye (16.0% owned) was our
  differential and it paid. Revisit when João Pedro's GW4 arrives.
