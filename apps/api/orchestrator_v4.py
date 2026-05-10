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
    td.flags.append(f"unit_multiplier={parsed.get('unit_multiplier', 1):.0f}")
    return td


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

    # Banking / Insurance / Unknown — DCF skip
    if td.dialect in ("banking", "insurance", "unknown"):
        td.dcf_method = f"{td.dialect}_skip"
        td.flags.append(f"dcf_skip: {td.dialect} method_not_implemented_session_4_5")
        return td

    # Holding — Faz B2 Phase 2 Adim 3: minimal SOTP + negative equity guard
    if td.dialect == "holding":
        try:
            ch_result = compute_cross_holdings_value(td.ticker)
            ch_tl = ch_result.total_value_tl
        except Exception as _ch_e:
            ch_tl = 0.0
            td.flags.append(f"holding_sotp_cross_fail: {type(_ch_e).__name__}")

        # Audit echo (her durumda populate)
        if ch_tl > 0:
            td.cross_holdings_value_tl = ch_tl
            td.cross_holdings_added_tl = ch_tl

        # Minimal SOTP attempt
        if ch_tl > 0 and td.shares_outstanding and td.shares_outstanding > 0:
            equity_minimal = ch_tl + (td.cash or 0) - (td.total_debt or 0)

            if equity_minimal > 0:
                td.intrinsic_per_share_tl = equity_minimal / td.shares_outstanding
                td.dcf_method = "holding_sotp_minimal"
                if td.current_price_tl:
                    td.upside_pct = (
                        td.intrinsic_per_share_tl - td.current_price_tl
                    ) / td.current_price_tl * 100
                td.flags.append(
                    f"holding_sotp_minimal: cross={ch_tl:.0f} "
                    f"+ cash={td.cash or 0:.0f} - debt={td.total_debt or 0:.0f} "
                    f"= {equity_minimal:.0f}"
                )
                return td
            else:
                td.dcf_method = "holding_sotp_minimal_negative_equity"
                td.flags.append(
                    f"holding_sotp_minimal_negative: cross={ch_tl:.0f} "
                    f"+ cash={td.cash or 0:.0f} - debt={td.total_debt or 0:.0f} "
                    f"= {equity_minimal:.0f}"
                )
                td.flags.append("holding_sotp_full_pending: full sub valuation Phase 3 scope")
                return td

        # Cross-holdings yok veya shares yok → eski davranis
        td.dcf_method = "holding_sotp_pending"
        td.flags.append("dcf_skip: holding SOTP pending (cross_holdings=0 or shares missing)")
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
        td.dcf_method = f"fcff_failed:{dcf.error[:30]}"
        return td

    # Negative intrinsic guard (capital-intensive cyclical reinvestment > NOPAT)
    if dcf.intrinsic_per_share is not None and dcf.intrinsic_per_share < 0:
        td.flags.append(
            f"dcf_negative_intrinsic={dcf.intrinsic_per_share:.2f} → NULL "
            f"(reinvestment > NOPAT, capital-intensive cyclical)"
        )
        td.dcf_method = "fcff_negative_intrinsic_unsuitable"
        return td

    # High D/E distress (>3.0)
    if td.de_ratio is not None and td.de_ratio > 3.0:
        td.flags.append(f"high_leverage_warn: D/E={td.de_ratio:.2f}")
        # DCF yine yapılır ama warning

    td.intrinsic_per_share_tl = dcf.intrinsic_per_share
    td.dcf_method = "industrial_fcff_2stage"
    if td.current_price_tl and dcf.intrinsic_per_share:
        td.upside_pct = (dcf.intrinsic_per_share - td.current_price_tl) / td.current_price_tl * 100

    # Faz B2 Phase 1 Adim 4 tamamlama: cross-holdings audit echo
    td.cross_holdings_value_tl = cross_holdings_tl if cross_holdings_tl > 0 else None
    td.cross_holdings_added_tl = dcf.cross_holdings_added_tl

    return td


def assemble_and_value(
    ticker: str,
    caches: Optional[_Caches] = None,
    fetch_yfinance_live: bool = True,
) -> TickerDataV4:
    """Tek atımda assemble + enrich + intrinsic value."""
    td = assemble_ticker_data(ticker, caches=caches, fetch_yfinance_live=fetch_yfinance_live)
    td = enrich_full_financials(td)
    td = calculate_intrinsic_value(td)
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
