#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-Holdings Valuator - Faz B2 Phase 1 Adım 3
==================================================

Damodaran cross-holdings value hesaplayıcı.

Formula:
    Cross-Holdings Value = SUM(market_cap × ownership_pct)

    where relationship_type IN ('equity', 'financial', 'joint')
    (relationship_type='full' SKIP — double-counting)

Damodaran categories:
    Majority (>50%):  Konsolide finansal raporda zaten -> SKIP
    Active (20-50%):  Equity method -> EKLE (mark-to-market)
    Passive (<20%):   FVTPL/FVTOCI -> EKLE (mark-to-market)

Usage:
    from apps.api.dcf_engine_v4.cross_holdings import (
        compute_cross_holdings_value
    )

    result = compute_cross_holdings_value('KCHOL')
    print(f'Total: {result.total_value_tl:,.0f} TL')
    print(f'Contributions: {len(result.contributions)}')
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SUBS_CSV = REPO_ROOT / "apps/api/_cache/kap_subsidiaries/kap_subs_2026-05-10.csv"
DEFAULT_MC_DIR = REPO_ROOT / "apps/api/_cache/market_caps"

# Phase 3b Adim 1.5: 'full' SKIP listesinden kaldirildi.
# Cons_ratio (orchestrator_v4) cash/debt asimetriyi cozuyor.
# Damodaran SOTP: listed full sub'lar piyasa degerinde dahil edilir.
SKIP_RELATIONSHIPS: set = set()
# Eligible cross-holdings (separately added to firm value)
ELIGIBLE_RELATIONSHIPS = {"equity", "financial", "joint", "full"}


@dataclass
class CrossHoldingContribution:
    sub_ticker: str
    sub_name: str
    ownership_pct: float       # decimal 0-1
    market_cap_tl: float
    contribution_tl: float     # market_cap × ownership
    relationship_type: str
    sector: Optional[str] = None


@dataclass
class CrossHoldingsResult:
    parent_ticker: str
    total_value_tl: float
    contributions: list[CrossHoldingContribution] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    full_consolidated_count: int = 0  # Skip edilen "full" sayisi
    null_relationship_count: int = 0  # Manuel review gereken
    computed_at: str = ""
    # Phase 3b: 3-tier valuation audit
    banking_proxy_subs: list[str] = field(default_factory=list)
    unknown_proxy_subs: list[str] = field(default_factory=list)
    private_subs: list[str] = field(default_factory=list)


def _load_market_caps(date_str: Optional[str] = None) -> dict:
    """En yeni market_caps cache'ini yukle."""
    if date_str:
        path = DEFAULT_MC_DIR / f"{date_str}.json"
    else:
        # En yeni dosyayi bul
        if not DEFAULT_MC_DIR.exists():
            raise FileNotFoundError(f"Cache dir yok: {DEFAULT_MC_DIR}")
        files = sorted(DEFAULT_MC_DIR.glob("*.json"))
        if not files:
            raise FileNotFoundError(f"Cache dosyasi yok: {DEFAULT_MC_DIR}")
        path = files[-1]

    if not path.exists():
        raise FileNotFoundError(f"Market caps cache yok: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def _load_subs_df():
    """Subsidiary cache'i yukle (pandas)."""
    import pandas as pd
    if not DEFAULT_SUBS_CSV.exists():
        raise FileNotFoundError(f"Subs CSV yok: {DEFAULT_SUBS_CSV}")
    return pd.read_csv(DEFAULT_SUBS_CSV)


def _load_dialect_map() -> dict:
    """Phase 3b: turkey_v4_batch.json'dan ticker -> dialect mapping."""
    batch_path = REPO_ROOT / "apps/api/outputs/turkey_v4_batch.json"
    if not batch_path.exists():
        return {}
    try:
        d = json.loads(batch_path.read_text(encoding="utf-8"))
        return {t['ticker']: t.get('dialect') for t in d.get('tickers', [])}
    except Exception:
        return {}


# Phase 3b: full consolidated SKIP exception (banking/insurance/unknown
# DCF yapilmadigi icin double-count YOK, dahil edilir)
NON_CONSOLIDATED_DIALECTS = {"banking", "insurance", "unknown", None}


def compute_cross_holdings_value(
    parent_ticker: str,
    subs_df=None,
    market_caps: Optional[dict] = None,
    dialect_map: Optional[dict] = None,
) -> CrossHoldingsResult:
    """Tek parent ticker icin cross-holdings hesapla."""
    parent_ticker = parent_ticker.upper().strip()
    now = datetime.now(timezone.utc).isoformat()

    if subs_df is None:
        subs_df = _load_subs_df()
    if market_caps is None:
        market_caps = _load_market_caps()
    if dialect_map is None:
        dialect_map = _load_dialect_map()

    # Parent'in tum sub'lari
    parent_subs = subs_df[subs_df['parent_ticker'].str.upper() == parent_ticker]

    # Listed olanlari filtrele
    listed = parent_subs[
        parent_subs['subsidiary_ticker'].notna() &
        (parent_subs['subsidiary_ticker'].astype(str).str.strip() != '')
    ]

    if len(listed) == 0:
        return CrossHoldingsResult(
            parent_ticker=parent_ticker,
            total_value_tl=0.0,
            full_consolidated_count=0,
            computed_at=now,
            errors=[f"No listed subsidiaries for {parent_ticker}"],
        )

    contributions = []
    skipped = []
    errors = []
    full_count = 0
    null_rel_count = 0
    # Phase 3b: 3-tier flags
    banking_proxy_subs: list[str] = []
    unknown_proxy_subs: list[str] = []
    private_subs: list[str] = []

    for _, row in listed.iterrows():
        sub_ticker = str(row['subsidiary_ticker']).upper().strip()
        rel_type = row.get('relationship_type')
        ownership = row.get('ownership_pct')

        # Null relationship_type -> manuel review
        if rel_type is None or (isinstance(rel_type, float) and rel_type != rel_type):
            null_rel_count += 1
            skipped.append(f"{sub_ticker}: null relationship_type (manuel review)")
            continue

        rel_type = str(rel_type).strip().lower()
        sub_dialect = dialect_map.get(sub_ticker)

        # Konsolide "full" -> DCF zaten konsolide bilancoda
        # EXCEPTION (Phase 3b): banking/insurance/unknown sub'lar konsolide DCF
        # yapmadiklari icin double-count YOK -> market_cap proxy ile dahil
        if rel_type in SKIP_RELATIONSHIPS:
            if sub_dialect not in NON_CONSOLIDATED_DIALECTS:
                full_count += 1
                continue
            # banking/insurance/unknown full -> dahil, asagidaki proxy logic

        # Eligible degil + dialect normal -> SKIP
        # (banking/insurance/unknown rel_type'i full degil de equity/joint vs ise zaten dahil)
        elif rel_type not in ELIGIBLE_RELATIONSHIPS:
            skipped.append(f"{sub_ticker}: unknown relationship_type='{rel_type}'")
            continue

        # Ownership pct kontrolü
        if ownership is None or (isinstance(ownership, float) and ownership != ownership):
            errors.append(f"{sub_ticker}: ownership_pct null")
            continue

        try:
            ownership = float(ownership)
        except (ValueError, TypeError):
            errors.append(f"{sub_ticker}: ownership_pct invalid '{ownership}'")
            continue

        # Outlier check (>1.0 yani >100%)
        if ownership > 1.0:
            errors.append(f"{sub_ticker}: ownership_pct {ownership} > 1.0 (outlier, manuel review)")
            continue

        # Market cap lookup
        mc_record = market_caps.get(sub_ticker)
        if not mc_record:
            errors.append(f"{sub_ticker}: not in market_caps cache")
            continue

        mc_tl = mc_record.get('market_cap_tl')
        if mc_tl is None:
            mc_err = mc_record.get('error', 'market_cap missing')
            skipped.append(f"{sub_ticker}: {mc_err}")
            continue

        # Contribution = market_cap × ownership
        contribution = float(mc_tl) * ownership

        # Phase 3b: proxy flag tracking
        if sub_dialect == "banking":
            banking_proxy_subs.append(sub_ticker)
        elif sub_dialect in ("unknown", None) or sub_dialect == "insurance":
            unknown_proxy_subs.append(sub_ticker)

        contributions.append(CrossHoldingContribution(
            sub_ticker=sub_ticker,
            sub_name=str(row.get('subsidiary_name', '')),
            ownership_pct=ownership,
            market_cap_tl=float(mc_tl),
            contribution_tl=contribution,
            relationship_type=rel_type,
            sector=str(row.get('sector', '')) if row.get('sector') else None,
        ))

    total = sum(c.contribution_tl for c in contributions)

    return CrossHoldingsResult(
        parent_ticker=parent_ticker,
        total_value_tl=total,
        contributions=contributions,
        skipped=skipped,
        errors=errors,
        full_consolidated_count=full_count,
        null_relationship_count=null_rel_count,
        computed_at=now,
        banking_proxy_subs=banking_proxy_subs,
        unknown_proxy_subs=unknown_proxy_subs,
        private_subs=private_subs,
    )


def compute_all_parents() -> dict[str, CrossHoldingsResult]:
    """Tum parent ticker'lar icin cross-holdings hesapla."""
    subs_df = _load_subs_df()
    market_caps = _load_market_caps()

    listed_subs = subs_df[
        subs_df['subsidiary_ticker'].notna() &
        (subs_df['subsidiary_ticker'].astype(str).str.strip() != '')
    ]
    parents = sorted(listed_subs['parent_ticker'].dropna().unique())

    results = {}
    for parent in parents:
        try:
            results[parent] = compute_cross_holdings_value(
                parent, subs_df=subs_df, market_caps=market_caps
            )
        except Exception as e:
            logger.error(f"{parent} fail: {e}")
            results[parent] = CrossHoldingsResult(
                parent_ticker=parent,
                total_value_tl=0.0,
                errors=[f"compute_fail: {e}"],
                computed_at=datetime.now(timezone.utc).isoformat(),
            )
    return results


def _smoke_test() -> int:
    """Smoke test: 5 holding parent."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s"
    )

    test_parents = ['KCHOL', 'SAHOL', 'AGHOL', 'ALARK', 'IHLAS']

    print("=" * 70)
    print("Cross-Holdings Valuator - Smoke Test")
    print("=" * 70)
    print()

    subs_df = _load_subs_df()
    market_caps = _load_market_caps()

    print(f"Subs records: {len(subs_df)}")
    print(f"Market caps cached: {len(market_caps)}")
    print()

    for parent in test_parents:
        result = compute_cross_holdings_value(parent, subs_df, market_caps)

        print(f"=== {parent} ===")
        print(f"  Total cross-holdings: {result.total_value_tl:>20,.0f} TL")
        print(f"  Contributions:        {len(result.contributions)}")
        print(f"  Full consolidated (SKIP): {result.full_consolidated_count}")
        print(f"  Null relationship:    {result.null_relationship_count}")
        print(f"  Skipped:              {len(result.skipped)}")
        print(f"  Errors:               {len(result.errors)}")

        if result.contributions:
            print(f"  Top contributions:")
            sorted_c = sorted(result.contributions, key=lambda x: -x.contribution_tl)
            for c in sorted_c[:5]:
                print(f"    {c.sub_ticker:8} ({c.relationship_type:10}) "
                      f"own={c.ownership_pct:.4f} "
                      f"mc={c.market_cap_tl:>15,.0f} "
                      f"contrib={c.contribution_tl:>15,.0f}")

        if result.errors:
            print(f"  Errors:")
            for e in result.errors[:3]:
                print(f"    - {e}")

        print()

    print("=" * 70)
    print("Smoke test tamamlandi")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_smoke_test())
