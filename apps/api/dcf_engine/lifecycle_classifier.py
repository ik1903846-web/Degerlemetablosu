"""
Damodaran 6-Stage Corporate Lifecycle Classifier.

Reference: Damodaran "Corporate Life Cycles" (Penguin, 2024)
ADR-006d: 6-stage lifecycle framework

6 Stages:
1. Young:           No history, negative earnings, high failure prob
2. High Growth:     Rapid revenue growth, marginal profitability
3. Mature Growth:   Profitable, reinvesting heavily, ROIC > WACC
4. Mature Stable:   Stable margins, modest growth, ROIC = WACC
5. Decline:         Revenue shrinking, margins compressing
6. Distress:        Going concern risk, π_distress > 20%

Sub-classifications:
- Cyclical: Margin stdev > 5pp (Toyota 2009, TUPRS pattern)
- Capital-Intensive: Reinvestment > 15% of revenue
- Asset-Light: Reinvestment < 5% of revenue

Classifier sonucu DCF model seçimini yönlendirir:
- Stage 1-2: Young Firm DCF (Uber 9-input template)
- Stage 3-4 + Cyclical: Cyclical DCF (Toyota 2009)
- Stage 3-4 + Stable: Industrial FCFF (2-stage)
- Stage 5: Decline + liquidation blend
- Stage 6: Distress equity-as-call-option (Eurotunnel)
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict
import logging
import statistics

logger = logging.getLogger(__name__)


# ============================================================================
# Lifecycle Stages
# ============================================================================

class LifecycleStage(str, Enum):
    """Damodaran 6-stage lifecycle."""
    YOUNG = "young"
    HIGH_GROWTH = "high_growth"
    MATURE_GROWTH = "mature_growth"
    MATURE_STABLE = "mature_stable"
    DECLINE = "decline"
    DISTRESS = "distress"
    UNKNOWN = "unknown"


class SubClassification(str, Enum):
    """Lifecycle alt-sınıflandırma."""
    CYCLICAL = "cyclical"
    STABLE = "stable"
    CAPITAL_INTENSIVE = "capital_intensive"
    ASSET_LIGHT = "asset_light"
    NONE = "none"


# ============================================================================
# Classification Result
# ============================================================================

@dataclass
class LifecycleClassification:
    """Sınıflandırma sonucu + diagnostik."""
    ticker: str
    stage: LifecycleStage
    sub_classifications: List[SubClassification]

    # Metrics
    revenue_cagr_usd: Optional[float]  # 5-yıl USD CAGR
    avg_operating_margin: Optional[float]
    margin_stdev: Optional[float]
    margin_spread: Optional[float]  # max - min
    avg_reinvestment_rate: Optional[float]
    has_negative_earnings: bool
    earnings_consistency: Optional[float]  # % positive years

    # Recommended DCF model
    recommended_model: str  # "industrial_fcff" / "cyclical_dcf" / "young_firm" / etc.
    confidence: float  # 0-1 (rule strictness)

    # Reasoning
    reasoning: List[str]

    def __repr__(self):
        return (
            f"LifecycleClassification("
            f"ticker={self.ticker}, "
            f"stage={self.stage.value}, "
            f"sub={[s.value for s in self.sub_classifications]}, "
            f"model={self.recommended_model})"
        )


# ============================================================================
# Helper Calculations
# ============================================================================

def _calc_cagr(values: List[Optional[Decimal]]) -> Optional[float]:
    """
    Compound Annual Growth Rate.

    Index 0 = en yeni, index N-1 = en eski.
    CAGR = (last/first)^(1/n) - 1
    """
    valid = [(i, v) for i, v in enumerate(values) if v is not None and v > 0]
    if len(valid) < 3:
        return None

    # En yeni ve en eski (en uzak)
    newest_idx, newest_val = valid[0]
    oldest_idx, oldest_val = valid[-1]

    n_years = oldest_idx - newest_idx
    if n_years <= 0:
        return None

    try:
        ratio = float(newest_val) / float(oldest_val)
        if ratio <= 0:
            return None
        cagr = ratio ** (1 / n_years) - 1
        return cagr
    except (ValueError, ZeroDivisionError, OverflowError):
        return None


def _calc_avg(values: List[Optional[Decimal]]) -> Optional[float]:
    """Mean of non-None values."""
    valid = [float(v) for v in values if v is not None]
    if not valid:
        return None
    return sum(valid) / len(valid)


def _calc_stdev(values: List[Optional[Decimal]]) -> Optional[float]:
    """Standard deviation of non-None values."""
    valid = [float(v) for v in values if v is not None]
    if len(valid) < 2:
        return None
    return statistics.stdev(valid)


def _calc_spread(values: List[Optional[Decimal]]) -> Optional[float]:
    """Max - Min of non-None values."""
    valid = [float(v) for v in values if v is not None]
    if len(valid) < 2:
        return None
    return max(valid) - min(valid)


def _has_any_negative(values: List[Optional[Decimal]]) -> bool:
    """Check if any value is negative."""
    return any(v is not None and v < 0 for v in values)


def _earnings_consistency(values: List[Optional[Decimal]]) -> Optional[float]:
    """% of years with positive earnings."""
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    positive = sum(1 for v in valid if v > 0)
    return positive / len(valid)


# ============================================================================
# Main Classifier
# ============================================================================

def classify_lifecycle(
    inputs,  # DamodaranDCFInputs
) -> LifecycleClassification:
    """
    DamodaranDCFInputs → LifecycleClassification.

    Çok-değişkenli decision tree (ADR-006d).
    """
    reasoning = []

    # ========================================================================
    # METRICS CALCULATION
    # ========================================================================

    # Revenue CAGR (USD-bazlı, eğer USD inputs verilirse)
    revenue_cagr = _calc_cagr(inputs.revenue)

    # Margin metrics
    avg_margin = _calc_avg(inputs.operating_margin)
    margin_stdev = _calc_stdev(inputs.operating_margin)
    margin_spread = _calc_spread(inputs.operating_margin)

    # Reinvestment
    avg_reinvestment = None
    if inputs.net_capex and inputs.revenue:
        rates = []
        for nc, rev in zip(inputs.net_capex, inputs.revenue):
            if nc is not None and rev is not None and rev > 0:
                rates.append(float(nc / rev))
        avg_reinvestment = sum(rates) / len(rates) if rates else None

    # Earnings analysis
    has_neg_earnings = _has_any_negative(inputs.ebit) or _has_any_negative(inputs.net_income)
    earnings_consistency = _earnings_consistency(inputs.net_income)

    # ========================================================================
    # STAGE CLASSIFICATION (decision tree)
    # ========================================================================

    stage = LifecycleStage.UNKNOWN
    confidence = 0.5

    # Stage 6: Distress (any year with major losses + recent stress)
    if avg_margin is not None and avg_margin < -0.05:  # avg margin < -5%
        stage = LifecycleStage.DISTRESS
        confidence = 0.9
        reasoning.append(f"Distress: avg margin {avg_margin*100:.1f}% < -5%")

    # Stage 5: Decline (negative revenue growth or persistent margin compression)
    elif revenue_cagr is not None and revenue_cagr < -0.05:  # CAGR < -5%
        stage = LifecycleStage.DECLINE
        confidence = 0.85
        reasoning.append(f"Decline: revenue CAGR {revenue_cagr*100:.1f}% < -5%")

    # Stage 1: Young (very small revenue + negative earnings)
    elif (
        avg_margin is not None and avg_margin < 0
        and earnings_consistency is not None and earnings_consistency < 0.4
    ):
        stage = LifecycleStage.YOUNG
        confidence = 0.8
        reasoning.append(f"Young: avg margin {avg_margin*100:.1f}% < 0, consistency {earnings_consistency*100:.0f}%")

    # Stage 2: High Growth (revenue CAGR > 30% + marginal earnings)
    elif (
        revenue_cagr is not None and revenue_cagr > 0.30
        and avg_margin is not None and avg_margin < 0.10
    ):
        stage = LifecycleStage.HIGH_GROWTH
        confidence = 0.85
        reasoning.append(f"High Growth: CAGR {revenue_cagr*100:.1f}% > 30%, margin {avg_margin*100:.1f}% < 10%")

    # Stage 3: Mature Growth (CAGR 10-30% + positive margins + heavy capex)
    elif (
        revenue_cagr is not None and 0.10 <= revenue_cagr <= 0.30
        and avg_margin is not None and avg_margin > 0.05
    ):
        stage = LifecycleStage.MATURE_GROWTH
        confidence = 0.80
        reasoning.append(f"Mature Growth: CAGR {revenue_cagr*100:.1f}% in 10-30%, margin {avg_margin*100:.1f}% > 5%")

    # Stage 4: Mature Stable (low growth + stable margins)
    elif (
        revenue_cagr is not None and 0 <= revenue_cagr < 0.10
        and avg_margin is not None and avg_margin > 0.02
        and earnings_consistency is not None and earnings_consistency >= 0.7
    ):
        stage = LifecycleStage.MATURE_STABLE
        confidence = 0.85
        reasoning.append(f"Mature Stable: CAGR {revenue_cagr*100:.1f}% < 10%, margin {avg_margin*100:.1f}% > 2%, consistency {earnings_consistency*100:.0f}%")

    # Default fallback (mid-range characteristics)
    else:
        # Catch-all: mature growth or stable
        if revenue_cagr is not None and revenue_cagr > 0.05:
            stage = LifecycleStage.MATURE_GROWTH
            confidence = 0.5
            reasoning.append(f"Default Mature Growth (mid-range): CAGR {revenue_cagr*100:.1f}%")
        else:
            stage = LifecycleStage.MATURE_STABLE
            confidence = 0.5
            reasoning.append(f"Default Mature Stable (low growth)")

    # ========================================================================
    # SUB-CLASSIFICATION
    # ========================================================================

    sub_classifications = []

    # Cyclical detection
    if margin_spread is not None and margin_spread > 0.05:  # > 5pp spread
        sub_classifications.append(SubClassification.CYCLICAL)
        reasoning.append(f"Cyclical: margin spread {margin_spread*100:.2f}pp > 5pp")
    elif margin_stdev is not None and margin_stdev > 0.03:  # > 3pp stdev
        sub_classifications.append(SubClassification.CYCLICAL)
        reasoning.append(f"Cyclical: margin stdev {margin_stdev*100:.2f}pp > 3pp")
    else:
        sub_classifications.append(SubClassification.STABLE)

    # Capital intensity
    if avg_reinvestment is not None:
        if avg_reinvestment > 0.15:
            sub_classifications.append(SubClassification.CAPITAL_INTENSIVE)
            reasoning.append(f"Capital-Intensive: reinvestment {avg_reinvestment*100:.1f}% > 15%")
        elif avg_reinvestment < 0.05:
            sub_classifications.append(SubClassification.ASSET_LIGHT)
            reasoning.append(f"Asset-Light: reinvestment {avg_reinvestment*100:.1f}% < 5%")

    # ========================================================================
    # RECOMMENDED DCF MODEL
    # ========================================================================

    if stage == LifecycleStage.YOUNG:
        recommended_model = "young_firm_dcf"  # Uber 9-input
    elif stage == LifecycleStage.HIGH_GROWTH:
        recommended_model = "young_firm_dcf"  # Uber template + early profitability
    elif stage == LifecycleStage.MATURE_GROWTH:
        if SubClassification.CYCLICAL in sub_classifications:
            recommended_model = "cyclical_dcf"
        else:
            recommended_model = "industrial_fcff"
    elif stage == LifecycleStage.MATURE_STABLE:
        if SubClassification.CYCLICAL in sub_classifications:
            recommended_model = "cyclical_dcf"  # Toyota 2009 pattern
        else:
            recommended_model = "industrial_fcff"  # 2-stage
    elif stage == LifecycleStage.DECLINE:
        recommended_model = "decline_dcf"  # DCF + liquidation blend
    elif stage == LifecycleStage.DISTRESS:
        recommended_model = "distress_dcf"  # equity as call option
    else:
        recommended_model = "industrial_fcff"  # default fallback

    return LifecycleClassification(
        ticker=inputs.ticker,
        stage=stage,
        sub_classifications=sub_classifications,
        revenue_cagr_usd=revenue_cagr,
        avg_operating_margin=avg_margin,
        margin_stdev=margin_stdev,
        margin_spread=margin_spread,
        avg_reinvestment_rate=avg_reinvestment,
        has_negative_earnings=has_neg_earnings,
        earnings_consistency=earnings_consistency,
        recommended_model=recommended_model,
        confidence=confidence,
        reasoning=reasoning,
    )
