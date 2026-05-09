# Production vs Damodaran Parameter Diff

**Rapor tarihi (UTC):** 2026-05-09T15:44:43.667542+00:00
**Audit faz:** Faz B1 Adim 2C
**Production source:** apps/api/dcf_engine_v4/cost_of_capital.py
**Damodaran source:** apps/api/data/damodaran/2026_05_09/parameters.json

## Karsilastirma

| Constant | Line | Production | Damodaran (2026-05-09) | Delta | Status |
|----------|------|------------|------------------------|-------|--------|
| `RF_USD_10Y` | 31 | 0.0395 | 0.0395 | +0.0000 (+0.00 pp) | **MATCH** |
| `MATURE_ERP_US` | 32 | 0.0423 | 0.0423 | +0.0000 (+0.00 pp) | **MATCH** |
| `TURKEY_CRP` | 33 | 0.0466 | 0.0466 | +0.0000 (+0.00 pp) | **MATCH** |
| `TURKEY_SOVEREIGN_SPREAD` | 35 | 0.0306 | 0.0306 | +0.0000 (+0.00 pp) | **MATCH** |
| `TURKEY_DEFAULT_SPREAD` | — | NOT FOUND | 0.0306 | — | **NOT_FOUND** |
| `TURKEY_RATING` | — | NOT FOUND | Ba3 | — | **NOT_FOUND** |
| `US_DEFAULT_SPREAD` | — | NOT FOUND | 0.0023 | — | **NOT_FOUND** |
| `US_RATING` | — | NOT FOUND | Aa1 | — | **NOT_FOUND** |

## Ozet

- Toplam kontrol: 8
- MATCH: 4
- MISMATCH: 0
- NOT_FOUND: 4

## Sonraki Adim

- Production zaten guncel. Faz B2'ye gec, sadece spec PDF guncelle.

---

*Bu rapor read-only diff'ten uretildi. cost_of_capital.py MODIFY EDILMEDI.*
