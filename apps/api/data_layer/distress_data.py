"""
Distress Ticker Manual Configuration — Faz 7.

6 BIST ticker (negative cyclical_dcf) için Black-Scholes inputs:
  KONTR / PETKM / THYAO / PGSUS / VESTL / HEKTS

Source: KAP yıllık raporlar + estimates.
NOT: Orchestrator pipeline financial_summary fetch'lemiyor henüz —
     manuel hardcode (Faz 7+ KAP integration parking).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class DistressInputs:
    """6 ticker × Black-Scholes input setleri."""
    ticker: str
    firm_value: float           # S USD (assets at market)
    debt_face_value: float      # K USD (total debt face)
    duration: float             # t years (debt weighted avg)
    volatility: float           # σ annualized (stock 60M proxy)
    risk_free_rate: float       # r decimal
    book_value: float           # for distress sale baseline
    rating: Optional[str] = None
    interest_coverage: Optional[float] = None
    z_score: Optional[float] = None
    notes: str = ""


DISTRESS_INPUTS: Dict[str, DistressInputs] = {
    "KONTR": DistressInputs(
        ticker="KONTR",
        firm_value=800e6,
        debt_face_value=600e6,
        duration=4.0,
        volatility=0.65,
        risk_free_rate=0.04,
        book_value=200e6,
        rating="B",
        interest_coverage=0.8,
        notes="Kontrolmatik tech post-IPO 2021 leveraged growth",
    ),
    "PETKM": DistressInputs(
        ticker="PETKM",
        firm_value=2_500e6,
        debt_face_value=2_000e6,
        duration=7.0,
        volatility=0.45,
        risk_free_rate=0.04,
        book_value=800e6,
        rating="BB",
        interest_coverage=1.5,
        notes="Petkim petrochemical SOCAR subsidiary",
    ),
    "THYAO": DistressInputs(
        ticker="THYAO",
        firm_value=14_000e6,
        debt_face_value=11_000e6,
        duration=8.0,
        volatility=0.55,
        risk_free_rate=0.04,
        book_value=4_000e6,
        rating="BB-",
        interest_coverage=2.0,
        notes="Türk Hava Yolları aviation",
    ),
    "PGSUS": DistressInputs(
        ticker="PGSUS",
        firm_value=4_500e6,
        debt_face_value=3_800e6,
        duration=6.0,
        volatility=0.60,
        risk_free_rate=0.04,
        book_value=800e6,
        rating="B+",
        interest_coverage=1.2,
        notes="Pegasus low-cost carrier",
    ),
    "VESTL": DistressInputs(
        ticker="VESTL",
        firm_value=1_500e6,
        debt_face_value=1_300e6,
        duration=5.0,
        volatility=0.50,
        risk_free_rate=0.04,
        book_value=250e6,
        rating="B",
        interest_coverage=0.6,
        notes="Vestel Beyaz Eşya consumer durables cyclical",
    ),
    "HEKTS": DistressInputs(
        ticker="HEKTS",
        firm_value=800e6,
        debt_face_value=700e6,
        duration=5.0,
        volatility=0.55,
        risk_free_rate=0.04,
        book_value=100e6,
        rating="B-",
        interest_coverage=0.5,
        notes="Hektaş chemical/agro",
    ),
}


def get_distress_inputs(ticker: str) -> Optional[DistressInputs]:
    """Ticker için distress inputs (case-insensitive)."""
    return DISTRESS_INPUTS.get(ticker.upper())


def is_distress_available(ticker: str) -> bool:
    """Bu ticker için manuel distress data var mı."""
    return ticker.upper() in DISTRESS_INPUTS


def list_distress_tickers() -> list:
    """Tüm distress ticker listesi."""
    return sorted(DISTRESS_INPUTS.keys())
