# Parameter Sensitivity Test - Faz B1 Adim 3

**Rapor tarihi (UTC):** 2026-05-09T14:49:25.839462+00:00
**Production source:** apps/api/dcf_engine_v4/cost_of_capital.py (Adim 2C okundu)
**Damodaran source:** apps/api/data/damodaran/2026_05_09/parameters.json

## Parametre Snapshot

| Parametre | Production | Damodaran | Delta |
|-----------|------------|-----------|-------|
| RF | 3.97% | 3.95% | -0.02pp |
| Mature ERP | 4.44% | 4.23% | -0.21pp |
| Turkey CRP | 6.01% | 4.66% | -1.35pp |
| Turkey Sovereign Spread | 4.46% | 3.06% | -1.40pp |

## Profil Bazli DCF Sapmalari

### Turk Traktor (Mature Growth, Stage 4)

- Profile key: `TTRAK_approx`
- Beta levered: 1.0925

| Metric | Production | Damodaran | Delta |
|--------|------------|-----------|-------|
| Cost of Equity | 13.93% | 12.53% | -1.40pp |
| Cost of Debt (pre-tax) | 9.93% | 8.51% | -1.42pp |
| WACC | 12.85% | 11.51% | -1.34pp |
| DCF value (normalized) | 1140.22 | 1313.98 | **+15.24%** |

### Tipik domestic BIST (Stage 4, sanity check)

- Profile key: `TYPICAL_DOMESTIC`
- Beta levered: 1.3750

| Metric | Production | Damodaran | Delta |
|--------|------------|-----------|-------|
| Cost of Equity | 16.09% | 14.43% | -1.66pp |
| Cost of Debt (pre-tax) | 10.43% | 9.01% | -1.42pp |
| WACC | 13.33% | 11.87% | -1.46pp |
| DCF value (normalized) | 1046.02 | 1211.91 | **+15.86%** |

## Ozet

- Profil sayisi: 2
- Ortalama DCF sapma: **+15.55%**

## Karar Noktasi (audit_decision §3.4)

- **%5-25 (BEKLENEN):** Audit hipotezi teyit. Adim 5'e gec (TUPRS shadow hesap).
- Anchor 187.10 INTACT, sadece shadow run.

---

*Read-only test. cost_of_capital.py MODIFY EDILMEDI. TUPRS test edilmedi (anchor riski).*
