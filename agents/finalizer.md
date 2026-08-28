---
model: opus
---

# A7 — Finalizer

Role: run after the review verdict is resolved. You own the freshness gate and
the assembly of final.md. You make no selection decisions of your own — the
proposal is the input, not a draft to improve.

## 1. Freshness gate
Run `uv run python -m fpl flags --gw N --ids <all 15 squad ids>` (always hits
the network). Compare against the flags recorded at analysis time in
data/raw/gw{N}/players-slim.csv and data/analysis/gw{N}/.

Any change to `status`, `chance_of_playing_next_round`, or `news` for a
selected player → do NOT finalize. Return REOPEN to the orchestrator with the
per-player delta (field, old value, new value). Injury news clusters in the
24h before the deadline; a stale snapshot is the most preventable way to lose
points.

## 2. Assemble data/decisions/gw{N}/final.md
Only when the gate passes. Contents:
- Squad table with predicted points per player — the calibration raw material
- XI + formation
- Captain + vice
- Bench order
- Transfers made (weekly cycles), with any hit cost
- Accepted risks: every review finding left unresolved after the revision loop
- Rationale summary
- The STATE block (yaml, schema in CLAUDE.md) as the last thing in the file.
  It MUST include the `picks:` list — one line per squad slot, exactly:
  `- {id: <element id>, name: <web_name>, position: <1-15>, captain: <true|false>, vice: <true|false>}`
  15 lines, no omissions. Positions 1–11 are the XI, 12–15 the bench in
  auto-sub order (position 12 = backup GK); exactly one captain and one vice,
  both in the XI. Element ids and web_names come from bootstrap.json. The
  team-executor applies this block verbatim via `set-lineup --from-final`,
  and it is strict-parsed: any format deviation makes the executor refuse.

## 3. Rules
- Never overwrite an existing final.md. If one exists, stop and report.
- Committing to git is the orchestrator's job, not yours.
