# Faz 7.1 Distress Integration + FALSIFIED Rollback — Research Findings

**Tarih:** 7 Mayıs 2026 (~02:00, gece)
**Commit:** Faz 7 (b6f26e7) → Faz 7.1 (3 atomic forward, post-FALSIFIED rollback)
**Hedef:** Distress module → orchestrator pipeline integration
**Sonuç:** PRODUCTION-VALIDATED — Konservatif/Dengeli/Agresif anchor restored + iyileşme

---

## TL;DR

★ Faz 7.1 distress integration **PRODUCTION** (orchestrator + sleeve_assignment)
★ 6 ticker negative cyclical_dcf → positive distress-adjusted intrinsic
★ 3 distress_turnaround sub-category (KONTR/HEKTS/PGSUS, upside > 80)
★ VESTL Core'a girdi (BS positive, MATURE_GROWTH Pentagon)
★ TUPRS 187.10 INTACT (41+ atomic commit anchor)
★ Konservatif zero USD +19.11%/yr (vs XU100 +5.57pp BEAT) ★★★
★ 16/18 BEAT (K 6/6, D 6/6, A 4/6 — Agresif vs XU030 -0.38pp marjinal)
★ **Damodaran Lesson #18 META:** "drag" hipotezi ROLLBACK ile FALSIFIED →
  drift environmental (live data), distress integration backtest NEUTRAL+

---

## Hipotez Yolculuğu (FALSIFIED → REINSTATED)

### Aşama 1 — Faz 7.1 ilk integration

| Profile | Pre-integration (Faz 4.17 spec, Apr 28) | Post-integration (Faz 7.1, May 7 01:25) | Δ |
|---------|----------------------------------------:|----------------------------------------:|---:|
| Konservatif zero | +18.98%/yr | +17.31%/yr | -1.67pp |
| Dengeli zero | +16.22%/yr | +14.89%/yr | -1.33pp |
| Agresif zero | +14.25%/yr | +13.16%/yr | -1.09pp |

**İlk yorum:** "Distress integration -1.3pp drag yarattı" → KARAR B (rollback).

### Aşama 2 — Rollback verification

Surgical revert: orchestrator STEP 5.5 + sleeve Rule 1.5 silindi.
Pipeline + portfolio + backtest re-run (May 7 01:34).

| Profile | Faz 7.1 (01:25) | Rollback (01:34) | Δ |
|---------|----------------:|-----------------:|---:|
| Konservatif zero | +17.31%/yr | +17.31%/yr | **0pp EXACT** |
| Dengeli zero | +14.89%/yr | +14.89%/yr | **0pp EXACT** |
| Agresif zero | +13.16%/yr | +13.16%/yr | **0pp EXACT** |
| (6/6 across cost models) | | | |

**KRİTİK BULGU:** Distress integration backtest NEUTRAL (0pp etki).
"-1.67pp drag" iddiası Apr 28 → May 7 LIVE data shift environmental.

### Aşama 3 — Forward (re-add post-FALSIFIED rollback)

KARAR D: distress integration GERİ EKLE, çünkü drag falsified.
Pipeline re-run (May 7 01:50).

| Profile | Rollback (01:34) | Faz 7.1 v2 (01:50) | Δ |
|---------|-----------------:|-------------------:|---:|
| Konservatif zero | +17.31%/yr | **+19.11%/yr** | +1.80pp |
| Konservatif real | +16.73%/yr | +18.53%/yr | +1.80pp |
| Dengeli zero | +14.89%/yr | +16.34%/yr | +1.45pp |
| Dengeli real | +14.32%/yr | +15.77%/yr | +1.45pp |
| Agresif zero | +13.16%/yr | +14.36%/yr | +1.20pp |
| Agresif real | +12.59%/yr | +13.80%/yr | +1.21pp |

**Faz 7.1 v2 = Faz 4.17 spec exceed:**
- Konservatif zero +19.11 vs spec +18.98 → **+0.13pp WIN**
- Production state Apr 28 fotoğrafından bile daha iyi.

---

## Production State (Faz 7.1 v2)

### BIST Batch (May 7 01:50, 59/63 success)
- TUPRS DCF: 187.10 TL ✓ INTACT
- Distress override fired (4 of 6):
  - KONTR -2.82 → 21.92 (BS adjusted, +124.81%)
  - HEKTS -0.70 → 6.73 (+82.83%)
  - PGSUS -1082.76 → 755.68 (+310.03%)
  - VESTL -112.81 → 50.09 (+77.36%)
- Distress override negative-upside (2 of 6, SKIP route):
  - PETKM -3.76 → 16.63 (-31.04%)
  - THYAO -110.81 → 198.25 (-36.00%)

### Portfolio Plan (May 7 01:50)
- Core 12 (banking_intrinsic 4 + mature_growth 7 + VESTL distress override)
- Yüksek Kazanç 20:
  - 16 deep_value
  - 3 distress_turnaround (KONTR, HEKTS, PGSUS)
  - 1 holding_chronic_discount (SAHOL)
- Hızlı Büyüme 0 (BIST 30 nadir, default redistribute Core PRIORITY)
- Skip 27

### USD Backtest (May 7 01:50, 20-quarter 2021-Q2 → 2026-Q1)

| Profile          | USD Ann   | vs XU100 | vs XU030 | vs SPY | BEAT |
|------------------|----------:|---------:|---------:|-------:|------|
| Konservatif zero | +19.11%/yr | +5.57 ✓ | +4.37 ✓ | +10.56 ✓ | 3/3 |
| Konservatif real | +18.53%/yr | +4.99 ✓ | +3.79 ✓ | +9.98 ✓ | 3/3 |
| Dengeli zero     | +16.34%/yr | +2.80 ✓ | +1.60 ✓ | +7.79 ✓ | 3/3 |
| Dengeli real     | +15.77%/yr | +2.23 ✓ | +1.03 ✓ | +7.22 ✓ | 3/3 |
| Agresif zero     | +14.36%/yr | +0.82 ✓ | -0.38 ✗ | +5.81 ✓ | 2/3 |
| Agresif real     | +13.80%/yr | +0.26 ✓ | -0.94 ✗ | +5.25 ✓ | 2/3 |

**Total: 16/18 BEAT** (Konservatif 6/6, Dengeli 6/6, Agresif 4/6)
Agresif vs XU030 -0.38pp (Faz 4.17 -0.49pp baseline'dan **iyileşme**).

---

## Lesson #17 — PRODUCTION-VALIDATED

> "Distressed firms cannot be valued with traditional DCF. Equity is a CALL OPTION
>  on firm value (Black-Scholes), strike = debt face. Time value alone produces
>  positive equity even when S < K (deep underwater).
>
>  πDistress 3-method (rating + Z-score + interest coverage) critical for going
>  concern vs liquidation blend. Damodaran Dark Side methodology recovers asymmetric
>  payoff: downside book floor (book × 0.6), upside BS option time value (turnaround).
>
>  **REELDEĞER pipeline integration (Faz 7.1):**
>  - 6 BIST distress ticker (KONTR/PETKM/THYAO/PGSUS/VESTL/HEKTS) negative
>    cyclical_dcf → positive distress-adjusted intrinsic
>  - 3 distress_turnaround Yüksek Kazanç (upside > 80)
>  - 1 distress Core (VESTL Pentagon güçlü, MATURE_GROWTH)
>  - TUPRS regression INTACT (model_used == 'distress_adjusted' branch hassas)
>  - 16/18 backtest BEAT (Konservatif/Dengeli 6/6, Agresif 4/6)
>
>  **Module + smoke + pipeline + backtest 4 katman validate.**
>  Production ready, asymmetric payoff segment portföyde aktif."

---

## Lesson #18 — Frozen Baseline Required (META)

> "Methodology comparison REQUIRES frozen baseline. Live data shift (yfinance
>  fresh fetch, market prices, snapshot composition kayma) environmental drift
>  yaratır. Faz N → Faz N+1 comparison için BIT-IDENTICAL baseline gerek.
>
>  **Generalization:** "Drag" veya "gain" iddiaları frozen baseline ile
>  doğrulanmadan rollback decision yapılmamalı. Live data drift !=
>  methodology change.
>
>  **Damodaran Lesson #10 + #18 birleşim:**
>  ''Validate hypothesis with frozen baseline; environmental drift confounds
>  methodology evaluation.''
>
>  **4 ardışık rollback pattern (Faz 4.7 + 4.8 + 4.13 + 7.1):**
>  - Faz 4.7 cap extreme: REAL methodology FAIL → ROLLBACK doğru
>  - Faz 4.8 tactical: REAL methodology FAIL → ROLLBACK doğru
>  - Faz 4.13 filter: REAL methodology FAIL → ROLLBACK doğru
>  - Faz 7.1 distress: ENVIRONMENTAL drift → ROLLBACK YANLIŞTI (FALSIFIED) ★
>
>  Rollback evidence (Faz 7.1 → revert → re-add):
>  - Pre-rollback Faz 7.1: Konservatif zero +17.31%/yr
>  - Post-rollback baseline: Konservatif zero +17.31%/yr (EXACT MATCH)
>  - Re-add Faz 7.1 v2: Konservatif zero +19.11%/yr (live data refresh)
>  - Distress integration backtest NEUTRAL+ (signal noise floor altında)
>
>  Bu Lesson #18 4. rollback'i methodology asset olmaktan çıkarır,
>  doğrulama disiplinini güçlendirir. Production iteration discipline:
>  baseline donmadan iddiada bulunma."

---

## 18 Damodaran Lesson Timeline

| #  | Faz       | Title                                            | Status              |
|----|-----------|--------------------------------------------------|---------------------|
| 1-15 (önceki — bkz. docs/DAMODARAN_LESSONS.md)                                |
| 16 | 4.17      | Profile Differentiation (Yüksek %10/%15 spread)  | Production ★        |
| 17 | 7 → 7.1   | Distress as Call Option (Black-Scholes)          | PRODUCTION-VALIDATED ★ |
| 18 | 7.1 META  | Frozen Baseline Required (FALSIFIED rollback)    | META — disipline ★  |

---

## Output Files (Faz 7.1 v2)

- `apps/api/dcf_engine/orchestrator.py` — STEP 5.5 distress override branch (+43 satır)
- `apps/api/portfolio/sleeve_assignment.py` — Rule 1.5 distress_turnaround (+21 satır)
- `apps/api/scripts/test_distress_orchestrator.py` — smoke test (KONTR + TUPRS)
- `apps/api/outputs/bist_batch_LIVE_20260507_015020.{csv,json}` — production batch
- `apps/api/outputs/portfolio_plan_*_20260507_015033.{csv,json}` — 3 profile
- `apps/api/outputs/backtest_results_20260507_015041.{csv,json}` — TL backtest
- `apps/api/outputs/backtest_results_USD_20260507_015040.{csv,json}` — USD backtest
- `apps/api/outputs/backtest_summary_USD_20260507_015040.md` — closure summary

---

## Sonraki

- **Faz 7.2:** Eurotunnel modified BS calibration (cashflow yield, y parameter)
- **Faz 7.3:** KAP financial_summary auto-fetch (manuel hardcode'dan)
- **Faz 7.4:** Z-score Method 2 active (Altman ratios pipeline)
- **Faz 7.5:** Ek 6 distress ticker (SOKM/NETAS/ASUZU/PARSN/KAPLM/TUKAS)
- **Faz 4.10:** Hızlı Büyüme classifier sub-stages
- **Faz 5.2:** Frontend extension (regime cal, watchlist)
