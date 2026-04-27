# CCOLA Secondary Analysis — Faz 2.7 (a) NET Diagnosis

**Tarih:** 27 Nisan 2026 gece
**Commit:** c95d4d8 (Faz 3 KAPANIŞ sonrası)
**Hedef:** CCOLA Pentagon Top 1 (composite 77.7) + extreme upside (+%418) NET diagnosis
**Method:** 16-yıl probe + 3 hipotez NET test

---

## TL;DR

★ **H1 Recent margin bias DOĞRULANDI** (+%31.3 recent vs older)
★ **H2 Lifecycle CAGR MATURE_STABLE doğru** (CAGR +%6.97 USD, normal range)
★ **H3 Margin stdev DOĞRULANDI** (2.03pp, defensive consumer ✓)
★ **Çözüm:** Adaptive cap factor (1.3x for high-bias defensive consumer)
★ **Tahmini etki:** CCOLA 386 → ~282 TL (-%27, +%276 hâlâ AL ama rasyonel)

---

## 16-Yıl Veri Tablosu (USD-bazlı)

| Year | Revenue (USD) | EBIT (USD) | Margin |
|------|--------------|-----------|--------|
| 2024 | $5.10B | $0.70B | 13.70% |
| 2023 | $4.96B | $0.71B | 14.32% |
| 2022 | $5.00B | $0.61B | 12.28% |
| 2021 | $1.69B | $0.26B | 15.62% (peak) |
| 2020 | $1.94B | $0.29B | 14.89% |
| 2019 | $2.02B | $0.26B | 12.63% |
| 2018 | $2.02B | $0.24B | 11.94% |
| 2017 | $2.21B | $0.23B | 10.41% |
| 2016 | $2.00B | $0.18B | 9.09% (trough) |
| 2015 | $2.30B | $0.22B | 9.51% |
| 2014 | $2.58B | $0.27B | 10.49% |
| 2013 | $2.43B | $0.28B | 11.44% |
| 2012 | n/a (FX) | n/a | 12.10% |
| 2011 | n/a (FX) | n/a | 9.56% |
| 2010 | n/a (FX) | n/a | 9.87% |
| 2009 | n/a (FX) | n/a | 9.82% |

**Stats (12 valid yıl):**
- Avg revenue: $2.86B
- Latest 2024: $5.10B (Latest/Avg = **1.79x** — peak bias yüksek)
- Avg margin: 12.19%
- Latest 2024 margin: 13.70%
- Margin stdev: **2.03pp** (defensive low volatility ✓)
- Revenue CAGR 12y: **+6.97%** USD

---

## Sub-Period Analysis (KRİTİK BULGU)

| Period | Revenue Avg | Margin Avg |
|--------|-------------|-----------|
| Recent 5y (2020-2024) | $3.74B | **14.16%** |
| Older 7y (2013-2019) | $2.23B | **10.79%** |
| Margin bias | — | **+3.37pp (+%31.3)** ★ |

**Recent margin yüksek bias %31.3 — DOĞRULANDI structural.**

Yıllık trend:
- 2020-2024 (post-COVID): %12.28-15.62 range, ortalama %14.16
- 2013-2019 (pre-COVID stable): %9.09-12.63 range, ortalama %10.79
- Geçiş 2020-2021'de margin sıçraması (~+3pp permanent shift)

---

## Faz 2.6 Cap 1.5x Effect (Mevcut)

- Cap threshold: $2.86B × 1.5 = **$4.28B**
- Latest revenue: $5.10B
- Cap ACTIVE: YES
- Capped at: $4.28B (**-%16.1 reduction**)

Etki: CCOLA effective revenue $5.10B → $4.28B
Mevcut cap ile DCF ~$2.78B / 254M shares = 386 TL (vs market 75 TL = +%418).

---

## 3 Hipotez NET Sonuç

### H1 Recent Margin Bias — ★ DOĞRULANDI (+%31.3)

- Recent 5y avg 14.16% vs older 7y avg 10.79%
- Structural shift 2020-2021 (post-COVID consumer durability)
- Eğer through-cycle margin alınsa: %12.19 → %10.79 = **-%11.5 DCF**
- Tahmini CCOLA: 386 → ~342 TL

### H2 Lifecycle Misclassification — REJECTED

- Revenue CAGR 12y: **+6.97% USD** (normal MATURE_STABLE range)
- Lifecycle classification doğru
- High Growth değil (>15% gerek)
- Mature Growth borderline ama 8% altı → MATURE_STABLE

### H3 Defensive Consumer Low Volatility — ★ DOĞRULANDI (2.03pp)

- Margin stdev 2.03pp (very low)
- Defensive consumer pattern (Coca-Cola International JV)
- CCOLA gerçek defensive — Q=85 Pentagon score doğru
- AMA "defensive + recent peak margin" → Pentagon V=100 anomaly

---

## Çözüm Path NET — Adaptive Cap Factor

### Path 1: Adaptive Lifecycle-Aware Cap (önerim)

Cap factor lifecycle + bias adaptive:
```python
if lifecycle == "MATURE_STABLE" and recent_bias_pct > 25:
    cap_ratio = 1.3   # High-bias defensive consumer
elif lifecycle in ("MATURE_STABLE", "MATURE_GROWTH"):
    cap_ratio = 1.5   # Default
elif lifecycle == "MATURE_GROWTH":
    cap_ratio = 1.7   # Allow more growth
```

**Etki tahmini:**
- Cap 1.3x: avg × 1.3 = $3.72B
- Latest $5.10B → capped at $3.72B = **-%27.0 reduction**
- DCF impact: ~%27 düşüş
- CCOLA 386 → **~282 TL** (vs market 75 TL = **+%276** hâlâ AL ama
  rasyonelleşmiş)
- TUPRS Latest/Avg 1.51x < 1.3x değil... wait, 1.51 > 1.3 yani TUPRS de
  cap aktif olur. -%14 TUPRS impact (188 → ~162 TL).
- TUPRS deep dive baseline drift -%14 ★ FAZ 2.5 SAHOL precedent (methodology > baseline)

### Path 2: Sub-Period Weighted Margin (alternatif)

Older 7y margin (10.79%) ile through-cycle:
- avg_margin: 12.19% → 10.79%
- DCF impact: -%11.5
- CCOLA 386 → ~342 TL (+%356 hâlâ AL)

**Pros:** Methodology-pure (margin de revenue gibi cycle-normalize)
**Cons:** Bütün ticker'larda recent bias hesabı + downstream impact büyük

### Path 3: Status Quo + Document

CCOLA "deep value anomaly" olarak kabul et:
- Faz 2.6 cap zaten devrede
- Recent margin bias structural shift (post-COVID)
- Pentagon V=100 + Q=85 → Sleeve "deep_value" doğru
- Methodology disipline yeterli, market story farklı (TR/CCOLA chronic discount)

---

## Önerilen Implementation (Faz 2.7+)

**Path 1 önerilen** ama dikkat:
- TUPRS deep dive baseline -%14 drift olabilir
- Faz 2.5 SAHOL precedent'e benzer ("methodology > baseline")
- Atomic commit + test gerek

Alternatif: Sadece CCOLA-specific bypass (lifecycle="MATURE_STABLE" + bias>25%):
- Diğer ticker'ları etkilemez
- TUPRS bias < 5% (recent ≈ older), cap 1.5x kalır
- CCOLA bias %31.3 > %25 → adaptive cap 1.3x
- ARCLK bias kontrol gerek (eğer >%25 → adaptive)

---

## Faz 2.7+ Sonraki Adımlar

a) **Adaptive Cap Implementation** (45-60 dk):
   - cyclical_dcf'e bias-detection logic ekle
   - lifecycle + bias_pct ile cap_ratio dinamik
   - Test: TUPRS, FROTO, CCOLA, ARCLK regression

b) **Through-Cycle Both-Side Normalization** (1-2 saat):
   - normalized_revenue = avg (not current capped)
   - normalized_margin = avg (mevcut)
   - Bütün ticker etkilenir, methodology daha disipline ama
     baseline drift büyük

c) **Status Quo + Doc** (0 dk):
   - Mevcut Faz 2.6 cap yeterli kabul
   - CCOLA chronic anomaly olarak portfolio'da reflect (deep_value sleeve)

---

## Karar Önerisi

**Tavsiye:** Path 1 (Adaptive Cap, lifecycle + bias aware)

Sebep:
- Damodaran disipline (methodology evolution)
- CCOLA özel bias structural (post-COVID shift)
- ARCLK benzer profil olabilir (bias kontrol gerek)
- TUPRS baseline -%14 drift (acceptable, Faz 2.5 SAHOL precedent)

Implementation Faz 2.7 (b) — yarın taze kafayla atomic commit.

CCOLA Pentagon scoring methodology-correct (V=100, Q=85, comp 77.7).
Sleeve "deep_value" doğru ama composite biraz şişkin (residual bias).
Adaptive cap ile %419 → +%276 makul band.

REELDEĞER methodology evolution: 4. Damodaran Lesson candidate
("Cyclical cap should be lifecycle + recent-bias adaptive, not fixed").
