# GW3 — 6-Gameweek Fixture Ticker (GW3–GW8)

Window **GW3–GW8**, all 20 clubs, no blanks, no doubles. Ratings rest on
**two** played rounds; the blend has advanced from GW2's 85/15 to roughly
**74/26** on established-club attack.

Downstream agents consume `lambda_att` and `p_cs` from
`data/analysis/gw3/fixtures.json`. The 1–10 attack/defence scores in this file
are presentation-only deciles and must not be read as inputs.

| Headline | Read |
|---|---|
| Best attacking ticker | **MCI** Σλ_att 13.11, then CHE 12.19, BRE 11.49 |
| Best defensive ticker | **ARS** ΣP(CS) 2.41, then MCI 2.40, NFO 1.95 |
| Worst combined | **HUL** (19th attack, 20th defence), **SUN**, **IPS** |
| Largest swing | **LIV** attack falls away after GW5 (−1.24 Σλ_att, halves of the window) |
| Blanks / doubles | none in GW3–GW8 |

## What changed since GW2

### 1. A club-attribution defect in the current-season xG build — found and fixed

Attributing an `element-summary` history row to a club by the player's
**current** bootstrap `team` is wrong for anyone transferred since the round
was played. The row belongs to the club the player turned out for; the
bootstrap field names the club he belongs to now.

The concrete failure: Ndiaye's round-1 row carried a round-1 opponent from his
former club but a bootstrap `team` of MCI, which pushed a foreign
`expected_goals_conceded` of 1.96 into Manchester City's round-1 defensive
figure — against a true value of 0.65. That is a **three-fold** error on the
single most consequential defensive rating in the file.

Club attribution now derives from the row's own `was_home` and
`opponent_team`, resolved against the fixture list for that round. This is
transfer-proof: it uses only facts about the match. Two secondary gaps closed
at the same time:

- **Missing summaries.** 69 players with minutes in rounds 1–2 have no
  `element-summary` file in the snapshot (HUL alone accounts for 11). Their xG
  is now recovered from the `event-live` snapshots. League-wide the recovery is
  1.89 xG across two rounds — small, but it was biasing exactly the clubs whose
  ratings are least certain.
- **xG-against is now opponent-symmetric by construction.** Club *i*'s xG
  conceded is defined as club *j*'s xG created, which is what the model's
  `lambda_def(i) = lambda_att(j)` already assumes. The per-player
  `expected_goals_conceded` field is no longer read at all.

**This does not retrospectively invalidate GW2.** The corrected build
reproduces GW2's published round-1 xG/xGA column to within rounding on all 20
clubs (ARS 1.88/0.21, MCI 2.24/0.65, TOT 0.57/3.91, BHA 3.77/0.30). GW2 got
the right numbers; the guard is what is new, and it matters more each round as
transfer activity accumulates.

### 2. FPL has still not populated the split-strength fields

Third gameweek running: `strength_attack_home/away` and
`strength_defence_home/away` are **0** for all 20 clubs, and `strength` is
`null`. Defence priors therefore still come from `strength_overall_home/away`
— five tiers spread across twenty clubs — and every one of them remains
**ASSUMPTION**-grade. The saving grace is that the current-season component is
now 33–40% of DEFW rather than 20–25%, so the weak prior's share is falling.

### 3. The blend advanced, on the schedule GW2 set

No parameter was retuned. GW2 expressed each prior's worth as `k`
match-equivalents; `k` is held fixed and the match count `n` grew from 1 to 2.

## Corrections applied

### C12 (A2) — the promoted-club band is now two-sided

GW2's retro revises C4. The unified reading is **inflated goal totals in both
directions**, not a one-way defensive discount: GW1 missed defensively (HUL 2-0
MUN, IPS 2-1 SUN against modelled clean sheets), GW2 missed attackingly
(Mbeumo 11 points off 1.76 xG against 4.90 predicted).

Implementation, in three parts:

1. **`band` marks both sides.** Any fixture with COV, HUL or IPS on *either*
   side sets `band: true` on *both* club-rows — **36 of 120 rows**. GW2 marked
   the same set; what changes is what the mark now means.
2. **The band covers `lambda_att` as well as `p_cs`.** A `±` row is a range on
   the attacking estimate too. Read λ_att ±15% and P(CS) ±15pp.
3. **No haircut to the central attacking estimate.** C12's second clause is
   explicit that the band's existence must not shrink it, so every club facing
   promoted opposition carries its full modelled λ_att: MCI 2.42 v COV(H), CHE
   2.78 v HUL(H) — the highest single λ_att in the window — MCI 2.62 v IPS(H),
   BRE 2.11 at HUL. The uncertainty is
   published as a band, never as a discount.

C4's residual prohibition — *never let a promoted-club fixture be the single
largest EP term for a selected player* — **stands for defensive terms only**,
per C12. It no longer binds attacking terms.

### C5 (A2, A4) — the GW3 Triple Captain gate

Active, and re-examined below under its own heading. Short version: the gate is
**clearable at GW3 on the arithmetic**, but GW3 offers no material edge over
the band-free GW5 alternative, so **A2 recommends holding the GW5 earmark**.

### C4 (A2) — superseded

Revised by C12. Its confidence-downgrade instruction is discharged by keeping
promoted-club uncertainty at HIGH with 2 played fixtures each.

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

Each played match yields an opponent- and venue-adjusted implied rating, which
strips out fixture quality:

```
impATT_i  = xG_i  / (base_venue_i  * DEFW_opponent)
impDEFW_i = xGA_i / (base_venue_j  * ATT_opponent)
```

Both adjustments use the **GW1 pure-prior** ratings as a fixed reference frame,
for the whole two-round history. Using the evolving blend instead would make
each round's implied value depend on the order rounds were processed.

Implied values are clipped to **[0.55, 1.80]** before blending — one match's xG
carries a standard deviation near a full goal. **22 of 80** implied ratings hit
the guard this cycle.

Rating = `(k * prior + Σ implied) / (k + n)`, with `n = 2`:

| Rating | Prior source | k | w_prior / w_current (n=2) | was at GW2 |
|---|---|---:|---|---|
| Attack, established | real prior-season squad xG | 5.7 | **74 / 26** | 85 / 15 |
| Defence, established | 5-tier `strength_overall` only | 4.0 | **67 / 33** | 80 / 20 |
| Attack, promoted | ASSUMPTION | 4.0 | **67 / 33** | 80 / 20 |
| Defence, promoted | ASSUMPTION | 3.0 | **60 / 40** | 75 / 25 |

Defence takes more current weight than attack because its **prior is weaker**,
not because its data is better. Promoted clubs converge faster because theirs
is weakest of all — which is C4-compatible: faster convergence off a worthless
prior is not an upgrade in confidence, and the ±15pp band carries the
uncertainty explicitly.

Prior weight stays ≥20% through GW10 on every line (at GW10, n=9: established
attack 39% prior, promoted defence 36%).

## Team ratings — GW3 (two rounds blended)

`Δ GW2` compares `data/analysis/gw2/fixtures.md`. `*` marks an implied value
clipped to [0.55, 1.80] before blending. **A** marks a promoted club.

| Club | GW1 xG | GW2 xG | GW1 xGA | GW2 xGA | impATT r1/r2 | impDEFW r1/r2 | ATT prior | **ATT** | Δ GW2 | DEFW prior | **DEFW** | Δ GW2 |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|
| CHE | 2.23 | 3.04 | 1.38 | 1.46 | 1.64 / 1.97* | 1.19 / 1.22 | 1.37 | **1.43** | +0.03 | 0.90 | **0.97** | +0.03 |
| MCI | 2.24 | 2.22 | 0.65 | 0.68 | 1.47 / 1.72 | 0.43* / 0.39* | 1.39 | **1.41** | +0.02 | 0.80 | **0.70** | -0.05 |
| BRE | 3.91 | 1.67 | 0.57 | 1.46 | 2.59* / 1.22 | 0.52* / 0.89 | 1.21 | **1.26** | -0.03 | 0.99 | **0.88** | -0.02 |
| LIV | 3.01 | 1.74 | 1.58 | 2.30 | 2.24* / 1.13 | 1.04 / 1.88* | 1.18 | **1.22** | -0.04 | 0.85 | **1.01** | +0.13 |
| MUN | 1.82 | 5.15 | 1.08 | 2.06 | 1.01 / 2.65* | 1.13 / 2.21* | 1.16 | **1.19** | +0.06 | 0.87 | **1.04** | +0.14 |
| ARS | 1.88 | 1.04 | 0.21 | 0.34 | 0.94 / 0.82 | 0.23* / 0.23* | 1.28 | **1.15** | -0.07 | 0.70 | **0.63** | -0.04 |
| CRY | 1.97 | 0.68 | 1.12 | 2.22 | 1.48 / 0.55 | 0.77 / 1.20 | 1.14 | **1.08** | -0.10 | 0.97 | **0.95** | +0.02 |
| BOU | 0.65 | 2.19 | 2.24 | 1.87 | 0.61 / 1.42 | 1.05 / 1.50 | 1.13 | **1.07** | +0.03 | 0.99 | **1.05** | +0.05 |
| BHA | 3.77 | 1.46 | 0.30 | 3.04 | 2.58* / 1.22 | 0.23* / 1.44 | 0.90 | **1.03** | +0.00 | 1.00 | **0.97** | +0.06 |
| NFO | 0.65 | 2.30 | 0.47 | 1.74 | 0.41* / 2.03* | 0.33* / 0.96 | 0.92 | **0.96** | +0.10 | 1.00 | **0.89** | -0.02 |
| LEE | 0.47 | 1.46 | 0.65 | 1.67 | 0.35* / 0.96 | 0.46* / 1.04 | 1.06 | **0.96** | -0.02 | 1.03 | **0.93** | -0.01 |
| EVE | 1.12 | 1.87 | 1.97 | 2.19 | 0.75 / 1.42 | 1.30 / 1.26 | 0.94 | **0.95** | +0.04 | 1.00 | **1.06** | +0.01 |
| NEW | 1.58 | 0.72 | 3.01 | 1.13 | 1.21 / 0.55 | 1.92* / 0.88 | 0.99 | **0.94** | -0.07 | 1.01 | **1.09** | -0.07 |
| IPS **A** | 1.79 | 2.06 | 0.67 | 5.15 | 1.14 / 1.78 | 0.64 / 2.88* | 0.70 | **0.93** | +0.15 | 1.26 | **1.21** | +0.11 |
| AVL | 0.30 | 0.34 | 3.77 | 1.04 | 0.23* / 0.32* | 2.72* / 0.61 | 0.98 | **0.85** | -0.06 | 0.95 | **1.01** | -0.10 |
| SUN | 0.67 | 2.03 | 1.79 | 0.94 | 0.40* / 1.29 | 1.66 / 0.94 | 0.79 | **0.80** | +0.05 | 1.02 | **1.08** | -0.07 |
| TOT | 0.57 | 1.13 | 3.91 | 0.72 | 0.43* / 0.73 | 2.10* / 0.55* | 0.83 | **0.76** | -0.02 | 0.98 | **1.02** | -0.12 |
| FUL | 1.38 | 0.94 | 2.23 | 2.03 | 1.00 / 0.69 | 1.22 / 1.67 | 0.75 | **0.76** | -0.03 | 1.02 | **1.13** | +0.07 |
| COV **A** | 0.21 | 1.30 | 1.88 | 0.72 | 0.23* / 0.62 | 0.95 / 0.87 | 0.68 | **0.63** | -0.02 | 1.30 | **1.11** | -0.10 |
| HUL **A** | 1.08 | 0.72 | 1.82 | 1.30 | 0.81 / 0.42* | 1.18 / 1.24 | 0.62 | **0.62** | -0.02 | 1.36 | **1.26** | -0.05 |

### Biggest rating changes vs GW2

| Club | Change | Driver |
|---|---|---|
| **IPS ATT 0.78 → 0.93** (+0.15) | largest move in the file | 1.79 then **2.06** xG, both above rating, the second at Old Trafford. Ipswich is now 14th on attack, not 20th. See the uncertainty flags — this is C12's inflation risk pointing *up*. |
| **MUN DEFW 0.90 → 1.04** (+0.14) | worst defensive downgrade | Conceded 2.06 xG to Ipswich in a match they won 5-2. The scoreline flatters a leaking defence. |
| **LIV DEFW 0.88 → 1.01** (+0.13) | | 1.58 then 2.30 xG conceded — 3.88 across two rounds, 4th-worst. Liverpool's defence is now rated *below* average. |
| **TOT DEFW 1.14 → 1.02** (−0.12) | largest improvement | Conceded 0.72 xG at Newcastle. GW2's downgrade came off a single clipped 2.10 implied; a second match unwound most of it. |
| **IPS DEFW 1.10 → 1.21** (+0.11) | | Conceded **5.15** xG at Manchester United, the worst single figure of either round. Implied 2.88, clipped. |
| **AVL DEFW 1.11 → 1.01** (−0.10) | | Conceded 1.04 xG to Arsenal. Same unwind as Spurs. |
| **COV DEFW 1.21 → 1.11** (−0.10) | | Conceded 0.72 xG to Hull. Two respectable defensive rounds; Coventry's defence is the least-bad thing about them. |
| **CRY ATT 1.18 → 1.08** (−0.10) | | 0.68 xG at home to City. Implied 0.55, floored — Palace's attack may be worse than this rating. |
| **NFO ATT 0.86 → 0.96** (+0.10) | | 2.30 xG against Liverpool, implied 2.03 and clipped. |
| **ARS ATT 1.22 → 1.15** (−0.07) | notable non-move | Second straight round below rating (1.88, then 1.04 at Villa). Arsenal are 6th on attack on a 4.5 strength tier, and the model has now disagreed with FDR on this for three cycles. |
| **MCI DEFW 0.75 → 0.70** (−0.05) | | 0.65 and 0.68 xG conceded — the best two-round defensive record in the league, and the reason City rank 2nd on both tickers. |

**Three of the four largest defensive improvements are GW2 clips unwinding**
(TOT, AVL, COV). That is the clipping guard working as designed: it capped the
single-match over-reaction, and the second match pulled the rating back toward
the prior. Expect less of this from GW4 as `n` grows.

## 6-GW ticker — best attacking (ranked by Σ λ_att, GW3–8)

`±` marks a fixture carrying the two-sided promoted-club band.

| # | Club | Σ λ_att | λ_att/GW | mean att score | mean FDR | Fixtures GW3→8 |
|---:|---|---:|---:|---:|---:|---|
| 1 | MCI | 13.11 | 2.19 | 9.5 | 3.00 | COV(H)± MUN(A) SUN(H) LIV(A) IPS(H)± AVL(A) |
| 2 | CHE | 12.19 | 2.03 | 8.7 | 3.17 | ARS(A) HUL(H)± BRE(A) BOU(H) EVE(A) TOT(H) |
| 3 | BRE | 11.49 | 1.92 | 9.0 | 3.17 | SUN(H) BOU(A) CHE(H) AVL(A) LIV(H) HUL(A)± |
| 4 | LIV | 10.38 | 1.73 | 7.8 | 2.67 | IPS(A)± FUL(H) BOU(A) MCI(H) BRE(A) BHA(H) |
| 5 | MUN | 10.03 | 1.67 | 7.5 | 3.17 | EVE(A) MCI(H) FUL(A) TOT(H) LEE(A) BOU(H) |
| 6 | ARS | 9.73 | 1.62 | 7.3 | 3.00 | CHE(H) SUN(A) BHA(A) LEE(H) NFO(A) EVE(H) |
| 7 | CRY | 9.67 | 1.61 | 7.0 | 2.67 | FUL(A) IPS(H)± LEE(A) NFO(H) BHA(A) NEW(H) |
| 8 | BOU | 9.34 | 1.56 | 6.7 | 3.33 | NEW(A) BRE(H) LIV(H) CHE(A) SUN(H) MUN(A) |
| 9 | NEW | 8.53 | 1.42 | 5.5 | 2.67 | BOU(H) LEE(A) HUL(H)± COV(A)± AVL(H) CRY(A) |
| 10 | EVE | 8.43 | 1.41 | 5.5 | 3.33 | MUN(H) TOT(A) IPS(H)± HUL(A)± CHE(H) ARS(A) |
| 11 | BHA | 8.38 | 1.40 | 5.5 | 3.00 | LEE(H) COV(A)± ARS(H) SUN(A) CRY(H) LIV(A) |
| 12 | NFO | 8.14 | 1.36 | 5.3 | 3.00 | TOT(H) AVL(A) COV(H)± CRY(A) ARS(H) IPS(A)± |
| 13 | LEE | 7.95 | 1.32 | 4.8 | 3.33 | BHA(A) NEW(H) CRY(H) ARS(A) MUN(H) SUN(A) |
| 14 | IPS | 7.70 | 1.28 | 4.3 | 3.33 | LIV(H)± CRY(A)± EVE(A)± FUL(H)± MCI(A)± NFO(H)± |
| 15 | FUL | 7.13 | 1.19 | 3.7 | 2.83 | CRY(H) LIV(A) MUN(H) IPS(A)± HUL(H)± COV(A)± |
| 16 | AVL | 7.01 | 1.17 | 3.3 | 3.00 | HUL(A)± NFO(H) TOT(A) BRE(H) NEW(A) MCI(H) |
| 17 | TOT | 6.67 | 1.11 | 2.8 | 3.17 | NFO(A) EVE(H) AVL(H) MUN(A) COV(H)± CHE(A) |
| 18 | SUN | 5.94 | 0.99 | 2.3 | 3.17 | BRE(A) ARS(H) MCI(A) BHA(H) BOU(A) LEE(H) |
| 19 | HUL | 5.48 | 0.91 | 1.5 | 3.17 | AVL(H)± CHE(A)± NEW(A)± EVE(H)± FUL(A)± BRE(H)± |
| 20 | COV | 5.30 | 0.88 | 1.7 | 2.83 | MCI(A)± BHA(H)± NFO(A)± NEW(H)± TOT(A)± FUL(H)± |

**MCI's ticker is the best in the league on both axes** — 1st on attack, 2nd on
defence — and it is not a soft-fixture artefact: City's two hardest fixtures in
the window (MUN away, LIV away) still produce λ_att 1.95 and 1.89.

**COV and IPS are the trap.** Coventry's mean FDR of 2.83 is 4th-easiest in the
league; their attacking ticker is **20th**. FDR scores the opponent; the model
also scores the club. All twelve of their and Hull's rows are banded.

## 6-GW ticker — best defensive (ranked by Σ P(CS), GW3–8)

| # | Club | Σ P(CS) | P(CS)/GW | Σ λ_def | mean def score | Fixtures GW3→8 |
|---:|---|---:|---:|---:|---:|---|
| 1 | ARS | 2.41 | 0.402 | 5.53 | 9.2 | CHE(H) SUN(A) BHA(A) LEE(H) NFO(A) EVE(H) |
| 2 | MCI | 2.40 | 0.401 | 5.70 | 8.7 | COV(H)± MUN(A) SUN(H) LIV(A) IPS(H)± AVL(A) |
| 3 | NFO | 1.95 | 0.325 | 6.95 | 7.7 | TOT(H) AVL(A) COV(H)± CRY(A) ARS(H) IPS(A)± |
| 4 | BRE | 1.81 | 0.301 | 7.46 | 6.8 | SUN(H) BOU(A) CHE(H) AVL(A) LIV(H) HUL(A)± |
| 5 | CRY | 1.71 | 0.285 | 7.58 | 6.8 | FUL(A) IPS(H)± LEE(A) NFO(H) BHA(A) NEW(H) |
| 6 | CHE | 1.64 | 0.273 | 8.23 | 5.8 | ARS(A) HUL(H)± BRE(A) BOU(H) EVE(A) TOT(H) |
| 7 | NEW | 1.62 | 0.270 | 8.17 | 6.0 | BOU(H) LEE(A) HUL(H)± COV(A)± AVL(H) CRY(A) |
| 8 | BHA | 1.62 | 0.270 | 8.09 | 6.0 | LEE(H) COV(A)± ARS(H) SUN(A) CRY(H) LIV(A) |
| 9 | LEE | 1.55 | 0.259 | 8.20 | 5.8 | BHA(A) NEW(H) CRY(H) ARS(A) MUN(H) SUN(A) |
| 10 | AVL | 1.53 | 0.256 | 8.46 | 5.7 | HUL(A)± NFO(H) TOT(A) BRE(H) NEW(A) MCI(H) |
| 11 | TOT | 1.51 | 0.251 | 8.89 | 5.3 | NFO(A) EVE(H) AVL(H) MUN(A) COV(H)± CHE(A) |
| 12 | MUN | 1.45 | 0.242 | 8.75 | 5.2 | EVE(A) MCI(H) FUL(A) TOT(H) LEE(A) BOU(H) |
| 13 | FUL | 1.40 | 0.234 | 9.20 | 4.7 | CRY(H) LIV(A) MUN(H) IPS(A)± HUL(H)± COV(A)± |
| 14 | EVE | 1.39 | 0.231 | 9.16 | 4.7 | MUN(H) TOT(A) IPS(H)± HUL(A)± CHE(H) ARS(A) |
| 15 | COV | 1.34 | 0.224 | 9.41 | 4.7 | MCI(A)± BHA(H)± NFO(A)± NEW(H)± TOT(A)± FUL(H)± |
| 16 | LIV | 1.33 | 0.221 | 9.37 | 4.5 | IPS(A)± FUL(H) BOU(A) MCI(H) BRE(A) BHA(H) |
| 17 | BOU | 1.14 | 0.190 | 10.37 | 3.5 | NEW(A) BRE(H) LIV(H) CHE(A) SUN(H) MUN(A) |
| 18 | SUN | 1.06 | 0.176 | 10.75 | 3.2 | BRE(A) ARS(H) MCI(A) BHA(H) BOU(A) LEE(H) |
| 19 | IPS | 1.03 | 0.171 | 11.14 | 2.8 | LIV(H)± CRY(A)± EVE(A)± FUL(H)± MCI(A)± NFO(H)± |
| 20 | HUL | 1.02 | 0.169 | 11.22 | 3.2 | AVL(H)± CHE(A)± NEW(A)± EVE(H)± FUL(A)± BRE(H)± |

**ARS and MCI are a tier apart** — ΣP(CS) 2.41 and 2.40 against 1.95 for third.
Both average better than a 40% clean-sheet chance per gameweek; nobody else
clears 33%.

**LIV's defence at 16th is the file's most consequential disagreement with
FDR**, which ranks their ticker 2nd-easiest. Liverpool defenders are priced and
owned as premium clean-sheet assets; this model does not support that over
GW3–8.

## Per club-fixture detail — GW3–GW8

λ_att = expected goals scored by that club in that fixture. λ_def = expected
goals conceded. P(CS) = exp(−λ_def). `att` and `def` are presentation-only
deciles of the respective λ across all 120 rows; `def` is inverted so 10 is
best. A `±` P(CS) and its row's λ_att both carry the ±15pp / ±15% two-sided
promoted-club band.

#### GW3

| Club | Opp | V | FDR | λ_att | λ_def | P(CS) | att | def | band |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| MCI | COV | H | 2 | 2.42 | 0.59 | 0.56± | 10 | 10 | ±15pp |
| BRE | SUN | H | 2 | 2.10 | 0.94 | 0.39 | 10 | 9 | — |
| LIV | IPS | A | 2 | 1.97 | 1.45 | 0.23± | 10 | 5 | ±15pp |
| ARS | CHE | H | 4 | 1.72 | 1.20 | 0.30 | 8 | 7 | — |
| MUN | EVE | A | 3 | 1.69 | 1.53 | 0.22 | 8 | 4 | — |
| CRY | FUL | A | 3 | 1.62 | 1.10 | 0.33 | 7 | 8 | — |
| BOU | NEW | A | 3 | 1.56 | 1.52 | 0.22 | 7 | 4 | — |
| EVE | MUN | H | 4 | 1.53 | 1.69 | 0.18 | 7 | 3 | — |
| NEW | BOU | H | 3 | 1.52 | 1.56 | 0.21 | 7 | 4 | — |
| NFO | TOT | H | 3 | 1.50 | 0.90 | 0.41 | 7 | 10 | — |
| BHA | LEE | H | 2 | 1.47 | 1.24 | 0.29 | 6 | 7 | — |
| IPS | LIV | H | 4 | 1.45 | 1.97 | 0.14± | 6 | 1 | ±15pp |
| AVL | HUL | A | 2 | 1.43 | 0.97 | 0.38± | 5 | 9 | ±15pp |
| LEE | BHA | A | 3 | 1.24 | 1.47 | 0.23 | 4 | 5 | — |
| CHE | ARS | A | 5 | 1.20 | 1.72 | 0.18 | 4 | 3 | — |
| FUL | CRY | H | 3 | 1.10 | 1.62 | 0.20 | 3 | 4 | — |
| HUL | AVL | H | 3 | 0.97 | 1.43 | 0.24± | 2 | 6 | ±15pp |
| SUN | BRE | A | 3 | 0.94 | 2.10 | 0.12 | 2 | 1 | — |
| TOT | NFO | A | 3 | 0.90 | 1.50 | 0.22 | 1 | 4 | — |
| COV | MCI | A | 5 | 0.59 | 2.42 | 0.09± | 1 | 1 | ±15pp |

#### GW4

| Club | Opp | V | FDR | λ_att | λ_def | P(CS) | att | def | band |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| CHE | HUL | H | 2 | 2.78 | 0.81 | 0.45± | 10 | 10 | ±15pp |
| LIV | FUL | H | 2 | 2.13 | 1.01 | 0.36 | 10 | 9 | — |
| CRY | IPS | H | 2 | 2.01 | 1.17 | 0.31± | 10 | 8 | ±15pp |
| MCI | MUN | A | 4 | 1.95 | 1.28 | 0.28 | 9 | 7 | — |
| BRE | BOU | A | 3 | 1.76 | 1.45 | 0.23 | 8 | 5 | — |
| ARS | SUN | A | 3 | 1.65 | 0.78 | 0.46 | 8 | 10 | — |
| LEE | NEW | H | 2 | 1.60 | 1.15 | 0.32 | 7 | 8 | — |
| BHA | COV | A | 2 | 1.53 | 0.94 | 0.39± | 7 | 9 | ±15pp |
| BOU | BRE | H | 3 | 1.45 | 1.76 | 0.17 | 6 | 3 | — |
| EVE | TOT | A | 3 | 1.29 | 1.25 | 0.29 | 4 | 7 | — |
| NFO | AVL | A | 4 | 1.29 | 1.17 | 0.31 | 4 | 8 | — |
| MUN | MCI | H | 4 | 1.28 | 1.95 | 0.14 | 4 | 2 | — |
| TOT | EVE | H | 3 | 1.25 | 1.29 | 0.28 | 4 | 7 | — |
| IPS | CRY | A | 3 | 1.17 | 2.01 | 0.13± | 3 | 1 | ±15pp |
| AVL | NFO | H | 3 | 1.17 | 1.29 | 0.28 | 3 | 7 | — |
| NEW | LEE | A | 3 | 1.15 | 1.60 | 0.20 | 3 | 4 | — |
| FUL | LIV | A | 4 | 1.01 | 2.13 | 0.12 | 2 | 1 | — |
| COV | BHA | H | 2 | 0.94 | 1.53 | 0.22± | 2 | 4 | ±15pp |
| HUL | CHE | A | 4 | 0.81 | 2.78 | 0.06± | 1 | 1 | ±15pp |
| SUN | ARS | H | 4 | 0.78 | 1.65 | 0.19 | 1 | 3 | — |

#### GW5

| Club | Opp | V | FDR | λ_att | λ_def | P(CS) | att | def | band |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| MCI | SUN | H | 2 | 2.35 | 0.74 | 0.47 | 10 | 10 | — |
| BRE | CHE | H | 4 | 1.89 | 1.66 | 0.19 | 9 | 3 | — |
| NEW | HUL | H | 2 | 1.83 | 0.91 | 0.41± | 9 | 10 | ±15pp |
| MUN | FUL | A | 3 | 1.79 | 1.21 | 0.30 | 9 | 7 | — |
| EVE | IPS | H | 2 | 1.78 | 1.31 | 0.27± | 8 | 6 | ±15pp |
| LIV | BOU | A | 3 | 1.71 | 1.67 | 0.19 | 8 | 3 | — |
| BOU | LIV | H | 4 | 1.67 | 1.71 | 0.18 | 8 | 3 | — |
| CHE | BRE | A | 3 | 1.66 | 1.89 | 0.15 | 8 | 2 | — |
| NFO | COV | H | 2 | 1.65 | 0.75 | 0.47± | 8 | 10 | ±15pp |
| ARS | BHA | A | 3 | 1.48 | 1.00 | 0.37 | 6 | 9 | — |
| LEE | CRY | H | 3 | 1.40 | 1.33 | 0.27 | 5 | 6 | — |
| CRY | LEE | A | 3 | 1.33 | 1.40 | 0.25 | 5 | 6 | — |
| IPS | EVE | A | 3 | 1.31 | 1.78 | 0.17± | 5 | 3 | ±15pp |
| FUL | MUN | H | 4 | 1.21 | 1.79 | 0.17 | 4 | 2 | — |
| TOT | AVL | H | 3 | 1.18 | 1.15 | 0.32 | 3 | 8 | — |
| AVL | TOT | A | 3 | 1.15 | 1.18 | 0.31 | 3 | 8 | — |
| BHA | ARS | H | 4 | 1.00 | 1.48 | 0.23 | 2 | 5 | — |
| HUL | NEW | A | 3 | 0.91 | 1.83 | 0.16± | 1 | 2 | ±15pp |
| COV | NFO | A | 3 | 0.75 | 1.65 | 0.19± | 1 | 3 | ±15pp |
| SUN | MCI | A | 5 | 0.74 | 2.35 | 0.10 | 1 | 1 | — |

#### GW6

| Club | Opp | V | FDR | λ_att | λ_def | P(CS) | att | def | band |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| CHE | BOU | H | 3 | 2.31 | 1.39 | 0.25 | 10 | 6 | — |
| MCI | LIV | A | 4 | 1.89 | 1.31 | 0.27 | 9 | 6 | — |
| MUN | TOT | H | 3 | 1.87 | 1.05 | 0.35 | 9 | 9 | — |
| BRE | AVL | A | 4 | 1.68 | 1.14 | 0.32 | 8 | 8 | — |
| ARS | LEE | H | 2 | 1.63 | 0.80 | 0.45 | 8 | 10 | — |
| IPS | FUL | H | 2 | 1.62 | 1.21 | 0.30± | 7 | 7 | ±15pp |
| EVE | HUL | A | 2 | 1.60 | 1.02 | 0.36± | 7 | 9 | ±15pp |
| CRY | NFO | H | 3 | 1.49 | 1.21 | 0.30 | 6 | 7 | — |
| BHA | SUN | A | 3 | 1.49 | 1.20 | 0.30 | 6 | 7 | — |
| BOU | CHE | A | 4 | 1.39 | 2.31 | 0.10 | 5 | 1 | — |
| NEW | COV | A | 2 | 1.39 | 1.06 | 0.35± | 5 | 9 | ±15pp |
| LIV | MCI | H | 4 | 1.31 | 1.89 | 0.15 | 5 | 2 | — |
| FUL | IPS | A | 2 | 1.21 | 1.62 | 0.20± | 4 | 4 | ±15pp |
| NFO | CRY | A | 3 | 1.21 | 1.49 | 0.23 | 4 | 5 | — |
| SUN | BHA | H | 2 | 1.20 | 1.49 | 0.23 | 4 | 5 | — |
| AVL | BRE | H | 3 | 1.14 | 1.68 | 0.19 | 3 | 3 | — |
| COV | NEW | H | 2 | 1.06 | 1.39 | 0.25± | 2 | 6 | ±15pp |
| TOT | MUN | A | 4 | 1.05 | 1.87 | 0.15 | 2 | 2 | — |
| HUL | EVE | H | 3 | 1.02 | 1.60 | 0.20± | 2 | 4 | ±15pp |
| LEE | ARS | A | 5 | 0.80 | 1.63 | 0.20 | 1 | 3 | — |

#### GW7

| Club | Opp | V | FDR | λ_att | λ_def | P(CS) | att | def | band |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| MCI | IPS | H | 2 | 2.62 | 0.86 | 0.42± | 10 | 10 | ±15pp |
| CHE | EVE | A | 3 | 2.02 | 1.43 | 0.24 | 10 | 5 | — |
| BRE | LIV | H | 4 | 1.96 | 1.43 | 0.24 | 9 | 6 | — |
| BOU | SUN | H | 2 | 1.79 | 1.13 | 0.32 | 8 | 8 | — |
| LEE | MUN | H | 4 | 1.53 | 1.47 | 0.23 | 7 | 5 | — |
| BHA | CRY | H | 3 | 1.51 | 1.40 | 0.25 | 7 | 6 | — |
| FUL | HUL | H | 2 | 1.47 | 0.94 | 0.39± | 6 | 9 | ±15pp |
| MUN | LEE | A | 3 | 1.47 | 1.53 | 0.22 | 6 | 4 | — |
| NEW | AVL | H | 3 | 1.46 | 1.23 | 0.29 | 6 | 7 | — |
| EVE | CHE | H | 4 | 1.43 | 2.02 | 0.13 | 6 | 1 | — |
| LIV | BRE | A | 3 | 1.43 | 1.96 | 0.14 | 5 | 2 | — |
| CRY | BHA | A | 3 | 1.40 | 1.51 | 0.22 | 5 | 4 | — |
| ARS | NFO | A | 3 | 1.36 | 0.94 | 0.39 | 5 | 9 | — |
| TOT | COV | H | 2 | 1.31 | 0.85 | 0.43± | 5 | 10 | ±15pp |
| AVL | NEW | A | 3 | 1.23 | 1.46 | 0.23 | 4 | 5 | — |
| SUN | BOU | A | 3 | 1.13 | 1.79 | 0.17 | 3 | 3 | — |
| HUL | FUL | A | 3 | 0.94 | 1.47 | 0.23± | 2 | 5 | ±15pp |
| NFO | ARS | H | 4 | 0.94 | 1.36 | 0.26 | 2 | 6 | — |
| IPS | MCI | A | 5 | 0.86 | 2.62 | 0.07± | 1 | 1 | ±15pp |
| COV | TOT | A | 3 | 0.85 | 1.31 | 0.27± | 1 | 6 | ±15pp |

#### GW8

| Club | Opp | V | FDR | λ_att | λ_def | P(CS) | att | def | band |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| CHE | TOT | H | 3 | 2.23 | 0.99 | 0.37 | 10 | 9 | — |
| BRE | HUL | A | 2 | 2.11 | 0.84 | 0.43± | 10 | 10 | ±15pp |
| MUN | BOU | H | 3 | 1.94 | 1.48 | 0.23 | 9 | 5 | — |
| MCI | AVL | A | 4 | 1.89 | 0.91 | 0.40 | 9 | 9 | — |
| ARS | EVE | H | 3 | 1.88 | 0.80 | 0.45 | 9 | 10 | — |
| LIV | BHA | H | 2 | 1.83 | 1.39 | 0.25 | 9 | 6 | — |
| CRY | NEW | H | 2 | 1.81 | 1.18 | 0.31 | 9 | 8 | — |
| NFO | IPS | A | 2 | 1.55 | 1.28 | 0.28± | 7 | 7 | ±15pp |
| BOU | MUN | A | 4 | 1.48 | 1.94 | 0.14 | 6 | 2 | — |
| BHA | LIV | A | 4 | 1.39 | 1.83 | 0.16 | 5 | 2 | — |
| LEE | SUN | A | 3 | 1.38 | 1.15 | 0.32 | 5 | 8 | — |
| IPS | NFO | H | 3 | 1.28 | 1.55 | 0.21± | 4 | 4 | ±15pp |
| NEW | CRY | A | 3 | 1.18 | 1.81 | 0.16 | 3 | 2 | — |
| SUN | LEE | H | 2 | 1.15 | 1.38 | 0.25 | 3 | 6 | — |
| FUL | COV | A | 2 | 1.12 | 1.10 | 0.33± | 3 | 8 | ±15pp |
| COV | FUL | H | 2 | 1.10 | 1.12 | 0.33± | 3 | 8 | ±15pp |
| TOT | CHE | A | 4 | 0.99 | 2.23 | 0.11 | 2 | 1 | — |
| AVL | MCI | H | 4 | 0.91 | 1.89 | 0.15 | 2 | 2 | — |
| HUL | BRE | H | 3 | 0.84 | 2.11 | 0.12± | 1 | 1 | ±15pp |
| EVE | ARS | A | 5 | 0.80 | 1.88 | 0.15 | 1 | 2 | — |

## Top fixture swings

Halves of the window compared: GW3–5 against GW6–8.

| # | Club | Swing | Detail |
|---:|---|---|---|
| 1 | **LIV** | attack **−1.24** Σλ_att, defence −0.24 ΣP(CS) | IPS(A) FUL(H) BOU(A) → **MCI(H) BRE(A) BHA(H)**. The steepest attacking decline in the league. Liverpool assets are a GW3–5 hold, not a GW3–8 one. |
| 2 | **NFO** | defence **−0.43** ΣP(CS) (0.40 → 0.25 per GW) | TOT(H) AVL(A) COV(H) → CRY(A) ARS(H) IPS(A). Forest are 3rd on the defensive ticker almost entirely on the first half. Their defence is a three-gameweek asset that expires at GW6. |
| 3 | **FUL** | defence **+0.44** ΣP(CS) (0.16 → 0.31 per GW) | CRY(H) LIV(A) MUN(H) → IPS(A) HUL(H) COV(A). The largest defensive improvement in the file — and **all three** improving fixtures are banded. Per C4's residual, a Fulham clean sheet must not be the largest defensive EP term for a selected player. |
| 4 | **AVL** | attack −0.46, defence **−0.39** — worst combined | HUL(A) NFO(H) TOT(A) → BRE(H) NEW(A) MCI(H). Villa's ticker is front-loaded and their attack rating (0.85, 16th) is the league's second-worst two-round xG total at 0.64. Avoid entirely from GW6. |
| 5 | **COV** | attack **+0.73**, defence **+0.35** | MCI(A) BHA(H) NFO(A) → NEW(H) TOT(A) FUL(H). Coventry's GW3 trip to City is the worst single fixture in the window (λ_att 0.76, P(CS) 0.09); their second half is genuinely playable. But off a 20th-ranked attack, "playable" means λ_att 0.98/GW, and every row is banded. |

Also worth naming: **CHE +0.92 attack** (ARS(A) is their only hard fixture,
then HUL(H) BRE(A) BOU(H) EVE(A) TOT(H) — 2nd-best ticker and improving), and
**SUN +1.01 attack**, the largest attacking rise, which still leaves Sunderland
18th.

### Multi-GW runs

| Run | Club | Fixtures |
|---|---|---|
| Attack, top third, GW3–8 | **MCI** | all six rows att-score ≥ 9 |
| Attack, top third, GW4–8 | **CHE** | HUL(H) BRE(A) BOU(H) EVE(A) TOT(H) |
| Defence, top third, GW3–5 | **NFO** | TOT(H) 0.41, AVL(A) 0.32, COV(H) 0.48 |
| Defence, bottom third, GW3–8 | **HUL**, **IPS**, **SUN** | no row above P(CS) 0.34 for any of the three |
| Attack, bottom third, GW3–8 | **HUL** | no row above λ_att 0.98 |

## FPL FDR vs this model

FDR is the mean of `team_h_difficulty` / `team_a_difficulty` over the six rows.
Rank 1 = easiest ticker.

| Club | mean FDR | FDR rank | model ATT rank | model CS rank | FDR−ATT | FDR−CS |
|---|---:|---:|---:|---:|---:|---:|
| CRY | 2.67 | 1 | 7 | 5 | −6 | −4 |
| LIV | 2.67 | 2 | 4 | 16 | −2 | **−14** |
| NEW | 2.67 | 3 | 9 | 7 | −6 | −4 |
| COV | 2.83 | 4 | 20 | 15 | **−16** | −11 |
| FUL | 2.83 | 5 | 15 | 13 | −10 | −8 |
| ARS | 3.00 | 6 | 6 | 1 | 0 | +5 |
| AVL | 3.00 | 7 | 16 | 10 | −9 | −3 |
| BHA | 3.00 | 8 | 11 | 8 | −3 | 0 |
| MCI | 3.00 | 9 | 1 | 2 | +8 | +7 |
| NFO | 3.00 | 10 | 12 | 3 | −2 | +7 |
| BRE | 3.17 | 11 | 3 | 4 | +8 | +7 |
| CHE | 3.17 | 12 | 2 | 6 | **+10** | +6 |
| HUL | 3.17 | 13 | 19 | 20 | −6 | −7 |
| MUN | 3.17 | 14 | 5 | 12 | +9 | +2 |
| SUN | 3.17 | 15 | 18 | 18 | −3 | −3 |
| TOT | 3.17 | 16 | 17 | 11 | −1 | +5 |
| BOU | 3.33 | 17 | 8 | 17 | +9 | 0 |
| EVE | 3.33 | 18 | 10 | 14 | +8 | +4 |
| IPS | 3.33 | 19 | 14 | 19 | +5 | 0 |
| LEE | 3.33 | 20 | 13 | 9 | +7 | **+11** |

**Where they disagree, and why.**

FDR is a per-fixture symmetric difficulty derived from the strength fields —
which are **still zeroed on the split axes**, so FPL's own FDR is currently
computed off the same five coarse tiers this model uses as its weakest prior.
It cannot separate attack from defence, and it says nothing about the club
whose players you are buying.

- **COV −16 on attack** is the largest disagreement and the most dangerous.
  FDR calls Coventry's run 4th-easiest; the model has their attack last. FDR is
  describing the opponents, not Coventry.
- **LIV −14 on clean sheets.** FDR sees an easy ticker; the model sees a defence
  rated 1.01 (below average) after conceding 3.88 xG in two rounds. Both can be
  true: easy fixtures against a leaky defence.
- **CHE +10 / MCI +8 / BRE +8 / MUN +9 on attack.** FDR under-rates these
  tickers because it prices the opponent only. Chelsea's 2.03 λ_att per
  gameweek is the model's second-best and FDR ranks their run 12th.
- **LEE +11 on clean sheets.** FDR calls Leeds' ticker joint-hardest; the model
  has their defence 9th, because LEE DEFW improved to 0.93 on two contained
  rounds.
- **ARS is the one clean agreement** at the top: FDR rank 6, model attack 6,
  model defence 1.

## Blank and double gameweeks

**None in GW3–GW8.** The snapshot holds all 380 fixtures with an `event`
assigned, exactly 10 per gameweek across GW3–8, and all 20 clubs appear exactly
once in each. No club plays itself, and no gameweek contains a repeated pairing.

For the phase-2 chip agent: there is **no Bench Boost or Triple Captain
double-gameweek target inside this window**. Blanks and doubles normally appear
once domestic cup rounds are drawn and league fixtures are displaced; nothing in
this snapshot anticipates that. Re-check each cycle — this is a fact about the
current snapshot, not a forecast.

## C5 — the GW3 Triple Captain gate

C5 binds A2 and A4: *justify any GW3 TC on Haaland's own fixture-independent EP
alone; if the case requires COV's defensive rating to clear, defer the chip.*

MCI v COV(H) carries **λ_att 2.42** — the highest single-fixture attacking
figure in GW3. The question C5 asks is how much of that Coventry supply.

| Component | λ_att | Share |
|---|---:|---:|
| MCI at home vs a **league-average** defence (1.54 × 1.408) | 2.17 | **89.7%** |
| Uplift from COV's DEFW of 1.11 | +0.25 | 10.3% |

**The COV-dependent share is 10.3%.** Nine-tenths of the fixture's attacking
strength is City's own attack rating (1.41, 2nd in the league) and home
advantage — both fixture-independent. On the arithmetic, C5's gate is
**clearable**: the case does not require Coventry's defensive rating.

Band sensitivity, per C12 — COV DEFW 1.11 ±15pp gives DEFW ∈ [0.96, 1.26]:

| COV DEFW | MCI λ_att |
|---|---:|
| 0.96 (band floor) | 2.08 |
| **1.11 (central)** | **2.42** |
| 1.26 (band ceiling) | 2.73 |

Even at the band floor, λ_att 2.08 remains a top-tier GW3 fixture.

**But the gate is not the decision.** The comparison that matters is against the
alternatives already earmarked:

| GW | Fixture | λ_att | Band |
|---:|---|---:|---|
| 3 | MCI v COV (H) | 2.42 | **±15pp** |
| 5 | MCI v SUN (H) | **2.35** | none |
| 7 | MCI v IPS (H) | 2.62 | ±15pp |

GW3's premium over the **band-free** GW5 fixture is **+0.07 λ_att, under 3%**.
GW7 is the best of City's three but is banded, and Ipswich's attack rating has
just risen 0.15 — the fixture is getting less one-sided, not more.

**A2's recommendation to A4: hold the GW5 earmark.** Not because C5 fails —
it passes — but because paying a chip for a 3% edge while accepting a ±15pp
band is the wrong trade when a clean equivalent sits two gameweeks later. This
is a recommendation on fixture grounds only; Haaland's p_start, rotation risk
and the rest of the EP case belong to A3 and A4.

## Uncertainty flags

| Level | Flag | Detail |
|---|---|---|
| **HIGH** | Promoted-club ratings (COV, HUL, IPS) | Two played fixtures each. The two-sided ±15pp band applies to all **36** rows where either side is promoted, on both λ_att and P(CS). C12 governs. |
| **HIGH** | **IPS attack is rising fast** | 0.70 → 0.93 (+0.15), the largest move in the file, on 1.79 and 2.06 xG. This is C12's inflation risk pointing **upward**: do not treat Ipswich as a soft attacking opponent, and do not bank a clean sheet against them. Their DEFW rose too (+0.11) — Ipswich are becoming a high-variance fixture on both sides. |
| **HIGH / ASSUMPTION** | All 20 defence priors | `strength_attack_*` and `strength_defence_*` are zero for the third gameweek running. Every DEFW prior comes from the 5-tier `strength_overall_*` plus my own reading of last season. Re-derive the moment FPL populates the split fields. |
| **MEDIUM** | **`base_lambda` may be ~12% low** | Held at 1.54 / 1.33 (2.87 goals per match). Observed league xG is **3.27 per match** over rounds 1–2 (31.30 then 34.06 across 10 matches each). If that persists, every λ_att in this file is systematically low and every P(CS) correspondingly high. Held deliberately, per the retro's no-overcorrection discipline — 20 matches of early-season xG is not enough to move a season-long base. **Re-test at GW6** (n ≈ 60 matches); if the excess holds above 8%, raise the base rather than inflating individual ATT indices. |
| **MEDIUM** | Clipping censors extremes | 22 of 80 implied ratings hit the [0.55, 1.80] guard. Clipped clubs have ratings **floored above their evidence**: AVL attack (implied 0.23 and 0.32, both clipped to 0.55) is rated 0.85 and is plausibly worse; CRY attack (0.55 floor in round 2) likewise. Treat a rating built from two clipped values as a bound, not an estimate. |
| **MEDIUM** | Two rounds is a thin base | Even at 74/26, a club with one aberrant match still carries it. The GW2 clips that unwound this cycle (TOT, AVL, COV) are the visible evidence of that. |
| **LOW / ASSUMPTION** | European and cup congestion is not modelled | The fixture file carries domestic league fixtures only. Clubs in continental competition (ASSUMPTION, from prior-season finish: ARS, MCI, LIV, CHE, NEW, TOT) carry midweek rotation risk that no λ in this file reflects. This belongs in A3's `p_start`, not in λ_att — flagged here so it is not double-counted. |

## Handoff to downstream agents

| Consumer | Reads | Must respect |
|---|---|---|
| `fpl ep` (code) | `base_lambda`, `att`, `lambda_att`, `lambda_def`, `p_cs` | `defw`, `fdr`, `band` are not emitted |
| **A3 player-analyst** | λ_att and P(CS) per club-fixture | Apply the 60-minute and rotation discounts yourself — P(CS) here is pure Poisson. European rotation is yours, not mine. |
| **A4 squad-optimizer** | the two 6-GW tickers, the swings, `band` | C4 residual: a banded fixture must not be a selected player's largest **defensive** EP term. C12 lifts that constraint for attacking terms. C5: hold the GW5 TC earmark. |
| **A2, GW4 cycle** | this file | Promoted clubs reach 3 played fixtures after GW3 — **re-derive and lift the ±15pp band**, per C4's stated threshold. Re-test `base_lambda` at GW6. |
