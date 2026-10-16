# GW7 Red-Team Review (no-chip plan)

Proposal: data/decisions/gw7/squad-proposal.md — no chip (user directive),
one free transfer Thiaw → Van Hecke, 3-4-3, Haaland (C), Mbeumo (V), bank
0.4, predicted GW7 54.855. The wildcard proposal and its review are archived
as squad-proposal.v1.md and review.v1.md; the no-chip constraint is taken as
fixed and not graded.

**Verdict: APPROVE.** No HIGH finding. Two MED findings (F1, F2) are
disclosure gaps the finalizer can close in final.md text — same XI, same
transfer, no revision loop.

## Independent recomputation

| Check | Result |
|---|---|
| Budget | GW6 sell column + Gabriel 8.0 → 7.9 = 98.8; + bank 0.3 = 99.1, equal to STATE `team_value` and the relayed `my-team` figure. Sell 5.0, buy 4.9, bank 0.4; squad sell sum 98.7; `team_value` 99.1 = 98.7 + 0.4. Bank not double-counted |
| Positions / clubs / formation | 2 GKP, 5 DEF, 5 MID, 3 FWD. ARS 2, TOT 2 (Van Hecke, Dubravka), EVE 2, MUN 2, BRE 2, others 1. XI 3-4-3 (1 GK, 3 DEF, 4 MID, 3 FWD), captain and vice both in the XI, bench 12–15 with GK at 12 |
| `objective` reproduction | `--sell <GW6 sells, Gabriel 7.9> --bank 0.3 --free-transfers 1 --moves 445:112`: baseline 318.730 / 313.869, plan +2.223 / +1.214, greedy reference the same move, verdict PASS, XI 54.855, captain list and bench identical to the proposal. `--moves none` FAILs (further free move passes); `94:403` FAILs the reference by 0.218; `445:112,94:403` FAILs the hit gate — every figure in the proposal's plan table matches |
| Prior-only view | `ep --prior-weight 1.0 --position DEF` (scratch): Van Hecke 23.25 v Thiaw 21.45 — the move is +1.80 on prior EP6 and Van Hecke is the top ≤ £4.9m DEF on both readings. No hit is taken, so C14's sign test is satisfied by the free gate alone |
| STATE / plan | `final-check --proposal` PASS P1–P3. `plan --from-final <proposal>` compiles: 1 transfer by picks-diff, chip none, 1 FT banked for GW8, four chip_plan rows inside their bootstrap windows |
| Ledger | S1–S5 byte-identical to the GW6 ledger; S6 keeps GW 6 as a re-affirmed `standing`; S7 and S8 first disposed at GW 7; marker `through S8` equals the file's highest S# |
| Flags | Bootstrap fetched 2026-10-16 15:35 UTC. All XI `a`; Schade d 75 (news 10 Oct), Shaw d 75 (news 12 Oct) both benched; Van Hecke `chance 100`, news cleared 30 Sep |
| Auth | runs.jsonl: auth-check FAIL 15:37 UTC, PASS 15:41 UTC after re-capture. Deadline 2026-10-17 10:00 UTC; writes are possible today |

## Findings

| # | Sev | Item | Finding | Alternative |
|---|---|---|---|---|
| F1 | MED | 7, 3, C12 | The free-gate pass (+2.223 v 2.0, margin 0.223) sits inside the promoted-club band. Van Hecke's per-GW lead over Thiaw is +0.81 (GW7 COV (H) ±, P(CS) 0.41), +0.25, +0.28, +0.08, +1.21 (GW11 IPS (H) ±, P(CS) 0.34), +0.65: 2.02 of the 3.27 EP6 lead sits on the two banded rows, and Thiaw's six rows are all unbanded. At the band's −15pp edge each banded row loses about 4 × 0.15 × 0.92 ≈ 0.55 EP on the clean-sheet term alone (before goals-conceded and bonus), taking the marginal to roughly +1.1 — below the gate; at the +15pp edge it is roughly +3.3. C12 keeps the central estimate, so the move is legal as graded, and his largest term is appearance (11.04), not a banded P(CS). R4 names GW7 only | No move changes within the rule: the only other gate-passing single (Schade → Sávio) buys the same two TOT rows on the attack side. Widen R4 to name GW11 and state that the gate pass is band-sensitive (fails at the band's low edge, clears at its centre and high edge) |
| F2 | MED | 12 (S7) | S7's reason is silent on Schade, the squad's largest faller (net −154.6k this event, d 75%, 14.4% owned) and the one faller with a gate-passing move away: Schade → Sávio +2.005 / +3.634, 0.218 behind plan A on blend — inside S7's "small difference" band — and three times ahead on prior-only. The reason's "none within 0.5 of plan A, so no in-band tie to settle" holds only for the six names S7 listed on 9 Oct; the row's policy is "players whose price is falling", and Schade was bought after it was written. The move loses to the transfer rule's greedy reference (tolerance 0.05), which S7 cannot override — but the reason must say so. S7 and S8 pull apart on this exact choice (S7 → sell Schade, S8 → Van Hecke over Sávio); the plan takes S8's side without naming it under S7 | Add to the S7 reason: "Schade (net −154.6k, d 75%) is the squad's largest faller; Schade → Sávio +2.005 / +3.634 is inside the band (0.218 behind plan A) but fails the greedy reference, which the transfer rule owns; S8 prefers Van Hecke on the same pair" |
| F3 | LOW | 11, 3 | Price exposure after the POST is covered: Van Hecke net +24.1k, Thiaw −15.8k; a 0.1 rise on the buy, a 0.1 fall on the sell, or both leave the bank at 0.3 / 0.3 / 0.2, never below 0.2. Holds at fall risk ahead of a GW8 wildcard: Schade −154.6k, Gabriel −94.1k (already −0.1 this event, sell 7.9 → 7.8 on another), Shaw −62.7k, Dubravka −21.0k — each fall takes 0.1 off `team_value` | POST today before the overnight price run (auth PASS 15:41 UTC); no fallback transfer needed at bank 0.4 |
| F4 | LOW | 8 | Captain Haaland 6.579 v Van Hecke 4.596, gap 1.98, outside the band. Vice: Van Hecke 4.596 / Barry 4.582 / Mbeumo 4.572 within 0.024, all `p_start_gw[0]` ≥ 0.85, so the spec's tiebreak does not separate them; S8 breaking the tie to Mbeumo is permitted (a row may settle a tie inside 0.5 single-GW EP). The vice pays only on a Haaland non-start (p 0.93) | None |
| F5 | LOW | 1, 10 | GK2 dead (Dubravka 0.03); outfield cover is Richards alone (Schade 0.65, Shaw 0.70). Chip path intact: wildcard GW8 and freehit GW16 inside 2–19, 3xc GW9 on Haaland v BHA (H) λ 2.09 unbanded (C5), bboost GW19 on the window's last GW — no slack, and it needs GK2 repaired first. One chip per GW, no consecutive FH, no 3xc target sold | Accept (R1, R2). Keep GK2 as the first GW8 repair whether or not the wildcard plays |
| F6 | LOW | 5 | Template unheld > 30%: João Pedro 70.9, Calafiori 52.7, Rogers 45.9, De Cuyper 37.3, Cherki 34.0, B.Fernandes 33.0; held Haaland 75.7, Raya 43.7, Groß 41.3 — R3 lists them. Tarkowski → Calafiori +1.217 / −0.034 fails both the blend floor and the sign test | Accept (R3) |
| F7 | LOW | 6, 4 | No decay trap: TOT GW13–16 FUL (H) ARS (H) HUL (A) LIV (A), TOT swing −0.46 Σλ_att / −0.05 ΣP(CS) and CS rank 4; NEW (sold) turns hard from GW10 (−0.70 / −0.14). Concentration: no club with more than two attack-dependent picks (BRE's Schade is benched; TOT's second is the dead GK) | None |
| F8 | LOW | 9 | Not a recency buy: Van Hecke 8, 8, 6, 3 in R3–R6, but the move is scored on EP with equal p_start (0.92 both) and holds on prior-only (+1.80 EP6); he is the top ≤ £4.9m DEF on both readings. S8's points-record tiebreak is the user's steer, applied only inside the band | None |
| F9 | LOW | 7, 12 (S8) | Plan B, Schade → Sávio (+2.005 / +3.634): fails the greedy reference by 0.218 under a 0.05 tolerance, leaves bank 0.0 (one-tick exposure on either side), sells the 75%-flagged biggest faller and buys TOT attack rows banded at the same two fixtures as F1. The rule picks A; the tolerance itself is already a GW7 A4 backlog row | None in-cycle |
| F10 | LOW | 12 | Ledger mechanics: S6 reason names how the plan honours it (chip null by directive, wildcard re-timed to GW8 inside the row's window, closes at GW8 either way); S8 reason states the band it applies (package delta, 0.5) and the vice tiebreak. No open S# without a row, no closed row altered, no expired or withdrawn row open, no From GW > 7 row, no deferral, no `followed` delta to reproduce. Malformed: none | None |
| F11 | LOW | 2 | Flags current (see recomputation). Schade's 10 Oct news is six days old at a 75% tag; BRE v LIV (H) GW7. The finalizer's `flags --ids` gate re-reads before final.md | None |

## Suggestions ledger (item 12)

Open set at GW7 from the GW6 ledger: S6 (standing, From 6, Until 8), S7
(From 7, no prior row), S8 (From 7, no prior row). Marker `through S8`
equals the file's highest S#.

| S# | Expected | Ledger | Check |
|---|---|---|---|
| S1–S5 | closed, carried verbatim | byte-identical to GW6 | PASS |
| S6 | open → re-affirmed or disposed | standing, GW 6 (kept) | PASS — honoured by chip_plan wildcard GW8; closes at the GW8 cycle |
| S7 | open → row | standing, GW 7 | PASS, MED F2 — reason silent on Schade, the faller with the in-band move |
| S8 | open → row | standing, GW 7 | PASS — band defined, Van Hecke v Sávio and the vice tie both stated |

## Verdict

**APPROVE.** Zero HIGH. The transfer, XI, captain, bench order, chip plan and
STATE all reproduce from code. F1 and F2 are text changes to R4 and the S7
reason; the finalizer can make both without a revision loop. The transfer
must be POSTed today, before the overnight price run, so the sell price graded
here is the one applied.
