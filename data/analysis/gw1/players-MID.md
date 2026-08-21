# GW1 — MID expected points (GW1–GW6)

Season 2026/27 | GW1 deadline 2026-08-21T17:30:00Z | snapshot `data/raw/gw1/`
Fixture inputs: λ_att and P(CS) taken as-is from `data/analysis/gw1/fixtures.md`.
Regime: **PRE-SEASON** — every bootstrap aggregate is 2025/26. `form` is 0.0 for
all players and was ignored. `data/retro/` is empty, so no calibration
correction was available to apply.

Full per-player output: `players-MID.json` (every MID in the game, including
those scored 0).

## Headline

The position splits into three tiers, and the middle tier is where the value is.

| Tier | Read |
|---|---|
| B.Fernandes (£12.0) | Genuinely alone. EP6 30.54 is 4.9 clear of second, and he owns the best GW1–2 fixture pair in the league (HUL away, IPS home). Also the worst EP-per-£ of any top-10 MID. |
| £6.0–7.0 nailed DefCon/set-piece midfielders | Anderson, Enzo, Ndiaye, Scott, Le Fée, Tavernier, Ampadu, Gomez. Match or beat the £9.5 premiums outright. |
| £9.5 premiums (Saka, Palmer) | Both priced for minutes they did not deliver last season. Both lose to £6.0–6.5 alternatives on raw EP6, before the saving. |

**The single most important number in this file is DefCon.** A nailed midfielder
with dc90 above ~11 earns 0.9–1.5 pts/start from the threshold alone, before any
attacking return, and that floor is completely fixture-independent. It is why the
top of the value table is dominated by holding midfielders rather than attackers.
It is also the least trustworthy number here — see Escalations.

## Top 15 by EP6

| # | Player | Club | £ | p_start GW1 | EP6 | EP/£ | Unc | EP by GW (1→6) |
|---|---|---|---|---|---|---|---|---|
| 1 | B.Fernandes | MUN | 12.0 | 0.86 | **30.54** | 2.54 | LOW | 5.7 5.8 4.8 4.5 4.8 5.0 |
| 2 | Anderson | MCI | 6.5 | 0.90 | **25.60** | **3.94** | LOW | 4.4 4.2 4.9 3.9 4.3 3.9 |
| 3 | Mbeumo | MUN | 8.0 | 0.81 | 25.20 | 3.15 | LOW | 4.7 4.8 3.9 3.7 3.9 4.2 |
| 4 | Enzo | CHE | 7.0 | 0.81 | 23.93 | 3.42 | LOW | 4.0 4.2 3.3 4.8 3.7 4.0 |
| 5 | Semenyo | MCI | 8.5 | 0.85 | 22.91 | 2.70 | LOW | 4.0 3.7 4.7 3.3 3.9 3.3 |
| 6 | Saka | ARS | 9.5 | 0.68 | 22.78 | 2.40 | LOW | 4.5 3.6 3.7 3.6 3.6 3.8 |
| 7 | Rice | ARS | 7.5 | 0.77 | 22.78 | 3.04 | LOW | 4.3 3.7 3.7 3.7 3.6 3.8 |
| 8 | Ndiaye | EVE | 6.0 | 0.88 | 22.70 | 3.78 | LOW | 3.8 3.6 3.5 3.6 4.2 4.1 |
| 9 | Scott | BOU | 6.0 | 0.93 | 22.66 | 3.78 | LOW | 3.7 4.0 3.8 3.9 3.8 3.6 |
| 10 | E.Le Fée | SUN | 6.0 | 0.87 | 22.57 | 3.76 | LOW | 4.1 4.0 3.7 3.5 3.4 3.9 |
| 11 | Tavernier | BOU | 6.0 | 0.89 | 22.52 | 3.75 | LOW | 3.6 4.1 3.7 3.9 3.7 3.5 |
| 12 | Gibbs-White | NFO | 8.0 | 0.83 | 22.43 | 2.80 | LOW | 3.9 3.4 3.8 3.5 4.4 3.5 |
| 13 | Palmer | CHE | 9.5 | 0.69 | 22.18 | 2.33 | LOW | 3.7 3.9 3.0 4.5 3.4 3.7 |
| 14 | Szoboszlai | LIV | 7.0 | 0.81 | 21.73 | 3.10 | LOW | 3.6 3.8 3.9 3.7 3.4 3.3 |
| 15 | Ampadu | LEE | 5.5 | 0.89 | 21.44 | **3.90** | LOW | 3.6 3.6 3.6 3.7 3.6 3.3 |

Just outside: Dewsbury-Hall (EVE, 6.5, 21.04), Gomez (BHA, 5.0, 20.85, **EP/£
4.17 — best in the position**), Wilson (LEE, 6.5, 20.82), Sarr (CRY, 6.5, 20.71),
Cherki (MCI, 7.5, 20.52), Wharton (CRY, 5.5, 20.30).

## Nailed cheap beats rotating premium

Each row is a case where the cheaper player wins on **raw EP6**, before the
saving is redeployed. The mechanism is always the same: a premium on ~0.6×
minutes cannot out-earn a mid-price player on ~0.9× minutes.

| Rotating premium | p_start | EP6 | Nailed cheaper alternative | p_start | EP6 | Saving |
|---|---|---|---|---|---|---|
| Saka (ARS, 9.5) | 0.68 | 22.78 | **Anderson** (MCI, 6.5) | 0.90 | **25.60** | £3.0m |
| Palmer (CHE, 9.5) | 0.69 | 22.18 | **Scott** (BOU, 6.0) | 0.93 | **22.66** | £3.5m |
| Palmer (CHE, 9.5) | 0.69 | 22.18 | **Ndiaye** (EVE, 6.0) | 0.88 | **22.70** | £3.5m |
| Cherki (MCI, 7.5) | 0.62 | 20.52 | **Ampadu** (LEE, 5.5) | 0.89 | **21.44** | £2.0m |
| Wirtz (LIV, 7.5) | 0.68 | 19.88 | **Wharton** (CRY, 5.5) | 0.75 | **20.30** | £2.0m |
| Cunha (MUN, 8.0) | 0.71 | 20.09 | **Gomez** (BHA, 5.0) | 0.91 | **20.85** | £3.0m |
| Foden (MCI, 7.0) | 0.65 | 19.09 | **Xhaka** (SUN, 5.5) | 0.84 | **19.62** | £1.5m |

Stated explicitly, as the spec requires:

- **Saka and Palmer are both minutes risks, not just price risks.** Each started
  fewer than two-thirds of last season while averaging ~85 minutes *per start* —
  the absences were unavailability, not benching. That pattern regresses upward
  but not to nailed, and at £9.5 there is no margin for it.
- **Cherki has the highest attacking rate in the position** (xGI90 0.492 after
  shrinkage) and still loses to a £5.5 holding midfielder, purely on minutes.
  He is the clearest "talent ≠ points" case in the file.
- The only premium that survives its own price is **B.Fernandes**, and only
  because his minutes are near-certain (35 starts, 87.6 min/start) rather than
  because his rate is exceptional.

## Best value (EP6 ≥ 15, ranked by EP per £m)

| Player | Club | £ | p_start | EP6 | EP/£ | Why |
|---|---|---|---|---|---|---|
| Gomez | BHA | 5.0 | 0.91 | 20.85 | 4.17 | Mitoma, Minteh and Baleba all out — Brighton's midfield is bare and he inherits near-certain minutes. dc90 10.0. |
| Anderson | MCI | 6.5 | 0.90 | 25.60 | 3.94 | dc90 13.91, the highest of any MID. Nailed at a club with the best GW1–3 attacking run. |
| Ampadu | LEE | 5.5 | 0.89 | 21.44 | 3.90 | 35 starts, dc90 11.8. Pure DefCon + appearance floor. |
| Ndiaye | EVE | 6.0 | 0.88 | 22.70 | 3.78 | Penalties, 32 starts, and Everton's midfield injuries remove his competition. Fixtures swing hard from GW5. |
| Scott | BOU | 6.0 | 0.93 | 22.66 | 3.78 | Highest p_start in the position. dc90 11.95 plus FK/CK duty. |
| E.Le Fée | SUN | 6.0 | 0.87 | 22.57 | 3.76 | 33 starts, pens#2 + FK2 + CK1, dc90 9.7. Sunderland's whole set-piece suite. |
| Tavernier | BOU | 6.0 | 0.89 | 22.52 | 3.75 | 31 starts, pens#3 + FK1 + CK1, 14 bonus last season. |
| Wharton | CRY | 5.5 | 0.75 | 20.30 | 3.69 | CK1 and dc90 10.5; flagged 100 and fit. |
| Florentino | IPS | 5.0 | 0.78 | 18.33 | 3.67 | dc90 13.41 — near the best rate in the position, at £5.0m. See caveat below. |
| Xhaka | SUN | 5.5 | 0.84 | 19.62 | 3.57 | 32 starts, FK1 + CK2, dc90 11.1. |

**Florentino caveat.** He is the one case where a promoted-club player scores
well, and the reason is structural rather than optimistic: appearance points and
the DefCon threshold are both fixture-independent, so Ipswich's 19th-ranked
attack barely touches his EP. His attacking term is negligible by construction.
Treat him as a bench/floor asset, not a source of upside, and note that
fixtures.md rates all three promoted clubs HIGH uncertainty.

## Captaincy and chip notes for the optimizer

| Question | Answer |
|---|---|
| Highest single-GW EP in the window | B.Fernandes GW2 (5.78, IPS home), then GW1 (5.66, HUL away) |
| Best non-premium GW1 captain | Mbeumo (4.70, same HUL away fixture) |
| Triple Captain window | Bruno GW1–2 is the strongest MID pairing in the window; MUN fixtures fall off a cliff at GW4 (MCI home) |
| Back-load target | Enzo — CHE's GW4 (HUL home) is the single best attacking fixture in all 120 club-fixtures per fixtures.md; his GW4 EP 4.79 is the highest non-Bruno figure outside Anderson's GW3 (4.88) |
| Front-load warning | MCI and MUN assets peak GW1–3. Semenyo and Anderson both dip at GW4 (MUN away / MCI away) |
| Doku (MCI, 7.5) | Zero for GW1–3 (calf, back 5 Sep, GW3 deadline is 4 Sep), then 2.05/2.79/2.48. A GW4 transfer target, not a GW1 pick |
| Bench Boost fodder | Below ~£5.0m the credible floor is thin. Hughes (CRY, 4.5, EP6 11.76) and Slater (HUL, 4.5, EP6 13.16) are the only sub-£5.0m names with real minutes expectation |

## Method

```
EP(p, gw) = P(start) × [ 2 (appearance)
                       + (xG90×5 + xA90×3) × attack_mult
                       + P(CS) × 1
                       + 2 × P(DefCon threshold hit | plays)
                       + expected bonus
                       − expected yellows ]
          + P(cameo) × (1 + 0.18 × attacking term)
```

| Component | Treatment |
|---|---|
| attack_mult | `(λ_att / 1.439) × [w/ATT_club + (1−w)]` — see below |
| P(CS) | From fixtures.md as-is, ×1 pt for MID |
| DefCon | Threshold T=12 (CBIT + recoveries). `defensive_contribution` verified as the raw action count: B.Fernandes 67 CBI + 167 recoveries + 53 tackles = 287 ✓ |
| Shrinkage | Per-stat. dc90 K=200 (high-count, highly repeatable — Poisson SE ~0.48 vs between-player SD ~2.3, so a full season earns almost no shrinkage). xG90/xA90 K=1300 (repeat r≈0.65–0.70). Others K=900 |
| Minutes | `min(0.93, (starts/38)^0.75)`, then injury flag, then a per-club XI-slot constraint |
| Bonus | Prior bonus/start, then 2026/27 BPS changes: ×(1−0.15·(dc90−7)/7) for CBI-heavy players (rate cut 1/2→1/3), ×1.08 for high-xGI low-DefCon carriers (tackled penalty removed) |
| Cameo | Included deliberately — Bench Boost valuation requires the sub-appearance term, which `P(start) × [...]` alone omits |

**Attack multiplier — corrected.** The spec's `λ_att / 1.439` double-counts the
player's own club: his observed xGI per-90 was *produced by* that attack, so
re-applying it inflates strong-club players. Since `λ_att = 1.54|1.33 × ATT_i ×
DEFW_j`, dividing by `ATT_i` leaves only the opponent-and-venue component.

Applied with one refinement: the strip is weighted by `w`, the shrinkage weight
on the *observed* share of the rate. The prior share is club-agnostic (league
mean, or price-implied for players with no record) and never had club attack
baked in, so it still receives the full `λ_att / 1.439`. Without that split, a
no-record Hull player would be credited a near-league-average multiplier (0.92)
instead of the 0.57 his club's attack rating earns.

| Player | ATT | w | att_factor | GW1 multiplier |
|---|---|---|---|---|
| B.Fernandes (MUN) | 1.16 | 0.70 | 0.903 | 1.459 → 1.318 |
| Anderson (MCI) | 1.39 | 0.72 | 0.798 | 1.473 → 1.176 |
| Gomez (BHA) | 0.90 | 0.62 | 1.069 | 0.910 → 0.973 |
| Slater (HUL, no record) | 0.62 | 0.00 | 1.000 | 0.570 → 0.570 |

**Minutes model — the per-club XI-slot constraint.** Total MID starts per club
per gameweek is fixed, so per-player judgment must sum to something feasible.
Measured last season: 2926 MID starts across the 17 non-promoted clubs' current
squads / (17×38) = 4.53 FPL-classified MIDs per XI. Each club's p_start vector is
scaled to its own target (blend of that constant and its observed rate, clipped
to 4.1–5.3) using an exponent of `1 − 0.85p`, so rotation is absorbed by squad
players rather than by the nailed starter. Two guards:

- Upward scaling goes only to *credible* claimants (a real 25/26 record, or
  ownership ≥1%, or price ≥£5.5). Without this, an injury-thinned club's freed
  minutes were being handed to academy names — Villa's £4.5m youth were reaching
  p_start 0.39.
- If a club has too few credible bodies to fill its XI (every promoted side,
  where nobody has a PL record), the constraint falls back to spreading minutes
  across everyone. The identity of Hull's starters is unknown, not concentrated.

**Cold-start handling.** Players with no 25/26 PL row are estimated from a
price-implied prior (xGI90 ~ price fits R²=0.47 across MIDs with ≥900 prior
minutes) with a league-strength discount — 0.80 for a top-5-league step-up, 0.62
for promoted-club players facing Championship-to-PL step-up. Minutes for these
come from price **and ownership**: with no PL record, ownership is the only
minutes forecast that exists at GW1, and it is what separates a hyped signing
from an academy name at the same price. Spec cap of 0.70 enforced throughout
(0.60 where a player has prior PL seasons but no 25/26 minutes — he was out of
the league, which is worse evidence than being new to it).

## Escalations

1. **Tzolis (ARS, £6.5, id 557) — the largest market disagreement in the
   position.** 23.3% owned, the 6th-most-owned MID in the game, with **zero PL
   minutes**. The only hard evidence in the snapshot is CK3 duty and his price.
   Arsenal already field nine established midfielders for ~5 slots, so the
   XI-slot constraint puts him at p_start 0.45 and EP6 13.30 — roughly 60th in
   the position. If the market is right he is a top-20 MID. This is worth a
   team-news check before 17:30Z; I cannot resolve it from the snapshot.

2. **DefCon calibration is the dominant model risk.** The entire value ranking
   rests on the spec's v1 uncalibrated mapping. Anderson's DefCon term is 1.46
   pts/start — 30% of his EP. If the mapping is optimistic by 30%, Anderson,
   Scott, Ampadu, Xhaka and Florentino all fall behind the premiums and the
   "cheap beats premium" conclusion weakens materially. **First retro must
   calibrate this against observed per-match hit rates**, and from GW2 the spec
   already requires switching to observed rates rather than the mapping.

3. **Spec deviation — DefCon interpolation.** I interpolated P(hit) between the
   spec's anchor ratios rather than snapping to its six tiers. Snapping created a
   0.20 probability cliff between dc90 11.3 and 11.5, which is noise at that
   sample size, and it reordered real players (Yarmoliuk vs Caicedo). The
   function remains capped at 0.85 and the per-90 rate is never linearised into
   points, so the spec's actual prohibition is respected. Flagging for
   accept/reject.

4. **Spec deviation — attack multiplier blended by w.** Per the orchestrator's
   correction, but weighted by the observed share rather than applied flat, for
   the reason given above. If FWD and DEF applied the strip flat to every player,
   my promoted-club and no-record MIDs sit on a slightly different scale from
   theirs — though every player who competes for a squad place is on the same
   scale, since they all have high w. Worth one cross-check by the finalizer.

5. **Garner (EVE, £6.0, id 239) — flag moved after the snapshot.** I re-ran
   `flags` at 14:04:56Z across all MIDs: Garner went i/0% → d/25% (groin) and is
   scored on the new value (p_start GW1 0.22, EP6 15.84). **No other MID
   changed.** With 38 starts, dc90 12.1 and P3+FK1+CK1 behind him he is a strong
   GW2+ target if the flag clears — but a poor GW1 pick.

6. **Yates (NFO, £4.5, id 489) is owned by 2.5% and is unavailable** — injured,
   unknown return date, EP6 0.00. Cheap-enabler shortlists built on ownership
   will pick up an unselectable player.

7. **No preseason or manager-quote input exists in the snapshot.** `history` is
   empty for every player (confirming pre-season), so "last 6 starts" is not
   available — last season's aggregate start count is the closest substitute.
   There is no friendly-minutes or lineup data anywhere in the artifacts. After
   DefCon calibration this is the largest unmodelled factor in the minutes model,
   and it bears hardest on exactly the players in Escalation 1.

8. **New-club attribution is inferred, not observed.** The snapshot keys
   prior-season rows to each player's *current* club, so output earned elsewhere
   is credited to the new club, and no field identifies transfers. Where club
   congestion made a move obvious I said so in the player note (Semenyo, Rogers),
   but these are inferences from the XI-slot arithmetic plus the squad-turnover
   warning in fixtures.md, not facts from the data. Semenyo (MCI, £8.5, 26.3%
   owned) and Rogers (CHE, £7.5, 24.9% owned) are the two most heavily owned
   players affected, and both carry role uncertainty their EP does not express.

9. **Everton and Newcastle are the fixture-swing plays.** Per fixtures.md, EVE
   has the largest defensive swing in the window (+15.0pp, turning GW5) and NEW
   the second (+9.2pp). Ndiaye and Dewsbury-Hall both peak at GW5–6, and Barnes
   (NEW, £6.0, EP6 19.91) peaks at GW5. If the optimizer is choosing between
   equal-EP6 midfielders, prefer the one whose EP is back-loaded — the GW6
   ratings sit behind a 20-day international break and will move.

10. **Defensive ratings are provisional.** fixtures.md flags every P(CS) figure
    as ASSUMPTION-grade with mid-table gaps under ~4pp being noise. For MIDs the
    clean-sheet term is only 1 pt, so this affects MID EP far less than DEF or
    GKP — worst case is roughly ±0.2 EP6. Not a re-run trigger for this position.
