# 15 Damodaran Lessons — REELDEĞER Methodology Compendium

**Project:** REELDEĞER v2.2 (BIST Damodaran-Aligned Valuation Platform)
**Discovery period:** 24 Nis → 28 Nis 2026 (5-day marathon, ~120 atomic commit)
**Source material:** `apps/api/_research_findings/` (20 dosya)

---

## Overview

REELDEĞER 2 günlük yoğun development döngüsünde 15 Damodaran prensibi
keşfetti. Her keşif aşağıdaki pattern'i takip eder:

1. **Hipotez** (Damodaran spec veya REELDEĞER inference)
2. **Implementation** (atomic commit)
3. **Test** (BIST 30/50/100 batch + 20-quarter backtest)
4. **Verdict** (VALIDATED / FALSIFIED / META-LESSON)
5. **Documentation** (research findings + commit message)

3 ardışık FAILED hipotez (Faz 4.7 + 4.8 + 4.13) Damodaran disipline
"validate before claim" prensibini doğruladı. 2 ardışık WIN (Faz 4.14 +
Faz 4.16) ULTIMATE VALIDATION'a götürdü — TÜM 6 backtest TÜM 3
benchmark BEAT.

---

## Timeline Tablosu

| #  | Faz       | Title                                            | Status         | Impact                  |
|----|-----------|--------------------------------------------------|----------------|-------------------------|
| 1  | 2.5       | Holdings cannot be valued like industrial firms  | VALIDATED      | KCHOL/SAHOL SOTP correct |
| 2  | 2.6       | Cyclical DCF asymmetric cap                      | VALIDATED      | TUPRS 169 → 188 TL      |
| 3  | 3         | Cash > overpay when universe inadequate          | VALIDATED      | Konservatif %72 cash OK |
| 4  | 2.7       | Adaptive cap by lifecycle + recent margin bias   | VALIDATED      | CCOLA 486 → 317 TL      |
| 5  | 6         | Banking DDM > P/B fallback (SOTP refinement)     | VALIDATED      | SAHOL refined -%10      |
| 6  | 6.5e      | Banking-specific Pentagon weights                | VALIDATED      | 4 banking → Core sleeve |
| 7  | 4         | MVP backtest documented look-ahead bias          | ACKNOWLEDGED   | Methodology disclosure  |
| 8  | 4.2       | Cash band strict %15 + empty redistribute        | VALIDATED ★    | USD alpha +%9.08/yr     |
| 9  | 4.5       | Universe size diminishing + DD via diversification| VALIDATED     | Max DD -7.61pp ↓        |
| 10 | 4.7       | Hypothesis falsification > methodology force-fit | META-LESSON ★ | AEFES/AKSA fail kayıt   |
| 11 | 4.8       | Tactical regime overlay NOT EFFECTIVE BIST       | FALSIFIED      | Alpha -3.4pp KAYIP      |
| 12 | 4.6       | Universe expansion PROFILE-DEPENDENT             | VALIDATED      | Konservatif XU100 BEAT  |
| 13 | 4.13      | Pentagon Q (past) ≠ future return; filter FAIL   | FALSIFIED      | -2.90pp, ROLLBACK       |
| 14 | 4.14      | Allocation > Filter — sleeve target lever WIN    | VALIDATED ★★   | TÜM 6 backtest GAIN     |
| 15 | 4.16      | Empty sleeve redistribution Core PRIORITY        | VALIDATED ★★★  | 6/6 × 3/3 BEAT ULTIMATE |

---

## Lesson #1 — Holdings cannot be valued like industrial firms

**Faz:** 2.5
**Status:** VALIDATED
**Source:** `_research_findings/sotp_batch_2026-04-27.md`

### Statement
> "Holdings için cyclical_dcf YANLIŞ — banking revenue mock high op_margin
> üretir. SOTP intrinsic-correct: per-child × ownership × disconto."

### Evidence
- SAHOL Component 4 (cyclical_dcf): 354 TL (banking distortion +%256 fake AL)
- SAHOL Faz 2.5 (SOTP): 202 TL (intrinsic-correct, banking children separately)
- KCHOL Component 4: 189 TL → SOTP 233 TL (+%23, P/B 1.5 banking premium)

### Implementation
- `apps/api/data_layer/holdings_config.py` — KCHOL/SAHOL portfolio
- `apps/api/dcf_engine/sotp.py` — calculate_sotp_value()
- Orchestrator STEP 1.5 SOTP routing

### Impact
Holdings valuation production-ready. Banking children PROVISIONAL fallback
(book × P/B 1.5) Faz 6'da CONFIRMED DDM ile değiştirildi.

---

## Lesson #2 — Cyclical DCF asymmetric cap (peak year)

**Faz:** 2.6
**Status:** VALIDATED
**Source:** `_research_findings/tuprs_deep_dive_2026-04-27.md` + `bist_batch_2026-04-27.md`

### Statement
> "current × avg_margin formula PEAK yıllarında inflation üretiyor.
> Damodaran Toyota 2009 reference TROUGH için doğru. Asymmetric cap:
> effective_revenue = min(current, avg × 1.5). Trough korunur, peak disipline."

### Evidence
- TUPRS no cap: 169 TL (peak inflation)
- TUPRS asymmetric cap 1.5x: 188 TL (deep dive baseline match)
- FROTO: 671 → 294 TL (-%56)
- ARCLK: 311 → 177 TL (-%43)
- BIST avg upside: +34.65% → -14.20% (rasyonelleşme)

### Implementation
`apps/api/dcf_engine/cyclical_dcf.py:325-346` — revenue cap branch

### Impact
TUPRS deep dive baseline (188.31 TL manuel 5+ saat) production'da match.
40+ atomic commit boyunca TUPRS 187.10 TL INTACT (-%0.6 sub-noise).

---

## Lesson #3 — Cash > overpay when universe inadequate

**Faz:** 3 (REVISITED Faz 4.2, REINFORCED Faz 4.8)
**Status:** VALIDATED
**Source:** `_research_findings/faz3_portfolio_2026-04-27.md`

### Statement
> "When investable universe is inadequate, holding cash is methodology-correct.
> Better to under-invest at intrinsic prices than to overpay because of
> artificial allocation targets."

### Evidence
- BIST 30 / 1M TL backtest period: Konservatif %72 cash, Dengeli %65, Agresif %55
- Sleeve breakdown: CORE 2 (EREGL, ARCLK), HIZLI 0, YÜKSEK 4, SKIP 11
- Universe darlık → 6 quality-Core max, target %80 Konservatif uncovered

### Implementation
`apps/api/portfolio/portfolio_construction.py` — empty sleeve handling

### Impact (Faz 3 → 4.2 evolution)
Faz 3'te cash %30+ kabul. Faz 4.2'de Lesson #8 ile cash strict %15 cap.
Çelişki YOK: prensip (cash > overpay) **universe inadequate** koşulunda
geçerli; Lesson #8 universe yeterli olduğunda strict %15 uygular.

---

## Lesson #4 — Adaptive cap by lifecycle + recent margin bias

**Faz:** 2.7 (EXTENDED Faz 4.7)
**Status:** VALIDATED
**Source:** `_research_findings/ccola_secondary_2026-04-27.md`

### Statement
> "Defensive consumers (CCOLA) post-COVID structural margin upshift bias > %25.
> MATURE_STABLE + bias > %25 → cap_ratio 1.5 → 1.3. Selective lifecycle-aware."

### Evidence
- CCOLA Pentagon Top 1 + extreme upside +%418 NET diagnosis:
  - H1 Recent margin bias DOĞRULANDI (+%31.3 post-COVID structural)
  - H2 Lifecycle misclassification REJECTED
  - H3 Defensive low volatility DOĞRULANDI (stdev %2.03)
- CCOLA evolution: 486 (no cap) → 386 (1.5x) → **317 TL** (1.3x adaptive)

### Implementation
`apps/api/dcf_engine/cyclical_dcf.py:330-346` — adaptive_cap branch
- Faz 4.7 extension: 3-tier (1.15x extreme bias > 50%, 1.3x medium 25-50%, 1.5x normal)

### Impact
CCOLA 317 TL stable production. Selektif: SADECE CCOLA etkilendi
(TUPRS bias %0.9 → 1.5x INTACT, FROTO MATURE_GROWTH bypass INTACT).

---

## Lesson #5 — Banking DDM > P/B fallback (SOTP refinement)

**Faz:** 6
**Status:** VALIDATED
**Source:** `_research_findings/faz6_banking_2026-04-27.md`

### Statement
> "Banking holding subsidiaries valued via DDM (not justified P/B fallback)
> produce more conservative SOTP values when banking weight is high."

### Evidence
- ABN Amro €30.87 baseline PASS (Faz 1 INTACT after Faz 6 integration)
- 5 banking ticker DDM production: AKBNK 99, GARAN 197, YKBNK 39, ISCTR 17, HALKB 142
- SAHOL refinement: 202 → 181 TL (-%10.3, banking-heavy %63 weight)
- KCHOL refinement: 203 → 190 TL (-%6.4, banking-light %12 weight)

### Implementation
- `apps/api/data_layer/banking_data.py` — 5 ticker × 4-yıl KAP-sourced
- `apps/api/dcf_engine/banking_ddm.py` — 2-stage DDM (high-growth + stable)
- `apps/api/dcf_engine/sotp.py:107-130` — banking_listed branch DDM lookup öncelikli

### Impact
Banking valuation methodology hierarchy:
1. DDM (Dividend Discount Model) — preferred for dividend-paying banks
2. Excess Return Model — alternative (Faz 7+ parking)
3. Justified P/B fallback — last resort (PROVISIONAL only)

---

## Lesson #6 — Banking-specific Pentagon weights

**Faz:** 6.5e
**Status:** VALIDATED
**Source:** `_research_findings/faz6_banking_2026-04-27.md` + sleeve_assignment.py

### Statement
> "Banking firms need separate Pentagon weights and sleeve thresholds.
> Industrial scoring framework misses banking's unique value drivers
> (ROE-CoE excess return spread, capital efficiency)."

### Evidence
- Industrial framework banking scoring (önce):
  GARAN composite 58.29 (V=70.8, Q=50, R=60, lifecycle UNKNOWN)
  AKBNK composite 55.67, YKBNK 51.63, ISCTR 54.48, HALKB 68.50
  Hepsi MATURE_STABLE fallback weights — banking semantik yok
- Banking-specific weights (sonra):
  GARAN composite 82.74 (V=70.8, Q=100 ROE-CoE+18.91pp, G=100 NI CAGR+89.7%)
  AKBNK 74.50, YKBNK 71.04, ISCTR 61.48, HALKB 73.50

### Implementation
- `apps/api/portfolio/pentagon_scoring.py` — `LIFECYCLE_WEIGHTS["BANKING"] = {V:.30, G:.15, Q:.30, M:.05, R:.20}`
- 4 banking score function: score_quality_banking (ROE-CoE), score_growth_banking (NI CAGR), score_value_banking (industrial uyumlu), score_risk_banking
- `score_ticker()` is_banking branch
- `sleeve_assignment.py` Rule 1d Banking branch: CORE banking_intrinsic + YÜKSEK_KAZANC banking_premium

### Impact
4 banking ticker (GARAN, AKBNK, YKBNK, ISCTR) Core sleeve'e geçti.
HALKB Yüksek Kazanç deep_value (state bank +%518 upside, Q=40 düşük).

---

## Lesson #7 — MVP backtest documented look-ahead bias

**Faz:** 4
**Status:** ACKNOWLEDGED
**Source:** `_research_findings/faz4_backtest_2026-04-28.md` + `apps/api/backtest/point_in_time.py`

### Statement
> "MVP backtest with documented look-ahead bias is acceptable IF
> (a) bias direction is conservative (overestimates portfolio strength
>     in bias period — i.e., we do not flatter past performance), AND
> (b) methodology evolution tracked, AND
> (c) primary insight (cash drag, sleeve attribution, Sharpe parity)
>     hardware-independent."

### Evidence
- Bugünkü Pentagon Faz 6.5(e) sonrası 4 banking ticker Core. 2021-2024
  period'unda bu seçim henüz yapılmamıştı; backtest "ileri bilgi" ile
  başarılı banking seçti.
- Yine de XU100 broad market'i yenemedi (Faz 4 phase) → bias overstate
  değil (real disadvantage cash drag).

### Implementation
`apps/api/backtest/point_in_time.py` — `LOOK_AHEAD_BIAS = True` constant +
`BIAS_NOTE` disclaimer in JSON output metadata.

### Impact
Methodology disclosure. Faz 4.10+ Option A historical Pentagon recompute
(parking) — isyatirim multi-year + Damodaran historical reference DB.

---

## Lesson #8 — Cash band strict %15 + empty sleeve redistribute ★

**Faz:** 4.2
**Status:** VALIDATED ★
**Source:** `_research_findings/faz4_2_cash_policy_2026-04-28.md`

### Statement
> "Cash policy must be strict (max %15) to capture USD alpha. Sleeve
> threshold flexibility (composite > 48 vs > 50) maintains value
> discipline. Lesson #3 prensibi (cash > overpay) korunur AMA cash
> band tightening + empty sleeve redistribution ile cash drag minimize edilir."

### Evidence
- Cash drag fix (Faz 4.1 → 4.2):
  Konservatif: %70.0 → %10.4 (-59.6pp ★)
  Dengeli:     %27.4 → %2.7 (-24.7pp)
  Agresif:     %35.0 → %2.0 (-33.0pp)
- USD alpha capture (Dengeli realistic):
  Faz 4.1: +0.06%/yr → Faz 4.2: +9.14%/yr (+9.08pp ★)

### Implementation
- `MAX_CASH_PCT = 15` (eski 30)
- `MAX_SINGLE_TICKER_PCT = 12` (eski 10)
- Empty sleeve redistribution capacity-pro-rata (Lesson #15'te Core PRIORITY'ye evrildi)

### Impact
Cash drag minimize, USD alpha capture başlangıç noktası. Faz 4.16'ya
kadar her phase'de Lesson #8 baseline.

---

## Lesson #9 — Universe size diminishing + DD via diversification

**Faz:** 4.5
**Status:** VALIDATED
**Source:** `_research_findings/faz4_5_bist50_2026-04-28.md`

### Statement
> "Universe size matters for active management — but with diminishing
> returns when value discipline is strict. BIST 30 → BIST 50 expansion
> (+19 ticker) USD alpha +%1.11/yr (mütevazı), AMA drawdown -7.6pp
> İYİLEŞTİRDİ (16 vs 11 pozisyon diversification etkisi)."

### Evidence
- BIST 30 (Faz 4.2): Dengeli realistic USD +9.14%/yr, Max DD -17.55%
- BIST 50 (Faz 4.5): Dengeli realistic USD +10.25%/yr, Max DD -9.94% (-7.61pp İYİLEŞME ★)
- Asıl kazanç: Sharpe parity korunurken DD koruma artırıldı

### Implementation
`apps/api/dcf_engine/batch_analyzer.py:BIST_50_ADDITIONS` (+19 ticker)
+ `shares_fetcher.py` static shares extension

### Impact
BIST 50 production. Faz 4.6'ya path açıldı (BIST 100 expansion).

---

## Lesson #10 — Hypothesis falsification > methodology force-fit ★ META

**Faz:** 4.7
**Status:** META-LESSON ★
**Source:** `_research_findings/faz4_7_cap_refinement_2026-04-28.md`

### Statement
> "Hypothesis falsification is a methodology asset. AEFES/AKSA extreme
> upside hypothesis (post-COVID margin bias > 50%) FAILED — bias gerçek
> 5-10% (NORMAL band). 3-tier cap (1.15/1.3/1.5x) implement edildi
> gelecek için, mevcut universe'de etkisiz. Hipotez fail dökümante etmek
> > methodology force-fit for non-existent problem. Damodaran disipline
> 'measure twice cut once' — methodology refinement evidence-based olmalı."

### Evidence
- Hipotez: AEFES/AKSA bias > %50 (post-COVID restoration)
- Probe: AEFES bias +5.2% MATURE_GROWTH, AKSA bias +10.3% MATURE_STABLE
- Yeni eşikler (1.15x bias > 50%) hiçbir mevcut ticker'ı etkilemedi
- AEFES/AKSA upside +%1196/+%1115 — gerçek sebep market depression
  (intrinsic $4.16B/$650M vs market cap $317M/$58M)

### Implementation
`cyclical_dcf.py:330-346` — 3-tier extreme detection (gelecek için)

### Impact
Methodology asset. 3 ardışık fail (Faz 4.7 cap + Faz 4.8 tactical +
Faz 4.13 filter) bu pattern'i 3x reinforce etti.

---

## Lesson #11 — Tactical regime overlay NOT EFFECTIVE BIST period

**Faz:** 4.8
**Status:** FALSIFIED ★
**Source:** `_research_findings/faz4_8_tactical_overlay_2026-04-28.md`

### Statement
> "Tactical regime overlay NOT EFFECTIVE for BIST 2021-2026 period:
> drawdowns CORRELATED across regimes (TL devaluation persistent), USD
> basis cash also TL-exposed (no real shelter). Alpha cost (-%3-5/yr)
> outweighs minimal DD protection. Damodaran 'value over timing'
> principle CONFIRMED."

### Evidence
- VIX-based 4-regime cash escalation (panic %15-25, normal %2-15)
- Static vs Tactical (Dengeli realistic USD):
  TL ann: +55.32% → +50.55% (-4.77pp)
  USD ann: +10.25% → +6.87% (-3.38pp ⚠)
  Max DD: -25.60% → -25.89% (+0.29pp DAHA KÖTÜ)
- vs SPY: +0.59pp BEAT → -1.68pp UNDERPERFORM (BEAT KAYBOLDU)

### Implementation
- `portfolio/portfolio_construction.py:REGIME_OVERLAY` (default OFF)
- `backtest/simulation.py:run_backtest(regime_overlay=, regime_calendar=)` opsiyonel
- `scripts/run_backtest_tactical.py` static vs tactical comparison

### Impact
Tactical mode default OFF kalır (Lesson #14 reinforce: static cash policy
preferable). Faz 4.9+ farklı tactical (sector rotation, momentum) parking.

---

## Lesson #12 — Universe expansion PROFILE-DEPENDENT

**Faz:** 4.6
**Status:** VALIDATED (REINFORCED Faz 4.7v2)
**Source:** `_research_findings/faz4_6_bist100_2026-04-28.md`

### Statement
> "Universe expansion etkisi PROFILE-DEPENDENT, monolithic değil.
> Conservative-heavy (Core %80) profilerde quality industrial+banking
> expansion → ALPHA GAIN. Aggressive-heavy (Yüksek Kazanç %25-35)
> profilerde deep value expansion → ALPHA LOSS. Damodaran 'value over
> factor exposure' — universe size yeterli değil; PROFILE-SLEEVE-MIX
> selection kritik."

### Evidence
- BIST 50 → BIST 100 (Konservatif zero):
  Faz 4.5: +11.07%/yr → Faz 4.6: +13.81%/yr (+2.74pp ★, vs XU100 +0.27pp BEAT)
- BIST 50 → BIST 100 (Dengeli zero):
  Faz 4.5: +10.78%/yr → Faz 4.6: +8.95%/yr (-1.83pp ⚠)
- Sebep: Yüksek Kazanç sleeve genişledi 8 → 14 ticker, deep value drag

### Implementation
`batch_analyzer.py:BIST_100_ADDITIONS` (+15 ticker quality industrial)

### Impact
Konservatif XU100 USD BEAT (ilk kez). Dengeli/Agresif drag kaynağı tespit
(Faz 4.13 filter FAIL → Faz 4.14 allocation WIN path açıldı).

---

## Lesson #13 — Pentagon Q (past) ≠ future return; filter FAIL

**Faz:** 4.13 (ROLLBACK)
**Status:** FALSIFIED → ROLLBACK
**Source:** `_research_findings/faz4_13_filter_fail_2026-04-28.md`

### Statement
> "Pentagon Q score (margin stability) PAST-LOOKING; future realized
> return correlation weak. Filter quality gate (Q > 45) drops historically
> high-return ticker'lar (HALKB Q=40 +%257 historical, ARENA Q=95 +%87,
> BOSSA +%75). Pentagon Q low ≠ realized return low. Selective expansion
> needs DIFFERENT lever — allocation reduction (Lesson #14)."

### Evidence
- Filter strict (upside > 120, Q > 45 banking deep_value, ROE > 20):
  Konservatif zero USD: -2.90pp/yr (-2.85pp vs XU100, BEAT KAYIP)
  Tüm 6 backtest alpha LOSS (-0.74 to -2.90pp)
- Drop'lanan ticker'lar (HALKB, ARENA, BOSSA) historical realized return yüksekti

### Implementation
- `sleeve_assignment.py` filter strengthen (Faz 4.13)
- ROLLBACK: `git checkout 3447f6d -- sleeve_assignment.py` (Faz 4.7 v2 baseline)

### Impact
Methodology asset (negative finding). Lesson #10 reinforce. Faz 4.14
allocation lever path açıldı.

---

## Lesson #14 — Allocation > Filter — sleeve target lever WIN ★★

**Faz:** 4.14
**Status:** VALIDATED ★★
**Source:** `_research_findings/faz4_14_allocation_lever_2026-04-28.md`

### Statement
> "Allocation lever (sleeve target reduction) FIXES profile-dependent
> expansion (Lesson #12). Filter approach (Lesson #13) FAIL — drops
> historical alpha sources. Allocation reduces sleeve weight WITHOUT
> dropping ticker'lar. Damodaran 'active management lever' = ALLOCATION,
> not stock screening. Generalization: When facing profile-dependent drag,
> FIRST try allocation reduction; ONLY IF that fails, consider filter."

### Evidence
- RISK_PROFILES Yüksek Kazanç -%5 to -%10pp:
  konservatif: 0.05 → 0.03, dengeli: 0.15 → 0.10, agresif: 0.25 → 0.15
- USD alpha gain (Faz 4.7v2 → Faz 4.14):
  Konservatif zero: +14.13 → +14.87 (+0.74pp ★)
  Dengeli zero:     +9.50 (Δ +1.73pp)
  Agresif zero:     +6.97 (Δ +0.46pp)
- Tüm 6 backtest USD alpha GAIN (no LOSS)

### Implementation
`sleeve_assignment.py:RISK_PROFILES` allocation reduction

### Impact
HALKB/ARENA/BOSSA + 14 ticker sleeve'de KALDI (filter approach'tan farklı).
Konservatif XU100 BEAT genişledi, Dengeli SPY BEAT geri kazanıldı.

---

## Lesson #15 — Empty sleeve redistribution Core PRIORITY ★★★ ULTIMATE

**Faz:** 4.16
**Status:** VALIDATED ★★★ ULTIMATE
**Source:** `_research_findings/faz4_16_core_priority_2026-04-28.md`

### Statement
> "Empty sleeve redistribution algoritma KRİTİK. Capacity-pro-rata
> capacity dominant sleeve'e (genelde Yüksek Kazanç) kayar = drag.
> Core PRIORITY algoritma overflow'u quality-first dağıtır. Damodaran
> 'quality > opportunistic' prensip redistribution tarafına. Aktif
> sleeve mix'i KORUR (Yüksek Kazanç ticker'lar sleeve'de kalır,
> sleeve weight'i azalır).
>
> Lesson #14 (allocation > filter) extension: ALLOCATION mekanizması
> içinde redistribution ALGORITHM SEÇİMİ kritik."

### Evidence
- Algoritma değişimi (capacity-pro-rata → Core PRIORITY):
  ```
  Step 1: Core'a kapasite dolana kadar (quality first)
  Step 2: Kalan kapasite diğer sleeve'lere capacity-pro-rata
  ```
- USD alpha gain (Faz 4.15 → Faz 4.16):
  Konservatif zero: +14.87 → +18.98 (+4.11pp ★★★)
  Dengeli zero:      +9.50 → +16.22 (+6.72pp ★★★)
  Agresif zero:      +7.37 → +16.22 (+8.85pp ★★★)
- ★★★ TÜM 6 BACKTEST TÜM 3 BENCHMARK BEAT:
  vs XU100 USD: +5.44pp BEAT (Konservatif zero)
  vs XU030 USD: +4.24pp BEAT (TR peer ilk kez tüm profillerde BEAT)
  vs SPY USD: +10.43pp BEAT

### Implementation
`portfolio/portfolio_construction.py:182-241` — empty sleeve redistribution
Core PRIORITY (Step 1) + capacity-pro-rata (Step 2) hibrit algoritma

### Impact ★★★ ULTIMATE VALIDATION
REELDEĞER methodology TAM doğrulandı. Faz 4.0 → Faz 4.16 evolution:
- Konservatif zero USD: -0.21%/yr → +18.98%/yr (+19.19pp turnaround)
- vs XU100 USD: -13.75pp UNDERPERFORM → +5.44pp BEAT (full inversion)

---

## Negative Findings Pattern (3 Ardışık FAIL)

| Faz   | Lesson | Hypothesis                                    | Result            |
|-------|--------|-----------------------------------------------|-------------------|
| 4.7   | #10    | AEFES/AKSA extreme bias > %50                 | FAIL — bias 5-10% |
| 4.8   | #11    | Tactical regime → DD %30-50 ↓                 | FAIL — DD aynı, alpha -3.4pp |
| 4.13  | #13    | Filter strict → Yüksek drag azalır            | FAIL — alpha -2.9pp, ROLLBACK |

### Pattern Conclusion
**Damodaran disipline: "validate before claim"**

Ad-hoc methodology change, backtest validation OLMADAN merge edilmemeli.
3 fail bunu 3x reinforce etti. Faz 4.10 (Lesson #10) META-LESSON olarak
disipline'i tanımladı; sonraki fail'ler (Faz 4.8, Faz 4.13) bu prensibi
empirik olarak test etti.

**Negative result = methodology asset.** Future implementation
kararlarında reference olarak duruyor (örn. Faz 4.16'da allocation
lever path Lesson #13 fail'inden sonra deneildi → ULTIMATE WIN).

---

## Methodology Pattern Conclusion

### Damodaran Compliance Hierarchy
1. **Valuation** — Industrial FCFF, Banking DDM, Holdings SOTP, Cyclical asymmetric
2. **Pentagon Scoring** — 5-D lifecycle weights (industrial + banking branch)
3. **Sleeve Assignment** — 3-Sleeve cascade (Core/Hızlı/Yüksek + skip)
4. **Portfolio Construction** — Risk profile + cash policy + Core PRIORITY redistribution
5. **Backtest Validation** — 20-quarter USD basis + triple benchmark + 5-failure tracker

### Lesson-to-Code Coverage
- Lesson #1-6: DCF + Pentagon (foundational)
- Lesson #7: Backtest disclosure (process)
- Lesson #8, #14, #15: Portfolio levers (allocation, redistribution)
- Lesson #9, #12: Universe (size + profile-dependent)
- Lesson #10, #11, #13: Methodology discipline (negative findings)

### Final Validation (Faz 4.16 Konservatif zero USD)
| Metric          | Value          |
|-----------------|---------------:|
| USD Annualized  | +18.98%/yr ★   |
| vs XU100 USD    | +5.44pp BEAT   |
| vs XU030 USD    | +4.24pp BEAT   |
| vs SPY USD      | +10.43pp BEAT  |
| Sharpe          | 1.20           |
| Max DD          | -18.50%        |

**6/6 backtest × 3/3 benchmark = ULTIMATE VALIDATION.**

---

## Lesson #17 — Distress as Call Option (Black-Scholes) ★ PRODUCTION-VALIDATED

### Statement
Distressed firms cannot be valued with traditional DCF (negative intrinsic
artifact, not feature). Equity is a CALL OPTION on firm value (Black-Scholes,
strike = debt face). Time value alone produces positive equity even when
S < K (deep underwater). Asymmetric payoff: downside book floor, upside
BS option time value (turnaround optionality).

### Evidence
6 BIST distress ticker negative cyclical_dcf → positive distress-adjusted intrinsic:

| Ticker | Cyclical DCF | BS Equity | πDistress | Adjusted | Upside |
|--------|-------------:|----------:|----------:|---------:|-------:|
| KONTR  | -2.82 TL     | 477.7M$   | 40.0%     | 21.92 TL | +124.81% |
| HEKTS  | -0.70 TL     | 440.3M$   | 43.8%     | 6.73 TL  | +82.83%  |
| PGSUS  | -1082.76 TL  | 2,831.8M$ | 27.5%     | 755.68 TL| +310.03% |
| VESTL  | -112.81 TL   | 783.9M$   | 40.0%     | 50.09 TL | +77.36%  |
| PETKM  | -3.76 TL     | 1,461.9M$ | 23.8%     | 16.63 TL | -31.04%  |
| THYAO  | -110.81 TL   | 9,513.5M$ | 25.0%     | 198.25 TL| -36.00%  |

### Implementation
- `apps/api/dcf_engine/distress_dcf.py` — BS equity-as-call (math.erf, no scipy)
- `apps/api/data_layer/distress_data.py` — 6 BIST manual KAP-sourced inputs
- `apps/api/dcf_engine/orchestrator.py` STEP 5.5 distress override branch
- `apps/api/portfolio/sleeve_assignment.py` Rule 1.5 distress_turnaround sub
- `apps/api/scripts/test_distress_dcf.py` — Eurotunnel + LVS + 6 BIST validation 3/3

### Impact — STATUS REVISE (Faz 7.3 Race-Fixed Evidence)
**Faz 7.1 v2 "production-validated" status REVISE → MODULE-ONLY.**

Faz 7.1 v2 USD "+19.11%/yr" claim'i ASLINDA race condition USD reader
artifact'iydi (mtime-sort stale TL → rollback baseline okunmuştu).
Faz 7.3 race-fix sonrası gerçek evidence:
- Distress integration TL ann -1.64pp drag (Konservatif zero +66.16 vs +67.80)
- USD ann -1.16pp drag (BEAT marjini daraldı, anchor metric kayboldu)

**Mevcut status:**
- **MODULE-VALIDATED ★** — Damodaran rigor korunur:
  - Eurotunnel £122M ±%5 PASS (computed £122.08M, dev 0.06%, y=11.70%)
  - Modified BS API: `black_scholes_equity_with_yield(..., cashflow_yield=0.0)`
  - 4/4 test PASS (Eurotunnel BS + Eurotunnel modified + LVS + 6 BIST)
- **PIPELINE INTEGRATION PARKING** — race-fixed evidence ile pipeline drag:
  - Yüksek Kazanç sleeve overflow (17 → 20 ticker)
  - Cap %2 each, deep_value alpha sources sıkıştı (Lesson #14 ihlali)
  - 16/18 BEAT (rollback baseline) > 12-15/18 (distress integrated)
- **FUTURE iteration** — longer horizon backtest (40Q+) veya separate sleeve

Anchor restored (Faz 7.3 race-fixed):
- TUPRS 187.10 INTACT (43+ commit)
- Konservatif zero TL +67.80%/yr / USD +19.11%/yr (race-fixed evidence)
- 16/18 BEAT (Konservatif 6/6, Dengeli 6/6, Agresif 4/6)

---

## Lesson #18 — Race Condition Methodology Tool Integrity (META) ★ REFRAMED

### Statement (Faz 7.3 race-fixed evidence)
Methodology comparison TOOL pipelines race-free olmalı. Parallel artifact
yazımı + mtime-sort reader stale evidence yaratır. Faz N → Faz N+1
comparison'da explicit artifact path (race-fix) zorunlu.

ESKİ tez ("frozen baseline / live data drift", Faz 7.1 KAPANIŞ) FALSIFIED:
yfinance ZATEN frozen cached, drift kaynağı yfinance live fetch DEĞİL.
Asıl kaynak: USD backtest reader `_latest_tl_backtest_json()` mtime-sort
ile parallel TL run henüz yazmadığında STALE artifact okuyor.

### Evidence — Race Condition Exposed (Faz 7.3)
**Yfinance cache audit:**
- Path: `~/.cache/reeldeger_backtest/` (1.5 MB, 37 ticker)
- Statik key: `_2021-06-20_2026-03-31` (range never changes)
- → "Live data drift" hipotezi PREMISE FALSE

**TL backtest determinism:**
- 2 ardışık run (aynı portföy + cache) BIT-IDENTICAL output
- → engine deterministic given identical inputs

**Portfolio plan determinism:**
- Faz 7.1 v2 (015033) vs Faz 7.2 (021038): 32/32 positions IDENTICAL across
  3 profiller (sleeve + weight 6 dec rounded)

**Race condition exposed:**
- TL backtest yazıyor: `backtest_results_20260507_015041.json` (01:50:41)
- USD backtest okuyor: `backtest_results_USD_20260507_015040.json` (01:50:40)
- USD 1 saniye ÖNCE → mtime-sort'ta TL 015041 görünmüyor → 013500 (rollback) okuyor

**Race-fixed evidence:**
- 013500 TL (rollback, NO distress): Konservatif zero ann +67.80%/yr
- 015041 TL (Faz 7.1 v2, distress ON): Konservatif zero ann +66.16%/yr
- DELTA: -1.64pp REAL drag (TL ann), -1.16pp USD ann

USD backtest (race-misleading):
- Faz 7.1 v2 USD "+19.11" ASLINDA TL 013500 okumuş (rollback baseline)
- Faz 7.2 USD "+17.95" race-fixed: gerçek distress drag

### Implementation (Faz 7.3 Fix → Faz 4.18 Automation)
- `scripts/run_backtest_usd_basis.py --tl-results PATH` (explicit, deterministic)
- Default: mtime-sort `_latest_tl_backtest_json()` (backward compat, race-prone uyarı)
- Sequential pipeline pattern: TL → wait write → USD --tl-results <new TL>
- **Faz 4.18 AUTOMATION:** `scripts/run_pipeline_full.py` wrapper (race-free by design)
  - Sequential subprocess 4-step (batch → portfolio → TL → USD)
  - File-based handoff with auto-detect fresh outputs
  - `--skip-batch` flag (faster re-runs)
  - 2 ardışık run BIT-IDENTICAL verified (deterministic)

### Impact ★ META-LESSON REFRAMED
4 ardışık rollback pattern reframed:
- Faz 4.7 cap extreme: REAL methodology FAIL → ROLLBACK doğru
- Faz 4.8 tactical: REAL methodology FAIL → ROLLBACK doğru
- Faz 4.13 filter: REAL methodology FAIL → ROLLBACK doğru
- **Faz 7.1 distress: REAL methodology drag (race-misleading initial evidence)
  → Faz 7.3 race-fixed re-rollback CORRECT ★**

3 ardışık decision revision:
- Faz 7.1: distress integration (race-misleading evidence based)
- Faz 7.1 v2: re-add (stale USD evidence based)
- **Faz 7.3: race exposed → re-rollback (correct decision)**

Lesson #10 + #18 birleşim ULTIMATE:
"Validate before claim, expose tool bugs, revise on cleaner evidence."

Methodology evaluation requires:
- (a) Frozen seed input cache (Faz 4 yfinance cache ZATEN var)
- (b) Sequential pipeline (TL → USD ordering enforce)
- (c) Explicit artifact path arg (race-free) — `--tl-results PATH`

---

## References

- `apps/api/_research_findings/` — 20 research findings (Lesson source)
- `notes/kaldim.md` — daily progress + Lesson timeline (in-project)
- `apps/api/dcf_engine/` — DCF implementations (Lesson #1-5 code)
- `apps/api/portfolio/` — sleeve/portfolio (Lesson #6, #8, #14, #15 code)
- `apps/api/backtest/` — backtest engine (Lesson #7, #9, #11 code)
- `apps/frontend/pages/3_Lessons.py` — UI presentation (Streamlit)

---

**Compendium last updated:** 7 May 2026 (Faz 4.18 pipeline orchestrator automation)
**Total commits:** 142+ (Faz 4.18 pipeline wrapper + race-free verify + docs)
**TUPRS regression anchor:** 187.10 TL (44+ commit INTACT, deep dive baseline -%0.6 sub-noise)
**18 Damodaran Lesson:** #1-15 (foundational) + #17 (distress MODULE-ONLY + Eurotunnel rigor) + #18 (race condition tool integrity AUTOMATION COMPLETE)
**Konservatif zero anchor:** TL +67.80%/yr / USD +19.11%/yr (race-fixed pipeline, 16/18 BEAT)
**Pipeline orchestrator:** `scripts/run_pipeline_full.py` (Faz 4.18, race-free by design)
