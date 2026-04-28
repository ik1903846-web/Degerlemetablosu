"""
4-Regime Detector — VIX-based classifier (ADR-042).

Faz 4 ADIM 2 — quarter-end VIX value → regime tag.

Bracket (Damodaran ERP + VIX hibrit, MVP VIX-only):
  Normal:             VIX < 20
  Moderate stress:    VIX 20-25
  Significant stress: VIX 25-30
  Panic:              VIX > 30

Faz 4.5'te ERP serisi eklenir (Damodaran historical reference DB).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Dict, List


# ============================================================================
# Regime Enum
# ============================================================================

class Regime(str, Enum):
    NORMAL = "normal"
    MODERATE = "moderate_stress"
    SIGNIFICANT = "significant_stress"
    PANIC = "panic"


# ============================================================================
# DataClass
# ============================================================================

@dataclass
class RegimeTag:
    quarter_end: date
    vix: float
    regime: Regime
    reasoning: str


# ============================================================================
# VIX Threshold Classifier
# ============================================================================

def classify_vix(vix: float) -> Regime:
    """Single VIX value → regime."""
    if vix < 20.0:
        return Regime.NORMAL
    if vix < 25.0:
        return Regime.MODERATE
    if vix < 30.0:
        return Regime.SIGNIFICANT
    return Regime.PANIC


def classify_quarter(qend: date, vix: float) -> RegimeTag:
    """Single quarter regime tag."""
    r = classify_vix(vix)
    bracket = ("VIX<20" if r == Regime.NORMAL
               else "VIX 20-25" if r == Regime.MODERATE
               else "VIX 25-30" if r == Regime.SIGNIFICANT
               else "VIX>30")
    return RegimeTag(
        quarter_end=qend,
        vix=vix,
        regime=r,
        reasoning=f"VIX={vix:.2f} → {r.value} ({bracket})",
    )


def regime_calendar(
    vix_quarterly: Dict[date, float],
) -> List[RegimeTag]:
    """Sıralı regime tag listesi."""
    out: List[RegimeTag] = []
    for qend in sorted(vix_quarterly.keys()):
        out.append(classify_quarter(qend, vix_quarterly[qend]))
    return out
