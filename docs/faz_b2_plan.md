# Faz B2 Plan — Cross-Holdings Integration

| Meta | Değer |
|------|-------|
| Status | PLAN (implementation pending) |
| Trigger | Session 7.x keşif + ADR-078 |
| Tarih | 10 Mayıs 2026 |
| Önceki | Faz B1 (Şubat 2026 vintage entegrasyonu) |

## 1. Felsefe

Faz B1'de uyguladığımız 8-adım protokol Faz B2'de tekrar.

  Faz B1 protokolü (ADR-074):
    1. Damodaran resmi sayfa kontrol
    2. parameters.json fetch
    3. Triple-source verify
    4. Production diff
    5. Sensitivity test
    6. Shadow run (TUPRS canonical)
    7. Atomic update (cost_of_capital.py)
    8. Anchor revize (anchor.json + git tag)

Faz B2'ye uyarlanmış protokol:

  1. Subsidiary listed/non-listed segmentation
  2. Market cap fetcher hazırlık (yfinance/isyatirim)
  3. Triple-source verify (ownership_pct + capital + market_cap)
  4. Production diff (mevcut anchor vs cross-holding eklenmiş)
  5. Sensitivity test (Phase 1 etki ölçümü, ARCLK + KCHOL)
  6. Shadow run (TUPRS dahil 5-10 ticker)
  7. Atomic update (fcff_engine.py firm_value formülü)
  8. Anchor revize (v4.1 → v4.2)

## 2. Phase 1 — Listed Subsidiary Cross-Holdings

Hedef: Cache'deki 3511 subsidiary'den listed olanları (subsidiary_ticker dolu) DCF'ye ekle.

### 2.1 Adım 1 — Veri Hazırlık (~3 saat)

  - kap_subs_2026-05-10.csv parse
  - subsidiary_ticker NULL olmayanları filtrele
  - Beklenti: 200-400 listed cross-holding
  - Per parent breakdown rapor

### 2.2 Adım 2 — Market Cap Fetcher (~3 saat)

  - apps/api/data_layer/market_cap_fetcher.py YENI modül
  - yfinance veya isyatirim cache (memory'de yfinance var)
  - Cache: apps/api/_cache/market_caps/YYYY-MM-DD.json
  - 251 BIST ticker market_cap

### 2.3 Adım 3 — Cross-Holdings Valuator (~4 saat)

  - apps/api/dcf_engine_v4/cross_holdings.py YENI modül
  - Function: compute_cross_holdings_value(parent_ticker)
  - Logic:
      Sum over subsidiaries:
        if subsidiary_ticker in BIST listed:
          market_cap = market_cap_fetcher(subsidiary_ticker)
          contribution = market_cap × (ownership_pct / 100)
          if NOT consolidated: include
          if consolidated: skip (double-count)
        else: skip (Phase 2/3 scope)

### 2.4 Adım 4 — fcff_engine.py Patch (~2 saat)

  Mevcut:
    equity_value = ev - inputs.total_debt + inputs.cash

  Yeni:
    cross_holdings = compute_cross_holdings_value(ticker)
    equity_value = ev + inputs.cash + cross_holdings - inputs.total_debt

### 2.5 Adım 5 — Sensitivity Test (~3 saat)

  - 5 ticker: ARCLK, KCHOL, SAHOL, TUPRS, SASA
  - Eski intrinsic vs yeni intrinsic
  - Beklenen: %3-15 artış (parent share × subsidiary market cap proportion)
  - SENARYO: %30+ sapma → manuel review

### 2.6 Adım 6 — Batch Regen + Diff (~2 saat)

  - 251 ticker turkey_v4_batch.json regen
  - TOP 20 değişen ticker raporu
  - Anchor v4.2 transition

### 2.7 Adım 7 — Audit Chain Doc'u (~3 saat)

  - faz_b2_findings.md (keşif sonuçları, Phase 1 dahil)
  - faz_b2_decision.md (8-adım plan)
  - faz_b2_progress.md (adım adım çalışma)
  - faz_b2_resolution.md (Phase 1 close)

### 2.8 Adım 8 — Anchor Revize (~1 saat)

  - apps/api/data/anchor.json v4.1 → v4.2
  - git tag anchor-v4.1-pre-crossholdings
  - Spec v3.1 addendum (yeni anchor + Phase 1 etki)

**Phase 1 toplam: ~21 saat ≈ 3 iş günü** (Faz B1 ile karşılaştırılabilir)

## 3. Phase 2 — İştirak Coverage (kpy41_acc8)

Süre tahmin: ~5-7 iş günü
Detay: Phase 1 sonrası, ayrı plan dosyası

Ana adımlar:
  - kap_affiliates_fetcher.py YENI modül
  - kpy41_acc8 endpoint scrape
  - Equity method valuation
  - Phase 1 entegrasyonu (consistent fallback)

## 4. Phase 3 — IFRS Bilanço Parse

Süre tahmin: ~10-14 iş günü
Detay: Phase 2 sonrası, ayrı plan dosyası

Ana adımlar:
  - kap_excel_parser augmentation (financial_investments fields)
  - Book value vs fair value handling
  - Multi-tier holding zinciri (circular reference önleme)
  - Damodaran iterative valuation pattern

## 5. Faz B2 Toplam Tahmin

  Phase 1: ~3 gün (Mayıs ortası)
  Phase 2: ~7 gün (Haziran başı)
  Phase 3: ~14 gün (Haziran ortası-sonu)
  ────────────────────────────────────
  Toplam:  ~24 iş günü (Mayıs-Haziran 2026)

## 6. Implementation Önceliklendirme

Phase 1 acil mi?

  TUPRS anchor 211.95 etkilenir mi?
    TUPRS sub: 6 record (Ditaş, OPET, Körfez, vs)
    Listed olanlar: ? (kontrol Phase 1 Adım 1'de)

  ARCLK için kritik (122 sub, çoğu non-listed Beko etc).
  KCHOL/SAHOL için zaten "holding_sotp_pending" flag var.

  Sonuç: Phase 1 öncelik **orta-yüksek**. Acil değil ama
         kıymetli. Mayıs ortasına kadar tamamlanabilir.

## 7. Sonuç

Faz B2 PLAN. Implementation onaylanmadıkça başlamaz.

Onay sonrası: Faz B1 disiplini uygulanır. Atomic commit zinciri, audit chain 5-doc pattern, multi-session breakdown.
