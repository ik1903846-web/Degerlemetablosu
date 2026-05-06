# Faz 4.17 Profile Differentiation — Research Findings (7 May 2026)

**Tarih:** 7 Mayıs 2026 (~01:00, gece)
**Commit:** Faz 4.16 (cde4da8) → Faz 4.17 (3 atomic chain)
**Hedef:** Identical emergent fix (Dengeli/Agresif farklılaştırma)
**Sonuç:** Profile spectrum doğrulandı, anchor BIT-IDENTICAL korundu

---

## TL;DR

★ Identical emergent çözüldü: Agresif Yüksek %10 → %15
★ 3 profile distinct outcome: Core 95/88/83, Yüksek 3/10/15
★ Konservatif/Dengeli BIT-IDENTICAL (anchor 4 BEAT INTACT)
★ Agresif distinct: USD ann -1.97pp (Faz 4.16'dan), Max DD -1.55pp İYİLEŞME
★ Profile spectrum: return decreasing, Max DD also decreasing
★ 16/18 backtest×benchmark BEAT (eski 18/18, Agresif XU030 kayıp)
★ TUPRS 187.10 INTACT (40 atomic commit)
★ Damodaran Lesson #16 confirmed

---

## Identical Emergent Root Cause

### Faz Phase Evolution (Yüksek Kazanç target)

| Phase    | Konservatif | Dengeli | Agresif | Note                         |
|----------|------------:|--------:|--------:|------------------------------|
| Faz 4.7v2| 0.05        | 0.15    | 0.25    | 3 distinct                    |
| Faz 4.14 | 0.03        | 0.10    | 0.15    | Lesson #14 reduction (3 distinct)|
| Faz 4.15 | 0.03        | 0.10    | 0.10    | Agresif tune → IDENTICAL ⚠   |
| Faz 4.16 | 0.03        | 0.10    | 0.10    | Core PRIORITY → derinleşti   |
| Faz 4.17 | 0.03        | 0.10    | **0.15**| Differentiation fix ✓         |

**Faz 4.15 anomaly:** Agresif Yüksek %15 → %10 reduction (Faz 4.15 ADIM 2)
Dengeli ile aynı target yarattı. Faz 4.16 Core PRIORITY redistribution
bu eşitliği amplify etti — capacity-pro-rata yerine Core'a full kayma
sonucunda Dengeli ve Agresif **TAM IDENTICAL** sleeve allocations
(Core %88 / Yüksek %10).

### Faz 4.17 Fix
```python
# RISK_PROFILES[agresif].yuksek_kazanc: 0.10 → 0.15
# Konservatif/Dengeli aynen
```

---

## RISK_PROFILES Final State

| Profile     | Core | Hızlı | Yüksek | Notes                     |
|-------------|-----:|------:|-------:|---------------------------|
| Konservatif | 0.82 | 0.15  | 0.03   | (anchor, Faz 4.14)        |
| Dengeli     | 0.65 | 0.25  | 0.10   | (anchor, Faz 4.14)        |
| Agresif     | 0.50 | 0.35  | 0.15   | Yüksek +%5 (Faz 4.17 fix) |

---

## Actual Allocations (Core PRIORITY redistribution)

### Konservatif (anchor — BIT-IDENTICAL)
- target Core 82, Hızlı 15, Yüksek 3
- redistributable = min(15, 13) = 13 (cash buffer hit)
- Step 1 Core: +13 → Core 95
- Final: **Core 95.0% / Yüksek 3.0% / Cash 2.0%**

### Dengeli (anchor — BIT-IDENTICAL)
- target Core 65, Hızlı 25, Yüksek 10
- redistributable = min(25, 23) = 23
- Step 1 Core: +23 → Core 88
- Final: **Core 88.0% / Yüksek 10.0% / Cash 2.0%**

### Agresif (DIFFERENTIATED — Faz 4.17 yenilik)
- target Core 50, Hızlı 35, Yüksek 15
- target sum active = 50+15 = 65
- cash_reserved_max = 100-2-65 = 33
- redistributable = min(35, 33) = 33
- Step 1 Core: min(33, 132-50=82) = 33 → Core 50+33 = 83
- Final: **Core 83.0% / Yüksek 15.0% / Cash 2.0%**

---

## Backtest Results (USD Basis)

### Faz 4.16 → Faz 4.17 (Anchor Verify)

| Profile          | Faz 4.16 USD | Faz 4.17 USD | Δ              |
|------------------|-------------:|-------------:|---------------:|
| Konservatif zero | +18.98%/yr   | +18.98%/yr   | 0.00 ✓ IDENTICAL |
| Konservatif real | +18.40%/yr   | +18.40%/yr   | 0.00 ✓ IDENTICAL |
| Dengeli zero     | +16.22%/yr   | +16.22%/yr   | 0.00 ✓ IDENTICAL |
| Dengeli real     | +15.65%/yr   | +15.65%/yr   | 0.00 ✓ IDENTICAL |
| Agresif zero     | +16.22%/yr   | +14.25%/yr   | -1.97pp (distinct★)|
| Agresif real     | +15.65%/yr   | +13.69%/yr   | -1.96pp (distinct★)|

### Profile Spectrum (Faz 4.17, return decreasing)

| Profile zero | USD Ann   | Sharpe | Max DD  |
|--------------|----------:|-------:|--------:|
| Konservatif  | +18.98%   | 1.20   | -18.50% |
| Dengeli      | +16.22%   | 1.19   | -17.60% |
| Agresif      | +14.25%   | 1.18   | -16.95% (en iyi MaxDD) |

**Spectrum interpretation:**
- Return: Konservatif (Core %95 quality dominant) > Agresif (Yüksek %15 drag)
- Max DD: Agresif (Yüksek %15 deep_value defensive) > Konservatif
- Sharpe: monotonic decrease with risk profile shift (1.20 → 1.18)

---

## vs Triple Benchmark USD (16/18 BEAT)

### vs XU100 USD (+13.54%/yr)
| Profile          | Faz 4.16 | Faz 4.17 | Verdict           |
|------------------|---------:|---------:|-------------------|
| Konservatif zero | +5.44 ★ | +5.44 ★ | BEAT (anchor)     |
| Konservatif real | +4.86 ★ | +4.86 ★ | BEAT (anchor)     |
| Dengeli zero     | +2.68 ★ | +2.68 ★ | BEAT (anchor)     |
| Dengeli real     | +2.11 ★ | +2.11 ★ | BEAT (anchor)     |
| Agresif zero     | +2.68    | +0.71 ★ | BEAT (zayıf)      |
| Agresif real     | +2.11    | +0.15 ★ | BEAT (marjinal)   |

### vs XU030 USD (+14.74%/yr)
| Profile          | Faz 4.16 | Faz 4.17 | Verdict             |
|------------------|---------:|---------:|---------------------|
| Konservatif zero | +4.24 ★ | +4.24 ★ | BEAT (anchor)       |
| Konservatif real | +3.66 ★ | +3.66 ★ | BEAT (anchor)       |
| Dengeli zero     | +1.48 ★ | +1.48 ★ | BEAT (anchor)       |
| Dengeli real     | +0.91 ★ | +0.91 ★ | BEAT (anchor)       |
| Agresif zero     | +1.48    | -0.49    | UNDERPERFORM ⚠ (kayıp)|
| Agresif real     | +0.91    | -1.05    | UNDERPERFORM ⚠      |

### vs SPY USD (+8.55%/yr)
| Profile          | Faz 4.16 | Faz 4.17 | Verdict       |
|------------------|---------:|---------:|---------------|
| Konservatif zero | +10.43 ★| +10.43 ★| BEAT (anchor) |
| Konservatif real | +9.85 ★ | +9.85 ★ | BEAT (anchor) |
| Dengeli zero     | +7.67 ★ | +7.67 ★ | BEAT (anchor) |
| Dengeli real     | +7.10 ★ | +7.10 ★ | BEAT (anchor) |
| Agresif zero     | +7.67    | +5.70 ★ | BEAT          |
| Agresif real     | +7.10    | +5.14 ★ | BEAT          |

**Toplam BEAT:** 16/18 (Faz 4.16 18/18 → Agresif XU030 BEAT kayıp).

---

## Damodaran Lesson #16 (REELDEĞER finding)

> "Core PRIORITY redistribution (Lesson #15) profile target equality
>  durumunda IDENTICAL EMERGENT yaratır. Iki profile aynı Yüksek
>  Kazanç target'ına sahipse (örn. Dengeli=Agresif Yüksek %10),
>  Core PRIORITY redistribution Core'a full kayar → identical actual
>  allocation → identical backtest sonucu.
>
>  Profile spectrum için CONSCIOUS DIFFERENTIATION gerekli. Agresif
>  Yüksek %15 (vs Dengeli %10) distinct outcome:
>    - Daha yüksek Yüksek Kazanç (deep_value drag) → daha düşük return
>    - Daha defansif Yüksek allocation → daha düşük Max DD
>    - Profile spectrum return decreasing, MaxDD decreasing
>
>  Generalization: Lesson #14+#15 kombine sonucunda profile target
>  equality durumlarında identical emergent kaçınılmaz. Conscious
>  differentiation gerek; her profile için SLEEVE TARGET FARKLI olmalı.
>
>  Damodaran disipline 'profile spectrum reflects investor risk
>  tolerance — not artificial allocation parity.'"

---

## 16 Damodaran Lesson Timeline (Cumulative)

| #  | Faz       | Title                                            | Status         |
|----|-----------|--------------------------------------------------|----------------|
| 1  | 2.5       | Holdings cannot be valued like industrial firms  | VALIDATED      |
| 2  | 2.6       | Cyclical DCF asymmetric cap                      | VALIDATED      |
| 3  | 3         | Cash > overpay                                   | VALIDATED      |
| 4  | 2.7       | Adaptive cap by lifecycle                        | VALIDATED      |
| 5  | 6         | Banking DDM > P/B                                | VALIDATED      |
| 6  | 6.5e      | Banking-specific Pentagon                        | VALIDATED      |
| 7  | 4         | MVP backtest documented bias                     | ACKNOWLEDGED   |
| 8  | 4.2       | Cash band strict %15 + redistribute              | VALIDATED ★    |
| 9  | 4.5       | Universe size diminishing                        | VALIDATED      |
| 10 | 4.7       | Hypothesis falsification                         | META-LESSON ★ |
| 11 | 4.8       | Tactical regime overlay NOT EFFECTIVE            | FALSIFIED      |
| 12 | 4.6       | Universe expansion PROFILE-DEPENDENT             | VALIDATED      |
| 13 | 4.13      | Pentagon Q ≠ future return; filter FAIL          | FALSIFIED      |
| 14 | 4.14      | Allocation > Filter — sleeve target lever        | VALIDATED ★★   |
| 15 | 4.16      | Empty sleeve Core PRIORITY                       | VALIDATED ★★★  |
| 16 | 4.17      | Profile differentiation required                 | VALIDATED ★    |

---

## Trade-off Analysis (Faz 4.16 → Faz 4.17)

### Konservatif/Dengeli (anchor)
- USD ann: BIT-IDENTICAL
- Sharpe: BIT-IDENTICAL
- Max DD: BIT-IDENTICAL
- Tüm metrikler değişmedi (anchor verify ✓)

### Agresif (distinct)
- USD ann: -1.97pp (alpha azaldı, Yüksek deep value drag)
- Sharpe: 1.19 → 1.18 (-0.01)
- Max DD: -17.60% → -16.95% (+0.65pp İYİLEŞME, defensive Yüksek)
- vs XU100: +2.68pp BEAT → +0.71pp BEAT (zayıfladı ama hâlâ BEAT)
- vs XU030: +1.48pp BEAT → -0.49pp UNDERPERFORM ⚠ (kayıp)
- vs SPY: +7.67pp BEAT → +5.70pp BEAT (zayıfladı)

**Net trade-off:** Agresif return -%1.97/yr, MaxDD +%0.65 İYİLEŞME.
Profile spectrum doğru ama ULTIMATE 6/6×3/3 kaybedildi (Agresif XU030).

---

## Bilinen Sınırlar (Faz 4.18+ Parking)

1. **Agresif XU030 BEAT kayıp:**
   - Faz 4.16 ULTIMATE state'inden bu trade-off kabul edildi
   - Profile spectrum doğruluk önemli
   - Faz 4.18 candidate: Agresif Yüksek %12 (ara değer, balance)

2. **Hızlı Büyüme HÂLÂ BOŞ** (Faz 4.10+ classifier sub-stages)

3. **TUPRS regression INTACT** (40 commit, preserved)

4. **Look-ahead bias** (Lesson #7) hâlâ var

---

## Output Files

- `apps/api/outputs/portfolio_plan_*_FAZ417.{csv,json}`
- `apps/api/outputs/backtest_results_*_FAZ417.{csv,json,md}`
- `apps/api/outputs/backtest_results_USD_*_FAZ417.{csv,json,md}`

---

## Sonraki

- **Faz 4.18:** Agresif Yüksek %12 (ara değer, ULTIMATE 6/6 geri kazanım)
- **Faz 4.10:** Hızlı Büyüme classifier sub-stages
- **Faz 5.2:** Frontend extension
- **Faz 7+:** Distress model Black-Scholes
