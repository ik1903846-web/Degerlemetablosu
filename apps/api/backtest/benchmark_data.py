"""
Triple Benchmark + VIX — ADR-019.

XU100  (BIST 100, TR broad)        — Yahoo: XU100.IS
XU030  (BIST 30, TR peer to universe) — Yahoo: XU030.IS
SPY    (S&P 500 ETF, USD global)   — Yahoo: SPY
VIX    (CBOE volatility — regime)  — Yahoo: %5EVIX (URL-encoded ^VIX)
XBANK  (bonus, banking sub-index)  — Yahoo: XBANK.IS
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List

from backtest.historical_data import (
    fetch_quarterly_close,
    fetch_batch_quarterly_close,
)


# ============================================================================
# Benchmark Symbol Map
# ============================================================================

BENCHMARK_SYMBOLS: Dict[str, str] = {
    "XU100": "XU100.IS",
    "XU030": "XU030.IS",
    "SPY":   "SPY",
    "XBANK": "XBANK.IS",
}

VIX_SYMBOL = "%5EVIX"


# ============================================================================
# Triple Benchmark Quarterly Close
# ============================================================================

async def fetch_benchmark_quarterly(
    benchmark: str,
    start_date: date,
    end_date: date,
    use_cache: bool = True,
) -> Dict[date, float]:
    """Tek benchmark için quarter-end close serisi."""
    sym = BENCHMARK_SYMBOLS.get(benchmark.upper())
    if sym is None:
        raise ValueError(
            f"Bilinmeyen benchmark: {benchmark} "
            f"(geçerli: {list(BENCHMARK_SYMBOLS.keys())})"
        )
    return await fetch_quarterly_close(sym, start_date, end_date, use_cache=use_cache)


async def fetch_triple_benchmark(
    start_date: date,
    end_date: date,
    use_cache: bool = True,
) -> Dict[str, Dict[date, float]]:
    """
    Triple benchmark (XU100, XU030, SPY) quarterly close.

    Returns:
        {"XU100": {date: close, ...}, "XU030": ..., "SPY": ...}
    """
    symbols = ["XU100.IS", "XU030.IS", "SPY"]
    raw = await fetch_batch_quarterly_close(
        symbols, start_date, end_date, use_cache=use_cache,
    )
    # Re-map via BENCHMARK_SYMBOLS reverse-lookup
    out: Dict[str, Dict[date, float]] = {}
    for label, sym in BENCHMARK_SYMBOLS.items():
        if label in ("XBANK",):  # Triple benchmark dışı
            continue
        if sym in raw:
            out[label] = raw[sym]
    return out


# ============================================================================
# VIX Regime Series
# ============================================================================

async def fetch_vix_quarterly(
    start_date: date,
    end_date: date,
    use_cache: bool = True,
) -> Dict[date, float]:
    """VIX quarter-end values (regime classifier input)."""
    return await fetch_quarterly_close(
        VIX_SYMBOL, start_date, end_date, use_cache=use_cache,
    )
