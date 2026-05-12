# Phase 3a Resolution

**Tarih:** 12 Mayis 2026
**Sonuc:** SEALED

## Hedef ve Sonuc

| Hedef | Durum |
|-------|-------|
| 2 yeni KAP field parse | TAMAM |
| FinancialLineItems extend | TAMAM (38 field) |
| Orchestrator chain | TAMAM |
| Batch regen + sanity gates | TAMAM (4 gate PASS) |
| Audit chain | TAMAM (4 doc + tag) |

## Phase 3b'ye Devir

Phase 3a sadece DATA layer. Phase 3b'de bu data tuketilecek:

1. cross_holdings.py extend:
   - Listed sub: market_cap × ownership (Phase 1+2 mevcut)
   - Unlisted + emi dolu: book value × ownership (Phase 3b YENI)
   - Hicbiri yok: skip + private_sub_no_data flag

2. orchestrator_v4 holding branch yeniden yaz:
   - Sub-level DCF chain (max tier=3)
   - parent_intrinsic = SUM(sub_intrinsic_i × ownership_i)
                       + non_op_assets
                       - parent_only_debt

3. Validation: KCHOL ~ market_cap ±%30

## Bilinen Kisitlar

- Banking sub (AKBNK gibi) Phase 3b'de market_cap × ownership ile cozulecek (ADR-079 Q4)
- Phase 3a parser'a "Istirakler ve Bagli Ortakliklardaki Yatirimlar" (row 143) eklemedik
  cunku KCHOL'da NaN — gerekirse Phase 3b'de ekleyebiliriz
- ARCLK gibi industrial'larda da EMI dolu (3.3B) — Phase 3b'de tuketilirse universe genel intrinsic etkisi var

## Anchor Update

v4.3.2 → v4.3.3-phase3a-sealed
