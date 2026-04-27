#!/usr/bin/env python
"""
SOTP banking refinement test — Faz 6 ADIM 4.

3 TEST:
  1) KCHOL recursive (YKBNK banking DDM dahil)
  2) SAHOL recursive (AKBNK banking DDM dahil — büyük etki bekleniyor)
  3) Banking source flag (CONFIRMED vs PROVISIONAL fallback)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from dcf_engine.orchestrator import analyze_ticker


async def test_kchol_with_banking():
    print("\n" + "=" * 80)
    print("TEST 1 — KCHOL SOTP recursive (YKBNK banking DDM dahil)")
    print("=" * 80)

    report = await analyze_ticker("KCHOL", market_price_tl=205.0)

    print(f"  Success:          {report.success}")
    print(f"  Model:            {report.model_used}")
    print(f"  Value/Share TL:   {report.value_per_share_tl:.2f}" if report.value_per_share_tl else "  None")
    print(f"  Equity USD:       ${report.equity_value_usd/1e9:.2f}B" if report.equity_value_usd else "  None")
    print(f"  Upside:           {report.upside_pct:+.2f}%" if report.upside_pct else "  n/a")

    print(f"\n  YKBNK banking treatment:")
    for r in report.reasoning:
        if "YKBNK" in r or "banking" in r.lower():
            print(f"    • {r}")

    # Önceki state: KCHOL 203.26 TL (banking book × P/B 1.5)
    # Yeni: banking_ddm result kullanır (daha düşük muhtemel)
    expected_changed = report.value_per_share_tl is not None and report.value_per_share_tl != 203.26
    has_ddm_source = any("banking_ddm_dcf" in r or "DDM result CONFIRMED" in r
                         for r in report.reasoning)

    checks = [
        ("Success=True", report.success, True),
        ("Value/Share TL > 0",
         report.value_per_share_tl is not None and report.value_per_share_tl > 0, True),
        ("Banking DDM source used",
         has_ddm_source, True),
    ]

    all_pass = all(actual == expected for _, actual, expected in checks)
    if all_pass:
        print(f"\n  [PASS] KCHOL refined: {report.value_per_share_tl:.2f} TL (eski 203.26)")
    else:
        print(f"\n  [FAIL]")
        for name, actual, expected in checks:
            if actual != expected:
                print(f"    ✗ {name}: actual={actual}, expected={expected}")
    return all_pass


async def test_sahol_with_banking():
    print("\n" + "=" * 80)
    print("TEST 2 — SAHOL SOTP recursive (AKBNK banking DDM, büyük etki)")
    print("=" * 80)

    report = await analyze_ticker("SAHOL", market_price_tl=98.15)

    print(f"  Success:          {report.success}")
    print(f"  Model:            {report.model_used}")
    print(f"  Value/Share TL:   {report.value_per_share_tl:.2f}" if report.value_per_share_tl else "  None")
    print(f"  Equity USD:       ${report.equity_value_usd/1e9:.2f}B" if report.equity_value_usd else "  None")
    print(f"  Upside:           {report.upside_pct:+.2f}%" if report.upside_pct else "  n/a")

    print(f"\n  AKBNK banking treatment:")
    for r in report.reasoning:
        if "AKBNK" in r or "banking" in r.lower():
            print(f"    • {r}")

    # Önceki state: SAHOL 202.09 TL (AKBNK book × P/B 1.5 = $7.38B contribution)
    # Yeni: AKBNK DDM ($14.55B at 100% × 41% ownership = $5.97B) — daha düşük
    has_ddm_source = any("banking_ddm_dcf" in r or "DDM result CONFIRMED" in r
                         for r in report.reasoning)

    checks = [
        ("Success=True", report.success, True),
        ("Value/Share TL > 0",
         report.value_per_share_tl is not None and report.value_per_share_tl > 0, True),
        ("Banking DDM source used (AKBNK)", has_ddm_source, True),
    ]

    all_pass = all(actual == expected for _, actual, expected in checks)
    if all_pass:
        print(f"\n  [PASS] SAHOL refined: {report.value_per_share_tl:.2f} TL (eski 202.09)")
    else:
        print(f"\n  [FAIL]")
    return all_pass


async def test_ykbnk_direct():
    print("\n" + "=" * 80)
    print("TEST 3 — YKBNK direct (banking_ddm execute)")
    print("=" * 80)

    report = await analyze_ticker("YKBNK", market_price_tl=20.0)

    print(f"  Success:          {report.success}")
    print(f"  is_banking:       {report.is_banking}")
    print(f"  Model:            {report.model_used}")
    print(f"  Value/Share TL:   {report.value_per_share_tl:.2f}" if report.value_per_share_tl else "  None")
    print(f"  CoE:              {report.wacc*100:.2f}%" if report.wacc else "  None")

    checks = [
        ("Success=True", report.success, True),
        ("is_banking=True", report.is_banking, True),
        ("Model=banking_ddm", report.model_used, "banking_ddm"),
        ("Value/Share TL > 0",
         report.value_per_share_tl is not None and report.value_per_share_tl > 0, True),
    ]

    all_pass = all(actual == expected for _, actual, expected in checks)
    if all_pass:
        print(f"\n  [PASS] YKBNK DDM: {report.value_per_share_tl:.2f} TL/share")
    else:
        print(f"\n  [FAIL]")
    return all_pass


async def main() -> int:
    print("\n" + "#" * 80)
    print("# SOTP Banking Refinement TEST (Faz 6 ADIM 4)")
    print("#" * 80)

    results = [
        ("TEST 1 KCHOL with banking DDM",  await test_kchol_with_banking()),
        ("TEST 2 SAHOL with banking DDM",   await test_sahol_with_banking()),
        ("TEST 3 YKBNK direct",              await test_ykbnk_direct()),
    ]

    print("\n" + "#" * 80)
    print("# ÖZET")
    print("#" * 80)
    for name, ok in results:
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}")

    all_pass = all(ok for _, ok in results)
    print(f"\n  Toplam: {sum(1 for _, ok in results if ok)}/{len(results)}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
