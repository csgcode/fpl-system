GW: 9
Deadline: 2026-10-31 11:00:00+00:00
Fetched at: 2026-10-30 16:32:56.812100+00:00
Previous GW: 8 finished=true data_checked=true
Commands run:
- bootstrap --gw 9 → (fetched)
- event-live --gw 9 --round 8 → (fetched)
- fixtures --gw 9 → (fetched)
- summaries --gw 9 --missing-past → (36 fetched, 0 cached)
- store sync --gw 9 → local
- entry --gw 9 --team-id 8455344 → (fetched)
- picks --gw 9 --team-id 8455344 --event 8 → (fetched)
- entry-history --gw 9 --team-id 8455344 → (fetched)
- slim-csv --gw 9 → local
- auth-check --gw 9 → FAIL
Coverage: players 669, no_pl_history 134, missing_past 0
Anomalies: top-level keys identical to data/raw/gw8/bootstrap.json; elements 668 → 669 (+1 player); summaries fetched 36 (unexplained, expected a few)
Errors: none
team_id: 8455344
auth: FAIL — session expired and refresh failed (token endpoint returned 400: invalid_grant — Refresh token does not exist) — re-copy credentials from browser devtools (see docs/api-write.md)
