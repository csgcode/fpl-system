# GW6 Squad Proposal (2026/27) — first optimizer run

Deadline **2026-10-10T10:00:00Z**. Horizon **GW6–GW11** (spec objective:
Σ best-XI EP + captain EP, 6 gameweeks). Cycle branch: **weekly**, 3 free
transfers banked, no chip used.

**THREE transfers, all free: OUT Scott (BOU, id 69, sell £6.0m) → IN E.Le Fée
(SUN, id 542, £5.7m); OUT Ndiaye (MCI, id 237, sell £5.8m) → IN Groß (BHA,
id 124, £5.9m); OUT Anderson (MCI, id 481, sell £6.3m) → IN Schade (BRE,
id 94, £6.2m). Hit 0. Bank £0.3m. No chip; wildcard earmark stays at GW8.
3-5-2, Haaland (C), Mbeumo (V). Predicted GW6 56.18. GW6–8 mean 56.37.**

## Inputs

| Source | Used for |
|---|---|
| `data/decisions/gw5/final.md` STATE block (post-deadline CORRECTION) | current squad = GW4's fifteen, bank 0.0, 3 FTs, no chips used, S1 fully open |
| `data/analysis/gw6/players-{GKP,DEF,MID,FWD}.json` | blend EP (`ep_gw`, `ep_total6`), `p_start_gw` already inside `ep_gw` |
| scratch rerun of `fpl ep` with `prior_weight: 1.0` on every inputs row | C14 prior-only reading (not written to `data/analysis/`) |
| `data/analysis/gw6/fixtures.md` | ticker, promoted-club band rows (C12) |
| `data/retro/gw1–gw5.md` | C5, C8, C14, C16, C20 active for A4 |
| `data/suggestions.md` read through **S6**; ledger in gw5 final.md | S1–S6 dispositions |
| `data/analysis/gw6/research-{ndiaye,anderson,scott,target}.md` | user research; its EP was GW5 proxy and is superseded by the GW6 files below |
| `fpl my-team --gw 6` (relayed by the orchestrator after auth was restored) | **verified** selling prices, bank, FT count, chip availability |

**Selling prices — VERIFIED.** `my-team` sell / buy, £m: Raya 6.0/6.0, Gabriel
8.0/8.0, Tarkowski 6.1/6.0, Richards 4.9/5.0, Tavernier 6.0/6.0, Mbeumo 7.9/8.0,
Scott 6.0/6.0, Ndiaye 5.8/6.0, Haaland 15.5/15.5, Thiago 7.8/8.0, Barry 5.6/5.5,
Dubravka 4.0/4.0, Anderson 6.3/6.5, Thiaw 5.0/5.0, Shaw 4.3/4.5. **Σ sell
99.2, bank 0.0.** The half-rise reconstruction from purchase prices gives the
same fifteen figures. The STATE block's `team_value: 99.8` and the entry
endpoint's value are the `now_cost` sum, not selling prices: **the wildcard
budget is £99.2m, not £99.8m.** The research files sized the wildcard on 99.8;
every wildcard figure below is re-run at 99.2.

## 1. Hold baseline

| Reading | GW6 | GW7 | GW8 | GW9 | GW10 | GW11 | Σ 6 GW | GW6–8 mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Blend | 53.82 | 55.17 | 52.98 | 54.58 | 55.03 | 54.09 | **325.67** | 53.99 |
| Prior-only | | | | | | | 316.59 | |

Scott (status `i`, 0%, "Thigh injury – Unknown return date", media estimate
GW13–14 return) scores **0.00** in every gameweek of the window, so the hold
XI must start Ndiaye (3.46) and bench Anderson (3.30). Ndiaye's
`p_start_gw` is phased `[0.85, 0.78, 0.75, 0.72, 0.72, 0.72]` (EP6 19.85);
Anderson is 0.90 flat (EP6 20.88, prior-only 23.97 — the prior is his
Forest season and still props him up).

## 2. Transfer sweep (audit trail)

Pool: every row of the four EP files (421 players). Pairs and triples use a
pruned pool of 144 (a player is kept unless ten cheaper-or-equal players beat
his EP6). Every move is scored on both C14 readings; `bank` is after the move.

### Singles — exhaustive, 1,404 legal

| Blend Δ6 | Prior Δ6 | Move | Bank | Verdict |
|---:|---:|---|---:|---|
| **+6.530** | +3.788 | Scott → E.Le Fée (5.7) | 0.3 | clears gate on both |
| +6.530 | +3.778 | Ndiaye → E.Le Fée (5.7) | 0.1 | clears gate on both |
| +6.183 | +1.500 | Scott → Groß (5.9) | 0.1 | clears gate on both |
| +5.893 | +0.799 | Anderson → E.Le Fée (5.7) | 0.6 | clears gate on both |
| +5.546 | −1.809 | Anderson → Groß (5.9) | 0.4 | blend clears; prior-only flips |
| +5.531 | +0.757 | Anderson → Schade (6.2) | 0.1 | clears gate on both |
| +4.692 | +2.020 | Scott → Stach (6.0) | 0.0 | clears gate on both |
| +4.055 | −1.188 | Anderson → Stach (6.0) | 0.3 | prior-only flips |
| +2.423 | +1.430 | Anderson → Barnes (6.1) | 0.2 | clears gate on both |
| +1.382 | 0.000 | Shaw → Davis (4.0) | 0.3 | fails gate |
| +1.225 | −2.091 | Thiago → João Pedro (7.7) | 0.1 | fails gate, flips |
| +1.087 | −0.725 | Richards → Justin (4.5) | 0.4 | fails gate |
| +0.979 | −0.768 | Raya → Trafford (5.0) | 1.0 | fails gate |
| +0.000 | — | Dubravka → any GK ≤ £4.0m | — | no playing keeper reachable; Steele/Forster are backups |

### Pairs — 98,315 legal over the pruned pool

| Blend Δ6 | Prior Δ6 | Move | Bank | GW6–8 mean |
|---:|---:|---|---:|---:|
| **+11.961** | +4.453 | Scott + Ndiaye → E.Le Fée + Groß | 0.2 | 55.89 |
| +11.961 | +2.299 | Scott + Anderson → E.Le Fée + Groß | 0.7 | 55.89 |
| +11.946 | +4.545 | Scott + Anderson → E.Le Fée + Schade | 0.4 | 55.88 |
| +11.946 | +4.535 | Ndiaye + Anderson → E.Le Fée + Schade | 0.2 | 55.88 |
| +10.470 | +4.897 | Scott + Ndiaye → E.Le Fée + Stach | 0.1 | 55.56 |
| +9.559 | +5.942 | Scott + Anderson → E.Le Fée + Sávio | 0.1 | 55.45 |
| +8.375 | +4.662 | Scott + Shaw → E.Le Fée + Justin | 0.1 | 55.16 |
| +8.130 | +1.911 | Scott + Thiaw → E.Le Fée + Hall | 0.0 | 55.25 |

### Triples — 2,725,602 legal with Scott out (he is in every improving triple)

| Blend Δ6 | Prior Δ6 | Move | Bank | GW6–8 mean |
|---:|---:|---|---:|---:|
| **+14.449** | **+5.210** | **Scott + Ndiaye + Anderson → E.Le Fée + Groß + Schade** | **0.3** | **56.37** |
| +13.528 | +0.819 | Gabriel + Scott + Anderson → De Cuyper + E.Le Fée + Saka | 0.0 | 55.89 |
| +13.493 | +3.371 | Gabriel + Scott + Ndiaye → Justin + E.Le Fée + Saka | 0.0 | 55.88 |
| +13.480 | +0.102 | Scott + Anderson + Thiaw → E.Le Fée + Groß + Hall | 0.4 | 56.14 |
| +13.308 | +3.505 | Scott + Ndiaye + Anderson → E.Le Fée + Groß + Stach | 0.5 | 56.16 |
| +13.293 | +5.459 | Scott + Ndiaye + Anderson → E.Le Fée + Stach + Schade | 0.2 | 56.16 |
| +13.191 | +5.878 | Scott + Thiago + Anderson → E.Le Fée + Gibbs-White + Wissa | 0.2 | 56.23 |
| +13.186 | +2.645 | Scott + Ndiaye + Thiago → E.Le Fée + Groß + João Pedro | 0.3 | 55.85 |
| +13.160 | +5.145 | Scott + Ndiaye + Shaw → E.Le Fée + Groß + Justin | 0.0 | 55.94 |
| +13.096 | +6.607 | Scott + Ndiaye + Anderson → E.Le Fée + Groß + Sávio | 0.0 | 56.09 |

The best triple is the user's three named exits, reached unaided: it leads on
blend by 0.92 over the next triple and is positive on prior-only (+5.21). The
Saka routes (rank 2–3) need Gabriel sold, cost 0.9–1.0 EP6 on blend and fall
to +0.8 / +3.4 on prior-only; Gabriel is the pool's best defender on both
readings and stays.

### Marginal gate per sale (plan with that one row removed)

| Sale | Plan minus it | Blend marginal | Prior marginal | Gate 2.0 |
|---|---|---:|---:|---|
| Scott (S5) | Ndiaye + Anderson → E.Le Fée + Schade, +11.946 / +4.535 | **+2.503** | +0.675 | cleared |
| Ndiaye (S3) | Scott + Anderson → E.Le Fée + Schade, +11.946 / +4.545 | **+2.503** | +0.665 | cleared |
| Anderson (S4) | Scott + Ndiaye → E.Le Fée + Groß, +11.961 / +4.453 | **+2.488** | +0.757 | cleared |

Each sale clears the transfer rule on its own marginal and is positive on
both readings, so none of S3–S5's "even below the threshold" clauses is
invoked.

### Fourth transfer (paid) — refused

From the post-transfer squad, the best paid single is Thiago → João Pedro
**+1.636 / −1.808** (gross, before the −4), then Thiaw → Hall +1.509 / −1.877
and Shaw → Justin +1.121 / +0.692. The hit gate is gross ≥ 6.0; nothing is
within four points of it, and the top two flip sign under C14.

### Swap pass on the chosen squad

Single swaps from the chosen fifteen (same table as the paid-move check, with
the move free): the best is +1.636, below the 2.0 gate. No improving swap
remains inside the rule. Dubravka and Shaw stay by default — the GK2 and
DEF5 repairs are the wildcard's job (§4).

## 3. Chip decision — wildcard GW6 against 3 FTs now + wildcard GW8

Wildcard squads come from a best-improvement search (1- and 2-player swaps,
8 random starts, pruned pool of 144) at the **verified £99.2m**. Heuristic,
not a proven optimum; the true maximum may be a few tenths higher.

| Path | Σ GW6–11 blend | Σ prior-only | GW6–8 mean | Notes |
|---|---:|---:|---:|---|
| Hold | 325.67 | 316.59 | 53.99 | — |
| **3 FTs now (chosen)** | **340.12** | **321.80** | **56.37** | bank 0.3; wildcard and all chips kept |
| Wildcard GW6, best blend squad | 350.09 | 320.23 | 57.63 | Trafford, Rushworth; Thomas, Davis, Gabriel, Guéhi, Tarkowski; E.Le Fée, Groß, Saka, Mbeumo, Tavernier; Barry, Haaland, Akpom — £99.2m |
| Wildcard GW6, LOW/MED-uncertainty rows only | 348.09 | 319.05 | 57.51 | Trafford, Tzolakis; Guéhi, Tarkowski, Justin, Hall, Schuster; Saka, Groß, E.Le Fée, Tavernier, Mbeumo; Barry, Haaland, Wissa — £98.9m |
| 3 FTs now + wildcard GW8 (GW8–11 rebuild scored on today's EP) | 113.27 + 234.86 = **348.13** | — | 56.37 | GW8–11 squad: Trafford, Walton; Justin, Gabriel, Davis, Greaves, Guéhi; E.Le Fée, Groß, Saka, Mbeumo, Tavernier; João Pedro, Haaland, Simms |
| Ceiling, no budget (club cap kept), GW6–8 | — | — | 59.61 | £113.6m: Trafford, Tzolakis; Guéhi, Gabriel, Tarkowski, Hall, Calafiori; B.Fernandes, Mbeumo, Gibbs-White, Saka, Tavernier; Haaland, Barry, João Pedro |

Reading the table:

1. **Wildcard now beats the 3-FT path by +9.97 on blend over GW6–11, but by
   −1.57 on prior-only** (320.23 v 321.80). The extra ten points are current-
   form rates — Groß (26.58 blend / 22.17 prior), Saka (33.04 / 29.52),
   Trafford, and two £4.0m HIGH-uncertainty promoted-club defenders (Thomas
   COV, Davis IPS). C14 bars a *hit* whose sign flips; a wildcard is not a
   hit, so the rule does not refuse it — but the increment is exactly the
   pattern C14 exists to flag, and the 3-FT path is the one that is positive
   on both readings.
2. **Against the fair comparison the gap is +1.96.** 3 FTs now plus a GW8
   wildcard rebuilt on today's EP scores 348.13 against 350.09. That is inside
   one player's MAE (1.51). The GW8 rebuild will be made on two more rounds of
   data and with the GK2 and DEF5 repairs priced then; the GW6 rebuild would
   be made on a blend that the fixture ticker still rates 53/47 prior.
3. **On the user's GW6–8 target** the wildcard gains 1.26 per gameweek
   (57.63 v 56.37), the robust build 1.14. The research's own switch rule was
   "well above 2 EP per GW"; it is not met.
4. **60 per gameweek is unreachable**: the no-budget ceiling is 59.61 over
   GW6–8 at £113.6m. The best legal GW6 figure is 57.63 (wildcard) or 56.37
   (3 FTs). The research's 57 / 59 estimates were on £99.8m; at the verified
   £99.2m the wildcard loses about 0.4 per gameweek of that.
5. Free transfers: the wildcard does not wipe banked FTs, so the GW6 wildcard
   would also keep three. After the chosen path 0 remain, 1 accrues for GW7,
   2 for GW8 and survive the GW8 wildcard. That is the one real cost of the
   chosen path and it is small: the post-transfer board has no ≥2.0 move left
   for those FTs to make.

**Decision: 3 free transfers now, wildcard earmark held at GW8.** The user may
reasonably prefer the GW6 wildcard for its +1.3 per gameweek on GW6–8; the
numbers are above, and switching is a one-line change to `chip:` plus the
squad table, which the red-team or the user can call for.

## 4. Squad after transfers — Σ sell £98.9m + bank £0.3m = £99.2m

`GW6 EP` and `EP6` are `ep_gw[0]` and `ep_total6` from the GW6 EP files;
`Prior6` is the C14 rerun. Sell = verified `my-team` for holds; incoming
players sell at their buy price.

| Slot | Pos | Player | Id | Club | Buy | Sell | GW6 EP | EP6 | Prior6 | p_start | Unc | DefCon share | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| 1 | GKP | Raya | 1 | ARS | 6.0 | 6.0 | 3.604 | 21.95 | 21.03 | 0.94 | LOW | 0.00 | XI |
| 2 | DEF | Tarkowski | 229 | EVE | 6.0 | 6.1 | 4.734 | 25.81 | 23.45 | 0.92 | LOW | 0.22 | XI |
| 3 | DEF | Gabriel | 4 | ARS | 8.0 | 8.0 | 4.671 | 28.36 | 29.98 | 0.93 | LOW | 0.17 | XI |
| 4 | DEF | Thiaw | 445 | NEW | 5.0 | 5.0 | 3.881 | 21.30 | 22.67 | 0.90 | LOW | 0.24 | XI |
| 5 | MID | Mbeumo | 427 | MUN | 8.0 | 7.9 | 5.230 | 30.21 | 27.33 | 0.93 | LOW | 0.02 | XI · **Vice** |
| 6 | MID | E.Le Fée | 542 | SUN | 5.7 | 5.7 | 4.687 | 26.93 | 24.77 | 0.92 | LOW | 0.07 | XI · **IN** |
| 7 | MID | Tavernier | 68 | BOU | 6.0 | 6.0 | 4.618 | 27.72 | 25.45 | 0.91 | LOW | 0.04 | XI |
| 8 | MID | Groß | 124 | BHA | 5.9 | 5.9 | 4.427 | 26.58 | 22.17 | 0.93 | LOW | 0.04 | XI · **IN** |
| 9 | MID | Schade | 94 | BRE | 6.2 | 6.2 | 4.427 | 26.57 | 24.73 | 0.93 | LOW | 0.03 | XI · **IN** |
| 10 | FWD | Haaland | 411 | MCI | 15.5 | 15.5 | 5.786 | 38.36 | 35.02 | 0.93 | LOW | 0.01 | XI · **Captain** |
| 11 | FWD | Barry | 249 | EVE | 5.5 | 5.6 | 4.327 | 25.31 | 22.49 | 0.91 | LOW | 0.01 | XI |
| 12 | GKP | Dubravka | 497 | TOT | 4.0 | 4.0 | 0.106 | 0.67 | 0.67 | 0.03 | HIGH | 0.00 | Bench GK |
| 13 | FWD | Thiago | 106 | BRE | 8.0 | 7.8 | 4.209 | 25.37 | 27.07 | 0.92 | LOW | 0.02 | Bench 1 |
| 14 | DEF | Richards | 202 | CRY | 5.0 | 4.9 | 3.509 | 20.95 | 22.02 | 0.90 | LOW | 0.28 | Bench 2 |
| 15 | DEF | Shaw | 423 | MUN | 4.5 | 4.3 | 2.673 | 13.16 | 13.58 | 0.75 | MED | 0.07 | Bench 3 |
| | | **Total** | | | | **98.9** | | **359.35** | 330.43 | | | | |

Constraints: **2 GKP / 5 DEF / 5 MID / 3 FWD** ✓ · 15 unique ids ✓ · club
counts ARS 2, EVE 2, MUN 2, BRE 2, BOU 1, MCI 1, CRY 1, NEW 1, TOT 1, SUN 1,
BHA 1 — all ≤ 3 ✓ · funding: sells 6.0 + 5.8 + 6.3 = 18.1, buys 5.7 + 5.9 +
6.2 = 17.8, bank 0.0 → **0.3** ✓ (≤ 0.5, budget exhausted).

Selling Ndiaye and Anderson takes MCI from 3 to 1, which frees two MCI slots
for the GW8 wildcard (Guéhi is the second-best DEF on EP6).

### Incoming players

| Player | Why | Risk |
|---|---|---|
| **E.Le Fée** (SUN, £5.7m) | 5/5 starts, 79–90 minutes every round, position-leading xG, penalties and corners; EP6 26.93 / 24.77 — first on blend among every single exit for all three outgoing players. Ownership 3.3%. | SUN rated 11th on attack and rising; GW7 BOU (A) is his weakest row |
| **Groß** (BHA, £5.9m) | 90 × 5, penalties, 9 bonus; EP6 26.58 / 22.17 — the largest blend-over-prior gap of the three (current form carries him). Ownership 31.9%: closes part of the R6 template gap. | GW8 LIV (A), GW9 MCI (A) are poor rows; the ticker turns at GW10 |
| **Schade** (BRE, £6.2m) | 87–90 × 5, second on penalties, xG 1.52; EP6 26.57 / 24.73, positive on both readings. BRE 3rd on both tickers. | Pairs with Thiago on BRE's attack (two of three BRE slots used); GW7 LIV (H) |

## 5. Starting XI — 3-5-2

| Slot | Player | Club | Pos | GW6 fixture | GW6 EP |
|---:|---|---|---|---|---:|
| 1 | Raya | ARS | GKP | LEE (H) | 3.604 |
| 2 | Tarkowski | EVE | DEF | HUL (A) ± | 4.734 |
| 3 | Gabriel | ARS | DEF | LEE (H) | 4.671 |
| 4 | Thiaw | NEW | DEF | COV (A) ± | 3.881 |
| 5 | Mbeumo **(V)** | MUN | MID | TOT (H) | 5.230 |
| 6 | E.Le Fée | SUN | MID | BHA (H) | 4.687 |
| 7 | Tavernier | BOU | MID | CHE (A) | 4.618 |
| 8 | Groß | BHA | MID | SUN (A) | 4.427 |
| 9 | Schade | BRE | MID | AVL (A) | 4.427 |
| 10 | Haaland **(C)** | MCI | FWD | LIV (A) | 5.786 |
| 11 | Barry | EVE | FWD | HUL (A) ± | 4.327 |
| | **XI total** | | | | **50.392** |
| | + captain (Haaland) | | | | 5.786 |
| | **Predicted GW6** | | | | **56.178** |

Formation 3-5-2 = 1 GK, 3 DEF, 5 MID, 2 FWD ✓. Exactly one captain and one
vice, both in the XI ✓. The XI and bench are ordered on undiscounted EP (C16).

**C20 boundary.** The XI/bench boundary is Thiago (4.209, bench 1) against the
fifth midfielder — Groß and Schade tie at 4.427 — a 0.218 gap, inside C8's
0.25 band. DefCon-floor share: Groß 0.044, Schade 0.029, Thiago 0.021. The
tie-break favours the midfielders, agreeing with the EP order, so 3-5-2
stands and 3-4-3 (Thiago for Schade, −0.218) is rejected. Thiaw (3.881) is
not at a free boundary: he is the mandatory third defender, and his
alternative is Richards (3.509, gap 0.372, outside the band).

**C12.** Tarkowski's and Barry's GW6 rows (EVE at HUL) carry the promoted-club
band; EVE's P(CS) 0.33 is a tripping row for defensive terms. Tarkowski is
selected on his six-gameweek EP (25.81, second DEF in the pool), not on that
row; his GW6 EP of 4.734 is the squad's highest DEF value and the XI holds
with the GW5 fixtures file's −15pp floor applied to that row (4.734 → about
4.3 still beats Richards 3.509 for the slot).

## 6. Captain and vice

Top five on single-GW EP × certainty (LOW 1.00 / MED 0.92 / HIGH 0.80):

| Rank | Player | GW6 fixture | EP | Unc | × certainty | Gap to #1 | Prior-only | Owned |
|---:|---|---|---:|---|---:|---:|---:|---|
| 1 | **Haaland** | LIV (A) | 5.786 | LOW | 5.786 | — | 5.287 | yes |
| 2 | B.Fernandes | TOT (H) | 5.777 | LOW | 5.777 | 0.009 | 5.680 | no |
| 3 | Saka | LEE (H) | 5.510 | LOW | 5.510 | 0.276 | 4.920 | no |
| 4 | Mbeumo | TOT (H) | 5.230 | LOW | 5.230 | 0.556 | 4.730 | yes |
| 5 | Gibbs-White | CRY (A) | 4.799 | LOW | 4.799 | 0.987 | 4.279 | no |

**Captain Haaland.** Among owned players he leads Mbeumo by 0.556, outside the
0.5 tie band; the gap holds on prior-only (5.287 v 4.730). Every candidate is
LOW, so the C16 multipliers reorder nothing. LIV (A) is his worst row in the
window (λ_att 1.59 against a 1.97 window mean), which is why B.Fernandes
ties him this week — but Fernandes is not owned, and buying him is not on the
board (no single or paid move featuring him clears any gate).

**Vice Mbeumo** (MUN v TOT, Sat 16:30Z; EP 5.230), the squad's second-highest
EP and on a different fixture from the captain. The vice applies
automatically if Haaland plays 0 minutes, whatever the kickoff order.

## 7. Bench order

| Slot | Player | Pos | GW6 fixture | GW6 EP | Gap to slot above |
|---:|---|---|---|---:|---:|
| 12 | Dubravka | GKP | AVL (H) | 0.106 | — (backup GK, fixed slot) |
| 13 | Thiago | FWD | AVL (A) | 4.209 | — |
| 14 | Richards | DEF | NFO (H) | 3.509 | 0.700 |
| 15 | Shaw | DEF | TOT (H) | 2.673 | 0.836 |

C8 does not bite within the bench: both gaps are outside the 0.25 band.
Thiago at bench 1 is the first auto-sub for any outfield non-starter and
keeps every formation legal (a missing DEF is covered by Richards at 14).

## 8. Transfers

| Out | In | Sell | Buy | Cost |
|---|---|---:|---:|---:|
| Scott (BOU, MID, id 69) | E.Le Fée (SUN, MID, id 542) | 6.0 | 5.7 | 0 (FT 1 of 3) |
| Ndiaye (MCI, MID, id 237) | Groß (BHA, MID, id 124) | 5.8 | 5.9 | 0 (FT 2 of 3) |
| Anderson (MCI, MID, id 481) | Schade (BRE, MID, id 94) | 6.3 | 6.2 | 0 (FT 3 of 3) |

Hit cost **0**. Three free transfers spent; 0 remain, 1 accrues for GW7
(`free_transfers_banked: 1` at the GW7 deadline). The out→in pairing is
nominal — FPL registers three outs and three ins — and is written so each
pair is self-funding. Package gain **+14.449 blend / +5.210 prior-only**
on the six-gameweek objective; GW6 alone +2.36 (53.82 → 56.18).

Transfers must be POSTed before the lineup: the XI names three players the
entry does not yet own, and `set-lineup` refuses until they land.

## 9. Provisional chip plan

`chip: null`. `chips_used: []`. All four set-1 chips available (verified).
Windows from the bootstrap `chips` array: wildcard/freehit GW2–19,
bboost/3xc GW1–19.

| Chip | Earmark | Basis |
|---|---|---|
| wildcard | **GW8** | carries the GK2 (Dubravka, p_start 0.03) and DEF5 (Shaw, 0.75 MED) repairs and the Saka/Guéhi upgrades the triple cannot fund; on today's EP the GW8–11 rebuild scores 234.86 against the chosen squad's 226.84 over the same rows (+8.0), to be re-run on GW8 data. Section 3 has the GW6 alternative |
| 3xc | GW9 | MCI v BHA (H), Haaland 6.87 — ties GW11 FUL (H) 6.87 and clears GW7 IPS (H) 6.84, which carries the promoted-club band and so cannot be the trigger (C5/C12). Haaland's fixture-independent window mean is 6.39; GW9 sits 0.48 above it |
| freehit | GW16 | placeholder — no blank or double inside GW6–11 |
| bboost | GW19 | last set-1 gameweek; blocked until the GK2 and DEF5 slots are repaired at the GW8 wildcard |

One chip per GW ✓ · freehit non-consecutive ✓ · wildcard does not wipe
banked FTs (2 will be banked at GW8 and survive it).

## 10. Rationale and rejected alternatives

**Scott out** is forced: 0.00 EP for the whole window and a media return of
GW13–14 at the earliest. **Ndiaye out** closes the move GW5 planned and never
POSTed; his phased `p_start_gw` and EP6 19.85 make him the fifth midfielder
on both readings. **Anderson out** is the half of S1 that previous cycles
declined under C14's prior-only reading; this week the package containing his
sale is positive on both readings (+5.21 prior) and his own marginal is
+2.49 / +0.76, so the sale clears on the merits rather than on the steer.
The research's point that his prior is a different role (Forest, 515 DefCon
actions, 16 bonus) against a City season of 0 bonus and 2/5 DefCon hits is
consistent with the blend-over-prior gap in his row (20.88 v 23.97).

| Rejected | Score | Why |
|---|---:|---|
| Wildcard GW6 | +9.97 blend / −1.57 prior over the chosen path; +1.96 against 3 FTs + GW8 wildcard | §3 — sign-flipping increment, HIGH-uncertainty £4.0m defenders in the best build, GW8 rebuild better informed |
| Gabriel + Scott + Anderson → De Cuyper + E.Le Fée + Saka | +13.528 / +0.819 | −0.92 on blend, −4.4 on prior; sells the pool's best DEF |
| Scott + Thiago + Anderson → E.Le Fée + Gibbs-White + Wissa | +13.191 / +5.878 | −1.26 on blend; best prior-only triple but keeps Ndiaye's phased minutes in the squad |
| Scott + Ndiaye + Anderson → E.Le Fée + Groß + Stach | +13.308 / +3.505 | −1.14; Stach's DefCon floor does not outscore Schade's attack |
| Scott + Ndiaye + Shaw → E.Le Fée + Groß + Justin | +13.160 / +5.145 | −1.29; repairs DEF5 now but leaves Anderson; DEF5 is the wildcard's job |
| Any 4th transfer (−4) | best gross +1.636 / −1.808 | below the 6.0 hit gate; flips |
| Bank 1–3 FTs for GW7 | 0 | nothing on the GW7 board beats using them now: the three sales each clear 2.0 on their own marginal |

**Risks accepted**

| # | Risk | Detail |
|---|---|---|
| R1 | GK2 dead, DEF5 weak | Dubravka 0.106 / Shaw 2.673 (0.75 MED). No reachable fix clears the gate; routed to the GW8 wildcard. Cost if an XI defender misses: Richards (3.509) covers one absence; a second absence fields Shaw |
| R2 | Three midfield buys on one week's EP | All three are LOW at p_start ≥ 0.92 with 5/5 starts; Groß's blend-over-prior gap (4.4) is the largest. If GW6–7 reverse the form the GW8 wildcard re-prices them at no transfer cost |
| R3 | Template | Owned ≥30%: Groß 31.9%, Haaland. Still unheld: B.Fernandes (ties Haaland on GW6 EP), Saka, Calafiori. Named for the GW8 wildcard |
| R4 | Captain fixture | Haaland at LIV (A) is his window-worst row; the 0.556 lead over Mbeumo still clears the band on both readings |
| R5 | Execution | The GW5 plan was never POSTed. The XI above is illegal to set until the three transfers land; a transfer decline leaves Scott (0 EP) in the carried-forward GW4 lineup, where auto-subs would bring Anderson on |

## Malformed

None. S1–S6 parse; no `withdraw` rows.

## Suggestions

Read data/suggestions.md through S6

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 6 | followed | both halves now complete: Ndiaye → Groß and Anderson → Schade inside the +14.449 blend / +5.210 prior-only triple; Ndiaye's marginal +2.503 / +0.665 and Anderson's +2.488 / +0.757 each clear the 2.0 gate on their own, so the steer broke no tie and the optimizer reached it unaided; EP6 delta of the row itself 0.00. The GW5 ledger's "Ndiaye half completed" was false in fact (never POSTed) and is superseded here |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |
| S3 | 6 | followed | Ndiaye → Groß made; marginal +2.503 blend / +0.665 prior against the plan without this sale (Scott + Anderson → E.Le Fée + Schade, +11.946 / +4.545), so the below-threshold clause was not needed |
| S4 | 6 | followed | Anderson → Schade made; marginal +2.488 blend / +0.757 prior against the plan without this sale (Scott + Ndiaye → E.Le Fée + Groß, +11.961 / +4.453); clears the gate on both readings, below-threshold clause not needed |
| S5 | 6 | followed | Scott → E.Le Fée made; EP6 0.00 for GW6–11 (status i, 0%); marginal +2.503 / +0.675 against the plan without this sale (Ndiaye + Anderson → E.Le Fée + Schade, +11.946 / +4.535) |
| S6 | 6 | standing | honoured: the three free transfers lift GW6–8 from 53.99 to 56.37 per GW (+2.38); the wildcard is timed at GW8 on the fresh EP — GW6 wildcard scores 57.63 (+1.26 per GW on GW6–8) but +1.96 over the full path against 3 FTs + GW8 wildcard and −1.57 on prior-only, below the research's own 2-per-GW switch rule. 60 is unreachable: no-budget ceiling 59.61 over GW6–8 at £113.6m, best legal 57.63. Completes `followed` at the GW8 wildcard, or `expired` after GW8 |

## STATE

```yaml
# Basis: free_transfers_banked = free transfers available at the NEXT (GW7)
# deadline: 3 available at GW6, 3 used, 1 accrues => 1.
# team_value on the selling-price basis verified by `fpl my-team --gw 6`:
# squad sell 98.9 (holds at my-team sell, incoming at buy) + bank 0.3 = 99.2.
# The entry endpoint's 99.8 is the now_cost sum and is not this field.
gw: 6
team_id: 8455344
team_value: 99.2
bank: 0.3
free_transfers_banked: 1
chip: null
chips_used: []
transfers_made:
  - {out: Scott, in: E.Le Fée, cost: 0}
  - {out: Ndiaye, in: Groß, cost: 0}
  - {out: Anderson, in: Schade, cost: 0}
chip_plan:
  - {chip: wildcard, gw: 8, status: provisional}
  - {chip: 3xc, gw: 9, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 1, name: Raya, position: 1, captain: false, vice: false}
  - {id: 229, name: Tarkowski, position: 2, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 3, captain: false, vice: false}
  - {id: 445, name: Thiaw, position: 4, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 5, captain: false, vice: true}
  - {id: 542, name: E.Le Fée, position: 6, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 7, captain: false, vice: false}
  - {id: 124, name: Groß, position: 8, captain: false, vice: false}
  - {id: 94, name: Schade, position: 9, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 10, captain: true, vice: false}
  - {id: 249, name: Barry, position: 11, captain: false, vice: false}
  - {id: 497, name: Dubravka, position: 12, captain: false, vice: false}
  - {id: 106, name: Thiago, position: 13, captain: false, vice: false}
  - {id: 202, name: Richards, position: 14, captain: false, vice: false}
  - {id: 423, name: Shaw, position: 15, captain: false, vice: false}
```
