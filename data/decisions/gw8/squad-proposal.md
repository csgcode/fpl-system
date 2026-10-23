# GW8 Squad Proposal (2026/27) — REOPEN: WILDCARD, Isak package (Saka out)

Fourth run of the cycle, on the freshness gate's exit 3
(data/raw/gw8/flags-delta-20261023T134015_536401Z.json: Saka d 50% → i,
unknown return date). The earlier runs are archived as squad-proposal.v1.md
(plan C), v2 (hold under the user's in-chat steers of the day) and v3 (the
red-team's F1 package, Saka in). The MID analyst re-ran in REOPEN mode:
players-MID.json now carries Saka at p_start 0 / 0.4 / 0.7 / 0.85 / 0.9 /
0.9 (EP6 21.39, was 28.64), Munoz 25% and the Madueke / Gakpo cover bumps;
the other positions are unchanged. Suggestion cut-off stays S8 (first run
of the cycle). Deadline 2026-10-23T17:30:00Z. Horizon GW8–13. Squad from
the STATE block of data/decisions/gw7/final.md; budget = its `team_value`
99.1.

**User instruction, verbatim:** "Ignore all my suggestions made today, Out
of all the suggestions that you made, select which is best for the future,
both in terms of short term and long term. You have my belief. I need you
to justify your actions and then make a decision."

**Decision: play the set-1 wildcard in GW8 with the Isak package (W2) —
Raya → Trafford, Dubravka → Kinsky, Tarkowski → Calafiori, Richards →
Hill, Shaw → Justin, Groß → Barnes, Schade → Gomez, Thiago → Isak.** The
Saka package is no longer a candidate: `objective` refuses him (`12 is not
in the pool (unknown, or status not a/d)`). W2 is the strongest package
found on both readings (+8.304 blend / +8.078 prior-only), clears the chip
gate by 2.30 on blend with no component whose prior-only sign flips, fixes
both dead bench slots, and keeps two free transfers for GW9. Holding was
graded as a full candidate and is rejected below with numbers.

**Wildcard. Eight transfers, hit 0. 4-4-2, Haaland (C), Gabriel (V).
Predicted GW8 55.052. Bank £0.0m. FT at GW9: 2.**

Sell basis: the GW7-verified selling prices from data/decisions/gw7/final.md
passed as `--sell` (the basis every earlier run, the review and both
research files used), so the CLI labels it `relayed`. No fresh `my-team`
read this cycle (session expired at step 1); every kept player's now_cost
is ≥ his GW7 sell price, so 99.1 is a floor and the true bank is ≥ 0.0.

## Verification — objective (verbatim)

`objective --gw 8 --sell 1:6.0,112:4.9,4:7.9,229:6.1,427:7.9,124:5.9,68:6.0,542:5.7,411:15.5,249:5.6,106:7.8,497:4.0,202:4.9,94:6.2,423:4.3 --bank 0.4 --free-transfers 1 --chip wildcard --moves 1:385,497:496,229:8,423:332,94:127,106:379,124:453,202:60`:

```
objective gw8 — horizon GW8–GW13; squad from data/decisions/gw7/final.md
sell basis: relayed (Σ sell 98.7 + bank 0.4 = 99.1)
baseline: blend 328.050 prior 318.513
plan: Raya → Trafford, Dubravka → Kinsky, Tarkowski → Calafiori, Shaw → Justin, Schade → Gomez, Thiago → Isak, Groß → Barnes, Richards → Hill — blend +8.304 prior +8.078; bank 0.0; transfers 8 under wildcard (FT unchanged (1)); chip gate: ≥ 6.0 over the greedy plan
  move Raya → Trafford: +0.042 / +0.045 — chip package
  move Dubravka → Kinsky: +0.119 / +0.189 — chip package
  move Tarkowski → Calafiori: +1.914 / +0.820 — chip package
  move Shaw → Justin: +1.138 / +1.482 — chip package
  move Schade → Gomez: +0.224 / +0.485 — chip package
  move Thiago → Isak: +3.314 / +1.636 — chip package
  move Groß → Barnes: +0.813 / +2.427 — chip package
  move Richards → Hill: +0.978 / +1.031 — chip package
after plan, best single: none legal
reference (greedy): bank — no move passes its gate
verdict: PASS
GW8 XI 4-4-2 55.260: Trafford, Gabriel, Calafiori, Hill, Justin, Mbeumo, E.Le Fée, Tavernier, Barnes, Haaland, Isak; captain top 5: Haaland 5.798 0.94, Gabriel 5.080 0.95, Mbeumo 4.932 0.96, Isak 4.854 0.88, Calafiori 4.596 0.94
boundary pairs within 0.25: Justin 3.773 (DefCon 0.161) | Barry 3.660 (0.008) ; Justin 3.773 (DefCon 0.161) | Van Hecke 3.565 (0.190) ; Justin 3.773 (DefCon 0.161) | Gomez 3.541 (0.139)
bench: Kinsky 2.916, Barry 3.660, Van Hecke 3.565, Gomez 3.541
```

| Check | Result |
|---|---|
| Legality | `objective` accepts the package (an illegal one refuses): 2 GKP / 5 DEF / 5 MID / 3 FWD |
| Budget | sells 45.2 + bank 0.4 = 45.6; buys Trafford 5.0 + Kinsky 4.5 + Calafiori 6.0 + Hill 5.5 + Justin 4.5 + Barnes 6.1 + Gomez 5.0 + Isak 9.0 = 45.6; bank 0.0 on the GW7-verified floor, so never negative |
| 3 per club | ARS 2 (Gabriel, Calafiori), BOU 2 (Tavernier, Hill), LEE 2 (Trafford, Justin), TOT 2 (Kinsky, Van Hecke); MUN, SUN, NEW, MCI, LIV, BHA, EVE 1 each. No club at 3 |
| Chip gate | greedy reference is bank (+0.000 / +0.000: no single move passes the free gate); the wildcard is +8.304 blend (≥ 6.0) and +8.078 prior-only (≥ 0). PASS, margin 2.304 on blend |
| Prior sign flips | none of the eight components; the smallest prior-only marginal is Raya → Trafford +0.045 |
| Flags | all 15 `a`; Isak and Haaland a/100. Saka (i) is not bought; Stach (d 50% foot) and Calvert-Lewin (d 50% foot), both flagged in the 13:13 UTC refresh, are not bought |
| Window | wildcard set 1, GW2–19 in bootstrap `chips`, unused (chips_used empty in GW7 STATE); one chip this GW |

## Ranked candidates — every package graded this run

All `--chip wildcard` on the relayed basis unless marked; GW8 XI = the
objective's best XI with captain, before the C20 tie-break. Gate = chip gate
(blend ≥ 6.0 and prior-only ≥ 0 over the greedy plan, which is bank).

| Rank | Package | Moves | blend / prior-only | GW8 XI | Gate | Sign-flip components |
|---:|---|---:|---:|---:|---|---|
| **1** | **W2 — this plan: Trafford, Kinsky, Calafiori, Hill, Justin, Barnes, Gomez, Isak** | 8 | **+8.304 / +8.078** | 55.260 | PASS (+2.30) | none |
| 2 | W1 — as W2 but Suzuki for Kinsky, Richards kept | 7 | +7.762 / +7.340 | 55.327 | PASS (+1.76) | none (Raya → Trafford −0.104 / −0.110 loses on both: a funding move, not a flip) |
| 3 | W1 with Rudoni for Gomez | 7 | +7.512 / +6.855 | 55.327 | PASS (+1.51) | none |
| 4 | W2 with Van Hecke → Hill instead of Richards → Hill | 8 | +7.425 / +7.349 | 55.531 | PASS (+1.43) | none |
| 5 | W2 without Richards → Hill (bank 0.6) | 7 | +7.326 / +7.047 | 55.327 | PASS (+1.33) | none |
| 6 | Isak + Barnes, Raya and Dubravka kept | 5 | +7.169 / +6.804 | 55.580 | PASS (+1.17) | none; Dubravka (p 0.03) stays a dead GK2 |
| 7 | W2 minus Hill, Xhaka for Gomez | 7 | +7.076 / +6.562 | 55.327 | PASS (+1.08) | none |
| 8 | Isak + Suzuki, Groß kept | 6 | +7.102 / +4.685 | 54.866 | PASS (+1.10) | none |
| 9 | Isak + Dewsbury-Hall + Kinsky | 7 | +6.916 / +5.223 | 54.866 | PASS (+0.92) | none |
| 10 | Isak + Kinsky, Groß kept | 6 | +6.666 / +4.392 | 54.866 | PASS (+0.67) | none |
| 11 | Isak + Xhaka + Suzuki | 7 | +6.327 / +4.282 | 54.866 | PASS (+0.33) | Groß → Xhaka −0.775 / −0.403 (loses on both) |
| 12 | Isak + Barnes + Kinsky, Hill for Calafiori | 7 | +6.258 / +7.264 | 54.708 | PASS (+0.26) | none |
| 13 | Raya kept: Kinsky, Hill, Justin, Gomez, Isak, Barnes | 6 | +6.216 / +7.219 | 54.961 | PASS (+0.22) | none |
| — | X1 (research-mid.md): Calafiori, Stach, Isak, Silva, Gomez, Justin | 6 | +9.338 / +3.626 | 55.790 | PASS on the files (+3.34) | Richards → Silva +1.387 / −1.269; Stach d 50% (13:13Z) priced at p 0.95; Dubravka dead → rejected |
| — | F1 (v3 plan, Saka) | 7 | refused | — | — | `Groß → Saka: 12 is not in the pool (unknown, or status not a/d)` |
| — | F1 frame, Groß kept (Wissa) | 6 | +3.659 / +4.001 | 54.506 | FAIL | — |
| — | F1 frame, Groß → Gibbs-White | 7 | +5.419 / +5.529 | 55.241 | FAIL | — |
| — | F1 frame, Groß → Rogers | 7 | +4.898 / +4.428 | 54.921 | FAIL | — |
| — | F1 frame, Groß → Ødegaard | 7 | +4.426 / +4.227 | 55.036 | FAIL | — |
| — | F1 frame, Groß → Barnes | 7 | +4.243 / +6.656 | 54.967 | FAIL | — |
| — | F1 frame, Groß → Dewsbury-Hall | 7 | +3.833 / +4.832 | 54.506 | FAIL | — |
| — | F1 frame, Groß → Xhaka | 7 | +2.808 / +3.598 | 54.506 | FAIL | Groß → Xhaka −0.851 / −0.403 |
| — | Free hit, W1 moves (GW8 alone) | 7 | +1.689 / +1.562 | 55.327 | FAIL | — |
| — | **Hold** (bank the free transfer, chip null) | 0 | +0.000 / +0.000 | 53.638 | — | — |

Not affordable on the floor basis (the CLI refused): João Pedro +
Dewsbury-Hall + Barnes + Suzuki (bank −0.4), Isak + Gibbs-White + Rudoni
(−1.1), Raya kept with Kinsky and Calafiori (−0.2). Palmer and B.Fernandes
packages are not re-graded: research-mid.md §3 found no Palmer package that
clears the gate (best +5.460) and no legal B.Fernandes package without
selling Gabriel for a promoted-club defender.

## Why this package — the justification the user asked for

The question is which option is best for the future, short and long term,
now that Saka is out. Every figure is on the same sell basis.

- **Short term (GW8).** W2's fielded XI is 55.052 after the C20 tie-break,
  against 53.638 for the hold: +1.41 this week. The hold fields Schade
  (p 0.80, form 0.5) and carries two dead bench slots (Shaw i, Dubravka
  p 0.03) with Richards as the only auto-sub cover.
- **Long term (GW8–13).** +8.304 blend / +8.078 prior-only. Prior-only is
  the reading with this season's seven games discounted, so it is the one
  that says most about what the squad does over the long run; W2's
  prior-only gain is within 0.55 of the Saka package's (+8.627) and
  above every other package graded. Blend and prior-only agree to within
  0.23, which is the "strong on both readings" test the delegation asked
  for; X1 scores +9.338 on blend but only +3.626 prior-only, and its
  margin rests on a sign-flipping Silva and an unpriced Stach flag.
- **What carries the gate.** Thiago → Isak (+3.314 / +1.636) is the one
  component without which the package fails: W2 with Wissa in Isak's place
  is the "F1 frame, Groß → Barnes" row, +4.243 / +6.656 FAIL. Removing any
  other single component keeps it over 6.0 (the next largest, Tarkowski →
  Calafiori +1.914, leaves ≈ +6.39). Isak's row is p_start 0.88 flat (MED):
  a/100, 6/7 starts, 78' in R7 after the R6 absence, LIV's first-choice
  striker with Ekitiké out and no return date. EP scales roughly with
  p_start, so the package holds the gate down to about p 0.83 and would
  fail near 0.80. Accepted: he is fit and flagged clean, and the prior-only
  component is positive, so the gate does not ride on a form premium.
- **Against holding.** The hold's value is the chip kept plus two free
  transfers at GW9, which research-mid.md §3c prices at roughly +2.7 to
  +3.1 blend over GW9–13 (CLI-graded pairs such as Richards → Silva + Shaw
  → Justin +3.10 / +0.80). The chip is +8.3 now, so playing it is worth
  about +5.3 blend and about +7 prior-only over the hold on this horizon.
  Nothing in GW8–13 argues for waiting: no blank or double (fixture
  analyst); the set-1 wildcard expires at GW19 whether or not a better week
  appears; Saka's return has no date, so a "wait for Saka" wildcard has
  nothing to wait for; and the wildcard leaves the free transfer unspent,
  so two FTs still bank at GW9 for the GW11 turn (SUN and NEW harden:
  E.Le Fée, Barnes).
- **Structure.** Bench of four playing rows (Kinsky 7/7 × 90, Justin,
  Gomez, Barry — all p ≥ 0.93), so the GW19 bench-boost earmark is live;
  no club above 2, so one bad club week costs at most two rows; the two
  biggest template holds stay (Haaland 77.2%, Calafiori 54.5%) and Isak
  (13.6%) replaces a 8.8%-owned Thiago.

Rejected, with the reason:

- **X1** (+9.338 / +3.626): +1.03 better on blend, −4.45 on prior-only.
  The gap rests on Richards → Silva (+1.387 / −1.269, a prior sign flip,
  C14's rule for hits applied to the package) and on Stach, who went d 50%
  (foot) in the 13:13 UTC refresh after players-MID.json priced him at
  p 0.95 every week; it also keeps Dubravka as a dead keeper. Fails the
  delegation's both-readings test.
- **W1 / Suzuki variants** (+7.762 / +7.340): −0.54 blend, −0.74 prior-only
  against W2. Suzuki's +0.44 over Kinsky costs the £0.5m that funds
  Richards → Hill (+0.978 / +1.031), and Raya → Trafford turns negative on
  both readings in the Suzuki pairing.
- **Van Hecke → Hill instead of Richards → Hill** (+7.425 / +7.349): the
  higher GW8 XI (55.531) but −0.88 blend over the horizon; Van Hecke
  (24.30) outscores Richards (22.70) by 1.6 EP6 for £0.0m, so Richards is
  the one to sell.
- **Groß kept** (+7.102 / +4.685 with Suzuki): Groß → Barnes is +0.813
  blend / +2.427 prior-only inside W2, outside the 0.5 band in which S8
  could break the tie toward Groß's 58-point record. Barnes is 7/7 × 90 at
  a club whose rows are steadier (NEW ATT rank 18 but 0.96 p_start), and
  his prior-only EP6 is 2.4 above Groß's.
- **Hill for Calafiori** (+6.258 / +7.264) and **Raya kept** (+6.216 /
  +7.219): no sign flip and a prior-only edge within 0.9 of W2, but −2.0
  blend and a gate margin of 0.2–0.3, inside Isak's own sensitivity.
- **Free hit** (+1.689 / +1.562 on GW8 alone): fails the 6.0 gate.
- **Hold** (+0.000): see above.

## Step 1 — budget skeleton

Premium-tier slots: Haaland 15.5 (sell basis; 3.65 EP6 clear of the pool's
#2 and the 3xc earmark) and Isak 9.0 (FWD #2, 28.62 / prior-only
positive). Saka is out of the pool. The split test: Isak's £2.9m over
Wissa buys the best MID upgrade found, Groß → Gibbs-White, and that
package (+5.419 / +5.529) fails the gate; every package that clears it
has Isak. Palmer 9.8 and B.Fernandes 11.8 are rejected on research-mid.md
§3 (no Palmer package clears the gate; no legal Fernandes package without
selling Gabriel for a promoted-club defender). Two premium-tier slots
leave £74.6m for 13; the budget is exhausted (bank 0.0).

## Step 2 — XI fill by raw EP

- GKP: Trafford 5.0 (21.70, pool #1). Raya 21.66 at 6.0 sells for +0.04
  EP6 and £1.0m; inside W2 the move is +0.042 / +0.045.
- DEF: Gabriel 28.58 (held), Calafiori 25.67 (6.0, the #3 DEF and the best
  with a full PL prior: 24.14 prior-only), Hill 24.95 (5.5, #4, 90 × 7,
  DefCon term 6.9), Van Hecke 24.30 (held), Justin 22.37 (4.5). Silva 25.85
  is the blend #2 but 21.87 prior-only — rejected above.
- MID: Mbeumo 30.43 (held), Tavernier 26.95 (held), E.Le Fée 26.20
  (held), Barnes 23.68 (6.1, 90 × 7), Gomez 22.86 (5.0, 7/7).
- FWD: Haaland 34.96 (held), Isak 28.62 (9.0), Barry 25.51 (held).

Clubs after: ARS, BOU, LEE, TOT at 2; the rest 1.

## Step 3 — bench

GK: **single playing keeper** Trafford, with Kinsky (TOT, 4.5, 7/7 × 90)
as a playing backup rather than a rotation partner — Kinsky's GW8–13 rows
are below Trafford's in five of six weeks (research-transfers.md §4), so
he is bought for auto-sub cover and the GW19 bench-boost earmark. Suzuki
(5.0) would add +0.44 but costs the £0.5m that funds Hill. Dubravka
(p 0.03) leaves.

Outfield bench: Justin 4.5 (p 0.95), Gomez 5.0 (p 0.93), Barry 5.6
(p 0.94). Justin is the £4.0–4.5m nailed starter the spec asks for.

## Step 4 — swap pass (audit trail)

Single-move table, no chip (`objective --gw 8 <basis> --top 15`), verbatim:

```
legal single moves: 1581 (pool 415); top 15 by blend:
  1 | Richards → Silva | +2.301 | -1.562 | bank 0.3 | fails (prior sign flip)
  2 | Schade → Stach | +1.764 | +0.894 | bank 0.6 | fails (blend < 2.0)
  3 | Tarkowski → Silva | +1.741 | -2.077 | bank 1.5 | fails (prior sign flip)
  4 | Tarkowski → Calafiori | +1.711 | +0.272 | bank 0.5 | fails (blend < 2.0)
  5 | Van Hecke → Silva | +1.551 | -1.835 | bank 0.3 | fails (prior sign flip)
  6 | Shaw → Justin | +1.439 | +2.019 | bank 0.2 | fails (blend < 2.0)
  7 | Groß → Stach | +1.382 | +0.535 | bank 0.3 | fails (blend < 2.0)
  8 | Schade → Barnes | +1.263 | +2.765 | bank 0.5 | fails (blend < 2.0)
  9 | Thiago → João Pedro | +1.139 | -0.516 | bank 0.3 | fails (prior sign flip)
  10 | Shaw → Konsa | +1.096 | +0.884 | bank 0.1 | fails (blend < 2.0)
  11 | Shaw → Affengruber | +1.094 | +0.626 | bank 0.2 | fails (blend < 2.0)
  12 | Shaw → Thomas | +1.056 | +0.090 | bank 0.7 | fails (blend < 2.0)
  13 | Tarkowski → Hill | +0.846 | +1.036 | bank 1.0 | fails (blend < 2.0)
  14 | Shaw → Bogle | +0.694 | +0.538 | bank 0.0 | fails (blend < 2.0)
  15 | Shaw → Elvedi | +0.683 | +0.829 | bank 0.2 | fails (blend < 2.0)
plan: none — blend +0.000 prior +0.000; bank 0.4; transfers 0 (free 1, hits 0); FT next 2
after plan, best single: Richards → Silva +2.301 / -1.562 — fails (prior sign flip)
reference (greedy): bank — no move passes its gate
verdict: PASS
```

No move passes the free gate without the chip, so the no-chip plan is bank
(2 FTs at GW9). Rows for the moves the open suggestions name, as singles on
the same basis, graded this run:

| Row | For | blend / prior | Verdict |
|---|---|---|---|
| Richards → Silva (202:566) | S7 (Richards a named faller) | +2.301 / −1.562 | FAIL, prior sign flip |
| Richards → Hill (202:60) | S7 | not in the top 15 as a single; inside the wildcard +0.978 / +1.031 | made under the chip |
| Shaw → Justin (423:332) | S7 (Shaw a named faller, status i) | +1.439 / +2.019 | FAIL as a single (blend < 2.0); inside the wildcard +1.138 / +1.482 |
| Thiago → João Pedro (106:165) | S7 (Thiago a named faller) | +1.139 / −0.516 | FAIL, prior sign flip; Thiago sold inside the wildcard for Isak (+3.314 / +1.636; not affordable as a single: 7.8 + 0.4 < 9.0) |
| Mbeumo → Gibbs-White (427:480) | S7 (Mbeumo a named faller) | −5.326 / −3.776 | FAIL |
| E.Le Fée → Stach (542:335) | S8 (Le Fée a named GW6 buy) | −0.968 / −0.700 | FAIL |
| Groß → Stach (124:335) | S8 (Groß a named GW6 buy) | +1.382 / +0.535 | FAIL as a single; Stach d 50% unpriced; Groß sold inside the wildcard for Barnes |
| Schade → Stach (94:335) | S8 (Schade a named GW6 buy) | +1.764 / +0.894 | FAIL as a single; Schade sold inside the wildcard for Gomez |

After the plan `objective` reports `best single: none legal`; the wildcard
uses no free transfer (FT 1 unchanged, 2 at GW9).

## Squad

Price = purchase price for buys, GW7-verified selling price for kept players
(now_cost in brackets where different). EP6 = `ep_total6`, GW8 = `ep_gw[0]`.

| Slot | Pos | Player | Id | Club | Price | GW8 EP | EP6 | p_start GW8 | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|
| 1 | GKP | Trafford | 385 | LEE | 5.0 | 3.574 | 21.70 | 0.95 | XI · IN |
| 2 | DEF | Gabriel | 4 | ARS | 7.9 | 5.080 | 28.58 | 0.95 | XI · Vice |
| 3 | DEF | Calafiori | 8 | ARS | 6.0 | 4.596 | 25.67 | 0.94 | XI · IN |
| 4 | DEF | Hill | 60 | BOU | 5.5 | 3.977 | 24.95 | 0.95 | XI · IN |
| 5 | DEF | Van Hecke | 112 | TOT | 4.9 | 3.565 | 24.30 | 0.95 | XI |
| 6 | MID | Mbeumo | 427 | MUN | 7.9 | 4.932 | 30.43 | 0.96 | XI |
| 7 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.406 | 26.20 | 0.94 | XI |
| 8 | MID | Tavernier | 68 | BOU | 6.0 (6.2) | 4.351 | 26.95 | 0.93 | XI |
| 9 | MID | Barnes | 453 | NEW | 6.1 | 4.121 | 23.68 | 0.96 | XI · IN |
| 10 | FWD | Haaland | 411 | MCI | 15.5 (15.7) | 5.798 | 34.96 | 0.94 | XI · Captain |
| 11 | FWD | Isak | 379 | LIV | 9.0 | 4.854 | 28.62 | 0.88 | XI · IN |
| 12 | GKP | Kinsky | 496 | TOT | 4.5 | 2.916 | 19.06 | 0.95 | Bench GK · IN |
| 13 | DEF | Justin | 332 | LEE | 4.5 | 3.773 | 22.37 | 0.95 | Bench 1 · IN |
| 14 | MID | Gomez | 127 | BHA | 5.0 | 3.541 | 22.86 | 0.93 | Bench 2 · IN |
| 15 | FWD | Barry | 249 | EVE | 5.6 (5.7) | 3.660 | 25.51 | 0.94 | Bench 3 |
| | | **Total** | | | **99.1** | | | | |

2 GKP / 5 DEF / 5 MID / 3 FWD. Max club count 2 (ARS, BOU, LEE, TOT).

## Starting XI — 4-4-2

The objective's best GW8 XI is the 4-4-2 above (55.260 with captain),
Justin in and Van Hecke on the bench. C20 applies C8's tie-break at the
XI/bench boundary: Justin 3.773 (DefCon share 0.161) and Van Hecke 3.565
(0.190) are 0.208 apart, inside the 0.25 band, so Van Hecke starts and
Justin sits (−0.208 EP). Barnes 4.121 against Van Hecke is 0.556 apart,
outside the band, so a 5-3-2 with both full-backs is not taken. The other
boundary pairs the objective prints (Barry 0.008, Gomez 0.139) sit below
Van Hecke on floor share after the swap.

| Slot | Player | Pos | GW8 fixture | GW8 EP |
|---:|---|---|---|---:|
| 1 | Trafford | GKP | SUN (A) | 3.574 |
| 2 | Gabriel (V) | DEF | EVE (H) | 5.080 |
| 3 | Calafiori | DEF | EVE (H) | 4.596 |
| 4 | Hill | DEF | MUN (A) | 3.977 |
| 5 | Van Hecke | DEF | CHE (A) | 3.565 |
| 6 | Mbeumo | MID | BOU (H) | 4.932 |
| 7 | E.Le Fée | MID | LEE (H) | 4.406 |
| 8 | Tavernier | MID | MUN (A) | 4.351 |
| 9 | Barnes | MID | CRY (A) | 4.121 |
| 10 | Haaland (C) | FWD | AVL (A) | 5.798 |
| 11 | Isak | FWD | BHA (H) | 4.854 |
| | XI total | | | 49.254 |
| | + captain | | | 5.798 |
| | **Predicted GW8** | | | **55.052** |

C12: no XI row is a promoted-club fixture this GW.

## Captain and vice

Top 5 in the XI by single-GW EP, undiscounted (`objective` captain line):

| Rank | Player | GW8 EP | p_start_gw[0] |
|---:|---|---:|---:|
| 1 | **Haaland** (C) | 5.798 | 0.94 |
| 2 | Gabriel (V) | 5.080 | 0.95 |
| 3 | Mbeumo | 4.932 | 0.96 |
| 4 | Isak | 4.854 | 0.88 |
| 5 | Calafiori | 4.596 | 0.94 |

Captain Haaland, 0.718 clear of Gabriel — outside the 0.5 band, EP decides.
Vice Gabriel: 0.148 over Mbeumo, inside the band; both p_start_gw[0] ≥
0.85, so the tiebreak does not separate them and the higher EP holds (S8's
read is mixed: Mbeumo 41 pts v Gabriel 35, four returns each, Gabriel at
the more consistent club).

## Bench order

| Slot | Player | Pos | GW8 EP | p_start | DefCon share |
|---:|---|---|---:|---:|---:|
| 12 | Kinsky | GKP | 2.916 | 0.95 | — |
| 13 | Justin | DEF | 3.773 | 0.95 | 0.161 |
| 14 | Gomez | MID | 3.541 | 0.93 | 0.139 |
| 15 | Barry | FWD | 3.660 | 0.94 | 0.008 |

Justin first: the highest bench EP and within C8's band of both others
with the higher floor share. Gomez ahead of Barry: 0.119 apart, inside the
band, higher DefCon share first. Kinsky is the only other keeper.

Bench check: none

## Transfers (wildcard, cost 0)

| Out | Id | Sell (GW7 verified) | In | Id | Buy |
|---|---:|---:|---|---:|---:|
| Raya (ARS, GKP) | 1 | 6.0 | Trafford (LEE, GKP) | 385 | 5.0 |
| Dubravka (TOT, GKP) | 497 | 4.0 | Kinsky (TOT, GKP) | 496 | 4.5 |
| Tarkowski (EVE, DEF) | 229 | 6.1 | Calafiori (ARS, DEF) | 8 | 6.0 |
| Richards (CRY, DEF) | 202 | 4.9 | Hill (BOU, DEF) | 60 | 5.5 |
| Shaw (MUN, DEF, status i) | 423 | 4.3 | Justin (LEE, DEF) | 332 | 4.5 |
| Groß (BHA, MID) | 124 | 5.9 | Barnes (NEW, MID) | 453 | 6.1 |
| Schade (BRE, MID) | 94 | 6.2 | Gomez (BHA, MID) | 127 | 5.0 |
| Thiago (BRE, FWD) | 106 | 7.8 | Isak (LIV, FWD) | 379 | 9.0 |
| | | 45.2 | | | 45.6 |

Bank after: 0.4 + 45.2 − 45.6 = **0.0** on the GW7-verified basis. The
deadline is today and the overnight price run has passed, so no price moves
before the POST; the plan-builder's `purchase_price_at_plan` audit covers
drift. Execution (review F9): the session was expired at step 1 — the chip
rides the make-transfers POST, so if credentials are not re-captured the
user applies by hand and must **activate the wildcard before confirming the
eight transfers**, or the site books seven of them as hits.

Gate ids: 385,496,4,8,60,112,427,542,68,453,411,379,332,127,249

## Chips

`chip: wildcard` — set-1 wildcard, window GW2–19 (bootstrap `chips`),
unused, clears the gate (+8.304 ≥ 6.0 blend, +8.078 ≥ 0 prior-only over
the greedy plan, which is bank). Free hit on the same moves fails (+1.689
on GW8 alone). No blank or double in GW8–13; S6's window ends this GW.

Provisional chip plan (windows from bootstrap `chips`: freehit GW2–19,
bboost and 3xc GW1–19):

- 3xc GW9 — Haaland v BHA (H), his own GW9 row 6.276 (C5: on his own EP;
  MCI λ_att supports but does not carry it). His GW11 row FUL (H) 6.371 is
  0.095 higher, inside noise; the GW9 cycle decides on fresh EP.
- freehit GW16 — placeholder, no blank or double in GW8–13.
- bboost GW19 — placeholder; live now that the bench is four playing rows
  (Kinsky, Justin, Gomez, Barry).

## Rationale and rejected alternatives

- The user delegated the choice; the freshness gate removed the Saka
  package; this run searched afresh on the updated files and found W2 the
  best package on both readings, legal, bank 0.0, no club above 2, gate
  PASS by 2.304.
- Where the gain comes from: Thiago → Isak +3.314 / +1.636 is the largest
  component and the one the gate needs; Tarkowski → Calafiori +1.914 /
  +0.820, Shaw → Justin +1.138 / +1.482, Richards → Hill +0.978 / +1.031
  and Groß → Barnes +0.813 / +2.427 add the rest of substance; Schade →
  Gomez, Dubravka → Kinsky and Raya → Trafford are small positives on both
  readings that fund the structure.
- Review findings carried as accepted risk (final.md should name them):
  F3 template exposure — held > 30%-owned: Haaland, Calafiori; sold Raya
  (45.1%) and Groß (45.9%); still off João Pedro (73.4%), Rogers, De
  Cuyper, Cherki, B.Fernandes; F7 price risk ≈ −0.1m (Barnes net −48k,
  Kinsky net −64k; Raya and Groß sold as net risers); F10 SUN and NEW turn
  hard from GW11, two free transfers at GW9 cover it. F2 (Saka) is closed:
  he is not bought.
- Data note for the finalizer and retro: the 13:13 UTC refresh moved Stach
  and Calvert-Lewin to d 50% with gate_changed false, so no REOPEN re-priced
  them; neither is in this squad (backlog row appended).
- Risks: Isak's minutes (p 0.88 flat, MED; the gate margin tolerates about
  0.83); Hill is a 21-point DefCon profile at 0.8% owned, so his EP is
  floor not ceiling; Justin v Van Hecke v Barry sit 0.2 apart at the
  boundary, so one news item can reorder the back line; bank 0.0 leaves no
  room for a price-driven refusal if `my-team` shows a selling price below
  the GW7 figure (none is expected: every now_cost is ≥ the GW7 sell
  price).

## Suggestions

Read data/suggestions.md through S8

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 6 | followed | both halves now complete: Ndiaye → Groß and Anderson → Schade inside the +14.449 blend / +5.210 prior-only triple; Ndiaye's marginal +2.503 / +0.665 and Anderson's +2.488 / +0.757 each clear the 2.0 gate on their own, so the steer broke no tie and the optimizer reached it unaided; EP6 delta of the row itself 0.00. The GW5 ledger's "Ndiaye half completed" was false in fact (never POSTed) and is superseded here |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |
| S3 | 6 | followed | Ndiaye → Groß made; marginal +2.503 blend / +0.665 prior against the plan without this sale (Scott + Anderson → E.Le Fée + Schade, +11.946 / +4.545), so the below-threshold clause was not needed |
| S4 | 6 | followed | Anderson → Schade made; marginal +2.488 blend / +0.757 prior against the plan without this sale (Scott + Ndiaye → E.Le Fée + Groß, +11.961 / +4.453); clears the gate on both readings, below-threshold clause not needed |
| S5 | 6 | followed | Scott → E.Le Fée made; EP6 0.00 for GW6–11 (status i, 0%); marginal +2.503 / +0.675 against the plan without this sale (Ndiaye + Anderson → E.Le Fée + Schade, +11.946 / +4.535) |
| S6 | 8 | followed | wildcard played at GW8, the timing the row left open (GW6 or GW8): the package +8.304 blend / +8.078 prior-only clears the chip gate against bank (+0.000); EP per GW over GW8–13 rises from 54.68 to 56.06 (336.354 / 6, captain included); the user's earlier hold today was withdrawn by the delegation quoted in this proposal; not taken: 60 per GW stays unreachable — the best package found on the post-Saka files is 56.06 |
| S7 | 7 | standing | honoured as a sell-side policy (review F5): the wildcard sells five net fallers — Thiago (net −21k this event), Shaw (−85k, status i), Richards (−567, a named faller), Tarkowski (−25k) and Dubravka (−25k); of the named fallers, Richards → Silva +2.301 / −1.562 (prior sign flip) and Thiago → João Pedro +1.139 / −0.516 (flip) FAIL as singles, Richards → Hill +0.978 / +1.031 and Thiago → Isak +3.314 / +1.636 are made inside the chip, Mbeumo → Gibbs-White −5.326 / −3.776 FAIL and Mbeumo is now a net riser (+197k) so he is held; the buys are net risers bar Barnes (−48k) and Kinsky (−64k), an expected −0.1 each after the deadline accepted against +8.304 EP6; Raya (+127k) and Groß (+234k) are sold before a rise, a cost of at most 0.1 each, justified by +0.042 / +0.045 and +0.813 / +2.427; EP6 delta of the row 0.00; policy stays live for GW9 with 2 FTs |
| S8 | 7 | standing | honoured: seven of the eight buys are unbroken-streak starters at p_start 0.93–0.96 (Trafford 7/7 × 90, Kinsky 7/7 × 90, Calafiori 7/7, Hill 7/7 × 90, Justin 7/7, Barnes 7/7 × 90, Gomez 7/7); the eighth, Isak (p 0.88, 6/7 starts, 42 pts, LIV), is the pool's #2 FWD on both readings and the component the chip gate needs, so the steer cannot override it; Groß (58 pts, the squad's best record bar Haaland) is sold for Barnes because Groß → Barnes is +0.813 blend / +2.427 prior-only inside the package, outside the 0.5 band in which the row could break a tie; Stach, the row's GW6-buy replacement candidate, went d 50% (foot) after the MID file was built and is not bought; the GW6 buys Groß and Schade are sold, E.Le Fée held (E.Le Fée → Stach −0.968 / −0.700 FAIL); vice tie Gabriel 5.080 v Mbeumo 4.932 inside 0.5 single-GW EP is mixed on the row's read (Mbeumo 41 pts v Gabriel 35, four returns each; Gabriel at the more consistent club), so the higher EP holds; EP6 delta of the row 0.00 |

Malformed: none

## STATE

```yaml
# free_transfers_banked = FTs available at the GW9 deadline: 1 unchanged under the wildcard, 1 accrues.
# team_value and bank on the GW7-verified selling-price basis (my-team not read this cycle, session expired): kept players at GW7 sell prices 53.5 + buys at purchase 45.6 = 99.1, bank 0.0.
gw: 8
team_id: 8455344
team_value: 99.1
bank: 0.0
free_transfers_banked: 2
chip: wildcard
chips_used: []
transfers_made:
  - {out: Raya, in: Trafford, cost: 0}
  - {out: Dubravka, in: Kinsky, cost: 0}
  - {out: Tarkowski, in: Calafiori, cost: 0}
  - {out: Richards, in: Hill, cost: 0}
  - {out: Shaw, in: Justin, cost: 0}
  - {out: Groß, in: Barnes, cost: 0}
  - {out: Schade, in: Gomez, cost: 0}
  - {out: Thiago, in: Isak, cost: 0}
chip_plan:
  - {chip: 3xc, gw: 9, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 385, name: Trafford, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: false, vice: true}
  - {id: 8, name: Calafiori, position: 3, captain: false, vice: false}
  - {id: 60, name: Hill, position: 4, captain: false, vice: false}
  - {id: 112, name: Van Hecke, position: 5, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 6, captain: false, vice: false}
  - {id: 542, name: E.Le Fée, position: 7, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 8, captain: false, vice: false}
  - {id: 453, name: Barnes, position: 9, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 10, captain: true, vice: false}
  - {id: 379, name: Isak, position: 11, captain: false, vice: false}
  - {id: 496, name: Kinsky, position: 12, captain: false, vice: false}
  - {id: 332, name: Justin, position: 13, captain: false, vice: false}
  - {id: 127, name: Gomez, position: 14, captain: false, vice: false}
  - {id: 249, name: Barry, position: 15, captain: false, vice: false}
```
