"""
KAP Sector Fetcher (Faz 11 v4.0 — Session 3.6 ADIM A).

Endpoint:
  GET https://kap.org.tr/tr/Sektorler

Sayfa Next.js SSR'da JSON embedded içerir:
  {
    "sectorName": "KIMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER",
    "sectorOid":  "33E5FED8039E00EAE0530A4A622B2AEA",
    "sectorNo":   "003000.005000.",
    "mkkMemberOid": "...",
    "stockCode":  "TUPRS",
    "title":      "TÜPRAŞ-TÜRKİYE PETROL RAFİNERİLERİ A.Ş.",
    "kapTypes":   ["IGS"]
  }

KAP sectorNo hiyerarşisi: "003000.005000." dot-separated:
  - "003000"  = Ana sektör grubu (BIST endeks koddu benzeri)
  - "005000"  = Alt sektör (eğer varsa)
  - 3-level granularity mümkün (ana.alt.spesifik)

Damodaran granularity için bazı sektörler genişletilebilir
(örn. "Petrol Rafineri" ≠ "İlaç" ≠ "Plastik" aynı broad bucket'ta).
Manuel override Session 3.6 ADIM A'da hibrid yaklaşım için
opsiyonel (apps/api/config/sector_overrides.json).
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import httpx


KAP_BASE_URL = "https://www.kap.org.tr"
KAP_SEKTORLER_URL = f"{KAP_BASE_URL}/tr/Sektorler"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Origin": KAP_BASE_URL,
    "Referer": KAP_BASE_URL,
}

CACHE_DIR = Path(__file__).resolve().parents[1] / "_cache"
DEFAULT_OUTPUT = CACHE_DIR / "ticker_sectors.json"


@dataclass
class SectorEntry:
    ticker: str
    company_title: str
    sector_name: str
    sector_oid: str
    sector_no: str            # "003000.005000." dot-separated KAP code
    mkk_member_oid: Optional[str]
    kap_types: List[str] = field(default_factory=list)


@dataclass
class SectorSnapshot:
    fetch_date: str
    record_count: int
    distinct_sectors: int = 0
    records: List[SectorEntry] = field(default_factory=list)
    error: Optional[str] = None
    notes: List[str] = field(default_factory=list)


# ============================================================================
# Parser
# ============================================================================

# JSON içindeki entry pattern: KAP HTML'de stringify edilmiş şekilde geçer.
# Backslashed quotes: \"sectorName\":\"...\",\"sectorOid\":\"...\",\"sectorNo\":\"...\",
#   \"mkkMemberOid\":\"...\",\"stockCode\":\"...\",\"title\":\"...\",\"kapTypes\":[\"IGS\"]
#
# Tek bir entry block'unu kapsayan regex:
_ENTRY_RE = re.compile(
    r'\\"sectorName\\":\\"(?P<sname>[^"\\]+)\\"'
    r',\\"sectorOid\\":\\"(?P<soid>[A-F0-9]+)\\"'
    r',\\"sectorNo\\":\\"(?P<sno>[\d.]+)\\"'
    r'(?:,\\"mkkMemberOid\\":\\"(?P<mkk>[A-Za-z0-9]+)\\")?'
    # stockCode multi-class olabilir: "GARAN, TGB" / "SEK, SKBNK" — virgül + space kabul
    r',\\"stockCode\\":\\"(?P<code>[A-Z0-9][A-Z0-9, ]*)\\"'
    r',\\"title\\":\\"(?P<title>[^"\\]+)\\"'
    r'(?:,\\"kapTypes\\":\[(?P<ktypes>[^\]]*)\])?'
)


def _decode_tr(s: str) -> str:
    """Strip + return as-is (HTML zaten doğru utf-8 decode edildi)."""
    if not s:
        return ""
    return s.strip()


def fetch_sektorler_html(timeout: float = 30.0) -> str:
    with httpx.Client(headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True) as c:
        r = c.get(KAP_SEKTORLER_URL)
        if r.status_code != 200:
            raise RuntimeError(f"KAP /tr/Sektorler HTTP {r.status_code}")
        # KAP HTTP response charset header eksik olabilir → manual utf-8 force
        return r.content.decode("utf-8", errors="replace")


def parse_sektorler_html(html: str) -> List[SectorEntry]:
    records: List[SectorEntry] = []
    seen: set = set()
    for m in _ENTRY_RE.finditer(html):
        # stockCode multi-class olabilir ("GARAN, TGB") — virgülle ayır
        code_raw = m.group("code")
        ticker_list = [
            t.strip().upper() for t in code_raw.split(",") if t.strip()
        ]
        if not ticker_list:
            continue

        sector_name = _decode_tr(m.group("sname"))
        company_title = _decode_tr(m.group("title"))
        ktypes_raw = m.group("ktypes") or ""
        kap_types = [
            t.strip().strip('\\"').upper()
            for t in re.findall(r'\\"([^"\\]+)\\"', ktypes_raw)
        ]

        # Her stock code (multi-class) için ayrı kayıt
        for ticker in ticker_list:
            if ticker in seen:
                continue
            seen.add(ticker)
            records.append(SectorEntry(
                ticker=ticker,
                company_title=company_title,
                sector_name=sector_name,
                sector_oid=m.group("soid"),
                sector_no=m.group("sno"),
                mkk_member_oid=m.group("mkk"),
                kap_types=kap_types,
            ))
    return records


def fetch_sectors_snapshot(
    output_path: Optional[Path] = None,
    cache: bool = True,
) -> SectorSnapshot:
    today_iso = date.today().isoformat()
    output_path = output_path or DEFAULT_OUTPUT
    snap = SectorSnapshot(fetch_date=today_iso, record_count=0)

    try:
        html = fetch_sektorler_html()
    except Exception as e:
        snap.error = f"{type(e).__name__}: {e}"
        return snap

    records = parse_sektorler_html(html)
    if not records:
        snap.error = "No sector entries parsed (regex mismatch)"
        return snap

    snap.records = records
    snap.record_count = len(records)
    snap.distinct_sectors = len({r.sector_oid for r in records})
    snap.notes.append(f"KAP /tr/Sektorler — JSON embedded extract")
    snap.notes.append(
        f"Hierarchical sectorNo (örn '003000.005000.') = ana.alt KAP code"
    )

    if cache:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "fetch_date": snap.fetch_date,
            "record_count": snap.record_count,
            "distinct_sectors": snap.distinct_sectors,
            "records": [asdict(r) for r in records],
            "notes": snap.notes,
        }
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        snap.notes.append(f"Cached: {output_path.name}")

    return snap


# ============================================================================
# Resolver helpers
# ============================================================================

def lookup_sector(snapshot: SectorSnapshot, ticker: str) -> Optional[SectorEntry]:
    ticker = ticker.upper().strip()
    for r in snapshot.records:
        if r.ticker == ticker:
            return r
    return None


def group_by_sector(snapshot: SectorSnapshot) -> Dict[str, List[SectorEntry]]:
    """sectorOid → [tickers]. Beta hesabı için sektör grupları."""
    out: Dict[str, List[SectorEntry]] = {}
    for r in snapshot.records:
        out.setdefault(r.sector_oid, []).append(r)
    return out


def load_snapshot(path: Optional[Path] = None) -> Optional[SectorSnapshot]:
    path = path or DEFAULT_OUTPUT
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        snap = SectorSnapshot(
            fetch_date=data.get("fetch_date", ""),
            record_count=data.get("record_count", 0),
            distinct_sectors=data.get("distinct_sectors", 0),
        )
        snap.records = [SectorEntry(**r) for r in data.get("records", [])]
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
    print("KAP Sector Fetcher — Session 3.6 ADIM A Validation")
    print("=" * 78)

    snap = fetch_sectors_snapshot(cache=True)
    if snap.error:
        print(f"  ✗ FAIL: {snap.error}")
        sys.exit(1)

    print(f"  ✓ Fetch date:        {snap.fetch_date}")
    print(f"  ✓ Records:           {snap.record_count}")
    print(f"  ✓ Distinct sectors:  {snap.distinct_sectors}")
    for n in snap.notes:
        print(f"    - {n}")

    # Anchor checks
    print(f"\n── Anchor lookup ──")
    targets = ["TUPRS", "GARAN", "AKBNK", "ARCLK", "THYAO", "SAHOL", "KCHOL",
               "TRALT", "TRMET", "TRENJ"]
    for t in targets:
        e = lookup_sector(snap, t)
        if e:
            print(f"  {t:6}: sector='{e.sector_name[:60]}' "
                  f"sectorNo='{e.sector_no}' types={e.kap_types}")
        else:
            print(f"  {t:6}: NOT FOUND")

    # Sektör dağılımı
    print(f"\n── Top 12 sectors by ticker count ──")
    groups = group_by_sector(snap)
    sector_size = sorted(
        [(name_oid, recs) for name_oid, recs in groups.items()],
        key=lambda x: len(x[1]), reverse=True,
    )
    for oid, recs in sector_size[:12]:
        sname = recs[0].sector_name[:60]
        sno = recs[0].sector_no
        sample = [r.ticker for r in recs[:5]]
        print(f"  {sno:18} {sname:55} ({len(recs):3d}) sample={sample}")

    # Tek firma sektörler
    print(f"\n── Single-firm sectors (Damodaran 'single_firm_sector' flag) ──")
    singles = [recs for recs in groups.values() if len(recs) == 1]
    print(f"  Count: {len(singles)}")
    for recs in singles[:12]:
        r = recs[0]
        print(f"    {r.ticker:6}  {r.sector_name[:55]}  ({r.sector_no})")

    print(f"\n  Output: {DEFAULT_OUTPUT}")
