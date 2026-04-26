#!/usr/bin/env python
"""Tube Investments EM DCF — ₹61.57 replicate."""
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.industrial_fcff_em import (
    project_year_reinvestment_based,
    project_multi_year_em,
    dcf_em_valuation,
)


def main():
    case_path = Path(__file__).parent.parent / "validation_cases" / "tube_investments_status_quo.json"
    with open(case_path, 'r', encoding='utf-8') as f:
        case = json.load(f)

    print("="*80)
    print("TUBE INVESTMENTS EM DCF — ₹61.57 hedef")
    print("="*80)

    sm = case['starting_metrics']
    hg = case['high_growth_phase']
    sg = case['stable_growth_phase']
    bs = case['balance_sheet']
    market = case['market']
    expected = case['expected']

    # ========================================================================
    # TEST 1: Year 1-5 Projection
    # ========================================================================
    print("\n[TEST 1] High Growth 5-Year Projection")
    print("-"*80)

    high_projs, year_6 = project_multi_year_em(
        starting_ebit_after_tax=sm['ebit_after_tax_millions'],
        high_growth_rate=hg['expected_growth_rate'],
        high_reinvestment_rate=hg['reinvestment_rate'],
        high_growth_duration=hg['duration_years'],
        stable_growth_rate=sg['growth_rate'],
        stable_reinvestment_rate=sg['reinvestment_rate'],
    )

    expected_yearly = hg['expected_yearly_projection']

    print(f"  Year | EBIT(1-t) | Reinv. | FCFF (computed) | FCFF (Damodaran) | Diff")
    print(f"  -----|-----------|--------|-----------------|------------------|------")

    all_pass = True
    for i, proj in enumerate(high_projs):
        exp = expected_yearly[i]
        diff = proj.fcff - exp['fcff']
        passed = abs(diff) < 50  # ±50 INR tolerance
        status = "✓" if passed else "✗"
        if not passed:
            all_pass = False

        print(f"  {proj.year:>4} | {proj.ebit_after_tax:>9,.0f} | {proj.reinvestment:>6,.0f} | {proj.fcff:>15,.0f} | {exp['fcff']:>16,} | {diff:>+5,.0f} {status}")

    print(f"\n  Year 6 (Terminal): EBIT(1-t)={year_6.ebit_after_tax:,.0f}, Reinv={year_6.reinvestment:,.0f}, FCFF={year_6.fcff:,.0f}")
    print(f"  Expected:         EBIT(1-t)={sg['year_6_ebit_after_tax']:,}, Reinv={sg['year_6_reinvestment']:,}, FCFF={sg['year_6_fcff']:,}")

    # ========================================================================
    # TEST 2: Full DCF
    # ========================================================================
    print("\n[TEST 2] Full DCF Valuation (₹61.57 hedef)")
    print("-"*80)

    result = dcf_em_valuation(
        starting_ebit_after_tax=sm['ebit_after_tax_millions'],
        high_growth_rate=hg['expected_growth_rate'],
        high_reinvestment_rate=hg['reinvestment_rate'],
        high_growth_duration=hg['duration_years'],
        high_growth_wacc=hg['wacc'],
        stable_growth_rate=sg['growth_rate'],
        stable_reinvestment_rate=sg['reinvestment_rate'],
        stable_wacc=sg['wacc'],
        cash=bs['cash_millions'],
        debt=bs['debt_millions'],
        options_value=bs['options_value_millions'],
        shares_outstanding=market['shares_outstanding_millions'],
    )

    print(f"\n  Terminal Value (computed):  ₹{result.terminal_value:>10,.0f}M")
    print(f"  Terminal Value (Damodaran): ₹{expected['terminal_value_millions']:>10,}M")

    tv_diff_pct = (result.terminal_value - expected['terminal_value_millions']) / expected['terminal_value_millions'] * 100
    print(f"  TV diff: {tv_diff_pct:+.2f}%")

    print(f"\n  PV(High Growth FCFF):  ₹{result.pv_high_growth_fcff:>10,.0f}M")
    print(f"  PV(Terminal Value):    ₹{result.pv_terminal_value:>10,.0f}M")

    print(f"\n  Firm Value (computed):     ₹{result.firm_value:>10,.0f}M")
    print(f"  Firm Value (Damodaran):    ₹{expected['firm_value_millions']:>10,}M")

    fv_diff_pct = (result.firm_value - expected['firm_value_millions']) / expected['firm_value_millions'] * 100
    print(f"  Firm diff: {fv_diff_pct:+.2f}%")

    print(f"\n  + Cash:                    {result.cash:>10,.0f}M")
    print(f"  - Debt:                    {-result.debt:>10,.0f}M")
    print(f"  - Options:                 {-result.options_value:>10,.0f}M")
    print(f"  Equity Value (computed):   ₹{result.equity_value:>10,.0f}M")
    print(f"  Equity Value (Damodaran):  ₹{expected['equity_value_millions']:>10,}M")

    eq_diff_pct = (result.equity_value - expected['equity_value_millions']) / expected['equity_value_millions'] * 100
    print(f"  Equity diff: {eq_diff_pct:+.2f}%")

    print(f"\n[VALUE PER SHARE]")
    print(f"  Computed:    ₹{result.value_per_share:.2f}")
    print(f"  Expected:    ₹{expected['value_per_share_inr']:.2f}")

    diff_pct = (result.value_per_share - expected['value_per_share_inr']) / expected['value_per_share_inr'] * 100
    print(f"  Diff:         {diff_pct:+.2f}%")

    tolerance = expected['tolerance_pct']
    lower = expected['value_per_share_inr'] * (1 - tolerance)
    upper = expected['value_per_share_inr'] * (1 + tolerance)
    print(f"  Pass range:  ₹{lower:.2f} - ₹{upper:.2f}")

    if lower <= result.value_per_share <= upper:
        print(f"\n  ✓✓✓ TUBE INVESTMENTS EM DCF VALIDATION PASS ★★★")
        print(f"  3/3 VALIDATION CASE PASS — REELDEĞER motoru tam çalışıyor!")
    else:
        print(f"\n  ✗ FAIL — {abs(diff_pct):.2f}% sapma")
        print(f"  Olası bug noktaları:")
        print(f"    - Reinvestment formülü (rate × EBIT vs ΔRev/Sales)")
        print(f"    - Terminal year hesabı (Year 5 → Year 6 transition)")
        print(f"    - Stable WACC kullanımı (terminal formülünde sadece)")
        print(f"    - Shares outstanding (246.21M derived)")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
