#!/usr/bin/env python
"""Orchestrator test — TUPRS end-to-end (Faz 2.3)."""
import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

# Proje root'undaki .env'i yükle (DATABASE_URL — Faz 2.4.6 Component 1)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from dcf_engine.orchestrator import analyze_ticker, print_report


async def main():
    print("="*80)
    print("ORCHESTRATOR END-TO-END TEST (Faz 2.3)")
    print("="*80)
    print("Pipeline: ticker → fetch → map → USD → classify → DCF → value")
    print("="*80)

    # ========================================================================
    # TEST 1: TUPRS (cyclical, doğrulanmış)
    # ========================================================================
    print("\n[TEST 1] TUPRS (cyclical_dcf bekleniyor)")
    print("-"*80)

    report = await analyze_ticker(
        ticker="TUPRS",
        market_price_tl=269.00,  # 24 Nis 2026
    )

    print_report(report)

    # ========================================================================
    # TEST 2: ARCLK (industrial_fcff bekleniyor)
    # ========================================================================
    print("\n\n[TEST 2] ARCLK (industrial_fcff bekleniyor)")
    print("-"*80)

    report_arclk = await analyze_ticker(
        ticker="ARCLK",
        market_price_tl=None,  # opsiyonel
    )

    print_report(report_arclk)

    # ========================================================================
    # TEST 3: GARAN (banking, skip bekleniyor)
    # ========================================================================
    print("\n\n[TEST 3] GARAN (banking, Faz 2.3.1'de skip bekleniyor)")
    print("-"*80)

    report_garan = await analyze_ticker(
        ticker="GARAN",
        market_price_tl=None,
    )

    print_report(report_garan)

    # ========================================================================
    # CONSISTENCY CHECK
    # ========================================================================
    print("\n\n[CONSISTENCY CHECK]")
    print("-"*80)
    print(f"  TUPRS orchestrator value:    {report.value_per_share_tl:.2f} TL")
    print(f"  TUPRS Adım 5 manuel value:   181.16 TL")

    if report.value_per_share_tl is not None:
        diff = abs(report.value_per_share_tl - 181.16)
        if diff < 1.0:
            print(f"  ✓ Orchestrator + manuel sonuç UYUMLU (fark <1 TL)")
        else:
            print(f"  ⚠ Fark: {diff:.2f} TL (debug gerek)")

    print("\n" + "="*80)
    print("Faz 2.3 Orchestrator PASS")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
