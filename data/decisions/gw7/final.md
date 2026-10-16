# GW7 Final (2026/27)

Deadline **2026-10-17T10:00:00Z**. Review verdict **APPROVE** (no HIGH; MED
F1 and F2 carried below as accepted risks). No revision loop. No-chip plan,
written on a binding user directive (no wildcard this GW).

**One free transfer: Thiaw → Van Hecke. Hit 0. Bank £0.4m. No chip. 3-4-3,
Haaland (C), Mbeumo (V). Predicted GW7 54.855.**

## Freshness gate

`fpl flags --gw 7` refreshed at 2026-10-16 22:55:07 UTC on the proposal's 15
gate ids, against baseline
`data/raw/gw7/.archive/bootstrap-20261016T220203_834178Z.json` (age 0.9h).
Exit 0. Delta: `data/raw/gw7/flags-delta-20261016T225507_407228Z.json`.

| Result | Detail |
|---|---|
| **PASS** | 0 of 15 gate ids changed. XI all `a`; Van Hecke chance 100. Schade d 75% (shoulder) and Shaw d 75% (unspecified), both benched, unchanged. Pool: 0 changed. |

## Verified entry state

`fpl my-team --gw 7` (authenticated): 1 free transfer, 0 made, bank 0.3,
budget 99.1 (selling-price sum + bank), equal to the proposal's
`team_value` 99.1. All four set-1 chips available.

## Squad — predicted points (calibration record)

`GW7 EP` = `ep_gw[0]`, `EP6` = `ep_total6` from
`data/analysis/gw7/players-{pos}.json`. Price = selling price for kept
players, purchase price for Van Hecke.

| Slot | Pos | Player | Id | Club | Price | GW7 EP | EP6 | p_start | Unc | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|---|
| 1 | GKP | Raya | 1 | ARS | 6.0 | 3.343 | 21.18 | 0.94 | LOW | XI |
| 2 | DEF | Van Hecke | 112 | TOT | 4.9 | 4.596 | 23.47 | 0.92 | LOW | XI · IN |
| 3 | DEF | Gabriel | 4 | ARS | 7.9 | 4.062 | 26.27 | 0.92 | LOW | XI |
| 4 | DEF | Tarkowski | 229 | EVE | 6.1 | 3.793 | 22.9 | 0.92 | LOW | XI |
| 5 | MID | Mbeumo | 427 | MUN | 7.9 | 4.572 | 28.79 | 0.93 | LOW | XI · Vice |
| 6 | MID | Groß | 124 | BHA | 5.9 | 4.435 | 24.66 | 0.93 | LOW | XI |
| 7 | MID | Tavernier | 68 | BOU | 6.0 | 4.274 | 24.32 | 0.90 | LOW | XI |
| 8 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.006 | 26.11 | 0.92 | LOW | XI |
| 9 | FWD | Haaland | 411 | MCI | 15.5 | 6.579 | 35.06 | 0.93 | LOW | XI · Captain |
| 10 | FWD | Barry | 249 | EVE | 5.6 | 4.582 | 25.38 | 0.90 | LOW | XI |
| 11 | FWD | Thiago | 106 | BRE | 7.8 | 4.034 | 25.14 | 0.92 | LOW | XI |
| 12 | GKP | Dubravka | 497 | TOT | 4.0 | 0.123 | 0.68 | 0.03 | HIGH | Bench GK |
| 13 | DEF | Richards | 202 | CRY | 4.9 | 3.089 | 22.19 | 0.92 | LOW | Bench 1 |
| 14 | MID | Schade | 94 | BRE | 6.2 | 2.761 | 22.12 | 0.65 | LOW | Bench 2 |
| 15 | DEF | Shaw | 423 | MUN | 4.3 | 1.907 | 11.96 | 0.70 | MED | Bench 3 |
| | | **Total** | | | **98.7** | | | | | |

2 GKP / 5 DEF / 5 MID / 3 FWD. Clubs: ARS 2, EVE 2, MUN 2, BRE 2, TOT 2,
others 1.

## Starting XI — 3-4-3

| Slot | Player | Pos | GW7 fixture | GW7 EP |
|---:|---|---|---|---:|
| 1 | Raya | GKP | NFO (A) | 3.343 |
| 2 | Van Hecke | DEF | COV (H) ± | 4.596 |
| 3 | Gabriel | DEF | NFO (A) | 4.062 |
| 4 | Tarkowski | DEF | CHE (H) | 3.793 |
| 5 | Mbeumo (V) | MID | LEE (A) | 4.572 |
| 6 | Groß | MID | CRY (H) | 4.435 |
| 7 | Tavernier | MID | SUN (H) | 4.274 |
| 8 | E.Le Fée | MID | BOU (A) | 4.006 |
| 9 | Haaland (C) | FWD | IPS (H) ± | 6.579 |
| 10 | Barry | FWD | CHE (H) | 4.582 |
| 11 | Thiago | FWD | LIV (H) | 4.034 |
| | XI total | | | 48.276 |
| | + captain | | | 6.579 |
| | **Predicted GW7** | | | **54.855** |

## Captain and vice

- **Captain Haaland** 6.579 — 1.983 clear of the next XI row.
- **Vice Mbeumo** 4.572 — Van Hecke 4.596 / Barry 4.582 / Mbeumo 4.572 sit
  within 0.024, all p_start ≥ 0.85; S8 breaks the tie to Mbeumo (steadiest
  record, unbanded row, different club from the captain).

## Bench order

| Slot | Player | Pos | GW7 EP | p_start |
|---:|---|---|---:|---:|
| 12 | Dubravka | GKP | 0.123 | 0.03 |
| 13 | Richards | DEF | 3.089 | 0.92 |
| 14 | Schade | MID | 2.761 | 0.65 |
| 15 | Shaw | DEF | 1.907 | 0.70 |

## Transfers

| Out | In | Sell | Buy | Cost |
|---|---|---:|---:|---:|
| Thiaw (NEW, DEF, id 445) | Van Hecke (TOT, DEF, id 112) | 5.0 | 4.9 | 0 |

One free transfer used, hit 0. Bank 0.3 → 0.4. 1 free transfer at GW8.
Execution order: transfers first, then the lineup. POST before the
overnight price run (Van Hecke net riser, Thiaw net faller; single-tick
moves leave the bank ≥ 0.2).

## Chips

`chip: null` — user directive, no chip this GW. Set-1 windows from
bootstrap: wildcard / freehit GW2–19, bboost / 3xc GW1–19; none used.
Provisional plan: wildcard GW8, 3xc GW9 (Haaland v BHA (H)), freehit GW16
(placeholder), bboost GW19 (placeholder; needs GK2 repaired first).

## Accepted risks

| # | Risk | Detail |
|---|---|---|
| F1 (R4, widened) | Free-gate pass is band-sensitive | The move clears the 2.0 free gate by 0.223. 2.02 of Van Hecke's 3.27 EP6 lead over Thiaw sits on two banded promoted-club rows: GW7 COV (H) P(CS) 0.41 ± and GW11 IPS (H) P(CS) 0.34 ±; Thiaw's rows are all unbanded. At the band's low edge (−15pp) the marginal falls to roughly +1.1 and would fail the gate; at the centre (+2.223, graded per C12) and high edge (~+3.3) it passes. Van Hecke's largest term is appearance (11.04), not a banded P(CS) |
| F2 | S7 reason silent on Schade | Schade is the squad's largest faller (net −154.6k this event, d 75%). Schade → Sávio +2.005 / +3.634 is within 0.218 of plan A but fails the transfer rule's greedy reference, which a suggestion cannot override; S8 prefers Van Hecke over Sávio on the same choice. Recorded here because the ledger is carried verbatim and its S7 reason is not altered |
| R1 / F5 | GK2 dead | Dubravka p 0.03; a Raya absence leaves the GK slot empty. First repair at GW8 |
| R2 / F5 | Bench rows flagged | Schade d 75%, Shaw d 75%; auto-sub cover is Richards alone |
| R3 / F6 | Template exposure | Unheld > 30%: João Pedro, Calafiori, Rogers, De Cuyper, Cherki, B.Fernandes |
| R5 | Promoted-club rows in the XI | Haaland v IPS, Van Hecke v COV, both banded |
| R6 | FT spent before a possible wildcard | 1 FT at GW8 instead of 2; costless if the wildcard is played |

## Rationale summary

Wildcard withheld by user directive. Of 1555 legal single moves, two pass
the free gate; Thiaw → Van Hecke (+2.223 blend / +1.214 prior-only over
GW7–12) is the greedy reference and the only plan that PASSes `objective`.
Banking fails the rule (a free move passes); Schade → Sávio fails the
reference by 0.218; a second move fails the 6.0 hit gate. Van Hecke leads
Thiaw on all six rows and holds with GW7 excluded (18.87 v 16.41). XI is
the objective's best 3-4-3 with no boundary pair within 0.25.

## Suggestions

Read data/suggestions.md through S8

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 6 | followed | both halves now complete: Ndiaye → Groß and Anderson → Schade inside the +14.449 blend / +5.210 prior-only triple; Ndiaye's marginal +2.503 / +0.665 and Anderson's +2.488 / +0.757 each clear the 2.0 gate on their own, so the steer broke no tie and the optimizer reached it unaided; EP6 delta of the row itself 0.00. The GW5 ledger's "Ndiaye half completed" was false in fact (never POSTed) and is superseded here |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |
| S3 | 6 | followed | Ndiaye → Groß made; marginal +2.503 blend / +0.665 prior against the plan without this sale (Scott + Anderson → E.Le Fée + Schade, +11.946 / +4.545), so the below-threshold clause was not needed |
| S4 | 6 | followed | Anderson → Schade made; marginal +2.488 blend / +0.757 prior against the plan without this sale (Scott + Ndiaye → E.Le Fée + Groß, +11.961 / +4.453); clears the gate on both readings, below-threshold clause not needed |
| S5 | 6 | followed | Scott → E.Le Fée made; EP6 0.00 for GW6–11 (status i, 0%); marginal +2.503 / +0.675 against the plan without this sale (Ndiaye + Anderson → E.Le Fée + Schade, +11.946 / +4.535) |
| S6 | 6 | standing | honoured: the wildcard is not played at GW7 by user directive (chip null), so its timing moves to GW8, inside this row's window; the GW7 EP cleared the chip gate (v1: +16.239 / +3.979, +14.016 / +2.765 over plan A) and the GW8 cycle regrades it; the free move Thiaw → Van Hecke +2.223 / +1.214 lifts GW7 to 54.86 from 54.05; 60 per GW stays unreachable (best legal GW7 build 57.49). Completes `followed` at a GW8 wildcard, or `expired` after GW8 |
| S7 | 7 | standing | honoured: the one legal free move sells a faller — Thiaw (17.4k out v 1.6k in this event, sold at 5.0 before a drop) — though he is not a named row; of the named fallers Richards (0.6% owned, net −406), Thiago (net −34.5k), Shaw (net −62.7k) and Mbeumo (net −18.7k) have no move passing the gate (Shaw → Justin +1.219 / +0.968, Richards → Silva +2.366 / −1.943 sign flip, Thiago and Mbeumo absent from the top 20), none within 0.5 of plan A, so no in-band tie to settle; Gabriel (−0.1 this event, net −94k) held, no DEF move from him in the top 20; policy stays live for GW8 |
| S8 | 7 | standing | honoured: Van Hecke (27 pts, 3 returns ≥ 5, 6/6 × 90, TOT CS rank 4) over Sávio (10 pts, 0 returns, 330', TOT ATT rank 16) inside the 0.5 band on the package delta (+2.223 v +2.005 blend), the same way the objective's greedy reference falls; vice tie inside 0.5 single-GW EP broken to Mbeumo 4.572 (33 pts, three 8+ returns, p 0.93) over Van Hecke 4.596 (banded COV row) and Barry 4.582; the GW6 buys E.Le Fée, Groß and Schade are held because no move from them passes the gate (Schade → Sávio FAIL on reference, Schade → Stach +0.740 / −0.427) |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW8 deadline: 1 at GW7, 1 used, 1 accrues.
# team_value on the selling-price basis: kept players at GW6 sell prices + Van Hecke at purchase price = 98.7, bank 0.4.
gw: 7
team_id: 8455344
team_value: 99.1
bank: 0.4
free_transfers_banked: 1
chip: null
chips_used: []
transfers_made:
  - {out: Thiaw, in: Van Hecke, cost: 0}
chip_plan:
  - {chip: wildcard, gw: 8, status: provisional}
  - {chip: 3xc, gw: 9, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 1, name: Raya, position: 1, captain: false, vice: false}
  - {id: 112, name: Van Hecke, position: 2, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 3, captain: false, vice: false}
  - {id: 229, name: Tarkowski, position: 4, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 5, captain: false, vice: true}
  - {id: 124, name: Groß, position: 6, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 7, captain: false, vice: false}
  - {id: 542, name: E.Le Fée, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: true, vice: false}
  - {id: 249, name: Barry, position: 10, captain: false, vice: false}
  - {id: 106, name: Thiago, position: 11, captain: false, vice: false}
  - {id: 497, name: Dubravka, position: 12, captain: false, vice: false}
  - {id: 202, name: Richards, position: 13, captain: false, vice: false}
  - {id: 94, name: Schade, position: 14, captain: false, vice: false}
  - {id: 423, name: Shaw, position: 15, captain: false, vice: false}
```
