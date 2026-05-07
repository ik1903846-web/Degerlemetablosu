"""
REELDEĞER — Damodaran-Aligned BIST Valuation Platform.

Streamlit dashboard home page.
Marathon (24 Nis → 7 May 2026, 160+ commit) sonucu UI'ı.
"""

from __future__ import annotations

import hmac

import streamlit as st

from utils.data_loader import (
    load_latest_usd_backtest,
    load_all_profiles,
    universe_stats,
)


# ============================================================================
# Page Config (must run first, before any st.* call)
# ============================================================================

st.set_page_config(
    page_title="REELDEĞER — Damodaran BIST",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# Password Auth (Faz 10 ADIM 1.B — Streamlit Cloud private access)
# ============================================================================

def _check_password() -> bool:
    """st.secrets['auth']['password'] ile karşılaştırma. Doğru ise True."""

    def password_entered() -> None:
        try:
            expected = st.secrets["auth"]["password"]
        except (KeyError, FileNotFoundError):
            st.session_state["password_correct"] = None
            return
        if hmac.compare_digest(st.session_state.get("password", ""), expected):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("## 🔐 REELDEĞER — Private Access")
        st.text_input(
            "Şifre",
            type="password",
            on_change=password_entered,
            key="password",
        )
        return False

    state = st.session_state["password_correct"]
    if state is None:
        st.error(
            "secrets.toml [auth] password yapılandırılmamış. "
            "Streamlit Cloud → Settings → Secrets ekle."
        )
        return False
    if state is False:
        st.markdown("## 🔐 REELDEĞER — Private Access")
        st.text_input(
            "Şifre",
            type="password",
            on_change=password_entered,
            key="password",
        )
        st.error("😕 Yanlış şifre")
        return False
    return True


if not _check_password():
    st.stop()


# ============================================================================
# Header
# ============================================================================

st.title("REELDEĞER")
st.markdown(
    "**Damodaran-Aligned BIST Valuation + Portfolio Construction Platform**"
)
st.caption(
    "v2.2 · 4-stage DCF (Industrial/Banking/Holdings/Cyclical) · "
    "Pentagon scoring · 3-Sleeve portfolio · Backtest 2021-Q2 → 2026-Q1"
)

st.divider()


# ============================================================================
# Hero Metrics
# ============================================================================

usd = load_latest_usd_backtest()
profiles = load_all_profiles()
stats = universe_stats()

if usd:
    backtests = usd.get("backtests_usd", [])
    benchmarks = usd.get("benchmarks_usd", [])

    # Konservatif zero (en güçlü profile)
    konser_zero = next(
        (b for b in backtests
         if b["profile"] == "konservatif" and b["cost_model"] == "zero"),
        None,
    )
    xu100 = next((b for b in benchmarks if b["label"] == "XU100"), None)
    spy = next((b for b in benchmarks if b["label"] == "SPY"), None)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if konser_zero:
            ann = konser_zero["usd_annualized"] * 100
            st.metric(
                "Konservatif USD Ann",
                f"{ann:+.2f}%/yr",
                "★★★ Best profile" if ann > 15 else None,
            )

    with col2:
        if konser_zero and xu100:
            delta = (konser_zero["usd_annualized"] -
                     xu100["usd_annualized"]) * 100
            st.metric(
                "vs XU100 USD",
                f"{delta:+.2f}pp",
                "BEAT ★" if delta > 0 else "underperform",
            )

    with col3:
        if konser_zero and spy:
            delta = (konser_zero["usd_annualized"] -
                     spy["usd_annualized"]) * 100
            st.metric(
                "vs SPY USD",
                f"{delta:+.2f}pp",
                "BEAT ★" if delta > 0 else "underperform",
            )

    with col4:
        st.metric(
            "Universe",
            f"{stats['successful']}/{stats['total_tickers']} ticker",
            f"{stats['successful']/max(stats['total_tickers'],1)*100:.0f}% success",
        )

st.divider()


# ============================================================================
# 3 Profile Comparison
# ============================================================================

st.subheader("3 Risk Profile USD Performance (2021-Q2 → 2026-Q1)")

if usd:
    import pandas as pd

    backtests = usd.get("backtests_usd", [])
    benchmarks = usd.get("benchmarks_usd", [])

    rows = []
    for bt in backtests:
        rows.append({
            "Profile": bt["profile"].capitalize(),
            "Cost": bt["cost_model"],
            "USD Cum %": f"{bt['usd_cumulative']*100:+.2f}",
            "USD Ann %/yr": f"{bt['usd_annualized']*100:+.2f}",
            "Sharpe": f"{bt['usd_sharpe']:.2f}" if bt.get("usd_sharpe") else "n/a",
            "Max DD %": f"{bt['usd_max_drawdown']*100:+.2f}",
        })

    for bm in benchmarks:
        rows.append({
            "Profile": f"📈 {bm['label']}",
            "Cost": "benchmark",
            "USD Cum %": f"{bm['usd_cumulative']*100:+.2f}",
            "USD Ann %/yr": f"{bm['usd_annualized']*100:+.2f}",
            "Sharpe": f"{bm['usd_sharpe']:.2f}" if bm.get("usd_sharpe") else "n/a",
            "Max DD %": f"{bm['usd_max_drawdown']*100:+.2f}",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================================
# 15 Damodaran Lesson Preview (Top 5)
# ============================================================================

st.subheader("Top Damodaran Lessons (15 keşif, /Lessons sayfasında tam liste)")

LESSON_PREVIEW = [
    ("#15", "Faz 4.16 ★★★", "Empty sleeve redistribution Core PRIORITY"),
    ("#14", "Faz 4.14", "Allocation > Filter — sleeve target lever"),
    ("#12", "Faz 4.6", "Universe expansion PROFILE-DEPENDENT"),
    ("#10", "Faz 4.7", "Hypothesis falsification > methodology force-fit"),
    ("#1",  "Faz 2.5", "Holdings cannot be valued like industrial firms"),
]

for num, faz, summary in LESSON_PREVIEW:
    col1, col2, col3 = st.columns([1, 2, 6])
    with col1:
        st.markdown(f"**{num}**")
    with col2:
        st.caption(faz)
    with col3:
        st.markdown(summary)


# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    st.markdown("### REELDEĞER")
    st.caption("Damodaran-aligned BIST valuation")
    st.divider()
    st.markdown("**Sayfalar:**")
    st.markdown("- 🏠 Home (bu sayfa)")
    st.markdown("- 📊 Portfolio")
    st.markdown("- 📈 Backtest")
    st.markdown("- 📚 Lessons")
    st.divider()
    st.caption(f"Universe: {stats.get('successful', 0)} ticker successful")
    st.caption("TUPRS anchor: 187.10 TL (39 commit INTACT)")
