"""
Industrial FCFF 2-stage DCF model (ADR-006a/b).

Damodaran Heineken 2019 reference:
- Years 1-5: Stable explicit growth (örn 3.22%)
- Years 6-10: Linear taper to terminal growth
- Year 10+: Stable growth perpetuity (terminal value)

Formulas:
- FCFF = EBIT × (1 - tax) - Reinvestment
- Reinvestment = ΔRevenue / Sales-to-Capital
- Terminal Value = FCFF_terminal / (Cost of Capital - Stable Growth)
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================================
# Helpers
# ============================================================================

def linear_taper(
    start_value: float,
    end_value: float,
    current_year: int,
    start_year: int,
    end_year: int,
) -> float:
    """
    Linear interpolation between two values across years.

    Damodaran Heineken Year 6-10 pattern:
        Tax rate Year 6 = 28.76%
        Tax rate Year 10 = 25.00%
        Linear: between Year 5 (29.70%) and Year 10 (25.00%)

    Args:
        start_value: Value at start_year (örn 0.2970)
        end_value: Value at end_year (örn 0.2500)
        current_year: Year for which to compute
        start_year: First year of taper (örn 5)
        end_year: Last year of taper (örn 10)

    Returns:
        Interpolated value

    Example:
        >>> linear_taper(0.2970, 0.2500, 6, 5, 10)
        0.2876
        >>> linear_taper(0.2970, 0.2500, 10, 5, 10)
        0.2500
    """
    if current_year <= start_year:
        return start_value
    if current_year >= end_year:
        return end_value

    progress = (current_year - start_year) / (end_year - start_year)
    return start_value + (end_value - start_value) * progress


# ============================================================================
# Single Year Projection
# ============================================================================

@dataclass
class YearProjection:
    """1 yıllık FCFF projection sonuç."""
    year: int
    revenue_growth: float
    revenues: float
    ebit_margin: float
    ebit: float
    tax_rate: float
    ebit_after_tax: float
    reinvestment: float
    fcff: float


def project_year(
    year: int,
    prev_revenues: float,
    revenue_growth: float,
    ebit_margin: float,
    tax_rate: float,
    sales_to_capital: float,
) -> YearProjection:
    """
    Tek yıllık FCFF projection.

    Steps:
        1. Revenues = prev × (1 + growth)
        2. EBIT = Revenues × margin
        3. EBIT(1-t) = EBIT × (1 - tax)
        4. Reinvestment = ΔRevenue / Sales-to-Capital
        5. FCFF = EBIT(1-t) - Reinvestment

    Args:
        year: Year index (1, 2, ...)
        prev_revenues: Previous year revenues
        revenue_growth: Growth rate this year (decimal)
        ebit_margin: Operating margin this year
        tax_rate: Effective tax rate this year
        sales_to_capital: Sales / Invested Capital ratio

    Returns:
        YearProjection with all intermediate values

    Example (Heineken Year 1):
        >>> r = project_year(1, 23119, 0.0322, 0.1438, 0.2970, 0.79)
        >>> r.revenues
        23863.4...
        >>> r.fcff
        1471.3...
    """
    revenues = prev_revenues * (1 + revenue_growth)
    revenue_change = revenues - prev_revenues

    ebit = revenues * ebit_margin
    ebit_after_tax = ebit * (1 - tax_rate)

    # Reinvestment (capital expenditure to support growth)
    if sales_to_capital > 0:
        reinvestment = revenue_change / sales_to_capital
    else:
        reinvestment = 0.0

    fcff = ebit_after_tax - reinvestment

    return YearProjection(
        year=year,
        revenue_growth=revenue_growth,
        revenues=revenues,
        ebit_margin=ebit_margin,
        ebit=ebit,
        tax_rate=tax_rate,
        ebit_after_tax=ebit_after_tax,
        reinvestment=reinvestment,
        fcff=fcff,
    )


# ============================================================================
# Multi-Year Projection (10-Year)
# ============================================================================

@dataclass
class ProjectionInputs:
    """10-yıl projection için input parametreleri."""
    # Starting state
    starting_revenues: float          # Year 0 (LTM) revenues
    sales_to_capital: float           # Stable boyunca

    # Margin trajectory
    starting_ebit_margin: float       # Year 1 starting margin
    terminal_ebit_margin: float       # Year 10 ending margin
    margin_taper_start_year: int      # Year 1 (default)
    margin_taper_end_year: int        # Year 10 (default)

    # Tax trajectory
    starting_tax_rate: float          # Year 1 starting tax
    terminal_tax_rate: float          # Year 10 ending tax
    tax_taper_start_year: int         # Year 5 (Damodaran Heineken)
    tax_taper_end_year: int           # Year 10

    # Growth trajectory
    explicit_growth_rate: float       # Year 1-5 sabit growth
    terminal_growth_rate: float       # Year 10+ stable growth
    explicit_period_years: int        # 5 (Damodaran)
    transition_period_years: int      # 5 (Year 6-10 linear taper)


def project_multi_year(
    inputs: ProjectionInputs,
    total_years: int = 10,
) -> List[YearProjection]:
    """
    10-yıl FCFF projection (3-stage: explicit / transition / pre-terminal).

    Damodaran Heineken pattern:
    - Year 1-5: Sabit growth (3.22%)
    - Year 6-10: Linear growth taper (3.22% → -0.5%)
    - EBIT margin Year 1-10: linear taper (14.38% → 14.00%)
    - Tax rate Year 5-10: linear taper (29.70% → 25.00%)

    Args:
        inputs: ProjectionInputs dataclass
        total_years: Default 10

    Returns:
        List of YearProjection (10 items)
    """
    projections = []
    prev_revenues = inputs.starting_revenues

    explicit_end = inputs.explicit_period_years  # 5

    # Margin: Year 1 starting → Year 10 terminal (linear)
    # Special case: Damodaran starts margin taper at Year 1

    # NOT: Damodaran Heineken Year 1 margin = 14.38% (NOT LTM 14.86%)
    # Yani margin taper Year 0 (LTM) → Year 10 olmalı
    # Year 1: 14.38% (LTM 14.86%'dan zaten 1 yıl taper edilmiş)
    # Year 10: 14.00%

    for year in range(1, total_years + 1):
        # 1) Revenue growth — explicit / transition
        if year <= explicit_end:
            growth = inputs.explicit_growth_rate
        else:
            # Year 6+: linear taper from explicit_growth → terminal_growth
            growth = linear_taper(
                start_value=inputs.explicit_growth_rate,
                end_value=inputs.terminal_growth_rate,
                current_year=year,
                start_year=explicit_end,
                end_year=total_years,
            )

        # 2) EBIT margin — linear taper Year 1 → Year 10
        ebit_margin = linear_taper(
            start_value=inputs.starting_ebit_margin,
            end_value=inputs.terminal_ebit_margin,
            current_year=year,
            start_year=inputs.margin_taper_start_year,
            end_year=inputs.margin_taper_end_year,
        )

        # 3) Tax rate — linear taper Year 5 → Year 10
        tax_rate = linear_taper(
            start_value=inputs.starting_tax_rate,
            end_value=inputs.terminal_tax_rate,
            current_year=year,
            start_year=inputs.tax_taper_start_year,
            end_year=inputs.tax_taper_end_year,
        )

        # 4) Project this year
        projection = project_year(
            year=year,
            prev_revenues=prev_revenues,
            revenue_growth=growth,
            ebit_margin=ebit_margin,
            tax_rate=tax_rate,
            sales_to_capital=inputs.sales_to_capital,
        )

        projections.append(projection)
        prev_revenues = projection.revenues

    return projections


# ============================================================================
# Terminal Value
# ============================================================================

def terminal_value(
    terminal_year_fcff: float,
    stable_growth: float,
    stable_cost_of_capital: float,
) -> float:
    """
    Gordon Growth Model (perpetuity).

    TV = FCFF_terminal / (Cost_of_Capital - Stable_Growth)

    Heineken 2019:
        FCFF_terminal = €3,269M (Year 11 = Year 10 stable phase)
        Stable cost of capital = 5%
        Stable growth = -0.5%
        TV = 3269 / (0.05 - (-0.005)) = 3269 / 0.055 = €59,436M

    Damodaran Heineken Year 10 EBIT(1-t) = €2,987M
    Year 10 ile Year 11 arası reinvestment formülü değişir:
        Year 11 reinvestment = -10% × EBIT(1-t) = -297M (disinvestment)
        Year 11 FCFF = 2972 - (-297) = 3269

    Args:
        terminal_year_fcff: FCFF terminal year (perpetual)
        stable_growth: Stable phase growth (decimal)
        stable_cost_of_capital: Stable phase WACC

    Returns:
        Terminal value (millions)
    """
    if stable_cost_of_capital <= stable_growth:
        raise ValueError(
            f"Cost of capital ({stable_cost_of_capital}) must exceed "
            f"stable growth ({stable_growth}) for finite terminal value"
        )

    return terminal_year_fcff / (stable_cost_of_capital - stable_growth)


# ============================================================================
# Present Value Discounting
# ============================================================================

def discount_to_present_value(
    cash_flow: float,
    cost_of_capital: float,
    year: int,
) -> float:
    """
    PV = CF / (1 + WACC)^year

    Args:
        cash_flow: Future cash flow (millions)
        cost_of_capital: WACC (decimal)
        year: Year offset (1, 2, ..., 10)

    Returns:
        Present value
    """
    discount_factor = (1 + cost_of_capital) ** year
    return cash_flow / discount_factor


@dataclass
class DCFResult:
    """DCF değerleme sonuçları (full breakdown)."""
    # Inputs özet
    starting_revenues: float
    wacc: float
    stable_growth: float

    # Yıllık projection
    yearly_projections: List[YearProjection]

    # Terminal
    terminal_year_fcff: float  # Year 11 (stable phase 1. yıl)
    terminal_value: float

    # Present Values
    pv_explicit_cash_flows: float    # Year 1-10 PV toplam
    pv_terminal_value: float

    # Operating value
    operating_assets_value: float    # PV explicit + PV terminal

    # Equity bridge
    debt: float
    minority_interests: float
    cash: float
    non_operating_assets: float
    equity_value: float

    # Per share
    shares_outstanding: float
    value_per_share: float


def dcf_valuation(
    projections: List[YearProjection],
    wacc: float,
    stable_cost_of_capital: float,
    stable_growth: float,
    stable_reinvestment_rate: float,
    debt: float,
    minority_interests: float,
    cash: float,
    non_operating_assets: float,
    shares_outstanding: float,
) -> DCFResult:
    """
    Complete DCF valuation: explicit projections + terminal + bridge.

    Steps:
        1. Compute Year 11 (terminal) FCFF
           - EBIT(1-t)_Y11 = Year 10 EBIT(1-t) × (1 + stable_growth)
           - Reinvestment_Y11 = EBIT(1-t)_Y11 × stable_reinvestment_rate
           - FCFF_Y11 = EBIT(1-t)_Y11 - Reinvestment_Y11
        2. Terminal Value = FCFF_Y11 / (stable_coc - stable_growth)
        3. Discount Year 1-10 FCFFs to PV (using WACC)
        4. Discount Terminal Value to PV (Year 10 endpoint)
        5. Operating value = PV(explicit) + PV(terminal)
        6. Equity = Operating - Debt - Minority + Cash + Non-op
        7. Value/share = Equity / Shares
    """
    # Year 10 sonucu
    year_10 = projections[-1]

    # Year 11 (terminal phase 1. yıl)
    terminal_revenue = year_10.revenues * (1 + stable_growth)
    terminal_ebit_margin = year_10.ebit_margin  # Stable phase'de margin sabit
    terminal_tax_rate = year_10.tax_rate
    terminal_ebit_at = terminal_revenue * terminal_ebit_margin * (1 - terminal_tax_rate)

    # Stable reinvestment = stable_growth / stable_roc
    # Heineken: reinvestment_rate = -10% (disinvestment)
    terminal_reinvestment = terminal_ebit_at * stable_reinvestment_rate
    terminal_fcff = terminal_ebit_at - terminal_reinvestment

    # Terminal Value
    tv = terminal_value(
        terminal_year_fcff=terminal_fcff,
        stable_growth=stable_growth,
        stable_cost_of_capital=stable_cost_of_capital,
    )

    # PV explicit cash flows
    pv_explicit = sum(
        discount_to_present_value(p.fcff, wacc, p.year)
        for p in projections
    )

    # PV terminal value (Year 10 endpoint, discount 10 years)
    pv_terminal = discount_to_present_value(tv, wacc, len(projections))

    # Operating assets
    operating_value = pv_explicit + pv_terminal

    # Equity bridge
    equity_value = operating_value - debt - minority_interests + cash + non_operating_assets

    # Per share
    value_per_share = equity_value / shares_outstanding

    return DCFResult(
        starting_revenues=projections[0].revenues / (1 + projections[0].revenue_growth),
        wacc=wacc,
        stable_growth=stable_growth,
        yearly_projections=projections,
        terminal_year_fcff=terminal_fcff,
        terminal_value=tv,
        pv_explicit_cash_flows=pv_explicit,
        pv_terminal_value=pv_terminal,
        operating_assets_value=operating_value,
        debt=debt,
        minority_interests=minority_interests,
        cash=cash,
        non_operating_assets=non_operating_assets,
        equity_value=equity_value,
        shares_outstanding=shares_outstanding,
        value_per_share=value_per_share,
    )
