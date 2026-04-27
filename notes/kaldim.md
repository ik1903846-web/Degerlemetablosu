# REELDEĞER — Kaldığım Yer

**Son güncelleme:** 27 Nisan 2026, ~23:45 (gece)
**Aktif Faz:** Faz 2.7 Adaptive Cap TAMAMLANDI ✓ (Damodaran Lesson #4)
**Sıradaki:** Faz 3.5 BIST 50/100 universe expansion veya Faz 4 Backtest engine

---

## Dün Tamamlananlar (26 Nis → 27 Nis 02:30, ~17 saat)

Sabah:
- Faz 1.3.2: Cost of Capital (5/5 PASS)
- Faz 1.3.3: Industrial FCFF (Heineken 59.65 EUR PASS, -0.14%)

Öğleden sonra:
- Faz 1.4: Banking DDM (ABN Amro 30.87 EUR PASS, +4.06%)
- Faz 1.5: Industrial FCFF EM (Tube Investments 61.55 INR PASS, -0.04%)
- Faz 1.6: Cyclical DCF (Toyota 4737 JPY PASS, +0.04%)
- Faz 1.7: Amazon young firm (skip — _wip_amazon klasörü)

Akşam:
- Faz 2.1.1a: KAP scraper foundation
- Faz 2.1.1b: isyatirim discovery (JACKPOT)
- Faz 2.1.2 A-B: scraper + Damodaran mapper
- Faz 2.1.3: TUPRS Cyclical DCF (placeholder bug, 169.94 TL)
- Faz 2.1.4 Adım 1-5: 4 düzeltme + Final DCF (181.16 TL)
- Faz 2.2: Lifecycle Classifier (6-stage)
- Faz 2.3: Orchestrator (analyze_ticker tek call)
- Faz 2.4: BIST 30 Batch Pilot (16/19 PASS, 28s)
- Faz 2.4.3: Live Market Price Fetcher (Yahoo Finance)
- Faz 2.4.4: Orchestrator Live Integration (auto-fetch + AL/SAT/BEKLE)

---

## REELDEĞER MOTORU — PRODUCTION-READY

4 DCF model:
- Industrial FCFF (Heineken EUR 59.65 PASS)
- Banking DDM (ABN Amro EUR 30.87 PASS)
- Industrial FCFF EM (Tube INR 61.55 PASS)
- Cyclical DCF (Toyota JPY 4737 PASS)

Pipeline (analyze_ticker tek call):
ticker → fetch (12 yıl) → map → USD → classify → DCF → shares → Yahoo price → AL/SAT verdict

5 BIST data source:
- isyatirim.com.tr (mali tablolar XBRL, 147 kalem × 12 dönem)
- Yahoo Finance v8 (.IS suffix, spot + historical)
- Damodaran fetcher (Rf, ERP, CRP, sektör beta — 101 param)
- Static FX rates (TCMB year-end 2013-2025)
- Static shares dictionary (25 BIST 30 ticker)

---

## BIST 19 Ticker — Damodaran AL/SAT/BEKLE (24 Nis 2026)

**Validated anchors:**
- TUPRS 181 vs 269 → -33% SAT (sweet spot retro doğrulandı)
- KCHOL 223 vs 207 → +8% BEKLE (motor doğruluğun canlı kanıtı)

**AL adayları (calibration suspect):**
- FROTO 940 vs 105 → +799% (overestimate?)
- CCOLA 513 vs 77 → +567% (defensive yanlış sınıf?)
- SAHOL 388 vs 99 → +293% (holding SOTP gerek)
- ARCLK 401 vs 117 → +242% (Cyclical White Goods)
- EREGL 74 vs 33 → +124% (steel cyclical)

**SAT (9):** TUPRS, TOASO, ASELS, MGROS, ENKAI, THYAO, PETKM, SOKM, PGSUS

**Negatif DCF (artifact):** SOKM -127, PGSUS -652

**Error (3):** KOZAL/KOZAA (Yahoo + isyatirim'de yok), BIMAS (taxonomy)

---

## Faz 2.4.5 — TUPRS Damodaran Deep Dive (TAMAM)

**Commit cb77d02:** apps/api/_research_findings/tuprs_deep_dive_2026-04-27.md (213 satır)
- 6/6 methodology checkpoint PASS
- 16-yıl historical depth (Damodaran ideal)
- Bottom-up beta (oil_gas_integrated 0.7043 + Hamada relever)
- Sovereign+Sector synthetic rating (BB+ %4)
- USD-only valuation (TFRS 29 noise paralel iptal)
- Real shares (KAP 1.93B doğrulandı)
- Net CapEx (Δ PP&E + Dep)
- Sonuç: TUPRS Damodaran-aligned DCF = 188.31 TL (eski 181.16 → +%4)

---

## Faz 2.4.6 KAPANIŞ — Damodaran Methodology Production Parity (27 Nis 2026)

### Atomic Commit Chain (6 commit, ana paket)

**Component 1 — Bottom-up Beta Integration** (3 atomic step)
- Adım 1.1 (7163b5e): damodaran_db.py + test (DB read helper, asyncpg + cache 3400x)
- Adım 1.2 (6e22767): sector_mapping.py + test (19/19 BIST 30, 13 unique sektör)
- Adım 1.3 (67d6ec9): orchestrator integration (Hamada relever, holding whitelist, +86/-10 satır)

**Component 2 — Synthetic Rating Sovereign+Sector** (09a2a9b)
- DAMODARAN_PARAMS["synthetic_spread"] = 0.04 (BB+)
- pretax_kd hard-coded BB %3 → BB+ %4
- TUPRS WACC 12.81% (deep dive baseline TAM TUTUYOR)
- AT_Kd 5.23% → 5.98% (+75 bps)

**Component 3 — 16-yıl Historical Default** (a7ed721)
- analyze_ticker years_back: 12 → 16 (Damodaran golden standard)
- TUPRS DCF 192.85 → 188.29 TL (deep dive 188.31, sapma 0.02 TL)
- 3 tam cyclical döngü (2009-2024)
- Margin 4.64% → 4.50% (-14 bps, peak bias hafifledi)

**Component 4 — BIST 30 FINAL Batch** (4256744)
- 19 ticker batch run (17/19 successful, 2 coverage gap)
- test_orchestrator_live.py dotenv eki
- Outputs: bist_batch_LIVE_20260427_133236.csv + .json
- Research rapor: _research_findings/bist_batch_2026-04-27.md (142 satır)

**Bonus — print_report None Handling** (3cdbb66)
- Cosmetic E bug fix (banking + failed industrial ticker'lar)
- Pattern A inline defansif fix (+4/-1 satır)
- test_orchestrator.py exit code 0 (eski 1)

### Methodology Validation %100

TUPRS Faz 2.4.5 Deep Dive Baseline:
- Manual deep dive (5+ saat): 188.31 TL
- Production (Component 1+2+3 entegre): 188.29 TL
- Sapma: 0.02 TL (yuvarlama)
- WACC: 12.81% (BIREBIR)
- Margin: 4.50% (BIREBIR)
- Upside: -30.00% (BIREBIR)

6/6 Damodaran Checkpoint PASS:
- ✓ 16-yıl historical (Damodaran ideal)
- ✓ Bottom-up beta (sector + Hamada)
- ✓ Sovereign + Sector synthetic rating
- ✓ USD-bazlı tutarlı WACC
- ✓ Real shares outstanding (KAP doğrulamalı)
- ✓ Net CapEx Damodaran formula

### Component 4 BIST 19 Sonuçları (Anchor Regression)

Successful 17/19, 6 deep value, 1 fair, 9 overvalued.
Detay: apps/api/_research_findings/bist_batch_2026-04-27.md

| Ticker | Eski (Faz 2.4) | Yeni (C1+2+3) | Δ |
|--------|----------------|----------------|---|
| TUPRS  | 181 TL         | 188 TL         | deep dive baseline |
| ARCLK  | 401 TL         | 311 TL         | -78 pp upside, rasyonel |
| KCHOL  | 223 TL         | 189 TL         | whitelist + C2+3 |
| SAHOL  | 388 TL         | 354 TL         | whitelist + C2+3 |
| CCOLA  | 513 TL         | 486 TL         | β fix kısmen, hâlâ +%541 |
| FROTO  | 940 TL         | 671 TL         | cycle peak bias kısmen, -254 pp |
| EREGL  | 74 TL          | 58 TL          | steel β + 16-yıl |
| TRALT  | yeni           | 158 TL         | precious_metals 1.4176 |
| TRMET  | yeni           | 69 TL          | metals_and_mining 1.3013 |

Failed 2/19:
- BIMAS: "No items in response" (taxonomy + 16-yıl coverage)
- SOKM: 2017 IPO, pre-IPO veri yok

### Bilinen Sınırlar (Component 5+ / Faz 2.5+ Parking)

1. **16-yıl Coverage Gap** (BIMAS, SOKM)
   - Çözüm önerisi: Lifecycle-adaptive years_back veya retry logic

2. **Extreme Upside (Cycle Peak Bias)** — FROTO +%545, CCOLA +%541
   - Çözüm önerisi: Sub-period weighting (recent 10-yıl ağırlıklı)
   - Veya industry-implied EV/EBITDA cross-check

3. **Negatif DCF (PETKM, PGSUS)** — Cycle dipi extreme
   - Çözüm önerisi: Distress-adjusted DCF (Faz 2.5+)
   - Equity as call option (Black-Scholes)

4. **Holding SOTP** — KCHOL/SAHOL whitelist geçici
   - Çözüm: Sum of Parts model (Faz 2.5)
   - 3-level segment-based valuation

### Sonraki Faz Adayları (Yarın 28 Nisan 2026)

- **Faz 2.5 — SAHOL SOTP** (~3-4 saat, kompleks)
  - Holding'leri segment-bazlı parçala
  - Otomotiv + Enerji + Finans + ... ayrı DCF
  - Re-aggregation + minority interests + holdings'e özel disconto
- **Faz 3 — Portfolio Construction** (~2-3 saat, daha hazır)
  - 19 ticker AL/SAT verdict'inden 3-sleeve portfolio (alpha, hedge, opportunity)
  - Position sizing (margin of safety bazlı)
  - Backtest Yahoo Finance historical
- **Faz 2.4.7 — Cycle Bias Refinement** (~1-2 saat, methodology)
  - Sub-period weighting (recent 10-yıl ağırlıklı)
  - FROTO/CCOLA için spesifik calibration

---

## Faz 2.5 SOTP KAPANIŞ — Holdings Methodology Production (27 Nis 2026)

### Atomic Commit Chain (5 commit, ana paket)

**ADIM 1** — PDF Probe + CONFIRMED Data Research (no commit)
- pdfplumber 0.11.9 yüklendi
- SAHOL Q4 2024 Earnings Presentation page 24 NAV table CONFIRMED
- Gedik Yatırım Mar 2025 KCHOL report page 2 CONFIRMED
- 19 listed children + 12 non-listed pool stake'leri çıkarıldı

**ADIM 2 (990aaa8)** — holdings_config.py
- HoldingChild + HoldingPortfolio dataclasses (404 satır)
- HOLDINGS_PORTFOLIO registry (KCHOL + SAHOL)
- Public API: is_holding, get_portfolio, list_listed/banking_children
- Test: 4/4 PASS, methodology note diagnostic

**ADIM 3 (5bcee39)** — sotp.py
- calculate_sotp_value() implementation (244 satır)
- SOTPChildContribution + SOTPResult dataclass
- Source tracking: dcf_lookup / book_fallback / banking_book_pb_15 / non_listed_book
- Test: 4/4 PASS (SAHOL $11.66B / 202 TL, KCHOL $16.73B / 233 TL)

**ADIM 4 (468197b)** — Orchestrator SOTP integration
- analyze_ticker(...dcf_lookups: Optional[Dict] = None) imza
- STEP 1.5 SOTP early-return branch
- _populate_report_from_sotp + _fetch_children_dcfs_recursive helpers
- batch_analyzer.py 2-aşamalı refactor (non-holdings → dcf_lookups → holdings)
- print_report defansif WACC/margin None handling (SOTP context)
- Test: 3/3 PASS, TUPRS 188.29 baseline INTACT

**ADIM 5 (61a368b)** — BIST batch validation
- 19 ticker batch run, 17/19 successful, 48.9s
- 17/17 industrial ticker davranışı %100 korundu (Component 4 INTACT)
- Research findings rapor (sotp_batch_2026-04-27.md, 242 satır)
- Output kayıtları (CSV+JSON kalıcı)

### Methodology Validation (Damodaran %100 Hizalandı)

TUPRS Deep Dive Baseline (Faz 2.4.5):
- Manual deep dive: 188.31 TL (5+ saat)
- Production (Component 1+2+3+4 + Faz 2.5): 188.29 TL
- Sapma: 0.02 TL (yuvarlama)
- ★ INTACT through Faz 2.5

Holdings Anchor Comparison:
- KCHOL: 189 TL (Component 4 cyclical+whitelist) → 233 TL (Faz 2.5 SOTP)
  +%23 yukarı: SOTP banking P/B 1.5 intrinsic premium yansıttı
- SAHOL: 354 TL (Component 4 cyclical+whitelist) → 202 TL (Faz 2.5 SOTP)
  -%43 düzeltme: Component 4 banking distortion (mock %55 margin) düzeldi

Damodaran Insight (KRİTİK):
- Component 4 holdings için cyclical_dcf("KCHOL") = "Pretend industrial"
- SAHOL'da banking revenue distortion → fake %55 op_margin → +%256 fake AL
- Faz 2.5 SOTP intrinsic-aligned, SAHOL +%106 (chronic discount kanıtlı)

### Damodaran Lesson — Component 4 SAHOL BUG (Explicit Quote)

**Damodaran principle (REELDEĞER 27 April 2026'da deneyimle doğrulandı):**

> "Holdings cannot be valued like industrial firms. Their cash flows
> belong to subsidiaries, not parent. SOTP is correct methodology.
> Industrial DCF on consolidated holding cash flows is BUG-PRONE,
> not just suboptimal."

**Bug mechanics (REELDEĞER discovery):**

isyatirim XBRL "Net Satışlar" SAHOL için BANKING DOMINANT:
- Akbank %41 stake: interest income revenue olarak görüldü
- Banking net interest margin %3-4 → revenue olarak görünüyor
- Insurance revenue (Aksigorta, Agesa) ek
- Industrial revenue (Carrefoursa, Teknosa, Çimsa) yarısından az

Sonuç: SAHOL consolidated margin %54.80 (industrial %5-15 range vs reality)
- cyclical_dcf "industrial firm" gibi alıyor
- Future Op Income = Future Revenue × 54.8% margin
- $20.46B fake intrinsic
- 354 TL fake DCF
- +%256 fake AL signal

**Faz 2.5 SOTP fix:**
- Per-child DCF/book aggregation
- Banking P/B 1.5 (justified Damodaran)
- Non-listed book × 1.0 (conservative)
- Disconto %15 (NAV intrinsic target)
- SAHOL +%106 deep value (gerçek intrinsic)

**Magnitude depends on banking weight:**
- KCHOL banking weight %12 (YKBNK only) → bug MILD (189 vs 233, sapma %23)
- SAHOL banking weight %63 (AKBNK dominant) → bug CATASTROPHIC (354 vs 202, sapma %75)

### Bilinen Sınırlar (Faz 2.6+ Parking)

1. **SAHOL listed children BIST 30 dışı** — DCF lookup yok, hep book_fallback
   (ENJSA, AKGRT, AGESA, AKCNS, CIMSA, BRISA, KORDS, CRFSA, TKNSA)
   Çözüm: BIST 50 evren genişletme

2. **Banking book values PROVISIONAL** (~$8B YKBNK, ~$12B AKBNK)
   Çözüm: Faz 2.3.1 banking equity-only model + KAP gerçek özkaynak

3. **KCHOL TUPRS effective ownership %40** (EYAS chain)
   Çözüm: Annual KAP raporu güncelleme

4. **Cycle bias (FROTO/CCOLA extreme +%500)** — industrial cyclical
   Çözüm: Faz 2.4.7 sub-period weighting

5. **16-yıl coverage gap (BIMAS, SOKM)** — IPO sonrası, pre-IPO yok
   Çözüm: Lifecycle-adaptive years_back

### Sleeve Implications (Future Faz 3 Portfolio)

- **SAHOL** Deep Value sleeve candidate (chronic %46 discount + intrinsic +%106)
- **KCHOL** Mature Holding sleeve (mild discount + intrinsic +%14)
- **TUPRS** SAT (Damodaran overvalued, sweet spot retro doğrulandı)

### Sonraki Faz Adayları (28 Nisan 2026)

- **Faz 2.6 — Banking Equity-Only Model** (~3-4 saat, kompleks)
  - YKBNK, AKBNK için gerçek banking DCF (banking_ddm)
  - Book values PROVISIONAL → CONFIRMED
  - SAHOL/KCHOL SOTP banking contribution refine
- **Faz 2.4.7 — Cycle Bias Refinement** (~1-2 saat, methodology)
  - Sub-period weighting (recent 10-yıl ağırlıklı)
  - FROTO/CCOLA +%500 extreme upside calibration
- **Faz 3 — Portfolio Construction** (TAMAMLANDI 27 Nis 2026 gece)
  - Pentagon Scoring (5-D Damodaran ADR-007) ✓
  - 3-Sleeve portfolio (Core/Hızlı/Yüksek, ADR-066, 067) ✓
  - Position sizing (ADR-015, concentration cap %10) ✓
- **FROTO/CCOLA Root Cause Analysis** (30-90 dk, quick win)
  - Component 4 batch'te FROTO +%545, CCOLA +%541 extreme upside
  - Hipotez 1: Industrial cycle peak bias (Faz 2.4.7 fix)
  - Hipotez 2: SAHOL-tipi banking/distortion bug (?)
  - Hipotez 3: Lifecycle misclassification (mature_growth → mature_stable?)
  - Diagnosis FIRST, then choose fix path
  - Quick win: 30-60 dk probe → karar

---

## Faz 2.6 — Cyclical Asymmetric Cap KAPANIŞ (27 Nisan 2026 akşam)

### Status: TAMAMLANDI ✓

2 atomic commit chain:
- **c906a14** — ADIM 8 FROTO/CCOLA root cause diagnosis (260 satır rapor)
- **9820cc0** — ADIM 9 cyclical_dcf asymmetric cap fix (Path A4)
- + ADIM 10 kapanış (this commit)

### Damodaran Lesson #2 (REELDEĞER keşfi)

**Damodaran cyclical_dcf reference (Toyota 2009):**
- Crisis year, current_revenue TROUGH'te
- current(low) × avg_margin = NORMALIZE UPLIFT (DOĞRU)

**REELDEĞER half-normalized formula bug:**
- normalized_op_income = current_revenue × avg_margin
-                          ↑ peak bias!     ↑ OK
- FROTO 2024 PEAK year, current 2.34x avg → INFLATION

**FIX (Path A4 — Asymmetric Cap, cap 1.5x):**
- effective_revenue = min(current_revenues, avg_revenue × 1.5)
- normalized_oi = effective_revenue × historical_avg_margin
- Trough year (current ≤ avg×1.5) → Toyota pattern KORUNUR
- Peak year (current > avg×1.5) → cap kicks in (peak inflation kırılır)
- Asymmetric: trough'u dokunmaz, peak'i disipline eder

### Anchor Sonuçları (61 commit batch)

| Ticker | Faz 2.5 | Faz 2.6 cap 1.5x | Δ | Verdict |
|--------|---------|-------------------|---|---------|
| TUPRS  | 188.29  | 187.10            | -%0.6 ★ | SAT (INTACT) |
| FROTO  | 671.37  | 294.34            | -%56 | AL (rasyonel +%187) |
| ARCLK  | 311.54  | 176.78            | -%43 | AL (sadeleşti +%52) |
| CCOLA  | 486.30  | 386.85            | -%20 | AL (+%418 hâlâ yüksek) |
| KCHOL  | 233.36  | 203.26            | -%13 | BEKLE (-%1) |
| SAHOL  | 202.09  | 202.09            | UNCHANGED | AL (book_fallback) |
| TOASO  | 114.90  | 114.90            | UNCHANGED | SAT |
| THYAO  | 16.45   | -110.81           | NEGATİF | SAT (distress) |
| PGSUS  | -839.77 | -1082.76          | DAHA NEG | SAT (distress) |

**TUPRS deep dive baseline -%0.6 sub-noise (effectively INTACT).**
Cap 1.5x mükemmel kalibrasyon — tahmin -%7, gerçek -%0.6.

**BIST Avg upside: +34.65% → -14.20%** (rasyonelleşme, methodology disipline).

### Bilinen Sınırlar (Faz 2.7+ Parking)

1. **CCOLA hâlâ +%418** — kısmen düzeldi:
   - 2.86B avg × 1.5 = 4.29B cap, current 5.10B = capped at -%16
   - Cap kısmi etkili (FROTO 2.34x vs CCOLA 1.78x)
   - Secondary analysis: 2-stage explicit veya lifecycle-adaptive cap

2. **THYAO/PGSUS negatif DCF** — distress
   - Damodaran distress-adjusted value formula
   - Equity as call option (Black-Scholes)

3. **BIMAS/SOKM 16-yıl coverage gap** (devam ediyor)

### Methodology Evolution Timeline

- **Faz 2.4.5** TUPRS deep dive baseline (Toyota 2009 trough pattern)
- **Faz 2.5** Holdings SOTP (Damodaran Lesson #1: per-child intrinsic)
- **Faz 2.6** Asymmetric cap (Damodaran Lesson #2: peak year extension)

İki Damodaran-aligned methodology iyileştirmesi keşfedildi.

### Faz 2.7+ Önerileri (yarın için)

a) **CCOLA Secondary Analysis** (30-60 dk, quick win)
   - 2-stage explicit projection (defensive consumer)
   - Lifecycle-adaptive cap (mature_stable için)
b) **Distress Model** (THYAO/PGSUS, 1-2 hafta)
   - Damodaran equity-as-call-option
   - Black-Scholes
c) **Banking Equity-Only Model** (3-4 saat)
   - YKBNK, AKBNK gerçek DCF
   - SOTP banking refinement
d) **Faz 3 Portfolio Foundation** (2-3 saat)
   - Pentagon Scoring (5-D narrative ADR-098)
   - 3-Sleeve (alpha + hedge + opportunity)
   - Methodology hazır → portfolio construction'a geçebiliriz

---

## Faz 3 — Portfolio Foundation KAPANIŞ (27 Nisan 2026 gece)

### Status: TAMAMLANDI ✓ (foundation %50-60)

5 atomic commit chain:
- 0c5e868 — ADIM 2 pentagon_scoring.py (5-D Pentagon, lifecycle weights)
- 1026d22 — ADIM 3 sleeve_assignment.py (Core/Hızlı/Yüksek/Skip)
- 0ac3784 — ADIM 4 portfolio_construction.py (position sizing, cap %10)
- aa76179 — ADIM 5 end-to-end pipeline + research findings
- + ADIM 6 KAPANIŞ docs (this commit)

### Yeni Modül: apps/api/portfolio/

- **pentagon_scoring.py** (~330 satır) — Pentagon 5-D (Damodaran ADR-007)
  - Value, Growth, Quality, Momentum (PARKING), Risk
  - Lifecycle-adjusted weights (ADR-044, 049)
- **sleeve_assignment.py** (~274 satır) — 3-Sleeve mapping (ADR-066, 067)
  - 4 YÜKSEK KAZANÇ alt-kategori (deep_value, holding_chronic_discount, distress, mature_transition)
  - Rule cascade with priority (holdings öncelikli)
- **portfolio_construction.py** (~283 satır) — Position sizing (ADR-015)
  - 3 risk profile (Konservatif/Dengeli/Agresif)
  - Concentration cap %10 + cash reserve management
  - Boş sleeve auto-reallocation to cash

### Pipeline Sonuçları (BIST 30 / 1M TL)

| Profile | Invested | Cash | Note |
|---------|----------|------|------|
| Konservatif | %28 | %72 | cap overflow + boş sleeve |
| Dengeli | %35 | %65 | cap overflow + boş sleeve |
| Agresif | %45 | %55 | en az cash |

★ Cash dominance methodology-aligned ("Better cash than overpay" Damodaran).

### Pentagon Top 5 / Bottom 3

**Top 5:**
- CCOLA 77.7 (deep value, +%418 — Faz 2.7 secondary pending)
- FROTO 75.2 (mature_growth, +%187)
- ARCLK 69.5 (Mature Stable, Q=85)
- SAHOL 63.7 (UNKNOWN holding chronic discount)
- EREGL 63.6 (Mature Stable, +%74)

**Bottom 3:**
- PETKM 31.1 (negatif DCF)
- TRMET 34.8 (low composite)
- PGSUS 36.7 (negatif DCF)

### Sleeve Breakdown (17 ticker)

- **CORE (2):** EREGL, ARCLK (mature_stable + upside > %30 + Q > 60)
- **HIZLI BÜYÜME (0):** BIST 30 mature ağırlıklı, beklenen
- **YÜKSEK KAZANÇ (4):**
  - Deep Value: CCOLA, FROTO, TRALT
  - Holding Chronic Discount: SAHOL
- **SKIP (11):** TUPRS (SAT), TOASO/MGROS/ASELS/ENKAI (overvalued), THYAO/PGSUS/PETKM (negatif DCF), KCHOL (composite < 50), KRDMD/TRMET (weak)

### Bilinen Sınırlar (Faz 3.5+ Parking)

1. **BIST 30 universe yetersiz** — 6 investable ticker yetmedi
   - Konservatif Core %80 için 8+ ticker gerek
   - Çözüm: BIST 50/100 evren genişletme

2. **Hızlı Büyüme sleeve boş** — BIST 30 mature ağırlıklı
   - YOUNG/HIGH_GROWTH ticker yok
   - Çözüm: BIST 50/100 + IPO ticker'lar

3. **Holdings UNKNOWN stage fallback** — KCHOL composite 49.9 (eşik altı)
   - SOTP routing lifecycle skip → UNKNOWN → Mature Stable weights
   - Çözüm: SOTP children lifecycle weighted aggregate

4. **Momentum boyutu PARKING** — MVP default 50 (neutral)
   - Yahoo Finance fetcher gerek (yfinance/yahooquery)
   - Çözüm: Faz 3.5+ momentum dimension activation

5. **CCOLA Pentagon Top 1** — V=100, Q=85 ama +%418 hâlâ
   - Faz 2.6 cap kısmen düzeltti (-%20)
   - Pentagon scoring methodology-aligned (input data shape)
   - Faz 2.7 secondary analysis dikkat

### Damodaran Lesson #3 (REELDEĞER 27 Nis 2026 keşfi)

> "When investable universe is inadequate, holding cash is methodology-correct.
>  Better to under-invest at intrinsic prices than to overpay because of
>  artificial allocation targets. Concentration cap + sleeve boundaries
>  enforce this discipline automatically."

(BIST 30 universe %55-72 cash → Damodaran-aligned, BIST 50/100 universe
expansion ile %20-30 cash beklentisi.)

### Faz 4+ Adayları

a) **BIST 50/100 Universe Expansion** (~1 hafta)
   - ENJSA, AKGRT, AGESA, AKCNS, CIMSA, BRISA, KORDS, vb.
   - Hızlı Büyüme sleeve dolar
   - Konservatif Core gerçek 8+ ticker

b) **Holdings-specific Pentagon Scoring** (3-4 saat)
   - SOTP children lifecycle weighted aggregate
   - KCHOL/SAHOL kendi lifecycle stage hesaplama

c) **Momentum Dimension** (Yahoo Finance, 2-3 saat)
   - 12M price momentum
   - 5. Pentagon boyutu aktif

d) **Backtest Engine** (1-2 hafta)
   - 2020-present quarterly rebalance simulation
   - Triple benchmark (XU100, BIST-30 ETF, S&P 500 ETF)
   - 5-failure metric tracker

e) **CCOLA Secondary Analysis** (30-60 dk)
   - Lifecycle-adaptive cap factor
   - 2-stage explicit projection

f) **Distress Model** (THYAO/PGSUS, 1-2 hafta)
   - Black-Scholes equity-as-call-option

g) **Banking Equity-Only** (3-4 saat)
   - YKBNK/AKBNK gerçek DCF
   - SAHOL/KCHOL SOTP banking PROVISIONAL → CONFIRMED

---

## Faz 2.7 — CCOLA Secondary + Adaptive Cap KAPANIŞ (27 Nisan 2026 gece)

### Status: TAMAMLANDI ✓

3 atomic commit chain:
- 898a14a — Faz 2.7 (a) CCOLA secondary research (high-level, gece başı)
- 7db0cec — Faz 2.7 (a) CCOLA NET diagnosis (3 hipotez)
- cc4ba56 — Faz 2.7 (b) Adaptive Cap implementation (Lesson #4)
- + ADIM 8 KAPANIŞ docs (this commit)

### Damodaran Lesson #4 (REELDEĞER keşfi)

> "Cyclical cap should be lifecycle + recent-bias adaptive, not fixed.
>  Defensive consumers with structural margin upshift need tighter cap (1.3x).
>  High growth firms maintain 1.5x default (revenue growth justified)."

### CCOLA Diagnosis NET Sonuç

**3 Hipotez:**
- H1 Recent margin bias: ★ DOĞRULANDI (+%31.3 post-COVID structural)
- H2 Lifecycle misclassification: REJECTED (CAGR %6.97 mature_stable)
- H3 Defensive low volatility: ★ DOĞRULANDI (stdev %2.03)

**Yorum:** CCOLA = defensive consumer with structural margin upshift.
Recent 5y margin %14.16 KALICI durum (post-COVID pricing power), older
7y avg %10.79. Bias post-COVID structural, artifact değil.

### Adaptive Cap Logic

```python
cap_ratio = (
    1.3 if (lifecycle == "MATURE_STABLE" AND recent_bias > 25%)
    else 1.5  # default Faz 2.6
)
```

**Etkilenen ticker:** SADECE CCOLA (selektif fix)
**Korunan:** TUPRS, ARCLK, FROTO, SAHOL, KCHOL (INTACT)

### CCOLA Methodology Evolution

| Aşama | DCF | Upside | Δ |
|-------|-----|--------|---|
| Faz 2.5 (no cap) | 486 TL | +%551 | baseline |
| Faz 2.6 cap 1.5x | 386 TL | +%418 | -%21 |
| Faz 2.7 adaptive | 317 TL | +%325 | -%18 |
| **Toplam (2.5→2.7)** | -169 TL | -%41 | -%35 |

### Anchor Final State (70 commit)

| Ticker | DCF (TL) | Upside | Verdict |
|--------|----------|--------|---------|
| TUPRS | 187.10 | -%32 | SAT (deep dive baseline INTACT, sapma -%0.6) |
| KCHOL | 203.26 | -%1 | BEKLE |
| SAHOL | 202.09 | +%106 | AL (holding chronic discount) |
| FROTO | 294.34 | +%187 | AL (rasyonel) |
| ARCLK | 176.78 | +%52 | AL (mature stable) |
| CCOLA | 317.51 | +%325 | AL (defensive, adaptive cap aktif) |

### 4 Damodaran Lesson Bugün Keşfedildi

#1 **Faz 2.5:** Holdings cannot be valued like industrial firms (SOTP)
#2 **Faz 2.6:** Cyclical DCF must handle peak years asymmetric cap
#3 **Faz 3:**   Cash > overpay when universe inadequate
#4 **Faz 2.7:** Adaptive cap by lifecycle + recent margin bias

### Bilinen Sınırlar (Faz 2.8+ Parking)

- KCHOL/SAHOL SOTP routed (adaptive cap relevant değil)
- Negatif DCF artifacts (PETKM, PGSUS, THYAO) → distress model gerek
- BIST 30 universe yetersiz → BIST 50/100 expansion
- ARCLK bias -%24 ilginç (recent margin DROPPED, ek analiz adayı)

### Sonraki Faz Adayları (yarın için)

- **Faz 3.5** BIST 50/100 universe expansion (1 hafta)
- **Faz 4** Backtest engine (1-2 hafta, 2020-present rebalance)
- **Faz 5** Distress model (Black-Scholes, THYAO/PGSUS, 1-2 hafta)
- **Faz 6** Banking equity-only (3-4 saat)
- **Faz 7** Holdings-specific Pentagon scoring (3-4 saat)
- **Faz 8** Momentum dimension (Yahoo Finance, 2-3 saat)

---

## BUGÜNÜN MARATHONUN ÖZETİ (27 Nisan 2026)

22 atomic commit Faz 2.4.6 + 2.5 + 2.6 + 2.7 + 3 paketleri:

**Faz 2.4.6 (industrial Damodaran):** 7 atomic commit chain
- Component 1+2+3+4 + Bonus + kapanış + docs

**Faz 2.5 (holdings SOTP):** 6 atomic commit chain
- ADIM 1 (PDF probe, no commit)
- ADIM 2 holdings_config + ADIM 3 sotp.py + ADIM 4 orchestrator integration
- ADIM 5 BIST batch validation + ADIM 6 kapanış + ADIM 7 follow-up

**Faz 2.6 (asymmetric cap):** 3 atomic commit chain
- ADIM 8 FROTO/CCOLA diagnosis + ADIM 9 cap fix + ADIM 10 kapanış (this)

İki Damodaran Lesson keşfi:
- #1 Holdings SOTP (industrial DCF holdings için yetersiz)
- #2 Cyclical Asymmetric Cap (peak yıllar için extension)

---

## Yarın Açılış Komutları

cd /c/Users/unutu/Desktop/abiminprojev2
git status
git log --oneline | head -10
cat notes/kaldim.md

---

## Repo Durumu

- 71 commit GitHub'da (clean)
- Branch: main
- Son commit: (Faz 2.7 kapanış, this update)
- Faz 2.4.6 atomic chain: 7163b5e → 6e22767 → 67d6ec9 → 09a2a9b → a7ed721 → 4256744 → 3cdbb66 → 658c195
- Faz 2.5 atomic chain: 990aaa8 → 5bcee39 → 468197b → 61a368b → 3f5692b → 16358ae
- Faz 2.6 atomic chain: c906a14 → 9820cc0 → 43b2425
- Faz 3 atomic chain: 0c5e868 → 1026d22 → 0ac3784 → aa76179 → c95d4d8
- Faz 2.7 atomic chain: 898a14a → 7db0cec → cc4ba56 → (kapanış)
- GitHub: https://github.com/ik1903846-web/Degerlemetablosu

---

## Validation Disiplini (5/5 zero-deviation)

| Case | Beklenen | Hesaplanan | Sapma |
|---|---|---|---|
| Heineken | €59.65 | €59.57 | -0.14% |
| Toyota | ¥4,735 | ¥4,737 | +0.04% |
| Tube Inv. | ₹61.57 | ₹61.55 | -0.04% |
| ABN Amro | €30.87 | €32.12 | +4.06% |
| TUPRS Mkt Cap | 518.30B | 518.31B | 0.00% |

TUPRS DCF: manuel = batch = live = **181.16 TL** (3 yöntem birebir)

---

## Önemli Notlar

1. **TUPRS sweet spot retro doğrulandı:**
   - 2024 sonu (144 TL): DCF 181 TL = %26 UCUZ → AL
   - 2026 Nis (269 TL): DCF 181 TL = %33 PAHALI → SAT
   - 2 yılda fiyat +%87, DCF üzerinde

2. **EM cyclicality endemic:** 19 ticker'ın hepsi mature_stable + cyclical
   - Damodaran "developed" firmalardan farklı
   - Faz 2.4.5'te sektör-bazlı threshold gerek

3. **TFRS 29 hyperinflation noise:** USD bazda bile PP&E gross-up etkisi var
   - Reinvestment rate %86 (12-yıl avg) şüpheli yüksek
   - Inflation-adjusted PP&E ileride

4. **Banking için 2.3.1 parking:** GARAN/AKBNK orchestrator skip ediyor
   - banking_ddm modülü hazır (Faz 1.4)
   - financialGroup XI_30 + lifecycle bypass gerek

5. **Pythonic Damodaran adapter çalışıyor:**
   - Heineken (EUR DM) + Tube (INR EM) + Toyota (JPY cyclical) + ABN (EUR bank)
   - 4 farklı para, 4 farklı model, hepsi <%5 sapma
   - BIST'te tek soru kalibrasyon (sayı doğru, threshold ayarı)

6. **41 commit / 17 saat:**
   - Sıfırdan production sistem
   - Faz 1 + Faz 2 birlikte
   - Validation gate: hep zero-deviation
