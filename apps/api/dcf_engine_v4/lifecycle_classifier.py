"""
Lifecycle Classifier (Damodaran 6-stage, simplified KAP-only).

Damodaran kitabındaki 6-stage corporate lifecycle:
  1) Start-up         — minimal revenue, negative earnings
  2) Young Growth     — yüksek büyüme (>50%), zarar/marjinal kar
  3) High Growth      — büyüme 15-50%, pozitif excess return
  4) Mature Growth    — büyüme 5-15%, kararlı kar (TUPRS, ARCLK)
  5) Mature Stable    — büyüme <5%, yüksek payout
  6) Decline/Distress — negatif büyüme, zarar trendi

Bu modül KAP fundamentals + yfinance fiyat geçmişi ile çalışır.
Tam revenue CAGR için Excel re-parse gerek (Session 4B scope).
Şu an basit heuristic: dialect + market_cap + IPO age.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


LIFECYCLE_STAGES = [
    "start_up",
    "young_growth",
    "high_growth",
    "mature_growth",
    "mature_stable",
    "decline_distress",
]


@dataclass
class LifecycleResult:
    stage: str
    rationale: str
    confidence: str  # "high" / "medium" / "low"


def classify_lifecycle(
    dialect: Optional[str],
    market_cap_tl: Optional[float],
    history_rows: int,
    year_change_pct: Optional[float],
    de_ratio: Optional[float],
    revenue: Optional[float] = None,
) -> LifecycleResult:
    """Heuristic 6-stage lifecycle classification.

    KAP-only data + yfinance fiyat momentum.
    Tam revenue CAGR + earnings trend için Session 4.5+ enrichment.
    """
    # 1) Insurance / Unknown — n/a
    if dialect in ("insurance", "unknown", None):
        return LifecycleResult(
            stage="mature_stable",
            rationale="dialect_unknown_default_mature",
            confidence="low",
        )

    # 2) Banking — genelde mature stable (regulated)
    if dialect == "banking":
        return LifecycleResult(
            stage="mature_stable",
            rationale="banking_regulated_mature_default",
            confidence="medium",
        )

    # 3) Young IPO — history < 1.5 yıl (~375 trading day)
    if history_rows < 375:
        return LifecycleResult(
            stage="young_growth",
            rationale=f"insufficient_history ({history_rows} day)",
            confidence="medium",
        )

    # 4) Distress sinyali — yüksek leverage + negative momentum
    if de_ratio is not None and de_ratio > 3.0:
        if year_change_pct is not None and year_change_pct < -30:
            return LifecycleResult(
                stage="decline_distress",
                rationale=f"high_leverage_DE={de_ratio:.2f}_negative_momentum",
                confidence="medium",
            )

    # 5) Mature growth — large/mid cap, stable, normal leverage (TUPRS/ARCLK)
    if market_cap_tl is not None and market_cap_tl >= 10_000_000_000:  # 10B TL
        return LifecycleResult(
            stage="mature_growth",
            rationale=f"large_cap_TL{market_cap_tl/1e9:.1f}B_stable_growth_default",
            confidence="medium",
        )

    # 6) High growth — orta cap (1B-10B), yüksek momentum
    if market_cap_tl is not None and 1_000_000_000 <= market_cap_tl < 10_000_000_000:
        if year_change_pct is not None and year_change_pct > 50:
            return LifecycleResult(
                stage="high_growth",
                rationale=f"mid_cap_high_momentum_{year_change_pct:.0f}%",
                confidence="medium",
            )
        return LifecycleResult(
            stage="mature_growth",
            rationale=f"mid_cap_TL{market_cap_tl/1e9:.1f}B_default",
            confidence="low",
        )

    # 7) Default — küçük cap → high growth (genelde IPO sonrası young)
    return LifecycleResult(
        stage="high_growth",
        rationale="small_cap_default_high_growth",
        confidence="low",
    )
