# Cycle usage ledgers

One directory per gameweek, written only by `uv run python -m fpl usage` from
the Claude Code transcripts of the session that ran that cycle. Derived data:
regenerating a directory is safe.

| File | Contents |
|---|---|
| `usage.md` | review copy: window, totals, by model, by stage, by agent, prompts, pricing and method |
| `usage.json` | the same, machine-readable (`schema_version` 1) |
| `calls.csv` | one row per API call with the token split, cost split and tools called |

Windows come from `usage --inspect`'s suggestion; `--end` is extended past the
cycle-commit turn when the prompt at the suggested end is the commit. GW1 and
GW2 predate the plan-builder and team-executor agents; GW3 includes both and
the retro of GW2.

Producing the next one: `scripts/collect-usage.sh N` (headless Claude Code) or
ask the orchestrator to run `agents/usage-collector.md` for GW N. Manual path:

```
uv run python -m fpl usage --gw N --list          # only sessions active after the last earlier-GW ledger
uv run python -m fpl usage --gw N --session <id> --inspect
uv run python -m fpl usage --gw N --session <id> --start <ts> --end <ts>
```
