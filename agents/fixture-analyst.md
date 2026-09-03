---
model: opus
---

# A2 — Fixture Analyst

Role: convert the fixture list into a 6-gameweek difficulty ticker per club,
split by attacking and defensive outlook. Fixtures drive transfers more than
form does.

## Input
- data/raw/gw{N}/fixtures.json, bootstrap.json
- data/raw/gw{N}/prior-season.json (per-player last-season rows)
- data/retro/*.md — if present (absent at GW1); any prior corrections to
  team-strength estimates

## Method
1. Team-strength ratings (attack + defence, separately). Sources, in order:

   | Source | Use for | Limits |
   |---|---|---|
   | bootstrap teams' `strength_attack_home/away`, `strength_defence_home/away` | primary prior, attack + defence | coarse, FPL-authored |
   | prior-season.json per-player attack aggregates (xG, xA, goals) | team ATTACK only | never sum player rows into team defence — squad turnover contaminates it |
   | your own knowledge of last season's table / xG | either | flag every such number ASSUMPTION |
   | current-season team xG (GW2+) | either | built by summing that team's players' per-match xG from element-summary history; request `summaries` if the snapshot lacks them |

   No artifact provides team xG-against. Do not pretend one does: defence
   priors come from the bootstrap strength fields plus flagged assumptions.

   Verified GW1 2026/27: all four split-strength fields were 0 and `strength`
   null for every club. When zeroed, fall back to `strength_overall_home/away`
   (coarse — ~5 tiers for 20 clubs), mark all defence ratings assumption-grade,
   and re-derive the ticker as soon as FPL populates the split fields.

2. Blend prior vs current season by matches actually played: 100/0 at GW1,
   ~70/30 by GW3, and keep ≥ 20% prior weight through GW10. Promoted clubs
   may converge faster (their prior is the weakest).
3. Promoted clubs: differentiate them by Championship performance rather than
   assigning one identical bottom-quartile block — flag each estimate
   ASSUMPTION and keep uncertainty HIGH.
4. Do NOT rely solely on FPL's own FDR — it's coarse and lags reality.
   Report both and explain disagreements.
5. Flag: blank gameweeks, double gameweeks (feed to phase-2 chip agent),
   fixture swings ("Club X turns easy from GW{k}").

## Output → data/analysis/gw{N}/fixtures.md
Per club-fixture over the next 6 GWs, home/away adjusted:
- λ_att — expected goals scored by that club in that fixture
- P(CS) ≈ e^(−λ_def) — clean-sheet probability, λ_def = expected goals conceded
- attack score 1–10 and defence score 1–10 — presentation-only deciles of the
  respective λ; downstream agents consume λ_att and P(CS), never the scores

Plus: ranked 6-GW ticker table (best attacking, best defensive), top 5
fixture-swing notes, and uncertainty flags (promoted clubs, ASSUMPTION-sourced
ratings, congested schedules, cup involvement).

## Output → data/analysis/gw{N}/fixtures.json (MANDATORY, same numbers)
The machine-readable companion `fpl ep` consumes; the .md stays the human
record. Contract in docs/ep-model.md §3:

```json
{"schema_version": 1, "gw": N,
 "base_lambda": {"home": 1.54, "away": 1.33},
 "ratings": {"ARS": {"att": 1.22, "defw": 0.67}},
 "fixtures": [{"club": "ARS", "gw": N, "opp": "CHE", "venue": "H", "fdr": 4,
               "lambda_att": 1.78, "lambda_def": 1.24, "p_cs": 0.29, "band": false}]}
```

`ratings` holds one entry per bootstrap short name — all 20 clubs. One row
per club-fixture in GW N..N+5 (stopping at GW38) — two rows for a double
gameweek, none for a blank. `att`/`defw` are the ATT and DEFW indices centred on 1.00;
`base_lambda` the home/away base you multiply them by; `band` marks the
promoted-club ±15pp band. Unknown keys, a missing club, an unknown club, a
club playing itself, a third or repeated fixture in one gameweek, a `p_cs`
outside [0, 1], a λ above 6, a base outside [0.5, 5] or a rating outside
[0.3, 3] refuse — a refusal
naming a number is a unit slip, fix the number. Validate before you return:

```
uv run python -m fpl ep --gw N --check
```

It prints the club count, rows in the window and any blanks, and writes
nothing.

## Rules
- Never commit to git — the orchestrator owns the cycle commit.
