#!/usr/bin/env python
"""Heineken inputs Engine B'ye (dcf_engine_v4/fcff_engine.py) verilse ne uretir?
Engine A (replication) -0.14% PASS, Engine B production simplified — sapma olcumu.
Read-only parite testi, kod degisikligi yok."""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine_v4.fcff_engine import calculate_fcff_dcf, DCFInputs


def main():
    case_path = Path(__file__).parent.parent / "validation_cases" / "heineken_2019.json"
    with open(case_path, 'r', encoding='utf-8') as f:
        hk = json.load(f)

    print("=" * 70)
    print("HEINEKEN 2019 — Engine A vs Engine B Parite Test")
    print("=" * 70)

    expected = hk['expected']['value_per_share']
    engine_a_actual = 59.57  # earlier test_full_dcf.py result

    # JSON'dan field extract (raw EUR, M -> 1e6)
    revenue = hk['operating']['revenues_ltm_millions'] * 1e6
    op_margin = hk['operating']['operating_margin_ltm']
    op_income = revenue * op_margin
    tax_rate = hk['operating']['effective_tax_rate_ltm']
    total_debt = hk['balance_sheet']['debt_millions'] * 1e6
    cash = hk['balance_sheet']['cash_millions'] * 1e6
    shares = hk['market']['shares_outstanding_millions'] * 1e6
    wacc = hk['cost_of_capital']['wacc']

    # Capex/DA proxies (Engine B requires, Heineken JSON ham capex'i ayri tutmuyor)
    # Brief'teki tahmin: capex ~5%, da ~4.5% of revenue
    capex = revenue * 0.05
    da = revenue * 0.045
    working_capital = 0.0  # initial level, delta'lar Engine B'de hesaplanir

    print(f"\nINPUTS (Heineken 2019 raw):")
    print(f"  Revenue:            EUR {revenue/1e9:.2f}B")
    print(f"  Operating margin:   {op_margin*100:.2f}%")
    print(f"  Op income:          EUR {op_income/1e9:.2f}B")
    print(f"  Tax rate:           {tax_rate*100:.2f}%")
    print(f"  Total debt:         EUR {total_debt/1e9:.2f}B")
    print(f"  Cash:               EUR {cash/1e9:.2f}B")
    print(f"  Shares:             {shares/1e6:.1f}M")
    print(f"  WACC:               {wacc*100:.2f}%")
    print(f"  CapEx (proxy 5%):   EUR {capex/1e9:.2f}B")
    print(f"  DA    (proxy 4.5%): EUR {da/1e9:.2f}B")
    print(f"  WC initial:         {working_capital}")

    inputs = DCFInputs(
        revenue=revenue,
        op_income=op_income,
        capex=capex,
        da=da,
        working_capital=working_capital,
        tax_rate=tax_rate,
        total_debt=total_debt,
        cash=cash,
        shares_outstanding=shares,
        wacc=wacc,
        lifecycle_stage='mature_stable',
        cross_holdings_value=0.0,
    )

    result = calculate_fcff_dcf(inputs)

    if result.error:
        print(f"\nEngine B ERROR: {result.error}")
        return

    print(f"\nENGINE B OUTPUT:")
    print(f"  explicit_g:         {result.explicit_g*100:.2f}% (fixed lifecycle)")
    print(f"  terminal_g:         {result.terminal_g*100:.2f}% (fixed lifecycle)")
    print(f"  fcff_year1:         EUR {result.fcff_year1/1e9:.2f}B" if result.fcff_year1 else "  fcff_year1:         N/A")
    print(f"  PV explicit:        EUR {result.pv_explicit/1e9:.2f}B" if result.pv_explicit else "  PV explicit:        N/A")
    print(f"  PV terminal:        EUR {result.pv_terminal/1e9:.2f}B" if result.pv_terminal else "  PV terminal:        N/A")
    print(f"  Enterprise value:   EUR {result.enterprise_value/1e9:.2f}B" if result.enterprise_value else "  Enterprise value:   N/A")
    print(f"  Equity value:       EUR {result.equity_value/1e9:.2f}B" if result.equity_value else "  Equity value:       N/A")

    actual = result.intrinsic_per_share

    print(f"\nPARITE KARSILASTIRMA:")
    print(f"  Damodaran expected: EUR {expected:.2f}")
    print(f"  Engine A actual:    EUR {engine_a_actual:.2f}  (diff vs Damodaran: -0.14%)")
    if actual is not None:
        engine_b_drift_vs_damo = (actual - expected) / expected * 100
        engine_b_drift_vs_a = (actual - engine_a_actual) / engine_a_actual * 100
        print(f"  Engine B output:    EUR {actual:.2f}")
        print(f"  Sapma vs Damodaran: {engine_b_drift_vs_damo:+.2f}%")
        print(f"  Sapma vs Engine A:  {engine_b_drift_vs_a:+.2f}%")

        print(f"\nKARAR:")
        abs_drift = abs(engine_b_drift_vs_damo)
        if abs_drift <= 5:
            tier = "Engine B Damodaran-uyumlu (+-%5)"
        elif abs_drift <= 15:
            tier = "Engine B kabul edilebilir simplification (5-15%)"
        elif abs_drift <= 30:
            tier = "Engine B onemli simplification (15-30%)"
        else:
            tier = "Engine B Damodaran'dan ciddi sapma (>30%)"
        print(f"  {tier}")

    print(f"\nDIAGNOSTIC:")
    print(f"  Engine B growth: 5y mature_stable=5%, terminal=3% (FIXED lifecycle)")
    print(f"  Heineken actual: 10y custom 3.22% -> -0.5% stable (DECLINING beer demand)")
    print(f"  Asymmetry sebep: Engine B 5y fixed lifecycle, custom taper destek YOK")
    print(f"  CapEx/DA proxy: revenue %5/%4.5 (Heineken JSON ham capex tutmuyor,")
    print(f"                  Damodaran reinvestment = ΔRev / sales-to-capital formul kullaniyor)")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
