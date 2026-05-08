"""
SPK Universe Fetcher (Faz 11 v4.0 — Session 1A).

Hedef: SPK 'Payları Borsada İşlem Gören Şirketler' 605 ticker (2026/05).

Strategy attempt order:
  B (Excel):  ✗ FAIL — sayfa SvelteKit SPA, JS render gerek
  A (HTML):   ✗ FAIL — SSR yok, page <body> empty
  C (JSON):   ✗ FAIL — /__data.json + /api/* hep 406 döndü

PROXY STRATEGY (kullanılan):
  KAP IGS member list filter:
    GET /tr/api/company/items/IGS/A  → 727 şirket
    Filter: payIslemDurumu == "1"   → 606 ticker (SPK 605'e ±1 yakın)

  ★ SPK 605 vs KAP 606: 1 fark tolere edilir (yeni IPO timing,
    delistir transit). Aylık SPK official figure ile cross-check.

NOT: Production'da direct fetch_borsa_listed_companies() KAP proxy döner.
Asıl SPK fetch için Selenium/Playwright gerekir (Faz 11.x parking).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import httpx


KAP_BASE_URL = "https://www.kap.org.tr"
KAP_COMPANY_ITEMS_URL = f"{KAP_BASE_URL}/tr/api/company/items"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Origin": KAP_BASE_URL,
    "Referer": f"{KAP_BASE_URL}/tr/bildirim-sorgu",
}

# Member types containing listed companies
KAP_MEMBER_TYPES = ["IGS", "BDK", "YK", "PYS"]


@dataclass
class SPKUniverseSnapshot:
    """SPK 'Borsa Listed' universe snapshot (KAP proxy)."""

    fetch_date: str
    source: str  # "kap_proxy_igs" | "spk_direct" | "selenium"
    borsa_listed_count: int = 0
    tickers: List[str] = field(default_factory=list)
    company_metadata: List[Dict] = field(default_factory=list)
    raw_kap_total: int = 0
    payislem_active_count: int = 0
    notes: List[str] = field(default_factory=list)


def _fetch_kap_member_type(member_type: str, state: str = "A") -> List[Dict]:
    """KAP /tr/api/company/items/<TYPE>/<STATE> fetch."""
    url = f"{KAP_COMPANY_ITEMS_URL}/{member_type}/{state}"
    with httpx.Client(headers=DEFAULT_HEADERS, timeout=30.0) as c:
        r = c.get(url, follow_redirects=True)
        if r.status_code != 200:
            return []
        try:
            return r.json()
        except Exception:
            return []


def _parse_stockcodes(raw: str) -> List[str]:
    """Field 'stockCode' may contain "A, B" → ["A", "B"]."""
    if not raw or raw == "-":
        return []
    parts = [p.strip().upper() for p in raw.split(",") if p.strip()]
    return [p for p in parts if p and p != "-"]


def fetch_borsa_listed_companies() -> SPKUniverseSnapshot:
    """SPK 'Borsa Listed' proxy — KAP IGS payIslemDurumu=1 filter.

    Returns SPK universe snapshot ~605 ticker.
    """
    igs = _fetch_kap_member_type("IGS", "A")

    raw_total = len(igs)
    payislem_active = [
        c for c in igs if c.get("payIslemDurumu") == "1"
    ]
    n_pay_active = len(payislem_active)

    tickers: List[str] = []
    metadata: List[Dict] = []
    seen: set = set()

    for c in payislem_active:
        codes = _parse_stockcodes(c.get("stockCode", ""))
        for code in codes:
            if code in seen:
                continue
            seen.add(code)
            tickers.append(code)
            metadata.append({
                "ticker": code,
                "kap_member_oid": c.get("kapMemberOid"),
                "mkk_member_oid": c.get("mkkMemberOid"),
                "company_title": c.get("kapMemberTitle"),
                "tax_no": c.get("taxNo"),
                "city": c.get("cityName"),
                "kap_type": c.get("kapMemberType"),
                "faaliyet_durumu": c.get("faaliyetDurumu"),
                "pay_islem_durumu": c.get("payIslemDurumu"),
            })

    snapshot = SPKUniverseSnapshot(
        fetch_date=date.today().isoformat(),
        source="kap_proxy_igs_payislem1",
        borsa_listed_count=len(tickers),
        tickers=sorted(tickers),
        company_metadata=metadata,
        raw_kap_total=raw_total,
        payislem_active_count=n_pay_active,
        notes=[
            f"SPK direct fetch FAIL (SvelteKit SPA, no public REST API).",
            f"Strategy used: KAP IGS payIslemDurumu=1 filter.",
            f"KAP IGS total: {raw_total}, payIslem=1: {n_pay_active}",
            f"Unique tickers (after stockCode multi-class split): {len(tickers)}",
            f"Expected SPK 2026/05: 605 borsa listed (1-3 ticker gap acceptable).",
        ],
    )
    return snapshot


def write_snapshot(snapshot: SPKUniverseSnapshot, out_path: Path) -> None:
    """spk_listed_universe.json kaydet."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetch_date": snapshot.fetch_date,
        "source": snapshot.source,
        "borsa_listed_count": snapshot.borsa_listed_count,
        "raw_kap_total": snapshot.raw_kap_total,
        "payislem_active_count": snapshot.payislem_active_count,
        "tickers": snapshot.tickers,
        "company_metadata": snapshot.company_metadata,
        "notes": snapshot.notes,
    }
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def compare_with_existing_universe(
    new_tickers: List[str],
    existing_universe_module: str = "dcf_engine.batch_analyzer",
    existing_attr: str = "BIST_TUM",
) -> Dict:
    """Yeni SPK 605 vs eski 559 (BIST_TUM) subset analizi."""
    try:
        import importlib

        mod = importlib.import_module(existing_universe_module)
        old = set(getattr(mod, existing_attr, []))
    except Exception:
        old = set()

    new = set(new_tickers)
    return {
        "old_universe_count": len(old),
        "new_universe_count": len(new),
        "intersection": len(new & old),
        "new_only_count": len(new - old),
        "old_only_count": len(old - new),
        "new_only_sample": sorted(new - old)[:30],
        "old_only_sample": sorted(old - new)[:30],
    }


if __name__ == "__main__":
    import sys
    import io

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 70)
    print("SPK Universe Fetcher (Faz 11 Session 1A)")
    print("=" * 70)

    snap = fetch_borsa_listed_companies()
    print(f"\nFetch date: {snap.fetch_date}")
    print(f"Source:     {snap.source}")
    print(f"Tickers:    {snap.borsa_listed_count}")
    print(f"\nNotes:")
    for n in snap.notes:
        print(f"  - {n}")

    print(f"\nFirst 20 tickers: {snap.tickers[:20]}")
    print(f"Last 10:          {snap.tickers[-10:]}")

    # Save
    outputs = Path(__file__).resolve().parents[1] / "outputs"
    out_path = outputs / "spk_listed_universe.json"
    write_snapshot(snap, out_path)
    print(f"\nSaved: {out_path.relative_to(Path.cwd())}"
          if out_path.is_relative_to(Path.cwd())
          else f"\nSaved: {out_path}")

    # Compare
    print("\n" + "=" * 70)
    print("Subset analysis: new SPK ~605 vs old BIST_TUM 559")
    print("=" * 70)
    cmp = compare_with_existing_universe(snap.tickers)
    print(f"  Old (BIST_TUM):  {cmp['old_universe_count']}")
    print(f"  New (SPK proxy): {cmp['new_universe_count']}")
    print(f"  Intersection:    {cmp['intersection']}")
    print(f"  New-only:        {cmp['new_only_count']}")
    print(f"  Old-only:        {cmp['old_only_count']}")
    print(f"\n  New-only sample (first 30):")
    for t in cmp["new_only_sample"]:
        print(f"    {t}")
    if cmp["old_only_count"] > 0:
        print(f"\n  Old-only sample (first 30 — eski universe'de var, SPK'da yok):")
        for t in cmp["old_only_sample"]:
            print(f"    {t}")
