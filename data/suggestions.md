# User suggestions

Non-binding steers from the user to the squad-optimizer: a transfer to
consider, a player to hold or avoid, a chip timing, a structure or target to
move toward. The optimizer weighs each row against expected points and may
follow, defer or reject it, or keep a long-horizon steer open as `standing`
and honour it every cycle. Every disposition carries an EP6 delta or the rule
the suggestion breaks; the hard constraints and transfer rule in CLAUDE.md
are never overridden; a row never drives a POST on its own — decisions still
flow through `picks:`.

The disposition ledger lives in `## Suggestions` of
data/decisions/gw{N}/final.md. A row here is considered every cycle until the
ledger closes it, and ignored after that.

## Writing a row

Append a row; never edit or delete one. To retract, append a row whose
Suggestion cell is exactly `withdraw S<n>`; it fires the cycle it is first
read, whatever its From/Until GW. Rows are read once per cycle, at the
squad-optimizer's first run; a row added after that waits for the next
gameweek. A cell must not contain `|`, a newline or a triple backtick. A
malformed row (wrong column count, reused S#) is listed as malformed and not
disposed; re-append it under a new S#.

| Column | Content |
|---|---|
| S# | id, next unused number; never reused |
| Date | ISO date the row was written; provenance only |
| From GW | first GW to consider; blank = the next deadline |
| Until GW | last GW to consider, inclusive; blank = open until the ledger closes it |
| Suggestion | one sentence; `withdraw S<n>` closes an earlier row |

The table must stay the last thing in this file so appends land in it.

## Rows

| S# | Date | From GW | Until GW | Suggestion |
|---|---|---|---|---|
| S1 | 2026-09-11 |  |  | Ndiaye and Anderson are a weak midfield pair: Anderson is a defensive mid with a low ceiling and Ndiaye may not get enough minutes in a stacked midfield; move long-term to players who consistently score big |
| S2 | 2026-09-11 |  |  | Aim for 65+ expected points per GW for the team as a long-term target |
