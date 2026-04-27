"""
Damodaran DB Lookup Layer.

DamodaranParameter tablosundan sektör unlevered beta'larını çeker.
Faz 2.4.6 Component 1: Sector Beta Integration.

Strategy:
- asyncpg.connect() (no pool, single connect — Faz 1.1 pattern)
- In-memory cache (batch run optimization)
- Prisma DATABASE_URL inline temizleme (?schema=public strip)

Tablo: "DamodaranParameter" (Prisma camelCase)
Kolonlar: parameter, value, vintage
Naming: sector_unlevered_beta_{normalized}  (örn: sector_unlevered_beta_oil_gas_integrated)

Usage:
    beta = await fetch_sector_unlevered_beta("oil_gas_integrated")
    # → Decimal("0.7043")
"""

import os
import logging
from decimal import Decimal
from typing import Dict, Optional

import asyncpg

logger = logging.getLogger(__name__)


# ============================================================================
# In-Memory Cache (batch run optimization)
# ============================================================================

# Sektör adı → unlevered beta (Decimal | None)
# None = "DB'de yok" cached
_SECTOR_BETA_CACHE: Dict[str, Optional[Decimal]] = {}


def clear_sector_beta_cache() -> None:
    """Cache'i temizle (test izolasyonu için)."""
    _SECTOR_BETA_CACHE.clear()


# ============================================================================
# DB URL Helpers (inline — Faz 2.4.6 scope dışı refactor)
# ============================================================================

def _clean_db_url_for_asyncpg(db_url: str) -> str:
    """
    Prisma DATABASE_URL'i asyncpg-compatible hale getirir.

    asyncpg, Prisma'nın ?schema=public, ?pgbouncer=true gibi query params'ı
    tanımıyor. Inline minimal strip: ilk "?" sonrası kaldır.

    NOT: scripts/_db_url.py'de daha kapsamlı whitelist-based versiyon var.
    Burada inline tutuldu (Faz 2.4.6 refactor scope dışı).
    """
    if "?" in db_url:
        return db_url.split("?", 1)[0]
    return db_url


def _get_database_url() -> str:
    """Env'den DATABASE_URL oku."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL env var bulunamadı. "
            "Proje root'undaki .env'i yüklediğinden emin ol."
        )
    return _clean_db_url_for_asyncpg(db_url)


# ============================================================================
# Sector Beta Fetcher
# ============================================================================

async def fetch_sector_unlevered_beta(
    sector_name: str,
    use_cache: bool = True,
) -> Optional[Decimal]:
    """
    DamodaranParameter tablosundan sektör unlevered beta'yı çeker.

    Args:
        sector_name: Damodaran sektör adı (normalized, örn: "oil_gas_integrated").
                     Tabloda parameter = 'sector_unlevered_beta_' + sector_name.
        use_cache: True → in-memory cache kullan; False → her zaman DB'ye git.

    Returns:
        Decimal unlevered beta, veya None (DB'de yoksa).

    Naming convention:
        DamodaranParameter.parameter = "sector_unlevered_beta_oil_gas_integrated"
        Bu fonksiyon "oil_gas_integrated" alır, prefix'i ekler.

    Raises:
        RuntimeError: DATABASE_URL env yok.
    """
    sector_key = sector_name.strip().lower()

    # Cache hit
    if use_cache and sector_key in _SECTOR_BETA_CACHE:
        cached = _SECTOR_BETA_CACHE[sector_key]
        logger.debug(f"[CACHE] {sector_key} → {cached}")
        return cached

    # DB lookup
    db_url = _get_database_url()
    parameter_name = f"sector_unlevered_beta_{sector_key}"

    conn = await asyncpg.connect(db_url)
    try:
        row = await conn.fetchrow(
            '''
            SELECT value
            FROM "DamodaranParameter"
            WHERE parameter = $1
            ORDER BY vintage DESC
            LIMIT 1
            ''',
            parameter_name,
        )
    finally:
        await conn.close()

    if row is None:
        logger.warning(f"[DB] {parameter_name} bulunamadı (DB'de yok)")
        if use_cache:
            _SECTOR_BETA_CACHE[sector_key] = None
        return None

    # asyncpg Numeric → Decimal direkt döner
    value = row["value"]
    if not isinstance(value, Decimal):
        value = Decimal(str(value))

    logger.info(f"[DB] {parameter_name} → {value}")
    if use_cache:
        _SECTOR_BETA_CACHE[sector_key] = value

    return value
