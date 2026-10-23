# EP model — the arithmetic behind players-{pos}.json

`fpl ep` turns the player analyst's judgment into expected points. The analyst
decides *who plays and how much to trust each player's history*; the command
does every multiplication. Four positions share one formula and one constants
table, so a term can never be implemented differently for DEF than for MID.

```
inputs-{pos}.json  (analyst judgment)  ─┐
fixtures.json      (fixture analyst)   ─┼─►  fpl ep  ─►  players-{pos}.json
cached bootstrap + season store        ─┘              (schema calibrate reads)
```

Each player's match history comes from the season store by default: a local
SQLite file built from data/raw (§4). `--history-from summaries` reads gw N's
cached element summaries instead.

Local-only: cached snapshots and the season store, no network, no
credentials. Output is derived —
regenerating it from the same inputs is safe until the gameweek is decided
(§4).

## 1. Formula

For each player and each gameweek `g` in the 6-GW window `[N, N+5]`:

```
EP(g) = p_start(g) × Σ_fixtures_in_g  [ appearance + attack + clean_sheet
                                          + goals_conceded + defcon + saves
                                          + bonus + cards ]
```

A blank gameweek contributes 0, a double gameweek two fixture terms. Sub
appearances without a start are ignored (v1 simplification).

| Term | Expression | Positions |
|---|---|---|
| appearance | `1 + P60` | all |
| attack | `(xg90 × goal_pts + xa90 × assist_pts) × mps/90 × attack_mult(fixture)` | all |
| clean_sheet | `p_cs × cs_pts × P60` | GKP, DEF, MID |
| goals_conceded | `−E[floor(GC/2)]`, `GC ~ Poisson(λ_def × mps/90)` | GKP, DEF |
| defcon | `2 × P(hit) × defcon_minutes_factor(mps)` | DEF, MID, FWD |
| saves | `E[floor(S/3)] + pen_save_tail`, `S ~ Poisson(saves90 × mps/90 × λ_def/base_mean)` | GKP |
| bonus | `bonus_per_start × bonus_adjust[pos]` | all |
| cards | `−yellow90 × mps/90` | all |

Where:

- `attack_mult(fixture) = lambda_att / (base_mean × ATT_club) × attack_mult_override`.
  Dividing by the club's own attack index avoids double-counting it — the
  player's xG rate already embeds it.
- `base_mean = (base_lambda.home + base_lambda.away) / 2` from fixtures.json.
- `P60 = P(≥ 60 minutes | start)`, interpolated from minutes-per-start:
  `(50, 0.25) (60, 0.50) (70, 0.80) (80, 0.95) (88, 1.00)`.
- `defcon_minutes_factor`: `(45, 0.0) (60, 0.65) (90, 1.0)`.
- Step functions (saves per 3, goals conceded per 2) are true Poisson
  expectations of the floor, never linearised.

### Scoring constants (2026/27)

| | GKP | DEF | MID | FWD |
|---|---|---|---|---|
| goal | 6 | 6 | 5 | 4 |
| assist | 3 | 3 | 3 | 3 |
| clean sheet | 4 | 4 | 1 | 0 |
| goals conceded, per 2 | −1 | −1 | 0 | 0 |
| saves, per 3 | 1 | 0 | 0 | 0 |
| DefCon threshold (2 pts) | none | CBIT ≥ 10 | CBIT+rec ≥ 12 | CBIT+rec ≥ 12 |
| bonus_adjust (BPS changes: GK save BPS up, CBI rate cut) | 1.10 | 0.90 | 1.00 | 1.00 |
| pen_save_tail per fixture | 0.10 | — | — | — |

`bonus_adjust` values are v1 ASSUMPTIONS for the 26/27 BPS changes; the retro
calibrates them.

## 2. Rates: prior, current, blend

Per player the command derives per-90 rates `xg90 xa90 dc90 saves90 yellow90`
plus `bonus_per_start` and `minutes_per_start` (mps). Pooled rows that record
no start (substitute-only spells, seasons predating the `starts` field) say
nothing about how long the player lasts once he starts, so mps then comes from
the league mean rather than from 90.

1. **Prior** — element-summary `history_past`, most recent PL seasons pooled
   until ≥ 900 minutes or two seasons, minutes-weighted. Shrunk toward the
   position league mean: `rate = (obs × M + league × K) / (M + K)` with
   `M` = prior minutes, `K = 450`. No PL history → `M = 0` → league mean,
   `prior_source = league_mean`.
2. **Current** — element-summary `history` rows with minutes > 0, this season.
   Every played match counts equally and no match is adjusted for its
   opponent. The `recency` and `saves-adjust` gates (§8) tested the
   alternatives and neither beat this:
   - `recency` tried weighting recent matches more (a half-life of 2, 3, 4
     or 6 matches) and dividing each match's xG and xA by how hard its
     opponent was to score against. The half-life counts played matches, not
     rounds, so an injured player's older matches keep their weight.
   - `saves-adjust` tried the same opponent adjustment for a goalkeeper's
     saves.
   - `effective-minutes` was meant to set the blend weight from the
     recency-weighted minutes rather than the raw ones. It could not be
     tested: with no half-life shipped, every match weighs 1, so the weighted
     minutes equal the raw minutes and the variant predicts exactly what the
     baseline does (ΔMAE 0 on every line). Its FAIL says nothing about the
     idea; it needs a fresh run if a half-life ever ships.
   - The opponent ratings used to adjust a past match are round N's, from
     `fixtures.json`. By GW7 they already include that match at a weight of
     about 1/10: the match influences its own adjustment a little, but no
     later result leaks in.
   - For rounds 3–6 those ratings were written by the LLM fixture analyst,
     before `fpl fixtures-rate` existed, so the gate judged the adjustment on
     ratings that production no longer produces.
3. **Blend** — `w_prior = max(0.2, 600 / (600 + current_minutes))`:
   0 min → 1.00, 90 → 0.87, 180 → 0.77, 450 → 0.57, 900 → 0.40, floor 0.20.
   `rate = w_prior × prior + (1 − w_prior) × current`.
   K = 600 is the value the `prior-weight` gate kept: the backtest's sweep did
   not beat it by enough to ship (§8). Worked example:
   <!-- example: prior_weight minutes=180 -->
   a player with 180 current minutes gets `w_prior = 600 / 780 = 0.77`.
   The floor is untested until players pass about 700 current minutes.
4. **League mean** — pooled from the past seasons of the position's players
   whose history `ep` reads, counting those with ≥ 900 prior minutes (≥ 8
   players needed). From the season store those players are the ones
   shortlisted in the gw N bootstrap plus the inputs ids; with
   `--history-from summaries` they are the players with a cached summary in
   gw N. Otherwise the v1 fallback table below, with a warning that names the
   command to fetch more summaries. `bonus_per_start` is the exception: see Bonus below.

| fallback per-90 | GKP | DEF | MID | FWD |
|---|---|---|---|---|
| xg90 | 0.00 | 0.07 | 0.18 | 0.40 |
| xa90 | 0.00 | 0.08 | 0.15 | 0.12 |
| dc90 | 0.0 | 8.5 | 7.0 | 3.5 |
| saves90 | 3.0 | 0 | 0 | 0 |
| bonus_per_start | 0.25 | 0.30 | 0.30 | 0.55 |
| yellow90 | 0.05 | 0.15 | 0.15 | 0.12 |
| minutes_per_start | 90 | 85 | 80 | 78 |

### Promoted clubs and no-history players

A player with no Premier League history gets the position league mean as his
prior (step 1), and player analysts discount some of them with `attack_mult`.
The backtest tests both choices, each with its own gate record:

- `drop-promoted` (data/model/gates/drop-promoted.json) removes the analysts'
  `attack_mult` from players at promoted clubs only, and judges the result on
  those players. Analysts set `attack_mult` on many other players for other
  reasons; this gate leaves those rows as they are.
- `drop-no-history` (data/model/gates/drop-no-history.json) does the same for
  players with no PL history.
- `no-history-k` (data/model/gates/no-history-k.json) tries a separate blend K
  for players with no PL history.

None of them changed the model or the analyst instructions: removing the
discounts did not make those players' predictions better, and the separate K
did not beat the shared one. The numbers are in the gate table in §8.

### Finishing

Some players score more goals than their xG says, season after season. The
code can scale a player's blended `xg90` by his finishing record:
`(goals + k) / (xG + k)`, summed over every Premier League season since
2022/23, the first with xG recorded (`XG_RECORDED_FROM`, the same rule that
sets `xg_recorded` in the season store). `k` pseudo-goals on each side pull the
multiplier toward 1, so a short record barely moves it. An analyst's `xg90`
override is never scaled, and `rates.finishing_mult` then shows 1.0.

The multiplier is off (`FINISHING_K = None`, multiplier 1.0). The `finishing`
gate (data/model/gates/finishing.json) tried k = 20, 10, 5, 2 and 1. A fold
is one round held out and scored with the k that did best on the other
rounds (§8). Every fold picked the smallest k, but the gain was too small and too uncertain to
ship. The numbers are in the gate table in §8.

### DefCon rate (dc90)

The API reports `defensive_contribution` as 0 for every season before
2024/25, when the stat did not exist. Those zeros are missing data, so dc90
counts only the minutes that could have recorded DefCon: this season's rows
and `history_past` seasons from 2024/25 on (`DEFCON_FIRST_SEASON`; season
names compare as strings).

- Prior dc90 = DefCon ÷ those minutes × 90, shrunk toward the league mean
  with `M` = those minutes, not all prior minutes. A prior pool with none of
  them gives the league mean.
- The older seasons still feed every other rate; `prior_minutes` still
  reports all prior minutes.
- The league mean's dc90 is pooled the same way, so older seasons do not
  dilute it.
- A recorded 0 from 2024/25 on is a real 0 and stays in.

### Bonus

Bonus per start skips steps 1–3. It varies a lot from match to match and
little between players, so a player's own record is trusted only once it
covers many starts. All his bonus — the prior seasons from step 1 and this
season — is pooled and shrunk toward the position's league bonus mean:

```
bonus_per_start = (prior_bonus + current_bonus + k × league_bonus)
                / (prior_starts + current_starts + k)
```

| | GKP | DEF | MID | FWD |
|---|---|---|---|---|
| `k` (starts) | 30 | 60 | 20 | 15 |

- Starts are counted per row: a row's `starts`, or its minutes ÷ 90 when it
  records no start (a substitute-only spell, or a season from before the API
  recorded starts), so the bonus such a row earned still has a denominator.
- `league_bonus` is this season's total bonus divided by total starts over
  every bootstrap player of the position. It reads the bootstrap, not the
  players' match histories, so it covers the whole position, not just the
  players whose history `ep` reads. Before anyone has started (total
  starts 0) it is the fallback table value.
- `prior_weight` (computed, overridden, or forced by `--prior-weight`) does
  not touch bonus; an analyst who wants a different bonus rate overrides
  `bonus_per_start` directly, and that override wins.

### DefCon probability

`P_map` interpolates the v1 anchor table on `ratio = dc90_prior / threshold`:
`(0.0, 0.00) (0.4, 0.05) (0.7, 0.20) (0.85, 0.35) (1.0, 0.55) (1.1, 0.70)
(1.3, 0.85) (1.6, 0.93)`, clamped. Observed hit rate = hits / matches with
≥ 60 minutes this season. `P(hit) = w_prior × P_map + (1 − w_prior) × observed`
(`P_map` alone when nothing observed). Retro C1 applies: the mapping itself
is never re-fitted inside a gameweek.

## 3. Contracts

Both documents are LLM-written and validated at the boundary: unknown keys,
bad ranges and mismatched names refuse with the offending row.

### inputs-{pos}.json — written by the player analyst

```json
{
  "schema_version": 1,
  "gw": 3,
  "position": "MID",
  "players": [
    {
      "id": 426,
      "name": "B.Fernandes",
      "p_start": 0.92,
      "p_start_gw": [0.92, 0.92, 0.90, 0.90, 0.90, 0.90],
      "uncertainty": "LOW",
      "notes": "35 starts 25/26; pens; GW1 90'",
      "overrides": {"attack_mult": 0.9},
      "reason": "lost penalty duty to Cunha"
    }
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | bootstrap element id; must be this position |
| `name` | no | if present must equal bootstrap `web_name`, ignoring accents and case — guards id typos; the output always carries `web_name` |
| `p_start` | yes | P(starts) for a window fixture; 0–1. With `p_start_gw` present it is unused: set it to `p_start_gw[0]`, or `ep` warns that it was ignored |
| `p_start_gw` | no | always six values, one per window gameweek (the surplus is ignored at the season's tail); overrides `p_start` per gameweek |
| `uncertainty` | yes | LOW / MED / HIGH — rate risk (agents/player-analyst.md); passed through, never used in the arithmetic |
| `notes` | no | analyst prose, copied to the output |
| `overrides` | no | any of `xg90 xa90 dc90 saves90 bonus_per_start yellow90 minutes_per_start prior_weight attack_mult` |
| `reason` | when `overrides` present | why the default rate is wrong |

Override ceilings (a decimal slip refuses instead of scoring): `xg90`, `xa90`
≤ 2; `dc90` ≤ 30; `saves90` ≤ 10; `bonus_per_start` ≤ 3; `yellow90` ≤ 1;
`minutes_per_start` in (0, 90]; `prior_weight` in [0, 1]; `attack_mult` in
[0.25, 4].

Coverage rule: every player of the position priced above £4.5m with status
`a` or `d` must appear; the command refuses otherwise and lists them. Players
at or below £4.5m, or unavailable, absent from the file are excluded and
counted. `--allow-missing-ids <ids>` exempts the listed players: they go
unscored and the run names them in a warning.

### fixtures.json — written by `fpl fixtures-rate`

```json
{
  "schema_version": 1,
  "gw": 3,
  "base_lambda": {"home": 1.54, "away": 1.33},
  "ratings": {"ARS": {"att": 1.22, "defw": 0.67}},
  "fixtures": [
    {"club": "ARS", "gw": 3, "opp": "CHE", "venue": "H", "fdr": 4,
     "lambda_att": 1.78, "lambda_def": 1.24, "p_cs": 0.29, "band": false}
  ]
}
```

`ratings` must hold every bootstrap club, each `att`/`defw` in [0.3, 3];
`base_lambda` values in [0.5, 5]; `lambda_att`/`lambda_def` in (0, 6]. A club
never plays itself and has at most two rows per gameweek, and a double
gameweek's two rows are different fixtures. Rows outside the
window are ignored; a club with no row for a window gameweek is a blank
(EP 0) and is reported. The model reads `base_lambda`, `att`, `lambda_att`,
`lambda_def` and `p_cs`; `defw`, `fdr` and `band` (the promoted-club ±15pp
uncertainty band) are for the analysts' own reads and are not emitted.

### players-{pos}.json — output

The documented prediction schema (`id name team price p_start p_start_gw
ep_gw ep_total6 ep_per_million uncertainty notes`) plus, per row:

- `p_start` is GW N's probability (`p_start_gw[0]`); `p_start_gw`, `ep_gw` and
  `fixtures` hold one entry per window gameweek — six, fewer at the season's tail
- `fixtures`: strings such as `"CHE(H)"`, `"AVL(A)+BHA(H)"`, `"-"`
- `terms`: window sums of the eight terms, weighted by `p_start_gw`, so they add up to `ep_total6`
- `rates`: the effective rates, `dc90_prior`, `prior_weight`, `prior_source`, `attack_mult`, prior and current minutes
- `rates.finishing_mult`: always present. The finishing multiplier applied to
  `xg90` (§2 Finishing): 1.0 while the multiplier is off, as it is now, and
  1.0 when an analyst's `xg90` override bypasses it
- `model`: the model version, the first 8 hex digits of a hash of the model
  constants (`ModelConfig.digest()`). `objective` refuses players files whose
  version differs from the code's
- `p4_gw` and `returns5`: the consistency columns (§9). They are not EP terms
- `share_flag`: the team-xG share check's finding for the row (§4), or null

There is no `terms.form`: the model has no form term (§10).

Rows sort by `ep_total6` descending. `calibrate` reads the documented fields
and ignores the rest.

## 4. Running it

```
uv run python -m fpl ep --gw 3 --position MID
```

Defaults: `data/analysis/gw3/inputs-MID.json` and `fixtures.json` in, `players-MID.json`
out; `--inputs`, `--fixtures`, `--out` override, `--format json` prints the
document. The output starts with a `model <digest>` line. The table shows the
top rows with their term breakdown and the `p4`, `ret5` and `share` columns,
the coverage line, and the ids with no history `ep` can read, together with
the command that fetches it.

Each player's history comes from the season store by default (`--store`
names another file). A store that is behind data/raw is synced first. For an
id with no history, the printed command is `summaries --gw N --missing-past`,
which fetches every player who has no summary in any gameweek; the next read
syncs the new summaries into the store. With `--history-from summaries`, `ep`
reads gw N's cached summaries instead, and the printed command is
`summaries --gw N --ids <ids>`.

Once `data/decisions/gw{N}/final.md` exists (`--decisions-root` moves it), the
gameweek is decided and its players files are the decision record: `ep`
refuses to write `players-{pos}.json` and only writes elsewhere with `--out`.

Team-xG share check: for each player with at least 3 counted starts, `ep`
compares the share of his club's xG and xA that his EP rates assume with the
share he has actually taken this season, and flags the row when the two
differ by more than 0.05 or 40% of the season share, whichever is larger
(`fpl/team_share.py`). It prints one `share check: <k> flagged (ids …)` line;
`--share-detail` adds one line per flagged row with both shares. The flag is
a reading aid for the analyst: a reason to look again at that player's rates,
never on its own a reason to override them. When the check cannot run (no
event-live snapshot to measure club xG from), `ep` prints a `share check
skipped` warning and still writes the file.

What-if view: `--prior-weight W` (W in [0, 1]) forces every row's
`prior_weight` to W, replacing any per-row `prior_weight` override; the other
overrides still apply. `--prior-weight 1.0` gives the prior-only view.
Because it is not the real prediction, it requires `--out`, so it never
overwrites `players-{pos}.json`, and it cannot be combined with `--check`.
A W outside [0, 1] is refused.

```
uv run python -m fpl ep --gw 3 --position MID --prior-weight 1.0 --out /tmp/players-MID-prior.json
```

## 5. Changing the model

A retro correction to the arithmetic (a coefficient, an anchor, a blend
constant) is a change to `fpl/ep.py` and this file, shipped with tests, not an
instruction to an analyst. The judgment inputs stay where they are.

A decided round's players-*.json is the decision record. `calibrate` scores the
predictions lock, or else the files in the commit that first added that round's
final.md, and warns when the working tree differs.

A model change is judged with `fpl backtest` (§8) and recorded under
data/model/gates/; a decided round is never regenerated to judge it.

## 6. Fixture ratings

`uv run python -m fpl fixtures-rate --gw N` writes `fixtures.json` and
`fixtures-tables.md` from the cached snapshots plus
`data/analysis/club-priors.json`. Code: `fpl/fixture_ratings.py`. It reads no
network and no credentials.

Inputs:
- `data/raw/gw{N}/bootstrap.json` (club short names, each player's club) and
  `fixtures.json`.
- This season's match rows. By default they come from the season store,
  each row on the side of the club the player played for in that match. With
  `--history-from summaries`, they come from every cached player summary in
  `data/raw/gw{N}/players/` (steps 2 and 3).
- `event-live-e{r}.json` from `data/raw/gw{r+1}/` for every round r before N,
  on either path (the season store is built from these snapshots). The data
  collector's `event-live` step fetches the latest one. Without it the
  command refuses and names the command that fetches it,
  `event-live --gw r+1 --round r`.
- `club-priors.json`: one ATT and DEFW per club, fixed at GW1, never edited.
- `data/analysis/gw{N-1}/fixtures.json`, if present, only for the Δ columns.

Steps:
1. A played match is a fixture with an event before N that is finished.
2. A club's xG in a match is the sum of the `expected_goals` of every summary
   row for that fixture on that side (`was_home`). Rows follow the fixture,
   not the player's current club, so a transferred player's old matches stay
   with his old club.
3. A player who played in a match but has no summary row is recovered from
   that round's event-live snapshot and counted on his current club's side.
   In a double gameweek his xG is split across the two fixtures by minutes.
4. Each side's xG is rounded to 2 decimals. The match then gives each club an
   implied ATT = xG / (base for its venue × opponent's prior DEFW) and an
   implied DEFW = xG conceded / (base for the opponent's venue × opponent's
   prior ATT). Both are clipped to [0.55, 1.80] and the clips are counted.
5. Blend: (k × prior + Σ implied) / (k + matches played).

   | Rating | k | k, promoted club |
   |---|---|---|
   | ATT | 5.7 | 4.0 |
   | DEFW | 4.0 | 3.0 |

   The prior keeps at least 25% weight through GW10 (k / (k + 9)).
6. ATT and DEFW are each rescaled to a 20-club mean of 1.00, then rounded to
   2 decimals. At GW1, with no matches, the ratings are the priors rescaled.
7. Rows for GW N to N+5 (never past GW38): λ_att = base × ATT_club ×
   DEFW_opp from the rounded ratings, rounded to 2 decimals, with base 1.54 at
   home and 1.33 away. λ_def is the opponent's λ_att and P(CS) =
   e^(−λ_def), rounded to 2 decimals. `band` is true when either club is
   promoted. A double gameweek gives two rows; a blank gives none.

The command prints the rounds and matches used, how many player-rounds were
recovered from event-live, the clip count, the league's xG per match against
the 1.54 + 1.33 base, and the window's blanks and doubles. `fixtures-tables.md`
holds the ratings with their Δ, the implied ratings by round, the attack and
defence tickers, the swings, FDR against the model's ranks, the promoted-club
rows with P(CS) ≥ 0.30, and one detail table per window gameweek. Every rank
is printed in its own column: `ATT rating rank` and `DEFW rating rank` in the
ratings table (level clubs share a rank), `ATT rank` and `CS rank` in the
tickers and in the FDR table. The fixture analyst quotes these tables, ranks
included, and never recomputes them.

## 7. Squad objective (`fpl objective`)

The squad optimizer, the red-team and the eval score squads with one tested
function, `fpl/objective.py`. Searching for a plan is the agent's job; scoring
it is code.

- **Objective:** the sum over GW N..N+5 of the best XI's EP plus the
  captain's EP. The captain is the XI's highest `ep_gw[k]`, so it counts
  twice.
- **Best XI for GW k:** for each formation, in the order 3-4-3, 3-5-2, 4-3-3,
  4-4-2, 4-5-1, 5-2-3, 5-3-2, 5-4-1, take the top goalkeeper and the top
  players per position, sorted by EP then id. The best total wins; a tie goes
  to the earlier formation. This is exact: each position's top player is in
  every formation, so the squad's best player always starts and the captain
  term never changes which XI wins. The bench scores nothing.
- **Two readings:** blend is players-*.json as published. Prior-only is the
  same inputs-*.json with every row's prior weight forced to 1.0, scored in
  memory with `build_predictions` and rounded as `fpl ep` writes. Every
  figure is printed on both.
- **Pool:** players in both readings whose status is `a` or `d`.
- **Money:** integer tenths. A purchase costs `now_cost`. A sale earns the
  relayed selling price (`--sell`); without it, `now_cost`, labelled
  unverified. A legal squad is 2/5/5/3, at most 3 per club, bank ≥ 0.
- **Move marginal:** the plan's objective minus the objective of the plan
  with that one pair undone.
- **Gates:** a free move needs blend ≥ 2.0 and prior-only ≥ 0; a hit needs
  blend ≥ 6.0 and prior-only > 0. When a plan takes hits, its lowest-gain
  moves are the paid ones. With free transfers left, no further single move
  may pass the free gate.
- **Greedy reference:** repeatedly take the best legal single move (blend
  gain, then out id, then in id) that keeps its prior-only sign, while it
  passes the gate for its slot: free while free transfers last, then a hit.
  A plan's blend gain may fall at most 0.05 below the reference's.
- **Chips:** a wildcard or free hit must beat the greedy plan, net of its hit
  costs, by ≥ 6.0 on blend and ≥ 0 on prior-only. A free hit is scored on
  GW N alone.
- **Free transfers next GW:** min(5, free − used + 1) when used ≤ free,
  else 1. Each transfer beyond the free ones costs 4.
- **Reported, never priced:** near-tie XI↔bench pairs (formation-legal swaps
  within 0.25 GW-N EP, with each player's DefCon share of EP6) and dead bench
  slots (`p_start_gw[0]` < 0.5).

## 8. Backtest

`fpl backtest` scores past rounds again under a changed model (a variant) and
compares it with the current model on the same player-rounds. It reads only
files already on disk: no network, no credentials.

### What the gates found

Every change tested so far failed its gate, so none shipped. The model runs
the same constants it ran before the backtest existed: `combined.json`
`shipped_config` equals `DEFAULT_CONFIG`, and a test keeps them equal.

The code for each tested change is kept, switched off. Each is a
`ModelConfig` field whose default is a constant in `fpl/ep.py`:

| Change | Setting (off value) | Gate |
|---|---|---|
| a different blend K | `BLEND_EQUIV_MINUTES` (stays 600) | `prior-weight` |
| a separate blend K for players with no PL history | `blend_k_no_history` (None) | `no-history-k` |
| weighting recent matches more | `HALF_LIFE_MATCHES` (None) | `recency` |
| adjusting xG and xA for the opponent | `OPPONENT_ADJUST` (False) | `recency` |
| adjusting saves for the opponent | `OPPONENT_ADJUST_SAVES` (False) | `saves-adjust` |
| blend weight from recency-weighted minutes (not testable yet: §2) | `BLEND_ON_EFFECTIVE_MINUTES` (False) | `effective-minutes` |
| finishing multiplier | `FINISHING_K` (None) | `finishing` |

The policy gates asked whether the analysts should stop discounting players
at promoted clubs (`drop-promoted`) and players with no PL history
(`drop-no-history`). Neither result supported a change, so the analyst
instructions stay as they are (§2).

`fpl persistence` found no evidence that a player's recent prediction errors
carry over to his next round, so no form term was built (§10). The test
could not rule out a small carry-over either: the interval includes 0.

The one change the work made: `p4_gw` breaks near ties in `objective` only
for the positions where it beats a plain base rate among likely starters,
GKP and FWD (§9).

### Where the records live

- `data/model/gates/<name>.json`: one gate record per test, written once.
- `data/model/gates/manifest.toml`: the tests in the order they run, each with
  its name, kind and arguments.
- `data/model/gates/combined.json`: every passing model change together, and
  `shipped_config`, the full set of constants that must ship.
- `data/model/gates/archive/`: records replaced with `--force`.

The records are derived from files on disk, but they are committed: they are
the evidence for each model decision.

### Running the gates again

From the repo root, once the latest round's event-live snapshot is final:

```
uv run python -m fpl backtest --gw 8 --rounds 3-7 \
  --manifest data/model/gates/manifest.toml --record-all
uv run python -m fpl persistence --gw 8 --window 3 --min-starts 2 --record persistence
uv run python -m fpl gates --gw 8 --summary
uv run python -m fpl gates --gw 8 --render
```

- `--record-all` runs each manifest entry that has no record yet, in order,
  then writes `combined.json` again. `--force` archives the existing records
  and runs every entry again. `combined.json` is archived only when its
  content changes; the code version, the recording time and the file paths
  of the inputs do not count as changes.
- `persistence --record persistence` refuses when the record exists. To
  record it again, add `--force`, which archives the old one. The command
  exits 3 when the result is not significant, which is the expected outcome
  today; the record is still written.
- An entry runs on top of the earlier passing entries, but an existing record
  is skipped. So when an entry starts to pass (for example `recency`), re-run
  with `--force`, or the later entries (such as `effective-minutes`) keep
  records judged without it.
- `--record <name>` with `--set` or `--sweep` records a single test outside
  the manifest.
- The match history comes from the season store beside `--data-root`
  (`data/store/`), synced first when it is behind the raw tree; `--store`
  names another file. Each record says which source it read, under
  `data.history_from`.
- `gates --summary` prints each record's result and what happened to it;
  `gates --render` rewrites the table at the end of this section.
- Without `--record` or `--record-all` the command writes nothing, so trying a
  variant is free: `--set blend_k=450`, or `--sweep blend_k=300,450 --cv`.

Other options: `--analysis-root`, `--decisions-root` and `--retro-root` move
the inputs; `--inputs-policy` and `--gate-slice` run a policy test; `--detail`
adds per-position and slice tables; `--format json` and `--out` give the full
document; `--max-ledger-n-gap N` exits 1 when a round's line count differs
from its calibration ledger's by more than N.

### Which rounds, and what is read

A round r can be scored when it has analyst inputs under
`data/analysis/gw{r}/` and a final event-live snapshot at
`data/raw/gw{r+1}/event-live-e{r}.json`. Final means its `.meta` sidecar says
`final: true`, or a kept bootstrap of a later gameweek, fetched no later than
the snapshot, shows round r data-checked. An archived bootstrap under
`.archive/` never counts: git ignores it, so a proof resting on it could not
be checked from the committed files. This is the same rule the season store
uses (`fpl.store.live_final`), and each gate record names the file that
proved each round final, under `data.actuals.<round>.basis`. The gates use
rounds from 3 on: before
GW3 the analysts computed EP by hand, so there is no code prediction to
compare with.

Nothing from after a round's deadline may reach its prediction:

- every model input (the gw r `bootstrap.json` and `fixtures.json`) must
  have been fetched before round r's deadline, by its sidecar;
- this season's match rows come from the season store as of round r, so only
  from rounds before r, for the players `fpl ep` reads: those shortlisted in
  the gw r bootstrap plus the round's inputs ids. Their past seasons come from
  whichever summary the raw tree holds, as past seasons do not change during
  a season;
- with `--history-from summaries` they come instead from the gw r cached
  summaries, each fetched before the deadline and holding only rounds before
  r. This reading works for rounds 3–6 only: from round 7 the analysts
  judged players whose summaries were not cached that gameweek, and from GW9
  the collector keeps a summary only for players with no past seasons on file;
- the inputs on disk must equal those in the round's decision commit (the
  commit that first added its final.md); `--no-drift-check` skips this;
- the actual points come only from the final event-live snapshot.

A player the coverage rule (§3) requires but the analyst left out is not
scored, as in production, and the run names him in a warning instead of
refusing. A player the analyst did judge but who has no history in the
chosen source refuses the round, naming the round and how many players: he
would be scored on the league mean, and a backtest must not do that
silently.

The baseline is today's code run on the recorded inputs. It is not the
calibration ledger, which scores what was predicted at the time. The
per-round table prints the gap as `code drift`: the mean difference per
player between the two predictions. In `baseline.json` it is about 0.05
points for rounds 3–6 and 0.0005 for round 7. Round 7's small gap comes from
the season store: it gives 13 players the analysts judged a history that
the round-7 summaries did not hold, so they are no longer scored on the
league mean.

### The gate

Lines are paired by (round, id). Per line, d = |e_variant| − |e_baseline|,
computed from the line errors, never from rounded aggregates.

- ΔMAE = mean d.
- SE clustered by (round, club), CR0: SE = √(Σ_g (Σ_{i∈g} (dᵢ − ΔMAE))²) / n.
- CI = ΔMAE ± 1.96·SE.
- Per-round ΔMAE_r = mean d over round r; a round is a win when ΔMAE_r < 0.

A variant beats the baseline iff all five hold:

| Rule | Key in `reasons` | Condition | Constant |
|---|---|---|---|
| 1 | `ci` | CI upper bound < 0 | `GATE_Z = 1.96` |
| 2 | `bias` | \|bias_variant\| ≤ \|bias_baseline\| + 0.05 | `GATE_BIAS_SLACK = 0.05` |
| 3 | `position <POS>` | every position: ΔMAE_pos ≤ +0.02 | `GATE_POSITION_SLACK = 0.02` |
| 4 | `effect` | ΔMAE ≤ −0.01 | `GATE_MIN_EFFECT = -0.01` |
| 5 | `rounds` | round wins ≥ M − 1 of M rounds | — |

For a sweep, the variant's lines are its leave-one-round-out (LORO) predictions.
The output always prints the per-round ΔMAE.

### Sweeps: leave-one-round-out and the ship value

A sweep (`--sweep key=v1,v2,… --cv`) tries several values of a setting, with
the current value always first. For each round, it picks the value with the
lowest MAE on the other rounds and scores the held-out round with it; the
gate judges those held-out predictions. This measures how well the choosing
works, not one fixed value. A fold may learn from rounds after the one it
holds out, which is acceptable for a setting like this.

The ship value is the value picked most often across the rounds, ties going
to the earlier value in the grid. It ships only when the gate passes.

### Policy tests and slices

A policy test (`--inputs-policy`) changes the analysts' inputs rather than the
code, for example removing their `attack_mult` from players at promoted
clubs. A policy never ships a constant. `--gate-slice` applies the same five
rules to the lines of one group of players (promoted clubs, or no PL
history); with fewer than 40 lines the slice verdict is n/a, and rule 3 is
pooled across positions when a position has fewer than 30 lines.

A policy's hypothesis is `supported` when the baseline under-rates the group
(its bias is above 0), the variant brings that bias closer to 0, the slice
gate passes, and the overall ΔMAE is not above 0. The overall gate need not
pass, since a change confined to a small group barely moves it. For a model
test on a slice, the overall gate must pass and the slice gate must not fail.

### The manifest and `combined.json`

Each manifest entry runs against the `baseline` record's config plus the ship
values of earlier passing model entries, unless the last combined record
reverted them, so a run after constants have
changed reproduces the same records. `combined.json` then tests every passing
ship value together against the baseline. If that fails, the last pass is
dropped and the rest tested again, until it passes or none is left; dropped
names go in `reverted`. A `calibration` entry (`p4`) records the `p4_gw`
scores and has no verdict.

Gate records live under `data/model/gates/`. The table between the markers
below is generated from them by `fpl gates --render`; do not edit it by hand.

<!-- gates:begin -->
| Gate | Kind | Rounds | Grid | Ship value | ΔMAE | CI | Bias | Wins | Verdict | Reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | model | 3-7 | — | — | — | — | — | — | — | reference: n 2127, bias +0.183, MAE 1.643 |
| prior-weight | model | 3-7 | blend_k=600,300,450,900,1200 | — | −0.0043 | [−0.008, −0.001] | +0.183→+0.192 | 5/5 | FAIL | effect: ΔMAE −0.0043 > −0.01 |
| drop-promoted | policy | 3-7 | — | — | +0.0021 | [−0.001, +0.005] | +0.183→+0.174 | 1/5 | FAIL · slice promoted FAIL: n 319, ΔMAE +0.0140 [CI −0.003, +0.031], bias +0.137→+0.077 · hypothesis not supported | ci: upper +0.005 ≥ 0; effect: ΔMAE +0.0021 > −0.01; rounds: won 1 of 5, need 4 |
| drop-no-history | policy | 3-7 | — | — | +0.0017 | [−0.001, +0.004] | +0.183→+0.173 | 1/5 | FAIL · slice no_history FAIL: n 462, ΔMAE +0.0080 [CI −0.004, +0.020], bias +0.345→+0.298 · hypothesis not supported | ci: upper +0.004 ≥ 0; effect: ΔMAE +0.0017 > −0.01; rounds: won 1 of 5, need 4 |
| no-history-k | model | 3-7 | blend_k_no_history=none,150,300 | — | +0.0002 | [−0.002, +0.003] | +0.183→+0.183 | 2/5 | FAIL · slice no_history FAIL: n 462, ΔMAE +0.0011 [CI −0.010, +0.012], bias +0.345→+0.343 · hypothesis not supported | ci: upper +0.003 ≥ 0; effect: ΔMAE +0.0002 > −0.01; rounds: won 2 of 5, need 4 |
| recency | model | 3-7 | half_life_matches=none,2,3,4,6; opponent_adjust=false,true | — | +0.0007 | [−0.001, +0.002] | +0.183→+0.185 | 3/5 | FAIL | ci: upper +0.002 ≥ 0; effect: ΔMAE +0.0007 > −0.01; rounds: won 3 of 5, need 4 |
| saves-adjust | model | 3-7 | — | — | +0.0001 | [−0.000, +0.000] | +0.183→+0.183 | 1/5 | FAIL | ci: upper +0.000 ≥ 0; effect: ΔMAE +0.0001 > −0.01; rounds: won 1 of 5, need 4 |
| effective-minutes | model | 3-7 | — | — | +0.0000 | [+0.000, +0.000] | +0.183→+0.183 | 0/5 | FAIL | ci: upper +0.000 ≥ 0; effect: ΔMAE +0.0000 > −0.01; rounds: won 0 of 5, need 4 |
| finishing | model | 3-7 | finishing_k=none,20,10,5,2,1 | — | −0.0026 | [−0.008, +0.002] | +0.183→+0.192 | 4/5 | FAIL | ci: upper +0.002 ≥ 0; effect: ΔMAE −0.0026 > −0.01 |
| p4 | calibration | 3-7 | — | — | — | — | — | — | — | p4 skill GKP +0.160 (starters +0.0201), DEF +0.095 (starters −0.0001), MID +0.094 (starters −0.0027), FWD +0.156 (starters +0.0147) |
| persistence | persistence | 1-7 | — | — | — | — | — | — | not significant | window 3: n 711, slope +0.034 [−0.095, +0.162], r +0.020; window 1: n 1098, slope +0.007 [−0.046, +0.060], r +0.007; window 2: n 805, slope +0.018 [−0.083, +0.119], r +0.013 |
| combined | combined | 3-7 | — | ships baseline (no passing entries) | — | — | — | — | — | — |
<!-- gates:end -->

## 9. Consistency columns

Two columns describe how steady a player is, not how many points he is
expected to score. Neither is an EP term: `ep_gw` and `ep_total6` never use
them. `objective` uses them only to break a near tie between two transfers.

### `p4_gw` — chance of 4 or more points

`p4_gw[g]` is the chance the player scores at least 4 points in GW g:
`p_start × P(points ≥ 4 | he starts)`. Given a start, `fpl/consistency.py`
builds the whole points distribution for each fixture from the same means the
EP formula uses (§1), adding these independent parts:

- appearance: 2 points with the chance of playing 60+ minutes, else 1;
- clean sheet: the position's clean-sheet points, in the 60+ branch only;
- goals: a Poisson count with the goal mean, times the position's goal points;
- assists: a Poisson count with the assist mean, times 3;
- DefCon: 2 points with the DefCon chance;
- saves: one point per 3 saves, the saves a Poisson count.

A double gameweek adds both fixtures; a blank gameweek gives 0. Some scoring
is left out, and each omission pushes the chance one way:

| Left out | Effect on `p4_gw` |
|---|---|
| bonus points | too low |
| substitute appearances (a non-start counts as 0) | too low for rotation players |
| goals conceded, and its link to the clean sheet | too high for GKP and DEF |
| cards, own goals, missed penalties | too high |
| penalty saves | slightly too low for GKP |

### `returns5` — returns over the last five rounds

`returns5` is `[k, n]`: of the rounds GW−5 to GW−1 in which the player had a
match row, n counts them and k counts those where his raw points totalled 4 or
more. A double gameweek's rows are added first; a round where he did not play
still counts in n, because being available is part of being steady.

### The tie-break in `objective`

When two single transfers share the same outgoing player and both pass the
transfer rule, and the second is within 0.5 EP6 of the best, `objective`'s
greedy reference picks the steadier incoming player:

1. the higher mean `p4_gw` over the next 3 GWs, when the gap is at least 0.03
   and the position is calibrated (below);
2. else the higher return rate k/n, when both players have at least 3 rounds
   and the gap is at least 0.2;
3. else the move ahead on EP6.

It applies to single transfers only, not to wildcard packages. Its
`tie-break move:` line names the winner, and a plan that takes the other move
fails the reference check.

### Which positions are calibrated

`p4_gw` decides a tie only for a position where it beats a plain base rate
among likely starters (`p_start` 0.5 or more), judged by Brier score with each
round's base rate taken from the other rounds. The tie-break only ever compares
two players expected to start, so the skill over all players, which mostly
rewards knowing who will play, is not the test.

The `p4` calibration record (data/model/gates/p4.json) and `combined.json`
hold the scores; the `p4` row of the gate table in §8 shows them. The
positions with a starter skill above 0 are `objective.P4_CALIBRATED`, and the
`ep` table shows `p4` only for those positions. The calibrated positions are
GKP and FWD. A test keeps the constant and this sentence equal to
`combined.json`.

## 10. Form

There is no form term. A form term would add a share of a player's recent
prediction errors to his next prediction, and it is worth adding only if those
errors carry over from one round to the next. `fpl persistence` measures that
on the calibration ledgers: for each player who started a round, it compares
his error in that round with his mean error over the rounds before it that he
started. The record is data/model/gates/persistence.json and its numbers are
in the gate table in §8: the slope is close to 0 and its interval includes 0
for every window tried (1, 2 and 3 rounds). So the ledgers give no evidence
that recent errors predict the next one, though the interval is too wide to
rule out a small effect.

Two cautions when reading the measurement:

- The GW1–2 ledgers score EP that the LLM analyst computed by hand, and the
  GW3 onward ledgers score EP that the code computed. The pooled errors mix
  the two.
- `objective`'s prior-only reading builds predictions at prior weight 1, so
  a form term would be 0 there by construction.
