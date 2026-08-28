# GW2 — Forward Expected Points (GW2–GW7)

Snapshot `data/raw/gw2/` (fetched 2026-08-28T09:45:31Z) | fixtures from
`data/analysis/gw2/fixtures.md` | corrections from `data/retro/gw1.md`
Machine-readable output: `data/analysis/gw2/players-FWD.json` (73 forwards scored)

## Headline

**Gameweek 1 was a role-information gameweek, not a points gameweek.** Three of
the position's twenty most-owned forwards played zero minutes — Watkins,
Gyökeres and Kusi-Asare — and four different clubs inverted the depth chart we
modelled at GW1. The EP numbers below move far more on `p_start` than on any
change to attacking rates.

| Change | Evidence |
|---|---|
| **Havertz is Arsenal's 9, not Gyökeres** | Havertz 90', 1 goal, 34 BPS. Gyökeres not in the 20 that appeared, no injury news, price −0.1. |
| **Wissa is Newcastle's 9** | Wissa 90', 1.00 xG, 1 assist. Woltemade 0'. Osula 55' and now out (foot, 0%). |
| **Watkins did not play** | Villa fielded a **strikerless XI** at Brighton and lost 4-0. No news, price −0.1. |
| **Manchester United field no forward** | Mbeumo, Cunha and Fernandes started. Šeško came on for 23'. Zirkzee 0'. |
| **Barry beat Beto at Everton** | Barry 78', goal, 37 BPS, 8 pts. Beto 11'. |
| **Gonzalo is nailed at Fulham** | 90', 0.73 xG, goal, 33 BPS, and FUL pen 1. |
| **Coventry start two forwards** | Thomas-Asante 69' and Simms 69' — the only playing £5.0m forwards in the game. |
| **Šeško's shin flag cleared** | status `a`, 100% — the injury risk resolved and a minutes risk replaced it. |

## Top 15 by 6-GW expected points

| # | Player | Club | £ | p_start | GW2 | GW3 | GW4 | GW5 | GW6 | GW7 | EP6 | EP/£m | Unc |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Haaland | MCI | 15.5 | 0.93 | 5.32 | 6.90 | 5.22 | 6.67 | 5.17 | 6.47 | **35.75** | 2.31 | LOW |
| 2 | Isak | LIV | 9.0 | 0.88 | 4.64 | 4.76 | 5.09 | 4.53 | 4.18 | 4.27 | **27.47** | 3.05 | MED |
| 3 | Thiago | BRE | 8.0 | 0.90 | 4.08 | 5.01 | 4.25 | 4.48 | 4.52 | 4.30 | **26.64** | 3.33 | MED |
| 4 | João Pedro | CHE | 7.6 | 0.86 | 4.39 | 3.51 | 5.41 | 4.04 | 4.61 | 4.40 | **26.36** | 3.47 | MED |
| 5 | Wissa | NEW | 6.0 | 0.80 | 3.83 | 3.86 | 3.43 | 4.56 | 3.96 | 4.12 | **23.76** | 3.96 | MED |
| 6 | Gonzalo | FUL | 6.0 | 0.84 | 3.83 | 3.71 | 3.35 | 3.65 | 3.74 | 4.51 | **22.79** | 3.80 | MED |
| 7 | Watkins | AVL | 7.9 | 0.68 | 2.38 | 3.47 | 3.29 | 3.51 | 3.35 | 3.54 | **19.54** | 2.47 | HIGH |
| 8 | Calvert-Lewin | LEE | 6.0 | 0.85 | 3.29 | 3.08 | 3.76 | 3.33 | 2.71 | 3.30 | **19.47** | 3.24 | MED |
| 9 | McBurnie ⚠ | HUL | 5.5 | 0.82 | 3.29 | 3.40 | 2.96 | 3.23 | 3.31 | 3.10 | **19.29** | 3.51 | HIGH |
| 10 | Emersonn ⚠ | IPS | 5.5 | 0.78 | 3.06 | 3.26 | 3.11 | 3.31 | 3.58 | 2.82 | **19.14** | 3.48 | HIGH |
| 11 | Mateta | CRY | 6.5 | 0.80 | 2.89 | 3.17 | 3.49 | 2.99 | 3.16 | 2.95 | **18.65** | 2.87 | MED |
| 12 | Barry | EVE | 5.5 | 0.72 | 2.81 | 2.87 | 2.98 | 3.14 | 3.19 | 2.93 | **17.92** | 3.26 | MED |
| 13 | Evanilson | BOU | 6.0 | 0.82 | 3.10 | 3.03 | 2.88 | 2.86 | 2.76 | 3.22 | **17.85** | 2.98 | MED |
| 14 | Igor Jesus | NFO | 6.0 | 0.82 | 2.67 | 3.10 | 2.90 | 3.19 | 2.72 | 2.56 | **17.14** | 2.86 | MED |
| 15 | Havertz | ARS | 7.5 | 0.64 | 3.00 | 2.91 | 2.91 | 2.55 | 2.76 | 2.55 | **16.68** | 2.22 | HIGH |

⚠ = C4-blocked, see below. Next five: Gyökeres 16.03, Richarlison 14.99,
Georginio 13.33, Šeško 13.32, Brobbey 13.28.

## Nailed cheap beats rotating premium — three live cases

The spec asks for this to be stated explicitly whenever it holds. At forward
this gameweek it holds three times, and every one of them points the same way.

| Rotating premium | vs | Nailed mid-price | EP6 gap | £ saved |
|---|---|---|---|---|
| **Watkins** 7.9, p_start 0.68 | ← | **Wissa** 6.0, p_start 0.80 | **+4.22** to Wissa | 1.9 |
| **Havertz** 7.5, p_start 0.64 | ← | **Gonzalo** 6.0, p_start 0.84 | **+6.11** to Gonzalo | 1.5 |
| **Šeško** 7.0, p_start 0.43 | ← | **Barry** 5.5, p_start 0.72 | **+4.60** to Barry | 1.5 |

Watkins is the sharpest of the three because we would be paying a premium
price for a player who **was not in his club's matchday twenty** and has no
injury note explaining it. A £7.9m asset at 0.68 minutes is the exact failure
mode the minutes model exists to catch.

The counter-case, stated for fairness: all three cheap alternatives have
exactly **one match** of role evidence, and all three sit at MED. Gyökeres
(16.03) still carries the better underlying rate of the two Arsenal forwards —
0.498 xG90 against Havertz's 0.393 — and is only 0.65 EP behind him on 0.10
less `p_start`. If Arsenal team news reverses, that gap closes immediately.

## Our three forwards

| Player | £ | p_start | GW2 | GW3 | GW4 | GW5 | GW6 | GW7 | EP6 | Δ vs GW1 model | Unc |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Haaland** | 15.5 | 0.93 | 5.32 | 6.90 | 5.22 | 6.67 | 5.17 | 6.47 | **35.75** | −0.45 | LOW |
| **Thiago** | 8.0 | 0.90 | 4.08 | 5.01 | 4.25 | 4.48 | 4.52 | 4.30 | **26.64** | +0.53 | MED |
| **Kusi-Asare** | 4.5 | 0.05 | 0.24 | 0.23 | 0.23 | 0.23 | 0.23 | 0.25 | **1.41** | **−2.58** | HIGH |

**Haaland and Thiago are both held on process, not on hope.** The retro is
explicit that GW1 was finishing variance — Thiago's 1.00 xG was the squad high
and Haaland's 0.74 was second — and the retro discipline note forbids shaving
FWD EPs for the −3.20 mean error. No such shave has been applied. Thiago
actually *rises*: Brentford's attack rating is now confirmed at 1.29 (3rd in
the league) on the round's highest team xG, so the GW1 MEDIUM flag on his club
lifts, and he keeps the penalty term the retro told us to keep.

**Kusi-Asare's slot is now confirmed dead, not assumed dead.** The GW1 model
priced him at 3.99 EP6 on an assumed 0.08 `p_start`. He was not in Fulham's
matchday twenty while Gonzalo played every minute. Observing the non-selection
rather than assuming it cuts him to **1.41 EP6** — 0.24 points a gameweek.

## For the optimizer: a genuinely playing £5.0m forward now exists

Asked explicitly. **Yes — two of them, and they are cheaper than the dead slot
is expensive.**

| Player | £ | p_start | EP6 | vs Kusi-Asare |
|---|---|---|---|---|
| **Thomas-Asante** (COV) | 5.0 | 0.70 | **13.17** | **+11.76** |
| **Simms** (COV) | 5.0 | 0.68 | **12.95** | **+11.54** |

Coventry started both of them for 69 minutes in GW1 — they play a genuine
front two, which is what makes both viable rather than one blocking the other.
For **£0.5m** the fourth bench slot converts from structurally incapable of
returning points into a slot that starts most weeks.

Two caveats the optimizer must price. Both carry **HIGH** uncertainty (zero and
280 career PL minutes respectively), and both are **C4-exposed** — Coventry's
own attack index, 0.65 and 80% assumption, is the largest term in their EP.
Buy them as bench cover that might return, never as a starting option.

This does **not** on its own make Bench Boost usable — the retro's MED-2 finding
covers four bench slots, and this fixes one.

### Best ≤£5.5m enabler

**Barry (EVE, £5.5m, 17.92 EP6, MED)** — the cleanest, and the only one of the
three £5.5m leaders that is not C4-blocked. He won the Everton role on the
pitch (78', goal, 37 BPS, 8 pts) while Beto got 11 minutes, and Everton's
attack turns easier from GW5. McBurnie (19.29) and Emersonn (19.14) both score
higher and both are unusable for the reason in the next section.

## C4 compliance — promoted-club exposure

C4 forbids a promoted-club-derived term from being the largest single EP
component of a **selected** player. Three of the top ten breach it:

| Player | Breach | Detail |
|---|---|---|
| **McBurnie** (HUL) | own club | Hull's ATT index 0.64 is 80% assumption with a ±15pp band, and it is his largest term in all six gameweeks. Prior is also stale — last PL season 2023/24 — so a 0.85 staleness decay is applied on top. |
| **Emersonn** (IPS) | own club | Same structure. Ipswich's DEFW moved more than any club's on a single match; the band exists to distrust exactly that. |
| **Thomas-Asante / Simms** (COV) | own club | As above. Acceptable **only** as bench cover, per the section above. |

**Haaland GW3 is a fourth, and it is the one that matters.** MCI v COV (H)
rates λ_att 2.59, and 63% of his 6.90 GW3 EP is that single attacking term.
Sensitivity across the ±15pp band on Coventry's defensive rating:

| COV DEFW | MCI λ_att | Haaland GW3 EP |
|---|---|---|
| 1.03 (band floor) | 2.20 | **6.18** |
| 1.21 (central) | 2.59 | **6.90** |
| 1.39 (band ceiling) | 2.98 | **7.59** |
| — | — | — |
| **GW5 MCI v SUN (H)** — band-free | 2.46 | **6.67** |

**Read for the C5 Triple Captain gate:** GW5 at 6.67 sits *above the GW3 band
floor* and only 0.24 below the GW3 central estimate. C5 requires the GW3 case
to rest on Haaland's fixture-independent EP alone; it cannot, because the
promoted-club term is the majority of that gameweek's number. The player-side
ledger therefore agrees with the fixture analyst — **GW5 is the better-evidenced
Triple Captain target, and deferring costs at most a quarter of a point.**

## Model notes

**Regime.** In-season, one match played. Bootstrap season-to-date fields are
one match and are never divided by. Attacking rates blend `history_past`
priors with the GW1 per-90 at **85/15** for players with real PL history and
**80/20** for players whose prior is itself an estimate (no PL history) — the
same asymmetry the fixture analyst applies, and for the same reason: a weaker
prior is displaced faster. Current-match per-90 rates are capped at 1.5 xG90 /
0.9 xA90 before blending, because a single 62-minute sample extrapolates
violently.

**Fixture multiplier.** `λ_att / (1.44 × ATT_club)`, taken from fixtures.md and
never re-derived. Dividing by the league base alone would double-count the
club's own attack strength, which is already inside the player's observed
xGI per-90.

**Minutes.** `p_start` is set from the GW1 team sheet first and the prior depth
chart second. Eight players carry a `p_start_gw` vector rather than a scalar —
Watkins, Havertz, Gyökeres, Georginio, Šeško, David, Osula, Ferguson — because
availability moves materially across the window. Sub appearances are modelled
separately (P(sub | no start) × ~18 minutes), which is what keeps non-starting
enablers above zero without inflating them.

**Clean sheets contribute nothing at forward** — the CS term is 0 for this
position, so Evanilson's and Georginio's GW1 shutouts add no points.

**Uncertainty tags follow C7 mechanically**: `p_start` < 0.85 → MED at best,
< 0.70 → HIGH. Only Haaland (0.93) qualifies for LOW. Havertz at 0.64 and
Watkins at 0.68 are both HIGH on that rule alone — under the GW1 tagging they
would have been LOW and received no rotation discount from the optimizer.

**Staleness decay.** Players with no ≥450-minute season in 2024/25 or 2025/26
take a ×0.85 on attacking rates: McBurnie, Abraham, Ferguson. Small-sample
`defensive_contribution` priors are shrunk toward the position mean (4.3) with
a 900-minute pseudo-count — without it Jebbison's 408-minute 15.4 dc90 would
have produced a fictitious DefCon floor.

## DefCon at forward — dead, and now measured to be dead

Per **C1** the v1 anchor mapping is used unchanged; the "5–8pp low below
0.85×T" shrinkage instruction is superseded and not applied.

The forward threshold is **CBIT + recoveries ≥ 12**. The highest prior dc90 in
the entire position is Richarlison's 6.47 — **ratio 0.54**, barely half the
threshold. Every forward sits in the "below 0.7×T" band, so the term is worth
at most 0.13 points per gameweek to anybody, and under 0.03 to the players we
actually own.

**C2 calibration log — FWD, GW1** (prior minutes ≥ 900, GW1 minutes ≥ 80).
Pool this with the DEF and MID logs for the GW4 slope re-test.

| Player | Club | prior dc90 | ratio | v1 P(hit) | GW1 DC | min | Hit? |
|---|---|---:|---:|---:|---:|---:|---|
| Georginio | BHA | 6.80 | 0.567 | 0.066 | 7 | 90 | N |
| Thiago | BRE | 6.05 | 0.504 | 0.052 | 5 | 82 | N |
| Havertz | ARS | 4.84 | 0.403 | 0.033 | 2 | 90 | N |
| Igor Jesus | NFO | 4.83 | 0.402 | 0.033 | 3 | 90 | N |
| João Pedro | CHE | 4.60 | 0.383 | 0.030 | 3 | 90 | N |
| Wissa | NEW | 4.16 | 0.346 | 0.024 | 8 | 90 | N |
| Calvert-Lewin | LEE | 3.68 | 0.307 | 0.019 | 2 | 90 | N |
| Isak | LIV | 3.20 | 0.266 | 0.014 | 1 | 90 | N |
| Haaland | MCI | 2.90 | 0.241 | 0.012 | 3 | 90 | N |
| **Σ** | | | | **0.283** | | | **0 hits / 9** |

Predicted 0.28 hits, observed 0. **No forward in the league reached the
threshold at GW1** — the highest count across all 73 was 8, reached by Wissa
and Evanilson, two-thirds of the way there. The position contributes 9 rows of
near-zero-information data
to the pooled sample; the GW4 slope test will have to be decided by DEF and MID.

## Flags for the finalizer's freshness gate

| Player | Flag | Why it matters |
|---|---|---|
| **Georginio** (BHA) | 75%, unspecified injury, added **2026-08-26** | Two days before the deadline. p_start opened at 0.55 for it. |
| **Gyökeres / Havertz** (ARS) | none — that is the problem | Gyökeres missed GW1 with **no news at all**. Arsenal team news is the single highest-value unknown in this position. |
| **Watkins** (AVL) | none | Same: a zero-minute premium with no explanation. |
| **Šeško** (MUN) | cleared to 100% | Flag resolved since GW1. Downgrade is now about role, not fitness. |
| **Osula** (NEW) | 0%, foot, added 2026-08-25 | New injury. Strengthens Wissa. |
| **Welbeck, Rodríguez, Emegha** | cleared to 100% | All resolved; none has a role. |

## Unmodelled

**Cup rotation.** The FPL API exposes no European or domestic-cup calendar, so
continental rotation is not in any number here. It bites hardest on MCI, ARS,
CHE, LIV and MUN — which is four of our top six. Haaland is not a rotation
risk; João Pedro and the Arsenal pair are.

**The 19-day international break between GW5 and GW6.** GW6 and GW7 EPs are the
least reliable in the window for every player, and the ramp vectors on Watkins,
Gyökeres and David all resolve inside it.
