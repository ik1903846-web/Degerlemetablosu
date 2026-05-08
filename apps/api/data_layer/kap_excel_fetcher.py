"""
KAP Excel Export Fetcher (Faz 11 v4.0 — Session 2 REVISED).

Session 2 BLOCKER → ÇÖZÜLDÜ ✓
  Endpoint: /tr/api/notification/export/excel/{disclosure_id}
  Format:   application/vnd.ms-excel (Excel HTML, single-file save-as-web)
  Parse:    pandas.read_html() / BeautifulSoup ile structured table extract
  Boyut:    1-2 MB per disclosure (TUPRS Q3 2025: 1.39 MB)

KEŞİF NOTU:
  Session 2 ilk denemesinde `/exportSgbfAndYfbfFinancialPage/` 666 hata,
  sonra TUPRS Bildirim page'inde `/notification/export/word` link bulundu,
  o pattern'den `excel` denenince ÇÖZÜLDÜ.

Production orchestrator henüz buraya bağlı DEĞİL.
Faz 11 Session 4'te orchestrator_v4.py bu wrapper'ı kullanacak.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


KAP_BASE_URL = "https://www.kap.org.tr"
KAP_EXCEL_EXPORT_URL = f"{KAP_BASE_URL}/tr/api/notification/export/excel"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}

CACHE_DIR = Path(__file__).resolve().parents[1] / "_cache" / "kap_excel"


@dataclass
class ExcelDownloadResult:
    disclosure_index: int
    success: bool
    content_bytes: bytes = b""
    file_path: Optional[Path] = None
    content_length: int = 0
    error: Optional[str] = None


def fetch_excel_export(
    disclosure_index: int,
    cache: bool = True,
    force_refresh: bool = False,
) -> ExcelDownloadResult:
    """KAP financial report Excel-HTML export.

    Args:
        disclosure_index: KAP disclosure index (örn 1510162)
        cache:            File cache aktif/pasif
        force_refresh:    Cache atlat, yeniden indir

    Returns:
        ExcelDownloadResult — content_bytes (parse için) + file_path (debug)
    """
    result = ExcelDownloadResult(disclosure_index=disclosure_index, success=False)

    cache_path = CACHE_DIR / f"kap_excel_{disclosure_index}.xls"

    if cache and not force_refresh and cache_path.exists():
        try:
            result.content_bytes = cache_path.read_bytes()
            result.file_path = cache_path
            result.content_length = len(result.content_bytes)
            result.success = True
            return result
        except Exception:
            pass  # cache corrupt, refresh

    url = f"{KAP_EXCEL_EXPORT_URL}/{disclosure_index}"
    referer = f"{KAP_BASE_URL}/tr/Bildirim/{disclosure_index}"
    headers = {**DEFAULT_HEADERS, "Referer": referer}

    try:
        with httpx.Client(headers=headers, timeout=60.0) as c:
            r = c.get(url, follow_redirects=True)
            if r.status_code != 200:
                result.error = f"HTTP {r.status_code}: {r.text[:120]}"
                return result

            ct = r.headers.get("content-type", "")
            if "excel" not in ct.lower() and "msword" not in ct.lower():
                result.error = f"Unexpected content-type: {ct}"
                return result

            result.content_bytes = r.content
            result.content_length = len(r.content)

            if cache:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                cache_path.write_bytes(r.content)
                result.file_path = cache_path

            result.success = True

    except Exception as e:
        result.error = f"{type(e).__name__}: {e}"

    return result


if __name__ == "__main__":
    import sys
    import io

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 70)
    print("KAP Excel Fetcher — Session 2 Revised Probe")
    print("=" * 70)

    # 4 ticker × en yeni FR disclosure_index
    targets = [
        ("TUPRS",   1510162),  # Q3 2025
        ("KUYAS",   1480086),  # Q2 2025
        ("AGROT",   1481009),  # Q2 2025
        ("EUPWR",   1483800),  # tahmin (Session 1.5'de listed, exact idx Session 1.5 raporda)
    ]

    for ticker, idx in targets:
        print(f"\n{'─'*70}")
        print(f"{ticker}  disclosure_index={idx}")
        print('─'*70)
        res = fetch_excel_export(idx)
        if res.success:
            print(f"  ✓ Downloaded {res.content_length:,} bytes")
            print(f"    Cache: {res.file_path}")
        else:
            print(f"  ✗ Error: {res.error}")
