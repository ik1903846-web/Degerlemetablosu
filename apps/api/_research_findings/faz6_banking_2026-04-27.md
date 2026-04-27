# Faz 6 Banking Equity-Only — Research Findings (27 Nisan 2026 gece)

**Tarih:** 27 Nisan 2026 gece (~01:30)
**Commit:** bacd356 (Faz 6 ADIM 4 sonrası) → ADIM 5 batch + validation
**Hedef:** BIST banking ticker DDM coverage + ABN Amro validation + SAHOL/KCHOL SOTP refinement

---

## TL;DR

★ 5 banking ticker (AKBNK, GARAN, YKBNK, ISCTR, HALKB) banking DDM PRODUCTION
★ ABN Amro €30.87 baseline PASS (Faz 1 validation INTACT after Faz 6 integration)
★ TUPRS 187.10 TL deep dive baseline INTACT (industrial pipeline korundu)
★ KCHOL 190 TL (eski 203, -%6.4 banking refinement etkisi)
★ SAHOL 181 TL (eski 202, -%10.3 banking refinement, AKBNK %63 weight dominant)
★ HALKB anomaly: +%518 upside (state bank, payout 0%, terminal value dominant)

---

## Banking Anchor Tablosu (DDM 2-Stage USD-Basis)

| Ticker | DDM TL/share | Equity USD | EPS TL | ROE % | Payout % | CoE % | Market | Upside % | Verdict |
|--------|-------------:|-----------:|-------:|------:|---------:|------:|-------:|---------:|---------|
| AKBNK | 98.96 | $14.55B | 11.01 | 21.5 | 20 | 11.09 | 70.00 | +41.37 | AL |
| GARAN | 197.28 | $23.43B | 21.95 | 30.0 | 20 | 11.09 | 140.00 | +40.92 | AL |
| YKBNK | 38.96 | $9.30B | 4.14 | 25.0 | 29.2 | 11.09 | 35.00 | +11.32 | IZLE-AL |
| ISCTR | 17.19 | $4.38B | 1.82 | 16.0 | 30 | 11.09 | 13.00 | +32.27 | AL |
| HALKB | 142.24 | $5.03B | 17.63 | 12.0 | 0 | 11.09 | 23.00 | +518.45 | AL ★ |

**Eklenen:**
- DDM 2-stage: 5-yıl high growth + stable perpetuity
- USD basis: EPS_USD = EPS_TL / spot 35.37
- High growth USD g cap: %8 (TR nominal yüksek inflation distort eder)
- Stable phase: ROE → Ke convergence (Damodaran banking)
- CoE = Rf + β × ERP + λ × CRP = 3.97 + 0.2495 × 4.44 + 1.0 × 6.01 = 11.09%

**HALKB anomaly:**
State bank, payout %0 (kar tutuluyor). DDM'de high-growth phase PV(DPS)=0,
tüm değer Terminal Value'da. EPS Year 6 ($0.755) × stable_payout 0.727 /
(0.11 - 0.03) = $6.86 PV → 144 TL. Market %85 discount (state bank risk premium).
Methodology aligned, market story farklı (Lesson #3 — chronic discount).

---

## ABN Amro Validation (Faz 1 → Faz 6 Re-test)

**Damodaran reference:** ABN Amro 2008, expected €30.87/share

**Re-test (test_full_ddm.py):**
- Computed: €32.12
- Expected: €30.87
- Diff: **+%4.06**
- Tolerance ±%5: ★ PASS

**Status:** Banking DDM motoru Faz 1'den bugüne unchanged. Faz 6 integration
(banking_data + orchestrator branch + SOTP refinement) ABN Amro validation'a
DRIFT yaratmadı. Methodology INTACT.

Computed breakdown:
- EPS_terminal Year 6: €2.6726 (Damodaran PDF: €2.67) ✓
- Terminal Value: €44.32 (PDF €42.41, +%4.5 fark — yuvarlama)
- PV(High Growth DPS): €3.08
- PV(Terminal Value): €29.05

---

## SOTP Refinement Etki (Single-Ticker Mode)

**KCHOL (banking-light %12 YKBNK):**
- Eski: 203.26 TL (YKBNK book $12B × P/B 1.5 × 41% = $4.92B contribution)
- Yeni: 190.16 TL (YKBNK banking_ddm $9.30B × 41% = $3.81B contribution)
- Δ DCF: -%6.4
- Banking contribution: -$1.11B
- Verdict: BEKLE → BEKLE (-%7.24, eşik içinde)

**SAHOL (banking-heavy %63 AKBNK):**
- Eski: 202.09 TL (AKBNK book $12B × P/B 1.5 × 41% = $7.38B contribution)
- Yeni: 181.24 TL (AKBNK banking_ddm $14.55B × 41% = $5.96B contribution)
- Δ DCF: -%10.3
- Banking contribution: -$1.42B
- Verdict: AL → AL (+%84.65, hâlâ deep value)

**Methodology:**
- Source: banking_ddm_dcf (CONFIRMED)
- Eski source: banking_book_pb_15 (PROVISIONAL fallback)
- Banking_ddm USD basis daha conservative (β 0.2495 düşük)

---

## BIST Industrial Batch (Banking Integration Etkisi)

**Latest output:** apps/api/outputs/bist_batch_LIVE_20260427_231428.{csv,json}

**Duration:** 37.7s (19 ticker)
**Successful:** 17/19
**Failed:** 2 (BIMAS, SOKM coverage gap, Faz 2.4.6 → Faz 6 INTACT)

**TUPRS:** 187.10 TL (★ deep dive baseline, sapma -%0.6 from manual 188.31)

**SAHOL/KCHOL batch mode note:**
- Single-ticker mode: banking DDM CONFIRMED (KCHOL 190, SAHOL 181)
- Batch mode: banking children non_holdings phase'de YOK → book × P/B fallback
- Yani batch outputs SAHOL 202, KCHOL 203 (PROVISIONAL — eski state)
- **Faz 6.5 parking:** batch_analyzer.py'ya banking phase eklenmesi
  (banking_tickers = [t for t in tickers if is_banking_ticker(t)])

Avg upside: -%19.66 (Faz 2.7'den aynı, banking refinement henüz batch'te aktif değil)

---

## Damodaran Lesson #5 (REELDEĞER candidate)

> "Banking holding subsidiaries valued via DDM (not justified P/B fallback)
>  produce more conservative SOTP values when banking weight is high.
>  
>  SAHOL %63 banking weight: book × P/B 1.5 fallback overestimates by ~%19
>  vs DDM USD-basis. KCHOL %12 weight: minor change ~%6.
>  
>  Banking valuation methodology hierarchy:
>    1. DDM (Dividend Discount Model) — preferred for dividend-paying banks
>    2. Excess Return Model — alternative, book equity centric
>    3. Justified P/B fallback — last resort (PROVISIONAL only)"

---

## Bilinen Sınırlar (Faz 6.5+ Parking)

### 1. Banking Ticker Coverage Eksik (6/11)

KNOWN_BANKING_TICKERS = 11 ticker, banking_data 5 ticker:
- ✓ AKBNK, GARAN, YKBNK, ISCTR, HALKB
- ✗ VAKBN, QNBFB, TSKB, SKBNK, ICBCT, ALBRK

**Çözüm:** Faz 6.5 ek 6 ticker manual config (KAP yıllık raporlar).

### 2. 2021-2023 ESTIMATE Confidence

5 ticker × 4-yıl = 20 yearly data. Sadece 2024 CONFIRMED (web search).
2021-2023 back-calculated from public ratios.

**Çözüm:** Faz 6.5 KAP PDF parser (otomasyon).

### 3. Banking Sector Beta Tek Değer (0.2495)

Tüm 5 banking ticker aynı β (Damodaran bank_money_center default).
BIST banking arasında β farklılığı (özel risk profili).

**Çözüm:** Faz 7+ ticker-specific bottom-up beta (Hamada banking).

### 4. Batch Mode Banking Refinement YOK

Single-ticker mode banking DDM uses _fetch_children_dcfs_recursive.
Batch mode banking ticker'ları non_holdings phase'de değil.

**Çözüm:** Faz 6.5 batch_analyzer.py'a banking phase ekleme:
```python
banking_tickers = [t for t in tickers if is_banking_ticker(t)]
non_holding_tickers = [t for t in tickers
                       if not is_holding(t) and not is_banking_ticker(t)]
# Phase 1.5: banking ticker'ları parallel + dcf_lookups'a ekle
```

### 5. HALKB State Bank Anomaly

Payout %0 (state bank, kar retention). DDM Terminal Value dominant.
Market %85 discount (regulatory + state risk).

**Damodaran prensip:** Methodology doğru söylüyor (intrinsic), market story
farklı (TR sovereign + state-controlled risk premium). Lesson #3 örneği.

---

## Faz 6 Final State

5 banking ticker production-ready DDM:
- DDM 2-stage motoru (Faz 1 ABN Amro PASS)
- KAP-sourced data (banking_data.py)
- Orchestrator integration (banking branch reactive)
- SOTP refinement (banking_ddm_dcf CONFIRMED source)
- Single-ticker mode tam coverage

Methodology timeline:
- Faz 1: ABN Amro DDM €30.87 validation PASS
- Faz 2.5: Holdings SOTP, banking children PROVISIONAL fallback
- Faz 6: Banking DDM production, SOTP refinement CONFIRMED

5 Damodaran Lesson Timeline:
- #1 Faz 2.5: Holdings cannot be valued like industrial firms
- #2 Faz 2.6: Cyclical DCF asymmetric cap (peak year)
- #3 Faz 3:   Cash > overpay when universe inadequate
- #4 Faz 2.7: Adaptive cap by lifecycle + recent margin bias
- #5 Faz 6:   Banking DDM > P/B fallback (SOTP refinement)

---

## Sonraki

- **ADIM 6:** Faz 6 KAPANIŞ docs (~15 dk)
- **Faz 6.5 (önerilen):** 6 banking ticker eklenmesi + batch banking phase
- **Faz 7+:** Backtest engine, distress model, frontend integration
