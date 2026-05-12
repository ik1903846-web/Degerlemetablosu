#!/usr/bin/env python
"""Phase 5b.1 PRE-IMPLEMENT TEST — Engine A + Damodaran EM data
5 ticker (TUPRS/EREGL/ARCLK/BIMAS/ASELS) manual Engine A run with:
  - terminal_margin: EM-first (margin_emerg.json) override (Adim 88 baseline global)
  - sales_to_capital: max(KAP, growth/Net_Cap_Ex_Sales_EM) floor (ASELS fix)
  - Diger inputs Adim 88 baseline (commit 88 pattern)
COMMIT YOK — sadece validation."""

import sys
import json
from pathlib import Path
from datetime import date

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.industrial_fcff import (
    ProjectionInputs, project_multi_year, dcf_valuation,
)
from dcf_engine_v4.inputs_helpers import (
    compute_sales_to_capital,
    compute_explicit_growth_rate,
    compute_taper_config,
    compute_non_operating_assets,
)
from data_layer.kap_excel_parser import parse_excel_html


# BIST -> Damodaran sector map (Phase 5b.1.2.A audit — sub-sector specificity)
# TUPRS refinery -> Oil/Gas Distribution (downstream, Integrated 17.74% too high)
# EREGL pure steel -> Steel sub-sector (Metals & Mining heterogeneous)
# BIMAS grocery chain -> Retail (Grocery and Food) sub-sector
BIST_DAMODARAN_SECTOR = {
    'TUPRS': 'Oil/Gas Distribution',          # 8.19% (was Integrated 17.74%)
    'EREGL': 'Steel',                          # 5.37% (was Metals & Mining 10.80%)
    'ARCLK': 'Household Products',             # 11.16% intact
    'BIMAS': 'Retail (Grocery and Food)',     # 3.77% (was Retail General 6.08%)
    'ASELS': 'Aerospace/Defense',              # 8.16% intact
}


def load_em_data():
    today = date.today().strftime('%Y_%m_%d')
    em_dir = Path(f'apps/api/data/damodaran/{today}/emerging_markets')
    with open(em_dir / 'margin_emerg.json', encoding='utf-8') as f:
        em_margin = json.load(f)
    with open(em_dir / 'capex_emerg.json', encoding='utf-8') as f:
        em_capex = json.load(f)
    return em_margin, em_capex


def em_terminal_margin(sector: str, em_margin: dict, fallback: float = 0.10) -> float:
    """Phase 5b.1: EM-first terminal_margin lookup."""
    rec = em_margin.get(sector, {})
    m = rec.get('Pre-tax Unadjusted Operating Margin')
    if m is not None and m > 0:
        return max(0.05, min(0.40, float(m)))
    return fallback


def em_sales_to_capital_floor(sector: str, em_capex: dict, growth: float, kap_s2c: float):
    """Phase 5b.1: max(KAP, growth/Net_Cap_Ex_Sales_EM) floor.

    Damodaran "Match data to region" — KAP s2c outlier (ASELS 0.088) icin
    EM sector benchmark floor. growth/Net_Cap_Ex_Sales = implied s2c.
    """
    rec = em_capex.get(sector, {})
    nce_sales = rec.get('Net Cap Ex/Sales')
    if nce_sales is None or nce_sales <= 0:
        return kap_s2c or 1.0
    em_implied_s2c = growth / nce_sales if growth > 0 else 1.0
    if kap_s2c is None:
        return em_implied_s2c
    return max(kap_s2c, em_implied_s2c)


def get_kap_fields(ticker: str):
    """Fresh KAP XLSX parse (Adim 5 batch hala stale icin)."""
    pf = Path(f'apps/api/_cache/parsed_financials/{ticker}.json')
    if not pf.exists():
        return None
    cached = json.loads(pf.read_text(encoding='utf-8'))
    disc = cached.get('disclosure_index')
    unit = cached.get('unit_multiplier', 1.0)
    xls = Path(f'apps/api/_cache/kap_excel/kap_excel_{disc}.xls')
    if not xls.exists():
        return None
    fli = parse_excel_html(xls.read_bytes(), disclosure_index=disc)

    def sc(v):
        return (v or 0) * unit if v else None

    return {
        'revenue': sc(fli.revenue_cari),
        'revenue_onceki': sc(fli.revenue_onceki),
        'op_income': sc(fli.operating_income_cari),
        'cash': sc(fli.cash),
        'total_debt': (sc(fli.short_term_debt) or 0) + (sc(fli.long_term_debt) or 0),
        'total_assets': sc(fli.total_assets),
        'minority': sc(fli.minority_interests),
        'fin_inv': sc(fli.financial_investments),
        'emi': sc(fli.equity_method_investments),
        'ip': sc(fli.investment_properties),
    }


def main():
    em_margin, em_capex = load_em_data()
    with open('apps/api/outputs/turkey_v4_batch.json', encoding='utf-8') as f:
        batch = json.load(f)

    tickers = list(BIST_DAMODARAN_SECTOR.keys())

    print("=" * 110)
    print("PHASE 5b.1 PRE-IMPLEMENT — Engine A + EM data (5 ticker, COMMIT YOK)")
    print("=" * 110)
    print(f"{'Ticker':<7} {'s2c':<7} {'start_m':<9} {'term_m':<9} {'g_exp':<8} {'intrinsic_TL':<14} {'market':<9} {'upside':<9} {'verdict'}")
    print("-" * 110)

    results = []
    for t in tickers:
        rec = next((r for r in batch['tickers'] if r['ticker'] == t), None)
        kap = get_kap_fields(t)
        if not kap or not rec:
            continue
        sector = BIST_DAMODARAN_SECTOR[t]
        lifecycle = rec.get('lifecycle_stage') or 'mature_stable'
        wacc = rec.get('wacc') or 0.12
        market = rec.get('current_price_tl') or 0
        shares = rec.get('shares_outstanding') or 1

        starting_margin = kap['op_income'] / kap['revenue'] if kap['revenue'] and kap['op_income'] else 0.05
        if starting_margin <= 0:
            starting_margin = 0.05  # floor (Damodaran convention)

        explicit_g = compute_explicit_growth_rate(kap['revenue'], kap['revenue_onceki'], lifecycle)
        terminal_m = em_terminal_margin(sector, em_margin)

        # Damodaran tax (KAP cari -> %25 effective floor)
        starting_tax_rate = 0.25

        # sales_to_capital with EM floor (Phase 5b.1 fix)
        kap_s2c = compute_sales_to_capital(kap['revenue'], kap['total_assets'], kap['cash']) or 1.0
        s2c = em_sales_to_capital_floor(sector, em_capex, explicit_g, kap_s2c)

        taper = compute_taper_config(lifecycle)
        non_op = compute_non_operating_assets(kap['fin_inv'], kap['ip'], kap['emi'])
        minority = kap['minority'] or 0

        inputs = ProjectionInputs(
            starting_revenues=kap['revenue'],
            sales_to_capital=s2c,
            starting_ebit_margin=starting_margin,
            terminal_ebit_margin=terminal_m,
            margin_taper_start_year=taper["margin_taper_start_year"],
            margin_taper_end_year=taper["margin_taper_end_year"],
            starting_tax_rate=starting_tax_rate,
            terminal_tax_rate=0.25,
            tax_taper_start_year=taper["tax_taper_start_year"],
            tax_taper_end_year=taper["tax_taper_end_year"],
            explicit_growth_rate=explicit_g,
            terminal_growth_rate=0.025,
            explicit_period_years=taper["explicit_period_years"],
            transition_period_years=taper["transition_period_years"],
        )

        try:
            projections = project_multi_year(inputs, total_years=10)
            result = dcf_valuation(
                projections=projections,
                wacc=wacc,
                stable_cost_of_capital=wacc * 0.9,
                stable_growth=0.025,
                stable_reinvestment_rate=0.025 / 0.12,
                debt=kap['total_debt'] or 0,
                minority_interests=minority,
                cash=kap['cash'] or 0,
                non_operating_assets=non_op,
                shares_outstanding=shares,
            )
            intrinsic_tl = result.value_per_share
            upside = ((intrinsic_tl - market) / market * 100) if market and market > 0 else None

            if intrinsic_tl is None or intrinsic_tl <= 0:
                verdict = "REJECT (negative)"
            elif intrinsic_tl > 10000:
                verdict = "REJECT (>10K)"
            elif upside is None:
                verdict = "n/a"
            elif -50 <= upside <= 500:
                verdict = "REASONABLE"
            else:
                verdict = "OUT_OF_BAND"

            results.append((t, intrinsic_tl, market, upside, verdict))

            intr_s = f"{intrinsic_tl:.2f}" if intrinsic_tl else "neg"
            ups_s = f"{upside:+.1f}%" if upside is not None else "n/a"
            print(f"{t:<7} {s2c:<7.3f} {starting_margin*100:<9.2f} {terminal_m*100:<9.2f} {explicit_g*100:<8.2f} {intr_s:<14} {market:<9.2f} {ups_s:<9} {verdict}")
        except Exception as e:
            print(f"{t}: ERROR {type(e).__name__}: {e}")
            results.append((t, None, market, None, f"ERROR {type(e).__name__}"))

    print()
    print("Adim 6 BLOCK trajectory (commit 88 baseline -> Phase 5b.1):")
    p4a = {'TUPRS': 168.88, 'EREGL': -22.63, 'ARCLK': 828.24, 'BIMAS': -263.30, 'ASELS': -27.56}
    for t, intr, mkt, ups, v in results:
        p_intr = p4a.get(t)
        delta = (intr - p_intr) if (intr and p_intr is not None) else None
        delta_s = f"{delta:+.2f} TL" if delta is not None else "n/a"
        print(f"  {t:<7} : 4a {p_intr:>7.2f} -> 5b.1 {(intr if intr else 0):>7.2f} TL (delta {delta_s})  -> {v}")

    print()
    reasonable_count = sum(1 for r in results if r[4] == "REASONABLE")
    print(f"VERDICT: {reasonable_count}/{len(results)} reasonable")
    if reasonable_count == len(results):
        print("  5/5 PASS -> Phase 5b.2 brief (orchestrator entegrasyon) onay HAZIR")
    elif reasonable_count == 4:
        print(f"  4/5 PASS -> Phase 5b.1.2 (outlier ticker tune)")
    else:
        print(f"  <4/5 PASS -> Phase 5b.1.3 logic tune (s2c veya margin)")


if __name__ == "__main__":
    main()
