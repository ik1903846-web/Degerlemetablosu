#!/usr/bin/env python
"""
Portfolio Construction test runner — Faz 3 ADIM 4.

3 TEST:
  1) 3 risk profile (Konservatif/Dengeli/Agresif) portfolio plan
  2) Boş sleeve cash reallocation (BIST 30 Hızlı Büyüme)
  3) Concentration cap %10 aktif çalışıyor mu
"""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from portfolio.pentagon_scoring import score_from_json_dict
from portfolio.sleeve_assignment import assign_batch, Sleeve
from portfolio.portfolio_construction import (
    build_portfolio,
    format_portfolio_report,
    MAX_SINGLE_TICKER_PCT,
    MAX_CASH_PCT,
)


def _load_assignments():
    project_root = Path(__file__).resolve().parents[3]
    outputs_dir = project_root / "apps/api/outputs"
    batches = sorted(outputs_dir.glob("bist_batch_LIVE_*.json"))
    data = json.loads(batches[-1].read_text(encoding="utf-8"))
    scores = score_from_json_dict(data)
    reports = data.get("reports", [])
    assignments = assign_batch(reports, scores)
    return assignments, batches[-1].name


def test_three_profiles() -> bool:
    print("\n" + "=" * 80)
    print("TEST 1 — 3 risk profile portfolio plan")
    print("=" * 80)

    assignments, fname = _load_assignments()
    print(f"  Source: {fname}")
    print(f"  Assignments: {len(assignments)}")

    plans = {}
    for profile in ["konservatif", "dengeli", "agresif"]:
        plan = build_portfolio(assignments, profile, total_capital_tl=1_000_000)
        plans[profile] = plan
        print(format_portfolio_report(plan))

    # PASS koşulları
    checks = []
    for profile in ["konservatif", "dengeli", "agresif"]:
        plan = plans[profile]
        # Plan oluşturuldu
        checks.append((f"{profile}: plan oluşturuldu",
                       plan is not None, True))
        # Total weights + cash = 100
        total_alloc = sum(p.weight_pct for p in plan.positions) + plan.cash_reserve_pct
        checks.append((f"{profile}: total alloc = 100",
                       round(total_alloc, 1), 100.0))
        # Hızlı Büyüme boş (BIST 30 mature)
        hizli_count = plan.sleeve_breakdown.get("hizli_buyume", 0)
        checks.append((f"{profile}: hizli_buyume boş (BIST 30)",
                       hizli_count == 0, True))

    print(f"\n  {'Check':<55} {'Result':<12} {'Expected':<10}")
    print(f"  {'-'*55} {'-'*12} {'-'*10}")
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "✓" if ok else "✗"
        print(f"  {marker} {name[:53]:<55} {str(actual)[:10]:<12} {str(expected)[:8]:<10}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  [PASS] {len(checks)}/{len(checks)} profile checks")
        return True
    print("\n  [FAIL]")
    return False


def test_empty_sleeve_cash() -> bool:
    print("\n" + "=" * 80)
    print("TEST 2 — Boş sleeve cash reallocation")
    print("=" * 80)

    assignments, _ = _load_assignments()
    plan = build_portfolio(assignments, "dengeli", 1_000_000)

    # Hızlı Büyüme target 25% but BOŞ → cash'e gitmeli
    target_hizli = plan.target_allocations["hizli_buyume"]
    actual_hizli = plan.actual_allocations["hizli_buyume"]

    print(f"  Hızlı Büyüme: target {target_hizli}% → actual {actual_hizli}%")
    print(f"  Cash reasons:")
    for reason in plan.cash_reasons:
        print(f"    • {reason}")

    checks = [
        ("Hızlı Büyüme target=25%",      target_hizli, 25.0),
        ("Hızlı Büyüme actual=0%",        actual_hizli, 0.0),
        ("Cash reasons içerir 'hizli_buyume'",
         any("hizli_buyume" in r for r in plan.cash_reasons), True),
        ("Cash reserve > %10",            plan.cash_reserve_pct > 10.0, True),
    ]

    print(f"\n  {'Check':<50} {'Result':<12} {'Expected':<10}")
    print(f"  {'-'*50} {'-'*12} {'-'*10}")
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "✓" if ok else "✗"
        print(f"  {marker} {name[:48]:<50} {str(actual)[:10]:<12} {str(expected)[:8]:<10}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  [PASS] {len(checks)}/{len(checks)} cash reallocation checks")
        return True
    print("\n  [FAIL]")
    return False


def test_concentration_cap() -> bool:
    print("\n" + "=" * 80)
    print("TEST 3 — Concentration cap %10 aktif")
    print("=" * 80)

    assignments, _ = _load_assignments()

    # Konservatif Core %80 + 2 ticker → her birine %40 raw → cap %10 aktif
    plan = build_portfolio(assignments, "konservatif", 1_000_000)

    # Per ticker max %10
    max_weight = max((p.weight_pct for p in plan.positions), default=0.0)
    print(f"  Konservatif max single ticker: {max_weight:.1f}%")
    print(f"  Cap threshold: {MAX_SINGLE_TICKER_PCT}%")
    print(f"  Cap warnings:  {len([w for w in plan.warnings if 'capped' in w])}")

    cap_active = any("capped" in w for w in plan.warnings)
    cap_respected = max_weight <= MAX_SINGLE_TICKER_PCT + 0.01

    checks = [
        ("Max single ticker ≤ %10",       cap_respected, True),
        ("Cap warnings logged",            cap_active, True),
    ]

    # Cash reserve under-investment warning (boş sleeve + cap overflow → büyük cash)
    under_invest = plan.cash_reserve_pct > 50  # Konservatif Core'da büyük overflow
    print(f"  Konservatif cash reserve: {plan.cash_reserve_pct:.1f}%")
    if under_invest:
        print(f"  Under-investment warning beklenir (cap overflow)")
    checks.append(("Konservatif cash > 50%", under_invest, True))

    print(f"\n  {'Check':<45} {'Result':<12} {'Expected':<10}")
    print(f"  {'-'*45} {'-'*12} {'-'*10}")
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "✓" if ok else "✗"
        print(f"  {marker} {name[:43]:<45} {str(actual)[:10]:<12} {str(expected)[:8]:<10}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"\n  [PASS] {len(checks)}/{len(checks)} cap checks")
        return True
    print("\n  [FAIL]")
    return False


def main() -> int:
    print("\n" + "#" * 80)
    print("# Portfolio Construction TEST RUNNER (Faz 3 ADIM 4)")
    print("#" * 80)

    results = [
        ("TEST 1 three profiles",     test_three_profiles()),
        ("TEST 2 empty sleeve cash",   test_empty_sleeve_cash()),
        ("TEST 3 concentration cap",   test_concentration_cap()),
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
