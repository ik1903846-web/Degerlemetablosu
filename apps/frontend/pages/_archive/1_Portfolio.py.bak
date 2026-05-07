"""
Portfolio Dashboard — 3 risk profile + sleeve breakdown + ticker drill-down.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent for utils import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from utils.data_loader import (
    load_latest_portfolio_plan,
    load_latest_batch,
    get_pentagon_for_ticker,
    positions_to_df,
)


st.set_page_config(page_title="Portfolio | REELDEĞER", layout="wide")

st.title("Portfolio Dashboard")
st.caption("3 risk profile — sleeve breakdown, position weights, Pentagon scoring")


# ============================================================================
# Profile Selector
# ============================================================================

profile = st.sidebar.selectbox(
    "Risk Profile",
    ["konservatif", "dengeli", "agresif"],
    index=1,  # Dengeli default
)

plan = load_latest_portfolio_plan(profile)
if not plan:
    st.error(f"Portfolio plan not found for {profile}")
    st.stop()


# ============================================================================
# Hero Metrics
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

actual = plan.get("actual_allocations_pct", {})
target = plan.get("target_allocations_pct", {})

with col1:
    st.metric(
        "Total Positions",
        plan.get("total_positions", 0),
    )

with col2:
    st.metric(
        "Core Allocation",
        f"{actual.get('core', 0):.1f}%",
        f"target {target.get('core', 0):.0f}%",
    )

with col3:
    st.metric(
        "Yüksek Kazanç",
        f"{actual.get('yuksek_kazanc', 0):.1f}%",
        f"target {target.get('yuksek_kazanc', 0):.0f}%",
    )

with col4:
    cash = plan.get("cash_reserve_pct", 0)
    st.metric(
        "Cash Reserve",
        f"{cash:.1f}%",
        f"TL {plan.get('cash_reserve_tl', 0):,.0f}",
    )

st.divider()


# ============================================================================
# Sleeve Pie Chart + Positions Table (Side-by-Side)
# ============================================================================

col_left, col_right = st.columns([2, 3])

with col_left:
    st.subheader("Sleeve Allocation")

    sleeve_data = {
        "Core": actual.get("core", 0),
        "Hızlı Büyüme": actual.get("hizli_buyume", 0),
        "Yüksek Kazanç": actual.get("yuksek_kazanc", 0),
        "Cash": plan.get("cash_reserve_pct", 0),
    }
    # Filter zero
    sleeve_data = {k: v for k, v in sleeve_data.items() if v > 0}

    fig_pie = go.Figure(data=[go.Pie(
        labels=list(sleeve_data.keys()),
        values=list(sleeve_data.values()),
        hole=0.4,
        marker=dict(colors=["#FFB700", "#00D4FF", "#FF6B6B", "#4ECDC4"]),
        textinfo="label+percent",
        textfont_size=14,
    )])
    fig_pie.update_layout(
        showlegend=False,
        height=400,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("Pozisyonlar")
    df = positions_to_df(plan)
    if not df.empty:
        df_display = df.copy()
        df_display["weight_pct"] = df_display["weight_pct"].apply(lambda x: f"{x:.2f}%")
        df_display["composite"] = df_display["composite"].apply(lambda x: f"{x:.2f}")
        df_display["capital_allocation_tl"] = df_display["capital_allocation_tl"].apply(
            lambda x: f"{x:,.0f}"
        )
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=400,
        )
    else:
        st.warning("No positions")


st.divider()


# ============================================================================
# Sleeve Composite Bar (Composite Score per Sleeve)
# ============================================================================

st.subheader("Sleeve Composite Distribution")

if not df.empty:
    fig_bar = px.bar(
        df,
        x="ticker",
        y="composite",
        color="sleeve",
        color_discrete_map={
            "core": "#FFB700",
            "hizli_buyume": "#00D4FF",
            "yuksek_kazanc": "#FF6B6B",
        },
        labels={"composite": "Pentagon Composite", "ticker": "Ticker"},
        height=400,
    )
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(30,30,46,0.5)",
        font_color="#FAFAFA",
        xaxis=dict(tickangle=-45),
    )
    st.plotly_chart(fig_bar, use_container_width=True)


st.divider()


# ============================================================================
# Pentagon Radar (Selected Ticker)
# ============================================================================

st.subheader("Pentagon Scoring — Ticker Drill-Down")

if not df.empty:
    selected_ticker = st.selectbox(
        "Ticker seç",
        df["ticker"].tolist(),
        index=0,
    )

    batch = load_latest_batch()
    pentagon = get_pentagon_for_ticker(batch, selected_ticker)

    if pentagon:
        col_radar, col_info = st.columns([2, 1])

        with col_radar:
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=[
                    pentagon["value"],
                    pentagon["growth"],
                    pentagon["quality"],
                    pentagon["momentum"],
                    pentagon["risk"],
                ],
                theta=["Value", "Growth", "Quality", "Momentum", "Risk"],
                fill="toself",
                line=dict(color="#FFB700", width=2),
                fillcolor="rgba(255, 183, 0, 0.3)",
                name=selected_ticker,
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100],
                                     gridcolor="rgba(255,255,255,0.2)"),
                    angularaxis=dict(gridcolor="rgba(255,255,255,0.2)"),
                    bgcolor="rgba(30,30,46,0.5)",
                ),
                showlegend=False,
                height=400,
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with col_info:
            st.markdown(f"**{selected_ticker} Pentagon**")
            st.markdown(f"- **Lifecycle:** `{pentagon['lifecycle_stage']}`")
            st.markdown(f"- **Composite:** `{pentagon['composite']:.2f}`")
            st.markdown(f"- **Value:** `{pentagon['value']:.1f}`")
            st.markdown(f"- **Growth:** `{pentagon['growth']:.1f}`")
            st.markdown(f"- **Quality:** `{pentagon['quality']:.1f}`")
            st.markdown(f"- **Momentum:** `{pentagon['momentum']:.1f}` (parking)")
            st.markdown(f"- **Risk:** `{pentagon['risk']:.1f}`")
    else:
        st.info(f"Pentagon scores yüklenemedi {selected_ticker}")


# ============================================================================
# Sidebar Info
# ============================================================================

with st.sidebar:
    st.divider()
    st.markdown("### Profile Info")
    st.caption(f"Profile: **{profile}**")
    st.caption(f"Total Capital: TL {plan.get('total_capital_tl', 0):,.0f}")
    st.caption(f"Positions: {plan.get('total_positions', 0)}")

    st.divider()
    sb = plan.get("sleeve_breakdown", {})
    st.markdown("**Sleeve Counts:**")
    for k, v in sb.items():
        st.caption(f"- {k}: {v}")
