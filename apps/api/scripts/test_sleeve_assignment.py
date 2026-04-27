#!/usr/bin/env python
"""
Sleeve Assignment test runner — Faz 3 ADIM 3.

3 TEST:
  1) Batch assignment (latest bist_batch JSON)
  2) Anchor sanity (SAHOL/CCOLA/ARCLK/TUPRS/THYAO expectations)
  3) Risk profile allocations validation
"""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from portfolio.pentagon_scoring import score_from_json_dict
from portfolio.sleeve_assignment import (
    Sleeve,
    assign_batch,
    summarize_sleeves,
    get_risk_profile_allocations,
    RISK_PROFILES,
)


def _load_latest_batch():
    project_root = Path(__file__).resolve().parents[3]
    outputs_dir = project_root / "apps/api/outputs"
    batches = sorted(outputs_dir.glob("bist_batch_LIVE_*.json"))
    if not batches:
        raise FileNotFoundError("No batch JSON")
    return json.loads(batches[-1].read_text(encoding="utf-8")), batches[-1].name


def test_batch_assignment() -> bool:
    print("\n" + "=" * 80)
    print("TEST 1 — Batch sleeve assignment from latest JSON")
    print("=" * 80)

    data, fname = _load_latest_batch()
    print(f"  Source: {fname}")

    scores = score_from_json_dict(data)
    reports = data.get("reports", [])
    assignments = assign_batch(reports, scores)

    print(f"  Total reports:       {len(reports)}")
    print(f"  Pentagon scored:     {len(scores)}")
    print(f"  Sleeve assignments:  {len(assignments)}")

    summary = summarize_sleeves(assignments)
    print(f"\n  Counts:")
    for sleeve_name, count in summary["counts"].items():
        tickers = ", ".join(summary["by_sleeve"][sleeve_name])
        print(f"    {sleeve_name:<15s}: {count:>2}  ({tickers})")

    if summary["yuksek_kazanc_subs"]:
        print(f"\n  YÜKSEK KAZANÇ alt-kategoriler:")
        for sub, tickers in summary["yuksek_kazanc_subs"].items():
            print(f"    {sub:<30s}: {', '.join(tickers)}")

    print(f"\n  Per-ticker assignments:")
    print(f"  {'Ticker':<7} {'Sleeve':<15s} {'Sub':<30} {'Comp':>6} {'Conf':>5}")
    print("  " + "-" * 70)
    for a in assignments:
        sub = a.sub_category or ""
        print(f"  {a.ticker:<7} {a.sleeve.value:<15s} {sub:<30} "
              f"{a.composite:>6.1f} {a.confidence:>5.2f}")

    coverage_ok = len(assignments) == len(scores)
    if coverage_ok:
        print(f"\n  [PASS] {len(assignments)} ticker assigned")
        return True
    print(f"\n  [FAIL] coverage gap: {len(assignments)}/{len(scores)}")
    return False


def test_anchor_sanity() -> bool:
    print("\n" + "=" * 80)
    print("TEST 2 — Anchor sanity")
    print("=" * 80)

    data, _ = _load_latest_batch()
    scores = score_from_json_dict(data)
    reports = data.get("reports", [])
    assignments = assign_batch(reports, scores)
    by_ticker = {a.ticker: a for a in assignments}

    checks = []

    # SAHOL → YÜKSEK KAZANÇ holding (chronic discount)
    sahol = by_ticker.get("SAHOL")
    if sahol:
        sahol_yk = sahol.sleeve == Sleeve.YUKSEK_KAZANC
        sahol_sub = sahol.sub_category == "holding_chronic_discount"
        checks.append(("SAHOL → YÜKSEK KAZANÇ", sahol_yk, True))
        checks.append(("SAHOL sub=holding_chronic_discount", sahol_sub, True))

    # CCOLA → YÜKSEK KAZANÇ deep_value (+%418)
    ccola = by_ticker.get("CCOLA")
    if ccola:
        ccola_yk = ccola.sleeve == Sleeve.YUKSEK_KAZANC
        ccola_sub = ccola.sub_category == "deep_value"
        checks.append(("CCOLA → YÜKSEK KAZANÇ", ccola_yk, True))
        checks.append(("CCOLA sub=deep_value", ccola_sub, True))

    # FROTO → YÜKSEK KAZANÇ deep_value (+%187)
    froto = by_ticker.get("FROTO")
    if froto:
        froto_yk = froto.sleeve == Sleeve.YUKSEK_KAZANC
        checks.append(("FROTO → YÜKSEK KAZANÇ", froto_yk, True))

    # ARCLK → CORE (+%52, mature stable)
    arclk = by_ticker.get("ARCLK")
    if arclk:
        arclk_core = arclk.sleeve == Sleeve.CORE
        checks.append(("ARCLK → CORE (mature stable)", arclk_core, True))

    # TUPRS → SKIP (upside -%32 < -30)
    tuprs = by_ticker.get("TUPRS")
    if tuprs:
        tuprs_skip = tuprs.sleeve == Sleeve.SKIP
        checks.append(("TUPRS → SKIP (upside -%32)", tuprs_skip, True))

    # THYAO → SKIP (negatif DCF)
    thyao = by_ticker.get("THYAO")
    if thyao:
        thyao_skip = thyao.sleeve == Sleeve.SKIP
        checks.append(("THYAO → SKIP (negatif DCF)", thyao_skip, True))

    # PETKM → SKIP (negatif DCF)
    petkm = by_ticker.get("PETKM")
    if petkm:
        petkm_skip = petkm.sleeve == Sleeve.SKIP
        checks.append(("PETKM → SKIP (negatif DCF)", petkm_skip, True))

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
        print(f"\n  [PASS] {len(checks)}/{len(checks)} anchor checks")
        return True
    print("\n  [FAIL]")
    return False


def test_risk_profiles() -> bool:
    print("\n" + "=" * 80)
    print("TEST 3 — Risk profile allocations")
    print("=" * 80)

    checks = []

    konservatif = get_risk_profile_allocations("konservatif")
    checks.append(("Konservatif Core=0.80",     konservatif["core"], 0.80))
    checks.append(("Konservatif sum=1.0",        round(sum(konservatif.values()), 4), 1.0))

    dengeli = get_risk_profile_allocations("dengeli")
    checks.append(("Dengeli Core=0.60",          dengeli["core"], 0.60))
    checks.append(("Dengeli Hızlı=0.25",         dengeli["hizli_buyume"], 0.25))
    checks.append(("Dengeli Yüksek=0.15",        dengeli["yuksek_kazanc"], 0.15))
    checks.append(("Dengeli sum=1.0",            round(sum(dengeli.values()), 4), 1.0))

    agresif = get_risk_profile_allocations("agresif")
    checks.append(("Agresif Core=0.40",          agresif["core"], 0.40))
    checks.append(("Agresif sum=1.0",            round(sum(agresif.values()), 4), 1.0))

    # Default (unknown profile)
    default = get_risk_profile_allocations("foobar")
    checks.append(("Foobar → Dengeli fallback",  default == dengeli, True))

    # Case insensitive
    upper = get_risk_profile_allocations("DENGELI")
    checks.append(("Case-insensitive (DENGELI)", upper == dengeli, True))

    print(f"\n  {'Check':<45} {'Result':<15} {'Expected':<15}")
    print(f"  {'-'*45} {'-'*15} {'-'*15}")
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "✓" if ok else "✗"
        print(f"  {marker} {name[:43]:<45} {str(actual)[:13]:<15} {str(expected)[:13]:<15}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  [PASS] {len(checks)}/{len(checks)} risk profile checks")
        return True
    print("\n  [FAIL]")
    return False


def main() -> int:
    print("\n" + "#" * 80)
    print("# Sleeve Assignment TEST RUNNER (Faz 3 ADIM 3)")
    print("#" * 80)

    results = [
        ("TEST 1 batch assignment",  test_batch_assignment()),
        ("TEST 2 anchor sanity",      test_anchor_sanity()),
        ("TEST 3 risk profiles",      test_risk_profiles()),
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
