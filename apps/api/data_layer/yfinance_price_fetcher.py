"""
Yahoo Finance Price Fetcher (Faz 11 v4.0 — Session 3.5).

KAPSAM DİSİPLİNİ:
  ✓ Anlık fiyat (current_price)
  ✓ 5 yıl günlük adjusted close (history)
  ✓ Volume
  ✓ BIST 100 endeksi (^XU100 / XU100.IS) benchmark
  ✗ financials, shares, sector, dividend, news, analyst_recs
    → Bunlar KAP-only kalır (Session 3A/3D/3E/3F).

NEDEN yfinance:
  Yahoo Finance BIST verisini LİSANSLI sublicensee olarak alır.
  Veri kaynağı = BIST resmi. Dağıtım kanalı = Yahoo.
  Damodaran academic practice'inde standart kabul edilir.
  Raw feed → parse layer minimum → bug riski az.

  3rd party scrape (İş Yatırım gibi) ≠ licensed sublicensee.
  yfinance KAPSAM disiplini: SADECE fiyat.

ŞEFFAFLIK ZORUNLU:
  Frontend Tarayıcı sidebar'ında disclaimer:
    "Fiyat verisi: Yahoo Finance (BIST lisanslı kanal)"

CORPORATE EVENTS (Session 3F integration):
  KOZAL → TRALT (06.11.2025) gibi mapping varsa:
    - Eski ticker tarihi YENİ ticker'a redirect
    - Merge logic: yfinance otomatik adjusted (split + ad değişikliği)
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    import yfinance as yf
except ImportError as e:
    raise ImportError(
        "yfinance gerekli. Kur: pip install yfinance>=0.2.40"
    ) from e

# Local sibling
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kap_corporate_events import load_snapshot as load_ce_snapshot  # noqa: E402
from kap_corporate_events import resolve_ticker as ce_resolve_ticker  # noqa: E402


CACHE_DIR = Path(__file__).resolve().parents[1] / "_cache" / "yfinance"
BIST_INDEX_SYMBOL_PRIMARY = "XU100.IS"
BIST_INDEX_SYMBOL_FALLBACK = "^XU100"
BIST_INDEX_CACHE_NAME = "_BIST100"

DEFAULT_THROTTLE_SEC = 0.5
SOURCE_LABEL = "yfinance (BIST lisanslı kanal)"


@dataclass
class PriceData:
    ticker: str
    yahoo_symbol: str
    current_price: Optional[float]
    currency: Optional[str]
    market_cap: Optional[float]
    fifty_day_avg: Optional[float]
    two_hundred_day_avg: Optional[float]
    year_change: Optional[float]
    history_rows: int = 0
    history_first_date: Optional[str] = None
    history_last_date: Optional[str] = None
    fetch_date: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    source: str = SOURCE_LABEL
    error: Optional[str] = None


@dataclass
class BatchReport:
    fetch_date: str
    success_count: int = 0
    fail_count: int = 0
    name_changed: List[Tuple[str, str]] = field(default_factory=list)
    failures: List[Tuple[str, str]] = field(default_factory=list)
    bist100_ok: bool = False


# ============================================================================
# Helpers
# ============================================================================

def _to_yahoo_symbol(ticker: str) -> str:
    """BIST ticker → Yahoo symbol (XXXX.IS)."""
    t = ticker.upper().strip()
    if t.endswith(".IS"):
        return t
    return f"{t}.IS"


def _resolve_via_corporate_events(ticker: str) -> Optional[str]:
    """Eski ticker → yeni ticker (Session 3F mapping)."""
    snap = load_ce_snapshot()
    if snap is None:
        return None
    res = ce_resolve_ticker(snap, ticker)
    if res:
        return res["new_ticker"]
    return None


# ============================================================================
# Single-ticker fetch
# ============================================================================

def fetch_one(
    ticker: str,
    period: str = "5y",
    interval: str = "1d",
    cache: bool = True,
    force_refresh: bool = False,
) -> PriceData:
    """Tek ticker fiyat verisi fetch + cache.

    Args:
        ticker: BIST ticker (TUPRS, GARAN, ...)
        period: yfinance period spec (1d, 5d, 1mo, ..., 5y, 10y, ytd, max)
        interval: yfinance interval (1d, 1wk, 1mo)
        cache: True → CSV write
        force_refresh: True → cache atla
    """
    yh = _to_yahoo_symbol(ticker)
    pd_obj = PriceData(
        ticker=ticker.upper().strip(),
        yahoo_symbol=yh,
        current_price=None,
        currency=None,
        market_cap=None,
        fifty_day_avg=None,
        two_hundred_day_avg=None,
        year_change=None,
    )

    cache_path = CACHE_DIR / f"{pd_obj.ticker}.csv"
    if cache and not force_refresh and cache_path.exists():
        # Eğer son tarih bugün veya dün ise skip (resume capability — basit kural)
        try:
            df = pd.read_csv(cache_path, parse_dates=["date"])
            if not df.empty:
                last = df["date"].max().date()
                if (date.today() - last).days <= 1:
                    pd_obj.history_rows = len(df)
                    pd_obj.history_first_date = df["date"].min().strftime("%Y-%m-%d")
                    pd_obj.history_last_date = last.strftime("%Y-%m-%d")
                    pd_obj.error = "cached_recent"
                    # current_price yine de canlı çek (anlık)
                    # — fakat throttle dostu: cached'da skip
        except Exception:
            pass

    try:
        ticker_obj = yf.Ticker(yh)
        # 1) Anlık fiyat (fast_info)
        try:
            fi = ticker_obj.fast_info
            pd_obj.current_price = fi.get("lastPrice") or fi.get("regularMarketPreviousClose")
            pd_obj.currency = fi.get("currency")
            pd_obj.market_cap = fi.get("marketCap")
            pd_obj.fifty_day_avg = fi.get("fiftyDayAverage")
            pd_obj.two_hundred_day_avg = fi.get("twoHundredDayAverage")
            pd_obj.year_change = fi.get("yearChange")
        except Exception as e:
            pd_obj.error = f"fast_info: {type(e).__name__}: {e}"

        # 2) 5 yıl history (auto_adjust=True → Close adjusted)
        if pd_obj.error != "cached_recent":
            hist = ticker_obj.history(
                period=period, interval=interval, auto_adjust=True,
            )
            if hist.empty:
                pd_obj.error = "history_empty"
            else:
                pd_obj.history_rows = len(hist)
                pd_obj.history_first_date = hist.index[0].strftime("%Y-%m-%d")
                pd_obj.history_last_date = hist.index[-1].strftime("%Y-%m-%d")

                if cache:
                    CACHE_DIR.mkdir(parents=True, exist_ok=True)
                    out = pd.DataFrame({
                        "date":   hist.index.strftime("%Y-%m-%d"),
                        "close":  hist["Close"].round(4),
                        "volume": hist["Volume"].astype("int64", errors="ignore"),
                    })
                    out.to_csv(cache_path, index=False)
    except Exception as e:
        pd_obj.error = f"{type(e).__name__}: {e}"

    return pd_obj


# ============================================================================
# Batch fetcher (605 ticker)
# ============================================================================

def fetch_batch(
    tickers: List[str],
    throttle_sec: float = DEFAULT_THROTTLE_SEC,
    cache: bool = True,
    force_refresh: bool = False,
    progress: bool = True,
) -> Tuple[List[PriceData], BatchReport]:
    today_iso = date.today().isoformat()
    report = BatchReport(fetch_date=today_iso)
    results: List[PriceData] = []

    # Pre-resolve ticker mappings (Session 3F)
    ce_snap = load_ce_snapshot()

    for i, ticker in enumerate(tickers, 1):
        eff_ticker = ticker
        if ce_snap is not None:
            res = ce_resolve_ticker(ce_snap, ticker)
            if res:
                eff_ticker = res["new_ticker"]
                report.name_changed.append((ticker, eff_ticker))

        pd_obj = fetch_one(
            eff_ticker,
            cache=cache,
            force_refresh=force_refresh,
        )
        results.append(pd_obj)

        if pd_obj.error and pd_obj.error not in ("cached_recent",):
            report.fail_count += 1
            report.failures.append((ticker, pd_obj.error[:80]))
        else:
            report.success_count += 1

        if progress:
            pct = i * 100 // len(tickers)
            short_err = pd_obj.error[:25] if pd_obj.error else ""
            cur = f"{pd_obj.current_price:>9,.2f}" if pd_obj.current_price else "    n/a "
            print(
                f"  [{i:3d}/{len(tickers)}] ({pct:3d}%) {ticker:6} → {eff_ticker:6} "
                f"price={cur}  rows={pd_obj.history_rows:>4}  {short_err}"
            )

        time.sleep(throttle_sec)

    return results, report


def fetch_bist100(
    period: str = "5y",
    cache: bool = True,
    force_refresh: bool = False,
) -> Optional[PriceData]:
    """BIST 100 endeksi (^XU100 fallback ile XU100.IS primary)."""
    cache_path = CACHE_DIR / f"{BIST_INDEX_CACHE_NAME}.csv"

    for sym in (BIST_INDEX_SYMBOL_PRIMARY, BIST_INDEX_SYMBOL_FALLBACK):
        try:
            t = yf.Ticker(sym)
            hist = t.history(period=period, interval="1d", auto_adjust=True)
            if not hist.empty:
                if cache:
                    CACHE_DIR.mkdir(parents=True, exist_ok=True)
                    out = pd.DataFrame({
                        "date":  hist.index.strftime("%Y-%m-%d"),
                        "close": hist["Close"].round(4),
                    })
                    out.to_csv(cache_path, index=False)
                fi = t.fast_info
                return PriceData(
                    ticker="BIST100",
                    yahoo_symbol=sym,
                    current_price=fi.get("lastPrice"),
                    currency=fi.get("currency"),
                    market_cap=None,
                    fifty_day_avg=fi.get("fiftyDayAverage"),
                    two_hundred_day_avg=fi.get("twoHundredDayAverage"),
                    year_change=fi.get("yearChange"),
                    history_rows=len(hist),
                    history_first_date=hist.index[0].strftime("%Y-%m-%d"),
                    history_last_date=hist.index[-1].strftime("%Y-%m-%d"),
                )
        except Exception:
            continue
    return None


# ============================================================================
# CLI / Validation
# ============================================================================

def _spk_universe() -> List[str]:
    """SPK universe load (605 ticker)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from kap_float_fetcher import fetch_float_snapshot  # noqa: E402
    snap = fetch_float_snapshot(cache=True)
    return sorted({r.ticker for r in snap.records})


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 78)
    print("yfinance Price Fetcher — Session 3.5 Production Validation")
    print("=" * 78)

    # 1) BIST 100 endeksi
    print("\n→ BIST 100 endeksi (5y daily)...")
    bist = fetch_bist100(period="5y", cache=True)
    if bist:
        print(f"  ✓ {bist.yahoo_symbol}: rows={bist.history_rows} "
              f"first={bist.history_first_date} last={bist.history_last_date}")
        print(f"    current={bist.current_price}  year_change="
              f"{(bist.year_change or 0)*100:.1f}%")
    else:
        print("  ✗ BIST 100 fetch FAIL")

    # 2) Spot check 5 ticker
    print("\n→ Spot check 5 ticker (TUPRS anchor + 4 random)...")
    spots = ["TUPRS", "GARAN", "THYAO", "ARCLK", "TRALT"]  # TRALT = eski KOZAL
    spot_results, spot_rep = fetch_batch(spots, throttle_sec=0.5, force_refresh=True)
    for r in spot_results:
        cur = f"{r.current_price:.2f}" if r.current_price else "n/a"
        print(f"    {r.ticker:6} → cur={cur:>10} rows={r.history_rows} "
              f"err={r.error or '-'}")

    # Anchor check
    tuprs = next((r for r in spot_results if r.ticker == "TUPRS"), None)
    if tuprs and tuprs.current_price:
        anchor_lo, anchor_hi = 246, 272  # 259 ±%5
        in_band = anchor_lo <= tuprs.current_price <= anchor_hi
        print(f"\n  ★ TUPRS anchor: {tuprs.current_price:.2f} TL  "
              f"band [{anchor_lo}-{anchor_hi}]  "
              f"{'✓ IN BAND' if in_band else '✗ OUT OF BAND'}")

    # 3) Full 605 ticker batch (use spk universe)
    print(f"\n→ Full SPK universe batch (605 ticker, ~10 dakika)...")
    print(f"  (Resume-capable: cached recent → skip)")
    universe = _spk_universe()
    print(f"  Universe size: {len(universe)} ticker")
    results, report = fetch_batch(
        universe,
        throttle_sec=0.4,
        cache=True,
        force_refresh=False,
        progress=True,
    )

    print(f"\n{'─'*78}")
    print(f"  BATCH SUMMARY")
    print(f"  Success: {report.success_count}/{len(universe)}")
    print(f"  Fail:    {report.fail_count}")
    print(f"  Name changes resolved: {len(report.name_changed)}")
    if report.name_changed:
        for old, new in report.name_changed[:8]:
            print(f"    - {old} → {new}")
    if report.failures:
        print(f"\n  First 10 failures:")
        for tk, err in report.failures[:10]:
            print(f"    - {tk:6}: {err}")
    print('─'*78)
