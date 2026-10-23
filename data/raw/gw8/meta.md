GW: 8
Deadline: 2026-10-23 17:30:00+00:00
Fetched at: 2026-10-23 09:58:20.571308+00:00
Previous GW: 7 finished=true data_checked=true
Commands run:
- bootstrap --gw 8 → (fetched)
- fixtures --gw 8 → (fetched)
- summaries --gw 8 --shortlist → 473 fetched, 0 cached
- entry --gw 8 --team-id 8455344 → (fetched)
- picks --gw 8 --team-id 8455344 --event 7 → (fetched)
- entry-history --gw 8 --team-id 8455344 → (fetched)
- slim-csv --gw 8 → local
- prior-season --gw 8 → local
- auth-check --gw 8 → FAIL (exit 1)
Coverage: players 378, no_pl_history 95, missing_summaries 0
Anomalies: bootstrap top-level keys identical to data/raw/gw7/bootstrap.json. Elements 667 → 668: one added (id 668, Tutierov, FWD, team 20), none removed.
Errors: none
team_id: 8455344
auth: FAIL — session expired and refresh failed (token endpoint returned 400: invalid_grant, refresh token does not exist); re-copy credentials from browser devtools (docs/api-write.md)
