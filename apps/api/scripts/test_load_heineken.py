#!/usr/bin/env python
"""Heineken validation case JSON sanity check."""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CASE_PATH = Path(__file__).parent.parent / "validation_cases" / "heineken_2019.json"


def main():
    print(f"[LOAD] {CASE_PATH}")

    with open(CASE_PATH, 'r', encoding='utf-8') as f:
        case = json.load(f)

    print(f"\n[CASE] {case['case_id']}")
    print(f"[NAME] {case['case_name']}")
    print(f"[MODEL] {case['model']}")
    print(f"[SNAPSHOT] {case['snapshot_date']}")
    print(f"[CURRENCY] {case['currency']}")

    print("\n[EXPECTED]")
    for k, v in case['expected'].items():
        print(f"  {k}: {v}")

    print("\n[MARKET]")
    print(f"  Share price: €{case['market']['share_price']}")
    print(f"  Shares: {case['market']['shares_outstanding_millions']}M")

    print("\n[OPERATING]")
    op = case['operating']
    print(f"  Revenue (LTM): €{op['revenues_ltm_millions']:,}M")
    print(f"  Op Margin (LTM): {op['operating_margin_ltm']*100:.2f}%")
    print(f"  Tax Rate (LTM): {op['effective_tax_rate_ltm']*100:.2f}%")

    print("\n[COST OF CAPITAL]")
    coc = case['cost_of_capital']
    print(f"  Cost of Equity: {coc['cost_of_equity']*100:.2f}%")
    print(f"  WACC: {coc['wacc']*100:.2f}%")

    print("\n[STABLE PHASE]")
    sp = case['stable_phase']
    print(f"  Growth: {sp['growth']*100:.2f}%")
    print(f"  Cost of Capital: {sp['cost_of_capital']*100:.2f}%")
    print(f"  Terminal Value: €{sp['terminal_value_millions']:,}M")

    print("\n[YEARLY PROJECTION]")
    print(f"  Toplam {len(case['expected_yearly_projection'])} yıl")

    print("\n[VALIDATION]")
    print(f"  Hedef value/share: €{case['expected']['value_per_share']}")
    print(f"  Tolerance: ±{case['expected']['tolerance_pct']*100:.0f}%")

    lower = case['expected']['value_per_share'] * (1 - case['expected']['tolerance_pct'])
    upper = case['expected']['value_per_share'] * (1 + case['expected']['tolerance_pct'])
    print(f"  Pass range: €{lower:.2f} - €{upper:.2f}")

    print("\n✓ JSON validation case başarıyla yüklendi")


if __name__ == "__main__":
    main()
