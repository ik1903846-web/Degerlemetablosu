"""
Lifecycle-Adaptive Valuation Orchestrator.

End-to-end pipeline:
  ticker → fetch → map → USD convert → classify → DCF → value/share

Otomatik karar zinciri:
- Banking detection (financialGroup XI_30)
- Lifecycle classification (6-stage)
- Model selection (cyclical/industrial/banking/young/decline/distress)
- Currency conversion (TL → USD → TL)
- Real shares lookup
- Market comparison

Tek call ile full Damodaran valuation.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Dict, Any

from data_layer.isyatirim_scraper import (
    fetch_yearly_extended,
    FG_INDUSTRIAL,
    FG_BANKING,
)
from data_layer.damodaran_mapper import map_to_damodaran_inputs, DamodaranDCFInputs
from data_layer.fx_converter import (
    get_static_rates,
    convert_inputs_to_usd,
    STATIC_YEAR_END_RATES,
)
from data_layer.shares_fetcher import get_shares_outstanding, SharesOutstanding
from data_layer.market_price_fetcher import fetch_spot_price
from data_layer.ticker_mapping import resolve_current_ticker
from data_layer.sector_mapping import get_damodaran_sector
from data_layer.damodaran_db import fetch_sector_unlevered_beta
from dcf_engine.lifecycle_classifier import (
    classify_lifecycle,
    LifecycleClassification,
    LifecycleStage,
    SubClassification,
)
from dcf_engine.cyclical_dcf import cyclical_dcf_valuation
from dcf_engine.cost_of_capital import relever_beta

logger = logging.getLogger(__name__)


# ============================================================================
# Damodaran Parameters (Türkiye, Nisan 2026)
# ============================================================================

DAMODARAN_PARAMS = {
    "rf_usd": 0.0397,
    "mature_erp": 0.0444,
    "turkey_crp": 0.0601,
    "stable_growth_usd": 0.03,
    "statutory_tax": 0.25,
    "spot_rate_usd_tl": 35.37,  # 24 Nisan 2026
}


# ============================================================================
# Banking Detection
# ============================================================================

# Manuel banking ticker listesi (financialGroup XI_30)
# İleride: KAP sektör API'siyle dinamik
KNOWN_BANKING_TICKERS = {
    "GARAN", "AKBNK", "ISCTR", "YKBNK", "HALKB", "VAKBN",
    "QNBFB", "TSKB", "SKBNK", "ICBCT", "ALBRK",
}


def is_banking_ticker(ticker: str) -> bool:
    """Banking ticker tespiti (statik liste, ileride dinamik)."""
    return ticker.upper() in KNOWN_BANKING_TICKERS


# ============================================================================
# Holding Whitelist (bottom-up beta SKIP)
# ============================================================================

# Damodaran disiplini: 'diversified' sector beta (β=0.3634) USA conglomerates
# için (GE, Honeywell). BIST holding'leri farklı yapılı (otomotiv + enerji +
# finans + ...) — SOTP yaklaşımı doğru ama Faz 2.5'te yapılacak.
# Şimdilik bu set'teki ticker'lar için bottom-up beta SKIP (eski β=1 implied).
HOLDING_TICKERS_NO_BOTTOMUP_BETA = {"KCHOL", "SAHOL"}
# Future (Faz 2.5 SOTP gelince): TKFEN, TRHOL, vb. eklenebilir, set kalkar


# ============================================================================
# Valuation Report (Output)
# ============================================================================

@dataclass
class ValuationReport:
    """Full valuation pipeline sonucu."""
    ticker: str
    success: bool

    # Pipeline metadata
    is_banking: bool
    financial_group: str
    periods_fetched: int
    items_mapped: int

    # Lifecycle classification
    lifecycle: Optional[LifecycleClassification]

    # DCF results
    dcf_executed: bool
    model_used: str

    # Currency
    currency_data: str  # "TL"
    currency_dcf: str   # "USD" or "TL"

    # Valuation outputs
    equity_value_usd: Optional[float]
    equity_value_tl: Optional[float]
    shares_outstanding: Optional[int]
    value_per_share_usd: Optional[float]
    value_per_share_tl: Optional[float]

    # Market comparison
    market_price_tl: Optional[float]
    upside_pct: Optional[float]
    damodaran_verdict: str  # "AL", "İZLE", "BEKLE", "İZLE-SAT", "SAT"

    # Diagnostics
    wacc: Optional[float]
    normalized_op_margin: Optional[float]
    reasoning: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# ============================================================================
# Helper: Damodaran Verdict
# ============================================================================

def calculate_verdict(upside_pct: float) -> str:
    """Margin of safety bazlı Damodaran verdict."""
    if upside_pct > 30:
        return "AL"
    elif upside_pct > 10:
        return "IZLE-AL"
    elif upside_pct > -10:
        return "BEKLE"
    elif upside_pct > -30:
        return "IZLE-SAT"
    else:
        return "SAT"


# ============================================================================
# Main Orchestrator
# ============================================================================

async def analyze_ticker(
    ticker: str,
    market_price_tl: Optional[float] = None,
    years_back: int = 12,
) -> ValuationReport:
    """
    End-to-end ticker analizi.

    Args:
        ticker: BIST ticker (TUPRS, GARAN, vb.)
        market_price_tl: Optional current market price for upside calc
        years_back: Historical depth (default 12 for cyclical)

    Returns:
        ValuationReport with full results
    """
    # Ticker resolution — rename handling (Faz 2.4.5)
    original_ticker = ticker.upper()
    ticker = resolve_current_ticker(ticker)

    if ticker != original_ticker:
        logger.info(f"Ticker rename: {original_ticker} → {ticker}")

    # Auto-fetch market price if not provided (Faz 2.4.4)
    if market_price_tl is None:
        try:
            price_obj = await fetch_spot_price(ticker)
            if price_obj is not None:
                market_price_tl = float(price_obj.spot_price)
        except Exception as e:
            logger.warning(f"{ticker}: spot price auto-fetch failed: {e}")

    # Initialize report
    report = ValuationReport(
        ticker=ticker,
        success=False,
        is_banking=False,
        financial_group="",
        periods_fetched=0,
        items_mapped=0,
        lifecycle=None,
        dcf_executed=False,
        model_used="none",
        currency_data="TL",
        currency_dcf="USD",
        equity_value_usd=None,
        equity_value_tl=None,
        shares_outstanding=None,
        value_per_share_usd=None,
        value_per_share_tl=None,
        market_price_tl=market_price_tl,
        upside_pct=None,
        damodaran_verdict="UNKNOWN",
        wacc=None,
        normalized_op_margin=None,
    )

    try:
        # ====================================================================
        # STEP 1: Banking Detection + Financial Group
        # ====================================================================
        report.is_banking = is_banking_ticker(ticker)
        report.financial_group = FG_BANKING if report.is_banking else FG_INDUSTRIAL

        if report.is_banking:
            report.reasoning.append(f"Banking ticker detected (XI_30)")
            report.errors.append("Banking DCF orchestration Faz 2.3.1'de eklenecek (şu an industrial only)")
            report.model_used = "banking_ddm"
            return report  # Skip — banking pipeline ayrı

        report.reasoning.append(f"Industrial ticker (XI_29)")

        # ====================================================================
        # STEP 2: Fetch + Map
        # ====================================================================
        years = list(range(2024, 2024 - years_back, -1))
        statements = await fetch_yearly_extended(
            ticker=ticker,
            years=years,
            financial_group=report.financial_group,
        )
        report.periods_fetched = len(statements.periods)

        inputs_tl = map_to_damodaran_inputs(statements)
        report.items_mapped = inputs_tl.items_found

        if inputs_tl.items_found < 8:
            report.errors.append(f"Only {inputs_tl.items_found}/12 items mapped, insufficient data")
            return report

        report.reasoning.append(f"{report.periods_fetched}-yıl historical, {inputs_tl.items_found}/12 items")

        # ====================================================================
        # STEP 3: USD Conversion
        # ====================================================================
        fx_series = get_static_rates(years)
        inputs_usd = convert_inputs_to_usd(inputs_tl, fx_series)
        report.reasoning.append("USD conversion completed (year-end rates)")

        # ====================================================================
        # STEP 4: Lifecycle Classification
        # ====================================================================
        report.lifecycle = classify_lifecycle(inputs_usd)
        report.reasoning.append(
            f"Lifecycle: {report.lifecycle.stage.value} + "
            f"{[s.value for s in report.lifecycle.sub_classifications]}"
        )
        report.model_used = report.lifecycle.recommended_model

        # ====================================================================
        # STEP 5: DCF Execute (model-adaptive)
        # ====================================================================
        if report.model_used == "cyclical_dcf":
            equity_value_usd = await _execute_cyclical_dcf(
                inputs_usd=inputs_usd,
                lifecycle=report.lifecycle,
                report=report,
            )
        elif report.model_used == "industrial_fcff":
            # Industrial FCFF orchestration (basit case)
            equity_value_usd = await _execute_industrial_fcff(
                inputs_usd=inputs_usd,
                lifecycle=report.lifecycle,
                report=report,
            )
        else:
            report.errors.append(f"Model {report.model_used} orchestration TBD (Faz 2.3.x)")
            return report

        if equity_value_usd is None:
            report.errors.append("DCF execution returned None")
            return report

        report.equity_value_usd = equity_value_usd
        report.equity_value_tl = equity_value_usd * DAMODARAN_PARAMS["spot_rate_usd_tl"]
        report.dcf_executed = True

        # ====================================================================
        # STEP 6: Value per Share
        # ====================================================================
        shares_obj = get_shares_outstanding(ticker)
        if shares_obj is None:
            report.errors.append(f"Shares outstanding not found for {ticker}")
            return report

        report.shares_outstanding = shares_obj.shares
        report.value_per_share_usd = equity_value_usd / shares_obj.shares
        report.value_per_share_tl = (
            report.value_per_share_usd * DAMODARAN_PARAMS["spot_rate_usd_tl"]
        )

        # ====================================================================
        # STEP 7: Market Comparison
        # ====================================================================
        if market_price_tl is not None:
            report.upside_pct = (
                (report.value_per_share_tl - market_price_tl) / market_price_tl * 100
            )
            report.damodaran_verdict = calculate_verdict(report.upside_pct)

        report.success = True
        return report

    except Exception as e:
        logger.exception(f"Orchestrator failed for {ticker}")
        report.errors.append(f"Pipeline error: {type(e).__name__}: {e}")
        return report


# ============================================================================
# Model Executors (private)
# ============================================================================

async def _execute_cyclical_dcf(
    inputs_usd: DamodaranDCFInputs,
    lifecycle: LifecycleClassification,
    report: ValuationReport,
) -> Optional[float]:
    """Cyclical DCF execute (Toyota 2009 pattern)."""

    # Through-the-cycle margin (12-yıl avg)
    margins = [m for m in inputs_usd.operating_margin if m is not None]
    if not margins:
        report.errors.append("No valid margins for cyclical normalize")
        return None

    avg_margin = sum(margins) / len(margins)
    report.normalized_op_margin = float(avg_margin)

    # Current revenue
    current_revenue = float(inputs_usd.revenue[0]) if inputs_usd.revenue[0] else None
    if current_revenue is None:
        report.errors.append("Current revenue is None")
        return None

    # WACC (USD-bazlı, Faz 2.4.6 Component 1: bottom-up beta + Hamada relever)
    debt_usd = float(inputs_usd.total_debt[0]) if inputs_usd.total_debt[0] else 0
    equity_usd = float(inputs_usd.total_equity[0]) if inputs_usd.total_equity[0] else 0

    if equity_usd <= 0:
        report.errors.append("Equity value <= 0")
        return None

    # İki farklı oran:
    #   debt_weight = D/(D+E) → WACC weighting için
    #   debt_to_equity = D/E → Hamada relever için
    debt_weight = debt_usd / (debt_usd + equity_usd) if (debt_usd + equity_usd) > 0 else 0
    debt_to_equity = debt_usd / equity_usd

    tax_rate = DAMODARAN_PARAMS["statutory_tax"]

    # ─────────────────────────────────────────────────────────────────────
    # Bottom-up beta (Damodaran ADR-065): sektör β_unlev → Hamada relever
    # ─────────────────────────────────────────────────────────────────────
    sector: Optional[str] = None
    beta_unlev: Optional[float] = None
    beta_lev: Optional[float] = None

    if report.ticker.upper() in HOLDING_TICKERS_NO_BOTTOMUP_BETA:
        # Holding fallback: 'diversified' sector beta methodologically yanlış
        # (USA conglomerates pattern). SOTP gerek — Faz 2.5'te.
        report.reasoning.append(
            "Holding ticker — bottom-up beta SKIP "
            "(diversified sector inappropriate for BIST holdings, "
            "SOTP needed in Faz 2.5)"
        )
    else:
        sector = get_damodaran_sector(report.ticker)
        if sector is not None:
            beta_unlev_decimal = await fetch_sector_unlevered_beta(sector)
            if beta_unlev_decimal is not None:
                beta_unlev = float(beta_unlev_decimal)
                beta_lev = relever_beta(
                    unlevered_beta=beta_unlev,
                    debt_to_equity=debt_to_equity,
                    tax_rate=tax_rate,
                )
                report.reasoning.append(
                    f"Bottom-up beta: sector={sector}, "
                    f"β_unlev={beta_unlev:.4f}, "
                    f"D/E={debt_to_equity:.4f}, "
                    f"β_lev={beta_lev:.4f}"
                )
            else:
                report.reasoning.append(
                    f"Sector '{sector}' DB'de yok — fallback β=1 implied"
                )
        else:
            report.reasoning.append(
                f"{report.ticker} sector mapping yok — fallback β=1 implied"
            )

    # Cost of Equity: Rf + β × ERP + λ × CRP  (λ=1.0 BIST domestic)
    if beta_lev is not None:
        coe_usd = (
            DAMODARAN_PARAMS["rf_usd"]
            + beta_lev * DAMODARAN_PARAMS["mature_erp"]
            + 1.0 * DAMODARAN_PARAMS["turkey_crp"]
        )
    else:
        # Fallback: β=1 implied (eski davranış — additive Rf + ERP + CRP)
        coe_usd = (
            DAMODARAN_PARAMS["rf_usd"]
            + DAMODARAN_PARAMS["mature_erp"]
            + DAMODARAN_PARAMS["turkey_crp"]
        )

    pretax_kd = DAMODARAN_PARAMS["rf_usd"] + 0.03  # BB rated default (Component 2'de değişecek)
    after_tax_kd = pretax_kd * (1 - tax_rate)

    wacc = (1 - debt_weight) * coe_usd + debt_weight * after_tax_kd
    report.wacc = wacc
    report.reasoning.append(
        f"WACC={wacc*100:.2f}% (CoE={coe_usd*100:.2f}%, AT_Kd={after_tax_kd*100:.2f}%, "
        f"debt_w={debt_weight:.4f})"
    )

    # Stable phase
    g = DAMODARAN_PARAMS["stable_growth_usd"]
    roc = wacc  # Mature firm assumption
    reinv_rate = g / roc if roc > 0 else 0

    # Cash + minority
    cash_usd = float(inputs_usd.cash[0]) if inputs_usd.cash[0] else 0

    # Execute cyclical_dcf
    result = cyclical_dcf_valuation(
        current_revenues=current_revenue,
        historical_avg_margin=float(avg_margin),
        growth_rate=g,
        tax_rate=DAMODARAN_PARAMS["statutory_tax"],
        reinvestment_rate=reinv_rate,
        wacc=wacc,
        cash=cash_usd,
        non_operating_assets=0.0,
        debt=debt_usd,
        minority_interests=0.0,
        shares_outstanding=1,  # placeholder, actual shares orchestrator'da
        options_value=0.0,
        current_op_margin=float(inputs_usd.operating_margin[0]) if inputs_usd.operating_margin[0] else None,
    )

    return result.equity_bridge.equity_value


async def _execute_industrial_fcff(
    inputs_usd: DamodaranDCFInputs,
    lifecycle: LifecycleClassification,
    report: ValuationReport,
) -> Optional[float]:
    """Industrial FCFF execute (2-stage)."""
    # Şu an basit: cyclical_dcf'i fallback olarak kullan
    # İleride: industrial_fcff modülünü import et + 2-stage execute
    report.reasoning.append("Industrial FCFF: fallback to cyclical_dcf (Faz 2.3.x'te 2-stage)")
    return await _execute_cyclical_dcf(inputs_usd, lifecycle, report)


# ============================================================================
# Print Helper (optional)
# ============================================================================

def print_report(report: ValuationReport) -> None:
    """Pretty-print valuation report."""
    print("="*80)
    print(f"VALUATION REPORT — {report.ticker}")
    print("="*80)

    print(f"\nSuccess: {report.success}")
    print(f"Banking: {report.is_banking}")
    print(f"Financial Group: {report.financial_group}")
    print(f"Periods: {report.periods_fetched}")
    print(f"Items: {report.items_mapped}/12")

    if report.lifecycle:
        print(f"\nLifecycle:")
        print(f"  Stage: {report.lifecycle.stage.value}")
        print(f"  Sub: {[s.value for s in report.lifecycle.sub_classifications]}")
        print(f"  Confidence: {report.lifecycle.confidence*100:.0f}%")

    print(f"\nModel: {report.model_used}")
    print(f"DCF Executed: {report.dcf_executed}")

    if report.dcf_executed:
        print(f"\nValuation:")
        print(f"  Equity Value (USD): {report.equity_value_usd/1_000_000_000:.2f}B")
        print(f"  Equity Value (TL):  {report.equity_value_tl/1_000_000_000:.2f}B")
        print(f"  Shares Outstanding: {report.shares_outstanding:,}")
        print(f"  Value/Share (USD):  ${report.value_per_share_usd:.4f}")
        print(f"  Value/Share (TL):   {report.value_per_share_tl:.2f} TL")
        print(f"  WACC:               {report.wacc*100:.2f}%")
        print(f"  Normalized Margin:  {report.normalized_op_margin*100:.2f}%")

    if report.market_price_tl is not None:
        print(f"\nMarket Comparison:")
        print(f"  Market Price:       {report.market_price_tl:.2f} TL")
        print(f"  Upside/(Discount):  {report.upside_pct:+.2f}%")
        print(f"  Damodaran Verdict:  {report.damodaran_verdict}")

    if report.reasoning:
        print(f"\nReasoning:")
        for r in report.reasoning:
            print(f"  • {r}")

    if report.errors:
        print(f"\nErrors:")
        for e in report.errors:
            print(f"  ⚠ {e}")

    print("="*80)
