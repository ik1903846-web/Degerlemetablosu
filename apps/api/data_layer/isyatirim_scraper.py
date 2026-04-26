"""
isyatirim.com.tr Financial Statements Scraper.

Faz 2.1.1b discovery sonrası implement (91201f8 commit reference).

Endpoint:
  https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo

Single call = 4 dönem comparison + 4 finansal tablo (Bilanço/Gelir/Nakit/Özkaynak).

Defensive coding patterns:
- value1-4 STRING formatında (Decimal cast)
- itemDescEng bazen null ((value or '') pattern)
- Negatif sayılar string '-prefix' ile

ADR References:
- ADR-001: BIST primary data source
- ADR-002: USD only valuation (raw data TL'de tutulur)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict
import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

ISYATIRIM_BASE_URL = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,*/*",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

# Period codes
PERIOD_Q1 = 3   # Q1 (3 aylık)
PERIOD_H1 = 6   # H1 / Q2 (6 aylık)
PERIOD_9M = 9   # 9M / Q3 (9 aylık)
PERIOD_Y = 12   # Yıllık (12 aylık)

# Financial group codes
FG_INDUSTRIAL = "XI_29"  # Industrial firms (TUPRS, EREGL, TOASO, etc.)
FG_BANKING = "XI_30"     # Banking/insurance (test edilecek)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class FinancialItem:
    """Tek XBRL kalem (4 dönem değer)."""
    item_code: str  # "1A", "3DF", "4C", etc.
    desc_tr: str
    desc_eng: str
    values: List[Optional[Decimal]]  # [value1, value2, value3, value4]

    @property
    def latest_value(self) -> Optional[Decimal]:
        """En yeni dönem (value1)."""
        return self.values[0] if self.values else None

    @property
    def is_summary_row(self) -> bool:
        """Indented kalem mi (alt detay vs summary)."""
        return self.desc_tr.startswith(' ') or self.desc_tr.startswith('\t')


@dataclass
class FinancialStatements:
    """4 dönem comparison full dataset."""
    ticker: str
    financial_group: str
    periods: List[Dict[str, int]]  # [{year: 2024, period: 12}, ...]
    items: List[FinancialItem]
    raw_response: Optional[dict] = None  # Debug için

    def get_item(self, item_code: str) -> Optional[FinancialItem]:
        """itemCode ile kalem bul."""
        for item in self.items:
            if item.item_code == item_code:
                return item
        return None

    def get_items_by_prefix(self, prefix: str) -> List[FinancialItem]:
        """Prefix'le başlayan tüm kalemleri döndür."""
        return [item for item in self.items if item.item_code.startswith(prefix)]

    def total_items(self) -> int:
        return len(self.items)


# ============================================================================
# Helper Functions
# ============================================================================

def parse_value(value_str: Optional[str]) -> Optional[Decimal]:
    """
    String value'yu Decimal'a çevir.

    isyatirim formatı:
    - Pozitif: "242924444741"
    - Negatif: "-971686119075"
    - Boş/null: None veya ""
    """
    if value_str is None:
        return None

    value_str = str(value_str).strip()
    if not value_str:
        return None

    try:
        return Decimal(value_str)
    except (InvalidOperation, ValueError):
        logger.warning(f"Cannot parse value: {value_str!r}")
        return None


def safe_str(value, max_len: int = 200) -> str:
    """None-safe string conversion (Faz 2.1.1b defensive pattern)."""
    if value is None:
        return ''
    return str(value)[:max_len]


# ============================================================================
# Scraper Functions
# ============================================================================

def build_url(
    ticker: str,
    periods: List[Dict[str, int]],
    financial_group: str = FG_INDUSTRIAL,
    exchange: str = "NTL",
) -> str:
    """
    isyatirim MaliTablo URL'i oluştur.

    Args:
        ticker: BIST ticker (TUPRS, EREGL, vb.)
        periods: [{year: 2024, period: 12}, {year: 2023, period: 12}, ...]
                 Max 4 dönem
        financial_group: XI_29 (industrial), XI_30 (banking)
        exchange: NTL (BIST)

    Returns:
        Full URL string
    """
    if len(periods) > 4:
        raise ValueError(f"Max 4 periods, got {len(periods)}")
    if not periods:
        raise ValueError("At least 1 period required")

    params = [
        f"companyCode={ticker}",
        f"exchange={exchange}",
        f"financialGroup={financial_group}",
    ]

    for i, p in enumerate(periods, start=1):
        params.append(f"year{i}={p['year']}")
        params.append(f"period{i}={p['period']}")

    # Eksik dönemler için en son dönemi tekrarla (4 dönem zorunlu olabilir)
    last_period = periods[-1]
    for i in range(len(periods) + 1, 5):
        params.append(f"year{i}={last_period['year']}")
        params.append(f"period{i}={last_period['period']}")

    query = "&".join(params)
    return f"{ISYATIRIM_BASE_URL}/MaliTablo?{query}"


async def fetch_financial_statements(
    ticker: str,
    periods: List[Dict[str, int]],
    financial_group: str = FG_INDUSTRIAL,
    client: Optional[httpx.AsyncClient] = None,
    timeout: float = 30.0,
) -> FinancialStatements:
    """
    Tek HTTP call ile 4 dönem mali tablo çek.

    Args:
        ticker: BIST ticker
        periods: List of {year, period} dicts (max 4)
        financial_group: XI_29 default
        client: Optional httpx client (yeniden kullanım için)
        timeout: HTTP timeout (saniye)

    Returns:
        FinancialStatements

    Raises:
        httpx.HTTPError: Network errors
        ValueError: Invalid response
    """
    url = build_url(ticker, periods, financial_group)

    own_client = False
    if client is None:
        client = httpx.AsyncClient(
            follow_redirects=True,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
        )
        own_client = True

    try:
        logger.info(f"Fetching {ticker} financials...")
        r = await client.get(url)
        r.raise_for_status()

        data = r.json()

        if not data.get('ok'):
            error_desc = data.get('errorDescription') or 'unknown error'
            raise ValueError(f"isyatirim returned ok=False: {error_desc}")

        raw_items = data.get('value', [])
        if not raw_items:
            raise ValueError(f"No items in response for {ticker}")

        # Parse items
        parsed_items = []
        for raw_item in raw_items:
            values = []
            for i in range(1, 5):
                val_str = raw_item.get(f'value{i}')
                values.append(parse_value(val_str))

            item = FinancialItem(
                item_code=safe_str(raw_item.get('itemCode'), 20),
                desc_tr=safe_str(raw_item.get('itemDescTr'), 200),
                desc_eng=safe_str(raw_item.get('itemDescEng'), 200),
                values=values,
            )
            parsed_items.append(item)

        return FinancialStatements(
            ticker=ticker,
            financial_group=financial_group,
            periods=periods,
            items=parsed_items,
            raw_response=data,
        )

    finally:
        if own_client:
            await client.aclose()


# ============================================================================
# Convenience Functions
# ============================================================================

async def fetch_yearly(
    ticker: str,
    years: List[int],
    financial_group: str = FG_INDUSTRIAL,
) -> FinancialStatements:
    """
    Yıllık (period=12) data fetch.

    Example:
        >>> data = await fetch_yearly("TUPRS", [2024, 2023, 2022, 2021])
        >>> data.total_items()
        147
        >>> ebit = data.get_item("3DF")
        >>> ebit.latest_value
        Decimal('46741606105')
    """
    if len(years) > 4:
        raise ValueError(f"Max 4 years, got {len(years)}")

    periods = [{"year": y, "period": PERIOD_Y} for y in years]
    return await fetch_financial_statements(ticker, periods, financial_group)


async def fetch_yearly_extended(
    ticker: str,
    years: List[int],
    financial_group: str = FG_INDUSTRIAL,
    chunk_size: int = 4,
) -> FinancialStatements:
    """
    Multi-call paralel fetcher — 4+ yıl historical.

    isyatirim single call max 4 dönem destekler.
    Bu fonksiyon yılları 4'lü chunk'lara böler, paralel fetch yapar,
    sonuçları merge eder.

    Args:
        ticker: BIST ticker
        years: List of years (e.g. [2024, 2023, ..., 2013])
        financial_group: XI_29 (industrial), XI_30 (banking)
        chunk_size: Max yıl/call (default 4, isyatirim limit)

    Returns:
        FinancialStatements (merged 12-yıl)

    Example:
        >>> data = await fetch_yearly_extended("TUPRS", list(range(2024, 2012, -1)))
        >>> len(data.periods)
        12
        >>> ebit = data.get_item("3DF")
        >>> len(ebit.values)
        12
    """
    if not years:
        raise ValueError("Years list empty")

    # Chunk years into 4-yıl groups
    chunks = [years[i:i+chunk_size] for i in range(0, len(years), chunk_size)]

    # Paralel fetch (shared client)
    async with httpx.AsyncClient(
        follow_redirects=True,
        headers=DEFAULT_HEADERS,
        timeout=30.0,
    ) as client:
        tasks = [
            fetch_yearly(
                ticker=ticker,
                years=chunk,
                financial_group=financial_group,
            )
            for chunk in chunks
        ]
        results = await asyncio.gather(*tasks)

    # Merge: en yeni yıl önce gelir
    # Her FinancialStatements'in items aynı sırada (147 kalem)

    # Periods merge (chronological, en yeni önce)
    merged_periods = []
    for r in results:
        merged_periods.extend(r.periods)

    # Items merge: itemCode-bazlı consolidation
    # Strategy: ilk result'tan items listesi al (taxonomy aynı)
    # Her item için tüm result'lardan values'ları concatenate et

    base_items = results[0].items
    merged_items = []

    for base_item in base_items:
        item_code = base_item.item_code
        all_values = []

        # Her chunk'tan bu item_code'un values'larını topla
        for r in results:
            chunk_item = r.get_item(item_code)
            if chunk_item is None:
                # Bu chunk'ta item yok — None doldur
                all_values.extend([None] * len(r.periods))
            else:
                all_values.extend(chunk_item.values)

        merged_item = FinancialItem(
            item_code=item_code,
            desc_tr=base_item.desc_tr,
            desc_eng=base_item.desc_eng,
            values=all_values,
        )
        merged_items.append(merged_item)

    return FinancialStatements(
        ticker=ticker,
        financial_group=financial_group,
        periods=merged_periods,
        items=merged_items,
        raw_response=None,  # Multi-call, raw saklanmıyor
    )
