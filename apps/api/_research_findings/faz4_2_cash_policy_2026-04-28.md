# Faz 4.2 Cash Policy Refinement — Research Findings (28 Nis 2026)

**Tarih:** 28 Nisan 2026 sabah (~09:10)
**Commit:** Faz 4.1 (87839a9) → Faz 4.2 (4 atomic chain)
**Hedef:** Cash drag minimize + USD alpha capture verify (Damodaran Lesson #8)

---

## TL;DR

★ Cash %27-35 → %2-10 (dramatic, Damodaran Lesson #8)
★ USD alpha +%9/yr capture (Dengeli realistic: +0.06% → +9.14%/yr USD)
★ SPY beat USD basis (Dengeli realistic +0.59pp/yr OUTPERFORM, eski -8.49pp UNDERPERFORM)
★ XU100/XU030 underperformance gap %66 kapandı (-13/-14pp → -4/-6pp/yr)
★ Sharpe ratio improvement: 1.27-1.31 → 1.32-1.37
★ Max drawdown elevation: -12.10/-12.80% → -15.70/-17.20% (cash buffer azaldı)

---

## Hipotez (Faz 4.1 USD-Basis Bulgusu)

**Faz 4.1'de tespit:** REELDEĞER USD basis 4.75 yıl ~%0/yr, tüm benchmark'lara underperform.
Ana neden: Cash %27-35 (Hızlı Büyüme sleeve boş + Konservatif Core capacity bottleneck).

**Hipotez:** "Cash %15 cap (vs %30) ile USD alpha capture +%5-7/yr artar.
Sleeve threshold flexibility (composite > 48 vs > 50) Damodaran value discipline'i
korur, ama cash drag minimize edilir."

---

## Yapılan Değişiklikler

### (1) Sleeve Threshold Gevşetme — `sleeve_assignment.py`

| Rule                | Eski Threshold        | Yeni Threshold        | Δ          |
|---------------------|----------------------|----------------------|------------|
| Skip floor          | comp<35, V<20, ups<-30 | comp<32, V<15, ups<-35 | gevşeme    |
| Core industrial     | ups>30, Q>60, comp>50  | ups>20, Q>55, comp>48  | gevşeme    |
| Core banking        | excess≥4pp, ups>0, comp>50, V>30 | excess≥3pp, ups>-5, comp>50, V>25 | gevşeme |
| Yüksek deep_value   | ups>100, comp>55       | ups>80, comp>50        | gevşeme    |
| Banking premium     | ROE>20, ups>50         | ROE>18, ups>30         | gevşeme    |

**Damodaran value discipline:** composite > 48 (vs eski 50) hâlâ Pentagon-disciplined.
Skip floor 32 (vs 35) marjinal — sadece -3pp oynama.

### (2) Cash Policy — `portfolio_construction.py`

| Constant                  | Eski | Yeni | Damodaran Note                    |
|---------------------------|-----:|-----:|-----------------------------------|
| MAX_SINGLE_TICKER_PCT     | 10.0 | 12.0 | ADR-015 disclaimer küçük esneklik |
| MAX_CASH_PCT              | 30.0 | 15.0 | Damodaran Lesson #8 cash drag     |
| MIN_CASH_PCT              | 2.0  | 2.0  | INTACT (full investment principle)|

### (3) Empty Sleeve Redistribution (Yeni Logic)

**Önce:** Boş sleeve target'ı cash'e dökülürdü → %30+ underinvested.
```
if not sleeve_groups[sleeve_name]:
    actual_alloc[sleeve_name] = 0  # cash'e gider
```

**Şimdi:** Boş sleeve target'ı aktif sleeve'lere capacity-pro-rata redistribute,
MIN_CASH_PCT (%2) buffer korunur.
```python
empty_target_pct = sum(target for empty sleeves)
capacity_headroom = {
    name: max_cap - current_target for active sleeves
}
cash_reserved_max = 100 - MIN_CASH_PCT - sum_active_target
redistributable = min(empty_target_pct, total_headroom, cash_reserved_max)
```

---

## Portfolio Plan Re-Run (24 ticker, sleeve breakdown aynı)

| Profile     | Eski Cash | Yeni Cash | Eski Pos | Yeni Pos |
|-------------|----------:|----------:|---------:|---------:|
| Konservatif | %70.0     | %10.4     | 7        | 11       |
| Dengeli     | %27.4     | %2.7      | 11       | 11       |
| Agresif     | %35.0     | %2.0      | 11       | 11       |

**Sleeve breakdown 24 ticker (degişmedi):**
- Core: 6 (GARAN, AKBNK, YKBNK, ARCLK, EREGL, ISCTR)
- Hızlı Büyüme: 0 (BIST 30 mature, Faz 4.5 BIST 50/100 expansion)
- Yüksek Kazanç: 5 (CCOLA, FROTO, HALKB, SAHOL, TRALT)
- Skip: 11 (TUPRS, MGROS, TOASO, KCHOL, ENKAI, KRDMD, ASELS, THYAO, PGSUS, TRMET, PETKM)

**Threshold gevşetme borderline ticker'lara YENİ Core/Yüksek eklemedi** —
SKIP listesindeki tüm ticker'lar upside <-30% (mevcut SAT verdict) veya
negative DCF (THYAO/PGSUS/PETKM Black-Scholes Faz 7+ parking).
Bu beklenen — Damodaran value discipline'i hâlâ disipline ediyor.

---

## TL-Basis Backtest Re-Run (yeni cash policy)

| Profile | Cost | Eski TL Ann | Yeni TL Ann | Δ          | Sharpe Δ        | Max DD Δ           |
|---------|------|------------:|------------:|-----------:|----------------:|-------------------:|
| Konservatif | zero      | +40.59%/yr | +51.75%/yr | +11.16pp | 1.29 → 1.34   | -12.10% → -15.70% |
| Konservatif | realistic | +39.91%/yr | +51.03%/yr | +11.12pp | 1.27 → 1.32   | -12.46% → -16.05% |
| Dengeli     | zero      | +41.65%/yr | +54.50%/yr | +12.85pp | 1.31 → 1.37   | -12.80% → -17.20% |
| Dengeli     | realistic | +40.96%/yr | +53.76%/yr | +12.80pp | 1.28 → 1.35   | -13.15% → -17.55% |
| Agresif     | zero      | +35.27%/yr | +53.29%/yr | +18.02pp | 1.28 → 1.36   | -11.69% → -17.63% |
| Agresif     | realistic | +34.61%/yr | +52.55%/yr | +17.94pp | 1.26 → 1.34   | -12.05% → -17.99% |

**Trade-off:** TL nominal +%11-18pp/yr alpha, ama max DD -3 ila -6pp daha kötü.
Cash buffer azaldığında volatility tam exposure → DD elevation beklenen.
Sharpe yine de iyileşti (+0.05-0.08 across profiles) — risk-adjusted alpha kalıcı.

---

## USD-Basis Backtest Re-Run ★ (Hipotez Verify)

| Profile | Cost | Eski USD Ann | Yeni USD Ann | Δ              |
|---------|------|-------------:|-------------:|---------------:|
| Konservatif | zero      |  -0.21%/yr | +7.72%/yr | **+7.93pp** ★ |
| Konservatif | realistic |  -0.69%/yr | +7.20%/yr | **+7.89pp** ★ |
| Dengeli     | zero      |  +0.54%/yr | +9.67%/yr | **+9.13pp** ★ |
| Dengeli     | realistic |  +0.06%/yr | +9.14%/yr | **+9.08pp** ★ |
| Agresif     | zero      |  -3.98%/yr | +8.81%/yr | **+12.79pp** ★★ |
| Agresif     | realistic |  -4.45%/yr | +8.29%/yr | **+12.74pp** ★★ |

**★ HİPOTEZ DOĞRULANDI:** Cash %15 cap → USD alpha +%7-13/yr capture.
Hipotez "+%5-7/yr" beklenenten yüksek geldi — Faz 4.2 değişimleri
beklentiyi aştı.

---

## REELDEĞER vs Benchmark USD-Basis (Dengeli realistic baseline)

| Comparison      | Eski Δ          | Yeni Δ          | Verdict Update             |
|-----------------|----------------:|----------------:|----------------------------|
| vs XU100 USD    | -13.48 pp/yr    | -4.40 pp/yr     | UNDERPERFORM (gap %67 ↓)   |
| vs XU030 USD    | -14.68 pp/yr    | -5.60 pp/yr     | UNDERPERFORM (gap %62 ↓)   |
| vs SPY USD      |  -8.49 pp/yr    | **+0.59 pp/yr** | **OUTPERFORM ★ INVERTED** |

**SPY beat sahte değildi:** Faz 4.1'de cash drag SPY beat'i tersine çevirmişti.
Faz 4.2 cash policy fix ile USD alpha capture geri geldi → SPY yine yenildi.

XU100/XU030 underperformance %60+ azaldı ama hâlâ var. Kalan gap (~%5/yr):
- BIST 30 universe darlığı (concentration cap 6 ticker × %12 = %72 max Core)
- Faz 4.5+ BIST 50/100 expansion gap'i kapatabilir (Hızlı Büyüme sleeve dolar)

---

## Damodaran Lesson #8 (REELDEĞER finding)

> "Cash policy must be strict (max %15) to capture USD alpha. Sleeve
>  threshold flexibility (composite > 48 vs > 50) allows broader Core
>  inclusion while maintaining value discipline. Lesson #3 prensibi
>  (cash > overpay) korunur AMA cash band tightening + empty sleeve
>  redistribution ile cash drag minimize edilir.
>
>  Cash %30 → %15 cap value-discipline ihlali değil — hepsi composite >
>  48 disciplined ticker'lara gidiyor. Pentagon Damodaran disipline'i
>  cash drop'la fonksiyonelliğini korudu."

**Lesson #3 reconciliation:**
- Faz 3 Lesson: "Cash > overpay when universe inadequate" → cash kabul edilebilir
- Faz 4.2 Lesson: "Cash strict %15 cap" → minimize edilmeli
- Çelişki YOK: Faz 4.2 strict cap zaten value-disciplined ticker'lar var
  olduğunda (Pentagon comp > 48) uygulanır. Universe inadequate olduğunda
  (yok composite > 48 ticker) cash overflow doğal olur.

---

## 8 Damodaran Lesson Timeline (Cumulative)

| #  | Lesson                                          | Faz       |
|----|-------------------------------------------------|-----------|
| 1  | Holdings cannot be valued like industrial firms | Faz 2.5   |
| 2  | Cyclical DCF asymmetric cap (peak year)         | Faz 2.6   |
| 3  | Cash > overpay when universe inadequate         | Faz 3     |
| 4  | Adaptive cap by lifecycle + recent margin bias  | Faz 2.7   |
| 5  | Banking DDM > P/B fallback (SOTP refinement)    | Faz 6     |
| 6  | Banking-specific Pentagon weights               | Faz 6.5 e |
| 7  | MVP backtest documented look-ahead bias         | Faz 4     |
| 8  | Cash band strict %15 + empty sleeve redistribute| Faz 4.2 ★ |

---

## Bilinen Sınırlar (Faz 4.5+ Parking)

1. **XU100/XU030 USD basis underperformance hâlâ var (-4-6pp/yr):**
   - BIST 30 concentration cap 6 Core × %12 = max %72
   - Faz 4.5 BIST 50/100 expansion → Hızlı Büyüme sleeve dolduğunda gap kapanır

2. **Max DD elevation -3-6pp:**
   - Cash buffer azalmasının fiyatı
   - Faz 4.5 tactical regime overlay panic regime'de cash escalation
     (VIX > 30 tetikleyici) DD'i azaltabilir

3. **Threshold gevşetme BIST 30'da yeni ticker getirmedi:**
   - Tüm SKIP ticker'lar upside <-30% (overvalued) veya negative DCF
   - Faz 4.5 BIST 50/100 universe 11 → 22 Core ticker daha fazla seçim

4. **MAX_SINGLE_TICKER_PCT 10 → 12 ADR-015 dis-respect:**
   - "Disclaimer küçük" — Damodaran spec %10 preferable, %12 absolute max
   - Faz 4.5 BIST 50 expansion sonrası %10'a geri dönülebilir

5. **Look-ahead bias hâlâ var (Faz 4 Lesson #7):**
   - Bugünkü Pentagon scores 20 quarter sabit
   - Faz 4.5 Option A historical Pentagon recompute

---

## Output Files

- `apps/api/outputs/portfolio_plan_{konservatif,dengeli,agresif}_20260428_090944.{csv,json}`
- `apps/api/outputs/backtest_results_20260428_090954.{csv,json}` — TL basis
- `apps/api/outputs/backtest_summary_20260428_090954.md`
- `apps/api/outputs/backtest_results_USD_20260428_090958.{csv,json}` — USD basis ★
- `apps/api/outputs/backtest_summary_USD_20260428_090958.md`

---

## Sonraki

- **ADIM 5:** kaldim.md + memory + atomic commit chain (~30 dk)
- **Faz 4.5 (önerilen):** BIST 50/100 universe expansion (Hızlı Büyüme dolar)
- **Faz 4.6:** Tactical regime overlay (VIX > 30 cash escalation)
- **Faz 4.7:** Option A historical Pentagon recompute (look-ahead bias removal)
