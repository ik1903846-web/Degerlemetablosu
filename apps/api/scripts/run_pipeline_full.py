#!/usr/bin/env python
"""
Faz 4.18 — Full Pipeline Orchestrator (race-free by design).

Sequential 4-step subprocess wrapper:
  1. test_orchestrator_live.py    — BIST batch (live spot prices + DCF)
  2. run_portfolio_pipeline.py    — 3 risk profile portfolio plan
  3. run_backtest_2021_2026.py    — 20-quarter TL backtest
  4. run_backtest_usd_basis.py    — USD backtest (--tl-results <fresh path>)

File-based handoff: each script writes timestamped output; wrapper auto-detects
fresh file via mtime sort and explicitly passes path to dependent step.

Damodaran Lesson #18 ACTIONABLE EXTEND (META → FIX → AUTOMATION):
- META observation (Faz 7.1): drift gözlem
- Reinforced (Faz 7.2): 3. drift
- ACTIONABLE FIX (Faz 7.3): --tl-results explicit path arg
- AUTOMATION (Faz 4.18): pipeline wrapper sequential + auto-detect ★

Usage:
  python scripts/run_pipeline_full.py            # full 4-step
  python scripts/run_pipeline_full.py --skip-batch  # 3-step (re-run faster)
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ============================================================================
# Configuration
# ============================================================================

API_DIR = Path(__file__).resolve().parent.parent  # apps/api
SCRIPTS_DIR = API_DIR / "scripts"
OUTPUTS_DIR = API_DIR / "outputs"

# Python interpreter — venv tercih, fallback sys.executable
_VENV_PY_WIN = API_DIR / ".venv" / "Scripts" / "python.exe"
PYTHON_EXE = str(_VENV_PY_WIN if _VENV_PY_WIN.exists() else sys.executable)

LOG_DIR = Path("/tmp")
if not LOG_DIR.exists():
    # Windows fallback
    LOG_DIR = API_DIR / "outputs"


# ============================================================================
# Helpers
# ============================================================================

def _log_path(step_name: str, ts: str) -> Path:
    safe = step_name.replace(" ", "_").replace("/", "_")
    return LOG_DIR / f"pipeline_{safe}_{ts}.log"


def find_latest(pattern: str, exclude_substring: Optional[str] = None) -> Path:
    """Latest output by mtime (Faz 7.3 race-fix style explicit detect)."""
    files = list(OUTPUTS_DIR.glob(pattern))
    if exclude_substring:
        files = [f for f in files if exclude_substring not in f.name]
    if not files:
        raise FileNotFoundError(
            f"No file matching {pattern} in {OUTPUTS_DIR}"
        )
    return max(files, key=lambda p: p.stat().st_mtime)


def run_step(name: str, command: List[str], log_path: Path) -> float:
    """
    Subprocess + write log. Failure → SystemExit(1).
    Returns elapsed seconds.
    """
    print(f"\n{'='*80}")
    print(f"STEP {name}")
    print(f"  Command: {' '.join(command)}")
    print(f"  Log:     {log_path}")
    print('='*80)

    start = time.time()
    with open(log_path, "w", encoding="utf-8") as log:
        result = subprocess.run(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            cwd=API_DIR,
            text=True,
        )
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"  [FAIL] returncode={result.returncode} (see log)")
        # Tail log for quick diagnosis
        try:
            tail = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
            print("  --- log tail ---")
            print(tail)
        except Exception:
            pass
        sys.exit(1)

    print(f"  [OK] elapsed {elapsed:.1f}s")
    return elapsed


# ============================================================================
# Pipeline
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="REELDEĞER full pipeline (race-free, Faz 4.18)"
    )
    parser.add_argument(
        "--skip-batch",
        action="store_true",
        help="BIST batch step'i atla (mevcut latest batch'i kullan, hızlı re-run)",
    )
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n{'#'*80}")
    print(f"# REELDEĞER Full Pipeline — Faz 4.18 (race-free)")
    print(f"# Timestamp: {ts}")
    print(f"# API dir:   {API_DIR}")
    print(f"# Python:    {PYTHON_EXE}")
    print(f"# Skip batch: {args.skip_batch}")
    print('#'*80)

    elapsed_total = 0.0
    steps_run: List[str] = []

    # ── Step 1/4 — BIST Batch ──
    if not args.skip_batch:
        elapsed_total += run_step(
            "1/4 BIST Batch",
            [PYTHON_EXE, str(SCRIPTS_DIR / "test_orchestrator_live.py")],
            _log_path("1_batch", ts),
        )
        steps_run.append("1/4 batch")
    else:
        print("\n[SKIP 1/4] BIST batch atlandı (--skip-batch)")

    # ── Step 2/4 — Portfolio Plan ──
    elapsed_total += run_step(
        "2/4 Portfolio Plan",
        [PYTHON_EXE, str(SCRIPTS_DIR / "run_portfolio_pipeline.py")],
        _log_path("2_portfolio", ts),
    )
    steps_run.append("2/4 portfolio")

    # ── Step 3/4 — TL Backtest ──
    elapsed_total += run_step(
        "3/4 TL Backtest",
        [PYTHON_EXE, str(SCRIPTS_DIR / "run_backtest_2021_2026.py")],
        _log_path("3_backtest_tl", ts),
    )
    steps_run.append("3/4 TL backtest")

    # ── Step 4/4 — USD Backtest (race-free explicit path) ──
    fresh_tl = find_latest(
        "backtest_results_2*.json", exclude_substring="USD"
    )
    print(f"\n[Race-free] Step 4 will read TL: {fresh_tl.name}")
    elapsed_total += run_step(
        "4/4 USD Backtest",
        [
            PYTHON_EXE,
            str(SCRIPTS_DIR / "run_backtest_usd_basis.py"),
            "--tl-results",
            str(fresh_tl),
        ],
        _log_path("4_backtest_usd", ts),
    )
    steps_run.append("4/4 USD backtest")

    # ── Summary ──
    print(f"\n{'#'*80}")
    print(f"# Pipeline COMPLETE — {len(steps_run)} step")
    print(f"# Total elapsed: {elapsed_total:.1f}s ({elapsed_total/60:.1f}min)")
    print('#'*80)

    print(f"\nLatest outputs:")
    for label, pattern in [
        ("BIST batch ", "bist_batch_LIVE_*.json"),
        ("Portfolio K", "portfolio_plan_konservatif_*.json"),
        ("TL backtest", "backtest_results_2*.json"),
        ("USD backtest", "backtest_results_USD_*.json"),
    ]:
        try:
            p = find_latest(
                pattern,
                exclude_substring=("USD" if pattern.startswith("backtest_results_2") else None),
            )
            print(f"  {label}: {p.name}")
        except FileNotFoundError:
            print(f"  {label}: (none)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
