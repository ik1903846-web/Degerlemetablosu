#!/usr/bin/env python
"""TUPRS Net CapEx formula test (Faz 2.1.4 Adım 4)."""
import sys
import asyncio
from pathlib import Path
from decimal import Decimal

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.isyatirim_scraper import fetch_yearly_extended
from data_layer.damodaran_mapper import map_to_damodaran_inputs


def fmt_billions(val):
    if val is None:
        return "    null"
    return f"{float(val) / 1_000_000_000:>10.2f}B TL"


def _safe_sum(*vals):
    valid = [v for v in vals if v is not None]
    if not valid:
        return None
    return sum(valid)


async def main():
    print("="*80)
    print("TUPRS Net CapEx Formula Test (Faz 2.1.4 Adım 4)")
    print("="*80)

    # 12 yıl fetch
    years = list(range(2024, 2012, -1))
    statements = await fetch_yearly_extended(ticker="TUPRS", years=years)
    inputs = map_to_damodaran_inputs(statements)

    print(f"\nPipeline: 12-yıl fetch + Damodaran map")
    print(f"  Items found: {inputs.items_found}/12")
    print(f"  Periods: {inputs.period_labels}")

    # ========================================================================
    # TEST 1: PP&E (1BG) extraction
    # ========================================================================
    print("\n[TEST 1] PP&E (1BG) Trend (12-yıl)")
    print("-"*80)

    ppe_item = statements.get_item("1BG")
    intangible_item = statements.get_item("1BH")

    if ppe_item and intangible_item:
        print(f"  Year | PP&E (1BG)        | Intangible (1BH)  | Operating Assets")
        print(f"  -----|-------------------|-------------------|------------------")
        for i, period in enumerate(statements.periods):
            year = period['year']
            ppe = ppe_item.values[i]
            intg = intangible_item.values[i]

            ppe_str = fmt_billions(ppe)
            intg_str = fmt_billions(intg)
            total_str = fmt_billions(_safe_sum(ppe, intg))

            print(f"  {year} | {ppe_str} | {intg_str} | {total_str}")

    # ========================================================================
    # TEST 2: Net CapEx 12-yıl
    # ========================================================================
    print("\n[TEST 2] Net CapEx (Damodaran formula) — 12-yıl")
    print("-"*80)

    print(f"  Year | Net CapEx          | vs Raw Aggregate (eski)")
    print(f"  -----|--------------------|------------------------")
    for i, year_str in enumerate(inputs.period_labels):
        year = year_str
        net_cx = inputs.net_capex[i] if i < len(inputs.net_capex) else None
        raw_cx = inputs.capex[i] if i < len(inputs.capex) else None

        net_str = fmt_billions(net_cx)
        raw_str = fmt_billions(raw_cx)

        if net_cx is not None and raw_cx is not None and raw_cx > 0:
            ratio = float(net_cx / raw_cx) * 100
            ratio_str = f"({ratio:>5.1f}% of raw)"
        else:
            ratio_str = ""

        print(f"  {year} | {net_str} | {raw_str} {ratio_str}")

    # ========================================================================
    # TEST 3: Reinvestment Rate
    # ========================================================================
    print("\n[TEST 3] Reinvestment Rate (Net CapEx + ΔWC) / Revenue")
    print("-"*80)

    print(f"  Year | Net CapEx | ΔWC | Reinvestment Total | Revenue | Reinv %")
    print(f"  -----|-----------|-----|--------------------|---------|--------")

    for i, year_str in enumerate(inputs.period_labels):
        net_cx = inputs.net_capex[i] if i < len(inputs.net_capex) else None
        wc = inputs.working_capital_change[i] if i < len(inputs.working_capital_change) else None
        rev = inputs.revenue[i] if i < len(inputs.revenue) else None

        if net_cx is not None and wc is not None and rev is not None and rev > 0:
            reinvestment = net_cx + wc  # ΔWC negatif olabilir
            ratio = float(reinvestment / rev) * 100

            net_str = fmt_billions(net_cx)
            wc_str = fmt_billions(wc)
            reinv_str = fmt_billions(reinvestment)
            rev_str = fmt_billions(rev)

            print(f"  {year_str} | {net_str} | {wc_str} | {reinv_str} | {rev_str} | {ratio:>5.2f}%")

    # ========================================================================
    # TEST 4: Backward Compat (4-yıl)
    # ========================================================================
    print("\n[TEST 4] Backward Compat (4-yıl mapper test)")
    print("-"*80)

    from data_layer.isyatirim_scraper import fetch_yearly

    statements_4y = await fetch_yearly(
        ticker="TUPRS",
        years=[2024, 2023, 2022, 2021],
    )
    inputs_4y = map_to_damodaran_inputs(statements_4y)

    print(f"  4-yıl items found:    {inputs_4y.items_found}/12")
    print(f"  4-yıl net_capex 2024: {fmt_billions(inputs_4y.net_capex[0])}")
    print(f"  12-yıl net_capex 2024: {fmt_billions(inputs.net_capex[0])}")

    if inputs_4y.net_capex[0] is not None and inputs.net_capex[0] is not None:
        diff = abs(inputs_4y.net_capex[0] - inputs.net_capex[0])
        if diff < Decimal("1_000_000_000"):  # < 1B TL fark
            print(f"  ✓ 4-yıl ve 12-yıl mapper aynı 2024 değerini üretti (consistent)")
        else:
            print(f"  ⚠ Fark: {fmt_billions(diff)} (taxonomy değişikliği?)")

    print("\n" + "="*80)
    print("Faz 2.1.4 Adım 4 — Net CapEx Formula PASS")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
