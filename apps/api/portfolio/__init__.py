"""
REELDEĞER Portfolio Construction Module.

Faz 3 — Pentagon Scoring + 3-Sleeve mapping + Position sizing.

Submodules:
- pentagon_scoring: Damodaran 5-D scoring (Value/Growth/Quality/Momentum/Risk)
- sleeve_assignment: 3-Sleeve mapping (Core/Hızlı/Yüksek)
- portfolio_construction: Position sizing + rebalance
"""

from portfolio.pentagon_scoring import (
    PentagonScore,
    score_ticker,
    score_batch,
    score_from_json_dict,
    get_lifecycle_weights,
)

__all__ = [
    "PentagonScore",
    "score_ticker",
    "score_batch",
    "score_from_json_dict",
    "get_lifecycle_weights",
]
