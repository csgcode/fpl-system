# GW4 — 6-Gameweek Fixture Ticker (GW4–GW9)

Window **GW4–GW9**, all 20 clubs, no blanks, no doubles. Ratings rest on
**three** played rounds; the blend has advanced from GW3's 74/26 to roughly
**66/34** on established-club attack.

Downstream agents consume `lambda_att` and `p_cs` from
`data/analysis/gw4/fixtures.json`. The 1–10 attack/defence scores in this file
are presentation-only deciles and must not be read as inputs.

| Headline | Read |
|---|---|
| Best attacking ticker | **CHE** Σλ_att 12.13, then MCI 12.05, BRE 10.40 |
| Best defensive ticker | **ARS** ΣP(CS) 2.43, then MCI 1.94, CHE 1.71 |
| Worst combined | **HUL** (20th attack, 20th defence), then **SUN** (17th/18th); **COV** and **BHA** level behind |
| Largest swing | **EVE** collapses after GW6 (−0.89 Σλ_att, −0.42 ΣP(CS)) |
| Blanks / doubles | none in GW4–GW9 |

## What changed since GW3

### 1. Round 3 reproduces the GW3 pipeline exactly — no method change

The club-attribution fix GW3 introduced (attribute an `element-summary` history
row by the row's own fixture, never by the player's *current* bootstrap `team`)
is carried forward unchanged. Re-running it over rounds 1–2 reproduces GW3's
published xG/xGA column on all 20 clubs to the last decimal (ARS 1.88/0.21,
MCI 2.24/0.65, IPS 2.06 r2, CHE 3.04 r2), so the only new information this
cycle is round 3 itself.

Coverage: 426 element summaries read; 97 player-rounds missing from the
snapshot recovered from the `event-live` files (rounds 1–3), worth **3.51 xG**
league-wide. The recovery rate is unchanged in character from GW3's 1.89 xG
over two rounds.

### 2. FPL has still not populated the split-strength fields

Fourth gameweek running: `strength_attack_home/away` and
`strength_defence_home/away` are **0** for all 20 clubs, and `strength` is
`null`. Defence priors still come from `strength_overall_home/away` — five
tiers across twenty clubs — and remain **ASSUMPTION**-grade. The mitigating
trend continues: the current-season component is now 43–50% of DEFW, against
33–40% at GW3, so the weak prior's share keeps falling on its own.

### 3. The blend advanced, on the schedule GW2 set

No parameter was retuned. Each prior's worth stays fixed at `k`
match-equivalents; the match count `n` grew from 2 to 3.

### 4. Clipping is starting to bite less, as predicted

**42 of 120** implied ratings hit the [0.55, 1.80] guard. Round 3 alone
contributed **13 of 40** (32.5%) against rounds 1–2's 29 of 80 (36.3%) — the
decline GW3 forecast, though shallower than hoped. Three rounds is still not
enough for a single match's xG to stop dominating.

## Corrections applied

`data/retro/gw3.md` did not exist when this file was written, so the binding
set is GW1's and GW2's corrections addressed to A2.

### C12 (A2) — the promoted-club band, two-sided

Carried forward unchanged from GW3. COV, HUL and IPS on *either* side of a
fixture set `band: true` on *both* club-rows — **34 of 120 rows** this window
(GW3: 36 of 120).

1. **The band covers `lambda_att` as well as `p_cs`.** Read λ_att ±15% and
   P(CS) ±15pp on any `±` row.
2. **No haircut to the central attacking estimate.** C12's second clause is
   explicit. Every club facing promoted opposition carries its full modelled
   λ_att: **CHE 2.64 v HUL(H)** — the highest single λ_att in the window —
   MCI 2.32 v IPS(H), CRY 1.90 v IPS(H), BRE 2.06 at HUL. The uncertainty is
   published as a band, never as a discount.
3. C4's residual prohibition — *never let a promoted-club fixture be the single
   largest defensive EP term for a selected player* — **stands for defensive
   terms only**. It bites hardest on **CHE v HUL(H) P(CS) 0.45**, the
   second-best defensive row in the window, and on FUL v HUL(H) 0.39, NEW v
   HUL(H) 0.42, NFO v COV(H) 0.42, TOT v COV(H) 0.40, BRE at HUL 0.40 and
   EVE at HUL(A) 0.39.

**Promoted-club convergence.** All three now have 3 played fixtures, the
threshold C4 named for relaxing the band. **The band is kept regardless.** C4's
instruction is to downgrade confidence and never upgrade it, and three rounds
of promoted-club xG is still a sample in which one match moves a rating by more
than the band's width. Revisit at GW6 (n=5), not before.

### C5 (A2, A4) — the Triple Captain gate

Active, and binding again this cycle. Examined under its own heading below.
Short version: **GW4 does not clear it, and the GW5 earmark is no longer the
best band-free option — GW9 is.**

### C4 (A2) — superseded

Revised by C12. Its confidence-downgrade instruction is discharged by keeping
promoted-club uncertainty at HIGH (see above) with the band unrelaxed at n=3.

## Model

```
lambda_att(i vs j, home) = 1.54 * ATT_i * DEFW_j
lambda_att(i vs j, away) = 1.33 * ATT_i * DEFW_j
lambda_def(i)            = lambda_att(j)        # opponent-symmetric
P(CS)_i                  = exp(-lambda_def_i)   # Poisson P(0 conceded)
```

Unchanged since GW1. `ATT` and `DEFW` are multiplicative indices renormalised
to a 20-club mean of exactly 1.00 after blending, so the 1.54 / 1.33 base rates
stay calibrated.

**P(CS) excludes the FPL 60-minute requirement and rotation risk** — the
player-analyst applies those.

### Blend

Each played match yields an opponent- and venue-adjusted implied rating:

```
impATT_i  = xG_i  / (base_venue_i  * DEFW_opponent)
impDEFW_i = xGA_i / (base_venue_j  * ATT_opponent)
```

Both adjustments use the **GW1 pure-prior** ratings as a fixed reference frame,
for the whole three-round history — so a round's implied value never depends on
the order rounds were processed. Implied values are clipped to **[0.55, 1.80]**
before blending.

Rating = `(k * prior + Σ implied) / (k + n)`, with `n = 3`:

| Rating | Prior source | k | w_prior / w_current (n=3) | was at GW3 |
|---|---|---:|---|---|
| Attack, established | real prior-season squad xG | 5.7 | **66 / 34** | 74 / 26 |
| Defence, established | 5-tier `strength_overall` only | 4.0 | **57 / 43** | 67 / 33 |
| Attack, promoted | ASSUMPTION | 4.0 | **57 / 43** | 67 / 33 |
| Defence, promoted | ASSUMPTION | 3.0 | **50 / 50** | 60 / 40 |

Defence takes more current weight than attack because its **prior is weaker**,
not because its data is better. Prior weight stays ≥20% through GW10 on every
line (at GW10, n=9: established attack 39%, promoted defence 25%).

## Team ratings — GW4 (three rounds blended)

`Δ GW3` compares `data/analysis/gw3/fixtures.json`. `*` marks an implied value
clipped to [0.55, 1.80] before blending. **A** marks a promoted club.

| Club | xG 1/2/3 | xGA 1/2/3 | impATT 1/2/3 | impDEFW 1/2/3 | ATT prior | **ATT** | Δ GW3 | DEFW prior | **DEFW** | Δ GW3 |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| MCI | 2.24 / 2.22 / 2.12 | 0.65 / 0.68 / 1.37 | 1.47 / 1.72 / 1.06 | 0.55* / 0.55* / 1.51 | 1.39 | **1.37** | -0.04 | 0.80 | **0.81** | +0.11 |
| CHE | 2.23 / 3.04 / 0.39 | 1.38 / 1.46 / 2.06 | 1.64 / 1.80* / 0.55* | 1.19 / 1.22 / 1.05 | 1.37 | **1.33** | -0.09 | 0.90 | **0.98** | +0.01 |
| BRE | 3.91 / 1.67 / 1.21 | 0.57 / 1.46 / 1.71 | 1.80* / 1.22 / 0.77 | 0.55* / 0.89 / 1.63 | 1.21 | **1.20** | -0.06 | 0.99 | **0.98** | +0.10 |
| ARS | 1.88 / 1.04 / 2.06 | 0.21 / 0.34 / 0.39 | 0.94 / 0.82 / 1.49 | 0.55* / 0.55* / 0.55* | 1.28 | **1.19** | +0.04 | 0.70 | **0.62** | -0.01 |
| LIV | 3.01 / 1.74 / 0.69 | 1.58 / 2.30 / 0.76 | 1.80* / 1.13 / 0.55* | 1.04 / 1.80* / 0.71 | 1.18 | **1.15** | -0.07 | 0.85 | **0.97** | -0.04 |
| CRY | 1.97 / 0.68 / 1.98 | 1.12 / 2.22 / 3.16 | 1.48 / 0.55 / 1.46 | 0.77 / 1.20 / 1.80* | 1.14 | **1.12** | +0.04 | 0.97 | **1.06** | +0.11 |
| MUN | 1.82 / 5.15 / 0.69 | 1.08 / 2.06 / 1.02 | 1.01 / 1.80* / 0.55* | 1.13 / 1.80* / 0.70 | 1.16 | **1.12** | -0.07 | 0.87 | **0.99** | -0.05 |
| BHA | 3.77 / 1.46 / 2.20 | 0.30 / 3.04 / 2.62 | 1.80* / 1.22 / 1.39 | 0.55* / 1.44 / 1.80* | 0.90 | **1.07** | +0.04 | 1.00 | **1.08** | +0.11 |
| BOU | 0.65 / 2.19 / 1.37 | 2.24 / 1.87 / 0.70 | 0.61 / 1.42 / 1.02 | 1.05 / 1.50 / 0.55* | 1.13 | **1.07** | -0.00 | 0.99 | **0.98** | -0.07 |
| LEE | 0.47 / 1.46 / 2.62 | 0.65 / 1.67 / 2.20 | 0.55* / 0.96 / 1.80* | 0.55* / 1.04 / 1.59 | 1.06 | **1.05** | +0.09 | 1.03 | **1.02** | +0.09 |
| EVE | 1.12 / 1.87 / 1.02 | 1.97 / 2.19 / 0.69 | 0.75 / 1.42 / 0.76 | 1.30 / 1.26 / 0.55* | 0.94 | **0.93** | -0.02 | 1.00 | **0.99** | -0.07 |
| NFO | 0.65 / 2.30 / 0.93 | 0.47 / 1.74 / 1.07 | 0.55* / 1.80* / 0.62 | 0.55* / 0.96 / 0.97 | 0.92 | **0.92** | -0.04 | 1.00 | **0.90** | +0.01 |
| NEW | 1.58 / 0.72 / 0.70 | 3.01 / 1.13 / 1.37 | 1.21 / 0.55 / 0.55* | 1.80* / 0.88 / 0.91 | 0.99 | **0.89** | -0.05 | 1.01 | **1.06** | -0.03 |
| IPS **A** | 1.79 / 2.06 / 0.76 | 0.67 / 5.15 / 0.69 | 1.14 / 1.78 / 0.58 | 0.64 / 1.80* / 0.55* | 0.70 | **0.88** | -0.05 | 1.26 | **1.10** | -0.11 |
| AVL | 0.30 / 0.34 / 1.93 | 3.77 / 1.04 / 0.57 | 0.55* / 0.55* / 1.07 | 1.80* / 0.61 / 0.60 | 0.98 | **0.87** | +0.02 | 0.95 | **0.95** | -0.06 |
| FUL | 1.38 / 0.94 / 3.16 | 2.23 / 2.03 / 1.98 | 1.00 / 0.69 / 1.80* | 1.22 / 1.67 / 1.31 | 0.75 | **0.87** | +0.11 | 1.02 | **1.15** | +0.02 |
| SUN | 0.67 / 2.03 / 1.71 | 1.79 / 0.94 / 1.21 | 0.55* / 1.29 / 1.30 | 1.66 / 0.94 / 0.65 | 0.79 | **0.86** | +0.06 | 1.02 | **1.02** | -0.06 |
| TOT | 0.57 / 1.13 / 1.07 | 3.91 / 0.72 / 0.93 | 0.55* / 0.73 / 0.80 | 1.80* / 0.55* / 0.66 | 0.83 | **0.77** | +0.01 | 0.98 | **0.96** | -0.06 |
| COV **A** | 0.21 / 1.30 / 1.37 | 1.88 / 0.72 / 2.12 | 0.55* / 0.62 / 1.29 | 0.95 / 0.87 / 0.99 | 0.68 | **0.72** | +0.09 | 1.30 | **1.09** | -0.02 |
| HUL **A** | 1.08 / 0.72 / 0.57 | 1.82 / 1.30 / 1.93 | 0.81 / 0.55* / 0.55* | 1.18 / 1.24 / 1.48 | 0.62 | **0.61** | -0.01 | 1.36 | **1.29** | +0.03 |

### Biggest rating changes vs GW3

| Club | Change | Driver |
|---|---|---|
| **MCI DEFW 0.70 → 0.81** (+0.11) | largest defensive downgrade | Conceded **1.37** xG to Coventry — a promoted side — after 0.65 and 0.68. City won 1-0; the xG says the defensive record was flattered. This is the single most consequential move in the file: City are still 2nd on the defensive ticker, but no longer in Arsenal's class. |
| **CRY DEFW 0.95 → 1.06** (+0.11) | | Conceded **3.16** xG at Fulham, the worst single figure of round 3 — implied 1.80, clipped. Palace won 3-2; the result hides a defence that has now conceded 2.22 and 3.16 in consecutive rounds. |
| **BHA DEFW 0.97 → 1.08** (+0.11) | | Conceded 2.62 xG at Leeds, implied clipped at 1.80. Three rounds: 0.30, 3.04, 2.62 — the opening clean sheet looks like the outlier. |
| **FUL ATT 0.76 → 0.87** (+0.11) | largest attacking rise | **3.16 xG** at home to Palace, implied 1.80 and clipped, and they still lost. Fulham's attack has moved from 18th to 13th in two cycles and the clip means the rating may still lag. |
| **BRE DEFW 0.88 → 0.98** (+0.10) | | 1.71 xG conceded to Sunderland. Brentford's defensive rating has given back GW3's entire gain. |
| **LEE ATT 0.96 → 1.05** (+0.09) | | 2.62 xG against Brighton, implied 1.80 and clipped. Leeds are 9th on attack. |
| **COV ATT 0.63 → 0.72** (+0.09) | | 1.37 xG at the Etihad, implied 1.29 — their best attacking round, against the best defence. Still 19th. |
| **CHE ATT 1.43 → 1.33** (−0.09) | | **0.39 xG** at Arsenal, implied 0.55 and floored. Chelsea scored once from it. They keep top spot on the attacking ticker on fixtures, not on a rising rating. |
| **LIV ATT 1.22 → 1.15** (−0.07) | | 0.69 xG at home to nobody's idea of a defence — third straight round below rating (3.01 → 1.74 → 0.69). The trend is real and the model is still 66% prior. |
| **MUN ATT 1.19 → 1.12** (−0.07) | | 0.69 xG at Everton. GW3's rating was built on a clipped 5.15-xG outlier against Ipswich; two rounds either side of it are 1.82 and 0.69. |
| **ARS DEFW 0.63 → 0.62** (−0.01) | notable non-move | **All three** impDEFW values are clipped at the 0.55 floor (0.21, 0.34, 0.39 xG conceded). The guard is now the binding constraint on Arsenal's defensive rating — see the uncertainty flags. |

## 6-GW ticker — best attacking (ranked by Σ λ_att, GW4–9)

`±` marks a fixture carrying the two-sided promoted-club band.

| # | Club | Σλ_att | GW4 | GW5 | GW6 | GW7 | GW8 | GW9 |
|---:|---|---:|---|---|---|---|---|---|
| 1 | **CHE** | 12.13 | HUL(H) 2.64 ± | BRE(A) 1.73 | BOU(H) 2.01 | EVE(A) 1.75 | TOT(H) 1.97 | MUN(H) 2.03 |
| 2 | **MCI** | 12.05 | MUN(A) 1.80 | SUN(H) 2.15 | LIV(A) 1.77 | IPS(H) 2.32 ± | AVL(A) 1.73 | BHA(H) 2.28 |
| 3 | **BRE** | 10.40 | BOU(A) 1.56 | CHE(H) 1.81 | AVL(A) 1.52 | LIV(H) 1.79 | HUL(A) 2.06 ± | NFO(H) 1.66 |
| 4 | **ARS** | 9.96 | SUN(A) 1.61 | BHA(A) 1.71 | LEE(H) 1.87 | NFO(A) 1.42 | EVE(H) 1.81 | LIV(A) 1.54 |
| 5 | **CRY** | 9.84 | IPS(H) 1.90 ± | LEE(A) 1.52 | NFO(H) 1.55 | BHA(A) 1.61 | NEW(H) 1.83 | TOT(A) 1.43 |
| 6 | **LIV** | 9.48 | FUL(H) 2.04 | BOU(A) 1.50 | MCI(H) 1.43 | BRE(A) 1.50 | BHA(H) 1.91 | ARS(H) 1.10 |
| 7 | **MUN** | 9.44 | MCI(H) 1.40 | FUL(A) 1.71 | TOT(H) 1.66 | LEE(A) 1.52 | BOU(H) 1.69 | CHE(A) 1.46 |
| 8 | **BOU** | 9.37 | BRE(H) 1.61 | LIV(H) 1.60 | CHE(A) 1.39 | SUN(H) 1.68 | MUN(A) 1.41 | LEE(H) 1.68 |
| 9 | **LEE** | 8.68 | NEW(H) 1.71 | CRY(H) 1.71 | ARS(A) 0.87 | MUN(H) 1.60 | SUN(A) 1.42 | BOU(A) 1.37 |
| 10 | **BHA** | 8.30 | COV(A) 1.55 ± | ARS(H) 1.02 | SUN(A) 1.45 | CRY(H) 1.75 | LIV(A) 1.38 | MCI(A) 1.15 |
| 11 | **NEW** | 8.18 | LEE(A) 1.21 | HUL(H) 1.77 ± | COV(A) 1.29 ± | AVL(H) 1.30 | CRY(A) 1.25 | EVE(H) 1.36 |
| 12 | **EVE** | 7.85 | TOT(A) 1.19 | IPS(H) 1.58 ± | HUL(A) 1.60 ± | CHE(H) 1.40 | ARS(A) 0.77 | NEW(A) 1.31 |
| 13 | **FUL** | 7.81 | LIV(A) 1.12 | MUN(H) 1.33 | IPS(A) 1.27 ± | HUL(H) 1.73 ± | COV(A) 1.26 ± | AVL(A) 1.10 |
| 14 | **IPS** | 7.64 | CRY(A) 1.24 ± | EVE(A) 1.16 ± | FUL(H) 1.56 ± | MCI(A) 0.95 ± | NFO(H) 1.22 ± | HUL(A) 1.51 ± |
| 15 | **AVL** | 7.49 | NFO(H) 1.21 | TOT(A) 1.11 | BRE(H) 1.31 | NEW(A) 1.23 | MCI(H) 1.09 | FUL(H) 1.54 |
| 16 | **NFO** | 7.43 | AVL(A) 1.16 | COV(H) 1.54 ± | CRY(A) 1.30 | ARS(H) 0.88 | IPS(A) 1.35 ± | BRE(A) 1.20 |
| 17 | **SUN** | 6.90 | ARS(H) 0.82 | MCI(A) 0.93 | BHA(H) 1.43 | BOU(A) 1.12 | LEE(H) 1.35 | COV(A) 1.25 ± |
| 18 | **TOT** | 6.86 | EVE(H) 1.17 | AVL(H) 1.13 | MUN(A) 1.01 | COV(H) 1.29 ± | CHE(A) 1.00 | CRY(H) 1.26 |
| 19 | **COV** | 6.57 | BHA(H) 1.20 ± | NFO(A) 0.86 ± | NEW(H) 1.18 ± | TOT(A) 0.92 ± | FUL(H) 1.28 ± | SUN(H) 1.13 ± |
| 20 | **HUL** | 5.47 | CHE(A) 0.80 ± | NEW(A) 0.86 ± | EVE(H) 0.93 ± | FUL(A) 0.93 ± | BRE(H) 0.92 ± | IPS(H) 1.03 ± |

## 6-GW ticker — best defensive (ranked by Σ P(CS), GW4–9)

| # | Club | ΣP(CS) | GW4 | GW5 | GW6 | GW7 | GW8 | GW9 |
|---:|---|---:|---|---|---|---|---|---|
| 1 | **ARS** | 2.43 | SUN(A) 0.44 | BHA(A) 0.36 | LEE(H) 0.42 | NFO(A) 0.42 | EVE(H) 0.46 | LIV(A) 0.33 |
| 2 | **MCI** | 1.94 | MUN(A) 0.25 | SUN(H) 0.40 | LIV(A) 0.24 | IPS(H) 0.39 ± | AVL(A) 0.34 | BHA(H) 0.32 |
| 3 | **CHE** | 1.71 | HUL(H) 0.45 ± | BRE(A) 0.16 | BOU(H) 0.25 | EVE(A) 0.25 | TOT(H) 0.37 | MUN(H) 0.23 |
| 4 | **NFO** | 1.66 | AVL(A) 0.30 | COV(H) 0.42 ± | CRY(A) 0.21 | ARS(H) 0.24 | IPS(A) 0.30 ± | BRE(A) 0.19 |
| 5 | **AVL** | 1.63 | NFO(H) 0.31 | TOT(A) 0.32 | BRE(H) 0.22 | NEW(A) 0.27 | MCI(H) 0.18 | FUL(H) 0.33 |
| 6 | **NEW** | 1.63 | LEE(A) 0.18 | HUL(H) 0.42 ± | COV(A) 0.31 ± | AVL(H) 0.29 | CRY(A) 0.16 | EVE(H) 0.27 |
| 7 | **TOT** | 1.61 | EVE(H) 0.31 | AVL(H) 0.33 | MUN(A) 0.19 | COV(H) 0.40 ± | CHE(A) 0.14 | CRY(H) 0.24 |
| 8 | **EVE** | 1.60 | TOT(A) 0.31 | IPS(H) 0.31 ± | HUL(A) 0.39 ± | CHE(H) 0.17 | ARS(A) 0.16 | NEW(A) 0.26 |
| 9 | **BRE** | 1.57 | BOU(A) 0.20 | CHE(H) 0.18 | AVL(A) 0.27 | LIV(H) 0.22 | HUL(A) 0.40 ± | NFO(H) 0.30 |
| 10 | **COV** | 1.54 | BHA(H) 0.21 ± | NFO(A) 0.21 ± | NEW(H) 0.28 ± | TOT(A) 0.27 ± | FUL(H) 0.28 ± | SUN(H) 0.29 ± |
| 11 | **CRY** | 1.48 | IPS(H) 0.29 ± | LEE(A) 0.18 | NFO(H) 0.27 | BHA(A) 0.17 | NEW(H) 0.29 | TOT(A) 0.28 |
| 12 | **FUL** | 1.40 | LIV(A) 0.13 | MUN(H) 0.18 | IPS(A) 0.21 ± | HUL(H) 0.39 ± | COV(A) 0.28 ± | AVL(A) 0.21 |
| 13 | **IPS** | 1.36 | CRY(A) 0.15 ± | EVE(A) 0.21 ± | FUL(H) 0.28 ± | MCI(A) 0.10 ± | NFO(H) 0.26 ± | HUL(A) 0.36 ± |
| 14 | **MUN** | 1.36 | MCI(H) 0.16 | FUL(A) 0.27 | TOT(H) 0.36 | LEE(A) 0.20 | BOU(H) 0.24 | CHE(A) 0.13 |
| 15 | **LIV** | 1.34 | FUL(H) 0.33 | BOU(A) 0.20 | MCI(H) 0.17 | BRE(A) 0.17 | BHA(H) 0.25 | ARS(H) 0.22 |
| 16 | **LEE** | 1.34 | NEW(H) 0.30 | CRY(H) 0.22 | ARS(A) 0.15 | MUN(H) 0.22 | SUN(A) 0.26 | BOU(A) 0.19 |
| 17 | **BOU** | 1.32 | BRE(H) 0.21 | LIV(H) 0.22 | CHE(A) 0.13 | SUN(H) 0.33 | MUN(A) 0.18 | LEE(H) 0.25 |
| 18 | **SUN** | 1.30 | ARS(H) 0.20 | MCI(A) 0.12 | BHA(H) 0.23 | BOU(A) 0.19 | LEE(H) 0.24 | COV(A) 0.32 ± |
| 19 | **BHA** | 1.17 | COV(A) 0.30 ± | ARS(H) 0.18 | SUN(A) 0.24 | CRY(H) 0.20 | LIV(A) 0.15 | MCI(A) 0.10 |
| 20 | **HUL** | 0.97 | CHE(A) 0.07 ± | NEW(A) 0.17 ± | EVE(H) 0.20 ± | FUL(A) 0.18 ± | BRE(H) 0.13 ± | IPS(H) 0.22 ± |

## Per club-fixture detail — GW4–GW9

`att` and `def` are presentation-only deciles of λ_att and P(CS) across all 120
rows in the window. Downstream agents read λ_att and P(CS), never the deciles.

#### GW4

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| CHE | HUL | H | 2 | 2.64 | 10 | 0.80 | 0.45 | 10 | ± |
| LIV | FUL | H | 2 | 2.04 | 10 | 1.12 | 0.33 | 9 |  |
| CRY | IPS | H | 2 | 1.90 | 10 | 1.24 | 0.29 | 7 | ± |
| MCI | MUN | A | 4 | 1.80 | 9 | 1.40 | 0.25 | 6 |  |
| LEE | NEW | H | 2 | 1.71 | 8 | 1.21 | 0.30 | 8 |  |
| ARS | SUN | A | 3 | 1.61 | 8 | 0.82 | 0.44 | 10 |  |
| BOU | BRE | H | 3 | 1.61 | 8 | 1.56 | 0.21 | 4 |  |
| BRE | BOU | A | 3 | 1.56 | 7 | 1.61 | 0.20 | 3 |  |
| BHA | COV | A | 2 | 1.55 | 7 | 1.20 | 0.30 | 8 | ± |
| MUN | MCI | H | 4 | 1.40 | 5 | 1.80 | 0.16 | 2 |  |
| IPS | CRY | A | 3 | 1.24 | 4 | 1.90 | 0.15 | 1 | ± |
| AVL | NFO | H | 3 | 1.21 | 3 | 1.16 | 0.31 | 8 |  |
| NEW | LEE | A | 3 | 1.21 | 3 | 1.71 | 0.18 | 2 |  |
| COV | BHA | H | 2 | 1.20 | 3 | 1.55 | 0.21 | 4 | ± |
| EVE | TOT | A | 3 | 1.19 | 3 | 1.17 | 0.31 | 8 |  |
| TOT | EVE | H | 3 | 1.17 | 3 | 1.19 | 0.31 | 8 |  |
| NFO | AVL | A | 4 | 1.16 | 3 | 1.21 | 0.30 | 8 |  |
| FUL | LIV | A | 4 | 1.12 | 2 | 2.04 | 0.13 | 1 |  |
| SUN | ARS | H | 4 | 0.82 | 1 | 1.61 | 0.20 | 3 |  |
| HUL | CHE | A | 4 | 0.80 | 1 | 2.64 | 0.07 | 1 | ± |

#### GW5

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| MCI | SUN | H | 2 | 2.15 | 10 | 0.93 | 0.40 | 10 |  |
| BRE | CHE | H | 4 | 1.81 | 9 | 1.73 | 0.18 | 2 |  |
| NEW | HUL | H | 2 | 1.77 | 9 | 0.86 | 0.42 | 10 | ± |
| CHE | BRE | A | 3 | 1.73 | 9 | 1.81 | 0.16 | 2 |  |
| ARS | BHA | A | 3 | 1.71 | 8 | 1.02 | 0.36 | 9 |  |
| LEE | CRY | H | 3 | 1.71 | 8 | 1.52 | 0.22 | 4 |  |
| MUN | FUL | A | 3 | 1.71 | 8 | 1.33 | 0.27 | 6 |  |
| BOU | LIV | H | 4 | 1.60 | 7 | 1.50 | 0.22 | 4 |  |
| EVE | IPS | H | 2 | 1.58 | 7 | 1.16 | 0.31 | 8 | ± |
| NFO | COV | H | 2 | 1.54 | 7 | 0.86 | 0.42 | 10 | ± |
| CRY | LEE | A | 3 | 1.52 | 6 | 1.71 | 0.18 | 2 |  |
| LIV | BOU | A | 3 | 1.50 | 6 | 1.60 | 0.20 | 3 |  |
| FUL | MUN | H | 4 | 1.33 | 5 | 1.71 | 0.18 | 2 |  |
| IPS | EVE | A | 3 | 1.16 | 3 | 1.58 | 0.21 | 4 | ± |
| TOT | AVL | H | 3 | 1.13 | 2 | 1.11 | 0.33 | 9 |  |
| AVL | TOT | A | 3 | 1.11 | 2 | 1.13 | 0.32 | 8 |  |
| BHA | ARS | H | 4 | 1.02 | 2 | 1.71 | 0.18 | 2 |  |
| SUN | MCI | A | 5 | 0.93 | 1 | 2.15 | 0.12 | 1 |  |
| COV | NFO | A | 3 | 0.86 | 1 | 1.54 | 0.21 | 4 | ± |
| HUL | NEW | A | 3 | 0.86 | 1 | 1.77 | 0.17 | 2 | ± |

#### GW6

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| CHE | BOU | H | 3 | 2.01 | 10 | 1.39 | 0.25 | 6 |  |
| ARS | LEE | H | 2 | 1.87 | 10 | 0.87 | 0.42 | 10 |  |
| MCI | LIV | A | 4 | 1.77 | 9 | 1.43 | 0.24 | 5 |  |
| MUN | TOT | H | 3 | 1.66 | 8 | 1.01 | 0.36 | 9 |  |
| EVE | HUL | A | 2 | 1.60 | 7 | 0.93 | 0.39 | 9 | ± |
| IPS | FUL | H | 2 | 1.56 | 7 | 1.27 | 0.28 | 7 | ± |
| CRY | NFO | H | 3 | 1.55 | 7 | 1.30 | 0.27 | 6 |  |
| BRE | AVL | A | 4 | 1.52 | 6 | 1.31 | 0.27 | 6 |  |
| BHA | SUN | A | 3 | 1.45 | 6 | 1.43 | 0.24 | 5 |  |
| LIV | MCI | H | 4 | 1.43 | 6 | 1.77 | 0.17 | 2 |  |
| SUN | BHA | H | 2 | 1.43 | 6 | 1.45 | 0.23 | 5 |  |
| BOU | CHE | A | 4 | 1.39 | 5 | 2.01 | 0.13 | 1 |  |
| AVL | BRE | H | 3 | 1.31 | 5 | 1.52 | 0.22 | 4 |  |
| NFO | CRY | A | 3 | 1.30 | 4 | 1.55 | 0.21 | 4 |  |
| NEW | COV | A | 2 | 1.29 | 4 | 1.18 | 0.31 | 8 | ± |
| FUL | IPS | A | 2 | 1.27 | 4 | 1.56 | 0.21 | 4 | ± |
| COV | NEW | H | 2 | 1.18 | 3 | 1.29 | 0.28 | 7 | ± |
| TOT | MUN | A | 4 | 1.01 | 2 | 1.66 | 0.19 | 3 |  |
| HUL | EVE | H | 3 | 0.93 | 1 | 1.60 | 0.20 | 3 | ± |
| LEE | ARS | A | 5 | 0.87 | 1 | 1.87 | 0.15 | 1 |  |

#### GW7

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| MCI | IPS | H | 2 | 2.32 | 10 | 0.95 | 0.39 | 9 | ± |
| BRE | LIV | H | 4 | 1.79 | 9 | 1.50 | 0.22 | 4 |  |
| BHA | CRY | H | 3 | 1.75 | 9 | 1.61 | 0.20 | 3 |  |
| CHE | EVE | A | 3 | 1.75 | 9 | 1.40 | 0.25 | 6 |  |
| FUL | HUL | H | 2 | 1.73 | 9 | 0.93 | 0.39 | 9 | ± |
| BOU | SUN | H | 2 | 1.68 | 8 | 1.12 | 0.33 | 9 |  |
| CRY | BHA | A | 3 | 1.61 | 8 | 1.75 | 0.17 | 2 |  |
| LEE | MUN | H | 4 | 1.60 | 7 | 1.52 | 0.22 | 4 |  |
| MUN | LEE | A | 3 | 1.52 | 6 | 1.60 | 0.20 | 3 |  |
| LIV | BRE | A | 3 | 1.50 | 6 | 1.79 | 0.17 | 2 |  |
| ARS | NFO | A | 3 | 1.42 | 6 | 0.88 | 0.42 | 10 |  |
| EVE | CHE | H | 4 | 1.40 | 5 | 1.75 | 0.17 | 2 |  |
| NEW | AVL | H | 3 | 1.30 | 4 | 1.23 | 0.29 | 7 |  |
| TOT | COV | H | 2 | 1.29 | 4 | 0.92 | 0.40 | 10 | ± |
| AVL | NEW | A | 3 | 1.23 | 4 | 1.30 | 0.27 | 6 |  |
| SUN | BOU | A | 3 | 1.12 | 2 | 1.68 | 0.19 | 3 |  |
| IPS | MCI | A | 5 | 0.95 | 2 | 2.32 | 0.10 | 1 | ± |
| HUL | FUL | A | 3 | 0.93 | 1 | 1.73 | 0.18 | 2 | ± |
| COV | TOT | A | 3 | 0.92 | 1 | 1.29 | 0.27 | 6 | ± |
| NFO | ARS | H | 4 | 0.88 | 1 | 1.42 | 0.24 | 5 |  |

#### GW8

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| BRE | HUL | A | 2 | 2.06 | 10 | 0.92 | 0.40 | 10 | ± |
| CHE | TOT | H | 3 | 1.97 | 10 | 1.00 | 0.37 | 9 |  |
| LIV | BHA | H | 2 | 1.91 | 10 | 1.38 | 0.25 | 6 |  |
| CRY | NEW | H | 2 | 1.83 | 9 | 1.25 | 0.29 | 7 |  |
| ARS | EVE | H | 3 | 1.81 | 9 | 0.77 | 0.46 | 10 |  |
| MCI | AVL | A | 4 | 1.73 | 9 | 1.09 | 0.34 | 9 |  |
| MUN | BOU | H | 3 | 1.69 | 8 | 1.41 | 0.24 | 5 |  |
| LEE | SUN | A | 3 | 1.42 | 6 | 1.35 | 0.26 | 6 |  |
| BOU | MUN | A | 4 | 1.41 | 5 | 1.69 | 0.18 | 2 |  |
| BHA | LIV | A | 4 | 1.38 | 5 | 1.91 | 0.15 | 1 |  |
| NFO | IPS | A | 2 | 1.35 | 5 | 1.22 | 0.30 | 8 | ± |
| SUN | LEE | H | 2 | 1.35 | 5 | 1.42 | 0.24 | 5 |  |
| COV | FUL | H | 2 | 1.28 | 4 | 1.26 | 0.28 | 7 | ± |
| FUL | COV | A | 2 | 1.26 | 4 | 1.28 | 0.28 | 7 | ± |
| NEW | CRY | A | 3 | 1.25 | 4 | 1.83 | 0.16 | 2 |  |
| IPS | NFO | H | 3 | 1.22 | 3 | 1.35 | 0.26 | 6 | ± |
| AVL | MCI | H | 4 | 1.09 | 2 | 1.73 | 0.18 | 2 |  |
| TOT | CHE | A | 4 | 1.00 | 2 | 1.97 | 0.14 | 1 |  |
| HUL | BRE | H | 3 | 0.92 | 1 | 2.06 | 0.13 | 1 | ± |
| EVE | ARS | A | 5 | 0.77 | 1 | 1.81 | 0.16 | 2 |  |

#### GW9

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| MCI | BHA | H | 2 | 2.28 | 10 | 1.15 | 0.32 | 8 |  |
| CHE | MUN | H | 4 | 2.03 | 10 | 1.46 | 0.23 | 5 |  |
| BOU | LEE | H | 2 | 1.68 | 8 | 1.37 | 0.25 | 6 |  |
| BRE | NFO | H | 3 | 1.66 | 8 | 1.20 | 0.30 | 8 |  |
| ARS | LIV | A | 4 | 1.54 | 7 | 1.10 | 0.33 | 9 |  |
| AVL | FUL | H | 2 | 1.54 | 7 | 1.10 | 0.33 | 9 |  |
| IPS | HUL | A | 2 | 1.51 | 6 | 1.03 | 0.36 | 9 | ± |
| MUN | CHE | A | 4 | 1.46 | 6 | 2.03 | 0.13 | 1 |  |
| CRY | TOT | A | 3 | 1.43 | 6 | 1.26 | 0.28 | 7 |  |
| LEE | BOU | A | 3 | 1.37 | 5 | 1.68 | 0.19 | 3 |  |
| NEW | EVE | H | 3 | 1.36 | 5 | 1.31 | 0.27 | 6 |  |
| EVE | NEW | A | 3 | 1.31 | 5 | 1.36 | 0.26 | 6 |  |
| TOT | CRY | H | 3 | 1.26 | 4 | 1.43 | 0.24 | 5 |  |
| SUN | COV | A | 2 | 1.25 | 4 | 1.13 | 0.32 | 8 | ± |
| NFO | BRE | A | 3 | 1.20 | 3 | 1.66 | 0.19 | 3 |  |
| BHA | MCI | A | 5 | 1.15 | 3 | 2.28 | 0.10 | 1 |  |
| COV | SUN | H | 2 | 1.13 | 2 | 1.25 | 0.29 | 7 | ± |
| FUL | AVL | A | 4 | 1.10 | 2 | 1.54 | 0.21 | 4 |  |
| LIV | ARS | H | 4 | 1.10 | 2 | 1.54 | 0.22 | 4 |  |
| HUL | IPS | H | 2 | 1.03 | 2 | 1.51 | 0.22 | 4 | ± |

## Top fixture swings

Halves of the window compared: GW4–6 against GW7–9.

| # | Club | Swing | Detail |
|---:|---|---|---|
| 1 | **EVE** | attack **−0.89** Σλ_att, defence **−0.42** ΣP(CS) — worst combined | TOT(A) IPS(H) HUL(A) → **CHE(H) ARS(A) NEW(A)**. The steepest decline in the league on both axes at once. Everton assets are a GW4–6 hold and nothing beyond: ARS(A) at λ_att **0.77** is the second-worst attacking row in the entire window, and Everton's own top-third defensive run (GW4–6) expires in the same breath. |
| 2 | **CHE** | attack **−0.63** | HUL(H) BRE(A) BOU(H) → EVE(A) TOT(H) MUN(H). Chelsea top the attacking ticker almost entirely on the first half, and the single biggest row in it (HUL(H) 2.64) is banded. Their second half is merely above average. |
| 3 | **BRE** | attack **+0.62**, defence **+0.27** | BOU(A) CHE(H) AVL(A) → LIV(H) HUL(A) NFO(H). The largest combined improvement. Brentford are 3rd on the attacking ticker and their better half is the later one — a buy-and-hold, not a sell-by-GW7. |
| 4 | **MCI** | attack **+0.61**, defence **+0.16** | MUN(A) SUN(H) LIV(A) → IPS(H) AVL(A) BHA(H). City's window is back-loaded: two of the three hardest fixtures land in GW4–6 (derby away, Anfield). Their three best attacking rows are GW7 (banded), GW9 and GW5. |
| 5 | **FUL** | defence **+0.36**, attack **+0.37** | LIV(A) MUN(H) IPS(A) → HUL(H) COV(A) AVL(A). The largest defensive improvement, and **two of the three** improving fixtures are banded. Per C4's residual, a Fulham clean sheet must not be the largest defensive EP term for a selected player. |

Also worth naming: **NFO −0.57 attack / −0.20 defence** (AVL(A) COV(H) CRY(A) →
ARS(H) IPS(A) BRE(A)) — Forest rank 4th on the defensive ticker overall, but the
strength is GW4–5 (0.30, 0.42) and from GW6 only one row reaches 0.30; **SUN +0.54 attack**, the second-largest attacking rise, which still
leaves Sunderland 17th.

### Multi-GW runs

Top third = λ_att ≥ 1.58 / P(CS) ≥ 0.29 across the window's 120 rows.
Consecutive runs only.

| Run | Club | Fixtures |
|---|---|---|
| Attack, top third, **all six** | **CHE** | HUL(H) 2.64 ±, BRE(A) 1.73, BOU(H) 2.01, EVE(A) 1.75, TOT(H) 1.97, MUN(H) 2.03 |
| Attack, top third, **all six** | **MCI** | MUN(A) 1.80, SUN(H) 2.15, LIV(A) 1.77, IPS(H) 2.32 ±, AVL(A) 1.73, BHA(H) 2.28 — att-score ≥ 9 on every row |
| Attack, top third, GW4–6 | **ARS** | SUN(A) 1.61, BHA(A) 1.71, LEE(H) 1.87 |
| Attack, top third, GW7–9 | **BRE** | LIV(H) 1.79, HUL(A) 2.06 ±, NFO(H) 1.66 |
| Defence, top third, **all six** | **ARS** | every row P(CS) ≥ 0.33, five of six ≥ 0.36 |
| Defence, top third, GW4–6 | **EVE** | TOT(A) 0.31, IPS(H) 0.31 ±, HUL(A) 0.39 ± — two of three banded, expires at GW7 |
| Defence, top third, GW5–7 | **NEW** | HUL(H) 0.42 ±, COV(A) 0.31 ±, AVL(H) 0.29 — two of three banded |
| Defence, top third, GW7–9 | **MCI** | IPS(H) 0.39 ±, AVL(A) 0.34, BHA(H) 0.32 |
| Defence, bottom third, GW4–9 | **HUL**, **BHA**, **SUN** | 16 of their 18 rows below P(CS) 0.25; none above 0.32 |
| Attack, bottom third, GW4–9 | **HUL** | no row above λ_att 1.03 |

Both six-gameweek defensive runs and both six-gameweek attacking runs belong to
the same three clubs — ARS, CHE, MCI. No other club holds a top-third run
longer than three gameweeks on either axis.

## FPL FDR vs this model

FDR is the mean of `team_h_difficulty` / `team_a_difficulty` over the six rows.
Rank 1 = easiest ticker. Disagreements of ≥ 8 places are bolded.

| Club | mean FDR | FDR rank | model ATT rank | model CS rank | FDR−ATT | FDR−CS |
|---|---:|---:|---:|---:|---:|---:|
| COV | 2.33 | 1 | 19 | 10 | **-18** | **-9** |
| CRY | 2.67 | 2 | 5 | 11 | -3 | **-9** |
| NEW | 2.67 | 3 | 11 | 6 | **-8** | -3 |
| ARS | 3.00 | 4 | 4 | 1 | +0 | +3 |
| AVL | 3.00 | 5 | 15 | 5 | **-10** | +0 |
| CHE | 3.00 | 6 | 1 | 3 | +5 | +3 |
| FUL | 3.00 | 7 | 13 | 12 | -6 | -5 |
| HUL | 3.00 | 8 | 20 | 20 | **-12** | **-12** |
| IPS | 3.00 | 9 | 14 | 13 | -5 | -4 |
| LIV | 3.00 | 10 | 6 | 15 | +4 | -5 |
| MCI | 3.00 | 11 | 2 | 2 | **+9** | **+9** |
| NFO | 3.00 | 12 | 16 | 4 | -4 | **+8** |
| SUN | 3.00 | 13 | 17 | 18 | -4 | -5 |
| BOU | 3.17 | 14 | 8 | 17 | +6 | -3 |
| EVE | 3.17 | 15 | 12 | 8 | +3 | +7 |
| TOT | 3.17 | 16 | 18 | 7 | -2 | **+9** |
| BRE | 3.33 | 17 | 3 | 9 | **+14** | **+8** |
| LEE | 3.33 | 18 | 9 | 16 | **+9** | +2 |
| MUN | 3.33 | 19 | 7 | 14 | **+12** | +5 |
| BHA | 3.50 | 20 | 10 | 19 | **+10** | +1 |

**Where FDR is most wrong this window:**

- **COV (FDR 1st, model 19th attack)** — the largest disagreement in the file.
  FDR reads Coventry's opponents as soft; the model reads Coventry's own attack
  as the second-worst in the league. An easy fixture list does not manufacture
  shots. Do not buy Coventry attackers off the FDR ticker.
- **BRE (FDR 17th, model 3rd attack)** — FDR's worst miss in the other
  direction, and the actionable one. Brentford's fixtures *look* hard and their
  attacking rating (1.20, 3rd) carries them anyway.
- **MUN (FDR 19th, model 7th attack)** and **BHA (FDR 20th, model 10th)** —
  same class as Brentford: FDR is pricing the opponent's name, the model the
  opponent's conceded xG.
- **HUL (FDR 8th, model 20th on both)** — FDR gives Hull a mid-table ticker.
  The model has them last on attack *and* last on defence. Every Hull asset is
  a trap this window.
- **TOT (FDR 16th, model 7th defensive)** and **NFO (FDR 12th, model 4th
  defensive)** — FDR understates two genuinely good defensive tickers, though
  Forest's is front-loaded (see swings).

The model and FDR agree closely only on **ARS** (4th / 4th / 1st) — the one
club where reputation and conceded xG point the same way.

## Blank and double gameweeks

**None in GW4–GW9.** All 20 clubs play exactly once in each of the six
gameweeks; the window contains 60 fixtures and 120 club-rows.

The first structural disruption is not visible in this window. Nothing here
feeds a Bench Boost or Free Hit case on fixture count.

## C5 — the Triple Captain gate

C5 binds A2 and A4: a Triple Captain must be justified on the captain's own
**fixture-independent** EP, and must not require a promoted club's defensive
rating to clear. GW2 deferred the chip to a GW5 earmark; GW3 re-affirmed it.

**A2's fixture-side read for GW4–9**, City's window being the relevant one:

| GW | Fixture | λ_att | P(CS) | Banded? |
|---:|---|---:|---:|:-:|
| 4 | MUN (A) | 1.80 | 0.25 | no |
| 5 | SUN (H) | 2.15 | 0.40 | no |
| 6 | LIV (A) | 1.77 | 0.24 | no |
| 7 | IPS (H) | **2.32** | 0.39 | **yes** |
| 8 | AVL (A) | 1.73 | 0.34 | no |
| 9 | BHA (H) | **2.28** | 0.32 | no |

Three findings:

1. **GW4 does not clear the gate.** A Manchester derby away at λ_att 1.80 is
   City's third-worst attacking row in the window. No fixture-independent case
   survives it.
2. **GW7 is the highest λ_att but is banded.** IPS(H) at 2.32 is the best
   attacking row City have, and it is exactly the case C5 was written to
   forbid: a chip whose margin comes from a promoted club's rating. Reject it
   on C5 regardless of how the arithmetic lands.
3. **GW9 now beats the GW5 earmark, band-free.** BHA(H) 2.28 against SUN(H)
   2.15 — a **+0.13 λ_att** edge, with neither row banded. Brighton's DEFW has
   risen 0.97 → 1.08 across two cycles (0.30, 3.04, 2.62 xG conceded), which is
   what opens the gap.

**A2 recommends A4 move the Triple Captain earmark from GW5 to GW9**, and holds
that neither GW4 nor GW7 is eligible. The edge is small (+0.13 λ_att ≈ +6% on
the attacking term) and rests on a Brighton defensive rating that has moved a
long way in two cycles — so this is a *forecast* for `chip_plan`, explicitly
not a commitment, and it should be re-tested every cycle to GW9. The
fixture-independent half of the test remains A3's and A4's.

## Uncertainty flags

| Flag | Detail |
|---|---|
| **Split-strength fields still zero** | Fourth GW running. All 20 defence priors are ASSUMPTION-grade, derived from 5-tier `strength_overall`. Current-season weight is now 43–50% of DEFW, which is the only thing making them usable. Re-derive the ticker the moment FPL populates the split fields. |
| **ARS defence is clip-limited** | All three of Arsenal's impDEFW values sit on the 0.55 floor (0.21 / 0.34 / 0.39 xG conceded). Their true DEFW is below what the guard permits, so **P(CS) 0.33–0.46 across the window is a floor, not a central estimate**. Arsenal's defensive ticker is understated and the error is one-directional. |
| **Promoted clubs — band unrelaxed** | COV, HUL, IPS all have 3 played fixtures, the count C4 named for revisiting. Confidence is **not** upgraded: 34 of 120 rows stay banded at ±15% λ_att / ±15pp P(CS), uncertainty stays **HIGH**, and C4's defensive prohibition stands. Revisit at GW6 (n=5). |
| **Clipping still heavy** | 42 of 120 implied ratings hit the guard, only modestly below GW3's rate. Fourteen clubs carry two or more clipped implied values — ARS, AVL, BHA, LEE, LIV, MUN, NFO and TOT have **all three** rounds clipped on at least one axis; BRE, CHE, HUL, IPS, MCI and NEW have two. Each has a rating pulled toward its prior more than the raw xG warrants. |
| **CHE attacking rating vs ticker** | Chelsea top the attacking ticker while their rating *fell* 0.09 this cycle on a 0.39-xG round. The ticker lead is a fixture artefact — and its largest single row (HUL(H) 2.64) is banded. Treat CHE assets as fixture-dependent, not form-backed. |
| **LIV attack trending down, three rounds** | 3.01 → 1.74 → 0.69 xG. The rating (1.15, 5th) is still 66% prior and has not caught up. If round 4 is another sub-1.0, expect a material downgrade at GW5. |
| **No cup/congestion adjustment** | European and domestic-cup fixtures are not modelled — no artifact in the snapshot lists them. Which clubs are in Europe is an **ASSUMPTION** and is deliberately not enumerated here; the rating carries no rotation term either way. The player-analyst applies rotation; the ticker does not. |
| **`played` and `points` are zero in bootstrap** | All 20 clubs report `played: 0`, `points: 0` while `position` carries what looks like a live table. No rating in this file reads those fields — ratings come from xG — but nothing downstream should trust them either. |

## Handoff to downstream agents

- **A3 (player-analyst)**: consume `lambda_att` and `p_cs` from
  `data/analysis/gw4/fixtures.json`. The 1–10 deciles are presentation only.
  Rotation and the 60-minute requirement are yours — P(CS) excludes both.
- **A4 (squad-optimizer)**: the attacking ticker favours CHE and MCI, but CHE's
  lead is front-loaded and banded, and MCI's window is back-loaded. ARS is the
  defensive pick by a wide margin *and* its rating is understated by the clip.
  C5: GW4 and GW7 are ineligible for the Triple Captain; GW9 beats GW5 by
  +0.13 λ_att, band-free.
- **C4 residual, binding**: no selected player may take his single largest
  **defensive** EP term from a fixture against COV, HUL or IPS. The rows that
  trip this are listed under C12 above.
