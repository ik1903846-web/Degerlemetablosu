"""
KAP-Only Orchestrator v4 (Faz 11 v4.0 — Session 4A iskelet).

KAP-first data assembly + yfinance fiyat:
  ✓ KAP financials (multi-dialect, Session 3A+3B)
  ✓ KAP free float + shares (Session 3D, kpy41_acc5)
  ✓ KAP subsidiaries (Session 3E, kpy41_acc7) — holding SOTP için
  ✓ KAP corporate events (Session 3F, ünvan değişikliği)
  ✓ yfinance current price + 5y history (Session 3.5, BIST lisanslı)
  ✓ Türkiye-pure bottom-up sektör beta (Session 3.7)

Damodaran kuralları:
  ✓ Banking dialect → unlever skip (regression β proxy)
  ✓ Holding → SOTP candidate (Session 5+)
  ✓ Insurance → parking (3rd dialect)
  ✓ Sektör override (sector_overrides.json) Damodaran granular

Production discipline:
  ✗ İş Yatırım sıfır (data layer'da)
  ✗ AI/LLM API kullanımı yok
  ✓ Mevcut orchestrator.py DOKUNULMAZ (Session 6 cutover)

Session 4A scope: data assembly framework.
Session 4B scope: DCF engine entegrasyon.
Session 4C scope: Tarayıcı v4 cutover.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

# Local data layer
sys.path.insert(0, str(Path(__file__).resolve().parent / "data_layer"))

from kap_corporate_events import (
    load_snapshot as load_ce_snapshot,
    resolve_ticker as ce_resolve,
)
from kap_float_fetcher import (
    fetch_float_snapshot,
    lookup_ticker as float_lookup,
    FloatData,
)
from kap_subsidiaries_fetcher import (
    fetch_subsidiaries_snapshot,
    lookup_parent as subs_lookup_parent,
)
from yfinance_price_fetcher import fetch_one as yf_fetch_one


REPO_API = Path(__file__).resolve().parent
CACHE_DIR = REPO_API / "_cache"
OUTPUTS_DIR = REPO_API / "outputs"

FUNDAMENTALS_CACHE = CACHE_DIR / "fundamentals.json"
SECTOR_BETA_OUTPUT = OUTPUTS_DIR / "turkey_sector_beta.json"
TICKER_SECTORS_CACHE = CACHE_DIR / "ticker_sectors.json"
SUBS_CACHE_DIR = CACHE_DIR / "kap_subsidiaries"


# ============================================================================
# Aggregated ticker data
# ============================================================================

@dataclass
class TickerDataV4:
    ticker: str
    requested_ticker: str  # corporate event redirect öncesi orijinal

    # Corporate event status
    name_change: Optional[Dict] = None  # {old_ticker, new_ticker, change_date, ...}
    delisted: bool = False

    # KAP financials (Bilanço cache'den, fundamentals.json)
    dialect: Optional[str] = None
    de_ratio: Optional[float] = None
    total_debt: Optional[float] = None
    total_equity: Optional[float] = None
    disclosure_index: Optional[int] = None

    # KAP float + shares (kpy41_acc5)
    company_title: Optional[str] = None
    shares_outstanding: Optional[float] = None
    odenmis_sermaye_tl: Optional[float] = None
    float_pct: Optional[float] = None
    float_amount_tl: Optional[float] = None

    # KAP subsidiaries (sadece holding)
    subsidiaries_count: int = 0
    listed_subsidiaries_count: int = 0

    # yfinance fiyat
    current_price_tl: Optional[float] = None
    market_cap_tl: Optional[float] = None
    fifty_day_avg: Optional[float] = None
    two_hundred_day_avg: Optional[float] = None
    year_change_pct: Optional[float] = None
    history_rows: int = 0

    # Türkiye sektör beta (Session 3.7)
    sector_oid: Optional[str] = None
    sector_name: Optional[str] = None
    beta_levered: Optional[float] = None
    beta_unlevered: Optional[float] = None
    beta_relevered: Optional[float] = None
    sector_unlevered_mean: Optional[float] = None
    r_squared: Optional[float] = None

    # Damodaran flags
    flags: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """DCF için minimum gereksinim kontrolü."""
        return bool(
            self.current_price_tl
            and self.shares_outstanding
            and self.beta_relevered is not None
        )


# ============================================================================
# Cache loaders (singleton-ish, idempotent)
# ============================================================================

class _Caches:
    """Lazy load + memoize across multiple ticker assemblies."""
    def __init__(self):
        self._fundamentals: Optional[Dict] = None
        self._float_snap = None
        self._subs_snap = None
        self._ce_snap = None
        self._sector_beta: Optional[Dict] = None
        self._ticker_sectors: Optional[Dict] = None

    @property
    def fundamentals(self) -> Dict:
        if self._fundamentals is None:
            if FUNDAMENTALS_CACHE.exists():
                self._fundamentals = json.loads(
                    FUNDAMENTALS_CACHE.read_text(encoding="utf-8")
                )
            else:
                self._fundamentals = {}
        return self._fundamentals

    @property
    def float_snap(self):
        if self._float_snap is None:
            self._float_snap = fetch_float_snapshot(cache=True)
        return self._float_snap

    @property
    def subs_snap(self):
        if self._subs_snap is None:
            self._subs_snap = fetch_subsidiaries_snapshot(cache=True)
        return self._subs_snap

    @property
    def ce_snap(self):
        if self._ce_snap is None:
            self._ce_snap = load_ce_snapshot()
        return self._ce_snap

    @property
    def sector_beta(self) -> Dict:
        if self._sector_beta is None:
            if SECTOR_BETA_OUTPUT.exists():
                data = json.loads(SECTOR_BETA_OUTPUT.read_text(encoding="utf-8"))
                # ticker → entry mapping
                self._sector_beta = {
                    t["ticker"]: t for t in data.get("tickers", [])
                }
            else:
                self._sector_beta = {}
        return self._sector_beta

    @property
    def ticker_sectors(self) -> Dict:
        if self._ticker_sectors is None:
            if TICKER_SECTORS_CACHE.exists():
                data = json.loads(TICKER_SECTORS_CACHE.read_text(encoding="utf-8"))
                self._ticker_sectors = {
                    r["ticker"]: r for r in data.get("records", [])
                }
            else:
                self._ticker_sectors = {}
        return self._ticker_sectors


# ============================================================================
# Single-ticker assembly
# ============================================================================

def assemble_ticker_data(
    ticker: str,
    caches: Optional[_Caches] = None,
    fetch_yfinance_live: bool = True,
) -> TickerDataV4:
    """Tek ticker için tüm KAP+yfinance veri aggregate.

    fetch_yfinance_live=False → cache CSV'den oku (anlık fiyat eski olabilir).
    """
    caches = caches or _Caches()
    requested = ticker.upper().strip()
    td = TickerDataV4(ticker=requested, requested_ticker=requested)

    # 1) Corporate events (name change resolve)
    if caches.ce_snap is not None:
        res = ce_resolve(caches.ce_snap, requested)
        if res:
            td.name_change = res
            td.ticker = res["new_ticker"]
            td.flags.append(
                f"name_change: {requested} → {res['new_ticker']} ({res['change_date']})"
            )

    eff_ticker = td.ticker

    # 2) KAP financials (fundamentals.json cache'den)
    fund = caches.fundamentals.get(eff_ticker, {})
    if "error" in fund:
        td.errors.append(f"fundamentals: {fund['error']}")
    else:
        td.dialect = fund.get("dialect")
        td.de_ratio = fund.get("de_ratio")
        td.total_debt = fund.get("total_debt")
        td.total_equity = fund.get("equity")
        td.disclosure_index = fund.get("disclosure_index")

    # 3) KAP float + shares
    fr: Optional[FloatData] = float_lookup(caches.float_snap, eff_ticker)
    if fr is not None:
        td.company_title = fr.sirket_adi
        td.shares_outstanding = fr.shares_outstanding
        td.odenmis_sermaye_tl = fr.odenmis_sermaye_tl
        td.float_pct = fr.float_pct
        td.float_amount_tl = fr.float_amount_tl
    else:
        td.errors.append("float: ticker not in kpy41_acc5")

    # 4) Subsidiaries (sadece holding)
    subs = subs_lookup_parent(caches.subs_snap, eff_ticker)
    td.subsidiaries_count = len(subs)
    td.listed_subsidiaries_count = sum(1 for s in subs if s.subsidiary_ticker)

    # 5) yfinance fiyat
    if fetch_yfinance_live:
        try:
            price = yf_fetch_one(eff_ticker, cache=True, force_refresh=False)
            td.current_price_tl = price.current_price
            td.market_cap_tl = price.market_cap
            td.fifty_day_avg = price.fifty_day_avg
            td.two_hundred_day_avg = price.two_hundred_day_avg
            if price.year_change is not None:
                td.year_change_pct = price.year_change * 100
            td.history_rows = price.history_rows
            if price.error and price.error != "cached_recent":
                td.errors.append(f"yfinance: {price.error}")
        except Exception as e:
            td.errors.append(f"yfinance exc: {type(e).__name__}: {e}")

    # 6) Sektör beta (Session 3.7)
    sb = caches.sector_beta.get(eff_ticker)
    if sb:
        td.sector_oid = sb.get("sector_oid")
        td.sector_name = sb.get("sector_name")
        td.beta_levered = sb.get("beta_levered")
        td.beta_unlevered = sb.get("beta_unlevered")
        td.beta_relevered = sb.get("beta_relevered")
        td.sector_unlevered_mean = sb.get("sector_beta_unlevered")
        td.r_squared = sb.get("r_squared")
        for fl in sb.get("flags", []):
            td.flags.append(f"beta: {fl}")
    else:
        td.errors.append("sector_beta: ticker not in turkey_sector_beta.json")

    return td


# ============================================================================
# Universe pipeline (skeleton — DCF entegrasyon Session 4B'de)
# ============================================================================

def run_pipeline_v4_data_only(
    universe: Optional[List[str]] = None,
    progress: bool = True,
) -> List[TickerDataV4]:
    """Universe data assembly (DCF YOK — Session 4A iskelet).

    universe=None → SPK 605 ticker (kpy41_acc5).
    """
    caches = _Caches()
    if universe is None:
        universe = [r.ticker for r in caches.float_snap.records]

    results: List[TickerDataV4] = []
    for i, t in enumerate(universe, 1):
        td = assemble_ticker_data(t, caches=caches, fetch_yfinance_live=True)
        results.append(td)
        if progress and i % 50 == 0:
            n_complete = sum(1 for r in results if r.is_complete)
            print(f"  [{i:3d}/{len(universe)}] complete={n_complete}/{i}")
    return results


# ============================================================================
# CLI / 5-ticker spot validation
# ============================================================================

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 78)
    print("Orchestrator v4 — Session 4A Validation (5-ticker spot)")
    print("=" * 78)

    targets = [
        ("TUPRS", "anchor — 187.10 hedef Session 4D'de"),
        ("GARAN", "banking dialect (D/E unlever skip)"),
        ("KCHOL", "holding + subsidiaries lookup"),
        ("ARCLK", "sanayi (sector override → Beyaz Eşya)"),
        ("AGROT", "yeni IPO"),
    ]

    caches = _Caches()
    print("\n→ Pre-loading caches…")
    _ = caches.fundamentals
    _ = caches.float_snap
    _ = caches.ce_snap
    _ = caches.sector_beta
    print(f"  ✓ fundamentals: {len(caches.fundamentals)} ticker")
    print(f"  ✓ float:        {caches.float_snap.record_count} ticker")
    print(f"  ✓ corporate:    {caches.ce_snap.record_count if caches.ce_snap else 0} events")
    print(f"  ✓ sector_beta:  {len(caches.sector_beta)} ticker")
    # Subs snap lazy — only if holding test
    print(f"  → Loading subsidiaries…")
    _ = caches.subs_snap
    print(f"  ✓ subsidiaries: {caches.subs_snap.record_count} records")

    for ticker, note in targets:
        print(f"\n{'─'*78}")
        print(f"{ticker}  ({note})")
        print('─'*78)

        td = assemble_ticker_data(ticker, caches=caches, fetch_yfinance_live=True)

        print(f"  Effective ticker:    {td.ticker}")
        if td.name_change:
            print(f"  ★ Name change:       {td.requested_ticker} → {td.ticker}")
        print(f"  Company:             {td.company_title}")
        print(f"  Dialect:             {td.dialect}")
        print(f"  Shares outstanding:  {td.shares_outstanding:>16,.0f}" if td.shares_outstanding else "  Shares: ?")
        print(f"  Float %:             {td.float_pct*100:>7.2f}%" if td.float_pct else "  Float %: ?")
        print(f"  Current price:       {td.current_price_tl:>10.2f} TL" if td.current_price_tl else "  Current price: ?")
        print(f"  Market cap:          {td.market_cap_tl:>16,.0f} TL" if td.market_cap_tl else "  Market cap: ?")
        print(f"  D/E:                 {td.de_ratio:>10.4f}" if td.de_ratio is not None else "  D/E: ?")
        print(f"  Total Debt:          {td.total_debt:>16,.0f}" if td.total_debt is not None else "  Total Debt: ?")
        print(f"  Total Equity:        {td.total_equity:>16,.0f}" if td.total_equity is not None else "  Total Equity: ?")
        print(f"  Sektör:              {td.sector_name}")
        if td.beta_relevered is not None:
            print(f"  β_levered:           {td.beta_levered:.4f}" if td.beta_levered is not None else "")
            print(f"  β_unlevered:         {td.beta_unlevered:.4f}" if td.beta_unlevered is not None else "")
            print(f"  β_relevered:         {td.beta_relevered:.4f}")
            if td.r_squared is not None:
                print(f"  R²:                  {td.r_squared:.4f}")
        if td.subsidiaries_count > 0:
            print(f"  Subsidiaries:        total={td.subsidiaries_count} listed={td.listed_subsidiaries_count}")
        if td.flags:
            print(f"  Flags:")
            for f in td.flags:
                print(f"    - {f}")
        if td.errors:
            print(f"  Errors:")
            for e in td.errors:
                print(f"    ⚠ {e}")
        verdict = "✓ COMPLETE" if td.is_complete else "⚠ INCOMPLETE"
        print(f"  → DCF input ready: {verdict}")
