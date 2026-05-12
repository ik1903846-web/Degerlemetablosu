# Phase 3b Decision Doc

**Tarih:** 12 Mayis 2026
**Scope:** Per-sub DCF + multi-tier holding (cross_holdings + parent debt asimetri)
**Sonuc:** SEALED (anchor v4.3.4-phase3b-sealed)

## Karar Konusu

Phase 3a SEALED state'te 2 yeni field (emi, ip) parse edildi ama henuz
tuketilmedi. Phase 2 minimal SOTP 41 holding'i negative_equity ile isaretledi.
Phase 3b cozum: cross_holdings 3-tier + parent debt asimetri formulu.

## Yapilan Secimler

| Konu | Karar | Gerekce |
|------|-------|---------|
| Cross_holdings tier | 3-tier (Phase 1+2+banking+unknown proxy) | Damodaran SOTP standart |
| Full subs inclusion | SKIP listesinden cikarildi (Adim 1.5) | Cons_ratio asimetriyi cozuyor |
| Recursion | SKIP | Sub kendi DCF'i, market_cap zaten piyasa konsensus |
| Banking sub | market_cap × ownership + flag | Banking DDM Faz 6.5+ scope |
| Unknown dialect | market_cap × ownership + flag | Insurance/REIT subset audit transparency |
| Parent_only_debt | total_debt × (1 - cons_ratio), cons_ratio cap 0.85 | Damodaran pragmatic SOTP |

## Damodaran SOTP Standardi

parent_equity = SUM(listed_sub.market_cap × ownership)
              + equity_method_investments
              + investment_properties
              + parent_only_cash
              - parent_only_debt

Konsolide cash/debt asimetri:
  cons_ratio = SUM(full_listed_sub.ownership), capped 0.85
  parent_only_X = X_consolidated × (1 - cons_ratio)

## Validation Sonuc

| Ticker | Phase 2 | Phase 3b | Market | Upside | Damodaran ±%30 |
|--------|---------|----------|--------|--------|----------------|
| KCHOL  | None    | 161.85 TL | 213.20 | -24.1% | PASS |
| SAHOL  | None    |  19.94 TL | ~100 TL?(shares bug) | -80% | shares bug isareti |
| OYYAT  | None    | None (phase3b_negative) | small | - | konservatif beklenen |
| TUPRS  | 211.95  | 211.95     | 215    | -1.4%  | INTACT (industrial) |

## Phase 3c'ye Devir (Damodaran Sector Regression)

OYYAT gibi kucuk holding'ler (cons_ratio=0, listed sub yok) Phase 3b'de
intrinsic null. Phase 3c'de Damodaran sector regression ile fallback:
  if dcf_fails: sector_multiple_value
