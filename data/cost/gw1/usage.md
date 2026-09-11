# GW1 — Claude Code usage

## 1. Window

| Field | Value |
|---|---|
| Gameweek | 1 |
| Session | `62692bc5-cd9e-4ab4-961b-c3f11e08cfa1` |
| Transcripts root | `~/.claude/projects/-Users-gokul-Dev-Personal-fpl-system` |
| Start (inclusive, UTC) | 2026-08-21T13:26:43Z |
| End (exclusive, UTC) | 2026-08-21T14:40:12Z |
| Claude Code versions | 2.1.237 |
| Models | claude-fable-5, claude-haiku-4-5-20251001, claude-opus-5 |

## 2. Totals

| Metric | Value |
|---|---|
| API calls | 318 |
| Agent threads (incl. orchestrator) | 11 |
| Tool calls | 335 |
| First → last call | 2026-08-21T13:27:00.711Z → 2026-08-21T14:37:12.980Z |
| Wall-clock minutes | 70.2 |
| Active minutes (gaps capped at 5) | 70.2 |
| Input tokens (uncached) | 873 |
| Cache write 5m / 1h | 1,291,903 / 96,537 |
| Cache read | 34,174,893 |
| Output tokens | 515,808 |
| of which thinking | 214,952 |
| Peak context (one call) | 249,416 |
| Cache hit ratio | 0.961 |
| Cost $ (input / cache write / cache read / output) | 0.00 / 11.08 / 18.85 / 15.09 |
| **Cost $ total** | **45.02** |
| Uncached-equivalent $ | 211.87 |
| Saved by caching $ | 166.85 |

## 3. By model

| Model | Calls | Input | Cache write | Cache read | Output | Cost $ |
|---|---|---|---|---|---|---|
| claude-fable-5 | 53 | 106 | 325,131 | 4,320,976 | 95,467 | 13.88 |
| claude-haiku-4-5-20251001 | 32 | 301 | 70,879 | 995,711 | 9,695 | 0.24 |
| claude-opus-5 | 233 | 466 | 992,430 | 28,858,206 | 410,646 | 30.90 |

## 4. By stage

| Stage | Agents | Models | Calls | Wall min | Peak context | Output | Cost $ |
|---|---|---|---|---|---|---|---|
| orchestrator | 1 | claude-fable-5 | 23 | 70.2 | 125,460 | 28,814 | 5.57 |
| data-collector | 1 | claude-haiku-4-5-20251001 | 28 | 3.8 | 40,537 | 7,351 | 0.18 |
| fixture-analyst | 1 | claude-opus-5 | 26 | 8.9 | 96,523 | 38,322 | 2.39 |
| player-analyst | 4 | claude-opus-5 | 199 | 29.7 | 249,416 | 360,742 | 27.67 |
| squad-optimizer | 1 | claude-fable-5 | 18 | 10.5 | 109,647 | 41,058 | 4.64 |
| red-team-reviewer | 1 | claude-fable-5 | 12 | 6.7 | 133,952 | 25,595 | 3.67 |
| finalizer | 1 | claude-opus-5 | 8 | 2.4 | 62,144 | 11,582 | 0.84 |
| in-cycle patch | 1 | claude-haiku-4-5-20251001 | 4 | 0.3 | 30,358 | 2,344 | 0.06 |

## 5. By agent

Spawn order; the orchestrator first.

| Spawned | Agent | Stage | Tier → model | Calls | Wall min | Peak context | Output | Cost $ |
|---|---|---|---|---|---|---|---|---|
| - | orchestrator | orchestrator | main → claude-fable-5 | 23 | 70.2 | 125,460 | 28,814 | 5.57 |
| 2026-08-21T13:27:19.766Z | Collect GW1 raw data | data-collector | haiku → claude-haiku-4-5-20251001 | 28 | 3.8 | 40,537 | 7,351 | 0.18 |
| 2026-08-21T13:31:48.486Z | Analyze GW1 fixtures | fixture-analyst | opus → claude-opus-5 | 26 | 8.9 | 96,523 | 38,322 | 2.39 |
| 2026-08-21T13:41:40.395Z | Score GKP players GW1 | player-analyst | opus → claude-opus-5 | 33 | 15.4 | 169,653 | 69,697 | 4.54 |
| 2026-08-21T13:41:58.064Z | Score DEF players GW1 | player-analyst | opus → claude-opus-5 | 45 | 26.4 | 202,355 | 104,078 | 7.37 |
| 2026-08-21T13:42:15.277Z | Score MID players GW1 | player-analyst | opus → claude-opus-5 | 74 | 29.1 | 249,416 | 107,400 | 9.81 |
| 2026-08-21T13:42:32.039Z | Score FWD players GW1 | player-analyst | opus → claude-opus-5 | 47 | 19.6 | 182,100 | 79,567 | 5.95 |
| 2026-08-21T14:03:21.788Z | Patch player-analyst spec formula | in-cycle patch | haiku → claude-haiku-4-5-20251001 | 4 | 0.3 | 30,358 | 2,344 | 0.06 |
| 2026-08-21T14:12:15.045Z | Optimize GW1 squad | squad-optimizer | fable → claude-fable-5 | 18 | 10.5 | 109,647 | 41,058 | 4.64 |
| 2026-08-21T14:23:26.246Z | Red-team GW1 proposal | red-team-reviewer | fable → claude-fable-5 | 12 | 6.7 | 133,952 | 25,595 | 3.67 |
| 2026-08-21T14:30:40.971Z | Finalize GW1 decision | finalizer | opus → claude-opus-5 | 8 | 2.4 | 62,144 | 11,582 | 0.84 |

## 6. Prompts in window

| Time | Kind | Text |
|---|---|---|
| 2026-08-21T13:26:43Z | human | Lets do a trial run pick now. to test out the flows. |
| 2026-08-21T13:31:22Z | notification | <task-notification> <task-id>a6524e1ce93f1e1ee</task-id> <tool-use-id>toolu_01LPQdvVfENJcDq9Qt8XzW2X</tool-use-id> <output-file>/private/tmp/claude-501/-Users-… |
| 2026-08-21T13:41:05Z | notification | <task-notification> <task-id>ad78c4fe5c286cc23</task-id> <tool-use-id>toolu_01Uxp5RwZZb4mxcFeVADVQKp</tool-use-id> <output-file>/private/tmp/claude-501/-Users-… |
| 2026-08-21T13:57:36Z | notification | <task-notification> <task-id>a1c3b748b45ffdc28</task-id> <tool-use-id>toolu_01Bjk3amtLJKVsmUJi9wrMpL</tool-use-id> <output-file>/private/tmp/claude-501/-Users-… |
| 2026-08-21T14:00:33Z | notification | <task-notification> <task-id>a5ad68533eede16d4</task-id> <tool-use-id>toolu_01WpgYEW5Dr3DQgg9ibvFU1H</tool-use-id> <output-file>/private/tmp/claude-501/-Users-… |
| 2026-08-21T14:02:14Z | notification | <task-notification> <task-id>ad7006b4cbbe33161</task-id> <tool-use-id>toolu_01MMig3jweJ6TWtHpb6JMDuy</tool-use-id> <output-file>/private/tmp/claude-501/-Users-… |
| 2026-08-21T14:03:48Z | notification | <task-notification> <task-id>a6aa7287de1d9937e</task-id> <tool-use-id>toolu_01A4dbeKUgRNajUsm3zAVUZL</tool-use-id> <output-file>/private/tmp/claude-501/-Users-… |
| 2026-08-21T14:08:28Z | notification | <task-notification> <task-id>a5ad68533eede16d4</task-id> <tool-use-id>toolu_01KwHprEGCMLqSuuQKnN8Kkr</tool-use-id> <output-file>/private/tmp/claude-501/-Users-… |
| 2026-08-21T14:11:33Z | notification | <task-notification> <task-id>aee06395bd9e5450e</task-id> <tool-use-id>toolu_01Rv6JGMaH914fS7rK5VmjyH</tool-use-id> <output-file>/private/tmp/claude-501/-Users-… |
| 2026-08-21T14:23:03Z | notification | <task-notification> <task-id>ad08ff0de6edf1a2c</task-id> <tool-use-id>toolu_01JrkEEfwzo79XJ3HRwyczPc</tool-use-id> <output-file>/private/tmp/claude-501/-Users-… |
| 2026-08-21T14:30:19Z | notification | <task-notification> <task-id>a51310c842094f5cb</task-id> <tool-use-id>toolu_01N2erjskN3FZE351peTN8ji</tool-use-id> <output-file>/private/tmp/claude-501/-Users-… |
| 2026-08-21T14:36:36Z | notification | <task-notification> <task-id>a0aa8a10b6571b42e</task-id> <tool-use-id>toolu_01Syr1H6UxexqocfCkFPPf7C</tool-use-id> <output-file>/private/tmp/claude-501/-Users-… |

## 7. Pricing and method

Anthropic list price, USD per 1M tokens, as of 2026-06-24.

| Model | Input | Output | Cache write 5m | Cache write 1h | Cache read |
|---|---|---|---|---|---|
| claude-fable-5 | 10.0 | 50.0 | 12.5 | 20.0 | 1.0 |
| claude-fable-5-1 | 10.0 | 50.0 | 12.5 | 20.0 | 0.25 |
| claude-haiku-4-5 | 1.0 | 5.0 | 1.25 | 2.0 | 0.1 |
| claude-opus-5 | 5.0 | 25.0 | 6.25 | 10.0 | 0.5 |
| claude-sonnet-5 | 2.0 | 10.0 | 2.5 | 4.0 | 0.2 |

- Costs are API list-price equivalents; a subscription is not billed at these rates.
- One row per API call (message id). Claude Code writes one transcript line per content block; output tokens are the max across a call's lines.
- Subagent calls belong to the window in which the orchestrator spawned them.
- `/compact` summarisation calls are not logged in transcripts and are not counted.
- Cache hit ratio = cache read ÷ (input + cache read + cache write).
- Uncached-equivalent prices every context token at the input rate; the difference is what prompt caching saved.
