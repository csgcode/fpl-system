# Price-adjusted gain: research and recommendation

Written 2026-11-20, before the GW11 deadline. Data: the GW1–GW11 bootstrap
snapshots, the GW2–GW11 transfer audit records under data/executor/, and the
GW11 players files. Everything below is from our own files except the FPL rule
text in §1, which is cited.

## Decision (2026-11-20)

An independent review of this document came first, then the user's ruling:
the player analysts must not use crowd trends (net transfers, ownership,
price moves) to judge a player. They judge on underlying data only.

**Built:**

- S7 is withdrawn (S9 in data/suggestions.md).
- S10, a money tie-break for the squad optimizer. Between two moves that both
  pass the transfer rule and are within 0.5 EP6 of each other, prefer the one
  that sells a player whose net transfers this gameweek are at or below −10%
  of his owners. It protects team value only. It is not a judgement of the
  player.
- A monitoring line in `fpl calibrate`. For each round it compares heavily
  sold players with every other player owned by at least 1%: the number of
  players, expected starts against actual starts, and mean points error. The
  groups come from the round's own pre-deadline bootstrap. The line changes
  no prediction.

**Not built, and why:**

| Item | Why not |
|---|---|
| A price term in the transfer gate (§9, the variant at the end of Part 1) | The money is a tenth of the gate at most, and it changed no decision in ten cycles (§3.4, §10.3) |
| The report-only `price watch:` line (Spec Part 1) | S10 covers the only use it had, a near-tie, without new code |
| The `heavy_selling_p_start_cut` `ModelConfig` field (Spec Part 2) | The backtest gate cannot judge it. A 14% cut in expected points lowers the points error (MAE) in every group, heavily sold or not, so any shrink would pass. Passing the gate would prove nothing |
| A net-selling input for the player analysts | It breaks the user's rule: analysts judge on underlying data, not crowd trends |

**What the review found about the gap in starts:**

- It sits in players with `p_start` between 0.3 and 0.9, and in flagged
  players (status `d` or `i`).
- Flagged, heavily sold players, GW2–10: status `d` started 0.393 of the
  time against 0.526 predicted; status `i` 0.104 against 0.203. This points
  at the player analyst's return ramps for flagged players, not at the
  crowd. It is logged in docs/backlog.md for the retro to test on underlying
  data (news, return dates, minutes).
- It has shrunk since GW6 to between 0 and 4 relevant players a week.

**When to look again:** in GW2–6 of next season, or after a gameweek with
mass selling. Judge it with a Brier test of starts on the heavily sold group
(predicted `p_start` against actual starts), not with points MAE. The
calibrate line collects the data for that test.

## Revised verdict (after the follow-up, §10)

**SUPPORTED, but not for the reason first proposed and not in the gate.**
Heavy net selling (≥ 10% of a player's owners in a gameweek) carries
information our EP model lacks: those players score about 0.4 points a round
below prediction for at least the next three rounds, almost all of it
because they start less often than `p_start` says. That is a case for
changing the minutes input (`p_start`), tested through the backtest gate. It
is not a case for a price term in the transfer gate: the money side stays
small even after raising V to about 0.3 (§10.3). The original analysis below
is kept unchanged; §10 holds the new evidence and the spec gains a second part.

## Verdict first (original, before the follow-up)

**The premise is WEAK. Recommendation: do not add a price term to the
transfer gate.** If anything is built, build the smallest version: a
report-only `price watch:` line in `objective` that names owned players likely
to fall, so the optimizer can use it as a near-tie breaker. It never changes a
gain or a gate.

Why, in one paragraph: our data *can* predict a fall before the next deadline,
but not from the signal the idea was built on. A player who has just fallen is
*less* likely than average to fall again. Heavy net selling that has not yet
caused a fall is the real signal (about 2 in 3 fall). But the money at stake
is tiny. A £0.1m fall is worth about 0.1 EP6 (points over the six-gameweek
horizon), so the expected value of selling a likely faller one week early is
about 0.06 EP6, roughly 3% of the 2.0 gate. Over GW2–GW11 the term would
not have changed a single transfer decision at any sensible value. The one
decision it changes at an inflated value (GW7) would have lost points and
saved no money.

## 1. How selling prices work

FPL's rule: when a player's price has risen since you bought him, you get
half the rise, rounded down to £0.1m. When it has fallen, you take the full
fall. The Premier League's own wording is "you only get £0.1m of profit for
every £0.2m that the player rises in cost". Prices change overnight (UK time),
by at most £0.1m a day, driven by net transfers.
([premierleague.com: FPL player price changes](https://www.premierleague.com/en/news/2858775);
[Fantasy Football Scout: how FPL price changes work](https://www.fantasyfootballscout.co.uk/2026/07/20/how-do-fpl-price-changes-work))

In tenths of £1m, with purchase price `p` and current price `now`:

```
selling price = now                      if now <= p
              = p + floor((now - p) / 2) if now >  p
```

Our 15 executed sales GW2–GW11 all match this formula exactly (audit
`selling_price` against purchase price and the bootstrap price that day).

### When a £0.1m fall costs us £0.1m, and when it costs nothing

| Profit before the fall (`now − p`) | Selling price before | After a £0.1m fall | Cost to us |
|---|---|---|---|
| 0 or less (at or below purchase) | `now` | `now − 1` | **£0.1m** |
| +1 | `p` | `p` | £0 |
| +2 | `p + 1` | `p` | **£0.1m** |
| +3 | `p + 1` | `p + 1` | £0 |
| +4 | `p + 2` | `p + 1` | **£0.1m** |

Rule: a fall costs £0.1m when the profit is zero, negative or even; it costs
nothing when the profit is odd (one of the two tenths was never ours).

In practice this barely matters for us: every one of the 15 falls on players
we held GW1–GW11 cost the full £0.1m. The players that fall are the ones we
hold at or below what we paid.

### Limits on change

The rule text promises at most £0.1m a day. What we actually saw between
consecutive pre-deadline snapshots (6,524 player-gameweek pairs):

| Change between snapshots | Count |
|---|---|
| −£0.2m | 1 |
| −£0.1m | 656 |
| 0 | 5,723 |
| +£0.1m | 131 |
| +£0.2m | 13 |

Even the three-week gap GW5→GW6 produced no fall bigger than £0.1m. So
"P(fall)" in this document means P(a £0.1m fall); a £0.2m fall is rare
enough to ignore.

## 2. Data coverage

| Item | What we have |
|---|---|
| Snapshots | 35 readable bootstrap files across GW1–GW11 (one GW5 archive file is unreadable, 49 bytes) |
| Useful snapshots | 11 — one per gameweek. The archived refreshes inside each gameweek span at most 7 hours and show **zero** price changes, so they add no information |
| Gameweek-to-gameweek pairs | 10 (GW1→2 … GW10→11), 6,524 player pairs |
| Gaps | GW5→6 is three weeks, GW10→11 two weeks (international breaks); the rest are one week |
| Players owned by ≥ 1% of managers, GW2–GW10 | 1,708 player pairs |
| Fields used | `now_cost`, `cost_change_event`, `cost_change_start`, `transfers_in_event`, `transfers_out_event`, `selected_by_percent`, top-level `total_players` |
| Missing | GW1's transfer counts are all zero (pre-season), so GW1 is left out of the probability work. No daily price history: we only see the net change between one snapshot and the next |
| Our own squads | GW2–GW11 `picks:` blocks; GW1 rebuilt from GW2 minus its one transfer; purchase prices from the GW1 snapshot and the executor audit records |

Timing check: `transfers_in_event` in the GW*N* snapshot counts transfers made
since the GW*N−1* deadline, so it is known when we decide. In all 15
executed transfers the price paid equals the snapshot price, so no overnight
change slipped in between our snapshot and the POST.

The data is thin in gameweeks (10 pairs) but large in player pairs. That is
enough for a small lookup table. It is not enough for a fitted model, and
nothing below is one.

## 3. Does the data back the premise?

**Verdict: WEAK.** The signal is real and stable; the money is too small to
move the gate.

### 3.1 Coverage

Enough to estimate a few probabilities with useful intervals (§2). Not enough
to estimate anything finer than about four groups, or to separate overnight
falls from later ones in the week.

### 3.2 Persistence: does a fall predict another fall?

Players owned by ≥ 1% of managers, GW2–GW10 snapshots, outcome = a fall
before the next snapshot. Intervals are 95% Wilson intervals.

| Group | Fell / n | Rate [95% interval] |
|---|---|---|
| Everyone (base rate) | 249 / 1,708 | 14.6% [13.0, 16.3] |
| **Fell this gameweek** (`cost_change_event` < 0) | 19 / 191 | **9.9% [6.5, 15.0]** |
| Below start price (`cost_change_start` < 0) | 98 / 537 | 18.2% [15.2, 21.7] |
| **Net selling ≥ 10% of owners** | 138 / 288 | **47.9%** |
| … and not yet fallen this gameweek | 120 / 184 | **65.2% [58.1, 71.7]** |
| … and already fallen this gameweek | 18 / 104 | 17.3% [11.2, 25.7] |

Two findings:

- **A fall does not predict another fall.** It predicts *fewer* falls than
  average. FPL's price mechanism appears to use up the selling pressure when
  it lowers the price. "Price is falling", as S7 was written, is the wrong
  signal.
- **Selling pressure that has not yet moved the price predicts a fall**, at
  about 4.5× the base rate.

### 3.3 Materiality: what did falls actually cost us?

Players we held across each gameweek GW1→GW11, priced with the selling-price
rule (§1):

| | £m of selling value |
|---|---|
| Lost to falls (15 falls, every one at full cost) | −1.5 |
| Gained from rises (after halving) | +1.1 |
| Net | −0.4 (matches team value 100.0 → 99.6) |
| Of the falls, ones the signal flagged when we decided | 0.8 (8 falls) |

At V = 0.1 EP6 per £0.1m (§5), the flagged £0.8m is worth **0.8 EP6 in
total across nine decisions**: less than half of one 2.0 gate. Capturing
it would have meant several extra sales of players whose sale was otherwise
below the gate, each spending a free transfer that the gate values at 2.0.

One of those £0.1m losses was not a decision at all. GW5 decided to sell
Ndiaye, the session had expired, the sale never ran, and he fell before GW6.

### 3.4 Decision impact

Re-scoring every GW2–GW11 decision (§7) with the term added: **no decision
flips at V ≤ 0.3**. The smallest V that changes any decision is 0.5 (GW7),
and that flip would have lost points and saved no money.

### 3.5 What would change the answer

- Daily snapshots (one bootstrap read a day, not one a week) would show *when*
  in the week falls happen and whether a mid-week sale is ever an option. It
  would not change the size of the money at stake.
- Evidence that the budget actually binds: a cycle where the best move is
  unaffordable by £0.1m–£0.3m. In GW11 the best move did not change between
  bank £0.0m and £3.0m (§5). If tight-budget cycles become common (for
  example, chasing two premium players), V rises and this should be re-run.
- A whole season of snapshots (around 37 gameweek pairs) would tighten the
  intervals, but the 65% figure is already stable between GW2–6 (66%) and
  GW7–10 (62%).

## 4. Probability of a fall or a rise before the next deadline

Lookup table for players owned by ≥ 1% of managers. "Net share" = (transfers
in − transfers out this gameweek) ÷ (owners), with owners =
`selected_by_percent` / 100 × `total_players`.

| Cell | Rule at decision time | P(fall) | Fell / n | P(rise) | Rose / n |
|---|---|---|---|---|---|
| A | net share ≤ −10%, not fallen this gameweek | **0.65** | 120 / 184 | 0.01 | 1 / 184 |
| B | net share ≤ −10%, already fallen this gameweek | 0.17 | 18 / 104 | 0 | 0 / 104 |
| C | −10% < net share ≤ −5% | 0.21 | 57 / 273 | 0 | 1 / 273 |
| D | −5% < net share < +5% | 0.064 | 54 / 838 | 0.04 | 36 / 838 |
| E | net share ≥ +5%, not risen this gameweek | 0 | 0 / 226 | 0.28 | 64 / 226 |
| F | net share ≥ +5%, already risen this gameweek | 0 | 0 / 83 | 0.42 | 35 / 83 |
| — | owned by < 1% | not used | | | |

Stability check (fit-free, so this is the calibration):

| Cell | GW2–GW6 | GW7–GW10 | Our own held players, GW2–GW10 |
|---|---|---|---|
| A | 66% (94/142) | 62% (26/42) | 83% (10/12) |
| B | 16% (14/85) | 21% (4/19) | 13% (1/8) |
| C | 19% (32/169) | 24% (25/104) | 9% (1/11) |
| D | 4% (15/360) | 8% (39/478) | 3% (2/72) |

Players owned by < 1% behave differently (30% fall rate at net share ≤
−10%, n = 443); we rarely own them, so they are left out rather than
modelled.

## 5. V: what £0.1m is worth in EP6

Three readings from the GW11 files:

| Method | EP6 per £0.1m |
|---|---|
| Price slope among regular starters (`p_start` ≥ 0.8), GKP / DEF / MID / FWD | 0.09 / 0.30 / 0.18 / 0.12 |
| Best affordable EP6 at each price, per position | mostly 0, with occasional large jumps: money only matters when it crosses a step |
| `objective --gw 11`, bank swept from £0.0m to £3.0m | **0**: the best single move and the greedy plan were identical at every bank |

The price slope says what money buys *when the budget binds*. The bank sweep
says it did not bind this week. The honest single number is the slope times
the chance the budget binds, which our data puts well below 1.

**Recommended V = 0.1 EP6 per £0.1m. Range 0 to 0.3.**

**Horizon.** A lost £0.1m stays lost for the rest of the season (28
gameweeks from GW11, about 4.7 six-week windows). Do not multiply V by that.
The £0.1m only costs points at a later move where the budget binds, and that
move will be scored by its own six-week gain at that time. Multiplying here
would count the same future points again. Using V = 0.1 already sits at the
generous end for a week like GW11, when the budget is not binding.

## 6. The buying side: a rise avoided is worth almost nothing

The agreed design adds "the purchase-price rise avoided on the IN player by
buying now". Because of the halving rule, that is worth £0 at the next
deadline.

Example in tenths. The IN player costs 50 now and rises to 51 next week.

| | Buy now at 50 | Buy next week at 51 |
|---|---|---|
| Cash spent | 50 | 51 |
| Selling price at 51 | 50 + floor(1/2) = 50 | 51 |
| Spending power (selling price − cash) | 0 | 0 |

Both paths leave the same spending power. Buying early only pays off if he
keeps rising: after two rises, buying early is £0.1m ahead; after three, the
two are level again. The expected gain is about £0.05m for each rise beaten,
worth about 0.005 EP6. That is not worth a term.

What does cost full price on the buying side is a **fall after we buy**: we
take the whole fall. We rarely buy cell A or B players (they are being sold
by everyone else), so this is also negligible.

**Recommendation: OUT side only.**

## 7. Backtest, GW2–GW11

Method: `objective --gw N` re-run today for GW4–GW7 and GW9–GW11, with
selling prices rebuilt from purchase prices (§2), the bank and free
transfers from the previous STATE block, and the term V × P(fall) ×
cost added to each move's blend gain by its OUT player's cell. GW2–GW3 predate
`objective` (GW3 cannot be re-run: a squad id is missing from its players
files), so they are read from the proposals. GW8 was a wildcard. Re-scored
figures can differ slightly from decision time; for example GW5's best move
reads +4.105 / +1.818 today against +4.105 / +2.205 in the proposal.

| GW | Decision taken | Flagged owned players (cell) | Smallest V that changes the decision | What would change | What happened to the price |
|---|---|---|---|---|---|
| 2 | Enzo → Tavernier | Anderson (B) | none | no Anderson move near the gate | Anderson flat |
| 3 | Kusi-Asare → Barry | Mbeumo, Ndiaye, Anderson, Thiago, Shaw (all A) | none | Shaw → De Cuyper already led on EP and was passed over on sequencing (a £1.3m budget argument), which a 0.07 term does not touch | all five fell £0.1m |
| 4 | bank | Ndiaye, Anderson, Thiago, Shaw (B); Gabriel, Mbeumo (C) | 4.3 | Thiago → João Pedro (+1.267) | Thiago fell; the others did not |
| 5 | Ndiaye → E.Le Fée (never executed) | Ndiaye, Shaw (A); Thiago (B) | 2.1 | none | Ndiaye and Shaw fell (the decision was right; the session had expired) |
| 6 | Scott, Ndiaye, Anderson out (3 FT) | Scott (A); Ndiaye, Shaw (B); Mbeumo, Anderson (C) | 0.0 for order only | Ndiaye → E.Le Fée ties Scott → E.Le Fée (+6.663) and wins the tie; the same players leave, only the pairing could change (not re-run) | — |
| 7 | Thiaw → Van Hecke (+2.223) | Schade, Shaw (A); Thiaw (C) | **0.5** | Schade → Sávio (+2.005) overtakes | Schade did **not** fall; Sávio played 0 minutes in GW7 (Van Hecke 4 points); Van Hecke has since risen £0.2m. The flip loses |
| 9 | bank | Calafiori, Barry (C) | 9.3 | none | — |
| 10 | bank | none | — | — | — |
| 11 | Calafiori → De Cuyper | Barnes (B); Mbeumo (C) | 9.7 | none | pending |

**Flips at the recommended V (0.1) or the top of its range (0.3): none.**

## 8. S7 and the new term

S7 asks the optimizer to move off players whose price is falling and to
prefer that move when the EP difference against a rival is small.

- The data says the signal S7 names ("price is falling") does not predict a
  further fall (§3.2). The predictive signal is heavy net selling before the
  fall.
- The data also says "small" must mean very small: the expected value of
  selling a cell-A player a week early is about 0.065 EP6 at V = 0.1.
- With no gate term built, S7 is not made redundant by code. If the
  report-only `price watch:` line below is built, it covers S7's purpose with
  the right signal and an explicit EP figure.

Options for the user:

| Option | Effect |
|---|---|
| a. Withdraw S7 | The tie-break stays with `objective`'s existing rule (S8: steadier player within 0.5 EP6) |
| b. Withdraw S7 and append a narrower row | e.g. "prefer selling a cell-A player (net selling ≥ 10% of owners, not yet fallen) when two moves are within 0.1 EP6" |
| c. Keep S7 | It keeps selecting on a signal that does not predict falls |

Recommendation: **a**, or **b** if the `price watch:` line is built.

## 9. Recommendation

1. **Do not add a price term to the transfer gate.** The largest plausible
   term (V 0.3 × P 0.65 × £0.1m = 0.2 EP6) is a tenth of the gate, and it
   changed no decision in ten cycles.
2. **Smallest defensible version (optional):** a report-only `price watch:`
   line in `objective`, OUT side only, using the cell table in §4 and
   V = 0.1. It changes no figure, gate or ranking.
3. **If the user wants the gate term anyway,** use the same inputs with a cap
   of 0.1 EP6 and a floor: the move must already have blend gain ≥ 1.9 and
   prior-only gain ≥ 0. Then the term can only decide moves within 0.1 of
   the gate, which is the honest size of the effect.
4. **Parity needs purchase prices.** `--sell` is not enough: from selling
   price and current price alone, a profit of 2k−1 and of 2k tenths give the
   same selling price, so the parity is unknowable. `my-team` returns
   `purchase_price` per pick (`MyTeamPick` in fpl/models.py), and the
   executor audits record it. For the report-only line, assume the full
   £0.1m cost when the purchase price is not given: it was true for all 15
   of our falls.

## 10. Follow-up (user challenge)

The user challenged the verdict on three points. Each is tested below with
our own data.

### 10.1 Asymmetry: falls cost in full, rises come back at half

Confirmed, and the figures in §3.3 already use it. The "+£1.1m from rises"
is in selling-price terms, after halving. In market-price (`now_cost`) terms
the same held players rose £2.9m (26 rises) and fell £1.5m (15 falls), a
market-value gain of +£1.4m. After the selling rule, the rises are worth
£1.1m and the falls still cost £1.5m: net −£0.4m. The asymmetry turned a
£1.4m paper gain into a £0.4m real loss. No figure needs correcting.

### 10.2 Information: does heavy selling mean the player is under-performing our prediction?

Test: join each player's price cell at decision time (§4) to his prediction
error (actual points − predicted EP) in the same decision's files.

- Predictions: the players files in the commit that first added each
  `final.md` (the decision record). For the next round these match the
  calibration ledgers data/retro/gw{2…10}-calibration.json exactly (4,141
  rows, largest difference below 0.000001).
- The next two rounds use `ep_gw[1]`, `ep_gw[2]` and `p_start_gw` from the
  same files, against points and starts from the saved event-live snapshots.
- Decisions GW2–GW10; every player with a prediction, including the < 1%
  owned.
- Intervals are 95%, from a bootstrap that resamples players (so repeated
  rows of one player are not counted as independent).
- "Start surprise" = started (1 or 0) − `p_start` for that round.

**Next three rounds (rounds N to N+2), difference against cell D (no strong
transfer signal):**

| Cell | Rows (players) | Points error vs D, per round | Start surprise vs D |
|---|---|---|---|
| A — heavy selling, not yet fallen | 490 (108) | −0.29 [−0.65, +0.07] | **−0.066 [−0.115, −0.015]** |
| B — heavy selling, already fallen | 262 (64) | **−0.67 [−1.09, −0.23]** | **−0.115 [−0.196, −0.035]** |
| **A + B — heavy selling** | **752 (120)** | **−0.43 [−0.78, −0.06]** | **−0.083 [−0.135, −0.030]** |
| C — mild selling | 659 (122) | −0.23 [−0.63, +0.14] | −0.004 [−0.051, +0.039] |
| D — base (its own error +0.23 [−0.02, +0.49]) | 1,846 (192) | 0 | 0 |
| E — buying, not yet risen | 618 (120) | +0.06 [−0.37, +0.45] | +0.051 [+0.004, +0.097] |
| F — buying, already risen | 223 (45) | −0.09 [−0.86, +0.64] | +0.033 [−0.026, +0.083] |
| Fell this gameweek (any net share) | 457 (100) | −0.42 [−0.82, +0.02] | −0.053 [−0.110, +0.005] |
| Owned by < 1% | 6,897 (486) | −0.12 [−0.40, +0.16] | −0.016 [−0.041, +0.013] |

Next round only: A + B −0.45 [−0.86, −0.06]; B alone −1.03 [−1.53, −0.56];
fell this gameweek −0.72 [−1.18, −0.23].

**Checks on the heavy-selling result (A + B, next three rounds):**

| Check | Points error vs D | Start surprise vs D |
|---|---|---|
| Round N / N+1 / N+2 separately | −0.45 / −0.40 / −0.41 | −0.115 / −0.066 / −0.055 |
| Decisions GW2–GW6 | −0.50 [−0.93, −0.08] | −0.090 [−0.150, −0.031] |
| Decisions GW7–GW10 (fewer rows) | −0.39 [−0.99, +0.17] | −0.048 [−0.149, +0.051] |
| Only players with status `a` and no news | −0.36 [−0.78, +0.09] | −0.073 [−0.133, −0.013] |
| Only rounds where he started | +0.09 [−0.45, +0.64] | — |
| Mean `p_start` against actual start rate | 0.578 predicted, 0.499 actual | (cell D: 0.770, 0.774) |

What this says:

- **The user's claim holds, for heavy selling.** Players being sold by ≥ 10%
  of their owners score about 0.4 points a round below our prediction, and
  the gap does not fade over three rounds. Over the three rounds measured
  that is **about −1.3 EP** (interval about −0.2 to −2.3). If it holds for six
  rounds, about −2.5 EP6; we have not measured beyond three.
- **It is about minutes, not form.** When these players start, they score as
  predicted. The whole gap comes from starting less often than `p_start`
  says (0.50 against 0.58). It also holds for players with no injury flag
  and no news, so the crowd is seeing something the news field does not
  carry (rotation, a dropped place, a manager change).
- **Falling price is a weaker version of the same signal**, not a separate
  one: "fell this gameweek" is −0.42 with an interval touching zero.
- **Caveats.** Several groups were compared, so one of them clearing zero
  by chance is possible; the combined A + B result is the one to rely on.
  The later half (GW7–GW10) points the same way but cannot confirm it alone.
  Selling also clusters on players our model already rates low, though the
  comparison is of *errors*, so the model's own rating is already taken out.

**Where a fix belongs: upstream, in the minutes input, not in the gate.**

| | Term in the transfer gate | Cut to `p_start` in the EP model |
|---|---|---|
| Matches where the error is | no: the error is in minutes | yes |
| Covers buying (an incoming player who is being sold), the XI and the captain | no: only the player sold | yes |
| Double-counts once minutes are fixed | yes | no |
| Can be tested before use | no test harness | yes: a `ModelConfig` field, off by default, decided by `fpl backtest` (docs/ep-model.md §5, §8) |

So the change is a CODE item for the user to approve outside the cycle: a
`ModelConfig` field that cuts `p_start` for heavily sold players, switched off
until its backtest gate passes. The measured size is a relative cut of about
14% (0.578 → 0.499); the backtest should sweep around it. Spec in Part 2
below.

Decision check, for scale only. Adding −1.28 EP6 (three rounds) to heavily
sold players, on both sides of every move, changes two GW4–GW11 decisions:
GW4 would sell Thiago for João Pedro instead of banking (João Pedro scored
24 to Thiago's 10 over rounds 4–6), and GW7 would sell Schade for Sávio
instead of Thiaw for Van Hecke (Sávio scored 0 over rounds 7–9; Van Hecke
26). One win, one loss, net −15 points. Two decisions are noise at this
size; the 752-row error test above is the evidence, not these.

### 10.3 Value of money: is −£0.4m large?

**What money buys when it fully binds.** A best-squad search on the GW11
files (the `objective` scoring, solved exactly for a full rebuild at each
team value; `objective` itself grades a given plan but does not search):

| Team value £m | Best squad, EP over GW11–16 |
|---|---|
| 97.0 | 345.57 |
| 99.6 | 348.41 |
| 100.0 | 349.03 |
| 100.4 | 349.75 |
| 103.0 | 352.02 |

- Across £97m–£103m: 0.11 EP6 per £0.1m. Near our value: £99.6m → £100.0m
  is +0.62 EP6 (0.15 per £0.1m), £100.0m → £100.4m +0.72 (0.18 per £0.1m).
- It is lumpy: most single £0.1m steps add nothing, and a few add 0.4–0.6.
- So £0.4m is worth about 0.6–0.7 EP6 on a full rebuild: about **0.1 points
  per gameweek** while the squad is fully re-optimised.

**How often money bound a weekly decision.** Each weekly cycle GW4–GW11
re-run with £0.1m, £0.2m, £0.3m, £0.5m and £1.0m added to the bank:

| GW | Did up to £0.5m more change the best plan? |
|---|---|
| 4 | no (a passing move appears only at +£1.0m) |
| 5 | no (a second passing move at +£1.0m) |
| 6 | blend unchanged; prior-only reading +2.0 at +£0.1m |
| 7 | **yes: +£0.2m allows Thiaw → Hill (+3.27) instead of Thiaw → Van Hecke (+2.22), +1.05 EP6** |
| 9, 10, 11 | no |

One of seven weekly cycles bound at ≤ £0.5m, plus the GW8 wildcard, where
money always binds.

**Season value of £0.1m.** About 0.018–0.030 points per gameweek when money
binds, over the 28 gameweeks GW11–GW38: at most 0.5–0.8 points if it always
bound. It binds at rebuilds (the set-2 wildcard and free hit remain) and
occasionally in a weekly cycle, so a fair share is 30–50% of the time: about
**0.15–0.4 points per £0.1m over the rest of the season**. The −£0.4m is
then worth about 0.6–1.6 points over the rest of the season (at most about
3), roughly 0.02–0.06 points a gameweek.

**The earlier "don't scale V by season" (§5) was too strong.** The argument
that a later move "counts the money again" is wrong: a later move is scored
with whatever budget it has, so the loss is charged nowhere unless it is
charged now. The right V is the season value above, not the six-week slope.
**Revised V = 0.3, range 0.15–0.4** (in points, the same unit as the gate).

**Does that change the money conclusion?** No. At V = 0.3 the largest
price term is 0.3 × 0.65 × £0.1m ≈ 0.2 points (cell A), a tenth of the 2.0
gate, and the backtest in §7 found no decision change below V = 0.5.

### 10.4 Revised recommendation

1. **Build the minutes change, not the price term.** Part 2 of the spec:
   a `ModelConfig` field that cuts `p_start` for heavily sold players, off by
   default, switched on only if its `fpl backtest` gate passes. This is a
   CODE item outside the gameweek cycle and needs the user's approval.
2. **Still no price term in the transfer gate.** Money is real but small
   (about 0.2 points per likely fall at the revised V).
3. **The report-only `price watch:` line (Part 1) stays optional.** Use
   V = 0.3 in it. With Part 2 in place it mainly reports money, since the
   points effect is then in the EP figures.
4. **S7.** The information finding supports S7's instinct but not its
   signal: it should name heavy net selling, not a falling price. Once Part 2
   is on, the EP figures carry it and S7 can be withdrawn; until then, option
   b in §8 (prefer selling a heavily sold player when two moves are close)
   is now better supported than it was, and "close" can be up to about 1
   EP6, the measured three-round effect.

## Spec for the developer

**Not built (decision 2026-11-20, see the top of this document).** Kept for
the record.

Part 1 (below) is the original, optional report-only line; use V = 0.3 in
it (§10.3). Part 2, after it, is the change the follow-up recommends.

### Scope

Report-only line in `fpl objective`. No change to gains, gates, the greedy
reference, tie-breaks or JSON fields that already exist. The gate-term
variant at the end is documented for completeness and is **not** to be built
unless the user asks.

### Inputs

| Input | Source | Note |
|---|---|---|
| `now_cost`, `cost_change_event`, `selected_by_percent` | gw N bootstrap `elements` | already on `Player` |
| `transfers_in_event`, `transfers_out_event` | gw N bootstrap `elements` | **add** to `Player` (ints, ≥ 0) |
| `total_players` | gw N bootstrap top level | **add** to `Bootstrap` (int, > 0) |
| purchase price per owned id | new optional flag `--purchase ID:£m,…` (the orchestrator relays it from `my-team`, as with `--sell`) | when absent for an id: cost = 1 tenth, labelled `purchase unverified` |

### Constants (fpl/objective.py)

```python
PRICE_V_EP6_PER_TENTH = 0.3          # season value of £0.1m, in points (§10.3)
PRICE_MIN_OWNERSHIP_PCT = 1.0
PRICE_NET_HEAVY = -0.10              # net share at or below this: cell A or B
PRICE_NET_MILD = -0.05               # net share at or below this: cell C
PRICE_P_FALL = {"A": 0.65, "B": 0.17, "C": 0.21, "D": 0.064}
```

### Formula

For each owned player `i`:

```
owners      = selected_by_percent / 100 * total_players
net_share   = (transfers_in_event - transfers_out_event) / owners
cell        = none  if selected_by_percent < 1.0 or owners == 0
              A     if net_share <= -0.10 and cost_change_event >= 0
              B     if net_share <= -0.10 and cost_change_event <  0
              C     if net_share <= -0.05
              D     if net_share <  +0.05
              none  otherwise
profit      = now_cost - purchase            (tenths)
cost_tenths = 1 if profit <= 0 or profit is even else 0
              (1 when purchase is unknown)
price_ep6   = PRICE_V_EP6_PER_TENTH * PRICE_P_FALL[cell] * cost_tenths
```

### Print lines

After the `tie-break group:` line, one line per owned player in cell A, B or
C, sorted by `price_ep6` descending then id; nothing for D or none:

```
price watch: Barnes cell B (net -11% of owners, fell this gameweek) P(fall) 0.17; a fall costs £0.1m (bought 6.1, now 6.0) — 0.051 EP at V 0.3
price watch: Mbeumo cell C (net -6% of owners) P(fall) 0.21; a fall costs £0.1m (purchase unverified) — 0.063 EP at V 0.3
```

When no owned player is in A, B or C:

```
price watch: none
```

JSON: a new top-level `price_watch` list of
`{id, name, cell, net_share, p_fall, cost_tenths, purchase_verified, ep6}`.

### Tests (synthetic numbers)

| Case | Given | Expect |
|---|---|---|
| Parity: at purchase | purchase 50, now 50 | cost_tenths 1 |
| Parity: below purchase | purchase 50, now 48 | cost_tenths 1 |
| Parity: odd profit | purchase 50, now 53 | cost_tenths 0 |
| Parity: even profit | purchase 50, now 52 | cost_tenths 1 |
| Parity: unknown purchase | no `--purchase` entry | cost_tenths 1, `purchase unverified` printed |
| Cell A | own 10%, total 10,000,000, in 20,000, out 150,000 (net −13%), cce 0 | A, P 0.65, ep6 0.195 at cost 1 |
| Cell B | same, cce −1 | B, P 0.17, ep6 0.051 |
| Boundary −10% exactly | net share −0.10, cce 0 | A |
| Cell C | net −7%, cce 0 | C, P 0.21 |
| Cell D not printed | net −2% | no `price watch` line for him |
| Riser not printed | net +8% | no line |
| Low ownership | own 0.8%, net −40% | no line |
| Zero owners | selected_by_percent 0 | no line, no division error |
| Ordering | two players with ep6 0.195 and 0.063 | 0.195 printed first |
| No effect on scoring | any squad, with and without the new inputs | baseline, singles, gains, gate notes, reference and verdict identical |
| Bad `--purchase` | `--purchase 12:abc` or an id not in the squad | refuses with the offending item, as `--sell` does |

### Variant not to build unless asked: the term inside the gate

```
gate_gain   = blend_gain + min(0.1, price_ep6(OUT))
passes free = blend_gain >= 1.9 and gate_gain >= 2.0 and prior_gain >= 0
passes hit  = unchanged (blend >= 6.0 and prior > 0); the term never applies to a hit
```

Extra tests: blend 1.95, prior 0.1, OUT in cell A at cost 1 → term
min(0.1, 0.195) = 0.1, gate gain 2.05, passes; blend 1.85, same → fails on the
1.9 floor; blend 1.95, prior −0.1 → fails on prior; OUT in cell A with odd
profit → term 0, fails.

## Spec Part 2: minutes cut for heavily sold players (recommended)

**Not built (decision 2026-11-20, see the top of this document).** Kept for
the record.

### Scope

A model variant in `fpl/ep.py`, switched off by default, that lowers
`p_start` for players being heavily sold. It follows the repo's rule for
model changes: a `ModelConfig` field, a gate record from `fpl backtest`, and
switched on only if the gate passes (docs/ep-model.md §5, §8). It changes no
agent, no gate in `objective` and no CLI output other than through the EP
figures. It is a CODE item: the user approves it outside the gameweek cycle.

### Inputs

| Input | Source |
|---|---|
| `transfers_in_event`, `transfers_out_event` | gw N bootstrap `elements` (add to `Player`, as in Part 1) |
| `selected_by_percent`, `cost_change_event` | gw N bootstrap, already on `Player` |
| `total_players` | gw N bootstrap top level (add to `Bootstrap`, as in Part 1) |

`backtest` must read the same gw N bootstrap snapshot for each past round, so
the variant sees only what was known at that decision.

### Config field and rule

```python
# ModelConfig
heavy_selling_p_start_cut: float | None = None   # relative cut; None = off
```

Validation: `None` or 0 < value < 1.

For each row, at build time:

```
owners    = selected_by_percent / 100 * total_players
net_share = (transfers_in_event - transfers_out_event) / owners
heavy     = selected_by_percent >= 1.0 and owners > 0 and net_share <= -0.10
if cut is not None and heavy:
    p_start_gw[k] = p_start_gw[k] * (1 - cut)   for every k in the horizon
```

The cut applies to every round of the horizon: the measured error did not
fade over rounds N to N+2 (§10.2). `p_start` (the scalar) follows
`p_start_gw[0]`, so the existing tolerance check still holds. The players
file records the cut in the row's `terms` so a reader can see it.

### Backtest

Measured relative cut ≈ 0.14 (0.578 → 0.499). Sweep around it:

```
fpl backtest --rounds 3-10 --sweep heavy_selling_p_start_cut=0.07,0.14,0.20 --cv
```

then `--record heavy-selling-cut` for the chosen value. The gate's five rules
decide. Heavily sold rows are a small share of all rows, so the overall error
change will be small; the result worth reading is the error on those rows.
`--gate-slice` knows only `promoted` and `no_history` today, so a
`heavy_selling` slice needs adding with the field.

### Tests (synthetic numbers)

| Case | Given | Expect |
|---|---|---|
| Off by default | `DEFAULT_CONFIG`, heavy seller | `p_start_gw` unchanged; digest unchanged from today |
| Heavy seller cut | cut 0.14, own 10%, total 10,000,000, in 20,000, out 150,000 (net −13%), `p_start_gw` all 0.9 | every entry 0.774 |
| Already fallen still counts | same, `cost_change_event` −1 | cut applied (cells A and B both count) |
| Boundary | net share exactly −0.10 | cut applied |
| Mild seller | net −7% | unchanged |
| Low ownership | own 0.8%, net −40% | unchanged |
| Zero owners | `selected_by_percent` 0 | unchanged, no division error |
| Validation | cut 0, 1 or −0.1 | `ValueError` |
| Digest | cut 0.14 v `None` | different digests |
| Only minutes move | heavy seller, cut 0.14 | per-start rates unchanged; EP falls by the start term only |
| Backtest sees the past | round M variant | reads the gw M bootstrap, not a later one |

## Method and reproduction

Scripts were throwaway (not committed). To reproduce:

- Panel: for each GW, the latest pre-deadline `data/raw/gw{N}/bootstrap.json`;
  outcome = `now_cost` in gw N+1 minus `now_cost` in gw N; signals from the
  gw N file.
- Held-player losses: squads from the `picks:` blocks, purchase prices from
  the GW1 snapshot and `data/executor/gw*/make-transfers-*.json`.
- V: least-squares slope of `ep_total6` on `price` per position in
  `data/analysis/gw11/players-*.json` for rows with `p_start` ≥ 0.8; bank
  sweep with `objective --gw 11 --sell <GW11 proposal list> --bank B
  --free-transfers 3`.
- Backtest: `objective --gw N --sell <rebuilt> --bank <prev STATE>
  --free-transfers <prev STATE> --top 3000 --format json`, then the term added
  per move by its OUT player's cell.
- Follow-up §10.2: cell per player from the gw N bootstrap; predictions from
  `git show <commit adding data/decisions/gw{N}/final.md>:data/analysis/gw{N}/players-*.json`;
  actual points and `starts` from `data/raw/gw{R+1}/event-live-e{R}.json`.
- Follow-up §10.3: exact best-squad search over the GW11 players files
  (status `a`/`d`, 2/5/5/3, 3 per club, budget on `now_cost`, best XI and
  captain chosen per gameweek), solved with SciPy's integer solver in a
  throwaway environment; and `objective` re-runs with extra bank per cycle.
