# Phase 3b Progress

**Tarih:** 12 Mayis 2026

## 4 Adim Ozeti

| Adim | Commit | Hash | Aciklama |
|------|--------|------|----------|
| 1 | 58 | f706205 | cross_holdings.py 3-tier (banking/unknown proxy) |
| 1.5 | 60 | 8d20b2a | Full subs inclusion (SKIP fix) |
| 2 | 59 | 726a534 | orchestrator_v4 holding branch rewrite |
| 3 | 61 | 075b629 | Batch regen (10 holding intrinsic filled) |
| 4 | 62-63 | (this) | Audit chain + UI sync + SEALED |

## Sanity Gates (Adim 3, 5 gate PASS)

- Gate A: TUPRS 211.95 INTACT (drift 0.0019%)
- Gate B: total_count 615 korundu, dcf_count 143 -> 155 (+12)
- Gate C: KCHOL/SAHOL intrinsic dolu (phase3b method)
- Gate D: KCHOL ±%30 Damodaran rule PASS
- Gate E: Holding coverage 10/41 (%24.4)

## Recovery Analiz

| Phase | Holding Intrinsic Filled | Recovery Rate |
|-------|--------------------------|---------------|
| Phase 2 | 0/41 | %0 |
| Phase 3b | 10/41 | %24.4 |

Kalan 31 holding: holding_sotp_pending (CH=0, listed sub yok) — Phase 3c kapsami.

## Method Dist (Holding)

| Method | Count |
|--------|-------|
| holding_sotp_pending | 30 |
| holding_sotp_phase3b | 10 |
| holding_sotp_phase3b_negative | 1 |

## Cross-holdings populate

Phase 1+2: 9 CH-value populate
Phase 3a: 13 (TUPRS/AKCNS gibi industrial joint subs)
Phase 3b: 26 (+13 full subs eklendi)
