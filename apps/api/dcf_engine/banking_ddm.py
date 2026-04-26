"""
Banking Dividend Discount Model (DDM) — 2-stage.

ADR-009: Banking firm valuation YASAK (equity-only zorunlu)
ADR-012: Banking 3-model — DDM (Damodaran ABN Amro reference)

DDM mantığı (Industrial FCFF'den ÇOK DAHA BASİT):
- Revenue/EBIT/margin yok (EPS-based)
- Reinvestment yok (sadece retention ratio)
- Tax complexity yok (zaten net income hesaplı)

Formula:
    DPS_t = EPS_0 × (1 + g)^t × payout
    Terminal Value = DPS_terminal / (Cost_of_Equity_stable - g_stable)
    Value = Σ PV(DPS_t, t=1..N) + PV(Terminal Value)
"""

from dataclasses import dataclass
from typing import List

# Industrial FCFF'den re-use
from .industrial_fcff import discount_to_present_value


# ============================================================================
# High Growth DPS Projection
# ============================================================================

@dataclass
class DPSProjection:
    """Tek yıllık DPS projection."""
    year: int
    eps: float
    dps: float


def project_dps_high_growth(
    starting_eps: float,
    growth_rate: float,
    payout_ratio: float,
    duration_years: int,
) -> List[DPSProjection]:
    """
    High growth phase DPS projection.

    EPS_t = EPS_0 × (1 + g)^t
    DPS_t = EPS_t × payout

    Args:
        starting_eps: Year 0 EPS
        growth_rate: High growth rate (decimal)
        payout_ratio: Dividend payout (decimal)
        duration_years: High growth period (örn 5)

    Returns:
        List of DPSProjection for years 1..duration_years

    Example (ABN Amro):
        >>> projs = project_dps_high_growth(1.60, 0.0973, 0.375, 5)
        >>> [p.dps for p in projs]
        [0.658, 0.722, 0.793, 0.870, 0.954]
    """
    projections = []
    for year in range(1, duration_years + 1):
        eps = starting_eps * (1 + growth_rate) ** year
        dps = eps * payout_ratio
        projections.append(DPSProjection(year=year, eps=eps, dps=dps))
    return projections


# ============================================================================
# Terminal Value (DDM specific)
# ============================================================================

def terminal_value_ddm(
    eps_terminal: float,
    payout_terminal: float,
    cost_of_equity_stable: float,
    growth_stable: float,
) -> float:
    """
    Stable phase Terminal Value (DDM).

    TV = (EPS_terminal × payout_stable) / (CoE_stable - g_stable)

    NOT: ABN Amro EPS_terminal = EPS_5 × (1 + g_stable)
         (high-growth Year 5'ten stable Year 6'ya geçiş)

    Args:
        eps_terminal: Year_terminal (= Year 6) EPS
        payout_terminal: Stable payout ratio (= 1 - g/ROE)
        cost_of_equity_stable: Stable phase Cost of Equity
        growth_stable: Stable growth rate

    Returns:
        Terminal Value (per share)

    Example (ABN Amro):
        >>> terminal_value_ddm(2.67, 0.6667, 0.0902, 0.05)
        44.27...  # Damodaran PDF: 42.41 (rounding farkı)
    """
    if cost_of_equity_stable <= growth_stable:
        raise ValueError(
            f"Cost of Equity ({cost_of_equity_stable}) must exceed "
            f"stable growth ({growth_stable}) for finite terminal value"
        )

    dps_terminal = eps_terminal * payout_terminal
    return dps_terminal / (cost_of_equity_stable - growth_stable)


# ============================================================================
# Full DDM Valuation
# ============================================================================

@dataclass
class DDMResult:
    """DDM valuation full breakdown."""
    starting_eps: float
    high_growth_rate: float
    high_growth_payout: float
    high_growth_coe: float
    stable_growth: float
    stable_coe: float

    dps_projections: List[DPSProjection]  # High growth phase
    eps_terminal: float

    terminal_value: float
    pv_high_growth_dps: float
    pv_terminal_value: float

    value_per_share: float


def dcf_ddm(
    starting_eps: float,
    high_growth_rate: float,
    high_growth_payout: float,
    high_growth_coe: float,
    high_growth_duration: int,
    stable_growth: float,
    stable_payout: float,
    stable_coe: float,
) -> DDMResult:
    """
    Full DDM valuation: 2-stage (high growth + stable perpetuity).

    Steps:
        1. Project DPS Year 1..N (high growth phase)
        2. Project Year N+1 EPS (stable phase 1. yıl)
        3. Terminal Value at Year N
        4. Discount all CFs to present (high-growth CoE)
        5. Sum: PV(DPS) + PV(TV) = value per share

    Args:
        starting_eps: Year 0 EPS
        high_growth_rate: High growth period growth
        high_growth_payout: High growth payout ratio
        high_growth_coe: Cost of Equity during high growth
        high_growth_duration: Duration in years (örn 5)
        stable_growth: Stable phase growth
        stable_payout: Stable phase payout (typically 1 - g/ROE)
        stable_coe: Stable phase Cost of Equity

    Returns:
        DDMResult with full breakdown

    Example (ABN Amro):
        >>> result = dcf_ddm(
        ...     starting_eps=1.60,
        ...     high_growth_rate=0.0973,
        ...     high_growth_payout=0.375,
        ...     high_growth_coe=0.0882,
        ...     high_growth_duration=5,
        ...     stable_growth=0.05,
        ...     stable_payout=0.6667,
        ...     stable_coe=0.0902,
        ... )
        >>> result.value_per_share  # ~30.87 EUR
        30.87
    """
    # 1) High growth DPS projection (Year 1..5)
    dps_projections = project_dps_high_growth(
        starting_eps=starting_eps,
        growth_rate=high_growth_rate,
        payout_ratio=high_growth_payout,
        duration_years=high_growth_duration,
    )

    # 2) EPS terminal (Year N+1) — stable growth ile
    eps_at_end_of_high_growth = starting_eps * (1 + high_growth_rate) ** high_growth_duration
    eps_terminal = eps_at_end_of_high_growth * (1 + stable_growth)

    # 3) Terminal Value (at Year N, end of high growth)
    tv = terminal_value_ddm(
        eps_terminal=eps_terminal,
        payout_terminal=stable_payout,
        cost_of_equity_stable=stable_coe,
        growth_stable=stable_growth,
    )

    # 4) PV — High growth DPS (Year 1..N), high-growth CoE ile discount
    pv_dps = sum(
        discount_to_present_value(p.dps, high_growth_coe, p.year)
        for p in dps_projections
    )

    # 5) PV — Terminal Value (at Year N endpoint)
    pv_tv = discount_to_present_value(tv, high_growth_coe, high_growth_duration)

    # 6) Final value per share
    value_per_share = pv_dps + pv_tv

    return DDMResult(
        starting_eps=starting_eps,
        high_growth_rate=high_growth_rate,
        high_growth_payout=high_growth_payout,
        high_growth_coe=high_growth_coe,
        stable_growth=stable_growth,
        stable_coe=stable_coe,
        dps_projections=dps_projections,
        eps_terminal=eps_terminal,
        terminal_value=tv,
        pv_high_growth_dps=pv_dps,
        pv_terminal_value=pv_tv,
        value_per_share=value_per_share,
    )
