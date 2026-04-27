"""
BIST Ticker Renames (TMSF süreçleri sonrası).

Kasım 2025'te BIST resmi kod değişikliği:
- KOZAL → TRALT  (Türk Altın İşletmeleri A.Ş.)
- KOZAA → TRMET  (TR Anadolu Metal Madencilik İşletmeleri A.Ş.)
- IPEKE → TRENJ  (TR Doğal Enerji Kaynakları Araştırma ve Üretim A.Ş.)

Şirketler aktif borsada işlem görüyor, sadece ticker yenilenmiş
(TMSF kayyum süreci + FETÖ davası sonrası şirket isim değişiklikleri).

Future renames buraya eklenecek (M&A, rebrand, vb.).

ADR References:
- ADR-001: BIST primary data (XBRL via isyatirim)
- ADR-072: Ticker continuity (eski referanslar geçerli kalır)
"""

from typing import Dict, Optional


# ============================================================================
# Ticker Rename Mappings
# ============================================================================

TICKER_RENAMES: Dict[str, str] = {
    # Koza İpek Holding tickers (Kasım 2025 BIST resmi rename)
    "KOZAL": "TRALT",  # Koza Altın → Türk Altın
    "KOZAA": "TRMET",  # Koza Anadolu Madencilik → TR Anadolu Metal
    "IPEKE": "TRENJ",  # İpek Doğal Enerji → TR Doğal Enerji

    # Future renames buraya
}


# ============================================================================
# Public API
# ============================================================================

def resolve_current_ticker(ticker: str) -> str:
    """
    Eski ticker'ı yeni koda çevir (eğer rename varsa).

    Args:
        ticker: Original ticker (case-insensitive)

    Returns:
        Current ticker (uppercase)

    Examples:
        >>> resolve_current_ticker("KOZAL")
        'TRALT'
        >>> resolve_current_ticker("TUPRS")
        'TUPRS'
        >>> resolve_current_ticker("kozaa")
        'TRMET'
    """
    upper = ticker.upper()
    return TICKER_RENAMES.get(upper, upper)


def is_renamed(ticker: str) -> bool:
    """Ticker yeniden adlandırılmış mı kontrol et."""
    return ticker.upper() in TICKER_RENAMES


def get_old_ticker(new_ticker: str) -> Optional[str]:
    """Yeni ticker'dan eski koda map (reverse lookup)."""
    new_upper = new_ticker.upper()
    for old, new in TICKER_RENAMES.items():
        if new == new_upper:
            return old
    return None
