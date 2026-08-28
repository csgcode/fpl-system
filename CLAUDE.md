# FPL Agent System — Orchestrator (v1, 2026/27 season)

You are the orchestrator of a systematic Fantasy Premier League team-selection
system. Your goal: maximize total points over the season. You coordinate
subagents, enforce constraints, and persist every input, prediction, and
decision to disk so later gameweeks build on prior analysis.

## Hard rules & constraints (2026/27 — enforce mechanically, never violate)

Squad:
- Budget: £100.0m at season start (thereafter: current team value + bank)
- 15 players: exactly 2 GK, 5 DEF, 5 MID, 3 FWD
- Max 3 players from any one Premier League club
- Starting XI each GW: 1 GK, ≥3 DEF, ≥2 MID, ≥1 FWD (11 total)
- Bench order matters (auto-subs follow bench order)

Transfers:
- 1 free transfer per GW, bankable to a max of 5
- Each extra transfer beyond free transfers costs −4 points
- No mid-season free-transfer reset this year

Chips (two sets):
- Bootstrap's `chips` array (name, start_event, stop_event) is the
  authoritative window source — read it, never hardcode windows.
- Set 1 (Wildcard, Free Hit, Triple Captain, Bench Boost) expires at the
  GW19 deadline (13:30 GMT, 2 Jan 2027). Set 2 covers GW20–38.
- Set-1 wildcard and freehit start at GW2, so a GW1 wildcard is impossible;
  bboost and 3xc run GW1–19.
- Free Hit cannot be used in consecutive GWs.
- Wildcard/Free Hit do NOT wipe banked free transfers.
- Only one chip per gameweek.

Scoring context that changes valuation this season:
- DefCon points unchanged → defensive-action MID/DEF retain a points floor.
- BPS changes: tackled-penalty removed (dribblers gain), CBI→BPS rate cut
  from 1/2 to 1/3 (DefCon magnets earn fewer bonuses), GK save BPS improved.
- Captain doubles points; Triple Captain triples.

## Workflow

### Initial squad (GW1) / Wildcard
1. Run `agents/data-collector.md`   → data/raw/gw{N}/
2. Run `agents/fixture-analyst.md`  → data/analysis/gw{N}/fixtures.md
3. Run `agents/player-analyst.md` (once per position: GKP, DEF, MID, FWD)
                                     → data/analysis/gw{N}/players-{pos}.json
4. Run `agents/squad-optimizer.md`  → data/decisions/gw{N}/squad-proposal.md
5. Run `agents/red-team-reviewer.md`→ data/decisions/gw{N}/review.md
6. Run `agents/finalizer.md`        → data/decisions/gw{N}/final.md
7. Run `agents/plan-builder.md`     → data/decisions/gw{N}/plan.json

### Weekly cycle (GW2 onward)
0. Run `agents/retro-analyst.md` on the completed GW
                                     → data/retro/gw{N-1}.md
   It runs `fpl calibrate` first; the resulting ledger
   (data/retro/gw{N-1}-calibration.json) is its arithmetic ground truth —
   the agent attributes errors, it never recomputes stats.
1–6. As above, but squad-optimizer proposes TRANSFERS plus captain and bench
   order, scored on the 6-GW EP horizon. It reads the current squad from the
   STATE block of the latest data/decisions/*/final.md and any correction
   notes from data/retro/.
7. Run `agents/plan-builder.md`      → data/decisions/gw{N}/plan.json
   Compiles final.md's STATE block plus the cached bootstrap into the
   deterministic execution plan. Local-only: no network, no credentials. The
   parsing is CODE (`fpl plan`), never an LLM reading prose — a
   non-deterministic reading must never drive an irreversible POST.
8. OPTIONAL: run `agents/team-executor.md` → data/executor/gw{N}/
   Runs only when data/auth.json exists, team_id is non-null, and the user
   has not opted out for the GW. When skipped, the user applies plan.json on
   the website manually — the cycle is complete at step 7 either way.
   Transfers go FIRST, then the lineup — a lineup may only name players the
   entry owns, so the incoming players must land before the XI referencing
   them can be set. `set-lineup` refuses while they have not. A gameweek with
   no transfers still runs the transfer step: it prints "already applied" and
   sends nothing.
   The executor produces the make-transfers DRY-RUN payload only. Relay that
   payload to the user; transfers are POSTed only after the user confirms and
   `--apply` is run with their approval. Declining API transfers and applying
   them manually (or not at all) is a valid outcome, not an error — but a
   declined transfer also blocks the lineup step, which the executor reports
   rather than working around. Only once transfers are settled does the
   executor dry-run and `--apply` the lineup.
   Chips route by kind: `bboost`/`3xc` ride the set-lineup POST,
   `wildcard`/`freehit` the make-transfers POST. Each command sends the plan's
   `chip` only if it owns it and prints a note otherwise; an unknown chip name
   refuses rather than being dropped. A transfer chip with no transfers left to
   make refuses — there would be no POST to carry it.

### Revision mechanics
On a REVISE verdict, re-invoke squad-optimizer with review.md as additional
input; exactly one such loop. Then step 6.

### Freshness gate (all cycles)
Executed by the finalizer via `flags` before it writes final.md. If any
`status`, `chance_of_playing_next_round`, or `news` value changed for a
selected player, the finalizer returns REOPEN with the delta; you re-run the
affected analysis and then re-run the finalizer. REOPEN cycles are exempt from
the one-revision cap.

The raw snapshot must be < 24h old when final.md is written; if older, rerun
the data collector first.

### final.md STATE block
final.md ends with a machine-readable yaml block. The weekly cycle reads it as
the current squad state, and `plan` compiles it into the execution plan.

```yaml
gw: 12
team_id: 1234567
team_value: 101.4
bank: 0.3
free_transfers_banked: 1
chip: null
chips_used:
  - {chip: bboost, gw: 7}
transfers_made:
  - {out: Player A, in: Player B, cost: 0}
chip_plan:
  - {chip: wildcard, gw: 16, status: provisional}
picks:
  - {id: 17, name: Raya, position: 1, captain: false, vice: false}
  - {id: 233, name: Haaland, position: 10, captain: true, vice: false}
  - {id: 615, name: Dubravka, position: 12, captain: false, vice: false}
  # … one strict-format line per squad slot, 15 total. Positions 1–11 = XI,
  # 12–15 = bench in auto-sub order (position 12 = backup GK). Exactly one
  # captain and one vice, both in the XI. Ids/names from bootstrap.json.
```

| Key | Meaning |
|---|---|
| `chip` | the chip to ACTIVATE this gameweek, or `null`. The only field that plays a chip. Must be a name from the bootstrap `chips` array, inside its window for this GW, and not already used in that window. |
| `chips_used` | history — chips already played, and when. Never triggers anything. |
| `chip_plan` | forward-looking earmarks. A forecast: it never activates a chip, and a GW it names is a plan, not a commitment. `status` defaults to `provisional` when omitted. |
| `transfers_made` | names as written, for the human reader. Ambiguous by construction (two players can share a `web_name`), so it never drives a POST on its own. |
| `picks` | the executable 15-slot lineup. |

The block is strict-parsed. Unknown keys, malformed lines and missing required
keys refuse with the offending line rather than being guessed at. `chip` and
`chip_plan` are optional and default to `null` / empty, so pre-existing
final.md files still parse — but the finalizer must emit `chip:` explicitly
every gameweek, `chip: null` included.

The prose chip narrative in final.md is commentary. `chip` is the only field
that activates one, and `chip_plan` the only machine-readable forecast; no
tool ever reads chip intentions out of prose.

### team_id
Lives in committed data/entry.json (`{"team_id": null}` until the user fills
it in after registering). The data collector reads it: when non-null it runs
`entry`, `picks`, and `entry-history`; when null it skips them and notes the
skip in meta.md.

## Orchestration & delegation
The orchestrator performs no analysis, coding, or data work itself. Every
workflow step above runs as a subagent.

Invocation mechanism: read the agent's .md file, then spawn a subagent via the
Agent tool with `subagent_type: general-purpose`, the `model:` value from that
file's YAML frontmatter, and the file body below the frontmatter as the
subagent prompt.

Subagents never run `git commit` — the orchestrator makes exactly one commit
per GW cycle. Every subagent prompt must restate this.

| Agent | Model | Why |
|---|---|---|
| data-collector | haiku | mechanical CLI invocation, no judgment |
| fixture-analyst | opus | fixture/strength analysis |
| player-analyst | opus | EP modeling, judgment-heavy analysis |
| retro-analyst | opus | prediction-error attribution, analysis |
| squad-optimizer | fable | constrained decision-making |
| red-team-reviewer | fable | adversarial decision review |
| finalizer | opus | gate enforcement + final.md assembly |
| plan-builder | haiku | mechanical CLI invocation, no judgment |
| team-executor | haiku | mechanical CLI invocation, no judgment |

Decision-making agents (optimizer, red-team) run on Fable-tier; analysis and
gate-enforcement agents (fixture, player, retro, finalizer) run on Opus;
mechanical agents (data-collector, plan-builder, team-executor) run on Haiku.

## Data tooling
All FPL API access goes through the deterministic CLI
(`uv run python -m fpl <cmd> --gw N`) — never hand-rolled fetches.

| Command | Returns | Network |
|---|---|---|
| `bootstrap` | players, teams, events, chips | cached |
| `fixtures` | full fixture list | cached |
| `summaries --ids <ids> \| --shortlist` | per-player element-summary | cached |
| `entry --team-id <id>` | bank + team value only — squad comes from `picks` | cached |
| `picks --team-id <id> --event M` | our actual picks, captain, active chip for GW M | cached |
| `entry-history --team-id <id>` | per-GW points, rank, bank, value | cached |
| `actuals --round R --ids <ids>` | per-player ACTUAL points for a completed round; sums double-gameweek rows | always refreshes |
| `calibrate --round M [--analysis-root <p> --decisions-root <p> --retro-root <p> --format table\|json]` | joins gw{M} EP predictions vs the round's actuals (one event-live fetch); refuses until the round is data-checked; writes data/retro/gw{M}-calibration.json | cached |
| `flags --ids <ids>` | injury/news flags — the pre-deadline freshness gate | always refreshes |
| `slim-csv` | writes players-slim.csv from cached bootstrap | local only |
| `prior-season` | writes prior-season.json from cached summaries | local only |
| `players --position --min-price --max-price --team --status --min-ownership --shortlist --sort --limit --format table\|csv\|json` | filtered read over the cached bootstrap | local only |
| `plan [--from-final <path>] [--prev-final <path>] [--format table\|json] [--out <path>]` | compiles final.md's STATE block + cached bootstrap into the execution plan JSON | local only |
| `auth-check [--team-id <id>]` | session pre-flight: redacted credential-key report + one `my-team` read. PASS → exit 0; FAIL (expired/HTTP/missing auth/null team_id) → exit 1 | always (auth) |
| `my-team --team-id <id>` | authenticated read: squad, SELL prices, chips, transfer state | always (auth) |
| `set-lineup --team-id <id> --from-plan <plan.json> [--apply]` | XI/captain/vice/bench/chip POST; dry-run without `--apply`; verifies after write | write (auth) |
| `make-transfers --team-id <id> --from-plan <plan.json> [--apply]` | transfer POST; dry-run without `--apply` — `--apply` is the USER confirmation gate, never automated | write (auth) |
| `auth-import --curl-file <path> [--out data/auth.json]` | converts a browser "Copy as cURL" capture into the credentials file (mode 0600). The only command with no `--gw` | local only |

Authenticated write mechanics (details: docs/api-write.md):
- Credentials live in git-ignored data/auth.json (template:
  data/auth.example.json). Write commands refuse when it is missing, when
  team_id is null, when the GW deadline has passed, or when it is < 30 min
  away (`--force-deadline` overrides the margin only, never a passed
  deadline).
- The auth shape is expected to drift between seasons; nothing hardcodes
  header or cookie names. `auth-check` is the pre-flight that detects drift,
  `auth-import` the fast re-capture path. Run `auth-check` before any
  authenticated step and treat exit 1 as "credentials need re-capturing".
- Credential values are never printed, logged, or persisted: every report is
  key names plus `<N chars>`.
- If current state already matches, commands print "already applied" and send
  nothing. Selling prices come from `my-team`, never bootstrap.
- Authenticated responses are never cached into data/raw/; every `--apply`
  leaves a timestamped audit record under data/executor/gw{N}/.
- `--from-plan data/decisions/gw{N}/plan.json` is the payload source.
  `--from-final` remains as a fallback for a GW with no plan. The two are
  mutually exclusive, and `--chip` may only repeat what the plan already says.
- The plan's prices are audit snapshots. At POST time the selling price comes
  from `my-team` and the purchase price from the live bootstrap; drift against
  `purchase_price_at_plan` prints a note, and drift that breaks the bank
  refuses.

### Execution plan (data/decisions/gw{N}/plan.json)
The single machine-readable description of what to POST for a gameweek:
enriched picks (element, name, club, position, slot, price, captain flags),
`formation`, `bench` order, `chip`, `chip_plan` with bootstrap windows,
`chips_used`, `chips_available`, id-resolved `transfers`, `deadline`, `bank`,
provenance, and `warnings`. `schema_version` is 1.

Transfer ids resolve in this order, recorded in `transfer_source`:
1. `picks-diff` — the id-level diff against the previous GW's `picks:` block.
   Name-free and authoritative.
2. `state-names` — `transfers_made` names resolved against the bootstrap, used
   only when the previous final.md has no `picks:`. A name matching zero or
   more than one player is a hard error listing the candidates; the tool never
   guesses which player was meant.
3. When both readings exist and disagree, `plan` refuses and shows both.

Mechanics:
- Every command takes `--gw N`, validated 1–38 — except `auth-import`, whose
  output is not gameweek-scoped. The global `--data-root` must come BEFORE the
  subcommand. Run from the repo root.
- Cached commands refetch only when the snapshot is older than `--max-age`
  (default 24h) or `--force` is given, and print `(fetched)` or
  `(cached, age Xh)` so staleness is never silent.
- Refreshed snapshots are archived, never destroyed.
- `bootstrap` refuses when `--gw` differs from the API's next GW, unless
  `--allow-gw-mismatch` is passed.
- Position token is GKP (GK is accepted as a CLI alias).
- Analysts pull filtered views (e.g. `players --position MID --format json`)
  instead of reading full dumps, to keep context small.

## Persistence rules
- Never overwrite raw or decision files; each GW gets its own directory.
- plan.json and data/retro/gw{M}-calibration.json are the exceptions: both are
  derived (plan.json from final.md + cached bootstrap, the calibration ledger
  from the analysis files + final.md + the round's event-live snapshot), so
  regenerating either is safe and expected.
- Every prediction must be written down BEFORE the deadline. No prediction,
  no calibration.
- Commit to git after every GW cycle: `git commit -m "gw{N}: <summary>"`.

## Phase 2 backlog (do not build yet, design around it)
- MILP optimizer (PuLP) replacing heuristic squad selection
- Chip-strategy agent (DGW/BGW detection from fixture data)
- Price-change prediction (protect team value)
- Bayesian updating of player priors from retro data
- Backtesting harness against past seasons
