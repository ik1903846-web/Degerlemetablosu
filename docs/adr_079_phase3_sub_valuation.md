# ADR-079: Phase 3 Sub Valuation (Full SOTP)

**Status:** SEALED (Phase 3 a+b+c+d tamamlandi, anchor v4.4)
**Tarih:** 12 Mayis 2026
**Onceki ADR:** ADR-078 (Phase 1+2 cross_holdings)

## Context

Phase 1+2 sonunda KCHOL/SAHOL "minimal SOTP" ile negative_equity (konsolide
debt asimetri). Phase 3 cozum tasarimi.

## Karar

4 alt-fazli yaklasim:
- 3a: KAP XBRL +2 field parse (SEALED)
- 3b: Per-sub DCF + multi-tier holding (recursion)
- 3c: Damodaran sector regression (fallback)
- 3d: Audit + UI sync + anchor v4.4

## Q&A (Phase 3 buyuk resim'den)

| Q | Karar | Gerekce |
|---|-------|---------|
| Q1 14 gun tahmini | EVET | Phase 1+2 olcek |
| Q2 Siralama | 3a → 3b → 3c → 3d | 3a 3b'nin girdisi |
| Q3 Private sub | Hibrit (listed/unlisted/skip+flag) | Damodaran konservatif |
| Q4 Banking limit | market_cap × ownership | banking DDM Faz 6.5+ |
| Q5 ADR | Yeni ADR-079 | ADR-078 Phase 1+2 sealed |

## Phase 3a Cikti

- equity_method_investments (109/615 dolu, %17.7)
- investment_properties (271/615 dolu, %44.1)
- TUPRS anchor INTACT
- Production state stable

## Consequences

Phase 3b'de cross_holdings.py book_value_tier eklenecek.
Tum holding ticker'larin intrinsic'i guncellenmesi beklenir.
Banking dialect (AKBNK gibi) market_cap proxy ile islenir.
