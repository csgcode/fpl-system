# GW1 Squad Proposal — initial squad (2026/27)

Prepared 2026-08-21 for the GW1 deadline 2026-08-21T17:30:00Z.
Inputs: `data/analysis/gw1/players-{GKP,DEF,MID,FWD}.json` (corrected EP scale,
A_fix = λ_att/(1.439·ATT_club)), `data/analysis/gw1/fixtures.md`.
Objective maximized: Σ over GW1–6 of best-legal-XI EP + captain EP (doubled),
per-GW ep_gw arrays, all hard constraints recomputed independently.

## Squad (15) — £100.0m spent, bank £0.0m

| # | Pos | Player | Club | Price | EP6 | GW1 EP | p_start | Unc |
|---|-----|--------|------|-------|-----|--------|---------|-----|
| 1 | GKP | Raya | ARS | 6.0 | 22.43 | 4.27 | 0.94 | LOW |
| 2 | GKP | Dubravka | TOT | 4.0 | 7.10 | 1.08 | 0.37 | HIGH |
| 3 | DEF | Gabriel | ARS | 8.0 | 26.92 | 5.31 | 0.93 | MED |
| 4 | DEF | Tarkowski | EVE | 6.0 | 23.58 | 3.63 | 0.93 | LOW |
| 5 | DEF | Richards | CRY | 5.0 | 22.45 | 3.55 | 0.88 | MED |
| 6 | DEF | Thiaw | NEW | 5.0 | 22.34 | 3.26 | 0.88 | LOW |
| 7 | DEF | Shaw | MUN | 4.5 | 17.96 | 3.41 | 0.90 | MED |
| 8 | MID | Anderson | MCI | 6.5 | 25.60 | 4.43 | 0.90 | LOW |
| 9 | MID | Mbeumo | MUN | 8.0 | 25.20 | 4.70 | 0.81 | LOW |
| 10 | MID | Enzo | CHE | 7.0 | 23.93 | 4.00 | 0.81 | LOW |
| 11 | MID | Ndiaye | EVE | 6.0 | 22.70 | 3.84 | 0.88 | LOW |
| 12 | MID | Scott | BOU | 6.0 | 22.66 | 3.68 | 0.93 | LOW |
| 13 | FWD | Haaland | MCI | 15.5 | 36.20 | 6.31 | 0.92 | LOW |
| 14 | FWD | Thiago | BRE | 8.0 | 26.11 | 4.62 | 0.90 | MED |
| 15 | FWD | Kusi-Asare | FUL | 4.5 | 3.99 | 0.66 | 0.08 | HIGH |

Constraint audit (recomputed): 2 GK / 5 DEF / 5 MID / 3 FWD ✓ · Σ price =
£100.0m ≤ £100.0m ✓ · club counts ARS 2, MCI 2, MUN 2, EVE 2, all others ≤1 ✓ ·
15 unique players ✓.

## GW1 starting XI — 3-5-2

| Line | Players |
|---|---|
| GK | Raya |
| DEF | Gabriel, Tarkowski, Richards |
| MID | Mbeumo, Anderson, Enzo, Ndiaye, Scott |
| FWD | **Haaland (C)**, Thiago |

- Captain: **Haaland** · Vice: **Gabriel**
- Bench order: 1. Shaw → 2. Thiaw → 3. Kusi-Asare (GK bench: Dubravka)
- Predicted GW1 points: **54.7** (XI 48.34 + captain double 6.31)

Bench-order rationale: Shaw (GW1 EP 3.41, MUN at HUL, p_start 0.90) outscores
Thiaw (3.26, NEW home to LIV) this week; Kusi-Asare is dead fodder and sits
last. Thiaw over Shaw is fixture-driven only — re-derive weekly.

The XI flexes weekly at zero cost: all 13 outfielders except Kusi-Asare are
plausible starters, so each GW the best 10 by that week's EP play (model
projects 3-5-2 in GW1/2/4/5, 4-4-2 in GW3/6).

## Captaincy (GW1) — EP × certainty (LOW 1.00 / MED 0.92 / HIGH 0.80)

| Rank | Player | GW1 EP | Unc | Discounted | Gap to #1 |
|---|---|---|---|---|---|
| 1 | **Haaland** (MCI, BOU H) | 6.31 | LOW | **6.31** | — |
| 2 | Gabriel (ARS, COV H) | 5.31 | MED | 4.89 | −1.42 |
| 3 | Mbeumo (MUN, HUL a) | 4.70 | LOW | 4.70 | −1.61 |
| 4 | Anderson (MCI, BOU H) | 4.43 | LOW | 4.43 | −1.88 |
| 5 | Thiago (BRE, TOT H) | 4.62 | MED | 4.25 | −2.06 |

Haaland clears the field by 1.42 discounted points (+29%) with a LOW flag — no
volatile-ceiling trade-off exists. He also tops raw EP in 5 of 6 GWs, so he is
the default captain for the whole horizon. Vice = Gabriel: highest discounted
EP among near-nailed starters (p_start 0.93); the MED discount already prices
the promoted-club doubt in ARS's 53% GW1 CS. Bruno Fernandes (not owned, 5.66
raw) would still not out-captain Haaland.

## Heuristic audit trail

### Step 1 — premium skeleton (players > £9.0m)

| Premium | Verdict | Evidence |
|---|---|---|
| Haaland £15.5 | **KEEP** | Full-squad test, not row arithmetic: best no-Haaland squad (Isak+Thiago+João Pedro front line, seed C) converged to objective 312.29 vs 316.56 with him = **−4.27/6GW**. His EP6 36.20 leads the game by 8.7 and he supplies the doubled captain slot in 5/6 GWs; a £8.0+£7.5 split cannot replicate the doubling. |
| B.Fernandes £12.0 | **REJECT** | Best squad with Bruno (seed A) = 315.35, **−1.21** vs B. £12.0 redeployed as Mbeumo £8.0 + spread beats him; Haaland out-captains him every GW so his captaincy hedge is worth ~0. |
| Saka £9.5 / Palmer £9.5 | REJECT | Dominated: Anderson £6.5 EP6 25.60 > Saka 22.78 > Palmer 22.18 at −£3.0. |
| Isak £9.0 | REJECT | +1.35 EP6 over Thiago £8.0 for +£1.0m and a HIGH flag; the structure carrying him (C) lost by 4.27. |

Single-premium skeleton: Haaland only.

### Steps 2–4 — fill + swap pass

Search: three seeds (A: Haaland+Bruno · B: Haaland-only · C: no-Haaland),
single-swap hill climb to a local optimum each (objective = Σ GW1–6 best-XI EP
+ captain EP, budget/quota/club-limit enforced per candidate), then eight
targeted two-swap rebalances re-polished by hill climb. Full log:

| Move | ΔObj | Result |
|---|---|---|
| A iter1: Konsa → Shaw (£4.5→£4.5) | +0.30 | accepted |
| B iter1: Gomez £5.0 → Scott £6.0 | +1.37 | accepted |
| B iter2: Konsa → Shaw | +0.05 | accepted |
| C: converged from seed unchanged | — | 312.29 final |
| V1 B: Enzo→Gomez + Kusi→Calvert-Lewin (then Shaw→Alderete +0.39) | — | 315.52 — **worse than B**: DCL's 21.4 EP6 sits on the bench behind Haaland/Thiago, while the XI lost Enzo−Gomez = 3.1 |
| V2 B: Enzo→Gomez + Kusi→Woltemade (then →Mateta +1.13) | — | 315.33 — worse |
| V5 B: Enzo→Ampadu + Kusi→DCL (then Scott→Le Fée +0.19) | — | 315.14 — worse |
| V7 B: Raya→Verbruggen + Kusi→DCL | — | 313.50 — Raya downgrade costs 3.06; keep Raya |
| V9 B: Enzo→Gomez + Kusi→Mateta | — | 315.33 — worse |
| V10 A: Bruno→Semenyo + Kusi→Mateta (climbed via DCL→João Pedro +3.92, Semenyo→Mbeumo +1.73, Shaw→Alderete +0.39) | — | 315.52 — independently converged toward B's shape, still short |

Terminal condition met: no improving single swap remains on B (objective
**316.56**, £100.0m spent). Budget exhausted per spec; bank £0.0 ≤ £0.5.

### GK strategy — stated choice

Set-and-forget premium GK1, not a rotating pair: Raya £6.0 (EP6 22.43, top of
the position, p_start 0.94 LOW — ARS #1 defensive ticker, mean P(CS) 39%).
GK2 = Dubravka £4.0: the GK analyst's flagged best £4.0 body (7.10 EP6, ~6×
normal fodder) as a free option on the unresolved TOT depth chart. He is never
intended to start; if team news kills his claim, a dead £4.0 GK2 behind a 0.94
p_start GK1 costs ~nothing, and V7 shows downgrading Raya to fund a playing
GK2 loses 3.06 objective points. Rotating-pair rejected: it burns a weekly
decision + bench slot to approximate what Raya provides alone.

### Escalation calls (explicit)

| Escalation | Call |
|---|---|
| Tzolis (ARS £6.5, 23.3% owned, EP6 13.30, zero PL minutes) | **FADE.** Model gap is the largest in the market and we take the anti-template side: no hard evidence beyond CK3 duty and price; p_start 0.45; European-rotation risk unmodelled. Accepted cost: if he is nailed and returns, ~23% of the field gains on us. Partial hedge: we already own ARS's two highest-certainty assets (Raya, Gabriel). Revisit at GW2 with observed minutes. |
| Šeško (MUN £7.0, 75% shin, HIGH) | **EXCLUDED from the search pool.** A GW1 squad must not depend on a fitness coin-flip; Zirkzee inheritance (EP6 9.6) is not investable either. MUN attack exposure via Mbeumo instead. |
| Sub-£4.5 escalation-gated GKs (TOT/LEE/COV/IPS) | Avoided for GK1. Dubravka taken as GK2 only, with the risk stated above; freshness gate will re-check. |
| CRY club-limit collision | One CRY slot; DEF analyst's priority honored — Richards first (EP6 22.45, 76% floor share, best EP/£m in position). Canvot/Muñoz/Mitchell not needed. |
| Hincapie (ARS £5.5, reverse gap) | Not taken: Richards beats him on EP6 (22.45 vs 21.30), floor share (76% vs 64%) and price (−£0.5); a third ARS defender adds correlation, not information. |
| Garner (EVE £6.0, d/25%) | Not investable at p_start 0.22; EVE exposure via Tarkowski + Ndiaye. |
| Promoted-club opponents (COV/HUL/IPS assets) | Zero promoted-club players held, per fixture analyst's rule. Their opponents' inflated EP is a stated risk below. |
| FDR rule (r=0.633) | No pick was benched or bought on FPL FDR; all rankings from λ_att/λ_def and ep_gw. |

## Provisional chip plan (set 1 — windows read from bootstrap chips array)

| Chip | Earmark | One-line basis |
|---|---|---|
| Triple Captain | **GW3** | Haaland home to COV, 7.72 EP — his season-high in the visible horizon; CONFIRM after GW1–2 because COV's rating is assumption-grade. |
| Wildcard | **GW10** | Window opens GW2; hold until promoted-club ratings, depth charts and price churn resolve; pull forward on structural damage (2+ long-term injuries). |
| Free Hit | **GW16** | Placeholder — no blank/double exists in the current fixture list; held as insurance (not usable consecutively with any FH). |
| Bench Boost | **GW19** | Last GW before set-1 expiry (13:30 GMT, 2 Jan 2027); bench must be rebuilt to 4 starters via the GW10 wildcard tail or late transfers. |

One chip per GW; none used at GW1 (GW1 wildcard impossible — window starts GW2).

## Open risks

1. **DefCon calibration (dominant model risk).** Anderson carries ~30% of EP6
   from an uncalibrated DefCon mapping; Richards/Tarkowski/Thiaw also lean on
   it. Mitigation applied: DEF picks skew to high floor-share (Tarkowski 77%,
   Richards 76%) which survives a 5–8pp mapping error. Anderson bound: under
   the MID analyst's stated worst case (mapping 30% optimistic) he drops
   ~2.3 to ≈23.3 EP6, still ahead of every non-owned ≤£8.0 alternative; only
   a full DefCon wipe (≈17.9) would demote him below Dewsbury-Hall (21.04),
   whose own DefCon term would shrink in the same scenario. Bounded downside;
   retro-analyst should check DefCon hit-rates from GW1.
2. **Promoted-club assumption concentration in GW1–3 EP.** Gabriel/Raya (COV
   H), Mbeumo/Shaw (HUL a, IPS H) and the GW3 TC plan all rest on
   assumption-grade COV/HUL/IPS ratings. Squad choice is robust to it (these
   players also top LOW/MED-unc rankings on later fixtures); the TC timing is
   not — hence the GW3 confirm-gate.
3. **Dubravka may be a non-playing GK2** if TOT team news favors Kinsky.
   Accepted: Raya p_start 0.94; cost of a dead £4.0 GK2 ≈ 0.
4. **Kusi-Asare is a non-playing FWD3** (p_start 0.08). No nailed £4.0–4.5
   FWD exists in the game (position floor £4.5, all fodder), so the spec's
   nailed-bench preference is unsatisfiable at FWD; auto-sub cover for a
   missing FWD comes from Shaw (first bench, p_start 0.90) via formation
   change. Wildcard should fix this slot when the £6.0 rung clarifies.
5. **£0.0 bank** — no buffer against opening-week price drops before any
   corrective transfer; accepted to maximize XI EP per spec.
6. **Rotation caps on Mbeumo/Enzo (p_start 0.81).** Both are LOW-unc but
   cup/European rotation is priced, not predicted; freshness gate covers
   GW1 team news only.
7. **Template exposure**: fading Tzolis (23.3%) and Bruno (premium template)
   concentrates relative risk in Haaland ownership parity — mitigated by
   holding him ourselves.

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
