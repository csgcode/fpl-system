# GW5 Squad Proposal (2026/27) — weekly cycle — **REVISED · REOPEN re-score**

Deadline **2026-09-18T17:30:00Z**. Horizon **GW5–GW10**.

**ONE transfer, free: OUT Ndiaye (MCI, sell £5.9m) → IN E.Le Fée (SUN, £5.8m).
The second free transfer is BANKED. Hit 0. Bank £0.1m. 3-4-3, Haaland (C),
Mbeumo (V). Predicted GW5 57.40. No chip.**

## REOPEN note — the freshness-gate re-score

The finalizer's pre-deadline freshness gate failed and returned **REOPEN**.
A3-DEF re-derived the affected rows and `data/analysis/gw5/players-DEF.json`
was regenerated against the refreshed bootstrap (fetched 2026-09-18T15:19:53Z).
Everything below is recomputed on those files. REOPEN cycles are exempt from
the one-revision cap, and the governing objective is unchanged: the **spec
objective** — starting-XI EP + captain EP — with the C14 blend and prior-only
readings. The auto-sub-aware simulation stays withdrawn and is not reintroduced
in any form.

Eleven bootstrap rows changed `status` / `chance_of_playing_next_round` /
`news`; prices did not move. What they did to this decision:

| Change | Effect on the decision |
|---|---|
| **Shaw (423, ours, bench 15)** 75% → **50%**; `p_start` 0.50 → **0.32**, ramp `[0.32, 0.66, 0.72, 0.72, 0.72, 0.72]`, EP6 12.81 → **11.79** | **none.** Shaw is in the best XI in **zero** of GW5–10 on **both** readings, so under the spec objective his EP enters the objective with weight 0. The marginal of replacing him is **unchanged at +1.013 / +0.443** |
| **Pau (34)** 75% → `i` 0%, **Maatsen (36)** 25% → `i` 0%, **Burn (448)** return moved to 12 Oct | removed from the buyable pool. **None of the three appeared in any candidate list**, so nothing is withdrawn from §3 |
| **Botman (447)** ramp improved, EP6 → **20.95** (Burn's absence leaves his GW6 uncontested) | best move bringing him in is **Richards → Botman +0.007 blend / +0.807 prior** — an order of magnitude below the gate |
| **Röhl (246)**, **Wilson (260)** MID and **M.Bizot (29)** GKP → `i` 0% | removed from the pool; none was a candidate |
| **Doku (400)** `i` → `d` 75% | **enters** the pool at £7.4m. Infeasible as a single; as a second move only Mbeumo funds him, at **−8.167 blend / −5.422 prior** |
| **Gomes (54)**, **Gruev (344)** doubts cleared to `a` 100% | already in the pool as `d`; their `p_start` rows are A3-MID's and are carried as given (C18). Best move for either is **Ndiaye → +0.000 blend / −0.090 prior** — nowhere near the gate |

**The premise that a worse Shaw raises the marginal of replacing him is false
under the spec objective, and that is the point of the finding already filed.**
XI-max scores a player who never starts at zero, so a bench player's decline is
invisible to it: Shaw at 0.50 and Shaw at 0.32 produce the *same* baseline
(337.699 blend) and therefore the *same* Shaw → Justin marginal. The figure did
not move because the metric cannot see the change. That is the XI-max
bench-blindness already in `docs/backlog.md` from the first pass — **no second
row is appended for it.**

One genuinely new finding *was* filed: the refetch moved Baleba (131, £4.9m)
from `i` 0% to `d` 50%, which puts him inside the band `fpl ep` requires a
`p_start` for, so `fpl ep --position MID` now **refuses** to regenerate an
otherwise-correct `players-MID.json` from inputs written before the refetch.
One TOOL row appended to `docs/backlog.md`; not acted on in-cycle. The blend
MID EP values themselves are unaffected — prices did not move and the formula
reads `p_start`, rates and fixtures, not `status` — so the pool is filtered on
the refreshed `status` here and Baleba, absent from both readings, stays out of
it.

Pool and enumeration counts moved with the status changes: **32 GKP, 131 DEF,
184 MID, 40 FWD**; **1 376** legal singles (was 1 392), **1 452** legal second
moves (was 1 469), **1 438** legal third moves (was 1 455). Every delta quoted
in this document was recomputed on the refreshed files; the prior-only rebuild
reproduces the earlier prior EP6 column **exactly** on every GKP, MID and FWD
row shared with it (36 / 191 / 43) and differs only on the five DEF rows
A3-DEF re-derived (Shaw, Pau, Maatsen, Burn, Botman), which is
the control that the rebuild changed nothing it should not have.

## Revision note — what changed and why

This file is the revision of the first-pass proposal after the red-team
returned **REVISE** with three HIGH findings (`data/decisions/gw5/review.md`).

| Finding | Disposition in this revision |
|---|---|
| **H1** — the decision metric was swapped for one the agent spec does not authorise | **Upheld.** The first pass filed an agent-spec defect to `docs/backlog.md` and then acted on it in the same cycle. CLAUDE.md §Improvement backlog and this agent's own `## Rules` both say such a finding is filed and **never acted on in-cycle** — filing and acting are alternatives, not a sequence. The user has ruled: **hold to spec for GW5.** The objective is the one the spec states — starting-XI EP + captain EP. The auto-sub-aware metric is not authorised for this cycle. Consequence: **transfer 2 (Shaw → Justin) is dropped**; Justin does not enter the squad and Shaw stays. |
| **H2** — the replacement simulation had a real auto-substitution defect | **Upheld and quarantined.** The scratch simulation's legality guard ended `… >= 1 or True`, so it never fired, and an illegal team was "repaired" by deleting the last-added substitute instead of skipping an ineligible one — a 3-DEF XI losing two defenders fielded **nine** players. It understated auto-sub value by **2.11 EP**. The simulation was defective. **It is not the basis of any figure in this document.** Every sim-derived number from the first pass has been deleted and replaced with a recomputation on the spec objective; none survives anywhere in this file, including §2, §3, §5, §7, §9 and §10. |
| **H3** — §3e's "three-way tie" and its ad-hoc tie-break were artefacts of H2 | **Upheld.** The invented tie-break ("prefer the candidate least exposed to the minutes model") is **deleted**. It was unsound on its own terms: it counted sub-0.90 `p_start` rows unweighted, so Dubravka at 0.03 scored the same as Cherki at 0.80; and it penalised `p_start` a third time when `p_start` is already inside `ep_gw` and C18 had already cut it pool-wide this cycle — the double discount **C16** retired. §14 claimed C16 compliance while doing what C16 forbids in a different currency; that row is corrected. On the spec objective the three pair candidates separate cleanly and no tie-break is needed (§3e). |
| **M1** — the Ndiaye rationale inverted A3-MID's own note | Fixed in §13. Foden's ban **frees** minutes; it does not contest them. |
| **M2** — template exposure (checklist 5) never analysed | Added as **§12**. |
| **M3** — the S1 ledger reason rested on §3e | Reason restated on the spec objective in §15. Status and GW unchanged. |
| **L2** — the C4 band table omitted an incoming player | E.Le Fée and Shaw added to the §5 table. |

Everything below is computed on the spec's objective only. The verification
script that produced every figure in §1–§5 reproduces the red-team's
independent recomputation to three decimals on all eight shared quantities
(baseline 337.699; transfer 1 +4.105 / +2.205; transfer 2 marginal +1.013 /
+0.443; best second move +1.853; PLAN pair +5.118 / +2.648; EARMARK +3.143 /
+2.600; banded-floor +4.101 / +1.057). Every one of those quantities survives
the REOPEN re-score unchanged; only the enumeration counts moved, to 1 376
singles and 1 452 second moves.

## 0. Inputs and the single EP metric

| Source | What it fixed |
|---|---|
| `data/decisions/gw4/final.md` STATE | 15 ids, team_value 99.4, bank 0.0, **2 free transfers**, `chips_used: []`, four provisional `chip_plan` rows |
| `data/analysis/gw5/players-{GKP,DEF,MID,FWD}.json` | blend EP, `ep_gw`, `p_start_gw`, `terms`, `rates`. **`players-DEF.json` regenerated by A3-DEF for the REOPEN** |
| `data/analysis/gw5/fixtures.{md,json}` | `lambda_att`, `p_cs`, `band` |
| `data/retro/gw1–gw4.md` | C5, C8, C14, C16 active; **C20 new and binding** |
| `data/suggestions.md` | S1, S2 — read through **S2** |
| `data/raw/gw5/` | snapshot **refetched 2026-09-18T15:19:53Z** for the freshness gate (< 24h at the deadline) |

Per **C14** every move is scored on two *readings of the rates*, not two
metrics. **Blend** = the analysts' `data/analysis/gw5/players-*.json`.
**Prior-only** = the same inputs rerun through `fpl ep` with an explicit
`prior_weight: 1.0` override on every row (scratch output, not written to
`data/analysis/`). Only the rates change; `p_start_gw`, fixtures and the
formula are identical. The rebuild reproduces the prior EP6 column of the
previous run on every GKP, MID and FWD row and on all DEF rows except the five
A3-DEF re-derived (Shaw, Pau, Maatsen, Burn, Botman) — the control that the
rerun moved only what the gate moved.

**Selling prices.** No authenticated `my-team` read was relayed this cycle, so
sell value is reconstructed from purchase prices: GW1's fifteen buys, plus
Tavernier £6.0m (GW2) and Barry £5.5m (GW3). Those purchases sum to exactly
£100.0m, and applying the FPL half-profit rule to GW4's `now_cost` reproduces
GW4's authenticated sell column on **all fifteen rows** — so the reconstruction
is checked, not assumed. Against GW5 prices: Thiago 8.0 → 7.8 is the only move,
giving **pre-transfer Σ sell 99.3 + bank 0.0 = £99.3m** (GW4: 99.4). The one
outgoing player has fallen *below* his purchase price (Ndiaye 6.0 → 5.9), so
his sell price equals `now_cost` whatever the purchase history was — the
reconstruction carries no risk on this transfer.

## 1. Objective — the spec's, used as written

`agents/squad-optimizer.md` §Objective: **maximize Σ over 6 GWs of starting-XI
EP + captain EP (doubled)**. §Transfer rule: **gains < 2 EP → bank the free
transfer**. Both are applied literally throughout this document. Formally, for
each gameweek `k` in GW5–10 the best legal XI is chosen from the 15 by
`ep_gw[k]`, its EP summed, and its maximum added once more for the captain;
the six gameweeks are summed. Baselines for the current squad: **337.699 blend
/ 323.421 prior.**

The first pass declared this objective defective and substituted a simulation.
That substitution is withdrawn (H1), and **its supporting argument was wrong on
its facts.** §1 of the first pass claimed that under the spec's objective *"the
largest 'gain' on the board is replacing Dubravka: +17 to +21 EP6"*. It is not.
The +21.58 figure is the **squad EP6 sum** (352.75 → 374.33 with Tzolakis for
Dubravka) — a quantity the spec never names. On the spec's actual objective,
Dubravka → Tzolakis is worth **+1.308 blend / +0.187 prior**, below the 2.0
gate and correctly refused; and Tzolakis at £4.6m is out of reach in any case.
The spec objective does not have the pathology it was retired for. An artefact
of one metric was attributed to a different metric and used to discard it.

The real limitation of XI-max — that it scores a bench slot at zero and so
cannot price auto-substitute cover — is a genuine observation, and it is
already filed to `docs/backlog.md` from the first pass. It is a finding for the
backlog, not a licence to change the objective mid-cycle. **No further backlog
row is appended for it** — see the REOPEN note for the one unrelated TOOL row
this run did file.

## 2. Premium skeleton — Haaland only, unchanged

Haaland (£15.6m, EP6 38.47 blend / 34.90 prior) is the squad's only player
above £9m. Would £15.6m split score more? Recomputed on the spec objective,
both readings:

| Restructure | Buy | Sell | Δ blend | Δ prior | Bank | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Haaland → Isak (free) | 9.1 | 15.5 | **−14.869** | **−11.690** | 6.4 | never |
| Haaland + Anderson → Isak + Saka (−4) | 18.6 | 21.8 | −2.906 | −7.239 | 3.2 | negative before the hit is charged |
| Haaland + Ndiaye → Isak + B.Fernandes (−4) | 21.1 | 21.4 | +0.211 | +2.744 | 0.3 | positive on both but far below the 6.0 gross a hit demands — refused on the gate |

C15 answered the premium-restructure question NO and round 4 did not reopen it
(≥8.0 band bias +0.30 on n=8, neither replicating nor reversing). Haaland
stays. He is also the only route to the GW9 Triple Captain earmark.

## 3. Swap pass — the audit trail

Pools: every player of the position not already owned, status `a` or `d`,
present in both readings, on the **refreshed** bootstrap — 32 GKP, 131 DEF,
184 MID, 40 FWD. **All 1 376 legal single transfers were enumerated
exhaustively and scored on the spec objective, both readings**, and — after
transfer 1 — **all 1 452 legal second free moves** and **all 1 438 legal third
moves**. The tables below report that arithmetic and
nothing else; no simulation output enters this document.

### 3a. Singles (free) — spec objective, both readings

| Δ blend | Δ prior | Bank | Move | Note |
|---:|---:|---:|---|---|
| **+4.105** | **+2.205** | 0.1 | **Ndiaye → E.Le Fée (SUN, 5.8)** | **taken — first on blend, clears 2.0 on both** |
| +3.665 | −1.325 | 0.5 | Anderson → E.Le Fée | sign flip — C14 |
| +2.942 | −1.107 | 0.2 | Anderson → Schade (BRE, 6.1) | sign flip — C14 |
| +2.383 | +0.142 | 0.2 | Ndiaye → Groß (BHA, 5.7) | fails the gate on prior-only; dominated by Le Fée on both |
| +2.065 | +1.530 | 0.2 | Scott → E.Le Fée | Ndiaye is the better funding side |
| +1.842 | −3.485 | 0.6 | Anderson → Groß | sign flip — C14 |
| +1.823 | −2.760 | 0.3 | Anderson → Stach (LEE, 6.0) | sign flip — C14 |
| +0.945 | −1.968 | 0.0 | Thiago → João Pedro | sign flip — C14; `d` 75%, p_start 0.68 HIGH |
| +0.904 | +0.182 | 0.5 | Richards → Justin (LEE, 4.5) | below the gate on both |
| −0.709 | +3.375 | 0.0 | Scott → Barnes (NEW, 6.0) | prior-only lead, negative on blend |
| −1.785 | +3.161 | 0.0 | Barry → Kostoulas (BHA, 5.5) | prior-only lead, negative on blend |
| +0.051 | +2.164 | 1.6 | Thiago → Wissa (NEW, 6.2) | flat on blend — a funding move, not an upgrade |

**Ndiaye → E.Le Fée is first on blend among all 1 376 singles and the only move
in the top tier positive on both readings**, clearing the 2.0 gate on the blend
(+4.105) **and** on prior-only (+2.205). Nothing else on the board clears 2.0
on both. C14 is satisfied outright: no sign flip, no hit.

Why Ndiaye is the one to sell: his `p_start` fell 0.93 → **0.78** this cycle
(C18, plus the GW4 45-minute hook that broke his streak), taking EP6 25.40 →
**21.17** — last of the five midfielders on both readings. Le Fée has 4/4
starts, the position's leading xG (2.06), penalties and a corner, `p_start`
0.92 flat across all six gameweeks, and EP6 27.02 / 24.43.

Note that **Shaw → Justin does not appear in this table at all**: standing
alone it is infeasible. Shaw sells at 4.4 against bank 0.0 and Justin costs
4.5. It becomes affordable only after transfer 1 leaves 0.1 in the bank, which
is why it is scored as a second move in §3b.

### 3b. The second free transfer — exhaustive, and banked

From the post-transfer-1 squad (bank 0.1), **all 1 452 legal second free moves**
were enumerated on the spec objective:

| Δ blend | Δ prior | Bank | Best second moves |
|---:|---:|---:|---|
| +1.853 | −1.107 | 0.3 | Anderson → Schade (BRE, 6.1) — the board maximum; sign-flips, and C14 bars it |
| +1.342 | +1.357 | 0.0 | Scott → Schade |
| +1.169 | −1.893 | 0.1 | Thiago → João Pedro — sign flip |
| +1.121 | −0.034 | 0.1 | Tarkowski → Guéhi — sign flip |
| **+1.013** | **+0.443** | 0.0 | **Shaw → Justin (LEE, 4.5)** — the first pass's transfer 2 |
| +0.904 | +0.094 | 0.6 | Richards → Justin |

**No second move clears 2.0 on the blend.** The board maximum is +1.853, which
also sign-flips and is barred by C14 independently. Re-run on the refreshed
files, with Shaw at `p_start` 0.32, the board is **identical** — the ordering,
the maximum and the Shaw → Justin marginal all reproduce to three decimals,
because Shaw enters no best XI in the window and so enters the objective at
weight 0 either way. There is therefore **no
spec-conformant second transfer available this week**, and the transfer rule is
unambiguous: *gains < 2 EP → bank the free transfer.*

Shaw → Justin scores **+1.013 blend / +0.443 prior** — roughly half the gate on
the better reading and a fifth of it on the worse. It is dropped. Justin does
not enter the squad; Shaw remains as bench slot 15.

### 3c. A hit (−4) — refused

The hit rule needs the extra transfer's **gross ≥ 6.0**. The first paid move
would be the third. Sweeping all 1 438 legal third moves from a
two-transfer squad, the best is **Anderson → Schade at +1.853 blend / −1.107
prior** — under a third of the threshold and sign-flipping besides. Since no
*free* second move even reaches 2.0, a paid third is not close. **No hit.**

### 3d. Rejected alternatives worth naming

| Move | Δ blend | Δ prior | Why not |
|---|---:|---:|---|
| Anderson + Thiago → Cherki + Wissa | +3.143 | +2.600 | GW4's earmarked pair, re-derived — loses to the plan on the blend; §3e |
| Anderson + Shaw → E.Le Fée + Justin | +4.711 | −0.504 | the first pass's "RIVAL" — sign-flips as a package; §3e |
| Ndiaye + Thiago → Cherki + Wissa | — | — | **infeasible by £0.3m** — the F2 price bleed GW4 flagged. Thiago fell 7.9 → 7.8 |
| Ndiaye → Cherki | +3.413 | +3.684 | **infeasible by £1.9m** |
| Dubravka → Tzolakis | +1.308 | +0.187 | below gate on both, and **infeasible** — Tzolakis £4.6m against a £4.1m budget. The £17–21 headline was the squad-EP6-sum artefact of §1 |
| Dubravka → Steele / Forster (the only reachable GK2s) | +0.000 | +0.000 | worth exactly nothing: both are themselves backups (`p_start` 0.04 and 0.02, EP6 0.74 and 0.42) |
| Shaw → Davis (IPS, £4.0m) | +0.421 | +0.000 | far below gate; promoted-club defender, every defensive row banded |
| Shaw → O'Shea (IPS, £4.0m) | +0.034 | +0.000 | same, and smaller |
| Tarkowski → Guéhi *(as second move)* | +1.121 | −0.034 | below gate and sign-flips. Legal only after Ndiaye leaves — with Ndiaye held it would be a fourth MCI asset |

### 3e. The three pair candidates — no tie, and no tie-break

The first pass reported a three-way tie among pairs and invented a tie-break to
break it. **Both were artefacts of the defective simulation (H2/H3).** On the
spec objective there is no tie: one candidate leads on **both** readings.

| Candidate (pair total v baseline) | Δ blend | Δ prior | Second leg's marginal |
|---|---:|---:|---:|
| **PLAN pair** — Ndiaye + Shaw → E.Le Fée + Justin | **+5.118** | **+2.648** | +1.013 / +0.443 |
| RIVAL — Anderson + Shaw → E.Le Fée + Justin | +4.711 | **−0.504** | — sign-flips as a package, C14 |
| EARMARK — Anderson + Thiago → Cherki + Wissa *(GW4's)* | +3.143 | +2.600 | — |

The PLAN pair leads on the blend and on prior-only; the RIVAL sign-flips and
C14 bars it; the EARMARK trails on both. **Every stated criterion selects the
plan's pair over the other two — no new criterion is required, and none is
used.** The deleted tie-break is not merely unnecessary; it was unsound, for
the reasons recorded in the Revision note.

What actually decides this week is one level up: the PLAN pair's **second leg**
is +1.013, below the 2.0 gate, so the pair is not taken either. The decision
collapses to the best single (§3a), which is transfer 1, with the second free
transfer banked.

This also settles the GW4 earmark honestly. The GW4 ledger banked a free
transfer naming "Anderson+Thiago→Cherki+Wissa +5.06 / +3.46" as its purpose.
Re-derived on this week's data and on the spec objective that pair is **+3.143
/ +2.600** — behind the plan on both readings. Abandoning the earmark is
justified by those numbers, not by exposure counting. Its first leg
(Anderson → Cherki, +3.092 blend / +0.436 prior) is infeasible anyway without
selling Thiago, and its second (Thiago → Wissa, +0.051 / +2.164) is flat on the
blend.

**Ticker check** (never transfer for one good fixture what turns bad in two):
Le Fée's window is MCI(A), BHA(H), BOU(A), LEE(H), COV(A), CHE(H) — his GW5 is
the *worst* row in it, so the move is bought on the back five, not the front
one. Not fixture-front-loaded.

## 4. Why one transfer and not two

The first pass took a second transfer that fails the spec's gate (+1.013
against 2.0) on the strength of a metric the spec does not define and an agent
may not substitute mid-cycle. That is H1, and it is upheld.

The substantive observation behind it survives as a *backlog item*, and should
be recorded plainly rather than acted on: Shaw is bench slot 15, and XI-max
scores a player who never starts at zero, so it prices his replacement at zero
too. Shaw is the squad's auto-substitute cover at `p_start` **0.32** this week
(0.66–0.72 after) with a **50%** injury flag, and Justin is `p_start` 0.90, 4/4
full 90s, DefCon 35 at £4.5m, EP6 22.41 against Shaw's **11.79**. Under a metric
that priced auto-subs the move would very likely clear its gate.

The REOPEN sharpens this rather than changing it. Shaw's `chance_of_playing`
fell 75% → 50% and his EP6 12.81 → 11.79, and the Shaw → Justin marginal did
**not** move: it is +1.013 / +0.443 on the refreshed files exactly as before,
because Shaw appears in the best XI in none of GW5–10 on either reading. A
bench player's decline is invisible to XI-max by construction. The cover got
worse and the metric did not notice — which is the filed finding restated with
a fresh example, not a reason to score it differently this week.

But that metric does not exist in the spec, the one attempt to build it this
cycle was **defective** (H2), and the rule for a finding of this kind is the
backlog, not the current gameweek's transfers. The row is filed. The transfer
is not made.

The cost of holding to spec is bounded and stated: if the auto-sub reading is
the better one, this decision gives up on the order of 1–3 EP over the window,
and it leaves Shaw's flag — now **50%**, cut from 75% at the gate — in the
squad for a third gameweek, so the GW19
Bench Boost stays blocked behind both the GK2 slot and the fifth defender. Both
repairs route to the **GW8 wildcard**, which is 3 gameweeks away and needs no
transfer budget. Against that, banking carries a second free transfer into GW6
with **2 FTs in hand**, which is the natural funding for exactly this repair
if the wildcard slips.

## 5. C4 / C12 — the banded promoted-club rows

Selected assets whose largest clean-sheet row comes from a promoted-club
fixture — the configuration C4 forbids. Both incoming and outgoing sides are
listed (L2: the first pass's table omitted E.Le Fée, whose largest row **is**
banded):

| Player | Pos | Largest P(CS) row | Value | Banded |
|---|---|---|---:|---|
| Gabriel, Raya | DEF, GKP | GW10 ARS v HUL (H) | 0.52 | **yes** |
| Tarkowski | DEF | GW10 EVE v COV (H) | 0.40 | **yes** |
| Thiaw | DEF | GW5 NEW v HUL (H) | 0.38 | **yes** |
| **E.Le Fée** *(incoming)* | MID | **GW9 SUN v COV (A)** | **0.31** | **yes** |
| Shaw *(retained)* | DEF | GW6 MUN v TOT (H) | 0.39 | no |
| Richards | DEF | GW9 CRY v TOT (A) | 0.27 | no |

No override reaches `P(CS)`, so the discount was applied by rebuilding
`fixtures.json` with **all 34 banded rows at their −15pp lower bound** and
rerunning `fpl ep` for all four positions. Effect on EP6: Gabriel 28.79 →
28.24, Raya 21.89 → 21.32, Tarkowski 25.82 → 24.16, Thiaw 22.98 → 21.90,
E.Le Fée 27.02 → **26.88**, Tzolakis 22.24 → **19.00**.

Re-scoring on that pessimistic fixture set, spec objective:

| | central | all-banded-low |
|---|---:|---:|
| Transfer 1 — Ndiaye → E.Le Fée | +4.105 | **+4.101** |
| Shaw → Justin (marginal, not taken) | +1.013 | +1.057 |

**Transfer 1 clears its gate at the band's floor and the banked second transfer
stays below it**, and Gabriel remains the best defender in the game. The
decision is invariant to the band, which is the strongest available answer to
C4: the prohibited configuration exists in the squad, but no selection this
week rests on it. E.Le Fée's own banded row costs him 0.14 EP6 at the floor —
immaterial to a +4.1 transfer.

The band did change one thing: Tzolakis leads GKP on the central read (22.24)
and falls to fourth (19.00) at the floor, because every Hull defensive row is
banded. Any future GK2 move must be re-tested this way rather than taken off
the headline number.

## 6. Squad (15) — Σ sell £99.2m + bank £0.1m = team value £99.3m

`GW5 EP` and `EP6` are the code's `ep_gw[0]` and `ep_total6`. Nothing is
recomputed here; this table is the raw material for `fpl calibrate --round 5`.

| Slot | Pos | Player | Id | Club | Buy | Sell | GW5 EP | EP6 | EP6 prior | p_start | Unc | DefCon share | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| 1 | GKP | Raya | 1 | ARS | 6.0 | 6.0 | 3.310 | 21.89 | 20.74 | 0.94 | LOW | 0.00 | XI |
| 2 | DEF | Thiaw | 445 | NEW | 5.0 | 5.0 | 4.450 | 22.98 | 24.72 | 0.90 | LOW | 0.20 | XI |
| 3 | DEF | Tarkowski | 229 | EVE | 6.0 | 6.0 | 4.425 | 25.82 | 24.86 | 0.92 | LOW | 0.22 | XI |
| 4 | DEF | Gabriel | 4 | ARS | 8.0 | 8.0 | 4.423 | 28.79 | 29.65 | 0.93 | LOW | 0.17 | XI |
| 5 | MID | Mbeumo | 427 | MUN | 8.0 | 7.9 | 5.212 | 31.08 | 27.56 | 0.92 | LOW | 0.02 | XI · **Vice** |
| 6 | MID | Tavernier | 68 | BOU | 6.0 | 6.0 | 4.911 | 29.32 | 25.65 | 0.92 | LOW | 0.05 | XI |
| 7 | MID | Scott | 69 | BOU | 6.0 | 6.0 | 4.173 | 24.95 | 22.90 | 0.92 | LOW | 0.22 | XI |
| 8 | MID | Anderson | 481 | MCI | 6.5 | 6.3 | 4.003 | 23.35 | 25.76 | 0.90 | LOW | **0.28** | XI |
| 9 | FWD | Haaland | 411 | MCI | 15.5 | 15.5 | 6.721 | 38.47 | 34.90 | 0.93 | LOW | 0.01 | XI · **Captain** |
| 10 | FWD | Thiago | 106 | BRE | 8.0 | 7.8 | 4.617 | 26.15 | 27.50 | 0.92 | LOW | 0.02 | XI |
| 11 | FWD | Barry | 249 | EVE | 5.5 | 5.5 | 4.431 | 26.05 | 22.87 | 0.91 | LOW | 0.01 | XI |
| 12 | GKP | Dubravka | 497 | TOT | 4.0 | 4.0 | 0.116 | 0.66 | 0.66 | 0.03 | HIGH | 0.00 | Bench GK |
| 13 | MID | E.Le Fée | 542 | SUN | 5.8 | 5.8 | 3.884 | 27.02 | 24.43 | 0.92 | LOW | 0.08 | Bench 1 · **IN** |
| 14 | DEF | Richards | 202 | CRY | 5.0 | 5.0 | 2.870 | 19.26 | 20.64 | 0.90 | LOW | 0.28 | Bench 2 |
| 15 | DEF | Shaw | 423 | MUN | 4.5 | 4.4 | 1.015 | 11.79 | 12.09 | 0.32 | HIGH | 0.07 | Bench 3 · retained |
| | | **Total** | | | 99.8 | **99.2** | | **357.58** | 344.93 | | | | |

Constraints: **2 GKP / 5 DEF / 5 MID / 3 FWD** ✓ · Σ sell 99.2 + bank 0.1 =
team value 99.3 ✓ · club counts ARS 2, EVE 2, BOU 2, MCI 2, MUN 2, CRY 1,
BRE 1, TOT 1, NEW 1, SUN 1 — all ≤ 3 ✓ · 15 unique ids ✓ · funding exact:
sell 5.9 = buy 5.8 + 0.1 to bank, bank 0.0 → 0.1 ✓.

**Two non-LOW rows remain**: Dubravka (`p_start` 0.03) and Shaw (**0.32**, status
`d`, **50%**, news 2026-09-11 — `news_added` did not move when the percentage
did, which is the frozen-`news_added` quirk already filed). Both are bench slots behind a 3-defender XI, and
both repairs are routed to the GW8 wildcard (§11, §12). This is the cost of
holding to spec, stated rather than absorbed.

## 7. Starting XI — 3-4-3 (unchanged)

Dropping transfer 2 changes nothing in the XI: Shaw was bench slot 15 before
the revision and Justin would have entered at bench slot 13. **Neither was ever
in the starting XI**, so the XI, the captain, the vice, the formation and the
predicted GW5 total are identical to the first pass.

| Slot | Player | Club | Pos | GW5 fixture | GW5 EP |
|---:|---|---|---|---|---:|
| 1 | Raya | ARS | GKP | BHA (A) | 3.310 |
| 2 | Thiaw | NEW | DEF | HUL (H) | 4.450 |
| 3 | Tarkowski | EVE | DEF | IPS (H) | 4.425 |
| 4 | Gabriel | ARS | DEF | BHA (A) | 4.423 |
| 5 | Mbeumo **(V)** | MUN | MID | FUL (A) | 5.212 |
| 6 | Tavernier | BOU | MID | LIV (H) | 4.911 |
| 7 | Scott | BOU | MID | LIV (H) | 4.173 |
| 8 | Anderson | MCI | MID | SUN (H) | 4.003 |
| 9 | Haaland **(C)** | MCI | FWD | SUN (H) | 6.721 |
| 10 | Thiago | BRE | FWD | CHE (H) | 4.617 |
| 11 | Barry | EVE | FWD | IPS (H) | 4.431 |
| | **XI total** | | | | **50.68** |
| | + captain (Haaland) | | | | 6.721 |
| | **Predicted GW5** | | | | **57.40** |

Formation 3-4-3: 1 GK, 3 DEF, 4 MID, 3 FWD ✓ (≥3 DEF, ≥2 MID, ≥1 FWD). Exactly
one captain and one vice, both in the XI ✓. Re-derived from the revised
15 by the spec objective at k=0 **on the refreshed files**, this is the best
legal XI: the eleven names, the formation, the order and the 57.397 total are
unchanged, because the only squad row the gate moved is Shaw and he is outside
the XI on every reading. Per **C16**, the XI
and the bench are ordered on **undiscounted** EP; the certainty multipliers are
confined to the captaincy in §8.

The first pass reported an auto-sub-inclusive expectation of 61.02 for this XI.
**That figure came from the defective simulation and is withdrawn.** 57.40 is
the prediction, and 57.40 is what `calibrate --round 5` will score.

### C20 — the XI/bench boundary, re-checked on the revised squad

C20 extends C8's ≤ 0.25 EP near-tie DefCon-floor tie-break from the bench
ordering to the XI/bench line. With Justin gone the boundary has **one** in-band
pair, not two:

| Boundary pair | Gap | DefCon share | In C20's ≤ 0.25 band? | Resolution |
|---|---:|---|---|---|
| Anderson 4.003 (XI) v **E.Le Fée** 3.884 (bench 1) | **0.119** | 0.28 v 0.08 | **yes** | **Anderson** — higher floor |
| Scott 4.173 (XI) v E.Le Fée 3.884 | 0.289 | — | no | outside the band; EP decides |
| Anderson 4.003 (XI) v Richards 2.870 (bench 2) | 1.133 | — | no | outside the band; EP decides |

The single in-band pair resolves to **Anderson**, who carries the squad's
highest DefCon share (0.281, DC 45 and minutes rising 62 → 90). The tie-break
and the EP order agree, so **C20 changes nothing this week — but it was applied
and the result is recorded.** The first pass's second in-band pair
(Anderson v Justin, 0.086) no longer exists, and the sim-derived confirmation
it cited ("Justin-in costs −0.104, Le Fée-in costs −0.569") is withdrawn with
the rest of H2.

This is the same boundary that went against us in three of four rounds and cost
3 points at GW4, where Anderson was the *benched* player with the higher floor.
This week he is the one kept in.

## 8. Captaincy — unchanged

Per **C16** the certainty multipliers (LOW 1.00 / MED 0.92 / HIGH 0.80) apply
here and nowhere else.

| Rank | Player | GW5 fixture | EP | Unc | × certainty | Gap to #1 | EP prior-only |
|---:|---|---|---:|---|---:|---:|---:|
| 1 | **Haaland** | SUN (H) | 6.721 | LOW | **6.721** | — | 6.104 |
| 2 | Mbeumo | FUL (A) | 5.212 | LOW | 5.212 | −1.509 | 4.621 |
| 3 | Tavernier | LIV (H) | 4.911 | LOW | 4.911 | −1.810 | 4.297 |
| 4 | Thiago | CHE (H) | 4.617 | LOW | 4.617 | −2.104 | 4.834 |
| 5 | Thiaw | HUL (H) | 4.450 | LOW | 4.450 | −2.271 | 4.791 |

**Captain Haaland**, 1.509 clear of the field — three times the 0.5 tie band, so
no suggestion and no variance argument enters. The gap holds on prior-only
(6.104 v 4.834). MCI v SUN (H) is his second-best fixture in the window
(λ_att 2.10), and every candidate is LOW, so the multipliers change no ordering.

**Vice Mbeumo** — highest remaining EP, on a different fixture from the captain
(FUL v MUN, Sunday 15:30 UTC, after MCI v SUN at 13:00), so a Haaland non-start
is known before Mbeumo's match begins. Le Fée is the only squad member sharing
Haaland's fixture and he is on the bench.

## 9. Bench order — revised

| Slot | Player | Pos | GW5 fixture | GW5 EP | Gap to slot above | DefCon share |
|---:|---|---|---|---:|---:|---:|
| 12 | Dubravka | GKP | AVL (H) | 0.116 | — (backup GK, fixed slot) | 0.00 |
| 13 | E.Le Fée | MID | MCI (A) | 3.884 | — | 0.08 |
| 14 | Richards | DEF | LEE (A) | 2.870 | **1.014** | 0.28 |
| 15 | Shaw | DEF | FUL (A) | 1.015 | **1.855** | 0.07 |

**C8 does not bite anywhere on this bench.** The 13/14 gap is **1.014** and the
14/15 gap is **1.855** — both far outside C8's ≤ 0.25 band, so undiscounted EP
decides the whole order and no DefCon tie-break is invoked. This is a change
from the first pass, where Justin at 3.917 sat 0.033 above Le Fée and C8 did
bite; with Justin withdrawn that near-tie no longer exists. Richards sits at 14
despite the highest floor share of the three because EP, not floor, orders an
out-of-band bench.

The order is the EP order and needs no further argument. The first pass's claim
that all six outfield permutations were simulated, and that the worst costs
0.601 expected points, rested on the defective simulation and is **withdrawn**.

Two defensive covers (slots 14 and 15) sit behind a 3-defender XI, where any
defender's absence must be filled by a defender to keep the formation legal.
Slot 15 is Shaw at `p_start` **0.32** with a live **50%** flag, which is the
weakest part of this squad and the honest cost of §4. The REOPEN widened the
14/15 gap from 1.285 to **1.855** and so pushed C8 *further* out of band; the
bench order is unchanged and no DefCon tie-break is invoked.

## 10. Transfers

| Out | In | Sell | Buy | Cost |
|---|---|---:|---:|---:|
| Ndiaye (MCI, MID, id 237) | E.Le Fée (SUN, MID, id 542) | 5.9 | 5.8 | **0** (free transfer 1 of 2) |

One free transfer spent, **one banked**; hit 0. Bank 0.0 → 0.1. One further free
transfer accrues for GW6, so `free_transfers_banked: 2` (available at the GW6
deadline, under the cap of 5).

Gate arithmetic, spec objective, both readings: transfer 1 **+4.105 / +2.205**
against the 2.0 gate — clears on both. Best available second free move
**+1.853 / −1.107** — fails the gate on the blend and sign-flips, so C14 bars
it independently; every other second move is smaller. Best third move (paid)
**+1.853** against the 6.0 gross a −4 hit demands — refused.

**Banking is the rule's own answer, not a fallback.** GW4 banked because nothing
cleared the gate; this week exactly one move clears it and nothing else does.
The international break means the banked transfer sits idle for 22 days
(GW6 deadline 2026-10-10T10:00Z), which is a real cost — but the transfer rule
does not have an exception for long breaks, and the two FTs it produces are the
natural funding for the Shaw and Dubravka repairs if the GW8 wildcard slips.

## 11. Chips — none played (`chip: null`)

**C5 binds: justify any Triple Captain on Haaland's fixture-independent EP
alone.** His window is 6.721 / 5.978 / 6.688 / 6.317 / **6.995** / 5.769, mean
6.412. GW5 is his second-best row and sits 0.274 below GW9. The earmark holds.

| GW | Fixture | Haaland EP | Above window mean | Banded | Verdict |
|---:|---|---:|---|---|---|
| 5 | SUN (H) | 6.721 | +0.309 | no | second-best; does not displace GW9 |
| 7 | IPS (H) | 6.688 | +0.276 | **yes** (promoted) | ineligible under C5/C4 |
| **9** | **BHA (H)** | **6.995** | **+0.583** | no | **earmark held** |

A2 concurs and the margin has widened since GW4 (MCI λ_att 2.27 at GW9 against
2.10 at GW5). Forward earmarks, all provisional, all inside their bootstrap
windows (wildcard/freehit GW2–19, bboost/3xc GW1–19):

| Chip | Earmark | Basis |
|---|---|---|
| wildcard | GW8 | carried, and now carrying **two** repairs: Dubravka is dead weight and Shaw is a flagged fifth defender at `p_start` 0.32. EVE's ticker turns from GW7 (P(CS) 0.21, 0.18) |
| 3xc | GW9 | MCI v BHA (H), Haaland 6.995, band-free, the window maximum. BHA are 20th on defence with all six rows P(CS) ≤ 0.21 |
| freehit | GW16 | placeholder — no blank or double inside GW5–10 |
| bboost | GW19 | last set-1 gameweek; blocked until **both** the GK2 and the fifth-defender slots are repaired |

One chip per GW ✓ (wildcard GW8 and 3xc GW9 are distinct) · freehit
non-consecutive ✓. This table is a forecast; `chip: null` activates nothing this
week and `chip_plan` is its only machine-readable form.

## 12. Template exposure (checklist item 5)

Checklist item 5 requires the differential position to be **deliberate and
stated**. The first pass did not mention ownership once, and the retro has
carried **MED-E template fades** unresolved for three rounds. Recorded here.

Unheld at ≥30% ownership (the whole list; nothing at ≥30% is omitted):

| Owned | Player | Pos | Price | Note |
|---:|---|---|---:|---|
| 70.7% | João Pedro | CHE FWD | £7.8 | status `d`, 75%, news 16 Sep |
| 50.2% | Calafiori | ARS DEF | £5.8 | fit |
| 40.5% | B.Fernandes | MUN MID | £12.0 | fit |
| 39.4% | Rogers | CHE MID | £7.7 | fit |
| 34.8% | Szoboszlai | LIV MID | £7.0 | fit |

Held above 20%: Haaland 73.1%, Raya 41.1%, Gabriel 23.1%, Mbeumo 21.9%.
Everything else is a differential: the **entire midfield** sits below 22% —
Mbeumo 21.9% is its most-owned member, then Tavernier 6.2%, Scott 5.8%,
Anderson 4.2% and the incoming Le Fée 3.6%.

**The exposure this creates.** Only Haaland is a genuine template hold, and he
is captained, so on a Haaland haul we match the field rather than gain on it.
Every point of rank movement therefore has to come from four sub-7%-owned
midfielders firing in the same week — high upside, and a mirror-image downside:
five heavily-owned players can each score without us, and a
B.Fernandes-or-Rogers haul costs rank even in a good week for our own squad.
With the top five unheld names spread across CHE, ARS, MUN, CHE and LIV there is
no single fixture that closes the gap, so the variance is structural rather than
week-specific.

**Is it deliberate? Partly — and now stated.** The differential midfield is a
by-product of a £15.6m striker plus a 5-man defence, not a chosen stance: the
budget left after Haaland cannot reach B.Fernandes at £12.0m. Selling Ndiaye
(7.5% owned) for Le Fée (3.6%) makes it marginally more differential this week,
which the EP margin (+4.105 / +2.205) justifies on its own. The two rows worth
naming as **accepted** risk are Calafiori (50.2%, £5.8m, an ARS defender we
could reach) and João Pedro (70.7%, but `d` at 75% and therefore not a
deadline-day buy). **Recommended for final.md:** record the list above as an
accepted rank-volatility risk, and name **Calafiori** as the single template
hole to close at the GW8 wildcard, where it competes with the GK2 and Shaw
repairs for the same wildcard slots.

## 13. Rationale summary

One thing was wrong with the squad that a free transfer could fix this week,
and it is fixed at no points cost with £0.1m left in the bank.

**Ndiaye** was the fifth-best midfielder on both readings and falling: C18 cut
his `p_start` 0.93 → 0.78 after the GW4 45-minute hook broke a three-start
streak. His analyst note (`inputs-MID.json`, id 237) reads *"Foden ban frees
minutes, Doku returns"*, and the raw data confirms it for the gameweek being
scored: **Foden is suspended until 17 Oct**, so he misses GW5 and GW6, and Doku
is out with a calf injury expected back 20 Sep — **after this deadline**. City's
midfield is therefore *less* contested in GW5, not more. (The first pass
rendered this as minutes "contested", inverting the analyst's own note; M1.)
That cuts the other way on the sale, and the sale still stands comfortably:
re-scoring with a phased Ndiaye `p_start_gw` of `[0.90, 0.88, 0.82, 0.78, 0.78,
0.78]` leaves transfer 1 at **+3.851**, still nearly twice the gate, and Le Fée
still leads the position on both readings. What sells Ndiaye is Le Fée, not
Ndiaye's minutes: 4/4 starts, the position's leading xG (2.06), penalties, a
corner, `p_start` 0.92 flat across all six gameweeks, EP6 27.02 / 24.43 against
21.17, for £0.1m less.

**Shaw** is the squad's remaining weakness — a **50%**-flagged fifth defender at
`p_start` **0.32** in the last bench slot — and he is **not** fixed this week,
because the move that fixes him scores +1.013 against a 2.0 gate and the
transfer rule says bank. That is the correct application of the spec, and §4
records both the reasoning behind wanting the move and the reason it is not
taken.

Neither the move made nor the move declined is a punt on one fixture. Le Fée's
GW5 (MCI away) is the worst row in his own window, so he is bought on the back
of the horizon rather than the front of it.

Three disciplines did real work. **C14** killed five of the ten best-looking
singles outright — Anderson → E.Le Fée, Anderson → Schade, Anderson → Groß,
Anderson → Stach and Thiago → João Pedro all gain on the blend and lose on
prior-only. **The transfer rule** banked the second free transfer against a
board whose best legal second move is +1.853. **C4's band** was applied by
rebuilding the fixture file at the −15pp floor and rerunning the model; the
transfer survives it at +4.101, which is the honest form of the answer rather
than an assertion that the band does not matter.

What is left unfixed is **Dubravka and Shaw**, the squad's only two sub-0.90
`p_start` rows. No playing keeper is reachable under £4.1m — the only two
affordable alternatives, Steele and Forster, are backups themselves at EP6 0.74
and 0.42 and score +0.000 — and Shaw's replacement fails the transfer gate. Both
repairs need headroom this squad does not have and stay routed to the GW8
wildcard, with two banked free transfers as the fallback if it slips.

## 14. Corrections compliance

| C# | Requirement | Where applied |
|---|---|---|
| C5 | TC justified on Haaland's fixture-independent EP alone, or deferred | §11 — GW5 6.721 below GW9 6.995; earmark held, `chip: null` |
| C8 | near-tie ≤ 0.25 bench ordering broken on DefCon floor share | §9 — **no bench pair is in band** (gaps 1.014 and 1.855), so EP orders the bench and C8 is not invoked. Recorded as checked, not as applied |
| C14 | gross gain on prior-only as well as blend; never a hit whose sign flips | §3 — every single, pair and third move carries both readings; five top-tier singles and the best second move rejected on sign flip; no hit taken |
| C15 | premium restructure answered NO, not deferred | §2 — re-tested on the spec objective, both readings, and closed |
| C16 | certainty multipliers on the captain only; XI and bench on undiscounted EP; `p_start` never discounted twice | §7, §8, §9 — and the first pass's §3e tie-break, which discounted `p_start` a third time behind `ep_gw` and C18, is **deleted** (H3). The first pass claimed this row while violating it in a different currency; that is corrected here |
| **C20** | **C8's tie-break extended to the XI/bench boundary** | **§7 — one in-band pair (Anderson v E.Le Fée, gap 0.119), resolved on DefCon floor share to Anderson; EP order agrees** |
| C4 / C12 | promoted-club band; no selected player's largest defensive term from a banded row | §5 — five assets engaged including the incoming Le Fée; all-banded-low rerun shows the decision is invariant (+4.101) |
| C18 | (A3's) `p_start` cuts carried into selection, not argued with | §3a, §13 — Ndiaye 0.78 is carried as given; the M1 sensitivity check is reported as a bound, not substituted for it |

## 15. Suggestions

Read data/suggestions.md through S2

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 4 | standing | Ndiaye half **completed**: Ndiaye (EP6 21.17, `p_start` cut 0.93 → 0.78 under C18, last of five MIDs on both readings) → E.Le Fée (27.02 / 24.43, leading position xG 2.06, pens + CK, 0.92 flat across the window), **+4.105 blend / +2.205 prior on the spec objective** — first on blend among all 1 376 legal singles and the only top-tier move positive on both readings, so the optimizer reached it unaided and the steer broke no tie; EP6 delta of the suggestion itself 0.00. Anderson half **available and declined on the merits, not on feasibility**: two legal pairs exit him, and both lose to the plan's pair on the spec objective — Anderson+Shaw → E.Le Fée+Justin **+4.711 blend / −0.504 prior** (sign-flips as a package, so C14 bars it independently) and Anderson+Thiago → Cherki+Wissa **+3.143 / +2.600**, against the plan pair's **+5.118 / +2.648**. The plan leads on both readings, so no tie-break is needed or used. The single best Anderson exit, Anderson → E.Le Fée **+3.665 / −1.325**, sign-flips and is refused under C14; the next, Anderson → Schade **+2.942 / −1.107**, does the same. The suggestion is explicitly about **ceiling**, and that is answered directly: no Anderson exit reachable this week raises the six-gameweek ceiling — every one of them lowers it on at least one reading. Anderson also holds the squad's highest DefCon share 0.281 and C20 kept him in the XI on it, which is a floor argument and is recorded as secondary. Stays standing until the Anderson half closes; revisit at the GW8 wildcard, when the GK2 and Shaw repairs free the same decision from the transfer budget |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |

No malformed rows. No withdraw rows. No row expired.

## STATE

```yaml
# Convention (as GW2-GW4): free_transfers_banked = free transfers available at
# the NEXT (GW6) deadline. One of this GW's two free transfers was spent
# (Ndiaye -> E.Le Fee); one was banked, and one new FT accrues for GW6, giving
# 2 (cap 5). team_value = squad sell value 99.2 + bank 0.1. Sell prices are
# reconstructed from purchase prices (GW1 fifteen + Tavernier GW2 + Barry GW3,
# sum exactly 100.0) via the FPL half-profit rule; the reconstruction
# reproduces GW4's authenticated my-team sell column on all fifteen rows. No
# authenticated my-team read was relayed this cycle. Ndiaye had fallen below
# his purchase price, so his 5.9 sell equals now_cost regardless of history.
gw: 5
team_id: 8455344
team_value: 99.3
bank: 0.1
free_transfers_banked: 2
chip: null
chips_used: []
transfers_made:
  - {out: Ndiaye, in: E.Le Fée, cost: 0}
chip_plan:
  - {chip: 3xc, gw: 9, status: provisional}
  - {chip: wildcard, gw: 8, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 1, name: Raya, position: 1, captain: false, vice: false}
  - {id: 445, name: Thiaw, position: 2, captain: false, vice: false}
  - {id: 229, name: Tarkowski, position: 3, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 4, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 5, captain: false, vice: true}
  - {id: 68, name: Tavernier, position: 6, captain: false, vice: false}
  - {id: 69, name: Scott, position: 7, captain: false, vice: false}
  - {id: 481, name: Anderson, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: true, vice: false}
  - {id: 106, name: Thiago, position: 10, captain: false, vice: false}
  - {id: 249, name: Barry, position: 11, captain: false, vice: false}
  - {id: 497, name: Dubravka, position: 12, captain: false, vice: false}
  - {id: 542, name: E.Le Fée, position: 13, captain: false, vice: false}
  - {id: 202, name: Richards, position: 14, captain: false, vice: false}
  - {id: 423, name: Shaw, position: 15, captain: false, vice: false}
```
