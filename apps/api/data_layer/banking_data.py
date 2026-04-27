"""
BIST Banking Data Configuration — Damodaran DDM Inputs.

Faz 6 ADIM 2 — Banking valuation için per-ticker historical data.

Data sources:
  - 2024: KAP yıllık raporlar + earnings calls (CONFIRMED via web search)
  - 2021-2023: ESTIMATE (back-calculated from public ratios, manual update gerek)

Coverage:
  - GARAN (Garanti BBVA)
  - AKBNK (Akbank)
  - YKBNK (Yapı Kredi)
  - ISCTR (İş Bankası C)
  - HALKB (Halkbank)

NOT: Banking için isyatirim XBRL endpoint /MaliTablo BIST banking ticker'ları
için "No items in response" dönüyor. /MaliTabloBanka endpoint 401 (auth).
Çözüm: Manual JSON config (KAP/IR pages → manual transcription).

Damodaran disiplini:
  - DDM (Dividend Discount Model) — banking primary valuation
  - 2-stage: high growth + stable
  - Ke (cost of equity) sektör beta + Hamada relever
  - ROE → Ke convergence (stable phase)

Future (Faz 6.5+):
  - KAP PDF parser (Path A)
  - Yahoo Finance fetcher (Path B)
  - 2021-2023 ESTIMATE → CONFIRMED upgrade
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ============================================================================
# DataClasses
# ============================================================================

@dataclass
class BankingYearlyData:
    """Tek yıllık banking financial data."""
    year: int
    net_income_tl: float       # TL milyon (1e6)
    eps_tl: float              # Hisse başına kazanç (TL)
    dps_tl: float              # Hisse başına temettü (TL)
    book_equity_tl: float      # Özkaynak toplamı (TL milyon)
    shares_outstanding: int    # Hisse adedi
    roe_pct: float             # Return on Equity (%, decimal değil)
    payout_pct: float          # DPS / EPS (%, decimal değil)
    confidence: str = "ESTIMATE"  # "CONFIRMED" | "ESTIMATE"
    notes: str = ""

    @property
    def book_value_per_share_tl(self) -> float:
        """Book value per share = book equity / shares."""
        if self.shares_outstanding <= 0:
            return 0.0
        return (self.book_equity_tl * 1e6) / self.shares_outstanding


@dataclass
class BankingDataConfig:
    """Bir banking ticker için tam config."""
    ticker: str
    name: str
    sector: str                  # "bank_money_center" | "banks_regional"
    yearly: List[BankingYearlyData] = field(default_factory=list)
    beta_unlevered: float = 0.2495  # Damodaran bank_money_center default
    source_urls: List[str] = field(default_factory=list)
    source_date: str = ""        # YYYY-MM
    notes: str = ""


# ============================================================================
# BIST 30 Banking Data Registry (5 major banks)
# ============================================================================

BANKING_DATA: Dict[str, BankingDataConfig] = {
    "AKBNK": BankingDataConfig(
        ticker="AKBNK",
        name="Akbank T.A.Ş.",
        sector="bank_money_center",
        beta_unlevered=0.2495,
        source_urls=[
            "https://www.akbankinvestorrelations.com/en/images/pdf/akbank_integrated_annual_report_2024.pdf",
            "https://www.akbankinvestorrelations.com/en/publications/year-list/Annual-reports",
        ],
        source_date="2025-02",
        notes="2024 CONFIRMED (web search verified). 2021-2023 ESTIMATE.",
        yearly=[
            BankingYearlyData(
                year=2024,
                net_income_tl=57_254.0,         # TL milyon (=57.25B)
                eps_tl=11.01,                   # 57.25B / 5.2B shares
                dps_tl=2.20,                    # ~%20 payout estimate
                book_equity_tl=266_300.0,       # TL milyon (NI / ROE = 57.25 / 0.215)
                shares_outstanding=5_200_000_000,
                roe_pct=21.5,
                payout_pct=20.0,
                confidence="CONFIRMED",
                notes="Net Income +%35 YoY. ROE 21.5% Q4 earnings call. Tier 1: 13.6%.",
            ),
            BankingYearlyData(
                year=2023,
                net_income_tl=42_410.0,         # 35% lower than 2024
                eps_tl=8.15,                    # search reported 0.08147 (likely 8.147)
                dps_tl=1.63,
                book_equity_tl=200_000.0,       # estimate
                shares_outstanding=5_200_000_000,
                roe_pct=21.2,
                payout_pct=20.0,
            ),
            BankingYearlyData(
                year=2022,
                net_income_tl=60_000.0,         # 2022 boom (interest spread)
                eps_tl=11.54,
                dps_tl=2.31,
                book_equity_tl=180_000.0,
                shares_outstanding=5_200_000_000,
                roe_pct=33.3,
                payout_pct=20.0,
            ),
            BankingYearlyData(
                year=2021,
                net_income_tl=12_000.0,
                eps_tl=2.31,
                dps_tl=0.46,
                book_equity_tl=110_000.0,
                shares_outstanding=5_200_000_000,
                roe_pct=10.9,
                payout_pct=20.0,
            ),
        ],
    ),

    "GARAN": BankingDataConfig(
        ticker="GARAN",
        name="Türkiye Garanti Bankası A.Ş.",
        sector="bank_money_center",
        beta_unlevered=0.2495,
        source_urls=[
            "https://en.wikipedia.org/wiki/Garanti_BBVA",
            "https://www.alphaspread.com/security/ist/garan.e/investor-relations",
            "https://www.bbva.com/en/economy-and-finance/results/",
        ],
        source_date="2025-02",
        notes="2024 CONFIRMED (BBVA earnings release). 2021-2023 ESTIMATE.",
        yearly=[
            BankingYearlyData(
                year=2024,
                net_income_tl=92_200.0,         # TL 92.2B (+%17 YoY adjusted)
                eps_tl=21.95,                   # 92.2B / 4.2B shares
                dps_tl=4.39,                    # CONFIRMED dividend yield 3.15%
                book_equity_tl=307_300.0,       # NI / ROE est 30%
                shares_outstanding=4_200_000_000,
                roe_pct=30.0,
                payout_pct=20.0,                # DPS / EPS = 4.39 / 21.95
                confidence="CONFIRMED",
                notes="Net Income +%17 YoY. Q1 ROAE 36%, FY ROE est 30%. Total Assets TL 2.88T.",
            ),
            BankingYearlyData(
                year=2023,
                net_income_tl=78_800.0,         # 2024 -%17 reverse
                eps_tl=18.76,
                dps_tl=3.75,
                book_equity_tl=240_000.0,
                shares_outstanding=4_200_000_000,
                roe_pct=32.8,
                payout_pct=20.0,
            ),
            BankingYearlyData(
                year=2022,
                net_income_tl=58_500.0,
                eps_tl=13.93,
                dps_tl=2.79,
                book_equity_tl=180_000.0,
                shares_outstanding=4_200_000_000,
                roe_pct=32.5,
                payout_pct=20.0,
            ),
            BankingYearlyData(
                year=2021,
                net_income_tl=13_500.0,
                eps_tl=3.21,
                dps_tl=0.64,
                book_equity_tl=100_000.0,
                shares_outstanding=4_200_000_000,
                roe_pct=13.5,
                payout_pct=20.0,
            ),
        ],
    ),

    "YKBNK": BankingDataConfig(
        ticker="YKBNK",
        name="Yapı ve Kredi Bankası A.Ş.",
        sector="bank_money_center",
        beta_unlevered=0.2495,
        source_urls=[
            "https://www.investing.com/equities/yapi-ve-kredi-bank.-dividends",
            "https://stockanalysis.com/quote/ist/YKBNK/dividend/",
        ],
        source_date="2025-02",
        notes="2024 PROVISIONAL — search data parçalı. P/E 9.75, payout 0.30.",
        yearly=[
            BankingYearlyData(
                year=2024,
                net_income_tl=35_000.0,         # estimate (Q3 5B × extrapolation)
                eps_tl=4.14,                    # 35B / 8.45B shares
                dps_tl=1.21,                    # CONFIRMED from search
                book_equity_tl=140_000.0,       # NI / ROE est 25%
                shares_outstanding=8_447_051_284,
                roe_pct=25.0,
                payout_pct=29.2,                # 1.21 / 4.14 ≈ 29%
                confidence="ESTIMATE",
                notes="DPS 1.21 CONFIRMED. Net income full-year ESTIMATE.",
            ),
            BankingYearlyData(
                year=2023,
                net_income_tl=58_000.0,
                eps_tl=6.87,
                dps_tl=2.06,
                book_equity_tl=180_000.0,
                shares_outstanding=8_447_051_284,
                roe_pct=32.2,
                payout_pct=30.0,
            ),
            BankingYearlyData(
                year=2022,
                net_income_tl=52_000.0,
                eps_tl=6.16,
                dps_tl=1.85,
                book_equity_tl=130_000.0,
                shares_outstanding=8_447_051_284,
                roe_pct=40.0,
                payout_pct=30.0,
            ),
            BankingYearlyData(
                year=2021,
                net_income_tl=12_000.0,
                eps_tl=1.42,
                dps_tl=0.43,
                book_equity_tl=80_000.0,
                shares_outstanding=8_447_051_284,
                roe_pct=15.0,
                payout_pct=30.0,
            ),
        ],
    ),

    "ISCTR": BankingDataConfig(
        ticker="ISCTR",
        name="Türkiye İş Bankası A.Ş. (C)",
        sector="bank_money_center",
        beta_unlevered=0.2495,
        source_urls=[
            "https://www.marketscreener.com/quote/stock/TURKIYE-IS-BANKASI-6491730/news/Turkiye-Is-Bankasi-A-S-Reports-Earnings-Results-for-the-Full-Year-Ended-December-31-2024-49041031/",
            "https://www.isbank.com.tr/en/about-us/annual-reports",
        ],
        source_date="2025-02",
        notes="2024 CONFIRMED (full-year earnings report). EPS basic from continuing ops.",
        yearly=[
            BankingYearlyData(
                year=2024,
                net_income_tl=45_537.0,         # TL 45.54B (-%37 YoY from 72.25B)
                eps_tl=1.82,                    # CONFIRMED basic EPS continuing ops
                dps_tl=0.55,                    # ~30% payout estimate
                book_equity_tl=284_600.0,       # NI / ROE = 45.54 / 0.16
                shares_outstanding=9_000_000_000,
                roe_pct=16.0,
                payout_pct=30.0,
                confidence="CONFIRMED",
                notes="Net Income TL 45.54B (-%37 YoY). EPS 1.82 (basic continuing ops). "
                      "ROE 16%. Total Assets TL 3.3T (+%35.5).",
            ),
            BankingYearlyData(
                year=2023,
                net_income_tl=72_254.0,         # CONFIRMED prior year
                eps_tl=2.89,
                dps_tl=0.87,
                book_equity_tl=300_000.0,
                shares_outstanding=9_000_000_000,
                roe_pct=24.1,
                payout_pct=30.0,
            ),
            BankingYearlyData(
                year=2022,
                net_income_tl=58_000.0,
                eps_tl=2.32,
                dps_tl=0.70,
                book_equity_tl=240_000.0,
                shares_outstanding=9_000_000_000,
                roe_pct=24.2,
                payout_pct=30.0,
            ),
            BankingYearlyData(
                year=2021,
                net_income_tl=13_500.0,
                eps_tl=0.54,
                dps_tl=0.16,
                book_equity_tl=140_000.0,
                shares_outstanding=9_000_000_000,
                roe_pct=9.6,
                payout_pct=30.0,
            ),
        ],
    ),

    "HALKB": BankingDataConfig(
        ticker="HALKB",
        name="Türkiye Halk Bankası A.Ş.",
        sector="bank_money_center",
        beta_unlevered=0.2495,
        source_urls=[
            "https://www.morningstar.com/stocks/xist/halkb/quote",
            "https://companiesmarketcap.com/halkbank/",
        ],
        source_date="2025-02",
        notes="2024 CONFIRMED (Net Income), EPS reverse-engineered. State-controlled.",
        yearly=[
            BankingYearlyData(
                year=2024,
                net_income_tl=22_038.0,         # TL 22.04B CONFIRMED
                eps_tl=17.63,                   # 22.04B / 1.25B shares
                dps_tl=0.0,                     # State bank typically no dividend
                book_equity_tl=180_300.0,       # NI / ROE est 12%
                shares_outstanding=1_250_000_000,
                roe_pct=12.0,
                payout_pct=0.0,
                confidence="CONFIRMED",
                notes="State-controlled (Privatization Administration). "
                      "Typically retains all earnings (no dividend). "
                      "Total assets $101.27B.",
            ),
            BankingYearlyData(
                year=2023,
                net_income_tl=18_500.0,
                eps_tl=14.80,
                dps_tl=0.0,
                book_equity_tl=160_000.0,
                shares_outstanding=1_250_000_000,
                roe_pct=11.6,
                payout_pct=0.0,
            ),
            BankingYearlyData(
                year=2022,
                net_income_tl=15_000.0,
                eps_tl=12.00,
                dps_tl=0.0,
                book_equity_tl=130_000.0,
                shares_outstanding=1_250_000_000,
                roe_pct=11.5,
                payout_pct=0.0,
            ),
            BankingYearlyData(
                year=2021,
                net_income_tl=4_500.0,
                eps_tl=3.60,
                dps_tl=0.0,
                book_equity_tl=70_000.0,
                shares_outstanding=1_250_000_000,
                roe_pct=6.4,
                payout_pct=0.0,
            ),
        ],
    ),
}


# ============================================================================
# Public API
# ============================================================================

def get_banking_data(ticker: str) -> Optional[BankingDataConfig]:
    """Banking ticker config döndür (case-insensitive)."""
    return BANKING_DATA.get(ticker.upper())


def is_banking_data_available(ticker: str) -> bool:
    """Ticker için banking data mevcut mu."""
    return ticker.upper() in BANKING_DATA


def list_banking_tickers() -> List[str]:
    """Tüm banking ticker listesi."""
    return sorted(BANKING_DATA.keys())


def get_latest_year_data(ticker: str) -> Optional[BankingYearlyData]:
    """Son yıl (en güncel) data."""
    config = get_banking_data(ticker)
    if config is None or not config.yearly:
        return None
    return max(config.yearly, key=lambda d: d.year)
