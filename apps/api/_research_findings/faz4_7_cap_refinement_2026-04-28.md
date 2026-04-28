# Faz 4.7 Adaptive Cap Refinement — Research Findings (28 Nis 2026)

**Tarih:** 28 Nisan 2026 (~12:30)
**Commit:** Faz 4.5 (518a23e) → Faz 4.7 (3 atomic chain)
**Hedef:** AEFES +%1196, AKSA +%1115 extreme upside diagnose + 3-tier cap refinement

---

## TL;DR

★ Hipotez ATLENIR ⚠ — AEFES/AKSA bias < %25 (NORMAL band), refinement etkilemiyor
★ Asıl sebep dökümante: AEFES depressed market price, AKSA cap inactive (latest <avg)
★ 3-tier cap_ratio infrastructure eklendi (extreme bias > %50 → 1.15x)
★ Mevcut universe'de hiçbir ticker etkilenmedi (gelecek extreme case için hazır)
★ TUPRS, CCOLA, FROTO INTACT — TUPRS 187.10, CCOLA 317.51, FROTO 294.34
★ Damodaran Lesson #10: Hypothesis falsification dokümantasyonu

---

## Hipotez vs Gerçek (KRİTİK BULGU)

**Hipotez (user önerisi):**
"AEFES, AKSA mature_stable lifecycle + post-COVID extreme margin restoration.
Recent margin bias > %50 (CCOLA'dan büyük). Faz 2.7 cap 1.3x yetersiz.
Yeni cap_ratio 1.15x (extreme bias) gerek."

**Probe sonuçları:**

| Ticker | Lifecycle      | Bias %  | Cap Logic                | Upside    | Hipotez? |
|--------|----------------|--------:|--------------------------|----------:|----------|
| AEFES  | MATURE_GROWTH  | +5.2    | 1.5x (mature_growth def) | +1196.36% | ❌ FAIL  |
| AKSA   | MATURE_STABLE  | +10.3   | 1.5x (bias < 25%)        | +1115.29% | ❌ FAIL  |
| CCOLA  | MATURE_STABLE  | +33.3   | 1.3x ✓ (Faz 2.7)         |  +325.05% | ✓ Faz 2.7 OK |
| TUPRS  | MATURE_STABLE  | +0.9    | 1.5x (bias < 25%)        |   -31.71% | n/a      |
| FROTO  | MATURE_GROWTH  | +48.7   | 1.5x (mature_growth def) |  +186.88% | n/a      |

**Hipotez DOĞRULANMADI:**
- AEFES bias +5.2% (NORMAL band), MATURE_GROWTH lifecycle (mature_stable değil)
- AKSA bias +10.3% (NORMAL band), cap zaten INACTIVE (latest 1.23x < 1.5x)
- Cap_ratio 1.15x extreme threshold (bias >%50) hiçbir ticker'ı etkilemez

**Gerçek upside sebebi:**
- AEFES: Market depressed ($317M cap vs intrinsic $4.16B) — methodology değil
- AKSA: Latest revenue avg'ya yakın, market underpriced (DCF 132 vs market 11)

---

## 3-Tier Cap_Ratio Implementation (Yine de Yapıldı)

**Mantık:** Hipotez fail olsa bile gelecek extreme bias case'leri için
infrastructure güvenli. Damodaran adaptive cap framework (Faz 2.7) generalize.

### Eski (Faz 2.7)
```python
if MATURE_STABLE and bias > 25%:
    cap_ratio = 1.3
else:
    cap_ratio = 1.5
```

### Yeni (Faz 4.7)
```python
is_mature_stable = (
    lifecycle == "MATURE_STABLE"
    and recent_margin_bias_pct is not None
)
if is_mature_stable and bias > 50%:
    cap_ratio = 1.15  # EXTREME (post-COVID restoration band)
elif is_mature_stable and bias > 25%:
    cap_ratio = 1.3   # MEDIUM (Faz 2.7 baseline)
# else: 1.5 (NORMAL default, Toyota peak year pattern)
```

**Etki:** BIST 50'de hiçbir ticker bias >%50 — 1.15x branch hiç hit edilmedi.

---

## Regression Verify (Tüm Anchor INTACT)

| Ticker | Faz 4.5 Value | Faz 4.7 Value | Δ        | Verdict |
|--------|--------------:|--------------:|---------:|---------|
| TUPRS  | 187.10 TL     | 187.10 TL     | 0.00     | INTACT ★ |
| CCOLA  | 317.51 TL     | 317.51 TL     | 0.00     | INTACT  |
| FROTO  | 294.34 TL     | 294.34 TL     | 0.00     | INTACT  |
| AEFES  | 249.42 TL     | 249.42 TL     | 0.00     | (hipotez fail, değişmedi) |
| AKSA   | 132.59 TL     | 132.59 TL     | 0.00     | (hipotez fail, değişmedi) |

**TUPRS deep dive baseline:** 188.31 TL → 187.10 TL (-%0.6 sapma, 30 commit boyunca INTACT)

---

## Backtest Verify (Bit-Identical with Faz 4.5)

| Profile          | Faz 4.5 USD Ann | Faz 4.7 USD Ann | Δ        |
|------------------|----------------:|----------------:|---------:|
| Konservatif zero | +11.07%/yr      | +11.07%/yr      | 0.00     |
| Konservatif real | +10.54%/yr      | +10.54%/yr      | 0.00     |
| Dengeli zero     | +10.78%/yr      | +10.78%/yr      | 0.00     |
| Dengeli real     | +10.25%/yr      | +10.25%/yr      | 0.00     |
| Agresif zero     | +10.40%/yr      | +10.40%/yr      | 0.00     |
| Agresif real     |  +9.87%/yr      |  +9.87%/yr      | 0.00     |

Sleeve breakdown identical: core 8, hızlı 0, yüksek 8, skip 24
Cash levels identical, position weights identical.

---

## Damodaran Lesson #10 (REELDEĞER finding) — Hipotez Falsification

> "Hypothesis falsification is a methodology asset. AEFES/AKSA extreme upside
>  hypothesis (post-COVID margin bias > 50%) FAILED because:
>    (a) Bias measurement gerçek değer değil, bias < %25 NORMAL band
>    (b) AEFES MATURE_GROWTH lifecycle (mature_stable assumed)
>    (c) AKSA cap INACTIVE (latest revenue avg'ya yakın)
>    (d) Real cause: market depression, not methodology overstatement
>
>  Faz 4.7 3-tier cap (1.15x extreme / 1.3x medium / 1.5x normal)
>  yine de implement edildi — gelecek genuine extreme bias case'leri
>  için infrastructure hazır.
>
>  Hipotez fail dokümante etmek > methodology değiştirmek for non-existent
>  problem. Damodaran disipline 'measure twice cut once' — methodology
>  refinement evidence-based olmalı, presumed pattern değil."

---

## 10 Damodaran Lesson Timeline (Cumulative)

| #  | Lesson                                            | Faz       |
|----|---------------------------------------------------|-----------|
| 1  | Holdings cannot be valued like industrial firms   | Faz 2.5   |
| 2  | Cyclical DCF asymmetric cap (peak year)           | Faz 2.6   |
| 3  | Cash > overpay when universe inadequate           | Faz 3     |
| 4  | Adaptive cap by lifecycle + recent margin bias    | Faz 2.7   |
| 5  | Banking DDM > P/B fallback (SOTP refinement)      | Faz 6     |
| 6  | Banking-specific Pentagon weights                 | Faz 6.5 e |
| 7  | MVP backtest documented look-ahead bias           | Faz 4     |
| 8  | Cash band strict %15 + empty sleeve redistribute  | Faz 4.2   |
| 9  | Universe size diminishing returns + DD via div    | Faz 4.5   |
| 10 | Hypothesis falsification > methodology force-fit  | Faz 4.7 ★ |

---

## AEFES/AKSA Real Root Cause (Faz 4.8+ Aday Analizler)

### AEFES Anomalisi
- Lifecycle: MATURE_GROWTH (Anadolu Efes beverage growth markets)
- Latest revenue $8.56B vs avg $4.77B → cap ACTIVE 1.5x ($7.16B effective)
- Norm OI = $7.16B × 0.108 = $773M
- WACC %11.75, equity bridge → $4.16B intrinsic
- Market cap: $317M (extreme depressed)
- Real upside: 13x = +%1196

**Gerçek soru:** Market neden bu kadar düşük fiyatlandırıyor?
  - Russia/Belarus operations (sanctions exposure)
  - Carlsberg JV uncertainty
  - Methodology değil, market sentiment

### AKSA Anomalisi
- Lifecycle: MATURE_STABLE (acrylic fiber niche)
- Latest revenue $1.10B vs avg $0.90B → cap INACTIVE (1.23x < 1.5x)
- Norm OI = $1.10B × 0.121 = $133M
- WACC %12.63, equity bridge → ~$650M intrinsic
- Market cap: $58M
- Real upside: 11x = +%1115

**Gerçek soru:** AKSA chemical cyclical, demand uncertainty?
  - Capital-intensive low-volume specialty
  - Methodology stable, market depressed

### Faz 4.8+ Aday Analizler
- **Distress signal eklenmesi:** market_cap / intrinsic < 0.20 → DISTRESS_DEEP_VALUE flag
- **Reasoning genişletme:** "market depression check" reasoning'e
- **Damodaran Lesson #11 candidate:** Methodology consistency vs market reality
  ("DCF doğru söylüyor, market story farklı" — Lesson #3 eko, banking HALKB pattern)

---

## Bilinen Sınırlar (Faz 4.8+ Parking)

1. AEFES/AKSA extreme upside DEVAM EDİYOR (refinement etkilemedi)
2. Distress signal yok (market_cap/intrinsic < 0.2 flag eklenmeli)
3. Lifecycle classifier MATURE_GROWTH/STABLE bisection AEFES için doğru mu?
4. BIST 100 expansion (Faz 4.6) hâlâ açık (Hızlı Büyüme dolma)
5. Look-ahead bias (Faz 4 Lesson #7) hâlâ var

---

## Output Files

- `apps/api/outputs/bist_batch_LIVE_20260428_122705.{csv,json}`
- `apps/api/outputs/portfolio_plan_*_20260428_122756.{csv,json}`
- `apps/api/outputs/backtest_results_20260428_122758.{csv,json,md}` — TL basis
- `apps/api/outputs/backtest_results_USD_20260428_122759.{csv,json,md}` — USD basis

---

## Sonraki

- **Faz 4.8 (önerilen):** AEFES/AKSA real root cause attack
  - Distress signal (market_cap/intrinsic < 0.2 flag)
  - Lifecycle classifier debug AEFES MATURE_GROWTH
  - "Market depression check" reasoning
- **Faz 4.6:** BIST 100 expansion (Hızlı Büyüme dolar)
- **Faz 4.9:** Option A historical Pentagon recompute
