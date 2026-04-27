"""
BIST Holdings Portfolio Configuration.

Faz 2.5 SOTP — Sum of the Parts valuation için iştirak yapıları.

CONFIRMED data sources:
  - SAHOL: Q4 2024 Earnings Presentation, page 24 (NAV table, Dec 2024)
    https://yatirimciiliskileri.sabanci.com/en/images/pdf/sabanci-holding-earnings-presentation-q424.pdf
  - KCHOL: Gedik Yatırım March 2025 Company Update Report, page 2 (NAV breakdown)
    https://cdn.gedik.com/media/media/jvlgu0pg/gedik_kchol_companyupdatereport_mar25.pdf

Ownership % değerleri Dec 2024 (SAHOL) ve Mar 2025 (KCHOL) bazlı.
TL → USD konversiyonu DAMODARAN_PARAMS spot 35.37 (24 Nis 2026) ile.
Yıllık güncelleme önerilir (KAP yıllık faaliyet raporları).

Damodaran disiplini:
  - Listed children: ownership × DCF_value (Component 4 batch lookup)
  - Listed children (DCF yoksa): ownership × book_value_usd × 1.0 (fallback)
  - Banking listed: book_value × 1.5 P/B × ownership (justified P/B)
  - Non-listed: book_value × 1.0 × ownership (conservative)

PROVISIONAL flags:
  - Banking book_value_usd: rough estimate (KAP yıllık özkaynak ile validate)
  - Discount: %15 NAV target (intrinsic) — market reality -%30-50 (chronic)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ============================================================================
# DataClasses
# ============================================================================

@dataclass
class HoldingChild:
    """Tek iştirak (listed/banking_listed/non_listed)."""
    name: str                                   # Display name (Türkçe)
    type: str                                   # "listed" | "banking_listed" | "non_listed"
    ownership_pct: float                        # 0.0-1.0 (parent direct stake)
    ticker: Optional[str] = None                # if listed → DCF lookup
    book_value_usd: Optional[float] = None      # 100% basis fallback (USD)
    book_multiplier: float = 1.0                # P/B for banking, 1.0 default
    notes: str = ""                             # Damodaran disiplin yorumu


@dataclass
class HoldingPortfolio:
    """Bir holding'in tam SOTP yapısı."""
    parent_ticker: str                          # KCHOL veya SAHOL
    children: List[HoldingChild]
    holding_net_cash_usd: float = 0.0           # parent-level net cash (positive ya da negatif debt)
    minority_at_subs_usd: float = 0.0           # subsidiarylerdeki minority interests (deduction)
    holding_disconto_pct: float = 0.15          # %15 NAV target intrinsic
    source_url: str = ""
    source_date: str = ""                       # YYYY-MM-DD
    notes: str = ""


# ============================================================================
# SAHOL — Sabancı Holding Portfolio (CONFIRMED Dec 2024)
# ============================================================================
# Source: SAHOL Q4 2024 Earnings Presentation, page 24 NAV table
# Total NAV: $10,592M (Dec 2024) | Mcap: $5,715M | Discount: -46.0%
# All USD values from PDF, banking book_value PROVISIONAL

SAHOL_PORTFOLIO = HoldingPortfolio(
    parent_ticker="SAHOL",
    children=[
        # ─── Banking Listed (book × P/B 1.5) ───────────────────────────────
        HoldingChild(
            name="Akbank",
            type="banking_listed",
            ticker="AKBNK",
            ownership_pct=0.41,
            book_value_usd=12_000_000_000.0,  # ~$12B özkaynak 2024 sonu
            book_multiplier=1.5,
            notes="PROVISIONAL_2026_04 — needs validation. "
                  "PDF Mcap $9.6B (market), book equity ~$12B estimate. "
                  "Justified P/B 1.5 (BIST banking historical median).",
        ),

        # ─── Listed (BIST 30 dışı, DCF lookup yok → book × 1.0 fallback) ───
        # PDF "Mcap" = full equity market value, ownership × Mcap = contribution
        HoldingChild(
            name="Enerjisa Enerji",
            type="listed",
            ticker="ENJSA",
            ownership_pct=0.40,
            book_value_usd=1_885_000_000.0,  # PDF Mcap Dec 2024
            notes="PDF Mcap $1.885B. BIST 30 dışı, DCF lookup yoksa "
                  "book × 1.0 fallback.",
        ),
        HoldingChild(
            name="Aksigorta",
            type="listed",
            ticker="AKGRT",
            ownership_pct=0.36,
            book_value_usd=284_000_000.0,
            notes="PDF Mcap $284M.",
        ),
        HoldingChild(
            name="Agesa Hayat ve Emeklilik",
            type="listed",
            ticker="AGESA",
            ownership_pct=0.40,
            book_value_usd=708_000_000.0,
            notes="PDF Mcap $708M.",
        ),
        HoldingChild(
            name="Akçansa",
            type="listed",
            ticker="AKCNS",
            ownership_pct=0.40,
            book_value_usd=905_000_000.0,
            notes="PDF Mcap $905M.",
        ),
        HoldingChild(
            name="Çimsa",
            type="listed",
            ticker="CIMSA",
            ownership_pct=0.55,
            book_value_usd=1_170_000_000.0,
            notes="PDF Mcap $1.17B.",
        ),
        HoldingChild(
            name="Brisa",
            type="listed",
            ticker="BRISA",
            ownership_pct=0.44,
            book_value_usd=669_000_000.0,
            notes="PDF Mcap $669M (Bridgestone JV).",
        ),
        HoldingChild(
            name="Kordsa",
            type="listed",
            ticker="KORDS",
            ownership_pct=0.71,
            book_value_usd=335_000_000.0,
            notes="PDF Mcap $335M. Yüksek ownership 71%.",
        ),
        HoldingChild(
            name="Carrefoursa",
            type="listed",
            ticker="CRFSA",
            ownership_pct=0.57,
            book_value_usd=310_000_000.0,
            notes="PDF Mcap $310M (Carrefour JV). Divestment haberleri 2025.",
        ),
        HoldingChild(
            name="Teknosa",
            type="listed",
            ticker="TKNSA",
            ownership_pct=0.50,
            book_value_usd=134_000_000.0,
            notes="PDF Mcap $134M. Divestment haberleri 2025.",
        ),

        # ─── Non-Listed (book × 1.0 conservative) ──────────────────────────
        HoldingChild(
            name="Enerjisa Üretim",
            type="non_listed",
            ownership_pct=0.50,
            book_value_usd=3_952_000_000.0,  # PDF: 10.0xEV/EBITDA, $3.952B
            notes="PDF Dec 2024: 50% × 10.0xEV/EBITDA = $3.952B at 100%.",
        ),
        HoldingChild(
            name="Çimsa Building Solutions",
            type="non_listed",
            ownership_pct=0.32,
            book_value_usd=287_000_000.0,  # PDF Adj. Net Asset Value
            notes="PDF Dec 2024: 32% × Adj. NAV $287M.",
        ),
        HoldingChild(
            name="Sabancı Climate Technologies",
            type="non_listed",
            ownership_pct=1.00,
            book_value_usd=463_000_000.0,
            notes="PDF Dec 2024: 100% Adj. Book value $463M.",
        ),
        HoldingChild(
            name="DxBV (digital)",
            type="non_listed",
            ownership_pct=1.00,
            book_value_usd=76_000_000.0,
            notes="PDF Dec 2024: 100% Book value $76M.",
        ),
        HoldingChild(
            name="TUA",
            type="non_listed",
            ownership_pct=0.50,
            book_value_usd=189_000_000.0,
            notes="PDF Dec 2024: 50% × Book value $189M.",
        ),
        HoldingChild(
            name="Other (Tursa, AEO, TMA, SabancıDx)",
            type="non_listed",
            ownership_pct=1.00,
            book_value_usd=362_000_000.0,
            notes="PDF Dec 2024: 100% pool $362M.",
        ),
    ],
    holding_net_cash_usd=351_000_000.0,  # PDF Dec 2024 net cash $351M
    minority_at_subs_usd=0.0,            # Already netted in PDF NAV
    holding_disconto_pct=0.15,
    source_url=(
        "https://yatirimciiliskileri.sabanci.com/en/images/pdf/"
        "sabanci-holding-earnings-presentation-q424.pdf"
    ),
    source_date="2024-12-31",
    notes="SAHOL official NAV breakdown Dec 2024. "
          "PDF reports market discount -46.0%, our %15 disconto NAV target.",
)


# ============================================================================
# KCHOL — Koç Holding Portfolio (CONFIRMED Mar 2025)
# ============================================================================
# Source: Gedik Yatırım Mar 2025 KCHOL Company Update Report, page 2
# Total NAV: TL 626.075bn (Mar 2025) ÷ 35.37 spot ≈ $17.7B
# All TL values from PDF, USD conversion at 35.37 spot

SPOT_RATE_USD_TL = 35.37  # DAMODARAN_PARAMS spot 24 Nis 2026


def _tl_to_usd(tl_amount_in_billions: float) -> float:
    """TL bn → USD (35.37 spot)."""
    return (tl_amount_in_billions * 1e9) / SPOT_RATE_USD_TL


KCHOL_PORTFOLIO = HoldingPortfolio(
    parent_ticker="KCHOL",
    children=[
        # ─── Banking Listed (book × P/B 1.5) ───────────────────────────────
        HoldingChild(
            name="Yapı Kredi Bankası",
            type="banking_listed",
            ticker="YKBNK",
            ownership_pct=0.41,
            book_value_usd=8_000_000_000.0,  # ~$8B özkaynak 2024 sonu
            book_multiplier=1.5,
            notes="PROVISIONAL_2026_04 — needs validation. "
                  "Gedik market value TL 74.3bn at 41%; book equity ~$8B est. "
                  "Justified P/B 1.5 (BIST banking historical median).",
        ),

        # ─── Listed (BIST 30 batch'te DCF lookup mevcut) ───────────────────
        HoldingChild(
            name="Tüpraş",
            type="listed",
            ticker="TUPRS",
            ownership_pct=0.40,  # KCHOL effective via EYAS chain (86.6% × 46%)
            book_value_usd=_tl_to_usd(274.568),  # Gedik 100% basis TL 274.568bn → $7.76B
            notes="EYAS chain effective ownership ~40% "
                  "(KCHOL 86.6% of EYAS, EYAS 46% of TUPRS). "
                  "BIST 30 batch'te DCF lookup mevcut.",
        ),
        HoldingChild(
            name="Ford Otosan",
            type="listed",
            ticker="FROTO",
            ownership_pct=0.387,
            book_value_usd=_tl_to_usd(362.475),  # 140.238 / 0.387 = TL 362.475bn → $10.25B
            notes="Ford Motor Co JV. BIST 30 batch'te DCF lookup mevcut.",
        ),
        HoldingChild(
            name="Arçelik",
            type="listed",
            ticker="ARCLK",
            ownership_pct=0.414,
            book_value_usd=_tl_to_usd(95.483),  # 39.530 / 0.414 = TL 95.483bn → $2.70B
            notes="BIST 30 batch'te DCF lookup mevcut.",
        ),
        HoldingChild(
            name="Tofaş",
            type="listed",
            ticker="TOASO",
            ownership_pct=0.376,
            book_value_usd=_tl_to_usd(87.225),  # 32.797 / 0.376 = TL 87.225bn → $2.47B
            notes="Stellantis JV. BIST 30 batch'te DCF lookup mevcut.",
        ),

        # ─── Listed (BIST 30 dışı, book × 1.0 fallback) ────────────────────
        HoldingChild(
            name="Otokar",
            type="listed",
            ticker="OTKAR",
            ownership_pct=0.474,
            book_value_usd=_tl_to_usd(58.535),  # 27.746 / 0.474 = TL 58.535bn → $1.66B
            notes="Defense vehicles. BIST 30 dışı, book × 1.0 fallback.",
        ),
        HoldingChild(
            name="Türk Traktör",
            type="listed",
            ticker="TTRAK",
            ownership_pct=0.375,
            book_value_usd=_tl_to_usd(82.104),  # 30.789 / 0.375 = TL 82.104bn → $2.32B
            notes="CNH Industrial JV. BIST 30 dışı.",
        ),
        HoldingChild(
            name="Aygaz",
            type="listed",
            ticker="AYGAZ",
            ownership_pct=0.407,
            book_value_usd=_tl_to_usd(35.172),  # 14.315 / 0.407 = TL 35.172bn → $0.99B
            notes="LPG distribution. BIST 30 dışı.",
        ),

        # ─── Non-Listed (book × 1.0 conservative) ──────────────────────────
        HoldingChild(
            name="Otokoç (Otomoto retail)",
            type="non_listed",
            ownership_pct=0.964,
            book_value_usd=_tl_to_usd(38.929),  # 37.525 / 0.964 = TL 38.929bn → $1.10B
            notes="Auto retail dealer. Gedik 96.4% × $1.10B = $1.06B contribution.",
        ),
        HoldingChild(
            name="Tourism Pool (Altınyunus, Mares, Setur)",
            type="non_listed",
            ownership_pct=1.00,  # blended
            book_value_usd=_tl_to_usd(7.124),  # ~$0.20B
            notes="Tourism subsidiaries blended. Minor.",
        ),
        HoldingChild(
            name="Real Estate Pool",
            type="non_listed",
            ownership_pct=1.00,
            book_value_usd=_tl_to_usd(9.227),  # ~$0.26B
            notes="Real estate consolidated. Gedik TL 9.227bn.",
        ),
        HoldingChild(
            name="Other Non-Listed (Koç Sistem, Token, WAT, Koçtaş, Düzey, "
                 "Koç Finans, Arçelik LG)",
            type="non_listed",
            ownership_pct=1.00,  # blended
            book_value_usd=_tl_to_usd(15.875),  # ~$0.45B blended
            notes="Diversified non-listed pool blended.",
        ),
    ],
    holding_net_cash_usd=_tl_to_usd(34.553),  # Gedik net cash TL 34.553bn → $0.98B
    minority_at_subs_usd=0.0,                 # Already netted in NAV breakdown
    holding_disconto_pct=0.15,
    source_url=(
        "https://cdn.gedik.com/media/media/jvlgu0pg/"
        "gedik_kchol_companyupdatereport_mar25.pdf"
    ),
    source_date="2025-03-27",
    notes="KCHOL NAV breakdown Mar 2025 (Gedik Yatırım analyst report). "
          "Gedik current discount -33%, 15-yıl average -13%. "
          "TUPRS via EYAS chain (KCHOL 86.6% of EYAS × EYAS 46% of TUPRS = ~40%).",
)


# ============================================================================
# Registry
# ============================================================================

HOLDINGS_PORTFOLIO: Dict[str, HoldingPortfolio] = {
    "KCHOL": KCHOL_PORTFOLIO,
    "SAHOL": SAHOL_PORTFOLIO,
}


# ============================================================================
# Public API
# ============================================================================

def is_holding(ticker: str) -> bool:
    """Ticker holding mi (SOTP gerekir)."""
    return ticker.upper() in HOLDINGS_PORTFOLIO


def get_portfolio(ticker: str) -> Optional[HoldingPortfolio]:
    """Holding ticker için portfolio config'i döndür."""
    return HOLDINGS_PORTFOLIO.get(ticker.upper())


def list_listed_children(ticker: str) -> List[str]:
    """Holding'in listed (BIST'te) child ticker'larını listele."""
    portfolio = get_portfolio(ticker)
    if portfolio is None:
        return []
    return [
        c.ticker
        for c in portfolio.children
        if c.type in ("listed", "banking_listed") and c.ticker is not None
    ]


def list_banking_children(ticker: str) -> List[str]:
    """Holding'in banking_listed child ticker'larını listele."""
    portfolio = get_portfolio(ticker)
    if portfolio is None:
        return []
    return [
        c.ticker
        for c in portfolio.children
        if c.type == "banking_listed" and c.ticker is not None
    ]


def list_all_holdings() -> List[str]:
    """Tüm holding parent ticker'larını listele."""
    return sorted(HOLDINGS_PORTFOLIO.keys())
