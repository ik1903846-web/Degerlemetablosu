#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Damodaran Sector Multiples Fetcher — Phase 3c Adim 1
=====================================================

Damodaran 3 sector multiples Excel fetch + JSON output:
  pbvData.xls    -> Price/Book by Industry
  vebitda.xls    -> EV/EBITDA by Industry
  pedata.xls     -> PE by Industry

Output: apps/api/data/damodaran/YYYY_MM_DD/sector_multiples.json

Phase 3c Adim 3'te orchestrator_v4 fallback chain bu JSON'u tuketir.

Annual cadence (Damodaran Ocak update standart).
Damodaran daily check workflow hash-based diff zaten tetikler.

Stand-alone, mevcut fetch_damodaran.py DOKUNULMAZ.

Usage:
    python apps/api/data_layer/damodaran_sector_fetcher.py
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import date
from io import BytesIO
from pathlib import Path

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

DAMODARAN_VEBITDA_URL = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/vebitda.xls"
DAMODARAN_PE_URL = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/pedata.xls"
DAMODARAN_PBV_URL = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/pbvdata.xls"

# Damodaran format: "Industry Averages" sheet, header row 9 (skiprows=8)
DAMODARAN_SHEET = "Industry Averages"
DAMODARAN_SKIPROWS = 8

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_BASE = REPO_ROOT / "apps/api/data/damodaran"


def _fetch_excel(url: str, timeout: float = 30.0) -> bytes:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.content


def _find_industry_col(df: pd.DataFrame) -> str | None:
    for c in df.columns:
        if 'industry' in str(c).lower() or 'sector' in str(c).lower():
            return c
    return df.columns[0] if len(df.columns) > 0 else None


def _find_value_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in df.columns:
        c_up = str(c).upper()
        for cand in candidates:
            if cand.upper() in c_up:
                return c
    return None


def _parse_sheet(content: bytes, value_candidates: list[str]) -> dict:
    """Damodaran Excel 'Industry Averages' sheet -> {industry: float}."""
    df = pd.read_excel(
        BytesIO(content),
        sheet_name=DAMODARAN_SHEET,
        skiprows=DAMODARAN_SKIPROWS,
        header=0,
    )

    industry_col = _find_industry_col(df)
    value_col = _find_value_col(df, value_candidates)

    if not industry_col or not value_col:
        logger.warning(f"Industry/value col not found. Cols: {list(df.columns)[:10]}")
        return {}

    result: dict[str, float] = {}
    for _, row in df.iterrows():
        ind = row[industry_col]
        val = row[value_col]
        if pd.isna(ind) or pd.isna(val):
            continue
        ind_s = str(ind).strip()
        if not ind_s or ind_s.lower() == 'nan' or ind_s.lower() == 'total market':
            continue
        try:
            result[ind_s] = float(val)
        except (ValueError, TypeError):
            continue
    return result


def fetch_sector_multiples() -> dict:
    """3 Damodaran sector multiple fetch + merge."""
    today_dir = OUTPUT_BASE / date.today().strftime("%Y_%m_%d")
    today_dir.mkdir(parents=True, exist_ok=True)

    sector_data: dict[str, dict] = {}

    for url, fname, key, candidates in [
        (DAMODARAN_VEBITDA_URL, "vebitda.xls", "ev_ebitda",
         ["EV/EBITDA", "EV/EBITDAR&D"]),
        (DAMODARAN_PE_URL, "pedata.xls", "pe",
         ["PE Ratio", "Current PE", "Trailing PE"]),
        (DAMODARAN_PBV_URL, "pbvData.xls", "pbv",
         ["PBV", "Price/Book", "Price / BV"]),
    ]:
        logger.info(f"Fetching {fname}...")
        try:
            content = _fetch_excel(url)
        except Exception as e:
            logger.error(f"{fname} fetch fail: {e}")
            continue

        (today_dir / fname).write_bytes(content)
        logger.info(f"Saved {fname} ({len(content):,} bytes)")

        parsed = _parse_sheet(content, candidates)
        logger.info(f"Parsed {len(parsed)} industries")

        for ind, val in parsed.items():
            if ind not in sector_data:
                sector_data[ind] = {}
            sector_data[ind][key] = val

    output_path = today_dir / "sector_multiples.json"
    output_path.write_text(
        json.dumps(sector_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(f"Wrote {len(sector_data)} sectors to {output_path}")
    return sector_data


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    print("=" * 60)
    print("Damodaran Sector Multiples Fetcher — Phase 3c Adim 1")
    print("=" * 60)

    try:
        data = fetch_sector_multiples()
    except Exception as e:
        logger.error(f"FATAL: {type(e).__name__}: {e}")
        return 1

    print()
    print(f"Total sectors: {len(data)}")
    if data:
        sample = list(data.items())[:5]
        for ind, vals in sample:
            print(f"  {ind}: {vals}")
        print()
        # Hedef Damodaran sektorler
        print("Hedef Damodaran sektorler (Phase 3c kritik):")
        for target in ['Diversified', 'Bank', 'R.E.I.T.', 'Investments & Asset Management']:
            matching = [k for k in data if target.lower() in k.lower()]
            print(f"  {target}: {matching[:3] if matching else 'NOT FOUND'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
