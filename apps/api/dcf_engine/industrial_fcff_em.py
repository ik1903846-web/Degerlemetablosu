"""
Industrial FCFF 2-stage DCF — EM (Emerging Markets) variant.

Damodaran Tube Investments (India) reference (fcff.pdf::page 8):
- Reinvestment-based growth (g = RR × ROC, top-down değil)
- EBIT(1-t) compound projection (revenue compound değil)
- Real Rf (nominal değil) — currency-aware
- Additive CRP (lambda değil)
- Stable phase ayrı WACC (high-growth WACC'tan farklı)

Industrial FCFF (Heineken) farkları:
- Heineken: Revenue × Margin → EBIT, Reinvestment = ΔRev/Sales-to-Cap
- EM:       EBIT(1-t) × (1+g) → EBIT(1-t), Reinvestment = EBIT(1-t) × RR

Module yapısı:
- project_year_reinvestment_based(): Tek yıl FCFF (reinvestment-driven)
- project_multi_year_em(): 5-yıl high growth + Year 6 terminal
- dcf_em_valuation(): Full DCF + equity bridge

ADR References:
- ADR-006a: Industrial FCFF 2-stage
- ADR-006c: EM additive CRP (lambda value-based variant)
- ADR-040: Currency consistency (real Rf for INR)
"""

from dataclasses import dataclass
from typing import List

# Industrial FCFF'den re-use
from .industrial_fcff import (
    discount_to_present_value,
    terminal_value,
)


# ============================================================================
# Single Year Projection (Reinvestment-Based)
# ============================================================================

@dataclass
class YearProjectionEM:
    """Tek yıl FCFF projection (reinvestment-driven)."""
    year: int
    ebit_after_tax: float
    reinvestment: float
    fcff: float


def project_year_reinvestment_based(
    year: int,
    prev_ebit_after_tax: float,
    growth_rate: float,
    reinvestment_rate: float,
) -> YearProjectionEM:
    """
    Reinvestment-driven FCFF (Tube Investments pattern).

    Steps:
        1. EBIT(1-t)_t = EBIT(1-t)_t-1 × (1 + growth)
        2. Reinvestment_t = EBIT(1-t)_t × reinvestment_rate
        3. FCFF_t = EBIT(1-t)_t - Reinvestment_t

    Heineken pattern'inden FARKLI:
    - Revenue × margin yok (direct EBIT compound)
    - Reinvestment formülü farklı (rate × EBIT, ΔRev/Sales-to-Cap değil)

    Args:
        year: Year index (1, 2, ...)
        prev_ebit_after_tax: Previous year EBIT(1-t)
        growth_rate: This year growth rate (decimal)
        reinvestment_rate: This year reinvestment rate (decimal)

    Returns:
        YearProjectionEM

    Example (Tube Investments Year 1):
        >>> proj = project_year_reinvestment_based(
        ...     year=1,
        ...     prev_ebit_after_tax=4425,
        ...     growth_rate=0.0552,
        ...     reinvestment_rate=0.60,
        ... )
        >>> proj.ebit_after_tax
        4669.28...  # 4425 × 1.0552
        >>> proj.reinvestment
        2801.57...  # 4669 × 0.60
        >>> proj.fcff
        1867.71...  # 4669 - 2802
    """
    ebit_at = prev_ebit_after_tax * (1 + growth_rate)
    reinvestment = ebit_at * reinvestment_rate
    fcff = ebit_at - reinvestment

    return YearProjectionEM(
        year=year,
        ebit_after_tax=ebit_at,
        reinvestment=reinvestment,
        fcff=fcff,
    )


# ============================================================================
# Multi-Year Projection
# ============================================================================

def project_multi_year_em(
    starting_ebit_after_tax: float,
    high_growth_rate: float,
    high_reinvestment_rate: float,
    high_growth_duration: int,
    stable_growth_rate: float,
    stable_reinvestment_rate: float,
) -> tuple[List[YearProjectionEM], YearProjectionEM]:
    """
    EM 2-stage projection: high growth + stable Year 6.

    Returns:
        (high_growth_projections, stable_year_6_projection)

    Example (Tube Investments):
        >>> proj_5y, proj_term = project_multi_year_em(
        ...     starting_ebit_after_tax=4425,
        ...     high_growth_rate=0.0552,
        ...     high_reinvestment_rate=0.60,
        ...     high_growth_duration=5,
        ...     stable_growth_rate=0.05,
        ...     stable_reinvestment_rate=0.5435,
        ... )
        >>> [p.fcff for p in proj_5y]  # Year 1-5 FCFF
        [1868, 1971, 2080, 2195, 2316]  # rounded
        >>> proj_term.fcff  # Year 6 stable phase 1. yıl
        2775
    """
    high_growth_projections = []
    prev_ebit = starting_ebit_after_tax

    for year in range(1, high_growth_duration + 1):
        proj = project_year_reinvestment_based(
            year=year,
            prev_ebit_after_tax=prev_ebit,
            growth_rate=high_growth_rate,
            reinvestment_rate=high_reinvestment_rate,
        )
        high_growth_projections.append(proj)
        prev_ebit = proj.ebit_after_tax

    # Year 6 (stable phase 1. yıl)
    # Growth ve reinv rate stable phase'ten
    year_6 = project_year_reinvestment_based(
        year=high_growth_duration + 1,
        prev_ebit_after_tax=prev_ebit,
        growth_rate=stable_growth_rate,
        reinvestment_rate=stable_reinvestment_rate,
    )

    return high_growth_projections, year_6


# ============================================================================
# Full DCF Valuation (EM + Equity Bridge)
# ============================================================================

@dataclass
class DCFEMResult:
    """EM DCF valuation full breakdown."""
    starting_ebit_after_tax: float

    high_growth_wacc: float
    stable_wacc: float
    stable_growth: float

    high_growth_projections: List[YearProjectionEM]
    terminal_year_projection: YearProjectionEM

    terminal_value: float
    pv_high_growth_fcff: float
    pv_terminal_value: float

    firm_value: float
    cash: float
    debt: float
    options_value: float
    equity_value: float

    shares_outstanding: float
    value_per_share: float


def dcf_em_valuation(
    starting_ebit_after_tax: float,
    high_growth_rate: float,
    high_reinvestment_rate: float,
    high_growth_duration: int,
    high_growth_wacc: float,
    stable_growth_rate: float,
    stable_reinvestment_rate: float,
    stable_wacc: float,
    cash: float,
    debt: float,
    options_value: float,
    shares_outstanding: float,
) -> DCFEMResult:
    """
    Full EM DCF valuation: 2-stage + equity bridge.

    Steps:
        1. Project Years 1-N (high growth, EBIT × (1+g), reinv × rate)
        2. Project Year N+1 (stable phase 1. yıl)
        3. Terminal Value = FCFF_N+1 / (stable_wacc - stable_growth)
        4. PV Years 1-N FCFF (discount at high_growth_wacc)
        5. PV Terminal (at Year N endpoint, discount at high_growth_wacc)
        6. Firm Value = PV(explicit) + PV(terminal)
        7. Equity = Firm + Cash − Debt − Options
        8. Value/share = Equity / Shares

    NOT: Damodaran Tube Investments PDF'inde tek discount rate
    (high_growth_wacc) kullanılmış. Stable WACC sadece terminal value
    formülünde kullanılır.

    Args:
        starting_ebit_after_tax: Year 0 EBIT(1-t)
        high_growth_rate: High growth phase growth rate
        high_reinvestment_rate: High growth reinvestment rate
        high_growth_duration: Years of high growth (örn 5)
        high_growth_wacc: WACC during high growth + discount rate
        stable_growth_rate: Stable phase growth
        stable_reinvestment_rate: Stable phase reinvestment rate
        stable_wacc: Stable phase WACC (terminal value formülünde)
        cash: Cash millions (equity bridge)
        debt: Debt millions
        options_value: Employee options millions (genelde 0)
        shares_outstanding: Outstanding shares millions

    Returns:
        DCFEMResult
    """
    # 1+2) Multi-year projection
    high_projs, year_6 = project_multi_year_em(
        starting_ebit_after_tax=starting_ebit_after_tax,
        high_growth_rate=high_growth_rate,
        high_reinvestment_rate=high_reinvestment_rate,
        high_growth_duration=high_growth_duration,
        stable_growth_rate=stable_growth_rate,
        stable_reinvestment_rate=stable_reinvestment_rate,
    )

    # 3) Terminal Value
    tv = terminal_value(
        terminal_year_fcff=year_6.fcff,
        stable_growth=stable_growth_rate,
        stable_cost_of_capital=stable_wacc,
    )

    # 4) PV high growth FCFF
    pv_high_growth = sum(
        discount_to_present_value(p.fcff, high_growth_wacc, p.year)
        for p in high_projs
    )

    # 5) PV terminal value
    pv_tv = discount_to_present_value(tv, high_growth_wacc, high_growth_duration)

    # 6) Firm Value
    firm_value = pv_high_growth + pv_tv

    # 7) Equity bridge
    equity_value = firm_value + cash - debt - options_value

    # 8) Value per share
    value_per_share = equity_value / shares_outstanding

    return DCFEMResult(
        starting_ebit_after_tax=starting_ebit_after_tax,
        high_growth_wacc=high_growth_wacc,
        stable_wacc=stable_wacc,
        stable_growth=stable_growth_rate,
        high_growth_projections=high_projs,
        terminal_year_projection=year_6,
        terminal_value=tv,
        pv_high_growth_fcff=pv_high_growth,
        pv_terminal_value=pv_tv,
        firm_value=firm_value,
        cash=cash,
        debt=debt,
        options_value=options_value,
        equity_value=equity_value,
        shares_outstanding=shares_outstanding,
        value_per_share=value_per_share,
    )
