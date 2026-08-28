# GW2 — Goalkeeper EP (GW2–GW7)

Season 2026/27 | GW2 deadline 2026-08-28T17:30:00Z | snapshot `data/raw/gw2/` (fetched 09:45:31Z, age < 1h)
Regime: **IN-SEASON, n = 1** | corrections applied: `data/retro/gw1.md` **C1**, **C4**, **C7**
Pool scored: **all 68 goalkeepers** (67 last cycle + Di Gregorio); 57 carry a non-zero start probability.
Full numbers in `players-GKP.json`. Supersedes `data/analysis/gw1/players-GKP.md`.

## The one thing that changed: every depth chart resolved at once

GW1 was played, and **all twenty clubs named a keeper who went the full 90**. The GW1 file
escalated four unresolved depth charts (TOT, LEE, COV, IPS) and two minutes risks (Henderson,
Pope/Horníček). Five of those six are now settled by observation, and **three resolved against
the GW1 model**:

| Club | GW1 model favourite | Who actually started | GW1 p_start of the starter | Read |
|---|---|---|---|---|
| **NEW** | Pope (.76) | **Horníček** (£5.0) | .19 | The GW1 ESCALATION was right in *direction* and far too timid in size. Pope played 0 minutes with no injury flag. |
| **AVL** | Martinez (.84) | **Bizot** (£4.5) | .06 | Not flagged at all — the only genuine blind spot. Martinez: 0 minutes, `status: a`, `news: ""`. |
| **IPS** | Walton (.38) | **Scherpen** (£4.5) | .26 | Correctly flagged unresolvable; the age/experience tie-break was noise, as stated. |
| TOT | Kinsky (.58) | Kinsky | .58 | Resolved as modelled. Dubravka 0 minutes. |
| LEE | Trafford (.70) | Trafford | .70 | Resolved as modelled — 9 pts, CS, 2 bonus. Price beat prior minutes. |
| COV | Rushworth (.45) | Rushworth | .45 | Resolved as modelled. |
| CRY | Henderson (.68 ramp) | Henderson | .68 | Ankle flag **cleared**: `chance_of_playing` 75 → 100, played 90. |

**Minutes-model scorecard for GKP, GW1: 17 of 20 clubs' starters were the model's favourite.**
The three misses share one shape — a cheaper or newer keeper displacing a more expensive
incumbent — and all three are now priced accordingly.

`transfers_in_event` / `transfers_out_event` are **non-zero for the first time** (they were
identically zero pre-season, per the GW1 data trap). Market flow is now a usable weak signal and
is carried in the JSON as `transfers_net_event`. It corroborates the reads above: Martinez
**−38.6k**, Pope **−8.3k**, Dubravka **−25.2k**, Kinsky **−40.5k**; Tzolakis **+77.9k** and
Trafford **+43.7k** are the round's chase trades.

## What the optimizer should take from this

| # | Claim | Confidence |
|---|---|---|
| 1 | **Raya (£6.0) is still #1 at 22.37 EP6 — and his window is now C4-clean.** ARS's GW2–7 run contains **no promoted opposition at all**, so not one of his six fixtures carries the ±15pp band. In GW1 his largest fixture was COV(H), which is exactly the exposure C4 was written about. | HIGH |
| 2 | **The Raya premium has narrowed by 29%.** Raya − Verbruggen was +3.83 EP6 for £1.5m at GW1; it is **+2.73** now (1.82 pts per £m). The gap moved because Verbruggen's window improved (+1.04), not because Raya got worse (−0.06). | HIGH |
| 3 | **Verbruggen (£4.5, BHA) is the best value in the pool** — 4.36 EP/£m, the highest of all 68, on the highest p_start (.947). BHA's DEFW improved to 0.91 after holding Villa to 0.29 xG. | HIGH |
| 4 | **Our GK2 slot has collapsed.** Dubravka falls **7.10 → 2.38 EP6 (−4.72)**, the largest single downgrade in the pool, because Kinsky started and he did not. This is the GK half of the retro's MED-2 dead-bench finding, and it is now confirmed rather than assumed. | HIGH |
| 5 | **Petrović is no longer a nailed £4.5 enabler.** Di Gregorio joined BOU *after* the GW1 deadline at £4.5 — level with the incumbent. That is structurally the identical setup to Pope/Horníček, which just resolved against the incumbent. p_start decays .90 → .70; EP6 falls 16.93 → 14.77. | MED |
| 6 | **Do not chase Tzolakis's 10 points.** +77.9k net transfers in is the largest GK flow in the game, but every HUL fixture is band-flagged and his EP6 range is **13.42–19.93**. Buying him is buying one match. | HIGH |
| 7 | **C4 trips exactly once in this pool: Donnarumma, GW3 v COV(H).** See the C4 section — it is a flag on him alone, not on the position. | HIGH |

## Top 15 by EP over GW2–GW7

`pS` = mean P(starts). `Δ` = EP6 vs the GW1 file — **this mixes a one-gameweek window roll with
model and p_start updates**, so read it as "how the asset moved", not as a model error.
`nailed` = EP6 recomputed at a flat p_start of .93, isolating depth-chart risk from fixture quality.

| # | Player | Tm | £ | pS | GW2 | GW3 | GW4 | GW5 | GW6 | GW7 | **EP6** | Δ | EP/£m | nailed | Unc |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Raya | ARS | 6.0 | .94 | 3.77 | 3.42 | 4.03 | 3.59 | 3.80 | 3.76 | **22.37** | −0.06 | 3.73 | 22.10 | LOW |
| 2 | Lammens | MUN | 5.0 | .92 | 3.70 | 3.29 | 2.99 | 3.47 | 3.66 | 3.16 | **20.27** | −0.52 | 4.05 | 20.42 | LOW |
| 3 | Donnarumma | MCI | 5.5 | .90 | 3.05 | 3.87 | 3.04 | 3.69 | 2.89 | 3.58 | **20.13** | +1.17 | 3.66 | 20.93 | MED |
| 4 | Kelleher | BRE | 5.0 | .94 | 3.33 | 3.84 | 3.28 | 3.13 | 3.35 | 3.17 | **20.10** | +0.91 | 4.02 | 19.96 | LOW |
| 5 | Verbruggen | BHA | 4.5 | .95 | 2.88 | 3.37 | 3.67 | 3.12 | 3.47 | 3.12 | **19.64** | +1.04 | **4.36** | 19.29 | LOW |
| 6 | Pickford | EVE | 5.5 | .95 | 2.96 | 3.07 | 3.32 | 3.47 | 3.55 | 2.77 | **19.14** | −0.55 | 3.48 | 18.67 | LOW |
| 7 | Henderson | CRY | 5.0 | .91 | 2.88 | 3.34 | 3.51 | 3.05 | 3.33 | 2.96 | **19.08** | **+2.01** | 3.81 | 19.46 | LOW |
| 8 | Leno | FUL | 4.5 | .94 | 3.28 | 2.89 | 2.71 | 2.89 | 3.17 | 3.61 | **18.56** | +0.77 | 4.12 | 18.31 | LOW |
| 9 | Roefs | SUN | 5.0 | .93 | 3.49 | 2.86 | 3.02 | 2.83 | 3.13 | 2.95 | **18.28** | −0.96 | 3.65 | 18.21 | LOW |
| 10 | Sels | NFO | 5.0 | .88 | 2.73 | 3.36 | 3.02 | 3.55 | 2.75 | 2.82 | **18.22** | +1.07 | 3.65 | 19.18 | MED |
| 11 | Sánchez | CHE | 5.0 | .89 | 3.08 | 2.76 | 3.67 | 2.67 | 2.98 | 2.99 | **18.14** | +0.06 | 3.63 | 18.88 | MED |
| 12 | A.Becker | LIV | 5.5 | .83 | 3.23 | 3.12 | 3.29 | 2.73 | 2.58 | 2.50 | **17.44** | +0.46 | 3.17 | 19.60 | MED |
| 13 | Trafford | LEE | 5.0 | .85 | 2.85 | 2.94 | 3.08 | 2.90 | 2.74 | 2.93 | **17.43** | **+4.01** | 3.49 | 19.00 | MED |
| 14 | Tzolakis | HUL | 4.5 | .86 | 2.99 | 2.77 | 2.49 | 2.60 | 2.78 | 2.78 | **16.42** | **+5.44** | 3.65 | 17.83 | HIGH |
| 15 | Kinsky | TOT | 4.5 | .86 | 2.61 | 2.64 | 2.73 | 2.73 | 2.40 | 3.07 | **16.19** | **+5.11** | 3.60 | 17.58 | MED |

Next five: Horníček NEW £5.0 **15.05** (+11.08) · Petrović BOU £4.5 **14.77** (−2.16) ·
Rushworth COV £4.5 **14.74** (+6.29) · Scherpen IPS £4.5 **13.54** (+8.66) · Bizot AVL £4.5 **9.55** (+8.34).

**Read the big positive deltas correctly.** Horníček +11.08, Scherpen +8.66, Bizot +8.34,
Rushworth +6.29 and Tzolakis +5.44 are almost entirely *p_start* moves, not fixture or scoring
moves — these are the keepers whose depth charts resolved in their favour. Their `nailed` column
shows how little of it is fixture quality: every one of them sits at 17.3–17.8 when the minutes
question is removed, i.e. squarely mid-table.

## Nailed cheap beats rotating premium

Sharper this week than last, because three keepers in the £4.5–£5.5 band just lost or diluted
their claim on the shirt.

| Cheap, nailed | Rotating, dearer | EP6 gap | Price gap | Verdict |
|---|---|---|---|---|
| Verbruggen £4.5 (pS .95) | **Petrović £4.5 (pS .78)** | **+4.87** | **£0** | Same price, 17pp more starting probability. Last week these two were separated by 1.67; the Di Gregorio arrival tripled the gap. The clearest case in the pool. |
| Verbruggen £4.5 (pS .95) | Horníček £5.0 (pS .75) | **+4.59** | −£0.5m | Horníček's per-start rate is fine (3.36); he is capped by the new-signing rule until two consecutive 60'+ starts. |
| Verbruggen £4.5 (pS .95) | A.Becker £5.5 (pS .83) | **+2.20** | **−£1.0m** | Cheap wins on both axes, and the gap **widened** from +1.62. LIV's defence is a GW2–4 asset only (−16.7pp from GW5). |
| Leno £4.5 (pS .94) | Trafford £5.0 (pS .85) | +1.13 | −£0.5m | Trafford has now earned his price, so this is no longer a mismatch — just a mild one. |
| Kelleher £5.0 (pS .94) | Donnarumma £5.5 (pS .90) | −0.03 | −£0.5m | A dead heat. Take the £0.5m and avoid Donnarumma's C4 exposure. |
| Verbruggen £4.5 (pS .95) | Donnarumma £5.5 (pS .90) | −0.49 | −£1.0m | £1.0m buys 0.49 pts over six GWs. Spend it outfield. |

**The one premium that survives, at a reduced margin.** Raya returns **+2.73 EP6 over Verbruggen
for £1.5m** — 1.82 pts per £m, down from 2.55 at GW1. It remains a budget-allocation question,
not a goalkeeper question, but the bar the £1.5m must clear outfield is now materially lower.

## GK1 + GK2 pairings

| Pairing | Cost | EP6 | Note |
|---|---|---|---|
| **Raya + Dubravka** | £10.0 | **24.75** | Our current pair. Highest-EP pairing available; the GK2 half now contributes 2.38, not 7.10. |
| Lammens + Dubravka | £9.0 | 22.65 | Best EP per pound at the position. |
| Kelleher + Dubravka | £9.0 | 22.48 | |
| Verbruggen + Phillips | £8.5 | 22.15 | Cheapest credible pairing; frees £1.5m against our current pair for 2.60 EP6. |
| Verbruggen + Dubravka | £8.5 | 22.02 | |
| Leno + Dubravka | £8.5 | 20.94 | |
| **Verbruggen + Leno** | £9.0 | **38.20** | Two *playing* keepers — the best Bench-Boost GK block available, up from 36.39. Still academic: `bboost` runs GW1–19 and the snapshot holds no DGW. |

Never pair two keepers from the same club — only one of them plays.

## The £4.0 bench slot

Both GW1 candidates lost their claim in the same round, and they are now effectively tied:

| Player | Tm | £ | pS | EP6 | Δ | Read |
|---|---|---|---|---|---|---|
| Phillips | HUL | 4.0 | .13 | **2.51** | −3.71 | Marginally ahead. Worse defence, marginally more open chart (Butland out, arm, no return date). |
| **Dubravka** | TOT | 4.0 | .12 | **2.38** | **−4.72** | Our incumbent. Kinsky went 90 and kept the shirt despite conceding 3 — TOT faced 3.87 xG at Brentford, the round's worst defensive display, which is a team failure and not a case for dropping the keeper. |

**The 0.13 EP6 gap is inside noise; it does not justify a transfer.** Every other £4.0 keeper
sits at ≤0.40 EP6 and is a genuinely dead slot, so the £4.0 tier is now worth ~2.4 EP6 at best
against ~0.3 for pure fodder. Dubravka's 18.6% ownership is stale bench-fodder demand — the
market is unwinding it at −25.2k this gameweek.

## C4 compliance — promoted-club exposure

C4 binds: *a promoted-club-derived term must never be the largest single EP component for a
selected player.* Checked mechanically across all 120 club-fixtures × the pool.

For a goalkeeper the appearance term is a flat **1.98** every week, so the clean-sheet term only
overtakes it above P(CS) = 49.5%. **Exactly one fixture in the entire window clears that bar:**

| Player | GW | Fixture | P(CS) | CS term | Largest component |
|---|---|---|---|---|---|
| **Donnarumma** (MCI) | 3 | COV (H) | 52% ± | **2.08** | clean sheet — **C4 TRIP** |
| Rulli, Bettinelli (MCI #2/#3) | 3 | COV (H) | 52% ± | 2.08 | same fixture; both unselectable at pS ≤ .10 |

**Donnarumma is the only selectable keeper who trips C4, and it is one gameweek of six.** His
band-floor EP6 is **18.97** against a central 20.13. fixtures.md independently revises COV's
implied DEFW to 0.95 — *league-average*, better than assumed — which pushes the true value toward
that floor. If the optimizer wants Donnarumma it must justify him on the other five gameweeks.

Every other keeper in the pool passes C4 trivially. **Raya passes it vacuously**: ARS play
AVL, CHE, SUN, BHA, LEE, NFO — no promoted club in the window.

Promoted-club keepers themselves (Tzolakis, Rushworth, Scherpen) are the widest bands in the file
and are quantified per player as `ep6_band_promoted`:

| Player | Central | ±15pp band | Width |
|---|---|---|---|
| Tzolakis HUL | 16.42 | 13.42 – 19.93 | **6.51** |
| Rushworth COV | 14.74 | 11.96 – 17.84 | **5.88** |
| Scherpen IPS | 13.54 | 10.96 – 16.39 | **5.43** |

A 5–6.5 point band on a 6-gameweek horizon is not a point estimate. Treat all three as ranges.

## Model

```
EP(gk, gw) = P(starts) × [ 1.98                                  appearance
                         + 4 × P(CS)                             clean sheet
                         − E[floor(GC/2)]      GC ~ Poisson(λ_def)
                         + E[floor(S/3)]       S  ~ Poisson(save_rate × λ_def)
                         + pen_save_rate × (λ_def / λ̄) × 5
                         + bonus_per_start × fixture_mult × 1.15
                         − 0.09 ]                                cards + own goals
```

Structure is **unchanged from GW1** — the retro found GKP predictions landed well (GKP bias
+0.33/player on n = 2), so there was no case for changing the scoring model. What changed is the
inputs.

- **λ_def and P(CS) taken directly from `fixtures.md`** per club-fixture. Ticker deciles not used.
  Window means: λ̄_def = **1.4318**, P(CS) = **25.77%** across 120 club-fixtures (GW1: 1.439 / 25.75%).
- **No DefCon term** — goalkeepers are not eligible. **C1 is therefore inert for this position**;
  it is noted and no DefCon mapping is touched here.
- **In-season blending (the one substantive input change).** Per-90 rates are formed from
  **prior-season + GW1 counting stats summed**, then shrunk to the league mean. Because the
  shrinkage weight is `min/(min+1350)`, a full-season keeper's GW1 match earns **90/3420 ≈ 2.6%**
  of the weight — which is precisely the "nudge, not replace" the in-season regime calls for, and
  it falls out of the estimator rather than being imposed. For a keeper with no prior at all
  (Tzolakis, Horníček, Rushworth) GW1 is the only evidence and still receives just 6.3% weight
  against the league mean.
  - `save_rate` = saves per unit xG faced; league mean **2.010**, weight `min/(min+1350)`.
  - `bonus_per_start`; league mean **0.219**, weight `starts/(starts+12)`.
  - `pen_save_rate`; league mean **0.0158**, weight `starts/(starts+120)`.
- **Observation caps, new this cycle.** A single match can produce a rate no season sustains —
  Tzolakis's 3 bonus in one start implies 3.00 bonus/start, and even after shrinkage that added
  ~1.2 EP6 on its own. Observed rates are therefore capped before shrinking: bonus at **0.60/start**
  (the best full season in the pool is Roefs at 0.343), saves at **4.0/xGC** (sustained rates run
  1.7–2.5), pen saves at **0.15/start**. This bites on exactly one player, and it is the one the
  market is chasing hardest.
- **`fixture_mult`** = `clip(0.5 + 0.5 × P(CS)/0.2577, 0.4, 1.8)`; bonus uplifted **×1.15** for the
  26/27 GK save-BPS improvement.
- **New signings** (Di Gregorio, Suzuki, Rulli, Horníček) capped per the spec at P(starts) ≤ 0.7
  and HIGH until two consecutive 60'+ starts. Horníček holds the cap despite starting GW1.

### Deviations from the spec, and why

Carried unchanged from GW1, plus one addition:

| Change | Spec text | Reason |
|---|---|---|
| Saves use `E[floor(S/3)]`, not `E[S]/3` | "E[saves]/3 pts" | FPL awards 1 pt per **3** saves — a step function. The spec forbids linearizing exactly this shape for DefCon; the identical argument applies. |
| Goals conceded uses `E[floor(GC/2)]`, not `λ/2` | "goals-conceded for GKP/DEF" | Same argument: −1 per **2** conceded. At λ = 1.3 the true cost is 0.42, not 0.65. |
| `p_start_gw[6]` emitted alongside scalar `p_start` | schema lists scalar | Petrović and the AVL/NEW splits vary materially across the window; a scalar hides the shape. |
| `ep6_band_promoted`, `ep6_band_defence`, `ep6_if_nailed` **replace** GW1's `ep6_sensitivity_prior_defence` | not in schema | **Retired deliberately.** GW1's field re-anchored λ_def to the incumbent's prior xGC — but the fixtures.md "squad-turnover contamination" flag means prior rows are keyed to a player's *current* club, so Dubravka's 71.26 xGC is credited to Spurs despite being earned elsewhere. The field's input is contaminated and its motivating flag has been downgraded HIGH → MEDIUM now that team xGA is measured. Replaced with an honest ±12% λ_def band, the C4-mandated ±15pp promoted band, and a p_start-flat figure. |

### Calibration

Two independent checks, both clean.

**1. Against prior-season points per start** (n = 17 keepers, ≥900 min and ≥20 starts):
**bias −0.094 pts/start, MAE 0.186.** GW1 recorded −0.007 / 0.245 — the MAE improved 24%, the
bias is slightly negative. The four largest residuals are all *under*-predictions and all on
high-bonus keepers (Roefs −0.43, Donnarumma −0.41, Kelleher −0.40, Pickford −0.29): the shrunk
bonus term deliberately pulls elite bonus accumulators toward the mean. This is conservative in a
known direction and is logged as a retro hook rather than fitted away on one round.

**2. Against GW1 actuals, all 20 starting keepers** — the first genuine out-of-sample test:

| | Value |
|---|---|
| Actual mean, 20 GKs who started GW1 | **3.45 pts** |
| Model mean EP per start across the 20 modelled #1s | **3.39 pts** |
| Difference | **+0.06** |

The scoring model reproduces the position's realised rate to within a sixteenth of a point. This
corroborates the retro's GKP verdict independently of our own two players.

**A distribution warning the mean conceals.** The 20 GW1 keeper scores were
`1,1,1,1,1,2,2,2,2,2,2,2,2,3,6,6,7,7,9,10` — **mean 3.45, median 2**. Goalkeeper EP is a mean over
a hard bimodal split (clean sheet or not); thirteen of twenty returned ≤2. Nothing at this
position should ever be captained, and a GK differential is a coin flip dressed as an edge.

## Uncertainty register

Tags obey **C7**: p_start < 0.85 → MED at best; p_start < 0.70 → HIGH. Applied as a floor, with
two grounds that override upward regardless of p_start — promoted-club employment and
no-PL-history — which is why Tzolakis (pS .86) and Horníček (pS .75) carry HIGH. Verified
mechanically across all 57 keepers with a non-zero start probability.

**One narrow carve-out from C7, stated rather than assumed.** Eleven keepers sit at p_start
exactly 0.0 with `status` `u` or `i` — on loan at another club, transferred out, or injured with
no return date (Vicario, Bayindir, Jörgensen, Patterson, Van Oevelen, Cartwright, Lo-Tutala,
Pecsi, Dennis, Jaros, Heaton). They are tagged **LOW**, not HIGH: the tag drives the optimizer's
rotation discount, and "certainly zero" is the opposite of uncertain. All eleven carry
`ep_total6: 0.0`, so no discount tier can reach them and the tag is inert. Every player with any
start probability at all — including Davies at 0.0 with `status: a` — takes the C7 floor.

| Flag | Severity | Change vs GW1 | Detail |
|---|---|---|---|
| **AVL keeper — Martinez benched** | **HIGH** | **NEW** | Bizot played 90, Martinez 0, `status: a`, `news: ""`, and **−38.6k net transfers out**. Owners are acting on information the snapshot does not carry. Modelled as an unresolved split (.51/.37/.10 Bizot/Martinez/Suzuki), not a resolution — one match against 32 prior starts. **Neither is selectable until the shirt is confirmed.** Highest-value manual team-news check before the deadline. |
| **BOU keeper — Di Gregorio** | **HIGH** | **NEW** | Added to the bootstrap after the GW1 deadline at £4.5, level with Petrović. Zero PL history, 0.0% owned, 113 transfers in — the market has not noticed. Structurally identical to Pope/Horníček, which just resolved against the incumbent. Petrović's decay .90 → .70 is the model's response; if it is wrong his EP6 is 17.63, not 14.77. |
| **Promoted-club keepers** | **HIGH** | band quantified (C4) | Tzolakis, Rushworth, Scherpen now carry explicit ±15pp EP6 bands of 5.4–6.5 points. All three have exactly one PL appearance to their name. |
| **Single-match sample** | **HIGH** | **new** | Every current-season input is n = 1. Five clubs' implied ratings were clipped at fixtures.md's guard band. The observation caps above are this file's brake on the same problem. |
| **Chasing the GW1 spike** | **MED** | **new** | Tzolakis +77.9k and Trafford +43.7k are the round's chase trades. Trafford's is defensible — he confirmed a contested job. Tzolakis's is not: HUL hold the 2nd-worst defensive ticker and the widest band in the file. |
| Defence ratings assumption-dominated | **MED** | **downgraded from HIGH** | Team xGA is now measured, but only 20–25% of each rating is empirical. `ep6_band_defence` reports EP6 at λ_def ×1.12 / ×0.88. GW1's residual analysis found the tier prior *compresses toward average*, so the favourable end is the likelier one for ARS/MCI and the unfavourable end for HUL/SUN. |
| GK save-BPS uplift magnitude | **MED** | unchanged | The 26/27 change is known directionally, not numerically; a flat ×1.15 is applied. Calibration §1 shows the bonus term running slightly low on elite accumulators — consistent with ×1.15 being conservative. Re-test at GW4. |
| Cup rotation | **MED** | unchanged | fixtures.md models no European or domestic cup calendar. Keeper league-rotation for cups is rarer than for outfielders (clubs play the deputy *in* the cup), so only a small haircut is applied to ARS/MCI/CHE/LIV/MUN/TOT/NEW. |
| International break GW5→GW6 | **LOW** | escalated in fixtures.md | A **19-day** gap. GW6–7 p_start shaded ~0.01–0.02 for return-from-break risk; GW6–7 fixture ratings are the least reliable in the window. |
| Penalty-save and card rates | **LOW** | unchanged | Heavily shrunk league rates; worth ≤0.3 pts across the window for anyone. |

**Retired this cycle:** the GW1 "unresolved depth charts" HIGH flag (four clubs, seven keepers) is
closed — six of seven resolved by observation. It is replaced by the two new HIGH flags above,
which is a net reduction in scope but not in severity.

## Retro hooks for GW3 onward

Ordered by leverage, and stated as testable propositions rather than intentions:

1. **The price-parity signing signal.** GW1 produced one clean test (Horníček £5.0 = Pope £5.0)
   and it resolved for the signing. Di Gregorio v Petrović is the second instance and is live
   now. **Log the outcome.** Two for two would justify promoting price-parity from a soft haircut
   to a hard p_start cap on the incumbent; one for two would mean GW1 was a coincidence.
2. **The ×1.15 GK save-BPS uplift.** Now directly measurable — GW1 gave 20 keeper BPS
   observations. Calibration §1 says the bonus term runs ~0.1 pts/start low on elite accumulators.
   Re-fit at GW4, not before.
3. **`save_rate` per unit xGC.** Prior-season anchored, now accumulating one match per cycle. The
   shrinkage weight handles the blend automatically; no manual intervention needed until ~GW8,
   when current-season weight passes 15%.
4. **Club DEFW.** Still the dominant term. `strength_defence_*` remains zeroed for the second
   cycle running — re-check every cycle; the moment FPL populates it, every number here moves.
