"""
5-Failure Metric Tracker — ADR-055.

Faz 4 ADIM 2 — backtest sonuçlarından 5 disipline edici metrik:

  (a) Trading cost      — turnover × COST_PER_TRADE (yıllık)
  (b) Turnover rate     — sum(quarterly_turnover) × 4 / n_years (annualized)
  (c) Tax-drag proxy    — quarterly tax_drag × 4 (annualized)
  (d) Cash allocation   — avg quarterly cash_weight
  (e) Style consistency — sleeve drift stdev (MVP fixed weights → 0)

Threshold (Damodaran disipline):
  Turnover < %50/yr (passive) | %50-100 (active) | >%100 alarm
  Trading cost < %1.5/yr
  Tax-drag < %1/yr
  Cash %5-15 ideal | >%30 underinvested
  Style drift < %30 stable
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from backtest.simulation import BacktestResult


# ============================================================================
# Threshold Constants
# ============================================================================

TURNOVER_PASSIVE_MAX = 0.50
TURNOVER_ACTIVE_MAX = 1.00
TRADING_COST_ALARM = 0.015
TAX_DRAG_ALARM = 0.010
CASH_IDEAL_MIN = 0.05
CASH_IDEAL_MAX = 0.15
CASH_UNDERINV = 0.30
STYLE_DRIFT_ALARM = 0.30


# ============================================================================
# DataClass
# ============================================================================

@dataclass
class FailureMetrics:
    """5-failure tracker output."""
    # (a) Trading cost
    annualized_trading_cost: float
    trading_cost_verdict: str
    # (b) Turnover
    annualized_turnover: float
    turnover_verdict: str
    # (c) Tax-drag
    annualized_tax_drag: float
    tax_drag_verdict: str
    # (d) Cash
    avg_cash_weight: float
    cash_verdict: str
    # (e) Style drift
    style_consistency_score: float
    style_verdict: str


# ============================================================================
# Calculator
# ============================================================================

def _years(n_quarters: int) -> float:
    return max(n_quarters / 4.0, 1e-9)


def compute_failure_metrics(result: BacktestResult) -> FailureMetrics:
    """BacktestResult → FailureMetrics."""
    n = len(result.quarter_results)
    yrs = _years(n)

    # (a) Trading cost
    annual_cost = result.total_trading_cost / yrs
    cost_verdict = (
        "OK" if annual_cost < TRADING_COST_ALARM
        else "ALARM"
    )

    # (b) Turnover
    annual_turnover = result.total_turnover / yrs
    if annual_turnover < TURNOVER_PASSIVE_MAX:
        turn_verdict = "PASSIVE"
    elif annual_turnover < TURNOVER_ACTIVE_MAX:
        turn_verdict = "ACTIVE"
    else:
        turn_verdict = "ALARM"

    # (c) Tax-drag
    annual_tax = result.total_tax_drag / yrs
    tax_verdict = "OK" if annual_tax < TAX_DRAG_ALARM else "ALARM"

    # (d) Cash
    cash_weights = [q.cash_weight for q in result.quarter_results]
    avg_cash = sum(cash_weights) / len(cash_weights) if cash_weights else 0.0
    if avg_cash > CASH_UNDERINV:
        cash_verdict = "UNDERINVESTED"
    elif CASH_IDEAL_MIN <= avg_cash <= CASH_IDEAL_MAX:
        cash_verdict = "IDEAL"
    elif avg_cash < CASH_IDEAL_MIN:
        cash_verdict = "OVERINVESTED"
    else:
        cash_verdict = "ELEVATED"

    # (e) Style consistency (MVP fixed weights → 0 drift)
    # Per-quarter target weights identical → stdev = 0 → consistency = 1.0
    # Faz 4.5'te quarterly recompute weights gelince drift hesaplanır
    style_consistency = 1.0
    style_verdict = "STABLE (MVP fixed weights)"

    return FailureMetrics(
        annualized_trading_cost=annual_cost,
        trading_cost_verdict=cost_verdict,
        annualized_turnover=annual_turnover,
        turnover_verdict=turn_verdict,
        annualized_tax_drag=annual_tax,
        tax_drag_verdict=tax_verdict,
        avg_cash_weight=avg_cash,
        cash_verdict=cash_verdict,
        style_consistency_score=style_consistency,
        style_verdict=style_verdict,
    )
