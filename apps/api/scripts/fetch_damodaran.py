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

DAMODARAN_CTRYPREM_URL = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx"

# Country Risk için sheet/column fallback chains
CTRYPREM_SHEETS_TO_TRY = [
    "ERPs by country",          # current (ana zengin sheet)
    "Country Premiums",         # eski ad fallback
    "Regional breakdown",       # alternatif
]

# Türkiye için ülke kolonu adı (case-insensitive search)
TURKEY_NAMES = ["Turkey", "Türkiye", "Turkiye"]

# Damodaran ctryprem vintage (manual, yarıyıllık update)
# Yarın smart parser eklenir (Excel cell'den extract)
CTRYPREM_VINTAGE = "2025-12"

DAMODARAN_BETAS_URL = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/betaemerg.xls"

# Beta için sheet/column fallback chains
BETAS_SHEETS_TO_TRY = [
    "Industry Averages",
    "Industries",
    "Sector Averages",
]

# Vintage manual (Damodaran yıllık update, Date updated cell'inden parse)
# Yarın smart parser eklenir (Excel cell extract)
BETAS_VINTAGE = "2026-01"


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


async def fetch_country_risk() -> list[dict]:
    """
    ctryprem.xlsx'ten Türkiye 3 parametresi.

    Returns: list of dicts (3 parameter, ortak checksum + vintage)
    """
    print(f"[FETCH] {DAMODARAN_CTRYPREM_URL}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(DAMODARAN_CTRYPREM_URL)
        response.raise_for_status()
        content = response.content

    print(f"[FETCH] OK — {len(content):,} bytes")

    checksum = hashlib.sha256(content).hexdigest()
    print(f"[CHECKSUM] {checksum[:16]}...")

    # Sheet fallback chain
    df = None
    sheet_used = None
    for sheet_name in CTRYPREM_SHEETS_TO_TRY:
        try:
            df = pd.read_excel(BytesIO(content), sheet_name=sheet_name)
            sheet_used = sheet_name
            print(f"[SHEET] '{sheet_name}' bulundu")
            break
        except ValueError:
            print(f"[SHEET] '{sheet_name}' yok, sonraki dene")
            continue

    if df is None:
        xl = pd.ExcelFile(BytesIO(content))
        print("[ERROR] Hiçbir bilinen sheet bulunamadı")
        print(f"[ERROR] Mevcut: {xl.sheet_names}")
        sys.exit(1)

    print(f"[PARSE] Columns: {list(df.columns)}")
    print(f"[PARSE] Rows: {len(df)}")

    # Türkiye satırını ara (her kolonda)
    turkey_row = None
    turkey_country_col = None
    for col in df.columns:
        try:
            col_str = df[col].astype(str)
            for name in TURKEY_NAMES:
                mask = col_str.str.lower() == name.lower()
                if mask.any():
                    turkey_row = df[mask].iloc[0]
                    turkey_country_col = col
                    print(f"[TURKEY] '{name}' bulundu kolon '{col}'")
                    break
            if turkey_row is not None:
                break
        except Exception:
            continue

    if turkey_row is None:
        # Fallback: contains Turkey
        for col in df.columns:
            try:
                col_str = df[col].astype(str)
                mask = col_str.str.lower().str.contains("turkey|türkiye", na=False, regex=True)
                if mask.any():
                    turkey_row = df[mask].iloc[0]
                    turkey_country_col = col
                    print(f"[TURKEY] fuzzy match kolon '{col}'")
                    break
            except Exception:
                continue

    if turkey_row is None:
        print("[ERROR] Türkiye satırı bulunamadı")
        sys.exit(1)

    # Güvenlik: turkey_country_col mutlaka set edilmiş olmalı
    if turkey_country_col is None:
        turkey_country_col = df.columns[0]

    # Sütun adıyla erişim (iloc index yerine)
    # 'ERPs by country' sheet'inde kolonlar 'Unnamed: N' olabilir
    # Ama belirgin isimler de olabilir — fallback gerek

    def find_column(df, keywords: list[str], exclude=None) -> str | None:
        """Kolon adında keyword'leri arar. exclude'da olan kolonları atla."""
        exclude = exclude or set()
        for col in df.columns:
            if col in exclude:
                continue
            col_lower = str(col).lower()
            if all(kw.lower() in col_lower for kw in keywords):
                return col
        return None

    # Default Spread kolonu
    default_spread_col = (
        find_column(df, ["default", "spread"], exclude={turkey_country_col}) or
        find_column(df, ["adj", "spread"], exclude={turkey_country_col}) or
        df.columns[3]  # Fallback: 4. kolon (index 3)
    )

    # Country Risk Premium kolonu
    crp_col = (
        find_column(df, ["country", "risk", "premium"], exclude={turkey_country_col}) or
        find_column(df, ["country", "risk"], exclude={turkey_country_col}) or
        df.columns[5]  # Fallback: 6. kolon (index 5)
    )

    print(f"[COL] Default Spread: '{default_spread_col}'")
    print(f"[COL] CRP: '{crp_col}'")

    # Ek güvenlik: detection sonrası type check
    test_default = turkey_row[default_spread_col]
    test_crp = turkey_row[crp_col]

    if not isinstance(test_default, (int, float)):
        print(f"[WARN] '{default_spread_col}' numeric değil ({test_default}), fallback df.columns[3]")
        default_spread_col = df.columns[3]

    if not isinstance(test_crp, (int, float)):
        print(f"[WARN] '{crp_col}' numeric değil ({test_crp}), fallback df.columns[5]")
        crp_col = df.columns[5]

    default_spread = float(turkey_row[default_spread_col])
    crp = float(turkey_row[crp_col])

    # Yüzde formatı kontrolü (>1.0 ise /100)
    if default_spread > 1.0:
        default_spread = default_spread / 100.0
    if crp > 1.0:
        crp = crp / 100.0

    # Scaling factor: derived = CRP / DefaultSpread
    scaling_factor = crp / default_spread if default_spread > 0 else 0.0

    print(f"[DATA] Sheet: {sheet_used}")
    print(f"[DATA] Default Spread: {default_spread:.4f} ({default_spread*100:.2f}%)")
    print(f"[DATA] CRP Total: {crp:.4f} ({crp*100:.2f}%)")
    print(f"[DATA] Scaling Factor: {scaling_factor:.4f}")
    print(f"[DATA] Vintage: {CTRYPREM_VINTAGE}")

    # effectiveFrom: vintage ay başı UTC
    effective_from = datetime.strptime(CTRYPREM_VINTAGE + "-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)

    # 3 parametre listesi (ortak vintage + checksum + effective_from)
    return [
        {
            "parameter": "turkey_default_spread",
            "value": default_spread,
            "source": f"ctryprem.xlsx::{sheet_used}::{default_spread_col}",
            "vintage": CTRYPREM_VINTAGE,
            "effective_from": effective_from,
            "checksum": checksum,
        },
        {
            "parameter": "turkey_crp_total",
            "value": crp,
            "source": f"ctryprem.xlsx::{sheet_used}::{crp_col}",
            "vintage": CTRYPREM_VINTAGE,
            "effective_from": effective_from,
            "checksum": checksum,
        },
        {
            "parameter": "turkey_crp_scaling_factor",
            "value": scaling_factor,
            "source": "ctryprem.xlsx::derived::CRP_div_DefaultSpread",
            "vintage": CTRYPREM_VINTAGE,
            "effective_from": effective_from,
            "checksum": checksum,
        },
    ]


async def fetch_sector_betas() -> list[dict]:
    """
    betaemerg.xls'den ~95 sektör unlevered beta'sı.

    Returns: list of dicts (her sektör için bir parametre)
    """
    print(f"[FETCH] {DAMODARAN_BETAS_URL}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(DAMODARAN_BETAS_URL)
        response.raise_for_status()
        content = response.content

    print(f"[FETCH] OK — {len(content):,} bytes")

    checksum = hashlib.sha256(content).hexdigest()
    print(f"[CHECKSUM] {checksum[:16]}...")

    # Sheet fallback chain
    df = None
    sheet_used = None
    for sheet_name in BETAS_SHEETS_TO_TRY:
        try:
            # header=9 — Row 9 gerçek header (inspect2 tespit etti)
            df = pd.read_excel(
                BytesIO(content),
                sheet_name=sheet_name,
                header=9,
                engine='xlrd'
            )
            sheet_used = sheet_name
            print(f"[SHEET] '{sheet_name}' bulundu (header=Row 9)")
            break
        except ValueError:
            print(f"[SHEET] '{sheet_name}' yok, sonraki dene")
            continue

    if df is None:
        xl = pd.ExcelFile(BytesIO(content), engine='xlrd')
        print("[ERROR] Hiçbir bilinen sheet bulunamadı")
        print(f"[ERROR] Mevcut: {xl.sheet_names}")
        sys.exit(1)

    print(f"[PARSE] Total rows: {len(df)}")
    print(f"[PARSE] Columns: {list(df.columns)[:8]}...")

    # Industry Name kolon var mı doğrula
    if 'Industry Name' not in df.columns:
        # Fallback: ilk kolonu industry name olarak al
        first_col = df.columns[0]
        print(f"[WARN] 'Industry Name' yok, ilk kolon kullanılıyor: '{first_col}'")
        df = df.rename(columns={first_col: 'Industry Name'})

    # Unlevered beta kolonu bul
    beta_col = None
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if 'unlevered' in col_lower and 'beta' in col_lower and 'corrected' not in col_lower and 'cash' not in col_lower:
            beta_col = col
            break

    if beta_col is None:
        # Fallback: 'Unlevered beta' exact match
        for col in df.columns:
            if str(col).strip() == 'Unlevered beta':
                beta_col = col
                break

    if beta_col is None:
        # Last fallback: col[5] (inspect2 found)
        if len(df.columns) > 5:
            beta_col = df.columns[5]
            print(f"[WARN] Unlevered beta kolon bulunamadı, df.columns[5] fallback: '{beta_col}'")

    if beta_col is None:
        print(f"[ERROR] Unlevered beta kolonu bulunamadı: {list(df.columns)}")
        sys.exit(1)

    print(f"[COL] Unlevered beta: '{beta_col}'")

    # Boş satırları kaldır
    df = df.dropna(subset=['Industry Name'])

    # "Total Market" aggregate satırı kaldır
    df = df[~df['Industry Name'].astype(str).str.contains('Total Market', case=False, na=False)]

    print(f"[PARSE] Sektör sayısı: {len(df)}")

    # Vintage + effective_from
    effective_from = datetime.strptime(BETAS_VINTAGE + "-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)

    # Her sektör için parametre üret
    import re
    params = []
    skipped = 0

    for _, row in df.iterrows():
        sector_name = str(row['Industry Name']).strip()

        # Boş veya geçersiz isim atla
        if not sector_name or sector_name.lower() in ('nan', 'none', ''):
            skipped += 1
            continue

        # Beta değeri
        try:
            unlevered_beta = float(row[beta_col])
            if pd.isna(unlevered_beta):
                skipped += 1
                continue
        except (ValueError, TypeError):
            print(f"[SKIP] {sector_name}: beta değeri numeric değil ({row[beta_col]})")
            skipped += 1
            continue

        # Sektör adı normalize (slugify)
        normalized = (
            sector_name
            .lower()
            .replace('/', '_')
            .replace('&', 'and')
            .replace('(', '')
            .replace(')', '')
            .replace(',', '')
            .replace('.', '')
            .replace("'", '')
        )
        # Birden fazla space/underscore'u tek underscore'a indir
        normalized = re.sub(r'[\s_]+', '_', normalized).strip('_')

        params.append({
            "parameter": f"sector_unlevered_beta_{normalized}",
            "value": unlevered_beta,
            "source": f"betaemerg.xls::{sheet_used}::{beta_col}::{sector_name}",
            "vintage": BETAS_VINTAGE,
            "effective_from": effective_from,
            "checksum": checksum,
        })

    print(f"[DATA] {len(params)} sektör hazır, {skipped} atlandı")
    return params


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
    print("Damodaran Fetcher v2 — Faz 1.2")
    print(f"Başlangıç: {datetime.now().isoformat()}")
    print("=" * 60)

    try:
        # 1) S&P 500 Implied ERP (monthly)
        print("\n--- ERP Monthly ---")
        erp_data = await fetch_erp_monthly()
        await write_to_postgres(erp_data)

        # 2) Turkey Country Risk (3 parameters)
        print("\n--- Country Risk (Turkey) ---")
        cr_params = await fetch_country_risk()
        for param in cr_params:
            await write_to_postgres(param)

        # 3) Sector Betas (Emerging, ~95 sectors)
        print("\n--- Sector Betas (Emerging Markets) ---")
        beta_params = await fetch_sector_betas()
        inserted = 0
        for param in beta_params:
            try:
                await write_to_postgres(param)
                inserted += 1
            except Exception as e:
                print(f"[ERROR] {param['parameter']}: {e}")
                raise

        print(f"\n[SUMMARY] Sector betas: {len(beta_params)} attempt, {inserted} processed")

        print("=" * 60)
        print("✅ Tüm parametreler tamamlandı")
        print("=" * 60)

    except httpx.HTTPError as e:
        print(f"[ERROR] HTTP: {e}")
        sys.exit(1)
    except asyncpg.PostgresError as e:
        print(f"[ERROR] DB: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
