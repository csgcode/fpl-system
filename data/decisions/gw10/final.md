# GW10 Final (2026/27)

Deadline **2026-11-06T18:30:00Z**. Built from
data/decisions/gw10/squad-proposal.md (first optimizer run of the cycle) and
data/decisions/gw10/review.md (verdict APPROVE, no HIGH finding; MED F5, F8,
F10). The previous final is data/decisions/gw9/final.md.

**No transfers, hit 0. Both free transfers banked (3 at the GW11 deadline).
No chip. 4-3-3, Gabriel (C), Haaland (V). Predicted GW10 58.945 for the XI
with the captain doubled.**

## Freshness gate

`fpl flags --gw 10` refreshed at 2026-11-05 20:11:53 UTC on the proposal's
`Gate ids:` line (the 15 squad ids; no transfers-in), against baseline
`data/raw/gw10/.archive/bootstrap-20261105T194504_242767Z.json` (age 0.4h).
Exit 0. Delta: `data/raw/gw10/flags-delta-20261105T201153_320711Z.json`.

| Result | Detail |
|---|---|
| **PASS** | 0 of 15 gate ids changed. All 15 status `a`; Calafiori, Van Hecke, Haaland and Isak carry cleared 100% flags. Pool (informational): 3 changed, none held (Diarra d → i; Timber d → a; Strand Larsen d → a). |

## Entry state

`fpl my-team --gw 10` (session live): bank 0.1, budget 99.5. Equals the
proposal's `team_value` 99.5 and `bank` 0.1; copied unchanged. Chips:
bboost and freehit available; wildcard played GW8, 3xc played GW9.

## Squad — predicted points (calibration record)

`GW10 EP` = `ep_gw[0]`, `EP6` = `ep_total6`, `p_start GW10` =
`p_start_gw[0]` from `data/analysis/gw10/players-{pos}.json` (model
64ad9c9c), copied as written there. Price = the proposal's reconstructed
selling price (sum 99.4, equal to the live `my-team` selling-price sum;
individual rows may differ by 0.1).

| Slot | Pos | Player | Id | Club | Price | GW10 EP | EP6 | p_start GW10 | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|
| 1 | GKP | Trafford | 385 | LEE | 5.0 | 3.888 | 22.17 | 0.95 | XI |
| 2 | DEF | Gabriel | 4 | ARS | 7.9 | 5.785 | 29.71 | 0.95 | XI · Captain |
| 3 | DEF | Calafiori | 8 | ARS | 5.9 | 4.876 | 24.37 | 0.9 | XI |
| 4 | DEF | Hill | 60 | BOU | 5.5 | 4.245 | 25.46 | 0.95 | XI |
| 5 | DEF | Van Hecke | 112 | TOT | 4.9 | 4.074 | 26.69 | 0.95 | XI |
| 6 | MID | Mbeumo | 427 | MUN | 7.9 | 5.213 | 30.5 | 0.96 | XI |
| 7 | MID | Tavernier | 68 | BOU | 6.3 | 4.932 | 27.85 | 0.95 | XI |
| 8 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.634 | 26.82 | 0.95 | XI |
| 9 | FWD | Haaland | 411 | MCI | 15.6 | 5.265 | 34.08 | 0.94 | XI · Vice |
| 10 | FWD | Isak | 379 | LIV | 9.1 | 5.167 | 29.73 | 0.93 | XI |
| 11 | FWD | Barry | 249 | EVE | 5.6 | 5.081 | 27.73 | 0.94 | XI |
| 12 | GKP | Kinsky | 496 | TOT | 4.4 | 3.22 | 20.19 | 0.95 | Bench GK |
| 13 | DEF | Justin | 332 | LEE | 4.5 | 4.155 | 22.65 | 0.94 | Bench 1 |
| 14 | MID | Gomez | 127 | BHA | 5.0 | 3.949 | 23.24 | 0.95 | Bench 2 |
| 15 | MID | Barnes | 453 | NEW | 6.1 | 3.741 | 22.9 | 0.95 | Bench 3 |
| | | **Total** | | | **99.4** + bank 0.1 | | | | |

2 GKP / 5 DEF / 5 MID / 3 FWD. Clubs: ARS 2, BOU 2, LEE 2, TOT 2; MUN, MCI,
LIV, SUN, NEW, BHA, EVE 1 each. No club at 3.

## Starting XI — 4-3-3

Trafford; Gabriel, Calafiori, Hill, Van Hecke; Mbeumo, Tavernier, E.Le Fée;
Haaland, Isak, Barry. XI EP 58.945 with the captain doubled: `objective`'s
59.026 XI less the C20 boundary swap (Van Hecke 4.074 starts over Justin
4.155, a 0.081 gap inside 0.25, on the higher DefCon floor share 0.151 v
0.137).

## Captain and vice

- **Captain Gabriel** (ARS v HUL (H)), GW10 EP 5.785 — 0.520 clear of
  Haaland, outside the 0.5 tie band; also the squad's top GW10 EP
  prior-only (5.546, review F8).
- **Vice Haaland** (NFO (A)), 5.265 — inside 0.5 of Mbeumo 5.213; S8 breaks
  the tie toward Haaland, also the higher EP, so the steer costs 0.00.

## Bench order

12 Kinsky (GK) · 13 Justin 4.155 · 14 Gomez 3.949 · 15 Barnes 3.741.
GW10 EP order; the C8 DefCon tie-break (0.137 > 0.123 > 0.015) agrees. All
four at p_start ≥ 0.94.

## Transfers

None; hit 0. Free transfers 2 now, 3 at the GW11 deadline. Best single
Calafiori → Silva +0.771 blend / −0.301 prior-only; best paired marginal
Barnes → Gibbs-White +1.903 / −0.551 — both fail the free gate. The
set-lineup POST is still required (formation, armbands and two slots change
from GW9); the transfer step prints "already applied".

## Chips

`chip: null`. Available (bootstrap `chips`, set 1): bboost GW1–19, freehit
GW2–19. Wildcard played GW8, 3xc GW9. Free hit graded on GW10 alone: +0.633
/ +0.191 against a 6.0 chip gate — fails. Bench boost has no `objective`
gate (logged in docs/backlog.md by the optimizer).

Provisional chip plan (forecast, mirrored in `chip_plan:`): freehit GW16
(placeholder, no blank or double known through GW15); bboost GW19 (last
set-1 gameweek).

## Accepted risks

| Review id | Severity | Risk | Why accepted |
|---|---|---|---|
| F8 | MED | Captaincy rests on a banded clean-sheet term: ARS v HUL `p_cs` 0.50 (C12, ±15pp). At the band's low end Gabriel is about 5.21 blend, below Haaland 5.265. Alternative: captain Haaland, −0.520 EP central. | The band is symmetric, so 5.785 is the expected value; Gabriel leads on blend and prior-only; switching breaches the captaincy rule (lower EP, outside the 0.5 band). |
| F10 | MED | Bench boost timing: the GW19 earmark is the window's last gameweek, so any mishap loses the chip; December congestion raises bench rotation risk. Alternative: play bboost at GW10 (+15.065 expected) or the first of GW11–13 with a matching bench EP. | No rule grades bboost timing; the earmark is provisional and keeps the double-gameweek option. Revisit each cycle until GW19. |
| F5 | MED | Template exposure (carried from GW9 F5): Rogers 52.8%, Groß 46.9%, Raya 46.8%, De Cuyper 45.4%, Cherki 34.9% not held. A haul from any lands as rank loss. Alternative: Calafiori → De Cuyper (+0.238 / +0.661). | No move into any of them comes near the 2.0 free gate. |

## Rationale summary

- Bank: only seven of 1551 singles are positive on blend; none passes the
  free gate, and no pair or hit plan passes either. Three free transfers at
  GW11 (after the international break) land before ARS turn harder from
  GW13.
- Hold Mbeumo and Barnes despite net-out price pressure (S7): Mbeumo →
  Gibbs-White −4.331 / −4.477; Barnes → McAtee +0.072 / +0.414.
- Premiums kept: Haaland → Thiago loses 11.580; Isak → Kostoulas loses 4.971.
- No free hit: +0.633 against a 6.0 gate; the squad already starts the
  GW10 top two scorers at every outfield position.
- Calibration context (data/retro/gw9.md): XI scored 58 against 55.46
  predicted; every squad miss was VARIANCE or a bench MINUTES row.

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
| S7 | 7 | standing | honoured as a sell-side policy: of the named fallers only Mbeumo is still owned, a net faller again this event (in 19,147 v out 123,616, price 7.9 unchanged) but Mbeumo → Gibbs-White is −4.331 / −4.477 FAIL, not a small gap, so he is held; the squad's other net-out row is Barnes (out 37,613 v in 12,129) and Barnes → McAtee +0.072 / +0.414 fails the free gate on blend; Calafiori is flat at 5.9 this event and Calafiori → Silva +0.771 / −0.301 fails on blend and prior sign; the policy never overrides the gate — the cost accepted is 0.1 of team value per fall before GW11, when 3 FTs are available; EP6 delta of the row 0.00 |
| S8 | 7 | standing | honoured: no buy this cycle because no move passes the gate (best single Calafiori → Silva +0.771 / −0.301; best paired marginal Barnes → Gibbs-White +1.903 / −0.551), so no buy is judged under the row; it breaks the vice tie, Haaland 5.265 v Mbeumo 5.213 inside 0.5 single-GW EP with the spec's p_start tie-break holding both, toward Haaland (ret5 4/5 v 2/5; MCI ATT rank 1 v MUN rank 7), the higher EP as well, so the steer costs 0.00; it cannot reach the captaincy, Gabriel 5.785 v Haaland 5.265 being 0.520 apart, outside the band; EP6 delta of the row 0.00 |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW11 deadline: 2 live at GW10 (my-team, relayed) + 1 accrued, none used (objective: FT next 3).
# team_value 99.5 and bank 0.1 are the live my-team budget and bank relayed by the orchestrator on 2026-11-05; no transfer this GW.
gw: 10
team_id: 8455344
team_value: 99.5
bank: 0.1
free_transfers_banked: 3
chip: null
chips_used:
  - {chip: wildcard, gw: 8}
  - {chip: 3xc, gw: 9}
transfers_made: []
chip_plan:
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 385, name: Trafford, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: true, vice: false}
  - {id: 8, name: Calafiori, position: 3, captain: false, vice: false}
  - {id: 60, name: Hill, position: 4, captain: false, vice: false}
  - {id: 112, name: Van Hecke, position: 5, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 6, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 7, captain: false, vice: false}
  - {id: 542, name: E.Le Fée, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: false, vice: true}
  - {id: 379, name: Isak, position: 10, captain: false, vice: false}
  - {id: 249, name: Barry, position: 11, captain: false, vice: false}
  - {id: 496, name: Kinsky, position: 12, captain: false, vice: false}
  - {id: 332, name: Justin, position: 13, captain: false, vice: false}
  - {id: 127, name: Gomez, position: 14, captain: false, vice: false}
  - {id: 453, name: Barnes, position: 15, captain: false, vice: false}
```
