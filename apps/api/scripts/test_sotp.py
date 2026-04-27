#!/usr/bin/env python
"""
Test: sotp.py — Faz 2.5 ADIM 3 SOTP value calculator.

4 TEST:
  1) SAHOL with empty dcf_lookups (full book fallback)
  2) KCHOL with realistic dcf_lookups (Component 4 batch values)
  3) Edge cases (invalid ticker, custom disconto override)
  4) Diagnostic warnings (DCF missing, banking PROVISIONAL, source tracking)
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.sotp import (
    calculate_sotp_value,
    format_sotp_breakdown,
    SOTPResult,
    SOTPChildContribution,
)


SPOT_RATE = 35.37  # DAMODARAN_PARAMS spot 24 Nis 2026


# ============================================================================
# TEST 1 — SAHOL with empty dcf_lookups (full book fallback)
# ============================================================================

def test_sahol_empty_lookups() -> bool:
    print("\n" + "=" * 80)
    print("TEST 1 — SAHOL with empty dcf_lookups")
    print("=" * 80)

    result = calculate_sotp_value("SAHOL", dcf_lookups={})
    if result is None:
        print("  [FAIL] SOTP calc returned None")
        return False

    print(format_sotp_breakdown(result))

    # SAHOL shares outstanding ≈ 2.04B (per shares_fetcher)
    sahol_shares = 2_040_403_931
    per_share_usd = result.net_value_usd / sahol_shares
    per_share_tl = per_share_usd * SPOT_RATE
    print(f"\n  Per-share USD:   ${per_share_usd:.2f}")
    print(f"  Per-share TL:    {per_share_tl:.2f}")
    print(f"  Market (~99 TL): chronic discount expected")

    # PASS criteria — methodology-aligned bounds
    # Empty lookups → all listed via book × 1.0
    # Banking AKBNK $12B × 1.5 × 41% = $7.38B
    # Listed (9) book values × stakes = ~$2.92B
    # Non-listed (6) = ~$3.06B
    # Net cash $0.351B → gross + cash ~$13.7B
    # Disconto %15 → $11.7B
    # Per share ~$5.71, ~202 TL
    net_value_ok = 10_000_000_000 <= result.net_value_usd <= 13_000_000_000
    per_share_tl_ok = 180 <= per_share_tl <= 220
    warnings_ok = any("book fallback" in w.lower() for w in result.warnings)
    listed_count = sum(1 for c in result.children if c.source == "book_fallback")
    listed_ok = listed_count == 9  # 9 listed children fell back

    if net_value_ok and per_share_tl_ok and warnings_ok and listed_ok:
        print(f"\n  [PASS] net_value=${result.net_value_usd/1e9:.2f}B, "
              f"per_share={per_share_tl:.0f} TL, "
              f"book_fallback count={listed_count}")
        return True
    print(f"\n  [FAIL] net_value_ok={net_value_ok}, "
          f"per_share_ok={per_share_tl_ok}, "
          f"warnings_ok={warnings_ok}, "
          f"listed_ok={listed_ok}")
    return False


# ============================================================================
# TEST 2 — KCHOL with realistic dcf_lookups
# ============================================================================

def test_kchol_with_lookups() -> bool:
    print("\n" + "=" * 80)
    print("TEST 2 — KCHOL with realistic dcf_lookups (Component 4 batch values)")
    print("=" * 80)

    # Component 4 batch (commit 4256744) values, USD-converted
    # value_per_share_tl × shares ÷ spot = equity_value_usd
    dcf_lookups = {
        "TUPRS": 188.29 * 1_926_795_598 / SPOT_RATE,   # ~$10.26B
        "FROTO": 671.37 * 350_910_000 / SPOT_RATE,     # ~$6.66B
        "ARCLK": 311.54 * 675_728_205 / SPOT_RATE,     # ~$5.95B
        "TOASO": 114.90 * 500_000_000 / SPOT_RATE,     # ~$1.62B
    }
    print(f"  dcf_lookups (Component 4 batch derived):")
    for t, v in dcf_lookups.items():
        print(f"    {t}: ${v/1e9:.3f}B")

    result = calculate_sotp_value("KCHOL", dcf_lookups=dcf_lookups)
    if result is None:
        print("  [FAIL] SOTP calc returned None")
        return False

    print()
    print(format_sotp_breakdown(result))

    # KCHOL shares ≈ 2.536B (per shares_fetcher)
    kchol_shares = 2_535_898_345
    per_share_usd = result.net_value_usd / kchol_shares
    per_share_tl = per_share_usd * SPOT_RATE
    print(f"\n  Per-share USD:   ${per_share_usd:.2f}")
    print(f"  Per-share TL:    {per_share_tl:.2f}")
    print(f"  Market (~207 TL): comparison")

    # PASS criteria — TUPRS, FROTO, ARCLK, TOASO use DCF lookup
    # OTKAR, TTRAK, AYGAZ use book_fallback
    # YKBNK banking
    dcf_lookup_count = sum(1 for c in result.children if c.source == "dcf_lookup")
    book_fallback_count = sum(1 for c in result.children if c.source == "book_fallback")
    banking_count = sum(1 for c in result.children if c.source == "banking_book_pb_15")
    non_listed_count = sum(1 for c in result.children if c.source == "non_listed_book")

    print(f"\n  Source breakdown:")
    print(f"    dcf_lookup:        {dcf_lookup_count} (expected 4 — TUPRS/FROTO/ARCLK/TOASO)")
    print(f"    book_fallback:     {book_fallback_count} (expected 3 — OTKAR/TTRAK/AYGAZ)")
    print(f"    banking_book_pb_15: {banking_count} (expected 1 — YKBNK)")
    print(f"    non_listed_book:   {non_listed_count} (expected 4 — pools)")

    sources_ok = (
        dcf_lookup_count == 4
        and book_fallback_count == 3
        and banking_count == 1
        and non_listed_count == 4
    )
    # KCHOL net intrinsic ~$15-19B band, per_share TL band 200-260
    net_value_ok = 13_000_000_000 <= result.net_value_usd <= 20_000_000_000
    per_share_tl_ok = 180 <= per_share_tl <= 280

    if sources_ok and net_value_ok and per_share_tl_ok:
        print(f"\n  [PASS] sources OK, net_value=${result.net_value_usd/1e9:.2f}B, "
              f"per_share={per_share_tl:.0f} TL")
        return True
    print(f"\n  [FAIL] sources_ok={sources_ok}, net_value_ok={net_value_ok}, "
          f"per_share_ok={per_share_tl_ok}")
    return False


# ============================================================================
# TEST 3 — Edge cases
# ============================================================================

def test_edge_cases() -> bool:
    print("\n" + "=" * 80)
    print("TEST 3 — Edge cases")
    print("=" * 80)

    checks = []

    # Invalid ticker
    invalid = calculate_sotp_value("UNKNOWN", dcf_lookups={})
    checks.append(("calculate_sotp_value('UNKNOWN')", invalid, None))

    # Lowercase ticker (case-insensitive via get_portfolio)
    lower_result = calculate_sotp_value("sahol", dcf_lookups={})
    lower_ok = lower_result is not None and lower_result.parent_ticker == "SAHOL"
    checks.append(("calculate_sotp_value('sahol') resolves", lower_ok, True))

    # Custom disconto override
    custom_result = calculate_sotp_value(
        "SAHOL", dcf_lookups={}, disconto_override=0.30,
    )
    custom_ok = (
        custom_result is not None
        and abs(custom_result.disconto_pct - 0.30) < 1e-6
    )
    checks.append(("disconto_override=0.30", custom_ok, True))

    # Custom disconto produces lower net_value
    default_result = calculate_sotp_value("SAHOL", dcf_lookups={})
    if default_result is not None and custom_result is not None:
        net_diff_ok = custom_result.net_value_usd < default_result.net_value_usd
    else:
        net_diff_ok = False
    checks.append(("custom disconto reduces net_value", net_diff_ok, True))

    # KCHOL with no lookups also works
    kchol_empty = calculate_sotp_value("KCHOL", dcf_lookups={})
    kchol_empty_ok = kchol_empty is not None and kchol_empty.gross_value_usd > 0
    checks.append(("KCHOL empty lookups still computes", kchol_empty_ok, True))

    print(f"  {'Check':<55} {'Result':<15} {'Expected':<10}")
    print(f"  {'-'*55} {'-'*15} {'-'*10}")
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        status = "✓" if ok else "✗"
        print(f"  {status} {name[:53]:<55} {str(actual)[:13]:<15} {str(expected)[:8]:<10}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  [PASS] {len(checks)}/{len(checks)} edge case checks")
        return True
    print(f"\n  [FAIL]")
    return False


# ============================================================================
# TEST 4 — Diagnostic warnings + source tracking
# ============================================================================

def test_diagnostic_warnings() -> bool:
    print("\n" + "=" * 80)
    print("TEST 4 — Diagnostic warnings + source tracking")
    print("=" * 80)

    # SAHOL empty lookups → many warnings
    sahol_result = calculate_sotp_value("SAHOL", dcf_lookups={})
    if sahol_result is None:
        print("  [FAIL] None result")
        return False

    print(f"  SAHOL empty lookups warnings ({len(sahol_result.warnings)}):")
    for w in sahol_result.warnings[:10]:
        print(f"    ⚠ {w}")
    if len(sahol_result.warnings) > 10:
        print(f"    ... +{len(sahol_result.warnings)-10} more")

    # Specific warning checks
    checks = []

    # 1. Listed children with no DCF should warn
    has_dcf_missing_warning = any(
        "dcf lookup missing" in w.lower() for w in sahol_result.warnings
    )
    checks.append(("DCF missing warning present", has_dcf_missing_warning, True))

    # 2. Banking PROVISIONAL warning
    has_banking_provisional = any(
        "provisional" in w.lower() and "akbnk" in w.lower()
        for w in sahol_result.warnings
    )
    checks.append(("Banking AKBNK PROVISIONAL warning", has_banking_provisional, True))

    # 3. All listed children have source="book_fallback" (no DCF lookups)
    listed_sources = [c.source for c in sahol_result.children if c.type == "listed"]
    all_book_fallback = all(s == "book_fallback" for s in listed_sources)
    checks.append(("All listed → book_fallback (empty lookups)", all_book_fallback, True))

    # 4. Banking child source = banking_book_pb_15
    banking_sources = [c.source for c in sahol_result.children if c.type == "banking_listed"]
    banking_correct = all(s == "banking_book_pb_15" for s in banking_sources)
    checks.append(("Banking source = banking_book_pb_15", banking_correct, True))

    # 5. Non-listed source = non_listed_book
    nonlisted_sources = [c.source for c in sahol_result.children if c.type == "non_listed"]
    nonlisted_correct = all(s == "non_listed_book" for s in nonlisted_sources)
    checks.append(("Non-listed source = non_listed_book", nonlisted_correct, True))

    # 6. KCHOL with partial lookups → mixed sources
    partial_lookups = {
        "TUPRS": 10.26e9,
        "FROTO": 6.66e9,
    }
    kchol_partial = calculate_sotp_value("KCHOL", dcf_lookups=partial_lookups)
    if kchol_partial is None:
        checks.append(("KCHOL partial lookups", False, True))
    else:
        # TUPRS/FROTO should be dcf_lookup, ARCLK/TOASO/OTKAR/TTRAK/AYGAZ should be book_fallback
        tuprs_child = next(c for c in kchol_partial.children if c.ticker == "TUPRS")
        arclk_child = next(c for c in kchol_partial.children if c.ticker == "ARCLK")
        mixed_ok = (
            tuprs_child.source == "dcf_lookup"
            and arclk_child.source == "book_fallback"
        )
        checks.append(("KCHOL mixed sources (TUPRS=dcf, ARCLK=book)", mixed_ok, True))

    print(f"\n  {'Check':<55} {'Result':<10} {'Expected':<10}")
    print(f"  {'-'*55} {'-'*10} {'-'*10}")
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        status = "✓" if ok else "✗"
        print(f"  {status} {name[:53]:<55} {str(actual):<10} {str(expected):<10}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  [PASS] {len(checks)}/{len(checks)} diagnostic checks")
        return True
    print(f"\n  [FAIL]")
    return False


# ============================================================================
# Runner
# ============================================================================

def main() -> int:
    print("\n" + "#" * 80)
    print("# sotp.py — Faz 2.5 ADIM 3 SOTP value calculator")
    print("#" * 80)

    results = [
        ("TEST 1 SAHOL empty lookups", test_sahol_empty_lookups()),
        ("TEST 2 KCHOL with lookups",   test_kchol_with_lookups()),
        ("TEST 3 Edge cases",            test_edge_cases()),
        ("TEST 4 Diagnostic warnings",   test_diagnostic_warnings()),
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
