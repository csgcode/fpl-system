# GW2 — 6-Gameweek Fixture Ticker (GW2–GW7)

Season 2026/27 | GW2 deadline 2026-08-28T17:30:00Z | snapshot `data/raw/gw2/`
(fetched 2026-08-28T09:45:31Z, age < 1h) | supersedes `data/analysis/gw1/fixtures.md`

Downstream agents consume **λ_att** and **P(CS)** only. The 1–10 attack/defence
scores are presentation deciles of the respective λ across the 120 club-fixtures
in this window — never use them as inputs.

## What changed since GW1

| | GW1 | GW2 |
|---|---|---|
| Split-strength fields | all zero | **still all zero** — no change |
| `strength_overall_home/away` | 5 tiers | **byte-identical**, no club moved |
| bootstrap league table (`played`/`points`/`form`) | empty | **still empty** — not updated after GW1 |
| Team xG-against | "no artifact provides it" | **available** — see below |
| Prior/current blend | 100 / 0 | **85 / 15** (attack), **80 / 20** (defence) |

### 1. FPL has still not populated the split-strength fields

Verified across all 20 clubs: `strength_attack_home`, `strength_attack_away`,
`strength_defence_home`, `strength_defence_away` are **0**, and `strength` is
**null**. The documented `strength_overall_home/away` fallback stays in force,
and it returns exactly the same 5-tier values as GW1 — not one club moved. The
bootstrap `teams` array also still shows `played: 0`, `points: 0`, `form: null`
for every club, so **the bootstrap carries no GW1 information at all**. Every
scrap of current-season signal below comes from element-summary history.

Re-check next cycle. The tier prior remains the dominant term in every defence
rating, so this stays the largest single modelling constraint.

### 2. Team xG-against now exists — the GW1 defence-data gap is closed

`data/analysis/gw1/fixtures.md` asserted "No artifact provides team xG-against."
**That is no longer true.** Element-summary `history` rows carry
`expected_goals_conceded`, and for any player who completed the full match it is
the **team's** xGA for that fixture. Cross-checked both ways across all 10 GW1
fixtures — 20 team-readings: a club's xGA read this way reproduces the sum of
its opponents' `expected_goals` to within 0.10 in **18 of 20**. The two
exceptions are MUN (1.83 vs 1.48) and MCI (2.25 vs 2.07), and both are
shortlist-coverage undercounts on the *summing* side — MUN logged 817 of 990
player-minutes in our snapshot, MCI 930. The xGA read is the more reliable of
the two and is what the ratings use.

Consequences:

- Team xG-against is now **measured, not assumed**, from GW2 onward.
- Team xG is best read as **the opponent's xGA**, which is immune to the missing
  ~30% of player summaries. Both directions are used below.
- Defence ratings remain assumption-*dominated* at GW2 (80% tier prior), but
  they are no longer assumption-*only*. Expect them to become genuinely
  empirical around GW4–5.

## Model

```
lambda_att(i vs j, home) = 1.54 * ATT_i * DEFW_j
lambda_att(i vs j, away) = 1.33 * ATT_i * DEFW_j
lambda_def(i)            = lambda_att(j)   # opponent-symmetric
P(CS)_i                  = exp(-lambda_def_i)
```

Unchanged from GW1. `ATT_i` and `DEFW_j` are multiplicative indices renormalised
to a 20-club mean of exactly 1.00 after blending, so the 1.54 / 1.33 base rates
stay calibrated.

**P(CS) is Poisson P(0 goals conceded).** It excludes the FPL 60-minute
requirement and rotation risk — the player-analyst applies those.

### Blend: how GW1 was folded in

Each club's GW1 match yields an **opponent- and venue-adjusted implied rating**:

```
impATT_i  = xG_i  / (base_venue     * DEFW_opponent)
impDEFW_i = xGA_i / (base_opp_venue * ATT_opponent)
```

This strips out fixture quality, so Brighton's 3.77 xG is credited against
Villa's actual rating rather than taken at face value. Implied values are then
clipped to **[0.55, 1.80]** before blending — a single match's xG has a standard
deviation near 1.0 goal, and five clubs produced implied ratings outside that
band that would otherwise dominate their blend.

Weights, expressed as `w_current = 1/(1+k)` where `k` is the prior's worth in
match-equivalents:

| Rating | Prior source | k | w_prior / w_current |
|---|---|---:|---|
| Attack, established club | real prior-season squad xG | 5.7 | **85 / 15** |
| Defence, established club | 5-tier `strength_overall` only | 4.0 | **80 / 20** |
| Attack, promoted club | ASSUMPTION | 4.0 | **80 / 20** |
| Defence, promoted club | ASSUMPTION | 3.0 | **75 / 25** |

Defence takes more current weight than attack because its **prior is weaker**,
not because its data is better — the tier prior carries less information than a
full season of squad xG, so one match displaces proportionally more of it.

**Deviation from the GW1 schedule, and why.** GW1 planned faster convergence for
promoted clubs (≥50% current weight by GW4). That is now **deferred to GW4+**,
per correction C4. One match is one match: a promoted club's single fixture is
no more informative than anyone else's, and C4 binds me to downgrade — not
upgrade — confidence in these ratings. The promoted clubs get only a 5pp weight
bump over the field at GW2, plus an explicit uncertainty band (below). Schedule
from here: ~70/30 at GW3, prior weight held ≥20% through GW10.

### C4 compliance — promoted-club ±15pp band

Every P(CS) in the detail table where the club **or its opponent** is COV, HUL
or IPS is marked `±` and carries a **±15pp uncertainty band** until that club
has 3+ played fixtures (i.e. through GW3; band lifts at GW4). Downstream agents
must treat a `±` P(CS) as a range, and **must not let a promoted-club-derived
term be the largest single EP component for any selected player**. In GW1 that
condition held for Gabriel, Raya, Mbeumo and Shaw and produced both MODEL
misses.

## Team ratings — GW2 (85/15 blend, GW1 xG applied)

`Δ` = change vs `data/analysis/gw1/fixtures.md`. `imp` columns are the
opponent- and venue-adjusted single-match implied ratings; `*` marks a value
clipped to the [0.55, 1.80] guard band before blending.

| Club | Tier | GW1 xG | GW1 xGA | impATT | impDEFW | ATT prior | **ATT** | Δ | DEFW prior | **DEFW** | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CHE  | 4.0 | 2.24 | 1.33 | 1.65 | 1.15 | 1.37 | **1.40** | +0.03 | 0.90 | **0.95** | +0.05 |
| MCI  | 4.5 | 2.25 | 0.65 | 1.48 | 0.43* | 1.39 | **1.39** | +0.00 | 0.80 | **0.75** | -0.05 |
| BRE  | 3.0 | 3.87 | 0.57 | 2.56* | 0.52* | 1.21 | **1.29** | +0.08 | 0.99 | **0.90** | -0.09 |
| LIV  | 4.0 | 2.98 | 1.58 | 2.22* | 1.04 | 1.18 | **1.26** | +0.08 | 0.85 | **0.88** | +0.03 |
| ARS  | 4.5 | 1.88 | 0.20 | 0.94 | 0.22* | 1.28 | **1.22** | -0.06 | 0.70 | **0.67** | -0.03 |
| CRY  | 3.0 | 1.96 | 1.12 | 1.47 | 0.77 | 1.14 | **1.18** | +0.04 | 0.97 | **0.93** | -0.04 |
| MUN  | 4.0 | 1.83 | 1.01 | 1.01 | 1.06 | 1.16 | **1.13** | -0.03 | 0.87 | **0.90** | +0.03 |
| BOU  | 3.0 | 0.65 | 2.25 | 0.61 | 1.05 | 1.13 | **1.04** | -0.08 | 0.99 | **1.00** | +0.01 |
| BHA  | 2.5 | 3.77 | 0.29 | 2.58* | 0.22* | 0.90 | **1.03** | +0.13 | 1.00 | **0.91** | -0.09 |
| NEW  | 2.5 | 1.58 | 2.98 | 1.21 | 1.90* | 0.99 | **1.01** | +0.02 | 1.01 | **1.16** | +0.15 |
| LEE  | 2.5 | 0.47 | 0.66 | 0.35* | 0.47* | 1.06 | **0.98** | -0.08 | 1.03 | **0.93** | -0.10 |
| AVL  | 3.5 | 0.29 | 3.77 | 0.22* | 2.72* | 0.98 | **0.91** | -0.07 | 0.95 | **1.11** | +0.17 |
| EVE  | 3.0 | 1.12 | 1.96 | 0.75 | 1.29 | 0.94 | **0.91** | -0.03 | 1.00 | **1.05** | +0.05 |
| NFO  | 3.0 | 0.66 | 0.47 | 0.42* | 0.33* | 0.92 | **0.86** | -0.06 | 1.00 | **0.91** | -0.09 |
| IPS **A** | 2.0 | 1.80 | 0.66 | 1.15 | 0.63 | 0.70 | **0.78** | +0.08 | 1.26 | **1.10** | -0.16 |
| TOT  | 3.0 | 0.57 | 3.87 | 0.43* | 2.08* | 0.83 | **0.78** | -0.05 | 0.98 | **1.14** | +0.16 |
| FUL  | 2.5 | 1.33 | 2.24 | 0.96 | 1.23 | 0.75 | **0.78** | +0.03 | 1.02 | **1.06** | +0.04 |
| SUN  | 2.5 | 0.66 | 1.80 | 0.39* | 1.67 | 0.79 | **0.75** | -0.04 | 1.02 | **1.15** | +0.12 |
| COV **A** | 2.0 | 0.20 | 1.88 | 0.21* | 0.95 | 0.68 | **0.65** | -0.03 | 1.30 | **1.21** | -0.09 |
| HUL **A** | 2.0 | 1.01 | 1.83 | 0.75 | 1.19 | 0.62 | **0.64** | +0.02 | 1.36 | **1.31** | -0.05 |

## What GW1 actually said — scorelines vs xG

The single most useful thing in this cycle: **four of the ten GW1 results
inverted their xG.** Reading the table below by scoreline would corrupt every
rating in this file.

| Fixture | Score | xG | Reading |
|---|---|---|---|
| HUL 2-0 MUN | HUL win | **MUN 1.83 – 1.01 HUL** | MUN out-created Hull comfortably and lost. |
| EVE 2-0 CRY | EVE win | **CRY 1.96 – 1.12 EVE** | Palace was the better side by a full goal of xG. |
| ARS 3-0 COV | ARS win | ARS 1.88 – 0.20 COV | Right winner, inflated margin (3 goals from 1.88). |
| NFO 0-1 LEE | LEE win | LEE 0.66 – 0.47 NFO | Coin-flip game; neither club created anything. |
| BRE 3-0 TOT | BRE win | **BRE 3.87 – 0.57 TOT** | The most one-sided match of the round, understated by the scoreline. |
| BHA 4-0 AVL | BHA win | **BHA 3.77 – 0.29 AVL** | Same. Villa's 0.29 xG is the second-worst of the round. |

### This contradicts the retro's MODEL classification for Mbeumo and Shaw

`data/retro/gw1.md` classes both as **MODEL** misses on the reasoning that
"MUN modelled at 44% clean sheet away to promoted HUL; MUN lost 0-2." The xG
says otherwise. The model predicted MUN λ_att 2.10 at Hull; MUN generated
**1.83** — a miss of only −0.27, one of the smaller attacking errors in the
round. MUN conceded just **1.01** xG, which is *better* than the 1.14 the model
implied. **Hull won that match on finishing, not on out-playing United.**

MUN's rating therefore barely moves: ATT 1.16 → 1.13, DEFW 0.87 → 0.90. I am
not downgrading Manchester United on a result their underlying numbers won. The
correct label for Mbeumo and Shaw is **VARIANCE**, not MODEL — and this
*strengthens* C4 rather than weakening it: the lesson is that promoted clubs
generate volatile *outcomes*, not that they are better teams than modelled.
Hull created 1.01 xG and remain 18th on attack.

C4 is applied in full regardless, via the ±15pp band, because the correction is
binding and the direction of travel is the same.

## Biggest rating changes vs GW1

Attack moved little — the prior is real prior-season xG and it held up. Defence
moved much more, because its prior was the weak one.

| Club | Change | Driver |
|---|---|---|
| **AVL DEFW 0.95 → 1.11** (+0.17) | worst defensive downgrade | Conceded **3.77** xG at Brighton, the round's highest. Implied DEFW 2.72, clipped to 1.80. |
| **TOT DEFW 0.98 → 1.14** (+0.16) | | Conceded **3.87** xG at Brentford, the round's highest single figure. Implied 2.08, clipped. |
| **IPS DEFW 1.26 → 1.10** (−0.16) | biggest improvement | Conceded only 0.66 xG vs Sunderland. No longer bottom-3 defensively. |
| **NEW DEFW 1.01 → 1.16** (+0.15) | | Conceded 2.98 xG at home to Liverpool. |
| **SUN DEFW 1.02 → 1.15** (+0.12) | | Conceded 1.80 xG at Ipswich — poor against a promoted side. |
| **BHA ATT 0.90 → 1.03** (+0.13) | biggest attacking move | 3.77 xG. Now rated an average-attack club rather than a bottom-six one. |
| **LEE DEFW 1.03 → 0.93** (−0.10) | | 0.47 xGA at Forest — but in a 0.66-vs-0.47 non-event. Low information. |
| **BRE / NFO / BHA DEFW** −0.09 each | | All three kept their opponents under 0.70 xG. |
| **BRE ATT 1.21 → 1.29**, **LIV ATT 1.18 → 1.26** (+0.08) | | Both confirmed the GW1 MEDIUM flag on Brentford's attack — see below. |
| **ARS ATT 1.28 → 1.22** (−0.06) | notable non-move | Arsenal scored 3 but generated 1.88 against a modelled 2.56. The rating fell despite the result. |

**Brentford's attack rating is now confirmed, and the GW1 MEDIUM flag lifts.**
GW1 flagged BRE ATT 1.21 as "unconfirmed until GW3" because it disagreed with
FPL's tier 3.0. Brentford then produced the round's highest xG (3.87). The
rating rises to 1.29 — 3rd in the league — and I now regard it as evidenced.

**Spurs' attack rating is also confirmed, in the other direction.** GW1 flagged
TOT ATT 0.83 (15th) as a disagreement with FDR. Spurs generated **0.57** xG.
Rating now 0.78, 17th. FDR was wrong, not the model.

## 6-GW ticker — best attacking (ranked by Σ λ_att, GW2–7)

| # | Club | Σ λ_att | λ/GW | mean att score | Fixtures GW2→7 |
|---|---|---:|---:|---:|---|
| 1 | MCI | 12.43 | 2.07 | 9.0 | CRY(a) COV(H) MUN(a) SUN(H) LIV(a) IPS(H) |
| 2 | CHE | 11.82 | 1.97 | 8.7 | BHA(H) ARS(a) HUL(H) BRE(a) BOU(H) EVE(a) |
| 3 | BRE | 11.12 | 1.85 | 8.7 | LEE(a) SUN(H) BOU(a) CHE(H) AVL(a) LIV(H) |
| 4 | LIV | 10.31 | 1.72 | 8.0 | NFO(H) IPS(a) FUL(H) BOU(a) MCI(H) BRE(a) |
| 5 | ARS | 10.13 | 1.69 | 8.0 | AVL(a) CHE(H) SUN(a) BHA(a) LEE(H) NFO(a) |
| 6 | NEW | 9.78 | 1.63 | 7.3 | TOT(a) BOU(H) LEE(a) HUL(H) COV(a) AVL(H) |
| 7 | MUN | 9.76 | 1.63 | 7.0 | IPS(H) EVE(a) MCI(H) FUL(a) TOT(H) LEE(a) |
| 8 | CRY | 9.55 | 1.59 | 7.2 | MCI(H) FUL(a) IPS(H) LEE(a) NFO(H) BHA(a) |
| 9 | BOU | 9.34 | 1.56 | 6.8 | EVE(H) NEW(a) BRE(H) LIV(H) CHE(a) SUN(H) |
| 10 | BHA | 8.51 | 1.42 | 5.7 | CHE(a) LEE(H) COV(a) ARS(H) SUN(a) CRY(H) |
| 11 | EVE | 8.26 | 1.38 | 5.2 | BOU(a) MUN(H) TOT(a) IPS(H) HUL(a) CHE(H) |
| 12 | LEE | 7.90 | 1.32 | 4.7 | BRE(H) BHA(a) NEW(H) CRY(H) ARS(a) MUN(H) |
| 13 | AVL | 7.83 | 1.30 | 4.5 | ARS(H) HUL(a) NFO(H) TOT(a) BRE(H) NEW(a) |
| 14 | TOT | 7.35 | 1.22 | 4.0 | NEW(H) NFO(a) EVE(H) AVL(H) MUN(a) COV(H) |
| 15 | NFO | 7.32 | 1.22 | 3.8 | LIV(a) TOT(H) AVL(a) COV(H) CRY(a) ARS(H) |
| 16 | FUL | 6.98 | 1.16 | 3.3 | SUN(a) CRY(H) LIV(a) MUN(H) IPS(a) HUL(H) |
| 17 | IPS | 6.13 | 1.02 | 2.5 | MUN(a) LIV(H) CRY(a) EVE(a) FUL(H) MCI(a) |
| 18 | HUL | 5.88 | 0.98 | 1.8 | COV(a) AVL(H) CHE(a) NEW(a) EVE(H) FUL(a) |
| 19 | COV | 5.79 | 0.96 | 2.0 | HUL(H) MCI(a) BHA(H) NFO(a) NEW(H) TOT(a) |
| 20 | SUN | 5.67 | 0.94 | 1.8 | FUL(H) BRE(a) ARS(H) MCI(a) BHA(H) BOU(a) |

## 6-GW ticker — best defensive (ranked by Σ P(CS), GW2–7)

| # | Club | Σ P(CS) | mean P(CS) | mean def score | Fixtures GW2→7 |
|---|---|---:|---:|---:|---|
| 1 | ARS | 2.33 | 39% | 9.0 | AVL(a) CHE(H) SUN(a) BHA(a) LEE(H) NFO(a) |
| 2 | MCI | 2.22 | 37% | 8.0 | CRY(a) COV(H) MUN(a) SUN(H) LIV(a) IPS(H) |
| 3 | MUN | 1.85 | 31% | 7.0 | IPS(H) EVE(a) MCI(H) FUL(a) TOT(H) LEE(a) |
| 4 | NFO | 1.72 | 29% | 6.0 | LIV(a) TOT(H) AVL(a) COV(H) CRY(a) ARS(H) |
| 5 | LIV | 1.72 | 29% | 6.2 | NFO(H) IPS(a) FUL(H) BOU(a) MCI(H) BRE(a) |
| 6 | CRY | 1.72 | 29% | 6.5 | MCI(H) FUL(a) IPS(H) LEE(a) NFO(H) BHA(a) |
| 7 | BHA | 1.68 | 28% | 6.3 | CHE(a) LEE(H) COV(a) ARS(H) SUN(a) CRY(H) |
| 8 | BRE | 1.60 | 27% | 6.0 | LEE(a) SUN(H) BOU(a) CHE(H) AVL(a) LIV(H) |
| 9 | CHE | 1.58 | 26% | 5.5 | BHA(H) ARS(a) HUL(H) BRE(a) BOU(H) EVE(a) |
| 10 | NEW | 1.55 | 26% | 5.8 | TOT(a) BOU(H) LEE(a) HUL(H) COV(a) AVL(H) |
| 11 | FUL | 1.50 | 25% | 5.3 | SUN(a) CRY(H) LIV(a) MUN(H) IPS(a) HUL(H) |
| 12 | EVE | 1.50 | 25% | 5.3 | BOU(a) MUN(H) TOT(a) IPS(H) HUL(a) CHE(H) |
| 13 | TOT | 1.46 | 24% | 5.2 | NEW(H) NFO(a) EVE(H) AVL(H) MUN(a) COV(H) |
| 14 | LEE | 1.37 | 23% | 4.8 | BRE(H) BHA(a) NEW(H) CRY(H) ARS(a) MUN(H) |
| 15 | BOU | 1.36 | 23% | 4.7 | EVE(H) NEW(a) BRE(H) LIV(H) CHE(a) SUN(H) |
| 16 | AVL | 1.36 | 23% | 4.7 | ARS(H) HUL(a) NFO(H) TOT(a) BRE(H) NEW(a) |
| 17 | COV | 1.26 | 21% | 4.2 | HUL(H) MCI(a) BHA(H) NFO(a) NEW(H) TOT(a) |
| 18 | HUL | 1.08 | 18% | 3.5 | COV(a) AVL(H) CHE(a) NEW(a) EVE(H) FUL(a) |
| 19 | IPS | 1.08 | 18% | 3.0 | MUN(a) LIV(H) CRY(a) EVE(a) FUL(H) MCI(a) |
| 20 | SUN | 1.02 | 17% | 3.0 | FUL(H) BRE(a) ARS(H) MCI(a) BHA(H) BOU(a) |

## Per club-fixture detail — GW2–GW7

Home/away adjusted. `att` / `def` are presentation deciles only — never inputs.
`±` marks a P(CS) carrying the **±15pp promoted-club band** (C4): either the club
or its opponent is COV / HUL / IPS.

| Club | GW | Opp | H/A | FPL FDR | λ_att | λ_def | P(CS) | att | def |
|---|---|---|---|---|---|---|---|---|---|
| ARS | 2 | AVL | A | 4 | 1.81 | 0.93 | 39% | 9 | 9 |
| ARS | 3 | CHE | H | 4 | 1.78 | 1.24 | 29% | 9 | 7 |
| ARS | 4 | SUN | A | 3 | 1.86 | 0.77 | 46% | 9 | 10 |
| ARS | 5 | BHA | A | 3 | 1.47 | 1.06 | 35% | 6 | 8 |
| ARS | 6 | LEE | H | 2 | 1.75 | 0.87 | 42% | 9 | 10 |
| ARS | 7 | NFO | A | 3 | 1.47 | 0.88 | 41% | 6 | 10 |
| AVL | 2 | ARS | H | 4 | 0.93 | 1.81 | 16% | 2 | 2 |
| AVL | 3 | HUL | A | 2 | 1.58 | 1.10 | 33% ± | 7 | 8 |
| AVL | 4 | NFO | H | 3 | 1.27 | 1.27 | 28% | 4 | 7 |
| AVL | 5 | TOT | A | 3 | 1.38 | 1.34 | 26% | 5 | 6 |
| AVL | 6 | BRE | H | 3 | 1.26 | 1.91 | 15% | 4 | 2 |
| AVL | 7 | NEW | A | 3 | 1.41 | 1.74 | 18% | 5 | 3 |
| BHA | 2 | CHE | A | 4 | 1.29 | 1.96 | 14% | 4 | 1 |
| BHA | 3 | LEE | H | 2 | 1.47 | 1.18 | 31% | 6 | 8 |
| BHA | 4 | COV | A | 2 | 1.65 | 0.91 | 40% ± | 8 | 10 |
| BHA | 5 | ARS | H | 4 | 1.06 | 1.47 | 23% | 3 | 5 |
| BHA | 6 | SUN | A | 3 | 1.57 | 1.05 | 35% | 7 | 9 |
| BHA | 7 | CRY | H | 3 | 1.47 | 1.42 | 24% | 6 | 5 |
| BOU | 2 | EVE | H | 3 | 1.70 | 1.20 | 30% | 8 | 8 |
| BOU | 3 | NEW | A | 3 | 1.62 | 1.56 | 21% | 7 | 4 |
| BOU | 4 | BRE | H | 3 | 1.45 | 1.71 | 18% | 6 | 3 |
| BOU | 5 | LIV | H | 4 | 1.42 | 1.68 | 19% | 6 | 3 |
| BOU | 6 | CHE | A | 4 | 1.31 | 2.15 | 12% | 5 | 1 |
| BOU | 7 | SUN | H | 2 | 1.84 | 0.99 | 37% | 9 | 9 |
| BRE | 2 | LEE | A | 3 | 1.59 | 1.35 | 26% | 7 | 6 |
| BRE | 3 | SUN | H | 2 | 2.27 | 0.89 | 41% | 10 | 10 |
| BRE | 4 | BOU | A | 3 | 1.71 | 1.45 | 24% | 8 | 5 |
| BRE | 5 | CHE | H | 4 | 1.88 | 1.67 | 19% | 9 | 3 |
| BRE | 6 | AVL | A | 4 | 1.91 | 1.26 | 28% | 9 | 7 |
| BRE | 7 | LIV | H | 4 | 1.75 | 1.51 | 22% | 9 | 5 |
| CHE | 2 | BHA | H | 2 | 1.96 | 1.29 | 27% | 10 | 7 |
| CHE | 3 | ARS | A | 5 | 1.24 | 1.78 | 17% | 4 | 2 |
| CHE | 4 | HUL | H | 2 | 2.83 | 0.81 | 45% ± | 10 | 10 |
| CHE | 5 | BRE | A | 3 | 1.67 | 1.88 | 15% | 8 | 2 |
| CHE | 6 | BOU | H | 3 | 2.15 | 1.31 | 27% | 10 | 6 |
| CHE | 7 | EVE | A | 3 | 1.97 | 1.32 | 27% | 10 | 6 |
| COV | 2 | HUL | H | 2 | 1.31 | 1.03 | 36% ± | 4 | 9 |
| COV | 3 | MCI | A | 5 | 0.64 | 2.59 | 7% ± | 1 | 1 |
| COV | 4 | BHA | H | 2 | 0.91 | 1.65 | 19% ± | 1 | 3 |
| COV | 5 | NFO | A | 3 | 0.78 | 1.60 | 20% ± | 1 | 4 |
| COV | 6 | NEW | H | 2 | 1.16 | 1.63 | 20% ± | 3 | 3 |
| COV | 7 | TOT | A | 3 | 0.98 | 1.45 | 23% ± | 2 | 5 |
| CRY | 2 | MCI | H | 4 | 1.36 | 1.72 | 18% | 5 | 3 |
| CRY | 3 | FUL | A | 3 | 1.66 | 1.11 | 33% | 8 | 8 |
| CRY | 4 | IPS | H | 2 | 2.00 | 0.97 | 38% ± | 10 | 9 |
| CRY | 5 | LEE | A | 3 | 1.46 | 1.39 | 25% | 6 | 6 |
| CRY | 6 | NFO | H | 3 | 1.65 | 1.06 | 35% | 8 | 8 |
| CRY | 7 | BHA | A | 3 | 1.42 | 1.47 | 23% | 6 | 5 |
| EVE | 2 | BOU | A | 3 | 1.20 | 1.70 | 18% | 3 | 3 |
| EVE | 3 | MUN | H | 4 | 1.26 | 1.58 | 21% | 4 | 4 |
| EVE | 4 | TOT | A | 3 | 1.37 | 1.27 | 28% | 5 | 7 |
| EVE | 5 | IPS | H | 2 | 1.53 | 1.10 | 33% ± | 7 | 8 |
| EVE | 6 | HUL | A | 2 | 1.58 | 1.04 | 35% ± | 7 | 9 |
| EVE | 7 | CHE | H | 4 | 1.32 | 1.97 | 14% | 5 | 1 |
| FUL | 2 | SUN | A | 3 | 1.18 | 1.22 | 30% | 3 | 7 |
| FUL | 3 | CRY | H | 3 | 1.11 | 1.66 | 19% | 3 | 3 |
| FUL | 4 | LIV | A | 4 | 0.91 | 2.06 | 13% | 1 | 1 |
| FUL | 5 | MUN | H | 4 | 1.08 | 1.59 | 20% | 3 | 4 |
| FUL | 6 | IPS | A | 2 | 1.13 | 1.28 | 28% ± | 3 | 7 |
| FUL | 7 | HUL | H | 2 | 1.57 | 0.90 | 41% ± | 7 | 10 |
| HUL | 2 | COV | A | 2 | 1.03 | 1.31 | 27% ± | 2 | 7 |
| HUL | 3 | AVL | H | 3 | 1.10 | 1.58 | 20% ± | 3 | 4 |
| HUL | 4 | CHE | A | 4 | 0.81 | 2.83 | 6% ± | 1 | 1 |
| HUL | 5 | NEW | A | 3 | 0.99 | 2.05 | 13% ± | 2 | 1 |
| HUL | 6 | EVE | H | 3 | 1.04 | 1.58 | 21% ± | 2 | 4 |
| HUL | 7 | FUL | A | 3 | 0.90 | 1.57 | 21% ± | 1 | 4 |
| IPS | 2 | MUN | A | 4 | 0.94 | 1.91 | 15% ± | 2 | 2 |
| IPS | 3 | LIV | H | 4 | 1.07 | 1.84 | 16% ± | 3 | 2 |
| IPS | 4 | CRY | A | 3 | 0.97 | 2.00 | 14% ± | 2 | 1 |
| IPS | 5 | EVE | A | 3 | 1.10 | 1.53 | 22% ± | 3 | 4 |
| IPS | 6 | FUL | H | 2 | 1.28 | 1.13 | 32% ± | 4 | 8 |
| IPS | 7 | MCI | A | 5 | 0.78 | 2.35 | 10% ± | 1 | 1 |
| LEE | 2 | BRE | H | 3 | 1.35 | 1.59 | 20% | 5 | 4 |
| LEE | 3 | BHA | A | 3 | 1.18 | 1.47 | 23% | 3 | 5 |
| LEE | 4 | NEW | H | 2 | 1.75 | 1.26 | 28% | 9 | 7 |
| LEE | 5 | CRY | H | 3 | 1.39 | 1.46 | 23% | 5 | 5 |
| LEE | 6 | ARS | A | 5 | 0.87 | 1.75 | 17% | 1 | 2 |
| LEE | 7 | MUN | H | 4 | 1.36 | 1.40 | 25% | 5 | 6 |
| LIV | 2 | NFO | H | 3 | 1.76 | 1.01 | 37% | 9 | 9 |
| LIV | 3 | IPS | A | 2 | 1.84 | 1.07 | 34% ± | 9 | 8 |
| LIV | 4 | FUL | H | 2 | 2.06 | 0.91 | 40% | 10 | 10 |
| LIV | 5 | BOU | A | 3 | 1.68 | 1.42 | 24% | 8 | 5 |
| LIV | 6 | MCI | H | 4 | 1.45 | 1.64 | 19% | 6 | 3 |
| LIV | 7 | BRE | A | 3 | 1.51 | 1.75 | 17% | 6 | 2 |
| MCI | 2 | CRY | A | 3 | 1.72 | 1.36 | 26% | 8 | 6 |
| MCI | 3 | COV | H | 2 | 2.59 | 0.64 | 52% ± | 10 | 10 |
| MCI | 4 | MUN | A | 4 | 1.67 | 1.30 | 27% | 8 | 7 |
| MCI | 5 | SUN | H | 2 | 2.46 | 0.74 | 48% | 10 | 10 |
| MCI | 6 | LIV | A | 4 | 1.64 | 1.45 | 23% | 8 | 5 |
| MCI | 7 | IPS | H | 2 | 2.35 | 0.78 | 46% ± | 10 | 10 |
| MUN | 2 | IPS | H | 2 | 1.91 | 0.94 | 39% ± | 9 | 9 |
| MUN | 3 | EVE | A | 3 | 1.58 | 1.26 | 28% | 7 | 7 |
| MUN | 4 | MCI | H | 4 | 1.30 | 1.67 | 19% | 4 | 3 |
| MUN | 5 | FUL | A | 3 | 1.59 | 1.08 | 34% | 7 | 8 |
| MUN | 6 | TOT | H | 3 | 1.98 | 0.94 | 39% | 10 | 9 |
| MUN | 7 | LEE | A | 3 | 1.40 | 1.36 | 26% | 5 | 6 |
| NEW | 2 | TOT | A | 3 | 1.54 | 1.40 | 25% | 7 | 6 |
| NEW | 3 | BOU | H | 3 | 1.56 | 1.62 | 20% | 7 | 4 |
| NEW | 4 | LEE | A | 3 | 1.26 | 1.75 | 17% | 4 | 2 |
| NEW | 5 | HUL | H | 2 | 2.05 | 0.99 | 37% ± | 10 | 9 |
| NEW | 6 | COV | A | 2 | 1.63 | 1.16 | 31% ± | 8 | 8 |
| NEW | 7 | AVL | H | 3 | 1.74 | 1.41 | 25% | 8 | 6 |
| NFO | 2 | LIV | A | 4 | 1.01 | 1.76 | 17% | 2 | 2 |
| NFO | 3 | TOT | H | 3 | 1.50 | 0.94 | 39% | 6 | 9 |
| NFO | 4 | AVL | A | 4 | 1.27 | 1.27 | 28% | 4 | 7 |
| NFO | 5 | COV | H | 2 | 1.60 | 0.78 | 46% ± | 7 | 10 |
| NFO | 6 | CRY | A | 3 | 1.06 | 1.65 | 19% | 3 | 3 |
| NFO | 7 | ARS | H | 4 | 0.88 | 1.47 | 23% | 1 | 5 |
| SUN | 2 | FUL | H | 2 | 1.22 | 1.18 | 31% | 4 | 8 |
| SUN | 3 | BRE | A | 3 | 0.89 | 2.27 | 10% | 1 | 1 |
| SUN | 4 | ARS | H | 4 | 0.77 | 1.86 | 16% | 1 | 2 |
| SUN | 5 | MCI | A | 5 | 0.74 | 2.46 | 9% | 1 | 1 |
| SUN | 6 | BHA | H | 2 | 1.05 | 1.57 | 21% | 2 | 4 |
| SUN | 7 | BOU | A | 3 | 0.99 | 1.84 | 16% | 2 | 2 |
| TOT | 2 | NEW | H | 2 | 1.40 | 1.54 | 21% | 5 | 4 |
| TOT | 3 | NFO | A | 3 | 0.94 | 1.50 | 22% | 2 | 5 |
| TOT | 4 | EVE | H | 3 | 1.27 | 1.37 | 25% | 4 | 6 |
| TOT | 5 | AVL | H | 3 | 1.34 | 1.38 | 25% | 5 | 6 |
| TOT | 6 | MUN | A | 4 | 0.94 | 1.98 | 14% | 2 | 1 |
| TOT | 7 | COV | H | 2 | 1.45 | 0.98 | 37% ± | 6 | 9 |

## Top fixture swings

Ranked by |Δ mean λ_att| between GW2–4 and GW5–7, defensive Δ alongside.

| # | Club | Turns | λ_att GW2-4 → GW5-7 | P(CS) GW2-4 → GW5-7 | Note |
|---|---|---|---|---|---|
| 1 | NEW | **easier from GW5** | 1.45 → 1.81 (+0.36) | 21% → 31% (+10.3pp) | The window's only club improving materially at **both** ends. Opens TOT(a), BOU(H), LEE(a); closes HUL(H) 37%, COV(a) 31%, AVL(H). Newcastle defenders are the cheapest route into a +10pp swing — but note two of the three easy fixtures are promoted clubs and carry the ±15pp band. |
| 2 | LIV | **harder from GW5** | 1.89 → 1.55 (−0.34) | 37% → 20% (**−16.7pp**) | **The largest swing of any kind in the window.** NFO(H), IPS(a), FUL(H) is one of the best opening triples in the league; then BOU(a), MCI(H), BRE(a) — and Brentford now rates 3rd on attack. Liverpool defence is a three-gameweek asset. Sell into GW5. |
| 3 | ARS | **attack cools, defence does not** | 1.81 → 1.56 (−0.25) | 38% → 39% (+1.3pp) | The attacking dip is real but the clean-sheet run is flat-to-better. Arsenal *defenders* have no swing to trade around; Arsenal *attackers* do. |
| 4 | LEE | **harder from GW5** | 1.43 → 1.21 (−0.22) | 24% → 22% | ARS(a) and MUN(H) close the window. |
| 5 | EVE | **easier from GW5** | 1.28 → 1.48 (+0.20) | 22% → 28% (+5.2pp) | IPS(H) then HUL(a), then CHE(H) spoils the run at GW7. A narrower version of the swing GW1 flagged, and it now ends one gameweek earlier. |

**Runner-up on defence: FUL +9.2pp** (20% → 30%), turning at GW5 and peaking
with HUL(H) at GW7 (41% P(CS), the club's best of the season so far). Fulham
defenders are the cheapest entry to that run, but the two best fixtures in it
are both promoted opposition and carry the ±15pp band.

Two clubs get materially harder defensively without an attacking swing to
compensate: **BRE −7.0pp** (CHE(H), AVL(a), LIV(H) to close) and **CHE −6.7pp**.

### Multi-GW runs (≥3 consecutive GWs in the top/bottom third)

| Club | Easy attacking run | Easy defensive run | Hard defensive run |
|---|---|---|---|
| MCI | GW5–7 | GW5–7 | — |
| CHE | GW5–7 | — | GW5–7 |
| BRE | GW3–7 | — | GW4–7 |
| LIV | GW2–4 | GW2–4 | GW5–7 |
| ARS | GW2–4 | **GW2–7 (all six)** | — |
| MUN | — | GW5–7 | — |
| SUN | — | — | **GW3–7** |
| IPS | — | — | GW2–5 |
| HUL | — | — | GW3–7 |

**Arsenal is again the standout defensive hold** — a top-third clean-sheet
fixture in every gameweek of the window, on the league's best rating
(DEFW 0.67). That signal survived GW1 intact and is now the most stable thing
in this file.

**Sunderland GW3–7 and Hull GW3–7 are the hard defensive runs to sell into.**
Sunderland is the worst 6-GW defensive ticker in the league (17% mean P(CS))
and its rating just got worse.

## Coventry read — GW3 Triple Captain gate (C5)

Requested explicitly. **The gate is NOT cleared, and the GW1 evidence moved
against it, not toward it.**

| COV GW1 evidence | Value | League rank |
|---|---|---|
| xG created (ARS a) | **0.20** | **worst of 20** |
| xG conceded | **1.88** | 7th-highest |
| Implied DEFW from that match | **0.95** | ≈ league average |

The critical number is the third one. Once you adjust 1.88 xGA for the fact
that it was conceded **to Arsenal, away**, Coventry's implied defensive rating
is **0.95 — essentially league-average**, not bottom-three. Blended at 75/25,
COV DEFW falls from 1.30 to **1.21**. The one match of real evidence we have
says Coventry's defence is *better* than we assumed, which makes MCI v COV a
*worse* Triple Captain fixture than the GW1 model implied.

Coventry's **attack** is confirmed dire and got no reprieve — 0.20 xG is the
worst single-match figure of the round, and COV stays 19th on the attacking
ticker.

### Sensitivity — how much of the fixture is COV-dependent

MCI v COV (H, GW3) rates **λ_att 2.59**. Manchester City's mean λ_att across
GW2–7 is **2.07**. So **0.52 goals — 20% of the fixture's expected output —
comes from Coventry being Coventry**, and that term sits inside the ±15pp band:

| COV DEFW | MCI GW3 λ_att |
|---|---|
| 1.03 (band floor) | **2.20** |
| 1.21 (central) | **2.59** |
| 1.39 (band ceiling) | **2.98** |

A 0.78-goal spread on the captain's own fixture. **If the Triple Captain case
needs any part of that 0.52 uplift to clear, C5 requires deferring the chip.**
Per C5 the decision must rest on Haaland's fixture-independent EP alone, which
is the player-analyst's number, not mine — but the fixture side of the ledger
gives no help worth relying on.

**GW2 cannot resolve this, as the retro predicted.** Coventry's GW2 fixture is
COV v HUL — promoted against promoted, λ_att 1.31, the second-largest FDR
disagreement in the window. It cannot test Coventry against an elite attack. At
the GW3 deadline the decision will still rest on one elite-opposition data
point, and that point now reads *average*, not *soft*.

### A cleaner alternative exists

**MCI v SUN (H, GW5) rates λ_att 2.46 — 95% of the Coventry fixture's value,
with no promoted-club dependency at all.** Sunderland carries a full prior
season of PL data (0.89 squad-minute coverage), sits on a DEFW of 1.15 that
GW1 *worsened*, and holds the league's worst 6-GW defensive ticker (17% mean
P(CS)). MCI v IPS (H, GW7) rates 2.35 but reintroduces the band.

Recommendation to the optimizer: **if the Triple Captain is deferred at GW3,
GW5 is the natural re-aim and it is barely worse.** That converts C5 from a
cost into an option.

## FPL FDR vs this model

| Pairing | Pearson r |
|---|---|
| FDR vs −λ_att (attacking difficulty) | **0.455** |
| FDR vs −P(CS) (defensive difficulty) | **0.633** |

The GW1 headline figure was 0.633, which corresponds exactly to the
**defensive** pairing here. On the attacking side FDR is materially weaker —
it explains barely a fifth of the variance in λ_att. **FDR is a passable proxy
for clean-sheet difficulty and a poor one for attacking returns.**

The mechanism is unchanged from GW1: **FDR grades the opponent, not the
fixture.** It ignores the rated club's own quality, so a weak club facing
another weak club scores as "easy" when its actual expected output stays poor.

| Club | GW | Fixture | FDR | Model | λ_att | P(CS) | Reading |
|---|---|---|---|---|---|---|---|
| COV | 4 | BHA (H) | 2 | 4.5 | 0.91 | 19% ± | Largest disagreement in the window. Brighton's attack rating just rose 0.13; Coventry at home is not an easy fixture for Coventry. |
| HUL | 2 | COV (a) | 2 | 4.3 | 1.03 | 27% ± | Promoted v promoted, graded easy for both sides. Low-scoring, not high-yield. |
| SUN | 6 | BHA (H) | 2 | 4.3 | 1.05 | 21% | Sunderland's own rating is the problem, not the opponent's. |
| FUL | 6 | IPS (a) | 2 | 4.1 | 1.13 | 28% ± | |
| COV | 6 | NEW (H) | 2 | 4.1 | 1.16 | 20% ± | |

In the other direction FDR over-punishes strong clubs' marquee fixtures:

| Club | GW | Fixture | FDR | Model | λ_att | P(CS) | Reading |
|---|---|---|---|---|---|---|---|
| CHE | 4 | HUL (H) | 2 | 1.0 | **2.83** | 45% ± | Best attacking fixture in the window by a distance. FDR 2 is nowhere near generous enough. |
| BRE | 6 | AVL (a) | 4 | 2.7 | 1.91 | 28% | Villa's DEFW just rose to 1.11. Do not bench Brentford attackers here. |
| BRE | 5 | CHE (H) | 4 | 2.7 | 1.88 | 19% | |
| ARS | 2 | AVL (a) | 4 | 2.9 | 1.81 | 39% | Same failure as GW1, now worse — Villa is a *weaker* opponent than a week ago. |
| ARS | 3 | CHE (H) | 4 | 2.9 | 1.78 | 29% | Hard defensively, but Arsenal's attacking output holds. |

Practical rule for the optimizer, unchanged: **do not use FDR to bench a strong
club's assets, and do not use FDR to buy a weak club's assets.**

## Blank and double gameweeks

**Still none across the entire season.** Re-verified over the full 380-fixture
list, not just the window: zero `event: null` fixtures, every GW1–38 holds
exactly 10 matches, and every club has exactly one fixture in every gameweek.
Identical to the GW1 snapshot.

Implication for the phase-2 chip agent: **no DGW/BGW structure exists to plan
around.** Bench Boost and Triple Captain must be timed on fixture quality
alone. Expect this to change — real blanks and doubles arrive later via cup
progression and postponements, and will surface as `event: null`. Re-check
every cycle; the first null-event fixture is the signal.

## Uncertainty flags

| Flag | Severity | Change vs GW1 | Detail |
|---|---|---|---|
| **Zeroed split-strength fields** | **HIGH** | unchanged | All four fields 0 for all 20 clubs, `strength` null, for the second cycle running. Defence ratings are still 75–80% driven by a 5-level tier prior. Mid-table P(CS) gaps under ~4pp remain noise. |
| **Promoted clubs (COV, HUL, IPS)** | **HIGH** | **band added (C4)** | ±15pp on every P(CS) involving them, through GW3. IPS moved most of any club (DEFW −0.16) on a single match against Sunderland — that is exactly the kind of move the band exists to distrust. COV and HUL still have almost no PL minutes among their defenders. |
| **Single-match sample** | **HIGH** | **new** | Every current-season input is n = 1. Five clubs' implied ratings were clipped at the [0.55, 1.80] guard band (AVL, TOT, BHA, BRE, LEE among them), meaning the raw data wanted to move them further than I allowed. Those clips are a deliberate brake, and they will unwind as n grows. |
| **Defence ratings assumption-dominated** | **MEDIUM** | **downgraded from HIGH** | Team xGA is now measured rather than assumed, but only 20–25% of each rating is empirical. Downgraded because the *method* gap is closed and the remaining problem is sample size, which time fixes on its own. |
| **Squad-turnover contamination** | **MEDIUM** | unchanged | Prior-season rows are keyed to each player's *current* club, so production earned elsewhere is credited to the new club. Worst-affected: NEW, FUL, BOU, LIV, AVL, CHE. Decays as current-season weight grows. |
| **Crystal Palace finishing** | **LOW→MEDIUM** | **escalated** | GW1 flagged CRY as an xG over-rater (92.4 prior xGI vs 70 actual G+A). GW1 repeated it exactly: **1.96 xG, 0 goals** at Everton. Two data points now point the same way. If this is a squad trait rather than variance, CRY λ_att is overstated by roughly 15%. Second occurrence — the player-analyst should discount Palace attackers accordingly. |
| **International break splits GW5→GW6** | **MEDIUM** | **new, was LOW** | A **19-day gap** separates the last GW5 match from the first GW6 match. GW6 and GW7 ratings are the least reliable in this window — squad news, injuries and returning-international fatigue will all move materially across it. Treat the GW6–7 half of every swing note as provisional. |
| **Congested schedule** | **LOW** | improved | **No club has a turnaround under 4 days anywhere in GW2–7.** Inter-gameweek gaps are 4, 5, 4, 19, 4, 4 days. Rotation pressure from fixture density is not a factor in this window. |
| **Cup involvement** | **UNKNOWN** | unchanged | The FPL API exposes no European or domestic-cup calendar. Rotation risk for clubs in continental competition is **not modelled anywhere in this ticker**. The player-analyst must apply it independently — still the largest unmodelled factor, and it now bites hardest on MCI, ARS, CHE, LIV, MUN, TOT and NEW. |

## Handoff to downstream agents

- Consume **λ_att** and **P(CS)** from the per club-fixture table. Ignore the 1–10 scores.
- **Treat any `±` P(CS) as a range, not a point.** Per C4, a promoted-club-derived
  term must never be the largest single EP component for a selected player.
- **ARS remains the best defensive hold** — DEFW 0.67, top-third clean-sheet
  fixture in all six gameweeks, no swing to trade around. Arsenal's *attack*
  cools from GW5 (1.81 → 1.56); its defence does not.
- **LIV defence is a GW2–4 asset only.** −16.7pp is the largest swing in the
  window. Buy now, sell into GW5.
- **MCI is the best attacking ticker (2.07 λ/GW) and its two best fixtures are
  GW3 COV(H) 2.59 and GW5 SUN(H) 2.46.** Only the second is band-free.
- **CHE v HUL (H, GW4), λ_att 2.83, is the single best attacking fixture in the
  window** — but it carries the ±15pp band. Chelsea's defence simultaneously
  worsens by 6.7pp over the same stretch.
- **BRE is now a genuine top-3 attack (ATT 1.29)** with an easy attacking run
  GW3–7 — and a hard defensive run GW4–7. Buy the attackers, not the defenders.
- **NEW is the only club improving at both ends from GW5** (+0.36 λ_att,
  +10.3pp P(CS)), though two of the three fixtures driving it are promoted
  opposition.
- **Avoid AVL and TOT defenders.** Both took the window's worst defensive
  downgrades (+0.17, +0.16 DEFW) and both were clipped at the guard band,
  meaning the raw GW1 data wanted them worse still.
- **SUN GW3–7 and HUL GW3–7** are the hard defensive runs to sell into.
- **Discount Crystal Palace attackers ~15%** — second consecutive xG-over-actual
  observation.
- **GW3 Triple Captain: the gate is not cleared and GW1 moved it further away.**
  GW5 MCI v SUN is a band-free alternative at 95% of the value.
