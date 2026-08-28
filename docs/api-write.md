# Authenticated write path — setup & operation

The write commands (`my-team`, `set-lineup`, `make-transfers`) talk to FPL's
**unofficial** authenticated API. It is undocumented, unversioned, and its
auth shape has changed before (2024). **Before first use each season — and
before the GW2 cycle — confirm the current auth shape against the live site**
using the capture steps below and verify with a `my-team` read.

## 1. Capture credentials from Chrome devtools

1. Log in at https://fantasy.premierleague.com and open your team page
   (Pick Team).
2. Open devtools (Cmd+Opt+I) → **Network** tab → filter for `my-team`.
3. Reload the page and click the `my-team/{team_id}/` request.
4. In **Request Headers**, find the auth-bearing entries. As of the 2024
   change these are typically:
   - header `X-Api-Authorization: Bearer …`
   - cookies `pl_profile` and `datadome` (from the `Cookie` header, or the
     Application tab → Cookies)
5. Copy `data/auth.example.json` to `data/auth.json` and paste the values in.
   The file is git-ignored — never commit it, never paste its contents into
   chat, tickets, or logs.

The schema is data-driven: **whatever** headers and cookies the file contains
are injected verbatim on every request. If FPL changes its auth shape again,
capture the new headers/cookies the same way and put them in the file —
no code change needed.

```json
{
 "headers": {"X-Api-Authorization": "Bearer …"},
 "cookies": {"pl_profile": "…", "datadome": "…"}
}
```

## 2. Verify the session

```
uv run python -m fpl my-team --gw N --team-id <id>
```

A squad table with bank, sell prices, and chip states means the session works.
`team_id` defaults from `data/entry.json` when `--team-id` is omitted.

## 3. Token expiry

Browser sessions expire (typically after weeks, but `datadome` can rotate much
faster). On any 401/403 the CLI prints:

> session expired — re-copy credentials from browser devtools (see docs/api-write.md)

Repeat step 1. Credential values are never printed, logged, or written
anywhere by the tooling — the error is always this generic message.

## 4. Dry-run first, `--apply` to execute

Both write commands default to a **dry run**: they print the exact payload
that would be POSTed and send nothing.

- `set-lineup` (XI, captain, vice, bench order, optional chip) is reversible
  until the deadline, so running it with `--apply` needs no extra ceremony.
- `make-transfers` is **irreversible** and can burn points. `--apply` is the
  user-confirmation gate: agents run the dry run and hand the payload to the
  user; only the user decides to re-run with `--apply`. Nothing in the system
  auto-applies transfers.

Payload sources: `--from-final data/decisions/gw{N}/final.md` (the STATE
block's `picks:` list; transfers are computed as the diff between the current
squad and that target), or explicit flags (`--picks`/`--captain`/`--vice`;
`--out`/`--in`).

## 5. Guard rails

- **Deadline gate**: writes refuse when the GW deadline (from the cached
  bootstrap) has passed, or is under 30 minutes away. `--force-deadline`
  overrides the 30-minute margin only — never a passed deadline.
- **Idempotency**: if the requested state is already live, the command prints
  "already applied" and sends nothing.
- **Verify-after-write**: after every `--apply` the squad is re-read and
  compared against the intent; a mismatch exits non-zero.
- **No POST retries**: retries are pinned to GET — a retried POST could
  double-apply a transfer.
- **Audit trail**: every `--apply` writes a timestamped record (payload +
  verification result, never credentials) under `data/executor/gw{N}/`.
  Authenticated responses are never cached into `data/raw/`.
- **Selling prices** always come from the authenticated `my-team` read;
  bootstrap's `now_cost` is the buy price, not ours.
