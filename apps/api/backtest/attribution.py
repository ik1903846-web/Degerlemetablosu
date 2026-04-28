"""
Per-Sleeve + Per-Regime Attribution.

Faz 4 ADIM 2 — backtest sonuçları üzerinden:
  - Sleeve contribution: per-quarter sum(weight × ticker_return) by sleeve
  - Regime breakdown: TWR per regime tag

Damodaran disiplini: "where does the return come from" — investor visibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from backtest.simulation import BacktestResult, QuarterResult
from backtest.regime_detector import RegimeTag, Regime


# ============================================================================
# DataClasses
# ============================================================================

@dataclass
class SleeveContribution:
    """Tek sleeve toplam katkı."""
    sleeve: str
    avg_weight: float            # quarter average sleeve weight
    cumulative_contribution: float   # toplam contribution (additive proxy)
    n_quarters: int


@dataclass
class RegimeBreakdown:
    """Tek regime için portfolio TWR."""
    regime: Regime
    n_quarters: int
    cumulative_return: float
    avg_quarterly_return: float
    quarter_ends: List[date] = field(default_factory=list)


# ============================================================================
# Sleeve Attribution
# ============================================================================

def sleeve_attribution(
    result: BacktestResult,
    sleeves: Dict[str, str],  # ticker → sleeve
) -> List[SleeveContribution]:
    """Per-sleeve average weight + cumulative contribution proxy."""
    sleeve_weights: Dict[str, List[float]] = {}
    sleeve_contribs: Dict[str, float] = {}

    for qres in result.quarter_results:
        for ticker, w in qres.post_rebalance_weights.items():
            sleeve = sleeves.get(ticker, "?")
            sleeve_weights.setdefault(sleeve, []).append(w)
            r = qres.ticker_returns.get(ticker, 0.0)
            sleeve_contribs[sleeve] = sleeve_contribs.get(sleeve, 0.0) + w * r

    out: List[SleeveContribution] = []
    for sleeve in sleeve_weights:
        ws = sleeve_weights[sleeve]
        out.append(SleeveContribution(
            sleeve=sleeve,
            avg_weight=sum(ws) / len(ws) if ws else 0.0,
            cumulative_contribution=sleeve_contribs.get(sleeve, 0.0),
            n_quarters=len(ws),
        ))
    return sorted(out, key=lambda x: -x.avg_weight)


# ============================================================================
# Regime Breakdown
# ============================================================================

def regime_breakdown(
    result: BacktestResult,
    regime_tags: List[RegimeTag],
) -> List[RegimeBreakdown]:
    """Per-regime TWR + average return."""
    # Build regime per quarter map (qend → regime)
    qe_to_regime: Dict[date, Regime] = {
        rt.quarter_end: rt.regime for rt in regime_tags
    }

    # Bucket quarter returns by regime
    buckets: Dict[Regime, List[tuple]] = {r: [] for r in Regime}
    for qres in result.quarter_results:
        regime = qe_to_regime.get(qres.quarter_end)
        if regime is None:
            continue
        buckets[regime].append((qres.quarter_end, qres.portfolio_return))

    out: List[RegimeBreakdown] = []
    for regime in Regime:
        items = buckets.get(regime, [])
        if not items:
            out.append(RegimeBreakdown(
                regime=regime, n_quarters=0,
                cumulative_return=0.0, avg_quarterly_return=0.0,
                quarter_ends=[],
            ))
            continue
        rets = [r for _, r in items]
        cum = 1.0
        for r in rets:
            cum *= (1.0 + r)
        cum -= 1.0
        out.append(RegimeBreakdown(
            regime=regime,
            n_quarters=len(items),
            cumulative_return=cum,
            avg_quarterly_return=sum(rets) / len(rets),
            quarter_ends=[d for d, _ in items],
        ))
    return out
