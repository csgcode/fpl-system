# GW8 Final (2026/27)

Deadline **2026-10-23T17:30:00Z**. Review verdict **REVISE** on the v1
wildcard proposal (HIGH F1); the one revision loop has run. The revised
proposal (data/decisions/gw8/squad-proposal.md; v1 archived as
squad-proposal.v1.md) follows the user's directive, quoted verbatim: "A,
hold the wildcard, We can rethink after having some more data to rely on."
Earlier in the cycle the user also chose to keep Raya and not buy Saka.

**No transfers. Hit 0. Free transfer banked: 2 at the GW9 deadline. Bank
£0.4m. No chip. 3-5-2, Haaland (C), Gabriel (V). Predicted GW8 53.600.**

## Freshness gate

`fpl flags --gw 8` refreshed at 2026-10-23 13:13:22 UTC on the proposal's 15
gate ids, against baseline
`data/raw/gw8/.archive/bootstrap-20261023T095820_571308Z.json` (age 3.3h).
Exit 0. Delta: `data/raw/gw8/flags-delta-20261023T131322_242608Z.json`.

| Result | Detail |
|---|---|
| **PASS** | 0 of 15 gate ids changed. XI all `a`; Haaland, Van Hecke and Schade chance 100. Shaw `i` 0% (unspecified injury, unknown return date), benched at slot 15, unchanged. Pool (informational): 12 changed, none in the squad. |

## Entry state

`fpl my-team --gw 8` could not be read: the session is expired and the
refresh failed (`auth-check` FAIL, invalid_grant). data/auth.json is dated
2026-10-16; a browser capture saved today as `curl-request` (repo root,
git-ignored) has not been imported with `auth-import`. The proposal's
`team_value` 99.1 therefore stands on the GW7-verified selling-price basis
(`my-team` budget 99.1 at GW7) with no transfer since, and is copied
unchanged. It is not re-verified this GW.

## Squad — predicted points (calibration record)

`GW8 EP` = `ep_gw[0]`, `EP6` = `ep_total6` from
`data/analysis/gw8/players-{pos}.json`, copied as written. Price = GW7-verified
selling price (now_cost in brackets where different).

| Slot | Pos | Player | Id | Club | Price | GW8 EP | EP6 | p_start GW8 | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|
| 1 | GKP | Raya | 1 | ARS | 6.0 (6.1) | 3.827 | 21.66 | 0.95 | XI |
| 2 | DEF | Gabriel | 4 | ARS | 7.9 | 5.08 | 28.58 | 0.95 | XI · Vice |
| 3 | DEF | Richards | 202 | CRY | 4.9 | 4.044 | 22.7 | 0.95 | XI |
| 4 | DEF | Van Hecke | 112 | TOT | 4.9 | 3.565 | 24.3 | 0.95 | XI |
| 5 | MID | Mbeumo | 427 | MUN | 7.9 | 4.932 | 30.43 | 0.96 | XI |
| 6 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.406 | 26.2 | 0.94 | XI |
| 7 | MID | Tavernier | 68 | BOU | 6.0 (6.2) | 4.351 | 26.95 | 0.93 | XI |
| 8 | MID | Schade | 94 | BRE | 6.2 | 3.676 | 20.46 | 0.80 | XI |
| 9 | MID | Groß | 124 | BHA | 5.9 (6.2) | 3.622 | 23.74 | 0.94 | XI |
| 10 | FWD | Haaland | 411 | MCI | 15.5 (15.7) | 5.798 | 34.96 | 0.94 | XI · Captain |
| 11 | FWD | Thiago | 106 | BRE | 7.8 | 4.501 | 25.23 | 0.95 | XI |
| 12 | GKP | Dubravka | 497 | TOT | 4.0 | 0.107 | 0.68 | 0.03 | Bench GK (dead) |
| 13 | FWD | Barry | 249 | EVE | 5.6 (5.7) | 3.66 | 25.51 | 0.94 | Bench 1 |
| 14 | DEF | Tarkowski | 229 | EVE | 6.1 (6.2) | 3.247 | 23.02 | 0.95 | Bench 2 |
| 15 | DEF | Shaw | 423 | MUN | 4.3 | 0.0 | 7.32 | 0.00 | Bench 3 (status i, dead) |
| | | **Total** | | | **98.7** + bank 0.4 = 99.1 | | | | |

2 GKP / 5 DEF / 5 MID / 3 FWD. Clubs: ARS 2, EVE 2, BRE 2, MUN 2, TOT 2,
rest 1.

## Starting XI — 3-5-2

Raya; Gabriel (V), Richards, Van Hecke; Mbeumo, E.Le Fée, Tavernier, Schade,
Groß; Haaland (C), Thiago. XI total 47.802 + captain 5.798 = **53.600**.

The objective's best XI is 3-4-3 with Barry for Groß (53.638). The C20/C8
tie-break at the XI/bench boundary starts Groß (DefCon share 0.043) over
Barry (0.008), 0.038 EP apart, inside the 0.25 band.

## Captain and vice

- Captain **Haaland** 5.798, 0.718 clear of Gabriel — outside the 0.5 band.
- Vice **Gabriel** 5.080 over Mbeumo 4.932: inside the band, both
  p_start ≥ 0.85, higher EP holds; the S8 reading is mixed and does not
  overturn it.

## Bench order

| Slot | Player | Pos | GW8 EP | p_start |
|---:|---|---|---:|---:|
| 12 | Dubravka | GKP | 0.107 | 0.03 (dead) |
| 13 | Barry | FWD | 3.66 | 0.94 |
| 14 | Tarkowski | DEF | 3.247 | 0.95 |
| 15 | Shaw | DEF | 0.0 | 0.00 (status i, dead) |

## Transfers

None. Hit 0. Of 1582 legal single moves none passes the transfer rule (best
blend Richards → Silva +2.301 flips sign prior-only at −1.562; best
gate-shaped Schade → Stach +1.764 / +0.894 is under 2.0). Free transfers: 1
at the GW8 deadline, banked → 2 at the GW9 deadline.

## Chips

`chip: null` — the user holds the wildcard. Provisional `chip_plan` (windows
from bootstrap `chips`: wildcard and freehit GW2–19, bboost and 3xc GW1–19):
3xc GW9 (Haaland v BHA (H)), wildcard GW10 (last deadline before the GW11
fixture turn), freehit GW16 and bboost GW19 as placeholders. Forecasts, not
commitments.

## Accepted risks

The final plan makes no transfer, so the v1 package findings carry no risk
into it: F1 (Silva's prior sign flip), F2 (Saka's flag), F4 (Wissa v
Calvert-Lewin under S8) and F5 (buying two fallers under S7) name players
the plan does not buy.

- **F3 (MED) — template exposure.** Held players owned by more than 30%:
  Haaland, Raya (44.9%), Groß (45.8%). Still off João Pedro (73.3%),
  Calafiori (54.3%), Rogers (48.8%), De Cuyper, Cherki, B.Fernandes.
  Accepted differential risk, unchanged from GW7.
- **F9 (LOW) — execution.** The session is still expired (see Entry state).
  The lineup POST needs no approval but cannot run until credentials are
  imported; otherwise the user sets the lineup by hand: 3-5-2 as above,
  Haaland (C), Gabriel (V), bench Dubravka, Barry, Tarkowski, Shaw. No
  transfer is pending, so nothing can be booked as a hit.
- **F10 (LOW) — fixture decay.** SUN (E.Le Fée) and NEW turn hard from GW11;
  carried into GW9 planning with two free transfers.
- Two dead bench slots (Dubravka, Shaw): a Raya non-start has no cover.
  Schade p 0.80 in the XI, with Barry 0.016 behind on the bench.

## Rationale summary

- The user chose option A: hold the wildcard, bank the free transfer, decide
  again with two more rounds of data.
- No single free transfer passes the rule and no pair reaches the 6.0 gross
  needed for a hit, so banking is also what the rule selects unaided.
- XI, captain, vice and bench follow the objective's GW8 rows with the C20
  boundary tie-break (Groß over Barry).
- GW9 opens with 2 free transfers; Shaw → Justin is the fallers-first
  candidate under S7.

## Suggestions

Read data/suggestions.md through S8

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 6 | followed | both halves now complete: Ndiaye → Groß and Anderson → Schade inside the +14.449 blend / +5.210 prior-only triple; Ndiaye's marginal +2.503 / +0.665 and Anderson's +2.488 / +0.757 each clear the 2.0 gate on their own, so the steer broke no tie and the optimizer reached it unaided; EP6 delta of the row itself 0.00. The GW5 ledger's "Ndiaye half completed" was false in fact (never POSTed) and is superseded here |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |
| S3 | 6 | followed | Ndiaye → Groß made; marginal +2.503 blend / +0.665 prior against the plan without this sale (Scott + Anderson → E.Le Fée + Schade, +11.946 / +4.545), so the below-threshold clause was not needed |
| S4 | 6 | followed | Anderson → Schade made; marginal +2.488 blend / +0.757 prior against the plan without this sale (Scott + Ndiaye → E.Le Fée + Groß, +11.961 / +4.453); clears the gate on both readings, below-threshold clause not needed |
| S5 | 6 | followed | Scott → E.Le Fée made; EP6 0.00 for GW6–11 (status i, 0%); marginal +2.503 / +0.675 against the plan without this sale (Ndiaye + Anderson → E.Le Fée + Schade, +11.946 / +4.535) |
| S6 | 8 | rejected | closed by the user's directive, not by EP: the wildcard timing the row left open (GW6 or GW8) is taken at neither — at GW8 the user chose to hold the wildcard ("A, hold the wildcard, We can rethink after having some more data to rely on") although the v1 package cleared the chip gate (+9.800 blend / +6.557 prior-only; review F1 variant +9.537 / +8.627) and the no-Saka, Raya-kept packages clear it only with a prior-only sign flip (best R1 +7.523 / +3.213); the row's window ends GW8, so it closes here; the GW6 overhaul half was ledgered under S3–S5; 60 per GW stays unreachable (this plan 53.60 at GW8, 54.68 per GW over GW8–13; best package found 56.45) |
| S7 | 7 | standing | honoured: no transfer this GW because no move passes the transfer rule, which the row never overrides; of the named fallers still held, Shaw → Justin +1.439 / +2.019 (blend < 2.0), Richards → Silva +2.301 / −1.562 (prior sign flip), Thiago → João Pedro +1.139 / −0.516 (prior sign flip) and Mbeumo → Gibbs-White −5.326 / −3.776 all FAIL as singles; the plan is bank (+0.000), so no in-band tie to settle; EP6 delta of the row 0.00; policy stays live for GW9 with 2 FTs, where Shaw → Justin is the fallers-first candidate; read as a sell-side policy (review F5): no buy is made, so no faller is bought |
| S8 | 7 | standing | honoured: no transfer, so no buy to test against the profile; the GW6 buys are held because no move from them passes the gate (Schade → Stach +1.764 / +0.894, Groß → Stach +1.382 / +0.535, E.Le Fée → Stach −0.968 / −0.700); vice tie Gabriel 5.080 v Mbeumo 4.932 inside 0.5 single-GW EP: the row's read is mixed (Mbeumo 41 pts v Gabriel 35, four returns each; Gabriel at the more consistent club, ARS ATT rank 2 and CS rank 1), so the higher EP holds and Gabriel is vice; the XI boundary (Groß over Barry) is settled by C20 on DefCon share, and the row points the same way (Groß 58 pts, 5 returns, BHA the league's top scorers; Barry 28 pts, 3 returns); EP6 delta of the row 0.00 |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW9 deadline: 1 at GW8, none used, 1 accrues.
# team_value and bank on the GW7-verified selling-price basis (no transfer, no my-team read this cycle): Σ sell 98.7 + bank 0.4.
gw: 8
team_id: 8455344
team_value: 99.1
bank: 0.4
free_transfers_banked: 2
chip: null
chips_used: []
transfers_made: []
chip_plan:
  - {chip: wildcard, gw: 10, status: provisional}
  - {chip: 3xc, gw: 9, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 1, name: Raya, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: false, vice: true}
  - {id: 202, name: Richards, position: 3, captain: false, vice: false}
  - {id: 112, name: Van Hecke, position: 4, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 5, captain: false, vice: false}
  - {id: 542, name: E.Le Fée, position: 6, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 7, captain: false, vice: false}
  - {id: 94, name: Schade, position: 8, captain: false, vice: false}
  - {id: 124, name: Groß, position: 9, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 10, captain: true, vice: false}
  - {id: 106, name: Thiago, position: 11, captain: false, vice: false}
  - {id: 497, name: Dubravka, position: 12, captain: false, vice: false}
  - {id: 249, name: Barry, position: 13, captain: false, vice: false}
  - {id: 229, name: Tarkowski, position: 14, captain: false, vice: false}
  - {id: 423, name: Shaw, position: 15, captain: false, vice: false}
```
