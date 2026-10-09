# Cycle usage ledgers

One directory per gameweek, written only by `uv run python -m fpl usage` from
the Claude Code transcripts of the session that ran that cycle. Derived data:
regenerating a directory is safe.

| File | Contents |
|---|---|
| `usage.md` | review copy: window, totals, by model, by stage, by agent, prompts, pricing and method |
| `usage.json` | the same, machine-readable (`schema_version` 1) |
| `calls.csv` | one row per API call with the token split, cost split and tools called |

Windows are `usage --inspect`'s suggestion, used exactly as printed. It runs
from the human prompt before the cycle's first spawn to the first human
prompt after both the last cycle agent finished and the last `gw{N}:` commit,
so the commit turn is counted. A GW{N} retro or usage-ledger spawn belongs to
the next cycle's window. GW1 and GW2 predate the plan-builder and
team-executor agents; GW3 includes both and the retro of GW2. The GW4 ledger
predates this rule: its window ends at the prompt after the commit amend
(19:04:10Z), so it holds 2 calls more than the rule gives (239, $32.91,
against 237, $32.76).

Producing the next one: `scripts/collect-usage.sh N` (headless Claude Code) or
ask the orchestrator to run `agents/usage-collector.md` for GW N. Manual path:

```
uv run python -m fpl usage --gw N --list          # only sessions active after the last earlier-GW ledger
uv run python -m fpl usage --gw N --session <id> --inspect
uv run python -m fpl usage --gw N --session <id> --start <ts> --end <ts>
```
