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
fpl/                   deterministic data CLI package
  models.py            typed FPL API payloads (validation boundary)
  http.py              HTTP gateway (swappable for tests)
  api.py               FPL API endpoint calls; raw payload + source URL
  store.py             snapshot persistence: cache, archive-on-refresh
  service.py           fetch-if-stale orchestration, validate-before-persist
  repository.py        filtered player queries over cached snapshots
  __main__.py          CLI entry point (`python -m fpl`)
tests/                 unit tests for fpl/
pyproject.toml         package + dependency manifest
uv.lock                pinned dependency lock
.python-version        pinned interpreter version
data/
  raw/gw{N}/           immutable API snapshots
  analysis/gw{N}/      fixture + player EP outputs
  decisions/gw{N}/     proposal, review, final (with predictions)
  retro/gw{N}.md       calibration + correction rules
```
Each agents/*.md carries `model:` YAML frontmatter selecting its Claude Code
subagent tier.

## Invariants
- Predictions written before deadlines; raw/decision files never overwritten.
- Snapshot < 24h old at final decision; injury flags re-checked for all 15
  picks immediately before final.md.
- Every agent that predicts must read data/retro/ corrections first.
- git commit after every GW cycle.

## Usage
- `uv sync` — install dependencies
- `uv run pytest` — run tests
- `uv run python -m fpl --help` — data CLI

## Usage (Claude Code)
- GW1/wildcard: "Run the initial squad workflow in CLAUDE.md."
- Weekly:       "Run the weekly cycle for GW{N}."

## Phase 2 backlog
MILP optimizer (PuLP), chip-strategy agent (DGW/BGW), price-change
prediction, Bayesian prior updating from retro data, season backtesting.
