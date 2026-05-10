"""
Industrial 2-Stage FCFF DCF (Damodaran simplified).

Stage 1: 5-yıl explicit FCFF projection
Stage 2: Gordon Growth terminal value (terminal_g + WACC)

FCFF = NOPAT + D&A - CapEx - ΔWC
NOPAT = Op Income × (1 - tax_rate)

Lifecycle-adjusted growth assumptions:
  Mature Growth     → explicit g=10%, terminal g=2.5%
  Mature Stable     → explicit g=5%,  terminal g=2.5%
  High Growth       → explicit g=20%, terminal g=2.5% (5-yıl içinde fade)
  Young Growth      → explicit g=35%, terminal g=2.5% (asset-light, hızlı fade)
  Start-up / Distress → DCF uygunsuz (NULL)

Per share = (PV explicit + PV terminal - Total Debt + Cash) / shares
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


# Lifecycle → growth assumptions
_LIFECYCLE_GROWTH: Dict[str, Dict[str, float]] = {
    "start_up":         {"explicit_g": None, "terminal_g": None},  # DCF uygunsuz
    "young_growth":     {"explicit_g": 0.35, "terminal_g": 0.030},
    "high_growth":      {"explicit_g": 0.20, "terminal_g": 0.030},
    "mature_growth":    {"explicit_g": 0.10, "terminal_g": 0.030},
    "mature_stable":    {"explicit_g": 0.05, "terminal_g": 0.030},
    "decline_distress": {"explicit_g": None, "terminal_g": None},
}


@dataclass
class DCFInputs:
    revenue: float
    op_income: float
    capex: float
    da: float
    working_capital: float
    tax_rate: float
    total_debt: float
    cash: float
    shares_outstanding: float
    wacc: float
    lifecycle_stage: str
    # Faz B2 Phase 1: cross-holdings (Damodaran)
    cross_holdings_value: float = 0.0


@dataclass
class DCFResult:
    intrinsic_per_share: Optional[float]
    enterprise_value: Optional[float]
    equity_value: Optional[float]
    pv_explicit: Optional[float]
    pv_terminal: Optional[float]
    fcff_year1: Optional[float]
    explicit_g: Optional[float]
    terminal_g: Optional[float]
    # Faz B2 Phase 1: cross-holdings audit trail
    cross_holdings_added_tl: Optional[float] = None
    error: Optional[str] = None
    notes: List[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []


def calculate_fcff_dcf(inputs: DCFInputs) -> DCFResult:
    """2-stage FCFF DCF + per-share intrinsic.

    Banking/Holding/Distress için NULL döner.
    """
    growth = _LIFECYCLE_GROWTH.get(inputs.lifecycle_stage, {})
    explicit_g = growth.get("explicit_g")
    terminal_g = growth.get("terminal_g")

    if explicit_g is None or terminal_g is None:
        return DCFResult(
            intrinsic_per_share=None,
            enterprise_value=None,
            equity_value=None,
            pv_explicit=None,
            pv_terminal=None,
            fcff_year1=None,
            explicit_g=explicit_g,
            terminal_g=terminal_g,
            error=f"lifecycle '{inputs.lifecycle_stage}' DCF unsuitable",
        )

    # Sanity check WACC vs terminal
    if inputs.wacc <= terminal_g:
        return DCFResult(
            intrinsic_per_share=None,
            enterprise_value=None,
            equity_value=None,
            pv_explicit=None,
            pv_terminal=None,
            fcff_year1=None,
            explicit_g=explicit_g,
            terminal_g=terminal_g,
            error=f"WACC ({inputs.wacc:.4f}) ≤ terminal_g ({terminal_g:.4f})",
        )

    # Base year ratios
    if inputs.revenue <= 0:
        return DCFResult(
            intrinsic_per_share=None,
            enterprise_value=None,
            equity_value=None,
            pv_explicit=None,
            pv_terminal=None,
            fcff_year1=None,
            explicit_g=explicit_g,
            terminal_g=terminal_g,
            error="non-positive revenue",
        )

    op_margin = inputs.op_income / inputs.revenue
    capex_ratio = inputs.capex / inputs.revenue
    da_ratio = inputs.da / inputs.revenue
    wc_ratio = inputs.working_capital / inputs.revenue

    # 5-year explicit FCFF
    rev_prev = inputs.revenue
    fcff_projections: List[float] = []
    for year in range(1, 6):
        rev_y = rev_prev * (1 + explicit_g)
        op_y = rev_y * op_margin
        nopat_y = op_y * (1 - inputs.tax_rate)
        capex_y = rev_y * capex_ratio
        da_y = rev_y * da_ratio
        wc_change_y = (rev_y - rev_prev) * wc_ratio
        fcff_y = nopat_y + da_y - capex_y - wc_change_y
        fcff_projections.append(fcff_y)
        rev_prev = rev_y

    # PV of explicit
    pv_explicit = sum(
        fcff / ((1 + inputs.wacc) ** year)
        for year, fcff in enumerate(fcff_projections, 1)
    )

    # Terminal value (Gordon Growth)
    fcff_terminal_year = fcff_projections[-1] * (1 + terminal_g)
    tv = fcff_terminal_year / (inputs.wacc - terminal_g)
    pv_tv = tv / ((1 + inputs.wacc) ** 5)

    # Enterprise + equity
    ev = pv_explicit + pv_tv
    # Faz B2 Phase 1: + cross-holdings (equity method, joint, financial)
    equity_value = ev - inputs.total_debt + inputs.cash + inputs.cross_holdings_value

    if inputs.shares_outstanding <= 0:
        return DCFResult(
            intrinsic_per_share=None,
            enterprise_value=ev,
            equity_value=equity_value,
            pv_explicit=pv_explicit,
            pv_terminal=pv_tv,
            fcff_year1=fcff_projections[0],
            explicit_g=explicit_g,
            terminal_g=terminal_g,
            error="non-positive shares_outstanding",
        )

    intrinsic = equity_value / inputs.shares_outstanding

    return DCFResult(
        intrinsic_per_share=intrinsic,
        enterprise_value=ev,
        equity_value=equity_value,
        pv_explicit=pv_explicit,
        pv_terminal=pv_tv,
        fcff_year1=fcff_projections[0],
        explicit_g=explicit_g,
        terminal_g=terminal_g,
        cross_holdings_added_tl=(
            inputs.cross_holdings_value
            if inputs.cross_holdings_value > 0 else None
        ),
    )
