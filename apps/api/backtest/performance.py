"""
Performance Metrics — TWR/IRR/Sharpe/Sortino/Drawdown/Beta.

Faz 4 ADIM 2 — quarterly returns serisi üzerinden risk-adjusted metrik.

Notlar:
  - Sharpe: Rf = Damodaran TR 10y bond proxy (~%4 USD basis MVP)
  - Sortino: downside deviation (sadece negative returns)
  - Drawdown: cumulative wealth peak-to-trough
  - Beta: cov(p, b) / var(b), benchmark vs portfolio
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, List, Optional


# ============================================================================
# Defaults (Faz 4 MVP)
# ============================================================================

RISK_FREE_USD_ANNUAL = 0.04  # USD basis MVP — Damodaran Rf proxy
QUARTERS_PER_YEAR = 4


# ============================================================================
# DataClasses
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Backtest performance metrik bundle."""
    cumulative_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe: Optional[float]
    sortino: Optional[float]
    max_drawdown: float
    avg_quarterly_return: float
    best_quarter: float
    worst_quarter: float
    n_quarters: int
    n_positive_quarters: int
    n_negative_quarters: int


@dataclass
class BetaResult:
    """Portfolio vs benchmark beta + correlation."""
    benchmark: str
    beta: Optional[float]
    correlation: Optional[float]
    alpha_quarterly: Optional[float]
    n_observations: int


# ============================================================================
# Math Helpers
# ============================================================================

def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _stdev(xs: List[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return sqrt(var)


def _covariance(xs: List[float], ys: List[float]) -> float:
    if len(xs) < 2 or len(xs) != len(ys):
        return 0.0
    mx, my = _mean(xs), _mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (len(xs) - 1)


# ============================================================================
# Drawdown
# ============================================================================

def cumulative_wealth(returns: List[float], start: float = 1.0) -> List[float]:
    """Wealth path (1 + r) cumprod."""
    out = []
    w = start
    for r in returns:
        w *= (1.0 + r)
        out.append(w)
    return out


def max_drawdown(returns: List[float]) -> float:
    """Max peak-to-trough drawdown (negative number, e.g., -0.30 = -%30)."""
    if not returns:
        return 0.0
    wealth = cumulative_wealth(returns)
    peak = wealth[0]
    max_dd = 0.0
    for w in wealth:
        if w > peak:
            peak = w
        dd = (w - peak) / peak if peak > 0 else 0.0
        if dd < max_dd:
            max_dd = dd
    return max_dd


# ============================================================================
# Performance Metrics
# ============================================================================

def compute_metrics(
    quarterly_returns: List[float],
    risk_free_annual: float = RISK_FREE_USD_ANNUAL,
) -> PerformanceMetrics:
    """Quarterly returns → full metric bundle."""
    n = len(quarterly_returns)
    if n == 0:
        return PerformanceMetrics(
            cumulative_return=0.0,
            annualized_return=0.0,
            annualized_volatility=0.0,
            sharpe=None,
            sortino=None,
            max_drawdown=0.0,
            avg_quarterly_return=0.0,
            best_quarter=0.0,
            worst_quarter=0.0,
            n_quarters=0,
            n_positive_quarters=0,
            n_negative_quarters=0,
        )

    # Cumulative
    cum = 1.0
    for r in quarterly_returns:
        cum *= (1.0 + r)
    cum_return = cum - 1.0
    annualized = (1.0 + cum_return) ** (QUARTERS_PER_YEAR / n) - 1.0

    # Volatility (annualized)
    q_vol = _stdev(quarterly_returns)
    annual_vol = q_vol * sqrt(QUARTERS_PER_YEAR)

    # Sharpe (annualized)
    if annual_vol > 0:
        sharpe = (annualized - risk_free_annual) / annual_vol
    else:
        sharpe = None

    # Sortino (downside deviation)
    downside = [r for r in quarterly_returns if r < 0]
    if downside:
        d_vol_q = _stdev(downside)
        d_vol_a = d_vol_q * sqrt(QUARTERS_PER_YEAR)
        sortino = ((annualized - risk_free_annual) / d_vol_a
                   if d_vol_a > 0 else None)
    else:
        sortino = None

    return PerformanceMetrics(
        cumulative_return=cum_return,
        annualized_return=annualized,
        annualized_volatility=annual_vol,
        sharpe=sharpe,
        sortino=sortino,
        max_drawdown=max_drawdown(quarterly_returns),
        avg_quarterly_return=_mean(quarterly_returns),
        best_quarter=max(quarterly_returns),
        worst_quarter=min(quarterly_returns),
        n_quarters=n,
        n_positive_quarters=sum(1 for r in quarterly_returns if r > 0),
        n_negative_quarters=sum(1 for r in quarterly_returns if r < 0),
    )


# ============================================================================
# Beta vs Benchmark
# ============================================================================

def compute_beta(
    portfolio_returns: List[float],
    benchmark_returns: List[float],
    benchmark_label: str = "BENCHMARK",
) -> BetaResult:
    """β = cov(p,b) / var(b), correlation, alpha."""
    n = min(len(portfolio_returns), len(benchmark_returns))
    p = portfolio_returns[:n]
    b = benchmark_returns[:n]

    if n < 2:
        return BetaResult(
            benchmark=benchmark_label,
            beta=None, correlation=None, alpha_quarterly=None,
            n_observations=n,
        )

    var_b = _stdev(b) ** 2
    if var_b <= 0:
        return BetaResult(
            benchmark=benchmark_label,
            beta=None, correlation=None, alpha_quarterly=None,
            n_observations=n,
        )

    cov_pb = _covariance(p, b)
    beta = cov_pb / var_b

    sd_p = _stdev(p)
    sd_b = _stdev(b)
    if sd_p > 0 and sd_b > 0:
        corr = cov_pb / (sd_p * sd_b)
    else:
        corr = None

    alpha_q = _mean(p) - beta * _mean(b)

    return BetaResult(
        benchmark=benchmark_label,
        beta=beta,
        correlation=corr,
        alpha_quarterly=alpha_q,
        n_observations=n,
    )
