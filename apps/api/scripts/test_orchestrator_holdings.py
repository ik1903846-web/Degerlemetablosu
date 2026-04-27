#!/usr/bin/env python
"""
Test: orchestrator SOTP integration (Faz 2.5 ADIM 4).

3 TEST:
  1) KCHOL single-ticker mode (recursive child fetch + SOTP)
  2) SAHOL single-ticker mode (BIST 30 dışı children → book fallback)
  3) Backward-compat — TUPRS regression (Component 4 baseline 188.29 TL)
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import asyncio
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Proje root'undaki .env'i yükle (DATABASE_URL — Faz 2.4.6 Component 1)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from dcf_engine.orchestrator import analyze_ticker, print_report


# ============================================================================
# TEST 1 — KCHOL Single-Ticker Mode
# ============================================================================

async def test_kchol_single_ticker():
    print("\n" + "=" * 80)
    print("TEST 1 — KCHOL single-ticker mode (recursive child fetch)")
    print("=" * 80)
    print("Beklenen: ~40-60s, value_per_share_tl ≈ 220-240 TL band")

    t0 = time.perf_counter()
    report = await analyze_ticker("KCHOL")
    duration = time.perf_counter() - t0

    print(f"\n  Duration: {duration:.1f}s")
    print_report(report)

    # PASS criteria
    success_ok = report.success
    model_ok = report.model_used == "holding_sotp"
    has_value = report.value_per_share_tl is not None
    value_ok = (
        has_value and 180 <= report.value_per_share_tl <= 280
    )
    has_sotp_log = any("SOTP:" in r for r in report.reasoning)

    if success_ok and model_ok and value_ok and has_sotp_log:
        print(f"\n  [PASS] KCHOL SOTP: {report.value_per_share_tl:.2f} TL "
              f"(model={report.model_used})")
        return True
    print(f"\n  [FAIL] success={success_ok}, model={model_ok}, "
          f"value={value_ok}, sotp_log={has_sotp_log}")
    return False


# ============================================================================
# TEST 2 — SAHOL Single-Ticker Mode
# ============================================================================

async def test_sahol_single_ticker():
    print("\n" + "=" * 80)
    print("TEST 2 — SAHOL single-ticker mode (BIST 30 dışı children → book fallback)")
    print("=" * 80)
    print("Beklenen: ~5-15s, value_per_share_tl ≈ 195-215 TL band, limited DCF coverage")

    t0 = time.perf_counter()
    report = await analyze_ticker("SAHOL")
    duration = time.perf_counter() - t0

    print(f"\n  Duration: {duration:.1f}s")
    print_report(report)

    # PASS criteria
    success_ok = report.success
    model_ok = report.model_used == "holding_sotp"
    has_value = report.value_per_share_tl is not None
    value_ok = (
        has_value and 180 <= report.value_per_share_tl <= 230
    )
    has_limited_warning = any(
        "limited DCF coverage" in r or "book_fallback" in r.lower()
        for r in report.reasoning
    )

    if success_ok and model_ok and value_ok:
        print(f"\n  [PASS] SAHOL SOTP: {report.value_per_share_tl:.2f} TL "
              f"(model={report.model_used}, limited_coverage={has_limited_warning})")
        return True
    print(f"\n  [FAIL] success={success_ok}, model={model_ok}, value={value_ok}")
    return False


# ============================================================================
# TEST 3 — Backward-Compat TUPRS Regression
# ============================================================================

async def test_tuprs_backward_compat():
    print("\n" + "=" * 80)
    print("TEST 3 — Backward-compat TUPRS (Component 4 baseline 188.29 TL)")
    print("=" * 80)
    print("Beklenen: 188.29 ± 1 TL (industrial flow INTACT)")

    t0 = time.perf_counter()
    report = await analyze_ticker("TUPRS")  # no dcf_lookups
    duration = time.perf_counter() - t0

    print(f"\n  Duration: {duration:.1f}s")
    print(f"  Value/Share TL:  {report.value_per_share_tl}")
    print(f"  WACC:            {report.wacc*100:.2f}% (expected 12.81%)")
    print(f"  Margin:          {report.normalized_op_margin*100:.2f}% (expected 4.50%)")
    print(f"  Model:           {report.model_used} (expected cyclical_dcf)")

    # PASS criteria
    success_ok = report.success
    model_ok = report.model_used == "cyclical_dcf"
    value_ok = (
        report.value_per_share_tl is not None
        and 187 <= report.value_per_share_tl <= 190  # ±1 TL band
    )

    if success_ok and model_ok and value_ok:
        print(f"\n  [PASS] TUPRS regression: {report.value_per_share_tl:.2f} TL")
        return True
    print(f"\n  [FAIL] success={success_ok}, model={model_ok}, "
          f"value={value_ok} (got {report.value_per_share_tl})")
    return False


# ============================================================================
# Runner
# ============================================================================

async def main() -> int:
    print("\n" + "#" * 80)
    print("# Orchestrator SOTP Integration Test (Faz 2.5 ADIM 4)")
    print("#" * 80)

    results = [
        ("TEST 1 KCHOL single-ticker", await test_kchol_single_ticker()),
        ("TEST 2 SAHOL single-ticker", await test_sahol_single_ticker()),
        ("TEST 3 TUPRS backward-compat", await test_tuprs_backward_compat()),
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
