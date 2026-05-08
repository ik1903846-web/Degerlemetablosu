"""
KAP Official API Custom Wrapper (Faz 11 v4.0 — Session 1B).

Mevcut kap-client 1.1.1 OUTDATED (member_types listesinde 'IGS' yok,
TUPRS bile bulunamıyor — Faz 11 mini prototype evidence).

Bu modül resmi KAP REST API ile direct httpx wrapper:
  - /tr/api/company/items/<TYPE>/<STATE>          — company list
  - /tr/api/disclosure/members/byCriteria         — disclosure search
  - /tr/Bildirim/<index>                          — disclosure HTML
  - <attachment_url>                              — XBRL .zip download

Disclosure subject_oid (FINANSAL_RAPOR):
  - Yıllık/3aylık finansal raporlar için subject filtre
  - kap-client'ten bilinen value (FundSubject.FINANSAL_RAPOR)

Production orchestrator henüz buraya bağlı DEĞİL (Lesson #21 anchor-safe).
Faz 11.x Session 4'te orchestrator_v4.py bu wrapper'ı kullanacak.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


KAP_BASE_URL = "https://www.kap.org.tr"
KAP_COMPANY_ITEMS_URL = f"{KAP_BASE_URL}/tr/api/company/items"
KAP_MEMBER_DISCLOSURE_URL = (
    f"{KAP_BASE_URL}/tr/api/disclosure/members/byCriteria"
)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Origin": KAP_BASE_URL,
    "Referer": f"{KAP_BASE_URL}/tr/bildirim-sorgu",
}

# Subject OIDs — pykap (recent KAP API format, Session 1.5 evidence)
# kap-client OID'leri OUTDATED, pykap source code'tan extracted:
SUBJECT_FINANSAL_RAPOR = "4028328c594bfdca01594c0af9aa0057"
SUBJECT_FAALIYET_RAPORU = "4028328d594c04f201594c5155dd0076"
# Disclosure class codes (KAP):
DISCLOSURE_CLASS_FR = "FR"   # Financial Report (zorunlu, pykap evidence)
DISCLOSURE_CLASS_OZD = "ODA"  # Özel Durum Açıklaması


@dataclass
class CompanyMeta:
    ticker: str
    kap_member_oid: Optional[str] = None
    mkk_member_oid: Optional[str] = None
    company_title: Optional[str] = None
    member_type: Optional[str] = None
    pay_islem_durumu: Optional[str] = None
    faaliyet_durumu: Optional[str] = None
    raw: Optional[Dict] = None


@dataclass
class DisclosureRecord:
    """KAP disclosure listing entry."""
    disclosure_index: Optional[int] = None
    publish_date: Optional[str] = None
    subject: Optional[str] = None
    title: Optional[str] = None
    company_oid: Optional[str] = None
    raw: Optional[Dict] = None


@dataclass
class CompanyDisclosureSummary:
    ticker: str
    company: Optional[CompanyMeta] = None
    disclosures: List[DisclosureRecord] = field(default_factory=list)
    error: Optional[str] = None


# ============================================================================
# Company Resolution
# ============================================================================

# Module-level memoize: paralel ortamda her thread tek seferlik fetch
# (önceden her find_company çağrısı ile fetch_companies tetikleniyor,
#  ThreadPoolExecutor 5 worker × 6 endpoint × N ticker → KAP rate limit
#  → "no_FR" empty response. Memoize ile 1 kez fetch + cache).
_COMPANIES_CACHE: Optional[List[CompanyMeta]] = None
_COMPANIES_CACHE_LOCK = None  # threading.Lock — lazy init


def _get_companies_lock():
    global _COMPANIES_CACHE_LOCK
    if _COMPANIES_CACHE_LOCK is None:
        from threading import Lock
        _COMPANIES_CACHE_LOCK = Lock()
    return _COMPANIES_CACHE_LOCK


def fetch_companies(
    member_types: Optional[List[str]] = None,
    force_refresh: bool = False,
) -> List[CompanyMeta]:
    """KAP IGS+BDK+YK+PYS member types union.

    Module-level memoize: ilk çağrıda tüm 4 member type'ı fetch eder,
    sonraki çağrılar in-memory cache döndürür. Thread-safe.

    IGS = Industrial general (BIST listed companies)
    BDK = Bankalar
    YK   = Yatırım Kuruluşları
    PYS  = Portföy Yönetim Şirketleri
    """
    global _COMPANIES_CACHE
    # Default args ile cache döndür
    if (member_types is None and not force_refresh
            and _COMPANIES_CACHE is not None):
        return _COMPANIES_CACHE

    with _get_companies_lock():
        if (member_types is None and not force_refresh
                and _COMPANIES_CACHE is not None):
            return _COMPANIES_CACHE

        types = member_types or ["IGS", "BDK", "YK", "PYS"]
        results: Dict[str, CompanyMeta] = {}

        with httpx.Client(headers=DEFAULT_HEADERS, timeout=30.0) as c:
            for mt in types:
                try:
                    r = c.get(
                        f"{KAP_COMPANY_ITEMS_URL}/{mt}/A",
                        follow_redirects=True,
                    )
                    if r.status_code != 200:
                        continue
                    rows = r.json() or []
                except Exception:
                    continue

                for row in rows:
                    stock_codes = (row.get("stockCode") or "").split(",")
                    for sc in stock_codes:
                        sc = sc.strip().upper()
                        if not sc or sc == "-":
                            continue
                        if sc in results:
                            continue
                        results[sc] = CompanyMeta(
                            ticker=sc,
                            kap_member_oid=row.get("kapMemberOid"),
                            mkk_member_oid=row.get("mkkMemberOid"),
                            company_title=row.get("kapMemberTitle"),
                            member_type=row.get("kapMemberType"),
                            pay_islem_durumu=row.get("payIslemDurumu"),
                            faaliyet_durumu=row.get("faaliyetDurumu"),
                            raw=row,
                        )

        out = list(results.values())
        if member_types is None:
            _COMPANIES_CACHE = out
        return out


def find_company(ticker: str) -> Optional[CompanyMeta]:
    """Tek ticker resolve (IGS+BDK+YK+PYS scan, memoized)."""
    ticker = ticker.upper().strip()
    for c in fetch_companies():
        if c.ticker == ticker:
            return c
    return None


# ============================================================================
# Disclosure Listing
# ============================================================================

def fetch_disclosures(
    ticker: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    subject_oid: Optional[str] = SUBJECT_FINANSAL_RAPOR,
    days_back: int = 365,
) -> CompanyDisclosureSummary:
    """KAP disclosure search (member oid + date range + subject filter).

    NOT: KAP API tarih aralığı **max 365 gün** (Session 1.5 evidence).
    Daha geniş aralık için chunked fetch yap (auto-split 365 gün).
    """

    summary = CompanyDisclosureSummary(ticker=ticker.upper())

    # Resolve company
    company = find_company(ticker)
    if not company or not company.mkk_member_oid:
        summary.error = f"Company '{ticker}' not found in KAP IGS/BDK/YK/PYS"
        return summary
    summary.company = company

    end_date = end_date or date.today()
    start_date = start_date or (end_date - timedelta(days=days_back))

    # Date range chunk (KAP 365-day limit, Session 1.5 evidence)
    chunks: list[tuple[date, date]] = []
    cur_end = end_date
    while cur_end > start_date:
        cur_start = max(start_date, cur_end - timedelta(days=365))
        chunks.append((cur_start, cur_end))
        cur_end = cur_start - timedelta(days=1)
        if cur_end <= start_date:
            break

    # Multi-chunk fetch (KAP 365-day limit per request)
    seen_idx: set = set()
    try:
        with httpx.Client(headers=DEFAULT_HEADERS, timeout=30.0) as c:
            for ch_start, ch_end in chunks:
                payload = {
                    "fromDate": ch_start.isoformat(),
                    "toDate": ch_end.isoformat(),
                    "disclosureClass": DISCLOSURE_CLASS_FR,
                    "subjectList": [subject_oid] if subject_oid else [SUBJECT_FINANSAL_RAPOR],
                    "mkkMemberOidList": [company.mkk_member_oid],
                    "inactiveMkkMemberOidList": [],
                    "bdkMemberOidList": [],
                    "fromSrc": False,
                    "disclosureIndexList": [],
                }
                r = c.post(
                    KAP_MEMBER_DISCLOSURE_URL,
                    json=payload,
                    follow_redirects=True,
                )
                if r.status_code != 200:
                    summary.error = (
                        f"Chunk {ch_start}/{ch_end} POST {r.status_code}: {r.text[:120]}"
                    )
                    return summary

                rows = r.json() or []
                for row in rows:
                    idx = row.get("disclosureIndex") or row.get("index")
                    if idx in seen_idx:
                        continue
                    seen_idx.add(idx)
                    summary.disclosures.append(DisclosureRecord(
                        disclosure_index=idx,
                        publish_date=(
                            row.get("publishDate")
                            or row.get("kapPublishDate")
                        ),
                        subject=row.get("subject") or row.get("disclosureClass"),
                        title=row.get("summary") or row.get("kapTitle"),
                        company_oid=row.get("memberOid"),
                        raw=row,
                    ))
    except Exception as e:
        summary.error = f"Disclosure fetch error: {type(e).__name__}: {e}"

    # Sort newest-first
    summary.disclosures.sort(
        key=lambda d: d.publish_date or "",
        reverse=True,
    )
    return summary


# ============================================================================
# Attachment Download (XBRL .zip)
# ============================================================================

def fetch_attachment_urls(disclosure_index: int) -> List[str]:
    """Disclosure detail page → attachment URL listesi.

    KAP Bildirim/<index> sayfasında attachments embedded.
    Faz 11 Session 2'de XBRL parse için kullanılır.
    """
    url = f"{KAP_BASE_URL}/tr/Bildirim/{disclosure_index}"
    try:
        with httpx.Client(headers=DEFAULT_HEADERS, timeout=30.0) as c:
            r = c.get(url, follow_redirects=True)
            if r.status_code != 200:
                return []
            # Attachment URLs typically in href patterns
            import re
            attach_urls = re.findall(
                r'href="([^"]*(?:ek-indir|tr/ek-indir)[^"]*)"',
                r.text,
            )
            return [
                u if u.startswith("http") else f"{KAP_BASE_URL}{u}"
                for u in attach_urls
            ]
    except Exception:
        return []


# ============================================================================
# Probe / CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    import io

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 70)
    print("KAP Official v2 — Session 1B Probe")
    print("=" * 70)

    # Test 4 ticker (TUPRS anchor + KUYAS bug + 2 yeni IPO)
    targets = ["TUPRS", "KUYAS", "AGROT", "EUPWR"]

    for ticker in targets:
        print(f"\n{'─'*70}")
        print(f"TICKER: {ticker}")
        print('─'*70)

        company = find_company(ticker)
        if not company:
            print(f"  ✗ NOT FOUND in KAP")
            continue

        print(f"  ✓ Resolved: {company.company_title}")
        print(f"    OID:           {company.kap_member_oid}")
        print(f"    MKK OID:       {company.mkk_member_oid}")
        print(f"    Member type:   {company.member_type}")
        print(f"    PayIslem:      {company.pay_islem_durumu}")
        print(f"    Faaliyet:      {company.faaliyet_durumu}")

        summary = fetch_disclosures(
            ticker,
            subject_oid=SUBJECT_FINANSAL_RAPOR,
            days_back=730,
        )
        if summary.error:
            print(f"  ⚠ Disclosure error: {summary.error}")
            continue

        n = len(summary.disclosures)
        print(f"  📋 FINANSAL_RAPOR disclosures (2 yıl): {n}")
        for d in summary.disclosures[:5]:
            print(f"    - [{d.disclosure_index}] {d.publish_date}: "
                  f"{(d.subject or '')[:50]}")
