# GW5 Red-Team Review (A5)

Target: `data/decisions/gw5/squad-proposal.md`. Deadline 2026-09-18T17:30:00Z.
Snapshot `data/raw/gw5/` fetched 2026-09-18T12:49:57Z — 4h41m before the
deadline, inside the 24h gate.

**Verdict: REVISE** — three HIGH findings.

Everything below was recomputed from `data/analysis/gw5/players-*.json`,
`data/analysis/gw5/fixtures.json`, `data/raw/gw5/{bootstrap,fixtures,entry-*}.json`
and `data/raw/gw5/players-slim.csv`. Where the proposal's arithmetic was
checked it reproduced exactly; the findings are about *which* arithmetic was
used, not about slips in it.

## Summary

| # | Severity | Finding |
|---|---|---|
| H1 | **HIGH** | The decision metric was swapped for one the spec does not authorise, and the swap is the only thing that makes transfer #2 pass its gate |
| H2 | **HIGH** | The simulation that replaced the metric has an auto-substitution defect; every sim figure in the proposal is affected |
| H3 | **HIGH** | §3e's three-way tie — and the ad-hoc tie-break invented to break it — is an artefact of H2 |
| M1 | MED | The Ndiaye sale rationale inverts the analyst's own note, and his `p_start_gw` is flat where availability is not |
| M2 | MED | Template exposure (checklist 5) is not analysed anywhere in the proposal |
| M3 | MED | The S1 ledger row is mechanically correct but its reason rests on H3 |
| L1 | LOW | Dead GK2 slot, fifth gameweek; unrepairable at this budget |
| L2 | LOW | §5's banded-exposure table omits an incoming player |
| L3 | LOW | Price bleed on the incoming midfielder |
| L4 | LOW | Correlated Arsenal clean sheet |
| L5 | LOW | Post-horizon decay is mild; no blanks or doubles anywhere in GW5–13 |

Clean on checklist items 1, 2, 3, 7, 8, 9 and 10 — see `## Checked and clean`.

---

## H1 — HIGH: the objective function was substituted mid-cycle

`agents/squad-optimizer.md` §Objective: *maximize Σ over 6 GWs of: starting-XI
EP + captain EP (doubled)*. §Transfer rule: *gains < 2 EP → bank the free
transfer*.

The proposal (§1, §4) declares that objective defective, runs its own
Monte-Carlo with auto-substitutions, and **uses the simulation as the decision
metric**. Transfer #2 is +1.01 on the spec's objective and +2.61 on the sim.
It is made because of the sim.

This is not a judgment call the optimizer is allowed to make. Its own
`## Rules` section and CLAUDE.md §Improvement backlog both say an agent-spec
finding is appended to `docs/backlog.md` and **never acted on in-cycle**. The
optimizer filed exactly that row — `| GW5 | 2026-09-18 | A4 | WORKFLOW |
agents/squad-optimizer.md states the objective as starting-XI EP plus captain
EP … | data/decisions/gw5/squad-proposal.md section 4 | open |` — and then
acted on it in the same cycle. Filing and acting are alternatives, not a
sequence.

**The argument for substituting is also wrong on its facts.** §1 claims that
under the spec's objective *"the largest 'gain' on the board is replacing
Dubravka: +17 to +21 EP6"*. It is not. Under starting-XI EP + captain EP,
Dubravka → Tzolakis is worth **+1.31**, below the gate and correctly refused.
The +21.58 figure is the *squad EP6 sum* — a metric the spec never names. §1
attributes an artefact of one metric to a different metric and uses that to
retire the different metric. §3d half-concedes this ("the £17–21 EP6 headline
is the §1 artefact") without noticing it dissolves §1's case.

Independent recomputation of the spec's objective (best legal XI per GW by
`ep_gw[k]`, captain doubled, summed over GW5–10) reproduces the proposal's own
XI-max column to three decimals:

| Quantity | Mine | Proposal |
|---|---:|---:|
| Current-squad baseline | 337.699 | 337.70 |
| Transfer 1 (Ndiaye → E.Le Fée) | **+4.105** | +4.11 |
| Transfer 2 marginal (Shaw → Justin) | **+1.013** | +1.01 |
| PLAN total | 342.817 | 342.82 |
| RIVAL total | 342.410 | 342.41 |

On prior-only rates transfer 2 is **+0.443**. It fails the 2.0 gate on both
readings.

I then searched **all 1 469 legal second free moves** from the post-transfer-1
squad on the spec's objective. **None clears 2.0 on the blend.** The best is
Anderson → Schade at +1.853 blend / −1.107 prior, which sign-flips and is
barred by C14 anyway. There is no spec-conformant second transfer available
this week — the correct action is to bank.

### Concrete alternative (recommended)

**Make transfer 1 only.** OUT Ndiaye (sell £5.9m) → IN E.Le Fée (£5.8m).
It is the best single move on *both* readings (+4.105 blend / +2.205 prior),
clears 2.0 on both, and none of H1–H3 touches it.

| STATE field | Proposal | Revised |
|---|---|---|
| `bank` | 0.0 | **0.1** |
| `team_value` | 99.3 | 99.3 (99.2 sell + 0.1 bank) |
| `free_transfers_banked` | 1 | **2** |
| `transfers_made` | 2 rows | Ndiaye → E.Le Fée only |

XI is unchanged — Shaw was bench slot 15 and Justin would have been slot 13,
so neither enters the XI in GW5. Predicted GW5 stays **57.40**, captain
Haaland, vice Mbeumo, formation 3-4-3. Bench becomes 12 Dubravka, 13 E.Le Fée
(3.884), 14 Richards (2.870), 15 Shaw (1.585): the 13/14 gap is 1.014, outside
C8's 0.25 band, so EP decides and no tie-break is needed.

### Alternative if the substitution is authorised

If the orchestrator relays this to the user and the user authorises the metric
change now, transfer #2 survives on the merits — my corrected simulation (H2)
puts it at **+2.69 blend / +2.01 prior**, clearing 2.0 on both, better than
the proposal's own +2.61 / +2.55. In that case final.md must record that
transfer #2 rests on a user-authorised metric change, and the backlog row must
be closed by a real spec change before GW6 rather than re-argued every cycle.

---

## H2 — HIGH: the replacement simulation misapplies FPL auto-substitution

The sim ran from an unversioned scratch script. I read it, reproduced the
proposal's headline figures from it exactly, and found a defect.

The substitution loop adds bench players in bench order with a legality guard
that is dead code — the condition ends `… >= 1 or True`, so it is always true —
and then "repairs" an illegal team by deleting the **last-added** substitute
until the formation is legal or no substitutes remain. Real FPL *skips* a bench
player whose entry would break the formation and tries the next one.

Worked case, which the plan's own 3-DEF XI makes common: two of Thiaw /
Tarkowski / Gabriel fail to play. FPL brings on bench 1 (Justin, DEF) and bench
3 (Richards, DEF), skipping the midfielder, and fields eleven. The script adds
bench 1 and bench 2 (Justin, E.Le Fée), finds 2 DEF, strips E.Le Fée, still
finds 2 DEF, strips Justin — and fields **nine**. The error is largest in
exactly the multi-absence branch the sim exists to price.

Running the script as written reproduces the proposal:

| | base | T1 | PLAN | RIVAL | EARMARK | T2 marginal |
|---|---:|---:|---:|---:|---:|---:|
| script, blend | 355.65 | +3.35 | +5.96 | **+6.49** | +5.43 | +2.61 |
| script, prior | 342.52 | +1.00 | +3.56 | +0.80 | **+4.76** | +2.55 |
| **corrected, blend** | **357.76** | +3.68 | **+6.37** | +5.92 | +5.16 | **+2.69** |
| **corrected, prior** | **343.51** | +1.85 | +3.86 | +0.26 | **+4.63** | **+2.01** |

(corrected figures: 5 independent seeds, n=20 000 paths per gameweek,
seed-to-seed sd ≤ 0.05 on every row.)

The defect costs **2.11 EP of auto-sub value** on the blend baseline — i.e. the
sim understates the very quantity it was introduced to capture, which cuts
*against* the proposal's own case as well as for it.

**Alternative:** if the sim is used at all, use the corrected numbers. They do
not change the transfer choice, and they change the reasoning completely (H3).
Decision-critical arithmetic should not live in a throwaway script with no
test — filed to the backlog.

---

## H3 — HIGH: §3e's three-way tie, and its tie-break, are artefacts of H2

§3e is the proposal's most consequential passage: it concedes that *"no EP
criterion separates these three honestly"*, notes that "the blend decides"
picks the RIVAL and minimax regret picks the EARMARK, and then introduces a
third criterion — *prefer the candidate least exposed to the minutes model* —
which is the only one of the three that selects the PLAN.

Under the corrected simulation the tie does not exist:

| Candidate | blend | prior | Σ | Max regret |
|---|---:|---:|---:|---:|
| **PLAN** — Ndiaye + Shaw → E.Le Fée + Justin | **+6.37** | +3.86 | **10.23** | **0.77** |
| RIVAL — Anderson + Shaw → E.Le Fée + Justin | +5.92 | +0.26 | 6.18 | 4.37 |
| EARMARK — Anderson + Thiago → Cherki + Wissa | +5.16 | **+4.63** | 9.79 | 1.21 |

The PLAN now wins on the blend, on the sum of the two readings, and on minimax
regret. It also wins on the spec's own objective (+5.118 v +4.711 v +3.143).
**Every stated criterion selects the plan.** The tie-break is not needed, and
should be deleted rather than defended.

That matters because the tie-break is unsound on its own terms:

- It counts rows below 0.90 `p_start` — an unweighted count in which Dubravka
  at 0.03 and Cherki at 0.80 score the same.
- It penalises `p_start` a third time. `p_start` is already inside `ep_gw`;
  **C16** retired the certainty multiplier from selection for precisely this
  reason ("p_start is already inside `ep`, so outside the captaincy's variance
  case the multiplier discounts rotation risk twice"); and **C18**'s pool-wide
  cut has already corrected the level bias *this cycle* — mean −0.023 across
  410 players, Ndiaye −0.15, Shaw −0.12. §3e then discounts the candidates
  again for the bias C18 just removed. The proposal claims C16 compliance in
  §13 while doing the thing C16 forbids, in a different currency.
- A criterion introduced in the same paragraph that needs it, selecting the
  option no pre-existing criterion selects, is post-hoc by construction. The
  §3e write-up is admirably candid that it is doing this; candour does not make
  it a rule.

**Alternative:** replace §3e with the corrected table above. The transfer
choice among the three candidates is unchanged and needs no new criterion. Note
also that the GW4 ledger banked a free transfer with the earmark named as its
purpose ("banking to 2 FTs for a GW5 upgrade (Anderson+Thiago→Cherki+Wissa
+5.06 / +3.46 clears free)"); abandoning that earmark is correct on the
corrected numbers, and should be justified by them rather than by exposure
counting.

---

## M1 — MED: the Ndiaye sale rationale inverts its own source

A3's note for Ndiaye (`data/analysis/gw5/inputs-MID.json`, id 237) reads:
*"3/4 starts; came off bench 45' GW4 - streak broken; **Foden ban frees
minutes**, Doku returns"*. §12 of the proposal renders this as *"Doku's return
plus **Foden's ban leave his minutes contested** in a stacked City midfield"* —
the opposite of what the analyst wrote for the Foden half.

The raw data agrees with the analyst, not the proposal, for the gameweek being
scored: Foden is `s`, *"Suspended until 17 Oct"* (misses GW5 and GW6, whose
deadline is 10 Oct); Doku is `i`, *"Calf injury - Expected back 20 Sep"* —
after this deadline. In GW5 City's midfield is **less** contested, not more.

Compounding it, Ndiaye's `p_start_gw` is flat `[0.78] × 6` while the
availability that drives it swings hard across the window; Shaw, by contrast,
correctly carries a per-GW vector `[0.50, 0.72, 0.74, 0.74, 0.74, 0.74]`. The
flat vector is too low at GW5 and too high at GW9–10.

**Impact is bounded and the sale survives.** Re-scoring with a phased Ndiaye
`[0.90, 0.88, 0.82, 0.78, 0.78, 0.78]` leaves transfer 1 at **+3.851** on the
spec's objective, still comfortably over 2.0, and Le Fée still leads the
position on both readings. Fix the sentence, not the transfer. The
`p_start_gw` shaping is A3's — filed to the backlog.

## M2 — MED: template exposure is never analysed

Checklist item 5 requires the differential position to be deliberate and
stated. The proposal does not mention ownership once, and the retro has carried
**MED-E template fades** unresolved for three rounds.

Unheld at ≥30% ownership:

| Owned | Player | Pos | Price | Note |
|---:|---|---|---:|---|
| 70.7% | João Pedro | CHE FWD | £7.8 | `d`, 75%, news 16 Sep |
| 50.2% | Calafiori | ARS DEF | £5.8 | fit |
| 40.5% | B.Fernandes | MUN MID | £12.0 | fit |
| 39.4% | Rogers | CHE MID | £7.7 | fit |
| 34.8% | Szoboszlai | LIV MID | £7.0 | fit |

Held above 20%: Haaland 73.1%, Raya 41.1%, Gabriel 23.1%, Mbeumo 21.9%. The
whole midfield sits below 22% and the incoming pair is 1.5% / 3.6%. That is a
deliberate-looking differential stance taken without a sentence acknowledging
it. **Alternative:** final.md records the list above as an accepted
rank-volatility risk, or names the single template hole to close at the GW8
wildcard.

## M3 — MED: the S1 ledger reason rests on H3

Mechanically the ledger is correct and I found nothing that meets the HIGH bar
in checklist item 12:

- marker `Read data/suggestions.md through S2` matches the highest S# in
  `data/suggestions.md`;
- S1 and S2 both have blank From/Until GW, so both are in window at N=5;
- S1 is re-affirmed `standing` and **keeps GW 4**, as CLAUDE.md requires of a
  re-affirmed standing row;
- S2 is closed `rejected` and is carried forward **verbatim**, character for
  character, from `data/decisions/gw4/final.md`;
- no expired, withdrawn, malformed or dropped S#; no deferral; no `followed`
  row to reproduce.

The defect is the reason text. The S1 Anderson half was declined *explicitly*
on §3e ("both within ~1 EP of the plan … so §3e decided on minutes-model
exposure instead"), and §3e is H3. The disposition itself survives — on the
corrected numbers both Anderson-exiting pairs lose to the plan on the blend
(+5.92 and +5.16 v +6.37) and on the sum — so the row stays `standing` at GW 4
and the reason is restated on those numbers. One further clause is owed: the
reason defends keeping Anderson partly on his DefCon floor (0.281) and C20,
which answers a suggestion that is explicitly about *ceiling*.

## LOW findings

**L1 — dead GK2, fifth gameweek.** Dubravka `p_start` 0.03, GW5 EP 0.116, EP6
0.66; the squad's only sub-0.90 row. No playing keeper is reachable at ≤£4.0m
(best available: Steele 0.74, Forster 0.42), and Tzolakis at £4.6m is out of
reach on either plan. The GW19 bench-boost earmark stays blocked until the GW8
wildcard. Correctly identified in the proposal; recorded here as the carried
risk.

**L2 — §5's banded table is incomplete.** I reproduced the all-banded-low
rerun by flooring all 34 banded `p_cs` rows by 15pp and re-running
`fpl ep --gw 5` for all four positions: Gabriel 28.79 → **28.24**, Raya 21.89 →
**21.32**, Tarkowski 25.82 → **24.16**, Thiaw 22.98 → **21.90** — exact on all
four. (Tzolakis came out 19.00 against the claimed 19.04; immaterial.) The
invariance claim holds: on the floored set the spec objective gives transfer 1
+4.101 and transfer 2 +1.057, both verdicts unchanged, and the PLAN still leads
RIVAL and EARMARK. But the table lists only GK/DEF: **E.Le Fée**, an incoming
player, takes his largest SUN clean-sheet row from GW9 COV(A) 0.31, which *is*
banded. "Incoming Justin deliberately has no banded row at all" is true of
Justin and silent about the other buy.

**L3 — price bleed on the incoming midfielder.** E.Le Fée is net **−74 697**
transfers this event and already −0.2 from his start price; he is the only buy
carrying fall risk. Justin is near-flat (net −2 506). Selling Ndiaye (net
−123 359) and Shaw (net −270 021) is right on value. The GW4 retro carried
"Price bleed against F2 — −0.3 this GW"; this belongs in final.md's risk list.

**L4 — correlated Arsenal clean sheet.** Raya and Gabriel are both ARS and both
take their largest P(CS) from the same banded GW10 row, so one conceded goal
hits both in the same gameweek. Club counts are legal (max 2). Tavernier +
Scott (BOU) are the only pair in the XI dependent on one team's attack — at
checklist item 4's limit, not over it.

**L5 — post-horizon decay is mild.** No blanks and no doubles anywhere in
GW5–13, which independently supports the freehit GW16 placeholder. GW11–13 mean
FDR: SUN 3.67 and LEE 3.67 for the two incoming clubs, against TOT 2.33, BOU
2.67, CRY 2.67 and MCI 3.00 elsewhere in the squad — the worse end of the
range, but both are bench/rotation slots and the GW8 wildcard precedes the
decay.

---

## Checked and clean

**1 — Minutes.** Every XI row is `p_start` ≥ 0.90 (Raya 0.94, Gabriel 0.93,
Haaland 0.93, Tarkowski / Mbeumo / Tavernier / Scott / Thiago 0.92, Barry 0.91,
Thiaw / Anderson 0.90) and every one is tagged LOW, consistent with C7. Σ
`p_start` over the XI is 10.11. The only sub-0.90 row is Dubravka (L1); the
outfield bench has no dead slot.

**2 — Flags.** All fifteen selected players are status `a` with empty `news`
and no `chance_of_playing`. Shaw (status `d`, 75%, news 2026-09-11) is the only
flagged name in the transfer set and he is the one leaving. Nothing stale: the
snapshot is 4h41m old and already carries today's 10:30Z Chelsea news.

**3 — Constraints, recomputed from bootstrap, not from the proposal.**
Positions 2 GKP / 5 DEF / 5 MID / 3 FWD ✓. Clubs ARS 2, EVE 2, BOU 2, MCI 2,
NEW / MUN / BRE / TOT / LEE / SUN / CRY 1 — max 2, all ≤ 3 ✓. 15 unique ids ✓.
XI is 1 GK / 3 DEF / 4 MID / 3 FWD ✓, exactly one captain and one vice, both in
the XI ✓, slot 12 is a GKP ✓, and every `picks:` name matches bootstrap
`web_name` ✓.

Budget, recomputed independently: purchases sum to **100.0** exactly
(GW1 fifteen + Tavernier 6.0 + Barry 5.5) against bank 0.0; applying the FPL
half-profit rule to GW5 `now_cost` gives pre-transfer sell **99.3** and
`now_cost` **99.8** (0.5 of unrealised profit across Tarkowski, Tavernier,
Scott, Haaland and Barry, all of which round down to zero profit). Funding:
sell 5.9 + 4.4 = **10.3** = buy 5.8 + 4.5, bank 0.0 → 0.0. Post-transfer sell
99.3 = the STATE `team_value`. **Legal and exact.**

The reconstruction risk the orchestrator flagged does not exist for this
transfer: both outgoing players have fallen *below* their purchase price
(Ndiaye 6.0 → 5.9, Shaw 4.5 → 4.4), so their sell price equals `now_cost`
whatever the purchase history was. Independently, `data/raw/gw5/entry-8455344.json`
gives `last_deadline_bank 0` and `last_deadline_value 996`, and 99.6 is exactly
the GW4 `now_cost` sum — which reconciles with the GW4 note that my-team's
"value" field is the purchase-basis total, not the sell basis.

**7 — Hits.** None taken, correctly. The best triple is +8.376 gross on the
spec's objective, so +4.376 net of the −4 — *below* the plan's +5.118 even
before the 6.0 gross gate. It loses outright, not just on the gate.

**8 — Captaincy.** Haaland 6.721 × 1.00 (LOW). Nearest XI alternative is
Mbeumo 5.212, a gap of **1.509** — three times the 0.5 band — and the gap holds
on prior-only (6.104 v 4.834). No candidate is within 0.5 under the mandated
LOW 1.00 / MED 0.92 / HIGH 0.80 mapping; every top-5 option is LOW so the
multipliers reorder nothing. Vice Mbeumo is verified correct on kickoff times:
MCI v SUN is 2026-09-20T13:00Z and FUL v MUN 2026-09-20T15:30Z, so a Haaland
non-start is known before Mbeumo's match starts.

**9 — Recency.** Pool-wide, the model does track last week: corr(GW4 actual
points, ΔEP6 from the GW4 to the GW5 analysis) = **+0.351** on n=410, slope
+0.315 EP6 per GW4 point; GW4 haulers gained +1.26 EP6 on average, blanks lost
−1.43. But **the buys run against the signal** — E.Le Fée scored 0 in GW4 and
gained +2.30 EP6; Justin scored 2 and gained +0.28. The recency signal shows up
on the *sell* side (Ndiaye 1 pt, −4.23; Cherki 1 pt, −3.45), which is M1's
point. Neither incoming player is a haul-chase.

**10 — Chips.** All four set-1 earmarks sit inside their bootstrap windows
(wildcard/freehit `start_event` 2 `stop_event` 19; bboost/3xc 1–19), one chip
per gameweek, freehit non-consecutive, `chip: null` this week. Nothing in the
plan sells a Triple Captain target (Haaland held; his GW9 row 6.995 is the
window maximum and band-free, so the C5 gate on fixture-independent EP is met
for the earmark) or dismantles a bench-boost bench — the bench improves. The
one live blocker is L1. GW6's deadline is 2026-10-10T10:00Z, **22 days** after
GW5's, so the proposal's international-break argument against banking is exact
— though under H1 the correct action is to bank anyway, because no legal second
move clears the gate.

---

## Unresolved risks for final.md

If the orchestrator takes the H1 alternative, these remain accepted risks:
L1 (dead GK2, routed to GW8), L3 (E.Le Fée price bleed), L4 (ARS clean-sheet
correlation), M2 (differential midfield) and the two banked free transfers
sitting idle for 22 days.

If the orchestrator keeps both transfers under a user-authorised metric change,
add: transfer #2 rests on a metric the agent spec does not define, and the
backlog row must be closed by a spec change before GW6.

Backlog rows appended this review: 2 (A5/WORKFLOW on unversioned
decision arithmetic, A3-MID/TOOL on flat `p_start_gw` against varying
availability).
