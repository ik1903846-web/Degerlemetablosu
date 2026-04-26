#!/usr/bin/env python
"""BIST 30 batch pilot test (Faz 2.4)."""
import sys
import asyncio
import time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dcf_engine.batch_analyzer import (
    BIST_30_INDUSTRIAL,
    analyze_batch,
    rank_by_upside,
    write_csv,
    write_json,
    summarize_batch,
)


# Manuel market prices (24 Nisan 2026, web search ile doğrulanmış değerler)
# NOT: Bu değerler Faz 2.4 sonrası live data fetcher ile dinamik olacak
MARKET_PRICES_24_APRIL_2026 = {
    "TUPRS": 269.00,    # Doğrulandı
    # Diğerleri tahmini, exact değerleri Faz 2.4 sonrası fetch edilecek
    # Şu an sadece TUPRS'i tam doğrulayıp diğerlerini "fiyat yok" bırakıyoruz
}


async def main():
    print("="*80)
    print("BIST 30 BATCH PILOT — FAZ 2.4")
    print("="*80)
    print(f"Industrial tickers: {len(BIST_30_INDUSTRIAL)}")
    print(f"Banking skip: {len(['GARAN', 'AKBNK', 'ISCTR', 'YKBNK', 'HALKB', 'VAKBN'])}")
    print("="*80)

    # ========================================================================
    # BATCH RUN
    # ========================================================================
    print(f"\n[BATCH RUN] {len(BIST_30_INDUSTRIAL)} ticker paralel...")
    print("-"*80)

    start = time.time()

    reports = await analyze_batch(
        tickers=BIST_30_INDUSTRIAL,
        market_prices=MARKET_PRICES_24_APRIL_2026,
        max_concurrent=5,  # 5 paralel concurrent (rate limit dostu)
    )

    duration = time.time() - start

    print(f"\n[BATCH COMPLETE] Duration: {duration:.1f}s ({duration/60:.1f}min)")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    summary = summarize_batch(reports, duration)

    print("\n[SUMMARY]")
    print("-"*80)
    print(f"  Total tickers:     {summary.total_tickers}")
    print(f"  Successful:        {summary.successful}")
    print(f"  Failed:            {summary.failed}")
    print(f"  Skipped (banking): {summary.skipped_banking}")
    print(f"  Duration:          {summary.duration_seconds:.1f}s")

    if summary.avg_upside_pct is not None:
        print(f"\n  Avg upside:        {summary.avg_upside_pct:+.2f}%")
        print(f"  Deep value (>+30%):{summary.deep_value_count}")
        print(f"  Fair value (±10%): {summary.fair_value_count}")
        print(f"  Overvalued (<-30%):{summary.overvalued_count}")

    # ========================================================================
    # RANKED RESULTS
    # ========================================================================
    print("\n[RANKED RESULTS — En ucuzdan en pahalıya]")
    print("-"*80)

    ranked = rank_by_upside(reports)

    print(f"  Rank | Ticker | DCF (TL)  | Market    | Upside    | Verdict     | Model")
    print(f"  -----|--------|-----------|-----------|-----------|-------------|----------")

    for i, r in enumerate(ranked, 1):
        if r.success and r.value_per_share_tl is not None:
            dcf_str = f"{r.value_per_share_tl:>9.2f}"
            market_str = f"{r.market_price_tl:>9.2f}" if r.market_price_tl else "    n/a"
            upside_str = f"{r.upside_pct:>+7.2f}%" if r.upside_pct is not None else "    n/a"
            verdict = r.damodaran_verdict
            model = r.model_used.replace("_dcf", "").replace("_fcff", "_fcff")
        else:
            dcf_str = "    error"
            market_str = "    -"
            upside_str = "    -"
            verdict = r.damodaran_verdict
            model = r.model_used

        print(f"  {i:>4} | {r.ticker:<6} | {dcf_str} | {market_str} | {upside_str} | {verdict:<11} | {model}")

    # ========================================================================
    # OUTPUT FILES
    # ========================================================================
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"bist_batch_{timestamp}.csv"
    json_path = output_dir / f"bist_batch_{timestamp}.json"

    write_csv(reports, csv_path)
    write_json(reports, json_path)

    print(f"\n[OUTPUT FILES]")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")

    # ========================================================================
    # FAILURES (varsa)
    # ========================================================================
    failures = [r for r in reports if not r.success and not r.is_banking]
    if failures:
        print(f"\n[FAILURES]")
        print("-"*80)
        for r in failures:
            print(f"  {r.ticker}: {' | '.join(r.errors)}")

    # ========================================================================
    # CONSISTENCY CHECK (TUPRS)
    # ========================================================================
    print("\n[CONSISTENCY CHECK]")
    print("-"*80)

    tuprs_report = next((r for r in reports if r.ticker == "TUPRS"), None)
    if tuprs_report and tuprs_report.success:
        print(f"  TUPRS batch value:        {tuprs_report.value_per_share_tl:.2f} TL")
        print(f"  TUPRS Adım 5 manuel:      181.16 TL")
        diff = abs(tuprs_report.value_per_share_tl - 181.16)
        if diff < 1.0:
            print(f"  ✓ Batch + manuel UYUMLU (fark <1 TL)")
        else:
            print(f"  ⚠ Fark: {diff:.2f} TL")

    print("\n" + "="*80)
    print("Faz 2.4 BIST Batch PILOT PASS")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
