"""Phase 7.3 Watchlist persistent storage (user-local JSON).

Streamlit Cloud ephemeral filesystem — production icin Supabase/cloud DB
Phase 7.3.2 scope. Bu MVP lokal kullanim icin (Path.home() / .reeldeger).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


_WATCHLIST_DIR = Path.home() / ".reeldeger"
_WATCHLIST_FILE = _WATCHLIST_DIR / "watchlist.json"


def _default_watchlist() -> dict:
    return {
        "tickers": [],
        "added_dates": {},
        "entry_targets": {},
        "notes": {},
    }


def load_watchlist() -> dict:
    """Load watchlist from user-local JSON; returns empty if none."""
    if not _WATCHLIST_FILE.exists():
        return _default_watchlist()
    try:
        with _WATCHLIST_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        # Schema validate
        for key in ("tickers", "added_dates", "entry_targets", "notes"):
            data.setdefault(key, {} if key != "tickers" else [])
        return data
    except Exception:
        return _default_watchlist()


def save_watchlist(watchlist: dict) -> bool:
    """Save watchlist atomically."""
    try:
        _WATCHLIST_DIR.mkdir(parents=True, exist_ok=True)
        tmp = _WATCHLIST_FILE.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(watchlist, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(_WATCHLIST_FILE)
        return True
    except Exception:
        return False


def add_ticker(
    ticker: str,
    entry_target: Optional[float] = None,
    notes: Optional[str] = None,
    added_date: Optional[str] = None,
) -> bool:
    """Add ticker to watchlist (no-op if already present)."""
    ticker = ticker.strip().upper()
    if not ticker:
        return False
    wl = load_watchlist()
    if ticker in wl["tickers"]:
        return False
    wl["tickers"].append(ticker)
    if added_date:
        wl["added_dates"][ticker] = added_date
    if entry_target is not None:
        wl["entry_targets"][ticker] = float(entry_target)
    if notes:
        wl["notes"][ticker] = notes
    return save_watchlist(wl)


def remove_ticker(ticker: str) -> bool:
    """Remove ticker from watchlist."""
    ticker = ticker.strip().upper()
    wl = load_watchlist()
    if ticker not in wl["tickers"]:
        return False
    wl["tickers"].remove(ticker)
    wl["added_dates"].pop(ticker, None)
    wl["entry_targets"].pop(ticker, None)
    wl["notes"].pop(ticker, None)
    return save_watchlist(wl)


def watchlist_count() -> int:
    return len(load_watchlist().get("tickers", []))
