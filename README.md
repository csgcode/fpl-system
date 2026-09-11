# FPL Agent System v1 (2026/27)

Systematic, multi-agent FPL team selection with persistent state and a
calibration loop. Designed to run under Claude Code (CLAUDE.md is the
orchestrator prompt; agents/ are subagent prompts).

## Layout
```
CLAUDE.md              orchestrator: rules, constraints, workflow
agents/
  data-collector.md    A1  raw FPL API snapshots
  fixture-analyst.md   A2  6-GW difficulty ticker
  player-analyst.md    A3  expected points + minutes model (×4 positions)
  squad-optimizer.md   A4  squad/transfers/captain under constraints
  red-team-reviewer.md A5  adversarial review
  retro-analyst.md     A6  predicted-vs-actual calibration
  finalizer.md         A7  freshness gate + final.md assembly
  plan-builder.md      A8  compiles final.md into plan.json (deterministic)
  team-executor.md     A9  applies plan.json to the real team (write API)
docs/
  api-write.md         authenticated write path: credential capture, gates
fpl/                   deterministic data CLI package
  models.py            typed FPL API payloads (validation boundary)
  http.py              HTTP gateway (swappable for tests)
  api.py               FPL API endpoint calls; raw payload + source URL
  auth.py              git-ignored session credentials (data-driven schema)
  capture.py           browser "Copy as cURL" capture → credentials
  write.py             authenticated gateway + lineup/transfer write service
  state.py             final.md STATE block parsing + validation
  plan.py              execution-plan model, squad legality, transfer ids
  store.py             snapshot persistence: cache, archive-on-refresh
  service.py           fetch-if-stale orchestration, validate-before-persist
  repository.py        filtered player queries over cached snapshots
  __main__.py          CLI entry point (`python -m fpl`)
tests/                 unit tests for fpl/
pyproject.toml         package + dependency manifest
uv.lock                pinned dependency lock
.python-version        pinned interpreter version
data/
  entry.json           our FPL team_id (null until registered)
  auth.example.json    credentials template (fill into git-ignored data/auth.json)
  raw/gw{N}/           immutable API snapshots
  analysis/gw{N}/      fixture + player EP outputs
  decisions/gw{N}/     proposal, review, final (with predictions + STATE
                       block), plan.json (the POST source)
  executor/gw{N}/      audit records for applied lineup/transfer writes
  retro/gw{M}.md       calibration + correction rules for completed GW M
```
Each agents/*.md carries `model:` YAML frontmatter selecting its Claude Code
subagent tier.

## Invariants
- Predictions written before deadlines; raw/decision files never overwritten
  (a refreshed snapshot archives the previous one rather than destroying it).
- Snapshot < 24h old at final decision; the finalizer re-checks injury flags
  for all 15 picks before writing final.md, and returns REOPEN on any change.
- Every agent that predicts reads data/retro/ corrections first, where they
  exist (no retro exists at GW1).
- git commit after every GW cycle.

## Usage
- `uv sync` — install dependencies
- `uv run pytest` — run tests
- `uv run python -m fpl --help` — data CLI (run from the repo root; the global
  `--data-root` goes before the subcommand)
- `picks`, `entry-history`, and `actuals` back the retro loop: our actual
  picks for a GW, our per-GW results, and per-player actual points
- `plan` compiles a gameweek's final.md STATE block plus the cached bootstrap
  into `data/decisions/gw{N}/plan.json` — the deterministic, machine-readable
  description of what to POST (picks, formation, bench, chip, id-resolved
  transfers, deadline, warnings). Local-only: no network, no credentials.
  Transfers resolve from the previous gameweek's id diff where possible, and
  an ambiguous player name is a hard error, never a guess
- `my-team`, `set-lineup`, `make-transfers` are the authenticated write path
  (setup: docs/api-write.md). They take `--from-plan plan.json`; writes are
  dry-run by default; `--apply` executes, and for transfers it is the
  user-confirmation gate — never automated. Selling prices always come from
  the authenticated read and purchase prices from the live bootstrap, never
  from plan.json — see docs/api-write.md § 4b
- `uv run python -m fpl auth-import --curl-file curl-request` — turn a browser
  "Copy as cURL" capture of a `my-team` request into git-ignored
  `data/auth.json` (mode 0600). The only command with no `--gw`
- `uv run python -m fpl usage --gw N --list | --session <id> --inspect |
  --session <id> --start <ts> --end <ts>` — token usage and list-price cost
  of one Claude Code session window, from the transcripts under
  `~/.claude/projects`, into `data/cost/gw{N}/` (usage.md, usage.json,
  calls.csv). Local-only. `scripts/collect-usage.sh N` runs it headlessly via
  `agents/usage-collector.md` on the Claude Code login
- `uv run python -m fpl auth-check --gw N` — session pre-flight. Exit 0 prints
  PASS plus entry id, squad size, bank, value, free transfers and chips; exit
  1 means the credentials need re-capturing, so it gates a shell cycle:
  `uv run python -m fpl auth-check --gw N || echo "re-capture"`. Credential
  values never reach the terminal — reports are key names and `<N chars>`

## Usage (Claude Code)
- GW1/wildcard: "Run the initial squad workflow in CLAUDE.md."
- Weekly:       "Run the weekly cycle for GW{N}."
- Cost ledger:  "Run agents/usage-collector.md for GW{N}." (completed cycles)

## Phase 2 backlog
MILP optimizer (PuLP), chip-strategy agent (DGW/BGW), price-change
prediction, Bayesian prior updating from retro data, season backtesting.
