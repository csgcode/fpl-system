# GW1 Red-Team Review — squad-proposal.md

Reviewed 2026-08-21 (~14:25 UTC), deadline 17:30 UTC. Inputs: squad-proposal.md,
players-{GKP,DEF,MID,FWD}.{md,json}, fixtures.md, players-slim.csv, plus a live
`flags` refresh (14:24:43Z) run by this reviewer.

## Verdict: **APPROVE**

No HIGH finding. The proposal's arithmetic, constraint compliance, captaincy
math, and search log all survived independent recomputation. Findings below are
MED/LOW; the MED items belong in final.md's accepted-risk list.

## Independent verifications (recomputed from raw data, not trusted)

| Check | Result |
|---|---|
| Budget | Σ price from players-slim.csv = **£100.0m exactly** (GK 10.0 + DEF 28.5 + MID 33.5 + FWD 28.0). Bank £0.0 ✓ |
| Position counts | 2 GK / 5 DEF / 5 MID / 3 FWD, 15 unique ✓ |
| Club counts | ARS 2, MCI 2, MUN 2, EVE 2, others 1 — all ≤3 ✓ |
| Formation | XI = 1 GK, 3 DEF, 5 MID, 2 FWD ✓ legal; XI is exactly the best 10 outfielders + Raya by GW1 EP ✓ |
| GW1 points claim | XI sums to 48.34; +6.31 captain = 54.65 ≈ 54.7 ✓ |
| Injury flags | `flags` re-run 14:24:43Z on all 15 ids: every player status `a`, no news, no `chance_of_playing` values. Šeško (75%), Garner (25%), Ekitiké (0%) correctly excluded ✓ |
| Snapshot freshness | Raw snapshot fetched 13:27Z today, <24h at deadline ✓ |
| Captaincy mapping | Discounts recomputed with LOW 1.00 / MED 0.92 / HIGH 0.80: Haaland 6.31, Gabriel 4.89, Mbeumo 4.70 — gap to #2 is 1.42, no pick within 0.5 EP ✓ |
| Per-player EP vs analyst files | All 15 EP6/GW1-EP/p_start/Unc values match the analyst JSONs (incl. Shaw 3.406→3.41 driving bench order Shaw > Thiaw) ✓ |
| Chip windows | meta.md bootstrap chips: WC/FH GW2–19, BB/TC GW1–19 — matches proposal; no chip at GW1; TC target (Haaland) held; path for all four set-1 chips remains open ✓ |
| Search-log spot probes | No improving single swap found in probes (Dubravka→Phillips −0.9 EP6, Shaw→Konsa −0.7, Thiaw→Canvot −1.9, Enzo→Szoboszlai −2.2, Kusi→any £4.5 FWD ≤0). FWD3-upgrade shapes correctly lose because FWD3 never enters the projected best-XI ✓ |

## Findings

### MED-1 — Two XI starters below the 0.85 minutes threshold
Mbeumo and Enzo both p_start 0.81, decaying to 0.77 by GW4 (European/cup
rotation priced, not predicted — cup calendars are absent from the snapshot).
Mitigation is real: both are their club's least-rotated attacker per the MID
notes, and first subs Shaw (0.90) / Thiaw (0.88) are genuine starters. The
tested fix (V5: Enzo→Ampadu) lost 1.42 objective points, so no change is
warranted. **Carry in final.md as accepted risk.**

### MED-2 — Dead bench: 2 of 4 bench slots non-playing
Kusi-Asare p_start 0.08, Dubravka 0.37. Verified unavoidable at FWD (no £4.5
forward exceeds p_start 0.10; floor is £4.5, and V1/V2/V9 showed a playing FWD3
costs ≥1.0 objective because FWD3 never makes the best XI). Consequences the
proposal already owns: auto-sub cover for a missing FWD routes through Shaw via
formation change, and Bench Boost is unusable until the GW10 wildcard rebuilds
the bench — consistent with the BB GW19 earmark. **Accepted risk; wildcard must
fix both slots.**

### MED-3 — Template-risk register is incomplete: João Pedro (63.9%) unlisted
The full >30%-owned template is: Haaland 69.4 (held), João Pedro 63.9 (**not
held**), B.Fernandes 51.5 (not held), Szoboszlai 41.7 (not held), Mbeumo 37.5
(held), Raya 37.2 (held), Calafiori 37.0 (not held), Calvert-Lewin 30.9 (not
held). Risk #7 names only Tzolis (23.3%) and Bruno. Every fade is numerically
deliberate — V10 evaluated a Haaland+João Pedro squad and it converged 1.04
short; Enzo beats Szoboszlai by 2.20 EP6 at equal price; Richards/Thiaw beat
Calafiori on EP6, price and floor share — but the aggregate exposure (holding 3
of 8 template players) is a real rank-volatility position, and João Pedro's GW4
(CHE v HUL, best fixture of all 120) is the single week it is most likely to
bite. **final.md must list the JP/Szoboszlai/Calafiori/DCL fades explicitly as
deliberate differentials**; JP is the natural GW3–4 transfer target if
correction is wanted.

### MED-4 — Portfolio-level DefCon exposure exceeds the single-player bound
Risk #1 bounds Anderson only, but six squad players carry material DefCon terms
(Anderson, Scott, Ndiaye, Tarkowski, Richards, Thiaw). Partial reassurance the
proposal doesn't cite: the DEF analyst's same-season back-solve found the
mapping **exact at and above the threshold** — where Tarkowski/Richards/Thiaw
sit — so the uncalibrated risk concentrates in the MID mapping (Anderson,
Scott). A 30%-optimistic MID mapping costs the squad ~4 EP6, not enough to
prefer the tested Bruno/premium structures (−1.21 was the gap). **Accepted
risk; retro-analyst must calibrate DefCon hit rates from GW1 actuals, as
already escalated by both analysts.**

### MED-5 — GW1 EP leans on assumption-grade promoted-club ratings (confirmed as controlled)
Gabriel+Raya (COV H, P(CS) 53%) and Mbeumo+Shaw (HUL a, 44%) draw GW1 value
from ratings fixtures.md says have "no empirical basis"; the GW3 TC earmark
(Haaland v COV) rests on the same. The proposal's controls are correct — these
players also top LOW/MED rankings on later, evidenced fixtures, and the TC
carries an explicit confirm-gate after GW1–2. No change requested; do not pull
the TC forward without that confirmation.

### LOW-1 — Misstated margin in the Haaland KEEP row
"His EP6 36.20 leads the game by 8.7" — 8.74 is the gap to the next **forward**
(Isak 27.46); the game-wide runner-up is B.Fernandes 30.54, a 5.66 gap. The
operative evidence (full-squad no-Haaland test, −4.27) is unaffected. Correct
the wording in final.md.

### LOW-2 — Post-window fixture cliff for the Everton pair
Tarkowski+Ndiaye peak GW5–6 (IPS H, HUL a) then draw CHE(H), ARS(a), NEW(a) in
GW7–9 (verified from fixtures.json). MUN's tail is LEE(a)/BOU(H)/CHE(a). Not a
trap — free transfers accrue weekly and nothing forces a hit — but the weekly
cycle should plan EVE exits around GW6–7 rather than discover them.

### LOW-3 — Price risk minimal but one-sided
£0.0 bank, and Dubravka is the one hold with a plausible early fall (20.3%
hedge-ownership unwinds if Kinsky is confirmed TOT #1). Bounded at £0.1 of
value; no pre-deadline action. Pre-season transfer flows are zeroed, so no
early/late timing edge exists this window.

### LOW-4 — MID attack-multiplier correction applied on a slightly different scale
MID blended the `1/ATT_club` strip by shrinkage weight w (documented deviation);
DEF/FWD applied it flat. All owned MIDs are high-w so no squad decision flips,
but `agents/player-analyst.md` should be fixed to one convention before GW2 —
already escalated by the FWD analyst.

## Checklist items with no finding

| # | Item | Result |
|---|---|---|
| 2 | Stale/missed flags | None — live refresh clean for all 15 |
| 4 | Concentration | No club supplies >2 attack-dependent players (MCI pair is attack+DefCon; ARS pair is defence-side) |
| 7 | Hit justification | N/A — GW1, no transfers, no hits |
| 8 | Captaincy | Haaland clears #2 by 1.42 discounted; vice Gabriel is the correct discounted-EP runner-up |
| 9 | Recency bias | None found — pre-season regime, picks are xG/shrinkage-based; no pick rests on an unrepresentative haul |
| 10 | Chip path | All four set-1 chips reachable before GW19; nothing foreclosed; TC target held |
