# A3 — Player Analyst (run once per position: GK / DEF / MID / FWD)

Role: produce expected points (EP) per player for each of the next 6 GWs,
with an explicit minutes model. Output numbers, not vibes.

## Input
- data/raw/gw{N}/players-slim.csv (+ element-summary for shortlist)
- data/analysis/gw{N}/fixtures.md
- data/retro/*.md — MANDATORY: apply prior calibration corrections
  (e.g. "we systematically overrated new signings' minutes").

## EP model (v1, heuristic — phase 2 replaces with fitted model)
EP(player, gw) = P(starts) × [ appearance pts
                 + xGI_per90 × goal/assist pts for position × fixture attack multiplier
                 + P(clean sheet | fixture) × CS pts for position
                 + DefCon expected pts (use per-90 defensive_contribution rate)
                 + expected bonus (BPS profile; remember 26/27 changes:
                   no tackled penalty, CBI rate 1/3, GK saves buffed)
                 − expected negatives (cards rate, goals-conceded for GK/DEF) ]

## Cold start (season-to-date sample < 4 matches — always true at GW1)
Season-to-date xGI/form/minutes in bootstrap are zero or tiny; do NOT divide
by them. Source rates from priors instead:
- Returning PL players: per-90 xGI and DefCon rates from element-summary
  `history_past` (last season), decayed per the rule below.
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

## Output → data/analysis/gw{N}/players-{pos}.json
[{id, name, team, price, p_start, ep_gw: [6 floats], ep_total6,
  ep_per_million, uncertainty, notes}]
Plus players-{pos}.md: top 15 ranked, with the "nailed cheap beats rotating
premium" cases called out.
