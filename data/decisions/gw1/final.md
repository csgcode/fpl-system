# GW1 Final — initial squad (2026/27)

Deadline 2026-08-21T17:30:00Z. Review verdict: **APPROVE** (zero HIGH, five MED
accepted). Finalized from `data/decisions/gw1/squad-proposal.md` with no
selection changes.

## Freshness gate — PASS

| Check | Method | Result |
|---|---|---|
| Injury/news flags, all 15 | `fpl flags --gw 1 --ids …` refreshed 2026-08-21T14:34:24Z | Every player `status: a`, `chance_of_playing_next_round: null`, `news: ""` — zero deltas vs the analysis-time baseline in `data/raw/gw1/players-slim.csv` |
| Snapshot age | CLI staleness line: `bootstrap.json (cached, age 0.0h)` | < 24h ✓ |
| Next GW / deadline | CLI: `next GW: 1, next deadline: 2026-08-21 17:30:00+00:00` | Matches ✓ |
| Prices | `cost_change_start = 0` for all 15; Σ = £100.0m | Budget intact ✓ |

No `status`, `chance_of_playing_next_round`, or `news` value moved for any
selected player between analysis time and finalization. Gate cleared; no REOPEN.

## Squad (15) — £100.0m spent, bank £0.0m

Predicted points below are the calibration baseline: score these against
`fpl actuals --round 1` in the GW1 retro.

| # | Pos | Player | Club | Price | GW1 EP | EP6 | p_start | Unc | Role |
|---|-----|--------|------|-------|--------|-----|---------|-----|------|
| 1 | GKP | Raya | ARS | 6.0 | 4.27 | 22.43 | 0.94 | LOW | XI |
| 2 | GKP | Dubravka | TOT | 4.0 | 1.08 | 7.10 | 0.37 | HIGH | Bench (GK) |
| 3 | DEF | Gabriel | ARS | 8.0 | 5.31 | 26.92 | 0.93 | MED | XI · **Vice** |
| 4 | DEF | Tarkowski | EVE | 6.0 | 3.64 | 23.58 | 0.93 | LOW | XI |
| 5 | DEF | Richards | CRY | 5.0 | 3.55 | 22.45 | 0.88 | MED | XI |
| 6 | DEF | Thiaw | NEW | 5.0 | 3.26 | 22.34 | 0.88 | LOW | Bench 2 |
| 7 | DEF | Shaw | MUN | 4.5 | 3.41 | 17.96 | 0.90 | MED | Bench 1 |
| 8 | MID | Anderson | MCI | 6.5 | 4.43 | 25.60 | 0.90 | LOW | XI |
| 9 | MID | Mbeumo | MUN | 8.0 | 4.70 | 25.20 | 0.81 | LOW | XI |
| 10 | MID | Enzo | CHE | 7.0 | 4.00 | 23.93 | 0.81 | LOW | XI |
| 11 | MID | Ndiaye | EVE | 6.0 | 3.84 | 22.70 | 0.88 | LOW | XI |
| 12 | MID | Scott | BOU | 6.0 | 3.68 | 22.66 | 0.93 | LOW | XI |
| 13 | FWD | Haaland | MCI | 15.5 | 6.31 | 36.20 | 0.92 | LOW | XI · **Captain** |
| 14 | FWD | Thiago | BRE | 8.0 | 4.62 | 26.11 | 0.90 | MED | XI |
| 15 | FWD | Kusi-Asare | FUL | 4.5 | 0.66 | 3.99 | 0.08 | HIGH | Bench 3 |

Constraints (recomputed at finalization): 2 GK / 5 DEF / 5 MID / 3 FWD ✓ ·
Σ price £100.0m ≤ £100.0m ✓ · club counts ARS 2, MCI 2, MUN 2, EVE 2, rest ≤1
— all ≤ 3 ✓ · 15 unique players ✓.

## Starting XI — 3-5-2

| Line | Players |
|---|---|
| GK | Raya |
| DEF | Gabriel, Tarkowski, Richards |
| MID | Mbeumo, Anderson, Enzo, Ndiaye, Scott |
| FWD | **Haaland (C)**, Thiago |

Legal: 1 GK, 3 DEF ≥ 3, 5 MID ≥ 2, 2 FWD ≥ 1, 11 total ✓.

- **Captain: Haaland** — 6.31 GW1 EP, LOW uncertainty, clears the discounted
  field (LOW 1.00 / MED 0.92 / HIGH 0.80) by 1.42 over Gabriel (4.89). Tops raw
  EP in 5 of 6 GWs in the horizon.
- **Vice: Gabriel** — highest discounted EP among near-nailed starters
  (p_start 0.93); the MED discount already prices ARS's assumption-grade 53%
  GW1 clean-sheet probability against COV.

## Bench order

| Slot | Player | GW1 EP | Basis |
|---|---|---|---|
| GK | Dubravka | 1.08 | Only GK2; never intended to start |
| 1 | Shaw | 3.41 | Highest bench EP (MUN at HUL, p_start 0.90); also the auto-sub cover for a missing FWD via formation change |
| 2 | Thiaw | 3.26 | NEW home to LIV suppresses him this week only — re-derive weekly |
| 3 | Kusi-Asare | 0.66 | p_start 0.08, dead fodder, must sit last |

Shaw-over-Thiaw is fixture-driven, not a standing ranking; the weekly cycle
re-derives bench order from that GW's `ep_gw`.

## Predicted GW1 points

**54.65** = XI 48.34 + captain double 6.31. Recomputed at finalization from the
per-player GW1 EP above.

## Transfers made

None — GW1 initial squad. No chip played (a GW1 wildcard is impossible: the
bootstrap `chips` array puts set-1 wildcard/freehit at GW2–19; bboost/3xc at
GW1–19, neither wanted on a two-dead-slot bench).

## Accepted risks

Carried forward unresolved after the review. All were priced, not overlooked.

### MED-1 — Two XI starters below the 0.85 minutes threshold
Mbeumo and Enzo at p_start 0.81, decaying to 0.77 by GW4. Cup and European
calendars are absent from the snapshot, so rotation is priced rather than
predicted. Both are their club's least-rotated attacker, and first subs Shaw
(0.90) / Thiaw (0.88) are genuine starters. The tested fix (Enzo → Ampadu) lost
1.42 objective points, so no change is warranted.

### MED-2 — Dead bench: 2 of 4 bench slots non-playing
Kusi-Asare 0.08, Dubravka 0.37. Unavoidable at FWD — the position floor is
£4.5 and no £4.5 forward exceeds p_start 0.10; three tested playing-FWD3 shapes
each cost ≥1.0 objective because FWD3 never enters the projected best XI.
Consequences owned: auto-sub cover for a missing FWD routes through Shaw via
formation change, and **Bench Boost is unusable until the bench is rebuilt** —
consistent with the BB GW19 earmark. The wildcard must fix both slots.

### MED-3 — Deliberate template fades (aggregate rank-volatility position)
We hold 3 of the 8 players owned above 30%. Every fade is numerically
deliberate, and each is a differential we are choosing, not an oversight:

| Faded | Own % | Why faded |
|---|---|---|
| João Pedro (CHE) | 63.9 | A Haaland + João Pedro squad was searched and converged 1.04 objective points short |
| B.Fernandes (MUN) | 51.5 | Best Bruno squad = 315.35 vs 316.56; Haaland out-captains him every GW, so his captaincy hedge is worth ≈0 |
| Szoboszlai (LIV) | 41.7 | Enzo beats him by 2.20 EP6 at equal price |
| Calafiori (ARS) | 37.0 | Richards and Thiaw beat him on EP6, price and floor share; a third ARS defender adds correlation, not information |
| Calvert-Lewin (EVE) | 30.9 | His 21.4 EP6 would sit on the bench behind Haaland/Thiago; the shapes buying him lost ≥1.0 |
| Tzolis (ARS) | 23.3 | Largest model gap in the market; no evidence beyond CK3 duty and price, p_start 0.45, unmodelled European rotation. Revisit at GW2 on observed minutes |

Held template: Haaland 69.4, Mbeumo 37.5, Raya 37.2. Ownership parity on
Haaland is the deliberate hedge against the aggregate fade. **João Pedro's GW4
(CHE v HUL — the best fixture in the 120-fixture window) is the single week
this is most likely to bite**; he is the natural GW3–4 transfer target if
correction is wanted.

### MED-4 — Portfolio-level DefCon exposure
Six players carry material DefCon terms (Anderson, Scott, Ndiaye, Tarkowski,
Richards, Thiaw), not the one the proposal bounded. Partial reassurance: the
DEF analyst's same-season back-solve found the mapping exact at and above the
threshold — where Tarkowski/Richards/Thiaw sit — so the uncalibrated risk
concentrates in the MID mapping (Anderson, Scott). A 30%-optimistic MID mapping
costs ~4 EP6, short of the −1.21 gap to the tested premium structures, so it
does not flip the squad. **Retro-analyst must calibrate DefCon hit rates from
GW1 actuals.**

### MED-5 — GW1 EP leans on assumption-grade promoted-club ratings
Gabriel + Raya (COV H, P(CS) 53%) and Mbeumo + Shaw (HUL a, 44%) draw GW1 value
from COV/HUL/IPS ratings that `fixtures.md` states have no empirical basis.
Controls hold: these players also top the LOW/MED-uncertainty rankings on
later, evidenced fixtures. The GW3 Triple Captain earmark rests on the same
ratings — **do not pull it forward without the post-GW1–2 confirmation.**

### LOW items
- **LOW-1 (corrected here)** — the proposal's "EP6 36.20 leads the game by 8.7"
  was the gap to the next *forward* (Isak 27.46). Game-wide, Haaland leads
  B.Fernandes 30.54 by **5.66**. The operative evidence — the full-squad
  no-Haaland test at −4.27 over six GWs — is unaffected.
- **LOW-2 — Everton fixture cliff.** Tarkowski + Ndiaye peak GW5–6 (IPS H,
  HUL a) then face CHE (H), ARS (a), NEW (a) in GW7–9; MUN's tail is LEE (a),
  BOU (H), CHE (a). Plan EVE exits around GW6–7 rather than discovering them.
- **LOW-3 — Price risk, one-sided.** £0.0 bank leaves no buffer against opening
  price drops before a corrective transfer. Dubravka is the one plausible early
  faller (20.3% hedge ownership unwinds if Kinsky is confirmed TOT #1), bounded
  at £0.1 of team value. Pre-season transfer flows are zeroed, so no
  early/late timing edge existed this window.
- **LOW-4 — Cross-position scale inconsistency.** MID applied the `1/ATT_club`
  strip weighted by shrinkage weight w; DEF and FWD applied it flat. All owned
  MIDs are high-w so no squad decision flips, but `agents/player-analyst.md`
  must be fixed to one convention before GW2.

### Also carried from the proposal
Šeško (MUN, 75% shin flag) was excluded from the search pool outright — a GW1
squad must not rest on a fitness coin-flip; MUN attack exposure runs through
Mbeumo. Garner (EVE, 25%) not investable at p_start 0.22. Zero promoted-club
players held. No pick was benched or bought on FPL FDR (r = 0.633 against the
model's own λ ratings).

## Rationale summary

Single-premium skeleton: **Haaland only**. He survived a full-squad test rather
than row arithmetic — the best no-Haaland structure converged to 312.29 against
316.56 with him, a loss of 4.27 points over six GWs, because a £8.0 + £7.5
split cannot replicate the captain doubling he absorbs in 5 of 6 weeks. Bruno
Fernandes at £12.0 lost 1.21 the same way; Saka, Palmer and Isak were dominated
on EP6 per £m.

The remaining £84.5m buys breadth: eleven of the thirteen outfielders are
plausible weekly starters, so the XI flexes at zero transfer cost as fixtures
rotate (the model projects 3-5-2 in GW1/2/4/5 and 4-4-2 in GW3/6). Defence and
midfield skew to high DefCon floor-share (Tarkowski 77%, Richards 76%), which
survives a 5–8pp mapping error — the deliberate hedge against MED-4. GK is
set-and-forget: Raya at £6.0 tops the position on EP6 with p_start 0.94, and
downgrading him to fund a playing GK2 was tested and cost 3.06.

The two dead bench slots (MED-2) and the £0.0 bank (LOW-3) are the price of
maximising XI EP under the spec, and both are wildcard-repairable. Provisional
set-1 chip earmarks carried forward: **TC GW3** (Haaland home to COV, 7.72 EP —
gated on post-GW1–2 confirmation of COV's rating), **WC GW10**, **FH GW16**
(placeholder — no blank or double is visible yet), **BB GW19** (last GW before
set-1 expiry at 13:30 GMT, 2 Jan 2027, and only after the bench is rebuilt).

## STATE

```yaml
# Convention: free_transfers_banked = free transfers available at the NEXT
# (GW2) deadline. GW1 has no transfers; the first FT accrues for GW2.
gw: 1
team_id: null
team_value: 100.0
bank: 0.0
free_transfers_banked: 1
chips_used: []
transfers_made: []
```
