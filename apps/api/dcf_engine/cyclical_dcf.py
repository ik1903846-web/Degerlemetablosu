"""
Cyclical Company DCF — Single-Stage Stable Growth + Earnings Normalization.

Damodaran Toyota 2009 reference (darksideextended13.pdf::page 59):
- Crisis year earnings → normalize via historical avg margin
- Single-stage stable growth (no high growth phase)
- Extended equity bridge (non-op assets + minority interests)

Mevcut motorlardan FARKLI:
- Heineken/Tube: 2-stage (high growth + stable)
- Toyota:        1-stage (cyclical normalize → direct stable perpetuity)

Industrial FCFF / FCFF EM ile re-use YOK — formula yapısı farklı:
  V = Normalized_OI × (1+g) × (1-t) × (1-RR) / (WACC - g)

Bu Gordon Growth perpetuity'nin EBIT-base versiyonu.
PV chain yok çünkü explicit cash flows yok — direkt perpetuity.

Module yapısı:
- normalize_operating_income(): Revenue × historical avg margin
- single_stage_stable_growth_value(): Stable growth perpetuity formula
- equity_bridge_cyclical(): Operating + Cash + Non-op − Debt − Minority

ADR References:
- ADR-006a: Industrial DCF (cyclical variant)
- ADR-011: Cyclical company normalization (historical avg margin)
- ADR-040: Currency consistency (JPY for Toyota)
"""

from dataclasses import dataclass
from typing import List


# ============================================================================
# Cyclical Earnings Normalization
# ============================================================================

@dataclass
class NormalizationResult:
    """Cyclical normalization breakdown."""
    current_revenues: float
    current_op_margin: float
    current_op_income: float
    historical_avg_margin: float
    normalized_op_income: float
    margin_uplift: float  # normalized_margin - current_margin


def normalize_operating_income(
    current_revenues: float,
    historical_avg_margin: float,
    current_op_margin: float = None,
) -> NormalizationResult:
    """
    Cyclical company earnings normalization.

    Crisis dönemde current margin sıkışmış olabilir. Historical average
    margin (10-15 yıl) "normal" performansı temsil eder. Damodaran
    methodology (ADR-011):
        Normalized OI = Current Revenues × Historical_Avg_Margin

    Args:
        current_revenues: Latest reported revenues
        historical_avg_margin: 10-15 year average operating margin (decimal)
        current_op_margin: Current period margin (optional, for diagnostic)

    Returns:
        NormalizationResult with breakdown

    Example (Toyota 2009):
        >>> result = normalize_operating_income(
        ...     current_revenues=22661,
        ...     historical_avg_margin=0.0733,
        ...     current_op_margin=0.0118,
        ... )
        >>> result.normalized_op_income
        1660.65...  # 22661 × 0.0733
        >>> result.margin_uplift
        0.0615  # 7.33% - 1.18% = 6.15 pp uplift
    """
    normalized_oi = current_revenues * historical_avg_margin
    current_oi = current_revenues * current_op_margin if current_op_margin else 0.0
    uplift = historical_avg_margin - current_op_margin if current_op_margin else 0.0

    return NormalizationResult(
        current_revenues=current_revenues,
        current_op_margin=current_op_margin or 0.0,
        current_op_income=current_oi,
        historical_avg_margin=historical_avg_margin,
        normalized_op_income=normalized_oi,
        margin_uplift=uplift,
    )


# ============================================================================
# Single-Stage Stable Growth Value (Operating Assets)
# ============================================================================

@dataclass
class StableGrowthValueResult:
    """Single-stage stable growth valuation breakdown."""
    normalized_op_income: float
    next_year_oi: float  # OI × (1+g)
    next_year_oi_after_tax: float  # × (1-t)
    next_year_fcff: float  # × (1-RR)
    discount_rate_minus_growth: float  # WACC - g
    operating_assets_value: float


def single_stage_stable_growth_value(
    normalized_op_income: float,
    growth_rate: float,
    tax_rate: float,
    reinvestment_rate: float,
    wacc: float,
) -> StableGrowthValueResult:
    """
    Single-stage stable growth FCFF valuation.

    Formula:
        V = Normalized_OI × (1+g) × (1-t) × (1-RR) / (WACC - g)

    Adımlar:
        1. Next year OI = OI × (1+g)
        2. After-tax OI = next_year_OI × (1-t)
        3. FCFF = after_tax_OI × (1-RR)
        4. Operating Assets = FCFF / (WACC - g)

    Note: Bu Gordon Growth model'in EBIT-base versiyonu.
    Reinvestment Rate genelde stable phase için: RR = g / ROC.

    Args:
        normalized_op_income: Cyclical-adjusted operating income
        growth_rate: Stable growth (decimal)
        tax_rate: Marginal tax rate (decimal)
        reinvestment_rate: Reinvestment rate (decimal)
        wacc: Weighted Average Cost of Capital (decimal)

    Returns:
        StableGrowthValueResult with full breakdown

    Raises:
        ValueError: WACC <= growth_rate (invalid stable growth)

    Example (Toyota 2009):
        >>> result = single_stage_stable_growth_value(
        ...     normalized_op_income=1660.7,
        ...     growth_rate=0.015,
        ...     tax_rate=0.407,
        ...     reinvestment_rate=0.2946,
        ...     wacc=0.0509,
        ... )
        >>> result.operating_assets_value
        19640.x...  # PDF birebir
    """
    if wacc <= growth_rate:
        raise ValueError(
            f"WACC ({wacc}) must exceed stable growth ({growth_rate}) "
            f"for finite stable growth value"
        )

    next_year_oi = normalized_op_income * (1 + growth_rate)
    next_year_oi_after_tax = next_year_oi * (1 - tax_rate)
    next_year_fcff = next_year_oi_after_tax * (1 - reinvestment_rate)
    discount_minus_g = wacc - growth_rate
    operating_value = next_year_fcff / discount_minus_g

    return StableGrowthValueResult(
        normalized_op_income=normalized_op_income,
        next_year_oi=next_year_oi,
        next_year_oi_after_tax=next_year_oi_after_tax,
        next_year_fcff=next_year_fcff,
        discount_rate_minus_growth=discount_minus_g,
        operating_assets_value=operating_value,
    )


# ============================================================================
# Extended Equity Bridge (Cyclical / Diversified Firms)
# ============================================================================

@dataclass
class CyclicalEquityBridge:
    """Extended equity bridge for cyclical/diversified firms."""
    operating_assets: float
    cash: float
    non_operating_assets: float
    debt: float
    minority_interests: float
    options_value: float
    equity_value: float


def equity_bridge_cyclical(
    operating_assets: float,
    cash: float = 0.0,
    non_operating_assets: float = 0.0,
    debt: float = 0.0,
    minority_interests: float = 0.0,
    options_value: float = 0.0,
) -> CyclicalEquityBridge:
    """
    Extended equity bridge.

    Industrial FCFF (Heineken/Tube) bridge:
        Equity = Firm + Cash − Debt − Options

    Cyclical/Diversified bridge (Toyota):
        Equity = Operating + Cash + Non-op_Assets − Debt − Minority − Options

    Yeni eklemeler:
    - Non-operating assets: Equity investments, financial subsidiaries
    - Minority interests: Subsidiary'lerdeki %100 olmayan paylar

    Args:
        operating_assets: Value of operating assets (DCF result)
        cash: Cash and equivalents
        non_operating_assets: Equity investments + financial subs
        debt: Total debt
        minority_interests: Minority shareholders' value
        options_value: Employee options (genelde 0 for mature firms)

    Returns:
        CyclicalEquityBridge with breakdown

    Example (Toyota 2009, billion JPY):
        >>> bridge = equity_bridge_cyclical(
        ...     operating_assets=19640,
        ...     cash=2288,
        ...     non_operating_assets=6845,
        ...     debt=11862,
        ...     minority_interests=583,
        ... )
        >>> bridge.equity_value
        16328.0  # 19640 + 2288 + 6845 - 11862 - 583
    """
    equity = (
        operating_assets
        + cash
        + non_operating_assets
        - debt
        - minority_interests
        - options_value
    )

    return CyclicalEquityBridge(
        operating_assets=operating_assets,
        cash=cash,
        non_operating_assets=non_operating_assets,
        debt=debt,
        minority_interests=minority_interests,
        options_value=options_value,
        equity_value=equity,
    )


# ============================================================================
# Full Cyclical DCF Aggregator
# ============================================================================

@dataclass
class CyclicalDCFResult:
    """Full cyclical DCF valuation breakdown."""
    normalization: NormalizationResult
    operating_value: StableGrowthValueResult
    equity_bridge: CyclicalEquityBridge

    shares_outstanding: float
    value_per_share: float


def cyclical_dcf_valuation(
    current_revenues: float,
    historical_avg_margin: float,
    growth_rate: float,
    tax_rate: float,
    reinvestment_rate: float,
    wacc: float,
    cash: float,
    non_operating_assets: float,
    debt: float,
    minority_interests: float,
    shares_outstanding: float,
    options_value: float = 0.0,
    current_op_margin: float = None,
    avg_revenue: float = None,
    revenue_cap_ratio: float = 1.5,
    lifecycle_stage: str = None,
    recent_margin_bias_pct: float = None,
) -> CyclicalDCFResult:
    """
    Full cyclical company DCF: normalize → stable growth → equity bridge.

    Steps:
        1. Asymmetric revenue cap (Faz 2.6 Damodaran Lesson #2):
           effective_revenue = min(current_revenues, avg_revenue × cap_ratio)
           if avg_revenue verilirse. Trough year korunur, peak year disipline.
        2. Normalize OI (effective_revenue × historical avg margin)
        3. Compute operating value (single-stage stable growth)
        4. Equity bridge (operating + cash + non-op - debt - minority)
        5. Value/share = equity / shares

    Args:
        current_revenues: Latest reported revenues
        historical_avg_margin: 10-15 year average op margin
        growth_rate: Stable growth rate
        tax_rate: Marginal tax rate
        reinvestment_rate: Reinvestment rate (genelde g/ROC)
        wacc: Weighted Avg Cost of Capital
        cash: Cash and equivalents
        non_operating_assets: Equity investments + non-op subs
        debt: Total debt
        minority_interests: Minority value
        shares_outstanding: Outstanding shares
        options_value: Employee options (genelde 0)
        current_op_margin: Current margin (optional, diagnostic)
        avg_revenue: 16-yıl avg revenue (asymmetric cap için).
                     None ise cap inactive (backward-compat, Toyota 2009 pattern).
        revenue_cap_ratio: Revenue cap factor (default 1.5).
                           current > avg × ratio → cap kicks in.

    Returns:
        CyclicalDCFResult
    """
    # 1) Asymmetric Revenue Cap (Faz 2.6 — Damodaran Lesson #2)
    # Damodaran Toyota 2009 reference (current × avg) trough year için doğrudur.
    # Peak year için inflation yaratır; cap ile asimetrik düzeltme uygulanır.
    #
    # Faz 2.7 — Damodaran Lesson #4 (Adaptive Cap):
    # MATURE_STABLE + recent_margin_bias > %25 → cap_ratio 1.5 → 1.3
    # (defensive consumers with structural margin upshift need tighter cap)
    effective_cap_ratio = revenue_cap_ratio
    if (
        lifecycle_stage is not None
        and lifecycle_stage.upper().replace("-", "_") == "MATURE_STABLE"
        and recent_margin_bias_pct is not None
        and recent_margin_bias_pct > 25.0
    ):
        effective_cap_ratio = 1.3  # Tighter cap for defensive consumer high-bias

    if avg_revenue is not None and avg_revenue > 0:
        revenue_ceiling = avg_revenue * effective_cap_ratio
        effective_revenue = min(current_revenues, revenue_ceiling)
    else:
        effective_revenue = current_revenues  # Backward-compat (no cap)

    # 2) Normalize earnings
    norm = normalize_operating_income(
        current_revenues=effective_revenue,
        historical_avg_margin=historical_avg_margin,
        current_op_margin=current_op_margin,
    )

    # 2) Operating value
    op_value = single_stage_stable_growth_value(
        normalized_op_income=norm.normalized_op_income,
        growth_rate=growth_rate,
        tax_rate=tax_rate,
        reinvestment_rate=reinvestment_rate,
        wacc=wacc,
    )

    # 3) Equity bridge
    bridge = equity_bridge_cyclical(
        operating_assets=op_value.operating_assets_value,
        cash=cash,
        non_operating_assets=non_operating_assets,
        debt=debt,
        minority_interests=minority_interests,
        options_value=options_value,
    )

    # 4) Value per share
    value_per_share = bridge.equity_value / shares_outstanding

    return CyclicalDCFResult(
        normalization=norm,
        operating_value=op_value,
        equity_bridge=bridge,
        shares_outstanding=shares_outstanding,
        value_per_share=value_per_share,
    )
