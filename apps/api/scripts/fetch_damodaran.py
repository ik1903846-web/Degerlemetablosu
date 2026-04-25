#!/usr/bin/env python
"""
Damodaran fetcher v1 — ERPbymonth.xlsx
Faz 1.2 başlangıç (ADR-040b)

Manual run: python scripts/fetch_damodaran.py
"""
import asyncio
import hashlib
import os
import sys
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import asyncpg
import httpx
import pandas as pd
from dotenv import load_dotenv

# Local helpers
sys.path.insert(0, str(Path(__file__).parent))
from _db_url import clean_db_url_for_asyncpg

# Windows cp1252 fix — emoji ve UTF-8 chars için stdout/stderr UTF-8'e zorla
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")

DAMODARAN_ERP_URL = "https://pages.stern.nyu.edu/~adamodar/pc/implprem/ERPbymonth.xlsx"

# Sheet name fallback chain (Damodaran rename'lerine karşı koru)
SHEETS_TO_TRY = [
    "Historical ERP",            # current (Nisan 2026+)
    "Historical Imp Prem",       # eski ad
    "Historical Implied ERP",    # hipotetik
]

# ERP column priority (ADR-005a: "T12 adjusted payout" primary)
ERP_PRIORITY = [
    "ERP (T12 m with sustainable payout)",     # ★ SPEC PRIMARY
    "ERP (T12m)",                               # secondary
    "Implied ERP",                              # eski ad
]


def generate_cuid_like() -> str:
    """Prisma cuid format'ına benzer 25 char ID."""
    return "c" + uuid.uuid4().hex[:24]


async def fetch_erp_monthly() -> dict:
    """ERPbymonth.xlsx fetch + parse."""
    print(f"[FETCH] {DAMODARAN_ERP_URL}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(DAMODARAN_ERP_URL)
        response.raise_for_status()
        content = response.content

    print(f"[FETCH] OK — {len(content):,} bytes")

    checksum = hashlib.sha256(content).hexdigest()
    print(f"[CHECKSUM] {checksum[:16]}...")

    # Sheet name fallback chain
    df = None
    sheet_used = None
    for sheet_name in SHEETS_TO_TRY:
        try:
            df = pd.read_excel(BytesIO(content), sheet_name=sheet_name)
            sheet_used = sheet_name
            print(f"[SHEET] '{sheet_name}' bulundu")
            break
        except ValueError:
            print(f"[SHEET] '{sheet_name}' yok, sonraki dene")
            continue

    if df is None:
        # Tüm sheet adlarını listele, hata mesajı
        xl = pd.ExcelFile(BytesIO(content))
        print("[ERROR] Hiçbir bilinen sheet bulunamadı")
        print(f"[ERROR] Mevcut sheets: {xl.sheet_names}")
        sys.exit(1)

    print(f"[PARSE] Columns: {list(df.columns)}")
    print(f"[PARSE] Rows: {len(df)}")

    latest = df.iloc[-1]

    # month_col detection (mevcut logic)
    month_col = next(
        (c for c in df.columns if "month" in str(c).lower() or "date" in str(c).lower()),
        df.columns[0]
    )

    # ERP column priority chain
    erp_col = None
    for priority_col in ERP_PRIORITY:
        if priority_col in df.columns:
            erp_col = priority_col
            print(f"[ERP] Primary kolon bulundu: '{priority_col}'")
            break

    if erp_col is None:
        # Fallback: herhangi "ERP" içeren kolon
        erp_col = next((c for c in df.columns if "erp" in str(c).lower()), None)
        if erp_col:
            print(f"[ERP] Fallback kolon: '{erp_col}'")

    if erp_col is None:
        print(f"[ERROR] ERP kolonu bulunamadı: {list(df.columns)}")
        sys.exit(1)

    # Vintage hesapla
    month_value = latest[month_col]
    if isinstance(month_value, str):
        try:
            parsed = datetime.fromisoformat(month_value.replace("/", "-"))
            vintage = parsed.strftime("%Y-%m")
        except ValueError:
            vintage = month_value[:7]
    elif hasattr(month_value, "strftime"):
        vintage = month_value.strftime("%Y-%m")
    else:
        vintage = str(month_value)[:7]

    erp_value = float(latest[erp_col])

    # ÖNEMLI: Damodaran %4.67 değerini "0.0467" olarak mı, "4.67"
    # olarak mı yazıyor? Kontrol et:
    # Eğer 1'den büyükse muhtemelen yüzde (4.67), bizim için decimal lazım
    if erp_value > 1.0:
        print(f"[WARN] ERP > 1.0 ({erp_value}), yüzde formatı tespit edildi, /100")
        erp_value = erp_value / 100.0

    print(f"[DATA] Sheet: {sheet_used}")
    print(f"[DATA] ERP Column: {erp_col}")
    print(f"[DATA] Month: {month_value}")
    print(f"[DATA] Vintage: {vintage}")
    print(f"[DATA] ERP value: {erp_value:.6f} ({erp_value*100:.2f}%)")

    effective_from = datetime.strptime(vintage + "-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)

    return {
        "parameter": "sp500_implied_erp",
        "value": erp_value,
        "source": f"ERPbymonth.xlsx::{sheet_used}::{erp_col}",  # provenance
        "vintage": vintage,
        "effective_from": effective_from,
        "checksum": checksum,
    }


async def write_to_postgres(data: dict) -> None:
    """DamodaranParameter tablosuna kaydet (idempotent)."""
    db_url_raw = os.getenv("DATABASE_URL")
    if not db_url_raw:
        print("[ERROR] DATABASE_URL not set")
        sys.exit(1)

    db_url_clean = clean_db_url_for_asyncpg(db_url_raw)

    if db_url_clean != db_url_raw:
        print("[DB] URL temizlendi (Prisma params kaldırıldı)")

    print("[DB] Connecting...")
    conn = await asyncpg.connect(db_url_clean)

    try:
        # Existing check (parameter + vintage unique)
        existing = await conn.fetchval(
            'SELECT id FROM "DamodaranParameter" WHERE parameter = $1 AND vintage = $2',
            data["parameter"], data["vintage"]
        )

        if existing:
            print(f"[DB] {data['vintage']} {data['parameter']} mevcut (id={existing[:8]}...). Atlanıyor.")
            return

        # Insert
        new_id = generate_cuid_like()
        result = await conn.fetchrow(
            '''
            INSERT INTO "DamodaranParameter"
                (id, parameter, value, source, vintage, "effectiveFrom", checksum)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, parameter, value, vintage
            ''',
            new_id,
            data["parameter"],
            data["value"],
            data["source"],
            data["vintage"],
            data["effective_from"],
            data["checksum"]
        )

        print("[DB] INSERTED:")
        print(f"     id={result['id']}")
        print(f"     parameter={result['parameter']}")
        print(f"     value={result['value']}")
        print(f"     vintage={result['vintage']}")

    finally:
        await conn.close()


async def main():
    print("=" * 60)
    print("Damodaran Fetcher v1 — Faz 1.2")
    print(f"Başlangıç: {datetime.now().isoformat()}")
    print("=" * 60)

    try:
        data = await fetch_erp_monthly()
        await write_to_postgres(data)
        print("=" * 60)
        print("✅ Tamamlandı")
        print("=" * 60)
    except httpx.HTTPError as e:
        print(f"[ERROR] HTTP: {e}")
        sys.exit(1)
    except asyncpg.PostgresError as e:
        print(f"[ERROR] DB: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
