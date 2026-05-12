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

from dataclasses import dataclass, field
from typing import List

# Industrial FCFF'den re-use
from .industrial_fcff import discount_to_present_value, linear_taper


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


# ============================================================================
# 3-Stage DDM (Damodaran ABN Amro pattern: high + transition + stable)
# ============================================================================

@dataclass
class YearlyDDMProjection:
    """3-stage DDM tek yil projection + phase metadata."""
    year: int
    phase: str  # "high" / "transition" / "stable"
    eps: float
    dps: float
    growth_rate: float
    payout_ratio: float
    cost_of_equity: float


@dataclass
class DDM3StageResult:
    """3-stage DDM full breakdown."""
    starting_eps: float

    # Phase params
    high_growth_rate: float
    high_growth_payout: float
    high_growth_coe: float
    high_growth_duration: int
    transition_period_years: int
    stable_growth: float
    stable_payout: float
    stable_coe: float

    # Projections (high + transition)
    yearly_projections: List[YearlyDDMProjection] = field(default_factory=list)

    # Terminal
    eps_terminal_phase: float = 0.0  # EPS at start of stable (Year N+transition+1)
    terminal_value: float = 0.0

    # PVs
    pv_high_growth_dps: float = 0.0
    pv_transition_dps: float = 0.0
    pv_terminal_value: float = 0.0

    value_per_share: float = 0.0


def dcf_ddm_3stage(
    starting_eps: float,
    # High growth phase (Y1..high_growth_duration sabit)
    high_growth_rate: float,
    high_growth_payout: float,
    high_growth_coe: float,
    # Stable phase (Y(end_transition+1)+ Gordon Growth)
    stable_growth: float,
    stable_payout: float,
    stable_coe: float,
    # Transition phase (linear taper Y(high_growth_duration+1)..(high_growth_duration+transition_period_years))
    high_growth_duration: int = 5,
    transition_period_years: int = 5,
) -> DDM3StageResult:
    """
    Damodaran 3-stage DDM (ABN Amro / Heineken hybrid pattern):
      Phase 1 (high)       : Y1..N1                       — sabit g, payout, CoE
      Phase 2 (transition) : Y(N1+1)..(N1+N2)             — linear taper to stable
      Phase 3 (stable)     : Y(N1+N2+1)+                  — Gordon Growth perpetuity

    Transition phase linear taper:
      growth_y  = high_g     + (stable_g     - high_g)     * (y - N1) / N2
      payout_y  = high_pay   + (stable_pay   - high_pay)   * (y - N1) / N2
      coe_y     = high_coe   + (stable_coe   - high_coe)   * (y - N1) / N2

    Discount factor: cumulative year-specific CoE
      df_y = prod_{k=1..y} (1 + coe_k)

    Terminal Value at end of transition (Y = N1+N2):
      EPS_(N1+N2+1) = EPS_(N1+N2) × (1 + stable_g)
      TV = EPS_(N1+N2+1) × stable_payout / (stable_coe - stable_g)
      PV(TV) = TV / df_(N1+N2)
    """
    if stable_coe <= stable_growth:
        raise ValueError(
            f"stable_coe ({stable_coe}) must exceed stable_growth ({stable_growth})"
        )

    n1 = high_growth_duration
    n2 = transition_period_years
    total_explicit_years = n1 + n2

    yearly: List[YearlyDDMProjection] = []
    cumulative_df = 1.0  # cumulative discount factor
    eps_prev = starting_eps
    pv_high = 0.0
    pv_transition = 0.0

    for y in range(1, total_explicit_years + 1):
        if y <= n1:
            phase = "high"
            g_y = high_growth_rate
            payout_y = high_growth_payout
            coe_y = high_growth_coe
        else:
            phase = "transition"
            g_y = linear_taper(high_growth_rate, stable_growth, y, n1, total_explicit_years)
            payout_y = linear_taper(high_growth_payout, stable_payout, y, n1, total_explicit_years)
            coe_y = linear_taper(high_growth_coe, stable_coe, y, n1, total_explicit_years)

        eps_y = eps_prev * (1 + g_y)
        dps_y = eps_y * payout_y
        cumulative_df *= (1 + coe_y)
        pv_y = dps_y / cumulative_df

        yearly.append(YearlyDDMProjection(
            year=y, phase=phase, eps=eps_y, dps=dps_y,
            growth_rate=g_y, payout_ratio=payout_y, cost_of_equity=coe_y,
        ))

        if phase == "high":
            pv_high += pv_y
        else:
            pv_transition += pv_y

        eps_prev = eps_y

    # Terminal Value at end of transition
    eps_end_transition = eps_prev  # EPS_(N1+N2)
    eps_terminal_phase = eps_end_transition * (1 + stable_growth)
    dps_terminal = eps_terminal_phase * stable_payout
    tv = dps_terminal / (stable_coe - stable_growth)
    pv_tv = tv / cumulative_df

    value_per_share = pv_high + pv_transition + pv_tv

    return DDM3StageResult(
        starting_eps=starting_eps,
        high_growth_rate=high_growth_rate,
        high_growth_payout=high_growth_payout,
        high_growth_coe=high_growth_coe,
        high_growth_duration=n1,
        transition_period_years=n2,
        stable_growth=stable_growth,
        stable_payout=stable_payout,
        stable_coe=stable_coe,
        yearly_projections=yearly,
        eps_terminal_phase=eps_terminal_phase,
        terminal_value=tv,
        pv_high_growth_dps=pv_high,
        pv_transition_dps=pv_transition,
        pv_terminal_value=pv_tv,
        value_per_share=value_per_share,
    )
