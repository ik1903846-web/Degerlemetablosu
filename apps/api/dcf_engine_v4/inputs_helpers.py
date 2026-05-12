"""Engine A ProjectionInputs builder helpers (Phase 4a).

Damodaran-style input computations from TickerDataV4
(KAP + yfinance + Damodaran parameters).

ADR-080 Section 3 Adim 1.
"""

from typing import Optional


def compute_sales_to_capital(
    revenue: Optional[float],
    total_assets: Optional[float],
    cash: Optional[float],
) -> Optional[float]:
    """Damodaran sales-to-capital ratio.

    invested_capital = total_assets - excess_cash
    excess_cash       = max(0, cash - operating_cash_need)
    operating_cash_need = revenue * 2% (Damodaran heuristic, opcash)

    Returns None if inputs missing or invalid.

    Reference: Damodaran "Investment Valuation" Ch.10 reinvestment formula
      reinvestment_y = dRevenue_y / sales_to_capital

    Heineken validation case: 0.79 (5y avg) reference.
    """
    if not revenue or not total_assets:
        return None
    if revenue <= 0 or total_assets <= 0:
        return None

    operating_cash_need = revenue * 0.02
    excess_cash = max(0.0, (cash or 0.0) - operating_cash_need)
    invested_capital = total_assets - excess_cash

    if invested_capital <= 0:
        return None

    return revenue / invested_capital


def compute_explicit_growth_rate(
    revenue_current: Optional[float],
    revenue_previous: Optional[float],
    lifecycle_stage: Optional[str] = None,
) -> Optional[float]:
    """Phase 4a Adim 2: Composite explicit_growth_rate (Damodaran).

    Composite formula:
        raw_growth = (revenue_current / revenue_previous) - 1
        bounded    = clamp(raw_growth, lifecycle_min, lifecycle_max)

    Fallback chain:
        Tier 1: KAP 2y growth clamped to lifecycle bound
        Tier 2: lifecycle_default (KAP data missing)

    Damodaran "Act Your Age" framework alignment.

    ADR-080 v2 doctrine: 5y CAGR yerine composite (yfinance 4y data
    eksik + TRY currency mismatch + KAP Excel 2 period limit).

    Args:
        revenue_current:  KAP cari period revenue (TickerDataV4.revenue)
        revenue_previous: KAP onceki period revenue (yeni transfer Adim 5'te)
        lifecycle_stage:  TickerDataV4.lifecycle_stage

    Returns:
        Composite explicit growth rate (decimal, e.g. 0.10 = 10%) or
        lifecycle_default if KAP data missing.
    """
    from dcf_engine.lifecycle_classifier import get_lifecycle_defaults

    config = get_lifecycle_defaults(lifecycle_stage)
    growth_min = config["growth_min"]
    growth_max = config["growth_max"]
    growth_default = config["growth_default"]

    if revenue_current and revenue_previous and revenue_previous > 0:
        raw_growth = (revenue_current / revenue_previous) - 1.0
        return max(growth_min, min(growth_max, raw_growth))

    return growth_default


def compute_taper_config(lifecycle_stage: Optional[str] = None) -> dict:
    """Phase 4a Adim 4: Damodaran 'Act Your Age' taper config builder.

    Returns ProjectionInputs taper fields (Engine A industrial_fcff):
      margin_taper_start_year, margin_taper_end_year (lifecycle-aware)
      tax_taper_start_year, tax_taper_end_year (5/10 Damodaran convention)
      explicit_period_years (5 mature, 10 growth)
      transition_period_years (5 Damodaran default)

    Damodaran convention (Heineken/ABN PASS pattern):
      tax_taper Year 5-10 (her ticker icin sabit, country tax convergence)
      margin_taper Year-N..10 (lifecycle stage'e gore N degisir)

    Unknown stage -> mature_stable conservative.
    """
    from dcf_engine.lifecycle_classifier import get_lifecycle_defaults

    config = get_lifecycle_defaults(lifecycle_stage)

    return {
        "margin_taper_start_year": int(config["margin_taper_start"]),
        "margin_taper_end_year": int(config["margin_taper_end"]),
        # Damodaran tax_taper convention (country tax converge Y5-Y10)
        "tax_taper_start_year": 5,
        "tax_taper_end_year": 10,
        "explicit_period_years": int(config["explicit_period_years"]),
        "transition_period_years": int(config["transition_period_years"]),
    }


def compute_non_operating_assets(
    financial_investments: Optional[float],
    investment_properties: Optional[float],
    equity_method_investments: Optional[float],
) -> float:
    """Phase 4a Adim 5: Damodaran non_operating_assets aggregate.

    Damodaran formal equity bridge convention:
      non_op_assets = financial_investments
                    + investment_properties (Phase 3a)
                    + equity_method_investments (Phase 3a)

    Equity bridge (Engine A industrial_fcff dcf_valuation):
      equity = operating_value - debt - minority + cash + non_op_assets

    Graceful degradation: None inputs -> 0.0.
    """
    total = 0.0
    total += financial_investments or 0.0
    total += investment_properties or 0.0
    total += equity_method_investments or 0.0
    return total
