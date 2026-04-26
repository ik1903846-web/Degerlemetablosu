#!/usr/bin/env python
"""TUPRS 12-yıl historical fetcher test."""
import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.isyatirim_scraper import fetch_yearly_extended


async def main():
    print("="*80)
    print("TUPRS 12-Yıl Historical Fetch Test (Faz 2.1.4 Adım 1)")
    print("="*80)

    # 12 yıl: 2024 → 2013
    years = list(range(2024, 2012, -1))  # [2024, 2023, ..., 2013]

    print(f"\n[FETCH] TUPRS, {len(years)} yıl: {years}")
    print("-"*80)

    data = await fetch_yearly_extended(
        ticker="TUPRS",
        years=years,
    )

    print(f"  Ticker:            {data.ticker}")
    print(f"  Financial Group:   {data.financial_group}")
    print(f"  Total periods:     {len(data.periods)}")
    print(f"  Total items:       {data.total_items()}")

    # Basic checks
    assert len(data.periods) == 12, f"Expected 12 periods, got {len(data.periods)}"
    print(f"  ✓ 12 dönem birleştirildi")

    assert data.total_items() == 147, f"Expected 147 items, got {data.total_items()}"
    print(f"  ✓ 147 item count birebir (tüm chunk'larda aynı taxonomy)")

    # ========================================================================
    # 12-Yıl EBIT trend
    # ========================================================================
    print("\n[EBIT 12-YIL TREND] (Cyclical pattern doğrulaması)")
    print("-"*80)

    ebit = data.get_item("3DF")
    if ebit:
        print(f"  Kalem: {ebit.desc_tr.strip()}")
        print()
        for period, val in zip(data.periods, ebit.values):
            year = period['year']
            if val is not None:
                val_b = float(val) / 1_000_000_000
                bar = "█" * min(int(abs(val_b) / 5), 50)  # Visual
                print(f"  {year}: {val_b:>10.2f}B TL  {bar}")
            else:
                print(f"  {year}:       null")

    # ========================================================================
    # Revenue 12-yıl trend
    # ========================================================================
    print("\n[REVENUE 12-YIL TREND]")
    print("-"*80)

    revenue_dom = data.get_item("4BC")
    revenue_for = data.get_item("4BD")

    if revenue_dom and revenue_for:
        print(f"  Yurtiçi + Yurtdışı toplam:")
        for i, period in enumerate(data.periods):
            year = period['year']
            d = revenue_dom.values[i] if i < len(revenue_dom.values) else None
            f = revenue_for.values[i] if i < len(revenue_for.values) else None

            if d is not None and f is not None:
                total = float(d + f) / 1_000_000_000
                print(f"  {year}: {total:>10.2f}B TL")
            elif d is not None:
                print(f"  {year}: {float(d)/1_000_000_000:>10.2f}B TL (sadece yurtiçi)")
            else:
                print(f"  {year}:       null")

    # ========================================================================
    # Operating Margin 12-yıl (cyclical normalize için)
    # ========================================================================
    print("\n[OPERATING MARGIN 12-YIL — CYCLICAL NORMALIZE]")
    print("-"*80)

    margins = []
    for i, period in enumerate(data.periods):
        year = period['year']
        e = ebit.values[i] if ebit and i < len(ebit.values) else None
        d = revenue_dom.values[i] if revenue_dom and i < len(revenue_dom.values) else None
        f = revenue_for.values[i] if revenue_for and i < len(revenue_for.values) else None

        if e is not None and d is not None and f is not None:
            total_rev = d + f
            if total_rev > 0:
                margin = float(e / total_rev)
                margins.append((year, margin))
                print(f"  {year}: {margin*100:>6.2f}%")
            else:
                print(f"  {year}: revenue=0")
        else:
            print(f"  {year}: null")

    if len(margins) >= 8:
        margin_values = [m for _, m in margins]
        avg_12y = sum(margin_values) / len(margin_values)
        avg_4y = sum(margin_values[:4]) / 4 if len(margin_values) >= 4 else None

        margin_min = min(margin_values)
        margin_max = max(margin_values)
        spread = margin_max - margin_min

        print(f"\n  12-yıl avg margin:        {avg_12y*100:.2f}%")
        if avg_4y:
            print(f"  4-yıl avg margin (yeni):  {avg_4y*100:.2f}%")
        print(f"  Range:                    {margin_min*100:.2f}% → {margin_max*100:.2f}%")
        print(f"  Spread:                   {spread*100:.2f}%")

        # Cyclical confirmation
        if spread > 0.05:
            print(f"\n  ✓ 12-yıl da CYCLICAL pattern doğrulandı")
            print(f"  → Damodaran ideal historical depth ile margin %{avg_12y*100:.2f}")
            print(f"  → 4-yıl baseline {avg_4y*100:.2f}% vs 12-yıl {avg_12y*100:.2f}%")
            print(f"  → Fark: {(avg_12y - avg_4y)*100:+.2f}pp")

    print("\n" + "="*80)
    print("Faz 2.1.4 Adım 1 — 12-yıl historical fetch PASS")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
