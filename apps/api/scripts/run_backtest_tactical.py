#!/usr/bin/env python
"""
Tactical Regime Overlay Backtest — Faz 4.8 (ADR-042).

Mevcut Faz 4.5/4.7 backtest'i tactical overlay ile re-run:
  Per-quarter regime detection (VIX-based)
  → sleeve_multiplier (panic 0.75, normal 1.0)
  → cash escalation (panic %15-25, normal %2-15)

Output: backtest_results_TACTICAL_*.{csv,json,md} + USD versions
"""

import asyncio
import csv
import json
import sys
from datetime import date, datetime
from dataclasses import asdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.historical_data import (
    fetch_batch_quarterly_close,
    quarter_end_calendar,
)
from backtest.benchmark_data import (
    fetch_triple_benchmark,
    fetch_vix_quarterly,
)
from backtest.point_in_time import load_three_profiles, BIAS_NOTE, LOOK_AHEAD_BIAS
from backtest.simulation import run_backtest, benchmark_returns
from backtest.performance import compute_metrics
from backtest.regime_detector import regime_calendar, Regime
from backtest.usd_conversion import (
    fetch_usd_try_quarterly,
    convert_quarterly_returns_to_usd,
)
from backtest.performance_usd import compute_metrics_usd
from portfolio.portfolio_construction import REGIME_OVERLAY


START_DATE = date(2021, 6, 30)
END_DATE = date(2026, 3, 31)


def _outputs_dir() -> Path:
    return Path(__file__).parent.parent / "outputs"


async def main() -> int:
    print("\n" + "#" * 80)
    print("# TACTICAL REGIME OVERLAY BACKTEST — Faz 4.8 (ADR-042)")
    print(f"# Period: {START_DATE} → {END_DATE}")
    print("# Sleeve multiplier: normal 1.0 / moderate 0.95 / significant 0.85 / panic 0.75")
    print("#" * 80)

    # 1. Load 3 portfolio snapshots
    print("\n[1/5] 3 risk profile snapshot yükleniyor...")
    snapshots = load_three_profiles()
    all_tickers = set()
    for snap in snapshots.values():
        all_tickers.update(snap.position_weights.keys())

    # 2. Fetch ticker prices + benchmarks + VIX
    print(f"\n[2/5] Price + benchmark + VIX fetch...")
    prices = await fetch_batch_quarterly_close(
        list(all_tickers), START_DATE, END_DATE, max_concurrent=8,
    )
    triple = await fetch_triple_benchmark(START_DATE, END_DATE)
    vix = await fetch_vix_quarterly(START_DATE, END_DATE)
    fx = await fetch_usd_try_quarterly(START_DATE, END_DATE)

    # 3. Regime calendar
    qends = sorted(quarter_end_calendar(START_DATE, END_DATE))
    rcal = regime_calendar(vix)
    regime_count = {r.value: 0 for r in Regime}
    for rt in rcal:
        regime_count[rt.regime.value] += 1
    print(f"\n[3/5] Regime calendar ({len(rcal)} quarter):")
    for k, v in regime_count.items():
        print(f"    {k:20s}: {v} quarter")

    # 4. Run STATIC + TACTICAL backtests
    print("\n[4/5] STATIC vs TACTICAL backtest comparison...")
    print(f"  {'Profile':<13s} {'Cost':<10s} {'Mode':<8s} {'TWR':>10s} {'Ann':>9s} {'Sharpe':>7s} {'Max DD':>8s}")

    results = {}  # (profile, cost, mode) → (BacktestResult, PerformanceMetrics)

    for profile in ("konservatif", "dengeli", "agresif"):
        snap = snapshots[profile]
        for cost in ("zero", "realistic"):
            # STATIC (Faz 4.7 baseline)
            bt_static = run_backtest(snap, prices, qends, cost_model=cost)
            m_static = compute_metrics(bt_static.quarterly_returns)
            results[(profile, cost, "static")] = (bt_static, m_static)

            # TACTICAL (Faz 4.8 regime overlay)
            bt_tact = run_backtest(
                snap, prices, qends, cost_model=cost,
                regime_overlay=REGIME_OVERLAY,
                regime_calendar=rcal,
            )
            m_tact = compute_metrics(bt_tact.quarterly_returns)
            results[(profile, cost, "tactical")] = (bt_tact, m_tact)

            print(f"  {profile:<13s} {cost:<10s} static   "
                  f"{m_static.cumulative_return*100:>+8.2f}% "
                  f"{m_static.annualized_return*100:>+7.2f}% "
                  f"{m_static.sharpe:>6.2f} "
                  f"{m_static.max_drawdown*100:>+7.2f}%")
            print(f"  {profile:<13s} {cost:<10s} tactical "
                  f"{m_tact.cumulative_return*100:>+8.2f}% "
                  f"{m_tact.annualized_return*100:>+7.2f}% "
                  f"{m_tact.sharpe:>6.2f} "
                  f"{m_tact.max_drawdown*100:>+7.2f}%")

    # 5. USD conversion + benchmark
    print("\n[5/5] USD-basis conversion + benchmark...")
    bench_metrics = {}
    for name in ("XU100", "XU030", "SPY"):
        rets_tl = benchmark_returns(triple[name], qends)
        if name == "SPY":
            rets_usd = rets_tl
        else:
            rets_usd = convert_quarterly_returns_to_usd(rets_tl, fx, qends)
        m_usd = compute_metrics_usd(rets_usd)
        bench_metrics[name] = m_usd
        print(f"  {name:6s}: USD ann {m_usd.annualized_return_usd*100:+.2f}%/yr "
              f"Sharpe {m_usd.sharpe_usd:.2f} DD {m_usd.max_drawdown_usd*100:+.2f}%")

    # USD basis for portfolios
    print("\n  Portfolio USD basis (static vs tactical):")
    print(f"  {'Profile':<13s} {'Cost':<10s} {'Static USD':>12s} {'Tactical USD':>14s} {'Δ':>8s} {'DD Static':>11s} {'DD Tact':>11s}")

    usd_metrics = {}
    for profile in ("konservatif", "dengeli", "agresif"):
        for cost in ("zero", "realistic"):
            # static
            bt_s, m_s = results[(profile, cost, "static")]
            usd_s = convert_quarterly_returns_to_usd(bt_s.quarterly_returns, fx, qends)
            mu_s = compute_metrics_usd(usd_s)
            usd_metrics[(profile, cost, "static")] = mu_s

            # tactical
            bt_t, m_t = results[(profile, cost, "tactical")]
            usd_t = convert_quarterly_returns_to_usd(bt_t.quarterly_returns, fx, qends)
            mu_t = compute_metrics_usd(usd_t)
            usd_metrics[(profile, cost, "tactical")] = mu_t

            delta = mu_t.annualized_return_usd - mu_s.annualized_return_usd
            print(
                f"  {profile:<13s} {cost:<10s} "
                f"{mu_s.annualized_return_usd*100:>+10.2f}%   "
                f"{mu_t.annualized_return_usd*100:>+12.2f}%   "
                f"{delta*100:>+6.2f}pp "
                f"{mu_s.max_drawdown_usd*100:>+10.2f}%  "
                f"{mu_t.max_drawdown_usd*100:>+10.2f}%"
            )

    # 6. Persist outputs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = _outputs_dir()

    # CSV summary
    csv_path = out_dir / f"backtest_results_TACTICAL_{timestamp}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["# REELDEĞER Tactical Regime Overlay Backtest 2021-Q2 → 2026-Q1"])
        w.writerow([f"# ADR-042: regime-adaptive cash escalation"])
        w.writerow([])
        w.writerow(["category", "label", "cost_model", "mode",
                     "tl_cum_pct", "tl_ann_pct", "usd_cum_pct", "usd_ann_pct",
                     "sharpe_tl", "max_dd_tl_pct", "sharpe_usd", "max_dd_usd_pct"])
        for profile in ("konservatif", "dengeli", "agresif"):
            for cost in ("zero", "realistic"):
                for mode in ("static", "tactical"):
                    bt, m_tl = results[(profile, cost, mode)]
                    m_usd = usd_metrics[(profile, cost, mode)]
                    w.writerow([
                        "portfolio", profile, cost, mode,
                        f"{m_tl.cumulative_return*100:.2f}",
                        f"{m_tl.annualized_return*100:.2f}",
                        f"{m_usd.cumulative_return_usd*100:.2f}",
                        f"{m_usd.annualized_return_usd*100:.2f}",
                        f"{m_tl.sharpe:.3f}" if m_tl.sharpe else "",
                        f"{m_tl.max_drawdown*100:.2f}",
                        f"{m_usd.sharpe_usd:.3f}" if m_usd.sharpe_usd else "",
                        f"{m_usd.max_drawdown_usd*100:.2f}",
                    ])
        for name, m in bench_metrics.items():
            w.writerow([
                "benchmark", name, "n/a", "n/a",
                "", "",
                f"{m.cumulative_return_usd*100:.2f}",
                f"{m.annualized_return_usd*100:.2f}",
                "", "",
                f"{m.sharpe_usd:.3f}" if m.sharpe_usd else "",
                f"{m.max_drawdown_usd*100:.2f}",
            ])

    # JSON full diagnostic
    json_path = out_dir / f"backtest_results_TACTICAL_{timestamp}.json"
    diag = {
        "metadata": {
            "timestamp": timestamp,
            "period_start": START_DATE.isoformat(),
            "period_end": END_DATE.isoformat(),
            "fx_devaluation": fx[max(fx)] / fx[min(fx)],
            "look_ahead_bias": LOOK_AHEAD_BIAS,
            "adr_reference": "ADR-042 (tactical regime overlay)",
            "regime_overlay": REGIME_OVERLAY,
        },
        "regime_calendar": [
            {"quarter_end": rt.quarter_end.isoformat(),
             "vix": rt.vix, "regime": rt.regime.value}
            for rt in rcal
        ],
        "regime_summary": regime_count,
        "comparison": [
            {
                "profile": p, "cost": c, "mode": m,
                "tl_cumulative": results[(p, c, m)][1].cumulative_return,
                "tl_annualized": results[(p, c, m)][1].annualized_return,
                "tl_sharpe": results[(p, c, m)][1].sharpe,
                "tl_max_dd": results[(p, c, m)][1].max_drawdown,
                "usd_cumulative": usd_metrics[(p, c, m)].cumulative_return_usd,
                "usd_annualized": usd_metrics[(p, c, m)].annualized_return_usd,
                "usd_sharpe": usd_metrics[(p, c, m)].sharpe_usd,
                "usd_max_dd": usd_metrics[(p, c, m)].max_drawdown_usd,
            }
            for p in ("konservatif", "dengeli", "agresif")
            for c in ("zero", "realistic")
            for m in ("static", "tactical")
        ],
        "benchmarks_usd": [
            {
                "label": name,
                "usd_annualized": m.annualized_return_usd,
                "usd_sharpe": m.sharpe_usd,
                "usd_max_dd": m.max_drawdown_usd,
            }
            for name, m in bench_metrics.items()
        ],
    }
    json_path.write_text(json.dumps(diag, indent=2, default=str), encoding="utf-8")

    print(f"\n[OUTPUT FILES]")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")

    print("\n" + "#" * 80)
    print("# TACTICAL OVERLAY BACKTEST COMPLETE")
    print("#" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
