#!/usr/bin/env python
"""ABN Amro DDM 3-stage re-test — Damodaran replication ile karsilastirma.
Mevcut 2-stage dcf_ddm() vs yeni dcf_ddm_3stage() output kiyasi.
Damodaran reference: 30.87 EUR (finsvc.pdf)."""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.banking_ddm import dcf_ddm, dcf_ddm_3stage


def main():
    case_path = Path(__file__).parent.parent / 'validation_cases' / 'abn_amro_ddm.json'
    with open(case_path, encoding='utf-8') as f:
        abn = json.load(f)

    print("=" * 78)
    print("ABN AMRO DDM — 2-STAGE vs 3-STAGE Karsilastirma")
    print("=" * 78)

    starting_eps = abn['starting_metrics']['eps_eur']
    hg = abn['high_growth_phase']
    sp = abn['stable_growth_phase']
    expected = abn['expected']['value_per_share']

    print(f"\nDamodaran reference (finsvc.pdf): EUR {expected:.2f}")
    print(f"Starting EPS                     : EUR {starting_eps:.2f}")
    print(f"\nHigh growth phase (Y1-5):")
    print(f"  growth   = {hg['growth_rate']*100:.2f}%")
    print(f"  payout   = {hg['payout_ratio']*100:.1f}%")
    print(f"  CoE      = {hg['cost_of_equity']*100:.2f}%")
    print(f"\nStable phase (Y11+):")
    print(f"  growth   = {sp['growth_rate']*100:.2f}%")
    print(f"  payout   = {sp['payout_ratio']*100:.2f}%")
    print(f"  CoE      = {sp['cost_of_equity']*100:.2f}%")

    # ============================
    # 2-stage (mevcut, geriye uyumlu)
    # ============================
    r2 = dcf_ddm(
        starting_eps=starting_eps,
        high_growth_rate=hg['growth_rate'],
        high_growth_payout=hg['payout_ratio'],
        high_growth_coe=hg['cost_of_equity'],
        high_growth_duration=hg['duration_years'],
        stable_growth=sp['growth_rate'],
        stable_payout=sp['payout_ratio'],
        stable_coe=sp['cost_of_equity'],
    )

    print(f"\n{'-'*78}")
    print(f"[2-STAGE — mevcut dcf_ddm()]")
    print(f"  PV high-growth DPS : EUR {r2.pv_high_growth_dps:.2f}")
    print(f"  PV terminal        : EUR {r2.pv_terminal_value:.2f}")
    print(f"  Terminal value     : EUR {r2.terminal_value:.2f}")
    print(f"  Value per share    : EUR {r2.value_per_share:.2f}")
    drift_2 = (r2.value_per_share - expected) / expected * 100
    print(f"  Drift vs Damodaran : {drift_2:+.2f}%")

    # ============================
    # 3-stage (yeni)
    # ============================
    r3 = dcf_ddm_3stage(
        starting_eps=starting_eps,
        high_growth_rate=hg['growth_rate'],
        high_growth_payout=hg['payout_ratio'],
        high_growth_coe=hg['cost_of_equity'],
        high_growth_duration=hg['duration_years'],
        transition_period_years=5,
        stable_growth=sp['growth_rate'],
        stable_payout=sp['payout_ratio'],
        stable_coe=sp['cost_of_equity'],
    )

    print(f"\n{'-'*78}")
    print(f"[3-STAGE — yeni dcf_ddm_3stage(), transition=5y]")
    print(f"  PV high-growth DPS : EUR {r3.pv_high_growth_dps:.2f}")
    print(f"  PV transition DPS  : EUR {r3.pv_transition_dps:.2f}")
    print(f"  PV terminal        : EUR {r3.pv_terminal_value:.2f}")
    print(f"  Terminal value     : EUR {r3.terminal_value:.2f}")
    print(f"  EPS terminal phase : EUR {r3.eps_terminal_phase:.2f}")
    print(f"  Value per share    : EUR {r3.value_per_share:.2f}")
    drift_3 = (r3.value_per_share - expected) / expected * 100
    print(f"  Drift vs Damodaran : {drift_3:+.2f}%")

    print(f"\n  Yearly projection (transition smooth):")
    print(f"  {'Year':<5} {'Phase':<12} {'g%':<6} {'pay%':<6} {'CoE%':<6} {'EPS':<7} {'DPS':<6}")
    for p in r3.yearly_projections:
        print(f"  {p.year:<5} {p.phase:<12} {p.growth_rate*100:<6.2f} {p.payout_ratio*100:<6.2f} {p.cost_of_equity*100:<6.2f} {p.eps:<7.3f} {p.dps:<6.3f}")

    # ============================
    # Karsilastirma
    # ============================
    print(f"\n{'=' * 78}")
    print(f"KARSILASTIRMA")
    print(f"{'=' * 78}")
    print(f"  Damodaran            : EUR {expected:.2f}")
    print(f"  2-stage              : EUR {r2.value_per_share:.2f}  ({drift_2:+.2f}%)")
    print(f"  3-stage (tr=5)       : EUR {r3.value_per_share:.2f}  ({drift_3:+.2f}%)")

    if abs(drift_3) < abs(drift_2):
        print(f"  3-stage daha YAKIN Damodaran reference'a (transition smooth etkisi)")
    elif abs(drift_3) > abs(drift_2):
        print(f"  3-stage daha UZAK — ABN Amro pattern saf 2-stage idi (transition kuvvetli)")
    else:
        print(f"  Aritmetik denk")

    tolerance = abn['expected']['tolerance_pct']
    lower = expected * (1 - tolerance)
    upper = expected * (1 + tolerance)
    print(f"\n  Pass range (+-{tolerance*100:.0f}%) : EUR {lower:.2f} - EUR {upper:.2f}")
    print(f"  2-stage PASS: {lower <= r2.value_per_share <= upper}")
    print(f"  3-stage PASS: {lower <= r3.value_per_share <= upper}")


if __name__ == "__main__":
    main()
