"""
3-Sleeve Assignment — Damodaran Portfolio Architecture.

Faz 3 ADIM 3 — Pentagon Score → Sleeve mapping.
Faz 6.5 (e) — Banking-specific sleeve rules (Damodaran Lesson #6).

3-Sleeve Mapping (Damodaran ADR-066, 067):

  CORE (default 60%):
    Lifecycle ∈ {MATURE_GROWTH, MATURE_STABLE, UNKNOWN}
    Upside > %30 + Quality > 60 + Composite > 50

    Banking branch (Faz 6.5 e):
      excess_return ≥ 4pp + upside > 0 + composite > 50 + value > 30
      Sub: "banking_intrinsic" (ROE > CoE + market gap)

  HIZLI BÜYÜME (default 25%):
    Lifecycle ∈ {YOUNG, HIGH_GROWTH}
    Growth > 60 + Composite > 55
    (BIST 30 nadir → MVP'de boş kalabilir)

  YÜKSEK KAZANÇ (default 15%) — alt-kategoriler:
    deep_value:               upside > %100 + composite > 55
    holding_chronic_discount: financial_group=HOLDING + upside > 50
    banking_premium:          is_banking + ROE > %20 + upside > %50  (Faz 6.5 e)
    mature_transition:        Mature/Decline + Quality<60 + Value>70
    distress:                 stage=DISTRESS

  SKIP / SAT:
    composite < 35  OR  value < 20  OR  upside < -%30
    negative DCF (THYAO, PGSUS, PETKM) — Faz 7.3 ROLLBACK: distress_turnaround
    sub-category Faz 7.1 v2'de eklenmişti, race-fixed evidence ile -1.6pp
    real drag exposed → re-rollback. Module distress_dcf.py production-ready
    parking, integration future iteration (40Q+ horizon veya separate sleeve).

Risk Profile Allocations (ADR-016):
  Konservatif: Core 80, Hızlı 15, Yüksek 5
  Dengeli (default): Core 60, Hızlı 25, Yüksek 15
  Agresif: Core 40, Hızlı 35, Yüksek 25
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from portfolio.pentagon_scoring import PentagonScore, _get_nested


# ============================================================================
# Sleeve Enum
# ============================================================================

class Sleeve(str, Enum):
    """3-Sleeve + Skip."""
    CORE = "core"
    HIZLI_BUYUME = "hizli_buyume"
    YUKSEK_KAZANC = "yuksek_kazanc"
    SKIP = "skip"


# ============================================================================
# DataClass
# ============================================================================

@dataclass
class SleeveAssignment:
    """Tek ticker için sleeve assignment sonucu."""
    ticker: str
    sleeve: Sleeve
    sub_category: Optional[str]  # YUKSEK_KAZANC için: deep_value | holding_chronic_discount | mature_transition | distress
    pentagon_score: PentagonScore
    composite: float
    confidence: float
    reasoning: List[str] = field(default_factory=list)


# ============================================================================
# Risk Profile Allocations
# ============================================================================

RISK_PROFILES: Dict[str, Dict[str, float]] = {
    # Faz 4.14 — Allocation lever (Damodaran Lesson #14):
    # Yüksek Kazanç sleeve target reduction (drag minimize WITHOUT ticker drop).
    # Faz 4.15 — Lesson #14 extension: Agresif Yüksek %15 → %10 (Core %50 → %55).
    # Faz 4.17 — Profile differentiation (Damodaran Lesson #16):
    #   Faz 4.16 Core PRIORITY + Yüksek %10 her ikisinde → Dengeli/Agresif IDENTICAL emergent.
    #   Fix: Agresif Yüksek %10 → %15, Core %55 → %50 (distinct profile spectrum).
    # Konservatif/Dengeli aynen (anchor 4 BEAT korunur).
    # Eski Faz 4.7 v2: 0.80/0.15/0.05, 0.60/0.25/0.15, 0.40/0.35/0.25
    "konservatif": {"core": 0.82, "hizli_buyume": 0.15, "yuksek_kazanc": 0.03},
    "dengeli":     {"core": 0.65, "hizli_buyume": 0.25, "yuksek_kazanc": 0.10},
    "agresif":     {"core": 0.50, "hizli_buyume": 0.35, "yuksek_kazanc": 0.15},
}


def get_risk_profile_allocations(profile: str = "dengeli") -> Dict[str, float]:
    """Damodaran risk profile allocations (ADR-016, default Dengeli 60/25/15)."""
    return RISK_PROFILES.get(profile.lower(), RISK_PROFILES["dengeli"])


# ============================================================================
# Sleeve Assignment Logic
# ============================================================================

def _stage_key(report: Any) -> str:
    """Lifecycle stage normalize (UNKNOWN if missing)."""
    raw = _get_nested(report, "lifecycle", "stage")
    if raw is None:
        return "UNKNOWN"
    if hasattr(raw, "name"):
        return raw.name.upper()
    return str(raw).upper().replace("-", "_")


def _is_holding(report: Any) -> bool:
    """Holding ticker mi (financial_group=HOLDING)?"""
    fg = _get_nested(report, "financial_group")
    return fg == "HOLDING"


def _banking_metrics(report: Any) -> tuple:
    """
    Banking ticker için (excess_return_pp, roe_pct) tuple döndür.

    Returns (None, None) banking değilse veya banking_data yoksa.
    """
    if not _get_nested(report, "is_banking"):
        return None, None

    ticker = _get_nested(report, "ticker")
    if not ticker:
        return None, None

    coe = _get_nested(report, "dcf", "wacc")
    if coe is None:
        coe = _get_nested(report, "wacc")

    # Lazy import — avoid eager dep
    from data_layer.banking_data import get_banking_data

    config = get_banking_data(ticker)
    if config is None or not config.yearly:
        return None, None

    latest = max(config.yearly, key=lambda d: d.year)
    roe = latest.roe_pct
    if roe is None or coe is None:
        return None, roe

    spread_pp = roe - (coe * 100.0)
    return spread_pp, roe


def assign_sleeve(report: Any, score: PentagonScore) -> SleeveAssignment:
    """
    Damodaran 3-sleeve assignment (ADR-066, 067).

    Priority order (rule cascade):
      1. SKIP (success/dcf/composite/value/upside thresholds)
      2. YÜKSEK KAZANÇ — deep_value (upside > 100)
      3. YÜKSEK KAZANÇ — holding_chronic_discount (KCHOL/SAHOL chronic)
      4. YÜKSEK KAZANÇ — distress (stage=DISTRESS)
      5. YÜKSEK KAZANÇ — mature_transition (stage compression)
      6. HIZLI BÜYÜME (Young/High Growth)
      7. CORE (Mature + upside + quality)
      8. SKIP (uncertain fallback)

    Args:
        report: ValuationReport veya JSON dict (polymorphic).
        score:  PentagonScore (pentagon_scoring.score_ticker output).

    Returns:
        SleeveAssignment with sub_category, confidence, reasoning.
    """
    ticker = _get_nested(report, "ticker") or score.ticker

    success = _get_nested(report, "success")
    dcf_executed = _get_nested(report, "dcf", "executed")
    if dcf_executed is None:
        dcf_executed = _get_nested(report, "dcf_executed")

    upside = _get_nested(report, "market", "upside_pct")
    if upside is None:
        upside = _get_nested(report, "upside_pct")
    if upside is None:
        upside = 0.0

    equity_value_usd = _get_nested(report, "dcf", "equity_value_usd")
    if equity_value_usd is None:
        equity_value_usd = _get_nested(report, "equity_value_usd")

    stage = _stage_key(report)
    holding = _is_holding(report)

    # ---- Rule 1: SKIP — failed pipeline ----
    if not success or not dcf_executed:
        return SleeveAssignment(
            ticker, Sleeve.SKIP, None, score, score.composite, 1.0,
            ["SKIP: success=False veya DCF execute edilmedi"]
        )

    # ---- Rule 1b: SKIP — negatif DCF (THYAO, PGSUS, PETKM artifact) ----
    if equity_value_usd is not None and equity_value_usd < 0:
        return SleeveAssignment(
            ticker, Sleeve.SKIP, None, score, score.composite, 1.0,
            [f"SKIP: negatif DCF (equity_value_usd=${equity_value_usd/1e9:.2f}B, distress artifact)"]
        )

    # ---- Rule 1c: SKIP — composite/value/upside hard floors (Faz 4.2 gevşetme) ----
    if score.composite < 32:
        return SleeveAssignment(
            ticker, Sleeve.SKIP, None, score, score.composite, 0.9,
            [f"SKIP: composite {score.composite:.1f} < 32 (Pentagon zayıf)"]
        )

    if score.value < 15:
        return SleeveAssignment(
            ticker, Sleeve.SKIP, None, score, score.composite, 0.9,
            [f"SKIP: V={score.value:.0f} < 15 (overvalued)"]
        )

    if upside < -35:
        return SleeveAssignment(
            ticker, Sleeve.SKIP, None, score, score.composite, 0.9,
            [f"SKIP: upside {upside:+.0f}% < -35% (SAT verdict)"]
        )

    # ---- Rule 1d: Banking branch (Faz 6.5 e — Damodaran Lesson #6) ----
    is_banking = bool(_get_nested(report, "is_banking"))
    if is_banking:
        spread_pp, roe_pct = _banking_metrics(report)

        # Banking deep_value: upside > %80 (Faz 4.2 gevşetme)
        if upside > 80 and score.composite > 50:
            return SleeveAssignment(
                ticker, Sleeve.YUKSEK_KAZANC, "deep_value", score, score.composite, 0.85,
                [f"YÜKSEK KAZANÇ deep_value (banking): upside {upside:+.0f}% > %80, "
                 f"composite {score.composite:.1f}"]
            )

        # Banking intrinsic CORE: excess_return ≥ 3pp + upside > -5 (Faz 4.2 gevşetme)
        if (
            spread_pp is not None and spread_pp >= 3.0
            and upside > -5
            and score.composite > 50
            and score.value > 25
        ):
            return SleeveAssignment(
                ticker, Sleeve.CORE, "banking_intrinsic",
                score, score.composite, 0.85,
                [f"CORE banking_intrinsic: excess_return {spread_pp:+.2f}pp ≥ 3pp, "
                 f"upside {upside:+.0f}% > -5, composite {score.composite:.1f}, V={score.value:.0f}"]
            )

        # Banking premium: ROE > %18 + upside > %30 (Faz 4.2 gevşetme)
        if roe_pct is not None and roe_pct > 18 and upside > 30:
            return SleeveAssignment(
                ticker, Sleeve.YUKSEK_KAZANC, "banking_premium",
                score, score.composite, 0.75,
                [f"YÜKSEK KAZANÇ banking_premium: ROE {roe_pct:.1f}% > %18, "
                 f"upside {upside:+.0f}% > %30"]
            )

        # Banking SKIP fallback (composite/spread inadequate)
        return SleeveAssignment(
            ticker, Sleeve.SKIP, None, score, score.composite, 0.6,
            [f"SKIP (banking): excess_return={spread_pp:+.2f}pp"
             if spread_pp is not None else f"SKIP (banking): excess_return YOK",
             f"upside={upside:+.0f}%, composite {score.composite:.1f}"]
        )

    # ---- Rule 2: YÜKSEK KAZANÇ — holding chronic discount (öncelikli) ----
    # Holdings için deep_value sub'ından farklı sınıflandırma — KCHOL/SAHOL
    # SOTP routed, lifecycle UNKNOWN, intrinsic > market chronic discount.
    if holding and upside > 50 and score.composite > 50:
        return SleeveAssignment(
            ticker, Sleeve.YUKSEK_KAZANC, "holding_chronic_discount",
            score, score.composite, 0.80,
            [f"YÜKSEK KAZANÇ holding: SOTP chronic discount, upside {upside:+.0f}%"]
        )

    # ---- Rule 3: YÜKSEK KAZANÇ — deep_value (non-holding upside > %80, Faz 4.2 gevşetme) ----
    if upside > 80 and score.composite > 50:
        return SleeveAssignment(
            ticker, Sleeve.YUKSEK_KAZANC, "deep_value", score, score.composite, 0.85,
            [f"YÜKSEK KAZANÇ deep_value: upside {upside:+.0f}% > %80, composite {score.composite:.1f}"]
        )

    # ---- Rule 4: YÜKSEK KAZANÇ — distress ----
    if stage == "DISTRESS":
        return SleeveAssignment(
            ticker, Sleeve.YUKSEK_KAZANC, "distress", score, score.composite, 0.75,
            [f"YÜKSEK KAZANÇ distress: stage={stage}"]
        )

    # ---- Rule 5: YÜKSEK KAZANÇ — mature_transition ----
    if stage in ("MATURE_STABLE", "DECLINE") and score.quality < 60 and score.value > 70:
        return SleeveAssignment(
            ticker, Sleeve.YUKSEK_KAZANC, "mature_transition",
            score, score.composite, 0.70,
            [f"YÜKSEK KAZANÇ mature_transition: stage={stage}, "
             f"Q={score.quality:.0f}<60, V={score.value:.0f}>70"]
        )

    # ---- Rule 6: HIZLI BÜYÜME ----
    if stage in ("YOUNG", "HIGH_GROWTH") and score.growth > 60 and score.composite > 55:
        return SleeveAssignment(
            ticker, Sleeve.HIZLI_BUYUME, None, score, score.composite, 0.85,
            [f"HIZLI BÜYÜME: stage={stage}, G={score.growth:.0f}>60, "
             f"composite {score.composite:.1f}"]
        )

    # ---- Rule 7: CORE (Faz 4.2 gevşetme: upside > 20, Q > 55, composite > 48) ----
    if (
        stage in ("MATURE_GROWTH", "MATURE_STABLE", "UNKNOWN")
        and upside > 20
        and score.quality > 55
        and score.composite > 48
    ):
        return SleeveAssignment(
            ticker, Sleeve.CORE, None, score, score.composite, 0.90,
            [f"CORE: stage={stage}, upside {upside:+.0f}% > %20, "
             f"Q={score.quality:.0f}>55, composite {score.composite:.1f}>48"]
        )

    # ---- Rule 8: SKIP fallback (uncertain) ----
    return SleeveAssignment(
        ticker, Sleeve.SKIP, None, score, score.composite, 0.5,
        [f"SKIP (uncertain): stage={stage}, upside={upside:+.0f}%, "
         f"V={score.value:.0f}, Q={score.quality:.0f}, comp={score.composite:.1f}"]
    )


def assign_batch(
    reports: List[Any],
    scores: List[PentagonScore],
) -> List[SleeveAssignment]:
    """
    Batch sleeve assignment.

    Reports + scores ticker-bazlı eşlenir. Eğer score yoksa o ticker skip.
    """
    score_map = {s.ticker: s for s in scores}
    assignments: List[SleeveAssignment] = []
    for r in reports:
        ticker = _get_nested(r, "ticker")
        if ticker is None:
            continue
        score = score_map.get(ticker)
        if score is None:
            continue
        assignments.append(assign_sleeve(r, score))
    return assignments


def summarize_sleeves(assignments: List[SleeveAssignment]) -> Dict[str, Any]:
    """Sleeve breakdown summary (count, tickers per sleeve)."""
    summary: Dict[str, Any] = {
        "total": len(assignments),
        "by_sleeve": {s.value: [] for s in Sleeve},
        "yuksek_kazanc_subs": {},
    }
    for a in assignments:
        summary["by_sleeve"][a.sleeve.value].append(a.ticker)
        if a.sleeve == Sleeve.YUKSEK_KAZANC and a.sub_category:
            summary["yuksek_kazanc_subs"].setdefault(a.sub_category, []).append(a.ticker)
    summary["counts"] = {k: len(v) for k, v in summary["by_sleeve"].items()}
    return summary
