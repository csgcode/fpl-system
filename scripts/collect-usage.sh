#!/usr/bin/env bash
# Headless Claude Code run of agents/usage-collector.md for one completed
# gameweek cycle. Uses the Claude Code login (subscription), not an API key.
#
#   scripts/collect-usage.sh 3        → data/cost/gw3/{usage.md,usage.json,calls.csv}
#
# The model may only run the `usage` CLI; every number is computed by code.
set -euo pipefail

gw="${1:?usage: $0 <gameweek>}"
cd "$(dirname "$0")/.."

# Agent body without its YAML frontmatter.
spec="$(awk 'body { print; next } /^---$/ { if (++fences == 2) body = 1 }' agents/usage-collector.md)"

claude -p "Collect the usage ledger for GW${gw}. Follow this agent spec exactly; N is ${gw}.

${spec}" \
  --model haiku \
  --allowedTools "Bash(uv run python -m fpl usage*)"
