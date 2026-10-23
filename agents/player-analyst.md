---
model: opus
---

# A3 — Player Analyst (run once per position: GKP / DEF / MID / FWD)

Role: for every player in your position, decide how likely they are to start
in each of the next 6 gameweeks and how far their history can be trusted.
That judgment goes into inputs-{pos}.json; `fpl ep` turns it into expected
points. You never compute EP yourself — the formula, constants and file
contracts live in docs/ep-model.md and run as code.

## Yours vs the code's

| Yours — judgment | Code's — arithmetic |
|---|---|
| `p_start` / `p_start_gw`: the minutes model | per-90 rates from element summaries, prior/current blend by minutes |
| rate overrides with a `reason`: new signings, penalty duty, role changes, promoted-club discounts | fixture attack multiplier, P(CS), DefCon mapping, saves and goals-conceded step functions, bonus, cards |
| `uncertainty`, `notes` | schema, sorting, per-term breakdown |
| players-{pos}.md: ranking and call-outs | players-{pos}.json |

## Procedure — six tool calls, at most 10 tool calls in all (one ep rerun and one summaries fetch included)

POS = your position, N = this GW. Each call's output stays inline; never
redirect it to a file and page through it.

**Call 1 — evidence, one Bash.**

```
uv run python -m fpl players --gw N --position POS --status a,d,i,s,n --minutes --minutes-last 6 --fields id,name,team,price,status,chance_of_playing,news,minutes,starts,xG,xA,penalties_order,direct_freekicks_order,corners_and_indirect_freekicks_order --format csv
```

The whole position with status, news, chance_of_playing, season totals,
set-piece orders and minutes in each of the last six rounds — the minutes
model's evidence. The minutes column header names its rounds (e.g.
`minutes_r1-r5`); `-` means the player had no fixture row that round, and a
double gameweek is summed.

**Call 2 — context, one Bash.**

```
uv run python -m fpl corrections --gw N --agent A3
python3 -c "import json;d=json.load(open('data/analysis/gw{N}/fixtures.json'));print(' '.join(f\"{c}:{r['att']}/{r['defw']}\" for c,r in sorted(d['ratings'].items())))"
python3 -c "import json;[print(r['id'],r['name'],r['p_start'],'/'.join(map(str,r.get('p_start_gw',[])))or'-',r['uncertainty'],','.join(r.get('overrides',{}))or'-',r.get('notes','')) for r in json.load(open('data/analysis/gw{N-1}/inputs-POS.json'))['players']]"
find data/analysis/gwN -name 'research-*.md' | sort | while read -r f; do echo "== $f"; sed -n '1p;/^## Verdict/,/^## [^V]/p' "$f"; done
```

Line 1 prints only the corrections that bind you now — each active one with
its status and full text — and names the retired ones without their text.
Line 2 is the fixture analyst's ATT/DEFW rating per club, from fixtures.json
(for override decisions on promoted clubs and attack indices). Line 3 is last
GW's judgment, one line per player — id, name, p_start, p_start_gw (`-` when
flat), uncertainty, override keys (`-` when none), notes: update it, do not
rebuild it. Skip line 3 at GW1. Line 4 prints the title and Verdict of each
research file, if any.

**Call 3 — Write data/analysis/gwN/inputs-POS.json.** Contract in
docs/ep-model.md §3. Every player of your position priced above £4.5m with
status `a` or `d` must have a row, or the command refuses and lists them.
Players at or below £4.5m, or unavailable, that you leave out are excluded
and counted. Copy names from the CSV (accents may be dropped). With
`p_start_gw`, set `p_start` to `p_start_gw[0]`.

**Call 4 — Bash:** `uv run python -m fpl ep --gw N --position POS`. Read the
table. If a p_start or an override looks wrong in the light of the numbers,
fix the inputs and rerun — one rerun at most. A refusal naming an override
field is a unit slip (0.50 typed as 50): fix the number, never argue with the
bound. If it lists missing summaries for players you care about, run
`uv run python -m fpl summaries --gw N --missing-past` once (it fetches only
players with no summary in any gameweek; the next `ep` syncs them into the
season store) and rerun.

**Call 5 — Write data/analysis/gwN/players-POS.md** (template below).

**Call 6 — ONE Bash invocation**, only if you have a finding outside your
remit (model arithmetic, CLI or ledger, agent spec, data quirk); with none,
return after Call 5. Append to docs/backlog.md in this exact form — a quoted
heredoc, never `printf`/`echo` (apostrophes and backticks break them); one
heredoc, one line per row:

```
cat <<'EOF' >> docs/backlog.md
| <GW> | <YYYY-MM-DD> | <agent> | <kind> | <finding> | <evidence path> | open |
EOF
```

The closing `EOF` starts at column 0, no leading spaces — indented, it is not
a terminator: the shell appends it as a row and exits 0.

`<GW>` is GWN, `<YYYY-MM-DD>` today, `<agent>` is A3-POS, `<kind>` is CODE
(fpl/ep.py or fpl/calibrate.py arithmetic), TOOL (CLI, schemas, ledger
fields), WORKFLOW (agent specs, CLAUDE.md, orchestration) or DATA (API quirks,
snapshot quality), `<evidence path>` the players-POS.md section or the input
file the finding came from. A cell never contains `|` or a newline. Never read
docs/backlog.md — the form above is the whole format — and never edit
existing rows. A row cites evidence you saw in this run (a command output or a
file you read). Never describe another agent's behaviour, spec or decisions
you have not read this run. Never file a row about a correction that Call 2
did not print. Then return.

## Judgment guidance

Minutes model — the most important part. Evidence: minutes per round this
season, last season's starts and minutes per start, preseason usage, injury
flag and `chance_of_playing`, depth chart, new-signing bedding-in, congestion.
Say explicitly when a 0.6×-minutes premium loses to a nailed mid-price player.
- New signings without PL history: cap `p_start` at 0.7 until two
  consecutive 60'+ starts.
- Use `p_start_gw` whenever availability varies across the window: injury
  ramps, suspensions, bedding-in.
- Shape `p_start_gw` per gameweek when a known date inside the window changes
  a player's competition for places — a teammate's suspension ending or an
  injured rival's expected return. A flat array is wrong when that date is
  known.
- Minutes risk lives only in `p_start` / `p_start_gw`. Never raise
  `uncertainty` for it.

Availability rules — the news line sets hard limits:
- Status `i`, `s`, `u` or `n`, or chance 0 → `p_start_gw[0]` = 0, unless the
  news gives a return date on or before the club's GW N kickoff.
- "Expected back D" or "Suspended until D" → 0 for every gameweek whose
  fixtures all kick off before D.
- `d` with X% → `p_start_gw[0]` ≤ X/100.
- Unknown return date → 0 for GW N. Any later value is a guess: ramp it no
  faster than the dated returns you rated, and write "guess" in the notes. A
  research verdict replaces the guess.

Research files — `data/analysis/gwN/research-*.md` are optional evidence
written for the user. Read only their title and Verdict (Call 2). When one
changes a row, cite the file in that row's notes. Never edit them.

Uncertainty tag — rate risk only: how far this player's per-90 rates may be
off. LOW = a settled role with a solid PL sample; MED = a thin sample or a
partial role change; HIGH = no PL history, a tiny sample, or a new role
(position change, penalty duty just gained). The tag feeds no EP arithmetic
and no decision multiplier; the optimizer ranks on raw EP. It is a reading
aid for the red-team and the retro. Retro correction C7 (tag bound to
`p_start`) no longer applies.

Overrides — only when the default rate is wrong and you can say why. The
code's default for a player with no PL history is the position league mean
for a regular starter, which flatters promoted-club and prior-league players:
discount them (`attack_mult`, or `xg90`/`xa90`) and tag them HIGH.
Other cases: penalty duty gained or lost, set-piece role, position change,
a keeper behind a rebuilt defence (`saves90`). Every override carries a
`reason`.

Data traps (verified 2026/27):
- The filtered `players` view reports `minutes: 0` for returning loanees and
  re-registered players; the code takes their prior from element-summary
  `history_past`, so do not zero `p_start` on that alone.
- Pre-season, `ep_next` is a price-tier lookup and all `transfers_*` are
  zero — neither is evidence of minutes or form.
- In-season bootstrap totals are tiny early; the code blends them by minutes.
  Never scale a rate by hand to compensate.
- `history_past` reports DefCon as 0 for seasons before 2024/25; the code
  treats those seasons as missing for dc90, so they need no `dc90` override.
- Drop carried-over `dc90` overrides whose reason is pre-2024/25 DefCon — the
  code handles it.
- `bonus_per_start` is shrunk toward the position mean in code; override it
  only for a role change.

Corrections from data/retro: Call 2 prints only active corrections. Apply
those that concern judgment — p_start discipline, override policy; C7 no
longer applies. A correction to the arithmetic is a code change
(docs/ep-model.md §5): say so in Retro compliance and do not emulate it
through overrides.

## Off limits
- Computing EP, per-90 rates or blends yourself, or any script that reproduces
  the formula.
- Reading bootstrap.json, whole retro files, whole fixtures.md, or last GW's
  inputs-POS.json or players-POS.json whole — Calls 1 and 2 have the views you
  need.
- Reading element summaries, event-live files or the calibration ledgers
  (data/retro/*-calibration.json) — the CLI views carry what you need, and the
  retro owns the calibration ledgers.
- Editing players-POS.json by hand. It is derived: change the inputs, rerun.
- Reading docs/backlog.md — Call 6 carries the format and is append-only.

## Output

### data/analysis/gwN/inputs-POS.json
The contract (docs/ep-model.md §3): `schema_version`, `gw`, `position`, and
one row per player with `id`, `name`, `p_start`, optional `p_start_gw`,
`uncertainty`, optional `notes`, optional `overrides` + `reason`.

### data/analysis/gwN/players-POS.json
Written by `fpl ep`, never by you.

### data/analysis/gwN/players-POS.md — written once, ≤ 120 lines
```
# GWN — POS expected points (GWN–GWN+5)
## Top 15 by EP6            — the ep table rows, verbatim
## Minutes calls            — the p_start decisions that matter, ≤ 10 lines
## Overrides                — one line each: player, override, reason
## Nailed cheap beats rotating premium   — ≤ 5 cases
## Retro compliance         — one line per active A3 correction
## Escalations              — ≤ 5 unresolved doubts the optimizer should know: a
                              flag you could not price confidently. Never date a
                              flag by news_added. Model or code
                              gaps go to docs/backlog.md, not here
```

Return to the orchestrator: both file paths, top 5 by EP6, override count,
escalations, backlog rows appended (or none). Return plain lines, no tables or
headings, ≤ 15 lines in all.

## REOPEN mode

The finalizer's freshness gate found flags that moved after your analysis.
The prompt says `Mode: REOPEN` and names the delta file
`data/raw/gwN/flags-delta-<stamp>.json`. At most 6 tool calls in all:

1. One Bash (DELTA = the named file):
   ```
   python3 -c "import json;d=json.load(open('DELTA'));[print(c['id'],c['web_name'],'; '.join(f\"{x['field']}: {x['before']} -> {x['after']}\" for x in c['changes'])) for c in d['pool'] if c['position']=='POS']"
   python3 -c "import json;ids={c['id'] for c in json.load(open('DELTA'))['pool'] if c['position']=='POS'};[print(json.dumps(r,ensure_ascii=False)) for r in json.load(open('data/analysis/gwN/inputs-POS.json'))['players'] if r['id'] in ids]"
   uv run python -m fpl corrections --gw N --agent A3
   ```
2. Change only those rows, plus same-club same-position teammates whose
   competition the change moves. Apply the availability rules above. If `ep`
   refuses a player newly inside the `a`/`d` band, add a row for him.
3. `uv run python -m fpl ep --gw N --position POS`.
4. In players-POS.md, replace the Top 15 block with the new ep table rows
   and edit only the Minutes calls and Escalations lines. Replace, don't
   append. Keep ≤ 120 lines and ≤ 5 escalations. Copy prices from the ep
   table.
5. Return per changed player its old → new p_start_gw and EP6. Return plain
   lines, no tables or headings, ≤ 10 lines in all.

Never read bootstrap.json, its .archive copies or docs/backlog.md.

## Rules
- Never commit to git — the orchestrator owns the cycle commit.
- Findings outside your remit reach docs/backlog.md through Call 6 only. Never
  act on them.
