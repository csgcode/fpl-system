GW: 7
Deadline: 2026-10-17 10:00:00+00:00
Fetched at: 2026-10-16 15:35:41.116161+00:00
Previous GW: 6 finished=true data_checked=true
Commands run:
- bootstrap --gw 7 → (fetched)
- fixtures --gw 7 → (fetched)
- summaries --gw 7 --shortlist → (469 fetched, 0 cached)
- entry --gw 7 --team-id 8455344 → (fetched)
- picks --gw 7 --team-id 8455344 --event 6 → (fetched, inferred: first run's header line was truncated by my output filter; the next run reports (cached, age 0.0h))
- entry-history --gw 7 --team-id 8455344 → (fetched, inferred: first run's header line was truncated by my output filter; the next run reports (cached, age 0.0h))
- prior-season --gw 7 → local
- slim-csv --gw 7 → local
Coverage: players 375, no_pl_history 94, missing_summaries 0
Anomalies: no top-level key diff vs data/raw/gw6/bootstrap.json; players 667 -> 667
Errors: none
team_id: 8455344
auth: FAIL — session expired and refresh failed (token endpoint returned invalid_grant: refresh token does not exist); re-copy credentials from browser devtools (docs/api-write.md)
