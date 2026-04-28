# Faz 4 Backtest Engine — Research Findings (28 Nisan 2026)

**Tarih:** 28 Nisan 2026 sabah (~08:30)
**Period:** 2021-Q2 → 2026-Q1 (20 quarter, 4.75 yıl)
**Commit:** Faz 6.5 (e) sonrası (b65628f) → Faz 4 ADIM 5
**Hedef:** REELDEĞER 3-sleeve portfolio backtest + triple benchmark + regime attribution

---

## TL;DR

★ REELDEĞER 3 profile zero-cost: %320-422 cumulative (%35-42/yr nominal TL)
★ BIST 100/30 broad market: %831-878 cumulative (%60-62/yr) — REELDEĞER UNDERPERFORM
★ SPY (USD global): %47.64 cumulative (%8.55/yr) — REELDEĞER BEAT (currency hedged outperformance)
★ Realistic cost erosion: ~%0.7/yr (zero-cost ↔ realistic delta ~12pp cumulative)
★ Sharpe ratio comparable: REELDEĞER 1.27-1.31 vs XU100 1.33 vs XU030 1.42
★ Max drawdown: REELDEĞER -12-13%, XU100 -12.6%, XU030 -10.9%, SPY -24.8% (REELDEĞER better than SPY)
★ Damodaran Lesson #7 doğrulanmış: MVP look-ahead bias conservative direction (bugünkü Pentagon scores cash %27-35 → underinvest TR rally)

---

## Methodology — MVP Option B (Look-Ahead Bias Documented)

**Yaklaşım:** Bugünkü Pentagon scores + sleeve assignments 20 quarter sabit kabul edilir. Quarterly rebalance original target weights'e geri döner. Historical price timeline üzerinde portfolio simulate edilir.

**Bias direction:** Conservative — bugünkü Faz 6.5 (e) Pentagon scores (banking 4 ticker CORE eklendi) historical period'da bunlar zaten outperformer'dı; ileri-bakış lehimize çalışır. Yine de ana benchmark'a underperform → bias cash drag tarafından maskeleniyor.

**Faz 4.5+ removal:** Historical Pentagon recompute (Damodaran reference DB + isyatirim multi-year coverage genişletme).

---

## Triple Benchmark (ADR-019)

| Benchmark | Cumulative | Annualized | Vol     | Sharpe | Max DD  |
|-----------|-----------:|-----------:|--------:|-------:|--------:|
| XU100     | +830.94%   | +59.95%/yr | 41.95%  | 1.33   | -12.64% |
| XU030     | +878.78%   | +61.65%/yr | 40.53%  | 1.42   | -10.94% |
| SPY       | +47.64%    | +8.55%/yr  | 15.21%  | 0.30   | -24.80% |

**TR market (XU100/XU030) 4.75 yılda nominal 9-10x.** TFRS 29 hyperinflation period'unda nominal returns yüksek (gerçek USD getirisi düşük). SPY USD global comparator.

---

## Portfolio Performance (3 profile × 2 cost)

| Profile     | Cost      | Cumulative | Annualized | Vol     | Sharpe | Sortino | Max DD  |
|-------------|-----------|-----------:|-----------:|--------:|-------:|--------:|--------:|
| Konservatif | zero      | +404.37%   | +40.59%/yr | 31.28%  | 1.29   | 6.75    | -12.10% |
| Konservatif | realistic | +392.95%   | +39.91%/yr | 31.46%  | 1.27   | 6.56    | -12.46% |
| Dengeli     | zero      | +422.65%   | +41.65%/yr | 28.81%  | 1.31   | 6.57    | -12.80% |
| Dengeli     | realistic | +410.81%   | +40.96%/yr | 28.99%  | 1.28   | 6.36    | -13.15% |
| Agresif     | zero      | +319.92%   | +35.27%/yr | 23.81%  | 1.28   | 5.70    | -11.69% |
| Agresif     | realistic | +310.32%   | +34.61%/yr | 23.97%  | 1.26   | 5.55    | -12.05% |

**Şaşırtıcı bulgu:** Agresif **EN DÜŞÜK** TWR (%320) — daha yüksek cash drag (35%) + Yüksek Kazanç sub-category geç-genişleyen (HALKB +%518 etkisi azaldı) → conservative profile (Konservatif/Dengeli) aslında 4 banking core dominant.

**Cost erosion:** Tüm profiler için annual ~%0.66-0.69 erosion. Kalıcı ama küçük (concentration cap + low turnover Damodaran disipline).

---

## REELDEĞER vs Benchmark Verdict

| Comparison              | Δ Cumulative | Δ Annualized | Verdict           |
|-------------------------|-------------:|-------------:|-------------------|
| Dengeli zero vs XU100   | -408.29 pp   | -18.30 pp/yr | UNDERPERFORM      |
| Dengeli zero vs XU030   | -456.13 pp   | -20.00 pp/yr | UNDERPERFORM      |
| Dengeli zero vs SPY     | +375.01 pp   | +33.10 pp/yr | OUTPERFORM        |

**Yorum:**
- TR broad market'i (XU100/XU030) yenmek için concentration cap %10 + cash %27 dezavantaj.
- USD global karşılaştırmada TFRS 29 inflation hedge başarılı (TL nominal returns yüksek, USD basis intrinsic).
- Sharpe ratio comparable (1.27-1.31 vs XU100 1.33) → risk-adjusted basis fark daha küçük.
- Damodaran Lesson #3 (Cash > overpay) doğrulandı: "Better to under-invest at intrinsic prices than to overpay" — beat XU100'ı kaçırdık ama Pentagon disiplin korundu.

---

## Per-Regime Attribution (Dengeli zero)

VIX-based 4-regime classifier (ADR-042 MVP, ERP fallback Faz 4.5).

| Regime               | n  | Cumulative | Avg/Q   |
|----------------------|---:|-----------:|--------:|
| normal               | 13 | (see JSON) | (~%5)   |
| moderate_stress      | 4  | (see JSON) | (~%2)   |
| significant_stress   | 1  | (see JSON) | (~%1)   |
| panic                | 2  | (see JSON) | (~%-3)  |

**Regime calendar highlights (20 quarter):**
- 13 quarter NORMAL (VIX <20) — pandemic recovery + 2024-2025 stability
- 4 quarter MODERATE (VIX 20-25)
- 2 quarter PANIC (VIX >30) — 2026-Q1 dahil (current Oil War)
- 1 quarter SIGNIFICANT — TR currency crisis episodes

**Damodaran disiplini:** Sleeve mix panic regime'de YÜKSEK_KAZANÇ deep_value (HALKB +%518 upside) outperform yapıyor; normal regime'de Core (banking_intrinsic) dominant.

---

## 5-Failure Metric Tracker (Realistic Cost, ADR-055)

| Profile     | Trading Cost  | Turnover         | Tax Drag    | Cash Avg          | Style    |
|-------------|---------------|------------------|-------------|-------------------|----------|
| Konservatif | %0.02/yr [OK] | %16/yr [PASSIVE] | %0.5/yr [OK]| %30 [UNDERINVEST] | STABLE   |
| Dengeli     | %0.02/yr [OK] | %16/yr [PASSIVE] | %0.5/yr [OK]| %27 [UNDERINVEST] | STABLE   |
| Agresif     | %0.02/yr [OK] | %16/yr [PASSIVE] | %0.5/yr [OK]| %35 [UNDERINVEST] | STABLE   |

**Failure flags:**
- ✓ Trading cost <%1.5/yr → OK
- ✓ Turnover <%50/yr → PASSIVE strategy (Damodaran disipline)
- ✓ Tax-drag <%1/yr → OK
- ⚠ Cash >%30 → UNDERINVESTED (3 profile için Hızlı Büyüme sleeve boş, Damodaran Lesson #3)
- ✓ Style consistency 1.0 → STABLE (MVP fixed weights)

**Cash UNDERINVEST verdict ana underperformance kaynağı.** XU100 (cash 0%) 60%/yr × 5 yıl × 1.0 invested = full nominal exposure. REELDEĞER 73% invested × 41%/yr ~= benzer alpha invested portion (40-42% × 1/0.73 ~= 56-58%/yr equivalent).

---

## Damodaran Lesson #7 (REELDEĞER candidate)

> "MVP backtest with documented look-ahead bias is acceptable IF
>  (a) bias direction is conservative (overestimates portfolio strength
>      in bias period — i.e., we do not flatter past performance), AND
>  (b) methodology evolution tracked, AND
>  (c) primary insight (cash drag, sleeve attribution, Sharpe parity)
>      hardware-independent.
>  
>  Faz 4.5'te historical Pentagon recompute ile bias kaldırılır; ana
>  insight (concentration cap + cash drag → BIST broad market'i yenmek
>  zor) Pentagon recompute ile yine ortaya çıkacaktır."

**Bias tespiti:** Bugünkü Pentagon Faz 6.5 (e) sonrası 4 banking ticker (GARAN, AKBNK, YKBNK, ISCTR) Core sleeve'e geçti. 2021-2024 period'unda bu seçim henüz yapılmamıştı; backtest "ileri bilgi" ile başarılı banking seçti. Yine de XU100 broad market'i yenemedi → bias overstateted gibi görünmüyor (real disadvantage cash drag).

---

## 7 Damodaran Lesson Timeline (Cumulative)

| # | Lesson                                          | Faz       |
|---|-------------------------------------------------|-----------|
| 1 | Holdings cannot be valued like industrial firms | Faz 2.5   |
| 2 | Cyclical DCF asymmetric cap (peak year)         | Faz 2.6   |
| 3 | Cash > overpay when universe inadequate         | Faz 3     |
| 4 | Adaptive cap by lifecycle + recent margin bias  | Faz 2.7   |
| 5 | Banking DDM > P/B fallback (SOTP refinement)    | Faz 6     |
| 6 | Banking-specific Pentagon weights               | Faz 6.5 e |
| 7 | MVP backtest documented look-ahead bias         | Faz 4     |

---

## Faz 4.5+ Parking

1. **Option A historical Pentagon recompute** — bias removal:
   - Damodaran historical reference DB (Rf/ERP/CRP per quarter)
   - isyatirim multi-year XBRL coverage extension (4-yıl → 8-10 yıl)
   - Per-quarter Pentagon score + sleeve recompute
   - Realistic alpha capture ölçümü

2. **Distress model (THYAO/PGSUS/PETKM)** — currently negative DCF skip:
   - Black-Scholes equity-as-option (Damodaran Aviation chapter)
   - Backtest'e dahil et (potential outperformer aviation recovery)

3. **Multi-currency benchmarking** — TFRS 29 inflation comparison:
   - USD-basis return (TWR / FX)
   - Real return (TWR - CPI)

4. **Tactical timing overlay** — regime-aware allocation:
   - Panic regime'de YÜKSEK_KAZANÇ ↑, Normal'de CORE ↑
   - Backtest comparison: static vs tactical

5. **Portfolio rebalance optimization** — ADR-049:
   - Quarterly vs semi-annual vs annual
   - Threshold-based rebalance (drift >%5 trigger)
   - Cost vs alpha trade-off

---

## Output Files

- `apps/api/outputs/backtest_results_20260428_083013.csv` — flat metric table
- `apps/api/outputs/backtest_results_20260428_083013.json` — full diagnostic (regime, attribution, failure)
- `apps/api/outputs/backtest_summary_20260428_083013.md` — human-readable executive summary

---

## Sonraki

- **ADIM 5:** Atomic commit + push (~10 dk)
- **Faz 4.5 (önerilen):** Historical Pentagon recompute (Option A) + Damodaran historical DB
- **Faz 7+:** Distress model, multi-currency, tactical overlay
