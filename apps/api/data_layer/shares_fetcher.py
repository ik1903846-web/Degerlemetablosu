"""
Shares Outstanding Fetcher.

Damodaran DCF için Equity Value / Shares Outstanding = Value per Share.
Doğru shares outstanding olmadan DCF değeri anlamsız.

Strategy:
- STATIC_SHARES dictionary (BIST 30 için manuel doğrulanmış)
- isyatirim API endpoint (Adım 3.5 future, parking)
- KAP genel bilgi sayfası (Adım 3.5 future, parking)

Pilot için STATIC_SHARES yeterli — TUPRS doğrulandı:
- Resmi şirket sayfası: 1,926,795,598 adet
- Market cap doğrulama: 1.93B × 269 TL = 518.3B TL ✓ (24 Nis 2026)

ADR References:
- ADR-001: BIST primary data (resmi şirket sayfaları)
- ADR-067: Sleeve entry — accurate value per share gerekir
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Static Shares Outstanding — BIST 30 Manuel Doğrulanmış
# ============================================================================

# Source: Resmi şirket sayfaları + market cap cross-check (Nisan 2026)
# Format: ticker → adet (integer)
# Bu liste BIST 30 için manuel maintain edilir
# Yapısal değişiklikler (split, capital increase) seyrek ama mümkün
STATIC_SHARES_OUTSTANDING: Dict[str, int] = {
    # Energy & Refining
    "TUPRS": 1_926_795_598,    # Tüpraş (resmi: 1.93B, doğrulandı 24 Nis 2026)

    # Banking
    "GARAN": 4_200_000_000,    # Garanti BBVA (~4.2B)
    "AKBNK": 5_200_000_000,    # Akbank (~5.2B)
    "ISCTR": 9_000_000_000,    # İş Bankası (~9B)
    "YKBNK": 8_447_051_284,    # Yapı Kredi (~8.45B)
    "HALKB": 1_250_000_000,    # Halkbank
    "VAKBN": 25_000_000_000,   # VakıfBank (~25B)

    # Steel & Mining
    "EREGL": 3_500_000_000,    # Ereğli Demir Çelik (~3.5B)
    "KRDMD": 950_000_000,      # Kardemir D
    "TRALT": 152_500_000,      # Türk Altın İşletmeleri (eski KOZAL, Kasım 2025 rename)
    "TRMET": 305_000_000,      # TR Anadolu Metal Madencilik (eski KOZAA, Kasım 2025 rename)

    # Consumer & Retail
    "BIMAS": 607_200_000,      # BIM (~607M)
    "MGROS": 181_000_000,      # Migros (~181M)
    "SOKM": 612_000_000,       # ŞOK Marketler (~612M)

    # Industrials
    "TOASO": 500_000_000,      # Tofaş (~500M)
    "FROTO": 350_910_000,      # Ford Otosan (~351M)
    "ARCLK": 675_728_205,      # Arçelik
    "ASELS": 1_140_000_000,    # Aselsan (~1.14B)

    # Aviation
    "THYAO": 1_380_000_000,    # Türk Hava Yolları (~1.38B)
    "PGSUS": 102_271_525,      # Pegasus (~102M)

    # Holding
    "KCHOL": 2_535_898_345,    # Koç Holding
    "SAHOL": 2_040_403_931,    # Sabancı Holding

    # Other
    "ENKAI": 6_000_000_000,    # ENKA İnşaat (~6B)
    "PETKM": 2_613_000_000,    # Petkim (~2.6B)
    "CCOLA": 254_370_782,      # Coca-Cola İçecek

    # Faz 4.5 — BIST 50 expansion (resmi şirket sayfası + KAP cross-check)
    "TCELL": 2_200_000_000,    # Turkcell (~2.2B)
    "TTKOM": 3_500_000_000,    # Türk Telekom (~3.5B)
    "AEFES": 592_105_263,      # Anadolu Efes (~592M)
    "ULKER": 384_000_000,      # Ülker Bisküvi (~384M)
    "AKSA": 185_000_000,       # Aksa Akrilik (~185M)
    "HEKTS": 1_440_000_000,    # Hektaş (~1.44B)
    "NETAS": 65_000_000,       # Netaş (~65M, küçük cap)
    "TAVHL": 363_281_250,      # TAV Havalimanları (~363M)
    "AKSGY": 1_200_000_000,    # Akiş GYO (~1.2B)
    "AKSEN": 1_226_750_000,    # Aksa Enerji (~1.23B)
    "BIZIM": 60_000_000,       # Bizim Toptan (~60M, küçük cap)
    "MAVI": 198_750_000,       # Mavi (~199M)
    "LOGO": 25_000_000,        # Logo Yazılım (~25M, küçük cap)
    "ASUZU": 30_000_000,       # Anadolu Isuzu (~30M, küçük cap)
    "TKFEN": 370_000_000,      # Tekfen (~370M)
    "VESTL": 374_500_000,      # Vestel (~374M)
    "OYAKC": 460_000_000,      # OYAK Çimento (~460M)
    "KARSN": 720_000_000,      # Karsan (~720M)
    "DOHOL": 2_616_938_288,    # Doğan Holding (~2.62B)

    # Faz 4.6 — BIST 100 expansion (KAP/şirket sayfası tahmini, 20 ticker)
    # Faz 4.7 — graceful IPO-aware fetch eklendi, 5 high-growth recover:
    "SMRTG": 1_213_750_000,    # Smart Güneş (~1.21B)
    "CWENE": 145_000_000,      # CW Enerji (~145M)
    "KCAER": 290_000_000,      # Kocaer Çelik (~290M)
    "KONTR": 540_000_000,      # Kontrolmatik (~540M)
    "ENJSA": 1_181_250_000,    # Enerjisa Enerji (~1.18B)

    "INFO":  110_000_000,      # İnfo Yatırım (~110M, fintech)

    # Mid-cap Industrial
    "OTKAR":  24_000_000,      # Otokar (~24M)
    "KORDS": 194_500_000,      # Kordsa (~195M)
    "PARSN":  95_000_000,      # Parsan (~95M)
    "VESBE": 190_000_000,      # Vestel Beyaz Eşya (~190M)
    "EUREN": 290_000_000,      # Eurometal (~290M)
    "ECILC":  30_000_000,      # Eczacıbaşı İlaç (~30M)

    # Mid-cap Diversified
    "TKNSA": 165_000_000,      # Teknosa (~165M)
    "PRKAB": 134_000_000,      # Türk Prysmian Kablo (~134M)
    "KAPLM": 200_000_000,      # Kaplamin (~200M)
    "ISMEN": 210_000_000,      # İş Yatırım (~210M)

    # Mid-cap Specialty
    "BOSSA": 220_000_000,      # Bossa (~220M)
    "ARENA":  63_000_000,      # Arena Bilgisayar (~63M)
    "INDES": 280_000_000,      # İndeks Bilgisayar (~280M)
    "TUKAS":  60_000_000,      # Tukaş Gıda (~60M)

    # Faz 4.21 — BIST 100 official tamamlama (35 ticker, yfinance fetch May 2026)
    "ALARK":      434_526_825,    # Alarko Holding
    "ANSGR":    2_000_000_000,    # Anadolu Sigorta
    "BALSU":    1_112_000_000,    # Balıkesir Çimento
    "BRYAT":       27_537_101,    # Borusan Yatırım Holding
    "BSOKE":    1_600_000_000,    # Batısöke Çimento
    "BTCIM":    5_580_000_000,    # Batıçim Çimento
    "CANTE":    9_974_175_415,    # Çan2 Termik
    "CIMSA":      945_591_094,    # Çimsa Çimento
    "CVKMD":    1_400_000_000,    # CVK Maden
    "DOAS":       220_000_000,    # Doğuş Otomotiv
    "EFOR":     2_178_000_000,    # Eforce Group
    "ENERY":    9_000_000_000,    # Enerya Enerji
    "EUPWR":      555_000_000,    # Europower Enerji
    "FENER":    6_250_000_000,    # Fenerbahçe Sportif
    "GESAN":      460_000_000,    # Girişim Elektrik
    "GRSEL":      102_000_000,    # Garanti Sigorta
    "GUBRF":      334_000_000,    # Gübre Fabrikaları
    "IZENR":    2_443_750_000,    # İz Enerji
    "KLRHO":    1_625_000_000,    # Kıler Holding
    "KUYAS":      400_000_000,    # Konya Çimento
    "MAGEN":    2_950_000_000,    # Margün Enerji
    "MIATK":      494_000_000,    # MIA Teknoloji (★ post-IPO)
    "OBAMS":    2_876_530_554,    # Oba Makarnacılık
    "ODAS":     1_400_000_000,    # Odaş Elektrik
    "PAHOL":   20_000_000_000,    # Pasifik GYO Holding
    "PASEU":      672_000_000,    # Pasifik Eurasia
    "PSGYO":    6_900_847_276,    # Petrol Ofisi GYO
    "RALYH":      333_000_000,    # RAL Yatırım Holding
    "REEDR":      950_000_000,    # Reeder Teknoloji (★ post-IPO)
    "SARKY":    1_000_000_000,    # Sarkuysan
    "SASA":    43_815_615_361,    # Sasa Polyester
    "SISE":     3_063_214_056,    # Şişe Cam
    "TRENJ":      259_785_561,    # TR Enerji
    "TURSG":   10_000_000_000,    # Türkiye Sigorta
    "ZOREN":    5_000_000_000,    # Zorlu Energy

    # Faz 4.22 — BIST 200 partial layer (19 ticker, yfinance fetch May 2026)
    "AGHOL":    2_435_345_180,    # Anadolu Group Holding
    "ALTNY":    1_000_000_000,    # Altınyağ
    "ASTOR":      998_000_000,    # Astor Enerji (★ post-IPO 2022)
    "BRSAN":      141_771_582,    # Borusan Mannesmann
    "DAPGM":    2_650_000_000,    # DAP Yapı Group
    "DSTKF":      333_333_333,    # Destekfonu
    "EKGYO":    3_661_120_138,    # Emlak Konut GYO
    "GENIL":    4_500_000_000,    # Geneksis İlaç
    "GLRMK":      322_600_000,    # Güler Yatırım Holding
    "GRTHO":      125_000_000,    # Güre Tarım Holding
    "GSRAY":   13_500_000_000,    # Galatasaray Sportif
    "KTLEV":    2_070_000_000,    # KaplanTekstil
    "MPARK":      102_122_233,    # MLP Care
    "PATEK":      674_934_432,    # Patek Mücevherat
    "QUAGR":    2_640_000_000,    # Quagger Tarım
    "SKBNK":    2_500_000_000,    # Şekerbank
    "TABGD":      261_292_000,    # Tab Gıda
    "TSKB":     2_800_000_000,    # Türkiye Sınai Kalkınma Bankası
    "TUREX":    1_080_000_000,    # Türker İnşaat

    # Faz 4.22 EXTEND — BIST 200 tam endeks tamamlama (82 ticker, yfinance May 2026)
    "AGESA":      180_000_000,    # Agesa Hayat Emeklilik
    "AKCNS":      191_447_068,    # Akçansa Çimento
    "AKFGY":    3_900_000_000,    # Akfen GYO
    "AKGRT":    1_612_000_000,    # Aksigorta
    "AKMGY":       37_264_000,    # Akmerkez GYO
    "ALBRK":    2_500_000_000,    # Albaraka Türk Katılım (banking)
    "ALGYO":    2_028_600_000,    # Alarko GYO
    "ANHYT":      430_000_000,    # Anadolu Hayat Emeklilik
    "ASGYO":      659_000_000,    # Akiş GYO
    "ATAGY":       47_500_000,    # Ata GYO
    "AVGYO":      111_600_000,    # Avrasya GYO
    "AVHOL":       37_250_000,    # Avrasya Holding
    "AVOD":       270_000_000,    # Avod Kurutulmuş Gıda
    "AYDEM":      705_000_000,    # Aydem Enerji
    "AYEN":       277_500_000,    # Aydın Enerji
    "AYGAZ":      219_800_767,    # Aygaz LPG
    "BAGFS":      135_000_000,    # Bagfaş Fertilizer
    "BANVT":      100_023_579,    # Banvit Tavukçuluk
    "BERA":       683_200_000,    # Bera Holding
    "BFREN":      122_522_806,    # Brisa Fren
    "BRISA":      305_116_875,    # Brisa Bridgestone
    "CLEBI":       24_300_000,    # Çelebi Hava Servisi
    "CRFSA":      127_773_766,    # CarrefourSA
    "DAGI":       400_000_000,    # Dagi Yatırım Holding
    "DEVA":       200_019_288,    # Deva Holding
    "DGATE":       29_841_960,    # Datagate Bilgisayar
    "DGGYO":      332_007_786,    # Doğuş GYO
    "DOCO":        10_983_458,    # DO & Co Catering
    "EBEBK":      160_000_000,    # eBebek
    "ECZYT":      105_000_000,    # Eczacıbaşı Yatırım
    "EDIP":        65_000_000,    # Edip Gayrimenkul
    "EGEGY":      200_000_000,    # Ege Endüstri
    "GEDIK":    2_000_000_000,    # Gedik Yatırım
    "GENTS":      750_000_000,    # Gen İlaç (post-IPO)
    "GLYHO":    1_950_000_000,    # Global Yatırım Holding
    "GOODY":      270_000_000,    # Good Year Lastik
    "GOZDE":      385_000_000,    # Gözde Girişim Sermayesi
    "HEDEF":    1_949_455_899,    # Hedef Yatırım
    "HLGYO":    3_752_699_766,    # Halk GYO
    "HOROZ":       90_488_084,    # Horoz Lojistik
    "HUBVC":      280_000_000,    # Hub Girişim
    "ICBCT":      860_000_000,    # ICBC Türkiye (banking)
    "IDGYO":      150_000_000,    # İdealist GYO
    "IEYHO":      543_595_733,    # IE Yatırım Holding
    "INTEK":        8_000_000,    # İntek Yatırım
    "INTEM":       19_164_221,    # İntema İnşaat
    "INVEO":    1_000_000_000,    # Inveo Yatırım
    "ISGYO":      958_750_000,    # İş GYO
    "JANTS":      700_000_000,    # Jantsa Jant
    "KAREL":      805_885_530,    # Karel Elektronik
    "KFEIN":      197_500_000,    # Kafein Yazılım
    "KLGYO":    1_395_000_000,    # Kıler GYO
    "KLNMA":   10_000_000_000,    # Kalkınma Bankası (banking)
    "KOTON":      829_650_000,    # Koton Apparel
    "KRDMA":      240_303_646,    # Kardemir A
    "KRDMB":      119_470_352,    # Kardemir B
    "KRONT":      171_222_156,    # Kron Teknoloji
    "MEGMT":      265_000_000,    # Megamotion
    "MERCN":      190_370_946,    # Merkez Tekstil
    "MNDRS":      277_292_576,    # Menderes Tekstil
    "MOGAN":    2_440_108_000,    # Mogan Enerji
    "MOPAS":      273_000_000,    # Mopaş Marketler
    "MZHLD":      108_559_000,    # Mazhar-El Holding
    "NETCD":      137_000_000,    # Net Holding C
    "NTHOL":      456_040_861,    # Net Holding
    "NUGYO":      335_348_000,    # Nurol GYO
    "NUHCM":      150_213_600,    # Nuh Çimento
    "OBASE":       45_500_000,    # Obase
    "ORCAY":      240_000_000,    # Orçay
    "OZKGY":    1_452_635_728,    # Özak GYO
    "PENTA":      393_516_000,    # Penta Teknoloji
    "PETUN":      303_345_000,    # Pet Holding
    "POLHO":      758_500_000,    # Polisan Holding
    "PSDTC":        7_425_000,    # Pasdas Termik
    "QNBTR":    5_500_000_000,    # QNB Finansbank (banking)
    "RAYSG":      163_069_856,    # Ray Sigorta
    "SELEC":      621_000_000,    # Selçuk İlaç
    "SMART":       31_862_500,    # Smart Solar (post-IPO)
    "SUNTK":      474_600_000,    # Sun Tekstil
    "TRHOL":       30_000_000,    # Türkiye Holding
    "TTRAK":      100_066_875,    # Türk Traktör
    "ULAS":        25_382_175,    # Ulaşlar Tekstil

    # NOT: Bu liste cross-check edildi ama %100 doğru olmayabilir.
    # BIST 30 batch testinde her ticker market cap doğrulaması yapılmalı.
    # TUPRS Adım 3.5 sonrası canonical (resmi 1.93B kayıt altında).
}


# ============================================================================
# Data Class
# ============================================================================

@dataclass
class SharesOutstanding:
    """Tek ticker için shares outstanding bilgisi."""
    ticker: str
    shares: int
    source: str  # "static", "isyatirim", "kap"
    market_cap_check: Optional[Decimal] = None  # Optional cross-check
    last_known_price: Optional[Decimal] = None

    @property
    def shares_billions(self) -> float:
        return self.shares / 1_000_000_000

    def calculate_value_per_share(
        self,
        equity_value: Decimal,
    ) -> Decimal:
        """Equity Value (currency-agnostic) → Value per Share."""
        if self.shares == 0:
            return Decimal("0")
        return equity_value / Decimal(self.shares)

    def calculate_market_cap(
        self,
        price: Decimal,
    ) -> Decimal:
        """Current price ile market cap."""
        return price * Decimal(self.shares)


# ============================================================================
# Fetcher Functions
# ============================================================================

def get_shares_outstanding_static(
    ticker: str,
) -> Optional[SharesOutstanding]:
    """
    Static dictionary'den shares outstanding.

    Pilot için yeterli (BIST 30 manuel doğrulanmış).
    """
    ticker = ticker.upper()
    if ticker not in STATIC_SHARES_OUTSTANDING:
        logger.warning(f"No static shares for {ticker}")
        return None

    return SharesOutstanding(
        ticker=ticker,
        shares=STATIC_SHARES_OUTSTANDING[ticker],
        source="static",
    )


def get_shares_outstanding(
    ticker: str,
    fallback_to_static: bool = True,
) -> Optional[SharesOutstanding]:
    """
    Smart fetcher — gelecekte multi-source.

    Şu an: static-only (pilot).
    İleride: isyatirim API → KAP → static fallback.
    """
    # Future: isyatirim API try here
    # Future: KAP scraping try here

    if fallback_to_static:
        return get_shares_outstanding_static(ticker)

    return None


# ============================================================================
# Verification Helper (market cap cross-check)
# ============================================================================

def verify_shares_against_market_cap(
    shares_obj: SharesOutstanding,
    current_price: Decimal,
    expected_market_cap: Decimal,
    tolerance: Decimal = Decimal("0.05"),  # ±5%
) -> bool:
    """
    Market cap = shares × price doğrulaması.

    BIST 30 batch için her ticker'da çalıştırılır.
    """
    calculated_mc = shares_obj.calculate_market_cap(current_price)

    if expected_market_cap == 0:
        return False

    diff_ratio = abs(calculated_mc - expected_market_cap) / expected_market_cap
    return diff_ratio <= tolerance
