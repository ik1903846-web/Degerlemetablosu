"""
KAP Corporate Events Tracker — MVP (Faz 11 v4.0 — Session 3F).

KAP "Ünvan Değişikliği" (subject UUID 'srp2205201502', disclosureClass 'ODA')
duyurularını takip eder. Eski-yeni ticker/ünvan mapping registry üretir.

Resolved data quality issue:
  KOZAL → TRALT (06.11.2025)  Koza Altın → Türk Altın İşletmeleri
  KOZAA → TRMET (06.11.2025)  Koza Anadolu → Türk Metal Madencilik
  ...

KAP DİSCLOSURE FIELDS (disclosure search response):
  disclosureIndex   — KAP duyuru ID
  publishDate       — DD.MM.YYYY HH:MM:SS
  stockCodes        — YENİ ticker (duyuru anında geçerli kod)
  kapTitle          — YENİ unvan (duyuru anında geçerli ünvan)
  summary           — Duyuru özeti (eski/yeni unvan parse buradan)
  subject           — "Ünvan Değişikliği"

ESKİ TICKER ÇIKARIM:
  KAP disclosure'da eski ticker doğrudan yok. Çözüm yolları (MVP):
    1. summary parse: "...KOZA ALTIN İŞLETMELERİ A.Ş." → eski_unvan
    2. Manual override (KNOWN_TICKER_MAPPINGS dict):
       eski → yeni 1:1 link bilinen anchor'lar
    3. resolver: kpy41_acc5'te eski-ticker yoksa, mapping'te ara

Genişletme (Session 5+ parking):
  - KAP "KAP Üyeliği Sona Eren" /sirketler/KSE Next.js sayfası
  - Member OID-based ticker history chain
  - M&A / kayyum / bölünme
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import httpx


KAP_BASE_URL = "https://www.kap.org.tr"
KAP_DISCLOSURE_URL = f"{KAP_BASE_URL}/tr/api/disclosure/members/byCriteria"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Origin": KAP_BASE_URL,
    "Referer": f"{KAP_BASE_URL}/tr/bildirim-sorgu",
}

# KAP subject UUIDs (Session 3F discovery — bildirim-sorgu HTML embedded)
SUBJECT_UNVAN_DEGISIKLIGI = "srp2205201502"
DISCLOSURE_CLASS_ODA = "ODA"

# Known eski→yeni manual mappings (research evidence)
# KAP disclosure'larında doğrudan ESKİ ticker yer almadığı için
# bilinen anchor'lar bu dict'le complement edilir. Source compare resolver
# bu dict'i ticker_mappings.json'a "manual" entry olarak ekler.
KNOWN_TICKER_MAPPINGS: Dict[str, str] = {
    # eski → yeni (TR Türk Şirketleri)
    "KOZAL": "TRALT",  # Koza Altın → Türk Altın İşletmeleri (06.11.2025)
    "KOZAA": "TRMET",  # Koza Anadolu Metal → Türk Metal Madencilik (06.11.2025)
    "IPEKE": "TRENJ",  # İpek Doğal Enerji → Türk Doğal Enerji (06.11.2025)
}

CACHE_DIR = Path(__file__).resolve().parents[1] / "_cache"
DEFAULT_OUTPUT = CACHE_DIR / "ticker_mappings.json"


@dataclass
class TickerMapping:
    new_ticker: str
    new_name: str
    old_name: Optional[str]              # summary'den parse
    change_date: str                     # YYYY-MM-DD
    disclosure_index: int
    summary_raw: str
    member_oid: Optional[str] = None
    old_ticker: Optional[str] = None     # manuel override / future enrichment


@dataclass
class CorporateEventsSnapshot:
    fetch_date: str
    record_count: int
    records: List[TickerMapping] = field(default_factory=list)
    error: Optional[str] = None
    notes: List[str] = field(default_factory=list)


# ============================================================================
# Helpers
# ============================================================================

_OLD_NAME_PATTERNS = [
    r"Ünvan\s+Değişikliği\s+Hk\.?\s+(.+?)$",            # "Ünvan Değişikliği Hk. KOZA ALTIN..."
    r"Ünvan\s+Değişikliğine\s+İlişkin",                  # generic
    r"Şirket\s+Ünvan(?:ı)?\s+Değişikliği\s+(.+?)$",     # "Şirket Ünvanı Değişikliği <X>"
    r"^(.+?)\s+(?:Yeni\s+)?Ünvan",                       # "<X> Yeni Ünvan..."
]


def _normalize_publish_date(raw: str) -> str:
    """'06.11.2025 18:17:06' → '2025-11-06'."""
    if not raw:
        return ""
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", raw)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{mo}-{d}"
    return raw


def _extract_old_name(summary: str) -> Optional[str]:
    """Summary'deki eski unvan candidate'ını çıkar.

    "Ünvan Değişikliği Hk. KOZA ALTIN İŞLETMELERİ A.Ş." → "KOZA ALTIN İŞLETMELERİ A.Ş."
    """
    if not summary:
        return None
    s = summary.strip()
    for pat in _OLD_NAME_PATTERNS:
        m = re.search(pat, s, flags=re.IGNORECASE)
        if m and m.lastindex:
            cand = m.group(1).strip(" .,—-")
            if 5 < len(cand) < 200:
                return cand
    return None


# ============================================================================
# Fetcher
# ============================================================================

def fetch_unvan_changes(
    years_back: int = 5,
    timeout: float = 60.0,
) -> List[Dict]:
    """KAP 'Ünvan Değişikliği' duyurularını N yıl geriye doğru çek.

    KAP API max 365-day → chunk fetch.
    """
    today = date.today()
    start_date = today - timedelta(days=365 * years_back)

    chunks: List[tuple[date, date]] = []
    cur_end = today
    while cur_end > start_date:
        cur_start = max(start_date, cur_end - timedelta(days=365))
        chunks.append((cur_start, cur_end))
        cur_end = cur_start - timedelta(days=1)
        if cur_end <= start_date:
            break

    seen_idx: set = set()
    all_rows: List[Dict] = []
    with httpx.Client(headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True) as c:
        for ch_start, ch_end in chunks:
            payload = {
                "fromDate":              ch_start.isoformat(),
                "toDate":                ch_end.isoformat(),
                "disclosureClass":       DISCLOSURE_CLASS_ODA,
                "subjectList":           [SUBJECT_UNVAN_DEGISIKLIGI],
                "mkkMemberOidList":      [],
                "inactiveMkkMemberOidList": [],
                "bdkMemberOidList":      [],
                "fromSrc":               False,
                "disclosureIndexList":   [],
            }
            r = c.post(KAP_DISCLOSURE_URL, json=payload)
            if r.status_code != 200:
                raise RuntimeError(
                    f"Chunk {ch_start}/{ch_end} HTTP {r.status_code}: {r.text[:120]}"
                )
            rows = r.json() or []
            for row in rows:
                idx = row.get("disclosureIndex") or row.get("index")
                if idx in seen_idx:
                    continue
                seen_idx.add(idx)
                all_rows.append(row)
    return all_rows


def parse_corporate_events(
    rows: List[Dict],
    today_iso: Optional[str] = None,
) -> List[TickerMapping]:
    """KAP disclosure rows → TickerMapping records."""
    today_iso = today_iso or date.today().isoformat()
    mappings: List[TickerMapping] = []
    for row in rows:
        new_ticker = (row.get("stockCodes") or "").strip().upper()
        if not new_ticker or "," in new_ticker:
            # Skip multi-ticker (rare), parking
            if not new_ticker:
                continue
        new_name = (row.get("kapTitle") or "").strip()
        summary = (row.get("summary") or "").strip()
        idx = row.get("disclosureIndex") or row.get("index") or 0
        publish = row.get("publishDate") or ""
        change_date = _normalize_publish_date(publish)
        old_name = _extract_old_name(summary)
        member_oid = row.get("memberOid")

        mappings.append(TickerMapping(
            new_ticker=new_ticker,
            new_name=new_name,
            old_name=old_name,
            change_date=change_date,
            disclosure_index=int(idx),
            summary_raw=summary,
            member_oid=member_oid,
            old_ticker=None,
        ))

    # Manual override enrichment (KNOWN_TICKER_MAPPINGS)
    for old_t, new_t in KNOWN_TICKER_MAPPINGS.items():
        # Mevcut record'ları bul yeni_ticker matched
        for m in mappings:
            if m.new_ticker == new_t and m.old_ticker is None:
                m.old_ticker = old_t

    # Sort: newest first
    mappings.sort(key=lambda m: m.change_date or "", reverse=True)
    return mappings


def fetch_corporate_events_snapshot(
    years_back: int = 5,
    output_path: Optional[Path] = None,
    cache: bool = True,
) -> CorporateEventsSnapshot:
    today_iso = date.today().isoformat()
    output_path = output_path or DEFAULT_OUTPUT
    snap = CorporateEventsSnapshot(fetch_date=today_iso, record_count=0)

    try:
        rows = fetch_unvan_changes(years_back=years_back)
    except Exception as e:
        snap.error = f"{type(e).__name__}: {e}"
        return snap

    mappings = parse_corporate_events(rows, today_iso=today_iso)
    snap.records = mappings
    snap.record_count = len(mappings)
    snap.notes.append(f"Subject: srp2205201502 (Ünvan Değişikliği)")
    snap.notes.append(f"Years back: {years_back}")
    n_with_old = sum(1 for m in mappings if m.old_ticker)
    snap.notes.append(
        f"Manual eski_ticker override: {n_with_old} of {len(mappings)} "
        f"(KNOWN_TICKER_MAPPINGS dict)"
    )

    if cache:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "fetch_date": snap.fetch_date,
            "record_count": snap.record_count,
            "subject_oid": SUBJECT_UNVAN_DEGISIKLIGI,
            "subject": "Ünvan Değişikliği",
            "years_back": years_back,
            "records": [asdict(m) for m in mappings],
            "notes": snap.notes,
        }
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        snap.notes.append(f"Cached: {output_path.name}")

    return snap


# ============================================================================
# Resolver (source_compare entegrasyonu için)
# ============================================================================

def resolve_ticker(snapshot: CorporateEventsSnapshot, ticker: str) -> Optional[Dict]:
    """Eski ticker → yeni ticker resolution.

    Source compare'da kpy41_acc5'te yoksa bu çağrılır.

    Returns: dict | None
      - {"status": "isim_değişti", "new_ticker": ..., "change_date": ..., "old_name": ...}
      - None: mapping yok (gerçek delisted candidate)
    """
    ticker = ticker.upper().strip()
    for m in snapshot.records:
        if m.old_ticker and m.old_ticker == ticker:
            return {
                "status": "isim_değişti",
                "new_ticker": m.new_ticker,
                "new_name": m.new_name,
                "old_name": m.old_name,
                "change_date": m.change_date,
                "disclosure_index": m.disclosure_index,
            }
    return None


def load_snapshot(path: Optional[Path] = None) -> Optional[CorporateEventsSnapshot]:
    """ticker_mappings.json'dan snapshot yükle."""
    path = path or DEFAULT_OUTPUT
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        snap = CorporateEventsSnapshot(
            fetch_date=data.get("fetch_date", ""),
            record_count=data.get("record_count", 0),
        )
        snap.records = [TickerMapping(**r) for r in data.get("records", [])]
        snap.notes = data.get("notes", [])
        return snap
    except Exception:
        return None


# ============================================================================
# CLI / Validation
# ============================================================================

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 78)
    print("KAP Corporate Events Tracker — Session 3F Production Validation")
    print("=" * 78)

    snap = fetch_corporate_events_snapshot(years_back=5, cache=True)
    if snap.error:
        print(f"  ✗ FAIL: {snap.error}")
        sys.exit(1)

    print(f"  ✓ Fetch date:    {snap.fetch_date}")
    print(f"  ✓ Records:       {snap.record_count} (Ünvan Değişikliği, son 5 yıl)")
    for n in snap.notes:
        print(f"    - {n}")

    print(f"\n── Latest 10 mappings ──")
    print(f"  {'Date':12} {'New':8} {'Old?':8} → {'New name'[:32]:32} | old_name (summary)")
    print('─'*78)
    for m in snap.records[:10]:
        old_t = m.old_ticker or "—"
        old_n = (m.old_name or "")[:50]
        new_n = (m.new_name or "")[:32]
        print(f"  {m.change_date:12} {m.new_ticker:8} {old_t:8} → {new_n:32} | {old_n}")

    print(f"\n── Validation: known anchor mappings ──")
    targets = [("KOZAL", "TRALT"), ("KOZAA", "TRMET"), ("IPEKE", "TRENJ")]
    for old_t, expected_new in targets:
        res = resolve_ticker(snap, old_t)
        if res and res["new_ticker"] == expected_new:
            print(f"  ✓ {old_t:6} → {res['new_ticker']:6} ({res['change_date']}) "
                  f"old_name={res['old_name']}")
        elif res:
            print(f"  ⚠ {old_t:6} → {res['new_ticker']} (expected {expected_new})")
        else:
            print(f"  ✗ {old_t:6} → mapping NOT FOUND")

    # MIPAZ check
    res_mipaz = resolve_ticker(snap, "MIPAZ")
    if res_mipaz:
        print(f"  ★ MIPAZ → {res_mipaz['new_ticker']} ({res_mipaz['change_date']})")
    else:
        # MIPAZ kpy41_acc5'te yok + ünvan değişikliği listesinde de yok →
        # gerçek delisted veya başka durum (kayyum/iflas — Session 5+ scope)
        print(f"  ⚠ MIPAZ: ne kpy41_acc5'te ne ünvan değişikliği listesinde "
              f"(gerçek delisted/kayyum candidate, Session 5+ scope)")

    print(f"\n  Output: {DEFAULT_OUTPUT}")
