"""
Pentagon Scoring — Damodaran 5-Dimensional Foundation.

Faz 3 ADIM 2 — Portfolio scoring temeli.

5 Boyut (Damodaran ADR-007 spec):
  1. Value (default 30%):     DCF intrinsic vs market gap
  2. Growth (default 25%):    Revenue CAGR + reinvestment
  3. Quality (default 20%):   Margin stability + lifecycle stage
  4. Momentum (default 15%):  12M price + earnings revision (MVP PARKING)
  5. Risk (default 10%):      Volatility + WACC INVERSE

Lifecycle-Adjusted Weights (ADR-044, 049):
  Mature Stable: V35/G15/Q25/M15/R10
  Mature Growth: V30/G25/Q20/M15/R10
  High Growth:   V20/G35/Q20/M15/R10
  Young:         V15/G40/Q20/M15/R10
  Decline:       V20/G05/Q30/M15/R30
  Distress:      V25/G05/Q25/M15/R30

Composite = sum(score_i × weight_i), 0-100 scale.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Lifecycle-Adjusted Weight Maps (ADR-044, 049)
# ============================================================================

LIFECYCLE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "MATURE_STABLE": {"value": 0.35, "growth": 0.15, "quality": 0.25, "momentum": 0.15, "risk": 0.10},
    "MATURE_GROWTH": {"value": 0.30, "growth": 0.25, "quality": 0.20, "momentum": 0.15, "risk": 0.10},
    "HIGH_GROWTH":   {"value": 0.20, "growth": 0.35, "quality": 0.20, "momentum": 0.15, "risk": 0.10},
    "YOUNG":         {"value": 0.15, "growth": 0.40, "quality": 0.20, "momentum": 0.15, "risk": 0.10},
    "DECLINE":       {"value": 0.20, "growth": 0.05, "quality": 0.30, "momentum": 0.15, "risk": 0.30},
    "DISTRESS":      {"value": 0.25, "growth": 0.05, "quality": 0.25, "momentum": 0.15, "risk": 0.30},
}
# UNKNOWN/Foobar/holding (SOTP) → fallback Mature Stable defaults below


def get_lifecycle_weights(stage: str) -> Dict[str, float]:
    """Lifecycle stage → Pentagon weights (UNKNOWN/holding → Mature Stable fallback)."""
    key = (stage or "").upper().replace("-", "_")
    return LIFECYCLE_WEIGHTS.get(key, LIFECYCLE_WEIGHTS["MATURE_STABLE"])


# ============================================================================
# DataClass
# ============================================================================

@dataclass
class PentagonScore:
    """Tek ticker için Pentagon scoring sonucu."""
    ticker: str
    value: float = 50.0
    growth: float = 50.0
    quality: float = 50.0
    momentum: float = 50.0  # MVP PARKING (default neutral)
    risk: float = 50.0
    composite: float = 50.0
    weights: Dict[str, float] = field(default_factory=dict)
    lifecycle_stage: str = "UNKNOWN"
    reasoning: List[str] = field(default_factory=list)


# ============================================================================
# Polymorphic Field Accessor (dataclass | dict | nested-dict)
# ============================================================================

def _get_nested(obj: Any, *keys: str, default: Any = None) -> Any:
    """
    Polymorphic getter — works with dataclass, flat dict, OR nested-dict JSON.

    For JSON output (nested):
      _get_nested(json_report, "market", "upside_pct") → market.upside_pct
    For ValuationReport (flat):
      _get_nested(report, "upside_pct") → report.upside_pct
      _get_nested(report, "market", "upside_pct") → report.upside_pct (fallback)
    """
    # Try nested path first
    cur = obj
    for k in keys:
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(k)
        else:
            cur = getattr(cur, k, None)
    if cur is not None:
        return cur

    # Fallback: try last key directly on root (flat dataclass)
    last_key = keys[-1]
    if isinstance(obj, dict):
        return obj.get(last_key, default)
    return getattr(obj, last_key, default)


# ============================================================================
# Per-Dimension Scoring
# ============================================================================

def score_value(report: Any) -> Tuple[float, str]:
    """
    Value boyutu — DCF upside tanh-normalize.

    -%100 → 0, 0 → 50, +%100 → ~76, +%∞ → 100
    Scale: tanh(upside / 50) modulated to 0-100
    """
    upside = _get_nested(report, "market", "upside_pct")
    if upside is None:
        return 50.0, "Value: upside_pct YOK, neutral 50"
    # Sigmoid-style: hard clamp, smooth in middle
    if upside <= -100:
        score = 0.0
    elif upside >= 200:
        score = 100.0
    else:
        # tanh(x/50) gives smooth -1..+1, scale to 0..100
        score = 50.0 + 50.0 * math.tanh(upside / 100.0)
        score = max(0.0, min(100.0, score))
    return score, f"Value: upside={upside:+.1f}% → {score:.1f}"


def score_growth(report: Any) -> Tuple[float, str]:
    """
    Growth boyutu — Revenue USD CAGR (5-yıl).

    -%5 → 0, 0% → 30, +%10 → 60, +%30+ → 100
    """
    cagr = _get_nested(report, "lifecycle", "revenue_cagr_usd")
    if cagr is None:
        return 50.0, "Growth: revenue_cagr_usd YOK, neutral 50"

    if cagr < -0.05:
        score = 0.0
    elif cagr < 0:
        score = 30.0 * (1.0 + cagr / 0.05)
    elif cagr < 0.30:
        score = 30.0 + 70.0 * (cagr / 0.30)
    else:
        score = 100.0

    score = max(0.0, min(100.0, score))
    return score, f"Growth: CAGR={cagr*100:+.1f}% → {score:.1f}"


def score_quality(report: Any) -> Tuple[float, str]:
    """
    Quality boyutu — Margin stability + lifecycle stage.

    Stability: stdev<2% → 100, <5% → 80, <10% → 50, else → 20
    Stage: Mature Stable/Growth high, Distress low.
    Score = avg(stability, stage)
    """
    stdev = _get_nested(report, "lifecycle", "margin_stdev")
    stage = _get_nested(report, "lifecycle", "stage")

    # Stability score
    if stdev is None:
        stability_score = 50.0
    elif stdev < 0.02:
        stability_score = 100.0
    elif stdev < 0.05:
        stability_score = 80.0
    elif stdev < 0.10:
        stability_score = 50.0
    else:
        stability_score = 20.0

    # Stage score
    stage_score_map = {
        "MATURE_STABLE": 90.0,
        "MATURE_GROWTH": 80.0,
        "HIGH_GROWTH":   60.0,
        "YOUNG":         40.0,
        "DECLINE":       30.0,
        "DISTRESS":      10.0,
        "UNKNOWN":       50.0,
    }
    stage_key = (stage or "").upper().replace("-", "_") if stage else "UNKNOWN"
    stage_score = stage_score_map.get(stage_key, 50.0)

    score = (stability_score + stage_score) / 2.0
    return score, (
        f"Quality: stdev={stdev*100:.1f}% (stab {stability_score:.0f}) + "
        f"stage={stage_key} ({stage_score:.0f}) → {score:.1f}"
        if stdev is not None
        else f"Quality: stage={stage_key} ({stage_score:.0f}), stdev YOK → {score:.1f}"
    )


def score_momentum(report: Any) -> Tuple[float, str]:
    """
    Momentum boyutu — MVP PARKING (default 50 neutral).

    Future: Yahoo Finance 12M return + earnings revision (Faz 3.5).
    """
    return 50.0, "Momentum: PARKING (default 50, Yahoo fetcher Faz 3.5)"


def score_risk(report: Any) -> Tuple[float, str]:
    """
    Risk boyutu (INVERSE — low risk = high score).

    Margin spread (volatility): <5pp → 100, <15pp → 70, <30pp → 40, else → 10
    WACC: <10% → 100, <13% → 70, <16% → 40, else → 10
    Score = avg(vol, wacc) INVERSE applied
    """
    spread = _get_nested(report, "lifecycle", "margin_spread")
    wacc = _get_nested(report, "dcf", "wacc")
    if wacc is None:
        wacc = _get_nested(report, "wacc")

    # Volatility score (low spread = high score)
    if spread is None:
        vol_score = 50.0
    elif spread < 0.05:
        vol_score = 100.0
    elif spread < 0.15:
        vol_score = 70.0
    elif spread < 0.30:
        vol_score = 40.0
    else:
        vol_score = 10.0

    # WACC score (low WACC = high score)
    if wacc is None:
        wacc_score = 50.0
    elif wacc < 0.10:
        wacc_score = 100.0
    elif wacc < 0.13:
        wacc_score = 70.0
    elif wacc < 0.16:
        wacc_score = 40.0
    else:
        wacc_score = 10.0

    score = (vol_score + wacc_score) / 2.0
    spread_str = f"{spread*100:.1f}pp" if spread is not None else "n/a"
    wacc_str = f"{wacc*100:.1f}%" if wacc is not None else "n/a"
    return score, (
        f"Risk: spread={spread_str} (vol {vol_score:.0f}) + "
        f"WACC={wacc_str} ({wacc_score:.0f}) → {score:.1f}"
    )


# ============================================================================
# Composite Scoring
# ============================================================================

def score_ticker(report: Any) -> Optional[PentagonScore]:
    """
    Single ticker Pentagon scoring.

    Args:
        report: ValuationReport veya JSON dict (polymorphic).

    Returns:
        PentagonScore (composite 0-100) veya None (success=False).
    """
    success = _get_nested(report, "success")
    if not success:
        return None

    ticker = _get_nested(report, "ticker") or "?"
    stage = _get_nested(report, "lifecycle", "stage") or "UNKNOWN"
    stage_key = (stage or "").upper().replace("-", "_")

    s = PentagonScore(ticker=ticker, lifecycle_stage=stage_key)

    s.value, log_v = score_value(report)
    s.growth, log_g = score_growth(report)
    s.quality, log_q = score_quality(report)
    s.momentum, log_m = score_momentum(report)
    s.risk, log_r = score_risk(report)

    s.weights = get_lifecycle_weights(stage_key)

    s.composite = (
        s.value * s.weights["value"]
        + s.growth * s.weights["growth"]
        + s.quality * s.weights["quality"]
        + s.momentum * s.weights["momentum"]
        + s.risk * s.weights["risk"]
    )

    s.reasoning.extend([log_v, log_g, log_q, log_m, log_r])
    s.reasoning.append(
        f"Composite: V({s.value:.0f}*{s.weights['value']*100:.0f}) + "
        f"G({s.growth:.0f}*{s.weights['growth']*100:.0f}) + "
        f"Q({s.quality:.0f}*{s.weights['quality']*100:.0f}) + "
        f"M({s.momentum:.0f}*{s.weights['momentum']*100:.0f}) + "
        f"R({s.risk:.0f}*{s.weights['risk']*100:.0f}) = {s.composite:.1f}"
    )

    return s


def score_batch(reports: List[Any]) -> List[PentagonScore]:
    """Batch Pentagon scoring (filters out failed reports)."""
    scores: List[PentagonScore] = []
    for r in reports:
        s = score_ticker(r)
        if s is not None:
            scores.append(s)
    return scores


def score_from_json_dict(json_data: Dict[str, Any]) -> List[PentagonScore]:
    """
    Batch JSON output ('reports' key list of dicts) → Pentagon scores.

    Convenience for working with bist_batch_LIVE_*.json outputs.
    """
    reports = json_data.get("reports", [])
    return score_batch(reports)


def rank_by_composite(scores: List[PentagonScore]) -> List[PentagonScore]:
    """Composite descending sort (highest first)."""
    return sorted(scores, key=lambda s: s.composite, reverse=True)
