"""
KAP Free-Float Fetcher (Faz 11 v4.0 — Session 3D).

Endpoint:
  GET https://kap.org.tr/tr/tumKalemler/kpy41_acc5_fiili_dolasimdaki_pay

Veri kaynağı = MKK (Merkezi Kayıt Kuruluşu) ön yüzü KAP üzerinden.
SPK 17.02.2011 tarih 5/157 kararı çerçevesinde günlük yayın.

KEŞİF NOTU (Session 3D):
  VAP (vap.org.tr) TLS handshake reset (Schannel uyumsuz).
  KAP kpy41_acc5 endpoint resmi alternatif (200 OK, 615 ticker).
  Lesson #27: Resmi devlet kurumu trio (KAP+MKK+SPK) resilience.

Kolon yapısı (HTML table):
  [0] Şirket                            (full name)
  [1] Borsa Kodu                        (ticker)
  [2] Fiili Dolaşımdaki Pay Tutarı(TL)  (TR float "936.392.381,98")
  [3] Fiili Dolaşımdaki Pay Oranı(%)    (INTEGER 4859 → 48.59%)

Damodaran per-share convention (BIST):
  Pay nominal: 1 TL effective (TUPRS örneği: 1 Kr × 100 = 1 TL grup)
  shares_outstanding = ödenmiş_sermaye_TL / 1.0
  ödenmiş_sermaye_TL = float_amount_tl / float_pct
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, asdict, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import pandas as pd


KAP_BASE_URL = "https://www.kap.org.tr"
KAP_FLOAT_URL = (
    f"{KAP_BASE_URL}/tr/tumKalemler/kpy41_acc5_fiili_dolasimdaki_pay"
)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Origin": KAP_BASE_URL,
    "Referer": f"{KAP_BASE_URL}/",
}

CACHE_DIR = Path(__file__).resolve().parents[1] / "_cache" / "kap_float"

# Pay nominal effective TL — BIST'te ödenmiş sermayeyi 1 TL nominale göre
# bölmek convention. TUPRS örneği: 1 Kr (kuruş) × 100 = 1 TL grup.
PAY_NOMINAL_EFFECTIVE_TL = 1.0


@dataclass
class FloatData:
    ticker: str
    sirket_adi: str
    float_amount_tl: float        # Fiili Dolaşımdaki Pay Tutarı (TL)
    float_pct: float              # 0..1 (KAP ham integer'dan / 100)
    odenmis_sermaye_tl: float     # = float_amount / float_pct
    shares_outstanding: float     # = odenmis_sermaye_tl / 1.0
    float_shares: float           # = shares × float_pct
    update_date: str              # YYYY-MM-DD


@dataclass
class FloatSnapshot:
    fetch_date: str
    record_count: int
    records: List[FloatData] = field(default_factory=list)
    error: Optional[str] = None
    notes: List[str] = field(default_factory=list)


def _parse_tr_float(s: str) -> Optional[float]:
    """'936.392.381,98' → 936392381.98"""
    if s is None:
        return None
    txt = str(s).strip()
    if not txt or txt in ("-", "—", "nan", "None"):
        return None
    cleaned = txt.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_oran_pct(s: str) -> Optional[float]:
    """KAP ham oran integer (4859) → 0.4859 (decimal fraction)."""
    if s is None:
        return None
    txt = str(s).strip()
    if not txt or txt in ("-", "—", "nan", "None"):
        return None
    # Bazı satırlarda ondalık olabilir ("48,59"); önce TR-float dene
    if "," in txt:
        v = _parse_tr_float(txt)
        if v is not None:
            return v / 100.0 if v > 1 else v
    try:
        v = int(re.sub(r"\D", "", txt))
        return v / 10000.0  # 4859 → 0.4859
    except (ValueError, TypeError):
        return None


def fetch_float_html(timeout: float = 30.0) -> str:
    """KAP kpy41_acc5 sayfa HTML — raw text döner."""
    with httpx.Client(headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True) as c:
        r = c.get(KAP_FLOAT_URL)
        if r.status_code != 200:
            raise RuntimeError(f"KAP float HTTP {r.status_code}")
        return r.text


def parse_float_table(html: str, today: Optional[date] = None) -> List[FloatData]:
    """HTML → List[FloatData]."""
    today = today or date.today()
    iso_date = today.isoformat()

    tables = pd.read_html(io.StringIO(html))
    if not tables:
        raise RuntimeError("No tables found")

    df = tables[0]
    if df.shape[1] < 4:
        raise RuntimeError(f"Unexpected schema, cols={list(df.columns)}")

    # Kolon isimleri TR-encoded; index ile çekiyoruz
    records: List[FloatData] = []
    for _, row in df.iterrows():
        sirket = str(row.iloc[0]).strip()
        ticker = str(row.iloc[1]).strip().upper()
        amt = _parse_tr_float(row.iloc[2])
        pct = _parse_oran_pct(row.iloc[3])

        if not ticker or ticker == "NAN" or amt is None or pct is None:
            continue
        if pct <= 0 or pct > 1.5:  # >100% sanity
            continue

        odenmis = amt / pct
        shares = odenmis / PAY_NOMINAL_EFFECTIVE_TL
        float_shares = shares * pct

        records.append(FloatData(
            ticker=ticker,
            sirket_adi=sirket,
            float_amount_tl=amt,
            float_pct=pct,
            odenmis_sermaye_tl=odenmis,
            shares_outstanding=shares,
            float_shares=float_shares,
            update_date=iso_date,
        ))
    return records


def fetch_float_snapshot(
    cache: bool = True,
    force_refresh: bool = False,
) -> FloatSnapshot:
    """KAP kpy41_acc5 → FloatSnapshot (cache-aware)."""
    today = date.today()
    iso_date = today.isoformat()
    snap = FloatSnapshot(fetch_date=iso_date, record_count=0)

    cache_path = CACHE_DIR / f"kap_float_{iso_date}.csv"

    if cache and not force_refresh and cache_path.exists():
        try:
            df = pd.read_csv(cache_path)
            for _, row in df.iterrows():
                snap.records.append(FloatData(**row.to_dict()))
            snap.record_count = len(snap.records)
            snap.notes.append(f"Loaded from cache: {cache_path.name}")
            return snap
        except Exception as e:
            snap.notes.append(f"Cache read fail, refreshing: {e}")

    try:
        html = fetch_float_html()
        records = parse_float_table(html, today=today)
    except Exception as e:
        snap.error = f"{type(e).__name__}: {e}"
        return snap

    snap.records = records
    snap.record_count = len(records)

    if cache and records:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame([asdict(r) for r in records])
        df.to_csv(cache_path, index=False, encoding="utf-8")
        snap.notes.append(f"Cached: {cache_path.name}")

    return snap


def lookup_ticker(snapshot: FloatSnapshot, ticker: str) -> Optional[FloatData]:
    ticker = ticker.upper().strip()
    for r in snapshot.records:
        if r.ticker == ticker:
            return r
    return None


# ============================================================================
# Validation / CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 78)
    print("KAP Free-Float Fetcher — Session 3D Production Validation")
    print("=" * 78)

    snap = fetch_float_snapshot(force_refresh=True)
    if snap.error:
        print(f"  ✗ FAIL: {snap.error}")
        sys.exit(1)

    print(f"  ✓ Fetch date:     {snap.fetch_date}")
    print(f"  ✓ Records:        {snap.record_count}")
    for n in snap.notes:
        print(f"    - {n}")

    # Anchor + spot checks
    targets = [
        ("TUPRS", 1_927_015_191, "anchor — 3 kaynak uyumlu"),
        ("GARAN", None, "spot check"),
        ("AKBNK", None, "spot check"),
        ("KCHOL", None, "spot check"),
        ("AGROT", None, "yeni IPO"),
        ("KUYAS", None, "Session 2 BUG"),
    ]

    print(f"\n{'─'*78}")
    print(f"{'TICKER':<8} {'Şirket':<32} {'Sermaye TL':>16} {'Shares':>14} {'Float%':>8}")
    print('─'*78)

    for ticker, expected_sermaye, note in targets:
        rec = lookup_ticker(snap, ticker)
        if rec is None:
            print(f"  {ticker}  ✗ NOT FOUND  ({note})")
            continue

        sirket_short = rec.sirket_adi[:30] + (".." if len(rec.sirket_adi) > 30 else "")
        print(
            f"{rec.ticker:<8} {sirket_short:<32} "
            f"{rec.odenmis_sermaye_tl:>16,.0f} "
            f"{rec.shares_outstanding:>14,.0f} "
            f"{rec.float_pct*100:>7.2f}%"
        )

        if expected_sermaye is not None:
            err_pct = abs(rec.odenmis_sermaye_tl - expected_sermaye) / expected_sermaye * 100
            verdict = "✓ PASS" if err_pct <= 0.5 else "✗ FAIL"
            print(
                f"         expected: {expected_sermaye:>16,.0f}  "
                f"err: {err_pct:.4f}%  {verdict}"
            )
