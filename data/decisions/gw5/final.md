# GW5 Final Decision (2026/27)

## CORRECTION - THE GW5 PLAN WAS NEVER EXECUTED (recorded post-deadline, 2026-09-18)

Read this before anything else in this file. **Everything below this section is
the pre-deadline prediction record, preserved verbatim for calibration. It
describes a team that was never fielded.** The single exception is the STATE
block at the end of the file, which has been REPLACED to describe reality: the
fifteen that actually played, no transfers, and the unused free transfers
carried forward. That block is what the GW6 cycle and `fpl plan` read, so it
must be true rather than aspirational.

What happened:

- **Nothing was POSTed.** The authenticated FPL session had expired. `auth-check`
  was attempted twice at the team-executor step and failed both times, and no
  credential re-capture completed before the GW5 deadline
  (**2026-09-18T17:30:00Z**), which has now passed. No transfer POST, no lineup
  POST. The window is closed.
- **The transfer did not happen.** Ndiaye (id 237) was **not** sold and
  **E.Le Fee (id 542) was never bought** - he has never been owned by this entry.
  Ndiaye remains in the squad. `fpl entry --gw 5 --team-id 8455344` reads
  `last_deadline_total_transfers: 2` (the GW2 Tavernier and GW3 Barry moves),
  confirming no third transfer was ever registered.
- **The team that played GW5 is GW4's, carried forward by FPL.** The XI, captain,
  vice and bench order set out below - the 3-4-3 with Thiaw and Gabriel shuffled
  and Mbeumo as vice - were never set. The authoritative record,
  `uv run python -m fpl picks --gw 5 --team-id 8455344 --event 5`, returns the
  GW4 fifteen in GW4's slot order, captain Haaland (411), vice Gabriel (4), no
  active chip. It matches `data/decisions/gw4/final.md`'s `picks:` block on all
  fifteen ids, all fifteen slots and both armbands, with no discrepancy.
- **Both free transfers went unused** and carry forward: 3 available at the GW6
  deadline.

### The GW5 retro must attribute this to EXECUTION, not to the model

**The 57.397 GW5 prediction recorded below is a prediction for a squad and an XI
that never took the field. The entire prediction-versus-actual gap for GW5 is an
EXECUTION failure - an expired credential and a missed deadline - and must be
attributed as such. It is NOT model error.**

Binding consequences for `agents/retro-analyst.md` on GW5:

- Do **not** raise a correction (`C<n>`) against A2 (fixture-analyst), A3
  (player-analyst), A4 (squad-optimizer) or A5 (red-team) on the strength of
  GW5's score. Their outputs were never tested by a real gameweek.
- `fpl calibrate --round 5` joins the gw5 EP predictions to the round's actuals.
  Those predictions stand and remain fair game as **per-player** minutes and rate
  calibration for players who actually played. But every **squad-level**
  aggregate - predicted versus actual total, captain hindsight, XI and bench
  decisions - compares a counterfactual team against a real scoreline and is
  **void as a model-accuracy signal**. E.Le Fee's row in particular is a
  prediction for a player this entry did not own.
- The one legitimate GW5 finding is the execution failure itself, logged to
  `docs/backlog.md` (GW5 / ORCH / WORKFLOW): `auth-check` runs only at the
  team-executor step at the end of the cycle, so credential expiry surfaces
  minutes before the deadline with no time to recover.

### Effect on the Suggestions ledger

The `## Suggestions` ledger below is **left exactly as written** - S1 standing
(GW4), S2 rejected (GW4). Disposition belongs to the squad-optimizer, and this is
a record correction rather than an optimizer run, so no row is re-disposed here.

**But S1's recorded reason is now false in fact.** It states the Ndiaye half was
*completed*; it was not - Ndiaye was never sold and E.Le Fee was never bought.
**The next optimizer must re-read S1 as still fully open**, both halves
outstanding, and dispose it on that basis.

---

Deadline **2026-09-18T17:30:00Z**. Horizon **GW5–GW10**.
Source: `data/decisions/gw5/squad-proposal.md` (REVISED · REOPEN re-score),
`data/decisions/gw5/review.md` (verdict REVISE, three HIGH, all closed).

**ONE transfer, free: OUT Ndiaye (MCI, id 237, sell £5.9m) → IN E.Le Fée
(SUN, id 542, £5.8m). Second free transfer BANKED. Hit 0. Bank £0.1m.
3-4-3, Haaland (C), Mbeumo (V). Predicted GW5 57.397. No chip.**

## Freshness gate — PASS

`uv run python -m fpl flags --gw 5 --ids 1,4,229,202,68,427,69,411,106,249,497,481,445,423,542`
refreshed at **2026-09-18T15:37:37Z**, ~1h52m before the deadline.

Baseline: the bootstrap snapshot the current analysis files were built on,
fetched **2026-09-18T15:19:53Z** (archived at
`data/raw/gw5/.archive/bootstrap-20260918T151953_303197Z.json`). Diffed field
by field on `status`, `chance_of_playing_next_round` and `news` for all 15
selected ids.

**Zero deltas.** `now_cost` also unmoved on all 15.

The only movement against the *original* analysis-time snapshot
(2026-09-18T12:49:57Z) is Shaw (423), `chance_of_playing_next_round` 75 → 50
and the matching `news` string — the change that triggered the first REOPEN and
which is already incorporated (A3-DEF re-derived `p_start` 0.50 → 0.32, ramp
`[0.32, 0.66, 0.72, 0.72, 0.72, 0.72]`, uncertainty HIGH, EP6 12.81 → 11.79;
`data/analysis/gw5/players-DEF.json` regenerated). Shaw reading `d` / 50% is the
expected value, not a new delta.

`news_added` was excluded from the comparison by design: this cycle proved it
can stay frozen (Shaw's stayed at 2026-09-11T13:00:09Z while the percentage
moved), so the values are gated, never the timestamp.

Snapshot age at write time: **< 1h** — inside the 24h requirement.

## Squad (15) — Σ sell £99.2m + bank £0.1m = team value £99.3m

`GW5 EP` and `EP6` are the code's `ep_gw[0]` and `ep_total6` from
`data/analysis/gw5/players-{GKP,DEF,MID,FWD}.json`. This table is the raw
material for `fpl calibrate --round 5`.

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

Constraints verified: **2 GKP / 5 DEF / 5 MID / 3 FWD** ✓ · 15 unique ids ✓ ·
Σ sell 99.2 + bank 0.1 = team value 99.3 ✓ · club counts ARS 2, EVE 2, BOU 2,
MCI 2, MUN 2, BRE 1, CRY 1, NEW 1, SUN 1, TOT 1 — all ≤ 3 ✓ · funding exact:
sell 5.9 = buy 5.8 + 0.1 to bank, bank 0.0 → 0.1 ✓.

## Starting XI — 3-4-3

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
| | **XI total** | | | | **50.676** |
| | + captain (Haaland) | | | | 6.721 |
| | **Predicted GW5** | | | | **57.397** |

Formation 3-4-3 = 1 GK, 3 DEF, 4 MID, 3 FWD ✓ (≥3 DEF, ≥2 MID, ≥1 FWD).
Exactly one captain and one vice, both in the XI ✓.

C20 (XI/bench boundary tie-break, ≤ 0.25 band) had one in-band pair — Anderson
4.003 v E.Le Fée 3.884, gap 0.119 — resolved to **Anderson** on DefCon floor
share (0.281 v 0.08). The tie-break and the EP order agree, so C20 changed
nothing this week; it was applied and the result is recorded.

## Captain and vice

**Captain Haaland** (MCI v SUN H, EP 6.721, LOW), 1.509 clear of the field —
three times the 0.5 tie band. The gap holds on prior-only (6.104 v 4.834).
Every candidate is LOW, so the C16 certainty multipliers reorder nothing.

**Vice Mbeumo** (MUN at FUL, EP 5.212), on a different fixture from the captain
and kicking off later (15:30 UTC v 13:00 UTC), so a Haaland non-start is known
before the vice's match begins. E.Le Fée is the only squad member sharing
Haaland's fixture and he is benched.

## Bench order

| Slot | Player | Pos | GW5 fixture | GW5 EP | Gap to slot above |
|---:|---|---|---|---:|---:|
| 12 | Dubravka | GKP | AVL (H) | 0.116 | — (backup GK, fixed slot) |
| 13 | E.Le Fée | MID | MCI (A) | 3.884 | — |
| 14 | Richards | DEF | LEE (A) | 2.870 | 1.014 |
| 15 | Shaw | DEF | FUL (A) | 1.015 | 1.855 |

C8 does not bite anywhere: both outfield gaps (1.014, 1.855) sit far outside
the ≤ 0.25 band, so undiscounted EP orders the whole bench and no DefCon
tie-break is invoked. Checked, not applied.

## Transfers

| Out | In | Sell | Buy | Cost |
|---|---|---:|---:|---:|
| Ndiaye (MCI, MID, id 237) | E.Le Fée (SUN, MID, id 542) | 5.9 | 5.8 | **0** (free transfer 1 of 2) |

**Hit cost: 0.** One free transfer spent, one banked; one further accrues for
GW6, giving `free_transfers_banked: 2` at the GW6 deadline (cap 5).

Gate arithmetic on the spec objective, both C14 readings:

| Move | Blend | Prior-only | Gate | Verdict |
|---|---:|---:|---|---|
| Transfer 1 — Ndiaye → E.Le Fée | **+4.105** | **+2.205** | 2.0 | **made** |
| Best second free move — Anderson → Schade | +1.853 | −1.107 | 2.0 | banked; fails gate and sign-flips (C14) |
| Shaw → Justin (second move, named) | +1.013 | +0.443 | 2.0 | banked; fails gate |
| Best third move (paid) | +1.853 | — | 6.0 gross | refused |

1,452 legal second moves were swept; none clears 2.0.

## Chips — none played

`chip: null`. `chips_used: []`. Forward earmarks, all provisional and all
inside their bootstrap windows (wildcard/freehit GW2–19, bboost/3xc GW1–19):

| Chip | Earmark | Basis |
|---|---|---|
| wildcard | GW8 | carries **two** repairs — the dead GK2 and the flagged fifth defender; EVE's ticker turns from GW7 |
| 3xc | GW9 | MCI v BHA (H), Haaland 6.995 — the window maximum, band-free (C5 satisfied on fixture-independent EP alone; GW5's 6.721 is second-best and does not displace it) |
| freehit | GW16 | placeholder — no blank or double inside GW5–10 |
| bboost | GW19 | last set-1 gameweek; blocked until **both** the GK2 and fifth-defender slots are repaired |

One chip per GW ✓ · freehit non-consecutive ✓. This table is a forecast;
`chip_plan` is its only machine-readable form and `chip: null` activates
nothing.

## Accepted risks

Carried from `review.md` and the revised proposal; none is resolved by this
week's decision.

| # | Risk | Detail | Routing |
|---|---|---|---|
| R1 | **Shaw — flagged fifth defender, third gameweek** | `d`, **50%**, `p_start` **0.32**, bench slot 15, EP6 11.79; the flag has stood three gameweeks. The replacement (Justin, `p_start` 0.90, 4/4 full 90s, DefCon 35, EP6 22.41 at £4.5m) scores **+1.013 / +0.443** against the 2.0 gate, so the transfer rule banks. Cost of holding to spec, if the auto-sub reading is the better one: order of **1–3 EP** over the window | GW8 wildcard; 2 banked FTs are the fallback if it slips |
| R2 | **Dead GK2** | Dubravka `p_start` 0.03, GW5 EP 0.116, EP6 0.66. No playing keeper is reachable under £4.1m — Steele and Forster are backups themselves (EP6 0.74 / 0.42) and score **+0.000** | GW8 wildcard |
| R3 | **GW19 Bench Boost blocked behind two weak slots** | R1 and R2 together — a dead GK2 *and* a 0.32 `p_start` fifth defender — make bboost GW19 unplayable as the squad stands | both repairs route to the GW8 wildcard |
| R4 | **E.Le Fée price bleed** | net **−74,697** transfers this event; already **−0.2** from start price. A further drop costs team value, not points | monitor; no action available pre-deadline |
| R5 | **Arsenal clean-sheet correlation** | Raya and Gabriel share one clean-sheet event (ARS at BHA). Their EP is not independent; a conceded goal costs both | accepted — Gabriel is the game's best defender on EP6 |
| R6 | **Differential midfield / rank volatility** | The **entire midfield** is below 22% ownership (Mbeumo 21.9%, Tavernier 6.2%, Scott 5.8%, Anderson 4.2%, E.Le Fée 3.6%). Unheld at ≥30%: João Pedro 70.7% (CHE FWD, `d` 75%), **Calafiori 50.2%** (ARS DEF £5.8m), B.Fernandes 40.5% (MUN MID £12.0m), Rogers 39.4% (CHE MID £7.7m), Szoboszlai 34.8% (LIV MID £7.0m). Only Haaland is a genuine template hold and he is captained, so a Haaland haul matches the field rather than gains on it. The stance is a by-product of a £15.6m striker plus a 5-man defence, not a chosen one — now stated | **Calafiori** named as the single template hole to close at the GW8 wildcard, competing with R1 and R2 for the same slots |
| R7 | **Two free transfers idle for 22 days** | The international break puts the GW6 deadline at **2026-10-10T10:00Z**. Two FTs sit unused for 22 days. The transfer rule has no long-break exception | accepted; the 2 FTs are the named funding for R1/R2 if the wildcard slips |
| R8 | **Freshness-gate scope limitation** | The gate covers only the selected 15, so it did not see Pau (34), Maatsen (36), Burn (448), Röhl (246), Wilson (260), M.Bizot (29), Doku (400), Gomes (54) or Gruev (344) move. A4 re-scored all of them against the refreshed status and none was near the gate, so **the decision is unaffected** — but the gate structurally cannot see a non-selected player becoming buyable or unbuyable | known limitation, already filed to `docs/backlog.md`; not acted on in-cycle |

## Rationale summary

One thing was wrong with the squad that a free transfer could fix this week,
and it is fixed at no points cost with £0.1m left in the bank.

**Ndiaye out.** Fifth-best midfielder on both readings and falling — C18 cut his
`p_start` 0.93 → 0.78 after the GW4 45-minute hook broke a three-start streak.
His analyst note reads *"Foden ban frees minutes, Doku returns"*: Foden is
suspended until 17 Oct (misses GW5 and GW6) and Doku returns 20 Sep, after this
deadline, so City's midfield is *less* contested in GW5, not more. That cuts
against the sale and the sale still stands: re-scoring with a phased Ndiaye
`p_start_gw` of `[0.90, 0.88, 0.82, 0.78, 0.78, 0.78]` leaves transfer 1 at
**+3.851**, still nearly twice the gate.

**E.Le Fée in.** 4/4 starts, the position's leading xG (2.06), penalties and a
corner, `p_start` 0.92 flat across all six gameweeks, EP6 **27.02 / 24.43**
against Ndiaye's 21.17, for £0.1m less. What sells Ndiaye is Le Fée, not
Ndiaye's minutes. His GW5 (MCI away) is the worst row in his own window, so he
is bought on the horizon rather than on one fixture.

**Shaw retained.** The squad's remaining weakness, and not fixed this week
because the move that fixes him scores +1.013 against a 2.0 gate. A4 established
that a *worse* Shaw does not raise the marginal under the spec objective: XI-max
weights bench players at zero and Shaw makes the best XI in none of GW5–10, so
his 75% → 50% decline left the marginal at +1.013 / +0.443 exactly. The metric
cannot see the change. That is a filed backlog finding, not a reason to score
this week differently.

**Three disciplines did real work.** C14 killed five of the ten best-looking
singles outright (Anderson → E.Le Fée, → Schade, → Groß, → Stach, and
Thiago → João Pedro all gain on blend and lose on prior-only). The transfer rule
banked the second FT against a board whose best legal second move is +1.853.
C4's band was applied by rebuilding `fixtures.json` at the −15pp floor and
rerunning `fpl ep` for all four positions — transfer 1 survives at **+4.101**
and the banked second stays below the gate at +1.057, so the decision is
invariant to the band.

### Orchestration facts for this cycle

- **Model tier deviation.** CLAUDE.md assigns the squad-optimizer and red-team
  to the Fable tier. That budget was exhausted mid-cycle (HTTP 429), so both ran
  on **Opus** for GW5 with the user's explicit authorisation. Already logged in
  `docs/backlog.md`.
- **Defective decision metric, caught and withdrawn.** The optimizer's first
  pass used an auto-substitution simulation as its decision metric. The red-team
  caught it: a legality guard ending `>= 1 or True` that never fired, so an
  illegal team was "repaired" by deleting the last-added substitute rather than
  skipping an ineligible one — a 3-DEF XI losing two defenders fielded nine
  players, understating auto-sub value by 2.11 EP. The user ruled the **spec
  objective governs this cycle**, so only one transfer is made; the second
  failed the 2.0 gate at +1.013 on the spec metric. Every sim-derived figure is
  withdrawn from the proposal, including the first pass's 61.02 auto-sub-
  inclusive GW5 expectation — **57.397 is the prediction and 57.397 is what
  `calibrate --round 5` will score.**
- **Loop count.** One red-team revision loop (verdict REVISE, 3 HIGH, all
  closed) plus one REOPEN from the freshness gate. REOPEN cycles are exempt from
  the one-revision cap.

## Suggestions

Read data/suggestions.md through S2

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 4 | standing | Ndiaye half **completed**: Ndiaye (EP6 21.17, `p_start` cut 0.93 → 0.78 under C18, last of five MIDs on both readings) → E.Le Fée (27.02 / 24.43, leading position xG 2.06, pens + CK, 0.92 flat across the window), **+4.105 blend / +2.205 prior on the spec objective** — first on blend among all 1 376 legal singles and the only top-tier move positive on both readings, so the optimizer reached it unaided and the steer broke no tie; EP6 delta of the suggestion itself 0.00. Anderson half **available and declined on the merits, not on feasibility**: two legal pairs exit him, and both lose to the plan's pair on the spec objective — Anderson+Shaw → E.Le Fée+Justin **+4.711 blend / −0.504 prior** (sign-flips as a package, so C14 bars it independently) and Anderson+Thiago → Cherki+Wissa **+3.143 / +2.600**, against the plan pair's **+5.118 / +2.648**. The plan leads on both readings, so no tie-break is needed or used. The single best Anderson exit, Anderson → E.Le Fée **+3.665 / −1.325**, sign-flips and is refused under C14; the next, Anderson → Schade **+2.942 / −1.107**, does the same. The suggestion is explicitly about **ceiling**, and that is answered directly: no Anderson exit reachable this week raises the six-gameweek ceiling — every one of them lowers it on at least one reading. Anderson also holds the squad's highest DefCon share 0.281 and C20 kept him in the XI on it, which is a floor argument and is recorded as secondary. Stays standing until the Anderson half closes; revisit at the GW8 wildcard, when the GK2 and Shaw repairs free the same decision from the transfer budget |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |

## STATE

Replaced post-deadline (2026-09-18) to describe the team that actually played
GW5. The pre-deadline block this supersedes proposed the Ndiaye -> E.Le Fee
transfer and a 3-4-3; neither was ever POSTed. See the CORRECTION section at the
top of this file.

```yaml
# CORRECTED POST-DEADLINE. Nothing was POSTed for GW5: the authenticated session
# had expired and the deadline passed. FPL carried the GW4 squad and GW4 lineup
# forward, so picks: below are GW4's fifteen in GW4's slot order, captain Haaland
# (411), vice Gabriel (4) - verified against
# `fpl picks --gw 5 --team-id 8455344 --event 5`, an exact match to
# data/decisions/gw4/final.md on all fifteen ids, all fifteen slots and both
# armbands. transfers_made is empty: none were made.
#
# Convention (as GW2-GW5): free_transfers_banked = free transfers available at
# the NEXT (GW6) deadline. Arithmetic: 2 were available at the GW5 deadline, 0
# were used, 1 accrues for GW6 => 3, under the cap of 5.
#
# team_value / bank basis (as GW4): squad selling-price sum + bank. Read from
# `fpl entry --gw 5 --team-id 8455344`, refreshed after the deadline on
# 2026-09-18: last_deadline_value 998, last_deadline_bank 0. That is FPL's own
# post-deadline accounting on the selling-price basis GW4 used, not the
# bootstrap now_cost sum. So team_value 99.8 = squad sell 99.8 + bank 0.0.
# No authenticated my-team read was possible this cycle (expired session); the
# unauthenticated entry endpoint is the basis of record here. The same read
# returns last_deadline_total_transfers 2 (GW2 Tavernier, GW3 Barry),
# independently confirming no GW5 transfer was ever registered.
gw: 5
team_id: 8455344
team_value: 99.8
bank: 0.0
free_transfers_banked: 3
chip: null
chips_used: []
transfers_made: []
chip_plan:
  - {chip: 3xc, gw: 9, status: provisional}
  - {chip: wildcard, gw: 8, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 1, name: Raya, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: false, vice: true}
  - {id: 229, name: Tarkowski, position: 3, captain: false, vice: false}
  - {id: 202, name: Richards, position: 4, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 5, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 6, captain: false, vice: false}
  - {id: 69, name: Scott, position: 7, captain: false, vice: false}
  - {id: 237, name: Ndiaye, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: true, vice: false}
  - {id: 106, name: Thiago, position: 10, captain: false, vice: false}
  - {id: 249, name: Barry, position: 11, captain: false, vice: false}
  - {id: 497, name: Dubravka, position: 12, captain: false, vice: false}
  - {id: 481, name: Anderson, position: 13, captain: false, vice: false}
  - {id: 445, name: Thiaw, position: 14, captain: false, vice: false}
  - {id: 423, name: Shaw, position: 15, captain: false, vice: false}
```
