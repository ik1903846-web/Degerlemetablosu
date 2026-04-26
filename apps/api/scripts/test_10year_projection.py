#!/usr/bin/env python
"""Heineken 2019 — 10-yıl projection birebir replicate."""
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.industrial_fcff import project_multi_year, ProjectionInputs


def main():
    case_path = Path(__file__).parent.parent / "validation_cases" / "heineken_2019.json"
    with open(case_path, 'r', encoding='utf-8') as f:
        case = json.load(f)

    print("="*80)
    print("HEINEKEN 2019 — 10-YEAR PROJECTION TEST")
    print("="*80)

    # Heineken Year 1 ebit_margin = 14.38% (Damodaran taper start)
    # JSON'dan al (expected_yearly_projection[0]['ebit_margin'])
    starting_ebit_margin = case['expected_yearly_projection'][0]['ebit_margin']  # 0.1438
    terminal_ebit_margin = case['growth']['year_10_operating_margin']  # 0.1400

    inputs = ProjectionInputs(
        starting_revenues=case['operating']['revenues_ltm_millions'],
        sales_to_capital=case['operating']['sales_to_invested_capital_5y_avg'],

        starting_ebit_margin=starting_ebit_margin,  # 0.1438
        terminal_ebit_margin=terminal_ebit_margin,   # 0.1400
        margin_taper_start_year=1,
        margin_taper_end_year=10,

        starting_tax_rate=case['operating']['effective_tax_rate_ltm'],  # 0.2970
        terminal_tax_rate=case['growth']['marginal_tax_rate'],  # 0.2500
        tax_taper_start_year=5,  # Damodaran Heineken Year 5 tax taper başlangıcı
        tax_taper_end_year=10,

        explicit_growth_rate=case['growth']['year_1_5_revenue_growth'],  # 0.0322
        terminal_growth_rate=case['growth']['year_10_revenue_growth'],   # -0.005
        explicit_period_years=case['growth']['explicit_period_years'],   # 5
        transition_period_years=case['growth']['transition_period_years'], # 5
    )

    print(f"\n[INPUTS]")
    print(f"  Starting revenues:       €{inputs.starting_revenues:,}M")
    print(f"  Sales/Capital:           {inputs.sales_to_capital}")
    print(f"  EBIT margin Y1 → Y10:    {inputs.starting_ebit_margin*100:.2f}% → {inputs.terminal_ebit_margin*100:.2f}%")
    print(f"  Tax rate Y1 → Y10:       {inputs.starting_tax_rate*100:.2f}% → {inputs.terminal_tax_rate*100:.2f}%")
    print(f"  Growth Y1-5 / Y10:       {inputs.explicit_growth_rate*100:.2f}% / {inputs.terminal_growth_rate*100:+.2f}%")

    # Project
    projections = project_multi_year(inputs, total_years=10)

    # Compare with expected
    expected_yearly = case['expected_yearly_projection']

    print(f"\n[10-YEAR PROJECTION]")
    print(f"  Year | Growth | Revenue   | EBIT mrg | EBIT  | Tax%  | EBITAT | Reinv | FCFF")
    print(f"  -----|--------|-----------|----------|-------|-------|--------|-------|------")

    all_pass = True
    failed_fields = []

    for i, proj in enumerate(projections):
        exp = expected_yearly[i]

        # Format: Year | Growth | Revenue | EBIT mrg | EBIT | Tax% | EBITAT | Reinv | FCFF
        print(f"  {proj.year:>4} | {proj.revenue_growth*100:>+5.2f}% | {proj.revenues:>9,.0f} | {proj.ebit_margin*100:>7.2f}% | {proj.ebit:>5,.0f} | {proj.tax_rate*100:>4.1f}% | {proj.ebit_after_tax:>6,.0f} | {proj.reinvestment:>5,.0f} | {proj.fcff:>5,.0f}")

        # Check each field
        checks = [
            ('revenue_growth', proj.revenue_growth, exp['revenue_growth'], 0.0001),
            ('revenues', proj.revenues, exp['revenues'], 50),  # ±€50M
            ('ebit_margin', proj.ebit_margin, exp['ebit_margin'], 0.0005),
            ('ebit', proj.ebit, exp['ebit'], 30),  # ±€30M
            ('tax_rate', proj.tax_rate, exp['tax_rate'], 0.0005),
            ('ebit_after_tax', proj.ebit_after_tax, exp['ebit_after_tax'], 30),
            ('reinvestment', proj.reinvestment, exp['reinvestment'], 30),
            ('fcff', proj.fcff, exp['fcff'], 30),
        ]

        for field, computed, expected, tol in checks:
            diff = abs(computed - expected)
            if diff > tol:
                all_pass = False
                failed_fields.append((proj.year, field, computed, expected, diff))

    print()

    # Expected (Damodaran)
    print(f"[EXPECTED — Damodaran Ground Truth]")
    print(f"  Year | Growth | Revenue   | EBIT mrg | EBIT  | Tax%  | EBITAT | Reinv | FCFF")
    print(f"  -----|--------|-----------|----------|-------|-------|--------|-------|------")
    for exp in expected_yearly:
        print(f"  {exp['year']:>4} | {exp['revenue_growth']*100:>+5.2f}% | {exp['revenues']:>9,.0f} | {exp['ebit_margin']*100:>7.2f}% | {exp['ebit']:>5,.0f} | {exp['tax_rate']*100:>4.1f}% | {exp['ebit_after_tax']:>6,.0f} | {exp['reinvestment']:>5,.0f} | {exp['fcff']:>5,.0f}")

    print()
    print("="*80)

    if all_pass:
        print("✓ TÜM 10 YIL × 8 ALAN PASS")
    else:
        print(f"✗ {len(failed_fields)} sapma var:")
        for year, field, computed, expected, diff in failed_fields[:10]:
            print(f"    Year {year} {field}: computed={computed:.4f}, expected={expected:.4f}, diff={diff:.4f}")

    print("="*80)


if __name__ == "__main__":
    main()
