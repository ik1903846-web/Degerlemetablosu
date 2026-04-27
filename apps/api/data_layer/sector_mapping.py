"""
BIST Ticker → Damodaran Sector Mapping.

Faz 2.4.6 Component 1 Adım 1.2 — Bottom-up beta integration.

Damodaran Industry Averages (Emerging Markets, 2026-01 vintage)
sektör isimleri DB'de doğrulanmış (94 sektör tam yüklü).

Mapping kararları (Faz 2.4.5 deep dive + Adım 1.1 dump probe):
- TRALT (gold pure-play) → precious_metals (NOT metals_and_mining)
- TRMET (diversified metals) → metals_and_mining (NOT precious)
- CCOLA (Coca-Cola İçecek) → beverage_soft (NOT retail, KRİTİK FIX)
- TUPRS (refining) → oil_gas_integrated (Damodaran'da Refining ayrı yok)

Holdings (KCHOL, SAHOL) → diversified (Damodaran sınıflama)

Future: SOTP holding model gelince override edilebilir.

ADR References:
- ADR-006d: 6-stage lifecycle
- ADR-008: Sector z-score normalization
- Faz 2.4.5: TUPRS deep dive methodology validation
"""

from typing import Optional


# ============================================================================
# BIST 30 Industrial → Damodaran Sector Mapping
# ============================================================================

TICKER_TO_DAMODARAN_SECTOR: dict[str, str] = {
    # Refining / Energy
    "TUPRS": "oil_gas_integrated",

    # Chemicals
    "PETKM": "chemical_basic",

    # Steel / Metals
    "EREGL": "steel",
    "KRDMD": "steel",

    # Mining (Koza grubu, Kasım 2025 ticker rename sonrası)
    "TRALT": "precious_metals",       # Türk Altın (eski KOZAL) - gold pure-play
    "TRMET": "metals_and_mining",     # TR Anadolu Metal (eski KOZAA) - diversified

    # Retail (single-segment 3C revenue pattern)
    "BIMAS": "retail_grocery_and_food",
    "MGROS": "retail_grocery_and_food",
    "SOKM":  "retail_grocery_and_food",

    # Beverage (CCOLA - Coca-Cola İçecek, NOT retail)
    "CCOLA": "beverage_soft",

    # Automotive
    "TOASO": "auto_and_truck",
    "FROTO": "auto_and_truck",

    # Consumer Durables
    "ARCLK": "household_products",

    # Aerospace / Defense
    "ASELS": "aerospace_defense",

    # Transportation (Aviation)
    "THYAO": "air_transport",
    "PGSUS": "air_transport",

    # Holdings (SOTP gelene kadar diversified)
    "KCHOL": "diversified",
    "SAHOL": "diversified",

    # Construction / Engineering
    "ENKAI": "engineering_construction",

    # Future renames buraya eklenecek
}


# ============================================================================
# Public API
# ============================================================================

def get_damodaran_sector(ticker: str) -> Optional[str]:
    """
    BIST ticker için Damodaran sector adı döndür.

    Args:
        ticker: BIST ticker (case-insensitive)

    Returns:
        Damodaran sector adı (DB'de query'lenebilir format)
        veya None mapping yoksa

    Examples:
        >>> get_damodaran_sector("TUPRS")
        'oil_gas_integrated'
        >>> get_damodaran_sector("ccola")
        'beverage_soft'
        >>> get_damodaran_sector("UNKNOWN")
        None
    """
    return TICKER_TO_DAMODARAN_SECTOR.get(ticker.upper())


def has_sector_mapping(ticker: str) -> bool:
    """Ticker için sector mapping var mı kontrol et."""
    return ticker.upper() in TICKER_TO_DAMODARAN_SECTOR


def get_all_mapped_tickers() -> list[str]:
    """Tüm mapped ticker listesini döndür."""
    return sorted(TICKER_TO_DAMODARAN_SECTOR.keys())


def get_unique_sectors() -> list[str]:
    """Mapping'deki unique sector listesini döndür."""
    return sorted(set(TICKER_TO_DAMODARAN_SECTOR.values()))
