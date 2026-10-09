GW: 6
Deadline: 2026-10-10 10:00:00+00:00
Fetched at: 2026-10-09 13:31:49 UTC

Commands run:
- bootstrap → (fetched)
- fixtures → (fetched)
- summaries --shortlist → 421 fetched, 13 cached (434 shortlisted)
- slim-csv → local only
- entry --team-id 8455344 → (fetched)
- picks --team-id 8455344 --event 5 → (fetched)
- entry-history --team-id 8455344 → (fetched)
- prior-season → local only

Coverage: 348 players with prior-season rows, 86 without PL history (from prior-season stdout: players 348, no_pl_history 86, missing_summaries 0)
Anomalies: Top-level bootstrap keys identical to gw5 (no schema change). Element schema unchanged. Player count 659 → 667 (+8). Events 38. The players/ directory holds 435 summary-*.json files against 434 reported by the summaries run; the extra file is not yet reconciled (possibly a stale summary from an earlier shortlist, not investigated).

team_id: 8455344 (non-null; entry, picks, entry-history run). Entry: bank 0.0, value 998 (£99.8m). Picks at event 5: no active chip; captain element 9 (C), vice element 4 (VC).
