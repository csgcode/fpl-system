# GW8 transfers — research and justification

Read-only research for the GW8 wildcard decision. It compares the squad
optimizer's proposal ("plan C", data/decisions/gw8/squad-proposal.md) with
the red-team's alternative ("F1", data/decisions/gw8/review.md). Nothing in
the proposal, review, inputs or players files was changed.

## How to read the numbers

- **EP** = expected points from the model (docs/ep-model.md). It already
  multiplies by the chance the player starts (`p_start`).
- **Blend** is the published figure: last season(s) and this season mixed
  roughly 50/50. **Prior-only** uses the player's longer history alone. When
  the two disagree in sign, the gain rests on seven games of this season.
- **Player delta** = incoming player's EP minus outgoing player's EP. **Team
  marginal** = how much the whole squad's score drops if only that one
  transfer is undone. They differ because only the best XI and captain
  score: a bench player adds nothing unless he would start.
- **±** marks a fixture against a promoted club (IPS, COV, HUL). Those clubs'
  ratings are an assumption with HIGH uncertainty.
- Sell prices are the GW7-verified ones from data/decisions/gw7/final.md
  (`--sell 1:6.0,112:4.9,4:7.9,229:6.1,427:7.9,124:5.9,68:6.0,542:5.7,411:15.5,249:5.6,106:7.8,497:4.0,202:4.9,94:6.2,423:4.3 --bank 0.4`),
  the same basis the review used. Plan C leaves £0.5m in the bank, F1 £0.0m.
- Season points (actual, GW1–7) are shown for context only. The model does
  not use them directly; it uses expected goals, assists, saves and minutes.

## Summary

| Move | Season pts out → in | EP6 out → in (blend) | Prior-only out → in | Team marginal, blend / prior | Role |
|---|---|---|---|---|---|
| Raya → Trafford | 42 → 32 | 21.66 → 21.70 | 21.38 → 21.43 | −0.104 / −0.110 | frees £1.0m for the GK2 upgrade |
| Dubravka → Suzuki | 0 → 26 | 0.68 → 20.74 | 0.68 → 20.26 | +0.555 / +0.482 | playing backup keeper, rotated in |
| *Dubravka → Kinsky (F1)* | 0 → 23 | 0.68 → 19.06 | 0.68 → 19.29 | +0.119 / +0.189 | cheaper backup, frees £0.5m |
| Tarkowski → Silva | 46 → 21 | 23.02 → 25.85 | 23.63 → 21.87 | +1.598 / **−1.959** | the one sign flip |
| *Tarkowski → Calafiori (F1)* | 46 → 44 | 23.02 → 25.67 | 23.63 → 24.14 | +1.771 / +0.404 | no sign flip |
| Shaw → Justin | 12 → 34 | 7.32 → 22.37 | 7.35 → 22.87 | +1.296 / +2.027 | removes an injured player |
| Groß → Saka | 58 → 37 | 23.74 → 28.64 | 22.93 → 26.83 | **+5.818 / +4.494** | the main gain |
| Schade → Gomez | 40 → 37 | 20.46 → 22.86 | 21.24 → 22.66 | +0.091 / +0.222 | saves £1.2m, small EP |
| Thiago → Wissa | 18 → 18 | 25.23 → 25.32 | 26.90 → 28.14 | +0.411 / +1.245 | saves £1.7m, same EP |

Where the money goes in plan C (GW7 sell prices): Saka costs £3.7m more than
Groß. That is paid for by Thiago → Wissa (£1.7m), Schade → Gomez (£1.2m) and
Tarkowski → Silva (£1.1m), less £0.2m extra for Justin over Shaw. The two
goalkeeper moves cancel out: Raya + Dubravka (£10.0m) become Trafford +
Suzuki (£10.0m). Net: £0.1m into the bank (0.4 → 0.5).

## 1. Per transfer, GW8–13

### Raya → Trafford

| GW | Raya opp | EP | Trafford opp | EP | Δ (in − out) |
|---|---|---|---|---|---|
| 8 | EVE(H) | 3.83 | SUN(A) | 3.57 | −0.25 |
| 9 | LIV(A) | 3.34 | BOU(A) | 3.47 | +0.13 |
| 10 | HUL(H) ± | 4.19 | TOT(H) | 3.90 | −0.29 |
| 11 | NEW(A) | 3.71 | CHE(A) | 3.45 | −0.25 |
| 12 | MCI(H) | 3.26 | COV(H) ± | 3.98 | +0.72 |
| 13 | BRE(A) | 3.34 | MCI(A) | 3.33 | −0.00 |
| **6-GW sum** | | **21.66** | | **21.70** | **+0.04** |
| prior-only sum | | 21.38 | | 21.43 | +0.05 |

Prices: Raya sells for £6.0m (GW7-verified) / Trafford costs £5.0m. Team-level marginal in plan C (blend / prior-only): −0.104 / −0.110; +0.042 / +0.045 inside F1.

### Dubravka → Suzuki

| GW | Dubravka opp | p_start | EP | Suzuki opp | p_start | EP | Δ (in − out) |
|---|---|---|---|---|---|---|---|
| 8 | CHE(A) | 0.03 | 0.11 | MCI(H) | 0.95 | 3.22 | +3.12 |
| 9 | CRY(H) | 0.03 | 0.11 | FUL(H) | 0.95 | 3.65 | +3.54 |
| 10 | LEE(A) | 0.03 | 0.11 | MUN(A) | 0.95 | 3.32 | +3.21 |
| 11 | IPS(H) ± | 0.03 | 0.12 | SUN(H) | 0.95 | 3.56 | +3.45 |
| 12 | SUN(A) | 0.03 | 0.11 | IPS(A) ± | 0.95 | 3.39 | +3.28 |
| 13 | FUL(H) | 0.03 | 0.12 | EVE(H) | 0.95 | 3.59 | +3.47 |
| **6-GW sum** | | | **0.68** | | | **20.74** | **+20.06** |
| prior-only sum | | | 0.68 | | | 20.26 | +19.58 |

Prices: Dubravka sells for £4.0m (GW7-verified) / Suzuki costs £5.0m. Team-level marginal in plan C (blend / prior-only): +0.555 / +0.482.

### Dubravka → Kinsky (red-team F1)

| GW | Dubravka opp | p_start | EP | Kinsky opp | p_start | EP | Δ (in − out) |
|---|---|---|---|---|---|---|---|
| 8 | CHE(A) | 0.03 | 0.11 | CHE(A) | 0.95 | 2.92 | +2.81 |
| 9 | CRY(H) | 0.03 | 0.11 | CRY(H) | 0.95 | 3.20 | +3.09 |
| 10 | LEE(A) | 0.03 | 0.11 | LEE(A) | 0.95 | 3.06 | +2.95 |
| 11 | IPS(H) ± | 0.03 | 0.12 | IPS(H) ± | 0.95 | 3.27 | +3.16 |
| 12 | SUN(A) | 0.03 | 0.11 | SUN(A) | 0.95 | 3.16 | +3.05 |
| 13 | FUL(H) | 0.03 | 0.12 | FUL(H) | 0.95 | 3.45 | +3.33 |
| **6-GW sum** | | | **0.68** | | | **19.06** | **+18.38** |
| prior-only sum | | | 0.68 | | | 19.29 | +18.61 |

Prices: Dubravka sells for £4.0m (GW7-verified) / Kinsky costs £4.5m. Team-level marginal inside the F1 package (blend / prior-only): +0.119 / +0.189.

### Tarkowski → Silva

| GW | Tarkowski opp | EP | Silva opp | EP | Δ (in − out) |
|---|---|---|---|---|---|
| 8 | ARS(A) | 3.25 | MUN(A) | 4.10 | +0.85 |
| 9 | NEW(A) | 4.06 | LEE(H) | 4.41 | +0.36 |
| 10 | COV(H) ± | 4.65 | IPS(A) ± | 4.29 | −0.36 |
| 11 | BRE(A) | 3.47 | NFO(H) | 4.36 | +0.90 |
| 12 | LIV(H) | 3.77 | FUL(A) | 4.42 | +0.66 |
| 13 | AVL(A) | 3.83 | BHA(H) | 4.26 | +0.43 |
| **6-GW sum** | | **23.02** | | **25.85** | **+2.83** |
| prior-only sum | | 23.63 | | 21.87 | −1.76 |

Prices: Tarkowski sells for £6.1m (GW7-verified) / Silva costs £5.0m. Team-level marginal in plan C (blend / prior-only): +1.598 / −1.959.

### Tarkowski → Calafiori (red-team F1)

| GW | Tarkowski opp | EP | Calafiori opp | EP | Δ (in − out) |
|---|---|---|---|---|---|
| 8 | ARS(A) | 3.25 | EVE(H) | 4.60 | +1.35 |
| 9 | NEW(A) | 4.06 | LIV(A) | 3.70 | −0.36 |
| 10 | COV(H) ± | 4.65 | HUL(H) ± | 5.18 | +0.53 |
| 11 | BRE(A) | 3.47 | NEW(A) | 4.48 | +1.01 |
| 12 | LIV(H) | 3.77 | MCI(H) | 3.85 | +0.08 |
| 13 | AVL(A) | 3.83 | BRE(A) | 3.86 | +0.03 |
| **6-GW sum** | | **23.02** | | **25.67** | **+2.65** |
| prior-only sum | | 23.63 | | 24.14 | +0.51 |

Prices: Tarkowski sells for £6.1m (GW7-verified) / Calafiori costs £6.0m. Team-level marginal inside the F1 package (blend / prior-only): +1.771 / +0.404.

### Shaw → Justin

| GW | Shaw opp | p_start | EP | Justin opp | p_start | EP | Δ (in − out) |
|---|---|---|---|---|---|---|---|
| 8 | BOU(H) | 0.00 | 0.00 | SUN(A) | 0.95 | 3.77 | +3.77 |
| 9 | CHE(A) | 0.30 | 0.77 | BOU(A) | 0.95 | 3.34 | +2.58 |
| 10 | AVL(H) | 0.45 | 1.48 | TOT(H) | 0.95 | 4.33 | +2.85 |
| 11 | LIV(A) | 0.55 | 1.41 | CHE(A) | 0.95 | 3.37 | +1.97 |
| 12 | BRE(H) | 0.60 | 1.75 | COV(H) ± | 0.95 | 4.61 | +2.86 |
| 13 | NEW(A) | 0.60 | 1.92 | MCI(A) | 0.95 | 2.94 | +1.02 |
| **6-GW sum** | | | **7.32** | | | **22.37** | **+15.05** |
| prior-only sum | | | 7.35 | | | 22.87 | +15.52 |

Prices: Shaw sells for £4.3m (GW7-verified) / Justin costs £4.5m. Team-level marginal in plan C (blend / prior-only): +1.296 / +2.027; +1.439 / +1.972 inside F1.

### Groß → Saka

| GW | Groß opp | p_start | EP | Saka opp | p_start | EP | Δ (in − out) |
|---|---|---|---|---|---|---|---|
| 8 | LIV(A) | 0.94 | 3.62 | EVE(H) | 0.50 | 2.95 | −0.67 |
| 9 | MCI(A) | 0.94 | 3.69 | LIV(A) | 0.85 | 4.23 | +0.54 |
| 10 | BRE(H) | 0.94 | 4.09 | HUL(H) ± | 0.92 | 5.95 | +1.87 |
| 11 | HUL(A) ± | 0.94 | 4.21 | NEW(A) | 0.92 | 5.43 | +1.22 |
| 12 | NEW(H) | 0.94 | 4.46 | MCI(H) | 0.92 | 5.12 | +0.65 |
| 13 | BOU(A) | 0.94 | 3.67 | BRE(A) | 0.92 | 4.95 | +1.28 |
| **6-GW sum** | | | **23.74** | | | **28.64** | **+4.90** |
| prior-only sum | | | 22.93 | | | 26.83 | +3.90 |

Prices: Groß sells for £5.9m (GW7-verified) / Saka costs £9.6m. Team-level marginal in plan C (blend / prior-only): +5.818 / +4.494; +5.878 / +4.626 inside F1.

### Schade → Gomez

| GW | Schade opp | p_start | EP | Gomez opp | p_start | EP | Δ (in − out) |
|---|---|---|---|---|---|---|---|
| 8 | HUL(A) ± | 0.80 | 3.68 | LIV(A) | 0.93 | 3.54 | −0.14 |
| 9 | NFO(H) | 0.80 | 3.40 | MCI(A) | 0.93 | 3.58 | +0.18 |
| 10 | BHA(A) | 0.80 | 3.30 | BRE(H) | 0.93 | 3.91 | +0.61 |
| 11 | EVE(H) | 0.80 | 3.63 | HUL(A) ± | 0.93 | 4.03 | +0.40 |
| 12 | MUN(A) | 0.80 | 3.36 | NEW(H) | 0.93 | 4.22 | +0.87 |
| 13 | ARS(H) | 0.80 | 3.10 | BOU(A) | 0.93 | 3.58 | +0.48 |
| **6-GW sum** | | | **20.46** | | | **22.86** | **+2.40** |
| prior-only sum | | | 21.24 | | | 22.66 | +1.42 |

Prices: Schade sells for £6.2m (GW7-verified) / Gomez costs £5.0m. Team-level marginal in plan C (blend / prior-only): +0.091 / +0.222; +0.141 / +0.029 inside F1.

### Thiago → Wissa

| GW | Thiago opp | EP | Wissa opp | EP | Δ (in − out) |
|---|---|---|---|---|---|
| 8 | HUL(A) ± | 4.50 | CRY(A) | 4.49 | −0.01 |
| 9 | NFO(H) | 4.17 | EVE(H) | 4.40 | +0.23 |
| 10 | BHA(A) | 4.13 | FUL(A) | 4.14 | +0.01 |
| 11 | EVE(H) | 4.47 | ARS(H) | 3.79 | −0.69 |
| 12 | MUN(A) | 4.17 | BHA(A) | 4.09 | −0.08 |
| 13 | ARS(H) | 3.79 | MUN(H) | 4.41 | +0.63 |
| **6-GW sum** | | **25.23** | | **25.32** | **+0.09** |
| prior-only sum | | 26.90 | | 28.14 | +1.25 |

Prices: Thiago sells for £7.8m (GW7-verified) / Wissa costs £6.1m. Team-level marginal in plan C (blend / prior-only): +0.411 / +1.245; +0.382 / +1.245 inside F1.

## 2. Team total EP per gameweek

Computed with the objective's own code (`fpl/objective.py`: `load_views`,
`_points`, `best_lineup`) in a scratch script, because `fpl objective` prints
only the 6-GW total and the GW8 XI. Each GW = best legal XI's EP + the
captain's EP again (the XI's highest EP player). The bench scores nothing.
The 6-GW sums match `fpl objective` exactly (baseline 328.050 / 318.513;
C +9.800 / +6.557; F1 +9.537 / +8.627).

Important: this assumes the best XI is picked every week from the 15, i.e.
the goalkeeper and outfield lineup are re-chosen each GW on that week's EP.

**Blend (the published figures)**

| Squad | GW8 | GW9 | GW10 | GW11 | GW12 | GW13 | 6-GW total | vs current |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| (a) Current, no moves | 53.64 | 54.94 | 56.86 | 55.76 | 53.16 | 53.70 | 328.05 | — |
| (b) Plan C | 54.01 | 56.30 | 59.03 | 56.75 | 55.47 | 56.30 | 337.85 | +9.80 |
| (c) Red-team F1 | 54.51 | 55.47 | 59.92 | 56.75 | 55.19 | 55.76 | 337.59 | +9.54 |
| F1 minus C | +0.50 | −0.84 | +0.89 | +0.00 | −0.28 | −0.53 | −0.26 | |

**Prior-only**

| Squad | GW8 | GW9 | GW10 | GW11 | GW12 | GW13 | 6-GW total | vs current |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| (a) Current | 52.68 | 53.23 | 55.12 | 54.06 | 51.34 | 52.08 | 318.51 | — |
| (b) Plan C | 52.60 | 53.84 | 56.24 | 54.60 | 53.94 | 53.87 | 325.07 | +6.56 |
| (c) Red-team F1 | 53.45 | 53.66 | 57.47 | 54.75 | 53.94 | 53.89 | 327.14 | +8.63 |

Captain each GW (all three squads unless noted): Haaland GW8, GW9, GW11,
GW13; Mbeumo GW12; GW10 Saka in C and F1 (HUL(H) ±, a promoted-club row),
Gabriel in the current squad.

Note on GW8: the objective's best GW8 XI for C is a 4-3-3 (54.01). The
proposal fields a 5-3-2 (53.92), starting Van Hecke over Barry by a
tie-break rule; that costs 0.095.

Average per GW: current 54.7, plan C 56.3, F1 56.3. The S6 target of 60 is
not reached by either.

**Reading C v F1.** They are 0.26 apart on blend, which is noise at this
scale. F1 is 2.07 better on prior-only, mostly because Calafiori has a long
Premier League record and Silva does not (Silva's prior is a league
average, `prior_source: league_mean`, 0 prior minutes). F1 is better in GW8
and GW10 (Calafiori v EVE (H) and HUL (H) ±); C is better in GW9, GW12, GW13
(Silva's fixtures LEE (H), FUL (A), BHA (H), and Suzuki's GW9 and GW13).

## 3. Saka

### Share of Arsenal's attack (GW1–7, from the event-live snapshots)

| | Saka | Arsenal | Saka's share |
|---|---:|---:|---:|
| Goals | 3 | 11 | 27% |
| Assists | 0 | 10 | 0% |
| Goal involvements (G+A) / team goals | 3 | 11 | 27% |
| xG | 3.63 | 11.97 | 30% |
| xA | 1.20 | 8.99 | 13% |
| xG + xA | 4.83 | 20.96 | 23% |

His round by round: points 9, 11, 2, 8, 2, 2, 3; goals in GW1, GW2, GW4;
xG 0.64, 0.63, 0.23, 1.38, 0.34, 0.41, 0.00. Since GW5 he has 7 points in
three games and no attacking return, though he still had 0.75 xG + 0.77 xA
in GW5–7. FPL form 2.5. Season points 37 (Groß, whom he replaces, has 58).

### Arsenal's scoring

| | Arsenal | League average (per team per match) |
|---|---:|---:|
| Goals per match, season (7) | 1.57 (11) | 1.45 |
| Goals per match, last 5 (GW3–7) | 1.40 (2, 2, 0, 2, 1) | 1.41 |
| xG per match, season | 1.71 (rank 6) | 1.51 |
| xG per match, last 5 | 1.81 | — |
| Goals rank, season | joint 5th (with IPS) | — |

Arsenal create above the league average but have finished at about the
average over the last five. The fixture model rates their GW8–13 attack 2nd
best (Σλ 10.40; only MCI higher) and their defence best (ΣP(clean sheet)
2.20).

### Availability

- This season: 7 starts from 7, 596 minutes (67, 90, 89, 90, 80, 90, 90).
- Previous seasons (from the cached history): 2022/23 37 starts, 2023/24
  35, 2024/25 20, 2025/26 25 (2218 minutes). The data gives starts, not
  reasons, so "games missed to injury" cannot be separated from rotation.
  The 2024/25 low matches his long hamstring absence that season (outside
  knowledge, not in the data). In the last two seasons he started 45 of 76
  league games (59%).
- Now: status `d`, 50% chance, "Thigh injury - 50% chance of playing",
  posted 21 Oct 20:30 UTC. 357k managers sold him this GW, 27k bought;
  a 0.1 price drop after the deadline is likely.

### How much his EP rests on the guessed return

The analyst's `p_start` for GW8–13 is 0.50 / 0.85 / 0.92 / 0.92 / 0.92 /
0.92, noted as "ramp is a guess". His EP per start is about 5.0 (GW9),
6.5 (GW10), 5.9, 5.6, 5.4, so each 0.1 of start probability is worth about
0.5–0.65 EP that week. Team-level effect (plan C and F1 rescored with only
Saka's start chances changed):

| Scenario | Saka EP6 | Plan C gain, blend / prior | F1 gain, blend / prior | Groß → Saka marginal, blend |
|---|---:|---:|---:|---:|
| As modelled | 28.64 | +9.80 / +6.56 | +9.54 / +8.63 | +5.82 |
| Fully fit now (0.92 every GW) | 31.46 | +11.92 / +8.49 | +11.66 / +10.55 | +7.94 |
| Misses GW8, GW9 at 0.50 | 23.94 | +9.33 / +6.26 | +9.01 / +8.14 | +5.35 |
| Misses GW8–9, back GW10 at 0.85 | 21.00 | +8.55 / +5.84 | +8.23 / +7.72 | +4.57 |
| Misses GW8–10, back GW11 at 0.85 | 15.09 | +6.55 / +4.24 | +6.22 / +6.12 | +2.57 |
| Misses all of GW8–13 | 0 | +3.18 / +1.25 | +2.81 / +3.37 | −0.80 |

- His GW8 is already benched in the plan, so missing GW8 costs the team
  nothing. A missed GW9 costs the team only about 0.5 because a bench
  player (Gomez or Richards) starts instead.
- Comparison: plan H (no Saka; Stach + Barnes + Calafiori instead of Saka +
  Gomez + Justin) scores +7.261 / +5.433 on the same sell basis, with £1.5m
  unspent. C beats H unless Saka misses roughly GW8–10. If he misses three
  weeks, H is ahead by about 0.7 and C sits only 0.55 above the 6.0
  wildcard gate.

## 4. Raya v Trafford, and the goalkeeper pair

### Why Raya is sold

It is a funding move. Raya sells for £6.0m, Trafford costs £5.0m, freeing
£1.0m (the proposal says £1.1m on the unverified current-price basis). That
£1.0m pays exactly for upgrading the backup from Dubravka (£4.0m, never
plays) to Suzuki (£5.0m). The goalkeeping pair costs £10.0m before and after.
On its own Raya → Trafford is −0.104 blend / −0.110 prior-only in plan C. In
F1 (Kinsky £4.5m as backup) it is +0.042 / +0.045, and £0.5m goes towards
Calafiori.

### Per GW

Figures per start (the model multiplies them by 0.95 start chance for both
keepers). "Save pts" = expected points from saves (1 per 3 saves, plus a small
penalty-save allowance).

| GW | Raya opp | P(CS) | Save pts | EP | Trafford opp | P(CS) | Save pts | EP | Better |
|---|---|---:|---:|---:|---|---:|---:|---:|---|
| 8 | EVE (H) | 0.42 | 0.22 | 3.83 | SUN (A) | 0.26 | 0.90 | 3.57 | Raya +0.25 |
| 9 | LIV (A) | 0.30 | 0.33 | 3.34 | BOU (A) | 0.21 | 1.10 | 3.47 | Trafford +0.13 |
| 10 | HUL (H) ± | 0.51 | 0.17 | 4.19 | TOT (H) | 0.38 | 0.60 | 3.90 | Raya +0.29 |
| 11 | NEW (A) | 0.39 | 0.24 | 3.71 | CHE (A) | 0.20 | 1.15 | 3.45 | Raya +0.25 |
| 12 | MCI (H) | 0.28 | 0.37 | 3.26 | COV (H) ± | 0.41 | 0.53 | 3.98 | Trafford +0.72 |
| 13 | BRE (A) | 0.30 | 0.34 | 3.34 | MCI (A) | 0.14 | 1.42 | 3.33 | level |
| **Sum** | | **2.20** | **1.67** | **21.66** | | **1.60** | **5.70** | **21.70** | |

The two arrive at the same total by different routes. Raya's EP is clean
sheets (8.4 of 21.7): Arsenal have the league's best defensive rating (0.71,
rank 1; 5 goals conceded in 7). Trafford's leans on saves (5.4 of 21.7):
Leeds' defensive rating is 0.92 (rank 6; 6 conceded in 7) and he averages
3.7 saves per 90 against Raya's 2.0. Save points come from being busy, so
they arrive with goals conceded; clean sheets also carry bonus points.
Season points: Raya 42, Trafford 32.

### Is the plan to rotate Trafford and Suzuki by fixture?

Yes, implicitly. The objective picks the better keeper each GW, and Suzuki's
whole +0.555 value comes from that. The proposal says so in Step 3 ("rotating
pair … T/S/T/S/T/S"). For GW8 it starts Trafford and benches Suzuki at slot
12.

| GW | Trafford (LEE) | Suzuki (AVL) | Kinsky (TOT) | Start |
|---|---|---|---|---|
| 8 | SUN (A) 3.57 | MCI (H) 3.22 | CHE (A) 2.92 | Trafford |
| 9 | BOU (A) 3.47 | FUL (H) 3.65 | CRY (H) 3.20 | Suzuki +0.19 |
| 10 | TOT (H) 3.90 | MUN (A) 3.32 | LEE (A) 3.06 | Trafford |
| 11 | CHE (A) 3.45 | SUN (H) 3.56 | IPS (H) ± 3.27 | Suzuki +0.11 |
| 12 | COV (H) ± 3.98 | IPS (A) ± 3.39 | SUN (A) 3.16 | Trafford |
| 13 | MCI (A) 3.33 | EVE (H) 3.59 | FUL (H) 3.45 | Suzuki +0.26 (Kinsky +0.12) |

The fixtures do alternate: Leeds and Villa swap home and away in five of
the six weeks. But the gain is small:

| GK pair (cost) | Always start the first-choice | Start the better one each GW | Gain from rotating |
|---|---:|---:|---:|
| Trafford + Suzuki (£10.0m, plan C) | 21.70 | 22.26 | +0.56 |
| Trafford + Kinsky (£9.5m, F1) | 21.70 | 21.82 | +0.12 |
| Raya + Dubravka (£10.0m, today) | 21.66 | 21.66 | 0 |
| Raya + Kinsky (£10.5m) | 21.66 | 21.78 | +0.12 |
| Raya + Suzuki (£11.0m, not affordable in C) | 21.66 | 22.36 | +0.70 |

Plan C's rotation is worth about 0.09 a week, and in each of Suzuki's weeks
he is ahead by only 0.11–0.26, well inside the model's error. Suzuki's prior
is also a league average (no Premier League minutes in his record). In
practice the plan is "Trafford first choice; Suzuki in GW9, 11, 13 if the
numbers still say so". The other value of a playing backup is auto-sub
cover and the bench-boost earmark in GW19, which Kinsky also gives.

Keeping Raya is affordable: plan C with Raya kept and Dubravka → Kinsky
(instead of Raya → Trafford and Dubravka → Suzuki) scores +9.322 / +6.219,
0.48 / 0.34 below C, leaving £0.0m in the bank.

## 5. How GW8–13 plays out (plan C)

- **GW8 (54.0).** Saka benched (50% flag). Trafford in goal at SUN (A).
  Haaland captain at AVL (A). Silva, Richards, Justin, Gabriel at the back.
- **GW9 (56.3).** Saka expected back at 85%, starts at LIV (A). Suzuki
  replaces Trafford (FUL (H)). Haaland captain v BHA (H): the provisional
  Triple Captain week.
- **GW10 (59.0), the peak.** Arsenal v HUL (H) ±: Saka is the top EP and
  captain (5.95); Gabriel, Saka and (in F1) Calafiori all lean on this
  promoted-club fixture, whose rating is the least certain in the window.
- **GW11 (56.7).** Suzuki v SUN (H). Wissa drops to the bench (NEW v ARS);
  3-5-2 with Gomez (HUL (A) ±).
- **GW12 (55.5).** Haaland is at ARS (A) (5.00), so Mbeumo v BRE (H)
  (5.30) is captain. Trafford v COV (H) ±.
- **GW13 (56.3).** Suzuki v EVE (H). Sunderland (Le Fée) and Newcastle
  (Wissa) turn hard from GW11; Brighton (Gomez) turns easy. Two free
  transfers at GW9 can absorb this.

### Weakest links

| Player | Why | Model detail |
|---|---|---|
| Saka (£9.6m) | 50% flag, guessed return | see §3; best week is a promoted-club fixture |
| Silva | the only move whose prior-only sign flips (−1.96) | 630 minutes of this season, prior = league average; 21 season points, 0.7% owned |
| Wissa | 18 season points, form 1.5, NEW attack rank 18 | EP held up by his longer record (prior 28.1 > blend 25.3); 254k sold him this GW |
| Gomez | marginal +0.09; mostly a funding move | nailed (7/7) but no upside over Schade |
| Suzuki | only valuable if rotated; prior is a league average | +0.555 over 6 GWs |
| Trafford | EP built on saves, Leeds rank 6 defence | P(CS) 0.14–0.41 |
| Promoted-club rows (±) | IPS/COV/HUL ratings HIGH uncertainty | Saka GW10, Trafford GW12, Silva GW10, Justin GW12 |

### The strongest case against each contested move

**Groß → Saka.** £9.6m on a player who is 50% for this week, is benched in
GW8 and has a guessed return. Groß has 58 points to Saka's 37 and is nailed;
Saka has one return in five games and two seasons of 20 and 25 starts. If
he misses three weeks the no-Saka plan H is better and C barely clears the
wildcard gate; if he goes `i` after the deadline, there is no wildcard left
to undo it, only free transfers. His biggest week (GW10) depends on the
least certain fixture rating. **For:** it is the largest single gain in
every reading (+5.8 blend, +4.5 prior-only), it survives one or two missed
weeks, Arsenal have the 2nd-best attacking fixtures, and his share of
Arsenal's xG (30%) is that of a main finisher.

**Raya → Trafford.** It loses EP on both readings in plan C (−0.10). It
swaps the league's best defence for Leeds, and a points source built on
clean sheets for one built on saves. It sells a keeper 45% of managers own
(Trafford is 6%), adding rank risk in Arsenal clean-sheet weeks. Its only
job is to fund Suzuki, whose rotation gain is under 0.1 a week. Keeping Raya
with Kinsky as backup costs 0.48. **For:** the whole GK change (Raya +
Dubravka → Trafford + Suzuki) is +0.45 at no cost, fixes the dead backup
(needed for the GW19 bench boost), and the user already owns Gabriel (and
Saka) for Arsenal clean-sheet exposure, so selling Raya spreads risk across
clubs. In F1, Raya → Trafford is mildly positive (+0.04).

## Method and caveats

- Per-GW totals, per-GW keeper terms and the Saka scenarios came from scratch
  scripts calling the repo's own functions (`fpl.objective`, `fpl.ep`); no
  repo file was modified and `fpl ep` was not run.
- `p_start` ramps (Saka, Shaw) are the analyst's guesses. Promoted-club
  fixture ratings (±) are assumptions with HIGH uncertainty.
- The keeper P(CS) and save figures are per start, before the 0.95 start
  chance.
- The objective assumes a perfect weekly lineup choice; real managers pick
  before results, so the rotation figures are an upper bound.
