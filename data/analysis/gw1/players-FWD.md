# GW1 — Forwards: expected points, GW1–GW6

Season 2026/27 | GW1 deadline 2026-08-21T17:30:00Z | snapshot `data/raw/gw1/` (fetched 13:27Z, age < 1h)
Regime: **PRE-SEASON** — bootstrap aggregates are 2025/26. `form` is 0.0 for every player and was ignored.
Universe: **72 forwards** priced £4.5–15.5m, all scored. `data/analysis/gw1/players-FWD.json`.

## Headline

| Finding | Detail |
|---|---|
| Price floor | **There is no £4.0m forward.** Cheapest FWD is £4.5m (12 of them). GKP and DEF both floor at £4.0m — budget the third FWD slot accordingly. |
| Value band | **£6.0m is the sweet spot.** £5.5→6.0 buys +5.22 EP6, the steepest step on the ladder; £6.0→7.0 buys **nothing** (Šeško at 7.0 scores *below* Calvert-Lewin at 6.0). |
| DefCon | **Dead for forwards.** No forward in the league reaches even 0.7× the 12-action threshold. Worth ≤0.10 EP/GW to anybody. See below. |
| Captaincy | Haaland tops **5 of 6** GWs. The exception is GW4, where João Pedro (CHE v HUL, λ_att 2.86) leads. |
| Avoid | £6.5–7.0m entirely; Ekitiké at £7.5m (Achilles); every promoted-club forward. |

## Top 15

| # | Player | Club | £m | p_start | GW1 | GW2 | GW3 | GW4 | GW5 | GW6 | **EP6** | EP6/£m | Unc |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Haaland | MCI | 15.5 | 0.92 | 6.31 | 5.62 | 7.72 | 5.15 | 6.38 | 5.02 | **36.20** | 2.34 | LOW |
| 2 | Isak | LIV | 9.0 | 0.84 | 4.41 | 4.81 | 5.05 | 4.84 | 4.28 | 4.07 | **27.46** | 3.05 | HIGH |
| 3 | Thiago | BRE | 8.0 | 0.90 | 4.62 | 4.32 | 4.69 | 4.17 | 4.30 | 4.01 | **26.11** | 3.26 | MED |
| 4 | João Pedro | CHE | 7.5 | 0.77 | 4.10 | 4.38 | 3.11 | 5.48 | 3.81 | 4.27 | **25.15** | 3.35 | MED |
| 5 | Watkins | AVL | 8.0 | 0.86 | 3.96 | 3.49 | 4.76 | 4.25 | 3.86 | 4.21 | **24.53** | 3.07 | MED |
| 6 | Gyökeres | ARS | 7.5 | 0.79 | 4.89 | 3.56 | 3.71 | 3.73 | 3.62 | 4.04 | **23.55** | 3.14 | MED |
| 7 | Mateta | CRY | 6.5 | 0.75 | 3.56 | 3.38 | 3.55 | 4.48 | 3.56 | 3.83 | **22.36** | 3.44 | MED |
| 8 | Calvert-Lewin | LEE | 6.0 | 0.78 | 3.57 | 3.85 | 3.55 | 3.84 | 3.76 | 2.86 | **21.43** | 3.57 | MED |
| 9 | Šeško | MUN | 7.0 | 0.70 | 3.57 | 3.98 | 3.32 | 3.18 | 3.34 | 3.57 | **20.96** | 2.99 | HIGH |
| 10 | Woltemade | NEW | 6.0 | 0.70 | 2.78 | 2.77 | 2.99 | 2.84 | 3.63 | 3.19 | **18.20** | 3.03 | MED |
| 11 | David | BHA | 6.0 | 0.63 | 2.90 | 2.68 | 3.20 | 3.42 | 2.70 | 3.04 | **17.94** | 2.99 | HIGH |
| 12 | Igor Jesus | NFO | 6.0 | 0.70 | 2.88 | 2.47 | 2.81 | 2.58 | 3.25 | 2.62 | **16.61** | 2.77 | MED |
| 13 | Evanilson | BOU | 6.0 | 0.73 | 2.54 | 3.00 | 2.75 | 2.93 | 2.73 | 2.61 | **16.56** | 2.76 | MED |
| 14 | Beto | EVE | 5.5 | 0.51 | 2.64 | 2.47 | 2.48 | 2.46 | 3.14 | 3.02 | **16.21** | 2.95 | HIGH |
| 15 | Gonzalo | FUL | 6.0 | 0.63 | 2.64 | 2.61 | 2.75 | 2.46 | 2.64 | 2.98 | **16.08** | 2.68 | HIGH |

Ranks 16–30 (EP6): Richarlison 15.87 · Havertz 15.38 · Brobbey 14.94 · McBurnie 14.47 · Barry 13.70 ·
Emersonn 13.58 · Wood 13.29 · Strand Larsen 13.20 · Georginio 12.39 · Awoniyi 12.36 · Osula 12.35 ·
Nmecha 12.19 · Isidor 11.65 · Wissa 11.33 · Solanke 11.23. Full set in the JSON.

## The price ladder — where money actually buys points

Best available EP6 at each price point, restricted to `p_start ≥ 0.45`:

| £m | Best forward | EP6 | Marginal EP6 | Verdict |
|---|---|---|---|---|
| 5.5 | Beto (EVE) | 16.21 | — | Rotation risk (p_start 0.51) is the price of entry here |
| 6.0 | Calvert-Lewin (LEE) | 21.43 | **+5.22 for +0.5m** | The single best step on the ladder |
| 6.5 | Mateta (CRY) | 22.36 | +0.93 for +0.5m | Thin |
| 7.0 | Šeško (MUN) | 20.96 | **−1.40 for +0.5m** | Negative. The dead zone |
| 7.5 | João Pedro (CHE) | 25.15 | +4.19 for +0.5m | Good step, back onto the frontier |
| 8.0 | Thiago (BRE) | 26.11 | +0.96 for +0.5m | Thin |
| 9.0 | Isak (LIV) | 27.46 | +1.35 for +1.0m | Thin, and buys HIGH uncertainty |
| 15.5 | Haaland (MCI) | 36.20 | +8.74 for +6.5m | 1.34 EP6 per £m — poor rate, unique ceiling |

**£6.0m and £7.5m are the only two efficient rungs.** Anything spent between them is wasted:
Mateta costs £0.5m more than Calvert-Lewin for +0.93 EP6, and Šeško costs £1.0m more for −0.47.

On Haaland: the upgrade rate is bad in isolation, but he is the only forward whose per-GW EP exceeds
6.0 in any gameweek, and his GW3 figure (7.72, COV at home) is the highest single-GW EP in the
position. He is a captaincy and Triple-Captain asset, and that value does not show up in EP6.
The £6.5m premium over Isak has to be funded from DEF/MID — that is the optimizer's call, not this
file's.

## Nailed cheap beats rotating premium

The most important structural result in the position this week. Eight cases where a cheaper player
with better minutes outscores a more expensive one:

| Expensive, rotating | Cheaper, nailed | Δ EP6 | Δ price |
|---|---|---|---|
| Ekitiké 7.5 (p_start 0.07) | McBurnie 5.5 (0.60) | **+10.20** | −2.0m |
| Havertz 7.5 (0.45) | Mateta 6.5 (0.75) | **+6.98** | −1.0m |
| N.Jackson 6.5 (0.24) | Beto 5.5 (0.51) | **+6.24** | −1.0m |
| Marmoush 7.0 (0.23) | Beto 5.5 (0.51) | **+6.18** | −1.5m |
| Havertz 7.5 (0.45) | Calvert-Lewin 6.0 (0.78) | **+6.05** | −1.5m |
| Osula 6.0 (0.30) | Woltemade 6.0 (0.70) | **+5.85** | same price |
| Welbeck 6.0 (0.28) | Barry 5.5 (0.48) | +2.85 | −0.5m |

**Havertz at £7.5m is the position's biggest trap.** FPL has priced him level with Gyökeres on the
strength of a 577-minute season and a 23/24 peak that is now two seasons old. He competes with
Gyökeres and G.Jesus for one role. Two forwards £1.0–1.5m cheaper beat him by ~6-7 EP6.

**Osula vs Woltemade is the cleanest illustration** — same club, same £6.0m price, and the only
difference is p_start (0.70 vs 0.30). That gap alone is worth 5.85 EP6. Newcastle field three £6.0m
forwards (Woltemade, Wissa, Osula) for one starting berth; only the incumbent is priced correctly.

## Minutes model

The dominant term. p_start was set from starts and minutes in 2025/26, the club's depth chart, the
`status` / `chance_of_playing_next_round` flag, price and ownership as proxies for editorial
expectation, penalty order as evidence of designated-starter status, and the new-signing cap.

| Tier | p_start | Who |
|---|---|---|
| Nailed | 0.85–0.93 | Haaland (34 starts), Thiago (**37 of 38** — the most nailed forward in the game), Watkins (33/33/32 across three seasons), Isak |
| Near-nailed | 0.70–0.82 | Gyökeres, Calvert-Lewin, João Pedro, Mateta, Evanilson, Woltemade, Igor Jesus, Brobbey, Šeško |
| Contested | 0.44–0.68 | Strand Larsen, David, Gonzalo, McBurnie, Richarlison, Georginio, Emersonn, Beto, Barry, Solanke, Wood |
| Rotation lottery | 0.20–0.45 | Havertz, Nmecha, Osula, Wissa, Isidor, Awoniyi, Zirkzee, Marmoush, N.Jackson, Welbeck, Delap, Muniz |
| Non-playing | ≤0.10 | Ekitiké (injured), Ferguson (injured), Tzimas (injured), and every £4.5m enabler |

New signings with zero PL history are capped at p_start 0.70 per the cold-start rule and carry HIGH
uncertainty: **David** (BHA), **Gonzalo** (FUL), **Emersonn** (IPS), **Rodríguez** (BOU),
**Emegha** (CHE), **Thomas-Asante** / **Cherif** (COV). Their rates come from a foreign or
Championship league with a strength discount applied.

### Chelsea and Coventry are minutes sinks

CHE and COV each field **seven** forwards priced £4.5–7.5m. Chelsea's is the deepest rotation in the
league: João Pedro (0.77) is the only one worth owning, and even he loses ~0.04 p_start from GW3
onward for European rotation. N.Jackson (£6.5m, 0.24), Welbeck (£6.0m, 0.28) and Delap (£5.5m, 0.25)
are all priced as starters and are not.

## DefCon is dead for forwards — do not spend a slot chasing it

Forwards need **CBIT + recoveries ≥ 12** per match. Ranked by 2025/26 defensive-contribution per 90:

| Player | DC/90 | vs T=12 | P(hit) |
|---|---|---|---|
| Richarlison | 6.77 | 0.56× | 0.05 |
| Georginio | 6.64 | 0.55× | 0.05 |
| Zirkzee | 6.52 | 0.54× | 0.05 |
| Solanke | 6.41 | 0.53× | 0.05 |
| Thiago | 5.87 | 0.49× | 0.03 |
| Haaland | 3.17 | 0.26× | 0.03 |

**Not one forward in the league reaches even the 0.7×T rung (8.4/90)** of the GW1 mapping, so every
forward falls into the "below" bucket at ≤0.10. The term contributes 0.06–0.10 EP/GW to the best of
them and ~0.05 to everyone else. The handful of forwards showing DC/90 above 9 (Kostoulas 10.5,
Tzimas 10.2, Scarlett 12.9, Mheuka 90.0) are sub-600-minute sampling noise and were floored at 0.03;
the mapping was gated at 600 minutes for exactly this reason.

Corollary for the optimizer: the DefCon floor that makes cheap defensive MID/DEF attractive **does
not exist at FWD**. A forward's EP is appearance points plus attacking returns plus bonus, and
nothing else.

## Penalties and set pieces

Penalty duty is already inside xG (a spot-kick carries ~0.79 xG), so it is not added again. It
matters here as evidence of *role security* — a manager who hands a new arrival the penalties has
decided who starts.

| Nailed pen-1 taker | Club | £m | EP6 |
|---|---|---|---|
| Haaland | MCI | 15.5 | 36.20 |
| Isak | LIV | 9.0 | 27.46 |
| Thiago | BRE | 8.0 | 26.11 |
| Mateta | CRY | 6.5 | 22.36 |
| Calvert-Lewin | LEE | 6.0 | 21.43 |
| Woltemade | NEW | 6.0 | 18.20 |
| Gonzalo | FUL | 6.0 | 16.08 |
| McBurnie | HUL | 5.5 | 14.47 |

**Gonzalo (FUL) holding pen 1 on arrival is the strongest single role signal among the new
signings** — it is the main reason his p_start sits at 0.62 despite zero PL minutes. It does not
rescue him: Fulham are the weakest-attacking club with real data (ATT 0.75, Σλ_att 6.24, 17th).

Not a penalty taker, and it costs them: **Gyökeres** is pen 2 behind a midfielder at Arsenal, and
**João Pedro** has no penalty order at all despite being Chelsea's first-choice nine.
No forward in the set has direct-freekick or corner duty except Marmoush (FK 2, MCI), who does not
start.

## Per-GW leaders — captain and bench rotation

| GW | 1st | 2nd | 3rd |
|---|---|---|---|
| 1 | Haaland 6.31 | Gyökeres 4.89 | Thiago 4.62 |
| 2 | Haaland 5.62 | Isak 4.81 | João Pedro 4.38 |
| 3 | **Haaland 7.72** | Isak 5.05 | Watkins 4.76 |
| 4 | **João Pedro 5.48** | Haaland 5.15 | Isak 4.84 |
| 5 | Haaland 6.38 | Thiago 4.30 | Isak 4.28 |
| 6 | Haaland 5.02 | João Pedro 4.27 | Watkins 4.21 |

GW3 (MCI v COV at home, λ_att 2.78) is the standout captaincy spot in the window and the natural
Triple Captain candidate from this position. GW4 is the one gameweek Haaland does not lead — he is
away at Man Utd while Chelsea host Hull in the best attacking fixture of all 120 club-fixtures.

## £4.5m enablers (bench-boost value)

All seven available £4.5m forwards are effectively non-playing. Ranked, but the spread is noise:

| Player | Club | EP6 | p_start | Owned |
|---|---|---|---|---|
| Kusi-Asare | FUL | 3.99 | 0.08 | **7.5%** |
| Walle Egeli | IPS | 3.20 | 0.06 | 2.2% |
| Mheuka | CHE | 2.78 | 0.04 | 0.3% |
| Scarlett | TOT | 2.60 | 0.04 | 1.7% |
| Obi | MUN | 1.83 | 0.03 | 1.1% |
| Neave | NEW | 1.83 | 0.03 | 0.7% |
| Furo | BRE | 1.80 | 0.03 | 0.9% |

Kusi-Asare's 7.5% ownership — the most-held £4.5m forward — rests on 49 career PL minutes and zero
goals. That is enabler demand, not merit. **Treat the third-forward slot as a £4.5m sunk cost or pay
up to £5.5m+; there is nothing in between**, and no £4.5m forward carries meaningful Bench Boost
value.

## Ownership vs model — where the crowd and this file disagree

| Player | Owned | EP6 | Read |
|---|---|---|---|
| Haaland | 69.4% | 36.20 | Agree. Priced right, owned right |
| João Pedro | 63.9% | 25.15 | Agree — best EP6/£m of any premium, and CHE's fixtures improve from GW4 |
| Calvert-Lewin | **30.9%** | 21.43 | **Agree on the player, not the club.** 30 starts, 14 goals, pen 1 — but LEE rate ATT 1.06, Σλ_att 8.63 (11th), and the window closes ARS(a) at λ_att 0.98 (his GW6 EP drops to 2.86, the worst decline in the top 10) |
| Thiago | 17.2% | 26.11 | **Under-owned.** 37 of 38 starts, pen 1, and the best risk-adjusted premium in the position |
| Isak | 16.5% | 27.46 | Fair, but the HIGH flag is real — see below |
| Brobbey | **14.4%** | 14.94 | **Over-owned.** 22 starts is the entire case. xG90 0.282 at a club rated ATT 0.79 with Σλ_att 6.55 (16th) and a hard run GW3–5 |
| Watkins | 10.6% | 24.53 | Fair. Most durable non-Haaland striker, on a below-average attack |
| Gyökeres | 9.5% | 23.55 | Fair-to-under. ARS is the only club with a top-third attacking fixture in **all six** GWs |
| David | 0.2% | 17.94 | **Under-owned at the price**, but BHA Σλ_att 7.58 (14th) caps it and the HIGH flag applies |

**Thiago (BRE, £8.0m, 17.2%) is the pick this file would defend hardest.** He is 1.35 EP6 behind
Isak for £1.0m less, at MED rather than HIGH uncertainty, with p_start 0.90 against 0.84. Caveat:
the fixture analyst flags Brentford's ATT 1.21 rating as MEDIUM-uncertainty and unconfirmed until
GW3, and Thiago's bonus ratio (0.98 per goal-equivalent) is the worst of any 20-goal forward here.

## Model

```
EP = P(app pts) + (E[min]/90) × (xG90×4 + xA90×3) × mult × 1.079
             + bonus_ratio × (E[min]/90) × (xG90 + 0.5×xA90) × mult × 1.079 × 1.03
             + 2 × P(DefCon hit) × p_start × minutes_scale
             − (E[min]/90) × (YC/90 + 3 × RC/90)
E[min] = p_start × mins_per_start + (1 − p_start) × P(cameo) × 20
mult   = λ_att(fixture) / (1.439 × ATT_club)
```

Two mechanical gates sit on top: `chance_of_playing_next_round == 0` hard-zeroes GW1, and the DefCon
mapping is only applied to players with ≥600 minutes of prior sample (below that it is floored at
0.03, because sub-600-minute per-90 rates are noise).

Clean sheets are worth 0 to forwards and goals-conceded does not apply, so those terms are absent.
λ_att comes from the per-club-fixture table in `fixtures.md` unmodified; the 1–10 ticker deciles were
not used as inputs anywhere.

### Deviation 1 — the fixture multiplier double-counted club strength (affects every position)

The A3 spec defines `attack multiplier = λ_att / league-average λ`. That is wrong, and materially so.
`λ_att = 1.54 × ATT_i × DEFW_j` already contains the player's **own** club attack index, and a
player's observed xG90 was earned while playing for that same club — so `ATT_i` enters twice.
The correct denominator is the club's own season-average fixture, `1.439 × ATT_i`, which leaves only
the opponent's `DEFW_j` and the home/away split in the multiplier.

Impact, using Haaland: the spec formula gives him a GW3 multiplier of 1.93 and an EP6 of **43.35**
(7.2/GW against 6.29/GW actual last season). The corrected form gives 1.39 and **36.20** (6.03/GW).
Strong-club attackers were inflated ~15–20% and weak-club attackers deflated by the same mechanism.
**This applies identically to the GKP / DEF / MID analysts — escalated below.**

### Deviation 2 — returns calibrated against 25/26 actuals

The model was replayed over 2025/26 for the 19 forwards with ≥1500 minutes, using their actual start
counts, actual per-90 rates and a neutral fixture, and compared to actual points per gameweek. Raw,
it under-predicted by 0.149 pts/GW. A single least-squares scale on the returns block (attack +
bonus) of **1.079** removes that:

| | mean bias | RMSE |
|---|---|---|
| Raw | −0.149 pts/GW | 0.307 |
| Calibrated (×1.079) | **−0.007 pts/GW** | **0.262** |

RMSE 0.26 pts/GW ≈ 10 points over a season. Worst residuals: Mateta +0.67 (he has under-finished his
xG in each of the last two seasons), João Pedro −0.45 (9 assists from 1.96 xA). Both were folded back
into those players' forward priors rather than left in the error term.

A separate **×1.03** sits on the bonus term for the 26/27 BPS changes: removing the tackled penalty
helps forwards, who are tackled often; the CBI→BPS cut from 1/2 to 1/3 barely touches them; improved
GK save BPS takes a small slice of the podium back. Net small positive, and the least-confident
number in the model.

### Deviation 3 — share-coherence cap on unevidenced rates

A player's xG90 implies a share of his club's expected goals. Where the prior rests on real minutes
at the *current* club, the observed rate is itself the evidence of that share and stands. Where it
rests on a foreign league, a Championship season or a sub-1200-minute sample, the implied share is
capped at 0.35 of the club's λ_att/GW so an unevidenced rate cannot exceed what the club is modelled
to create. It bound on five players:

| Player | Club | xG90 before | after |
|---|---|---|---|
| Awoniyi | COV | 0.450 | 0.338 |
| Gonzalo | FUL | 0.400 | 0.365 |
| McBurnie | HUL | 0.330 | 0.310 |
| Nmecha | LEE | 0.520 | 0.503 |
| David | BHA | 0.450 | 0.442 |

## Uncertainty and escalations

### Freshness gate — flagged players in the top 30

| Player | £m | Flag | Effect |
|---|---|---|---|
| **Šeško** (MUN) | 7.0 | `d`, **75%**, shin injury | Ranked 9th on p_start 0.62 for GW1. If ruled out, Zirkzee (p_start 0.30 in GW1 for this reason alone) inherits MUN's best-in-league opening pair — HUL(a) λ_att 2.10 then IPS(H) 2.25. **Re-check before the deadline.** |
| **Ekitiké** (LIV) | 7.5 | `i`, Achilles, **0%**, unknown return | EP6 **4.27**, GW1 hard-zeroed. Achilles tendon layoffs run 3–6 months; scored at p_start 0 in GW1 rising to 0.14 by GW6. A £7.5m asset at ~0.7 EP/GW — do not buy pre-news. His absence is what makes Isak near-nailed. |
| Welbeck (CHE) | 6.0 | `d`, 75% | Already a 0.28-p_start rotation option |
| Rodríguez (BOU) | 6.0 | `d`, 75% | New signing **and** injured — two HIGH factors stacked |
| Abraham (AVL) | 5.5 | `d`, 75%, knock | Third choice |
| Ferguson (BHA) | 5.0 | `i`, **0%**, back **10 Oct** | GW6 at the earliest. Not an asset in this window |
| Tzimas (BHA) | 5.5 | `i`, **0%**, unknown | 132 career PL minutes |
| Wright (COV) | 5.5 | `i`, **0%**, thigh, unknown | Pen 1 when fit; ramped 0 → 0.38 |

Four players carry `chance_of_playing_next_round: 0` — Ekitiké, Wright, Tzimas and Ferguson. That is
an explicit statement that they will not feature in GW1, so **their GW1 EP is hard-zeroed** rather
than carrying a cameo tail. Their GW2–6 values remain a ramped recovery estimate and should be
re-derived from news, not trusted as a schedule.

Eleven forwards are carried at **EP6 = 0.0**: eight have left the club (`status: u` — Ünal,
Markelo, Uche, Hirst, Piroe, Bassette, Destan, Burstow) and three are injured with no return date
and zero career PL minutes (Madjo, Mateo Joseph, Danns). They are in the JSON so the optimizer sees
a complete position and cannot pick them.

### Fixture-analyst caveats, as applied

- **Defensive ratings are assumption-grade at GW1.** Irrelevant to this file. Clean sheets are worth
  0 to forwards and goals-conceded does not apply, so no forward EP here depends on any P(CS)
  number. Forwards are the position **least** exposed to the zeroed split-strength fields.
- **Promoted clubs COV/HUL/IPS are HIGH uncertainty; avoid outright.** Honoured. Every promoted-club
  forward carries HIGH uncertainty, a Championship-discounted rate, and the share cap where it bound.
  Best of them is McBurnie at EP6 14.47 — and **~60% of that is appearance points**, with HUL last
  in the league on Σλ_att (5.29) and a hard defensive run GW3–6. Awoniyi (COV) is the only one with
  real PL output (10G/1395 min at NFO in 22/23) and opens ARS(a) λ_att 0.63 then MCI(a) 0.73, two of
  the three worst attacking fixtures in the entire window.
- **Cup rotation is unmodelled in the ticker** and was applied here: a 0.02–0.05 p_start haircut from
  GW3 onward for MCI, ARS, CHE, LIV, MUN and TOT forwards, heaviest at Chelsea.
- **CRY finishing underperformance (LOW flag)** applied to Mateta: xG90 cut from 0.587 to 0.495,
  combining the club-level xGI-vs-actual gap with his own two-season under-finishing.
- **BRE ATT 1.21 unconfirmed until GW3 (MEDIUM)** — carried as the reason Thiago is MED rather than
  LOW uncertainty despite being the most nailed forward in the game.
- **GW6 is the least reliable column** (20-day international break splits GW5 from GW6). Treat GW6 EP
  as indicative.

### Escalations to the orchestrator

1. **The A3 spec's attack multiplier is wrong for every position, and one sibling file already has
   it.** `λ_att / league-average λ` double-counts the player's own club attack index.
   `players-DEF.md` (line 29–30) uses `xG90·6·(λ_att/1.435)` — the uncorrected form — so its
   attacking terms are inflated for strong-club defenders and deflated for weak-club ones. The
   effect is smaller there than at FWD, because a defender's EP is dominated by appearance, clean
   sheet and DefCon rather than attacking returns, but it still biases ARS/MCI/CHE defenders upward
   against LEE/BOU/HUL by roughly 1–3 EP6. **`players-GKP.md` is unaffected** (a goalkeeper has no
   attacking term, and it correctly drives P(CS) from λ_def). **MID will be the worst-affected
   after FWD.** Either propagate `mult = λ_att / (1.439 × ATT_club)` to the other analysts and
   re-run, or accept that FWD EP is on a different scale from DEF/MID EP — which would distort
   every budget trade-off the optimizer makes across positions. Fix `agents/player-analyst.md`
   before GW2 regardless.
2. **`fpl players --format json` reports `minutes: 0` for returning loanees**, because bootstrap
   season aggregates are keyed to FPL elements rather than career history. N.Jackson (CHE) shows 0
   minutes and 0 xG but has 5,021 PL minutes and 24 goals across 23/24–24/25; Wilson (BRE) shows 0
   but played 1,234 minutes last season; Ferguson (BHA) likewise. Any agent reading the filtered
   view without cross-checking `history_past` will write these players off. `prior-season.json` and
   the element summaries are correct — the CLI view is the trap.
3. **No £4.0m forward exists** (floor £4.5m, against £4.0m at GKP and DEF). The optimizer's budget
   arithmetic needs this.
4. **Šeško's 75% shin flag** is the one top-10 selection that could move on deadline-day news.
5. **DefCon contributes nothing at FWD.** If a squad is being built around a DefCon points floor,
   that thesis has to be carried entirely by DEF and MID.

## Handoff to the squad optimizer

- **Two efficient price rungs only: £6.0m and £7.5m.** Do not buy at £6.5–7.0m.
- **Calvert-Lewin (£6.0m, EP6 21.43, 3.57 EP6/£m)** is the best value in the position and the
  natural third forward — with the caveat that his GW6 (ARS away) is the weakest tail in the top 10.
- **Thiago (£8.0m)** is the best risk-adjusted premium; **João Pedro (£7.5m)** has the best premium
  EP6/£m and the best fixture swing (CHE turns from GW4).
- **Haaland is a captaincy asset, not a value asset.** GW3 is the Triple Captain spot from this
  position; GW4 is the only week he is not the best forward.
- **Max-3-per-club interacts here**: CHE and COV each list 7 forwards, BHA and IPS 5, and NEW fields
  three at £6.0m. Only one forward per club is worth owning in every case except Everton, where Beto
  (0.51) and Barry (0.48) genuinely split the role and neither is startable with confidence.
- **Avoid**: Havertz (£7.5m, p_start 0.45), Ekitiké (£7.5m, injured), Brobbey (over-owned at 14.4%),
  every promoted-club forward, and Strand Larsen (£6.0m, 26 starts, 4 goals — minutes without
  threat, the trap in the value band).
- **Bench**: no £4.5m forward has Bench Boost value. If a £4.5m slot is needed, it is a pure enabler.
