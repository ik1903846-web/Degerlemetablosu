#!/usr/bin/env python3
"""Faz B2 Phase 1 Adim 6: Full universe regen (unbuffered progress)."""
import sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from apps.api.orchestrator_v4 import (
    run_pipeline_v4, save_v4_batch_json, _Caches, assemble_and_value
)

print("Adim 6 regen baslıyor (unbuffered)", flush=True)
print(f"  cwd={Path.cwd()}", flush=True)
print(f"  repo={REPO}", flush=True)
print()

caches = _Caches()
universe = [r.ticker for r in caches.float_snap.records]
print(f"  universe count: {len(universe)}", flush=True)
print(f"  fetch_yfinance_live=False (cache hit)", flush=True)
print(f"  cross_holdings entegre (Adim 4 + 31)", flush=True)
print()

start = time.time()
results = []
for i, t in enumerate(universe, 1):
    t_start = time.time()
    td = assemble_and_value(t, caches=caches, fetch_yfinance_live=False)
    t_dur = time.time() - t_start
    results.append(td)
    if i % 25 == 0 or t_dur > 5.0:
        n_dcf = sum(1 for r in results if r.intrinsic_per_share_tl is not None)
        ch_dolu = sum(1 for r in results if r.cross_holdings_added_tl)
        elapsed = time.time() - start
        print(
            f"  [{i:3d}/{len(universe)}] last={t} ({t_dur:.2f}s) "
            f"dcf={n_dcf} ch={ch_dolu} elapsed={elapsed:.1f}s",
            flush=True,
        )

duration = time.time() - start
print()
print(f"Regen tamamlandi: {duration:.1f} sn ({duration/60:.1f} dk)", flush=True)
print(f"Ticker count: {len(results)}", flush=True)

output_path = save_v4_batch_json(results)
print(f"Batch JSON yazildi: {output_path}", flush=True)

ch_populated = sum(1 for r in results if r.cross_holdings_added_tl)
ch_value_dolu = sum(1 for r in results if r.cross_holdings_value_tl)
intrinsic_dolu = sum(1 for r in results if r.intrinsic_per_share_tl is not None)
n_complete = sum(1 for r in results if r.is_complete)

print(f"  Complete:                {n_complete}/{len(results)}", flush=True)
print(f"  DCF intrinsic dolu:      {intrinsic_dolu}/{len(results)}", flush=True)
print(f"  CH-value populate (>0):  {ch_value_dolu}", flush=True)
print(f"  CH-added populate (>0):  {ch_populated}", flush=True)
