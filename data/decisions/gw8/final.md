# GW8 Final (2026/27)

Deadline **2026-10-23T17:30:00Z**. Written after a REOPEN: the 13:40 UTC
freshness gate fired on Saka (d 50% → i, unknown return date), the MID
analyst re-ran in REOPEN mode, and the optimizer re-searched on the updated
files (data/decisions/gw8/squad-proposal.md; earlier runs archived as
squad-proposal.v1–v3.md). data/decisions/gw8/final.v1.md is a superseded
no-chip final from earlier in the cycle and is not the previous final; the
previous final is data/decisions/gw7/final.md.

The wildcard decision was delegated by the user, quoted verbatim: "Ignore
all my suggestions made today, Out of all the suggestions that you made,
select which is best for the future, both in terms of short term and long
term. You have my belief. I need you to justify your actions and then make
a decision."

**Set-1 wildcard. Eight transfers, hit 0. Bank £0.0m. 4-4-2, Haaland (C),
Gabriel (V). Predicted GW8 55.052. 2 free transfers at the GW9 deadline.**

## Freshness gate

`fpl flags --gw 8` refreshed at 2026-10-23 13:53:31 UTC on the proposal's
`Gate ids:` line (the 15 squad ids, which include all eight transfers-in),
against baseline `data/raw/gw8/.archive/bootstrap-20261023T134015_536401Z.json`
(age 0.2h). Exit 0. Delta:
`data/raw/gw8/flags-delta-20261023T135331_453649Z.json`.

| Result | Detail |
|---|---|
| **PASS** | 0 of 15 gate ids changed. All 15 status `a`; Haaland, Isak and Van Hecke chance 100. Pool (informational): 0 changed. |

## Entry state

`fpl my-team --gw 8` could not be read: data/auth.json exists but the
session is expired and the token refresh failed (invalid_grant). The
`team_value` check therefore did not run. The proposal's `team_value` 99.1
and `bank` 0.0 stand on the GW7-verified selling-price basis (`my-team`
budget 99.1 at GW7, no transfer made since) and are copied unchanged. Kept
players at GW7 sell prices sum to 53.5, buys at purchase price to 45.6.
Every kept player's now_cost is at or above his GW7 sell price, so 99.1 is
a floor and the true bank is at least 0.0. Not re-verified this GW.

## Squad — predicted points (calibration record)

`GW8 EP` = `ep_gw[0]`, `EP6` = `ep_total6`, `p_start GW8` = `p_start_gw[0]`
from `data/analysis/gw8/players-{pos}.json`, copied as written there. Price =
purchase price for buys, GW7-verified selling price for kept players
(now_cost in brackets where different).

| Slot | Pos | Player | Id | Club | Price | GW8 EP | EP6 | p_start GW8 | Unc | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---|---|
| 1 | GKP | Trafford | 385 | LEE | 5.0 | 3.574 | 21.7 | 0.95 | LOW | XI · IN |
| 2 | DEF | Gabriel | 4 | ARS | 7.9 | 5.08 | 28.58 | 0.95 | LOW | XI · Vice |
| 3 | DEF | Calafiori | 8 | ARS | 6.0 | 4.596 | 25.67 | 0.94 | LOW | XI · IN |
| 4 | DEF | Hill | 60 | BOU | 5.5 | 3.977 | 24.95 | 0.95 | LOW | XI · IN |
| 5 | DEF | Van Hecke | 112 | TOT | 4.9 | 3.565 | 24.3 | 0.95 | LOW | XI |
| 6 | MID | Mbeumo | 427 | MUN | 7.9 | 4.932 | 30.43 | 0.96 | LOW | XI |
| 7 | MID | E.Le Fée | 542 | SUN | 5.7 | 4.406 | 26.2 | 0.94 | LOW | XI |
| 8 | MID | Tavernier | 68 | BOU | 6.0 (6.2) | 4.351 | 26.95 | 0.93 | LOW | XI |
| 9 | MID | Barnes | 453 | NEW | 6.1 | 4.121 | 23.68 | 0.96 | LOW | XI · IN |
| 10 | FWD | Haaland | 411 | MCI | 15.5 (15.7) | 5.798 | 34.96 | 0.94 | LOW | XI · Captain |
| 11 | FWD | Isak | 379 | LIV | 9.0 | 4.854 | 28.62 | 0.88 | MED | XI · IN |
| 12 | GKP | Kinsky | 496 | TOT | 4.5 | 2.916 | 19.06 | 0.95 | LOW | Bench GK · IN |
| 13 | DEF | Justin | 332 | LEE | 4.5 | 3.773 | 22.37 | 0.95 | LOW | Bench 1 · IN |
| 14 | MID | Gomez | 127 | BHA | 5.0 | 3.541 | 22.86 | 0.93 | LOW | Bench 2 · IN |
| 15 | FWD | Barry | 249 | EVE | 5.6 (5.7) | 3.66 | 25.51 | 0.94 | LOW | Bench 3 |
| | | **Total** | | | **99.1** + bank 0.0 | | | | | |

2 GKP / 5 DEF / 5 MID / 3 FWD. Clubs: ARS 2, BOU 2, LEE 2, TOT 2; MUN, SUN,
NEW, MCI, LIV, BHA, EVE 1 each. No club at 3.

## Starting XI — 4-4-2

| Slot | Player | Pos | GW8 fixture | GW8 EP |
|---:|---|---|---|---:|
| 1 | Trafford | GKP | SUN (A) | 3.574 |
| 2 | Gabriel (V) | DEF | EVE (H) | 5.08 |
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

The objective's best XI started Justin over Van Hecke (55.260); C20 applies
C8's tie-break at the XI/bench boundary (Justin 3.773, DefCon share 0.161 v
Van Hecke 3.565, 0.190; 0.208 apart, inside 0.25), so Van Hecke starts at a
cost of 0.208 EP. No XI row is a promoted-club fixture (C12).

## Captain and vice

- **Captain Haaland** 5.798 — 0.718 clear of Gabriel, outside the 0.5 band.
- **Vice Gabriel** 5.080 — 0.148 over Mbeumo 4.932, inside the band, both
  p_start ≥ 0.85; S8's read is mixed, so the higher EP holds.

## Bench order

| Slot | Player | Pos | GW8 EP | p_start | DefCon share |
|---:|---|---|---:|---:|---:|
| 12 | Kinsky | GKP | 2.916 | 0.95 | — |
| 13 | Justin | DEF | 3.773 | 0.95 | 0.161 |
| 14 | Gomez | MID | 3.541 | 0.93 | 0.139 |
| 15 | Barry | FWD | 3.66 | 0.94 | 0.008 |

Four playing bench rows; both dead slots of GW7 (Dubravka p 0.03, Shaw `i`)
are gone.

## Transfers (wildcard, cost 0)

| Out | Id | Sell (GW7 verified) | In | Id | Buy | Cost |
|---|---:|---:|---|---:|---:|---:|
| Raya (ARS, GKP) | 1 | 6.0 | Trafford (LEE, GKP) | 385 | 5.0 | 0 |
| Dubravka (TOT, GKP) | 497 | 4.0 | Kinsky (TOT, GKP) | 496 | 4.5 | 0 |
| Tarkowski (EVE, DEF) | 229 | 6.1 | Calafiori (ARS, DEF) | 8 | 6.0 | 0 |
| Richards (CRY, DEF) | 202 | 4.9 | Hill (BOU, DEF) | 60 | 5.5 | 0 |
| Shaw (MUN, DEF) | 423 | 4.3 | Justin (LEE, DEF) | 332 | 4.5 | 0 |
| Groß (BHA, MID) | 124 | 5.9 | Barnes (NEW, MID) | 453 | 6.1 | 0 |
| Schade (BRE, MID) | 94 | 6.2 | Gomez (BHA, MID) | 127 | 5.0 | 0 |
| Thiago (BRE, FWD) | 106 | 7.8 | Isak (LIV, FWD) | 379 | 9.0 | 0 |
| | | 45.2 | | | 45.6 | 0 |

Bank 0.4 + 45.2 − 45.6 = 0.0 on the GW7-verified basis. The wildcard uses
no free transfer: 1 FT unchanged, 2 at the GW9 deadline.

Execution: transfers first, then the lineup. The wildcard rides the
make-transfers POST. Credentials are expired, so unless they are
re-captured and imported (`auth-import`) before 17:30 UTC the user applies
by hand and must **activate the wildcard before confirming the eight
transfers**, or the site books seven of them as −4 hits (review F9).

## Chips

`chip: wildcard` — set-1 wildcard, window GW2–19 in bootstrap `chips`,
unused (`chips_used` empty), one chip this GW. It clears the chip gate:
+8.304 blend (≥ 6.0) and +8.078 prior-only (≥ 0) over the greedy plan,
which is bank. Free hit on the same moves fails (+1.689 on GW8 alone).

Provisional plan (windows from bootstrap: freehit GW2–19, bboost and 3xc
GW1–19), all in `chip_plan`:

- 3xc GW9 — Haaland v BHA (H); the GW9 cycle decides on fresh EP.
- freehit GW16 — placeholder; no blank or double in GW8–13.
- bboost GW19 — placeholder; live now that the bench is four playing rows.

## Accepted risks

The review (data/decisions/gw8/review.md) graded the v1 proposal (plan C,
Saka + Wissa + Silva). **W2 was not separately red-teamed.** The review's F1
frame (Calafiori funded by a Kinsky GK2, no Silva) was adopted, then
re-searched after Saka's injury.

| Review id | Status in W2 | Detail |
|---|---|---|
| F1 (HIGH) | fixed | Calafiori + Kinsky in, Silva not bought; no package component has a prior-only sign flip (smallest prior-only marginal Raya → Trafford +0.045) |
| F2 (MED) | lapsed | Saka is not bought; he is `i` and out of the pool |
| F3 (MED) | **accepted** | Template exposure. Held > 30%-owned: Haaland, Calafiori. Sold Raya (45.1%) and Groß (45.9%). Still off João Pedro (73.4%), Rogers, De Cuyper, Cherki, B.Fernandes. A haul from one of them lands as rank loss |
| F4 (MED) | resolved | Isak replaces the Wissa / Calvert-Lewin choice; neither is bought (Calvert-Lewin went d 50% at 13:13Z) |
| F5 (MED) | **accepted** | Two of the buys are net fallers this event: Barnes (net −48k) and Kinsky (net −64k), about −0.1m each after the deadline. The S7 reason now states S7 is read as a sell-side policy and accepts this cost explicitly |
| F7 (LOW) | accepted | Price risk ≈ −0.1m net; Raya and Groß sold as net risers |
| F9 (LOW) | accepted | Execution with expired credentials; see Transfers |
| F10 (LOW) | accepted | SUN (E.Le Fée) and NEW (Barnes) turn hard from GW11; two free transfers at GW9 cover it |

Other risks named by the proposal:

- Isak p_start 0.88 flat (MED). He is the component the chip gate needs;
  the package holds the 6.0 gate down to about p 0.83 and would fail near
  0.80.
- Stach and Calvert-Lewin moved to d 50% at the 13:13Z refresh with no
  REOPEN; neither is bought, so nothing here rests on them.
- Justin, Van Hecke and Barry sit within about 0.2 EP at the XI/bench
  boundary; one news item can reorder the back line.
- Bank 0.0 leaves no margin if `my-team` shows a selling price below the
  GW7 figure at POST time (none expected: every now_cost ≥ GW7 sell price).

## Rationale summary

The user delegated the choice. The freshness gate removed the Saka package
(`objective` refuses him: not in the a/d pool). The optimizer's fresh search
found W2 the strongest package on both readings: +8.304 blend / +8.078
prior-only over GW8–13, gate margin 2.304, no prior sign flip. Thiago →
Isak (+3.314 / +1.636) carries the gate; Tarkowski → Calafiori, Shaw →
Justin, Richards → Hill and Groß → Barnes add the rest of substance.

- Short term: GW8 XI 55.052 against 53.638 for the hold (+1.41).
- Long term: blend and prior-only agree within 0.23. X1 (+9.338 blend) was
  rejected for its +3.626 prior-only reading, a sign-flipping Silva and an
  unpriced Stach flag.
- Against holding: two FTs at GW9 are worth roughly +2.7 to +3.1 blend over
  GW9–13; the chip is worth +8.3 now. No blank or double in GW8–13, the
  set-1 wildcard expires at GW19, and Saka has no return date to wait for.
- Structure: no club above 2, four playing bench rows, two premium slots
  (Haaland, Isak).

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
