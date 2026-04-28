# Faz 4.7 v2 IPO-Aware XBRL Fetch — Research Findings (28 Nis 2026)

**Tarih:** 28 Nisan 2026 (~14:00)
**Commit:** Faz 4.6 (3512dd9) → Faz 4.7 v2 (4 atomic chain)
**Hedef:** SMRTG/CWENE/KCAER/KONTR/ENJSA recover + Hızlı Büyüme dolma

---

## TL;DR

★ XBRL graceful fetch — IPO öncesi chunk fail'leri tolerate ediliyor
★ 5 high-growth ticker'dan 4'ü recover: KCAER, CWENE, ENJSA, KONTR (SMRTG hâlâ fail)
★ Konservatif XU100 USD BEAT genişledi: +0.27pp → +0.59pp (zero), +0.03pp BEAT (real)
★ Dengeli/Agresif universe expansion DRAG arttı (Lesson #12 reinforce)
★ Hızlı Büyüme sleeve HÂLÂ BOŞ — yeni ticker'lar mature_growth lifecycle'a düştü
★ TUPRS 187.10 INTACT (38 atomic commit boyunca)

---

## XBRL Fetch Debug Findings

### Probe Sonuçları (5 ticker × 4 financial group × 4 yıl-uzunluğu)

| Ticker | XI_29 | XI_30 | 4-yıl | 8-yıl | 12-yıl | 16-yıl |
|--------|------:|------:|------:|------:|-------:|-------:|
| SMRTG  | 147 ✓ | fail  | ✓     | ✓ 8p  | FAIL   | FAIL   |
| CWENE  | 147 ✓ | fail  | ✓     | ✓ 8p  | FAIL   | FAIL   |
| KCAER  | 147 ✓ | fail  | ✓     | ✓ 8p  | FAIL   | FAIL   |
| KONTR  | 147 ✓ | fail  | ✓     | ✓ 8p  | FAIL   | FAIL   |
| ENJSA  | 147 ✓ | fail  | ✓     | ✓     | ✓ 12p  | FAIL   |
| TUPRS  | 147 ✓ | fail  | ✓     | ✓     | ✓      | ✓ 16p  |

**Bulgu:** Bu 5 ticker post-2017 IPO. Orchestrator'da default `years_back=16`
fetch ederken pre-IPO chunk'lar `ValueError: No items in response` atıyor.

### Çözüm — Graceful Chunk Tolerance

**Eski (`fetch_yearly_extended`):**
```python
results = await asyncio.gather(*tasks)  # Tek chunk fail tüm fetch'i fail eder
```

**Yeni (Faz 4.7):**
```python
raw_results = await asyncio.gather(*tasks, return_exceptions=True)
results = [r for r in raw_results if not isinstance(r, Exception)]
if not results:
    raise ValueError(f"No items in response for {ticker}")
if len(results) < len(raw_results):
    n_failed = len(raw_results) - len(results)
    logger.info(
        f"{ticker}: {n_failed}/{len(raw_results)} chunk(s) failed "
        f"(likely pre-IPO years), continuing with {len(results)} chunk(s)"
    )
```

**Etki:** Post-IPO ticker'lar mevcut yıllarla devam ediyor.
SMRTG hâlâ fail (sebep daha karmaşık, Faz 4.10+ debug parking).

---

## Recover Sonuçları

| Ticker | Eski Status | Yeni Value     | Upside    | Sleeve              |
|--------|-------------|---------------:|----------:|---------------------|
| KCAER  | error       |  60.26 TL      | +430.02%  | Core (mature_growth)|
| CWENE  | error       |  56.06 TL      |  +58.27%  | Core (mature_growth)|
| ENJSA  | error       | 167.99 TL      |  +37.47%  | Core (mature_growth)|
| KONTR  | error       |  -2.82 TL      | -127.39%  | Skip (negative DCF) |
| SMRTG  | error       | error (devam)  | n/a       | Skip (XBRL hâlâ fail)|

**3 ticker Core'a girdi**, 1 ticker negative DCF (Faz 7+ Black-Scholes parking),
1 ticker hâlâ fail (Faz 4.10+ deep debug).

---

## Backtest Sonuçları (USD Basis Phase Comparison)

### Dengeli realistic USD basis (4-yıl 75 quarter trace)

| Phase    | Tickers | USD Cum  | USD Ann   | Sharpe | vs XU100 USD | vs SPY USD |
|----------|--------:|---------:|----------:|-------:|-------------:|-----------:|
| Faz 4.5  | 43      | +60.52%  | +10.25%/y |  0.16  |  -3.29 pp    | +1.70 pp ★ |
| Faz 4.6  | 58      | +51.30%  |  +8.42%/y |  0.11  |  -5.12 pp    | -0.13 pp ⚠ |
| Faz 4.7v2| 63      | +43.26%  |  +7.24%/y |  0.08  |  -6.30 pp    | -1.31 pp ⚠ |

### Konservatif realistic USD basis ★

| Phase    | Tickers | USD Ann      | vs XU100 USD | vs SPY USD |
|----------|--------:|-------------:|-------------:|-----------:|
| Faz 4.5  | 43      | +10.54%/yr   | -2.47 pp     | +1.99 pp   |
| Faz 4.6  | 58      | +13.26%/yr   | -0.28 pp     | +4.71 pp   |
| Faz 4.7v2| 63      | +13.57%/yr ★ | +0.03 pp ★   | +5.02 pp   |

**Konservatif zero (best case):**
- Faz 4.7 v2: +14.13%/yr USD, vs XU100 +0.59pp BEAT ★

---

## PROFILE-DEPENDENT Pattern (Lesson #12 Reinforce)

| Profile          | Faz 4.6 USD | Faz 4.7 v2 USD | Δ        | Verdict |
|------------------|------------:|---------------:|---------:|---------|
| Konservatif zero | +13.81%/yr  | +14.13%/yr     | +0.32pp ★| GAIN    |
| Konservatif real | +13.26%/yr  | +13.57%/yr     | +0.31pp ★| GAIN    |
| Dengeli zero     |  +8.95%/yr  |  +7.77%/yr     | -1.18pp  | LOSS    |
| Dengeli real     |  +8.42%/yr  |  +7.24%/yr     | -1.18pp  | LOSS    |
| Agresif zero     |  +8.26%/yr  |  +6.51%/yr     | -1.75pp  | LOSS    |
| Agresif real     |  +7.74%/yr  |  +5.99%/yr     | -1.75pp  | LOSS    |

**Lesson #12 (Faz 4.6) reinforce:** Universe expansion etkisi PROFILE-DEPENDENT.
Konservatif Core %80 → quality industrial+banking expansion alpha gain
sürdürdü. Dengeli/Agresif Yüksek Kazanç deep_value sleeve'e yeni
volatil ticker'lar (KCAER post-IPO 2020, KONTR neg DCF) eklendi → drag.

---

## Hızlı Büyüme Sleeve HÂLÂ BOŞ

### Lifecycle Classification Sonucu

KCAER, CWENE, ENJSA → **MATURE_GROWTH** (Core'a girdi)
KONTR → negative DCF (Skip)
SMRTG → fetch fail (Skip)

**Sebep:** Lifecycle classifier 4-yıl revenue CAGR'a bakar. Bu ticker'lar
post-IPO 2018-2022 dönemi içinde "young/high-growth" pattern'i bitirmiş —
mature_growth aşamasındalar (revenue CAGR >%20 ama declining).

**Faz 4.10+ Parking — Lifecycle Classifier Debug:**
- Sub-stages: early_growth (post-IPO 2-4y), late_growth, mature_growth
- HIZLI_BUYUME sleeve threshold: stage in (YOUNG, HIGH_GROWTH, EARLY_GROWTH)
- veya Pentagon Growth dimension dominant trigger (ek bypass)

---

## 13 Damodaran Lesson Timeline (Cumulative)

Lesson #13 candidate **YOK** — Faz 4.7 v2 yeni lesson üretmedi, Lesson #12
(profile-dependent expansion) reinforce yaptı. Damodaran disipline:
"validate before claim". Yeni paradigm bulunmadıkça Lesson #13 saymıyoruz.

| #  | Lesson                                            | Faz       |
|----|---------------------------------------------------|-----------|
| 1-12 (önceki, Faz 4.6 sonrası 12 lesson)           |           |
| —  | Faz 4.7 v2 — Lesson #12 reinforce, no new lesson  | Faz 4.7 v2|

**Methodology asset:** Negative result kayıt edildi, gelecek implementations
için reference.

---

## Bilinen Sınırlar (Faz 4.10+ Parking)

1. **SMRTG XBRL hâlâ fail:**
   - 8-yıl chunk OK ama orchestrator'da fetch_financial_statements path'ı fail
   - Detaylı debug Faz 4.10+

2. **Hızlı Büyüme sleeve HÂLÂ BOŞ:**
   - Lifecycle classifier sub-stages eklenmesi
   - Pentagon Growth dimension HIZLI_BUYUME bypass

3. **Dengeli/Agresif universe expansion DRAG:**
   - Selective expansion strategy (Yüksek Kazanç filtre artırma)
   - Faz 4.11 candidate: Pentagon Yüksek Kazanç threshold tighten

4. **AEFES/AKSA extreme upside (Faz 4.7'den):**
   - Distress signal market_cap/intrinsic flag

5. **Look-ahead bias (Faz 4 Lesson #7):**
   - Faz 4.10 Option A historical Pentagon recompute

---

## Output Files

- `apps/api/outputs/bist_batch_LIVE_*_FAZ47v2.{csv,json}`
- `apps/api/outputs/portfolio_plan_*_FAZ47v2.{csv,json}`
- `apps/api/outputs/backtest_results_*_FAZ47v2.{csv,json,md}`

---

## Sonraki

- **Faz 4.10+:** SMRTG XBRL deep debug + lifecycle classifier sub-stages
- **Faz 5:** Frontend integration (UI dashboard)
- **Faz 7+:** Distress model Black-Scholes (KONTR neg DCF + diğerleri)
