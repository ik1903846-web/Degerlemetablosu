# Faz B2 Phase 2 — Decision

**Session:** 7.x | **Tarih:** 2026-05-10 | **ADR:** 078 (Phase 2 update)

## Plan Revize (Post-Keşif)

Original plan (kpy41_acc8 fetcher) → IPTAL (endpoint yok)
Yeni plan: kpy41_acc7 parser improvement

## Phase 2 Tasarım Kararları

### D1: Idempotent Post-Processing
relationship_categorizer.py ayrı modül, parser DOKUNULMAZ.
NaN olmayan kayıtlara dokunmaz. Tekrar çalıştırılabilir.

### D2: Keyword Priority + Composite Override
Damodaran kategorileri Türkçe KAP terminolojisi ile eşleşti.
"Girişim Şirketi (Finansal Yatırım)" → financial (composite override)

### D3: Decimal Format Tolerance
Türkçe virgül, %100, ondalık çok haneli (8,24742) destekli.

### D4: Holdings Minimal SOTP + Negative Equity Guard
KCHOL/SAHOL audit field populate, NaN intrinsic guard.
Konsolide debt asimetri sorunu Phase 3 scope (full sub valuation).

### D5: Damodaran Transparency
Negatif equity flag'de açıkça yazılı:
  "holding_sotp_minimal_negative: cross + cash - debt = -X TL"
  "holding_sotp_full_pending: full sub valuation Phase 3 scope"
