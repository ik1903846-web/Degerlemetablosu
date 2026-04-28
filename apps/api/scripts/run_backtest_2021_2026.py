#!/usr/bin/env python
"""
Production Backtest Runner — Faz 4 ADIM 4.

3 risk profile × 2 cost model = 6 backtest run.
Triple benchmark (XU100/XU030/SPY) + VIX regime calendar.
Output: CSV + JSON + Markdown summary.
"""

import asyncio
import csv
import json
import sys
from dataclasses import asdict
from datetime import date, datetime
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
from backtest.point_in_time import (
    load_three_profiles,
    BIAS_NOTE,
    LOOK_AHEAD_BIAS,
)
from backtest.simulation import run_backtest, benchmark_returns
from backtest.performance import compute_metrics, compute_beta
from backtest.regime_detector import regime_calendar, Regime
from backtest.attribution import sleeve_attribution, regime_breakdown
from backtest.failure_metrics import compute_failure_metrics


# Faz 4 backtest period
START_DATE = date(2021, 6, 30)
END_DATE = date(2026, 3, 31)


# ============================================================================
# Helpers
# ============================================================================

def _outputs_dir() -> Path:
    return Path(__file__).parent.parent / "outputs"


def _research_dir() -> Path:
    return Path(__file__).parent.parent / "_research_findings"


# ============================================================================
# Main Pipeline
# ============================================================================

async def main() -> int:
    print("\n" + "#" * 80)
    print("# REELDEĞER Backtest Production Run — Faz 4 ADIM 4")
    print(f"# Period: {START_DATE} → {END_DATE}")
    print(f"# 3 risk profile × 2 cost model = 6 backtest")
    print(f"# Look-ahead bias: {LOOK_AHEAD_BIAS} (Damodaran Lesson #7)")
    print("#" * 80)

    # ── 1. Load 3 portfolio snapshots ──
    print("\n[1/6] 3 risk profile snapshot yükleniyor...")
    snapshots = load_three_profiles()
    all_tickers = set()
    for snap in snapshots.values():
        all_tickers.update(snap.position_weights.keys())
    print(f"  Tickers (unique): {sorted(all_tickers)}")

    # ── 2. Fetch ticker prices ──
    print(f"\n[2/6] {len(all_tickers)} ticker quarterly close fetch...")
    prices = await fetch_batch_quarterly_close(
        list(all_tickers), START_DATE, END_DATE, max_concurrent=8,
    )
    fetched = sum(1 for p in prices.values() if p)
    print(f"  Fetched: {fetched}/{len(all_tickers)} ticker")

    # ── 3. Fetch benchmarks + VIX ──
    print("\n[3/6] Triple benchmark (XU100/XU030/SPY) + VIX...")
    triple = await fetch_triple_benchmark(START_DATE, END_DATE)
    vix = await fetch_vix_quarterly(START_DATE, END_DATE)
    for name, series in triple.items():
        print(f"  {name:6s}: {len(series)} quarter")
    print(f"  VIX:    {len(vix)} quarter")

    # ── 4. Run 3×2 = 6 backtests ──
    print("\n[4/6] 6 backtest run...")
    qends = sorted(quarter_end_calendar(START_DATE, END_DATE))

    # Regime calendar
    rcal = regime_calendar(vix)
    regime_summary = {r.value: 0 for r in Regime}
    for rt in rcal:
        regime_summary[rt.regime.value] += 1
    print(f"\n  Regime calendar ({len(rcal)} quarter):")
    for k, v in regime_summary.items():
        print(f"    {k:20s}: {v} quarter")

    backtests = {}  # (profile, cost) → BacktestResult
    metrics = {}    # (profile, cost) → PerformanceMetrics

    for profile in ("konservatif", "dengeli", "agresif"):
        snap = snapshots[profile]
        for cost in ("zero", "realistic"):
            bt = run_backtest(snap, prices, qends, cost_model=cost)
            mt = compute_metrics(bt.quarterly_returns)
            backtests[(profile, cost)] = bt
            metrics[(profile, cost)] = mt
            print(f"\n  [{profile:13s} {cost:9s}] "
                  f"TWR {mt.cumulative_return*100:+7.2f}% | "
                  f"ann {mt.annualized_return*100:+6.2f}%/yr | "
                  f"Sharpe {mt.sharpe:.2f} | "
                  f"DD {mt.max_drawdown*100:+6.2f}%")

    # ── 5. Benchmark metrics ──
    print("\n[5/6] Benchmark performance...")
    bench_metrics = {}
    for name in ("XU100", "XU030", "SPY"):
        rets = benchmark_returns(triple[name], qends)
        m = compute_metrics(rets)
        bench_metrics[name] = (rets, m)
        print(f"  {name:6s}: TWR {m.cumulative_return*100:+7.2f}% | "
              f"ann {m.annualized_return*100:+6.2f}%/yr | "
              f"vol {m.annualized_volatility*100:.2f}% | "
              f"Sharpe {m.sharpe:.2f} | "
              f"DD {m.max_drawdown*100:+6.2f}%")

    # ── 6. Per-regime + per-sleeve attribution ──
    print("\n[6/6] Attribution + failure metrics...")

    # Attribution dict (zero-cost dengeli baseline)
    bt_dengeli_zero = backtests[("dengeli", "zero")]
    sleeve_attr = sleeve_attribution(
        bt_dengeli_zero, snapshots["dengeli"].sleeves,
    )
    regime_attr = regime_breakdown(bt_dengeli_zero, rcal)
    failure = {p: compute_failure_metrics(backtests[(p, "realistic")])
               for p in ("konservatif", "dengeli", "agresif")}

    # ── 7. Persist outputs ──
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = _outputs_dir()
    out_dir.mkdir(exist_ok=True)

    # CSV: per profile/cost summary
    csv_path = out_dir / f"backtest_results_{timestamp}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["# REELDEĞER Backtest 2021-Q2 → 2026-Q1 (look-ahead bias)"])
        w.writerow([])
        w.writerow(["category", "label", "cost_model",
                     "cumulative_twr_pct", "annualized_pct",
                     "annual_vol_pct", "sharpe", "sortino",
                     "max_drawdown_pct", "best_q_pct", "worst_q_pct",
                     "n_pos_q", "n_neg_q"])
        for profile in ("konservatif", "dengeli", "agresif"):
            for cost in ("zero", "realistic"):
                m = metrics[(profile, cost)]
                w.writerow([
                    "portfolio", profile, cost,
                    f"{m.cumulative_return*100:.2f}",
                    f"{m.annualized_return*100:.2f}",
                    f"{m.annualized_volatility*100:.2f}",
                    f"{m.sharpe:.3f}" if m.sharpe else "",
                    f"{m.sortino:.3f}" if m.sortino else "",
                    f"{m.max_drawdown*100:.2f}",
                    f"{m.best_quarter*100:.2f}",
                    f"{m.worst_quarter*100:.2f}",
                    m.n_positive_quarters, m.n_negative_quarters,
                ])
        for name, (rets, m) in bench_metrics.items():
            w.writerow([
                "benchmark", name, "n/a",
                f"{m.cumulative_return*100:.2f}",
                f"{m.annualized_return*100:.2f}",
                f"{m.annualized_volatility*100:.2f}",
                f"{m.sharpe:.3f}" if m.sharpe else "",
                f"{m.sortino:.3f}" if m.sortino else "",
                f"{m.max_drawdown*100:.2f}",
                f"{m.best_quarter*100:.2f}",
                f"{m.worst_quarter*100:.2f}",
                m.n_positive_quarters, m.n_negative_quarters,
            ])

    # JSON: full diagnostic
    json_path = out_dir / f"backtest_results_{timestamp}.json"
    diag = {
        "metadata": {
            "timestamp": timestamp,
            "period_start": START_DATE.isoformat(),
            "period_end": END_DATE.isoformat(),
            "n_quarters": len(qends),
            "look_ahead_bias": LOOK_AHEAD_BIAS,
            "bias_note": BIAS_NOTE,
        },
        "regime_calendar": [
            {"quarter_end": rt.quarter_end.isoformat(),
             "vix": rt.vix, "regime": rt.regime.value}
            for rt in rcal
        ],
        "regime_summary": regime_summary,
        "backtests": [
            {
                "profile": profile,
                "cost_model": cost,
                "cumulative_twr": metrics[(profile, cost)].cumulative_return,
                "annualized_return": metrics[(profile, cost)].annualized_return,
                "annual_vol": metrics[(profile, cost)].annualized_volatility,
                "sharpe": metrics[(profile, cost)].sharpe,
                "sortino": metrics[(profile, cost)].sortino,
                "max_drawdown": metrics[(profile, cost)].max_drawdown,
                "n_quarters": metrics[(profile, cost)].n_quarters,
                "total_turnover": backtests[(profile, cost)].total_turnover,
                "total_trading_cost": backtests[(profile, cost)].total_trading_cost,
                "total_tax_drag": backtests[(profile, cost)].total_tax_drag,
                "quarterly_returns": backtests[(profile, cost)].quarterly_returns,
            }
            for profile in ("konservatif", "dengeli", "agresif")
            for cost in ("zero", "realistic")
        ],
        "benchmarks": [
            {
                "label": name,
                "cumulative_twr": m.cumulative_return,
                "annualized_return": m.annualized_return,
                "annual_vol": m.annualized_volatility,
                "sharpe": m.sharpe,
                "max_drawdown": m.max_drawdown,
                "quarterly_returns": rets,
            }
            for name, (rets, m) in bench_metrics.items()
        ],
        "attribution_dengeli_zero": {
            "sleeve": [asdict(s) for s in sleeve_attr],
            "regime": [
                {**asdict(r), "regime": r.regime.value,
                 "quarter_ends": [d.isoformat() for d in r.quarter_ends]}
                for r in regime_attr
            ],
        },
        "failure_metrics": {
            p: asdict(failure[p])
            for p in ("konservatif", "dengeli", "agresif")
        },
    }
    json_path.write_text(json.dumps(diag, indent=2, default=str), encoding="utf-8")

    # Markdown summary
    md_path = out_dir / f"backtest_summary_{timestamp}.md"
    md = []
    md.append(f"# REELDEĞER Backtest Summary — {timestamp}")
    md.append(f"\n**Period:** {START_DATE} → {END_DATE} ({len(qends)} quarter-end)")
    md.append(f"**Look-ahead bias:** `{LOOK_AHEAD_BIAS}` (Damodaran Lesson #7)\n")

    md.append("## Triple Benchmark\n")
    md.append("| Benchmark | Cumulative | Annualized | Vol | Sharpe | Max DD |")
    md.append("|-----------|-----------:|-----------:|----:|-------:|-------:|")
    for name, (_, m) in bench_metrics.items():
        md.append(
            f"| {name} | {m.cumulative_return*100:+.2f}% | "
            f"{m.annualized_return*100:+.2f}%/yr | "
            f"{m.annualized_volatility*100:.2f}% | "
            f"{m.sharpe:.2f} | {m.max_drawdown*100:+.2f}% |"
        )

    md.append("\n## Portfolio Performance (3 profile × 2 cost)\n")
    md.append("| Profile | Cost | Cumulative | Annualized | Vol | Sharpe | Sortino | Max DD |")
    md.append("|---------|------|-----------:|-----------:|----:|-------:|--------:|-------:|")
    for profile in ("konservatif", "dengeli", "agresif"):
        for cost in ("zero", "realistic"):
            m = metrics[(profile, cost)]
            sortino_str = f"{m.sortino:.2f}" if m.sortino else "n/a"
            md.append(
                f"| {profile} | {cost} | "
                f"{m.cumulative_return*100:+.2f}% | "
                f"{m.annualized_return*100:+.2f}%/yr | "
                f"{m.annualized_volatility*100:.2f}% | "
                f"{m.sharpe:.2f} | {sortino_str} | "
                f"{m.max_drawdown*100:+.2f}% |"
            )

    md.append("\n## Regime Calendar (VIX-based)\n")
    md.append("| Quarter-End | VIX | Regime |")
    md.append("|-------------|----:|--------|")
    for rt in rcal:
        md.append(f"| {rt.quarter_end} | {rt.vix:.2f} | {rt.regime.value} |")

    md.append("\n## Per-Regime Attribution (Dengeli zero)\n")
    md.append("| Regime | n | Cumulative | Avg/Q |")
    md.append("|--------|--:|-----------:|------:|")
    for r in regime_attr:
        md.append(
            f"| {r.regime.value} | {r.n_quarters} | "
            f"{r.cumulative_return*100:+.2f}% | "
            f"{r.avg_quarterly_return*100:+.2f}% |"
        )

    md.append("\n## Per-Sleeve Attribution (Dengeli zero)\n")
    md.append("| Sleeve | Avg Weight | Contribution |")
    md.append("|--------|-----------:|-------------:|")
    for s in sleeve_attr:
        md.append(
            f"| {s.sleeve} | {s.avg_weight*100:.2f}% | "
            f"{s.cumulative_contribution*100:+.2f}% |"
        )

    md.append("\n## 5-Failure Metric Tracker (realistic cost)\n")
    md.append("| Profile | Trading Cost | Turnover | Tax Drag | Cash Avg | Style |")
    md.append("|---------|------------:|---------:|---------:|---------:|-------|")
    for p in ("konservatif", "dengeli", "agresif"):
        f = failure[p]
        md.append(
            f"| {p} | {f.annualized_trading_cost*100:.2f}%/yr [{f.trading_cost_verdict}] | "
            f"{f.annualized_turnover*100:.2f}%/yr [{f.turnover_verdict}] | "
            f"{f.annualized_tax_drag*100:.2f}%/yr [{f.tax_drag_verdict}] | "
            f"{f.avg_cash_weight*100:.2f}% [{f.cash_verdict}] | "
            f"{f.style_verdict} |"
        )

    md.append(f"\n## Bias Note\n\n> {BIAS_NOTE}\n")
    md_path.write_text("\n".join(md), encoding="utf-8")

    print(f"\n[OUTPUT FILES]")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")

    print("\n" + "#" * 80)
    print("# BACKTEST PRODUCTION RUN COMPLETE")
    print("#" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
