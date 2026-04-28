"""
Historical Price Fetcher — Yahoo Finance v8 period1/period2 + disk cache.

Faz 4 ADIM 2 — backtest engine için BIST + benchmark daily/quarterly close.

Yahoo Finance:
  https://query1.finance.yahoo.com/v8/finance/chart/{symbol}
  ?period1=<epoch_start>&period2=<epoch_end>&interval=1d

Cache:
  ~/.cache/reeldeger_backtest/{symbol_hash}.json
  Per-symbol JSON, daily close prices.

Quarter-end resampling:
  Calendar quarter end (Mar/Jun/Sep/Dec) → last trading day on or before.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

CACHE_DIR = Path.home() / ".cache" / "reeldeger_backtest"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,*/*",
}

BIST_SUFFIX = ".IS"


# ============================================================================
# Symbol Helpers
# ============================================================================

def to_yahoo_symbol(ticker_or_symbol: str) -> str:
    """
    BIST ticker → Yahoo symbol; index/ETF/FX passthrough.

    TUPRS    → TUPRS.IS
    XU100    → XU100.IS
    SPY      → SPY (no suffix)
    %5EVIX   → %5EVIX (URL-encoded ^VIX, passthrough)
    USDTRY=X → USDTRY=X (FX pair, passthrough)
    """
    s = ticker_or_symbol.upper().strip()
    if s.endswith(BIST_SUFFIX):
        return s
    if s.endswith("=X"):
        # FX pair: USDTRY=X, EURTRY=X, etc.
        return s
    if s in ("SPY", "QQQ", "DIA"):
        return s
    if s.startswith("%5E") or s.startswith("^"):
        # ^GSPC, ^VIX, ^XU100 — Yahoo URL needs %5E URL-encoding
        return s.replace("^", "%5E")
    if s.startswith("XU") or s.startswith("XBANK"):
        # BIST indices (XU100, XU030, XBANK)
        return f"{s}{BIST_SUFFIX}"
    # Default: assume BIST ticker
    return f"{s}{BIST_SUFFIX}"


def _cache_path(symbol: str, start: date, end: date) -> Path:
    safe = symbol.replace("%5E", "_idx_").replace(".", "_")
    return CACHE_DIR / f"{safe}_{start.isoformat()}_{end.isoformat()}.json"


# ============================================================================
# Daily Range Fetch
# ============================================================================

async def fetch_daily_range(
    yahoo_symbol: str,
    start_date: date,
    end_date: date,
    use_cache: bool = True,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[date, float]:
    """
    Yahoo Finance daily close prices for [start_date, end_date].

    Returns:
        Dict[date, float]: trading day close prices.
    """
    cache_path = _cache_path(yahoo_symbol, start_date, end_date)
    if use_cache and cache_path.exists():
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        return {date.fromisoformat(k): float(v) for k, v in data.items()}

    period1 = int(datetime.combine(start_date, datetime.min.time()).timestamp())
    period2 = int(datetime.combine(end_date, datetime.min.time()).timestamp())

    own_client = False
    if client is None:
        client = httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=30.0)
        own_client = True

    try:
        url = YAHOO_URL.format(symbol=yahoo_symbol)
        r = await client.get(url, params={
            "period1": period1,
            "period2": period2,
            "interval": "1d",
        })
        r.raise_for_status()
        j = r.json()

        result = j["chart"]["result"][0]
        timestamps = result.get("timestamp", []) or []
        quote = result.get("indicators", {}).get("quote", [{}])[0]
        closes = quote.get("close", []) or []

        out: Dict[date, float] = {}
        for ts, close in zip(timestamps, closes):
            if close is None:
                continue
            d = datetime.fromtimestamp(ts).date()
            out[d] = float(close)

        if use_cache:
            serializable = {d.isoformat(): v for d, v in out.items()}
            cache_path.write_text(
                json.dumps(serializable, indent=2),
                encoding="utf-8",
            )
        return out

    finally:
        if own_client:
            await client.aclose()


# ============================================================================
# Quarter-End Resampling
# ============================================================================

def quarter_end_calendar(start: date, end: date) -> List[date]:
    """Calendar quarter-ends (Mar/Jun/Sep/Dec) within [start, end]."""
    out: List[date] = []
    for year in range(start.year, end.year + 1):
        for month, day in [(3, 31), (6, 30), (9, 30), (12, 31)]:
            qe = date(year, month, day)
            if start <= qe <= end:
                out.append(qe)
    return sorted(out)


def resample_quarterly(
    daily: Dict[date, float],
    quarter_ends: List[date],
) -> Dict[date, float]:
    """For each quarter-end calendar date, last trading day close on or before."""
    sorted_dates = sorted(daily.keys())
    out: Dict[date, float] = {}
    for qe in quarter_ends:
        latest = None
        for d in sorted_dates:
            if d <= qe:
                latest = d
            else:
                break
        if latest is not None:
            out[qe] = daily[latest]
    return out


async def fetch_quarterly_close(
    ticker_or_symbol: str,
    start_date: date,
    end_date: date,
    use_cache: bool = True,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[date, float]:
    """
    High-level: fetch daily, resample to quarter-ends.

    Backfill: start_date'den 10 gün öncesine kadar fetch yapılır ki
    weekend/holiday düşen quarter-end'ler için son trading day yakalansın
    (örn. 2024-03-31 Easter Sunday → 2024-03-28 Friday close kullanılır).
    """
    yh = to_yahoo_symbol(ticker_or_symbol)
    fetch_start = start_date - timedelta(days=10)
    daily = await fetch_daily_range(yh, fetch_start, end_date,
                                     use_cache=use_cache, client=client)
    qends = quarter_end_calendar(start_date, end_date)
    return resample_quarterly(daily, qends)


async def fetch_batch_quarterly_close(
    tickers: List[str],
    start_date: date,
    end_date: date,
    use_cache: bool = True,
    max_concurrent: int = 5,
) -> Dict[str, Dict[date, float]]:
    """Multi-ticker quarterly close (paralel)."""
    sem = asyncio.Semaphore(max_concurrent)

    async with httpx.AsyncClient(
        headers=DEFAULT_HEADERS, timeout=30.0,
    ) as client:
        async def one(t: str) -> tuple:
            async with sem:
                try:
                    q = await fetch_quarterly_close(
                        t, start_date, end_date,
                        use_cache=use_cache, client=client,
                    )
                    return t, q
                except Exception as e:
                    logger.warning(f"Fetch fail for {t}: {type(e).__name__}: {e}")
                    return t, {}

        results = await asyncio.gather(*[one(t) for t in tickers])

    return {t: q for t, q in results}
