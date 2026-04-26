#!/usr/bin/env python
"""Toyota 2009 validation case JSON sanity check."""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CASE_PATH = Path(__file__).parent.parent / "validation_cases" / "toyota_2009.json"

def main():
    print(f"[LOAD] {CASE_PATH}")

    with open(CASE_PATH, 'r', encoding='utf-8') as f:
        case = json.load(f)

    print(f"\n[CASE] {case['case_id']}")
    print(f"[MODEL] {case['model']}")
    print(f"[CURRENCY] {case['currency']} ({case['currency_unit']})")
    print(f"[SNAPSHOT] {case['snapshot_date']}")

    print(f"\n[EXPECTED]")
    exp = case['expected']
    print(f"  Value/share: ¥{exp['value_per_share_jpy']:,}")
    print(f"  Tolerance: ±{exp['tolerance_pct']*100:.0f}%")

    pass_low = exp['value_per_share_jpy'] * (1 - exp['tolerance_pct'])
    pass_high = exp['value_per_share_jpy'] * (1 + exp['tolerance_pct'])
    print(f"  Pass range: ¥{pass_low:,.0f} - ¥{pass_high:,.0f}")

    print(f"\n[CYCLICAL NORMALIZATION]")
    cn = case['cyclical_normalization']
    print(f"  Revenues 2009: ¥{cn['revenues_2009_billions']:,}B")
    print(f"  Current margin (kriz): {cn['current_operating_margin_2009']*100:.2f}%")
    print(f"  Avg margin (98-09):    {cn['avg_operating_margin_98_09']*100:.2f}%")
    print(f"  Normalized OI: ¥{cn['revenues_2009_billions'] * cn['avg_operating_margin_98_09']:,.1f}B")

    print(f"\n[COST OF CAPITAL]")
    coc = case['cost_of_capital']
    print(f"  Cost of Equity: {coc['cost_of_equity']*100:.2f}%")
    print(f"  Cost of Debt (after-tax): {coc['cost_of_debt_after_tax']*100:.3f}%")
    print(f"  WACC: {coc['wacc']*100:.2f}%")

    print(f"\n[STABLE GROWTH]")
    sg = case['stable_growth']
    print(f"  Growth: {sg['growth_rate']*100:.1f}%")
    print(f"  ROC: {sg['roc']*100:.2f}%")
    print(f"  Reinvestment: {sg['reinvestment_rate']*100:.2f}%")

    print(f"\n[VALUATION FORMULA]")
    vf = case['valuation_formula']
    print(f"  {vf['name']}")
    print(f"  {vf['formula']}")
    print(f"  Result: ¥{vf['result_billions']:,}B")

    print(f"\n[BALANCE SHEET]")
    bs = case['balance_sheet']
    print(f"  + Cash:       ¥{bs['cash_billions']:,}B")
    print(f"  + Non-op:     ¥{bs['non_operating_assets_billions']:,}B")
    print(f"  - Debt:       ¥{bs['debt_billions']:,}B")
    print(f"  - Minority:   ¥{bs['minority_interests_billions']:,}B")

    print(f"\n[SHARES]")
    print(f"  Outstanding: {case['market']['shares_outstanding_millions']:,}M")

    print(f"\n[NOTE]")
    print(f"  {case['spec_note']}")

    print(f"\n✓ JSON başarıyla yüklendi")


if __name__ == "__main__":
    main()
