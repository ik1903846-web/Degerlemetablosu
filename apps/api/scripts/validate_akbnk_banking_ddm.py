#!/usr/bin/env python
"""AKBNK 2024 Banking DDM Validation — Engine A banking_ddm.py BIST Turkey context.
TL native + USD spec mode iki context, fx_converter STATIC_YEAR_END_RATES 2024=35.37.
Read-only test, production code touch yok."""

import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.banking_ddm import dcf_ddm


def main():
    print("=" * 70)
    print("AKBNK 2024 — Banking DDM Validation (Damodaran-style)")
    print("=" * 70)

    # AKBNK 2024 inputs (banking_data.py CONFIRMED)
    eps_2024 = 11.01      # TL
    dps_2024 = 2.20       # TL
    book_equity = 266_300_000_000  # TL
    shares = 5_200_000_000
    roe = 0.215
    payout = 0.20
    beta_unlevered = 0.2495

    retention = 1 - payout
    high_growth = roe * retention  # = 21.5% × 80% = 17.2%

    current_price = 75.35  # TL (KAP/yfinance)

    print(f"\nAKBNK 2024 Inputs:")
    print(f"  EPS:           {eps_2024} TL")
    print(f"  DPS:           {dps_2024} TL")
    print(f"  Book Equity:   {book_equity/1e9:.1f}B TL")
    print(f"  Shares:        {shares/1e9:.2f}B")
    print(f"  ROE:           {roe*100:.1f}%")
    print(f"  Payout:        {payout*100:.0f}%")
    print(f"  Implied growth (ROE x retention): {high_growth*100:.1f}%")
    print(f"  Beta unlevered (bank_money_center): {beta_unlevered}")
    print(f"  Current price: {current_price} TL")

    intrinsic_tl = None
    intrinsic_tl_via_usd = None

    # ============================================
    # MODE 1: TL native context (Turkey)
    # ============================================
    print(f"\n{'-'*70}")
    print(f"MODE 1: TL NATIVE CONTEXT")
    print(f"{'-'*70}")

    rf_tl = 0.35           # 10Y TR bond tahmini (nominal TL, enflasyon dahil)
    mature_erp_tl = 0.045
    crp_tr = 0.06
    beta = 0.85  # relevered (bank ortalama)

    coe_tl_high = rf_tl + beta * (mature_erp_tl + crp_tr)
    print(f"  Rf (TL nominal):        {rf_tl*100:.1f}%")
    print(f"  beta:                   {beta}")
    print(f"  Mature ERP:             {mature_erp_tl*100:.1f}%")
    print(f"  CRP (TR):               {crp_tr*100:.1f}%")
    print(f"  Cost of Equity (high):  {coe_tl_high*100:.2f}%")

    stable_g_tl = 0.10
    stable_roe_tl = 0.14
    stable_payout_tl = 1 - stable_g_tl / stable_roe_tl
    coe_tl_stable = rf_tl + 0.80 * (mature_erp_tl + crp_tr * 0.5)

    print(f"  Stable g (TL):          {stable_g_tl*100:.1f}%")
    print(f"  Stable ROE:             {stable_roe_tl*100:.1f}%")
    print(f"  Stable payout:          {stable_payout_tl*100:.1f}%")
    print(f"  Stable CoE:             {coe_tl_stable*100:.2f}%")

    try:
        result_tl = dcf_ddm(
            starting_eps=eps_2024,
            high_growth_rate=high_growth,
            high_growth_payout=payout,
            high_growth_coe=coe_tl_high,
            high_growth_duration=5,
            stable_growth=stable_g_tl,
            stable_payout=stable_payout_tl,
            stable_coe=coe_tl_stable,
        )
        intrinsic_tl = result_tl.value_per_share
        print(f"\n  Intrinsic (TL DDM):     {intrinsic_tl:.2f} TL")
        print(f"  PV high-growth DPS:     {result_tl.pv_high_growth_dps:.2f}")
        print(f"  PV terminal value:      {result_tl.pv_terminal_value:.2f}")
        print(f"  Terminal value:         {result_tl.terminal_value:.2f}")
        upside = (intrinsic_tl - current_price) / current_price * 100
        print(f"  Upside vs market:       {upside:+.1f}%")
    except Exception as e:
        print(f"  TL DDM ERROR: {e}")
        import traceback
        traceback.print_exc()

    # ============================================
    # MODE 2: USD context
    # ============================================
    print(f"\n{'-'*70}")
    print(f"MODE 2: USD CONTEXT (spec convention)")
    print(f"{'-'*70}")

    # 2026 Mayis ortalama USD/TL ~40 (fx_converter 2024=35.37, 2025=39.50 placeholder)
    fx_rate = 40.0
    eps_usd = eps_2024 / fx_rate
    dps_usd = dps_2024 / fx_rate
    price_usd = current_price / fx_rate

    rf_usd = 0.0397        # parameters.json rf_usd_estimate
    mature_erp = 0.0423    # parameters.json mature_erp
    crp_tr_usd = 0.0466    # parameters.json turkey.crp

    coe_usd_high = rf_usd + beta * (mature_erp + crp_tr_usd)
    print(f"  fx_rate (USD/TL):       {fx_rate}")
    print(f"  EPS (USD):              ${eps_usd:.3f}")
    print(f"  Rf (USD 10Y UST):       {rf_usd*100:.2f}%")
    print(f"  Mature ERP:             {mature_erp*100:.2f}%")
    print(f"  CRP (TR USD):           {crp_tr_usd*100:.2f}%")
    print(f"  Cost of Equity (high):  {coe_usd_high*100:.2f}%")

    stable_g_usd = 0.025
    stable_roe_usd = 0.10
    stable_payout_usd = 1 - stable_g_usd / stable_roe_usd
    coe_usd_stable = rf_usd + 0.80 * (mature_erp + crp_tr_usd * 0.5)

    print(f"  Stable g (USD):         {stable_g_usd*100:.1f}%")
    print(f"  Stable CoE (USD):       {coe_usd_stable*100:.2f}%")

    try:
        result_usd = dcf_ddm(
            starting_eps=eps_usd,
            high_growth_rate=high_growth,  # ROE*retention currency-invariant
            high_growth_payout=payout,
            high_growth_coe=coe_usd_high,
            high_growth_duration=5,
            stable_growth=stable_g_usd,
            stable_payout=stable_payout_usd,
            stable_coe=coe_usd_stable,
        )
        intrinsic_usd = result_usd.value_per_share
        intrinsic_tl_via_usd = intrinsic_usd * fx_rate
        print(f"\n  Intrinsic (USD DDM):    ${intrinsic_usd:.3f}")
        print(f"  Convert TL:             {intrinsic_tl_via_usd:.2f} TL")
        upside = (intrinsic_tl_via_usd - current_price) / current_price * 100
        print(f"  Upside vs market:       {upside:+.1f}%")
    except Exception as e:
        print(f"  USD DDM ERROR: {e}")
        import traceback
        traceback.print_exc()

    # ============================================
    # COMPARISON
    # ============================================
    print(f"\n{'=' * 70}")
    print(f"AKBNK BANKING DDM — TL vs USD KARSILASTIRMA")
    print(f"{'=' * 70}")
    print(f"  Market price:          {current_price:.2f} TL")
    if intrinsic_tl is not None:
        print(f"  TL DDM intrinsic:      {intrinsic_tl:.2f} TL  ({(intrinsic_tl-current_price)/current_price*100:+.1f}%)")
    if intrinsic_tl_via_usd is not None:
        print(f"  USD DDM intrinsic:     {intrinsic_tl_via_usd:.2f} TL  ({(intrinsic_tl_via_usd-current_price)/current_price*100:+.1f}%)")
    if intrinsic_tl and intrinsic_tl_via_usd:
        spread = abs(intrinsic_tl - intrinsic_tl_via_usd) / intrinsic_tl_via_usd * 100
        print(f"  TL vs USD spread:      {spread:.1f}%")
        if spread < 10:
            verdict = "Currency invariant — Phase 4b implement guvenli"
        elif spread < 30:
            verdict = "Currency choice onemli — spec USD takip et"
        else:
            verdict = "Sapma yuksek — parametre tune gerek"
        print(f"  Verdict:               {verdict}")

    print()
    print("Damodaran 'reasonable' AKBNK 2024 PE/PBV cross-check:")
    print(f"  Current PE  = price/EPS = {current_price/eps_2024:.2f}x")
    print(f"  Implied PE (TL DDM)  = {intrinsic_tl/eps_2024:.2f}x" if intrinsic_tl else "")
    print(f"  Implied PE (USD DDM) = {intrinsic_tl_via_usd/eps_2024:.2f}x" if intrinsic_tl_via_usd else "")
    print(f"  Current PBV = price*shares/book_equity = {current_price*shares/book_equity:.2f}x")


if __name__ == "__main__":
    main()
