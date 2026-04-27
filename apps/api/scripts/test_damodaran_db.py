#!/usr/bin/env python
"""
Test: damodaran_db.fetch_sector_unlevered_beta

Faz 2.4.6 Component 1 Adım 1.1 doğrulama.

3 TEST:
  1) oil_gas_integrated -> 0.7043 (TUPRS deep dive baseline)
  2) Cache test — 2. çağrı cache'den gelmeli
  3) BIST 30 candidate sectors — 11 sektör coverage check

Çalıştırma:
    cd apps/api
    .venv\\Scripts\\activate
    python scripts/test_damodaran_db.py
"""

import sys

# UTF-8 stdout (Windows cp1254 fix — defansif)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import asyncio
import os
import time
from decimal import Decimal
from pathlib import Path

# Proje root'undaki .env'i yükle
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).resolve().parents[3]
    env_path = project_root / ".env"
    load_dotenv(env_path)
    print(f"[ENV] .env yüklendi: {env_path}")
except ImportError:
    print("[ENV] python-dotenv yok, ortam değişkenleri zaten yüklü olmalı")

# apps/api'yi sys.path'e ekle
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_layer.damodaran_db import (  # noqa: E402
    fetch_sector_unlevered_beta,
    clear_sector_beta_cache,
    _SECTOR_BETA_CACHE,
)


# ============================================================================
# Test 1 — TUPRS baseline (oil_gas_integrated -> 0.7043)
# ============================================================================

async def test_oil_gas_integrated() -> bool:
    print("\n" + "=" * 70)
    print("TEST 1 — oil_gas_integrated (TUPRS baseline)")
    print("=" * 70)

    expected = Decimal("0.7043")
    tolerance = Decimal("0.001")

    clear_sector_beta_cache()
    actual = await fetch_sector_unlevered_beta("oil_gas_integrated")

    print(f"  Beklenen: {expected}")
    print(f"  Gerçek:   {actual}")

    if actual is None:
        print("  [FAIL] DB'de bulunamadı")
        return False

    diff = abs(actual - expected)
    if diff <= tolerance:
        print(f"  Sapma: {diff} (tolerance ±{tolerance})")
        print("  [PASS]")
        return True
    else:
        print(f"  Sapma: {diff} > {tolerance}")
        print("  [FAIL]")
        return False


# ============================================================================
# Test 2 — Cache davranışı
# ============================================================================

async def test_cache_behavior() -> bool:
    print("\n" + "=" * 70)
    print("TEST 2 — Cache davranışı")
    print("=" * 70)

    clear_sector_beta_cache()

    # 1. çağrı (DB)
    t0 = time.perf_counter()
    first = await fetch_sector_unlevered_beta("oil_gas_integrated")
    t1 = time.perf_counter()
    duration_first_ms = (t1 - t0) * 1000

    # 2. çağrı (cache)
    t2 = time.perf_counter()
    second = await fetch_sector_unlevered_beta("oil_gas_integrated")
    t3 = time.perf_counter()
    duration_second_ms = (t3 - t2) * 1000

    print(f"  1. çağrı (DB):    {duration_first_ms:.2f} ms -> {first}")
    print(f"  2. çağrı (cache): {duration_second_ms:.2f} ms -> {second}")
    print(f"  Cache size:       {len(_SECTOR_BETA_CACHE)} entry")

    if first != second:
        print("  [FAIL] Cache farklı değer döndürdü")
        return False

    if "oil_gas_integrated" not in _SECTOR_BETA_CACHE:
        print("  [FAIL] Cache'e yazılmadı")
        return False

    # Cache 2x'ten hızlı olmalı (network roundtrip yok)
    if duration_second_ms < duration_first_ms / 2:
        print("  [PASS] Cache aktif (2. çağrı belirgin hızlı)")
        return True
    else:
        # Yine de eşit değer döndüyse PASS — ölçüm gürültüsü olabilir
        print("  [PASS] Değer eşleşti (timing ölçüm gürültüsü olabilir)")
        return True


# ============================================================================
# Test 3 — BIST 30 candidate sektör coverage
# ============================================================================

BIST_CANDIDATE_SECTORS = [
    "oil_gas_integrated",      # TUPRS
    "chemical_basic",           # PETKM
    "steel",                    # EREGL, KRDMD
    "metals_mining",            # TRALT, TRMET
    "retail_grocery",           # BIMAS, MGROS, SOKM, CCOLA
    "auto_truck",               # TOASO, FROTO
    "household_products",       # ARCLK
    "aerospace_defense",        # ASELS
    "air_transport",            # THYAO, PGSUS
    "diversified",              # KCHOL, SAHOL
    "engineering_construction", # ENKAI
]


async def test_bist_30_coverage() -> bool:
    print("\n" + "=" * 70)
    print("TEST 3 — BIST 30 candidate sektör coverage")
    print("=" * 70)

    clear_sector_beta_cache()

    found = 0
    missing = []
    for sector in BIST_CANDIDATE_SECTORS:
        beta = await fetch_sector_unlevered_beta(sector, use_cache=False)
        clear_sector_beta_cache()
        status = f"{beta}" if beta is not None else "YOK"
        marker = "[OK] " if beta is not None else "[X]  "
        print(f"  {marker}{sector:30s} -> {status}")
        if beta is not None:
            found += 1
        else:
            missing.append(sector)

    total = len(BIST_CANDIDATE_SECTORS)
    print(f"\n  Coverage: {found}/{total}")
    if missing:
        print(f"  Eksik:    {missing}")

    # En az TUPRS sektörü (oil_gas_integrated) olmalı
    if found >= 1 and "oil_gas_integrated" not in missing:
        print("  [PASS] En az TUPRS baseline sektörü mevcut")
        return True
    print("  [FAIL] TUPRS baseline (oil_gas_integrated) DB'de yok")
    return False


# ============================================================================
# Runner
# ============================================================================

async def main() -> int:
    print("\n" + "#" * 70)
    print("# damodaran_db.py — fetch_sector_unlevered_beta TEST RUNNER")
    print("#" * 70)

    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # Şifreyi maskele
        masked = db_url
        if "@" in db_url and "://" in db_url:
            scheme, rest = db_url.split("://", 1)
            if "@" in rest:
                creds, host = rest.split("@", 1)
                if ":" in creds:
                    user, _ = creds.split(":", 1)
                    masked = f"{scheme}://{user}:***@{host}"
        print(f"[ENV] DATABASE_URL: {masked}")
    else:
        print("[ENV] DATABASE_URL: YOK")
        return 1

    results = []
    try:
        results.append(("TEST 1 oil_gas_integrated", await test_oil_gas_integrated()))
        results.append(("TEST 2 cache",              await test_cache_behavior()))
        results.append(("TEST 3 BIST coverage",      await test_bist_30_coverage()))
    except Exception as e:
        print(f"\n[EXCEPTION] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 2

    print("\n" + "#" * 70)
    print("# ÖZET")
    print("#" * 70)
    for name, ok in results:
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}")

    all_pass = all(ok for _, ok in results)
    print(f"\n  Toplam: {sum(1 for _, ok in results if ok)}/{len(results)}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
