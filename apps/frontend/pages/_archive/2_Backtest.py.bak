"""
Backtest Performance — USD vs TL toggle, benchmark comparison, regime calendar.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from utils.data_loader import (
    load_latest_tl_backtest,
    load_latest_usd_backtest,
)


st.set_page_config(page_title="Backtest | REELDEĞER", layout="wide")

st.title("Backtest Performance")
st.caption("2021-Q2 → 2026-Q1 (20 quarter, 4.75 yıl) — 3 profile × 2 cost = 6 run")


# ============================================================================
# Basis Toggle (USD / TL)
# ============================================================================

basis = st.sidebar.radio("Basis", ["USD", "TL"], horizontal=True)

usd_data = load_latest_usd_backtest()
tl_data = load_latest_tl_backtest()

if not usd_data:
    st.error("USD backtest results not found")
    st.stop()


# ============================================================================
# Hero Metrics (Konservatif Zero — Best Profile)
# ============================================================================

backtests_usd = usd_data.get("backtests_usd", [])
benchmarks_usd = usd_data.get("benchmarks_usd", [])

konser_zero = next(
    (b for b in backtests_usd
     if b["profile"] == "konservatif" and b["cost_model"] == "zero"),
    None,
)
xu100 = next((b for b in benchmarks_usd if b["label"] == "XU100"), None)
xu030 = next((b for b in benchmarks_usd if b["label"] == "XU030"), None)
spy = next((b for b in benchmarks_usd if b["label"] == "SPY"), None)

if konser_zero:
    if basis == "USD":
        ann_pct = konser_zero["usd_annualized"] * 100
    else:
        ann_pct = konser_zero["tl_annualized"] * 100

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Best Profile", "Konservatif Zero")
    with col2:
        st.metric(
            f"{basis} Annualized",
            f"{ann_pct:+.2f}%/yr",
        )
    with col3:
        if xu100 and basis == "USD":
            delta = (konser_zero["usd_annualized"] -
                     xu100["usd_annualized"]) * 100
            st.metric(
                "vs XU100 USD",
                f"{delta:+.2f}pp",
                "BEAT ★" if delta > 0 else "underperform",
            )
    with col4:
        if spy and basis == "USD":
            delta = (konser_zero["usd_annualized"] -
                     spy["usd_annualized"]) * 100
            st.metric(
                "vs SPY USD",
                f"{delta:+.2f}pp",
                "BEAT ★" if delta > 0 else "underperform",
            )

st.divider()


# ============================================================================
# 6 Backtest Comparison Table
# ============================================================================

st.subheader(f"6 Backtest × 3 Benchmark — {basis} Basis")

rows = []
for bt in backtests_usd:
    if basis == "USD":
        ann = bt["usd_annualized"] * 100
        cum = bt["usd_cumulative"] * 100
        sharpe = bt.get("usd_sharpe")
        max_dd = bt["usd_max_drawdown"] * 100
    else:
        ann = bt["tl_annualized"] * 100
        cum = bt["tl_cumulative"] * 100
        sharpe = None  # TL Sharpe ayrı endpoint
        max_dd = None  # TL Max DD ayrı

    # Benchmark deltas
    delta_xu100 = (bt["usd_annualized"] - xu100["usd_annualized"]) * 100 if xu100 and basis == "USD" else None
    delta_spy = (bt["usd_annualized"] - spy["usd_annualized"]) * 100 if spy and basis == "USD" else None

    rows.append({
        "Profile": bt["profile"].capitalize(),
        "Cost": bt["cost_model"],
        f"{basis} Cum %": f"{cum:+.2f}",
        f"{basis} Ann %/yr": f"{ann:+.2f}",
        "Sharpe": f"{sharpe:.2f}" if sharpe else "—",
        "Max DD %": f"{max_dd:+.2f}" if max_dd else "—",
        "vs XU100 pp": f"{delta_xu100:+.2f} {'★' if delta_xu100 and delta_xu100 > 0 else ''}" if delta_xu100 else "—",
        "vs SPY pp": f"{delta_spy:+.2f} {'★' if delta_spy and delta_spy > 0 else ''}" if delta_spy else "—",
    })

# Add benchmarks
for bm in benchmarks_usd:
    if basis == "USD":
        ann = bm["usd_annualized"] * 100
        cum = bm["usd_cumulative"] * 100
        sharpe = bm.get("usd_sharpe")
        max_dd = bm["usd_max_drawdown"] * 100
    else:
        ann = None
        cum = None
        sharpe = None
        max_dd = None

    rows.append({
        "Profile": f"📈 {bm['label']}",
        "Cost": "benchmark",
        f"{basis} Cum %": f"{cum:+.2f}" if cum is not None else "—",
        f"{basis} Ann %/yr": f"{ann:+.2f}" if ann is not None else "—",
        "Sharpe": f"{sharpe:.2f}" if sharpe else "—",
        "Max DD %": f"{max_dd:+.2f}" if max_dd is not None else "—",
        "vs XU100 pp": "—",
        "vs SPY pp": "—",
    })

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)


st.divider()


# ============================================================================
# USD Annualized Bar Chart
# ============================================================================

if basis == "USD":
    st.subheader("USD Annualized Comparison (vs Triple Benchmark)")

    fig = go.Figure()

    portfolio_names = []
    portfolio_anns = []
    for bt in backtests_usd:
        portfolio_names.append(f"{bt['profile'].capitalize()} {bt['cost_model']}")
        portfolio_anns.append(bt["usd_annualized"] * 100)

    fig.add_trace(go.Bar(
        x=portfolio_names,
        y=portfolio_anns,
        name="REELDEĞER",
        marker_color="#FFB700",
        text=[f"{v:+.2f}%" for v in portfolio_anns],
        textposition="outside",
    ))

    # Benchmark horizontal lines
    for bm, color in zip(benchmarks_usd, ["#FF6B6B", "#4ECDC4", "#00D4FF"]):
        ann_pct = bm["usd_annualized"] * 100
        fig.add_hline(
            y=ann_pct,
            line_dash="dash",
            line_color=color,
            annotation_text=f"{bm['label']} {ann_pct:+.2f}%",
            annotation_position="right",
        )

    fig.update_layout(
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(30,30,46,0.5)",
        font_color="#FAFAFA",
        showlegend=False,
        yaxis=dict(title="USD Annualized %/yr", gridcolor="rgba(255,255,255,0.1)"),
        xaxis=dict(tickangle=-30),
    )
    st.plotly_chart(fig, use_container_width=True)


st.divider()


# ============================================================================
# Quarterly Returns Line Chart (cumulative wealth path)
# ============================================================================

st.subheader("Cumulative Wealth Path (USD basis)")

# Pick profile to highlight
selected_profile = st.selectbox(
    "Profile",
    ["konservatif", "dengeli", "agresif"],
    index=0,
)
selected_cost = st.radio("Cost", ["zero", "realistic"], horizontal=True)

selected_bt = next(
    (b for b in backtests_usd
     if b["profile"] == selected_profile and b["cost_model"] == selected_cost),
    None,
)

if selected_bt and selected_bt.get("usd_quarterly_returns"):
    quarterly = selected_bt["usd_quarterly_returns"]

    # Cumulative wealth path
    wealth = [1.0]
    for r in quarterly:
        wealth.append(wealth[-1] * (1 + r))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=[w * 100 for w in wealth],
        mode="lines+markers",
        name=f"{selected_profile} {selected_cost}",
        line=dict(color="#FFB700", width=3),
        fill="tozeroy",
        fillcolor="rgba(255, 183, 0, 0.1)",
    ))

    # Benchmarks (USD basis if available)
    for bm in benchmarks_usd:
        bm_quarterly = bm.get("quarterly_returns") or bm.get("usd_quarterly_returns")
        if bm_quarterly:
            bm_wealth = [1.0]
            for r in bm_quarterly:
                bm_wealth.append(bm_wealth[-1] * (1 + r))
            fig.add_trace(go.Scatter(
                y=[w * 100 for w in bm_wealth],
                mode="lines",
                name=bm["label"],
                line=dict(width=2, dash="dash"),
            ))

    fig.update_layout(
        height=500,
        xaxis=dict(title="Quarter index", gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(title="Cumulative wealth (USD, base=100)",
                    gridcolor="rgba(255,255,255,0.1)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(30,30,46,0.5)",
        font_color="#FAFAFA",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# Sidebar Info
# ============================================================================

with st.sidebar:
    st.divider()
    st.markdown("### Backtest Info")
    meta = usd_data.get("metadata", {})
    st.caption(f"Period: {meta.get('period_start')} → {meta.get('period_end')}")
    st.caption(f"FX devaluation: {meta.get('fx_devaluation', 0):.2f}x")
    st.caption(f"Look-ahead bias: {meta.get('look_ahead_bias')}")
    st.caption("ADR-002 (USD-only) compliant")

    st.divider()
    st.markdown("**Benchmarks (USD):**")
    for bm in benchmarks_usd:
        ann = bm["usd_annualized"] * 100
        st.caption(f"- {bm['label']}: {ann:+.2f}%/yr")
