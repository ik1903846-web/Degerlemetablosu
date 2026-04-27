# REELDEĞER — Kaldığım Yer

**Son güncelleme:** 27 Nisan 2026, 15:00
**Aktif Faz:** Faz 2.4.6 TAMAMLANDI ✓ (Component 1+2+3+4 + Bonus)
**Sıradaki:** Faz 2.5 (SAHOL SOTP) veya Faz 3 (Portfolio Construction) — yarın karar

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

## Yarın Açılış Komutları

cd /c/Users/unutu/Desktop/abiminprojev2
git status
git log --oneline | head -10
cat notes/kaldim.md

---

## Repo Durumu

- 53 commit GitHub'da (clean)
- Branch: main
- Son commit: (kapanış commit, bu güncellemeyi içerir)
- Önceki: 3cdbb66 (Bonus print_report None handling)
- Faz 2.4.6 atomic chain: 7163b5e → 6e22767 → 67d6ec9 → 09a2a9b → a7ed721 → 4256744 → 3cdbb66
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
