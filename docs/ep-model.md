# EP model — the arithmetic behind players-{pos}.json

`fpl ep` turns the player analyst's judgment into expected points. The analyst
decides *who plays and how much to trust each player's history*; the command
does every multiplication. Four positions share one formula and one constants
table, so a term can never be implemented differently for DEF than for MID.

```
inputs-{pos}.json  (analyst judgment)  ─┐
fixtures.json      (fixture analyst)   ─┼─►  fpl ep  ─►  players-{pos}.json
cached bootstrap + element summaries   ─┘              (schema calibrate reads)
```

Local-only: cached snapshots, no network, no credentials. Output is derived —
regenerating it from the same inputs is always safe.

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
3. **Blend** — `w_prior = max(0.2, 600 / (600 + current_minutes))`:
   0 min → 1.00, 90 → 0.87, 180 → 0.77, 450 → 0.57, 900 → 0.40, floor 0.20.
   `rate = w_prior × prior + (1 − w_prior) × current`.
4. **League mean** — pooled from cached summaries of the position with ≥ 900
   prior minutes (≥ 8 players); otherwise the v1 fallback table below, with a
   warning. `bonus_per_start` is the exception: see Bonus below.

| fallback per-90 | GKP | DEF | MID | FWD |
|---|---|---|---|---|
| xg90 | 0.00 | 0.07 | 0.18 | 0.40 |
| xa90 | 0.00 | 0.08 | 0.15 | 0.12 |
| dc90 | 0.0 | 8.5 | 7.0 | 3.5 |
| saves90 | 3.0 | 0 | 0 | 0 |
| bonus_per_start | 0.25 | 0.30 | 0.30 | 0.55 |
| yellow90 | 0.05 | 0.15 | 0.15 | 0.12 |
| minutes_per_start | 90 | 85 | 80 | 78 |

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
  cached summaries, so it covers the whole position, not just the players
  whose summaries happen to be cached. Before anyone has started (total
  starts 0) it is the fallback table value.
- `prior_weight` (computed or overridden) does not touch bonus; an analyst who
  wants a different bonus rate overrides `bonus_per_start` directly, and that
  override wins.

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
| `name` | no | if present must equal bootstrap `web_name` — guards id typos |
| `p_start` | yes | P(starts) for a window fixture; 0–1 |
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
counted.

### fixtures.json — written by the fixture analyst

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

Rows sort by `ep_total6` descending. `calibrate` reads the documented fields
and ignores the rest.

## 4. Running it

```
uv run python -m fpl ep --gw 3 --position MID
```

Defaults: `data/analysis/gw3/inputs-MID.json` and `fixtures.json` in, `players-MID.json`
out; `--inputs`, `--fixtures`, `--out` override, `--format json` prints the
document. The table shows the top rows with their term breakdown, the coverage
line, and the ids that lack a cached element summary together with the
`summaries --ids` command that fetches them.

## 5. Changing the model

A retro correction to the arithmetic (a coefficient, an anchor, a blend
constant) is a change to `fpl/ep.py` and this file, shipped with tests, not an
instruction to an analyst. The judgment inputs stay where they are.
