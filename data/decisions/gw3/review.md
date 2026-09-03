# GW3 Red-Team Review — `squad-proposal.md`

Reviewed adversarially against `data/analysis/gw3/*`, `data/raw/gw3/players-slim.csv`
+ bootstrap `chips`/`events`, `data/retro/gw{1,2}.md`, both calibration ledgers and
the GW2 STATE block. Every number below is recomputed, not copied.

## Verdict summary

| # | Severity | Finding | Action |
|---|---|---|---|
| 1 | MED | GW4 restructure decision rule is not recency-robust: on prior-only attack rates the Isak + B.Fernandes move is **−1.69 gross**, not +9.74; both stated GW4 conditions would fire it anyway | finalizer rewrites the GW4 earmark with a third condition (below) |
| 2 | MED | Barry rise window: net +75k in-event at 4.5% owned; one price-change night before the deadline | apply Kusi-Asare → Barry before ~01:30 UTC 4 Sep; fallback (bank FT) stands |
| 3 | MED | Template: four >30%-owned players unheld (João Pedro 69.7, B.Fernandes 48.6, Calafiori 43.9, Szoboszlai 41.4) | accepted risk, priced; João Pedro rising +0.1/event |
| 4 | MED | MCI at the 3-cap with the captain on the same fixture: 4 XI shares on MCI v COV, P(MCI blank) 8.9% central / 12.8% at band floor | accepted; the cap block on Guéhi/Cherki is wildcard material |
| 5 | LOW | EVE v MUN carries Tarkowski, Barry, Mbeumo (V) and Shaw (bench) | internal hedge, no action |
| 6 | LOW | Dead GK2 leaks ≈ 0.18 EP/GW (5% Raya non-start × 3.6) | repair queued behind the FWD fix; needs +0.5 the bank lacks |
| 7 | LOW | Sell-value drift: Mbeumo −491k, Gabriel −217k, Ndiaye −213k, Shaw −209k, Thiago −192k net out this event | up to −0.5 team value; no GW3 selection impact |
| 8 | LOW | If the restructure ever proceeds, the TC "GW8 BOU(H)" alternative collides with the GW8 wildcard earmark (one chip per GW) | GW6 TOT(H) is the only legal Fernandes TC slot under the current chip_plan |
| 9 | LOW | Barry/Scott boundary (0.36) and Mbeumo/Thiago vice (0.17) both flip on prior-only rates | inside the model's own estimate; log for the GW4 C8/LOW-4 verdicts |

No HIGH. **Verdict: APPROVE** (line at the end).

## Constraint check — recomputed from `picks:` + raw prices

| Check | Result |
|---|---|
| Σ price (15) | 10.0 GK + 28.5 DEF + 32.4 MID + 29.0 FWD = **99.9** |
| Funding | pre-transfer sell 98.9 + bank 1.0 = 99.9 → bank after **0.0** ✓ |
| Positions | 2 GKP / 5 DEF / 5 MID / 3 FWD ✓ |
| Clubs | MCI 3 (Haaland, Anderson, **Ndiaye — MCI in the GW3 snapshot**), ARS 2, EVE 2, MUN 2, BOU 2, CRY/BRE/TOT/NEW 1 — max 3 ✓ |
| Formation (slots 1–11) | 1 GK / 3 DEF / 4 MID / 3 FWD ✓; slot 12 = Dubravka (GKP) ✓ |
| Captain / vice | Haaland slot 9, Mbeumo slot 5 — both XI, exactly one each ✓ |
| XI EP GW3 | Σ 50.104 + Haaland 6.388 = **56.49** ✓ |
| 6-GW horizon | best legal XI + captain per GW = **337.04** (base squad 335.20) ✓ |
| Flags | all 16 ids `status a`, `news` blank, `chance_of_playing` null except Anderson 100 (added 23 Aug) ✓ |
| Snapshot | fetched 2026-09-03T17:38Z; deadline 2026-09-04T17:30Z — inside 24h ✓ |
| Chip windows | wildcard 2–19, freehit 2–19, bboost 1–19, 3xc 1–19 (bootstrap); GW5/8/16/19 earmarks all in-window, one per GW ✓ |
| STATE block | `chip: null` and `chip_plan` emitted (C11) ✓; 15 `picks:` lines ✓; `free_transfers_banked: 1` = FTs at the GW4 deadline ✓ |

The proposal's arithmetic is correct throughout.

## Checklist findings

### 1. Minutes risk — clear
No starter below p_start 0.88; Shaw (0.85, MED) is bench 3. All `p_start_gw`
vectors are flat, so the scalar reads are the per-GW reads. Dubravka 0.05 is the
known dead slot (finding 6). Barry's 0.88 rests on EVE having no other
registered forward: the bootstrap lists Beto (`status u`, sold) and Barry only.
The escalation is confirmed, not assumed.

### 2. Flags — clear
See table. Anderson's `cop 100` is a cleared flag, not a live one; GW2 recorded
the baseline and a re-downgrade would diff as REOPEN.

### 7 + 9. The deferred −4, attacked both ways (MED-1)

**Way A — "make it now".** The pooled GW1–2 ledger already answers the
optimizer's condition (a):

| ≥ £8.0m player | GW1 error | GW2 error | Mean / appearance |
|---|---:|---:|---:|
| Haaland | −4.31 | +7.68 | **+1.69** |
| B.Fernandes | −3.66 | +17.34 | **+6.84** |
| Isak | −2.41 | +3.36 | +0.48 |

The band's under-prediction is concentrated in **Fernandes**, not Haaland — one
23-point round. So "not concentrated in Haaland" is already true and cannot be
what protects us at GW4. If the trade were sound, waiting costs +1.10 (GW3) and
gains nothing the ledger does not already show. Fundability at GW4 is fine
(Isak −34k net, Fernandes +53k at 48.6% — neither rising).

**Way B — "it should not be made at GW4 either".** Back out each player's prior
rate from the model's own blend (`rate = w·prior + (1−w)·current`, w = 0.769 at
180'), rescale the attack term, rerun the horizon:

| Player | Blend xg90 / xa90 | Prior-only xg90 / xa90 | Attack term | EP6 |
|---|---|---|---:|---:|
| B.Fernandes | 0.47 / 0.34 | 0.296 / 0.331 | 18.0 → 13.2 | 38.06 → **33.26** |
| Haaland | 0.727 / 0.063 | 0.735 / 0.079 | 18.23 → 18.7 | 36.40 → **36.87** |
| Isak | 0.687 / 0.072 | 0.581 / 0.092 | 14.99 → 13.2 | 31.04 → 29.20 |

| Rates | Base Σ6 | Isak + Fernandes | Gross | Net of −4 |
|---|---:|---:|---:|---:|
| blended (model) | 337.04 | 346.78 | +9.74 | +5.74 |
| prior-only attack | 331.92 | 330.22 | **−1.69** | **−5.69** |

The whole +9.74 is the two-round tilt. Fernandes' "outright lead" over Haaland
reverses to a 3.6-point deficit once his 1.05 xG/90 fortnight (prior 0.30) is
removed. Condition (b) — "lead survives round 3" — is mechanical: w_prior only
moves 0.769 → 0.69 at 270', so one ordinary game cannot unwind a 23-point one.
**As written, both GW4 conditions fire the trade on a recency artefact.** That is
the LOW-4 pattern the retro assigned to the GW4 verdict, and it is worth +5.74 on
paper precisely because the paper is the outlier.

Way A fails; the deferral is right. Way B lands: the decision *rule* is the
defect, not the deferral. **Concrete fix for final.md §GW4 earmarks:** add
condition (c) — *the restructure proceeds only if its gross clears ≥ 6 with the
attack terms recomputed on prior-only rates (current-season component removed);
today that figure is −1.69*. Conditions (a) and (b) alone are not a gate.

Rank variance, priced as asked: Haaland 71.2% owned and captained by most of
that; selling him is the season's largest variance decision. It does not change
the EV verdict, but on a trade whose EV sign flips under a robustness check,
variance breaks the tie toward holding.

Why MED, not HIGH: nothing in GW3's executed decision changes. The fix is a
sentence in the GW4 earmark, which the GW4 cycle re-derives anyway; a revision
loop would re-run the optimizer to change commentary.

### 3. Constraints — verified (table above).

### 4. Concentration (MED-4, LOW-5)
MCI v COV: Haaland (C, attack 50% of EP6), Ndiaye (attack 30%), Anderson (DefCon
27%, attack 20%) — two attack-dependent plus the captain double. P(MCI 0 goals)
= e^−2.42 = 8.9%; at the band floor (λ 2.05) 12.8%. Anderson's and Ndiaye's
DefCon terms are the floor. The cap block on Guéhi (30.37, 2nd DEF) and Cherki
(30.68) is structural and correctly routed to the GW8 wildcard.
EVE v MUN: Tarkowski + Barry (EVE) v Mbeumo (V) + Shaw (bench). A Mbeumo goal
costs Tarkowski's CS, which is 5.11/23.55 of his EP6 at P(CS) 0.185 — a small
hedge, not a stack.

### 5. Template (MED-3)
Unheld >30%: João Pedro 69.7, B.Fernandes 48.6, Calafiori 43.9, Szoboszlai
41.4 — ≈ 204pp combined. Held >30%: Haaland 71.2, Raya 37.7 (Mbeumo 29.1,
Gabriel 26.1 just under). João Pedro is the one that bites: 70% of the field
gains when he hauls. The model prefers Thiago this GW by 1.03 (SUN(H) 5.10 v
ARS(A) 4.07) and JP by 0.75 over six; on prior-only rates JP 27.88 v Thiago's
blend 29.13 — Thiago's hold is not a recency call. JP is +0.1 this event with
+243k net, so the eventual swap gets ≈ 0.1 dearer per week deferred. Accepted
risk; MED-E verdict stays with GW4 as the retro scheduled.

### 6. Fixture myopia — LOW
GW9 LIV v ARS (Raya/Gabriel), NEW v EVE (Tarkowski, Barry, Thiaw) are the first
post-window hits; the GW8 wildcard earmark covers them, and the FT count at GW9
is 1 either way.

### 8. Captaincy — clear
Haaland 6.39 v Mbeumo 5.27 (both LOW × 1.00): gap 1.12 > 0.5, no safer pick in
range. At COV's band floor Haaland ≈ 5.9, still 0.6 clear. Vice Mbeumo v Thiago
5.10 is inside 0.17 and flips on prior-only rates (Mbeumo 4.5 v Thiago ≈ 5.0);
fires only on a Haaland non-start (~7%), expected cost < 0.05. Note only.

### 9. Recency — Barry passes, the restructure does not
Barry prior-only EP6 22.10 (attack 12.1 → 8.8) still beats every ≤ £5.5m
alternative (McBurnie 19.43 HIGH, all rows banded) and the 0 he replaces; his
p_start driver is Beto's sale, not his points. De Cuyper (+514k net, already
+0.1, likely 4.8 tonight) correctly rejected on sequencing. The Barry/Scott XI
boundary (0.36) narrows to −0.19 prior-only and would then go to Scott on the C8
DefCon share (22% v 1%); the model's blend is the system's estimate, so Barry
starts — logged as the third C8 observation.

### 10. Chip path — clear
All four set-1 chips have in-window earmarks (3xc GW5, wildcard GW8, freehit
GW16, bboost GW19), one per GW, freehit non-consecutive trivially. Nothing sold
this GW is a chip target. If the restructure ever proceeds, the proposal's
"Fernandes GW8 BOU(H) 6.80" TC option is illegal alongside the GW8 wildcard;
GW6 TOT(H) 6.79 is the only slot (LOW-8).

### 11. Price (MED-2, LOW-7)
Barry: net +75k in-event at 4.5% owned, `cost_change_event 0` so far; one price
night (~01:30 UTC 4 Sep) sits between now and the deadline. A rise to 5.6
strands the move (bank 1.0 + 4.5 = 5.5). **Execute tonight, before the price
window** — a zero-cost action that retires the risk; the named fallback (bank
the FT, GW4 two-FT route) remains if it has already moved. Kusi-Asare −7k, no
drop risk. Deferral of the restructure carries no buy-side price cost (Isak
falling, Fernandes flat). Drift on holdings (LOW-7) trims GW4/5 headroom but the
Tarkowski → De Cuyper route still frees ≥ 1.2 at 4.8.

## Accepted risks to carry into final.md
- MED-3 template fades (João Pedro above all) — deliberate, GW4 verdict.
- MED-4 MCI cap + captain concentration — wildcard GW8 material.
- LOW-6 dead GK2 — repair GW5 via the De Cuyper cash or the wildcard.
- LOW-9 boundary/vice recency sensitivity — GW4 C8 / LOW-4 evidence.

## Required edits before final.md (no re-optimization)
1. GW4 earmark §1: add condition (c) — prior-only-rates gross ≥ 6 — and record
   today's value (−1.69) and the ledger split (Haaland +1.69/app, Fernandes
   +6.84/app) so GW4 tests it rather than re-discovers it.
2. Executor note: apply Kusi-Asare → Barry before the 4 Sep price window.
3. Chip commentary: strike "GW8 BOU(H)" as a Fernandes TC option while the GW8
   wildcard earmark stands.

Verdict: APPROVE
