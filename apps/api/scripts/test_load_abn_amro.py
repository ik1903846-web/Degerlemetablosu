#!/usr/bin/env python
"""ABN Amro validation case JSON sanity check."""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CASE_PATH = Path(__file__).parent.parent / "validation_cases" / "abn_amro_ddm.json"

def main():
    print(f"[LOAD] {CASE_PATH}")

    with open(CASE_PATH, 'r', encoding='utf-8') as f:
        case = json.load(f)

    print(f"\n[CASE] {case['case_id']}")
    print(f"[NAME] {case['case_name']}")
    print(f"[MODEL] {case['model']}")
    print(f"[SOURCE] {case['source']}")

    print(f"\n[EXPECTED]")
    print(f"  Value per share: €{case['expected']['value_per_share']}")
    print(f"  Tolerance: ±{case['expected']['tolerance_pct']*100:.0f}%")
    print(f"  Terminal value (PDF): €{case['expected']['terminal_value_eur']}")

    print(f"\n[STARTING METRICS]")
    sm = case['starting_metrics']
    print(f"  EPS: €{sm['eps_eur']}")
    print(f"  DPS: €{sm['dps_eur']}")
    print(f"  Payout: {sm['payout_ratio']*100:.1f}%")
    print(f"  ROE: {sm['roe']*100:.2f}%")
    print(f"  Growth: {sm['expected_growth_rate']*100:.2f}%")
    print(f"  Beta: {sm['beta']}")

    print(f"\n[HIGH GROWTH PHASE]")
    hg = case['high_growth_phase']
    print(f"  Duration: {hg['duration_years']} yıl")
    print(f"  Growth: {hg['growth_rate']*100:.2f}%")
    print(f"  Cost of Equity: {hg['cost_of_equity']*100:.2f}%")
    print(f"  DPS projection:")
    for proj in hg['expected_dps_projection']:
        print(f"    Year {proj['year']}: €{proj['dps_eur']}")

    print(f"\n[STABLE GROWTH PHASE]")
    sg = case['stable_growth_phase']
    print(f"  Growth: {sg['growth_rate']*100:.2f}%")
    print(f"  ROE: {sg['roe']*100:.2f}%")
    print(f"  Payout: {sg['payout_ratio']*100:.2f}%")
    print(f"  Cost of Equity: {sg['cost_of_equity']*100:.2f}%")
    print(f"  Year 6 EPS: €{sg['year_6_eps_eur']}")

    print(f"\n[COMMON]")
    ci = case['common_inputs']
    print(f"  Rf: {ci['risk_free_rate']*100:.2f}%")
    print(f"  ERP: {ci['equity_risk_premium']*100:.2f}%")

    print(f"\n[SPEC NOTE]")
    print(f"  {case['spec_note']}")

    print(f"\n✓ JSON başarıyla yüklendi")


if __name__ == "__main__":
    main()
