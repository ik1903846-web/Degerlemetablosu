# TUPRS Shadow Calculation - Faz B1 Adim 5

**Rapor tarihi (UTC):** 2026-05-09T15:01:16.350429+00:00
**Yontem:** WACC ratio (anchor INTACT, FCFF projection sabit)

## Anchor Durumu

- **TUPRS_v4.0_anchor:** 187.10 TL
- **Param state:** Ocak 2026 (production stale)
- **Status:** INTACT - Bu hesapta DOKUNULMADI

## Sensitivity Profiles

### TUPRS Defansif (dusuk beta, lambda<1)

- Profile key: `TUPRS_defensive`
- Rationale: Petrokimya defansif yorum, ihracat dusuk varsayim

| Metric | Production | Damodaran | Delta |
|--------|------------|-----------|-------|
| Beta levered | 1.1638 | 1.1638 | (sabit) |
| WACC | 12.68% | 11.34% | -1.33pp |
| Value ratio (norm) | 1.0000 | 1.1521 | +15.21% |
| TUPRS shadow (TL) | 187.10 | **215.56** | **+15.21%** |

### TUPRS Base (Damodaran sector cyclical)

- Profile key: `TUPRS_base`
- Rationale: Damodaran sector beta cyclical petrokimya, lambda=1 domestik+regional heavy

| Metric | Production | Damodaran | Delta |
|--------|------------|-----------|-------|
| Beta levered | 1.3650 | 1.3650 | (sabit) |
| WACC | 13.65% | 12.16% | -1.49pp |
| Value ratio (norm) | 1.0000 | 1.1567 | +15.67% |
| TUPRS shadow (TL) | 187.10 | **216.41** | **+15.67%** |

### TUPRS Agresif (yuksek beta, commodity export)

- Profile key: `TUPRS_aggressive`
- Rationale: Cyclical aggressive yorum, commodity export lambda > 1 (Damodaran formulu)

| Metric | Production | Damodaran | Delta |
|--------|------------|-----------|-------|
| Beta levered | 1.5812 | 1.5812 | (sabit) |
| WACC | 14.54% | 12.92% | -1.62pp |
| Value ratio (norm) | 1.0000 | 1.1599 | +15.99% |
| TUPRS shadow (TL) | 187.10 | **217.03** | **+15.99%** |

## Shadow Range Ozeti

- **Min shadow:** 215.56 TL
- **Max shadow:** 217.03 TL
- **Mean shadow:** 216.33 TL
- **Mean delta:** +15.62%

## Audit Decision §3.5 Beklentisi vs Sonuc

- Beklenen shadow: 210-225 TL araligi
- Olculen shadow range: 215.56 - 217.03 TL
- **Sonuc: BEKLENTI ICINDE (range bekleneni kapsiyor)**

## Adim 6 Onerisi (audit_decision §3.6)

**Onerilen: 6a Yumusak Gecis**

- v4.0 anchor (187.10 TL): Git tag `anchor-v4.0-pre-Feb2026`
- v4.1 anchor (yeni): 216.33 TL (3 profil ortalamasi)
- Gecis tarihi: bugun (2026-05-09)
- Yeni Δ tolerance: %0.50 (gecis ayinda esnek)
- 1 ay sonra Δ tolerance %0.30'a sikilasir

Reddedilen: 6b cift anchor (operasyonel karmasa), 6c degistirme (apples-to-oranges, bilimsel olmuyor).

## Sonraki Adim

- **Adim 6:** Yumusak gecis kararini commit'le (yeni anchor ilan, eski archive)
- **Adim 7:** cost_of_capital.py constants update (atomic, audit_decision_v4.md)
- **Adim 8:** ADR-040 post-mortem

---

*Read-only test. TUPRS anchor 187.10 DOKUNULMADI. cost_of_capital.py DOKUNULMADI.*
