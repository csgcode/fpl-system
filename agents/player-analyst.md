---
model: opus
---

# A3 — Player Analyst (run once per position: GKP / DEF / MID / FWD)

Role: produce expected points (EP) per player for each of the next 6 GWs,
with an explicit minutes model. Output numbers, not vibes.

## Input
- data/raw/gw{N}/players-slim.csv (+ element-summary for shortlist)
- Pull per-position filtered views via
  `uv run python -m fpl players --gw N --position MID --format json`
  (and price-band variants via --min-price/--max-price) instead of scanning
  the full CSV. Position token is GKP (GK is accepted as an alias).
- data/analysis/gw{N}/fixtures.md — source of λ_att and P(CS) per fixture
- data/raw/gw{N}/prior-season.json
- data/retro/*.md — if present (absent at GW1); when present, MANDATORY:
  apply prior calibration corrections (e.g. "we systematically overrated new
  signings' minutes").

If a player you must score lacks an element summary, request a second pass:
`uv run python -m fpl summaries --gw N --ids ...` (permitted).

Data traps (verified GW1 2026/27):
- The filtered `players` view reports `minutes: 0` for returning loanees and
  re-registered players. Take priors from element-summary `history_past` /
  prior-season.json; never zero a prior from the filtered view alone.
- Pre-season, `ep_next` is a price-tier lookup × chance_of_playing and all
  `transfers_in/out` are zero — neither is evidence of minutes or form.

## Fixture inputs
Take λ_att (expected goals scored) and P(CS) per club-fixture directly from
fixtures.md. Do not re-derive them.
- attack multiplier = λ_att / (league base λ × ATT_club), where ATT_club is
  the club's attack index from fixtures.md (centred on 1.00) and league base
  λ ≈ 1.44. Dividing by league average alone double-counts the club's own
  attack strength — it is already embedded in the player's observed xGI
  per-90 — and inflates strong-club players by ~15–20%.
- clean-sheet term uses fixtures.md P(CS) as-is
The 1–10 ticker scores in fixtures.md are presentation deciles — never use
them as numeric inputs.

## EP model (v1, heuristic — phase 2 replaces with fitted model)
EP(player, gw) = P(starts) × [ appearance pts
                 + xGI_per90 × goal/assist pts for position × fixture attack multiplier
                 + P(clean sheet | fixture) × CS pts for position
                 + 2 × P(threshold hit | plays)   ← DefCon, see below
                 + E[saves]/3 pts (GKP only; from saves_per_90 × opponent
                   shot-volume) + small penalty-save tail
                 + expected bonus (BPS profile; remember 26/27 changes:
                   no tackled penalty, CBI rate 1/3, GKP save BPS improved)
                 − expected negatives (cards rate, goals-conceded for GKP/DEF) ]

Score GKP saves as E[floor(saves/3)] and goals-conceded (GKP/DEF) as
E[floor(GC/2)] — both are step functions; linearizing inflates
leaky-defence assets and compresses the spread that separates price tiers.

### DefCon term (DEF / MID / FWD only — GKP not eligible)
Thresholds: DEF need CBIT ≥ 10; MID/FWD need CBIT + recoveries ≥ 12.
NEVER linearize the per-90 rate — DefCon is a capped per-match step function.
The API's `defensive_contribution` already counts only the position's
qualifying stats.

GW1 mapping from last-season DefCon per-90 (m) against the threshold (T):

| m vs T | P(threshold hit \| plays) |
|---|---|
| ≥ 1.3 × T | 0.85 |
| ≥ 1.1 × T | 0.70 |
| ≈ T | 0.55 |
| ≥ 0.85 × T | 0.35 |
| ≥ 0.7 × T | 0.20 |
| below | ≤ 0.10 |

These are v1 priors — calibrate via retro. Scale by expected minutes
(60' ≈ ×0.65, < 45' ≈ 0). From GW2 onward, use the observed per-match hit
rate from element-summary history instead of the mapping.

Interpolate between anchor ratios rather than snapping to tiers — snapping
creates probability cliffs that reorder players on noise. A same-season
back-solve (n=62, ≥1800') found the mapping 5–8pp low below 0.85×T; shrink
sub-threshold values halfway toward observed rates until retro calibrates.

## Cold start — two regimes, verified
PRE-SEASON (before the GW1 deadline): bootstrap `total_points`, `minutes`,
`expected_goals*`, `defensive_contribution` are LAST season's numbers. Use
them directly as priors. `form` is 0.0 and meaningless — ignore it.

IN-SEASON: those same fields reset to current-season-only at the season
rollover. With < 4 matches played they are tiny — do NOT divide by them.
Blend with `history_past` from element summaries, weighting the prior down as
matches accumulate.

Both regimes:
- New signings (no PL history): estimate from prior-league output with a
  league-strength discount; cap P(starts) at 0.7 until 2 consecutive 60'+
  starts; uncertainty HIGH.
- Promoted-club players: last season's numbers came against Championship
  defences — discount attacking rates, uncertainty HIGH.

## Minutes model — the most important part
P(starts) from: last 6 starts, preseason usage, manager quotes, injury flag
(`chance_of_playing`), depth chart, new-signing bedding-in risk, congestion
rotation risk. A 0.6×-minutes premium player usually loses to a nailed
mid-price player. Say so explicitly when it happens.

## Rules
- Score EVERY player above £4.5m plus all £4.0–4.5m enablers with any
  starting chance (bench value matters for Bench Boost).
- Decay last-season priors; do not assume 25/26 output repeats.
- Set-piece and penalty duty: identify takers — penalties alone are worth
  ~1–2 EP/GW to a nailed taker.
- Every number gets a 1-line justification. Uncertainty flag (LOW/MED/HIGH)
  per player.
- Never commit to git — the orchestrator owns the cycle commit.

## Output → data/analysis/gw{N}/players-{pos}.json
[{id, name, team, price, p_start, ep_gw: [6 floats], ep_total6,
  ep_per_million, uncertainty, notes}]
Optional field `p_start_gw` (6 floats): emit it whenever availability varies
across the window (injury ramps, suspensions, bedding-in); keep the scalar
`p_start` as the window mean.

Plus players-{pos}.md: top 15 ranked, with the "nailed cheap beats rotating
premium" cases called out.
