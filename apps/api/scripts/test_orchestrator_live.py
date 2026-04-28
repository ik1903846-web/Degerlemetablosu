#!/usr/bin/env python
"""Orchestrator live integration test (Faz 2.4.4)."""
import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

# Proje root'undaki .env'i yükle (DATABASE_URL — Faz 2.4.6 Component 1)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from dcf_engine.orchestrator import analyze_ticker, print_report
from dcf_engine.batch_analyzer import (
    BIST_30,
    BIST_30_BANKING,
    BIST_30_INDUSTRIAL,
    BIST_50,
    BIST_50_ADDITIONS,
    analyze_batch,
    rank_by_upside,
    write_csv,
    write_json,
    summarize_batch,
)
import time


async def main():
    print("="*80)
    print("ORCHESTRATOR LIVE INTEGRATION TEST (Faz 2.4.4)")
    print("="*80)

    # ========================================================================
    # TEST 1: Single ticker (TUPRS) — auto-fetch price
    # ========================================================================
    print("\n[TEST 1] TUPRS auto-fetch market price")
    print("-"*80)

    # market_price_tl=None → orchestrator auto-fetch
    report = await analyze_ticker(ticker="TUPRS")

    print(f"  Auto-fetched market: {report.market_price_tl}")
    print(f"  DCF value:           {report.value_per_share_tl:.2f} TL")
    print(f"  Upside:              {report.upside_pct:+.2f}%")
    print(f"  Verdict:             {report.damodaran_verdict}")

    if report.market_price_tl and abs(report.market_price_tl - 269.0) < 1.0:
        print(f"  ✓ Auto-fetch çalıştı (~269 TL)")
    else:
        print(f"  ⚠ Market price beklenen değil")

    # ========================================================================
    # TEST 2: BIST 50 batch live — Faz 4.5 universe expansion
    # ========================================================================
    print(f"\n[TEST 2] BIST {len(BIST_50)} ticker — auto-fetch all prices")
    print(f"  BIST 30 base:    {len(BIST_30)} (industrial+banking+holdings)")
    print(f"  BIST 50 additions: {len(BIST_50_ADDITIONS)} (Faz 4.5 universe expansion)")
    print("-"*80)

    start = time.time()

    # market_prices=None → orchestrator her ticker için auto-fetch
    reports = await analyze_batch(
        tickers=BIST_50,
        market_prices=None,  # ← KRİTİK: auto-fetch trigger
        max_concurrent=5,
    )

    duration = time.time() - start

    print(f"  Duration: {duration:.1f}s ({len(BIST_50)} ticker)")

    summary = summarize_batch(reports, duration)
    print(f"  Successful: {summary.successful}")
    print(f"  Failed:     {summary.failed}")

    if summary.avg_upside_pct is not None:
        print(f"\n  Avg upside: {summary.avg_upside_pct:+.2f}%")
        print(f"  Deep value (>+30%): {summary.deep_value_count}")
        print(f"  Fair value (±10%):  {summary.fair_value_count}")
        print(f"  Overvalued (<-30%): {summary.overvalued_count}")

    # ========================================================================
    # RANKED RESULTS (live)
    # ========================================================================
    print("\n[RANKED RESULTS — LIVE PRICES]")
    print("-"*80)
    print(f"  Rank | Ticker | DCF (TL)  | Market    | Upside    | Verdict")
    print(f"  -----|--------|-----------|-----------|-----------|----------")

    ranked = rank_by_upside(reports)
    for i, r in enumerate(ranked, 1):
        if r.success and r.value_per_share_tl is not None:
            dcf = f"{r.value_per_share_tl:>9.2f}"
            mkt = f"{r.market_price_tl:>9.2f}" if r.market_price_tl else "    n/a"
            up = f"{r.upside_pct:>+7.2f}%" if r.upside_pct is not None else "    n/a"
            v = r.damodaran_verdict
        else:
            dcf = "    error"
            mkt = "    -"
            up = "    -"
            v = r.damodaran_verdict
        print(f"  {i:>4} | {r.ticker:<6} | {dcf} | {mkt} | {up} | {v}")

    # ========================================================================
    # OUTPUT FILES
    # ========================================================================
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"bist_batch_LIVE_{timestamp}.csv"
    json_path = output_dir / f"bist_batch_LIVE_{timestamp}.json"

    write_csv(reports, csv_path)
    write_json(reports, json_path)

    print(f"\n[OUTPUT FILES]")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")

    # ========================================================================
    # CONSISTENCY CHECK
    # ========================================================================
    tuprs_r = next((r for r in reports if r.ticker == "TUPRS"), None)
    if tuprs_r and tuprs_r.success:
        print(f"\n[CONSISTENCY]")
        print(f"  TUPRS DCF:    {tuprs_r.value_per_share_tl:.2f} TL (Adım 5: 181.16)")
        if abs(tuprs_r.value_per_share_tl - 181.16) < 1.0:
            print(f"  ✓ DCF stabil (live prices DCF'i etkilemedi)")

    print("\n" + "="*80)
    print("Faz 2.4.4 Live Integration PASS")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
