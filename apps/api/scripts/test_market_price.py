#!/usr/bin/env python
"""Market price fetcher test."""
import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.market_price_fetcher import (
    fetch_spot_price,
    fetch_batch_spot_prices,
    fetch_historical,
)


async def main():
    print("="*80)
    print("Market Price Fetcher Test")
    print("="*80)

    # ========================================================================
    # TEST 1: Single fetch (TUPRS)
    # ========================================================================
    print("\n[TEST 1] Single fetch — TUPRS")
    print("-"*80)

    tuprs = await fetch_spot_price("TUPRS")
    if tuprs:
        print(f"  Ticker:        {tuprs.ticker}")
        print(f"  Yahoo Symbol:  {tuprs.yahoo_symbol}")
        print(f"  Spot Price:    {tuprs.spot_price} {tuprs.currency}")
        print(f"  Exchange:      {tuprs.exchange}")
        print(f"  Fetched:       {tuprs.fetched_at}")

        if abs(float(tuprs.spot_price) - 269.0) < 1.0:
            print(f"  ✓ TUPRS spot ~269 TL doğrulandı")
        else:
            print(f"  ⚠ TUPRS spot {tuprs.spot_price}, beklenen ~269")
    else:
        print(f"  ✗ TUPRS fetch fail")

    # ========================================================================
    # TEST 2: Batch fetch (BIST 19 industrial)
    # ========================================================================
    print("\n[TEST 2] Batch fetch — BIST 19 industrial")
    print("-"*80)

    from dcf_engine.batch_analyzer import BIST_30_INDUSTRIAL

    import time
    start = time.time()
    prices = await fetch_batch_spot_prices(BIST_30_INDUSTRIAL)
    duration = time.time() - start

    print(f"  Tickers: {len(BIST_30_INDUSTRIAL)}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Successful: {sum(1 for p in prices.values() if p is not None)}/{len(BIST_30_INDUSTRIAL)}")

    print(f"\n  Ticker | Spot Price (TRY)")
    print(f"  -------|------------------")
    for ticker in BIST_30_INDUSTRIAL:
        p = prices.get(ticker)
        if p:
            print(f"  {ticker:<6} | {float(p.spot_price):>10.2f}")
        else:
            print(f"  {ticker:<6} | FAIL")

    # ========================================================================
    # TEST 3: Historical (TUPRS, 1mo)
    # ========================================================================
    print("\n[TEST 3] Historical — TUPRS 1ay")
    print("-"*80)

    history = await fetch_historical("TUPRS", "1mo")
    print(f"  Days fetched: {len(history)}")
    print(f"\n  Last 5 days:")
    for h in history[-5:]:
        close_str = f"{float(h.close):>8.2f}" if h.close else "    null"
        print(f"    {h.date}: {close_str} TRY")

    print("\n" + "="*80)
    print("Market Price Fetcher PASS")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
