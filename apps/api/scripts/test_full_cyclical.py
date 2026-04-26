#!/usr/bin/env python
"""Toyota 2009 cyclical DCF — ¥4,735 replicate."""
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.cyclical_dcf import (
    normalize_operating_income,
    single_stage_stable_growth_value,
    equity_bridge_cyclical,
    cyclical_dcf_valuation,
)


def main():
    case_path = Path(__file__).parent.parent / "validation_cases" / "toyota_2009.json"
    with open(case_path, 'r', encoding='utf-8') as f:
        case = json.load(f)

    print("="*80)
    print("TOYOTA 2009 — CYCLICAL DCF VALIDATION (¥4,735 hedef)")
    print("="*80)

    cn = case['cyclical_normalization']
    coc = case['cost_of_capital']
    sg = case['stable_growth']
    bs = case['balance_sheet']
    market = case['market']
    expected = case['expected']

    # ========================================================================
    # TEST 1: Earnings Normalization
    # ========================================================================
    print("\n[TEST 1] Cyclical Earnings Normalization")
    print("-"*80)

    norm = normalize_operating_income(
        current_revenues=cn['revenues_2009_billions'],
        historical_avg_margin=cn['avg_operating_margin_98_09'],
        current_op_margin=cn['current_operating_margin_2009'],
    )

    print(f"  Current revenues:        ¥{norm.current_revenues:>10,.0f}B")
    print(f"  Current op margin:        {norm.current_op_margin*100:>10.2f}%")
    print(f"  Current op income:       ¥{norm.current_op_income:>10,.1f}B  (kriz)")
    print(f"  Historical avg margin:    {norm.historical_avg_margin*100:>10.2f}%")
    print(f"  Margin uplift:            {norm.margin_uplift*100:>10.2f}pp")
    print(f"  Normalized op income:    ¥{norm.normalized_op_income:>10,.1f}B")
    print(f"  Damodaran PDF:           ¥1,660.7B")

    norm_diff = abs(norm.normalized_op_income - 1660.7)
    if norm_diff < 1:
        print(f"  ✓ Normalization birebir (sapma {norm_diff:.2f}B)")
    else:
        print(f"  ✗ Normalization sapma {norm_diff:.2f}B")

    # ========================================================================
    # TEST 2: Single-Stage Stable Growth Value
    # ========================================================================
    print("\n[TEST 2] Single-Stage Stable Growth Value")
    print("-"*80)

    op_value = single_stage_stable_growth_value(
        normalized_op_income=norm.normalized_op_income,
        growth_rate=sg['growth_rate'],
        tax_rate=coc['tax_rate_japan_marginal'],
        reinvestment_rate=sg['reinvestment_rate'],
        wacc=coc['wacc'],
    )

    print(f"  Normalized OI:            ¥{op_value.normalized_op_income:>10,.1f}B")
    print(f"  Next year OI (×1.015):    ¥{op_value.next_year_oi:>10,.1f}B")
    print(f"  After-tax OI (×0.593):    ¥{op_value.next_year_oi_after_tax:>10,.1f}B")
    print(f"  Next year FCFF (×0.7054): ¥{op_value.next_year_fcff:>10,.1f}B")
    print(f"  WACC - g (5.09%-1.5%):    {op_value.discount_rate_minus_growth*100:>10.2f}%")
    print(f"  Operating Assets:         ¥{op_value.operating_assets_value:>10,.0f}B")
    print(f"  Damodaran PDF:           ¥{expected['operating_assets_billions']:>10,}B")

    op_diff_pct = (op_value.operating_assets_value - expected['operating_assets_billions']) / expected['operating_assets_billions'] * 100
    print(f"  Operating diff:           {op_diff_pct:+.2f}%")

    # ========================================================================
    # TEST 3: Extended Equity Bridge
    # ========================================================================
    print("\n[TEST 3] Extended Equity Bridge")
    print("-"*80)

    bridge = equity_bridge_cyclical(
        operating_assets=op_value.operating_assets_value,
        cash=bs['cash_billions'],
        non_operating_assets=bs['non_operating_assets_billions'],
        debt=bs['debt_billions'],
        minority_interests=bs['minority_interests_billions'],
    )

    print(f"    Operating Assets:        ¥{bridge.operating_assets:>10,.0f}B")
    print(f"  + Cash:                    ¥{bridge.cash:>10,.0f}B")
    print(f"  + Non-operating Assets:    ¥{bridge.non_operating_assets:>10,.0f}B")
    print(f"  - Debt:                    ¥{bridge.debt:>10,.0f}B")
    print(f"  - Minority Interests:      ¥{bridge.minority_interests:>10,.0f}B")
    print(f"  = Equity Value:            ¥{bridge.equity_value:>10,.0f}B")
    print(f"  Damodaran PDF:             ¥{expected['equity_value_billions']:>10,}B")

    eq_diff_pct = (bridge.equity_value - expected['equity_value_billions']) / expected['equity_value_billions'] * 100
    print(f"  Equity diff:               {eq_diff_pct:+.2f}%")

    # ========================================================================
    # TEST 4: Full Aggregator + Value/Share
    # ========================================================================
    print("\n[TEST 4] Full Cyclical DCF + Value/Share (¥4,735 hedef)")
    print("-"*80)

    result = cyclical_dcf_valuation(
        current_revenues=cn['revenues_2009_billions'],
        historical_avg_margin=cn['avg_operating_margin_98_09'],
        growth_rate=sg['growth_rate'],
        tax_rate=coc['tax_rate_japan_marginal'],
        reinvestment_rate=sg['reinvestment_rate'],
        wacc=coc['wacc'],
        cash=bs['cash_billions'],
        non_operating_assets=bs['non_operating_assets_billions'],
        debt=bs['debt_billions'],
        minority_interests=bs['minority_interests_billions'],
        shares_outstanding=market['shares_outstanding_millions'],
        current_op_margin=cn['current_operating_margin_2009'],
    )

    print(f"\n  Equity Value:    ¥{result.equity_bridge.equity_value:,.0f}B")
    print(f"  Shares:           {result.shares_outstanding:,.0f}M")
    print(f"  Value per Share: ¥{result.value_per_share*1000:.0f}  (note: B÷M = 1000× scale)")

    # NOT: equity_value billion, shares million → bölüm 1000× yer değiştirir
    # 16,326 B¥ / 3,448 M shares = 4.735 (B¥/M shares) = 4,735 ¥/share
    value_per_share_yen = result.value_per_share * 1000  # B÷M = Bin → Yen

    print(f"\n[VALUE PER SHARE — FINAL]")
    print(f"  Computed:    ¥{value_per_share_yen:,.0f}")
    print(f"  Expected:    ¥{expected['value_per_share_jpy']:,}")

    diff_pct = (value_per_share_yen - expected['value_per_share_jpy']) / expected['value_per_share_jpy'] * 100
    print(f"  Diff:         {diff_pct:+.2f}%")

    tolerance = expected['tolerance_pct']
    lower = expected['value_per_share_jpy'] * (1 - tolerance)
    upper = expected['value_per_share_jpy'] * (1 + tolerance)
    print(f"  Pass range:  ¥{lower:,.0f} - ¥{upper:,.0f}")

    if lower <= value_per_share_yen <= upper:
        print(f"\n  ✓✓✓ TOYOTA 2009 CYCLICAL DCF VALIDATION PASS ★★★")
        print(f"  4/4 VALIDATION CASE PASS — REELDEĞER motoru tam hazır!")
    else:
        print(f"\n  ✗ FAIL — {abs(diff_pct):.2f}% sapma")
        print(f"  Olası bug noktaları:")
        print(f"    - Normalize formülü (revenues × avg_margin)")
        print(f"    - Stable growth value formula")
        print(f"    - Equity bridge non-op assets / minority interests")
        print(f"    - Currency unit scaling (B÷M = 1000×)")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
