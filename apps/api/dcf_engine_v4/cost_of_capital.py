"""
Cost of Capital (Damodaran ERP+CRP framework).

Ke = Rf + β × ERP + λ × CRP   (Damodaran "lambda" Türkiye exposure)
WACC = (E/V) × Ke + (D/V) × Kd × (1-tax)

Kd synthetic rating (Damodaran tablosu, simplified):
  Interest Coverage Ratio → Default Spread

Türkiye 2026 Q1 market parametreleri (Damodaran ctryprem.xlsx):
  Rf USD (10Y UST):         3.97%
  Mature ERP (US):          4.44%
  Türkiye CRP:              6.01%
  Türkiye corporate tax:   25.00%
  Türkiye sovereign spread: 4.46%
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Damodaran market params (2026-Q1 — manuel maintained)
# ---------------------------------------------------------------------------
# Updated 2026-05-09 via Faz B1 audit Adim 7 (anchor v4.0 -> v4.1 transition)
# Source: apps/api/data/damodaran/2026_05_09/parameters.json
# Audit chain: docs/audit_findings_session4.md, audit_decision_v4.md
# Anchor declaration: apps/api/data/anchor.json (v4.1 = 216.33 TL TUPRS)
RF_USD_10Y = 0.0395  # was: 0.0397 (Damodaran 10Y UST - US default Aa1)
MATURE_ERP_US = 0.0423  # was: 0.0444 (S&P implied - US default Aa1)
TURKEY_CRP = 0.0466  # was: 0.0601 (Damodaran ctryprem Sub 2026 update)
TURKEY_TAX_RATE = 0.25  # unchanged
TURKEY_SOVEREIGN_SPREAD = 0.0306  # was: 0.0446 (Turkey Ba3 upgrade Sub 2026)


# Damodaran synthetic rating tablosu (interest_coverage → default_spread)
# Source: ctryprem.xlsx "Default Spreads for Ratings" sheet (1/1/26)
# Updated: Session 6.b 2026-05-10 — 13 spread refresh + 2 preserve
# NOT: Coverage thresholds + rating strings UNCHANGED ([II] Conservative)
# NOT: C2/C, D2/D PRESERVED (Damodaran sheet'te yok)
_RATING_TABLE = [
    # (min_coverage, max_coverage, rating, default_spread)
    (8.50,  9999.0, "Aaa/AAA",  0.0000),  # was: 0.0069
    (6.50,   8.50,  "Aa2/AA",   0.0042),  # was: 0.0085
    (5.50,   6.50,  "A1/A+",    0.0060),  # was: 0.0107
    (4.25,   5.50,  "A2/A",     0.0072),  # was: 0.0122
    (3.00,   4.25,  "A3/A-",    0.0102),  # was: 0.0156
    (2.50,   3.00,  "Baa2/BBB", 0.0162),  # was: 0.0212
    (2.25,   2.50,  "Ba1/BB+",  0.0213),  # was: 0.0273
    (2.00,   2.25,  "Ba2/BB",   0.0256),  # was: 0.0337
    (1.75,   2.00,  "B1/B+",    0.0383),  # was: 0.0398
    (1.50,   1.75,  "B2/B",     0.0467),  # was: 0.0470
    (1.25,   1.50,  "B3/B-",    0.0552),  # unchanged
    (0.80,   1.25,  "Caa/CCC",  0.0765),  # was: 0.0850 (Caa2 mid)
    (0.65,   0.80,  "Ca2/CC",   0.1020),  # was: 0.1135 (Ca)
    (0.20,   0.65,  "C2/C",     0.1469),  # preserved (Dam yok)
    (-9999.0, 0.20, "D2/D",     0.1969),  # preserved (Dam yok)
]


@dataclass
class WACCResult:
    cost_of_equity: float        # Ke (decimal)
    cost_of_debt_pretax: float   # Kd_pretax
    cost_of_debt_aftertax: float # Kd_aftertax
    wacc: float                  # decimal
    rating: str                  # "A2/A" gibi
    weight_equity: float         # 0..1
    weight_debt: float
    interest_coverage: Optional[float]


def synthetic_rating(interest_coverage: Optional[float]) -> tuple[str, float]:
    """Interest coverage → (rating, default_spread).

    Coverage None → "BB+_sovereign_sector" fallback (Damodaran Türkiye
    sovereign+sector synthetic, manuel %4 spread, mevcut orchestrator.py
    DAMODARAN_PARAMS["synthetic_spread"] ile uyumlu).
    Coverage gerçekten negatif → "D2/D".
    """
    if interest_coverage is None:
        # Damodaran Türkiye Sovereign+Sector synthetic (mevcut orchestrator.py
        # DAMODARAN_PARAMS["synthetic_spread"]=0.04 BB+ rating). Faz 2.4.5.
        return "BB+_sovereign_sector", 0.0400
    if interest_coverage < -9000:
        return "D2/D", 0.1969
    for lo, hi, rating, spread in _RATING_TABLE:
        if lo <= interest_coverage < hi:
            return rating, spread
    return "D2/D", 0.1969


def calculate_cost_of_equity(
    beta: float,
    lambda_tr: float = 1.0,
    rf: float = RF_USD_10Y,
    erp: float = MATURE_ERP_US,
    crp: float = TURKEY_CRP,
) -> float:
    """Ke = Rf + β × ERP + λ × CRP.

    lambda_tr: Türkiye risk maruziyeti (1.0 = full domestic, 0.5 = half).
    Default 1.0 — KAP-listed BIST şirketleri çoğunluğu domestic.
    """
    return rf + beta * erp + lambda_tr * crp


def calculate_wacc(
    beta_relevered: float,
    market_cap: float,
    total_debt: float,
    op_income: Optional[float] = None,
    interest_expense: Optional[float] = None,
    tax_rate: float = TURKEY_TAX_RATE,
    lambda_tr: float = 1.0,
) -> WACCResult:
    """WACC = (E/V) Ke + (D/V) Kd_aftertax.

    Args:
        beta_relevered: Session 3.7 beta (sektör + firma D/E).
        market_cap:   piyasa değeri TL (yfinance).
        total_debt:   KAP Bilanço short+long term borçlanma.
        op_income:    EBIT / interest_coverage hesabı için.
        interest_expense: KAP financials.
        tax_rate:     Türkiye 25%.
        lambda_tr:    Türkiye exposure (default 1.0).
    """
    ke = calculate_cost_of_equity(beta_relevered, lambda_tr=lambda_tr)

    # Kd synthetic rating
    if op_income is not None and interest_expense is not None and interest_expense != 0:
        coverage = op_income / abs(interest_expense)
    else:
        coverage = None
    rating, default_spread = synthetic_rating(coverage)
    kd_pretax = RF_USD_10Y + default_spread + TURKEY_SOVEREIGN_SPREAD
    kd_aftertax = kd_pretax * (1 - tax_rate)

    # Weights
    total_v = market_cap + total_debt
    if total_v <= 0:
        # Degenerate — return Ke as WACC fallback
        return WACCResult(
            cost_of_equity=ke,
            cost_of_debt_pretax=kd_pretax,
            cost_of_debt_aftertax=kd_aftertax,
            wacc=ke,
            rating=rating,
            weight_equity=1.0,
            weight_debt=0.0,
            interest_coverage=coverage,
        )
    we = market_cap / total_v
    wd = total_debt / total_v
    wacc = we * ke + wd * kd_aftertax

    return WACCResult(
        cost_of_equity=ke,
        cost_of_debt_pretax=kd_pretax,
        cost_of_debt_aftertax=kd_aftertax,
        wacc=wacc,
        rating=rating,
        weight_equity=we,
        weight_debt=wd,
        interest_coverage=coverage,
    )
