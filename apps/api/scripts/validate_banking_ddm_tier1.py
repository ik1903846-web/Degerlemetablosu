#!/usr/bin/env python
"""Banking DDM Tier 1 (AKBNK/GARAN/YKBNK/ISCTR/HALKB) USD validation.
Damodaran-sadik banking valuation Turkey context'inde 5 banka toplu test.
Read-only validation. Market prices turkey_v4_batch.json'dan."""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.banking_ddm import dcf_ddm
from data_layer.banking_data import get_banking_data


# Damodaran USD parameters (parameters.json 2026-05-09)
RF_USD = 0.0397
MATURE_ERP = 0.0423
CRP_TR = 0.0466
FX_RATE = 40.0  # TL/USD May 2026

BANKING_SECTOR_BETA = 0.85
BANKING_STABLE_ROE = 0.14
BANKING_STABLE_G_USD = 0.025

TIER1 = ['AKBNK', 'GARAN', 'YKBNK', 'ISCTR', 'HALKB']


def get_market_price(ticker: str) -> float:
    batch_path = Path(__file__).parent.parent / 'outputs' / 'turkey_v4_batch.json'
    with open(batch_path, encoding='utf-8') as f:
        data = json.load(f)
    found = next((x for x in data['tickers'] if x['ticker'] == ticker), None)
    return found.get('current_price_tl') if found else None


def latest_year(config):
    if not config or not config.yearly:
        return None
    return max(config.yearly, key=lambda d: d.year)


def main():
    print("=" * 100)
    print("BANKING DDM TIER 1 — USD VALIDATION (Damodaran-sadik)")
    print("=" * 100)
    print(f"Damodaran params: Rf_USD={RF_USD*100:.2f}%, ERP={MATURE_ERP*100:.2f}%, CRP_TR={CRP_TR*100:.2f}%")
    print(f"Banking sector:   beta={BANKING_SECTOR_BETA}, stable_ROE={BANKING_STABLE_ROE*100:.0f}%, stable_g_USD={BANKING_STABLE_G_USD*100:.1f}%")
    print(f"FX rate:          {FX_RATE} TL/USD")
    print()

    coe_high_usd = RF_USD + BANKING_SECTOR_BETA * (MATURE_ERP + CRP_TR)
    coe_stable_usd = RF_USD + 0.80 * (MATURE_ERP + CRP_TR * 0.5)
    stable_payout = 1 - BANKING_STABLE_G_USD / BANKING_STABLE_ROE

    print(f"CoE high USD:     {coe_high_usd*100:.2f}%")
    print(f"CoE stable USD:   {coe_stable_usd*100:.2f}%")
    print(f"Stable payout:    {stable_payout*100:.1f}%")
    print()

    results = []

    for ticker in TIER1:
        config = get_banking_data(ticker)
        if config is None:
            print(f"{ticker}: banking_data MISSING")
            continue
        bd = latest_year(config)
        if bd is None:
            print(f"{ticker}: no yearly data")
            continue

        # TL -> USD convert
        eps_usd = bd.eps_tl / FX_RATE
        roe = bd.roe_pct / 100
        payout = bd.payout_pct / 100
        retention = 1 - payout
        high_growth = roe * retention

        market_price = get_market_price(ticker)

        try:
            result = dcf_ddm(
                starting_eps=eps_usd,
                high_growth_rate=high_growth,
                high_growth_payout=payout,
                high_growth_coe=coe_high_usd,
                high_growth_duration=5,
                stable_growth=BANKING_STABLE_G_USD,
                stable_payout=stable_payout,
                stable_coe=coe_stable_usd,
            )
            intrinsic_usd = result.value_per_share
            intrinsic_tl = intrinsic_usd * FX_RATE
            upside = ((intrinsic_tl - market_price) / market_price * 100) if market_price else None

            results.append({
                'ticker': ticker,
                'year': bd.year,
                'eps_tl': bd.eps_tl,
                'eps_usd': eps_usd,
                'roe': roe,
                'payout': payout,
                'high_growth': high_growth,
                'intrinsic_usd': intrinsic_usd,
                'intrinsic_tl': intrinsic_tl,
                'market_price': market_price,
                'upside': upside,
                'confidence': bd.confidence,
            })
        except Exception as e:
            print(f"{ticker} ERROR: {e}")

    # Output table
    print()
    hdr = f"{'Ticker':<7} {'Year':<5} {'EPS_TL':<7} {'ROE%':<6} {'Payout%':<8} {'g%':<6} {'Intr.USD':<10} {'Intr.TL':<10} {'Market':<8} {'Upside':<10} {'Conf'}"
    print(hdr)
    print("-" * 100)

    for r in results:
        upside_str = f"{r['upside']:+.1f}%" if r['upside'] is not None else "n/a"
        market_str = f"{r['market_price']:.2f}" if r['market_price'] else "n/a"
        print(
            f"{r['ticker']:<7} {r['year']:<5} {r['eps_tl']:<7.2f} {r['roe']*100:<6.1f} "
            f"{r['payout']*100:<8.1f} {r['high_growth']*100:<6.1f} "
            f"${r['intrinsic_usd']:<9.2f} {r['intrinsic_tl']:<10.1f} {market_str:<8} {upside_str:<10} {r['confidence']}"
        )

    # Sanity
    print()
    print("=" * 100)
    print("SANITY CHECK")
    print("=" * 100)

    reasonable = sum(1 for r in results if r['upside'] is not None and -20 < r['upside'] < 250)
    print(f"Reasonable range (-20%% < upside < +250%%): {reasonable}/{len(results)}")

    if all(r['upside'] is not None and r['upside'] > 0 for r in results):
        print("PATTERN: All Tier 1 banks UNDERVALUED — Damodaran 'TR banking ucuz' destekleniyor")
    elif any(r['upside'] is not None and r['upside'] < 0 for r in results):
        overvalued = [r['ticker'] for r in results if r['upside'] is not None and r['upside'] < 0]
        print(f"PATTERN: Bazi banka overvalued: {overvalued}")
    else:
        print("PATTERN: mixed")

    print()
    print("Damodaran banking PE/PBV cross-check:")
    print(f"  {'Ticker':<7} {'PE current':<11} {'PE implied':<12} {'PBV current'}")
    print("-" * 60)
    batch_path = Path(__file__).parent.parent / 'outputs' / 'turkey_v4_batch.json'
    with open(batch_path, encoding='utf-8') as f:
        batch = json.load(f)
    for r in results:
        pe_current = r['market_price'] / r['eps_tl'] if r['market_price'] and r['eps_tl'] else None
        pe_implied = r['intrinsic_tl'] / r['eps_tl'] if r['eps_tl'] else None
        # PBV from batch (book_equity / shares = BVPS, price / BVPS = PBV)
        cfg = get_banking_data(r['ticker'])
        bd_2024 = latest_year(cfg)
        bvps = (bd_2024.book_equity_tl * 1e6) / bd_2024.shares_outstanding if bd_2024.shares_outstanding else None
        pbv = r['market_price'] / bvps if bvps else None
        print(
            f"  {r['ticker']:<7} {pe_current:<11.2f} {pe_implied:<12.2f} {pbv if pbv else 'n/a':<12}"
        )

    print()
    if reasonable == 5:
        print("VERDICT: 5/5 reasonable -> Phase 4b implement SAFE")
    elif reasonable >= 3:
        print(f"VERDICT: {reasonable}/5 reasonable -> parameter tune brief gerek")
    else:
        print(f"VERDICT: {reasonable}/5 reasonable -> root cause analiz gerek")


if __name__ == "__main__":
    main()
