"""
Distress Valuation — Damodaran Dark Side: Equity as a Call Option.

Faz 7 — Black-Scholes equity-as-call + πDistress 3-method + distress-adjusted blend.

Reference:
- Damodaran "The Dark Side of Valuation" (Eurotunnel 1998 £122M, LVS 2009 $1.92)
- Damodaran ADR-029 (distress probability), ADR-030 (Black-Scholes equity)

Methodology:
1. Black-Scholes equity-as-call: Equity = S*N(d1) - K*e^(-rt)*N(d2)
   - S = firm value (total assets at market)
   - K = debt face value
   - t = debt weighted average duration
   - σ = firm value volatility (proxy: stock historical vol annualized)
   - r = risk-free rate

2. πDistress 3-method (rating + Z-score + interest coverage):
   - Floor 5%, cap 95%

3. Distress-adjusted value (going concern + sale blend):
   - Going concern × (1 - π) + DistressSale × π
   - DistressSale ≈ book × 0.6 (conservative liquidation)
   - Deep distress (π > 50%): BS only

NOT: scipy mevcut değil — math.erf ile norm.cdf alternatif kullanılır.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional


# ============================================================================
# Math Helpers (no scipy)
# ============================================================================

def norm_cdf(x: float) -> float:
    """Standard normal CDF via math.erf (no scipy dependency)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


# ============================================================================
# DataClasses
# ============================================================================

@dataclass
class BlackScholesResult:
    """Black-Scholes equity-as-call output."""
    equity_value: float
    d1: Optional[float]
    d2: Optional[float]
    n_d1: Optional[float]
    n_d2: Optional[float]
    method: str  # "black_scholes" | "fallback_book"


@dataclass
class DistressProbability:
    """πDistress 3-method estimation."""
    pi_distress: float
    method_1_rating: float
    method_2_zscore: Optional[float]
    method_3_coverage: Optional[float]
    methods_used: int
    notes: str = ""


@dataclass
class DistressValuation:
    """Full distress valuation pipeline output."""
    ticker: str
    intrinsic_equity_value: float
    black_scholes_value: float
    distress_sale_value: float
    pi_distress: float
    method: str  # "black_scholes_deep_distress" | "distress_adjusted_blend"
    bs_breakdown: BlackScholesResult
    pi_breakdown: DistressProbability


# ============================================================================
# Black-Scholes Equity-as-Call
# ============================================================================

def black_scholes_equity_with_yield(
    firm_value: float,        # S — total firm value (assets at market)
    debt_face_value: float,   # K — strike (debt face)
    duration: float,          # t — debt weighted avg duration (years)
    volatility: float,        # σ — annualized firm value volatility
    risk_free_rate: float,    # r — risk-free rate
    cashflow_yield: float = 0.0,  # y — Damodaran Faz 7.2 (asset payout/dividend yield)
) -> BlackScholesResult:
    """
    Damodaran Dark Side: Equity as a call option with cashflow yield (modified BS).

    Modified Formula (y > 0, cashflow yield reduces equity time value):
        Equity = S * exp(-y*t) * N(d1) - K * exp(-r*t) * N(d2)

        d1 = (ln(S/K) + (r - y + σ²/2) * t) / (σ * √t)
        d2 = d1 - σ * √t

    Vanilla case (y = 0):
        Equity = S * N(d1) - K * exp(-r*t) * N(d2)
        d1 = (ln(S/K) + (r + σ²/2) * t) / (σ * √t)

    Cashflow yield (y) Damodaran Eurotunnel reference:
        - y captures asset payout (dividends, asset sale, debt service) consuming
          firm value over option life. Long-duration distress firms with
          significant cash burn → y materially reduces equity option value.
        - Eurotunnel 1998: y ≈ 11.70% calibrates equity to £122M anchor
          (vs vanilla BS y=0 £5,570M overestimate, 25-yıl duration sensitive).
        - BIST distress ticker'larında y ≈ 0 (asset payout minimal pre-distress).

    Edge cases:
        - Invalid inputs (≤0): fallback to max(0, S - K) book floor
        - Deep underwater (S << K): equity ≈ 0 (option far OTM)
        - Deep ITM (S >> K, y=0): equity ≈ S - K * e^(-rt)
    """
    if (
        firm_value <= 0
        or debt_face_value <= 0
        or duration <= 0
        or volatility <= 0
    ):
        return BlackScholesResult(
            equity_value=max(0.0, firm_value - debt_face_value),
            d1=None, d2=None, n_d1=None, n_d2=None,
            method="fallback_book",
        )

    sigma_sqrt_t = volatility * math.sqrt(duration)

    d1 = (
        math.log(firm_value / debt_face_value)
        + (risk_free_rate - cashflow_yield + 0.5 * volatility ** 2) * duration
    ) / sigma_sqrt_t

    d2 = d1 - sigma_sqrt_t

    n_d1 = norm_cdf(d1)
    n_d2 = norm_cdf(d2)

    equity_value = (
        firm_value * math.exp(-cashflow_yield * duration) * n_d1
        - debt_face_value * math.exp(-risk_free_rate * duration) * n_d2
    )

    method_label = (
        "black_scholes_with_yield" if cashflow_yield > 0 else "black_scholes"
    )

    return BlackScholesResult(
        equity_value=equity_value,
        d1=d1, d2=d2,
        n_d1=n_d1, n_d2=n_d2,
        method=method_label,
    )


def black_scholes_equity_as_call(
    firm_value: float,
    debt_face_value: float,
    duration: float,
    volatility: float,
    risk_free_rate: float,
) -> BlackScholesResult:
    """
    Vanilla Black-Scholes equity-as-call (backward compat alias, y=0).

    Faz 7.2'de modified BS (`black_scholes_equity_with_yield`) tanıtıldı,
    bu fonksiyon vanilla case'i koruyor (mevcut çağrılar değişmez).
    """
    return black_scholes_equity_with_yield(
        firm_value=firm_value,
        debt_face_value=debt_face_value,
        duration=duration,
        volatility=volatility,
        risk_free_rate=risk_free_rate,
        cashflow_yield=0.0,
    )


# ============================================================================
# πDistress Estimation (3-method)
# ============================================================================

# Damodaran rating-based default spread (10-year cumulative)
_RATING_PI = {
    "AAA":  0.001,  "AA+":  0.003, "AA":  0.005, "AA-": 0.007,
    "A+":   0.008,  "A":    0.010, "A-":  0.015,
    "BBB+": 0.020,  "BBB":  0.025, "BBB-":0.040,
    "BB+":  0.060,  "BB":   0.075, "BB-": 0.100,
    "B+":   0.150,  "B":    0.200, "B-":  0.275,
    "CCC+": 0.350,  "CCC":  0.400, "CCC-":0.500,
    "CC":   0.600,  "C":    0.800, "D":   1.000,
}


def estimate_distress_probability(
    rating: Optional[str] = None,
    z_score: Optional[float] = None,
    interest_coverage: Optional[float] = None,
    fallback_pi: float = 0.30,
) -> DistressProbability:
    """
    πDistress 3-method estimation:
    1. Rating-based default spread (Damodaran table)
    2. Altman Z-score brackets
    3. Interest coverage ratio brackets

    Average available methods, floor 5%, cap 95%.
    """
    # Method 1: Rating
    if rating and rating.upper() in _RATING_PI:
        pi_rating = _RATING_PI[rating.upper()]
    else:
        pi_rating = fallback_pi  # unrated default

    # Method 2: Altman Z-score
    pi_z: Optional[float] = None
    if z_score is not None:
        if z_score > 3.0:
            pi_z = 0.05
        elif z_score > 1.8:
            pi_z = 0.20
        elif z_score > 1.0:
            pi_z = 0.40
        else:
            pi_z = 0.60

    # Method 3: Interest coverage
    pi_ic: Optional[float] = None
    if interest_coverage is not None:
        if interest_coverage > 5.0:
            pi_ic = 0.05
        elif interest_coverage > 2.0:
            pi_ic = 0.15
        elif interest_coverage > 1.0:
            pi_ic = 0.40
        elif interest_coverage > 0:
            pi_ic = 0.60
        else:
            pi_ic = 0.80

    available = [p for p in [pi_rating, pi_z, pi_ic] if p is not None]
    pi_avg = sum(available) / len(available) if available else fallback_pi

    pi_final = max(0.05, min(0.95, pi_avg))

    notes_parts = [f"rating={pi_rating:.3f}"]
    if pi_z is not None:
        notes_parts.append(f"z_score={pi_z:.2f}")
    if pi_ic is not None:
        notes_parts.append(f"int_cov={pi_ic:.2f}")
    notes_parts.append(f"avg={pi_avg:.3f}")

    return DistressProbability(
        pi_distress=pi_final,
        method_1_rating=pi_rating,
        method_2_zscore=pi_z,
        method_3_coverage=pi_ic,
        methods_used=len(available),
        notes=" | ".join(notes_parts),
    )


# ============================================================================
# Distress-Adjusted Value (Blend)
# ============================================================================

def distress_adjusted_value(
    going_concern_value: float,
    distress_sale_value: float,
    pi_distress: float,
) -> float:
    """
    Damodaran distress-adjusted value:
        Value = GoingConcern × (1 − π) + DistressSale × π

    DistressSale typically book × 0.5-0.7 (conservative liquidation).
    """
    pi = max(0.0, min(1.0, pi_distress))
    return going_concern_value * (1 - pi) + distress_sale_value * pi


# ============================================================================
# Full Pipeline
# ============================================================================

def value_distressed_company(
    ticker: str,
    firm_value: float,
    debt_face_value: float,
    duration: float,
    volatility: float,
    risk_free_rate: float,
    book_value: float,
    rating: Optional[str] = None,
    z_score: Optional[float] = None,
    interest_coverage: Optional[float] = None,
    distress_sale_recovery: float = 0.6,
    deep_distress_threshold: float = 0.50,
    cashflow_yield: float = 0.0,  # Faz 7.2: modified BS y param (default 0 = vanilla)
) -> DistressValuation:
    """
    Full distress valuation pipeline (Damodaran Dark Side).

    Step 1: Black-Scholes equity-as-call (going concern proxy under distress)
    Step 2: πDistress 3-method estimation
    Step 3: Distress-adjusted value:
        - Deep distress (π > threshold): BS only
        - Otherwise: BS × (1-π) + DistressSale × π

    Args:
        ticker: Identifier
        firm_value: S (total firm value, assets at market)
        debt_face_value: K (total debt face)
        duration: t (debt weighted avg duration in years)
        volatility: σ (annualized firm volatility, stock vol proxy)
        risk_free_rate: r (decimal, e.g., 0.04 for 4%)
        book_value: distress sale baseline
        rating: credit rating (optional, default 30% pi)
        z_score: Altman Z-score (optional)
        interest_coverage: EBIT / Interest (optional)
        distress_sale_recovery: Liquidation recovery rate (default 0.6)
        deep_distress_threshold: π threshold for BS-only (default 0.50)

    Returns:
        DistressValuation with intrinsic_equity_value (positive or zero).
    """
    # Step 1: Black-Scholes equity as call (Faz 7.2: modified BS with yield)
    bs = black_scholes_equity_with_yield(
        firm_value=firm_value,
        debt_face_value=debt_face_value,
        duration=duration,
        volatility=volatility,
        risk_free_rate=risk_free_rate,
        cashflow_yield=cashflow_yield,
    )

    # Step 2: πDistress
    pi_result = estimate_distress_probability(
        rating=rating,
        z_score=z_score,
        interest_coverage=interest_coverage,
    )
    pi = pi_result.pi_distress

    # Step 3: Distress-adjusted blend
    distress_sale = max(0.0, book_value * distress_sale_recovery)

    if pi >= deep_distress_threshold:
        # Deep distress: BS captures option value, sale floor implicit
        intrinsic = bs.equity_value
        method = "black_scholes_deep_distress"
    else:
        # Going concern blend
        intrinsic = distress_adjusted_value(
            going_concern_value=bs.equity_value,
            distress_sale_value=distress_sale,
            pi_distress=pi,
        )
        method = "distress_adjusted_blend"

    return DistressValuation(
        ticker=ticker,
        intrinsic_equity_value=max(0.0, intrinsic),
        black_scholes_value=bs.equity_value,
        distress_sale_value=distress_sale,
        pi_distress=pi,
        method=method,
        bs_breakdown=bs,
        pi_breakdown=pi_result,
    )


# ============================================================================
# Diagnostic Helpers
# ============================================================================

def format_distress_report(val: DistressValuation) -> str:
    """Insan-okur distress valuation raporu."""
    lines = []
    lines.append(f"DISTRESS VALUATION — {val.ticker}")
    lines.append(f"  Method: {val.method}")
    lines.append(f"  Black-Scholes equity: ${val.black_scholes_value/1e6:,.1f}M")
    lines.append(f"  Distress sale value:  ${val.distress_sale_value/1e6:,.1f}M")
    lines.append(f"  πDistress: {val.pi_distress*100:.1f}%  ({val.pi_breakdown.notes})")
    lines.append(f"  Intrinsic equity:     ${val.intrinsic_equity_value/1e6:,.1f}M")
    bs = val.bs_breakdown
    if bs.method == "black_scholes":
        lines.append(f"  BS d1={bs.d1:.3f}, N(d1)={bs.n_d1:.4f}")
        lines.append(f"  BS d2={bs.d2:.3f}, N(d2)={bs.n_d2:.4f}")
    return "\n".join(lines)
