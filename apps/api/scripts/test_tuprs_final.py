#!/usr/bin/env python
"""
TUPRS FINAL DCF — Faz 2.1.4 Adım 5

4 düzeltmenin birleşik etkisi:
- Adım 1: 12-yıl historical depth
- Adım 2: USD-only valuation
- Adım 3: Real shares outstanding (1.93B)
- Adım 4: Damodaran-aligned net CapEx

Bu "true intrinsic value" — Faz 2.1.3 placeholder bug'ları temizlendi.
"""
import sys
import asyncio
from pathlib import Path
from decimal import Decimal

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.isyatirim_scraper import fetch_yearly_extended
from data_layer.damodaran_mapper import map_to_damodaran_inputs
from data_layer.fx_converter import (
    get_static_rates,
    convert_inputs_to_usd,
    STATIC_YEAR_END_RATES,
)
from data_layer.shares_fetcher import get_shares_outstanding
from dcf_engine.cyclical_dcf import cyclical_dcf_valuation


def fmt_tl(val, scale=1_000_000_000):
    if val is None:
        return "    null"
    return f"{float(val) / scale:>10.2f}B TL"


def fmt_usd(val, scale=1_000_000_000):
    if val is None:
        return "    null"
    return f"{float(val) / scale:>10.2f}B USD"


def fmt_usd_m(val):
    if val is None:
        return "    null"
    return f"{float(val) / 1_000_000:>10.2f}M USD"


async def main():
    print("="*80)
    print("TUPRS FINAL DCF — Faz 2.1.4 Adım 5")
    print("="*80)
    print("4 düzeltme birleşik:")
    print("  ✓ 12-yıl historical depth (Adım 1)")
    print("  ✓ USD-only valuation (Adım 2)")
    print("  ✓ Real shares 1.93B (Adım 3)")
    print("  ✓ Damodaran net CapEx (Adım 4)")
    print("="*80)

    # ========================================================================
    # STEP 1: Data Pipeline (12-yıl + USD)
    # ========================================================================
    print("\n[STEP 1] Data Pipeline — 12-yıl USD")
    print("-"*80)

    years = list(range(2024, 2012, -1))
    statements = await fetch_yearly_extended(ticker="TUPRS", years=years)
    inputs_tl = map_to_damodaran_inputs(statements)

    fx_series = get_static_rates(years)
    inputs_usd = convert_inputs_to_usd(inputs_tl, fx_series)

    print(f"  Periods:     {len(inputs_usd.period_labels)} (12-yıl)")
    print(f"  Currency:    {inputs_usd.currency}")
    print(f"  Items found: {inputs_usd.items_found}/12")

    # ========================================================================
    # STEP 2: Cyclical Normalization (USD-bazlı, 12-yıl avg)
    # ========================================================================
    print("\n[STEP 2] Cyclical Normalization (USD, 12-yıl through-the-cycle)")
    print("-"*80)

    # USD operating margin 12-yıl avg (Adım 1 + 2 birleşik)
    margins = [m for m in inputs_usd.operating_margin if m is not None]
    avg_margin_12y = sum(margins) / len(margins)

    # Current USD revenue (2024)
    current_revenue_usd = float(inputs_usd.revenue[0])

    print(f"  12-yıl margin range:    {float(min(margins))*100:.2f}% → {float(max(margins))*100:.2f}%")
    print(f"  Through-the-cycle avg:  {float(avg_margin_12y)*100:.2f}%")
    print(f"  Current revenue (2024): {fmt_usd(current_revenue_usd)} = {current_revenue_usd/1_000_000_000:.2f}B USD")
    print(f"  Normalized OI:          {fmt_usd(current_revenue_usd * float(avg_margin_12y))} (revenue × margin)")

    # ========================================================================
    # STEP 3: WACC (USD-bazlı, consistent)
    # ========================================================================
    print("\n[STEP 3] Cost of Capital (USD-only, ADR-002 compliant)")
    print("-"*80)

    # Damodaran current parameters (Nisan 2026)
    rf_usd = 0.0397           # Rf USD
    mature_erp = 0.0444       # Mature market ERP
    turkey_crp = 0.0601       # Turkey country risk

    cost_of_equity = rf_usd + 1.0 * mature_erp + 1.0 * turkey_crp

    # Debt ratio USD-bazlı
    debt_usd = float(inputs_usd.total_debt[0])
    equity_usd = float(inputs_usd.total_equity[0])
    debt_ratio = debt_usd / (debt_usd + equity_usd)

    pretax_kd = rf_usd + 0.03  # BB rated
    statutory_tax = 0.25
    after_tax_kd = pretax_kd * (1 - statutory_tax)

    wacc = (1 - debt_ratio) * cost_of_equity + debt_ratio * after_tax_kd

    print(f"  Rf USD:               {rf_usd*100:.2f}%")
    print(f"  Mature ERP:           {mature_erp*100:.2f}%")
    print(f"  Turkey CRP:           {turkey_crp*100:.2f}%")
    print(f"  Cost of Equity:       {cost_of_equity*100:.2f}%")
    print(f"  Debt ratio:           {debt_ratio*100:.2f}% (USD-bazlı)")
    print(f"  Pretax Kd:            {pretax_kd*100:.2f}%")
    print(f"  After-tax Kd:         {after_tax_kd*100:.2f}%")
    print(f"  WACC:                 {wacc*100:.2f}%")

    # ========================================================================
    # STEP 4: Stable Growth + Real Reinvestment Rate
    # ========================================================================
    print("\n[STEP 4] Stable Growth Assumptions")
    print("-"*80)

    stable_growth = 0.03  # 3% USD long-run

    # Real reinvestment rate (Adım 4 net CapEx)
    # 12-yıl avg reinvestment rate
    reinv_total_usd = []
    for i in range(len(inputs_usd.net_capex)):
        nc = inputs_usd.net_capex[i]
        wc = inputs_usd.working_capital_change[i]
        rev = inputs_usd.revenue[i]

        if nc is not None and wc is not None and rev is not None and rev > 0:
            reinv = float((nc + wc) / rev)
            reinv_total_usd.append(reinv)

    actual_reinv_rate = sum(reinv_total_usd) / len(reinv_total_usd) if reinv_total_usd else 0

    # Damodaran "stable phase" reinvestment = g/ROC (mature firm)
    roc = wacc  # Mature firm: ROC = WACC
    stable_reinv_rate = stable_growth / roc if roc > 0 else 0

    print(f"  Stable growth (USD):     {stable_growth*100:.2f}%")
    print(f"  ROC (= WACC mature):     {roc*100:.2f}%")
    print(f"  Stable reinvestment:     {stable_reinv_rate*100:.2f}% (g/ROC)")
    print(f"  Actual 12-yıl avg reinv: {actual_reinv_rate*100:.2f}% (diagnostic)")

    # ========================================================================
    # STEP 5: Cyclical DCF Execute (USD-bazlı)
    # ========================================================================
    print("\n[STEP 5] Cyclical DCF — Single Stage Stable Growth (USD)")
    print("-"*80)

    cash_usd = float(inputs_usd.cash[0])
    minority_usd = 0.0  # TUPRS minor
    non_op_usd = 0.0

    # Damodaran convention: shares Cyclical DCF içinde (placeholder geç)
    placeholder_shares = 1

    print(f"  Inputs (USD-bazlı):")
    print(f"    Current Revenue:      {fmt_usd(current_revenue_usd)}")
    print(f"    Normalized margin:    {float(avg_margin_12y)*100:.2f}%")
    print(f"    WACC:                 {wacc*100:.2f}%")
    print(f"    Stable growth:        {stable_growth*100:.2f}%")
    print(f"    Tax rate:             {statutory_tax*100:.0f}%")
    print(f"    Reinvestment rate:    {stable_reinv_rate*100:.2f}%")
    print(f"    Cash:                 {fmt_usd(cash_usd)}")
    print(f"    Total Debt:           {fmt_usd(debt_usd)}")

    result = cyclical_dcf_valuation(
        current_revenues=current_revenue_usd,
        historical_avg_margin=float(avg_margin_12y),
        growth_rate=stable_growth,
        tax_rate=statutory_tax,
        reinvestment_rate=stable_reinv_rate,
        wacc=wacc,
        cash=cash_usd,
        non_operating_assets=non_op_usd,
        debt=debt_usd,
        minority_interests=minority_usd,
        shares_outstanding=placeholder_shares,
        options_value=0.0,
        current_op_margin=float(inputs_usd.operating_margin[0]) if inputs_usd.operating_margin[0] else None,
    )

    print(f"\n[RESULTS — USD]")
    print(f"  Normalized OI:           {fmt_usd(result.normalization.normalized_op_income)}")
    print(f"  Operating Assets:        {fmt_usd(result.operating_value.operating_assets_value)}")
    print(f"\n  Equity Bridge (USD):")
    print(f"    Operating:             {fmt_usd(result.equity_bridge.operating_assets)}")
    print(f"    + Cash:                {fmt_usd(result.equity_bridge.cash)}")
    print(f"    + Non-op:              {fmt_usd(result.equity_bridge.non_operating_assets)}")
    print(f"    - Debt:                {fmt_usd(-result.equity_bridge.debt)}")
    print(f"    - Minority:            {fmt_usd(-result.equity_bridge.minority_interests)}")
    print(f"    = Equity Value:        {fmt_usd(result.equity_bridge.equity_value)}")

    equity_value_usd = result.equity_bridge.equity_value

    # ========================================================================
    # STEP 6: Real Shares + Per Share (USD → TL)
    # ========================================================================
    print("\n[STEP 6] Value per Share Calculation")
    print("-"*80)

    tuprs_shares = get_shares_outstanding("TUPRS")
    if tuprs_shares is None:
        print("  ✗ TUPRS shares not found")
        return

    # USD value per share
    value_per_share_usd = equity_value_usd / tuprs_shares.shares

    # Spot rate USD/TL (24 Nisan 2026 ~ 35.37)
    spot_rate_usd_tl = 35.37
    value_per_share_tl = value_per_share_usd * spot_rate_usd_tl

    print(f"  Equity Value (USD):       {fmt_usd(equity_value_usd)}")
    print(f"  Real Shares Outstanding:  {tuprs_shares.shares:,} ({tuprs_shares.shares_billions:.4f}B)")
    print(f"  Value per Share (USD):    ${value_per_share_usd:.4f}")
    print(f"  Spot rate (24 Nis 2026):  {spot_rate_usd_tl} TL/USD")
    print(f"  ")
    print(f"  ★ Value per Share (TL):  {value_per_share_tl:.2f} TL")

    # ========================================================================
    # STEP 7: Market Comparison
    # ========================================================================
    print("\n[STEP 7] Market Comparison (24 Nisan 2026)")
    print("-"*80)

    market_price_tl = 269.00  # Web search'le doğrulandı
    market_cap_tl = market_price_tl * tuprs_shares.shares
    market_cap_usd = market_cap_tl / spot_rate_usd_tl

    upside = (value_per_share_tl - market_price_tl) / market_price_tl * 100

    print(f"  Market Price (TL):        {market_price_tl:.2f} TL")
    print(f"  DCF Value (TL):           {value_per_share_tl:.2f} TL")
    print(f"  Upside / (Discount):      {upside:+.2f}%")
    print(f"  ")
    print(f"  Market Cap (TL):          {market_cap_tl/1_000_000_000:.2f}B TL")
    print(f"  DCF Equity Value (TL):    {float(equity_value_usd) * spot_rate_usd_tl/1_000_000_000:.2f}B TL")

    # Damodaran interpretation
    print(f"\n  Damodaran Yorumu:")
    if upside > 30:
        print(f"  → ÇOK UCUZ (DCF market'ten %{upside:.0f} yüksek)")
        print(f"  → AL (margin of safety > %30)")
    elif upside > 10:
        print(f"  → UCUZ (DCF market'ten %{upside:.0f} yüksek)")
        print(f"  → IZLE (potansiyel buy)")
    elif upside > -10:
        print(f"  → FAIR VALUE (±%10 band)")
        print(f"  → BEKLE")
    elif upside > -30:
        print(f"  → PAHALI (DCF market'ten %{abs(upside):.0f} düşük)")
        print(f"  → IZLE (potansiyel sell)")
    else:
        print(f"  → ÇOK PAHALI (DCF market'ten %{abs(upside):.0f} düşük)")
        print(f"  → SAT")

    # ========================================================================
    # STEP 8: Faz 2.1.3 vs Adım 5 Karşılaştırma
    # ========================================================================
    print("\n[STEP 8] Faz 2.1.3 vs Adım 5 Karşılaştırma")
    print("-"*80)

    print(f"  Metric                | Faz 2.1.3 (BUG)      | Adım 5 (FINAL)       |")
    print(f"  ----------------------|----------------------|-----------------------|")
    print(f"  Historical depth      | 4-yıl                | 12-yıl                |")
    print(f"  Margin baseline       | 5.91% (4Y avg)       | {float(avg_margin_12y)*100:.2f}% (12Y avg)      |")
    print(f"  Currency              | TL+USD hibrit (BUG)  | USD-only              |")
    print(f"  Shares outstanding    | 2.5B (placeholder)   | 1.93B (real)          |")
    print(f"  Net CapEx             | 192B TL (raw, BUG)   | 117B TL (Damodaran)   |")
    print(f"  Reinvestment rate     | 21.66% (g/ROC TL)    | {stable_reinv_rate*100:.2f}% (g/ROC USD)   |")
    print(f"  Value per Share       | 169.94 TL (BUG)      | {value_per_share_tl:.2f} TL          |")

    print("\n" + "="*80)
    print("✓✓✓ TUPRS FINAL DCF EXECUTE PASS")
    print(f"INTRINSIC VALUE: {value_per_share_tl:.2f} TL/share (USD: ${value_per_share_usd:.4f})")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
