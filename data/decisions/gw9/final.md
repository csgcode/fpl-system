# GW9 Final (2026/27)

Deadline **2026-10-31T11:00:00Z**. Built from
data/decisions/gw9/squad-proposal.md (first optimizer run of the cycle) and
data/decisions/gw9/review.md (verdict APPROVE, no HIGH finding). The
previous final is data/decisions/gw8/final.md.

**No transfers, hit 0. Free transfer banked (2 at the GW10 deadline).
Triple Captain on Haaland. 3-4-3, Haaland (C, 3xc), Tavernier (V).
Predicted GW9 55.458 with the captain doubled, 61.574 with the triple.**

## Freshness gate

`fpl flags --gw 9` refreshed at 2026-10-30 17:05:13 UTC on the proposal's
`Gate ids:` line (the 15 squad ids; no transfers-in), against baseline
`data/raw/gw9/.archive/bootstrap-20261030T163256_812100Z.json` (age 0.5h).
Exit 0. Delta: `data/raw/gw9/flags-delta-20261030T170513_603791Z.json`.

| Result | Detail |
|---|---|
| **PASS** | 0 of 15 gate ids changed. Calafiori d 75% (hip, news 24 Oct, unchanged); the other 14 status `a`; Haaland, Isak and Van Hecke chance 100. Pool (informational): 0 changed. |

## Entry state

`fpl my-team --gw 9` (session live): free transfers 1, made 0; bank 0.1;
budget 99.2. Equals the proposal's `team_value` 99.2 and `bank` 0.1; copied
unchanged. Chips: bboost, 3xc, freehit available; wildcard played (GW8).

## Squad — predicted points (calibration record)

`GW9 EP` = `ep_gw[0]`, `EP6` = `ep_total6`, `p_start GW9` = `p_start_gw[0]`
from `data/analysis/gw9/players-{pos}.json` (model 64ad9c9c), copied as
written there. Price = the proposal's reconstructed selling price (sum 99.1,
equal to the live `my-team` selling-price sum; individual rows may differ
by 0.1).

| Slot | Pos | Player | Id | Club | Price | GW9 EP | EP6 | p_start GW9 | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|
| 1 | GKP | Trafford | 385 | LEE | 5.0 | 3.52 | 22.28 | 0.95 | XI |
| 2 | DEF | Gabriel | 4 | ARS | 7.9 | 4.519 | 29.98 | 0.95 | XI |
| 3 | DEF | Hill | 60 | BOU | 5.5 | 4.385 | 26.36 | 0.95 | XI |
| 4 | DEF | Van Hecke | 112 | TOT | 4.9 | 4.189 | 24.26 | 0.95 | XI |
| 5 | MID | Mbeumo | 427 | MUN | 7.9 | 4.839 | 30.69 | 0.96 | XI |
| 6 | MID | Tavernier | 68 | BOU | 6.0 | 4.643 | 28.73 | 0.93 | XI · Vice |
| 7 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.405 | 25.86 | 0.94 | XI |
| 8 | MID | Barnes | 453 | NEW | 6.1 | 4.043 | 23.24 | 0.94 | XI |
| 9 | FWD | Haaland | 411 | MCI | 15.5 | 6.116 | 34.47 | 0.94 | XI · Captain (3xc) |
| 10 | FWD | Barry | 249 | EVE | 5.6 | 4.503 | 26.2 | 0.94 | XI |
| 11 | FWD | Isak | 379 | LIV | 9.0 | 4.18 | 28.26 | 0.88 | XI |
| 12 | GKP | Kinsky | 496 | TOT | 4.5 | 3.321 | 19.93 | 0.95 | Bench GK |
| 13 | MID | Gomez | 127 | BHA | 5.0 | 3.583 | 23.04 | 0.94 | Bench 1 |
| 14 | DEF | Justin | 332 | LEE | 4.5 | 3.216 | 22.51 | 0.95 | Bench 2 |
| 15 | DEF | Calafiori | 8 | ARS | 6.0 | 2.594 | 23.39 | 0.65 | Bench 3 |
| | | **Total** | | | **99.1** + bank 0.1 | | | | |

2 GKP / 5 DEF / 5 MID / 3 FWD. Clubs: ARS 2, BOU 2, LEE 2, TOT 2; MUN, MCI,
LIV, SUN, NEW, BHA, EVE 1 each. No club at 3.

## Starting XI — 3-4-3

Trafford; Gabriel, Hill, Van Hecke; Mbeumo, Tavernier, E.Le Fée, Barnes;
Haaland (C), Barry, Isak. XI EP 55.458 with the captain doubled
(`objective`); 61.574 with the triple.

The formation follows EP: Barry 4.503 (third forward) beats the fourth
defender options, Justin 3.216 and Calafiori 2.594 (p_start 0.65, hip 75%,
22 minutes as a substitute in R8). XI/bench outfield gap: Barnes 4.043 v
Gomez 3.583 (0.460, outside the 0.25 band). The only pair inside 0.25 is
the goalkeepers, Trafford 3.520 v Kinsky 3.321: higher EP starts.

## Captain and vice

| # | Player | GW9 EP | p_start GW9 | Gap to #1 |
|---|---|---|---|---|
| 1 | Haaland | 6.116 | 0.94 | — |
| 2 | Mbeumo | 4.839 | 0.96 | 1.277 |
| 3 | Tavernier | 4.643 | 0.93 | 1.473 |
| 4 | Gabriel | 4.519 | 0.95 | 1.597 |
| 5 | Barry | 4.503 | 0.94 | 1.613 |

**Captain Haaland** (Triple Captain), 1.277 clear, outside the 0.5 band.

**Vice Tavernier.** Mbeumo 4.839 v Tavernier 4.643 is inside 0.5 and both
clear p_start 0.85, so the tie is open to a suggestion; S8 (standing) breaks
it toward Tavernier (ret5 3/5 v 2/5; BOU ATT rank 2, FDR rank 1 v MUN 16th).
Cost of the steer (review F8): the vice is tripled under 3xc, so the gap if
Haaland misses is 0.588, and weighted by P(Haaland misses) ≈ 0.06 the
expected cost is about 0.04 EP. The S8 ledger row below, carried verbatim,
states 0.196; this figure supersedes it.

## Bench order

12 Kinsky (GK) · 13 Gomez 3.583 · 14 Justin 3.216 · 15 Calafiori 2.594.
Ordered by GW9 EP; gaps 0.367 and 0.622, none inside the 0.25 band. With a
3-DEF XI an absent defender skips Gomez and brings Justin.

## Transfers

None; hit 0. Free transfer banked: 1 now (live), 2 at the GW10 deadline
(6 Nov 18:30 UTC). Only five of 1543 legal singles are positive on blend;
the best, Calafiori → Silva +1.797 blend / −0.085 prior-only, fails the free
gate (blend < 2.0, prior sign flip). No hit plan reaches +6.0 gross.

Cost of waiting (review F11): Calafiori fell 0.1 this event on heavy net
transfers out and a second fall before GW10 is plausible, so holding costs
0.1–0.2 of team value, not "0.1 at most" as the proposal and the S7 ledger
row state. It does not change the decision.

## Chips

`chip: 3xc` on Haaland. Windows from bootstrap `chips` (set 1): 3xc GW1–19,
bboost GW1–19, freehit GW2–19; wildcard played GW8. One chip this GW; no
transfer chip in play.

Case: Haaland GW9 EP 6.116 v next-best captain Mbeumo 4.839; `ep_gw` GW9–14
6.116, 5.378, 6.208, 4.948, 5.916, 5.901. GW9 is within 0.092 of the window
best (GW11 FUL (H)), across an international break, and rests on his own
rates (xG90 0.756, penalties, 8/8 starts) and this week's team news. No
double gameweek in GW9–14. Expected gain over a plain captaincy +6.116.
Review F10 checked GW15–19: only HUL (H) GW16 is materially higher, and it
rests on a banded promoted-club rating (C5); the decision stands.

Chip plan (provisional): freehit GW16 (placeholder, no blank or double
known), bboost GW19 (last set-1 gameweek).

Execution (review F13): the chip rides the set-lineup POST. If the session
lapses before the deadline, 3xc must be set by hand on the website — a
planned but unactivated chip is the one irreversible loss in this plan.

## Accepted risks

| Review id | Severity | Risk | Why accepted |
|---|---|---|---|
| F5 | MED | Template exposure (carried from GW8 F3): Rogers 50.5%, De Cuyper 42.5%, Cherki 37.6%, Groß 45.8%, Raya 45.6% not held; the one held template player besides Haaland (Calafiori 49.1%) is on the bench at p_start 0.65. A haul from any lands as rank loss. | No move into any of them passes the gate; Calafiori → De Cuyper +0.050 / +0.389 is the only single positive on both readings, far short of 2.0. |

## Rationale summary

- Bank: no single passes the free gate; the best (+1.797 / −0.085) fails on
  blend and prior sign. Two free transfers at GW10 cover a reshape before
  ARS and MCI fixtures turn harder from GW12 (review F6).
- Hold Mbeumo: pool #1 MID on EP6 (30.69); Mbeumo → Gibbs-White −4.365 /
  −3.988 (S7 named-faller check).
- Triple Captain now: fixture-independent 6.116 on this week's news,
  within 0.092 of the window best, no double to wait for, and set 1 still
  has bboost and freehit to place before GW19.
- Calibration context: the GW8 wildcard squad scored 94 (XI predicted
  55.05); the retro shows no player mispriced enough to move for.

## Suggestions

Read data/suggestions.md through S8

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 6 | followed | both halves now complete: Ndiaye → Groß and Anderson → Schade inside the +14.449 blend / +5.210 prior-only triple; Ndiaye's marginal +2.503 / +0.665 and Anderson's +2.488 / +0.757 each clear the 2.0 gate on their own, so the steer broke no tie and the optimizer reached it unaided; EP6 delta of the row itself 0.00. The GW5 ledger's "Ndiaye half completed" was false in fact (never POSTed) and is superseded here |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |
| S3 | 6 | followed | Ndiaye → Groß made; marginal +2.503 blend / +0.665 prior against the plan without this sale (Scott + Anderson → E.Le Fée + Schade, +11.946 / +4.545), so the below-threshold clause was not needed |
| S4 | 6 | followed | Anderson → Schade made; marginal +2.488 blend / +0.757 prior against the plan without this sale (Scott + Ndiaye → E.Le Fée + Groß, +11.961 / +4.453); clears the gate on both readings, below-threshold clause not needed |
| S5 | 6 | followed | Scott → E.Le Fée made; EP6 0.00 for GW6–11 (status i, 0%); marginal +2.503 / +0.675 against the plan without this sale (Ndiaye + Anderson → E.Le Fée + Schade, +11.946 / +4.535) |
| S6 | 8 | followed | wildcard played at GW8, the timing the row left open (GW6 or GW8): the package +8.304 blend / +8.078 prior-only clears the chip gate against bank (+0.000); EP per GW over GW8–13 rises from 54.68 to 56.06 (336.354 / 6, captain included); the user's earlier hold today was withdrawn by the delegation quoted in this proposal; not taken: 60 per GW stays unreachable — the best package found on the post-Saka files is 56.06 |
| S7 | 7 | standing | honoured as a sell-side policy: of the named fallers only Mbeumo is still owned, a net faller again this event (in 87,670 v out 129,541, price 7.9 unchanged) but Mbeumo → Gibbs-White is −4.365 / −3.988 FAIL, not a small gap, so he is held; the squad's live faller is Calafiori (−0.1 this event, out 497,609 v in 23,332) and Calafiori → Silva +1.797 / −0.085 fails the free gate on blend and prior sign, which the policy never overrides — the cost accepted is at most 0.1 of team value before GW10, when 2 FTs are available; EP6 delta of the row 0.00 |
| S8 | 7 | standing | honoured: no transfer this cycle because no single passes the gate (best Calafiori → Silva +1.797 / −0.085), so no buy is judged under the row; it breaks the vice tie, Mbeumo 4.839 v Tavernier 4.643 inside 0.5 single-GW EP with the spec's p_start tie-break holding both, toward Tavernier (ret5 3/5 v 2/5; BOU ATT rank 2 and FDR rank 1 v MUN 16th, manager under pressure), a cost of 0.196 EP only if Haaland misses; EP6 delta of the row 0.00 |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW10 deadline: 1 live at GW9 (my-team, relayed) + 1 accrued, none used.
# team_value 99.2 and bank 0.1 are the live my-team budget and bank relayed by the orchestrator on 2026-10-30; no transfer this GW.
gw: 9
team_id: 8455344
team_value: 99.2
bank: 0.1
free_transfers_banked: 2
chip: 3xc
chips_used:
  - {chip: wildcard, gw: 8}
transfers_made: []
chip_plan:
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 385, name: Trafford, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: false, vice: false}
  - {id: 60, name: Hill, position: 3, captain: false, vice: false}
  - {id: 112, name: Van Hecke, position: 4, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 5, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 6, captain: false, vice: true}
  - {id: 542, name: E.Le Fée, position: 7, captain: false, vice: false}
  - {id: 453, name: Barnes, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: true, vice: false}
  - {id: 249, name: Barry, position: 10, captain: false, vice: false}
  - {id: 379, name: Isak, position: 11, captain: false, vice: false}
  - {id: 496, name: Kinsky, position: 12, captain: false, vice: false}
  - {id: 127, name: Gomez, position: 13, captain: false, vice: false}
  - {id: 332, name: Justin, position: 14, captain: false, vice: false}
  - {id: 8, name: Calafiori, position: 15, captain: false, vice: false}
```
