"""
Data loader — apps/api/outputs/ JSON files → Python dict/DataFrame.

Frontend için latest backtest, portfolio plan, batch results loader'ları.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# ============================================================================
# Path Resolver
# ============================================================================

def _outputs_dir() -> Path:
    """apps/api/outputs/ absolute path (frontend → api outputs cross-app)."""
    # __file__ = apps/frontend/utils/data_loader.py
    return Path(__file__).resolve().parent.parent.parent / "api" / "outputs"


def _research_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "api" / "_research_findings"


# ============================================================================
# Portfolio Plan Loader
# ============================================================================

def load_latest_portfolio_plan(profile: str) -> Optional[Dict[str, Any]]:
    """Latest portfolio_plan_{profile}_*.json."""
    paths = sorted(_outputs_dir().glob(f"portfolio_plan_{profile}_*.json"))
    if not paths:
        return None
    return json.loads(paths[-1].read_text(encoding="utf-8"))


def load_all_profiles() -> Dict[str, Dict[str, Any]]:
    """Konservatif + Dengeli + Agresif latest plans."""
    return {
        p: load_latest_portfolio_plan(p)
        for p in ("konservatif", "dengeli", "agresif")
    }


def positions_to_df(plan: Dict[str, Any]) -> pd.DataFrame:
    """Portfolio plan positions → pandas DataFrame."""
    if not plan:
        return pd.DataFrame()
    rows = plan.get("positions", [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # Order columns
    cols = [c for c in ["ticker", "sleeve", "sub_category", "weight_pct",
                          "composite", "capital_allocation_tl"] if c in df.columns]
    return df[cols].sort_values("weight_pct", ascending=False).reset_index(drop=True)


# ============================================================================
# Backtest Loader
# ============================================================================

def load_latest_tl_backtest() -> Optional[Dict[str, Any]]:
    """Latest TL-basis backtest_results_*.json."""
    paths = [p for p in _outputs_dir().glob("backtest_results_2*.json")
             if "USD" not in p.name and "TACTICAL" not in p.name]
    if not paths:
        return None
    return json.loads(sorted(paths)[-1].read_text(encoding="utf-8"))


def load_latest_usd_backtest() -> Optional[Dict[str, Any]]:
    """Latest USD-basis backtest_results_USD_*.json."""
    paths = sorted(_outputs_dir().glob("backtest_results_USD_*.json"))
    if not paths:
        return None
    return json.loads(paths[-1].read_text(encoding="utf-8"))


def backtests_to_df(usd_data: Dict[str, Any]) -> pd.DataFrame:
    """USD backtest data → DataFrame (6 row × profile/cost)."""
    if not usd_data:
        return pd.DataFrame()
    rows = usd_data.get("backtests_usd", [])
    return pd.DataFrame(rows)


def benchmarks_to_df(usd_data: Dict[str, Any]) -> pd.DataFrame:
    """Triple benchmark USD data."""
    if not usd_data:
        return pd.DataFrame()
    rows = usd_data.get("benchmarks_usd", [])
    return pd.DataFrame(rows)


# ============================================================================
# Pentagon Score Loader (Batch JSON)
# ============================================================================

def load_latest_batch() -> Optional[Dict[str, Any]]:
    """Latest bist_batch_LIVE_*.json (Pentagon scores per ticker)."""
    paths = sorted(_outputs_dir().glob("bist_batch_LIVE_*.json"))
    if not paths:
        return None
    return json.loads(paths[-1].read_text(encoding="utf-8"))


def get_pentagon_for_ticker(batch: Dict[str, Any], ticker: str) -> Optional[Dict[str, float]]:
    """Pentagon scores (V/G/Q/M/R + composite) belirli ticker için."""
    if not batch:
        return None
    import sys
    api_path = Path(__file__).resolve().parent.parent.parent / "api"
    if str(api_path) not in sys.path:
        sys.path.insert(0, str(api_path))
    try:
        from portfolio.pentagon_scoring import score_from_json_dict
        scores = score_from_json_dict(batch)
        for s in scores:
            if s.ticker == ticker.upper():
                return {
                    "value": s.value,
                    "growth": s.growth,
                    "quality": s.quality,
                    "momentum": s.momentum,
                    "risk": s.risk,
                    "composite": s.composite,
                    "lifecycle_stage": s.lifecycle_stage,
                }
    except Exception:
        return None
    return None


# ============================================================================
# Universe Stats
# ============================================================================

def universe_stats() -> Dict[str, Any]:
    """Mevcut universe + production state özeti."""
    batch = load_latest_batch()
    if not batch:
        return {"total_tickers": 0, "successful": 0, "failed": 0}
    reports = batch.get("reports", [])
    total = len(reports)
    successful = sum(1 for r in reports if r.get("success"))
    return {
        "total_tickers": total,
        "successful": successful,
        "failed": total - successful,
        "timestamp": batch.get("timestamp"),
    }
