# Faz B2 Phase 1 — Decision

**ADR:** 078 | **Tarih:** 2026-05-10

## 3-Phase Plan

- **Phase 1** (Mayıs 2026, ~3 gün): Listed subsidiary cross-holdings
- **Phase 2** (PARKING, ~7 gün): kpy41_acc8 equity method
- **Phase 3** (PARKING, ~14 gün): IFRS financial_investments parse

## Phase 1 Tasarım Kararları

### D1: Damodaran Formula
equity_value = ev - debt + cash + cross_holdings_value

### D2: Konsolide SKIP
SKIP_RELATIONSHIPS = {'full'}
ELIGIBLE = {'equity', 'financial', 'joint'}

### D3: Backward Compat
cross_holdings_value: float = 0.0 (default)

### D4: Audit Echo
TickerDataV4 + DCFResult'a audit field
Batch JSON traceable

### D5: Per-Ticker Try/Except
Bir ticker fail diğer 614'ü etkilemez

## Reddedilenler

- Big-Bang IFRS (~14 gün scope, anchor risk)
- Banking industrial FCFF (ADR-009 ihlali)
