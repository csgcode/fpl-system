GW: 10
Deadline: 2026-11-06 18:30:00+00:00
Fetched at: 2026-11-05 19:45:04.242767+00:00
Previous GW: 9 finished=true data_checked=true
Commands run:
- bootstrap --gw 10 → (fetched)
- event-live --gw 10 --round 9 → (fetched)
- fixtures --gw 10 → (fetched)
- summaries --gw 10 --missing-past → (fetched)
- store sync --gw 10 → local
- entry --gw 10 --team-id 8455344 → (fetched)
- picks --gw 10 --team-id 8455344 --event 9 → (fetched)
- entry-history --gw 10 --team-id 8455344 → (fetched)
- slim-csv --gw 10 → local
Coverage: players 670, no_pl_history 135, missing_past 0
Anomalies: no top-level key diff vs data/raw/gw9/bootstrap.json
Errors: none
team_id: 8455344
auth: FAIL — session expired and refresh failed (no refresh token in the credentials; re-capture while logged in, see docs/api-write.md)
