# Faz B2 Phase 3 — Buyuk Resim Decision Doc

**Tarih:** 11 Mayis 2026
**Scope:** KCHOL/SAHOL gercek intrinsic + full sub valuation × ownership
**Tahmini:** ~12-15 gun, 4 alt-faz, 20-30 commit
**Onceki adim:** Phase 2 SEALED (anchor v4.3) + Operasyonel Sertlestirme Adim 1+2 (v4.3.2)

## Mevcut Durum (Phase 2 SEALED)

KCHOL, SAHOL, OYYAT holding ticker'lari Phase 2'de "minimal SOTP"
ile islenmis. Sonuc: **negative_equity** (konsolide debt asimetri).

| Ticker | CH (Phase 1) | Cash | Debt | Minimal SOTP | Method |
|--------|--------------|------|------|--------------|--------|
| KCHOL  | 192.5B       | 311B | 646B | -143B        | holding_sotp_minimal_negative_equity |
| SAHOL  | 85.1B        | 163B | 356B | -108B        | holding_sotp_minimal_negative_equity |
| OYYAT  | 509M         | 925M | 6.7B | -5.3B        | holding_sotp_minimal_negative_equity |

**Sorun:** Cash + debt KONSOLIDE (parent + tum subs), cross_holdings ise
parent-level. Asimetri matematik bozar.

**Cozum (Phase 3):** Sub-level DCF + parent attribution.
  KCHOL_intrinsic = SUM(sub_DCF_i * ownership_i) + non_op - parent_only_debt
  Konsolide debt cancel olur (sub_DCF kendi debt'ini icerir)

## 4 Alt-Faz Breakdown

### Phase 3a — KAP XBRL Financial Investments Parse (~3-4 gun)

**Hedef:** parsed_financials/*.json'a financial_investments field

**Adimlar:**
- kap_excel_parser.py'a Turkce XBRL tag mapping:
  - "Istirakler ve Is Ortakliklari"
  - "Finansal Yatirimlar"
  - "Yatirim Amacli Gayrimenkuller"
- ParsedFinancialItems dataclass extend
- 615 ticker × 9 sn = ~90 dk lokal regen
- Validation: KCHOL'da FROTO/AKBNK istirak degeri dolu mu
- 5-doc audit chain + Phase 3a SEALED tag

**Risk:** Dusuk (parsing katman extension)

### Phase 3b — Per-Sub DCF + Multi-Tier Holding (~4-5 gun)

**Hedef:** KCHOL/SAHOL gercek intrinsic (negative -> positive)

**Adimlar:**
- orchestrator_v4 holding branch yeniden yaz:
  - Sub-level DCF chain (recursion limit: max 3 tier)
  - Konsolide debt sub-level subtraction
- parent_intrinsic formula:
  parent = SUM(sub_intrinsic_i × ownership_pct_i)
         + non_op_assets
         - parent_only_debt (KONSOLIDE DEGIL)
- Multi-tier sirasiyla:
  Listed sub: market_cap × ownership (Phase 1+2 pattern)
  Listed degil + financial_investments dolu: book value × ownership
  Banking sub (AKBNK gibi): market_cap × ownership (banking_market_proxy flag)
  Hicbiri yok: skip + private_sub_no_data flag
- Validation: KCHOL ~ market_cap ±%30 (Damodaran SOTP rule)
- 5-doc audit chain + Phase 3b SEALED tag

**Risk:** YUKSEK (recursion, banking limit case, KCHOL deep holding 40 sub)

### Phase 3c — Damodaran Sector Regression (~3-4 gun)

**Hedef:** DCF basarisiz case'lerde sector multiple ile fallback

**Adimlar:**
- Damodaran vebupdt.html parse (sector EV/EBITDA, PE, EV/Sales)
- Annual fetch (Ocak update)
- BIST sector mapping entegrasyon (bist_sector_beta)
- orchestrator_v4 alternatif path:
  if dcf_fails: sector_multiple_value
- Cross-validation: DCF vs sector ±%20
- 5-doc audit chain + Phase 3c SEALED tag

**Risk:** Orta (yeni data source, parser fragility)

### Phase 3d — Audit + UI Sync + Anchor v4.4 (~2-3 gun)

**Hedef:** Phase 3 SEALED, production'da goster

**Adimlar:**
- 5-doc audit chain final (decision + progress + resolution + ADR-079 + spec_v3 §16)
- anchor.json v4.3.2 -> v4.4 transition
- UI Phase 3 sync (Adim 2.5 pattern):
  KCHOL/SAHOL artik intrinsic dolu -> upside hesabi
  Streamlit Tarayici'da gozukur
- git tag anchor-v4.4-phase3-sealed

**Risk:** Dusuk

## Karar Tablosu

| Soru | Karar |
|------|-------|
| Phase 3 gerekli mi? | EVET (KCHOL/SAHOL universe %5'i, intrinsic null) |
| 14 gun tahmini uyumlu mu? | EVET (Phase 1+2 olceginde) |
| Siralama 3a -> 3b -> 3c -> 3d | EVET (3a 3b'nin girdisi) |
| Private sub icin yaklasim | Hibrit (listed=market_cap, unlisted=book value, hicbiri=skip+flag) |
| Banking limit case (AKBNK) | market_cap × ownership (banking_market_proxy flag) |
| ADR | YENI ADR-079 (ADR-078 Phase 1+2 sealed) |

## Risk Register

| ID | Risk | Olasilik | Etki | Azaltma |
|----|------|----------|------|---------|
| R1 | Recursion infinite loop (KCHOL -> sub -> KCHOL) | Orta | Yuksek | Max tier=3, visited set |
| R2 | Banking limit case yanlis valuation | Orta | Orta | banking_market_proxy flag transparent |
| R3 | Konsolide debt double-count | Yuksek | Yuksek | Sub-level test (FROTO standalone DCF) |
| R4 | TUPRS anchor drift (cross_holdings refactor) | Dusuk | Yuksek | Anchor v4.3.x test her commit |
| R5 | Phase 3a parsing tag eksik | Orta | Orta | Multiple Turkce XBRL alternatif tag |
| R6 | Damodaran sector data fetch fail | Orta | Dusuk | Annual fetch + manual fallback |

## Validation Kriterleri

Phase 3 SEALED kriterleri:
- KCHOL intrinsic dolu (negative_equity flag yok)
- SAHOL intrinsic dolu
- KCHOL intrinsic ~market_cap ±%30 (Damodaran SOTP rule)
- TUPRS 211.95 INTACT
- 615 ticker total_count korundu
- Streamlit UI Phase 3 sync (Adim 2.5 pattern)
- 5-doc audit chain her alt-faz icin
- 4 SEALED tag (Phase 3a/b/c/d) + 1 anchor v4.4-phase3

## Sonraki Adim

Phase 3a kesif brief:
- kap_excel_parser.py mevcut tag mapping inceleme
- KAP XBRL'da "Istirakler" tag varianti arama
- ParsedFinancialItems extend plani
- Test ticker secimi (KCHOL en kompleks, ARCLK basit endustriyel)
