#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Cap Fetcher - Faz B2 Phase 1 Adım 2
============================================

Cross-holdings valuation için BIST listed ticker market_cap fetcher.

Veri kaynağı: yfinance (primary)
Cache: apps/api/_cache/market_caps/YYYY-MM-DD.json
TTL: 1 gün (her gün regen)

Usage:
    from apps.api.data_layer.market_cap_fetcher import (
        fetch_market_caps, get_market_cap
    )

    # Single
    mc = get_market_cap('TUPRS')

    # Batch
    mcs = fetch_market_caps(['TUPRS', 'KCHOL', 'AKBNK'])
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parents[1] / "_cache" / "market_caps"
TODAY = datetime.now(timezone.utc).date().isoformat()
CACHE_FILE = CACHE_DIR / f"{TODAY}.json"


@dataclass
class MarketCapRecord:
    ticker: str
    market_cap_tl: Optional[float]
    market_cap_usd: Optional[float]
    currency: str
    fetched_at: str
    source: str  # "yfinance" | "manual" | "stale_cache"
    error: Optional[str] = None


def _bist_suffix(ticker: str) -> str:
    """BIST ticker yfinance format: TUPRS -> TUPRS.IS"""
    return ticker if ticker.endswith(".IS") else f"{ticker}.IS"


def _yfinance_fetch(ticker: str) -> MarketCapRecord:
    """yfinance ile market cap çek."""
    try:
        import yfinance as yf
    except ImportError:
        return MarketCapRecord(
            ticker=ticker, market_cap_tl=None, market_cap_usd=None,
            currency="TRY", fetched_at=datetime.now(timezone.utc).isoformat(),
            source="yfinance", error="yfinance not installed"
        )

    try:
        yf_ticker = _bist_suffix(ticker)
        info = yf.Ticker(yf_ticker).info

        market_cap = info.get("marketCap")  # TL bazli BIST için
        if market_cap is None:
            return MarketCapRecord(
                ticker=ticker, market_cap_tl=None, market_cap_usd=None,
                currency="TRY", fetched_at=datetime.now(timezone.utc).isoformat(),
                source="yfinance", error="marketCap field missing"
            )

        return MarketCapRecord(
            ticker=ticker,
            market_cap_tl=float(market_cap),
            market_cap_usd=None,  # USD conversion ayrı (USD_TRY rate gerekli)
            currency="TRY",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            source="yfinance",
        )
    except Exception as e:
        return MarketCapRecord(
            ticker=ticker, market_cap_tl=None, market_cap_usd=None,
            currency="TRY", fetched_at=datetime.now(timezone.utc).isoformat(),
            source="yfinance", error=str(e)
        )


def _load_cache() -> dict:
    """Bugünkü cache dosyasını yükle (yoksa boş)."""
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Cache load fail: {e}")
        return {}


def _save_cache(cache: dict) -> None:
    """Cache dosyasına yaz (atomic)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CACHE_FILE)


def get_market_cap(ticker: str, force_refresh: bool = False) -> MarketCapRecord:
    """Tek ticker market cap (cache hit ise yfinance bypass)."""
    ticker = ticker.upper().strip()

    cache = _load_cache()
    if not force_refresh and ticker in cache:
        record = MarketCapRecord(**cache[ticker])
        if record.market_cap_tl is not None:
            return record

    record = _yfinance_fetch(ticker)
    cache[ticker] = asdict(record)
    _save_cache(cache)

    return record


def fetch_market_caps(tickers: list[str],
                      sleep_between: float = 0.3,
                      progress: bool = True) -> dict[str, MarketCapRecord]:
    """Batch fetch with rate limiting."""
    tickers = [t.upper().strip() for t in tickers]
    cache = _load_cache()

    results = {}
    fetch_count = 0
    cache_hit = 0
    error_count = 0

    for i, ticker in enumerate(tickers, 1):
        if ticker in cache and cache[ticker].get("market_cap_tl") is not None:
            results[ticker] = MarketCapRecord(**cache[ticker])
            cache_hit += 1
            if progress:
                logger.info(f"[{i}/{len(tickers)}] {ticker} cache hit")
            continue

        record = _yfinance_fetch(ticker)
        results[ticker] = record
        cache[ticker] = asdict(record)
        fetch_count += 1

        if record.error:
            error_count += 1
            if progress:
                logger.warning(f"[{i}/{len(tickers)}] {ticker} ERROR: {record.error}")
        else:
            if progress:
                logger.info(f"[{i}/{len(tickers)}] {ticker} ${record.market_cap_tl:,.0f} TL")

        # Rate limit
        if fetch_count % 5 == 0:
            _save_cache(cache)

        time.sleep(sleep_between)

    _save_cache(cache)

    if progress:
        logger.info(f"Fetch summary: cache_hit={cache_hit}, fetched={fetch_count}, errors={error_count}")

    return results


def _smoke_test() -> int:
    """Standalone smoke test."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s"
    )

    test_tickers = ['TUPRS', 'KCHOL', 'AKBNK', 'ARCLK', 'EREGL']

    print("=" * 60)
    print("Market Cap Fetcher - Smoke Test")
    print("=" * 60)
    print(f"Test tickers: {test_tickers}")
    print(f"Cache: {CACHE_FILE}")
    print()

    results = fetch_market_caps(test_tickers, sleep_between=0.5)

    print()
    print("Results:")
    print(f"{'Ticker':8} | {'Market Cap TL':>20} | {'Source':12} | {'Error':30}")
    print("-" * 80)
    for ticker, r in results.items():
        mc_str = f"{r.market_cap_tl:,.0f}" if r.market_cap_tl else "N/A"
        err = (r.error or "")[:28]
        print(f"{ticker:8} | {mc_str:>20} | {r.source:12} | {err:30}")

    print()
    success = sum(1 for r in results.values() if r.market_cap_tl is not None)
    print(f"Success: {success}/{len(results)}")

    return 0 if success == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(_smoke_test())
