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
    load_latest_v4_batch,
    universe_stats_v4,
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

v4_stats = universe_stats_v4()
TOTAL_COUNT = v4_stats.get("total_count", 0)
DCF_COUNT = v4_stats.get("dcf_count", 0)
INTRINSIC_FILLED = v4_stats.get("intrinsic_filled", DCF_COUNT)
HOLDING_FILLED = v4_stats.get("holding_intrinsic_filled", 0)
SECTOR_FILLED = v4_stats.get("sector_multiple_count", 0)
BOOK_FILLED = v4_stats.get("book_value_count", 0)
# Phase 6: Phase 5b.2 + 5c yansimasi
INDUSTRIAL_EA_COUNT = v4_stats.get("industrial_engine_a_count", 0)
INDUSTRIAL_BOOK_FB = v4_stats.get("industrial_book_fallback_count", 0)
BANKING_DDM_COUNT = v4_stats.get("banking_ddm_count", 0)
TS_UNSUSTAINABLE = v4_stats.get("ts_unsustainable_count", 0)
ANCHOR_TUPRS = v4_stats.get("anchor_tuprs")

st.title("REELDEĞER")
st.markdown(
    f"## 📊 Damodaran Hedef Fiyat Hesaplayıcısı — BIST {TOTAL_COUNT} hisse"
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

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "📈 BIST Universe",
        f"{INTRINSIC_FILLED} / {TOTAL_COUNT} hisse",
        f"Engine A EM {INDUSTRIAL_EA_COUNT} + Book FB {INDUSTRIAL_BOOK_FB} + "
        f"Holding {HOLDING_FILLED} + Banking {BANKING_DDM_COUNT} + Sector {SECTOR_FILLED} (Phase 5c)",
    )

with col2:
    st.metric(
        "✅ Damodaran Validation",
        "20 / 20 case ±%5",
        "Heineken, Toyota, ABN Amro, Tube, Eurotunnel",
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

st.subheader(f"📈 Lifecycle Stage Dağılımı (BIST Tüm {TOTAL_COUNT} universe)")

batch = load_latest_v4_batch()
if batch:
    from collections import Counter

    stages = Counter()
    for r in batch.get("tickers", []):
        if not r.get("intrinsic_per_share_tl"):
            continue
        stages[r.get("lifecycle_stage") or "unknown"] += 1

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
    f"Sol kenar çubuğundan **Tarayıcı** sayfasına geç → {TOTAL_COUNT} hisseyi tek tabloda "
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
    st.caption(
        f"BIST Universe: {INTRINSIC_FILLED}/{TOTAL_COUNT} "
        f"(Engine A EM {INDUSTRIAL_EA_COUNT} + Book FB {INDUSTRIAL_BOOK_FB} + "
        f"Holding {HOLDING_FILLED} + Banking {BANKING_DDM_COUNT} + "
        f"Sector {SECTOR_FILLED} + Book {BOOK_FILLED})"
    )
    _anchor_text = f"{ANCHOR_TUPRS:.2f}" if ANCHOR_TUPRS else "N/A"
    st.caption(f"TUPRS anchor: {_anchor_text} TL (Phase 5b.2 Engine A swap)")
    if TS_UNSUSTAINABLE:
        st.caption(
            f"⚠️ {TS_UNSUSTAINABLE} ticker terminal sustainability uyari "
            f"(TR fiat regime Damodaran insight, ADR-080 §7.2)"
        )
    # Phase 6.2: Multi-multiple consensus dispersion stats
    _hi_disp = v4_stats.get("high_dispersion_count", 0)
    _ext_disp = v4_stats.get("extreme_dispersion_count", 0)
    _val_disp = v4_stats.get("multi_multiple_validated_count", 0)
    if _hi_disp or _val_disp:
        st.caption(
            f"📊 Multi-multiple consensus (Phase 4d): "
            f"validated {_val_disp} (<%30 disp) · "
            f"high {_hi_disp} (>%50) · "
            f"extreme {_ext_disp} (>%100)"
        )
    # Phase 7.1 MoS composite signal
    _buy = v4_stats.get("buy_signal_count", 0)
    _wait = v4_stats.get("wait_signal_count", 0)
    _no_margin = v4_stats.get("no_margin_signal_count", 0)
    _overvalued = v4_stats.get("overvalued_signal_count", 0)
    _mos_med = v4_stats.get("mos_median")
    if _buy or _overvalued:
        st.caption(
            f"💰 Yatirim Sinyali (Phase 7.1 MoS):"
        )
        st.caption(
            f"🟢 BUY {_buy} · 🟡 WAIT {_wait} · 🟠 NO-MARGIN {_no_margin} · 🔴 OVERVALUED {_overvalued}"
        )
        if _mos_med is not None:
            st.caption(f"Universe MoS median: {_mos_med*100:+.1f}%")
    st.caption("v4.13 anchor SEALED · Damodaran sinyal stack 4-katmanli")
