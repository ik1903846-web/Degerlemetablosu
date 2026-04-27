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
    capex: List[Optional[Decimal]]  # Raw aggregate (4CB serisi, deprecated)
    net_capex: List[Optional[Decimal]]  # Damodaran-aligned (Δ PP&E + Dep)
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
ITEM_REVENUE_NET_SALES = "3C"  # Single-segment Net Satışlar (BIMAS, TRALT pattern)
ITEM_REVENUE_TOTAL_ALT = "3CB"  # Bazı şirketlerde toplam satış burada (legacy)

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

# Fixed Assets (Net CapEx hesabı için)
ITEM_PPE = "1BG"  # Maddi Duran Varlıklar (Tangible Fixed Assets)
ITEM_INTANGIBLE = "1BH"  # Maddi Olmayan Duran Varlıklar (Intangible)


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
    """Tek kalemden N dönem değer çek (N = mevcut taxonomy period count)."""
    item = statements.get_item(item_code)
    if item is None:
        # Period count'u taxonomy'den dinamik al
        period_count = (
            len(statements.items[0].values)
            if statements.items
            else 4
        )
        return [None] * period_count
    return list(item.values)


def _aggregate_revenue(statements: FinancialStatements) -> List[Optional[Decimal]]:
    """
    Net satış toplam.

    Strateji 1: 4BC (yurtiçi) + 4BD (yurtdışı) — TUPRS multi-segment pattern
    Strateji 2: 3C (Net Satışlar tek kalem) — BIMAS single-segment pattern
    Strateji 3: 3CB (legacy fallback)
    """
    domestic = _get_value_series(statements, ITEM_REVENUE_DOMESTIC)
    foreign = _get_value_series(statements, ITEM_REVENUE_FOREIGN)

    # Strateji 1: Multi-segment (4BC + 4BD)
    # NOT: BIMAS gibi firmalarda bu kalemler tüm dönemlerde 0 dönüyor.
    # "any not None" yetersiz çünkü Decimal(0) None değil ama valid de değil.
    # Toplamın >0 olduğunu da kontrol et.
    if any(v is not None for v in domestic) or any(v is not None for v in foreign):
        result = []
        for d, f in zip(domestic, foreign):
            total = _safe_add(d, f)
            result.append(total)
        # Eğer toplam değerler hep 0 veya None ise multi-segment fail demektir
        non_zero = [v for v in result if v is not None and v != 0]
        if non_zero:
            return result

    # Strateji 2: Single-segment Net Satışlar (3C) ★ YENİ
    net_sales = _get_value_series(statements, ITEM_REVENUE_NET_SALES)
    non_zero = [v for v in net_sales if v is not None and v != 0]
    if non_zero:
        logger.info(f"Revenue from 3C (single-segment) for {statements.ticker}")
        return net_sales

    # Strateji 3: Legacy fallback (3CB)
    fallback = _get_value_series(statements, ITEM_REVENUE_TOTAL_ALT)
    non_zero = [v for v in fallback if v is not None and v != 0]
    if non_zero:
        logger.info(f"Revenue from 3CB (legacy) for {statements.ticker}")
        return fallback

    logger.warning(f"Revenue not found for {statements.ticker}")
    return _get_value_series(statements, "__not_existing__")  # period_count adaptive None list


def _aggregate_capex(statements: FinancialStatements) -> List[Optional[Decimal]]:
    """
    CapEx aggregate (yatırım faaliyetleri).

    Damodaran net CapEx ≈ -1 × (gross capex - asset sales)
    Basit yaklaşım: 4CB* serisi toplama (negatif değerleri pozitife çevir)

    Period count taxonomy'den dinamik (4-yıl, 12-yıl, vs. desteklenir).
    """
    # Period count'u taxonomy'den dinamik al
    period_count = (
        len(statements.items[0].values)
        if statements.items
        else 4
    )
    capex_values: List[Optional[Decimal]] = [None] * period_count

    for code in ITEM_CAPEX_CANDIDATES:
        item = statements.get_item(code)
        if item is None:
            continue

        for i, val in enumerate(item.values):
            if val is None:
                continue
            if i >= len(capex_values):
                # Defensive: item.values period_count'tan büyükse skip
                break
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


def _compute_net_capex(
    statements: FinancialStatements,
    depreciation: List[Optional[Decimal]],
) -> List[Optional[Decimal]]:
    """
    Damodaran-aligned Net CapEx formula.

    Net CapEx = Δ Net PP&E + Depreciation
              = (PP&E[t] + Intangible[t]) - (PP&E[t-1] + Intangible[t-1]) + Dep[t]

    Sebep:
    - PP&E hesabı bilanço net (depreciation çıkarılmış)
    - Yıllık değişim = Gross CapEx - Depreciation
    - Geri ekleyince: Δ Net PP&E + Depreciation = Gross CapEx

    Period sıralaması:
    - index 0 en yeni (latest year)
    - index N-1 en eski
    - Net CapEx[t] = Operating Assets[t] - Operating Assets[t+1] + Depreciation[t]

    Son yıl için (en eski period) Net CapEx hesaplanamaz (prior year yok).
    """
    ppe = _get_value_series(statements, ITEM_PPE)
    intangible = _get_value_series(statements, ITEM_INTANGIBLE)

    # Operating fixed assets (PP&E + Intangible)
    operating_assets = [_safe_add(p, i) for p, i in zip(ppe, intangible)]

    # Δ Operating Assets (year-over-year)
    delta_assets = []
    for i in range(len(operating_assets)):
        if i + 1 >= len(operating_assets):
            # Son yıl (en eski) için prior year yok
            delta_assets.append(None)
            continue

        current = operating_assets[i]
        prior = operating_assets[i + 1]

        if current is None or prior is None:
            delta_assets.append(None)
        else:
            delta_assets.append(current - prior)

    # Net CapEx = Δ Operating Assets + Depreciation
    net_capex = [_safe_add(d, dep) for d, dep in zip(delta_assets, depreciation)]
    return net_capex


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
    capex = _aggregate_capex(statements)  # Raw, deprecated
    net_capex = _compute_net_capex(statements, depreciation)  # Damodaran-aligned
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
        net_capex=net_capex,
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
