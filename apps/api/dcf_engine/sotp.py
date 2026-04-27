"""
SOTP (Sum of the Parts) Value Calculator.

Faz 2.5 ADIM 3 — Holdings için iştirak-bazlı toplam değer hesabı.

Akış:
  1. Listed children: dcf_lookups[ticker] × ownership (DCF available)
                       VEYA book_value × multiplier × ownership (fallback)
  2. Banking listed: book × P/B 1.5 × ownership (justified Damodaran)
  3. Non-listed: book × multiplier × ownership (conservative)
  4. Aggregate: listed + banking + non_listed = gross_value
  5. Pre-disconto: gross + holding_net_cash - minority_at_subs
  6. Net: pre_disconto × (1 - disconto_pct)

Damodaran disiplini:
  - Listed DCF lookup tercih edilir (Component 4 batch context)
  - Book fallback: BIST 30 dışı listed children için
  - Banking intrinsic > market (P/B 1.5 BIST historical median)
  - Non-listed conservative (book × 1.0)
  - Disconto %15 NAV target intrinsic
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

from data_layer.holdings_config import (
    HoldingChild,
    HoldingPortfolio,
    get_portfolio,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DataClasses
# ============================================================================

@dataclass
class SOTPChildContribution:
    """Tek iştirakin SOTP'a katkısı."""
    name: str
    type: str                                # listed/banking_listed/non_listed
    ticker: Optional[str]
    ownership_pct: float
    full_equity_value_usd: float             # 100% basis (DCF veya book × multiplier)
    contribution_usd: float                  # ownership × full
    source: str                              # "dcf_lookup" | "book_fallback" |
                                             # "banking_book_pb_15" | "non_listed_book" |
                                             # "missing"


@dataclass
class SOTPResult:
    """Holding için tam SOTP hesabı."""
    parent_ticker: str
    listed_contribution_usd: float
    banking_contribution_usd: float
    non_listed_contribution_usd: float
    gross_value_usd: float
    holding_net_cash_usd: float
    minority_adjustment_usd: float
    pre_disconto_value_usd: float
    disconto_pct: float
    net_value_usd: float
    children: List[SOTPChildContribution] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ============================================================================
# Per-Child Resolver
# ============================================================================

def _resolve_child_value(
    child: HoldingChild,
    dcf_lookups: Dict[str, float],
    warnings: List[str],
) -> Tuple[float, str]:
    """
    Bir iştirak için 100% basis full_equity_value_usd + source döndür.

    Listed children priority:
      1. dcf_lookups[ticker] varsa → use DCF (preferred)
      2. book_value_usd × multiplier (fallback)
      3. None → 0 contribution + warning

    Banking_listed: hep book × multiplier (P/B 1.5 intrinsic).
    Non-listed: book × multiplier (1.0 conservative).
    """
    if child.type == "listed":
        if child.ticker and child.ticker in dcf_lookups:
            return dcf_lookups[child.ticker], "dcf_lookup"
        if child.book_value_usd is not None:
            warnings.append(
                f"Listed child '{child.ticker or child.name}': "
                f"DCF lookup MISSING, book fallback "
                f"(${child.book_value_usd/1e9:.2f}B × {child.book_multiplier})"
            )
            return child.book_value_usd * child.book_multiplier, "book_fallback"
        warnings.append(
            f"Listed child '{child.ticker or child.name}': "
            f"NO VALUE (skipped, contribution=0)"
        )
        return 0.0, "missing"

    if child.type == "banking_listed":
        # Faz 6 ADIM 4: DDM result öncelikli (banking valuation correct methodology)
        # Fallback: book × P/B 1.5 (banking_data missing veya DDM fail)
        if child.ticker and child.ticker in dcf_lookups:
            ddm_value = dcf_lookups[child.ticker]
            warnings.append(
                f"Banking child '{child.ticker}': DDM result CONFIRMED "
                f"(${ddm_value/1e9:.2f}B from banking_ddm)"
            )
            return ddm_value, "banking_ddm_dcf"

        if child.book_value_usd is None:
            warnings.append(
                f"Banking child '{child.ticker}': "
                f"DDM lookup missing AND book value missing (skipped)"
            )
            return 0.0, "missing"
        if "PROVISIONAL" in child.notes:
            warnings.append(
                f"Banking child '{child.ticker}': "
                f"DDM lookup MISSING, PROVISIONAL book × P/B fallback "
                f"(${child.book_value_usd/1e9:.2f}B × P/B {child.book_multiplier})"
            )
        return child.book_value_usd * child.book_multiplier, "banking_book_pb_15_fallback"

    if child.type == "non_listed":
        if child.book_value_usd is None:
            warnings.append(
                f"Non-listed '{child.name}': book value missing (skipped)"
            )
            return 0.0, "missing"
        return child.book_value_usd * child.book_multiplier, "non_listed_book"

    warnings.append(f"Unknown child type '{child.type}' for {child.name}")
    return 0.0, "missing"


# ============================================================================
# Main SOTP Calculator
# ============================================================================

def calculate_sotp_value(
    parent_ticker: str,
    dcf_lookups: Dict[str, float],
    portfolio: Optional[HoldingPortfolio] = None,
    disconto_override: Optional[float] = None,
) -> Optional[SOTPResult]:
    """
    Holding için SOTP net value hesabı.

    Args:
        parent_ticker: KCHOL veya SAHOL (case-insensitive)
        dcf_lookups: ticker → equity_value_usd dict (Component 4 batch'ten)
        portfolio: Opsiyonel direct portfolio (default: holdings_config registry)
        disconto_override: Opsiyonel disconto_pct override (default: portfolio default %15)

    Returns:
        SOTPResult veya None (parent_ticker holding değilse)
    """
    if portfolio is None:
        portfolio = get_portfolio(parent_ticker)
    if portfolio is None:
        logger.warning(f"No portfolio config for '{parent_ticker}' (not a holding)")
        return None

    children: List[SOTPChildContribution] = []
    warnings: List[str] = []
    listed_total = 0.0
    banking_total = 0.0
    non_listed_total = 0.0

    for child in portfolio.children:
        full_value, source = _resolve_child_value(child, dcf_lookups, warnings)
        contribution = full_value * child.ownership_pct

        children.append(
            SOTPChildContribution(
                name=child.name,
                type=child.type,
                ticker=child.ticker,
                ownership_pct=child.ownership_pct,
                full_equity_value_usd=full_value,
                contribution_usd=contribution,
                source=source,
            )
        )

        if child.type == "listed":
            listed_total += contribution
        elif child.type == "banking_listed":
            banking_total += contribution
        elif child.type == "non_listed":
            non_listed_total += contribution

    gross_value = listed_total + banking_total + non_listed_total
    pre_disconto = (
        gross_value
        + portfolio.holding_net_cash_usd
        - portfolio.minority_at_subs_usd
    )

    disconto = disconto_override if disconto_override is not None else portfolio.holding_disconto_pct
    net_value = pre_disconto * (1 - disconto)

    return SOTPResult(
        parent_ticker=portfolio.parent_ticker,
        listed_contribution_usd=listed_total,
        banking_contribution_usd=banking_total,
        non_listed_contribution_usd=non_listed_total,
        gross_value_usd=gross_value,
        holding_net_cash_usd=portfolio.holding_net_cash_usd,
        minority_adjustment_usd=portfolio.minority_at_subs_usd,
        pre_disconto_value_usd=pre_disconto,
        disconto_pct=disconto,
        net_value_usd=net_value,
        children=children,
        warnings=warnings,
    )


# ============================================================================
# Diagnostic Helper
# ============================================================================

def format_sotp_breakdown(result: SOTPResult) -> str:
    """SOTPResult'ı insan-okur formata çevir (test/debug için)."""
    lines = []
    lines.append(f"SOTP — {result.parent_ticker}")
    lines.append(f"  Children breakdown:")
    for c in result.children:
        lines.append(
            f"    {c.type:<18s} {c.name[:35]:<35s} "
            f"{c.ownership_pct*100:>5.1f}% × ${c.full_equity_value_usd/1e9:>6.2f}B "
            f"= ${c.contribution_usd/1e9:>6.2f}B  [{c.source}]"
        )
    lines.append(f"  ----------------------------------------------------------------")
    lines.append(f"  Listed contribution:     ${result.listed_contribution_usd/1e9:>7.3f}B")
    lines.append(f"  Banking contribution:    ${result.banking_contribution_usd/1e9:>7.3f}B")
    lines.append(f"  Non-listed contribution: ${result.non_listed_contribution_usd/1e9:>7.3f}B")
    lines.append(f"  Gross value:             ${result.gross_value_usd/1e9:>7.3f}B")
    lines.append(f"  Net cash:               ${result.holding_net_cash_usd/1e9:>+7.3f}B")
    lines.append(f"  Minority adjustment:    ${-result.minority_adjustment_usd/1e9:>+7.3f}B")
    lines.append(f"  Pre-disconto value:      ${result.pre_disconto_value_usd/1e9:>7.3f}B")
    lines.append(f"  Disconto applied:        -{result.disconto_pct*100:.1f}%")
    lines.append(f"  Net value (intrinsic):   ${result.net_value_usd/1e9:>7.3f}B")
    if result.warnings:
        lines.append(f"  Warnings ({len(result.warnings)}):")
        for w in result.warnings:
            lines.append(f"    ⚠ {w}")
    return "\n".join(lines)
