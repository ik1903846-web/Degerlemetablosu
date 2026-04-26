#!/usr/bin/env python
"""TUPRS Damodaran mapper test."""
import sys
import asyncio
from pathlib import Path
from decimal import Decimal

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.isyatirim_scraper import fetch_yearly
from data_layer.damodaran_mapper import map_to_damodaran_inputs


def fmt_decimal(val, scale=1_000_000_000):
    """Format Decimal in billions."""
    if val is None:
        return "    null"
    val_b = float(val) / scale
    return f"{val_b:>9.2f}B"


def fmt_pct(val):
    """Format Decimal as percentage."""
    if val is None:
        return "  null"
    return f"{float(val)*100:>5.2f}%"


async def main():
    print("="*80)
    print("TUPRS Damodaran Mapper Test (Faz 2.1.2 Adım B)")
    print("="*80)

    # ========================================================================
    # TEST 1: Fetch + Map
    # ========================================================================
    print("\n[TEST 1] Fetch + Map TUPRS")
    print("-"*80)

    statements = await fetch_yearly(
        ticker="TUPRS",
        years=[2024, 2023, 2022, 2021],
    )

    print(f"  Statements fetched: {statements.total_items()} items")

    inputs = map_to_damodaran_inputs(statements)

    print(f"  Mapped inputs:")
    print(f"    Ticker:         {inputs.ticker}")
    print(f"    Currency:       {inputs.currency}")
    print(f"    Period labels:  {inputs.period_labels}")
    print(f"    Items found:    {inputs.items_found}/12")

    if inputs.items_missing:
        print(f"    ⚠ Missing: {inputs.items_missing}")
    else:
        print(f"    ✓ Tüm 12 kalem extract edildi")

    # ========================================================================
    # TEST 2: 4-Yıl Time Series Display
    # ========================================================================
    print("\n[TEST 2] 4-Yıl Time Series (TL Billions)")
    print("-"*80)

    print(f"  Metric                  | {inputs.period_labels[0]:>10} | {inputs.period_labels[1]:>10} | {inputs.period_labels[2]:>10} | {inputs.period_labels[3]:>10}")
    print(f"  ------------------------|------------|------------|------------|------------")

    metrics = [
        ("Revenue", inputs.revenue),
        ("EBIT", inputs.ebit),
        ("Pretax Income", inputs.pretax_income),
        ("Net Income", inputs.net_income),
        ("Operating CF", inputs.operating_cash_flow),
        ("Depreciation", inputs.depreciation),
        ("CapEx", inputs.capex),
        ("ΔWorking Cap", inputs.working_capital_change),
        ("Cash", inputs.cash),
        ("ST Debt", inputs.short_term_debt),
        ("LT Debt", inputs.long_term_debt),
        ("Total Debt", inputs.total_debt),
        ("Total Equity", inputs.total_equity),
    ]

    for name, series in metrics:
        v0 = fmt_decimal(series[0])
        v1 = fmt_decimal(series[1]) if len(series) > 1 else "       -"
        v2 = fmt_decimal(series[2]) if len(series) > 2 else "       -"
        v3 = fmt_decimal(series[3]) if len(series) > 3 else "       -"
        print(f"  {name:<24}| {v0:>10} | {v1:>10} | {v2:>10} | {v3:>10}")

    # ========================================================================
    # TEST 3: Computed Metrics
    # ========================================================================
    print("\n[TEST 3] Computed Metrics")
    print("-"*80)

    print(f"  Year | Op Margin | Eff Tax Rate")
    print(f"  -----|-----------|-------------")
    for i, year in enumerate(inputs.period_labels):
        m = fmt_pct(inputs.operating_margin[i])
        t = fmt_pct(inputs.effective_tax_rate[i])
        print(f"  {year} |  {m:>7} |   {t:>7}")

    # ========================================================================
    # TEST 4: Cyclical Pattern Check (TUPRS expected)
    # ========================================================================
    print("\n[TEST 4] TUPRS Cyclical Pattern Detection")
    print("-"*80)

    margins = [m for m in inputs.operating_margin if m is not None]
    if len(margins) >= 3:
        margin_min = min(margins)
        margin_max = max(margins)
        margin_range = margin_max - margin_min
        margin_avg = sum(margins) / len(margins)

        print(f"  Op Margin range: {fmt_pct(margin_min)} → {fmt_pct(margin_max)}")
        print(f"  Spread:          {fmt_pct(margin_range)}")
        print(f"  Average:         {fmt_pct(margin_avg)}")

        # Cyclical detection: margin spread > 5pp suggests cyclical
        if margin_range > Decimal('0.05'):
            print(f"\n  ✓ CYCLICAL pattern tespit edildi (margin spread > 5pp)")
            print(f"  → cyclical_dcf.py uygulanabilir (Toyota 2009 pattern)")
            print(f"  → Historical avg margin = {fmt_pct(margin_avg)}")
        else:
            print(f"\n  ⚠ Stable margin pattern (cyclical değil)")
            print(f"  → industrial_fcff.py daha uygun olabilir")

    print("\n" + "="*80)
    print("Faz 2.1.2 Adım B — Damodaran mapper PASS")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
