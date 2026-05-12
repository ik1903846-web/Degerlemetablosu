# Faz B2 Phase 3 — Master Decision Doc

**Tarih:** 12 Mayis 2026
**Scope:** KCHOL/SAHOL gercek intrinsic + full sub valuation evren genisletmesi
**Sonuc:** SEALED (anchor v4.4-phase3-sealed)

## Phase 3 Buyuk Resim

Decision doc commit 52 (d7be2cd) ile Phase 3 4 alt-faza bolundu:
  - 3a: KAP XBRL +2 field parse
  - 3b: Per-sub DCF + multi-tier holding
  - 3c: Damodaran sector regression fallback
  - 3d: Master audit + anchor v4.4 (THIS DOC)

## 3 Alt-Faz Ozet

### Phase 3a SEALED (commits 53-57, anchor v4.3.3)

Kazanim:
  parsed_financials/*.json'a 2 yeni field:
    equity_method_investments (109/615, %17.7)
    investment_properties (271/615, %44.1)

  KCHOL ornek: emi=113.6B, ip=3.1B (konsolide bilanco DISI)

### Phase 3b SEALED (commits 58-63, anchor v4.3.4)

Kazanim:
  cross_holdings.py 3-tier valuation (listed/banking/unknown proxy)
  orchestrator_v4 holding branch yeniden yaz (parent debt asimetri)
  parent_only_debt = total_debt × (1 - cons_ratio), cap 0.85
  Full subs SKIP fix (Damodaran SOTP standart)

  Recovery: 0/41 -> 10/41 holding intrinsic (24.4%)
  KCHOL: None -> 161.85 TL (Damodaran ±%30 PASS)

### Phase 3c SEALED (commits 64-70, anchor v4.3.5)

Kazanim:
  Damodaran sector multiples fetcher (92 sector, annual)
  BIST -> Damodaran sector mapping (%93.2)
  3-Level fallback chain (industrial / sector / book_value)
  Sanity cap Damodaran ±%100

  Recovery: 155/615 -> 186/615 (+31, +5.0% universe)

## Damodaran SOTP Chain (Final)

Level 1: Industrial DCF / Phase 3b SOTP
  industrial_fcff_2stage (145 ticker)
  holding_sotp_phase3b (10 ticker)

Level 2: Sector multiple regression
  sector_multiple_regression (16 ticker)
  EV = sector_EV_EBITDA × EBITDA
  Equity = EV - debt + cash
  Sanity cap: ±%100

Level 3: book_value_fallback (Damodaran Dark Side)
  book_value_fallback (15 ticker)
  intrinsic = total_equity / shares (konservatif)

Level 4: None + flag (Phase 4+ scope)
  banking_skip, unknown_skip, fcff_negative, None sector

## Aktif Production State

Anchor: v4.4-phase3-sealed
Universe: 186/615 intrinsic dolu (30.2%)
TUPRS: 211.95412760984857 (10 anchor noktasi, drift 0.0019%)
KCHOL: 161.85 TL (Damodaran ±%30 PASS)
SAHOL: 19.94 TL

## Sirada (Phase 4+ veya Faz B3)

| Item | Scope |
|------|-------|
| Banking DDM (16 ticker) | Faz 6.5+ |
| fcff_negative case'ler (135) | Phase 4 (Decline/Distress, Damodaran patterns) |
| Multi-multiple consensus (PE + PBV) | Phase 4 |
| Sector regression refinement | Phase 4 |
