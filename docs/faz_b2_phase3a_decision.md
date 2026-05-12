# Phase 3a Decision Doc

**Tarih:** 12 Mayis 2026
**Scope:** KAP XBRL bilanco istirak/yatirim parse
**Sonuc:** SEALED (anchor v4.3.3-phase3a-sealed)

## Karar Konusu

Phase 2 SEALED state'te KCHOL/SAHOL/OYYAT "minimal SOTP" ile negative_equity
olarak isaretli. Cozum icin Phase 3'un ilk alt-fazi (3a): yeni 2 field parse.

## Yapilan Secimler

| Konu | Karar | Gerekce |
|------|-------|---------|
| Parse field'lari | 2 yeni: equity_method_investments + investment_properties | Konsolide bilanco DISI, cross_holdings ile cakismaz |
| SKIP edilenler | financial_investments_long, kisa vadeli, istirakler | Double-count veya cash equivalent |
| Banking dialect | KAPSAM DISI | banking_skip nedeniyle production etki 0 |
| Parser pattern | _find_value_in_tables require_exact=True | Mevcut pattern korundu |
| TR decimal handling | _parse_tr_number (mevcut) | Yeni helper gereksiz |
| Audit chain | 4 doc (Phase 1+2 ile uyumlu) | findings.md Adim 1'de yapildi |

## Beklenmedik Bulgular (Gate D)

Phase 3a etkisi tahmin edilenden buyuk:
  - equity_method_investments: 109/615 ticker (%17.7) — holdings + industrial mix
  - investment_properties: 271/615 ticker (%44.1) — REIT + gayrimenkul exposure cok yaygin

Bu Phase 3b scope'unu genisletir — sadece 2-3 holding degil, 100+ ticker etkilenir.
