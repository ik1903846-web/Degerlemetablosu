#!/usr/bin/env python
"""
TUPRS Cyclical DCF — BIST ilk gerçek uygulama (Faz 2.1.3).

Pipeline:
  isyatirim_scraper → damodaran_mapper → cyclical_dcf

Toyota 2009 modelini TUPRS'e uygula:
- Cyclical normalization (historical avg margin)
- Single-stage stable growth
- Extended equity bridge (cash + non-op - debt - minority)

Bu test value/share hedef koymaz — sadece motorun BIST'te
end-to-end çalıştığını ispatlar.
"""
import sys
import asyncio
from pathlib import Path
from decimal import Decimal

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.isyatirim_scraper import fetch_yearly
from data_layer.damodaran_mapper import map_to_damodaran_inputs
from dcf_engine.cyclical_dcf import (
    cyclical_dcf_valuation,
    normalize_operating_income,
    single_stage_stable_growth_value,
    equity_bridge_cyclical,
)


def fmt_billions(val, suffix="B"):
    """Format Decimal in billions."""
    if val is None:
        return "    null"
    val_b = float(val) / 1_000_000_000
    return f"{val_b:>10.2f}{suffix}"


async def main():
    print("="*80)
    print("TUPRS CYCLICAL DCF — Faz 2.1.3")
    print("="*80)
    print("BIST ilk uçtan uca Damodaran valuation")
    print("Motor: cyclical_dcf.py (Toyota 2009 modeli)")
    print("="*80)

    # ========================================================================
    # STEP 1: Fetch & Map
    # ========================================================================
    print("\n[STEP 1] Data Pipeline (Fetch + Map)")
    print("-"*80)

    statements = await fetch_yearly(
        ticker="TUPRS",
        years=[2024, 2023, 2022, 2021],
    )
    inputs = map_to_damodaran_inputs(statements)

    print(f"  Ticker:         {inputs.ticker}")
    print(f"  Currency:       {inputs.currency}")
    print(f"  Items found:    {inputs.items_found}/12")
    print(f"  Periods:        {inputs.period_labels}")

    # ========================================================================
    # STEP 2: Cyclical Inputs Preparation
    # ========================================================================
    print("\n[STEP 2] Cyclical Normalization Inputs")
    print("-"*80)

    # Latest revenue (2024 — cyclical normalize için bu kullanılır)
    current_revenue = inputs.revenue[0]
    if current_revenue is None:
        print("  ✗ Revenue not found, abort")
        return

    # Historical avg margin (4-yıl simple average)
    margins = [m for m in inputs.operating_margin if m is not None]
    if not margins:
        print("  ✗ Operating margin not computable, abort")
        return

    avg_margin = sum(margins) / len(margins)

    # 2021 outlier diagnostic
    margins_excl_2021 = [m for m in inputs.operating_margin[:-1] if m is not None]
    avg_margin_excl_2021 = (
        sum(margins_excl_2021) / len(margins_excl_2021)
        if margins_excl_2021 else None
    )

    print(f"  Current revenue (2024):     {fmt_billions(current_revenue)} TL")
    print(f"  Operating margins (4Y):")
    for year, m in zip(inputs.period_labels, inputs.operating_margin):
        m_str = f"{float(m)*100:.2f}%" if m is not None else "null"
        print(f"    {year}: {m_str}")
    print(f"  Average margin (4Y):        {float(avg_margin)*100:.2f}%")
    print(f"  Average margin (excl 2021): {float(avg_margin_excl_2021)*100:.2f}%" if avg_margin_excl_2021 else "    (insufficient data)")

    # Karar: 2021'i dahil et (Damodaran historical avg konsepti)
    # NOT: Ideal 10-15 yıl, sadece 4 yıl var. Bu pilot.
    selected_avg_margin = avg_margin
    print(f"\n  → Seçilen normalize margin: {float(selected_avg_margin)*100:.2f}% (4Y avg, 2021 dahil)")
    print(f"  NOT: Damodaran ideal 10-15Y. Pilot için 4Y kullanılıyor.")

    # ========================================================================
    # STEP 3: Damodaran TR Parameters (Faz 0 DB'den)
    # ========================================================================
    print("\n[STEP 3] Damodaran Parameters (Türkiye, current)")
    print("-"*80)

    # DB'deki güncel parametreler (manuel — gelecekte DB query'lenecek)
    rf_usd = 0.0397           # Rf USD (Damodaran fetcher)
    mature_erp = 0.0444       # Mature market ERP
    turkey_crp = 0.0601       # Turkey country risk

    # Cost of Equity (Türkiye exposure %100, λ=1)
    cost_of_equity = rf_usd + 1.0 * mature_erp + 1.0 * turkey_crp

    # WACC simplified (TUPRS for now, debt ratio approximate)
    # Total debt / (debt + equity) ≈ 24.85B / (24.85B + 374.68B) ≈ 6.2%
    debt_ratio = float(inputs.total_debt[0]) / (float(inputs.total_debt[0]) + float(inputs.total_equity[0]))

    # Cost of Debt (TUPRS rated BB-ish, Damodaran spread ≈ 3%)
    pretax_cost_of_debt = rf_usd + 0.03  # ≈ 6.97%
    statutory_tax = 0.25  # Türkiye corporate tax
    after_tax_kd = pretax_cost_of_debt * (1 - statutory_tax)

    wacc = (1 - debt_ratio) * cost_of_equity + debt_ratio * after_tax_kd

    print(f"  Risk-free (USD):           {rf_usd*100:.2f}%")
    print(f"  Mature ERP:                {mature_erp*100:.2f}%")
    print(f"  Turkey CRP:                {turkey_crp*100:.2f}%")
    print(f"  Cost of Equity:            {cost_of_equity*100:.2f}%")
    print(f"  Debt ratio (current):      {debt_ratio*100:.2f}%")
    print(f"  Pretax Cost of Debt:       {pretax_cost_of_debt*100:.2f}%")
    print(f"  After-tax Kd:              {after_tax_kd*100:.2f}%")
    print(f"  WACC:                      {wacc*100:.2f}%")

    # NOT: Bu hesaplama USD-bazlı — TUPRS data TL'de
    # Damodaran USD-only DCF → TL data USD'ye çevrilmeli
    # Pilot için: TL'de hesapla, USD conversion ileri faz
    print(f"\n  ⚠ DİKKAT: WACC USD-bazlı, TUPRS data TL'de.")
    print(f"  Pilot için: TL data + USD WACC hibrit yaklaşım.")
    print(f"  Düzeltilmesi: Faz 2.1.4'te USD converter modülü.")

    # ========================================================================
    # STEP 4: Stable Growth Assumptions
    # ========================================================================
    print("\n[STEP 4] Stable Growth Assumptions")
    print("-"*80)

    stable_growth = 0.03  # %3 USD-terms long-run growth
    roc = wacc  # Mature firm assumption (no excess return)
    reinvestment_rate = stable_growth / roc if roc > 0 else 0

    print(f"  Stable growth (USD):       {stable_growth*100:.2f}%")
    print(f"  ROC (= WACC, mature):      {roc*100:.2f}%")
    print(f"  Reinvestment rate (g/ROC): {reinvestment_rate*100:.2f}%")

    # ========================================================================
    # STEP 5: Cyclical DCF Execute
    # ========================================================================
    print("\n[STEP 5] Cyclical DCF Execute")
    print("-"*80)

    # Inputs (Decimal → float convert for cyclical_dcf)
    revenue_float = float(current_revenue)
    margin_float = float(selected_avg_margin)

    cash_float = float(inputs.cash[0]) if inputs.cash[0] else 0
    debt_float = float(inputs.total_debt[0]) if inputs.total_debt[0] else 0
    equity_float = float(inputs.total_equity[0]) if inputs.total_equity[0] else 0

    # Non-operating + minority varsayımları (yok TUPRS'de)
    non_op_assets = 0.0
    minority_interests = 0.0

    # Shares outstanding — TUPRS için sabit (gerçek: ~2.5 milyar pay)
    # NOT: Bu Faz 2.1.4'te isyatirim'den çekilecek
    tuprs_shares_outstanding = 2_500_000_000  # 2.5 milyar pay (yaklaşık)

    print(f"  Inputs:")
    print(f"    Current revenue:     {fmt_billions(current_revenue)} TL")
    print(f"    Normalized margin:   {margin_float*100:.2f}%")
    print(f"    WACC:                {wacc*100:.2f}%")
    print(f"    Stable growth:       {stable_growth*100:.2f}%")
    print(f"    Tax rate:            {statutory_tax*100:.0f}%")
    print(f"    Reinvestment rate:   {reinvestment_rate*100:.2f}%")
    print(f"    Cash:                {fmt_billions(Decimal(cash_float))} TL")
    print(f"    Total Debt:          {fmt_billions(Decimal(debt_float))} TL")
    print(f"    Shares outstanding:  {tuprs_shares_outstanding/1_000_000:.0f}M (placeholder)")

    try:
        result = cyclical_dcf_valuation(
            current_revenues=revenue_float,
            historical_avg_margin=margin_float,
            growth_rate=stable_growth,
            tax_rate=statutory_tax,
            reinvestment_rate=reinvestment_rate,
            wacc=wacc,
            cash=cash_float,
            non_operating_assets=non_op_assets,
            debt=debt_float,
            minority_interests=minority_interests,
            shares_outstanding=tuprs_shares_outstanding,
            options_value=0.0,
            current_op_margin=float(inputs.operating_margin[0]) if inputs.operating_margin[0] else None,
        )

        print("\n[RESULTS]")
        print(f"  Normalized OI:           {fmt_billions(Decimal(result.normalization.normalized_op_income))} TL")
        print(f"  Operating Assets:        {fmt_billions(Decimal(result.operating_value.operating_assets_value))} TL")
        print(f"\n  Equity Bridge:")
        print(f"    Operating:             {fmt_billions(Decimal(result.equity_bridge.operating_assets))} TL")
        print(f"    + Cash:                {fmt_billions(Decimal(result.equity_bridge.cash))} TL")
        print(f"    + Non-op:              {fmt_billions(Decimal(result.equity_bridge.non_operating_assets))} TL")
        print(f"    - Debt:                {fmt_billions(Decimal(-result.equity_bridge.debt))} TL")
        print(f"    - Minority:            {fmt_billions(Decimal(-result.equity_bridge.minority_interests))} TL")
        print(f"    = Equity Value:        {fmt_billions(Decimal(result.equity_bridge.equity_value))} TL")

        value_per_share_tl = result.value_per_share

        print(f"\n  Shares Outstanding:      {result.shares_outstanding/1_000_000:.0f}M (placeholder)")
        print(f"  Value per Share:         {value_per_share_tl:.2f} TL")

        print(f"\n  Market Price (Ekim 2024):  ~150-180 TL (placeholder)")
        print(f"  ⚠ NOT: Real market price comparison ileri faz.")

        print("\n" + "="*80)
        print("✓✓✓ TUPRS CYCLICAL DCF EXECUTE PASS")
        print("BIST İLK UÇTAN UCA DAMODARAN VALUATION TAMAMLANDI")
        print("="*80)

    except Exception as e:
        print(f"\n  ✗ DCF FAILED: {type(e).__name__}: {e}")
        raise

    # ========================================================================
    # FAZ 2.1.3 SCOPE LIMITS (dökümante)
    # ========================================================================
    print("\n[SCOPE LIMITS — FAZ 2.1.4'TE DÜZELTILECEK]")
    print("-"*80)
    print("""
1. USD CONVERSION:
   Şu an TL data + USD WACC hibrit (yanıltıcı).
   USD converter modülü gerek (TCMB FX rate).

2. SHARES OUTSTANDING:
   Placeholder 2.5B kullanıldı. Gerçek isyatirim'den çekilmeli
   (KAP genel bilgi sayfası veya alternative endpoint).

3. CAPEX:
   Faz 2.1.2 Adım B'de raw aggregation (192B too high).
   Net CapEx = ΔPP&E + Depreciation pattern uygulanmalı.

4. HISTORICAL DEPTH:
   Sadece 4 yıl margin avg. Damodaran ideal 10-15Y.
   Multiple parallel call ile 8+ yıl desteği eklenecek.

5. MARKET PRICE:
   Real market price comparison yok (cheap/fair/expensive eşiği).
   Faz 2.2 sonrası ekleme.

6. LIFECYCLE CLASSIFICATION:
   Cyclical assumption manual. Faz 2.2'de classifier
   her ticker için otomatik karar verecek (Cyclical/Mature/Growth/etc.).
""")


if __name__ == "__main__":
    asyncio.run(main())
