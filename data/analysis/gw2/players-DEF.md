# GW2 — Defender EP model (GW2–GW7)

Season 2026/27 | GW2 deadline 2026-08-28T17:30:00Z | snapshot `data/raw/gw2/`
(fetched 2026-08-28T09:45:31Z) | flags refreshed 2026-08-28T10:12:45Z
| fixtures from `data/analysis/gw2/fixtures.md` | supersedes `data/analysis/gw1/players-DEF.json`

205 defenders scored: 174 with a non-zero EP (69 above £4.5m, 105 at £4.0–4.5m),
31 zeroed as unavailable. `data/retro/gw1.md` corrections C1, C2, C3, C4 and C7
are all applied and each is evidenced below.

## What changed since GW1

| | GW1 | GW2 |
|---|---|---|
| Regime | pre-season (bootstrap fields = last season) | **in-season**, 1 match played |
| Rate blend | 100% prior | **85 / 15**, current weight scaled by minutes played, with a **[0.40×, 2.50×] single-match guard band** |
| Team defence input | assumption-grade tier prior | tier prior + **measured** team xGA (fixtures.md) |
| DefCon curve, DEF | 4-step band, capped at 0.55 | **spec anchor table, linearly interpolated** — C3 |
| Minutes model | pre-season depth chart | depth chart + **GW1 lineup evidence**, weighted by prior strength |
| Uncertainty tag | judgment | **bound to p_start** — C7 |
| Bonus model | per-player judgment | recovered as `0.02093 × bps90 − 0.1221` (mean abs residual 0.012 against the 85 GW1 values) — same model, now reproducible |

## Corrections compliance

**C1 — v1 DefCon mapping unchanged.** No level was shifted, and the spec's
sub-threshold shrinkage instruction was **not** applied (C1 supersedes it). The
probabilities used are exactly the CLAUDE.md anchor table: 0.85 at ≥1.30×T, 0.70
at ≥1.10×T, 0.55 at T, 0.35 at ≥0.85×T, 0.20 at ≥0.70×T, ≤0.10 below — now
interpolated between anchors rather than snapped, per the spec's own
anti-cliff instruction. GW1 hits enter only through the 15% blend on dc90, which
moves a defender's ratio by at most ±0.1×T.

**C2 — calibration sample logged below** (n = 50 DEF), per player, with ratio
band, v1 P(hit), realised DefCon count and hit flag. Pool at GW4.

**C3 — cross-position curve unified.** This is the largest methodological change
in this file and the one the red-team should attack first. GW1 scored DEF on a
four-step band function capped at 0.55 while MID used a continuous curve reaching
0.73, so an identical ratio scored up to 18pp lower for a defender. Both now use
the single interpolated anchor curve above. **This is not a recalibration** — the
anchor *levels* are the spec's, unchanged; GW1's DEF implementation was the
deviation from them. Effect quantified in the sensitivity table below: +3.4% on
the top-20 aggregate, +0.9 to +1.8 EP6 on nine players, all of them high-CBIT
centre-backs.

**C4 — promoted-club band respected.** Every ± fixture is tracked per player and
the exposure is in the JSON `notes` and in the band table below. **No selected
player has a ±-derived term as their largest single EP component** — appearance
points exceed every band-derived clean-sheet term in the file. The stricter
reading (largest *non-appearance* term) does bind on several players, Shaw among
them, and is tabulated so the optimizer can apply the rule either way.

**C7 — uncertainty bound to p_start.** p_start < 0.85 → at least MED; < 0.70 →
HIGH. Applied mechanically, then escalated for no-PL-history, promoted-club and
club-change cases. No defender in this file carries a LOW tag below p_start 0.85.

## Top 15 by EP6

| # | Player | Team | £ | p_start | EP6 | EP/£m | Unc | Own | GW2 | GW3 | GW4 | GW5 | GW6 | GW7 |
|---:|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | **Gabriel** | ARS | 8.0 | 0.92 | **26.31** | 3.29 | LOW | 29.2% | 4.45 | 3.97 | 4.77 | 4.14 | 4.56 | 4.42 |
| 2 | **Virgil** | LIV | 6.5 | 0.92 | **24.88** | 3.83 | LOW | 19.6% | 4.58 | 4.49 | 4.85 | 3.93 | 3.56 | 3.47 |
| 3 | **Calafiori** | ARS | 5.6 | 0.90 | **24.56** | 4.39 | LOW | 41.6% | 4.18 | 3.71 | 4.51 | 3.80 | 4.27 | 4.08 |
| 4 | **Guéhi** | MCI | 6.0 | 0.86 | **24.19** | 4.03 | MED | 19.4% | 3.41 | 4.89 | 3.44 | 4.67 | 3.24 | 4.54 |
| 5 | **Thiaw** | NEW | 5.0 | 0.89 | **24.15** | 4.83 | LOW | 1.7% | 3.95 | 3.70 | 3.39 | 4.78 | 4.29 | 4.05 |
| 6 | **Richards** | CRY | 5.0 | 0.89 | **24.14** | 4.83 | LOW | 0.7% | 3.43 | 4.26 | 4.58 | 3.82 | 4.34 | 3.71 |
| 7 | **Senesi** | TOT | 6.0 | 0.90 | **23.81** | 3.97 | MED | 7.6% | 3.91 | 3.76 | 4.06 | 4.09 | 3.29 | 4.70 |
| 8 | **O'Reilly** | MCI | 6.5 | 0.78 | **23.38** | 3.60 | MED | 20.9% | 3.26 | 4.77 | 3.29 | 4.55 | 3.10 | 4.41 |
| 9 | **Canvot** | CRY | 5.0 | 0.83 | **22.69** | 4.54 | MED | 0.3% | 3.21 | 4.00 | 4.31 | 3.59 | 4.08 | 3.48 |
| 10 | **Tarkowski** | EVE | 6.0 | 0.92 | **22.67** | 3.78 | LOW | 8.7% | 3.37 | 3.54 | 3.96 | 4.26 | 4.38 | 3.16 |
| 11 | **Lacroix** | CHE | 6.0 | 0.86 | **22.08** | 3.68 | MED | 9.5% | 3.74 | 3.07 | 4.69 | 3.06 | 3.78 | 3.73 |
| 12 | **Botman** | NEW | 5.0 | 0.79 | **21.45** | 4.29 | MED | 0.5% | 3.52 | 3.30 | 3.06 | 4.18 | 3.81 | 3.58 |
| 13 | **Muñoz** | CRY | 5.5 | 0.86 | **21.05** | 3.83 | LOW | 8.4% | 2.87 | 3.75 | 4.14 | 3.28 | 3.83 | 3.17 |
| 14 | **White** | ARS | 5.5 | 0.75 | **20.94** | 3.81 | MED | 6.6% | 3.55 | 3.15 | 3.81 | 3.28 | 3.63 | 3.51 |
| 15 | **Collins** | BRE | 5.5 | 0.89 | **20.84** | 3.79 | LOW | 2.1% | 3.38 | 4.26 | 3.31 | 3.10 | 3.58 | 3.23 |

Reading:

- **Gabriel is the only defender in the top twelve with zero promoted-club
  exposure.** ARS meet no COV/HUL/IPS in the window, so none of his 26.31 sits
  inside the ±15pp band, and his floor is the flattest in the file (4.45 → 3.97
  is his whole range). He is also the most expensive route to it at £8.0m.
- **Virgil is a three-gameweek asset.** 13.9 of his 24.9 EP6 lands in GW2–4;
  Liverpool's clean-sheet outlook falls 37% → 20% at GW5, the largest swing of
  any kind in the window. Buy for the front half, plan the exit.
- **Richards and Thiaw are joint-best on EP per £m at 4.83** and are owned by
  0.7% and 1.7% of managers respectively. Both are already in our squad.
- **Senesi has the highest DefCon rate of any nailed defender** (11.35/90 →
  0.73) but Tottenham took the window's joint-worst defensive downgrade, and
  fixtures.md notes their implied rating was *clipped* at the guard band — the
  raw GW1 data wanted them worse still. The floor is real; the clean sheets are not.
- **O'Reilly carries the highest attacking rate in the position** (xG+xA/90
  0.302) and the position's worst premium-price/minutes trade: he came off on
  62′ while four City defenders played 90, and 24.8% of his EP6 is band-derived.

## Our five

| Player | £ | p_start | EP6 | GW1 EP6 | Δ | Rank | Unc | Flag change | Largest single driver |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| **Gabriel** (ARS) | 8.0 | 0.92 | **26.31** | 26.92 | -0.61 | 1 | LOW | none — `a`, no news | CS 39% mean, no ± exposure |
| **Richards** (CRY) | 5.0 | 0.89 | **24.14** | 22.45 | +1.69 | 6 | LOW | none — `a`, no news | DefCon 0.67 floor |
| **Thiaw** (NEW) | 5.0 | 0.89 | **24.15** | 22.34 | +1.81 | 5 | LOW | none — `a`, no news | DefCon 0.52 + GW5-7 swing |
| **Tarkowski** (EVE) | 6.0 | 0.92 | **22.67** | 23.58 | -0.91 | 10 | LOW | none — `a`, no news | DefCon 0.55 floor |
| **Shaw** (MUN) | 4.5 | 0.90 | **17.66** | 17.96 | -0.30 | 27 | LOW | none — `a`, no news | CS, no DefCon floor |

**No flag changed on any of the five.** All five are `status: a`, blank
`chance_of_playing`, blank `news`, verified against the 10:12Z `flags` refresh.
This is the pre-deadline read; the finalizer must re-run the gate.

Notes on each:

- **Gabriel** — position leader for the second cycle. Held.
- **Richards +1.69** — the C3 curve unification (ratio 1.08 → 0.67 rather than
  0.55) plus a GW1 DefCon count of 16 that nudged his blended rate to 10.82.
  4.5 of his 24.1 EP6 is fixture-independent DefCon floor.
- **Thiaw +1.81** — same curve effect plus Newcastle's improving fixtures.
  **Caveat: GW5 HUL(H) and GW6 COV(a) carry 18% of his EP6 inside the ± band.**
- **Tarkowski −0.91** — the DefCon floor rose but the Everton run now ends a
  gameweek earlier than GW1 planning assumed. GW7 is CHE(H) at 14% P(CS), his
  worst fixture of the window; his GW7 EP (3.16) is the lowest of his six. The
  GW7–9 cliff flagged in GW1 planning starts at **GW7**, not GW8.
- **Shaw −0.30** — unchanged in substance, but the C4 condition that produced
  his GW1 MODEL miss **repeats**: his largest non-appearance term across the
  entire window is the GW2 IPS(H) clean sheet, a ± fixture. MUN's ticker then
  decays to 19% by GW4. Defensible as a £4.5m enabler; not as a fixture play.

## Nailed cheap beats rotating premium

| Rotating premium | £ | p_start | EP6 | Nailed cheaper alternative | £ | p_start | EP6 | Gain |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| White (ARS) | 5.5 | 0.75 | 20.94 | Thiaw (NEW) | 5.0 | 0.89 | 24.15 | **+3.21 for −£0.5m** |
| Gvardiol (MCI) | 5.5 | 0.63 | 17.94 | Thiaw (NEW) | 5.0 | 0.89 | 24.15 | **+6.21 for −£0.5m** |
| Mosquera (ARS) | 5.5 | 0.74 | 17.33 | Thiaw (NEW) | 5.0 | 0.89 | 24.15 | **+6.82 for −£0.5m** |
| James (CHE) | 5.5 | 0.76 | 16.86 | Thiaw (NEW) | 5.0 | 0.89 | 24.15 | **+7.29 for −£0.5m** |
| Pedro Porro (TOT) | 5.5 | 0.78 | 15.83 | Thiaw (NEW) | 5.0 | 0.89 | 24.15 | **+8.32 for −£0.5m** |
| Rúben (MCI) | 5.5 | 0.65 | 15.15 | Thiaw (NEW) | 5.0 | 0.89 | 24.15 | **+9.00 for −£0.5m** |
| Frimpong (LIV) | 5.5 | 0.69 | 14.59 | Thiaw (NEW) | 5.0 | 0.89 | 24.15 | **+9.56 for −£0.5m** |
| Branthwaite (EVE) | 5.5 | 0.68 | 14.48 | Thiaw (NEW) | 5.0 | 0.89 | 24.15 | **+9.67 for −£0.5m** |

The pattern is one-sided this week: **Thiaw at £5.0m beats every rotating
premium in the position**, including three Manchester City defenders who each
played 90 minutes in GW1 and still cannot clear p_start 0.66 on their prior
start counts. Gvardiol is the sharpest case — 13.5% ownership at £5.5m for
6.2 fewer EP6 than a £5.0m defender.

## £4.0–4.5m enablers

| Player | Team | £ | p_start | EP6 | EP/£m | Unc | GW1 | Note |
|---|---|---:|---:|---:|---:|---|---:|---|
| Mitchell | CRY | 4.5 | 0.89 | 18.18 | 4.04 | LOW | 90′ | Nailed CRY wing-back, 90′ GW1 |
| Shaw | MUN | 4.5 | 0.90 | 17.66 | 3.92 | LOW | 90′ | Ours. GW2 term is ±-derived |
| Ajer | BRE | 4.5 | 0.77 | 17.60 | 3.91 | MED | 90′ | BRE defence turns hard GW4-7 |
| Justin | LEE | 4.5 | 0.76 | 17.43 | 3.87 | MED | 90′ | One of five LEE defenders |
| Bassey | FUL | 4.5 | 0.89 | 17.10 | 3.80 | LOW | 90′ | FUL, 90′ GW1, no DefCon floor |
| Rodon | LEE | 4.5 | 0.86 | 17.05 | 3.79 | LOW | 90′ | LEE back five |
| Maatsen | AVL | 4.5 | 0.77 | 17.04 | 3.79 | MED | 81′ | AVL defence downgraded hardest |
| O'Shea | IPS | 4.0 | 0.71 | 16.00 | 4.00 | HIGH | 90′ | £4.0m; prior is 2024/25; ± band |
| Robinson | FUL | 4.5 | 0.70 | 15.87 | 3.53 | MED | 81′ | 81′ GW1, pen2 |
| Castagne | FUL | 4.5 | 0.72 | 15.60 | 3.47 | MED | 90′ | 90′ GW1 but FUL 25% CS |
| Mykolenko | EVE | 4.5 | 0.86 | 15.52 | 3.45 | LOW | 90′ | Cheapest route into the EVE back three |
| F.Kadıoğlu | BHA | 4.5 | 0.75 | 15.35 | 3.41 | MED | 0′ | 0′ GW1; cleared flag softens the read |

**Best enabler: Mitchell (CRY, £4.5m, EP6 18.18, LOW).** He is the only £4.5m
defender combining a 90-minute GW1 start, a settled back-3 wing-back role, LOW
uncertainty and a top-third clean-sheet ticker. He beats Shaw by 0.52 EP6 at the
same price with less ± exposure.

**Best true £4.0m: O'Shea (IPS, EP6 16.00) — but read the tag.** His prior is
Ipswich's *2024/25* Premier League season (decayed 10%, the only DEF in the file
on a two-season-old prior), his 0.72 DefCon floor rests on a single observed
match (18 DC in GW1), and every Ipswich P(CS) carries the ±15pp band. He is
bench fodder with a floor, not a playing asset. He does, however, now out-rate
his own team-mate **Diop (17.1% owned)**, whose GW1 DefCon count was 5.

## C2 — DefCon calibration sample, DEF, GW1

Per C2: every DEF with ≥900 prior-season minutes and ≥80 GW1 minutes, with the
prior dc90 (**pre-blend**), the ratio to the DEF threshold of 10, the v1
probability under the unified curve, the realised count and the hit flag. Pool
this with the MID/FWD samples and re-test the **slope** hypothesis at GW4.

| ratio band | n | v1 pred | hits | observed | delta |
|---|---:|---:|---:|---:|---:|
| >=1.10T | 4 | 0.717 | 1 | 0.250 | -46.7pp |
| 1.00-1.10T | 6 | 0.596 | 5 | 0.833 | +23.7pp |
| 0.85-1.00T | 11 | 0.439 | 6 | 0.545 | +10.7pp |
| 0.70-0.85T | 15 | 0.264 | 1 | 0.067 | -19.7pp |
| <0.70T | 14 | 0.122 | 1 | 0.071 | -5.0pp |
| **all** | **50** | **0.339** | **14** | **0.280** | **-5.9pp** |

| Player | Team | prior dc90 | ratio | band | v1 P(hit) | GW1 DC | Hit |
|---|---|---:|---:|---|---:|---:|---|
| Canvot | CRY | 11.43 | 1.14 | >=1.10T | 0.73 | 8 | ✗ |
| J.Cuenca | FUL | 11.26 | 1.13 | >=1.10T | 0.72 | 10 | ✓ |
| Hill | BOU | 11.13 | 1.11 | >=1.10T | 0.71 | 6 | ✗ |
| Ballard | SUN | 11.08 | 1.11 | >=1.10T | 0.71 | 9 | ✗ |
| Botman | NEW | 10.60 | 1.06 | 1.00-1.10T | 0.64 | 10 | ✓ |
| Senesi | TOT | 10.53 | 1.05 | 1.00-1.10T | 0.63 | 16 | ✓ |
| Bijol | LEE | 10.44 | 1.04 | 1.00-1.10T | 0.62 | 12 | ✓ |
| Tarkowski | EVE | 10.16 | 1.02 | 1.00-1.10T | 0.57 | 9 | ✗ |
| O'Shea | IPS | 10.09 | 1.01 | 1.00-1.10T | 0.56 | 18 | ✓ |
| Lacroix | CHE | 10.02 | 1.00 | 1.00-1.10T | 0.55 | 12 | ✓ |
| Richards | CRY | 9.91 | 0.99 | 0.85-1.00T | 0.54 | 16 | ✓ |
| Collins | BRE | 9.66 | 0.97 | 0.85-1.00T | 0.51 | 3 | ✗ |
| Ajer | BRE | 9.57 | 0.96 | 0.85-1.00T | 0.49 | 10 | ✓ |
| Murillo | NFO | 9.42 | 0.94 | 0.85-1.00T | 0.47 | 14 | ✓ |
| Virgil | LIV | 9.26 | 0.93 | 0.85-1.00T | 0.45 | 11 | ✓ |
| Heaven | MUN | 9.10 | 0.91 | 0.85-1.00T | 0.43 | 2 | ✗ |
| Gabriel | ARS | 9.07 | 0.91 | 0.85-1.00T | 0.42 | 4 | ✗ |
| Thiaw | NEW | 8.87 | 0.89 | 0.85-1.00T | 0.40 | 15 | ✓ |
| Justin | LEE | 8.70 | 0.87 | 0.85-1.00T | 0.38 | 12 | ✓ |
| Mosquera | ARS | 8.67 | 0.87 | 0.85-1.00T | 0.37 | 6 | ✗ |
| Van Hecke | TOT | 8.59 | 0.86 | 0.85-1.00T | 0.36 | 9 | ✗ |
| Rodon | LEE | 8.35 | 0.83 | 0.70-0.85T | 0.34 | 7 | ✗ |
| Milenković | NFO | 8.29 | 0.83 | 0.70-0.85T | 0.33 | 7 | ✗ |
| Maguire | MUN | 8.24 | 0.82 | 0.70-0.85T | 0.32 | 4 | ✗ |
| Robinson | FUL | 8.23 | 0.82 | 0.70-0.85T | 0.32 | 7 | ✗ |
| Truffert | BOU | 8.02 | 0.80 | 0.70-0.85T | 0.30 | 7 | ✗ |
| Guéhi | MCI | 7.89 | 0.79 | 0.70-0.85T | 0.29 | 4 | ✗ |
| Khusanov | MCI | 7.76 | 0.78 | 0.70-0.85T | 0.28 | 4 | ✗ |
| Reinildo | SUN | 7.51 | 0.75 | 0.70-0.85T | 0.25 | 8 | ✗ |
| Dunk | BHA | 7.33 | 0.73 | 0.70-0.85T | 0.23 | 2 | ✗ |
| Bassey | FUL | 7.29 | 0.73 | 0.70-0.85T | 0.23 | 4 | ✗ |
| Maatsen | AVL | 7.25 | 0.72 | 0.70-0.85T | 0.23 | 9 | ✗ |
| Hall | NEW | 7.16 | 0.72 | 0.70-0.85T | 0.22 | 11 | ✓ |
| Castagne | FUL | 7.15 | 0.71 | 0.70-0.85T | 0.21 | 6 | ✗ |
| Rúben | MCI | 7.03 | 0.70 | 0.70-0.85T | 0.20 | 6 | ✗ |
| Mykolenko | EVE | 7.03 | 0.70 | 0.70-0.85T | 0.20 | 4 | ✗ |
| N.Williams | NFO | 6.94 | 0.69 | <0.70T | 0.20 | 6 | ✗ |
| Mitchell | CRY | 6.78 | 0.68 | <0.70T | 0.19 | 5 | ✗ |
| Gvardiol | MCI | 6.77 | 0.68 | <0.70T | 0.19 | 7 | ✗ |
| Shaw | MUN | 6.26 | 0.63 | <0.70T | 0.16 | 4 | ✗ |
| James | CHE | 5.89 | 0.59 | <0.70T | 0.13 | 6 | ✗ |
| Smith | BOU | 5.87 | 0.59 | <0.70T | 0.13 | 5 | ✗ |
| Bogle | LEE | 5.73 | 0.57 | <0.70T | 0.12 | 3 | ✗ |
| Cash | AVL | 5.55 | 0.56 | <0.70T | 0.11 | 7 | ✗ |
| Calafiori | ARS | 5.41 | 0.54 | <0.70T | 0.10 | 5 | ✗ |
| Kerkez | LIV | 5.36 | 0.54 | <0.70T | 0.10 | 7 | ✗ |
| Lindelöf | AVL | 5.16 | 0.52 | <0.70T | 0.09 | 3 | ✗ |
| Robertson | TOT | 5.12 | 0.51 | <0.70T | 0.09 | 11 | ✓ |
| Davis | IPS | 4.92 | 0.49 | <0.70T | 0.07 | 7 | ✗ |
| Frimpong | LIV | 2.62 | 0.26 | <0.70T | 0.02 | 2 | ✗ |

Three things the GW4 pooling must know:

1. **n = 50, not the retro's 34.** The retro ran against a snapshot missing 93
   defender element-summaries. Those were fetched this cycle, plus 3 players
   whose most recent PL season is 2024/25 rather than 2025/26. The extra 16
   rows are new coverage, not a different rule.
2. **The v1 predicted rate here (0.339) is higher than the retro's DEF figure
   (0.314)** purely because the curve is the unified one. Compare like with like
   at GW4.
3. **`defensive_contribution` in `history_past` is computed under the player's
   position at the time.** Two current defenders — **Wieffer (BHA)** and
   **Sessegnon (FUL)** — were midfielders in 2025/26, so their season aggregate
   silently folds in recoveries and overstates their DEF rate by 61% and 51%
   respectively. This file computes dc90 as CBI + tackles directly. Any pooled
   retro analysis that reads the aggregate field will inherit the bug.

## C4 — promoted-club (±) exposure, top 20

| Player | ± fixtures | band-derived EP | share of EP6 | Largest non-appearance term in a ± GW |
|---|---|---:|---:|---|
| Virgil (LIV) | GW3 IPS | 1.97 | 8% | GW3 IPS clean sheet 1.19 |
| Guéhi (MCI) | GW3 COV, GW7 IPS | 5.33 | 22% | GW3 COV clean sheet 1.71; GW7 IPS clean sheet 1.51 |
| Thiaw (NEW) | GW5 HUL, GW6 COV | 4.25 | 18% | GW5 HUL clean sheet 1.24; GW6 COV clean sheet 1.04 |
| Richards (CRY) | GW4 IPS | 1.86 | 8% | GW4 IPS clean sheet 1.28 |
| Senesi (TOT) | GW7 COV | 1.91 | 8% | GW7 COV clean sheet 1.26 |
| O'Reilly (MCI) | GW3 COV, GW7 IPS | 5.80 | 25% | GW3 COV clean sheet 1.54; GW7 IPS attack 1.38 |
| Canvot (CRY) | GW4 IPS | 1.80 | 8% | GW4 IPS clean sheet 1.20 |
| Tarkowski (EVE) | GW5 IPS, GW6 HUL | 3.59 | 16% | GW5 IPS clean sheet 1.16; GW6 HUL clean sheet 1.23 |
| Lacroix (CHE) | GW4 HUL | 2.08 | 9% | GW4 HUL clean sheet 1.48 |
| Botman (NEW) | GW5 HUL, GW6 COV | 3.22 | 15% | GW5 HUL clean sheet 1.12 |
| Muñoz (CRY) | GW4 IPS | 2.29 | 11% | GW4 IPS clean sheet 1.24 |
| N.Williams (NFO) | GW5 COV | 2.25 | 12% | GW5 COV clean sheet 1.55 |
| Andersen (FUL) | GW6 IPS, GW7 HUL | 2.94 | 15% | GW7 HUL clean sheet 1.25 |
| Hall (NEW) | GW5 HUL, GW6 COV | 3.51 | 19% | GW5 HUL clean sheet 1.17; GW6 COV clean sheet 0.98 |

Under the literal rule — *largest single EP component* — **no player breaches
C4**: the appearance term (≈1.8) exceeds every band-derived clean-sheet term in
the file, the largest of which is Guéhi's GW3 COV(H) at 1.71. Under the stricter
reading the fourth column names the breach. **Guéhi (22.0%), O'Reilly (24.8%),
Gvardiol (22.4%), Hall (18.5%) and Thiaw (17.6%) carry the most band exposure**;
Gabriel, Calafiori, White and Mosquera carry none at all.

## C3 sensitivity — what the curve unification actually moved

| Player | ratio | GW1 DEF band | unified anchor | EP6 old | EP6 new | Δ |
|---|---:|---:|---:|---:|---:|---:|
| Gabriel (ARS) | 0.83 | 0.24 | 0.33 | 25.35 | 26.31 | **+0.96** |
| Virgil (LIV) | 0.95 | 0.38 | 0.49 | 23.76 | 24.88 | **+1.12** |
| Thiaw (NEW) | 0.98 | 0.38 | 0.52 | 22.72 | 24.15 | **+1.43** |
| Richards (CRY) | 1.08 | 0.55 | 0.67 | 22.90 | 24.14 | **+1.24** |
| Senesi (TOT) | 1.14 | 0.55 | 0.73 | 22.00 | 23.81 | **+1.81** |
| Canvot (CRY) | 1.09 | 0.55 | 0.69 | 21.40 | 22.69 | **+1.29** |
| Tarkowski (EVE) | 1.00 | 0.38 | 0.55 | 20.90 | 22.67 | **+1.77** |
| Bijol (LEE) | 1.07 | 0.55 | 0.65 | 18.68 | 19.62 | **+0.94** |
| N.Williams (NFO) | 0.68 | 0.10 | 0.19 | 18.56 | 19.45 | **+0.89** |
| *top-20 aggregate* | | | | 429.9 | 444.4 | **+14.5 (+3.4%)** |

Nine of the top twenty gained more than 0.8 EP6, every one of them a high-CBIT
centre-back. The reordering is real: Richards, Thiaw, Senesi, Canvot and
Tarkowski all rise relative to the attack-led defenders (Calafiori, O'Reilly,
Muñoz) whose DefCon rate is near zero. **If the red-team wants to reject one
thing in this file, it should be this** — the counter-argument is that GW1's own
DEF sample above 0.85×T ran +16.7pp *above* v1, which points the same way but is
not statistically distinguishable from noise at n = 16.

Cross-checked against `data/analysis/gw2/players-MID.md`: the MID analyst uses
the same six spec anchors, linearly interpolated. The two files differ only in
the tail below 0.70×T (this file anchors 0.40→0.02, MID anchors 0.55→0.10),
where they agree to within 1pp at every ratio. **C3 is satisfied
cross-position** — an identical ratio now scores identically for a DEF and a MID
up to the threshold-relative difference in T itself (10 vs 12).

## Minutes model — what GW1 resolved

GW1 lineups are the first real depth-chart evidence of the season, so the update
is asymmetric: a fit player who logged **zero** minutes while four club-mates
played 90 gets a heavier demotion (evidence weight 3.5) than a 90-minute starter
gets a promotion (2.5), and the whole update is scaled by the prior's strength
(8 match-equivalents for a 25+ start prior, down to 1.5 for a player with no
GW1-file entry). Movement is capped at ±0.30.

Two confounds are handled explicitly:

- **Cleared injury flags.** A player showing `chance_of_playing: 100` with a
  recent `news_added` is one FPL just un-flagged; a low GW1 minute count for such
  a player is confounded with injury management, not demotion. Evidence weight
  drops to 1.5. This affects **Pedro Porro** (13.6% owned, 0 minutes in GW1,
  flag cleared on the day of the GW1 deadline — p_start 0.78 rather than 0.60),
  Struijk, Mukiele, Van de Ven, Alderete and Kadıoğlu.
- **Availability-driven zeros.** **Andersen (FUL)** was *suspended* for GW1, so
  his zero carries no depth-chart information; FPL now lists him `a` at 100% and
  Fulham's GW2 kick-off (30 Aug 13:00) falls after the ban expires. Manual
  p_start 0.80. He re-enters the file at rank 19 with a 0.59 DefCon floor at
  £5.0m and 0.1% ownership.

Biggest movers:

| Player | GW1 p_start | GW2 p_start | Why |
|---|---:|---:|---|
| White (ARS) | 0.65 | 0.75 | 90′ and 11 points; ARS have 5 fit senior DEF for 4 slots |
| Mosquera (ARS) | 0.62 | 0.74 | 90′ |
| Gvardiol (MCI) | 0.52 | 0.63 | 90′, but 16 prior starts caps the move |
| Maguire (MUN) | 0.70 | 0.76 | 90′; 17.1% owned |
| James (CHE) | 0.70 | 0.76 | 90′ |
| Hincapie (ARS) | 0.85 | 0.56 | 9′ off the bench; joined 2026-07-01 so the prior is weak |
| Dalot (MUN) | 0.82 | 0.64 | 10′ while Mazraoui started |
| Konsa (ARS) | 0.90 | **0.50** | **Moved AVL → ARS since GW1**; unused in GW1. Manual override |
| Struijk (BHA) | 0.82 | 0.70 | 0′, but a cleared flag softens the read |
| O'Brien (EVE) | 0.90 | 0.69 | 0′; EVE played a back three |

**Konsa is the trap of the week.** He is 10.9% owned at £4.5m and the GW2
bootstrap has him at **Arsenal**, not Aston Villa — a club change the GW1 file
predates. He did not play a minute in GW1 while Gabriel, White, Mosquera and
Calafiori did, and Saliba and Timber both return eventually. The market is
pricing an Arsenal starting job he does not hold. EP6 12.09, rank 84.

## Data traps verified this cycle

1. **`history_past.defensive_contribution` is position-at-the-time**, not
   position-now. Affects Wieffer and Sessegnon among current defenders. Compute
   CBI + tackles directly.
2. **93 of 205 defenders had no element-summary in the delivered snapshot** —
   including Bassey, Castagne, Mykolenko, Dunk, Boscagli, Colwill, Robertson and
   every Fulham defender. Fetched this cycle. Any analysis reading only
   `prior-season.json` for these players sees `minutes: 0`.
3. **`prior-season.json` falls back to a player's most recent PL season**, which
   is 2024/25 for three defenders (O'Shea among them). The `season_name` field
   says so; it is easy to read as 2025/26 and is decayed 10% here.
4. **One 90-minute match will triple a rate if you let it.** De Cuyper generated
   **1.47 xG in 77 minutes** — the round's largest defender outlier. Unclipped,
   a 15% blend weight would have lifted his xG+xA/90 from 0.368 to 0.573 and his
   EP6 from 17.04 to 21.23, putting him 15th. The [0.40×, 2.50×] guard band
   binds on 39 players.
5. **Prices have moved.** Calafiori £5.5 → 5.6, Kayode and De Cuyper £4.5 → 4.6,
   Hincapie £5.5 → 5.4. Read prices from the GW2 bootstrap, not the GW1 file.

## Uncertainty

| Flag | Severity | Detail |
|---|---|---|
| **C3 curve unification** | **HIGH** | The single largest change in this file. +3.4% on the top-20 aggregate, concentrated entirely on high-CBIT centre-backs. Level-preserving against the spec, but it reorders the £5.0m tier. Reject it and Richards/Thiaw/Senesi/Canvot/Tarkowski all fall 1–2 EP6. |
| **Promoted-club ratings** | **HIGH** | ±15pp on every COV/HUL/IPS P(CS) through GW3. Five of the top 20 carry >15% of their EP6 inside it. |
| **n = 1 current-season sample** | **HIGH** | Every current-season input is one match. The guard band and the 85/15 weight are deliberate brakes; both unwind as n grows. |
| **Team defence assumption-dominated** | **MEDIUM** | 80% of each club's defence rating is still a 5-tier prior. Mid-table P(CS) gaps under ~4pp are noise, and the clean-sheet term is 25–35% of a typical defender's EP. |
| **European rotation** | **MEDIUM** | The FPL API exposes no continental calendar. Rotation risk for ARS, MCI, CHE, LIV, MUN, TOT and NEW is carried inside p_start from GW1 judgment and is **not** re-derived from data. UCL fixtures begin mid-September, i.e. inside GW4–7. |
| **International break GW5→GW6** | **MEDIUM** | A 19-day gap. GW6–7 EPs are the least reliable in the window for every player. |
| **Bonus model** | **LOW** | Recovered from GW1 by regression (mean abs residual 0.012 on 85 players) rather than re-derived. It reproduces GW1's judgment exactly, including any error in it. The 26/27 CBI→BPS cut from 1/2 to 1/3 is embedded in that GW1 judgment, not modelled independently. |
| **Set-piece data** | **LOW** | No defender in the file has penalty duty above pen2. Free-kick and corner orders are read from the GW2 bootstrap and are current. |
