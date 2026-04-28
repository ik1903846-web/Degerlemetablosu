#!/usr/bin/env python
"""
USD-Basis Backtest Re-Report — Faz 4.1 (ADR-002).

Mevcut TL nominal backtest (run_backtest_2021_2026.py) sonuçlarını
USD basis'e çevirir:

  USD_value_t = TL_value_t / USDTRY_t
  USD_return_q = USD_value_t / USD_value_t-1 - 1

Output: backtest_results_USD_*.csv / json / md

Damodaran disiplini:
  ADR-002: USD-only zorunlu
  TFRS-29 hyperinflation period'unda TL nominal yanıltıcı
  USD-basis return real alpha measurement
"""

import asyncio
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.historical_data import quarter_end_calendar
from backtest.usd_conversion import (
    fetch_usd_try_quarterly,
    convert_quarterly_returns_to_usd,
)
from backtest.performance_usd import compute_metrics_usd, RISK_FREE_USD_ANNUAL


# Faz 4 backtest period
START_DATE = date(2021, 6, 30)
END_DATE = date(2026, 3, 31)


def _outputs_dir() -> Path:
    return Path(__file__).parent.parent / "outputs"


def _latest_tl_backtest_json() -> Path:
    files = sorted(_outputs_dir().glob("backtest_results_2*.json"))
    # Filter out any USD outputs
    files = [f for f in files if "USD" not in f.name]
    if not files:
        raise FileNotFoundError("No TL-basis backtest_results_*.json found")
    return files[-1]


async def main() -> int:
    print("\n" + "#" * 80)
    print("# USD-Basis Backtest Re-Report — Faz 4.1 (ADR-002)")
    print(f"# Period: {START_DATE} → {END_DATE}")
    print("#" * 80)

    # ── 1. Mevcut TL backtest yükle ──
    tl_json = _latest_tl_backtest_json()
    print(f"\n[1/4] TL backtest yükleniyor: {tl_json.name}")
    tl_data = json.loads(tl_json.read_text(encoding="utf-8"))

    # ── 2. USD/TRY quarterly fetch ──
    print("\n[2/4] USD/TRY quarterly rates fetch...")
    fx = await fetch_usd_try_quarterly(START_DATE, END_DATE)
    print(f"  {len(fx)} quarter, devaluation: "
          f"{fx[max(fx)] / fx[min(fx)]:.3f}x")

    qends = sorted(quarter_end_calendar(START_DATE, END_DATE))

    # ── 3. Convert each backtest + benchmark ──
    print("\n[3/4] Converting TL → USD basis...")
    usd_backtests = []
    for bt in tl_data["backtests"]:
        tl_returns = bt["quarterly_returns"]
        usd_returns = convert_quarterly_returns_to_usd(
            tl_returns, fx, qends,
        )
        m = compute_metrics_usd(usd_returns, RISK_FREE_USD_ANNUAL)
        usd_backtests.append({
            "profile": bt["profile"],
            "cost_model": bt["cost_model"],
            "tl_cumulative": bt["cumulative_twr"],
            "tl_annualized": bt["annualized_return"],
            "usd_cumulative": m.cumulative_return_usd,
            "usd_annualized": m.annualized_return_usd,
            "usd_volatility": m.annualized_volatility_usd,
            "usd_sharpe": m.sharpe_usd,
            "usd_sortino": m.sortino_usd,
            "usd_max_drawdown": m.max_drawdown_usd,
            "usd_quarterly_returns": usd_returns,
            "n_quarters": m.n_quarters,
        })
        print(f"  [{bt['profile']:13s} {bt['cost_model']:9s}] "
              f"TL ann {bt['annualized_return']*100:+6.2f}% → "
              f"USD ann {m.annualized_return_usd*100:+6.2f}%/yr "
              f"(Sharpe {m.sharpe_usd:.2f})")

    usd_benchmarks = []
    for bm in tl_data["benchmarks"]:
        tl_returns = bm["quarterly_returns"]
        if bm["label"] == "SPY":
            # SPY zaten USD-denominated, conversion gereksiz
            usd_returns = tl_returns
            label_note = "(zaten USD)"
        else:
            usd_returns = convert_quarterly_returns_to_usd(
                tl_returns, fx, qends,
            )
            label_note = "(TL → USD converted)"
        m = compute_metrics_usd(usd_returns, RISK_FREE_USD_ANNUAL)
        usd_benchmarks.append({
            "label": bm["label"],
            "note": label_note,
            "tl_cumulative": bm["cumulative_twr"],
            "tl_annualized": bm["annualized_return"],
            "usd_cumulative": m.cumulative_return_usd,
            "usd_annualized": m.annualized_return_usd,
            "usd_volatility": m.annualized_volatility_usd,
            "usd_sharpe": m.sharpe_usd,
            "usd_max_drawdown": m.max_drawdown_usd,
            "usd_quarterly_returns": usd_returns,
        })
        print(f"  {bm['label']:6s} {label_note}: "
              f"TL ann {bm['annualized_return']*100:+6.2f}% → "
              f"USD ann {m.annualized_return_usd*100:+6.2f}%/yr "
              f"(Sharpe {m.sharpe_usd:.2f})")

    # ── 4. Persist outputs ──
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = _outputs_dir()

    # CSV
    csv_path = out_dir / f"backtest_results_USD_{timestamp}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["# REELDEĞER USD-Basis Backtest 2021-Q2 → 2026-Q1 (ADR-002)"])
        w.writerow([f"# Source: {tl_json.name}"])
        w.writerow([f"# USD/TRY devaluation: {fx[max(fx)] / fx[min(fx)]:.3f}x ({fx[min(fx)]:.2f} → {fx[max(fx)]:.2f})"])
        w.writerow([])
        w.writerow(["category", "label", "cost_model",
                     "tl_cum_pct", "usd_cum_pct",
                     "tl_ann_pct", "usd_ann_pct",
                     "usd_vol_pct", "usd_sharpe", "usd_sortino",
                     "usd_max_dd_pct"])
        for b in usd_backtests:
            w.writerow([
                "portfolio", b["profile"], b["cost_model"],
                f"{b['tl_cumulative']*100:.2f}",
                f"{b['usd_cumulative']*100:.2f}",
                f"{b['tl_annualized']*100:.2f}",
                f"{b['usd_annualized']*100:.2f}",
                f"{b['usd_volatility']*100:.2f}",
                f"{b['usd_sharpe']:.3f}" if b["usd_sharpe"] else "",
                f"{b['usd_sortino']:.3f}" if b["usd_sortino"] else "",
                f"{b['usd_max_drawdown']*100:.2f}",
            ])
        for b in usd_benchmarks:
            w.writerow([
                "benchmark", b["label"], "n/a",
                f"{b['tl_cumulative']*100:.2f}",
                f"{b['usd_cumulative']*100:.2f}",
                f"{b['tl_annualized']*100:.2f}",
                f"{b['usd_annualized']*100:.2f}",
                f"{b['usd_volatility']*100:.2f}",
                f"{b['usd_sharpe']:.3f}" if b["usd_sharpe"] else "",
                "",
                f"{b['usd_max_drawdown']*100:.2f}",
            ])

    # JSON full
    json_path = out_dir / f"backtest_results_USD_{timestamp}.json"
    diag = {
        "metadata": {
            "timestamp": timestamp,
            "period_start": START_DATE.isoformat(),
            "period_end": END_DATE.isoformat(),
            "source_tl_backtest": tl_json.name,
            "fx_devaluation": fx[max(fx)] / fx[min(fx)],
            "fx_start_rate": fx[min(fx)],
            "fx_end_rate": fx[max(fx)],
            "risk_free_usd_annual": RISK_FREE_USD_ANNUAL,
            "adr_reference": "ADR-002 (USD-only zorunlu)",
        },
        "fx_quarterly": {qe.isoformat(): r for qe, r in sorted(fx.items())},
        "backtests_usd": usd_backtests,
        "benchmarks_usd": usd_benchmarks,
    }
    json_path.write_text(json.dumps(diag, indent=2, default=str), encoding="utf-8")

    # Markdown summary
    md_path = out_dir / f"backtest_summary_USD_{timestamp}.md"
    md = []
    md.append(f"# REELDEĞER USD-Basis Backtest — {timestamp}\n")
    md.append(f"**Period:** {START_DATE} → {END_DATE} (4.75 yıl)")
    md.append(f"**ADR Reference:** ADR-002 (USD-only zorunlu, TL DCF yasak)")
    md.append(f"**FX devaluation:** {fx[min(fx)]:.2f} → {fx[max(fx)]:.2f} TL/USD "
              f"= {fx[max(fx)] / fx[min(fx)]:.3f}x (TL %"
              f"{(1 - fx[min(fx)] / fx[max(fx)]) * 100:.1f} lost vs USD)\n")

    md.append("## Triple Benchmark — TL vs USD\n")
    md.append("| Benchmark | TL Cum   | USD Cum | TL Ann   | USD Ann   | USD Sharpe | USD Max DD |")
    md.append("|-----------|---------:|--------:|---------:|----------:|-----------:|-----------:|")
    for b in usd_benchmarks:
        md.append(
            f"| {b['label']} | "
            f"{b['tl_cumulative']*100:+.2f}% | "
            f"{b['usd_cumulative']*100:+.2f}% | "
            f"{b['tl_annualized']*100:+.2f}%/yr | "
            f"{b['usd_annualized']*100:+.2f}%/yr | "
            f"{b['usd_sharpe']:.2f} | "
            f"{b['usd_max_drawdown']*100:+.2f}% |"
        )

    md.append("\n## Portfolio — TL vs USD\n")
    md.append("| Profile | Cost | TL Cum | USD Cum | TL Ann | USD Ann | USD Sharpe | USD DD |")
    md.append("|---------|------|-------:|--------:|-------:|--------:|-----------:|-------:|")
    for b in usd_backtests:
        md.append(
            f"| {b['profile']} | {b['cost_model']} | "
            f"{b['tl_cumulative']*100:+.2f}% | "
            f"{b['usd_cumulative']*100:+.2f}% | "
            f"{b['tl_annualized']*100:+.2f}%/yr | "
            f"{b['usd_annualized']*100:+.2f}%/yr | "
            f"{b['usd_sharpe']:.2f} | "
            f"{b['usd_max_drawdown']*100:+.2f}% |"
        )

    md.append("\n## USD-Basis Verdict (vs Triple Benchmark)\n")
    # Dengeli zero baseline
    deng = next(b for b in usd_backtests
                if b["profile"] == "dengeli" and b["cost_model"] == "zero")
    bench_xu100 = next(b for b in usd_benchmarks if b["label"] == "XU100")
    bench_xu030 = next(b for b in usd_benchmarks if b["label"] == "XU030")
    bench_spy = next(b for b in usd_benchmarks if b["label"] == "SPY")
    for bench in [bench_xu100, bench_xu030, bench_spy]:
        d_cum = deng["usd_cumulative"] - bench["usd_cumulative"]
        d_ann = deng["usd_annualized"] - bench["usd_annualized"]
        verdict = "OUTPERFORM" if d_ann > 0 else "UNDERPERFORM"
        md.append(
            f"- **vs {bench['label']}:** "
            f"Δ cumulative {d_cum*100:+.2f}pp, "
            f"Δ annualized {d_ann*100:+.2f}pp/yr → **{verdict}**"
        )

    md.append("\n## Damodaran Lesson #7 Reinforce\n")
    md.append("> 'Backtest reporting must be currency-consistent. TL nominal returns")
    md.append("> hide TL devaluation effects. USD-basis is the proper benchmark for")
    md.append("> active management value-add measurement (ADR-002).'\n")

    md_path.write_text("\n".join(md), encoding="utf-8")

    print(f"\n[OUTPUT FILES]")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")

    print("\n" + "#" * 80)
    print("# USD-BASIS RE-REPORT COMPLETE")
    print("#" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
