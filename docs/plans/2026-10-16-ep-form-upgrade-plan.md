# EP model upgrade v2: decision record, backtest gate, current-form features, and a local season store

## Context

The user wants `fpl ep` to weigh current form: recent 3–5 GW performance, how consistently a player returns, over-performance against our own EP, and how hard his past fixtures were, all as deterministic code. The design was agreed with the user on 2026-10-16. Raw total points never become an EP input, because they count luck twice. A feature goes live only if it beats the current model on held-out past rounds, on MAE and on bias, by a margin that matters. Samples are small, so every feature is shrunk hard.

Plan v1 was reviewed by four reviewers (A determinism, B data fetching, C workflow, D correctness). The orchestrator's decision record (`01-integration-decisions.md`) is binding: where a report and the record disagree, the record wins. Where both are silent, this plan prefers D for code facts, B for data facts, C for process facts and A for determinism, and `## Changes from v1` says which it chose.

The work now has three parts that v1 did not have, alongside the model features:

1. **A decision record that cannot drift.** GW6's `players-*.json` were rewritten 36 minutes after the decision commit, before the deadline, and the GW6 calibration ledger scored the rewritten files. The record of what we predicted is now the commit that first adds `data/decisions/gw{M}/final.md`. From GW8 on, `fpl plan` also writes a write-once `predictions.lock.json`. `calibrate` scores the record, and `ep` refuses to overwrite a decided gameweek.
2. **Gate records.** Every backtest verdict is a machine artefact under `data/model/gates/`. Tests bind the shipped constants and the docs to those records, so no number is copied by hand.
3. **A local season store.** Immutable data is fetched once (final snapshots, a `fpl event-live` command, local `actuals`). A git-ignored SQLite file, derived from `data/raw`, gives as-of views to `ep`, the backtest and the agents. It is built as a parallel workstream (Phase S). The one change that alters the live cycle, the collector switch (S.10), waits for the user's go-ahead.

Agent specs change only where the reports showed an agent would otherwise meet new output with no rule: one sentence each in the retro-analyst (0.6), squad-optimizer and red-team (4.7) and player-analyst (6.3) specs, plus the conditional promoted-club sentence (2.6) and the collector switch (S.10).

This is a CODE change shipped outside the GW cycle (docs/ep-model.md §5). The target is the GW9 cycle.

## Changes from v1

| Area | What changed | Why (report) |
|---|---|---|
| Decision record | "Cycle commit" (first `gw{M}:` commit) replaced by the decision commit, the commit that first adds `data/decisions/gw{M}/final.md`. `cycle_commit` renamed `decision_commit`. | GW7's first commit 9017751 is a progress commit with no final.md; a REOPEN would make the old rule score stale files. Same shas for GW1–6 (A8, C-A1, D-0.3) |
| Freeze guard | v1 Decision 2's deadline-keyed `ep` guard dropped. New Task 0.6b: `ep` refuses to write the canonical `players-{pos}.json` once final.md exists. | The GW6 rewrite happened before the deadline (C-V3, D) |
| Prediction lock | New Task 0.9: `fpl plan` writes `predictions.lock.json` once. `calibrate` reads lock, then decision commit, then refuses. | No git in the retro's path from GW8 on (A8). How calibrate rebuilds rows from the lock is this plan's choice: the lock overlays `ep_gw[0]` and `p_start` on the rows on disk (record silent; A8's shape kept) |
| Drift output | One stdout `predictions:` line with a drift count; one WARNING line only when files changed; ledger gains `drifted`. | A9, record D1 |
| Retro eval | `check_validity` ignores `predictions_source`; files listed in Task 0.6. | C-A11, D-0.5 |
| Triage prompt | Whole fenced paragraph replaced in one edit; calibrate kept; the §8 pointer moves to Task 7.1. | Wrapped text, stale last sentence (C-A2, D-0.8) |
| Backtest data path | Reads disk, never `git archive`. Optional drift refusal against the decision commit. `--repo` replaced by global `--data-root`, `--analysis-root`, `--retro-root`. | `club-priors.json` is absent at every GW3–6 commit; disk reproduces the ledgers (D-1.3, B, first-pass F2) |
| `--data-root` | The backtest honours it (D said "state it is ignored"; the record says make it honour it). | Record D2 |
| Actuals location | `fpl event-live --gw 8 --round 7` runs from the WS worktree with `--data-root /Users/gokul/Dev/Personal/fpl-system/data/raw`, so the final snapshot lands at `MAIN/data/raw/gw8/event-live-e7.json`, where the GW8 retro's `calibrate` finds it cached and final. One fetch, ever; the backtest reads actuals from the data root, and there is no separate actuals root. Data files live only on main, so nothing conflicts. | B S.2; the fetch-once principle |
| Backtest lines | Built from `to_documents()` (3-dp), so unchanged players give d = 0 exactly; `error` asserted with `approx`. | D-1.4, D-c-8 |
| Gate | Five rules: CI on raw d with SE clustered by (round, club); bias slack; position slack; minimum effect ΔMAE ≤ −0.01; round wins ≥ M−1 of M. v1's "small gains will fail" claim replaced by the measured fact. | K=300 passes v1's rule 1 at −0.0043 (A1, D-1.5, D-c-4) |
| Gate tests | Each gate rule isolated by its own test with hand values. | v1's bias and position tests also failed the CI rule (D-1.5) |
| LORO test | Explicit per-round MAEs; picks `{3:"a",4:"a",5:"b"}`. | v1 left two folds unspecified (D-1.6) |
| Ship value | `ship_value()` in code: mode over folds, ties to the earlier grid entry, production forced first. | A2, D-1.6 |
| Gate records | `--record`, ordered manifest, `combined` gate, `fpl gates --render/--summary`, `tests/test_gate_records.py` replace every per-task `test_*_is_the_backtested_value`. | A1, A3, A12, A14, A16 |
| Slice gate | `--gate-slice promoted|no_history` with a computed `hypothesis` field drives the promoted-club sentence. | A13 |
| Floor sweep | `--sweep blend_floor` dropped. | Unidentifiable: max current minutes 540, the floor binds only past ~700 (D-2.1) |
| Phase 3 | Sort key `(round or 0, fixture)`; separate weighted/raw minutes; new `blend_on_effective_minutes` (default off); `current_totals` helper; reproduce-today compares documents. | D-3.2, D-3.4, D-c-7 |
| Phase 4 | `FixtureMeans` defaults; DGW test with `p60=0`; Task 4.2 overrides add `dc90 0`, `prior_weight 1.0`; tie-break inside `greedy_reference`, same-`out` pairs, `TIE_BREAK_LABEL = "tie-break move:"`; `P4_CALIBRATED`; LORO base rate; model digest guard (new Task 4.6b). | A4–A7, C-A4, C-A5, C-A9, D-4.1/4.2/4.5/4.6 |
| Phase 5 | Residuals re-scored with the current code via `backtest.score_round` (not ledgers); blank GW gives 0; `persistence` SE clustered by player; `test_no_persistence` uses alternating ±1. | F5, D-5.1, D-5.4, C-A12 |
| Phase 6 | Test seeds event-live e1 and e2; one stderr summary line; compact `share_flag`; Call 4 size golden test; one analyst sentence (v1 Decision 6 reversed). | D-6.3, A10, A15, C-A3 |
| Phase S | New: B's S.1–S.10, adjusted per the record. New S.11 (Track WB) moves the model consumers (1.3, 2.4, 4.3, 5.6, 6.3) onto the store once WS has merged. | Record D6–D8 require the store paths; grouping them keeps WB from waiting on WS |
| CLAUDE.md rows for WS commands | Land with WS in Task S.9, not in 7.2. | WS merges on its own schedule (C process) |
| Sequencing | Four worktrees, merge windows, merge freeze, gates serial via the manifest, register-style CLI wiring. | C-B1–B4, record D9 |
| Worked doc numbers | Marked example line checked by a test (Task 2.2). | A17; record silent, adopted because it is cheap and of the same kind as the gate render |
| `materialize` | Kept as v1 (works, verified). D's optional `read_at` not adopted. | D-0.4 marked it optional |
| Backlog kinds | TOOL for freeze, backtest, persistence and store rows. | D-7.3, record D9 |

## Facts verified while planning (read-only, 2026-10-16)

- Repo root: `/Users/gokul/Dev/Personal/fpl-system`. HEAD `9017751` `gw7: retro gw6, data, fixtures, player EP, wildcard proposal + review (decision pending)`. It is a progress commit: GW7's `players-*.json`, `squad-proposal.md` and `review.md` are in it, `final.md` is not.
- The working tree is dirty. Tracked and modified: `CLAUDE.md`, `agents/{data-collector,player-analyst,red-team-reviewer,retro-analyst}.md`, `docs/ep-model.md`, `evals/__main__.py`, `evals/harness/{freeze,live,transcript,workspace}.py`, `fpl/{__main__,calibrate,ep,service}.py`, and their tests. Untracked: `fpl/corrections.py`, `evals/player_analyst/`, `evals/retro_analyst/`, `evals/fixtures/{player-analyst,retro-analyst}/`, `tests/test_corrections*.py`, `tests/test_analyst_view_golden.py`, `tests/evals/test_player_analyst_*.py`, `tests/evals/test_retro_*.py`.
  - The live GW7 cycle already calls this uncommitted code (`fpl corrections`, `players --fields/--minutes-last`, calibrate's `squad misses`, `names_match` and the `p_start` warning in ep.py). A worktree cut from 9017751 would have specs that call missing commands.
  - So the user commits it, in three commits, before any worktree is created (see "What the user commits first"). It is committed, never stashed.
- Deadlines (UTC, from `data/raw/gw7/bootstrap.json` events): GW7 2026-10-17 10:00; GW8 2026-10-23 17:30; GW9 2026-10-31 11:00. GW7's last match kicks off 2026-10-19 19:00, so round 7 is data-checked about 20–21 Oct. GW8's last match is 25 Oct, so round 8 is data-checked about 26–27 Oct.
- Decision commits (the commit that first adds `data/decisions/gw{M}/final.md`; identical to v1's table):

  | GW | Decision commit |
  |---|---|
  | 1 | 9d3ba46 |
  | 2 | 0b8dbdf |
  | 3 | 82ad6da |
  | 4 | db2ab51 |
  | 5 | 571f5b0 |
  | 6 | b28927f |
  | 7 | none yet; the GW7 cycle is run by the user separately (outside this plan) and its decision commit lands on main when it finishes |

  The GW5 `correct record` commit b965a64 modifies final.md and never adds it, so it is never chosen.
- GW6 rewrite: decision b28927f at 2026-10-09 14:21 UTC; `ep:` commits 8307b53 and ae4b9e4 rewrote all four `data/analysis/gw6/players-*.json` at about 14:55–14:57 UTC, before the GW6 deadline (2026-10-10 10:00 UTC). A triage session did it under the current triage prompt. Backlog row "GW7 A6 TOOL calibrate squad XI predicted 53.80 v final.md 56.178" is the symptom.
- GW6 ledger re-scored from the b28927f files: squad `predicted_xi_total` 56.18, overall n 421, bias 0.254, MAE 1.632. All four gw6 players files differ from the commit.
- `inputs-{pos}.json` exist for GW3–GW7 only (`ep` moved into code in 07c8dcc). GW1–2 EP was LLM-computed, so the backtest covers GW3 onward.
- Disk-only baseline (current code; `data/analysis/gw{r}/inputs-*` and `fixtures.json`; `data/raw/gw{r}`; actuals `data/raw/gw{r+1}/event-live-e{r}.json`; no git) reproduces the ledgers:

  | Round | n | bias | MAE | Ledger |
  |---|---|---|---|---|
  | 3 | 426 | 0.034 | 1.552 | 426 / 0.039 / 1.556 |
  | 4 | 426 | 0.092 | 1.791 | MAE 1.783 |
  | 5 | 415 | 0.341 | 1.678 | MAE 1.681 |
  | 6 | 421 | 0.253 | 1.636 | identical |

  The only allow-missing ids: r3 MID 488 (I.Sangaré £4.9 a), r5 MID 131 (Baleba £4.9 d). The bootstrap differs from the one the analyst saw, so the backtest must allow every uncovered id.
- `git diff <decision commit> -- data/raw/gw{r} data/analysis/gw{r}/inputs-* data/analysis/gw{r}/fixtures.json` is empty for r = 3–6 (gw5 raw differs only in entry/picks files the model does not read). Only gw6 `players-*.json` drifted.
- `data/analysis/club-priors.json` was added in 855eb92, after every GW3–6 decision commit: `git archive 82ad6da data/analysis/club-priors.json` fails (rc 128). v1's materialize path was broken.
- Gate arithmetic on rounds 3–6 (n 1688, in-sample, K=300 against 600): ΔMAE −0.0043 (0.27% of MAE); naive SE 0.0020 (CI upper −0.0004, passes v1's rule 1); round-cluster SE 0.0017; (round, club)-cluster SE 0.0019; per-round ΔMAE −0.0023 / −0.0098 / −0.0046 / −0.0005 (4/4 wins); bias 0.178 → 0.187. K=1200: ΔMAE +0.0034, 0/4 wins. Under the v2 gate, K=300 fails rule 4 (minimum effect).
- Max current-season minutes at GW7 = 6 × 90 = 540, so `w_prior = K/(K+540)`: 0.53 at K=600, 0.36 at K=300. A floor of 0.1–0.3 binds only past ~700–2400 current minutes.
- Leakage: every `data/raw/gw{r}/players/summary-*.json` holds `history` rows up to round r−1 only (max round gw3→2 … gw7→6).
- Data facts from report B (all checked over cached data, no network):

  | # | Fact |
  |---|---|
  | V1 | Every summary `history` row for GW2–7 (9,791 player-rounds, 14 stat fields) equals the event-live stats of that round. A store built from event-live reproduces what `ep` saw. |
  | V2 | gw7 rows also match on 22 fields (adds red cards, own goals, pens, CBI, tackles, recoveries, xGC). |
  | V3 | Event-live gives the fixture id for every element, 0-minute players included (`explain[0].fixture`), but not the side or the club. |
  | V4 | Side rule, 100% correct on 2,753 rows: (1) the fixture's `stats[bps].h/.a` lists; else (2) {club in bootstrap gw r, club in bootstrap gw r+1} ∩ {team_h, team_a} has exactly one member. Rule (2) with gw r alone is wrong on 11 rows. |
  | V5 | `history_past` never changed for any of 632 players across 7 snapshots. |
  | V6 | Bootstrap season totals equal Σ event-live rounds exactly at gw3, gw5, gw7: a free detector for post-check stat corrections. |
  | V7 | `modified` is false on every event-live element (e1–e6) and summary row. |
  | V8 | No double gameweek yet. DGW handling is untested on real data. |
  | V9 | Every model-input snapshot (bootstrap, fixtures, players/*) in gw1–7 has `.meta fetched_at` before that GW's deadline. |
  | V10 | The retro's `actuals` force-refreshes summaries into the current GW's `players/` (gw7: 9 archived, byte-identical). |
  | V11 | Event-live lacks per-fixture xG/xA in a DGW; fixtures.json `stats` lack xG/xA too. |
  | V12 | `LiveStats` parses no `expected_assists`, `yellow_cards`, `expected_goals_conceded`, `red_cards`; `Fixture` parses no `stats` or scores. |
  | V13 | Player-analyst Call 1 at gw7 prints `no summary` for 93 players. |
  | V14 | `_league_mean` pools whichever summaries are cached; a store with every player's `history_past` would change it unless the pool is pinned. |
  | V15 | Runtime is not the problem (0.5 s against 0.2 s). The gains are network, disk, determinism and coverage. |
  | V16 | The eval cache-note parser matches `\bcached\b`, so `(cached, age 52.3h, final)` still parses as cached. |

- `MatchRecord` (`fpl/models.py`) does not parse `opponent_team`, although every raw row carries it with `was_home`, `kickoff_time` and `round`.
- `history_past.expected_goals` is 0 for every season before 2022/23.
- `fpl/fixture_ratings.py` imports `fpl/ep.py`, so `ep.py` must never import `fixture_ratings` or `backtest`. Opponent ratings come from the round's own `fixtures.json` `ratings`, which `build_predictions` already receives.
- Promoted clubs (`data/analysis/club-priors.json`): COV, HUL, IPS. `promoted` is a property on the loaded priors (no call). Analysts set `attack_mult` on 54–69 rows per round (range 0.65–1.15), for many reasons, not only promotion.
- `objective` already has `NEAR_TIE = 0.25` (XI/bench boundary pairs) and `REFERENCE_TOLERANCE = 0.05` (fpl/objective.py:33, :36, :392). The GW7 proposal hit the tolerance (backlog row "GW7 A4 TOOL `objective` greedy-reference tolerance …").
- `calibrate` already takes `--decisions-root`. `PlayerPrediction` has `extra="ignore"`, so new row keys need no calibrate change.
- `tests/conftest.py` makes the repo's `data/` read-only for tests. Tests write only under `tmp_path`; reading committed `data/` (the Call-4 golden test, `tests/test_gate_records.py`) is allowed.
- `evals/squad_optimizer/views.py` extracts `fpl/` per case commit but builds `fpl.objective.Row` with keyword arguments from the current code, so new `Row` fields need defaults.
- `players-{pos}.md` "Top 15 by EP6" is the `fpl ep` table copied verbatim. `tests/test_analyst_view_golden.py` budgets Calls 1–2, not the ep table.
- Tests that read the git-ignored `data/raw/**/.archive/` skip when it is absent, so a fresh worktree records a different baseline from main.
- The official FPL API serves only season totals (`history_past`) for earlier seasons. It has no per-match data for 2025/26.

## Guardrails

- No `git commit` by the executing session. The user commits, in the split given under "Commit split by stream", and the messages carry no AI attribution trailer.
- No network calls in tests. Tests use synthetic data from `tests/factories.py`, `tests/gitrepo.py` and write only under `tmp_path`; reads of committed `data/` are allowed (conftest blocks writes). Real-data runs of cached commands pass `--max-age inf`. The only network operations in this plan are the two marked data operations (`bootstrap --gw 8` and `event-live --gw 8 --round 7` into `MAIN/data/raw/gw8/`, Task 1.9 prerequisite), public endpoints with no credentials.
- Never read, print or touch `data/auth.json`.
- A past round is any round whose `data/decisions/gw{M}/final.md` exists. Never regenerate a past round's `data/analysis/gw{M}/players-*.json`. What-if runs write under the scratchpad (`--out`), never under `data/analysis/`.
- Never edit `data/retro/gw*.md`, `data/decisions/` (except the write-once lock written by `fpl plan` in the live cycle), `data/suggestions.md` or anything under `data/raw/`. Files that may be regenerated:
  - a calibration ledger (`data/retro/gw{M}-calibration.json`, Task 0.7);
  - `players-*.json` of a gameweek with no final.md;
  - the season store (`data/store/`), which is derived from `data/raw` and git-ignored.
- Gate records under `data/model/gates/` are written once. A re-run with `--force` archives the old record first.
- Never re-enable live evals and never run `evals` live modes. `uv run python -m evals replay …` (offline) and pytest are allowed. Do not re-freeze eval views.
- `docs/backlog.md` changes only by shell append (`cat <<'EOF' >> docs/backlog.md`, `EOF` at column 0) and by Status edits in Task 7.3, which runs on main after merge 2 as a declared triage session. Task 0.8 edits the triage prompt paragraph, which is header prose, not a row.
- No triage of the open calibrate.py rows (C10, C13, C17, C19) until merge 2. They then rebase onto `aggregate`/`grouped` (Task 1.2).
- No merge to main between a cycle's step 0 and its decision commit.
- TDD for every code task: write the test, run it and see it fail for the stated reason, implement, see it pass, then run the full suite at each phase end in that worktree.

## Decisions for the user

**Status (2026-10-16): the user accepted every recommendation below.** Decisions 1–7, 9 and 10 are settled as recommended. Decision 8 is settled as "not now": Task S.10 runs only after S.8's real-data parity passes and after a separate, explicit go-ahead from the user at that time; nothing else waits on it.

1. **Worktree layout.** Four worktrees, each cut from main after the user's three commits (today, 16 Oct; the in-flight GW7 cycle is not part of this plan):

   | Track | Worktree | Branch | Content |
   |---|---|---|---|
   | WA | `/Users/gokul/Dev/Personal/fpl-system-ep-freeze` | `ep-freeze` | Phase 0 |
   | WB | `/Users/gokul/Dev/Personal/fpl-system-ep-form` | `ep-form` | Phase 1–3, 4.2, 4.4, 4.5, 4.6b, 4.8, 5.3–5.7, 6.3, S.11, 7.1, 7.2; owns `fpl/ep.py` |
   | WC | `/Users/gokul/Dev/Personal/fpl-system-ep-modules` | `ep-modules` | pure modules 4.1, 4.3, 4.6, 4.7, 5.1, 5.2, 6.1, 6.2 |
   | WS | `/Users/gokul/Dev/Personal/fpl-system-ep-store` | `ep-store` | Phase S (S.1–S.10) |

   - **Recommend this layout.** The GW8 cycle keeps running on main's checkout. WA lands before the GW8 retro; WB lands after the GW8 decision.
   - Cost: each worktree needs `uv sync`, a copy of the ignored archives and its own pytest baseline (Task 0.1). WC merges into WB, not main, because 4.6/4.7 must ship with 4.2/4.4.
   - Alternative: one worktree for everything. Simpler, but WA could not land before the GW8 retro.
2. **Gate strictness.** The five-rule gate (Shared definitions). Measured fact: on rounds 3–6, K=300 passes v1's CI rule at ΔMAE −0.0043, 0.27% of MAE, because most players' d is zero and the paired CI is very tight. Rule 4 (ΔMAE ≤ −0.01) and rule 5 (wins ≥ M−1 of M rounds) stop such gains from shipping.
   - **Recommend the five-rule gate.** A feature ships only if it helps by at least 0.01 points per player-round and does so in almost every round.
   - Alternative: v1's three rules. K=300 would then ship on a 0.27% gain.
3. **Opponent rating used to adjust a past match** (Phase 3). Proposed: the ratings in round N's `fixtures.json`, the latest estimate available before the deadline. Two caveats go in §2: round-N ratings already include the adjusted match at weight about 1/10 by GW7 (mild self-influence, not leakage), and rounds 3–6 `fixtures.json` ratings were written by the LLM fixture analyst before `fixtures-rate` existed.
   - **Recommend round N's ratings.** The alternative (the rating as of the match's round) is noisier and needs every past round's ratings.
4. **Promoted-club sentence edit** (Task 2.6). If the `drop-promoted` gate record has verdict PASS and `hypothesis: supported`, replace the analyst sentence that tells analysts to discount promoted-club players (agents/player-analyst.md § Overrides, "discount them (`attack_mult`, or `xg90`/`xa90`) and tag them HIGH") with the text given in Task 2.6.
   - **Recommend making the edit when the record triggers it.** Otherwise analysts keep applying a discount that the evidence says loses points.
5. **Team-share flag reaches the analyst with one rule** (v1 Decision 6 reversed). Add one sentence to agents/player-analyst.md Call 4 (Task 6.3): act on a share flag only for a row where you set `xg90`, `xa90` or `attack_mult`; never file a backlog row per flag.
   - **Recommend adding the sentence.** Without it, a dozen flags per position become either override churn or backlog spam.
6. **Gate timing.** Gates run on rounds 3–7 as soon as round 7 has a final event-live snapshot: `fpl event-live --gw 8 --round 7` (Task S.2) run from the WS worktree with `--data-root MAIN/data/raw`, or the GW8 retro's own fetch on main, whichever comes first (about Tue 21 Oct). Either way the snapshot is `MAIN/data/raw/gw8/event-live-e7.json`. No merge of main is needed for data.
   - **Recommend shipping for GW9.** Shipping for GW8 would mean gating on four rounds and merging during the GW8 cycle. Waiting costs no gameweek: merge window 2 opens only after the GW8 decision anyway.
7. **Prediction lock** (Task 0.9). `fpl plan`, which the plan-builder already runs, writes `data/decisions/gw{N}/predictions.lock.json` once. No spec change. `calibrate` reads the lock first, then the decision commit.
   - **Recommend yes.** It takes git out of the retro's path from GW8 on and survives eval workspaces and non-git copies. Cost: about 40 lines and one CLAUDE.md persistence line.
8. **Collector switch** (Task S.10). The data collector stops refetching ~470 summaries a gameweek and runs `summaries --missing-past` then `store sync`. It changes `agents/data-collector.md`, `agents/retro-analyst.md`, `CLAUDE.md`, and the paused data-collector eval files (`evals/data_collector/checks.py` C15, `tests/evals/test_data_collector_spec_markers.py`, `tests/evals/test_data_collector_checks.py`).
   - **Needs your go-ahead.** Recommend doing it only after S.8's real-data parity passes and when you resume eval work. Until then the collector keeps fetching summaries and the store is built alongside.
9. **Deferred items: backlog rows only, not built here.** final-check EP-column equality; generated Top-15 and retro skeleton blocks (need analyst/retro spec changes); a `fpl predictions` filtered view and "optimizer and red-team never open players-*.json whole"; p4 goals-conceded/clean-sheet coupling and bonus mass; the saves DEFW_club double count; `_prior_seasons` pooling pre-2022/23 seasons with xG 0; a daily price series.
   - **Recommend accepting the list.** Each is appended in Task 7.3 for a later triage.
10. **Scope of "last season's data".** The official API has no per-match data for 2025/26, only season totals (`history_past`). The store makes this season's per-match data next season's prior, joined by the player `code`.
    - **Recommend accepting this scope.** Per-match data for earlier seasons would need a third-party source, which this plan does not add.

## Shared definitions (used by many tasks)

- **Paths.** `MAIN` = `/Users/gokul/Dev/Personal/fpl-system`. `WA`, `WB`, `WC`, `WS` = the worktree roots in Decision 1. `<SCRATCH>` = the absolute path of the session's scratchpad directory, substituted literally wherever it appears (it is not a shell variable). File paths inside a task are relative to the root of the worktree its Track names; commands run from that root.
- **Decision commit of GW M**: `git log --diff-filter=A --format=%H -- data/decisions/gw{M}/final.md | tail -1`, the commit that first adds final.md. A `correct record` commit modifies final.md and never adds it, so it is never chosen. Progress commits such as 9017751 are never the record. When final.md was never added there is no record. In an eval workspace the `baseline` commit adds final.md, so it is the record.
- **Decision record of GW M** (what `calibrate` scores):
  1. `data/decisions/gw{M}/predictions.lock.json` when it exists (GW8 onward, Task 0.9);
  2. else the `players-*.json` in the decision commit (GW1–7 backfill);
  3. else refuse, naming `--predictions-from worktree`.
- **Model variant**: a frozen `ModelConfig` (Task 1.1). Production constants are its defaults, so shipping a variant means changing a module constant. `ModelConfig.digest()` is the first 8 hex digits of the sha256 of the sorted field repr.
- **Backtest line**: one (player, round) pair, scored like the calibration ledger from exactly what production would write.
  - Rows come from `result.to_documents()` (3-dp), validated with `PlayerPrediction.model_validate({**doc, "position": pos})`.
  - `predicted` = `ep_gw[0]` (3-dp); `actual` = event-live `total_points`; `error` = actual − predicted (rounded to 3 dp by `build_report`); `started` = event-live `starts ≥ 1`.
  - Extra fields: `round`, `club`, `promoted`, `no_history`, and later `p4`.
- **Gate ("beats")**: lines are paired by (round, id). Per line, d = |e_variant| − |e_baseline|, computed from the line errors, never from rounded aggregates.
  - ΔMAE = mean d.
  - SE clustered by (round, club), CR0: SE = √(Σ_g (Σ_{i∈g} (dᵢ − ΔMAE))²) / n.
  - CI = ΔMAE ± 1.96·SE.
  - Per-round ΔMAE_r = mean d over round r; a round is a win when ΔMAE_r < 0.

  A variant beats the baseline iff all five hold:

  | Rule | Key in `reasons` | Condition | Constant |
  |---|---|---|---|
  | 1 | `ci` | CI upper bound < 0 | `GATE_Z = 1.96` |
  | 2 | `bias` | \|bias_variant\| ≤ \|bias_baseline\| + 0.05 | `GATE_BIAS_SLACK = 0.05` |
  | 3 | `position <POS>` | every position: ΔMAE_pos ≤ +0.02 | `GATE_POSITION_SLACK = 0.02` |
  | 4 | `effect` | ΔMAE ≤ −0.01 | `GATE_MIN_EFFECT = -0.01` |
  | 5 | `rounds` | round wins ≥ M − 1 of M rounds | — |

  For a sweep, the variant's lines are its leave-one-round-out (LORO) predictions (Task 1.6). The output always prints the per-round ΔMAE.
- **ship_value(picks, grid)**: the value to ship after a sweep. The mode of the LORO picks over folds (a tuple for a two-key grid); ties go to the earlier grid entry. The CLI puts each swept key's production value first in the grid, adding it when absent.
- **Gate record**: `data/model/gates/<name>.json`, written once by `fpl backtest --record <name>` (or `--record-all`). Fields: `schema_version` 1, `name`, `kind` (`model`, `policy`, `calibration`, `persistence`, `combined`), `argv`, `rounds`, `data` (roots, plus path and sha256 of each round's actuals snapshot), `decision_commits` (round → sha or null), `code` (`git rev-parse HEAD` and a dirty flag), `baseline_config`, `grid`, `picks`, `ship_value`, `comparison` (n, ΔMAE, SE, CI, per-round ΔMAE, round wins, baseline and variant aggregates, `by_position`, `slices`, optional `p4`), `verdict` (`PASS`/`FAIL`), `reasons`, optional `slice_verdict` and `hypothesis`, `recorded_at`.
  - `--force` moves an existing record to `data/model/gates/archive/<name>.<UTC stamp>.json` before writing.
- **Gate manifest**: `data/model/gates/manifest.toml`, an ordered list of `[[gate]]` tables with `name`, `kind` and `argv`. `fpl backtest --manifest <p> --record-all` runs each entry that has no record yet, in order. Each entry's baseline = the `baseline` record's `baseline_config` overlaid with the ship values of earlier `model` entries whose verdict is PASS and that are not in `combined.json` `reverted`; `DEFAULT_CONFIG` is never read by the manifest run, so a `--force` re-run after ship tasks have changed constants reproduces the same records. "Production value first" in a grid means that baseline's value. It then rewrites `combined.json` (archiving the previous one): all PASS ship values together against the `baseline` record's `baseline_config`. If `combined` fails, the last PASS entry is dropped from the overlay and `combined` re-runs, until it passes or nothing is left; dropped names go in `combined.json` `reverted`. `combined.json` `shipped_config` is the full `ModelConfig` that must ship. `--record-all --force` re-runs every entry.
- **Rounds available for gates**: 3..M, where M is the latest round that has inputs under `data/analysis/gw{M}/` and a **final** `event-live-e{M}.json` snapshot. Final means the `.meta` sidecar has `final: true` (Task S.1), or a cached bootstrap of gw ≥ M+1, fetched at or before the snapshot, shows event M `data_checked` (`data_checked` never reverts, so a check seen before the fetch proves the fetch came after it; a bootstrap fetched after the snapshot proves nothing). Today every `event-live-e{r}` passes: the collector's `bootstrap --gw r+1` precedes the retro's fetch and `calibrate` refuses to fetch before the check. The snapshot is looked for under the data root at `gw{M+1}/event-live-e{M}.json`. M = 6 today; 7 once round 7 is final (about 21 Oct).
- **Standard gate invocation** (from `WB`, once `MAIN/data/raw/gw8/event-live-e7.json` is final):

  ```
  uv run python -m fpl --data-root /Users/gokul/Dev/Personal/fpl-system/data/raw backtest --gw 8 --rounds 3-7 \
    --analysis-root /Users/gokul/Dev/Personal/fpl-system/data/analysis \
    --retro-root /Users/gokul/Dev/Personal/fpl-system/data/retro \
    --decisions-root /Users/gokul/Dev/Personal/fpl-system/data/decisions \
    --manifest data/model/gates/manifest.toml --record-all
  ```

- **Track codes**: `WA` freeze (Phase 0), `WB` model form (owns `fpl/ep.py`), `WC` pure modules, `WS` season store. "Parallel with X" means the two tasks can be built at the same time in different worktrees: they touch no common file and neither needs the other's output. "Depends on X" means X must be merged into this task's worktree first.

## Tasks

### Phase 0 — Preconditions and the decision record (WA)

### Task 0.1: Confirm a clean starting point and create the worktrees
- [ ] **Files:** none in the repo (checks and worktree creation).
- **Track:** WA (creates all four worktrees)
- **Depends on / parallel with:** depends on the user's three commits (see "What the user commits first"). Not on the GW7 cycle: that cycle runs on main separately, and the build happens in worktrees. Blocks everything else.
- **Effort:** S
- **Test:** each check must print what is stated, or the session stops and asks the user.
  - `git -C /Users/gokul/Dev/Personal/fpl-system status --porcelain -- fpl tests evals docs agents CLAUDE.md` prints nothing. The pending work is committed by the user, not stashed and not committed by this session.
  - The GW7 cycle is NOT a precondition and is not part of this plan. While `git log --diff-filter=A -- data/decisions/gw7/final.md` prints nothing, the GW7 cycle is still in flight on main: no merge to main (merge-freeze rule) until it prints a sha; the worktrees are unaffected.
  - `git -C /Users/gokul/Dev/Personal/fpl-system stash list` is noted in the session log. Do not pop it.
- **Implement:** for each row of Decision 1:
  1. `git -C /Users/gokul/Dev/Personal/fpl-system worktree add ../fpl-system-ep-freeze -b ep-freeze` (and `../fpl-system-ep-form -b ep-form`, `../fpl-system-ep-modules -b ep-modules`, `../fpl-system-ep-store -b ep-store`);
  2. `uv sync` in the new root;
  3. copy the ignored archives: `rsync -a --include='*/' --include='.archive/***' --exclude='*' /Users/gokul/Dev/Personal/fpl-system/data/raw/ <worktree>/data/raw/`.
- **Verify:** `uv run pytest -q` in each worktree passes with zero failures. Record each worktree's pass/skip count as that worktree's baseline. Main's counts are not comparable.

### Task 0.2: Git test helper
- [ ] **Files:** `tests/gitrepo.py` (create), `tests/test_gitrepo.py` (create).
- **Track:** WA
- **Depends on / parallel with:** 0.1. Parallel with all of WB, WC, WS.
- **Effort:** S
- **Test:** `test_commit_files_returns_the_sha_and_the_file_is_in_the_tree`:
  - `init_repo(tmp_path)`, then `commit_files(repo, {"a/b.json": "[]"}, "gw3: x")`;
  - returns a 40-hex sha;
  - `git -C repo show <sha>:a/b.json` prints `[]`.
- **Implement:**
  - `init_repo(path) -> Path`.
  - `commit_files(repo, files: dict[str, str | bytes | None], message: str) -> str`. Writing `None` as a value deletes the file in that commit.
  - Run git with `subprocess.run([...], check=True, capture_output=True, env=...)`. The env sets `GIT_CONFIG_GLOBAL=os.devnull` and `GIT_CONFIG_NOSYSTEM=1`.
  - Pass `-c user.name=test -c user.email=test@localhost -c commit.gpgsign=false -c init.defaultBranch=main`, so the user's config never applies and git prints no branch hint.
- **Verify:** `uv run pytest tests/test_gitrepo.py -q`

### Task 0.3: Find a round's decision commit
- [ ] **Files:** `fpl/decision_record.py` (create), `tests/test_decision_record.py` (create).
- **Track:** WA
- **Depends on / parallel with:** 0.2. Parallel with WB, WC, WS.
- **Effort:** S
- **Test:** build this history with `tests/gitrepo.py`:
  1. `gw6: progress` adds `data/analysis/gw6/players-MID.json`;
  2. `gw6: decision` rewrites `players-MID.json` (a REOPEN) and adds `data/decisions/gw6/final.md`;
  3. `ep: rewrite` changes `players-MID.json`;
  4. `gw6: correct record — x` modifies `final.md` and `players-MID.json`.

  Assert:
  - `decision_commit(repo, 6) == sha(2)`;
  - `decision_commit(repo, 7) is None`;
  - a repo with `players-MID.json` committed but no `final.md` returns `None`;
  - `decision_commit(repo, 6, decisions_rel="elsewhere/decisions")` looks under that path.
- **Implement:**
  - `decision_commit(repo: Path, gw: int, decisions_rel: str = "data/decisions") -> str | None`: the oldest sha of `git log --diff-filter=A --format=%H -- <decisions_rel>/gw{gw}/final.md`.
  - `repo_root(path: Path) -> Path` via `git -C <path> rev-parse --show-toplevel`, returned resolved. It raises `ValueError("<path> is not inside a git repository — pass --predictions-from worktree")` on failure.
- **Verify:** `uv run pytest tests/test_decision_record.py -q`

### Task 0.4: Extract files at a commit and detect drift
- [ ] **Files:** `fpl/decision_record.py` (modify), `tests/test_decision_record.py` (modify).
- **Track:** WA
- **Depends on / parallel with:** 0.3. Parallel with WB, WC, WS. WB merges `ep-freeze` after this task for the drift check in 1.3 and the code-drift column in 1.9.
- **Effort:** S
- **Test:**
  - `test_materialize_writes_the_commit_version`: after `materialize(repo, sha2, ["data/analysis/gw6"], dest)`, `dest/data/analysis/gw6/players-MID.json` holds the commit-2 content, not the working-tree content.
  - `test_drifted_names_changed_and_deleted_paths`: once the working-tree file is changed (and another is deleted), `drifted(repo, sha2, ["data/analysis/gw6"])` lists both, sorted. Unchanged files are not listed.
- **Implement:**
  - `materialize(repo, commit, paths, dest)`: run `git archive <commit> -- <paths>` (stdout bytes, no shell), then `tarfile.open(fileobj=io.BytesIO(out)).extractall(dest, filter="data")`.
  - `drifted(repo, commit, paths) -> list[str]`: `git diff --name-only <commit> -- <paths>`, sorted.
- **Verify:** `uv run pytest tests/test_decision_record.py -q`

### Task 0.5: The ledger records where its predictions came from
- [ ] **Files:** `fpl/calibrate.py` (modify), `tests/test_calibrate.py` (modify).
- **Track:** WA
- **Depends on / parallel with:** 0.1. Parallel with 0.2–0.4, WB (except 1.2, which also edits calibrate.py: WB takes 1.2 after merging `ep-freeze`), WC, WS.
- **Effort:** S
- **Test:**
  - `test_report_carries_predictions_source_and_drift`: `build_report(..., predictions_source="commit b28927f1a2b3", drifted=("data/analysis/gw6/players-MID.json",))` sets both fields.
  - `test_old_ledger_without_source_still_loads`: `load_report` on a JSON written without the keys yields `predictions_source == "worktree"` and `drifted == ()`.
- **Implement:**
  - `CalibrationReport.predictions_source: str = "worktree"` and `CalibrationReport.drifted: tuple[str, ...] = ()`.
  - `build_report(..., predictions_source: str = "worktree", drifted: Sequence[str] = ())`.
  - `SCHEMA_VERSION` stays 1: both fields are additive with defaults.
- **Verify:** `uv run pytest tests/test_calibrate.py -q`

### Task 0.6: `calibrate` scores the decision record
- [ ] **Files:** `fpl/decision_record.py` (modify: `record_predictions`), `fpl/__main__.py` (calibrate parser block, `run_calibrate`, `print_calibration`), `tests/test_calibrate_cli.py` (modify), `agents/retro-analyst.md` (one sentence), `evals/retro_analyst/live.py` (`check_validity`), `tests/evals/test_retro_cases.py` (modify).
- **Track:** WA
- **Depends on / parallel with:** 0.4, 0.5. Parallel with WB, WC, WS.
- **Effort:** M
- **Test:**
  - `test_calibrate_reads_predictions_from_the_decision_commit`, reusing `setup_round` in `tests/test_calibrate_cli.py` (it seeds `analysis/gw1` and runs `--gw 2 --round 1`):
    - `init_repo(tmp_path)`; commit `analysis/gw1/players-*.json` (Alpha `ep_gw[0]=3.0`) together with `decisions/gw1/final.md` as `gw1: decision`; then rewrite Alpha to 5.0 in an `ep: x` commit.
    - Run calibrate with `--analysis-root <tmp>/analysis --decisions-root <tmp>/decisions`.
    - The ledger's Alpha `predicted` == 3.0; `predictions_source` starts `commit `; `drifted == ("analysis/gw1/players-MID.json",)`.
    - Stdout has exactly one line starting `predictions: commit <sha12> (drift: 1 file)`.
    - Stderr has exactly one line `WARNING: 1 prediction file changed after decision commit <sha12> — calibrated the decision record: analysis/gw1/players-MID.json`.
  - `test_calibrate_prints_no_warning_without_drift`: no `ep: x` commit → stdout `predictions: commit <sha12> (drift: none)`, no WARNING.
  - `test_calibrate_refuses_without_a_decision_commit`: final.md never committed → exit 1, and the message names `--predictions-from worktree`.
  - `test_calibrate_still_refuses_an_unchecked_round_first`: with `checked=False`, the message still names "data-checked" (the commit lookup runs after that refusal).
  - `test_calibrate_worktree_mode_reads_the_files_on_disk`: `--predictions-from worktree` gives 5.0, `predictions_source == "worktree"` and stdout `predictions: worktree`.
  - Existing tests: the module's `run()` helper appends `--predictions-from worktree` when argv holds `calibrate` and not the flag. Existing assertions stay unchanged.
  - `tests/evals/test_retro_cases.py`: assert `"predictions: commit "` in the calibrate stdout of the workspace run.
- **Implement:**
  - Flag `--predictions-from {commit,worktree}`, default `commit`.
  - `decision_record.record_predictions(analysis_root, decisions_root, gw) -> RecordPredictions(predictions, source, drifted)`. In commit mode:
    - `repo = repo_root(analysis_root.resolve())`;
    - `rel = (analysis_root.resolve() / f"gw{gw}").relative_to(repo)`;
    - `sha = decision_commit(repo, gw, decisions_rel=str(decisions_root.resolve().relative_to(repo)))`, refusing when `None`;
    - `materialize(repo, sha, [str(rel)], tmp)` into a `tempfile.TemporaryDirectory()`; `load_predictions(tmp / rel)`;
    - `drifted(repo, sha, [str(rel)])` gives the drift list; `source = f"commit {sha[:12]}"`.
  - `run_calibrate` calls it after the `data_checked` refusal and passes `predictions_source` and `drifted` to `build_report`.
  - `print_calibration` prints `predictions: <source> (drift: none | k file[s])` (worktree mode: `predictions: worktree`) after its header line, above the `group … cumulative` block, so the retro's fences stay contiguous. One WARNING line on stderr only when the drift list is non-empty.
  - agents/retro-analyst.md, after the paragraph starting "`fpl corrections` prints the latest status table": add "`predictions:` names the decision record calibrate scored. A `changed after decision commit` warning means files on disk were changed after the decision; state it once in Findings and never attribute a miss to it."
  - `evals/retro_analyst/live.py` `check_validity`: pop `predictions_source` and `drifted` from both the written and the committed ledger before comparing (the regenerated gw6 ledger carries four drifted files a workspace run need not reproduce).
- **Verify:** `uv run pytest tests/test_calibrate_cli.py tests/test_calibrate.py tests/test_decision_record.py tests/evals/test_retro_cases.py tests/evals/test_retro_replay.py tests/evals/test_retro_spec_markers.py tests/evals/test_retro_checks.py -q`

### Task 0.6b: `ep` refuses to overwrite a decided gameweek
- [ ] **Files:** `fpl/__main__.py` (`run_ep`, ep parser block), `tests/test_ep_cli.py` (modify).
- **Track:** WA
- **Depends on / parallel with:** 0.6 (same file, serial). Parallel with WB, WC, WS.
- **Effort:** S
- **Test:**
  - `test_ep_refuses_the_canonical_file_once_final_md_exists`: seed `decisions/gw2/final.md`; `ep --gw 2 --position MID --decisions-root <tmp>/decisions` exits 1 with a message naming `final.md` and `--out`; nothing is written.
  - `test_ep_out_still_works_on_a_decided_gameweek`: with `--out <tmp>/x.json` it exits 0; `--prior-weight 1.0 --out <tmp>/p.json` (the red-team path) exits 0.
  - `test_ep_writes_before_final_md_exists`: no final.md → exit 0 and the canonical file is written.
- **Implement:** in `run_ep`, when `args.out is None` and `<decisions-root>/gw{N}/final.md` exists, raise `ValueError(f"gw{N} is decided (final.md exists): players-{pos}.json is the decision record; write a what-if with --out")`. Add `--decisions-root` (default `data/decisions`) to `ep`. A REOPEN is unaffected: the finalizer writes final.md only after the freshness gate passes.
- **Verify:** `uv run pytest tests/test_ep_cli.py -q`

### Task 0.7: Regenerate the GW6 ledger from b28927f (data operation, no test)
- [ ] **Files:** `data/retro/gw6-calibration.json` (regenerated in WA; it is a derived file).
- **Track:** WA
- **Depends on / parallel with:** 0.6. Lands on main in merge window 1 as its own commit, before the GW8 retro.
- **Effort:** S
- **Test:** the assert one-liner in Verify passes.
- **Implement:** from the WA root: `uv run python -m fpl calibrate --gw 7 --round 6 --max-age inf`.
  - Stdout shows `predictions: commit b28927f… (drift: 4 files)`, and one WARNING line names the four `data/analysis/gw6/players-*.json`.
  - Do not touch `data/retro/gw6.md`. Its prose quotes the old ledger, and that is history.
- **Verify:** `python3 -c "import json;d=json.load(open('data/retro/gw6-calibration.json'));assert d['predictions_source'].startswith('commit b28927f'),d['predictions_source'];assert abs(d['squad']['predicted_xi_total']-56.18)<0.01;o=d['overall'];assert (o['n'],round(o['bias'],3),round(o['mae'],3))==(421,0.254,1.632),o;print('ok')"` prints `ok`.

### Task 0.8: Stop the triage prompt from regenerating decided rounds
- [ ] **Files:** `docs/backlog.md` (the fenced triage paragraph only, lines 42–53 at HEAD, starting "Triage docs/backlog.md." and ending "by the commands above."), `docs/ep-model.md` (§5, one sentence).
- **Track:** WA
- **Depends on / parallel with:** 0.6b (the prompt names its behaviour). Parallel with WB, WC, WS.
- **Effort:** S
- **Test:** `uv run pytest tests/test_backlog_shape.py -q` still passes, and the Verify grep finds the new last sentence.
- **Implement:**
  - Replace the whole fenced paragraph in one edit (the old text wraps `fpl calibrate` across a line, so a one-line replace misses) with:

    ```
    Triage docs/backlog.md. Read every row with status `open`, group rows that
    share a fix, and for each group state: what changes (file, function), the
    evidence for it, a rough cost, and whether it is a retro correction (C#) that
    docs/ep-model.md §5 says must ship before the next cycle. Present the groups
    as a menu; wait for my pick. For each picked group: TDD, `uv run pytest`,
    regenerate derived files and explain any diff — `fpl ep --gw N --position POS`
    only for a gameweek with no final.md (the CLI refuses otherwise), and
    `fpl calibrate --gw N --round M` for any round (it scores the decision
    record, so regenerating a ledger is safe) — update docs/ep-model.md where the
    formula changed, one commit per group in the repo's `<area>: <summary>`
    style, no AI attribution. Then edit only the Status column of the rows you
    touched. Never edit data/retro/gw*.md or data/decisions/; the
    *-calibration.json ledgers are derived and regenerated by `fpl calibrate`;
    a decided round's players-{pos}.json is the decision record and is never
    regenerated.
    ```

  - Append to ep-model.md §5: "A decided round's players-*.json is the decision record. `calibrate` scores the predictions lock, or else the files in the commit that first added that round's final.md, and warns when the working tree differs." The sentence pointing at `fpl backtest` (§8) is added in Task 7.1, when §8 exists.
- **Verify:** `uv run pytest tests/test_backlog_shape.py -q && grep -n "is the decision record and is never" docs/backlog.md && tail -c1 docs/backlog.md | od -An -c`. The last command must print `\n`.

### Task 0.9: Prediction lock written by `fpl plan`
- [ ] **Files:** `fpl/decision_record.py` (lock writer and reader), `fpl/__main__.py` (`run_plan`, plan parser block; `run_calibrate` through `record_predictions`), `tests/test_decision_record.py`, `tests/test_plan_cli.py`, `tests/test_calibrate_cli.py`.
- **Track:** WA
- **Depends on / parallel with:** 0.6, 0.6b (same file, serial). Parallel with WB, WC, WS.
- **Effort:** M
- **Test:**
  - Existing tests: `tests/test_plan_cli.py`'s `run()` helper appends `--analysis-root <tmp>/analysis` when argv holds `plan` and not the flag, so no existing test hashes the repo's real `data/analysis/gw2/` into a lock (mirrors Task 0.6's helper rule).
  - `test_write_lock_records_hashes_and_rows`: for two seeded players files, `write_lock(analysis_dir, lock_path, gw)` writes `{"schema_version": 1, "gw": 2, "files": {"players-MID.json": "<sha256>", …}, "rows": {"1": [3.0, 0.9], …}}`, where each row is `[ep_gw[0], p_start]` as written in the file.
  - `test_write_lock_is_write_once`: a second call with changed files leaves the lock unchanged and returns a warning naming the lock; the same files return no warning.
  - `test_plan_writes_the_lock_next_to_final_md`: `plan --gw 2 --from-final <tmp>/decisions/gw2/final.md --analysis-root <tmp>/analysis --out <tmp>/plan.json` writes `<tmp>/decisions/gw2/predictions.lock.json`; with no players files it prints one stderr warning `no players-*.json for gw2 — predictions lock not written` and still exits 0; stdout is unchanged, so `--format json` output still parses.
  - `test_calibrate_prefers_the_lock`: a lock exists and one players file was changed after it. Calibrate (no git repo needed) gives the lock's `ep_gw[0]` and `p_start` for that file's ids, `predictions_source == "lock <sha256 of the lock file, 12 hex>"`, and `drifted` names the changed file.
  - `test_calibrate_refuses_a_lock_id_missing_on_disk`: a lock id absent from every players file → exit 1, message names the id and `--predictions-from worktree`.
- **Implement:**
  - `write_lock(analysis_dir, lock_path, gw) -> list[str]` (warnings). Writes only when the lock is absent.
  - `run_plan` gains `--analysis-root` (default `data/analysis`) and calls `write_lock(analysis_root / f"gw{N}", <from-final dir> / "predictions.lock.json", N)` after the plan is built. The plan-builder spec does not change.
  - `record_predictions` source order: lock → decision commit → refuse. With a lock: load the players files on disk; for each file whose sha256 differs from the lock, overlay `ep_gw[0]` and `p_start` from the lock on its rows (name, team, price and uncertainty come from disk) and add the file to `drifted`.
- **Verify:** `uv run pytest tests/test_decision_record.py tests/test_plan_cli.py tests/test_plan.py tests/test_calibrate_cli.py -q`, then `uv run pytest -q` (phase end, WA).

### Phase 1 — Backtest harness and gate records (WB)

### Task 1.1: `ModelConfig` with the blend constants and a digest
- [ ] **Files:** `fpl/ep.py`, `fpl/__main__.py` (`print_ep`: one line), `tests/test_ep.py`, `tests/test_ep_cli.py`.
- **Track:** WB
- **Depends on / parallel with:** 0.1. Parallel with WA, WC, WS.
- **Effort:** S
- **Test:**
  - `test_default_config_reproduces_the_production_constants`: `DEFAULT_CONFIG.blend_k == BLEND_EQUIV_MINUTES` and `DEFAULT_CONFIG.blend_floor == BLEND_PRIOR_FLOOR`.
  - `test_config_blend_k_changes_the_computed_prior_weight`: `build_predictions(..., config=replace(DEFAULT_CONFIG, blend_k=300.0))` for a player with two 90-minute current rows (`match_record_payload(minutes=90, round=1)` and `round=2`) and no `prior_weight` override gives `rates.prior_weight == pytest.approx(300/480)` (0.625).
  - `test_prior_weight_floor_from_config`: `prior_weight(10_000, k=600, floor=0.1) == 0.1`.
  - `test_config_digest_is_stable_and_changes_with_a_field`: `DEFAULT_CONFIG.digest() == ModelConfig().digest()`, it is 8 hex characters, and `replace(DEFAULT_CONFIG, blend_k=300.0).digest()` differs.
  - `test_documents_and_table_carry_the_model_digest` (test_ep_cli): every written row has `"model": DEFAULT_CONFIG.digest()`; the table's second line is `model <digest>`.
- **Implement:**
  - `@dataclass(frozen=True) class ModelConfig` with `blend_k: float = BLEND_EQUIV_MINUTES` and `blend_floor: float = BLEND_PRIOR_FLOOR`. Later tasks add fields.
  - `digest()`: `hashlib.sha256(repr(sorted(asdict(self).items())).encode()).hexdigest()[:8]`.
  - `DEFAULT_CONFIG = ModelConfig()`.
  - `prior_weight(current_minutes, *, k=BLEND_EQUIV_MINUTES, floor=BLEND_PRIOR_FLOOR)`.
  - Thread `config: ModelConfig = DEFAULT_CONFIG` through `build_predictions` → `_effective_rates`. `EpResult` keeps the config; `to_documents()` calls `_round_row(row, digest)` and `_round_row` adds `"model": digest` (it receives only an `EpRow` today).
  - Existing tests pass unchanged (calibrate ignores the new key).
- **Verify:** `uv run pytest tests/test_ep.py tests/test_ep_cli.py -q`

### Task 1.2: Public aggregate helpers in calibrate
- [ ] **Files:** `fpl/calibrate.py`, `tests/test_calibrate.py`.
- **Track:** WB
- **Depends on / parallel with:** 0.5 merged into WB (same file; merge `ep-freeze` into `ep-form` first). Parallel with WC, WS.
- **Effort:** S
- **Test:** `test_aggregate_and_brier_are_public`: for two `PlayerLine`s with errors +1 and −3, `aggregate(lines) == Aggregate(n=2, bias=-1.0, mae=2.0)`. For p_start 0.8 started and 0.3 not started, `brier(lines) == round((0.04+0.09)/2, 4)` (0.065).
- **Implement:** rename `_aggregate` → `aggregate`, `_grouped` → `grouped`, `_brier` → `brier`, and update the internal call sites. No behaviour change. `aggregate` rounds to 3 dp, so the gate never uses it for ΔMAE.
- **Verify:** `uv run pytest tests/test_calibrate.py tests/test_calibrate_cli.py -q`

### Task 1.3: Load one round from disk, leakage-checked
- [ ] **Files:** `fpl/backtest.py` (create), `tests/test_backtest.py` (create).
- **Track:** WB
- **Depends on / parallel with:** 1.1. The drift check needs 0.3/0.4 merged into WB (`git merge ep-freeze` after 0.4); write the other tests first. Parallel with WA, WC, WS.
- **Effort:** M
- **Test:** a `tmp_path` world, no git, with:
  - `raw/gw3/bootstrap.json` (two clubs TST and OPP, MID ids 1–2, id 2 priced 4.9 with status `a` and absent from inputs; event 3 deadline set);
  - `raw/gw3/fixtures.json`, `raw/gw3/players/summary-1.json` (history rounds 1–2), each with a `.meta` sidecar fetched before the deadline;
  - `analysis/gw3/{fixtures.json, inputs-GKP/DEF/MID/FWD.json}` (only MID has rows; the others have `players: []`);
  - `analysis/club-priors.json` marking OPP promoted;
  - `raw/gw4/event-live-e3.json` with a final sidecar.

  Assert:
  - `test_load_round_reads_disk`: `load_round(data_root=raw, analysis_root=analysis, actuals_root=raw, gw=3)` returns `RoundData` with `gw == 3`, `promoted == frozenset({"OPP"})`, `live` parsed, inputs keyed by position, `commit is None`.
  - `test_load_round_refuses_a_summary_holding_the_round_itself`: a summary row with `round: 3` raises `ValueError` naming `summary-1` and "leak".
  - `test_load_round_refuses_an_input_fetched_after_the_deadline`: a `summary-1` sidecar `fetched_at` after deadline 3 raises, naming the file and the deadline.
  - `test_load_round_refuses_without_actuals`: no event-live file raises, naming `<raw>/gw4/event-live-e3.json`.
  - `test_load_round_refuses_non_final_actuals`: a sidecar without `final` and no later bootstrap showing event 3 `data_checked` raises, naming "not final".
  - `test_load_round_accepts_actuals_checked_by_an_earlier_bootstrap`: no `final` key, but `raw/gw4/bootstrap.json` fetched before the snapshot shows event 3 `data_checked` → loads.
  - `test_load_round_refuses_actuals_fetched_before_the_check`: the only bootstrap showing event 3 `data_checked` was fetched after the snapshot → refuses, naming `fpl event-live --gw 4 --round 3 --force`.
  - `test_load_round_refuses_drift_from_the_decision_commit` (git, `tests/gitrepo.py`): commit the world plus `decisions/gw3/final.md` as `gw3: decision`, then change `analysis/gw3/inputs-MID.json` → raises naming that path; with `drift_check=False` it loads.
- **Implement:**
  - `@dataclass(frozen=True) class RoundData`: `gw, commit, deadline, bootstrap, summaries, fixtures, inputs: dict[Position, InputsDocument], live: EventLive, promoted: frozenset[str]`.
  - `load_round(*, data_root, analysis_root, actuals_root, gw, decisions_root=None, drift_check=True)` (`actuals_root` is a test seam; the CLI always passes the data root — there is no separate actuals root):
    - `SnapshotStore(data_root)`; `load_cached_bootstrap` and `load_cached_summaries` (bootstrap ids of every position + inputs ids) for gw r;
    - `ep.load_inputs` and `ep.load_fixtures` from `analysis_root/gw{r}`;
    - `promoted = fixture_ratings.load_priors(analysis_root / "club-priors.json").promoted` (a property; no call);
    - actuals from `actuals_root/gw{r+1}/event-live-e{r}.json`, final per Shared definitions;
    - leakage: every summary's max `history.round` < r; every model-input sidecar (`bootstrap.json`, `fixtures.json`, `players/*`) has `fetched_at` < deadline r (`SnapshotStore.fetched_at`);
    - drift: when `drift_check` and `analysis_root` is inside a git repo, `sha = decision_commit(repo, r, decisions_rel)` and `drifted(repo, sha, [raw/gw{r}/bootstrap.json, raw/gw{r}/fixtures.json, raw/gw{r}/players, analysis/gw{r}/inputs-*.json, analysis/gw{r}/fixtures.json])` must be empty, else refuse naming the files. Outside a repo, skip with one warning. `commit` = sha or `None`.
- **Verify:** `uv run pytest tests/test_backtest.py -q`

### Task 1.4: Score a round under a variant
- [ ] **Files:** `fpl/backtest.py`, `tests/test_backtest.py`.
- **Track:** WB
- **Depends on / parallel with:** 1.3. Parallel with WA, WC, WS.
- **Effort:** M
- **Test:**
  - `test_score_round_matches_documents_and_live`: on the Task 1.3 world, `score_round(data, DEFAULT_CONFIG)` returns lines where Alpha's `predicted` == `build_predictions(...).to_documents()[0]["ep_gw"][0]` (3-dp), `actual` == the live `total_points`, and `error == pytest.approx(actual − predicted, abs=5e-4)`.
  - `test_score_round_scores_despite_coverage_gaps`: the uncovered £4.9m id 2 does not refuse; the result's `warnings` names it.
  - `test_lines_carry_slices`: each line has `round`, `club`, `promoted` (club in `data.promoted`) and `no_history` (`doc["rates"]["prior_source"] == "league_mean"`).
  - `test_unchanged_player_gives_zero_difference`: a player whose `prior_weight` is overridden scores the same `predicted` under `blend_k=600` and `blend_k=300`, exactly (`==`).
- **Implement:**
  - `class BacktestLine(PlayerLine)` adds `round: int`, `club: str`, `promoted: bool`, `no_history: bool`, `p4: float | None = None`.
  - `score_round(data, config, *, inputs_policy="keep") -> RoundScore(lines, warnings)`:
    - per position with rows: `allow_missing` = every bootstrap id of that position with `now_cost > ep.COVERAGE_PRICE_FLOOR_TENTHS` and status in `ep.COVERAGE_STATUSES` that is absent from inputs (the same constants `_check_coverage` uses, so the rule cannot drift);
    - `result = build_predictions(..., config=config, allow_missing=allow_missing)`;
    - `docs = result.to_documents()`; `PlayerPrediction.model_validate({**doc, "position": pos})` for each;
    - `calibrate.build_report(predictions, data.live, match_round=r).players`;
    - `BacktestLine(**line.model_dump(), round=r, club=line.team, promoted=…, no_history=…)` with `no_history` from the matching doc.
- **Verify:** `uv run pytest tests/test_backtest.py -q`

### Task 1.5: Compare a variant with the baseline (five-rule gate)
- [ ] **Files:** `fpl/backtest.py`, `tests/test_backtest.py`.
- **Track:** WB
- **Depends on / parallel with:** 1.4. Parallel with WA, WC, WS.
- **Effort:** M
- **Test** (synthetic `BacktestLine`s; `reasons` keys are the part before the first `:`):
  - `test_compare_reports_paired_delta_and_gate`: round 3; MID ids 1, 2 in club TST, DEF ids 3, 4 in club OPP; baseline errors [2, −2, 4, −4], variant halved [1, −1, 2, −2]. d = [−1, −1, −2, −2].
    - `delta_mae == -1.5`; `se == pytest.approx(math.sqrt(2)/4)` (clusters (3,TST) sum +1.0, (3,OPP) sum −1.0);
    - `ci == pytest.approx((-1.5 - 1.96*math.sqrt(2)/4, -1.5 + 1.96*math.sqrt(2)/4))` (−2.193, −0.807);
    - `round_deltas == {3: -1.5}`, `round_wins == (1, 1)`;
    - `beats is True`, `reasons == ()`;
    - `by_position` holds n, bias and MAE for each reading; `slices` holds `promoted` and `no_history`.
  - `test_gate_fails_on_ci_only`: round 3, two MID lines in different clubs; baseline errors [4, 0.1], variant [1, 3.0]. d = [−3, 2.9], ΔMAE −0.05; bias 2.05 → 2.0; reasons keys == `["ci"]`.
  - `test_gate_fails_on_bias_only`: round 3, four MID lines in four clubs; baseline [2, −2, 2, −2], variant [1.06, −0.94, 1.06, −0.94]. ΔMAE −1.0, SE 0.03, bias 0 → 0.06; reasons keys == `["bias"]`.
  - `test_gate_fails_on_position_only`: round 3, each line its own club; 20 MID lines baseline ±2 alternating → variant ±1; 2 DEF lines baseline [1, −1] → variant [1.05, −1.05]. ΔMAE = −19.9/22 (−0.9045); DEF ΔMAE +0.05; reasons keys == `["position DEF"]`.
  - `test_gate_fails_on_effect_only`: round 3, 100 MID lines baseline ±2 alternating, variant ±1.995. d = −0.005 everywhere (SE 0); reasons keys == `["effect"]`.
  - `test_gate_fails_on_round_wins_only`: each line its own club, all MID. Round 3: 10 lines baseline ±2 → variant ±1 (d −1). Rounds 4 and 5: 10 lines each baseline ±1 → variant ±1.01 (d +0.01). ΔMAE = −9.8/30 (−0.3267); round wins (1, 3); reasons keys == `["rounds"]`.
  - `test_compare_refuses_unpaired_lines`: a line present in only one side raises `ValueError`.
- **Implement:**
  - `Comparison` dataclass: `n`, `baseline: Aggregate`, `variant: Aggregate` (from `calibrate.aggregate`, display only), `delta_mae`, `se`, `ci: tuple[float, float]`, `round_deltas: dict[int, float]`, `round_wins: tuple[int, int]`, `by_position`, `slices`, `beats: bool`, `reasons: tuple[str, ...]`.
  - Constants `GATE_Z = 1.96`, `GATE_BIAS_SLACK = 0.05`, `GATE_POSITION_SLACK = 0.02`, `GATE_MIN_EFFECT = -0.01`.
  - Pair on `(round, id)`. ΔMAE, SE and per-round values from raw d. Bias for rule 2 is the unrounded mean error. Reason strings: `ci: upper +0.xxx ≥ 0`, `bias: |b_v| x.xxx > |b_b| x.xxx + 0.05`, `position DEF: ΔMAE +0.xxx > +0.02`, `effect: ΔMAE −0.xxxx > −0.01`, `rounds: won k of M, need M−1`. The p_start Brier is not part of `Comparison` (it is identical for every variant).
- **Verify:** `uv run pytest tests/test_backtest.py -q`

### Task 1.6: Leave-one-round-out selection and `ship_value`
- [ ] **Files:** `fpl/backtest.py`, `tests/test_backtest.py`.
- **Track:** WB
- **Depends on / parallel with:** 1.5. Parallel with WA, WC, WS.
- **Effort:** S
- **Test:**
  - `test_loro_picks_per_fold_and_scores_the_held_out_round`: grid values `["a", "b"]`, equal n per round, per-round MAE a: r3 2.0, r4 2.0, r5 1.0; b: r3 1.0, r4 1.5, r5 2.0.
    - fold 3 trains on 4, 5 (a 1.5, b 1.75) → a; fold 4 trains on 3, 5 (a 1.5, b 1.5, tie) → a; fold 5 trains on 3, 4 (a 2.0, b 1.25) → b;
    - `picks == {3: "a", 4: "a", 5: "b"}`;
    - the CV lines are round 3 and 4 lines from a and round 5 lines from b.
  - `test_ship_value_mode_then_grid_order`: `ship_value({3: "a", 4: "a", 5: "b"}, ["a", "b"]) == "a"`; `ship_value({3: "a", 4: "b"}, ["b", "a"]) == "b"`; two-key values are tuples and compare the same way.
- **Implement:**
  - `cross_validate(lines_by_value: dict[str, list[BacktestLine]]) -> tuple[list[BacktestLine], dict[int, str]]`, dict order = grid order. Selection by pooled MAE over the training rounds; ties go to the earlier grid entry.
  - `ship_value(picks, grid)`.
  - Docstring note: a fold trains on later rounds for an earlier held-out round. That is acceptable for a hyper-parameter, and LORO measures the selection procedure, not the exact constant.
- **Verify:** `uv run pytest tests/test_backtest.py -q`

### Task 1.7: `fpl backtest` command
- [ ] **Files:** `fpl/backtest.py` (`register`, `run`), `fpl/__main__.py` (one `register` call in `build_parser`, one dispatch line in `main`), `tests/test_backtest_cli.py` (create).
- **Track:** WB
- **Depends on / parallel with:** 1.6. Parallel with WA, WC, WS (WS and WC also add register calls; each is one line, so merges stay trivial).
- **Effort:** M
- **Test**, on a `tmp_path` world with rounds 3 and 4 seeded as in Task 1.3:
  - `main(["--data-root", raw, "backtest", "--gw", "5", "--rounds", "3-4", "--analysis-root", analysis, "--no-drift-check"])` exits 0 and prints:
    - `rounds 3-4 · drift check: off`;
    - a per-round baseline table with columns `round n bias MAE`;
    - a `baseline` row with n, bias and MAE, and one row per position.
  - With `--set blend_k=300` it prints a `variant blend_k=300` line, a `per-round ΔMAE: 3 …, 4 …` line and `gate: PASS` or `gate: FAIL — <reasons>`.
  - `test_sweep_output_is_compact`: `--sweep blend_k=300,450 --cv` prints `LORO picks: 3→…, 4→…`, `ship: blend_k=…` and a gate line, the grid starts with production 600 (added), and the output has at most `configs + 6` lines (`configs` = 3).
  - `test_sweep_parses_none_and_bool`: `--sweep half_life_matches=none,2` and `--sweep opponent_adjust=false,true` parse by `ModelConfig` field type (add these fields as test-local or wait for Task 3.4; until then, test with `blend_k` and a dummy optional-float field in a test `ModelConfig` subclass).
  - `--set nope=1` exits 1 and lists the valid keys (the `ModelConfig` field names).
  - `--rounds 3-5 --gw 5` exits 1: "round 5 is not before --gw 5".
  - `--format json` prints one parseable document with the comparison and per-round values.
  - Nothing is written unless `--record` or `--out` is given.
- **Implement:**
  - `register(add)` receives `build_parser`'s `add` helper: `p = add("backtest", "re-score past rounds under a model variant against actuals", cached=False)`, then the arguments below. Dispatch in `main` like `objective`: `if args.command == "backtest": return backtest.run(args.data_root, args)`.
  - Arguments: `--rounds A-B` (required); `--analysis-root` (default `data/analysis`); `--decisions-root` (default `data/decisions`); `--retro-root` (default `data/retro`); `--no-drift-check`; `--set key=value` (repeatable); `--sweep key=v1,v2,...` (repeatable, up to two keys, cartesian grid, production value of each key first); `--cv`; `--detail`; `--format table|json`; `--out`.
  - Values parse by field type: `none` → `None` for optional fields, `true/false` → bool, else float.
  - The backtest honours the global `--data-root` for raw snapshots.
  - Load each round once and score every variant from memory.
- **Verify:** `uv run pytest tests/test_backtest_cli.py -q`

### Task 1.8: Gate records, manifest and `fpl gates`
- [ ] **Files:** `fpl/backtest.py` (`--record`, `--manifest`, `--record-all`, `--force`, `--gates-root`, `--max-ledger-n-gap`), `fpl/gates.py` (create: record I/O, render, summary, `register`, `run`), `fpl/__main__.py` (one register call, one dispatch line), `tests/test_gate_records.py` (create), `tests/test_gates_cli.py` (create), `tests/test_backtest_cli.py`, `data/model/gates/manifest.toml` (create, with the `baseline` entry only), `docs/ep-model.md` (empty `<!-- gates:begin -->` / `<!-- gates:end -->` markers under a stub `## 8. Backtest` heading).
- **Track:** WB
- **Depends on / parallel with:** 1.7. Parallel with WA, WC, WS.
- **Effort:** M
- **Test:**
  - `test_record_writes_once_and_force_archives`: `--set blend_k=300 --record k300 --gates-root <tmp>` writes `<tmp>/k300.json` with every field in Shared definitions; a second run without `--force` exits 1 naming the record; with `--force` the old file moves to `<tmp>/archive/k300.<stamp>.json`.
  - `test_record_all_runs_in_order_with_earlier_passes_as_baseline`: a manifest with entries `baseline`, `x` (a sweep that passes on the synthetic world), `y` (a `--set` that fails). `y`'s record `baseline_config` carries `x`'s ship value; `combined.json` `shipped_config` = production + `x`; a re-run skips existing records and rewrites `combined.json`.
  - `test_combined_failure_reverts_the_last_pass`: when `combined` fails with two passing entries, `combined.json` `reverted == ["<second>"]` and `shipped_config` holds only the first.
  - `test_ledger_n_gap_refuses`: a ledger with n 10 above the backtest n and `--max-ledger-n-gap 5` exits 1; the per-round table prints `ledger_n` and `Δn`.
  - `test_default_config_matches_gate_records` (tests/test_gate_records.py, reads the repo's `data/model/gates/` read-only): when `combined.json` exists, `DEFAULT_CONFIG == ModelConfig(**shipped_config)`; when it does not, the test passes trivially and says so in its id. Later tasks extend this file for `P4_CALIBRATED` (4.8).
  - `test_ep_model_gate_block_matches_records`: the text between the markers in `docs/ep-model.md` equals `gates.render(records)`.
  - `test_gates_summary_prints_report_and_status_lines` (test_gates_cli): for a PASS and a FAIL record, `gates --gw 8 --summary --gates-root <tmp>` prints `<name>: PASS ship blend_k=450 — ΔMAE −0.0123 [CI −0.020, −0.004], bias 0.18→0.17, wins 5/5` and a status line `shipped` / `rejected: ΔMAE −0.0043 > −0.01 (effect)`.
- **Implement:**
  - Record writer and reader in `fpl/gates.py`; `backtest --record <name>` and `--manifest <p> --record-all [--force]` per Shared definitions; `--gates-root` (default `data/model/gates`).
  - The per-round baseline table adds `ledger_n` and `Δn` from `calibrate.load_report(<retro-root>/gw{r}-calibration.json)` (`-` when absent). `--max-ledger-n-gap N` exits 1 when any |Δn| > N.
  - The per-round table adds `code drift`: mean |baseline predicted − decision-record `ep_gw[0]`| over paired ids, read through `decision_record.record_predictions` (Task 0.6). This needs 0.6 merged into WB; print `-` when the record is unavailable.
  - `fpl gates --gw N (--render | --summary) [--gates-root p] [--doc docs/ep-model.md]`, registered like backtest. `--render` rewrites only the text between the markers: one table row per record (name, kind, rounds, grid, ship value, ΔMAE, CI, bias, wins, verdict, reasons) and, when present, the persistence and p4 blocks.
  - `manifest.toml` starts with `[[gate]] name = "baseline" kind = "model" argv = []`.
- **Verify:** `uv run pytest tests/test_gate_records.py tests/test_gates_cli.py tests/test_backtest_cli.py tests/test_backtest.py -q`

### Task 1.9: Baseline on real data
- [ ] **Files:** `data/model/gates/baseline.json` (written by the run on rounds 3–7).
- **Track:** WB
- **Depends on / parallel with:** 1.8 and `ep-freeze` merged into WB (code-drift column). The recorded run needs round 7 final (Decision 6). Parallel with WA, WC, WS.
- **Effort:** S
- **Test:** the unrecorded dev run exits 0 with `--max-ledger-n-gap 10`; Δn is 0 for rounds 3–6 (measured: n 426, 426, 415, 421).
- **Implement:**
  1. Dev run now (no record): `uv run python -m fpl --data-root /Users/gokul/Dev/Personal/fpl-system/data/raw backtest --gw 7 --rounds 3-6 --analysis-root /Users/gokul/Dev/Personal/fpl-system/data/analysis --retro-root /Users/gokul/Dev/Personal/fpl-system/data/retro --decisions-root /Users/gokul/Dev/Personal/fpl-system/data/decisions --max-ledger-n-gap 10`.
  2. Round-7 actuals (data operation, network, public endpoints; skip when `MAIN/data/raw/gw8/event-live-e7.json` already exists and is final): once round 7 is data-checked, from the WS worktree with S.1–S.2 built: `uv run python -m fpl --data-root /Users/gokul/Dev/Personal/fpl-system/data/raw bootstrap --gw 8` then `uv run python -m fpl --data-root /Users/gokul/Dev/Personal/fpl-system/data/raw event-live --gw 8 --round 7`. The second prints `(fetched)` and writes a final sidecar into main's `data/raw/gw8/`; the GW8 collector and retro then find both snapshots cached (the collector's `bootstrap --gw 8` refetches and archives ours only when it is over 24h old). Until WS merges, main's `calibrate` refetches an event-live snapshot older than 24h (no `final` sidecar yet): run this step within 24h before the GW8 retro, or rely on the retro's own fetch, which is final under the Shared-definitions rule because the collector's `bootstrap --gw 8` precedes it.
  3. Recorded run: the standard gate invocation (Shared definitions). With only the `baseline` entry in the manifest it writes `baseline.json` and `combined.json`.
- **Note:** `baseline.json` scores today's code on the recorded inputs, not the decisions as made. Measured code drift against the decision records is 0.047–0.051 points per player-round. The record's reading and the §8 text (Task 7.1) say so.
- **Verify:** `uv run python -m fpl gates --gw 8 --summary` lists `baseline`; then `uv run pytest -q` (phase end, WB).

### Phase 2 — Prior-weight calibration and promoted clubs (WB)

### Task 2.1: Sweep the blend K
- [ ] **Files:** `data/model/gates/manifest.toml` (append entry), `data/model/gates/prior-weight.json` (written by the run).
- **Track:** WB
- **Depends on / parallel with:** 1.9. First gate in manifest order. Parallel with WA, WC, WS.
- **Effort:** S
- **Test:** the record exists with `picks`, `ship_value`, `verdict` and `reasons`.
- **Implement:**
  - Append `[[gate]] name = "prior-weight" kind = "model" argv = ["--sweep", "blend_k=600,300,450,900,1200", "--cv"]`.
  - Run the standard gate invocation.
  - The floor is not swept: on rounds 3–7 no player passes about 700 current minutes, so every floor value gives identical lines. `--prior-weight` stays a per-run what-if.
- **Verify:** `uv run python -m fpl gates --gw 8 --summary` prints a `prior-weight:` line.

### Task 2.2: Ship or record the prior-weight result
- [ ] **Files:** `fpl/ep.py`, `tests/test_ep.py`, `tests/test_ep_model_doc.py` (create), `docs/ep-model.md` (§2 step 3, gates block).
- **Track:** WB
- **Depends on / parallel with:** 2.1. Parallel with WA, WC, WS.
- **Effort:** S
- **Test:**
  - `tests/test_gate_records.py::test_default_config_matches_gate_records` fails until the constant matches `combined.json` (when the gate passed) and passes unchanged when it failed.
  - If the gate passed: update `test_prior_weight_decays_with_current_minutes_to_a_floor` to the shipped K with hand values at 0/90/180/450/900 minutes, computed by `python3 -c "k=<K>;print([round(max(0.2,k/(k+m)),4) for m in (0,90,180,450,900)])"`, never mentally.
  - `test_ep_model_worked_examples` (tests/test_ep_model_doc.py): the line after `<!-- example: prior_weight minutes=180 -->` in docs/ep-model.md states the value `prior_weight(180)` gives with the current constants, to 2 dp.
- **Implement:**
  - Pass: set `BLEND_EQUIV_MINUTES` to `prior-weight.json` `ship_value`. Rewrite the §2 step 3 line and its worked example under the marker.
  - Fail: no constant change; add the marker and example for the current K.
  - Either way: add under §2 "The floor is untested until players pass about 700 current minutes." Run `uv run python -m fpl gates --gw 8 --render`.
- **Verify:** `uv run pytest tests/test_ep.py tests/test_gate_records.py tests/test_ep_model_doc.py -q`

### Task 2.3: A separate blend K for players with no PL history
- [ ] **Files:** `fpl/ep.py`, `tests/test_ep.py`.
- **Track:** WB
- **Depends on / parallel with:** 1.1. Parallel with 1.2–1.9, WA, WC, WS.
- **Effort:** S
- **Test:** `test_no_history_blend_k_applies_only_to_league_mean_priors`, with `config.blend_k_no_history=300` and 180 current minutes each:
  - a player with no `history_past` gets `prior_weight == 300/480`;
  - a player with `history_past` keeps `600/780`;
  - `None` (the default) behaves as today.
- **Implement:** `ModelConfig.blend_k_no_history: float | None = None`. In `_effective_rates`, use it when `prior_minutes == 0` (equivalent to `prior_source == "league_mean"`).
- **Verify:** `uv run pytest tests/test_ep.py -q`

### Task 2.4: Inputs policies and the slice gate
- [ ] **Files:** `fpl/backtest.py`, `tests/test_backtest.py`, `tests/test_backtest_cli.py`.
- **Track:** WB
- **Depends on / parallel with:** 1.7 (1.8 for the record fields). Parallel with WA, WC, WS.
- **Effort:** S
- **Test:**
  - `test_strip_attack_mult_removes_only_the_named_rows`: `strip_attack_mult(inputs, ids={5})` drops `attack_mult` on id 5 and keeps its other overrides; a row left with no overrides has `overrides=None` and `reason=None` and still validates; id 6 is untouched.
  - `test_inputs_policy_drop_promoted`: `score_round(..., inputs_policy="drop_promoted")` strips rows whose club is in `data.promoted`; `drop_no_history` strips ids whose summary has no `history_past` minutes.
  - `test_slice_gate_and_hypothesis_fields`: with `--gate-slice promoted`, the comparison also applies the five rules to the promoted lines (rule 3 pooled across positions when the slice has under `SLICE_MIN_POSITION_N = 30` lines); the record gets `slice_verdict` and `hypothesis`. `hypothesis == "supported"` iff the baseline slice bias > 0, the variant slice |bias| < the baseline slice |bias|, and the overall verdict is PASS; else `"not supported"`.
- **Implement:** `strip_attack_mult`; `inputs_policy` parameter (`keep`, `drop_promoted`, `drop_no_history`); CLI flags `--inputs-policy` and `--gate-slice promoted|no_history`. `ModelConfig` does not hold the policy.
- **Note:** `--inputs-policy` and `--gate-slice` must also be accepted by the manifest entry parser (`_entry_parser` in fpl/backtest.py), not only by the CLI; otherwise a manifest entry using them is refused as an unknown argument.
- **Verify:** `uv run pytest tests/test_backtest.py tests/test_backtest_cli.py -q`

### Task 2.5: Promoted-club and no-history gates
- [ ] **Files:** `data/model/gates/manifest.toml` (append three entries), `data/model/gates/{drop-promoted,drop-no-history,no-history-k}.json` (written by the run).
- **Track:** WB
- **Depends on / parallel with:** 2.2, 2.3, 2.4. Parallel with WA, WC, WS.
- **Effort:** S
- **Test:** the three records exist; `drop-promoted.json` and `drop-no-history.json` carry `hypothesis`.
- **Implement:** append, then run the standard gate invocation:

  ```
  [[gate]]
  name = "drop-promoted"
  kind = "policy"
  argv = ["--inputs-policy", "drop_promoted", "--gate-slice", "promoted"]

  [[gate]]
  name = "drop-no-history"
  kind = "policy"
  argv = ["--inputs-policy", "drop_no_history", "--gate-slice", "no_history"]

  [[gate]]
  name = "no-history-k"
  kind = "model"
  argv = ["--sweep", "blend_k_no_history=none,150,300", "--cv", "--gate-slice", "no_history"]
  ```

  The user's hypothesis is that the model under-rates high performers from promoted clubs. `attack_mult` is set on 54–69 rows per round for many reasons, so `drop_promoted` tests only the promoted subset. `policy` records never enter `combined`. For a `model` entry run with `--gate-slice`, `slice_verdict` is informational: PASS and the ship value come from the overall five-rule gate only. `hypothesis` is `supported` iff the baseline slice bias is > 0 and the variant's slice |bias| is smaller without the slice failing the five rules pooled across positions (`GATE_SLICE_MIN_LINES = 40`, below which the slice verdict is `n/a`).
- **Verify:** `uv run python -m fpl gates --gw 8 --summary` prints the three lines.

### Task 2.6: Ship or record the promoted-club result
- [ ] **Files:** `fpl/ep.py` (only if `no-history-k` passes), `tests/test_ep.py`, `docs/ep-model.md` (§2 new "Promoted clubs and no-history players" paragraph), `agents/player-analyst.md` (only if `drop-promoted.json` has verdict PASS and `hypothesis == "supported"`).
- **Track:** WB
- **Depends on / parallel with:** 2.5. Parallel with WA, WC, WS.
- **Effort:** S
- **Test:** `test_default_config_matches_gate_records` passes. If the analyst sentence is edited: `uv run pytest tests/evals/test_player_analyst_spec_markers.py -q` passes.
- **Implement:**
  - `no-history-k` PASS: add `BLEND_EQUIV_MINUTES_NO_HISTORY = <ship value>` and make it the `ModelConfig.blend_k_no_history` default.
  - The §2 paragraph names the records, says `drop_promoted` tests only the promoted subset, and points at the gates block for the numbers.
  - Decision 4 trigger: in agents/player-analyst.md § Overrides (the sentence wraps across lines 139–141; replace it in one edit), replace "The code's default for a player with no PL history is the position league mean for a regular starter, which flatters promoted-club and prior-league players: discount them (`attack_mult`, or `xg90`/`xa90`) and tag them HIGH." with "The code's default for a player with no PL history is the position league mean for a regular starter. The backtest found that a blanket discount for promoted-club players loses points (data/model/gates/drop-promoted.json): discount one only for a stated, player-specific reason, and tag it HIGH."
  - `uv run python -m fpl gates --gw 8 --render`.
- **Verify:** `uv run pytest tests/test_ep.py tests/test_gate_records.py -q`, then `uv run pytest -q` (phase end).

### Phase 3 — Opponent-adjusted, recency-weighted current rates (WB)

### Task 3.1: Parse `opponent_team`
- [ ] **Files:** `fpl/models.py`, `tests/test_models.py`.
- **Track:** WB
- **Depends on / parallel with:** 0.1. Parallel with WA, WC, WS (S.4/S.5 also edit `fpl/models.py`, other classes; the merge is additive).
- **Effort:** S
- **Test:** `test_match_record_parses_opponent_team`: `MatchRecord.model_validate(match_record_payload(opponent_team=7)).opponent_team == 7`. A payload without the key gives `None`.
- **Implement:** `opponent_team: int | None = None` on `MatchRecord`.
- **Verify:** `uv run pytest tests/test_models.py -q`

### Task 3.2: Recency weights
- [ ] **Files:** `fpl/ep.py`, `tests/test_ep.py`.
- **Track:** WB
- **Depends on / parallel with:** 1.1 (serial on ep.py). Parallel with WA, WC, WS.
- **Effort:** S
- **Test:** `test_match_weights_halve_every_half_life`:
  - `match_weights(4, half_life=2.0) == [0.5**1.5, 0.5**1.0, 0.5**0.5, 1.0]` (oldest first);
  - `match_weights(3, None) == [1.0, 1.0, 1.0]`.
- **Implement:**
  - `match_weights(count, half_life) -> list[float]`: the j-th most recent played match (age a = 0 for the latest) gets 0.5^(a/H).
  - Only rows with minutes > 0 count, ordered by `(row.round or 0, row.fixture)`. The half-life counts played matches, not rounds: an injured player's older matches keep their weight. One line in §2 says so (Task 3.6).
- **Verify:** `uv run pytest tests/test_ep.py -q`

### Task 3.3: Opponent factors
- [ ] **Files:** `fpl/ep.py`, `tests/test_ep.py`.
- **Track:** WB
- **Depends on / parallel with:** 3.2. Parallel with WA, WC, WS.
- **Effort:** S
- **Test:** `test_opponent_factors_match_hand_values`, base home 1.54, away 1.33 (mean 1.435):
  - `attack_factor(was_home=True, opp_defw=1.25, base) == pytest.approx(1.435/(1.54*1.25))` (0.7455);
  - `attack_factor(False, 0.8, base) == pytest.approx(1.435/(1.33*0.8))` (1.3487);
  - `saves_factor(was_home=True, opp_att=1.2, base) == pytest.approx(1.435/(1.33*1.2))` (0.8991; the opponent plays away);
  - `None` opponent data gives 1.0.
- **Implement:**
  - xG/xA: `adj = raw × base_mean / (base[venue] × DEFW_opp)`, the exact inverse of the forecast multiplier; the player's own ATT_club cancels.
  - Saves: `adj = raw × base_mean / (base[opp_venue] × ATT_opp)`.
  - DefCon is not opponent-adjusted (the forecast DefCon term has no opponent dependence). It is still recency-weighted.
  - The pre-existing saves DEFW_club double count (saves90 already embeds the club's DEFW and the forecast multiplies by DEFW_club again) is out of scope: a backlog row in Task 7.3.
- **Verify:** `uv run pytest tests/test_ep.py -q`

### Task 3.4: Weighted, adjusted current totals feed the blend
- [ ] **Files:** `fpl/ep.py`, `tests/test_ep.py`.
- **Track:** WB
- **Depends on / parallel with:** 3.1, 3.3. Parallel with WA, WC, WS.
- **Effort:** M
- **Test:**
  - `test_defaults_reproduce_today_documents`: for the existing `run_single` worlds of every position, `to_documents()` under `DEFAULT_CONFIG` equals the documents built before this task (store them in the test as expected dicts minus the `model` key, or compare against `replace(DEFAULT_CONFIG)` with the new fields at their off values and the pre-change code path). Compare documents, not floats.
  - `test_recency_weighted_current_rate`: `half_life_matches=1.0`, no adjustment, no prior history, two 90-minute rows (round 1 xG 1.0, round 2 xG 0.0):
    - `totals = current_totals(history, config, ratings=None, team_names={}, base=None)`; `totals.rates(league).xg90 == pytest.approx(1/3)` (= 0.5×1.0 / (0.5×90 + 1×90) × 90);
    - `rates.current_minutes == 180` (raw);
    - with `blend_on_effective_minutes=False` (default) `rates.prior_weight == pytest.approx(600/780)`; with `True`, `600/735` (0.8163).
  - `test_opponent_adjusted_current_rate`: `opponent_adjust=True`, one home row xG 0.6 against OPP with `defw` 1.2 and base home 1.54 / away 1.33:
    - `current_totals(...).rates(league).xg90 == pytest.approx(0.6*1.435/(1.54*1.2))` (0.4659);
    - a row with `opponent_team` missing contributes unadjusted, and one warning line counts such rows.
- **Implement:**
  - `ModelConfig` gains `half_life_matches: float | None = None`, `opponent_adjust: bool = False`, `opponent_adjust_saves: bool = False`, `blend_on_effective_minutes: bool = False`.
  - `_Totals` gains `w_minutes: float` and `w_dc_minutes: float`. `add(row, weight=1.0, attack_factor=1.0, saves_factor=1.0)` accumulates weighted xg, xa, dc, saves and yellow, and weighted minutes into `w_minutes`/`w_dc_minutes`. `minutes`, `starts`, `start_equivalents` and `bonus` stay raw.
  - `rates()` uses `w_minutes` (and `w_dc_minutes`) for per-90 rates and raw `minutes/starts` for `minutes_per_start`. With weight 1 and factor 1 everywhere, every value equals today's.
  - `current_totals(history, config, ratings, team_names, base) -> _Totals` is a module helper used by `_effective_rates`.
  - The blend's `w_prior` uses raw current minutes, or `m_eff = w_minutes` when `blend_on_effective_minutes`. `EffectiveRates.current_minutes` stays raw. Bonus and the observed DefCon hit rate stay unweighted. The DefCon P(hit) blend uses the same `w_prior` as the rates.
  - `build_predictions` passes `fixtures.ratings`, `fixtures.base_lambda` and `bootstrap.team_by_id()` short names to `_effective_rates`. No import of `fixture_ratings`.
- **Note:** the new `ModelConfig` fields change `DEFAULT_CONFIG.digest()` although the output is unchanged; update the hard-coded `044ed4c1` in tests/test_ep.py. A digest change in the middle of a cycle is fine only if every players-*.json of that cycle is regenerated together, because `objective` refuses mixed digests (Task 4.6b).
- **Verify:** `uv run pytest tests/test_ep.py -q`

### Task 3.5: Gate the half-life and the adjustment
- [ ] **Files:** `data/model/gates/manifest.toml` (append three entries), `data/model/gates/{recency,saves-adjust,effective-minutes}.json`.
- **Track:** WB
- **Depends on / parallel with:** 2.6 (gates run in manifest order), 3.4. Parallel with WA, WC, WS.
- **Effort:** S
- **Test:** the three records exist.
- **Implement:** append, then run the standard gate invocation:

  ```
  [[gate]]
  name = "recency"
  kind = "model"
  argv = ["--sweep", "half_life_matches=none,2,3,4,6", "--sweep", "opponent_adjust=false,true", "--cv"]

  [[gate]]
  name = "saves-adjust"
  kind = "model"
  argv = ["--set", "opponent_adjust_saves=true"]

  [[gate]]
  name = "effective-minutes"
  kind = "model"
  argv = ["--set", "blend_on_effective_minutes=true"]
  ```

  `effective-minutes` is measured against a baseline that includes `recency`'s ship value when it passed. Without a half-life it gives d = 0 and fails rule 4 by construction.
- **Verify:** `uv run python -m fpl gates --gw 8 --summary` prints the three lines.

### Task 3.6: Ship or record the Phase 3 result
- [ ] **Files:** `fpl/ep.py`, `tests/test_ep.py`, `docs/ep-model.md` (§2 step 2).
- **Track:** WB
- **Depends on / parallel with:** 3.5. Parallel with WA, WC, WS.
- **Effort:** S
- **Test:** `test_default_config_matches_gate_records` passes.
- **Implement:**
  - Add module constants `HALF_LIFE_MATCHES`, `OPPONENT_ADJUST`, `OPPONENT_ADJUST_SAVES`, `BLEND_ON_EFFECTIVE_MINUTES` as the `ModelConfig` defaults, set from `combined.json` `shipped_config` (`None` / `False` / `False` / `False` when not shipped).
  - If anything shipped, rewrite §2 step 2: `current_rate = Σ wᵢ·adjᵢ·xᵢ / Σ wᵢ·minutesᵢ × 90`, with `wᵢ = 0.5^(ageᵢ/H)` over played matches and `adjᵢ` per Task 3.3; `w_prior` uses raw minutes unless `BLEND_ON_EFFECTIVE_MINUTES`; the DefCon P(hit) blend uses the same `w_prior`.
  - §2 notes either way: the half-life counts played matches; round-N opponent ratings include the adjusted match at weight about 1/10 by GW7 (self-influence, not leakage); rounds 3–6 `fixtures.json` ratings were written by the LLM fixture analyst, so the gate judged the adjustment on ratings production no longer produces.
  - `uv run python -m fpl gates --gw 8 --render`.
- **Verify:** `uv run pytest tests/test_ep.py tests/test_ep_cli.py tests/test_objective.py tests/test_gate_records.py -q`, then `uv run pytest -q` (phase end).

### Phase 4 — Consistency columns and the objective tie-break (not an EP term)

### Task 4.1: P(≥4 points) from the term distribution
- [ ] **Files:** `fpl/consistency.py` (create), `tests/test_consistency.py` (create).
- **Track:** WC
- **Depends on / parallel with:** 0.1. Parallel with WA, WB, WS.
- **Effort:** M
- **Test**, using `FixtureMeans(goal_pts, goal_mean=0, assist_mean=0, p60=0, p_cs=0, cs_pts=0, p_defcon=0, saves_mean=0)` (every field defaults to 0 except `goal_pts`, which is required):
  - FWD, `goal_pts=4`, only `goal_mean=μ`: `p_at_least([fm], p_start=0.9, k=4) == pytest.approx(0.9*(1-math.exp(-μ)))`.
  - MID, `goal_pts=5`, only `p_defcon=0.4`, `p60=0.75`, `p_start=1`: P == 0.75×0.4 (2+2 = 4 in the 60+ branch; 1+2 = 3 otherwise).
  - DEF, `p_cs=0.3`, `cs_pts=4`, `p60=1`: P == 0.3.
  - GKP, `saves_mean=6`, `p60=1`, `p_cs=0`: P == 1 − P(S ≤ 5) for S ~ Poisson(6) (0.5543).
  - Double gameweek, two FWD fixtures with `goal_mean=μ` and `p60=0` explicitly: P == 1 − e^(−2μ).
  - Double gameweek, two fixtures with `p60=1` and μ = 0: P == 1 (2 + 2 = 4).
  - `p_start=0` gives 0.
- **Implement:**
  - Integer-points PMF on 0..40 (overflow mass goes to 40) for one fixture, given a start. It mixes two branches: 60+ (`p60`): base 2, plus `cs_pts` with probability `p_cs`; under 60: base 1, no CS.
  - Convolve independent components: goals Poisson(`goal_mean`) × `goal_pts`, truncated at 10; assists Poisson(`assist_mean`) × 3; DefCon 2 with probability `p_defcon`; saves ⌊S/3⌋.
  - Excluded and documented in §9 with their bias direction: bonus (biases P down), goals conceded (biases GKP/DEF up), cards, the penalty-save tail. The GC/CS coupling and a bonus mass are backlog rows (Task 7.3).
  - A double gameweek convolves both fixtures. `p_at_least = p_start × P(X ≥ k)`.
  - The module imports nothing from `fpl.ep` (plain floats in).
- **Verify:** `uv run pytest tests/test_consistency.py -q`

### Task 4.2: `ep` emits `p4_gw`
- [ ] **Files:** `fpl/ep.py`, `tests/test_ep.py`.
- **Track:** WB
- **Depends on / parallel with:** 4.1 merged into WB (`git merge ep-modules`), 3.4 (serial on ep.py). Parallel with WA, WS.
- **Effort:** M
- **Test:**
  - `test_p4_matches_the_hand_value_for_a_goal_only_forward`: `run_single(4, "FWD", overrides={"xg90": 0.5, "xa90": 0.0, "dc90": 0.0, "minutes_per_start": 90, "prior_weight": 1.0})` with a fixture `lambda_att = BASE_MEAN`:
    - `row.p4_gw[0] == pytest.approx(1 - math.exp(-0.5))` (0.39347; without `dc90 0` the default history's DefCon gives 0.39695);
    - a blank gameweek gives `p4_gw[k] == 0.0`.
  - `test_rows_still_parse_as_calibrate_predictions`: `to_documents()` rows carry `"p4_gw"` (3-dp list), and `PlayerPrediction.model_validate` still accepts them.
- **Implement:**
  - In `build_predictions`, build one `FixtureMeans` per window fixture from the values `_score_fixture` uses: `goal_mean = xg90·share·fixture_mult`, `assist_mean` likewise, `p60`, `p_cs`, `p_defcon = p_hit·defcon_minutes_factor`, `saves_mean`, and the position's `goal_pts`/`cs_pts`.
  - `EpRow.p4_gw: list[float]`; `_round_row` builds its dict by hand, so add `"p4_gw": [round(v, 3) for v in row.p4_gw]` there.
- **Verify:** `uv run pytest tests/test_ep.py -q`

### Task 4.3: Observed return rate over the last five rounds
- [ ] **Files:** `fpl/consistency.py`, `tests/test_consistency.py`.
- **Track:** WC
- **Depends on / parallel with:** 4.1. Parallel with WA, WB, WS.
- **Effort:** S
- **Test:** `test_returns_last5_counts_rounds_at_four_or_more`, at gw 8, with history rows:
  - round 2: 6 points; round 3: 2 points; round 4: two rows, 2 + 3; round 5: 0 points (0 minutes); round 7: 4 points; no round 6 row (a blank); one row with `round: None`.

  Expect `returns_last5(rows, gw=8) == (2, 4)`:
  - the window is rounds 3–7, so round 2 is outside it; the `None` row is skipped;
  - n = distinct rounds with a row in the window = {3, 4, 5, 7} = 4 (a 0-minute round counts in n: availability is part of consistency);
  - k = round 4 (5 points) and round 7 (4 points) = 2.
- **Implement:**
  - `returns_last5(history, gw) -> tuple[int, int]`, over rounds `max(1, gw−5)..gw−1`, skipping rows whose `round` is `None`.
  - Rows are summed per round first. A round is a return iff its total is ≥ 4. Raw points are used because this is a display column, never an EP input.
- **Verify:** `uv run pytest tests/test_consistency.py -q`

### Task 4.4: `p4` and `ret5` in the JSON and the `ep` table
- [ ] **Files:** `fpl/ep.py`, `fpl/__main__.py` (`print_ep`), `tests/test_ep_cli.py`.
- **Track:** WB
- **Depends on / parallel with:** 4.2, 4.3 merged into WB, 4.6 merged into WB (for `P4_CALIBRATED`). Parallel with WA, WS.
- **Effort:** S
- **Test:** `test_ep_table_and_file_carry_p4_and_ret5`:
  - the written `players-MID.json` row has `"returns5": [k, n]`;
  - the printed header (the fixed f-string in `print_ep`) contains ` p4 ` and `ret5`;
  - Alpha's line shows `p4` to 2 dp when MID is in `P4_CALIBRATED` (patch it in the test) and `-` otherwise, and `k/n`.
- **Implement:**
  - `EpRow.returns5: tuple[int, int]`, `(0, 0)` when the player has no current rows.
  - `print_ep` adds `p4` (= `p4_gw[0]`, `-` for positions outside `objective.P4_CALIBRATED`) and `ret5` after `ep/£m`.
- **Verify:** `uv run pytest tests/test_ep_cli.py -q`

### Task 4.5: Calibration of `p4` in the backtest
- [ ] **Files:** `fpl/backtest.py`, `tests/test_backtest.py`.
- **Track:** WB
- **Depends on / parallel with:** 4.2, 1.8. Parallel with WA, WS.
- **Effort:** S
- **Test:** `test_p4_brier_against_a_leave_one_round_out_base_rate`, all MID: round 3 lines p4 [0.8, 0.2], outcomes (actual ≥ 4) [1, 0]; round 4 lines p4 [0.5, 0.5], outcomes [1, 0].
  - `p4_brier == pytest.approx((0.04+0.04+0.25+0.25)/4)` (0.145);
  - the base rate for each round comes from the other rounds (0.5 both ways), so `base_rate_brier == 0.25`;
  - `p4_skill == pytest.approx(1 - 0.145/0.25)` (0.42).
- **Implement:** `score_round` copies `doc["p4_gw"][0]` onto `BacktestLine.p4`. `p4_calibration(lines)` returns per position: n, `p4_brier`, `base_rate_brier` (base rate computed leave-one-round-out and labelled so), skill, and a 5-bin reliability table (mean p4 against observed rate). The comparison and record carry it under `p4`.
- **Note:** calibration entries in the manifest (`argv = []`) are recorded today with `comparison: null`, but Task 4.8's test reads `record["comparison"]["p4"]`. This task must give a calibration record a comparison holding `p4`, or move `p4` to its own record field and change 4.8's test to match.
- **Verify:** `uv run pytest tests/test_backtest.py -q`

### Task 4.6: Tie-break move inside `objective`'s greedy reference
- [ ] **Files:** `fpl/objective.py`, `fpl/objective_report.py`, `tests/test_objective.py`, `tests/test_objective_cli.py`.
- **Track:** WC
- **Depends on / parallel with:** 4.1, 4.3 (row fields). Parallel with WA, WB, WS.
- **Effort:** M
- **Test** (`P4_CALIBRATED` passed explicitly as `calibrated=`):
  - `test_tie_break_picks_the_steadier_incoming_player`: singles A (out X, +2.40, incoming p4₃ 0.30, ret5 1/5) and B (out X, +2.10, p4₃ 0.42, ret5 4/5) both pass the free gate, MID calibrated → `tie_break_moves(singles, view, calibrated={MID}) == [(A, B, B, "p4 0.42 v 0.30")]`.
  - `test_no_tie_outside_the_band`: A at +2.70 and B at +2.10 (0.6 behind, both pass the free gate) gives `[]`, so the test tells the band from the gate.
  - `test_ties_need_the_same_out_player`: B with out Y gives `[]`.
  - `test_ret5_breaks_an_equal_p4`: p4₃ within 0.03 → the higher k/n wins when the k/n gap is ≥ 0.2; otherwise A wins with reason "blend".
  - `test_uncalibrated_position_skips_p4`: MID not in `calibrated` → the decision falls to ret5, then blend.
  - `test_ret5_with_zero_rounds_is_na`: n = 0 → treated as missing, reason "n/a — blend".
  - `test_greedy_reference_takes_the_tie_break_winner`: the greedy reference's first move is B.
  - `test_plan_taking_the_tie_break_winner_passes_the_reference_check`: plan [B] → `evaluate_plan(...).verdict_reasons == ()`; plan [A] fails with a reason naming the tie-break.
  - `test_the_displaced_best_single_is_not_a_further_free_move`: with a spare free transfer and plan [B], A is not reported as a further passing free move.
  - `test_rows_without_consistency_fields_load`: old `players-*.json` without `p4_gw`/`returns5` load with `p4_3=None`, `ret5=None`.
  - CLI: the single-move table has `p4₃` and `ret5` columns; the table output holds a line starting with `TIE_BREAK_LABEL` (`tie-break move:`); `--moves <B>` prints `tie-break: plan takes <B>`, and a plan with no tie in band prints `tie-break: none in band`.
- **Implement:**
  - `Row.p4_3: float | None = None` (mean of `p4_gw[0:3]`), `Row.ret5: tuple[int, int] | None = None`, both at the end of the frozen dataclass, so `evals/squad_optimizer/views.py::_rows` keeps working.
  - `NEAR_TIE_MOVE = 0.5`; `P4_CALIBRATED: frozenset[Position] = frozenset()` (set from the p4 record in Task 4.8); `TIE_BREAK_LABEL = "tie-break move:"` in objective_report.py. `NEAR_TIE = 0.25` and its `near-tie pairs` line are unchanged.
  - `tie_break_moves(singles, view, *, calibrated) -> list[tuple[Scored, Scored, Scored, str]]`: one `(best, challenger, winner, reason)` per passing single with the best's `out` within `NEAR_TIE_MOVE` of it, decided by `tie_break_winner`.
  - `tie_break_winner(a, b, calibrated)`: higher incoming `p4_3` when the position is calibrated and the gap is ≥ 0.03; else higher incoming k/n when both n > 0 and the gap is ≥ 0.2; else A.
  - `greedy_reference` applies it at each step among passing singles with the same `out` within `NEAR_TIE_MOVE` of the best. The "further free move passes" check ignores a single whose `out` matches a tie-break winner already in the plan.
  - The JSON document gains `tie_breaks`. Applies to singles only, not wildcard package marginals (stated in §9).
- **Verify:** `uv run pytest tests/test_objective.py tests/test_objective_cli.py tests/evals/test_squad_optimizer_checks.py tests/evals/test_squad_optimizer_replay.py -q`, and `uv run python -m evals replay squad-optimizer` (offline) diffed against a run from before this task; explain any O3/O4 verdict that flips in the session log.

### Task 4.6b: `objective` refuses mixed model digests
- [ ] **Files:** `fpl/objective.py`, `tests/test_objective.py`.
- **Track:** WB
- **Depends on / parallel with:** 1.1, 4.6 merged into WB. Parallel with WA, WS.
- **Effort:** S
- **Test:**
  - `test_objective_refuses_mixed_model_digests`: players files whose rows carry two different `model` values → `ValueError` "players files built by another model version — rerun `fpl ep` or check out the code they were built with".
  - `test_objective_refuses_a_digest_other_than_the_code`: one digest that differs from `DEFAULT_CONFIG.digest()` → same refusal.
  - `test_objective_accepts_rows_without_a_digest`: rows with no `model` key (files written before 1.1) load.
- **Implement:** in the blend loader, collect the `model` values; refuse on more than one, or on one that differs from `DEFAULT_CONFIG.digest()`.
- **Verify:** `uv run pytest tests/test_objective.py tests/test_objective_cli.py -q`

### Task 4.7: Tie-break sentences in the squad-optimizer and red-team specs
- [ ] **Files:** `agents/squad-optimizer.md` (§ Transfer rule, after "Never transfer for one good fixture what the ticker says turns bad in two."), `agents/red-team-reviewer.md` (checklist item 7), `tests/test_objective_cli.py`.
- **Track:** WC
- **Depends on / parallel with:** 4.6 (lands with it). Parallel with WA, WB, WS.
- **Effort:** S
- **Test:** `test_optimizer_spec_quotes_the_tie_break_label` (tests/test_objective_cli.py): `TIE_BREAK_LABEL in Path("agents/squad-optimizer.md").read_text()`. `tests/evals/test_squad_optimizer_spec_markers.py` still passes: the new text contains neither `--prior-weight` nor `Record every attempted swap`.
- **Implement:**
  - squad-optimizer.md, add this paragraph:

    > Tie-break: `objective`'s greedy reference already prefers the steadier incoming player when two singles with the same outgoing player are within 0.5 blend EP6, and a plan that departs from it fails. Its `tie-break move:` line names the winner. Returns and P(≥4) come from `objective`; never count them yourself. Cite the `tie-break move:` line in the S# reason it decides.

  - red-team-reviewer.md item 7, append: "A move taken from `objective`'s `tie-break move:` line is not a finding unless the line names a different winner."
- **Verify:** `uv run pytest tests/test_objective_cli.py tests/evals/test_squad_optimizer_spec_markers.py -q && grep -n "tie-break move:" agents/squad-optimizer.md agents/red-team-reviewer.md`

### Task 4.8: Validate `p4` on real data, then document
- [ ] **Files:** `data/model/gates/manifest.toml` (append `p4`), `data/model/gates/p4.json`, `fpl/objective.py` (`P4_CALIBRATED`), `tests/test_gate_records.py`, `docs/ep-model.md` (new §9 "Consistency columns").
- **Track:** WB
- **Depends on / parallel with:** 4.4, 4.5, 4.6b. Independent of the other gates' order. Parallel with WA, WS.
- **Effort:** S
- **Test:** `test_p4_calibrated_positions_match_record`: when `p4.json` exists, `objective.P4_CALIBRATED == frozenset(pos for pos, v in record["comparison"]["p4"].items() if v["skill"] > 0)`.
- **Implement:**
  - Append `[[gate]] name = "p4" kind = "calibration" argv = []` and run the standard gate invocation.
  - Set `P4_CALIBRATED` to the positions with skill > 0.
  - §9 defines `p4_gw` (Task 4.1 components and exclusions with their bias directions), `returns5` (Task 4.3), the tie-break (Task 4.6, singles only, uncalibrated positions skip p4), and holds the rendered p4 block. Run `uv run python -m fpl gates --gw 8 --render`.
- **Verify:** `uv run pytest tests/test_gate_records.py -q`, then `uv run pytest -q` (phase end).

### Phase 5 — Residual persistence, then an optional form term and finishing multiplier

### Task 5.1: Persistence statistic
- [ ] **Files:** `fpl/persistence.py` (create), `tests/test_persistence.py` (create).
- **Track:** WC
- **Depends on / parallel with:** 0.1. Parallel with WA, WB, WS.
- **Effort:** M
- **Test**, on synthetic `CalibrationReport`s for rounds 1–5:
  - `test_exact_linear_persistence`: y = 0.5·x for every pair → `slope == 0.5`, `se_ols == 0`, `se_cluster == 0`, `r == 1`.
  - `test_no_persistence`: x symmetric around 0 and y alternating +1/−1 independent of x → `slope == pytest.approx(0)` and both CIs contain 0.
  - `test_constant_y_gives_r_zero`: y constant → `r == 0` (no division by zero).
  - `test_inclusion_rules`, window w = 3, min_starts = 2: a player not started at t is excluded; a player with one window start is excluded; x is the mean error over started window rounds only.
  - `test_by_position_and_target_rounds`: the result lists target rounds 4 and 5 and per-position n.
  - `test_cluster_se_by_player`: two players each contributing two pairs; `se_cluster` equals the hand value from the sandwich formula below.
- **Implement:** `persistence(reports, *, window=3, min_starts=2) -> PersistenceResult`.
  - Pairs: x = mean error over started rounds in t−w..t−1; y = error at t.
  - OLS β = Σ(x−x̄)(y−ȳ)/Σ(x−x̄)²; s² = Σ(y−α−βx)²/(n−2); `se_ols` = √(s²/Σ(x−x̄)²).
  - `se_cluster` by player id: √(Σ_p (Σ_{i∈p} (xᵢ−x̄)·uᵢ)²) / Σ(x−x̄)², with uᵢ the OLS residual. CI = β ± 1.96·`se_cluster`; the OLS CI is reported too.
  - Pearson r, 0 when either sd is 0.
  - `significant` = `n ≥ 100 and ci_low (clustered) > 0`.
- **Verify:** `uv run pytest tests/test_persistence.py -q`

### Task 5.2: `fpl persistence` command
- [ ] **Files:** `fpl/persistence.py` (`register`, `run`), `fpl/__main__.py` (one register call, one dispatch line), `tests/test_persistence_cli.py` (create).
- **Track:** WC
- **Depends on / parallel with:** 5.1. Parallel with WA, WB, WS.
- **Effort:** S
- **Test:** with ledgers written to `tmp_path/retro`, `main(["persistence", "--gw", "7", "--retro-root", str(root)])` prints:
  - `window 3, min starts 2: n <n>, slope <β> [lo, hi] (cluster), r <r> — significant|not significant`;
  - one line per position;
  - the same at window 1 and window 2, below, as sensitivity;
  - exit 0 when window 3 is significant, 3 when not. Ledgers for rounds ≥ gw are ignored.
- **Implement:** `register(add)`: `add("persistence", "does a player's recent EP residual predict his next one", cached=False)` with `--window` (default 3), `--min-starts` (default 2), `--retro-root` (default `data/retro`), `--format`. Load with `calibrate.load_report`. Exit 0 when significant, 3 when not (argparse uses 2 for usage errors); Task 5.3 branches on the record's `significant` field, with the exit code as a convenience.
- **Verify:** `uv run pytest tests/test_persistence_cli.py -q`

### Task 5.3: Measure on the real ledgers and branch
- [ ] **Files:** `fpl/persistence.py` (`--record`, using `fpl/gates.py`), `tests/test_persistence_cli.py`, `data/model/gates/persistence.json`, `docs/ep-model.md` (new §10 "Form").
- **Track:** WB
- **Depends on / parallel with:** 5.2 merged into WB, 1.8, 5.7 (gate order); needs `MAIN/data/retro/gw7-calibration.json` (written by the GW8 retro, about 21 Oct). Parallel with WA, WS.
- **Effort:** S
- **Test:** `test_persistence_record_holds_three_windows`: `--record persistence --gates-root <tmp>` writes `kind: persistence` with windows 1–3 and `significant`.
- **Implement:**
  - Run `uv run python -m fpl persistence --gw 8 --retro-root /Users/gokul/Dev/Personal/fpl-system/data/retro --record persistence`. Ledgers GW1–7, with GW6 regenerated by Task 0.7.
  - §10 notes that GW1–2 ledgers score LLM-computed EP and GW3+ score code EP, so the pooled residuals mix model versions; `objective`'s prior-only reading builds predictions at prior weight 1, so the form term is 0 there by construction. The numbers come from `fpl gates --render`.
  - **`significant: false`:** §10 says "no form term". Skip Tasks 5.4 and 5.5. Task 7.3 gives the row the status from `fpl gates --summary`.
  - **`significant: true`:** do Tasks 5.4 and 5.5.
- **Note:** a persistence record needs the `GateRecord` schema extended (it has `extra="forbid"` and required comparison-style fields), and `gates._headline` / `gates._render_row` must handle a persistence comparison. `fpl persistence` exits 3 when the result is not significant, which is what today's real data gives; the recording step must not treat exit 3 as a failure.
- **Verify:** `uv run pytest tests/test_persistence_cli.py -q && grep -n "^## 10" docs/ep-model.md`

### Task 5.4 (only if 5.3 is significant): Shrunk form term
- [ ] **Files:** `fpl/ep.py`, `fpl/__main__.py` (`run_ep` computes residuals), `fpl/backtest.py` (`residuals_for`), `tests/test_ep.py`, `tests/test_backtest.py`, `tests/test_ep_cli.py`.
- **Track:** WB
- **Depends on / parallel with:** 5.3. Parallel with WA, WS.
- **Effort:** M
- **Test:**
  - `test_form_term_is_shrunk_by_one_minus_prior_weight`: `form_beta=0.3`, residual x = 2.0 (mean of [2, 1, 3], all started), `prior_weight` 0.6 → each window GW's `terms.form == p_start_gw[g] × 0.3 × 0.4 × 2.0` and `ep_total6` includes it.
  - `test_blank_gameweek_has_no_form`: a window GW with no fixture has `terms.form == 0`.
  - `test_prior_only_reading_has_no_form`: `prior_weight` forced to 1.0 → form == 0.
  - `test_residuals_default_none_gives_no_form`.
  - `test_backtest_form_uses_only_earlier_rounds_rescored_by_the_variant`: for round r, `residuals_for(rounds r−3..r−1, config)` re-scores those rounds with `score_round` under the same config; round r's own actuals are never read.
  - `test_ep_missing_snapshots_give_zero_form_and_one_warning` (test_ep_cli): no event-live for the residual rounds → exit 0, no form, one warning line.
  - `test_ep_non_final_snapshot_gives_zero_form_and_one_warning` (test_ep_cli): a residual round whose event-live is present but not final → exit 0, zero form for it, one warning; no git drift check runs (a non-repo tmp tree).
- **Implement:**
  - `ModelConfig.form_beta: float = 0.0`; `Terms.form`.
  - `build_predictions(..., residuals: Mapping[int, float] | None = None)`. x per player = mean error over the started rounds among N−3..N−1; fewer than 2 such rounds → 0.
  - `form(g) = p_start_gw[g] × form_beta × (1 − w_prior) × x` when GW g has a fixture, else 0.
  - `backtest.residuals_for(round_data_list, config) -> dict[int, float]` uses `score_round`, the same function in production and in the backtest. `run_ep` loads rounds N−3..N−1 with `load_round(..., drift_check=False)` and passes the mapping; a round whose snapshot is missing or not final gives zero form for that round and one warning line (at step 3 of a cycle round N−1 is often not yet final). `ep.py` never imports `backtest`.
- **Verify:** `uv run pytest tests/test_ep.py tests/test_backtest.py tests/test_ep_cli.py -q`

### Task 5.5 (only if 5.3 is significant): Gate the form term
- [ ] **Files:** `fpl/backtest.py` (`@persistence:` sweep values), `tests/test_backtest_cli.py`, `data/model/gates/manifest.toml`, `data/model/gates/form.json`, `fpl/ep.py` (constant `FORM_BETA`), `docs/ep-model.md` (§1 term table row, §10).
- **Track:** WB
- **Depends on / parallel with:** 5.4. Last gate in manifest order. Parallel with WA, WS.
- **Effort:** S
- **Test:** `test_sweep_reads_multiples_of_the_recorded_slope`: with a persistence record of slope 0.4, `--sweep form_beta=@persistence:0,0.5,1` expands to `0.0, 0.2, 0.4`. `test_default_config_matches_gate_records` passes after the constant is set.
- **Implement:**
  - Append `[[gate]] name = "form" kind = "model" argv = ["--sweep", "form_beta=@persistence:0,0.5,1", "--cv"]`; run the standard gate invocation.
  - `FORM_BETA` = `combined.json` `shipped_config.form_beta` (0.0 if not shipped), as the `ModelConfig` default.
  - If shipped, add the §1 row `form | p_start × β × (1 − w_prior) × mean residual (last 3 started rounds, current code) | all`. Render.
- **Verify:** `uv run pytest tests/test_ep.py tests/test_gate_records.py tests/test_backtest_cli.py -q`

### Task 5.6: Multi-season finishing multiplier (behind the gate)
- [ ] **Files:** `fpl/ep.py`, `tests/test_ep.py`.
- **Track:** WB
- **Depends on / parallel with:** 1.1 (serial on ep.py after 3.4). Parallel with WA, WC, WS.
- **Effort:** S
- **Test:**
  - `test_finishing_multiplier_is_heavily_shrunk`: seasons 2023/24 (G 7, xG 5) and 2024/25 (G 5, xG 3) with `k=10` give `pytest.approx(22/18)` (= (12+10)/(8+10)).
  - `test_seasons_before_xg_existed_are_ignored`: a 2021/22 season with G 9, xG 0 changes nothing.
  - `test_multiplier_scales_xg90_but_not_an_override`: an `xg90` override is left unscaled.
  - `test_none_disables`: `finishing_k=None` gives multiplier 1.0.
- **Implement:**
  - `XG_FIRST_SEASON = "2022/23"`; `finishing_multiplier(history_past, k)` over seasons ≥ `XG_FIRST_SEASON`: `(ΣG + k)/(ΣxG + k)`. `history_past` comes from summaries now; Task S.11 switches it to the store's `xg_recorded`.
  - `ModelConfig.finishing_k: float | None = None`. Apply it to the blended `xg90` before overrides. Expose `rates.finishing_mult`.
- **Verify:** `uv run pytest tests/test_ep.py -q`

### Task 5.7: Gate the finishing multiplier
- [ ] **Files:** `data/model/gates/manifest.toml`, `data/model/gates/finishing.json`, `fpl/ep.py` (constant `FINISHING_K`), `docs/ep-model.md` (§2 new "Finishing" paragraph).
- **Track:** WB
- **Depends on / parallel with:** 3.6 (gate order), 5.6. Parallel with WA, WS.
- **Effort:** S
- **Test:** `test_default_config_matches_gate_records` passes after the constant is set.
- **Implement:**
  - Append `[[gate]] name = "finishing" kind = "model" argv = ["--sweep", "finishing_k=none,20,10,5", "--cv"]`; run the standard gate invocation.
  - `FINISHING_K` = `combined.json` `shipped_config.finishing_k` (`None` if not shipped), as the `ModelConfig` default.
  - The paragraph explains the multiplier and points at the gates block. Render.
- **Verify:** `uv run pytest tests/test_ep.py tests/test_gate_records.py -q`, then `uv run pytest -q` (phase end).

### Phase 6 — Team-xG cross-check (a reading aid, not an EP change)

### Task 6.1: Observed shares of club xG
- [ ] **Files:** `fpl/team_share.py` (create), `tests/test_team_share.py` (create).
- **Track:** WC
- **Depends on / parallel with:** 0.1. Parallel with WA, WB, WS.
- **Effort:** S
- **Test:** `test_observed_shares_over_started_matches`:
  - `club_xg = {(10, "H"): 1.5, (11, "A"): 1.0, (12, "H"): 2.0}`;
  - player rows: fixture 10 home start xG 0.3 xA 0.2; fixture 11 away start xG 0.5 xA 0; fixture 12 sub (starts 0) xG 0.4;
  - xG share = 0.8/2.5; xA share = 0.2/2.5; starts = 2;
  - `recent` uses the last 4 started matches (here the same two).
- **Implement:**
  - `observed_shares(history, club_xg) -> Shares(xg_season, xa_season, xg_recent, xa_recent, starts)`.
  - Only rows with `starts ≥ 1` whose (fixture, side) is in `club_xg` count.
  - The xA share uses club xG as its denominator.
- **Verify:** `uv run pytest tests/test_team_share.py -q`

### Task 6.2: Implied share and the flag rule
- [ ] **Files:** `fpl/team_share.py`, `tests/test_team_share.py`.
- **Track:** WC
- **Depends on / parallel with:** 6.1. Parallel with WA, WB, WS.
- **Effort:** S
- **Test:**
  - `test_implied_share`: `implied_share(rate90=0.45, mps=90, attack_mult=1.0, base_mean=1.435, att_club=1.2) == pytest.approx(0.45/(1.435*1.2))` (0.2613).
  - `test_flag_when_far_apart`: implied 0.30 against season 0.18 with 4 starts gives `"xG EP>club"`.
  - `test_no_flag_inside_tolerance`: 0.22 against 0.18 is no flag; the tolerance is max(0.05, 0.4×0.18 = 0.072).
  - `test_no_flag_under_three_starts`: no flag.
  - Both xG and xA flagged give `"xG EP>club; xA EP<club"`.
- **Implement:**
  - `implied = rate90 × min(mps, 90)/90 × attack_mult / (base_mean × ATT_club)`.
  - Flag when `starts ≥ 3` and `|implied − season| > max(0.05, 0.4 × season)`.
  - Constants `SHARE_MIN_STARTS = 3`, `SHARE_ABS_TOL = 0.05`, `SHARE_REL_TOL = 0.4`.
- **Verify:** `uv run pytest tests/test_team_share.py -q`

### Task 6.3: Wire the cross-check into `fpl ep`
- [ ] **Files:** `fpl/__main__.py` (`run_ep`, `print_ep`, `--share-detail`), `fpl/team_share.py` (`annotate`), `tests/test_ep_cli.py`, `tests/test_analyst_view_golden.py` (Call 4 size test), `agents/player-analyst.md` (Call 4, one sentence).
- **Track:** WB
- **Depends on / parallel with:** 4.4, 6.1–6.2 merged into WB. Parallel with WA, WS.
- **Effort:** M
- **Test:**
  - `test_ep_flags_a_share_disagreement`:
    - seed `analysis/club-priors.json` with priors for TST and OPP, the `fixtures` snapshot with finished fixtures for rounds 1–2, `raw/gw2/event-live-e1.json` and `raw/gw3/event-live-e2.json` (the rating path needs every round 1..gw−1), and a summary where Alpha took 0.1 of club xG over 3 starts while his override makes the implied share 0.4;
    - the written row has `"share_flag": "xG EP>club (implied 0.40, season 0.10, 3 starts)"`;
    - the table has a `share` column showing `xG EP>club`;
    - stderr has exactly one line `share check: 1 flagged (ids 1)`;
    - with `--share-detail`, stderr also has `share check: id 1 Alpha xG EP>club (implied 0.40, season 0.10, 3 starts)`.
  - `test_ep_unflagged_rows_carry_a_null_share_flag`.
  - `test_ep_runs_without_rating_inputs`: no club-priors → one warning `share check skipped: <refusal>`, exit 0, every row `share_flag: null`. Check existing test_ep_cli tests that assert stderr exactly and update them for this line.
  - `test_call_4_fits_inline[GKP|DEF|MID|FWD]` (tests/test_analyst_view_golden.py): `ep --gw 6 --position POS --out <tmp>/p.json` on the committed GW6 data (`ep` is local-only and takes no `--max-age`) prints stdout + stderr ≤ `LIMIT`.
- **Implement:**
  - In `run_ep`, after `build_predictions`: the club xG map comes from `fixture_ratings.load_inputs(store, gw, priors_path=args.analysis_root / PRIORS_FILENAME, analysis_root=args.analysis_root)` then `rate(...)`; `RatingRefusal` and `SnapshotMissingError` become the skip warning. Task S.11 replaces this with the store.
  - `team_share.annotate(documents, ...)` sets `share_flag` on each document; then `write_predictions`. `build_predictions` stays pure; the backtest is untouched.
  - agents/player-analyst.md, Call 4 paragraph, add: "A `share check` warning or a `share` flag is evidence about the rates. Act on it only for a row where you set `xg90`, `xa90` or `attack_mult`. Never file a backlog row per flag."
  - docs/ep-model.md §4 (Task 7.1) says the flag is a reading aid, never an override reason on its own.
- **Note:** `fixture_ratings._side_xg` raises a plain `ValueError` on a summary row with no `was_home`; catch it as a skip warning too, so `fpl ep` (live cycle step 3) never fails on the cross-check. The club xG map is built from `RatingRun.matches` as `{(m.fixture, "H"): m.xg_home, (m.fixture, "A"): m.xg_away}`.
- **Verify:** `uv run pytest tests/test_ep_cli.py tests/test_team_share.py tests/test_analyst_view_golden.py tests/evals/test_player_analyst_spec_markers.py -q`, then `uv run pytest -q` (phase end).

### Phase S — Fetch policy and season store (WS)

Within WS, S.1 → S.2 → S.3 → S.4 are serial: all four edit `fpl/service.py`, `fpl/__main__.py`, `tests/test_service.py` and `tests/test_cli.py`. S.5 and S.6 run beside them (new files only).

Fetch policy, recorded at fetch time in the `.meta` sidecar and enforced in `FplDataService._load_or_fetch`:

| Endpoint | Policy |
|---|---|
| bootstrap-static | TTL 24h, never final; `flags` force-refreshes; `bootstrap --gw N` already refuses once N is past |
| fixtures | TTL 24h for the snapshot; in the store, a fixture of a data-checked round is final |
| element-summary `history_past` | fetched once per player per season (every id with no `history_past` in the store); served at any age |
| element-summary `history` | rebuilt from event-live × fixtures × bootstrap; targeted fetches only for DGW players, unresolved sides, or a reconciliation mismatch |
| element-summary `fixtures` | never needed (derivable from fixtures.json) |
| event/{r}/live | final once fetched while a bootstrap fetched ≤ 1h before shows event r `data_checked`; served at any age; `--force` refetches and archives |
| entry/{id}/event/{M}/picks | final when fetched after deadline M |
| entry, entry history | TTL 24h (unchanged) |
| my-team, writes | never cached (unchanged) |
| `actuals` | local: reads the final event-live snapshot, zero calls |

What must not change: `data/raw/gw{N}/` stays the committed evidence (never destroyed, archived on refresh); as-of r uses only rounds < r and snapshots fetched before deadline r; a past round's files are never regenerated; `ep` output for the open GW must be byte-identical from the store before the collector stops fetching summaries; `flags` always refreshes; the cache-note grammar `(fetched)`, `(cached, age Xh)`, `(F fetched, C cached)` stays (a final hit prints `(cached, age Xh, final)`).

Store tables (`data/store/season-2026-27.sqlite`, stdlib `sqlite3`, `PRAGMA user_version` = schema version, mismatch → rebuild):

| Table | Key | Columns | Source |
|---|---|---|---|
| `manifest` | path | sha256, kind, gw, fetched_at, final, ingested_rows | every raw file ingested |
| `events` | id | deadline_time, finished, data_checked, seen_in | latest bootstrap |
| `clubs` | id | short_name, name | bootstrap |
| `fixtures` | id | event, team_h, team_a, kickoff_time, finished, scores, source_gw | latest fixtures snapshot; frozen once the round is data-checked |
| `player_rounds` | (element, fixture) | round, team, opponent_team, was_home, kickoff_time, minutes, starts, total_points, goals, assists, CS, GC, saves, bonus, bps, xg, xa, xgc, dc, yellow, red, own_goals, pens_saved, pens_missed, source, side_rule, split, modified, source_path | event-live e{r} × fixtures × bootstrap gw r, gw r+1; summary rows override for DGW and unresolved rows |
| `history_past` | (element, season_name) | code, every PastSeason field, xg_recorded (season ≥ 2022/23), dc_recorded (≥ 2024/25), source_path | first summary per player |
| `player_state` | (gw, element) | fetched_at, code, web_name, team, position, now_cost, status, chance, news_added, selected_by_percent, form, totals | the kept bootstrap of each GW |
| `summary_coverage` | (gw, element) | — | which summaries existed in `data/raw/gw{r}/players` |

Archived bootstraps are not ingested (they are git-ignored and absent in worktrees).

### Task S.1: Final snapshots and sidecar keys
- [ ] **Files:** `fpl/store.py`, `fpl/service.py`, `fpl/__main__.py` (`_format_fetch_log`), `tests/test_store.py`, `tests/test_service.py`, `tests/test_cli.py`.
- **Track:** WS
- **Depends on / parallel with:** 0.1. Parallel with WA, WB, WC, S.5 (S.2–S.4 are serial after it on `fpl/service.py`).
- **Effort:** M
- **Test:**
  - `test_save_records_final_and_basis_in_the_sidecar`: `store.save(..., final=True, basis="x")` writes both keys; `store.meta(gw, name)` returns them; `fetched_at()` still parses.
  - `test_old_sidecar_without_final_reads_as_not_final`.
  - `test_final_snapshot_is_served_past_max_age`: a final snapshot aged 100h with `max_age_hours=24` gives a cache hit, no API call (FakeApi records calls), `FetchEvent(final=True)`.
  - `test_force_refetches_a_final_snapshot_and_archives_it`.
  - `test_cache_note_spells_final`: `_format_fetch_log` gives `(cached, age 100.0h, final)`, and `evals.harness.fpl_output.note_from_text` reads it as `CacheNote("cached")`.
- **Implement:** `save(..., final: bool = False, basis: str | None = None, reason: str | None = None)`; `meta()`; `_load_or_fetch(..., final_when: Callable[[Any], tuple[bool, str | None]] | None = None)` decides finality at fetch time and writes it; a final cached snapshot ignores `max_age_hours`. `FetchEvent.final: bool = False`. Unknown sidecar keys stay ignored by old readers.
- **Verify:** `uv run pytest tests/test_store.py tests/test_service.py tests/test_cli.py -q`

### Task S.2: `fpl event-live` and a final actuals snapshot
- [ ] **Files:** `fpl/service.py` (`event_live`), `fpl/__main__.py` (parser, dispatch, `run_calibrate`), `tests/test_service.py`, `tests/test_calibrate_cli.py`, `tests/test_cli.py`.
- **Track:** WS
- **Depends on / parallel with:** S.1. Parallel with WA, WB, WC, S.5. Needed by about 20 Oct for the round-7 actuals (Task 1.9 step 2).
- **Effort:** M
- **Test:**
  - `test_event_live_refuses_before_data_checked`: cached bootstrap gw 8 with event 7 `data_checked=false` exits 1; the message names `bootstrap --gw 8 --force`. No fetch.
  - `test_event_live_saves_final_with_basis`: event 7 checked; `main(["event-live", "--gw", "8", "--round", "7"])` writes `gw8/event-live-e7.json` with sidecar `final: true` and a basis naming the bootstrap fetch time; prints `(fetched)`.
  - `test_event_live_second_run_is_a_final_cache_hit_at_any_age`: clock +72h → `(cached, age 72.0h, final)`, no API call.
  - `test_calibrate_reuses_the_final_snapshot`: after the above, `calibrate --gw 8 --round 7` makes no event-live call at the default max-age.
  - `test_event_live_round_must_be_before_gw`: `--round 8 --gw 8` exits 1.
- **Implement:** `add("event-live", "fetch one data-checked round's live stats (final once fetched)")` with `--round`; `final_when` = the cached bootstrap gw N, fetched before this fetch (any age: `data_checked` never reverts), shows event R `data_checked`; calibrate calls the same service method.
- **Verify:** `uv run pytest tests/test_service.py tests/test_calibrate_cli.py tests/test_cli.py -q`

### Task S.3: Picks final after their deadline; post-deadline write guard
- [ ] **Files:** `fpl/service.py`, `fpl/__main__.py`, `tests/test_service.py`, `tests/test_cli.py`.
- **Track:** WS
- **Depends on / parallel with:** S.2 (serial on `fpl/service.py`). Parallel with S.5, WA, WB, WC.
- **Effort:** S
- **Test:**
  - `test_picks_fetched_after_the_event_deadline_are_final`.
  - `test_summaries_into_a_past_gw_refuse_after_its_deadline`: cached bootstrap says deadline 6 passed; `summaries --gw 6 --ids 1 --force` exits 1 naming `--allow-post-deadline`; bootstrap and fixtures likewise; `event-live` into gw 7 for round 6 is allowed.
- **Implement:** deadline from the cached bootstrap of the same GW (`deadline_for`); guard in `_load_or_fetch` for kinds bootstrap, fixtures, summary; `--allow-post-deadline` on those three commands.
- **Verify:** `uv run pytest tests/test_service.py tests/test_cli.py -q`

### Task S.4: `actuals` from event-live, no network
- [ ] **Files:** `fpl/service.py` (`actuals`), `fpl/models.py` (`LiveStats` adds `expected_assists`, `yellow_cards`, `expected_goals_conceded`, `red_cards`, all default `None`), `fpl/__main__.py`, `tests/test_service.py`, `tests/test_models.py`, `tests/test_cli.py`.
- **Track:** WS
- **Depends on / parallel with:** S.3 (serial on `fpl/service.py`; S.2 supplies the final snapshot it reads). Parallel with S.5, WA, WB, WC.
- **Effort:** S
- **Test:**
  - `test_actuals_reads_the_round_snapshot_without_fetching`: FakeApi raises on any call; lines equal the event-live stats.
  - `test_actuals_refuses_without_a_final_snapshot`: names `fpl event-live --gw N --round M`.
  - `test_actuals_double_gameweek_is_already_summed`.
  - `test_live_stats_parse_the_new_fields`.
- **Implement:** read `event-live-e{M}` from gw N (or M+1); the `cached=False` parser entry stays.
- **Verify:** `uv run pytest tests/test_service.py tests/test_models.py tests/test_cli.py -q`

### Task S.5: Season store schema and `sync`
- [ ] **Files:** `fpl/season_store.py` (create), `fpl/models.py` (`Fixture` adds scores and `stats`; `Player` adds `code`), `tests/test_season_store.py` (create), `tests/factories.py`, `.gitignore` (`data/store/`).
- **Track:** WS
- **Depends on / parallel with:** 0.1. Parallel with S.1–S.4, WA, WB, WC.
- **Effort:** M
- **Test** (synthetic raw tree under `tmp_path`, two clubs, rounds 1–2):
  - `test_sync_rebuilds_summary_rows_from_event_live`: for every covered id, `player_rounds` equals the summary rows field by field.
  - `test_side_from_bps_list_then_bootstrap_union`: a played player resolves by the bps list; a 0-minute player by bootstrap gw r ∪ gw r+1; a player transferred between the gw r snapshot and the match lands on the match club; a player absent from bootstrap gw r resolves from gw r+1.
  - `test_unresolved_side_is_listed_not_guessed`.
  - `test_double_gameweek_without_summary_splits_by_minutes_and_marks_it`; `test_double_gameweek_with_summary_uses_the_summary_rows`.
  - `test_refuses_a_non_final_event_live`.
  - `test_sync_is_incremental_and_idempotent`: a second sync ingests 0 files; the `iterdump()` text is identical.
  - `test_rebuild_equals_incremental`.
  - `test_history_past_ingested_once_per_player`.
  - `test_archives_are_not_ingested`.
  - `test_reconciliation_flags_a_total_mismatch`: bootstrap totals ≠ Σ rounds for one id gives a mismatch line; skipped when the current event is not data-checked.
- **Implement:** schema per the table above; `sync(raw_root, db_path) -> SyncReport`; models validate every file at the boundary; one transaction per sync; `PRAGMA user_version`; no clock reads. An event-live snapshot is ingested as final only if its sidecar says `final` or a bootstrap of the same or a later GW, fetched after it, shows the round data-checked.
- **Verify:** `uv run pytest tests/test_season_store.py tests/test_models.py -q`

### Task S.6: As-of readers returning existing models
- [ ] **Files:** `fpl/season_store.py`, `tests/test_season_store.py`.
- **Track:** WS
- **Depends on / parallel with:** S.5. Parallel with S.1–S.4, WA, WB, WC.
- **Effort:** M
- **Test:**
  - `test_as_of_excludes_round_r_and_later`.
  - `test_as_of_summaries_equal_raw_summaries_for_covered_ids`: `summaries(as_of=3, coverage="production")` equals `load_cached_summaries(store, 3, ids)` on `history` and `history_past`, with `opponent_team` filled.
  - `test_coverage_shortlist_pins_the_league_pool`: an extra non-shortlisted player with 2,000 prior minutes is absent under `shortlist`, present under `all`; `_league_mean` differs only under `all`.
  - `test_schedule_comes_from_the_as_of_fixtures_snapshot`: a fixture moved after the gw r snapshot keeps its gw r round.
  - `test_club_match_xg_equals_fixture_ratings_side_xg` on the synthetic tree (2-dp rounding).
  - `test_reader_refuses_a_store_behind_the_raw`: a raw file not in `manifest` names `fpl store sync --gw N`.
- **Implement:** `open_ro(path)` (`mode=ro`); `summaries(as_of, ids, coverage)` with coverage `production` (ids in `summary_coverage` gw r), `shortlist` (is_shortlisted on bootstrap gw r ∪ the round's inputs ids, the set `run_ep` loads today) or `all` (a model variant, gated like any other); `rounds(as_of, ids)`; `past(ids)`; `club_match_xg(as_of)`; `player_state(gw)`. Readers return `ElementSummary` with `MatchRecord`/`PastSeason`, so `build_predictions` does not change.
- **Verify:** `uv run pytest tests/test_season_store.py -q`

### Task S.7: `fpl store sync|verify|status|rebuild`
- [ ] **Files:** `fpl/season_store.py` (`register`, `run`), `fpl/__main__.py` (one register call, one dispatch line), `tests/test_store_cli.py` (create).
- **Track:** WS
- **Depends on / parallel with:** S.5, S.6. Parallel with WA, WB, WC.
- **Effort:** S
- **Test:** `main(["--data-root", raw, "store", "sync", "--gw", "3", "--store", db])` exits 0 and prints `rounds 1-2`, `player_rounds <n>`, `history_past players <n>`, `unresolved sides 0`, `dgw splits 0`, `reconciliation: OK`; a seeded mismatch prints `reconciliation: 1 mismatch` and exits 3; `status` prints the manifest summary; `verify` and `status` write nothing.
- **Implement:** `add("store", "build and check the local season store (derived from data/raw)", cached=False)` with a positional action `sync|verify|status|rebuild` and `--store` (default `data/store/season-2026-27.sqlite`).
- **Verify:** `uv run pytest tests/test_store_cli.py -q`, then on real data, writing only to the scratchpad: `uv run python -m fpl store sync --gw 7 --store <SCRATCH>/s.sqlite` exits 0 with `unresolved sides 0` and `reconciliation: OK`.

### Task S.8: Readers switch to the store (parity first)
- [ ] **Files:** `fpl/__main__.py` (`run_ep`, `run_ep_check`, `_minutes_by_round`), `fpl/objective.py`, `fpl/fixture_ratings.py` (`load_inputs`, `_side_xg`), `tests/test_ep_cli.py`, `tests/test_fixture_ratings.py`, `tests/test_cli.py`, `tests/test_analyst_view_golden.py`.
- **Track:** WS
- **Depends on / parallel with:** S.6, S.7. Parallel with S.9, WA, WB, WC.
- **Effort:** M
- **Test:**
  - `test_ep_from_store_equals_ep_from_summaries`: same synthetic world, `--history-from store` and `--history-from summaries` write identical `players-MID.json`.
  - `test_players_minutes_from_store_fills_summary_less_players`.
  - `test_fixtures_rate_from_store_equals_summaries_when_no_transfers`.
  - Golden: update `test_analyst_view_golden.py` for the `no summary` → minutes change, under `--history-from store` only (the default stays `summaries`).
- **Implement:** `--history-from {store,summaries}` on `ep`, `objective`, `players`, `fixtures-rate`. The default stays `summaries` until S.10. Put the source switch in one helper `_history(store, gw, ids, source)` in `fpl/__main__.py`, so `run_ep`, `run_ep_check`, `_minutes_by_round` and `objective.prior_documents` change one call each; Tasks 0.6b, 5.4 and 6.3 also edit `run_ep`, so WB merges main immediately after WS lands and resolves that one block.
- **Verify:** `uv run pytest tests/test_ep_cli.py tests/test_fixture_ratings.py tests/test_cli.py tests/test_analyst_view_golden.py -q`; real-data parity, writing only to the scratchpad and the git-ignored `data/store/` (GW7 is decided, so `--out` is required): `uv run python -m fpl store sync --gw 7 --store data/store/season-2026-27.sqlite`, then for each POS in GKP DEF MID FWD: `uv run python -m fpl ep --gw 7 --position POS --history-from store --out <SCRATCH>/s-POS.json` and `… --history-from summaries --out <SCRATCH>/r-POS.json`, then `cmp <SCRATCH>/s-POS.json <SCRATCH>/r-POS.json` (must be identical for all four).

### Task S.9: `fpl history` agent views and the CLAUDE.md rows for WS
- [ ] **Files:** `fpl/season_store.py` (or `fpl/history_view.py`, create, with `register`), `fpl/__main__.py` (one register call), `tests/test_history_cli.py` (create), `CLAUDE.md` (data-tooling rows and one persistence line).
- **Track:** WS
- **Depends on / parallel with:** S.6. Parallel with S.8, WA, WB, WC.
- **Effort:** S
- **Test:** `history --gw 8 --position MID --last 5 --fields id,name,round,opp,venue,minutes,xg,xa,points --format csv` prints one row per player-match, rounds 3–7 only; `--ids 1,2`; `--per round` sums a DGW; `history --past --season 2025/26 --min-minutes 900 --fields id,name,minutes,xg` filters `history_past`; `--group-by team` prints one row per club; an unknown field exits 1 listing valid fields.
- **Implement:**
  - Read-only over S.6; same `--fields`/`--format` conventions as `players`.
  - CLAUDE.md data-tooling table: new rows `event-live --round R` (final once data-checked; served at any age), `store sync|verify|status|rebuild [--store <p>]` (local only), `history …` (local only); amend `actuals` (local only, reads the final event-live snapshot); amend `ep`, `objective`, `players`, `fixtures-rate` with `--history-from store|summaries`; amend the `Cached commands` mechanics line for final snapshots and the post-deadline guard (`--allow-post-deadline`). Persistence rules: "data/store/ is derived from data/raw and git-ignored; rebuild with `fpl store rebuild`."
- **Verify:** `uv run pytest tests/test_history_cli.py -q && grep -n "event-live\|store sync\|history-from" CLAUDE.md`, then `uv run pytest -q` (phase end, WS).

### Task S.10: Collector stops refetching summaries (cycle-facing; needs the user's go-ahead)
- [ ] **Files:** `fpl/__main__.py` (`summaries --missing-past`), `agents/data-collector.md`, `agents/retro-analyst.md` (`actuals` line: "local, from event-live"), `CLAUDE.md`, `evals/data_collector/checks.py` (C15), `tests/evals/test_data_collector_spec_markers.py`, `tests/evals/test_data_collector_checks.py`, `tests/test_cli.py`.
- **Track:** WS
- **Depends on / parallel with:** S.2, S.7, S.8 (real-data parity passed), S.9, and Decision 8. Last task of WS.
- **Effort:** S
- **Test:**
  - `test_summaries_missing_past_fetches_only_ids_without_history_past` (FakeApi counts calls: only the new id).
  - Spec markers and C15 updated to "every bootstrap id has `history_past` in the store".
- **Implement:** collector order: `bootstrap` → `fixtures` → `summaries --missing-past` → `store sync` → entry/picks/history → `slim-csv` → (GW1 only) `prior-season` → auth-check. Default `--history-from store` everywhere. Drop the 600000 timeout note; meta.md `Coverage:` line from `store sync`.
- **Verify:** `uv run pytest tests/test_cli.py tests/evals -q -k "data_collector or cli"` and `grep -n "missing-past\|store sync" agents/data-collector.md CLAUDE.md`.

### Task S.11: Model consumers read the store when it exists
- [ ] **Files:** `fpl/backtest.py` (`load_round` history from the store with coverage `production`; `drop_no_history` from `history_past`), `fpl/consistency.py` callers in `fpl/ep.py` (`returns_last5` from store rows), `fpl/ep.py` (finishing multiplier uses `xg_recorded`), `fpl/__main__.py` (`run_ep` club xG from `season_store.club_match_xg(as_of=N)`), `tests/test_backtest.py`, `tests/test_consistency.py`, `tests/test_ep.py`, `tests/test_ep_cli.py`.
- **Track:** WB
- **Depends on / parallel with:** WS merged into main and main merged into WB (S.6), plus 1.3, 2.4, 4.3, 5.6, 6.3. Not needed to ship for GW9; it can land in a later merge window.
- **Effort:** M
- **Test:**
  - `test_load_round_from_store_equals_raw`: on the Task 1.3 world plus a synced tmp store, `load_round(..., store=db)` gives the same `score_round` lines as the raw path.
  - `test_returns_last5_from_store_rows_matches_summary_rows`: one synthetic player, same answer from both sources.
  - `test_finishing_uses_xg_recorded`: a store row with `xg_recorded = 0` is ignored.
  - `test_ep_share_check_reads_the_store`: `test_ep_flags_a_share_disagreement`'s world built as a tmp store instead of event-live snapshots gives the same flag; a store missing a round gives the `share check skipped: …` warning.
- **Implement:** each consumer takes the store when `data/store/season-2026-27.sqlite` (or `--store`) exists and is in sync, else the current path. `returns5` is `(0, 0)` only when the store has no rows for the player.
- **Verify:** `uv run pytest tests/test_backtest.py tests/test_consistency.py tests/test_ep.py tests/test_ep_cli.py -q`

### Phase 7 — Docs, process, hand-off

### Task 7.1: docs/ep-model.md
- [ ] **Files:** `docs/ep-model.md`.
- **Track:** WB
- **Depends on / parallel with:** every WB gate and ship task. Parallel with WA, WS.
- **Effort:** S
- **Test:** `uv run pytest tests/test_gate_records.py tests/test_ep_model_doc.py -q` passes (the gates block equals the render, the worked example matches the code).
- **Implement:** Phases 2, 3, 4 and 5 already updated §1, §2, §5, §9 and §10. Add:
  - §3 output fields: `model`, `p4_gw`, `returns5`, `share_flag`, and `terms.form` and `rates.finishing_mult` if shipped.
  - §4 "Running it": the refusal after final.md, the `share check` summary line and `--share-detail`, the share flag as a reading aid, never an override reason on its own.
  - §5: append "A model change is judged with `fpl backtest` (§8) and recorded under data/model/gates/; a decided round is never regenerated to judge it."
  - §8 "Backtest": the command; the rounds rule; the leakage rules (raw inputs fetched before the deadline per sidecar; summary rounds < r; optional drift refusal against the decision commit; actuals from a final event-live snapshot); the coverage-replay rule; the gate (verbatim from Shared definitions); LORO and `ship_value`; records, manifest, `combined`; the fact that the baseline is the current code on recorded inputs, which differs from the ledger (the historical record) by the printed code drift. The gates block sits here.
  - Plain English, no counts in prose.
- **Verify:** `grep -n "^## 8\|^## 9\|^## 10\|gates:begin" docs/ep-model.md`

### Task 7.2: CLAUDE.md
- [ ] **Files:** `CLAUDE.md`.
- **Track:** WB
- **Depends on / parallel with:** 7.1. Parallel with WA, WS (S.9 edits other rows of the same table; merge is row-level).
- **Effort:** S
- **Test:** `uv run pytest tests/evals/test_retro_spec_markers.py tests/evals/test_player_analyst_spec_markers.py -q` passes (they read CLAUDE.md markers such as "calibrate reads that snapshot's data_checked flag"); the rest is checked by grep.
- **Implement:**
  - New data-tooling rows:
    - `backtest --rounds A-B [--analysis-root <p> --decisions-root <p> --retro-root <p>] [--set k=v] [--sweep k=v1,v2] [--cv] [--inputs-policy keep|drop_promoted|drop_no_history] [--gate-slice promoted|no_history] [--record <name> | --manifest <p> --record-all] [--force] [--max-ledger-n-gap N] [--gates-root <p>] [--no-drift-check] [--detail] [--format table|json] [--out <p>]`: re-scores past rounds under a model variant from disk; paired five-rule gate; writes gate records. Local only.
    - `gates (--render | --summary) [--gates-root <p>] [--doc <p>]`: renders the docs/ep-model.md §8 evidence block from the gate records, or prints report and status lines. Local only.
    - `persistence [--window W] [--min-starts S] [--retro-root <p>] [--record <name>]`: residual-persistence slope with a player-clustered CI from the calibration ledgers; exit 0 significant, 2 not. Local only.
  - Amend `calibrate`: `--predictions-from commit|worktree` (default commit) scores the decision record (the predictions lock, else the commit that first added final.md) and prints one `predictions:` line; one WARNING when files changed after the decision.
  - Amend `ep`: prints a `model <digest>` line, `p4`, `ret5` and `share` columns and one `share check` line; refuses to write `players-{pos}.json` once final.md exists (`--out` what-ifs still work); `--decisions-root`, `--share-detail`.
  - Amend `plan`: also writes `data/decisions/gw{N}/predictions.lock.json` once.
  - Amend `objective`: `tie-break move:` line and `p4₃`/`ret5` columns; refuses players files built by another model digest.
  - Persistence rules:
    - change "data/analysis/gw{N}/players-{pos}.json … regenerating any of them is safe and expected" so players-{pos}.json is safe to regenerate "until final.md exists for that GW (`ep` refuses afterwards)";
    - add "data/decisions/gw{N}/predictions.lock.json is written once by `fpl plan` and never overwritten";
    - add "data/model/gates/ holds gate records: derived, but kept and committed as the evidence for a model decision; written once (`--force` archives)";
    - add "Progress commits `gw{N}: … (decision pending)` are allowed. The decision record is the commit that adds data/decisions/gw{N}/final.md; calibrate scores the players-*.json in it."
  - Weekly cycle step 0: "a `C<n> — CODE` correction ships as a code change with tests and an `fpl backtest` gate record (docs/ep-model.md §8)".
  - Orchestration: "Code merges land on main only between a decision commit and the next cycle's step 0."
- **Verify:** `grep -n "backtest\|gates (--render\|persistence \[\|predictions-from\|predictions.lock\|until final.md exists\|Code merges land" CLAUDE.md`

### Task 7.3: Backlog rows (on main, after merge 2, as a triage session)
- [ ] **Files:** `docs/backlog.md` (append with `cat <<'EOF' >> docs/backlog.md`, `EOF` at column 0; Status edits only on rows this work closes).
- **Track:** WB (runs on main after WB has merged)
- **Depends on / parallel with:** merge 2. Not parallel with any branch append.
- **Effort:** S
- **Test:** both shape checks from CLAUDE.md pass, and `uv run pytest tests/test_backlog_shape.py -q` passes.
- **Implement:**
  - The report's first line declares this a triage session.
  - Append one row per item, format `| GW<N> | <ISO date> | ORCH | <KIND> | <finding> | <evidence path> | <status> |`, where N is the gameweek whose deadline is next on the append date. Status for built items comes from `uv run python -m fpl gates --gw <N> --summary` (`shipped <sha>` after the user's commit, or `rejected: <reason>`); deferred items are `open`.

    | Item | Kind | Evidence | Status |
    |---|---|---|---|
    | decision record, prediction lock, `ep` refusal after final.md | TOOL | fpl/decision_record.py | shipped |
    | backtest harness, gate records, manifest, `fpl gates` | TOOL | fpl/backtest.py | shipped |
    | prior-weight K | CODE | data/model/gates/prior-weight.json | from summary |
    | promoted clubs and no-history K | CODE | data/model/gates/no-history-k.json, drop-promoted.json | from summary |
    | point player-analyst Call 1 and the retro-analyst at the `fpl history` views once S.10 lands; the optimizer and red-team never open players-*.json whole (a `fpl predictions` view) | WORKFLOW | agents/player-analyst.md, agents/retro-analyst.md, agents/squad-optimizer.md | open |
    | opponent-adjusted recency rates | CODE | data/model/gates/recency.json | from summary |
    | p4 and ret5 columns | CODE | data/model/gates/p4.json | shipped |
    | objective tie-break and digest guard | TOOL | fpl/objective.py | shipped |
    | residual persistence command | TOOL | data/model/gates/persistence.json | shipped |
    | form term | CODE | data/model/gates/form.json or persistence.json | from summary |
    | finishing multiplier | CODE | data/model/gates/finishing.json | from summary |
    | team-share flag | TOOL | fpl/team_share.py | shipped |
    | final snapshots, event-live, local actuals, season store, history views | TOOL | fpl/season_store.py | shipped or open (if WS not merged) |
    | final-check: each final.md `GW{N} EP` cell equals players-*.json `ep_gw[0]` | TOOL | fpl/final_check.py | open |
    | generated Top-15 block in players-POS.md and retro skeleton fences (need analyst and retro spec sentences) | TOOL | fpl/__main__.py print_ep, print_calibration | open |
    | `fpl predictions` filtered view; optimizer and red-team never open players-*.json whole | WORKFLOW | agents/squad-optimizer.md | open |
    | p4: couple goals conceded with clean sheets; add a bonus mass | CODE | fpl/consistency.py | open |
    | saves90 embeds the club's DEFW and the forecast multiplies by DEFW_club again | CODE | fpl/ep.py | open |
    | `_prior_seasons` can pool a pre-2022/23 season whose xG is reported as 0 — prior xg90 = 0 for a player returning to the PL | CODE | fpl/ep.py `_prior_seasons` | open |
    | daily price series needs an unattended daily bootstrap fetch | DATA | data/raw | open |

  - Status edits on existing rows: "GW7 A6 TOOL calibrate squad XI predicted 53.80 v final.md 56.178 …" → `shipped <sha>`; "GW7 A4 TOOL `objective` greedy-reference tolerance (0.05 blend) …" stays `open` (Task 4.6's tie-break covers only singles with the same `out`; that row's pair, Schade → Sávio v Thiaw → Van Hecke, differs in `out`); "GW4 A4 TOOL C14 needs every candidate's EP on prior-only rates …" stays as it is.
- **Verify:** `tail -c1 docs/backlog.md | od -An -c && awk '/^## Rows/{p=1} p && NF && !/^\|.*\|$/' docs/backlog.md`. They must print `\n` and only `## Rows`.

### Task 7.4: Final verification and hand-off
- [ ] **Files:** none.
- **Track:** WB (runs on main after merge 2)
- **Depends on / parallel with:** 7.3.
- **Effort:** S
- **Test:** the full suite on main passes with a pass count ≥ main's pre-build count plus the new tests.
- **Implement:**
  - `git status --short`: no file under `data/analysis/gw[1-7]/`, `data/raw/`, `data/decisions/` (except locks written by the live cycle), `data/retro/gw*.md` or `data/auth.json` changed by this work. Expected data changes: `data/retro/gw6-calibration.json` and `data/model/gates/*`.
  - Report to the user:
    - `uv run python -m fpl gates --gw 9 --summary` output: shipped and not-shipped features with their gate numbers;
    - the commit split by stream (see below), no attribution trailer;
    - this is a CODE change outside the GW cycle, so the GW9 cycle's `fpl ep` is the first to use it;
    - ask the orchestrator to add one line to the next retro brief: "data/retro/gw6-calibration.json was regenerated from decision commit b28927f on <date>; cumulative figures before that date used the post-decision files." If Phase 0 merged before the GW8 retro, that retro is the one that needed it;
    - whether S.10 is still waiting for the go-ahead, and that until WS merges and S.10 lands the collector still refetches about 470 summaries a gameweek, `actuals` still force-refreshes summaries and `calibrate` refetches event-live after 24h.
  - Do not commit.
- **Verify:** `uv run pytest -q`

## Build sequencing and parallel tracks

### Dependency graph

```
 WA ep-freeze (Phase 0)                              WS ep-store (Phase S)  ∥ everything
 0.1 → 0.2 → 0.3 → 0.4 → 0.5 → 0.6 → 0.6b → 0.9      S.1 → S.2 ─────────────┐ (round-7 actuals ~21 Oct)
                    │             ├→ 0.7 (data)       S.1 → S.3              │
                    │             └→ 0.8 (docs)       S.4                    │
                    │                                 S.5 → S.6 → S.7 → S.8 → [S.10 user go-ahead]
                    │                                             └→ S.9     │
                    ▼ merge ep-freeze into WB after 0.4 (drift check 1.3; 1.2 after 0.5; code drift 1.8)
 WB ep-form (owns fpl/ep.py)   ∥ Phase 0                         WC ep-modules (pure modules)
 1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6 → 1.7 → 1.8 → 1.9            4.1 → 4.3 → 4.6 → 4.7
  ├→ 2.3 → 2.4                                                   5.1 → 5.2
  ├→ 3.1 → 3.2 → 3.3 → 3.4 → 5.6                                 6.1 → 6.2
  └→ (WC merged in) 4.2 → 4.4 → 4.5 → 4.6b → 6.3                  (merged into WB as each finishes)
                                                                 │
 DATA, gates in manifest order (round 7 final, ~21 Oct)          ▼
   1.9 baseline → 2.1/2.2 → 2.5/2.6 → 3.5/3.6 → 5.7 → 5.3 → [5.4 → 5.5]     4.8 any time after 4.5/4.6b
                                                                 │
   → 7.1 → 7.2 → merge 2 (WB → main) → 7.3 (main) → 7.4         S.11 after WS → main → WB
```

Phase 0 and Phase 1 are parallel: the backtest reads disk, so its only link to WA is the optional drift check (needs 0.4) and the code-drift column (needs 0.6). The graph draws file order inside WB, not strict dependencies: Task 3.1 (models.py) needs only 0.1, and Task 2.4 needs 1.7 (the CLI flag) as well as 2.3; the per-task Depends-on lines are authoritative. Phase S is parallel with everything; its only data link is S.2 producing round-7 actuals early.

### File ownership

| File | Tasks (track) |
|---|---|
| fpl/ep.py | 1.1, 2.2, 2.3, 2.6, 3.2, 3.3, 3.4, 3.6, 4.2, 4.4, 5.4, 5.5, 5.6, 5.7, S.11 (WB only) |
| fpl/__main__.py | 0.6, 0.6b, 0.9 (WA); 1.1, 1.7, 1.8, 4.4, 5.4, 6.3, S.11 (WB); 5.2 (WC, one register line); S.1, S.2, S.3, S.4, S.7, S.8, S.9, S.10 (WS) |
| fpl/calibrate.py | 0.5 (WA), 1.2 (WB, after merging ep-freeze) |
| fpl/decision_record.py (new) | 0.3, 0.4, 0.6, 0.9 (WA) |
| fpl/plan.py / run_plan | 0.9 (WA) |
| fpl/backtest.py (new) | 1.3–1.9, 2.4, 4.5, 5.4, 5.5, S.11 (WB) |
| fpl/gates.py (new) | 1.8, 5.3 (WB) |
| fpl/consistency.py (new) | 4.1, 4.3 (WC); S.11 (WB) |
| fpl/persistence.py (new) | 5.1, 5.2 (WC); 5.3 (WB) |
| fpl/team_share.py (new) | 6.1, 6.2 (WC); 6.3 (WB) |
| fpl/objective.py, objective_report.py | 4.6 (WC); 4.6b, 4.8 (WB); S.8 (WS, `--history-from` only) |
| fpl/models.py | 3.1 (WB, `MatchRecord`); S.4, S.5 (WS, `LiveStats`, `Fixture`, `Player`) |
| fpl/store.py, fpl/service.py | S.1–S.4 (WS) |
| fpl/season_store.py (new) | S.5–S.9 (WS) |
| fpl/fixture_ratings.py | S.8 (WS) |
| docs/ep-model.md | 0.8 (WA); 1.8, 2.2, 2.6, 3.6, 4.8, 5.3, 5.5, 5.7, 7.1 (WB) |
| docs/backlog.md | 0.8 (WA, prompt only); 7.3 (main) |
| CLAUDE.md | S.9, S.10 (WS); 7.2 (WB) |
| agents/retro-analyst.md | 0.6 (WA); S.10 (WS) |
| agents/player-analyst.md | 2.6 conditional, 6.3 (WB) |
| agents/squad-optimizer.md, red-team-reviewer.md | 4.7 (WC) |
| agents/data-collector.md, evals/data_collector/* | S.10 (WS) |
| evals/retro_analyst/live.py | 0.6 (WA) |
| data/model/gates/* | 1.8, 1.9, 2.1, 2.5, 3.5, 4.8, 5.3, 5.5, 5.7 (WB) |

New CLI commands register through module functions (`backtest.register(add)`, `gates.register(add)`, `persistence.register(add)`, the store and history registers) with one line each in `build_parser` and one dispatch line in `main`, so `__main__.py` merges stay trivial.

### Workstreams, merge order and merge gates

| Order | Stream | Content | Gate command before merging | Target, window |
|---|---|---|---|---|
| 1 | WA freeze | 0.2–0.9 | `uv run pytest tests/test_gitrepo.py tests/test_decision_record.py tests/test_calibrate.py tests/test_calibrate_cli.py tests/test_ep_cli.py tests/test_plan.py tests/test_plan_cli.py tests/test_backlog_shape.py tests/evals/test_retro_cases.py tests/evals/test_retro_replay.py tests/evals/test_retro_spec_markers.py tests/evals/test_retro_checks.py -q && uv run pytest -q`; the Task 0.7 assert prints `ok`; `uv run python -m evals replay retro-analyst` scorecard unchanged against a run on main | main, merge window 1 (Mon 19–Tue 20 Oct, before the GW8 retro) |
| 2 | WC modules | 4.1, 4.3, 4.6, 4.7, 5.1, 5.2, 6.1, 6.2 | `uv run pytest tests/test_consistency.py tests/test_persistence.py tests/test_persistence_cli.py tests/test_team_share.py tests/test_objective.py tests/test_objective_cli.py tests/evals/test_squad_optimizer_spec_markers.py tests/evals/test_squad_optimizer_checks.py tests/evals/test_squad_optimizer_replay.py -q`; `uv run python -m evals replay squad-optimizer` diffed against a pre-change run | into WB (`git merge ep-modules` in WB), as modules finish; never straight to main |
| 3 | WS store | S.1–S.9 (S.10 only with the go-ahead) | `uv run pytest tests/test_store.py tests/test_service.py tests/test_cli.py tests/test_models.py tests/test_calibrate_cli.py tests/test_season_store.py tests/test_store_cli.py tests/test_history_cli.py tests/test_ep_cli.py tests/test_fixture_ratings.py tests/test_analyst_view_golden.py -q && uv run pytest -q`; S.7 real sync prints `reconciliation: OK`; S.8 `cmp` identical for all four positions | main, any window after S.8 parity (never during a cycle) |
| 4 | WB form | 1.x, 2.x, 3.x, 4.2, 4.4, 4.5, 4.6b, 4.8, 5.3–5.7, 6.3, 7.1, 7.2 (+ WC) | `uv run pytest -q` (count ≥ the WB baseline plus new tests); `uv run pytest tests/test_gate_records.py tests/test_ep_model_doc.py tests/test_analyst_view_golden.py tests/evals/test_player_analyst_spec_markers.py tests/evals/test_squad_optimizer_spec_markers.py -q`; `uv run python -m evals replay player-analyst` and `uv run python -m evals replay squad-optimizer` (offline); `uv run python -m fpl gates --gw 8 --summary` lists every manifest entry; when `combined.json` `shipped_config` equals the baseline config, `uv run python -m fpl --data-root /Users/gokul/Dev/Personal/fpl-system/data/raw ep --gw 8 --position MID --analysis-root /Users/gokul/Dev/Personal/fpl-system/data/analysis --out <SCRATCH>/p.json` gives the same `ep_gw` per id as main's committed `data/analysis/gw8/players-MID.json` | main, merge window 2 (after the GW8 decision commit, Fri 23 Oct, by Mon 26 Oct) |
| 5 | Process | 7.3, 7.4 | the two CLAUDE.md shape checks; `uv run pytest -q` | main |

Live evals stay disabled: every eval command above is `replay` or a pytest run.

### Critical path

0.1 → 1.1 → 1.3 → 1.4 → 1.5 → 1.6 → 1.7 → 1.8 → 3.1–3.4 → [round 7 final, ~21 Oct] → 1.9 → 2.1/2.2 → 2.5/2.6 → 3.5/3.6 → 5.6/5.7 → 5.3 (→ 5.4/5.5) → 7.1/7.2 → merge 2 (by Mon 26 Oct).

S.1 → S.2 must be ready by about 20 Oct only if the gates are to start before the GW8 retro. The slack sits in WC (pure modules, needed before 4.2/6.3) and in WS (needed only for S.11 and S.10).

### Timeline

| Date (UTC) | Main (live cycle) | Build |
|---|---|---|
| Thu 16 Oct | GW7 cycle in flight on main (outside this plan; the user runs it separately) — merge freeze | user makes commits 1–3; Task 0.1: four worktrees, baselines; build starts in the worktrees |
| 16–20 Oct | GW7 cycle completes on main; its decision commit opens merge window 1 | WA Phase 0; WB 1.1–1.8, 2.3, 2.4, 3.1–3.4, 5.6; WC modules; WS S.1–S.7; 1.9 dev run on rounds 3–6 |
| Mon 19–Tue 20 Oct | **merge window 1: WA → main** (incl. the 0.7 GW6 ledger as its own commit) | WB merges main |
| ~Tue 20–Wed 21 Oct | round 7 data-checked; GW8 cycle starts (collector, retro writes `data/raw/gw8/event-live-e7.json`, scoring the GW7 decision record) | as soon as `event-live --gw 8 --round 7` returns final into `MAIN/data/raw/gw8/` (or the GW8 retro has run): 1.9 recorded, then gates in manifest order |
| 21–Fri 23 Oct 17:30 | **GW8 cycle — merge freeze on main** | gates 2.1→2.6, 3.5→3.6, 5.7, 5.3→5.5; 4.8; ship/record tasks in WB; WS S.8 parity |
| Fri 23 Oct after the GW8 decision commit | merge window 2 opens | WS → main if S.8 parity passed; WB merges main right after WS lands (expect one conflict in `run_ep`); WC already in WB |
| by Mon 26 Oct | — | **WB → main**; 7.3 backlog rows on main; 7.4 report |
| ~Tue 27–Sat 31 Oct 11:00 | GW9 cycle: the first `fpl ep` on the new model | S.11 in a later window; S.10 only with the go-ahead |

### Merge-freeze rule

No merge to main between a cycle's step 0 (retro) and its decision commit (the commit that adds final.md). A shipped constant merged mid-cycle would make positions scored earlier and a REOPEN rerun use different models, and `objective`'s prior-only reading would be rebuilt with new code against blend files from the old. Task 4.6b's digest guard makes such a half-merge refuse rather than pass silently. Task 7.2 writes the rule into CLAUDE.md.

### Commit split by stream (the user commits; no attribution trailer)

| Stream | Commit subject | Tasks |
|---|---|---|
| WA | `calibrate: score the decision record` | 0.2–0.6, 0.9 |
| WA | `ep: refuse to overwrite a decided gameweek` | 0.6b |
| WA | `retro: regenerate gw6 ledger from decision commit b28927f` | 0.7 |
| WA | `docs: triage prompt never regenerates a decided round` | 0.8 |
| WS | `data: final snapshots, event-live, local actuals` | S.1–S.4 |
| WS | `store: season store and history views` | S.5–S.9 |
| WS | `collector: fetch only missing history_past, sync the store` | S.10 (only with the go-ahead) |
| WB | `backtest: harness, gate records and manifest` | 1.1–1.9 |
| WB | `ep: prior-weight and no-history gates (<shipped|kept>)` | 2.x |
| WB | `ep: opponent-adjusted recency rates (<shipped|kept>)` | 3.x |
| WB | `ep: consistency columns and objective tie-break` | 4.x (incl. WC 4.1, 4.3, 4.6, 4.7) |
| WB | `ep: residual persistence and form term (<shipped|kept|not significant>)` | 5.1–5.5 |
| WB | `ep: finishing multiplier (<shipped|kept>)` | 5.6–5.7 |
| WB | `ep: team-share check` | 6.x |
| WB | `docs: ep-model §8–§10, CLAUDE.md tooling and persistence rules` | 7.1, 7.2 |
| WB | `store: model consumers read the season store` | S.11 (later window) |
| main | `backlog: ep form upgrade rows` | 7.3 |

### What the user commits first (on main, today)

Committing changes nothing on disk, so the in-flight GW7 cycle, which runs main's working tree, is unaffected.

Use the hunk-staging helper `/Users/gokul/Dev/Personal/fpl-transcripts-archive/eval-plans/stage_hunks.py`, because hunks interleave. Run `uv run pytest -q` after each commit.

1. **Tooling the live cycle already uses** (must be committed):
   - `fpl/__main__.py`, `fpl/corrections.py`, `fpl/calibrate.py`, `fpl/ep.py`, `fpl/service.py`;
   - `tests/test_cli.py`, `tests/test_calibrate.py`, `tests/test_calibrate_cli.py`, `tests/test_ep.py`, `tests/test_service.py`, `tests/test_corrections.py`, `tests/test_corrections_cli.py`, `tests/test_analyst_view_golden.py`;
   - `agents/player-analyst.md`, `agents/retro-analyst.md`, `agents/data-collector.md`, `agents/red-team-reviewer.md`, `CLAUDE.md`, `docs/ep-model.md`.
2. **Player-analyst eval**: `evals/player_analyst/`, `evals/fixtures/player-analyst/`, `tests/evals/test_player_analyst_*.py`, plus its hunks in `evals/__main__.py`, `evals/harness/{freeze,live,transcript,workspace}.py` and `tests/evals/test_{freeze,transcript,workspace}.py`.
3. **Retro-analyst eval WIP** (committed, not stashed, so Task 0.6 can fix its validity check): `evals/retro_analyst/`, `evals/fixtures/retro-analyst/`, `tests/evals/test_retro_*.py`, as `evals: retro-analyst eval (offline parts, no e2e review)`.

## Self-review

- [x] Every v1 task is accounted for. Kept with changes: 0.1–0.8, 1.1–1.7, 2.1–2.6, 3.1–3.6, 4.1–4.8, 5.1–5.7, 6.1–6.3, 7.1–7.4. Renumbered: v1 1.8 (baseline) is v2 1.9. Dropped: v1 Decision 2's deadline-keyed `ep` guard (replaced by 0.6b, keyed on final.md), the `blend_floor` sweep (unidentifiable), and every per-task `test_*_is_the_backtested_value` (replaced by `tests/test_gate_records.py`). New: 0.6b, 0.9, 1.8, 4.6b, S.1–S.11.
- [x] Every report D FIX is applied: 0.1, 0.3, 0.5, 0.6, 0.8, 1.3, 1.4, 1.5, 1.6, 2.1, 3.4, 4.1, 4.2, 4.6, 5.1, 5.4, 6.3, 7.3; D's notes applied in 0.2, 1.7, 3.2, 3.3, 3.6, 4.3, 4.4, 4.5, 2.5, 5.6. D-0.4's optional `read_at` is not adopted (stated in Changes). D-4.1's GC/CS coupling and D-3.3's saves double count are deferred to backlog rows (Task 7.3).
- [x] Every adopted A, B, C finding per the decision record is in a task; the record's deferred items are backlog rows in Task 7.3 and are listed in Decision 9.
- [x] Every task has `**Files:**`, `**Test:**`, `**Implement:**`, `**Verify:**`, `**Track:**`, `**Depends on / parallel with:**` and `**Effort:**`.
- [x] No placeholders in code tasks. Data-bound tasks name the record that decides them; conditional tasks (5.4, 5.5) branch on `persistence.json` `significant`; gate-dependent constants have a defined value for both outcomes via `combined.json`.
- [x] Hand values are stated and checked: 1.5 (each rule isolated), 1.6 (picks `{3:"a",4:"a",5:"b"}`), 3.3 (0.7455, 1.3487, 0.8991), 3.4 (1/3, 600/780, 600/735, 0.4659), 4.1 (DGW with `p60=0`, 0.5543), 4.2 (overrides with `dc90 0`, `prior_weight 1.0`), 4.3 ((2, 4)), 4.5 (0.145, 0.25, 0.42), 5.6 (22/18), 6.2 (0.2613), 0.7 (56.18, 421, 0.254, 1.632).
- [x] File paths are real at HEAD 9017751 plus the user's three commits; created files are marked (create).
- [x] Verify commands are runnable `uv run pytest …`, `uv run python -m fpl …`, `uv run python -m evals replay …`, or grep/od/awk from the worktree root.
- [x] No `git commit` by the executing session; the user commits in the stated split, without an attribution trailer.
- [x] No network in tests. The only network operations are the two marked data-operation commands in Task 1.9 (public endpoints, no credentials, written into `MAIN/data/raw/gw8/`).
- [x] Live evals untouched: only `evals replay` and pytest runs appear; no re-freeze.
- [x] `data/auth.json` is never read.
- [x] Order holds: `decision_commit` (0.3) before calibrate (0.6) and the drift check (1.3); `ModelConfig` (1.1) before every sweep; records (1.8) before every gate; gates run in manifest order 2 → 3 → 5.6/5.7 → 5.3–5.5, with 4.8 independent; consistency (4.1, 4.3) before `objective` (4.6) and `ep` (4.2, 4.4); 4.6 and 4.7 ship together through WB.
- [x] Compliance: no PHI or PII anywhere (synthetic test data; public FPL data in the repo); credentials never touched.
- [x] The plan lives in the repo at `docs/plans/2026-10-16-ep-form-upgrade-plan.md` (tracked); v1 and the review notes stay in the transcripts archive.
