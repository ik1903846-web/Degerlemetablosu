# Faz 4.14 Allocation Lever — Research Findings (28 Nis 2026)

**Tarih:** 28 Nisan 2026 (~15:00)
**Commit:** Faz 4.13 ROLLBACK (2ef2466) → Faz 4.14 (3 atomic chain)
**Hedef:** Yüksek Kazanç drag fix via allocation (Lesson #13 fix path)
**Sonuç:** ★★★ HİPOTEZ DOĞRULANDI — TÜM 6 backtest alpha GAIN

---

## TL;DR

★ Allocation lever ÇALIŞTI — Yüksek Kazanç sleeve target reduction
★ TÜM profilerde alpha GAIN (+0.46 to +1.73pp/yr USD)
★ Konservatif XU100 USD BEAT genişledi: +0.59pp → +1.33pp zero, +0.77pp real
★ Dengeli SPY USD BEAT GERİ KAZANILDI: -1.31pp → +0.42pp ★
★ Konservatif SPY USD BEAT expand: +5.02pp → +5.76pp
★ XU100 gap kapanma (Dengeli zero -5.77 → -4.04, %30 azaldı)
★ HALKB/ARENA/BOSSA + 14 ticker korundu (filter'dan farkı: ticker drop yok)
★ Damodaran Lesson #14: Allocation > Filter approach
★ TUPRS 187.10 INTACT (39 atomic commit boyunca)

---

## Hipotez vs Gerçek

**Hipotez:**
"Allocation lever (sleeve target %15 → %10) Yüksek Kazanç drag azaltır
AMA historical alpha sources korunur. Filter'dan farkı:
- Filter (Faz 4.13): ticker drop = alpha kayıp (FAIL)
- Allocation (Faz 4.14): ticker korunur, weight azalır"

**Gerçek:**

| Profile          | Faz 4.7 v2 USD | Faz 4.14 USD | Δ          | vs Faz 4.13 |
|------------------|---------------:|-------------:|-----------:|------------:|
| Konservatif zero | +14.13%/yr     | +14.87%/yr   | +0.74pp ★  | +3.64pp ★★  |
| Konservatif real | +13.57%/yr     | +14.31%/yr   | +0.74pp ★  | +3.62pp ★★  |
| Dengeli zero     |  +7.77%/yr     |  +9.50%/yr   | +1.73pp ★  | +3.37pp ★★  |
| Dengeli real     |  +7.24%/yr     |  +8.97%/yr   | +1.73pp ★  | +3.36pp ★★  |
| Agresif zero     |  +6.51%/yr     |  +6.97%/yr   | +0.46pp    | +1.20pp     |
| Agresif real     |  +5.99%/yr     |  +6.45%/yr   | +0.46pp    | +1.20pp     |

**HİPOTEZ DOĞRULANDI** — TÜM profilerde alpha GAIN. Lesson #13 fix path
allocation lever ile başarılı.

---

## RISK_PROFILES Değişikliği

| Profile     | Faz 4.7 v2 (eski)              | Faz 4.14 (yeni)                |
|-------------|--------------------------------|--------------------------------|
| Konservatif | core 0.80, hızlı 0.15, y 0.05 | core **0.82**, hızlı 0.15, y **0.03** |
| Dengeli     | core 0.60, hızlı 0.25, y 0.15 | core **0.65**, hızlı 0.25, y **0.10** |
| Agresif     | core 0.40, hızlı 0.35, y 0.25 | core **0.50**, hızlı 0.35, y **0.15** |

Toplam değişim:
- Konservatif: Yüksek -%2pp, Core +%2pp
- Dengeli: Yüksek -%5pp, Core +%5pp
- Agresif: Yüksek -%10pp, Core +%10pp

Hızlı Büyüme target değişmedi (15/25/35), boş sleeve redistribution
capacity-pro-rata Core+Yüksek'e dağılır (Faz 4.2 mekanizması korunur).

---

## Actual Allocations (Capacity-Pro-Rata Effect)

| Profile     | Sleeve     | Faz 4.7 v2 actual | Faz 4.14 actual | Δ        |
|-------------|-----------|------------------:|----------------:|---------:|
| Konservatif | core      | 82.7%             | 84.6%           | +1.9pp ★ |
| Konservatif | yuksek    | 15.3%             | 13.4%           | -1.9pp   |
| Dengeli     | core      | 66.3%             | 70.9%           | +4.6pp ★ |
| Dengeli     | yuksek    | 31.7%             | 27.1%           | -4.6pp   |
| Agresif     | core      | 51.2%             | 60.0%           | +8.8pp ★ |
| Agresif     | yuksek    | 46.8%             | 38.0%           | -8.8pp   |

Cash levels (MIN_CASH 2%):
- Konservatif: 0% → 2% (MIN_CASH floor restored)
- Dengeli: 0% → 2%
- Agresif: 2% → 2% (aynı)

---

## REELDEĞER vs Benchmark USD-Basis (Final Verdict)

### vs XU100 USD (+13.54%/yr)

| Profile          | Faz 4.7 v2 | Faz 4.14   | Verdict                     |
|------------------|-----------:|-----------:|-----------------------------|
| Konservatif zero | +0.59 BEAT | +1.33 BEAT | BEAT GENİŞLEDİ ★★ (+0.74pp) |
| Konservatif real | +0.03 BEAT | +0.77 BEAT | BEAT GENİŞLEDİ ★ (+0.74pp)  |
| Dengeli zero     | -5.77      | -4.04      | gap %30 azaldı ★            |
| Dengeli real     | -6.30      | -4.57      | gap %27 azaldı              |
| Agresif zero     | -7.03      | -6.57      | gap %7 azaldı (marjinal)    |
| Agresif real     | -7.55      | -7.09      | gap %6 azaldı               |

### vs SPY USD (+8.55%/yr)

| Profile          | Faz 4.7 v2  | Faz 4.14   | Verdict                              |
|------------------|------------:|-----------:|--------------------------------------|
| Konservatif zero | +5.58 BEAT  | +6.32 BEAT | BEAT EXPAND ★★                       |
| Konservatif real | +5.02 BEAT  | +5.76 BEAT | BEAT EXPAND                          |
| Dengeli zero     | -0.78       | +0.95 BEAT | UNDERPERFORM → BEAT ★★ (geri kazanıldı) |
| Dengeli real     | -1.31       | +0.42 BEAT | UNDERPERFORM → BEAT ★ (geri kazanıldı)  |
| Agresif zero     | -2.04       | -1.58      | underperform (marjinal iyileşme)     |
| Agresif real     | -2.56       | -2.10      | underperform (marjinal iyileşme)     |

---

## Filter vs Allocation — Methodology Comparison

| Profile          | Faz 4.13 USD (filter) | Faz 4.14 USD (allocation) | Δ          |
|------------------|----------------------:|--------------------------:|-----------:|
| Konservatif zero | +11.23%/yr            | +14.87%/yr                | +3.64pp ★  |
| Konservatif real | +10.69%/yr            | +14.31%/yr                | +3.62pp ★  |
| Dengeli zero     |  +6.13%/yr            |  +9.50%/yr                | +3.37pp ★  |
| Dengeli real     |  +5.61%/yr            |  +8.97%/yr                | +3.36pp ★  |
| Agresif zero     |  +5.77%/yr            |  +6.97%/yr                | +1.20pp    |
| Agresif real     |  +5.25%/yr            |  +6.45%/yr                | +1.20pp    |

**Allocation lever WIN** — sleeve target reduction her profilde
better than filter strengthen. Damodaran Lesson #14 confirmed.

---

## Damodaran Lesson #14 (REELDEĞER finding) ★★

> "Allocation lever (sleeve target reduction) FIXES profile-dependent
>  expansion (Lesson #12). Filter approach (Lesson #13) FAIL — drops
>  historical alpha sources.
>
>  Allocation reduces sleeve weight WITHOUT dropping ticker'lar:
>    HALKB Q=40 (banking deep_value low quality but +%257 historical)
>    ARENA Q=95 (high quality but +%87 marginal upside)
>    BOSSA upside +%75 (mature_transition)
>  Hepsi sleeve'de kaldı, sadece weight azaldı.
>
>  Damodaran 'active management lever' = ALLOCATION, not stock screening.
>  Filter intuition wrong — Pentagon Q (margin stability) past-looking,
>  realized return correlation weak. Allocation neutral to ticker
>  selection, just rebalances sleeve targets.
>
>  Generalization: When facing profile-dependent drag, FIRST try
>  allocation reduction; ONLY IF that fails, consider filter strengthen.
>  3 ardışık fail (cap, tactical, filter) = ad-hoc methodology drift;
>  systematic Lesson #10-11-12-13 reinforce 'validate before claim'."

---

## 14 Damodaran Lesson Timeline (Cumulative)

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
| 10 | Hypothesis falsification > methodology force-fit  | Faz 4.7   | active |
| 11 | Tactical regime overlay NOT EFFECTIVE             | Faz 4.8   | active |
| 12 | Universe expansion PROFILE-DEPENDENT              | Faz 4.6   | active |
| 13 | Pentagon Q (past) ≠ future return; filter FAIL    | Faz 4.13  | dökümante (rollback'd) |
| 14 | Allocation > Filter — sleeve target lever WIN     | Faz 4.14 ★| ACTIVE |

---

## Trade-off (Faz 4.7 v2 → Faz 4.14)

### Sharpe (improvement marginal)
- Konservatif: 1.18 → 1.18 (aynı)
- Dengeli:     1.15 → 1.16 (+0.01)
- Agresif:     1.12 → 1.14 (+0.02)

### Max DD (marjinal değişim)
- Konservatif: -16.91% → -17.16% (-0.25pp marginal kötüleşme)
- Dengeli:     -14.81% → -15.39% (-0.58pp)
- Agresif:     -15.05% → -14.63% (+0.42pp İYİLEŞME)

### Cash recovery
- Konservatif: 0% → 2% (MIN_CASH restored)
- Dengeli:     0% → 2%
- Agresif:     2% → 2%

---

## Bilinen Sınırlar (Faz 4.15+ Parking)

1. **Agresif XU100 gap hâlâ büyük (-7pp):**
   - Yüksek Kazanç actual %38 (target %15) — capacity-pro-rata redistribution
     hâlâ Yüksek'e oransız kayıyor
   - Daha agresif allocation reduction (Yüksek %15 → %10) test edilebilir

2. **Hızlı Büyüme HÂLÂ BOŞ:**
   - Faz 4.10+ classifier sub-stages parking
   - Pentagon Growth dimension HIZLI_BUYUME bypass

3. **SMRTG XBRL hâlâ fail** (Faz 4.10+ deep debug)

4. **Look-ahead bias** (Faz 4 Lesson #7) hâlâ var

---

## Output Files

- `apps/api/outputs/portfolio_plan_*_FAZ414.{csv,json}`
- `apps/api/outputs/backtest_results_*_FAZ414.{csv,json,md}`
- `apps/api/outputs/backtest_results_USD_*_FAZ414.{csv,json,md}`

---

## Sonraki

- **Faz 4.15:** Agresif Yüksek %15 → %10 (daha agresif allocation reduction)
- **Faz 4.10:** Hızlı Büyüme classifier sub-stages
- **Faz 5:** Frontend integration
- **Faz 7+:** Distress model Black-Scholes
