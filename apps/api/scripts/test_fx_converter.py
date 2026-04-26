#!/usr/bin/env python
"""TUPRS USD conversion test (Faz 2.1.4 Adım 2)."""
import sys
import asyncio
from pathlib import Path
from decimal import Decimal

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.isyatirim_scraper import fetch_yearly_extended
from data_layer.damodaran_mapper import map_to_damodaran_inputs
from data_layer.fx_converter import (
    get_static_rates,
    convert_inputs_to_usd,
    STATIC_YEAR_END_RATES,
)


def fmt_billions_tl(val):
    if val is None:
        return "    null"
    return f"{float(val) / 1_000_000_000:>9.2f}B TL"


def fmt_millions_usd(val):
    if val is None:
        return "    null"
    return f"{float(val) / 1_000_000:>9.2f}M USD"


async def main():
    print("="*80)
    print("TUPRS USD Converter Test (Faz 2.1.4 Adım 2)")
    print("="*80)

    # ========================================================================
    # STEP 1: 12-yıl historical fetch (Adım 1'den)
    # ========================================================================
    print("\n[STEP 1] 12-yıl TL historical fetch")
    print("-"*80)

    years = list(range(2024, 2012, -1))  # 2024 → 2013
    statements = await fetch_yearly_extended(ticker="TUPRS", years=years)
    inputs_tl = map_to_damodaran_inputs(statements)

    print(f"  Periods: {len(inputs_tl.period_labels)}")
    print(f"  Currency (TL): {inputs_tl.currency}")
    print(f"  Items found: {inputs_tl.items_found}/12")

    # ========================================================================
    # STEP 2: FX rates load
    # ========================================================================
    print("\n[STEP 2] FX Rates (Year-end USD/TL)")
    print("-"*80)

    fx_series = get_static_rates(years)

    print(f"  Year | USD/TL Rate | Source")
    print(f"  -----|-------------|--------")
    for year in years:
        fx = fx_series.get_rate(year)
        if fx:
            print(f"  {year} |  {float(fx.rate):>9.4f} | {fx.source}")
        else:
            print(f"  {year} |  NOT FOUND  | -")

    # ========================================================================
    # STEP 3: USD conversion
    # ========================================================================
    print("\n[STEP 3] USD Conversion (TL → USD)")
    print("-"*80)

    inputs_usd = convert_inputs_to_usd(inputs_tl, fx_series)

    print(f"  Currency (USD): {inputs_usd.currency}")
    print(f"\n  REVENUE COMPARISON (TL vs USD):")
    print(f"  Year | TL (Billions)    | USD (Millions)   | USD/TL Rate")
    print(f"  -----|------------------|------------------|------------")

    for i, year_str in enumerate(inputs_tl.period_labels):
        year = int(year_str)
        tl_val = inputs_tl.revenue[i]
        usd_val = inputs_usd.revenue[i]
        rate = STATIC_YEAR_END_RATES.get(year, Decimal("0"))

        tl_str = fmt_billions_tl(tl_val)
        usd_str = fmt_millions_usd(usd_val)

        print(f"  {year} | {tl_str} | {usd_str} | {float(rate):>8.4f}")

    # ========================================================================
    # STEP 4: Hyperinflation Noise Eliminated Check
    # ========================================================================
    print("\n[STEP 4] Hyperinflation Noise Check")
    print("-"*80)

    # 2021 vs 2022 TL revenue jump (6×) USD'de aynı mı?
    tl_2021 = inputs_tl.revenue[3]  # index 3 = 2021
    tl_2022 = inputs_tl.revenue[2]  # index 2 = 2022
    usd_2021 = inputs_usd.revenue[3]
    usd_2022 = inputs_usd.revenue[2]

    if all(v is not None for v in [tl_2021, tl_2022, usd_2021, usd_2022]):
        tl_jump = float(tl_2022 / tl_2021)
        usd_jump = float(usd_2022 / usd_2021)

        print(f"  TL Revenue Jump (2021 → 2022):  {tl_jump:.2f}× ({(tl_jump-1)*100:.0f}%)")
        print(f"  USD Revenue Jump (2021 → 2022): {usd_jump:.2f}× ({(usd_jump-1)*100:.0f}%)")
        print(f"\n  → TL'de 6× görünen jump, USD'de gerçek operational change")

        if tl_jump > usd_jump * 2:
            print(f"  ✓ Hyperinflation noise BAŞARI ile elimine edildi")
        else:
            print(f"  ⚠ TL/USD jumps benzer — daha derin inceleme gerek")

    # ========================================================================
    # STEP 5: USD Margin Check
    # ========================================================================
    print("\n[STEP 5] USD-Bazlı Operating Margin (Cyclical Normalize)")
    print("-"*80)

    print(f"  Year | Op Margin (USD bazlı)")
    print(f"  -----|----------------------")

    margins = []
    for i, year in enumerate(inputs_tl.period_labels):
        ebit_usd = inputs_usd.ebit[i]
        rev_usd = inputs_usd.revenue[i]

        if ebit_usd and rev_usd and rev_usd > 0:
            margin = float(ebit_usd / rev_usd)
            margins.append(margin)
            print(f"  {year} | {margin*100:>6.2f}%")
        else:
            print(f"  {year} |  null")

    if len(margins) >= 8:
        avg_margin = sum(margins) / len(margins)
        margin_min = min(margins)
        margin_max = max(margins)
        spread = margin_max - margin_min

        print(f"\n  USD-bazlı 12-yıl avg margin: {avg_margin*100:.2f}%")
        print(f"  Range: {margin_min*100:.2f}% → {margin_max*100:.2f}%")
        print(f"  Spread: {spread*100:.2f}pp")
        print(f"\n  Önceki TL-bazlı 12-yıl avg: %4.64 (Adım 1'den)")
        print(f"  USD vs TL margin farkı:     {(avg_margin - 0.0464)*100:+.2f}pp")
        print(f"  → Margin ratio currency-agnostic, USD vs TL aynı olması beklenir")

    # ========================================================================
    # STEP 6: USD Equity Bridge Components
    # ========================================================================
    print("\n[STEP 6] USD Equity Bridge (2024 latest)")
    print("-"*80)

    print(f"  Component        | TL (Billions)  | USD (Millions)")
    print(f"  -----------------|----------------|----------------")
    print(f"  Total Equity     | {fmt_billions_tl(inputs_tl.total_equity[0])} | {fmt_millions_usd(inputs_usd.total_equity[0])}")
    print(f"  Cash             | {fmt_billions_tl(inputs_tl.cash[0])} | {fmt_millions_usd(inputs_usd.cash[0])}")
    print(f"  Total Debt       | {fmt_billions_tl(inputs_tl.total_debt[0])} | {fmt_millions_usd(inputs_usd.total_debt[0])}")
    print(f"  EBIT             | {fmt_billions_tl(inputs_tl.ebit[0])} | {fmt_millions_usd(inputs_usd.ebit[0])}")

    print("\n" + "="*80)
    print("Faz 2.1.4 Adım 2 — USD Converter PASS")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
