# GW6 — 6-Gameweek Fixture Ticker (GW6–GW11)

Window **GW6–GW11**, all 20 clubs, no blanks, no doubles. Ratings rest on
**five** played rounds; the blend has advanced from GW5's 59/41 to **53/47** on
established-club attack.

Downstream agents consume `lambda_att` and `p_cs` from
`data/analysis/gw6/fixtures.json`. The 1–10 attack/defence scores in this file
are presentation-only deciles and must not be read as inputs.

| Headline | Read |
|---|---|
| Best attacking ticker | **MCI** Σλ_att 11.79, then ARS 10.26, BRE 10.17, CHE 10.07 |
| Best defensive ticker | **ARS** ΣP(CS) 2.24, then MCI 1.77, BRE 1.71 |
| Worst combined | **HUL** (20th attack, 20th defence), then **COV** (19th/11th); **BHA** 5th on attack and **19th** on defence |
| Largest swings | **ARS +0.48** attack improving (GW9–11 v GW6–8); **CRY −0.41** and **NEW −0.40** attack declining; **FUL** worst combined (−0.29 / −0.21) |
| Blanks / doubles | none in GW6–GW11 |

## What changed since GW5

### 1. Round 5 added through the unchanged pipeline

The club-attribution rule (attribute each `element-summary` history row by the
row's own fixture, never by the player's current bootstrap `team`) is carried
forward. Re-running rounds 1–4 through the GW6 snapshot reproduces GW5's
published xG/xGA column on all 20 clubs to the last decimal, its 56-of-160
clip count, and its ATT/DEFW on 38 of 40 values; the other two differ by 0.01
(CRY ATT 1.07 v 1.06, EVE DEFW 0.93 v 0.94), a rounding-edge effect of the
snapshot's slightly different summary set.

Coverage: 435 element summaries read; 141 player-rounds missing from the
snapshot recovered from the `event-live` files (rounds 1–5), worth **4.69 xG**
league-wide. Round 5 alone needed only 19 player-rounds (0.18 xG), so the
recovery matters less each round.

### 2. FPL has still not populated the split-strength fields

Sixth gameweek running: `strength_attack_home/away` and
`strength_defence_home/away` are **0** for all 20 clubs, and `strength` is
`null`. Defence priors still come from the five-tier `strength_overall_home/away`
and remain **ASSUMPTION**-grade. Current-season data is now 56–62% of every
DEFW, so the weak prior is a minority input everywhere.

### 3. The blend advanced, on the schedule GW2 set

No parameter was retuned. Each prior keeps its fixed worth of `k`
match-equivalents; the match count `n` grew from 4 to 5.

### 4. Clipping fell sharply in round 5

**64 of 200** implied ratings hit the [0.55, 1.80] guard. Round 5 alone
contributed **8 of 40** (20.0%), against round 4's 14 of 40 (35.0%) — the
lowest single-round rate yet. Four of the eight came from two matches:
MCI v SUN and BRE v CHE (two each).

### 5. The scheduled `base_lambda` re-test — base held

GW3 scheduled a GW6 re-test of the 1.54 / 1.33 base (2.87 goals per match).
League xG per match by round: **3.13 / 3.41 / 2.86 / 2.67 / 3.24**. Over 50
matches: home **1.65**, away **1.41**, total **3.06** — **+6.7%** above the
base (home +7.3%, away +5.9%).

The base is **kept**. Per-match xG totals vary by roughly a goal, so the
standard error on a 50-match mean is about 0.14; 2.87 sits about 1.4 standard
errors below the observed mean — not a clear signal. The retro's pool bias
points the same way but is small (cumulative +0.10 points per player). Raising
the base 6.7% would lift every λ_att by the same proportion and cut every
P(CS) by roughly 0.02–0.03, so the direction of any future fix is known. Next
re-test at GW10 (n=90). Logged as a follow-up row to the GW3 backlog item.

## Corrections applied

Binding set: the corrections addressed to **A2** in `data/retro/gw1.md`
through `data/retro/gw5.md` — C4 (revised by C12), C5 and C12. GW5's retro
raised no new corrections.

### C12 (A2) — the promoted-club band, two-sided

Carried forward unchanged. COV, HUL and IPS on *either* side of a fixture set
`band: true` on *both* club-rows — **34 of 120 rows** this window (GW5: 34).

1. **The band covers `lambda_att` as well as `p_cs`.** Read λ_att ±15% and
   P(CS) ±15pp on any `±` row.
2. **No haircut to the central attacking estimate.** Every club facing promoted
   opposition carries its full modelled λ_att: **MCI 2.24 v IPS(H)**, ARS 2.13
   v HUL(H), BRE 1.82 at HUL, BHA 1.73 at HUL, EVE 1.62 v COV(H), FUL 1.54 v
   HUL(H), CRY 1.53 at COV. The uncertainty is published as a band, never as a
   discount.
3. C4's residual prohibition — *never let a promoted-club fixture be the single
   largest defensive EP term for a selected player* — **stands for defensive
   terms only**. The rows it forbids, P(CS) ≥ 0.30:

   | GW | Club | Fixture | P(CS) |
   |---:|---|---|---:|
   | 10 | ARS | HUL (H) | **0.49** |
   | 7 | TOT | COV (H) | 0.41 |
   | 10 | EVE | COV (H) | 0.39 |
   | 7 | FUL | HUL (H) | 0.35 |
   | 8 | BRE | HUL (A) | 0.35 |
   | 6 | EVE | HUL (A) | 0.33 |
   | 7 | MCI | IPS (H) | 0.33 |
   | 9 | SUN | COV (A) | 0.31 |
   | 11 | TOT | IPS (H) | 0.31 |
   | 8 | FUL | COV (A) | 0.30 |
   | 8 | NFO | IPS (A) | 0.30 |
   | 9 | IPS | HUL (A) | 0.30 |
   | 11 | CRY | COV (A) | 0.30 |
   | 11 | BHA | HUL (A) | 0.30 |

   **ARS v HUL(H) at 0.49 is again the single best defensive row in the window,
   and it is banded.** An Arsenal defender selected for GW10 must not take his
   largest defensive term from it. For GW6 itself, the only tripping row is
   EVE at HUL (0.33).

**Promoted-club convergence — the GW6 revisit.** GW5 scheduled this revisit at
n=5. **The band is kept.** Two reasons:

- Round 5's promoted-club defensive readings are still scattered: implied
  DEFW COV 0.78, HUL 0.94, IPS 1.55 (2.24 xG conceded at Everton). Across five
  rounds IPS alone has readings from the 0.55 floor to the 1.80 ceiling.
- The retro lists C12 as **active — untested**: its audit is blocked until C17
  (largest EP term per squad row) ships. Relaxing a binding correction before
  it can be tested is not A2's call.

Next revisit at GW8 (n=7), or earlier if a retro releases C12.

### C5 (A2, A4) — the Triple Captain gate

Active and binding. Examined under its own heading below. Short version: **the
GW9 earmark is held; GW11 FUL(H) now ties it on λ_att, GW7 stays ineligible.**

### C4 (A2) — superseded

Revised by C12. Its confidence-downgrade instruction is discharged by keeping
promoted-club uncertainty at HIGH with the band unrelaxed at n=5.

## Model

```
lambda_att(i vs j, home) = 1.54 * ATT_i * DEFW_j
lambda_att(i vs j, away) = 1.33 * ATT_i * DEFW_j
lambda_def(i)            = lambda_att(j)        # opponent-symmetric
P(CS)_i                  = exp(-lambda_def_i)   # Poisson P(0 conceded)
```

Unchanged since GW1. `ATT` and `DEFW` are multiplicative indices renormalised
to a 20-club mean of exactly 1.00 after blending. λ values in the JSON are
computed from the two-decimal ratings it publishes, so `fpl ep` and this file
agree exactly.

**P(CS) excludes the FPL 60-minute requirement and rotation risk** — the
player-analyst applies those.

### Blend

Each played match yields an opponent- and venue-adjusted implied rating:

```
impATT_i  = xG_i  / (base_venue_i  * DEFW_opponent)
impDEFW_i = xGA_i / (base_venue_j  * ATT_opponent)
```

Both adjustments use the **GW1 pure-prior** ratings (the "prior" columns below)
as a fixed reference frame for the whole five-round history. Implied values
are clipped to **[0.55, 1.80]** before blending.

Rating = `(k * prior + Σ implied) / (k + n)`, with `n = 5`:

| Rating | Prior source | k | w_prior / w_current (n=5) | was at GW5 |
|---|---|---:|---|---|
| Attack, established | real prior-season squad xG | 5.7 | **53 / 47** | 59 / 41 |
| Defence, established | 5-tier `strength_overall` only | 4.0 | **44 / 56** | 50 / 50 |
| Attack, promoted | ASSUMPTION | 4.0 | **44 / 56** | 50 / 50 |
| Defence, promoted | ASSUMPTION | 3.0 | **38 / 62** | 43 / 57 |

Prior weight stays ≥20% through GW10 on every line (at GW10, n=9: established
attack 39%, promoted defence 25%).

## Team ratings — GW6 (five rounds blended)

`Δ GW5` compares `data/analysis/gw5/fixtures.json`. `*` marks an implied value
clipped to [0.55, 1.80] before blending. **A** marks a promoted club.

| Club | xG 1/2/3/4/5 | xGA 1/2/3/4/5 | impATT 1–5 | impDEFW 1–5 | clips |
|---|---|---|---|---|---:|
| MCI | 2.24 / 2.22 / 2.12 / 1.10 / 2.81 | 0.65 / 0.68 / 1.37 / 1.01 / 3.62 | 1.47 / 1.72 / 1.06 / 0.95 / 1.79 | 0.55* / 0.55* / 1.51 / 0.57 / 1.80* | 3 |
| ARS | 1.88 / 1.04 / 2.06 / 1.89 / 1.64 | 0.21 / 0.34 / 0.39 / 1.80 / 1.32 | 0.94 / 0.82 / 1.49 / 1.39 / 1.23 | 0.55* / 0.55* / 0.55* / 1.48 / 0.95 | 3 |
| BRE | 3.91 / 1.67 / 1.21 / 0.52 / 2.90 | 0.57 / 1.46 / 1.71 / 1.78 / 0.85 | 1.80* / 1.22 / 0.77 / 0.55* / 1.80* | 0.55* / 0.89 / 1.63 / 1.02 / 0.55* | 5 |
| CHE | 2.23 / 3.04 / 0.39 / 0.91 / 0.85 | 1.38 / 1.46 / 2.06 / 1.39 / 2.90 | 1.64 / 1.80* / 0.55* / 0.55* / 0.65 | 1.19 / 1.22 / 1.05 / 1.69 / 1.56 | 3 |
| BHA | 3.77 / 1.46 / 2.20 / 2.80 / 1.32 | 0.30 / 3.04 / 2.62 / 1.37 / 1.64 | 1.80* / 1.22 / 1.39 / 1.62 / 1.22 | 0.55* / 1.44 / 1.80* / 1.31 / 0.96 | 3 |
| LIV | 3.01 / 1.74 / 0.69 / 1.29 / 1.65 | 1.58 / 2.30 / 0.76 / 0.69 / 0.80 | 1.80* / 1.13 / 0.55* / 0.82 / 1.25 | 1.04 / 1.80* / 0.71 / 0.69 / 0.55* | 4 |
| MUN | 1.82 / 5.15 / 0.69 / 1.01 / 1.60 | 1.08 / 2.06 / 1.02 / 1.10 / 1.63 | 1.01 / 1.80* / 0.55* / 0.82 / 1.18 | 1.13 / 1.80* / 0.70 / 0.60 / 1.41 | 3 |
| LEE | 0.47 / 1.46 / 2.62 / 2.07 / 1.32 | 0.65 / 1.67 / 2.20 / 0.87 / 1.07 | 0.55* / 0.96 / 1.80* / 1.33 / 0.88 | 0.55* / 1.04 / 1.59 / 0.66 / 0.71 | 3 |
| BOU | 0.65 / 2.19 / 1.37 / 1.78 / 0.80 | 2.24 / 1.87 / 0.70 / 0.52 / 1.65 | 0.61 / 1.42 / 1.02 / 1.17 / 0.61 | 1.05 / 1.50 / 0.55* / 0.55* / 1.05 | 2 |
| CRY | 1.97 / 0.68 / 1.98 / 0.61 / 1.07 | 1.12 / 2.22 / 3.16 / 1.70 / 1.32 | 1.48 / 0.55 / 1.46 / 0.55* / 0.78 | 0.77 / 1.20 / 1.80* / 1.80* / 0.81 | 3 |
| SUN | 0.67 / 2.03 / 1.71 / 1.80 / 3.62 | 1.79 / 0.94 / 1.21 / 1.89 / 2.81 | 0.55* / 1.29 / 1.30 / 1.67 / 1.80* | 1.66 / 0.94 / 0.65 / 1.11 / 1.31 | 2 |
| NFO | 0.65 / 2.30 / 0.93 / 2.30 / 1.10 | 0.47 / 1.74 / 1.07 / 0.82 / 0.68 | 0.55* / 1.80* / 0.62 / 1.80* / 0.55* | 0.55* / 0.96 / 0.97 / 0.55* / 0.75 | 6 |
| EVE | 1.12 / 1.87 / 1.02 / 1.12 / 2.24 | 1.97 / 2.19 / 0.69 / 0.69 / 1.44 | 0.75 / 1.42 / 0.76 / 0.86 / 1.15 | 1.30 / 1.26 / 0.55* / 0.55* / 1.55 | 2 |
| IPS | 1.79 / 2.06 / 0.76 / 1.70 / 1.44 | 0.67 / 5.15 / 0.69 / 0.61 / 2.24 | 1.14 / 1.78 / 0.58 / 1.32 / 1.08 | 0.64 / 1.80* / 0.55* / 0.55* / 1.55 | 3 |
| FUL | 1.38 / 0.94 / 3.16 / 0.69 / 1.63 | 2.23 / 2.03 / 1.98 / 1.29 / 1.60 | 1.00 / 0.69 / 1.80* / 0.61 / 1.22 | 1.22 / 1.67 / 1.31 / 0.71 / 1.04 | 1 |
| AVL | 0.30 / 0.34 / 1.93 / 0.82 / 1.17 | 3.77 / 1.04 / 0.57 / 2.30 / 1.56 | 0.55* / 0.55* / 1.07 / 0.55* / 0.90 | 1.80* / 0.61 / 0.60 / 1.80* / 1.22 | 5 |
| NEW | 1.58 / 0.72 / 0.70 / 0.87 / 1.44 | 3.01 / 1.13 / 1.37 / 2.07 / 1.59 | 1.21 / 0.55 / 0.55* / 0.64 / 0.69 | 1.80* / 0.88 / 0.91 / 1.27 / 1.80* | 3 |
| TOT | 0.57 / 1.13 / 1.07 / 0.69 / 1.56 | 3.91 / 0.72 / 0.93 / 1.12 / 1.17 | 0.55* / 0.73 / 0.80 / 0.55* / 1.07 | 1.80* / 0.55* / 0.66 / 0.90 / 0.90 | 4 |
| HUL | 1.08 / 0.72 / 0.57 / 1.39 / 1.59 | 1.82 / 1.30 / 1.93 / 0.91 / 1.44 | 0.81 / 0.55* / 0.55* / 1.16 / 1.18 | 1.18 / 1.24 / 1.48 / 0.55* / 0.94 | 3 |
| COV | 0.21 / 1.30 / 1.37 / 1.37 / 0.68 | 1.88 / 0.72 / 2.12 / 2.80 / 1.10 | 0.55* / 0.62 / 1.29 / 0.89 / 0.55* | 0.95 / 0.87 / 0.99 / 1.80* / 0.78 | 3 |

| Club | ATT prior | **ATT** | Δ GW5 | DEFW prior | **DEFW** | Δ GW5 |
|---|---:|---:|---:|---:|---:|---:|
| MCI | 1.39 | **1.36** | +0.03 | 0.80 | **0.88** | +0.10 |
| ARS | 1.28 | **1.20** | -0.01 | 0.70 | **0.74** | +0.02 |
| BRE | 1.21 | **1.19** | +0.05 | 0.99 | **0.93** | -0.05 |
| CHE | 1.37 | **1.18** | -0.07 | 0.90 | **1.11** | +0.04 |
| BHA | 0.90 | **1.13** | +0.00 | 1.00 | **1.08** | -0.03 |
| LIV | 1.18 | **1.12** | +0.01 | 0.85 | **0.88** | -0.05 |
| MUN | 1.16 | **1.09** | +0.00 | 0.87 | **0.98** | +0.04 |
| LEE | 1.06 | **1.05** | -0.03 | 1.03 | **0.93** | -0.04 |
| BOU | 1.13 | **1.03** | -0.05 | 0.99 | **0.93** | +0.00 |
| CRY | 1.14 | **1.03** | -0.03 | 0.97 | **1.10** | -0.05 |
| SUN | 0.79 | **1.01** | +0.07 | 1.02 | **1.05** | +0.02 |
| NFO | 0.92 | **0.96** | -0.05 | 1.00 | **0.84** | -0.02 |
| EVE | 0.94 | **0.94** | +0.02 | 1.00 | **0.99** | +0.05 |
| IPS **A** | 0.70 | **0.94** | +0.01 | 1.26 | **1.07** | +0.05 |
| FUL | 0.75 | **0.87** | +0.02 | 1.02 | **1.08** | -0.02 |
| AVL | 0.98 | **0.84** | +0.00 | 0.95 | **1.06** | +0.01 |
| NEW | 0.99 | **0.84** | -0.03 | 1.01 | **1.15** | +0.06 |
| TOT | 0.83 | **0.77** | +0.03 | 0.98 | **0.94** | -0.01 |
| HUL **A** | 0.62 | **0.73** | +0.05 | 1.36 | **1.15** | -0.04 |
| COV **A** | 0.68 | **0.72** | -0.02 | 1.30 | **1.12** | -0.07 |


### Biggest rating changes vs GW5

| Club | Change | Driver |
|---|---|---|
| **MCI DEFW 0.78 → 0.88** (+0.10) | largest move in the file | City conceded **3.62 xG at home to Sunderland** — implied 1.80, ceiling-clipped. Their worst defensive round by far; they fall from 2nd to joint-3rd-best DEFW (behind ARS and NFO, level with LIV) and their ΣP(CS) falls to 1.77. One clipped match drives it; the other four rounds average implied 0.80. |
| **SUN ATT 0.94 → 1.01** (+0.07) | largest attacking rise | The other side of the same match: **3.62 xG at the Etihad**, implied 1.80 and clipped. Sunderland have now produced 1.71 xG or more in four straight rounds and sit 11th on attack, up from 14th at GW5 — rated 0.22 above their prior, second only to Brighton's +0.23. |
| **CHE ATT 1.25 → 1.18** (−0.07) | fourth straight fall | 0.85 xG at Brentford (implied 0.65). Chelsea's rating has gone 1.43 → 1.33 → 1.25 → 1.18 across four cycles; all three of their latest rounds sit at or below 0.65 implied. Their ticker still ranks 4th — the fixtures carry it, not form. |
| **COV DEFW 1.19 → 1.12** (−0.07) | largest defensive upgrade | 1.10 xG conceded at Forest, implied 0.78. Still inside the band. |
| **NEW DEFW 1.09 → 1.15** (+0.06) | | **1.59 xG conceded at home to Hull** — implied 1.80, clipped. Newcastle now have three ceiling-or-near readings in five rounds and rank 17th on the defensive ticker. |
| **BRE ATT 1.14 → 1.19** (+0.05), **DEFW 0.98 → 0.93** (−0.05) | best two-way move | **2.90 xG v Chelsea, 0.85 conceded** — both clipped at the guard. Brentford climb to 3rd on both tickers. |
| **HUL ATT 0.68 → 0.73** (+0.05) | | 1.59 xG at Newcastle, implied 1.18. Still 20th on the attacking ticker. |
| **IPS DEFW 1.02 → 1.07** (+0.05), **EVE DEFW 0.94 → 0.99** (+0.05) | | The same match at Goodison: Everton 2.24 xG, Ipswich 1.44. Both defences rated worse. |
| **LIV DEFW 0.93 → 0.88** (−0.05) | | 0.80 xG conceded at Bournemouth, floored at 0.55. Liverpool's third good defensive round in a row. |
| **BOU ATT 1.08 → 1.03** (−0.05), **NFO ATT 1.01 → 0.96** (−0.05) | | Bournemouth 0.80 xG v Liverpool; Forest 1.10 v Coventry (implied 0.55, floored). Forest's GW5 attacking rise reverses. |

## 6-GW ticker — best attacking (ranked by Σ λ_att, GW6–11)

`±` marks a fixture carrying the two-sided promoted-club band.

| # | Club | Σ | GW6 | GW7 | GW8 | GW9 | GW10 | GW11 |
|---:|---|---:|---|---|---|---|---|---|
| 1 | **MCI** | 11.79 | LIV(A) 1.59 | IPS(H) 2.24 ± | AVL(A) 1.92 | BHA(H) 2.26 | NFO(A) 1.52 | FUL(H) 2.26 |
| 2 | **ARS** | 10.26 | LEE(H) 1.72 | NFO(A) 1.34 | EVE(H) 1.83 | LIV(A) 1.40 | HUL(H) 2.13 ± | NEW(A) 1.84 |
| 3 | **BRE** | 10.17 | AVL(A) 1.68 | LIV(H) 1.61 | HUL(A) 1.82 ± | NFO(H) 1.54 | BHA(A) 1.71 | EVE(H) 1.81 |
| 4 | **CHE** | 10.07 | BOU(H) 1.69 | EVE(A) 1.55 | TOT(H) 1.71 | MUN(H) 1.78 | SUN(A) 1.65 | LEE(H) 1.69 |
| 5 | **BHA** | 9.48 | SUN(A) 1.58 | CRY(H) 1.91 | LIV(A) 1.32 | MCI(A) 1.32 | BRE(H) 1.62 | HUL(A) 1.73 ± |
| 6 | **LIV** | 9.38 | MCI(H) 1.52 | BRE(A) 1.39 | BHA(H) 1.86 | ARS(H) 1.28 | CRY(A) 1.64 | MUN(H) 1.69 |
| 7 | **MUN** | 9.16 | TOT(H) 1.58 | LEE(A) 1.35 | BOU(H) 1.56 | CHE(A) 1.61 | AVL(H) 1.78 | LIV(A) 1.28 |
| 8 | **SUN** | 9.03 | BHA(H) 1.68 | BOU(A) 1.25 | LEE(H) 1.45 | COV(A) 1.50 ± | CHE(H) 1.73 | AVL(A) 1.42 |
| 9 | **CRY** | 8.85 | NFO(H) 1.33 | BHA(A) 1.48 | NEW(H) 1.82 | TOT(A) 1.29 | LIV(H) 1.40 | COV(A) 1.53 ± |
| 10 | **BOU** | 8.81 | CHE(A) 1.52 | SUN(H) 1.67 | MUN(A) 1.34 | LEE(H) 1.48 | IPS(A) 1.47 ± | NFO(H) 1.33 |
| 11 | **LEE** | 8.45 | ARS(A) 1.03 | MUN(H) 1.58 | SUN(A) 1.47 | BOU(A) 1.30 | TOT(H) 1.52 | CHE(A) 1.55 |
| 12 | **EVE** | 8.20 | HUL(A) 1.44 ± | CHE(H) 1.61 | ARS(A) 0.93 | NEW(A) 1.44 | COV(H) 1.62 ± | BRE(A) 1.16 |
| 13 | **FUL** | 7.87 | IPS(A) 1.24 ± | HUL(H) 1.54 ± | COV(A) 1.30 ± | AVL(A) 1.23 | NEW(H) 1.54 | MCI(A) 1.02 |
| 14 | **IPS** | 7.85 | FUL(H) 1.56 ± | MCI(A) 1.10 ± | NFO(H) 1.22 ± | HUL(A) 1.44 ± | BOU(H) 1.35 ± | TOT(A) 1.18 ± |
| 15 | **NFO** | 7.54 | CRY(A) 1.40 | ARS(H) 1.09 | IPS(A) 1.37 ± | BRE(A) 1.19 | MCI(H) 1.30 | BOU(A) 1.19 |
| 16 | **AVL** | 7.47 | BRE(H) 1.20 | NEW(A) 1.28 | MCI(H) 1.14 | FUL(H) 1.40 | MUN(A) 1.09 | SUN(H) 1.36 |
| 17 | **NEW** | 7.30 | COV(A) 1.25 ± | AVL(H) 1.37 | CRY(A) 1.23 | EVE(H) 1.28 | FUL(A) 1.21 | ARS(H) 0.96 |
| 18 | **TOT** | 6.99 | MUN(A) 1.00 | COV(H) 1.33 ± | CHE(A) 1.14 | CRY(H) 1.30 | LEE(A) 0.95 | IPS(H) 1.27 ± |
| 19 | **COV** | 6.71 | NEW(H) 1.28 ± | TOT(A) 0.90 ± | FUL(H) 1.20 ± | SUN(H) 1.16 ± | EVE(A) 0.95 ± | CRY(H) 1.22 ± |
| 20 | **HUL** | 6.34 | EVE(H) 1.11 ± | FUL(A) 1.05 ± | BRE(H) 1.05 ± | IPS(H) 1.20 ± | ARS(A) 0.72 ± | BHA(H) 1.21 ± |


## 6-GW ticker — best defensive (ranked by Σ P(CS), GW6–11)

| # | Club | Σ | GW6 | GW7 | GW8 | GW9 | GW10 | GW11 |
|---:|---|---:|---|---|---|---|---|---|
| 1 | **ARS** | 2.24 | LEE(H) 0.36 | NFO(A) 0.34 | EVE(H) 0.39 | LIV(A) 0.28 | HUL(H) 0.49 ± | NEW(A) 0.38 |
| 2 | **MCI** | 1.77 | LIV(A) 0.22 | IPS(H) 0.33 ± | AVL(A) 0.32 | BHA(H) 0.27 | NFO(A) 0.27 | FUL(H) 0.36 |
| 3 | **BRE** | 1.71 | AVL(A) 0.30 | LIV(H) 0.25 | HUL(A) 0.35 ± | NFO(H) 0.30 | BHA(A) 0.20 | EVE(H) 0.31 |
| 4 | **TOT** | 1.61 | MUN(A) 0.21 | COV(H) 0.41 ± | CHE(A) 0.18 | CRY(H) 0.28 | LEE(A) 0.22 | IPS(H) 0.31 ± |
| 5 | **EVE** | 1.53 | HUL(A) 0.33 ± | CHE(H) 0.21 | ARS(A) 0.16 | NEW(A) 0.28 | COV(H) 0.39 ± | BRE(A) 0.16 |
| 6 | **MUN** | 1.53 | TOT(H) 0.37 | LEE(A) 0.21 | BOU(H) 0.26 | CHE(A) 0.17 | AVL(H) 0.34 | LIV(A) 0.18 |
| 7 | **BOU** | 1.51 | CHE(A) 0.18 | SUN(H) 0.29 | MUN(A) 0.21 | LEE(H) 0.27 | IPS(A) 0.26 ± | NFO(H) 0.30 |
| 8 | **FUL** | 1.51 | IPS(A) 0.21 ± | HUL(H) 0.35 ± | COV(A) 0.30 ± | AVL(A) 0.25 | NEW(H) 0.30 | MCI(A) 0.10 |
| 9 | **NFO** | 1.51 | CRY(A) 0.26 | ARS(H) 0.26 | IPS(A) 0.30 ± | BRE(A) 0.21 | MCI(H) 0.22 | BOU(A) 0.26 |
| 10 | **LEE** | 1.47 | ARS(A) 0.18 | MUN(H) 0.26 | SUN(A) 0.23 | BOU(A) 0.23 | TOT(H) 0.39 | CHE(A) 0.18 |
| 11 | **COV** | 1.46 | NEW(H) 0.29 ± | TOT(A) 0.26 ± | FUL(H) 0.27 ± | SUN(H) 0.22 ± | EVE(A) 0.20 ± | CRY(H) 0.22 ± |
| 12 | **IPS** | 1.46 | FUL(H) 0.29 ± | MCI(A) 0.11 ± | NFO(H) 0.25 ± | HUL(A) 0.30 ± | BOU(H) 0.23 ± | TOT(A) 0.28 ± |
| 13 | **LIV** | 1.45 | MCI(H) 0.20 | BRE(A) 0.20 | BHA(H) 0.27 | ARS(H) 0.25 | CRY(A) 0.25 | MUN(H) 0.28 |
| 14 | **CRY** | 1.45 | NFO(H) 0.25 | BHA(A) 0.15 | NEW(H) 0.29 | TOT(A) 0.27 | LIV(H) 0.19 | COV(A) 0.30 ± |
| 15 | **SUN** | 1.39 | BHA(H) 0.21 | BOU(A) 0.19 | LEE(H) 0.23 | COV(A) 0.31 ± | CHE(H) 0.19 | AVL(A) 0.26 |
| 16 | **CHE** | 1.33 | BOU(H) 0.22 | EVE(A) 0.20 | TOT(H) 0.32 | MUN(H) 0.20 | SUN(A) 0.18 | LEE(H) 0.21 |
| 17 | **NEW** | 1.33 | COV(A) 0.28 ± | AVL(H) 0.28 | CRY(A) 0.16 | EVE(H) 0.24 | FUL(A) 0.21 | ARS(H) 0.16 |
| 18 | **AVL** | 1.29 | BRE(H) 0.19 | NEW(A) 0.25 | MCI(H) 0.15 | FUL(H) 0.29 | MUN(A) 0.17 | SUN(H) 0.24 |
| 19 | **BHA** | 1.16 | SUN(A) 0.19 | CRY(H) 0.23 | LIV(A) 0.16 | MCI(A) 0.10 | BRE(H) 0.18 | HUL(A) 0.30 ± |
| 20 | **HUL** | 1.15 | EVE(H) 0.24 ± | FUL(A) 0.21 ± | BRE(H) 0.16 ± | IPS(H) 0.24 ± | ARS(A) 0.12 ± | BHA(H) 0.18 ± |


## Per club-fixture detail — GW6–GW11

`att` and `def` are presentation-only deciles of λ_att and P(CS) across all 120
rows in the window. Downstream agents read λ_att and P(CS), never the deciles.

#### GW6

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| ARS | LEE | H | 3 | 1.72 | 9 | 1.03 | 0.36 | 10 |  |
| CHE | BOU | H | 3 | 1.69 | 9 | 1.52 | 0.22 | 4 |  |
| BRE | AVL | A | 3 | 1.68 | 9 | 1.20 | 0.30 | 8 |  |
| SUN | BHA | H | 3 | 1.68 | 9 | 1.58 | 0.21 | 3 |  |
| MCI | LIV | A | 4 | 1.59 | 8 | 1.52 | 0.22 | 4 |  |
| MUN | TOT | H | 2 | 1.58 | 8 | 1.00 | 0.37 | 10 |  |
| BHA | SUN | A | 3 | 1.58 | 8 | 1.68 | 0.19 | 2 |  |
| IPS | FUL | H | 2 | 1.56 | 7 | 1.24 | 0.29 | 8 | ± |
| BOU | CHE | A | 4 | 1.52 | 7 | 1.69 | 0.18 | 2 |  |
| LIV | MCI | H | 4 | 1.52 | 7 | 1.59 | 0.20 | 3 |  |
| EVE | HUL | A | 2 | 1.44 | 6 | 1.11 | 0.33 | 9 | ± |
| NFO | CRY | A | 3 | 1.40 | 5 | 1.33 | 0.26 | 6 |  |
| CRY | NFO | H | 3 | 1.33 | 4 | 1.40 | 0.25 | 5 |  |
| COV | NEW | H | 3 | 1.28 | 3 | 1.25 | 0.29 | 8 | ± |
| NEW | COV | A | 2 | 1.25 | 3 | 1.28 | 0.28 | 7 | ± |
| FUL | IPS | A | 2 | 1.24 | 3 | 1.56 | 0.21 | 3 | ± |
| AVL | BRE | H | 3 | 1.20 | 2 | 1.68 | 0.19 | 2 |  |
| HUL | EVE | H | 3 | 1.11 | 2 | 1.44 | 0.24 | 5 | ± |
| LEE | ARS | A | 5 | 1.03 | 1 | 1.72 | 0.18 | 2 |  |
| TOT | MUN | A | 4 | 1.00 | 1 | 1.58 | 0.21 | 3 |  |

#### GW7

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| MCI | IPS | H | 2 | 2.24 | 10 | 1.10 | 0.33 | 9 | ± |
| BHA | CRY | H | 2 | 1.91 | 10 | 1.48 | 0.23 | 5 |  |
| BOU | SUN | H | 3 | 1.67 | 8 | 1.25 | 0.29 | 8 |  |
| BRE | LIV | H | 4 | 1.61 | 8 | 1.39 | 0.25 | 5 |  |
| EVE | CHE | H | 4 | 1.61 | 8 | 1.55 | 0.21 | 3 |  |
| LEE | MUN | H | 4 | 1.58 | 8 | 1.35 | 0.26 | 6 |  |
| CHE | EVE | A | 3 | 1.55 | 7 | 1.61 | 0.20 | 3 |  |
| FUL | HUL | H | 2 | 1.54 | 7 | 1.05 | 0.35 | 10 | ± |
| CRY | BHA | A | 4 | 1.48 | 6 | 1.91 | 0.15 | 1 |  |
| LIV | BRE | A | 3 | 1.39 | 5 | 1.61 | 0.20 | 3 |  |
| NEW | AVL | H | 3 | 1.37 | 5 | 1.28 | 0.28 | 7 |  |
| MUN | LEE | A | 3 | 1.35 | 5 | 1.58 | 0.21 | 3 |  |
| ARS | NFO | A | 3 | 1.34 | 5 | 1.09 | 0.34 | 9 |  |
| TOT | COV | H | 2 | 1.33 | 4 | 0.90 | 0.41 | 10 | ± |
| AVL | NEW | A | 3 | 1.28 | 3 | 1.37 | 0.25 | 5 |  |
| SUN | BOU | A | 3 | 1.25 | 3 | 1.67 | 0.19 | 2 |  |
| IPS | MCI | A | 5 | 1.10 | 2 | 2.24 | 0.11 | 1 | ± |
| NFO | ARS | H | 4 | 1.09 | 1 | 1.34 | 0.26 | 6 |  |
| HUL | FUL | A | 3 | 1.05 | 1 | 1.54 | 0.21 | 3 | ± |
| COV | TOT | A | 3 | 0.90 | 1 | 1.33 | 0.26 | 6 | ± |

#### GW8

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| MCI | AVL | A | 3 | 1.92 | 10 | 1.14 | 0.32 | 9 |  |
| LIV | BHA | H | 3 | 1.86 | 10 | 1.32 | 0.27 | 7 |  |
| ARS | EVE | H | 3 | 1.83 | 10 | 0.93 | 0.39 | 10 |  |
| CRY | NEW | H | 3 | 1.82 | 10 | 1.23 | 0.29 | 8 |  |
| BRE | HUL | A | 2 | 1.82 | 10 | 1.05 | 0.35 | 10 | ± |
| CHE | TOT | H | 2 | 1.71 | 9 | 1.14 | 0.32 | 9 |  |
| MUN | BOU | H | 3 | 1.56 | 7 | 1.34 | 0.26 | 6 |  |
| LEE | SUN | A | 3 | 1.47 | 6 | 1.45 | 0.23 | 5 |  |
| SUN | LEE | H | 3 | 1.45 | 6 | 1.47 | 0.23 | 5 |  |
| NFO | IPS | A | 2 | 1.37 | 5 | 1.22 | 0.30 | 8 | ± |
| BOU | MUN | A | 4 | 1.34 | 5 | 1.56 | 0.21 | 3 |  |
| BHA | LIV | A | 4 | 1.32 | 4 | 1.86 | 0.16 | 1 |  |
| FUL | COV | A | 2 | 1.30 | 4 | 1.20 | 0.30 | 8 | ± |
| NEW | CRY | A | 3 | 1.23 | 3 | 1.82 | 0.16 | 1 |  |
| IPS | NFO | H | 3 | 1.22 | 3 | 1.37 | 0.25 | 5 | ± |
| COV | FUL | H | 2 | 1.20 | 2 | 1.30 | 0.27 | 7 | ± |
| AVL | MCI | H | 4 | 1.14 | 2 | 1.92 | 0.15 | 1 |  |
| TOT | CHE | A | 4 | 1.14 | 2 | 1.71 | 0.18 | 2 |  |
| HUL | BRE | H | 3 | 1.05 | 1 | 1.82 | 0.16 | 1 | ± |
| EVE | ARS | A | 5 | 0.93 | 1 | 1.83 | 0.16 | 1 |  |

#### GW9

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| MCI | BHA | H | 3 | 2.26 | 10 | 1.32 | 0.27 | 7 |  |
| CHE | MUN | H | 4 | 1.78 | 9 | 1.61 | 0.20 | 3 |  |
| MUN | CHE | A | 4 | 1.61 | 8 | 1.78 | 0.17 | 2 |  |
| BRE | NFO | H | 3 | 1.54 | 7 | 1.19 | 0.30 | 8 |  |
| SUN | COV | A | 2 | 1.50 | 6 | 1.16 | 0.31 | 9 | ± |
| BOU | LEE | H | 3 | 1.48 | 6 | 1.30 | 0.27 | 7 |  |
| IPS | HUL | A | 2 | 1.44 | 6 | 1.20 | 0.30 | 8 | ± |
| EVE | NEW | A | 3 | 1.44 | 6 | 1.28 | 0.28 | 7 |  |
| AVL | FUL | H | 2 | 1.40 | 5 | 1.23 | 0.29 | 8 |  |
| ARS | LIV | A | 4 | 1.40 | 5 | 1.28 | 0.28 | 7 |  |
| BHA | MCI | A | 5 | 1.32 | 4 | 2.26 | 0.10 | 1 |  |
| LEE | BOU | A | 3 | 1.30 | 4 | 1.48 | 0.23 | 5 |  |
| TOT | CRY | H | 2 | 1.30 | 4 | 1.29 | 0.28 | 7 |  |
| CRY | TOT | A | 3 | 1.29 | 4 | 1.30 | 0.27 | 7 |  |
| LIV | ARS | H | 4 | 1.28 | 3 | 1.40 | 0.25 | 5 |  |
| NEW | EVE | H | 3 | 1.28 | 3 | 1.44 | 0.24 | 5 |  |
| FUL | AVL | A | 3 | 1.23 | 3 | 1.40 | 0.25 | 5 |  |
| HUL | IPS | H | 2 | 1.20 | 2 | 1.44 | 0.24 | 5 | ± |
| NFO | BRE | A | 3 | 1.19 | 2 | 1.54 | 0.21 | 3 |  |
| COV | SUN | H | 3 | 1.16 | 2 | 1.50 | 0.22 | 4 | ± |

#### GW10

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| ARS | HUL | H | 2 | 2.13 | 10 | 0.72 | 0.49 | 10 | ± |
| MUN | AVL | H | 3 | 1.78 | 9 | 1.09 | 0.34 | 9 |  |
| SUN | CHE | H | 4 | 1.73 | 9 | 1.65 | 0.19 | 2 |  |
| BRE | BHA | A | 4 | 1.71 | 9 | 1.62 | 0.20 | 3 |  |
| CHE | SUN | A | 3 | 1.65 | 8 | 1.73 | 0.18 | 2 |  |
| LIV | CRY | A | 3 | 1.64 | 8 | 1.40 | 0.25 | 5 |  |
| BHA | BRE | H | 3 | 1.62 | 8 | 1.71 | 0.18 | 2 |  |
| EVE | COV | H | 2 | 1.62 | 8 | 0.95 | 0.39 | 10 | ± |
| FUL | NEW | H | 3 | 1.54 | 7 | 1.21 | 0.30 | 8 |  |
| LEE | TOT | H | 2 | 1.52 | 7 | 0.95 | 0.39 | 10 |  |
| MCI | NFO | A | 3 | 1.52 | 7 | 1.30 | 0.27 | 7 |  |
| BOU | IPS | A | 2 | 1.47 | 6 | 1.35 | 0.26 | 6 | ± |
| CRY | LIV | H | 4 | 1.40 | 5 | 1.64 | 0.19 | 2 |  |
| IPS | BOU | H | 3 | 1.35 | 5 | 1.47 | 0.23 | 5 | ± |
| NFO | MCI | H | 4 | 1.30 | 4 | 1.52 | 0.22 | 4 |  |
| NEW | FUL | A | 3 | 1.21 | 3 | 1.54 | 0.21 | 3 |  |
| AVL | MUN | A | 4 | 1.09 | 1 | 1.78 | 0.17 | 2 |  |
| COV | EVE | A | 3 | 0.95 | 1 | 1.62 | 0.20 | 3 | ± |
| TOT | LEE | A | 3 | 0.95 | 1 | 1.52 | 0.22 | 4 |  |
| HUL | ARS | A | 5 | 0.72 | 1 | 2.13 | 0.12 | 1 | ± |

#### GW11

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| MCI | FUL | H | 2 | 2.26 | 10 | 1.02 | 0.36 | 10 |  |
| ARS | NEW | A | 3 | 1.84 | 10 | 0.96 | 0.38 | 10 |  |
| BRE | EVE | H | 3 | 1.81 | 10 | 1.16 | 0.31 | 9 |  |
| BHA | HUL | A | 2 | 1.73 | 9 | 1.21 | 0.30 | 8 | ± |
| CHE | LEE | H | 3 | 1.69 | 9 | 1.55 | 0.21 | 3 |  |
| LIV | MUN | H | 4 | 1.69 | 9 | 1.28 | 0.28 | 7 |  |
| LEE | CHE | A | 4 | 1.55 | 7 | 1.69 | 0.18 | 2 |  |
| CRY | COV | A | 2 | 1.53 | 7 | 1.22 | 0.30 | 8 | ± |
| SUN | AVL | A | 3 | 1.42 | 6 | 1.36 | 0.26 | 6 |  |
| AVL | SUN | H | 3 | 1.36 | 5 | 1.42 | 0.24 | 5 |  |
| BOU | NFO | H | 3 | 1.33 | 4 | 1.19 | 0.30 | 8 |  |
| MUN | LIV | A | 4 | 1.28 | 3 | 1.69 | 0.18 | 2 |  |
| TOT | IPS | H | 2 | 1.27 | 3 | 1.18 | 0.31 | 9 | ± |
| COV | CRY | H | 2 | 1.22 | 3 | 1.53 | 0.22 | 4 | ± |
| HUL | BHA | H | 3 | 1.21 | 3 | 1.73 | 0.18 | 2 | ± |
| NFO | BOU | A | 3 | 1.19 | 2 | 1.33 | 0.26 | 6 |  |
| IPS | TOT | A | 3 | 1.18 | 2 | 1.27 | 0.28 | 7 | ± |
| EVE | BRE | A | 3 | 1.16 | 2 | 1.81 | 0.16 | 1 |  |
| FUL | MCI | A | 5 | 1.02 | 1 | 2.26 | 0.10 | 1 |  |
| NEW | ARS | H | 4 | 0.96 | 1 | 1.84 | 0.16 | 1 |  |


## Top fixture swings

Halves of the window compared: GW6–8 against GW9–11.

| # | Club | Swing | Detail |
|---:|---|---|---|
| 1 | **ARS** | attack **+0.48** Σλ_att, defence +0.06 ΣP(CS) — largest improvement | LEE(H) NFO(A) EVE(H) → LIV(A) **HUL(H) NEW(A)**. The improvement rests on GW10 v Hull (2.13 λ_att, 0.49 P(CS), banded on both) and GW11 at Newcastle (1.84, 0.38, band-free). Arsenal's defence is top-third in all six rows regardless. |
| 2 | **FUL** | attack −0.29, defence **−0.21** — worst combined decline | IPS(A) HUL(H) COV(A) → AVL(A) NEW(H) MCI(A). Fulham's first half is three promoted opponents in a row, all banded; GW11 at City (λ_att 1.02, P(CS) 0.10) is the hardest row they face. Their 8th-place defensive ticker is band-dependent. |
| 3 | **CRY** | attack **−0.41** | NFO(H) BHA(A) **NEW(H)** → TOT(A) LIV(H) COV(A). Palace's best row is GW8 v Newcastle (1.82); the second half averages 1.41. |
| 4 | **NEW** | attack **−0.40**, defence −0.11 | COV(A) AVL(H) CRY(A) → EVE(H) FUL(A) **ARS(H)**. Newcastle sit 17th on both tickers already; the run ends with Arsenal (λ_att 0.96, P(CS) 0.16). Five of their six attacking rows are bottom-third. |
| 5 | **LEE** and **SUN** | attack +0.29 / +0.27, defence +0.13 each | LEE: ARS(A) MUN(H) SUN(A) → BOU(A) TOT(H) CHE(A) — Leeds start with a bottom-decile attacking row (1.03 at Arsenal), then turn ordinary-to-good; TOT(H) GW10 is their best defensive row (0.39). SUN: BHA(H) BOU(A) LEE(H) → COV(A) ± CHE(H) AVL(A) — on a rising attack rating, CHE(H) 1.73 in GW10 is their best row. |

Also worth naming: **MCI +0.29 attack** — the best ticker gets better, with
FUL(H) 2.26 in GW11; **BOU −0.25 attack / +0.15 defence**, the clearest
attack-to-defence trade in the file; **COV −0.18 defence**.

### Multi-GW runs

Top third = λ_att ≥ 1.55 / P(CS) ≥ 0.28 across the window's 120 rows.
Bottom third = λ_att ≤ 1.29 / P(CS) ≤ 0.21. Consecutive runs unless stated.

| Run | Club | Fixtures |
|---|---|---|
| Attack, top third, **all six** | **CHE** | BOU(H) 1.69, EVE(A) 1.55, TOT(H) 1.71, MUN(H) 1.78, SUN(A) 1.65, LEE(H) 1.69 — again the only six-row attacking run, and band-free |
| Attack, top third, GW6–9 | **MCI** | LIV(A) 1.59, IPS(H) 2.24 ±, AVL(A) 1.92, BHA(H) 2.26 — breaks at GW10 (NFO away, 1.52), resumes GW11 FUL(H) 2.26 |
| Attack, top third, GW6–8 and GW10–11 | **BRE** | AVL(A) 1.68, LIV(H) 1.61, HUL(A) 1.82 ±; then BHA(A) 1.71, EVE(H) 1.81 |
| Attack, top third, GW8–10 | **MUN** | BOU(H) 1.56, CHE(A) 1.61, AVL(H) 1.78 |
| Defence, top third, **all six** | **ARS** | every row P(CS) ≥ 0.28; the highest (HUL(H) 0.49) is banded |
| Defence, top third, GW8–9 and GW11 | **BRE** | HUL(A) 0.35 ±, NFO(H) 0.30; EVE(H) 0.31 |
| Attack, bottom third, all six | **HUL**, **COV** | no Hull row above 1.21; no Coventry row above 1.28 |
| Attack, bottom third, 5 of 6 | **NEW** | only AVL(H) 1.37 escapes |

Arsenal own the only six-row defensive run and Chelsea the only six-row
attacking one. City's defensive run shrinks to GW7–8, and GW7 is banded: the 3.62 xG
concession removed the rest.

## FPL FDR vs this model

FDR is the mean of `team_h_difficulty` / `team_a_difficulty` over the six rows.
Rank 1 = easiest ticker (ties broken by model attack). Disagreements of ≥ 8
places are bolded.

| Club | mean FDR | FDR rank | model ATT rank | model CS rank | FDR−ATT | FDR−CS |
|---|---:|---:|---:|---:|---:|---:|
| COV | 2.67 | 1 | 19 | 11 | **-18** | **-10** |
| MCI | 2.83 | 2 | 1 | 2 | +1 | +0 |
| FUL | 2.83 | 3 | 13 | 8 | **-10** | -5 |
| TOT | 2.83 | 4 | 18 | 4 | **-14** | +0 |
| ARS | 3.00 | 5 | 2 | 1 | +3 | +4 |
| CHE | 3.00 | 6 | 4 | 16 | +2 | **-10** |
| SUN | 3.00 | 7 | 8 | 15 | -1 | **-8** |
| IPS | 3.00 | 8 | 14 | 12 | -6 | -4 |
| NEW | 3.00 | 9 | 17 | 17 | **-8** | **-8** |
| BRE | 3.17 | 10 | 3 | 3 | +7 | +7 |
| BHA | 3.17 | 11 | 5 | 19 | +6 | **-8** |
| MUN | 3.17 | 12 | 7 | 6 | +5 | +6 |
| CRY | 3.17 | 13 | 9 | 14 | +4 | -1 |
| BOU | 3.17 | 14 | 10 | 7 | +4 | +7 |
| EVE | 3.17 | 15 | 12 | 5 | +3 | **+10** |
| NFO | 3.17 | 16 | 15 | 9 | +1 | +7 |
| AVL | 3.17 | 17 | 16 | 18 | +1 | -1 |
| HUL | 3.17 | 18 | 20 | 20 | -2 | -2 |
| LIV | 3.50 | 19 | 6 | 13 | **+13** | +6 |
| LEE | 3.50 | 20 | 11 | 10 | **+9** | **+10** |


**Where FDR is most wrong this window:**

- **COV (FDR 1st, model 19th attack, 11th defence)** — the largest disagreement
  for the third cycle running. FDR reads Coventry's opponents as soft; the
  model reads Coventry's own attack as second-worst. Do not buy Coventry
  attackers off the FDR ticker.
- **LIV (FDR 19th, model 6th attack)** — FDR's largest miss in the other
  direction. Liverpool's run *looks* hard (MCI, BRE, ARS, MUN) but BHA(H) 1.86
  and the attacking rating carry it.
- **TOT (FDR 4th, model 18th attack, 4th defence)** — FDR is right about
  Spurs' defence and wrong about their attack. The defensive ticker leans on
  two banded rows (COV(H) 0.41, IPS(H) 0.31).
- **CHE (FDR 6th, model 16th defence)** — FDR still treats Chelsea's defence
  as solid; the model rates it the 4th-worst DEFW (1.11), and it has risen two cycles running.
- **LEE (FDR 20th, model 11th / 10th)** and **EVE (FDR 15th, model 5th
  defence)** — both better than FDR thinks; Everton's defensive rank leans on
  two banded rows.
- **BHA (FDR 11th, model 5th attack, 19th defence)** — still the widest split:
  buy Brighton's attack, never their defence.

The model and FDR agree closely on **MCI** and **ARS** (top-5 on all three
rankings), and on **HUL** at the bottom.

## Blank and double gameweeks

**None in GW6–GW11.** All 20 clubs play exactly once in each of the six
gameweeks; the window holds 60 fixtures and 120 club-rows, and no fixture in
the snapshot carries a null `event`. Nothing here feeds a Bench Boost or Free
Hit case on fixture count.

## C5 — the Triple Captain gate

C5 binds A2 and A4: a Triple Captain must be justified on the captain's own
**fixture-independent** EP, and must not need a promoted club's defensive
rating to clear. The earmark has stood at GW9 since GW4. City's window:

| GW | Fixture | λ_att | P(CS) | Banded? | Δ vs GW5's read |
|---:|---|---:|---:|:-:|---|
| 6 | LIV (A) | 1.59 | 0.22 | no | 1.64 → 1.59 |
| 7 | IPS (H) | **2.24** | 0.33 | **yes** | 2.08 → 2.24 |
| 8 | AVL (A) | 1.92 | 0.32 | no | 1.85 → 1.92 |
| 9 | BHA (H) | **2.26** | 0.27 | no | 2.27 → 2.26 |
| 10 | NFO (A) | 1.52 | 0.27 | no | 1.51 → 1.52 |
| 11 | FUL (H) | **2.26** | 0.36 | no | new to the window |

Findings:

1. **GW9 holds.** BHA(H) 2.26 is unchanged in practice and remains the joint
   best band-free row. Its edge over this week's GW6 LIV(A) 1.59 is +0.67 — no
   case for a GW6 Triple Captain on fixture grounds.
2. **GW11 FUL(H) now ties GW9 at 2.26** and carries the higher P(CS) (0.36 v
   0.27). On λ_att alone the two are indistinguishable; GW9's Brighton reading
   rests on a DEFW (1.08) that eased 0.03 this cycle, Fulham's (1.08) eased
   0.02. Nothing here moves the earmark, but GW11 is a valid fallback if GW9
   is lost to an injury or a fixture move. Set-1 chips run to GW19.
3. **GW7 stays ineligible.** IPS(H) rose to 2.24 and is still banded — C5
   forbids it regardless of the arithmetic.

**A2 recommends A4 hold the Triple Captain earmark at GW9, with GW11 as the
named fallback.** This is a *forecast* for `chip_plan`, not a commitment;
re-test every cycle. The fixture-independent half of the test belongs to A3
and A4 — nothing in this file clears C5.

## Uncertainty flags

| Flag | Detail |
|---|---|
| **Split-strength fields still zero** | Sixth GW running. All 20 defence priors are ASSUMPTION-grade, from 5-tier `strength_overall`. Current-season data is now 56–62% of each DEFW. Re-derive the ticker the moment FPL populates the split fields. |
| **MCI defence — one clipped match** | The +0.10 DEFW move comes from a single 3.62 xG concession, clipped at 1.80. If it is an outlier, City's defensive rows are understated by roughly 0.03–0.05 P(CS) each; the clip already limits how much one match can do. |
| **Promoted clubs — band unrelaxed at n=5** | 34 of 120 rows banded at ±15% λ_att / ±15pp P(CS); uncertainty stays **HIGH**; C4's defensive prohibition stands. IPS's five defensive readings span floor to ceiling. Revisit at GW8 (n=7). |
| **`base_lambda` held at +6.7%** | Observed 3.06 xG per match over 50 matches against the 2.87 base. Not significant at n=50 (≈1.4 SE). If raised, every λ_att rises ~7% and every P(CS) falls ~0.02–0.03. Re-test at GW10. |
| **Clipping eased** | 64 of 200 implied ratings at the guard, but round 5's rate (20%) is the lowest so far. NFO carries six clipped values, BRE and AVL five; their ratings are pulled toward the prior more than the raw xG warrants. |
| **CHE attack trend** | Fourth straight downgrade (1.43 → 1.18). Chelsea keep 4th on the attacking ticker on fixtures alone; the rating trend is the risk. |
| **SUN attack rising fast** | 11th and climbing on four straight 1.7+ xG rounds, the latest clipped. The rating may still lag Sunderland's real level. |
| **No cup/congestion adjustment** | European and domestic-cup fixtures are not in any artifact; which clubs are in Europe is an **ASSUMPTION** and deliberately not enumerated. The player-analyst applies rotation; the ticker does not. |
| **`played` and `points` are zero in bootstrap** | All 20 clubs still report `played: 0`, `points: 0`. Already in the backlog (GW4 A2 DATA). No rating reads these fields. |

## Handoff to downstream agents

- **A3 (player-analyst)**: consume `lambda_att` and `p_cs` from
  `data/analysis/gw6/fixtures.json`. The 1–10 deciles are presentation only.
  Rotation and the 60-minute requirement are yours — P(CS) excludes both.
- **A4 (squad-optimizer)**: MCI top the attacking ticker and ARS the defensive
  one. City's defensive rows weakened this cycle on one clipped match. Brentford
  climb to 3rd on both tickers. Liverpool are the largest FDR under-rating;
  Coventry the largest over-rating. C5: **hold the Triple Captain earmark at
  GW9**, GW11 FUL(H) a tied fallback; GW7 remains ineligible.
- **C4 residual, binding**: no selected player may take his single largest
  **defensive** EP term from a fixture against COV, HUL or IPS. The fourteen rows
  that trip it are tabulated under C12 above; for GW6 only EVE at HUL (0.33).
