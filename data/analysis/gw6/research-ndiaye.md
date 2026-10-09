# Research: Ndiaye (id 237, MCI MID) — is he starting? (GW6)

Written 2026-10-09 for the GW6 cycle (deadline 2026-10-10 10:00 UTC). Raw snapshot
fetched 2026-10-09 13:31:49 UTC (`data/raw/gw6/meta.md`).

## Verdict

**Likely starter, not rotation.** The data does not support "not starting over his
teammates": 4 starts in 5 rounds, 385 of 450 minutes. The one non-start (GW4) was a
45-minute half-time appearance. City's midfield is thinner for GW6, not thicker.
His weakness is low attacking output, not minutes.

## Availability (bootstrap, `data/raw/gw6/bootstrap.json`)

- status `a`, chance_of_playing_next_round `null`, news empty.
- now_cost 5.8 (cost_change_event −1, cost_change_start −2).
- GW6 fixture: LIV (A) (`data/analysis/gw5/players-MID.json`, fixtures list, slot 2).

## Minutes and starts per round, City MIDs/FWD

Source: `fpl players --gw 6 --team MCI --position MID|FWD --minutes` and the `starts`
field in `data/raw/gw6/players/summary-{id}.json`.

| id | Player | Status (bootstrap) | Minutes R1–R5 | Starts |
|---|---|---|---|---|
| 397 | Semenyo | `d` 75%, "Ankle injury" (added 24 Sep) | 90,90,90,90,90 | 5 |
| 481 | Anderson | `a` | 62,81,90,90,90 | 5 |
| **237** | **Ndiaye** | **`a`** | **90,90,86,45,74** | **4 (R4 sub)** |
| 399 | Cherki | `a` | 27,81,65,45,84 | 4 |
| 155 | Enzo | `a` | 25,0,75,81,90 | 3 |
| 398 | Foden | `s` 0%, "Suspended until 17 Oct" | 81,90,24,22,0 | 3 |
| 400 | Doku | `a` 100% | 0,0,0,0,15 | 0 |
| 406 | Kovačić | `a` | 27,15,0,0,0 | 0 |
| 411 | Haaland (FWD) | `a` | 90×5 | 5 |

Reading:
- Foden misses GW6 (suspended to 17 Oct). Semenyo is a 75% doubt. Both reduce
  competition for Ndiaye's minutes this week.
- Doku is the only returning rival: back from a calf injury, 15 minutes off the bench in GW5.
  He is a threat over the six-gameweek window, not for GW6.
- Enzo has started 3 in a row (R3–R5), which is the one trend against Ndiaye.
- The GW4 retro (`data/retro/gw4.md` line 37) says Ndiaye "started… withdrawn at 45'".
  `summary-237.json` records R4 `starts: 0`, 45 minutes, which means he came on as a
  half-time substitute. The GW5 analyst note agrees ("came off bench 45' GW4"). The retro line is wrong.

## Recent output (`data/raw/gw6/players/summary-237.json`)

| Round | Min | Pts | G | A | xG | xA | DefCon | Bonus | BPS |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 90 | 9 | 0 | 1 | 0.24 | 0.32 | 12 | 1 | 36 |
| 2 | 90 | 4 | 0 | 0 | 0.02 | 0.07 | 13 | 0 | 16 |
| 3 | 86 | 3 | 0 | 0 | 0.02 | 0.04 | 5 | 0 | 12 |
| 4 | 45 | 1 | 0 | 0 | 0.00 | 0.01 | 10 | 0 | 15 |
| 5 | 74 | 5 | 0 | 1 | 0.10 | 0.14 | 4 | 0 | 31 |

Season (bootstrap): 22 pts, xG 0.38, xA 0.58, DefCon 44, form 3.0. Rounds 1 and 2 were
his only DefCon hits at MID's threshold of 12. Rounds 2–4 combined produced xG + xA 0.16.

## Prior model view (GW5)

- `data/analysis/gw5/players-MID.json`: p_start 0.78 flat ×6 (cut from 0.93 under C18),
  EP6 21.17, ep_gw[GW6] 3.34, uncertainty MED.
- `data/decisions/gw5/review.md` M1 argued the flat 0.78 was too low early in the
  window (Foden ban) and proposed `[0.90, 0.88, 0.82, 0.78, 0.78, 0.78]`.
- `data/decisions/gw5/final.md` planned to sell Ndiaye for E.Le Fée (+4.105 EP6 blend), and
  said "What sells Ndiaye is Le Fée, not Ndiaye's minutes." The transfer was never
  POSTed (session expired).
- `data/retro/gw5.md`: Ndiaye predicted 3.66, scored 5 in 74 minutes; Le Fée also 5.
  The unmade Ndiaye → Le Fée move is recorded as still open.

## Web search (2026-10-09; unconfirmed, not official team news)

- Reports say City signed him from Everton in early September 2026 on a five-year deal,
  and describe him as able to play either wing or centrally
  ([Free Press Journal](https://www.freepressjournal.in/sports/manchester-city-sign-senegal-international-iliman-ndiaye-from-everton-on-five-year-deal-ahead-of-2026-27-premier-league-season-video),
  [Times of Oman](https://timesofoman.com/article/176350-manchester-city-sign-senegal-winger-iliman-ndiaye-on-five-year-deal)).
- No October 2026 press-conference quote, injury report or Liverpool–City predicted XI
  mentioning him was found. Search results were older fixtures or sources that contradict each other.

## Selling price

Bought at 6.0 in GW1 (`data/decisions/gw1/final.md` line 36), now 5.8. When the price
has fallen below the purchase price, the selling price equals now_cost, so the **selling price is
£5.8m**. This is the same rule `data/decisions/gw5/review.md` applied at 5.9. Confirm
with `my-team` before any POST.
