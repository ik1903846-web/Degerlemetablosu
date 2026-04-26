#!/usr/bin/env python
"""Amazon 2000 validation case JSON sanity check."""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CASE_PATH = Path(__file__).parent.parent / "validation_cases" / "amazon_2000.json"

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
    print(f"  Value/share: ${exp['value_per_share_usd']}")
    print(f"  Tolerance: ±{exp['tolerance_pct']*100:.0f}%")

    pass_low = exp['value_per_share_usd'] * (1 - exp['tolerance_pct'])
    pass_high = exp['value_per_share_usd'] * (1 + exp['tolerance_pct'])
    print(f"  Pass range: ${pass_low:.2f} - ${pass_high:.2f}")

    print(f"\n[STARTING METRICS]")
    sm = case['starting_metrics']
    print(f"  Current revenues:   ${sm['current_revenues_millions']:,}M")
    print(f"  Current op margin:  {sm['current_op_margin']*100:.2f}%  (NEGATIVE)")
    print(f"  Current EBIT:       ${sm['current_ebit_millions']:,}M")
    print(f"  NOL:                ${sm['nol_starting_millions']:,}M")
    print(f"  Sales/Capital:      {sm['sales_turnover_ratio']}")

    print(f"\n[5 SIMULTANEOUS TAPERS]")
    print(f"  Year 1-5: Margin -36.71% → 10% (linear)")
    print(f"  Year 6-10: Growth 42% → 6%, Tax 0% → 35%, Beta 1.60 → 1.00, Debt 1.2% → 15%")
    print(f"  WACC: 12.84% → 9.61% (Year 1 → Year 10)")

    print(f"\n[YEARLY PROJECTION (Damodaran ground truth)]")
    print(f"  Year | Revenue   | EBIT    | EBIT(1-t) | Reinv.   | FCFF")
    print(f"  -----|-----------|---------|-----------|----------|--------")
    for proj in case['yearly_projection_expected']:
        print(f"  {proj['year']:>4} | ${proj['revenues']:>7,} | ${proj['ebit']:>5,} | ${proj['ebit_after_tax']:>7,} | ${proj['reinvestment']:>6,} | ${proj['fcff']:>6,}")

    print(f"\n[TERMINAL VALUE]")
    tv = case['terminal_year']
    print(f"  Term FCFF: ${tv['fcff']:,}M")
    print(f"  TV = {tv['fcff']} / ({tv['wacc']*100:.2f}% - {tv['growth']*100:.0f}%) = ${exp['terminal_value_millions']:,}M")

    print(f"\n[EQUITY BRIDGE]")
    bs = case['balance_sheet']
    print(f"  Operating Assets:    ${exp['operating_assets_millions']:>8,}M")
    print(f"  + Cash:              ${bs['cash_millions']:>8,}M")
    print(f"  = Firm Value:        ${exp['firm_value_millions']:>8,}M")
    print(f"  - Debt:              ${bs['debt_millions']:>8,}M")
    print(f"  = Equity (pre-opt):  ${exp['equity_value_pre_options_millions']:>8,}M")
    print(f"  - Equity Options:    ${bs['equity_options_millions']:>8,}M")
    print(f"  = Equity (final):    ${exp['equity_value_pre_options_millions'] - bs['equity_options_millions']:>8,}M")

    print(f"\n[SHARES]")
    print(f"  Outstanding: {case['market']['shares_outstanding_millions']}M")

    print(f"\n[VALUE/SHARE]")
    final_equity = exp['equity_value_pre_options_millions'] - bs['equity_options_millions']
    val_per_share = final_equity / case['market']['shares_outstanding_millions']
    print(f"  Computed (sanity): ${val_per_share:.2f}")
    print(f"  Damodaran:         ${exp['value_per_share_usd']}")

    print(f"\n[NOTE]")
    print(f"  {case['spec_note']}")

    print(f"\n✓ JSON başarıyla yüklendi")
    print(f"\n  YARIN: young_firm_dcf.py implement (en karmaşık model)")
    print(f"         5 simultaneous taper + NOL + options deduction")
    print(f"         Hedef: ${exp['value_per_share_usd']} ±5% PASS")


if __name__ == "__main__":
    main()
