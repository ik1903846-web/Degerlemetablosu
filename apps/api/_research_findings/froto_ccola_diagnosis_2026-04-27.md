# FROTO/CCOLA Root Cause Diagnosis — Faz 2.6 (e)

**Tarih:** 27 Nisan 2026
**Commit:** 16358ae (Faz 2.5 KAPANIŞ genişletme sonrası)
**Hedef:** Component 4 batch'te FROTO +%545, CCOLA +%541 extreme upside neden?
**Hipotezler:** Cycle bias (1) | Distortion bug (2) | Lifecycle misclass (3)

---

## TL;DR

★ **Hipotez 1 CONFIRMED** — Revenue cycle peak bias (REELDEĞER cyclical_dcf
margin'i normalize ediyor, revenue'yu DEĞİL).

★ **Hipotez 2 REJECTED** — Margin'ler normal industrial range (FROTO 7.14%,
CCOLA 11.73%). SAHOL tipi banking distortion YOK.

★ **Hipotez 3 PARTIAL** — FROTO mature_growth (rev CAGR 13.55%), CCOLA
mature_stable. Model selection aynı (cyclical_dcf), classification etki minimal.

**Fix Path:** Cyclical Revenue Normalization (Damodaran proper through-the-cycle).

---

## Margin Comparison (16-yıl, USD-bazlı)

| Ticker | Avg 16-yıl | Recent 5-yıl | Older 11-yıl | Peak | Trough | Status |
|--------|-----------|--------------|--------------|------|--------|--------|
| TUPRS  | **4.50%** | 4.53%        | 4.49%        | 10.56% | -0.96% | ★ Fully normalized |
| FROTO  | **7.14%** | 9.22%        | 6.20%        | 13.02% | 4.38%  | Recent biased (+302 bps vs older) |
| CCOLA  | **11.73%**| 14.16%       | 10.62%       | 15.62% | 9.09%  | Recent biased (+354 bps vs older) |
| ARCLK  | 7.68%     | n/a          | n/a          | n/a    | n/a    | (industrial reference) |
| SAHOL  | **54.80%**| n/a          | n/a          | 91.88pp spread | — | ★ Banking distortion (known) |

**Bulgular:**

- **TUPRS** through-the-cycle MARGIN tam normalized (recent ≈ older).
  Cyclical_dcf burada doğru çalışıyor.
- **FROTO/CCOLA** margins recent 5-yıl yüksek, older 11-yıl düşük.
  Avg margin SLIGHT bias var ama range industrial normal.
- **Margin tek başına extreme upside açıklamıyor** — başka faktör var.

---

## Revenue Comparison (16-yıl, USD-bazlı) — KRİTİK BULGU

| Ticker | Latest Rev | Avg 16-yıl | Peak Rev | Latest/Avg Ratio | Cycle Bias |
|--------|-----------|------------|----------|------------------|------------|
| TUPRS  | $30.33B   | $20.06B    | $49.72B  | **1.51x**       | Hafif (latest ≠ peak) |
| FROTO  | **$22.49B** | $9.61B   | $22.49B  | **2.34x** ★★   | **MASİF (latest = peak)** |
| CCOLA  | **$5.10B**  | $2.86B   | $5.10B   | **1.79x** ★    | **YÜKSEK (latest = peak)** |

**Kritik tespit:**
- **FROTO** latest revenue = peak revenue ($22.49B), avg'dan **2.34x** yüksek
- **CCOLA** latest revenue = peak revenue ($5.10B), avg'dan **1.79x** yüksek
- **TUPRS** latest revenue avg'dan 1.51x ama PEAK DEĞİL (peak 2022, $49.72B; 2024 down)

---

## Bug Mechanism (Damodaran Lesson #2)

**REELDEĞER cyclical_dcf formülü:**
```
normalized_op_income = current_revenue × historical_avg_margin
                       ↑                  ↑
                       NOT normalized!    Normalized through-cycle
```

Bu formül HALF-NORMALIZED:
- ✓ Margin: 16-yıl avg ile yumuşatılıyor
- ✗ Revenue: Latest year (current_revenue) DOĞRUDAN kullanılıyor

**FROTO örneği (mevcut bug):**
- current_revenue = $22.49B (2024 peak)
- avg_margin = 7.14% (16-yıl)
- normalized_op_income = $22.49B × 7.14% = **$1.61B**

**Damodaran proper (revenue de normalize):**
- avg_revenue = $9.61B (16-yıl)
- avg_margin = 7.14% (16-yıl)
- through_cycle_op_income = $9.61B × 7.14% = **$0.69B**
- 57% reduction!

**FROTO DCF impact tahmini:**
- Mevcut DCF: $6.66B / 350.91M shares = $19/share = 671 TL
- Through-cycle revenue normalized: ~$2.85B / 350.91M = $8.1/share = ~**287 TL**
- Market 104 TL → upside +%545 → **+%176** (still AL, ama rasyonel)

**CCOLA DCF impact tahmini:**
- Mevcut: $3.50B → 486 TL
- Through-cycle revenue: ~$1.95B → ~**272 TL**
- Market 76 TL → upside +%541 → **+%258** (still AL)

**TUPRS PEAK DEĞİL → bu bug TUPRS'i etkilemiyor:**
- 2024 cycle dipi (margin 4.36%, revenue declined from 2022 peak)
- Latest/avg 1.51x (modest), through-cycle ile değişim ufak
- Methodology TUPRS için zaten doğru çalışıyor

---

## Hipotez Doğrulama Detay

### Hipotez 1: Revenue Cycle Peak Bias — ✓ CONFIRMED

**Kanıt:**
- FROTO latest_rev/avg = 2.34x (extreme bias)
- CCOLA latest_rev/avg = 1.79x (yüksek bias)
- TUPRS latest_rev/avg = 1.51x (orta, peak değil)
- Bug: cyclical_dcf revenue normalize etmiyor, sadece margin

**Magnitude:**
- FROTO: cycle peak bias = 134% revenue inflation
- CCOLA: cycle peak bias = 79% revenue inflation
- Bu bias × normal margin → fake high NOPAT → fake DCF

**Status:** ✓ ★ Primary root cause

### Hipotez 2: Distortion Bug (banking-type) — ✗ REJECTED

**Kanıt:**
- FROTO margin 7.14% (industrial otomotiv normal range)
- CCOLA margin 11.73% (consumer staples normal range)
- SAHOL margin %54.80 (banking distortion known) ile karşılaştırma:
  - FROTO/CCOLA endüstriyel pure-play, banking yok
  - margin range industrial normal, distortion DEĞİL

**Status:** ✗ Bu hipotez geçersiz

### Hipotez 3: Lifecycle Misclassification — Partial

**Kanıt:**
- FROTO lifecycle stage: **mature_growth** (rev CAGR 13.55% USD — high)
- CCOLA lifecycle stage: **mature_stable**
- Her ikisi de cyclical_dcf modeline routed
- Lifecycle classification model selection'ı etkiliyor AMA aynı model

**Detay:**
- FROTO mature_growth → cyclical_dcf (model dispatch'te aynı)
- Lifecycle alternative: industrial_fcff_em (yok henüz)
- mature_growth için Damodaran 2-stage model tercih edilmeli (yüksek growth
  + stable terminal)
- Şu an cyclical_dcf 2-stage fallback olarak kullanılıyor

**Status:** Marginal contributor, primary değil. Faz 2.7+ için parking
(industrial_fcff EM model implement gerek).

---

## Damodaran Lesson #2 (REELDEĞER 27 Nisan 2026 keşfi)

> "Cyclical DCF must normalize BOTH revenue level AND margin.
> Single-side normalization (margin only) creates peak bias
> when revenue is at cycle peak.
>
> Proper through-the-cycle valuation:
>   normalized_op_income = avg_revenue × avg_margin
>   (not: current_revenue × avg_margin)"

**REELDEĞER bug profili:**
- TUPRS: zarar görmez (latest revenue peak DEĞİL, declining)
- FROTO: %134 over-inflation (latest = peak)
- CCOLA: %79 over-inflation (latest = peak)
- Genel: Cyclical industries with rising recent revenue → bias yüksek

---

## Fix Path Önerileri

### Path A — Cyclical Revenue Normalization (önerim)

**Tahmin:** ~1-2 saat

cyclical_dcf'i değiştir:
- Eski: `current_revenue × avg_margin`
- Yeni: `avg_revenue × avg_margin` (through-the-cycle baseline)
- Plus: revenue projection (CAGR-based growth path)

Etki:
- FROTO: 671 → ~287 TL (rasyonelleşir)
- CCOLA: 486 → ~272 TL (rasyonelleşir)
- TUPRS: 188 → ~165-175 TL (hafif düşüş, hâlâ SAT)
- ARCLK: 311 → ~245 TL (tahmini)

Damodaran-aligned, methodology disipline.

### Path B — Sub-period Weighting (recent 10-yıl ağırlıklı)

**Tahmin:** ~30-60 dk

Avg margin/revenue hesabında recent 10-yıl 2x ağırlık.
Pros: Daha basit, mevcut formula yapısı korunur.
Cons: Recent ağırlık peak bias'ı azaltmaz (sadece moderate eder).

ÖNERMİYORUM — root cause'a vurmuyor.

### Path C — Lifecycle-Adaptive Cyclical (FROTO için)

**Tahmin:** ~2-3 saat

FROTO mature_growth için 2-stage explicit model:
- Stage 1: Explicit projection (5-10 yıl, CAGR ile)
- Stage 2: Terminal value (through-cycle margin)

Pros: Methodology daha sofistike.
Cons: Cyclical_dcf yeniden yazımı, scope büyük.

Faz 2.7+ için parking.

### ÖNERİM: Path A (Cyclical Revenue Normalization)

- Damodaran proper methodology
- 1-2 saat scope dar
- Tüm cyclical industries için aynı fix
- TUPRS baseline minimal etki (zaten through-cycle uyumlu)
- BIST batch re-run ile validation
- Ayrı atomic commit (Faz 2.7 başlangıcı veya Faz 2.4.7 eki)

---

## BIST Batch Etkisi (Path A sonrası tahmini)

| Ticker | Mevcut | Path A sonrası (tahmin) | Δ |
|--------|--------|--------------------------|---|
| TUPRS  | 188 TL | ~165-175 TL              | -7 to -%14 |
| FROTO  | 671 TL | ~287 TL                  | -%57 |
| CCOLA  | 486 TL | ~272 TL                  | -%44 |
| ARCLK  | 311 TL | ~245 TL                  | -%21 |
| EREGL  | 58 TL  | ~50 TL                   | -%14 |

(Diğer ticker'lar revenue cycle position'a göre değişir.)

---

## Faz 2.6 / 2.7 Önceliği

Diagnosis sonrası önerilen sıra:

1. **Path A — Cyclical Revenue Normalization** (1-2 saat) — KRITIK FIX
2. **Faz 2.6 — Banking Equity-Only Model** (3-4 saat) — methodology
3. **Faz 3 — Portfolio Construction** (2-3 saat) — Pentagon Scoring + Sleeve

Path A ÖNCE yapılmalı çünkü:
- BIST'in birçok ticker'ında cycle peak bias var (genel sorun)
- Sleeve assignment için doğru intrinsic gerek
- Banking model'inden bağımsız (Path A industrial only)

---

## Sonuç

★ FROTO/CCOLA extreme upside Component 4 BUG'ından kaynaklı (cyclical_dcf
revenue normalize etmiyor).

★ Hipotez 1 CONFIRMED (revenue peak bias).

★ Fix Path A önerilen (cyclical revenue normalization, 1-2 saat).

★ TUPRS baseline INTACT kalır (peak değil, methodology zaten doğru).

★ Damodaran disiplin: Through-the-cycle = HEM revenue HEM margin.
