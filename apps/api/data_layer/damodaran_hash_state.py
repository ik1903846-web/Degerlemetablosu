#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Damodaran Hash State Manager - Session 5.2
===========================================

Damodaran xlsx URL'lerinin gunluk HEAD check'i. ETag +
Last-Modified state dosyasinda tutulur. Hash degisti ->
trigger flag.

State dosyasi: apps/api/data/damodaran/_hash_state.json

Kullanim:
    state = HashState.load(STATE_PATH)
    result = state.check_url('ctryprem', URL)
    if result.changed:
        # downstream fetch + parse trigger
        ...
    state.save(STATE_PATH)

YASAK: fetch_damodaran.py v1 dokunulmaz. Standalone.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15.0
SCHEMA_VERSION = "1.0"


@dataclass
class CheckResult:
    """Tek URL HEAD check sonucu."""
    name: str
    url: str
    changed: bool
    reason: str  # first_check | etag_diff | lm_diff | size_diff | unchanged | error
    new_etag: Optional[str] = None
    new_last_modified: Optional[str] = None
    new_content_length: Optional[str] = None
    old_etag: Optional[str] = None
    old_last_modified: Optional[str] = None
    error: Optional[str] = None


@dataclass
class UrlState:
    """Bir URL'nin son durumu."""
    url: str
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    content_length: Optional[str] = None
    last_check_utc: Optional[str] = None
    last_changed_utc: Optional[str] = None
    check_count: int = 0
    change_count: int = 0


@dataclass
class HashState:
    """Tum URL'lerin state'i."""
    schema_version: str = SCHEMA_VERSION
    last_check_utc: Optional[str] = None
    urls: dict[str, UrlState] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "HashState":
        """State dosyasini yukle. Yoksa bos state dondur."""
        if not path.exists():
            logger.info(f"State yok, yeni baslangic: {path}")
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            urls = {
                name: UrlState(**ud)
                for name, ud in data.get("urls", {}).items()
            }
            return cls(
                schema_version=data.get("schema_version", SCHEMA_VERSION),
                last_check_utc=data.get("last_check_utc"),
                urls=urls,
            )
        except Exception as e:
            logger.error(f"State load fail {path}: {e}")
            return cls()

    def save(self, path: Path) -> None:
        """State dosyasini yaz."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "schema_version": self.schema_version,
            "last_check_utc": self.last_check_utc,
            "urls": {name: asdict(us) for name, us in self.urls.items()},
        }
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def check_url(self, name: str, url: str,
                  timeout: float = DEFAULT_TIMEOUT) -> CheckResult:
        """URL'i HEAD ile kontrol et, state ile karsilastir, update et."""
        now_utc = datetime.now(timezone.utc).isoformat()
        prev = self.urls.get(name)

        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                r = client.head(url)
                r.raise_for_status()
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            logger.error(f"HEAD fail {name} ({url}): {err}")
            return CheckResult(
                name=name, url=url, changed=False, reason="error",
                error=err,
                old_etag=prev.etag if prev else None,
                old_last_modified=prev.last_modified if prev else None,
            )

        new_etag = r.headers.get("etag")
        new_lm = r.headers.get("last-modified")
        new_cl = r.headers.get("content-length")

        # Karsilastirma
        if prev is None:
            reason = "first_check"
            changed = True
        elif prev.etag != new_etag and new_etag is not None:
            reason = "etag_diff"
            changed = True
        elif prev.last_modified != new_lm and new_lm is not None:
            reason = "lm_diff"
            changed = True
        elif prev.content_length != new_cl and new_cl is not None:
            reason = "size_diff"
            changed = True
        else:
            reason = "unchanged"
            changed = False

        # State update
        new_state = UrlState(
            url=url,
            etag=new_etag,
            last_modified=new_lm,
            content_length=new_cl,
            last_check_utc=now_utc,
            last_changed_utc=(
                now_utc if changed
                else (prev.last_changed_utc if prev else now_utc)
            ),
            check_count=(prev.check_count if prev else 0) + 1,
            change_count=(prev.change_count if prev else 0) + (1 if changed else 0),
        )
        self.urls[name] = new_state
        self.last_check_utc = now_utc

        return CheckResult(
            name=name, url=url, changed=changed, reason=reason,
            new_etag=new_etag, new_last_modified=new_lm,
            new_content_length=new_cl,
            old_etag=prev.etag if prev else None,
            old_last_modified=prev.last_modified if prev else None,
        )

    def check_all(self, urls: dict[str, str]) -> dict[str, CheckResult]:
        """Tum URL'leri sirayla kontrol et."""
        results = {}
        for name, url in urls.items():
            results[name] = self.check_url(name, url)
        return results


# ────────────────────────────────────────────────────────────────────
# Standalone smoke test
# ────────────────────────────────────────────────────────────────────

DAMODARAN_URLS = {
    "ctryprem": "https://pages.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx",
    "ERPbymonth": "https://pages.stern.nyu.edu/~adamodar/pc/implprem/ERPbymonth.xlsx",
    "betaemerg": "https://pages.stern.nyu.edu/~adamodar/pc/datasets/betaemerg.xls",
}


def _smoke_test() -> int:
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    repo_root = Path(__file__).resolve().parents[3]
    state_path = (
        repo_root / "apps" / "api" / "data" / "damodaran" / "_hash_state.json"
    )

    print("=" * 60)
    print("Damodaran Hash State - Smoke Test")
    print("=" * 60)
    print(f"State file: {state_path}")
    print(f"State exists: {state_path.exists()}")
    print()

    # 1. Yukle (varsa)
    state = HashState.load(state_path)
    print(f"Loaded state: {len(state.urls)} URL kayitli")
    print(f"Last check: {state.last_check_utc}")
    print()

    # 2. Tum URL'leri kontrol et
    print("Tum URL'leri kontrol ediliyor...")
    results = state.check_all(DAMODARAN_URLS)
    print()

    # 3. Sonuclari yazdir
    for name, r in results.items():
        print(f"[{name}]")
        print(f"  changed:           {r.changed}")
        print(f"  reason:            {r.reason}")
        if r.error:
            print(f"  error:             {r.error}")
        else:
            print(f"  new_etag:          {r.new_etag}")
            print(f"  new_last_modified: {r.new_last_modified}")
            print(f"  new_content_length:{r.new_content_length}")
            if r.old_etag:
                print(f"  old_etag:          {r.old_etag}")
                print(f"  old_last_modified: {r.old_last_modified}")
        print()

    # 4. Save
    state.save(state_path)
    print(f"State kaydedildi: {state_path}")
    print()

    # 5. Ozet
    changed_count = sum(1 for r in results.values() if r.changed)
    error_count = sum(1 for r in results.values() if r.reason == "error")

    print("=" * 60)
    print(f"Toplam URL: {len(results)}")
    print(f"  Changed:   {changed_count}")
    print(f"  Unchanged: {len(results) - changed_count - error_count}")
    print(f"  Error:     {error_count}")
    print("=" * 60)

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(_smoke_test())
