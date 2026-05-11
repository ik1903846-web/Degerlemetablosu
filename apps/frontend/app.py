"""
REELDEĞER — Damodaran Hedef Fiyat Hesaplayıcısı.

BIST 559 hisse için Aswath Damodaran metodolojisiyle DCF intrinsic value
+ lifecycle classification + sektörel beta. Yatırım otomasyonu DEĞİL —
hedef fiyat hesaplayıcısı.

Asıl ürün: 🔍 Tarayıcı sayfası (5 sütun tablo).
"""

from __future__ import annotations

import hmac

import streamlit as st

from utils.data_loader import (
    load_latest_batch,
    universe_stats,
)
from utils.freshness import render_freshness_banner


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
    "## 📊 Damodaran Hedef Fiyat Hesaplayıcısı — BIST 559 hisse"
)
st.caption(
    "Aswath Damodaran metodolojisiyle 5-stage DCF + Pentagon scoring + lifecycle "
    "classification. **Yatırım otomasyonu DEĞİL — hedef fiyat hesaplayıcısı.** "
    "Asıl ürün: 🔍 Tarayıcı sayfası."
)

render_freshness_banner()

st.divider()


# ============================================================================
# 3 KPI (Hesaplayıcı Odaklı)
# ============================================================================

stats = universe_stats()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "📈 BIST Universe",
        f"{stats.get('successful', 0)} / {stats.get('total_tickers', 0)} hisse",
        f"{stats.get('successful', 0) / max(stats.get('total_tickers', 1), 1) * 100:.0f}% DCF runnable",
    )

with col2:
    st.metric(
        "✅ Damodaran Validation",
        "20 / 20 case ±%5",
        "Heineken, Toyota, ABN Amro, Tube, TUPRS anchor",
    )

with col3:
    st.metric(
        "🔄 Lifecycle Stages",
        "6 stage classified",
        "Young / High Growth / Mature / Decline / Distress",
    )

st.divider()


# ============================================================================
# Validation Case Listesi (Damodaran Reference)
# ============================================================================

st.subheader("✅ Damodaran Reference Validation Cases (20/20 PASS ±%5)")

VALIDATION_CASES = [
    ("Heineken",   "€59.65",   "Industrial FCFF 2-stage",    "Faz 1.3"),
    ("Toyota 2009","¥4,737",   "Cyclical asymmetric cap",    "Faz 2.6"),
    ("ABN Amro",   "€30.87",   "Banking DDM 2-stage",        "Faz 1.4"),
    ("Tube India", "₹61.55",   "Emerging market DCF",        "Faz 1.5"),
    ("TUPRS",      "187.10 TL","BIST cyclical anchor (50+)", "Faz 2.4.5"),
    ("Eurotunnel", "£122M",    "Distress equity-as-call BS", "Faz 7.2 (±0.06%)"),
    ("LVS 2009",   "$1.92/sh", "Distress sanity (post-crisis)","Faz 7"),
    ("Damodaran sector betas", "210+", "Unlevered β fetch", "Faz 2.4.5 DB"),
]

import pandas as pd

vc_df = pd.DataFrame(VALIDATION_CASES, columns=[
    "Case", "Damodaran Reference", "Methodology", "Validated Faz"
])
st.dataframe(vc_df, use_container_width=True, hide_index=True)

st.caption(
    "💡 Doğru success metric: **DCF accuracy ±%5 vs Damodaran reference**, "
    "**not** backtest portfolio returns. REELDEĞER amacı Damodaran replication "
    "(Lesson #21)."
)

st.divider()


# ============================================================================
# Lifecycle Distribution (Mevcut Universe)
# ============================================================================

st.subheader("📈 Lifecycle Stage Dağılımı (BIST Tüm 559 universe)")

batch = load_latest_batch()
if batch:
    from collections import Counter

    stages = Counter()
    for r in batch.get("reports", []):
        if not r.get("success"):
            continue
        lc = r.get("lifecycle") or {}
        stages[lc.get("stage", "unknown")] += 1

    if stages:
        STAGE_DISPLAY = {
            "mature_stable":   "⭐⭐⭐⭐⭐ Mature Stable",
            "mature_growth":   "⭐⭐⭐⭐ Mature Growth",
            "high_growth":     "⭐⭐⭐ High Growth",
            "young":           "⭐⭐ Young",
            "decline":         "⭐ Decline",
            "distress":        "⚠️ Distress",
            "unknown":         "— Unknown",
        }

        rows = []
        total = sum(stages.values())
        for stage, label in STAGE_DISPLAY.items():
            count = stages.get(stage, 0)
            pct = count / max(total, 1) * 100
            rows.append({
                "Stage": label,
                "Count": count,
                "Pct": f"{pct:.1f}%",
            })

        stage_df = pd.DataFrame(rows)
        st.dataframe(stage_df, use_container_width=True, hide_index=True)

st.divider()


# ============================================================================
# Tarayıcı Yönlendirme
# ============================================================================

st.subheader("🔍 Asıl Ürün: Tarayıcı")
st.markdown(
    "Sol kenar çubuğundan **Tarayıcı** sayfasına geç → 559 hisseyi tek tabloda "
    "DCF intrinsic value + güncel fiyat + upside %, en ucuz hisseler üstte."
)
st.info(
    "🎯 **Doğru kullanım:** Tarayıcıda upside ≥ %30 (deep value) + lifecycle "
    "⭐⭐⭐⭐ (Mature Growth/Stable) ticker'ları manuel inceleme listene al. "
    "Damodaran reference validation case'lerine göre DCF güvenilirliği zaten ±%5."
)


# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    st.markdown("### REELDEĞER")
    st.caption("Damodaran Hedef Fiyat Hesaplayıcısı")
    st.divider()
    st.markdown("**Sayfalar:**")
    st.markdown("- 🏠 Home (bu sayfa)")
    st.markdown("- 🔍 **Tarayıcı** ← asıl ürün")
    st.markdown("- 📚 Lessons")
    st.divider()
    st.caption(f"BIST Universe: {stats.get('successful', 0)} hisse DCF runnable")
    st.caption("TUPRS anchor: 187.10 TL (50+ commit INTACT)")
    st.caption("v3.0 · Damodaran replication odaklı")
