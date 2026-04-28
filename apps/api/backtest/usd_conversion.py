"""
USD Basis Conversion — Faz 4.1 (Damodaran ADR-002).

TL nominal portfolio values + benchmark series → USD basis.

USD/TRY Yahoo symbol: USDTRY=X (1 USD = X TL)
USD value at quarter t = TL_value_t / USD_TRY_rate_t

Damodaran disiplini:
  ADR-002: USD-only zorunlu (TL DCF yasak)
  TFRS-29 hyperinflation period'unda TL nominal returns yanıltıcı
  USD-basis return real alpha measurement

Usage:
  fx_quarterly = await fetch_usd_try_quarterly(start, end)
  tl_values = build_value_series_from_returns(quarterly_returns, base=1.0)
  usd_values = convert_tl_series_to_usd(tl_values, fx_quarterly, qends)
  usd_returns = value_series_to_returns(usd_values)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List

from backtest.historical_data import (
    fetch_quarterly_close,
    quarter_end_calendar,
)


# ============================================================================
# USD/TRY Symbol
# ============================================================================

USD_TRY_SYMBOL = "USDTRY=X"


# ============================================================================
# DataClasses
# ============================================================================

@dataclass
class FXRate:
    """Tek quarter-end USD/TRY kur."""
    date: date
    usd_try: float  # 1 USD = X TL

    @property
    def try_usd(self) -> float:
        """1 TL kaç USD."""
        return 1.0 / self.usd_try if self.usd_try > 0 else 0.0


# ============================================================================
# FX Fetcher
# ============================================================================

async def fetch_usd_try_quarterly(
    start_date: date,
    end_date: date,
    use_cache: bool = True,
) -> Dict[date, float]:
    """
    Quarter-end USD/TRY kur serisi.

    Returns:
        {date(2021,6,30): 8.65, date(2021,9,30): 8.83, ...}
    """
    return await fetch_quarterly_close(
        USD_TRY_SYMBOL,
        start_date,
        end_date,
        use_cache=use_cache,
    )


# ============================================================================
# Value Series Builders
# ============================================================================

def build_value_series_from_returns(
    quarterly_returns: List[float],
    base: float = 1.0,
) -> List[float]:
    """
    Quarter returns → wealth path (1 + r) cumprod.

    Returns N+1 values: [base, base*(1+r0), base*(1+r0)*(1+r1), ...]
    İlk değer base, son değer cumulative wealth.
    """
    out = [base]
    w = base
    for r in quarterly_returns:
        w *= (1.0 + r)
        out.append(w)
    return out


def value_series_to_returns(values: List[float]) -> List[float]:
    """N value → N-1 quarterly return."""
    if len(values) < 2:
        return []
    return [
        (values[i + 1] / values[i]) - 1.0
        for i in range(len(values) - 1)
        if values[i] > 0
    ]


# ============================================================================
# TL → USD Conversion
# ============================================================================

def convert_tl_series_to_usd(
    tl_values: List[float],
    fx_rates: Dict[date, float],
    quarter_ends: List[date],
) -> List[float]:
    """
    TL value serisi → USD value serisi.

    USD_t = TL_t / USDTRY_t

    Args:
        tl_values: N+1 TL value (base + N quarter returns sonrası)
        fx_rates: {date: usd_try}
        quarter_ends: N+1 quarter-end (tl_values ile aynı uzunluk)

    Returns:
        N+1 USD value serisi.
    """
    if len(tl_values) != len(quarter_ends):
        raise ValueError(
            f"tl_values ({len(tl_values)}) != quarter_ends ({len(quarter_ends)})"
        )
    out: List[float] = []
    for tl_v, qe in zip(tl_values, quarter_ends):
        fx = fx_rates.get(qe)
        if fx is None or fx <= 0:
            # Yakın quarter-end'den fallback
            sorted_dates = sorted(fx_rates.keys())
            fx = None
            for d in reversed(sorted_dates):
                if d <= qe:
                    fx = fx_rates[d]
                    break
            if fx is None or fx <= 0:
                fx = 1.0  # Edge case — should not happen
        out.append(tl_v / fx)
    return out


def convert_quarterly_returns_to_usd(
    tl_quarterly_returns: List[float],
    fx_rates: Dict[date, float],
    quarter_ends: List[date],
) -> List[float]:
    """
    TL quarterly returns + FX serisi → USD quarterly returns.

    Akış:
      1. TL returns → TL value serisi (base=1.0, N+1 values)
      2. TL values + FX → USD values (N+1)
      3. USD values → USD returns (N)

    Args:
        tl_quarterly_returns: N quarter return (TL nominal)
        fx_rates: {date: usd_try} (quarter-ends dahil)
        quarter_ends: N+1 quarter-end (start + N quarter)
    """
    tl_values = build_value_series_from_returns(tl_quarterly_returns, base=1.0)
    usd_values = convert_tl_series_to_usd(tl_values, fx_rates, quarter_ends)
    return value_series_to_returns(usd_values)


# ============================================================================
# Cumulative Helpers
# ============================================================================

def cumulative_return_from_returns(returns: List[float]) -> float:
    """Geometric cumulative: prod(1 + r) - 1."""
    cum = 1.0
    for r in returns:
        cum *= (1.0 + r)
    return cum - 1.0


def annualized_return(cumulative: float, n_quarters: int) -> float:
    """Cumulative + quarter sayısı → annualized."""
    if n_quarters <= 0:
        return 0.0
    return (1.0 + cumulative) ** (4.0 / n_quarters) - 1.0
