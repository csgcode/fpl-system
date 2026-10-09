# GW6 Red-Team Review

Reviewed: `data/decisions/gw6/squad-proposal.md` (first optimizer run) against
`data/analysis/gw6/*`, `data/raw/gw6/bootstrap.json` and the per-player
summaries, `data/retro/gw5.md`, the corrected STATE block of
`data/decisions/gw5/final.md`, and `data/suggestions.md`.

**Verdict: APPROVE.** No HIGH finding. Three MED findings, each with a named
action for the finalizer or executor; none changes the fifteen, the XI, the
captain or the chip call.

## Independent recomputation

Every number below was rebuilt from the EP files and the bootstrap, not read
from the proposal.

| Check | Proposal | Recomputed | Match |
|---|---:|---:|---|
| Hold objective, GW6–11 (best XI + captain) | 325.67 | 325.67 | yes |
| Proposed squad objective, GW6–11 | 340.12 | 340.12 | yes |
| Package gain | +14.449 | +14.45 | yes |
| GW6 predicted (3-5-2, Haaland C) | 56.178 | 56.18 | yes |
| GW6–8 mean | 56.37 | 56.37 | yes |
| Pair Scott + Anderson → E.Le Fée + Schade | +11.946 | +11.946 | yes |
| Pair Scott + Ndiaye → E.Le Fée + Groß | +11.961 | +11.961 | yes |
| Marginals Scott / Ndiaye / Anderson | +2.503 / +2.503 / +2.488 | same | yes |
| Wildcard GW6 best-blend squad: cost / objective / GW6–8 mean | 99.2 / 350.09 / 57.63 | 99.2 / 350.09 / 57.63 | yes |
| 3 FTs now + GW8 wildcard rebuild (today's EP) | 113.27 + 234.86 = 348.13 | 113.27 + 234.86 | yes |
| Triple with Stach for Groß | +13.293 | +13.293 | yes |

Constraints, from the bootstrap: 2 GKP / 5 DEF / 5 MID / 3 FWD; club counts
ARS 2, EVE 2, MUN 2, BRE 2, every other club 1; funding sells 6.0 + 5.8 + 6.3 =
18.1 against buys 5.7 + 5.9 + 6.2 = 17.8 (all three buy prices equal bootstrap
`now_cost`), bank 0.0 → 0.3; 3-5-2 is legal; exactly one captain and one vice,
both in the XI; all fifteen `picks:` ids resolve to the named players. The
three free transfers are the entry's actual count (`my-team`: 3 FTs, bank
0.0). All pass.

## Findings

| # | Item | Severity | Finding | Action |
|---|---|---|---|---|
| F1 | 11 Price risk | **MED** | The plan is bank-fragile overnight. Groß has 1,090,374 transfers in this event and has already risen twice (`cost_change_event` +2); Schade 600,777 in and +1. Scott (0%, injured) has 111,940 out, Ndiaye 98,722 out and already −1. Price changes land at about 01:30 UTC, eight hours before the deadline. Groß +0.1 and Scott −0.1 leaves bank 0.1; Groß +0.1, Schade +0.1, Scott −0.1, Ndiaye −0.1 leaves −0.1 and `make-transfers` refuses on bank. | POST the three transfers today, before the overnight price run, not on deadline morning. If the bank does break, the named fallback is Stach (LEE, £6.0m, id 335) in place of Groß: the triple E.Le Fée + Stach + Schade is +13.293 blend / +5.459 prior-only, the best triple on prior-only, and costs 99.5 against 99.2 only because Schade's 6.2 is kept, so it needs Scott and Ndiaye to hold price; failing that, Stach for Schade (+13.308, cost 99.2). |
| F2 | 9 Recency bias | **MED** | Groß's EP6 26.58 is the squad's largest blend-over-prior gap (prior-only 22.17). His 47 points come from 3 goals and 4 assists on 1.77 xG + 0.86 xA, and 9 bonus in five starts; the bonus term alone is 5.92 of his EP6 and is priced at 1.06 per start against a prior-season rate of about 0.55. If the bonus regresses to the prior, his EP6 falls to roughly 23.8, below Stach (25.09, prior-only above Groß, DefCon hits in 3 of 5 rounds). The points are frequent (three double-digit rounds in five) but half of them sit above his underlying numbers. | Hold the pick: the blend is the model's reading, Groß is a penalty taker on the fifth-best attacking ticker, 31.9% owned (closes the template gap), 90 × 5, and the package stays positive on prior-only. Record Stach as the named alternative so the GW8 wildcard re-prices him without a transfer cost if GW6–7 reverse the form. Not a revision trigger: −1.16 blend / +0.25 prior between the two. |
| F3 | 5 Template | **MED** | R3 names B.Fernandes, Saka and Calafiori as the unheld template and omits the two largest: João Pedro (CHE, **63.6%** owned, the most-owned player after Haaland) and Rogers (CHE, 41.6%). Thiago → João Pedro is the best paid single (+1.636 / −1.808) and fails the gate; João Pedro is `d` 75%, p_start 0.68 HIGH, 0 minutes in GW5. Not holding him is defensible, but it must be stated, since a João Pedro haul is the rank-volatility event the squad is most exposed to. | Finalizer adds João Pedro and Rogers to R3 with the gate figures above. No squad change. |
| F4 | 1 Minutes | LOW | Every XI starter is at p_start ≥ 0.90 and LOW; Shaw (bench 3) is 0.75 MED, status `a` 100%, 83' in GW5; Dubravka (bench GK) is 0.03, dead, carried as R1. No XI player carries a flag. | None; R1 stands, routed to the GW8 wildcard. |
| F5 | 2 Flags | LOW | Scott `i` 0% "Thigh injury – Unknown return date" (news 2026-10-05) is sold. Shaw's `news_added` is stale (2026-09-11) but his `status` is `a` and chance 100, so the gate's value-based diff is right. Thiago, Barry and the three incoming players carry no flag. | Freshness gate at finalizer as usual. |
| F6 | 4 Concentration | LOW | No club supplies more than two attack-dependent starters: BRE Schade + Thiago (Thiago benched), EVE Tarkowski + Barry, MUN Mbeumo + Shaw. Raya and Gabriel share one clean-sheet event (ARS v LEE). E.Le Fée and Groß are on opposite sides of SUN v BHA, so one's attacking return is the other's conceded goal — immaterial for two midfielders whose clean-sheet terms are about 1 point each. | None. |
| F7 | 6 Fixture myopia | LOW | Groß's GW8 LIV (A) and GW9 MCI (A) are the squad's worst two rows; Thiaw plays for the 17th-ranked club on both tickers with a −0.40 attacking swing in GW9–11. Both are inside the window the GW8 wildcard rewrites, and the squad carries 2 banked FTs into it. | None. |
| F8 | 7 Hits | LOW | No hit taken. Best paid single +1.636 gross against a 6.0 gate and sign-flips. | None. |
| F9 | 8 Captaincy | LOW | Haaland 5.786 v Mbeumo 5.230 among owned players, gap 0.556, every candidate LOW so the certainty multipliers are all 1.00 and reorder nothing; B.Fernandes (5.777, not owned) is unreachable. Haaland's LIV (A) is his window-worst row (λ_att 1.59), which is a reason the lead is small, not a reason to switch. Vice on a different fixture. | None. |
| F10 | 10 Chip path | LOW | Wildcard GW8, 3xc GW9 (BHA (H) 2.26, band-free, C5 satisfied; GW11 FUL (H) is the tied fallback), freehit GW16, bboost GW19 — four chips, four distinct gameweeks, all inside their bootstrap windows and before the GW19 stop. Selling Ndiaye and Anderson forecloses nothing: neither is a chip target, and it frees two MCI slots for Guéhi at the wildcard. Bench Boost stays blocked behind the dead GK2 and Shaw until the wildcard. | None. |
| F11 | 3 Constraints | LOW | All recomputed above; `free_transfers_banked: 1` is right (3 available, 3 used, 1 accrues); `team_value: 99.2` is the selling-price basis the STATE comment declares. | None. |

## The two questions the user asked

### Wildcard GW6 or GW8

The proposal's arithmetic is right, and the review's own reading is that the
case for waiting is slightly stronger than the proposal states.

| Path | GW6–11 blend | prior-only | GW6–8 mean | Banked FTs at GW8 |
|---|---:|---:|---:|---:|
| 3 FTs now, wildcard GW8 (chosen) | 348.13 (rebuild on today's EP) | 321.80 (pre-rebuild) | 56.37 | 2 + the wildcard |
| Wildcard GW6, best blend build | 350.09 | 320.23 | 57.63 | 5 |
| Wildcard GW6, LOW/MED rows only | 348.09 | 319.05 | 57.51 | 5 |

- The +1.96 edge for a GW6 wildcard exists only in the best-blend build, and
  that build is: 2 COV + 2 IPS players, three HIGH-uncertainty rows (Thomas,
  Davis, Akpom at p_start 0.10 as a dead third forward) and one MED
  (Rushworth). Every defensive term for a COV or IPS defender sits inside the
  C12 band, so the C4 residual rule — no selected player takes his largest
  defensive term from a promoted-club fixture — would bite on both £4.0m
  defenders every week. The proposal did not say this; it strengthens its
  rejection.
- The robust build (348.09) does not beat the chosen path (348.13) at all.
- The prior-only reading goes the other way (−1.57).
- The real cost of waiting is three banked free transfers, as the proposal
  says; the real cost of going now is making the one-off rebuild on a 53/47
  blend with no GK2 or DEF5 priced on two more rounds of data.
- The user's own research rule was "switch only if well above 2 EP per GW on
  GW6–8"; the measured gap is 1.26.

Hold at GW8. One caveat for the finalizer to carry: the GW8 rebuild used for
the fair comparison (234.86) also contains HIGH rows (Davis, Greaves, Simms at
p_start 0.18), so the +8.0 the wildcard is forecast to add over GW8–11 will
shrink once the GW8 analyst prices those slots on real minutes. The decision
does not depend on that number.

### Are E.Le Fée, Groß and Schade consistent performers or one-off spikes?

Per-round points, minutes and underlying from the GW6 summaries (rounds 1–5):

| Player | Points | Minutes | G+A | xG + xA | Bonus | Read |
|---|---|---|---|---|---|---|
| E.Le Fée | 2, 3, 8, 0, 5 (18) | 79–90 × 5 | 1 + 1 | 2.06 + 1.34 = 3.40 | 1 | **Under-performing**: two returns on 3.4 expected. His EP is built on position-leading xG, penalties and corners, not on points scored — the opposite of a spike. The user's "consistent high scorer" label does not describe his points yet; it describes his chances. |
| Groß | 2, 13, 1, 17, 14 (47) | 90 × 5 | 3 + 4 | 1.77 + 0.86 = 2.63 | 9 | **Over-performing**: seven returns on 2.6 expected, nine bonus. Three double-digit rounds in five is consistency in points, but roughly half of it sits above his numbers (F2). Penalty taker, which supports a higher floor than the xG alone. |
| Schade | 3, 10, 2, 15, 9 (39) | 87–90 × 5 | 3 + 2 | 1.52 + 0.32 = 1.84 | 6 | **Over-performing this season, but backed by last season**: 12.08 xG in 2,744 minutes in 2025/26 (8 goals, an under-performer then). His EP rests on that prior xG rate, so the blend-over-prior gap is small (26.57 v 24.73). Second penalty taker at the third-best attack. The best-founded of the three. |

All three are nailed (5/5 starts, 79'+ every round, LOW uncertainty), which is
the part of "consistent" that matters most for a 6-GW horizon. Groß is the
only one of the three bought partly on a spike, and his alternative is on the
table (F2).

## Ledger (checklist item 12)

Open set recomputed. Previous ledger (`data/decisions/gw5/final.md`): S1
`standing` GW4, S2 `rejected` GW4 — so S1 is the only carried open row, and
the CORRECTION reopens both of its halves. `data/suggestions.md` rows S3–S6
have From GW 6 ≤ 6 and no Until GW passed, so all four are open at GW6. S7
(From GW 7) is above the proposal's `through S6` marker and is not a finding.
No `withdraw` rows.

| S# | Expected | Proposal | Check |
|---|---|---|---|
| S1 | open; standing → may close | followed, GW6, EP6 delta 0.00, both halves named | clean: the plan contains both moves; the optimizer reached them unaided (each sale clears the gate on its own marginal), so delta 0.00 is reproducible |
| S2 | closed, carried verbatim | rejected, GW4, text identical to the GW5 ledger | clean |
| S3 | open, From GW 6 | followed, GW6, marginal +2.503 / +0.665 | reproduced (14.449 − 11.946) |
| S4 | open, From GW 6 | followed, GW6, marginal +2.488 / +0.757 | reproduced (14.449 − 11.961) |
| S5 | open, From GW 6 | followed, GW6, marginal +2.503 / +0.675 | reproduced |
| S6 | open, From GW 6, Until GW 8 | standing, GW6; reason states how the plan honours it (53.99 → 56.37 per GW on GW6–8), why the wildcard waits, and that 60 is unreachable; names its closing condition | clean; `standing` is the right status for a GW6–8 target that completes at the wildcard |

No open S# without a row, no closed row altered, no From GW > 6 row present,
no deferral, no `followed` row below −0.5 or unreproducible. The ledger passes.

## Accepted risks to carry into final.md

R1–R5 from the proposal stand. Add:

- **R6 — overnight price exposure (F1).** Three transfers, bank 0.3, two
  incoming players on rising momentum and two outgoing on falling momentum.
  Mitigation: execute today; fallback Stach.
- **R3 widened (F3).** João Pedro 63.6% and Rogers 41.6% unheld, with the gate
  figures.

## Backlog

One row appended to `docs/backlog.md` (A5, WORKFLOW): the execution plan has
no fallback transfer, so an overnight price move that breaks the bank by
£0.1m leaves the executor with only a refusal on deadline morning.
