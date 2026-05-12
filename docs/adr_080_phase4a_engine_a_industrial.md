# ADR-080 — Phase 4a: Engine A Industrial Entegrasyon

**Status:** PROPOSED → SEALED (Phase 4a implement sonrasi)
**Date:** 2026-05-12
**Decision Maker:** REELDEĞER project
**Related:** ADR-078 (cross-holdings), ADR-079 (Phase 3 sub valuation)

---

## Section 1 — Baglam: Engine A vs Engine B Asymmetry

**Bulgu (commits 73-74, 2026-05-12):**
- Engine A (dcf_engine/industrial_fcff.py): 10-year explicit + transition,
  Damodaran-sadik (Heineken -0.14% PASS)
- Engine B (dcf_engine_v4/fcff_engine.py): 5-year fixed lifecycle,
  Damodaran'dan +%100-220 sapma (3/3 multi-case test)

**Kanit:**
- Heineken: A -0.14%, B +%221
- Tube: A -0.04%, B +%132
- Toyota: A +0.04%, B +%130

Production'da 145 industrial + 10 holding SOTP Engine B kullaniyor.
TUPRS 211.95 anchor Engine B output — Damodaran reference YOK.

## Section 2 — Phase 4a Kapsam

**In-scope:**
- Engine A → orchestrator_v4 industrial branch entegrasyon
- 145 industrial ticker Damodaran-sadik intrinsic
- 10 holding SOTP Engine A adapter (Phase 3b ile uyum)
- TUPRS, KCHOL, SAHOL gibi tum industrial path revize

**Out-of-scope (Phase 4b+):**
- Banking DDM aktivasyon (Tier 1 5 banka)
- Multi-multiple consensus (PE + PBV)
- young_firm_dcf (Amazon path)
- Sector regression Level 2 SOTP

## Section 3 — 8 Adim Detay + Dependency

**Adim 1: KAP +1 field (total_assets)** — 0.5 gun
- Hedef: sales_to_capital = revenue / (total_assets - excess_cash)
- Implementation: kap_excel_parser.py extend
- Output: TickerDataV4.total_assets field
- Test: 5 KAP excel manuel parse + value compare

**Adim 2: KAP 5y revenue CAGR helper** — 0.5 gun
- Hedef: explicit_growth_rate (Engine A input)
- Implementation: history_rows'tan CAGR (5y geometric mean)
- Fallback: <5y data → 3y veya median 1y
- Sanity: cap %50 max (boom outlier protection)

**Adim 3: Damodaran sector op_margin fetcher** — 1 gun
- Hedef: terminal_ebit_margin (Engine A input)
- Implementation: damodaran_sector_fetcher.py extend (margin.xls)
- Pattern: Phase 3c'deki sector_multiple_fetcher.py reuse
- Sector map: 44 BIST → Damodaran (mevcut config)
- Source: pages.stern.nyu.edu/~adamodar/pc/datasets/margin.xls

**Adim 4: Lifecycle → taper config map** — 0.5 gun
- Hedef: margin_taper_start/end_year, explicit_period_years
- Implementation: lifecycle_classifier.py'a DEFAULT_TAPER_CONFIG dict
- Default convention:
    mature_stable: explicit=5y, transition=5y, margin_taper=2-10
    mature_growth: explicit=10y, transition=5y, margin_taper=3-10
    high_growth: explicit=10y, transition=10y, margin_taper=5-15
- Damodaran "Act Your Age" framework alignment

**Adim 5: KAP +2 field (minority + non_op_assets)** — 1 gun
- Hedef: equity bridge formal Damodaran SOTP
- Implementation: kap_excel_parser.py extend (Phase 3a benzeri)
- Fields: minority_interests, non_operating_assets
- Equity bridge yenilemesi:
    equity = ops_value - debt - minority + cash + non_op + cross_holdings

**Adim 6: orchestrator_v4 Engine A adapter** — 2 gun (EN ZOR)
- Hedef: industrial dialect Engine A'ya route
- Implementation:
    a) DCFInputsBuilder class (TickerDataV4 → ProjectionInputs)
    b) industrial branch yeniden yaz:
       OLD: from dcf_engine_v4 import calculate_fcff_dcf
       NEW: from dcf_engine.industrial_fcff import project_multi_year + dcf_valuation
    c) Engine B legacy (Phase 6+ archive flag, kod kalir)
- Test: 5 ticker (TUPRS, EREGL, ARCLK, BIM, ASELS) manuel run + sanity

**Adim 7: Batch regen + 6 sanity gate** — 0.5 gun
- Hedef: 615 ticker yeniden intrinsic
- 6 sanity gate (Phase 3 pattern):
    g1: universe count band (155-186 range)
    g2: industrial intrinsic median (~50-150 TL)
    g3: TUPRS new band (90-130 TL)
    g4: KCHOL hala 130-170 (Phase 3b intact)
    g5: SAHOL bug zaten Phase 1+2 data quality (intact)
    g6: AHGAZ ~25-30 TL (Phase 3b intact)

**Adim 8: UI sync + audit chain** — 1 gun
- Hedef: Streamlit Tarayici, KPI, audit chain
- universe_stats_v4 regenerate
- Faz B2 Phase 4a master/progress/resolution doc
- Anchor tag: v4.5-phase4a-engine-a-industrial-sealed

**Dependency graph:**
  Adim 1, 2, 3, 4 → paralel (1-2 gun)
  Adim 5 → paralel (1 gun)
  Adim 6 → SEQUENTIAL after 1-5 (2 gun)
  Adim 7 → SEQUENTIAL after 6 (0.5 gun)
  Adim 8 → SEQUENTIAL after 7 (1 gun)

  Min realistic: 4-5 gun

## Section 4 — Anchor Doktrin

**Mevcut anchor (v4.4-phase3-sealed):**
- TUPRS 211.95412760984857 INTACT 10 noktasi (Engine B output)
- Bu reference Damodaran-sadik DEGIL

**Phase 4a transition:**
- v4.4-phase3-sealed → v4.5-phase4a-engine-a-industrial-sealed
- TUPRS yeni band: ~90-130 TL (Engine A Damodaran-rule)
- Shadow 216.33 anchor.json'da yedek (Engine B legacy)
- Memory project_reeldeger.md update: 'TUPRS 211.95 INTACT' iddiasi DEGISIR

**Backward compat:**
- v4.4 tag intact (geriye donus mumkun)
- Engine B code intact (Phase 6+ archive)
- Streamlit Tarayici 1-2 gun feedback period

## Section 5 — Damodaran Sadakat Doktrini

**Success metric:**
- Damodaran sadakat skoru: 78/100 → 92/100 hedef
- 4 validation case Engine A path PASS (Heineken/ABN/Tube/Toyota)
- BIST 145 industrial ticker Engine A intrinsic generated
- Cross-validation: 5 ticker manuel Damodaran-rule sanity (TUPRS, EREGL, ARCLK, BIM, ASELS)
- 6 sanity gate Phase 3 pattern

**Damodaran rule alignment:**
- Currency: USD bazli (ADR-002)
- Beta: bottom-up + sektor levered (Phase 4 enhancement scope disi)
- Terminal value sanity: ImpliedROCROE Phase 4 yan modul scope disi (Phase 5)
- Equity bridge: formal Damodaran SOTP (Adim 5 ile)

## Section 6 — Risk + Mitigation

**Risk 1: TUPRS anchor degisimi**
- Memory '211.95 INTACT 10 noktasi' iddiasi DEGISIR
- Mitigation: ADR-080'de explicit doctrine + memory revize commit
- Shadow 216.33 yedek (anchor.json zaten kayitli)

**Risk 2: Universe count dusmesi (186 → ~155)**
- Engine A daha titiz (KAP eksik ticker'lar book value'a kayar)
- Mitigation: 6 sanity gate g1 (band 155-186 kabul)

**Risk 3: Streamlit Tarayici siralama kayar**
- Kullanici beklentisi shift
- Mitigation: UI'da "Phase 4a Damodaran-sadik" rozet + audit chain doc link

**Risk 4: Adim 6 (orchestrator adapter) implement hatasi**
- En karmasik adim, ~2 gun
- Mitigation:
    a) 5 ticker manuel test (TUPRS/EREGL/ARCLK/BIM/ASELS)
    b) Pre-implement: ProjectionInputsBuilder unit test
    c) Engine A 4-case validation re-run (Heineken/ABN/Tube/Toyota)

## Section 7 — Phase 4b/4c/4d Parking

**Phase 4b (Banking DDM Tier 1):**
- AKBNK/YKBNK/ISCTR 2-stage prod (3/5 reasonable)
- GARAN/HALKB outlier sanity flag (>%200 upside review)
- 3-stage TR-specific tune (commit 76 sonrasi param adjust)
- Effort: ~1 gun
- Hedef anchor: v4.6-phase4b-banking-tier1-sealed

**Phase 4c (Banking Tier 2 + TR-specific tune):**
- TSKB/KLNMA/SKBNK/QNBTR (manuel banking_data config)
- 3-stage DDM TR-banking parametre tune (stable_ROE %18, CRP up)
- Effort: ~2 gun
- Hedef anchor: v4.7-phase4c-banking-tier2-sealed

**Phase 4d (Multi-multiple + young_firm):**
- PE + PBV consensus (sadece EV/EBITDA mevcut)
- Amazon young_firm_dcf (_wip_amazon WIP from commit memory)
- ImpliedROCROE terminal sanity (Damodaran webcast Phase 4 yan)
- Effort: ~2-3 gun
- Hedef anchor: v4.8-phase4d-multi-multiple-sealed

## Section 8 — Test Plan

**Pre-implement test (Adim 6 oncesi):**
1. Engine A 4-case validation re-run (PASS hala?)
2. ProjectionInputsBuilder unit test (TickerDataV4 → ProjectionInputs)
3. 5 BIST ticker manuel Damodaran-rule sanity:
   - TUPRS: Damodaran cyclical petrol → ~90-130 TL?
   - EREGL: cyclical steel → ?
   - ARCLK: mature stable → ?
   - BIM: mature growth → ?
   - ASELS: high growth defense → ?

**Post-implement test (Adim 7):**
1. 615 ticker batch regen
2. 6 sanity gate
3. Phase 1+2+3 chain regression (KCHOL 161.85, AHGAZ 26.71, vs.)
4. Engine A coverage report: 145 industrial Engine A, 10 holding adapter, 16 banking 2-stage, vs.

**Acceptance:**
- 6/6 sanity gate PASS
- 4/4 validation case Engine A path PASS (regression)
- Universe Damodaran-sadik 155-186 range
- TUPRS yeni band 90-130 TL kabul

---

## Approval

- [x] Doctrine validated
- [ ] Phase 4a implement onayi (kullanici)
- [ ] Adim 1 implement start
