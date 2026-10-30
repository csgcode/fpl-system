# GW9 Red-Team Review

Reviewed: data/decisions/gw9/squad-proposal.md (bank the free transfer,
Triple Captain on Haaland v BHA (H), vice Tavernier, chip_plan freehit GW16
and bboost GW19). Inputs: data/analysis/gw9/*, data/raw/gw9/bootstrap.json
and players-slim.csv, data/retro/gw8.md, the GW8 final.md ledger and STATE
block, data/suggestions.md. Deadline 2026-10-31 11:00 UTC.

**Verdict: APPROVE** — no HIGH finding. One MED (template exposure, the
same accepted risk as GW8 F3). Everything else is LOW or a pass.

## Independent checks

| Check | Result |
|---|---|
| `objective` re-run (same `--sell`, `--bank 0.1 --free-transfers 1 --moves none`) | identical: baseline 339.865 / 329.329, top singles, `plan: none`, XI 3-4-3 55.458, captain top 5, bench line |
| Positions | GKP 2, DEF 5, MID 5, FWD 3 |
| Clubs | ARS 2, BOU 2, TOT 2, LEE 2, MUN/MCI/LIV/SUN/NEW/BHA/EVE 1 — none at 3 |
| XI formation | 1 GK, 3 DEF, 4 MID, 3 FWD = 11; one captain, one vice, both in the XI |
| Budget | Σ `--sell` 99.1 + bank 0.1 = 99.2 = STATE `team_value`; bank not added twice. Market value Σ now_cost 99.7 (matches the retro) |
| Chip windows (bootstrap `chips`) | 3xc 1–19, bboost 1–19, freehit 2–19; wildcard used GW8; `chip: 3xc` legal, no other chip this GW |
| Flags (bootstrap, fetched 16:32 UTC) | Calafiori d 75% hip (news 24 Oct); 14 others `a`; Haaland, Isak, Van Hecke carry cleared 100% flags; no suspension within one card (Tavernier 3 yellows is the highest) |
| Ledger closed rows S1–S6 | byte-identical to the GW8 ledger |
| Auth | runs.jsonl: auth-check FAIL 16:33:37Z, PASS 16:34:59Z — the relayed `my-team` read post-dates a working session |

## Findings

### F1 — LOW — Minutes and bench

No XI starter is below p_start 0.85; the lowest is Isak 0.88 (MED
uncertainty, 7/8 starts). Bench: Kinsky 0.95, Gomez 0.94, Justin 0.95,
Calafiori 0.65 at slot 15. Slot 15 is reached only when two XI players
miss, so it is not a dead bench. With a 3-DEF XI an absent defender skips
Gomez and brings Justin — the order wanted.

Note: players-DEF.json and the proposal both say Calafiori was "hooked 22'
R8". The calibration ledger (data/retro/gw8.md) says start N, 22 minutes —
he came on, he was not taken off. The p_start of 0.65 is defensible either
way; the wording should not be carried into final.md as fact.

### F2 — LOW — Flag freshness

Calafiori's 75% flag is six days old and pre-dates his R8 substitute
appearance; no newer bootstrap news. The finalizer's `flags` gate re-checks
all 15 ids before final.md, which is the right place for it. Nothing in the
XI carries a flag.

### F3 — pass — Constraints and money

Recomputed above. Bank 0.1 is under the £0.2m line, but no purchase is
proposed, so an overnight rise can block nothing; no fallback transfer is
needed. The per-player `--sell` list is a reconstruction whose sum matches
the relayed `my-team` selling total; individual prices may differ by 0.1
(Tavernier up 0.2, Calafiori and Kinsky down 0.1). Before any GW10
transfer the executor's `my-team` figures replace it — the proposal says
so.

### F4 — LOW — Concentration

No club has more than two players, and no club's attack carries more than
one XI player. The pairs are defensive (Gabriel + Calafiori, Hill +
Tavernier, Van Hecke + Kinsky, Trafford + Justin) and half of each pair is
on the bench.

### F5 — MED — Template exposure (accepted risk, carried from GW8 F3)

Held above 30%: Haaland 78.6%, Calafiori 49.1%. Not held above 30%:

| Player | Club | Owned | Note |
|---|---|---|---|
| João Pedro | CHE | 55.4% | status i — no cost while out |
| Rogers | CHE | 50.5% | |
| Groß | BHA | 45.8% | sold GW8 |
| Raya | ARS | 45.6% | sold GW8 |
| De Cuyper | BHA | 42.5% | |
| Cherki | MCI | 37.6% | |

Five healthy template players are not held, and the one template player we
do hold besides Haaland sits on our bench at p_start 0.65. A haul from any
of the five lands as rank loss. The exposure is deliberate: no move into
any of them passes the gate (Calafiori → De Cuyper +0.050 / +0.389 is the
only single positive on both readings and is far short of 2.0). Carry into
final.md as an accepted risk, as GW8 did.

### F6 — LOW — Fixture decay after the window

ARS (Gabriel, Calafiori) and MCI (Haaland) turn harder from GW12
(Σλ_att −0.65 and −0.61); LEE, MUN and NFO turn easier. Two free transfers
at GW10 and three at GW11 if unused cover a reshape before GW12. Nothing
beyond GW14 is modelled (see F10).

### F7 — n/a — Hits

None proposed. The free gate was not reached by any single (best
+1.797 blend, prior −0.085). No `tie-break group:` line exists to test.
The prior-only reproduction is not required for a no-transfer plan;
`objective`'s prior column was reproduced instead.

### F8 — LOW — Captain and vice

Captain Haaland 6.116 is the top undiscounted single-GW EP in the XI,
1.277 clear of Mbeumo — outside the 0.5 band. p_start_gw[0] 0.94.

Vice: Mbeumo 4.839 v Tavernier 4.643 is inside 0.5 and both clear 0.85, so
the spec's tie-break holds both and S8 may break it. The proposal prices
the steer at 0.196 EP "only if Haaland misses". Under Triple Captain the
vice is tripled, so the gap in that case is 0.588; weighted by
P(Haaland misses) ≈ 0.06 the cost is about 0.04 EP. Immaterial, but the
figure in the ledger row should say 0.588 × P(miss), not 0.196.

### F9 — LOW — Recency

The 3xc is not driven by R8 (Haaland 8 pts, err +2.20): his GW9 EP rests
on xG90 0.756, penalties, 8/8 starts and MCI's ATT rank 1. The vice steer
cites Tavernier's ret5 3/5 after his R8 goal; it decides a 0.04-EP tie
and nothing else.

### F10 — LOW — Chip path and 3xc timing

Path: wildcard GW8 (used), 3xc GW9, freehit GW16, bboost GW19 — ten
gameweeks for the last two, one chip per gameweek, all inside the bootstrap
windows. No proposed move sells a 3xc target or dismantles the bench.

Timing: the proposal compares GW9 only against GW10–14 (ep_gw 6.116,
5.378, 6.208, 4.948, 5.916, 5.901). The 3xc window runs to GW19, where
MCI play CHE (H) GW15, HUL (H) GW16, NEW (A) GW17, EVE (A) GW18, TOT (H)
GW19. Scaling GW9's λ_att 2.05 by the current ratings (MCI ATT 1.37;
opponent DEFW) gives roughly CHE (H) 2.15, HUL (H) 2.47, NEW (A) 2.17,
EVE (A) 1.87, TOT (H) 1.84. Only HUL (H) is materially above GW9, and it
rests on a banded promoted-club rating — exactly what C5 says a Triple
Captain case may never stand on; GW16 is also the freehit placeholder.
Holding seven weeks for an unmodelled fixture on a 0.94 starter is not a
better bet than a fixture-independent 6.116 on this week's team news.
The decision stands; the gap in the method (chip timing graded only inside
the EP horizon) goes to the backlog.

### F11 — LOW — Price risk

Calafiori fell 0.1 this event on net transfers out of about 474k and has
seven days to the GW10 deadline; a second fall is plausible. His selling
price tracks now_cost below the 6.0 purchase, so the cost of holding is
0.1–0.2 of team value, not the "0.1 at most" the proposal and the S7 row
state. It does not change the decision: Calafiori → Silva fails the gate
on the prior-only sign, which the S7 policy never overrides. Tavernier's
rise (+0.2 banked) and the Kinsky and Barry falls are already taken.
No transfer, so nothing to time against the price change.

### F12 — pass — Suggestions ledger

Open set recomputed: S1–S6 are closed in the GW8 ledger (followed ×5,
rejected ×1); no withdraw rows; no Until GW has passed; S7 and S8
(From GW 7, open-ended) are open. Marker `through S8` equals the file's
highest S#; nothing above it. S7 and S8 keep GW 7 as re-affirmed standing
rows must. Closed rows carried verbatim (checked). Each standing reason
states how the plan honours it: S7 as a sell-side policy with the live
faller named and the gate result quoted; S8 as the vice tie-break with no
buy judged. The plan does not contradict either. Two figures inside the
rows are understated (F8, F11); neither changes a disposition.

### F13 — LOW — Execution dependency

The chip rides the set-lineup POST. The session that expired at 16:33 was
re-captured by 16:35. If it lapses again before 11:00 UTC the 3xc must be
set by hand on the website; a chip that is planned but not activated is
the one irreversible loss in this plan.

## Verdict

**APPROVE.** No HIGH. Carry F5 (template exposure) into final.md as an
accepted risk; correct the two figures in F8 and F11 when the ledger rows
are copied; drop the "hooked" wording (F1).

## Backlog

One row appended to docs/backlog.md (A5, WORKFLOW): Triple Captain timing
is graded only inside the 6-GW EP horizon while the chip window runs to
GW19.
