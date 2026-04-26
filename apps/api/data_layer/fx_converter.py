"""
TL → USD Historical FX Converter.

12-yıl TUPRS data hyperinflation noise (TFRS 29) içeriyor.
USD conversion ile gerçek through-the-cycle margin ortaya çıkar.

Strategy:
- Year-end USD/TL rates (Aralık ortalaması ya da 31 Aralık spot)
- Yahoo Finance USDTRY=X primary source (free, no API key)
- TCMB EVDS fallback (API key gerektirir)
- Cache: in-memory dict (year → rate)

Damodaran prensibi:
- Each year's TL value / Year-end USD/TL rate = USD value
- Inflation noise eliminated by FX adjustment
- Cross-year comparison meaningful

ADR References:
- ADR-002: USD-only valuation
- ADR-005: TR market data sources
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
import logging
import httpx
from datetime import datetime, date

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

YAHOO_FINANCE_URL = "https://query1.finance.yahoo.com/v7/finance/download/USDTRY=X"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}


# ============================================================================
# Static Year-End Rates (FALLBACK — bilinen tarihi kurlar)
# ============================================================================

# Year-end USD/TL rates (Aralık 31 spot kapanış, TCMB resmi)
# Source: TCMB historical data + cross-check Bloomberg
# Bu fallback olarak kullanılır eğer Yahoo fail olursa
STATIC_YEAR_END_RATES: Dict[int, Decimal] = {
    2013: Decimal("2.1343"),   # 31 Aralık 2013
    2014: Decimal("2.3189"),
    2015: Decimal("2.9189"),
    2016: Decimal("3.5192"),
    2017: Decimal("3.7916"),
    2018: Decimal("5.2609"),
    2019: Decimal("5.9402"),
    2020: Decimal("7.4359"),
    2021: Decimal("12.9775"),  # Currency crisis
    2022: Decimal("18.6983"),
    2023: Decimal("29.4382"),
    2024: Decimal("35.3739"),  # 31 Aralık 2024 (yaklaşık)
    2025: Decimal("39.5000"),  # placeholder, current bilinmiyorsa
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class FXRate:
    """Tek yıl için USD/TL rate."""
    year: int
    rate: Decimal  # Kaç TL = 1 USD (Aralık 31)
    source: str  # "static", "yahoo", "tcmb"

    def tl_to_usd(self, tl_amount: Decimal) -> Decimal:
        """TL → USD conversion."""
        if self.rate == 0:
            return Decimal("0")
        return tl_amount / self.rate


@dataclass
class FXRateSeries:
    """Multi-year FX rates collection."""
    rates: Dict[int, FXRate]  # year → FXRate

    def get_rate(self, year: int) -> Optional[FXRate]:
        return self.rates.get(year)

    def convert_series(
        self,
        years: List[int],
        tl_values: List[Optional[Decimal]],
    ) -> List[Optional[Decimal]]:
        """Year-aligned TL series → USD series."""
        result = []
        for year, tl_val in zip(years, tl_values):
            if tl_val is None:
                result.append(None)
                continue

            fx = self.get_rate(year)
            if fx is None:
                logger.warning(f"No FX rate for year {year}")
                result.append(None)
                continue

            result.append(fx.tl_to_usd(tl_val))
        return result


# ============================================================================
# Static Source (Pilot için — Yahoo'ya gerek olmadan)
# ============================================================================

def get_static_rates(years: List[int]) -> FXRateSeries:
    """
    Static fallback rates (built-in).

    Hızlı ve güvenilir. Pilot için bu yeterli.
    İleride Yahoo Finance veya TCMB EVDS ile dinamik fetch eklenir.
    """
    rates = {}
    for year in years:
        if year in STATIC_YEAR_END_RATES:
            rates[year] = FXRate(
                year=year,
                rate=STATIC_YEAR_END_RATES[year],
                source="static",
            )
        else:
            logger.warning(f"No static rate for year {year}")

    return FXRateSeries(rates=rates)


# ============================================================================
# Yahoo Finance Source (Future — şu an parking)
# ============================================================================

async def fetch_yahoo_year_end_rate(
    year: int,
    client: Optional[httpx.AsyncClient] = None,
) -> Optional[FXRate]:
    """
    Yahoo Finance USDTRY=X year-end rate.

    NOT: Yahoo CSV download endpoint sometimes requires session/crumb.
    Pilot için static_rates kullanıyoruz, bu fonksiyon ileride.
    """
    # Placeholder — Yahoo Finance integration parking
    # Pilot için get_static_rates kullan
    static = get_static_rates([year])
    return static.get_rate(year)


# ============================================================================
# Helper: Apply FX to Damodaran Inputs
# ============================================================================

def convert_inputs_to_usd(
    inputs,  # DamodaranDCFInputs
    fx_series: FXRateSeries,
):
    """
    DamodaranDCFInputs (TL) → DamodaranDCFInputs (USD).

    Returns new dataclass instance with USD values.
    Original TL inputs unchanged.
    """
    from dataclasses import replace

    # Period years (string → int)
    years = [int(p) for p in inputs.period_labels]

    # All financial series convert
    converted = replace(
        inputs,
        currency="USD",
        revenue=fx_series.convert_series(years, inputs.revenue),
        ebit=fx_series.convert_series(years, inputs.ebit),
        pretax_income=fx_series.convert_series(years, inputs.pretax_income),
        net_income=fx_series.convert_series(years, inputs.net_income),
        operating_cash_flow=fx_series.convert_series(years, inputs.operating_cash_flow),
        depreciation=fx_series.convert_series(years, inputs.depreciation),
        capex=fx_series.convert_series(years, inputs.capex),
        working_capital_change=fx_series.convert_series(years, inputs.working_capital_change),
        cash=fx_series.convert_series(years, inputs.cash),
        short_term_debt=fx_series.convert_series(years, inputs.short_term_debt),
        long_term_debt=fx_series.convert_series(years, inputs.long_term_debt),
        total_equity=fx_series.convert_series(years, inputs.total_equity),
        total_debt=fx_series.convert_series(years, inputs.total_debt),
        # Computed metrics (margin, tax rate) currency-agnostic
        # Recompute USD-bazlı
    )

    # Operating margin recompute (USD bazda da aynı, ratio değişmez)
    converted.operating_margin = inputs.operating_margin  # Ratio currency-agnostic
    converted.effective_tax_rate = inputs.effective_tax_rate  # Ratio currency-agnostic

    return converted
