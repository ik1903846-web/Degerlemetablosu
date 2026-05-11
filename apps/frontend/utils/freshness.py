"""
Freshness Warning Banner — Evre 2 Adim 2
=========================================

turkey_v4_batch.json fetch_date'ine gore 3 katmanli yas uyarisi.
Adim 1 Gate D ile uyumlu threshold (7d WARN, 14d FAIL).

Usage:
    from utils.freshness import render_freshness_banner
    render_freshness_banner()                # default render
    render_freshness_banner(force_days=8)    # debug: zorlanmis day count
"""

from datetime import date
from pathlib import Path
import json
import streamlit as st


# Repo root: utils/ -> frontend/ -> apps/ -> repo_root
BATCH_PATH = Path(__file__).resolve().parents[3] / "apps/api/outputs/turkey_v4_batch.json"

WARN_THRESHOLD_DAYS = 7
ERROR_THRESHOLD_DAYS = 14


@st.cache_data(ttl=300)
def _read_fetch_date():
    """batch.json'dan fetch_date oku. Hata/yok durumunda None."""
    try:
        if not BATCH_PATH.exists():
            return None
        d = json.loads(BATCH_PATH.read_text(encoding="utf-8"))
        fetch_date_str = d.get('fetch_date')
        if not fetch_date_str:
            return None
        return date.fromisoformat(fetch_date_str)
    except Exception:
        return None


def render_freshness_banner(show_caption_when_fresh=True, force_days=None):
    """3 katmanli freshness banner render.

    Threshold (Adim 1 Gate D ile uyumlu):
        0 gun:    Hicbir sey (fresh)
        1-6 gun:  st.caption (small text)
        7-13 gun: st.warning (sari)
        14+ gun:  st.error (kirmizi)

    Args:
        show_caption_when_fresh: 1-6 gun arasi caption goster (default True)
        force_days: Debug — gercek fetch_date yerine bu day count kullan
    """
    if force_days is not None:
        stale_days = force_days
        fetch_date_label = "DEBUG"
    else:
        fetch_date = _read_fetch_date()
        if fetch_date is None:
            return
        stale_days = (date.today() - fetch_date).days
        fetch_date_label = fetch_date.isoformat()

    if stale_days < 0:
        return

    if stale_days >= ERROR_THRESHOLD_DAYS:
        st.error(
            f"Veri {stale_days} gun eski (>{ERROR_THRESHOLD_DAYS}d). "
            f"Acil regen gerekli. Son regen: {fetch_date_label}. "
            f"CI validation muhtemelen issue acti."
        )
    elif stale_days >= WARN_THRESHOLD_DAYS:
        st.warning(
            f"Veri {stale_days} gun eski (>{WARN_THRESHOLD_DAYS}d). "
            f"Daily regen kacirilmis olabilir. Son regen: {fetch_date_label}. "
            f"Lokal: python apps/api/_regen_phase1.py + git push"
        )
    elif show_caption_when_fresh and stale_days > 0:
        st.caption(f"Veri {stale_days} gun eski (son regen: {fetch_date_label})")
