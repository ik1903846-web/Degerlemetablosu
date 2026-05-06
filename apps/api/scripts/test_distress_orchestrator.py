#!/usr/bin/env python
"""
Faz 7.1 ADIM 4 — Distress orchestrator smoke test.

Hedef: distress override'ın live pipeline'da çalıştığını doğrula.
  - KONTR (negative cyclical_dcf → BS override expected)
  - TUPRS (positive cyclical_dcf, distress YOK → unchanged anchor)
"""

import asyncio
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

# Proje root .env (DATABASE_URL — sector beta lookup)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from dcf_engine.orchestrator import analyze_ticker


async def smoke(ticker: str) -> None:
    print(f"\n{'='*70}")
    print(f"SMOKE — {ticker}")
    print('='*70)
    report = await analyze_ticker(ticker)
    print(f"  success={report.success}, dcf_executed={report.dcf_executed}")
    print(f"  model_used={report.model_used}")
    if report.equity_value_usd is not None:
        print(f"  equity_value_usd={report.equity_value_usd/1e6:,.1f}M")
    if report.value_per_share_tl is not None:
        print(f"  value_per_share_tl={report.value_per_share_tl:,.2f}")
    if report.upside_pct is not None:
        print(f"  upside_pct={report.upside_pct:+.1f}%")
    print(f"  reasoning tail:")
    for r in report.reasoning[-5:]:
        print(f"    - {r}")
    if report.errors:
        print(f"  errors:")
        for e in report.errors:
            print(f"    ! {e}")


async def main() -> None:
    await smoke("KONTR")  # distress expected
    await smoke("TUPRS")  # anchor — distress override NOT to fire


if __name__ == "__main__":
    asyncio.run(main())
