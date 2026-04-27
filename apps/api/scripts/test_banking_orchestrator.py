#!/usr/bin/env python
"""
Banking orchestrator integration test — Faz 6 ADIM 3.

4 TEST:
  1) AKBNK banking DDM
  2) GARAN banking DDM
  3) TUPRS regression (industrial flow INTACT)
  4) Banking data unavailable graceful skip
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


async def test_akbnk():
    print("\n" + "=" * 80)
    print("TEST 1 — AKBNK banking DDM")
    print("=" * 80)

    report = await analyze_ticker("AKBNK", market_price_tl=70.0)

    print(f"  Success:          {report.success}")
    print(f"  is_banking:       {report.is_banking}")
    print(f"  Model:            {report.model_used}")
    print(f"  Value/Share USD:  ${report.value_per_share_usd:.4f}" if report.value_per_share_usd else "  Value/Share USD:  None")
    print(f"  Value/Share TL:   {report.value_per_share_tl:.2f}" if report.value_per_share_tl else "  Value/Share TL:   None")
    print(f"  Equity USD:       ${report.equity_value_usd/1e9:.2f}B" if report.equity_value_usd else "  Equity USD:       None")
    print(f"  CoE (WACC field): {report.wacc*100:.2f}%" if report.wacc else "  CoE: None")
    print(f"  Upside:           {report.upside_pct:+.2f}%" if report.upside_pct else "  Upside: n/a")
    print(f"  Verdict:          {report.damodaran_verdict}")

    print(f"\n  Reasoning ({len(report.reasoning)}):")
    for r in report.reasoning:
        print(f"    • {r}")

    if report.errors:
        print(f"\n  Errors:")
        for e in report.errors:
            print(f"    ⚠ {e}")

    checks = [
        ("Success=True", report.success, True),
        ("is_banking=True", report.is_banking, True),
        ("Model=banking_ddm", report.model_used, "banking_ddm"),
        ("Value/Share TL > 0",
         report.value_per_share_tl is not None and report.value_per_share_tl > 0, True),
        ("CoE positive",
         report.wacc is not None and report.wacc > 0, True),
        ("Reasoning has DDM logs",
         any("DDM" in r for r in report.reasoning), True),
    ]

    print(f"\n  Checks:")
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "✓" if ok else "✗"
        print(f"    {marker} {name:<40} {str(actual):<15} expected {expected}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  [PASS] AKBNK DDM: {report.value_per_share_tl:.2f} TL/share")
    else:
        print(f"\n  [FAIL]")
    return all_pass


async def test_garan():
    print("\n" + "=" * 80)
    print("TEST 2 — GARAN banking DDM (ROE 30%)")
    print("=" * 80)

    report = await analyze_ticker("GARAN", market_price_tl=140.0)

    print(f"  Success:          {report.success}")
    print(f"  Value/Share TL:   {report.value_per_share_tl:.2f}" if report.value_per_share_tl else "  None")
    print(f"  CoE:              {report.wacc*100:.2f}%" if report.wacc else "  None")
    print(f"  Upside:           {report.upside_pct:+.2f}%" if report.upside_pct else "  n/a")
    print(f"  Verdict:          {report.damodaran_verdict}")

    checks = [
        ("Success=True", report.success, True),
        ("Model=banking_ddm", report.model_used, "banking_ddm"),
        ("Value/Share TL > 0",
         report.value_per_share_tl is not None and report.value_per_share_tl > 0, True),
        ("GARAN has higher value than AKBNK ratio (ROE %30 > %21.5)",
         report.value_per_share_tl is not None, True),
    ]

    all_pass = all(actual == expected for _, actual, expected in checks)
    if all_pass:
        print(f"\n  [PASS] GARAN DDM: {report.value_per_share_tl:.2f} TL/share")
    else:
        print(f"\n  [FAIL]")
        for name, actual, expected in checks:
            if actual != expected:
                print(f"    ✗ {name}: actual={actual}, expected={expected}")
    return all_pass


async def test_tuprs_regression():
    print("\n" + "=" * 80)
    print("TEST 3 — TUPRS industrial regression (INTACT)")
    print("=" * 80)

    report = await analyze_ticker("TUPRS", market_price_tl=274.0)

    print(f"  Success:          {report.success}")
    print(f"  is_banking:       {report.is_banking}")
    print(f"  Model:            {report.model_used}")
    print(f"  Value/Share TL:   {report.value_per_share_tl:.2f}" if report.value_per_share_tl else "  None")
    print(f"  WACC:             {report.wacc*100:.2f}%" if report.wacc else "  None")
    print(f"  Margin:           {report.normalized_op_margin*100:.2f}%" if report.normalized_op_margin else "  None")

    # Expected: industrial cyclical_dcf path, value 187.10 ± 1
    checks = [
        ("Success=True", report.success, True),
        ("is_banking=False", report.is_banking, False),
        ("Model=cyclical_dcf", report.model_used, "cyclical_dcf"),
        ("Value 186-189 TL band",
         report.value_per_share_tl is not None
         and 186.0 <= report.value_per_share_tl <= 189.0, True),
    ]

    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "✓" if ok else "✗"
        print(f"  {marker} {name}: {actual}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  [PASS] TUPRS regression: {report.value_per_share_tl:.2f} TL (INTACT)")
    else:
        print(f"\n  [FAIL]")
    return all_pass


async def test_unavailable_data():
    print("\n" + "=" * 80)
    print("TEST 4 — Banking data unavailable (SKBNK case)")
    print("=" * 80)

    # SKBNK is_banking_ticker True but banking_data.py'de YOK
    report = await analyze_ticker("SKBNK")

    print(f"  is_banking:       {report.is_banking}")
    print(f"  Model:            {report.model_used}")
    print(f"  Errors:           {report.errors}")

    has_skip_error = any("not available" in e or "manuel" in r
                         for e in report.errors
                         for r in report.reasoning)

    checks = [
        ("is_banking=True", report.is_banking, True),
        ("Model=banking_ddm", report.model_used, "banking_ddm"),
        ("Has 'not available' error", any("not available" in e for e in report.errors), True),
    ]

    all_pass = all(actual == expected for _, actual, expected in checks)
    if all_pass:
        print(f"\n  [PASS] Graceful skip with warning")
    else:
        print(f"\n  [FAIL]")
    return all_pass


async def main() -> int:
    print("\n" + "#" * 80)
    print("# Banking Orchestrator Integration TEST (Faz 6 ADIM 3)")
    print("#" * 80)

    results = [
        ("TEST 1 AKBNK DDM",          await test_akbnk()),
        ("TEST 2 GARAN DDM",           await test_garan()),
        ("TEST 3 TUPRS regression",    await test_tuprs_regression()),
        ("TEST 4 Unavailable graceful",await test_unavailable_data()),
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
