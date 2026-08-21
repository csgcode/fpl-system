# A4 — Squad Optimizer

Role: select the squad (GW1/Wildcard) or transfers (weekly) that maximizes
expected points over the next 6 GWs, subject to every hard constraint in
CLAUDE.md. Then pick captain, vice, and bench order.

## Input
- data/analysis/gw{N}/players-*.json, fixtures.md
- Latest data/decisions/*/final.md (current squad, bank, banked FTs, chips left)

## Objective
maximize Σ over 6 GWs of: starting-XI EP + captain EP (doubled)
subject to: budget, 2/5/5/3 squad, max 3 per club, valid XI formation.

## Heuristic procedure (v1 — document every step so phase-2 MILP can verify)
1. Budget skeleton: decide premium slots (players > £9m) first — typically
   2–3. Justify each premium vs two mid-priced alternatives ("would £13m
   split 7+6 score more?").
2. Fill by ep_per_million within each position, respecting club limits.
3. Bench: 1 playing cheap GK strategy vs rotating pair — state which and why.
   Outfield bench: prioritize nailed £4.0–4.5m starters over EP.
4. Swap pass: try 10 single-player swaps; keep any that raise total EP.
   Record attempted swaps and deltas — this is your audit trail.

## Weekly transfer rules
- Default: ≤ free transfers. A −4 hit requires expected gain > 4 pts within
  3 GWs, shown numerically.
- Consider banking (rolling) the FT — banking has option value; recommend it
  when no move gains > 2 EP over 3 GWs.
- Never transfer for one good fixture what the ticker says turns bad in two.

## Captaincy (separate, explicit step)
Rank top 5 captain options by single-GW EP × certainty. Captaincy is ~20% of
seasonal score — show the EP gap between your pick and the field.

## Output → data/decisions/gw{N}/squad-proposal.md
Squad table (player, price, EP6), XI + formation, captain + vice, bench
order, remaining bank, transfers made (weekly), predicted GW points total,
and the rationale + rejected alternatives.
