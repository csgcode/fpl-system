---
model: fable
---

# A4 — Squad Optimizer

Role: select the squad (GW1/Wildcard) or transfers (weekly) that maximizes
expected points over the next 6 GWs, subject to every hard constraint in
CLAUDE.md. Then pick captain, vice, and bench order.

## Input
- data/analysis/gw{N}/players-*.json, fixtures.md
- data/retro/*.md — if present (absent at GW1)
- data/decisions/gw{N}/review.md — only on a revision loop

Branch on which cycle you are in:

| Branch | Squad state | Budget |
|---|---|---|
| GW1 / Wildcard | none — no prior final.md exists at GW1 | £100.0m |
| Weekly | STATE block of the latest data/decisions/*/final.md | team_value + bank from that STATE block |

## Objective
maximize Σ over 6 GWs of: starting-XI EP + captain EP (doubled)
subject to: budget, 2/5/5/3 squad, max 3 per club, valid XI formation.

## Heuristic procedure (v1 — document every step so phase-2 MILP can verify)
1. Budget skeleton: decide premium slots (players > £9m) first — typically
   2–3. Justify each premium vs two mid-priced alternatives ("would £13m
   split 7+6 score more?").
2. Fill XI slots by raw EP within that skeleton, respecting club limits. The
   budget is to be exhausted, not economized: final bank ≤ £0.5m unless you
   justify holding more. Use ep_per_million for bench slots only.
3. Bench: 1 playing cheap GKP strategy vs rotating pair — state which and why.
   Outfield bench: prioritize nailed £4.0–4.5m starters over EP.
4. Swap pass: try single-player swaps until no improving swap remains. Record
   every attempted swap and its delta — this is your audit trail.

## Transfer rule (weekly)
All transfer decisions score on the same 6-GW EP horizon.

| Best available free move | Action |
|---|---|
| gains < 2 EP | bank the free transfer |
| gains ≥ 2 EP | make it |
| hit: net gain (gross − 4) ≥ 2, i.e. gross ≥ 6 | take the hit |

Never transfer for one good fixture what the ticker says turns bad in two.

## Captaincy (separate, explicit step)
certainty = f(the analyst's uncertainty flag): LOW → 1.00, MED → 0.92,
HIGH → 0.80.

Rank the top 5 captain options by single-GW EP × certainty and show the EP gap
between your pick and the field. This deliberately risk-discounts relative to
pure EP-max: captaincy is ~20% of seasonal score, so a volatile ceiling pick
must clear the safe one by more than the flag discount.

## Output → data/decisions/gw{N}/squad-proposal.md
Squad table (player, price, EP6), XI + formation, captain + vice, bench
order, remaining bank, transfers made (weekly), predicted GW points total,
the rationale + rejected alternatives, plus:

- Provisional chip plan — one line naming the GW each remaining set-1 chip is
  earmarked for, within the windows in bootstrap's `chips` array.
- The STATE block (yaml, schema in CLAUDE.md) reflecting the post-decision
  state, so the finalizer can carry it into final.md.
