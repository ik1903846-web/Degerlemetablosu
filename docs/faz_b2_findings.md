# Faz B2 Phase 1 — Findings

**Session:** 7.x | **Tarih:** 2026-05-10 | **Durum:** SEALED

## 1. Cross-Holdings Gap

DCF formülü Damodaran ile uyumsuzdu:
- Mevcut: equity = ev - debt + cash
- Damodaran: equity = ev - debt + cash + cross_holdings + non_op

Cross-holdings DCF'ten kaçırılıyordu, holdings/parent ticker'lar
sistematik undervalue.

## 2. ARCLK Örneği

KCHOL'un joint venture'ları DCF'te 0:
- FROTO: 342B × 38.65% = 132B TL
- TOASO: 160B × 37.62% = 60B TL
- Toplam KCHOL cross: ~192B TL kayıp

## 3. Veri Altyapı

KAP cache: kap_subs_2026-05-10.csv, 3511 record
- Listed sub: 124 | unique: 100 | parent: 68
- Damodaran karşılığı:
  - full (>50%) → SKIP (konsolide)
  - equity (20-50%) → EKLE
  - joint → EKLE (FROTO, ENJSA)
  - financial (<20%) → EKLE
  - null → manuel review

## 4. Phase 1 Scope

ÇÖZER: Industrial parent + listed subsidiary cross-holdings
ÇÖZMEZ:
- Holdings operating DCF (Phase 2/3 SOTP)
- Bankalar (ADR-009, equity-only model)
- Null relationship_type
- IFRS bilanço financial_investments
