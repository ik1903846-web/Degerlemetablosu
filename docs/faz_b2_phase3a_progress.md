# Phase 3a Progress

**Tarih:** 12 Mayis 2026

## 5 Adim Ozeti

| Adim | Commit | Hash | Aciklama |
|------|--------|------|----------|
| 1 | 53 | e81b0d2 | findings.md kanit belgesi |
| 2 | 54 | 5994da5 | FinancialLineItems +2 field |
| 3 | 55 | 20e4b79 | _parse_balance_sheet +2 tag |
| 4 | 56 | c321da1 | orchestrator chain + batch regen |
| 5 | 57 | (this) | audit chain + anchor v4.3.3 |

## Sanity Gates (Adim 4)

- Gate A: TUPRS 211.95 INTACT (drift 0.0019%)
- Gate B: total_count 615 korundu
- Gate C: KCHOL emi=113.6B, ip=3.1B (kanit)
- Gate D: Coverage emi 109/615, ip 271/615

## Regen Sure

56.7 dk (cache invalidate sonrasi tam parse).
Onceki Phase 2 regen 16.5 sn (cache hit) — Phase 3a parse 2 yeni field nedeniyle
KAP excel yeniden okuma gerekti.

## Top 10 EMI Ticker

SAHOL 124.9B, KCHOL 113.6B, ALARK 48.3B, AYGAZ 46.7B, THYAO 35.5B,
PETKM 32.0B, TAVHL 31.0B, ECZYT 18.0B, BRYAT 17.7B, TUPRS 16.5B
