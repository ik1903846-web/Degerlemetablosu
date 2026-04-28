"""
Backtest engine — Faz 4 Foundation.

REELDEĞER 3 risk profile portfolio plan ve historical price/regime data
üzerinden 2021-Q2 → 2026-Q1 (20 quarter) simülasyon.

MVP: Option B look-ahead bias (Damodaran Lesson #7).
Faz 4.5+: Option A historical Pentagon recompute (bias removal).

Modüller:
  historical_data    — Yahoo period1/period2 + disk cache
  benchmark_data     — XU100/XU030/SPY/VIX
  point_in_time      — bugünkü Pentagon scores (LOOK_AHEAD_BIAS=True)
  simulation         — quarterly rebalance engine
  performance        — TWR/Sharpe/Sortino/drawdown/beta
  regime_detector    — VIX-based 4-regime classifier
  attribution        — per-sleeve + per-regime
  failure_metrics    — 5-failure tracker (ADR-055)
"""
