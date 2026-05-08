"""
KAP Bağlı Ortaklıklar Fetcher (Faz 11 v4.0 — Session 3E).

Endpoint:
  GET https://kap.org.tr/tr/tumKalemler/kpy41_acc7_bagli_ortakliklar

Hedef: Damodaran Holding SOTP modeli (ADR-013) enabler.
Holding ticker'ları için iştirak listesi → her iştirak ayrı
mini-DCF → aggregate SOTP intrinsic value.

Kolon yapısı (HTML table):
  [0] Şirket                              (parent full Turkish name)
  [1] Ticaret Ünvanı                      (subsidiary name)
  [2] Şirketin Faaliyet Konusu            (sector / activity)
  [3] Ödenmiş/Çıkarılmış Sermayesi        (subsidiary's own capital)
  [4] Şirketin Sermayedeki Payı           (parent's share amount)
  [5] Para Birimi                         (TRY / USD / EUR / ...)
  [6] Şirketin Sermayedeki Payı(%)        (INTEGER 6482 → 64.82%)
  [7] Şirket ile Olan İlişkinin Niteliği  (Bağlı Ortaklık / İştirak / ...)

Probe stats (2026-05):
  3512 satır, 535 distinct parent
  Anchor validations:
    SAHOL: 19 subs (Akbank, Aksigorta, Brisa, Çimsa, Teknosa+) ✓
    KCHOL: 40 subs (Arçelik, Aygaz, Ford+) ✓
    TUPRS: 6 subs (Ditaş, OPET, Körfez+) ✓
    DOHOL: 39 subs ✓  AKBNK: 16 ✓  ARCLK: 122 ✓

Parent ticker resolution:
  kpy41_acc7 sadece full name veriyor — ticker yok.
  kap_float_fetcher (kpy41_acc5) snapshot ile JOIN:
    parent_full_name → ticker (büyük harf normalize ile)
"""

from __future__ import annotations

import io
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import pandas as pd

# Local sibling import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kap_float_fetcher import fetch_float_snapshot, FloatSnapshot  # noqa: E402


KAP_BASE_URL = "https://www.kap.org.tr"
KAP_SUBS_URL = (
    f"{KAP_BASE_URL}/tr/tumKalemler/kpy41_acc7_bagli_ortakliklar"
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

CACHE_DIR = Path(__file__).resolve().parents[1] / "_cache" / "kap_subsidiaries"


@dataclass
class SubsidiaryData:
    parent_ticker: Optional[str]      # JOIN'den gelir (None = unmatched)
    parent_name: str                  # Şirket (full name)
    subsidiary_name: str              # Ticaret Ünvanı
    subsidiary_ticker: Optional[str]  # BIST listed ise (JOIN ile)
    sector: Optional[str]             # Faaliyet Konusu
    sub_capital: Optional[float]      # Ödenmiş/Çıkarılmış Sermayesi
    parent_share_amount: Optional[float]  # Şirketin Sermayedeki Payı
    currency: Optional[str]           # TRY/USD/EUR
    ownership_pct: Optional[float]    # 0..1 fraction (KAP raw int / 10000)
    relationship_type: Optional[str]  # Normalize edilmiş: full/joint/equity/financial
    relationship_raw: Optional[str]   # Ham TR metin
    update_date: str                  # YYYY-MM-DD


@dataclass
class SubsidiariesSnapshot:
    fetch_date: str
    record_count: int
    distinct_parents: int = 0
    matched_parents: int = 0
    matched_subsidiaries: int = 0
    records: List[SubsidiaryData] = field(default_factory=list)
    error: Optional[str] = None
    notes: List[str] = field(default_factory=list)


# ============================================================================
# Helpers
# ============================================================================

def _parse_tr_float(s) -> Optional[float]:
    """'2.074.240.000' / '6.900' / '0' → float, '-' / 'nan' → None."""
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


def _parse_pct_raw(s) -> Optional[float]:
    """KAP raw integer → fraction (0..1).

    KAP ondalık ayraç convention bipolar:
      "100"  → 100.00%  → 1.00     (3-digit veya altı, decimal yok)
      "6482" → 64.82%   → 0.6482   (4-digit, son 2 hane ondalık)
      "9999" → 99.99%   → 0.9999
    Heuristic: raw ≤ 100 → /100, raw > 100 → /10000.
    """
    if s is None:
        return None
    txt = str(s).strip()
    if not txt or txt in ("-", "—", "nan", "None"):
        return None
    if "," in txt:
        v = _parse_tr_float(txt)
        if v is not None:
            return v / 100.0 if v > 1 else v
    digits = re.sub(r"\D", "", txt)
    if not digits:
        return None
    try:
        raw = int(digits)
    except ValueError:
        return None
    if raw <= 100:
        return raw / 100.0
    return raw / 10000.0


_REL_NORMALIZE: Dict[str, str] = {
    # full ownership
    "bagli ortaklik":         "full",
    "endirekt bagli ortaklik":"full",
    "dolayli bagli ortaklik": "full",
    # joint / proportional
    "musterek yonetime tabi ortaklik": "joint",
    "is ortakligi":          "joint",
    "is ortakliklarindaki yatirimlar": "joint",
    # equity method
    "istirak":               "equity",
    # financial investment
    "finansal yatirim":      "financial",
    "finansal duran varlik": "financial",
}


_TR_DIACRITIC_MAP = {
    "ı": "i", "İ": "i", "i̇": "i",  # i variants + combining-dot
    "ş": "s", "Ş": "s",
    "ğ": "g", "Ğ": "g",
    "ç": "c", "Ç": "c",
    "ö": "o", "Ö": "o",
    "ü": "u", "Ü": "u",
}


def _normalize_tr(s: str) -> str:
    """Lower + Türkçe diakritik fold (Lesson #26 extended).

    ı/i, İ/i, ş/s, ğ/g, ç/c, ö/o, ü/u — ASCII fallback.
    Matching disiplini için her iki tarafı normalize et.
    """
    if not s:
        return ""
    s = s.lower()
    for src, dst in _TR_DIACRITIC_MAP.items():
        s = s.replace(src, dst)
    s = s.replace("̇", "")  # combining dot above (post İ.lower())
    return s


def _normalize_relationship(raw: str) -> Optional[str]:
    if raw is None:
        return None
    norm = _normalize_tr(str(raw))
    norm = re.sub(r"[^a-z\s]", " ", norm)  # diacritics + punct out
    norm = re.sub(r"\s+", " ", norm).strip()
    # strip plural 's' / 'ler' tails roughly
    norm = norm.replace("ortakliklar", "ortaklik")
    return _REL_NORMALIZE.get(norm)


def _build_name_to_ticker(float_snap: FloatSnapshot) -> Dict[str, str]:
    """Parent full-name (TR-normalize) → ticker mapping."""
    mp: Dict[str, str] = {}
    for r in float_snap.records:
        key = _normalize_tr(r.sirket_adi).strip()
        if key:
            mp.setdefault(key, r.ticker)
    return mp


# ============================================================================
# Fetcher
# ============================================================================

def fetch_subs_html(timeout: float = 60.0) -> str:
    with httpx.Client(headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True) as c:
        r = c.get(KAP_SUBS_URL)
        if r.status_code != 200:
            raise RuntimeError(f"KAP subs HTTP {r.status_code}")
        return r.text


def parse_subs_table(
    html: str,
    name_to_ticker: Dict[str, str],
    today: Optional[date] = None,
) -> List[SubsidiaryData]:
    today = today or date.today()
    iso_date = today.isoformat()

    tables = pd.read_html(io.StringIO(html))
    if not tables:
        raise RuntimeError("No tables found")
    df = tables[0]
    if df.shape[1] < 8:
        raise RuntimeError(f"Unexpected schema, cols={list(df.columns)}")

    records: List[SubsidiaryData] = []
    for _, row in df.iterrows():
        parent_name = str(row.iloc[0]).strip()
        sub_name = str(row.iloc[1]).strip()
        if not parent_name or parent_name == "nan":
            continue
        if not sub_name or sub_name == "nan":
            continue

        sector = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else None
        sub_cap = _parse_tr_float(row.iloc[3])
        parent_share = _parse_tr_float(row.iloc[4])
        currency = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else None
        pct = _parse_pct_raw(row.iloc[6])
        rel_raw = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else None
        rel_norm = _normalize_relationship(rel_raw) if rel_raw else None

        # JOIN: parent name → ticker
        parent_ticker = name_to_ticker.get(_normalize_tr(parent_name).strip())
        sub_ticker = name_to_ticker.get(_normalize_tr(sub_name).strip())

        records.append(SubsidiaryData(
            parent_ticker=parent_ticker,
            parent_name=parent_name,
            subsidiary_name=sub_name,
            subsidiary_ticker=sub_ticker,
            sector=sector,
            sub_capital=sub_cap,
            parent_share_amount=parent_share,
            currency=currency,
            ownership_pct=pct,
            relationship_type=rel_norm,
            relationship_raw=rel_raw,
            update_date=iso_date,
        ))
    return records


def fetch_subsidiaries_snapshot(
    cache: bool = True,
    force_refresh: bool = False,
    float_snapshot: Optional[FloatSnapshot] = None,
) -> SubsidiariesSnapshot:
    """KAP kpy41_acc7 → SubsidiariesSnapshot (cache-aware)."""
    today = date.today()
    iso_date = today.isoformat()
    snap = SubsidiariesSnapshot(fetch_date=iso_date, record_count=0)

    cache_path = CACHE_DIR / f"kap_subs_{iso_date}.csv"

    if cache and not force_refresh and cache_path.exists():
        try:
            df = pd.read_csv(cache_path)
            for _, row in df.iterrows():
                snap.records.append(SubsidiaryData(**row.to_dict()))
            snap.record_count = len(snap.records)
            snap.notes.append(f"Loaded from cache: {cache_path.name}")
            return _post_compute(snap)
        except Exception as e:
            snap.notes.append(f"Cache read fail, refreshing: {e}")

    # JOIN için kpy41_acc5 snapshot
    fs = float_snapshot or fetch_float_snapshot(cache=True)
    if fs.error or not fs.records:
        snap.notes.append(f"Float snapshot unavailable ({fs.error}), parent_ticker JOIN skipped")
        name_to_ticker: Dict[str, str] = {}
    else:
        name_to_ticker = _build_name_to_ticker(fs)

    try:
        html = fetch_subs_html()
        records = parse_subs_table(html, name_to_ticker, today=today)
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

    return _post_compute(snap)


def _post_compute(snap: SubsidiariesSnapshot) -> SubsidiariesSnapshot:
    """Distinct parent + match counts for diagnostic."""
    distinct = set()
    matched_parents = set()
    matched_subs = 0
    for r in snap.records:
        distinct.add(r.parent_name)
        if r.parent_ticker:
            matched_parents.add(r.parent_ticker)
        if r.subsidiary_ticker:
            matched_subs += 1
    snap.distinct_parents = len(distinct)
    snap.matched_parents = len(matched_parents)
    snap.matched_subsidiaries = matched_subs
    return snap


def lookup_parent(snapshot: SubsidiariesSnapshot, ticker: str) -> List[SubsidiaryData]:
    ticker = ticker.upper().strip()
    return [r for r in snapshot.records if r.parent_ticker == ticker]


# ============================================================================
# Validation / CLI
# ============================================================================

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 78)
    print("KAP Bağlı Ortaklıklar Fetcher — Session 3E Production Validation")
    print("=" * 78)

    snap = fetch_subsidiaries_snapshot(force_refresh=True)
    if snap.error:
        print(f"  ✗ FAIL: {snap.error}")
        sys.exit(1)

    print(f"  ✓ Fetch date:           {snap.fetch_date}")
    print(f"  ✓ Records:              {snap.record_count}")
    print(f"  ✓ Distinct parents:     {snap.distinct_parents}")
    print(f"  ✓ Matched parents:      {snap.matched_parents}  (kpy41_acc5 join)")
    print(f"  ✓ Matched subsidiaries: {snap.matched_subsidiaries}  (BIST-listed iştirak)")
    for n in snap.notes:
        print(f"    - {n}")

    # Anchor / spot check
    targets = [
        ("SAHOL", 5),   # min 5 sub bekleniyor
        ("KCHOL", 10),
        ("TUPRS", 3),
        ("DOHOL", 5),
        ("AKBNK", 5),
        ("ARCLK", 5),
    ]

    for ticker, min_count in targets:
        subs = lookup_parent(snap, ticker)
        verdict = "✓ PASS" if len(subs) >= min_count else "✗ FAIL"
        print(f"\n{'─'*78}")
        print(f"{ticker}  subsidiaries={len(subs)}  (min {min_count})  {verdict}")
        print('─'*78)
        if not subs:
            print(f"  ⚠ Parent '{ticker}' name JOIN failed — kpy41_acc5 mapping eksik")
            continue
        # Listed iştirakleri öne al
        subs_sorted = sorted(subs, key=lambda r: (r.subsidiary_ticker is None,
                                                  -(r.ownership_pct or 0)))
        for r in subs_sorted[:8]:
            tflag = f"[{r.subsidiary_ticker}]" if r.subsidiary_ticker else "[—]"
            pct = f"{r.ownership_pct*100:5.2f}%" if r.ownership_pct is not None else "  -  "
            rel = r.relationship_type or "?"
            print(f"  {tflag:8} {r.subsidiary_name[:48]:<48} {pct}  {rel}")

    # KCHOL → TUPRS circular ref test
    print(f"\n{'─'*78}")
    print("CIRCULAR REF TEST: KCHOL → TUPRS expected (Damodaran SOTP edge)")
    print('─'*78)
    kc = lookup_parent(snap, "KCHOL")
    tuprs_in_kc = [r for r in kc if "TÜPRAŞ" in r.subsidiary_name.upper() or
                   r.subsidiary_ticker == "TUPRS"]
    if tuprs_in_kc:
        for r in tuprs_in_kc:
            print(f"  ✓ KCHOL → {r.subsidiary_name}  ticker={r.subsidiary_ticker}  "
                  f"pct={r.ownership_pct}")
    else:
        print("  ⚠ KCHOL kayıtlarında TUPRS sub görünmüyor (subsidiary 1 hop ötede olabilir)")
