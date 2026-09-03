# GW3 Squad Proposal — weekly cycle (2026/27)

Deadline 2026-09-04T17:30:00Z. Horizon GW3–GW8. Not a revision loop.

Inputs: `data/analysis/gw3/players-{GKP,DEF,MID,FWD}.json` (+ .md), `fixtures.md`
/ `fixtures.json`, `data/raw/gw3/players-slim.csv` + targeted bootstrap reads
(prices, transfer pressure), `data/retro/gw1.md`, `data/retro/gw2.md`
(Corrections, Carried into GW3), STATE block of `data/decisions/gw2/final.md`.
All EP figures are the code's `ep_gw` / `ep_total6`; nothing is recomputed.

## Decision in one line

**One free transfer: Kusi-Asare (FUL, 4.5) → Barry (EVE, 5.5). Hit 0. Bank
£0.0m. 3-4-3, Haaland (C), Mbeumo (V). Predicted GW3 56.49. No chip.**

## 0. State read

| Item | Value | Source |
|---|---|---|
| Squad | the 15 in GW2's `picks:` — confirmed identical to `picks-8455344-e2.json` (Enzo → Tavernier applied, 0 cost) | `data/raw/gw3/picks-8455344-e2.json` |
| Sell value / bank | £98.9m / £1.0m; entry shows `bank 10, value 999` — the paper convention and the real entry agree | `entry-8455344.json`, `entry-history` |
| Free transfers at this deadline | 1 | GW2 STATE `free_transfers_banked: 1` |
| Chips used | none (`chips: []`) | `entry-history` |
| Set-1 windows | wildcard 2–19, freehit 2–19, bboost 1–19, 3xc 1–19 | bootstrap `chips` |
| Squad price moves since GW2 | none (all 15 `cost_change_event 0`; Anderson still 6.4) | bootstrap |
| **Club change** | **Ndiaye is now MCI** (deadline-day move). MCI = Haaland, Anderson, Ndiaye = **3, at the cap**. Every MCI-in single (Guéhi 30.37, Cherki 30.68, Foden 27.43, O'Reilly, Gvardiol) is illegal without an MCI-out | players-slim.csv |
| EVE count | 1 (Tarkowski) — Barry takes it to 2, not the 3 GW2 projected | — |

Pricing convention unchanged from GW2: sell = purchase price, lower-bounded by
current price on drops, purchase + floor(rise/2) on rises. No `data/auth.json`,
so no authenticated selling prices exist; every squad price is flat this week so
the convention has nothing to adjudicate.

## 1. Premium skeleton — re-tested, not just re-affirmed

Single premium, Haaland (15.5). GW1's test found the best no-Haaland structure
−4.27 over six GWs. Re-run on GW3 numbers against the post-Barry squad, scoring
Σ(best legal XI + captain) over GW3–8 for every "Haaland → FWD X plus one more
sale → B.Fernandes" pair the budget allows:

| Restructure (2 transfers, −4) | Gross 6-GW | Net of hit | Bank | Per-GW delta GW3→8 |
|---|---:|---:|---:|---|
| Haaland → Isak + Scott → B.Fernandes | **+9.74** | **+5.74** | 0.5 | +1.10 +1.61 +1.50 +2.87 **−0.98** +3.64 |
| Haaland → Isak + Anderson → B.Fernandes | +9.50 | +5.50 | 0.9 | +1.04 +1.61 +1.50 +2.87 −1.05 +3.53 |
| Haaland → João Pedro + Scott → B.Fernandes | +8.89 | +4.89 | 1.8 | −0.08 +1.69 +0.92 +3.59 −0.75 +3.52 |
| Haaland → Wissa + Scott → B.Fernandes | +7.14 | +3.14 | 3.4 | +0.52 −0.01 +1.80 +3.02 −0.88 +2.70 |
| Haaland → Isak alone | −8.76 | −8.76 | 6.5 | — |

**The model now prefers the split.** B.Fernandes' EP6 (38.06) exceeds
Haaland's (36.40) outright — their attack terms are equal (18.0 vs 18.2) at
£3.5m apart — and the released cash upgrades a benched Scott into a starter.
The gross clears the hit rule (≥ 6). **I am not making it this week**, and the
reasons are process, not EP:

1. **It is the flagged band.** The retro's largest open calibration item is
   the ≥ £8.0m band: bias **+5.67 per appearance on n = 11**, "outlier-robust,
   withheld on power", with C10 (the GW4 ledger) as its instrument. Both sides
   of this trade sit in that band. If the under-prediction is flat across the
   band the trade is as good as it looks; if it scales with ceiling, Haaland is
   the more under-predicted of the two and the +1.6/GW edge is inside the
   error. Restructuring the skeleton on those numbers is acting on the very
   sample the retro withheld.
2. **It is the LOW-4 pattern.** B.Fernandes (25 pts, 2.10 xG + 0.74 xA in
   180') and Isak are this season's top-two-round scorers; LOW-4 assigns the
   recency-chasing test to the GW4 retro. A hit-taking premium move toward the
   last-two-GW leader is exactly what that test watches.
3. **Deferral is nearly free.** GW4 also has exactly 1 FT, so the hit cost is
   identical next week. Waiting forfeits only GW3's own delta (+1.10 on the
   Isak version, −0.08 on the João Pedro version) and gains a third round of
   premium data plus the C10 ledger. Haaland's GW3 (COV H, λ_att 2.42, 6.39)
   is also the fixture where selling him hurts most.
4. **Chips survive the wait.** If the restructure is made at GW4, the Triple
   Captain earmark migrates to Fernandes (GW6 TOT H 6.79, GW8 BOU H 6.80 —
   both above Haaland's GW5 6.29 in the model). Nothing chip-side is lost by
   deciding at GW4 rather than GW3.

**Carried to GW4 as the headline decision.** Make it at GW4 if (a) the C10
ledger shows the ≥ £8.0m bias is not concentrated in Haaland, and (b) the
Fernandes-over-Haaland EP6 lead survives round 3. Otherwise re-affirm Haaland.

Note the ownership asymmetry for the reviewer: Haaland 71.2%, B.Fernandes
48.6%, Isak 16.6%. Selling the 71% player is the season's largest
rank-variance decision; the objective is points, not rank, but the reviewer
should price it explicitly.

## 2. Transfer decision — swap pass (audit trail)

Metric: **realized** = Σ over GW3–8 of (best legal XI EP + captain EP) with
the player in, minus the same without. **Raw** = EP6 delta of the two players.
**Cover** = expected auto-sub value of the resulting bench, modelled as
P(k XI outfielders record 0 minutes) ≈ Poisson(Σ 0.65·(1 − p_start)) against
bench EP-if-plays (`ep_gw / p_start`) in bench order. Base squad cover = 11.68
over six GWs. Kusi-Asare is unscored (0 minutes, excluded from the analysis
pool) and enters as 0.

Every legal single transfer within budget (sell + £1.0m) and the 3-per-club
cap was scored. Top of the list:

| Out → In | Club | £ | p_start | Unc | Realized | Raw | Cover Δ | Realized + cover | Bank after |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| Shaw → De Cuyper | BHA | 4.7 | 0.86 | LOW | **+4.02** | +10.98 | +1.64 | **+5.66** | 0.8 |
| Scott → Szoboszlai | LIV | 7.0 | 0.93 | LOW | +3.14 | +3.15 | 0 | +3.14 | 0.0 |
| Richards → De Cuyper | BHA | 4.7 | 0.86 | LOW | +2.84 | +2.97 | ~0 | +2.84 | 1.3 |
| Shaw → Collins | BRE | 5.5 | 0.90 | LOW | +2.84 | +9.27 | ~+1.6 | ~+4.4 | 0.0 |
| Scott → Schade | BRE | 6.0 | 0.92 | LOW | +2.83 | +2.83 | 0 | +2.83 | 1.0 |
| Shaw → Hall | NEW | 5.1 | 0.90 | LOW | +2.76 | +9.80 | ~+1.6 | ~+4.4 | 0.4 |
| Anderson → Foden | MCI | 7.0 | 0.86 | LOW | +2.43 | +2.43 | 0 | +2.43 | 0.4 |
| Tarkowski → De Cuyper | BHA | 4.7 | 0.86 | LOW | +2.31 | +2.38 | ~0 | +2.31 | 2.3 |
| Thiago → Isak | LIV | 9.0 | 0.91 | LOW | +1.92 | +1.91 | 0 | +1.92 | 0.0 |
| **Kusi-Asare → Barry** | **EVE** | **5.5** | **0.88** | **LOW** | **+1.84** | **+25.40** | **+2.53** | **+4.37** | **0.0** |
| Shaw → Ajer | BRE | 4.5 | 0.88 | LOW | +1.38 | +6.81 | ~+1.5 | ~+2.9 | 1.0 |
| Thiago → João Pedro | CHE | 7.7 | 0.89 | LOW | ~+0.7 | +0.75 | 0 | ~+0.7 | 1.3 |
| Raya → Trafford | LEE | 5.0 | 0.95 | LOW | +0.49 | +0.49 | 0 | +0.49 | 2.0 |
| Dubravka → Leno | FUL | 4.5 | 0.95 | LOW | ~+0.1 | +17.45 | ~+0.9 | ~+1.0 | 0.5 |

Two-transfer combinations (one FT + one hit, gross must be ≥ 6):

| Pair | Gross | Net (−4) | Bank |
|---|---:|---:|---:|
| Shaw → De Cuyper + Scott → Schade | +6.74 | +2.74 | 0.8 |
| Shaw → De Cuyper + Anderson → Foden | +6.44 | +2.44 | 0.2 |
| Barry + Tarkowski → De Cuyper | +4.14 | +0.14 | 1.3 |
| Barry + Scott → Schade | +4.05 | +0.05 | 0.0 |
| Barry + Shaw → Ajer | +3.22 | −0.78 | 0.0 |
| Barry + Shaw → De Cuyper | **unfundable** (needs £1.2m, bank £1.0m) | — | — |

### Chosen: Kusi-Asare → Barry, free

- **Threshold.** XI-only realized is +1.84 — below the 2.0 bar on its own. It
  clears on the honest total, +4.37 with cover, because this is the move that
  converts the dead FWD bench slot (0 minutes, three GWs running — MED-B) into
  a 0.88-p_start starter: the 3-4-3 it enables gains +0.36 in GW3 alone
  (Barry 4.41 over Scott 4.05) and pushes Scott (4.4 EP-if-plays) to first
  sub, where the base squad had Thiaw then Shaw then nothing.
- **Structural, not form.** Barry's 0.72 → 0.88 p_start is Beto's sale to
  Fiorentina (2 Sep) — Everton have no other senior forward. His rates are
  prior-blended (`prior_weight 0.80`, 1898 prior minutes); the 10 points in
  two GWs are not the driver. Recorded for LOW-4: the earmark predates his
  GW2 points (it was written in GW2's final.md off his GW1 start).
- **Sequencing beats De Cuyper.** Shaw → De Cuyper scores higher (+5.66) but
  leaves bank £0.8m, so Kusi-Asare (4.5) can then afford only £5.3m — Barry is
  gone for good at this budget and the FWD slot stays dead. Barry first keeps
  the DEF upgrade open at GW4 (Tarkowski → De Cuyper frees £1.3m; Shaw →
  Ajer/Justin is fundable at 4.5). De Cuyper is also the pool's hottest
  recency signal (17 pts, 599k transfers in this event, already +0.1) —
  buying him on a hit-free FT is fine, buying him instead of the flagged
  bench fix is LOW-4 territory.
- **Szoboszlai (+3.14) rejected** on the ticker rule: LIV's attack falls
  −1.24 Σλ_att after GW5 ("a GW3–5 hold, not a GW3–8 one"), GW3 IPS(A) is
  banded, and in the Barry squad his displaced player is Tavernier (4.34),
  not Scott, so his realized gain shrinks to ≈ +1.4.
- **No second transfer.** No pair including Barry reaches gross 6; the best
  (Tarkowski → De Cuyper, +4.14 gross) nets +0.14 — noise for a −4 that also
  spends the GW4 FT's best candidate.
- **Band exposure.** Barry's largest term is attack (12.1). EVE's banded rows
  are GW5 IPS(H)± and GW6 HUL(A)±, attacking-side only; C12 lifts the C4
  prohibition for attacking terms. No defensive term of any selected player
  has a banded fixture as its largest component.

### MED-D — funding headroom, executed as written

Barry is **5.5** in the GW3 snapshot (`cost_change_event 0`), so the GW2 plan
executes exactly: 1.0 + 4.5 = 5.5, bank £0.0m. Pressure persists — transfers
in 143,648 vs out 68,469 this event at 4.5% ownership — so a rise to 5.6
before 17:30Z on 4 Sep strands it. Kusi-Asare is net −7k (48k in / 55k out),
no drop risk this week.

**Fallback if Barry is ≥ 5.6 at execution: bank the FT** — one of the three
options GW2 named. With 2 FTs at GW4, Kusi-Asare → Barry + Raya → Trafford
(+0.49 EP6 in its own right, frees £1.0m) funds Barry at 5.6 hit-free. The COV
pair GW2 named first is **retired on evidence, not re-litigated**:
Thomas-Asante lost the start to Awoniyi (p_start 0.45) and Simms is unscored.
Deferring Barry one GW costs ≈ 0.7 EP (0.36 XI + ~0.4 cover); a HIGH-tagged
HUL forward (McBurnie 19.43, all six rows banded) would fill the slot for
less and need fixing again.

## 3. Squad (15) — sell value £99.9m + bank £0.0m = team value £99.9m

| # | Pos | Player | Club | £ | GW3 EP | EP6 | p_start | Unc | Role |
|---|---|---|---|---:|---:|---:|---:|---|---|
| 1 | GKP | Raya | ARS | 6.0 | 3.12 | 21.39 | 0.95 | LOW | XI |
| 2 | GKP | Dubravka | TOT | 4.0 | 0.18 | 1.10 | 0.05 | HIGH | Bench GK |
| 3 | DEF | Gabriel | ARS | 8.0 | 4.46 | 29.40 | 0.93 | LOW | XI |
| 4 | DEF | Richards | CRY | 5.0 | 4.06 | 22.96 | 0.90 | LOW | XI |
| 5 | DEF | Tarkowski | EVE | 6.0 | 3.73 | 23.55 | 0.92 | LOW | XI |
| 6 | DEF | Thiaw | NEW | 5.0 | 3.56 | 22.79 | 0.88 | LOW | Bench 2 |
| 7 | DEF | Shaw | MUN | 4.5 | 2.39 | 14.95 | 0.85 | MED | Bench 3 |
| 8 | MID | Mbeumo | MUN | 8.0 | 5.27 | 31.58 | 0.91 | LOW | XI · **Vice** |
| 9 | MID | Ndiaye | MCI | 6.0 | 4.84 | 27.31 | 0.92 | LOW | XI |
| 10 | MID | Anderson | MCI | 6.4 | 4.39 | 25.00 | 0.90 | LOW | XI |
| 11 | MID | Tavernier | BOU | 6.0 | 4.34 | 25.88 | 0.92 | LOW | XI |
| 12 | MID | Scott | BOU | 6.0 | 4.05 | 24.13 | 0.92 | LOW | Bench 1 |
| 13 | FWD | Haaland | MCI | 15.5 | 6.39 | 36.40 | 0.93 | LOW | XI · **Captain** |
| 14 | FWD | Thiago | BRE | 8.0 | 5.10 | 29.13 | 0.92 | LOW | XI |
| 15 | FWD | **Barry** | EVE | 5.5 | 4.41 | 25.40 | 0.88 | LOW | XI · **IN** |

Constraints: 2 GK / 5 DEF / 5 MID / 3 FWD ✓ · Σ price 99.9 ≤ 98.9 + 1.0 ✓ ·
club counts MCI 3, ARS 2, MUN 2, BOU 2, EVE 2, NEW 1, CRY 1, BRE 1, TOT 1 —
all ≤ 3 ✓ · 15 unique ✓ · Shaw's MED is the only non-LOW outfielder and he
is 15th on GW3 EP.

Bench GK strategy: one playing keeper (Raya) plus a £4.0m non-player, held by
necessity. A playing £4.5m GK2 is worth ≈ 0.9 EP6 realized behind a 0.95
Raya — the lowest-value repair in the squad, so it stays last in the queue
(GW5 via the Tarkowski → De Cuyper cash, or the wildcard).

## 4. Starting XI — 3-4-3

| Line | Players |
|---|---|
| GK | Raya |
| DEF | Gabriel, Richards, Tarkowski |
| MID | Mbeumo, Ndiaye, Anderson, Tavernier |
| FWD | **Haaland (C)**, Thiago, Barry |

Legal: 1 GK, 3 DEF, 4 MID, 3 FWD ✓. GW3 EP ranking of the 13 outfielders is
Haaland 6.39, Mbeumo 5.27, Thiago 5.10, Ndiaye 4.84, Gabriel 4.46, Barry 4.41,
Anderson 4.39, Tavernier 4.34, Richards 4.06, Scott 4.05, Tarkowski 3.73,
Thiaw 3.56, Shaw 2.39. The raw top ten hold only two defenders, so the third
DEF slot is formation-forced; the question is who sits for him.

| Boundary | Gap | Rule | Call |
|---|---:|---|---|
| Barry 4.41 (in) vs Scott 4.05 (out) — 3-4-3 vs 3-5-2 | 0.36 | > 0.25, EP decides | 3-4-3, +0.36 |
| Tarkowski 3.73 vs Thiaw 3.56 for DEF 3 | 0.17 | ≤ 0.25 → **C8** DefCon floor share | Tarkowski: dc 5.8 / 23.55 = 25% vs Thiaw 4.3 / 22.79 = 19%; also leads raw EP |

Recorded for the GW4 C8 verdict (n → 3): boundary pair this GW is **Barry
(started) / Scott (benched)**, gap 0.36.

Six-GW horizon of the chosen squad (best legal XI per GW; captain = highest EP
in the XI):

| GW | Formation | XI EP | Captain | Total | Benched outfield |
|---:|---|---:|---|---:|---|
| 3 | 3-4-3 | 50.10 | Haaland 6.39 | 56.49 | Scott, Thiaw, Shaw |
| 4 | 3-4-3 | 48.66 | Haaland 5.73 | 54.39 | Scott, Thiaw, Shaw |
| 5 | 3-4-3 | 51.86 | Haaland 6.29 | 58.15 | Scott, Richards, Shaw |
| 6 | 3-4-3 | 50.40 | Mbeumo 5.68 | 56.08 | Scott, Richards, Shaw |
| 7 | 3-4-3 | 50.30 | Haaland 6.67 | 56.97 | Scott, Tarkowski, Shaw |
| 8 | 3-5-2 | 49.26 | Mbeumo 5.69 | 54.95 | Barry, Thiaw, Shaw |
| Σ | | | | **337.04** | base squad 335.20 |

## 5. Captaincy

certainty: LOW 1.00 / MED 0.92 / HIGH 0.80.

| Rank | Player | Fixture | GW3 EP | Unc | × certainty | Band |
|---:|---|---|---:|---|---:|---|
| 1 | **Haaland** | MCI v COV (H) | 6.39 | LOW | **6.39** | ± attacking (COV DEFW 1.11 ± 15pp) |
| 2 | Mbeumo | EVE v MUN (A) | 5.27 | LOW | 5.27 | none |
| 3 | Thiago | BRE v SUN (H) | 5.10 | LOW | 5.10 | none |
| 4 | Ndiaye | MCI v COV (H) | 4.84 | LOW | 4.84 | ± attacking |
| 5 | Gabriel | ARS v CHE (H) | 4.46 | LOW | 4.46 | none |

- **Captain: Haaland.** Clears the field by 1.12 discounted. Band check: at
  COV's DEFW floor (0.96) MCI's λ_att falls 2.42 → 2.08 (−14%); scaling
  Haaland's ≈ 3.4 GW3 attack term by 0.86 gives ≈ 5.9, still 0.6 above
  Mbeumo. The pick is robust to the whole band, and the C4 residual does
  not apply — it is an attacking term and C12 governs.
- **Vice: Mbeumo.** Second on discounted EP, band-free fixture, so GW2's
  MED-A (vice on a ± fixture) does not recur. The vice fires only if Haaland
  logs zero minutes (≲ 5%).

## 6. Bench order

| Slot | Player | GW3 EP | Basis |
|---|---|---:|---|
| 12 (GK) | Dubravka | 0.18 | only GK2; dead slot, repair queued behind the FWD fix |
| 13 | Scott | 4.05 | highest bench EP; covers any MID or FWD absence (3-5-2 / 3-4-3 stay legal). A DEF absence skips him to Thiaw automatically |
| 14 | Thiaw | 3.56 | gap to Scott 0.49 > 0.25 — EP orders; the DEF cover |
| 15 | Shaw | 2.39 | MED (0.85), gap 1.17 — last |

## 7. Predicted GW3 points

**56.49** = XI 50.10 + captain double 6.39. Recompute at finalization from the
per-player GW3 EP above (Raya 3.123, Gabriel 4.455, Richards 4.064, Tarkowski
3.731, Mbeumo 5.265, Ndiaye 4.840, Anderson 4.393, Tavernier 4.339, Haaland
6.388, Thiago 5.098, Barry 4.408).

## 8. Chips — none played this GW (`chip: null`)

### C5 — GW3 Triple Captain gate

Not activated. The fixture analyst shows the gate is clearable on arithmetic
(COV-dependent share of MCI's λ_att is 10.3%; nine-tenths is City's own
rating plus home advantage) — but clearing the gate is not the decision. The
TC's marginal value is one extra Haaland: GW3 6.39 against GW5 (SUN H,
band-free) 6.29, **+0.10 EP for accepting a ±15% band whose floor (≈ 5.9)
sits below the GW5 central estimate**. Hold GW5, as GW2 earmarked. GW7 IPS(H)
6.67 is the model's best of the three but is banded and IPS's attack rating
just rose +0.15; re-derive when the band lifts after GW3 (promoted clubs
reach three played fixtures).

### Plan (set 1, windows from bootstrap `chips`)

| Chip | Window | Earmark | Status | Justification |
|---|---|---|---|---|
| 3xc | GW1–19 | **GW5** — MCI v SUN (H), Haaland 6.29 | provisional | Band-free; GW3 offers +0.10 for a ±15% band. If the GW4 premium restructure goes ahead, migrates to Fernandes GW6 TOT(H) 6.79 / GW8 BOU(H) 6.80 |
| wildcard | GW2–19 | **GW8** | provisional | EVE defensive cliff from GW7 (Tarkowski 3.36 / 3.26), LIV/NFO swings land GW5–7, GW6–7 sit behind the 19-day break; MCI at the 3-cap blocks Guéhi/Cherki without a rebuild. Held from GW2 |
| bboost | GW1–19 | **GW19** | provisional | Bench half-repaired (Barry); GK2 and Shaw still dead weight. Last set-1 GW |
| freehit | GW2–19 | **GW16** | provisional | Placeholder — no blank or double in the 380-fixture list; re-check each cycle |

## 9. Retro-correction compliance

| Item | Binding on A4 | How met |
|---|---|---|
| **C5** | TC only on fixture-independent EP | No GW3 TC; GW5 earmark held; GW3's edge over GW5 is +0.10 and inside the band |
| **C8** | near-tied bench/XI orderings on DefCon floor | Applied once (Tarkowski over Thiaw, gap 0.17); Barry/Scott (0.36) and Scott/Thiaw (0.49) exceed the tie band. Third boundary observation logged for the GW4 verdict |
| **C4 residual / C12** | banded fixture never a selected player's largest *defensive* term | Checked all 11: no DEF/GK has a banded CS term as largest component (ARS unbanded; Richards' and Tarkowski's largest terms are appearance). Barry's banded rows are attacking-side — permitted |
| **C7** (consumed) | discount by uncertainty tag | All XI LOW; Shaw MED sits 15th; no HIGH-tagged player bought. Promoted-club HIGH tags (Egan, Ajayi) read as rate uncertainty per the DEF escalation — none selected anyway |
| **MED-B** dead bench | GW3 FT earmarked at the FWD half | Done. GK2 repair path: GW5 (via Tarkowski → De Cuyper cash) or wildcard |
| **MED-D** funding headroom | do not re-litigate | Executed at 5.5; fallback = bank the FT (a GW2-named option); COV pair retired on evidence |
| **LOW-4** recency test (GW4 retro) | log incoming transfers vs last-GW points | Barry: 10 pts GW1–2, structural driver (Beto sold), prior-blended rates, earmarked before GW2 points. De Cuyper (17 pts) and the Fernandes/Isak restructure rejected/deferred partly on this test |
| **Premium under-prediction** | withheld on power | Skeleton restructure deferred to GW4 with the C10 ledger, numbers in §1 |

### MED-E — template fades, re-affirmed on GW3 numbers

| Faded | Own % | GW3 reading |
|---|---:|---|
| João Pedro (CHE) | 69.7 | Now **leads Thiago 29.88 vs 29.13** (GW2 had Thiago ahead). Thiago → João Pedro is +0.75 raw / ≈ +0.7 realized — under the 2.0 bar — and GW3 is ARS(A) 4.07 vs Thiago's SUN(H) 5.10. His GW4 HUL(H) 5.79 is the week this fade bites; priced, not overlooked |
| B.Fernandes (MUN) | 48.6 | No longer "held on funding" — the Haaland sale funds him. Deferred to GW4 on the ≥ £8.0m calibration flag and LOW-4, §1 |
| Calafiori (ARS) | 43.9 | Richards → Calafiori +1.88 realized, under the bar, and a third correlated ARS asset |
| Szoboszlai (LIV) | 41.4 | Scott → Szoboszlai +3.14 realized but LIV's attack drops −1.24 after GW5; rejected on the ticker rule |
| De Cuyper (BHA) | 15.6 | Not a template player yet but the market's strongest buy signal (599k in). Rejected this week on sequencing; first candidate for the GW4 FT |

## 10. Risks and freshness-gate list

| Level | Risk | Handling |
|---|---|---|
| MED | **Barry rises to 5.6 before 17:30Z 4 Sep** (net +75k in-event) | Fallback: bank the FT, GW4 two-FT route (Barry + Raya → Trafford). Do not substitute a HIGH HUL forward |
| MED | Premium skeleton decision deferred one GW | Costs ≈ 1.1 EP if the restructure proves right; buys round-3 data and the C10 ledger |
| MED | MCI at the 3-cap | Guéhi (2nd-best DEF at 6.0) and Cherki unreachable without an MCI out — wildcard material |
| LOW | Shaw net −209k transfers this event | Possible −0.1 drop → sell value −0.1 under the convention; he is bench 3, no selection impact |
| LOW | Anderson `cop 100`, news blank | Record baseline explicitly (as GW2 did) so a re-downgrade diffs as REOPEN |
| LOW | Kusi-Asare drops to 4.4 before the deadline | Net −7k in-event; would strand Barry (4.4 + 1.0 = 5.4). Very unlikely this week |
| — | Analyst escalations (Gyökeres, Senesi, Pope/Horníček, Cherki, Villa GK) | None touches a selected player. Gabriel/Raya unaffected by ARS's FWD question; Thiaw unaffected by NEW's GK split |

Finalizer `flags` list (16 ids — the 15 post-transfer plus the outgoing
player, so a Kusi-Asare status change is visible): `1,4,445,202,427,68,481,
237,69,411,106,497,229,423,249,272`. Snapshot fetched 2026-09-03T17:38Z; the
24h window closes 2026-09-04T17:38Z, after the deadline — no refetch needed
unless a flag moves.

## 11. GW4 earmarks (re-derived next cycle — not commitments)

1. **Premium skeleton**: Haaland → Isak (or João Pedro) + Scott →
   B.Fernandes, −4, gross +9.74 / net +5.74 on GW3 numbers. Decide on the C10
   ledger's ≥ £8.0m reading and round-3 data (§1 conditions).
2. **Otherwise the FT**: Tarkowski → De Cuyper (+2.3 realized, frees £1.3m →
   GK2 fix at GW5) or Shaw → Ajer / Justin (+6.8 / +7.2 raw, ≈ +2.9 with
   cover). Shaw → De Cuyper needs £0.2m the bank will not have unless a
   holding rises.
3. Wildcard GW8 hold; re-check after GW4's band lift whether the GW7 IPS(H)
   TC alternative beats GW5.

## STATE

```yaml
# Convention (as GW2): free_transfers_banked = free transfers available at the
# NEXT (GW4) deadline. This GW's single FT was spent on Kusi-Asare → Barry;
# one new FT accrues.
# team_value = post-transfer squad sell value 99.9 + bank 0.0 under the
# paper-pricing convention (no data/auth.json). The GW3 entry snapshot shows
# bank 1.0 / value 99.9 pre-transfer, matching the convention exactly.
gw: 3
team_id: 8455344
team_value: 99.9
bank: 0.0
free_transfers_banked: 1
chip: null
chips_used: []
transfers_made:
  - {out: Kusi-Asare, in: Barry, cost: 0}
chip_plan:
  - {chip: 3xc, gw: 5, status: provisional}
  - {chip: wildcard, gw: 8, status: provisional}
  - {chip: freehit, gw: 16, status: provisional}
  - {chip: bboost, gw: 19, status: provisional}
picks:
  - {id: 1, name: Raya, position: 1, captain: false, vice: false}
  - {id: 4, name: Gabriel, position: 2, captain: false, vice: false}
  - {id: 202, name: Richards, position: 3, captain: false, vice: false}
  - {id: 229, name: Tarkowski, position: 4, captain: false, vice: false}
  - {id: 427, name: Mbeumo, position: 5, captain: false, vice: true}
  - {id: 237, name: Ndiaye, position: 6, captain: false, vice: false}
  - {id: 481, name: Anderson, position: 7, captain: false, vice: false}
  - {id: 68, name: Tavernier, position: 8, captain: false, vice: false}
  - {id: 411, name: Haaland, position: 9, captain: true, vice: false}
  - {id: 106, name: Thiago, position: 10, captain: false, vice: false}
  - {id: 249, name: Barry, position: 11, captain: false, vice: false}
  - {id: 497, name: Dubravka, position: 12, captain: false, vice: false}
  - {id: 69, name: Scott, position: 13, captain: false, vice: false}
  - {id: 445, name: Thiaw, position: 14, captain: false, vice: false}
  - {id: 423, name: Shaw, position: 15, captain: false, vice: false}
```
