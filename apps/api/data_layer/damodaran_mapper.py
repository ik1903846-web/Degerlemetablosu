"""
XBRL → Damodaran DCF Input Mapper.

isyatirim 147 XBRL kaleminden Damodaran DCF input'larını çıkartır.

Kalem mapping (Faz 2.1.1b discovery'den):
- Revenue:      Hasılat / 4BC + 4BD (yurtiçi + yurtdışı)
- EBIT:         3DF (FAALİYET KARI/ZARARI)
- Pre-tax:      3I (Sürdürülen Faaliyetler Vergi Öncesi Kar)
- Tax expense:  3IA (Vergi Geliri/Gideri)
- Net Income:   2OCF (Dönem Net Kar/Zararı)
- CapEx:        4CB serisi (Yatırım faaliyetleri)
- ΔWC:          4CAF (İşletme Sermayesi Değişimleri)
- ST Debt:      2AA (Kısa Vadeli Finansal Borçlar)
- LT Debt:      2BA (Uzun Vadeli Finansal Borçlar)
- Cash:         1AA (Nakit ve Benzerleri)
- Equity:       2N (Özkaynaklar TOPLAM)
- Depreciation: 4B (Amortisman Giderleri)
- Operating CF: 4C (İşletme Faaliyetlerinden Net Nakit)

Currency:
- Raw data TL'de (isyatirim native)
- USD conversion ayrı utility (henüz değil)
- Damodaran USD-only valuation kullanır ama mapping TL'de kalır

ADR References:
- ADR-001: BIST primary data (XBRL via isyatirim)
- ADR-006a: Industrial FCFF inputs
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Dict
import logging

from .isyatirim_scraper import FinancialStatements, FinancialItem

logger = logging.getLogger(__name__)


# ============================================================================
# Damodaran DCF Input Schema
# ============================================================================

@dataclass
class DamodaranDCFInputs:
    """
    Damodaran Industrial FCFF için tüm input'lar.

    4 dönem time series — En yeni dönem [0], en eski [3].
    """
    ticker: str
    currency: str  # "TL" raw isyatirim native
    period_labels: List[str]  # ["2024", "2023", "2022", "2021"]

    # Income Statement
    revenue: List[Optional[Decimal]]  # Net Satış (4BC + 4BD veya alternative)
    ebit: List[Optional[Decimal]]  # 3DF
    pretax_income: List[Optional[Decimal]]  # 3I
    net_income: List[Optional[Decimal]]  # 2OCF

    # Cash Flow Statement
    operating_cash_flow: List[Optional[Decimal]]  # 4C
    depreciation: List[Optional[Decimal]]  # 4B
    capex: List[Optional[Decimal]]  # Hesaplama (4CB serisi)
    working_capital_change: List[Optional[Decimal]]  # 4CAF

    # Balance Sheet
    cash: List[Optional[Decimal]]  # 1AA
    short_term_debt: List[Optional[Decimal]]  # 2AA
    long_term_debt: List[Optional[Decimal]]  # 2BA
    total_equity: List[Optional[Decimal]]  # 2N

    # Computed metrics
    total_debt: List[Optional[Decimal]]  # ST + LT
    effective_tax_rate: List[Optional[Decimal]]  # (Pretax - NI) / Pretax
    operating_margin: List[Optional[Decimal]]  # EBIT / Revenue

    # Diagnostic
    items_found: int  # Kaç kalem bulundu (ideal: 12+)
    items_missing: List[str]  # Bulunamayan kalem code'ları


# ============================================================================
# Item Code Constants (XBRL Türkiye)
# ============================================================================

# Income Statement
ITEM_REVENUE_DOMESTIC = "4BC"  # Yurtiçi Satışlar
ITEM_REVENUE_FOREIGN = "4BD"  # Yurtdışı Satışlar
ITEM_REVENUE_TOTAL_ALT = "3CB"  # Bazı şirketlerde toplam satış burada

ITEM_EBIT = "3DF"
ITEM_PRETAX_INCOME = "3I"
ITEM_NET_INCOME = "2OCF"

# Cash Flow
ITEM_OPERATING_CF = "4C"
ITEM_DEPRECIATION = "4B"
ITEM_WC_CHANGE = "4CAF"

# CapEx alternative codes (yatırım faaliyetlerinden farklı kalemler topla)
ITEM_CAPEX_CANDIDATES = [
    "4CBA", "4CBB", "4CBC", "4CBD", "4CBE",
    "4CC", "4CCA", "4CCB",
]

# Balance Sheet
ITEM_CASH = "1AA"
ITEM_ST_DEBT = "2AA"
ITEM_LT_DEBT = "2BA"
ITEM_TOTAL_EQUITY = "2N"


# ============================================================================
# Helper Functions
# ============================================================================

def _safe_add(*values: Optional[Decimal]) -> Optional[Decimal]:
    """None-safe Decimal sum."""
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    return sum(valid)


def _safe_div(num: Optional[Decimal], den: Optional[Decimal]) -> Optional[Decimal]:
    """None-safe division."""
    if num is None or den is None or den == 0:
        return None
    return num / den


def _get_value_series(
    statements: FinancialStatements,
    item_code: str,
) -> List[Optional[Decimal]]:
    """Tek kalemden 4 dönem değer çek."""
    item = statements.get_item(item_code)
    if item is None:
        return [None, None, None, None]
    return list(item.values)


def _aggregate_revenue(statements: FinancialStatements) -> List[Optional[Decimal]]:
    """
    Net satış toplam.

    Strateji 1: 4BC (yurtiçi) + 4BD (yurtdışı)
    Strateji 2: 3CB (toplam satış alternative)
    """
    domestic = _get_value_series(statements, ITEM_REVENUE_DOMESTIC)
    foreign = _get_value_series(statements, ITEM_REVENUE_FOREIGN)

    # Eğer ikisi de varsa toplam
    if any(v is not None for v in domestic) or any(v is not None for v in foreign):
        result = []
        for d, f in zip(domestic, foreign):
            total = _safe_add(d, f)
            result.append(total)
        if any(v is not None for v in result):
            return result

    # Fallback: 3CB
    fallback = _get_value_series(statements, ITEM_REVENUE_TOTAL_ALT)
    if any(v is not None for v in fallback):
        return fallback

    logger.warning(f"Revenue not found for {statements.ticker}")
    return [None, None, None, None]


def _aggregate_capex(statements: FinancialStatements) -> List[Optional[Decimal]]:
    """
    CapEx aggregate (yatırım faaliyetleri).

    Damodaran net CapEx ≈ -1 × (gross capex - asset sales)
    Basit yaklaşım: 4CB* serisi toplama (negatif değerleri pozitife çevir)
    """
    capex_values = [None, None, None, None]

    for code in ITEM_CAPEX_CANDIDATES:
        item = statements.get_item(code)
        if item is None:
            continue

        for i, val in enumerate(item.values):
            if val is None:
                continue
            # CapEx'in mutlak değerini topla
            abs_val = abs(val)
            if capex_values[i] is None:
                capex_values[i] = abs_val
            else:
                capex_values[i] += abs_val

    return capex_values


def _compute_total_debt(
    st_debt: List[Optional[Decimal]],
    lt_debt: List[Optional[Decimal]],
) -> List[Optional[Decimal]]:
    """ST + LT debt aggregate."""
    return [_safe_add(s, l) for s, l in zip(st_debt, lt_debt)]


def _compute_effective_tax_rate(
    pretax: List[Optional[Decimal]],
    net_income: List[Optional[Decimal]],
) -> List[Optional[Decimal]]:
    """
    Effective tax rate = (Pretax - NetIncome) / Pretax

    Note: Bu basit hesaplama, NOL veya deferred tax adjustments yok.
    """
    result = []
    for pt, ni in zip(pretax, net_income):
        if pt is None or ni is None or pt == 0:
            result.append(None)
        else:
            tax = pt - ni
            rate = _safe_div(tax, pt)
            result.append(rate)
    return result


def _compute_operating_margin(
    ebit: List[Optional[Decimal]],
    revenue: List[Optional[Decimal]],
) -> List[Optional[Decimal]]:
    """Operating Margin = EBIT / Revenue."""
    return [_safe_div(e, r) for e, r in zip(ebit, revenue)]


# ============================================================================
# Main Mapping Function
# ============================================================================

def map_to_damodaran_inputs(
    statements: FinancialStatements,
) -> DamodaranDCFInputs:
    """
    isyatirim FinancialStatements → Damodaran DCF Inputs.

    Eksik kalemler None olarak bırakılır (downstream model decide eder).
    """
    period_labels = [str(p['year']) for p in statements.periods]

    # Income Statement
    revenue = _aggregate_revenue(statements)
    ebit = _get_value_series(statements, ITEM_EBIT)
    pretax = _get_value_series(statements, ITEM_PRETAX_INCOME)
    net_income = _get_value_series(statements, ITEM_NET_INCOME)

    # Cash Flow
    operating_cf = _get_value_series(statements, ITEM_OPERATING_CF)
    depreciation = _get_value_series(statements, ITEM_DEPRECIATION)
    capex = _aggregate_capex(statements)
    wc_change = _get_value_series(statements, ITEM_WC_CHANGE)

    # Balance Sheet
    cash = _get_value_series(statements, ITEM_CASH)
    st_debt = _get_value_series(statements, ITEM_ST_DEBT)
    lt_debt = _get_value_series(statements, ITEM_LT_DEBT)
    total_equity = _get_value_series(statements, ITEM_TOTAL_EQUITY)

    # Computed
    total_debt = _compute_total_debt(st_debt, lt_debt)
    eff_tax_rate = _compute_effective_tax_rate(pretax, net_income)
    op_margin = _compute_operating_margin(ebit, revenue)

    # Diagnostic
    all_series = [
        ("Revenue", revenue),
        ("EBIT", ebit),
        ("PreTax", pretax),
        ("NetIncome", net_income),
        ("OperatingCF", operating_cf),
        ("Depreciation", depreciation),
        ("CapEx", capex),
        ("WCChange", wc_change),
        ("Cash", cash),
        ("STDebt", st_debt),
        ("LTDebt", lt_debt),
        ("Equity", total_equity),
    ]

    items_found = sum(1 for name, series in all_series if any(v is not None for v in series))
    items_missing = [name for name, series in all_series if all(v is None for v in series)]

    return DamodaranDCFInputs(
        ticker=statements.ticker,
        currency="TL",
        period_labels=period_labels,
        revenue=revenue,
        ebit=ebit,
        pretax_income=pretax,
        net_income=net_income,
        operating_cash_flow=operating_cf,
        depreciation=depreciation,
        capex=capex,
        working_capital_change=wc_change,
        cash=cash,
        short_term_debt=st_debt,
        long_term_debt=lt_debt,
        total_equity=total_equity,
        total_debt=total_debt,
        effective_tax_rate=eff_tax_rate,
        operating_margin=op_margin,
        items_found=items_found,
        items_missing=items_missing,
    )
