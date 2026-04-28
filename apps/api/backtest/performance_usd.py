"""
USD-Basis Performance Metrics — Faz 4.1.

USD return serisi üzerinden TWR/Sharpe/Sortino/drawdown.
USD risk-free rate (Damodaran 10y Treasury proxy ~4%/yr).

Yapı: performance.py ile aynı API, sadece USD basis input + USD Rf.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from backtest.performance import (
    PerformanceMetrics,
    BetaResult,
    compute_metrics as _compute_metrics_base,
    compute_beta as _compute_beta_base,
    max_drawdown,
    cumulative_wealth,
)


# ============================================================================
# USD Risk-Free (Damodaran 10y Treasury proxy)
# ============================================================================

RISK_FREE_USD_ANNUAL = 0.04  # 10y T-Bond ~4% (2021-2026 ortalama)


# ============================================================================
# USD Performance Bundle
# ============================================================================

@dataclass
class USDPerformanceMetrics:
    """USD-basis metrik (TL muadili ile aynı schema)."""
    cumulative_return_usd: float
    annualized_return_usd: float
    annualized_volatility_usd: float
    sharpe_usd: Optional[float]
    sortino_usd: Optional[float]
    max_drawdown_usd: float
    avg_quarterly_return_usd: float
    best_quarter_usd: float
    worst_quarter_usd: float
    n_quarters: int
    n_positive_quarters: int
    n_negative_quarters: int


def compute_metrics_usd(
    usd_quarterly_returns: List[float],
    risk_free_annual: float = RISK_FREE_USD_ANNUAL,
) -> USDPerformanceMetrics:
    """USD basis returns → USDPerformanceMetrics."""
    base = _compute_metrics_base(usd_quarterly_returns, risk_free_annual)
    return USDPerformanceMetrics(
        cumulative_return_usd=base.cumulative_return,
        annualized_return_usd=base.annualized_return,
        annualized_volatility_usd=base.annualized_volatility,
        sharpe_usd=base.sharpe,
        sortino_usd=base.sortino,
        max_drawdown_usd=base.max_drawdown,
        avg_quarterly_return_usd=base.avg_quarterly_return,
        best_quarter_usd=base.best_quarter,
        worst_quarter_usd=base.worst_quarter,
        n_quarters=base.n_quarters,
        n_positive_quarters=base.n_positive_quarters,
        n_negative_quarters=base.n_negative_quarters,
    )


def compute_beta_usd(
    portfolio_returns_usd: List[float],
    benchmark_returns_usd: List[float],
    benchmark_label: str = "BENCHMARK_USD",
) -> BetaResult:
    """USD basis beta vs benchmark."""
    return _compute_beta_base(
        portfolio_returns_usd, benchmark_returns_usd,
        benchmark_label=benchmark_label,
    )
