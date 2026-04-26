"""
Banking Dividend Discount Model (DDM) — 2-stage.

Damodaran ABN Amro reference:
- High growth phase (5 yıl): EPS × payout × (1+g)^t
- Stable phase: Terminal Value = EPS_terminal × payout / (r - g)
- PV at high-growth Cost of Equity
- Final value = PV(high growth DPS) + PV(Terminal)

Industrial FCFF'den FARKLI:
- Revenue/EBIT/margin yok (EPS-based)
- Reinvestment YOK (sadece retention ratio kavramı)
- Tax rate complexity YOK (zaten net income'da hesaplı)

ADR-012: Banking 3-model (DDM + Excess Return + Modified FCFE)
ADR-009: Bank firm valuation YASAK (equity-only zorunlu)
"""

# TODO Faz 1.4 implement: yarın
# Fonksiyonlar:
# - project_dps_high_growth(eps_0, growth, payout, years) -> List[float]
# - terminal_value_ddm(eps_terminal, payout_terminal, coe_stable, growth_stable) -> float
# - dcf_ddm(...) -> DDMResult
