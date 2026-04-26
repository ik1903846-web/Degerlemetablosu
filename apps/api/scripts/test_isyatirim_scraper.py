#!/usr/bin/env python
"""TUPRS isyatirim scraper test."""
import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.isyatirim_scraper import (
    fetch_yearly,
    FG_INDUSTRIAL,
)


async def main():
    print("="*80)
    print("TUPRS isyatirim Scraper Test (Faz 2.1.2 Adım A)")
    print("="*80)

    # ========================================================================
    # TEST 1: TUPRS 4 yıllık fetch
    # ========================================================================
    print("\n[TEST 1] TUPRS 4-yıl fetch (2024-2021)")
    print("-"*80)

    data = await fetch_yearly(
        ticker="TUPRS",
        years=[2024, 2023, 2022, 2021],
    )

    print(f"  Ticker:           {data.ticker}")
    print(f"  Financial Group:  {data.financial_group}")
    print(f"  Periods:          {len(data.periods)} dönem")
    print(f"  Total items:      {data.total_items()}")

    assert data.total_items() == 147, f"Expected 147 items, got {data.total_items()}"
    print(f"  ✓ Item count birebir (Faz 2.1.1b'deki 147 doğrulaması)")

    # ========================================================================
    # TEST 2: Damodaran kalem extraction
    # ========================================================================
    print("\n[TEST 2] Damodaran DCF kalemleri extraction")
    print("-"*80)

    test_items = [
        ("3DF", "EBIT (FAALİYET KARI)"),
        ("1AA", "Cash (Nakit ve Benzerleri)"),
        ("2N",  "Total Equity (Özkaynaklar TOPLAM)"),
        ("2OCF", "Net Income (Dönem Net Kar)"),
        ("2AA", "ST Debt (Kısa Vadeli Finansal Borçlar)"),
        ("2BA", "LT Debt (Uzun Vadeli Finansal Borçlar)"),
        ("4B",  "Depreciation (Amortisman)"),
        ("4C",  "Operating Cash Flow"),
        ("4CAF", "ΔWorking Capital"),
    ]

    print(f"  Code  | Açıklama                                  | 2024 (TL)")
    print(f"  ------|-------------------------------------------|--------------")

    all_found = True
    for code, label in test_items:
        item = data.get_item(code)
        if item is None:
            print(f"  {code:<5} | ✗ NOT FOUND ({label})")
            all_found = False
            continue

        value = item.latest_value
        if value is None:
            value_str = "null"
        else:
            value_str = f"{int(value):,}"

        print(f"  {code:<5} | {label:<41} | {value_str}")

    if all_found:
        print(f"\n  ✓ Tüm 9 Damodaran kalemi başarıyla çekildi")
    else:
        print(f"\n  ✗ Bazı kalemler bulunamadı")

    # ========================================================================
    # TEST 3: Prefix-based grouping
    # ========================================================================
    print("\n[TEST 3] Prefix dağılımı doğrulama")
    print("-"*80)

    prefixes = ["1A", "1B", "2A", "2B", "2N", "2O", "3", "4B", "4C"]

    for prefix in prefixes:
        items = data.get_items_by_prefix(prefix)
        if items:
            print(f"  {prefix:<4}: {len(items):>3} kalem  (örn: {items[0].item_code} {items[0].desc_tr[:50].strip()})")

    # ========================================================================
    # TEST 4: 4-dönem comparison
    # ========================================================================
    print("\n[TEST 4] EBIT (3DF) 4 yıllık trend")
    print("-"*80)

    ebit = data.get_item("3DF")
    if ebit:
        print(f"  Kalem: {ebit.desc_tr.strip()}")
        period_labels = [f"{p['year']}" for p in data.periods]
        for i, (label, val) in enumerate(zip(period_labels, ebit.values)):
            if val is not None:
                val_str = f"{int(val):>20,}"
            else:
                val_str = "null".rjust(20)
            print(f"  {label}: {val_str} TL")

    print("\n" + "="*80)
    print("Faz 2.1.2 Adım A — fetch + parse PASS")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
