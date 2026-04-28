"""
Portfolio Construction — Position Sizing + Risk Profile Allocation.

Faz 3 ADIM 4 — Sleeve assignments → PortfolioPlan.
Faz 4.2 — Cash policy refinement (Damodaran Lesson #8).

Damodaran ADR-015 (Position Sizing):
  1. Risk profile allocation (Konservatif 80/15/5, Dengeli 60/25/15, Agresif 40/35/25)
  2. Boş sleeve → AKTIF SLEEVE'lere overflow redistribution (Faz 4.2 yenilik)
     Mevcut universe'de Hızlı Büyüme boş → Core+Yüksek Kazanç'a kaydır
     (eski: cash'e atılırdı, %30+ underinvested oluşurdu)
  3. Composite-weighted distribution within sleeve:
     weight_i = (composite_i / sum(composite_in_sleeve)) × sleeve_allocation
  4. Concentration caps:
     - Max %12 single ticker (Faz 4.2: %10 → %12, hafif esneklik)
     - Min %2 single ticker (significant position only)
  5. Cash reserve (Faz 4.2 strict):
     - Min %2 (full investment principle)
     - Max %15 (eski %30 → %15, Damodaran Lesson #8 cash drag minimize)
     - Cap overflow + capacity overflow → cash (rare)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from portfolio.sleeve_assignment import (
    Sleeve,
    SleeveAssignment,
    get_risk_profile_allocations,
)


# ============================================================================
# Constants (ADR-015 + Faz 4.2 refinement — Damodaran Lesson #8)
# ============================================================================

MAX_SINGLE_TICKER_PCT = 12.0   # Faz 4.2: 10 → 12 (BIST 30 universe darlığı)
MIN_SINGLE_TICKER_PCT = 2.0
MIN_CASH_PCT = 2.0
MAX_CASH_PCT = 15.0            # Faz 4.2: 30 → 15 (cash drag minimize)


# ============================================================================
# DataClasses
# ============================================================================

@dataclass
class TickerPosition:
    """Tek ticker için portfolio pozisyonu."""
    ticker: str
    sleeve: str  # "core" | "hizli_buyume" | "yuksek_kazanc"
    sub_category: Optional[str]
    weight_pct: float            # 0-100 portföy ağırlığı
    composite: float
    capital_allocation_tl: float
    reasoning: List[str] = field(default_factory=list)


@dataclass
class PortfolioPlan:
    """Tam portfolio çıktısı."""
    risk_profile: str
    total_capital_tl: float

    # Sleeve breakdown
    target_allocations: Dict[str, float]   # {"core": 60.0, "hizli_buyume": 25.0, ...}
    actual_allocations: Dict[str, float]   # boş sleeve sonrası gerçekleşen

    # Positions
    positions: List[TickerPosition] = field(default_factory=list)

    # Cash
    cash_reserve_pct: float = 0.0
    cash_reserve_tl: float = 0.0
    cash_reasons: List[str] = field(default_factory=list)

    # Diagnostics
    total_positions: int = 0
    sleeve_breakdown: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    reasoning: List[str] = field(default_factory=list)


# ============================================================================
# Builder
# ============================================================================

def build_portfolio(
    assignments: List[SleeveAssignment],
    risk_profile: str = "dengeli",
    total_capital_tl: float = 1_000_000.0,
) -> PortfolioPlan:
    """
    Damodaran portfolio construction (ADR-015).

    Args:
        assignments: SleeveAssignment listesi (sleeve_assignment.assign_batch output)
        risk_profile: "konservatif" | "dengeli" | "agresif"
        total_capital_tl: Toplam yatırım sermayesi TL

    Returns:
        PortfolioPlan with positions, cash reserve, warnings.
    """
    # 1. Risk profile allocations
    target_alloc = get_risk_profile_allocations(risk_profile)
    target_alloc_pct = {k: v * 100.0 for k, v in target_alloc.items()}

    # 2. SKIP'leri filtrele
    investable = [a for a in assignments if a.sleeve != Sleeve.SKIP]

    # 3. Sleeve grouping
    sleeve_groups: Dict[str, List[SleeveAssignment]] = {
        "core":          [a for a in investable if a.sleeve == Sleeve.CORE],
        "hizli_buyume":  [a for a in investable if a.sleeve == Sleeve.HIZLI_BUYUME],
        "yuksek_kazanc": [a for a in investable if a.sleeve == Sleeve.YUKSEK_KAZANC],
    }

    actual_alloc_pct: Dict[str, float] = {}
    cash_reasons: List[str] = []
    warnings: List[str] = []
    reasoning: List[str] = []

    # 4. Boş sleeve detection + REDISTRIBUTION (Faz 4.2 yenilik)
    # Önce: boş sleeve target'ı cash'e dökerdi → %30+ cash drag
    # Yeni: aktif sleeve'lere capacity-pro-rata redistribute
    empty_target_pct = 0.0
    for sleeve_name, target_pct in target_alloc_pct.items():
        if not sleeve_groups[sleeve_name]:
            actual_alloc_pct[sleeve_name] = 0.0
            empty_target_pct += target_pct
            cash_reasons.append(
                f"Sleeve '{sleeve_name}' BOŞ ({target_pct:.0f}% target → "
                f"aktif sleeve'lere redistribute, Faz 4.2)"
            )
        else:
            actual_alloc_pct[sleeve_name] = target_pct

    # Redistribution: empty target'ları aktif sleeve'lere capacity-pro-rata kaydır
    # MIN_CASH_PCT buffer korunur (Damodaran ADR-015 minimal cash floor)
    if empty_target_pct > 0:
        active_sleeves = {
            name: actual_alloc_pct[name]
            for name in actual_alloc_pct
            if sleeve_groups[name]
        }
        if active_sleeves:
            # Capacity headroom: max kapasite (n_ticker × cap) - mevcut target
            capacity_headroom = {}
            for name in active_sleeves:
                max_cap = len(sleeve_groups[name]) * MAX_SINGLE_TICKER_PCT
                headroom = max(0.0, max_cap - actual_alloc_pct[name])
                capacity_headroom[name] = headroom

            total_headroom = sum(capacity_headroom.values())
            sum_active = sum(active_sleeves.values())
            # Cash buffer (MIN_CASH_PCT) korunur
            cash_reserved_max = max(0.0, 100.0 - MIN_CASH_PCT - sum_active)
            if total_headroom > 0:
                redistributable = min(empty_target_pct, total_headroom, cash_reserved_max)
                for name, headroom in capacity_headroom.items():
                    if headroom > 0:
                        share = (headroom / total_headroom) * redistributable
                        actual_alloc_pct[name] += share
                        reasoning.append(
                            f"↪ Redistribute → {name}: +{share:.1f}% "
                            f"(headroom {headroom:.1f}%)"
                        )
                if redistributable < empty_target_pct:
                    overflow = empty_target_pct - redistributable
                    cash_reasons.append(
                        f"Redistribution capacity overflow: +{overflow:.1f}% → cash"
                    )

    # 5. Position sizing within each non-empty sleeve
    positions: List[TickerPosition] = []
    for sleeve_name, group in sleeve_groups.items():
        if not group:
            continue

        sleeve_alloc = actual_alloc_pct[sleeve_name]
        total_composite = sum(a.composite for a in group)
        if total_composite <= 0:
            warnings.append(f"Sleeve '{sleeve_name}' total_composite ≤ 0, skipping")
            continue

        for assignment in group:
            raw_weight = (assignment.composite / total_composite) * sleeve_alloc

            # Concentration caps
            capped_weight = min(MAX_SINGLE_TICKER_PCT, max(MIN_SINGLE_TICKER_PCT, raw_weight))

            cap_note = (
                f"Cap applied: raw {raw_weight:.1f}% → {capped_weight:.1f}%"
                if abs(capped_weight - raw_weight) > 0.01
                else f"No cap: {capped_weight:.1f}%"
            )
            if abs(capped_weight - raw_weight) > 0.01:
                warnings.append(
                    f"{assignment.ticker} ({sleeve_name}): "
                    f"raw {raw_weight:.1f}% → capped {capped_weight:.1f}%"
                )

            capital_tl = (capped_weight / 100.0) * total_capital_tl

            positions.append(
                TickerPosition(
                    ticker=assignment.ticker,
                    sleeve=sleeve_name,
                    sub_category=assignment.sub_category,
                    weight_pct=capped_weight,
                    composite=assignment.composite,
                    capital_allocation_tl=capital_tl,
                    reasoning=[
                        f"Sleeve {sleeve_name}: {sleeve_alloc:.0f}% × "
                        f"composite_share({assignment.composite:.1f}/{total_composite:.1f}) "
                        f"= raw {raw_weight:.1f}%",
                        cap_note,
                    ],
                )
            )

    # 6. Cash reserve calculation
    invested_pct = sum(p.weight_pct for p in positions)
    cash_reserve_pct = max(0.0, 100.0 - invested_pct)

    if cash_reserve_pct < MIN_CASH_PCT:
        warnings.append(
            f"Cash reserve {cash_reserve_pct:.1f}% < min {MIN_CASH_PCT}% (over-allocation)"
        )
    if cash_reserve_pct > MAX_CASH_PCT:
        warnings.append(
            f"Cash reserve {cash_reserve_pct:.1f}% > max {MAX_CASH_PCT}% "
            f"(under-investment, boş sleeve veya cap overflow)"
        )

    cash_reserve_tl = (cash_reserve_pct / 100.0) * total_capital_tl

    # 7. Sleeve breakdown count
    sleeve_breakdown = {name: len(group) for name, group in sleeve_groups.items()}
    sleeve_breakdown["skip"] = sum(1 for a in assignments if a.sleeve == Sleeve.SKIP)

    reasoning.append(
        f"Risk profile: {risk_profile}. Target alloc: "
        f"core={target_alloc_pct['core']:.0f}%, "
        f"hizli={target_alloc_pct['hizli_buyume']:.0f}%, "
        f"yuksek={target_alloc_pct['yuksek_kazanc']:.0f}%."
    )
    reasoning.append(
        f"{len(positions)} pozisyon, cash reserve {cash_reserve_pct:.1f}%."
    )

    return PortfolioPlan(
        risk_profile=risk_profile,
        total_capital_tl=total_capital_tl,
        target_allocations=target_alloc_pct,
        actual_allocations=actual_alloc_pct,
        positions=positions,
        cash_reserve_pct=cash_reserve_pct,
        cash_reserve_tl=cash_reserve_tl,
        cash_reasons=cash_reasons,
        total_positions=len(positions),
        sleeve_breakdown=sleeve_breakdown,
        warnings=warnings,
        reasoning=reasoning,
    )


# ============================================================================
# Pretty Print Helper
# ============================================================================

def format_portfolio_report(plan: PortfolioPlan) -> str:
    """Insan-okur portfolio raporu."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"PORTFOLIO PLAN — {plan.risk_profile.upper()}")
    lines.append("=" * 80)
    lines.append(f"\nTotal Capital: TL {plan.total_capital_tl:,.0f}")
    lines.append(f"Risk Profile:  {plan.risk_profile}")

    lines.append(f"\n[Target vs Actual Allocations]")
    for sleeve, target_pct in plan.target_allocations.items():
        actual = plan.actual_allocations.get(sleeve, 0.0)
        if abs(target_pct - actual) < 0.1:
            status = "✓"
        else:
            status = "⚠ BOŞ → cash"
        lines.append(
            f"  {sleeve:<20s} target {target_pct:>5.1f}%  "
            f"actual {actual:>5.1f}%  {status}"
        )

    lines.append(f"\n[Positions ({plan.total_positions})]")
    for sleeve_name in ["core", "yuksek_kazanc", "hizli_buyume"]:
        sleeve_positions = [p for p in plan.positions if p.sleeve == sleeve_name]
        if sleeve_positions:
            lines.append(f"\n  {sleeve_name.upper()}:")
            for p in sorted(sleeve_positions, key=lambda x: -x.weight_pct):
                sub = f" [{p.sub_category}]" if p.sub_category else ""
                lines.append(
                    f"    {p.ticker:<6s} {p.weight_pct:>5.1f}%  "
                    f"TL {p.capital_allocation_tl:>11,.0f}  "
                    f"comp {p.composite:>5.1f}{sub}"
                )

    lines.append(f"\n[Cash Reserve]")
    lines.append(
        f"  {plan.cash_reserve_pct:.1f}% = TL {plan.cash_reserve_tl:,.0f}"
    )
    for reason in plan.cash_reasons:
        lines.append(f"  • {reason}")

    lines.append(f"\n[Sleeve Breakdown]")
    for sleeve, count in plan.sleeve_breakdown.items():
        lines.append(f"  {sleeve:<15s}: {count}")

    if plan.warnings:
        lines.append(f"\n[Warnings ({len(plan.warnings)})]")
        for w in plan.warnings:
            lines.append(f"  ⚠ {w}")

    lines.append("=" * 80)
    return "\n".join(lines)
