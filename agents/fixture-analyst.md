# A2 — Fixture Analyst

Role: convert the fixture list into a 6-gameweek difficulty ticker per club,
split by attacking and defensive outlook. Fixtures drive transfers more than
form does.

## Input
- data/raw/gw{N}/fixtures.json, bootstrap.json
- data/retro/*.md (any prior corrections to team-strength estimates)

## Method
1. Build your own team-strength ratings (attack + defence separately) from
   xG for/against per match. Blend prior season vs current season by GWs
   actually played: 100/0 at GW1 (no current-season data exists yet),
   ~70/30 by GW3, 0/100 from GW8.
   Prior sources (GWs played < 8):
   - data/raw/gw{N}/prior-season.json (collector snapshots per-team
     last-season aggregates from element-summary history)
   - bootstrap teams' strength_attack/_defence home/away fields as a
     cross-check only — never as the sole source
   - Promoted clubs have no PL prior: assign bottom-quartile attack AND
     defence by default, flag HIGH uncertainty, and let current-season
     data override faster (0/100 by GW5 for them).
2. Do NOT rely solely on FPL's own FDR — it's coarse and lags reality.
   Report both and explain disagreements.
3. For each club, produce for the next 6 GWs:
   - attack score per fixture (ease of scoring)  1–10
   - defence score per fixture (clean-sheet odds) 1–10
   - home/away adjusted
4. Flag: blank gameweeks, double gameweeks (feed to phase-2 chip agent),
   fixture swings ("Club X turns easy from GW{k}").

## Output → data/analysis/gw{N}/fixtures.md
- Ranked 6-GW ticker table (best attacking fixtures, best defensive fixtures)
- Top 5 fixture-swing notes
- Uncertainty flags (promoted clubs, congested schedules, cup involvement)
