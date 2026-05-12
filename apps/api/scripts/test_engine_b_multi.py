#!/usr/bin/env python
"""Engine B multi-case parite — Heineken / Tube / Toyota Damodaran sapma pattern.

Her case JSON yapisi farkli (nested), her birine ozel adapter.
Engine B'nin lifecycle-driven generic projection'i tum case'lerde Damodaran
custom taper'larina UYAMAZ — sapma magnitude pattern karari Phase 4 oncelik icin.
"""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine_v4.fcff_engine import calculate_fcff_dcf, DCFInputs


def adapt_heineken(case):
    """Heineken 2019 (industrial 2-stage, mature declining)."""
    revenue = case['operating']['revenues_ltm_millions'] * 1e6
    op_margin = case['operating']['operating_margin_ltm']
    return dict(
        revenue=revenue,
        op_income=revenue * op_margin,
        capex=revenue * 0.05,
        da=revenue * 0.045,
        working_capital=0.0,
        tax_rate=case['operating']['effective_tax_rate_ltm'],
        total_debt=case['balance_sheet']['debt_millions'] * 1e6,
        cash=case['balance_sheet']['cash_millions'] * 1e6,
        shares_outstanding=case['market']['shares_outstanding_millions'] * 1e6,
        wacc=case['cost_of_capital']['wacc'],
        lifecycle_stage='mature_stable',
        cross_holdings_value=0.0,
    )


def adapt_tube(case):
    """Tube Investments (EM 2-stage, India CRP, RR×ROC growth ~5.52%)."""
    tax = case['cost_of_capital_high_growth']['tax_rate']
    ebit_after_tax = case['starting_metrics']['ebit_after_tax_millions'] * 1e6
    op_income = ebit_after_tax / (1 - tax)
    revenue = op_income / 0.10  # placeholder margin (Tube revenue exposed degil)
    return dict(
        revenue=revenue,
        op_income=op_income,
        capex=revenue * 0.05,
        da=revenue * 0.045,
        working_capital=0.0,
        tax_rate=tax,
        total_debt=case['balance_sheet']['debt_millions'] * 1e6,
        cash=case['balance_sheet']['cash_millions'] * 1e6,
        shares_outstanding=case['market']['shares_outstanding_millions'] * 1e6,
        wacc=case['high_growth_phase']['wacc'],  # 16.9%
        lifecycle_stage='mature_growth',  # 10%/3%, Tube actual 5.52%/5%
        cross_holdings_value=0.0,
    )


def adapt_toyota(case):
    """Toyota 2009 (cyclical normalized, 1-stage stable growth)."""
    revenue = case['cyclical_normalization']['revenues_2009_billions'] * 1e9
    op_margin = case['cyclical_normalization']['avg_operating_margin_98_09']
    return dict(
        revenue=revenue,
        op_income=revenue * op_margin,
        capex=revenue * 0.05,
        da=revenue * 0.045,
        working_capital=0.0,
        tax_rate=case['cost_of_capital']['tax_rate_japan_marginal'],
        total_debt=case['balance_sheet']['debt_billions'] * 1e9,
        cash=case['balance_sheet']['cash_billions'] * 1e9,
        shares_outstanding=case['market']['shares_outstanding_millions'] * 1e6,
        wacc=case['cost_of_capital']['wacc'],
        lifecycle_stage='mature_stable',
        cross_holdings_value=0.0,
    )


CASES = [
    ('heineken_2019.json', 59.65, 'EUR', adapt_heineken,
     'declining mature: explicit 3.22% -> terminal -0.5%'),
    ('tube_investments_status_quo.json', 61.57, 'INR', adapt_tube,
     'EM growth: explicit 5.52% -> stable 5% (high WACC 16.9%)'),
    ('toyota_2009.json', 4735.0, 'JPY', adapt_toyota,
     'cyclical normalized: 1-stage stable 1.5% (NOT 5%)'),
]


def main():
    print("=" * 90)
    print("ENGINE B (production v4) MULTI-CASE PARITE — Damodaran sapma pattern")
    print("=" * 90)
    print(f"{'Case':<28} {'Damodaran':<14} {'Engine B':<14} {'Sapma':<10} {'Pattern'}")
    print("-" * 90)

    summary = []
    for case_file, expected, ccy, adapter, taper_note in CASES:
        path = Path(__file__).parent.parent / 'validation_cases' / case_file
        try:
            with open(path) as f:
                case = json.load(f)
            kwargs = adapter(case)
            inputs = DCFInputs(**kwargs)
            result = calculate_fcff_dcf(inputs)

            if result.error:
                print(f"{case_file:<28}  ENGINE B ERROR: {result.error}")
                summary.append((case_file, None, "ERROR"))
                continue

            actual = result.intrinsic_per_share
            drift = (actual - expected) / expected * 100

            if abs(drift) <= 5:
                pattern = "DAMODARAN-UYUMLU"
            elif abs(drift) <= 30:
                pattern = "KABUL EDILEBILIR"
            elif abs(drift) <= 100:
                pattern = "ONEMLI SAPMA"
            else:
                pattern = "CIDDI SAPMA"

            case_name = case_file.replace('.json', '')[:27]
            damo_str = f"{ccy} {expected:>9.2f}"
            eng_str = f"{ccy} {actual:>9.2f}"
            print(f"{case_name:<28} {damo_str:<14} {eng_str:<14} {drift:+7.1f}%  {pattern}")
            summary.append((case_file, drift, pattern))

            # diagnostic per case
            print(f"  -> {taper_note}")
            print(f"  -> WACC={kwargs['wacc']*100:.2f}%, Engine B terminal_g=3%, denominator={(kwargs['wacc']-0.03)*100:.2f}%")
            print()

        except Exception as e:
            print(f"{case_file:<28}  EXCEPTION: {type(e).__name__}: {e}")
            summary.append((case_file, None, "EXCEPTION"))
            print()

    print("=" * 90)
    print("PATTERN OZET:")
    all_drifts = [s[1] for s in summary if s[1] is not None]
    if all_drifts:
        max_abs = max(abs(d) for d in all_drifts)
        if all(abs(d) > 100 for d in all_drifts):
            verdict = "TUM CASE >100% -> Engine B SYSTEMIC SAPMA (Phase 4a swap adayi)"
        elif all(abs(d) > 30 for d in all_drifts):
            verdict = "TUM CASE >30% -> Engine B genel olarak Damodaran'dan onemli sapiyor"
        elif any(abs(d) <= 30 for d in all_drifts):
            verdict = "KARISIK pattern -> Engine B bazi case'lerde uyumlu, bazilarinda sapma"
        else:
            verdict = "Sapma karisik"
        print(f"  {verdict}")
        print(f"  Max abs drift: {max_abs:.1f}%")

    print("=" * 90)


if __name__ == "__main__":
    main()
