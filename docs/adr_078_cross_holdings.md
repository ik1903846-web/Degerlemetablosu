# ADR-078: Cross-Holdings Valuation Protocol

| Meta | Değer |
|------|-------|
| Status | ACCEPTED (Phase 1 PRODUCTION, 2026-05-10) |
| Phase 1 Commits | 74e13f0 (Adım 1), abdf9c0 (Adım 2), c6c10f1 (Adım 3), 80f7ef3 (Adım 4), 4c40f73 (Adım 4 tamamlama audit echo) |
| Production Effect | 4 ticker delta (ESEN +481%, GOLTS +367%, ALGYO +173%, AKCNS +68%) — 9 audit populate, 0 anomali, TUPRS INTACT 211.95 |
| Phase 2/3 | PARKING |
| Tarih | 10 Mayıs 2026 |
| Trigger | Session 7.x keşif (Damodaran ilke ihlali tespit) |
| Bağlam | Spec v3.0 §12.5 + ARCLK/KCHOL gap analizi |

## 1. Konu

Cross-holdings (bağlı ortaklık + iştirak + finansal yatırım) DCF firm value formülünde dikkate alınmıyor. Damodaran metodolojisi:

  Equity Value = Operating Assets DCF
               + Cash & marketable securities
               + Cross-holdings (market value veya intrinsic)
               + Other non-operating assets
               - Debt

Mevcut sistem (fcff_engine.py:152):

  Equity Value = Operating EV + Cash - Debt
                                    ─────
                                    Cross-holdings YOK

## 2. Etki Analizi (Session 7.x Keşif)

### 2.1 Subsidiary Cache (kpy41_acc7 - >%50)

  Total: 3511 record, 12 field, 657.5 KB
  Field'lar: parent_ticker, subsidiary_ticker, ownership_pct,
             sub_capital, sector, relationship_type, vs

  Örnek dağılım:
    KCHOL:   40 subsidiary (Pure holding, listed children)
    SAHOL:   18 subsidiary
    TUPRS:    6 subsidiary
    SASA:     3 subsidiary
    ARCLK:  122 subsidiary (Global, Beko Romania vs)

### 2.2 Coverage Gap (KAP endpoint'leri)

  ✓ kpy41_acc5 - Float + shares (kap_float_fetcher)
  ✓ kpy41_acc7 - Bağlı ortaklıklar (>%50)
  ✗ kpy41_acc8 - İştirakler (%20-50)              ← YOK
  ✗ kpy41_acc9 - Finansal yatırımlar (<%20)       ← YOK

### 2.3 IFRS Bilanço Parse Gap

  Grep sonucu (apps/api/data_layer/, dcf_engine_v4/):
    financial_asset:    0 match
    fvtpl, fvtoci:      0 match
    equity_method:      0 match
    investments_in:     0 match

  → Konsolide olmayan finansal varlıklar parse edilmiyor.

### 2.4 DCF Formula Gap

  fcff_engine.py:152:
    equity_value = ev - inputs.total_debt + inputs.cash

  → "non_operating_assets" parametresi yok.

## 3. Damodaran Metodolojisi (Referans)

Cross-holdings 3 kategori:

  Majority (>50%): Konsolide finansal raporda zaten
                   Operating'e dahil. AYRICA EKLEME
                   (double-counting riski!)

  Minority active (20-50%): Equity method
                            → Mark-to-market VEYA intrinsic DCF
                            → Bilançodaki book value yetersiz

  Minority passive (<20%): Fair value (FVTPL/FVTOCI)
                           → Mark-to-market

### 3.1 Critical Rule

"Add cross holdings to firm value BEFORE deriving per-share value."
— Damodaran, Investment Valuation, Ch. 26

## 4. Karar (PROPOSED)

Cross-holdings entegrasyonu **Faz B2** olarak yapılandırılır.

3-Phase yaklaşım:

  Phase 1 — Listed Subsidiary Cross-Holdings (~2-3 gün)
    - Subsidiary cache'de subsidiary_ticker dolu olanlar
    - Market cap × ownership_pct = proportional value
    - DCF firm value'ya eklenir (NON-CONSOLIDATED ise)
    - Etki: ARCLK, TKFEN, ENKAI gibi 20-30 ticker

  Phase 2 — kpy41_acc7 Parser Improvement (~3-5 gün, REVIZE 2026-05-10)
    - Keşif bulgusu: kpy41_acc8 endpoint'i KAP'ta YOK
    - Asıl problem: kpy41_acc7'de 616 NaN relationship_type (raw_text dolu)
    - Adım 1: relationship_raw → relationship_type kategorizer (regex/keyword)
    - Adım 2: ownership_pct fallback parse (raw_text içinde % varsa çek)
    - Adım 3: Holdings SOTP başlangıcı (KCHOL/SAHOL NaN problemi)
    - Adım 4: Regen + sensitivity + audit chain
    - Ref: docs/faz_b2_phase2_findings.md

  Phase 3 — IFRS Bilanço Parse (~2 hafta)
    - financial_investments parser
    - Book value → fair value adjustment
    - Multi-tier holding zinciri (SAHOL → AKBNK → AKGRT)

### 4.1 Double-Counting Önleme Kuralı

  Eğer subsidiary KONSOLIDE finansal raporda → AYRICA EKLEME
  Eğer subsidiary equity method veya investment → AYRICA EKLE

  Detection: relationship_type field'ı, KAP'ta consolidated flag'i

## 5. Risk

  Risk                              Olasılık   Etki    Mitigation
  ───────────────────────────────────────────────────────────────
  Double-counting konsolide ile      Yüksek    Yüksek  Phase 1: konsolide yok
  Cross-holding circular value       Orta      Orta    Iterative valuation
  Listed subsidiary market cap       Düşük     Düşük   yfinance/isyatirim cache
  Book value stale (IFRS)            Yüksek    Orta    Fair value adjustment

## 6. Bağımlılıklar

  - fcff_engine.py firm_value formülü (Phase 1'de patch)
  - kap_subsidiaries_fetcher mevcut (Phase 1)
  - kpy41_acc7 parser improvement (Phase 2 REVIZE — endpoint zaten mevcut)
  - IFRS parser augmentation (Phase 3)
  - Anchor v4.1 → v4.2 transition (Phase 1 sonrası)

## 7. Sonuç

ADR-078 PROPOSED. Implementation Faz B2'de (3 phase, multi-session).

Faz B1 audit chain methodology (5-doc pattern, ADR-073) Faz B2'de tekrar uygulanacak:

  faz_b2_findings.md
  faz_b2_decision.md
  faz_b2_progress.md
  faz_b2_postmortem.md (gerekirse)
  faz_b2_resolution.md
