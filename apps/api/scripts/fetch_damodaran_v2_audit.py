#!/usr/bin/env python3
"""
Damodaran Audit Fetcher v2 — Faz B1 Adım 1
==========================================

Standalone, file-only fetcher. Production v1 fetcher
(apps/api/scripts/fetch_damodaran.py) ile parallel çalışır,
DOKUNMAZ.

Amaç:
  - 3 Damodaran resmi xlsx fetch
  - apps/api/data/damodaran/{date}/ folder'a kaydet
  - parameters.json türet (Türkiye + US + Mature ERP)
  - DB write YOK
  - .env credentials OPSİYONEL

Faz B1 Adım 1 — Audit Decision v4 §3:
  Risk: Sıfır (read-only fetch).
  Production config dokunulmaz.
  Anchor 187.10 INTACT.

Kaynak doğrulama:
  Damodaran ctryprem.html "Turkey (updated February 2026)" satırı:
    Ba3 | 3.06% | 4.66% | 8.89% | 25.00% | 2.85% | 8.56%

Kullanım:
  python fetch_damodaran_v2_audit.py
  python fetch_damodaran_v2_audit.py --date 2026-05-09
  python fetch_damodaran_v2_audit.py --output-dir custom/path/

Çıktı:
  apps/api/data/damodaran/{YYYY_MM_DD}/
    ├─ ctryprem.xlsx       (telif, .gitignore)
    ├─ ERPbymonth.xlsx     (telif, .gitignore)
    ├─ histimpl.xlsx       (telif, .gitignore)
    └─ parameters.json     (türetilmiş, commit'lenir)

Exit codes:
  0 — başarı, parameters.json üretildi
  1 — fetch hatası veya parse hatası (parameters.json üretilmez)
  2 — argüman hatası
"""

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ─────────────────────────────────────────────────────────────────
# KONFIGÜRASYON
# ─────────────────────────────────────────────────────────────────

DAMODARAN_URLS = {
    "ctryprem.xlsx": (
        "https://pages.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx"
    ),
    "ERPbymonth.xlsx": (
        "https://pages.stern.nyu.edu/~adamodar/pc/implprem/ERPbymonth.xlsx"
    ),
    "histimpl.xlsx": (
        "https://pages.stern.nyu.edu/~adamodar/pc/datasets/histimpl.xlsx"
    ),
}

# Default output: REPO_ROOT/apps/api/data/damodaran/{date}/
DEFAULT_OUTPUT_BASE = (
    Path(__file__).resolve().parent.parent / "data" / "damodaran"
)

# Damodaran resmi sayfasından (manuel doğrulama, Şubat 2026 update)
# Kaynak: pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html
# Bu değerler script ilk çalıştığında parameters.json'a yazılır.
# İleride xlsx parser eklenince otomatik çekilir.
KNOWN_PARAMS_2026_05_09 = {
    "fetch_date": "2026-05-09",
    "source_last_updated": "Turkey: 2026-02 (Damodaran resmi notu)",
    "turkey": {
        "rating": "Ba3",
        "default_spread": 0.0306,
        "crp": 0.0466,
        "total_erp_lambda1": 0.0889,
        "tax_rate": 0.25,
        "sovereign_cds": 0.0285,
        "erp_based_on_cds": 0.0856,
    },
    "us": {
        "rating": "Aa1",
        "default_spread": 0.0023,
        "crp": 0.0023,
        "total_erp": 0.0446,
    },
    "mature_erp": 0.0423,
    "rf_usd_estimate": 0.0395,
    "methodology": (
        "Riskfree rate USD = 10Y UST − US default spread; "
        "ERP for US = Implied S&P expected return − Rf USD; "
        "Mature ERP = ERP for US − US default spread"
    ),
    "source_urls": {
        "ctryprem": (
            "https://pages.stern.nyu.edu/~adamodar/"
            "New_Home_Page/datafile/ctryprem.html"
        ),
        "erp_paper_2026": (
            "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6361419"
        ),
    },
}

USER_AGENT = (
    "REELDEGER-v4-audit-fetcher/1.0 "
    "(https://github.com/ik1903846-web/Degerlemetablosu)"
)

TIMEOUT_SECONDS = 60

# ─────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("damodaran_v2_audit")


# ─────────────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────────────────────────

def fetch_url(url: str, dest: Path) -> tuple[int, str]:
    """
    Tek bir URL'yi indir, dest path'ine yaz.

    Returns:
        (byte_size, sha256_hex)

    Raises:
        URLError, HTTPError, OSError
    """
    log.info(f"Fetching: {url}")
    req = Request(url, headers={"User-Agent": USER_AGENT})

    with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
        content = response.read()

    dest.write_bytes(content)
    sha = hashlib.sha256(content).hexdigest()
    log.info(f"  → {dest.name} ({len(content):,} bytes, sha256={sha[:12]}…)")
    return len(content), sha


def write_parameters_json(
    output_dir: Path,
    fetch_results: dict,
) -> Path:
    """
    parameters.json üret. KNOWN_PARAMS_2026_05_09 baseline'ı +
    fetch metadata'sı ile birleşir.
    """
    params = dict(KNOWN_PARAMS_2026_05_09)  # shallow copy
    params["fetch_metadata"] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "files": fetch_results,
        "fetcher_version": "v2-audit-1.0",
        "fetcher_path": "apps/api/scripts/fetch_damodaran_v2_audit.py",
    }
    params["audit_context"] = {
        "phase": "Faz B1 Adım 1",
        "decision_doc": "docs/audit_decision_v4.md",
        "findings_doc": "docs/audit_findings_session4.md",
        "anchor_status": "INTACT (TUPRS 187.10 dokunulmadı)",
    }

    params_path = output_dir / "parameters.json"
    params_path.write_text(
        json.dumps(params, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    log.info(f"  → parameters.json yazıldı: {params_path}")
    return params_path


# ─────────────────────────────────────────────────────────────────
# ANA AKIŞ
# ─────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Damodaran audit fetcher v2 (Faz B1 Adım 1)"
    )
    parser.add_argument(
        "--date",
        default="2026-05-09",
        help="Tarih damgası (YYYY-MM-DD), default 2026-05-09",
    )
    parser.add_argument(
        "--output-base",
        type=Path,
        default=DEFAULT_OUTPUT_BASE,
        help=f"Çıktı klasörü base, default {DEFAULT_OUTPUT_BASE}",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help=(
            "Sadece parameters.json üret, xlsx fetch atla "
            "(network sorunlu durumlar için)"
        ),
    )
    args = parser.parse_args()

    # Tarih klasörünü hazırla (YYYY_MM_DD format)
    date_folder = args.date.replace("-", "_")
    output_dir = args.output_base / date_folder
    output_dir.mkdir(parents=True, exist_ok=True)
    log.info(f"Çıktı klasörü: {output_dir}")

    fetch_results = {}

    # XLSX dosyalarını fetch et
    if not args.skip_fetch:
        for filename, url in DAMODARAN_URLS.items():
            dest = output_dir / filename
            try:
                size, sha = fetch_url(url, dest)
                fetch_results[filename] = {
                    "url": url,
                    "size_bytes": size,
                    "sha256": sha,
                    "status": "success",
                }
            except (URLError, HTTPError, OSError) as e:
                log.error(f"  ✗ {filename} fetch hatası: {e}")
                fetch_results[filename] = {
                    "url": url,
                    "status": "failed",
                    "error": str(e),
                }
                # Kritik: en az bir fetch başarılı olmalı
                # Ama tek fetch fail olsa da parameters.json üretilebilir
                # (KNOWN_PARAMS sabitleri Damodaran resmi sayfasından)
    else:
        log.info("--skip-fetch verildi, xlsx indirme atlandı")
        for filename, url in DAMODARAN_URLS.items():
            fetch_results[filename] = {
                "url": url,
                "status": "skipped",
            }

    # Hata sayısını kontrol et
    failed = [
        f for f, r in fetch_results.items()
        if r.get("status") == "failed"
    ]
    if failed and not args.skip_fetch:
        log.warning(
            f"{len(failed)}/{len(DAMODARAN_URLS)} dosya fetch edilemedi: "
            f"{', '.join(failed)}"
        )
        if len(failed) == len(DAMODARAN_URLS):
            log.error(
                "Tüm fetch'ler başarısız. parameters.json üretilmiyor."
            )
            return 1

    # parameters.json yaz
    try:
        write_parameters_json(output_dir, fetch_results)
    except OSError as e:
        log.error(f"parameters.json yazılamadı: {e}")
        return 1

    log.info("─" * 60)
    log.info("✓ Faz B1 Adım 1 TAMAMLANDI")
    log.info(f"  Çıktı: {output_dir}")
    log.info(f"  Başarılı fetch: "
             f"{sum(1 for r in fetch_results.values() if r.get('status') == 'success')}"
             f"/{len(DAMODARAN_URLS)}")
    log.info("  Sıradaki: parameters.json'u user'a göster, Adım 2 onayı bekle")
    log.info("─" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
