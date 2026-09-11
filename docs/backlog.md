# Improvement backlog

Findings that fall outside an agent's remit during a gameweek cycle: a
model-arithmetic gap, a CLI or ledger shortfall, an agent-spec or
orchestration defect, an API data quirk. Agents append rows here and never act
on them in-cycle. Retro corrections (`C<n>` in data/retro/gw*.md) remain the
authoritative rules; every CODE correction is mirrored here so this file is the
single triage list.

## Writing a row (any agent, any cycle)

Append only, with a shell append — never a whole-file write, because the
player analysts run in parallel. The quoted `'EOF'` delimiter passes
apostrophes, backticks, `$` and `%` through literally:

```
cat <<'EOF' >> docs/backlog.md
| <GW> | <YYYY-MM-DD> | <agent> | <kind> | <finding> | <evidence path> | open |
EOF
```

A cell must not contain `|` or a newline; either breaks the table.

| Column | Content |
|---|---|
| GW | cycle in which the finding was made |
| Date | ISO date of the run |
| Agent | A1 data-collector · A2 fixture-analyst · A3-{GKP,DEF,MID,FWD} player-analyst · A4 squad-optimizer · A5 red-team · A6 retro-analyst · A7 finalizer · A8 plan-builder · A9 team-executor · ORCH |
| Kind | CODE (fpl/ep.py, fpl/calibrate.py arithmetic) · TOOL (CLI, schemas, ledger fields) · WORKFLOW (agent specs, CLAUDE.md, orchestration) · DATA (API quirks, snapshot quality) |
| Finding | one sentence: defect, evidence figure, proposed fix |
| Evidence | repo path the triage session should open |
| Status | `open` on write; edited only at triage to `shipped <sha>`, `rejected: <why>`, or `superseded by <C# or row>` |

The table must stay the last thing in this file so appends land in it.

## Triage (dedicated session, not part of a GW cycle)

Run from the repo root in a fresh session, before the next cycle when a CODE
row is open:

```
Triage docs/backlog.md. Read every row with status `open`, group rows that
share a fix, and for each group state: what changes (file, function), the
evidence for it, a rough cost, and whether it is a retro correction (C#) that
docs/ep-model.md §5 says must ship before the next cycle. Present the groups
as a menu; wait for my pick. For each picked group: TDD, `uv run pytest`,
regenerate derived files (`fpl ep --gw N --position POS`, `fpl calibrate
--gw N --round M`) and explain any diff, update docs/ep-model.md where the
formula changed, one commit per group in the repo's `<area>: <summary>`
style, no AI attribution. Then edit only the Status column of the rows you
touched. Never edit data/retro/gw*.md or data/decisions/; the
*-calibration.json ledgers and players-{pos}.json are derived and regenerated
by the commands above.
```

## Rows

| GW | Date | Agent | Kind | Finding | Evidence | Status |
|---|---|---|---|---|---|---|
| GW3 | 2026-09-03 | A6 | CODE | C9: unify the DefCon hit curve across DEF/MID/FWD, position entering only via the 10/12 threshold. Verify the premise first: `DEFCON_HIT_ANCHORS` already maps `dc90/threshold` through one table, so the GW2 gap (DEF bias −0.21 vs MID +0.26) may have another cause. | data/retro/gw2.md §Corrections; fpl/ep.py `defcon_hit_probability` | open |
| GW3 | 2026-09-03 | A6 | CODE | C10: `fpl calibrate` emits Σ P(DefCon hit) beside the realised count and carries price-band and uncertainty-tier aggregates in the cumulative block. Also raised by A3-MID and A3-DEF as the only way to produce C2's pooled sample. Until shipped the ≥£8.0m power test and the GW4 DefCon slope test cannot run. | data/retro/gw2.md §Corrections; fpl/calibrate.py `_defcon_sample`, `CumulativeStats` | open |
| GW3 | 2026-09-03 | A3-FWD | CODE | League-mean `bonus_per_start` is pooled from the cached shortlist, which is premium-skewed, giving 0.68 against the documented 0.35 fallback; every no-PL-history forward inherits a premium bonus rate. Weight the pool by minutes across the whole position or floor it at the fallback. | data/analysis/gw3/players-FWD.md §Escalations | open |
| GW3 | 2026-09-03 | A3-GKP | CODE | The saves term never divides out the keeper's prior club's defence, so there is no counterpart to `attack_mult`'s 1/ATT_club: a prior `saves90` embeds the previous club's leakiness and is then multiplied by the current club's λ_def. Trafford's Burnley-era 3.60/90 applied at Leeds is the live case. | data/analysis/gw3/players-GKP.md §Escalations | open |
| GW3 | 2026-09-03 | A3-FWD | CODE | v1 ignores sub appearances (Isidor: 9 pts and 1.39 xG in 49 bench minutes scored 10.52 EP6). Documented simplification; revisit when the minutes model gains a sub term. | data/analysis/gw3/players-FWD.md §Escalations | open |
| GW3 | 2026-09-03 | A2 | CODE | `base_lambda` 1.54/1.33 (2.87 goals per match) against observed league xG of 3.27 per match over rounds 1–2, about 12% low; if it persists every λ_att is low and every P(CS) high. Re-test at GW6 (n≈60) and raise the base rather than the ATT indices. | data/analysis/gw3/fixtures.md uncertainty table | open |
| GW3 | 2026-09-03 | A2 | TOOL | Attributing element-summary history rows to a club by the player's current bootstrap `team` mis-assigns transferred players (Ndiaye's round-1 xGC 1.96 landed on MCI against a true 0.65). Attribute by the row's `was_home`/`opponent_team` against the fixture list and add a guard in the ep/calibrate path. | data/analysis/gw3/fixtures.md §1 | open |
| GW3 | 2026-09-03 | A3-MID | DATA | `news_added` can carry a timestamp ahead of the clock (element 407, +15.7h), so it must not be used as a bare recency filter. | data/analysis/gw3/players-MID.md §Escalations | open |
| GW3 | 2026-09-03 | ORCH | TOOL | data/auth.json captured 2026-08-28 had expired by 2026-09-03; expect a re-capture every GW. `auth-check` could print the session's age or expiry (key names only) so the orchestrator can warn before the executor step. | data/executor/gw3/ | open |
| GW3 | 2026-09-03 | ORCH | WORKFLOW | Analysts filed model and code gaps under `## Escalations`, which is defined as freshness-gate candidates, and the retro-analyst does not read data/analysis, so findings never reached the agent that issues corrections. | agents/player-analyst.md; CLAUDE.md §Improvement backlog | shipped 0315b8e |
| GW4 | 2026-09-11 | A6 | CODE | C13 — calibrate must emit expected-vs-actual starts by p_start band in the round and cumulative blocks, and accept an --ids list whose round rows print regardless of error rank | data/retro/gw3.md §Corrections | open |
| GW4 | 2026-09-11 | A6 | TOOL | No expected-starts-by-p_start-band emission, so two consecutive rounds of start over-prediction (227.9 v 220, 225.9 v 217) cannot be attributed to a band | data/retro/gw3.md §Findings | open |
| GW4 | 2026-09-11 | A6 | TOOL | calibrate prints only the top-8 error tails, so a named non-squad player (rejected transfer target, unheld template player) has no readable round row for the LOW-4 and MED-E tests | data/retro/gw3.md §Findings | open |
| GW4 | 2026-09-11 | A2 | WORKFLOW | A2 rebuilds the club-xG and team-rating pipeline from scratch in a scratchpad every cycle because no build script is persisted, and the GW1 pure-prior reference frame had to be recovered by parsing the prior cycle's markdown table since data/analysis/gw1/fixtures.json was never written - the reference frame is load-bearing for every implied rating and is one transcription error from silently drifting | data/analysis/gw4/fixtures.md | open |
| GW4 | 2026-09-11 | A2 | DATA | bootstrap teams report played 0 and points 0 for all 20 clubs after 3 completed rounds while the position field carries what looks like a live league table, so any consumer trusting played/points reads a pre-season state that contradicts position | data/raw/gw4/bootstrap.json | open |
| GW4 | 2026-09-11 | A3-GKP | CODE | bonus_per_start is a per-start lumpy count but blends an unshrunk current sample at the minutes-derived w_prior, so 3 bonus-heavy starts put Tzolakis at 0.769/start vs the 0.214 GKP league mean — 4.9 of his 21.75 EP6, enough to rank him above Donnarumma and level with Raya; per-start counts need their own shrinkage, not the xG minutes weight | data/analysis/gw4/players-GKP.md | open |
| GW4 | 2026-09-11 | A3-FWD | TOOL | Retro C2 asks A3 to log the DefCon calibration sample every GW and re-test the slope at GW4, but no analyst file can emit it - the per-player prior dc90, ratio, v1 P(hit), realised DC and hit flag live in fpl/calibrate.py. The GW4 re-test is now due with no pooled sample to run it on; needs a calibrate-side emission before any A3 can discharge the correction | data/analysis/gw4/players-FWD.md (Retro compliance) | open |
| GW4 | 2026-09-11 | A3-FWD | TOOL | players --minutes emits minutes_by_round as a bare positional series, so a player whose element-summary holds fewer rounds than the season prints a short list (id 634 "27", id 640 "24") that positionally reads as GW1 rather than the round actually played. Pad to the rounds played or label each entry with its round | data/analysis/gw4/inputs-FWD.json | open |
| GW4 | 2026-09-11 | A3-MID | WORKFLOW | Call 1 line 4 surfaces last GW p_start/ep6/uncertainty but not p_start_gw, so every ramped player must be rebuilt from scratch instead of shifted one gameweek; the prior inputs-{pos}.json is the only source and is not in the prescribed reads | agents/player-analyst.md Call 1 | open |
| GW4 | 2026-09-11 | A3-MID | TOOL | players --minutes emits minutes_by_round with a variable round count and no round labels (Barcola "26", Bouaddi "8,14", others "90,90,90"), so a reader cannot tell whether the absent rounds lead or trail — a late signing and a dropped starter look identical | data/analysis/gw4/players-MID.md Minutes calls | open |
| GW4 | 2026-09-11 | A3-DEF | CODE | history_past records defensive_contribution as 0 for every season before 2024/25 because the stat did not exist; rates_from_seasons reads it as a genuine zero, so any player whose prior pool predates 2024/25 gets a near-zero dc90 prior and a near-zero P_map. Egan's prior lands at 1.07/90 against a realised 13.7/90. Fix: exclude pre-2024/25 seasons from the DefCon prior pool and fall back to the position league mean. 6 DEF rows affected at GW4; GKP/MID/FWD unchecked | data/analysis/gw4/players-DEF.md (Overrides) | open |
| GW4 | 2026-09-11 | A3-DEF | TOOL | retro C2's GW4 DefCon slope re-test is not executable: the calibration ledger's defcon block covers only the 15 squad players and carries minutes, value, threshold and hit, but not dc90_prior, the ratio to threshold, or the predicted P(hit) the test needs; pooled n is ~40 across GW1-3, not the ~250 C2 assumed. Fix: emit the per-player DefCon row over the whole scored pool with dc90_prior, ratio and predicted P(hit) | data/analysis/gw4/players-DEF.md (Retro compliance) | open |
| GW4 | 2026-09-11 | A4 | TOOL | C14 needs every candidate's EP on prior-only rates, but players-{pos}.json rates expose dc90_prior only (no xg90_prior, xa90_prior, bonus prior), so A4 must rerun fpl ep with prior_weight 1.0 overrides on every input row into scratch; suggest ep emit a per-row ep_total6_prior (or the prior rates) so the robustness reading is one column, not a second run | data/analysis/gw4/players-MID.json rates block | open |
| GW4 | 2026-09-11 | A5 | TOOL | Relayed my-team team value 99.6 equals the bootstrap now_cost sum, while the per-player selling prices sum to 99.4; unclear which field my-team prints as value, so the executor or data-collector should label the total as sell or purchase before the optimizer reads it | data/decisions/gw4/squad-proposal.md | open |
