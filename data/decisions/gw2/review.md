# GW2 Red-Team Review — squad-proposal.md

Reviewed adversarially against `data/analysis/gw2/*`, `data/raw/gw2/`
(bootstrap, fixtures, players-slim.csv), `data/retro/gw1.md` (C1–C8) and
`data/decisions/gw1/final.md`. Every number below was recomputed from raw or
analyst files, not taken from the proposal.

## Verdict: **APPROVE** — zero HIGH findings

MED findings carry conditions the finalizer must write into final.md (noted
per finding). One revision loop is not warranted: the transfer, XI, captain,
bench order and chip plan all survive independent attack.

## Independent re-checks — all pass

| Check | Result |
|---|---|
| Budget | Enzo sells 7.0 (unchanged price, per paper convention) + bank 0.0 ≥ Tavernier 6.0 buy. Bank after = 1.0 ✓. Post-transfer sell value Σ = 98.9 recomputed from the 15 listed prices ✓; STATE `team_value: 99.9` = 98.9 + 1.0 ✓ |
| Paper-pricing convention | Applied consistently: 14 players at purchase price, Anderson at current 6.4 (drop-bounded), Tavernier at buy 6.0. No player has risen, so the half-rise rule is untested this cycle ✓ |
| Positions / clubs | 2 GK, 5 DEF, 5 MID, 3 FWD ✓. Clubs: ARS 2, MCI 2, MUN 2, EVE 2, BOU 2, rest 1 — all ≤ 3 ✓. 15 unique ✓ |
| Formation | 3-5-2, 1 GK / 3 DEF / 5 MID / 2 FWD ✓. Auto-sub paths legal: a missing FWD routes to Tarkowski → 4-5-1 (≥1 FWD via Haaland) ✓ |
| STATE `picks:` (C6) | Present, 15 strict-format lines. All ids verified against bootstrap (Raya 1, Gabriel 4, Thiaw 445, Richards 202, Mbeumo 427, Tavernier 68, Anderson 481, Ndiaye 237, Scott 69, Haaland 411, Thiago 106, Dubravka 497, Tarkowski 229, Shaw 423, Kusi-Asare 272) ✓. Positions 1–11 XI, 12 backup GK, 13–15 bench order matching the bench table, exactly one captain and one vice, both in the XI ✓ |
| EP arithmetic | Realized-XI delta recomputed from `ep_gw` vectors: with Tavernier, per-GW slot max = 25.84; without = 22.68; delta +3.16 — exact ✓. Raw deltas in the swap table all reconcile to the JSONs (Szoboszlai +8.72, Gomez +5.55, Thomas-Asante +11.76, Barry +16.51, Mitchell +0.52, Phillips +0.13) ✓ |
| Predicted points | XI Σ = 46.34 + captain 5.32 = 51.66 recomputed ✓ |
| Analyst-value fidelity | Every p_start, uncertainty tag, GW2 EP and EP6 in the squad table matches the players-*.json rows ✓ |
| C7 tag binding | All XI p_start ≥ 0.86 with LOW tags — compliant (≥ 0.85 floor). Enzo 0.609 → HIGH ✓, Barry 0.72 → MED ✓, Thomas-Asante 0.70 → HIGH ✓ |
| C8 tie-breaks | Tarkowski-over-Shaw gap 0.009 (3.375 vs 3.366) → floor share 0.57 vs 0.16, correctly applied. Richards for the last XI slot leads on both raw EP and floor (1.08 ratio / 0.67 P(hit) per DEF analysis) ✓ |
| C4 | Tavernier meets no COV/HUL/IPS in GW2–7 (verified against fixtures.json: EVE NEW BRE LIV CHE SUN) — zero band exposure ✓. Shaw's ±-derived GW2 EP excluded from ranking ✓. COV forwards not bought ✓ |
| C5 / TC gate | FWD analysis confirms 63% of Haaland's 6.90 GW3 EP is the COV attacking term with band floor 6.18 < 6.67 (GW5). GW5 = MCI v SUN (H), verified in fixtures; SUN has a full PL prior and the league-worst 6-GW defensive ticker (17% mean P(CS)), worsened by GW1 — band-free. Deferral cost 0.23. Correctly moved ✓ |
| Chip path (set 1) | TC GW5, WC GW8, FH GW16, BB GW19 — all inside their bootstrap windows (wildcard/freehit 2–19, bboost/3xc 1–19), one per GW, FH non-consecutive trivially, no TC target sold, BB deferred while the bench is dead. Viable ✓ |
| Captaincy (spec mapping) | All five options LOW → discount 1.00. Haaland 5.32 leads Mbeumo 4.90 by 0.42. The only rival within 0.5 EP is *less* safe (p_start 0.86 vs 0.93, ± fixture), so no safer-alternative finding. Vice exposure ~0.02 EP correctly bounded ✓ |
| Concentration | No club contributes > 2 attack-dependent players (MCI: Haaland + Anderson; BOU: Tavernier + Scott; EVE splits attack/defence) ✓ |
| Hits | None taken; both rejected hits fail the gross ≥ 6 bar on honest bench-realization arithmetic, which I reproduce ✓ |
| Freshness | Snapshot 2026-08-28T09:45:31Z, deadline 17:30Z — well inside 24h. All 15 `status: a` in bootstrap (see F4 on Anderson) ✓ |

## Findings

### F1 — MED — Barry earmark: zero funding headroom against the market's strongest rise signal
The GW3 plan (Kusi-Asare 4.5 + bank 1.0 = Barry 5.5) has exactly £0.0m slack,
and bootstrap shows Barry with the heaviest buy pressure of any player checked:
transfers_in_event 122,618 vs out 18,560 (net +104k at 3.2% ownership, off an
8-point GW1). A £0.1 rise before the GW3 deadline strands the plan; the
proposal's "Why £1.0m is held" section never mentions rise risk (checklist 11).
Not HIGH because the GW2 decision is robust to every Barry price: the transfer
cannot be brought forward (bank is 0.0 until Enzo sells), Szoboszlai (frees
0.0) kills the plan outright, and Gomez (frees 2.0 of headroom) costs a
guaranteed −1.15 EP6 — more than the expected loss if Barry rises (fallbacks
at ≤5.5 exist: Thomas-Asante/Simms 5.0 as bench cover, a playing 4.5 GK for
Dubravka, or banking the FT). **Condition for final.md:** record the rise risk
and a named fallback so GW3 doesn't re-litigate; if the user applies decisions
manually, note that the earmark degrades, not the GW2 move.

### F2 — MED — Carried MED-3 template audit dropped: João Pedro and Calafiori fades not re-affirmed
Players owned > 30% and not held: João Pedro (CHE, 67.8% — up from 63.9),
B.Fernandes (48.4), Szoboszlai (43.2), Calafiori (41.6). The proposal
re-affirms the B.Fernandes and Szoboszlai fades with numbers, but is silent on
João Pedro — despite GW1 final.md scheduling exactly this revisit ("Revisit
when João Pedro's GW4 arrives"; CHE v HUL, his best window fixture at 5.41 EP,
now inside the horizon while the GW3 FT is already earmarked for Barry) — and
silent on Calafiori. Selling Enzo also zeroes CHE exposure while CHE rates
2nd on the 6-GW attack ticker. The numbers still defend both fades — Thiago
(EP6 26.64, rank 3) is held above João Pedro (26.36, rank 4), and Calafiori
(24.56) clears Thiaw/Richards (24.15/24.14) by less than a transfer is worth
while adding a third correlated ARS asset — so this is a process defect, not a
selection error. **Condition for final.md:** state both fades explicitly with
these numbers, per checklist 5 (differential risk must be deliberate and on the
record each cycle).

### F3 — LOW — Prose arithmetic slip: "sell value £98.9m … pre-transfer"
Pre-transfer sell value is £99.9m (GW1 Σ100.0 − 0.1 Anderson; the pre-transfer
squad still holds Enzo at 7.0). £98.9m is the *post*-transfer figure, which the
squad table and STATE use correctly (98.9 + 1.0 = 99.9). No downstream number
is wrong. Fix the sentence when carrying it into final.md.

### F4 — LOW — "All 15 status: a, no news" overstates cleanliness on Anderson
Anderson carries `chance_of_playing_next_round: 100` (not null) with
`news_added: 2026-08-23` — a since-cleared flag, consistent with his 62′ GW1.
The MID analyst has priced the substance (dc90 13.60 → 13.10, P(hit) 0.73 →
0.69, p_start 0.93). Action: the freshness-gate baseline must record 100, so a
re-downgrade (e.g. 100 → 75) diffs as a REOPEN delta rather than reading as
"still flagged, no change".

### F5 — LOW — Price drift on holds (notional under paper pricing)
Anderson (net −134k event flow, already −0.1 this event) and Dubravka (net
−25k, GW1 LOW-3 carryover) risk further −0.1 steps; each costs 0.1 of sell
value under the drop-bounded convention. Mbeumo shows net −117k (post-loss MUN
exodus) — his EP case is intact, no action, but check at GW3. Tavernier (net
+57k) is being bought ahead of his rise — timing favorable. Enzo is sold at
7.0 ahead of heavy outflow (net −60k) — also favorable.

### F6 — LOW — Recency-pattern watch for the GW4 retro
This cycle's buy (Tavernier, 10 pts GW1) and next cycle's earmark (Barry,
8 pts GW1) are both GW1 top-scorers. Each has model support independent of the
haul (set-piece portfolio + EP6 rank 7 on 90′; won the shirt vs Beto 11′), and
the sale is process-driven (p_start 0.61 HIGH), so no bias verdict now — but
the GW4 retro should test whether incoming transfers systematically chase
last-GW points.

### F7 — LOW — Dead bench persists (accepted as MED-B; concur with the pricing)
Kusi-Asare 0.05 and Dubravka 0.12 cover nothing in GW2, but three simultaneous
XI absences are needed before a dead slot is reached (Tarkowski 0.92 and Shaw
0.90 are genuine cover), the expected auto-sub loss ≈ 0.3 pts is priced, and
the GW3 repair is planned. No cheaper fix exists this week (verified: the
Kusi-Asare hit fails the gross ≥ 6 bar; Dubravka swaps gain ≤ 0.13).

## Checklist coverage

| # | Item | Outcome |
|---|---|---|
| 1 | Minutes risk | Pass — XI min p_start 0.86; dead bench = F7 |
| 2 | Flags missed/stale | F4 (baseline nuance only); no live flag on any of the 15; flagged non-squad players (Gyökeres, Watkins, Martinez, Georginio, Bruno G., Caicedo) touch no selection |
| 3 | Constraints recomputed | Pass (table above) |
| 4 | Concentration | Pass |
| 5 | Template exposure | F2 (MED) |
| 6 | Fixture myopia | Pass — EVE cliff GW7 and LIV/BRE turns are named and the WC GW8 earmark addresses the decay; FT flow (1/GW from GW4) covers the LOW-2 exit window |
| 7 | Hit justification | Pass — no hits; rejections verified |
| 8 | Captaincy | Pass — chosen pick is both highest discounted EP and safest; rival within 0.5 is riskier |
| 9 | Recency bias | F6 (LOW watch item) |
| 10 | Chip path | Pass; BB-at-expiry zero slack already an accepted LOW |
| 11 | Price risk | F1 (MED), F5 (LOW) |

## For final.md

- Write F1's fallback line and F2's two fade re-affirmations into final.md
  (accepted-risk or rationale section) — both are documentation conditions,
  not selection changes.
- Correct the F3 sentence if the pricing paragraph is carried over.
- Freshness gate: re-run flags on all 15 ids with Anderson's baseline
  chance = 100 (F4); any status/chance/news delta = REOPEN per CLAUDE.md.
