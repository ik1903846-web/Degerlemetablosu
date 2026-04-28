"""
Quarterly Rebalance Simulation Engine — Faz 4 ADIM 2.

Akış:
  1. PortfolioSnapshot (FIXED weights MVP look-ahead)
  2. Per-quarter:
     - Pre-rebalance weights = drift'lenmiş weights (eski quarter return ile)
     - Turnover = sum(abs(target - drifted)) / 2
     - Trading cost (realistic): turnover × COST_PER_TRADE
     - Rebalance → target weights restored
     - Quarterly portfolio return = sum(target_w × ticker_return) - cost
  3. TWR cumulative = product(1 + r_q) - 1

Cost models:
  zero      → trading_cost = 0, tax_drag = 0
  realistic → trading_cost = turnover × 0.0015 (round-trip),
              tax_drag = ~%0.5/yr proxy (BIST stopaj %15 × ~%3 div yield)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from backtest.point_in_time import PortfolioSnapshot


# ============================================================================
# Cost Constants
# ============================================================================

COST_PER_TRADE = 0.0015  # %0.15 round-trip (commission %0.05-0.1 + slippage %0.05)
TAX_DRAG_ANNUAL = 0.005  # %0.5/yr proxy (BIST div stopaj %15 × ~%3 yield)
TAX_DRAG_QUARTERLY = TAX_DRAG_ANNUAL / 4.0


# ============================================================================
# DataClasses
# ============================================================================

@dataclass
class QuarterResult:
    """Tek quarter sonuç."""
    quarter_end: date
    portfolio_return: float            # net (cost included)
    portfolio_return_gross: float
    turnover: float
    trading_cost: float
    tax_drag: float
    cash_weight: float
    pre_rebalance_weights: Dict[str, float]
    post_rebalance_weights: Dict[str, float]
    ticker_returns: Dict[str, float]   # quarter return per ticker
    skipped_tickers: List[str] = field(default_factory=list)


@dataclass
class BacktestResult:
    """Tam backtest sonuçları."""
    risk_profile: str
    cost_model: str                    # "zero" | "realistic"
    quarter_results: List[QuarterResult]
    quarterly_returns: List[float]     # net quarter returns
    quarterly_returns_gross: List[float]
    cumulative_twr: float              # 5-yıl cumulative return
    cumulative_twr_gross: float
    annualized_return: float
    annualized_return_gross: float
    total_turnover: float              # toplam (4 × quarterly avg)
    total_trading_cost: float
    total_tax_drag: float
    look_ahead_bias: bool = True


# ============================================================================
# Simulation Core
# ============================================================================

def _compute_ticker_returns(
    prices: Dict[str, Dict[date, float]],
    q_start: date,
    q_end: date,
) -> Dict[str, float]:
    """Per-ticker return for quarter [q_start, q_end]."""
    out: Dict[str, float] = {}
    for ticker, series in prices.items():
        p_start = series.get(q_start)
        p_end = series.get(q_end)
        if p_start is None or p_end is None or p_start <= 0:
            continue
        out[ticker] = (p_end / p_start) - 1.0
    return out


def _drift_weights(
    target_weights: Dict[str, float],
    ticker_returns: Dict[str, float],
    cash_weight: float,
) -> Dict[str, float]:
    """
    Pre-rebalance drift'lenmiş weights.
    weight_drifted_i = target_i × (1 + r_i) / (1 + r_p)
    """
    portfolio_return = 0.0
    for t, w in target_weights.items():
        r = ticker_returns.get(t, 0.0)
        portfolio_return += w * r
    # Cash 0% return
    denom = 1.0 + portfolio_return
    if denom <= 0:
        return dict(target_weights)
    return {
        t: w * (1.0 + ticker_returns.get(t, 0.0)) / denom
        for t, w in target_weights.items()
    }


def _turnover(
    pre: Dict[str, float],
    target: Dict[str, float],
) -> float:
    """L1 turnover = sum(|target - pre|) / 2."""
    keys = set(pre) | set(target)
    return sum(abs(target.get(k, 0.0) - pre.get(k, 0.0)) for k in keys) / 2.0


def run_backtest(
    snapshot: PortfolioSnapshot,
    prices: Dict[str, Dict[date, float]],
    quarter_ends: List[date],
    cost_model: str = "zero",
    regime_overlay: Optional[Dict[str, Dict[str, float]]] = None,
    regime_calendar: Optional[List] = None,
) -> BacktestResult:
    """
    Tek profile + cost model için 20-quarter simulation.

    Args:
        snapshot: PortfolioSnapshot (FIXED weights, MVP look-ahead)
        prices: ticker → {date: close}
        quarter_ends: 21 quarter-end (start + 20 quarter)
        cost_model: "zero" | "realistic"
        regime_overlay: Faz 4.8 — {regime_name: {sleeve_multiplier, cash_min, cash_max}}
        regime_calendar: List[RegimeTag] (per quarter regime tag)
    """
    if cost_model not in ("zero", "realistic"):
        raise ValueError(f"cost_model: {cost_model}")

    base_target_w = dict(snapshot.position_weights)
    cash_w = snapshot.cash_weight
    quarter_results: List[QuarterResult] = []
    quarterly_returns: List[float] = []
    quarterly_returns_gross: List[float] = []
    total_turnover = 0.0
    total_trading_cost = 0.0
    total_tax_drag = 0.0

    # Tactical overlay per-quarter regime map
    regime_for_qe: Dict[date, str] = {}
    if regime_calendar:
        for rt in regime_calendar:
            regime_for_qe[rt.quarter_end] = rt.regime.value

    # Quarter loop: q_start → q_end pairs
    for i in range(len(quarter_ends) - 1):
        q_start = quarter_ends[i]
        q_end = quarter_ends[i + 1]

        # Regime-adjusted target weights (Faz 4.8 tactical overlay)
        if regime_overlay and regime_calendar:
            regime = regime_for_qe.get(q_start, "normal")
            mult = regime_overlay.get(regime, regime_overlay.get("normal", {})).get(
                "sleeve_multiplier", 1.0
            )
            target_w = {t: w * mult for t, w in base_target_w.items()}
        else:
            target_w = base_target_w

        ticker_returns = _compute_ticker_returns(prices, q_start, q_end)
        skipped = [t for t in target_w if t not in ticker_returns]

        # Gross portfolio return (target weights)
        gross_ret = 0.0
        for t, w in target_w.items():
            r = ticker_returns.get(t, 0.0)
            gross_ret += w * r
        # Cash earns 0 (MVP)

        # Drift + turnover
        drifted = _drift_weights(target_w, ticker_returns, cash_w)
        turnover = _turnover(drifted, target_w)

        # Cost application
        if cost_model == "realistic":
            trading_cost = turnover * COST_PER_TRADE
            tax_drag = TAX_DRAG_QUARTERLY
        else:
            trading_cost = 0.0
            tax_drag = 0.0

        net_ret = gross_ret - trading_cost - tax_drag

        quarter_results.append(QuarterResult(
            quarter_end=q_end,
            portfolio_return=net_ret,
            portfolio_return_gross=gross_ret,
            turnover=turnover,
            trading_cost=trading_cost,
            tax_drag=tax_drag,
            cash_weight=cash_w,
            pre_rebalance_weights=drifted,
            post_rebalance_weights=dict(target_w),
            ticker_returns=ticker_returns,
            skipped_tickers=skipped,
        ))
        quarterly_returns.append(net_ret)
        quarterly_returns_gross.append(gross_ret)
        total_turnover += turnover
        total_trading_cost += trading_cost
        total_tax_drag += tax_drag

    # Cumulative TWR (geometric)
    cum_twr = 1.0
    for r in quarterly_returns:
        cum_twr *= (1.0 + r)
    cum_twr -= 1.0

    cum_twr_gross = 1.0
    for r in quarterly_returns_gross:
        cum_twr_gross *= (1.0 + r)
    cum_twr_gross -= 1.0

    n_quarters = len(quarterly_returns)
    if n_quarters > 0:
        annualized = (1.0 + cum_twr) ** (4.0 / n_quarters) - 1.0
        annualized_gross = (1.0 + cum_twr_gross) ** (4.0 / n_quarters) - 1.0
    else:
        annualized = 0.0
        annualized_gross = 0.0

    return BacktestResult(
        risk_profile=snapshot.risk_profile,
        cost_model=cost_model,
        quarter_results=quarter_results,
        quarterly_returns=quarterly_returns,
        quarterly_returns_gross=quarterly_returns_gross,
        cumulative_twr=cum_twr,
        cumulative_twr_gross=cum_twr_gross,
        annualized_return=annualized,
        annualized_return_gross=annualized_gross,
        total_turnover=total_turnover,
        total_trading_cost=total_trading_cost,
        total_tax_drag=total_tax_drag,
        look_ahead_bias=snapshot.look_ahead_bias,
    )


def benchmark_returns(
    benchmark_series: Dict[date, float],
    quarter_ends: List[date],
) -> List[float]:
    """Benchmark quarter-by-quarter returns."""
    out: List[float] = []
    for i in range(len(quarter_ends) - 1):
        q0 = quarter_ends[i]
        q1 = quarter_ends[i + 1]
        p0 = benchmark_series.get(q0)
        p1 = benchmark_series.get(q1)
        if p0 is None or p1 is None or p0 <= 0:
            out.append(0.0)
            continue
        out.append((p1 / p0) - 1.0)
    return out
