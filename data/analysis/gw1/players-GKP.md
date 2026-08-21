# GW1 — Goalkeeper EP (GW1–GW6)

Season 2026/27 | GW1 deadline 2026-08-21T17:30:00Z | snapshot `data/raw/gw1/`
Regime: **PRE-SEASON** (bootstrap aggregates are 2025/26) | `data/retro/` empty — no calibration corrections available
Pool scored: **all 67 goalkeepers**; 57 carry a non-zero start probability. Full numbers in `players-GKP.json`.

## What the optimizer should take from this

| # | Claim | Confidence |
|---|---|---|
| 1 | **Raya (£6.0) is the highest-EP keeper and the only premium who earns his price.** 22.43 EP6, and he is the one name the model *understates* — see the defensive sensitivity below. | HIGH |
| 2 | **Lammens (£5.0, MUN) is the best base-model value in the pool** — 4.158 EP/£m, highest of all 67. Driven by MUN holding the 2nd-best defensive run in the window. | MED |
| 3 | **Verbruggen (£4.5, BHA) is the sensitivity-robust value pick** — 4.133 EP/£m base, best in the pool once defensive ratings are corrected toward prior-season xGC. | HIGH |
| 4 | **The £5.0–£5.5 band is dominated apart from Lammens.** Pickford, Donnarumma and A.Becker all return less per pound than a £4.5 nailed starter. | HIGH |
| 5 | **Dubravka (£4.0, TOT) is the best GK2 body in the game** — 7.10 EP6 against 1.21 for the next-best genuinely-cheap bench keeper. Free option value, not a starter. | MED |
| 6 | **Four depth charts are unresolved and gate any pick from those clubs**: TOT, LEE, COV, IPS. See Escalations. | — |

## Top 15 by EP over GW1–GW6

`pS` = mean P(starts). `sens` = EP6 if club defensive ratings are re-anchored to prior-season xGC
instead of the tier prior (see Defensive-rating sensitivity). `—` = no clean club prior exists.

| # | Player | Tm | £ | pS | GW1 | GW2 | GW3 | GW4 | GW5 | GW6 | **EP6** | EP/£m | sens | Unc |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Raya | ARS | 6.0 | .94 | 4.27 | 3.59 | 3.35 | 3.89 | 3.70 | 3.63 | **22.43** | 3.74 | 24.42 | LOW |
| 2 | Lammens | MUN | 5.0 | .90 | 3.78 | 3.82 | 3.23 | 2.93 | 3.52 | 3.51 | **20.79** | **4.16** | 19.73 | MED |
| 3 | Pickford | EVE | 5.5 | .95 | 3.07 | 2.94 | 3.04 | 3.29 | 3.71 | 3.64 | **19.69** | 3.58 | 18.89 | LOW |
| 4 | Roefs | SUN | 5.0 | .92 | 3.51 | 3.61 | 2.95 | 3.03 | 2.85 | 3.29 | **19.24** | 3.85 | 19.68 | LOW |
| 5 | Kelleher | BRE | 5.0 | .92 | 3.52 | 3.08 | 3.55 | 3.02 | 2.96 | 3.06 | **19.19** | 3.84 | 19.26 | LOW |
| 6 | Donnarumma | MCI | 5.5 | .89 | 3.10 | 2.91 | 3.69 | 2.92 | 3.52 | 2.82 | **18.96** | 3.45 | 19.26 | MED |
| 7 | Verbruggen | BHA | 4.5 | .93 | 3.18 | 2.79 | 3.09 | 3.44 | 2.93 | 3.17 | **18.60** | **4.13** | 19.43 | LOW |
| 8 | Martinez | AVL | 5.0 | .84 | 3.03 | 2.83 | 3.47 | 3.18 | 3.12 | 2.82 | **18.45** | 3.69 | 18.13 | MED |
| 9 | Sánchez | CHE | 5.0 | .86 | 3.20 | 3.14 | 2.63 | 3.61 | 2.68 | 2.82 | **18.08** | 3.62 | 17.51 | MED |
| 10 | Leno | FUL | 4.5 | .93 | 2.76 | 3.19 | 2.91 | 2.76 | 2.91 | 3.26 | **17.79** | 3.95 | 18.41 | LOW |
| 11 | Sels | NFO | 5.0 | .86 | 2.84 | 2.61 | 3.06 | 2.76 | 3.31 | 2.57 | **17.15** | 3.43 | 16.84 | MED |
| 12 | Henderson | CRY | 5.0 | .82 | 2.26 | 2.55 | 3.13 | 3.35 | 2.78 | 3.00 | **17.07** | 3.41 | 16.79 | HIGH |
| 13 | A.Becker | LIV | 5.5 | .78 | 2.70 | 2.94 | 3.10 | 3.20 | 2.58 | 2.46 | **16.98** | 3.09 | 17.28 | MED |
| 14 | Petrović | BOU | 4.5 | .93 | 2.62 | 3.13 | 2.91 | 2.84 | 2.87 | 2.56 | **16.93** | 3.76 | 17.69 | LOW |
| 15 | Pope | NEW | 5.0 | .76 | 2.56 | 2.70 | 2.57 | 2.51 | 3.08 | 2.78 | **16.20** | 3.24 | 16.51 | HIGH |

Next five: Trafford LEE £5.0 13.42 · Kinsky TOT £4.5 11.08 · Tzolakis HUL £4.5 10.98 ·
Rushworth COV £4.5 8.45 · Walton IPS £4.5 7.14 — all HIGH, all gated on an unresolved depth chart.

## Nailed cheap beats rotating premium

The spec asks for these to be named. At goalkeeper the effect is unusually strong this season,
because the three best-value nailed keepers all sit at £4.5 while the £5.0–£5.5 band is
populated by keepers with real competition behind them.

| Cheap, nailed | Rotating, dearer | EP6 gap | Price gap | Verdict |
|---|---|---|---|---|
| Verbruggen £4.5 (pS .93) | A.Becker £5.5 (pS .78) | **+1.62** | **−£1.0m** | Cheap wins on both axes. Widens to +2.15 under the defensive sensitivity. The cleanest case in the pool. |
| Verbruggen £4.5 (pS .93) | Trafford £5.0 (pS .70) | **+5.18** | **−£0.5m** | Not close. Trafford's price implies a job he has not held. |
| Leno £4.5 (pS .93) | Pope £5.0 (pS .76) | **+1.59** | **−£0.5m** | Pope's own rate is fine (3.57 pts/start); the £5.0 Horníček signing is what costs him. |
| Petrović £4.5 (pS .93) | Kinsky £4.5 (pS .58) | **+5.85** | £0 | Same price, 35pp more starting probability. |
| Verbruggen £4.5 (pS .93) | Donnarumma £5.5 (pS .89) | −0.36 | −£1.0m | £1.0m buys 0.36 pts over six GWs. The sensitivity **reverses** the sign. Treat as a coin flip and spend the £1.0m outfield. |

**The one premium that survives**: Raya at £6.0 returns +3.83 EP6 over Verbruggen for £1.5m —
2.55 pts per £m across the window, rising to +4.99 EP6 (3.33 pts per £m) under the defensive
sensitivity. That is a real edge, but it is a *budget-allocation* question, not a goalkeeper
question: the optimizer should only take it if £1.5m has no better outfield home.

## GK1 + GK2 pairings

Standard construction is one nailed starter plus the cheapest body. Never pair two keepers from
the same club — only one of them plays.

| Pairing | Cost | EP6 | Note |
|---|---|---|---|
| Raya + Dubravka | £10.0 | **29.53** | Highest-EP pairing. Ceiling play. |
| Lammens + Dubravka | £9.0 | 27.89 | Best EP per pound spent on the position. |
| Roefs + Dubravka | £9.0 | 26.34 | |
| Verbruggen + Dubravka | £8.5 | 25.70 | Cheapest credible pairing; frees £1.5m against Raya. |
| Leno + Dubravka | £8.5 | 24.89 | |
| **Verbruggen + Leno** | £9.0 | **36.39** | Two *playing* keepers. Irrelevant most weeks, but the best Bench-Boost GK block available — worth holding in mind, noting `bboost` runs GW1–19 and the snapshot contains no DGW. |

If Dubravka is judged too speculative, Phillips (HUL, £4.0, 6.22) is the next body; every other
£4.0 keeper sits at ≤1.21 EP6 and is functionally a non-playing slot.

## Enabler and bench pool (£4.0–£4.5)

| Player | Tm | £ | pS | EP6 | EP/£m | Read |
|---|---|---|---|---|---|---|
| Verbruggen | BHA | 4.5 | .93 | 18.60 | 4.13 | Nailed starter at enabler price. The pick. |
| Leno | FUL | 4.5 | .93 | 17.79 | 3.95 | Nailed; FUL fixtures are the only drag. |
| Petrović | BOU | 4.5 | .93 | 16.93 | 3.76 | Nailed; hardest defensive run of the three. |
| Kinsky | TOT | 4.5 | .58 | 11.08 | 2.46 | Gated on the TOT escalation. |
| Tzolakis | HUL | 4.5 | .60 | 10.98 | 2.44 | Worst defence in the league; avoid per fixtures.md. |
| Rushworth | COV | 4.5 | .45 | 8.45 | 1.88 | Gated on the COV escalation. |
| Walton | IPS | 4.5 | .38 | 7.14 | 1.59 | Gated on the IPS escalation. |
| **Dubravka** | TOT | 4.0 | .37 | **7.10** | 1.78 | Best £4.0 body by ~6× over normal bench fodder. |
| Phillips | HUL | 4.0 | .34 | 6.22 | 1.55 | Second-best £4.0 body. |
| Wilson | COV | 4.5 | .33 | 6.19 | 1.38 | COV co-favourite — see escalation. |
| Perri | LEE | 4.5 | .30 | 5.46 | 1.21 | The cheaper half of the LEE two-way. |
| Scherpen | IPS | 4.5 | .26 | 4.88 | 1.08 | IPS co-favourite — see escalation. |
| Dovin | COV | 4.0 | .22 | 4.13 | 1.03 | |
| Van Oevelen | IPS | 4.5 | .16 | 3.01 | 0.67 | Third IPS keeper at £4.5. |
| Benitez | CRY | 4.5 | .14 | 2.92 | 0.65 | EP concentrated in GW1 (0.92) on the Henderson flag. |
| Penders | CHE | 4.5 | .13 | 2.77 | 0.62 | |
| Palmer | IPS | 4.0 | .14 | 2.63 | 0.66 | 4.9% ownership is bench-fodder demand, not a start signal. |

Note how much of this table is escalation-gated: **ten of these seventeen** are TOT/LEE/COV/IPS
keepers whose EP exists only because a depth chart is unresolved — which is the real reason the
cheap end of this position is thin, not a shortage of names. Everything below Palmer sits at ≤2.10 EP6 —
pure non-playing fodder, where the only sane criterion is "cheapest". Ten keepers score exactly
zero: Jörgensen, Bayindir, Vicario, Cartwright, Lo-Tutala, Pecsi, Patterson (out on loan or
transferred, status `u`), Jaros, Heaton (injured, no return date), and Davies (no route to minutes).

## Escalations

Four depth charts cannot be resolved from this snapshot. Each one gates a pick, and each is worth
a manual check of team news before the deadline.

| Club | Situation | Split applied | Why unresolved |
|---|---|---|---|
| **TOT** | Vicario loaned to Juventus. Kinsky £4.5 vs Dubravka £4.0. | Kinsky .58 / Dubravka .37 | Price says Kinsky; prior minutes say Dubravka (35 starts, 127 saves vs Kinsky's 7 starts). Ownership is split **23.9% / 20.3%** — the market is hedging, not deciding. |
| **LEE** | Trafford £5.0 vs Perri £4.5. | Trafford .70 / Perri .30 | Price says Trafford is the new #1; last season says Perri (16 starts vs 4). Price and minutes disagree outright. |
| **COV** | Rushworth £4.5, Wilson £4.5, Dovin £4.0. | .45 / .33 / .22 | Two keepers tied on price. Zero PL minutes for any of them. Separated only by 1.1% vs 0.5% ownership — noise. |
| **IPS** | Walton, Scherpen, Van Oevelen **all £4.5**; Palmer £4.0. | .38 / .26 / .16 / .14 | FPL priced three keepers identically. Walton and Scherpen are also tied on ownership (0.6%). No signal exists in the snapshot. |

Two further minutes risks worth flagging, both already priced into the EP above:

- **Henderson (CRY)** — ankle injury, `chance_of_playing_next_round` 75%. GW1 is the exposed week;
  P(starts) is modelled as a ramp `.68 → .82 → .86…`, not a flat number. Benitez (£4.5) is the
  GW1 beneficiary at pS .28.
- **Pope (NEW)** — no injury flag, but Horníček was signed in at **£5.0, exactly level with Pope**.
  FPL pricing a new-signing keeper at parity with the incumbent is a rotation warning, and it is
  the single reason Pope grades below the £4.5 nailed group.

### A signal that does not exist
`ep_next` is **not** usable as a minutes signal. It is a pure price-tier lookup — £6.0→4.0,
£5.5→3.3, £5.0→2.6, £4.5→1.9, £4.0→1.0 — multiplied by `chance_of_playing` (Henderson £5.0→2.0,
Darlow £4.5→1.4). It carries no depth-chart information. `transfers_in`/`transfers_out` are zero
for every player (pre-season reset), so market flow is unavailable too.

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

- **λ_def and P(CS) taken directly from `fixtures.md`**, per club-fixture, as instructed. The 1–10
  ticker deciles were not used. Window means: λ̄_def = 1.439, P(CS) = 25.75% over 120 club-fixtures.
- **No DefCon term** — goalkeepers are not eligible.
- **`save_rate` = saves per unit xG faced** (prior season), shrunk to the league mean 2.007 with
  weight `min/(min+1350)`. Multiplying by fixture λ_def gives expected saves. This is why leaky
  defences are not pure negatives: Petrović vs MCI(a) loses clean-sheet value but gains 4.1
  expected saves.
- **`bonus_per_start`** shrunk to the league mean 0.223 with weight `starts/(starts+12)`, then
  scaled by `0.5 + 0.5 × P(CS)/0.2575` (clipped 0.4–1.8) and uplifted **×1.15** for the 26/27
  improvement to goalkeeper save BPS.
- **`pen_save_rate`** shrunk hard — `starts/(starts+120)` — because penalty-saving barely persists
  year to year. Without heavy shrinkage Kelleher's 3 prior saves alone moved him ~1.4 pts and
  decided his rank against Roefs; those two are inside noise of each other either way.
- **New signings and promoted-club keepers** capped per the spec: no PL history → P(starts) ≤ 0.7,
  uncertainty HIGH. COV/HUL/IPS keepers additionally inherit fixtures.md's HIGH flag — those clubs
  have **zero** PL goalkeeper minutes, so their P(CS) has no empirical basis at all.

### Deviations from the spec, and why

| Change | Spec text | Reason | Effect |
|---|---|---|---|
| Saves use `E[floor(S/3)]`, not `E[S]/3` | "E[saves]/3 pts" | FPL awards 1 pt per **3** saves — a step function. The spec forbids linearizing exactly this shape for DefCon; the same argument applies here. | Linearizing would overstate every keeper, worst for leaky defences (+0.39/GW for Petrović vs +0.32 for Raya), compressing the spread. |
| Goals conceded uses `E[floor(GC/2)]`, not `λ/2` | "goals-conceded for GKP/DEF" | Same step-function argument: −1 per **2** conceded. At λ=1.3 the true cost is 0.42, not 0.65. | Understates the penalty by ~0.2/GW if linearized. |
| Added `p_start_gw[6]` to the JSON | schema lists scalar `p_start` | Henderson's injury flag makes GW1 materially different from GW2–6; a scalar hides it. Scalar `p_start` retained alongside. | — |
| Added `ep6_sensitivity_prior_defence` | not in schema | Quantifies the fixtures.md HIGH defensive-rating warning per player rather than leaving it as prose. | — |

Note the two floor corrections partly cancel (saves up, GC penalty down), so the *net* effect on
EP6 is modest — but they do not cancel evenly across keepers, and the direction of the residual is
what separates the £4.5 group from the £5.5 group.

### Calibration

The model was checked against prior-season points per start for the 18 keepers with ≥900 minutes
and ≥20 starts. **Mean bias −0.007 pts/start, MAE 0.245.** The model reproduces last season's
scoring rate while still responding to fixtures, which is the behaviour wanted.

### Defensive-rating sensitivity — the largest open risk

`fixtures.md` flags its defensive ratings as ASSUMPTION-grade: split-strength fields are zeroed,
so 65–72% of every DEFW comes from a 5-level tier prior, compressing eleven clubs into
DEFW 0.95–1.03. The calibration residuals show that compression directly — errors are **not**
random, they sort by defensive quality:

| Club | model mean λ_def | prior xGC/match | ratio | EP6 swing on the #1 |
|---|---|---|---|---|
| ARS | 0.958 | 0.745 | 0.78 | Raya **+1.99** |
| BHA | 1.468 | 1.291 | 0.88 | Verbruggen **+0.83** |
| BOU | 1.687 | 1.493 | 0.88 | Petrović +0.76 |
| FUL | 1.528 | 1.388 | 0.91 | Leno +0.62 |
| MCI | 1.180 | 1.132 | 0.96 | Donnarumma +0.30 |
| CHE | 1.273 | 1.390 | 1.09 | Sánchez −0.57 |
| EVE | 1.327 | 1.480 | 1.12 | Pickford −0.80 |
| MUN | 1.070 | 1.227 | 1.15 | Lammens **−1.06** |

Reading: the tier prior pulls good defences toward average and bad defences up toward average, so
the model **understates elite-defence keepers and overstates weak-defence keepers**. Consequences:

- **Raya's lead is understated, not overstated.** He is #1 at 22.43 and #1 at 24.42. Robust.
- **Lammens vs the £4.5 group is not robust.** His 4.16 EP/£m falls to 3.95 under the sensitivity,
  below Verbruggen's 4.32. Lammens is a bet that MUN's *fixture run* beats ARS/BHA quality — and
  the run peaks in GW1–2 (HUL a, IPS H) then decays.
- Re-run this once FPL populates `strength_defence_*`. Every number in this file moves with it.

Caveat on the sensitivity column itself: it re-anchors to the prior xGC of the club's modelled
incumbent, which is only valid where that keeper actually played for that club last season.
TOT, LEE and the three promoted clubs have no such keeper, so they get no sensitivity figure
rather than a contaminated one.

## Uncertainty register

| Flag | Severity | Detail |
|---|---|---|
| Defensive ratings ASSUMPTION-grade | **HIGH** | Inherited from fixtures.md. Sorts the calibration residuals by defensive quality — see above. Mid-table P(CS) gaps under ~4pp are noise, so Sels/Henderson/A.Becker/Pope ordering is not meaningful. |
| Promoted-club keepers | **HIGH** | COV/HUL/IPS have zero PL goalkeeper minutes. P(CS), save rate and depth chart are all assumption. fixtures.md advises avoiding these assets outright; the EP figures agree. |
| Unresolved depth charts | **HIGH** | TOT, LEE, COV, IPS — four clubs, seven keepers with a live claim. Pre-deadline team news is the only fix. |
| Henderson fitness | **HIGH** | 75% flag, GW1-specific. The finalizer's freshness gate should catch any movement. |
| Pope / Horníček | **HIGH** | Price-parity signal only; no team news either way. |
| GK save-BPS uplift magnitude | **MED** | The 26/27 change is known directionally but not numerically; a flat ×1.15 was applied. Verbruggen is the most exposed — 106 prior saves for only 6 bonus, so a larger uplift helps him most. Calibrate from GW1–3 retro. |
| Cup rotation | **MED** | fixtures.md leaves European/domestic cup calendars unmodelled. Goalkeeper league rotation for cups is rarer than for outfielders — clubs play the back-up *in* the cup — so only a small haircut was applied to ARS/MCI/CHE/LIV/MUN/TOT. |
| GW6 post-break | **LOW** | A 20-day international break splits GW5 from GW6. All GW6 P(starts) shaded ~0.02 for return-from-break injury risk. |
| Penalty-save and card rates | **LOW** | League-average rates with heavy shrinkage; worth ≤0.3 pts across the window for anyone. |

## Retro hooks for GW2 onward

`data/retro/` is empty, so nothing was corrected. The three parameters most worth calibrating
first, in order of leverage:

1. **Club DEFW** — recompute the moment FPL populates `strength_defence_*`; this dominates everything else.
2. **`save_rate` and the ×1.15 BPS uplift** — both are directly observable from GW1–3 actuals.
3. **P(starts) for the seven escalated keepers** — replace the assumed splits with observed starts.

From GW2, per spec, minutes should come from observed element-summary history rather than the
price-and-prior heuristics used here.
