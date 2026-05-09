# Production vs Damodaran Parameter Diff

**Rapor tarihi (UTC):** 2026-05-09T14:42:34.720769+00:00
**Audit faz:** Faz B1 Adim 2C
**Production source:** apps/api/dcf_engine_v4/cost_of_capital.py
**Damodaran source:** apps/api/data/damodaran/2026_05_09/parameters.json

## Karsilastirma

| Constant | Line | Production | Damodaran (2026-05-09) | Delta | Status |
|----------|------|------------|------------------------|-------|--------|
| `RF_USD_10Y` | 27 | 0.0397 | 0.0395 | -0.0002 (-0.02 pp) | **MATCH** |
| `MATURE_ERP_US` | 28 | 0.0444 | 0.0423 | -0.0021 (-0.21 pp) | **MISMATCH** |
| `TURKEY_CRP` | 29 | 0.0601 | 0.0466 | -0.0135 (-1.35 pp) | **MISMATCH** |
| `TURKEY_SOVEREIGN_SPREAD` | 31 | 0.0446 | 0.0306 | -0.0140 (-1.40 pp) | **MISMATCH** |
| `TURKEY_DEFAULT_SPREAD` | — | NOT FOUND | 0.0306 | — | **NOT_FOUND** |
| `TURKEY_RATING` | — | NOT FOUND | Ba3 | — | **NOT_FOUND** |
| `US_DEFAULT_SPREAD` | — | NOT FOUND | 0.0023 | — | **NOT_FOUND** |
| `US_RATING` | — | NOT FOUND | Aa1 | — | **NOT_FOUND** |

## Ozet

- Toplam kontrol: 8
- MATCH: 1
- MISMATCH: 3
- NOT_FOUND: 4

## Kritik Sapmalar (MISMATCH)

- **MATURE_ERP_US** (line 28): production=0.0444, damodaran=0.0423, delta=-0.21 pp
- **TURKEY_CRP** (line 29): production=0.0601, damodaran=0.0466, delta=-1.35 pp
- **TURKEY_SOVEREIGN_SPREAD** (line 31): production=0.0446, damodaran=0.0306, delta=-1.40 pp

## Sonraki Adim

- **Adim 3:** TTRAK uzerinde test sirketi dogrulamasi (anchor INTACT)
- **Adim 7:** cost_of_capital.py constants update (atomic, audit_decision_v4.md kurali)
- **Adim 8:** ADR-040 post-mortem - neden Subat 2026 update otomatik fetch'lenmedi?

---

*Bu rapor read-only diff'ten uretildi. cost_of_capital.py MODIFY EDILMEDI.*
