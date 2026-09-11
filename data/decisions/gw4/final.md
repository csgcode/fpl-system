# GW4 Final Decision (2026/27)

Deadline **2026-09-12T12:30:00Z**. Weekly cycle. Verdict from
`data/decisions/gw4/review.md`: **APPROVE**, no HIGH findings — no revision
loop. Sources: `data/decisions/gw4/squad-proposal.md`, that review,
`data/analysis/gw4/players-{GKP,DEF,MID,FWD}.json`, `data/raw/gw4/` (snapshot
2026-09-11T17:58Z), STATE block of `data/decisions/gw3/final.md`,
`data/suggestions.md` through S2.

**No transfer — the free transfer is banked (2 available at the GW5
deadline). Hit 0. Bank £0.0m. 3-4-3, Haaland (C), Gabriel (V). Predicted GW4
55.20. No chip.**

## Freshness gate — PASS

`fpl flags --gw 4 --ids 1,4,229,202,68,427,69,237,411,106,249,497,481,445,423`
refreshed 2026-09-11T18:54:16Z (the 15 selected ids; no transfer, so no
outgoing player to add). Compared field-by-field against
`data/raw/gw4/players-slim.csv` (fetched 2026-09-11T17:58Z).

| Field | Live reading | Baseline | Delta |
|---|---|---|---|
| `status` | `a` for 14; Shaw (423) `d` | `a` for 14; Shaw `d` | none |
| `chance_of_playing_next_round` | null for 13; Anderson (481) `100`; Shaw `75` | identical | none |
| `news` | blank for 14; Shaw `Unspecified injury - 75% chance of playing` | identical | none |
| Shaw `news_added` | 2026-09-11T13:00:09.030120Z | identical | none |
| Anderson `news_added` | 2026-08-23T17:00:07.952697Z | identical | none |

No change to any gated field for any selected player. Shaw's 75% flag was
already in the baseline snapshot (raised 13:00, snapshot 17:58) — a match, not
a change. Anderson's 23 Aug `news_added` at `cop 100` is the stale-cleared
flag the GW2 baseline recorded; unchanged, so not a REOPEN. Raw snapshot age
at write time ≈ 2h; the 24h window closes 2026-09-12T17:58Z, after the
deadline.

## Squad (15) — sell value £99.4m + bank £0.0m = team value £99.4m

EP figures are the code's `ep_gw[0]` (GW4) and `ep_total6` (GW4–9) from
`data/analysis/gw4/players-{pos}.json`. Nothing is recomputed here; this table
is the calibration raw material for `fpl calibrate --round 4`. `Sell` is the
authenticated `my-team` selling price; `Buy` is the bootstrap `now_cost`.

| Slot | Pos | Player | Id | Club | Sell | Buy | GW4 EP | EP6 | p_start | Unc | Role |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---|---|
| 1 | GKP | Raya | 1 | ARS | 6.0 | 6.0 | 3.776 | 21.76 | 0.96 | LOW | XI |
| 2 | DEF | Gabriel | 4 | ARS | 8.0 | 8.0 | 5.046 | 29.41 | 0.93 | LOW | XI · **Vice** |
| 3 | DEF | Tarkowski | 229 | EVE | 6.0 | 6.0 | 4.333 | 24.78 | 0.92 | LOW | XI |
| 4 | DEF | Richards | 202 | CRY | 5.0 | 5.0 | 3.794 | 20.97 | 0.90 | LOW | XI |
| 5 | MID | Tavernier | 68 | BOU | 6.0 | 6.0 | 5.000 | 29.68 | 0.93 | LOW | XI |
| 6 | MID | Mbeumo | 427 | MUN | 7.9 | 7.9 | 4.822 | 31.02 | 0.93 | LOW | XI |
| 7 | MID | Scott | 69 | BOU | 6.0 | 6.1 | 4.146 | 24.78 | 0.93 | LOW | XI |
| 8 | MID | Ndiaye | 237 | MCI | 5.9 | 5.9 | 4.042 | 25.40 | 0.93 | LOW | XI |
| 9 | FWD | Haaland | 411 | MCI | 15.5 | 15.5 | 5.998 | 37.94 | 0.93 | LOW | XI · **Captain** |
| 10 | FWD | Thiago | 106 | BRE | 7.9 | 7.9 | 4.375 | 27.69 | 0.92 | LOW | XI |
| 11 | FWD | Barry | 249 | EVE | 5.5 | 5.6 | 3.874 | 24.25 | 0.88 | LOW | XI |
| 12 | GKP | Dubravka | 497 | TOT | 4.0 | 4.0 | 0.152 | 0.89 | 0.04 | HIGH | Bench GK |
| 13 | MID | Anderson | 481 | MCI | 6.3 | 6.3 | 3.853 | 24.00 | 0.92 | LOW | Bench 1 |
| 14 | DEF | Thiaw | 445 | NEW | 5.0 | 5.0 | 3.209 | 21.74 | 0.90 | LOW | Bench 2 |
| 15 | DEF | Shaw | 423 | MUN | 4.4 | 4.4 | 1.459 | 13.12 | 0.62 | HIGH | Bench 3 |
| | | **Total** | | | **99.4** | 99.6 | | 357.43 | | | |

Constraints: 2 GKP / 5 DEF / 5 MID / 3 FWD ✓ · Σ sell **99.4** + bank 0.0 =
team value 99.4, no spend this GW ✓ · club counts MCI 3 (Haaland, Ndiaye,
Anderson), ARS 2, EVE 2, MUN 2, BOU 2, CRY 1, BRE 1, TOT 1, NEW 1 — all ≤ 3 ✓
· 15 unique ids ✓. Dubravka and Shaw are the only non-LOW rows and occupy
bench slots 12 and 15.

**Team-value basis.** The authenticated `my-team` read (2026-09-11 ~18:10Z)
prints `value 99.6`, which equals the bootstrap `now_cost` sum of the fifteen
`Buy` prices above, not the sum of its own selling-price rows. The selling
prices sum to 99.4 (Scott and Barry each sell 0.1 below purchase; the other
thirteen are level). `team_value: 99.4` is the sell-price basis, consistent
with GW2/GW3's convention of sell value + bank, and is the figure carried in
the STATE block. Reconciliation is closed — no discrepancy remains, only two
different fields with two different meanings.

## Starting XI — 3-4-3

| Slot | Player | Club | Pos | GW4 fixture | GW4 EP |
|---:|---|---|---|---|---:|
| 1 | Raya | ARS | GKP | SUN (A) | 3.776 |
| 2 | Gabriel **(V)** | ARS | DEF | SUN (A) | 5.046 |
| 3 | Tarkowski | EVE | DEF | TOT (A) | 4.333 |
| 4 | Richards | CRY | DEF | IPS (H) | 3.794 |
| 5 | Tavernier | BOU | MID | BRE (H) | 5.000 |
| 6 | Mbeumo | MUN | MID | MCI (H) | 4.822 |
| 7 | Scott | BOU | MID | BRE (H) | 4.146 |
| 8 | Ndiaye | MCI | MID | MUN (A) | 4.042 |
| 9 | Haaland **(C)** | MCI | FWD | MUN (A) | 5.998 |
| 10 | Thiago | BRE | FWD | BOU (A) | 4.375 |
| 11 | Barry | EVE | FWD | TOT (A) | 3.874 |
| | **XI total** | | | | **49.21** |
| | + captain (Haaland) | | | | 5.998 |
| | **Predicted GW4** | | | | **55.20** |

Formation 3-4-3: 1 GK, 3 DEF, 4 MID, 3 FWD ✓ (≥ 3 DEF, ≥ 2 MID, ≥ 1 FWD).
Exactly one captain and one vice, both in the XI ✓. The proposal's headline
55.21 is the same quantity summed from its 2-decimal table; 55.20 is the sum
of the code's `ep_gw[0]` values and is the figure calibration will score.

**Captain Haaland** — 6.00 blend, 0.95 clear of the field (Gabriel 5.05,
Tavernier 5.00), above the 0.5 tie band, so no suggestion or variance argument
enters. The prior-only reading narrows the gap to 0.30 but does not flip it.
**Vice Gabriel** — highest of the three inside the 0.5 band, on a different
fixture from the captain (Mbeumo shares the MUN v MCI derby), and kicking off
Saturday 19:00 before the Sunday 15:30 derby. The vice fires only on a Haaland
non-start (p_start 0.93).

## Bench order

| Slot | Player | Pos | GW4 fixture | GW4 EP | Gap to slot above |
|---:|---|---|---|---:|---:|
| 12 | Dubravka | GKP | EVE (H) | 0.152 | — (backup GK, fixed slot) |
| 13 | Anderson | MID | MUN (A) | 3.853 | — |
| 14 | Thiaw | DEF | LEE (A) | 3.209 | 0.64 |
| 15 | Shaw | DEF | MCI (H) | 1.459 | 1.75 |

C8 (near-tie ≤ 0.25 → DefCon floor share) does not bite: gaps are 0.64 and
1.75, so EP order stands. Anderson also holds the highest DefCon share (0.26),
so the tie-break would not have reordered anything. Shaw at 75% sits 15th; a
non-start costs nothing unless two XI outfielders also miss.

## Transfers

**None.** The free transfer is banked → 2 free transfers at the GW5 deadline
(1 + 1 accrued, ≤ 5 cap). Hit cost 0. Bank unchanged at £0.0m.

Gate arithmetic: the best single swap is Anderson → Stach at +1.38 blend /
−2.85 prior-only, below the 2.0 threshold on the blend and sign-flipped on the
prior rates; the best pair is Anderson + Thiago → Cherki + Wissa at +5.06 /
+3.46 gross, below the 6.0 threshold that a −4 hit requires. Every other pair
above +4 gross flips sign on prior-only, which C14 forbids. Banking buys that
same pair free at GW5 — an earmark, not a commitment (see F2).

## Chips — none played (`chip: null`)

The GW4 Triple Captain gate fails under C5: Haaland's row is MUN (A) with
λ_att 1.80, City's third-worst attacking fixture in the window, and his 6.00
is below his 6.32 window mean. Nothing else in the squad is within 0.95 of him.

Forward earmarks (provisional, mirrored in `chip_plan`; windows read from the
bootstrap `chips` array — wildcard and freehit GW2–19, bboost and 3xc GW1–19):

| Chip | Earmark | Basis |
|---|---|---|
| wildcard | GW8 | EVE cliff from GW7, promoted-club defensive rows expiring, GK2 and DEF5 dead weight |
| 3xc | GW9 | MCI v BHA (H), Haaland 6.75, band-free; moved from GW5 (6.54). GW7 IPS (H) 6.81 is higher but banded, rejected under C5 |
| freehit | GW16 | placeholder — no blank or double inside GW4–9 |
| bboost | GW19 | last set-1 GW; needs GK2 and DEF5 repaired first |

One chip per GW ✓ (wildcard GW8 and 3xc GW9 are distinct) · freehit
non-consecutive ✓ · all earmarks inside their bootstrap windows ✓. This table
is a forecast; `chip: null` is what activates nothing this gameweek, and
`chip_plan` is the only machine-readable version of the plan above.

## Accepted risks

Every review finding left unresolved. No HIGH findings; no revision loop ran.

| # | Sev | Risk | Why it is accepted |
|---|---|---|---|
| F1 | MED | XI slot 11 — Barry 3.874 v Anderson 3.853 is a 0.02 blend edge broken toward Barry by suggestion S1. Prior-only reverses it by 0.81 (3.44 v 4.25), and the prior-only optimum XI (3-5-2 with Anderson) scores 53.46 v 52.66. | Inside model noise on the reading that drives selection, and user-steered via an open standing suggestion. Cost ≈ 0 on blend, ≈ −0.8 on prior-only. |
| F2 | MED | The GW5 payoff for banking — Anderson + Thiago → Cherki + Wissa, free — needs £14.0 from a £14.2 sale. Wissa is rising (+457k net in), Thiago falling (−230k net out); one more price move each makes it 14.1 v 14.1, two makes it infeasible. | No hedge exists: Thiago → Wissa alone flips sign (−0.68 / +2.03) and Cherki is unaffordable from Anderson alone. The GW5 optimizer re-derives on live prices and must not treat the pair as committed. |
| F3 | MED | Template exposure unheld — João Pedro 73.2%, Calafiori 48.7%, B.Fernandes 44.0%, Szoboszlai 38.4%, Rogers 32.1%. (The proposal's 48.6% for B.Fernandes is wrong; Szoboszlai and Rogers were omitted. Figures here are the corrected ones.) | Every route in is below the 2.0 transfer gate on both readings — João Pedro is the largest at +1.27 blend / +0.43 prior-only. Priced rank-variance risk, not a points risk. |
| F4 | MED | Two dead bench slots: Dubravka p_start 0.04 (0 minutes, Kinsky starts) and Shaw 0.62 (75%, flagged 11 Sep). A 4% Raya non-start leaks ≈ 3.7 EP uncovered. | Repair needs ≈ +0.5 of headroom the bank does not have. Carried explicitly into the GW5 earmarks below and into the GW8 wildcard. |
| F5 | MED | MCI concentration on the derby — Haaland (C, doubled) + Ndiaye in the XI + Anderson on the bench, all at MUN (A), λ_att 1.80, P(CS) 0.25. MCI carries 16.0 of the 55.2 predicted (29%). | Ndiaye's DefCon term (4.13 of his EP6) is a floor independent of the scoreline; Haaland at 71.2% owned is rank-safe; Mbeumo (MUN) is an internal hedge. At the 3-player cap, so no rule is strained. |

LOW findings F6–F12 are recorded in the review and need no carry: the
captaincy is robust on both readings (F6), the 3xc move to GW9 is re-tested
each cycle (F7, F8), price bleed matters only through F2 (F9), the flags gate
above closes F10, the team-value basis is settled in §Squad (F11), and no
fixture risk sits outside the window (F12).

## GW5 earmarks — re-derived next cycle, not commitments

- Two free transfers available. Today's only candidate clearing 2.0 on both
  readings is Anderson + Thiago → Cherki + Wissa (+5.06 / +3.46, free, bank
  0.2 after) — price-fragile per F2.
- **GK2 (F4):** a playing £4.0–4.5 keeper (Kinsky, Leno, Petrović, Verbruggen,
  Scherpen, Rushworth all start, EP6 17–19) needs ≈ +0.5 of headroom; pair it
  with the above only if the bank allows, otherwise it is a wildcard item.
- Re-test the 3xc GW9 earmark against GW5 SUN (H) before the GW5 deadline;
  revert only if the 0.21 edge closes.

## Rationale summary

Nothing moves this week because nothing clears the gate. The swap pass
enumerated every same-position single and every pair against the top-40 EP6 of
each position on two EP readings, and the pattern C14 was written for held
throughout: every blended gain above +1 (Stach, Le Fée, Schade, De Cuyper)
turns negative on prior-only rates, and every prior-only gain above +2 turns
negative on the blend. No move clears 2.0 on both, and no pair clears the 6.0
a −4 hit demands. Banking converts a sub-threshold single into a free
two-transfer at GW5 that clears the gate on both readings.

The squad itself is unchanged from GW3 and the XI is the same 3-4-3. Haaland
captains on a poor fixture because the alternatives are worse by 0.95 — the
derby is the reason the Triple Captain waits for GW9, not a reason to move the
armband. The two genuine weaknesses are structural rather than selection
errors: a non-playing GK2 and a 75% fifth defender, both needing money the
bank does not hold, both routed to the GW5 headroom or the GW8 wildcard.
Suggestion S1 is honoured in the only way the transfer rule permits — by
banking toward the Anderson exit rather than taking a sub-threshold move now —
and it also broke the 0.02 Barry/Anderson XI tie, the one place a steer
touched the team sheet.

## Suggestions

Read data/suggestions.md through S2

| S# | GW | Status | Reason |
|---|---|---|---|
| S1 | 4 | standing | EP6 +0.00 this GW (FT banked either way); Anderson is the target: best single Anderson→Stach +1.38 blend / −2.85 prior fails the 2.0 gate on both readings, so honoured by banking to 2 FTs for a GW5 upgrade (Anderson+Thiago→Cherki+Wissa +5.06 / +3.46 clears free); broke the 0.02 Barry v Anderson XI tie toward Barry; the Ndiaye half is unsupported — 266 of 270 minutes, EP6 25.40 third of five MIDs, best Ndiaye swap −0.07 |
| S2 | 4 | rejected | unreachable: unconstrained model ceiling 62.8 EP per GW (376.98 over GW4–9 incl. captain, no budget or club cap); this plan 55.2 GW4, 56.4 per GW mean; a reachable restatement (share of ceiling, or rank-relative) can be re-appended under a new S# |

## STATE

```yaml
# Convention (as GW2/GW3): free_transfers_banked = free transfers available at
# the NEXT (GW5) deadline. This GW's FT is banked (1 + 1 accrued = 2).
# team_value = authenticated my-team selling prices Σ 99.4 + bank 0.0
# (read 2026-09-11 ~18:10Z, fifteen rows summed). my-team's own "value 99.6"
# is the bootstrap now_cost sum, a different field with a different meaning —
# reconciled in the Squad section, sell basis kept as in GW2/GW3. Supersedes
# GW3's paper 99.9. No transfer, so this decision changes neither value.
gw: 4
team_id: 8455344
team_value: 99.4
bank: 0.0
free_transfers_banked: 2
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
