# Faz 4.13 Selective Filter Strengthen — Research Findings (28 Nis 2026)

**Tarih:** 28 Nisan 2026 (~14:30)
**Commit:** Faz 4.7 v2 (3447f6d) → Faz 4.13 (3 atomic chain)
**Hedef:** Yüksek Kazanç sleeve filter strict → Dengeli/Agresif XU100 gap kapatma
**Sonuç:** ⚠ HİPOTEZ FAIL — filter alpha drag çözmedi, kötüleştirdi

---

## TL;DR

★ ⚠ Hipotez FAIL: filter strengthen TÜM profilerde alpha KAYBI
★ Konservatif XU100 USD BEAT KAYBOLDU (Faz 4.7 v2 +0.03pp → Faz 4.13 -2.85pp)
★ Konservatif zero -2.90pp, Dengeli -1.64pp, Agresif -0.74pp/yr USD
★ Damodaran Lesson #13 candidate: Pentagon Q score (past) ≠ future return
★ TUPRS 187.10 INTACT (38 atomic commit boyunca)
★ Rollback önerisi: Faz 4.7 v2 baseline'a dönüş (user kararı)

---

## Hipotez vs Gerçek

**Hipotez (user önerisi):**
"Yüksek Kazanç drag deep value low-quality kaynaklı. Filter strict
(Q > 45, upside > 120) → drag azalır, Dengeli/Agresif USD alpha gain."

**Gerçek (3 profile × 2 cost = 6 backtest):**

| Profile          | Faz 4.7 v2 USD | Faz 4.13 USD | Δ          | vs XU100   |
|------------------|---------------:|-------------:|-----------:|-----------:|
| Konservatif zero | +14.13%/yr     | +11.23%/yr   | -2.90pp ⚠  | -2.31pp ⚠  |
| Konservatif real | +13.57%/yr     | +10.69%/yr   | -2.88pp ⚠  | -2.85pp ⚠  |
| Dengeli zero     |  +7.77%/yr     |  +6.13%/yr   | -1.64pp ⚠  | -7.41pp ⚠  |
| Dengeli real     |  +7.24%/yr     |  +5.61%/yr   | -1.63pp ⚠  | -7.93pp ⚠  |
| Agresif zero     |  +6.51%/yr     |  +5.77%/yr   | -0.74pp ⚠  | -7.77pp    |
| Agresif real     |  +5.99%/yr     |  +5.25%/yr   | -0.74pp ⚠  | -8.29pp    |

**TÜM profilerde alpha LOSS. Konservatif XU100 BEAT KAYBOLDU.**

---

## Filter Değişiklikleri

| Rule                    | Eski (Faz 4.2)              | Yeni (Faz 4.13 strict)              |
|-------------------------|------------------------------|--------------------------------------|
| Banking deep_value      | upside>80, comp>50           | upside>80, comp>50, **Q>45** (gate) |
| Banking premium         | ROE>18, upside>30            | ROE>20, upside>50, **Q>60**         |
| Holding chronic         | upside>50, comp>50           | upside>**70**, comp>**55**          |
| Industrial deep_value   | upside>80, comp>50           | upside>**120**, comp>**55**, Q>45   |

---

## Drop'lanan Ticker'lar (Sebep Analizi)

### HALKB (Banking deep_value, Q=40 < 45)
- Banking sleeve drop, Skip'e düştü
- Faz 4.7 v2: +257% upside, deep_value
- Historical 2021-2026 banking rally'sinden faydalandı
- Drop büyük alpha kayıp

### ARENA (Industrial deep_value, upside +87% < 120)
- Q=95 (en yüksek!), comp=78.71 (3. en yüksek)
- Faz 4.13 upside threshold 120% → drop
- Quality high ama threshold rigid → kayıp

### BOSSA (mature_transition → Core)
- upside +75% < 120
- Faz 4.13 Core'a geçti (lifecycle MATURE_GROWTH/STABLE)
- Yüksek Kazanç'tan Core'a kaydı, weight değişimi marginal

---

## Damodaran Lesson #13 (REELDEĞER finding)

> "Yüksek Kazanç filter strengthen DOES NOT fix profile-dependent
>  expansion (Lesson #12). Pentagon Q score (margin stability)
>  PAST-LOOKING; future realized return correlation weak.
>
>  Filter "quality" gate (Q > 45 etc.) drops historically high-return
>  ticker'lar (HALKB Q=40 +257% upside, ARENA Q=95 +87% upside, BOSSA
>  +75%). Pentagon Q low ≠ realized return low — Q is volatility-of-margin,
>  realized return is total path.
>
>  Selective expansion needs DIFFERENT lever:
>    (a) Reduce Yüksek Kazanç sleeve target % (allocation, not filter)
>    (b) Profile-aware sleeve targets (Konservatif Yüksek %5 → %3)
>    (c) Historical realized return as Pentagon dimension (Faz 5+ research)
>
>  3 ardışık hipotez fail (Faz 4.7 cap refinement + Faz 4.8 tactical
>  overlay + Faz 4.13 filter strengthen) Lesson #10 (validate before
>  methodology change) reinforce. Pattern: ad-hoc fix without backtest
>  validation = methodology drift."

---

## Trade-off Analizi

### Sharpe Ratio (düşüş)
- Konservatif: 1.18 → 1.11 (-0.07)
- Dengeli:     1.15 → 1.10 (-0.05)
- Agresif:     1.12 → 1.08 (-0.04)

### Max DD (marjinal değişim)
- Konservatif: -16.91% → -16.29% (+0.62pp iyileşme, marginal)
- Dengeli:     -14.81% → -14.64% (+0.17pp marginal)
- Agresif:     -15.05% → -15.96% (-0.91pp daha kötü)

### Vol (azaldı ama Sharpe düştü, yani return düşüşü vol düşüşünden büyük)

---

## 13 Damodaran Lesson Timeline (Cumulative)

| #  | Lesson                                            | Faz       |
|----|---------------------------------------------------|-----------|
| 1  | Holdings cannot be valued like industrial firms   | Faz 2.5   |
| 2  | Cyclical DCF asymmetric cap                       | Faz 2.6   |
| 3  | Cash > overpay                                    | Faz 3     |
| 4  | Adaptive cap by lifecycle                         | Faz 2.7   |
| 5  | Banking DDM > P/B                                 | Faz 6     |
| 6  | Banking-specific Pentagon                         | Faz 6.5 e |
| 7  | MVP backtest documented bias                      | Faz 4     |
| 8  | Cash band strict %15 + redistribute               | Faz 4.2   |
| 9  | Universe size diminishing                         | Faz 4.5   |
| 10 | Hypothesis falsification > methodology force-fit  | Faz 4.7   |
| 11 | Tactical regime overlay NOT EFFECTIVE             | Faz 4.8   |
| 12 | Universe expansion PROFILE-DEPENDENT              | Faz 4.6   |
| 13 | Pentagon Q (past) ≠ future return; filter         | Faz 4.13 ★|
|    | strengthen drops historical alpha sources         |           |

---

## Rollback Önerisi (User Kararı)

**Option A:** Faz 4.13 commit + dökümante (mevcut state, filter aktif)
  - Konservatif XU100 BEAT kayıp, alpha drag tüm profilerde

**Option B:** Faz 4.7 v2'ye rollback (filter geri alınır)
  - Konservatif XU100 BEAT geri kazanılır
  - Damodaran disipline "validate before claim" — hipotez fail rollback

**Option C:** Hibrit — Q gate kaldır, upside > 120 koru
  - Sadece marginal upside ticker'lar drop
  - HALKB Q=40 ama upside 257% → kalır
  - ARENA upside 87% < 120 → drop (kayıp)

**Önerim:** Option B (rollback) Damodaran disiplinine en uygun.
Filter alpha kaybı 6/6 backtest'te confirmed — Lesson #13 finding zaten
yeterli methodology asset. User kararı bekleniyor.

---

## Bilinen Sınırlar

1. Pentagon Q score historical margin stability based, future return
   correlation weak (Faz 5+ research candidate: realized momentum)
2. Profile-dependent fix doğru lever bilinmiyor (Faz 4.14+ candidate:
   sleeve target reduction, not filter strengthen)
3. SMRTG XBRL hâlâ fail
4. Look-ahead bias (Lesson #7) hâlâ var

---

## Output Files

- `apps/api/outputs/portfolio_plan_*_20260428_142457.{csv,json}`
- `apps/api/outputs/backtest_results_20260428_142515.{csv,json,md}`
- `apps/api/outputs/backtest_results_USD_20260428_142516.{csv,json,md}`

---

## Sonraki

- **Karar:** User rollback isteği bekleniyor (Faz 4.7 v2 baseline)
- **Faz 4.14+:** Sleeve target reduction (allocation lever, not filter)
- **Faz 5:** Frontend integration
- **Faz 7+:** Distress model Black-Scholes
