#!/usr/bin/env python
"""
Sector mapping integration test (Component 1 Adım 1.2).

Her BIST 30 ticker için:
1. Ticker -> Damodaran sector resolve
2. DB'den sector beta fetch
3. Beta None dönmemeli (regression guard)
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.sector_mapping import (
    get_damodaran_sector,
    get_all_mapped_tickers,
    get_unique_sectors,
)
from data_layer.damodaran_db import (
    fetch_sector_unlevered_beta,
    clear_sector_beta_cache,
)


async def main():
    print("=" * 80)
    print("SECTOR MAPPING INTEGRATION TEST (Component 1 Adım 1.2)")
    print("=" * 80)

    tickers = get_all_mapped_tickers()
    sectors = get_unique_sectors()

    print(f"\n  Total mapped tickers: {len(tickers)}")
    print(f"  Unique sectors:       {len(sectors)}")

    # TEST 1 — Her ticker için end-to-end resolve
    print("\n[TEST 1] Ticker -> Sector -> Beta (end-to-end)")
    print("-" * 80)
    print(f"  {'Ticker':<8} | {'Sector':<35} | Beta")
    print(f"  {'-'*8}-+-{'-'*35}-+--------")

    all_pass = True
    coverage_count = 0

    for ticker in tickers:
        sector = get_damodaran_sector(ticker)
        beta = await fetch_sector_unlevered_beta(sector)

        if beta is None:
            status = "[FAIL]"
            beta_str = "None"
            all_pass = False
        else:
            status = "[OK]"
            beta_str = f"{float(beta):.4f}"
            coverage_count += 1

        print(f"  {ticker:<8} | {sector:<35} | {beta_str:>7}  {status}")

    print(f"\n  Coverage: {coverage_count}/{len(tickers)}")
    print(f"  Status:   {'[PASS]' if all_pass else '[FAIL]'}")

    # TEST 2 — Anchor regression (TUPRS, CCOLA kritik)
    print("\n[TEST 2] Anchor + Critical Fix Regression")
    print("-" * 80)

    anchors = [
        ("TUPRS", "oil_gas_integrated", 0.7043, "TUPRS Damodaran-aligned baseline"),
        ("CCOLA", "beverage_soft",       0.5501, "Faz 2.4.5 +%567 fix"),
        ("TRALT", "precious_metals",     1.4176, "Gold pure-play (NOT diversified)"),
        ("TRMET", "metals_and_mining",   1.3013, "Diversified metals (NOT precious)"),
    ]

    print(f"  {'Ticker':<8} | {'Sector':<25} | {'Expected':<10} | {'Actual':<10} | Status")
    print(f"  {'-'*8}-+-{'-'*25}-+-{'-'*10}-+-{'-'*10}-+-------")

    all_anchors_pass = True

    for ticker, expected_sector, expected_beta, note in anchors:
        sector = get_damodaran_sector(ticker)
        beta = await fetch_sector_unlevered_beta(sector)

        sector_match = sector == expected_sector
        beta_match = beta is not None and abs(float(beta) - expected_beta) < 0.001

        if sector_match and beta_match:
            status = "[OK]"
        else:
            status = "[FAIL]"
            all_anchors_pass = False

        beta_str = f"{float(beta):.4f}" if beta else "None"
        print(f"  {ticker:<8} | {sector:<25} | {expected_beta:<10.4f} | {beta_str:<10} | {status}")
        if status == "[OK]":
            print(f"           {note}")

    print(f"\n  Anchor regression: {'[PASS]' if all_anchors_pass else '[FAIL]'}")

    # TEST 3 — Unique sector listesi (audit)
    print("\n[TEST 3] Unique Sector Audit")
    print("-" * 80)
    for sector in sectors:
        # Hangi ticker'lar bu sektörde?
        members = [t for t, s in [(t, get_damodaran_sector(t)) for t in tickers] if s == sector]
        beta = await fetch_sector_unlevered_beta(sector)
        beta_str = f"{float(beta):.4f}" if beta else "None"
        members_str = ", ".join(members)
        print(f"  {sector:<35} = {beta_str}  ({members_str})")

    print("\n" + "=" * 80)
    if all_pass and all_anchors_pass:
        print("Component 1 Adım 1.2 — SECTOR MAPPING TEST PASS")
    else:
        print("Component 1 Adım 1.2 — FAIL")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
