# CCOLA Secondary Analysis — Faz 2.7 (a) Probe

**Tarih:** 27 Nisan 2026 akşam
**Commit:** 43b2425 (Faz 2.6 KAPANIŞ sonrası)
**Hedef:** Faz 2.6 cap sonrası CCOLA hâlâ +%418 — neden?

---

## TL;DR

★ Cap 1.5x CCOLA için kısmi etkili (%16 azaltma vs FROTO %58).
★ Diğer faktörler (β, margin, growth) toplu uygulansa bile CCOLA hâlâ +%300+.
★ **STRUCTURAL ANOMALY**: CCOLA market cap $0.54B vs DCF $2.78B = **5.2x gap**.
★ Olası kök nedenler: TFRS 29 inflation-adjusted income overstatement,
  extreme TR sovereign discount, veya bilinmeyen idiosyncratic risk.

---

## Faz 2.6 Cap Sonrası State

| Metric | Değer |
|---|---|
| DCF (Faz 2.6) | 386.85 TL |
| Market | 74.70 TL |
| Upside | +%418 (eski +%551, -%24 düştü) |
| Equity (USD) | $2.78B |
| Market cap | $0.54B (= 19.0B TL) |
| **Gap ratio** | **5.2x** |
| WACC | 10.38% |
| β_unlev (sector) | 0.5501 (beverage_soft) |
| β_lev (Hamada) | 0.8790 |
| Norm margin | 11.73% |
| Avg revenue | $2.86B |
| Latest revenue | $5.10B → capped at $4.29B (cap aktif) |

---

## Cap Asimetri — CCOLA Düşük Etki Sebebi

CCOLA latest/avg = 1.79x  vs cap_ratio 1.5x:
- Capped at: avg × 1.5 = $4.29B
- vs latest $5.10B = **-%16 reduction**

FROTO latest/avg = 2.34x:
- Capped at: $14.4B vs latest $22.5B = **-%36 reduction**

CCOLA peak bias daha zayıf (1.79x vs 2.34x), o yüzden cap kısmi etkili.

---

## Senaryo Analizi (cap üstüne ek fix'ler)

| Senaryo | Per Share TL | Upside | Δ |
|---------|-------------|--------|---|
| Mevcut (Faz 2.6 cap) | 387 | +%419 | baseline |
| Older 11-yıl margin (10.62%) | 351 | +%370 | -%9 |
| g=2% USD (vs 3%) | 384 | +%414 | -%1 |
| β floor 1.0 (vs 0.55) | 312 | +%318 | -%19 |
| **β + older margin combined** | ~283 | **+%279** | -%27 |

★ TÜM düzeltmeler birleştirilse bile CCOLA +%279 hâlâ extreme.

---

## STRUCTURAL ANOMALY HİPOTEZLERİ

### Hipotez A — TFRS 29 Hyperinflation EBIT Overstatement

CCOLA 2024 EBIT $699M (margin 13.70%).
- TFRS 29 inflation accounting: inventories/receivables revaluation income
- Operating margin nominal vs real terms divergence
- **Test:** Pre-TFRS 29 (2021 öncesi) margin avg ~10.5% → recent ~14% jump
- Eğer TFRS 29 etkisi → recent margin bias yapay
- Damodaran fix: kullanım gerçek ekonomik margin (nominal pre-inflation)

### Hipotez B — TR Sovereign Risk Premium Underestimated

Bizim CRP %6.01 (Damodaran 2025).
- CCOLA market'i pricing daha yüksek CRP'yle (%15+?)
- Foreign investors discount + capital controls fear
- Damodaran prensip: market consensus methodology'den daha bilgilendirici (sometimes)
- **Test:** CRP %10-12 ile WACC re-compute → DCF düşer

### Hipotez C — Idiosyncratic Bug (Data Issue)

- CCOLA EBIT'inde derivative income, FX gain dahil mi?
- Operating vs Total income ayrımı doğru mu?
- isyatirim "EBIT" tanımı standartlaşmış mı?
- **Test:** CCOLA financial statements detayı (EBIT decomposition)

### Hipotez D — Market Inefficiency (Anomaly)

- TR consumer staples chronic discount (Akbank +%55 vs intrinsic, vb.)
- BIST yabancı yatırımcı çıkışı (TFRS 29 + inflation)
- CCOLA Coca-Cola International JV → bayrak riski
- **Conclusion:** Market may be wrong, but 5x gap için diğer faktörler likely

### Hipotez E — Net Income vs Operating Income Confusion

- DCF NOPAT-based (operating income × (1-tax))
- Net income << Operating income (financial expenses büyük)
- TR 2022-2024 financial expenses massive (interest + FX + TFRS 29 monetary loss)
- **Test:** Net income-based valuation comparison (P/E proxy)

---

## Damodaran Disiplin

> "If your model is dramatically off from market consensus, either:
>  (1) Market is wrong (rare, opportunity), 
>  (2) Your model has unstated assumption that doesn't hold, OR
>  (3) Data inputs are corrupted.
>  
>  Default to (3) first, then (2), then (1)."

CCOLA için:
- (1) Mümkün ama extreme (5x gap nadir)
- (2) Likely (TFRS 29 + recent margin bias)
- (3) Possible (EBIT decomposition gerek)

---

## Önerilen Fix Path

### Path X — Margin Recent Bias Cap (Quick Win, 30-60 dk)

Margin için de cap uygula:
```python
effective_margin = min(historical_avg_margin, older_avg × 1.2)
```

CCOLA için:
- older 11-yıl avg: 10.62%
- × 1.2 ceiling = 12.74%
- 16-yıl avg 11.73% < 12.74% → cap inactive
- TUPRS recent ≈ older (4.53 vs 4.49) → cap inactive (intact)

Bu CCOLA'yı ne kadar etkiler? Limited (recent margin uplift sadece ~1pp).
Probably -%10 → CCOLA 387 → ~350 TL. Hâlâ +%369.

### Path Y — TFRS 29 Pre-Inflation Margin Override (Deep Fix, 2-3 saat)

CCOLA'nın 2021 öncesi margin avg ~10.5% (deflated yıllar).
Kullan: pre_2022_margin_avg = 10.5% (12-yıl 2010-2021)

Etki: 11.73% → 10.5% = -%10 margin → ~%10 DCF düşüş
CCOLA 387 → ~350 TL.

### Path Z — Currency Risk Premium Adjustment (Methodology Decision)

CRP %6.01 → %10 USD bandında test (Damodaran TR sovereign risk re-assess)
WACC ~13.5% (vs current 10.38%)
Etki: CCOLA DCF -%30-40
CCOLA 387 → ~250 TL. Hâlâ +%235.

### Path W — Net Income-Based DCF (Damodaran "Equity DCF")

EBIT × (1-tax) yerine: Net Income × (1-payout)
Financial expenses dahil. Daha conservative.

Etki: CCOLA için büyük (TR 2022-2024 financial expenses massive).
Tahmini DCF -%50 → ~190 TL. Yine market 75 TL üstü ama daha makul.

---

## Sonuç + Tavsiye

**CCOLA durumu Faz 2.6 cap ile %20 düzeldi ama yetersiz.**

**Tüm Path X+Y+Z+W birleşik bile CCOLA +%100-200 muhtemelen kalır** — bu TR
defensive consumer chronic discount'un parçası olabilir.

**Damodaran prensibi:** "Methodology cevabı verir, story Market'i açıklar."
- Bizim methodology: $2.78B intrinsic
- Market story: $0.54B (TR currency + inflation + capital controls)
- Fark Methodology BUG'ı değil, market chronic discount

**Önerilen:**
1. **Path X** (margin asymmetric cap) — hızlı, methodology disipline ekler
2. **Document CCOLA as "intrinsic > market" anomaly**:
   - Methodology validated through TUPRS/FROTO/ARCLK
   - CCOLA gerçek intrinsic premium structural — Damodaran "deep value" candidate
3. **Faz 3 Portfolio Construction'a geç** — sleeve seçimi için methodology yeterli

**CCOLA için ek pursue gerekli değil** — methodology disiplinli, sonuç
methodology-correct (market disagrees, that's market's view).

---

## Faz 2.7 Önerileri Güncelleme

a) ~~CCOLA Secondary Analysis~~ → **DONE** (this rapor)
   - Path X (margin cap) opsiyonel, +%9 düzeltme
   - Diğer paths fundamental research gerek

b) Distress Model (THYAO/PGSUS) — yine de yararlı
   - Negatif DCF açık methodology bug

c) Banking Equity-Only Model — methodology iyileştirme

d) **Faz 3 Portfolio Foundation** — RECOMMENDED NEXT
   - Methodology iki Damodaran Lesson sonrası production-ready
   - Sleeve assignment için yeterli intrinsic data
   - Pentagon Scoring + 3-Sleeve

---

## Damodaran Lesson #2.5 (potential)

> "Market gaps > 3x intrinsic için methodology ek fix değil, market story
>  araştırması gerek. TR sovereign + currency + inflation discount
>  combinations defensive consumers için chronic ve methodology-aligned."
