# Phase 3c Decision Doc

**Tarih:** 12 Mayis 2026
**Scope:** Damodaran sector multiple regression + book value fallback
**Sonuc:** SEALED (anchor v4.3.5-phase3c-sealed)

## Karar Konusu

Phase 3b SEALED state'te 31 holding_sotp_pending + 1 phase3b_negative
durumda kalmisti. Ayrica 42 None sector_name ticker. Phase 3c hedefi:
Damodaran SOTP fallback chain ile bu ticker'lar icin intrinsic uretmek.

## Damodaran SOTP Fallback Chain (valpacket2)

Level 1: Industrial DCF / Phase 3b SOTP (MEVCUT)
Level 2: Sector multiple regression (Phase 3c YENI)
  EV = sector_EV_EBITDA × EBITDA
  Equity = EV - debt + cash
  intrinsic = Equity / shares
  Sanity cap: |intrinsic/market - 1| > 1.0 -> Level 3'e dus
Level 3: book_value_fallback (Damodaran "Dark Side" konservatif)
  intrinsic = total_equity / shares

## Yapilan Secimler

| Konu | Karar | Gerekce |
|------|-------|---------|
| Multiple secimi | Sadece EV/EBITDA | Damodaran "if conflict, EV/EBITDA primary" |
| PE | SKIP | net_income field yok, op_income×0.75 proxy yanlis sonuc verir |
| PBV | SKIP | Sadece EV/EBITDA + book_value yeterli (Damodaran) |
| Sanity cap | ±%100 (Damodaran rule) | Outlier sector multiple Level 3'e fall back |
| Banking sector | Financial Svcs. (NB&I) @ 52.24x | EV/EBITDA banking icin Damodaran convention |
| Aracı kurumlar | Investments & Asset Mgmt @ 36.76x | Damodaran reference |
| None sector | book_value_fallback | Level 3 konservatif yedek |

## Sector Multiples Source

apps/api/data/damodaran/2026_05_09/sector_multiples.json (92 sector)
Annual fetch (Damodaran Ocak update convention)

## Sector Mapping

apps/api/config/damodaran_sector_map.json (44 BIST TR sector)
Coverage: 573/615 (%93.2)

## Validation Sonuc

| Ticker | Phase 3b | Phase 3c | Method | Market | Upside |
|--------|----------|----------|--------|--------|--------|
| OYYAT | None | 32.45 TL | book_value_fallback (capped) | 54.3 | -40.3% |
| TUPRS | 211.95 | 211.95 INTACT | industrial (Level 1) | - | - |
| KCHOL | 161.85 | 161.85 INTACT | holding_sotp_phase3b (Level 1) | 213 | -24.1% |
| SAHOL | 19.94 | 19.94 INTACT | holding_sotp_phase3b (Level 1) | - | - |
