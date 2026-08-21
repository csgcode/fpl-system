# GW1 — 6-Gameweek Fixture Ticker (GW1–GW6)

Season 2026/27 | GW1 deadline 2026-08-21T17:30:00Z | snapshot `data/raw/gw1/`

Downstream agents consume **λ_att** and **P(CS)** only. The 1–10 attack/defence
scores are presentation deciles of the respective λ across the 120 club-fixtures
in this window — never use them as inputs.

## Data-quality warning — read before using these numbers

`bootstrap.json` ships **all four split-strength fields at zero** for all 20 clubs:
`strength_attack_home`, `strength_attack_away`, `strength_defence_home`,
`strength_defence_away` = 0, and `strength` = null. FPL has not populated them
pre-season. The intended primary prior for both attack and defence is therefore
**unavailable at GW1**.

Substitutes used, in order:

| Rank | Source | Applied to | Status |
|---|---|---|---|
| 1 | `strength_overall_home/away` (1–5, mean of the pair) | attack + defence | available, but only **5 distinct tiers** for 20 clubs |
| 2 | prior-season squad xG normalised per team-match | attack | available for 17 clubs |
| 3 | prior-season GK+DEF xGC per 90 | defence | **ASSUMPTION-grade** — contaminated by squad turnover, weight capped at 0.35 |
| 4 | differentiated promoted-club estimates | attack + defence | **ASSUMPTION** — 3 clubs |

Consequence: **defensive resolution in mid-table is poor.** Eleven clubs land
inside DEFW 0.95–1.03, which is an artefact of the 5-level tier prior, not a
finding. Treat mid-table P(CS) differences under ~4pp as noise. Attack
resolution is materially better (real per-90 xG for 17 clubs).

Re-run this analysis once FPL populates the split-strength fields (typically
after GW1–2) — every defensive number here should be expected to move.

## Model

```
lambda_att(i vs j, home) = 1.54 * ATT_i * DEFW_j
lambda_att(i vs j, away) = 1.33 * ATT_i * DEFW_j
lambda_def(i)            = lambda_att(j)   # opponent-symmetric
P(CS)_i                  = exp(-lambda_def_i)
```

- `1.54 / 1.33` — PL long-run goals per team per match, home / away (2.87 total).
- `ATT_i`, `DEFW_j` — multiplicative indices centred on the 20-club mean = 1.00.
  `DEFW > 1` = leakier than average.
- Tier→rating regressions fitted over the 17 non-promoted clubs:
  `xG/match = 0.297*tier + 0.516`, `xGC/match = -0.174*tier + 1.902`.
- Data weight scales with prior-season minute coverage of the *current* squad
  (`cov = squad prior minutes / 37,620`), capped at 0.65 for attack and 0.35 for
  defence. Low coverage = a squad rebuilt with players who have no PL record,
  so the rating shrinks toward the tier prior.

**P(CS) is Poisson P(0 goals conceded).** It excludes the FPL 60-minute
requirement and rotation risk — the player-analyst applies those.

### Prior/current blend schedule

GW1 is **100% prior / 0% current** — no 2026/27 match has been played, so no
current-season component exists to blend. Schedule for later cycles: ~70/30 by
GW3, prior weight held at ≥20% through GW10. Promoted clubs may converge faster
(their prior is the weakest input here, so current data should displace it
quickly — target ≥50% current weight by GW4 for COV/HUL/IPS).

## Team ratings

| Club | Tier | prior xG/match | prior xGC/match* | cov | ATT | DEFW | ATT weights | DEFW weights |
|---|---|---|---|---|---|---|---|---|
| Man City (MCI) | 4.5 | 1.99 | 1.17 | 1.00 | 1.39 | 0.80 | 0.65 data + 0.35 tier | 0.35 data* + 0.65 tier |
| Chelsea (CHE) | 4.0 | 2.03 | 1.39 | 1.02 | 1.37 | 0.90 | 0.65 data + 0.35 tier | 0.35 data* + 0.65 tier |
| Arsenal (ARS) | 4.5 | 1.74 | 0.73 | 1.02 | 1.28 | 0.70 | 0.65 data + 0.35 tier | 0.35 data* + 0.65 tier |
| Brentford (BRE) | 3.0 | 1.85 | 1.45 | 1.02 | 1.21 | 0.99 | 0.65 data + 0.35 tier | 0.35 data* + 0.65 tier |
| Liverpool (LIV) | 4.0 | 1.61 | 1.21 | 0.82 | 1.18 | 0.85 | 0.63 data + 0.37 tier | 0.28 data* + 0.72 tier |
| Man Utd (MUN) | 4.0 | 1.58 | 1.26 | 1.05 | 1.16 | 0.87 | 0.65 data + 0.35 tier | 0.35 data* + 0.65 tier |
| Crystal Palace (CRY) | 3.0 | 1.69 | 1.37 | 0.88 | 1.14 | 0.97 | 0.65 data + 0.35 tier | 0.32 data* + 0.68 tier |
| Bournemouth (BOU) | 3.0 | 1.68 | 1.47 | 0.79 | 1.13 | 0.99 | 0.61 data + 0.39 tier | 0.28 data* + 0.72 tier |
| Leeds (LEE) | 2.5 | 1.59 | 1.46 | 0.92 | 1.06 | 1.03 | 0.65 data + 0.35 tier | 0.34 data* + 0.66 tier |
| Newcastle (NEW) | 2.5 | 1.48 | 1.35 | 0.74 | 0.99 | 1.01 | 0.57 data + 0.43 tier | 0.34 data* + 0.66 tier |
| Aston Villa (AVL) | 3.5 | 1.26 | 1.42 | 0.83 | 0.98 | 0.95 | 0.63 data + 0.37 tier | 0.35 data* + 0.65 tier |
| Everton (EVE) | 3.0 | 1.26 | 1.48 | 0.92 | 0.94 | 1.00 | 0.65 data + 0.35 tier | 0.35 data* + 0.65 tier |
| Nott'm Forest (NFO) | 3.0 | 1.21 | 1.47 | 0.84 | 0.92 | 1.00 | 0.64 data + 0.36 tier | 0.35 data* + 0.65 tier |
| Brighton (BHA) | 2.5 | 1.26 | 1.33 | 0.86 | 0.90 | 1.00 | 0.65 data + 0.35 tier | 0.35 data* + 0.65 tier |
| Spurs (TOT) | 3.0 | 1.02 | 1.41 | 1.10 | 0.83 | 0.98 | 0.65 data + 0.35 tier | 0.35 data* + 0.65 tier |
| Sunderland (SUN) | 2.5 | 1.03 | 1.40 | 0.89 | 0.79 | 1.02 | 0.65 data + 0.35 tier | 0.35 data* + 0.65 tier |
| Fulham (FUL) | 2.5 | 0.89 | 1.40 | 0.77 | 0.75 | 1.02 | 0.59 data + 0.41 tier | 0.35 data* + 0.65 tier |
| Ipswich Town (IPS) **A** | 2.0 | _0.70_ | _1.89_ | 0.39 | 0.70 | 1.26 | — | — |
| Coventry City (COV) **A** | 2.0 | _1.63_ | — | 0.13 | 0.68 | 1.30 | — | — |
| Hull City (HUL) **A** | 2.0 | _5.35_ | — | 0.03 | 0.62 | 1.36 | — | — |

`*` xGC/match is the contaminated turnover-affected proxy — see the data-quality
warning. `**A**` = ASSUMPTION-sourced rating. _Italic_ prior-season figures are
reported for transparency but were **discarded** from the rating (coverage too low).

Discarded values and why:

| Club | prior xG/match | cov | Verdict |
|---|---|---|---|
| Hull City | 5.35 | 0.03 | 1,279 squad minutes of PL history. Nonsense — 6 goals over a 3% sample annualised. Discarded. |
| Coventry City | 1.63 | 0.13 | 4,825 minutes, no PL minutes at all for any GK or DEF. Discarded. |
| Ipswich Town | 0.70 | 0.39 | 14,571 minutes — the largest promoted sample, and the only one with usable defensive minutes (xGC/match 1.89). Informed the assumption, not used raw. |

## Promoted clubs — differentiated, ASSUMPTION, uncertainty HIGH

FPL assigns Coventry, Hull and Ipswich an **identical** `strength_overall` 2/2 —
one undifferentiated bottom block. Rather than fabricate Championship xG figures,
the three were separated using three independent signals already present in the
snapshot. All three rank them in the **same order**:

| Signal | IPS | COV | HUL |
|---|---|---|---|
| Prior-season PL minute coverage of current squad | 0.39 | 0.13 | 0.03 |
| Mean FPL price per squad player (£m) | 4.70 | 4.67 | 4.46 |
| Summed `selected_by_percent` | 44.2 | 33.6 | 17.5 |
| Players with no PL history | 6 | 10 | 9 |
| **Assumed xG/match** | **0.98** | **0.95** | **0.86** |
| **Assumed xGC/match** | **1.78** | **1.84** | **1.92** |

The spread is deliberately narrow (ATT 0.62–0.70, DEFW 1.26–1.36) because the
evidence separating them is weak. Do not read the IPS-over-HUL ordering as
confident — a single result reverses it. FPL price-setting encodes editorial
expectation, which is a real signal but a soft one.

## 6-GW ticker — best attacking (ranked by Σ λ_att)

| # | Club | Σ λ_att | λ/GW | mean att score | Fixtures GW1→6 |
|---|---|---|---|---|---|
| 1 | MCI | 12.06 | 2.01 | 8.8 | BOU(H) CRY(a) COV(H) MUN(a) SUN(H) LIV(a) |
| 2 | CHE | 12.01 | 2.00 | 8.7 | FUL(a) BHA(H) ARS(a) HUL(H) BRE(a) BOU(H) |
| 3 | ARS | 11.39 | 1.90 | 8.7 | COV(H) AVL(a) CHE(H) SUN(a) BHA(a) LEE(H) |
| 4 | MUN | 10.66 | 1.78 | 8.0 | HUL(a) IPS(H) EVE(a) MCI(H) FUL(a) TOT(H) |
| 5 | LIV | 10.22 | 1.70 | 7.8 | NEW(a) NFO(H) IPS(a) FUL(H) BOU(a) MCI(H) |
| 6 | BRE | 10.20 | 1.70 | 7.8 | TOT(H) LEE(a) SUN(H) BOU(a) CHE(H) AVL(a) |
| 7 | CRY | 9.99 | 1.67 | 7.2 | EVE(a) MCI(H) FUL(a) IPS(H) LEE(a) NFO(H) |
| 8 | NEW | 9.25 | 1.54 | 6.5 | LIV(H) TOT(a) BOU(H) LEE(a) HUL(H) COV(a) |
| 9 | BOU | 8.99 | 1.50 | 6.0 | MCI(a) EVE(H) NEW(a) BRE(H) LIV(H) CHE(a) |
| 10 | EVE | 8.65 | 1.44 | 5.7 | CRY(H) BOU(a) MUN(H) TOT(a) IPS(H) HUL(a) |
| 11 | LEE | 8.63 | 1.44 | 5.8 | NFO(a) BRE(H) BHA(a) NEW(H) CRY(H) ARS(a) |
| 12 | AVL | 8.40 | 1.40 | 5.3 | BHA(a) ARS(H) HUL(a) NFO(H) TOT(a) BRE(H) |
| 13 | NFO | 8.07 | 1.34 | 4.7 | LEE(H) LIV(a) TOT(H) AVL(a) COV(H) CRY(a) |
| 14 | BHA | 7.58 | 1.26 | 4.5 | AVL(H) CHE(a) LEE(H) COV(a) ARS(H) SUN(a) |
| 15 | TOT | 6.90 | 1.15 | 3.3 | BRE(a) NEW(H) NFO(a) EVE(H) AVL(H) MUN(a) |
| 16 | SUN | 6.55 | 1.09 | 2.8 | IPS(a) FUL(H) BRE(a) ARS(H) MCI(a) BHA(H) |
| 17 | FUL | 6.24 | 1.04 | 2.3 | CHE(H) SUN(a) CRY(H) LIV(a) MUN(H) IPS(a) |
| 18 | COV | 5.79 | 0.96 | 2.5 | ARS(a) HUL(H) MCI(a) BHA(H) NFO(a) NEW(H) |
| 19 | IPS | 5.78 | 0.96 | 2.0 | SUN(H) MUN(a) LIV(H) CRY(a) EVE(a) FUL(H) |
| 20 | HUL | 5.29 | 0.88 | 1.5 | MUN(H) COV(a) AVL(H) CHE(a) NEW(a) EVE(H) |

## 6-GW ticker — best defensive (ranked by Σ P(CS))

| # | Club | Σ P(CS) | mean P(CS) | mean def score | Fixtures GW1→6 |
|---|---|---|---|---|---|
| 1 | ARS | 2.35 | 39% | 9.0 | COV(H) AVL(a) CHE(H) SUN(a) BHA(a) LEE(H) |
| 2 | MUN | 2.13 | 35% | 8.2 | HUL(a) IPS(H) EVE(a) MCI(H) FUL(a) TOT(H) |
| 3 | MCI | 1.93 | 32% | 7.3 | BOU(H) CRY(a) COV(H) MUN(a) SUN(H) LIV(a) |
| 4 | LIV | 1.89 | 31% | 7.2 | NEW(a) NFO(H) IPS(a) FUL(H) BOU(a) MCI(H) |
| 5 | CHE | 1.80 | 30% | 6.3 | FUL(a) BHA(H) ARS(a) HUL(H) BRE(a) BOU(H) |
| 6 | AVL | 1.71 | 29% | 6.7 | BHA(a) ARS(H) HUL(a) NFO(H) TOT(a) BRE(H) |
| 7 | NEW | 1.68 | 28% | 6.2 | LIV(H) TOT(a) BOU(H) LEE(a) HUL(H) COV(a) |
| 8 | EVE | 1.67 | 28% | 6.2 | CRY(H) BOU(a) MUN(H) TOT(a) IPS(H) HUL(a) |
| 9 | CRY | 1.65 | 28% | 6.3 | EVE(a) MCI(H) FUL(a) IPS(H) LEE(a) NFO(H) |
| 10 | NFO | 1.54 | 26% | 5.7 | LEE(H) LIV(a) TOT(H) AVL(a) COV(H) CRY(a) |
| 11 | BHA | 1.46 | 24% | 5.2 | AVL(H) CHE(a) LEE(H) COV(a) ARS(H) SUN(a) |
| 12 | BRE | 1.45 | 24% | 5.0 | TOT(H) LEE(a) SUN(H) BOU(a) CHE(H) AVL(a) |
| 13 | SUN | 1.43 | 24% | 5.0 | IPS(a) FUL(H) BRE(a) ARS(H) MCI(a) BHA(H) |
| 14 | TOT | 1.43 | 24% | 5.2 | BRE(a) NEW(H) NFO(a) EVE(H) AVL(H) MUN(a) |
| 15 | FUL | 1.35 | 23% | 4.5 | CHE(H) SUN(a) CRY(H) LIV(a) MUN(H) IPS(a) |
| 16 | LEE | 1.25 | 21% | 4.0 | NFO(a) BRE(H) BHA(a) NEW(H) CRY(H) ARS(a) |
| 17 | BOU | 1.16 | 19% | 3.7 | MCI(a) EVE(H) NEW(a) BRE(H) LIV(H) CHE(a) |
| 18 | IPS | 1.07 | 18% | 3.2 | SUN(H) MUN(a) LIV(H) CRY(a) EVE(a) FUL(H) |
| 19 | COV | 1.03 | 17% | 3.2 | ARS(a) HUL(H) MCI(a) BHA(H) NFO(a) NEW(H) |
| 20 | HUL | 0.90 | 15% | 2.2 | MUN(H) COV(a) AVL(H) CHE(a) NEW(a) EVE(H) |

## Per club-fixture detail — GW1–GW6

Home/away adjusted. `att` / `def` are presentation deciles only.

| Club | GW | Opp | H/A | FPL FDR | λ_att | λ_def | P(CS) | att | def |
|---|---|---|---|---|---|---|---|---|---|
| ARS | 1 | COV | H | 2 | 2.56 | 0.63 | 53% | 10 | 10 |
| ARS | 2 | AVL | A | 4 | 1.60 | 1.05 | 35% | 7 | 9 |
| ARS | 3 | CHE | H | 4 | 1.77 | 1.27 | 28% | 9 | 7 |
| ARS | 4 | SUN | A | 3 | 1.73 | 0.85 | 43% | 8 | 10 |
| ARS | 5 | BHA | A | 3 | 1.70 | 0.97 | 38% | 8 | 9 |
| ARS | 6 | LEE | H | 2 | 2.03 | 0.98 | 38% | 10 | 9 |
| AVL | 1 | BHA | A | 3 | 1.30 | 1.31 | 27% | 5 | 6 |
| AVL | 2 | ARS | H | 4 | 1.05 | 1.60 | 20% | 2 | 4 |
| AVL | 3 | HUL | A | 2 | 1.77 | 0.90 | 41% | 9 | 10 |
| AVL | 4 | NFO | H | 3 | 1.50 | 1.15 | 32% | 6 | 8 |
| AVL | 5 | TOT | A | 3 | 1.28 | 1.20 | 30% | 4 | 7 |
| AVL | 6 | BRE | H | 3 | 1.50 | 1.52 | 22% | 6 | 5 |
| BHA | 1 | AVL | H | 3 | 1.31 | 1.30 | 27% | 5 | 6 |
| BHA | 2 | CHE | A | 4 | 1.08 | 2.12 | 12% | 3 | 1 |
| BHA | 3 | LEE | H | 2 | 1.44 | 1.41 | 24% | 6 | 6 |
| BHA | 4 | COV | A | 2 | 1.56 | 1.05 | 35% | 7 | 8 |
| BHA | 5 | ARS | H | 4 | 0.97 | 1.70 | 18% | 2 | 3 |
| BHA | 6 | SUN | A | 3 | 1.22 | 1.23 | 29% | 4 | 7 |
| BOU | 1 | MCI | A | 5 | 1.20 | 2.12 | 12% | 3 | 1 |
| BOU | 2 | EVE | H | 3 | 1.74 | 1.24 | 29% | 8 | 7 |
| BOU | 3 | NEW | A | 3 | 1.51 | 1.51 | 22% | 6 | 5 |
| BOU | 4 | BRE | H | 3 | 1.72 | 1.60 | 20% | 8 | 4 |
| BOU | 5 | LIV | H | 4 | 1.48 | 1.55 | 21% | 6 | 4 |
| BOU | 6 | CHE | A | 4 | 1.34 | 2.10 | 12% | 5 | 1 |
| BRE | 1 | TOT | H | 3 | 1.83 | 1.09 | 34% | 9 | 8 |
| BRE | 2 | LEE | A | 3 | 1.67 | 1.62 | 20% | 8 | 3 |
| BRE | 3 | SUN | H | 2 | 1.90 | 1.05 | 35% | 9 | 9 |
| BRE | 4 | BOU | A | 3 | 1.60 | 1.72 | 18% | 7 | 3 |
| BRE | 5 | CHE | H | 4 | 1.68 | 1.81 | 16% | 8 | 2 |
| BRE | 6 | AVL | A | 4 | 1.52 | 1.50 | 22% | 6 | 5 |
| CHE | 1 | FUL | A | 3 | 1.86 | 1.03 | 36% | 9 | 9 |
| CHE | 2 | BHA | H | 2 | 2.12 | 1.08 | 34% | 10 | 8 |
| CHE | 3 | ARS | A | 5 | 1.27 | 1.77 | 17% | 4 | 2 |
| CHE | 4 | HUL | H | 2 | 2.86 | 0.74 | 48% | 10 | 10 |
| CHE | 5 | BRE | A | 3 | 1.81 | 1.68 | 19% | 9 | 3 |
| CHE | 6 | BOU | H | 3 | 2.10 | 1.34 | 26% | 10 | 6 |
| COV | 1 | ARS | A | 5 | 0.63 | 2.56 | 8% | 1 | 1 |
| COV | 2 | HUL | H | 2 | 1.42 | 1.07 | 34% | 6 | 8 |
| COV | 3 | MCI | A | 5 | 0.73 | 2.78 | 6% | 1 | 1 |
| COV | 4 | BHA | H | 2 | 1.05 | 1.56 | 21% | 3 | 4 |
| COV | 5 | NFO | A | 3 | 0.90 | 1.84 | 16% | 1 | 2 |
| COV | 6 | NEW | H | 2 | 1.06 | 1.71 | 18% | 3 | 3 |
| CRY | 1 | EVE | A | 3 | 1.52 | 1.41 | 24% | 6 | 6 |
| CRY | 2 | MCI | H | 4 | 1.41 | 1.80 | 17% | 5 | 2 |
| CRY | 3 | FUL | A | 3 | 1.54 | 1.12 | 33% | 7 | 8 |
| CRY | 4 | IPS | H | 2 | 2.21 | 0.91 | 40% | 10 | 10 |
| CRY | 5 | LEE | A | 3 | 1.57 | 1.58 | 21% | 7 | 4 |
| CRY | 6 | NFO | H | 3 | 1.75 | 1.19 | 31% | 8 | 8 |
| EVE | 1 | CRY | H | 3 | 1.41 | 1.52 | 22% | 5 | 5 |
| EVE | 2 | BOU | A | 3 | 1.24 | 1.74 | 18% | 4 | 3 |
| EVE | 3 | MUN | H | 4 | 1.25 | 1.55 | 21% | 4 | 4 |
| EVE | 4 | TOT | A | 3 | 1.23 | 1.27 | 28% | 4 | 7 |
| EVE | 5 | IPS | H | 2 | 1.82 | 0.93 | 39% | 9 | 9 |
| EVE | 6 | HUL | A | 2 | 1.70 | 0.95 | 39% | 8 | 9 |
| FUL | 1 | CHE | H | 4 | 1.03 | 1.86 | 16% | 2 | 2 |
| FUL | 2 | SUN | A | 3 | 1.01 | 1.25 | 29% | 2 | 7 |
| FUL | 3 | CRY | H | 3 | 1.12 | 1.54 | 21% | 3 | 4 |
| FUL | 4 | LIV | A | 4 | 0.85 | 1.85 | 16% | 1 | 2 |
| FUL | 5 | MUN | H | 4 | 0.99 | 1.57 | 21% | 2 | 4 |
| FUL | 6 | IPS | A | 2 | 1.25 | 1.10 | 33% | 4 | 8 |
| HUL | 1 | MUN | H | 4 | 0.82 | 2.10 | 12% | 1 | 1 |
| HUL | 2 | COV | A | 2 | 1.07 | 1.42 | 24% | 3 | 5 |
| HUL | 3 | AVL | H | 3 | 0.90 | 1.77 | 17% | 1 | 2 |
| HUL | 4 | CHE | A | 4 | 0.74 | 2.86 | 6% | 1 | 1 |
| HUL | 5 | NEW | A | 3 | 0.83 | 2.07 | 13% | 1 | 1 |
| HUL | 6 | EVE | H | 3 | 0.95 | 1.70 | 18% | 2 | 3 |
| IPS | 1 | SUN | H | 2 | 1.10 | 1.33 | 26% | 3 | 6 |
| IPS | 2 | MUN | A | 4 | 0.81 | 2.25 | 11% | 1 | 1 |
| IPS | 3 | LIV | H | 4 | 0.92 | 1.97 | 14% | 2 | 2 |
| IPS | 4 | CRY | A | 3 | 0.91 | 2.21 | 11% | 1 | 1 |
| IPS | 5 | EVE | A | 3 | 0.93 | 1.82 | 16% | 2 | 2 |
| IPS | 6 | FUL | H | 2 | 1.10 | 1.25 | 29% | 3 | 7 |
| LEE | 1 | NFO | A | 3 | 1.40 | 1.46 | 23% | 5 | 5 |
| LEE | 2 | BRE | H | 3 | 1.62 | 1.67 | 19% | 8 | 3 |
| LEE | 3 | BHA | A | 3 | 1.41 | 1.44 | 24% | 5 | 5 |
| LEE | 4 | NEW | H | 2 | 1.64 | 1.36 | 26% | 8 | 6 |
| LEE | 5 | CRY | H | 3 | 1.58 | 1.57 | 21% | 7 | 4 |
| LEE | 6 | ARS | A | 5 | 0.98 | 2.03 | 13% | 2 | 1 |
| LIV | 1 | NEW | A | 3 | 1.58 | 1.30 | 27% | 7 | 6 |
| LIV | 2 | NFO | H | 3 | 1.81 | 1.04 | 35% | 9 | 9 |
| LIV | 3 | IPS | A | 2 | 1.97 | 0.92 | 40% | 9 | 9 |
| LIV | 4 | FUL | H | 2 | 1.85 | 0.85 | 43% | 9 | 10 |
| LIV | 5 | BOU | A | 3 | 1.55 | 1.48 | 23% | 7 | 5 |
| LIV | 6 | MCI | H | 4 | 1.45 | 1.58 | 21% | 6 | 4 |
| MCI | 1 | BOU | H | 3 | 2.12 | 1.20 | 30% | 10 | 8 |
| MCI | 2 | CRY | A | 3 | 1.80 | 1.41 | 24% | 9 | 6 |
| MCI | 3 | COV | H | 2 | 2.78 | 0.73 | 48% | 10 | 10 |
| MCI | 4 | MUN | A | 4 | 1.60 | 1.44 | 24% | 7 | 5 |
| MCI | 5 | SUN | H | 2 | 2.18 | 0.85 | 43% | 10 | 10 |
| MCI | 6 | LIV | A | 4 | 1.58 | 1.45 | 23% | 7 | 5 |
| MUN | 1 | HUL | A | 2 | 2.10 | 0.82 | 44% | 10 | 10 |
| MUN | 2 | IPS | H | 2 | 2.25 | 0.81 | 45% | 10 | 10 |
| MUN | 3 | EVE | A | 3 | 1.55 | 1.25 | 29% | 7 | 7 |
| MUN | 4 | MCI | H | 4 | 1.44 | 1.60 | 20% | 6 | 4 |
| MUN | 5 | FUL | A | 3 | 1.57 | 0.99 | 37% | 7 | 9 |
| MUN | 6 | TOT | H | 3 | 1.76 | 0.95 | 39% | 8 | 9 |
| NEW | 1 | LIV | H | 4 | 1.30 | 1.58 | 21% | 5 | 4 |
| NEW | 2 | TOT | A | 3 | 1.29 | 1.28 | 28% | 5 | 7 |
| NEW | 3 | BOU | H | 3 | 1.51 | 1.51 | 22% | 6 | 5 |
| NEW | 4 | LEE | A | 3 | 1.36 | 1.64 | 19% | 5 | 3 |
| NEW | 5 | HUL | H | 2 | 2.07 | 0.83 | 44% | 10 | 10 |
| NEW | 6 | COV | A | 2 | 1.71 | 1.06 | 35% | 8 | 8 |
| NFO | 1 | LEE | H | 2 | 1.46 | 1.40 | 25% | 6 | 6 |
| NFO | 2 | LIV | A | 4 | 1.04 | 1.81 | 16% | 2 | 2 |
| NFO | 3 | TOT | H | 3 | 1.39 | 1.10 | 33% | 5 | 8 |
| NFO | 4 | AVL | A | 4 | 1.15 | 1.50 | 22% | 3 | 5 |
| NFO | 5 | COV | H | 2 | 1.84 | 0.90 | 41% | 9 | 10 |
| NFO | 6 | CRY | A | 3 | 1.19 | 1.75 | 17% | 3 | 3 |
| SUN | 1 | IPS | A | 2 | 1.33 | 1.10 | 33% | 5 | 8 |
| SUN | 2 | FUL | H | 2 | 1.25 | 1.01 | 36% | 4 | 9 |
| SUN | 3 | BRE | A | 3 | 1.05 | 1.90 | 15% | 2 | 2 |
| SUN | 4 | ARS | H | 4 | 0.85 | 1.73 | 18% | 1 | 3 |
| SUN | 5 | MCI | A | 5 | 0.85 | 2.18 | 11% | 1 | 1 |
| SUN | 6 | BHA | H | 2 | 1.23 | 1.22 | 29% | 4 | 7 |
| TOT | 1 | BRE | A | 3 | 1.09 | 1.83 | 16% | 3 | 2 |
| TOT | 2 | NEW | H | 2 | 1.28 | 1.29 | 27% | 4 | 6 |
| TOT | 3 | NFO | A | 3 | 1.10 | 1.39 | 25% | 3 | 6 |
| TOT | 4 | EVE | H | 3 | 1.27 | 1.23 | 29% | 4 | 7 |
| TOT | 5 | AVL | H | 3 | 1.20 | 1.28 | 28% | 4 | 7 |
| TOT | 6 | MUN | A | 4 | 0.95 | 1.76 | 17% | 2 | 3 |

## Top fixture swings

Ranked by |Δ mean λ_att| between GW1–3 and GW4–6, with the defensive Δ alongside.

| # | Club | Turns | λ_att GW1-3 → GW4-6 | P(CS) GW1-3 → GW4-6 | Note |
|---|---|---|---|---|---|
| 1 | CHE | **easier from GW4** | 1.75 → 2.26 (+0.51) | 29% → 31% | ARS(a) in GW3 is the only hard fixture in the window. HUL(H) GW4 is the single best attacking fixture in all 120 (λ_att 2.86, P(CS) 48%). Then BOU(H) GW6. Buy Chelsea attack before GW4. |
| 2 | MCI | **harder from GW4** | 2.23 → 1.79 (−0.45) | 34% → 30% | Front-loaded: BOU(H), CRY(a), COV(H) — λ_att 2.12 / 1.80 / 2.78. Then MUN(a) and LIV(a) inside three GWs. Captain window is GW1 and GW3, not GW4–6. |
| 3 | MUN | **harder from GW4** | 1.96 → 1.59 (−0.38) | 39% → 32% (−7pp) | Best opening pair in the league on paper: HUL(a) then IPS(H), P(CS) 44% / 45%. MCI(H) GW4 is the cliff. Defensive assets are a two-GW play unless you intend to hold through. |
| 4 | CRY | **easier from GW4** | 1.49 → 1.84 (+0.35) | 25% → 30% | MCI(H) GW2 is the only real block. IPS(H) GW4 λ_att 2.21. |
| 5 | NEW | **easier from GW4** | 1.37 → 1.71 (+0.35) | 23% → 33% (+9pp) | Worst-to-best swing in defensive terms alongside EVE. Opens LIV(H), TOT(a); closes HUL(H) 44% P(CS) then COV(a) 35%. |

Runner-up worth flagging separately: **EVE has the largest defensive swing in the
window, +15.0pp** (20% → 35% mean P(CS)), turning at GW5 with IPS(H) then HUL(a).
Its attacking swing (+0.28) fell just outside the top five. Everton defenders are
the cheapest route into that run.

### Multi-GW runs (≥3 consecutive GWs in the top/bottom third)

| Club | Easy attacking run | Easy defensive run | Hard defensive run |
|---|---|---|---|
| ARS | **GW1–6 (all six)** | GW4–6 | — |
| MCI | GW1–5 | — | — |
| BRE | GW1–5 | — | — |
| CHE | GW4–6 | — | — |
| LIV | GW2–4 | GW2–4 | — |
| AVL | — | GW3–5 | — |
| HUL | — | — | **GW3–6** |
| IPS | — | — | GW2–5 |
| SUN | — | — | GW3–5 |

Arsenal is the only club with a top-third attacking fixture in **every** GW of the
window while also holding the best defensive rating (DEFW 0.70, mean P(CS) 39%).
That is the strongest single-club signal in this ticker.

## FPL FDR vs this model

Pearson **r = 0.633** across the 120 club-fixtures — directionally aligned, but
FDR loses more than a third of the variance. FDR is reported in the detail table
so downstream agents can see both.

**The systematic disagreement: FDR grades the opponent, not the fixture.** It
ignores the rated club's own quality, so a weak club facing another weak club is
scored as an easy fixture when its actual expected output stays poor. Every one of
the largest disagreements in that direction involves a promoted club:

| Club | GW | Fixture | FDR | Model | λ_att | P(CS) | Reading |
|---|---|---|---|---|---|---|---|
| COV | 6 | NEW (H) | 2 | 4.1 | 1.06 | 18% | FDR's largest single error in the window. Coventry at home is not an easy fixture for Coventry. |
| COV | 4 | BHA (H) | 2 | 3.9 | 1.05 | 21% | Same failure mode. |
| HUL | 2 | COV (a) | 2 | 3.6 | 1.07 | 24% | FDR calls a promoted-vs-promoted game easy for both sides. It is low-scoring, not high-yield. |
| IPS | 1 | SUN (H) | 2 | 3.4 | 1.10 | 26% | Both clubs given FDR 2. Neither is a source of points. |
| IPS | 4 | CRY (a) | 3 | 4.7 | 0.91 | 11% | |
| HUL | 5 | NEW (a) | 3 | 4.7 | 0.83 | 13% | |

**In the other direction, FDR over-punishes the strong clubs' marquee fixtures:**

| Club | GW | Fixture | FDR | Model | λ_att | P(CS) | Reading |
|---|---|---|---|---|---|---|---|
| ARS | 2 | AVL (a) | 4 | 2.0 | 1.60 | 35% | AVL's attack rates 0.98 ATT — below average. Not a fixture to bench Arsenal defenders for. |
| ARS | 3 | CHE (H) | 4 | 2.1 | 1.77 | 28% | Genuinely hard defensively, but Arsenal's attacking output holds up. |
| ARS | 4 | SUN (a) | 3 | 1.6 | 1.73 | 43% | Best Arsenal clean-sheet spot after GW1. FDR 3 understates it badly. |
| MCI | 1 | BOU (H) | 3 | 1.7 | 2.12 | 30% | |
| MCI | 4 | MUN (a) | 4 | 2.6 | 1.60 | 24% | |
| CHE | 1 | FUL (a) | 3 | 1.6 | 1.86 | 36% | FUL is the weakest-attacking club with usable data (ATT 0.75). |

Practical rule for the optimizer: **do not use FDR to bench a strong club's
assets, and do not use FDR to buy a weak club's assets.** Those are the two
regimes where it fails hardest.

## Blank and double gameweeks

**None across the entire season.** All 380 fixtures carry a non-null `event`,
every GW1–38 has exactly 10 matches, and every club has exactly one fixture in
every one of the 38 gameweeks. Verified over the full fixture list, not just the
6-GW window.

Implication for the phase-2 chip agent: **there is no DGW/BGW structure to plan
around in this snapshot.** Bench Boost and Triple Captain have to be timed on
fixture quality alone, not fixture count. Expect this to change — real blanks and
doubles are created later in the season by cup progression and postponements, and
they will appear in `fixtures.json` as clubs are removed from a GW. Re-check this
section every cycle; the first `event: null` fixture is the signal.

## Uncertainty flags

| Flag | Severity | Detail |
|---|---|---|
| **Zeroed split-strength fields** | **HIGH** | `strength_attack_*` and `strength_defence_*` are 0 for all 20 clubs; `strength` is null. The intended primary prior does not exist at GW1. Every rating here is a substitute. |
| **Defensive ratings are ASSUMPTION-grade** | **HIGH** | No artifact provides team xG-against. Defence is 65–72% driven by a 5-level tier prior; the remaining 28–35% is prior-season GK+DEF xGC, which squad turnover contaminates. Eleven clubs sit within DEFW 0.95–1.03 — that compression is a model artefact. Mid-table P(CS) gaps under ~4pp are noise. |
| **Promoted clubs (COV, HUL, IPS)** | **HIGH** | Fully ASSUMPTION-sourced. FPL gives all three an identical 2/2 tier; the separation used here rests on FPL price-setting and manager sentiment, which are soft signals. COV and HUL have **zero** PL minutes for any GK or DEF, so their P(CS) figures have no empirical basis at all. |
| **Squad-turnover contamination** | **MEDIUM** | Prior-season rows are keyed to each player's *current* club, so production earned elsewhere is credited to the new club. Worst-affected (lowest minute coverage, most players with no PL history): NEW 0.74 cov / 4 no-history, FUL 0.77 / 2, BOU 0.79 / 2, LIV 0.82 / 3, AVL 0.83 / 3, CHE 1.02 / 4. Ratings for these clubs were shrunk toward the tier prior in proportion. |
| **Brentford attack rating** | **MEDIUM** | BRE rates ATT 1.21 — 6th in the league, well above its tier 3.0 — on the back of 71.7 prior-season squad xG at full minute coverage. The data is internally consistent, but the gap against FPL's own view is large enough that it should be treated as unconfirmed until GW3. |
| **Spurs attack rating** | **MEDIUM** | TOT rates ATT 0.83, 15th, despite tier 3.0 — on the **highest** minute coverage in the league (1.10). The prior data is unusually well-supported here, so the disagreement with FDR is more likely FDR's error than the model's. |
| **Crystal Palace finishing** | **LOW** | CRY posted 92.4 prior-season xGI against 70 actual G+A — a 22-unit underperformance. λ_att is xG-based and so carries the optimistic view. If the underperformance was a persistent squad trait rather than variance, CRY λ_att is overstated by roughly 15%. |
| **Congested schedule** | **LOW** | No club has a turnaround under 4 days anywhere in GW1–6. Tightest: AVL GW2→3, LEE GW4→5, NEW GW4→5 (4 days each). A 20-day international break splits GW5 (last match 2026-09-20) from GW6 (first match 2026-10-10), so GW6 ratings are the least reliable in the window — injury and fitness news will move materially across that gap. |
| **Cup involvement** | **UNKNOWN** | The FPL API exposes no European or domestic-cup calendar. Rotation risk for clubs in continental competition is **not** modelled anywhere in this ticker. The player-analyst must apply it independently — it is the largest unmodelled factor for MCI, ARS, CHE, LIV, MUN and TOT. |

## Handoff to downstream agents

- Consume **λ_att** and **P(CS)** from the per club-fixture table. Ignore the 1–10 scores.
- **ARS is the standout**: best defence in the league (DEFW 0.70) *and* a top-third attacking fixture in all six GWs. Both ends of the pitch.
- **Front-load MCI and MUN, back-load CHE.** MCI and MUN peak GW1–3; CHE peaks GW4–6 with the best single fixture in the window (HUL(H), λ_att 2.86).
- **EVE and NEW defenders** are the cheap routes into the two largest defensive swings (+15.0pp and +9.2pp), both turning around GW5.
- **Avoid promoted-club assets outright.** COV/HUL/IPS occupy the bottom three of both tickers, and their ratings are the least trustworthy in the file — the downside is real and the upside is unevidenced.
- **SUN GW3–5 and HUL GW3–6** are the hard defensive runs to sell into.
- Treat every defensive number as provisional. Re-run this analysis as soon as FPL populates the split-strength fields.
