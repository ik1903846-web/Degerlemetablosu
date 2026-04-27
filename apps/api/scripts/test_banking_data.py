#!/usr/bin/env python
"""
Banking data config test — Faz 6 ADIM 2.

3 TEST:
  1) 5 ticker config + 4-yıl yearly data structure
  2) Data sanity (EPS positive, ROE range, payout range)
  3) Public API (get_banking_data, is_banking_data_available, list)
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.banking_data import (
    BANKING_DATA,
    BankingDataConfig,
    BankingYearlyData,
    get_banking_data,
    is_banking_data_available,
    list_banking_tickers,
    get_latest_year_data,
)


EXPECTED_TICKERS = ["AKBNK", "GARAN", "HALKB", "ISCTR", "YKBNK"]


def test_structure() -> bool:
    print("\n" + "=" * 80)
    print("TEST 1 — 5 ticker config + 4-yıl yearly data structure")
    print("=" * 80)

    print(f"\n  Total tickers: {len(BANKING_DATA)}")
    print(f"  Listed: {list_banking_tickers()}")

    checks = []
    checks.append(("Ticker count = 5", len(BANKING_DATA), 5))

    for ticker in EXPECTED_TICKERS:
        config = get_banking_data(ticker)
        checks.append((f"{ticker} config exists", config is not None, True))
        if config:
            checks.append((f"{ticker} has 4-year yearly", len(config.yearly), 4))
            checks.append((f"{ticker} source_urls non-empty", len(config.source_urls) > 0, True))

    print(f"\n  {'Check':<45} {'Result':<10} {'Expected':<10}")
    print(f"  {'-'*45} {'-'*10} {'-'*10}")
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "✓" if ok else "✗"
        print(f"  {marker} {name[:43]:<45} {str(actual)[:8]:<10} {str(expected)[:8]:<10}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  [PASS] {len(checks)}/{len(checks)} structure checks")
        return True
    print("\n  [FAIL]")
    return False


def test_data_sanity() -> bool:
    print("\n" + "=" * 80)
    print("TEST 2 — Data sanity (EPS positive, ROE range, payout range)")
    print("=" * 80)

    print(f"\n  Per-ticker latest year (2024) summary:")
    print(f"  {'Ticker':<7} {'NI (B TL)':>10} {'EPS (TL)':>10} {'DPS (TL)':>10} "
          f"{'BV/share':>10} {'ROE %':>7} {'Pay %':>7} {'Conf':<10}")
    print(f"  {'-'*7} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*7} {'-'*7} {'-'*10}")

    checks = []
    for ticker in EXPECTED_TICKERS:
        latest = get_latest_year_data(ticker)
        if latest is None:
            continue
        bvps = latest.book_value_per_share_tl
        print(
            f"  {ticker:<7} "
            f"{latest.net_income_tl/1000:>9.1f}B "
            f"{latest.eps_tl:>9.2f} "
            f"{latest.dps_tl:>9.2f} "
            f"{bvps:>9.2f} "
            f"{latest.roe_pct:>6.1f}% "
            f"{latest.payout_pct:>6.1f}% "
            f"{latest.confidence:<10}"
        )

        # Sanity checks
        checks.append((f"{ticker} EPS positive (2024)", latest.eps_tl > 0, True))
        checks.append((f"{ticker} BV/share positive", bvps > 0, True))
        checks.append((f"{ticker} ROE 5-50% range",
                       5.0 <= latest.roe_pct <= 50.0, True))
        checks.append((f"{ticker} payout 0-50% range",
                       0.0 <= latest.payout_pct <= 50.0, True))

    print(f"\n  {'Check':<55} {'Result':<10} {'Expected':<10}")
    print(f"  {'-'*55} {'-'*10} {'-'*10}")
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "✓" if ok else "✗"
        print(f"  {marker} {name[:53]:<55} {str(actual):<10} {str(expected):<10}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  [PASS] {len(checks)}/{len(checks)} data sanity checks")
        return True
    print("\n  [FAIL]")
    return False


def test_public_api() -> bool:
    print("\n" + "=" * 80)
    print("TEST 3 — Public API")
    print("=" * 80)

    checks = []

    # is_banking_data_available
    checks.append(("is_banking_data_available('AKBNK')",
                   is_banking_data_available("AKBNK"), True))
    checks.append(("is_banking_data_available('akbnk')",
                   is_banking_data_available("akbnk"), True))
    checks.append(("is_banking_data_available('TUPRS')",
                   is_banking_data_available("TUPRS"), False))

    # get_banking_data
    config = get_banking_data("GARAN")
    checks.append(("get_banking_data('GARAN').sector",
                   config.sector if config else None, "bank_money_center"))
    checks.append(("get_banking_data('UNKNOWN') is None",
                   get_banking_data("UNKNOWN") is None, True))

    # list_banking_tickers
    tickers = list_banking_tickers()
    checks.append(("list_banking_tickers count", len(tickers), 5))
    checks.append(("list_banking_tickers sorted",
                   tickers == sorted(tickers), True))

    # get_latest_year_data
    latest = get_latest_year_data("AKBNK")
    checks.append(("AKBNK latest year=2024",
                   latest.year if latest else None, 2024))

    # CONFIRMED flag check (en az 1 ticker 2024 CONFIRMED)
    confirmed_count = sum(
        1 for t in EXPECTED_TICKERS
        if (latest := get_latest_year_data(t)) is not None
        and latest.confidence == "CONFIRMED"
    )
    checks.append(("CONFIRMED 2024 ticker count >= 4",
                   confirmed_count >= 4, True))

    print(f"\n  {'Check':<55} {'Result':<15} {'Expected':<15}")
    print(f"  {'-'*55} {'-'*15} {'-'*15}")
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "✓" if ok else "✗"
        print(f"  {marker} {name[:53]:<55} {str(actual)[:13]:<15} {str(expected)[:13]:<15}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  [PASS] {len(checks)}/{len(checks)} API checks")
        return True
    print("\n  [FAIL]")
    return False


def main() -> int:
    print("\n" + "#" * 80)
    print("# Banking Data Config TEST RUNNER (Faz 6 ADIM 2)")
    print("#" * 80)

    results = [
        ("TEST 1 structure",      test_structure()),
        ("TEST 2 data sanity",     test_data_sanity()),
        ("TEST 3 public API",      test_public_api()),
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
    sys.exit(main())
