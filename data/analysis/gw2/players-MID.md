# GW2 — MID expected points (GW2–GW7)

Season 2026/27 | GW2 deadline 2026-08-28T17:30:00Z | snapshot `data/raw/gw2/`
(fetched 2026-08-28T09:45Z, age < 1h) | supersedes `data/analysis/gw1/players-MID.md`

Fixture inputs: λ_att and P(CS) taken as-is from `data/analysis/gw2/fixtures.md`.
Regime: **IN-SEASON, n = 1**. Bootstrap season-to-date fields hold one match and
are never divided by; every rate is an element-summary `history_past` prior
blended **85 / 15** with the GW1 row, the current-season share scaled by minutes
played. Corrections C1, C2, C3, C4 and C7 from `data/retro/gw1.md` are applied —
see *Retro compliance*.

Full per-player output: `players-MID.json` (all 270 MIDs, 257 with non-zero EP).

## What changed since GW1

| | GW1 | GW2 |
|---|---|---|
| Minutes evidence | last season's start counts only | **one observed lineup per club** — the single largest change in this file |
| Rate priors | 100% 25/26 | 85 / 15 prior / GW1, current share × min(1, mins/90) |
| DefCon mapping | v1 anchors, interpolated | **unchanged (C1)** — applied to the blended dc90 |
| Uncertainty tag | judgment | **bound to p_start (C7)** |
| Palace attackers | full rate | **×0.85** on the attack multiplier (fixture-analyst escalation) |

The GW1 lineups moved p_start far more than the GW1 xG moved any rate. Eight of
the top 20 changed p_start by more than 0.08, and every large EP6 move in the
file is a minutes move, not a rate move.

## Top 15 by EP6

| # | Player | Club | £ | own | p_start | EP6 | EP/£ | EP by GW (2→7) |
|---|---|---|---|---|---|---|---|---|
| 1 | B.Fernandes | MUN | 12.0 | 48.4% | 0.92 | **31.46** | 2.62 | 5.7 5.2 4.7 5.2 5.8 4.9 |
| 2 | Szoboszlai | LIV | 7.0 | 43.2% | 0.92 | **27.02** | 3.86 | 4.6 4.7 4.9 4.4 4.2 4.2 |
| 3 | Anderson | MCI | 6.4 | 6.1% | 0.93 | **26.98** | **4.22** | 4.2 4.9 4.2 4.8 4.2 4.7 |
| 4 | Mbeumo | MUN | 8.0 | 36.0% | 0.86 | **26.84** | 3.35 | 4.9 4.4 4.0 4.5 5.0 4.2 |
| 5 | Rogers | CHE | 7.5 | 26.1% | 0.92 | **26.08** | 3.48 | 4.3 3.6 5.3 4.0 4.5 4.3 |
| 6 | Rice | ARS | 7.5 | 17.0% | 0.92 | **25.58** | 3.41 | 4.3 4.2 4.4 4.1 4.3 4.2 |
| 7 | Tavernier | BOU | 6.0 | 2.4% | 0.88 | **25.00** | 4.17 | 4.4 4.2 4.0 4.0 3.8 4.6 |
| 8 | Semenyo | MCI | 8.5 | 24.2% | 0.93 | **24.86** | 2.92 | 3.8 4.7 3.8 4.5 3.7 4.4 |
| 9 | Schade | BRE | 6.0 | 3.5% | 0.88 | **24.53** | 4.09 | 3.8 4.6 3.9 4.0 4.2 3.9 |
| 10 | Ndiaye | EVE | 6.0 | 16.1% | 0.90 | **24.25** | 4.04 | 3.8 3.9 4.1 4.3 4.3 3.9 |
| 11 | Gomez | BHA | 5.0 | 3.8% | 0.93 | **23.85** | **4.77** | 3.7 4.0 4.3 3.6 4.2 4.0 |
| 12 | Gibbs-White | NFO | 8.0 | 8.6% | 0.93 | **23.77** | 2.97 | 3.6 4.4 4.0 4.5 3.7 3.5 |
| 13 | Scott | BOU | 6.0 | 1.5% | 0.93 | **23.36** | 3.89 | 4.0 3.9 3.8 3.8 3.7 4.2 |
| 14 | Saka | ARS | 9.5 | 10.4% | 0.68 | **23.21** | 2.44 | 4.0 3.9 4.1 3.6 4.0 3.7 |
| 15 | Gakpo | LIV | 7.0 | 6.1% | 0.88 | **22.50** | 3.21 | 3.9 3.9 4.2 3.7 3.4 3.5 |

Just outside: Buendía (AVL, 6.0, 22.09), Cunha (MUN, 8.0, 22.02),
Ampadu (LEE, 5.5, 21.80), Dewsbury-Hall (EVE, 6.5, 21.69), Wirtz (LIV, 7.5, 21.29),
Gravenberch (LIV, 6.0, 20.86), Foden (MCI, 7.0, 20.85), Wharton (CRY, 5.5, 20.77),
Le Fée (SUN, 6.0, 20.77), Stach (LEE, 6.0, 20.65).

## Our five

| Player | £ | p_start | GW1 mins | EP6 | rank | GW2 EP | Unc | Read |
|---|---|---|---|---|---|---|---|---|
| Anderson | 6.4 | **0.93** | 62 (started) | **26.98** | 3 | 4.23 | LOW | dc90 blends 13.60 → 13.10 on the GW1 miss; P(hit) 0.73 → 0.69. Still the highest DefCon floor of any nailed MID. 29% of his EP6 is DefCon and it is fixture-independent. |
| Mbeumo | 8.0 | **0.86** | 90 (started) | **26.84** | 4 | 4.90 | LOW | The 90 minutes confirmed the minutes prior (0.81 → 0.86). MUN's ticker is 7th and peaks GW6 (TOT H, λ 1.98). 53% of EP6 is attacking — the highest share in our five. |
| Ndiaye | 6.0 | **0.90** | 90 (started) | **24.25** | 10 | 3.80 | LOW | dc90 9.16 → 9.55 on the GW1 hit; P(hit) still only 0.30. His 9 points came from a DefCon *against* his prior — do not re-rate him on it. EVE fixtures back-load (GW5–6). Penalty taker. |
| Scott | 6.0 | **0.93** | 90 (started) | **23.36** | 13 | 4.03 | LOW | Highest p_start in the position alongside Anderson/Gomez. dc90 11.81, ratio 0.98, P(hit) 0.53 — 26% of EP6. Missed the GW1 threshold by one action, which is exactly what a 0.53 looks like. |
| **Enzo** | 7.0 | **0.61** | **25 (bench)** | **18.30** | **36** | 3.05 | **HIGH** | **−5.63 EP6, the largest fall in the file.** See below. |

### Enzo — the p_start rebuild the retro demanded

C7 was written because Enzo was tagged LOW at p_start 0.81 in GW1 and then
started on the bench. The number is now rebuilt from evidence, not repeated:

| Input | Value |
|---|---|
| 25/26 prior | 35 starts, 89 min/start → base 0.93 |
| GW1 observation | **benched**, 25' off the bench at Fulham |
| Chelsea's GW1 XI | Palmer 82', Rogers 81', **Lavia 64'** — three FPL-MIDs, and the third slot went to Lavia (4 prior starts), not Enzo |
| Caicedo | `d`/75%, 0 minutes — the pivot partner was unavailable and Enzo *still* did not start |
| Club MID-slot target | 3.90 (Chelsea fielded 3; shrunk halfway to the 4.53 league constant) |
| **p_start** | **0.609** |
| **Uncertainty** | **HIGH** — p_start < 0.70 (C7 floor), and the estimate itself rests on one lineup |

The last row matters: 0.61 is not a confident number, it is a wide one. One
benching cannot distinguish "lost his place" from "rotated in the opener".
**The optimizer should treat Enzo as the squad's live rotation risk and price
the HIGH tag, not the point estimate.** One GW2 start would push the observation
set back toward his prior and lift him into the high-0.70s by GW3 — but that
information does not exist before the deadline.

Enzo is now the clearest case in our own squad of a premium losing to a nailed
mid-price player: at £7.0m he scores 18.30, while **Tavernier at £6.0m scores
25.00** on p_start 0.88.

## Nailed cheap beats rotating premium

Each row is a case where the cheaper player wins on **raw EP6**, before the
saving is redeployed. Mechanism is unchanged from GW1 and now has an observed
lineup behind every p_start.

| Rotating premium | p_start | EP6 | Nailed cheaper alternative | p_start | EP6 | Saving |
|---|---|---|---|---|---|---|
| Saka (ARS, 9.5) | 0.68 | 23.21 | **Anderson** (MCI, 6.4) | 0.93 | **26.98** | £3.1m |
| Palmer (CHE, 9.5) | 0.60 | 19.09 | **Ndiaye** (EVE, 6.0) | 0.90 | **24.25** | £3.5m |
| Palmer (CHE, 9.5) | 0.60 | 19.09 | **Gomez** (BHA, 5.0) | 0.93 | **23.85** | £4.5m |
| Wirtz (LIV, 7.5) | 0.75 | 21.29 | **Schade** (BRE, 6.0) | 0.88 | **24.53** | £1.5m |
| Enzo (CHE, 7.0) | 0.61 | 18.30 | **Tavernier** (BOU, 6.0) | 0.88 | **25.00** | £1.0m |
| Foden (MCI, 7.0) | 0.71 | 20.85 | **Scott** (BOU, 6.0) | 0.93 | **23.36** | £1.0m |
| Cherki (MCI, 7.5) | 0.44 | 15.99 | **Ampadu** (LEE, 5.5) | 0.93 | **21.80** | £2.0m |
| O.Dango (BRE, 6.5) | 0.69 | 20.38 | **Ayari** (BHA, 5.5) | 0.88 | **20.54** | £1.0m |

Stated explicitly, as the spec requires:

- **Palmer is the worst value in the position.** At £9.5m and EP/£ 2.01 he is
  the only top-40 MID under 2.1. Chelsea started three FPL-MIDs in GW1 and he
  has 24 prior starts, not 35 — the minutes risk is real and unpriced.
- **Cherki started GW1 on the bench (27') and Doku is out until ~GW4.**
  Manchester City's £7.0–7.5m band is a rotation trap; the club's own £6.4m
  Anderson outscores all three of them combined per pound.
- **Saka retains the highest xG90 in the top 15 (0.319)** and still loses to a
  £6.4m holding midfielder. His 67 minutes in GW1 confirmed the start but not
  the 90.
- The premiums that *survive* their price are B.Fernandes, Mbeumo and Rogers —
  all on p_start ≥ 0.86, all confirmed by GW1 minutes.

## Best value (EP6 ≥ 15, ranked by EP per £m)

| Player | Club | £ | p_start | EP6 | EP/£ | Why |
|---|---|---|---|---|---|---|
| Gomez | BHA | 5.0 | 0.93 | 23.85 | **4.77** | Best EP/£ in the position for the second cycle. Brighton's midfield remains bare (Mitoma, Minteh, Hinshelwood all flagged); 85' in GW1. dc90 9.46. |
| Anderson | MCI | 6.4 | 0.93 | 26.98 | 4.22 | Highest DefCon floor of any nailed MID (ratio 1.09, P(hit) 0.69). Price already drifted 6.5 → 6.4. |
| Tavernier | BOU | 6.0 | 0.88 | 25.00 | 4.17 | 90' in GW1, pens#3 + FK1 + CK1, BOU's best fixtures bookend the window (GW2 EVE H, GW7 SUN H). |
| Ndiaye | EVE | 6.0 | 0.90 | 24.25 | 4.04 | Penalty taker, 90' in GW1, EVE fixtures peak GW5–6. |
| Schade | BRE | 6.0 | 0.88 | 24.53 | 4.09 | Brentford's attack is now rated 3rd (ATT 1.29) with an easy GW3–7 run. Highest xG90 (0.349) under £6.5m. |
| Ampadu | LEE | 5.5 | 0.93 | 21.80 | 3.96 | Pure floor: dc90 11.97, ratio 1.00, hit the GW1 threshold with 13. Almost no attacking term. |
| Scott | BOU | 6.0 | 0.93 | 23.36 | 3.89 | dc90 11.81 plus FK/CK duty. |
| Szoboszlai | LIV | 7.0 | 0.92 | 27.02 | 3.86 | **The most-transferred-to MID in the game (43.2% owned).** PENS + FK1 + CK1 and Liverpool's GW2–4 run is the best opening triple in the league. Sell into GW5 — LIV's P(CS) swings −16.7pp, the largest swing in the window. |
| Wharton | CRY | 5.5 | 0.83 | 20.77 | 3.78 | dc90 11.05, ratio 0.92. Palace's 15% attacking discount barely touches him — his attack term is 11% of EP6. |
| Ayari | BHA | 5.5 | 0.88 | 20.54 | 3.73 | dc90 9.86; 63' in GW1 caps the DefCon minutes factor at 0.90. |
| Buendía | AVL | 6.0 | 0.91 | 22.09 | 3.68 | 85' in GW1, PENS + FK1. Prior sample only 1753' → tagged HIGH. |

## Captaincy and chip notes for the optimizer

| Question | Answer |
|---|---|
| Highest single-GW MID EP in the window | B.Fernandes GW6 (5.75, TOT H) and GW2 (5.66, IPS H) |
| Best GW2 MID captain | **B.Fernandes 5.66** (IPS home, λ 1.91); Mbeumo 4.90 is the same fixture at £4.0m less |
| Highest non-Bruno single GW | **Rogers GW4, 5.32** (CHE v HUL, λ 2.83 — the best attacking fixture in all 120 club-fixtures) — **carries the ±15pp band** |
| Triple Captain (MID) | No MID reaches 6.0 in any gameweek. A MID TC is not competitive in this window |
| Front-load | LIV (Szoboszlai, Gakpo, Gravenberch) peak GW2–4 and fall off a cliff at GW5 |
| Back-load | EVE (Ndiaye, Dewsbury-Hall) peak GW5–6; NFO (Gibbs-White) peaks GW5 |
| Bench Boost fodder | **Still unusable from this position.** The best £4.5m MID is Slater (HUL, EP6 10.81, p_start 0.71) and he has zero PL history. Hughes (CRY, £4.5m, **10.9% owned**) played **0 minutes** in GW1 — an ownership-built enabler shortlist will pick a non-starter |
| Doku (MCI, 7.5) | `i`/0%, calf, expected back 5 Sep — the GW3 deadline is 4 Sep. Zero for GW2–3, EP6 9.14. A GW4 target at the earliest, unchanged from GW1 |

## Retro compliance

### C1 — DefCon mapping unchanged

The v1 anchor curve is applied exactly as at GW1: the spec's six anchors
interpolated (ratio 0.55→0.10, 0.70→0.20, 0.85→0.35, 1.00→0.55, 1.10→0.70,
1.30→0.85, capped). **No level shift, no sub-threshold shrinkage toward observed
rates, and no switch to the observed per-match hit rate.** The only GW1
influence on DefCon is through the 85/15 blend of the dc90 *rate*, which is the
"nudged only marginally" channel C1 permits. Effect on our players: Anderson
13.60 → 13.10 (P(hit) 0.73 → 0.69), Ndiaye 9.16 → 9.55 (0.26 → 0.30),
Scott 12.00 → 11.81 (0.55 → 0.53).

### C2 — DefCon calibration sample, GW1, MID

Qualifying: ≥900 prior-season minutes **and** ≥80 GW1 minutes. dc90 is the
prior-only shrunk rate (K = 200) — the value the v1 mapping was applied to at
GW1, so this is a clean out-of-sample test. Threshold T = 12.

| Ratio band | n | v1 predicted | observed | delta | hits |
|---|---:|---:|---:|---:|---:|
| < 0.70 | 22 | 0.125 | 0.045 | **−7.9pp** | 1 |
| 0.70 – 0.85 | 10 | 0.287 | 0.300 | +1.3pp | 3 |
| 0.85 – 1.00 | 6 | 0.472 | 0.667 | **+19.5pp** | 4 |
| **all** | **38** | **0.222** | **0.211** | **−1.2pp** | **8** |

Aggregate calibration is essentially exact (−1.2pp). The band pattern reproduces
the retro's **slope** hypothesis rather than its refuted level hypothesis: v1 is
too flat — high below 0.70 and low above 0.85. n is far too small to act on;
C2 defers the test to GW4 on the pooled sample.

Per-player rows for pooling at GW4:

| Player | dc90 | ratio | band | v1 P(hit) | GW1 DC | Result |
|---|---:|---:|---|---:|---:|---|
| Scott | 11.95 | 0.996 | 0.85–1.00 | 0.545 | 11 | miss |
| Ampadu | 11.79 | 0.983 | 0.85–1.00 | 0.527 | 13 | HIT |
| I.Sangaré | 11.32 | 0.943 | 0.85–1.00 | 0.474 | 6 | miss |
| Janelt | 11.12 | 0.926 | 0.85–1.00 | 0.452 | 13 | HIT |
| Xhaka | 11.05 | 0.921 | 0.85–1.00 | 0.445 | 13 | HIT |
| Wharton | 10.53 | 0.877 | 0.85–1.00 | 0.386 | 14 | HIT |
| Stach | 9.98 | 0.832 | 0.70–0.85 | 0.332 | 16 | HIT |
| Gomez | 9.98 | 0.831 | 0.70–0.85 | 0.331 | 6 | miss |
| Buendía | 9.95 | 0.829 | 0.70–0.85 | 0.329 | 7 | miss |
| Kamada | 9.73 | 0.811 | 0.70–0.85 | 0.311 | 14 | HIT |
| Lukić | 9.41 | 0.784 | 0.70–0.85 | 0.284 | 6 | miss |
| Kamara | 9.38 | 0.782 | 0.70–0.85 | 0.282 | 7 | miss |
| Szoboszlai | 9.36 | 0.780 | 0.70–0.85 | 0.280 | 7 | miss |
| Ndiaye | 9.11 | 0.759 | 0.70–0.85 | 0.259 | 12 | HIT |
| Tonali | 9.08 | 0.757 | 0.70–0.85 | 0.257 | 4 | miss |
| B.Fernandes | 8.43 | 0.703 | 0.70–0.85 | 0.203 | 6 | miss |
| Tavernier | 8.28 | 0.690 | < 0.70 | 0.194 | 8 | miss |
| Gray | 8.12 | 0.677 | < 0.70 | 0.185 | 5 | miss |
| Groß | 8.03 | 0.669 | < 0.70 | 0.180 | 5 | miss |
| Aaronson | 7.98 | 0.665 | < 0.70 | 0.177 | 7 | miss |
| Dewsbury-Hall | 7.92 | 0.660 | < 0.70 | 0.173 | 8 | miss |
| Sadiki | 7.77 | 0.647 | < 0.70 | 0.165 | 2 | miss |
| Tel | 7.62 | 0.635 | < 0.70 | 0.157 | 8 | miss |
| King | 7.60 | 0.633 | < 0.70 | 0.156 | 8 | miss |
| Iwobi | 7.11 | 0.592 | < 0.70 | 0.128 | 10 | miss |
| Foden | 7.07 | 0.589 | < 0.70 | 0.126 | 6 | miss |
| Rayan | 6.93 | 0.577 | < 0.70 | 0.118 | 1 | miss |
| Semenyo | 6.75 | 0.562 | < 0.70 | 0.108 | 5 | miss |
| McGinn | 6.51 | 0.542 | < 0.70 | 0.099 | 6 | miss |
| Rogers | 6.44 | 0.536 | < 0.70 | 0.098 | 7 | miss |
| Palmer | 6.43 | 0.536 | < 0.70 | 0.098 | 9 | miss |
| Schade | 6.38 | 0.532 | < 0.70 | 0.097 | 9 | miss |
| Tchaouna | 5.42 | 0.452 | < 0.70 | 0.086 | 8 | miss |
| Gibbs-White | 5.37 | 0.447 | < 0.70 | 0.085 | 3 | miss |
| Gakpo | 5.24 | 0.436 | < 0.70 | 0.083 | 12 | HIT |
| Mbeumo | 5.05 | 0.421 | < 0.70 | 0.081 | 4 | miss |
| Barnes | 4.97 | 0.414 | < 0.70 | 0.080 | 8 | miss |
| Lewis-Potter | 3.87 | 0.322 | < 0.70 | 0.067 | 10 | miss |

Machine-readable copy of this table is reproducible from the model script; the
retro can also regenerate it from `data/raw/gw2/players/summary-*.json`.

### C3 — DefCon curve shape

MID uses the spec's own six anchors, linearly interpolated and capped at 0.85 —
a single continuous function with no bands and no separate ceiling. **This is
the unifying form C3 asks for**, and it is unchanged from GW1. The GW1 defect
was on the DEF side (a four-step band function capped at 0.55, scoring an
identical ratio up to 18pp lower). I cannot change the DEF file from this
position — **the finalizer should verify `players-DEF.json` now uses the same
anchors before accepting the cycle.**

### C4 — promoted-club band

Every top-30 MID whose peak gameweek falls on a COV / HUL / IPS fixture was
audited. **No MID violates C4**, because for a midfielder the peak single-GW EP
is only 18–20% of EP6 while the appearance term alone is 35–40% — a
promoted-club fixture is never the largest EP component.

It *does* bind on captaincy. Twelve top-30 MIDs peak on a `±` fixture, including
**Rogers GW4 (CHE v HUL, 5.32 — the highest non-Bruno single-GW EP in the file)**
and **Anderson / Semenyo / Foden GW3 (MCI v COV)**. Treat every one of those as
a range, not a point, if it is being considered for the armband.

### C7 — uncertainty bound to p_start

Applied mechanically: p_start < 0.85 → at least MED; p_start < 0.70 → HIGH.
Additional escalators: prior sample < 900 minutes → HIGH; promoted club → HIGH
(the ±15pp band); any `d`/`i`/`s`/`u` flag → at least MED; and — new this cycle
— **a fit player with ≥20 prior starts who logged under 45 GW1 minutes → HIGH**,
because his role is contradicted by the only lineup we have seen. That last rule
is what puts Enzo and Garner on HIGH rather than the MED their p_start alone
would earn, and it catches ten more names including Zubimendi, Mac Allister and
Neto.

Distribution: **27 LOW / 12 MED / 231 HIGH** across 270 MIDs. The HIGH bucket is
dominated by the 200-odd fringe players who were always uncertain; among the top
30 the split is 22 LOW / 5 MED / 3 HIGH. This is the C7 correction working, not
a modelling regression.

## Method

```
EP(p, gw) = P(start) × [ 1 + P(60') (appearance)
                       + (xG90×5 + xA90×3) × attack_mult
                       + P(CS) × 1 × P(60')
                       + 2 × P(DefCon hit) × minutes_factor
                       + expected bonus − expected yellows ]
          + P(cameo) × (1 + 0.18 × attacking term)
```

Unchanged from GW1 except where noted.

| Component | Treatment |
|---|---|
| Rate blend | `0.85 × prior_shrunk + 0.15 × GW1_per90`, current share × min(1, mins/90). Skipped below 25 GW1 minutes |
| Shrinkage | dc90 K = 200, xG90/xA90 K = 1300, bonus/yellows K = 900, toward MID league means (xG90 0.156, xA90 0.132, dc90 8.48, bonus/start 0.330) from 129 MIDs with ≥900 prior minutes |
| attack_mult | `(λ_att / 1.439) × [w/ATT_club + (1−w)]`, w = the observed share of the rate. CRY multiplied by **0.85** per the fixture-analyst escalation |
| DefCon | T = 12 (CBIT + recoveries). v1 anchors interpolated (C1). Minutes factor 90'→1.00, 75'→0.86, 60'→0.65, 45'→0.18, below → 0 |
| Bonus | prior bonus/start, then 26/27 BPS: ×(1 − 0.15·(dc90−7)/7) for CBI-heavy players, ×1.08 for high-xGI low-DefCon carriers |
| p_start | prior `min(0.93, (starts/38)^0.75)`, then the GW1 observation, then the injury vector, then the club XI-slot constraint |
| Injury vector | per-GW availability from `status` / `chance_of_playing` / news return dates; `i` with a stated return date ramps 0 → 0.55 → 0.90; `i` with unknown return ramps 0 → 0.05 → 0.15 → 0.28 → 0.45 → 0.55 |

**Minutes model — the GW1 observation.** One match is weighted asymmetrically by
how much prior the player already has:

```
w_obs = 0.15 + 0.30 × (1 − min(1, prior_minutes/1500))   for a start
      = 0.24 + 0.20 × (…)                                for a cameo
      = 0.30 + 0.20 × (…)                                for zero minutes while fit
```

A 3000-minute veteran barely moves on one lineup; a promoted-club player with no
PL record moves a lot, because that one lineup is nearly all the evidence that
exists about him. Slater (HUL, no PL history, 90' in GW1) goes 0.28 → 0.70 —
the spec's cold-start cap, which stays in force until two consecutive 60'+ starts.

**Club XI-slot constraint.** Each club's MID p_start vector is scaled to a target
of `0.5 × 4.53 + 0.5 × (GW1 MID starts)`, clipped to [3.9, 5.6]. Observed GW1
MID starts ranged 3 (CHE, MCI, CRY) to 6 (MUN, EVE, AVL, BRE, TOT). The 50/50
shrink toward the 4.53 league constant is deliberate — one lineup is one lineup.
Two guards, both tightened this cycle:

- Upscaling reaches only *credible, available* claimants who were not just
  dropped: a fit player who logged under 45 GW1 minutes cannot be scaled **up**,
  and no player may exceed `pre-constraint × 1.25 + 0.04`. Without these,
  Barkley (AVL, 0.2% owned) reached 0.93 and Florentino (IPS, `d`, 0 GW1
  minutes) reached 0.92.
- The scaling exponent is `(1 − p)² × 2.5`, so a p = 0.9 starter is effectively
  immune and rotation is absorbed by squad players.

## Escalations

1. **Chelsea's entire MID allocation rests on one three-man lineup.** Palmer
   (0.60), Enzo (0.61) and Caicedo (0.77) all sit below where their prior
   records alone would put them, purely because Chelsea fielded three FPL-MIDs
   at Fulham with Lavia in the third slot. Sensitivity, re-running the whole
   model with Chelsea's target set to four MIDs: Palmer 0.603 → 0.645 p_start
   (EP6 19.09 → 20.25), Enzo 0.609 → 0.650 (18.30 → 19.40), Caicedo 0.771 →
   0.780, Rogers unchanged. The direction matters more than the magnitude —
   neither player's ranking changes — but this is the single largest structural
   assumption in the file and it is n = 1.
   **Worth a team-news check before 17:30Z.**

2. **Enzo — HIGH, and the point estimate is not the story.** Detailed above.
   Recommend the optimizer treat him as a sell candidate on process (a £7.0m
   asset at p_start 0.61 is dominated by £6.0m alternatives at 0.88–0.93) rather
   than on the EP delta, which is itself uncertain.

3. **Sarr (CRY, £6.4m) is out — `i`/0%, groin, unknown return.** He was ranked
   19th at GW1 (EP6 20.71) and is now 4.65. Anyone holding him from a GW1
   shortlist must move. Not in our squad.

4. **Bruno G. (ARS, £6.9m, `d`/75%, thigh) and Caicedo (CHE, £5.5m, `d`/75%)**
   are the only flagged players inside the top 40 (ranks 34 and 35). Both are
   scored on a ramping availability vector, so their EP6 embeds a recovery
   assumption the snapshot cannot confirm.

5. **Garner (EVE, £6.0m) — the GW1 flag has cleared.** Status `a`,
   `chance_of_playing` 100, news empty, `news_added` 2026-07-25; the mid-GW1
   `d`/25% groin flag is gone. He is fit but **not in the team**: 11 minutes off
   the bench while Everton started six other midfielders. p_start 0.755, EP6
   19.36, dc90 11.88 (P(hit) 0.54). A strong floor asset the moment he starts,
   and worthless until he does. HIGH on the new role-contradiction rule.

6. **Szoboszlai is now a 43.2%-owned template pick.** Nothing in the model
   objects — EP6 27.02 on p_start 0.92 with PENS + FK1 + CK1 — but note the
   fixture cliff: Liverpool's P(CS) falls 37% → 20% at GW5, the largest swing in
   `fixtures.md`. He is a GW2–4 asset priced as a season-long one.

7. **The £4.5m MID enabler pool is empty, again.** Best is Slater (HUL, EP6
   10.81, zero PL history, HIGH). Hughes (CRY, £4.5m) is **10.9% owned and
   played zero minutes in GW1** — the same ownership-driven trap the GW1 file
   flagged for Yates. Bench Boost remains unusable from this position.

8. **Cup rotation is still unmodelled.** `fixtures.md` flags it UNKNOWN and it
   bites hardest on MCI, ARS, CHE, LIV, MUN, TOT, NEW — which is where seven of
   the top ten MIDs play. The GW6/GW7 half of every number in this file also
   sits behind a 19-day international break.

9. **Spec deviations carried forward from GW1, unchanged and still open for
   accept/reject**: DefCon anchors interpolated rather than snapped to tiers
   (avoids probability cliffs); attack multiplier's `1/ATT_club` strip weighted
   by the observed share `w` rather than applied flat. The second is half of the
   still-open LOW-4 cross-position inconsistency that C3 also touches.
