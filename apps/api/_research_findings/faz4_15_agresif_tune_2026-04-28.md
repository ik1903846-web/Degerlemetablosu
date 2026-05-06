# Faz 4.15 Agresif Allocation Tune — Research Findings (28 Nis 2026)

**Tarih:** 28 Nisan 2026 (~15:30)
**Commit:** Faz 4.14 (ac1c64b) → Faz 4.15 (3 atomic chain)
**Hedef:** Agresif Yüksek Kazanç %15 → %10 (Lesson #14 extension)
**Sonuç:** Agresif marjinal gain (+0.40pp), anchor (Konservatif/Dengeli) bit-identical korundu

---

## TL;DR

★ Agresif Faz 4.14 → Faz 4.15: USD ann +0.40pp gain (zero +6.97 → +7.37)
★ Konservatif/Dengeli BIT-IDENTICAL (anchor BEAT korundu)
★ Agresif vs SPY USD: -2.10 → -1.71pp (BEAT geri kazanılmadı, marjinal iyileşme)
★ Agresif vs XU100 USD: -7.09 → -6.70pp (gap %5 kapandı, küçük)
★ Hipotez kısmen doğrulandı: gain var ama SPY BEAT eşiği geçilmedi
★ TUPRS 187.10 INTACT (39 atomic commit boyunca)

---

## Hipotez vs Gerçek

**Hipotez:**
"Agresif Yüksek %15 → %10 reduction → +0.5-1.5pp ek alpha gain,
SPY BEAT geri kazanılabilir."

**Gerçek:**
- Gain: +0.40pp (hipotez range alt sınırda, marjinal)
- SPY BEAT: -1.71pp underperform (BEAT geri kazanılmadı)
- XU100 gap: -6.70pp (hâlâ büyük)

**Hipotez KISMEN doğrulandı** — alpha gain var ama büyük yapısal değişim yok.

---

## RISK_PROFILES Değişikliği

| Profile     | Faz 4.14 (eski)                | Faz 4.15 (yeni)                |
|-------------|--------------------------------|--------------------------------|
| Konservatif | core 0.82, hızlı 0.15, y 0.03 | (DEĞİŞMEDİ — anchor)           |
| Dengeli     | core 0.65, hızlı 0.25, y 0.10 | (DEĞİŞMEDİ — anchor)           |
| Agresif     | core 0.50, hızlı 0.35, y 0.15 | core **0.55**, hızlı 0.35, y **0.10** |

Sadece Agresif değişti — Yüksek -%5pp, Core +%5pp.

---

## Actual Allocations (Capacity-Pro-Rata Effect)

### Konservatif (anchor)
| Sleeve | Faz 4.14 | Faz 4.15 | Δ |
|--------|---------:|---------:|--:|
| core   | 84.6%    | 84.6%    | 0 (BIT-IDENTICAL) |
| yuksek | 13.4%    | 13.4%    | 0 |

### Dengeli (anchor)
| Sleeve | Faz 4.14 | Faz 4.15 | Δ |
|--------|---------:|---------:|--:|
| core   | 70.9%    | 70.9%    | 0 (BIT-IDENTICAL) |
| yuksek | 27.1%    | 27.1%    | 0 |

### Agresif (target değişti)
| Sleeve | Faz 4.14 | Faz 4.15 | Δ        |
|--------|---------:|---------:|---------:|
| core   | 60.0%    | 64.4%    | +4.4pp ★ |
| yuksek | 38.0%    | 33.6%    | -4.4pp   |
| cash   | 1.6%     | 2.0%     | +0.4pp (MIN_CASH floor) |

Yüksek -%4.4 (target -%5), Core +%4.4 — capacity-pro-rata
redistribution Yüksek'e hâlâ %23+ kayıyor (sleeve capacity dominant).

---

## REELDEĞER vs Benchmark USD-Basis (Faz 4.15 Final)

### vs XU100 USD (+13.54%/yr)
| Profile          | Faz 4.14 | Faz 4.15 | Verdict          |
|------------------|---------:|---------:|------------------|
| Konservatif zero | +1.33 ★ | +1.33 ★ | BEAT (anchor)    |
| Konservatif real | +0.77 ★ | +0.77 ★ | BEAT (anchor)    |
| Dengeli zero     | -4.04   | -4.04   | (anchor)         |
| Dengeli real     | -4.57   | -4.57   | (anchor)         |
| Agresif zero     | -6.57   | -6.17   | gap %6 azaldı    |
| Agresif real     | -7.09   | -6.70   | gap %5 azaldı    |

### vs SPY USD (+8.55%/yr)
| Profile          | Faz 4.14 | Faz 4.15 | Verdict          |
|------------------|---------:|---------:|------------------|
| Konservatif zero | +6.32 ★ | +6.32 ★ | BEAT (anchor)    |
| Konservatif real | +5.76 ★ | +5.76 ★ | BEAT (anchor)    |
| Dengeli zero     | +0.95 ★ | +0.95 ★ | BEAT (anchor)    |
| Dengeli real     | +0.42 ★ | +0.42 ★ | BEAT (anchor)    |
| Agresif zero     | -1.58   | -1.18   | underperform     |
| Agresif real     | -2.10   | -1.71   | underperform     |

**4 profile (Konservatif zero/real, Dengeli zero/real) hâlâ SPY BEAT.**
**Agresif SPY BEAT eşiği geçilmedi** — daha agresif allocation gerek
veya farklı lever (Faz 4.16+).

---

## Damodaran Lesson #14 Extension (Faz 4.15)

> "Allocation lever (Lesson #14, Faz 4.14) profile-by-profile applicable.
>  Recursive sweep: each profile finds optimal allocation through
>  iterative reduction.
>
>  Agresif Faz 4.15 (Yüksek %15 → %10) marginal gain (+0.40pp) çünkü:
>  capacity-pro-rata redistribution Yüksek'e hâlâ %23+ kayıyor (17
>  ticker × cap %12 = %204 capacity, Core 11 × %12 = %132 capacity).
>
>  Daha derin fix: Hızlı Büyüme target redistribution Core PRIORITY
>  (capacity-pro-rata yerine), veya Agresif Yüksek %5 (extreme).
>  Faz 4.16+ candidate: redistribution algoritma Core priority."

---

## Alpha Gain Path (Faz Phase Comparison)

### Konservatif zero USD (en iyi profile)
| Phase    | USD Ann      | vs XU100  |
|----------|-------------:|----------:|
| Faz 4.1  |  -0.21%/yr   | -13.75pp  |
| Faz 4.2  |  +7.72%/yr   |  -5.82pp  |
| Faz 4.5  | +11.07%/yr   |  -2.47pp  |
| Faz 4.6  | +13.81%/yr   |  +0.27 ★  |
| Faz 4.7v2| +14.13%/yr   |  +0.59 ★  |
| Faz 4.14 | +14.87%/yr   |  +1.33 ★★ |
| Faz 4.15 | +14.87%/yr   |  +1.33 ★★ |

**Konservatif zero net journey:** 0.21% → +14.87%/yr (+15.08pp ★★★)

### Agresif real USD (en zayıf profile)
| Phase    | USD Ann   | vs XU100  |
|----------|----------:|----------:|
| Faz 4.1  |  -4.45%/yr| -17.99pp  |
| Faz 4.2  |  +8.29%/yr|  -5.25pp  |
| Faz 4.5  |  +9.87%/yr|  -3.67pp  |
| Faz 4.6  |  +7.74%/yr|  -5.80pp  |
| Faz 4.7v2|  +5.99%/yr|  -7.55pp  |
| Faz 4.14 |  +6.45%/yr|  -7.09pp  |
| Faz 4.15 |  +6.84%/yr|  -6.70pp  |

**Agresif real journey:** -4.45% → +6.84%/yr (+11.29pp, hâlâ underperform XU100)

---

## 14 Damodaran Lesson Timeline (Cumulative, Stable)

| #  | Lesson                                            | Faz       | Status |
|----|---------------------------------------------------|-----------|--------|
| 1  | Holdings cannot be valued like industrial firms   | Faz 2.5   | active |
| 2  | Cyclical DCF asymmetric cap                       | Faz 2.6   | active |
| 3  | Cash > overpay                                    | Faz 3     | active |
| 4  | Adaptive cap by lifecycle                         | Faz 2.7   | active |
| 5  | Banking DDM > P/B                                 | Faz 6     | active |
| 6  | Banking-specific Pentagon                         | Faz 6.5 e | active |
| 7  | MVP backtest documented bias                      | Faz 4     | active |
| 8  | Cash band strict %15 + redistribute               | Faz 4.2   | active |
| 9  | Universe size diminishing                         | Faz 4.5   | active |
| 10 | Hypothesis falsification > methodology force     | Faz 4.7   | active |
| 11 | Tactical regime overlay NOT EFFECTIVE             | Faz 4.8   | active |
| 12 | Universe expansion PROFILE-DEPENDENT              | Faz 4.6   | active |
| 13 | Pentagon Q past ≠ future return (filter FAIL)     | Faz 4.13  | dökümante |
| 14 | Allocation > Filter — sleeve target lever WIN     | Faz 4.14  | active |
|    | Faz 4.15 extension: profile-by-profile sweep      |           |        |

---

## Bilinen Sınırlar (Faz 4.16+ Parking)

1. **Agresif SPY BEAT eşiği geçilmedi (-1.71pp):**
   - Daha agresif Yüksek %10 → %5 test edilebilir
   - Veya redistribution algoritma Core PRIORITY (capacity-pro-rata yerine)

2. **Hızlı Büyüme HÂLÂ BOŞ:**
   - Faz 4.10+ classifier sub-stages parking

3. **TUPRS regression INTACT** (39 atomic commit, preserved)

4. **Look-ahead bias** (Lesson #7) hâlâ var

---

## Output Files

- `apps/api/outputs/portfolio_plan_*_FAZ415.{csv,json}`
- `apps/api/outputs/backtest_results_*_FAZ415.{csv,json,md}`
- `apps/api/outputs/backtest_results_USD_*_FAZ415.{csv,json,md}`

---

## Sonraki

- **Faz 4.16:** Daha agresif Agresif allocation veya redistribution algoritma değişimi
- **Faz 4.10:** Hızlı Büyüme classifier sub-stages
- **Faz 5:** Frontend integration (UI dashboard)
- **Faz 7+:** Distress model Black-Scholes
