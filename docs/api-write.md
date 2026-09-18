# Authenticated write path — setup & operation

The write commands (`my-team`, `set-lineup`, `make-transfers`) talk to FPL's
**unofficial** authenticated API. It is undocumented, unversioned, and its
auth shape has already changed twice (2024, 2026/27). **Assume it will drift
again**: nothing in this repo hardcodes header or cookie names, and
`auth-check` is how you find out that the shape moved.

## 1. Capture credentials from Chrome devtools

1. Log in at https://fantasy.premierleague.com and open your team page
   (Pick Team).
2. Open devtools (Cmd+Opt+I) → **Network** tab → filter for `my-team`.
3. Reload the page and click the `my-team/{team_id}/` request.
4. Right-click it → **Copy** → **Copy as cURL**, and paste into a file in the
   repo root (`curl-request` and `*.curl` are git-ignored).
5. Import it:

```
uv run python -m fpl auth-import --curl-file curl-request
```

That writes `data/auth.json` (mode 0600, git-ignored), printing only the
source URL, key names, and value lengths. Delete the capture file afterwards —
it holds a plaintext bearer token. The command warns loudly if the capture
file is not git-ignored.

## 1a. Refreshing instead of re-capturing

A capture goes stale in **60 minutes** — that is the bearer's whole lifetime,
and you are already some way into it when you copy it. The `refresh_token`
cookie beside it lives for **months** (verified 2026-09-18: six). So a failed
`auth-check` right after a fresh import means the capture was *late*, not
malformed — do not debug the parse.

```
uv run python -m fpl auth-refresh              # mint a new bearer, rewrite data/auth.json
uv run python -m fpl auth-refresh --dry-run    # show where it would go, send nothing
```

Usually you will not need to run it at all: the write path refreshes itself.
A request refused with 401/403 triggers one refresh and one replay, so a
session that expires mid-cycle heals instead of ending the gameweek. The
refresh is **reactive only** — a working token is never spent, because each
refresh rotates the refresh token. Run `auth-refresh` by hand to check the
plumbing or to see the current expiry; re-capture only when the refresh token
itself has expired or been revoked (a browser logout revokes it).

The replay happens exactly once. A 401/403 is refused before it changes
anything, so replaying even a transfer POST cannot double-apply it — but a
second rejection surfaces rather than looping, and once a refresh has failed
it is not retried on later requests.

Everything is derived from the tokens already held, so nothing breaks when FPL
moves: the endpoint from the bearer's `iss` claim, the client id from the
client the **refresh token** was issued to. Those are two different clients —
FPL runs both in one PingOne environment, and presenting the bearer's client
id is rejected with `invalid_grant — Refresh token does not exist`. Override
either with `--token-endpoint` / `--client-id` if the shape drifts again.

The refresh token **rotates**: the server issues a new one and kills the old
on every successful call, so `auth-refresh` persists it immediately and an
older copy of `data/auth.json` is *not* a working fallback.

The destination is allow-listed to `premierleague.com` and `pingone.eu`
(`ALLOWED_ENDPOINT_DOMAINS` in `fpl/refresh.py`). The endpoint is read from an
unverified JWT claim, so it is untrusted input to a request carrying a
months-long credential; widen that list deliberately or not at all.

`auth-import` is the fast path. Editing `data/auth.json` by hand — copy
`data/auth.example.json` and paste values from devtools — is the fallback when
"Copy as cURL" is unavailable or the capture will not parse.

### What the 2026/27 session looks like

| Kind | Names |
|---|---|
| Auth headers | `x-api-authorization` (Bearer JWT), `x-api-language` |
| Browser fingerprint headers | `user-agent`, `accept`, `accept-language`, `referer`, `origin`, `priority`, `cache-control`, `pragma`, `sec-ch-ua*`, `sec-fetch-*` |
| Session cookies | `datadome`, `cf_clearance` (Cloudflare), `global_sso_id`, `pl_guest_id`, `req_language` |
| Analytics cookies | `AMCV_*`, `kndctr_*`, `s_nr` — kept verbatim; harmless, and dropping them changes the fingerprint |

`pl_profile` is **gone** — it was the 2024 shape. If you find it in an old
`data/auth.json`, re-capture.

`auth-import` drops two classes of header:

- **Transport** — `cookie` (split into the cookies map instead),
  `content-length`, `host`, `connection`, `accept-encoding`, `content-type`,
  `te`, `trailer`, `transfer-encoding`, `upgrade`. requests/urllib3 must own
  these per request; a replayed value contradicts the actual request.
- **Per-request tracing** — `baggage` and `sentry-trace`. These carry a single
  request's Sentry trace id. Replaying one capture's trace id on every
  subsequent call is wrong, and a frozen trace id is a fingerprint.

HTTP/2 pseudo-headers (`:authority`, `:method`, `:path`, `:scheme`) are
dropped too — they are not headers.

The schema itself stays data-driven: **whatever** headers and cookies the file
contains are injected verbatim on every request. If FPL changes its auth shape
again, capture the new request the same way — no code change needed.

## 2. Verify the session

```
uv run python -m fpl auth-check --gw N [--team-id <id>]
```

The pre-flight. It reports which credential keys are loaded (names and value
lengths only, never values), then performs one authenticated `my-team` read.

| Exit | Meaning |
|---|---|
| 0 | `PASS` — prints entry id, squad size, bank, team value, free transfers, available chips |
| 1 | `FAIL` — session expired (401/403), another HTTP/network error, missing `data/auth.json`, or a null `team_id` |

Because the exit code is meaningful, it gates a shell cycle:

```
uv run python -m fpl auth-check --gw 5 || echo "re-capture credentials"
```

An informational warning appears when no `authorization`-like header is
present. It is advice, not a gate — the schema is data-driven, so an
unfamiliar header name may still be the right one.

`team_id` defaults from `data/entry.json` when `--team-id` is omitted.
`uv run python -m fpl my-team --gw N` remains the fuller read: the squad table
with per-player sell prices.

## 3. Token expiry and shape drift

Browser sessions expire (typically after weeks), but `datadome` and
`cf_clearance` rotate much faster — days, sometimes hours. On any 401/403 the
CLI prints:

> session expired — re-copy credentials from browser devtools (see docs/api-write.md)

Repeat step 1. Credential values are never printed, logged, or written
anywhere by the tooling — the error is always this generic message.

Run `auth-check` before each gameweek cycle. A `FAIL` that persists after a
fresh capture means the auth shape itself moved: compare the live request's
headers and cookies against the table above and update
`data/auth.example.json` and this section.

## 4. Dry-run first, `--apply` to execute

Both write commands default to a **dry run**: they print the exact payload
that would be POSTed and send nothing.

- `set-lineup` (XI, captain, vice, bench order, optional chip) is reversible
  until the deadline, so running it with `--apply` needs no extra ceremony.
- `make-transfers` is **irreversible** and can burn points. `--apply` is the
  user-confirmation gate: agents run the dry run and hand the payload to the
  user; only the user decides to re-run with `--apply`. Nothing in the system
  auto-applies transfers.

### Order: transfers, then the lineup

A lineup may only name players the entry owns, so a plan's incoming players
must land before the XI referencing them can be set. `set-lineup` reads the
live squad first and refuses with `lineup names N player(s) not in the squad`
rather than letting the server reject the whole payload for an opaque reason.

Run `make-transfers` first every gameweek, including ones with no transfers —
the diff comes back empty, it prints "already applied" and sends nothing. If
the user declines the transfers, the lineup step is blocked too whenever the
plan's XI depends on them; that is a reported outcome, not a bug to route
around.

### Chip routing

The site plays bench boost and triple captain when saving the lineup, and
wildcard and free hit when confirming transfers. A chip sent to the other
endpoint is accepted and never activates, so each command carries the plan's
single `chip` only when it owns it:

| `chip` | `make-transfers` sends | `set-lineup` sends |
|---|---|---|
| `null` | `null` | `null` |
| `bboost`, `3xc` | `null` + a `note:` | the chip |
| `wildcard`, `freehit` | the chip | `null` + a `note:` |

An unrecognised chip name refuses rather than being dropped — a silently
omitted chip is indistinguishable from a write that played it. A transfer chip
on a gameweek with no transfers left to make also refuses, because the POST
that would activate it never happens; it is allowed only when the chip is
already active, which is what re-running an applied gameweek looks like.
`apply_transfers` and `apply_lineup` both verify after writing that the chip
came back active.

Payload sources, in order of preference:

| Flag | Source | Notes |
|---|---|---|
| `--from-plan data/decisions/gw{N}/plan.json` | the execution plan | **the default path.** Carries picks, chip and planned prices. Refuses if `schema_version` is not 1 or the plan's `gw` is not `--gw` |
| `--from-final data/decisions/gw{N}/final.md` | the STATE block's `picks:` list | fallback for a gameweek with no plan. No chip, no drift check |
| `--picks`/`--captain`/`--vice`, `--out`/`--in` | explicit ids | manual override |

`--from-plan` and `--from-final` are mutually exclusive. In both cases
transfers are computed as the diff between the *current live squad* and the
target 15 — that is what makes the command idempotent and safe to re-run.
`--chip` may only restate what the plan already says; a contradiction refuses.

Build the plan first (local-only, no network, no credentials):

```
uv run python -m fpl plan --gw N --out data/decisions/gw{N}/plan.json
```

## 4b. Prices: the one place plan.json is deliberately not authoritative

plan.json is the single source for everything a POST needs — element ids,
slots, captain, chip — with two exceptions, marked in the file by
`"price_resolution": "live"`:

| Field | Why it cannot be frozen |
|---|---|
| `selling_price` (always `null`) | The sell price is per-entry, not per-player: it encodes your own purchase price and FPL's 50%-of-profit rounding rule. It exists only in the authenticated `my-team` read. A number copied into a plan file would be wrong for anyone, and wrong for you the moment a price moves |
| `purchase_price_at_plan` | Bootstrap's `now_cost` changes overnight. The value in the plan is a snapshot taken when the plan was built, for audit, not for posting |

So at POST time the CLI always re-resolves both — selling price from
`my-team`, purchase price from the live bootstrap — and the plan's numbers are
only used to detect movement:

- **Warn** when a live purchase price differs from `purchase_price_at_plan`:
  `price drift: element 68 planned at £6.0m, now £6.2m`. Informational; the
  dry run still prints the payload.
- **Refuse** when the live prices no longer fit the bank. The message names
  the shortfall and both totals. Re-run `bootstrap` and `plan`, then retry —
  never edit the plan by hand to make the arithmetic work.

The bank gate only applies on the `--from-plan` path, where a planned price
exists to compare against. Explicit `--out`/`--in` stays the operator's call,
with the FPL server as the authority.

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
