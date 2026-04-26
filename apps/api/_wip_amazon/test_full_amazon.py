#!/usr/bin/env python
"""Amazon 2000 Young Firm DCF — $34.32 replicate."""
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.young_firm_dcf import dcf_young_firm_valuation


def main():
    case_path = Path(__file__).parent.parent / "validation_cases" / "amazon_2000.json"
    with open(case_path, 'r', encoding='utf-8') as f:
        case = json.load(f)

    print("="*80)
    print("AMAZON 2000 — YOUNG FIRM DCF VALIDATION ($34.32 hedef)")
    print("="*80)

    sm = case['starting_metrics']
    hg = case['high_growth_phase_year_1_5']
    sg = case['stable_growth_phase']
    coc = case['cost_of_capital_inputs']
    bs = case['balance_sheet']
    market = case['market']
    expected = case['expected']

    # Full DCF
    result = dcf_young_firm_valuation(
        starting_revenue=sm['current_revenues_millions'],
        starting_op_margin=sm['current_op_margin'],
        starting_nol=sm['nol_starting_millions'],
        sales_to_capital_ratio=sm['sales_turnover_ratio'],
        statutory_tax_rate=sg['tax_rate'],
        risk_free_rate=coc['risk_free_rate'],
        mature_erp=coc['mature_erp'],
        # High growth (Year 1-5)
        high_growth_rate=hg['revenue_growth_rate'],
        high_growth_duration=5,
        high_growth_beta=coc['beta_starting'],
        high_growth_debt_ratio=0.012,  # Starting 1.2%
        high_growth_cost_of_debt_pretax=coc['cost_of_debt_pretax_starting'],
        # Stable (Year 11+)
        stable_op_margin=sg['operating_margin'],
        stable_growth_rate=sg['growth_rate'],
        stable_beta=coc['beta_stable'],
        stable_debt_ratio=0.15,
        stable_cost_of_debt_pretax=coc['cost_of_debt_pretax_stable'],
        # Balance sheet
        cash=bs['cash_millions'],
        debt=bs['debt_millions'],
        equity_options=bs['equity_options_millions'],
        shares_outstanding=market['shares_outstanding_millions'],
    )

    # ========================================================================
    # TEST 1: 10-yıl yearly projection
    # ========================================================================
    print("\n[TEST 1] 10-Yıl Yearly Projection (Damodaran ground truth)")
    print("-"*80)
    print(f"  Year | Revenue   | EBIT(1-t) | Reinv. | FCFF (comp) | FCFF (D)  | Diff")
    print(f"  -----|-----------|-----------|--------|-------------|-----------|------")

    expected_yearly = case['yearly_projection_expected']

    for i, proj in enumerate(result.yearly_projections):
        exp = expected_yearly[i]
        diff = proj.fcff - exp['fcff']
        passed = abs(diff) < 100  # ±100M tolerance
        status = "✓" if passed else "✗"

        print(f"  {proj.year:>4} | ${proj.revenue:>7,.0f} | ${proj.ebit_after_tax:>7,.0f} | ${proj.reinvestment:>6,.0f} | ${proj.fcff:>9,.0f} | ${exp['fcff']:>7,} | {diff:>+5,.0f} {status}")

    # ========================================================================
    # TEST 2: Final value
    # ========================================================================
    print(f"\n[TEST 2] Equity Bridge + Value/Share")
    print("-"*80)

    print(f"  Operating Assets:           ${result.operating_assets:>10,.0f}M")
    print(f"  Damodaran:                  ${expected['operating_assets_millions']:>10,}M")
    op_diff = (result.operating_assets - expected['operating_assets_millions']) / expected['operating_assets_millions'] * 100
    print(f"  Operating diff:              {op_diff:+.2f}%")

    print(f"\n  + Cash:                     ${result.cash:>10,.0f}M")
    print(f"  - Debt:                    -${result.debt:>10,.0f}M")
    print(f"  = Equity (pre-opt):         ${result.equity_value_pre_options:>10,.0f}M")
    print(f"  Damodaran:                  ${expected['equity_value_pre_options_millions']:>10,}M")

    print(f"\n  - Equity Options:          -${result.equity_options:>10,.0f}M")
    print(f"  = Equity (final):           ${result.equity_value_final:>10,.0f}M")

    print(f"\n  Shares:                      {result.shares_outstanding:>9,.1f}M")

    print(f"\n[VALUE PER SHARE — FINAL]")
    print(f"  Computed:    ${result.value_per_share:.2f}")
    print(f"  Expected:    ${expected['value_per_share_usd']:.2f}")

    diff_pct = (result.value_per_share - expected['value_per_share_usd']) / expected['value_per_share_usd'] * 100
    print(f"  Diff:         {diff_pct:+.2f}%")

    tolerance = expected['tolerance_pct']
    lower = expected['value_per_share_usd'] * (1 - tolerance)
    upper = expected['value_per_share_usd'] * (1 + tolerance)
    print(f"  Pass range:  ${lower:.2f} - ${upper:.2f}")

    if lower <= result.value_per_share <= upper:
        print(f"\n  ✓✓✓ AMAZON 2000 YOUNG FIRM DCF VALIDATION PASS ★★★")
        print(f"  5/5 VALIDATION CASE PASS — REELDEĞER motoru tam tamam!")
    else:
        print(f"\n  ✗ FAIL — {abs(diff_pct):.2f}% sapma")
        print(f"  Olası bug noktaları:")
        print(f"    - 5 simultaneous taper orchestration")
        print(f"    - NOL handling (year 4 transition)")
        print(f"    - Year-by-year cumulative WACC discount")
        print(f"    - Terminal year FCFF formula")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
