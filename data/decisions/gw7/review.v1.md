# GW7 Red-Team Review

Proposal: data/decisions/gw7/squad-proposal.md — Set-1 wildcard, eight
transfers, 3-4-3, Haaland (C), Saka (V), bank 0.0, predicted GW7 57.492.

**Verdict: APPROVE.** No HIGH finding. Five MED findings (F1–F5) for the
finalizer to take or carry as accepted risks; F1 + F2 together are one
concrete change the finalizer can make without a revision loop.

## Independent recomputation

| Check | Result |
|---|---|
| Budget | Selling prices GW6 final + Gabriel 8.0 → 7.9 = 98.8; + bank 0.3 = 99.1, equal to STATE `team_value` and the relayed `my-team` figure. Sells 46.3, buys 46.6, bank 0.0. Squad at proposal prices sums to 99.1. Bank not double-counted |
| Positions / clubs / formation | 2 GKP, 5 DEF, 5 MID, 3 FWD. TOT 3 (Van Hecke, Sávio, Dubravka), ARS 2, LEE 2, others 1. XI 3-4-3, captain and vice both in the XI, bench 12–15 in EP order |
| `objective` reproduction | `--chip wildcard --moves 1:385,229:112,445:566,68:12,94:403,106:569,202:588,423:332` prints blend +16.239 / prior +3.979, greedy reference Thiaw → Van Hecke +2.223 / +1.214, verdict PASS, GW7 XI 57.492 — every figure in the proposal matches |
| Prior-only view | `ep --prior-weight 1.0` per position (scratch). Squad prior EP6: Silva 21.28 (blend 25.39), Barry 21.88 (25.38), Khalaili 19.02 (22.31), Saka 29.21 (32.10), Sávio 27.26 (25.78), Gabriel 27.40 (26.27) |
| STATE / plan | `final-check --proposal` PASS P1–P3. `plan --from-final <proposal>` compiles: 8 transfers by picks-diff, chip wildcard, 2 FT banked for GW8, windows per bootstrap |
| Flags | Bootstrap fetched 2026-10-16 15:35 UTC. All 15 picks `a`; Schade (d 75) and Shaw (d 75) both sold; Van Hecke, Sávio, Khalaili carry `chance 100` with cleared news |
| Auth | runs.jsonl: auth-check FAIL 15:37 UTC, PASS 15:41 UTC after re-capture. Writes are possible today |

## Findings

| # | Sev | Item | Finding | Alternative |
|---|---|---|---|---|
| F1 | MED | 3, 11 | Bank 0.0 exposure is two-sided; R4 names only in-side rises. Sell-side falls also break the package: Schade net −154.6k this event (d 75%), Shaw −62.7k, Thiago −34.5k; Gabriel (held) −94.1k. In-side rises: Justin +27.6k on 1.8% owned, Van Hecke +24.1k, Sávio +20.8k, Trafford +8.8k. One 0.1 move on either side and `make-transfers` refuses | POST today, before the ~01:30 UTC 17 Oct price run (deadline 10:00 UTC; auth PASS 15:41 UTC). Pre-empt with F2 for a 0.1 buffer. Widen R4 to sell-side falls |
| F2 | MED | 7, 12 | Richards → Khalaili is +0.247 blend / −1.713 prior — a sign flip taken because the wildcard makes it free, not because it is wanted. Dropping it grades +15.992 / +5.692 (−0.247 blend, +1.713 prior), bank 0.1, seven POSTs, and Richards' GW7 bench EP 3.089 exceeds Khalaili's 3.074. S7's "falling price" basis for Richards is stale (net −406 this event, no change) and S8's "nailed starter" test favours Richards (6/6 × 90) over Khalaili (5 starts) | Drop the pair: keep Richards at slot 15, bank 0.1. No revision loop needed — same XI, same captain, one fewer transfer |
| F3 | MED | 5 | Template exposure understated. Unheld > 30%: João Pedro 70.9, Calafiori 52.7 (net +144.7k this event, the pool's fastest riser), Rogers 45.9, Raya 43.7 (sold here), De Cuyper 37.3, Cherki 34.0, B.Fernandes 33.0. After the wildcard the squad holds 2 of 9 (Haaland, Groß). R3 names two. The wildcard is the free moment to take cover; V3 (Calafiori in, Gabriel out) is −0.40 blend / +1.60 prior | Widen R3 to the full list and state the differential position as deliberate; or take V3 |
| F4 | MED | 12 (S7) | S7's reason does not address Gabriel, the squad's live faller (−0.1 this event, net −94.1k, another fall takes sell 7.9 → 7.8), held on a wildcard where selling is free. S7 (sell fallers when EP is close) and S8 (keep the consistent-club player) pull opposite ways on him; the proposal picks S8 without saying so under S7. V3 is inside the 0.5 band (−0.40) and +1.60 prior | S7 reason names Gabriel and why S8 wins (ARS CS rank 1, ΣP(CS) 2.20, GW10 HUL(H) 0.50, 3 returns in 6); or V3 |
| F5 | MED | 12 (S8) | Three of eight buys are the profile S8 steers away from: Silva 13 pts / 0 returns, Sávio 10 pts / 330', Gonzalo 16 pts / 1 return. The ledger's defence ("no steadier player within 0.5 EP6 at their price") applies the band to the `objective` package delta, not the row EP6: Calvert-Lewin v Gonzalo is −0.41 on EP6 (inside the band) but −0.96 on the package; CL 24 pts, pens #1, prior 25.70 v 23.74. Variant drop-F2 + CL for Gonzalo grades +15.031 / +7.583, bank 0.2 (−1.21 blend, +3.60 prior). Silva and Sávio have no rival within 0.5 on either band | State the band definition in the S8 reason (package delta, 0.5) and the CL figures; or take CL for Gonzalo |
| F6 | LOW | 1, 10 | GK2 dead through the wildcard (Dubravka 0.03). Bench Boost sits on GW19, the window's last GW — no slack — and needs a free transfer on GK2 first. V2 (Trafford + Kelleher) −0.27 / −2.1 is correctly rejected; a £4.5m playing keeper needs a DEF downgrade | Accept (R1). Name GK2 as the first GW8 FT in final.md |
| F7 | LOW | 9 | Silva is the squad's largest blend-over-prior row (+4.11); prior-only ranks him 6th among ≤ £5.0m DEF, below Richards, Justin, Thiaw. Thiaw → Silva +3.066 / −0.556. Once Van Hecke is taken no ≤ £5.0m DEF beats him on both readings | Accept (R2) |
| F8 | LOW | 6, C12 | Van Hecke's GW7 4.596 (his best row by 0.34; 4th in the captain list) leans on TOT v COV (H) P(CS) 0.41, banded. The buy stands on EP6: top ≤ £4.9m DEF on both readings (23.47 / 23.25). GW13–16: TOT FUL(H) ARS(H) HUL(A) LIV(A); LEE MCI(A) IPS(H) LIV(A) FUL(H); MCI LEE(H) BRE(A) CHE(H) HUL(H); 2 FT at GW8 and accruing — no decay trap | None |
| F9 | LOW | 10 | Chip path intact: wildcard GW7 (window 2–19), 3xc GW9 on Haaland v BHA (H) λ 2.09 unbanded (ep_gw 6.20), freehit GW16, bboost GW19; one chip per GW, no consecutive FH, Haaland held. `chips_used: []` with `chip: wildcard` compiles; GW8 must record it | None |
| F10 | LOW | 2 | Flags current (see recomputation). Khalaili's `news_added` 2026-10-04 is a cleared knock; 90 × 4 R3–R6 | None |
| F11 | LOW | 8 | Captain Haaland 6.579 v Saka 4.878, gap 1.70, outside the band; vice Saka second on EP, different fixture | None |
| F12 | LOW | 4 | Concentration: ARS 2 (Gabriel, Saka), TOT 2 attack-side (Van Hecke, Sávio), LEE GK + DEF. No club carries > 2 attack-dependent picks | None |

Alternative packages graded on the same `objective` command (all PASS the
chip gate):

| Variant | Blend / prior | Bank |
|---|---|---|
| Proposal | +16.239 / +3.979 | 0.0 |
| Drop Richards → Khalaili (F2) | +15.992 / +5.692 | 0.1 |
| F2 + Calvert-Lewin for Gonzalo (F5) | +15.031 / +7.583 | 0.2 |
| Calvert-Lewin for Gonzalo only | +15.278 / +5.920 | 0.1 |
| Muharemović for Silva | +14.439 / +4.118 | 0.0 |
| Stach for Sávio | +14.962 / −0.082 — FAIL (prior < 0) | 0.5 |

## Suggestions ledger (item 12)

Marker `through S8` equals the file's highest S#. Open set at GW7 from the
GW6 ledger: S6 (standing, From 6, Until 8), S7 (From 7), S8 (From 7).

| S# | Expected | Ledger | Check |
|---|---|---|---|
| S1–S5 | closed, carried verbatim | identical to GW6 | PASS |
| S6 | open → disposed | followed, GW 7 | PASS — single-choice steer done in part, reason names what was not taken (60 per GW); EP6 delta +16.239 reproduced exactly |
| S7 | open → row | standing, GW 7 | PASS, MED F4 — reason silent on Gabriel |
| S8 | open → row | standing, GW 7 | PASS, MED F5 — band definition unstated |

No open S# without a row, no closed row altered, no expired or withdrawn
row left open, no From GW > 7 row, no stale deferral, no unreproducible
`followed` delta. Malformed: none.

## Verdict

**APPROVE.** Zero HIGH. The one change worth making before the POST is F2
(drop Richards → Khalaili: +1.713 prior, −0.247 blend, 0.1 bank buffer
against F1). F3–F5 are disclosure gaps in the ledger and R3 unless the
finalizer takes the named alternative. The transfers must be POSTed today,
before the overnight price run, or the fallback chain in the proposal
applies.
