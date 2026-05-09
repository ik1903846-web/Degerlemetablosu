#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Damodaran Vintage Parser - Session 5.1
=======================================

Damodaran xlsx dosyalarinin "vintage" tarihini iki bagimsiz
kaynaktan cikarip cross-check eder.

Primary:    HTTP Last-Modified header (RFC 7231)
Secondary:  XLSX file properties.modified (workbook metadata)
Cross-check: < 1 gun fark = OK, > 1 gun = WARNING

Hardcoded CTRYPREM_VINTAGE / BETAS_VINTAGE sabitlerinin
yerine kullanilir. Production kullanim Session 5.4'te
(auto regen trigger).

YASAK: fetch_damodaran.py v1 dokunulmaz. Bu modul standalone.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional

import httpx
from openpyxl import load_workbook

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15.0
CROSS_CHECK_TOLERANCE_SECONDS = 86400  # 1 gun


@dataclass
class VintageResult:
    """Vintage parse sonucu."""
    vintage: str  # "YYYY-MM"
    primary_source: str  # "http" veya "xlsx"
    http_last_modified: Optional[datetime]
    xlsx_modified: Optional[datetime]
    cross_check_ok: bool
    cross_check_delta_seconds: Optional[float]
    warnings: list[str]


def fetch_http_vintage(url: str, timeout: float = DEFAULT_TIMEOUT) -> Optional[datetime]:
    """HEAD request, Last-Modified header'i datetime'a cevir.

    Damodaran sunucu RFC 7231 format kullaniyor:
      "Mon, 16 Feb 2026 22:20:18 GMT"

    Returns:
        datetime (UTC tz-aware) veya None (header yok / hata)
    """
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            r = client.head(url)
            r.raise_for_status()
            lm = r.headers.get("last-modified")
            if not lm:
                logger.warning(f"Last-Modified header yok: {url}")
                return None
            dt = parsedate_to_datetime(lm)
            # RFC 7231 her zaman GMT, ama tz-aware olsun
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    except Exception as e:
        logger.error(f"HTTP HEAD fail {url}: {type(e).__name__}: {e}")
        return None


def read_xlsx_vintage(path: Path) -> Optional[datetime]:
    """XLSX file properties'den modified tarihini oku.

    workbook.properties.modified naive datetime (lokal saat dilimi
    bilinmiyor). UTC oldugu varsayilir (Damodaran'in upload
    server'i UTC oldugundan, en azindan tutarli baseline).

    Returns:
        datetime (UTC tz-aware varsayim) veya None
    """
    if not path.exists():
        logger.warning(f"XLSX dosyasi yok: {path}")
        return None
    try:
        wb = load_workbook(path, data_only=True, read_only=True)
        modified = wb.properties.modified
        if modified is None:
            logger.warning(f"XLSX properties.modified yok: {path}")
            return None
        # Naive datetime ise UTC varsay
        if modified.tzinfo is None:
            modified = modified.replace(tzinfo=timezone.utc)
        return modified
    except Exception as e:
        logger.error(f"XLSX read fail {path}: {type(e).__name__}: {e}")
        return None


def cross_check(http_dt: Optional[datetime],
                xlsx_dt: Optional[datetime],
                tolerance_seconds: int = CROSS_CHECK_TOLERANCE_SECONDS
                ) -> tuple[bool, Optional[float], list[str]]:
    """Iki kaynagi karsilastir.

    Returns:
        (ok, delta_seconds, warnings)
        ok=True if both present and within tolerance
        ok=False if mismatch or one missing
    """
    warnings = []

    if http_dt is None and xlsx_dt is None:
        warnings.append("Iki kaynak da bos")
        return False, None, warnings

    if http_dt is None:
        warnings.append("HTTP Last-Modified yok, sadece XLSX")
        return False, None, warnings

    if xlsx_dt is None:
        warnings.append("XLSX modified yok, sadece HTTP")
        return False, None, warnings

    delta = abs((http_dt - xlsx_dt).total_seconds())

    if delta > tolerance_seconds:
        warnings.append(
            f"Cross-check FAIL: HTTP {http_dt.isoformat()} vs "
            f"XLSX {xlsx_dt.isoformat()}, delta {delta:.0f}s "
            f"(> {tolerance_seconds}s tolerance)"
        )
        return False, delta, warnings

    return True, delta, warnings


def format_vintage(dt: datetime) -> str:
    """datetime -> 'YYYY-MM' string."""
    return dt.strftime("%Y-%m")


def get_vintage(url: str,
                xlsx_path: Optional[Path] = None,
                tolerance_seconds: int = CROSS_CHECK_TOLERANCE_SECONDS
                ) -> VintageResult:
    """Hibrit vintage parse: HTTP primary, XLSX secondary, cross-check.

    Args:
        url: Damodaran xlsx URL'i (HEAD request hedefi)
        xlsx_path: Lokal indirilmis xlsx dosyasi (optional, cross-check)
        tolerance_seconds: Cross-check tolerance (default 1 gun)

    Returns:
        VintageResult dataclass
    """
    http_dt = fetch_http_vintage(url)
    xlsx_dt = read_xlsx_vintage(xlsx_path) if xlsx_path else None

    ok, delta, cc_warnings = cross_check(http_dt, xlsx_dt, tolerance_seconds)

    # Primary kaynak secimi: HTTP varsa onu kullan, yoksa XLSX
    if http_dt is not None:
        primary_dt = http_dt
        primary_source = "http"
    elif xlsx_dt is not None:
        primary_dt = xlsx_dt
        primary_source = "xlsx"
    else:
        # Iki kaynak da bos - degerleme yapilamaz
        return VintageResult(
            vintage="",
            primary_source="none",
            http_last_modified=None,
            xlsx_modified=None,
            cross_check_ok=False,
            cross_check_delta_seconds=None,
            warnings=cc_warnings + ["Vintage cikarilamadi"],
        )

    return VintageResult(
        vintage=format_vintage(primary_dt),
        primary_source=primary_source,
        http_last_modified=http_dt,
        xlsx_modified=xlsx_dt,
        cross_check_ok=ok,
        cross_check_delta_seconds=delta,
        warnings=cc_warnings,
    )


# ────────────────────────────────────────────────────────────────────
# Standalone smoke test
# ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    DAMOD_DIR = Path(__file__).resolve().parents[3] / \
                "apps" / "api" / "data" / "damodaran" / "2026_05_09"

    targets = [
        ("ctryprem",
         "https://pages.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx",
         DAMOD_DIR / "ctryprem.xlsx"),
        ("ERPbymonth",
         "https://pages.stern.nyu.edu/~adamodar/pc/implprem/ERPbymonth.xlsx",
         DAMOD_DIR / "ERPbymonth.xlsx"),
    ]

    print("=" * 60)
    print("Damodaran Vintage Parser - Smoke Test")
    print("=" * 60)

    all_ok = True
    for name, url, xlsx_path in targets:
        print(f"\n[{name}]")
        result = get_vintage(url, xlsx_path)
        print(f"  vintage:               {result.vintage}")
        print(f"  primary_source:        {result.primary_source}")
        print(f"  http_last_modified:    {result.http_last_modified}")
        print(f"  xlsx_modified:         {result.xlsx_modified}")
        print(f"  cross_check_ok:        {result.cross_check_ok}")
        print(f"  cross_check_delta:     "
              f"{result.cross_check_delta_seconds:.0f}s"
              if result.cross_check_delta_seconds is not None
              else "  cross_check_delta:     None")
        if result.warnings:
            print(f"  warnings:")
            for w in result.warnings:
                print(f"    - {w}")
        if not result.cross_check_ok:
            all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("PASS: Tum hedefler cross-check OK")
        sys.exit(0)
    else:
        print("FAIL: Bir veya daha fazla hedefte issue var")
        sys.exit(1)
