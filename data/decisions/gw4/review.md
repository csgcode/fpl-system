# GW4 Red-Team Review — data/decisions/gw4/squad-proposal.md

Reviewer: A5. Deadline 2026-09-12 12:30 UTC. Snapshot 2026-09-11 17:58 UTC
(18.5h old at the deadline). Live `my-team` 18:10 UTC: bank 0.0, 1 FT, sell Σ 99.4.

## Verdict: APPROVE

No HIGH finding. Five MED findings are accepted risks to carry into final.md
(§Accepted risks below). Every number in the proposal that I could recompute
reproduced within rounding — see §Independent recomputation.

## Independent recomputation

| Check | Proposal | Recomputed | Result |
|---|---|---|---|
| Budget | sell Σ 99.4 + bank 0.0 | 15 relayed selling prices Σ 99.4; bootstrap now_cost Σ 99.6; no transfer → spend 0.0 | PASS |
| Position counts | 2 GKP / 5 DEF / 5 MID / 3 FWD | Raya, Dubravka / Gabriel, Tarkowski, Richards, Thiaw, Shaw / Mbeumo, Tavernier, Ndiaye, Scott, Anderson / Haaland, Thiago, Barry | PASS |
| Club cap | MCI 3, others ≤ 2 | MCI 3 (Haaland, Ndiaye, Anderson), ARS 2, EVE 2, MUN 2, BOU 2, CRY 1, BRE 1, TOT 1, NEW 1 = 15 | PASS |
| Formation | 3-4-3 | positions 1–11: 1 GK, 3 DEF, 4 MID, 3 FWD; captain Haaland and vice Gabriel both in the XI; slot 12 is the GK | PASS |
| Free transfers | 1 available → bank to 2 | 1 + 1 accrued = 2 ≤ 5 | PASS |
| GW4 predicted | 55.21 blend / 52.66 prior-only | 49.21 + 6.00 = 55.20 blend; 47.08 + 5.58 = 52.66 prior-only (own `fpl ep` rerun, prior_weight 1.0 on every row) | PASS |
| 6-GW objective | 338.51 blend / 327.24 prior-only | 338.51 / 327.24; per-GW best XI and formations match §3 exactly | PASS |
| Swap pass (top singles) | Anderson→Stach +1.38 / −2.85; Thiago→JP +1.27 / +0.43; Richards→De Cuyper +1.05 / −0.96; Tarkowski→Calafiori +0.79 / +0.39; Scott→Barnes −0.42 / +2.94 | identical to ±0.01 on both readings | PASS |
| Swap pass (pairs) | Cherki+Wissa +5.06 / +3.46; Janelt+Guéhi +4.99 / −2.77; Wissa+Janelt +1.49 / +5.91 | identical; every other pair above +4 flips sign on prior-only | PASS |
| S2 ceiling | 376.98 = 62.8 per GW | 376.98 / 62.83 (unconstrained best XI + captain per GW) | PASS |
| Chip windows | wildcard/freehit GW2–19, bboost/3xc GW1–19 | bootstrap `chips`: wildcard 2–19, freehit 2–19, bboost 1–19, 3xc 1–19 | PASS |

## Findings

| # | Sev | Item | Finding | Alternative / disposition |
|---|---|---|---|---|
| F1 | MED | 1, 9 | XI slot 11: Barry 3.87 v Anderson 3.85 is a 0.02 blend edge broken toward Barry by S1. Prior-only reverses it by 0.81 (3.44 v 4.25) and the prior-only optimum XI (3-5-2 with Anderson) is 53.46 v 52.66. Barry p_start 0.88 (78/69/90 minutes) v Anderson 0.92. Using a suggestion to break a ≤ 0.5 tie is permitted, but the tie is 0.02 one way and 0.80 the other. | Start Anderson (3-5-2), Barry to bench 13. Expected cost of the proposal's choice ≈ 0 on blend, −0.8 on prior-only. Not a revision trigger: inside model noise and user-steered. Accepted risk if kept. |
| F2 | MED | 11, 6 | The headline payoff of banking — Anderson + Thiago → Cherki + Wissa at GW5 (+5.06 / +3.46, free) — needs £14.0 from a £14.2 sale. Wissa is rising (+457k net in this event, already +0.1); Thiago is falling (−230k net out, already −0.1). One more move each → 14.1 v 14.1; two more → infeasible. | No hedge exists: Thiago → Wissa alone is −0.68 blend / +2.03 prior (sign flip) and Cherki (7.8) is unaffordable from Anderson (6.3) alone. Accept; the GW5 optimizer re-derives on live prices and must not treat the pair as committed. |
| F3 | MED | 5 | Template exposure list is incomplete and misquoted: B.Fernandes is 44.0% owned (proposal says 48.6%); Szoboszlai 38.4% and Rogers 32.1% are omitted. João Pedro 73.2% is the single largest exposure — GW4 EP 5.49 v Thiago 4.38 (−1.11 this GW), +1.27 / +0.43 on the 6-GW objective. | Correct the ownership figures in final.md. No transfer: every route is below the 2.0 gate on both readings (verified). Accepted, priced rank-variance risk. |
| F4 | MED | 1 | Dead bench in two of four slots: Dubravka p_start 0.04 (0 minutes, Kinsky starts) and Shaw 0.62 (75%, flagged today). A Raya non-start (4%) leaks ≈ 3.7 EP with no cover; a Shaw sub-in is worth 1.46. Six £4.5 GKs start every week (Kinsky, Leno, Petrović, Verbruggen, Scherpen, Rushworth; EP6 17–19). | Needs +0.5 the bank does not have, so it is a paired GW5 move or a wildcard item. Accept for GW4; the finalizer should list GK2 in the GW5 earmarks explicitly. |
| F5 | MED | 4 | MCI concentration on the derby: Haaland (C, ×2) + Ndiaye in the XI + Anderson on the bench, all at MUN (A), λ_att 1.80 (MCI's third-worst row in the window), P(CS) 0.25. MCI carries 16.0 of the 55.2 predicted (29%). Mbeumo (MUN) is the only hedge. | Ndiaye's DefCon term (4.13 of 25.40 EP6) is a floor independent of the scoreline; Haaland at 71.2% owned is rank-safe. Accept. |
| F6 | LOW | 8 | Captaincy on prior-only: Haaland 5.58 v Gabriel 5.28 — a 0.30 gap, inside the 0.5 band on the robustness reading. On blend the gap is 0.95 (6.00 v 5.05, both LOW → ×1.00). | Haaland stands: the optimizer's certainty mapping is applied to blend, and Haaland is also the low-variance rank pick. Vice Gabriel plays Sat 19:00, before MUN v MCI Sun 15:30 — the vice mechanism is unaffected by order. |
| F7 | LOW | 10 | 3xc earmark GW5 → GW9 buys +0.21 on Haaland's own row (6.75 v 6.54) for four extra GWs of injury/suspension exposure on a single player, and rests on BHA DEFW having moved 0.97 → 1.08 in two cycles. GW7 IPS(H) 6.81 is correctly rejected under C5 (banded). | Acceptable: GW9 follows the GW8 wildcard, which can be built around the TC. Re-test each cycle as the proposal commits; revert to GW5 only before the GW5 deadline. |
| F8 | LOW | 10 | Chip path is feasible (wildcard GW8, 3xc GW9, freehit GW16, bboost GW19; one chip per GW; freehit non-consecutive). Bench Boost sits on the last eligible GW with zero slack, and needs GK2 and DEF5 fixed first. | The GW8 wildcard is the repair point; re-evaluate the bboost earmark for GW17–18 once those fixtures firm. |
| F9 | LOW | 11 | Price bleed: Mbeumo, Ndiaye, Thiago and Shaw each fell 0.1 this event and keep net outflows of 220–260k. Sell value 99.4 likely 99.0–99.2 by GW5. No buy is proposed, so no timing issue this GW. | Relevant only through F2. |
| F10 | LOW | 2 | Flags: Shaw's 13:00 flag is in the 17:58 snapshot; no XI player carries news; Anderson's 23 Aug `news_added` at 100% is a stale-cleared flag, not a risk. Snapshot 18.5h old at the deadline (< 24h). Gakpo is not owned. | Friday/Saturday pressers precede a Sunday derby; the finalizer's `flags` gate covers ids 1, 4, 202, 229, 427, 237, 481, 68, 411, 106, 249, 497, 69, 445, 423. |
| F11 | LOW | 3 | team_value provenance: the relayed `my-team` total 99.6 equals the bootstrap now_cost sum (99.6), not the selling-price sum (99.4). STATE's 99.4 is the right figure. | Finalizer records which field `my-team` printed; out-of-remit row appended to docs/backlog.md. |
| F12 | LOW | 6 | Fixture myopia: none past the window. The EVE cliff (Tarkowski 3.64 / 3.36, Barry 4.17 / 3.28 at GW7–8) is inside the window, the GW7 XI already benches Barry, and GW10–12 rows for MCI (NFO(A), FUL(H), ARS(A)), ARS (HUL(H), NEW(A), MCI(H)) and BOU (IPS(A), NFO(H), FUL(A)) hold. Two FTs at GW5 plus the GW8 wildcard give a fix path. | None. |
| F13 | — | 7 | Hit justification: no hit taken. All four +4-to-+5 pairs except Cherki + Wissa flip sign on prior-only — reproduced. | PASS |
| F14 | — | 9 | Recency bias: none. Thiago is held on 2.30 xG / 0 goals (4 pts), Richards on 31 DefCon / 4 pts; Scott and Tavernier rank 2nd/3rd of the MIDs on prior-only as well as blend, so their hauls are not the basis. | PASS |

## Retro-correction compliance (C14, C15, C16 bind this cycle)

| C# | Check | Result |
|---|---|---|
| C14 | Every single and pair carries a prior-only reading; no hit whose sign flips | My own `fpl ep` rerun with `prior_weight: 1.0` reproduces every prior-only figure in §1–§2 to ±0.01. No hit proposed; no move clears 2.0 on both readings. COMPLIANT |
| C15 | Conditions (a), (b) = NO; C14 the only gate | Restructure pair scored +3.33 / −1.91, closed. COMPLIANT |
| C16 | Certainty multiplier on the captain only | §5 only; §4 and §6 use undiscounted EP. COMPLIANT |
| C5 | No TC on a promoted-club row; GW4 gate | GW4 fails (MUN(A) λ_att 1.80, third-worst of MCI's six); GW7 IPS(H) banded, rejected; GW9 band-free. COMPLIANT |
| C8 | Bench near-ties on DefCon share | Gaps 0.64 and 1.75, none ≤ 0.25. COMPLIANT |

## Suggestions ledger (checklist item 12)

Marker `Read data/suggestions.md through S2`. Open set recomputed: S1 and S2
have blank From GW (= next deadline = GW4 ≤ N) and blank Until GW; the latest
final.md (GW3) has no `## Suggestions` section, so nothing is closed → both
open, both need a row. Both present.

| S# | Row | Check |
|---|---|---|
| S1 | GW 4, standing | Reason states how the plan honours it (banked FT for a GW5 Anderson exit; Ndiaye half quantified — 266/270 minutes, EP6 25.40, best swap −0.07, which I reproduce). First cycle, so GW = 4 is right. PASS |
| S2 | GW 4, rejected | Carries a number: 62.8 EP/GW unconstrained ceiling (recomputed 62.83) v 56.4 plan mean. Infeasible = valid rejection. PASS |

No malformed rows; no S# above the marker. No finding.

## Accepted risks to carry into final.md

F1 (Barry/Anderson tie broken against the prior-only reading), F2 (GW5 pair is
price-fragile — not a commitment), F3 (template exposure: João Pedro 73.2%,
Calafiori 48.7%, B.Fernandes 44.0%, Szoboszlai 38.4%, Rogers 32.1% unheld),
F4 (dead GK2 and a 75% bench 15), F5 (MCI derby concentration under the
captain).
