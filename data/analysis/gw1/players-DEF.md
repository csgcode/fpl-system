# GW1 — Defender expected points (GW1–GW6)

Season 2026/27 | GW1 deadline 2026-08-21T17:30:00Z | 198 defenders scored
Inputs: `data/raw/gw1/bootstrap.json`, `data/raw/gw1/prior-season.json`,
`data/analysis/gw1/fixtures.md` (λ_att, λ_def, P(CS), ATT index), `flags`
refreshed 2026-08-21 13:45 UTC. `data/retro/` empty — no calibration
corrections available.

Machine-readable output: `data/analysis/gw1/players-DEF.json` (all 198).

**Revision 2** — attack multiplier corrected to divide out the club's own attack
index (see *Attack multiplier correction* below). All other terms unchanged.

## Regime and inherited caveats

**PRE-SEASON.** Every bootstrap aggregate is last season's. `form` is 0.0 for all
600 players and was ignored. `history` in every element summary is empty, so no
current-season signal exists — GW1 is 100% prior.

Caveats carried forward from `fixtures.md` and how they were handled:

| Caveat | Handling |
|---|---|
| Defensive ratings assumption-grade; mid-table P(CS) gaps < 4pp are noise | P(CS) used as given, but every pick below is reported with its **floor share** — the fraction of EP that does not depend on P(CS). Prefer high-floor picks while this holds. |
| COV / HUL / IPS HIGH uncertainty, no PL GK/DEF minutes | All 30 of their defenders flagged HIGH. Their own P(CS) is unusable, and it also inflates the GW1 numbers of the clubs facing them (ARS, MUN). |
| Cup / European rotation not modelled anywhere in the ticker | Priced into `p_start` directly: MCI, CHE, TOT, MUN, LIV capped at 0.85–0.90 max. ARS is the exception — injuries force a settled back four. |
| CRY λ_att overstated ~15% if the finishing underperformance is a squad trait | CRY picks below (Richards, Canvot) are DefCon-led, not attack-led, so this bites their ceiling, not their floor. Muñoz and Mitchell are exposed to it. |

## Model

```
EP = 2·P(60') + P(start)−P(60') + P(sub app)          appearance
   + xG90·6·A_fix·P(start)·E[90s]                     goals
   + xA90·3·A_fix·P(start)·E[90s]                     assists
   + 4·P(CS)·P(60')                                   clean sheet
   + 2·P(DefCon hit)·P(start)·g(minutes)              DefCon
   + bonus_per_app·P(app)                             bonus
   − E[⌊GC/2⌋ | Poisson(λ_def)]·P(start)·E[90s]       goals conceded
   − YC90·P(start)·E[90s] − 3·RC90·P(start)·E[90s]    cards

A_fix = λ_att / (1.439 · ATT_club)
```

### Attack multiplier correction

The A3 spec's `λ_att / 1.4` **double-counts the club's own attack strength.** A
player's observed xGI per-90 was earned inside his club's attack, so that
strength is already in the prior. `fixtures.md` builds λ_att as
`1.54 · ATT_i · DEFW_j` (home) or `1.33 · ATT_i · DEFW_j` (away), so dividing by
the league mean alone leaves `ATT_i` in the multiplier a second time.

Dividing by `1.439 · ATT_club` collapses the multiplier to exactly what it
should be — the home/away term times the opponent's leakiness:

```
A_fix (home) = (1.54 / 1.439) · DEFW_opp = 1.070 · DEFW_opp
A_fix (away) = (1.33 / 1.439) · DEFW_opp = 0.924 · DEFW_opp
```

ATT_club parsed from the `fixtures.md` team-ratings table (mean 1.00 verified):
MCI 1.39, CHE 1.37, ARS 1.28, BRE 1.21, LIV 1.18, MUN 1.16, CRY 1.14, BOU 1.13,
LEE 1.06, NEW 0.99, AVL 0.98, EVE 0.94, NFO 0.92, BHA 0.90, TOT 0.83, SUN 0.79,
FUL 0.75, IPS 0.70, COV 0.68, HUL 0.62.

**Effect on this position:** strong-club defenders lose EP (ARS −1.1 to −1.3,
MCI −1.5 to −2.3, CHE −1.0, LIV −0.7); defenders at clubs with ATT below 1.00
gain slightly (TOT +0.5, EVE +0.2, NEW ≈0). Only the goals and assists terms
move — CS, DefCon, bonus and the negatives are untouched. A useful side effect:
because the attack term shrinks most where it was largest, **floor share rises
across the top of the table**, so the ranking is now *less* exposed to the
provisional defensive ratings than it was before the correction.

### Rate shrinkage

Toward the DEF positional prior (xG90 0.0628, xA90 0.0605, CBIT/90 7.84,
bps/90 15.06, YC/90 0.178; n=71 starters ≥1500'): `w = m/(m+900)` for attacking
and bonus rates, `m/(m+600)` for CBIT (defensive rates carry far more signal per
minute), `m/(m+1200)` for cards. Attacking rates then decayed a further ×0.95.
Players who changed club in 2026 pulled an extra 25% toward the prior — their
output was earned in a different system.

Set-piece order fields are *current*-season duty, so an order-1 corner or
free-kick taker gets an xA90 **floor** of 0.085 rather than a multiplier. That
avoids double-counting duty already inside a continuing player's prior, while
still crediting takers with no attacking prior (Davis, Giles).

`goals conceded` uses the exact Poisson `E[⌊k/2⌋]` at the fixture's λ_def, not
λ_def/2. The naive halving overstates the penalty by 2–3× at typical λ.

### Two model calibrations performed

**1. DefCon mapping validated against a same-season back-solve.** Reconstructing
last season's non-DefCon points for every defender with ≥1800 minutes (n=62)
and reading the residual as DefCon points recovers each player's *observed*
per-match hit rate. Against the A3 spec mapping:

| CBIT/90 vs T=10 | spec mapping | back-solved (observed) | n | used |
|---|---|---|---|---|
| ≥ 1.3 × T | 0.85 | — (no observations) | 0 | 0.85 |
| 1.1 – 1.3 × T | 0.70 | 0.713 | 3 | **0.71** |
| ≈ T (0.95–1.1) | 0.55 | 0.550 | 10 | **0.55** |
| 0.85 – 0.95 × T | 0.35 | 0.406 | 12 | **0.38** |
| 0.70 – 0.85 × T | 0.20 | 0.279 | 15 | **0.24** |
| below 0.7 × T | ≤0.10 | 0.131 | 22 | **0.105** |

The mapping is well calibrated at and above the threshold and runs 5–8pp low
below it — expected, since a per-match step function rewards over-dispersion
that a per-90 average hides. Used values are shrunk **halfway** toward the spec
mapping, because the back-solve absorbs all reconstruction error (appearance
points and the goals-conceded floor-sum are approximated from season
aggregates), not only DefCon. Escalated for retro calibration.

**2. Bonus curve fitted, not assumed.** Regressing observed bonus per
appearance on bps/90 across defenders with ≥900 minutes (n=98) gives
`bonus/app = 0.0338·bps90 − 0.263`. 26/27 adjustment: CBI→BPS cut from 1/2 to
1/3 means `bps90_adj = bps90 − CBI90/6`, then ×0.92 for the shrinking share of
the defensive bonus pool (improved GK save BPS, no tackled penalty for
dribblers). Net effect on a typical CBI-heavy defender: −0.04 bonus per match,
≈ −0.25 over the window.

### Position stats caveat

Three current defenders were midfielders last season, so their
`defensive_contribution` field counts recoveries, which do **not** qualify for
the DEF threshold: **Wieffer** (BHA), **Sessegnon** (FUL), **Cardines** (CRY).
CBIT was recomputed from `clearances_blocks_interceptions + tackles` for every
player rather than trusting that field.

## Top 15 by EP6

`Δ` is the change from the uncorrected `λ_att / 1.435` multiplier; `rank Δ` is
the move in rank order.

| # | Player | Team | £ | p_start | EP6 | EP/£m | Δ EP6 | rank Δ | GW1→GW6 EP | Unc |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Gabriel | ARS | 8.0 | 0.93 | **26.92** | 3.37 | −1.08 | — | 5.31 4.21 3.93 4.61 4.38 4.48 | MED |
| 2 | Tarkowski | EVE | 6.0 | 0.93 | **23.58** | 3.93 | **+0.19** | ▲1 | 3.63 3.33 3.53 3.88 4.63 4.57 | LOW |
| 3 | Virgil | LIV | 6.5 | 0.93 | **23.54** | 3.62 | −0.66 | ▼1 | 3.68 4.15 4.43 4.51 3.46 3.31 | MED |
| 4 | Richards | CRY | 5.0 | 0.88 | **22.45** | **4.49** | −0.44 | ▲2 | 3.55 3.12 3.97 4.48 3.39 3.94 | MED |
| 5 | Thiaw | NEW | 5.0 | 0.88 | **22.34** | 4.47 | **+0.04** | ▲4 | 3.26 3.61 3.43 3.20 4.70 4.14 | LOW |
| 6 | Calafiori | ARS | 5.5 | 0.90 | **21.87** | 3.98 | −1.25 | ▼1 | 4.42 3.38 3.15 3.73 3.53 3.66 | MED |
| 7 | Lacroix | CHE | 6.0 | 0.85 | **21.64** | 3.61 | −0.95 | — | 3.86 3.83 2.85 4.55 3.06 3.48 | MED |
| 8 | Senesi | TOT | 6.0 | 0.90 | **21.43** | 3.57 | **+0.49** | ▲3 | 3.13 3.81 3.63 3.90 3.82 3.14 | MED |
| 9 | Hincapie | ARS | 5.5 | 0.85 | **21.30** | 3.87 | −0.65 | ▲1 | 4.23 3.33 3.06 3.68 3.47 3.53 | MED |
| 10 | O'Reilly | MCI | 6.5 | 0.80 | **20.95** | 3.22 | **−2.31** | **▼6** | 3.48 3.07 4.50 2.96 4.02 2.92 | MED |
| 11 | Guéhi | MCI | 6.0 | 0.85 | **20.92** | 3.49 | −1.45 | ▼3 | 3.45 3.08 4.39 3.01 4.01 2.97 | MED |
| 12 | Canvot | CRY | 5.0 | 0.80 | **20.41** | 4.08 | −0.41 | ▲1 | 3.22 2.83 3.60 4.08 3.08 3.58 | MED |
| 13 | Muñoz | CRY | 5.5 | 0.90 | **20.23** | 3.68 | −0.60 | ▼1 | 3.17 2.74 3.57 4.15 3.02 3.57 | MED |
| 14 | Botman | NEW | 5.0 | 0.75 | **19.46** | 3.89 | **+0.02** | ▲2 | 2.89 3.18 3.01 2.84 3.98 3.56 | MED |
| 15 | Dalot | MUN | 5.0 | 0.82 | **18.93** | 3.79 | −0.51 | — | 3.59 3.67 2.82 2.38 3.17 3.30 | MED |

Ranks 16–22: Collins (BRE 5.5) 18.91, Alderete (SUN 5.0) 18.80, N.Williams
(NFO 5.0) 18.43, Hill (BOU 5.5) 18.18, Struijk (BHA 5.0) 18.02, **Shaw (MUN 4.5)
17.96**, Hall (NEW 5.0) 17.72.

**What the correction changed at the top:** O'Reilly falls six places and out of
the top nine — his case was almost entirely a 6.12-prior-xG attacking bet
amplified by City's 1.39 attack index, and removing that double-count costs him
2.31 EP6, the largest single move in the position. Guéhi falls three. Thiaw rises
four and Senesi three purely because their clubs sit *below* the league attack
mean. Richards moves to 4th and keeps the best EP-per-million in the position.
Gabriel still leads, but his margin over 2nd narrowed from 3.80 to 3.34.

## Floor vs fixture-dependent EP

`fixtures.md` states outright that mid-table P(CS) is an artefact of a 5-level
tier prior. Ranking on total EP therefore ranks partly on noise. The floor —
appearance + DefCon + bonus — does **not** move when the split-strength fields
land and the defensive ratings get rewritten.

| Player | £ | EP6 | app | DefCon | bonus | **floor** | floor % | CS | attack | neg |
|---|---|---|---|---|---|---|---|---|---|---|
| Senesi | 6.0 | 21.4 | 10.5 | 5.9 | 1.0 | **17.5** | **82%** | 4.8 | 2.9 | −2.7 |
| Collins | 5.5 | 18.9 | 10.3 | 4.0 | 0.8 | **15.1** | **80%** | 4.7 | 2.7 | −2.6 |
| Tarkowski | 6.0 | 23.6 | 10.8 | 6.1 | 1.1 | **18.1** | **77%** | 5.8 | 3.3 | −2.4 |
| Lacroix | 6.0 | 21.6 | 10.0 | 5.6 | 1.0 | **16.6** | **77%** | 5.7 | 2.5 | −2.0 |
| Richards | 5.0 | 22.4 | 10.3 | 5.8 | 0.9 | **17.0** | **76%** | 5.4 | 3.1 | −2.3 |
| Canvot | 5.0 | 20.4 | 9.5 | 5.3 | 0.8 | **15.6** | **76%** | 4.9 | 2.9 | −2.1 |
| Botman | 5.0 | 19.5 | 8.8 | 5.0 | 0.9 | **14.6** | **75%** | 4.5 | 2.7 | −1.9 |
| Virgil | 6.5 | 23.5 | 10.8 | 4.2 | 1.1 | 16.2 | 69% | 6.5 | 3.6 | −2.1 |
| Muñoz | 5.5 | 20.2 | 10.3 | 2.3 | 1.4 | 14.1 | 69% | 5.3 | 4.2 | −2.2 |
| Thiaw | 5.0 | 22.3 | 10.3 | 4.0 | 0.8 | 15.1 | 68% | 5.5 | 4.7 | −2.3 |
| Guéhi | 6.0 | 20.9 | 10.0 | 2.4 | 1.5 | 13.9 | 67% | 6.1 | 3.7 | −1.9 |
| Gabriel | 8.0 | 26.9 | 10.8 | 4.2 | 2.2 | 17.3 | 64% | 8.1 | 3.8 | −1.5 |
| Hincapie | 5.5 | 21.3 | 10.0 | 2.4 | 1.2 | 13.6 | 64% | 7.4 | 2.3 | −1.4 |
| Dalot | 5.0 | 18.9 | 9.7 | 1.0 | 0.9 | 11.6 | 62% | 6.5 | 3.2 | −1.6 |
| Calafiori | 5.5 | 21.9 | 10.0 | 0.9 | 1.7 | 12.7 | 58% | 7.1 | 4.4 | −1.2 |
| O'Reilly | 6.5 | 20.9 | 9.5 | 1.0 | 1.5 | **12.0** | **57%** | 5.7 | 5.9 | −1.8 |

**Reading:** Senesi, Collins, Tarkowski, Lacroix, Richards, Canvot and Botman all
clear 75% floor — they hold their rank whichever way the defensive ratings move.
O'Reilly and Calafiori remain the two picks resting most on provisional inputs:
O'Reilly on a 6.12-prior-xG outlier, Calafiori on Arsenal's DEFW 0.70 and a 53%
GW1 P(CS) drawn from a promoted club with no PL defensive minutes.

## Value ladder — best three at each price point

| £ | 1st | 2nd | 3rd |
|---|---|---|---|
| 4.0 | Diop (IPS) 14.0 / 3.50 | Davis (IPS) 13.1 / 3.29 | van Ewijk (COV) 12.4 / 3.10 |
| 4.5 | **Shaw (MUN) 18.0 / 3.99** | Konsa (AVL) 17.2 / 3.83 | Mitchell (CRY) 17.1 / 3.80 |
| 5.0 | **Richards (CRY) 22.4 / 4.49** | **Thiaw (NEW) 22.3 / 4.47** | Canvot (CRY) 20.4 / 4.08 |
| 5.5 | **Calafiori (ARS) 21.9 / 3.98** | Hincapie (ARS) 21.3 / 3.87 | Muñoz (CRY) 20.2 / 3.68 |
| 6.0 | Tarkowski (EVE) 23.6 / 3.93 | Lacroix (CHE) 21.6 / 3.61 | Senesi (TOT) 21.4 / 3.57 |
| 6.5 | Virgil (LIV) 23.5 / 3.62 | O'Reilly (MCI) 20.9 / 3.22 | — |
| 8.0 | Gabriel (ARS) 26.9 / 3.37 | — | — |

**£5.0m is the efficiency sweet spot, and the correction widened its lead.**
Richards (4.49) and Thiaw (4.47) both beat every £5.5m, £6.0m and £6.5m defender
on EP per million, and Richards tops the whole position. Gabriel is the highest
total but the worst efficiency in the top 15 — his £2.5m premium over Calafiori
now buys 5.1 EP over six gameweeks. O'Reilly at 3.22 is the least efficient
non-injured defender priced above £5.0m.

## Nailed cheap beats rotating premium

Seventeen strict inversions — cheaper **and** higher p_start **and** higher EP6.
The correction created two new ones and, more importantly, turned O'Reilly from
a beneficiary into the position's most-beaten premium:

| Cheap + nailed | beats | by |
|---|---|---|
| Tarkowski (EVE) £6.0, p 0.93 | **O'Reilly (MCI) £6.5, p 0.80** | +2.63 EP6, −£0.5m |
| Richards (CRY) £5.0, p 0.88 | **O'Reilly (MCI) £6.5, p 0.80** | +1.50, −£1.5m |
| Thiaw (NEW) £5.0, p 0.88 | **O'Reilly (MCI) £6.5, p 0.80** | +1.39, −£1.5m |
| Calafiori (ARS) £5.5, p 0.90 | **O'Reilly (MCI) £6.5, p 0.80** | +0.92, −£1.0m |
| Senesi (TOT) £6.0, p 0.90 | **O'Reilly (MCI) £6.5, p 0.80** | +0.48, −£0.5m |
| Richards (CRY) £5.0, p 0.88 | Mukiele (SUN) £5.5, p 0.82 | +4.86, −£0.5m |
| Thiaw (NEW) £5.0, p 0.88 | Mukiele (SUN) £5.5, p 0.82 | +4.75, −£0.5m |
| Richards / Thiaw £5.0, p 0.88 | Kerkez (LIV) £5.5, p 0.82 | +5.96 / +5.85, −£0.5m |
| N.Williams (NFO) £5.0, p 0.88 | Mukiele £5.5 / Kerkez £5.5 | +0.84 / +1.94, −£0.5m |
| Shaw (MUN) £4.5, p 0.90 | Mukiele £5.5 / Kerkez £5.5 | +0.37 / +1.47, −£1.0m |
| Shaw (MUN) £4.5, p 0.90 | Hall (NEW) £5.0, p 0.80 | +0.24, −£0.5m |
| Konsa (AVL) £4.5, p 0.90 | Kerkez (LIV) £5.5, p 0.82 | +0.75, −£1.0m |
| Mitchell (CRY) £4.5, p 0.88 | Kerkez (LIV) £5.5, p 0.82 | +0.60, −£1.0m |
| Bassey (FUL) £4.5, p 0.88 | Kerkez (LIV) £5.5, p 0.82 | +0.16, −£1.0m |

The bigger pattern is the **Manchester City mid-block**, where FPL prices
rotation at premium rates — and where the corrected multiplier bites hardest,
since City's 1.39 attack index was inflating every one of them:

| MCI defender | £ | p_start | EP6 | Shaw (£4.5m, p 0.90, 17.96) beats him by |
|---|---|---|---|---|
| Matheus N. | 6.0 | 0.65 | 13.97 | **+3.99 EP6, −£1.5m** |
| Gvardiol | 5.5 | 0.52 | 13.24 | **+4.72 EP6, −£1.0m** |
| Rúben | 5.5 | 0.55 | 12.66 | +5.30, −£1.0m |
| Khusanov | 5.5 | 0.42 | 10.31 | +7.65, −£1.0m |
| Aït-Nouri | 5.5 | 0.35 | 8.20 | +9.76, −£1.0m |

Gvardiol at 10.9% ownership is the position's clearest trap: £5.5m for 1370
prior minutes and 16 starts inside a Pep back line with a UCL fixture load.
Only Guéhi and O'Reilly are worth paying MCI prices for at all, and after the
correction even they are beaten on EP-per-million by both £5.0m Palace/Newcastle
options. **Mitchell (CRY £4.5m) still out-scores 17 of the 24 £5.5m defenders**
— the seven above him are Calafiori, Hincapie, Muñoz, Collins, Hill, Mukiele
and Pedro Porro.

## £4.0–4.5m enablers and Bench Boost value

Every promoted-club defender is £4.0m and every one is flagged HIGH — none has
a single PL minute except Diop. The correction *helped* this group: COV 0.68,
HUL 0.62 and IPS 0.70 attack indices were suppressing their attacking term
before it was divided out.

| Player | Team | £ | p_start | EP6 | EP/£m | own% | Note |
|---|---|---|---|---|---|---|---|
| Diop | IPS | 4.0 | 0.80 | 13.99 | **3.50** | 18.3 | Only promoted-club DEF with PL minutes (812'). Best £4.0m by 0.85 EP6. |
| Davis | IPS | 4.0 | 0.70 | 13.14 | 3.29 | 5.3 | fk2 + cor2 — set-piece duty gives him an assist route the others lack. |
| van Ewijk | COV | 4.0 | 0.70 | 12.42 | 3.10 | 14.1 | Highest-owned COV defender. Zero PL minutes for any COV GK or DEF. |
| O'Shea | IPS | 4.0 | 0.65 | 11.89 | 2.97 | 3.4 | |
| Targett | HUL | 4.0 | 0.68 | 11.65 | 2.91 | 2.5 | Best HUL option; HUL own the league's worst defensive ticker (15% mean P(CS)). |
| Thomas | COV | 4.0 | 0.65 | 11.61 | 2.90 | 8.0 | |

**Diop at 3.50 EP/£m beats 62 defenders priced £5.0m or above** — the enabler
that costs the least real EP, and he now out-ranks the whole £4.0m tier on both
total and efficiency. If a fifteenth-defender slot must be £4.0m, Diop then
Davis, and stack IPS over COV over HUL exactly as the ticker ranks them. Note
the ordering between the three promoted clubs is explicitly labelled
non-confident in `fixtures.md` — a single result reverses IPS over HUL.

Genuine £4.5m starters clearing 16.5 EP6: **Shaw 17.96, Konsa 17.24,
Mitchell 17.09, Mykolenko 16.84, Maatsen 16.69, Bassey 16.65, Cash 16.52.**
**For Bench Boost the £4.5m tier, not the £4.0m tier, is where the value is:**
Shaw returns 17.96 against Diop's 13.99 for £0.5m more.

## Set-piece and penalty duty

**No defender is a first-choice penalty taker.** The only two with any penalty
order are Robinson (FUL, 2nd) and Matheus N. (MCI, 5th) — worth nothing.
The ~1–2 EP/GW penalty premium the spec flags does not exist in this position
this season.

Order-1 or order-2 corner / free-kick duty, which does matter:

| Player | Team | £ | Duty | prior xA | EP6 |
|---|---|---|---|---|---|
| N.Williams | NFO | 5.0 | fk2 + cor1 | 3.97 | **18.43** |
| Hall | NEW | 5.0 | fk1 + cor1 | 2.78 | 17.72 |
| Pedro Porro | TOT | 5.5 | fk1 + cor1 | 4.37 | 17.19 |
| Cash | AVL | 4.5 | cor1 | 2.94 | 16.52 |
| James | CHE | 5.5 | fk1 + cor1 | 3.20 | 15.83 |
| Davis | IPS | 4.0 | fk2 + cor2 | — | 13.14 |
| Giles | HUL | 4.0 | fk1 + cor1 | — | 10.94 |

James carries the highest expected bonus per appearance in the position (0.37,
on 22.7 prior bps/90) but is the one set-piece defender the correction punished
(Chelsea ATT 1.37, −1.02 EP6) — and 20 starts in 1957 minutes last season is why
he is p_start 0.70 and £5.5m rather than £6.5m. **N.Williams is now the clear
best combination of nailed minutes and set-piece duty**, and Porro overtakes
James on the back of Tottenham's below-average 0.83 attack index.

## Minutes model

`p_start` was set per club from the depth chart under a squad-total constraint —
the sum across each club's defenders must land near 4.0–4.6 for a back four,
~5.0 for a back three plus wing-backs. Constraint check at GW1:

| Club | Σ p_start | Club | Σ p_start | Club | Σ p_start | Club | Σ p_start |
|---|---|---|---|---|---|---|---|
| ARS | 3.95 | BRE | 3.95 | HUL | 4.43 | NEW | 3.95 |
| AVL | 4.27 | CHE | 4.43 | IPS | 4.30 | NFO | 4.30 |
| BHA | 4.40 | COV | 4.10 | LEE | 3.98 | SUN | 4.34 |
| BOU | 3.96 | CRY | **5.11** | LIV | 3.95 | TOT | 4.52 |
| | | EVE | 4.33 | MCI | 4.44 | MUN | 4.34 |
| | | FUL | 3.95 | | | | |

CRY is deliberately over 5.0 — Muñoz and Mitchell are wing-backs in a back-three
system, so five FPL-classified defenders start. TOT at 4.52 reflects four
centre-backs competing for two or three slots after three departures.

New signings with no PL history are capped at p_start 0.70 per the spec, and
their rates come from the positional prior: promoted-club defenders at
CBIT/90 ×1.15 (weaker sides defend more, which is a real DefCon floor) and
attacking rates ×0.60 (Championship output, discounted).

### Availability — modelled, not ignored

| Player | Team | £ | Status | Modelled p_start GW1→6 | EP6 |
|---|---|---|---|---|---|
| Andersen | FUL | 5.0 | **Suspended until 30 Aug** | 0, 0, 0.88, 0.88, 0.88, 0.88 | 12.62 |
| Fofana | CHE | 5.0 | **Suspended until 6 Sep** | 0, 0, 0, 0.35, 0.35, 0.35 | 4.34 |
| J.Timber | ARS | 6.5 | Groin injury, no return date | 0, 0, 0.10, 0.18, 0.22, 0.27 | 3.79 |
| Saliba | ARS | 6.0 | Back injury, no return date | 0, 0, 0.11, 0.19, 0.25, 0.30 | 3.65 |
| Jacob | HUL | 4.0 | Hip, back 29 Aug | 0, 0, 0.25, 0.30, 0.30, 0.30 | 3.44 |
| Van den Berg | BRE | 5.0 | Injury, no return date | return curve on 0.82 | 3.36 |
| De Ligt | MUN | 5.0 | Back injury, no return date | return curve on 0.60 | 2.72 |
| Gudmundsson | LEE | 4.5 | Hamstring, no return date | return curve on 0.78 | 2.35 |
| Livramento | NEW | 5.0 | Calf, no return date | return curve on 0.55 | 2.30 |
| Savona | NFO | 4.5 | Knee, no return date | return curve on 0.55 | 2.13 |
| Bradley, Gomez, Leoni | LIV | | injured, no return date | return curves | ≤2.0 |
| Milosavljević, J.Araujo | BOU | | injured, no return date | return curves | ≤1.6 |
| Hughes | HUL | 4.0 | Groin, no return date | return curve on 0.35 | 1.11 |

"No return date" cases are modelled with a graded return curve rather than
zeroed, so the optimizer sees their six-GW value without treating them as
selectable now — all are flagged HIGH and none exceeds 3.8 EP6. Andersen at
12.62 is the only entry here worth holding a slot for, and only from GW3.

**Departed / unavailable, EP 0 across the window — do not select:** Digne and
Nedeljkovic (AVL), Chalobah (CHE), Cardines (CRY), Bornauw (LEE), Alleyne (MCI),
Fredricson (MUN), A.Murphy (NEW), Masuaku and Hjelde (SUN), Romero, Spence and
Phillips (TOT). Thirteen of the 198 records.

## Escalations

1. **The attack-multiplier double-count was live in revision 1 of this file.**
   Corrected to `λ_att / (1.439 · ATT_club)` per the FWD analyst's finding. If
   the GKP or MID outputs still use `λ_att / league-mean`, their strong-club
   assets are overstated by the same mechanism — for defenders it was worth up
   to 2.31 EP6 (O'Reilly) and it reordered the top ten. Worth confirming
   cross-position before the optimizer consumes any of these files.

2. **The DefCon mapping in the A3 spec runs 5–8pp low below the threshold.**
   Back-solved from n=62 defenders on the same season the mapping approximates:
   0.70–0.85×T observed 0.279 vs mapped 0.20; 0.85–0.95×T observed 0.406 vs
   mapped 0.35. At and above the threshold it is exact. I used halfway-shrunk
   values. **Retro must resolve this** — it moves roughly 1.5 EP over six GWs
   for a mid-CBIT defender, which is enough to reorder the £4.5–5.0m tier. The
   correction in point 1 raises the stakes here: with the attack term smaller,
   DefCon is now a larger share of every ranking above.

3. **Arsenal have lost both first-choice centre-backs with no return dates**
   (Saliba, J.Timber). Five available senior defenders for four slots, so ARS
   minutes are the most locked in the league despite European commitments — and
   **Hincapie is 2.0% owned at £5.5m while the depth chart says he starts**
   (EP6 21.30, 9th in the position). That is the largest apparent market/model
   gap in the position. It is MED not LOW because he joined 2026-07-01 and the
   market may be reading a rotation it can see and I cannot.

4. **Gabriel's GW1 EP is 21% clean-sheet points from a fixture with no
   empirical basis.** COV(H) P(CS) 53% is the highest in the window and comes
   from a rating `fixtures.md` labels ASSUMPTION with zero PL minutes for any
   Coventry goalkeeper or defender. The same contamination inflates MUN GW1–2
   (HUL a 44%, IPS H 45%) — i.e. the two most attractive defensive fixtures in
   the window are the two least evidenced. Shaw at £4.5m is the cheap way to
   take that bet; Gabriel at £8.0m is the expensive way, and the corrected
   multiplier cut his attacking compensation from 4.9 to 3.8 EP6.

5. **Chelsea's defensive EP peaks at GW4, not GW1.** Lacroix's GW4 (HUL H,
   P(CS) 48%) EP of 4.55 is the second-highest single-gameweek defender figure
   in this file. If the optimizer intends a Chelsea defender, GW1 is not the
   entry point — GW3 (ARS away, P(CS) 17%, EP 2.85) is the trough to buy into.

6. **Everton and Newcastle confirmed as the cheap swing routes, and the
   correction strengthened both.** Tarkowski rose to 2nd overall and Thiaw to
   5th; Mykolenko (£4.5m) and Thiaw (£5.0m) capture the +15pp and +9pp defensive
   swings the ticker flagged, both turning at GW5. Thiaw's 4.47 EP/£m is 2nd in
   the position — the ticker's recommendation and the player model agree
   independently, and neither depends on a high club attack index.

7. **Club-limit collision at Palace.** Three CRY defenders sit in the top 13
   (Richards 4th, Canvot 12th, Muñoz 13th) and Mitchell is 28th. The
   max-3-per-club rule binds before the budget does, and CRY's λ_att is the one
   attacking rating `fixtures.md` flags as likely ~15% overstated — which hits
   attack-led Muñoz and Mitchell but not DefCon-led Richards and Canvot (76%
   floor each). Prefer Richards + Canvot if only two CRY slots are available.

8. **`selected_by_percent` was used as a depth-chart signal for promoted clubs
   only**, where every player is £4.0m and price carries no information. It is
   community expectation, not team news — a soft signal, and the sole separator
   between the ten Coventry and twelve Hull defenders.
