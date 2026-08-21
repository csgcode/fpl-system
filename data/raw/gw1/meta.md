GW: 1
Deadline: 2026-08-21T17:30:00Z
Fetched at: 2026-08-21 13:27:35.717979+00:00

Commands run:
- bootstrap --gw 1 → (fetched)
- fixtures --gw 1 → (fetched)
- summaries --gw 1 --shortlist → (fetched, 453 player summaries)
- slim-csv --gw 1 → (local)
- prior-season --gw 1 → (local, with cached summaries)

Coverage: 399 players with prior-season history, 54 with no PL history, 0 missing summaries
Anomalies: no prior snapshot

team_id: null — entry/picks/entry-history skipped

## Chip Windows (Set 1: GW1–19 | Set 2: GW20–38)

| Chip | Set | GW Range |
|---|---|---|
| Wildcard | 1 | GW2–19 |
| Wildcard | 2 | GW20–38 |
| Free Hit | 1 | GW2–19 |
| Free Hit | 2 | GW20–38 |
| Bench Boost | 1 | GW1–19 |
| Bench Boost | 2 | GW20–38 |
| Triple Captain | 1 | GW1–19 |
| Triple Captain | 2 | GW20–38 |

## Data Files Generated

- `bootstrap.json` – 600 players, 20 teams, 8 chips
- `fixtures.json` – 380 fixtures
- `players-slim.csv` – all 600 players (not filtered)
- `prior-season.json` – 399 players with historical data
- `players/` directory – 453 cached element summaries
