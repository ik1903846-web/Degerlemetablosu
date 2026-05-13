"""
Watchlist — Phase 7.3 (kisisel takip + Damodaran alert)

Bolumler:
  1. Watchlist tablo (mevcut ticker + sinyal stack 5-katmanli)
  2. Ticker ekle form
  3. Alert paneli (3 type)
  4. PRIMARY_TARGET quick-add (10 ticker tek tikla)
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_APPS = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = REPO_APPS / "api" / "outputs"

_FRONTEND_DIR = Path(__file__).resolve().parents[1]
if str(_FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(_FRONTEND_DIR))

from utils.watchlist_storage import (  # noqa: E402
    load_watchlist, add_ticker, remove_ticker, watchlist_count,
)
from utils.alert_checker import check_alerts  # noqa: E402
from utils.data_loader import load_latest_v4_batch  # noqa: E402


st.set_page_config(page_title="Watchlist — REELDEĞER", page_icon="📋", layout="wide")

st.title("📋 Watchlist Manager")
st.markdown("**Phase 7.3 — Kisisel takip + Damodaran alert sistemi**")
st.caption("Damodaran '10-15 hisse izlemesi' disiplin. Alert: PRICE_DROP / DISPERSION / VALUE_TRAP.")


# ============================================================================
# Load batch + watchlist
# ============================================================================

batch = load_latest_v4_batch()
if not batch:
    st.error("turkey_v4_batch.json yuklenemedi.")
    st.stop()

ticker_records = batch.get("tickers", [])
by_ticker = {r.get("ticker"): r for r in ticker_records}

wl = load_watchlist()
wl_tickers = wl.get("tickers", [])

st.divider()


# ============================================================================
# 1. PRIMARY_TARGET Quick-add
# ============================================================================

st.subheader("🎯 Phase 7.2 PRIMARY_TARGET — Quick-add")

primary_targets = [
    r for r in ticker_records
    if r.get("final_recommendation") == "PRIMARY_TARGET"
]

if primary_targets:
    st.caption(
        f"{len(primary_targets)} PRIMARY_TARGET ticker (sinyal stack tam senkron). "
        f"Tek tikla watchlist'e ekle:"
    )
    pt_cols = st.columns(min(5, len(primary_targets)))
    for i, pt in enumerate(primary_targets):
        with pt_cols[i % len(pt_cols)]:
            tic = pt.get("ticker")
            already = tic in wl_tickers
            mos = pt.get("mos_min")
            mos_s = f"{mos*100:+.0f}%" if mos else "n/a"
            label = f"✓ {tic}" if already else f"➕ {tic}"
            disabled = already
            help_text = f"MoS {mos_s} · cat {pt.get('catalyst_score', '?')}/50"
            if st.button(label, key=f"add_{tic}", disabled=disabled, help=help_text):
                if add_ticker(tic, added_date=str(date.today()), notes="PRIMARY_TARGET quick-add"):
                    st.success(f"{tic} watchlist'e eklendi")
                    st.rerun()
else:
    st.info("PRIMARY_TARGET ticker yok bu regen'de.")

st.divider()


# ============================================================================
# 2. Alert Paneli
# ============================================================================

st.subheader("🚨 Alert Paneli")

alerts = check_alerts(wl_tickers, ticker_records)
if not alerts:
    st.success("✓ Aktif alert yok — watchlist sakin.")
else:
    high = [a for a in alerts if a["severity"] == "HIGH"]
    medium = [a for a in alerts if a["severity"] == "MEDIUM"]
    low = [a for a in alerts if a["severity"] == "LOW"]

    if high:
        st.error(f"🚨 {len(high)} HIGH-priority alert")
        for a in high:
            st.warning(f"**{a['ticker']}** [{a['alert_type']}] — {a['message']}")
    if medium:
        st.info(f"⚠️ {len(medium)} MEDIUM-priority alert")
        for a in medium:
            st.write(f"• **{a['ticker']}** [{a['alert_type']}] — {a['message']}")
    if low:
        st.caption(f"ℹ️ {len(low)} LOW-priority alert")
        for a in low:
            st.caption(f"  {a['ticker']} [{a['alert_type']}] — {a['message']}")

st.divider()


# ============================================================================
# 3. Watchlist Tablo
# ============================================================================

st.subheader(f"📋 Watchlist ({len(wl_tickers)} ticker)")

if not wl_tickers:
    st.info("Watchlist bos. Yukaridan PRIMARY_TARGET ticker ekle veya asagidan manuel.")
else:
    rows = []
    for tic in wl_tickers:
        r = by_ticker.get(tic, {})
        added = wl.get("added_dates", {}).get(tic, "?")
        entry = wl.get("entry_targets", {}).get(tic)
        notes = wl.get("notes", {}).get(tic, "")
        rows.append({
            "Ticker": tic,
            "Eklendi": added,
            "Anlik Fiyat": r.get("current_price_tl"),
            "Intrinsic": r.get("intrinsic_per_share_tl"),
            "MoS %": (r.get("mos_min") or 0) * 100 if r.get("mos_min") else None,
            "Composite": r.get("composite_signal") or "—",
            "Catalyst": r.get("catalyst_score"),
            "Final Rec": r.get("final_recommendation") or "—",
            "Entry Target": entry,
            "Notes": notes,
        })
    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.format({
            "Anlik Fiyat": "{:,.2f}",
            "Intrinsic": "{:,.2f}",
            "MoS %": "{:+.1f}%",
            "Entry Target": "{:,.2f}",
        }, na_rep="—"),
        use_container_width=True,
        hide_index=True,
    )

    # Remove buttons
    st.caption("Watchlist'ten cikar:")
    rm_cols = st.columns(min(5, len(wl_tickers)))
    for i, tic in enumerate(wl_tickers):
        with rm_cols[i % len(rm_cols)]:
            if st.button(f"🗑️ {tic}", key=f"rm_{tic}"):
                if remove_ticker(tic):
                    st.success(f"{tic} watchlist'ten cikarildi")
                    st.rerun()

st.divider()


# ============================================================================
# 4. Manuel Ticker Ekle
# ============================================================================

st.subheader("➕ Manuel Ticker Ekle")

with st.form("add_ticker_form"):
    col1, col2 = st.columns([1, 2])
    with col1:
        new_ticker = st.text_input("Ticker (örn. ARCLK)", value="").strip().upper()
        entry_target = st.number_input("Entry Target (opsiyonel)", min_value=0.0, value=0.0, step=1.0)
    with col2:
        notes_input = st.text_area("Notlar (Damodaran tezi)", value="", height=100)
    submitted = st.form_submit_button("Watchlist'e Ekle")
    if submitted:
        if not new_ticker:
            st.error("Ticker bos.")
        elif new_ticker not in by_ticker:
            st.error(f"{new_ticker} BIST universe'de YOK.")
        elif new_ticker in wl_tickers:
            st.warning(f"{new_ticker} zaten watchlist'te.")
        else:
            ok = add_ticker(
                new_ticker,
                entry_target=entry_target if entry_target > 0 else None,
                notes=notes_input or None,
                added_date=str(date.today()),
            )
            if ok:
                st.success(f"{new_ticker} watchlist'e eklendi")
                st.rerun()
            else:
                st.error("Kayit basarisiz.")


# Sidebar
with st.sidebar:
    st.markdown("### Watchlist")
    st.metric("Toplam", watchlist_count())
    st.metric("Aktif Alert", len(alerts))
    st.caption("Damodaran 10-15 hisse izlemesi disiplin.")
