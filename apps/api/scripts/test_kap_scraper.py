#!/usr/bin/env python
"""TUPRS KAP scraper test."""
import sys
import asyncio
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_layer.kap_scraper import (
    fetch_company_page,
    find_html_clues,
    TUPRS_KAP_ID,
)


async def main():
    print("="*80)
    print("TUPRS KAP SCRAPER TEST — Faz 2.1.1")
    print("="*80)

    print(f"\nFetching TUPRS page (kap_id={TUPRS_KAP_ID})...")
    result = await fetch_company_page(TUPRS_KAP_ID)

    # ========================================================================
    # Result özet
    # ========================================================================
    print(f"\n[RESULT]")
    print(f"  URL: {result.url}")
    print(f"  HTTP Status: {result.http_status}")
    print(f"  HTML Size: {result.html_size:,} bytes")
    print(f"  Inline JSON Found: {result.inline_json_found}")

    if result.error:
        print(f"  ERROR: {result.error}")
        return

    if result.inline_json_found:
        print(f"  Pattern matched: {result.inline_json_pattern_matched}")
        print(f"\n[COMPANY META]")
        meta = result.company_meta
        print(f"  KAP ID:    {meta.kap_id}")
        print(f"  Full Name: {meta.full_name}")
        print(f"  Ticker:    {meta.ticker}")

        if meta.raw_inline_json:
            print(f"\n  Top-level JSON keys ({len(meta.raw_inline_json) if isinstance(meta.raw_inline_json, dict) else 'array'}):")
            if isinstance(meta.raw_inline_json, dict):
                for key in list(meta.raw_inline_json.keys())[:15]:
                    val = meta.raw_inline_json[key]
                    if isinstance(val, (dict, list)):
                        print(f"    {key}: <{type(val).__name__}, len={len(val)}>")
                    else:
                        val_str = str(val)[:80]
                        print(f"    {key}: {val_str}")
    else:
        # Inline JSON bulunamadı — clue'lara bakalım
        print(f"\n  ⚠ Inline JSON pattern eşleşmedi. HTML clues taranıyor...")

        clues = find_html_clues(result.raw_html_first_2000_chars)

        print(f"\n[HTML CLUES — first 2000 chars from page]")

        if clues['script_tags_with_data']:
            print(f"\n  Script tags with potential data ({len(clues['script_tags_with_data'])}):")
            for i, script in enumerate(clues['script_tags_with_data'][:3]):
                print(f"\n    Script {i+1}:")
                print(f"      {script[:300]}")

        if clues['meta_tags']:
            print(f"\n  Meta tags ({len(clues['meta_tags'])}):")
            for meta in clues['meta_tags'][:5]:
                print(f"    {meta[:120]}")

        if clues['data_attributes']:
            print(f"\n  Data attributes ({len(clues['data_attributes'])}):")
            for attr in clues['data_attributes'][:5]:
                print(f"    {attr}")

    # First HTML preview
    print(f"\n[HTML PREVIEW — first 1500 chars]")
    print("-"*80)
    print(result.raw_html_first_2000_chars[:1500])
    print("-"*80)

    print(f"\n{'='*80}")
    print("TUPRS scraper test tamam.")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
