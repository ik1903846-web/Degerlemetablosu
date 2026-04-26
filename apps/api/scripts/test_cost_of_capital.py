#!/usr/bin/env python
"""
Cost of Capital — Heineken 2019 validation tests (Faz 1.3.2).

5 test:
  1. Cost of Equity     (target 7.66%, ±5 bps)
  2. Unlever Beta       (target 0.80, ±0.05)
  3. Relever Beta       (target 1.20, ±0.05)
  4. After-tax Cost of Debt (target 1.13%, ±5 bps)
  5. WACC               (target 5.04%, ±5 bps)

Source: validation_cases/heineken_2019.json (Damodaran valpacket1spr26.pdf p.206)
"""
import json
import sys
from pathlib import Path

# Windows cp1252 -> utf-8 stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Repo root'u path'e ekle (apps/api'yi import edebilmek için)
API_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(API_ROOT))

from dcf_engine.cost_of_capital import (  # noqa: E402
    cost_of_equity,
    unlever_beta,
    relever_beta,
    after_tax_cost_of_debt,
    wacc,
)

CASE_PATH = API_ROOT / "validation_cases" / "heineken_2019.json"

# Toleranslar
BPS_TOL = 0.0005   # 5 bps = 0.05%
BETA_TOL = 0.05    # 0.05 beta puanı


def fmt_pct(x: float) -> str:
    return f"{x*100:.4f}%"


def fmt_bps(diff: float) -> str:
    return f"{diff*10000:+.2f} bps"


def run_test(name: str, computed: float, expected: float, tol: float, unit: str) -> bool:
    diff = computed - expected
    passed = abs(diff) <= tol
    status = "PASS" if passed else "FAIL"
    print(f"\n[{status}] {name}")
    print(f"  Computed: {computed:.6f}  ({fmt_pct(computed) if unit == 'pct' else f'{computed:.4f}'})")
    print(f"  Expected: {expected:.6f}  ({fmt_pct(expected) if unit == 'pct' else f'{expected:.4f}'})")
    if unit == "pct":
        print(f"  Diff:     {fmt_bps(diff)}  (tol: ±{tol*10000:.0f} bps)")
    else:
        print(f"  Diff:     {diff:+.4f}  (tol: ±{tol})")
    return passed


def main():
    print(f"[LOAD] {CASE_PATH}")
    with open(CASE_PATH, 'r', encoding='utf-8') as f:
        case = json.load(f)

    coc = case['cost_of_capital']
    growth = case['growth']

    rf = coc['euro_riskfree_rate']            # -0.005
    beta_l = coc['levered_beta']              # 1.20
    beta_u = coc['unlevered_beta_sector_alcoholic_beverage']  # 0.80
    erp = coc['revenue_weighted_erp']         # 0.0683
    de = coc['de_ratio']                      # 0.6698
    tax = growth['marginal_tax_rate']         # 0.25
    spread = coc['default_spread']            # 0.02
    e_w = coc['equity_weight']                # 0.599
    d_w = coc['debt_weight']                  # 0.401

    expected_coe = coc['cost_of_equity']                 # 0.0766
    expected_kd = coc['cost_of_debt_after_tax']          # 0.0113
    expected_wacc = coc['wacc']                          # 0.0504
    expected_beta_l = coc['levered_beta']                # 1.20
    expected_beta_u = coc['unlevered_beta_sector_alcoholic_beverage']  # 0.80

    print(f"\n[CASE] {case['case_id']}")
    print(f"[INPUTS]")
    print(f"  Rf={fmt_pct(rf)}  ERP={fmt_pct(erp)}  β_L={beta_l}  β_U={beta_u}")
    print(f"  D/E={de}  tax={fmt_pct(tax)}  spread={fmt_pct(spread)}")
    print(f"  E_w={e_w}  D_w={d_w}")

    results = []

    # ---- TEST 1: Cost of Equity ----
    coe = cost_of_equity(rf, beta_l, erp)
    results.append(("Cost of Equity",
                    run_test("TEST 1 — Cost of Equity = Rf + β_L × ERP",
                             coe, expected_coe, BPS_TOL, "pct")))

    # ---- TEST 2: Unlever Beta ----
    beta_u_calc = unlever_beta(beta_l, de, tax)
    results.append(("Unlever Beta",
                    run_test("TEST 2 — Unlever β = β_L / (1 + (1-t)×D/E)",
                             beta_u_calc, expected_beta_u, BETA_TOL, "beta")))

    # ---- TEST 3: Relever Beta ----
    beta_l_calc = relever_beta(beta_u, de, tax)
    results.append(("Relever Beta",
                    run_test("TEST 3 — Relever β = β_U × (1 + (1-t)×D/E)",
                             beta_l_calc, expected_beta_l, BETA_TOL, "beta")))

    # ---- TEST 4: After-tax Cost of Debt ----
    kd = after_tax_cost_of_debt(rf, spread, tax)
    results.append(("After-tax Kd",
                    run_test("TEST 4 — Kd_after_tax = (Rf + spread) × (1-t)",
                             kd, expected_kd, BPS_TOL, "pct")))

    # ---- TEST 5: WACC ----
    wacc_result = wacc(coe, kd, e_w, d_w)
    results.append(("WACC",
                    run_test("TEST 5 — WACC = E_w×Re + D_w×Kd",
                             wacc_result.wacc, expected_wacc, BPS_TOL, "pct")))

    # ---- Summary ----
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    pass_count = sum(1 for _, p in results if p)
    for name, passed in results:
        marker = "✓" if passed else "✗"
        print(f"  {marker} {name}: {'PASS' if passed else 'FAIL'}")
    print(f"\n  {pass_count}/{len(results)} PASS")

    if pass_count == len(results):
        print("\n[OK] Cost of Capital implementasyonu Heineken 2019 ground truth ile doğrulandı.")
        sys.exit(0)
    else:
        print("\n[FAIL] En az bir formülde sapma var — yukarıdaki diff'leri incele.")
        sys.exit(1)


if __name__ == "__main__":
    main()
