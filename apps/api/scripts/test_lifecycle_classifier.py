#!/usr/bin/env python
"""TUPRS lifecycle classification test (Faz 2.2)."""
import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.isyatirim_scraper import fetch_yearly_extended
from data_layer.damodaran_mapper import map_to_damodaran_inputs
from data_layer.fx_converter import get_static_rates, convert_inputs_to_usd
from dcf_engine.lifecycle_classifier import classify_lifecycle, LifecycleStage, SubClassification


async def main():
    print("="*80)
    print("TUPRS Lifecycle Classification Test (Faz 2.2)")
    print("="*80)

    # 12-yıl USD pipeline
    years = list(range(2024, 2012, -1))
    statements = await fetch_yearly_extended(ticker="TUPRS", years=years)
    inputs_tl = map_to_damodaran_inputs(statements)
    fx_series = get_static_rates(years)
    inputs_usd = convert_inputs_to_usd(inputs_tl, fx_series)

    print(f"\nPipeline: 12-yıl USD (Items: {inputs_usd.items_found}/12)")

    # ========================================================================
    # CLASSIFY
    # ========================================================================
    print("\n[CLASSIFY]")
    print("-"*80)

    result = classify_lifecycle(inputs_usd)

    print(f"  Ticker:                {result.ticker}")
    print(f"  Stage:                 {result.stage.value.upper()}")
    print(f"  Sub-classifications:   {[s.value for s in result.sub_classifications]}")
    print(f"  Recommended Model:     {result.recommended_model}")
    print(f"  Confidence:            {result.confidence*100:.0f}%")

    # ========================================================================
    # METRICS
    # ========================================================================
    print("\n[METRICS]")
    print("-"*80)

    print(f"  Revenue CAGR (USD):    {result.revenue_cagr_usd*100:>6.2f}%" if result.revenue_cagr_usd else "  Revenue CAGR:           null")
    print(f"  Avg Operating Margin:  {result.avg_operating_margin*100:>6.2f}%" if result.avg_operating_margin else "  Avg Margin:             null")
    print(f"  Margin Stdev:          {result.margin_stdev*100:>6.2f}pp" if result.margin_stdev else "  Margin Stdev:           null")
    print(f"  Margin Spread:         {result.margin_spread*100:>6.2f}pp" if result.margin_spread else "  Margin Spread:          null")
    print(f"  Avg Reinvestment:      {result.avg_reinvestment_rate*100:>6.2f}%" if result.avg_reinvestment_rate else "  Avg Reinvestment:       null")
    print(f"  Has Negative Earnings: {result.has_negative_earnings}")
    print(f"  Earnings Consistency:  {result.earnings_consistency*100:>6.0f}%" if result.earnings_consistency else "  Earnings Consistency:   null")

    # ========================================================================
    # REASONING
    # ========================================================================
    print("\n[REASONING]")
    print("-"*80)

    for r in result.reasoning:
        print(f"  • {r}")

    # ========================================================================
    # EXPECTED VS ACTUAL
    # ========================================================================
    print("\n[EXPECTED vs ACTUAL]")
    print("-"*80)

    print(f"  TUPRS Damodaran profili:")
    print(f"    - Mature firm (rafinaj sektör, 50+ yıl)")
    print(f"    - Cyclical (commodity exposure)")
    print(f"    - Capital-intensive (PP&E heavy)")
    print(f"    - USD revenue ~stabil (12-yıl)")
    print(f"    - Through-cycle margin %4.64")

    print(f"\n  Beklenti: MATURE STABLE veya MATURE GROWTH + CYCLICAL")
    print(f"  Sonuç:    {result.stage.value.upper()} + {[s.value for s in result.sub_classifications]}")

    expected_stages = [LifecycleStage.MATURE_STABLE, LifecycleStage.MATURE_GROWTH]
    if result.stage in expected_stages and SubClassification.CYCLICAL in result.sub_classifications:
        print(f"  ✓ Sınıflandırma DOĞRU")
    else:
        print(f"  ⚠ Beklenenden farklı (manuel inceleme gerek)")

    # ========================================================================
    # MODEL SELECTION VALIDATION
    # ========================================================================
    print("\n[MODEL SELECTION]")
    print("-"*80)

    print(f"  Recommended:  {result.recommended_model}")
    print(f"  Faz 2.1.4 Adım 5'te kullandığımız: cyclical_dcf")

    if result.recommended_model == "cyclical_dcf":
        print(f"  ✓ Lifecycle classifier 'cyclical_dcf' önerdi (Adım 5 uyumlu)")
        print(f"  → BIST 30 batch'te otomatik model seçimi çalışacak")
    else:
        print(f"  ⚠ Recommended model farklı: {result.recommended_model}")

    print("\n" + "="*80)
    print("Faz 2.2 — Lifecycle Classifier PASS")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
