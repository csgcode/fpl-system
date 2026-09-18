# GW5 — 6-Gameweek Fixture Ticker (GW5–GW10)

Window **GW5–GW10**, all 20 clubs, no blanks, no doubles. Ratings rest on
**four** played rounds; the blend has advanced from GW4's 66/34 to
**59/41** on established-club attack.

Downstream agents consume `lambda_att` and `p_cs` from
`data/analysis/gw5/fixtures.json`. The 1–10 attack/defence scores in this file
are presentation-only deciles and must not be read as inputs.

| Headline | Read |
|---|---|
| Best attacking ticker | **MCI** Σλ_att 11.45, then ARS 10.40, CHE 10.32, BRE 10.07 |
| Best defensive ticker | **ARS** ΣP(CS) 2.17, then MCI 1.99, EVE 1.77 |
| Worst combined | **HUL** (20th attack, 19th defence), then **COV** (19th/15th); **BHA** is 7th on attack and **20th** on defence |
| Largest swings | **SUN +0.71** and **LIV +0.69** attack improving; **NFO −0.63** attack and **NEW −0.30** defence declining |
| Blanks / doubles | none in GW5–GW10 |

## What changed since GW4

### 1. Round 4 reproduces the GW4 pipeline exactly — no method change

The club-attribution rule (attribute an `element-summary` history row by the
row's own fixture, never by the player's current bootstrap `team`) is carried
forward unchanged, and re-running rounds 1–3 through it reproduces GW4's
published xG/xGA column on all 20 clubs to the last decimal, its 42-of-120
clip count, and its ATT/DEFW to two decimals on every club. The only new
information this cycle is round 4 itself.

Coverage: 433 element summaries read; 117 player-rounds missing from the
snapshot recovered from the `event-live` files (rounds 1–4), worth **4.72 xG**
league-wide — unchanged in character from GW4's 3.51 over three rounds.

### 2. FPL has still not populated the split-strength fields

Fifth gameweek running: `strength_attack_home/away` and
`strength_defence_home/away` are **0** for all 20 clubs, and `strength` is
`null`. Defence priors still come from `strength_overall_home/away` — five
tiers across twenty clubs — and remain **ASSUMPTION**-grade. The mitigating
trend continues: the current-season component is now 50–57% of DEFW, against
43–50% at GW4, so the weak prior's share keeps falling on its own.

### 3. The blend advanced, on the schedule GW2 set

No parameter was retuned. Each prior's worth stays fixed at `k`
match-equivalents; the match count `n` grew from 3 to 4. Promoted-club attack
has now reached the ≥50% current weight GW1 targeted for GW4.

### 4. Clipping has stopped declining

**56 of 160** implied ratings hit the [0.55, 1.80] guard. Round 4 alone
contributed **14 of 40** (35.0%) against round 3's 13 of 40 (32.5%) and rounds
1–2's 36.3%. The decline GW3 forecast and GW4 recorded did not continue; one
match's xG still dominates a club's implied rating.

## Corrections applied

Binding set: the corrections addressed to **A2** in `data/retro/gw1.md`
through `data/retro/gw4.md` — C4 (revised by C12), C5 and C12.

### C12 (A2) — the promoted-club band, two-sided

Carried forward unchanged. COV, HUL and IPS on *either* side of a fixture set
`band: true` on *both* club-rows — **34 of 120 rows** this window (GW4: 34).

1. **The band covers `lambda_att` as well as `p_cs`.** Read λ_att ±15% and
   P(CS) ±15pp on any `±` row.
2. **No haircut to the central attacking estimate.** Every club facing promoted
   opposition carries its full modelled λ_att: **ARS 2.21 v HUL(H)** — the
   highest single λ_att in the window — MCI 2.08 v IPS(H), NFO 1.85 v COV(H),
   BRE 1.80 at HUL, EVE 1.69 v COV(H), NEW 1.59 v HUL(H), FUL 1.55 v HUL(H).
   The uncertainty is published as a band, never as a discount.
3. C4's residual prohibition — *never let a promoted-club fixture be the single
   largest defensive EP term for a selected player* — **stands for defensive
   terms only**, and bites harder this window than last. The rows it forbids,
   P(CS) ≥ 0.30:

   | GW | Club | Fixture | P(CS) |
   |---:|---|---|---:|
   | 10 | ARS | HUL (H) | **0.52** |
   | 5 | NFO | COV (H) | 0.43 |
   | 10 | EVE | COV (H) | 0.40 |
   | 7 | TOT | COV (H) | 0.39 |
   | 7 | MCI | IPS (H) | 0.38 |
   | 5 | NEW | HUL (H) | 0.38 |
   | 6 | EVE | HUL (A) | 0.38 |
   | 7 | FUL | HUL (H) | 0.37 |
   | 8 | BRE | HUL (A) | 0.36 |
   | 5 | EVE | IPS (H) | 0.31 |
   | 9 | SUN | COV (A) | 0.31 |

   **ARS v HUL(H) at 0.52 is the single best defensive row in the window and
   it is banded** — the exact configuration C4 was written to forbid. An
   Arsenal defender selected for GW10 must not take his largest defensive term
   from it.

**Promoted-club convergence.** All three now have 4 played fixtures. **The band
is kept.** GW4 set the revisit at n=5, and round 4 supplies the reason to hold:
COV's implied DEFW hit the 1.80 ceiling (2.80 xG conceded to Brighton) while
HUL's hit the 0.55 floor (0.91 xG conceded at Chelsea) in the same round — the
two promoted defences moved to opposite guards on one weekend. Revisit at GW6
(n=5), as scheduled, not before.

### C5 (A2, A4) — the Triple Captain gate

Active and binding. Examined under its own heading below. Short version: **the
GW9 earmark GW4 set is re-affirmed and its margin widens; GW5 does not displace
it, and GW7 stays ineligible.**

### C4 (A2) — superseded

Revised by C12. Its confidence-downgrade instruction is discharged by keeping
promoted-club uncertainty at HIGH with the band unrelaxed at n=4.

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
for the whole four-round history — so a round's implied value never depends on
the order rounds were processed. Implied values are clipped to **[0.55, 1.80]**
before blending.

Rating = `(k * prior + Σ implied) / (k + n)`, with `n = 4`:

| Rating | Prior source | k | w_prior / w_current (n=4) | was at GW4 |
|---|---|---:|---|---|
| Attack, established | real prior-season squad xG | 5.7 | **59 / 41** | 66 / 34 |
| Defence, established | 5-tier `strength_overall` only | 4.0 | **50 / 50** | 57 / 43 |
| Attack, promoted | ASSUMPTION | 4.0 | **50 / 50** | 57 / 43 |
| Defence, promoted | ASSUMPTION | 3.0 | **43 / 57** | 50 / 50 |

Defence takes more current weight than attack because its **prior is weaker**,
not because its data is better. Prior weight stays ≥20% through GW10 on every
line (at GW10, n=9: established attack 39%, promoted defence 25%).

## Team ratings — GW5 (four rounds blended)

`Δ GW4` compares `data/analysis/gw4/fixtures.json`. `*` marks an implied value
clipped to [0.55, 1.80] before blending. **A** marks a promoted club.

| Club | xG 1/2/3/4 | xGA 1/2/3/4 | impATT 1/2/3/4 | impDEFW 1/2/3/4 | clips |
|---|---|---|---|---|---:|
| MCI | 2.24 / 2.22 / 2.12 / 1.10 | 0.65 / 0.68 / 1.37 / 1.01 | 1.47 / 1.72 / 1.06 / 0.95 | 0.55* / 0.55* / 1.51 / 0.57 | 2 |
| CHE | 2.23 / 3.04 / 0.39 / 0.91 | 1.38 / 1.46 / 2.06 / 1.39 | 1.64 / 1.80* / 0.55* / 0.55* | 1.19 / 1.22 / 1.05 / 1.69 | 3 |
| ARS | 1.88 / 1.04 / 2.06 / 1.89 | 0.21 / 0.34 / 0.39 / 1.80 | 0.94 / 0.82 / 1.49 / 1.39 | 0.55* / 0.55* / 0.55* / 1.48 | 3 |
| BRE | 3.91 / 1.67 / 1.21 / 0.52 | 0.57 / 1.46 / 1.71 / 1.78 | 1.80* / 1.22 / 0.77 / 0.55* | 0.55* / 0.89 / 1.63 / 1.02 | 3 |
| LIV | 3.01 / 1.74 / 0.69 / 1.29 | 1.58 / 2.30 / 0.76 / 0.69 | 1.80* / 1.13 / 0.55* / 0.82 | 1.04 / 1.80* / 0.71 / 0.69 | 3 |
| MUN | 1.82 / 5.15 / 0.69 / 1.01 | 1.08 / 2.06 / 1.02 / 1.10 | 1.01 / 1.80* / 0.55* / 0.82 | 1.13 / 1.80* / 0.70 / 0.60 | 3 |
| CRY | 1.97 / 0.68 / 1.98 / 0.61 | 1.12 / 2.22 / 3.16 / 1.70 | 1.48 / 0.55 / 1.46 / 0.55* | 0.77 / 1.20 / 1.80* / 1.80* | 3 |
| BOU | 0.65 / 2.19 / 1.37 / 1.78 | 2.24 / 1.87 / 0.70 / 0.52 | 0.61 / 1.42 / 1.02 / 1.17 | 1.05 / 1.50 / 0.55* / 0.55* | 2 |
| LEE | 0.47 / 1.46 / 2.62 / 2.07 | 0.65 / 1.67 / 2.20 / 0.87 | 0.55* / 0.96 / 1.80* / 1.33 | 0.55* / 1.04 / 1.59 / 0.66 | 3 |
| NEW | 1.58 / 0.72 / 0.70 / 0.87 | 3.01 / 1.13 / 1.37 / 2.07 | 1.21 / 0.55 / 0.55* / 0.64 | 1.80* / 0.88 / 0.91 / 1.27 | 2 |
| AVL | 0.30 / 0.34 / 1.93 / 0.82 | 3.77 / 1.04 / 0.57 / 2.30 | 0.55* / 0.55* / 1.07 / 0.55* | 1.80* / 0.61 / 0.60 / 1.80* | 5 |
| EVE | 1.12 / 1.87 / 1.02 / 1.12 | 1.97 / 2.19 / 0.69 / 0.69 | 0.75 / 1.42 / 0.76 / 0.86 | 1.30 / 1.26 / 0.55* / 0.55* | 2 |
| NFO | 0.65 / 2.30 / 0.93 / 2.30 | 0.47 / 1.74 / 1.07 / 0.82 | 0.55* / 1.80* / 0.62 / 1.80* | 0.55* / 0.96 / 0.97 / 0.55* | 5 |
| BHA | 3.77 / 1.46 / 2.20 / 2.80 | 0.30 / 3.04 / 2.62 / 1.37 | 1.80* / 1.22 / 1.39 / 1.62 | 0.55* / 1.44 / 1.80* / 1.31 | 3 |
| TOT | 0.57 / 1.13 / 1.07 / 0.69 | 3.91 / 0.72 / 0.93 / 1.12 | 0.55* / 0.73 / 0.80 / 0.55* | 1.80* / 0.55* / 0.66 / 0.90 | 4 |
| SUN | 0.67 / 2.03 / 1.71 / 1.80 | 1.79 / 0.94 / 1.21 / 1.89 | 0.55* / 1.29 / 1.30 / 1.67 | 1.66 / 0.94 / 0.65 / 1.11 | 1 |
| FUL | 1.38 / 0.94 / 3.16 / 0.69 | 2.23 / 2.03 / 1.98 / 1.29 | 1.00 / 0.69 / 1.80* / 0.61 | 1.22 / 1.67 / 1.31 / 0.71 | 1 |
| IPS | 1.79 / 2.06 / 0.76 / 1.70 | 0.67 / 5.15 / 0.69 / 0.61 | 1.14 / 1.78 / 0.58 / 1.32 | 0.64 / 1.80* / 0.55* / 0.55* | 3 |
| COV | 0.21 / 1.30 / 1.37 / 1.37 | 1.88 / 0.72 / 2.12 / 2.80 | 0.55* / 0.62 / 1.29 / 0.89 | 0.95 / 0.87 / 0.99 / 1.80* | 2 |
| HUL | 1.08 / 0.72 / 0.57 / 1.39 | 1.82 / 1.30 / 1.93 / 0.91 | 0.81 / 0.55* / 0.55* / 1.16 | 1.18 / 1.24 / 1.48 / 0.55* | 3 |

| Club | ATT prior | **ATT** | Δ GW4 | DEFW prior | **DEFW** | Δ GW4 |
|---|---:|---:|---:|---:|---:|---:|
| MCI | 1.39 | **1.33** | -0.04 | 0.80 | **0.78** | -0.03 |
| CHE | 1.37 | **1.25** | -0.08 | 0.90 | **1.07** | +0.09 |
| ARS | 1.28 | **1.21** | +0.02 | 0.70 | **0.72** | +0.10 |
| BRE | 1.21 | **1.14** | -0.06 | 0.99 | **0.98** | +0.00 |
| BHA | 0.90 | **1.13** | +0.06 | 1.00 | **1.11** | +0.03 |
| LIV | 1.18 | **1.11** | -0.04 | 0.85 | **0.93** | -0.04 |
| MUN | 1.16 | **1.09** | -0.03 | 0.87 | **0.94** | -0.05 |
| BOU | 1.13 | **1.08** | +0.01 | 0.99 | **0.93** | -0.05 |
| LEE | 1.06 | **1.08** | +0.03 | 1.03 | **0.97** | -0.05 |
| CRY | 1.14 | **1.06** | -0.06 | 0.97 | **1.15** | +0.09 |
| NFO | 0.92 | **1.01** | +0.09 | 1.00 | **0.86** | -0.04 |
| SUN | 0.79 | **0.94** | +0.08 | 1.02 | **1.03** | +0.01 |
| IPS **A** | 0.70 | **0.93** | +0.05 | 1.26 | **1.02** | -0.08 |
| EVE | 0.94 | **0.92** | -0.01 | 1.00 | **0.94** | -0.05 |
| NEW | 0.99 | **0.87** | -0.02 | 1.01 | **1.09** | +0.03 |
| FUL | 0.75 | **0.85** | -0.02 | 1.02 | **1.10** | -0.05 |
| AVL | 0.98 | **0.84** | -0.03 | 0.95 | **1.05** | +0.10 |
| COV **A** | 0.68 | **0.74** | +0.02 | 1.30 | **1.19** | +0.10 |
| TOT | 0.83 | **0.74** | -0.03 | 0.98 | **0.95** | -0.01 |
| HUL **A** | 0.62 | **0.68** | +0.07 | 1.36 | **1.19** | -0.10 |

### Biggest rating changes vs GW4

| Club | Change | Driver |
|---|---|---|
| **ARS DEFW 0.62 → 0.72** (+0.10) | the clip streak breaks | Arsenal conceded **1.80 xG at Sunderland** — implied 1.48, the first of their four defensive rounds not to hit the 0.55 floor. GW4 flagged their rating as guard-limited and one-directional; round 4 supplies the first real reading, and it is materially worse than the floor. ARS stay 1st on the defensive ticker (next-best DEFW is MCI 0.78), but ΣP(CS) falls 2.43 → 2.17. |
| **AVL DEFW 0.95 → 1.05** (+0.10) | largest defensive downgrade | **2.30 xG conceded at home to Forest**, implied 1.80 and clipped — Villa's second ceiling-clipped defensive round in four. |
| **COV DEFW 1.09 → 1.19** (+0.10) | | 2.80 xG conceded to Brighton, implied 1.80 and clipped. Coventry's worst defensive round, and it lands on an ASSUMPTION-grade prior. |
| **HUL DEFW 1.29 → 1.19** (−0.10) | largest defensive upgrade | Conceded **0.91 xG at Chelsea**, implied 0.55 and floored. Hull's best defensive round; it still leaves them 19th on the defensive ticker. |
| **CHE DEFW 0.98 → 1.07** (+0.09) and **ATT 1.33 → 1.25** (−0.08) | worst combined move | Chelsea conceded 1.39 xG **to Hull at home** and generated only 0.91 from it — implied 0.55, floored, their second straight floored attacking round. GW4's warning that Chelsea's ticker lead was a fixture artefact rather than form is now priced in: they fall from 1st to 3rd on attack. |
| **CRY DEFW 1.06 → 1.15** (+0.09) | | 1.70 xG conceded to Ipswich, implied 1.80 and clipped — a second consecutive ceiling clip. Palace are now 18th on the defensive ticker. |
| **NFO ATT 0.92 → 1.01** (+0.09) | largest attacking rise | **2.30 xG at Villa Park**, implied 1.80 and clipped. Forest have now clipped the attacking ceiling twice in four rounds and the rating may still lag. |
| **SUN ATT 0.86 → 0.94** (+0.08) | | 1.80 xG against Arsenal, implied 1.67 — their best attacking round, against the best defence in the league. Still 14th. |
| **IPS DEFW 1.10 → 1.02** (−0.08) | | 0.61 xG conceded at Palace, implied 0.55 and floored. Ipswich now rate the best of the three promoted defences by a clear margin, on an ASSUMPTION prior — treat within the band. |
| **BHA ATT 1.07 → 1.13** (+0.06) | | 2.80 xG at Coventry, implied 1.62. Brighton are 7th on attack and **20th on defence** — the widest split in the file. |
| **BRE ATT 1.20 → 1.14** (−0.06) | | 0.52 xG at Bournemouth, implied 0.55 and floored. Brentford keep 4th on attack on the prior, not on round 4. |
| **MCI ATT 1.37 → 1.33** (−0.04), **DEFW 0.81 → 0.78** (−0.03) | notable non-move | 1.10 xG and 1.01 conceded in the Manchester derby — both near the mean, both unclipped. City's ratings barely move and they take top spot on attack by attrition. |

## 6-GW ticker — best attacking (ranked by Σ λ_att, GW5–10)

`±` marks a fixture carrying the two-sided promoted-club band.

| # | Club | Σλ_att | GW5 | GW6 | GW7 | GW8 | GW9 | GW10 |
|---:|---|---:|---|---|---|---|---|---|
| 1 | **MCI** | 11.45 | SUN(H) 2.10 | LIV(A) 1.64 | IPS(H) 2.08 ± | AVL(A) 1.85 | BHA(H) 2.27 | NFO(A) 1.51 |
| 2 | **ARS** | 10.40 | BHA(A) 1.78 | LEE(H) 1.80 | NFO(A) 1.38 | EVE(H) 1.74 | LIV(A) 1.49 | HUL(H) 2.21 ± |
| 3 | **CHE** | 10.32 | BRE(A) 1.63 | BOU(H) 1.78 | EVE(A) 1.55 | TOT(H) 1.84 | MUN(H) 1.81 | SUN(A) 1.71 |
| 4 | **BRE** | 10.07 | CHE(H) 1.87 | AVL(A) 1.59 | LIV(H) 1.63 | HUL(A) 1.80 ± | NFO(H) 1.50 | BHA(A) 1.68 |
| 5 | **MUN** | 9.47 | FUL(A) 1.59 | TOT(H) 1.60 | LEE(A) 1.41 | BOU(H) 1.56 | CHE(A) 1.55 | AVL(H) 1.76 |
| 6 | **BOU** | 9.21 | LIV(H) 1.55 | CHE(A) 1.53 | SUN(H) 1.71 | MUN(A) 1.35 | LEE(H) 1.61 | IPS(A) 1.46 ± |
| 7 | **BHA** | 9.08 | ARS(H) 1.26 | SUN(A) 1.54 | CRY(H) 2.00 | LIV(A) 1.40 | MCI(A) 1.17 | BRE(H) 1.71 |
| 8 | **LIV** | 9.03 | BOU(A) 1.37 | MCI(H) 1.34 | BRE(A) 1.46 | BHA(H) 1.91 | ARS(H) 1.24 | CRY(A) 1.71 |
| 9 | **CRY** | 9.02 | LEE(A) 1.38 | NFO(H) 1.41 | BHA(A) 1.57 | NEW(H) 1.78 | TOT(A) 1.35 | LIV(H) 1.53 |
| 10 | **LEE** | 8.92 | CRY(H) 1.92 | ARS(A) 1.04 | MUN(H) 1.56 | SUN(A) 1.48 | BOU(A) 1.33 | TOT(H) 1.59 |
| 11 | **NFO** | 8.43 | COV(H) 1.85 ± | CRY(A) 1.55 | ARS(H) 1.13 | IPS(A) 1.37 ± | BRE(A) 1.32 | MCI(H) 1.21 |
| 12 | **EVE** | 8.35 | IPS(H) 1.45 ± | HUL(A) 1.46 ± | CHE(H) 1.52 | ARS(A) 0.89 | NEW(A) 1.34 | COV(H) 1.69 ± |
| 13 | **NEW** | 8.21 | HUL(H) 1.59 ± | COV(A) 1.37 ± | AVL(H) 1.40 | CRY(A) 1.33 | EVE(H) 1.25 | FUL(A) 1.27 |
| 14 | **SUN** | 8.19 | MCI(A) 0.97 | BHA(H) 1.61 | BOU(A) 1.16 | LEE(H) 1.41 | COV(A) 1.49 ± | CHE(H) 1.55 |
| 15 | **FUL** | 7.87 | MUN(H) 1.23 | IPS(A) 1.15 ± | HUL(H) 1.55 ± | COV(A) 1.34 ± | AVL(A) 1.18 | NEW(H) 1.42 |
| 16 | **IPS** | 7.75 | EVE(A) 1.16 ± | FUL(H) 1.58 ± | MCI(A) 0.97 ± | NFO(H) 1.23 ± | HUL(A) 1.48 ± | BOU(H) 1.33 ± |
| 17 | **AVL** | 7.03 | TOT(A) 1.07 | BRE(H) 1.27 | NEW(A) 1.21 | MCI(H) 1.01 | FUL(H) 1.42 | MUN(A) 1.05 |
| 18 | **TOT** | 6.83 | AVL(H) 1.20 | MUN(A) 0.93 | COV(H) 1.36 ± | CHE(A) 1.06 | CRY(H) 1.32 | LEE(A) 0.96 |
| 19 | **COV** | 6.39 | NFO(A) 0.85 ± | NEW(H) 1.24 ± | TOT(A) 0.94 ± | FUL(H) 1.26 ± | SUN(H) 1.18 ± | EVE(A) 0.92 ± |
| 20 | **HUL** | 5.70 | NEW(A) 0.98 ± | EVE(H) 0.98 ± | FUL(A) 0.99 ± | BRE(H) 1.03 ± | IPS(H) 1.07 ± | ARS(A) 0.65 ± |

## 6-GW ticker — best defensive (ranked by Σ P(CS), GW5–10)

| # | Club | ΣP(CS) | GW5 | GW6 | GW7 | GW8 | GW9 | GW10 |
|---:|---|---:|---|---|---|---|---|---|
| 1 | **ARS** | 2.17 | BHA(A) 0.28 | LEE(H) 0.35 | NFO(A) 0.32 | EVE(H) 0.41 | LIV(A) 0.29 | HUL(H) 0.52 ± |
| 2 | **MCI** | 1.99 | SUN(H) 0.38 | LIV(A) 0.26 | IPS(H) 0.38 ± | AVL(A) 0.36 | BHA(H) 0.31 | NFO(A) 0.30 |
| 3 | **EVE** | 1.77 | IPS(H) 0.31 ± | HUL(A) 0.38 ± | CHE(H) 0.21 | ARS(A) 0.18 | NEW(A) 0.29 | COV(H) 0.40 ± |
| 4 | **MUN** | 1.66 | FUL(A) 0.29 | TOT(H) 0.39 | LEE(A) 0.21 | BOU(H) 0.26 | CHE(A) 0.16 | AVL(H) 0.35 |
| 5 | **NFO** | 1.65 | COV(H) 0.43 ± | CRY(A) 0.24 | ARS(H) 0.25 | IPS(A) 0.29 ± | BRE(A) 0.22 | MCI(H) 0.22 |
| 6 | **NEW** | 1.64 | HUL(H) 0.38 ± | COV(A) 0.29 ± | AVL(H) 0.30 | CRY(A) 0.17 | EVE(H) 0.26 | FUL(A) 0.24 |
| 7 | **FUL** | 1.58 | MUN(H) 0.20 | IPS(A) 0.21 ± | HUL(H) 0.37 ± | COV(A) 0.28 ± | AVL(A) 0.24 | NEW(H) 0.28 |
| 8 | **TOT** | 1.55 | AVL(H) 0.34 | MUN(A) 0.20 | COV(H) 0.39 ± | CHE(A) 0.16 | CRY(H) 0.26 | LEE(A) 0.20 |
| 9 | **BRE** | 1.52 | CHE(H) 0.20 | AVL(A) 0.28 | LIV(H) 0.23 | HUL(A) 0.36 ± | NFO(H) 0.27 | BHA(A) 0.18 |
| 10 | **IPS** | 1.49 | EVE(A) 0.23 ± | FUL(H) 0.32 ± | MCI(A) 0.12 ± | NFO(H) 0.25 ± | HUL(A) 0.34 ± | BOU(H) 0.23 ± |
| 11 | **LEE** | 1.48 | CRY(H) 0.25 | ARS(A) 0.17 | MUN(H) 0.24 | SUN(A) 0.24 | BOU(A) 0.20 | TOT(H) 0.38 |
| 12 | **BOU** | 1.46 | LIV(H) 0.25 | CHE(A) 0.17 | SUN(H) 0.31 | MUN(A) 0.21 | LEE(H) 0.26 | IPS(A) 0.26 ± |
| 13 | **AVL** | 1.39 | TOT(A) 0.30 | BRE(H) 0.20 | NEW(A) 0.25 | MCI(H) 0.16 | FUL(H) 0.31 | MUN(A) 0.17 |
| 14 | **CHE** | 1.36 | BRE(A) 0.15 | BOU(H) 0.22 | EVE(A) 0.22 | TOT(H) 0.35 | MUN(H) 0.21 | SUN(A) 0.21 |
| 15 | **COV** | 1.34 | NFO(A) 0.16 ± | NEW(H) 0.25 ± | TOT(A) 0.26 ± | FUL(H) 0.26 ± | SUN(H) 0.23 ± | EVE(A) 0.18 ± |
| 16 | **LIV** | 1.30 | BOU(A) 0.21 | MCI(H) 0.19 | BRE(A) 0.20 | BHA(H) 0.25 | ARS(H) 0.23 | CRY(A) 0.22 |
| 17 | **SUN** | 1.23 | MCI(A) 0.12 | BHA(H) 0.21 | BOU(A) 0.18 | LEE(H) 0.23 | COV(A) 0.31 ± | CHE(H) 0.18 |
| 18 | **CRY** | 1.21 | LEE(A) 0.15 | NFO(H) 0.21 | BHA(A) 0.14 | NEW(H) 0.26 | TOT(A) 0.27 | LIV(H) 0.18 |
| 19 | **HUL** | 1.15 | NEW(A) 0.20 ± | EVE(H) 0.23 ± | FUL(A) 0.21 ± | BRE(H) 0.17 ± | IPS(H) 0.23 ± | ARS(A) 0.11 ± |
| 20 | **BHA** | 1.02 | ARS(H) 0.17 | SUN(A) 0.20 | CRY(H) 0.21 | LIV(A) 0.15 | MCI(A) 0.10 | BRE(H) 0.19 |

## Per club-fixture detail — GW5–GW10

`att` and `def` are presentation-only deciles of λ_att and P(CS) across all 120
rows in the window. Downstream agents read λ_att and P(CS), never the deciles.

#### GW5

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| MCI | SUN | H | 2 | 2.10 | 10 | 0.97 | 0.38 | 10 |  |
| LEE | CRY | H | 3 | 1.92 | 10 | 1.38 | 0.25 | 6 |  |
| BRE | CHE | H | 4 | 1.87 | 10 | 1.63 | 0.20 | 3 |  |
| NFO | COV | H | 2 | 1.85 | 10 | 0.85 | 0.43 | 10 | ± |
| ARS | BHA | A | 3 | 1.78 | 9 | 1.26 | 0.28 | 8 |  |
| CHE | BRE | A | 3 | 1.63 | 8 | 1.87 | 0.15 | 1 |  |
| MUN | FUL | A | 3 | 1.59 | 8 | 1.23 | 0.29 | 8 |  |
| NEW | HUL | H | 2 | 1.59 | 8 | 0.98 | 0.38 | 10 | ± |
| BOU | LIV | H | 4 | 1.55 | 7 | 1.37 | 0.25 | 6 |  |
| EVE | IPS | H | 2 | 1.45 | 6 | 1.16 | 0.31 | 9 | ± |
| CRY | LEE | A | 3 | 1.38 | 5 | 1.92 | 0.15 | 1 |  |
| LIV | BOU | A | 3 | 1.37 | 5 | 1.55 | 0.21 | 4 |  |
| BHA | ARS | H | 4 | 1.26 | 4 | 1.78 | 0.17 | 2 |  |
| FUL | MUN | H | 4 | 1.23 | 3 | 1.59 | 0.20 | 3 |  |
| TOT | AVL | H | 3 | 1.20 | 3 | 1.07 | 0.34 | 9 |  |
| IPS | EVE | A | 3 | 1.16 | 2 | 1.45 | 0.23 | 5 | ± |
| AVL | TOT | A | 3 | 1.07 | 2 | 1.20 | 0.30 | 8 |  |
| HUL | NEW | A | 3 | 0.98 | 1 | 1.59 | 0.20 | 3 | ± |
| SUN | MCI | A | 5 | 0.97 | 1 | 2.10 | 0.12 | 1 |  |
| COV | NFO | A | 3 | 0.85 | 1 | 1.85 | 0.16 | 2 | ± |

#### GW6

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| ARS | LEE | H | 2 | 1.80 | 10 | 1.04 | 0.35 | 9 |  |
| CHE | BOU | H | 3 | 1.78 | 9 | 1.53 | 0.22 | 5 |  |
| MCI | LIV | A | 4 | 1.64 | 8 | 1.34 | 0.26 | 7 |  |
| SUN | BHA | H | 2 | 1.61 | 8 | 1.54 | 0.21 | 4 |  |
| MUN | TOT | H | 3 | 1.60 | 8 | 0.93 | 0.39 | 10 |  |
| BRE | AVL | A | 4 | 1.59 | 8 | 1.27 | 0.28 | 8 |  |
| IPS | FUL | H | 2 | 1.58 | 8 | 1.15 | 0.32 | 9 | ± |
| NFO | CRY | A | 3 | 1.55 | 7 | 1.41 | 0.24 | 6 |  |
| BHA | SUN | A | 3 | 1.54 | 7 | 1.61 | 0.20 | 3 |  |
| BOU | CHE | A | 4 | 1.53 | 7 | 1.78 | 0.17 | 2 |  |
| EVE | HUL | A | 2 | 1.46 | 6 | 0.98 | 0.38 | 10 | ± |
| CRY | NFO | H | 3 | 1.41 | 5 | 1.55 | 0.21 | 4 |  |
| NEW | COV | A | 2 | 1.37 | 5 | 1.24 | 0.29 | 8 | ± |
| LIV | MCI | H | 4 | 1.34 | 4 | 1.64 | 0.19 | 3 |  |
| AVL | BRE | H | 3 | 1.27 | 4 | 1.59 | 0.20 | 3 |  |
| COV | NEW | H | 2 | 1.24 | 3 | 1.37 | 0.25 | 6 | ± |
| FUL | IPS | A | 2 | 1.15 | 2 | 1.58 | 0.21 | 4 | ± |
| LEE | ARS | A | 5 | 1.04 | 2 | 1.80 | 0.17 | 2 |  |
| HUL | EVE | H | 3 | 0.98 | 1 | 1.46 | 0.23 | 5 | ± |
| TOT | MUN | A | 4 | 0.93 | 1 | 1.60 | 0.20 | 3 |  |

#### GW7

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| MCI | IPS | H | 2 | 2.08 | 10 | 0.97 | 0.38 | 10 | ± |
| BHA | CRY | H | 3 | 2.00 | 10 | 1.57 | 0.21 | 4 |  |
| BOU | SUN | H | 2 | 1.71 | 9 | 1.16 | 0.31 | 9 |  |
| BRE | LIV | H | 4 | 1.63 | 8 | 1.46 | 0.23 | 5 |  |
| CRY | BHA | A | 3 | 1.57 | 8 | 2.00 | 0.14 | 1 |  |
| LEE | MUN | H | 4 | 1.56 | 7 | 1.41 | 0.24 | 6 |  |
| CHE | EVE | A | 3 | 1.55 | 7 | 1.52 | 0.22 | 5 |  |
| FUL | HUL | H | 2 | 1.55 | 7 | 0.99 | 0.37 | 10 | ± |
| EVE | CHE | H | 4 | 1.52 | 7 | 1.55 | 0.21 | 4 |  |
| LIV | BRE | A | 3 | 1.46 | 6 | 1.63 | 0.20 | 3 |  |
| MUN | LEE | A | 3 | 1.41 | 5 | 1.56 | 0.21 | 4 |  |
| NEW | AVL | H | 3 | 1.40 | 5 | 1.21 | 0.30 | 8 |  |
| ARS | NFO | A | 3 | 1.38 | 5 | 1.13 | 0.32 | 9 |  |
| TOT | COV | H | 2 | 1.36 | 5 | 0.94 | 0.39 | 10 | ± |
| AVL | NEW | A | 3 | 1.21 | 3 | 1.40 | 0.25 | 6 |  |
| SUN | BOU | A | 3 | 1.16 | 2 | 1.71 | 0.18 | 3 |  |
| NFO | ARS | H | 4 | 1.13 | 2 | 1.38 | 0.25 | 6 |  |
| HUL | FUL | A | 3 | 0.99 | 2 | 1.55 | 0.21 | 4 | ± |
| IPS | MCI | A | 5 | 0.97 | 1 | 2.08 | 0.12 | 1 | ± |
| COV | TOT | A | 3 | 0.94 | 1 | 1.36 | 0.26 | 7 | ± |

#### GW8

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| LIV | BHA | H | 2 | 1.91 | 10 | 1.40 | 0.25 | 6 |  |
| MCI | AVL | A | 4 | 1.85 | 10 | 1.01 | 0.36 | 10 |  |
| CHE | TOT | H | 3 | 1.84 | 10 | 1.06 | 0.35 | 9 |  |
| BRE | HUL | A | 2 | 1.80 | 10 | 1.03 | 0.36 | 10 | ± |
| CRY | NEW | H | 2 | 1.78 | 9 | 1.33 | 0.26 | 7 |  |
| ARS | EVE | H | 3 | 1.74 | 9 | 0.89 | 0.41 | 10 |  |
| MUN | BOU | H | 3 | 1.56 | 7 | 1.35 | 0.26 | 7 |  |
| LEE | SUN | A | 3 | 1.48 | 6 | 1.41 | 0.24 | 6 |  |
| SUN | LEE | H | 2 | 1.41 | 5 | 1.48 | 0.23 | 5 |  |
| BHA | LIV | A | 4 | 1.40 | 5 | 1.91 | 0.15 | 1 |  |
| NFO | IPS | A | 2 | 1.37 | 5 | 1.23 | 0.29 | 8 | ± |
| BOU | MUN | A | 4 | 1.35 | 5 | 1.56 | 0.21 | 4 |  |
| FUL | COV | A | 2 | 1.34 | 4 | 1.26 | 0.28 | 8 | ± |
| NEW | CRY | A | 3 | 1.33 | 4 | 1.78 | 0.17 | 2 |  |
| COV | FUL | H | 2 | 1.26 | 4 | 1.34 | 0.26 | 7 | ± |
| IPS | NFO | H | 3 | 1.23 | 3 | 1.37 | 0.25 | 6 | ± |
| TOT | CHE | A | 4 | 1.06 | 2 | 1.84 | 0.16 | 2 |  |
| HUL | BRE | H | 3 | 1.03 | 2 | 1.80 | 0.17 | 2 | ± |
| AVL | MCI | H | 4 | 1.01 | 2 | 1.85 | 0.16 | 2 |  |
| EVE | ARS | A | 5 | 0.89 | 1 | 1.74 | 0.18 | 3 |  |

#### GW9

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| MCI | BHA | H | 2 | 2.27 | 10 | 1.17 | 0.31 | 9 |  |
| CHE | MUN | H | 4 | 1.81 | 10 | 1.55 | 0.21 | 4 |  |
| BOU | LEE | H | 2 | 1.61 | 8 | 1.33 | 0.26 | 7 |  |
| MUN | CHE | A | 4 | 1.55 | 7 | 1.81 | 0.16 | 2 |  |
| BRE | NFO | H | 3 | 1.50 | 6 | 1.32 | 0.27 | 7 |  |
| ARS | LIV | A | 4 | 1.49 | 6 | 1.24 | 0.29 | 8 |  |
| SUN | COV | A | 2 | 1.49 | 6 | 1.18 | 0.31 | 9 | ± |
| IPS | HUL | A | 2 | 1.48 | 6 | 1.07 | 0.34 | 9 | ± |
| AVL | FUL | H | 2 | 1.42 | 6 | 1.18 | 0.31 | 9 |  |
| CRY | TOT | A | 3 | 1.35 | 5 | 1.32 | 0.27 | 7 |  |
| EVE | NEW | A | 3 | 1.34 | 4 | 1.25 | 0.29 | 8 |  |
| LEE | BOU | A | 3 | 1.33 | 4 | 1.61 | 0.20 | 3 |  |
| NFO | BRE | A | 3 | 1.32 | 4 | 1.50 | 0.22 | 5 |  |
| TOT | CRY | H | 3 | 1.32 | 4 | 1.35 | 0.26 | 7 |  |
| NEW | EVE | H | 3 | 1.25 | 3 | 1.34 | 0.26 | 7 |  |
| LIV | ARS | H | 4 | 1.24 | 3 | 1.49 | 0.23 | 5 |  |
| FUL | AVL | A | 4 | 1.18 | 3 | 1.42 | 0.24 | 6 |  |
| COV | SUN | H | 2 | 1.18 | 3 | 1.49 | 0.23 | 5 | ± |
| BHA | MCI | A | 5 | 1.17 | 3 | 2.27 | 0.10 | 1 |  |
| HUL | IPS | H | 2 | 1.07 | 2 | 1.48 | 0.23 | 5 | ± |

#### GW10

| Club | Opp | V | FDR | λ_att | att | λ_def | P(CS) | def | ± |
|---|---|:-:|---:|---:|---:|---:|---:|---:|:-:|
| ARS | HUL | H | 2 | 2.21 | 10 | 0.65 | 0.52 | 10 | ± |
| MUN | AVL | H | 3 | 1.76 | 9 | 1.05 | 0.35 | 9 |  |
| CHE | SUN | A | 3 | 1.71 | 9 | 1.55 | 0.21 | 4 |  |
| LIV | CRY | A | 3 | 1.71 | 9 | 1.53 | 0.22 | 5 |  |
| BHA | BRE | H | 3 | 1.71 | 9 | 1.68 | 0.19 | 3 |  |
| EVE | COV | H | 2 | 1.69 | 9 | 0.92 | 0.40 | 10 | ± |
| BRE | BHA | A | 3 | 1.68 | 9 | 1.71 | 0.18 | 3 |  |
| LEE | TOT | H | 3 | 1.59 | 8 | 0.96 | 0.38 | 10 |  |
| SUN | CHE | H | 4 | 1.55 | 7 | 1.71 | 0.18 | 3 |  |
| CRY | LIV | H | 4 | 1.53 | 7 | 1.71 | 0.18 | 3 |  |
| MCI | NFO | A | 3 | 1.51 | 6 | 1.21 | 0.30 | 8 |  |
| BOU | IPS | A | 2 | 1.46 | 6 | 1.33 | 0.26 | 7 | ± |
| FUL | NEW | H | 2 | 1.42 | 6 | 1.27 | 0.28 | 8 |  |
| IPS | BOU | H | 3 | 1.33 | 4 | 1.46 | 0.23 | 5 | ± |
| NEW | FUL | A | 3 | 1.27 | 4 | 1.42 | 0.24 | 6 |  |
| NFO | MCI | H | 4 | 1.21 | 3 | 1.51 | 0.22 | 5 |  |
| AVL | MUN | A | 4 | 1.05 | 2 | 1.76 | 0.17 | 2 |  |
| TOT | LEE | A | 3 | 0.96 | 1 | 1.59 | 0.20 | 3 |  |
| COV | EVE | A | 3 | 0.92 | 1 | 1.69 | 0.18 | 3 | ± |
| HUL | ARS | A | 5 | 0.65 | 1 | 2.21 | 0.11 | 1 | ± |
## Top fixture swings

Halves of the window compared: GW5–7 against GW8–10.

| # | Club | Swing | Detail |
|---:|---|---|---|
| 1 | **SUN** | attack **+0.71** Σλ_att, defence **+0.21** ΣP(CS) — largest combined improvement | MCI(A) BHA(H) BOU(A) → **LEE(H) COV(A) CHE(H)**. Sunderland's first half contains the worst attacking row any club faces (MCI away, λ_att 0.97). From GW8 they have three rows at 1.41 or better. A GW8 buy, not a GW5 one — and the GW9 COV(A) row is banded. |
| 2 | **LIV** | attack **+0.69**, defence **+0.10** | BOU(A) MCI(H) BRE(A) → **BHA(H) ARS(H) CRY(A)**. The largest attacking improvement, and it is band-free on all six rows. BHA(H) at 1.91 is Liverpool's best row of the window and lands in GW8, against the league's 20th defensive rating. |
| 3 | **NFO** | attack **−0.63**, defence **−0.19** — largest attacking decline | COV(H) CRY(A) ARS(H) → IPS(A) BRE(A) MCI(H). Forest rank 5th on the defensive ticker, but the strength is entirely GW5 (COV(H) 0.43, banded) and the second half holds no row above 0.29. Their two best rows on either axis are the two banded ones. |
| 4 | **NEW** | defence **−0.30**, attack **−0.51** — worst combined decline | HUL(H) COV(A) AVL(H) → CRY(A) EVE(H) FUL(A). Newcastle sit 6th on the defensive ticker on a first half in which **two of three fixtures are banded**. Strip the band-dependent rows and the ticker is ordinary. FPL's FDR ranks them 2nd-easiest; the model ranks them 13th on attack. |
| 5 | **ARS** | attack **+0.48**, defence **+0.27** — largest defensive improvement | BHA(A) LEE(H) NFO(A) → EVE(H) LIV(A) **HUL(H)**. Arsenal are the only club improving materially on both axes, but the improvement is concentrated in GW10 v Hull — their best attacking *and* best defensive row of the window, and banded on both counts. Per C4's residual, that clean sheet may not be a selected player's largest defensive term. |

Also worth naming: **BHA −0.52 attack / −0.14 defence** (ARS(H) SUN(A) CRY(H) →
LIV(A) MCI(A) BRE(H)) — already 20th defensively, and the second half is the
harder one; **TOT −0.31 defence**, the steepest defensive decline, which leaves
Spurs' one strong row (COV(H) 0.39, banded) in GW7; **CHE +0.40 attack**, whose
better half is the later one despite the rating falling.

### Multi-GW runs

Top third = λ_att ≥ 1.55 / P(CS) ≥ 0.27 across the window's 120 rows.
Consecutive runs only.

| Run | Club | Fixtures |
|---|---|---|
| Attack, top third, **all six** | **CHE** | BRE(A) 1.63, BOU(H) 1.78, EVE(A) 1.55, TOT(H) 1.84, MUN(H) 1.81, SUN(A) 1.71 — the only band-free six-row attacking run in the file |
| Attack, top third, GW5–9 | **MCI** | SUN(H) 2.10, LIV(A) 1.64, IPS(H) 2.08 ±, AVL(A) 1.85, BHA(H) 2.27 — breaks only at GW10 (NFO away, 1.51) |
| Attack, top third, GW5–8 | **BRE** | CHE(H) 1.87, AVL(A) 1.59, LIV(H) 1.63, HUL(A) 1.80 ± |
| Attack, top third, GW8–10 | **MUN** | BOU(H) 1.56, CHE(A) 1.55, AVL(H) 1.76 |
| Defence, top third, **all six** | **ARS** | every row P(CS) ≥ 0.28; the highest (HUL(H) 0.52) is banded |
| Defence, top third, GW7–10 | **MCI** | IPS(H) 0.38 ±, AVL(A) 0.36, BHA(H) 0.31, NFO(A) 0.30 |
| Defence, top third, GW5–7 | **NEW** | HUL(H) 0.38 ±, COV(A) 0.29 ±, AVL(H) 0.30 — two of three banded |
| Defence, bottom third, GW5–10 | **BHA**, **CRY**, **SUN**, **HUL** | BHA 6 of 6 rows at or below P(CS) 0.21; CRY, SUN and HUL 4 of 6 each |
| Attack, bottom third, GW5–10 | **HUL**, **COV** | 6 of 6 rows each at or below λ_att 1.32; no Hull row above 1.07 |

Arsenal own the only six-gameweek defensive run and Chelsea the only band-free
six-gameweek attacking one. City hold a five-row attacking run and a four-row
defensive one that do not overlap.

## FPL FDR vs this model

FDR is the mean of `team_h_difficulty` / `team_a_difficulty` over the six rows.
Rank 1 = easiest ticker. Disagreements of ≥ 8 places are bolded.

| Club | mean FDR | FDR rank | model ATT rank | model CS rank | FDR−ATT | FDR−CS |
|---|---:|---:|---:|---:|---:|---:|
| COV | 2.50 | 1 | 19 | 15 | **-18** | **-14** |
| NEW | 2.67 | 2 | 13 | 6 | **-11** | -4 |
| FUL | 2.67 | 3 | 15 | 7 | **-12** | -4 |
| MCI | 2.83 | 4 | 1 | 2 | +3 | +2 |
| ARS | 2.83 | 5 | 2 | 1 | +3 | +4 |
| NFO | 3.00 | 6 | 11 | 5 | -5 | +1 |
| BOU | 3.00 | 7 | 6 | 12 | +1 | -5 |
| EVE | 3.00 | 8 | 12 | 3 | -4 | +5 |
| CRY | 3.00 | 9 | 9 | 18 | +0 | **-9** |
| IPS | 3.00 | 10 | 16 | 10 | -6 | +0 |
| SUN | 3.00 | 11 | 14 | 17 | -3 | -6 |
| CHE | 3.17 | 12 | 3 | 14 | **+9** | -2 |
| MUN | 3.17 | 13 | 5 | 4 | **+8** | **+9** |
| LIV | 3.17 | 14 | 8 | 16 | +6 | -2 |
| TOT | 3.17 | 15 | 18 | 8 | -3 | +7 |
| AVL | 3.17 | 16 | 17 | 13 | -1 | +3 |
| HUL | 3.17 | 17 | 20 | 19 | -3 | -2 |
| BRE | 3.33 | 18 | 4 | 9 | **+14** | **+9** |
| LEE | 3.50 | 19 | 10 | 11 | **+9** | **+8** |
| BHA | 3.67 | 20 | 7 | 20 | **+13** | +0 |

**Where FDR is most wrong this window:**

- **COV (FDR 1st, model 19th attack, 15th defence)** — the largest disagreement
  in the file for the second cycle running, and it has widened on the defensive
  side (−9 → −14). FDR reads Coventry's opponents as soft; the model reads
  Coventry's own attack as second-worst and their defence as freshly downgraded
  (2.80 xG conceded in round 4). Do not buy Coventry assets off the FDR ticker.
- **BRE (FDR 18th, model 4th attack)** — FDR's worst miss in the other
  direction, repeated from GW4. Brentford's fixtures *look* hard; their
  attacking rating carries them anyway.
- **BHA (FDR 20th, model 7th attack, 20th defence)** — the most actionable
  split in the file. FDR's hardest ticker is genuinely hard **for defenders**
  and genuinely soft for attackers. Buy Brighton's attack, never their defence.
- **FUL (FDR 3rd) and NEW (FDR 2nd)** — the two clubs FDR most over-rates.
  Both rank 13th–15th on the model's attacking ticker, and both lean on banded
  fixtures for their defensive numbers.
- **HUL (FDR 17th, model 20th attack, 19th defence)** — FDR has finally moved
  Hull down, and now broadly agrees. Every Hull asset remains a trap.
- **CRY (FDR 9th, model 18th defence, −9)** — Palace's defensive rating has
  risen 0.95 → 1.06 → 1.15 across three cycles on consecutive ceiling-clipped
  rounds. FDR has not registered it.

The model and FDR agree closely on **ARS** and **MCI** (both top-5 on all three
rankings) — the two clubs where reputation and conceded xG point the same way.

## Blank and double gameweeks

**None in GW5–GW10.** All 20 clubs play exactly once in each of the six
gameweeks; the window contains 60 fixtures and 120 club-rows, and no fixture in
the snapshot carries a null `event`.

The first structural disruption is not visible in this window. Nothing here
feeds a Bench Boost or Free Hit case on fixture count.

## C5 — the Triple Captain gate

C5 binds A2 and A4: a Triple Captain must be justified on the captain's own
**fixture-independent** EP, and must not require a promoted club's defensive
rating to clear. GW2 earmarked GW5; GW4 moved the earmark to GW9 on a +0.13
λ_att band-free edge. City's window is the relevant one:

| GW | Fixture | λ_att | P(CS) | Banded? | Δ vs GW4's read |
|---:|---|---:|---:|:-:|---|
| 5 | SUN (H) | 2.10 | 0.38 | no | 2.15 → 2.10 |
| 6 | LIV (A) | 1.64 | 0.26 | no | 1.77 → 1.64 |
| 7 | IPS (H) | **2.08** | 0.38 | **yes** | 2.32 → 2.08 |
| 8 | AVL (A) | 1.85 | 0.36 | no | 1.73 → 1.85 |
| 9 | BHA (H) | **2.27** | 0.31 | no | 2.28 → 2.27 |
| 10 | NFO (A) | 1.51 | 0.30 | no | new to the window |

Three findings:

1. **GW9 is re-affirmed and its margin widens.** BHA(H) 2.27 against GW5's
   SUN(H) 2.10 is a **+0.17 λ_att** edge, up from +0.13 at GW4, with neither
   row banded. It widened because Sunderland's defensive rating held while
   Brighton's rose again (1.08 → 1.11).
2. **The Brighton caveat GW4 attached is now better supported, not worse.**
   GW4 warned the edge rested on a Brighton defensive rating that had moved a
   long way in two cycles. Round 4 adds a fourth reading, 1.37 xG conceded
   (implied 1.31) — consistent with the rise rather than reversing it. Three of
   Brighton's four defensive rounds now sit above average and they are 20th on
   the defensive ticker.
3. **GW7 stays ineligible and GW5 does not displace GW9.** IPS(H) has fallen
   2.32 → 2.08 and is still banded — C5 forbids it regardless of the
   arithmetic. GW5 is today's deadline and sits 0.17 below GW9 on a rating that
   fell this cycle.

**A2 recommends A4 hold the Triple Captain earmark at GW9.** The edge is small
(+0.17 λ_att ≈ +8% on the attacking term) and this is a *forecast* for
`chip_plan`, explicitly not a commitment; re-test every cycle to GW9. The
fixture-independent half of the test remains A3's and A4's — C5 is not cleared
by anything in this file.

## Uncertainty flags

| Flag | Detail |
|---|---|
| **Split-strength fields still zero** | Fifth GW running. All 20 defence priors are ASSUMPTION-grade, derived from 5-tier `strength_overall`. Current-season weight is now 50–57% of DEFW, which is the only thing making them usable. Re-derive the ticker the moment FPL populates the split fields. |
| **ARS defence — the floor artefact is partly resolved** | Round 4 broke a three-round run of 0.55-floored impDEFW values with a genuine 1.48 (1.80 xG conceded at Sunderland). GW4's "understated, one-directional error" flag is **discharged in direction**: the rating rose 0.62 → 0.72 and remains the league's best by 0.06 over MCI. Three of four readings are still clipped, so the rating is still guard-influenced — but it is no longer a pure floor. |
| **Promoted clubs — band unrelaxed** | COV, HUL and IPS all have 4 played fixtures. Confidence is **not** upgraded: 34 of 120 rows stay banded at ±15% λ_att / ±15pp P(CS), uncertainty stays **HIGH**, and C4's defensive prohibition stands. Round 4 put COV's implied DEFW on the ceiling and HUL's on the floor in the same weekend, which is the volatility the band exists for. Revisit at GW6 (n=5). |
| **Clipping stopped declining** | 56 of 160 implied ratings hit the guard, and round 4's rate (35.0%) is **above** round 3's (32.5%). AVL and NFO carry five clipped values each, TOT four. Every clipped club has a rating pulled toward its prior more than the raw xG warrants, and the affected priors are the ASSUMPTION-grade ones. |
| **BHA attack/defence split is the widest in the file** | 7th on the attacking ticker, 20th on the defensive, with all six defensive rows at or below P(CS) 0.21. A single club rating cannot be read across positions here: Brighton attackers and Brighton defenders point opposite ways. |
| **CHE ticker lead is gone, as GW4 predicted** | GW4 flagged Chelsea's top attacking ranking as a fixture artefact on a falling rating. Round 4 (0.91 xG at home to Hull) confirmed it; they fall to 3rd and their rating has now dropped 1.43 → 1.33 → 1.25 across three cycles. They still hold the only band-free six-row attacking run, so the ticker is real — the rating trend is the risk. |
| **LIV attack downgrade arrived on schedule** | GW4 forecast a material downgrade if round 4 was another sub-1.0 xG round. It was 1.29 — above that threshold — so the downgrade is mild (1.15 → 1.11). Four rounds: 3.01, 1.74, 0.69, 1.29. The rating is still 59% prior; the fixture swing (+0.69, 2nd-largest) is the reason to hold Liverpool assets, not the rating. |
| **`base_lambda` — the GW3 over-shoot is decaying** | GW3 flagged 1.54/1.33 (2.87 goals per match) as ~12% low against observed league xG of 3.27/match over rounds 1–2, and scheduled a re-test at GW6 (n≈60). The series is now **3.13 / 3.41 / 2.85 / 2.67**, so four rounds give 3.02/match — **+5.1%**, with rounds 3 and 4 *below* the base. The base is left untouched, as the schedule requires; the GW6 re-test should read the full series, not the rounds 1–2 figure that prompted it. |
| **No cup/congestion adjustment** | European and domestic-cup fixtures are not modelled — no artifact in the snapshot lists them. Which clubs are in Europe is an **ASSUMPTION** and is deliberately not enumerated here; the rating carries no rotation term either way. The player-analyst applies rotation; the ticker does not. |
| **`played` and `points` are zero in bootstrap** | All 20 clubs report `played: 0`, `points: 0` while `position` carries what looks like a live table. No rating in this file reads those fields — ratings come from xG — but nothing downstream should trust them either. |

## Handoff to downstream agents

- **A3 (player-analyst)**: consume `lambda_att` and `p_cs` from
  `data/analysis/gw5/fixtures.json`. The 1–10 deciles are presentation only.
  Rotation and the 60-minute requirement are yours — P(CS) excludes both.
- **A4 (squad-optimizer)**: MCI top the attacking ticker and ARS the defensive
  one, and they are the only two clubs FDR and the model both rank top-5.
  Brighton's attack is the largest FDR mispricing available; Brighton's defence
  is the worst in the file. C5: **hold the Triple Captain earmark at GW9**
  (+0.17 λ_att band-free over GW5); GW7 remains ineligible.
- **C4 residual, binding**: no selected player may take his single largest
  **defensive** EP term from a fixture against COV, HUL or IPS. The eleven rows
  that trip it are tabulated under C12 above — ARS v HUL(H) in GW10 is the
  window's best defensive row and the one most likely to breach it.
