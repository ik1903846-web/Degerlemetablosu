#!/usr/bin/env python
"""ABN Amro DDM — €30.87/share replicate."""
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.banking_ddm import dcf_ddm, project_dps_high_growth


def main():
    case_path = Path(__file__).parent.parent / "validation_cases" / "abn_amro_ddm.json"
    with open(case_path, 'r', encoding='utf-8') as f:
        case = json.load(f)

    print("="*80)
    print("ABN AMRO 2008 — DDM VALIDATION (€30.87 hedef)")
    print("="*80)

    sm = case['starting_metrics']
    hg = case['high_growth_phase']
    sg = case['stable_growth_phase']
    expected = case['expected']

    # ========================================================================
    # TEST 1: DPS High Growth Projection (5 yıl)
    # ========================================================================
    print("\n[TEST 1] High Growth DPS Projection (Year 1-5)")
    print("-"*80)

    projections = project_dps_high_growth(
        starting_eps=sm['eps_eur'],
        growth_rate=hg['growth_rate'],
        payout_ratio=hg['payout_ratio'],
        duration_years=hg['duration_years'],
    )

    print(f"  Year | EPS    | DPS (computed) | DPS (Damodaran) | Diff")
    print(f"  -----|--------|----------------|-----------------|---------")

    expected_dps = hg['expected_dps_projection']
    all_pass = True

    for i, proj in enumerate(projections):
        exp_dps = expected_dps[i]['dps_eur']
        diff = proj.dps - exp_dps
        passed = abs(diff) < 0.05  # ±5 cent tolerance
        status = "✓" if passed else "✗"
        if not passed:
            all_pass = False

        print(f"  {proj.year:>4} | {proj.eps:>6.4f} | {proj.dps:>14.4f} | {exp_dps:>15.4f} | {diff:>+8.4f} {status}")

    print(f"\n  {'5/5 PASS' if all_pass else 'FAIL'}")

    # ========================================================================
    # TEST 2: Full DDM Valuation
    # ========================================================================
    print("\n[TEST 2] Full DDM Valuation (€30.87 hedef)")
    print("-"*80)

    result = dcf_ddm(
        starting_eps=sm['eps_eur'],
        high_growth_rate=hg['growth_rate'],
        high_growth_payout=hg['payout_ratio'],
        high_growth_coe=hg['cost_of_equity'],
        high_growth_duration=hg['duration_years'],
        stable_growth=sg['growth_rate'],
        stable_payout=sg['payout_ratio'],
        stable_coe=sg['cost_of_equity'],
    )

    print(f"\n  Inputs:")
    print(f"    EPS_0:                 €{sm['eps_eur']}")
    print(f"    High growth rate:      {hg['growth_rate']*100:.2f}%")
    print(f"    High growth payout:    {hg['payout_ratio']*100:.2f}%")
    print(f"    High growth CoE:       {hg['cost_of_equity']*100:.2f}%")
    print(f"    Duration:              {hg['duration_years']} yıl")
    print(f"    Stable growth:         {sg['growth_rate']*100:.2f}%")
    print(f"    Stable payout:         {sg['payout_ratio']*100:.2f}%")
    print(f"    Stable CoE:            {sg['cost_of_equity']*100:.2f}%")

    print(f"\n  Computed Breakdown:")
    print(f"    EPS_terminal (Year 6):    €{result.eps_terminal:.4f}")
    print(f"    Damodaran PDF Year 6 EPS: €{sg['year_6_eps_eur']}")

    print(f"\n    Terminal Value:           €{result.terminal_value:.4f}")
    print(f"    Damodaran PDF TV:         €{expected['terminal_value_eur']}")

    tv_diff_pct = (result.terminal_value - expected['terminal_value_eur']) / expected['terminal_value_eur'] * 100
    print(f"    TV diff:                  {tv_diff_pct:+.2f}%")

    print(f"\n    PV(High Growth DPS):      €{result.pv_high_growth_dps:.4f}")
    print(f"    PV(Terminal Value):       €{result.pv_terminal_value:.4f}")

    print(f"\n[VALUE PER SHARE — FINAL]")
    print(f"  Computed:    €{result.value_per_share:.2f}")
    print(f"  Expected:    €{expected['value_per_share']:.2f}")

    diff_pct = (result.value_per_share - expected['value_per_share']) / expected['value_per_share'] * 100
    print(f"  Diff:         {diff_pct:+.2f}%")

    tolerance = expected['tolerance_pct']
    lower = expected['value_per_share'] * (1 - tolerance)
    upper = expected['value_per_share'] * (1 + tolerance)
    print(f"  Pass range:  €{lower:.2f} - €{upper:.2f}")

    if lower <= result.value_per_share <= upper:
        print(f"\n  ✓✓✓ ABN AMRO DDM VALIDATION PASS ★★★")
        print(f"  Banking DDM motoru Damodaran ground truth ile uyumlu!")
    else:
        print(f"\n  ✗ FAIL — {abs(diff_pct):.2f}% sapma")
        print(f"  Olası bug noktaları:")
        print(f"    - Terminal value formula (eps_terminal hesabı)")
        print(f"    - Stable payout (1 - g/ROE) doğru mu")
        print(f"    - PV discount factor")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
