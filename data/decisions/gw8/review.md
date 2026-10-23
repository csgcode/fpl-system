# GW8 Red-Team Review — WILDCARD proposal

Reviewed data/decisions/gw8/squad-proposal.md against data/analysis/gw8/*,
data/raw/gw8/bootstrap.json, data/decisions/gw7/final.md, the retro
corrections through gw7.md (C21 new) and data/suggestions.md (S1–S8).

**Verdict: REVISE** — one HIGH (F1). Everything else is MED or below and
can be carried as accepted risk if the revision does not absorb it.

## Reproduction

Every `objective` figure below is on the GW7-verified selling-price basis,
passed as `--sell` (the seven outgoing players at their GW7 sell prices,
the eight kept at theirs; Σ 98.7 + bank 0.4 = 99.1), so the bank is the
floor the proposal quotes, not the CLI's unverified now_cost 1.0.

```
objective --gw 8 --sell <GW7 prices> --bank 0.4 --chip wildcard --moves 1:385,497:597,229:566,423:332,124:12,94:127,106:464
plan: … — blend +9.800 prior +6.557; bank 0.5; verdict: PASS
```

Matches the proposal exactly. Prior-only EP files rebuilt with
`ep --prior-weight 1.0` for all four positions; the per-row figures cited
below come from them.

| Check | Result |
|---|---|
| Budget | kept 58.4 + buys 40.2 = 98.6 ≤ team_value 99.1; bank 0.5. Bank not double-counted. Every kept player's now_cost ≥ his GW7 sell price, so 99.1 is a true floor |
| Positions / clubs / formation | 2 GKP, 5 DEF, 5 MID, 3 FWD; ARS 2, BOU 2, LEE 2, rest 1; 5-3-2 legal |
| Minutes | XI p_start_gw[0] 0.93–0.96; bench Suzuki 0.95, Gomez 0.93, Barry 0.94, Saka 0.50 at slot 15. No dead bench |
| Flags | Saka d 50% thigh (news 21 Oct, fresh). Haaland a/100, Van Hecke a/100. Other 13 clean. Shaw (i, 0%) and Dubravka (p 0.03) both leave |
| Concentration | no club with > 2 attack-dependent players |
| Captain / vice | Haaland 5.798 is the top undiscounted single-GW EP, 0.718 clear. Vice Gabriel 5.080 v Mbeumo 4.932: inside 0.5, both p ≥ 0.85, higher EP holds |
| XI boundary | C20/C8 applied correctly: Barry 3.660 (DefCon 0.008) v Van Hecke 3.565 (0.190), 0.095 apart → Van Hecke starts |
| Chip path | wildcard GW8, 3xc GW9, freehit GW16, bboost GW19 — all inside the bootstrap set-1 windows (wildcard/freehit 2–19, bboost/3xc 1–19); no consecutive free hit; Haaland held for the 3xc; bench-boost bench now four playing rows |
| Ledger | S1–S5 verbatim; S6 standing(6) → followed(8), names the part not taken; S7 and S8 standing, GW 7 kept; no open S# without a row; none expired; marker S8, nothing above it |
| C12 | no GW8 XI row is a promoted-club fixture |

## Findings

### F1 — HIGH — The package keeps the one prior-sign-flipping component when an in-band alternative removes it

Tarkowski → Silva is +1.598 blend / **−1.959 prior-only**. Silva's blend
EP6 25.85 sits 3.98 above his prior-only 21.87, the largest form premium in
the DEF pool bar Thomas (COV): 630 PL minutes, `prior_source: league_mean`,
attack term 5.07 off xG90 0.123 / xA90 0.053 at £5.0m, 0.7% owned. The
proposal keeps him because "Calafiori does not fit the £99.1 floor with Van
Hecke and Richards kept". That is wrong: Calafiori fits when the GK2 slot
funds him.

```
--moves 1:385,497:496,229:8,423:332,124:12,94:127,106:464   (Kinsky for Suzuki, Calafiori for Silva)
plan: … — blend +9.537 prior +8.627; bank 0.0; verdict: PASS
  move Raya → Trafford: +0.042 / +0.045
  move Dubravka → Kinsky: +0.119 / +0.189
  move Tarkowski → Calafiori: +1.771 / +0.404
  move Shaw → Justin: +1.439 / +1.972
  move Groß → Saka: +5.878 / +4.626
  move Schade → Gomez: +0.141 / +0.029
  move Thiago → Wissa: +0.382 / +1.245
GW8 XI 4-3-3 54.506 (5-3-2 after the C20 tie-break, Van Hecke for Barry, as in the proposal)
```

Against plan C: **−0.263 blend, +2.070 prior-only**, no component with a
prior sign flip, and the Raya → Trafford move turns positive on both
readings. The 0.263 blend gap is inside the 0.5 band the proposal itself
uses; the proposal settled plan A v C (0.828 blend apart) on the prior-only
margin and uncertainty, so its own decider picks this package over C.
Side-effects, all tolerable: ARS goes to 3 (Gabriel, Calafiori, Saka —
legal; two of them share the ARS clean sheet), Calafiori is 54.3%-owned
template (fixes part of F3), Kinsky is a nailed £4.5m keeper (6/6 × 90, so
the bench-boost bench stays live), bank 0.0 on the floor basis — the
deadline is today 17:30 UTC and the overnight price run has already
happened, so nothing can move a price before the POST, and the true
`my-team` bank is ≥ 0.0 because 99.1 is a floor.

Secondary alternatives graded, for the optimizer's audit trail:

| Package | blend / prior | bank | Note |
|---|---|---|---|
| C (proposal) | +9.800 / +6.557 | 0.5 | Silva component −1.959 prior |
| **C with Calafiori + Kinsky** | **+9.537 / +8.627** | 0.0 | no sign flip; recommended |
| C with Hill (BOU 5.5) for Silva | +8.905 / +9.104 | 0.0 | same-club swap, no sign flip, −0.895 blend |
| C with Hill + Kinsky | +8.469 / +8.811 | 0.5 | keeps the 0.5 margin |
| C with Palmer for Saka | +5.626 / +7.293 | 0.3 | FAILS the 6.0 blend gate — Saka stands (see F2) |
| C with Calvert-Lewin for Wissa | +9.527 / +5.102 | 0.5 | see F4 |

Concrete alternative: regrade the wildcard with
`--moves 1:385,497:496,229:8,423:332,124:12,94:127,106:464`; if the
optimizer still prefers C, the proposal must say which rule beats its own
A-v-C decider at a 0.263 blend gap.

### F2 — MED — £9.6m on a 50% flag with a guessed ramp (accepted risk)

Saka's EP6 28.64 prices p_start_gw 0.50 / 0.85 / 0.92…; the analyst calls
the GW9+ ramp "a guess". Sensitivity: holding GW9 at 0.50 instead of 0.85
removes about 1.7 EP6, leaving the package at roughly +8.1 blend, still
over the 6.0 gate, and Saka still above Palmer (25.11) on blend. The
flag-free alternative, Palmer, fails the chip gate as a package (+5.626).
So the rule holds Saka; the risk is a second missed week on a £9.6m bench
row with the wildcard spent. The freshness gate re-checks him before the
POST; if he goes `i`, REOPEN.

### F3 — MED — Template exposure widens deliberately

Of the seven players owned by > 30%, the proposal holds Haaland only. It
sells two of them (Raya 44.9%, Groß 45.8%) and stays off João Pedro 73.3%,
Calafiori 54.3%, Rogers 48.8%, De Cuyper 41.6%, Cherki 38.5%. Every one of
those is an EP decision, but the rank-volatility cost is a João Pedro or
Calafiori haul landing in a week we field 0.7%-owned Silva. F1's alternative
brings Calafiori in; the rest is accepted differential risk and should be
named as such in final.md.

### F4 — MED — S8 reason does not say how the Wissa v Calvert-Lewin choice honours it

S8 asks, when two moves are close on EP, for the steadier points record at
the more consistent club. Thiago → Wissa and Thiago → Calvert-Lewin are
0.1 EP6 apart (25.32 v 25.42) and 0.273 blend apart as packages — inside
the 0.5 band. Calvert-Lewin: 33 pts, form 5.5, LEE ATT rank 11 / CS rank 5.
Wissa: 18 pts, form 1.5, NEW ATT rank 18 / CS rank 19, mean FDR 3.50, and
NEW turns hard from GW11 (ARS (H), BHA (A), MUN (H); his GW11 row 3.79).
S8 points to Calvert-Lewin; the plan takes Wissa on the prior-only margin
(+1.245 v −0.210 as components, +1.455 as packages), which is a legitimate
decider — but the S8 reason says "Wissa, unbroken-streak starter" and
nothing about this choice. Either state the prior-only decider in the S8
reason or switch (LEE would go to 3, legal). The finalizer carries the
ledger verbatim, so the text can only change in the revision F1 triggers.

### F5 — MED — S7 reason silent on buying two fallers

S7 is a move-away-from-fallers policy. The plan sells three fallers and
says so, but also buys the pool's two largest outflows this event: Saka
(27k in / 357k out) and Wissa (8k in / 254k out). Both will most likely
drop 0.1 tonight, after the deadline, so the squad starts the GW holding
two fallers at −0.2m team value. Immaterial against +9.8 EP6, but the S7
reason should either say S7 is read as a sell-side policy or accept the
−0.2 explicitly.

### F6 — LOW — Raya → Trafford loses EP on both readings

−0.104 / −0.110: a pure funding move that also sells a 44.9%-owned keeper.
Under the wildcard it costs no transfer; in F1's alternative it turns
+0.042 / +0.045 because Kinsky, not Suzuki, is the pair.

### F7 — LOW — Price risk

No action possible: the deadline is today, the overnight run has passed.
Expected: Saka and Wissa −0.1 each tonight; Groß (254k in) sold before a
rise; Trafford, Justin, Gomez, Mbeumo, Tavernier are net risers and held or
bought. Net ≈ −0.2m, nothing in the plan hinges on it.

### F8 — LOW — Penders p_start 0.95 contrary to C21 (no squad effect)

Penders (CHE, 560) has 15 PL minutes (0,0,0,0,0,0,15) and p_start_gw[0]
0.95 as sole cover for Martinez (i, head). C21 reserves ≥ 0.93 for an
unbroken three-round start streak. The analyst self-escalated it in
players-GKP.md. He is in no plan graded here, so nothing in this proposal
rests on it; recorded for the retro, and a tool guard is proposed in the
backlog.

### F9 — LOW — Execution: credentials expired at step 1

meta.md: `auth-check → FAIL (session expired, refresh token does not
exist)`. The wildcard chip rides the make-transfers POST. If the session is
not re-captured before 17:30 UTC, the user applies seven transfers by hand:
activate the wildcard **before** confirming the transfers, otherwise the
site books six of them as −24. The finalizer's `my-team` budget check will
also fail; the proposal's floor basis makes that safe.

### F10 — LOW — Fixture decay after the window

SUN (E.Le Fée) and NEW (Wissa) turn hard from GW11; BHA (Gomez) turns easy.
Two free transfers at GW9 cover it. No action.

## Verdict

**REVISE** — F1. Re-run the optimizer with this review as input, grading
`--moves 1:385,497:496,229:8,423:332,124:12,94:127,106:464` (and the Hill
variants) on the floor sell basis. Whatever package it settles on, F2, F3
and F5 carry into final.md as accepted risks, and F4 is resolved by the
revised ledger text or a Calvert-Lewin switch.
