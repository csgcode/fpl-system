# GW11 Red-Team Review — squad-proposal.md (first proposal, no prior revision)

**Verdict: APPROVE** — no HIGH finding. Five MED/LOW findings below are
accepted risks for final.md to carry.

Reviewed: data/decisions/gw11/squad-proposal.md (Calafiori → De Cuyper, free;
no chip; captain Haaland, vice Gabriel). Deadline 2026-11-21 11:00 UTC.

## What was recomputed independently

| Check | Result |
|---|---|
| `objective --gw 11 --sell <proposal list> --bank 0.1 --free-transfers 3 --moves 8:115` | reproduces the proposal line for line: baseline 345.346 / 334.971, plan +2.374 blend / +1.881 prior-only, `verdict: PASS`, XI 58.405, `tie-break group: Calafiori winner De Cuyper (decided by blend)` |
| `final-check --gw 11 --proposal …` | PASS P1, P2, P3 (STATE parses, ledger present, nothing dropped against GW10 final.md) |
| Budget | selling prices after the move sum to 99.1 (15.6, 9.1, 8.0, 7.9, 6.3, 6.0, 5.7, 5.6, 5.5, 5.5, 5.0, 5.0, 5.0, 4.5, 4.4); + bank 0.5 = 99.6 = STATE `team_value`. Bank is not added twice. Bank 0.1 + 5.9 − 5.5 = 0.5 |
| Positions | GKP 2, DEF 5, MID 5, FWD 3 |
| Clubs | BHA 2, BOU 2, LEE 2, TOT 2; ARS, MUN, NEW, SUN, MCI, LIV, EVE 1 each — none at 3 |
| Formation | 1-4-3-3, legal; slot 1 and slot 12 are goalkeepers; one captain (411) and one vice (4), both in the XI |
| Free transfers | 3 live − 1 used + 1 accrued = 3 at GW12 (cap 5 not reached, nothing wasted) |
| Flags (gw11 bootstrap, fetched 2026-11-20 11:01 UTC) | all 15 picks status `a`, no news text, chance null or 100; De Cuyper status `a`, no news |
| Chips | bootstrap `chips`: bboost GW1–19, freehit GW2–19 remain; wildcard (GW8) and 3xc (GW9) used; `chip: null` |

## Findings

### F1 — MED — GW12–14 congestion is not priced into any p_start (checklist 1)
Deadlines: GW12 27 Nov, GW13 1 Dec (midweek), GW14 5 Dec — three rounds in
nine days. Every squad row carries a flat `p_start_gw` (0.93–0.95 in all six
gameweeks), including the six players at clubs the analysts flagged for
European or cup rotation (Gabriel, Haaland, Isak, Barnes, Van Hecke, Kinsky).
The six-gameweek totals are therefore optimistic for those rows. It does not
change this week's decision: the one transfer sells an ARS full-back
(Calafiori, p_start 0.90, minutes 22 / 90 / 68 over rounds 8–10) for a BHA
starter with no European fixture, so repricing would widen the gain. No
starter is below 0.85 for GW11 and no bench player is a non-player.
Accepted risk; the GW12 and GW13 cycles should expect lower p_start on these
six and have 3 free transfers to respond.

### F2 — MED — Template exposure after the sale (checklist 5)
Owned above 30% and not held after the move:

| Player | Owned | EP6 | Our holder in that slot |
|---|---:|---:|---|
| Rogers (CHE MID) | 54.2% | 24.14 | every owned MID is higher (lowest: Gomez 23.43 on the bench; XI lowest Tavernier 28.30) |
| Calafiori (ARS DEF) | 48.7% | 23.73 | sold for De Cuyper 25.93, owned 48.6% — ownership exposure is unchanged |
| Groß (BHA MID) | 48.6% | 25.79 | Barnes → Groß is +0.621 / −1.723, fails on prior sign |
| Raya (ARS GKP) | 47.6% | 21.26 | Trafford 22.53 |
| Cherki (MCI MID) | 33.6% | 16.69 | p_start 0.55 |
| N.Jackson (AVL FWD) | 33.0% | 25.51 | Barry 27.68 |
| João Pedro (CHE FWD) | 30.5% | — | status `i` |

The real change is to Arsenal's defence: ARS is clean-sheet rank 1 for the
window (ΣP(CS) 2.20) and the template holds two or three of Raya, Calafiori,
Gabriel, Konsa; after the sale we hold Gabriel only. An ARS clean-sheet run
costs rank. The files price this (Calafiori loses to De Cuyper in four of six
gameweeks, GW13 and GW14 excepted) and the swap is like for like on
ownership, so the differential is deliberate. Accepted risk.

### F3 — MED — Two held players at price-fall risk (checklist 11)
Barnes fell 6.1 → 6.0 this event with 81,995 out against 4,703 in; Mbeumo is
130,298 out against 13,145 in with the price still 7.9. Both sell at their
current price, so each further fall takes 0.1 off `team_value`. No sale of
either passes the gate (Mbeumo → Gibbs-White −2.610 / −2.347; Barnes → Groß
+0.621 / −1.723), so holding is correct on points; the cost is up to 0.2 of
team value. Barnes is also the third outfield substitute at £6.0m.
The buy side runs the other way: De Cuyper has 243,074 transfers in this
event and has already risen once, so the transfer should be POSTed today, not
held to the deadline. Bank after the plan is 0.5, so an overnight rise to 5.6
leaves 0.4 and no fallback transfer is needed (the < £0.2m rule does not
fire).

### F4 — LOW — Bench tie-break used last week's DefCon shares (checklist 1, C8)
Justin 3.538 v Barnes 3.510 is inside C8's 0.25 band. The proposal settles it
on the GW10 shares (0.137 v 0.015) because `objective` prints shares only for
XI/bench boundary pairs. The window rates agree — Justin's DefCon term is
3.58 of 23.44 EP6 against a winger's — so the order Justin, Barnes stands.
Tool gap logged in docs/backlog.md.

### F5 — LOW — Banded clean-sheet rows are not shown to be below the largest term (C12 / C4 clause)
Two GW11 starters play banded fixtures: De Cuyper at HUL (P(CS) 0.36 ±) and
Van Hecke v IPS (0.35 ±). The proposal names the band but does not state that
the banded clean sheet is not either player's largest EP term. From the
window terms it is not: De Cuyper appearance 11.11, attack 9.31, clean sheet
6.56; Van Hecke appearance 11.40, clean sheet 7.03, attack 5.64 — appearance
leads both, and De Cuyper's attack term also exceeds his clean-sheet term.
The files carry terms for the window only, not per gameweek, so the GW11
reading is an estimate. No change.

### Checked, no finding

- **Concentration (4):** no club supplies more than two players; the BHA pair
  is one defender and one benched midfielder; the LEE pair shares a clean
  sheet but Justin is on the bench.
- **Fixture myopia (6):** GW17–19 have ten fixtures each, no blank or double.
  TOT turns hard from GW14 and ends GW19 at MCI (Van Hecke, Kinsky); BHA runs
  FUL(A), TOT(A), MUN(H). With 3 free transfers banked and one accruing each
  week the squad can be repaired; nothing collapses at a point with no
  transfers.
- **Hits (7):** none taken. The largest second-move marginal is +1.985
  against the 6.0 a paid move needs. The single move is the `tie-break
  group:` winner and is positive on both readings.
- **Captaincy (8):** Haaland 6.047 is the highest undiscounted GW11 EP, 0.741
  clear of Isak. Vice Gabriel 5.229 over Isak 5.306 gives up 0.077 in a slot
  that pays only if Haaland misses (p_start 0.94); the spec's captain rule
  does not bind the vice and both clear 0.85.
- **Recency (9):** the buy is not a haul chase. De Cuyper's last six scores
  are 6, 15, 6, 1, 9, 6; the gain holds prior-only (+1.881); BHA's defensive
  rating (DEFW 0.92, rank 8) is built on xGA, not on the seven clean sheets.
  The captain scored 2 last round and is picked on EP.
- **Chips (10):** nine gameweeks (GW11–19) remain for two chips. The move
  swaps one starting defender for another; the bench (Kinsky, Gomez, Justin,
  Barnes, all p_start ≥ 0.94, 14.47 EP) is untouched for a Bench Boost. Free
  hit on GW11 alone fails the chip gate (+0.313 over the plan). Neither
  earmark (freehit GW16, bboost GW19) has a blank or double behind it — both
  are placeholders, as the proposal says.

## Checklist item 12 — Suggestions: PASS, no finding

Marker: `Read data/suggestions.md through S8`; the file holds S1–S8, nothing
above the marker, no withdraw row, no row with From GW > 11, no Until GW that
has newly passed (S6's Until GW 8 was closed `followed` at GW8).

| S# | Previous ledger (GW10 final.md) | Open at GW11? | Proposal row | Check |
|---|---|---|---|---|
| S1 | followed, GW6 | no | followed, GW6 | verbatim |
| S2 | rejected, GW4 | no | rejected, GW4 | verbatim |
| S3 | followed, GW6 | no | followed, GW6 | verbatim |
| S4 | followed, GW6 | no | followed, GW6 | verbatim |
| S5 | followed, GW6 | no | followed, GW6 | verbatim |
| S6 | followed, GW8 | no | followed, GW8 | verbatim |
| S7 | standing, GW7 | yes | standing, GW7 | GW unchanged; reason says how the plan honours it; figures reproduce |
| S8 | standing, GW7 | yes | standing, GW7 | GW unchanged; reason says how the plan honours it; figures reproduce |

Closed rows S1–S6 were compared by `diff` against the GW10 ledger: identical.
Open set recomputed: S7 and S8 only; both have a row. No `deferred` row
exists, so the three-cycle rule does not apply. No row was newly set to
`followed` or `rejected` this cycle, so there is no EP6 delta to reproduce.

S7 figures checked against the gw11 bootstrap: Mbeumo in 13,145 / out
130,298, price 7.9; Barnes in 4,703 / out 81,995, `cost_change_event` −1;
Haaland in 29,389 / out 55,842; Calafiori in 85,587 / out 48,073 (a net
riser, as stated). The plan does not contradict the row: the only faller
sales available lose EP or fail the gate, and the row yields to the gate by
its own wording.

S8 figures checked against the players files: De Cuyper returns 4/5 v Silva
3/5 (`objective`'s tie-break line); Gabriel 4/5, p4 0.696, LOW v Isak 3/5,
p4 0.481, MED. The buy is a ten-from-ten starter and the plan does not
contradict the row.

## For final.md — accepted risks

1. F1: flat p_start across the GW12–14 congestion for six players at clubs
   with European or cup fixtures.
2. F2: one Arsenal defender held against a template of two or three.
3. F3: Barnes and Mbeumo held through likely price falls (up to 0.2 of team
   value); POST the De Cuyper transfer today.
