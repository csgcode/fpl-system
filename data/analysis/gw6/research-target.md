# GW6 research — can the squad reach 60 EP per GW? (scoping study)

Written 2026-10-09 for the GW6 cycle (deadline 2026-10-10 10:00 UTC). This is
a scoping study for the user's squad-overhaul request, not a decision. The
squad-optimizer decides in the GW6 cycle.

## Inputs and approximations

- **EP is a proxy.** GW6 EP files do not exist yet. All EP below comes from
  `data/analysis/gw5/players-{GKP,DEF,MID,FWD}.json` (GW5–10 horizon); GW6–8 =
  indices 1–3 of `ep_gw`. These were made before GW5 was played, so they miss
  GW5 results and any news since.
- **Availability overlay from the GW6 bootstrap.** Players with status i/s/u/n
  get EP × chance (0 when chance is null or 0) for all three GWs; status d
  scales GW6 only. Scott (69) is `i`, chance 0, "Thigh injury – Unknown return
  date" → EP 0 for GW6–8 (his raw proxy was 4.1/4.3/4.0).
- **Prices** are GW6 bootstrap `now_cost`. Selling prices were not available
  (expired session), so sell = now_cost. This is approximate. The current
  squad's now_cost sum is exactly £99.8m, equal to the recorded team value, so
  the error is likely small. Budget = £99.8m, bank 0.0.
- **Pool:** the 415 players in the GW5 EP files (the analyst shortlist), not
  every player. A per-position pruning keeps players unless 8 cheaper-or-equal
  players already have a higher 3-GW EP.
- **Score per GW** = best XI that GW (any legal formation, 1 GK, ≥3 DEF, ≥2
  MID, ≥1 FWD) + the captain's EP once more (the highest XI player). The bench
  scores nothing. Hits are −4 per transfer beyond 3, spread over the 3 GWs.
- **Search:** best-improvement hill climbing with 1- and 2-player swaps,
  several starting squads for the wildcard. A heuristic, not a proven optimum;
  the true maximum may be a few tenths higher.
- Constraints enforced: £99.8m, 2/5/5/3, max 3 per club.
- Scripts: scratchpad `opt.py`, `opt2.py`, `opt3.py` (not committed).

## 1. Current squad (no transfers)

GW6 54.9 · GW7 55.7 · GW8 53.9 → **54.9 per GW**. Scott's zero costs about
1 EP per GW: Anderson or Ndiaye must start in his place.

## 2. Paths compared (proxy EP per GW, GW6–8, captain included)

| Path | Transfers | GW6 | GW7 | GW8 | Gross avg | Hits | **Net avg** |
|---|---|---|---|---|---|---|---|
| Hold | 0 | 54.9 | 55.7 | 53.9 | 54.9 | 0 | **54.9** |
| (a) 3 FT, best | Scott, Ndiaye, Tarkowski → E.Le Fée 5.7, Schade 6.2, Guéhi 6.0 | 56.2 | 57.5 | 57.1 | 56.9 | 0 | **56.9** |
| (a′) 3 FT, user's sales | Scott, Ndiaye, Anderson → E.Le Fée, Schade, Groß | 57.0 | 57.1 | 56.2 | 56.8 | 0 | **56.8** |
| (b) 4 transfers | Raya, Scott, Ndiaye, Thiago → Tzolakis, E.Le Fée, Saka, Kostoulas | 58.5 | 57.9 | 56.2 | 57.6 | −4 | **56.2** |
| (b) 5 transfers | above + Tarkowski → Guéhi | 57.7 | 58.8 | 57.3 | 58.0 | −8 | **55.3** |
| (c) Wildcard GW6 | 10 changes (squad below) | 58.6 | 59.5 | 58.1 | 58.8 | 0 | **58.8** |
| Ceiling, no budget (club cap kept) | — | 60.6 | 60.3 | 61.0 | 60.7 | 0 | 60.7 (£114.1m) |

When the search may take a 4th or 5th transfer freely, it stops at 3: no hit
pays back over 3 GWs.

Wildcard squad (£99.8m): GK Tzolakis, Steele · DEF Gabriel, Guéhi, Thomas,
Van Hecke, Davis · MID Saka, Mbeumo, Gibbs-White, Tavernier, E.Le Fée · FWD
Haaland, Kostoulas, Barry. Kept from today: Gabriel, Mbeumo, Tavernier,
Haaland, Barry.

## 3. Is 60 per GW reachable?

**No, not on any budget-legal path.** The best legal squad (wildcard) is
about 58.8. Even with no budget at all the ceiling is 60.7, so 60 needs about
£14m the squad does not have. This matches GW4, when S2 (65+) was rejected
with a 62.8 ceiling.

Realistic target: **57 per GW with 3 free transfers, about 59 with a
wildcard.** Context for actual scores: the model's cumulative bias is +0.10 per
player (actual above predicted, retro gw5), roughly +1 point per GW across
XI + captain, so a ~59 EP squad can land at 60 in actual points in an average
week — but that is noise, not something the plan can aim at.

Ndiaye and Anderson are both sold or benched on every improving path; the
model agrees with S1 here. Selling Anderson rather than Tarkowski costs only
0.1–0.2 EP per GW.

## 4. Wildcard timing — GW6 or GW8?

Recommendation: **keep the wildcard at GW8; use the 3 free transfers now.**

| | Wildcard GW6 | 3 FT now, wildcard GW8 |
|---|---|---|
| EP GW6–7 | 58.6 + 59.5 | 56.2 + 57.5 |
| Difference | about +4.4 pts over GW6–7 | — |
| GW8 onward | must rebuild with FTs only until Set-1 FH/other chips | wildcard rebuild on GW8 data, 2 GWs more evidence |
| Banked FTs | CLAUDE.md: a wildcard does not wipe banked FTs, so the 3 survive (accrual during a WC week not confirmed) | 3 FTs spent now; 1 accrues for GW7 |

Trade-off: a GW6 wildcard buys about 4 proxy points over two weeks and keeps
the 3 FTs. Waiting keeps the wildcard for a better-informed rebuild: the proxy
is a week stale (GW5 results unseen, Scott injury already moved the numbers),
and the GW6–8 gap between paths (≈2 EP per GW) is inside the model's error
(MAE 1.51 per player). Also the 3-FT path already fixes the two weak spots
the user named (Scott, Ndiaye), and with Anderson as a variant at −0.1/GW.
If the GW6 EP files, once built, show a wildcard advantage well above
2 EP per GW, or an injury cluster appears, switch to the GW6 wildcard: the
banked FTs survive and the Set-1 window runs to GW19.

## Caveats

- Proxy EP from GW5 files; the GW6 player-analyst run will move numbers.
- Sell price = now_cost (no authenticated `my-team` read).
- Heuristic search over a pruned shortlist; not exhaustive.
- 3-GW horizon only. The optimizer scores on 6 GWs, which favours fixture-
  robust players and may rank these paths differently.
