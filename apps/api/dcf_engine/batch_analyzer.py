"""
BIST 30 Batch Analyzer.

Paralel orchestration:
- asyncio.gather: 25 ticker eş zamanlı
- Ranking: en ucuz (deep value) → en pahalı
- CSV + JSON output
- Failure isolation: 1 ticker fail diğerleri etkilemiyor

Banking ticker'lar skip edilir (Faz 2.3.1'de eklenecek).
"""

import asyncio
import csv
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Dict

from dcf_engine.orchestrator import (
    analyze_ticker,
    ValuationReport,
    KNOWN_BANKING_TICKERS,
)

logger = logging.getLogger(__name__)


# ============================================================================
# BIST 30 Universe (industrial only — banking skip)
# ============================================================================

BIST_30_INDUSTRIAL = [
    # Energy & Refining
    "TUPRS",
    "PETKM",

    # Steel & Mining
    "EREGL",
    "KRDMD",
    "KOZAL",
    "KOZAA",

    # Consumer & Retail
    "BIMAS",
    "MGROS",
    "SOKM",
    "CCOLA",

    # Industrials
    "TOASO",
    "FROTO",
    "ARCLK",
    "ASELS",

    # Aviation
    "THYAO",
    "PGSUS",

    # Holding
    "KCHOL",
    "SAHOL",

    # Construction
    "ENKAI",
]


# ============================================================================
# Batch Result
# ============================================================================

@dataclass
class BatchSummary:
    """Batch run özeti."""
    timestamp: str
    total_tickers: int
    successful: int
    failed: int
    skipped_banking: int
    duration_seconds: float

    # Aggregated stats
    avg_upside_pct: Optional[float]
    deep_value_count: int  # upside > 30%
    fair_value_count: int  # -10% to +10%
    overvalued_count: int  # < -30%


# ============================================================================
# Batch Analyze
# ============================================================================

async def analyze_batch(
    tickers: List[str],
    market_prices: Optional[Dict[str, float]] = None,
    max_concurrent: int = 5,
) -> List[ValuationReport]:
    """
    Paralel ticker analizi.

    Args:
        tickers: BIST ticker listesi
        market_prices: Opsiyonel ticker → price dict
        max_concurrent: Aynı anda çalışan task sayısı (rate limit için)

    Returns:
        Liste of ValuationReport (her ticker için)
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def analyze_with_semaphore(ticker: str) -> ValuationReport:
        async with semaphore:
            price = market_prices.get(ticker) if market_prices else None
            try:
                return await analyze_ticker(
                    ticker=ticker,
                    market_price_tl=price,
                )
            except Exception as e:
                logger.exception(f"Failed: {ticker}")
                # Return error report
                from dcf_engine.orchestrator import ValuationReport
                return ValuationReport(
                    ticker=ticker,
                    success=False,
                    is_banking=False,
                    financial_group="?",
                    periods_fetched=0,
                    items_mapped=0,
                    lifecycle=None,
                    dcf_executed=False,
                    model_used="error",
                    currency_data="?",
                    currency_dcf="?",
                    equity_value_usd=None,
                    equity_value_tl=None,
                    shares_outstanding=None,
                    value_per_share_usd=None,
                    value_per_share_tl=None,
                    market_price_tl=price,
                    upside_pct=None,
                    damodaran_verdict="ERROR",
                    wacc=None,
                    normalized_op_margin=None,
                    errors=[f"Exception: {type(e).__name__}: {e}"],
                )

    tasks = [analyze_with_semaphore(t) for t in tickers]
    reports = await asyncio.gather(*tasks)
    return reports


# ============================================================================
# Ranking
# ============================================================================

def rank_by_upside(
    reports: List[ValuationReport],
) -> List[ValuationReport]:
    """En yüksek upside (en ucuz) → en düşük (en pahalı)."""
    successful = [r for r in reports if r.success and r.upside_pct is not None]
    failed = [r for r in reports if not (r.success and r.upside_pct is not None)]

    successful.sort(key=lambda r: r.upside_pct, reverse=True)
    return successful + failed


# ============================================================================
# Output Writers
# ============================================================================

def write_csv(
    reports: List[ValuationReport],
    output_path: Path,
) -> None:
    """CSV output."""
    fieldnames = [
        "ticker", "success", "is_banking", "model_used",
        "lifecycle_stage", "lifecycle_sub",
        "value_per_share_tl", "market_price_tl", "upside_pct",
        "damodaran_verdict",
        "equity_value_tl", "shares_outstanding",
        "wacc", "normalized_margin",
        "periods_fetched", "items_mapped",
        "errors",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in reports:
            row = {
                "ticker": r.ticker,
                "success": r.success,
                "is_banking": r.is_banking,
                "model_used": r.model_used,
                "lifecycle_stage": r.lifecycle.stage.value if r.lifecycle else "",
                "lifecycle_sub": ",".join([s.value for s in r.lifecycle.sub_classifications]) if r.lifecycle else "",
                "value_per_share_tl": f"{r.value_per_share_tl:.2f}" if r.value_per_share_tl else "",
                "market_price_tl": f"{r.market_price_tl:.2f}" if r.market_price_tl else "",
                "upside_pct": f"{r.upside_pct:.2f}" if r.upside_pct is not None else "",
                "damodaran_verdict": r.damodaran_verdict,
                "equity_value_tl": f"{r.equity_value_tl/1_000_000_000:.2f}B" if r.equity_value_tl else "",
                "shares_outstanding": r.shares_outstanding or "",
                "wacc": f"{r.wacc*100:.2f}%" if r.wacc else "",
                "normalized_margin": f"{r.normalized_op_margin*100:.2f}%" if r.normalized_op_margin else "",
                "periods_fetched": r.periods_fetched,
                "items_mapped": r.items_mapped,
                "errors": " | ".join(r.errors) if r.errors else "",
            }
            writer.writerow(row)


def write_json(
    reports: List[ValuationReport],
    output_path: Path,
) -> None:
    """JSON output (full diagnostic)."""

    def _serialize(r: ValuationReport) -> dict:
        return {
            "ticker": r.ticker,
            "success": r.success,
            "is_banking": r.is_banking,
            "financial_group": r.financial_group,
            "periods_fetched": r.periods_fetched,
            "items_mapped": r.items_mapped,
            "lifecycle": {
                "stage": r.lifecycle.stage.value,
                "sub_classifications": [s.value for s in r.lifecycle.sub_classifications],
                "confidence": r.lifecycle.confidence,
                "revenue_cagr_usd": r.lifecycle.revenue_cagr_usd,
                "avg_operating_margin": r.lifecycle.avg_operating_margin,
                "margin_stdev": r.lifecycle.margin_stdev,
                "margin_spread": r.lifecycle.margin_spread,
                "avg_reinvestment_rate": r.lifecycle.avg_reinvestment_rate,
                "earnings_consistency": r.lifecycle.earnings_consistency,
                "reasoning": r.lifecycle.reasoning,
            } if r.lifecycle else None,
            "dcf": {
                "executed": r.dcf_executed,
                "model_used": r.model_used,
                "equity_value_usd": r.equity_value_usd,
                "equity_value_tl": r.equity_value_tl,
                "value_per_share_usd": r.value_per_share_usd,
                "value_per_share_tl": r.value_per_share_tl,
                "wacc": r.wacc,
                "normalized_op_margin": r.normalized_op_margin,
            },
            "shares_outstanding": r.shares_outstanding,
            "market": {
                "price_tl": r.market_price_tl,
                "upside_pct": r.upside_pct,
                "verdict": r.damodaran_verdict,
            },
            "reasoning": r.reasoning,
            "errors": r.errors,
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "reports": [_serialize(r) for r in reports],
            },
            f,
            indent=2,
            default=str,
        )


# ============================================================================
# Summary
# ============================================================================

def summarize_batch(
    reports: List[ValuationReport],
    duration_seconds: float,
) -> BatchSummary:
    """Batch run özeti."""
    successful = sum(1 for r in reports if r.success)
    failed = sum(1 for r in reports if not r.success and not r.is_banking)
    skipped_banking = sum(1 for r in reports if r.is_banking)

    valid_upsides = [r.upside_pct for r in reports if r.success and r.upside_pct is not None]
    avg_upside = sum(valid_upsides) / len(valid_upsides) if valid_upsides else None

    deep_value = sum(1 for u in valid_upsides if u > 30)
    fair_value = sum(1 for u in valid_upsides if -10 <= u <= 10)
    overvalued = sum(1 for u in valid_upsides if u < -30)

    return BatchSummary(
        timestamp=datetime.now().isoformat(),
        total_tickers=len(reports),
        successful=successful,
        failed=failed,
        skipped_banking=skipped_banking,
        duration_seconds=duration_seconds,
        avg_upside_pct=avg_upside,
        deep_value_count=deep_value,
        fair_value_count=fair_value,
        overvalued_count=overvalued,
    )
