# Research: Scott (id 69, BOU MID) — GW6

Researched 2026-10-09 for the GW6 deadline (2026-10-10 10:00 UTC). Question from the user: is this a long-term injury, so that selling him to free funds is justified?

## Verdict

**Long-term (6+ GWs). Confidence: medium-high.**

- Expected return: early December 2026, i.e. **GW13–GW14 at the earliest** (GW13 deadline 2 Dec, GW14 deadline 5 Dec). A realistic first start is GW14–GW15.
- Expected to miss **GW6–GW12 at least** (7 GWs), which covers the whole 6-GW EP horizon from GW6.
- Why not "high" confidence: no Bournemouth club statement with a timeframe was found, the FPL feed says "Unknown return date", and outlets disagree on the exact injury (quadriceps vs tendon). Every source agrees on a multi-week absence; none suggests a short one.

## FPL data (data/raw/gw6/bootstrap.json, fetched 2026-10-09 13:31 UTC)

| Field | Value |
|---|---|
| status | `i` (injured) |
| chance_of_playing_next_round | 0 |
| chance_of_playing_this_round | null |
| news | "Thigh injury - Unknown return date" |
| news_added | 2026-10-05T09:30:09Z |
| now_cost | £6.1m (cost_change_start +0.1) |
| season | 446 min, 5 starts, 30 pts, form 3.0 |

Minutes by round (`fpl players --minutes`, summary-69.json): GW1 90, GW2 86, GW3 90, GW4 90, GW5 90. He was a nailed 90-minute starter until the injury, which happened on England duty after GW5, not in a Bournemouth match.

## Outside sources

### Official statements
- **England / FA** (reported 5 Oct 2026): confirmed Scott's withdrawal from the England squad with a thigh injury. No timeframe given in the official confirmation as reported.
- **Bournemouth**: no official club statement with a diagnosis or return date was found as of 2026-10-09.
- **Thomas Tuchel** (England head coach, press comments reported by Express & Star / Irish News, ~6 Oct 2026): said England took "zero risk" with Scott's fitness. This comments on how it happened, not on the prognosis.

### Media reports (not official)
- **The Athletic** (cited by Sports Mole, 5 Oct 2026): quadriceps injury; fears he could be out for **up to two months**.
- **Sky Sports** (5 Oct 2026): tendon injury; "initial indications suggest he could be missing for several weeks"; further scans planned at Bournemouth.
- **Flashscore** (~5 Oct 2026): out for **six to eight weeks**.
- **Sports Mole** (5 Oct 2026): expects a return in **early December**; could miss 13–14 Bournemouth matches across three competitions; fitness for the 2 Dec game unclear.
- **Yorkshire Evening Post** (Oct 2026): "two-month absence"; out of Leeds v Bournemouth (31 Oct, GW9).
- Also reporting a similar timeframe: Football Faithful, CaughtOffside ("serious thigh problem"), Khel Now, Fanatik.

Links:
- https://www.sportsmole.co.uk/football/england/injury-news/news/bournemouth-and-england-games-scott-will-miss-as-midfield-star-suffers-serious-injury_606250.html
- https://www.skysports.com/share/13595264
- https://www.flashscore.com/news/soccer-uefa-nations-league-scott-pulls-out-of-england-squad-with-injury-and-could-miss-two-months/Aa7XbhuP/
- https://www.irishnews.com/sport/soccer/alex-scott-withdraws-from-england-squad-and-faces-up-to-two-months-out-3JPAGFIXBZIU7ICE5P42XTNQQI/
- https://www.expressandstar.com/uk-sports/england-took-zero-risk-with-alex-scotts-fitness-says-thomas-tuchel-9267633
- https://yorkshireeveningpost.co.uk/sport/football/leeds-united/leeds-united-bournemouth-alex-scott-injury-news-latest-9266737
- https://thefootballfaithful.com/alex-scott-facing-two-months-out-with-thigh-injury/

## Price

| Item | Value | Source |
|---|---|---|
| Purchase price | £6.0m (bought GW1; summary-69.json value 60 at GW1) | data/decisions/gw1/final.md, gw5/final.md |
| Current price | £6.1m | bootstrap now_cost 61 |
| Selling price | **£6.0m** (derived) | FPL rule: purchase + half the rise, rounded down → 6.0 + floor(0.1/2) = 6.0. Matches the GW4/GW5 final.md `Sell` column. |

The selling price is derived, not read from `my-team` (no authenticated call made). The executor takes the binding figure from `my-team` at POST time. A price drop is likely given the injury: once now_cost falls to £5.9m, the selling price falls to £5.9m too.

## Open uncertainties
- No Bournemouth medical update yet; scans were pending as of 5 Oct. A club update at the pre-GW6 press conference could shorten or lengthen the estimate.
- Injury type differs by outlet (quadriceps vs tendon); a tendon injury would tend to mean the longer end of the range.
