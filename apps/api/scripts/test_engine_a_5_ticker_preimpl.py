#!/usr/bin/env python
"""Phase 4a Adim 6 PRE-IMPLEMENT TEST — 5 ticker Engine A manual run.
Adim 1-5 helper'larini composing ProjectionInputs build edip Engine A
industrial_fcff'i 5 ticker icin manuel calistirir.
revenue_onceki batch stale, fresh KAP XLSX parse ediyor (sanity)."""

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
    compute_terminal_ebit_margin,
    compute_taper_config,
    compute_non_operating_assets,
)
from data_layer.kap_excel_parser import parse_excel_html


def get_revenue_onceki(ticker: str) -> float:
    """Fresh KAP XLSX parse (batch stale, Adim 5 transfer regen pending)."""
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
    return (fli.revenue_onceki or 0) * unit if fli.revenue_onceki else None


def get_minority(ticker: str) -> float:
    pf = Path(f'apps/api/_cache/parsed_financials/{ticker}.json')
    cached = json.loads(pf.read_text(encoding='utf-8'))
    disc = cached.get('disclosure_index')
    unit = cached.get('unit_multiplier', 1.0)
    xls = Path(f'apps/api/_cache/kap_excel/kap_excel_{disc}.xls')
    fli = parse_excel_html(xls.read_bytes(), disclosure_index=disc)
    return (fli.minority_interests or 0) * unit if fli.minority_interests else 0


def get_non_op(ticker: str) -> float:
    pf = Path(f'apps/api/_cache/parsed_financials/{ticker}.json')
    cached = json.loads(pf.read_text(encoding='utf-8'))
    disc = cached.get('disclosure_index')
    unit = cached.get('unit_multiplier', 1.0)
    xls = Path(f'apps/api/_cache/kap_excel/kap_excel_{disc}.xls')
    fli = parse_excel_html(xls.read_bytes(), disclosure_index=disc)
    fi = (fli.financial_investments or 0) * unit if fli.financial_investments else 0
    em = (fli.equity_method_investments or 0) * unit if fli.equity_method_investments else 0
    ip = (fli.investment_properties or 0) * unit if fli.investment_properties else 0
    return compute_non_operating_assets(fi, ip, em)


def main():
    with open('apps/api/outputs/turkey_v4_batch.json', encoding='utf-8') as f:
        batch = json.load(f)
    today = date.today().strftime('%Y_%m_%d')
    with open(f'apps/api/data/damodaran/{today}/sector_multiples.json', encoding='utf-8') as f:
        sector_multiples = json.load(f)

    tickers = ['TUPRS', 'EREGL', 'ARCLK', 'BIMAS', 'ASELS']

    print("=" * 100)
    print("PHASE 4a PRE-IMPLEMENT — 5 ticker Engine A manual run (TL native)")
    print("=" * 100)

    summary = []

    for t in tickers:
        rec = next((r for r in batch['tickers'] if r['ticker'] == t), None)
        if not rec:
            continue

        print(f"\n=== {t} ===")
        revenue = rec.get('revenue')
        op_income = rec.get('op_income')
        tax_expense = rec.get('tax_expense') or 0
        total_assets = rec.get('total_assets')  # batch stale, may be None
        cash = rec.get('cash') or 0
        sector_name = rec.get('sector_name')
        lifecycle = rec.get('lifecycle_stage') or 'mature_stable'
        wacc = rec.get('wacc')
        market_price = rec.get('current_price_tl')
        shares = rec.get('shares_outstanding')

        # Batch stale (Adim 1+5 regen pending) - fresh XLSX fallback
        if not total_assets:
            pf = Path(f'apps/api/_cache/parsed_financials/{t}.json')
            cached = json.loads(pf.read_text(encoding='utf-8'))
            disc = cached.get('disclosure_index')
            unit = cached.get('unit_multiplier', 1.0)
            xls = Path(f'apps/api/_cache/kap_excel/kap_excel_{disc}.xls')
            fli = parse_excel_html(xls.read_bytes(), disclosure_index=disc)
            total_assets = (fli.total_assets or 0) * unit
            print(f"  total_assets: fresh XLSX parse = {total_assets/1e9:.1f}B (batch stale)")

        revenue_onceki = get_revenue_onceki(t)
        minority = get_minority(t)
        non_op = get_non_op(t)

        starting_margin = op_income / revenue if (revenue and op_income) else None
        starting_tax_rate = (tax_expense / op_income) if (op_income and op_income > 0) else 0.25
        # tax_expense KAP'ta negatif olabilir (vergi gideri)
        if starting_tax_rate < 0:
            starting_tax_rate = abs(starting_tax_rate)
        starting_tax_rate = min(max(starting_tax_rate, 0.10), 0.40)

        taper = compute_taper_config(lifecycle)

        inputs = ProjectionInputs(
            starting_revenues=revenue,
            sales_to_capital=compute_sales_to_capital(revenue, total_assets, cash) or 1.0,
            starting_ebit_margin=starting_margin,
            terminal_ebit_margin=compute_terminal_ebit_margin(sector_name, starting_margin, sector_multiples),
            margin_taper_start_year=taper["margin_taper_start_year"],
            margin_taper_end_year=taper["margin_taper_end_year"],
            starting_tax_rate=starting_tax_rate,
            terminal_tax_rate=0.25,
            tax_taper_start_year=taper["tax_taper_start_year"],
            tax_taper_end_year=taper["tax_taper_end_year"],
            explicit_growth_rate=compute_explicit_growth_rate(revenue, revenue_onceki, lifecycle),
            terminal_growth_rate=0.025,
            explicit_period_years=taper["explicit_period_years"],
            transition_period_years=taper["transition_period_years"],
        )

        print(f"  Lifecycle: {lifecycle}, Sector: {sector_name}")
        print(f"  Inputs:")
        print(f"    starting_revenues   : {revenue/1e9:.1f}B TL")
        print(f"    sales_to_capital    : {inputs.sales_to_capital:.3f}")
        print(f"    start ebit margin   : {starting_margin*100:.2f}%")
        print(f"    terminal ebit margin: {inputs.terminal_ebit_margin*100:.2f}%")
        print(f"    margin_taper        : {inputs.margin_taper_start_year}-{inputs.margin_taper_end_year}")
        print(f"    tax_taper           : {inputs.tax_taper_start_year}-{inputs.tax_taper_end_year}")
        print(f"    start tax rate      : {starting_tax_rate*100:.2f}%")
        print(f"    terminal tax rate   : 25.00%")
        print(f"    explicit growth     : {inputs.explicit_growth_rate*100:+.2f}%")
        print(f"    terminal growth     : 2.50%")
        print(f"    explicit/transition : {inputs.explicit_period_years}y / {inputs.transition_period_years}y")
        print(f"    revenue_onceki      : {revenue_onceki/1e9:.1f}B")
        print(f"  Balance: debt={rec.get('total_debt') or 0:.0f}, cash={cash/1e9:.1f}B, minority={minority/1e9:.2f}B, non_op={non_op/1e9:.2f}B")
        print(f"  WACC={wacc*100 if wacc else 'n/a':.2f}%, shares={shares/1e6 if shares else 0:.1f}M, market_price={market_price}")

        try:
            projections = project_multi_year(inputs, total_years=10)
            result = dcf_valuation(
                projections=projections,
                wacc=wacc or 0.20,
                stable_cost_of_capital=(wacc or 0.20) * 0.9,
                stable_growth=0.025,
                stable_reinvestment_rate=0.025 / 0.12,
                debt=rec.get('total_debt') or 0,
                minority_interests=minority,
                cash=cash,
                non_operating_assets=non_op,
                shares_outstanding=shares or 1,
            )
            intrinsic_tl = result.value_per_share
            upside = ((intrinsic_tl - market_price) / market_price * 100) if market_price else None
            print(f"  RESULT (TL native):")
            print(f"    operating_value     : {result.operating_assets_value/1e9:.1f}B TL")
            print(f"    equity_value        : {result.equity_value/1e9:.1f}B TL")
            print(f"    value_per_share     : {intrinsic_tl:.2f} TL")
            print(f"    market_price        : {market_price} TL")
            if upside is not None:
                print(f"    upside              : {upside:+.1f}%")
            summary.append((t, intrinsic_tl, market_price, upside))
        except Exception as e:
            print(f"  ENGINE A ERROR: {type(e).__name__}: {e}")
            summary.append((t, None, market_price, None))

    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"{'Ticker':<8} {'Intrinsic':<12} {'Market':<12} {'Upside'}")
    for t, intr, mkt, ups in summary:
        intr_s = f"{intr:.2f} TL" if intr is not None else "ERROR"
        mkt_s = f"{mkt} TL" if mkt else "n/a"
        ups_s = f"{ups:+.1f}%" if ups is not None else "n/a"
        print(f"{t:<8} {intr_s:<12} {mkt_s:<12} {ups_s}")

    print()
    print("Pre-implement sanity:")
    print("  TUPRS Engine B output 211.95 TL (Damodaran reference DEGIL)")
    print("  TUPRS Engine A beklenen band: 90-130 TL (Damodaran 'industrial cyclical')")
    print("  Bu test TL native; USD-currency convention Adim 6 sirasinda eklenir.")


if __name__ == "__main__":
    main()
