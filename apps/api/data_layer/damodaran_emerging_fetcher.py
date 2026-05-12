#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Damodaran Emerging Markets Fetcher — Phase 5a (Adim 6 BLOCK prerequisite)
=========================================================================

Damodaran EM datasets fetch + JSON cache:
  capexemerg.xls    -> capex_emerg.json     (capex, depreciation, sales_to_capital)
  marginemerg.xls   -> margin_emerg.json    (pre-tax op margin, gross, net)
  roeemerg.xls      -> roe_emerg.json       (ROE adjusted/unadjusted)
  peemerg.xls       -> pe_emerg.json        (current PE, trailing PE, PEG)
  pbvemerg.xls      -> pbv_emerg.json       (PBV, ROIC, EV/InvCap)
  vebitdaemerg.xls  -> vebitda_emerg.json   (EV/EBITDA, EV/EBIT)
  countrystats.xls  -> countrystats.json    (Turkey row + 126 country median multiples)

Output: apps/api/data/damodaran/YYYY_MM_DD/emerging_markets/

Phase 3c sector_multiple_fetcher.py pattern reuse + extend.
TR-BIST industrial ticker'lar icin Damodaran emerg benchmark
Phase 5b Adim 6 UNBLOCK prerequisite.

Stand-alone, mevcut fetcher'lar DOKUNULMAZ.

Usage:
    python apps/api/data_layer/damodaran_emerging_fetcher.py
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

DAMODARAN_BASE = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/"

# Industry-based datasets: (filename, output_key, skiprows, value_columns_to_extract)
EM_INDUSTRY_DATASETS = [
    ("capexemerg.xls", "capex_emerg.json", 7,
     ["Capital Expenditures (US $ millions)", "Depreciation & Amort ((US $ millions)",
      "Cap Ex/Deprecn", "Net Cap Ex/Sales"]),
    ("marginemerg.xls", "margin_emerg.json", 8,
     ["Gross Margin", "Net Margin", "Pre-tax Unadjusted Operating Margin",
      "After-tax Unadjusted Operating Margin", "EBITDA/Sales"]),
    ("roeemerg.xls", "roe_emerg.json", 7,
     ["ROE (unadjusted)", "ROE (adjusted for R&D)"]),
    ("peemerg.xls", "pe_emerg.json", 7,
     ["Current PE", "Trailing PE", "Forward PE",
      "% of Money Losing firms (Trailing)"]),
    ("pbvemerg.xls", "pbv_emerg.json", 7,
     ["PBV", "ROE", "EV/ Invested Capital", "ROIC"]),
    ("vebitdaemerg.xls", "vebitda_emerg.json", 8,
     ["EV/EBITDA", "EV/EBIT", "EV/EBIT (1-t)"]),
]

# Country dataset (different schema: 'Country' col, median multiples)
EM_COUNTRY_DATASET = (
    "countrystats.xls", "countrystats.json", 8,
    ["count", "median(Current PE)", "median(Trailing PE)", "median(Forward PE)",
     "median(PEG)", "median(PBV)"],
)

DAMODARAN_INDUSTRY_SHEET = "Industry Averages"
DAMODARAN_COUNTRY_SHEET = "Sheet1"

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_BASE = REPO_ROOT / "apps/api/data/damodaran"


def _fetch_excel(url: str, timeout: float = 30.0) -> bytes:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.content


def _parse_industry_sheet(content: bytes, skiprows: int, value_cols: list[str]) -> dict:
    """Parse 'Industry Averages' sheet -> dict[industry] = {col: val}."""
    df = pd.read_excel(
        BytesIO(content),
        sheet_name=DAMODARAN_INDUSTRY_SHEET,
        skiprows=skiprows,
        header=0,
    )
    industry_col = next((c for c in df.columns if 'industry' in str(c).lower() or 'sector' in str(c).lower()), None)
    if not industry_col:
        industry_col = df.columns[0]

    matched_cols: dict[str, str] = {}
    for want in value_cols:
        for actual in df.columns:
            if str(actual).strip() == want.strip():
                matched_cols[want] = actual
                break

    result: dict[str, dict[str, float]] = {}
    for _, row in df.iterrows():
        ind = row[industry_col]
        if pd.isna(ind):
            continue
        ind_s = str(ind).strip()
        if not ind_s or ind_s.lower() in ('nan', 'total market'):
            continue
        record: dict[str, float] = {}
        for want, actual in matched_cols.items():
            val = row[actual]
            if pd.isna(val):
                continue
            try:
                record[want] = float(val)
            except (ValueError, TypeError):
                continue
        if record:
            result[ind_s] = record
    return result, list(matched_cols.keys())


def _parse_country_sheet(content: bytes, skiprows: int, value_cols: list[str]) -> dict:
    """Parse countrystats.xls 'Sheet1' -> dict[country] = {col: val}."""
    df = pd.read_excel(
        BytesIO(content),
        sheet_name=DAMODARAN_COUNTRY_SHEET,
        skiprows=skiprows,
        header=0,
    )
    country_col = next((c for c in df.columns if 'country' in str(c).lower()), df.columns[0])

    matched_cols: dict[str, str] = {}
    for want in value_cols:
        for actual in df.columns:
            if str(actual).strip() == want.strip():
                matched_cols[want] = actual
                break

    result: dict[str, dict[str, float]] = {}
    for _, row in df.iterrows():
        country = row[country_col]
        if pd.isna(country):
            continue
        c_s = str(country).strip()
        if not c_s or c_s.lower() == 'nan':
            continue
        record: dict[str, float] = {}
        for want, actual in matched_cols.items():
            val = row[actual]
            if pd.isna(val):
                continue
            try:
                record[want] = float(val)
            except (ValueError, TypeError):
                continue
        if record:
            result[c_s] = record
    return result, list(matched_cols.keys())


def fetch_emerging_markets() -> dict:
    """Phase 5a: 7 Damodaran EM dataset fetch + cache."""
    today_dir = OUTPUT_BASE / date.today().strftime("%Y_%m_%d") / "emerging_markets"
    today_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, dict] = {}

    # 6 industry datasets
    for fname, out_name, skiprows, value_cols in EM_INDUSTRY_DATASETS:
        url = DAMODARAN_BASE + fname
        logger.info(f"Fetching {fname}...")
        try:
            content = _fetch_excel(url)
        except Exception as e:
            logger.error(f"{fname} fetch fail: {e}")
            summary[out_name] = {"error": str(e), "sectors": 0}
            continue

        (today_dir / fname).write_bytes(content)
        parsed, matched = _parse_industry_sheet(content, skiprows, value_cols)
        out_path = today_dir / out_name
        out_path.write_text(
            json.dumps(parsed, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        summary[out_name] = {
            "sectors": len(parsed),
            "matched_columns": matched,
            "file_size_bytes": len(content),
        }
        logger.info(f"  {out_name}: {len(parsed)} sectors, {len(matched)} columns")

    # countrystats
    fname, out_name, skiprows, value_cols = EM_COUNTRY_DATASET
    url = DAMODARAN_BASE + fname
    logger.info(f"Fetching {fname}...")
    try:
        content = _fetch_excel(url)
        (today_dir / fname).write_bytes(content)
        parsed, matched = _parse_country_sheet(content, skiprows, value_cols)
        out_path = today_dir / out_name
        out_path.write_text(
            json.dumps(parsed, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        summary[out_name] = {
            "countries": len(parsed),
            "matched_columns": matched,
            "turkey_row": parsed.get("Turkey"),
        }
        logger.info(f"  {out_name}: {len(parsed)} countries (Turkey: {parsed.get('Turkey')})")
    except Exception as e:
        logger.error(f"{fname} fetch fail: {e}")
        summary[out_name] = {"error": str(e), "countries": 0}

    return summary


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )
    print("=" * 70)
    print("Damodaran Emerging Markets Fetcher — Phase 5a")
    print("=" * 70)
    try:
        summary = fetch_emerging_markets()
    except Exception as e:
        logger.error(f"FATAL: {type(e).__name__}: {e}")
        return 1

    print()
    print(f"7 dataset cache yazildi (apps/api/data/damodaran/{date.today():%Y_%m_%d}/emerging_markets/):")
    for name, info in summary.items():
        if "error" in info:
            print(f"  {name}: ERROR ({info['error']})")
        elif "sectors" in info:
            print(f"  {name}: {info['sectors']} sectors, {len(info['matched_columns'])} cols matched")
        else:
            print(f"  {name}: {info['countries']} countries")

    return 0


if __name__ == "__main__":
    sys.exit(main())
