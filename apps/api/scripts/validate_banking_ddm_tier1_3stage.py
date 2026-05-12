#!/usr/bin/env python
"""Banking DDM Tier 1 — 3-stage USD validation (transition fade)
GARAN/HALKB outlier auto-correct hedefi.
2-stage tier1 script kardesi (validate_banking_ddm_tier1.py)."""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.banking_ddm import dcf_ddm, dcf_ddm_3stage
from data_layer.banking_data import get_banking_data


RF_USD = 0.0397
MATURE_ERP = 0.0423
CRP_TR = 0.0466
FX_RATE = 40.0

BETA = 0.85
STABLE_ROE = 0.14
STABLE_G_USD = 0.025

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
    print("=" * 110)
    print("BANKING DDM TIER 1 — 3-STAGE USD VALIDATION (transition fade)")
    print("=" * 110)

    coe_high = RF_USD + BETA * (MATURE_ERP + CRP_TR)
    coe_stable = RF_USD + 0.80 * (MATURE_ERP + CRP_TR * 0.5)
    stable_payout = 1 - STABLE_G_USD / STABLE_ROE

    print(f"\nDamodaran params: Rf={RF_USD*100:.2f}%, ERP={MATURE_ERP*100:.2f}%, CRP_TR={CRP_TR*100:.2f}%")
    print(f"CoE high USD     : {coe_high*100:.2f}%  -> stable {coe_stable*100:.2f}%")
    print(f"Stable g (USD)   : {STABLE_G_USD*100:.1f}% , Stable ROE = {STABLE_ROE*100:.0f}%, Stable payout = {stable_payout*100:.1f}%")
    print(f"FX rate          : {FX_RATE} TL/USD")
    print(f"Transition fade  : 5y (Y6-10 linear taper growth + payout RISE + CoE)")
    print()

    results = []

    for ticker in TIER1:
        cfg = get_banking_data(ticker)
        if cfg is None:
            print(f"{ticker}: NO CONFIG")
            continue
        bd = latest_year(cfg)
        if bd is None:
            continue

        eps_usd = bd.eps_tl / FX_RATE
        roe = bd.roe_pct / 100
        payout = bd.payout_pct / 100
        retention = 1 - payout
        high_growth = roe * retention

        market_price = get_market_price(ticker)

        # 2-stage (mevcut)
        r2 = dcf_ddm(
            starting_eps=eps_usd,
            high_growth_rate=high_growth,
            high_growth_payout=payout,
            high_growth_coe=coe_high,
            high_growth_duration=5,
            stable_growth=STABLE_G_USD,
            stable_payout=stable_payout,
            stable_coe=coe_stable,
        )

        # 3-stage (yeni, transition Y6-10)
        r3 = dcf_ddm_3stage(
            starting_eps=eps_usd,
            high_growth_rate=high_growth,
            high_growth_payout=payout,
            high_growth_coe=coe_high,
            high_growth_duration=5,
            transition_period_years=5,
            stable_growth=STABLE_G_USD,
            stable_payout=stable_payout,
            stable_coe=coe_stable,
        )

        intr_tl_2 = r2.value_per_share * FX_RATE
        intr_tl_3 = r3.value_per_share * FX_RATE

        ups_2 = ((intr_tl_2 - market_price) / market_price * 100) if market_price else None
        ups_3 = ((intr_tl_3 - market_price) / market_price * 100) if market_price else None

        results.append({
            'ticker': ticker, 'eps_tl': bd.eps_tl, 'roe': roe, 'payout': payout, 'g': high_growth,
            'market': market_price,
            'intr_tl_2': intr_tl_2, 'intr_tl_3': intr_tl_3,
            'ups_2': ups_2, 'ups_3': ups_3,
        })

    print(f"{'Ticker':<7} {'ROE%':<6} {'Pay%':<6} {'g%':<6} {'Market':<8} {'2-stage':<10} {'2-ups%':<9} {'3-stage':<10} {'3-ups%':<9} {'Delta'}")
    print("-" * 105)
    for r in results:
        ups2 = f"{r['ups_2']:+.1f}%" if r['ups_2'] is not None else "n/a"
        ups3 = f"{r['ups_3']:+.1f}%" if r['ups_3'] is not None else "n/a"
        delta = (r['ups_3'] - r['ups_2']) if (r['ups_2'] is not None and r['ups_3'] is not None) else None
        delta_str = f"{delta:+.1f}pp" if delta is not None else "n/a"
        print(
            f"{r['ticker']:<7} {r['roe']*100:<6.1f} {r['payout']*100:<6.1f} {r['g']*100:<6.1f} "
            f"{r['market']:<8.2f} {r['intr_tl_2']:<10.1f} {ups2:<9} {r['intr_tl_3']:<10.1f} {ups3:<9} {delta_str}"
        )

    print()
    print("=" * 110)
    print("SANITY CHECK (3-stage)")
    print("=" * 110)
    reasonable = sum(1 for r in results if r['ups_3'] is not None and -20 < r['ups_3'] < 250)
    print(f"3-stage reasonable (-20% < upside < +250%): {reasonable}/{len(results)}")

    # Per-bank verdict
    print()
    for r in results:
        if r['ups_3'] is None:
            continue
        if -20 < r['ups_3'] < 250:
            tag = "REASONABLE"
        else:
            tag = "OUTLIER"
        print(f"  {r['ticker']:<7} 3-stage upside {r['ups_3']:+.1f}% — {tag}")

    print()
    if reasonable == 5:
        print("VERDICT: 5/5 reasonable -> Phase 4b implement SAFE (3-stage)")
    elif reasonable >= 4:
        print(f"VERDICT: {reasonable}/5 reasonable -> 1 outlier flag ile devam edilebilir")
    elif reasonable >= 3:
        print(f"VERDICT: {reasonable}/5 reasonable -> outlier'lar parameter tune gerek")
    else:
        print(f"VERDICT: {reasonable}/5 reasonable -> root cause analiz gerek")


if __name__ == "__main__":
    main()
