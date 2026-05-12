"""
Data loader — apps/api/outputs/ JSON files → Python dict/DataFrame.

Frontend için latest backtest, portfolio plan, batch results loader'ları.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


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


# ============================================================================
# v4 Batch Loader (Phase 2 SEALED format — turkey_v4_batch.json)
# ============================================================================

@st.cache_data(ttl=300)
def load_latest_v4_batch() -> Optional[Dict[str, Any]]:
    """turkey_v4_batch.json oku (Phase 2 SEALED format)."""
    path = _outputs_dir() / "turkey_v4_batch.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


@st.cache_data(ttl=300)
def universe_stats_v4() -> Dict[str, Any]:
    """turkey_v4_batch.json'dan ozet stats (Phase 2 + Phase 3b + Phase 3c + Phase 5b.2 + 5c)."""
    batch = load_latest_v4_batch()
    if not batch:
        return {
            "total_count": 0, "dcf_count": 0, "complete_count": 0,
            "intrinsic_filled": 0, "holding_intrinsic_filled": 0,
            "sector_multiple_count": 0, "book_value_count": 0,
            "industrial_engine_a_count": 0, "industrial_book_fallback_count": 0,
            "banking_ddm_count": 0, "ts_unsustainable_count": 0,
            "anchor_tuprs": None, "fetch_date": None,
        }
    tickers = batch.get("tickers", [])

    def _count_by_method(prefix=None, exact=None):
        if exact:
            return sum(1 for t in tickers if t.get("dcf_method") == exact and t.get("intrinsic_per_share_tl") is not None)
        return sum(1 for t in tickers if (t.get("dcf_method") or "").startswith(prefix) and t.get("intrinsic_per_share_tl") is not None)

    intrinsic_filled = sum(1 for t in tickers if t.get("intrinsic_per_share_tl") is not None)
    holding_intrinsic_filled = _count_by_method(exact="holding_sotp_phase3b")
    sector_multiple_count = _count_by_method(prefix="sector_multiple_regression")
    book_value_count = _count_by_method(exact="book_value_fallback")
    # Phase 5b.2 industrial Engine A swap
    industrial_engine_a_count = _count_by_method(exact="industrial_engine_a_em")
    industrial_book_fallback_count = _count_by_method(exact="industrial_engine_a_book_fallback")
    # Phase 4b/4c banking
    banking_ddm_count = _count_by_method(exact="banking_ddm_2stage_usd") + _count_by_method(exact="banking_ddm_3stage_tr_tune")
    # Phase 5c terminal sanity
    ts_unsustainable_count = sum(1 for t in tickers if t.get("terminal_value_sustainable") is False)
    # Phase 4d multi-multiple dispersion
    high_dispersion_count = sum(
        1 for t in tickers
        if t.get("consensus_dispersion") is not None and t["consensus_dispersion"] > 0.50
    )
    extreme_dispersion_count = sum(
        1 for t in tickers
        if t.get("consensus_dispersion") is not None and t["consensus_dispersion"] > 1.00
    )
    multi_multiple_validated_count = sum(
        1 for t in tickers
        if t.get("consensus_dispersion") is not None and t["consensus_dispersion"] <= 0.30
    )

    return {
        "total_count": batch.get("total_count", 0),
        "dcf_count": batch.get("dcf_count", 0),
        "complete_count": batch.get("complete_count", 0),
        "intrinsic_filled": intrinsic_filled,
        "holding_intrinsic_filled": holding_intrinsic_filled,
        "sector_multiple_count": sector_multiple_count,
        "book_value_count": book_value_count,
        "industrial_engine_a_count": industrial_engine_a_count,
        "industrial_book_fallback_count": industrial_book_fallback_count,
        "banking_ddm_count": banking_ddm_count,
        "ts_unsustainable_count": ts_unsustainable_count,
        "high_dispersion_count": high_dispersion_count,
        "extreme_dispersion_count": extreme_dispersion_count,
        "multi_multiple_validated_count": multi_multiple_validated_count,
        "anchor_tuprs": batch.get("anchor_tuprs"),
        "fetch_date": batch.get("fetch_date"),
    }
