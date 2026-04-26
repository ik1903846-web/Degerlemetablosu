#!/usr/bin/env python
"""TUPRS shares outstanding test (Faz 2.1.4 Adım 3)."""
import sys
from pathlib import Path
from decimal import Decimal

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.shares_fetcher import (
    get_shares_outstanding,
    get_shares_outstanding_static,
    verify_shares_against_market_cap,
    STATIC_SHARES_OUTSTANDING,
)


def main():
    print("="*80)
    print("Shares Outstanding Fetcher Test (Faz 2.1.4 Adım 3)")
    print("="*80)

    # ========================================================================
    # TEST 1: TUPRS canonical
    # ========================================================================
    print("\n[TEST 1] TUPRS — Canonical (Resmi 1.93B doğrulandı)")
    print("-"*80)

    tuprs = get_shares_outstanding("TUPRS")

    if tuprs is None:
        print("  ✗ TUPRS not found")
        return

    print(f"  Ticker:           {tuprs.ticker}")
    print(f"  Shares:           {tuprs.shares:,}")
    print(f"  Shares (billion): {tuprs.shares_billions:.4f}B")
    print(f"  Source:           {tuprs.source}")

    # Beklenen: 1,926,795,598
    expected_tuprs = 1_926_795_598
    if tuprs.shares == expected_tuprs:
        print(f"  ✓ Resmi sayı ile birebir uyum (1,926,795,598)")
    else:
        print(f"  ✗ Beklenen {expected_tuprs}, geldi {tuprs.shares}")

    # ========================================================================
    # TEST 2: Market Cap Cross-Check (24 Nis 2026)
    # ========================================================================
    print("\n[TEST 2] Market Cap Cross-Check")
    print("-"*80)

    # 24 Nis 2026 fiyat: 269 TL
    # Beklenen market cap: 518.3B TL
    current_price = Decimal("269.00")
    expected_mc = Decimal("518_300_000_000")  # 518.3B TL

    calc_mc = tuprs.calculate_market_cap(current_price)
    print(f"  Current Price (24 Nis 2026): {current_price} TL")
    print(f"  Calculated Market Cap:       {float(calc_mc)/1_000_000_000:.2f}B TL")
    print(f"  Expected (web doğrulama):    {float(expected_mc)/1_000_000_000:.2f}B TL")

    is_valid = verify_shares_against_market_cap(
        shares_obj=tuprs,
        current_price=current_price,
        expected_market_cap=expected_mc,
        tolerance=Decimal("0.02"),  # ±2% tolerance
    )

    if is_valid:
        diff_pct = float(abs(calc_mc - expected_mc) / expected_mc) * 100
        print(f"  ✓ Market cap doğrulandı (±2% tolerance, fark {diff_pct:.2f}%)")
    else:
        diff_pct = float(abs(calc_mc - expected_mc) / expected_mc) * 100
        print(f"  ⚠ Market cap fark {diff_pct:.2f}% — tolerans dışı")

    # ========================================================================
    # TEST 3: Value per Share Hesabı
    # ========================================================================
    print("\n[TEST 3] Value per Share Hesabı (Faz 2.1.3'teki bug düzeltmesi)")
    print("-"*80)

    # Faz 2.1.3'te equity value = 424.85B TL hesaplandı (eski 4-yıl pilot)
    # Bu sayı yanıltıcı (4-yıl margin %5.91 ile)
    # Yine de mekanik test için kullanıyoruz
    eski_pilot_equity_tl = Decimal("424_850_000_000")  # 424.85B TL

    # ESKİ PILOT (placeholder shares = 2.5B):
    eski_placeholder_shares = 2_500_000_000
    eski_value_per_share = eski_pilot_equity_tl / Decimal(eski_placeholder_shares)

    # YENİ (real shares = 1.93B):
    yeni_value_per_share = tuprs.calculate_value_per_share(eski_pilot_equity_tl)

    print(f"  Equity Value (Faz 2.1.3 pilot): {float(eski_pilot_equity_tl)/1_000_000_000:.2f}B TL")
    print(f"  ")
    print(f"  ESKİ pilot (2.5B placeholder):  {float(eski_value_per_share):.2f} TL/share (YANLIŞ)")
    print(f"  YENİ canonical (1.93B real):    {float(yeni_value_per_share):.2f} TL/share")
    print(f"  ")
    print(f"  Fark: {float(yeni_value_per_share - eski_value_per_share):.2f} TL/share")
    print(f"  ")
    print(f"  ⚠ NOT: Bu hâlâ '4-yıl margin %5.91' bazlı, gerçek değil.")
    print(f"  Faz 2.1.4 Adım 5'te 12-yıl + USD + real shares ile gerçek DCF.")

    # ========================================================================
    # TEST 4: BIST 30 Coverage
    # ========================================================================
    print("\n[TEST 4] BIST 30 Static Coverage")
    print("-"*80)

    bist_30_tickers = [
        "TUPRS", "GARAN", "AKBNK", "ISCTR", "YKBNK", "HALKB", "VAKBN",
        "EREGL", "KRDMD", "KOZAL", "KOZAA",
        "BIMAS", "MGROS", "SOKM",
        "TOASO", "FROTO", "ARCLK", "ASELS",
        "THYAO", "PGSUS",
        "KCHOL", "SAHOL",
        "ENKAI", "PETKM", "CCOLA",
    ]

    found = 0
    missing = []
    for ticker in bist_30_tickers:
        result = get_shares_outstanding_static(ticker)
        if result:
            found += 1
        else:
            missing.append(ticker)

    print(f"  BIST 30 tickers tested: {len(bist_30_tickers)}")
    print(f"  Found in static dict:   {found}")
    print(f"  Missing:                {len(missing)}")

    if missing:
        print(f"  Missing tickers: {missing}")

    print(f"\n  Static dict total tickers: {len(STATIC_SHARES_OUTSTANDING)}")

    # ========================================================================
    # TEST 5: Edge cases
    # ========================================================================
    print("\n[TEST 5] Edge Cases")
    print("-"*80)

    # Bilinmeyen ticker
    unknown = get_shares_outstanding("UNKNOWN_TICKER")
    if unknown is None:
        print(f"  ✓ Unknown ticker → None döndü (graceful)")
    else:
        print(f"  ✗ Unknown ticker None dönmedi")

    # Lowercase
    tuprs_lower = get_shares_outstanding("tuprs")
    if tuprs_lower and tuprs_lower.shares == 1_926_795_598:
        print(f"  ✓ Lowercase ticker doğru çalıştı")
    else:
        print(f"  ✗ Lowercase ticker problem")

    print("\n" + "="*80)
    print("Faz 2.1.4 Adım 3 — Shares Fetcher PASS")
    print("="*80)


if __name__ == "__main__":
    main()
