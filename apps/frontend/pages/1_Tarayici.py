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

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================================
# Path Resolution (Streamlit Cloud + Local uyumlu)
# ============================================================================
# apps/frontend/pages/1_Tarayici.py
#   parents[0] = pages, parents[1] = frontend, parents[2] = apps
# Streamlit Cloud working dir: /mount/src/degerlemetablosu
# Local working dir: C:/Users/unutu/Desktop/abiminprojev2

REPO_APPS = Path(__file__).resolve().parents[2]              # apps/
OUTPUTS_DIR = REPO_APPS / "api" / "outputs"


# ─────────────────────────────────────────────────────────────────
# HOOK[Audit Session 4]: Stage 2/3 Banner Integration
# ─────────────────────────────────────────────────────────────────
#
# TODO: Lifecycle classifier sonucu Stage 2 (Young Growth) veya
# Stage 3 (High Growth) ise, ticker seçildiğinde Mature DCF render
# etmeden ÖNCE şu banner gösterilmeli:
#
#   if get_lifecycle(ticker) in ("Stage 2", "Stage 3"):
#       st.error(
#           f"⚠️ {ticker} bir {get_lifecycle(ticker)} şirketidir. "
#           f"Mature DCF bu evre için yanlış model "
#           f"(Damodaran §4.1). Lütfen 🚀 Hızlı Büyüme "
#           f"sekmesinde değerleyin."
#       )
#       st.page_link(
#           "pages/3_Hizli_Buyume.py",
#           label="🚀 Hızlı Büyüme sekmesine git",
#       )
#       st.stop()  # Mature DCF render'ı durdur
#
# Implementation: docs/young_growth_tab_spec.md §2 + Hafta 1
# Audit dependency: docs/audit_decision_v4.md Faz B1 Adım 1-4
#                   (lifecycle classifier'ın Stage 2/3 doğru
#                    sınıflandırması için Damodaran Şub 2026
#                    parametrelerine bağlı)
#
# Status: HOOK READY — implementation Hafta 1 (3_Hizli_Buyume.py
# placeholder dolulduktan sonra aktif edilir)
# ─────────────────────────────────────────────────────────────────


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
def _load_scanner_df() -> tuple[pd.DataFrame, str]:
    """Batch JSON → 5-column DataFrame (ticker/price/intrinsic/upside/lifecycle).

    Streamlit Cloud-compatible explicit path (REPO_APPS / api / outputs).
    Returns (df, debug_message).
    """
    if not OUTPUTS_DIR.exists():
        debug = (
            f"❌ OUTPUTS_DIR yok: `{OUTPUTS_DIR}`\n"
            f"REPO_APPS: `{REPO_APPS}` (exists={REPO_APPS.exists()})"
        )
        return pd.DataFrame(), debug

    files = sorted(
        OUTPUTS_DIR.glob("bist_batch_LIVE_*.json"),
        reverse=True,
    )
    if not files:
        contents = list(OUTPUTS_DIR.iterdir())[:10]
        debug = (
            f"❌ bist_batch_LIVE_*.json bulunamadı.\n"
            f"Aranan path: `{OUTPUTS_DIR}`\n"
            f"Klasör içeriği (ilk 10): {[p.name for p in contents]}"
        )
        return pd.DataFrame(), debug

    latest = files[0]
    try:
        batch = json.loads(latest.read_text(encoding="utf-8"))
    except Exception as e:
        debug = f"❌ JSON parse hatası ({latest.name}): {type(e).__name__}: {e}"
        return pd.DataFrame(), debug

    rows = []
    for r in batch.get("reports", []):
        if not r.get("success"):
            continue
        ticker = r.get("ticker", "")
        lc = r.get("lifecycle") or {}
        dcf = r.get("dcf") or {}
        market = r.get("market") or {}

        intrinsic = dcf.get("value_per_share_tl")
        # JSON field name: market.price_tl (NOT market_price_tl)
        price = market.get("price_tl") or market.get("market_price_tl")
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
    debug_ok = (
        f"✓ Source: `{latest.name}` "
        f"(reports {len(batch.get('reports', []))}, success {len(rows)})"
    )
    if df.empty:
        return df, debug_ok + " — ama success satırı yok"
    return (
        df.sort_values("upside_pct", ascending=False).reset_index(drop=True),
        debug_ok,
    )


# ============================================================================
# v4 KAP-Only Loader (Faz 11 v4.0 — Session 4C)
# ============================================================================

@st.cache_data(ttl=300)
def _load_scanner_df_v4() -> tuple[pd.DataFrame, str]:
    """KAP-only v4 batch JSON → 5-column DataFrame.

    apps/api/outputs/turkey_v4_batch.json (orchestrator_v4 output).
    """
    v4_path = OUTPUTS_DIR / "turkey_v4_batch.json"
    if not v4_path.exists():
        return pd.DataFrame(), f"❌ v4 batch yok: `{v4_path}`"
    try:
        batch = json.loads(v4_path.read_text(encoding="utf-8"))
    except Exception as e:
        return pd.DataFrame(), f"❌ v4 parse fail: {e}"

    rows = []
    for r in batch.get("tickers", []):
        intrinsic = r.get("intrinsic_per_share_tl")
        price = r.get("current_price_tl")
        upside = r.get("upside_pct")
        stage = (r.get("lifecycle_stage") or "unknown").lower()
        method = r.get("dcf_method") or "unknown"
        # Price yoksa skip (delisted/no_data)
        if price is None:
            continue
        # Intrinsic yoksa method'a göre tabloda göster
        if intrinsic is None:
            method_label = {
                "banking_skip":                       "Banking (4.5+)",
                "holding_sotp_pending":               "Holding SOTP (4.5+)",
                "fcff_negative_intrinsic_unsuitable": "Cyclical capex",
                "insurance_skip":                     "Insurance (parking)",
                "unknown_skip":                       "Insurance/unknown",
            }.get(method, f"Skip ({method[:20]})")
            rows.append({
                "ticker": r.get("ticker", ""),
                "current_price_tl": float(price),
                "intrinsic_value_tl": None,
                "upside_pct": None,
                "lifecycle_stage": stage,
                "lifecycle_label": f"{STAGE_STARS.get(stage, '—')} {STAGE_LABELS.get(stage, '?')}",
                "method": method_label,
            })
            continue
        rows.append({
            "ticker": r.get("ticker", ""),
            "current_price_tl": float(price),
            "intrinsic_value_tl": float(intrinsic),
            "upside_pct": float(upside) if upside is not None else 0.0,
            "lifecycle_stage": stage,
            "lifecycle_label": f"{STAGE_STARS.get(stage, '—')} {STAGE_LABELS.get(stage, '?')}",
            "method": "DCF",
        })
    df = pd.DataFrame(rows)
    debug = (
        f"✓ v4 KAP-Only: {batch.get('total_count',0)} ticker, "
        f"{batch.get('dcf_count',0)} DCF, "
        f"anchor TUPRS={batch.get('anchor_tuprs','?')}"
    )
    if df.empty:
        return df, debug
    return df.sort_values("upside_pct", ascending=False).reset_index(drop=True), debug


# ============================================================================
# A/B Switch — Sidebar
# ============================================================================

st.sidebar.markdown("### 🔀 Sistem Seçimi")
v4_path = OUTPUTS_DIR / "turkey_v4_batch.json"
v4_available = v4_path.exists()

use_v4 = st.sidebar.checkbox(
    "🆕 KAP-Only Sistem (BETA)",
    value=v4_available,
    disabled=not v4_available,
    help=(
        "**Yeni:** KAP financials + yfinance fiyat + Türkiye-pure beta.\n"
        "**Eski:** İş Yatırım scrape (legacy fallback).\n\n"
        f"v4 batch: {'✓ mevcut' if v4_available else '✗ yok (eski sistem aktif)'}"
    ),
)

if use_v4:
    df, debug_msg = _load_scanner_df_v4()
    source_label = "🆕 KAP-Only v4 (BETA)"
else:
    df, debug_msg = _load_scanner_df()
    source_label = "📋 İş Yatırım v1 (legacy)"

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Veri Kaynakları")
if use_v4:
    st.sidebar.markdown(
        """
        - 💼 Finansallar: **KAP** (resmi)
        - 📈 Fiyat: **Yahoo Finance** (BIST lisanslı)
        - 📐 Beta: **Türkiye-pure** bottom-up
        - 🎯 DCF: **Damodaran 2-stage FCFF**
        - 🌀 Cyclical: **ADR-011 normalize**
        """
    )
else:
    st.sidebar.markdown(
        """
        - 📋 İş Yatırım scrape (legacy)
        - Damodaran Global EM beta
        """
    )

with st.sidebar.expander("ℹ️ Metodoloji"):
    st.markdown(
        """
        **Damodaran ADR-011 (Cyclical):**
        Petrol/Çelik/Otomotiv için Q-snapshot
        margin yerine sektör uplift normalize.

        **Türkiye-spesifik beta:**
        BIST sektör ortalaması (587 ticker × 44 sektör).

        **Anchor TUPRS = 187.10 TL** ✓
        """
    )

st.caption(f"Aktif kaynak: **{source_label}**")

if df.empty:
    st.error("Tarayıcı verisi bulunamadı.")
    st.code(debug_msg, language="text")
    st.caption(
        "DEBUG: Streamlit Cloud working dir vs path resolution analizi yukarıda. "
        "Beklenen path: `apps/api/outputs/bist_batch_LIVE_*.json` veya `turkey_v4_batch.json`."
    )
    st.stop()


# ============================================================================
# Sanity Bounds (Faz 10 — Lesson #22)
# ============================================================================
# DCF model bazı ticker'larda patlıyor (XBRL veri corruption, WACC kalibrasyon,
# reinvestment anomaly). Damodaran sanity:
#   upside > +500% → suspect (data quality issue)
#   upside > +1000% → exclude (model failure)
# Production listesinde -50% < upside < +500% varsayılan filter.

SANITY_LOWER_BOUND = -50.0
SANITY_UPPER_BOUND = 500.0

# DCF olmayan satırlar (intrinsic NULL) sanity filter'a tabi değil
# (banking/holding/cyclical_capex method flag ile gösteriliyor)
df_dcf = df[df["upside_pct"].notna()]
df_skip = df[df["upside_pct"].isna()]

extreme_count = ((df_dcf["upside_pct"] > SANITY_UPPER_BOUND) |
                 (df_dcf["upside_pct"] < SANITY_LOWER_BOUND)).sum()

show_extreme = st.checkbox(
    f"⚠️ Şüpheli upside göster (debug, {extreme_count} hisse)",
    value=False,
    help=(
        f"Damodaran sanity: upside > +{SANITY_UPPER_BOUND:.0f}% genelde DCF model failure "
        "(XBRL veri kalitesi, WACC/reinvestment kalibrasyon hatası). "
        f"Default: {SANITY_LOWER_BOUND:.0f}% < upside < {SANITY_UPPER_BOUND:.0f}% gösterilir."
    ),
)

show_skip = st.checkbox(
    f"📋 Method skip ticker'ları göster ({len(df_skip)} hisse: banking/holding/cyclical)",
    value=False,
    help="Banking (4.5+ Excess Return), Holding (4.5+ SOTP), Cyclical (capex unsuitable) ticker'ları."
)

if not show_extreme:
    df_dcf = df_dcf[
        (df_dcf["upside_pct"] >= SANITY_LOWER_BOUND)
        & (df_dcf["upside_pct"] <= SANITY_UPPER_BOUND)
    ].reset_index(drop=True)
    if extreme_count > 0:
        st.caption(
            f"🔬 **Sanity filter aktif** — {extreme_count} şüpheli hisse gizlendi "
            f"(upside <{SANITY_LOWER_BOUND:.0f}% veya >{SANITY_UPPER_BOUND:.0f}%). "
            "Lesson #22 — DCF sanity bounds. Detay için ☑️ checkbox aktive et."
        )

# Method skip ticker'ları opsiyonel
if show_skip:
    df = pd.concat([df_dcf, df_skip], ignore_index=True)
else:
    df = df_dcf


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
