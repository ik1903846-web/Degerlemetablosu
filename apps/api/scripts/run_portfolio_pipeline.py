#!/usr/bin/env python
"""
End-to-end portfolio pipeline (Faz 3 ADIM 5).

Latest BIST batch JSON → Pentagon scoring → Sleeve assignment → Portfolio plan.
3 risk profile için CSV+JSON output (Konservatif/Dengeli/Agresif).

Usage:
    python scripts/run_portfolio_pipeline.py
"""

import sys
import json
import csv
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from portfolio.pentagon_scoring import score_from_json_dict
from portfolio.sleeve_assignment import assign_batch
from portfolio.portfolio_construction import (
    build_portfolio,
    format_portfolio_report,
)


PROFILES = ["konservatif", "dengeli", "agresif"]
DEFAULT_CAPITAL_TL = 1_000_000.0


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _outputs_dir() -> Path:
    return _project_root() / "apps" / "api" / "outputs"


def _latest_batch() -> Path:
    batches = sorted(_outputs_dir().glob("bist_batch_LIVE_*.json"))
    if not batches:
        raise FileNotFoundError("No bist_batch_LIVE_*.json found in outputs/")
    return batches[-1]


def _write_csv(plan, path: Path) -> None:
    """Plan'ı CSV olarak yaz (positions + cash row + metadata)."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["# Portfolio Plan", plan.risk_profile,
                          f"capital_tl={plan.total_capital_tl:.0f}"])
        writer.writerow([
            "ticker", "sleeve", "sub_category", "weight_pct",
            "composite", "capital_allocation_tl",
        ])
        for p in sorted(plan.positions, key=lambda x: -x.weight_pct):
            writer.writerow([
                p.ticker,
                p.sleeve,
                p.sub_category or "",
                f"{p.weight_pct:.2f}",
                f"{p.composite:.2f}",
                f"{p.capital_allocation_tl:.0f}",
            ])
        writer.writerow([
            "CASH", "cash", "reserve",
            f"{plan.cash_reserve_pct:.2f}",
            "",
            f"{plan.cash_reserve_tl:.0f}",
        ])


def _write_json(plan, path: Path) -> None:
    """Plan'ı full JSON olarak yaz."""
    plan_dict = {
        "risk_profile": plan.risk_profile,
        "total_capital_tl": plan.total_capital_tl,
        "target_allocations_pct": plan.target_allocations,
        "actual_allocations_pct": plan.actual_allocations,
        "positions": [
            {
                "ticker": p.ticker,
                "sleeve": p.sleeve,
                "sub_category": p.sub_category,
                "weight_pct": round(p.weight_pct, 4),
                "composite": round(p.composite, 2),
                "capital_allocation_tl": round(p.capital_allocation_tl, 2),
                "reasoning": p.reasoning,
            }
            for p in plan.positions
        ],
        "cash_reserve_pct": round(plan.cash_reserve_pct, 4),
        "cash_reserve_tl": round(plan.cash_reserve_tl, 2),
        "cash_reasons": plan.cash_reasons,
        "total_positions": plan.total_positions,
        "sleeve_breakdown": plan.sleeve_breakdown,
        "warnings": plan.warnings,
        "reasoning": plan.reasoning,
    }
    path.write_text(json.dumps(plan_dict, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    print("=" * 80)
    print("PORTFOLIO PIPELINE END-TO-END (Faz 3 ADIM 5)")
    print("=" * 80)

    # 1. Latest batch
    latest = _latest_batch()
    print(f"\nLatest batch: {latest.name}")

    data = json.loads(latest.read_text(encoding="utf-8"))
    reports = data.get("reports", [])
    print(f"Reports: {len(reports)} (successful: "
          f"{sum(1 for r in reports if r.get('success'))})")

    # 2. Pentagon + Sleeve
    scores = score_from_json_dict(data)
    assignments = assign_batch(reports, scores)
    print(f"Pentagon scored: {len(scores)}")
    print(f"Sleeve assigned: {len(assignments)}")

    # 3. 3 profile portfolio plans
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_paths: list[tuple[str, Path, Path]] = []

    for profile in PROFILES:
        print()
        plan = build_portfolio(assignments, profile, total_capital_tl=DEFAULT_CAPITAL_TL)
        print(format_portfolio_report(plan))

        csv_path = _outputs_dir() / f"portfolio_plan_{profile}_{timestamp}.csv"
        json_path = _outputs_dir() / f"portfolio_plan_{profile}_{timestamp}.json"
        _write_csv(plan, csv_path)
        _write_json(plan, json_path)
        output_paths.append((profile, csv_path, json_path))

    # 4. Output summary
    print("\n" + "=" * 80)
    print("OUTPUT FILES")
    print("=" * 80)
    for profile, csv_path, json_path in output_paths:
        print(f"\n  {profile.upper()}:")
        print(f"    CSV:  {csv_path}")
        print(f"    JSON: {json_path}")

    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
