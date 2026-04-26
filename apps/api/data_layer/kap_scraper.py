"""
KAP (Kamuyu Aydınlatma Platformu) HTML scraper.

Faz 2.1 inspect bulguları:
- KAP public REST API YOK
- HTML sayfaları erişilebilir (bot blok yok)
- 924 KB COMPANY_LIST_PAGE inline JSON içeriyor (muhtemelen Nuxt/React SPA)
- TUPRS_PAGE 70 KB HTML — şirket data'sı embedded

Strateji:
1. HTML fetch
2. Inline JSON extract (regex: __INITIAL_STATE__, __NUXT__, vb.)
3. Şirket meta + disclosure list parse

ADR References:
- ADR-001: KAP XBRL primary data source
- ADR-040: Scraping User-Agent + Accept headers
"""

import re
import json
import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import httpx


# ============================================================================
# KAP Scraper Configuration
# ============================================================================

KAP_BASE_URL = "https://www.kap.org.tr"

# TUPRS company KAP ID (inspect'ten bulundu)
TUPRS_KAP_ID = "4028e4a040a47b840140b4140a4106f4"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

# Inline JSON pattern'leri (Nuxt.js, React, Vue popular framework'ler)
INLINE_JSON_PATTERNS = [
    # Nuxt.js
    r'window\.__NUXT__\s*=\s*({.*?});</script>',
    # React Server-Side Rendering
    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
    # Generic data attributes
    r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(.*?)</script>',
    # Custom KAP patterns (test edilecek)
    r'window\.companyData\s*=\s*({.*?});',
    r'var\s+sirketBilgileri\s*=\s*({.*?});',
]


# ============================================================================
# Result Dataclasses
# ============================================================================

@dataclass
class KAPCompanyMeta:
    """KAP şirket meta bilgileri."""
    kap_id: str
    ticker: Optional[str] = None
    full_name: Optional[str] = None
    sector: Optional[str] = None
    market_segment: Optional[str] = None  # Yıldız, Ana, vb.
    raw_inline_json: Optional[Dict[str, Any]] = None


@dataclass
class KAPScrapeResult:
    """Full KAP scrape result with raw HTML for debugging."""
    kap_id: str
    url: str
    http_status: int
    html_size: int
    inline_json_found: bool
    inline_json_pattern_matched: Optional[str]
    company_meta: Optional[KAPCompanyMeta]
    raw_html_first_2000_chars: str
    error: Optional[str] = None


# ============================================================================
# KAP Scraper Functions
# ============================================================================

async def fetch_company_page(
    kap_id: str,
    client: Optional[httpx.AsyncClient] = None,
) -> KAPScrapeResult:
    """
    KAP şirket sayfasını fetch et + inline JSON extract et.

    Args:
        kap_id: KAP company ID (örn TUPRS için "4028e4a040a47b840140b4140a4106f4")
        client: httpx client (None ise yeni oluşturulur)

    Returns:
        KAPScrapeResult — full breakdown
    """
    url = f"{KAP_BASE_URL}/tr/sirket-bilgileri/genel/{kap_id}"

    own_client = False
    if client is None:
        client = httpx.AsyncClient(
            follow_redirects=True,
            headers=DEFAULT_HEADERS,
            timeout=30.0,
        )
        own_client = True

    try:
        r = await client.get(url)
        html = r.text

        result = KAPScrapeResult(
            kap_id=kap_id,
            url=url,
            http_status=r.status_code,
            html_size=len(html),
            inline_json_found=False,
            inline_json_pattern_matched=None,
            company_meta=None,
            raw_html_first_2000_chars=html[:2000],
        )

        if r.status_code != 200:
            result.error = f"HTTP {r.status_code}"
            return result

        # Inline JSON extraction try
        for pattern in INLINE_JSON_PATTERNS:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1)
                    data = json.loads(json_str)
                    result.inline_json_found = True
                    result.inline_json_pattern_matched = pattern[:60]

                    result.company_meta = KAPCompanyMeta(
                        kap_id=kap_id,
                        raw_inline_json=data,
                    )

                    # Try to extract common fields
                    # (Pattern'a göre struktur farklı olabilir, yarın detaya bakacağız)
                    if isinstance(data, dict):
                        result.company_meta.full_name = (
                            data.get('companyName')
                            or data.get('name')
                            or data.get('sirketAdi')
                            or data.get('title')
                        )
                        result.company_meta.ticker = (
                            data.get('ticker')
                            or data.get('symbol')
                            or data.get('borsaKodu')
                        )

                    break
                except json.JSONDecodeError as e:
                    # Pattern matched but JSON invalid — devam
                    continue

        return result

    except httpx.TimeoutException:
        return KAPScrapeResult(
            kap_id=kap_id,
            url=url,
            http_status=0,
            html_size=0,
            inline_json_found=False,
            inline_json_pattern_matched=None,
            company_meta=None,
            raw_html_first_2000_chars="",
            error="TIMEOUT",
        )
    except Exception as e:
        return KAPScrapeResult(
            kap_id=kap_id,
            url=url,
            http_status=0,
            html_size=0,
            inline_json_found=False,
            inline_json_pattern_matched=None,
            company_meta=None,
            raw_html_first_2000_chars="",
            error=f"{type(e).__name__}: {e}",
        )
    finally:
        if own_client:
            await client.aclose()


def find_html_clues(html: str) -> Dict[str, List[str]]:
    """
    HTML içinde data clues ara — inline JSON pattern bulamazsak fallback.

    Returns:
        Dict with potential data hints
    """
    clues = {
        'script_tags_with_data': [],
        'meta_tags': [],
        'data_attributes': [],
    }

    # <script> tags with src or data
    script_matches = re.findall(r'<script[^>]*>([^<]{50,500})</script>', html)
    for script in script_matches[:5]:
        if any(kw in script.lower() for kw in ['window.', 'var ', 'const ', 'data', 'state']):
            clues['script_tags_with_data'].append(script[:200])

    # Meta tags
    meta_matches = re.findall(r'<meta\s+([^>]+)>', html)
    clues['meta_tags'] = [m for m in meta_matches[:10] if 'content' in m.lower()]

    # data-* attributes (kısa)
    data_attr_matches = re.findall(r'data-([\w-]+)="([^"]{1,100})"', html)
    clues['data_attributes'] = [f'{k}={v[:50]}' for k, v in data_attr_matches[:10]]

    return clues
