"""
Tarayıcı (Hisse Scanner) — Damodaran Hedef Fiyat Hesaplayıcısı.

Asıl ürün: BIST 559 hisse için Damodaran DCF intrinsic value + güncel fiyat
karşılaştırması, upside renkli, lifecycle stage yıldız etiketli.

5 sütun:
  1. ticker
  2. current_price_tl  (anlık fiyat, batch fetch)
  3. intrinsic_value_tl  (Damodaran DCF intrinsic, USD × güncel kur)
  4. upside_pct  (renkli: >30 yeşil, 15-30 sarı, 0-15 turuncu, <0 kırmızı)
  5. lifecycle_stage  (yıldız: Mature Stable ⭐⭐⭐⭐⭐ → Distress ⚠️)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Frontend utils path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.data_loader import load_latest_batch  # noqa: E402


# ============================================================================
# Page Config
# ============================================================================

st.set_page_config(
    page_title="Tarayıcı — REELDEĞER",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Hisse Tarayıcı")
st.markdown(
    "**Damodaran Hedef Fiyat Hesaplayıcısı — BIST 559 hisse**"
)
st.caption(
    "Tek tablo, 5 sütun. DCF intrinsic value × güncel fiyat → upside %. "
    "Default sıralama: en ucuz hisseler üstte."
)

st.divider()


# ============================================================================
# Lifecycle Stage → Yıldız Mapping
# ============================================================================

STAGE_STARS = {
    "mature_stable":   "⭐⭐⭐⭐⭐",
    "mature_growth":   "⭐⭐⭐⭐",
    "high_growth":     "⭐⭐⭐",
    "young":           "⭐⭐",
    "decline":         "⭐",
    "distress":        "⚠️",
    "unknown":         "—",
}

STAGE_LABELS = {
    "mature_stable":   "Mature Stable",
    "mature_growth":   "Mature Growth",
    "high_growth":     "High Growth",
    "young":           "Young",
    "decline":         "Decline",
    "distress":        "Distress",
    "unknown":         "Unknown",
}


# ============================================================================
# Data Load
# ============================================================================

@st.cache_data(ttl=300)
def _load_scanner_df() -> pd.DataFrame:
    """Batch JSON → 5-column DataFrame (ticker/price/intrinsic/upside/lifecycle)."""
    batch = load_latest_batch()
    if not batch:
        return pd.DataFrame()

    rows = []
    for r in batch.get("reports", []):
        if not r.get("success"):
            continue
        ticker = r.get("ticker", "")
        lc = r.get("lifecycle") or {}
        dcf = r.get("dcf") or {}
        market = r.get("market") or {}

        intrinsic = dcf.get("value_per_share_tl")
        price = market.get("market_price_tl")
        upside = market.get("upside_pct")
        stage = (lc.get("stage") or "unknown").lower()

        if intrinsic is None or price is None or upside is None:
            continue

        rows.append({
            "ticker": ticker,
            "current_price_tl": float(price),
            "intrinsic_value_tl": float(intrinsic),
            "upside_pct": float(upside),
            "lifecycle_stage": stage,
            "lifecycle_label": f"{STAGE_STARS.get(stage, '—')} {STAGE_LABELS.get(stage, '?')}",
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("upside_pct", ascending=False).reset_index(drop=True)


df = _load_scanner_df()

if df.empty:
    st.error(
        "Tarayıcı verisi bulunamadı. "
        "apps/api/outputs/bist_batch_LIVE_*.json dosyası gerekli."
    )
    st.stop()


# ============================================================================
# Search Box
# ============================================================================

search = st.text_input(
    "🔎 Ticker ara",
    value="",
    placeholder="GARAN, TUPRS, ASELS...",
    help="Ticker yazıp filtreleyebilirsin (case-insensitive).",
).strip().upper()

if search:
    df = df[df["ticker"].str.contains(search, case=False, na=False)]

# Tarayıcı başlık + sayım
total_rows = len(df)
st.caption(
    f"📊 **{total_rows} hisse listeleniyor** — sütun başlığına tıklayarak sırala."
)


# ============================================================================
# Color-coded Upside Display
# ============================================================================

def _upside_color(val: float) -> str:
    """Upside % → background renk (CSS)."""
    if val > 30:
        return "background-color: #1b5e20; color: #ffffff;"   # green
    if val > 15:
        return "background-color: #f9a825; color: #000000;"   # yellow
    if val > 0:
        return "background-color: #ef6c00; color: #ffffff;"   # orange
    return "background-color: #b71c1c; color: #ffffff;"       # red


# Display columns (lifecycle_label tek görünür sütun)
display_df = df[[
    "ticker",
    "current_price_tl",
    "intrinsic_value_tl",
    "upside_pct",
    "lifecycle_label",
]].copy()
display_df.columns = [
    "Ticker",
    "Anlık Fiyat (TL)",
    "Hedef Fiyat (TL)",
    "Upside %",
    "Yaşam Döngüsü",
]

styled = (
    display_df.style
    .format({
        "Anlık Fiyat (TL)": "{:,.2f}",
        "Hedef Fiyat (TL)": "{:,.2f}",
        "Upside %": "{:+.1f}%",
    })
    .map(_upside_color, subset=["Upside %"])
)

st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
    height=600,
)


# ============================================================================
# Footer Info
# ============================================================================

st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Toplam Değerlenen",
        f"{total_rows} hisse",
        f"BIST Tüm 559 universe içinden",
    )

with col2:
    deep_value = (df["upside_pct"] > 30).sum()
    st.metric(
        "🟢 Deep Value (>30%)",
        f"{deep_value} hisse",
        f"{deep_value/max(total_rows,1)*100:.0f}%",
    )

with col3:
    overvalued = (df["upside_pct"] < 0).sum()
    st.metric(
        "🔴 Overvalued (<0%)",
        f"{overvalued} hisse",
        f"{overvalued/max(total_rows,1)*100:.0f}%",
    )

st.caption(
    "**Renk kodu:** 🟢 >30% (deep value) · 🟡 15-30% (cazip) · "
    "🟠 0-15% (fair) · 🔴 <0% (overvalued)"
)
st.caption(
    "**Yaşam döngüsü:** ⭐⭐⭐⭐⭐ Mature Stable · ⭐⭐⭐⭐ Mature Growth · "
    "⭐⭐⭐ High Growth · ⭐⭐ Young · ⭐ Decline · ⚠️ Distress"
)
st.caption(
    "💡 REELDEĞER **Damodaran hedef fiyat hesaplayıcısı**dır — yatırım otomasyonu değil. "
    "Real money kararları için DCF anchor'larıyla manuel doğrulama yap."
)
