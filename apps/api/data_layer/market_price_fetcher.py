"""
BIST Live Market Price Fetcher.

Yahoo Finance v8 API:
- Free, no auth
- BIST suffix .IS (TUPRS.IS, ARCLK.IS)
- Currency TRY, Exchange IST
- Stable schema (yıllardır değişmedi)

Fields:
- regularMarketPrice: Current spot price
- regularMarketTime: Unix timestamp
- timestamp[]: Daily series
- indicators.quote[0].close[]: Closing prices

ADR References:
- ADR-001: BIST primary data source
- ADR-019: Triple benchmark (XU100, BIST-30 ETF, S&P 500 ETF)
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

YAHOO_FINANCE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

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
# Data Classes
# ============================================================================

@dataclass
class MarketPrice:
    """Tek ticker için spot fiyat + meta."""
    ticker: str  # Original ticker (TUPRS, no suffix)
    yahoo_symbol: str  # Yahoo symbol (TUPRS.IS)
    spot_price: Decimal
    currency: str  # "TRY", "USD"
    exchange: str  # "IST", "NMS"
    timestamp: Optional[int]  # Unix ts

    @property
    def fetched_at(self) -> Optional[datetime]:
        if self.timestamp:
            return datetime.fromtimestamp(self.timestamp)
        return None


@dataclass
class HistoricalPrice:
    """Tek günlük close."""
    date: date
    close: Optional[Decimal]


# ============================================================================
# Helper: Symbol Conversion
# ============================================================================

def to_yahoo_symbol(ticker: str) -> str:
    """BIST ticker → Yahoo symbol (TUPRS → TUPRS.IS)."""
    ticker = ticker.upper().strip()
    if ticker.endswith(BIST_SUFFIX):
        return ticker
    return f"{ticker}{BIST_SUFFIX}"


# ============================================================================
# Single Ticker Fetch
# ============================================================================

async def fetch_spot_price(
    ticker: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Optional[MarketPrice]:
    """
    Tek ticker spot price.

    Args:
        ticker: BIST ticker (TUPRS, ARCLK, vb.)
        client: Optional httpx client (batch için)

    Returns:
        MarketPrice or None (eğer fetch fail)
    """
    yahoo_symbol = to_yahoo_symbol(ticker)
    url = YAHOO_FINANCE_URL.format(symbol=yahoo_symbol)

    own_client = False
    if client is None:
        client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=15.0,
        )
        own_client = True

    try:
        r = await client.get(url, params={"interval": "1d", "range": "5d"})
        if r.status_code != 200:
            logger.warning(f"{ticker}: HTTP {r.status_code}")
            return None

        data = r.json()
        chart = data.get("chart", {})

        if chart.get("error"):
            logger.warning(f"{ticker}: {chart['error']}")
            return None

        results = chart.get("result", [])
        if not results:
            return None

        meta = results[0].get("meta", {})
        spot = meta.get("regularMarketPrice")
        if spot is None:
            return None

        return MarketPrice(
            ticker=ticker.upper(),
            yahoo_symbol=yahoo_symbol,
            spot_price=Decimal(str(spot)),
            currency=meta.get("currency", "?"),
            exchange=meta.get("exchangeName", "?"),
            timestamp=meta.get("regularMarketTime"),
        )

    except Exception as e:
        logger.exception(f"{ticker} fetch failed")
        return None

    finally:
        if own_client:
            await client.aclose()


# ============================================================================
# Historical Fetch
# ============================================================================

async def fetch_historical(
    ticker: str,
    range_period: str = "5d",
    client: Optional[httpx.AsyncClient] = None,
) -> List[HistoricalPrice]:
    """
    Historical close prices.

    Args:
        ticker: BIST ticker
        range_period: '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max'
        client: Optional httpx client

    Returns:
        List of HistoricalPrice (ascending date)
    """
    yahoo_symbol = to_yahoo_symbol(ticker)
    url = YAHOO_FINANCE_URL.format(symbol=yahoo_symbol)

    own_client = False
    if client is None:
        client = httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=15.0)
        own_client = True

    try:
        r = await client.get(url, params={"interval": "1d", "range": range_period})
        r.raise_for_status()

        data = r.json()
        result = data["chart"]["result"][0]

        timestamps = result.get("timestamp", [])
        closes = result["indicators"]["quote"][0].get("close", [])

        history = []
        for ts, close in zip(timestamps, closes):
            d = datetime.fromtimestamp(ts).date()
            close_dec = Decimal(str(close)) if close is not None else None
            history.append(HistoricalPrice(date=d, close=close_dec))

        return history

    except Exception as e:
        logger.exception(f"{ticker} historical fetch failed")
        return []

    finally:
        if own_client:
            await client.aclose()


# ============================================================================
# Batch Fetch
# ============================================================================

async def fetch_batch_spot_prices(
    tickers: List[str],
    max_concurrent: int = 10,
) -> Dict[str, Optional[MarketPrice]]:
    """
    Paralel batch spot price fetch.

    Args:
        tickers: BIST ticker list
        max_concurrent: Concurrent semaphore (Yahoo OK with 10+)

    Returns:
        Dict ticker → MarketPrice (None for failed)
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_semaphore(client, ticker):
        async with semaphore:
            return ticker, await fetch_spot_price(ticker, client)

    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=15.0) as client:
        tasks = [fetch_with_semaphore(client, t) for t in tickers]
        results = await asyncio.gather(*tasks)

    return dict(results)
