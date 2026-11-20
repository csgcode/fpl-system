# GW11 Final (2026/27)

Deadline **2026-11-21T11:00:00Z**. Built from
data/decisions/gw11/squad-proposal.md (first optimizer run of the cycle) and
data/decisions/gw11/review.md (verdict APPROVE, no HIGH finding; MED F1, F2,
F3; LOW F4, F5). The previous final is data/decisions/gw10/final.md.

**Calafiori → De Cuyper, free, hit 0. 3 free transfers at the GW12 deadline.
No chip. 4-3-3, Haaland (C), Gabriel (V). Predicted GW11 58.405 for the XI
with the captain doubled.**

## Freshness gate

`fpl flags --gw 11` refreshed at 2026-11-20 11:19:49 UTC on the proposal's
`Gate ids:` line (the 15 squad ids, De Cuyper the one transfer-in), against
baseline `data/raw/gw11/.archive/bootstrap-20261120T110117_325694Z.json`
(age 0.3h). Exit 0. Delta:
`data/raw/gw11/flags-delta-20261120T111949_151858Z.json`.

| Result | Detail |
|---|---|
| **PASS** | 0 of 15 gate ids changed. All 15 status `a`; Van Hecke, Haaland and Isak carry cleared 100% flags. Pool (informational): 0 changed. |

## Entry state

`fpl my-team --gw 11` (session live): free transfers 3, made 0; bank 0.1;
budget 99.6. Equals the proposal's `team_value` 99.6 (the transfer swaps a
5.9 sale for a 5.5 buy, so bank 0.1 → 0.5 and the budget is unchanged);
copied unchanged. Chips: bboost and freehit available; wildcard played GW8,
3xc played GW9.

## Squad — predicted points (calibration record)

`GW11 EP` = `ep_gw[0]`, `EP6` = `ep_total6`, `p_start GW11` =
`p_start_gw[0]` from `data/analysis/gw11/players-{pos}.json` (model
64ad9c9c), copied as written there. Price = the proposal's reconstructed
selling price (De Cuyper at his purchase price); sum 99.1 + bank 0.5 = 99.6.

| Slot | Pos | Player | Id | Club | Price | GW11 EP | EP6 | p_start GW11 | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|
| 1 | GKP | Trafford | 385 | LEE | 5.0 | 3.578 | 22.53 | 0.95 | XI |
| 2 | DEF | Gabriel | 4 | ARS | 8.0 | 5.229 | 29.62 | 0.95 | XI · Vice |
| 3 | DEF | Van Hecke | 112 | TOT | 5.0 | 4.947 | 26.46 | 0.95 | XI |
| 4 | DEF | De Cuyper | 115 | BHA | 5.5 | 4.614 | 25.93 | 0.94 | XI (in) |
| 5 | DEF | Hill | 60 | BOU | 5.5 | 4.405 | 27.0 | 0.95 | XI |
| 6 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.706 | 28.44 | 0.95 | XI |
| 7 | MID | Tavernier | 68 | BOU | 6.3 | 4.547 | 28.3 | 0.95 | XI |
| 8 | MID | Mbeumo | 427 | MUN | 7.9 | 4.288 | 28.66 | 0.95 | XI |
| 9 | FWD | Haaland | 411 | MCI | 15.6 | 6.047 | 34.9 | 0.94 | XI · Captain |
| 10 | FWD | Isak | 379 | LIV | 9.1 | 5.306 | 29.41 | 0.93 | XI |
| 11 | FWD | Barry | 249 | EVE | 5.6 | 4.691 | 27.68 | 0.94 | XI |
| 12 | GKP | Kinsky | 496 | TOT | 4.4 | 3.468 | 19.9 | 0.95 | Bench GK |
| 13 | MID | Gomez | 127 | BHA | 5.0 | 3.956 | 23.43 | 0.95 | Bench 1 |
| 14 | DEF | Justin | 332 | LEE | 4.5 | 3.538 | 23.44 | 0.94 | Bench 2 |
| 15 | MID | Barnes | 453 | NEW | 6.0 | 3.51 | 23.46 | 0.95 | Bench 3 |
| | | **Total** | | | **99.1** + bank 0.5 | | | | |

2 GKP / 5 DEF / 5 MID / 3 FWD. Clubs: BHA 2, BOU 2, LEE 2, TOT 2; ARS, MUN,
MCI, LIV, SUN, NEW, EVE 1 each. No club at 3.

## Starting XI — 4-3-3

Trafford; Gabriel, Van Hecke, De Cuyper, Hill; E.Le Fée, Tavernier, Mbeumo;
Haaland, Isak, Barry. XI EP 58.405 with the captain doubled (`objective`).
C20 boundary: Trafford 3.578 v Kinsky 3.468, both DefCon share 0.000, so the
higher EP starts; no outfield pair inside 0.25.

## Captain and vice

- **Captain Haaland** (MCI), GW11 EP 6.047 — 0.741 clear of Isak, outside
  the 0.5 tie band.
- **Vice Gabriel** (ARS), 5.229 — inside 0.5 of Isak 5.306 (0.077 gap), both
  p_start ≥ 0.85; S8 breaks the tie toward Gabriel (ret5 4/5 v 3/5, p4 0.696
  v 0.481, uncertainty LOW v MED). Cost 0.077 single-GW EP, paid only if
  Haaland does not play.

## Bench order

12 Kinsky (GK) · 13 Gomez 3.956 · 14 Justin 3.538 · 15 Barnes 3.510.
GW11 EP order; Justin v Barnes (0.028, inside C8's band) settled on the GW10
DefCon shares 0.137 v 0.015, which agree with the EP order (review F4). All
four at p_start ≥ 0.94.

## Transfers

| Out | In | Cost | Marginal (blend / prior-only) |
|---|---|---:|---|
| Calafiori (ARS, sell 5.9) | De Cuyper (BHA, buy 5.5) | 0 | +2.374 / +1.881 |

Free; hit 0. One of three free transfers used; 3 at the GW12 deadline. Bank
0.1 + 5.9 − 5.5 = 0.5. POST the transfer today (2026-11-20): De Cuyper has
243,074 transfers in this event and has already risen once (review F3).

## Chips

`chip: null`. Available (bootstrap `chips`, set 1): bboost GW1–19, freehit
GW2–19. Wildcard played GW8, 3xc GW9. Free hit graded on GW11 alone: +0.313
/ +0.276 over the greedy plan against a 6.0 chip gate — fails.

Provisional chip plan (forecast, mirrored in `chip_plan:`): freehit GW16
(placeholder, no blank or double in GW11–16); bboost GW19 (last set-1
gameweek).

## Accepted risks

| Review id | Severity | Risk | Why accepted |
|---|---|---|---|
| F1 | MED | GW12–14 congestion (three rounds in nine days) is not priced into any p_start; the six players at clubs with European or cup fixtures (Gabriel, Haaland, Isak, Barnes, Van Hecke, Kinsky) carry flat 0.93–0.95, so their six-GW totals are optimistic. | Does not change this week's decision: the transfer sells a rotation-exposed ARS full-back for a BHA starter with no European fixture, so repricing would widen the gain. GW12 and GW13 cycles should expect lower p_start on these six; 3 free transfers are available to respond. |
| F2 | MED | Template exposure: after the sale only one Arsenal defender (Gabriel) is held, against a template of two or three of Raya, Calafiori, Gabriel, Konsa (ARS clean-sheet rank 1 for the window). An ARS clean-sheet run costs rank. Rogers 54.2%, Groß 48.6%, Raya 47.6% also not held. | The files price it (De Cuyper beats Calafiori in four of six gameweeks) and the swap is like for like on ownership (48.6% v 48.7%). No move into the other template names passes the gate. |
| F3 | MED | Barnes (fell 6.1 → 6.0, net out 81,995 v 4,703 in) and Mbeumo (net out 130,298 v 13,145 in) held through likely price falls — up to 0.2 of team value. | No sale of either passes the gate (Mbeumo → Gibbs-White −2.610 / −2.347; Barnes → Groß +0.621 / −1.723). POST the De Cuyper transfer today; an overnight rise to 5.6 leaves bank 0.4. |

LOW (no change): F4 bench tie-break on last week's DefCon shares; F5 banded
clean-sheet rows (De Cuyper at HUL 0.36, Van Hecke v IPS 0.35) are not
either player's largest EP term.

## Rationale summary

- One free move: Calafiori → De Cuyper is the greedy reference and the only
  plan that passes (`verdict: PASS`). It beats Calafiori → Silva (+2.042 /
  +0.646) on blend, prior-only and the ret5 tie-break, and Silva would put a
  third BOU player in the squad.
- Two free transfers banked: after the plan the best single (Barnes → Groß
  +0.621 / −1.723) fails the gate; no second move reaches 2.0, no hit reaches
  6.0.
- Premiums kept: Haaland → N.Jackson loses 11.761; Isak → Calvert-Lewin
  loses 3.767 / 2.929 even when it funds Mbeumo → B.Fernandes.
- S7 (sell-side policy on fallers) held Mbeumo and Barnes because their
  sales lose EP or fail the gate; S8 decided the vice.
- Analyst escalations (CHE goalkeeper, MCI back four, Virgil/N.Williams 75%,
  share-check-inflated B.Fernandes/Awoniyi/Osula) touch no owned or bought
  player in the chosen plan.

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
| S7 | 7 | standing | honoured as a sell-side policy: of the named fallers only Mbeumo is still owned, a net faller again this event (in 13,145 v out 130,298, price 7.9 unchanged) but Mbeumo → Gibbs-White is −2.610 / −2.347 FAIL, not a small gap, so he is held; Barnes fell 6.1 → 6.0 this event (in 4,703 v out 81,995) and no sale of him passes the gate: Barnes → Groß +0.621 / −1.723 beside the plan (prior sign flip), Barnes → McAtee −0.604 / +0.569, Barnes → Gibbs-White +1.985 / +0.039 only inside a plan whose Isak leg loses 3.618; Haaland is net out (in 29,389 v out 55,842, price flat) and Haaland → N.Jackson loses 11.761 / 11.932; the one transfer made sells Calafiori, a net riser, on EP alone, with no rival transfer inside a small gap for the row to prefer; the policy never overrides the gate; EP6 delta of the row 0.00 |
| S8 | 7 | standing | honoured: the one buy is De Cuyper (BHA, 10/10 starts, ret5 4/5, BHA ATT rank 2), a nailed starter with the steadier record of the two close options — objective's line `tie-break move: Calafiori → De Cuyper +2.374 v Calafiori → Silva +2.042 — winner Calafiori → De Cuyper (ret5 4/5 v 3/5)` and its group line ends (decided by blend), so the steer and the blend agree and the row costs 0.00 EP6 there; it also breaks the vice tie, Isak 5.306 v Gabriel 5.229 inside 0.5 single-GW EP with both at p_start 0.93 or above, toward Gabriel (ret5 4/5 v 3/5, p4 0.696 v 0.481, uncertainty LOW v MED), at −0.077 single-GW EP in the vice slot only; it cannot reach the captaincy, Haaland 6.047 v Isak 5.306 being 0.741 apart; EP6 delta of the row 0.00 |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW12 deadline: 3 live at GW11 (auth-check, relayed) − 1 used + 1 accrued (objective: FT next 3).
# team_value 99.6 = selling-price sum 99.1 + bank 0.5 after Calafiori (sell 5.9) → De Cuyper (buy 5.5); the live budget relayed on 2026-11-20 was 99.6.
gw: 11
team_id: 8455344
team_value: 99.6
bank: 0.5
free_transfers_banked: 3
chip: null
chips_used:
  - {chip: wildcard, gw: 8}
  - {chip: 3xc, gw: 9}
transfers_made:
  - {out: Calafiori, in: De Cuyper, cost: 0}
chip_plan:
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 385, name: Trafford, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: false, vice: true}
  - {id: 112, name: Van Hecke, position: 3, captain: false, vice: false}
  - {id: 115, name: De Cuyper, position: 4, captain: false, vice: false}
  - {id: 60, name: Hill, position: 5, captain: false, vice: false}
  - {id: 542, name: E.Le Fée, position: 6, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 7, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: true, vice: false}
  - {id: 379, name: Isak, position: 10, captain: false, vice: false}
  - {id: 249, name: Barry, position: 11, captain: false, vice: false}
  - {id: 496, name: Kinsky, position: 12, captain: false, vice: false}
  - {id: 127, name: Gomez, position: 13, captain: false, vice: false}
  - {id: 332, name: Justin, position: 14, captain: false, vice: false}
  - {id: 453, name: Barnes, position: 15, captain: false, vice: false}
```
