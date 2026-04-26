#!/usr/bin/env python
"""İlk yıl projection — Heineken 2019 Year 1 birebir replicate."""
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.industrial_fcff import project_year, linear_taper


def main():
    # Heineken 2019 case yükle
    case_path = Path(__file__).parent.parent / "validation_cases" / "heineken_2019.json"
    with open(case_path, 'r', encoding='utf-8') as f:
        case = json.load(f)

    print("="*70)
    print("HEINEKEN 2019 — YEAR 1 PROJECTION TEST")
    print("="*70)

    # Inputs
    prev_revenues = case['operating']['revenues_ltm_millions']
    growth = case['growth']['year_1_5_revenue_growth']
    ebit_margin = case['operating']['operating_margin_ltm']  # Year 1 yaklaşık
    tax_rate = case['operating']['effective_tax_rate_ltm']
    sales_to_capital = case['operating']['sales_to_invested_capital_5y_avg']

    print(f"\n[INPUTS]")
    print(f"  Previous revenues: €{prev_revenues:,}M")
    print(f"  Revenue growth:    {growth*100:.2f}%")
    print(f"  EBIT margin (LTM): {ebit_margin*100:.2f}%")
    print(f"  Tax rate (LTM):    {tax_rate*100:.2f}%")
    print(f"  Sales/Capital:     {sales_to_capital:.2f}")

    # Year 1 projection
    result = project_year(
        year=1,
        prev_revenues=prev_revenues,
        revenue_growth=growth,
        ebit_margin=ebit_margin,
        tax_rate=tax_rate,
        sales_to_capital=sales_to_capital,
    )

    # Expected (Heineken JSON)
    expected = case['expected_yearly_projection'][0]  # Year 1

    print(f"\n[YEAR 1 RESULT]")
    print(f"  {'Field':<20} {'Computed':>15} {'Expected':>15} {'Diff':>12}")
    print(f"  {'-'*65}")

    fields_to_check = [
        ('revenues', 'revenues', 1),
        ('ebit', 'ebit', 1),
        ('ebit_after_tax', 'ebit_after_tax', 1),
        ('reinvestment', 'reinvestment', 1),
        ('fcff', 'fcff', 1),
    ]

    all_pass = True
    for field, exp_key, decimals in fields_to_check:
        computed = getattr(result, field)
        expected_val = expected[exp_key]
        diff = computed - expected_val
        diff_pct = (diff / expected_val * 100) if expected_val != 0 else 0

        # Tolerance: ±1% (Damodaran rounding zaten 2 ondalık)
        passed = abs(diff_pct) < 1.0
        status = "✓" if passed else "✗"
        if not passed:
            all_pass = False

        print(f"  {field:<20} {computed:>15,.0f} {expected_val:>15,.0f} {diff_pct:>+10.2f}% {status}")

    print()

    # NOT: EBIT margin Year 1 = 14.38% beklendiği halde biz LTM 14.86% kullandık.
    # Damodaran taper yapıyor: LTM 14.86% → Year 10 14.00% linear
    # İlk testte LTM kullandık, hata bekliyoruz.
    print("\n[NOT] Bu test EBIT margin için LTM (14.86%) kullandı.")
    print("      Damodaran Year 1'de 14.38% kullanıyor (taper başlıyor).")
    print("      Margin taper logic Adım 2'de eklenecek.")
    print()

    if all_pass:
        print("✓ TÜM ALANLAR PASS")
    else:
        print("✗ Sapmalar var — beklenen (margin taper henüz yok)")

    # ========================================================================
    # BONUS: linear_taper() helper testi
    # ========================================================================
    print("\n" + "="*70)
    print("LINEAR TAPER HELPER TEST")
    print("="*70)

    # Tax rate Year 6 = 28.76% (Damodaran taper)
    test_cases = [
        # (start, end, current, start_y, end_y, expected, name)
        (0.2970, 0.2500, 5, 5, 10, 0.2970, "Year 5 (start)"),
        (0.2970, 0.2500, 6, 5, 10, 0.2876, "Year 6 (Damodaran)"),
        (0.2970, 0.2500, 7, 5, 10, 0.2782, "Year 7"),
        (0.2970, 0.2500, 8, 5, 10, 0.2688, "Year 8"),
        (0.2970, 0.2500, 9, 5, 10, 0.2594, "Year 9"),
        (0.2970, 0.2500, 10, 5, 10, 0.2500, "Year 10 (end)"),
    ]

    print(f"\n  {'Test':<25} {'Computed':>10} {'Expected':>10} {'Diff':>10}")
    print(f"  {'-'*60}")

    for start, end, curr, sy, ey, expected, name in test_cases:
        result = linear_taper(start, end, curr, sy, ey)
        diff = result - expected
        passed = abs(diff) < 0.0001
        status = "✓" if passed else "✗"
        print(f"  {name:<25} {result:>10.4f} {expected:>10.4f} {diff:>+10.4f} {status}")

    print()


if __name__ == "__main__":
    main()
