# GW10 Red-Team Review

Reviewed: data/decisions/gw10/squad-proposal.md (no transfers, bank both
free transfers to 3 at GW11; captain Gabriel v HUL (H), vice Haaland;
`chip: null`; chip_plan freehit GW16 and bboost GW19). Inputs:
data/analysis/gw10/*, data/raw/gw10/bootstrap.json and players-slim.csv,
data/retro/gw9.md, the GW9 final.md ledger and STATE block,
data/suggestions.md, and the live account facts relayed by the orchestrator
(free transfers 2, bank 0.1, budget 99.5; bboost and freehit available, 3xc
and wildcard played). Deadline 2026-11-06 18:30 UTC.

**Verdict: APPROVE** — no HIGH finding. Three MED (captaincy resting on a
banded clean-sheet term, bench boost timing, template exposure), the rest
LOW or a pass. Each MED names its alternative so the finalizer can record it
as an accepted risk.

## Independent checks

| Check | Result |
|---|---|
| `objective` re-run (same `--sell`, `--bank 0.1 --free-transfers 2 --moves none`) | identical: baseline 342.415 / 333.269, 1551 legal singles, same top 10, `plan: none`, `FT next 3`, XI 4-3-3 59.026, captain top 5, three boundary pairs, bench line |
| Prior-only files rebuilt (`ep --prior-weight 1.0`, DEF / MID / FWD, scratch) | Gabriel 5.546 is still the squad's top GW10 EP prior-only (Isak 5.314, Haaland 5.207, Mbeumo 4.980); every top-10 single's prior-only sign matches `objective`'s |
| Positions | GKP 2, DEF 5, MID 5, FWD 3 |
| Clubs | ARS 2, BOU 2, TOT 2, LEE 2; MUN, MCI, LIV, SUN, NEW, BHA, EVE 1 — none at 3 |
| XI formation | 1 GK, 4 DEF, 3 MID, 3 FWD = 11; one captain (Gabriel) and one vice (Haaland), both in the XI |
| Budget | Σ `--sell` 99.4 + bank 0.1 = 99.5 = STATE `team_value` = live budget; bank not added twice. Market value Σ now_cost 100.2 |
| Predicted XI | 59.026 − Justin 4.155 + Van Hecke 4.074 = 58.945, as stated |
| Chip windows (bootstrap `chips`, set 1) | bboost 1–19, freehit 2–19; wildcard used GW8, 3xc used GW9; `chip: null` legal; chips_used matches the live account |
| Flags (bootstrap cached 2026-11-05) | all 15 status `a`; Calafiori `chance_of_playing_this_round` 75 is the 24 Oct news, next-round chance 100, played 90' in R9; Haaland, Isak, Van Hecke carry cleared 100% flags; yellows: Tavernier 3, Gabriel / Mbeumo / Van Hecke 2 — none within one card of a ban |
| Ledger closed rows S1–S6 | byte-identical to the GW9 ledger; S7 and S8 keep GW 7 |
| Auth | data/executor/gw10/runs.jsonl: auth-check FAIL 19:45:36Z (expired session), PASS 19:48:14Z — the relayed `my-team` figures post-date a working session |

## Findings

### F1 — LOW — Minutes and bench

No XI starter is below p_start 0.85; the lowest is Calafiori 0.90 (hip flag
24 Oct, status `a`, 22' then 90' in R8–R9, back starting at LB) and Isak
0.93 (MED uncertainty). Bench: Kinsky 0.95, Justin 0.94, Gomez 0.95, Barnes
0.95 — no dead bench. With a 4-DEF XI an absent defender, midfielder or
forward all bring Justin first (5-2-3 and 5-3-2 are legal), the higher-EP
sub either way.

### F2 — LOW — Flag freshness

Nothing new in the bootstrap. Calafiori's 75% this-round figure is twelve
days old and pre-dates two appearances; the bootstrap's next-round figure is
100. The finalizer's `flags` gate re-checks the 15 ids before final.md,
which is the right place for it. Nothing in the XI carries a live flag.

### F3 — pass — Constraints and money

Recomputed above. Bank 0.1 is under the £0.2m line, but no purchase is
proposed, so an overnight rise can block nothing and no fallback transfer is
needed. The per-player `--sell` list is a reconstruction whose sum (99.4)
matches the relayed selling total; the four price moves since GW9 it names
(Gabriel, Van Hecke, Tavernier, Isak) are the four the two bootstraps show.
Haaland's row (sell 15.6, now_cost 15.8 in both bootstraps) moved 15.5 →
15.6 between the two lists without a bootstrap move behind it — the
proposal already says rows without a purchase price on record may be off by
0.1. Harmless this GW (no POST); before any GW11 transfer the executor's
`my-team` figures replace the list.

### F4 — LOW — Concentration

No club has more than two players, and no club's attack carries more than
one XI player. The ARS pair (Gabriel, Calafiori) is defensive and both
start, so one ARS clean sheet or its absence moves two XI rows plus the
captain double — about 11.4 EP of the 58.945 rests on ARS keeping HUL out
(F8). The other pairs (Hill + Tavernier, Van Hecke + Kinsky, Trafford +
Justin) each have one half on the bench.

### F5 — MED — Template exposure (accepted risk, carried from GW9 F5)

Held above 30%: Haaland 79.1%, Calafiori 48.0% (now in the XI). Not held
above 30%:

| Player | Club | Owned | Note |
|---|---|---|---|
| Rogers | CHE | 52.8% | |
| Groß | BHA | 46.9% | sold GW8 |
| Raya | ARS | 46.8% | sold GW8; GW10 EP 4.089 v Trafford 3.888 |
| De Cuyper | BHA | 45.4% | Calafiori → De Cuyper +0.238 / +0.661, the only single positive on both readings |
| João Pedro | CHE | 38.4% | status `i` — no cost while out |
| Cherki | MCI | 34.9% | |

Five healthy template players are not held; a haul from any lands as rank
loss. Deliberate: no move into any of them comes near the 2.0 free gate
(`objective` top 10 re-run above). Alternative if the user wants the
exposure reduced: Calafiori → De Cuyper on one free transfer (+0.238 blend,
+0.661 prior, bank 0.6), which costs one of the three GW11 transfers and
sells the squad's highest-owned defender.

### F6 — LOW — Fixture myopia

ARS turn hard from GW13 (Δ Σλ_att −1.21, Δ ΣP(CS) −0.13) with two ARS
defenders held; MCI (+0.91) and NEW (+1.02) turn easy. Three free transfers
at the GW11 deadline, after the international break, land before the turn.
Nothing beyond GW15 is in the files; the GW11 fixture analyst's scheduled
swing check covers it.

### F7 — pass — Hits and prior-only (C14)

No hit and no transfer proposed. Reproduced the prior-only view: the best
single (Calafiori → Silva +0.771) is −0.301 prior-only, the two
positive-both singles (+0.238 / +0.661, +0.072 / +0.414) are far short of
2.0, and the best paired marginal (Barnes → Gibbs-White +1.903) is −0.551
prior-only. No `tie-break group:` line was printed. Banking is the greedy
reference and the plan.

### F8 — MED — Captaincy rests on a banded clean-sheet term (C4/C12)

Gabriel is the highest undiscounted single-GW EP on both readings: 5.785
blend (Haaland 5.265, gap 0.520, outside the 0.5 band) and 5.546
prior-only (Isak 5.314, Haaland 5.207). The spec's captaincy rule (item 8)
is met and the pick is not a blend artefact.

The concern is where the EP comes from. From fixtures.json, ARS v HUL (H)
has `p_cs` 0.50 on a banded row (C12, ±15pp). Gabriel's GW10 terms, derived
from the files (players-DEF.json carries 6-GW term totals only):

| Term | GW10 value | Basis |
|---|---|---|
| appearance | 1.90 | p_start 0.95 × 2, minutes_per_start 90 |
| clean sheet | 1.90 | p_cs 0.50 × 4 × 0.95 |
| attack | ≈ 1.0 | 5.2 over six fixtures, GW10 λ_att 2.14 is the window's largest |
| DefCon | ≈ 0.8 | 4.86 / 6 |
| bonus, cards, conceded | ≈ 0.2 net | |

The clean-sheet term ties the appearance term for largest; it is not the
*single* largest, so C4's letter ("never let a promoted-club fixture be the
single largest EP term for a selected player") is not broken, and Gabriel
starts in the XI on any reading (pool #1 DEF on blend and prior). But the
captaincy — a doubling — rests on the central value of the banded term: at
the band's low end (p_cs 0.35) the term is 1.33 and Gabriel is 5.21 blend
(below Haaland 5.265) and 4.98 prior-only (below Isak and Haaland); at the
high end (0.65) he is 6.36. The band is symmetric, so 5.785 is still the
expected value and the pick maximizes EP; the GW4 record (Raya and Gabriel
at SUN (A), the round's two largest *positive* residuals) says the band's
low side has not been where the misses fell.

Not HIGH: a REVISE to Haaland would breach item 8 (lower EP, outside the
tie band) and the spec never says the C4 prohibition reaches the captain
pick. Alternative for the finalizer to record: captain Haaland (NFO (A),
5.265, his window-low fixture), cost −0.520 EP central, in exchange for a
captaincy that does not depend on a banded promoted-club term. The GW11
fixture analyst's scheduled check (ARS v HUL not a selected player's
largest defensive term, in the GW10 retro) already covers the audit; the
retro should state the tie explicitly.

### F9 — LOW — Recency bias

Van Hecke (15 pts in R9, classed VARIANCE) starts over Justin on C20's
DefCon-floor tie-break (0.151 v 0.137 inside a 0.081 gap), not on the haul:
his GW10 EP 4.074 is the *lower* of the pair and the proposal says so.
Barry (9 pts) is fifth in the captain ranking; Gabriel scored 6, not a
haul. No pick is driven by last week.

### F10 — MED — Bench boost timing (chip path)

Chip path: bboost and freehit, ten gameweeks (GW10–19) and one chip per
GW — no foreclosure, and no proposed move dismantles anything. The chip
plan (freehit GW16 placeholder, bboost GW19) is a forecast only.

The open question is whether GW19 is the right bboost earmark. The current
bench is 15.065 GW10 EP, four rows at p_start ≥ 0.94, no rotation risk
before the break; the proposal's own reading says 14–15 in each of
GW10–12. Against that: GW19 is the window's last gameweek, so any mishap
(lineup not set, session lapse, a bench row injured that week) loses the
chip outright; the three GW11 free transfers will be spent on the XI, not
the bench; and GW14–19 is the congested December run, when bench rows at
£4.4–6.1m are likelier to rotate than now. The earmark's upside is a double
gameweek in GW16–19, which no file forecasts and which set-1 windows rarely
contain. There is no `objective` reading for bboost (the optimizer appended
the backlog row), so nothing grades GW19's bench against today's 15.065.

Alternative for the finalizer to record: play bboost at GW10 (+15.065
expected on the current files) or hold it for the first of GW11–13 whose
bench EP matches, rather than the last-GW default. Not HIGH: the files
cannot grade the comparison and the earmark is provisional.

### F11 — LOW — Price risk

Net-out rows: Mbeumo (out 123,616 v in 19,147, 7.9) and Barnes (out 37,613
v in 12,129, 6.1). Each fall costs 0.1 of team value; no move out of either
passes the gate (Mbeumo → Gibbs-White −4.331 / −4.477; Barnes → McAtee
+0.072 / +0.414), so the cost is accepted, as the S7 row says. Rising rows
held: Tavernier (in 350,001), Isak (270,834), Van Hecke (256,690), Gabriel
(110,916) — all already moved 0.1–0.2 since GW9 and still net-in. No buy
proposed, so transfer timing in the window does not arise.

### F12 — pass — Suggestions (item 12)

Recomputed: data/suggestions.md holds S1–S8, no withdraw rows, every From
GW ≤ 10; the GW9 ledger closes S1–S6 (followed / rejected) and leaves S7
and S8 standing. Open set = {S7, S8}; the proposal's marker is S8 and
nothing is above it. S1–S6 are carried byte-identical. S7 and S8 keep GW 7
(the cycle that set `standing`), and each reason says how this plan honours
it: S7 as a sell-side policy that never overrides the gate (the Mbeumo and
Barnes grades are quoted verbatim); S8 as the vice tie-break (Haaland v
Mbeumo inside 0.5, both p_start ≥ 0.85) at zero cost, and correctly unable
to reach the captaincy. No deferred row, no expired row, no malformed row.

### F13 — LOW — STATE block and execution

15 picks, one captain and one vice, both in the XI; `chip: null` explicit;
`chips_used` lists wildcard GW8 and 3xc GW9, matching the live account;
`team_value` 99.5 and `bank` 0.1 are the live figures. `free_transfers_banked:
3` follows the GW9 convention (transfers available at the next deadline),
which the live account confirmed last cycle (forecast 2, live 2). The
lineup changes from GW9 (3-4-3 → 4-3-3, captain Haaland → Gabriel, vice
Tavernier → Haaland, Calafiori and Van Hecke's slots), so the set-lineup
POST is required even with no transfers; the transfer step still runs and
prints "already applied".

## Backlog rows appended

Two, outside this agent's remit (format at the top of docs/backlog.md):
per-GW term breakdowns missing from players-{pos}.json (F8 had to derive
them), and the undefined interaction between the captaincy rule and the
C4/C12 largest-term prohibition.
