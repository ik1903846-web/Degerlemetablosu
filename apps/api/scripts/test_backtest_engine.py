#!/usr/bin/env python
"""
Backtest engine integration test — Faz 4 ADIM 3.

5 TEST:
  1) Historical data fetch (TUPRS daily 2021-Q2 → 2026-Q1, quarter resample)
  2) Triple benchmark + VIX (XU100/XU030/SPY + VIX quarterly)
  3) Single quarter rebalance (Q1 → Q2 2024 sample)
  4) Full 20-quarter simulation (Dengeli zero-cost)
  5) Cost model comparison (Dengeli zero vs realistic)
"""

import asyncio
import sys
import io
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.historical_data import (
    fetch_quarterly_close,
    quarter_end_calendar,
    fetch_batch_quarterly_close,
)
from backtest.benchmark_data import (
    fetch_triple_benchmark,
    fetch_vix_quarterly,
)
from backtest.point_in_time import load_portfolio_snapshot
from backtest.simulation import run_backtest, benchmark_returns
from backtest.performance import compute_metrics, compute_beta


# Faz 4 backtest period (Q1 answer (b))
START_DATE = date(2021, 6, 30)   # 2021-Q2 (start = Q2 quarter-end)
END_DATE = date(2026, 3, 31)     # 2026-Q1 (end = Q1 quarter-end)


async def test_1_historical_data() -> bool:
    print("\n" + "=" * 70)
    print("TEST 1 — Historical data fetch (TUPRS quarterly)")
    print("=" * 70)

    qclose = await fetch_quarterly_close("TUPRS", START_DATE, END_DATE)
    print(f"  Quarter-end count: {len(qclose)}")
    qends = sorted(qclose.keys())
    if qends:
        print(f"  First quarter:     {qends[0]} = {qclose[qends[0]]:.2f} TL")
        print(f"  Last quarter:      {qends[-1]} = {qclose[qends[-1]]:.2f} TL")

    expected_qends = quarter_end_calendar(START_DATE, END_DATE)
    print(f"  Expected calendar quarter-ends: {len(expected_qends)}")

    checks = [
        ("Quarter count >= 18", len(qclose) >= 18, True),
        ("Quarter count <= 21", len(qclose) <= 21, True),
        ("First quarter >= 2021-06-30",
         qends[0] >= date(2021, 6, 30) if qends else False, True),
        ("Last quarter <= 2026-03-31",
         qends[-1] <= date(2026, 3, 31) if qends else False, True),
    ]
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}: {actual}")
        if not ok:
            all_pass = False
    return all_pass


async def test_2_benchmarks() -> bool:
    print("\n" + "=" * 70)
    print("TEST 2 — Triple benchmark + VIX quarterly")
    print("=" * 70)

    triple = await fetch_triple_benchmark(START_DATE, END_DATE)
    print(f"  Benchmarks fetched: {list(triple.keys())}")
    for name, series in triple.items():
        qends = sorted(series.keys())
        if qends:
            print(f"  {name:6s}: {len(series)} quarter, "
                  f"first={qends[0]} ({series[qends[0]]:.2f}), "
                  f"last={qends[-1]} ({series[qends[-1]]:.2f})")

    vix = await fetch_vix_quarterly(START_DATE, END_DATE)
    print(f"  VIX:    {len(vix)} quarter")
    if vix:
        latest_q = sorted(vix.keys())[-1]
        print(f"          last = {latest_q} → VIX {vix[latest_q]:.2f}")

    checks = [
        ("XU100 fetched", "XU100" in triple, True),
        ("XU030 fetched", "XU030" in triple, True),
        ("SPY fetched", "SPY" in triple, True),
        ("VIX fetched", len(vix) > 0, True),
        ("XU100 >= 18 quarter", len(triple.get("XU100", {})) >= 18, True),
    ]
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}: {actual}")
        if not ok:
            all_pass = False
    return all_pass


async def test_3_single_quarter() -> bool:
    print("\n" + "=" * 70)
    print("TEST 3 — Single quarter rebalance (Dengeli, Q1→Q2 2024)")
    print("=" * 70)

    snap = load_portfolio_snapshot("dengeli")
    tickers = list(snap.position_weights.keys())
    print(f"  Snapshot tickers: {len(tickers)}")
    print(f"  Cash weight:      {snap.cash_weight*100:.2f}%")

    q_start = date(2024, 3, 31)
    q_end = date(2024, 6, 30)

    # Yalnız bu 2 quarter prices
    prices_raw = await fetch_batch_quarterly_close(
        tickers, q_start, q_end, max_concurrent=8,
    )
    # ticker → {date: float}
    print(f"  Prices fetched: {sum(1 for p in prices_raw.values() if p)}/{len(tickers)}")

    # Run backtest 1-period
    result = run_backtest(snap, prices_raw, [q_start, q_end], cost_model="zero")
    print(f"  Quarter return: {result.quarterly_returns[0]*100:+.2f}%")
    print(f"  Turnover:       {result.quarter_results[0].turnover*100:.2f}%")
    print(f"  Skipped tickers: {result.quarter_results[0].skipped_tickers}")

    checks = [
        ("Has 1 quarter result", len(result.quarter_results), 1),
        ("Return is float",
         isinstance(result.quarterly_returns[0], float), True),
    ]
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}: {actual}")
        if not ok:
            all_pass = False
    return all_pass


async def test_4_full_simulation() -> bool:
    print("\n" + "=" * 70)
    print("TEST 4 — Full 20-quarter simulation (Dengeli, zero-cost)")
    print("=" * 70)

    snap = load_portfolio_snapshot("dengeli")
    tickers = list(snap.position_weights.keys())

    prices = await fetch_batch_quarterly_close(
        tickers, START_DATE, END_DATE, max_concurrent=8,
    )

    qends = sorted(quarter_end_calendar(START_DATE, END_DATE))
    print(f"  Quarter-end count: {len(qends)} (expect 20-21)")

    result = run_backtest(snap, prices, qends, cost_model="zero")
    metrics = compute_metrics(result.quarterly_returns)

    print(f"\n  Cumulative TWR:   {metrics.cumulative_return*100:+.2f}%")
    print(f"  Annualized:       {metrics.annualized_return*100:+.2f}%/yr")
    print(f"  Annual vol:       {metrics.annualized_volatility*100:.2f}%")
    print(f"  Sharpe:           {metrics.sharpe:.2f}" if metrics.sharpe else "  Sharpe: n/a")
    print(f"  Sortino:          {metrics.sortino:.2f}" if metrics.sortino else "  Sortino: n/a")
    print(f"  Max drawdown:     {metrics.max_drawdown*100:+.2f}%")
    print(f"  Best quarter:     {metrics.best_quarter*100:+.2f}%")
    print(f"  Worst quarter:    {metrics.worst_quarter*100:+.2f}%")
    print(f"  +Q / -Q:          {metrics.n_positive_quarters}/{metrics.n_negative_quarters}")

    checks = [
        ("Quarter results >= 18", len(result.quarter_results) >= 18, True),
        ("Cumulative return is float",
         isinstance(metrics.cumulative_return, float), True),
        ("Sharpe computed", metrics.sharpe is not None, True),
        ("Max DD <= 0", metrics.max_drawdown <= 0, True),
    ]
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}: {actual}")
        if not ok:
            all_pass = False
    return all_pass


async def test_5_cost_comparison() -> bool:
    print("\n" + "=" * 70)
    print("TEST 5 — Cost model comparison (Dengeli zero vs realistic)")
    print("=" * 70)

    snap = load_portfolio_snapshot("dengeli")
    tickers = list(snap.position_weights.keys())
    prices = await fetch_batch_quarterly_close(
        tickers, START_DATE, END_DATE, max_concurrent=8,
    )
    qends = sorted(quarter_end_calendar(START_DATE, END_DATE))

    r_zero = run_backtest(snap, prices, qends, cost_model="zero")
    r_real = run_backtest(snap, prices, qends, cost_model="realistic")

    m_zero = compute_metrics(r_zero.quarterly_returns)
    m_real = compute_metrics(r_real.quarterly_returns)

    diff_cum = m_zero.cumulative_return - m_real.cumulative_return
    diff_ann = m_zero.annualized_return - m_real.annualized_return

    print(f"\n  Zero cost:")
    print(f"    Cumulative: {m_zero.cumulative_return*100:+.2f}%")
    print(f"    Annualized: {m_zero.annualized_return*100:+.2f}%/yr")
    print(f"  Realistic cost:")
    print(f"    Cumulative: {m_real.cumulative_return*100:+.2f}%")
    print(f"    Annualized: {m_real.annualized_return*100:+.2f}%/yr")
    print(f"  Cost erosion:")
    print(f"    Δ cumulative: {diff_cum*100:.2f}pp")
    print(f"    Δ annualized: {diff_ann*100:.2f}pp/yr")
    print(f"    Total trading cost (5y): {r_real.total_trading_cost*100:.2f}%")
    print(f"    Total tax-drag (5y):     {r_real.total_tax_drag*100:.2f}%")

    checks = [
        ("Zero >= Realistic (cumulative)",
         m_zero.cumulative_return >= m_real.cumulative_return, True),
        ("Cost erosion > 0", diff_ann > 0, True),
        ("Trading cost > 0 in realistic",
         r_real.total_trading_cost > 0, True),
    ]
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}: {actual}")
        if not ok:
            all_pass = False
    return all_pass


async def main() -> int:
    print("\n" + "#" * 80)
    print("# Backtest Engine TEST (Faz 4 ADIM 3 — 5 test)")
    print("# Period: 2021-Q2 → 2026-Q1 (20 quarter)")
    print("#" * 80)

    results = [
        ("TEST 1 Historical data fetch", await test_1_historical_data()),
        ("TEST 2 Triple benchmark + VIX", await test_2_benchmarks()),
        ("TEST 3 Single quarter rebalance", await test_3_single_quarter()),
        ("TEST 4 Full 20-quarter simulation", await test_4_full_simulation()),
        ("TEST 5 Cost model comparison", await test_5_cost_comparison()),
    ]

    print("\n" + "#" * 80)
    print("# ÖZET")
    print("#" * 80)
    for name, ok in results:
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}")

    all_pass = all(ok for _, ok in results)
    print(f"\n  Toplam: {sum(1 for _, ok in results if ok)}/{len(results)}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
