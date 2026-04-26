#!/usr/bin/env python
"""Heineken 2019 — FULL DCF: €59.65/share replicate."""
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.industrial_fcff import (
    project_multi_year,
    ProjectionInputs,
    dcf_valuation,
)


def main():
    case_path = Path(__file__).parent.parent / "validation_cases" / "heineken_2019.json"
    with open(case_path, 'r', encoding='utf-8') as f:
        case = json.load(f)

    print("="*80)
    print("HEINEKEN 2019 — FULL DCF VALIDATION (€59.65 hedef)")
    print("="*80)

    # Inputs (Adım 2'yle aynı)
    inputs = ProjectionInputs(
        starting_revenues=case['operating']['revenues_ltm_millions'],
        sales_to_capital=case['operating']['sales_to_invested_capital_5y_avg'],
        starting_ebit_margin=case['expected_yearly_projection'][0]['ebit_margin'],
        terminal_ebit_margin=case['growth']['year_10_operating_margin'],
        margin_taper_start_year=1,
        margin_taper_end_year=10,
        starting_tax_rate=case['operating']['effective_tax_rate_ltm'],
        terminal_tax_rate=case['growth']['marginal_tax_rate'],
        tax_taper_start_year=5,
        tax_taper_end_year=10,
        explicit_growth_rate=case['growth']['year_1_5_revenue_growth'],
        terminal_growth_rate=case['growth']['year_10_revenue_growth'],
        explicit_period_years=case['growth']['explicit_period_years'],
        transition_period_years=case['growth']['transition_period_years'],
    )

    # 10-year projection
    projections = project_multi_year(inputs, total_years=10)

    # DCF valuation
    coc = case['cost_of_capital']
    sp = case['stable_phase']
    bs = case['balance_sheet']
    market = case['market']

    result = dcf_valuation(
        projections=projections,
        wacc=coc['wacc'],
        stable_cost_of_capital=sp['cost_of_capital'],
        stable_growth=sp['growth'],
        stable_reinvestment_rate=sp['reinvestment_rate'],
        debt=bs['debt_millions'],
        minority_interests=bs['minority_interests_millions'],
        cash=bs['cash_millions'],
        non_operating_assets=bs['non_operating_assets_millions'],
        shares_outstanding=market['shares_outstanding_millions'],
    )

    # Compare with expected
    expected = case['expected']

    print(f"\n[TERMINAL VALUE]")
    print(f"  Year 11 FCFF (computed):     €{result.terminal_year_fcff:>10,.0f}M")
    print(f"  Stable growth:                {sp['growth']*100:>+6.2f}%")
    print(f"  Stable cost of capital:       {sp['cost_of_capital']*100:>6.2f}%")
    print(f"  Terminal Value (computed):   €{result.terminal_value:>10,.0f}M")
    print(f"  Terminal Value (Damodaran):  €{sp['terminal_value_millions']:>10,.0f}M")

    tv_diff_pct = (result.terminal_value - sp['terminal_value_millions']) / sp['terminal_value_millions'] * 100
    print(f"  Terminal Value diff:          {tv_diff_pct:>+6.2f}%")

    print(f"\n[PRESENT VALUES]")
    print(f"  PV explicit CFs (computed):  €{result.pv_explicit_cash_flows:>10,.0f}M")
    print(f"  PV explicit CFs (Damodaran): €{expected['pv_explicit_cf_millions']:>10,.0f}M")

    pv_explicit_diff = (result.pv_explicit_cash_flows - expected['pv_explicit_cf_millions']) / expected['pv_explicit_cf_millions'] * 100
    print(f"  PV explicit diff:             {pv_explicit_diff:>+6.2f}%")

    print(f"\n  PV terminal (computed):      €{result.pv_terminal_value:>10,.0f}M")
    print(f"  PV terminal (Damodaran):     €{expected['pv_terminal_value_millions']:>10,.0f}M")

    pv_terminal_diff = (result.pv_terminal_value - expected['pv_terminal_value_millions']) / expected['pv_terminal_value_millions'] * 100
    print(f"  PV terminal diff:             {pv_terminal_diff:>+6.2f}%")

    print(f"\n[OPERATING ASSETS]")
    print(f"  Computed:                    €{result.operating_assets_value:>10,.0f}M")
    print(f"  Damodaran:                   €{expected['operating_assets_millions']:>10,.0f}M")

    print(f"\n[EQUITY BRIDGE]")
    print(f"  Operating Value:             €{result.operating_assets_value:>10,.0f}M")
    print(f"  - Debt:                       {-result.debt:>10,.0f}M")
    print(f"  - Minority Interests:         {-result.minority_interests:>10,.0f}M")
    print(f"  + Cash:                       {result.cash:>10,.0f}M")
    print(f"  + Non-op Assets:              {result.non_operating_assets:>10,.0f}M")
    print(f"  Equity Value (computed):     €{result.equity_value:>10,.0f}M")
    print(f"  Equity Value (Damodaran):    €{expected['value_of_equity_millions']:>10,.0f}M")

    equity_diff_pct = (result.equity_value - expected['value_of_equity_millions']) / expected['value_of_equity_millions'] * 100
    print(f"  Equity diff:                  {equity_diff_pct:>+6.2f}%")

    print(f"\n[VALUE PER SHARE — FİNAL TEST]")
    print(f"  Computed:                    €{result.value_per_share:>10.2f}")
    print(f"  Damodaran (Expected):        €{expected['value_per_share']:>10.2f}")

    diff_pct = (result.value_per_share - expected['value_per_share']) / expected['value_per_share'] * 100
    print(f"  Diff:                         {diff_pct:>+6.2f}%")

    tolerance = expected['tolerance_pct']
    lower = expected['value_per_share'] * (1 - tolerance)
    upper = expected['value_per_share'] * (1 + tolerance)

    print(f"  Pass range (±{tolerance*100:.0f}%):     €{lower:.2f} - €{upper:.2f}")

    if lower <= result.value_per_share <= upper:
        print(f"\n  ✓✓✓ HEINEKEN 2019 VALIDATION PASS ★★★")
        print(f"  REELDEĞER motoru Damodaran ground truth ile uyumlu!")
    else:
        print(f"\n  ✗ FAIL — {abs(diff_pct):.2f}% sapma var")
        print(f"  Bug fix gerekecek. Detaylı analiz:")
        print(f"    - PV explicit diff: {pv_explicit_diff:+.2f}%")
        print(f"    - PV terminal diff: {pv_terminal_diff:+.2f}%")
        print(f"    - Equity diff: {equity_diff_pct:+.2f}%")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
