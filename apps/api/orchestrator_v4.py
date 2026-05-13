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
from kap_excel_fetcher import fetch_excel_export
from kap_excel_parser import parse_excel_html, FinancialLineItems

# DCF Engine v4
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dcf_engine_v4.lifecycle_classifier import classify_lifecycle, LifecycleResult
from dcf_engine_v4.cost_of_capital import calculate_wacc, WACCResult, TURKEY_TAX_RATE
from dcf_engine_v4.fcff_engine import calculate_fcff_dcf, DCFInputs, DCFResult
from dcf_engine_v4.cyclical_normalize import normalize_op_income
from dcf_engine_v4.cross_holdings import compute_cross_holdings_value


REPO_API = Path(__file__).resolve().parent
CACHE_DIR = REPO_API / "_cache"
OUTPUTS_DIR = REPO_API / "outputs"

FUNDAMENTALS_CACHE = CACHE_DIR / "fundamentals.json"
SECTOR_BETA_OUTPUT = OUTPUTS_DIR / "turkey_sector_beta.json"
TICKER_SECTORS_CACHE = CACHE_DIR / "ticker_sectors.json"
SUBS_CACHE_DIR = CACHE_DIR / "kap_subsidiaries"
PARSED_FIN_CACHE_DIR = CACHE_DIR / "parsed_financials"


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

    # DCF inputs (Excel re-parse'tan)
    revenue: Optional[float] = None
    op_income: Optional[float] = None
    capex: Optional[float] = None
    depreciation: Optional[float] = None
    working_capital: Optional[float] = None
    cash: Optional[float] = None
    tax_expense: Optional[float] = None
    # Phase 3a: holding sub valuation icin (konsolide bilanco DISI)
    equity_method_investments: Optional[float] = None
    investment_properties: Optional[float] = None
    # Phase 4a Adim 1: sales_to_capital ratio icin
    total_assets: Optional[float] = None
    # Phase 4a Adim 5: Damodaran formal equity bridge + Adim 2 entegrasyon
    minority_interests: Optional[float] = None
    financial_investments: Optional[float] = None
    revenue_onceki: Optional[float] = None

    # DCF outputs
    lifecycle_stage: Optional[str] = None
    lifecycle_rationale: Optional[str] = None
    wacc: Optional[float] = None
    cost_of_equity: Optional[float] = None
    cost_of_debt: Optional[float] = None
    rating: Optional[str] = None
    intrinsic_per_share_tl: Optional[float] = None
    upside_pct: Optional[float] = None
    dcf_method: Optional[str] = None  # "industrial_fcff" / "banking_skip" / vb.

    # Damodaran flags
    flags: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Faz B2 Phase 1 Adim 4 tamamlama: cross-holdings audit echo
    cross_holdings_value_tl: Optional[float] = None
    cross_holdings_added_tl: Optional[float] = None

    # Phase 5c: Terminal value sanity (Damodaran ImpliedROCROE.xls)
    implied_roc: Optional[float] = None
    terminal_value_sustainable: Optional[bool] = None

    # Phase 4d: Multi-multiple PE/PBV consensus (Damodaran cross-check)
    pe_implied: Optional[float] = None
    pbv_implied: Optional[float] = None
    consensus_intrinsic: Optional[float] = None
    consensus_dispersion: Optional[float] = None

    # Phase 7.1: Margin of Safety (Damodaran/Buffett/Graham 4-level signal)
    mos_intrinsic: Optional[float] = None
    mos_consensus: Optional[float] = None
    mos_min: Optional[float] = None
    composite_signal: Optional[str] = None  # BUY / WAIT / NO_MARGIN / OVERVALUED

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
    else:
        # File-only mode: CSV cache son satır close = current_price proxy
        try:
            from yfinance_price_fetcher import CACHE_DIR as YF_CACHE_DIR
            csv_path = YF_CACHE_DIR / f"{eff_ticker}.csv"
            if csv_path.exists():
                import pandas as pd
                df = pd.read_csv(csv_path, parse_dates=["date"])
                if not df.empty:
                    last_close = float(df["close"].iloc[-1])
                    td.current_price_tl = last_close
                    td.history_rows = len(df)
                    if td.shares_outstanding:
                        td.market_cap_tl = last_close * td.shares_outstanding
        except Exception as e:
            td.errors.append(f"yf_csv: {type(e).__name__}: {e}")

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
# DCF integration (Session 4B)
# ============================================================================

def enrich_full_financials(td: TickerDataV4, force_refresh: bool = False) -> TickerDataV4:
    """KAP Excel cache → disk-cached parsed financials.

    parsed_financials/{ticker}.json disk cache.
    İlk run yavaş (Excel parse 1-4 sec), sonraki run instant.
    """
    if td.disclosure_index is None:
        td.errors.append("enrich: no disclosure_index for full re-parse")
        return td

    cache_path = PARSED_FIN_CACHE_DIR / f"{td.ticker}.json"
    parsed = None
    if not force_refresh and cache_path.exists():
        try:
            parsed = json.loads(cache_path.read_text(encoding="utf-8"))
            if parsed.get("disclosure_index") != td.disclosure_index:
                # Stale (yeni FR var) → refresh
                parsed = None
        except Exception:
            parsed = None

    if parsed is None:
        try:
            dl = fetch_excel_export(td.disclosure_index)
            if not dl.success:
                td.errors.append(f"enrich: download fail {dl.error}")
                return td
            fli: FinancialLineItems = parse_excel_html(
                dl.content_bytes, disclosure_index=td.disclosure_index,
            )
            if fli.error:
                td.errors.append(f"enrich: parse {fli.error}")
                return td
            # Sunum birimi normalize
            unit_multiplier = 1.0
            if fli.sunum_birimi:
                txt = fli.sunum_birimi.lower().replace(" ", "")
                if "1.000.000" in txt or "1000000" in txt:
                    unit_multiplier = 1_000_000.0
                elif "1.000" in txt or "1000" in txt:
                    unit_multiplier = 1_000.0

            parsed = {
                "ticker": td.ticker,
                "disclosure_index": td.disclosure_index,
                "unit_multiplier": unit_multiplier,
                "revenue":         (fli.revenue_cari or 0) * unit_multiplier or None,
                "op_income":       (fli.operating_income_cari or 0) * unit_multiplier or None,
                "capex":           (fli.capex_cari or 0) * unit_multiplier or None,
                "depreciation":    (fli.depreciation_cari or 0) * unit_multiplier or None,
                "working_capital": (fli.working_capital or 0) * unit_multiplier or None,
                "cash":            (fli.cash or 0) * unit_multiplier or None,
                "tax_expense":     (fli.tax_expense_cari or 0) * unit_multiplier or None,
                "total_debt":      (fli.total_debt or 0) * unit_multiplier or None,
                "total_equity":    (fli.total_equity or 0) * unit_multiplier or None,
                # Phase 3a: holding sub valuation icin
                "equity_method_investments": (fli.equity_method_investments or 0) * unit_multiplier or None,
                "investment_properties":     (fli.investment_properties or 0) * unit_multiplier or None,
                # Phase 4a Adim 1: sales_to_capital ratio icin
                "total_assets":    (fli.total_assets or 0) * unit_multiplier or None,
                # Phase 4a Adim 5: Damodaran formal equity bridge + Adim 2 entegrasyon
                "minority_interests":    (fli.minority_interests or 0) * unit_multiplier or None,
                "financial_investments": (fli.financial_investments or 0) * unit_multiplier or None,
                "revenue_onceki":        (fli.revenue_onceki or 0) * unit_multiplier or None,
            }
            # Atomic cache write
            PARSED_FIN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            tmp = cache_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(cache_path)
        except Exception as e:
            td.errors.append(f"enrich exc: {type(e).__name__}: {e}")
            return td

    # Apply parsed → ticker data
    td.revenue = parsed.get("revenue")
    td.op_income = parsed.get("op_income")
    td.capex = parsed.get("capex")
    td.depreciation = parsed.get("depreciation")
    td.working_capital = parsed.get("working_capital")
    td.cash = parsed.get("cash")
    td.tax_expense = parsed.get("tax_expense")
    if parsed.get("total_debt") is not None:
        td.total_debt = parsed["total_debt"]
    if parsed.get("total_equity") is not None:
        td.total_equity = parsed["total_equity"]
    # Phase 3a: holding sub valuation icin
    td.equity_method_investments = parsed.get("equity_method_investments")
    td.investment_properties = parsed.get("investment_properties")
    # Phase 4a Adim 1: sales_to_capital ratio icin
    td.total_assets = parsed.get("total_assets")
    # Phase 4a Adim 5: Damodaran formal equity bridge + Adim 2 entegrasyon
    td.minority_interests = parsed.get("minority_interests")
    td.financial_investments = parsed.get("financial_investments")
    td.revenue_onceki = parsed.get("revenue_onceki")
    td.flags.append(f"unit_multiplier={parsed.get('unit_multiplier', 1):.0f}")
    return td


_PHASE3B_SUBS_SNAP = None
_PHASE3B_DIALECT_MAP = None


def _phase3b_load_snap_and_map():
    """Phase 3b helper: lazy load subs_snap + dialect_map (memoized)."""
    global _PHASE3B_SUBS_SNAP, _PHASE3B_DIALECT_MAP
    if _PHASE3B_SUBS_SNAP is None:
        _PHASE3B_SUBS_SNAP = fetch_subsidiaries_snapshot(cache=True)
    if _PHASE3B_DIALECT_MAP is None:
        from dcf_engine_v4.cross_holdings import _load_dialect_map
        _PHASE3B_DIALECT_MAP = _load_dialect_map()
    return _PHASE3B_SUBS_SNAP, _PHASE3B_DIALECT_MAP


def _compute_consolidation_ratio(parent_ticker: str) -> float:
    """Phase 3b: parent_only_debt asimetri icin consolidation ratio.

    Sum(ownership × is_full × is_listed × is_consolidated_dialect)
    Capped at 0.85 (parent kendi en az %15 standalone yuku tasir).

    Banking/insurance/unknown DAHIL EDILMEZ — konsolide DCF yapilmiyor.
    """
    subs_snap, dialect_map = _phase3b_load_snap_and_map()
    subs = subs_lookup_parent(subs_snap, parent_ticker)
    ratio = 0.0
    for s in subs:
        rel = s.relationship_type
        if not isinstance(rel, str):
            continue
        if rel.lower() != "full":
            continue
        if not s.subsidiary_ticker or not isinstance(s.subsidiary_ticker, str):
            continue
        sub_dialect = dialect_map.get(s.subsidiary_ticker)
        if sub_dialect in ("banking", "insurance", "unknown", None):
            continue
        if s.ownership_pct is not None:
            try:
                ratio += float(s.ownership_pct)
            except (ValueError, TypeError):
                continue
    return min(ratio, 0.85)


# Phase 3c helpers (Damodaran Level 2/3 fallback)
_SECTOR_MULTIPLES_CACHE: Optional[dict] = None
_SECTOR_MAP_CACHE: Optional[dict] = None


def _load_sector_multiples() -> dict:
    """Damodaran sector_multiples.json memoized loader."""
    global _SECTOR_MULTIPLES_CACHE
    if _SECTOR_MULTIPLES_CACHE is not None:
        return _SECTOR_MULTIPLES_CACHE
    damo_root = REPO_API.parent / "api/data/damodaran"
    if not damo_root.exists():
        _SECTOR_MULTIPLES_CACHE = {}
        return {}
    candidates = [d for d in damo_root.iterdir() if d.is_dir()]
    if not candidates:
        _SECTOR_MULTIPLES_CACHE = {}
        return {}
    latest = sorted(candidates)[-1]
    sm_path = latest / "sector_multiples.json"
    if not sm_path.exists():
        _SECTOR_MULTIPLES_CACHE = {}
        return {}
    _SECTOR_MULTIPLES_CACHE = json.loads(sm_path.read_text(encoding="utf-8"))
    return _SECTOR_MULTIPLES_CACHE


def _load_sector_map() -> dict:
    """BIST -> Damodaran sector mapping memoized loader."""
    global _SECTOR_MAP_CACHE
    if _SECTOR_MAP_CACHE is not None:
        return _SECTOR_MAP_CACHE
    sm_path = REPO_API.parent / "api/config/damodaran_sector_map.json"
    if not sm_path.exists():
        _SECTOR_MAP_CACHE = {}
        return {}
    data = json.loads(sm_path.read_text(encoding="utf-8"))
    _SECTOR_MAP_CACHE = data.get("mapping", {})
    return _SECTOR_MAP_CACHE


def _phase3c_sector_intrinsic(td: "TickerDataV4"):
    """Phase 3c Level 2: Sector EV/EBITDA fallback."""
    if not td.sector_name:
        return None, "sector_unmapped_no_fallback"
    sector_map = _load_sector_map()
    damo_sector = sector_map.get(td.sector_name)
    if not damo_sector:
        return None, "sector_unmapped_no_fallback"
    multiples = _load_sector_multiples()
    sector_data = multiples.get(damo_sector)
    if not sector_data or not sector_data.get("ev_ebitda"):
        return None, "damodaran_sector_no_evebitda"

    ev_ebitda = float(sector_data["ev_ebitda"])
    op_income = td.op_income or 0
    depreciation = td.depreciation or 0
    ebitda = op_income + depreciation
    if ebitda <= 0:
        return None, "negative_or_zero_ebitda"

    debt = td.total_debt or 0
    cash = td.cash or 0
    enterprise_value = ev_ebitda * ebitda
    equity_value = enterprise_value - debt + cash
    if equity_value <= 0 or not td.shares_outstanding:
        return None, "negative_equity_sector_multiple"

    intrinsic = equity_value / td.shares_outstanding

    # Phase 3c sanity: Damodaran ±%100 cap (valpacket2 SOTP rule)
    # Sector multiple outlier durumunda Level 3 book_value'ya fall back
    if td.current_price_tl and td.current_price_tl > 0:
        upside = abs(intrinsic / td.current_price_tl - 1)
        if upside > 1.0:
            return None, "sector_multiple_outlier_capped"

    return intrinsic, f"sector_multiple_regression({damo_sector}@{ev_ebitda:.2f}x)"


def _phase3c_book_value_fallback(td: "TickerDataV4"):
    """Phase 3c Level 3: Book value fallback (Damodaran Dark Side)."""
    if not td.total_equity or not td.shares_outstanding:
        return None, "no_book_value_data"
    if td.total_equity <= 0:
        return None, "negative_book_value"
    return td.total_equity / td.shares_outstanding, "book_value_fallback"


def calculate_intrinsic_value(td: TickerDataV4) -> TickerDataV4:
    """Lifecycle → WACC → FCFF DCF → intrinsic per share.

    Banking/Holding/Insurance: graceful skip (Session 4.5+).
    """
    # Lifecycle classification
    lc: LifecycleResult = classify_lifecycle(
        dialect=td.dialect,
        market_cap_tl=td.market_cap_tl,
        history_rows=td.history_rows,
        year_change_pct=td.year_change_pct,
        de_ratio=td.de_ratio,
        revenue=td.revenue,
    )
    td.lifecycle_stage = lc.stage
    td.lifecycle_rationale = lc.rationale

    # Banking — Phase 4b Engine A DDM (USD MANDATORY, ADR-080 doctrine)
    # Phase 4c: 3-stage select logic (ROE>25% or explicit flag -> Damodaran fade)
    if td.dialect == "banking":
        try:
            from data_layer.banking_data import get_banking_data
            from dcf_engine.banking_ddm import dcf_ddm, dcf_ddm_3stage
            cfg = get_banking_data(td.ticker)
        except Exception as _e_imp:
            cfg = None
            td.flags.append(f"banking_ddm_import_fail: {type(_e_imp).__name__}")

        if cfg and cfg.yearly:
            try:
                bd = max(cfg.yearly, key=lambda d: d.year)
                # Damodaran USD parameters (parameters.json 2026-05-09)
                FX_TL_USD = 40.0       # May 2026 (fx_converter 2025 placeholder 39.50)
                RF_USD = 0.0397
                MATURE_ERP = 0.0423
                CRP_TR = 0.0466
                BETA = 0.85            # banking_money_center relevered
                STABLE_ROE = 0.14
                STABLE_G_USD = 0.025

                eps_usd = bd.eps_tl / FX_TL_USD
                payout = bd.payout_pct / 100.0
                roe = bd.roe_pct / 100.0
                high_growth_2s = roe * (1.0 - payout)
                coe_high = RF_USD + BETA * (MATURE_ERP + CRP_TR)
                coe_stable = RF_USD + 0.80 * (MATURE_ERP + CRP_TR * 0.5)

                # Phase 4c: 3-stage select (ROE>25% boom OR explicit flag, TR-tune)
                use_3stage = bool(cfg.use_3stage) or roe > 0.25

                if use_3stage and cfg.stage3_high_growth is not None:
                    result_3 = dcf_ddm_3stage(
                        starting_eps=eps_usd,
                        high_growth_rate=cfg.stage3_high_growth,
                        high_growth_payout=cfg.stage3_high_payout if cfg.stage3_high_payout is not None else payout,
                        high_growth_coe=coe_high,
                        stable_growth=cfg.stage3_stable_growth if cfg.stage3_stable_growth is not None else STABLE_G_USD,
                        stable_payout=cfg.stage3_stable_payout if cfg.stage3_stable_payout is not None else (1.0 - STABLE_G_USD / STABLE_ROE),
                        stable_coe=coe_stable,
                        high_growth_duration=5,
                        transition_period_years=5,
                    )
                    intrinsic_tl = result_3.value_per_share * FX_TL_USD
                    ddm_method = "banking_ddm_3stage_tr_tune"
                else:
                    stable_payout_2s = 1.0 - STABLE_G_USD / STABLE_ROE
                    result = dcf_ddm(
                        starting_eps=eps_usd,
                        high_growth_rate=high_growth_2s,
                        high_growth_payout=payout,
                        high_growth_coe=coe_high,
                        high_growth_duration=5,
                        stable_growth=STABLE_G_USD,
                        stable_payout=stable_payout_2s,
                        stable_coe=coe_stable,
                    )
                    intrinsic_tl = result.value_per_share * FX_TL_USD
                    ddm_method = "banking_ddm_2stage_usd"

                # Sanity: negative or >10000 TL -> book_value fallback (Damodaran rule)
                if intrinsic_tl <= 0 or intrinsic_tl > 10000:
                    if bd.shares_outstanding and bd.shares_outstanding > 0:
                        bvps = (bd.book_equity_tl * 1e6) / bd.shares_outstanding
                        td.intrinsic_per_share_tl = bvps
                        td.dcf_method = "banking_book_value_fallback"
                        td.flags.append(f"banking_ddm_outlier_capped: ddm={intrinsic_tl:.0f}TL -> book {bvps:.2f}TL")
                    else:
                        td.dcf_method = "banking_skip"
                        td.flags.append(f"banking_ddm_outlier_no_bvps: {intrinsic_tl:.0f}TL")
                else:
                    td.intrinsic_per_share_tl = intrinsic_tl
                    td.dcf_method = ddm_method

                if td.current_price_tl and td.current_price_tl > 0 and td.intrinsic_per_share_tl:
                    td.upside_pct = (td.intrinsic_per_share_tl / td.current_price_tl - 1) * 100

                return td
            except Exception as _e:
                td.errors.append(f"banking_ddm: {type(_e).__name__}: {_e}")
                td.flags.append(f"banking_ddm_exception_fallback")

        # No banking_data config OR exception -> book_value fallback (Damodaran Dark Side)
        if td.total_equity and td.shares_outstanding and td.total_equity > 0:
            bvps = td.total_equity / td.shares_outstanding
            td.intrinsic_per_share_tl = bvps
            td.dcf_method = "banking_book_value_fallback"
            td.flags.append("banking_no_config_book_fallback")
            if td.current_price_tl and td.current_price_tl > 0:
                td.upside_pct = (bvps / td.current_price_tl - 1) * 100
            return td

        # No config + no book_value -> keep skip
        td.dcf_method = "banking_skip"
        td.flags.append("dcf_skip: banking no_config_no_book")
        return td

    # Insurance / Unknown — DCF skip (Phase 4b sonrasi banking ayri branch)
    if td.dialect in ("insurance", "unknown"):
        td.dcf_method = f"{td.dialect}_skip"
        td.flags.append(f"dcf_skip: {td.dialect} method_not_implemented_session_4_5")
        return td

    # Holding — Phase 3b: 3-tier cross_holdings + Phase 3a fields + pragmatic debt asimetri
    if td.dialect == "holding":
        try:
            ch_result = compute_cross_holdings_value(td.ticker)
            ch_tl = ch_result.total_value_tl or 0.0
        except Exception as _ch_e:
            ch_tl = 0.0
            ch_result = None
            td.flags.append(f"holding_sotp_cross_fail: {type(_ch_e).__name__}")

        # Audit echo (her durumda populate)
        if ch_tl > 0:
            td.cross_holdings_value_tl = ch_tl
            td.cross_holdings_added_tl = ch_tl

        if not (ch_tl > 0 and td.shares_outstanding and td.shares_outstanding > 0):
            # Phase 3c Level 2 fallback (sector multiple)
            sec_intrinsic, sec_flag = _phase3c_sector_intrinsic(td)
            if sec_intrinsic:
                td.intrinsic_per_share_tl = sec_intrinsic
                td.dcf_method = sec_flag
                if td.current_price_tl:
                    td.upside_pct = (sec_intrinsic - td.current_price_tl) / td.current_price_tl * 100
                td.flags.append(f"phase3c_level2: {sec_flag}, intrinsic={sec_intrinsic:.2f}")
                return td
            # Phase 3c Level 3 fallback (book value)
            bv_intrinsic, bv_flag = _phase3c_book_value_fallback(td)
            if bv_intrinsic:
                td.intrinsic_per_share_tl = bv_intrinsic
                td.dcf_method = bv_flag
                if td.current_price_tl:
                    td.upside_pct = (bv_intrinsic - td.current_price_tl) / td.current_price_tl * 100
                td.flags.append(f"phase3c_level3: book_value={bv_intrinsic:.2f}")
                return td
            td.dcf_method = "holding_sotp_pending"
            td.flags.append(f"dcf_skip: holding SOTP pending (ch=0, sec_fail={sec_flag}, bv_fail={bv_flag})")
            return td

        # Phase 3b 5-component formula
        emi = td.equity_method_investments or 0.0
        ip = td.investment_properties or 0.0
        cash = td.cash or 0.0
        debt = td.total_debt or 0.0

        cons_ratio = _compute_consolidation_ratio(td.ticker)
        parent_only_cash = cash * (1 - cons_ratio)
        parent_only_debt = debt * (1 - cons_ratio)

        parent_equity = ch_tl + emi + ip + parent_only_cash - parent_only_debt

        if parent_equity > 0:
            td.intrinsic_per_share_tl = parent_equity / td.shares_outstanding
            td.dcf_method = "holding_sotp_phase3b"
            if td.current_price_tl:
                td.upside_pct = (
                    td.intrinsic_per_share_tl - td.current_price_tl
                ) / td.current_price_tl * 100
            td.flags.append(
                f"holding_sotp_phase3b: ch={ch_tl/1e9:.1f}B "
                f"+ emi={emi/1e9:.1f}B + ip={ip/1e9:.1f}B "
                f"+ cash_only={parent_only_cash/1e9:.1f}B "
                f"- debt_only={parent_only_debt/1e9:.1f}B "
                f"= {parent_equity/1e9:.1f}B (cons_ratio={cons_ratio:.3f})"
            )
            if ch_result and ch_result.banking_proxy_subs:
                td.flags.append(f"banking_proxy_subs: {ch_result.banking_proxy_subs}")
            if ch_result and ch_result.unknown_proxy_subs:
                td.flags.append(f"unknown_proxy_subs: {ch_result.unknown_proxy_subs}")
        else:
            td.flags.append(
                f"holding_sotp_phase3b_negative: ch={ch_tl/1e9:.1f}B "
                f"+ emi={emi/1e9:.1f}B + ip={ip/1e9:.1f}B "
                f"+ cash_only={parent_only_cash/1e9:.1f}B "
                f"- debt_only={parent_only_debt/1e9:.1f}B "
                f"= {parent_equity/1e9:.1f}B (cons_ratio={cons_ratio:.3f})"
            )
            # Phase 3c Level 2 fallback (sector multiple)
            sec_intrinsic, sec_flag = _phase3c_sector_intrinsic(td)
            if sec_intrinsic:
                td.intrinsic_per_share_tl = sec_intrinsic
                td.dcf_method = sec_flag
                if td.current_price_tl:
                    td.upside_pct = (sec_intrinsic - td.current_price_tl) / td.current_price_tl * 100
                td.flags.append(f"phase3c_level2: {sec_flag}, intrinsic={sec_intrinsic:.2f}")
                return td
            # Phase 3c Level 3 fallback (book value)
            bv_intrinsic, bv_flag = _phase3c_book_value_fallback(td)
            if bv_intrinsic:
                td.intrinsic_per_share_tl = bv_intrinsic
                td.dcf_method = bv_flag
                if td.current_price_tl:
                    td.upside_pct = (bv_intrinsic - td.current_price_tl) / td.current_price_tl * 100
                td.flags.append(f"phase3c_level3: book_value={bv_intrinsic:.2f}")
                return td
            td.dcf_method = "holding_sotp_phase3b_negative"
            td.intrinsic_per_share_tl = None
        return td

    # Industrial DCF
    if td.beta_relevered is None:
        td.errors.append("dcf: beta_relevered missing")
        return td
    if td.market_cap_tl is None or td.total_debt is None:
        td.errors.append("dcf: market_cap or total_debt missing")
        return td

    wacc_res: WACCResult = calculate_wacc(
        beta_relevered=td.beta_relevered,
        market_cap=td.market_cap_tl,
        total_debt=td.total_debt,
        op_income=td.op_income,
        interest_expense=None,  # KAP parser yet to expose interest_expense
        tax_rate=TURKEY_TAX_RATE,
    )
    td.wacc = wacc_res.wacc
    td.cost_of_equity = wacc_res.cost_of_equity
    td.cost_of_debt = wacc_res.cost_of_debt_aftertax
    td.rating = wacc_res.rating

    # FCFF DCF
    if not all(v is not None and v > 0 for v in [
        td.revenue, td.op_income, td.shares_outstanding,
    ]):
        td.errors.append("dcf: revenue/op_income/shares incomplete")
        return td

    # Damodaran ADR-011: cyclical sector op_margin normalize
    op_income_normalized, cyclical_flag = normalize_op_income(
        current_revenue=td.revenue,
        current_op_income=td.op_income,
        sector_name=td.sector_name,
    )
    td.flags.append(f"op_margin: {cyclical_flag}")

    # Faz B2 Phase 1: cross-holdings (Damodaran)
    try:
        ch_result = compute_cross_holdings_value(td.ticker)
        cross_holdings_tl = ch_result.total_value_tl
    except Exception as _ch_e:
        cross_holdings_tl = 0.0
        td.flags.append(f"cross_holdings_fail: {type(_ch_e).__name__}")

    # ========================================================================
    # Phase 5b.2: Industrial dialect Engine A swap (Damodaran-faithful, EM benchmark)
    # ESKI: Engine B (calculate_fcff_dcf) — drift +%100-220 (commits 73-74)
    # YENI: Engine A (industrial_fcff.py project_multi_year + dcf_valuation)
    #       + EM_FIRST terminal_margin (Phase 5a margin_emerg.json)
    #       + 3 ticker_override (Phase 5b.1.2.A audit: TUPRS/EREGL/BIMAS)
    #       + 4 sanity guard (negative -> book_value, extreme cap)
    # ========================================================================
    try:
        import json as _json
        from pathlib import Path as _Path
        from datetime import date as _date
        from dcf_engine.industrial_fcff import (
            ProjectionInputs as _ProjInp,
            project_multi_year as _proj_multi,
            dcf_valuation as _dcf_val,
        )
        from dcf_engine_v4.inputs_helpers import (
            compute_sales_to_capital as _s2c,
            compute_explicit_growth_rate as _gexp,
            compute_taper_config as _taper,
            compute_non_operating_assets as _nonop,
            compute_terminal_ebit_margin as _tmargin,
        )

        # Phase 5b.1.2.A: ticker-level Damodaran sector override (audit specific sub-sector)
        _TICKER_DAMO_OVERRIDE = {
            "TUPRS": "Oil/Gas Distribution",         # refinery downstream (not Integrated)
            "EREGL": "Steel",                         # pure steel (not Metals & Mining)
            "BIMAS": "Retail (Grocery and Food)",    # grocery chain (not Retail General)
        }
        damo_sector_override = _TICKER_DAMO_OVERRIDE.get(td.ticker)

        # Phase 5a EM data + Phase 3c global sector multiples (lazy load, cached)
        # Today dir oncelik, yoksa en guncel mevcut date dir fallback (idempotent)
        _damodaran_root = _Path(__file__).resolve().parent / "data" / "damodaran"
        _today_dir = _damodaran_root / _date.today().strftime("%Y_%m_%d")
        if not _today_dir.exists():
            _dated_dirs = sorted(
                [d for d in _damodaran_root.iterdir() if d.is_dir() and d.name.startswith("2026")],
                reverse=True,
            )
            if _dated_dirs:
                _today_dir = _dated_dirs[0]
        _em_margin_data = None
        _global_sm_data = None
        _em_path = _today_dir / "emerging_markets" / "margin_emerg.json"
        _g_path = _today_dir / "sector_multiples.json"
        if _em_path.exists():
            _em_margin_data = _json.loads(_em_path.read_text(encoding="utf-8"))
        if _g_path.exists():
            _global_sm_data = _json.loads(_g_path.read_text(encoding="utf-8"))

        # Engine A inputs (Phase 4a Adim 1-5 helpers)
        starting_margin = (op_income_normalized / td.revenue) if td.revenue and op_income_normalized else 0.05
        if starting_margin <= 0:
            starting_margin = 0.05
        terminal_margin = _tmargin(
            ticker_sector_tr=td.sector_name,
            starting_margin=starting_margin,
            sector_multiples_data=_global_sm_data,
            em_margin_data=_em_margin_data,
            damodaran_sector_override=damo_sector_override,
        ) or 0.10

        kap_s2c = _s2c(td.revenue, td.total_assets, td.cash) or 1.0
        explicit_g = _gexp(td.revenue, td.revenue_onceki, td.lifecycle_stage) or 0.05

        # EM Net Cap Ex/Sales floor (Phase 5b.1 ASELS fix pattern)
        em_capex_path = _today_dir / "emerging_markets" / "capex_emerg.json"
        sales_to_capital_final = kap_s2c
        if em_capex_path.exists():
            em_capex_data = _json.loads(em_capex_path.read_text(encoding="utf-8"))
            damo_s = damo_sector_override or _Path  # placeholder
            from dcf_engine_v4.inputs_helpers import _load_bist_to_damodaran_sector_map
            damo_s = damo_sector_override or _load_bist_to_damodaran_sector_map().get(td.sector_name)
            if damo_s and damo_s in em_capex_data:
                nce = em_capex_data[damo_s].get("Net Cap Ex/Sales")
                if nce and nce > 0 and explicit_g > 0:
                    em_implied_s2c = explicit_g / nce
                    sales_to_capital_final = max(kap_s2c, em_implied_s2c)

        taper = _taper(td.lifecycle_stage or "mature_stable")
        non_op = _nonop(td.financial_investments, td.investment_properties, td.equity_method_investments)
        minority = td.minority_interests or 0
        starting_tax_rate = 0.25  # Damodaran TR convention

        proj_inputs = _ProjInp(
            starting_revenues=td.revenue,
            sales_to_capital=sales_to_capital_final,
            starting_ebit_margin=starting_margin,
            terminal_ebit_margin=terminal_margin,
            margin_taper_start_year=taper["margin_taper_start_year"],
            margin_taper_end_year=taper["margin_taper_end_year"],
            starting_tax_rate=starting_tax_rate,
            terminal_tax_rate=0.25,
            tax_taper_start_year=taper["tax_taper_start_year"],
            tax_taper_end_year=taper["tax_taper_end_year"],
            explicit_growth_rate=explicit_g,
            terminal_growth_rate=0.025,
            explicit_period_years=taper["explicit_period_years"],
            transition_period_years=taper["transition_period_years"],
        )
        projections = _proj_multi(proj_inputs, total_years=10)
        result = _dcf_val(
            projections=projections,
            wacc=td.wacc or 0.12,
            stable_cost_of_capital=(td.wacc or 0.12) * 0.9,
            stable_growth=0.025,
            stable_reinvestment_rate=0.025 / 0.12,
            debt=td.total_debt or 0,
            minority_interests=minority,
            cash=td.cash or 0,
            non_operating_assets=non_op + cross_holdings_tl,  # Phase 1+2+3 cross_holdings dahil
            shares_outstanding=td.shares_outstanding,
        )
        intrinsic_tl = result.value_per_share

        # 4 Sanity Guard
        bvps = (td.total_equity / td.shares_outstanding) if (td.total_equity and td.shares_outstanding and td.total_equity > 0) else None
        market = td.current_price_tl

        if intrinsic_tl is None:
            td.dcf_method = "industrial_engine_a_skip"
            td.flags.append("engine_a_intrinsic_none")
            return td

        # Guard A: negative intrinsic -> book_value fallback (Damodaran "value destruction")
        if intrinsic_tl < 0:
            if bvps is not None:
                td.intrinsic_per_share_tl = bvps
                td.dcf_method = "industrial_engine_a_book_fallback"
                td.flags.append(f"negative_fcff_value_destruction: dcf={intrinsic_tl:.2f} -> bvps {bvps:.2f}")
            else:
                td.dcf_method = "industrial_engine_a_skip"
                td.flags.append(f"negative_fcff_no_bvps: {intrinsic_tl:.2f}")
        # Guard C: extreme overpriced (intrinsic > market * 20) -> book_value
        elif market and market > 0 and intrinsic_tl > market * 20:
            if bvps is not None:
                td.intrinsic_per_share_tl = bvps
                td.dcf_method = "industrial_engine_a_book_fallback"
                td.flags.append(f"extreme_undervalued_review: dcf={intrinsic_tl:.2f} -> bvps {bvps:.2f}")
            else:
                td.intrinsic_per_share_tl = intrinsic_tl
                td.dcf_method = "industrial_engine_a_em"
        # Guard B: extreme underpriced (intrinsic < market * 0.10) -> KEEP (Damodaran "overvalued")
        elif market and market > 0 and intrinsic_tl < market * 0.10:
            td.intrinsic_per_share_tl = intrinsic_tl
            td.dcf_method = "industrial_engine_a_em"
            td.flags.append(f"extreme_overvalued_market_premium: dcf={intrinsic_tl:.2f} market {market:.2f}")
        else:
            # Normal case
            td.intrinsic_per_share_tl = intrinsic_tl
            td.dcf_method = "industrial_engine_a_em"

        if td.current_price_tl and td.current_price_tl > 0 and td.intrinsic_per_share_tl:
            td.upside_pct = (td.intrinsic_per_share_tl - td.current_price_tl) / td.current_price_tl * 100

        # Phase 1 cross_holdings audit echo
        td.cross_holdings_value_tl = cross_holdings_tl if cross_holdings_tl > 0 else None
        td.cross_holdings_added_tl = cross_holdings_tl if cross_holdings_tl > 0 else None

        # Phase 5c: Damodaran ImpliedROCROE terminal value sanity
        try:
            from dcf_engine_v4.inputs_helpers import compute_implied_roc as _imp_roc
            em_capex_path = _today_dir / "emerging_markets" / "capex_emerg.json"
            if em_capex_path.exists():
                em_capex = _json.loads(em_capex_path.read_text(encoding="utf-8"))
                damo_s = damo_sector_override or _load_bist_to_damodaran_sector_map().get(td.sector_name)
                if damo_s and damo_s in em_capex:
                    nce_sales = em_capex[damo_s].get("Net Cap Ex/Sales")
                    implied_roc_val = _imp_roc(
                        stable_growth=0.025,
                        net_cap_ex_sales=nce_sales,
                        stable_op_margin=terminal_margin,
                        tax_rate=0.25,
                    )
                    td.implied_roc = implied_roc_val
                    if implied_roc_val is not None and td.wacc:
                        sustainable = implied_roc_val >= td.wacc
                        td.terminal_value_sustainable = sustainable
                        if not sustainable:
                            td.flags.append(f"implied_roc_below_wacc: {implied_roc_val*100:.2f}% < {td.wacc*100:.2f}%")
        except Exception as _ic_e:
            td.flags.append(f"implied_roc_compute_fail: {type(_ic_e).__name__}")

        # Phase 4d: Multi-multiple PE/PBV consensus (Damodaran cross-check)
        try:
            from dcf_engine_v4.inputs_helpers import (
                compute_pe_implied_intrinsic as _pe_imp,
                compute_pbv_implied_intrinsic as _pbv_imp,
                compute_consensus as _consensus,
            )
            em_pe_path = _today_dir / "emerging_markets" / "pe_emerg.json"
            em_pbv_path = _today_dir / "emerging_markets" / "pbv_emerg.json"
            em_pe_data = _json.loads(em_pe_path.read_text(encoding="utf-8")) if em_pe_path.exists() else {}
            em_pbv_data = _json.loads(em_pbv_path.read_text(encoding="utf-8")) if em_pbv_path.exists() else {}

            damo_s_consensus = damo_sector_override or _load_bist_to_damodaran_sector_map().get(td.sector_name)
            sector_pe = None
            sector_pbv = None
            if damo_s_consensus:
                sector_pe = (em_pe_data.get(damo_s_consensus) or {}).get("Trailing PE")
                sector_pbv = (em_pbv_data.get(damo_s_consensus) or {}).get("PBV")

            pe_implied = _pe_imp(td.op_income, td.shares_outstanding, sector_pe, tax_rate=0.25)
            pbv_implied = _pbv_imp(td.total_equity, td.shares_outstanding, sector_pbv)

            consensus, dispersion = _consensus(td.intrinsic_per_share_tl, pe_implied, pbv_implied)
            td.pe_implied = pe_implied
            td.pbv_implied = pbv_implied
            td.consensus_intrinsic = consensus
            td.consensus_dispersion = dispersion
            if dispersion is not None and dispersion > 0.5:
                td.flags.append(f"high_multi_multiple_dispersion: {dispersion:.2f}")
        except Exception as _mm_e:
            td.flags.append(f"multi_multiple_fail: {type(_mm_e).__name__}")

        return td

    except Exception as _ea_e:
        # Engine A swap exception -> fallback to Engine B legacy (defensive)
        td.errors.append(f"engine_a_exception: {type(_ea_e).__name__}: {_ea_e}")
        td.flags.append("engine_a_fallback_to_b")
        # Engine B legacy path (kept for safety)
        inputs = DCFInputs(
            revenue=td.revenue,
            op_income=op_income_normalized,
            capex=td.capex or 0.0,
            da=td.depreciation or 0.0,
            working_capital=td.working_capital or 0.0,
            tax_rate=TURKEY_TAX_RATE,
            total_debt=td.total_debt,
            cash=td.cash or 0.0,
            shares_outstanding=td.shares_outstanding,
            wacc=td.wacc,
            lifecycle_stage=td.lifecycle_stage,
            cross_holdings_value=cross_holdings_tl,
        )
        dcf: DCFResult = calculate_fcff_dcf(inputs)
        if dcf.error:
            td.errors.append(f"dcf: {dcf.error}")
            td.dcf_method = f"engine_b_legacy_fcff_failed:{dcf.error[:30]}"
            return td
        if dcf.intrinsic_per_share is not None and dcf.intrinsic_per_share < 0:
            td.dcf_method = "engine_b_legacy_fcff_negative"
            return td
        td.intrinsic_per_share_tl = dcf.intrinsic_per_share
        td.dcf_method = "engine_b_legacy_fcff_2stage"
        if td.current_price_tl and dcf.intrinsic_per_share:
            td.upside_pct = (dcf.intrinsic_per_share - td.current_price_tl) / td.current_price_tl * 100
        td.cross_holdings_value_tl = cross_holdings_tl if cross_holdings_tl > 0 else None
        td.cross_holdings_added_tl = dcf.cross_holdings_added_tl
        return td


def assemble_and_value(
    ticker: str,
    caches: Optional[_Caches] = None,
    fetch_yfinance_live: bool = True,
) -> TickerDataV4:
    """Tek atımda assemble + enrich + intrinsic value + Phase 7.1 MoS."""
    td = assemble_ticker_data(ticker, caches=caches, fetch_yfinance_live=fetch_yfinance_live)
    td = enrich_full_financials(td)
    td = calculate_intrinsic_value(td)
    # Phase 7.1: Margin of Safety + composite signal (tum dialect tek nokta)
    try:
        from dcf_engine_v4.inputs_helpers import apply_mos_to_td as _apply_mos
        _apply_mos(td)
    except Exception as _mos_e:
        td.flags.append(f"mos_apply_fail: {type(_mos_e).__name__}")
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


def run_pipeline_v4(
    universe: Optional[List[str]] = None,
    progress: bool = True,
    fetch_yfinance_live: bool = False,
) -> List[TickerDataV4]:
    """Full v4 pipeline: assemble + enrich + DCF intrinsic.

    Returns TickerDataV4 list. Banking/Holding/Insurance graceful skip.

    fetch_yfinance_live=False (default): yfinance cache CSV'den oku (hızlı).
    fetch_yfinance_live=True: anlık fetch (yavaş, 605 ticker × ~30 dk).
    """
    caches = _Caches()
    if universe is None:
        universe = [r.ticker for r in caches.float_snap.records]

    results: List[TickerDataV4] = []
    for i, t in enumerate(universe, 1):
        td = assemble_and_value(
            t, caches=caches, fetch_yfinance_live=fetch_yfinance_live,
        )
        results.append(td)
        if progress and i % 50 == 0:
            n_complete = sum(1 for r in results if r.is_complete)
            n_dcf = sum(1 for r in results if r.intrinsic_per_share_tl is not None)
            print(f"  [{i:3d}/{len(universe)}] complete={n_complete}/{i}  dcf={n_dcf}")
    return results


def save_v4_batch_json(
    results: List[TickerDataV4],
    output_path: Optional[Path] = None,
) -> Path:
    """v4 results → JSON for Tarayıcı sayfası."""
    if output_path is None:
        output_path = OUTPUTS_DIR / "turkey_v4_batch.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetch_date": date.today().isoformat(),
        "total_count": len(results),
        "complete_count": sum(1 for r in results if r.is_complete),
        "dcf_count": sum(1 for r in results if r.intrinsic_per_share_tl is not None),
        "anchor_tuprs": next(
            (r.intrinsic_per_share_tl for r in results if r.ticker == "TUPRS"),
            None,
        ),
        "tickers": [asdict(r) for r in results],
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return output_path


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

        td = assemble_and_value(ticker, caches=caches, fetch_yfinance_live=True)

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

        # DCF section
        print(f"  ── DCF ─────────────────────────────────")
        print(f"  Lifecycle:           {td.lifecycle_stage}  ({td.lifecycle_rationale})")
        if td.revenue is not None:
            print(f"  Revenue (cari):      {td.revenue:>20,.0f} TL")
        if td.op_income is not None:
            print(f"  Op Income (cari):    {td.op_income:>20,.0f} TL")
        if td.wacc is not None:
            print(f"  Cost of Equity:      {td.cost_of_equity*100:>6.2f}%")
            print(f"  Cost of Debt (a/t):  {td.cost_of_debt*100:>6.2f}%")
            print(f"  WACC:                {td.wacc*100:>6.2f}%  rating={td.rating}")
        print(f"  DCF method:          {td.dcf_method}")
        if td.intrinsic_per_share_tl is not None:
            print(f"  Intrinsic /share:    {td.intrinsic_per_share_tl:>10.2f} TL")
            if td.upside_pct is not None:
                print(f"  Upside vs market:    {td.upside_pct:>+7.2f}%")

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

        # TUPRS anchor regression test
        if td.ticker == "TUPRS" and td.intrinsic_per_share_tl is not None:
            anchor = 187.10
            tol_lower = anchor * 0.88   # 164.65
            tol_upper = anchor * 1.12   # 209.55
            in_band = tol_lower <= td.intrinsic_per_share_tl <= tol_upper
            band_str = f"[{tol_lower:.2f}-{tol_upper:.2f}]"
            verdict = "✓ IN BAND" if in_band else "✗ OUT OF BAND"
            print(f"\n  ★ TUPRS ANCHOR REGRESSION:")
            print(f"     Intrinsic:    {td.intrinsic_per_share_tl:.2f} TL")
            print(f"     Anchor:       {anchor:.2f} TL")
            print(f"     ±%12 band:    {band_str}")
            print(f"     Verdict:      {verdict}")
