#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relationship Categorizer - Faz B2 Phase 2 Adim 1
==================================================

KAP subsidiary CSV'sindeki NaN relationship_type'lari
relationship_raw'dan kurtarmak icin keyword-priority parser.

Damodaran kategorileri:
    full      : >50% kontrol, konsolide bilanco
    joint     : musterek yonetim (joint venture)
    equity    : 20-50% istirak (equity method)
    financial : <20% finansal yatirim

Idempotent: NaN olmayan record'lara dokunmaz.

Usage:
    python -m apps.api.data_layer.relationship_categorizer

    veya:

    from apps.api.data_layer.relationship_categorizer import (
        categorize_csv, categorize_relationship
    )
"""

from __future__ import annotations

import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


_TR_TRANSLATE = str.maketrans(
    "ÇĞIİÖŞÜçğıiöşü",
    "CGIIOSUcgiiosu"
)


def _normalize_tr(s: str) -> str:
    """Turkce karakter + lowercase + whitespace normalize."""
    if not s:
        return ""
    return s.translate(_TR_TRANSLATE).lower().strip()


# Priority-ordered rules (yukaridan asagi tarama)
# Damodaran kategorileri, Turkce KAP terminoloji
CATEGORIZATION_RULES = [
    # ===== financial (oncelik: composite "bagli menkul" full'dan once) =====
    (r"bagli.{0,5}menkul",       "financial"),

    # ===== full (>50% kontrol, konsolide) =====
    (r"tam.{0,5}konsol",         "full"),
    (r"konsol.{0,15}tabi",       "full"),
    (r"mali.{0,5}bagli",         "full"),
    (r"dogrudan.{0,15}bagli",    "full"),
    (r"dolayli.{0,15}bagli",     "full"),
    (r"bagli.{0,5}ortak",        "full"),

    # ===== joint (musterek yonetim) =====
    (r"musterek.{0,15}yonet",    "joint"),
    (r"musterek.{0,15}faaliy",   "joint"),
    (r"musterek.{0,15}tesebbus", "joint"),
    (r"is.{0,5}ortak",           "joint"),
    (r"joint.{0,5}venture",      "joint"),

    # ===== equity (istirak, equity method) =====
    (r"ozkaynak.{0,15}yontem",   "equity"),
    (r"sermayesine.{0,15}istirak", "equity"),
    (r"istirak",                 "equity"),
    (r"girisim.{0,5}sirket",     "equity"),

    # ===== financial (FVTPL/FVTOCI) =====
    (r"finansal.{0,15}yatir",    "financial"),
    (r"finansal.{0,15}varlik",   "financial"),
    (r"finansal.{0,15}duran",    "financial"),
    (r"menkul.{0,5}kiymet",      "financial"),
    (r"satilm.{0,15}hazir",      "financial"),
    (r"hisse.{0,15}donust",      "financial"),
]


# Composite override: "Girisim Sirketi (Finansal Yatirim)" -> financial
COMPOSITE_OVERRIDE = [
    ((r"girisim", r"finansal"), "financial"),
]


def categorize_relationship(raw_text: Optional[str]) -> Optional[str]:
    """relationship_raw'dan Damodaran kategorisi cikar.

    Returns "full" | "equity" | "joint" | "financial" | None.
    """
    if raw_text is None:
        return None

    text = str(raw_text).strip()
    if not text or text == "-":
        return None

    normalized = _normalize_tr(text)

    for keywords, override_cat in COMPOSITE_OVERRIDE:
        if all(re.search(kw, normalized) for kw in keywords):
            return override_cat

    for pattern, category in CATEGORIZATION_RULES:
        if re.search(pattern, normalized):
            return category

    return None


def categorize_csv(
    csv_path,
    output_path=None,
    dry_run: bool = False,
) -> dict:
    """CSV'deki NaN relationship_type'lari kategorize et."""
    import pandas as pd

    csv_path = Path(csv_path)
    output_path = Path(output_path) if output_path else csv_path

    df = pd.read_csv(csv_path)
    total = len(df)

    before_null = df['relationship_type'].isna().sum()
    before_breakdown = df['relationship_type'].value_counts(dropna=False).to_dict()

    null_mask = df['relationship_type'].isna()

    recovered = 0
    by_category = {"full": 0, "equity": 0, "joint": 0, "financial": 0}

    for idx in df[null_mask].index:
        raw = df.at[idx, 'relationship_raw']
        if pd.isna(raw):
            continue

        category = categorize_relationship(raw)
        if category:
            df.at[idx, 'relationship_type'] = category
            recovered += 1
            by_category[category] += 1

    after_null = df['relationship_type'].isna().sum()
    after_breakdown = df['relationship_type'].value_counts(dropna=False).to_dict()

    stats = {
        "total_records": total,
        "before_null": int(before_null),
        "after_null": int(after_null),
        "recovered": recovered,
        "recovery_rate_pct": round(recovered / before_null * 100, 1) if before_null else 0.0,
        "recovered_breakdown": by_category,
        "before_breakdown": {str(k): int(v) for k, v in before_breakdown.items()},
        "after_breakdown": {str(k): int(v) for k, v in after_breakdown.items()},
    }

    if not dry_run:
        df.to_csv(output_path, index=False)
        logger.info(f"CSV updated: {output_path}")

    return stats


def _smoke_test() -> int:
    """Standalone smoke test."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    print("=" * 70)
    print("Relationship Categorizer - Smoke Test")
    print("=" * 70)

    test_cases = [
        ("BAGLI ORTAKLIK (PAY %51,23)", "full"),
        ("TAM KONSOLIDASYON", "full"),
        ("Dogrudan Bagli Ortaklik", "full"),
        ("Bagli Ortakligi", "full"),
        ("MUSTEREK YONETIME TABI ORT. (PAY %50)", "joint"),
        ("Musterek Faaliyet", "joint"),
        ("Dolayli Istirak", "equity"),
        ("Ozkaynak Yontemiyle Degerlenen Yatirimlar", "equity"),
        ("Girisim Sirketi", "equity"),
        ("Girisim Sirketi (Finansal Yatirim)", "financial"),
        ("Bagli Menkul Kiymet", "financial"),
        ("Satilmaya Hazir Finansal Varlik", "financial"),
        ("Finansal Duran Varlik", "financial"),
        ("-", None),
        ("", None),
    ]

    print()
    print("Categorization tests:")
    print(f'{"Input":50} | {"Expected":10} | {"Got":10} | OK?')
    print("-" * 90)

    pass_count = 0
    for raw, expected in test_cases:
        got = categorize_relationship(raw)
        ok = "OK" if got == expected else "FAIL"
        if got == expected:
            pass_count += 1
        raw_short = raw[:48] if len(raw) > 48 else raw
        print(f'{raw_short:50} | {str(expected):10} | {str(got):10} | {ok}')

    print()
    print(f"Pass: {pass_count}/{len(test_cases)}")

    return 0 if pass_count == len(test_cases) else 1


if __name__ == "__main__":
    import sys
    sys.exit(_smoke_test())
