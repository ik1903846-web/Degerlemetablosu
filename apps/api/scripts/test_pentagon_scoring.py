#!/usr/bin/env python
"""
Pentagon Scoring test runner — Faz 3 ADIM 2.

3 TEST:
  1) JSON-based batch scoring (latest bist_batch_LIVE_*.json)
  2) Anchor sanity check (TUPRS, SAHOL, FROTO expectations)
  3) Lifecycle weights validation (Mature Stable default)
"""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from portfolio.pentagon_scoring import (
    PentagonScore,
    score_from_json_dict,
    rank_by_composite,
    get_lifecycle_weights,
    LIFECYCLE_WEIGHTS,
)


def test_batch_scoring() -> bool:
    print("\n" + "=" * 80)
    print("TEST 1 — Batch scoring from latest JSON")
    print("=" * 80)

    project_root = Path(__file__).resolve().parents[3]
    outputs_dir = project_root / "apps/api/outputs"
    batches = sorted(outputs_dir.glob("bist_batch_LIVE_*.json"))
    if not batches:
        print("  [FAIL] No batch JSON found")
        return False
    latest = batches[-1]
    print(f"  Source: {latest.name}")

    data = json.loads(latest.read_text(encoding="utf-8"))
    scores = score_from_json_dict(data)

    print(f"  Total reports: {len(data['reports'])}")
    print(f"  Scored:        {len(scores)}")

    successful = sum(1 for r in data["reports"] if r.get("success"))
    coverage_ok = len(scores) == successful

    print()
    print(f"  {'Rank':<5} {'Ticker':<7} {'V':>5} {'G':>5} {'Q':>5} {'M':>5} {'R':>5} {'Comp':>7} Stage")
    print("  " + "-" * 75)

    ranked = rank_by_composite(scores)
    for i, s in enumerate(ranked, 1):
        print(
            f"  {i:<5} {s.ticker:<7} "
            f"{s.value:>5.0f} {s.growth:>5.0f} {s.quality:>5.0f} "
            f"{s.momentum:>5.0f} {s.risk:>5.0f} {s.composite:>7.1f} "
            f"{s.lifecycle_stage}"
        )

    composites = [s.composite for s in scores]
    range_ok = all(0 <= c <= 100 for c in composites)
    if coverage_ok and range_ok:
        print(f"\n  [PASS] {len(scores)} ticker scored, all composites in [0,100]")
        return True
    print(f"\n  [FAIL] coverage={coverage_ok}, range={range_ok}")
    return False


def test_anchor_sanity() -> bool:
    print("\n" + "=" * 80)
    print("TEST 2 — Anchor sanity check (TUPRS, SAHOL, FROTO)")
    print("=" * 80)

    project_root = Path(__file__).resolve().parents[3]
    outputs_dir = project_root / "apps/api/outputs"
    batches = sorted(outputs_dir.glob("bist_batch_LIVE_*.json"))
    data = json.loads(batches[-1].read_text(encoding="utf-8"))
    scores = score_from_json_dict(data)
    by_ticker = {s.ticker: s for s in scores}

    checks = []

    # TUPRS: SAT (-%32), low Value score expected (low cheapness)
    tuprs = by_ticker.get("TUPRS")
    if tuprs:
        tuprs_value_low = tuprs.value < 50  # SAT → Value < 50
        tuprs_quality_high = tuprs.quality > 60  # Mature Stable + low stdev
        checks.append(("TUPRS Value<50 (SAT signal)", tuprs_value_low, True))
        checks.append(("TUPRS Quality>60 (Mature Stable)", tuprs_quality_high, True))

    # SAHOL: Deep value AL (+%106), high Value
    sahol = by_ticker.get("SAHOL")
    if sahol:
        sahol_value_high = sahol.value > 70  # +%106 → Value > 70
        checks.append(("SAHOL Value>70 (deep value)", sahol_value_high, True))

    # FROTO: AL (+%187), high Value
    froto = by_ticker.get("FROTO")
    if froto:
        froto_value_high = froto.value > 80  # +%187 → Value > 80
        checks.append(("FROTO Value>80 (extreme upside)", froto_value_high, True))

    print(f"\n  {'Check':<45} {'Result':<10} {'Expected':<10}")
    print(f"  {'-'*45} {'-'*10} {'-'*10}")
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "✓" if ok else "✗"
        print(f"  {marker} {name:<43} {str(actual):<10} {str(expected):<10}")
        if not ok:
            all_pass = False

    if tuprs:
        print(f"\n  TUPRS: V={tuprs.value:.0f}, G={tuprs.growth:.0f}, "
              f"Q={tuprs.quality:.0f}, R={tuprs.risk:.0f}, Comp={tuprs.composite:.1f}")
    if sahol:
        print(f"  SAHOL: V={sahol.value:.0f}, G={sahol.growth:.0f}, "
              f"Q={sahol.quality:.0f}, R={sahol.risk:.0f}, Comp={sahol.composite:.1f}")
    if froto:
        print(f"  FROTO: V={froto.value:.0f}, G={froto.growth:.0f}, "
              f"Q={froto.quality:.0f}, R={froto.risk:.0f}, Comp={froto.composite:.1f}")

    if all_pass:
        print(f"\n  [PASS] {len(checks)}/{len(checks)} anchor checks")
        return True
    print("\n  [FAIL]")
    return False


def test_lifecycle_weights() -> bool:
    print("\n" + "=" * 80)
    print("TEST 3 — Lifecycle weights validation")
    print("=" * 80)

    checks = []

    # Mature Stable Value 35
    ws = get_lifecycle_weights("MATURE_STABLE")
    checks.append(("Mature Stable Value=0.35", ws["value"], 0.35))
    checks.append(("Mature Stable sum=1.0", round(sum(ws.values()), 4), 1.0))

    # Mature Growth Growth 25
    ws = get_lifecycle_weights("MATURE_GROWTH")
    checks.append(("Mature Growth Growth=0.25", ws["growth"], 0.25))
    checks.append(("Mature Growth sum=1.0", round(sum(ws.values()), 4), 1.0))

    # High Growth Growth 35
    ws = get_lifecycle_weights("HIGH_GROWTH")
    checks.append(("High Growth Growth=0.35", ws["growth"], 0.35))

    # Distress Risk 30
    ws = get_lifecycle_weights("DISTRESS")
    checks.append(("Distress Risk=0.30", ws["risk"], 0.30))

    # Unknown → fallback Mature Stable
    ws_unk = get_lifecycle_weights("UNKNOWN")
    ws_def = get_lifecycle_weights("FOOBAR")
    checks.append(("Unknown == Foobar (fallback)", ws_unk == ws_def, True))

    # All 6 stages defined
    expected_stages = {"MATURE_STABLE", "MATURE_GROWTH", "HIGH_GROWTH",
                       "YOUNG", "DECLINE", "DISTRESS"}
    defined = set(LIFECYCLE_WEIGHTS.keys())
    checks.append(("All 6 stages defined", expected_stages.issubset(defined), True))

    print(f"\n  {'Check':<45} {'Result':<15} {'Expected':<15}")
    print(f"  {'-'*45} {'-'*15} {'-'*15}")
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "✓" if ok else "✗"
        print(f"  {marker} {name:<43} {str(actual)[:13]:<15} {str(expected)[:13]:<15}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  [PASS] {len(checks)}/{len(checks)} weight checks")
        return True
    print("\n  [FAIL]")
    return False


def main() -> int:
    print("\n" + "#" * 80)
    print("# Pentagon Scoring TEST RUNNER (Faz 3 ADIM 2)")
    print("#" * 80)

    results = [
        ("TEST 1 batch scoring",      test_batch_scoring()),
        ("TEST 2 anchor sanity",       test_anchor_sanity()),
        ("TEST 3 lifecycle weights",   test_lifecycle_weights()),
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
