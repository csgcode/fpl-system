# Research: Anderson (id 481, MCI MID) — sell case, GW6

Prepared 2026-10-09 for the GW6 cycle (deadline 2026-10-10 10:00 UTC). Research only;
no decision. Sources are abbreviated:

- **SUM** = data/raw/gw6/players/summary-481.json (or summary-{id}.json for others)
- **BS** = data/raw/gw6/bootstrap.json (fetched 2026-10-09 13:31 UTC, per data/raw/gw6/meta.md)
- **CLI** = `uv run python -m fpl players --gw 6 --position MID --min-price 5.5 --max-price 8.5 --sort points --minutes`
- **EP5** = data/analysis/gw5/players-MID.json (horizon GW5–10)
- **F4 / F5** = data/decisions/gw4/final.md, data/decisions/gw5/final.md
- **PICKS** = data/raw/gw6/picks-8455344-e5.json

## Verdict

**Low-ceiling floor player, not a broken asset — but the floor is thin and the price is
wrong.** He nails 90 minutes and racks up defensive actions, yet he has converted that into
DefCon points only twice in five games, has zero bonus, and almost no attacking output.
At £6.3m he returns the lowest points per £m of any regular-starting MID in the
£5.5–8.5m band. The user's read is right on ceiling; the model's earlier "floor" defence
over-weighted DefCon volume that is not turning into points.

## Season so far (GW1–5)

| GW | Opp | Min | Pts | xG | xA | DefCon actions | DefCon pts (≥12) | Bonus | BPS | Other |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | BOU (H) | 62 | 2 | 0.00 | 0.25 | 6 | 0 | 0 | 14 | — |
| 2 | CRY (A) | 81 | 3 | 0.07 | 0.22 | 14 | 2 | 0 | 25 | yellow −1 |
| 3 | COV (H) | 90 | 3 | 0.02 | 0.17 | 11 | 0 | 0 | 23 | clean sheet +1 |
| 4 | MUN (A) | 90 | 5 | 0.00 | 0.01 | 14 | 2 | 0 | 18 | clean sheet +1 |
| 5 | SUN (H) | 90 | 2 | 0.02 | 0.02 | 9 | 0 | 0 | 15 | — |
| **Total** | | **413** | **15** | **0.11** | **0.67** | **54** | **4** | **0** | **95** | 0 G, 0 A |

Source: SUM `history`; totals match BS (`total_points` 15, `minutes` 413,
`expected_goals` 0.11, `expected_assists` 0.67, `defensive_contribution` 54,
`defensive_contribution_per_90` 11.77, `bonus` 0, `bps` 95). Points breakdown derived from
SUM row fields (appearance 2, `defensive_contribution` ≥ 12 → +2, `clean_sheets` → +1,
`yellow_cards` → −1).

Observations:
- **Points ceiling so far: 5.** Never more than one scoring event beyond appearance.
- **DefCon conversion 2 of 5.** His per-90 rate (11.77) sits just *under* the MID threshold
  of 12, so he hovers on the line (11 in GW3, 9 in GW5). Last season's rate was higher
  (EP5 `dc90_prior` 13.25, from 515 actions in 3,332 min, SUM `history_past` 2025/26).
- **Attacking output collapsed in GW4–5**: xG+xA 0.01 and 0.04 (SUM). GW1–3 xA 0.17–0.25
  per game came while minutes were building.
- **Bonus 0 from 95 BPS.** Consistent with the 2026/27 BPS change (CBI→BPS rate cut from
  1/2 to 1/3): his BPS is mostly defensive and no longer reaches bonus. The GW5 EP model
  still gave him a bonus term of 1.47 over 6 GWs (EP5 `terms.bonus`, `bonus_per_start`
  0.273), which looks too high on current evidence.
- Minutes are secure: 62, 81, 90, 90, 90 (CLI), 5/5 starts.

## Price and value

- Price £6.3m (BS `now_cost` 63); bought at £6.5m (F5 squad table row 8: buy 6.5,
  now 6.3), so selling price is **£6.3m**. Bank £0.0m (PICKS `entry_history.bank` 0).
  An upgrade to £8.3m therefore needs £2.0m raised elsewhere in the same window.
- Ownership 3.9% (BS), falling every GW (SUM `transfers_balance` negative GW2–5).
- Points per £m: **2.38** (15 / 6.3, BS).

## Comparison with MIDs £5.5–8.5m

All from BS (pts, min, xG, xA, DefCon, bonus, status) and CLI (minutes); pts/£m = pts ÷ price.
DefCon-point rounds = rounds with ≥ 12 actions, from each SUM `history`. EP6 = EP5 `ep_total6`.

| Player | Club | £m | Pts | Pts/£m | xG | xA | DefCon (per 90) | DefCon-pt rounds | Bonus | EP6 (GW5) | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Anderson** | MCI | 6.3 | 15 | **2.38** | 0.11 | 0.67 | 54 (11.77) | 2/5 | 0 | 23.35 | a |
| Groß | BHA | 5.9 | 47 | 7.97 | 1.77 | 0.86 | 26 (5.2) | 0/5 | 9 | 25.20 | a |
| Schade | BRE | 6.2 | 39 | 6.29 | 1.52 | 0.32 | 34 (6.85) | 0/5 | 6 | 26.30 | a |
| Tavernier (owned) | BOU | 6.1 | 31 | 5.08 | 1.70 | 0.92 | 42 (8.92) | 0/5 | 8 | 29.32 | a |
| Stach | LEE | 6.0 | 27 | 4.50 | 0.97 | 0.31 | 61 (12.28) | 3/5 | 3 | 25.18 | a |
| Barnes | NEW | 6.1 | 28 | 4.59 | 0.62 | 0.48 | 33 (6.6) | 0/5 | 3 | 24.24 | a |
| King | FUL | 5.6 | 24 | 4.29 | 1.54 | 0.46 | 28 (5.93) | 0/5 | 3 | 22.67 | a |
| Xhaka | SUN | 5.5 | 21 | 3.82 | 0.06 | 1.32 | 54 (10.8) | 2/5 | 5 | 22.71 | a |
| Ndiaye (owned) | MCI | 5.8 | 22 | 3.79 | 0.38 | 0.58 | 44 (10.29) | 2/5 | 1 | 21.17 | a |
| Ødegaard | ARS | 6.8 | 29 | 4.26 | 1.08 | 1.32 | 23 (5.49) | 0/5 | 6 | 25.34 | a |
| Rogers | CHE | 7.8 | 29 | 3.72 | 1.72 | 1.23 | 31 (6.38) | 0/5 | 2 | 23.84 | a |
| Cherki | MCI | 7.8 | 34 | 4.36 | 0.72 | 1.54 | 12 (3.58) | — | 5 | 26.45 | a (mins 27,81,65,45,84) |
| Gibbs-White | NFO | 8.0 | 28 | 3.50 | 1.56 | 1.42 | 21 (4.2) | — | 6 | 29.21 | a |
| Semenyo | MCI | 8.4 | 33 | 3.93 | 0.33 | 1.16 | 22 (4.4) | — | 2 | — | d 75% ankle (over budget) |
| Scott (owned) | BOU | 6.1 | 30 | 4.92 | 0.64 | 0.42 | 60 (12.11) | — | 5 | 24.95 | **i — thigh, unknown return** |

Takeaways:
- Every regular starter in the band beats his pts/£m; the next lowest is Gibbs-White at 3.50.
- **As a DefCon pick he is outperformed by cheaper players**: Stach (£6.0m, 3/5 DefCon
  rounds, 27 pts) and Xhaka (£5.5m, same 54 actions, 21 pts) give the same floor for less.
- Under the BPS change, DefCon-heavy MIDs earn little bonus (Anderson 0, Stach 3, Ndiaye 1)
  while attacking MIDs collect it (Groß 9, Tavernier 8, Schade 6, Ødegaard 6).
- EP6 at GW5 ranked him 18th of all MIDs (EP5), behind cheaper Groß, Schade, Stach,
  E.Le Fée (27.02, £5.8m) and Barnes.

## Model and optimizer reasoning that kept him

- **GW4 (F4 `## Suggestions`, S1 standing)**: best single exit Anderson → Stach +1.38 blend
  / −2.85 prior-only; failed the 2.0 transfer gate and flipped sign on prior-only rates.
  The optimizer banked the FT to target Anderson + Thiago → Cherki + Wissa at GW5
  (+5.06 / +3.46).
- **GW5 (F5 `## Suggestions`, S1 standing)**: Anderson exits declined on the merits — best
  single Anderson → E.Le Fée +3.665 / −1.325 and → Schade +2.942 / −1.107, both sign-flip
  under C14. Kept in the XI over E.Le Fée by the C20 tie-break on DefCon share (0.281).
  Revisit set for the GW8 wildcard.
- **Why prior-only kept saving him**: the prior rates come from his 2025/26 Forest season
  (180 pts, 515 DefCon actions, 16 bonus; SUM `history_past`), weighted 0.65
  (EP5 `rates.prior_weight`). That season does not reflect his current City role (fewer
  DefCon points, no bonus, no attacking returns). The prior-only reading is the one
  propping him up.
- **The GW5 plan was never applied** (F5 correction note; commit b965a64), so the GW4 squad
  carried into GW6 and S1 must be re-read as fully open (both halves).
- GW5 outcome: on the bench, scored 2 against an EP of 4.00 (data/retro/gw5.md line 28).

## Status, news and context

- BS: `status` a, `chance_of_playing_next_round` 100, `news` empty; `news_added`
  2026-08-23 is a stale entry from GW1.
- GW1 (23 Aug 2026): went off around the hour mark against Bournemouth holding his
  hamstring; Maresca called it cramp, not injury
  ([LiveScore](https://www.livescore.com/en/news/football/premier-league/early-crisis-for-man-city-enzo-maresca-provides-elliot-anderson-injury-update-after-dramatic-premier-league-comeback-victory-over-bournemouth-goal/),
  [BritBrief](https://britbrief.co.uk/sports/grassroots/maresca-anderson-cramp-not-injury-after-city-win.html)).
  He has played 90 minutes in all three games since (CLI).
- Role: signed from Nottingham Forest in July 2026 for a club-record fee
  ([ITV, 2 Jul 2026](https://www.itv.com/news/granada/2026-07-02/manchester-city-confirm-deal-to-sign-elliot-anderson));
  described as a box-to-box player, not a like-for-like Rodri replacement, and an important
  part of City's midfield this season
  ([Sports Mole preview](https://www.sportsmole.co.uk/football/man-city/title-race/feature/man-city-2026-27-premier-league-preview-prediction-fixtures-squad-depth-chart_603198.html)).
  That deeper role fits the data: high defensive actions, low xG/xA.
- Rotation risk is low on current evidence (5/5 starts). No October 2026 team news was found.
  Some web sources conflict on details (one names his previous club as Newcastle), so treat
  them as weak evidence.
- Fixtures GW6–11: LIV (A, FDR 4), IPS (H, 2), AVL (A, 3), BHA (H, 3), NFO (A, 3),
  FUL (H, 2) (SUM `fixtures`).

## Upgrade candidates (≤ £8.3m)

Club limit: MCI already has 3 players (Haaland, Ndiaye, Anderson per PICKS), so selling
Anderson frees one MCI slot. Note that Scott is injured, which may make a midfield move
more urgent anyway.

| Candidate | £m | Funding from £6.3m | Case | Concern |
|---|---|---|---|---|
| Groß (BHA) | 5.9 | frees £0.4m | 47 pts, 9 bonus, penalties (CLI `pen` 1), 90 min every game | GW8–9 LIV (A), MCI (A) |
| Schade (BRE) | 6.2 | frees £0.1m | 39 pts, xG 1.52, penalties (CLI `pen` 2), 90 min | GW7 LIV |
| Ødegaard (ARS) | 6.8 | needs £0.5m | xG+xA 2.40, 6 bonus, penalties (CLI `pen` 3) | subbed off 70–84 min each game |
| Rogers (CHE) | 7.8 | needs £1.5m | xG 1.72 + xA 1.23, 41.6% owned (template cover) | 2 bonus only |
| Gibbs-White (NFO) | 8.0 | needs £1.7m | GW5 EP6 29.21 (5th MID), xG+xA 2.98 | 3.50 pts/£m so far |

Like-for-like floor option if the user wants to keep a DefCon player: Stach (LEE, £6.0m,
3/5 DefCon rounds), though his GW6–7 run is ARS, MUN.

Cherki (MCI £7.8m) is excluded as a recommendation: minutes 27–84 (CLI) mean rotation risk.
Semenyo is over budget (£8.4m) and flagged d 75% ankle (BS).
