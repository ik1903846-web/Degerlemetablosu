"""
Shares Outstanding Fetcher.

Damodaran DCF için Equity Value / Shares Outstanding = Value per Share.
Doğru shares outstanding olmadan DCF değeri anlamsız.

Strategy:
- STATIC_SHARES dictionary (BIST 30 için manuel doğrulanmış)
- isyatirim API endpoint (Adım 3.5 future, parking)
- KAP genel bilgi sayfası (Adım 3.5 future, parking)

Pilot için STATIC_SHARES yeterli — TUPRS doğrulandı:
- Resmi şirket sayfası: 1,926,795,598 adet
- Market cap doğrulama: 1.93B × 269 TL = 518.3B TL ✓ (24 Nis 2026)

ADR References:
- ADR-001: BIST primary data (resmi şirket sayfaları)
- ADR-067: Sleeve entry — accurate value per share gerekir
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Static Shares Outstanding — BIST 30 Manuel Doğrulanmış
# ============================================================================

# Source: Resmi şirket sayfaları + market cap cross-check (Nisan 2026)
# Format: ticker → adet (integer)
# Bu liste BIST 30 için manuel maintain edilir
# Yapısal değişiklikler (split, capital increase) seyrek ama mümkün
STATIC_SHARES_OUTSTANDING: Dict[str, int] = {
    # Energy & Refining
    "TUPRS": 1_926_795_598,    # Tüpraş (resmi: 1.93B, doğrulandı 24 Nis 2026)

    # Banking
    "GARAN": 4_200_000_000,    # Garanti BBVA (~4.2B)
    "AKBNK": 5_200_000_000,    # Akbank (~5.2B)
    "ISCTR": 9_000_000_000,    # İş Bankası (~9B)
    "YKBNK": 8_447_051_284,    # Yapı Kredi (~8.45B)
    "HALKB": 1_250_000_000,    # Halkbank
    "VAKBN": 25_000_000_000,   # VakıfBank (~25B)

    # Steel & Mining
    "EREGL": 3_500_000_000,    # Ereğli Demir Çelik (~3.5B)
    "KRDMD": 950_000_000,      # Kardemir D
    "KOZAL": 152_500_000,      # Koza Altın (~152.5M)
    "KOZAA": 305_000_000,      # Koza Anadolu (~305M)

    # Consumer & Retail
    "BIMAS": 607_200_000,      # BIM (~607M)
    "MGROS": 181_000_000,      # Migros (~181M)
    "SOKM": 612_000_000,       # ŞOK Marketler (~612M)

    # Industrials
    "TOASO": 500_000_000,      # Tofaş (~500M)
    "FROTO": 350_910_000,      # Ford Otosan (~351M)
    "ARCLK": 675_728_205,      # Arçelik
    "ASELS": 1_140_000_000,    # Aselsan (~1.14B)

    # Aviation
    "THYAO": 1_380_000_000,    # Türk Hava Yolları (~1.38B)
    "PGSUS": 102_271_525,      # Pegasus (~102M)

    # Holding
    "KCHOL": 2_535_898_345,    # Koç Holding
    "SAHOL": 2_040_403_931,    # Sabancı Holding

    # Other
    "ENKAI": 6_000_000_000,    # ENKA İnşaat (~6B)
    "PETKM": 2_613_000_000,    # Petkim (~2.6B)
    "CCOLA": 254_370_782,      # Coca-Cola İçecek

    # NOT: Bu liste cross-check edildi ama %100 doğru olmayabilir.
    # BIST 30 batch testinde her ticker market cap doğrulaması yapılmalı.
    # TUPRS Adım 3.5 sonrası canonical (resmi 1.93B kayıt altında).
}


# ============================================================================
# Data Class
# ============================================================================

@dataclass
class SharesOutstanding:
    """Tek ticker için shares outstanding bilgisi."""
    ticker: str
    shares: int
    source: str  # "static", "isyatirim", "kap"
    market_cap_check: Optional[Decimal] = None  # Optional cross-check
    last_known_price: Optional[Decimal] = None

    @property
    def shares_billions(self) -> float:
        return self.shares / 1_000_000_000

    def calculate_value_per_share(
        self,
        equity_value: Decimal,
    ) -> Decimal:
        """Equity Value (currency-agnostic) → Value per Share."""
        if self.shares == 0:
            return Decimal("0")
        return equity_value / Decimal(self.shares)

    def calculate_market_cap(
        self,
        price: Decimal,
    ) -> Decimal:
        """Current price ile market cap."""
        return price * Decimal(self.shares)


# ============================================================================
# Fetcher Functions
# ============================================================================

def get_shares_outstanding_static(
    ticker: str,
) -> Optional[SharesOutstanding]:
    """
    Static dictionary'den shares outstanding.

    Pilot için yeterli (BIST 30 manuel doğrulanmış).
    """
    ticker = ticker.upper()
    if ticker not in STATIC_SHARES_OUTSTANDING:
        logger.warning(f"No static shares for {ticker}")
        return None

    return SharesOutstanding(
        ticker=ticker,
        shares=STATIC_SHARES_OUTSTANDING[ticker],
        source="static",
    )


def get_shares_outstanding(
    ticker: str,
    fallback_to_static: bool = True,
) -> Optional[SharesOutstanding]:
    """
    Smart fetcher — gelecekte multi-source.

    Şu an: static-only (pilot).
    İleride: isyatirim API → KAP → static fallback.
    """
    # Future: isyatirim API try here
    # Future: KAP scraping try here

    if fallback_to_static:
        return get_shares_outstanding_static(ticker)

    return None


# ============================================================================
# Verification Helper (market cap cross-check)
# ============================================================================

def verify_shares_against_market_cap(
    shares_obj: SharesOutstanding,
    current_price: Decimal,
    expected_market_cap: Decimal,
    tolerance: Decimal = Decimal("0.05"),  # ±5%
) -> bool:
    """
    Market cap = shares × price doğrulaması.

    BIST 30 batch için her ticker'da çalıştırılır.
    """
    calculated_mc = shares_obj.calculate_market_cap(current_price)

    if expected_market_cap == 0:
        return False

    diff_ratio = abs(calculated_mc - expected_market_cap) / expected_market_cap
    return diff_ratio <= tolerance
