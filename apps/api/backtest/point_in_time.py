"""
Point-in-Time Portfolio Plan Loader — MVP look-ahead bias.

Faz 4 ADIM 2 — Damodaran Lesson #7 candidate.

MVP yaklaşımı (Option B):
  Bugünkü Pentagon scores ile build_portfolio() output (3 risk profile)
  20 quarter boyunca FIXED kabul edilir. Quarterly rebalance original
  weights'e geri döner. Look-ahead bias documented.

Faz 4.5 (Option A):
  Her quarter için historical Pentagon recompute (bias removal).
  isyatirim multi-year + Damodaran historical DB inşası.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================================
# MVP Bias Disclaimer
# ============================================================================

LOOK_AHEAD_BIAS = True
BIAS_NOTE = (
    "MVP backtest: bugünkü Pentagon scores 20 quarter sabit. "
    "Geçmiş quarter performansı 'ileri-bakış' içerir; bias direction "
    "muhafazakâr (bugünkü intrinsic değerler conservative). "
    "Faz 4.5'te historical Pentagon recompute ile bias kaldırılır."
)


# ============================================================================
# Plan Loader
# ============================================================================

OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"


@dataclass
class PortfolioSnapshot:
    """Tek risk profile için pozisyon weights snapshot."""
    risk_profile: str
    position_weights: Dict[str, float]   # ticker → decimal (0.10 = %10)
    cash_weight: float                    # decimal
    sleeves: Dict[str, str]               # ticker → sleeve
    sub_categories: Dict[str, Optional[str]]  # ticker → sub
    composites: Dict[str, float]          # ticker → composite score
    source_path: str
    look_ahead_bias: bool = True


def latest_portfolio_plan_path(profile: str) -> Optional[Path]:
    files = sorted(OUTPUTS_DIR.glob(f"portfolio_plan_{profile}_*.json"))
    return files[-1] if files else None


def load_portfolio_snapshot(profile: str) -> PortfolioSnapshot:
    """Latest portfolio_plan_{profile}_*.json → PortfolioSnapshot."""
    path = latest_portfolio_plan_path(profile)
    if path is None:
        raise FileNotFoundError(
            f"No portfolio_plan_{profile}_*.json found in {OUTPUTS_DIR}"
        )
    plan = json.loads(path.read_text(encoding="utf-8"))

    weights: Dict[str, float] = {}
    sleeves: Dict[str, str] = {}
    subs: Dict[str, Optional[str]] = {}
    composites: Dict[str, float] = {}

    for pos in plan.get("positions", []):
        t = pos["ticker"]
        wpct = pos.get("weight_pct")
        if wpct is None:
            continue
        weights[t] = float(wpct) / 100.0
        sleeves[t] = pos.get("sleeve", "?")
        subs[t] = pos.get("sub_category")
        composites[t] = float(pos.get("composite", 50.0))

    cash_pct = plan.get("cash_reserve_pct", 0.0)
    cash = float(cash_pct) / 100.0

    return PortfolioSnapshot(
        risk_profile=profile,
        position_weights=weights,
        cash_weight=cash,
        sleeves=sleeves,
        sub_categories=subs,
        composites=composites,
        source_path=str(path),
        look_ahead_bias=LOOK_AHEAD_BIAS,
    )


def load_three_profiles() -> Dict[str, PortfolioSnapshot]:
    """3 risk profile snapshot dict."""
    return {
        p: load_portfolio_snapshot(p)
        for p in ("konservatif", "dengeli", "agresif")
    }
