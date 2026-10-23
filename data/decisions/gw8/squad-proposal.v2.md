# GW8 Squad Proposal (2026/27) — REVISION: hold the wildcard, bank the free transfer

Revision run after the red-team's REVISE (data/decisions/gw8/review.md).
The wildcard proposal it reviewed is archived as squad-proposal.v1.md.
Deadline 2026-10-23T17:30:00Z. Horizon GW8–13. Squad from the STATE block
of data/decisions/gw7/final.md; budget = its `team_value` 99.1.

**User decision for this revision, quoted verbatim:** "A, hold the wildcard,
We can rethink after having some more data to rely on." — option A being:
hold the wildcard and bank the free transfer; no transfers this GW; the
revision sets captain and bench order. Earlier in the cycle the user also
chose "C": keep Raya, drop Saka. Under this directive the v1 wildcard
package is withdrawn. The review's package findings F1 (Silva's prior-only
sign flip, the Calafiori + Kinsky variant), F4 (Wissa v Calvert-Lewin under
S8) and F5 (buying two fallers under S7) are moot: no player named in them
is bought. F2 (Saka's flag), F3 (template exposure of the package), F6
(Raya → Trafford) and F7 (price risk on the buys) fall with the package too.
F9 (expired session) now bears on the lineup POST only; F10 (SUN and NEW
turn hard from GW11) carries into GW9 planning with two free transfers.

**No transfers. Chip null. 3-5-2, Haaland (C), Gabriel (V). Predicted GW8
53.600. Bank £0.4m. FT at GW9: 2.**

Sell basis: the GW7-verified selling prices from data/decisions/gw7/final.md,
passed as `--sell` (the basis the review and both research files used), so
the CLI labels it `relayed`. No fresh `my-team` read this cycle; with no
transfer the prices are not load-bearing.

## Scoring — objective (verbatim)

`objective --gw 8 --sell 1:6.0,112:4.9,4:7.9,229:6.1,427:7.9,124:5.9,68:6.0,542:5.7,411:15.5,249:5.6,106:7.8,497:4.0,202:4.9,94:6.2,423:4.3 --bank 0.4 --free-transfers 1 --moves none`:

```
objective gw8 — horizon GW8–GW13; squad from data/decisions/gw7/final.md
sell basis: relayed (Σ sell 98.7 + bank 0.4 = 99.1)
baseline: blend 328.050 prior 318.513
legal single moves: 1582 (pool 416); top 10 by blend:
  1 | Richards → Silva | +2.301 | -1.562 | bank 0.3 | fails (prior sign flip)
  2 | Schade → Stach | +1.764 | +0.894 | bank 0.6 | fails (blend < 2.0)
  3 | Tarkowski → Silva | +1.741 | -2.077 | bank 1.5 | fails (prior sign flip)
  4 | Tarkowski → Calafiori | +1.711 | +0.272 | bank 0.5 | fails (blend < 2.0)
  5 | Van Hecke → Silva | +1.551 | -1.835 | bank 0.3 | fails (prior sign flip)
  6 | Shaw → Justin | +1.439 | +2.019 | bank 0.2 | fails (blend < 2.0)
  7 | Groß → Stach | +1.382 | +0.535 | bank 0.3 | fails (blend < 2.0)
  8 | Schade → Barnes | +1.263 | +2.765 | bank 0.5 | fails (blend < 2.0)
  9 | Thiago → João Pedro | +1.139 | -0.516 | bank 0.3 | fails (prior sign flip)
  10 | Shaw → Konsa | +1.096 | +0.884 | bank 0.1 | fails (blend < 2.0)
plan: none — blend +0.000 prior +0.000; bank 0.4; transfers 0 (free 1, hits 0); FT next 2
after plan, best single: Richards → Silva +2.301 / -1.562 — fails (prior sign flip)
reference (greedy): bank — no move passes its gate
verdict: PASS
GW8 XI 3-4-3 53.638: Raya, Gabriel, Richards, Van Hecke, Mbeumo, E.Le Fée, Tavernier, Schade, Haaland, Thiago, Barry; captain top 5: Haaland 5.798 0.94, Gabriel 5.080 0.95, Mbeumo 4.932 0.96, Thiago 4.501 0.95, E.Le Fée 4.406 0.94
boundary pairs within 0.25: Schade 3.676 (DefCon 0.030) | Groß 3.622 (0.043) ; Barry 3.660 (DefCon 0.008) | Groß 3.622 (0.043)
bench: Dubravka 0.107 (p 0.03 — dead), Groß 3.622, Tarkowski 3.247, Shaw 0.000 (p 0.00 — dead)
```

## Transfer decision

Transfer rule (free move: blend ≥ 2.0 and prior-only ≥ 0). Of 1582 legal
single moves none passes: the only move over 2.0 on blend (Richards →
Silva +2.301) flips sign on prior-only (−1.562), and the best move that
holds on prior-only (Schade → Stach +1.764 / +0.894) is under 2.0. A hit
needs a gross gain ≥ 6.0; the two best gate-shaped singles sum to 4.065, so
no hit path exists either. This confirms research-mid.md § 3c. The free
transfer is banked: 2 at the GW9 deadline.

Rows for the moves the open suggestions name, each graded as the single
free transfer (same `--sell` basis):

| Row | For | blend / prior | Verdict |
|---|---|---|---|
| Richards → Silva (202:566) | S7 (Richards a named faller) | +2.301 / −1.562 | FAIL, prior sign flip |
| Shaw → Justin (423:332) | S7 (Shaw a named faller, status i) | +1.439 / +2.019 | FAIL, blend < 2.0 |
| Thiago → João Pedro (106:383) | S7 (Thiago a named faller) | +1.139 / −0.516 | FAIL, prior sign flip |
| Mbeumo → Gibbs-White (427:480) | S7 (Mbeumo a named faller) | −5.326 / −3.776 | FAIL |
| E.Le Fée → Stach (542:335) | S8 (Le Fée a named GW6 buy) | −0.968 / −0.700 | FAIL |
| Groß → Stach (124:335) | S8 (Groß a named GW6 buy) | +1.382 / +0.535 | FAIL, blend < 2.0 |
| Schade → Stach (94:335) | S8 (Schade a named GW6 buy) | +1.764 / +0.894 | FAIL, blend < 2.0 |

Wildcard: not graded for play this GW — the user's directive holds it. For
the record, the v1 package scored +9.800 / +6.557 and the review's F1
variant +9.537 / +8.627 on this basis, both over the chip gate; the
no-Saka, Raya-kept packages in research-mid.md clear it only with a
prior-only sign-flipping component (best R1 +7.523 / +3.213). The user
weighed that and chose to hold; the set-1 window runs to GW19.

Steps 1–3 of the heuristic procedure (budget skeleton, XI fill, bench
build) do not apply to a no-transfer revision: the squad is unchanged from
GW7. Step 4 is the table above; step 5 is the ledger.

## Squad

Price = GW7-verified selling price (now_cost in brackets where different).
EP6 = `ep_total6`, GW8 = `ep_gw[0]`.

| Slot | Pos | Player | Id | Club | Price | GW8 EP | EP6 | p_start GW8 | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|
| 1 | GKP | Raya | 1 | ARS | 6.0 (6.1) | 3.827 | 21.66 | 0.95 | XI |
| 2 | DEF | Gabriel | 4 | ARS | 7.9 | 5.080 | 28.58 | 0.95 | XI · Vice |
| 3 | DEF | Richards | 202 | CRY | 4.9 | 4.044 | 22.70 | 0.95 | XI |
| 4 | DEF | Van Hecke | 112 | TOT | 4.9 | 3.565 | 24.30 | 0.95 | XI |
| 5 | MID | Mbeumo | 427 | MUN | 7.9 | 4.932 | 30.43 | 0.96 | XI |
| 6 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.406 | 26.20 | 0.94 | XI |
| 7 | MID | Tavernier | 68 | BOU | 6.0 (6.2) | 4.351 | 26.95 | 0.93 | XI |
| 8 | MID | Schade | 94 | BRE | 6.2 | 3.676 | 20.46 | 0.80 | XI |
| 9 | MID | Groß | 124 | BHA | 5.9 (6.2) | 3.622 | 23.74 | 0.94 | XI |
| 10 | FWD | Haaland | 411 | MCI | 15.5 (15.7) | 5.798 | 34.96 | 0.94 | XI · Captain |
| 11 | FWD | Thiago | 106 | BRE | 7.8 | 4.501 | 25.23 | 0.95 | XI |
| 12 | GKP | Dubravka | 497 | TOT | 4.0 | 0.107 | 0.68 | 0.03 | Bench GK (dead) |
| 13 | FWD | Barry | 249 | EVE | 5.6 (5.7) | 3.660 | 25.51 | 0.94 | Bench 1 |
| 14 | DEF | Tarkowski | 229 | EVE | 6.1 (6.2) | 3.247 | 23.02 | 0.95 | Bench 2 |
| 15 | DEF | Shaw | 423 | MUN | 4.3 | 0.000 | 7.32 | 0.00 | Bench 3 (status i, dead) |
| | | **Total** | | | **98.7** + bank 0.4 = 99.1 | | | | |

2 GKP / 5 DEF / 5 MID / 3 FWD. Clubs: ARS 2, EVE 2, BRE 2, MUN 2, TOT 2,
rest 1.

## Starting XI — 3-5-2

The objective's best GW8 XI is the 3-4-3 above (53.638 with captain), Barry
and Schade in, Groß on the bench. C20 applies C8's tie-break at the
XI/bench boundary: both boundary pairs the objective prints are inside the
0.25 band with Groß (DefCon share 0.043) holding the higher floor share
over Barry (0.008, 0.038 apart) and Schade (0.030, 0.054 apart). One slot
changes: Groß replaces the XI member with the lowest floor share, Barry
(−0.038 EP). Schade stays: against Barry he is 0.016 apart on EP and holds
the higher share. Tarkowski 3.247 is 0.413 below Barry, outside the band.

| Slot | Player | Pos | GW8 fixture | GW8 EP |
|---:|---|---|---|---:|
| 1 | Raya | GKP | EVE (H) | 3.827 |
| 2 | Gabriel (V) | DEF | EVE (H) | 5.080 |
| 3 | Richards | DEF | NEW (H) | 4.044 |
| 4 | Van Hecke | DEF | CHE (A) | 3.565 |
| 5 | Mbeumo | MID | BOU (H) | 4.932 |
| 6 | E.Le Fée | MID | LEE (H) | 4.406 |
| 7 | Tavernier | MID | MUN (A) | 4.351 |
| 8 | Schade | MID | HUL (A) | 3.676 |
| 9 | Groß | MID | LIV (A) | 3.622 |
| 10 | Haaland (C) | FWD | AVL (A) | 5.798 |
| 11 | Thiago | FWD | HUL (A) | 4.501 |
| | XI total | | | 47.802 |
| | + captain | | | 5.798 |
| | **Predicted GW8** | | | **53.600** |

C12 (promoted-club defensive rows): Schade and Thiago at HUL (A) are
attacking rows on a banded fixture; no XI defender or keeper faces a
promoted club this GW.

## Captain and vice

Top 5 in the XI by single-GW EP, undiscounted (`objective` captain line):

| Rank | Player | GW8 EP | p_start_gw[0] | Points GW1–7 (returns ≥ 5) |
|---:|---|---:|---:|---|
| 1 | **Haaland** (C) | 5.798 | 0.94 | 58 (6) |
| 2 | Gabriel (V) | 5.080 | 0.95 | 35 (4) |
| 3 | Mbeumo | 4.932 | 0.96 | 41 (4) |
| 4 | Thiago | 4.501 | 0.95 | 18 (1) |
| 5 | E.Le Fée | 4.406 | 0.94 | 24 (2) |

Captain Haaland, 0.718 clear of Gabriel — outside the 0.5 band, EP decides.
Vice Gabriel: 0.148 over Mbeumo, inside the band; both p_start_gw[0] ≥ 0.85,
so the rule's tiebreak does not separate them and the higher EP holds. S8
read as a tiebreak is mixed — Mbeumo has more points (41 v 35, four returns
each), Gabriel the more consistent club (ARS: ATT rank 2, CS rank 1, v MUN
ATT rank 10) — so it does not overturn the EP order. Points per round from
the cached event-live snapshots (GW1–7).

## Bench order

| Slot | Player | Pos | GW8 EP | p_start | DefCon share |
|---:|---|---|---:|---:|---:|
| 12 | Dubravka | GKP | 0.107 | 0.03 | — |
| 13 | Barry | FWD | 3.660 | 0.94 | 0.008 |
| 14 | Tarkowski | DEF | 3.247 | 0.95 | — |
| 15 | Shaw | DEF | 0.000 | 0.00 | — |

Barry ahead of Tarkowski: 0.413 apart, outside C8's band, so EP order.
Shaw last: status i, 0%, no return date. Dubravka is the only other keeper.

Bench check: Dubravka (12, 0.03), Shaw (15, 0.00)

Both dead slots are reported, not transfer reasons: the objective scores the
bench at 0 and no move from either passes the gate this GW (Shaw → Justin
+1.439 / +2.019 is the closest). Auto-sub cover is Barry then Tarkowski; a
keeper non-start has no cover.

## Transfers

None. Free transfers: 1 at the GW8 deadline, banked → 2 at the GW9 deadline.

Gate ids: 1,4,229,112,202,423,427,124,68,542,94,411,249,106,497

## Chips

`chip: null` — the user's directive holds the wildcard ("A, hold the
wildcard, We can rethink after having some more data to rely on"). The chip
gate is therefore not applied this GW; the figures above record what the
packages scored.

Provisional chip plan (windows from bootstrap `chips`: wildcard and
freehit GW2–19, bboost and 3xc GW1–19):

- wildcard GW10 — the next earmark, not a commitment: two more rounds of
  data (GW8, GW9) before the user rethinks, and GW10 is the last deadline
  before the GW11 fixture turn the fixture analyst flags (BHA and LIV turn
  easy, FUL, SUN and NEW turn hard), so a GW10 rebuild is shaped by GW11–16
  rather than by fixtures already in play. With no wildcard at GW9 the two
  banked free transfers cover GW9 (the best pair in research-mid.md § 3c is
  worth about +3 blend over GW9–13).
- 3xc GW9 — Haaland v BHA (H), his own GW9 row 6.276 (C5: on his own EP;
  MCI λ_att 2.09 supports but does not carry it). His GW11 row FUL (H) 6.371
  is 0.095 higher, inside noise; the GW9 cycle decides on fresh EP.
- freehit GW16 — placeholder, no blank or double in GW8–13.
- bboost GW19 — placeholder; live only once a wildcard repairs the two dead
  bench slots (Dubravka, Shaw).

## Rationale and rejected alternatives

- The user chose option A. The optimizer's role in this revision is to
  verify that no single free transfer passes the gate on the verified sell
  basis (it does not: 1582 legal moves, best gate-shaped +1.764 < 2.0, best
  blend +2.301 with a prior sign flip), then set the XI, captain, vice and
  bench order for the unchanged squad.
- Rejected: Richards → Silva (+2.301 / −1.562) — C14's prior-only rule;
  Schade → Stach (+1.764 / +0.894) — 0.236 short of the blend gate; Shaw →
  Justin (+1.439 / +2.019) — 0.561 short, though it is the move the two
  dead bench slots argue for and the strongest prior-only single; it heads
  the GW9 pair candidates (Shaw → Justin + Richards → Silva +3.10 / +0.80
  over GW9–13 per research-mid.md, the Silva half still carrying a sign
  flip).
- Rejected: any hit — no pair of singles reaches a gross 6.0.
- Template exposure (review F3, restated for the hold): held > 30%-owned
  players are Haaland, Raya (44.9%), Groß (45.8%); still off João Pedro
  (73.3%), Calafiori (54.3%), Rogers (48.8%), De Cuyper, Cherki,
  B.Fernandes. Accepted differential risk, unchanged from GW7.
- Risks: two dead bench slots (a Haaland or Raya non-start costs the full
  row — Raya has no cover at all); Schade p 0.80 in the XI with Barry 0.016
  behind on the bench, so a Schade non-start is nearly free; Shaw's EP6
  7.32 is a guessed ramp (0.0 / 0.3 / 0.45 / 0.55 / 0.6 / 0.6) with no
  return date in his news.
- Execution (review F9): the session was expired at step 1. The lineup
  POST needs no approval, so if credentials are re-captured the executor
  applies it; otherwise the user sets by hand: 3-5-2 as above, Haaland (C),
  Gabriel (V), bench Dubravka, Barry, Tarkowski, Shaw. No transfer is
  pending, so nothing is booked as a hit either way.

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
