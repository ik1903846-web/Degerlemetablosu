#!/usr/bin/env python
"""Tube Investments validation case JSON sanity check."""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CASE_PATH = Path(__file__).parent.parent / "validation_cases" / "tube_investments_status_quo.json"

def main():
    print(f"[LOAD] {CASE_PATH}")

    with open(CASE_PATH, 'r', encoding='utf-8') as f:
        case = json.load(f)

    print(f"\n[CASE] {case['case_id']}")
    print(f"[MODEL] {case['model']}")
    print(f"[CURRENCY] {case['currency']}")
    print(f"[SNAPSHOT] {case['snapshot_date']}")

    print(f"\n[EXPECTED]")
    exp = case['expected']
    print(f"  Value/share: ₹{exp['value_per_share_inr']}")
    print(f"  Tolerance: ±{exp['tolerance_pct']*100:.0f}%")

    pass_low = exp['value_per_share_inr'] * (1 - exp['tolerance_pct'])
    pass_high = exp['value_per_share_inr'] * (1 + exp['tolerance_pct'])
    print(f"  Pass range: ₹{pass_low:.2f} - ₹{pass_high:.2f}")

    print(f"\n[HIGH GROWTH PHASE]")
    hg = case['high_growth_phase']
    print(f"  Duration: {hg['duration_years']} yıl")
    print(f"  Growth: {hg['expected_growth_rate']*100:.2f}%")
    print(f"  WACC: {hg['wacc']*100:.2f}%")
    print(f"  Reinv. rate: {hg['reinvestment_rate']*100:.0f}%")

    print(f"\n[STABLE PHASE]")
    sg = case['stable_growth_phase']
    print(f"  Growth: {sg['growth_rate']*100:.0f}%")
    print(f"  WACC: {sg['wacc']*100:.2f}%")
    print(f"  Country Risk: {sg['country_risk_premium']*100:.0f}%")

    print(f"\n[COST OF EQUITY DECOMPOSITION]")
    coe = case['cost_of_equity_decomposition']
    print(f"  Real Rf: {coe['risk_free_rate_real']*100:.0f}%")
    print(f"  Beta: {coe['beta_levered']}")
    print(f"  Mature ERP: {coe['mature_erp']*100:.0f}%")
    print(f"  Country Risk: {coe['country_risk_premium']*100:.2f}%")
    print(f"  Total ERP: {coe['total_erp']*100:.2f}%")
    print(f"  → Cost of Equity: 0.12 + 1.17 × 0.0923 = {0.12 + 1.17 * 0.0923:.4f}")

    print(f"\n[YEARLY PROJECTION]")
    print(f"  Year | EBIT(1-t) | Reinv. | FCFF")
    print(f"  -----|-----------|--------|------")
    for proj in hg['expected_yearly_projection']:
        print(f"  {proj['year']:>4} | {proj['ebit_after_tax']:>9,} | {proj['reinvestment']:>6,} | {proj['fcff']:>5,}")

    print(f"\n[BALANCE SHEET]")
    bs = case['balance_sheet']
    print(f"  Cash: ₹{bs['cash_millions']:,}M")
    print(f"  Debt: ₹{bs['debt_millions']:,}M")

    print(f"\n[SPEC NOTE]")
    print(f"  {case['spec_note']}")

    print(f"\n✓ JSON başarıyla yüklendi")


if __name__ == "__main__":
    main()
