# GW8 revision — a midfielder instead of Saka (Raya kept)

Read-only research for the GW8 revision after the red-team's REVISE. The
user's steer for the revision: **keep Raya** (no Raya → Trafford), **drop
Saka** (no Groß → Saka), and look instead for a midfielder from a
high-scoring club who is near the top on expected goals and assists (xG, xA)
and on expected points (EP). Nothing in the proposal, review, inputs or
players files was changed; `fpl ep` was not run.

## How to read the numbers

- **EP6** = expected points over GW8–13 from data/analysis/gw8/players-*.json.
  **Blend** is the published figure. **Prior-only** uses the player's longer
  history alone (the objective's own prior view). When the two disagree in
  sign, the gain rests on seven games of this season.
- **Package gain** = 6-GW team score (best XI each week + captain) after the
  moves, minus the current squad's (blend 328.050 / prior-only 318.513), from
  `fpl objective --chip wildcard`.
- **Chip gate**: a wildcard must beat the best no-chip plan by at least 6.0
  on blend and not lose on prior-only. The no-chip plan this week is **bank**
  (+0.000 / +0.000: no single move passes the free-transfer gate), so the
  wildcard needs **+6.0 blend and ≥ 0 prior-only**.
- Sell basis: the GW7-verified prices the review and the earlier research
  used: `--sell 1:6.0,112:4.9,4:7.9,229:6.1,427:7.9,124:5.9,68:6.0,542:5.7,411:15.5,249:5.6,106:7.8,497:4.0,202:4.9,94:6.2,423:4.3 --bank 0.4`
  (team value 99.1). The CLI reproduces F1 exactly on it (+9.537 / +8.627,
  bank 0.0).
- Season stats are GW1–7 from the event-live snapshots
  (data/raw/gw{2..8}/event-live-e{1..7}.json). "Last 5" = GW3–7.
- **±** marks a fixture against a promoted club (IPS, COV, HUL), whose
  ratings carry HIGH uncertainty.

## Summary

- **The high-scoring clubs** are Brighton, Man City and Chelsea on goals,
  with Brentford fourth. On chances created (xG) the top group is Man City,
  Brighton, Bournemouth, Brentford, Man Utd and Arsenal. Chelsea score far
  more than their chances: 2.0 goals a game over the last five on 0.94 xG,
  the **lowest** xG in the league over that stretch.
- **Brentford has no midfielder worth buying.** Their attack runs through
  Thiago (a forward). Their best midfielders by EP are Schade (ours, 20.46),
  Lewis-Potter (20.03) and Anthony (18.23), all below the 22–25 the squad
  already fields.
- **Chelsea's case is Rogers, not Palmer.** Rogers: 7/7 starts, 40 points,
  returns in 5 of 7 games, 22% of Chelsea's xG+xA, EP6 24.66 / 22.48. Palmer
  has the higher prior-only EP (28.28) but every Palmer package fails the
  chip gate on blend (best +5.46).
- **We already own the steadiest high-scoring-club midfielder: Groß.**
  Brighton are the league's top scorers; Groß has 58 points (squad best bar
  Haaland), 7/7 starts, returns in 5 of 7, and his last-5 xG+xA per 90 rose
  to 0.60. Replacing him with Rogers adds only +0.5 to +1.2 blend and about
  0 prior-only inside any package.
- **Without Saka the wildcard is marginal.** The best Rogers package (R1)
  scores **+7.523 / +3.213** and clears the gate by 1.5, but about 1.6 of
  that comes from Richards → Silva, whose prior-only sign flips (−1.28) — the
  same kind of move the red-team's F1 objected to. Every Rogers package found
  that clears the gate has one such sign flip; the best one without (R5,
  +5.894) fails the gate by 0.11. The plain "F1 minus
  Raya→Trafford, Groß → Rogers" version scores +4.856 and **fails** the gate.
- **Recommendation: hold the wildcard and bank the free transfer** (2 free
  transfers at GW9). If the user wants Rogers now regardless, R1 is the
  package to play (see § 4).

## 1. Team attack

Goals from data/raw/gw8/fixtures.json; xG = sum of player xG in the
event-live snapshots. League average: 1.45 goals and 1.51 xG per team per
match. Σλ_att = the fixture model's expected goals summed over GW8–13
(data/analysis/gw8/fixtures.json); ATT rank is on that sum.

| Club | Goals (7) | Goals/match | rank | Goals/match last 5 | rank | xG/match | rank | xG/match last 5 | rank | Σλ_att GW8–13 | ATT rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MCI | 19 | 2.71 | 2 | 2.60 | 2 | 2.20 | 1 | 2.13 | 1 | 10.85 | 1 |
| ARS | 11 | 1.57 | 5 | 1.40 | 7 | 1.71 | 6 | 1.81 | 4 | 10.40 | 2 |
| CHE | 17 | 2.43 | 3 | 2.00 | 3 | 1.43 | 12 | 0.94 | 20 | 10.09 | 3 |
| LIV | 9 | 1.29 | 10 | 1.00 | 16 | 1.57 | 9 | 1.25 | 14 | 9.72 | 4 |
| BHA | 23 | 3.29 | 1 | 3.20 | 1 | 2.18 | 2 | 2.01 | 2 | 9.62 | 5 |
| BOU | 9 | 1.29 | 9 | 1.40 | 6 | 1.77 | 3 | 1.92 | 3 | 9.41 | 6 |
| CRY | 9 | 1.29 | 12 | 1.60 | 5 | 1.35 | 14 | 1.40 | 10 | 9.35 | 7 |
| BRE | 13 | 1.86 | 4 | 1.80 | 4 | 1.74 | 4 | 1.31 | 12 | 9.15 | 8 |
| NFO | 5 | 0.71 | 20 | 0.60 | 20 | 1.68 | 7 | 1.72 | 6 | 8.79 | 9 |
| MUN | 10 | 1.43 | 7 | 1.00 | 14 | 1.71 | 5 | 1.01 | 18 | 8.58 | 10 |
| LEE | 9 | 1.29 | 11 | 1.40 | 9 | 1.43 | 13 | 1.61 | 7 | 8.49 | 11 |
| AVL | 7 | 1.00 | 16 | 1.40 | 10 | 1.21 | 16 | 1.56 | 9 | 8.46 | 12 |
| IPS | 11 | 1.57 | 6 | 1.40 | 8 | 1.54 | 10 | 1.38 | 11 | 8.29 | 13 |
| SUN | 6 | 0.86 | 17 | 0.80 | 19 | 1.52 | 11 | 1.58 | 8 | 7.78 | 14 |
| TOT | 6 | 0.86 | 18 | 1.20 | 12 | 1.07 | 18 | 1.16 | 16 | 7.48 | 15 |
| EVE | 8 | 1.14 | 13 | 1.00 | 17 | 1.32 | 15 | 1.30 | 13 | 7.37 | 16 |
| FUL | 7 | 1.00 | 15 | 1.00 | 15 | 1.57 | 8 | 1.74 | 5 | 7.23 | 17 |
| NEW | 10 | 1.43 | 8 | 1.20 | 11 | 1.16 | 17 | 1.17 | 15 | 7.20 | 18 |
| COV | 6 | 0.86 | 19 | 1.20 | 13 | 1.03 | 19 | 1.13 | 17 | 6.96 | 19 |
| HUL | 8 | 1.14 | 14 | 1.00 | 18 | 0.98 | 20 | 1.01 | 19 | 6.31 | 20 |

What this says:

- **Brighton and Man City** are high-scoring on every measure: goals and xG,
  season and last 5. Man City also have the best fixtures (ATT rank 1);
  Brighton's are 5th.
- **Chelsea** score a lot (3rd) but create little: 1.43 xG a game this
  season (12th) and 0.94 over the last five (20th). Twelve goals from 4.7
  xG over GW3–7. The fixture model still rates their GW8–13 attack 3rd,
  because it is prior-weighted and their opponents are soft (TOT, MUN, SUN,
  LEE, NFO, CRY). Expect fewer goals than lately.
- **Brentford** are 4th on goals and 4th on season xG, but their last-5 xG
  (1.31) is 12th, and the fixture model rates their GW8–13 attack 8th.
- **Bournemouth** create well (3rd on xG) and finish poorly; we already own
  Tavernier. **Arsenal** are 2nd on fixtures and 4th on last-5 xG.
- Nottingham Forest are the opposite of Chelsea: 7th on xG, last on goals.

## 2. Midfield shortlist

xG+xA per 90 needs at least 180 minutes in the window ("–" otherwise).
"Club share" = the player's share of his club's xG+xA, season / last 5.
"Pts (returns)" = season points and the number of games with a goal or
assist. EP6 from players-MID.json (blend) and the objective's prior-only
view. `p` = start probability for GW8.

| Player | Club | £m | Status | Starts, mins | Pts (returns) | G/A | xG/xA | xGI/90 | xGI/90 last 5 | Club share | EP6 blend | EP6 prior | p | Owned % |
|---|---|---:|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| **Rogers** | CHE | 8.0 | a | 7/7, 610 | 40 (5) | 4/1 | 2.07/1.36 | 0.51 | 0.25 | 22% / 15% | 24.66 | 22.48 | 0.94 | 48.8 |
| Palmer | CHE | 9.8 | a | 7/7, 619 | 38 (4) | 2/4 | 1.44/0.92 | 0.34 | 0.22 | 15% / 14% | 25.11 | 28.28 | 0.95 | 27.4 |
| Neto | CHE | 6.5 | a | 6/7, 504 | 34 (3) | 3/1 | 1.21/0.88 | 0.37 | 0.27 | 13% / 16% | 22.27 | 22.69 | 0.94 | 3.0 |
| **Groß** (held) | BHA | 6.2 | a | 7/7, 610 | 58 (5) | 3/6 | 2.16/1.16 | 0.49 | 0.60 | 15% / 21% | 23.74 | 22.93 | 0.94 | 45.8 |
| Gibbs-White | NFO | 7.9 | a | 6/7, 540 | 30 (2) | 1/2 | 1.65/1.87 | 0.59 | 0.62 | 18% / 18% | 25.40 | 24.20 | 0.88 | 11.7 |
| Ødegaard | ARS | 6.8 | a | 7/7, 556 | 33 (2) | 2/0 | 1.90/1.60 | 0.57 | 0.67 | 17% / 19% | 24.36 | 22.86 | 0.93 | 18.4 |
| Stach | LEE | 6.0 | a | 7/7, 627 | 31 (1) | 1/0 | 1.37/0.52 | 0.27 | 0.33 | 14% / 15% | 25.23 | 23.57 | 0.95 | 2.3 |
| Lewis-Potter | BRE | 5.5 | a | 7/7, 548 | 33 (3) | 2/1 | 1.40/0.86 | 0.37 | 0.30 | 12% / 11% | 20.03 | 19.38 | 0.90 | 1.8 |
| Anthony | BRE | 5.9 | a | 5/7, 427 | 22 (2) | 1/1 | 1.43/0.56 | 0.42 | 0.38 | 10% / 13% | 18.23 | 17.72 | 0.80 | 0.3 |
| Schade (held) | BRE | 6.2 | a | 6/7, 543 | 40 (3) | 3/2 | 1.93/0.34 | 0.38 | 0.36 | 12% / 14% | 20.46 | 21.24 | 0.80 | 14.4 |
| B.Fernandes | MUN | 11.8 | a | 7/7, 630 | 33 (1) | 3/1 | 2.66/1.50 | 0.59 | 0.26 | 21% / 14% | 31.31 | 32.46 | 0.96 | 27.8 |
| Cherki | MCI | 8.0 | a | 5/7, 392 | 44 (4) | 4/2 | 1.30/1.70 | 0.69 | 0.51 | 11% / 9% | 18.00 | 18.48 | 0.60 | 38.5 |
| Foden | MCI | 6.8 | a | 4/7, 293 | 18 (2) | 1/2 | 2.23/1.42 | 1.12 | – | 13% / 11% | 21.84 | 19.40 | 0.72 | 2.3 |
| *Mbeumo (held)* | MUN | 7.9 | a | 7/7, 630 | 41 (4) | 4/1 | 3.96/0.90 | 0.69 | 0.43 | 25% / 23% | 30.43 | 27.97 | 0.96 | 21.1 |
| *Tavernier (held)* | BOU | 6.2 | a | 7/7, 574 | 42 (4) | 4/0 | 2.89/1.12 | 0.63 | 0.74 | 20% / 22% | 26.95 | 26.72 | 0.93 | 11.1 |

Points per round, GW1–7: Rogers 8, 5, 6, 8, 2, 9, 2 · Palmer 13, 7, 1, 5, 2,
8, 2 · Groß 2, 13, 1, 17, 14, 6, 5 · Gibbs-White 2, 13, 3, 8, 2, 2, 0 ·
B.Fernandes 2, 23, 2, 2, 2, 1, 1 · Ødegaard 11, 3, 10, 3, 2, 1, 3.

### Per-GW EP (blend) with opponent

| Player | GW8 | GW9 | GW10 | GW11 | GW12 | GW13 | EP6 |
|---|---|---|---|---|---|---|---:|
| Rogers | TOT(H) 4.08 | MUN(H) 4.19 | SUN(A) 4.11 | LEE(H) 4.05 | NFO(A) 3.72 | CRY(H) 4.52 | 24.66 |
| Palmer | TOT(H) 4.13 | MUN(H) 4.28 | SUN(A) 4.18 | LEE(H) 4.12 | NFO(A) 3.75 | CRY(H) 4.64 | 25.11 |
| Neto | TOT(H) 3.69 | MUN(H) 3.78 | SUN(A) 3.70 | LEE(H) 3.66 | NFO(A) 3.38 | CRY(H) 4.06 | 22.27 |
| Groß | LIV(A) 3.62 | MCI(A) 3.69 | BRE(H) 4.09 | HUL(A) ± 4.21 | NEW(H) 4.46 | BOU(A) 3.67 | 23.74 |
| Gibbs-White | IPS(A) ± 4.39 | BRE(A) 4.05 | MCI(H) 4.17 | BOU(A) 3.85 | CHE(H) 4.44 | HUL(A) ± 4.49 | 25.40 |
| Ødegaard | EVE(H) 4.19 | LIV(A) 3.64 | HUL(H) ± 4.54 | NEW(A) 4.18 | MCI(H) 3.95 | BRE(A) 3.86 | 24.36 |
| Stach | SUN(A) 4.28 | BOU(A) 3.98 | TOT(H) 4.30 | CHE(A) 4.14 | COV(H) ± 4.57 | MCI(A) 3.97 | 25.23 |
| Lewis-Potter | HUL(A) ± 3.56 | NFO(H) 3.33 | BHA(A) 3.23 | EVE(H) 3.52 | MUN(A) 3.29 | ARS(H) 3.10 | 20.03 |
| B.Fernandes | BOU(H) 5.09 | CHE(A) 5.13 | AVL(H) 5.46 | LIV(A) 4.69 | BRE(H) 5.42 | NEW(A) 5.52 | 31.31 |

### Reading the shortlist

- **Rogers** is the strongest Chelsea case: nailed, the steadiest points
  record on the list (returns in 5 of 7, never below 2), 22% of Chelsea's
  attack, near-template ownership (48.8%, so low rank risk). Against: his
  last-5 xG+xA per 90 halved to 0.25, and Chelsea's recent goals run well
  ahead of their chances.
- **Palmer** has the best prior (penalties, long record) but this season's
  underlying numbers are modest (0.34, then 0.22 per 90), and at £9.8m he
  forces two or three downgrades elsewhere. No Palmer package clears the
  gate.
- **Brentford**: no midfielder above EP6 20.5. Not a source this window.
- **Man City** midfielders fail on minutes: Cherki p 0.60, Foden p 0.72.
- **B.Fernandes** has the top EP6 (31.31 / 32.46) but would need £3.2m more
  than F1's frame frees; the only legal packages found sell Gabriel for a
  promoted-club defender or swap him in for Mbeumo. He also has one return
  in seven (a 23-point haul, then 1–2 points six times), which is not the
  S8 profile.
- **Ødegaard** cannot join with Raya, Gabriel and Calafiori (4 Arsenal).
- **Gibbs-White** has the best underlying numbers of the buyable options
  and the better package (§ 3), but Forest are the league's lowest scorers
  (0.71 goals a game) and his points are lumpy. He fails the user's
  "high-scoring club" test and S8.
- **S8 fit** (nailed, steady returns, consistent club): Groß and Rogers
  fit best; Palmer next. Gibbs-White, B.Fernandes, Stach (1 return in 7) and
  the Man City pair do not.

## 3. Packages

All with `--chip wildcard`, Raya kept, Saka not bought. "Bank" is on the
GW7-verified basis. All rows are legal: 2 GKP / 5 DEF / 5 MID / 3 FWD, cost
≤ 99.1, no club above 3 (Arsenal at 3 wherever Calafiori comes in: Raya,
Gabriel, Calafiori).

### 3a. The user's frame: F1 minus Raya → Trafford, minus Groß → Saka

F1's other moves kept: Dubravka → Kinsky, Tarkowski → Calafiori, Shaw →
Justin, Schade → Gomez, Thiago → Wissa. Removing the two moves leaves £2.7m
in the bank with Groß kept.

| Groß's slot | Blend | Prior | Bank | Legal | Gate |
|---|---:|---:|---:|---|---|
| keep Groß | +3.617 | +3.956 | 2.7 | yes | FAIL |
| → Rogers | +4.856 | +4.383 | 0.6 | yes | FAIL |
| → Gibbs-White | +5.377 | +5.484 | 0.7 | yes | FAIL |
| → Stach | +5.059 | +4.702 | 2.6 | yes | FAIL |
| → Neto | +3.361 | +4.521 | 2.1 | yes | FAIL |
| → Lewis-Potter | +2.766 | +3.325 | 3.1 | yes | FAIL |
| → Palmer | +5.271 | +9.310 | −1.2 | no (budget) | — |
| → B.Fernandes | +11.258 | +14.326 | −3.2 | no (budget) | — |
| → Ødegaard | +4.384 | +4.182 | 1.8 | no (4 ARS) | — |

Nothing in the plain frame clears the gate. To clear it the package has to
be re-funded and widened.

### 3b. Re-funded packages, ranked by blend

A grid over the frame's slots (GK2: keep / Kinsky / Suzuki; Tarkowski:
keep / Calafiori / Silva / Hill; Thiago: keep / Wissa / Calvert-Lewin /
João Pedro / Wood / Mateta; Groß and Schade slots: keep / any of 19 MIDs;
Shaw → Justin fixed), then a local search over the whole squad (Raya kept,
Saka banned). Every figure below is from the CLI.

| # | Package (moves) | Blend | Prior | Bank | Gate (≥ 6.0 / ≥ 0) | Sign-flip components (prior) |
|---|---|---:|---:|---:|---|---|
| X1 | Tarkowski → Calafiori, Groß → Stach, Thiago → **Isak**, Richards → Silva, Schade → Gomez, Shaw → Justin | +9.338 | +3.626 | 0.1 | PASS (+3.34) | Richards → Silva −1.269 |
| K1 | **Groß kept**: Tarkowski → Calafiori, Thiago → Wissa, Dubravka → Trafford, Richards → Murillo, Schade → Stach, Shaw → Silva | +8.330 | +2.612 | 0.1 | PASS (+2.33) | Richards → Murillo −0.935 |
| G1 | Tarkowski → Calafiori, Groß → **Gibbs-White**, Thiago → Wissa, Richards → Silva, Schade → Stach, Shaw → Justin | +8.020 | +4.354 | 0.1 | PASS (+2.02) | Richards → Silva −1.031 |
| **R1** | Tarkowski → Calafiori, Groß → **Rogers**, Thiago → Wissa, Richards → Silva, Schade → Stach, Shaw → Justin | **+7.523** | **+3.213** | 0.0 | PASS (+1.52) | Richards → Silva −1.279; Groß → Rogers −0.112 |
| R2 | **Groß kept**, Schade → **Rogers**, Tarkowski → Calafiori, Thiago → Wissa, Richards → Silva, Shaw → Justin | +6.831 | +2.760 | 0.1 | PASS (+0.83) | Richards → Silva −1.438 |
| R4 | Shaw → Justin, Dubravka → Suzuki, Tarkowski → Silva, Thiago → Wissa, Groß → Rogers, Schade → Stach | +6.468 | +2.799 | 0.1 | PASS (+0.47) | Tarkowski → Silva −1.941 |
| R3 | Tarkowski → Calafiori, Groß → Stach, Thiago → Wissa, Richards → Muharemović, Schade → **Rogers**, Shaw → Justin | +6.159 | +3.550 | 0.0 | PASS (+0.16) | Richards → Muharemović −0.942 |
| R5 | Shaw → Justin, Tarkowski → Calafiori, Thiago → Wissa, Groß → Rogers, Schade → Stach | +5.894 | +4.492 | 0.1 | FAIL (−0.11) | Groß → Rogers −0.004 |
| P1 | Shaw → Justin, Tarkowski → Silva, Thiago → Wissa, Groß → **Palmer**, Schade → Gomez | +5.033 | +6.757 | 0.3 | FAIL (−0.97) | Tarkowski → Silva −1.959 |
| P2 | best Palmer found (Silva, Vušković, Gomez, Wissa, Justin) | +5.460 | +5.597 | 0.1 | FAIL (−0.54) | — |
| ref | F1 (Saka + Trafford, red-team) | +9.537 | +8.627 | 0.0 | PASS (+3.54) | none |

Notes:

- Rogers' own marginal inside R1 is **+0.614 blend / −0.112 prior**; inside
  R2 (Schade → Rogers, Groß kept) +1.546 / +0.519. Most of R1's gain comes
  from Tarkowski → Calafiori (+1.78), Richards → Silva (+1.63), Schade →
  Stach (+1.32) and Shaw → Justin (+0.80).
- R1, G1, R2, R3, R5 and X1 keep **Dubravka** (p 0.03) as the backup keeper.
  That is a dead bench slot for auto-subs and for the GW19 bench-boost
  earmark. Repairing it (→ Kinsky, £0.5m) breaks the budget in R1.
- K1 and X1 are not what the user asked for: K1 buys no new attacking
  midfielder, and X1's gain comes from Isak (LIV forward, p 0.88, MED) with
  Stach and Gomez in midfield.
- Promoted-club defenders (Thomas COV, Diop/Walton IPS) were excluded from
  the searches above; including them adds up to about +0.2 blend at a large
  prior-only cost.

### 3c. Best no-wildcard option

Single free transfer (`objective --gw 8 --free-transfers 1`, same basis): no
move passes the free-transfer gate (blend ≥ 2.0, prior ≥ 0), so the
no-chip plan is **bank** (+0.000 / +0.000), 2 free transfers at GW9.

| Best singles | Blend | Prior | Bank | Gate |
|---|---:|---:|---:|---|
| Richards → Silva | +2.301 | −1.562 | 0.3 | fails (prior flip) |
| Schade → Stach | +1.764 | +0.894 | 0.6 | fails (< 2.0) |
| Tarkowski → Calafiori | +1.711 | +0.272 | 0.5 | fails (< 2.0) |
| Shaw → Justin | +1.439 | +2.019 | 0.2 | fails (< 2.0) |
| Groß → Stach | +1.382 | +0.535 | 0.3 | fails (< 2.0) |
| Schade → Neto | +0.428 | +0.538 | 0.1 | fails |

Rogers and Palmer are not affordable as a single free transfer (Schade
£6.2m + bank £0.4m = £6.6m). As a rough value for holding: the best pair of
moves made with 2 free transfers at GW9 is worth about +2.7 to +3.1 blend
over GW9–13 (e.g. Richards → Silva + Shaw → Justin +3.10 / +0.80, or Thiago
→ João Pedro + Schade → Stach +2.71 / +0.72), and keeps the wildcard.

### 3d. Team EP per gameweek

Best XI + captain each week from the 15 (the objective's own functions).

**Blend**

| Squad | GW8 | GW9 | GW10 | GW11 | GW12 | GW13 | 6-GW | vs current |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Current, no moves | 53.64 | 54.94 | 56.86 | 55.76 | 53.16 | 53.70 | 328.05 | — |
| F1 (reference, Saka) | 54.51 | 55.47 | 59.92 | 56.75 | 55.19 | 55.76 | 337.59 | +9.54 |
| X1 (Isak) | 55.79 | 55.52 | 59.07 | 56.80 | 54.39 | 55.82 | 337.39 | +9.34 |
| G1 (Gibbs-White) | 56.05 | 55.81 | 58.38 | 56.05 | 54.20 | 55.58 | 336.07 | +8.02 |
| **R1 (Rogers)** | 55.73 | 55.95 | 58.38 | 56.05 | 53.85 | 55.61 | 335.57 | +7.52 |
| R2 (Rogers, Groß kept) | 55.23 | 55.95 | 58.22 | 56.12 | 53.75 | 55.61 | 334.88 | +6.83 |
| R0 (frame + Groß → Rogers) | 55.17 | 55.30 | 58.04 | 55.62 | 53.45 | 55.33 | 332.91 | +4.86 |

**Prior-only**

| Squad | GW8 | GW9 | GW10 | GW11 | GW12 | GW13 | 6-GW | vs current |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Current | 52.68 | 53.23 | 55.12 | 54.06 | 51.34 | 52.08 | 318.51 | — |
| F1 (reference) | 53.44 | 53.66 | 57.47 | 54.75 | 53.94 | 53.89 | 327.14 | +8.63 |
| X1 | 53.42 | 52.53 | 56.64 | 54.45 | 52.15 | 52.96 | 322.14 | +3.63 |
| G1 | 54.28 | 53.38 | 56.28 | 53.47 | 52.14 | 53.32 | 322.87 | +4.35 |
| **R1** | 53.85 | 53.32 | 56.28 | 53.47 | 51.71 | 53.10 | 321.73 | +3.21 |
| R2 | 53.44 | 53.32 | 56.16 | 53.63 | 51.63 | 53.09 | 321.27 | +2.76 |

Captains (all packages): Haaland GW8, 9, 11, 13; Gabriel GW10 (HUL(H) ±);
Mbeumo GW12.

R1's GW8 XI (3-5-2, 55.73): Raya; Gabriel, Calafiori, Silva; Mbeumo,
E.Le Fée, Tavernier, Stach, Rogers; Haaland (C), Wissa. Bench: Dubravka
(dead), Justin, Barry, Van Hecke. Of R1's +7.52, +2.09 lands in GW8 and
+5.43 in GW9–13.

## 4. Recommendation

**Hold the wildcard this week and bank the free transfer.** With Saka out
and Raya kept, the wildcard's case rests on four mid-sized defensive and
funding moves, not on the midfielder the user wants:

- Rogers adds only +0.6 blend and −0.1 prior-only inside the best package
  (R1). He is a like-for-like swap for Groß, who is already the steady
  high-scoring-club midfielder S8 asks for.
- The packages that clear the gate comfortably either use Richards → Silva
  or Richards → Murillo (prior-only sign flips, the red-team's F1 objection)
  or are not midfielder moves at all (X1's Isak, K1). The best Rogers
  package with no sign flip (R5) fails the gate (+5.89); R3, which swaps
  Silva for Muharemović, still has a flip (−0.94) and clears by only 0.16.
- R1's edge over holding is roughly +7.5 against about +3 from two free
  transfers at GW9, i.e. about +4.5 over six weeks for the chip. The 6.0
  gate is meant to price the chip's future value; R1 clears it only on
  blend, and on prior-only R1 is +3.2.
- Set-1 wildcard runs to GW19. Holding keeps it for a fixture swing or for
  Saka once fit.

If the user plays the wildcard anyway, the package is **R1**:
`--moves 229:8,124:40,106:464,202:566,94:335,423:332` (+7.523 / +3.213,
bank 0.0, PASS). Its **strongest risk** is that the gate is cleared by
Richards → Silva (+1.629 blend / −1.279 prior): Silva has 630 Premier League
minutes and a league-average prior, so if his form premium fades the
package falls to about R5 (+5.89, below the gate). Secondary risks:

- Chelsea's goals are well ahead of their chances (12 from 4.7 xG over
  GW3–7), and Rogers' last-5 xG+xA per 90 is down to 0.25.
- Dubravka stays as a dead backup keeper.
- Arsenal at 3 (Raya, Gabriel, Calafiori): one bad Arsenal week hits three
  players.

If the user wants the best pure-EP wildcard with Raya kept and no Saka,
that is X1 (+9.34 / +3.63), but it buys Isak (p 0.88) rather than a
high-scoring-club midfielder, and still carries the Silva sign flip.

## Method and caveats

- Scratch scripts (not in the repo):
  /private/tmp/claude-501/-Users-gokul-Dev-Personal-fpl-system/70f77343-52e6-47bb-b22d-13a23da3a7fe/scratchpad/
  `mid_team.py`, `mid_short.py`, `grade_lib.py`, `enum.py`, `ls.py`,
  `frame.py`, `pergw_mid.py`, `hold.py`, `finalists.txt`. They call
  `fpl.objective` (`load_views`, `evaluate_plan`, `_points`,
  `best_lineup`, `legal_singles`) on the cached data; local only.
- Every package figure in § 3b was re-run through
  `uv run python -m fpl objective --gw 8 --sell <basis> --bank 0.4 --chip wildcard --moves …`.
- The local search is a heuristic (single and pair swaps from several
  starts); it is not a proof that no better package exists.
- The hold estimate scores GW9–13 with today's EP files; it ignores price
  changes and new information by GW9.
- Club xG is the sum of player xG in the event-live files and ignores
  own goals; transferred players are counted at their current club.
